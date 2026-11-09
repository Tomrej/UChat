import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Allow passing custom local server port via CLI argument (e.g., python main.py 5001)
    listen_port = 5000
    if len(sys.argv) > 1:
        try:
            listen_port = int(sys.argv[1])
        except ValueError:
            print(f"[WARN] Invalid port parameter '{sys.argv[1]}'. Defaulting to 5000.")

    window = MainWindow(listen_port=listen_port)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()