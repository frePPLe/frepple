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

// Define the methods to be exposed into Python
PyMethodDef CommandPython::PythonAPI[] = 
{
  {"version", CommandPython::python_version, METH_NOARGS, 
     "Prints the frepple version."},
  {"readXMLdata", CommandPython::python_readXMLdata, METH_VARARGS, 
     "Processes an XML string passed as argument."},
  {"createItem", CommandPython::python_createItem, METH_VARARGS, 
     "Uses the C++ API to create an item."},
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

  // Initialize the interpreter and the frepple module
  Py_InitializeEx(0);  // The arg 0 indicates that the interpreter doesn't 
                       // implement its own signal handler
  Py_InitModule3
    ("frepple", CommandPython::PythonAPI, "Acces to the frepple API");
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

  // Execute the command
  if (!cmd.empty())
  {
    ScopeMutexLock l(interpreterbusy);
    cmd += "\n";  // Make sure last line is ended properly
  	PyObject *m = PyImport_AddModule("__main__");
	  if (!m) 
      throw frepple::RuntimeException("Can't initialize Python interpreter");
	  PyObject *d = PyModule_GetDict(m);
	  PyObject *v = PyRun_String(cmd.c_str(), Py_file_input, d, d);
	  if (v == NULL) {
		  PyErr_Print();
      throw frepple::RuntimeException("Error executing python command");
	  }
	  Py_DECREF(v);
	  if (Py_FlushLine()) PyErr_Clear();
  } 
  else if (!filename.empty())
  {
    ScopeMutexLock l(interpreterbusy);
    FILE *fp = fopen(filename.c_str(), "r");
    if(!fp)
      throw frepple::RuntimeException
        ("Can't open python file '" + filename + "'");
    if(PyRun_SimpleFile(fp,filename.c_str()))
      throw frepple::RuntimeException
        ("Error executing python file '" + filename + "'");
  }
  else
    throw DataException("Python command without statement or filename");

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


PyObject * CommandPython::python_version(PyObject *self, PyObject *args) 
{    
#ifdef VERSION
  return Py_BuildValue("s", VERSION);
#else
  return Py_BuildValue("s", "unknown");
#endif
}


PyObject * CommandPython::python_readXMLdata(PyObject *self, PyObject *args) 
{    
  char *data;
  int b1, b2;
  int ok = PyArg_ParseTuple(args, "sii", &data, &b1, &b2);
  if (!ok) return NULL;
  int i = FreppleWrapperReadXMLData(data,b1,b2);
  return Py_BuildValue("i", i);
}


PyObject * CommandPython::python_createItem(PyObject *self, PyObject *args) 
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

} // End namespace
