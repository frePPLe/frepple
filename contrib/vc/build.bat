rem Build frePPLe with Microsoft Visual C++ 2008 (vc9)
setlocal

rem EDIT THIS SECTION TO MATCH YOUR INSTALLATION
set VC=C:\Program Files\Microsoft Visual Studio 9.0
set PYTHON=C:\develop\python27
set XERCES=C:\develop\xerces-c-3.1.1-x86-windows-vc-9.0
set GLPK=C:\develop\glpk-4.46
set DOTNET=C:\WINDOWS\Microsoft.NET\Framework\v4.0.30319

rem PROCESS COMMAND LINE ARGUMENTS "-r (rebuild)" and "-d (debug)"
set conf=Release
set build=
:CheckOpts
if "%1"=="-r" (set build="/rebuild") & shift & goto CheckOpts
if "%1"=="-d" (set conf=Debug) & shift & goto CheckOpts

rem BUILD THE PROJECT
call "%VC%\VC\vcvarsall"
set INCLUDE=%PYTHON%\include;%XERCES%\include;%GLPK%\src;%INCLUDE%
set LIB=%PYTHON%\libs;%XERCES%\lib;%GLPK%\w32;%LIB%

"%VC%\VC\vcpackages\vcbuild.exe" %build%  /useenv /showenv frepple.sln "%conf%|Win32"
