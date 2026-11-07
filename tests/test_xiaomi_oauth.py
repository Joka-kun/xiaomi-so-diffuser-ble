"""Network-free protocol tests for one-time Xiaomi S5 token acquisition."""
from __future__ import annotations

import asyncio
import unittest
from urllib.parse import parse_qs, urlparse

from custom_components.so_diffuser_ble.xiaomi_oauth import (
    OAUTH_CLIENT_ID,
    XiaomiOAuth,
    XiaomiProvisioningError,
    authorization_url,
    cloud_host,
    extract_s5_devices,
    new_oauth_identity,
    parse_manual_oauth_callback,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status
        self.content_length = 150

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, **kwargs):
        return self.payload


class FakeSession:
    def __init__(self, get_response=None, post_responses=None):
        self.get_response = get_response
        self.post_responses = list(post_responses or [])
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return FakeResponse(self.get_response)

    def post(self, url, **kwargs):
        self.calls.append(("post", url, kwargs))
        return FakeResponse(self.post_responses.pop(0))


class OAuthHelpersTests(unittest.TestCase):
    def test_authorization_state_is_unique_and_bound_to_device_id(self):
        one = new_oauth_identity()
        two = new_oauth_identity()
        self.assertNotEqual(one, two)
        url = authorization_url(
            "http://homeassistant.local:8123/api/webhook/opaque", *one
        )
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params["state"], [one[1]])
        self.assertEqual(params["device_id"], [one[0]])
        self.assertEqual(params["client_id"], [OAUTH_CLIENT_ID])
        self.assertEqual(params["response_type"], ["code"])

    def test_reject_untrusted_redirect_and_region(self):
        for redirect in (
            "https://evil.example/api/webhook/x",
            "http://homeassistant.local.evil:8123/api/webhook/x",
            "file:///secret",
        ):
            with self.subTest(redirect=redirect):
                with self.assertRaises(XiaomiProvisioningError):
                    authorization_url(redirect, "ha.random", "state")
        with self.assertRaises(XiaomiProvisioningError):
            cloud_host("evil.example")
        self.assertEqual(cloud_host("ru"), "ru.ha.api.io.mi.com")

    def test_manual_redirect_requires_same_uri_and_matching_state(self):
        expected = "http://homeassistant.local:8123/api/webhook/random"
        valid = expected + "?state=secure-state&code=one-use-code"
        self.assertEqual(
            parse_manual_oauth_callback(valid, expected, "secure-state"),
            "one-use-code",
        )
        for url in (
            expected + "?state=wrong&code=one-use-code",
            "http://attacker.invalid/api/webhook/random?state=secure-state&code=x",
            expected + "?state=secure-state&code=x&code=y",
            expected + "?state=secure-state",
            expected + "?state=secure-state&code=x#fragment",
        ):
            with self.subTest(url=url):
                with self.assertRaises(XiaomiProvisioningError):
                    parse_manual_oauth_callback(url, expected, "secure-state")

    def test_exact_model_and_gatt_token_size(self):
        page = {"list": [
            {"model": "bwj.diffuser.s5", "did": "blt.001", "name": "My S5",
             "token": "0102030405060708090a0b0c"},
            {"model": "bwj.diffuser.s6", "did": "blt.002", "token": "0102030405060708090a0b0c"},
            {"model": "bwj.diffuser.s5", "did": "blt.003", "token": "f" * 32},
            {"model": "bwj.diffuser.s5", "did": "blt.004", "token": "bad-token"},
        ]}
        self.assertEqual(
            extract_s5_devices(page),
            [{"did": "blt.001", "name": "My S5", "mac": "",
              "token": "0102030405060708090a0b0c"}],
        )


class XiaomiOAuthRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_exchange_code_and_fetch_token_only_from_s5(self):
        session = FakeSession(
            get_response={"code": 0, "result": {"access_token": "ACCESS",
                                               "refresh_token": "DO_NOT_SAVE"}},
            post_responses=[
                {"code": 0, "result": {"list": [
                    {"model": "bwj.diffuser.s5", "did": "blt.aaa",
                     "token": "00112233445566778899aabb", "name": "S5"},
                    {"model": "other.device", "did": "2", "token": "f" * 24}
                ], "has_more": True, "next_start_did": "next"}},
                {"code": 0, "result": {"list": [
                    {"model": "bwj.diffuser.s5", "did": "blt.bbb",
                     "token": "ffeeddccbbaa998877665544", "name": "Second S5"},
                ], "has_more": False}},
            ],
        )
        api = XiaomiOAuth(session, "ru", "ha.test", "http://homeassistant.local:8123/api/webhook/c")
        token = await api.exchange_code("CODE")
        self.assertEqual(token, "ACCESS")
        devices = await api.get_s5_devices(token)
        self.assertEqual([d["did"] for d in devices], ["blt.aaa", "blt.bbb"])
        self.assertEqual(len(session.calls), 3)
        self.assertIn("/app/v2/ha/oauth/get_token", session.calls[0][1])
        self.assertIn("/app/v2/home/device_list_page", session.calls[1][1])
        self.assertEqual(session.calls[1][2]["headers"]["Authorization"], "BearerACCESS")
        self.assertEqual(session.calls[2][2]["json"]["start_did"], "next")

    async def test_empty_or_invalid_page_rejected_without_secrets_in_errors(self):
        for result in ({"code": 1, "message": "secret-token"},
                       {"code": 0, "result": {"list": "not-a-list"}}):
            session = FakeSession(post_responses=[result])
            api = XiaomiOAuth(session, "cn", "ha.id", "http://homeassistant.local:8123/api/webhook/a")
            with self.assertRaises(XiaomiProvisioningError) as caught:
                await api.get_s5_devices("SECRET_ACCESS")
            self.assertNotIn("SECRET_ACCESS", str(caught.exception))
            self.assertNotIn("secret-token", str(caught.exception))

    async def test_pagination_loop_is_rejected(self):
        page = {"code": 0, "result": {"list": [], "has_more": True,
                                        "next_start_did": "same"}}
        api = XiaomiOAuth(
            FakeSession(post_responses=[page, page]), "cn", "ha.id",
            "http://homeassistant.local:8123/api/webhook/a",
        )
        with self.assertRaises(XiaomiProvisioningError) as caught:
            await api.get_s5_devices("ACCESS")
        self.assertEqual(caught.exception.reason, "invalid_device_pagination")


if __name__ == "__main__":
    unittest.main()
