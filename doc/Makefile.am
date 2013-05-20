
FILES_COMMON = generate.py frepple.doxyfile frepple.1 apiheader.html apifooter.html apistyles.css search.html

if APIDOC
if WEBDOC 
EXTRA_DIST = html ${FILES_COMMON}
else
EXTRA_DIST =  html ${FILES_COMMON}
endif
else
if WEBDOC 
EXTRA_DIST = html ${FILES_COMMON} 
else
EXTRA_DIST = ${FILES_COMMON}
endif
endif

if APIDOC
apidoc: html/api
html/api: 
	-mkdir -p html
	-rm -rf html/api
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile
else
apidoc:
	-echo Skipping generation of API documentation...
endif

if WEBDOC
webdoc: html/index.html
html/index.html: 
	-rm -rf html
	-@WGET@ --mirror --adjust-extension --no-parent --convert-links --exclude-directories='feed,*/feed,*/*/feed,*/*/*/feed,*/*/*/*/feed,*/*/*/*/*/feed' --no-verbose --page-requisites --no-host-directories --directory-prefix=html -e robots=off http://frepple.com/documentation/
	-cp index.html html
	export PACKAGE_VERSION=$(PACKAGE_VERSION); `pwd`/generate.py
else
webdoc:
	-echo Skipping generation of WEB documentation...
endif

clean-local:
	-rm -rf html frepple.com

all-local: webdoc apidoc

man_MANS = frepple.1

install-data-local: apidoc webdoc
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	for p in html; do \
	  if test -e $$p; \
	  then if test -d $$p; \
	  then $(mkinstalldirs) "$(DESTDIR)$(docdir)/$$p"; \
	       $(INSTALL_DATA) $$p/* "$(DESTDIR)$(docdir)/$$p"; \
	  else $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	  fi; \
	  fi; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: apidoc webdoc clean-local uninstall-local install-data-local all-local
