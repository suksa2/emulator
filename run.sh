#!/bin/sh
# Запуск эмулятора: ./run.sh [параметры]
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src" exec python3 -m emulator "$@"
