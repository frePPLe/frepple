#
# Process this file with automake to produce Makefile.in
#

pkgsysconfdir = $(sysconfdir)/frepple
pkgsysconf_DATA = djangosettings.py

SUBDIRS = src include test contrib bin doc

EXTRA_DIST = AUTHORS COPYING CONTRIBUTING.md README.md SECURITY.md Makefile.am Makefile.dist freppledb frepplectl.py setup.py djangosettings.py requirements.txt package.json Gruntfile.js

AUTOMAKE_OPTIONS = foreign

.PHONY: $(.PHONY) migrate check runserver collect-translations compile-translations

install-data-local: setup.py
	echo "Installing Django web application"; \
	$(PYTHON) setup.py install --prefix $(DESTDIR)$(prefix) $(PYFLAGS)
	mv "$(DESTDIR)$(bindir)/frepplectl.py" "$(DESTDIR)$(bindir)/frepplectl"
	-mkdir static
	$(PYTHON) frepplectl.py collectstatic --noinput --clear --ignore '*.less'
	find static -type d -exec $(mkinstalldirs) "$(DESTDIR)$(datadir)/frepple/{}" \;; \
	for p in `find static -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(datadir)/frepple/$$p"; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(datadir)/frepple $(DESTDIR)$(libdir)/frepple
	-rm -rf $(DESTDIR)$(pythondir)/frepple*
	-rm -rf $(DESTDIR)$(datadir)/frepple/static
	-rm -rf $(DESTDIR)$(bindir)/frepplectl

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

# Translations process:
# 1) Run "make extra-translations" to get all translatable strings from thr source code.
# 2) Translate all strings local/<LANGUAGE>/<LANGUAGE>.po file. The real work!
# 3) Run "make compile-translations" to merge the translations into the right places.

extract-translations:
	## extract django
	cd freppledb; django-admin.py makemessages --ignore node_modules --no-wrap -a -d django
	cd freppledb; django-admin.py makemessages --ignore node_modules --no-wrap -a -d djangojs

	## extract angular
	if test -n '$(NPM)' && test -n '$(GRUNT)'; then \
	  grunt nggettext_extract; \
	fi

	## Preparation for each language
	django=`python3 -c "import django; import os; print(os.path.dirname(django.__file__))"`; \
	for language in $$( ls freppledb/locale ); \
	do \
	  ## Build a compendium with known translations
	  msgcat --use-first $$django/conf/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/admin/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/admin/locale/$$language/LC_MESSAGES/djangojs.po \
	    $$django/contrib/admindocs/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/auth/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/contenttypes/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/flatpages/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/gis/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/humanize/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/postgres/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/redirects/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/sessions/locale/$$language/LC_MESSAGES/django.po \
	    $$django/contrib/sites/locale/$$language/LC_MESSAGES/django.po \
	    | msgattrib --translated --no-fuzzy -o freppledb/locale/$$language/djangocompendium.po; \
	  ## Combine all frepple strings coming from django, djangojs and angular
	  mv freppledb/locale/$$language/$$language.po freppledb/locale/$$language/$$language_old.po; \
	  msgcat --use-first freppledb/locale/$$language/LC_MESSAGES/djangojs.po \
	    freppledb/locale/$$language/LC_MESSAGES/django.po \
	    freppledb/common/static/common/po/$$( echo $$language | tr _ - ).po \
	    freppledb/common/static/common/po/template.pot \
	    -o freppledb/locale/$$language/$$language.po; \
	  ## Pick up known translations from the compendium
	  msgmerge --silent \
	    --compendium freppledb/locale/$$language/djangocompendium.po \
	    freppledb/locale/$$language/$$language_old.po \
	    freppledb/locale/$$language/$$language.po \
	    -o freppledb/locale/$$language/$$language.po; \
	  rm freppledb/locale/$$language/$$language_old.po freppledb/locale/$$language/djangocompendium.po; \
	done

compile-translations:
	## Preparation for each language
	django=/cygdrive/c/develop/python36/Lib/site-packages/django; \
	for language in $$( ls freppledb/locale ); \
	do \
	  ## Build a compendium with all translated frepple strings
	  msgattrib --translated --no-fuzzy \
	    freppledb/locale/$$language/$$language.po \
	    -o freppledb/locale/$$language/frepplecompendium.po; \
	  ## Update djangojs file from our compendium
	  mv freppledb/locale/$$language/LC_MESSAGES/djangojs.po \
	     freppledb/locale/$$language/LC_MESSAGES/djangojs.old.po; \
	  msgmerge --silent --compendium \
	    freppledb/locale/$$language/frepplecompendium.po \
	    freppledb/locale/$$language/$$language.po \
	    freppledb/locale/$$language/LC_MESSAGES/djangojs.old.po \
	    | msgattrib --no-obsolete --no-fuzzy -o freppledb/locale/$$language/LC_MESSAGES/djangojs.po; \
	  rm freppledb/locale/$$language/LC_MESSAGES/djangojs.old.po; \
	  ## Update django file from our compendium
	  mv freppledb/locale/$$language/LC_MESSAGES/django.po \
	     freppledb/locale/$$language/LC_MESSAGES/django.old.po; \
	  msgmerge --silent --compendium \
	    freppledb/locale/$$language/frepplecompendium.po \
	    freppledb/locale/$$language/$$language.po \
	    freppledb/locale/$$language/LC_MESSAGES/django.old.po \
	    | msgattrib --no-obsolete --no-fuzzy -o freppledb/locale/$$language/LC_MESSAGES/django.po; \
	  rm freppledb/locale/$$language/LC_MESSAGES/django.old.po; \
	  ## Update angular file from our compendium
	  mv freppledb/common/static/common/po/$$( echo $$language | tr _ - ).po \
	     freppledb/common/static/common/po/$$( echo $$language | tr _ - ).old.po; \
	  msgmerge --silent --compendium \
	    freppledb/locale/$$language/frepplecompendium.po \
	    freppledb/locale/$$language/$$language.po \
	    freppledb/common/static/common/po/$$( echo $$language | tr _ - ).old.po \
	    | msgattrib --no-obsolete --no-fuzzy -o freppledb/common/static/common/po/$$( echo $$language | tr _ - ).po; \
	  rm freppledb/common/static/common/po/$$( echo $$language | tr _ - ).old.po; \
	  rm freppledb/locale/$$language/frepplecompendium.po; \
	done

	## compile django 
	./frepplectl.py compilemessages

	## compile angular
	if test -n '$(NPM)' && test -n '$(GRUNT)'; then \
	  grunt nggettext_compile; \
	fi
