rem Build frePPLe with Microsoft Visual C++ 2010
 
rem EDIT THIS SECTION TO MATCH YOUR INSTALLATION
set VC=C:\Program Files\Microsoft Visual Studio 10.0
set PYTHON=C:\develop\python27
set XERCES=C:\packages\xerces-c-3.1.1-x86-windows-vc-10.0
set GLPK=C:\packages\glpk-4.25
set DOTNET=C:\WINDOWS\Microsoft.NET\Framework\v4.0.30319

rem BUILD THE PROJECT
call "%VC%\VC\vcvarsall"
set INCLUDE=%PYTHON%\include;%XERCES%\include;%GLPK%\include;%INCLUDE%
set LIB=%PYTHON%\libs;%XERCES%\lib;%GLPK%;%LIB%
"%DOTNET%\MSBuild.exe" /target:rebuild  /property:useenv=true /property:Configuration=Release /property:Platform=Win32  frepple.sln 
