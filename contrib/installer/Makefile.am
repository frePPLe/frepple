#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.nsi README.txt frepple.bmp frepplectl.py setup.py freppleservice.py parameters.ini finish.ini licensefile.ini

clean-local:
	-rm -rf dist build *.pyc

contrib:
	"/c/Program Files/NSIS/makensis.exe" /DPYTHON='c:\develop\python27' frepple.nsi

py2exe:
	setup.py
