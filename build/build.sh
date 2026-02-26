#!/usr/bin/env bash
# Build script — run from repo root.
# Usage:
#   ./build/build.sh windows    → dist/SpeechToText/ (Windows folder, ready to MSIX-pack)
#   ./build/build.sh mac        → dist/SpeechToText.app (macOS .app bundle)
#   ./build/build.sh mac-dmg    → dist/SpeechToText.dmg (notarized DMG, requires Apple Developer ID)

set -e

PLATFORM="${1:-$(uname -s | tr '[:upper:]' '[:lower:]')}"

install_deps() {
    pip install pyinstaller
}

build_windows() {
    echo "Building Windows executable..."
    pyinstaller build/speech-to-text-windows.spec --clean --noconfirm
    echo "Done → dist/SpeechToText/"
    echo ""
    echo "To create an MSIX installer, run:"
    echo "  makeappx pack /d dist/SpeechToText /p dist/SpeechToText.msix"
}

build_mac() {
    echo "Building macOS .app bundle..."
    pyinstaller build/speech-to-text-mac.spec --clean --noconfirm
    echo "Done → dist/SpeechToText.app"
}

build_mac_dmg() {
    build_mac

    # Codesign (requires DEVELOPER_ID env var set to your Apple Developer ID)
    if [ -n "$DEVELOPER_ID" ]; then
        echo "Code signing..."
        codesign --deep --force --options runtime \
            --entitlements build/entitlements.plist \
            --sign "$DEVELOPER_ID" \
            dist/SpeechToText.app
    else
        echo "Warning: DEVELOPER_ID not set, skipping code signing."
        echo "Set DEVELOPER_ID='Developer ID Application: Your Name (XXXXXXXXXX)'"
    fi

    # Create DMG
    echo "Creating DMG..."
    hdiutil create -volname "SpeechToText" \
        -srcfolder dist/SpeechToText.app \
        -ov -format UDZO \
        dist/SpeechToText.dmg

    # Notarize (requires APPLE_ID, APPLE_PASSWORD, APPLE_TEAM_ID env vars)
    if [ -n "$APPLE_ID" ]; then
        echo "Submitting for notarization..."
        xcrun notarytool submit dist/SpeechToText.dmg \
            --apple-id "$APPLE_ID" \
            --password "$APPLE_PASSWORD" \
            --team-id "$APPLE_TEAM_ID" \
            --wait
        xcrun stapler staple dist/SpeechToText.dmg
        echo "Notarization complete → dist/SpeechToText.dmg"
    else
        echo "Warning: APPLE_ID not set, skipping notarization."
    fi
}

install_deps

case "$PLATFORM" in
    windows)  build_windows ;;
    mac)      build_mac ;;
    mac-dmg)  build_mac_dmg ;;
    Darwin)   build_mac ;;
    *)
        echo "Usage: $0 [windows|mac|mac-dmg]"
        exit 1
        ;;
esac
