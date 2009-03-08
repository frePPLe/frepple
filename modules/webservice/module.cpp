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

#include "module.h"


namespace module_webservice
{

const MetaClass CommandWebservice::metadata;

unsigned int CommandWebservice::port = 6262;
unsigned int CommandWebservice::threads = 10;


MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z)
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

  // Process the module parameters
  for (CommandLoadLibrary::ParameterList::const_iterator x = z.begin();
    x != z.end(); ++x)
  {
    if (x->first == "port")
      CommandWebservice::setPort(x->second.getInt());
    else if (x->first == "threads")
      CommandWebservice::setThreads(x->second.getInt());
    else
      logger << "Warning: Unrecognized parameter '" << x->first << "'" << endl;
  }

  // Initialize the metadata.
  PythonInterpreter::registerGlobalMethod(
    "webservice", CommandWebservice::pythonService, METH_NOARGS,
    "Starts the webservice to listen for HTTP requests");

  // Return the name of the module
  return name;
}


}       // end namespace
