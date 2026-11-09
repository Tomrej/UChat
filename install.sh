#!/usr/bin/env bash
set -e

APP_NAME="UChat"
INSTALL_DIR="$HOME/.local/share/UChat"
DESKTOP_ENTRY_DIR="$HOME/.local/share/applications"

# Zjištění adresáře, ve kterém je skript uložen
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Installing $APP_NAME for Linux ==="

# Check Python 3 availability
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed. Please install python3 first."
    exit 1
fi

# Určení složky se zdrojovým kódem (podporuje kořen i podsložku UChat)
if [ -d "$SCRIPT_DIR/UChat" ]; then
    SOURCE_DIR="$SCRIPT_DIR/UChat"
else
    SOURCE_DIR="$SCRIPT_DIR"
fi

# Create app directory in ~/.local/share/UChat
echo "[1/4] Preparing installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Copy application files (včetně config.py)
echo "Copying source files from $SOURCE_DIR..."
cp -r "$SOURCE_DIR/main.py" "$SOURCE_DIR/config.py" "$SOURCE_DIR/requirements.txt" "$SOURCE_DIR/src" "$INSTALL_DIR/"

# Setup virtual environment
echo "[2/4] Setting up Python virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"

# Install dependencies
echo "[3/4] Installing dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet

# Create runner shell script
RUNNER_SCRIPT="$INSTALL_DIR/run.sh"
cat << 'EOF' > "$RUNNER_SCRIPT"
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/main.py" "$@"
EOF
chmod +x "$RUNNER_SCRIPT"

# Create Desktop Shortcut (.desktop file)
echo "[4/4] Creating desktop shortcut..."
mkdir -p "$DESKTOP_ENTRY_DIR"

DESKTOP_FILE="$DESKTOP_ENTRY_DIR/UChat.desktop"
cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=UChat (Unsafe Chat)
Comment=Educational P2P Cybersecurity Messaging Client
Exec=$RUNNER_SCRIPT
Terminal=false
Type=Application
Categories=Development;Education;Network;
EOF

chmod +x "$DESKTOP_FILE"

echo ""
echo "=== Installation Completed Successfully! ==="
echo "You can now start UChat from your application menu or run:"
echo "  $RUNNER_SCRIPT"