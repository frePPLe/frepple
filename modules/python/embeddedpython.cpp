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
Mutex CommandPython::interpreterbusy;
PyObject* CommandPython::PythonLogicException;
PyObject* CommandPython::PythonDataException;
PyObject* CommandPython::PythonRuntimeException;


// Define the methods to be exposed into Python
PyMethodDef CommandPython::PythonAPI[] = 
{
  {"readXMLdata", CommandPython::python_readXMLdata, METH_VARARGS, 
     "Processes an XML string passed as argument."},
  {"createItem", CommandPython::python_createItem, METH_VARARGS, 
     "Uses the C++ API to create an item."},
  {"readXMLfile", CommandPython::python_readXMLfile, METH_VARARGS, 
     "Read an XML-file."},
  {"saveXMLfile", CommandPython::python_saveXMLfile, METH_VARARGS, 
     "Save the model to an XML-file."},
  {NULL, NULL, 0, NULL}
};


MODULE_EXPORT void initialize(const CommandLoadLibrary::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  if (init)
  {
    clog << "Warning: Initializing module lp_solver more than one." << endl;
    return;
  }
  init = true;

  // Initialize the metadata.
  CommandPython::metadata.registerClass(
    "COMMAND", 
    "COMMAND_PYTHON", 
    Object::createDefault<CommandPython>);

  // Initialize the interpreter
  CommandPython::initialize();
}


void CommandPython::initialize()
{
  // Initialize the interpreter and the frepple module
  Py_InitializeEx(0);  // The arg 0 indicates that the interpreter doesn't 
                       // implement its own signal handler
  PyEval_InitThreads();
  PyObject* m = Py_InitModule3
    ("frepple", CommandPython::PythonAPI, "Acces to the Frepple library");
  if (!m)
    throw frepple::RuntimeException("Can't initialize Python interpreter");

  // Create python exception types
  PythonLogicException = PyErr_NewException("frepple.LogicException", NULL, NULL);
  Py_IncRef(PythonLogicException);
  PyModule_AddObject(m, "LogicException", PythonLogicException);
  PythonDataException = PyErr_NewException("frepple.DataException", NULL, NULL);
  Py_IncRef(PythonDataException);
  PyModule_AddObject(m, "DataException", PythonDataException);
  PythonRuntimeException = PyErr_NewException("frepple.RuntimeException", NULL, NULL);
  Py_IncRef(PythonRuntimeException);
  PyModule_AddObject(m, "RuntimeException", PythonRuntimeException);

  // Add a string constant for the version
  PyModule_AddStringConstant(m, "version", PACKAGE_VERSION);
  PyEval_ReleaseLock();
}


void CommandPython::execute()
{
  // Log
  if (getVerbose())
  {
    clog << "Start executing python ";
    if (!cmd.empty()) clog << "command";
    if (!filename.empty()) clog << "file";
    clog << " at " << Date::now() << endl;
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
    // impossible to use a lib compiled in version x when compiling under
    // version y.  Quite ugly... :-( :-( :-(
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
  else  throw DataException("Python command without statement or filename");

  // Execute the command
  {
  ScopeMutexLock l(interpreterbusy);
  PyEval_AcquireLock();
  PyObject *m = PyImport_AddModule("__main__");
  if (!m) 
  {
    PyEval_ReleaseLock();
    throw frepple::RuntimeException("Can't initialize Python interpreter");
  }
  PyObject *d = PyModule_GetDict(m);
  if (!d) 
  {
    PyEval_ReleaseLock();
    throw frepple::RuntimeException("Can't initialize Python interpreter");
  }

  // Execute the Python code
  PyObject *v = PyRun_String(c.c_str(), Py_file_input, d, d);
  if (!v) 
  {
	  PyErr_Print();
    PyEval_ReleaseLock();
    throw frepple::RuntimeException("Error executing python command"); // Leak python thread xxx
  }
  Py_DECREF(v);
  if (Py_FlushLine()) PyErr_Clear();
  PyEval_ReleaseLock();
  }

  // Log
  if (getVerbose()) clog << "Finished executing python at " 
    << Date::now() << " : " << t << endl;
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
    // Replace environment variables with their value.
    pElement.resolveEnvironment();
    cmd.clear();
    pElement >> filename;
  }
  else
  {
    // Replace environment variables with their value.
    pElement.resolveEnvironment();
    Command::endElement(pIn, pElement);
  }
}


PyObject* CommandPython::python_readXMLdata(PyObject *self, PyObject *args) 
{    
  // Pick up arguments
  char *data;
  int i1(1), i2(0);
  int ok = PyArg_ParseTuple(args, "s|ii", &data, &i1, &i2);
  if (!ok) return NULL;

  // Execute and catch exceptions
  bool okay = true;
  Py_BEGIN_ALLOW_THREADS
  try { FreppleReadXMLData(data,i1!=0,i2!=0); }
  catch (LogicException e) {PyErr_SetString(PythonLogicException, e.what()); okay=false;}
  catch (DataException e) {PyErr_SetString(PythonDataException, e.what()); okay=false;}
  catch (frepple::RuntimeException e) {PyErr_SetString(PythonRuntimeException, e.what()); okay=false;}
  catch (exception e) {PyErr_SetString(PythonRuntimeException, e.what()); okay=false;}
  catch (...) {PyErr_SetString(PythonRuntimeException, "unknown type"); okay=false;}
  Py_END_ALLOW_THREADS
  if (!okay) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
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
  bool okay = true;
  Py_BEGIN_ALLOW_THREADS
  try { FreppleReadXMLFile(data,i1!=0,i2!=0); }
  catch (LogicException e) {PyErr_SetString(PythonLogicException, e.what()); okay=false;}
  catch (DataException e) {PyErr_SetString(PythonDataException, e.what()); okay=false;}
  catch (frepple::RuntimeException e) {PyErr_SetString(PythonRuntimeException, e.what()); okay=false;}
  catch (exception e) {PyErr_SetString(PythonRuntimeException, e.what()); okay=false;}
  catch (...) {PyErr_SetString(PythonRuntimeException, "unknown type"); okay=false;}
  Py_END_ALLOW_THREADS
  if (!okay) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}


PyObject* CommandPython::python_saveXMLfile(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *data;
  int ok = PyArg_ParseTuple(args, "s", &data);
  if (!ok) return NULL;

  // Execute and catch exceptions
  bool okay = true;
  Py_BEGIN_ALLOW_THREADS
  try { FreppleSaveFile(data); }
  catch (LogicException e) {PyErr_SetString(PythonLogicException, e.what()); okay=false;}
  catch (DataException e) {PyErr_SetString(PythonDataException, e.what()); okay=false;}
  catch (frepple::RuntimeException e) {PyErr_SetString(PythonRuntimeException, e.what()); okay=false;}
  catch (exception e) {PyErr_SetString(PythonRuntimeException, e.what()); okay=false;}
  catch (...) {PyErr_SetString(PythonRuntimeException, "unknown type"); okay=false;}
  Py_END_ALLOW_THREADS
  if (!okay) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}


} // End namespace
