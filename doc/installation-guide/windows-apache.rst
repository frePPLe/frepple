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

   The recommended version is 10.x 64-bit. It is recommended to tune the database
   parameters with the values found on http://pgtune.leopard.in.ua/.

#. **Install Python 3.5 64-bit or higher**

   The download URL is http://www.python.org/download/releases/3.5/

#. **Install Psycopg2**

   The Python database driver for PostgreSQLcan be downloaded from
   http://stickpeople.com/projects/python/win-psycopg/

   Pick the executable that matches the Python version. 

#. **Install PyWin32**

   The Python Windows extensions can be downloaded from
   http://sourceforge.net/projects/pywin32/

   Select the 64-bit installer for Python 3.5.

#. **Install the Python database drivers, Django and other python modules**

   Since frePPle requires some patches to the standard Django package, so the source
   from our cloned and patched version of django will be downloaded and installed.

   In the root of your Python install you will find a "requirements.txt" file containing a list as 
   shown below. You can always pick up the correct version from 
   https://raw.githubusercontent.com/frepple/frepple/4.2/requirements.txt
   (make sure to replace 4.2 with the appropriate version number!)
   
   ::

      CherryPy >= 3.2.2
      CherryPy == 5.1.0
      djangorestframework == 3.6.2
      djangorestframework-bulk == 0.2.1
      djangorestframework-filters == 0.10.0
      django-admin-bootstrapped
      django-bootstrap3 == 8.2.2
      html5lib == 0.999
      jdcal == 1.0.1
      Markdown == 2.6.8
      openpyxl == 2.4.7
      lxml == 3.7.3
      PyJWT == 1.5.0
      https://github.com/frePPLe/django/tarball/frepple_4.2

   To install the requirements just issue a pip3 command:
   ::

      sudo pip install -r requirements.txt

#. **Install mod_wsgi**

   Mod_wsgi is python WSGI adapter module for Apache.

   The download URL is http://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi
   Choose the 64-bit for Python 3.5 and Apache 2.4, and copy the file to the Apache
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
