import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QHBoxLayout,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QFileDialog, QMessageBox, QTextEdit
)
from PySide6.QtCore import Signal, Qt

# Maximum allowed file attachment size in Megabytes to prevent memory exhaustion
MAX_FILE_SIZE_MB = 25


class MailTab(QWidget):
    """Tab interface for drafting, sending, and reading emails with file attachments."""

    # Emits (mail_data_dict, optional_file_path)
    send_mail_requested = Signal(dict, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_doc_path = None
        self.inbox_files_data = {}  # Map of row_index -> (file_name, bytes)
        self.inbox_bodies = {}      # Map of row_index -> full email body text
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Email Drafting Group
        form_group = QGroupBox("Draft New Email")
        form_layout = QFormLayout(form_group)

        self.sender_input = QLineEdit("Company A")
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Enter email subject...")

        # Multi-line text field for email body
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Type your email message content here...")
        self.body_input.setMaximumHeight(110)

        # File Attachment Row
        doc_attach_layout = QHBoxLayout()
        self.doc_path_label = QLabel("No document file attached.")
        self.doc_path_label.setStyleSheet("color: #666; font-style: italic;")

        self.attach_doc_btn = QPushButton("Browse Attachment...")
        self.attach_doc_btn.clicked.connect(self._on_browse_document)
        doc_attach_layout.addWidget(self.doc_path_label)
        doc_attach_layout.addWidget(self.attach_doc_btn)

        form_layout.addRow("Sender Identity:", self.sender_input)
        form_layout.addRow("Subject:", self.subject_input)
        form_layout.addRow("Message Body:", self.body_input)
        form_layout.addRow("Attached File:", doc_attach_layout)

        self.send_btn = QPushButton("Send Email (Unencrypted)")
        self.send_btn.clicked.connect(self._on_send)
        form_layout.addRow(self.send_btn)

        layout.addWidget(form_group)

        # Received Emails Group (Inbox)
        inbox_group = QGroupBox("Received Emails (Inbox)")
        inbox_layout = QVBoxLayout(inbox_group)

        self.inbox_table = QTableWidget(0, 4)
        self.inbox_table.setHorizontalHeaderLabels([
            "Sender", "Subject", "Body Preview", "Attached File"
        ])
        self.inbox_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inbox_table.doubleClicked.connect(self._on_view_full_email)
        inbox_layout.addWidget(self.inbox_table)

        inbox_controls = QHBoxLayout()
        self.view_email_btn = QPushButton("View Full Email")
        self.view_email_btn.clicked.connect(self._on_view_full_email)

        self.download_attachment_btn = QPushButton("Save Attachment")
        self.download_attachment_btn.clicked.connect(self._on_save_inbox_attachment)

        inbox_controls.addWidget(self.view_email_btn)
        inbox_controls.addStretch()
        inbox_controls.addWidget(self.download_attachment_btn)
        inbox_layout.addLayout(inbox_controls)

        layout.addWidget(inbox_group)

    def _on_browse_document(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Email Attachment")
        if file_path:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                QMessageBox.warning(
                    self, "File Too Large",
                    f"Selected file size ({size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_FILE_SIZE_MB} MB."
                )
                return

            self.selected_doc_path = file_path
            filename = os.path.basename(file_path)
            self.doc_path_label.setText(f"{filename} ({size_mb:.1f} MB)")
        else:
            self.selected_doc_path = None
            self.doc_path_label.setText("No document file attached.")

    def _on_send(self):
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        sender_id = self.sender_input.text().strip()

        if not subject and not body:
            QMessageBox.warning(self, "Empty Email", "Please enter a subject or message body before sending.")
            return

        mail_payload = {
            "sender_id": sender_id,
            "subject": subject,
            "body": body,
        }

        self.send_mail_requested.emit(mail_payload, self.selected_doc_path)

        # Reset draft fields after sending
        self.subject_input.clear()
        self.body_input.clear()
        self.selected_doc_path = None
        self.doc_path_label.setText("No document file attached.")

    def add_received_mail(self, data: dict, file_bytes: bytes = None):
        """Populates the inbox table with received email payload."""
        row = self.inbox_table.rowCount()
        self.inbox_table.insertRow(row)

        payload = data.get("payload", {})
        has_file = payload.get("has_file", False)
        filename = payload.get("file_name", "None") if has_file else "None"
        body_text = payload.get("body", "")

        # Create one-line preview for table cell
        body_preview = body_text.replace("\n", " ")
        if len(body_preview) > 60:
            body_preview = body_preview[:57] + "..."

        self.inbox_bodies[row] = body_text

        self.inbox_table.setItem(row, 0, QTableWidgetItem(str(data.get("sender_id", "Unknown"))))
        self.inbox_table.setItem(row, 1, QTableWidgetItem(str(payload.get("subject", "(No Subject)"))))
        self.inbox_table.setItem(row, 2, QTableWidgetItem(body_preview))
        self.inbox_table.setItem(row, 3, QTableWidgetItem(filename))

        if has_file and file_bytes:
            self.inbox_files_data[row] = (filename, file_bytes)

    def _on_view_full_email(self):
        current_row = self.inbox_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an email from the inbox list.")
            return

        sender = self.inbox_table.item(current_row, 0).text()
        subject = self.inbox_table.item(current_row, 1).text()
        full_body = self.inbox_bodies.get(current_row, "")
        attachment = self.inbox_table.item(current_row, 3).text()

        formatted_body = full_body.replace('\n', '<br>')
        details = f"<b>From:</b> {sender}<br><b>Subject:</b> {subject}<br><b>Attachment:</b> {attachment}<hr><br>{formatted_body}"

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Email Viewer")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(details)
        msg_box.exec()

    def _on_save_inbox_attachment(self):
        current_row = self.inbox_table.currentRow()
        if current_row < 0 or current_row not in self.inbox_files_data:
            QMessageBox.information(self, "No Attachment", "Selected email has no attached file.")
            return

        filename, file_bytes = self.inbox_files_data[current_row]
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Email Attachment", filename)
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                QMessageBox.information(self, "Saved", f"Attachment saved successfully to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save attachment: {e}")