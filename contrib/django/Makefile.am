#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple README.txt

clean-local:
	-rm -rf `find . -name '*.pyc'`
	-rm -rf `find . -name '*.pyo'`

start:
	cd frepple; manage.py runserver

create:
	cd frepple; manage.py syncdb
	cd frepple; manage.py reset input
	cd frepple; manage.py reset output
	cd frepple; manage.py reset execute
