============================================
Deployment on Windows with Apache web server
============================================

The windows installer installs a Python based web server. For environments
with a few concurrent users or for a trial installation this will suffice,
and it is the recommended configuration.

If the number of concurrent users is higher or when more complex configurations
are required on the network (such as HTTPS encryption, additional web pages
to be served from the same web server, access from the internet as well as
from the intranet, using external authentication instead, configure compression
and caching, etc…), you can deploy frePPLe with an Apache web server.

Note that scalability of the web application on Linux is significantly better
on Linux than on Windows. Environments with more than 20 concurrent users
should prefer Linux.

To configure frePPLe on Windows with an Apache web server, the following steps
are required:

#. Assure you **have administrator rights** on the machine.

#. **Install frePPLe** using the Windows installer, following the steps from the
   previous page.

#. **Collect all static files**

   The static files will be served by the Apache web server, and we need to
   collect all of these files in a separate folder.
   Open a command prompt in the bin folder of your frePPLe installation and run:
   ::

     frepplectl collectstatic

#. **Install PostgreSQL database.**

   The recommended version is 9.3, 64-bit. Information on tuning the database
   configuration is easily found on Google.

#. **Install Python 2.7**

   The download URL is http://www.python.org/download/releases/2.7/
   Use the 32-bit version, even on 64-bit platforms.

#. **Install Psycopg2**

   The Python database driver for PostgreSQLcan be downloaded from
   http://stickpeople.com/projects/python/win-psycopg/

   Pick the executable for Python 2.7. The executable built for PostgreSQL 9.2
   also works with PostgreSQL 9.3.

#. **Install PyWin32**

   The Python Windows extensions can be downloaded from
   http://sourceforge.net/projects/pywin32/

   Select the 32-bit installer for Python 2.7.

#. **Install django**

   Django is a high-level Python Web framework.

   You will need to:

     #. Download django 1.6.x from https://www.djangoproject.com/download/

     #. Apply the patch you find in contrib/django/django.patch

     #. Install django with the command:
        ::

           python setup.py install

#. **Install openpyxl**

   OpenPyXL is a Python library to read/write Excel 2007 xlsx/xlsm files

   First install PIP wich you can find on http://www.lfd.uci.edu/~gohlke/pythonlibs/#pip

   Next, run this command from the Scripts folder in your Python installation:
   ::

      pip install openpyxl

#. **Install cherrypy**:

   CherryPy is pythonic, object-oriented HTTP framework available from
   http://download.cherrypy.org/cherrypy/3.2.2/

#. **Install Apache web server**

   Recommended download is http://www.apachelounge.com/download/win32/: 2.4.7, 32-bit, vc10

   It is easiest to run Apache as a service.

#. **Install mod_wsgi**

   Mod_wsgi is python WSGI adapter module for Apache.

   The download URL is http://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi
   Choose the 32-bit for Python 2.7 and Apache 2.4, and copy the file to the Apache
   modules folder.

#. **Configure the Apache web server**

   Add a line to the file conf/httpd.conf:

   ::

       Include conf/extra/httpd-frepple.conf

   Create a file conf/extra/httpd-frepple.conf using the example we provide in
   the file contrib/debian/httpd/conf.
   Adjust the paths, review carefully, and tweak to your preferences and needs!

#. **Test the setup**

   Open your browser and verify the frePPLe pages display correctly.
