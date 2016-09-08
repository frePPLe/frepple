=======
frepple
=======

This executable runs the planning engine and solver.
The program reads XML input data, and executes Python command using the
embedded Python interpreter.

This executable is only relevant when you use only the frePPLe solver
functionality in the back end and you have developed your own front end and
data store.

**For all other purposes, it is recommended to use the command
‘frepplectl frepple_run’ instead of this executable.**

Usage:

* | **frepple [options] [files | directories]**
  | Passing one or more XML files and/or directories.
  | When a directory is specified, the application will process all files in
    it with the extension ‘.xml’ in alphabetical order.

* | **frepple [options]**
  | Without any file or directory arguments, input will be read from the
    standard input. Output from other programs can be piped to the command.

Options:

* | **-validate -v**:
  | Validate the XML input for correctness, as defined in the frepple.xsd schema.
  | This validation is disabled by default.

* | **-check -c**:
  | Only validate the input, without executing the content.

* | **-? -h -help**:
  | Show help.

The program will automatically execute the commands in the init.xml and init.py files.

The variable FREPPLE_HOME optionally points to a directory where the initialization
files init.xml, init.py, frepple.xsd and module libraries will be searched.

The return code is 0 when the program completes succesfully, and non-zero in case
of errors.
