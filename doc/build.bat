rem Rebuilds the documentation on Microsoft Windows
rmdir /s /q _build
sphinx-build -a -E -b html -d _build/doctrees . _build/html
IF %0 == "%~0"  pause