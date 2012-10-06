
FILES_COMMON = favicon.ico *.pdf 
FILES_API = reference
FILES_WEB = index.html Frepple UI Tutorial License Developer Installation Main uploads uploads/Frepple uploads/UI uploads/Tutorial uploads/Installation uploads/Developer js images css
FILES_EXTRA = htmlindexer.py frepple.doxyfile frepple.1 apiheader.html apifooter.html api_styles.css search.html index.js

if APIDOC
if WEBDOC 
EXTRA_DIST = ${FILES_WEB} ${FILES_API} ${FILES_COMMON} ${FILES_EXTRA} 
else
EXTRA_DIST =  ${FILES_API} ${FILES_COMMON} ${FILES_EXTRA}
endif
else
if WEBDOC 
EXTRA_DIST = ${FILES_WEB} ${FILES_COMMON} ${FILES_EXTRA} 
else
EXTRA_DIST = ${FILES_COMMON} ${FILES_EXTRA}
endif
endif

if APIDOC
apidoc: reference
reference: 
	-rm -rf reference
	export PACKAGE_VERSION=$(PACKAGE_VERSION) HAVE_DOT=${HAVE_DOT}; @DOXYGEN@ frepple.doxyfile
else
apidoc:
	-echo Skipping generation of API documentation...
endif

if WEBDOC
webdoc: index.html
index.html: 
	-rm -rf frepple.com ${FILES_WEB}
	-@WGET@ -k -r -nv --html-extension http://frepple.com/pmwiki/pmwiki.php/Main/HomePage?setskin=doc
	mv frepple.com/js .
	mv frepple.com/css .
	mv frepple.com/images .
	mv frepple.com/pmwiki/pmwiki.php/* .
	mv frepple.com/pmwiki/uploads uploads
	-rm -rf frepple.com	
	sed -i "s|action='\(\.\./\)*Main/HomePage.html'>|action='\1search.html'>|g" `find . -name '*\.html' -print | grep -v '^\./reference'` 
	sed -i "s|href='\(\.\./\)*pmwiki.php/|href='\1|g" `find . -name '*\.html' -print | grep -v '^\./reference'` 
	sed -i "s|href='\(\.\./\)*Frepple/Main.html'>C++|href='\1reference/index.html'>C++|g" `find . -name '*\.html' -print | grep -v '^\./reference'` 
	sed -i "s|src='\(\.\./\)*../uploads/|src='\1uploads/|g" `find . -name '*\.html' -print | grep -v '^\./reference'` 
	sed -i "s|href='\(\.\./\)*../../css/|href='\1css/|g" `find . -name '*\.html' -print | grep -v '^\./reference'` 
	sed -i "s|src='\(\.\./\)*../../js/|src='\1js/|g" `find . -name '*\.html' -print | grep -v '^\./reference'` 
	sed -i "s|href='HomePage.html'>C++|href='../reference/index.html'>C++|g" Main/HomePage.html Main/FAQ.html
	sed -i "s|action='HomePage.html'>|action='../search.html'>|g" Main/HomePage.html Main/FAQ.html
	cp Main/HomePage.html index.html
	sed -i "s|\.\./||g" index.html 
	sed -i "s|FAQ.html|Main/FAQ.html|g" index.html 
	`pwd`/htmlindexer.py UI Frepple Main Tutorial License Installation Developer
else
webdoc:
	-echo Skipping generation of WEB documentation...
endif

clean-local:
	-rm -rf index.js index.html ${FILES_API} ${FILES_WEB} frepple.com

all-local: apidoc webdoc

man_MANS = frepple.1

install-data-local: apidoc webdoc
	echo "Installing documentation in $(DESTDIR)$(docdir)"; \
	for p in $(FILES_COMMON) $(FILES_API) $(FILES_WEB); do \
	  if test -e $$p; \
	  then if test -d $$p; \
	  then $(mkinstalldirs) "$(DESTDIR)$(docdir)/$$p"; \
	       $(INSTALL_DATA) $$p/* "$(DESTDIR)$(docdir)/$$p"; \
	  else $(INSTALL_DATA) $$p "$(DESTDIR)$(docdir)/$$p"; \
	  fi; \
	  fi; \
	done

uninstall-local:
	-rm -rf $(DESTDIR)$(docdir)

.PHONY: apidoc webdoc clean-local uninstall-local install-data-local all-local
