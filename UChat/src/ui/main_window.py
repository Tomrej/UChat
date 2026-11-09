import os
import base64
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTabWidget, QStatusBar, QMessageBox, QFrame
)
from PySide6.QtCore import Slot

from src.network.server import NetworkServer
from src.network.client import NetworkClient
from src.ui.chat_tab import ChatTab
from src.ui.mail_tab import MailTab


class MainWindow(QMainWindow):
    """Main application window connecting network engines to UI components."""

    def __init__(self, listen_port: int = 5000):
        super().__init__()
        self.listen_port = listen_port
        self.setWindowTitle(f"CryptoLab Peer - Unsecured Baseline (Listening on :{self.listen_port})")
        self.resize(900, 700)

        # Initialize network components
        self.server = NetworkServer(host="0.0.0.0", port=self.listen_port)
        self.client = NetworkClient()

        # Build UI layout
        self._init_ui()
        self._bind_signals()

        # Start listening server socket
        self._start_server()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Networking Control Header Panel
        conn_layout = QHBoxLayout()

        # Local Server Binding Configuration
        conn_layout.addWidget(QLabel("<b>My Port:</b>"))
        self.local_port_input = QLineEdit(str(self.listen_port))
        self.local_port_input.setFixedWidth(60)
        conn_layout.addWidget(self.local_port_input)

        self.bind_port_btn = QPushButton("Bind Port")
        self.bind_port_btn.clicked.connect(self._restart_server)
        conn_layout.addWidget(self.bind_port_btn)

        # Vertical Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        conn_layout.addWidget(line)

        # Remote Peer Destination Configuration
        conn_layout.addWidget(QLabel("<b>Target IP:</b>"))
        self.target_ip_input = QLineEdit("127.0.0.1")
        conn_layout.addWidget(self.target_ip_input)

        conn_layout.addWidget(QLabel("<b>Target Port:</b>"))
        self.target_port_input = QLineEdit("5001" if self.listen_port == 5000 else "5000")
        self.target_port_input.setFixedWidth(60)
        conn_layout.addWidget(self.target_port_input)

        main_layout.addLayout(conn_layout)

        # Main Navigation Tabs
        self.tabs = QTabWidget()
        self.chat_tab = ChatTab()
        self.mail_tab = MailTab()

        self.tabs.addTab(self.chat_tab, "Live Chat")
        self.tabs.addTab(self.mail_tab, "Mail & Invoices")
        main_layout.addWidget(self.tabs)

        self.setStatusBar(QStatusBar())

    def _bind_signals(self):
        # Server network signals
        self.server.message_received.connect(self._on_message_received)

        # Tab user action signals
        self.chat_tab.send_message_requested.connect(self._send_chat_message)
        self.mail_tab.send_invoice_requested.connect(self._send_invoice_document)

        # Network client error handling
        self.client.error_occurred.connect(
            lambda err: self.statusBar().showMessage(f"Network Error: {err}")
        )

    def _start_server(self):
        if self.server.start():
            self.setWindowTitle(f"CryptoLab Peer - Unsecured Baseline (Listening on :{self.listen_port})")
            self.statusBar().showMessage(f"Server active on port {self.listen_port} | Mode: Unencrypted Plaintext")
        else:
            QMessageBox.critical(
                self, "Socket Bind Error",
                f"Failed to start local TCP server on port {self.listen_port}.\n"
                "Port might be in use by another application or instance."
            )

    def _restart_server(self):
        try:
            new_port = int(self.local_port_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Local port must be a valid integer.")
            return

        self.server.stop()
        self.listen_port = new_port
        self.server.port = new_port
        self._start_server()

    @Slot(str, object)
    def _send_chat_message(self, text: str, file_path: str = None):
        target_ip = self.target_ip_input.text().strip()
        try:
            target_port = int(self.target_port_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Target port must be an integer value.")
            return

        payload = {
            "message": text,
            "has_file": False,
            "file_name": "",
            "file_size": 0,
            "file_data_b64": ""
        }

        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    raw_bytes = f.read()
                payload["has_file"] = True
                payload["file_name"] = os.path.basename(file_path)
                payload["file_size"] = len(raw_bytes)
                payload["file_data_b64"] = base64.b64encode(raw_bytes).decode("utf-8")
            except Exception as err:
                QMessageBox.critical(self, "File Read Error", f"Failed to read attached file: {err}")
                return

        packet = {
            "version": "1.0",
            "msg_type": "CHAT",
            "sender_id": f"Peer:{self.listen_port}",
            "payload": payload,
            "security_metadata": {}
        }

        self.client.send_message(target_ip, target_port, packet)

    @Slot(dict, object)
    def _send_invoice_document(self, invoice_data: dict, file_path: str = None):
        target_ip = self.target_ip_input.text().strip()
        try:
            target_port = int(self.target_port_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Target port must be an integer value.")
            return

        payload = dict(invoice_data)
        payload["has_file"] = False
        payload["file_name"] = ""
        payload["file_size"] = 0
        payload["file_data_b64"] = ""

        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    raw_bytes = f.read()
                payload["has_file"] = True
                payload["file_name"] = os.path.basename(file_path)
                payload["file_size"] = len(raw_bytes)
                payload["file_data_b64"] = base64.b64encode(raw_bytes).decode("utf-8")
            except Exception as err:
                QMessageBox.critical(self, "File Read Error", f"Failed to read attached document: {err}")
                return

        packet = {
            "version": "1.0",
            "msg_type": "INVOICE",
            "sender_id": invoice_data.get("sender_id", f"Company-{self.listen_port}"),
            "payload": payload,
            "security_metadata": {
                "hash": "",
                "hmac": "",
                "signature": ""
            }
        }

        self.client.send_message(target_ip, target_port, packet)

    @Slot(dict, str)
    def _on_message_received(self, data: dict, sender_ip: str):
        msg_type = data.get("msg_type", "")
        payload = data.get("payload", {})
        sender_label = data.get("sender_id", sender_ip)

        file_bytes = None
        if payload.get("has_file", False) and payload.get("file_data_b64"):
            try:
                file_bytes = base64.b64decode(payload.get("file_data_b64"))
            except Exception as err:
                print(f"[WARN] Failed to decode Base64 attachment: {err}")

        if msg_type == "CHAT":
            msg_text = payload.get("message", "")
            if file_bytes and payload.get("file_name"):
                filename = payload.get("file_name")
                self.chat_tab.add_received_file(filename, file_bytes, sender_label)
                msg_text += f" <i>[Attached file: {filename}]</i>"

            self.chat_tab.append_message(sender_label, msg_text)
            self.statusBar().showMessage(f"New chat message received from {sender_label}")

        elif msg_type == "INVOICE":
            self.mail_tab.add_received_invoice(data, file_bytes)
            self.statusBar().showMessage(f"New document received from {sender_label}")