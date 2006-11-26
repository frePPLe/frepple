
EXTRA_DIST = planner.doxyfile header.doxyfile favicon.ico tutorial *.html *.css *.pdf *.jpg *.gif *.bmp

# This points to the installation directory of the documentation
INSTALL_DIR=$(prefix)/share/doc/$(PACKAGE)-$(PACKAGE_VERSION)

if DOC
EXTRA_DIST += reference
reference: clean planner.doxyfile
	-rm -rf reference planner.tags
	export PACKAGE_VERSION=$(PACKAGE_VERSION); @DOXYGEN@ planner.doxyfile
else
reference: 
	-echo Skipping generation of documentation...
endif

clean-local:
	-rm -rf reference planner.tags

all-local: reference

if DOC
install-data-local:
	$(mkinstalldirs) $(INSTALL_DIR)/reference
	for p in $(EXTRA_DIST); do \
	  if test -d $$p; \
	   then $(INSTALL_DATA) -d $$p $(INSTALL_DIR)/$$p; \
	        $(INSTALL_DATA) $$p/* $(INSTALL_DIR)/$$p; \
	   else $(INSTALL_DATA) $$p $(INSTALL_DIR)/$$p; \
          fi; \
	done
endif

uninstall-local:
	rm -rf $(INSTALL_DIR)

.PHONY: reference clean-local uninstall-local install-data-local all-local

