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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
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
  * as the key to Python . */
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
      //x.supportstr();
      //x.supportcompare();xxx
      x.supportcreate(Object::create<T>);
      const_cast<MetaCategory*>(T::metadata)->pythonClass = x.type_object();
      return x.typeReady(PythonInterpreter::getModule());
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
      // x.supportcompare();xxx
      x.supportcreate(Object::create<ME>);
      x.setBase(BASE::metadata->pythonClass);
      x.addMethod("toXML", ME::toXML, METH_VARARGS, "return a XML representation");
      const_cast<MetaClass*>(ME::metadata)->pythonClass = x.type_object();
      return x.typeReady(PythonInterpreter::getModule());
    }

    /** Comparison operator. */
    /*
    xxx int compare(const PythonObject& other)
    {
      if (!obj || !other.check(BASE::getType()))
      {
        // Different type
        PyErr_SetString(PythonDataException, "Wrong type in comparison");
        return -1;
      }
      BASE* y = static_cast<BASE*>(static_cast<PyObject*>(other));
      return obj->getName().compare(y->getName());
    }
    */
};


/** @brief A template class to expose iterators to Python. */
template <class ME, class ITERCLASS, class DATACLASS>
class FreppleIterator : public PythonExtension<ME>
{
  public:
    static int initialize()
    {
      // Initialize the type
      PythonType& x = PythonExtension<ME>::getType();
      x.setName(DATACLASS::metadata->type + "Iterator");
      x.setDoc("frePPLe iterator for " + DATACLASS::metadata->type);
      x.supportiter();
      return x.typeReady(PythonInterpreter::getModule());
    }

    FreppleIterator() : i(DATACLASS::begin()) {initType(PythonExtension<ME>::getType().type_object());}

    template <class OTHER> FreppleIterator(const OTHER *o) : i(o) {}

    static PyObject* create(PyObject* self, PyObject* args)
     {return new ME();}

  private:
    ITERCLASS i;

    virtual PyObject* iternext()
    {
      if (i == DATACLASS::end()) return NULL;
      PyObject* result = &*i;
      ++i;
      Py_INCREF(result);
      return result;
    }
};

} // end namespace
} // end namespace
