#
# Process this file with automake to produce Makefile.in
#

pkgsysconfdir = $(sysconfdir)/frepple
pkgsysconf_DATA = djangosettings.py

EXTRA_DIST = freppledb django.patch README.txt frepplectl.py setup.py djangosettings.py

install-data-local:
	echo "Installing Django web application"; \
	$(PYTHON) setup.py install --prefix $(DESTDIR)$(prefix) $(PYFLAGS)
	-mkdir static
	$(PYTHON) frepplectl.py collectstatic --noinput --clear
	find static -type d -exec $(mkinstalldirs) "$(DESTDIR)$(datadir)/frepple/{}" \;; \
	for p in `find static -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(datadir)/frepple/$$p"; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(pythondir)/freppledb
	-rm -rf $(DESTDIR)$(pythondir)/freppledb-$(PACKAGE_VERSION)*.egg-info
	-rm -rf $(DESTDIR)$(datadir)/frepple/static

clean-local:
	-rm -rf `find . -name '*.pyc'`
	-rm -rf `find . -name '*.pyo'`
	-rm -rf build dist doc static *.sqlite *.log

# Avoid packaging python bytecode files from the subdirectories
dist-hook:
	-rm -rf `find $(distdir) -name '*.pyc'`
	-rm -rf `find $(distdir) -name '*.pyo'`

create:
	./frepplectl.py syncdb

contrib-check:
	./frepplectl.py test

runserver:
	./frepplectl.py frepple_runserver

international:
	cd freppledb; django-admin.py makemessages -a -e html -e xml && django-admin.py compilemessages
	cd freppledb; django-admin.py makemessages -a -d djangojs && django-admin.py compilemessages

doc:
	-rm -rf doc
	export PYTHONPATH=freppledb:.; export DJANGO_SETTINGS_MODULE=freppledb.settings; epydoc --name frePPLe --output doc --html --url "http://www.frepple.com/" --no-imports --show-sourcecode freppledb

.PHONY: create check runserver international doc

