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

#include <random>

#include "frepple/database.h"
#include "rapidjson/document.h"

namespace frepple {

ForecastBase::HashTable ForecastBase::table;

Calendar* Forecast::calptr = nullptr;
long ForecastBase::horizon_future = 365L * 3L;
long ForecastBase::horizon_history = 365L * 10L;
long ForecastBase::forecast_partition = -1L;

const Keyword Forecast::tag_methods("methods");
const Keyword Forecast::tag_method("method");
const Keyword Forecast::tag_deviation("deviation");
const Keyword Forecast::tag_smape_error("smape_error");
const Keyword Forecast::tag_horizon_future("horizon_future");
const Keyword Forecast::tag_horizon_history("horizon_history");
const Keyword Forecast::tag_forecast_partition("forecast_partition");
const Keyword ForecastBucket::tag_weight("weight");
const Keyword ForecastBucket::tag_forecast("forecast");
const Keyword ForecastBucket::tag_forecast_total("forecasttotal");
const Keyword ForecastBucket::tag_forecast_consumed("forecastconsumed");
const Keyword ForecastBucket::tag_forecast_baseline("forecastbaseline");
const Keyword ForecastBucket::tag_forecast_override("forecastoverride");
const Keyword ForecastBucket::tag_orders_total("orderstotal");
const Keyword ForecastBucket::tag_orders_adjustment("ordersadjustment");
const Keyword ForecastBucket::tag_orders_adjustment_1("ordersadjustment1");
const Keyword ForecastBucket::tag_orders_adjustment_2("ordersadjustment2");
const Keyword ForecastBucket::tag_orders_adjustment_3("ordersadjustment3");
const Keyword ForecastBucket::tag_orders_open("ordersopen");
const Keyword ForecastBucket::tag_orders_planned("ordersplanned");
const Keyword ForecastBucket::tag_outlier("outlier");
const Keyword ForecastBucket::tag_forecast_planned("forecastplanned");

const MetaClass* Forecast::metadata = nullptr;
const MetaClass* ForecastBucket::metadata = nullptr;
const MetaCategory* ForecastBucket::metacategory = nullptr;
short ForecastBucket::DueWithinBucket = 1;
const string ForecastBucket::DUEATSTART = "start";
const string ForecastBucket::DUEATMIDDLE = "middle";
const string ForecastBucket::DUEATEND = "end";

int Forecast::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<Forecast>("demand", "demand_forecast",
                                                Object::create<Forecast>);
  registerFields<Forecast>(const_cast<MetaClass*>(metadata));

  // Get notified when a calendar is deleted
  FunctorStatic<Calendar, Forecast>::connect(SIG_REMOVE);

  // An extra global method
  PythonInterpreter::registerGlobalMethod(
      "saveforecast", saveForecast, METH_VARARGS,
      "Save the forecast information to a file.");
  PythonInterpreter::registerGlobalMethod(
      "aggregateMeasures", ForecastMeasure::aggregateMeasuresPython,
      METH_VARARGS,
      "Recompute the aggregate levels for the specified measures");
  PythonInterpreter::registerGlobalMethod(
      "computeMeasures", ForecastMeasure::computeMeasuresPython, METH_VARARGS,
      "Recompute calculated measures for the specified measures");
  PythonInterpreter::registerGlobalMethod(
      "updatePlannedForecast", ForecastMeasure::updatePlannedForecastPython,
      METH_NOARGS, "Update the planned quantity in the forecastplan table");
  PythonInterpreter::registerGlobalMethod(
      "resetMeasures", ForecastMeasure::resetMeasuresPython, METH_VARARGS,
      "Reset the specified measures");
  PythonInterpreter::registerGlobalMethod(
      "setForecast", Forecast::setValuePython2, METH_VARARGS,
      "Update forecast values");
  PythonInterpreter::registerGlobalMethod(
      "releaseUnusedMemory", MeasurePagePool::releaseEmptyPagesPython,
      METH_NOARGS, "Release memory pages with unused measure data");

  // Initialize the Python class
  auto& x = FreppleClass<Forecast, Demand>::getPythonType();
  x.addMethod("inspect", inspectPython, METH_VARARGS,
              "debugging function to print the forecast information");
  x.addMethod("set", setValuePython, METH_VARARGS | METH_KEYWORDS,
              "update measure data");
  x.addMethod("get", getValuePython, METH_VARARGS | METH_KEYWORDS,
              "retrieve measure data");
  return FreppleClass<Forecast, Demand>::initialize();
}

bool ForecastBase::Comparator::operator()(ForecastBase* a,
                                          ForecastBase* b) const {
  auto a_item = a->getForecastItem();
  auto a_location = a->getForecastLocation();
  auto a_customer = a->getForecastCustomer();
  auto b_item = b->getForecastItem();
  auto b_location = b->getForecastLocation();
  auto b_customer = b->getForecastCustomer();

  if (!a_item)
    return false;
  else if (!b_item)
    return true;
  else if (a_item != b_item || !a_location || !b_location || !a_customer ||
           !b_customer)
    return a_item->getName().compare(b_item->getName()) < 0;
  else if (a_location != b_location)
    return a_location->getName().compare(b_location->getName()) < 0;
  else if (a_customer != b_customer)
    return a_customer->getName().compare(b_customer->getName()) < 0;
  else
    // Pointer comparison as last resort
    return a_item < b_item;
}

ForecastBase::ItemIterator::ItemIterator(Item* it) {
  ForecastKey tmp(it);
  auto lb_ub = table.equal_range(&tmp);
  iter = lb_ub.first;
  ub = lb_ub.second;
  forecast = (iter != ub) ? *iter : nullptr;
}

ForecastBase* ForecastBase::findForecast(Item* i, Customer* c, Location* l,
                                         bool allow_create) {
  if (!i || !l || !c) return nullptr;
  if (c->getNumberOfDemands()) {
    ForecastKey tmp(i, l, c);
    auto f = table.find(&tmp);
    if (f != table.end()) return *f;
  }
  if (allow_create) {
    if (!i->isGroup() && !l->isGroup() && !c->isGroup()) {
      auto f = new Forecast();
      f->setItem(i);
      f->setCustomer(c);
      f->setLocation(l);
      return f;
    } else
      return new ForecastAggregated(i, l, c);
  }
  return nullptr;
}

bool Forecast::isLeaf() const {
  if (leaf == -1) {
    const_cast<Forecast*>(this)->leaf = 1;
    for (Item::memberRecursiveIterator itm(getItem()); !itm.empty(); ++itm) {
      for (ItemIterator itmfcst(&*itm); itmfcst; ++itmfcst) {
        if ((itmfcst->getForecastItem() != getItem() ||
             itmfcst->getForecastLocation() != getLocation() ||
             itmfcst->getForecastCustomer() != getCustomer()) &&
            itmfcst->getForecastCustomer()->isMemberOf(getCustomer()) &&
            itmfcst->getForecastLocation()->isMemberOf(getLocation())) {
          const_cast<Forecast*>(this)->leaf = 0;
          return false;
        }
      }
    }
  }
  return leaf == 1;
}

int ForecastBucket::initialize() {
  // Initialize the metadata
  // No factory method for this class
  metacategory = MetaCategory::registerCategory<ForecastBucket>(
      "forecastbucket", "forecastbuckets", reader);
  metadata = MetaClass::registerClass<ForecastBucket>("forecastbucket",
                                                      "demand_forecastbucket");
  registerFields<ForecastBucket>(const_cast<MetaClass*>(metadata));

  ProblemOutlier::metadata =
      MetaClass::registerClass<ProblemOutlier>("problem", "outlier", true);

  // Initialize the Python class
  auto& x = FreppleClass<ForecastBucket, Demand>::getPythonType();
  x.setName("demand_forecastbucket");
  x.setDoc("frePPLe forecastbucket");
  x.supportgetattro();
  x.supportsetattro();
  x.supportstr();
  x.supportcreate(create);
  x.supportcompare();
  x.setBase(metacategory->pythonClass);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  x.addMethod("addConstraint", addConstraint, METH_VARARGS,
              "add a constraint to the demand");
  x.addMethod("set", setMeasurePython, METH_VARARGS | METH_KEYWORDS,
              "update a measure");
  x.addMethod("get", getMeasurePython, METH_VARARGS, "get a measure");
  metadata->setPythonClass(x);
  return x.typeReady();
}

Object* ForecastBucket::reader(const MetaClass*, const DataValueDict& in,
                               CommandManager* mgr) {
  // Pick up the forecast attribute. An error is reported if it's missing.
  const DataValue* fcstElement = in.get(ForecastBucket::tag_forecast);
  if (!fcstElement) throw DataException("Missing forecast field");
  Object* fcstobject = fcstElement->getObject();
  if (!fcstobject || fcstobject->getType() != *Forecast::metadata)
    throw DataException("Invalid forecast field");

  // Pick up the start date.
  const DataValue* strtElement = in.get(Tags::start);
  if (!strtElement) throw DataException("Start date must be provided");
  Date strt = strtElement->getDate();

  // Pick up the end date.
  const DataValue* endElement = in.get(Tags::end);
  Date nd;
  if (endElement) nd = endElement->getDate();

  // Find the bucket
  {
    auto data = static_cast<Forecast*>(fcstobject)->getData();
    lock_guard<recursive_mutex> exclusive(data->lock);
    ForecastBucket* fcstbckt = nullptr;
    for (auto& fcstbktdata : data->getBuckets()) {
      if (fcstbktdata.getDates().within(strt)) {
        fcstbckt = fcstbktdata.getOrCreateForecastBucket();
        if (fcstbckt && !nd || (nd && fcstbckt->getStartDate() <= nd &&
                                fcstbckt->getEndDate() >= nd))
          // A single bucket is being updated
          return fcstbckt;
        break;
      }
    }
  }

  /** Only a start date was given, and we didn't find a matching bucket. */
  if (!nd) return nullptr;

  /** A start and end date are given, and multiple buckets can be impacted.
   */
  DateRange dr(strt, nd);
  static_cast<Forecast*>(fcstobject)->setFields(dr, in, mgr);
  return nullptr;
}

PyObject* ForecastBucket::create(PyTypeObject*, PyObject*, PyObject* kwds) {
  try {
    // Pick up the forecast. An error is reported if it's missing or has a
    // wrong data type.
    PyObject* pyfcst = PyDict_GetItemString(kwds, "forecast");
    if (!pyfcst) throw DataException("missing forecast on forecastbucket");
    if (!PyObject_TypeCheck(pyfcst, Forecast::metadata->pythonClass))
      throw DataException("forecastbucket forecast must be of type forecast");

    // Pick up the start date
    PyObject* strt = PyDict_GetItemString(kwds, "start");
    if (!strt) throw DataException("Start date must be provided");
    Date startdate = PythonData(strt).getDate();

    // Initialize the forecast.
    {
      auto* fcst = static_cast<Forecast*>(pyfcst);
      auto data = fcst->getData();
      lock_guard<recursive_mutex> exclusive(data->lock);

      // Find the correct forecast bucket
      // @todo This linear loop doesn't scale well when the number of
      // buckets increases. The loading time goes up quadratically: need to
      // read more buckets + each bucket takes longer
      for (auto& bckt : data->getBuckets()) {
        if (bckt.getDates().within(startdate)) {
          auto fcstbckt = bckt.getOrCreateForecastBucket();
          if (!fcstbckt) continue;
          // Iterate over extra keywords, and set attributes.
          PyObject *key, *value;
          Py_ssize_t pos = 0;
          while (PyDict_Next(kwds, &pos, &key, &value)) {
            PythonData field(value);
            PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
            DataKeyword attr(PyBytes_AsString(key_utf8));
            Py_DECREF(key_utf8);
            if (!attr.isA(ForecastBucket::tag_forecast) &&
                !attr.isA(Tags::start) && !attr.isA(Tags::name) &&
                !attr.isA(Tags::type) && !attr.isA(Tags::action)) {
              logger << "   extra " << attr.getName() << '\n';
              const MetaFieldBase* fmeta =
                  fcstbckt->getType().findField(attr.getHash());
              if (!fmeta && fcstbckt->getType().category)
                fmeta = fcstbckt->getType().category->findField(attr.getHash());
              if (fmeta)
                // Update the attribute
                fmeta->setField(fcstbckt, field);
              else
                fcstbckt->setProperty(attr.getName(), value);
            }
          };

          // Return the object
          Py_INCREF(fcstbckt);
          return fcstbckt;
        }
      }
    }
    return nullptr;
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

ForecastBucketData::ForecastBucketData(const ForecastBase* f, Date s, Date e,
                                       short i, bool d)
    : fcst(const_cast<ForecastBase*>(f)), dates(s, e), index(i) {
  if (d) markDirty();
  if (fcst->getPlanned()) {
    string fcstbcktname;
    if (e - s > Duration(22L * 3600L))
      fcstbcktname = static_cast<const Forecast*>(f)->getName() + " - " +
                     s.toString("%Y-%m-%d");
    else
      fcstbcktname =
          static_cast<const Forecast*>(f)->getName() + " - " + string(s);
    auto tmp = Demand::find(fcstbcktname);
    if (tmp && tmp->hasType<ForecastBucket>())
      fcstbkt = static_cast<ForecastBucket*>(tmp);
  }
}

ForecastBucket::ForecastBucket(Forecast* f, const DateRange& b, short i)
    : timebucket(b), bucketindex(i) {
  if (!f->getName().empty()) {
    if (b.getDuration() > Duration(22L * 3600L))
      setName(f->getName() + " - " + b.getStart().toString("%Y-%m-%d"));
    else
      setName(f->getName() + " - " + string(b.getStart()));
  }
  setOwner(f);
  setHidden(true);  // Avoid the subdemands show up in the list of demands
  setItem(f->getItem());
  setCustomer(f->getCustomer());
  auto currentdate = Plan::instance().getFcstCurrent();
  Date due;
  switch (DueWithinBucket) {
    case 0:  // Start
      due = b.getStart();
      break;
    case 1: {  // Middle
      DateDetail tmp =
          b.getStart() + Duration(b.getDuration().getSeconds() / 2);
      tmp.roundDownDay();  // Truncate to the start of the day
      due = tmp;
      break;
    }
    case 2: {  // End
      // Removing one second to the end date to remain in the same bucket.
      due = b.getEnd() - Duration(1L);
      break;
    }
  }
  if (b.getStart() <= currentdate && b.getEnd() > currentdate &&
      due < currentdate)
    // Forecast in the current week shouldn't be in the past
    due = currentdate;
  setDue(due);
  setPriority(f->getPriority());
  setMaxLateness(f->getMaxLateness());
  auto tmp = f->getRawMinShipment();
  if (tmp >= 0.0) setMinShipment(tmp);
  if (f->getOperation()) setOperation(f->getOperation());
  setLocation(f->getLocation());
  setBatch(f->getBatch());
  initType(metadata);
}

void ForecastBucket::writeProperties(Serializer& o) const {
  Object::writeProperties(o);
  auto fcstdata = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  auto& fcstbktdata = fcstdata->getBuckets()[bucketindex];
  fcstbktdata.sortMeasures();
  for (auto tmp : fcstbktdata.getMeasures())
    o.writeElement(Tags::data, tmp->getMeasure(), tmp->getValue());
}

double ForecastBucket::getForecastTotal() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  return Measures::forecasttotal->getValue(data->getBuckets()[bucketindex]);
}

double ForecastBucket::getForecastNet() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  auto& bcktdata = data->getBuckets()[bucketindex];
  return Measures::forecasttotal->getValue(bcktdata) -
         Measures::forecastconsumed->getValue(bcktdata);
}

double ForecastBucket::getForecastConsumed() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  return Measures::forecastconsumed->getValue(data->getBuckets()[bucketindex]);
}

double ForecastBucket::getForecastBaseline() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  return Measures::forecastbaseline->getValue(data->getBuckets()[bucketindex]);
}

void ForecastBucket::setForecastBaseline(double v) {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Measures::forecastbaseline->disaggregate(data->getBuckets()[bucketindex], v);
}

double ForecastBucket::getForecastOverride() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  return Measures::forecastoverride->getValue(data->getBuckets()[bucketindex]);
}

void ForecastBucket::setForecastOverride(double v) {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Measures::forecastoverride->disaggregate(data->getBuckets()[bucketindex], v);
}

double ForecastBucket::getOrdersOpen() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  return Measures::ordersopen->getValue(data->getBuckets()[bucketindex]);
}

double ForecastBucket::getOrdersTotal() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  return Measures::orderstotal->getValue(data->getBuckets()[bucketindex]);
}

void ForecastBucket::setOrdersTotal(double v) {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Measures::orderstotal->disaggregate(data->getBuckets()[bucketindex], v);
}

double ForecastBucket::getOrdersAdjustment() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  return Measures::ordersadjustment->getValue(data->getBuckets()[bucketindex]);
}

void ForecastBucket::setOrdersAdjustment(double v) {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Measures::ordersadjustment->disaggregate(data->getBuckets()[bucketindex], v);
}

bool Forecast::callback(Calendar* l, const Signal) {
  // This function is called when a calendar is about to be deleted.
  // If that calendar happens to be the one defining calendar buckets, we
  // reset the calendar pointer to null.
  if (calptr == l) calptr = nullptr;
  return true;
}

Forecast::~Forecast() {
  // Update the dictionary
  eraseFromHash(this);

  // Delete all children demands
  ForecastBucket::bucketiterator iter(this);
  while (ForecastBucket* bckt = iter.next()) delete bckt;
}

void Forecast::setPlanned(const bool b) {
  if (planned == b) return;
  planned = b;
  if (getItem() && getLocation() && getCustomer()) {
    for (auto m = getMembers(); m != end(); ++m)
      m->setQuantity(b ? static_cast<ForecastBucket*>(&*m)->getForecastNet()
                       : 0);
  }
}

void ForecastBase::setFields(DateRange& d, const DataValueDict& in,
                             CommandManager* mgr, bool add) {
  // Get all data, if not done yet
  auto data = getData();
  lock_guard<recursive_mutex> exclusive(data->lock);

  // Find all forecast demands, and sum their weights
  double weights = 0.0;
  for (auto& x : data->getBuckets()) {
    if (d.intersect(x.getDates())) {
      // Bucket intersects with daterange
      if (!d.getDuration()) {
        // Single date provided. Update that one bucket.
        // TODO Currently we only update the fcstoverride field
        const DataValue* fcstOverrideElement =
            in.get(ForecastBucket::tag_forecast_override);
        if (fcstOverrideElement) {
          double total = fcstOverrideElement->getDouble();
          Measures::forecastoverride->disaggregate(
              this, x.getStart(), x.getEnd(),
              add ? Measures::forecastoverride->getValue(x) + total : total,
              false, 0.0, mgr);
        }
        return;
      }
      weights += static_cast<double>(x.getDates().overlap(d));
    }
  }

  // Update the forecast quantity, respecting the weights
  // TODO Currently we only update the total field. Need to do this for all
  // possible fields...
  const DataValue* fcstOverrideElement =
      in.get(ForecastBucket::tag_forecast_override);
  if (fcstOverrideElement) {
    double total = fcstOverrideElement->getDouble();
    // Expect to find at least one non-zero weight...
    if (!weights && total) {
      ostringstream o;
      o << "No valid forecast date in range " << d << " of forecast '"
        << getForecastItem() << "', '" << getForecastLocation() << "', '"
        << getForecastCustomer() << "'";
      throw DataException(o.str());
    } else if (weights)
      total /= weights;
    double carryover = 0.0;
    for (auto& x : data->getBuckets()) {
      if (d.intersect(x.getDates())) {
        // Bucket intersects with daterange
        Duration o = x.getDates().overlap(d);
        auto percent = static_cast<double>(o);
        if (getDiscrete()) {
          // Rounding to discrete numbers
          carryover += total * percent;
          auto intdelta = ceil(carryover - 0.5);
          if (!intdelta)
            // Little trick to avoid "-0" as forecast override
            intdelta = 0.0;
          carryover -= intdelta;
          if (o < x.getDates().getDuration() || add) {
            // The bucket is only partially updated
            auto tmp = Measures::forecastoverride->getValue(x);
            if (tmp == -1) tmp = 0;
            Measures::forecastoverride->disaggregate(this, x.getStart(),
                                                     x.getEnd(), tmp + intdelta,
                                                     false, 0.0, mgr);
          } else
            // The bucket is completely updated
            Measures::forecastoverride->disaggregate(
                this, x.getStart(), x.getEnd(), intdelta, false, 0.0, mgr);
        } else {
          // No rounding
          if (o < x.getDates().getDuration() || add) {
            // The bucket is only partially updated
            auto tmp = Measures::forecastoverride->getValue(x);
            if (tmp == -1) tmp = 0;
            Measures::forecastoverride->disaggregate(
                this, x.getStart(), x.getEnd(), tmp + total * percent, false,
                0.0, mgr);
          } else
            // The bucket is completely updated
            Measures::forecastoverride->disaggregate(
                this, x.getStart(), x.getEnd(), total * percent, false, 0.0,
                mgr);
        }
      }
    }
  }
}

void Forecast::setItem(Item* i) {
  // No change
  if (getItem() == i) return;

  // Check for duplicates
  if (getLocation() && i && getCustomer()) {
    auto exists = findForecast(i, getCustomer(), getLocation());
    if (exists) {
      if (exists->isAggregate()) {
        // Replace existing element
        eraseFromHash(exists);
        delete exists;
      } else
        // Already exists
        throw DataException(
            "Duplicate forecast for item, location and customer");
    }
  }

  // Update the dictionary
  if (getLocation() && getItem() && getCustomer()) eraseFromHash(this);
  Demand::setItem(i);
  if (getLocation() && getItem() && getCustomer()) insertInHash(this);

  // Update the item for all buckets/subdemands
  for (auto m = getMembers(); m != end(); ++m) m->setItem(i);
}

void Forecast::setCustomer(Customer* i) {
  // No change
  if (getCustomer() == i) return;

  // Check for duplicates
  if (getLocation() && getItem() && i) {
    auto exists = findForecast(getItem(), i, getLocation());
    if (exists) {
      if (exists->isAggregate()) {
        // Replace existing element
        eraseFromHash(exists);
        delete exists;
      } else
        // Already exists
        throw DataException(
            "Duplicate forecast for item, location and customer");
    }
  }

  // Update the dictionary
  if (getLocation() && getItem() && getCustomer()) eraseFromHash(this);
  Demand::setCustomer(i);
  if (getLocation() && getItem() && getCustomer()) insertInHash(this);

  // Update the item for all buckets/subdemands
  for (auto m = getMembers(); m != end(); ++m) m->setCustomer(i);
}

void Forecast::setLocation(Location* i) {
  // No change
  if (getLocation() == i) return;

  // Check for duplicates
  if (i && getItem() && getCustomer()) {
    auto exists = findForecast(getItem(), getCustomer(), i);
    if (exists) {
      if (exists->isAggregate()) {
        // Replace existing element
        eraseFromHash(exists);
        delete exists;
      } else
        // Already exists
        throw DataException(
            "Duplicate forecast for item, location and customer");
    }
  }

  // Update the dictionary
  if (getLocation() && getItem() && getCustomer()) eraseFromHash(this);
  Demand::setLocation(i);
  if (getLocation() && getItem() && getCustomer()) insertInHash(this);

  // Update the item for all buckets/subdemands
  for (auto m = getMembers(); m != end(); ++m) m->setLocation(i);
}

void Forecast::setMaxLateness(Duration i) {
  Demand::setMaxLateness(i);
  // Update the maximum lateness for all buckets/subdemands
  for (auto m = getMembers(); m != end(); ++m) m->setMaxLateness(i);
}

void Forecast::setMinShipment(double i) {
  Demand::setMinShipment(i);
  // Update the minimum shipment for all buckets/subdemands
  for (auto m = getMembers(); m != end(); ++m) m->setMinShipment(i);
}

void Forecast::setPriority(int i) {
  Demand::setPriority(i);
  // Update the priority for all buckets/subdemands
  for (auto m = getMembers(); m != end(); ++m) m->setPriority(i);
}

void Forecast::setMethodsString(const string& n) {
  int tmp_methods = 0;
  if (n.empty())
    tmp_methods |= METHOD_ALL;
  else {
    for (const char* ch = n.c_str(); *ch; ++ch) {
      if (isspace(*ch) || ispunct(*ch)) continue;
      if (!strncmp(ch, "automatic", 9)) {
        ch += 8;
        tmp_methods |= METHOD_ALL;
      } else if (!strncmp(ch, "constant", 8)) {
        ch += 7;
        tmp_methods |= METHOD_CONSTANT;
      } else if (!strncmp(ch, "trend", 5)) {
        ch += 4;
        tmp_methods |= METHOD_TREND;
      } else if (!strncmp(ch, "intermittent", 12)) {
        ch += 11;
        tmp_methods |= METHOD_CROSTON;
      } else if (!strncmp(ch, "seasonal", 8)) {
        ch += 7;
        tmp_methods |= METHOD_SEASONAL;
      } else if (!strncmp(ch, "moving average", 14)) {
        ch += 13;
        tmp_methods |= METHOD_MOVINGAVERAGE;
      } else if (!strncmp(ch, "manual", 6)) {
        ch += 5;
        tmp_methods |= METHOD_MANUAL;
      } else
        throw DataException("Can't parse forecast methods list");
    }
  }
  methods = tmp_methods;
}

string Forecast::getMethodsString() const {
  if (!methods || methods & METHOD_MANUAL) return "manual";
  if ((methods & METHOD_ALL) == METHOD_ALL) return "automatic";
  stringstream o;
  bool first = true;
  if (methods & METHOD_CONSTANT) {
    if (first) {
      first = false;
      o << "constant";
    } else
      o << ", constant";
  }
  if (methods & METHOD_TREND) {
    if (first) {
      first = false;
      o << "trend";
    } else
      o << ", trend";
  }
  if (methods & METHOD_SEASONAL) {
    if (first) {
      first = false;
      o << "seasonal";
    } else
      o << ", seasonal";
  }
  if (methods & METHOD_CROSTON) {
    if (first) {
      first = false;
      o << "intermittent";
    } else
      o << ", intermittent";
  }
  if (methods & METHOD_MOVINGAVERAGE) {
    if (first) {
      first = false;
      o << "moving average";
    } else
      o << ", moving average";
  }
  return o.str();
}

void ForecastBase::ParentIterator::increment() {
  while (item) {
    // Find the next parent
    if (customer) customer = customer->getOwner();
    if (!customer) {
      customer = rootforecast->getForecastCustomer();
      if (location) location = location->getOwner();
      if (!location) {
        location = rootforecast->getForecastLocation();
        if (item) item = item->getOwner();
      }
    }

    // Check if a forecast exists at this combination
    if (item) {
      forecast = Forecast::findForecast(item, customer, location);
      if (!forecast)
        forecast = new ForecastAggregated(item, location, customer);
      return;
    }
  }

  // No more parents exists
  customer = nullptr;
  location = nullptr;
  forecast = nullptr;
}

void ForecastBase::LeafIterator::increment(bool first) {
  if (!first) {
    if (itmfcst)
      ++itmfcst;
    else {
      ++item;
      if (!item.empty()) itmfcst = ItemIterator(&*item);
    }
  }
  while (!item.empty()) {
    while (itmfcst) {
      if (itmfcst->getForecastCustomer()->isMemberOf(
              rootforecast->getForecastCustomer()) &&
          itmfcst->getForecastLocation()->isMemberOf(
              rootforecast->getForecastLocation()) &&
          (inclusive || *itmfcst != rootforecast) &&
          (measure ? measure->isLeaf(*itmfcst) : itmfcst->isLeaf()))
        // Found a leaf forecast
        return;
      else
        ++itmfcst;
    }
    ++item;
    if (!item.empty()) itmfcst = ItemIterator(&*item);
  }
}

double ForecastBucket::getOrdersAdjustmentMinus1() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Date tmpdate = getDue() - Duration(365 * 86400L);
  for (auto& b : data->getBuckets()) {
    if (b.getStart() <= tmpdate && b.getEnd() > tmpdate)
      return Measures::ordersadjustment->getValue(b);
  }
  return 0.0;
}

void ForecastBucket::setOrdersAdjustmentMinus1(double val) {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Date tmpdate = getDue() - Duration(365 * 86400L);
  for (auto& b : data->getBuckets()) {
    if (b.getStart() <= tmpdate && b.getEnd() > tmpdate) {
      Measures::ordersadjustment->disaggregate(b, val);
      return;
    }
  }
}

double ForecastBucket::getOrdersAdjustmentMinus2() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Date tmpdate = getDue() - Duration(2 * 365 * 86400L);
  for (auto& b : data->getBuckets()) {
    if (b.getStart() <= tmpdate && b.getEnd() > tmpdate)
      return Measures::ordersadjustment->getValue(b);
  }
  return 0.0;
}

void ForecastBucket::setOrdersAdjustmentMinus2(double val) {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Date tmpdate = getDue() - Duration(2 * 365 * 86400L);
  for (auto& b : data->getBuckets()) {
    if (b.getStart() <= tmpdate && b.getEnd() > tmpdate) {
      Measures::ordersadjustment->disaggregate(b, val);
      return;
    }
  }
}

double ForecastBucket::getOrdersAdjustmentMinus3() const {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Date tmpdate = getDue() - Duration(3 * 365 * 86400L);
  for (auto& b : data->getBuckets()) {
    if (b.getStart() <= tmpdate && b.getEnd() > tmpdate)
      return Measures::ordersadjustment->getValue(b);
  }
  return 0.0;
}

void ForecastBucket::setOrdersAdjustmentMinus3(double val) {
  auto data = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(data->lock);
  Date tmpdate = getDue() - Duration(3 * 365 * 86400L);
  for (auto& b : data->getBuckets()) {
    if (b.getStart() <= tmpdate && b.getEnd() > tmpdate) {
      Measures::ordersadjustment->disaggregate(b, val);
      return;
    }
  }
}

double ForecastBucket::getOrdersPlanned() const {
  auto fcstdata = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  return fcstdata->getBuckets()[getIndex()].getOrdersPlanned();
}

double ForecastBucketData::getOrdersPlanned() const {
  double planned = 0.0;
  Item::bufferIterator bufiter(getForecast()->getForecastItem());
  while (Buffer* buf = bufiter.next()) {
    if (buf->getLocation() != getForecast()->getForecastLocation()) continue;

    for (auto& oo : buf->getFlowPlans()) {
      if (oo.getQuantity() >= 0 || oo.getEventType() != 1) continue;
      OperationPlan* opplan = static_cast<FlowPlan&>(oo).getOperationPlan();
      auto* dmd = dynamic_cast<DemandDefault*>(opplan->getDemand());
      if (dmd && getDates().within(opplan->getEnd()) &&
          dmd->getCustomer() == getForecast()->getForecastCustomer())
        planned += opplan->getQuantity();
    }
  }
  return planned;
}

double ForecastBucket::getForecastPlanned() const {
  auto fcstdata = getForecast()->getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  return fcstdata->getBuckets()[getIndex()].getForecastPlanned();
}

double ForecastBucketData::getForecastPlanned() const {
  // Find all delivery operationplans that fall within this forecast bucket
  if (!getForecast()->getPlanned()) return 0.0;
  double planned = 0.0;
  auto fcst = static_cast<const Forecast*>(getForecast());
  for (auto m = fcst->getMembers(); m != Demand::end(); ++m) {
    auto dlvryIter = m->getOperationPlans();
    while (OperationPlan* dlvry = dlvryIter.next())
      if (getDates().within(dlvry->getEnd())) planned += dlvry->getQuantity();
  }
  return planned;
}

void ForecastBucket::reduceDeliveries(double qty_to_free, CommandManager* mgr) {
  // Reduce delivery plans of this forecast bucket.
  // By reducing the delivery plans we free up the planned supply for new
  // orders.
  auto fcst = getForecast();
  if (!fcst->getPlanned() || qty_to_free < ROUNDING_ERROR) return;

  // Collect all deliveries
  list<OperationPlan*> deliveries;
  for (auto m = fcst->getMembers(); m != Demand::end(); ++m) {
    auto dlvryIter = m->getOperationPlans();
    while (OperationPlan* dlvry = dlvryIter.next()) deliveries.push_back(dlvry);
  }
  if (deliveries.empty()) return;
  deliveries.sort([](OperationPlan*& a, OperationPlan*& b) { return *a < *b; });

  // First, try to find deliveries in the due date bucket
  for (auto dlvry = deliveries.begin();
       qty_to_free > ROUNDING_ERROR && dlvry != deliveries.end(); ++dlvry) {
    if (getDueRange().within((*dlvry)->getEnd())) {
      if ((*dlvry)->getQuantity() > qty_to_free + ROUNDING_ERROR) {
        if (mgr)
          mgr->add(new CommandMoveOperationPlan(
              *dlvry, Date::infinitePast, (*dlvry)->getEnd(),
              (*dlvry)->getQuantity() - qty_to_free, true));
        else
          (*dlvry)->setQuantity((*dlvry)->getQuantity() - qty_to_free, true);
        return;
      } else {
        if (mgr)
          mgr->add(new CommandMoveOperationPlan(*dlvry, Date::infinitePast,
                                                (*dlvry)->getEnd(), 0, true));
        else
          (*dlvry)->setQuantity(0, true);
        qty_to_free -= (*dlvry)->getQuantity();
      }
    }
  }
  if (qty_to_free < ROUNDING_ERROR) return;

  // Second, search backward for deliveries in earlier buckets
  for (auto dlvry = deliveries.rbegin();
       qty_to_free > ROUNDING_ERROR && dlvry != deliveries.rend(); ++dlvry) {
    if ((*dlvry)->getEnd() < getDueRange().getStart()) {
      if ((*dlvry)->getQuantity() > qty_to_free + ROUNDING_ERROR) {
        (*dlvry)->setQuantity((*dlvry)->getQuantity() - qty_to_free, true);
        return;
      } else {
        (*dlvry)->setQuantity(0, true);
        qty_to_free -= (*dlvry)->getQuantity();
      }
    }
  }
  if (qty_to_free < ROUNDING_ERROR) return;

  // Thirdly, search forward for deliveries in later buckets
  for (auto dlvry = deliveries.begin();
       qty_to_free > ROUNDING_ERROR && dlvry != deliveries.end(); ++dlvry) {
    if ((*dlvry)->getEnd() >= getDueRange().getEnd()) {
      if ((*dlvry)->getQuantity() > qty_to_free + ROUNDING_ERROR) {
        (*dlvry)->setQuantity((*dlvry)->getQuantity() - qty_to_free, true);
        return;
      } else {
        (*dlvry)->setQuantity(0, true);
        qty_to_free -= (*dlvry)->getQuantity();
      }
    }
  }
}

ForecastData::ForecastData(const ForecastBase* f) {
  if (Cache::instance->getLogLevel() > 0)
    logger << "Cache reads forecast " << f->getForecastItem() << "   "
           << f->getForecastLocation() << "   " << f->getForecastCustomer()
           << '\n';

  // One off initialization
  auto dbconnection = Plan::instance().getDBconnection();
  thread_local static DatabaseReader db(dbconnection);
  thread_local static DatabasePreparedStatement stmt;
  thread_local static short mode = 0;
  thread_local static vector<DateRange> dates;

  for (short attempts = 0; attempts <= 1; ++attempts) try {
      if (!mode) {
        if (dbconnection.empty())
          // Mode 1: Not connected to a database
          mode = 1;
        else {
          // Mode 2: Connected to a database
          mode = 2;

          // We use a single, dedicated database connection for this
          stringstream str;
          str << "select extract(epoch from startdate), extract(epoch from "
                 "enddate)";
          for (auto msr = ForecastMeasure::begin();
               msr != ForecastMeasure::end(); ++msr) {
            if (msr->getStored()) str << ", " << msr->getName();
          }
          str << " from forecastplan";
          auto partition = f->getForecastPartition();
          if (partition != -1) str << "_" << partition;
          str << " where item_id = $1::text and location_id = $2::text "
                 "and customer_id = $3::text "
                 "and enddate >= $4::timestamp and startdate <= $5::timestamp "
                 "order by startdate";
          try {
            stmt = DatabasePreparedStatement(db, "Read forecastplan values",
                                             str.str(), 5);
            auto currentdate = Plan::instance().getFcstCurrent();
            stmt.setArgument(
                3, currentdate - Duration(86400L * f->getHorizonHistory()));
            stmt.setArgument(
                4, currentdate + Duration(86400L * f->getHorizonFuture()));
          } catch (exception& e) {
            logger << "Error creating prepared statement: " << e.what() << '\n';
            db.closeConnection();
          } catch (...) {
            logger << "Error creating prepared statement\n";
            db.closeConnection();
          }
        }
      }

      // One-of building of forecast bucket dates
      if (dates.empty()) {
        Date prevDate;
        Date hrzn_start =
            Plan::instance().getFcstCurrent() -
            Duration(ForecastBase::getHorizonHistoryStatic() * 86400L);
        Date hrzn_end =
            Plan::instance().getCurrent() +
            Duration(ForecastBase::getHorizonFutureStatic() * 86400L);
        for (Calendar::EventIterator i(Forecast::getCalendar_static());
             prevDate <= hrzn_end; prevDate = i.getDate(), ++i) {
          if (prevDate && i.getDate() > hrzn_start &&
              i.getDate() != Date::infiniteFuture)
            dates.emplace_back(prevDate, i.getDate());
        }
      }

      // Create buckets
      if (buckets.empty()) {
        short cnt = 0;
        buckets.reserve(dates.size());
        for (const auto& b : dates)
          buckets.emplace_back(f, b.getStart(), b.getEnd(), cnt++, mode == 2);
      }

      if (mode == 2) {
        // Reading forecast data from a database connection

        stmt.setArgument(0, f->getForecastItem()->getName());
        stmt.setArgument(1, f->getForecastLocation()->getName());
        stmt.setArgument(2, f->getForecastCustomer()->getName());
        DatabaseResult res(db, stmt);

        auto totalRows = res.countRows();
        auto bckiter = buckets.begin();
        for (int i = 0; i < totalRows; ++i) {
          // Find the matching forecastbucketdata object
          Date st(res.getValueLong(i, 0));
          Date nd(res.getValueLong(i, 1));
          while (bckiter != buckets.end() && bckiter->getStart() < st)
            // missing record in the database, which is perfectly ok
            ++bckiter;
          if (bckiter == buckets.end()) {
            logger << "Time buckets not aligned: got " << st << ", " << nd
                   << '\n';
            throw DataException("Forecastplan buckets not matching calendar");
          }
          if (bckiter->getStart() != st || bckiter->getEnd() != nd) {
            logger << "Time buckets not aligned: got " << st << ", " << nd
                   << " and expected " << bckiter->getStart() << ", "
                   << bckiter->getEnd() << '\n';
            throw DataException("Forecastplan buckets not matching calendar");
          }

          // Read the measures
          int fieldcounter = 1;
          for (auto msr = ForecastMeasure::begin();
               msr != ForecastMeasure::end(); ++msr) {
            if (!msr->getStored()) continue;
            auto val = res.getValueDoubleOrNull(i, ++fieldcounter);
            if (!val.second) {
              if (val.first != msr->getDefault())
                bckiter->setValue(false, nullptr, &*msr, val.first);
              else
                bckiter->removeValue(false, nullptr, &*msr);
            }
          }

          // Update the supply side
          if (bckiter->getEnd() > Plan::instance().getFcstCurrent() &&
              f->getPlanned()) {
            auto tmp = Measures::forecastnet->getValue(*bckiter);
            if (tmp)
              bckiter->getOrCreateForecastBucket()->setQuantity(tmp);
            else {
              auto fcstbckt = bckiter->getOrCreateForecastBucket();
              if (fcstbckt)
                bckiter->getOrCreateForecastBucket()->setQuantity(0.0);
            }
          }
        }

        // We need to reset the dirty flag on all buckets:
        clearDirty();
      }

      // Successfully completed
      return;
    } catch (DatabaseBadConnection) {
      // Try again with a new connection
      mode = 0;
      db = DatabaseReader(dbconnection);
    }
}

void ForecastData::clearDirty() const {
  for (const auto& bucket : buckets) bucket.clearDirty();
  if (!buckets.empty()) buckets[0].getForecast()->clearDirty();
}

size_t ForecastData::getSize() const {
  size_t tmp = 0;
  size_t cnt = 0;
  for (const auto& bucket : buckets) {
    ++cnt;
    tmp += bucket.getSize();
  }
  return tmp;
}

size_t ForecastBucketData::getSize() const {
  // Assuming the implementation of the measure map is a red-black binary
  // tree, the size per measure is a) a pointer to a pooledstring, b) a
  // pointer to the numeric, and c) 3 pointers to maintain the tree
  // structure.
  return sizeof(ForecastBucketData) +
         measures.size() * (2 * sizeof(void*) + sizeof(double));
}

void ForecastData::flush() {
  if (Cache::instance->getLogLevel() > 0) {
    assert(!buckets.empty());
    auto fcst = buckets[0].getForecast();
    logger << "Cache writes forecast " << fcst->getForecastItem() << "   "
           << fcst->getForecastLocation() << "   "
           << fcst->getForecastCustomer() << '\n';
  }

  auto dbconnection = Plan::instance().getDBconnection();
  thread_local static DatabaseReader db(dbconnection);
  thread_local static DatabasePreparedStatement stmt;
  thread_local static DatabasePreparedStatement stmt_begin;
  thread_local static DatabasePreparedStatement stmt_end;
  thread_local static short mode = 0;
  for (short attempts = 0; attempts <= 1; ++attempts) try {
      if (mode == 0) {
        // We use a single, dedicated database connection for this
        if (dbconnection.empty())
          mode = 1;
        else {
          mode = 2;
          try {
            stringstream str;
            str << "with cte (st, nd";
            for (auto msr = ForecastMeasure::begin();
                 msr != ForecastMeasure::end(); ++msr) {
              if (msr->getStored()) str << ", " << msr->getName();
            }
            str << ") as ( values ";
            int argcounter = 0;
            for (short r = 0; r < 10; ++r) {
              str << "($" << ++argcounter << ", $" << ++argcounter;
              for (auto msr = ForecastMeasure::begin();
                   msr != ForecastMeasure::end(); ++msr) {
                if (msr->getStored())
                  str << ", $" << ++argcounter << "::numeric";
              }
              if (r < 9)
                str << "),";
              else
                str << ")";
            }
            str << ") insert into forecastplan";
            auto partition = ForecastBase::getForecastPartitionStatic();
            if (partition != -1) str << "_" << partition;
            str << " as fcstplan "
                   "(item_id,location_id,customer_id,startdate,enddate";
            for (auto msr = ForecastMeasure::begin();
                 msr != ForecastMeasure::end(); ++msr) {
              if (msr->getStored()) str << ", " << msr->getName();
            }
            str << ") select $" << (argcounter + 1) << ", $" << (argcounter + 2)
                << ", $" << (argcounter + 3) << ",st::timestamp, nd::timestamp";
            for (auto msr = ForecastMeasure::begin();
                 msr != ForecastMeasure::end(); ++msr) {
              if (msr->getStored()) str << ", " << msr->getName();
            }
            str << " from cte where st is not null "
                   "on conflict(item_id, location_id, customer_id, "
                   "startdate) "
                   "do update set ";
            bool first = true;
            for (auto msr = ForecastMeasure::begin();
                 msr != ForecastMeasure::end(); ++msr) {
              if (!msr->getStored()) continue;
              if (first)
                first = false;
              else
                str << ", ";
              str << msr->getName() << " = excluded." << msr->getName();
            }
            str << " where ";
            first = true;
            for (auto msr = ForecastMeasure::begin();
                 msr != ForecastMeasure::end(); ++msr) {
              if (!msr->getStored()) continue;
              if (first)
                first = false;
              else
                str << " or ";
              str << "fcstplan." << msr->getName()
                  << " is distinct from excluded." << msr->getName();
            }
            stmt = DatabasePreparedStatement(db, "forecastplan_write",
                                             str.str(), argcounter + 3);
            stmt_begin = DatabasePreparedStatement(db, "begin_trx", "begin");
            stmt_end = DatabasePreparedStatement(db, "commit_trx", "commit");
          } catch (exception& e) {
            logger << "Error creating forecastplan export:\n";
            logger << e.what() << '\n';
            db.closeConnection();
          } catch (...) {
            db.closeConnection();
          }
        }
      }

      if (mode == 2) {
        // start a transaction
        DatabaseResult(db, stmt_begin);
        bool first = true;
        int argcount = -1;
        auto argmax = stmt.getArgs();
        for (auto& i : buckets) {
          if (!i.isDirty()) continue;
          if (first) {
            if (!i.getForecast()->getForecastItem() ||
                !i.getForecast()->getForecastLocation() ||
                !i.getForecast()->getForecastCustomer())
              break;
            stmt.setArgument(argmax - 3,
                             i.getForecast()->getForecastItem()->getName());
            stmt.setArgument(argmax - 2,
                             i.getForecast()->getForecastLocation()->getName());
            stmt.setArgument(argmax - 1,
                             i.getForecast()->getForecastCustomer()->getName());
            first = false;
          }
          stmt.setArgument(++argcount, i.getStart());
          stmt.setArgument(++argcount, i.getEnd());
          for (auto msr = ForecastMeasure::begin();
               msr != ForecastMeasure::end(); ++msr) {
            if (!msr->getStored()) continue;
            auto t = i.getValueAndFound(*msr);
            stmt.setArgument(
                ++argcount,
                t.second ? to_string(round(t.first * 1e8) / 1e8) : "");
          }

          if (argcount >= argmax - 4) {
            // All records in prepared statements are full now
            try {
              DatabaseResult(db, stmt);
            } catch (exception& e) {
              logger << "Exception caught when saving a forecast: " << e.what()
                     << '\n';
              DatabaseStatement rollback("rollback");
              db.executeSQL(rollback);
              DatabaseResult(db, stmt_begin);
            }
            argcount = -1;
          }
          i.clearDirty();
        }
        if (argcount > 0) {
          while (argcount < argmax - 4) stmt.setArgument(++argcount, "");
          try {
            DatabaseResult(db, stmt);
          } catch (exception& e) {
            logger << "Exception caught when saving a forecast: " << e.what()
                   << '\n';
            // Roll back current transaction, and start a new one
            DatabaseStatement rollback("rollback");
            db.executeSQL(rollback);
            DatabaseResult(db, stmt_begin);
          }
        }
        // commit the transaction
        DatabaseResult(db, stmt_end);
      }

      // Successful execution
      return;
    } catch (DatabaseBadConnection) {
      // Try again with a new connection
      mode = 0;
      db = DatabaseReader(dbconnection);
    } catch (exception& e) {
      logger << "Exception caught when saving a forecast: " << e.what() << '\n';
      break;
    }
}

ForecastBucket* ForecastBucketData::getOrCreateForecastBucket() const {
  if (!fcstbkt)
    const_cast<ForecastBucketData*>(this)->fcstbkt =
        new ForecastBucket(static_cast<Forecast*>(fcst), dates, index);
  return fcstbkt;
}

void ForecastBucketData::deleteForecastBucket() const {
  delete fcstbkt;
  const_cast<ForecastBucketData*>(this)->fcstbkt = nullptr;
}

void ForecastBucketData::markDirty() {
  if (dirty) return;
  dirty = true;
  getForecast()->markDirty();
}

string ForecastBucketData::toString(bool add_dates, bool sorted) const {
  stringstream o;
  if (sorted) sortMeasures();
  // Use the same precision as we use for all numbers in our postgres
  // database
  o.precision(20);
  o << "{";
  bool first = true;
  if (add_dates) {
    o << R"("startdate":")" << getStart() << R"(","enddate":")" << getEnd()
      << "\"";
    first = false;
  }
  for (auto tmp : measures)
    if (tmp->getMeasure().front() != '-') {
      // Measures starting with '-' are hidden, temporary measures
      if (first) {
        first = false;
        o << "\"" << tmp->getMeasure()
          << "\":" << round(tmp->getValue() * 1e8) / 1e8;
      } else
        o << ",\"" << tmp->getMeasure()
          << "\":" << round(tmp->getValue() * 1e8) / 1e8;
    }
  o << "}";
  return o.str();
}

string ForecastData::toString() const {
  stringstream o;
  o << "[";
  bool first = true;
  for (auto& tmp : buckets) {
    if (first)
      first = false;
    else
      o << ',';
    o << tmp.toString(true);
  }
  o << "]";
  return o.str();
}

CommandSetForecastData::CommandSetForecastData(ForecastBucketData* b,
                                               const ForecastMeasure* k, double)
    : owner(b->getForecast()->getData()), fcstbucket(b), key(k) {
  oldvalue = key->getValue(*b);
}

void Forecast::parse(Object*, const DataValueDict& in, CommandManager* mgr) {
  // TODO currently only the JSON parser calls this function

  // Validate the forecast field
  ForecastBase* forecast = nullptr;
  auto fcstname = in.get(ForecastBucket::tag_forecast);
  if (fcstname) {
    auto tmp = Demand::find(fcstname->getString());
    if (tmp && tmp->hasType<Forecast>()) forecast = static_cast<Forecast*>(tmp);
  }

  if (!forecast) {
    // Validate item
    Item* item = nullptr;
    auto itemname = in.get(Tags::item);
    if (itemname) item = Item::find(itemname->getString());

    // Validate location
    Location* location = nullptr;
    auto locname = in.get(Tags::location);
    if (locname) location = Location::find(locname->getString());

    // Validate customer
    Customer* customer;
    auto custname = in.get(Tags::customer);
    if (custname)
      customer = Customer::find(custname->getString());
    else
      // Customer field can be left blank.
      // This is used in the inventory planning screen.
      customer = Customer::getRoot();

    // Check if a forecast can be found here
    if (item && customer && location)
      forecast = Forecast::findForecast(item, customer, location, true);
    if (!forecast)
      throw DataException(
          "Required fields missing: forecast or item, location and "
          "customer");
  }

  // Pick up the start and end date
  Date startdate;
  Date enddate;
  auto dateval = in.get(Tags::startdate);
  if (dateval) startdate = dateval->getDate();
  dateval = in.get(Tags::enddate);
  if (dateval) enddate = dateval->getDate();
  if (!enddate && !startdate)
    throw DataException("Missing startdate and enddate");
  else if (!enddate)
    enddate = startdate;
  else if (!startdate)
    startdate = enddate;

  // Parse the measures
  // TODO This code accesses internal APIs of JSONDataValueDict
  auto& j = static_cast<const JSONDataValueDict&>(in);
  for (auto i = j.strt; i <= j.nd; ++i) {
    if (j.fields[i].name == "startdate" || j.fields[i].name == "enddate" ||
        j.fields[i].name == "item" || j.fields[i].name == "location" ||
        j.fields[i].name == "customer" || j.fields[i].name == "forecast")
      continue;

    // Find and update the measure
    auto msr = ForecastMeasure::find(j.fields[i].name);
    if (msr)
      msr->disaggregate(forecast, startdate, enddate,
                        j.fields[i].value.getDouble(), false, 0.0, mgr);
  }
}

void ForecastBucketData::validateOverride(const ForecastMeasure* key) {
  // Loop over all leafs, searching for existing overrides
  auto index = getIndex();
  for (auto ch = getForecast()->getLeaves(false, key); ch; ++ch) {
    auto chdata = ch->getData();
    lock_guard<recursive_mutex> exclusive(chdata->lock);
    for (auto mch : chdata->getBuckets()[index].measures) {
      if (mch->getMeasure() == key->getHashedName() &&
          mch->getValue() != -1.0) {
        for (auto mp : measures)
          if (mp->getMeasure() == key->getHashedName()) {
            mp->setValue(0.0);
            break;
          }
        return;
      }
    }
  }
  // No override found at any leaf -> case where all overrides are gone
  measures.erase(key->getHashedName());
}

PyObject* Forecast::setValuePython(PyObject* self, PyObject* args,
                                   PyObject* kwdict) {
  // TODO Can this method be merged with the next one?
  try {
    // Parse the arguments
    PyObject* pystartdate = nullptr;
    PyObject* pyenddate = nullptr;
    if (!PyArg_ParseTuple(args, "|OO:set", &pystartdate, &pyenddate))
      return nullptr;
    Date startdate = Date::infinitePast;
    Date enddate = Date::infiniteFuture;
    if (pystartdate) startdate = PythonData(pystartdate).getDate();
    if (pyenddate) enddate = PythonData(pyenddate).getDate();

    // Update the forecast with each keyword argument
    PyObject *pykey, *pyvalue;
    Py_ssize_t pos = 0;
    while (PyDict_Next(kwdict, &pos, &pykey, &pyvalue)) {
      PythonData key(pykey);
      PythonData value(pyvalue);
      auto msr = ForecastMeasure::find(key.getString());
      if (!msr)
        // TODO is auto-creation of measures really useful?
        msr = new ForecastMeasureAggregated(PooledString(key.getString()));
      msr->disaggregate(static_cast<Forecast*>(self), startdate, enddate,
                        value.getDouble());
    }
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}

PyObject* Forecast::setValuePython2(PyObject*, PyObject*, PyObject* kwargs) {
  // Keyword arguments are:
  //  bucket, startdate, enddate, item, location, customer, plus measure
  //  names
  Item* item = nullptr;
  Location* location = nullptr;
  Customer* customer = nullptr;
  Date startdate = Date::infinitePast;
  Date enddate = Date::infiniteFuture;
  bool date_ok = false;
  try {
    auto py_val = PyDict_GetItemString(kwargs, "item");
    if (!PyObject_TypeCheck(py_val, Item::metadata->pythonClass))
      throw DataException("item argument must be of type item");
    else
      item = static_cast<Item*>(py_val);
    py_val = PyDict_GetItemString(kwargs, "location");
    if (!PyObject_TypeCheck(py_val, Location::metadata->pythonClass))
      throw DataException("location argument must be of type location");
    else
      location = static_cast<Location*>(py_val);
    py_val = PyDict_GetItemString(kwargs, "customer");
    if (!PyObject_TypeCheck(py_val, Customer::metadata->pythonClass))
      throw DataException("customer argument must be of type customer");
    else
      customer = static_cast<Customer*>(py_val);
    py_val = PyDict_GetItemString(kwargs, "bucket");
    if (py_val) {
      auto bucket = CalendarBucket::getByName(PythonData(py_val).getString());
      if (bucket) {
        startdate = bucket->getStart();
        enddate = bucket->getEnd();
        date_ok = true;
      }
    }
    if (startdate == Date::infinitePast && enddate == Date::infiniteFuture) {
      py_val = PyDict_GetItemString(kwargs, "startdate");
      if (py_val) {
        startdate = PythonData(py_val).getDate();
        date_ok = true;
      }
      py_val = PyDict_GetItemString(kwargs, "enddate");
      if (py_val) {
        enddate = PythonData(py_val).getDate();
        date_ok = true;
      } else if (startdate)
        enddate = startdate;
    }

    if (date_ok && item && location && customer) {
      // Update the forecast with each keyword argument
      auto fcst = Forecast::findForecast(item, customer, location, true);
      PyObject *pykey, *pyvalue;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwargs, &pos, &pykey, &pyvalue)) {
        PythonData key(pykey);
        PythonData value(pyvalue);
        const auto& keystring = key.getString();
        if (keystring != "item" && keystring != "customer" &&
            keystring != "location" && keystring != "bucket" &&
            keystring != "startdate" && keystring != "enddate") {
          auto msr = ForecastMeasure::find(keystring);
          if (msr) {
            msr->disaggregate(fcst, startdate, enddate, value.getDouble());
          }
        }
      }
    }
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}

PyObject* Forecast::getValuePython(PyObject* self, PyObject* args, PyObject*) {
  try {
    // Parse the arguments
    PyObject* pydate;
    char* pymeasure;
    if (!PyArg_ParseTuple(args, "Os:get", &pydate, &pymeasure)) return nullptr;
    Date thedate = PythonData(pydate).getDate();
    string measure = pymeasure;

    // Retrieve the forecast with each keyword argument
    auto msr = ForecastMeasure::find(measure);
    if (!msr) throw DataException("Unknown measure");
    auto fcstdata = static_cast<Forecast*>(self)->getData();
    lock_guard<recursive_mutex> exclusive(fcstdata->lock);
    for (auto& bckt : fcstdata->getBuckets()) {
      if (bckt.getDates().within(thedate))
        return PythonData(bckt.getValue(*msr));
    }
    throw DataException("Couldn't find time bucket");
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}

void ForecastBase::inspect(const string& msg) const {
  logger << "Inspecting forecast " << getForecastName() << " ("
         << getForecastItem() << ", " << getForecastLocation() << ", "
         << getForecastCustomer() << ": ";
  if (!msg.empty()) logger << msg;
  logger << '\n';

  auto fcstdata = getData();
  lock_guard<recursive_mutex> exclusive(fcstdata->lock);
  for (auto& bckt : fcstdata->getBuckets())
    logger << "    " << bckt.getStart() << " - " << bckt.getEnd() << ": "
           << bckt.toString(false) << '\n';
}

PyObject* Forecast::inspectPython(PyObject* self, PyObject* args) {
  try {
    char* msg = nullptr;
    if (!PyArg_ParseTuple(args, "|s:inspect", &msg)) return nullptr;

    static_cast<Forecast*>(self)->inspect(msg ? msg : "");

    return Py_BuildValue("");
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

PyObject* Forecast::saveForecast(PyObject*, PyObject* args) {
  // Pick up arguments
  const char* filename = "plan.out";
  if (!PyArg_ParseTuple(args, "s:saveforecast", &filename)) return nullptr;

  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;

  // Execute and catch exceptions
  ofstream textoutput;
  try {
    // Open the output file
    textoutput.open(filename, ios::out);

    struct {
      bool operator()(ForecastBase* const& a, ForecastBase* const& b) {
        if (a->getForecastItem() != b->getForecastItem()) {
          if (a->getForecastItem()) {
            if (b->getForecastItem())
              return a->getForecastItem()->getName() <
                     b->getForecastItem()->getName();
            else
              return false;
          } else
            return true;
        } else if (a->getForecastLocation() != b->getForecastLocation()) {
          if (a->getForecastLocation()) {
            if (b->getForecastLocation())
              return a->getForecastLocation()->getName() <
                     b->getForecastLocation()->getName();
            else
              return false;
          } else
            return true;
        } else if (a->getForecastCustomer()) {
          if (b->getForecastCustomer())
            return a->getForecastCustomer()->getName() <
                   b->getForecastCustomer()->getName();
          else
            return false;
        } else
          return true;
      }
    } mysort;

    // This is quite memory&cpu-intensive as we need to fill and sort a
    // vector with pointers to all forecasts. Since we expect to call this
    // function only small datasets we can live with this.
    vector<ForecastBase*> sortedforecast;
    for (auto fcst : Forecast::getForecasts()) sortedforecast.push_back(&*fcst);
    sort(sortedforecast.begin(), sortedforecast.end(), mysort);

    // Write out all forecasts
    for (auto& fcst : sortedforecast) {
      auto fcstdata = fcst->getData();
      lock_guard<recursive_mutex> exclusive(fcstdata->lock);
      for (auto& bckt : fcstdata->getBuckets())
        textoutput << fcst->getForecastItem() << "\t"
                   << fcst->getForecastLocation() << "\t"
                   << fcst->getForecastCustomer() << "\t" << bckt.getStart()
                   << "\t" << bckt.getEnd() << "\t" << bckt.toString(false)
                   << '\n';
    }

    // Close the output file
    textoutput.close();
  } catch (...) {
    if (textoutput.is_open()) textoutput.close();
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

PyObject* ForecastBucket::getMeasurePython(PyObject* self, PyObject* args,
                                           PyObject*) {
  try {
    // Parse the arguments
    char* pymeasure = nullptr;
    if (!PyArg_ParseTuple(args, "s:set", &pymeasure)) return nullptr;
    if (!pymeasure) return nullptr;
    auto msr = ForecastMeasure::find(pymeasure);
    if (!msr) return nullptr;
    auto me = static_cast<ForecastBucket*>(self);
    auto fcstdata = me->getForecast()->getData();
    lock_guard<recursive_mutex> exclusive(fcstdata->lock);
    return PythonData(
        msr->getValue(fcstdata->getBuckets()[me->getBucketIndex()]));
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}

PyObject* ForecastBucket::setMeasurePython(PyObject* self, PyObject*,
                                           PyObject* kwdict) {
  try {
    // Update the forecastbucket with each keyword argument
    PyObject *pykey, *pyvalue;
    Py_ssize_t pos = 0;
    auto fcstbucket = static_cast<ForecastBucket*>(self);
    auto fcst = fcstbucket->getForecast();
    while (PyDict_Next(kwdict, &pos, &pykey, &pyvalue)) {
      PythonData key(pykey);
      PythonData value(pyvalue);
      auto msr = ForecastMeasure::find(key.getString());
      if (!msr)
        // TODO is auto-creation of measures really useful?
        msr = new ForecastMeasureAggregated(PooledString(key.getString()));
      msr->disaggregate(fcst, fcstbucket->getStartDate(),
                        fcstbucket->getEndDate(), value.getDouble());
    }
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}

}  // namespace frepple
