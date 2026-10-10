#!/bin/sh
# Stage 2: test all supported command line options.
# --no-gui runs the startup script in the console; without it a window
# is opened (close it to continue).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/src"
SCRIPT="$ROOT/examples/scripts/stage2.txt"
LOG="${TMPDIR:-/tmp}/emulator_test_log.csv"
PY=python3
rm -f "$LOG"

echo "===== 1. help ====="
$PY -m emulator --help

echo "===== 2. --script only ====="
$PY -m emulator --no-gui --script "$SCRIPT"

echo "===== 3. --log and --script ====="
$PY -m emulator --no-gui --log "$LOG" --script "$SCRIPT"
echo "----- log file -----"
cat "$LOG"

echo "===== 4. all options ====="
$PY -m emulator --no-gui --vfs "$ROOT/examples/vfs/deep.xml" \
    --log "$LOG" --script "$SCRIPT"

echo "===== 5. missing script file ====="
$PY -m emulator --no-gui --script "$ROOT/examples/scripts/missing.txt"

echo "===== 6. bad log path ====="
$PY -m emulator --no-gui --log "$ROOT/no_such_dir/log.csv"
echo "exit code: $?"

echo "===== 7. unknown option ====="
$PY -m emulator --bad-option
echo "exit code: $?"

echo "===== 8. GUI with all options ====="
$PY -m emulator --vfs "$ROOT/examples/vfs/deep.xml" --log "$LOG" \
    --script "$SCRIPT"
