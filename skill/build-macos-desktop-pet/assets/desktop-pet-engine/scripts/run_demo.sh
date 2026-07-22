#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h:h}"
APP_PATH="$($ROOT_DIR/scripts/build_app.sh | tail -1)"
open "$APP_PATH"
