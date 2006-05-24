#
# Process this file with automake to produce Makefile.in
#

SUBDIRS =

EXTRA_DIST = frepple.wsdl client.vcproj dll.vcproj staticlib.vcproj webservice.sln clientmain.cpp README.txt

#AXIS = c:/develop/packages/axis-c-1-1-win32
AXIS = C:/develop/Apache/axis-c-win32-bin
CLASSPATH = '$(AXIS)/lib/axisjava/axis.jar;$(AXIS)/lib/axisjava/commons-discovery.jar;$(AXIS)/lib/axisjava/commons-logging.jar;$(AXIS)/lib/axisjava/jaxrpc.jar;$(AXIS)/lib/axisjava/saaj.jar;$(AXIS)/lib/axisjava/wsdl4j.jar;$(AXIS)/lib/axis/wsdl2ws.jar;.'

.PHONY: $(.PHONY) serverout clientout

clean-local:
	rm -rf serverout clientout *debug *release

contrib: serverout clientout

serverout: frepple.wsdl
	java -classpath $(CLASSPATH) org.apache.axis.wsdl.wsdl2ws.WSDL2Ws frepple.wsdl -o./serverout -lc++ -sserver

clientout: frepple.wsdl
	java -classpath $(CLASSPATH) org.apache.axis.wsdl.wsdl2ws.WSDL2Ws frepple.wsdl -o./clientout -lc++ -sclient

tcpmon:
	java -classpath $(CLASSPATH) org.apache.axis.utils.tcpmon