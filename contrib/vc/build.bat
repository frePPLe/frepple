rem Build frePPLe with Microsoft Visual C++ 2010
setlocal

rem EDIT THIS SECTION TO MATCH YOUR INSTALLATION
set VC=C:\Program Files\Microsoft Visual Studio 10.0
set PYTHON=C:\develop\python27
set XERCES=C:\packages\xerces-c-3.1.1-x86-windows-vc-10.0
set GLPK=C:\packages\glpk-4.25
set DOTNET=C:\WINDOWS\Microsoft.NET\Framework\v4.0.30319

rem PROCESS COMMAND LINE ARGUMENTS "-r (rebuild)" and "-d (debug)"
set conf=Release
set build=build
:CheckOpts
if "%1"=="-r" (set build=rebuild) & shift & goto CheckOpts
if "%1"=="-d" (set conf=Debug) & shift & goto CheckOpts

rem BUILD THE PROJECT
call "%VC%\VC\vcvarsall"
set INCLUDE=%PYTHON%\include;%XERCES%\include;%GLPK%\include;%INCLUDE%
set LIB=%PYTHON%\libs;%XERCES%\lib;%GLPK%;%LIB%
"%DOTNET%\MSBuild.exe" /target:%build%  /property:useenv=true /property:Configuration=%conf% /property:Platform=Win32 frepple.sln
