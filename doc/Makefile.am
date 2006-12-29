
EXTRA_DIST = planner.doxyfile header.doxyfile favicon.ico *.html *.css *.pdf *.jpg *.gif *.bmp

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
	case $$prefix in \
	    /usr*) docdir="/usr/share/doc/$(PACKAGE_NAME)-$(PACKAGE_VERSION)";; \
	    *) docdir="$(prefix)/doc/$(PACKAGE_NAME)-$(PACKAGE_VERSION)";; \
	esac; \
	echo "installing documentation in $$docdir"; \
	$(mkinstalldirs) $$docdir/reference; \
	for p in $(EXTRA_DIST); do \
	  if test -d $$p; \
	  then $(mkinstalldirs) $$docdir/$$p; \
	       $(INSTALL_DATA) $$p/* $$docdir/$$p; \
	  else $(INSTALL_DATA) $$p $$docdir/$$p; \
	  fi; \
	done
endif

uninstall-local:
	rm -rf $(docdir)

.PHONY: reference clean-local uninstall-local install-data-local all-local

