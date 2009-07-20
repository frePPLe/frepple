
EXTRA_DIST = frepple.doxyfile favicon.ico *.html *.css *.pdf *.gif *.bmp frepple.1

if DOC
EXTRA_DIST += reference
reference: clean frepple.doxyfile
	-rm -rf reference frepple.tags
	export PACKAGE_VERSION=$(PACKAGE_VERSION); @DOXYGEN@ frepple.doxyfile
else
reference:
	-echo Skipping generation of documentation...
endif

clean-local:
	-rm -rf reference frepple.tags

all-local: reference

if DOC

man_MANS = frepple.1

install-data-local:
	echo "installing documentation in $(DESTDIR)$(docdir)"; \
	$(mkinstalldirs) "$(DESTDIR)$(docdir)/reference"; \
	for p in $(EXTRA_DIST); do \
	  if test -d $$p; \
	  then $(mkinstalldirs) "$(DESTDIR)$(docdir)/$$p"; \
	       $(INSTALL_DATA) $$p/* "$(DESTDIR)$(docdir)/$$p"; \
	  else $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	  fi; \
	done

endif

uninstall-local:
	-rm -rf "$(DESTDIR)$(docdir)"

.PHONY: reference clean-local uninstall-local install-data-local all-local

