#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = freppledb django.patch README.txt httpd.conf setup.py

install-data-local:
	echo "installing Django web application to $(DESTDIR)$(pythondir)"; \
	export FREPPLE_APP=$(DESTDIR)$(pythondir)/freppledb; \
	export DJANGO_SETTINGS_MODULE=freppledb.settings; \
	export FREPPLE_HOME=dummy; \
	$(PYTHON) setup.py install --prefix $(DESTDIR)$(prefix)
	
uninstall-local:
	-rm -rf $(DESTDIR)$(pythondir)/freppledb 
	-rm -rf $(DESTDIR)$(pythondir)/freppledb-$(PACKAGE_VERSION)*.egg-info

clean-local:
	-rm -rf `find . -name '*.pyc'`
	-rm -rf `find . -name '*.pyo'`
	-rm -rf build dist doc freppledb/static *.sqlite *.log

# Avoid packaging python bytecode files from the subdirectories
dist-hook:
	-rm -rf `find $(distdir) -name '*.pyc'`
	-rm -rf `find $(distdir) -name '*.pyo'`

create:
	cd freppledb; ./manage.py syncdb

contrib-check:
	cd freppledb; ./manage.py test

runserver:
	cd freppledb; ./manage.py frepple_runserver

international:
	cd freppledb; django-admin.py makemessages -a -e html -e xml && django-admin.py compilemessages
	cd freppledb; django-admin.py makemessages -a -d djangojs && django-admin.py compilemessages

doc:
	-rm -rf doc
	export PYTHONPATH=freppledb:.; export DJANGO_SETTINGS_MODULE=freppledb.settings; epydoc --name frePPLe --output doc --html --url "http://www.frepple.com/" --no-imports --show-sourcecode freppledb

.PHONY: create check runserver international doc

