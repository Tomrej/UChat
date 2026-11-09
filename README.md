# UChat (Unsafe Chat)

An educational P2P (Peer-to-Peer) Python application built with PySide6, specifically designed for cybersecurity and cryptography training. UChat serves as an intentionally vulnerable baseline application. Students analyze insecure network traffic in real time using tools like Wireshark.

---

## ⚠️ IMPORTANT NOTICE: INTENTIONALLY INSECURE COMMUNICATION

> **UChat has NO application-layer security by default.**
>
>All communication—including live chat messages, email subjects, body text, and file attachments—is transmitted **in unencrypted plain text (plaintext)** using standard>JSON packets sent over raw TCP sockets.
>
>**Educational Purpose:** This allows students to capture live network traffic using `Wireshark` or `tcpdump`, inspect transmitted payloads directly, and visually understand>why unencrypted network protocols are vulnerable to eavesdropping and data tampering.

---

## Key Features

- **Live Chat:** Real-time P2P text messaging with file attachment support.

- **Mail & Documents:** Simulated corporate email client (subject line, multi-line message body, and document attachments).

- **File Transfer Engine:** Base64 binary file encoding directly within JSON network frames (enforces a safety limit of 25 MB per file to prevent memory exhaustion).

- **Flexible P2P Networking:** Dynamic binding of local listening ports (`My Port`) and target destination endpoints (`Target IP` / `Target Port`) via GUI or CLI.

---

## Requirements & Installation

Requires Python 3.10 or higher.

1. **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/UChat.git
    cd UChat
    ```

2. **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux / macOS
    # .venv\Scripts\activate   # Windows
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## Quick Start

You can run multiple instances of UChat on the same machine (using different local ports) or across separate hosts on a local network (LAN).
Running Two Local Instances (Loopback Mode)

1. **Instance 1 (Peer A):**
    ```bash
    python main.py 5000
    Listens on port 5000.
    Set Target Port in the top bar to 5001.
    ``

2. **Instance 2 (Peer B):**
    ```bash
    python main.py 5001
    Listens on port 5001.
    Set Target Port in the top bar to 5000.
    ```

Now send a chat message or email from either window to verify P2P transmission.
Lab Exercise: Wireshark Traffic Analysis

**Open Wireshark.**

Select your capture interface:

- For local loopback testing, select Adapter for loopback traffic / lo.
- For LAN testing, select your active network adapter (Ethernet / Wi-Fi).

**Apply the display filter:**
    
    tcp.port == 5000 || tcp.port == 5001

- Send a chat message or email in UChat.

- Right-click any captured TCP packet in Wireshark and select Follow -> TCP Stream.

**Expected Result:** You will observe the raw JSON structure containing unencrypted plain text fields and Base64-encoded file data.

---

## Project Structure
```bash
UChat/
├── main.py                  # Application entry point (supports optional CLI port argument)
├── requirements.txt         # Project dependencies (PySide6)
├── README.md                # Project documentation
└── src/
    ├── network/             # Asynchronous TCP networking engine
    │   ├── server.py        # QTcpServer managing incoming P2P socket connections
    │   └── client.py        # QTcpSocket managing outbound frame transmission
    └── ui/                  # Graphical User Interface (PySide6)
        ├── chat_tab.py      # Live chat & file sharing view
        ├── mail_tab.py      # Email drafting, inbox & viewer interface
        └── main_window.py   # Main window integration & socket signal wiring
```

*note: This app was vibecoded.*