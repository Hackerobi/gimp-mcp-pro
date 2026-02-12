"""Tests for GimpBridge communication layer."""

import json
import socket
import struct
import threading
import pytest

from gimp_mcp_pro.bridge import GimpBridge, HEADER_SIZE
from gimp_mcp_pro.utils.errors import GimpCommandError, GimpConnectionError


class MockGimpServer:
    """A mock GIMP plugin socket server for testing."""

    def __init__(self, host='localhost', port=0, use_length_prefix=True):
        self.host = host
        self.use_length_prefix = use_length_prefix
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.running = False
        self.response_queue: list[dict] = []
        self.received_requests: list[dict] = []

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def queue_response(self, response: dict):
        self.response_queue.append(response)

    def _serve(self):
        self.sock.settimeout(1.0)
        while self.running:
            try:
                client, _ = self.sock.accept()
                self._handle(client)
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle(self, client):
        try:
            while self.running and self.response_queue:
                if self.use_length_prefix:
                    header = self._recv_exact(client, HEADER_SIZE)
                    if not header:
                        break
                    length = struct.unpack('>I', header)[0]
                    data = self._recv_exact(client, length)
                    if not data:
                        break
                    self.received_requests.append(json.loads(data.decode('utf-8')))
                else:
                    data = client.recv(65536)
                    if not data:
                        break
                    self.received_requests.append(json.loads(data.decode('utf-8')))

                if self.response_queue:
                    response = self.response_queue.pop(0)
                    payload = json.dumps(response).encode('utf-8')
                    if self.use_length_prefix:
                        client.sendall(struct.pack('>I', len(payload)) + payload)
                    else:
                        client.sendall(payload)
        finally:
            client.close()

    def _recv_exact(self, sock, n):
        data = bytearray()
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data.extend(chunk)
        return bytes(data)


class TestGimpBridgeConnection:
    def test_connect_success(self):
        server = MockGimpServer()
        server.start()
        try:
            bridge = GimpBridge(host='localhost', port=server.port)
            bridge.connect()
            assert bridge.connected
            bridge.disconnect()
            assert not bridge.connected
        finally:
            server.stop()

    def test_connect_failure_raises(self):
        bridge = GimpBridge(host='localhost', port=1, timeout=0.5)
        with pytest.raises(GimpConnectionError):
            bridge.connect()

    def test_context_manager(self):
        server = MockGimpServer()
        server.start()
        try:
            with GimpBridge(host='localhost', port=server.port) as bridge:
                assert bridge.connected
            assert not bridge.connected
        finally:
            server.stop()

    def test_disconnect_idempotent(self):
        bridge = GimpBridge()
        bridge.disconnect()  # Should not raise
        bridge.disconnect()


class TestGimpBridgeCommunication:
    def test_send_command_length_prefixed(self):
        server = MockGimpServer(use_length_prefix=True)
        server.queue_response({"status": "success", "results": {"key": "value"}})
        server.start()
        try:
            bridge = GimpBridge(host='localhost', port=server.port, use_length_prefix=True)
            bridge.connect()
            result = bridge.send_command("test_command", {"arg": 1})
            assert result["status"] == "success"
            assert result["results"]["key"] == "value"
        finally:
            server.stop()

    def test_send_command_json_fallback(self):
        server = MockGimpServer(use_length_prefix=False)
        server.queue_response({"status": "success", "results": "ok"})
        server.start()
        try:
            bridge = GimpBridge(host='localhost', port=server.port, use_length_prefix=False)
            bridge.connect()
            result = bridge.send_command("test", {})
            assert result["status"] == "success"
        finally:
            server.stop()

    def test_error_response_raises(self):
        server = MockGimpServer()
        server.queue_response({"status": "error", "error": "something broke"})
        server.start()
        try:
            bridge = GimpBridge(host='localhost', port=server.port)
            bridge.connect()
            with pytest.raises(GimpCommandError, match="something broke"):
                bridge.send_command("bad_cmd")
        finally:
            server.stop()

    def test_command_id_increments(self):
        server = MockGimpServer()
        server.queue_response({"status": "success", "results": {}})
        server.queue_response({"status": "success", "results": {}})
        server.start()
        try:
            bridge = GimpBridge(host='localhost', port=server.port)
            bridge.connect()
            bridge.send_command("cmd1")
            bridge.send_command("cmd2")

            assert len(server.received_requests) == 2
            assert server.received_requests[0]["id"] == 1
            assert server.received_requests[1]["id"] == 2
        finally:
            server.stop()

    def test_execute_python_convenience(self):
        server = MockGimpServer()
        server.queue_response({"status": "success", "results": ["6\n"]})
        server.start()
        try:
            bridge = GimpBridge(host='localhost', port=server.port)
            bridge.connect()
            result = bridge.execute_python(["print(2+4)"])
            assert result["results"] == ["6\n"]

            req = server.received_requests[0]
            assert req["type"] == "exec"
            assert req["params"]["args"][0] == "pyGObject-console"
            assert req["params"]["args"][1] == ["print(2+4)"]
        finally:
            server.stop()
