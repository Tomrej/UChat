import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QHBoxLayout,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Signal


class MailTab(QWidget):
    """Tab interface for crafting and inspecting invoices and corporate documents with attachments."""

    # Emits (invoice_data_dict, optional_file_path)
    send_invoice_requested = Signal(dict, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_doc_path = None
        self.inbox_files_data = {}  # Map of row_index -> (file_name, bytes)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Document Creation Form
        form_group = QGroupBox("Draft New Document / Invoice")
        form_layout = QFormLayout(form_group)

        self.sender_input = QLineEdit("Company A")
        self.account_input = QLineEdit("22001122/0800")
        self.amount_input = QLineEdit("150000")
        self.currency_input = QLineEdit("CZK")
        self.note_input = QLineEdit("Services rendered")

        # Attachment Selection Row
        doc_attach_layout = QHBoxLayout()
        self.doc_path_label = QLabel("No document file attached.")
        self.doc_path_label.setStyleSheet("color: #666; font-style: italic;")

        self.attach_doc_btn = QPushButton("Browse Document...")
        self.attach_doc_btn.clicked.connect(self._on_browse_document)
        doc_attach_layout.addWidget(self.doc_path_label)
        doc_attach_layout.addWidget(self.attach_doc_btn)

        # Placeholders for future cryptographic metadata (Disabled/Read-only for baseline)
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Unprotected (Plaintext)")
        self.hash_input.setReadOnly(True)

        form_layout.addRow("Sender Identity:", self.sender_input)
        form_layout.addRow("Target Account Number:", self.account_input)
        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("Currency:", self.currency_input)
        form_layout.addRow("Note:", self.note_input)
        form_layout.addRow("Attached Document File:", doc_attach_layout)
        form_layout.addRow("Document Hash (SHA-256):", self.hash_input)

        self.send_btn = QPushButton("Send Document (Unencrypted)")
        self.send_btn.clicked.connect(self._on_send)
        form_layout.addRow(self.send_btn)

        layout.addWidget(form_group)

        # Received Documents Inbox
        inbox_group = QGroupBox("Received Documents (Inbox)")
        inbox_layout = QVBoxLayout(inbox_group)

        self.inbox_table = QTableWidget(0, 6)
        self.inbox_table.setHorizontalHeaderLabels([
            "Sender", "Account Number", "Amount", "Currency", "Note", "Attached File"
        ])
        self.inbox_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        inbox_layout.addWidget(self.inbox_table)

        inbox_controls = QHBoxLayout()
        self.download_attachment_btn = QPushButton("Save Selected Document Attachment")
        self.download_attachment_btn.clicked.connect(self._on_save_inbox_attachment)
        inbox_controls.addStretch()
        inbox_controls.addWidget(self.download_attachment_btn)
        inbox_layout.addLayout(inbox_controls)

        layout.addWidget(inbox_group)

    def _on_browse_document(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Invoice Document")
        if file_path:
            self.selected_doc_path = file_path
            filename = os.path.basename(file_path)
            self.doc_path_label.setText(filename)
        else:
            self.selected_doc_path = None
            self.doc_path_label.setText("No document file attached.")

    def _on_send(self):
        try:
            amount_val = float(self.amount_input.text().strip())
        except ValueError:
            amount_val = 0.0

        invoice_payload = {
            "sender_id": self.sender_input.text().strip(),
            "account_number": self.account_input.text().strip(),
            "amount": amount_val,
            "currency": self.currency_input.text().strip(),
            "note": self.note_input.text().strip(),
        }

        self.send_invoice_requested.emit(invoice_payload, self.selected_doc_path)

        # Reset document selection after sending
        self.selected_doc_path = None
        self.doc_path_label.setText("No document file attached.")

    def add_received_invoice(self, data: dict, file_bytes: bytes = None):
        """Populates the received invoices table with incoming document payload."""
        row = self.inbox_table.rowCount()
        self.inbox_table.insertRow(row)

        payload = data.get("payload", {})
        has_file = payload.get("has_file", False)
        filename = payload.get("file_name", "None") if has_file else "None"

        self.inbox_table.setItem(row, 0, QTableWidgetItem(str(data.get("sender_id", "Unknown"))))
        self.inbox_table.setItem(row, 1, QTableWidgetItem(str(payload.get("account_number", ""))))
        self.inbox_table.setItem(row, 2, QTableWidgetItem(str(payload.get("amount", ""))))
        self.inbox_table.setItem(row, 3, QTableWidgetItem(str(payload.get("currency", ""))))
        self.inbox_table.setItem(row, 4, QTableWidgetItem(str(payload.get("note", ""))))
        self.inbox_table.setItem(row, 5, QTableWidgetItem(filename))

        if has_file and file_bytes:
            self.inbox_files_data[row] = (filename, file_bytes)

    def _on_save_inbox_attachment(self):
        current_row = self.inbox_table.currentRow()
        if current_row < 0 or current_row not in self.inbox_files_data:
            QMessageBox.information(self, "No Attachment", "Selected row has no attached document file.")
            return

        filename, file_bytes = self.inbox_files_data[current_row]
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Invoice Attachment", filename)
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                QMessageBox.information(self, "Saved", f"Document saved successfully to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save document: {e}")