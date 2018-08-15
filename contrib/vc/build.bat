@ECHO OFF
rem Build frePPLe with Microsoft Visual C++ 2015 (aka vc14.0)
setlocal

rem EDIT THIS SECTION TO MATCH YOUR INSTALLATION
set PYTHON=C:\develop\python36
set XERCES=C:\develop\xerces-c-3.1.3-x86_64-windows-vc14.0
set MSBUILD=C:\Program Files (x86)\MSBuild\14.0

rem EDIT THIS SECTION WHEN NON_DEFAULT INSTALLATION FOLDER WAS CHOSEN
if exist "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC" (
  set VC=C:\Program Files ^(x86^)\Microsoft Visual Studio 14.0\VC
) else (
if exist "C:\Program Files\Microsoft Visual Studio 14.0\VC" (
  set VC=C:\Program Files\Microsoft Visual Studio 14.0\VC
) else (
  echo "Microsoft Visual Studio C++ 2015 not found"
  exit /B
)) 

rem PROCESS COMMAND LINE ARGUMENTS "-r (rebuild)" and "-d (debug)"
set conf=Release
set build=
:CheckOpts
if "%1"=="-r" (set build="/t:rebuild") & shift & goto CheckOpts
if "%1"=="-d" (set conf=Debug) & shift & goto CheckOpts

rem BUILD THE PROJECT
call "%VC%\vcvarsall" x86_amd64
set INCLUDE=%PYTHON%\include;%XERCES%\include;%INCLUDE%
set LIB=%PYTHON%\libs;%XERCES%\lib;%LIB%

"%MSBUILD%\bin\msbuild.exe" %build% /m /p:useenv=true /p:showenv=true frepple.sln "/p:Configuration=%conf%" /p:Platform=x64
