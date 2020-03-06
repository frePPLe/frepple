@echo off
rem Rebuilds the documentation on Microsoft Windows
:start
rmdir /s /q _build
sphinx-build -a -E -b html -d _build/doctrees . _build/html
IF not %0 == "%~0" goto end
set choice=
echo.
set /p choice="Press 'y' to repeat. Press any other other key to exit.  "
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto start
:end