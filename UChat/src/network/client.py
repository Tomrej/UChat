import sys
import json
import struct
from PySide6.QtCore import QObject, Signal, QCoreApplication
from PySide6.QtNetwork import QTcpSocket, QAbstractSocket


class NetworkClient(QObject):
    """Client module transmitting JSON formatted network frames over raw TCP sockets."""

    connected = Signal()
    disconnected = Signal()
    message_received = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.socket = QTcpSocket(self)
        self.buffer = bytearray()
        self.expected_len = None
        self._pending_payload = None

        self.socket.connected.connect(self._on_connected)
        self.socket.disconnected.connect(self.disconnected.emit)
        self.socket.readyRead.connect(self._on_ready_read)
        self.socket.errorOccurred.connect(self._on_error)

    def send_message(self, host: str, port: int, data_dict: dict) -> bool:
        """
        Connects to targeted host:port, transmits JSON frame, and gracefully disconnects.
        If socket is currently active or stuck, it aborts existing connection first.
        """
        if self.socket.state() != QAbstractSocket.SocketState.UnconnectedState:
            self.socket.abort()

        self.buffer.clear()
        self.expected_len = None
        self._pending_payload = data_dict

        print(f"[CLIENT] Connecting to {host}:{port}...")
        self.socket.connectToHost(host, port)
        return True

    def _on_connected(self):
        self.connected.emit()
        if self._pending_payload is not None:
            try:
                json_bytes = json.dumps(self._pending_payload, ensure_ascii=False).encode("utf-8")
                header = struct.pack(">I", len(json_bytes))
                packet = header + json_bytes

                written = self.socket.write(packet)
                self.socket.flush()
                print(f"[CLIENT] Sent {written} bytes (payload: {len(json_bytes)} B).")
            except Exception as err:
                error_str = f"Error sending message packet: {err}"
                print(f"[CLIENT ERROR] {error_str}")
                self.error_occurred.emit(error_str)
            finally:
                self._pending_payload = None
                # Flush and gracefully tear down connection after message transmission
                self.socket.disconnectFromHost()

    def _on_ready_read(self):
        """Processes responses received on client socket."""
        self.buffer.extend(self.socket.readAll().data())

        while True:
            if self.expected_len is None:
                if len(self.buffer) < 4:
                    break
                self.expected_len = struct.unpack(">I", self.buffer[:4])[0]
                del self.buffer[:4]

            if len(self.buffer) < self.expected_len:
                break

            payload_bytes = self.buffer[:self.expected_len]
            del self.buffer[:self.expected_len]
            self.expected_len = None

            try:
                json_str = payload_bytes.decode("utf-8")
                data = json.loads(json_str)
                self.message_received.emit(data)
            except (UnicodeDecodeError, json.JSONDecodeError) as err:
                print(f"[CLIENT WARN] Error decoding incoming response: {err}")

    def _on_error(self, socket_error):
        error_msg = self.socket.errorString()
        print(f"[CLIENT ERROR] {error_msg}")
        self.error_occurred.emit(error_msg)


if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    client = NetworkClient()

    client.connected.connect(lambda: print("[EVENT] Connected to host!"))
    client.send_message("127.0.0.1", 5000, {"test": "data"})

    sys.exit(app.exec())