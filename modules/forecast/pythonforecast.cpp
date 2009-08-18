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

#include "forecast.h"

namespace module_forecast
{

int PythonForecast::initialize(PyObject* m)
{
  // Add a method for forecast generation
  getType().addMethod("timeseries", Forecast::timeseries, METH_VARARGS,
     "Set the future based on the timeseries of historical data");

  // Normal initialization for the rest
  return FreppleClass<PythonForecast,PythonDemand,Forecast>::initialize(m);
}


PyObject* Forecast::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_calendar))
    return PythonObject(getCalendar());
  else if (attr.isA(Tags::tag_discrete))
    return PythonObject(getDiscrete());
  return Demand::getattro(attr); 
}


int Forecast::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_calendar))
  {
    if (!field.check(PythonCalendar::getType())) 
    {
      PyErr_SetString(PythonDataException, "forecast calendar must be of type calendar");
      return -1;
    }
    Calendar* y = static_cast<Calendar*>(static_cast<PyObject*>(field));
    setCalendar(y);
  }  
  else if (attr.isA(Tags::tag_discrete))
    setDiscrete(field.getBool());
  else
    return Demand::setattro(attr, field);  
  return 0; // OK
}


extern "C" PyObject* Forecast::timeseries(PyObject *self, PyObject *args)
{
  // Get the forecast model
  Forecast* forecast = static_cast<Forecast*>(self);

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
  if (buckets) bucketiterator = PyObject_GetIter(buckets);
  if (!bucketiterator)
  {
    PyErr_Format(PyExc_AttributeError,"Invalid type for time series");
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
  const_cast<MetaClass*>(ForecastBucket::metadata)->pythonClass = x.type_object();
  return x.typeReady(m);
}


PyObject* ForecastBucket::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_startdate))
    return PythonObject(getDueRange().getStart());
  if (attr.isA(Tags::tag_enddate))
    return PythonObject(getDueRange().getEnd());
  if (attr.isA(Forecast::tag_total))
    return PythonObject(getTotal());
  if (attr.isA(Forecast::tag_consumed))
    return PythonObject(getConsumed());
  if (attr.isA(Tags::tag_weight))
    return PythonObject(getWeight());
  return Demand::getattro(attr); 
}


int ForecastBucket::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Forecast::tag_total))
    setTotal(field.getDouble());
  else if (attr.isA(Forecast::tag_consumed))
    setConsumed(field.getDouble());
  else if (attr.isA(Tags::tag_weight))
    setWeight(field.getDouble());
  else
    return Demand::setattro(attr, field);  
  return 0;  // OK
}


PyObject* ForecastSolver::getattro(const Attribute& attr)
{
  return Solver::getattro(attr); 
}


int ForecastSolver::setattro(const Attribute& attr, const PythonObject& field)
{
  return Solver::setattro(attr, field);
}


} // end namespace
