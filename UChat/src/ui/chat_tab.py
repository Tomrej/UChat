import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFileDialog, QListWidget, QListWidgetItem, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal

# Maximum allowed file attachment size in Megabytes to prevent memory exhaustion
MAX_FILE_SIZE_MB = 200


class ChatTab(QWidget):
    """Tab interface for real-time text chatting and file sharing."""

    # Emits (message_text, optional_file_path)
    send_message_requested = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file_path = None
        self.received_files_data = {}  # Map of file_id -> (file_name, bytes)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Chat history display area
        layout.addWidget(QLabel("<b>Chat History:</b>"))
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display, stretch=1)

        # File attachment status bar
        self.attachment_label = QLabel("No file attached.")
        self.attachment_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.attachment_label)

        # Message input row
        input_layout = QHBoxLayout()

        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.returnPressed.connect(self._on_send)

        self.attach_btn = QPushButton("Attach File")
        self.attach_btn.clicked.connect(self._on_attach_file)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._on_send)

        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.attach_btn)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Compact Received Attachments List Group
        files_group = QGroupBox("Received Chat Attachments")
        files_layout = QHBoxLayout(files_group)
        files_layout.setContentsMargins(8, 8, 8, 8)

        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(90)
        files_layout.addWidget(self.files_list)

        self.save_file_btn = QPushButton("Save Selected File")
        self.save_file_btn.clicked.connect(self._on_save_received_file)
        files_layout.addWidget(self.save_file_btn)

        layout.addWidget(files_group, stretch=0)

    def _on_attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Send")
        if file_path:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                QMessageBox.warning(
                    self, "File Too Large",
                    f"Selected file size ({size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_FILE_SIZE_MB} MB."
                )
                return

            self.selected_file_path = file_path
            filename = os.path.basename(file_path)
            self.attachment_label.setText(f"Attached: {filename} ({size_mb:.1f} MB)")
        else:
            self.selected_file_path = None
            self.attachment_label.setText("No file attached.")

    def _on_send(self):
        text = self.msg_input.text().strip()
        if text or self.selected_file_path:
            file_path = self.selected_file_path
            self.send_message_requested.emit(text, file_path)

            file_info = ""
            if file_path:
                file_info = f" <i>[Attached file: {os.path.basename(file_path)}]</i>"

            self.append_message("Me", f"{text}{file_info}")

            # Reset input fields
            self.msg_input.clear()
            self.selected_file_path = None
            self.attachment_label.setText("No file attached.")

    def append_message(self, sender: str, text: str):
        """Appends a new formatted message line to the display."""
        self.chat_display.append(f"<b>[{sender}]</b>: {text}")

    def add_received_file(self, filename: str, file_bytes: bytes, sender: str):
        """Registers a received attachment and adds it to the saveable list."""
        file_key = f"{sender}_{filename}_{len(self.received_files_data)}"
        self.received_files_data[file_key] = (filename, file_bytes)

        display_item = QListWidgetItem(f"📄 {filename} ({len(file_bytes) / 1024:.1f} KB) - from {sender}")
        display_item.setData(32, file_key)
        self.files_list.addItem(display_item)

    def _on_save_received_file(self):
        current_item = self.files_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Select File", "Please select a file from the list to save.")
            return

        file_key = current_item.data(32)
        if file_key in self.received_files_data:
            filename, file_bytes = self.received_files_data[file_key]
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Received File", filename)
            if save_path:
                try:
                    with open(save_path, "wb") as f:
                        f.write(file_bytes)
                    QMessageBox.information(self, "Saved", f"File saved successfully to:\n{save_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Save Error", f"Failed to save file: {e}")