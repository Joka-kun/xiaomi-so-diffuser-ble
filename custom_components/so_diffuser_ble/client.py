"""Offline-testable S5 GATT sessions with fixed, allowlisted UI controls.

The client has no scanner, connector, pairing, reset, generic MIoT read, or
unbounded property-write API. HA owns connection lifecycle; synthetic tests do
not establish physical device behavior.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from collections import deque
import secrets
import struct

from .protocol import (
    FIXED_PROPERTIES,
    PayloadAuthenticationError,
    _SessionKeys,
    decrypt_ccm,
    derive_login_material,
    encode_fixed_property_set,
    encrypt_tx_parcel,
    parse_set_property_response,
)


@dataclass(frozen=True)
class MiotProperty:
    siid: int
    piid: int
    value_type: int
    value: bool | int | float | str | bytes


@dataclass(frozen=True)
class MiotMessage:
    version: int
    transaction_id: int
    opcode: int
    name: str
    properties: tuple[MiotProperty, ...]


def _decode_value(value_type: int, raw: bytes) -> bool | int | float | str | bytes:
    if value_type == 0:
        if len(raw) != 1:
            raise ValueError("invalid bool value length")
        return bool(raw[0])
    if value_type in (1, 2, 3, 4, 5, 6, 7, 8):
        if len(raw) not in (1, 2, 4, 8):
            raise ValueError("invalid integer value length")
        return int.from_bytes(raw, "little", signed=value_type in (2, 4, 6, 8))
    if value_type == 9:
        if len(raw) != 4:
            raise ValueError("invalid float value length")
        return struct.unpack("<f", raw)[0]
    if value_type == 10:
        return raw.decode("utf-8")
    return raw


def _derive_login_material(
    token: bytes, rand: bytes, remote_key: bytes, remote_info: bytes
):
    """Verify both captured Xiaomi-login HMAC proofs and derive session keys."""
    return derive_login_material(token, rand, remote_key, remote_info)


def parse_miot_message(packet: bytes) -> MiotMessage:
    """Parse an authenticated MIoT Spec-v2 PropertyChanged message only."""
    if len(packet) < 6:
        raise ValueError("MIoT packet is too short")
    header = int.from_bytes(packet[:2], "little")
    version, packet_length = header >> 12, header & 0x0FFF
    if version != 2 or packet_length != len(packet):
        raise ValueError("invalid MIoT Spec-v2 header or length")
    transaction_id = int.from_bytes(packet[2:4], "little")
    opcode = packet[4]
    if opcode != 4:
        raise ValueError("only PropertyChanged notifications are supported")

    body = packet[5:]
    count = body[0]
    offset = 1
    properties: list[MiotProperty] = []
    for _ in range(count):
        if len(body) - offset < 5:
            raise ValueError("truncated PropertyChanged property header")
        siid = body[offset]
        piid = int.from_bytes(body[offset + 1:offset + 3], "little")
        type_length = int.from_bytes(body[offset + 3:offset + 5], "little")
        value_type, value_length = (type_length >> 12) & 0x0F, type_length & 0x0FFF
        offset += 5
        if value_length > len(body) - offset:
            raise ValueError("truncated PropertyChanged value")
        raw = body[offset:offset + value_length]
        properties.append(MiotProperty(siid, piid, value_type, _decode_value(value_type, raw)))
        offset += value_length
    if offset != len(body):
        raise ValueError("unexpected trailing PropertyChanged bytes")

    return MiotMessage(version, transaction_id, opcode, "PropertyChanged", tuple(properties))


class S5ClientError(RuntimeError):
    """Base error for the bounded S5 session adapter."""


class AuthenticationError(S5ClientError):
    """The captured S5 login proof or authenticated frame did not validate."""


class ProtocolTimeout(S5ClientError):
    """An expected GATT protocol notification did not arrive in time."""


class S5ReadOnlyClient:
    """Authenticate and listen through a caller-owned, already-connected GATT client.

    The constructor never connects or scans. The only supported outbound
    traffic is the S5 login exchange and ``00 00 03 00`` acknowledgements on
    UUID 001B. No MIoT property command is constructed or sent.
    """

    UUID_CONTROL = "00000010-0000-1000-8000-00805f9b34fb"
    UUID_AUTH = "00000019-0000-1000-8000-00805f9b34fb"
    UUID_DATA_RX = "0000001b-0000-1000-8000-00805f9b34fb"
    UUID_DATA_TX = "0000001a-0000-1000-8000-00805f9b34fb"

    A4 = bytes([0xA4])
    CMD_LOGIN = bytes.fromhex("24000000")
    HDR_SEND_KEY = bytes.fromhex("0000000b0100")
    HDR_SEND_INFO = bytes.fromhex("0000000a0100")
    RCV_RDY = bytes.fromhex("00000101")
    RCV_OK = bytes.fromhex("00000100")
    ACK_DATA = bytes.fromhex("00000300")
    CFM_LOGIN_OK = bytes.fromhex("21000000")
    AUTH_FRAME_PREFIX = bytes.fromhex("000004")
    AUTH_ECHO_PREFIX = bytes.fromhex("000005")
    DIRECT_DATA_PREFIX = bytes.fromhex("00000200")
    NOTIFICATION_UUIDS = (UUID_CONTROL, UUID_AUTH, UUID_DATA_RX)

    def __init__(
        self,
        gatt_client,
        token: bytes,
        *,
        timeout: float = 8.0,
        auth_quiet: float = 2.0,
    ) -> None:
        if not isinstance(token, (bytes, bytearray)) or len(token) != 12:
            raise ValueError("S5 GATT token must be 12 bytes")
        if timeout <= 0 or auth_quiet <= 0:
            raise ValueError("timeouts must be positive")
        if not callable(getattr(gatt_client, "start_notify", None)):
            raise TypeError("connected GATT client must provide start_notify")
        if not callable(getattr(gatt_client, "write_gatt_char", None)):
            raise TypeError("connected GATT client must provide write_gatt_char")

        self._client = gatt_client
        self._token: bytes | None = bytes(token)
        self._timeout = float(timeout)
        self._auth_quiet = float(auth_quiet)
        self._inbox: deque[tuple[str, bytes]] = deque()
        self._event = asyncio.Event()
        self._overflow = False
        self._notifications_started = False
        self._authenticated = False
        self._keys: _SessionKeys | None = None

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    def _on_notify(self, uuid: str, data) -> None:
        if len(self._inbox) >= 512:
            self._overflow = True
        else:
            self._inbox.append((uuid, bytes(data)))
        self._event.set()

    async def _wait_for(self, predicate, timeout: float | None = None) -> tuple[str, bytes]:
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout
        while True:
            if self._overflow:
                raise S5ClientError("notification queue overflow")
            for index, (uuid, data) in enumerate(self._inbox):
                if predicate(uuid, data):
                    del self._inbox[index]
                    return uuid, data
            if deadline is None:
                self._event.clear()
                await self._event.wait()
                continue
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise ProtocolTimeout("timed out waiting for S5 GATT notification")
            self._event.clear()
            try:
                await asyncio.wait_for(self._event.wait(), timeout=remaining)
            except TimeoutError:
                continue

    async def _write(self, uuid: str, data: bytes) -> None:
        if uuid not in {self.UUID_CONTROL, self.UUID_AUTH, self.UUID_DATA_RX}:
            raise S5ClientError("GATT write characteristic is outside the S5 read-only allowlist")
        if uuid == self.UUID_DATA_RX and (not self._authenticated or data != self.ACK_DATA):
            raise S5ClientError("only authenticated transport ACKs are allowed on UUID 001B")
        await self._client.write_gatt_char(uuid, data, response=False)

    async def _start_notifications(self) -> None:
        if self._notifications_started:
            raise S5ClientError("notification subscriptions are already active")
        for uuid in self.NOTIFICATION_UUIDS:
            callback = lambda sender, data, char_uuid=uuid: self._on_notify(char_uuid, data)
            await self._client.start_notify(uuid, callback)
        self._notifications_started = True

    async def _auth_init(self) -> None:
        await self._write(self.UUID_CONTROL, self.A4)
        while True:
            try:
                _, data = await self._wait_for(
                    lambda uuid, value: uuid == self.UUID_AUTH
                    and len(value) >= 4
                    and value.startswith(self.AUTH_FRAME_PREFIX),
                    timeout=self._auth_quiet,
                )
            except ProtocolTimeout:
                return
            await self._write(self.UUID_AUTH, self.AUTH_ECHO_PREFIX + data[3:])

    async def authenticate(self) -> None:
        """Run the captured S5 login exchange; never sends a property command."""
        if self._authenticated:
            return
        if self._notifications_started:
            raise S5ClientError("authentication may be attempted only once per client")
        if not bool(getattr(self._client, "is_connected", False)):
            raise S5ClientError("caller-owned GATT client is not already connected")
        if self._token is None:
            raise AuthenticationError("GATT token is no longer available")

        token = self._token
        try:
            await self._start_notifications()
            await self._auth_init()
            await self._write(self.UUID_CONTROL, self.CMD_LOGIN)

            rand = secrets.token_bytes(16)
            await self._write(self.UUID_AUTH, self.HDR_SEND_KEY)
            await self._wait_for(
                lambda uuid, data: uuid == self.UUID_AUTH and data == self.RCV_RDY,
                timeout=self._timeout,
            )
            await self._write(self.UUID_AUTH, bytes.fromhex("0100") + rand)
            await self._wait_for(
                lambda uuid, data: uuid == self.UUID_AUTH and data == self.RCV_OK,
                timeout=self._timeout,
            )

            _, remote_key_frame = await self._wait_for(
                lambda uuid, data: uuid == self.UUID_AUTH
                and len(data) == 20
                and data.startswith(bytes.fromhex("0000020d")),
                timeout=self._timeout,
            )
            remote_key = remote_key_frame[4:]
            await self._write(self.UUID_AUTH, self.ACK_DATA)

            _, remote_info_frame = await self._wait_for(
                lambda uuid, data: uuid == self.UUID_AUTH
                and len(data) == 36
                and data.startswith(bytes.fromhex("0000020c")),
                timeout=self._timeout,
            )
            remote_info = remote_info_frame[4:]
            await self._write(self.UUID_AUTH, self.ACK_DATA)

            try:
                login_info, keys = _derive_login_material(token, rand, remote_key, remote_info)
            except (PayloadAuthenticationError, ValueError):
                raise AuthenticationError("S5 GATT login proof validation failed") from None

            await self._write(self.UUID_AUTH, self.HDR_SEND_INFO)
            await self._wait_for(
                lambda uuid, data: uuid == self.UUID_AUTH and data == self.RCV_RDY,
                timeout=self._timeout,
            )
            await self._write(self.UUID_AUTH, bytes.fromhex("0100") + login_info)
            await self._wait_for(
                lambda uuid, data: uuid == self.UUID_AUTH and data == self.RCV_OK,
                timeout=self._timeout,
            )
            await self._wait_for(
                lambda uuid, data: uuid == self.UUID_CONTROL and data == self.CFM_LOGIN_OK,
                timeout=self._timeout,
            )

            self._keys = keys
            self._authenticated = True
        finally:
            self._token = None

    async def _iter_authenticated_payloads(self, timeout: float | None = None):
        if not self._authenticated or self._keys is None:
            raise AuthenticationError("authenticate before listening for S5 data")
        while True:
            _, frame = await self._wait_for(
                lambda uuid, data: uuid == self.UUID_DATA_RX,
                timeout=timeout,
            )
            if not frame.startswith(self.DIRECT_DATA_PREFIX):
                continue
            if len(frame) < 10:
                raise S5ClientError("truncated S5 direct data frame")
            counter = int.from_bytes(frame[4:6], "little")
            try:
                plaintext = decrypt_ccm(
                    self._keys.dev_key,
                    self._keys.dev_iv,
                    counter,
                    frame[6:],
                )
            except PayloadAuthenticationError:
                raise AuthenticationError("S5 AES-CCM tag validation failed") from None

            await self._write(self.UUID_DATA_RX, self.ACK_DATA)
            if len(plaintext) < 5:
                raise S5ClientError("authenticated MIoT payload is truncated")
            header = int.from_bytes(plaintext[:2], "little")
            if header >> 12 != 2 or (header & 0x0FFF) != len(plaintext):
                raise S5ClientError("authenticated MIoT Spec-v2 header is invalid")
            yield plaintext

    async def iter_property_changes(self, timeout: float | None = None):
        """Yield authenticated PropertyChanged messages; send transport ACKs only."""
        async for plaintext in self._iter_authenticated_payloads(timeout):
            if plaintext[4] != 4:
                continue
            try:
                yield parse_miot_message(plaintext)
            except ValueError:
                raise S5ClientError("authenticated PropertyChanged payload is malformed") from None


class S5ControlClient(S5ReadOnlyClient):
    """Fixed, allowlisted S5 UI properties; waits for response and read-back."""

    TX_HEADER = bytes.fromhex("000000000100")
    NOTIFICATION_UUIDS = (
        S5ReadOnlyClient.UUID_CONTROL,
        S5ReadOnlyClient.UUID_AUTH,
        S5ReadOnlyClient.UUID_DATA_TX,
        S5ReadOnlyClient.UUID_DATA_RX,
    )

    def __init__(self, gatt_client, token: bytes, **kwargs) -> None:
        super().__init__(gatt_client, token, **kwargs)
        self._command_lock = asyncio.Lock()
        self._next_transaction_id = 0
        self._tx_counter = 0
        self._pending_responses = {}
        self._pending_values = {}
        self._active_tx_frames: frozenset[bytes] = frozenset()
        self._reader_active = False

    def iter_messages(self, timeout: float | None = None):
        if not self._authenticated:
            raise AuthenticationError("authenticate before listening for S5 messages")
        if self._reader_active:
            raise S5ClientError("only one S5 control-message listener is supported")
        self._reader_active = True
        return self._iter_messages(timeout)

    async def _iter_messages(self, timeout: float | None = None):
        try:
            async for packet in self._iter_authenticated_payloads(timeout):
                opcode = packet[4]
                if opcode == 1:
                    try:
                        transaction_id, results = parse_set_property_response(packet)
                    except ValueError:
                        raise S5ClientError("authenticated SetPropertyResp payload is malformed") from None
                    pending_response = self._pending_responses.get(transaction_id)
                    if pending_response is not None and not pending_response[1].done():
                        expected_key, future = pending_response
                        if len(results) != 1 or results[0][:2] != expected_key:
                            future.set_exception(S5ClientError("S5 SetPropertyResp did not match the active property"))
                        else:
                            future.set_result(results[0][2])
                    continue
                if opcode != 4:
                    continue
                try:
                    message = parse_miot_message(packet)
                except ValueError:
                    raise S5ClientError("authenticated PropertyChanged payload is malformed") from None
                for prop in message.properties:
                    pending = self._pending_values.get((prop.siid, prop.piid))
                    if pending is None or pending[2].done():
                        continue
                    expected_type, expected_value, future = pending
                    if prop.value_type != expected_type or type(prop.value) is not int:
                        future.set_exception(S5ClientError("S5 property read-back type is invalid"))
                    elif prop.value == expected_value:
                        future.set_result(prop.value)
                    else:
                        # PropertyChanged messages have no command correlation ID.
                        # A queued notification can still report the previous
                        # value after the write is acknowledged. Do not fail the
                        # command on that stale observation: await the requested
                        # value until the bounded read-back timeout expires.
                        pass
                yield message
        finally:
            self._reader_active = False

    async def _set_fixed_property(self, name: str, value: int, *, timeout: float | None = None) -> None:
        if not self._authenticated or self._keys is None:
            raise AuthenticationError("authenticate before setting an S5 property")
        if not self._reader_active:
            raise S5ClientError("start the S5 control-message listener before setting a property")
        wait_timeout = self._timeout if timeout is None else timeout
        if wait_timeout <= 0:
            raise ValueError("timeout must be positive")

        if name not in FIXED_PROPERTIES:
            raise ValueError("S5 property is outside the fixed UI allowlist")
        siid, piid, value_type, _width, _minimum, _maximum = FIXED_PROPERTIES[name]
        encode_fixed_property_set(0, name, value)

        async with self._command_lock:
            if self._next_transaction_id >= 0xFFFF:
                raise S5ClientError("S5 transaction id space exhausted for this session")
            if self._tx_counter > 0xFFFF:
                raise S5ClientError("S5 parcel counter exhausted for this session")
            self._next_transaction_id += 1
            transaction_id = self._next_transaction_id
            counter = self._tx_counter
            self._tx_counter += 1
            plaintext = encode_fixed_property_set(transaction_id, name, value)
            parcel = encrypt_tx_parcel(self._keys.app_key, self._keys.app_iv, counter, plaintext)

            loop = asyncio.get_running_loop()
            response_future = loop.create_future()
            property_future = loop.create_future()
            self._pending_responses[transaction_id] = ((siid, piid), response_future)
            self._pending_values[(siid, piid)] = (value_type, value, property_future)
            self._active_tx_frames = frozenset((self.TX_HEADER, parcel))
            self._inbox = deque(item for item in self._inbox if item[0] != self.UUID_DATA_TX)
            try:
                await self._write_tx_frame(self.TX_HEADER)
                await self._wait_for(
                    lambda uuid, data: uuid == self.UUID_DATA_TX and data == self.RCV_RDY,
                    timeout=wait_timeout,
                )
                await self._write_tx_frame(parcel)
                await self._wait_for(
                    lambda uuid, data: uuid == self.UUID_DATA_TX and data == self.RCV_OK,
                    timeout=wait_timeout,
                )
                try:
                    result_code = await asyncio.wait_for(response_future, timeout=wait_timeout)
                    if result_code != 0:
                        raise S5ClientError("S5 rejected the property request")
                    await asyncio.wait_for(property_future, timeout=wait_timeout)
                except TimeoutError:
                    raise ProtocolTimeout("timed out waiting for S5 property response and read-back") from None
            finally:
                self._pending_responses.pop(transaction_id, None)
                self._pending_values.pop((siid, piid), None)
                self._active_tx_frames = frozenset()
                for future in (response_future, property_future):
                    if future.done() and not future.cancelled():
                        future.exception()
                    elif not future.done():
                        future.cancel()

    async def set_power(self, enabled: bool, *, timeout: float | None = None) -> None:
        if type(enabled) is not bool:
            raise TypeError("power state must be bool")
        await self._set_fixed_property("power", int(enabled), timeout=timeout)

    async def set_fragrance_out_time(self, value: int, *, timeout: float | None = None) -> None:
        await self._set_fixed_property("fragrance_out_time", value, timeout=timeout)

    async def set_idle_time(self, value: int, *, timeout: float | None = None) -> None:
        await self._set_fixed_property("idle_time", value, timeout=timeout)

    async def set_light(self, value: int, *, timeout: float | None = None) -> None:
        await self._set_fixed_property("light", value, timeout=timeout)

    async def set_color(self, value: int, *, timeout: float | None = None) -> None:
        await self._set_fixed_property("color", value, timeout=timeout)

    async def _write_tx_frame(self, data: bytes) -> None:
        if not self._authenticated or data not in self._active_tx_frames:
            raise S5ClientError("only the active fixed S5 transaction may write UUID 001A")
        await self._client.write_gatt_char(self.UUID_DATA_TX, data, response=False)
