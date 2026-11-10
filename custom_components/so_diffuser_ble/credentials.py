"""Validate a standalone 12-byte SO diffuser token file for offline tools."""
from __future__ import annotations

import errno
import os
import stat
from pathlib import Path

from .protocol import decode_token_hex


class TokenFileError(ValueError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        messages = {
            "missing": "SO diffuser token file is missing",
            "permissions": "SO diffuser token file must have mode 0600 or stricter",
            "type": "SO diffuser token file must be a regular file",
            "format": "SO diffuser token file must contain exactly 24 hexadecimal characters with no newline",
        }
        super().__init__(messages.get(reason, "S5 token file is invalid"))


def load_token_file(path: str | Path) -> bytes:
    try:
        fd = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
        )
    except FileNotFoundError:
        raise TokenFileError("missing") from None
    except OSError as exc:
        if exc.errno in (errno.EACCES, errno.EPERM):
            raise TokenFileError("permissions") from None
        reason = "missing" if exc.errno == errno.ENOENT else "type"
        raise TokenFileError(reason) from None

    with os.fdopen(fd, "r", encoding="ascii") as token_file:
        metadata = os.fstat(token_file.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise TokenFileError("type")
        mode = stat.S_IMODE(metadata.st_mode)
        if not mode & stat.S_IRUSR or mode & (0o077 | 0o111):
            raise TokenFileError("permissions")
        try:
            value = token_file.read(25)
        except UnicodeDecodeError:
            raise TokenFileError("format") from None

    try:
        return decode_token_hex(value)
    except ValueError:
        raise TokenFileError("format") from None
