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
  metadata = new MetaCategory("solver", "solvers", reader);

  // Initialize the Python class
  FreppleCategory<Solver>::getType().addMethod("solve", solve, METH_NOARGS, "run the solver");
  return FreppleCategory<Solver>::initialize();
}


DECLARE_EXPORT void Solver::writeElement
(Serializer* o, const Keyword &tag, mode m) const
{
  // The subclass should have written its own header
  assert(m == NOHEAD || m == NOHEADTAIL);

  // Fields
  if (loglevel) o->writeElement(Tags::tag_loglevel, loglevel);

  // Write the tail
  if (m != NOHEADTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Solver::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_loglevel))
  {
    int i = pElement.getInt();
    if (i<0 || i>USHRT_MAX)
      throw DataException("Invalid log level" + pElement.getString());
    setLogLevel(i);
  }
}


DECLARE_EXPORT PyObject* Solver::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_loglevel))
    return PythonObject(getLogLevel());
  return NULL;
}


DECLARE_EXPORT int Solver::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_loglevel))
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
