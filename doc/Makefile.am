
EXTRA_DIST = planner.doxyfile header.doxyfile reference/* *.html *.css *.pdf *.jpg *.gif

SUBDIRS = tutorial

# This points to the installation directory of the documentation
INSTALL_DIR=$(prefix)/doc/$(PACKAGE)-$(PACKAGE_VERSION)

if DOC
reference/index.html: clean planner.doxyfile
	-rm -rf reference planner.tags
	export PACKAGE_VERSION=$(PACKAGE_VERSION); @DOXYGEN@ planner.doxyfile
else
reference/index.html: clean
	-echo Skipping generation of documentation...
endif

clean-local:
	-rm -rf reference planner.tags

all-local: reference/index.html

install-data-local:
	$(mkinstalldirs) $(INSTALL_DIR)/reference
	for p in $(EXTRA_DIST); do \
	  $(INSTALL_DATA) $$p $(INSTALL_DIR)/$$p; \
	done

uninstall-local:
	rm -rf $(INSTALL_DIR)

.PHONY: clean-local uninstall-local install-data-local all-local

dist: reference/index.html