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

/* Python.h has to be included first. */
#include "Python.h"
#include "datetime.h"

#include "forecast.h"

namespace module_forecast
{

PyTypeObject PythonForecast::InfoType =
{
  PyObject_HEAD_INIT(NULL)
  0,					/* ob_size */
  "freppleforecast.forecast",	/* tp_name */
  sizeof(PythonForecast),	/* tp_basicsize */
  0,					/* tp_itemsize */
  reinterpret_cast<destructor>(PythonForecast::destroy),  /* tp_dealloc */
  0,					/* tp_print */
  0,					/* tp_getattr */
  0,					/* tp_setattr */
  0,					/* tp_compare */
  0,	        /* tp_repr */
  0,					/* tp_as_number */
  0,					/* tp_as_sequence */
  0,					/* tp_as_mapping */
  0,					/* tp_hash */
  0,          /* tp_call */
  0,					/* tp_str */
  0,		      /* tp_getattro */
  0,					/* tp_setattro */
  0,					/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
  "frePPLe forecast", /* tp_doc */
  0,					/* tp_traverse */
  0,					/* tp_clear */
  0,					/* tp_richcompare */
  0,					/* tp_weaklistoffset */
  PyObject_SelfIter,  /* tp_iter */
  reinterpret_cast<iternextfunc>(PythonForecast::next),	/* tp_iternext */
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
  PythonForecast::create,	/* tp_new */
  0,					/* tp_free */
};


PyTypeObject PythonForecastBucket::InfoType =
{
  PyObject_HEAD_INIT(NULL)
  0,					/* ob_size */
  "freppleforecast.bucket",	/* tp_name */
  sizeof(PythonForecastBucket),	/* tp_basicsize */
  0,					/* tp_itemsize */
  reinterpret_cast<destructor>(PythonForecastBucket::destroy),  /* tp_dealloc */
  0,					/* tp_print */
  0,					/* tp_getattr */
  0,					/* tp_setattr */
  0,					/* tp_compare */
  0,	        /* tp_repr */
  0,					/* tp_as_number */
  0,					/* tp_as_sequence */
  0,					/* tp_as_mapping */
  0,					/* tp_hash */
  0,          /* tp_call */
  0,					/* tp_str */
  0,		      /* tp_getattro */
  0,					/* tp_setattro */
  0,					/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
  "frePPLe forecast bucket", /* tp_doc */
  0,					/* tp_traverse */
  0,					/* tp_clear */
  0,					/* tp_richcompare */
  0,					/* tp_weaklistoffset */
  PyObject_SelfIter,  /* tp_iter */
  reinterpret_cast<iternextfunc>(PythonForecastBucket::next),	/* tp_iternext */
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
  PythonForecastBucket::create,	/* tp_new */
  0,					/* tp_free */
};


void initializePython()
{
  // Check the status of the interpreter, and lock it
  if (!Py_IsInitialized())
    throw frepple::RuntimeException("Python module is not initialized correctly");
  PyEval_AcquireLock();
  try
  {

    // Create a new module
    PyObject* m = Py_InitModule("freppleforecast", NULL);  // @todo frepple.forecast would be a cleaner name...
    if (!m)
      throw frepple::RuntimeException("Can't initialize Python extensions");

    // Register new forecast type
    if (PyType_Ready(&PythonForecast::InfoType) < 0)
      throw frepple::RuntimeException("Can't register python type Forecast");
    Py_INCREF(&PythonForecast::InfoType);
    PyModule_AddObject(m, "forecast", reinterpret_cast<PyObject*>(&PythonForecast::InfoType));

    // Register new forecast bucket type
    if (PyType_Ready(&PythonForecastBucket::InfoType) < 0)
      throw frepple::RuntimeException("Can't register python type ForecastBucket");
    Py_INCREF(&PythonForecastBucket::InfoType);
    PyModule_AddObject(m, "bucket", reinterpret_cast<PyObject*>(&PythonForecastBucket::InfoType));

    // Make the datetime types available
    PyDateTime_IMPORT;

  }
  // Release the global lock when leaving the function
  catch (...)
  {
    PyEval_ReleaseLock();
    throw;  // Rethrow the exception
  }
  PyEval_ReleaseLock();
}


PyObject* PythonDateTime(const Date& d)   // @todo avoid redefining this function - already in python module
{
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
  return PyDateTime_FromDateAndTime(t.tm_year+1900, t.tm_mon+1, t.tm_mday,
      t.tm_hour, t.tm_min, t.tm_sec, 0);
}


extern "C" PyObject* PythonForecast::create(PyTypeObject* type, PyObject *args, PyObject *kwargs)
{
  PythonForecast* obj = PyObject_New(PythonForecast, &PythonForecast::InfoType);
  obj->iter = Forecast::getForecasts().begin();
  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonForecast::next(PythonForecast* obj)
{
  if (obj->iter != Forecast::getForecasts().end())
  {
    // Build a python dictionary
    PyObject* result = Py_BuildValue("{s:s,s:s,s:s,s:O}",
      "NAME", obj->iter->second->getName().c_str(),
      "CUSTOMER", obj->iter->first.second ? obj->iter->first.second->getName().c_str() : NULL,
      "ITEM", obj->iter->first.first ? obj->iter->first.first->getName().c_str() : NULL,
      "BUCKETS", PythonForecastBucket::createFromForecast(&*(obj->iter->second))
      );
    ++(obj->iter);
    return result;
  }
  // Reached the end of the iteration
  return NULL;
}


extern "C" PyObject* PythonForecastBucket::createFromForecast(Forecast* fcst)
{
  PythonForecastBucket* obj = PyObject_New(PythonForecastBucket, &PythonForecastBucket::InfoType);
  obj->iter = fcst ? dynamic_cast<Forecast::ForecastBucket*>(&*(fcst->beginMember())) : NULL;
  return reinterpret_cast<PyObject*>(obj);
}


extern "C" PyObject* PythonForecastBucket::next(PythonForecastBucket* obj)
{
  if (!obj->iter) return NULL;
  PyObject* result = Py_BuildValue("{s:N,s:N,s:f,s:f,s:f}",
    "START_DATE", PythonDateTime(obj->iter->timebucket.getStart()),
    "END_DATE", PythonDateTime(obj->iter->timebucket.getEnd()),
    "TOTALQTY", obj->iter->total,
    "CONSUMEDQTY", obj->iter->consumed,
    "NETQTY", obj->iter->total - obj->iter->consumed
    );
  obj->iter = obj->iter->next;
  return result;
}

} // end namespace
