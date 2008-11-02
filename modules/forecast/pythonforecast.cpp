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

/* PythonUtils.h has to be included first.*/
#include "frepple/pythonutils.h"
#include "forecast.h"
using namespace frepple::python;

namespace module_forecast
{

int PythonForecast::initialize(PyObject* m)
{
  // Add a method for forecast generation
  getType().addMethod("timeseries", (PyCFunction)timeseries, METH_VARARGS,
     "Set the future based on the timeseries of historical data");

  // Normal initialization for the rest
  return FreppleClass<PythonForecast,PythonDemand,Forecast>::initialize(m);
}


void initializePython()
{
  // Check the status of the interpreter, and lock it
  if (!Py_IsInitialized())
    throw RuntimeException("Python isn't initialized correctly");
  PyEval_AcquireLock();
  try
  {
    // Register new Python data types
    if (PythonForecast::initialize(PythonInterpreter::getModule()))
      throw RuntimeException("Error registering Python forecast extension");
    if (PythonForecastBucket::initialize(PythonInterpreter::getModule()))
      throw RuntimeException("Error registering Python forecastbucket extension");

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


PyObject* PythonForecast::getattro(const Attribute& attr)
{
  if (!obj) return Py_None;
  if (attr.isA(Tags::tag_calendar))
    return PythonObject(obj->getCalendar());
  return PythonDemand(obj).getattro(attr); 
}


int PythonForecast::setattro(const Attribute& attr, const PythonObject& field)
{
  logger << "   PP " << attr.getName() << "  " << attr.isA(Tags::tag_calendar) << endl;
  if (attr.isA(Tags::tag_calendar))
  {
    logger << "OOOcOO" << endl;
    if (!field.check(PythonCalendar::getType())) 
    {
    logger << "OOODOO" << endl;
      PyErr_SetString(PythonDataException, "forecast calendar must be of type calendar");
      return -1;
    }
    logger << "OOOaOO" << endl;
    Calendar* y = static_cast<PythonCalendar*>(static_cast<PyObject*>(field))->obj;
    obj->setCalendar(y);
    logger << "OOObOO" << endl;
  }  
  else
    return PythonDemand(obj).setattro(attr, field);  
  return 0; // OK
}


extern "C" PyObject* PythonForecast::timeseries(PyObject *self, PyObject *args)
{
  // Get the forecast model
  Forecast* forecast = reinterpret_cast<PythonForecast*>(self)->obj;
  logger << "willy " << forecast->getName() << endl;

  // Parse the Python arguments
  PyObject* history;
  PyObject* buckets = NULL;
  int ok = PyArg_ParseTuple(args, "O|O", &history, &buckets);
  if (!ok) return NULL;

  // Verify we can iterate over the arguments
  PyObject *historyiterator = PyObject_GetIter(history);
  PyObject *bucketiterator = NULL;
  if (!historyiterator)
  {
    PyErr_Format(PyExc_AttributeError,"Invalid type for time series");
    return NULL;
  }
  if (buckets)
  {
    bucketiterator = PyObject_GetIter(buckets);
    if (!bucketiterator)
    {
      PyErr_Format(PyExc_AttributeError,"Invalid type for time series");
      return NULL;
    }
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

  // Copy the bucket data into a C++ data structure     @todo bucketiterator can be null
  Date bucketdata[300];
  unsigned int bucketcount = 0;
  while (item = PyIter_Next(bucketiterator))
  {
    bucketdata[bucketcount++] = PythonObject(item).getDate();
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
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Release the Python interpreter
  return Py_BuildValue("");
}


int PythonForecastBucket::initialize(PyObject* m)
{
  // Initialize the type
  // Note: No support for creation
  PythonType& x = getType();
  x.setName("demand_forecastbucket");
  x.setDoc("frePPLe forecastbucket");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaCategory&>(Demand::metadata).factoryPythonProxy = proxy;
  return x.typeReady(m);
}


PyObject* PythonForecastBucket::getattro(const Attribute& attr)
{
/* xxx
  PyObject* result = Py_BuildValue("{s:N,s:N,s:f,s:f,s:f}",
    "start_date", PythonObject(obj->iter->timebucket.getStart()),
    "end_date", PythonObject(obj->iter->timebucket.getEnd()),
    "totalqty", obj->iter->total,
    "consumedqty", obj->iter->consumed,
    "netqty", obj->iter->total - obj->iter->consumed
    );
*/
  return PythonDemand(obj).getattro(attr); 
}


int PythonForecastBucket::setattro(const Attribute& attr, const PythonObject& field)
{
  return PythonDemand(obj).setattro(attr, field);  
}

} // end namespace
