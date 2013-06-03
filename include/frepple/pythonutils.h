/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba                 *
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

/** @file pythonutils.h
  * @brief Reusable functions for python functionality.
  *
  * Utility classes for interfacing with the Python language.
  */

#include "frepple/utils.h"

namespace frepple
{
namespace utils
{

/** @brief A template class to expose category classes which use a string
  * as the key to Python. */
template <class T>
class FreppleCategory : public PythonExtension< FreppleCategory<T> >
{
  public:
    /** Initialization method. */
    static int initialize()
    {
      // Initialize the type
      PythonType& x = PythonExtension< FreppleCategory<T> >::getType();
      x.setName(T::metadata->type);
      x.setDoc("frePPLe " + T::metadata->type);
      x.supportgetattro();
      x.supportsetattro();
      x.supportstr();
      x.supportcompare();
      x.supportcreate(Object::create<T>);
      const_cast<MetaCategory*>(T::metadata)->pythonClass = x.type_object();
      return x.typeReady();
    }
};


/** @brief A template class to expose classes to Python. */
template <class ME, class BASE>
class FreppleClass  : public PythonExtension< FreppleClass<ME,BASE> >
{
  public:
    static int initialize()
    {
      // Initialize the type
      PythonType& x = PythonExtension< FreppleClass<ME,BASE> >::getType();
      x.setName(ME::metadata->type);
      x.setDoc("frePPLe " + ME::metadata->type);
      x.supportgetattro();
      x.supportsetattro();
      x.supportstr();
      x.supportcompare();
      x.supportcreate(Object::create<ME>);
      x.setBase(BASE::metadata->pythonClass);
      x.addMethod("toXML", ME::toXML, METH_VARARGS, "return a XML representation");
      const_cast<MetaClass*>(ME::metadata)->pythonClass = x.type_object();
      return x.typeReady();
    }
};

} // end namespace
} // end namespace
