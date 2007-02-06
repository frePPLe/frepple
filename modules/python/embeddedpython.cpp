/***************************************************************************
  file : $URL: https://frepple.svn.sourceforge.net/svnroot/frepple/trunk/modules/lp_solver/lpsolver.cpp $
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
     "Prints a string to the frepple log file."},
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


MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  static const char* name = "python";
  if (init)
  {
    cout << "Warning: Initializing module python more than once." << endl;
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

  // Register our new type: iterator
  if (PyType_Ready(&PythonIterator::InfoType) < 0) 
    throw frepple::RuntimeException("Can't register frepple python extensions");
  Py_INCREF(&PythonIterator::InfoType);
  PyModule_AddObject(m, "iterator", reinterpret_cast<PyObject*>(&PythonIterator::InfoType));
  
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
    cout << "Start executing python ";
    if (!cmd.empty()) cout << "command";
    if (!filename.empty()) cout << "file";
    cout << " at " << Date::now() << endl;
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
    c = "execfile('" + c + "')\n";
  }
  else throw DataException("Python command without statement or filename");

  // Pass to the interpreter. 
  executePython(c.c_str());

  // Log
  if (getVerbose()) cout << "Finished executing python at " 
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
  PyThreadState_Swap(myThreadState);

  // Execute the command
  PyObject *m = PyImport_AddModule("__main__");
  if (!m) 
  {
    // Clean up the thread
    PyThreadState_Swap(NULL);
    PyThreadState_Clear(myThreadState);
    PyThreadState_Delete(myThreadState);
    // Release the lock
    PyEval_ReleaseLock();
    throw frepple::RuntimeException("Can't initialize Python interpreter");
  }
  PyObject *d = PyModule_GetDict(m);
  if (!d) 
  {
    // Clean up the thread
    PyThreadState_Swap(NULL);
    PyThreadState_Clear(myThreadState);
    PyThreadState_Delete(myThreadState);
    // Release the lock
    PyEval_ReleaseLock();
    throw frepple::RuntimeException("Can't initialize Python interpreter");
  }

  // Execute the Python code. Note that during the call the python lock can be
  // temporarily released.
  PyObject *v = PyRun_String(cmd, Py_file_input, d, d);
  if (!v) 
  {
    // Print the error message
	  PyErr_Print();
    // Clean up the thread
    PyThreadState_Swap(NULL);
    PyThreadState_Clear(myThreadState);
    PyThreadState_Delete(myThreadState);
    // Release the lock
    PyEval_ReleaseLock();
    throw frepple::RuntimeException("Error executing python command"); 
  }
  Py_DECREF(v);
  if (Py_FlushLine()) PyErr_Clear();
  // Clean up the thread
  PyThreadState_Swap(NULL);
  PyThreadState_Clear(myThreadState);
  PyThreadState_Delete(myThreadState);

  // Release the lock. No more python calls now.
  PyEval_ReleaseLock();
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
  
  // Print 
  cout << data;
  
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
  Item *it = dynamic_cast<Item*>(Object::createString<ItemDefault>(itemname));
  Item::add(it);   // @todo need a cleaner and safer API for this
  Operation* op = dynamic_cast<Operation*>(Object::createString<OperationFixedTime>(operationname));
  Operation::add(op);
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


extern "C" PyObject* PythonIterator::repr(PythonIterator* obj)
{
    return PyString_FromFormat("Frepple problem iterator");
}


extern "C" PyObject* PythonIterator::create(PyTypeObject* type, PyObject *args, PyObject *kwargs)
{
  // Allocate memory
  PythonIterator* obj = PyObject_New(PythonIterator, &PythonIterator::InfoType);

  // Initialize the problem iterator
  obj->iter.reset();
  obj->iter = Problem::begin();

  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonIterator::next(PythonIterator* obj) 
{
  if (obj->iter != Problem::end())
  {
    PyObject* result = PyTuple_New(3);
    PyTuple_SET_ITEM(result, 0, PyString_FromFormat("%s", obj->iter->getDescription().c_str()));
    PyTuple_SET_ITEM(result, 1, PyString_FromFormat("%s", obj->iter->getType().type.c_str()));
    PyTuple_SET_ITEM(result, 2, PyString_FromFormat("%s", string(obj->iter->getDateRange()).c_str()));
    ++(obj->iter);
    return result;
  }
  else 
    // Reached the end of the iteration
    return NULL;
}


PyTypeObject PythonIterator::InfoType = 
{
	PyObject_HEAD_INIT(NULL)
	0,					/* ob_size */
	"frepple.iterator",	/* tp_name */
	sizeof(PythonIterator),	/* tp_basicsize */
	0,					/* tp_itemsize */
	0,          /* tp_dealloc */
	0,					/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_compare */
	reinterpret_cast<reprfunc>(PythonIterator::repr),	/* tp_repr */
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
	"Iterate over frepple objects", /* tp_doc */
	0,					/* tp_traverse */
	0,					/* tp_clear */
	0,					/* tp_richcompare */
	0,					/* tp_weaklistoffset */
	PyObject_SelfIter,  /* tp_iter */
	reinterpret_cast<iternextfunc>(PythonIterator::next),	/* tp_iternext */
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
	PythonIterator::create,	/* tp_new */
	0,					/* tp_free */
};

} // End namespace
