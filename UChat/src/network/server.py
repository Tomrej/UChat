import sys
import json
import struct
from PySide6.QtCore import QObject, Signal, QCoreApplication
from PySide6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress


class ClientHandler(QObject):
    """Handles communication with a single connected peer client."""

    message_received = Signal(dict, str)  # Emits (data_dict, sender_ip)
    disconnected = Signal(str)            # Emits (sender_ip)

    def __init__(self, socket: QTcpSocket, parent=None):
        super().__init__(parent)
        self.socket = socket
        self.peer_ip = socket.peerAddress().toString()
        self.buffer = bytearray()
        self.expected_len = None

        self.socket.readyRead.connect(self._on_ready_read)
        self.socket.disconnected.connect(self._on_disconnected)

    def _on_ready_read(self):
        # Append incoming raw bytes to the internal buffer
        self.buffer.extend(self.socket.readAll().data())

        while True:
            # Step 1: Parse the 4-byte Big-Endian length header
            if self.expected_len is None:
                if len(self.buffer) < 4:
                    break  # Wait for full header to arrive
                self.expected_len = struct.unpack(">I", self.buffer[:4])[0]
                del self.buffer[:4]

            # Step 2: Read the complete JSON payload body
            if len(self.buffer) < self.expected_len:
                break  # Wait for remaining payload bytes

            payload_bytes = self.buffer[:self.expected_len]
            del self.buffer[:self.expected_len]
            self.expected_len = None

            # Step 3: Deserialize the raw JSON packet
            try:
                json_str = payload_bytes.decode("utf-8")
                data = json.loads(json_str)
                self.message_received.emit(data, self.peer_ip)
            except (UnicodeDecodeError, json.JSONDecodeError) as err:
                print(f"[SERVER WARN] Decoding error from {self.peer_ip}: {err}")

    def _on_disconnected(self):
        self.disconnected.emit(self.peer_ip)
        self.socket.deleteLater()


class NetworkServer(QObject):
    """Main P2P network server component accepting incoming TCP connections."""

    message_received = Signal(dict, str)  # Emits (data_dict, sender_ip)
    client_connected = Signal(str)        # Emits (client_ip)
    client_disconnected = Signal(str)     # Emits (client_ip)
    server_error = Signal(str)

    def __init__(self, host: str = "0.0.0.0", port: int = 5000, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.server = QTcpServer(self)
        self.clients: list[ClientHandler] = []

        self.server.newConnection.connect(self._on_new_connection)

    def start(self) -> bool:
        """Starts listening for incoming peer connections on the host and port."""
        address = QHostAddress(self.host)
        if self.server.listen(address, self.port):
            print(f"[SERVER] Listening on {self.host}:{self.port}")
            return True
        else:
            error_msg = self.server.errorString()
            print(f"[SERVER ERROR] Failed to start server: {error_msg}")
            self.server_error.emit(error_msg)
            return False

    def stop(self):
        """Stops the server and closes all active peer connections."""
        self.server.close()
        print("[SERVER] Server stopped.")

    def _on_new_connection(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            handler = ClientHandler(socket, self)

            client_ip = socket.peerAddress().toString()
            print(f"[SERVER] Incoming connection from {client_ip}:{socket.peerPort()}")

            handler.message_received.connect(self.message_received.emit)
            handler.disconnected.connect(self._handle_client_disconnect)
            handler.disconnected.connect(self.client_disconnected.emit)

            self.clients.append(handler)
            self.client_connected.emit(client_ip)

    def _handle_client_disconnect(self, client_ip: str):
        print(f"[SERVER] Client {client_ip} disconnected.")
        self.clients = [c for c in self.clients if c.peer_ip != client_ip]


# === STANDALONE SERVER TEST (Phase 1) ===
if __name__ == "__main__":
    app = QCoreApplication(sys.argv)

    server = NetworkServer(host="0.0.0.0", port=5000)

    def on_message(data: dict, sender: str):
        print(f"\n[RECEIVED MESSAGE from {sender}]:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    server.message_received.connect(on_message)
    server.client_connected.connect(lambda ip: print(f"[EVENT] Connected: {ip}"))
    server.client_disconnected.connect(lambda ip: print(f"[EVENT] Disconnected: {ip}"))

    if server.start():
        print("Press Ctrl+C to terminate...")
        sys.exit(app.exec())