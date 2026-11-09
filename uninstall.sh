#!/usr/bin/env bash
echo "Uninstalling UChat..."
rm -rf "$HOME/.local/share/UChat"
rm -f "$HOME/.local/share/applications/UChat.desktop"
echo "UChat has been removed."