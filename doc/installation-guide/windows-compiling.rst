====================
Compiling on Windows
====================

Here are the steps to compile frePPLe under Windows with Microsoft Visual Studio.

* First, install the following third party tools:

  - | **Python 3.6 or higher**
    | Install the 64-bit version of Python 3.
    | https://www.python.org/downloads/

  - | **Microsoft Visual Studio C++ 2019**.
    | The community edition is sufficient.
    | https://visualstudio.microsoft.com/vs/
    
  - | **CMake tools foor Visual Studio**
    | This plugin integrates cmake into the Visual Studio IDE.
    | https://marketplace.visualstudio.com/items?itemName=ms-vscode.cmake-tools

  - | **Xerces-C 3.1.3**
    | You will have to compile this package from source. The xerces-c team
      provides a Visual Studio file that can be used to create a 64-bit static
      library.
    | https://xerces.apache.org/xerces-c/download.cgi

  - | **PostgreSQL 10 or higher**
    | You'll need the PostgreSQL relational database. 

- | **Download the source code** from https://github.com/frePPLe/frepple

- | **Install the required Python packages** 
  | The source code contains a requirements.txt with a list of all packages. You install them with pip:
  
  ::
   
      python -m pip install -r requirements.txt
  
- | **Option 1: Open the Visual studio project**
  | In Windows Explorer, right click on any source code folder and select "Open with Visual Studio".
  | Visual Studio will start and configure the project. Visual Studio will report if python or xerces-c
    aren't be found. When these are available you're all set to compile the project. 

- | **Option 2: Use Cmake from the command line**
  | This is an alternative to the previous step.
  | Open a Visual Studio Developer command shell and run the standard CMake build steps:
  
  ::
  
     # Make a build folder
     cd <your-source-folder>
     mkdir build 
     cd build 
     
     # Configure the environment.
     # If python or xercesc are not found, you'll get errors here.
     cmake ..
     
     # Compile the source code
     cmake --build . --config Release
     
- | **Test the result**:
  | Finally, let's check if it all worked.

  - After successful compilation you will find your binaries in the folder <your-source-folder>/bin.
  
  - Run the unit test suite:
  
    ::
    
       cd <your-source-folder>\test
       python runtest.py --regression
    