from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Signal


class MailTab(QWidget):
    """Tab interface for crafting and inspecting invoices and corporate documents."""

    send_invoice_requested = Signal(dict)  # Emits structured invoice data dict

    def __init__(self, parent=None):
        super().__init__(parent)
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

        # Placeholders for future cryptographic metadata (Disabled/Read-only for baseline)
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Unprotected (Plaintext)")
        self.hash_input.setReadOnly(True)

        form_layout.addRow("Sender Identity:", self.sender_input)
        form_layout.addRow("Target Account Number:", self.account_input)
        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("Currency:", self.currency_input)
        form_layout.addRow("Note:", self.note_input)
        form_layout.addRow("Document Hash (SHA-256):", self.hash_input)

        self.send_btn = QPushButton("Send Document (Unencrypted)")
        self.send_btn.clicked.connect(self._on_send)
        form_layout.addRow(self.send_btn)

        layout.addWidget(form_group)

        # Received Documents Inbox
        inbox_group = QGroupBox("Received Documents (Inbox)")
        inbox_layout = QVBoxLayout(inbox_group)

        self.inbox_table = QTableWidget(0, 5)
        self.inbox_table.setHorizontalHeaderLabels([
            "Sender", "Account Number", "Amount", "Currency", "Note"
        ])
        self.inbox_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        inbox_layout.addWidget(self.inbox_table)

        layout.addWidget(inbox_group)

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
        self.send_invoice_requested.emit(invoice_payload)

    def add_received_invoice(self, data: dict):
        """Populates the received invoices table with incoming document payload."""
        row = self.inbox_table.rowCount()
        self.inbox_table.insertRow(row)

        payload = data.get("payload", {})
        self.inbox_table.setItem(row, 0, QTableWidgetItem(str(data.get("sender_id", "Unknown"))))
        self.inbox_table.setItem(row, 1, QTableWidgetItem(str(payload.get("account_number", ""))))
        self.inbox_table.setItem(row, 2, QTableWidgetItem(str(payload.get("amount", ""))))
        self.inbox_table.setItem(row, 3, QTableWidgetItem(str(payload.get("currency", ""))))
        self.inbox_table.setItem(row, 4, QTableWidgetItem(str(payload.get("note", ""))))