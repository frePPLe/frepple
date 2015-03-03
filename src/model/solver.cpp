/***************************************************************************
 *                                                                         *
 * Copyright (C) 2009 by Johan De Taeye, frePPLe bvba                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
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

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Solver> DECLARE_EXPORT Tree utils::HasName<Solver>::st;
DECLARE_EXPORT const MetaCategory* Solver::metadata;


int Solver::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("solver", "solvers", MetaCategory::ControllerDefault);

  // Initialize the Python class
  PythonType& x = FreppleCategory<Flow>::getType();
  x.setName("solver");
  x.setDoc("frePPLe solver");
  x.supportgetattro();
  x.supportsetattro();
  x.addMethod("solve", solve, METH_NOARGS, "run the solver");
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT PyObject* Solver::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_loglevel))
    return PythonObject(getLogLevel());
  return NULL;
}


DECLARE_EXPORT int Solver::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_loglevel))
    setLogLevel(field.getInt());
  else
    return -1;  // Error
  return 0;  // OK
}


DECLARE_EXPORT PyObject *Solver::solve(PyObject *self, PyObject *args)
{
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    static_cast<Solver*>(self)->solve();
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}

} // end namespace
