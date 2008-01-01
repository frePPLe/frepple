#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.sln README.txt model.vcproj utils.vcproj main.vcproj module_forecast.vcproj module_python.vcproj solver.vcproj dll.vcproj swig.vcproj module_lp_solver.vcproj module_webservice.vcproj

clean-local:
	-rm -rf model erp utils module_forecast main dll solver module_python module_lp_solver module_webservice swig *.opt *.ncb

contrib:
# Call the microsoft development environment from the command line
# You'll need to update the path to your studio installation directory
	'/c/Program Files/Microsoft Visual Studio .NET/Common7/IDE/devenv' /build release frepple.sln
