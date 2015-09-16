#
# Process this file with automake to produce Makefile.in
#

pkgsysconfdir = $(sysconfdir)/frepple
pkgsysconf_DATA = djangosettings.py

EXTRA_DIST = freppledb README.txt frepplectl.py setup.py djangosettings.py

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
	-rm -rf `find . -name '__pycache__'`
	-rm -rf build dist doc static *.log

# Avoid packaging python bytecode files from the subdirectories
dist-hook:
	-rm -rf `find $(distdir) -name '__pycache__'`

create:
	./frepplectl.py syncdb

contrib-check:
	./frepplectl.py test

runserver:
	./frepplectl.py frepple_runserver

international:
	cd freppledb; django-admin.py makemessages -a -e html -e xml && django-admin.py compilemessages
	cd freppledb; django-admin.py makemessages -a -d djangojs && django-admin.py compilemessages

pep8:
	flake8 freppledb --ignore=E121,E111,E501,E303,E201,E202,E123

doc:
	-rm -rf doc
	export PYTHONPATH=freppledb:.; export DJANGO_SETTINGS_MODULE=freppledb.settings; epydoc --name frePPLe --output doc --html --url "http://www.frepple.com/" --no-imports --show-sourcecode freppledb

.PHONY: create check runserver international doc

