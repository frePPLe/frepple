#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.sln README.txt model.vcproj utils.vcproj main.vcproj module_forecast.vcproj solver.vcproj dll.vcproj module_lp_solver.vcproj module_webservice.vcproj

clean-local:
	-rm -rf model utils module_forecast main dll solver module_lp_solver module_webservice *.vcproj.* *.opt *.ncb *.suo

contrib:
# Call the microsoft development environment from the command line.
# You'll need to update the path to your studio installation directory.
# The INCLUDE and LIB environment variables also need to be set okay.
	'c:\Program Files\Microsoft Visual Studio 9.0\VC\vcpackages\vcbuild.exe' /rebuild  /useenv /showenv frepple.sln "Release|Win32"
