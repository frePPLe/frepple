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
  catch (...)
  {
    Py_BLOCK_THREADS; 
    PythonType::evalException(); 
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");  // Safer than using Py_None, which is not
                             // portable across compilers
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
  catch (...)
  {
    Py_BLOCK_THREADS; 
    PythonType::evalException(); 
    return NULL;
  }
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
  catch (...)
  {
    Py_BLOCK_THREADS; 
    PythonType::evalException(); 
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


PyObject *CommandPython::python_saveXMLstring(PyObject* self, PyObject* args)
{
  // Execute and catch exceptions
  string result;
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try { result = FreppleSaveString(); }
  catch (...)
  {
    Py_BLOCK_THREADS; 
    PythonType::evalException(); 
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("s",result.c_str());
}


} // End namespace
