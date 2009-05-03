/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
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

/** @file pythonutils.cpp
  * @brief Reusable functions for python functionality.
  *
  * The structure of the C++ wrappers around the C Python API is heavily
  * inspired on the design of PyCXX.<br>
  * More information can be found on http://cxx.sourceforge.net
  */

#define FREPPLE_CORE
#include "frepple/utils.h"

namespace frepple
{
namespace utils
{

DECLARE_EXPORT PyObject* PythonLogicException = NULL;
DECLARE_EXPORT PyObject* PythonDataException = NULL;
DECLARE_EXPORT PyObject* PythonRuntimeException = NULL;

const MetaClass* CommandPython::metadata2;

DECLARE_EXPORT PyObject *PythonInterpreter::module = NULL;
DECLARE_EXPORT string PythonInterpreter::encoding;


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
  PythonInterpreter::execute(c.c_str());

  // Log
  if (getVerbose()) logger << "Finished executing python at "
    << Date::now() << " : " << t << endl;
}


void PythonInterpreter::initialize()
{
  // Initialize the interpreter and the frepple module
  Py_InitializeEx(0);  // The arg 0 indicates that the interpreter doesn't
                       // implement its own signal handler
  PyEval_InitThreads();  // Initializes threads and captures global lock
  module = Py_InitModule3("frepple", NULL, "Access to the frePPLe library");
  if (!module)
  {
    PyEval_ReleaseLock();
    throw RuntimeException("Can't initialize Python interpreter");
  }

  // Make the datetime types available
  PyDateTime_IMPORT;

  // Create python exception types
  int nok = 0;
  PythonLogicException = PyErr_NewException("frepple.LogicException", NULL, NULL);
  Py_IncRef(PythonLogicException);
  nok += PyModule_AddObject(module, "LogicException", PythonLogicException);
  PythonDataException = PyErr_NewException("frepple.DataException", NULL, NULL);
  Py_IncRef(PythonDataException);
  nok += PyModule_AddObject(module, "DataException", PythonDataException);
  PythonRuntimeException = PyErr_NewException("frepple.RuntimeException", NULL, NULL);
  Py_IncRef(PythonRuntimeException);
  nok += PyModule_AddObject(module, "RuntimeException", PythonRuntimeException);

  // Add a string constant for the version
  nok += PyModule_AddStringConstant(module, "version", PACKAGE_VERSION);
  
  // Redirect the stderr and stdout streams of Python
  registerGlobalMethod("log", python_log, METH_VARARGS,
    "Prints a string to the frePPLe log file.", false);
  PyRun_SimpleString(
    "import frepple, sys\n"
    "class redirect:\n"
    "\tdef write(self,str):\n"
    "\t\tfrepple.log(str)\n"
    "sys.stdout = redirect()\n"
    "sys.stderr = redirect()"
  );

  // Get the preferred Python locale
  PyObject* localemodule = PyImport_ImportModule("locale");
  if (!localemodule)
    throw RuntimeException("Can't import 'locale' Python module");
  else
  {
    PyObject* moduledict = PyModule_GetDict(localemodule);
    PyObject* func = PyDict_GetItemString(moduledict, "getpreferredencoding");
    if (!func)
      throw RuntimeException("Can't find 'getpreferredencoding' Python function");
    PyObject* retval = PyEval_CallObject(func, NULL);
    if (retval)
    {
      encoding =  PyString_AsString(retval);
      Py_XDECREF(retval);
    }
    Py_XDECREF(localemodule);
  }

  // Release the lock
  PyEval_ReleaseLock();

  // A final check...
  if (nok) throw RuntimeException("Can't initialize Python interpreter");
}


DECLARE_EXPORT void PythonInterpreter::addThread()
{
  // Check whether the thread already has a Python state
  PyThreadState * myThreadState = PyGILState_GetThisThreadState();
  if (myThreadState) return;

  // Create a new state  
  PyThreadState *tcur = PyThreadState_New(PyInterpreterState_Head());
  if (!tcur) throw RuntimeException("Can't create new thread state");

  // Make the new state current
  PyEval_RestoreThread(tcur); 
  PyEval_ReleaseLock();
}


DECLARE_EXPORT void PythonInterpreter::deleteThread()
{
  // Check whether the thread already has a Python state
  PyThreadState * tcur = PyGILState_GetThisThreadState();
  if (!tcur) return;

  // Delete the current Python thread state
  PyEval_RestoreThread(tcur); 
  PyThreadState_Clear(tcur);
  PyThreadState_DeleteCurrent(); // This releases the GIL too!
}


DECLARE_EXPORT void PythonInterpreter::execute(const char* cmd)
{
  // Get the global lock.
  // After this command we are the only thread executing Python code.
  PyThreadState *myThreadState = PyGILState_GetThisThreadState();
  if (!myThreadState) 
    throw RuntimeException("No Python thread state for this thread");
  PyEval_RestoreThread(myThreadState);

  // Execute the command
  PyObject *m = PyImport_AddModule("__main__");
  if (!m)
  {
    // Release the global python lock
    PyEval_ReleaseLock();
    throw RuntimeException("Can't initialize Python interpreter");
  }
  PyObject *d = PyModule_GetDict(m);
  if (!d)
  {
    // Release the global python lock
    PyEval_ReleaseLock();
    throw RuntimeException("Can't initialize Python interpreter");
  }

  // Execute the Python code. Note that during the call the python lock can be
  // temporarily released.
  PyObject *v = PyRun_String(cmd, Py_file_input, d, d);
  if (!v)
  {
    // Print the error message
    PyErr_Print();
    // Release the global python lock
    PyEval_ReleaseLock();
    throw RuntimeException("Error executing python command");
  }
  Py_DECREF(v);
  if (Py_FlushLine()) PyErr_Clear();

  // Release the global python lock
  PyEval_ReleaseLock();
}


DECLARE_EXPORT void PythonInterpreter::registerGlobalMethod(
  const char* name, PyCFunction method, int flags, const char* doc, bool lock
  )
{
  // Define a new method object.
  // We need are leaking the memory allocated for it to assure the data
  // are available at all times to Python.
  string *leakingName = new string(name);
  string *leakingDoc = new string(doc);
  PyMethodDef *newMethod = new PyMethodDef;
  newMethod->ml_name = leakingName->c_str();
  newMethod->ml_meth = method;	
  newMethod->ml_flags = flags;	
  newMethod->ml_doc = leakingDoc->c_str();	

  // Lock the interpreter
  if (lock) PyEval_AcquireLock();

  // Register a new C function in Python
  PyObject* mod = PyString_FromString("frepple");
	if (!mod)
  {
    if (lock) PyEval_ReleaseLock();
    throw RuntimeException("Error registering a new Python method.");
  }
  PyObject* func = PyCFunction_NewEx(newMethod, NULL, mod);
  Py_DECREF(mod);
  if (!func)
  {
    if (lock) PyEval_ReleaseLock();
    throw RuntimeException("Error registering a new Python method.");
  }

  // Add the method to the module dictionary
  PyObject* moduledict = PyModule_GetDict(module);
  if (!moduledict)
  {
    Py_DECREF(func);
    if (lock) PyEval_ReleaseLock();
    throw RuntimeException("Error registering a new Python method.C");
  }
  if (PyDict_SetItemString(moduledict ,leakingName->c_str(), func) < 0)
  {
    Py_DECREF(func);
    if (lock) PyEval_ReleaseLock();
    throw RuntimeException("Error registering a new Python method.");
  }
  Py_DECREF(func);

  // Release the interpeter
  if (lock) PyEval_ReleaseLock();
}


DECLARE_EXPORT void PythonInterpreter::registerGlobalMethod
  (const char* c, PyCFunctionWithKeywords f, int i, const char* d)
{
  registerGlobalMethod(c, reinterpret_cast<PyCFunction>(f), i | METH_KEYWORDS, d);
}


PyObject* PythonInterpreter::python_log(PyObject *self, PyObject *args)
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


const PyTypeObject PythonType::PyTypeObjectTemplate =
  {
    PyObject_HEAD_INIT(NULL)
    0,					/* ob_size */
    "frepple.unspecified",	/* WILL BE UPDATED tp_name */
    0,	/* WILL BE UPDATED tp_basicsize */
    0,					/* tp_itemsize */
    0,  /* CAN BE UPDATED tp_dealloc */
    0,					/* tp_print */
    0,					/* tp_getattr */
    0,					/* tp_setattr */
    0,					/* tp_compare */
    0,	        /* tp_repr */
    0,					/* tp_as_number */
    0,					/* tp_as_sequence */
    0,					/* tp_as_mapping */
    0,					/* tp_hash */
    0,  /* CAN BE UPDATED tp_call */
    0,	/* CAN BE UPDATED tp_str */
    0,	/* CAN BE UPDATED tp_getattro */
    0,	/* CAN BE UPDATED tp_setattro */
    0,					/* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
    "std doc", /* CAN BE UPDATED  tp_doc */
    0,					/* tp_traverse */
    0,					/* tp_clear */
    0,					/* tp_richcompare */
    0,					/* tp_weaklistoffset */
    0,   /* CAN BE UPDATED tp_iter */
    0,	 /* CAN BE UPDATED tp_iternext */
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
    0,	/* CAN BE UPDATED tp_new */
    0,					/* tp_free */
  };


DECLARE_EXPORT PythonObject::PythonObject(const Date& d)
{
  PyDateTime_IMPORT;
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
  obj = PyDateTime_FromDateAndTime(t.tm_year+1900, t.tm_mon+1, t.tm_mday,
      t.tm_hour, t.tm_min, t.tm_sec, 0);
}


DECLARE_EXPORT Date PythonObject::getDate() const
{
  PyDateTime_IMPORT;
  if (PyDateTime_Check(obj))
    return Date(
      PyDateTime_GET_YEAR(obj),
      PyDateTime_GET_MONTH(obj),
      PyDateTime_GET_DAY(obj),
      PyDateTime_DATE_GET_HOUR(obj),
      PyDateTime_DATE_GET_MINUTE(obj),
      PyDateTime_DATE_GET_SECOND(obj)
      );
  else if (PyDate_Check(obj))
    return Date(
      PyDateTime_GET_YEAR(obj),
      PyDateTime_GET_MONTH(obj),
      PyDateTime_GET_DAY(obj)
      );
  else
   throw DataException(
    "Invalid data type. Expecting datetime.date or datetime.datetime"
    );
}


DECLARE_EXPORT PythonObject::PythonObject(Object* p)
{
  if (!p)
  {
    obj = Py_None;
    Py_INCREF(obj);
  }
  else if (p->getType().factoryPythonProxy)
    obj = reinterpret_cast<PyObject*>(p->getType().factoryPythonProxy(p));
  else if (p->getType().category->factoryPythonProxy)
    obj = reinterpret_cast<PyObject*>(p->getType().category->factoryPythonProxy(p));
  else
    throw LogicException("Can't create a Python proxy for " + p->getType().type);
}


DECLARE_EXPORT PythonType::PythonType(size_t base_size, const type_info* tp) 
  : methods(NULL), cppClass(tp)
{
  // Copy a standard info type to start with
  memcpy(&table, &PyTypeObjectTemplate, sizeof(PyTypeObject));
  table.tp_basicsize = base_size;
}


DECLARE_EXPORT void PythonType::addMethod
  (const char* method_name, PyCFunction f, int flags, const char* doc )
{
  // The type is already registered
  if (methods) throw LogicException("Too late to add a method");

  // Populate a method definition struct
  PyMethodDef m;
  m.ml_name = method_name;
  m.ml_meth = f;
  m.ml_flags = flags;
  m.ml_doc = doc;
  methodvector.push_back(m);
}


DECLARE_EXPORT void PythonType::addMethod
  (const char* c, PyCFunctionWithKeywords f, int i, const char* d)
{
  addMethod(c, reinterpret_cast<PyCFunction>(f), i | METH_KEYWORDS, d);
}


DECLARE_EXPORT int PythonType::typeReady(PyObject* m)
{
  // Fill the method table
  if (!methodvector.empty())
  {
    addMethod(NULL, static_cast<PyCFunction>(NULL), 0, NULL);  // Terminator
    methods = new PyMethodDef[methodvector.size()];
    int j = 0;
    for(vector<PyMethodDef>::iterator i = methodvector.begin(); i != methodvector.end(); i++ )
      methods[j++] = *i;
    table.tp_methods = methods;
  }

  // Register the new type in the module
  if (PyType_Ready(&table) < 0)
    throw RuntimeException("Can't register python type " + name);
  Py_INCREF(&table);
  // Note: +8 is to skip the "frepple." characters in the name
  return PyModule_AddObject(m, const_cast<char*>(name.c_str()) + 8, reinterpret_cast<PyObject*>(&table));
}


DECLARE_EXPORT void PythonType::evalException()
{
  // Rethrowing the exception to catch its type better
  try {throw;}
  catch (DataException e)
    { PyErr_SetString(PythonDataException, e.what()); }
  catch (LogicException e)
    { PyErr_SetString(PythonLogicException, e.what()); }
  catch (RuntimeException e)
    { PyErr_SetString(PythonRuntimeException, e.what()); }
  catch (exception e)
    { PyErr_SetString(PyExc_Exception, e.what()); }
  catch (...)
    { PyErr_SetString(PyExc_Exception, "Unidentified exception"); }
}


extern "C" DECLARE_EXPORT PyObject* getattro_handler(PyObject *self, PyObject *name)
{
  try
  {
    if (!PyString_Check(name))
		{
      PyErr_Format(PyExc_TypeError,
        "attribute name must be string, not '%s'",
        name->ob_type->tp_name);
			return NULL;
		}
    PyObject* result = static_cast<PythonExtensionBase*>(self)->getattro(Attribute(PyString_AsString(name)));
    // Exit 1: Normal
    if (result) return result;
    // Exit 2: Exception occurred
    if (PyErr_Occurred()) return NULL;
    // Exit 3: No error occurred but the attribute was not found.
    // Use the standard generic function to pick up  standard attributes
    // (such as __class__, __doc__, ...)
    // Note that this function also picks up attributes from base classes, but
    // we can't rely on that: any C++ exceptions are lost along the way...
    return PyObject_GenericGetAttr(self,name);
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}


extern "C" DECLARE_EXPORT int setattro_handler(PyObject *self, PyObject *name, PyObject *value)
{
  try
  {
    // Pick up the field name
    if (!PyString_Check(name))
		{
      PyErr_Format(PyExc_TypeError,
        "attribute name must be string, not '%s'",
        name->ob_type->tp_name);
			return -1;
		}
    PythonObject field(value);

    // Call the object to update the attribute
    int result = static_cast<PythonExtensionBase*>(self)->setattro(Attribute(PyString_AsString(name)), field);

    // Process result
    if (!result) return 0;
    PyErr_Format(PyExc_AttributeError,
      "attribute '%s' on '%s' can't be updated",
      PyString_AsString(name), self->ob_type->tp_name);
		return -1;
  }
  catch (...)
  {
    PythonType::evalException();
    return -1;
  }
}


extern "C" DECLARE_EXPORT int compare_handler(PyObject *self, PyObject *other)
{
  try
  {
    return static_cast<PythonExtensionBase*>(self)->compare(other);
  }
  catch (...)
  {
    PythonType::evalException();
    return -1;
  }
}


extern "C" DECLARE_EXPORT PyObject* iternext_handler(PyObject *self)
{
  try
  {
    return static_cast<PythonExtensionBase*>(self)->iternext();
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}


extern "C" DECLARE_EXPORT PyObject* call_handler(PyObject* self, PyObject* args, PyObject* kwds)
{
  try 
  { 
    return static_cast<PythonExtensionBase*>(self)->call(args, kwds); 
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}


extern "C" DECLARE_EXPORT PyObject* str_handler(PyObject* self)
{
  try
  {
    return static_cast<PythonExtensionBase*>(self)->str();
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}

} // end namespace
} // end namespace
