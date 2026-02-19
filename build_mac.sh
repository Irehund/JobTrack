#!/bin/bash
# JobTrack — macOS Build Script (Future Release)
# Packages the app into a standalone .app bundle using PyInstaller.
# Run from the project root: bash build_mac.sh

echo "=========================================="
echo " JobTrack — Building macOS App Bundle"
echo "=========================================="

# Ensure PyInstaller is available
if ! pip show pyinstaller &> /dev/null; then
    echo "[ERROR] PyInstaller not found. Run: pip install pyinstaller"
    exit 1
fi

# Clean previous build artifacts
echo "[1/3] Cleaning previous build..."
rm -rf build dist JobTrack.spec

# Run PyInstaller
echo "[2/3] Running PyInstaller..."
pyinstaller \
    --name "JobTrack" \
    --onefile \
    --windowed \
    --icon "assets/icons/jobtrack.icns" \
    --add-data "assets:assets" \
    --hidden-import "customtkinter" \
    --hidden-import "PIL" \
    --hidden-import "folium" \
    --hidden-import "keyring.backends.macOS" \
    main.py

if [ $? -ne 0 ]; then
    echo "[ERROR] PyInstaller failed. See output above."
    exit 1
fi

echo "[3/3] Build complete!"
echo "Output: dist/JobTrack.app"
echo "=========================================="
