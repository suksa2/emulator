#!/bin/sh
# Stages 4-5: run startup scripts that test emulator commands.
# Usage: test_commands.sh [gui]  (default: console mode)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/src"
VFS="$ROOT/examples/vfs/deep.xml"
MODE="--no-gui"
[ "$1" = "gui" ] && MODE=""

for stage in stage4 stage5; do
    script="$ROOT/examples/scripts/$stage.txt"
    if [ -f "$script" ]; then
        echo "===== $stage ====="
        python3 -m emulator $MODE --vfs "$VFS" --script "$script"
    fi
done
