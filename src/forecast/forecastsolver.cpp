/***************************************************************************
 *                                                                         *
 * Copyright (C) 2012-2015 by frePPLe bv                                   *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#include "forecast.h"

namespace frepple {

const MetaClass* ForecastSolver::metadata;
bool ForecastSolver::Customer_Then_Item_Hierarchy = true;
bool ForecastSolver::Match_Using_Delivery_Operation = true;
bool ForecastSolver::Net_Ignore_Location = false;
Duration ForecastSolver::Net_Late(0L);
Duration ForecastSolver::Net_Early(0L);
bool ForecastSolver::Net_PastDemand = false;
bool ForecastSolver::AverageNoDataDays = true;

const Keyword ForecastSolver::tag_DueWithinBucket("DueWithinBucket");
const Keyword ForecastSolver::tag_Net_CustomerThenItemHierarchy(
    "Net_CustomerThenItemHierarchy");
const Keyword ForecastSolver::tag_Net_MatchUsingDeliveryOperation(
    "Net_MatchUsingDeliveryOperation");
const Keyword ForecastSolver::tag_Net_NetEarly("Net_NetEarly");
const Keyword ForecastSolver::tag_Net_NetLate("Net_NetLate");
const Keyword ForecastSolver::tag_Net_PastDemand("Net_PastDemand");
const Keyword ForecastSolver::tag_AverageNoDataDays("AverageNoDataDays");
const Keyword ForecastSolver::tag_Net_IgnoreLocation("Net_IgnoreLocation");
const Keyword ForecastSolver::tag_Iterations("Iterations");
const Keyword ForecastSolver::tag_SmapeAlfa("SmapeAlfa");
const Keyword ForecastSolver::tag_Skip("Skip");
const Keyword ForecastSolver::tag_MovingAverage_order("MovingAverage_order");
const Keyword ForecastSolver::tag_SingleExponential_initialAlfa(
    "SingleExponential_initialAlfa");
const Keyword ForecastSolver::tag_SingleExponential_minAlfa(
    "SingleExponential_minAlfa");
const Keyword ForecastSolver::tag_SingleExponential_maxAlfa(
    "SingleExponential_maxAlfa");
const Keyword ForecastSolver::tag_DoubleExponential_initialAlfa(
    "DoubleExponential_initialAlfa");
const Keyword ForecastSolver::tag_DoubleExponential_minAlfa(
    "DoubleExponential_minAlfa");
const Keyword ForecastSolver::tag_DoubleExponential_maxAlfa(
    "DoubleExponential_maxAlfa");
const Keyword ForecastSolver::tag_DoubleExponential_initialGamma(
    "DoubleExponential_initialGamma");
const Keyword ForecastSolver::tag_DoubleExponential_minGamma(
    "DoubleExponential_minGamma");
const Keyword ForecastSolver::tag_DoubleExponential_maxGamma(
    "DoubleExponential_maxGamma");
const Keyword ForecastSolver::tag_DoubleExponential_dampenTrend(
    "DoubleExponential_dampenTrend");
const Keyword ForecastSolver::tag_Seasonal_initialAlfa("Seasonal_initialAlfa");
const Keyword ForecastSolver::tag_Seasonal_minAlfa("Seasonal_minAlfa");
const Keyword ForecastSolver::tag_Seasonal_maxAlfa("Seasonal_maxAlfa");
const Keyword ForecastSolver::tag_Seasonal_initialBeta("Seasonal_initialBeta");
const Keyword ForecastSolver::tag_Seasonal_minBeta("Seasonal_minBeta");
const Keyword ForecastSolver::tag_Seasonal_maxBeta("Seasonal_maxBeta");
const Keyword ForecastSolver::tag_Seasonal_gamma("Seasonal_gamma");
const Keyword ForecastSolver::tag_Seasonal_dampenTrend("Seasonal_dampenTrend");
const Keyword ForecastSolver::tag_Seasonal_minPeriod("Seasonal_minPeriod");
const Keyword ForecastSolver::tag_Seasonal_maxPeriod("Seasonal_maxPeriod");
const Keyword ForecastSolver::tag_Seasonal_minAutocorrelation(
    "Seasonal_minAutocorrelation");
const Keyword ForecastSolver::tag_Seasonal_maxAutocorrelation(
    "Seasonal_maxAutocorrelation");
const Keyword ForecastSolver::tag_Croston_initialAlfa("Croston_initialAlfa");
const Keyword ForecastSolver::tag_Croston_minAlfa("Croston_minAlfa");
const Keyword ForecastSolver::tag_Croston_maxAlfa("Croston_maxAlfa");
const Keyword ForecastSolver::tag_Croston_minIntermittence(
    "Croston_minIntermittence");
const Keyword ForecastSolver::tag_Croston_decayRate("Croston_decayRate");
const Keyword ForecastSolver::tag_Outlier_maxDeviation("Outlier_maxDeviation");
const Keyword ForecastSolver::tag_DeadAfterInactivity("DeadAfterInactivity");

int ForecastSolver::initialize() {
  // Initialize the smape weight array
  weight[0] = 1.0;
  for (int i = 0; i < MAXBUCKETS - 1; ++i)
    weight[i + 1] = weight[i] * Forecast_SmapeAlfa;

  // Initialize the metadata
  metadata = MetaClass::registerClass<ForecastSolver>(
      "solver", "solver_forecast", Object::create<ForecastSolver>);
  registerFields<ForecastSolver>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleClass<ForecastSolver, Solver>::getPythonType();
  x.setName("solver_forecast");
  x.setDoc("frePPLe solver_forecast");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("solve", solve, METH_VARARGS, "run the solver");
  x.addMethod("commit", commit, METH_NOARGS, "commit the plan changes");
  x.addMethod("rollback", rollback, METH_NOARGS, "rollback the plan changes");
  metadata->setPythonClass(x);
  return x.typeReady();
}

PyObject* ForecastSolver::create(PyTypeObject* pytype, PyObject* args,
                                 PyObject* kwds) {
  try {
    // Create the solver
    ForecastSolver* s = new ForecastSolver();

    // Iterate over extra keywords, and set attributes.   @todo move this
    // responsibility to the readers...
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    while (PyDict_Next(kwds, &pos, &key, &value)) {
      PythonData field(value);
      PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
      DataKeyword attr(PyBytes_AsString(key_utf8));
      Py_DECREF(key_utf8);
      const MetaFieldBase* fmeta = metadata->findField(attr.getHash());
      if (!fmeta) fmeta = Solver::metadata->findField(attr.getHash());
      if (fmeta)
        // Update the attribute
        fmeta->setField(s, field);
      else
        s->setProperty(attr.getName(), value);
    };

    // Return the object. The reference count doesn't need to be increased
    // as we do with other objects, because we want this object to be available
    // for the garbage collector of Python.
    return static_cast<PyObject*>(s);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

void ForecastSolver::solve(const Demand* l, void* v) {
  if (l->hasType<Forecast>())
    // Compute the baseline forecast
    computeBaselineForecast(static_cast<const Forecast*>(l));
  else {
    // Message
    if (getLogLevel() > 0)
      logger << "  Netting of demand '" << l << "'  ('" << l->getCustomer()
             << "', '" << l->getItem() << "', '" << l->getLocation() << "', '"
             << l->getDeliveryOperation() << "'): " << l->getDue() << ", "
             << l->getQuantity() << endl;

    // Find a matching forecast
    Forecast* fcst = matchDemandToForecast(l);

    if (!fcst) {
      // Message
      if (getLogLevel() > 0)
        logger << "    No matching forecast available" << endl;
      return;
    } else if (getLogLevel() > 0)
      logger << "    Matching forecast: " << fcst << endl;

    // Netting the order from the forecast
    netDemandFromForecast(l, fcst);
  }
}

PyObject* ForecastSolver::solve(PyObject* self, PyObject* args,
                                PyObject* kwargs) {
  static const char* kwlist[] = {"run_fcst", "cluster", "run_netting", "demand",
                                 nullptr};
  // Create the command
  int run_fcst = 1;
  int run_netting = 1;
  int cluster = -1;
  PyObject* dem = nullptr;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|pipO:solve",
                                   const_cast<char**>(kwlist), &run_fcst,
                                   &cluster, &run_netting, &dem))
    return nullptr;
  if (dem && !PyObject_TypeCheck(dem, Demand::metadata->pythonClass) &&
      !PyObject_TypeCheck(dem, Forecast::metadata->pythonClass)) {
    PyErr_SetString(PythonDataException,
                    "demand argument must be a demand or forecast");
    return nullptr;
  }

  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    auto sol = static_cast<ForecastSolver*>(self);
    if (!dem) {
      // Run for all or a single cluster
      sol->setAutocommit(true);
      sol->solve(run_fcst == 1, run_netting == 1, cluster);
    } else {
      // Run for a single forecast or run netting for a sales order
      sol->setAutocommit(false);
      sol->solve(static_cast<Demand*>(dem));
    }
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }

  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void ForecastSolver::solve(bool run_fcst, bool run_netting, int cluster) {
  // Switch to lazy cache flushing
  auto prevCachePolicy = Cache::instance->setWriteImmediately(false);

  // Reset forecastconsumed to 0 and forecastnet to forecasttotal.
  // When running for a cluster we reset the leafs and propagate.
  // When running globablly we can skip the propagation.
  for (auto& f : Forecast::getForecasts()) {
    if (cluster != -1 &&
        (!f->isLeaf() || static_cast<Forecast*>(&*f)->getCluster() != cluster))
      continue;
    auto fcstdata = f->getData();
    lock_guard<recursive_mutex> exclusive(fcstdata->lock);
    for (auto& bckt : fcstdata->getBuckets()) {
      if (bckt.getValue(*Measures::forecastconsumed))
        bckt.removeValue(cluster != -1, !getAutocommit() ? commands : nullptr,
                         Measures::forecastconsumed);
      auto fcsttotal = bckt.getValue(*Measures::forecasttotal);
      if (bckt.getEnd() < Plan::instance().getFcstCurrent() -
                              (ForecastSolver::getNetPastDemand()
                                   ? ForecastSolver::getNetLate()
                                   : Duration(0L)) ||
          !fcsttotal)
        bckt.removeValue(cluster != -1, !getAutocommit() ? commands : nullptr,
                         Measures::forecastnet);
      else
        bckt.setValue(cluster != -1, !getAutocommit() ? commands : nullptr,
                      Measures::forecastnet, fcsttotal);
    }
  }

  if (run_fcst) {
    // Time series forecasting for all leaf forecasts
    // TODO Assumes that the lowest forecasting level is a leaf forecast.
    if (getLogLevel() > 5)
      logger << "Start forecasting for leaf forecasts" << endl;
    for (auto& x : Forecast::getForecasts()) {
      try {
        if (x->getMethods() && x->isLeaf() &&
            (cluster == -1 ||
             static_cast<Forecast*>(&*x)->getCluster() == cluster))
          solve(static_cast<Forecast*>(&*x), nullptr);
      } catch (...) {
        logger << "Error: Caught an exception while forecasting '"
               << static_cast<Forecast*>(&*x) << "':" << endl;
        try {
          throw;
        } catch (const bad_exception&) {
          logger << "  bad exception" << endl;
        } catch (const exception& e) {
          logger << "  " << e.what() << endl;
        } catch (...) {
          logger << "  Unknown type" << endl;
        }
      }
    }
    if (getLogLevel() > 5)
      logger << "End forecasting for leaf forecasts" << endl;

    // Time series forecasting for all middle-out parent forecasts
    if (getLogLevel() > 5)
      logger << "Start forecasting for parent forecasts" << endl;
    for (auto& x : Forecast::getForecasts()) {
      try {
        if (x->getMethods() && !x->isLeaf() &&
            (cluster == -1 ||
             static_cast<Forecast*>(&*x)->getCluster() == cluster))
          solve(static_cast<Forecast*>(&*x), nullptr);
      } catch (...) {
        logger << "Error: Caught an exception while forecasting '"
               << static_cast<Forecast*>(&*x)->getName() << "':" << endl;
        try {
          throw;
        } catch (const bad_exception&) {
          logger << "  bad exception" << endl;
        } catch (const exception& e) {
          logger << "  " << e.what() << endl;
        } catch (...) {
          logger << "  Unknown type" << endl;
        }
      }
    }
    if (getLogLevel() > 5)
      logger << "End forecasting for parent forecasts" << endl;
  }

  if (run_netting) {
    // Sort the demands using the same sort function as used for planning.
    // Note: the memory consumption of the sorted list can be significant
    sortedDemandList l;
    for (auto& i : Demand::all())
      if (i.getType() != *Forecast::metadata &&
          i.getType() != *ForecastBucket::metadata &&
          i.getStatus() != Demand::STATUS_INQUIRY &&
          i.getStatus() != Demand::STATUS_CANCELED &&
          (cluster == -1 || i.getCluster() == cluster))
        l.insert(&i);

    // Forecast netting loop
    for (auto i : l) {
      try {
        solve(i, nullptr);
      } catch (...) {
        logger << "Error: Caught an exception while netting demand '"
               << i->getName() << "':" << endl;
        try {
          throw;
        } catch (const bad_exception&) {
          logger << "  bad exception" << endl;
        } catch (const exception& e) {
          logger << "  " << e.what() << endl;
        } catch (...) {
          logger << "  Unknown type" << endl;
        }
      }
    }
  }

  // Restore the previous caching policy
  Cache::instance->setWriteImmediately(prevCachePolicy);
}

Forecast* ForecastSolver::matchDemandToForecast(const Demand* l) {
  auto curItem = l->getItem();
  auto curCustomer = l->getCustomer();
  auto curLocation = l->getLocation();
  do  // Loop through third dimension
  {
    do  // Loop through second dimension
    {
      do  // Loop through first dimension
      {
        if (Net_Ignore_Location) {
          // Check for a match, ignoring the location dimension
          if (!curItem) return nullptr;
          auto dmds = curItem->getDemandIterator();
          while (auto dmd = dmds.next()) {
            if (dmd->hasType<Forecast>() && dmd->getCustomer() == curCustomer) {
              auto fcst = static_cast<Forecast*>(dmd);
              if (!fcst->isAggregate() && fcst->getPlanned())
                // Match found
                return fcst;
            }
          }
        } else {
          // Check for a item + location + customer match
          auto xb =
              Forecast::findForecast(curItem, curCustomer, curLocation, false);
          if (xb && !xb->isAggregate()) {
            auto x = static_cast<Forecast*>(xb);
            if (x->getPlanned() &&
                (!getMatchUsingDeliveryOperation() ||
                 x->getDeliveryOperation() == l->getDeliveryOperation()))
              // Match found
              return x;
          }
        }

        // Not found: try a higher level match in first dimension
        if (Customer_Then_Item_Hierarchy) {
          // First customer hierarchy
          if (curCustomer)
            curCustomer = curCustomer->getOwner();
          else
            break;
        } else {
          // First item hierarchy
          if (curItem)
            curItem = curItem->getOwner();
          else
            break;
        }
      } while (true);

      // Not found at any level in the first dimension

      // Try a new level in the second dimension
      if (Customer_Then_Item_Hierarchy) {
        // Second is item
        if (curItem)
          curItem = curItem->getOwner();
        else
          return nullptr;
        // Reset to lowest level in the first dimension again
        curCustomer = l->getCustomer();
      } else {
        // Second is customer
        if (curCustomer)
          curCustomer = curCustomer->getOwner();
        else
          return nullptr;
        // Reset to lowest level in the first dimension again
        curItem = l->getItem();
      }
    } while (true);

    // Try parent location
    if (curLocation)
      curLocation = curLocation->getOwner();
    else
      return nullptr;
    // Reset to lowest level in the first and second dimensions again
    curItem = l->getItem();
    curCustomer = l->getCustomer();
  } while (true);
}

void ForecastSolver::netDemandFromForecast(const Demand* dmd, Forecast* fcst) {
  // Check quantity to net
  double remaining = dmd->getQuantity();
  auto tmp = dmd->getDoubleProperty("quantity_to_net", -1.0);
  if (tmp >= 0) remaining = tmp;

  // Empty forecast model
  if (!fcst->isGroup()) {
    if (getLogLevel() > 1) logger << "    Empty forecast model" << endl;
    if (getLogLevel() > 0 && remaining)
      logger << "    Remains " << remaining << " that can't be netted" << endl;
    return;
  }

  // Load forecast data
  auto data = fcst->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);

  // Find the bucket with the due date
  auto zerobucket = data->getBuckets().begin();
  while (zerobucket != data->getBuckets().end()) {
    if (zerobucket->getDates().within(dmd->getDue())) break;
    ++zerobucket;
  }
  if (zerobucket == data->getBuckets().end())
    throw LogicException("Can't find forecast bucket for " +
                         string(dmd->getDue()) + " in forecast '" +
                         fcst->getName() + "'");

  Duration netLate = dmd->hasProperty("net_late")
                         ? Duration(dmd->getDoubleProperty("net_late") * 86400)
                         : getNetLate();
  if (zerobucket->getEnd() <=
      Plan::instance().getFcstCurrent() -
          (getNetPastDemand() ? netLate : Duration(0L))) {
    // The order is due in a bucket in the past.
    // Such orders shouldn't be considered for netting, as we can assume
    // they consumed from past buckets we're not concerned with any longer.
    if (getLogLevel() > 1)
      logger << "    Overdue order doesn't require netting" << endl;
    return;
  }

  // Netting - looking for time buckets with net forecast
  auto curbucket = zerobucket;
  bool backward = true;
  Duration netEarly =
      dmd->hasProperty("net_early")
          ? Duration(dmd->getDoubleProperty("net_early") * 86400)
          : getNetEarly();

  while (remaining > 0 && curbucket != data->getBuckets().end() &&
         (dmd->getDue() - netEarly < curbucket->getEnd()) &&
         (dmd->getDue() + netLate >= curbucket->getStart())) {
    // Net from the current bucket
    auto available = Measures::forecastnet->getValue(*curbucket);
    if (available > ROUNDING_ERROR) {
      if (available >= remaining) {
        // Partially consume a bucket
        if (getLogLevel() > 1)
          logger << "    Consuming " << remaining << " from bucket "
                 << curbucket->getDates() << " (" << available << " available)"
                 << endl;
        remaining = 0;
      } else {
        // Completely consume a bucket
        if (getLogLevel() > 1)
          logger << "    Consuming " << available << " from bucket "
                 << curbucket->getDates() << " (" << available << " available)"
                 << endl;
        remaining -= available;
      }
    } else if (getLogLevel() > 1)
      logger << "    Nothing available in bucket " << curbucket->getDates()
             << endl;

    // Find the next forecast bucket
    if (backward) {
      // Moving to earlier buckets
      if (curbucket == data->getBuckets().begin()) {
        // Switch from consuming earlier buckets to consuming later buckets
        backward = false;
        curbucket = zerobucket;
        ++curbucket;
      } else {
        --curbucket;
        if (curbucket->getEnd() <= dmd->getDue() - netEarly) {
          // Switch from consuming earlier buckets to consuming later buckets
          backward = false;
          curbucket = zerobucket;
          ++curbucket;
        }
      }
    } else
      // Moving to later buckets
      ++curbucket;
  }

  // Quantity for which no bucket is found
  if (remaining > 0 && getLogLevel() > 0)
    logger << "    Remains " << remaining << " that can't be netted" << endl;
}

PyObject* ForecastSolver::commit(PyObject* self, PyObject* args) {
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    static_cast<ForecastSolver*>(self)->commands->commit();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

PyObject* ForecastSolver::rollback(PyObject* self, PyObject* args) {
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    static_cast<ForecastSolver*>(self)->commands->rollback();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

}  // namespace frepple
