@echo off
rem Stage 2: test all supported command line options.
rem --no-gui runs the startup script in the console; without it a window
rem is opened (close it to continue).
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\src
set SCRIPT=%ROOT%\examples\scripts\stage2.txt
set LOG=%TEMP%\emulator_test_log.csv
if exist "%LOG%" del "%LOG%"

echo ===== 1. help =====
python -m emulator --help

echo ===== 2. --script only =====
python -m emulator --no-gui --script "%SCRIPT%"

echo ===== 3. --log and --script =====
python -m emulator --no-gui --log "%LOG%" --script "%SCRIPT%"
echo ----- log file -----
type "%LOG%"

echo ===== 4. all options =====
python -m emulator --no-gui --vfs "%ROOT%\examples\vfs\deep.xml" --log "%LOG%" --script "%SCRIPT%"

echo ===== 5. missing script file =====
python -m emulator --no-gui --script "%ROOT%\examples\scripts\missing.txt"

echo ===== 6. bad log path =====
python -m emulator --no-gui --log "%ROOT%\no_such_dir\log.csv"
echo exit code: %ERRORLEVEL%

echo ===== 7. unknown option =====
python -m emulator --bad-option
echo exit code: %ERRORLEVEL%

echo ===== 8. GUI with all options =====
python -m emulator --vfs "%ROOT%\examples\vfs\deep.xml" --log "%LOG%" --script "%SCRIPT%"
endlocal
