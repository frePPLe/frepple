==================================
Running the VMWare virtual machine
==================================

.. caution::

   This virtual machine is **NOT** intended for use as a production
   environment. It is intended as evaluation, education or test environment.

A VMware virtual machine is available with a demo and development environment.

The setup is based on a **Ubuntu 14.04.1 LTS Server** Linux distribution and
has the following software installed:

* postgresql database server
* apache web server, using the mod_wsgi module
* full C++ and python2 development stack
* ssh access

The machines is configured with two CPU cores, 500MB of RAM and a bridged
network connection. VMware tools are not installed. Feel free to update
the settings to suit your hardware.

To get up and running:

#. Download and install the VMWare player from http://www.vmware.com/.

#. Download and unzip the virtual machine from the sourceforge site.

#. Using the VMware console open the virtual machine ubuntu.vmx and
   start it.

#. When started the login screen will display the URL where you can browse
   the demo environment.

#. Instructions about login details, user accounts, database instance, etc
   will be displayed on the login screen. They are also available in the
   README.txt file included with the virtual machine.
