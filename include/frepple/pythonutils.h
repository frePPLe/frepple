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


/** @brief Template class to define Python extensions.
  *
  * The template argument should be your extension class, inheriting from
  * this template class:
  *   class MyClass : PythonExtension<MyClass>
  *
  * The structure of the C++ wrappers around the C Python API is heavily
  * inspired on the design of PyCXX.<br>
  * More information can be found on http://cxx.sourceforge.net
  */
template<class T>
class PythonExtension: public PythonExtensionBase, public NonCopyable
{
  public:
    /** Constructor. */
    explicit PythonExtension()
    {
      PyObject_Init(this, getType().type_object());
    }

    /** Destructor. */
    virtual ~PythonExtension() {}

    /** This method keeps the type information object for your extension. */
    static PythonType& getType() 
    {
      static PythonType* cachedTypePtr = NULL;
      if (cachedTypePtr) return *cachedTypePtr;
      
      // Scan the vector
      for (vector<PythonType*>::const_iterator i = table.begin(); i != table.end(); ++i)
        if (**i==typeid(T))
        {
          // Found...
          cachedTypePtr = *i;
          return *cachedTypePtr;
        }
      
      // Not found in the vector, so create a new one
      cachedTypePtr = new PythonType(sizeof(T), &typeid(T));
      table.push_back(cachedTypePtr);

      // Using our own memory deallocator
      cachedTypePtr->supportdealloc( deallocator );

      return *cachedTypePtr;
    }

    /** Free the memory.<br>
      * See the note on the memory management in the class documentation
      * for PythonExtensionBase.
      */
    static void deallocator(PyObject* o) {delete static_cast<T*>(o);}
};


/** @brief A template class to expose category classes which use a string
  * as the key to Python . */
template <class ME, class PROXY>
class FreppleCategory : public PythonExtension< FreppleCategory<ME,PROXY> >
{
  public:
    /** Initialization method. */
    static int initialize(PyObject* m)
    {
      // Initialize the type
      PythonType& x = PythonExtension< FreppleCategory<ME,PROXY> >::getType();
      x.setName(PROXY::metadata->type);
      x.setDoc("frePPLe " + PROXY::metadata->type);
      x.supportgetattro();
      x.supportsetattro();
      //x.supportstr();
      //x.supportcompare();xxx
      x.supportcreate(create);
      const_cast<MetaCategory*>(PROXY::metadata)->pythonClass = x.type_object();
      return x.typeReady(m);
    }

  private:
    /** Comparison operator. xxx
    int compare(const PythonObject& other)
    {
      if (!obj || !other.check(ME::getType()))
      {
        // Different type
        PyErr_SetString(PythonDataException, "Wrong type in comparison");
        return -1;
      }
      PROXY* y = static_cast<PROXY*>(static_cast<PyObject*>(other));
      return obj->getName().compare(y->getName());
    }*/

    static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    {
      try
      {
        // Find or create the C++ object
        PythonAttributeList atts(kwds);
        Object* x = PROXY::reader(PROXY::metadata,atts);
        
        // Object was deleted
        if (!x)       
        {
          Py_INCREF(Py_None);
          return Py_None;
        }

        // Iterate over extra keywords, and set attributes. @todo move this responsability to the readers...
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(kwds, &pos, &key, &value))
        {
          PythonObject field(value);
          Attribute attr(PyString_AsString(key));
          if (!attr.isA(Tags::tag_name) && !attr.isA(Tags::tag_type) && !attr.isA(Tags::tag_action))
          {
            int result = x->setattro(attr, field);
            if (result && !PyErr_Occurred())
              PyErr_Format(PyExc_AttributeError,
                "attribute '%s' on '%s' can't be updated",
                PyString_AsString(key), x->ob_type->tp_name);
          }
        };
        Py_INCREF(x);
        return x;
      }
      catch (...)
      {
        PythonType::evalException();
        return NULL;
      }
    }
};


/** @brief A template class to expose classes to Python. */
template <class ME, class BASE, class PROXY>
class FreppleClass  : public PythonExtension< FreppleClass<ME,BASE,PROXY> >
{
  public:
    static int initialize(PyObject* m)
    {
      // Initialize the type
      PythonType& x = PythonExtension< FreppleClass<ME,BASE,PROXY> >::getType();
      x.setName(PROXY::metadata->type);
      x.setDoc("frePPLe " + PROXY::metadata->type);
      x.supportgetattro();
      x.supportsetattro();
      //x.supportstr();xxx
     // x.supportcompare();xxx
      x.supportcreate(create);
      x.setBase(BASE::metadata->pythonClass);
      x.addMethod("toXML", PROXY::toXML, METH_VARARGS, "return a XML representation");
      const_cast<MetaClass*>(PROXY::metadata)->pythonClass = x.type_object();
      return x.typeReady(m);
    }

    
    /** Return the name as the string representation in Python. xxx */  
    /*
    PyObject* str()
    {
      return PythonObject(string("test"));
    }
    */

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

    /** Generator function. */
    static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    {
      try
      {
        // Find or create the C++ object
        PythonAttributeList atts(kwds);
        Object* x = PROXY::reader(PROXY::metadata,atts);
        
        // Object was deleted
        if (!x)       
        {
          Py_INCREF(Py_None);
          return Py_None;
        }

        // Iterate over extra keywords, and set attributes.   @todo move this responsability to the readers...
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(kwds, &pos, &key, &value))
        {
          PythonObject field(value);
          Attribute attr(PyString_AsString(key));
          if (!attr.isA(Tags::tag_name) && !attr.isA(Tags::tag_type) && !attr.isA(Tags::tag_action))
          {
            int result = x->setattro(attr, field);
            if (result && !PyErr_Occurred())
              PyErr_Format(PyExc_AttributeError,
                "attribute '%s' on '%s' can't be updated",
                PyString_AsString(key), x->ob_type->tp_name);
          }
        };
        Py_INCREF(x);
        return x;
      }
      catch (...)
      {
        PythonType::evalException();
        return NULL;
      }
    }
};


/** @brief A template class to expose iterators to Python. */
template <class ME, class ITERCLASS, class DATACLASS, class PROXYCLASS>
class FreppleIterator : public PythonExtension<ME>
{
  public:
    static int initialize(PyObject* m)
    {
      // Initialize the type
      PythonType& x = PythonExtension<ME>::getType();
      x.setName(DATACLASS::metadata->type + "Iterator");
      x.setDoc("frePPLe iterator for " + DATACLASS::metadata->type);
      x.supportiter();
      return x.typeReady(m);
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
