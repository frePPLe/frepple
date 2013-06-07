
FILES_COMMON = generate.py frepple.doxyfile frepple.1 apiheader.html apifooter.html apistyles.css search.html index.html

if DOC
EXTRA_DIST = html ${FILES_COMMON}
else
EXTRA_DIST = ${FILES_COMMON}
endif

all-local: htmlfolder

if DOC
htmlfolder:
	-rm -rf html
	-@WGET@ --mirror --adjust-extension --no-parent --convert-links \
    --exclude-directories='feed,*/feed,*/*/feed,*/*/*/feed,*/*/*/*/feed,*/*/*/*/*/feed' \
    --no-verbose --page-requisites --no-host-directories --directory-prefix=html \
    -e robots=off http://frepple.com/documentation/
	cp index.html html
	export PACKAGE_VERSION=$(PACKAGE_VERSION); `pwd`/generate.py
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile    
else
htmlfolder:
	echo Skipping generation of documentation...  
endif

clean-local:
	-rm -rf html

man_MANS = frepple.1

install-data-local: htmlfolder
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	find html -type d -exec $(mkinstalldirs) "$(DESTDIR)$(docdir)/{}" \;; \
	for p in `find html -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: clean-local uninstall-local install-data-local all-local
