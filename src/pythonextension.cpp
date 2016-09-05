/***************************************************************************
 *                                                                         *
 * Copyright (C) 2015 by frePPLe bvba                                      *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 *(at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;

/** Used to initialize frePPLe as a Python extension module. */
PyMODINIT_FUNC PyInit_frepple(void)
{
  try
  {
    // Initialize frePPLe, without reading the configuration
    // files init.xml or init.py
    FreppleInitialize(false);
    return PythonInterpreter::getModule();
  }
  catch(const exception& e)
  {
    PyErr_SetString(PyExc_SystemError, e.what());
    return nullptr;
  }
  catch (...)
  {
    PyErr_SetString(PyExc_SystemError, "Initialization failed");
    return nullptr;
  }
}
