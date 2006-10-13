
This directory creates a simple user interface for Frepple.
It consists of an Apache web server module and some static web pages.

The Apache plugin loads the frepple library. 
The module then can serve data to client browsers. All these report
data are in XML format that is then processed further on the browser.
The module can also receive XML formatted data input. The data is 
parsed and processed by frepple.

The web pages are based on the AJAX principles, and heavily rely on 
JavaScript, Dynamic HTML and Cascading Stylesheets.

The user interface works both in HTTP and in HTTPS (ie encrypted) mode.
For the HTTPS mode, a sample key and certificate are included. 

Currently only the Firefox browser is supported! :-( Due to incompatibel
javascript functions...

Follow these steps to get up and running:

1) Install the following packages on your machine:
      - Apache 2.2.*
      - OpenSSL development libraries, in case you want to use SSL 
   The code is not compatible with Apache 1.x
   
2) In some cases you may need to rebuild the apache executables and/or
   update your apache configuration:
    - make sure a single-process MPM is enabled
    - configure SSL key and certificate, if SSL support is required
   The file Makefile.am give as an example the commands I used to 
   compile apache on my pc running Linux 
   If you want to use SSL, you should not use the key and certificate 
   included here. For security reasons you need to create your own!!!

3) Compile the new module with the command:
     make build

4) Edit the frepple.conf file
   This file contains a bare-bone Apache configuration for running the 
   Frepple module.
   It is by no means intended to be complete. You will need to update the
   settings to meet your taste and requirements.
   The paths in the file coming with the distribution will definately 
   need to be edited.

5) Start the web server with the command:
     make start
   Depending on your environment and operating system you may need additional
   steps to get the web server up and running.
   E.g. On cygwin, you need to configure the cygwin server and set an extra
        environment variable:  export CYGWIN=server
   E.g. On *nix systems, users normally won't have permissions to start a
        server on a port number less than 1024.
   E.g. The start up with HTTPS support, edit the Makefile.am file.
        The password phrase for the SSL startup is 'frepple'.

6) Stopping the web server is done with the command:
     make stop

Enjoy
