=================
Extension modules
=================

FrePPLe is designed as an extendible framework. Additional modelling and
solver modules can be loaded at runtime without recompiling the core library.

Such extension modules can be shipped with frePPLe, or can be developed by
third parties. They can be open source or have a commercial license.

The steps below describe how a custom extension can be build on the framework.
An complete example is available in the test case 'sample_module', with a
Linux makefile and Visual Studio project.

* Create your own header files, and include the frePPLe header file
  frepple.h to have access to the frePPLe objects.

  A simple header file can look like this:

  ::

     #include "frepple.h"
     using namespace frepple;

     namespace your_module
     {
        MODULE_EXPORT const char* initialize(
          const CommandLoadLibrary::ParameterList& z
          );
        ...
        your classes and function definitions
        ...
     }

* Create your own C++ implementation files, which will include your customized
  header file.

  It is important is to include an initialize() method, and use it to register
  your extension in the frePPLe framework. The method is automatically called
  when the module is loaded.

  ::

     #include "your_module.h"
     namespace your_module
     {

     MODULE_EXPORT const char* initialize(
       const CommandLoadLibrary::ParameterList& z
       )
     {
       ...
       your initialization code goes here
       ...
     }

     your method and class implementations go here

* Compile your code as a loadable module.

  The command line options and arguments vary for each compiler and platform.
  For gcc I use the options '-module -shrext .so -avoid-version', adding also
  '-no-undefined' when running under Cygwin.

  To keep things simple and transparent please use the .so extension for your
  modules and place them in the $FREPPLE_HOME directory.

* Update the file frepple.xsd by defining the XML constructs enabled by
  your module.

  It is recommended to do this by including a separate XSD file rather than
  directly entering the definition in the file.
