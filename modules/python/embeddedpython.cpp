/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Lesser General Public License as published   *
 * by the Free Software Foundation; either version 2.1 of the License, or  *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser *
 * General Public License for more details.                                *
 *                                                                         *
 * You should have received a copy of the GNU Lesser General Public        *
 * License along with this library; if not, write to the Free Software     *
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/

#include "embeddedpython.h"

namespace module_python
{

const MetaClass CommandPython::metadata;
const MetaClass CommandPython::metadata2;
PyThreadState *CommandPython::mainThreadState = NULL;
PyObject* CommandPython::PythonLogicException = NULL;
PyObject* CommandPython::PythonDataException = NULL;
PyObject* CommandPython::PythonRuntimeException = NULL;


// Define the methods to be exposed into Python
PyMethodDef CommandPython::PythonAPI[] =
  {
    {"log", CommandPython::python_log, METH_VARARGS,
     "Prints a string to the frepple log file."
    },
    {"readXMLdata", CommandPython::python_readXMLdata, METH_VARARGS,
     "Processes an XML string passed as argument."},
    {"createItem", CommandPython::python_createItem, METH_VARARGS,
     "Uses the C++ API to create an item."},
    {"readXMLfile", CommandPython::python_readXMLfile, METH_VARARGS,
     "Read an XML-file."},
    {"saveXMLfile", CommandPython::python_saveXMLfile, METH_VARARGS,
     "Save the model to an XML-file."},
    {"saveXMLstring", CommandPython::python_saveXMLstring, METH_NOARGS,
     "Returns the model as an XML-formatted string."},
    {NULL, NULL, 0, NULL}
  };


const PyTypeObject CommandPython::TemplateInfoType =
  {
    PyObject_HEAD_INIT(NULL)
    0,					/* ob_size */
    "frepple.generic",	/* WILL BE UPDATED tp_name */
    0,	/* WILL BE UPDATED tp_basicsize */
    0,					/* tp_itemsize */
    0,  /* WILL BE UPDATED tp_dealloc */
    0,					/* tp_print */
    0,					/* tp_getattr */
    0,					/* tp_setattr */
    0,					/* tp_compare */
    0,	        /* tp_repr */
    0,					/* tp_as_number */
    0,					/* tp_as_sequence */
    0,					/* tp_as_mapping */
    0,					/* tp_hash */
    0,          /* tp_call */
    0,					/* tp_str */
    0,		      /* tp_getattro */
    0,					/* tp_setattro */
    0,					/* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
    "std doc", /* WILL BE UPDATED  tp_doc */
    0,					/* tp_traverse */
    0,					/* tp_clear */
    0,					/* tp_richcompare */
    0,					/* tp_weaklistoffset */
    PyObject_SelfIter,  /* tp_iter */
    0,	/* WILL BE UPDATED tp_iternext */
    0,				  /* tp_methods */
    0,					/* tp_members */
    0,					/* tp_getset */
    0,					/* tp_base */
    0,					/* tp_dict */
    0,					/* tp_descr_get */
    0,					/* tp_descr_set */
    0,					/* tp_dictoffset */
    0,          /* tp_init */
    0,          /* tp_alloc */
    0,	/* WILL BE UPDATED tp_new */
    0,					/* tp_free */
  };


MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  static const char* name = "python";
  if (init)
  {
    logger << "Warning: Initializing module python more than once." << endl;
    return name;
  }
  init = true;

  // Initialize the metadata.
  CommandPython::metadata.registerClass(
    "COMMAND",
    "COMMAND_PYTHON",
    Object::createDefault<CommandPython>);

  // Register python also as a processing instruction.
  CommandPython::metadata2.registerClass(
    "INSTRUCTION",
    "PYTHON",
    Object::createDefault<CommandPython>);

  // Initialize the interpreter
  CommandPython::initialize();

  // Return the name of the module
  return name;
}


void CommandPython::initialize()
{
  // Initialize the interpreter and the frepple module
  Py_InitializeEx(0);  // The arg 0 indicates that the interpreter doesn't
                       // implement its own signal handler
  PyEval_InitThreads();  // Initializes threads and captures global lock
  PyObject* m = Py_InitModule3
      ("frepple", CommandPython::PythonAPI, "Acces to the Frepple library");
  if (!m)
  {
    PyEval_ReleaseLock();
    throw frepple::RuntimeException("Can't initialize Python interpreter");
  }

  // Make the datetime types available
  PyDateTime_IMPORT;

  // Create python exception types
  int nok = 0;
  PythonLogicException = PyErr_NewException("frepple.LogicException", NULL, NULL);
  Py_IncRef(PythonLogicException);
  nok += PyModule_AddObject(m, "LogicException", PythonLogicException);
  PythonDataException = PyErr_NewException("frepple.DataException", NULL, NULL);
  Py_IncRef(PythonDataException);
  nok += PyModule_AddObject(m, "DataException", PythonDataException);
  PythonRuntimeException = PyErr_NewException("frepple.RuntimeException", NULL, NULL);
  Py_IncRef(PythonRuntimeException);
  nok += PyModule_AddObject(m, "RuntimeException", PythonRuntimeException);

  // Add a string constant for the version
  nok += PyModule_AddStringConstant(m, "version", PACKAGE_VERSION);

  // Capture the main trhead state, for use during threaded execution
  mainThreadState = PyThreadState_Get();

  // Register our new types
  define_type<PythonProblem>(m, "problem", "frepple problem");
  define_type<PythonFlowPlan>(m, "flowplan", "frepple flowplan");
  define_type<PythonLoadPlan>(m, "loadplan", "frepple loadplan");
  define_type<PythonOperationPlan>(m, "operationplan", "frepple operationplan");
  define_type<PythonDemand>(m, "demand", "frepple demand");
  define_type<PythonDemandPegging>(m, "pegging", "frepple demand pegging");
  define_type<PythonDemandDelivery>(m, "delivery", "frepple demand delivery");
  define_type<PythonBuffer>(m, "buffer", "frepple buffer");
  define_type<PythonResource>(m, "resource", "frepple resource");

  // Redirect the stderr and stdout streams of Python
  PyRun_SimpleString(
    "import frepple, sys\n"
    "class redirect:\n"
    "\tdef write(self,str):\n"
    "\t\tfrepple.log(str)\n"
    "sys.stdout = redirect()\n"
    "sys.stderr = redirect()\n"
  );

  // Search and execute the initialization file '$FREPPLE_HOME/init.py'
  string init = Environment::getHomeDirectory() + "init.py";
  struct stat stat_p;
  if (!nok && !stat(init.c_str(), &stat_p))
  {
    // Initialization file exists
    PyObject *m = PyImport_AddModule("__main__");
    if (!m)
    {
      PyEval_ReleaseLock();
      throw frepple::RuntimeException("Can't execute Python script 'init.py'");
    }
    PyObject *d = PyModule_GetDict(m);
    if (!d)
    {
      PyEval_ReleaseLock();
      throw frepple::RuntimeException("Can't execute Python script 'init.py'");
    }
    init = "execfile('" + init + "')\n";
    PyObject *v = PyRun_String(init.c_str(), Py_file_input, d, d);
    if (!v)
    {
      // Print the error message
      PyErr_Print();
      // Release the lock
      PyEval_ReleaseLock();
      throw frepple::RuntimeException("Error executing Python script 'init.py'");
    }
    Py_DECREF(v);
    if (Py_FlushLine()) PyErr_Clear();
  }

  // Release the lock
  PyEval_ReleaseLock();

  // A final check...
  if (nok || !mainThreadState)
    throw frepple::RuntimeException("Can't initialize Python interpreter");
}


void CommandPython::execute()
{
  // Log
  if (getVerbose())
  {
    logger << "Start executing python ";
    if (!cmd.empty()) logger << "command";
    if (!filename.empty()) logger << "file";
    logger << " at " << Date::now() << endl;
  }
  Timer t;

  // Replace environment variables in the filename and command line.
  Environment::resolveEnvironment(filename);
  Environment::resolveEnvironment(cmd);

  // Evaluate data fields
  string c;
  if (!cmd.empty())
    // A command to be executed.
    c = cmd + "\n";  // Make sure last line is ended properly
  else if (!filename.empty())
  {
    // A file to be executed.
    // We build an equivalent python command rather than using the
    // PyRun_File function. On windows different versions of the
    // VC compiler have a different structure for FILE, thus making it
    // impossible to use a lib compiled in python version x when compiling
    // under version y.  Quite ugly... :-( :-( :-(
    c = filename;
    for (string::size_type pos = c.find_first_of("'", 0);   
        pos < string::npos;
        pos = c.find_first_of("'", pos))   
    {
      c.replace(pos,1,"\\'",2); // Replacing ' with \'
      pos+=2;
    }
    c = "execfile(u'" + c + "')\n";
  }
  else throw DataException("Python command without statement or filename");

  // Pass to the interpreter.
  executePython(c.c_str());

  // Log
  if (getVerbose()) logger << "Finished executing python at "
    << Date::now() << " : " << t << endl;
}


void CommandPython::executePython(const char* cmd)
{
  // Get the global lock.
  // After this command we are the only thread executing Python code.
  PyEval_AcquireLock();

  // Initialize this thread for execution
  PyInterpreterState *mainInterpreterState = mainThreadState->interp;
  PyThreadState *myThreadState = PyThreadState_New(mainInterpreterState);
  PyThreadState *prevThreadState = PyThreadState_Swap(myThreadState);

  // Execute the command
  PyObject *m = PyImport_AddModule("__main__");
  if (!m)
  {
    // Clean up the thread and release the global python lock
    myThreadState = PyThreadState_Swap(prevThreadState);
    PyThreadState_Clear(myThreadState);
    PyEval_ReleaseLock();
    PyThreadState_Delete(myThreadState);
    throw frepple::RuntimeException("Can't initialize Python interpreter");
  }
  PyObject *d = PyModule_GetDict(m);
  if (!d)
  {
    // Clean up the thread and release the global python lock
    myThreadState = PyThreadState_Swap(prevThreadState);
    PyThreadState_Clear(myThreadState);
    PyEval_ReleaseLock();
    PyThreadState_Delete(myThreadState);
    throw frepple::RuntimeException("Can't initialize Python interpreter");
  }

  // Execute the Python code. Note that during the call the python lock can be
  // temporarily released.
  PyObject *v = PyRun_String(cmd, Py_file_input, d, d);
  if (!v)
  {
    // Print the error message
    PyErr_Print();
    // Clean up the thread and release the global python lock
    myThreadState = PyThreadState_Swap(prevThreadState);
    PyThreadState_Clear(myThreadState);
    PyEval_ReleaseLock();
    PyThreadState_Delete(myThreadState);
    throw frepple::RuntimeException("Error executing python command");
  }
  Py_DECREF(v);
  if (Py_FlushLine()) PyErr_Clear();

  // Clean up the thread and release the global python lock
  myThreadState = PyThreadState_Swap(prevThreadState);
  PyThreadState_Clear(myThreadState);
  PyEval_ReleaseLock();
  PyThreadState_Delete(myThreadState);
}


void CommandPython::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_cmdline))
  {
    // No replacement of environment variables here
    filename.clear();
    pElement >> cmd;
  }
  else if (pElement.isA(Tags::tag_filename))
  {
    cmd.clear();
    pElement >> filename;
  }
  else
    Command::endElement(pIn, pElement);
}


PyObject* CommandPython::python_log(PyObject *self, PyObject *args)
{
  // Pick up arguments
  char *data;
  int ok = PyArg_ParseTuple(args, "s", &data);
  if (!ok) return NULL;

  // Print and flush the output stream
  logger << data;
  logger.flush();

  // Return code
  return Py_BuildValue("");  // Safer than using Py_None, which is not
                             // portable across compilers
}


PyObject* CommandPython::python_readXMLdata(PyObject *self, PyObject *args)
{
  // Pick up arguments
  char *data;
  int i1(1), i2(0);
  int ok = PyArg_ParseTuple(args, "s|ii", &data, &i1, &i2);
  if (!ok) return NULL;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try { FreppleReadXMLData(data,i1!=0,i2!=0); }
  catch (LogicException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonLogicException, e.what()); return NULL;}
  catch (DataException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonDataException, e.what()); return NULL;}
  catch (frepple::RuntimeException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (exception e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (...)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, "unknown type"); return NULL;}
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");  // Safer than using Py_None, which is not
                             // portable across compilers
}


PyObject* CommandPython::python_createItem(PyObject *self, PyObject *args)
{
  // Pick up the arguments
  char *itemname;
  char *operationname;
  int ok = PyArg_ParseTuple(args, "ss", &itemname, &operationname);
  if (!ok) return NULL;  // Wrong arguments

  // Create the items
  Item* it = Item::add(itemname, BufferDefault::metadata);
  Operation* op = Operation::add(operationname, OperationFixedTime::metadata);
  if (it && op) it->setDelivery(op);

  // Return code for Python
  return Py_BuildValue("i", it && op);
}


PyObject* CommandPython::python_readXMLfile(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *data;
  int i1(1), i2(0);
  int ok = PyArg_ParseTuple(args, "s|ii", &data, &i1, &i2);
  if (!ok) return NULL;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try { FreppleReadXMLFile(data,i1!=0,i2!=0); }
  catch (LogicException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonLogicException, e.what()); return NULL;}
  catch (DataException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonDataException, e.what()); return NULL;}
  catch (frepple::RuntimeException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (exception e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (...)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, "unknown type"); return NULL;}
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


PyObject* CommandPython::python_saveXMLfile(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *data;
  int ok = PyArg_ParseTuple(args, "s", &data);
  if (!ok) return NULL;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try { FreppleSaveFile(data); }
  catch (LogicException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonLogicException, e.what()); return NULL;}
  catch (DataException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonDataException, e.what()); return NULL;}
  catch (frepple::RuntimeException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (exception e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (...)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, "unknown type"); return NULL;}
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


PyObject *CommandPython::python_saveXMLstring(PyObject* self, PyObject* args)
{
  // Execute and catch exceptions
  string result;
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try { result = FreppleSaveString(); }
  catch (LogicException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonLogicException, e.what()); return NULL;}
  catch (DataException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonDataException, e.what()); return NULL;}
  catch (frepple::RuntimeException e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (exception e)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, e.what()); return NULL;}
  catch (...)
  {Py_BLOCK_THREADS; PyErr_SetString(PythonRuntimeException, "unknown type"); return NULL;}
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("s",result.c_str());
}


PyObject* PythonDateTime(const Date& d)
{
  // The standard library function localtime() is not re-entrant: the same
  // static structure is used for all calls. In a multi-threaded environment
  // the function is not to be used.
  // The POSIX standard defines a re-entrant version of the function:
  // localtime_r.
  // Visual C++ 6.0 and Borland 5.5 are missing it, but provide a thread-safe
  // variant without changing the function semantics.
  time_t ticks = d.getTicks();
#ifdef HAVE_LOCALTIME_R
  struct tm t;
  localtime_r(&ticks, &t);
#else
  struct tm t = *localtime(&ticks);
#endif
  return PyDateTime_FromDateAndTime(t.tm_year+1900, t.tm_mon+1, t.tm_mday,
      t.tm_hour, t.tm_min, t.tm_sec, 0);
}


} // End namespace
