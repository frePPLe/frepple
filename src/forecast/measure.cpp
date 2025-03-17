/***************************************************************************
 *                                                                         *
 * Copyright (C) 2019 by frePPLe bv                                        *
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

template <class ForecastMeasure>
Tree utils::HasName<ForecastMeasure>::st;
const MetaCategory* ForecastMeasure::metadata;
const MetaClass* ForecastMeasureAggregated::metadata;
const MetaClass* ForecastMeasureAggregatedPlanned::metadata;
const MetaClass* ForecastMeasureLocal::metadata;
const MetaClass* ForecastMeasureComputed::metadata;
const MetaClass* ForecastMeasureComputedPlanned::metadata;
const MetaClass* ForecastMeasureTemp::metadata;
const Keyword ForecastMeasureAggregated::tag_overrides("overrides");

const ForecastMeasureComputed* Measures::forecasttotal = nullptr;
const ForecastMeasureAggregatedPlanned* Measures::forecastnet = nullptr;
const ForecastMeasureAggregatedPlanned* Measures::forecastconsumed = nullptr;
const ForecastMeasureAggregated* Measures::forecastbaseline = nullptr;
const ForecastMeasureAggregated* Measures::forecastoverride = nullptr;
const ForecastMeasureAggregated* Measures::orderstotal = nullptr;
const ForecastMeasureAggregated* Measures::ordersadjustment = nullptr;
const ForecastMeasureAggregated* Measures::ordersopen = nullptr;
const ForecastMeasureAggregatedPlanned* Measures::forecastplanned = nullptr;
const ForecastMeasureAggregated* Measures::ordersplanned = nullptr;
const ForecastMeasureLocal* Measures::outlier = nullptr;
const ForecastMeasureLocal* Measures::nodata = nullptr;
const ForecastMeasureLocal* Measures::leaf = nullptr;

MeasurePagePool MeasurePagePool::measurepages_default("default");
MeasurePagePool MeasurePagePool::measurepages_temp("temp");

int ForecastMeasure::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<ForecastMeasure>(
      "measure", "measuress", reader, finder);
  registerFields<ForecastMeasure>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<ForecastMeasure>::initialize();
}

int ForecastMeasureAggregated::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<ForecastMeasureAggregated>(
      "measure", "measure_aggregated",
      Object::create<ForecastMeasureAggregated>, true);

  // Initialize the Python class
  return FreppleClass<ForecastMeasureAggregated, ForecastMeasure>::initialize();
}

int ForecastMeasureAggregatedPlanned::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<ForecastMeasureAggregatedPlanned>(
      "measure", "measure_aggregatedplanned",
      Object::create<ForecastMeasureAggregatedPlanned>);

  // Initialize the Python class
  return FreppleClass<ForecastMeasureAggregatedPlanned,
                      ForecastMeasure>::initialize();
}

int ForecastMeasureLocal::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<ForecastMeasureLocal>(
      "measure", "measure_local", Object::create<ForecastMeasureLocal>);

  // Initialize the Python class
  return FreppleClass<ForecastMeasureLocal, ForecastMeasure>::initialize();
}

int ForecastMeasureTemp::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<ForecastMeasureTemp>(
      "measure", "measure_temp", Object::create<ForecastMeasureTemp>);

  // Initialize the Python class
  return FreppleClass<ForecastMeasureTemp, ForecastMeasure>::initialize();
}

bool ForecastMeasure::isLeaf(const ForecastBase* f) const {
  // Leaf level is the lowest forecast level by default
  return f->isLeaf();
}

bool ForecastMeasureAggregatedPlanned::isLeaf(const ForecastBase* f) const {
  // Planned measures are stored from the planned forecast upwards
  return f->getPlanned();
}

bool ForecastMeasureComputedPlanned::isLeaf(const ForecastBase* f) const {
  // Planned measures are stored from the planned forecast upwards
  return f->getPlanned();
}

bool ForecastMeasureLocal::isLeaf(const ForecastBase* f) const {
  // Local measures consider all nodes as leafs
  return true;
}

void ForecastMeasure::aggregateMeasures(bool include_planned) {
  vector<ForecastMeasure*> msrs;
  for (auto& msr : ForecastMeasure::all()) {
    if (!msr.isAggregate()) continue;
    if (include_planned ||
        (msr.getName() != Measures::forecastplanned->getName() &&
         msr.getName() != Measures::ordersplanned->getName()))
      msrs.push_back(&msr);
  }
  aggregateMeasures(msrs);
}

void ForecastMeasure::aggregateMeasures(const vector<ForecastMeasure*>& msrs) {
  // Flush dirty entries and switch to lazy mode
  Cache::instance->flush();
  auto prev = Cache::instance->setWriteImmediately(false);

  // Activate all parent forecasts.
  // Validate the planned flag while we are looping.
  {
    // We need to make a copy because the forecast container is
    // getting updating during the loop.
    vector<ForecastBase*> tmp;
    for (auto fcst : Forecast::getForecasts()) tmp.push_back(fcst);
    for (auto& fcst : tmp) {
      auto planned = fcst->getPlanned();
      for (auto p = fcst->getParents(); p; ++p) {
        if (planned && p->getPlanned()) {
          static_cast<Forecast*>(fcst)->setPlanned(false);
          planned = false;
          logger << static_cast<Forecast*>(fcst)
                 << " can't be planned because its parent is already planned"
                 << endl;
        }
      }
    }
  }

  // Create temp measures
  vector<pair<ForecastMeasure*, ForecastMeasureTemp*> > msrlist;
  for (auto msr : msrs) {
    if (!msr->isAggregate()) continue;
    auto tmpmsr = new ForecastMeasureTemp(*msr);
    msrlist.emplace_back(&*msr, tmpmsr);
    if (msr->getDefault() == -1.0)
      // Disable override aggregation logic on the temp measure
      msrlist.back().second->setDefault(0.0);
  }

  // Propagate the leave value as a temporary measure
  for (auto fcst : Forecast::getForecasts()) {
    shared_ptr<ForecastData> fcstdata(nullptr);
    for (auto& msr : msrlist)
      if (msr.first->isLeaf(&*fcst)) {
        if (!fcstdata) {
          fcstdata = fcst->getData();
          fcstdata->lock.lock();
        }
        for (auto& bckt : fcstdata->getBuckets()) {
          auto val = msr.first->getValue(bckt);
          if (val != msr.first->getDefault()) {
            bckt.propagateValue(msr.second, val);
          }
        }
      }
    if (fcstdata) fcstdata->lock.unlock();
  }

  // Verify the correctness of the aggregation results
  unsigned long updated = 0;
  for (auto fcst : Forecast::getForecasts()) {
    shared_ptr<ForecastData> fcstdata(nullptr);
    for (auto& msr : msrlist)
      if (!msr.first->isLeaf(&*fcst)) {
        if (!fcstdata) {
          fcstdata = fcst->getData();
          fcstdata->lock.lock();
        }
        for (auto& bckt : fcstdata->getBuckets()) {
          // Compare the aggregate value with the existing value
          auto val = msr.second->getValueAndFound(bckt);
          auto cur = msr.first->getValue(bckt);
          if (fabs(cur - val.first) > ROUNDING_ERROR &&
              (msr.first->getDefault() != -1.0 || val.second)) {
            if (!bckt.isDirty()) ++updated;
            if (Cache::instance->getLogLevel() > 2)
              logger << "Correcting " << msr.first << ": found " << cur
                     << " but expected " << val.first << " on " << bckt << endl;
            bckt.setValue(false, nullptr, msr.first, val.first);
          }
          bckt.removeValue(false, nullptr, msr.second);
        }
      }
    if (fcstdata) fcstdata->lock.unlock();
  }

  // Delete temp measures
  for (auto& msr : msrlist) delete msr.second;

  logger << "Corrected " << updated << " parent forecast buckets" << endl;
  Cache::instance->setWriteImmediately(prev);
}

void ForecastMeasure::computeMeasures() {
  vector<ForecastMeasure*> msrs;
  for (auto& msr : ForecastMeasure::all()) {
    if (msr.isComputed()) msrs.push_back(&msr);
  }
  computeMeasures(msrs);
}

void ForecastMeasure::computeMeasures(const vector<ForecastMeasure*>& msrs) {
  // Flush dirty entries and switch to lazy mode
  Cache::instance->flush();
  auto prev = Cache::instance->setWriteImmediately(false);

  for (auto& m : msrs) resetMeasure(ALL, m);

  // Recompute all leave forecasts
  for (auto fcst : Forecast::getForecasts()) {
    shared_ptr<ForecastData> fcstdata(nullptr);
    for (auto& msr : msrs)
      if (msr->isLeaf(&*fcst) && msr->isComputed()) {
        if (!fcstdata) {
          fcstdata = fcst->getData();
          fcstdata->lock.lock();
        }
        for (auto& bckt : fcstdata->getBuckets()) {
          // Initialize symbol table
          for (auto m = begin(); m != end(); ++m)
            m->expressionvalue = bckt.getValue(*m);
          ForecastMeasureComputed::cost =
              bckt.getForecast()->getForecastItem()->getCost();
          auto val = static_cast<ForecastMeasureComputed*>(msr)->compute();
          if (val != bckt.getValue(*msr)) {
            if (val == msr->getDefault())
              bckt.removeValue(true, nullptr, msr);
            else
              bckt.setValue(true, nullptr, msr, val);
          }
        }
      }
    if (fcstdata) fcstdata->lock.unlock();
  }

  Cache::instance->setWriteImmediately(prev);
}

PyObject* ForecastMeasure::updatePlannedForecastPython(PyObject* self,
                                                       PyObject* args) {
  // Switch on lazy writes
  auto prev = Cache::instance->setWriteImmediately(false);

  Py_BEGIN_ALLOW_THREADS;
  try {
    // Reset to 0
    resetMeasure(ALL, Measures::ordersplanned, Measures::forecastplanned);

    // Set the value on all leaf nodes
    for (auto fcst : Forecast::getForecasts()) {
      auto fcstdata = fcst->getData();
      lock_guard<recursive_mutex> exclusive(fcstdata->lock);
      for (auto& bckt : fcstdata->getBuckets()) {
        auto tmp = bckt.getOrdersPlanned();
        if (tmp) Measures::ordersplanned->update(bckt, tmp);
        tmp = bckt.getForecastPlanned();
        if (tmp) Measures::forecastplanned->update(bckt, tmp);
      }
    }
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    Cache::instance->setWriteImmediately(prev);
    return nullptr;
  }
  Py_END_ALLOW_THREADS;

  // Restore the previous cache policy
  Cache::instance->setWriteImmediately(prev);

  return Py_BuildValue("");
}

template <>
void ForecastBucketData::setValue(bool propagate, CommandManager* mgr,
                                  const ForecastMeasure* key, double val) {
  if (!key) return;
  if (key == Measures::forecastnet &&
      getEnd() > Plan::instance().getFcstCurrent()) {
    // This is the connection between the supply chain and the forecast
    // data structures
    if (getForecast()->getPlanned()) {
      auto b1 = getForecastBucket();
      if (val || b1) {
        auto tmp = getOrCreateForecastBucket();
        auto current_quantity = tmp->getQuantity();
        if (current_quantity > val + ROUNDING_ERROR)
          tmp->reduceDeliveries(current_quantity - val, mgr);
        tmp->setQuantity(val);
      }
    } else {
      auto b1 = getForecastBucket();
      if (b1) b1->setQuantity(0.0);
    }
  }

  auto t = measures.find(key->getHashedName());
  if (!t) {
    if (val != key->getDefault()) {
      // New non-empty key
      measures.insert(key->getHashedName(), val, false);
      if (propagate && key->isAggregate()) {
        auto index = getIndex();
        for (auto p = getForecast()->getParents(); p; ++p) {
          auto parentfcstdata = p->getData();
          lock_guard<recursive_mutex> exclusive(parentfcstdata->lock);
          parentfcstdata->getBuckets()[index].incValue(false, mgr, key, val);
        }
      }
      if (!key->isTemporary()) markDirty();
    }
  } else {
    auto delta = val - t->getValue();
    if (fabs(delta) > ROUNDING_ERROR || key->getDefault()) {
      if (val != key->getDefault())
        // Updating an existing key
        t->setValue(val);
      else
        // Existing key becomes equal to default and is removed
        measures.erase(t);
      if (propagate && key->isAggregate()) {
        auto index = getIndex();
        for (auto p = getForecast()->getParents(); p; ++p) {
          auto parentfcstdata = p->getData();
          lock_guard<recursive_mutex> exclusive(parentfcstdata->lock);
          parentfcstdata->getBuckets()[index].incValue(false, mgr, key, delta);
        }
      }
      if (!key->isTemporary()) markDirty();
    }
  }
}

void ForecastBucketData::propagateValue(const ForecastMeasure* key,
                                        double val) {
  if (!key || !key->isAggregate() || !val) return;
  auto index = getIndex();
  for (auto p = getForecast()->getParents(); p; ++p) {
    auto parentfcstdata = p->getData();
    lock_guard<recursive_mutex> exclusive(parentfcstdata->lock);
    parentfcstdata->getBuckets()[index].incValue(false, nullptr, key, val);
  }
}

template <>
void ForecastBucketData::incValue(bool propagate, CommandManager* mgr,
                                  const ForecastMeasure* key, double val) {
  if (!key || (!val && !key->getDefault())) return;
  if (key == Measures::forecastnet &&
      getEnd() > Plan::instance().getFcstCurrent()) {
    // This is the connection between the supply chain and the forecast
    // data structures
    if (getForecast()->getPlanned()) {
      auto b1 = getForecastBucket();
      if ((b1 ? b1->getQuantity() + val : val) || b1) {
        auto tmp = getOrCreateForecastBucket();
        tmp->setQuantity(tmp->getQuantity() + val);
      }
    } else {
      auto b1 = getForecastBucket();
      if (b1) b1->setQuantity(0.0);
    }
  }

  // Increment locally
  auto t = measures.find(key->getHashedName());
  if (!t) {
    // Inserting a new key
    if (val != key->getDefault())
      // New non-empty key
      measures.insert(key->getHashedName(), val, false);
  } else {
    auto tmp = t->getValue() + val;
    if (key->getDefault() == -1.0 && fabs(tmp) < ROUNDING_ERROR)
      // Special case for override measures
      validateOverride(key);
    else if (fabs(tmp - key->getDefault()) > ROUNDING_ERROR)
      // Updating an existing key
      t->setValue(tmp);
    else
      // Existing key becomes equal to default and is removed
      measures.erase(t);
  }

  // Increment parents
  if (key->isAggregate() && propagate) {
    auto index = getIndex();
    for (auto p = getForecast()->getParents(); p; ++p) {
      auto parentfcstdata = p->getData();
      lock_guard<recursive_mutex> exclusive(parentfcstdata->lock);
      parentfcstdata->getBuckets()[index].incValue(false, mgr, key, val);
    }
  }

  // Mark dirty
  if (!key->isTemporary()) markDirty();
}

template <>
void ForecastBucketData::removeValue(bool propagate, CommandManager* mgr,
                                     const ForecastMeasure* key) {
  if (!key) return;
  auto t = measures.find(key->getHashedName());
  if (!t) return;
  auto val = t->getValue();
  measures.erase(t);

  if (key->isLeaf(getForecast())) {
    key->computeDependentMeasures(*this);
    if (propagate) {
      auto index = getIndex();
      for (auto p = getForecast()->getParents(); p; ++p) {
        auto pdata = p->getData();
        lock_guard<recursive_mutex> exclusive(pdata->lock);
        pdata->getBuckets()[index].incValue(false, mgr, key, -val);
      }
    }
  }
  if (!key->isTemporary()) markDirty();
}

PyObject* ForecastMeasure::aggregateMeasuresPython(PyObject* self,
                                                   PyObject* args,
                                                   PyObject* kwargs) {
  static const char* kwlist[] = {"includeplanned", "measures", nullptr};
  int include_planned = 0;
  PyObject* py_msrs = nullptr;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|pO:aggregateMeasures",
                                   const_cast<char**>(kwlist), &include_planned,
                                   &py_msrs))
    return nullptr;

  vector<ForecastMeasure*> msrs;
  if (py_msrs) {
    PyObject* py_iter = PyObject_GetIter(py_msrs);
    PyObject* py_msr;
    if (!py_iter) throw DataException("Object not iterable");
    while ((py_msr = PyIter_Next(py_iter))) {
      string msrname = PythonData(py_msr).getString();
      auto msr = ForecastMeasure::find(msrname);
      if (msr)
        msrs.push_back(msr);
      else
        throw DataException("Measure not found");
      Py_DECREF(py_msr);
    }
    Py_DECREF(py_iter);
  }

  Py_BEGIN_ALLOW_THREADS;
  try {
    if (py_msrs)
      aggregateMeasures(msrs);
    else
      aggregateMeasures(include_planned != 0);
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

PyObject* ForecastMeasure::computeMeasuresPython(PyObject* self, PyObject* args,
                                                 PyObject* kwargs) {
  static const char* kwlist[] = {"measures", nullptr};
  PyObject* py_msrs = nullptr;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O:computeMeasures",
                                   const_cast<char**>(kwlist), &py_msrs))
    return nullptr;

  vector<ForecastMeasure*> msrs;
  if (py_msrs) {
    PyObject* py_iter = PyObject_GetIter(py_msrs);
    PyObject* py_msr;
    if (!py_iter) throw DataException("Object not iterable");
    while ((py_msr = PyIter_Next(py_iter))) {
      string msrname = PythonData(py_msr).getString();
      auto msr = ForecastMeasure::find(msrname);
      if (msr)
        msrs.push_back(msr);
      else
        throw DataException("Measure not found");
      Py_DECREF(py_msr);
    }
    Py_DECREF(py_iter);
  }

  Py_BEGIN_ALLOW_THREADS;
  try {
    if (py_msrs)
      computeMeasures(msrs);
    else
      computeMeasures();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

PyObject* ForecastMeasure::resetMeasuresPython(PyObject* self, PyObject* args) {
  const char* pymeasure1 = nullptr;
  const char* pymeasure2 = nullptr;
  const char* pymeasure3 = nullptr;
  const char* pymeasure4 = nullptr;
  short int mode;
  if (!PyArg_ParseTuple(args, "hs|sss:resetmeasures", &mode, &pymeasure1,
                        &pymeasure2, &pymeasure3, &pymeasure4))
    return nullptr;

  Py_BEGIN_ALLOW_THREADS;
  try {
    if (pymeasure4)
      resetMeasure(mode, ForecastMeasure::find(pymeasure1),
                   ForecastMeasure::find(pymeasure2),
                   ForecastMeasure::find(pymeasure3),
                   ForecastMeasure::find(pymeasure4));
    else if (pymeasure3)
      resetMeasure(mode, ForecastMeasure::find(pymeasure1),
                   ForecastMeasure::find(pymeasure2),
                   ForecastMeasure::find(pymeasure3));
    else if (pymeasure2)
      resetMeasure(mode, ForecastMeasure::find(pymeasure1),
                   ForecastMeasure::find(pymeasure2));
    else
      resetMeasure(mode, ForecastMeasure::find(pymeasure1));
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

double ForecastMeasureAggregated::disaggregate(ForecastBucketData& bckt,
                                               double val, bool multiply,
                                               double remainder,
                                               CommandManager* mgr) const {
  if (override_measure)
    // Special logic for overriding another measure
    return disaggregateOverride(bckt, val, multiply, remainder, mgr);

  // Get the current value of this node
  auto fcst = bckt.getForecast();
  auto fcstdata = fcst->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);

  if (isLeaf(fcst))
    //  Handling of leaf forecasts
    remainder = update(fcstdata->getBuckets()[bckt.getIndex()], val, mgr);
  else {
    // Handling of parent forecasts
    auto currentvalue = getValue(fcstdata->getBuckets()[bckt.getIndex()]);
    if (currentvalue) {
      // Proportionally scale all child forecasts
      double factor = val / currentvalue;
      for (auto ch = fcst->getLeaves(false, this); ch; ++ch)
        remainder = disaggregate(*ch, bckt.getStart(), bckt.getEnd(), factor,
                                 true, remainder, mgr);
    } else {
      // Equal distribution of all child forecasts
      unsigned int cnt = 0;
      for (auto ch = fcst->getLeaves(false, this); ch; ++ch) ++cnt;
      if (!cnt)
        logger << " no child forecast found to update for "
               << fcst->getForecastItem() << " / "
               << fcst->getForecastLocation() << " / "
               << fcst->getForecastCustomer() << endl;
      else {
        auto delta = val / cnt;
        for (auto p = fcst->getLeaves(false, this); p; ++p)
          remainder = disaggregate(*p, bckt.getStart(), bckt.getEnd(),
                                   delta + remainder, false, 0.0, mgr);
      }
    }
  }
  return remainder;
}

double ForecastMeasureAggregated::disaggregate(ForecastBase* fcst,
                                               Date startdate, Date enddate,
                                               double val, bool multiply,
                                               double remainder,
                                               CommandManager* mgr) const {
  if (override_measure)
    // Special logic for overriding another measure
    return disaggregateOverride(fcst, startdate, enddate, val, multiply,
                                remainder, mgr);

  // Get the current value of this node
  auto fcstdata = fcst->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  double currentvalue = 0.0;
  unsigned int cnt = 0;
  if (!multiply)
    for (auto& bckt : fcstdata->getBuckets()) {
      if (bckt.getStart() > enddate) break;
      if ((bckt.getStart() >= startdate && bckt.getStart() < enddate) ||
          (bckt.getDates().within(startdate) &&
           bckt.getDates().between(enddate))) {
        currentvalue += getValue(bckt);
        ++cnt;
      }
    }

  // TODO the leaf and parent logic can be combined
  if (isLeaf(fcst)) {
    //  Handling of leaf forecasts
    if (multiply || currentvalue) {
      if (!multiply) val /= currentvalue;
      // Proportionally scale all buckets
      for (auto& bckt : fcstdata->getBuckets()) {
        if (bckt.getStart() > enddate) break;
        if ((bckt.getStart() >= startdate && bckt.getStart() < enddate) ||
            (bckt.getDates().within(startdate) &&
             bckt.getDates().between(enddate)))
          remainder = update(bckt, getValue(bckt) * val + remainder, mgr);
      }
    } else {
      // Equally distribute over all buckets
      if (multiply) logger << "ignoring multiply flag" << endl;
      if (!cnt)
        logger << " no child forecast found to update for "
               << fcst->getForecastItem() << " / "
               << fcst->getForecastLocation() << " / "
               << fcst->getForecastCustomer() << endl;
      else {
        auto newval = val / cnt;
        for (auto& bckt : fcstdata->getBuckets()) {
          if (bckt.getStart() > enddate) break;
          if ((bckt.getStart() >= startdate && bckt.getStart() < enddate) ||
              (bckt.getDates().within(startdate) &&
               bckt.getDates().between(enddate)))
            remainder = update(bckt, newval + remainder, mgr);
        }
      }
    }
  } else {
    // Handling of parent forecasts
    if (currentvalue) {
      // Proportionally scale all child forecasts
      double factor = val / currentvalue;
      for (auto ch = fcst->getLeaves(false, this); ch; ++ch)
        remainder =
            disaggregate(*ch, startdate, enddate, factor, true, remainder, mgr);
    } else {
      // Equal distribution of all child forecasts
      unsigned int cnt = 0;
      for (auto ch = fcst->getLeaves(false, this); ch; ++ch) ++cnt;
      if (!cnt)
        logger << " no child forecast found to update for "
               << fcst->getForecastItem() << " / "
               << fcst->getForecastLocation() << " / "
               << fcst->getForecastCustomer() << endl;
      else {
        auto delta = val / cnt;
        for (auto p = fcst->getLeaves(false, this); p; ++p)
          remainder = disaggregate(*p, startdate, enddate, delta + remainder,
                                   false, 0, mgr);
      }
    }
  }
  return remainder;
}

double ForecastMeasureAggregated::disaggregateOverride(
    ForecastBucketData& bckt, double val, bool multiply, double remainder,
    CommandManager* mgr) const {
  // Get the current value of this node
  auto fcst = bckt.getForecast();
  auto fcstdata = fcst->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  auto& fcstbcktdata = fcstdata->getBuckets()[bckt.getIndex()];

  // Get status
  unsigned int count_override = 0;
  unsigned int count_no_override = 0;
  auto current_override = getValue(fcstbcktdata);
  auto current_base = override_measure->getValue(fcstbcktdata);
  double current_total;
  if (current_override != -1.0) {
    count_override = 1;
    current_total = current_override;
  } else {
    current_override = 0.0;
    count_no_override = 1;
    current_total = current_base;
  }

  // Select the update mode
  short mode;
  double arg;
  if (val <= -1.0) {
    // Mode 0: Remove the overrides on the children
    mode = 0;
    arg = -1.0;
  } else if (count_override) {
    if (current_override > val ||
        fabs(current_override - current_total) < ROUNDING_ERROR) {
      if (current_override) {
        // Mode 1: scale the existing overrides and set others expliclitly to
        // 0.
        mode = 1;
        arg = val / current_override;
      } else {
        // Mode 11: Distribute equally over all overrides
        mode = 11;
        arg = val / count_override;
      }
    } else {
      if (current_total) {
        // Scale non-overriden values to sum up correctly.
        // Existing overridden values are left untouched.
        mode = 3;
        arg = val / current_total;
      } else {
        // Mode 4: Set non-overridden values
        mode = 4;
        arg = val / count_no_override;
      }
    }
  } else if (current_base) {
    // Mode 3: Scale all existing records proportional to the base.
    mode = 3;
    arg = val / current_base;
  } else if (count_no_override) {
    // Mode 4: Divide the quantity evenly over all existing leafs.
    mode = 4;
    arg = val / count_no_override;
  } else {
    logger << "no children found!!!!" << endl;
    return remainder;
  }
  for (auto ch = fcst->getLeaves(true, this); ch; ++ch) {
    auto childfcstdata = ch->getData();
    lock_guard<recursive_mutex> exclusive(childfcstdata->lock);
    auto& childfcstbcktdata = childfcstdata->getBuckets()[bckt.getIndex()];

    switch (mode) {
      case 0:
        // Remove the current override
        remainder = update(childfcstbcktdata, -1, mgr);
        break;
      case 1: {
        // Scale existing overrides and set non-overriden to 0
        auto c = getValue(childfcstbcktdata);
        remainder = update(childfcstbcktdata,
                           c == -1.0 ? 0.0 : c * arg + remainder, mgr);
        break;
      }
      case 11: {
        // Set overridden
        remainder = update(childfcstbcktdata, arg + remainder, mgr);
        break;
      }
      case 3: {
        // Scale non-overriden
        auto o = getValue(childfcstbcktdata);
        if (o == -1.0) {
          auto c = override_measure->getValue(childfcstbcktdata);
          remainder = update(childfcstbcktdata, c * arg + remainder, mgr);
        }
        break;
      }
      case 4: {
        // Set non-overriden
        auto o = getValue(childfcstbcktdata);
        if (o == -1.0)
          remainder = update(childfcstbcktdata, arg + remainder, mgr);
        break;
      }
      default:
        throw LogicException("Unkown mode");
    }
  }
  return remainder;
}

double ForecastMeasureAggregated::disaggregateOverride(
    ForecastBase* fcst, Date startdate, Date enddate, double val, bool multiply,
    double remainder, CommandManager* mgr) const {
  // Get the current status
  double current_base = 0.0;
  double current_override = 0.0;
  double current_no_override = 0.0;
  double current_total = 0.0;
  unsigned int count_override = 0;
  unsigned int count_no_override = 0;
  unsigned int cnt = 0;
  {
    auto fcstdata = fcst->getData();
    lock_guard<recursive_mutex> exclusive(fcstdata->lock);
    for (auto bckt = fcstdata->getBuckets().begin();; ++bckt) {
      if (bckt == fcstdata->getBuckets().end() || bckt->getStart() > enddate)
        break;
      if ((bckt->getStart() >= startdate && bckt->getStart() < enddate) ||
          (bckt->getDates().within(startdate) &&
           bckt->getDates().between(enddate))) {
        for (auto ch = fcst->getLeaves(true, this); ch; ++ch) {
          auto childfcstdata = ch->getData();
          lock_guard<recursive_mutex> exclusive(childfcstdata->lock);
          auto tmp = getValue(childfcstdata->getBuckets()[bckt->getIndex()]);
          auto base = override_measure->getValue(
              childfcstdata->getBuckets()[bckt->getIndex()]);
          current_base += base;
          if (tmp != -1.0) {
            current_total += tmp;
            current_override += tmp;
            ++count_override;
          } else {
            current_total += base;
            current_no_override += base;
            ++count_no_override;
          }
          ++cnt;
        }
      }
    }
  }

  // Select the update mode
  short mode;
  double arg;
  if (val <= -1.0) {
    // Mode 0: Remove the overrides on the children
    mode = 0;
    arg = -1.0;
  } else if (count_override) {
    // Some overrides already exist
    if (current_override > val || !count_no_override) {
      // Scale existing overrides
      if (current_override) {
        // Mode 1: scale the existing overrides and set others expliclitly to
        // 0.
        mode = 1;
        arg = val / current_override;
      } else {
        // Mode 11: Distribute equally over all overrides
        mode = 11;
        arg = val / count_override;
      }
    } else {
      // Update non-overriden entries
      if (current_no_override) {
        // Scale non-overriden values to sum up correctly.
        // Existing overridden values are left untouched.
        mode = 3;
        arg = (val - current_override) / current_no_override;
      } else {
        // Mode 4: Set non-overridden values
        mode = 4;
        arg = (val - current_override) / count_no_override;
      }
    }
  } else if (current_base) {
    // Mode 3: Scale all existing records proportional to the base.
    mode = 3;
    arg = val / current_base;
  } else if (count_no_override) {
    // Mode 4: Divide the quantity evenly over all existing leafs.
    mode = 4;
    arg = val / count_no_override;
  } else
    return remainder;

  for (auto ch = fcst->getLeaves(true, this); ch; ++ch) {
    auto childfcstdata = ch->getData();
    lock_guard<recursive_mutex> exclusive(childfcstdata->lock);
    for (auto& bckt : childfcstdata->getBuckets()) {
      if (bckt.getStart() > enddate) break;
      if ((bckt.getStart() >= startdate && bckt.getStart() < enddate) ||
          (bckt.getDates().within(startdate) &&
           bckt.getDates().between(enddate)))
        switch (mode) {
          case 0:
            // Remove the current override
            remainder = update(bckt, -1, mgr);
            break;
          case 1: {
            // Scale existing overrides and set non-overriden to 0
            auto c = getValue(bckt);
            remainder =
                update(bckt, c == -1.0 ? 0.0 : c * arg + remainder, mgr);
            break;
          }
          case 11: {
            // Set existing overrides
            auto c = getValue(bckt);
            remainder = update(bckt, c == -1.0 ? 0.0 : arg + remainder, mgr);
            break;
          }
          case 3: {
            // Scale non-overriden
            auto o = getValue(bckt);
            if (o == -1.0) {
              auto c = override_measure->getValue(bckt);
              remainder = update(bckt, c * arg + remainder, mgr);
            }
            break;
          }
          case 4: {
            // Set non-overriden
            auto o = getValue(bckt);
            if (o == -1.0) remainder = update(bckt, arg + remainder, mgr);
          } break;
          default:
            throw LogicException("Unkown mode");
        }
    }
  }
  return remainder;
}

double ForecastMeasureLocal::disaggregate(ForecastBucketData& bckt, double val,
                                          bool multiply, double remainder,
                                          CommandManager* mgr) const {
  auto fcstdata = bckt.getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  auto& fcsbcktdata = fcstdata->getBuckets()[bckt.getIndex()];
  if (multiply)
    return update(fcsbcktdata, val * getValue(fcsbcktdata) + remainder, mgr);
  else
    return update(fcsbcktdata, val + remainder, mgr);
}

double ForecastMeasureLocal::disaggregate(ForecastBase* fcst, Date startdate,
                                          Date enddate, double val,
                                          bool multiply, double remainder,
                                          CommandManager* mgr) const {
  auto fcstdata = fcst->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  for (auto& bckt : fcstdata->getBuckets()) {
    if (bckt.getStart() > enddate) break;
    if ((bckt.getStart() >= startdate && bckt.getStart() < enddate) ||
        (bckt.getDates().within(startdate) &&
         bckt.getDates().between(enddate))) {
      if (multiply)
        remainder = update(bckt, getValue(bckt) * val + remainder, mgr);
      else
        remainder = update(bckt, val + remainder, mgr);
    }
  }
  return remainder;
}

double ForecastMeasure::update(ForecastBucketData& fcstdata, double val,
                               CommandManager* mgr) const {
  // TODO use a single setvalue call with multiple arguments to avoid
  // iterating many times over the parents
  auto fcst = fcstdata.getForecast();
  auto fdata = fcst->getData();
  lock_guard<recursive_mutex> exclusive(fdata->lock);
  double remainder = 0.0;
  bool initialized = false;

  // Create a command to be able to undo the change later
  if (mgr) mgr->add(new CommandSetForecastData(&fcstdata, this, val));

  // FORECAST BASELINE
  if (this == Measures::forecastbaseline) {
    double qty;
    if (fcst->getDiscrete()) {
      qty = floor(val + ROUNDING_ERROR);
      remainder = val - qty;
    } else
      qty = val;
    fcstdata.setValue(true, mgr, Measures::forecastbaseline, qty);
  }
  // FORECAST OVERRIDE
  else if (this == Measures::forecastoverride) {
    if (val == -1)
      // TODO We shouldn't need this special case. However a unit test fails
      // if we remove it. Looks like removevalue and setvalue do something
      // different somewhere.
      fcstdata.removeValue(true, mgr, Measures::forecastoverride);
    else {
      double qty;
      if (fcst->getDiscrete()) {
        qty = floor(val + ROUNDING_ERROR);
        remainder = val - qty;
      } else
        qty = val;
      fcstdata.setValue(true, mgr, Measures::forecastoverride, qty);
    }
  }
  // FORECAST CONSUMED
  else if (this == Measures::forecastconsumed) {
    fcstdata.setValue(true, nullptr, Measures::forecastconsumed, val);
    auto new_net = Measures::forecasttotal->getValue(fcstdata) - val;
    Measures::forecastnet->update(fcstdata, new_net, mgr);
  }
  // UPDATING A COMPUTED MEASURES
  else if (hasType<ForecastMeasureComputed>()) {
    auto me = static_cast<const ForecastMeasureComputed*>(this);
    if (me->getUpdateExpression().empty()) return remainder;
    if (!initialized) {
      // Initialize symbol table
      for (auto m = begin(); m != end(); ++m)
        m->expressionvalue = fcstdata.getValue(*m);
      initialized = true;
      ForecastMeasureComputed::cost = fcst->getForecastItem()->getCost();
      ForecastMeasureComputed::fcstbckt = fcstdata.getForecastBucket();
      ForecastMeasureComputed::newvalue = val;
    }
    // Run assigments expressions
    me->update();
    // Copy from formula back to the measures
    for (auto& a : me->assignments)
      if (a != this)
        a->update(fcstdata, a->expressionvalue, mgr);
      else
        fcstdata.setValue(true, mgr, a, a->expressionvalue);
  }
  // OTHERS - SIMPLE, UNRELATED AGGREGATION
  else {
    // Note that we use measure.getDiscrete() rather than fcst.getDiscrete
    // here
    if (getDiscrete()) {
      auto qty = floor(val + ROUNDING_ERROR);
      remainder = val - qty;
      fcstdata.setValue(true, mgr, this, qty);
    } else
      fcstdata.setValue(true, mgr, this, val);
  }

  computeDependentMeasures(fcstdata, !initialized);
  return remainder;
}

void ForecastMeasure::computeDependentMeasures(ForecastBucketData& fcstdata,
                                               bool initialize) const {
  // Process all dependent measures
  for (auto& i : alldependents) {
    if (initialize) {
      // Initialize symbol table
      for (auto& m : all()) m.expressionvalue = fcstdata.getValue(m);
      ForecastMeasureComputed::cost =
          fcstdata.getForecast()->getForecastItem()->getCost();
      ForecastMeasureComputed::fcstbckt = fcstdata.getForecastBucket();
    }
    const_cast<ForecastMeasureComputed*>(i)->expressionvalue =
        i->getDiscrete() ? floor(i->compute() + ROUNDING_ERROR) : i->compute();
    double val = i->expressionvalue;
    if (i->getDefault() == -1 && val == -1.0)
      fcstdata.removeValue(true, nullptr, i);
    else
      fcstdata.setValue(true, nullptr, i, val);

    // Process changes of the computed total forecast
    if (i == Measures::forecasttotal) {
      fcstdata.setValue(true, nullptr, i, val);
      if (fcstdata.getEnd() > Plan::instance().getFcstCurrent()) {
        if (fcstdata.getForecast()->getPlanned())
          Measures::forecastnet->update(
              fcstdata, val - fcstdata.getValue(*Measures::forecastconsumed));
        else
          for (auto p = fcstdata.getForecast()->getParents(); p; ++p)
            if (p->getPlanned()) {
              auto pfcstdata = p->getData();
              lock_guard<recursive_mutex> exclusive(pfcstdata->lock);
              auto& pfcstbucketdata =
                  pfcstdata->getBuckets()[fcstdata.getIndex()];
              Measures::forecastnet->update(
                  pfcstbucketdata,
                  pfcstbucketdata.getValue(*Measures::forecasttotal) -
                      pfcstbucketdata.getValue(*Measures::forecastconsumed));
              break;
            }
      }
    }
  }
}

void MeasureValue::addToFree(MeasurePagePool& pool) {
  prev = pool.lastfree;
  next = nullptr;
  msr = PooledString::nullstring;
  if (pool.lastfree)
    pool.lastfree->next = this;
  else
    pool.firstfree = this;
  pool.lastfree = this;
}

void MeasureValue::addToFree() {
  auto& pool = getPagePool();
  lock_guard<mutex> l(pool.lock);
  addToFree(pool);
}

MeasurePage::MeasurePage(MeasurePagePool& pool) : next(nullptr) {
  // Insert into page list
  if (pool.lastpage) {
    prev = pool.lastpage;
    pool.lastpage->next = this;
  } else {
    pool.firstpage = this;
    prev = nullptr;
  }
  pool.lastpage = this;

  // Extend the list of free pairs
  for (auto& v : data) v.addToFree(pool);
}

short MeasurePage::status() const {
  bool empty = true;
  bool heads = false;
  for (auto& v : data) {
    if (v.msr) {
      empty = false;
      if (!v.prev || !v.next) heads = true;
    }
  }
  if (empty)
    return 2;
  else if (heads)
    return 0;  // Untouchable
  else
    return 1;  // can be emptied
}

void MeasurePagePool::releaseEmptyPages() {
  lock_guard<mutex> l(lock);
  unsigned int count = 0;
  for (auto p = firstpage; p;) {
    auto status = p->status();
    if (status == 2) {
      // Unlink the page
      if (p->prev)
        p->prev->next = p->next;
      else
        firstpage = p->next;
      if (p->next)
        p->next->prev = p->prev;
      else
        lastpage = p->prev;

      // Unlink the free nodes
      for (auto& v : p->data) {
        if (v.next)
          v.next->prev = v.prev;
        else
          lastfree = v.prev;
        if (v.prev)
          v.prev->next = v.next;
        else
          firstfree = v.next;
      }

      // Release the memory
      auto tmp = p;
      p = p->next;
      free(tmp);
      ++count;
    } else
      p = p->next;
  }
  logger << "Released " << count << " " << name << " memory pages" << endl;
}

void MeasureList::insert(const PooledString& k, double v, bool c) {
  if (c) {
    // Update if it exists already
    for (auto p = first; p; p = p->next)
      if (p->msr == k) {
        p->val = v;
        return;
      }
  }

  // Get a free pair
  MeasureValue* n;
  {
    auto& pool = k.starts_with("temp") ? MeasurePagePool::measurepages_temp
                                       : MeasurePagePool::measurepages_default;
    lock_guard<mutex> l(pool.lock);
    if (!pool.firstfree) {
      new MeasurePage(pool);
      if (!pool.firstfree) throw RuntimeException("No free memory");
    }
    n = pool.firstfree;
    pool.firstfree = pool.firstfree->next;
    if (pool.firstfree)
      pool.firstfree->prev = nullptr;
    else
      pool.lastfree = nullptr;
  }

  // Insert a new pair
  n->next = nullptr;
  n->msr = k;
  n->val = v;
  n->prev = last;
  if (last)
    last->next = n;
  else
    first = n;
  last = n;
}

void MeasureList::erase(const PooledString& k) {
  for (auto p = first; p; p = p->next)
    if (p->msr == k) {
      // Unlink from the list
      if (p->prev)
        p->prev->next = p->next;
      else
        first = p->next;
      if (p->next)
        p->next->prev = p->prev;
      else
        last = p->prev;

      // Add to free list
      p->addToFree();
      return;
    }
}

void MeasureList::erase(MeasureValue* p) {
  // Unlink from the list
  if (p->prev)
    p->prev->next = p->next;
  else
    first = p->next;
  if (p->next)
    p->next->prev = p->prev;
  else
    last = p->prev;

  // Add to free list
  p->addToFree();
}

void MeasureList::sort() {
  // Bubble sort
  bool ok;
  do {
    ok = true;
    for (auto p = first; p && p->next; p = p->next) {
      if (p->next->msr < p->msr) {
        swap(p->msr, p->next->msr);
        swap(p->val, p->next->val);
        ok = false;
      };
    }
  } while (!ok);
}

void MeasureList::check() {
  unsigned int count_fwd = 0;
  for (auto p = first; p; p = p->next) ++count_fwd;
  unsigned int count_bck = 0;
  unsigned int count_wrong_links = 0;
  for (auto p = last; p; p = p->prev) {
    ++count_bck;
    if (p->prev && p->prev->next != p) ++count_wrong_links;
  }
  if (count_fwd != count_bck)
    logger << "Error: Mismatch forward and backward size: " << count_fwd
           << " vs " << count_bck << endl;
  if (count_wrong_links)
    logger << "Error: " << count_wrong_links << "incorrect links in list"
           << endl;
  if (count_fwd != count_bck || count_wrong_links)
    throw DataException("Corrupted list");
}

pair<double, double> MeasurePagePool::check(const string& msg) {
  unsigned int count_pages = 0;
  unsigned int count_pages_free = 0;
  unsigned int count_pages_temp = 0;
  unsigned int count_pages_temp_free = 0;
  unsigned int count_free = 0;
  unsigned int count_used = 0;
  unsigned int count_temp_free = 0;
  unsigned int count_temp_used = 0;
  unsigned int count_wrong_links = 0;

  // Exclusive access needed
  lock_guard<mutex> l_tmp(measurepages_temp.lock);
  lock_guard<mutex> l_default(measurepages_default.lock);

  // Count temp pages
  for (auto p = measurepages_temp.firstpage; p; p = p->next) {
    ++count_pages_temp;
    if (p->prev && p->prev->next != p) ++count_wrong_links;
    bool empty = true;
    for (auto& v : p->data)
      if (v.msr) {
        ++count_temp_used;
        empty = false;
      } else
        ++count_temp_free;
    if (empty) ++count_pages_temp_free;
  }

  // Count default pages
  for (auto p = measurepages_default.firstpage; p; p = p->next) {
    ++count_pages;
    if (p->prev && p->prev->next != p) ++count_wrong_links;
    bool empty = true;
    for (auto& v : p->data)
      if (v.msr) {
        ++count_used;
        empty = false;
      } else
        ++count_free;
    if (empty) ++count_pages_free;
  }

  // Default free list
  unsigned int count_freelist_fwd = 0;
  for (auto p = measurepages_default.firstfree; p; p = p->next)
    ++count_freelist_fwd;
  unsigned int count_freelist_bck = 0;
  for (auto p = measurepages_default.lastfree; p; p = p->prev)
    ++count_freelist_bck;
  if (count_freelist_fwd != count_free || count_freelist_bck != count_free) {
    logger << "Error: mismatched free count " << count_freelist_fwd << " vs "
           << count_freelist_bck << " vs " << count_free << endl;
  }

  // Temp free list
  unsigned int count_freelist_temp_fwd = 0;
  for (auto p = measurepages_temp.firstfree; p; p = p->next)
    ++count_freelist_temp_fwd;
  unsigned int count_freelist_temp_bck = 0;
  for (auto p = measurepages_temp.lastfree; p; p = p->prev)
    ++count_freelist_temp_bck;
  if (count_freelist_temp_fwd != count_temp_free ||
      count_freelist_temp_bck != count_temp_free) {
    logger << "Error: mismatched temp free count " << count_freelist_temp_fwd
           << " vs " << count_freelist_temp_bck << " vs " << count_temp_free
           << endl;
  }

  // Print stats
  if (count_wrong_links) {
    logger << "Error: " << count_wrong_links << "incorrect links in list"
           << endl;
  }
  logger << "Measure memory page stats: " << msg << endl;
  logger << "   " << count_pages << " pages with " << count_used
         << " pairs in use and " << count_free << " free pairs." << endl;
  logger << "   " << count_pages_temp << " temporary pages with "
         << count_temp_used << " pairs in use and " << count_temp_free
         << " free pairs." << endl;
  double util = count_free + count_used + count_temp_free + count_temp_used;
  util = util ? round(100.0 * (count_used + count_temp_used) / util) : 0.0;
  logger << "   " << util << "% average utilization" << endl;
  logger << "   " << count_pages_free << " empty pages, "
         << count_pages_temp_free << " free temporary pages." << endl;
  return make_pair(util, static_cast<double>(count_pages + count_pages_temp));
}

}  // namespace frepple
