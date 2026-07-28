#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h:h}"
cd "$ROOT_DIR"

python3 -m unittest discover -s tests -v
APP_PATH="$($ROOT_DIR/scripts/build_app.sh | tail -1)"

"$APP_PATH/Contents/MacOS/DesktopPetEngine" --self-test
lipo "$APP_PATH/Contents/MacOS/DesktopPetEngine" -verify_arch x86_64 arm64
echo "可执行文件架构：$(lipo -archs "$APP_PATH/Contents/MacOS/DesktopPetEngine")"
codesign --verify --deep --strict "$APP_PATH"
plutil -lint "$APP_PATH/Contents/Info.plist"
echo "开源桌宠引擎自检全部通过"
