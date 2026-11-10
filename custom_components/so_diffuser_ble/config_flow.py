"""SO/BWJ diffuser discovery and address-bound Xiaomi Home token provisioning."""
from __future__ import annotations

import asyncio
import html
import secrets

import voluptuous as vol
from aiohttp import web
from homeassistant import config_entries
from homeassistant.components import bluetooth, webhook
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .config import validate_ble_address
from .const import DOMAIN
from .models import (
    CONF_EXPERIMENTAL, CONF_MODEL, DEFAULT_MODEL, advertised_model,
    assert_model_opt_in, get_profile,
)
from .credentials import TokenFileError
from .provisioning import async_validate_s5_token
from .token_store import load_device_token, save_device_token
from .xiaomi_oauth import (
    CLOUD_REGIONS,
    OAUTH_REDIRECT_BASE,
    XiaomiOAuth,
    XiaomiProvisioningError,
    authorization_url,
    new_oauth_identity,
    parse_manual_oauth_callback,
)

_CHOOSE_DEVICE = "device"
_MANUAL = "__manual__"
_SEARCH = "__search__"
_SEARCH_SECONDS = 10
_MAX_SCAN_RESULTS = 60
_S5_NAMES = frozenset({"bwj.diffuser.s5", "so smart aroma diffuser s5"})
_AUTH_TIMEOUT = 300
_OAUTH_CALLBACKS = "oauth_callbacks"


def is_s5_advertisement(service_info: BluetoothServiceInfoBleak) -> bool:
    """Conservative original S5 matcher, preserved for backwards compatibility."""
    name = getattr(service_info, "name", "") or ""
    return name.strip().casefold() in _S5_NAMES


def is_so_candidate_advertisement(service_info: BluetoothServiceInfoBleak) -> bool:
    """Exact registered SO identifiers only; never generic Xiaomi FE95."""
    return advertised_model(getattr(service_info, "name", None)) is not None


async def _handle_oauth_callback(hass, webhook_id, request):
    """One-shot, state-validated OAuth callback without logging or echoing a code."""
    callbacks = hass.data.get(DOMAIN, {}).get(_OAUTH_CALLBACKS, {})
    record = callbacks.get(webhook_id)
    state = request.query.get("state")
    code = request.query.get("code")
    headers = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
    if (
        record is None
        or not isinstance(state, str)
        or not secrets.compare_digest(state, record["state"])
        or not isinstance(code, str)
        or not 1 <= len(code) <= 4096
        or record["future"].done()
    ):
        return web.Response(
            status=400, text="Invalid or expired Xiaomi authorization",
            headers=headers,
        )
    record["future"].set_result(code)
    return web.Response(
        text="Authorization received. Return to the Home Assistant setup dialog.",
        content_type="text/plain", headers=headers,
    )


class S5ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Discover each SO diffuser and save a GATT-verified, device-bound token."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, BluetoothServiceInfoBleak] = {}
        self._show_all_candidates = False
        self._search_task: asyncio.Task | None = None
        self._search_error: str | None = None
        self._bluetooth_address: str | None = None
        self._cloud_region = "cn"
        self._cloud_devices: dict[str, dict[str, str]] = {}
        self._oauth_task: asyncio.Task | None = None
        self._oauth_future: asyncio.Future | None = None
        self._oauth_id: str | None = None
        self._oauth_url: str | None = None
        self._oauth_redirect: str | None = None
        self._oauth_device_id: str | None = None
        self._oauth_error = "cloud_request_failed"
        self._manual_state: str | None = None
        self._model = DEFAULT_MODEL
        self._experimental_confirmed = False
        self._experimental_did: str | None = None
        self._discovered_model: str | None = None

    def _legacy_entry_conflicts(self, address: str) -> bool:
        """An existing so_s5 config entry must not compete for the same BLE device."""
        return any(
            (entry.data.get(CONF_ADDRESS) or "").upper() == address.upper()
            for entry in self.hass.config_entries.async_entries("so_s5")
        )

    async def _async_finish(self, address: str):
        """Never create an entry without a locally usable credential source."""
        address = validate_ble_address(address).upper()
        if self._legacy_entry_conflicts(address):
            return self.async_abort(reason="legacy_entry_exists")
        profile = assert_model_opt_in(self._model, self._experimental_confirmed)
        await self.async_set_unique_id(address)
        if self.source == config_entries.SOURCE_RECONFIGURE:
            self._abort_if_unique_id_mismatch()
        else:
            self._abort_if_unique_id_configured()
        await self.hass.async_add_executor_job(
            load_device_token, self.hass.config.path(), address
        )
        if self.source == config_entries.SOURCE_RECONFIGURE:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(), data_updates={
                    CONF_ADDRESS: address,
                    CONF_MODEL: self._model,
                    CONF_EXPERIMENTAL: self._experimental_confirmed,
                }
            )
        return self.async_create_entry(
            title="Xiaomi SO Diffuser BLE" if not profile.experimental else f"{profile.name} (experimental)",
            data={
                CONF_ADDRESS: address,
                CONF_MODEL: self._model,
                CONF_EXPERIMENTAL: self._experimental_confirmed,
            }
        )

    async def async_step_reconfigure(self, user_input: dict | None = None):
        """Reauthorize one configured diffuser without changing other entries."""
        entry = self._get_reconfigure_entry()
        self._model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        self._experimental_confirmed = entry.data.get(CONF_EXPERIMENTAL, False)
        assert_model_opt_in(self._model, self._experimental_confirmed)
        self._bluetooth_address = validate_ble_address(
            entry.data[CONF_ADDRESS]
        ).upper()
        await self.async_set_unique_id(self._bluetooth_address)
        self._abort_if_unique_id_mismatch()
        return await self.async_step_credentials(user_input)

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak):
        if not is_so_candidate_advertisement(discovery_info):
            return self.async_abort(reason="not_supported")
        address = discovery_info.address.upper()
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        self._bluetooth_address = address
        self._discovered_model = advertised_model(discovery_info.name)
        self.context["title_placeholders"] = {"name": discovery_info.name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input: dict | None = None):
        if user_input is not None:
            return await self.async_step_credentials()
        return self.async_show_form(
            step_id="bluetooth_confirm", data_schema=vol.Schema({})
        )

    def _remember_candidate(
        self, info: BluetoothServiceInfoBleak, *, include_unrecognized: bool
    ) -> None:
        """Keep connectable BLE candidates, but never infer a model from a fuzzy name."""
        try:
            address = validate_ble_address(getattr(info, "address", None)).upper()
        except ValueError:
            return
        recognized = is_so_candidate_advertisement(info)
        if not recognized and not include_unrecognized:
            return
        if address not in self._discovered and len(self._discovered) >= _MAX_SCAN_RESULTS:
            if not recognized:
                return
            # A verified exact-name candidate takes priority over a generic entry.
            for previous, value in self._discovered.items():
                if not is_so_candidate_advertisement(value):
                    del self._discovered[previous]
                    break
            else:
                return
        self._discovered[address] = info

    def _refresh_candidates(self) -> None:
        """Read connectable advertisements already received by Home Assistant."""
        for info in bluetooth.async_discovered_service_info(
            self.hass, connectable=True
        ):
            self._remember_candidate(
                info, include_unrecognized=self._show_all_candidates
            )

    async def _async_search_nearby(self) -> None:
        """Listen for new advertisements; never launch a competing BLE scanner."""
        self._show_all_candidates = True

        def on_advertisement(info: BluetoothServiceInfoBleak, _change) -> None:
            self._remember_candidate(info, include_unrecognized=True)

        # The HA Bluetooth manager owns the actual scanners and ESPHome proxies.
        # No address is known yet; registration observes advertisements but
        # does not force an active scan on a passive-only Bluetooth proxy.
        unsubscribe = bluetooth.async_register_callback(
            self.hass, on_advertisement, None, bluetooth.BluetoothScanningMode.ACTIVE
        )
        try:
            self._refresh_candidates()
            await asyncio.sleep(_SEARCH_SECONDS)
            self._refresh_candidates()
        finally:
            unsubscribe()

    async def async_step_search(self, user_input: dict | None = None):
        """Bounded discovery progress, then show nearby candidates or retry."""
        if self._search_task is None:
            self._search_task = self.hass.async_create_task(
                self._async_search_nearby()
            )
        if self._search_task.done():
            try:
                self._search_task.result()
            except Exception:
                self._search_error = "scan_unavailable"
            finally:
                self._search_task = None
            return self.async_show_progress_done(next_step_id="user")
        return self.async_show_progress(
            step_id="search",
            progress_action="search",
            progress_task=self._search_task,
        )

    async def async_step_user(self, user_input: dict | None = None):
        """Offer explicit search even when no exact SO advertisement is cached."""
        if user_input is not None:
            selected = user_input[_CHOOSE_DEVICE]
            if selected == _SEARCH:
                return await self.async_step_search()
            if selected == _MANUAL:
                return await self.async_step_manual()
            if selected not in self._discovered:
                return self.async_abort(reason="not_supported")
            self._bluetooth_address = selected
            self._discovered_model = advertised_model(
                getattr(self._discovered[selected], "name", None)
            )
            self.context["title_placeholders"] = {
                "name": getattr(self._discovered[selected], "name", None)
                or "Bluetooth device"
            }
            return await self.async_step_bluetooth_confirm()

        self._refresh_candidates()
        language = str(getattr(self.hass.config, "language", "en")).casefold()
        ru = language.startswith("ru")
        choices = {
            _SEARCH: "🔍 Искать устройства (10 секунд)" if ru
                     else "🔍 Search nearby devices (10 seconds)",
        }
        for address, info in sorted(
            self._discovered.items(),
            key=lambda item: (
                advertised_model(getattr(item[1], "name", None)) is None,
                (getattr(item[1], "name", None) or "").casefold(),
                item[0],
            ),
        ):
            name = getattr(info, "name", None) or (
                "Без имени" if ru else "Unnamed Bluetooth device"
            )
            if advertised_model(getattr(info, "name", None)) is None:
                name += " — не подтверждено" if ru else " — unverified"
            choices[address] = f"{name} ({address})"
        choices[_MANUAL] = (
            "Ввести Bluetooth-адрес вручную" if ru
            else "Enter Bluetooth address manually"
        )
        errors = {"base": self._search_error} if self._search_error else {}
        self._search_error = None
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(_CHOOSE_DEVICE): vol.In(choices)}),
            errors=errors,
            description_placeholders={"count": str(len(self._discovered))},
        )

    async def async_step_manual(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            try:
                address = validate_ble_address(user_input[CONF_ADDRESS]).upper()
            except (ValueError, KeyError):
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                self._bluetooth_address = address
                return await self.async_step_credentials()
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): str}),
            errors=errors,
        )

    async def async_step_credentials(self, user_input: dict | None = None):
        """Use Xiaomi OAuth or the token already saved for this BLE address."""
        if (self._bluetooth_address is not None
                and self._legacy_entry_conflicts(self._bluetooth_address)):
            return self.async_abort(reason="legacy_entry_exists")
        errors = {}
        if user_input is not None:
            method = user_input["method"]
            if method == "existing":
                assert self._bluetooth_address is not None
                if (
                    self._discovered_model not in (None, DEFAULT_MODEL)
                    and self.source != config_entries.SOURCE_RECONFIGURE
                ):
                    errors["base"] = "experimental_cloud_required"
                else:
                    try:
                        saved = await self.hass.async_add_executor_job(
                            load_device_token, self.hass.config.path(),
                            self._bluetooth_address,
                        )
                        # A readable token file alone cannot identify a real
                        # diffuser: verify possession via the local GATT login.
                        await async_validate_s5_token(
                            self.hass, self._bluetooth_address, saved
                        )
                        return await self._async_finish(self._bluetooth_address)
                    except TokenFileError as exc:
                        errors["base"] = f"token_{exc.reason}"
                    except XiaomiProvisioningError as exc:
                        errors["base"] = exc.reason
            else:
                self._cloud_region = user_input["region"]
                if method == "oauth_manual":
                    return await self.async_step_oauth_manual()
                return await self.async_step_oauth()
        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema({
                vol.Required("method", default="oauth"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["oauth", "oauth_manual", "existing"], translation_key="credential_method",
                    )
                ),
                vol.Required("region", default=self._cloud_region):
                    vol.In(CLOUD_REGIONS),
            }),
            errors=errors,
        )

    async def async_step_oauth_manual(self, user_input: dict | None = None):
        """Fallback when homeassistant.local cannot receive Xiaomi's redirect."""
        if self._oauth_url is None:
            self._oauth_id = secrets.token_urlsafe(32)
            self._oauth_device_id, self._manual_state = new_oauth_identity()
            self._oauth_redirect = (
                OAUTH_REDIRECT_BASE + webhook.async_generate_path(self._oauth_id)
            )
            self._oauth_url = authorization_url(
                self._oauth_redirect, self._oauth_device_id, self._manual_state
            )

        errors = {}
        if user_input is not None:
            assert self._oauth_redirect is not None
            assert self._oauth_device_id is not None
            assert self._manual_state is not None
            try:
                code = parse_manual_oauth_callback(
                    user_input["callback_url"],
                    self._oauth_redirect, self._manual_state,
                )
                api = XiaomiOAuth(
                    async_get_clientsession(self.hass),
                    self._cloud_region,
                    self._oauth_device_id,
                    self._oauth_redirect,
                )
                access_token = await api.exchange_code(code)
                try:
                    devices = await api.get_so_devices(access_token)
                finally:
                    del access_token
                if not devices:
                    raise XiaomiProvisioningError("no_s5_in_account")
                self._cloud_devices = {device["did"]: device for device in devices}
                self._manual_state = None
                return await self.async_step_cloud_device()
            except XiaomiProvisioningError as exc:
                errors["base"] = exc.reason

        return self.async_show_form(
            step_id="oauth_manual",
            data_schema=vol.Schema({vol.Required("callback_url"): str}),
            errors=errors,
            description_placeholders={
                "link_left": f'<a href="{html.escape(self._oauth_url, quote=True)}" target="_blank" rel="noopener noreferrer">',
                "link_right": "</a>",
            },
        )

    async def _async_oauth_exchange_and_discover(self) -> None:
        assert self._oauth_future is not None
        assert self._oauth_device_id is not None
        assert self._oauth_redirect is not None
        assert self._oauth_id is not None
        try:
            code = await asyncio.wait_for(self._oauth_future, timeout=_AUTH_TIMEOUT)
            api = XiaomiOAuth(
                async_get_clientsession(self.hass),
                self._cloud_region,
                self._oauth_device_id,
                self._oauth_redirect,
            )
            access_token = await api.exchange_code(code)
            try:
                candidates = await api.get_so_devices(access_token)
            finally:
                del access_token
            if not candidates:
                raise XiaomiProvisioningError("no_s5_in_account")
            self._cloud_devices = {item["did"]: item for item in candidates}
        except TimeoutError:
            raise XiaomiProvisioningError("oauth_expired") from None
        finally:
            webhook.async_unregister(self.hass, self._oauth_id)
            self.hass.data.get(DOMAIN, {}).get(_OAUTH_CALLBACKS, {}).pop(
                self._oauth_id, None
            )
            self._oauth_future = None

    async def async_step_oauth(self, user_input: dict | None = None):
        """Authorize in Xiaomi's own browser page, receive code at HA webhook."""
        if self._oauth_task is None:
            self._oauth_id = secrets.token_urlsafe(32)
            self._oauth_device_id, state = new_oauth_identity()
            self._oauth_redirect = (
                OAUTH_REDIRECT_BASE + webhook.async_generate_path(self._oauth_id)
            )
            self._oauth_url = authorization_url(
                self._oauth_redirect, self._oauth_device_id, state
            )
            self._oauth_future = asyncio.get_running_loop().create_future()
            self.hass.data.setdefault(DOMAIN, {}).setdefault(
                _OAUTH_CALLBACKS, {}
            )[self._oauth_id] = {
                "state": state,
                "future": self._oauth_future,
            }
            webhook.async_register(
                self.hass, DOMAIN, "SO diffuser Xiaomi OAuth",
                self._oauth_id, _handle_oauth_callback,
                allowed_methods=("GET",),
            )
            self._oauth_task = self.hass.async_create_task(
                self._async_oauth_exchange_and_discover()
            )
        if self._oauth_task.done():
            try:
                self._oauth_task.result()
            except (XiaomiProvisioningError, asyncio.CancelledError) as exc:
                self._oauth_error = (
                    exc.reason if isinstance(exc, XiaomiProvisioningError)
                    else "oauth_expired"
                )
                return self.async_show_progress_done(next_step_id="oauth_error")
            except Exception:
                self._oauth_error = "cloud_request_failed"
                return self.async_show_progress_done(next_step_id="oauth_error")
            return self.async_show_progress_done(next_step_id="cloud_device")
        return self.async_show_progress(
            step_id="oauth",
            progress_action="oauth",
            description_placeholders={
                "link_left": f'<a href="{html.escape(self._oauth_url, quote=True)}" target="_blank" rel="noopener noreferrer">',
                "link_right": "</a>",
                "default_host": OAUTH_REDIRECT_BASE,
                "example_host": "http://192.168.1.50:8123",
            },
            progress_task=self._oauth_task,
        )

    async def async_step_oauth_error(self, user_input: dict | None = None):
        if user_input is not None:
            self._oauth_task = None
            return await self.async_step_oauth()
        return self.async_show_form(
            step_id="oauth_error",
            data_schema=vol.Schema({}),
            errors={"base": self._oauth_error},
        )

    async def _async_try_provision(self, chosen: dict[str, str]):
        """Returns (flow_result, error_code); no device commands before BLE proof."""
        assert self._bluetooth_address is not None
        if self._legacy_entry_conflicts(self._bluetooth_address):
            return None, "legacy_entry_exists"
        profile = get_profile(chosen["model"])
        if (
            self._discovered_model is not None
            and self._discovered_model != profile.model
        ):
            # An exact advertised model and a different cloud model are
            # inconsistent. Never try a token for the mismatched device.
            return None, "model_mismatch"
        token = bytes.fromhex(chosen["token"])
        try:
            # The S5-compatible Standard Auth proof binds the selected cloud
            # device credential to the *actual* local BLE address. A matching
            # MIoT property schema or friendly name alone is never sufficient.
            await async_validate_s5_token(
                self.hass, self._bluetooth_address, token
            )
            await self.hass.async_add_executor_job(
                save_device_token, self.hass.config.path(),
                self._bluetooth_address, token,
            )
        except XiaomiProvisioningError as exc:
            return None, exc.reason
        except (OSError, TokenFileError):
            return None, "credential_storage_failed"
        finally:
            del token

        self._model = profile.model
        self._experimental_confirmed = profile.experimental
        self._cloud_devices.clear()
        return await self._async_finish(self._bluetooth_address), None

    async def async_step_cloud_device(self, user_input: dict | None = None):
        """Cloud models are candidates; only S5 has field-confirmed GATT."""
        assert self._bluetooth_address is not None
        errors = {}
        if user_input is not None:
            chosen = self._cloud_devices.get(user_input.get("device"))
            if chosen is None:
                errors["base"] = "invalid_cloud_device"
            else:
                profile = get_profile(chosen["model"])
                if profile.experimental:
                    # Explicit additional step; model is not called supported
                    # merely because it exists in the user's Xiaomi account.
                    self._experimental_did = chosen["did"]
                    return await self.async_step_experimental_confirm()
                result, error = await self._async_try_provision(chosen)
                if error is None:
                    return result
                errors["base"] = error

        # Experimental consent has its own localized step. Keep device options
        # short, preserve the user-provided Xiaomi device name verbatim.
        choices = {
            did: f'{get_profile(device["model"]).name}: {device["name"]}'
            for did, device in sorted(self._cloud_devices.items())
        }
        return self.async_show_form(
            step_id="cloud_device",
            data_schema=vol.Schema({
                vol.Required("device"): vol.In(choices),
            }),
            errors=errors,
        )

    async def async_step_experimental_confirm(self, user_input: dict | None = None):
        """Never auto-enable an untested model with S5 command semantics."""
        chosen = self._cloud_devices.get(self._experimental_did)
        if chosen is None:
            return self.async_abort(reason="not_supported")
        profile = get_profile(chosen["model"])
        if not profile.experimental:
            return self.async_abort(reason="not_supported")
        errors = {}
        if user_input is not None:
            if user_input.get("acknowledge") is True:
                result, error = await self._async_try_provision(chosen)
                if error is None:
                    return result
                errors["base"] = error
            else:
                errors["base"] = "experimental_confirmation_required"
        return self.async_show_form(
            step_id="experimental_confirm",
            data_schema=vol.Schema({
                vol.Required("acknowledge", default=False): bool,
            }),
            errors=errors,
            description_placeholders={"model": profile.name},
        )
