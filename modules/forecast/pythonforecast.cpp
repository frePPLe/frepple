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

/* Python.h has to be included first.
   For a debugging build on windows we avoid using the debug version of Python
   since that also requires Python and all its modules to be compiled in debug
   mode.
*/
#if defined(_DEBUG) && defined(_MSC_VER)
#undef _DEBUG
#include "Python.h"
#define _DEBUG
#else
#include "Python.h"
#endif
#include "datetime.h"

#include "forecast.h"

namespace module_forecast
{

// Include commonly used utility functions, provided by the python module
#ifndef DOXYGEN
#include "../python/pythonutils.h"
#include "../python/pythonutils.cpp"
#endif

PyMethodDef PythonForecast::methods[] = {
    {"timeseries", (PyCFunction)PythonForecast::timeseries, METH_VARARGS,
     "Set the future based on the timeseries of historical data"
    },
    {NULL}  /* Sentinel */
};


/** @todo Use the new python api utilities */
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
  PythonForecast::methods,	/* tp_methods */
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
    // Putting the extension in a Python submodule would be cleaner.
    // Unfortunately the Python API's don't allow this.
    PyObject* m = Py_InitModule("freppleforecast", NULL);
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
      "name", obj->iter->second->getName().c_str(),
      "customer", obj->iter->first.second ? obj->iter->first.second->getName().c_str() : NULL,
      "item", obj->iter->first.first ? obj->iter->first.first->getName().c_str() : NULL,
      "buckets", PythonForecastBucket::createFromForecast(&*(obj->iter->second))
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
    "start_date", PythonDateTime(obj->iter->timebucket.getStart()),
    "end_date", PythonDateTime(obj->iter->timebucket.getEnd()),
    "totalqty", obj->iter->total,
    "consumedqty", obj->iter->consumed,
    "netqty", obj->iter->total - obj->iter->consumed
    );
  obj->iter = obj->iter->next;
  return result;
}


Date getDate(PyObject* obj)   // @todo remove this method
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


extern "C" PyObject* PythonForecast::timeseries(PyObject *self, PyObject *args)
{
  // Get the forecast model
  Forecast* forecast = reinterpret_cast<PythonForecast*>(self)->iter->second;

  // Parse the Python arguments
  PyObject* history;
  PyObject* buckets;
  int ok = PyArg_ParseTuple(args, "OO", &history, &buckets);
  if (!ok) return NULL;

  // Verify we can iterate over the arguments
  PyObject *historyiterator = PyObject_GetIter(history);
  PyObject *bucketiterator = PyObject_GetIter(buckets);
  if (!historyiterator || !bucketiterator)
  {
    PyErr_Format(PyExc_AttributeError,"Invalid argument type");
    return NULL;
  }

  // Copy the history data into a C++ data structure
  double data[300];
  unsigned int historycount = 0;
  PyObject *item;
  while (item = PyIter_Next(historyiterator))
  {
    data[historycount++] = PyFloat_AsDouble(item);
    Py_DECREF(item);
    if (historycount>=300) break;
  }
  Py_DECREF(historyiterator);

  // Copy the bucket data into a C++ data structure
  Date bucketdata[300];
  unsigned int bucketcount = 0;
  while (item = PyIter_Next(bucketiterator))
  {
    bucketdata[bucketcount++] = getDate(item);
    Py_DECREF(item);
    if (bucketcount>=300) break;
  }
  Py_DECREF(bucketiterator);

  Py_BEGIN_ALLOW_THREADS  // Free the Python interpreter for other threads
  try {
    // Generate the forecast
    forecast->generateFutureValues
      (data, historycount, bucketdata, bucketcount, true);
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    // @todo PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim the Python interpreter
  return Py_BuildValue("");
}

} // end namespace
