#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.sln README.txt model.vcproj utils.vcproj main.vcproj common_python.vcproj module_forecast.vcproj module_python.vcproj solver.vcproj dll.vcproj module_lp_solver.vcproj module_webservice.vcproj

clean-local:
	-rm -rf model erp utils common_python module_forecast main dll solver module_python module_lp_solver module_webservice *.vcproj.* *.opt *.ncb *.suo

contrib:
# Call the microsoft development environment from the command line
# You'll need to update the path to your studio installation directory
	'/c/Program Files/Microsoft Visual Studio 9.0/Common7/IDE/VCExpress.exe' /build modules frepple.sln
