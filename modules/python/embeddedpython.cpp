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
  Py_InitializeEx(0);
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
    if(PyRun_SimpleString(cmd.c_str()))
      throw frepple::RuntimeException("Error executing python command");
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



} // End namespace
