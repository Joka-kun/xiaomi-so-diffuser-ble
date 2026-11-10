"""Small Xiaomi Home OAuth2 token-acquisition client for one-time S5 provisioning.

Independent implementation of the published API request/response formats. No
Xiaomi account password, refresh token, or cloud session is stored by SO S5.
The OAuth client ID is the public Xiaomi Home for HA application identifier;
the provider may change or restrict its authorization flow.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from urllib.parse import parse_qs, urlencode, urlsplit

from .models import DEFAULT_MODEL, MODEL_PROFILES
from .protocol import decode_token_hex

OAUTH_CLIENT_ID = "2882303761520251711"
OAUTH_AUTH_URL = "https://account.xiaomi.com/oauth2/authorize"
OAUTH_REDIRECT_BASE = "http://homeassistant.local:8123"
CLOUD_REGIONS = ("cn", "de", "us", "ru", "tw", "sg", "in", "i2")
S5_MODEL = DEFAULT_MODEL
MAX_PAGES = 20
MAX_S5_DEVICES = 64


class XiaomiProvisioningError(RuntimeError):
    """An intentionally non-sensitive reason that may be shown in HA."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def cloud_host(region: str) -> str:
    if region not in CLOUD_REGIONS:
        raise XiaomiProvisioningError("invalid_region")
    return "ha.api.io.mi.com" if region == "cn" else f"{region}.ha.api.io.mi.com"


def new_oauth_identity() -> tuple[str, str]:
    """Random identity and unpredictable state bound to this authorization flow."""
    device_id = f"ha.{secrets.token_hex(16)}"
    return device_id, hashlib.sha1(f"d={device_id}".encode()).hexdigest()


def authorization_url(redirect_uri: str, device_id: str, state: str) -> str:
    if not redirect_uri.startswith(("http://homeassistant.local:8123/",)):
        raise XiaomiProvisioningError("invalid_redirect")
    params = {
        "client_id": OAUTH_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "device_id": device_id,
        "state": state,
        "skip_confirm": "false",
    }
    return f"{OAUTH_AUTH_URL}?{urlencode(params)}"


def parse_manual_oauth_callback(callback_url: str, redirect_uri: str, state: str) -> str:
    """Extract a one-time code only from the exact expected OAuth redirect."""
    if not isinstance(callback_url, str) or len(callback_url) > 8192:
        raise XiaomiProvisioningError("invalid_oauth_callback")
    try:
        actual = urlsplit(callback_url)
        expected = urlsplit(redirect_uri)
        if (
            actual.scheme != expected.scheme
            or actual.netloc != expected.netloc
            or actual.path != expected.path
            or actual.fragment
        ):
            raise XiaomiProvisioningError("invalid_oauth_callback")
        values = parse_qs(actual.query, keep_blank_values=True)
        codes = values.get("code", [])
        states = values.get("state", [])
        if (
            len(codes) != 1 or not (1 <= len(codes[0]) <= 4096)
            or len(states) != 1
            or not secrets.compare_digest(states[0], state)
        ):
            raise XiaomiProvisioningError("invalid_oauth_callback")
        return codes[0]
    except (ValueError, UnicodeError):
        raise XiaomiProvisioningError("invalid_oauth_callback") from None


def _api_result(payload: object) -> dict:
    if not isinstance(payload, dict) or payload.get("code") != 0:
        raise XiaomiProvisioningError("cloud_rejected")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise XiaomiProvisioningError("invalid_cloud_response")
    return result


def extract_so_devices(result: dict) -> list[dict[str, str]]:
    """Parse known SO model candidates only; discovery is NOT BLE compatibility."""
    devices = result.get("list")
    if not isinstance(devices, list):
        raise XiaomiProvisioningError("invalid_device_list")
    matches: list[dict[str, str]] = []
    for item in devices:
        if not isinstance(item, dict) or item.get("model") not in MODEL_PROFILES:
            continue
        did = item.get("did")
        value = item.get("token")
        if not isinstance(did, str) or not did or len(did) > 256:
            continue
        if not isinstance(value, str):
            continue
        try:
            decode_token_hex(value)
        except ValueError:
            continue
        extra = item.get("extra")
        address = item.get("mac") or (
            extra.get("mac") if isinstance(extra, dict) else None
        )
        matches.append({
            "model": item["model"],
            "did": did,
            "name": str(item.get("name") or "SO S5")[:80],
            "mac": address.upper() if isinstance(address, str) else "",
            "token": value.lower(),
        })
    return matches


def extract_s5_devices(result: dict) -> list[dict[str, str]]:
    """Backwards-compatible S5-only extraction for legacy callers/tests."""
    return [
        {key: value for key, value in candidate.items() if key != "model"}
        for candidate in extract_so_devices(result)
        if candidate["model"] == S5_MODEL
    ]


class XiaomiOAuth:
    """API client using the Home Assistant-managed aiohttp session."""

    def __init__(self, session, region: str, device_id: str, redirect_uri: str) -> None:
        self._session = session
        self._host = cloud_host(region)
        self._device_id = device_id
        self._redirect_uri = redirect_uri

    async def _json(self, method: str, path: str, *, params=None, body=None, headers=None) -> dict:
        url = f"https://{self._host}{path}"
        options = {
            "timeout": 20,
            "allow_redirects": False,
            "headers": {
                "User-Agent": f"xiaomi-so-diffuser-ble/1.0.8 client/{self._device_id}",
                **(headers or {}),
            },
        }
        if params is not None:
            options["params"] = params
        if body is not None:
            options["json"] = body
        request = getattr(self._session, method)
        try:
            async with request(url, **options) as response:
                if response.status != 200:
                    raise XiaomiProvisioningError("cloud_http_error")
                if response.content_length is not None and response.content_length > 1_000_000:
                    raise XiaomiProvisioningError("cloud_response_too_large")
                data = await response.json(content_type=None)
        except XiaomiProvisioningError:
            raise
        except Exception:
            # Never surface request URLs (which may contain OAuth codes) or tokens.
            raise XiaomiProvisioningError("cloud_request_failed") from None
        if not isinstance(data, dict):
            raise XiaomiProvisioningError("invalid_cloud_response")
        return data

    async def exchange_code(self, code: str) -> str:
        if not isinstance(code, str) or not (1 <= len(code) <= 4096):
            raise XiaomiProvisioningError("invalid_oauth_code")
        payload = {
            "client_id": OAUTH_CLIENT_ID,
            "redirect_uri": self._redirect_uri,
            "code": code,
            "device_id": self._device_id,
        }
        result = _api_result(await self._json(
            "get", "/app/v2/ha/oauth/get_token",
            params={"data": json.dumps(payload, separators=(",", ":"))},
        ))
        token = result.get("access_token")
        if not isinstance(token, str) or not token:
            raise XiaomiProvisioningError("invalid_cloud_response")
        return token

    async def get_so_devices(self, access_token: str) -> list[dict[str, str]]:
        if not isinstance(access_token, str) or not access_token:
            raise XiaomiProvisioningError("invalid_cloud_token")
        headers = {
            "X-Client-BizId": "haapi",
            "X-Client-AppId": OAUTH_CLIENT_ID,
            "Authorization": f"Bearer{access_token}",
            "Content-Type": "application/json",
        }
        seen_pages: set[str] = set()
        candidates: dict[str, dict[str, str]] = {}
        start_did = None
        for _ in range(MAX_PAGES):
            body: dict = {
                "limit": 200,
                "get_split_device": True,
                "get_third_device": True,
                "dids": [],
            }
            if start_did:
                body["start_did"] = start_did
            page = _api_result(await self._json(
                "post", "/app/v2/home/device_list_page",
                body=body, headers=headers,
            ))
            for match in extract_so_devices(page):
                candidates[match["did"]] = match
                if len(candidates) > MAX_S5_DEVICES:
                    raise XiaomiProvisioningError("too_many_s5_devices")
            if not page.get("has_more"):
                return list(candidates.values())
            next_did = page.get("next_start_did")
            if not isinstance(next_did, str) or not next_did or next_did in seen_pages:
                raise XiaomiProvisioningError("invalid_device_pagination")
            seen_pages.add(next_did)
            start_did = next_did
        raise XiaomiProvisioningError("too_many_device_pages")

    async def get_s5_devices(self, access_token: str) -> list[dict[str, str]]:
        """Preserve the S5-only public helper used in existing tests."""
        candidates = await self.get_so_devices(access_token)
        return [
            {key: value for key, value in item.items() if key != "model"}
            for item in candidates if item["model"] == S5_MODEL
        ]
