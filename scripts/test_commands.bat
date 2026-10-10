@echo off
rem Stages 4-5: run startup scripts that test emulator commands.
rem Usage: test_commands.bat [gui]  (default: console mode)
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src
set VFS=%ROOT%\examples\vfs\deep.xml
set MODE=--no-gui
if "%1"=="gui" set MODE=

for %%S in (stage4 stage5) do (
    if exist "%ROOT%\examples\scripts\%%S.txt" (
        echo ===== %%S =====
        python -m emulator %MODE% --vfs "%VFS%" --script "%ROOT%\examples\scripts\%%S.txt"
    )
)
endlocal
