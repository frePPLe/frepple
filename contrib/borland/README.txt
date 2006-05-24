
               BUILD INSTRUCTIONS ON WINDOWS 
               -----------------------------		
        USING THE BORLAND C++ COMMAND LINE COMPILER
        -------------------------------------------

The Frepple source distribution comes with Borland C++ Compiler make files. 
The following describes the steps you need to build Frepple.

1. Install xerces-c and follow the build instructions for the Borland
   compiler.
   
2. Open a command shell and change directory to:
     <frepple_installation_directory>/contrib/bcc.551

3. Edit the following variables in the file frepple.mak
     a. ROOT: Refers to the frepple installation directory
     b. XERCES: Refers to a directory where the xerces has been installed.
                Both the library file and the include files are expected in
                this directory
     c. XERCESVERSION: Refers to the xerces version being used. The default
                       value is 2_6_0. This variable is used to build the 
                       correct filename of the xerces library.
                          
4. Issue the command:
      <borland directory>/bin/make -f frepple.mak
   It will compile the code and create the executables.
   The final executables will be generated in the directory 
   		<frepple_installation_directory>/bin
   (Make sure to use the Borland make. Avoid mixing it up with other build
   executables, such as cygwin's gnu make.)
   
5. When using the executable, remember to include the xercess dll directory 
   in the path.
 
