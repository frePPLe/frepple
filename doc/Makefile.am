
EXTRA_DIST = frepple.doxyfile frepple.1 frepplectl.1 conf.py index.rst license.rst faq.rst
EXTRA_DIST += _templates cookbook extension-modules installation-guide model-reference technical-guide user-guide

man_MANS = frepple.1 frepplectl.1

if DOC

all-local: sphinx

sphinx:
	-rm -rf _build _html
	@SPHINXBUILD@ -a -E -b html -d _build/doctrees . _build/html

doxygen:
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile

clean-local:
	-rm -rf _build *.pyc *.pyo html

install-data-local: rebuildHTML
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	find _build/html -type d -exec $(mkinstalldirs) "$(DESTDIR)$(docdir)/{}" \;; \
	for p in `find _build/html -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: clean-local uninstall-local install-data-local all-local rebuildHTML

endif
