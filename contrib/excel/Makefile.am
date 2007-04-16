#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.xls frepple.xsd commands.xml README.txt xercesc-LICENSE

clean-local:
	-rm -rf frepple-excel

contrib:
	-rm -rf frepple-excel
	mkdir frepple-excel
	cp ../../bin/frepple.exe frepple-excel/frepple.exe
	cp `which xerces-c_2_7.dll` frepple-excel
	cp ../../COPYING frepple-excel/LICENSE
	cp frepple.xsd frepple-excel
	cp frepple.xls frepple-excel
	cp xercesc-LICENSE frepple-excel
	echo Zip the folder "frepple-excel" to distribute
