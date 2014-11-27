/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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


int Resource::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("resource", "resources", reader, writer);

  // Initialize the Python class
  FreppleCategory<Resource>::getType().addMethod("plan", Resource::plan, METH_VARARGS,
      "Return an iterator with tuples representing the resource plan in each time bucket");
  return FreppleCategory<Resource>::initialize();
}


int ResourceDefault::initialize()
{
  // Initialize the metadata
  ResourceDefault::metadata = new MetaClass(
    "resource",
    "resource_default",
    Object::createString<ResourceDefault>,
    true);

  // Initialize the Python class
  return FreppleClass<ResourceDefault,Resource>::initialize();
}


int ResourceInfinite::initialize()
{
  // Initialize the metadata
  ResourceInfinite::metadata = new MetaClass(
    "resource",
    "resource_infinite",
    Object::createString<ResourceInfinite>);

  // Initialize the Python class
  return FreppleClass<ResourceInfinite,Resource>::initialize();
}


int ResourceBuckets::initialize()
{
  // Initialize the metadata
  ResourceBuckets::metadata = new MetaClass(
    "resource",
    "resource_buckets",
    Object::createString<ResourceBuckets>);

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
    if (oo->getType() == 4)
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


DECLARE_EXPORT void Resource::setMaximumCalendar(CalendarDouble* c)
{
  // Resetting the same calendar
  if (size_max_cal == c) return;

  // Mark as changed
  setChanged();

  // Remove the current max events.
  for (loadplanlist::iterator oo=loadplans.begin(); oo!=loadplans.end(); )
    if (oo->getType() == 4)
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
  for (CalendarDouble::EventIterator x(size_max_cal); x.getDate()<Date::infiniteFuture; ++x)
    if (curMax != x.getValue())
    {
      curMax = x.getValue();
      loadplanlist::EventMaxQuantity *newBucket =
        new loadplanlist::EventMaxQuantity(x.getDate(), &loadplans, curMax);
      loadplans.insert(newBucket);
    }
}


DECLARE_EXPORT void ResourceBuckets::setMaximumCalendar(CalendarDouble* c)
{
  // Resetting the same calendar
  if (size_max_cal == c) return;

  // Mark as changed
  setChanged();

  // Remove the current set-onhand events.
  for (loadplanlist::iterator oo=loadplans.begin(); oo!=loadplans.end(); )
    if (oo->getType() == 2)
    {
      loadplans.erase(&(*oo));
      delete &(*(oo++));
    }
    else ++oo;

  // Create timeline structures for every bucket.
  size_max_cal = c;
  double v = 0.0;
  for (CalendarDouble::EventIterator x(size_max_cal); x.getDate()<Date::infiniteFuture; ++x)
    if (v != x.getValue())
    {
      v = x.getValue();
      loadplanlist::EventSetOnhand *newBucket =
        new loadplanlist::EventSetOnhand(x.getDate(), v);
      loadplans.insert(newBucket);
    }
}


DECLARE_EXPORT void Resource::writeElement(Serializer* o, const Keyword& tag, mode m) const
{
  // Write a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL)
    o->BeginObject(tag, Tags::tag_name, getName());

  // Write my fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Resource>::writeElement(o, tag);
  if (getMaximum() != 1)
    o->writeElement(Tags::tag_maximum, getMaximum());
  o->writeElement(Tags::tag_maximum_calendar, size_max_cal);
  if (getMaxEarly() != TimePeriod(defaultMaxEarly))
    o->writeElement(Tags::tag_maxearly, getMaxEarly());
  if (getCost() != 0.0) o->writeElement(Tags::tag_cost, getCost());
  o->writeElement(Tags::tag_location, loc);
  if (!getSetup().empty()) o->writeElement(Tags::tag_setup, getSetup());
  if (getSetupMatrix())
    o->writeElement(Tags::tag_setupmatrix, getSetupMatrix());
  Plannable::writeElement(o, tag);

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write extra plan information
  loadplanlist::const_iterator i = loadplans.begin();
  if (o->getContentType() == Serializer::PLAN  && i!=loadplans.end())
  {
    o->BeginList(Tags::tag_loadplans);
    for (; i!=loadplans.end(); ++i)
      if (i->getType()==1)
      {
        const LoadPlan *lp = static_cast<const LoadPlan*>(&*i);
        o->BeginObject(Tags::tag_loadplan);
        o->writeElement(Tags::tag_date, lp->getDate());
        o->writeElement(Tags::tag_quantity, lp->getQuantity());
        o->writeElement(Tags::tag_onhand, lp->getOnhand());
        o->writeElement(Tags::tag_minimum, lp->getMin());
        o->writeElement(Tags::tag_maximum, lp->getMax());
        o->writeElement(Tags::tag_operationplan, &*(lp->getOperationPlan()), FULL);
        o->EndObject(Tags::tag_loadplan);
      }
    o->EndList(Tags::tag_loadplans);
    bool first = true;
    for (Problem::const_iterator j = Problem::begin(const_cast<Resource*>(this), true); j!=Problem::end(); ++j)
    {
      if (first)
      {
        first = false;
        o->BeginList(Tags::tag_problems);
      }
      o->writeElement(Tags::tag_problem, *j, FULL);
    }
    if (!first) o->EndList(Tags::tag_problems);
  }

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Resource::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_load)
      && pIn.getParentElement().first.isA(Tags::tag_loads))
  {
    Load* l = new Load();
    l->setResource(this);
    pIn.readto(&*l);
  }
  else if (pAttr.isA(Tags::tag_resourceskill)
      && pIn.getParentElement().first.isA(Tags::tag_resourceskills))
  {
    ResourceSkill *s =
      dynamic_cast<ResourceSkill*>(MetaCategory::ControllerDefault(ResourceSkill::metadata,pIn.getAttributes()));
    if (s) s->setResource(this);
    pIn.readto(s);
  }
  else if (pAttr.isA(Tags::tag_maximum_calendar))
    pIn.readto( Calendar::reader(Calendar::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_loadplans))
    pIn.IgnoreElement();
  else if (pAttr.isA(Tags::tag_location))
    pIn.readto( Location::reader(Location::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_setupmatrix))
    pIn.readto( SetupMatrix::reader(SetupMatrix::metadata,pIn.getAttributes()) );
  if (pAttr.isA(Tags::tag_skill)
      && pIn.getParentElement().first.isA(Tags::tag_skills))
    pIn.readto( Skill::reader(Skill::metadata,pIn.getAttributes()) );
  else
  {
    PythonDictionary::read(pIn, pAttr, getDict());
    HasHierarchy<Resource>::beginElement(pIn, pAttr);
  }
}


DECLARE_EXPORT void Resource::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  /* Note that while restoring the size, the parent's size is NOT
     automatically updated. The getDescription of the 'set_size' function may
     suggest this would be the case... */
  if (pAttr.isA (Tags::tag_maximum))
    setMaximum(pElement.getDouble());
  else if (pAttr.isA (Tags::tag_maximum_calendar))
  {
    CalendarDouble *c = dynamic_cast<CalendarDouble*>(pIn.getPreviousObject());
    if (c)
      setMaximumCalendar(c);
    else
    {
      Calendar *c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
      if (!c)
        throw LogicException("Incorrect object type during read operation");
      throw DataException("Calendar '" + c->getName() +
          "' has invalid type for use as resource max calendar");
    }
  }
  else if (pAttr.isA (Tags::tag_maxearly))
    setMaxEarly(pElement.getTimeperiod());
  else if (pAttr.isA (Tags::tag_cost))
    setCost(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_location))
  {
    Location * d = dynamic_cast<Location*>(pIn.getPreviousObject());
    if (d) setLocation(d);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA (Tags::tag_setup))
    setSetup(pElement.getString());
  else if (pAttr.isA(Tags::tag_setupmatrix))
  {
    SetupMatrix * d = dynamic_cast<SetupMatrix*>(pIn.getPreviousObject());
    if (d) setSetupMatrix(d);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
  {
    Plannable::endElement(pIn, pAttr, pElement);
    HasDescription::endElement(pIn, pAttr, pElement);
    HasHierarchy<Resource>::endElement (pIn, pAttr, pElement);
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


DECLARE_EXPORT void ResourceInfinite::writeElement
(Serializer* o, const Keyword &tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEAD && m != NOHEADTAIL) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Resource::writeElement(o, tag, NOHEAD);
}


DECLARE_EXPORT void ResourceBuckets::writeElement
(Serializer *o, const Keyword &tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEAD && m != NOHEADTAIL) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Resource::writeElement(o, tag, NOHEAD);
}



DECLARE_EXPORT PyObject* Resource::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_description))
    return PythonObject(getDescription());
  if (attr.isA(Tags::tag_category))
    return PythonObject(getCategory());
  if (attr.isA(Tags::tag_subcategory))
    return PythonObject(getSubCategory());
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  if (attr.isA(Tags::tag_owner))
    return PythonObject(getOwner());
  if (attr.isA(Tags::tag_location))
    return PythonObject(getLocation());
  if (attr.isA(Tags::tag_maximum))
    return PythonObject(getMaximum());
  if (attr.isA(Tags::tag_maximum_calendar))
    return PythonObject(getMaximumCalendar());
  if (attr.isA(Tags::tag_maxearly))
    return PythonObject(getMaxEarly());
  if (attr.isA(Tags::tag_cost))
    return PythonObject(getCost());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(getHidden());
  if (attr.isA(Tags::tag_loadplans))
    return new LoadPlanIterator(this);
  if (attr.isA(Tags::tag_loads))
    return new LoadIterator(this);
  if (attr.isA(Tags::tag_setup))
    return PythonObject(getSetup());
  if (attr.isA(Tags::tag_setupmatrix))
    return PythonObject(getSetupMatrix());
  if (attr.isA(Tags::tag_level))
    return PythonObject(getLevel());
  if (attr.isA(Tags::tag_cluster))
    return PythonObject(getCluster());
  if (attr.isA(Tags::tag_members))
    return new ResourceIterator(this);
  if (attr.isA(Tags::tag_resourceskills))
    return new ResourceSkillIterator(this);
  return NULL;
}


DECLARE_EXPORT int Resource::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_description))
    setDescription(field.getString());
  else if (attr.isA(Tags::tag_category))
    setCategory(field.getString());
  else if (attr.isA(Tags::tag_subcategory))
    setSubCategory(field.getString());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(Resource::metadata))
    {
      PyErr_SetString(PythonDataException, "resource owner must be of type resource");
      return -1;
    }
    Resource* y = static_cast<Resource*>(static_cast<PyObject*>(field));
    setOwner(y);
  }
  else if (attr.isA(Tags::tag_location))
  {
    if (!field.check(Location::metadata))
    {
      PyErr_SetString(PythonDataException, "resource location must be of type location");
      return -1;
    }
    Location* y = static_cast<Location*>(static_cast<PyObject*>(field));
    setLocation(y);
  }
  else if (attr.isA(Tags::tag_maximum))
    setMaximum(field.getDouble());
  else if (attr.isA(Tags::tag_maximum_calendar))
  {
    if (!field.check(CalendarDouble::metadata))
    {
      PyErr_SetString(PythonDataException, "resource maximum_calendar must be of type calendar_double");
      return -1;
    }
    CalendarDouble* y = static_cast<CalendarDouble*>(static_cast<PyObject*>(field));
    setMaximumCalendar(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    setHidden(field.getBool());
  else if (attr.isA(Tags::tag_cost))
    setCost(field.getDouble());
  else if (attr.isA(Tags::tag_maxearly))
    setMaxEarly(field.getTimeperiod());
  else if (attr.isA(Tags::tag_setup))
    setSetup(field.getString());
  else if (attr.isA(Tags::tag_setupmatrix))
  {
    if (!field.check(SetupMatrix::metadata))
    {
      PyErr_SetString(PythonDataException, "resource setup_matrix must be of type setup_matrix");
      return -1;
    }
    SetupMatrix* y = static_cast<SetupMatrix*>(static_cast<PyObject*>(field));
    setSetupMatrix(y);
  }
  else
    return -1;  // Error
  return 0;  // OK
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
  PythonType& x = PythonExtension<Resource::PlanIterator>::getType();
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
    while (ldplaniter != res->getLoadPlans().end() && ldplaniter->getType() != 2)
      ++ldplaniter;
  }
  else
  {
    // Start date of the first bucket
    end_date = PyIter_Next(bucketiterator);
    if (!end_date) throw LogicException("Expecting at least two dates as argument");
    cur_date = PythonObject(end_date).getDate();
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
      unsigned short tp = ldplaniter->getType();
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
        start_date = PythonObject(ldplaniter->getDate());
      bucket_available = ldplaniter->getOnhand();
    }
    // Advance the loadplan iterator to the start of the next bucket
    ++ldplaniter;
    while (ldplaniter != res->getLoadPlans().end() && ldplaniter->getType() != 2)
    {
      if (ldplaniter->getType() == 1)
        bucket_load -= ldplaniter->getQuantity();
      ++ldplaniter;
    }
    if (ldplaniter == res->getLoadPlans().end())
      end_date = PythonObject(Date::infiniteFuture);
    else
      end_date = PythonObject(ldplaniter->getDate());
  }
  else
  {
    // Get the start and end date of the current bucket
    if (start_date) Py_DECREF(start_date);
    start_date = end_date;
    end_date = PyIter_Next(bucketiterator);
    if (!end_date) return NULL;
    cur_date = PythonObject(end_date).getDate();

    // Measure from beginning of the bucket till the first event in this bucket
    if (ldplaniter != res->getLoadPlans().end() && ldplaniter->getDate() < cur_date)
      update(ldplaniter->getDate());

    // Advance the loadplan iterator to the next event date
    while (ldplaniter != res->getLoadPlans().end() && ldplaniter->getDate() <= cur_date)
    {
      // Measure from the previous event till the current one
      update(ldplaniter->getDate());

      // Process the event
      unsigned short tp = ldplaniter->getType();
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
