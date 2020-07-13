
DOC_DIRS = developer-guide installation-guide integration-guide examples modeling-wizard model-reference user-interface videos _templates
DOC_FILES = $(shell find . -type f -name '*.rst') $(shell find . -type f -name '*.png')

EXTRA_DIST = frepple.1 frepplectl.1 frepple.py conf.py build.bat *.rst
EXTRA_DIST += $(DOC_DIRS)

man_MANS = frepple.1 frepplectl.1

if DOC

all: _build

_build: $(DOC_DIRS) $(DOC_FILES)
	-rm -rf _build
	@SPHINXBUILD@ -a -E -b html -d _build/doctrees . _build/html

install-data-local: all
	cd _build; \
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	find html -type d -exec $(mkinstalldirs) "$(DESTDIR)$(docdir)/{}" \;; \
	for p in `find html -type f`; do \
	  $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: clean-local uninstall-local install-data-local all

endif

clean-local:
	-rm -rf _build __pycache__
