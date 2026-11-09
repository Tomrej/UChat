from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Signal


class ChatTab(QWidget):
    """Tab interface for real-time text chatting."""

    send_message_requested = Signal(str)  # Emits raw message text to be transmitted

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Chat history display area
        layout.addWidget(QLabel("Chat History:"))
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Message input row
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.returnPressed.connect(self._on_send)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._on_send)

        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

    def _on_send(self):
        text = self.msg_input.text().strip()
        if text:
            self.send_message_requested.emit(text)
            self.append_message("Me", text)
            self.msg_input.clear()

    def append_message(self, sender: str, text: str):
        """Appends a new formatted message line to the display."""
        self.chat_display.append(f"<b>[{sender}]</b>: {text}")