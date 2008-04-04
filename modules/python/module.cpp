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

#include "embeddedpython.h"

namespace module_python
{

const MetaClass CommandPython::metadata;
const MetaClass CommandPython::metadata2;
PyThreadState *CommandPython::mainThreadState = NULL;

PyObject* PythonLogicException = NULL;
PyObject* PythonDataException = NULL;
PyObject* PythonRuntimeException = NULL;


// Define the methods to be exposed into Python
PyMethodDef CommandPython::PythonAPI[] =
  {
    {"log", CommandPython::python_log, METH_VARARGS,
     "Prints a string to the frePPLe log file."
    },
    {"readXMLdata", CommandPython::python_readXMLdata, METH_VARARGS,
     "Processes an XML string passed as argument."},
    {"readXMLfile", CommandPython::python_readXMLfile, METH_VARARGS,
     "Read an XML-file."},
    {"saveXMLfile", CommandPython::python_saveXMLfile, METH_VARARGS,
     "Save the model to an XML-file."},
    {"saveXMLstring", CommandPython::python_saveXMLstring, METH_NOARGS,
     "Returns the model as an XML-formatted string."},
    {"buffers", PythonBufferIterator::create, METH_NOARGS,
     "Returns an iterator over the buffers."},
    {"locations", PythonLocationIterator::create, METH_NOARGS,
     "Returns an iterator over the locations."},
    {"customers", PythonCustomerIterator::create, METH_NOARGS,
     "Returns an iterator over the customer."},
    {"items", PythonItemIterator::create, METH_NOARGS,
     "Returns an iterator over the items."},
    {"calendars", PythonCalendarIterator::create, METH_NOARGS,
     "Returns an iterator over the calendars."},
    {"demands", PythonDemandIterator::create, METH_NOARGS,
     "Returns an iterator over the demands."},
    {"resources", PythonResourceIterator::create, METH_NOARGS,
     "Returns an iterator over the resources."},
    {"operations", PythonOperationIterator::create, METH_NOARGS,
     "Returns an iterator over the operations."},
    {"operationplans", PythonOperationPlanIterator::create, METH_NOARGS,
     "Returns an iterator over the operationplans."},
    {"problems", PythonProblemIterator::create, METH_NOARGS,
     "Returns an iterator over the problems."},
    {NULL, NULL, 0, NULL}
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
    "command",
    "command_python",
    Object::createDefault<CommandPython>);

  // Register python also as a processing instruction.
  CommandPython::metadata2.registerClass(
    "instruction",
    "python",
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
      ("frepple", CommandPython::PythonAPI, "Access to the frePPLe library");
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
  nok += PythonPlan::initialize(m);
  nok += PythonBuffer::initialize(m);
  nok += PythonBufferDefault::initialize(m);
  nok += PythonBufferInfinite::initialize(m);
  nok += PythonBufferProcure::initialize(m);
  nok += PythonBufferIterator::initialize(m);
  nok += PythonLocation::initialize(m);
  nok += PythonLocationDefault::initialize(m);
  nok += PythonLocationIterator::initialize(m);
  nok += PythonItem::initialize(m);
  nok += PythonItemDefault::initialize(m);
  nok += PythonItemIterator::initialize(m);
  nok += PythonCustomer::initialize(m);
  nok += PythonCustomerDefault::initialize(m);
  nok += PythonCustomerIterator::initialize(m);
  nok += PythonCalendar::initialize(m);
  nok += PythonCalendarIterator::initialize(m);
  nok += PythonCalendarBucket::initialize(m);
  nok += PythonCalendarBucketIterator::initialize(m);
  nok += PythonCalendarBool::initialize(m);
  nok += PythonCalendarVoid::initialize(m);
  nok += PythonCalendarDouble::initialize(m);
  nok += PythonDemand::initialize(m);
  nok += PythonDemandIterator::initialize(m);
  nok += PythonDemandDefault::initialize(m);
  nok += PythonResource::initialize(m);
  nok += PythonResourceDefault::initialize(m);
  nok += PythonResourceInfinite::initialize(m);
  nok += PythonResourceIterator::initialize(m);
  nok += PythonOperation::initialize(m);
  nok += PythonOperationAlternate::initialize(m);
  nok += PythonOperationFixedTime::initialize(m);
  nok += PythonOperationTimePer::initialize(m);
  nok += PythonOperationRouting::initialize(m);
  nok += PythonOperationIterator::initialize(m);
  nok += PythonProblem::initialize(m);
  nok += PythonProblemIterator::initialize(m);
  nok += PythonOperationPlan::initialize(m);
  nok += PythonOperationPlanIterator::initialize(m);
  nok += PythonFlowPlan::initialize(m);
  nok += PythonFlowPlanIterator::initialize(m);
  nok += PythonLoadPlan::initialize(m);
  nok += PythonLoadPlanIterator::initialize(m);
  nok += PythonDemandPlanIterator::initialize(m);
  nok += PythonPeggingIterator::initialize(m);
  nok += PythonLoad::initialize(m);
  nok += PythonLoadIterator::initialize(m);
  nok += PythonFlow::initialize(m);
  nok += PythonFlowIterator::initialize(m);
  // @todo Missing Python proxies: Solver

  // Redirect the stderr and stdout streams of Python
  PyRun_SimpleString(
    "import frepple, sys\n"
    "class redirect:\n"
    "\tdef write(self,str):\n"
    "\t\tfrepple.log(str)\n"
    "sys.stdout = redirect()\n"
    "sys.stderr = redirect()"
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


} // End namespace
