============================================
Deployment on Windows with Apache web server
============================================

.. warning:: This deployment method is deprecated. Installing on Linux
             is the right option to give the best scalability and performance
             in more demanding deployments.

The windows installer installs a Python based web server. For environments
with a few concurrent users or for a trial installation this will suffice.

If the number of concurrent users is higher or when more complex configurations
are required on the network (such as HTTPS encryption, additional web pages
to be served from the same web server, access from the internet as well as
from the intranet, using external authentication instead, configure compression
and caching, etc…), you can deploy frePPLe with an Apache web server.

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

#. **Install Python 3.6 64-bit or higher**

   The download URL is http://www.python.org/download/releases/3.6/

#. **Install the Python database drivers, Django and other python modules**

   The following pip commands install all Python third party packages
   used by frePPLe.

   :: 
   
      pip3 install psycopg2-binary pywin32
      pip3 install -r https://raw.githubusercontent.com/frepple/frepple/6.0.0/requirements.txt

#. **Install mod_wsgi**

   Mod_wsgi is python WSGI adapter module for Apache.

   The download URL is http://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi
   Choose the 64-bit for Python 3.6 and Apache 2.4, and copy the file to the Apache
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
