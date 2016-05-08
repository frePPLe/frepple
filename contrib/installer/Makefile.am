#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.nsi README.txt frepple.bmp frepplectl.py setup.py freppleservice.py freppleserver.py parameters.ini finish.ini finish.bmp pgsql

clean-local:
	-rm -rf dist build *.pyc

contrib:
	"/c/Program Files (x86)/NSIS/makensis.exe" frepple.nsi

py2exe:
	setup.py
