========================================
Configuring as a Python extension module
========================================

FrePPLe can be set up as a Python extension module. Your Python program can
simply import the module to have full access to the frePPLe objects and all
planning functionality.

* On **windows**, copy the file frepple.pyd into the site-packages folder (found
  at <Python installation folder>\Lib\site-packages).

  The file frepple.dll and its extension libraries must be found in the PATH, or
  be placed in the working directory from which you'll be running Python.

* On **linux**, the installation procedure will already copy the all files
  to the right folder. No additional configuration steps are required.

* Your Python program can now import frePPLe as a regular extension module.
  ::

     import frepple
