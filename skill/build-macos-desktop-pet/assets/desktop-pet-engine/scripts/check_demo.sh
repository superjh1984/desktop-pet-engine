#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h:h}"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

"$ROOT_DIR/scripts/generate_demo_cursor_themes.py" \
  --output-dir "$TEMP_DIR/CursorThemes" \
  --config "$TEMP_DIR/cursor_themes.json"

APP_PATH="$(
  CURSOR_THEMES_CONFIG="$TEMP_DIR/cursor_themes.json" \
  CURSOR_THEMES_DIR="$TEMP_DIR/CursorThemes" \
  "$ROOT_DIR/scripts/build_app.sh" | tail -1
)"

"$APP_PATH/Contents/MacOS/DesktopPetEngine" --self-test
CURSOR_CHECK_OUTPUT="$("$APP_PATH/Contents/MacOS/DesktopPetEngine" --cursor-self-test)"
echo "$CURSOR_CHECK_OUTPUT"
grep -q "2 custom themes" <<<"$CURSOR_CHECK_OUTPUT"
test -s "$APP_PATH/Contents/Resources/CursorThemes/blob-blue.cape"
test -s "$APP_PATH/Contents/Resources/CursorThemes/blob-gold.cape"
test ! -e "$APP_PATH/Contents/Resources/Mousecape.app"
lipo "$APP_PATH/Contents/MacOS/DesktopPetEngine" -verify_arch x86_64 arm64
echo "可执行文件架构：$(lipo -archs "$APP_PATH/Contents/MacOS/DesktopPetEngine")"
codesign --verify --deep --strict "$APP_PATH"
plutil -lint "$APP_PATH/Contents/Info.plist"
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_PATH/Contents/Info.plist")" = "1.1.0"
echo "开源桌宠引擎自检全部通过"
