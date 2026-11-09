import sys
import json
import struct
from PySide6.QtCore import QObject, Signal, QCoreApplication
from PySide6.QtNetwork import QTcpSocket, QAbstractSocket


class NetworkClient(QObject):
    """Client module responsible for transmitting unencrypted P2P messages."""

    connected = Signal()
    disconnected = Signal()
    message_received = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.socket = QTcpSocket(self)
        self.buffer = bytearray()
        self.expected_len = None

        self.socket.connected.connect(self.connected.emit)
        self.socket.disconnected.connect(self.disconnected.emit)
        self.socket.readyRead.connect(self._on_ready_read)
        self.socket.errorOccurred.connect(self._on_error)

    def connect_to_host(self, host: str, port: int):
        """Establishes an asynchronous TCP socket connection to a targeted peer host."""
        print(f"[CLIENT] Connecting to {host}:{port}...")
        self.socket.connectToHost(host, port)

    def disconnect_from_host(self):
        """Terminates active socket connection."""
        self.socket.disconnectFromHost()

    def send_message(self, data_dict: dict) -> bool:
        """
        Serializes a Python dictionary into JSON, prepends a 4-byte length header,
        and transmits the frame over the raw TCP socket.
        """
        if self.socket.state() != QAbstractSocket.SocketState.ConnectedState:
            print("[CLIENT ERROR] Message send failed – Socket is not connected.")
            self.error_occurred.emit("Socket is not connected.")
            return False

        try:
            json_bytes = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")
            # Create 4-byte header (Big-Endian unsigned integer)
            header = struct.pack(">I", len(json_bytes))

            packet = header + json_bytes
            written = self.socket.write(packet)
            self.socket.flush()

            print(f"[CLIENT] Sent {written} bytes (payload size: {len(json_bytes)} B).")
            return True
        except Exception as err:
            error_str = f"Error sending message packet: {err}"
            print(f"[CLIENT ERROR] {error_str}")
            self.error_occurred.emit(error_str)
            return False

    def _on_ready_read(self):
        """Processes incoming data or responses received from the peer host."""
        self.buffer.extend(self.socket.readAll().data())

        while True:
            # Parse 4-byte framing length header
            if self.expected_len is None:
                if len(self.buffer) < 4:
                    break
                self.expected_len = struct.unpack(">I", self.buffer[:4])[0]
                del self.buffer[:4]

            # Read full expected body length
            if len(self.buffer) < self.expected_len:
                break

            payload_bytes = self.buffer[:self.expected_len]
            del self.buffer[:self.expected_len]
            self.expected_len = None

            # Deserialize string payload to dictionary
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


# === STANDALONE CLIENT TEST (Phase 1) ===
if __name__ == "__main__":
    app = QCoreApplication(sys.argv)

    client = NetworkClient()

    def on_connected():
        print("[EVENT] Successfully connected to target peer!")

        # Unencrypted test payload mimicking invoice exchange
        sample_payload = {
            "version": "1.0",
            "msg_type": "INVOICE",
            "sender_id": "Company A",
            "payload": {
                "account_number": "123456789/0800",
                "amount": 250000,
                "currency": "CZK",
                "note": "Payment for server racks"
            },
            "security_metadata": {
                "hash": "",
                "hmac": "",
                "signature": ""
            }
        }
        client.send_message(sample_payload)

    def on_error(msg):
        print(f"[EVENT ERROR] {msg}")
        app.quit()

    client.connected.connect(on_connected)
    client.error_occurred.connect(on_error)
    client.disconnected.connect(lambda: print("[EVENT] Disconnected from peer host."))

    # Connect to local test server instance
    client.connect_to_host("127.0.0.1", 5000)

    sys.exit(app.exec())