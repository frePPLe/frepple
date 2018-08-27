
EXTRA_DIST = frepple.doxyfile frepple.1 frepplectl.1 frepple.py conf.py build.bat *.rst
EXTRA_DIST += _templates installation-guide developer-guide user-guide

man_MANS = frepple.1 frepplectl.1

if DOC

all-local: sphinx

sphinx:
	-rm -rf _build
	@SPHINXBUILD@ -a -E -b html -d _build/doctrees . _build/html

doxygen:
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile

clean-local:
	-rm -rf _build *.pyc *.pyo

install-data-local:
	cd _build; \
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	find html -type d -exec $(mkinstalldirs) "$(DESTDIR)$(docdir)/{}" \;; \
	for p in `find html -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: clean-local uninstall-local install-data-local all-local rebuildHTML

endif
