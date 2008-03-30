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

/** @file wrapper.cpp
  * @brief Generic C++ wrapper classes to facilitate working with Python.
  *
  * The structure of the C++ wrappers around the C Python API is heavily 
  * based on the design of PyCXX.<br> 
  * More information can be found on http://cxx.sourceforge.net
  */

#include "embeddedpython.h"

namespace module_python
{


const PyTypeObject PythonType::PyTypeObjectTemplate =
  {
    PyObject_HEAD_INIT(NULL)
    0,					/* ob_size */
    "frepple.unspecified",	/* WILL BE UPDATED tp_name */
    0,	/* WILL BE UPDATED tp_basicsize */
    0,					/* tp_itemsize */
    0,  /* CAN BE UPDATED tp_dealloc */
    0,					/* tp_print */
    0,					/* tp_getattr */
    0,					/* tp_setattr */
    0,					/* tp_compare */
    0,	        /* tp_repr */
    0,					/* tp_as_number */
    0,					/* tp_as_sequence */
    0,					/* tp_as_mapping */
    0,					/* tp_hash */
    0,  /* CAN BE UPDATED tp_call */
    0,	/* CAN BE UPDATED tp_str */
    0,	/* CAN BE UPDATED tp_getattro */
    0,	/* CAN BE UPDATED tp_setattro */
    0,					/* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
    "std doc", /* CAN BE UPDATED  tp_doc */
    0,					/* tp_traverse */
    0,					/* tp_clear */
    0,					/* tp_richcompare */
    0,					/* tp_weaklistoffset */
    0,   /* CAN BE UPDATED tp_iter */
    0,	 /* CAN BE UPDATED tp_iternext */
    0,				  /* tp_methods */
    0,					/* tp_members */
    0,					/* tp_getset */
    0,					/* tp_base */
    0,					/* tp_dict */
    0,					/* tp_descr_get */
    0,					/* tp_descr_set */
    0,					/* tp_dictoffset */
    0,          /* tp_init */
    0,          /* tp_alloc */
    0,	/* CAN BE UPDATED tp_new */
    0,					/* tp_free */
  };


// Include the code of commonly used python utility functions
#ifndef DOXYGEN
#include "pythonutils.cpp"
#endif


PythonObject::PythonObject(const Date& d)
{
  PyDateTime_IMPORT;
  // The standard library function localtime() is not re-entrant: the same
  // static structure is used for all calls. In a multi-threaded environment
  // the function is not to be used.
  // The POSIX standard defines a re-entrant version of the function:
  // localtime_r.
  // Visual C++ 6.0 and Borland 5.5 are missing it, but provide a thread-safe
  // variant without changing the function semantics.
  time_t ticks = d.getTicks();
#ifdef HAVE_LOCALTIME_R
  struct tm t;
  localtime_r(&ticks, &t);
#else
  struct tm t = *localtime(&ticks);
#endif
  obj = PyDateTime_FromDateAndTime(t.tm_year+1900, t.tm_mon+1, t.tm_mday,
      t.tm_hour, t.tm_min, t.tm_sec, 0);
}


Date PythonObject::getDate() const 
{
  PyDateTime_IMPORT;
  if (PyDateTime_Check(obj))
    return Date(
      PyDateTime_GET_YEAR(obj), 
      PyDateTime_GET_MONTH(obj), 
      PyDateTime_GET_DAY(obj), 
      PyDateTime_DATE_GET_HOUR(obj), 
      PyDateTime_DATE_GET_MINUTE(obj), 
      PyDateTime_DATE_GET_SECOND(obj)
      );
  else if (PyDate_Check(obj))
    return Date(
      PyDateTime_GET_YEAR(obj), 
      PyDateTime_GET_MONTH(obj), 
      PyDateTime_GET_DAY(obj) 
      );
  else 
   throw DataException(
    "Invalid data type. Expecting datetime.date or datetime.datetime"
    );
}


PythonObject::PythonObject(Object* p)
{
  if (!p)
  {
    obj = Py_None;
    Py_INCREF(obj);
  }
  else if (p->getType().factoryPythonProxy)
    obj = reinterpret_cast<PyObject*>(p->getType().factoryPythonProxy(p)); 
  else if (p->getType().category->factoryPythonProxy)
    obj = reinterpret_cast<PyObject*>(p->getType().category->factoryPythonProxy(p));  
  else
    throw LogicException("Can't create a Python proxy for " + p->getType().type);
}


PythonType::PythonType(size_t base_size)
{
  // Copy a standard info type to start with
  memcpy(&table, &PyTypeObjectTemplate, sizeof(PyTypeObject));
  table.tp_basicsize =	base_size; 
}


int PythonType::typeReady(PyObject* m)
{
  // Register the new type in the module  
  if (PyType_Ready(&table) < 0)
    throw frepple::RuntimeException("Can't register python type " + name);
  Py_INCREF(&table);
  // Note: +8 is to skip the "frepple." characters in the name
  return PyModule_AddObject(m, name.c_str() + 8, reinterpret_cast<PyObject*>(&table));
}


extern "C" PyObject* getattro_handler(PyObject *self, PyObject *name)
{
  try
  {
    if (!PyString_Check(name))
		{
      PyErr_Format(PyExc_TypeError, 
        "attribute name must be string, not '%s'", 
        name->ob_type->tp_name);
			return NULL;
		}
    XMLElement field(PyString_AsString(name)); 
    PyObject* result = static_cast<PythonExtensionBase*>(self)->getattro(field);  
    // Exit 1: Normal
    if (result) return result;
    // Exit 2: Exception occurred
    if (PyErr_Occurred()) return NULL;
    // Exit 3: No error occurred but the attribute was not found. 
    // Use the standard generic function to pick up  standard attributes 
    // (such as __class__, __doc__, ...)
    // Note that this function also picks up attributes from base classes, but
    // we can't rely on that: any C++ exceptions are lost along the way...
    return PyObject_GenericGetAttr(self,name);                  
  }
  catch (DataException e)                                                     
  {                                                                           
    PyErr_SetString(PythonDataException, e.what());                           
    return NULL;                                                                
  }                                                                           
  catch (LogicException e)                                                    
  {                                                                           
    PyErr_SetString(PythonLogicException, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (frepple::RuntimeException e)                                         
  {                                                                           
    PyErr_SetString(PythonRuntimeException, e.what());                        
    return NULL;                                                                
  }                                                                           
  catch (exception e)                                                         
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (...)                                                                 
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, "Unidentified exception");          
    return NULL;                                                                
  }                                                                           
}                                                                             


extern "C" int setattro_handler(PyObject *self, PyObject *name, PyObject *value)
{
  try
  {
    // Pick up the field name
    if (!PyString_Check(name))
		{
      PyErr_Format(PyExc_TypeError, 
        "attribute name must be string, not '%s'", 
        name->ob_type->tp_name);
			return -1;
		}
    XMLElement field(PyString_AsString(name)); 

    // Call the object to update the attribute
    int result = static_cast<PythonExtensionBase*>(self)->setattro(field, value);

    // Process result
    if (!result) return 0;
    PyErr_Format(PyExc_AttributeError, 
      "attribute '%s' on '%s' can't be updated", 
      PyString_AsString(name), self->ob_type->tp_name);
		return -1;
  }
  catch (DataException e)                                                     
  {                                                                           
    PyErr_SetString(PythonDataException, e.what()); 
    return -1;                                                                
  }                                                                           
  catch (LogicException e)                                                    
  {                                                                           
    PyErr_SetString(PythonLogicException, e.what());                          
    return -1;                                                                
  }                                                                           
  catch (frepple::RuntimeException e)                                         
  {                                                                           
    PyErr_SetString(PythonRuntimeException, e.what());                        
    return -1;                                                                
  }                                                                           
  catch (exception e)                                                         
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, e.what());                          
    return -1;                                                                
  }                                                                           
  catch (...)                                                                 
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, "Unidentified exception");          
    return -1;                                                                
  }                                                                           
}                                                                             
                                                                                  

extern "C" int compare_handler(PyObject *self, PyObject *other)
{
  try
  {
    return static_cast<PythonExtensionBase*>(self)->compare(other);
  }
  catch (DataException e)                                                     
  {                                                                           
    PyErr_SetString(PythonDataException, e.what());                           
    return -1;                                                                
  }                                                                           
  catch (LogicException e)                                                    
  {                                                                           
    PyErr_SetString(PythonLogicException, e.what());                          
    return -1;                                                                
  }                                                                           
  catch (frepple::RuntimeException e)                                         
  {                                                                           
    PyErr_SetString(PythonRuntimeException, e.what());                        
    return -1;                                                                
  }                                                                           
  catch (exception e)                                                         
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, e.what());                          
    return -1;                                                                
  }                                                                           
  catch (...)                                                                 
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, "Unidentified exception");          
    return -1;                                                                
  } 
}


extern "C" PyObject* iternext_handler(PyObject *self)
{
  try
  {
    return static_cast<PythonExtensionBase*>(self)->iternext();
  }
  catch (DataException e)                                                     
  {                                                                           
    PyErr_SetString(PythonDataException, e.what());                           
    return NULL;                                                                
  }                                                                           
  catch (LogicException e)                                                    
  {                                                                           
    PyErr_SetString(PythonLogicException, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (frepple::RuntimeException e)                                         
  {                                                                           
    PyErr_SetString(PythonRuntimeException, e.what());                        
    return NULL;                                                                
  }                                                                           
  catch (exception e)                                                         
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (...)                                                                 
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, "Unidentified exception");          
    return NULL;                                                                
  }         
}


extern "C" PyObject* call_handler(PyObject* self, PyObject* args, PyObject* kwds)
{
  try
  {
    return static_cast<PythonExtensionBase*>(self)->call(args, kwds);
  }
  catch (DataException e)                                                     
  {                                                                           
    PyErr_SetString(PythonDataException, e.what());                           
    return NULL;                                                                
  }                                                                           
  catch (LogicException e)                                                    
  {                                                                           
    PyErr_SetString(PythonLogicException, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (frepple::RuntimeException e)                                         
  {                                                                           
    PyErr_SetString(PythonRuntimeException, e.what());                        
    return NULL;                                                                
  }                                                                           
  catch (exception e)                                                         
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (...)                                                                 
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, "Unidentified exception");          
    return NULL;                                                                
  }         
}


extern "C" PyObject* str_handler(PyObject* self)
{
  try
  {
    return static_cast<PythonExtensionBase*>(self)->str();
  }
  catch (DataException e)                                                     
  {                                                                           
    PyErr_SetString(PythonDataException, e.what());                           
    return NULL;                                                                
  }                                                                           
  catch (LogicException e)                                                    
  {                                                                           
    PyErr_SetString(PythonLogicException, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (frepple::RuntimeException e)                                         
  {                                                                           
    PyErr_SetString(PythonRuntimeException, e.what());                        
    return NULL;                                                                
  }                                                                           
  catch (exception e)                                                         
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, e.what());                          
    return NULL;                                                                
  }                                                                           
  catch (...)                                                                 
  {                                                                           
    PyErr_SetString(PyExc_AttributeError, "Unidentified exception");          
    return NULL;                                                                
  }         
}


} // End namespace
