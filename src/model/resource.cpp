/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Resource> DECLARE_EXPORT Tree utils::HasName<Resource>::st;
DECLARE_EXPORT const MetaCategory* Resource::metadata;
DECLARE_EXPORT const MetaClass* ResourceDefault::metadata;
DECLARE_EXPORT const MetaClass* ResourceInfinite::metadata;
DECLARE_EXPORT const MetaClass* ResourceBuckets::metadata;

Duration Resource::defaultMaxEarly(100*86400L);


int Resource::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Resource>("resource", "resources", reader, finder);
  registerFields<Resource>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  FreppleCategory<Resource>::getPythonType().addMethod("plan", Resource::plan, METH_VARARGS,
      "Return an iterator with tuples representing the resource plan in each time bucket");
  return FreppleCategory<Resource>::initialize();
}


int ResourceDefault::initialize()
{
  // Initialize the metadata
  ResourceDefault::metadata = MetaClass::registerClass<ResourceDefault>(
    "resource", "resource_default",
    Object::create<ResourceDefault>,
    true
    );
  
  // Initialize the Python class
  return FreppleClass<ResourceDefault,Resource>::initialize();
}


int ResourceInfinite::initialize()
{
  // Initialize the metadata
  ResourceInfinite::metadata = MetaClass::registerClass<ResourceInfinite>(
    "resource", "resource_infinite",
    Object::create<ResourceInfinite>
    );

  // Initialize the Python class
  return FreppleClass<ResourceInfinite,Resource>::initialize();
}


int ResourceBuckets::initialize()
{
  // Initialize the metadata
  ResourceBuckets::metadata = MetaClass::registerClass<ResourceBuckets>(
    "resource",
    "resource_buckets",
    Object::create<ResourceBuckets>);

  // Initialize the Python class
  return FreppleClass<ResourceBuckets,Resource>::initialize();
}


DECLARE_EXPORT void Resource::setMaximum(double m)
{
  if (m < 0)
    throw DataException("Maximum capacity for resource '" + getName() + "' must be postive");

  // There is already a maximum calendar.
  if (size_max_cal)
  {
    // We update the field, but don't use it yet.
    size_max = m;
    return;
  }

  // Mark as changed
  setChanged();

  // Set field
  size_max = m;

  // Create or update a single timeline max event
  for (loadplanlist::iterator oo=loadplans.begin(); oo!=loadplans.end(); oo++)
    if (oo->getEventType() == 4)
    {
      // Update existing event
      static_cast<loadplanlist::EventMaxQuantity *>(&*oo)->setMax(size_max);
      return;
    }
  // Create new event
  loadplanlist::EventMaxQuantity *newEvent =
    new loadplanlist::EventMaxQuantity(Date::infinitePast, &loadplans, size_max);
  loadplans.insert(newEvent);
}


DECLARE_EXPORT void Resource::setMaximumCalendar(Calendar* c)
{
  // Resetting the same calendar
  if (size_max_cal == c) return;

  // Mark as changed
  setChanged();

  // Remove the current max events.
  for (loadplanlist::iterator oo=loadplans.begin(); oo!=loadplans.end(); )
    if (oo->getEventType() == 4)
    {
      loadplans.erase(&(*oo));
      delete &(*(oo++));
    }
    else ++oo;

  // Null pointer passed. Change back to time independent maximum size.
  if (!c)
  {
    setMaximum(size_max);
    return;
  }

  // Create timeline structures for every bucket.
  size_max_cal = c;
  double curMax = 0.0;
  for (CalendarDefault::EventIterator x(size_max_cal); x.getDate()<Date::infiniteFuture; ++x)
    if (curMax != x.getValue())
    {
      curMax = x.getValue();
      loadplanlist::EventMaxQuantity *newBucket =
        new loadplanlist::EventMaxQuantity(x.getDate(), &loadplans, curMax);
      loadplans.insert(newBucket);
    }
}


DECLARE_EXPORT void ResourceBuckets::setMaximumCalendar(Calendar* c)
{
  // Resetting the same calendar
  if (size_max_cal == c) return;

  // Mark as changed
  setChanged();

  // Remove the current set-onhand events.
  for (loadplanlist::iterator oo=loadplans.begin(); oo!=loadplans.end(); )
    if (oo->getEventType() == 2)
    {
      loadplans.erase(&(*oo));
      delete &(*(oo++));
    }
    else ++oo;

  // Create timeline structures for every bucket.
  size_max_cal = c;
  double v = 0.0;
  for (CalendarDefault::EventIterator x(size_max_cal); x.getDate()<Date::infiniteFuture; ++x)
    if (v != x.getValue())
    {
      v = x.getValue();
      loadplanlist::EventSetOnhand *newBucket =
        new loadplanlist::EventSetOnhand(x.getDate(), v);
      loadplans.insert(newBucket);
    }
}


DECLARE_EXPORT void Resource::deleteOperationPlans(bool deleteLocked)
{
  // Delete the operationplans
  for (loadlist::iterator i=loads.begin(); i!=loads.end(); ++i)
    OperationPlan::deleteOperationPlans(i->getOperation(),deleteLocked);

  // Mark to recompute the problems
  setChanged();
}


DECLARE_EXPORT Resource::~Resource()
{
  // Delete all operationplans
  // An alternative logic would be to delete only the loadplans for this
  // resource and leave the rest of the plan untouched. The currently
  // implemented method is way more drastic...
  deleteOperationPlans(true);

  // The Load and ResourceSkill objects are automatically deleted by the
  // destructor of the Association list class.
}


DECLARE_EXPORT void Resource::updateSetups(const LoadPlan* ldplan)
{
  // No updating required this resource
  if (!getSetupMatrix() || (ldplan && ldplan->getOperationPlan()->getOperation() != OperationSetup::setupoperation))
    return;

  // Update later setup opplans
  OperationPlan *opplan = ldplan ? ldplan->getOperationPlan() : NULL;
  loadplanlist::const_iterator i = ldplan ?
      getLoadPlans().begin(ldplan) :
      getLoadPlans().begin();
  string prevsetup = ldplan ? ldplan->getSetup() : getSetup();
  for (; i != getLoadPlans().end(); ++i)
  {
    const LoadPlan* l = dynamic_cast<const LoadPlan*>(&*i);
    if (l && !l->getLoad()->getSetup().empty()
        && l->getOperationPlan()->getOperation() == OperationSetup::setupoperation
        && l->getOperationPlan() != opplan
        && !l->isStart())
    {
      // Next conversion operation
      OperationPlanState x = l->getOperationPlan()->getOperation()->setOperationPlanParameters(
          l->getOperationPlan(),
          l->getOperationPlan()->getQuantity(),
          Date::infinitePast,
          l->getOperationPlan()->getDates().getEnd(),
          true,
          false);
      if (x.start != l->getOperationPlan()->getDates().getStart())
        // We need to change a setup plan
        l->getOperationPlan()->restore(x);
      else if (ldplan && x.start == l->getOperationPlan()->getDates().getStart())
        // We found a setup plan that doesn't need updating. Later setup plans
        // won't require updating either
        return;
    }
  }
}


extern "C" PyObject* Resource::plan(PyObject *self, PyObject *args)
{
  // Get the resource model
  Resource* resource = static_cast<Resource*>(self);

  // Parse the Python arguments
  PyObject* buckets = NULL;
  int ok = PyArg_ParseTuple(args, "O:plan", &buckets);
  if (!ok) return NULL;

  // Validate that the argument supports iteration.
  PyObject* iter = PyObject_GetIter(buckets);
  if (!iter)
  {
    PyErr_Format(PyExc_AttributeError,"Argument to resource.plan() must support iteration");
    return NULL;
  }

  // Return the iterator
  return new Resource::PlanIterator(resource, iter);
}


int Resource::PlanIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<Resource::PlanIterator>::getPythonType();
  x.setName("resourceplanIterator");
  x.setDoc("frePPLe iterator for resourceplan");
  x.supportiter();
  return x.typeReady();
}


Resource::PlanIterator::PlanIterator(Resource* r, PyObject* o) :
  res(r), bucketiterator(o), ldplaniter(r ? r->getLoadPlans().begin() : NULL),
  cur_setup(0.0), cur_load(0.0), cur_size(0.0), start_date(NULL), end_date(NULL)
{
  if (!r)
  {
    bucketiterator = NULL;
    throw LogicException("Creating resource plan iterator for NULL resource");
  }

  // Count differently for bucketized and continuous resources
  bucketized = (r->getType() == *ResourceBuckets::metadata);

  if (bucketized)
  {
    while (ldplaniter != res->getLoadPlans().end() && ldplaniter->getEventType() != 2)
      ++ldplaniter;
  }
  else
  {
    // Start date of the first bucket
    end_date = PyIter_Next(bucketiterator);
    if (!end_date) throw LogicException("Expecting at least two dates as argument");
    cur_date = PythonData(end_date).getDate();
    prev_date = cur_date;

    // A flag to remember whether this resource has an unavailability calendar.
    hasUnavailability = r->getLocation() && r->getLocation()->getAvailable();
    if (hasUnavailability)
    {
      unavailableIterator = Calendar::EventIterator(res->getLocation()->getAvailable(), cur_date);
      prev_value = unavailableIterator.getBucket() ?
        unavailableIterator.getBucket()->getBool() :
        res->getLocation()->getAvailable()->getDefault()!=0;
    }

    // Advance loadplan iterator just beyond the starting date
    while (ldplaniter != res->getLoadPlans().end() && ldplaniter->getDate() <= cur_date)
    {
      unsigned short tp = ldplaniter->getEventType();
      if (tp == 4)
        // New max size
        cur_size = ldplaniter->getMax();
      else if (tp == 1)
      {
        const LoadPlan* ldplan = dynamic_cast<const LoadPlan*>(&*ldplaniter);
        if (ldplan->getOperationPlan()->getOperation() == OperationSetup::setupoperation)
          // Setup starting or ending
          cur_setup = ldplan->getQuantity() < 0 ? 0.0 : cur_size;
        else
          // Normal load
          cur_load = ldplan->getOnhand();
      }
      ++ldplaniter;
    }
  }
}


Resource::PlanIterator::~PlanIterator()
{
  if (bucketiterator && !bucketized) Py_DECREF(bucketiterator);
  if (start_date) Py_DECREF(start_date);
  if (end_date) Py_DECREF(end_date);
}


void Resource::PlanIterator::update(Date till)
{
  long timedelta;
  if (hasUnavailability)
  {
    // Advance till the iterator exceeds the target date
    while (unavailableIterator.getDate() <= till)
    {
      timedelta = unavailableIterator.getDate() - prev_date;
      if (prev_value)
      {
        bucket_available += cur_size * timedelta;
        bucket_load += cur_load * timedelta;
        bucket_setup += cur_setup * timedelta;
      }
      else
        bucket_unavailable += cur_size * timedelta;
      prev_value = unavailableIterator.getBucket() ?
        unavailableIterator.getBucket()->getBool() :
        res->getLocation()->getAvailable()->getDefault()!=0;
      prev_date = unavailableIterator.getDate();
      ++unavailableIterator;
    }
    // Account for time period finishing at the "till" date
    timedelta = till - prev_date;
    if (prev_value)
    {
      bucket_available += cur_size * timedelta;
      bucket_load += cur_load * timedelta;
      bucket_setup += cur_setup * timedelta;
    }
    else
      bucket_unavailable += cur_size * timedelta;
  }
  else
  {
    // All time is available on this resource
    timedelta = till - prev_date;
    bucket_available += cur_size * timedelta;
    bucket_load += cur_load  * timedelta;
    bucket_setup += cur_setup * timedelta;
  }
  // Remember till which date we already have reported
  prev_date = till;
}


PyObject* Resource::PlanIterator::iternext()
{
  // Reset counters
  bucket_available = 0.0;
  bucket_unavailable = 0.0;
  bucket_load = 0.0;
  bucket_setup = 0.0;

  if (bucketized)
  {
    if (ldplaniter == res->getLoadPlans().end())
      // No more resource buckets
      return NULL;
    else
    {
      // At this point ldplaniter points to a bucket start event.
      if (start_date) Py_DECREF(start_date);
      if (end_date)
        start_date = end_date;
      else
        start_date = PythonData(ldplaniter->getDate());
      bucket_available = ldplaniter->getOnhand();
    }
    // Advance the loadplan iterator to the start of the next bucket
    ++ldplaniter;
    while (ldplaniter != res->getLoadPlans().end() && ldplaniter->getEventType() != 2)
    {
      if (ldplaniter->getEventType() == 1)
        bucket_load -= ldplaniter->getQuantity();
      ++ldplaniter;
    }
    if (ldplaniter == res->getLoadPlans().end())
      end_date = PythonData(Date::infiniteFuture);
    else
      end_date = PythonData(ldplaniter->getDate());
  }
  else
  {
    // Get the start and end date of the current bucket
    if (start_date) Py_DECREF(start_date);
    start_date = end_date;
    end_date = PyIter_Next(bucketiterator);
    if (!end_date) return NULL;
    cur_date = PythonData(end_date).getDate();

    // Measure from beginning of the bucket till the first event in this bucket
    if (ldplaniter != res->getLoadPlans().end() && ldplaniter->getDate() < cur_date)
      update(ldplaniter->getDate());

    // Advance the loadplan iterator to the next event date
    while (ldplaniter != res->getLoadPlans().end() && ldplaniter->getDate() <= cur_date)
    {
      // Measure from the previous event till the current one
      update(ldplaniter->getDate());

      // Process the event
      unsigned short tp = ldplaniter->getEventType();
      if (tp == 4)
        // New max size
        cur_size = ldplaniter->getMax();
      else if (tp == 1)
      {
        const LoadPlan* ldplan = dynamic_cast<const LoadPlan*>(&*ldplaniter);
        assert(ldplan);
        if (ldplan->getOperationPlan()->getOperation() == OperationSetup::setupoperation)
          // Setup starting or ending
          cur_setup = ldplan->getQuantity() < 0 ? 0.0 : cur_size;
        else
          // Normal load
          cur_load = ldplan->getOnhand();
      }

      // Move to the next event
      ++ldplaniter;
    }

    // Measure from the previous event till the end of the bucket
    update(cur_date);

    // Convert from seconds to hours
    bucket_available /= 3600;
    bucket_load /= 3600;
    bucket_unavailable /= 3600;
    bucket_setup /= 3600;
  }

  // Return the result
  return Py_BuildValue("{s:O,s:O,s:d,s:d,s:d,s:d,s:d}",
    "start", start_date,
    "end", end_date,
    "available", bucket_available,
    "load", bucket_load,
    "unavailable", bucket_unavailable,
    "setup", bucket_setup,
    "free", bucket_available - bucket_load - bucket_setup);
}

}
