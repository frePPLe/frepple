
FILES_COMMON = generate.py frepple.doxyfile frepple.1 apiheader.html apifooter.html apistyles.css search.html

if DOC
EXTRA_DIST = html ${FILES_COMMON}
else
EXTRA_DIST = ${FILES_COMMON}
endif

all-local: doc

if DOC
doc:
	-rm -rf html
	-@WGET@ --mirror --adjust-extension --no-parent --convert-links \
    --exclude-directories='feed,*/feed,*/*/feed,*/*/*/feed,*/*/*/*/feed,*/*/*/*/*/feed' \
    --no-verbose --page-requisites --no-host-directories --directory-prefix=html \
    -e robots=off http://frepple.com/documentation/
	cp index.html html
	export PACKAGE_VERSION=$(PACKAGE_VERSION); `pwd`/generate.py
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile  
else
doc:
	echo Skipping generation of documentation...  
endif

clean-local:
	-rm -rf html

man_MANS = frepple.1

install-data-local: doc
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

.PHONY: doc clean-local uninstall-local install-data-local all-local
