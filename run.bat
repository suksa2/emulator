@echo off
rem Run the emulator: run.bat [options]
set PYTHONPATH=%~dp0src
python -m emulator %*
