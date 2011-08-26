/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba                 *
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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#include "module.h"


namespace module_webservice
{

unsigned int CommandWebservice::port = 6262;
unsigned int CommandWebservice::threads = 10;


MODULE_EXPORT const char* initialize(const Environment::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  static const char* name = "webservice";
  if (init)
  {
    logger << "Warning: Initializing module webservice more than once." << endl;
    return name;
  }
  init = true;

  try
  {
    // Process the module parameters
    for (Environment::ParameterList::const_iterator x = z.begin();
      x != z.end(); ++x)
    {
      if (x->first == "port")
        CommandWebservice::setPort(x->second.getInt());
      else if (x->first == "threads")
        CommandWebservice::setThreads(x->second.getInt());
      else
        logger << "Warning: Unrecognized parameter '" << x->first << "'" << endl;
    }

    // Initialize the Python extension.
    PyGILState_STATE state = PyGILState_Ensure();
    try
    {
      // Register new Python data types
      PythonInterpreter::registerGlobalMethod(
        "webservice", CommandWebservice::pythonService, METH_NOARGS,
        "Starts the webservice to listen for HTTP requests");
      PyGILState_Release(state);
    }
    catch (exception &e)
    {
      PyGILState_Release(state);
      logger << "Error: " << e.what() << endl;
    }
    catch (...)
    {
      PyGILState_Release(state);
      logger << "Error: unknown exception" << endl;
    }

  // Return the name of the module
  return name;
}


}       // end namespace
