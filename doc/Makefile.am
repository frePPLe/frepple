
EXTRA_DIST_COMMON = favicon.ico styles.css *.pdf *.gif *.bmp 
EXTRA_DIST_API = reference
EXTRA_DIST_WEB = Frepple UI Tutorial Main uploads uploads/Frepple uploads/UI uploads/Tutorial pmwiki.css index.html 
EXTRA_DIST = ${EXTRA_DIST_COMMON} frepple.doxyfile frepple.1

reference: apidoc
Frepple: webdoc

if APIDOC
EXTRA_DIST += ${EXTRA_DIST_API}
apidoc: frepple.doxyfile
	-rm -rf reference
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile
else
apidoc:
	-echo Skipping generation of API documentation...
endif

if WEBDOC
EXTRA_DIST += ${EXTRA_DIST_WEB}
webdoc:
	-rm -rf www.frepple.com ${EXTRA_DIST_WEB}
	-@WGET@ -r -k -p -nv -l 0 --html-extension http://www.frepple.com/pmwiki/pmwiki.php/Main/HomePage?setskin=doc 
	mv www.frepple.com/pmwiki/pmwiki.php/* .
	mv www.frepple.com/pmwiki/uploads uploads
	mv www.frepple.com/pmwiki/pub/skins/doc/pmwiki.css .
	mv www.frepple.com/pmwiki/pmwiki.php.1.html index.html
	-rm -rf www.frepple.com
	find . -regex '[^reference/].*\.html' -exec sed -i "s|href='\(\.\./\)*pmwiki.php.1.html'>Main|href='\1index.html'>Main|" {} \; 
	find . -regex '[^reference/].*\.html' -exec sed -i "s|href='\(\.\./\)*pmwiki.php.1.html'>C++|href='\1reference/index.html'>C++|" {} \; 
	find . -regex '[^reference/].*\.html' -exec sed -i "s|href='\(\.\./\)*pmwiki.php/|href='\1|g" {} \;
	find . -regex '[^reference/].*\.html' -exec sed -i "s|href='\(\.\./\)*pub/skins/doc/pmwiki.css'|href='\1pmwiki.css'|" {} \; 
	find . -regex '[^reference/].*\.html' -exec sed -i "s|src='\(\.\./\)*../uploads/|src='\1uploads/|g" {} \; 
	find . -regex '[^reference/].*\.html' -exec sed -i "s|src='\(\.\./\)*../../images/frepple.bmp'|src='\1frepple.bmp'|" {} \; 
	find . -regex '[^reference/].*\.html' -exec sed -i "s|href='\(\.\./\)*../../styles.css'|href='\1styles.css'|" {} \; 
	sed -i "s|src='../images/frepple.bmp'|src='frepple.bmp'|" index.html 
	sed -i "s|href='../styles.css'|href='styles.css'|" index.html 
else
webdoc:
	-echo Skipping generation of WEB documentation...
endif

clean-local:
	-rm -rf pmwiki.css index.html ${EXTRA_DIST_API} ${EXTRA_DIST_WEB}

all-local: apidoc webdoc

man_MANS = frepple.1

if DOC 
install-data-local: apidoc webdoc
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	for p in $(EXTRA_DIST_COMMON) $(EXTRA_DIST_API) $(EXTRA_DIST_WEB); do \
	  if test -e $$p; \
	  then if test -d $$p; \
	  then $(mkinstalldirs) "$(DESTDIR)$(docdir)/$$p"; \
	       $(INSTALL_DATA) $$p/* "$(DESTDIR)$(docdir)/$$p"; \
	  else $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	  fi; \
	  fi; \
	done
endif

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: apidoc webdoc clean-local uninstall-local install-data-local all-local
