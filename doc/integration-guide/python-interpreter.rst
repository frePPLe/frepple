==================
Python interpreter
==================

FrePPle embeds an interpreter for the Python language. The full capabilities
of this scripting language are accessible from frePPLe, and Python also has
access to the frePPLe objects in memory. Python is thus a very powerful way
to interact with frePPLe.

Python code can be executed in two ways:

* A XML processing instruction in XML data files.

  .. code-block:: XML

     <?xml version="1.0" encoding="UTF-8" ?>
     <plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance&quot;>
     ...
     <?python
     Your python code goes here.
     ?>
     ...
     </plan>

* Python code in a file init.py, located in one of the frePPLe directories,
  is executed automatically when frePPLe starts. This provides a clean
  mechanism to define global Python functions and classes your application
  needs.

The interpreter is multi-threaded. Multiple python scripts can run in parallel.
However, Python internally executes only one thread at a time and the
interpreter switches between the active threads. A single, global interpreter
instance is used. A global Python variable or function is thus visible across
multiple invocations of the Python interpreter.

The following Python functions are defined:

* `loadmodule`_ dynamically loads an extension module.

* `readXMLfile`_ processes a XML-file from the local file system.

* `readXMLdata`_ processes a XML-formatted string.

* `erase`_ removes part of the model or plan from memory.

* `saveXMLfile`_ saves the model to an XML-formatted file.

* `saveplan`_ saves the most important plan information to a file.

* `printsize`_ prints information about the memory size of the model.

loadmodule
----------

This command dynamically loads an extension module.

It takes as arguments:

* | The name of the shared library file to be loaded.
  | The module file should be found in the directory list defined with the
    environment variable PATH (Windows) or LD_LIBRARY_PATH (Linux).

* | Parameter and value pairs
  | Initialization and configuration values that are passed to the module’s
    initialization routine.
  | A parameter consists of a PARAMETER and VALUE pair.

Example code:

::

   <?python
   frepple.loadmodule("your_module.so",
     parameter1="string value",
     parameter2=100,
     parameter3=True)
   ?>

readXMLfile
-----------

This command reads and processes a XML-file from the local file system.

It takes as arguments:

* | filename
  | Name of the data file to be loaded.

* | validate boolean
  | A boolean flag that activates validation of the XML data against the
    XML-schema.
  | The default value is true, for security reasons.
  | When parsing large files with a trusted structure setting this field
    to false will speed up the import.

* | validate_only
  | If this optional boolean argument is equal to true the input data are
    only validated against the XML-schema. The data are not processed in
    the core application.

* | callback
  | An optional callback Python function that is called when an object
    has been read from the input data.
  | The object is passed as argument.

Example code:

::

   <?python
   frepple.readXMLfile("input.xml",True,True)
   ?>

readXMLdata
-----------

This command processes a XML-formatted data string.

It takes as arguments:

* | data
  | XML-formatted data string to be processed.

* | validate boolean
  | A boolean flag that activates validation of the XML data against the
    XML-schema.
  | The default value is true, for security reasons.
  | When parsing large files with a trusted structure setting this field
    to false will speed up the import.

* | validate_only
  | If this optional boolean argument is equal to true the input data are
    only validated against the XML-schema. The data are not processed in
    the core application.

* | callback
  | An optional callback Python function that is called when an object
    has been read from the input data.
  | The object is passed as argument.

Example code:

::

   <?python
   frepple.readXMLdata('''
     <plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
     <locations>
     <location name="Location 1" action="R"/>
     </locations>
     </plan>''',True,True)
   ?>

erase
-----

Use this command to erase the plan or the entire model from memory.

It takes as arguments:

* | mode
  | When this boolean argument is set to true the complete model is erased.
    You will again have a completely empty model.
  | When the argument is false only the plan information is erased, ie only
    the operationplans with their load- and flowplans are removed (except the ones that are locked).

Example code:

::

   <?python
   frepple.erase(False)
   ?>

saveXMLfile
-----------

This commands saves the model into an XML file.

It takes as arguments:

* | filename
  | Name of the output file.

* | content
  | Controls the level of detail in the output. Possible values are:

  * STANDARD: plan information is sufficient for restoring the model from
    the output file. This is the default mode.

  * PLAN: adds more detail about its plan with each entity. A buffer will
    report on its flowplans, a resource reports on its loadplans, and a
    demand on its delivery operationplans.

  * PLANDETAIL: goes even further and includes full pegging information
    the output. A buffer will report how the material is supplied and which
    demands it satisfies, a resource will report on how the capacity used
    links to the demands, and a demand shows the complete supply path used
    to meet it.

* | headerstart
  | The first line of the XML output.
  | The default value is: <?xml version="1.0" encoding="UTF-8"?>

* | headeratts
  | Predefined attributes of the XML root-element.
  | The default value is: xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"

Example code:

::

   <?python
   frepple.saveXMLfile("output.xml")
   frepple.saveXMLfile("detailedoutput.xml","PLANDETAIL")
   ?>

saveplan
--------

This command saves the most important plan information to a file.

It is used for the unit tests, but its’ usefulness in a real-life implementation is probably limited.

The only argument it takes is the name of the output file.

Example code:

::

   <?python
   frepple.saveplan("output.xml")
   ?>

printsize
---------

This command prints information about the memory size of the model and other sytem parameters.

Example code:

::

   <?python
   frepple.printsize()
   ?>
