#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h:h}"
APP_DIR="$ROOT_DIR/dist/桌宠引擎.app"
BUILD_DIR="$ROOT_DIR/.build/universal-release"

cd "$ROOT_DIR"
mkdir -p "$BUILD_DIR"
xcrun --sdk macosx swiftc \
  -O \
  -target x86_64-apple-macosx12.0 \
  -framework AppKit \
  "$ROOT_DIR"/Sources/DesktopPetEngine/*.swift \
  -o "$BUILD_DIR/DesktopPetEngine-x86_64"
xcrun --sdk macosx swiftc \
  -O \
  -target arm64-apple-macosx12.0 \
  -framework AppKit \
  "$ROOT_DIR"/Sources/DesktopPetEngine/*.swift \
  -o "$BUILD_DIR/DesktopPetEngine-arm64"
lipo -create \
  "$BUILD_DIR/DesktopPetEngine-x86_64" \
  "$BUILD_DIR/DesktopPetEngine-arm64" \
  -output "$BUILD_DIR/DesktopPetEngine"
lipo "$BUILD_DIR/DesktopPetEngine" -verify_arch x86_64 arm64

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"
cp "$BUILD_DIR/DesktopPetEngine" "$APP_DIR/Contents/MacOS/DesktopPetEngine"
cp "$ROOT_DIR/packaging/Info.plist" "$APP_DIR/Contents/Info.plist"
cp -R "$ROOT_DIR/Sources/DesktopPetEngine/Assets" "$APP_DIR/Contents/Resources/Assets"
codesign --force --sign - "$APP_DIR" >/dev/null
echo "$APP_DIR"
