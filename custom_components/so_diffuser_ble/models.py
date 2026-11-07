"""Explicit SO/BWJ model capabilities and transport-confidence gates.

A published MIoT schema describes properties; it does NOT prove that another
physical model uses the S5 GATT authentication, framing or command semantics.
Only S5 is field-confirmed. Other model entries require explicit experimental
opt-in and a successful cryptographic BLE login before any credential is saved.
"""
from __future__ import annotations

from dataclasses import dataclass


DEFAULT_MODEL = "bwj.diffuser.s5"
CONF_MODEL = "miot_model"
CONF_EXPERIMENTAL = "experimental_protocol"


@dataclass(frozen=True, slots=True)
class ModelProfile:
    model: str
    name: str
    light: bool = False
    temperature: bool = False
    long_spray: bool = False
    confirmed_gatt: bool = False
    advertisement_names: tuple[str, ...] = ()

    @property
    def experimental(self) -> bool:
        return not self.confirmed_gatt


def _profile(model: str, name: str, *, light: bool, temperature: bool = False,
             confirmed_gatt: bool = False,
             advertisements: tuple[str, ...] = (), long_spray: bool = True) -> ModelProfile:
    return ModelProfile(
        model=model, name=name, light=light, temperature=temperature,
        long_spray=long_spray,
        confirmed_gatt=confirmed_gatt,
        advertisement_names=(model, *advertisements),
    )


# All listed SO schemas allow idle-time 3.4 = 0; only S5's physical
# LongSpray behaviour has been reported by a user. Every non-S5 model
# still requires an explicit experimental onboarding opt-in.
# Published spec capabilities, NOT full protocol/hardware certification.
# Keep explicit model IDs; never match a generic "bwj.diffuser" prefix.
_PROFILES = (
    _profile(DEFAULT_MODEL, "SO S5", light=True, long_spray=True,
             confirmed_gatt=True,
             advertisements=("SO Smart Aroma Diffuser S5",)),
    _profile("bwj.diffuser.s6", "SO S6", light=True),
    _profile("bwj.diffuser.h10", "SO S2", light=True),
    _profile("bwj.diffuser.bw11", "SO S7", light=True),
    _profile("bwj.diffuser.s8", "SO S8", light=True),
    _profile("bwj.diffuser.s9", "SO S9", light=True),
    _profile("bwj.diffuser.s1pro", "SO S1 Pro", light=True, temperature=True),
    _profile("bwj.diffuser.k09", "SO S1", light=False),
    _profile("bwj.diffuser.s19", "SO S19", light=False),
)
MODEL_PROFILES = {p.model: p for p in _PROFILES}

if len(MODEL_PROFILES) != len(_PROFILES):
    raise RuntimeError("duplicate SO diffuser model ID")

_ADVERTISEMENT_TO_MODEL = {
    advertised.casefold(): profile.model
    for profile in _PROFILES
    for advertised in profile.advertisement_names
}


def get_profile(model: str | None = None) -> ModelProfile:
    """Default only pre-existing S5 entries; unknown models fail closed."""
    if model is None:
        model = DEFAULT_MODEL
    try:
        return MODEL_PROFILES[model]
    except (KeyError, TypeError):
        raise ValueError("unknown_so_diffuser_model") from None


def advertised_model(name: str | None) -> str | None:
    """Only exact known names: never a generic Xiaomi FE95 wildcard."""
    if not isinstance(name, str):
        return None
    return _ADVERTISEMENT_TO_MODEL.get(name.strip().casefold())


def assert_model_opt_in(model: str, experimental: bool) -> ModelProfile:
    """Guard both config flow and loading manually modified config entries."""
    profile = get_profile(model)
    if profile.experimental and experimental is not True:
        raise ValueError("experimental_model_requires_explicit_opt_in")
    return profile


def cloud_candidate_models() -> frozenset[str]:
    return frozenset(MODEL_PROFILES)
