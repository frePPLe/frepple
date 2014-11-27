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

template<class Operation> DECLARE_EXPORT Tree utils::HasName<Operation>::st;
DECLARE_EXPORT const MetaCategory* Operation::metadata;
DECLARE_EXPORT const MetaClass* OperationFixedTime::metadata,
               *OperationTimePer::metadata,
               *OperationRouting::metadata,
               *OperationSplit::metadata,
               *OperationAlternate::metadata,
               *OperationSetup::metadata;
DECLARE_EXPORT Operation::Operationlist Operation::nosubOperations;
DECLARE_EXPORT const Operation* OperationSetup::setupoperation;


int Operation::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("operation", "operations", reader, writer);

  // Initialize the Python class
  return FreppleCategory<Operation>::initialize();
}


int OperationFixedTime::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass("operation", "operation_fixed_time",
      Object::createString<OperationFixedTime>, true);

  // Initialize the Python class
  return FreppleClass<OperationFixedTime,Operation>::initialize();
}


int OperationTimePer::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass("operation", "operation_time_per",
      Object::createString<OperationTimePer>);

  // Initialize the Python class
  return FreppleClass<OperationTimePer,Operation>::initialize();
}


int OperationSplit::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass("operation", "operation_split",
      Object::createString<OperationSplit>);

  // Initialize the Python class
  FreppleClass<OperationSplit,Operation>::getType().addMethod(
    "addAlternate", OperationSplit::addAlternate,
    METH_VARARGS | METH_KEYWORDS, "add an alternate"
    );
  return FreppleClass<OperationSplit,Operation>::initialize();
}


int OperationAlternate::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass("operation", "operation_alternate",
      Object::createString<OperationAlternate>);

  // Initialize the Python class
  FreppleClass<OperationAlternate,Operation>::getType().addMethod(
    "addAlternate", OperationAlternate::addAlternate,
    METH_VARARGS | METH_KEYWORDS, "add an alternate"
    );
  return FreppleClass<OperationAlternate,Operation>::initialize();
}


int OperationRouting::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass("operation", "operation_routing",
      Object::createString<OperationRouting>);

  // Initialize the Python class
  FreppleClass<OperationRouting,Operation>::getType().addMethod("addStep", OperationRouting::addStep, METH_VARARGS , "add steps to the routing");
  return FreppleClass<OperationRouting,Operation>::initialize();
}


int OperationSetup::initialize()
{
  // Initialize the metadata.
  // There is NO factory method
  metadata = new MetaClass("operation", "operation_setup");

  // Initialize the Python class
  int tmp = FreppleClass<OperationSetup,Operation>::initialize();

  // Create a generic setup operation.
  // This will be the only instance of this class.
  setupoperation = add(new OperationSetup("setup operation"));

  return tmp;
}


DECLARE_EXPORT Operation::~Operation()
{
  // Delete all existing operationplans (even locked ones)
  deleteOperationPlans(true);

  // The Flow and Load objects are automatically deleted by the destructor
  // of the Association list class.

  // Remove the reference to this operation from all items
  for (Item::iterator k = Item::begin(); k != Item::end(); ++k)
    if (k->getOperation() == this) k->setOperation(NULL);

  // Remove the reference to this operation from all demands
  for (Demand::iterator l = Demand::begin(); l != Demand::end(); ++l)
    if (l->getOperation() == this) l->setOperation(NULL);

  // Remove the reference to this operation from all buffers
  for (Buffer::iterator m = Buffer::begin(); m != Buffer::end(); ++m)
    if (m->getProducingOperation() == this) m->setProducingOperation(NULL);

  // Remove the operation from its super-operations and sub-operations
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSuperOperations().empty())
    removeSuperOperation(*getSuperOperations().begin());
}


DECLARE_EXPORT OperationRouting::~OperationRouting()
{
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSubOperations().empty())
    removeSubOperation(*getSubOperations().begin());
}


DECLARE_EXPORT OperationSplit::~OperationSplit()
{
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSubOperations().empty())
    removeSubOperation(*getSubOperations().begin());
}


DECLARE_EXPORT OperationAlternate::~OperationAlternate()
{
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSubOperations().empty())
    removeSubOperation(*getSubOperations().begin());
}


DECLARE_EXPORT OperationPlan* Operation::createOperationPlan (double q, Date s, Date e,
    Demand* l, OperationPlan* ow, unsigned long i,
    bool makeflowsloads) const
{
  OperationPlan *opplan = new OperationPlan();
  initOperationPlan(opplan,q,s,e,l,ow,i,makeflowsloads);
  return opplan;
}


DECLARE_EXPORT DateRange Operation::calculateOperationTime
(Date thedate, TimePeriod duration, bool forward,
 TimePeriod *actualduration) const
{
  int calcount = 0;
  // Initial size of 10 should do for 99.99% of all cases
  vector<Calendar::EventIterator*> cals(10);

  // Default actual duration
  if (actualduration) *actualduration = duration;

  try
  {
    // Step 1: Create an iterator on each of the calendars
    // a) operation's location
    if (loc && loc->getAvailable())
      cals[calcount++] = new Calendar::EventIterator(loc->getAvailable(), thedate, forward);
    /* @todo multiple availability calendars are not implemented yet
      for (Operation::loadlist::const_iterator g=loaddata.begin();
        g!=loaddata.end(); ++g)
    {
      Resource* res = g->getResource();
      if (res->getMaximum())
        // b) resource size calendar
        cals[calcount++] = new Calendar::EventIterator(
          res->getMaximum(),
          thedate
          );
      if (res->getLocation() && res->getLocation()->getAvailable())
        // c) resource location
        cals[calcount++] = new Calendar::EventIterator(
          res->getLocation()->getAvailable(),
          thedate
          );
    }
    */

    // Special case: no calendars at all
    if (calcount == 0)
      return forward ?
          DateRange(thedate, thedate+duration) :
          DateRange(thedate-duration, thedate);

    // Step 2: Iterate over the calendar dates to find periods where all
    // calendars are simultaneously effective.
    DateRange result;
    Date curdate = thedate;
    bool status = false;
    TimePeriod curduration = duration;
    while (true)
    {
      // Check whether all calendars are available
      bool available = true;
      for (int c = 0; c < calcount && available; c++)
      {
    	const Calendar::Bucket *tmp = cals[c]->getBucket();
        if (tmp)
          available = tmp->getBool();
        else
          available = cals[c]->getCalendar()->getBool();
      }
      curdate = cals[0]->getDate();

      if (available && !status)
      {
        // Becoming available after unavailable period
        thedate = curdate;
        status = true;
        if (forward && result.getStart() == Date::infinitePast)
          // First available time - make operation start at this time
          result.setStart(curdate);
        else if (!forward && result.getEnd() == Date::infiniteFuture)
          // First available time - make operation end at this time
          result.setEnd(curdate);
      }
      else if (!available && status)
      {
        // Becoming unavailable after available period
        status = false;
        if (forward)
        {
          // Forward
          TimePeriod delta = curdate - thedate;
          if (delta >= curduration)
          {
            result.setEnd(thedate + curduration);
            break;
          }
          else
            curduration -= delta;
        }
        else
        {
          // Backward
          TimePeriod delta = thedate - curdate;
          if (delta >= curduration)
          {
            result.setStart(thedate - curduration);
            break;
          }
          else
            curduration -= delta;
        }
      }
      else if (forward && curdate == Date::infiniteFuture)
      {
        // End of forward iteration
        if (available)
        {
          TimePeriod delta = curdate - thedate;
          if (delta >= curduration)
            result.setEnd(thedate + curduration);
          else if (actualduration)
            *actualduration = duration - curduration;
        }
        else  if (actualduration)
          *actualduration = duration - curduration;
        break;
      }
      else if (!forward && curdate == Date::infinitePast)
      {
        // End of backward iteration
        if (available)
        {
          TimePeriod delta = thedate - curdate;
          if (delta >= curduration)
            result.setStart(thedate - curduration);
          else if (actualduration)
            *actualduration = duration - curduration;
        }
        else if (actualduration)
          *actualduration = duration - curduration;
        break;
      }

      // Advance to the next event
      if (forward) ++(*cals[0]);
      else --(*cals[0]);
    }

    // Step 3: Clean up
    while (calcount) delete cals[--calcount];
    return result;
  }
  catch (...)
  {
    // Clean up
    while (calcount) delete cals[calcount--];
    // Rethrow the exception
    throw;
  }
}


DECLARE_EXPORT DateRange Operation::calculateOperationTime
(Date start, Date end, TimePeriod *actualduration) const
{
  // Switch start and end if required
  if (end < start)
  {
    Date tmp = start;
    start = end;
    end = tmp;
  }

  int calcount = 0;
  // Initial size of 10 should do for 99.99% of all cases
  vector<Calendar::EventIterator*> cals(10);

  // Default actual duration
  if (actualduration) *actualduration = 0L;

  try
  {
    // Step 1: Create an iterator on each of the calendars
    // a) operation's location
    if (loc && loc->getAvailable())
      cals[calcount++] = new Calendar::EventIterator(loc->getAvailable(), start);
    /* @todo multiple availability calendars are not implmented yet
      for (Operation::loadlist::const_iterator g=loaddata.begin();
        g!=loaddata.end(); ++g)
    {
      Resource* res = g->getResource();
      if (res->getMaximum())
        // b) resource size calendar
        cals[calcount++] = new Calendar::EventIterator(
          res->getMaximum(),
          start
          );
      if (res->getLocation() && res->getLocation()->getAvailable())
        // c) resource location
        cals[calcount++] = new Calendar::EventIterator(
          res->getLocation()->getAvailable(),
          start
          );
    }
    */

    // Special case: no calendars at all
    if (calcount == 0)
    {
      if (actualduration) *actualduration = end - start;
      return DateRange(start, end);
    }

    // Step 2: Iterate over the calendar dates to find periods where all
    // calendars are simultaneously effective.
    DateRange result;
    Date curdate = start;
    bool status = false;
    while (true)
    {
      // Check whether all calendar are available
      bool available = true;
      for (int c = 0; c < calcount && available; c++)
      {
        if (cals[c]->getBucket())
          available = cals[c]->getBucket()->getBool();
        else
          available = cals[c]->getCalendar()->getBool();
      }
      curdate = cals[0]->getDate();

      if (available && !status)
      {
        // Becoming available after unavailable period
        if (curdate >= end)
        {
          // Leaving the desired date range
          result.setEnd(start);
          break;
        }
        start = curdate;
        status = true;
        if (result.getStart() == Date::infinitePast)
          // First available time - make operation start at this time
          result.setStart(curdate);
      }
      else if (!available && status)
      {
        // Becoming unavailable after available period
        if (curdate >= end)
        {
          // Leaving the desired date range
          if (actualduration) *actualduration += end - start;
          result.setEnd(end);
          break;
        }
        status = false;
        if (actualduration) *actualduration += curdate - start;
        start = curdate;
      }
      else if (curdate >= end)
      {
        // Leaving the desired date range
        if (available)
        {
          if (actualduration) *actualduration += end - start;
          result.setEnd(end);
          break;
        }
        else
          result.setEnd(start);
        break;
      }

      // Advance to the next event
      ++(*cals[0]);
    }

    // Step 3: Clean up
    while (calcount) delete cals[--calcount];
    return result;
  }
  catch (...)
  {
    // Clean up
    while (calcount) delete cals[calcount--];
    // Rethrow the exception
    throw;
  }
}


DECLARE_EXPORT void Operation::initOperationPlan (OperationPlan* opplan,
    double q, const Date& s, const Date& e, Demand* l, OperationPlan* ow,
    unsigned long i, bool makeflowsloads) const
{
  opplan->oper = const_cast<Operation*>(this);
  opplan->setDemand(l);
  opplan->id = i;

  // Setting the owner first. Note that the order is important here!
  // For alternates & routings the quantity needs to be set through the owner.
  opplan->setOwner(ow);

  // Setting the dates and quantity
  setOperationPlanParameters(opplan,q,s,e);

  // Create the loadplans and flowplans, if allowed
  if (makeflowsloads) opplan->createFlowLoads();

  // Update flow and loadplans, and mark for problem detection
  opplan->update();
}


DECLARE_EXPORT void Operation::deleteOperationPlans(bool deleteLockedOpplans)
{
  OperationPlan::deleteOperationPlans(this, deleteLockedOpplans);
}


DECLARE_EXPORT void Operation::writeElement(Serializer* o, const Keyword& tag, mode m) const
{
  // Note that this class is abstract and never instantiated directly. There is
  // therefore no reason to ever write a header.
  assert(m == NOHEAD || m == NOHEADTAIL);

  // Write the fields
  HasDescription::writeElement(o, tag);
  Plannable::writeElement(o, tag);
  if (post_time)
    o->writeElement(Tags::tag_posttime, post_time);
  if (getCost() != 0.0)
    o->writeElement(Tags::tag_cost, getCost());
  if (fence)
    o->writeElement(Tags::tag_fence, fence);
  if (size_minimum != 1.0)
    o->writeElement(Tags::tag_size_minimum, size_minimum);
  if (size_multiple > 0.0)
    o->writeElement(Tags::tag_size_multiple, size_multiple);
  if (size_maximum < DBL_MAX)
    o->writeElement(Tags::tag_size_maximum, size_maximum);
  if (loc)
    o->writeElement(Tags::tag_location, loc);

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write extra plan information
  if ((o->getContentType() == Serializer::PLAN
      || o->getContentType() == Serializer::PLANDETAIL) && first_opplan)
  {
    o->BeginList(Tags::tag_operationplans);
    for (OperationPlan::iterator i(this); i!=OperationPlan::end(); ++i)
      o->writeElement(Tags::tag_operationplan, *i, FULL);
    o->EndList(Tags::tag_operationplans);
  }
}


DECLARE_EXPORT void Operation::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_flow)
      && pIn.getParentElement().first.isA(Tags::tag_flows))
  {
    Flow *f =
      dynamic_cast<Flow*>(MetaCategory::ControllerDefault(Flow::metadata,pIn.getAttributes()));
    if (f) f->setOperation(this);
    pIn.readto(f);
  }
  else if (pAttr.isA (Tags::tag_load)
      && pIn.getParentElement().first.isA(Tags::tag_loads))
  {
    Load* l = new Load();
    l->setOperation(this);
    pIn.readto(&*l);
  }
  else if (pAttr.isA (Tags::tag_operationplan))
    pIn.readto(OperationPlan::createOperationPlan(OperationPlan::metadata, pIn.getAttributes()));
  else if (pAttr.isA (Tags::tag_location))
    pIn.readto( Location::reader(Location::metadata,pIn.getAttributes()) );
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT void Operation::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_fence))
    setFence(pElement.getTimeperiod());
  else if (pAttr.isA (Tags::tag_size_minimum))
    setSizeMinimum(pElement.getDouble());
  else if (pAttr.isA (Tags::tag_cost))
    setCost(pElement.getDouble());
  else if (pAttr.isA (Tags::tag_size_multiple))
    setSizeMultiple(pElement.getDouble());
  else if (pAttr.isA (Tags::tag_size_maximum))
    setSizeMaximum(pElement.getDouble());
  else if (pAttr.isA (Tags::tag_posttime))
    setPostTime(pElement.getTimeperiod());
  else if (pAttr.isA (Tags::tag_location))
  {
    Location *l = dynamic_cast<Location*>(pIn.getPreviousObject());
    if (l) setLocation(l);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
  {
    Plannable::endElement(pIn, pAttr, pElement);
    HasDescription::endElement(pIn, pAttr, pElement);
  }
}


DECLARE_EXPORT OperationPlanState
OperationFixedTime::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, bool execute) const
{
  // Invalid call to the function, or locked operationplan.
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for fixedtime operationplan");
  if (opplan->getLocked())
    return OperationPlanState(opplan);

  // All quantities are valid, as long as they are above the minimum size and
  // below the maximum size
  if (q > 0 && q < getSizeMinimum()) q = getSizeMinimum();
  if (q > getSizeMaximum()) q = getSizeMaximum();
  if (fabs(q - opplan->getQuantity()) > ROUNDING_ERROR)
    q = opplan->setQuantity(q, false, false, execute);

  // Set the start and end date.
  DateRange x;
  TimePeriod actualduration;
  if (e && s)
  {
    if (preferEnd) x = calculateOperationTime(e, duration, false, &actualduration);
    else x = calculateOperationTime(s, duration, true, &actualduration);
  }
  else if (s) x = calculateOperationTime(s, duration, true, &actualduration);
  else x = calculateOperationTime(e, duration, false, &actualduration);
  if (!execute)
    // Simulation only
    return OperationPlanState(x, actualduration == duration ? q : 0);
  else if (actualduration == duration)
    // Update succeeded
    opplan->setStartAndEnd(x.getStart(), x.getEnd());
  else
    // Update failed - Not enough available time
    opplan->setQuantity(0);

  // Return value
  return OperationPlanState(opplan);
}


DECLARE_EXPORT bool OperationFixedTime::extraInstantiate(OperationPlan* o)
{
  // See if we can consolidate this operationplan with an existing one.
  // Merging is possible only when all the following conditions are met:
  //   - id of the new opplan is not set
  //   - id of the old opplan is set
  //   - it is a fixedtime operation
  //   - it doesn't load any resources of type default
  //   - both operationplans aren't locked
  //   - both operationplans have no owner
  //   - start and end date of both operationplans are the same
  //   - demand of both operationplans are the same
  //   - maximum operation size is not exceeded
  //   - alternate flowplans need to be on the same alternate
  if (!o->getRawIdentifier() && !o->getLocked() && !o->getOwner())
  {
    // Verify we load no resources of type "default".
    // It's ok to merge operationplans which load "infinite" or "buckets" resources.
    for (Operation::loadlist::const_iterator i = getLoads().begin(); i != getLoads().end(); ++i)
      if (i->getResource()->getType() == *ResourceDefault::metadata)
        return true;

    // Loop through candidates
    OperationPlan::iterator x(this);
    OperationPlan *y = NULL;
    for (; x != OperationPlan::end() && *x < *o; ++x)
      y = &*x;
    if (y && y->getDates() == o->getDates() && !y->getOwner()
        && y->getDemand() == o->getDemand() && !y->getLocked() && y->getRawIdentifier()
        && y->getQuantity() + o->getQuantity() < getSizeMaximum())
    {
      // Check that the flowplans are on identical alternates and not of type fixed
      OperationPlan::FlowPlanIterator fp1 = o->beginFlowPlans();
      OperationPlan::FlowPlanIterator fp2 = y->beginFlowPlans();
      while (fp1 != o->endFlowPlans())
      {
        if (fp1->getBuffer() != fp2->getBuffer()
          || fp1->getFlow()->getType() == *FlowFixedEnd::metadata
          || fp1->getFlow()->getType() == *FlowFixedStart::metadata
          || fp2->getFlow()->getType() == *FlowFixedEnd::metadata
          || fp2->getFlow()->getType() == *FlowFixedStart::metadata)
          // No merge possible
          return true;
        ++fp1;
        ++fp2;
      }
      // Merging with the 'next' operationplan
      y->setQuantity(y->getQuantity() + o->getQuantity());
      return false;
    }
    if (x!= OperationPlan::end() && x->getDates() == o->getDates() && !x->getOwner()
        && x->getDemand() == o->getDemand() && !x->getLocked() && x->getRawIdentifier()
        && x->getQuantity() + o->getQuantity() < getSizeMaximum())
    {
      // Check that the flowplans are on identical alternates
      OperationPlan::FlowPlanIterator fp1 = o->beginFlowPlans();
      OperationPlan::FlowPlanIterator fp2 = x->beginFlowPlans();
      while (fp1 != o->endFlowPlans())
      {
        if (fp1->getBuffer() != fp2->getBuffer())
          // Different alternates - no merge possible
          return true;
        ++fp1;
        ++fp2;
      }
      // Merging with the 'previous' operationplan
      x->setQuantity(x->getQuantity() + o->getQuantity());
      return false;
    }
  }
  return true;
}


DECLARE_EXPORT void OperationFixedTime::writeElement
(Serializer* o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Operation::writeElement(o, tag, NOHEAD);
  if (duration) o->writeElement (Tags::tag_duration, duration);

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject (tag);
}


DECLARE_EXPORT void OperationFixedTime::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_duration))
    setDuration (pElement.getTimeperiod());
  else
    Operation::endElement (pIn, pAttr, pElement);
}


DECLARE_EXPORT OperationPlanState
OperationTimePer::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, bool execute) const
{
  // Invalid call to the function.
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for timeper operationplan");
  if (opplan->getLocked())
    return OperationPlanState(opplan);

  // Respect minimum and maximum size
  if (q > 0 && q < getSizeMinimum()) q = getSizeMinimum();
  if (q > getSizeMaximum()) q = getSizeMaximum();

  // The logic depends on which dates are being passed along
  DateRange x;
  TimePeriod actual;
  if (s && e)
  {
    // Case 1: Both the start and end date are specified: Compute the quantity.
    // Calculate the available time between those dates
    x = calculateOperationTime(s,e,&actual);
    if (actual < duration)
    {
      // Start and end aren't far enough from each other to fit the constant
      // part of the operation duration. This is infeasible.
      if (!execute) return OperationPlanState(x,0);
      opplan->setQuantity(0,true,false,execute);
      opplan->setEnd(e);
    }
    else
    {
      // Calculate the quantity, respecting minimum, maximum and multiple size.
      if (duration_per)
      {
        if (q * duration_per < static_cast<double>(actual - duration) + 1)
          // Provided quantity is acceptable.
          // Note that we allow a margin of 1 second to accept.
          q = opplan->setQuantity(q, true, false, execute);
        else
          // Calculate the maximum operationplan that will fit in the window
          q = opplan->setQuantity(
              static_cast<double>(actual - duration) / duration_per,
              true, false, execute);
      }
      else
        // No duration_per field given, so any quantity will go
        q = opplan->setQuantity(q, true, false, execute);

      // Updates the dates
      TimePeriod wanted(
        duration + static_cast<long>(duration_per * q)
      );
      if (preferEnd) x = calculateOperationTime(e, wanted, false, &actual);
      else x = calculateOperationTime(s, wanted, true, &actual);
      if (!execute) return OperationPlanState(x,q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
  }
  else if (e || !s)
  {
    // Case 2: Only an end date is specified. Respect the quantity and
    // compute the start date
    // Case 4: No date was given at all. Respect the quantity and the
    // existing end date of the operationplan.
    q = opplan->setQuantity(q,true,false,execute); // Round and size the quantity
    TimePeriod wanted(duration + static_cast<long>(duration_per * q));
    x = calculateOperationTime(e, wanted, false, &actual);
    if (actual == wanted)
    {
      // Size is as desired
      if (!execute) return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
    else if (actual < duration)
    {
      // Not feasible
      if (!execute) return OperationPlanState(x, 0);
      opplan->setQuantity(0,true,false);
      opplan->setStartAndEnd(e,e);
    }
    else
    {
      // Resize the quantity to be feasible
      double max_q = duration_per ?
          static_cast<double>(actual-duration) / duration_per :
          q;
      q = opplan->setQuantity(q < max_q ? q : max_q, true, false, execute);
      wanted = duration + static_cast<long>(duration_per * q);
      x = calculateOperationTime(e, wanted, false, &actual);
      if (!execute) return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
  }
  else
  {
    // Case 3: Only a start date is specified. Respect the quantity and
    // compute the end date
    q = opplan->setQuantity(q,true,false,execute); // Round and size the quantity
    TimePeriod wanted(
      duration + static_cast<long>(duration_per * q)
    );
    TimePeriod actual;
    x = calculateOperationTime(s, wanted, true, &actual);
    if (actual == wanted)
    {
      // Size is as desired
      if (!execute) return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
    else if (actual < duration)
    {
      // Not feasible
      if (!execute) return OperationPlanState(x, 0);
      opplan->setQuantity(0,true,false);
      opplan->setStartAndEnd(s,s);
    }
    else
    {
      // Resize the quantity to be feasible
      double max_q = duration_per ?
          static_cast<double>(actual-duration) / duration_per :
          q;
      q = opplan->setQuantity(q < max_q ? q : max_q, true, false, execute);
      wanted = duration + static_cast<long>(duration_per * q);
      x = calculateOperationTime(e, wanted, false, &actual);
      if (!execute) return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
  }

  // Return value
  return OperationPlanState(opplan);
}


DECLARE_EXPORT void OperationTimePer::writeElement
(Serializer *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Operation::writeElement(o, tag, NOHEADTAIL);
  o->writeElement(Tags::tag_duration, duration);
  if (duration_per)
  {
    char t[65];
    TimePeriod::double2CharBuffer(duration_per, t);
    o->writeElement(Tags::tag_duration_per, t);
  }

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void OperationTimePer::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_duration))
    setDuration(pElement.getTimeperiod());
  else if (pAttr.isA(Tags::tag_duration_per))
    setDurationPer( TimePeriod::parse2double(pElement.getString().c_str()) );
  else
    Operation::endElement (pIn, pAttr, pElement);
}


DECLARE_EXPORT void OperationRouting::writeElement
(Serializer *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Operation::writeElement(o, tag, NOHEADTAIL);
  if (steps.size())
  {
    o->BeginList(Tags::tag_steps);
    for (Operationlist::const_iterator i = steps.begin(); i!=steps.end(); ++i)
      o->writeElement(Tags::tag_operation, *i, REFERENCE);
    o->EndList(Tags::tag_steps);
  }

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void OperationRouting::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
    Operation::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void OperationRouting::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_operation)
      && pIn.getParentElement().first.isA(Tags::tag_steps))
  {
    Operation *oper = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (oper) addStepBack (oper);
    else throw LogicException("Incorrect object type during read operation");
  }
  Operation::endElement (pIn, pAttr, pElement);
}


DECLARE_EXPORT OperationPlanState OperationRouting::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, bool execute) const
{
  // Invalid call to the function
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for routing operationplan");
  if (opplan->getLocked())
    return OperationPlanState(opplan);

  if (!opplan->lastsubopplan || opplan->lastsubopplan->getOperation() == OperationSetup::setupoperation) // @todo replace with proper iterator
  {
    // No step operationplans to work with. Just apply the requested quantity
    // and dates.
    q = opplan->setQuantity(q,false,false,execute);
    if (!s && e) s = e;
    if (s && !e) e = s;
    if (!execute) return OperationPlanState(s, e, q);
    opplan->setStartAndEnd(s,e);
    return OperationPlanState(opplan);
  }

  // Behavior depends on the dates being passed.
  // Move all sub-operationplans in an orderly fashion, either starting from
  // the specified end date or the specified start date.
  OperationPlanState x;
  Date y;
  bool realfirst = true;
  if (e)
  {
    // Case 1: an end date is specified
    for (OperationPlan* i = opplan->lastsubopplan; i; i = i->prevsubopplan)
    {
      if (i->getOperation() == OperationSetup::setupoperation) continue;
      x = i->getOperation()->setOperationPlanParameters(i,q,Date::infinitePast,e,preferEnd,execute);
      e = x.start;
      if (realfirst)
      {
        y = x.end;
        realfirst = false;
      }
    }
    return OperationPlanState(x.start, y, x.quantity);
  }
  else if (s)
  {
    // Case 2: a start date is specified
    for (OperationPlan *i = opplan->firstsubopplan; i; i = i->nextsubopplan)
    {
      if (i->getOperation() == OperationSetup::setupoperation) continue;
      x = i->getOperation()->setOperationPlanParameters(i,q,s,Date::infinitePast,preferEnd,execute);
      s = x.end;
      if (realfirst)
      {
        y = x.start;
        realfirst = false;
      }
    }
    return OperationPlanState(y, x.end, x.quantity);
  }
  else
    throw LogicException(
      "Updating a routing operationplan without start or end date argument"
    );
}


DECLARE_EXPORT bool OperationRouting::extraInstantiate(OperationPlan* o)
{
  // Create step suboperationplans if they don't exist yet.
  if (!o->lastsubopplan || o->lastsubopplan->getOperation() == OperationSetup::setupoperation)
  {
    Date d = o->getDates().getEnd();
    OperationPlan *p = NULL;
    // @todo not possible to initialize a routing oplan based on a start date
    if (d != Date::infiniteFuture)
    {
      // Using the end date
      for (Operation::Operationlist::const_reverse_iterator e =
          getSubOperations().rbegin(); e != getSubOperations().rend(); ++e)
      {
        p = (*e)->createOperationPlan(o->getQuantity(), Date::infinitePast,
            d, NULL, o, 0, true);
        d = p->getDates().getStart();
      }
    }
    else
    {
      // Using the start date when there is no end date
      d = o->getDates().getStart();
      // Using the current date when both the start and end date are missing
      if (!d) d = Plan::instance().getCurrent();
      for (Operation::Operationlist::const_iterator e =
          getSubOperations().begin(); e != getSubOperations().end(); ++e)
      {
        p = (*e)->createOperationPlan(o->getQuantity(), d,
            Date::infinitePast, NULL, o, 0, true);
        d = p->getDates().getEnd();
      }
    }
  }
  return true;
}


DECLARE_EXPORT SearchMode decodeSearchMode(const string& c)
{
  if (c == "PRIORITY") return PRIORITY;
  if (c == "MINCOST") return MINCOST;
  if (c == "MINPENALTY") return MINPENALTY;
  if (c == "MINCOSTPENALTY") return MINCOSTPENALTY;
  throw DataException("Invalid search mode " + c);
}

DECLARE_EXPORT void OperationAlternate::addAlternate
(Operation* o, int prio, DateRange eff)
{
  if (!o) return;
  Operationlist::iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && prio >= propIter->first)
  {
    ++propIter;
    ++altIter;
  }
  alternateProperties.insert(propIter,alternateProperty(prio,eff));
  alternates.insert(altIter,o);
  o->addSuperOperation(this);
}


DECLARE_EXPORT const OperationAlternate::alternateProperty&
OperationAlternate::getProperties(Operation* o) const
{
  if (!o)
    throw LogicException("Null pointer passed when searching for a \
        suboperation of alternate operation '" + getName() + "'");
  Operationlist::const_iterator altIter = alternates.begin();
  alternatePropertyList::const_iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++propIter;
    ++altIter;
  }
  if (*altIter == o) return *propIter;
  throw DataException("Operation '" + o->getName() +
      "' isn't a suboperation of alternate operation '" + getName() + "'");
}


DECLARE_EXPORT void OperationAlternate::setPriority(Operation* o, int f)
{
  if (!o) return;
  Operationlist::const_iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++propIter;
    ++altIter;
  }
  if (*altIter == o)
    propIter->first = f;
  else
    throw DataException("Operation '" + o->getName() +
        "' isn't a suboperation of alternate operation '" + getName() + "'");
}


DECLARE_EXPORT void OperationAlternate::setEffective(Operation* o, DateRange dr)
{
  if (!o) return;
  Operationlist::const_iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++propIter;
    ++altIter;
  }
  if (*altIter == o)
    propIter->second = dr;
  else
    throw DataException("Operation '" + o->getName() +
        "' isn't a suboperation of alternate operation '" + getName() + "'");
}


DECLARE_EXPORT void OperationAlternate::writeElement
(Serializer *o, const Keyword& tag, mode m) const
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

  // Write the standard fields
  Operation::writeElement(o, tag, NOHEADTAIL);
  if (search != PRIORITY)
    o->writeElement(Tags::tag_search, search);

  // Write the extra fields
  o->BeginList(Tags::tag_alternates);
  alternatePropertyList::const_iterator propIter = alternateProperties.begin();
  for (Operationlist::const_iterator i = alternates.begin();
      i != alternates.end(); ++i)
  {
    o->BeginObject(Tags::tag_alternate);
    o->writeElement(Tags::tag_operation, *i, REFERENCE);
    o->writeElement(Tags::tag_priority, propIter->first);
    if (propIter->second.getStart() != Date::infinitePast)
      o->writeElement(Tags::tag_effective_start, propIter->second.getStart());
    if (propIter->second.getEnd() != Date::infiniteFuture)
      o->writeElement(Tags::tag_effective_end, propIter->second.getEnd());
    o->EndObject (Tags::tag_alternate);
    ++propIter;
  }
  o->EndList(Tags::tag_alternates);

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void OperationAlternate::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
    Operation::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void OperationAlternate::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  // Saving some typing...
  typedef pair<Operation*,alternateProperty> tempData;

  // Create a temporary object
  if (!pIn.getUserArea())
    pIn.setUserArea(new tempData(static_cast<Operation*>(NULL),alternateProperty(1,DateRange())));
  tempData* tmp = static_cast<tempData*>(pIn.getUserArea());

  if (pAttr.isA(Tags::tag_alternate))
  {
    addAlternate(tmp->first, tmp->second.first, tmp->second.second);
    // Reset the defaults
    tmp->first = NULL;
    tmp->second.first = 1;
    tmp->second.second = DateRange();
  }
  else if (pAttr.isA(Tags::tag_priority))
    tmp->second.first = pElement.getInt();
  else if (pAttr.isA(Tags::tag_search))
    setSearch(pElement.getString());
  else if (pAttr.isA(Tags::tag_effective_start))
    tmp->second.second.setStart(pElement.getDate());
  else if (pAttr.isA(Tags::tag_effective_end))
    tmp->second.second.setEnd(pElement.getDate());
  else if (pAttr.isA(Tags::tag_operation)
      && pIn.getParentElement().first.isA(Tags::tag_alternate))
  {
    Operation * b = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (b) tmp->first = b;
    else throw LogicException("Incorrect object type during read operation");
  }
  Operation::endElement (pIn, pAttr, pElement);

  // Delete the temporary object
  if (pIn.isObjectEnd()) delete static_cast<tempData*>(pIn.getUserArea());
}


DECLARE_EXPORT OperationPlanState
OperationAlternate::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd,
 bool execute) const
{
  // Invalid calls to this function
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for alternate operationplan");
  if (opplan->getLocked())
    return OperationPlanState(opplan);

  OperationPlan *x = opplan->lastsubopplan;
  while (x && x->getOperation() == OperationSetup::setupoperation)
    x = x->prevsubopplan;
  if (!x)
  {
    // Blindly accept the parameters if there is no suboperationplan
    if (execute)
    {
      opplan->setQuantity(q,false,false);
      opplan->setStartAndEnd(s, e);
      return OperationPlanState(opplan);
    }
    else
      return OperationPlanState(s, e, opplan->setQuantity(q,false,false,false));
  }
  else
    // Pass the call to the sub-operation
    return x->getOperation()
        ->setOperationPlanParameters(x,q,s,e,preferEnd, execute);
}


DECLARE_EXPORT bool OperationAlternate::extraInstantiate(OperationPlan* o)
{
  // Create a suboperationplan if one doesn't exist yet.
  // We use the first effective alternate by default.
  if (!o->lastsubopplan || o->lastsubopplan->getOperation() == OperationSetup::setupoperation)
  {
    // Find the right operation
    Operationlist::const_iterator altIter = getSubOperations().begin();
    for (; altIter != getSubOperations().end(); )
    {
      const OperationAlternate::alternateProperty& props = getProperties(*altIter);
      // Filter out alternates that are not suitable
      if (props.first != 0.0 && props.second.within(o->getDates().getEnd()))
        break;
    }
    if (altIter != getSubOperations().end())
      // Create an operationplan instance
      (*altIter)->createOperationPlan(
        o->getQuantity(), o->getDates().getStart(),
        o->getDates().getEnd(), NULL, o, 0, true);
  }
  return true;
}


DECLARE_EXPORT void OperationAlternate::removeSubOperation(Operation *o)
{
  Operationlist::iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++propIter;
    ++altIter;
  }
  if (*altIter == o)
  {
    alternates.erase(altIter);
    alternateProperties.erase(propIter);
    o->superoplist.remove(this);
    setChanged();
  }
  else
    logger << "Warning: operation '" << *o
        << "' isn't a suboperation of alternate operation '" << *this
        << "'" << endl;
}


DECLARE_EXPORT void OperationSplit::addAlternate
(Operation* o, int prio, DateRange eff)
{
  if (!o) return;
  Operationlist::iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && prio >= propIter->first)
  {
    ++propIter;
    ++altIter;
  }
  alternateProperties.insert(propIter,alternateProperty(prio,eff));
  alternates.insert(altIter,o);
  o->addSuperOperation(this);
}


DECLARE_EXPORT void OperationSplit::setPercent(Operation* o, int f)
{
  if (!o) return;
  Operationlist::const_iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++propIter;
    ++altIter;
  }
  if (*altIter == o)
    propIter->first = f;
  else
    throw DataException("Operation '" + o->getName() +
        "' isn't a suboperation of split operation '" + getName() + "'");
}


DECLARE_EXPORT void OperationSplit::setEffective(Operation* o, DateRange dr)
{
  if (!o) return;
  Operationlist::const_iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++propIter;
    ++altIter;
  }
  if (*altIter == o)
    propIter->second = dr;
  else
    throw DataException("Operation '" + o->getName() +
        "' isn't a suboperation of split operation '" + getName() + "'");
}


DECLARE_EXPORT void OperationSplit::writeElement
(Serializer *o, const Keyword& tag, mode m) const
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

  // Write the standard fields
  Operation::writeElement(o, tag, NOHEADTAIL);

  // Write the extra fields
  o->BeginList(Tags::tag_alternates);
  alternatePropertyList::const_iterator propIter = alternateProperties.begin();
  for (Operationlist::const_iterator i = alternates.begin();
      i != alternates.end(); ++i)
  {
    o->BeginObject(Tags::tag_alternate);
    o->writeElement(Tags::tag_operation, *i, REFERENCE);
    o->writeElement(Tags::tag_percent, propIter->first);
    if (propIter->second.getStart() != Date::infinitePast)
      o->writeElement(Tags::tag_effective_start, propIter->second.getStart());
    if (propIter->second.getEnd() != Date::infiniteFuture)
      o->writeElement(Tags::tag_effective_end, propIter->second.getEnd());
    o->EndObject (Tags::tag_alternate);
    ++propIter;
  }
  o->EndList(Tags::tag_alternates);

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void OperationSplit::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
    Operation::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void OperationSplit::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  // Saving some typing...
  typedef pair<Operation*,alternateProperty> tempData;

  // Create a temporary object
  if (!pIn.getUserArea())
    pIn.setUserArea(new tempData(static_cast<Operation*>(NULL),alternateProperty(1,DateRange())));
  tempData* tmp = static_cast<tempData*>(pIn.getUserArea());

  if (pAttr.isA(Tags::tag_alternate))
  {
    addAlternate(tmp->first, tmp->second.first, tmp->second.second);
    // Reset the defaults
    tmp->first = NULL;
    tmp->second.first = 1;
    tmp->second.second = DateRange();
  }
  else if (pAttr.isA(Tags::tag_percent))
    tmp->second.first = pElement.getInt();
  else if (pAttr.isA(Tags::tag_effective_start))
    tmp->second.second.setStart(pElement.getDate());
  else if (pAttr.isA(Tags::tag_effective_end))
    tmp->second.second.setEnd(pElement.getDate());
  else if (pAttr.isA(Tags::tag_operation)
      && pIn.getParentElement().first.isA(Tags::tag_alternate))
  {
    Operation * b = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (b) tmp->first = b;
    else throw LogicException("Incorrect object type during read operation");
  }
  Operation::endElement (pIn, pAttr, pElement);

  // Delete the temporary object
  if (pIn.isObjectEnd()) delete static_cast<tempData*>(pIn.getUserArea());
}


DECLARE_EXPORT OperationPlanState
OperationSplit::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd,
 bool execute) const
{
  // Invalid calls to this function
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for split operationplan");
  if (opplan->getLocked())
    return OperationPlanState(opplan);

  // Blindly accept the parameters: only sizing constraints from the child
  // operations are respected.
  if (execute)
  {
    opplan->setQuantity(q, false, false);
    opplan->setStartAndEnd(s, e);
    return OperationPlanState(opplan);
  }
  else
    return OperationPlanState(s, e, q);
}


DECLARE_EXPORT bool OperationSplit::extraInstantiate(OperationPlan* o)
{
  if (o->lastsubopplan && o->lastsubopplan->getOperation() != OperationSetup::setupoperation)
    // Suboperationplans already exist. Nothing to do here.
    return true;

  // Compute the sum of all effective percentages.
  int sum_percent = 0;
  Date enddate = o->getDates().getEnd();
  OperationSplit::alternatePropertyList::const_iterator propIter = getProperties().begin();
  for (Operation::Operationlist::const_iterator altIter = getSubOperations().begin();
    altIter != getSubOperations().end();
    ++altIter, ++propIter)
  {
    if (propIter->second.within(enddate))
      sum_percent += propIter->first;
  }
  if (!sum_percent)
    // Oops, no effective suboperations found.
    // Let's not create any suboperationplans then.
    return true;

  // Create all child operationplans
  propIter = getProperties().begin();
  for (Operation::Operationlist::const_iterator altIter = getSubOperations().begin();
    altIter != getSubOperations().end();
    ++altIter, ++propIter)
  {
    // Verify effectivity date and percentage > 0
    if (!propIter->first || !propIter->second.within(enddate))
      continue;

    // Find the first producing flow.
    // In case the split suboperation produces multiple materials this code
    // is not foolproof...
    const Flow* f = NULL;
    for (Operation::flowlist::const_iterator fiter = (*altIter)->getFlows().begin();
      fiter != (*altIter)->getFlows().end() && !f; ++fiter)
    {
      if (fiter->getQuantity() > 0.0 && fiter->getEffective().within(enddate))
        f = &*fiter;
    }

    // Create an operationplan instance
    (*altIter)->createOperationPlan(
      o->getQuantity() * propIter->first / sum_percent / (f ? f->getQuantity() : 1.0),
      o->getDates().getStart(), enddate, NULL, o, 0, true
      );
  }
  return true;
}


DECLARE_EXPORT void OperationSplit::removeSubOperation(Operation *o)
{
  Operationlist::iterator altIter = alternates.begin();
  alternatePropertyList::iterator propIter = alternateProperties.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++propIter;
    ++altIter;
  }
  if (*altIter == o)
  {
    alternates.erase(altIter);
    alternateProperties.erase(propIter);
    o->superoplist.remove(this);
    setChanged();
  }
  else
    logger << "Warning: operation '" << *o
        << "' isn't a suboperation of split operation '" << *this
        << "'" << endl;
}


DECLARE_EXPORT OperationPlanState OperationSetup::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, bool execute) const
{
  // Find or create a loadplan
  OperationPlan::LoadPlanIterator i = opplan->beginLoadPlans();
  LoadPlan *ldplan = NULL;
  if (i != opplan->endLoadPlans())
    // Already exists
    ldplan = &*i;
  else
  {
    // Create a new one
    if (!opplan->getOwner())
      throw LogicException("Setup operationplan always must have an owner");
    for (loadlist::const_iterator g=opplan->getOwner()->getOperation()->getLoads().begin();
        g!=opplan->getOwner()->getOperation()->getLoads().end(); ++g)
      if (g->getResource()->getSetupMatrix() && !g->getSetup().empty())
      {
        ldplan = new LoadPlan(opplan, &*g);
        break;
      }
    if (!ldplan)
      throw LogicException("Can't find a setup on operation '"
          + opplan->getOwner()->getOperation()->getName() + "'");
  }

  // Find the setup of the resource at the start of the conversion
  const Load* lastld = NULL;
  Date boundary = s ? s : e;
  if (ldplan->getDate() < boundary)
  {
    for (TimeLine<LoadPlan>::const_iterator i = ldplan->getResource()->getLoadPlans().begin(ldplan);
        i != ldplan->getResource()->getLoadPlans().end() && i->getDate() <= boundary; ++i)
    {
      const LoadPlan *l = dynamic_cast<const LoadPlan*>(&*i);
      if (l && i->getQuantity() != 0.0
          && l->getOperationPlan() != opplan
          && l->getOperationPlan() != opplan->getOwner()
          && !l->getLoad()->getSetup().empty())
        lastld = l->getLoad();
    }
  }
  if (!lastld)
  {
    for (TimeLine<LoadPlan>::const_iterator i = ldplan->getResource()->getLoadPlans().begin(ldplan);
        i != ldplan->getResource()->getLoadPlans().end(); --i)
    {
      const LoadPlan *l = dynamic_cast<const LoadPlan*>(&*i);
      if (l && i->getQuantity() != 0.0
          && l->getOperationPlan() != opplan
          && l->getOperationPlan() != opplan->getOwner()
          && !l->getLoad()->getSetup().empty()
          && l->getDate() <= boundary)
      {
        lastld = l->getLoad();
        break;
      }
    }
  }
  string lastsetup = lastld ? lastld->getSetup() : ldplan->getResource()->getSetup();

  TimePeriod duration(0L);
  if (lastsetup != ldplan->getLoad()->getSetup())
  {
    // Calculate the setup time
    SetupMatrix::Rule *conversionrule = ldplan->getLoad()->getResource()->getSetupMatrix()
        ->calculateSetup(lastsetup, ldplan->getLoad()->getSetup());
    duration = conversionrule ? conversionrule->getDuration() : TimePeriod(365L*86400L);
  }

  // Set the start and end date.
  DateRange x;
  TimePeriod actualduration;
  if (e && s)
  {
    if (preferEnd) x = calculateOperationTime(e, duration, false, &actualduration);
    else x = calculateOperationTime(s, duration, true, &actualduration);
  }
  else if (s) x = calculateOperationTime(s, duration, true, &actualduration);
  else x = calculateOperationTime(e, duration, false, &actualduration);
  if (!execute)
    // Simulation only
    return OperationPlanState(x, actualduration == duration ? q : 0);
  else if (actualduration == duration)
  {
    // Update succeeded
    opplan->setStartAndEnd(x.getStart(), x.getEnd());
    if (opplan->getOwner()->getDates().getStart() != opplan->getDates().getEnd())
      opplan->getOwner()->setStart(opplan->getDates().getEnd());
  }
  else
    // Update failed - Not enough available time @todo setting the qty to 0 is not enough
    opplan->setQuantity(0);

  return OperationPlanState(opplan);
}


DECLARE_EXPORT PyObject* Operation::getattro(const Attribute& attr)
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
  if (attr.isA(Tags::tag_location))
    return PythonObject(getLocation());
  if (attr.isA(Tags::tag_fence))
    return PythonObject(getFence());
  if (attr.isA(Tags::tag_size_minimum))
    return PythonObject(getSizeMinimum());
  if (attr.isA(Tags::tag_size_multiple))
    return PythonObject(getSizeMultiple());
  if (attr.isA(Tags::tag_size_maximum))
    return PythonObject(getSizeMaximum());
  if (attr.isA(Tags::tag_cost))
    return PythonObject(getCost());
  if (attr.isA(Tags::tag_posttime))
    return PythonObject(getPostTime());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(getHidden());
  if (attr.isA(Tags::tag_loads))
    return new LoadIterator(this);
  if (attr.isA(Tags::tag_flows))
    return new FlowIterator(this);
  if (attr.isA(Tags::tag_operationplans))
    return new OperationPlanIterator(this);
  if (attr.isA(Tags::tag_level))
    return PythonObject(getLevel());
  if (attr.isA(Tags::tag_cluster))
    return PythonObject(getCluster());
  return NULL;
}


DECLARE_EXPORT int Operation::setattro(const Attribute& attr, const PythonObject& field)
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
  else if (attr.isA(Tags::tag_location))
  {
    if (!field.check(Location::metadata))
    {
      PyErr_SetString(PythonDataException, "buffer location must be of type location");
      return -1;
    }
    Location* y = static_cast<Location*>(static_cast<PyObject*>(field));
    setLocation(y);
  }
  else if (attr.isA(Tags::tag_fence))
    setFence(field.getTimeperiod());
  else if (attr.isA(Tags::tag_size_minimum))
    setSizeMinimum(field.getDouble());
  else if (attr.isA(Tags::tag_size_multiple))
    setSizeMultiple(field.getDouble());
  else if (attr.isA(Tags::tag_size_maximum))
    setSizeMaximum(field.getDouble());
  else if (attr.isA(Tags::tag_cost))
    setCost(field.getDouble());
  else if (attr.isA(Tags::tag_posttime))
    setPostTime(field.getTimeperiod());
  else if (attr.isA(Tags::tag_hidden))
    setHidden(field.getBool());
  else
    return -1;  // Error
  return 0;  // OK
}


DECLARE_EXPORT PyObject* OperationFixedTime::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_duration))
    return PythonObject(getDuration());
  return Operation::getattro(attr);
}


DECLARE_EXPORT int OperationFixedTime::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_duration))
    setDuration(field.getTimeperiod());
  else
    return Operation::setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* OperationTimePer::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_duration))
    return PythonObject(getDuration());
  if (attr.isA(Tags::tag_duration_per))
    return PythonObject(getDurationPer());
  return Operation::getattro(attr);
}


DECLARE_EXPORT int OperationTimePer::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_duration))
    setDuration(field.getTimeperiod());
  else if (attr.isA(Tags::tag_duration_per))
    setDurationPer(field.getDouble());
  else
    return Operation::setattro(attr, field);
  return 0;
}

DECLARE_EXPORT PyObject* OperationSplit::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_alternates))
  {
    PyObject* result = PyTuple_New(getSubOperations().size());
    alternatePropertyList::const_iterator j = alternateProperties.begin();
    int count = 0;
    for (Operation::Operationlist::const_iterator i = getSubOperations().begin();
      i != getSubOperations().end(); i++, j++)
      PyTuple_SetItem(result, count++, Py_BuildValue("(OiNN)",
        static_cast<PyObject*>(*i),
        j->first,
        static_cast<PyObject*>(PythonObject(j->second.getStart())),
        static_cast<PyObject*>(PythonObject(j->second.getEnd()))
        ));
    return result;
  }
  return Operation::getattro(attr);
}


DECLARE_EXPORT PyObject* OperationSplit::addAlternate(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the alternate operation
    OperationSplit *altoper = static_cast<OperationSplit*>(self);
    if (!altoper) throw LogicException("Can't add alternates to NULL split");

    // Parse the arguments
    PyObject *oper = NULL;
    int percent = 0;
    PyObject *eff_start = NULL;
    PyObject *eff_end = NULL;
    static const char *kwlist[] = {"operation", "percent", "effective_start", "effective_end", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwdict,
        "O|iOO:addAlternate",
        const_cast<char**>(kwlist), &oper, &percent, &eff_start, &eff_end))
      return NULL;
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("alternate operation must be of type operation");
    DateRange eff;
    if (eff_start)
    {
      PythonObject d(eff_start);
      eff.setStart(d.getDate());
    }
    if (eff_end)
    {
      PythonObject d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Add the alternate
    altoper->addAlternate(static_cast<Operation*>(oper), percent, eff);
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* OperationAlternate::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_alternates))
  {
    PyObject* result = PyTuple_New(getSubOperations().size());
    alternatePropertyList::const_iterator j = alternateProperties.begin();
    int count = 0;
    for (Operation::Operationlist::const_iterator i = getSubOperations().begin();
      i != getSubOperations().end(); i++, j++)
      PyTuple_SetItem(result, count++, Py_BuildValue("(OiNN)",
        static_cast<PyObject*>(*i),
        j->first,
        static_cast<PyObject*>(PythonObject(j->second.getStart())),
        static_cast<PyObject*>(PythonObject(j->second.getEnd()))
        ));
    return result;
  }
  if (attr.isA(Tags::tag_search))
  {
    ostringstream ch;
    ch << getSearch();
    return PythonObject(ch.str());
  }
  return Operation::getattro(attr);
}


DECLARE_EXPORT int OperationAlternate::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_search))
    setSearch(field.getString());
  else
    return Operation::setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* OperationAlternate::addAlternate(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the alternate operation
    OperationAlternate *altoper = static_cast<OperationAlternate*>(self);
    if (!altoper) throw LogicException("Can't add alternates to NULL alternate");

    // Parse the arguments
    PyObject *oper = NULL;
    int prio = 1;
    PyObject *eff_start = NULL;
    PyObject *eff_end = NULL;
    static const char *kwlist[] = {"operation", "priority", "effective_start", "effective_end", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwdict,
        "O|iOO:addAlternate",
        const_cast<char**>(kwlist), &oper, &prio, &eff_start, &eff_end))
      return NULL;
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("alternate operation must be of type operation");
    DateRange eff;
    if (eff_start)
    {
      PythonObject d(eff_start);
      eff.setStart(d.getDate());
    }
    if (eff_end)
    {
      PythonObject d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Add the alternate
    altoper->addAlternate(static_cast<Operation*>(oper), prio, eff);
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* OperationRouting::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_steps))
  {
    PyObject* result = PyTuple_New(getSubOperations().size());
    int count = 0;
    for (Operation::Operationlist::const_iterator i = getSubOperations().begin(); i != getSubOperations().end(); ++i)
      PyTuple_SetItem(result, count++, PythonObject(*i));
    return result;
  }
  return Operation::getattro(attr);
}


PyObject *OperationRouting::addStep(PyObject *self, PyObject *args)
{
  try
  {
    // Pick up the routing operation
    OperationRouting *oper = static_cast<OperationRouting*>(self);
    if (!oper) throw LogicException("Can't add steps to NULL routing");

    // Parse the arguments
    PyObject *steps[4];
    for (unsigned int i=0; i<4; ++i) steps[i] = NULL;
    if (PyArg_UnpackTuple(args, "addStep", 1, 4, &steps[0], &steps[1], &steps[2], &steps[3]))
      for (unsigned int i=0; i<4 && steps[i]; ++i)
      {
        if (!PyObject_TypeCheck(steps[i], Operation::metadata->pythonClass))
          throw DataException("routing steps must be of type operation");
        oper->addStepBack(static_cast<Operation*>(steps[i]));
      }
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT void Operation::addSubOperationPlan(
  OperationPlan* parent, OperationPlan* child, bool fast
  )
{
  // Check
  if (!parent)
    throw LogicException("Invalid parent for suboperationplan");
  if (!child)
    throw LogicException("Adding null suboperationplan");
  if (child->getOperation() != OperationSetup::setupoperation)
    throw LogicException("Only setup suboperationplans are allowed");
  if (parent->firstsubopplan)
    throw LogicException("Expected suboperationplan list to be empty");

  // Adding a suboperationplan that was already added
  if (child->owner == parent)  return;

  // Clear the previous owner, if there is one
  if (child->owner) child->owner->eraseSubOperationPlan(child);

  // Set as only child operationplan
  parent->firstsubopplan = child;
  parent->lastsubopplan = child;
  child->owner = parent;

  // Update the flow and loadplans
  parent->update();
}


DECLARE_EXPORT void OperationSplit::addSubOperationPlan(
  OperationPlan* parent, OperationPlan* child, bool fast
  )
{
  // Check
  if (!parent)
    throw LogicException("Invalid parent for suboperationplan");
  if (!child)
    throw DataException("Adding null suboperationplan");

  // Adding a suboperationplan that was already added
  if (child->owner == parent)  return;

  if (!fast)
  {
    // Check whether the new alternate is a valid suboperation
    bool ok = false;
    const Operationlist& alts = parent->getOperation()->getSubOperations();
    for (Operationlist::const_iterator i = alts.begin(); i != alts.end(); i++)
      if (*i == child->getOperation())
      {
        ok = true;
        break;
      }
    if (!ok) throw DataException("Invalid split suboperationplan");
  }

  // The new child operationplan is inserted as the first unlocked
  // suboperationplan.
  if (!parent->firstsubopplan)
  {
    // First element
    parent->firstsubopplan = child;
    parent->lastsubopplan = child;
  }
  else if (parent->firstsubopplan->getOperation() != OperationSetup::setupoperation)
  {
    // New head
    child->nextsubopplan = parent->firstsubopplan;
    parent->firstsubopplan->prevsubopplan = child;
    parent->firstsubopplan = child;
  }
  else
  {
    // Insert right after the setup operationplan
    OperationPlan *s = parent->firstsubopplan->nextsubopplan;
    child->nextsubopplan = s;
    if (s) s->nextsubopplan = child;
    else parent->lastsubopplan = child;
  }

  // Update the owner
  if (child->owner) child->owner->eraseSubOperationPlan(child);
  child->owner = parent;

  // Update the flow and loadplans
  parent->update();
}


DECLARE_EXPORT void OperationAlternate::addSubOperationPlan(
  OperationPlan* parent, OperationPlan* child, bool fast
  )
{
  // Check
  if (!parent)
    throw LogicException("Invalid parent for suboperationplan");
  if (!child)
    throw DataException("Adding null suboperationplan");

  // Adding a suboperationplan that was already added
  if (child->owner == parent)  return;

  if (!fast)
  {
    // Check whether the new alternate is a valid suboperation
    bool ok = false;
    const Operationlist& alts = parent->getOperation()->getSubOperations();
    for (Operationlist::const_iterator i = alts.begin(); i != alts.end(); i++)
      if (*i == child->getOperation())
      {
        ok = true;
        break;
      }
    if (!ok) throw DataException("Invalid alternate suboperationplan");
  }

  // Link in the list, keeping the right ordering
  if (!parent->firstsubopplan)
  {
    // First element
    parent->firstsubopplan = child;
    parent->lastsubopplan = child;
  }
  else if (parent->firstsubopplan->getOperation() != OperationSetup::setupoperation)
  {
    // Remove previous head alternate suboperationplan
    if (parent->firstsubopplan->getLocked())
      throw DataException("Can't replace locked alternate suboperationplan");
    OperationPlan *tmp = parent->firstsubopplan;
    parent->eraseSubOperationPlan(tmp);
    delete tmp;
    // New head
    parent->firstsubopplan = child;
    parent->lastsubopplan = child;
  }
  else
  {
    // Insert right after the setup operationplan
    OperationPlan *s = parent->firstsubopplan->nextsubopplan;

    // Remove previous alternate suboperationplan
    if (s)
    {
      if (s->getLocked())
        throw LogicException("Can't replace locked alternate suboperationplan");
      parent->eraseSubOperationPlan(s);
      delete s;
    }
    else
    {
      parent->firstsubopplan->nextsubopplan = child;
      parent->lastsubopplan = child;
    }
  }

  // Update the owner
  if (child->owner) child->owner->eraseSubOperationPlan(child);
  child->owner = parent;

  // Update the flow and loadplans
  parent->update();
}


DECLARE_EXPORT void OperationRouting::addSubOperationPlan
  (OperationPlan* parent, OperationPlan* child, bool fast)
{
  // Check
  if (!parent)
    throw LogicException("Invalid parent for suboperationplan");
  if (!child)
    throw LogicException("Adding null suboperationplan");

  // Adding a suboperationplan that was already added
  if (child->owner == parent)  return;

  // Link in the suoperationplan list
  if (fast)
  {
    // Method 1: Fast insertion
    // The new child operationplan is inserted as the first unlocked
    // suboperationplan.
    // No validation of the input data is performed.
    // We assume the child operationplan to be unlocked.
    // No netting with locked suboperationplans.
    if (!parent->firstsubopplan)
    {
      // First element
      parent->firstsubopplan = child;
      parent->lastsubopplan = child;
    }
    else if (parent->firstsubopplan->getOperation() != OperationSetup::setupoperation)
    {
      // New head
      child->nextsubopplan = parent->firstsubopplan;
      parent->firstsubopplan->prevsubopplan = child;
      parent->firstsubopplan = child;
    }
    else
    {
      // Insert right after the setup operationplan
      OperationPlan *s = parent->firstsubopplan->nextsubopplan;
      child->nextsubopplan = s;
      if (s) s->nextsubopplan = child;
      else parent->lastsubopplan = child;
    }
  }
  else
  {
    // Method 2: full validation
    // Child operationplan can be locked or unlocked.
    // We verify that the new operationplan is a valid step in the routing.
    // The child element is inserted at the right place in the list, which
    // considers its status locked/unlocked and its order in the routing.
    OperationPlan* matchingUnlocked = NULL;
    OperationPlan* prevsub = parent->firstsubopplan;
    if (prevsub && prevsub->getOperation() == OperationSetup::setupoperation)
      prevsub = prevsub->nextsubopplan;
    if (child->getLocked())
    {
      // Advance till first already registered locked suboperationplan
      while (prevsub && !prevsub->getLocked())
      {
        if (prevsub->getOperation() == child->getOperation())
          matchingUnlocked = prevsub;
        prevsub = prevsub->nextsubopplan;
      }
    }
    bool ok = false;
    for (Operationlist::const_iterator i = steps.begin(); i != steps.end(); i++)
    {
      if (*i == child->getOperation())
      {
        ok = true;
        break;
      }
      if (prevsub && *i == prevsub->getOperation())
        prevsub = prevsub->nextsubopplan;
    }
    if (!ok)
      throw DataException("Invalid routing suboperationplan");
    // At this point, we know the operation is a valid step. And the variable
    // prevsub points to the suboperationplan before which we need to insert
    // the new suboperationplan.
    if (prevsub && prevsub->getOperation() == child->getOperation())
    {
      if (prevsub->getLocked())
        throw DataException("Can't replace locked routing suboperationplan");
      parent->eraseSubOperationPlan(prevsub);
      OperationPlan* tmp = prevsub->nextsubopplan;
      delete prevsub;
      prevsub = tmp;
    }
    if (child->getLocked() && matchingUnlocked)
    {
      // Adjust the unlocked part of the operationplan
      matchingUnlocked->quantity = parent->quantity - child->quantity;
      if (matchingUnlocked->quantity < 0.0) matchingUnlocked->quantity = 0.0;
      matchingUnlocked->resizeFlowLoadPlans();
    }
    if (prevsub)
    {
      // Append in middle
      child->nextsubopplan = prevsub;
      child->prevsubopplan = prevsub->prevsubopplan;
      if (prevsub->prevsubopplan)
        prevsub->prevsubopplan->nextsubopplan = child;
      else
        parent->firstsubopplan = child;
      prevsub->prevsubopplan = child;
    }
    else if (parent->lastsubopplan)
    {
      // Append at end
      child->prevsubopplan = parent->lastsubopplan;
      parent->lastsubopplan->nextsubopplan = child;
      parent->lastsubopplan = child;
    }
    else
    {
      // First suboperationplan
      parent->lastsubopplan = child;
      parent->firstsubopplan = child;
    }
  }

  // Update the owner
  if (child->owner) child->owner->eraseSubOperationPlan(child);
  child->owner = parent;

  // Update the flow and loadplans
  parent->update();
}


DECLARE_EXPORT double Operation::setOperationPlanQuantity
  (OperationPlan* oplan, double f, bool roundDown, bool upd, bool execute) const
{
  assert(oplan);
  // No impact on locked operationplans
  if (oplan->getLocked()) return oplan->quantity;

  // Invalid operationplan: the quantity must be >= 0.
  if (f < 0)
    throw DataException("Operationplans can't have negative quantities");

  // Setting a quantity is only allowed on a top operationplan.
  // Two exceptions: on alternate and split operations the sizing on the
  // sub-operations is respected.
  if (oplan->owner && oplan->owner->getOperation()->getType() != *OperationAlternate::metadata
    && oplan->owner->getOperation()->getType() != *OperationSplit::metadata)
    return oplan->owner->setQuantity(f,roundDown,upd,execute);

  // Compute the correct size for the operationplan
  if (oplan->getOperation()->getType() == *OperationSplit::metadata)
  {
    // A split operation doesn't respect any size constraints at the parent level
    if (execute)
    {
      oplan->quantity = f;
      if (upd) oplan->update();
    }
    return f;
  }
  else
  {
    // All others respect constraints
    if (f!=0.0 && getSizeMinimum()>0.0 && f < getSizeMinimum())
    {
      if (roundDown)
      {
        // Smaller than the minimum quantity, rounding down means... nothing
        if (!execute) return 0.0;
        oplan->quantity = 0.0;
        // Update the flow and loadplans, and mark for problem detection
        if (upd) oplan->update();
        // Update the parent of an alternate operationplan
        if (oplan->owner && oplan->owner->getOperation()->getType() == *OperationAlternate::metadata)
        {
          oplan->owner->quantity = 0.0;
          if (upd) oplan->owner->resizeFlowLoadPlans();
        }
        return 0.0;
      }
      f = getSizeMinimum();
    }
    if (f != 0.0 && f >= getSizeMaximum())
    {
      roundDown = true; // force rounddown to stay below the limit
      f = getSizeMaximum();
    }
    if (f!=0.0 && getSizeMultiple()>0.0)
    {
      int mult = static_cast<int> (f / getSizeMultiple()
          + (roundDown ? 0.0 : 0.99999999));
      double q = mult * getSizeMultiple();
      if (q < getSizeMinimum())
      {
        q += getSizeMultiple();
        if (q > getSizeMaximum())
          throw DataException("Invalid sizing parameters for operation " + getName());
      }
      else if (q > getSizeMaximum())
      {
        q -= getSizeMultiple();
        if (q < getSizeMinimum())
          throw DataException("Invalid sizing parameters for operation " + getName());
      }
      if (!execute) return q;
      oplan->quantity = q;
    }
    else
    {
      if (!execute) return f;
      oplan->quantity = f;
    }
  }

  // Update the parent of an alternate operationplan
  if (execute && oplan->owner
      && oplan->owner->getOperation()->getType() == *OperationAlternate::metadata)
  {
    oplan->owner->quantity = oplan->quantity;
    if (upd) oplan->owner->resizeFlowLoadPlans();
  }

  // Apply the same size also to its unlocked children
  if (execute && oplan->firstsubopplan)
    for (OperationPlan *i = oplan->firstsubopplan; i; i = i->nextsubopplan)
      if (i->getOperation() != OperationSetup::setupoperation && !i->getLocked())
      {
        i->quantity = oplan->quantity;
        if (upd) i->resizeFlowLoadPlans();
      }

  // Update the flow and loadplans, and mark for problem detection
  if (upd) oplan->update();
  return oplan->quantity;
}


DECLARE_EXPORT double OperationRouting::setOperationPlanQuantity
  (OperationPlan* oplan, double f, bool roundDown, bool upd, bool execute) const
{
  assert(oplan);
  // Call the default logic, implemented on the Operation class
  double newqty = Operation::setOperationPlanQuantity(oplan, f, roundDown, false, execute);
  if (!execute) return newqty;

  // Update all routing sub operationplans
  for (OperationPlan *i = oplan->firstsubopplan; i; i = i->nextsubopplan)
  {
    if (i->getOperation() == OperationSetup::setupoperation)
      continue;
    if (i->getLocked())
    {
      // Find the unlocked operationplan on the same operation
      OperationPlan* match = i->prevsubopplan;
      while (match && match->getOperation() != i->getOperation())
        match = match->prevsubopplan;
      if (match)
      {
        match->quantity = newqty - i->quantity;
        if (match->quantity < 0.0) match->quantity = 0.0;
        if (upd) match->resizeFlowLoadPlans();
      }
    }
    else
    {
      i->quantity = newqty;
      if (upd) i->resizeFlowLoadPlans();
    }
  }

  // Update the flow and loadplans, and mark for problem detection
  if (upd) oplan->update();

  return newqty;
}


} // end namespace
