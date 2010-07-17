#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.sln README.txt model.vcxproj utils.vcxproj main.vcxproj module_forecast.vcxproj solver.vcxproj dll.vcxproj module_lp_solver.vcxproj module_webservice.vcxproj

clean-local:
	-rm -rf model utils module_forecast main dll solver module_lp_solver module_webservice *.vcxproj.* *.opt *.ncb *.suo *.log *.sdf ipch

contrib:
# Call the microsoft development environment from the command line.
# You'll need to update the path to your studio installation directory.
# The INCLUDE and LIB environment variables also need to be set okay.
	'C:\WINDOWS\Microsoft.NET\Framework\v4.0.30319\MSBuild.exe' /target:rebuild  /property:useenv=true /property:Configuration=Release /property:Platform=Win32 frepple.sln 
