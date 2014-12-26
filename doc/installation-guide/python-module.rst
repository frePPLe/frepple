========================================
Configuring as a Python extension module
========================================

FrePPLe can be set up as a Python extension module. Your Python program can
simply import the module to have full access to the frePPLe objects and all
planning functionality.

Here are the steps to get it up and running:

* On **windows**, copy the file frepple.dll as frepple.pyd, and place it
  in the site-packages folder (found at <Python installation folder>\Lib\site-packages).

* On **linux**, copy the file libfrepple.so to frepple.so, and place it in
  your site-packages folder (typically found at /usr/lib/pythonX.Y/site-packages).

* Alternatively or if you don't have write privileges to the site-packages folder,
  you can also modify the module search path in your application.
  This assures the frepple.so (or frepple.dll on Windows) file is found.

  Solution 1:
  ::

     import site
     site.addsitedir("Folder with .pyd/.so file")

  Solution 2:
  ::

     import sys
     sys.path.append("Folder with .pyd/.so file")

* Your Python program can now import frePPLe as a regular extension module.
  ::

     import frepple