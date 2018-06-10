#
# Process this file with automake to produce Makefile.in
#

pkgsysconfdir = $(sysconfdir)/frepple
pkgsysconf_DATA = djangosettings.py

SUBDIRS = src include test contrib bin doc

EXTRA_DIST = freppledb AUTHORS COPYING CONTRIBUTING.md README.md Makefile.am Makefile.dist freppledb frepplectl.py setup.py djangosettings.py requirements.txt package.json Gruntfile.js

AUTOMAKE_OPTIONS = foreign

.PHONY: $(.PHONY) migrate check runserver international pep8

install-data-local: setup.py
	echo "Installing Django web application"; \
	$(PYTHON) setup.py install --prefix $(DESTDIR)$(prefix) $(PYFLAGS)
	-mkdir static
	$(PYTHON) frepplectl.py collectstatic --noinput --clear --ignore '*.less'
	find static -type d -exec $(mkinstalldirs) "$(DESTDIR)$(datadir)/frepple/{}" \;; \
	for p in `find static -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(datadir)/frepple/$$p"; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(datadir)/frepple $(DESTDIR)$(libdir)/frepple
	-rm -rf $(DESTDIR)$(pythondir)/freppledb
	-rm -rf $(DESTDIR)$(pythondir)/freppledb-$(PACKAGE_VERSION)*.egg-info
	-rm -rf $(DESTDIR)$(datadir)/frepple/static

clean-local:
	-rm -rf install-test *.exe
	-rm -rf `find . -name '__pycache__'`
	-rm -rf build dist static node_modules

# Avoid packaging any git folders and python bytecode files
dist-hook:
	-rm -rf `find $(top_distdir) -name '.git' -type d`
	-rm -rf `find $(distdir) -name '__pycache__'`

# Initialize
migrate:
	./frepplectl.py migrate

check:
	./frepplectl.py test

runserver:
	./frepplectl.py runserver

international:
	cd freppledb; django-admin.py makemessages -a -d django
	cd freppledb; django-admin.py makemessages -a -d djangojs
	find .  -name '*.po' -exec msggrep -X -e 'Translators: Translation included with Django' --invert-match  {} -o tmp.po \; -exec mv tmp.po {} \;
	cd freppledb; django-admin.py compilemessages

pep8:
	flake8 freppledb --ignore=E121,E111,E501,E303,E201,E202,E123
