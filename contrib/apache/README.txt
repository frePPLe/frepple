
This directory creates a simple user interface for Frepple.
It consists of an Apache web server module and some static web pages.

The Apache plugin loads the frepple library. 
The module then can serve data to client browsers. All these report
data are in XML format that is then processed further on the browser.
The module can also receive XML formatted data input. The data is 
parsed and processed by frepple.

The web pages implement a simple (and still experimental) user 
interface. The pages are based on the AJAX principles, and heavily rely
on JavaScript, Dynamic HTML and Cascading Stylesheets.
Currently only Internet Explorer 6 is supported!

Follow these steps to get up and running:

1) Install the following packages on your machine:
      - Apache 2.0.*
   Apache 1.x is incompatible with the code.

2) Compile the new module with the command:
     make build

3) Edit the frepple.conf file
   This file contains a bare-bone Apache configuration for running the 
   Frepple module.
   It is by no means intended to be complete. You will need to update the
   settings to meet your taste and requirements.
   The paths in the file coming with the distribution will definately 
   need to be edited.

4) Start the web server with the command:
     make start
   Depending on your environment and operating system you may need additional
   steps to get the web server up and running.
   E.g. On cygwin, you need to configure the cygwin server and set an extra
        environment variable:  export CYGWIN=server
   E.g. On *nix systems, users normally won't have permissions to start a
        server on a port number less than 1024.
        Login as root user, or choose a different port number.

Enjoy
