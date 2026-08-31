"""
Minimal WebSocket client built on the standard library only.

Implements just enough of RFC 6455 for the Ark ASR service: a TLS handshake
with custom headers, plus binary frame send/receive. This keeps the skill
dependency-free (no `websockets` package required).

@license MIT
"""

from __future__ import annotations

import base64
import os
import socket
import ssl
import struct
import threading
from typing import Optional
from urllib.parse import urlparse

# RFC 6455 opcodes
OP_CONTINUATION = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

_HANDSHAKE_BUFFER_LIMIT = 65536


class WebSocketError(RuntimeError):
    """Raised when the handshake fails or the peer sends a malformed frame."""


class WebSocket:
    """A blocking client for a single WebSocket conversation."""

    def __init__(self, url: str, headers: dict[str, str], timeout: float = 30.0):
        parsed = urlparse(url)
        if parsed.scheme not in ("ws", "wss"):
            raise WebSocketError(f"Unsupported scheme: {parsed.scheme}")

        secure = parsed.scheme == "wss"
        port = parsed.port or (443 if secure else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        self._sock = socket.create_connection((parsed.hostname, port), timeout=timeout)
        if secure:
            context = ssl.create_default_context()
            self._sock = context.wrap_socket(
                self._sock, server_hostname=parsed.hostname
            )
        self._buffer = b""
        self._send_lock = threading.Lock()
        self.response_headers: dict[str, str] = {}
        self._handshake(parsed.hostname, port, path, headers)

    # ------------------------------------------------------------------
    # Handshake
    # ------------------------------------------------------------------

    def _handshake(
        self, host: str, port: int, path: str, headers: dict[str, str]
    ) -> None:
        nonce = base64.b64encode(os.urandom(16)).decode()
        lines = [
            f"GET {path} HTTP/1.1",
            f"Host: {host}:{port}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {nonce}",
            "Sec-WebSocket-Version: 13",
        ]
        lines += [f"{key}: {value}" for key, value in headers.items()]
        self._sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())

        # Read until the end of the header block.
        while b"\r\n\r\n" not in self._buffer:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise WebSocketError("Connection closed during handshake")
            self._buffer += chunk
            if len(self._buffer) > _HANDSHAKE_BUFFER_LIMIT:
                raise WebSocketError("Handshake response too large")

        raw_head, self._buffer = self._buffer.split(b"\r\n\r\n", 1)
        head = raw_head.decode("utf-8", "replace").split("\r\n")
        if "101" not in head[0]:
            raise WebSocketError(f"Handshake failed: {head[0]}\n" + "\n".join(head[1:]))
        for line in head[1:]:
            if ":" in line:
                name, _, value = line.partition(":")
                self.response_headers[name.strip().lower()] = value.strip()

    # ------------------------------------------------------------------
    # Frame IO
    # ------------------------------------------------------------------

    def send(self, payload: bytes, opcode: int = OP_BINARY) -> None:
        """Send one masked, unfragmented frame (clients must always mask).

        Guarded by a lock so a sender thread and the receiving thread cannot
        interleave bytes on the same socket.
        """
        header = bytearray([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack(">H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack(">Q", length))

        mask = os.urandom(4)
        masked = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
        with self._send_lock:
            self._sock.sendall(bytes(header) + mask + masked)

    def _read_exactly(self, count: int) -> bytes:
        while len(self._buffer) < count:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise WebSocketError("Connection closed by peer")
            self._buffer += chunk
        data, self._buffer = self._buffer[:count], self._buffer[count:]
        return data

    def recv(self) -> Optional[bytes]:
        """Return the next application message, or None once the peer closes.

        Continuation frames are reassembled; control frames are handled inline.
        """
        message = bytearray()
        while True:
            first, second = self._read_exactly(2)
            final = bool(first & 0x80)
            opcode = first & 0x0F
            length = second & 0x7F

            if length == 126:
                (length,) = struct.unpack(">H", self._read_exactly(2))
            elif length == 127:
                (length,) = struct.unpack(">Q", self._read_exactly(8))

            # Servers must not mask, but tolerate it defensively.
            mask = self._read_exactly(4) if second & 0x80 else None
            payload = self._read_exactly(length) if length else b""
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

            if opcode == OP_CLOSE:
                return None
            if opcode == OP_PING:
                self.send(payload, OP_PONG)
                continue
            if opcode == OP_PONG:
                continue

            message.extend(payload)
            if final:
                return bytes(message)

    def close(self) -> None:
        """Send a close frame and tear down the socket, ignoring teardown errors."""
        try:
            self.send(struct.pack(">H", 1000), OP_CLOSE)
        except OSError:
            pass
        finally:
            self._sock.close()

    def __enter__(self) -> "WebSocket":
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()
