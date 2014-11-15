@ECHO OFF
rem Build frePPLe with Microsoft Visual C++ 2010 (vc10)
setlocal

rem EDIT THIS SECTION TO MATCH YOUR INSTALLATION
set PYTHON=C:\develop\python34
set XERCES=C:\develop\xerces-c-3.1.1-x86-windows-vc-10.0
set DOTNET=C:\WINDOWS\Microsoft.NET\Framework\v4.0.30319

rem DETECT VISUAL STUDIO C++ 10.0
rem EDIT THIS SECTION WHEN NON_DEFAULT INSTALLATION FOLDER WAS CHOSEN
if exist "C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC" (
  set VC=C:\Program Files ^(x86^)\Microsoft Visual Studio 10.0\VC
) else (
if exist "C:\Program Files\Microsoft Visual Studio 10.0\VC" (
  set VC=C:\Program Files\Microsoft Visual Studio 10.0\VC
) else (
  echo "Microsoft Visual Studio C++ 10.0 not found"
  exit /B
)) 

rem PROCESS COMMAND LINE ARGUMENTS "-r (rebuild)" and "-d (debug)"
set conf=Release
set build=
:CheckOpts
if "%1"=="-r" (set build="/t:rebuild") & shift & goto CheckOpts
if "%1"=="-d" (set conf=Debug) & shift & goto CheckOpts

rem BUILD THE PROJECT
call "%VC%\vcvarsall"
set INCLUDE=%PYTHON%\include;%XERCES%\include;%INCLUDE%
set LIB=%PYTHON%\libs;%XERCES%\lib;%LIB%

"%DOTNET%\msbuild.exe" %build% /p:useenv=true /p:showenv=true frepple.sln "/p:Configuration=%conf%"
