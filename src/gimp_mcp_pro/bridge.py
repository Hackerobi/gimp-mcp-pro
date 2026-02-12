"""GimpBridge — reliable communication layer between MCP server and GIMP plugin.

Key improvements over existing implementations:
- Length-prefixed framing (no more JSON boundary guessing)
- Persistent connection (no socket-per-command overhead)
- Automatic reconnection with exponential backoff
- Thread-safe send/receive with locking
- Configurable timeouts per command
- Fallback to JSON boundary detection for backward compatibility
"""

from __future__ import annotations

import json
import logging
import socket
import struct
import threading
import time
from typing import Any

from gimp_mcp_pro.utils.errors import (
    GimpCommandError,
    GimpConnectionError,
    GimpTimeoutError,
)

logger = logging.getLogger("gimp_mcp_pro.bridge")

# Protocol constants
HEADER_SIZE = 4  # 4-byte big-endian uint32 length prefix
MAX_MESSAGE_SIZE = 100 * 1024 * 1024  # 100 MB max (for base64 image data)
DEFAULT_TIMEOUT = 30.0
LONG_TIMEOUT = 120.0  # For filters, exports, large operations
RECONNECT_DELAYS = [0.5, 1.0, 2.0, 4.0, 8.0]  # Exponential backoff


class GimpBridge:
    """Manages TCP socket communication with the GIMP plugin.

    Usage:
        bridge = GimpBridge(host='localhost', port=9877)
        bridge.connect()

        # Send a typed command
        result = bridge.send_command("get_image_metadata")

        # Execute raw Python in GIMP
        result = bridge.execute_python([
            "images = Gimp.get_images()",
            "print(len(images))"
        ])
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9877,
        timeout: float = DEFAULT_TIMEOUT,
        use_length_prefix: bool = True,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_length_prefix = use_length_prefix

        self._sock: socket.socket | None = None
        self._lock = threading.Lock()
        self._command_id = 0
        self._connected = False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._connected and self._sock is not None

    def connect(self) -> None:
        """Connect to the GIMP plugin socket with retry logic."""
        if self._connected and self._sock is not None:
            return

        last_error: Exception | None = None
        for delay in RECONNECT_DELAYS:
            try:
                self._do_connect()
                return
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Connection attempt failed: {e}. Retrying in {delay}s..."
                )
                time.sleep(delay)

        # Final attempt
        try:
            self._do_connect()
        except Exception as e:
            raise GimpConnectionError(
                f"Could not connect to GIMP at {self.host}:{self.port} "
                f"after {len(RECONNECT_DELAYS) + 1} attempts. "
                f"Ensure the GIMP MCP plugin is running. Last error: {e}"
            ) from e

    def _do_connect(self) -> None:
        """Perform a single connection attempt."""
        self.disconnect()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        self._sock = sock
        self._connected = True
        logger.info(f"Connected to GIMP at {self.host}:{self.port}")

    def disconnect(self) -> None:
        """Close the connection."""
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self._connected = False

    def ensure_connected(self) -> None:
        """Ensure we have an active connection, reconnecting if needed."""
        if not self.connected:
            self.connect()

    # ------------------------------------------------------------------
    # Command sending
    # ------------------------------------------------------------------

    def _next_id(self) -> int:
        self._command_id += 1
        return self._command_id

    def send_command(
        self,
        command_type: str,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Send a command to GIMP and wait for the response."""
        effective_timeout = timeout or self.timeout

        with self._lock:
            self.ensure_connected()
            assert self._sock is not None

            self._sock.settimeout(effective_timeout)

            cmd_id = self._next_id()
            payload = {
                "id": cmd_id,
                "type": command_type,
                "params": params or {},
            }

            try:
                self._send(payload)
                response = self._receive()
            except socket.timeout as e:
                self.disconnect()
                raise GimpTimeoutError(
                    f"Command '{command_type}' timed out after {effective_timeout}s",
                    timeout_seconds=effective_timeout,
                ) from e
            except (ConnectionError, OSError, BrokenPipeError) as e:
                self.disconnect()
                raise GimpConnectionError(
                    f"Connection lost while executing '{command_type}': {e}"
                ) from e

        if isinstance(response, dict) and response.get("status") == "error":
            raise GimpCommandError(
                message=response.get("error", "Unknown GIMP error"),
                command=command_type,
                traceback=response.get("traceback"),
            )

        return response

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def execute_python(
        self,
        code_lines: list[str],
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Execute Python code in GIMP's PyGObject console."""
        return self.send_command(
            "exec",
            {"args": ["pyGObject-console", code_lines]},
            timeout=timeout,
        )

    def evaluate_python(
        self,
        expressions: list[str],
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Evaluate Python expressions in GIMP and return their values."""
        return self.send_command(
            "exec",
            {"args": ["pyGObject-eval", expressions]},
            timeout=timeout,
        )

    def get_image_bitmap(
        self,
        max_width: int | None = None,
        max_height: int | None = None,
        region: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """Get the current image as base64 PNG data."""
        params: dict[str, Any] = {}
        if max_width is not None:
            params["max_width"] = max_width
        if max_height is not None:
            params["max_height"] = max_height
        if region is not None:
            params["region"] = region
        return self.send_command(
            "get_image_bitmap",
            params,
            timeout=LONG_TIMEOUT,
        )

    def get_image_metadata(self) -> dict[str, Any]:
        """Get metadata about the current image (no bitmap transfer)."""
        return self.send_command("get_image_metadata")

    def get_context_state(self) -> dict[str, Any]:
        """Get GIMP's current context (colors, brush, opacity, etc.)."""
        return self.send_command("get_context_state")

    def get_gimp_info(self) -> dict[str, Any]:
        """Get GIMP environment information."""
        return self.send_command("get_gimp_info")

    # ------------------------------------------------------------------
    # Wire protocol
    # ------------------------------------------------------------------

    def _send(self, payload: dict[str, Any]) -> None:
        """Send a JSON payload with length-prefix framing."""
        assert self._sock is not None
        data = json.dumps(payload).encode("utf-8")

        if self.use_length_prefix:
            header = struct.pack(">I", len(data))
            self._sock.sendall(header + data)
        else:
            self._sock.sendall(data)

    def _receive(self) -> dict[str, Any]:
        """Receive a JSON response."""
        assert self._sock is not None

        if self.use_length_prefix:
            return self._receive_length_prefixed()
        else:
            return self._receive_json_boundary()

    def _receive_length_prefixed(self) -> dict[str, Any]:
        """Receive using 4-byte length prefix."""
        assert self._sock is not None

        header = self._recv_exact(HEADER_SIZE)
        length = struct.unpack(">I", header)[0]

        if length > MAX_MESSAGE_SIZE:
            raise GimpConnectionError(
                f"Message size {length} exceeds maximum {MAX_MESSAGE_SIZE}"
            )

        data = self._recv_exact(length)
        return json.loads(data.decode("utf-8"))

    def _receive_json_boundary(self) -> dict[str, Any]:
        """Receive by detecting JSON boundaries (fallback mode)."""
        assert self._sock is not None

        buffer = b""
        while True:
            chunk = self._sock.recv(8192)
            if not chunk:
                if buffer:
                    try:
                        return json.loads(buffer.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                raise GimpConnectionError("Connection closed by GIMP plugin")

            buffer += chunk

            try:
                return json.loads(buffer.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

    def _recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes from the socket."""
        assert self._sock is not None

        data = bytearray()
        while len(data) < n:
            remaining = n - len(data)
            chunk = self._sock.recv(min(remaining, 65536))
            if not chunk:
                raise GimpConnectionError(
                    f"Connection closed while reading "
                    f"(got {len(data)} of {n} bytes)"
                )
            data.extend(chunk)
        return bytes(data)

    def __enter__(self) -> GimpBridge:
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        self.disconnect()
