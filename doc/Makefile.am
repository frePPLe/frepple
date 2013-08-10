
FILES_COMMON = generate.py frepple.doxyfile frepple.1 frepplectl.1 apiheader.html apifooter.html apistyles.css search.html index.html

if DOC
EXTRA_DIST = output ${FILES_COMMON}
else
EXTRA_DIST = ${FILES_COMMON}
endif

all-local: output

if DOC
output:
	-rm -rf output
	-@WGET@ --recursive --level 10 --adjust-extension --no-parent --convert-links \
    --exclude-directories='feed,*/feed,*/*/feed,*/*/*/feed,*/*/*/*/feed,*/*/*/*/*/feed' \
    --no-verbose --page-requisites --no-host-directories --directory-prefix=output \
    -e robots=off http://frepple.com/documentation/
	cp index.html output
	sed 's/%VERSION%/$(PACKAGE_VERSION)/' search.html > output/search.html
	export PACKAGE_VERSION=$(PACKAGE_VERSION); `pwd`/generate.py
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile
else
output:
	echo Skipping generation of documentation...
endif

clean-local:
	-rm -rf output

man_MANS = frepple.1 frepplectl.1

install-data-local: output
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	find output -type d -exec $(mkinstalldirs) "$(DESTDIR)$(docdir)/{}" \;; \
	for p in `find output -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	done
	mv "$(DESTDIR)$(docdir)/output" "$(DESTDIR)$(docdir)/html"

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: clean-local uninstall-local install-data-local all-local
