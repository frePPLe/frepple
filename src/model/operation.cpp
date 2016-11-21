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

template<class Operation> Tree utils::HasName<Operation>::st;
const MetaCategory* Operation::metadata;
const MetaClass* OperationFixedTime::metadata,
               *OperationTimePer::metadata,
               *OperationRouting::metadata,
               *OperationSplit::metadata,
               *OperationAlternate::metadata,
               *OperationSetup::metadata;
Operation::Operationlist Operation::nosubOperations;
Operation* OperationSetup::setupoperation;


int Operation::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Operation>(
    "operation", "operations", reader, finder
    );
  registerFields<Operation>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Operation>::initialize();
}


int OperationFixedTime::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationFixedTime>(
    "operation", "operation_fixed_time",
    Object::create<OperationFixedTime>, true
    );
  registerFields<OperationFixedTime>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<OperationFixedTime, Operation>::initialize();
}


int OperationTimePer::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationTimePer>(
    "operation", "operation_time_per",
    Object::create<OperationTimePer>
    );
  registerFields<OperationTimePer>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<OperationTimePer, Operation>::initialize();
}


int OperationSplit::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationSplit>(
    "operation", "operation_split",
    Object::create<OperationSplit>
    );
  registerFields<OperationSplit>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<OperationSplit, Operation>::initialize();
}


int OperationAlternate::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationAlternate>(
    "operation", "operation_alternate",
    Object::create<OperationAlternate>
    );
  registerFields<OperationAlternate>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<OperationAlternate, Operation>::initialize();
}


int OperationRouting::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationRouting>(
    "operation", "operation_routing",
    Object::create<OperationRouting>
    );
  registerFields<OperationRouting>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<OperationRouting,Operation>::initialize();
}


int OperationSetup::initialize()
{
  // Initialize the metadata.
  // There is NO factory method
  metadata = MetaClass::registerClass<OperationSetup>("operation", "operation_setup");

  // Initialize the Python class
  int tmp = FreppleClass<OperationSetup,Operation>::initialize();

  // Create a generic setup operation.
  // This will be the only instance of this class.
  setupoperation = new OperationSetup();
  setupoperation->setName("setup operation");

  return tmp;
}


void Operation::removeSuperOperation(Operation *o)
{
  if (!o) return;
  superoplist.remove(o);
  Operationlist::iterator i = o->getSubOperations().begin();
  while (i != o->getSubOperations().end())
  {
    if ((*i)->getOperation() == this)
    {
      SubOperation *tmp = *i;
      // note: erase also advances the iterator
      i = o->getSubOperations().erase(i);
      delete tmp;
    }
    else
      ++i;
  }
}


Operation::~Operation()
{
  // Delete all existing operationplans (even locked ones)
  deleteOperationPlans(true);

  // The Flow and Load objects are automatically deleted by the destructor
  // of the Association list class.

  // Unlink from item
  if (item)
  {
    if (item->firstOperation == this)
      // Remove from head
      item->firstOperation = next;
    else
    {
      // Remove from middle
      Operation *j = item->firstOperation;
      while (j->next && j->next != this)
        j = j->next;
      if (j)
        j->next = next;
      else
        logger << "Error: Corrupted Operation list on Item" << endl;
    }
  }

  // Remove the reference to this operation from all demands
  for (Demand::iterator l = Demand::begin(); l != Demand::end(); ++l)
    if (l->getOperation() == this)
      l->setOperation(nullptr);

  // Remove the reference to this operation from all buffers
  for (Buffer::iterator m = Buffer::begin(); m != Buffer::end(); ++m)
    if (m->getProducingOperation() == this)
      m->setProducingOperation(nullptr);

  // Remove the operation from its super-operations and sub-operations
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSuperOperations().empty())
    removeSuperOperation(*getSuperOperations().begin());
}


OperationRouting::~OperationRouting()
{
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSubOperations().empty())
    delete *getSubOperations().begin();
}


OperationSplit::~OperationSplit()
{
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSubOperations().empty())
    delete *getSubOperations().begin();
}


OperationAlternate::~OperationAlternate()
{
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSubOperations().empty())
    delete *getSubOperations().begin();
}


OperationPlan::iterator Operation::getOperationPlans() const
{
  return OperationPlan::iterator(this);
}


OperationPlan* Operation::createOperationPlan (double q, Date s, Date e,
    Demand* l, OperationPlan* ow, unsigned long i,
    bool makeflowsloads) const
{
  OperationPlan *opplan = new OperationPlan();
  initOperationPlan(opplan,q,s,e,l,ow,i,makeflowsloads);
  return opplan;
}


DateRange Operation::calculateOperationTime
(Date thedate, Duration duration, bool forward,
 Duration *actualduration) const
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
    Duration curduration = duration;
    while (true)
    {
      // Check whether all calendars are available
      bool available = true;
      for (int c = 0; c < calcount && available; c++)
      {
        const CalendarBucket *tmp = cals[c]->getBucket();
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
          Duration delta = curdate - thedate;
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
          Duration delta = thedate - curdate;
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
          Duration delta = curdate - thedate;
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
          Duration delta = thedate - curdate;
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


DateRange Operation::calculateOperationTime
(Date start, Date end, Duration *actualduration) const
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


void Operation::initOperationPlan (OperationPlan* opplan,
    double q, const Date& s, const Date& e, Demand* l, OperationPlan* ow,
    unsigned long i, bool makeflowsloads) const
{
  opplan->oper = const_cast<Operation*>(this);
  if (l) opplan->setDemand(l);
  opplan->id = i;

  // Setting the owner first. Note that the order is important here!
  // For alternates & routings the quantity needs to be set through the owner.
  if (ow) opplan->setOwner(ow);

  // Setting the dates and quantity
  setOperationPlanParameters(opplan, q, s, e);

  // Create the loadplans and flowplans, if allowed
  if (makeflowsloads) opplan->createFlowLoads();

  // Update flow and loadplans, and mark for problem detection
  opplan->update();
}


Flow* Operation::findFlow(const Buffer* b, Date d) const
{
  for (flowlist::const_iterator fl = flowdata.begin();
    fl != flowdata.end(); ++fl)
  {
    if (!fl->effectivity.within(d))
      continue;
    if (fl->getBuffer() == b)
        return const_cast<Flow*>(&*fl);
    else if (!fl->getBuffer() && fl->getItem() == b->getItem() && getLocation() == b->getLocation())
      return const_cast<Flow*>(&*fl);
  }
  return nullptr;
}


void Operation::deleteOperationPlans(bool deleteLockedOpplans)
{
  OperationPlan::deleteOperationPlans(this, deleteLockedOpplans);
}


OperationPlanState OperationFixedTime::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, bool execute) const
{
  // Invalid call to the function, or locked operationplan.
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for fixedtime operationplan");
  if (opplan->getLocked())
    return OperationPlanState(opplan);

  // Compute the start and end date.
  DateRange x;
  Duration actualduration;
  if (e && s)
  {
    if (preferEnd)
      x = calculateOperationTime(e, duration, false, &actualduration);
    else
      x = calculateOperationTime(s, duration, true, &actualduration);
  }
  else if (s)
    x = calculateOperationTime(s, duration, true, &actualduration);
  else
    x = calculateOperationTime(e, duration, false, &actualduration);

  // All quantities are valid, as long as they are above the minimum size and
  // below the maximum size
  if (q > 0)
  {
    if (getSizeMinimumCalendar())
    {
      // Minimum size varies over time
      double curmin = getSizeMinimumCalendar()->getValue(x.getEnd());
      if (q < curmin)
        q = curmin;
    }
    else if (q < getSizeMinimum())
      // Minimum size is constant over time
      q = getSizeMinimum();
  }
  if (q > getSizeMaximum())
    q = getSizeMaximum();
  if (fabs(q - opplan->getQuantity()) > ROUNDING_ERROR)
    q = opplan->setQuantity(q, false, false, execute, x.getEnd());

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


bool OperationFixedTime::extraInstantiate(OperationPlan* o)
{
  // See if we can consolidate this operationplan with an existing one.
  // Merging is possible only when all the following conditions are met:
  //   - id of the new opplan is not set
  //   - id of the old opplan is set
  //   - it is a fixedtime operation
  //   - it doesn't load any resources of type default
  //   - both operationplans aren't locked
  //   - both operationplans have no owner
  //     or both have an owner of the same operation and is of type operation_alternate
  //   - start and end date of both operationplans are the same
  //   - demand of both operationplans are the same
  //   - maximum operation size is not exceeded
  //   - alternate flowplans need to be on the same alternate
  if (!o->getRawIdentifier() && !o->getLocked())
  {
    // Verify we load no resources of type "default".
    // It's ok to merge operationplans which load "infinite" or "buckets" resources.
    for (Operation::loadlist::const_iterator i = getLoads().begin(); i != getLoads().end(); ++i)
      if (i->getResource()->getType() == *ResourceDefault::metadata)
        return true;

    // Loop through candidates
    OperationPlan::iterator x(this);
    OperationPlan *y = nullptr;
    for (; x != OperationPlan::end() && *x < *o; ++x)
      y = &*x;
    if (y && y->getDates() == o->getDates()
        && y->getDemand() == o->getDemand() && !y->getLocked() && y->getRawIdentifier()
        && y->getQuantity() + o->getQuantity() < getSizeMaximum())
    {
      if (o->getOwner())
      {
        // Both must have the same owner operation of type alternate
        if (!y->getOwner())
          return true;
        else if (o->getOwner()->getOperation() != y->getOwner()->getOperation())
          return true;
        else if (o->getOwner()->getOperation()->getType() != *OperationAlternate::metadata)
          return true;
        else if (o->getOwner()->getDemand() != y->getOwner()->getDemand())
          return true;
     }

      // Check that the flowplans are on identical alternates and not of type fixed
      OperationPlan::FlowPlanIterator fp1 = o->beginFlowPlans();
      OperationPlan::FlowPlanIterator fp2 = y->beginFlowPlans();
      if (fp1 == o->endFlowPlans() || fp2 == o->endFlowPlans())
        // Operationplan without flows are already deleted. Leave them alone.
        return true;
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
      if (o->getOwner())
        o->setOwner(nullptr);
      return false;
    }
    if (x!= OperationPlan::end() && x->getDates() == o->getDates()
        && x->getDemand() == o->getDemand() && !x->getLocked() && x->getRawIdentifier()
        && x->getQuantity() + o->getQuantity() < getSizeMaximum())
    {
      if (o->getOwner())
      {
        // Both must have the same owner operation of type alternate
        if (!x->getOwner())
          return true;
        else if (o->getOwner()->getOperation() != x->getOwner()->getOperation())
          return true;
        else if (o->getOwner()->getOperation()->getType() != *OperationAlternate::metadata)
          return true;
      }

      // Check that the flowplans are on identical alternates
      OperationPlan::FlowPlanIterator fp1 = o->beginFlowPlans();
      OperationPlan::FlowPlanIterator fp2 = x->beginFlowPlans();
      if (fp1 == o->endFlowPlans() || fp2 == o->endFlowPlans())
        // Operationplan without flows are already deleted. Leave them alone.
        return true;
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
      if (o->getOwner())
        o->setOwner(nullptr);
      return false;
    }
  }
  return true;
}


OperationPlanState
OperationTimePer::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, bool execute) const
{
  // Invalid call to the function.
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for timeper operationplan");
  if (opplan->getLocked())
    return OperationPlanState(opplan);

  // Respect minimum and maximum size
  if (q > 0)
  {
    if (getSizeMinimumCalendar())
    {
      // Minimum varies over time.
      // This configuration is not really supported: when the size changes
      // a different minimum size could be effective. The planning results
      // in a constrained plan can be not optimal or incorrect.
      Duration tmp1;
      DateRange tmp2 = calculateOperationTime(s, e, &tmp1);
      double curmin = getSizeMinimumCalendar()->getValue(tmp2.getEnd());
      if (q < curmin)
        q = curmin;
    }
    else if (q < getSizeMinimum())
      // Minimum is constant over time
      q = getSizeMinimum();
  }
  if (q > getSizeMaximum())
    q = getSizeMaximum();

  // The logic depends on which dates are being passed along
  DateRange x;
  Duration actual;
  if (s && e)
  {
    // Case 1: Both the start and end date are specified: Compute the quantity.
    // Calculate the available time between those dates
    x = calculateOperationTime(s,e,&actual);
    if (actual < duration)
    {
      // Start and end aren't far enough from each other to fit the constant
      // part of the operation duration. This is infeasible.
      if (!execute)
        return OperationPlanState(x, 0);
      opplan->setQuantity(0, true, false, execute);
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
                true, false, execute
                );
      }
      else
        // No duration_per field given, so any quantity will go
        q = opplan->setQuantity(q, true, false, execute);

      // Updates the dates
      // The cast on the next line truncates the decimal part. We add half a
      // second to get a rounded value.
      Duration wanted(
        duration + static_cast<long>(duration_per * q + 0.5)
      );
      if (preferEnd)
        x = calculateOperationTime(e, wanted, false, &actual);
      else
        x = calculateOperationTime(s, wanted, true, &actual);
      if (!execute)
        return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(), x.getEnd());
    }
  }
  else if (e || !s)
  {
    // Case 2: Only an end date is specified. Respect the quantity and
    // compute the start date
    // Case 4: No date was given at all. Respect the quantity and the
    // existing end date of the operationplan.
    q = opplan->setQuantity(q, true, false, execute);
    // Round and size the quantity
    // The cast on the next line truncates the decimal part. We add half a
    // second to get a rounded value.
    Duration wanted(duration + static_cast<long>(duration_per * q + 0.5));
    x = calculateOperationTime(e, wanted, false, &actual);
    if (actual == wanted)
    {
      // Size is as desired
      if (!execute)
        return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
    else if (actual < duration)
    {
      // Not feasible
      if (!execute)
        return OperationPlanState(x, 0);
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
      // The cast on the next line truncates the decimal part. We add half a
      // second to get a rounded value.
      wanted = duration + static_cast<long>(duration_per * q + 0.5);
      x = calculateOperationTime(e, wanted, false, &actual);
      if (!execute)
        return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(), x.getEnd());
    }
  }
  else
  {
    // Case 3: Only a start date is specified. Respect the quantity and
    // compute the end date
    q = opplan->setQuantity(q, true, false, execute);
    // Round and size the quantity
    // The cast on the next line truncates the decimal part. We add half a
    // second to get a rounded value.
    Duration wanted(
      duration + static_cast<long>(duration_per * q + 0.5)
    );
    Duration actual;
    x = calculateOperationTime(s, wanted, true, &actual);
    if (actual == wanted)
    {
      // Size is as desired
      if (!execute)
        return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
    else if (actual < duration)
    {
      // Not feasible
      if (!execute)
        return OperationPlanState(x, 0);
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
      // The cast on the next line truncates the decimal part. We add half a
      // second to get a rounded value.
      wanted = duration + static_cast<long>(duration_per * q + 0.5);
      x = calculateOperationTime(e, wanted, false, &actual);
      if (!execute)
        return OperationPlanState(x, q);
      opplan->setStartAndEnd(x.getStart(),x.getEnd());
    }
  }

  // Return value
  return OperationPlanState(opplan);
}


OperationPlanState OperationRouting::setOperationPlanParameters
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
    if (!s && e)
      s = e;
    if (s && !e)
      e = s;
    if (!execute)
      return OperationPlanState(s, e, q);
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
      x = i->getOperation()->setOperationPlanParameters(
        i, q, Date::infinitePast, e, preferEnd, execute
        );
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
      x = i->getOperation()->setOperationPlanParameters(
        i, q, s, Date::infinitePast, preferEnd, execute
        );
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


bool OperationRouting::extraInstantiate(OperationPlan* o)
{
  // Create step suboperationplans if they don't exist yet.
  if (!o->lastsubopplan || o->lastsubopplan->getOperation() == OperationSetup::setupoperation)
  {
    Date d = o->getDates().getEnd();
    OperationPlan *p = nullptr;
    // @todo not possible to initialize a routing oplan based on a start date
    if (d != Date::infiniteFuture)
    {
      // Using the end date
      for (Operation::Operationlist::const_reverse_iterator e =
          getSubOperations().rbegin(); e != getSubOperations().rend(); ++e)
      {
        p = (*e)->getOperation()->createOperationPlan(
          o->getQuantity(), Date::infinitePast, d, nullptr, o, 0, true
          );
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
        p = (*e)->getOperation()->createOperationPlan(
          o->getQuantity(), d, Date::infinitePast, nullptr, o, 0, true
          );
        d = p->getDates().getEnd();
      }
    }
  }
  return true;
}


SearchMode decodeSearchMode(const string& c)
{
  if (c == "PRIORITY")
    return PRIORITY;
  if (c == "MINCOST")
    return MINCOST;
  if (c == "MINPENALTY")
    return MINPENALTY;
  if (c == "MINCOSTPENALTY")
    return MINCOSTPENALTY;
  throw DataException("Invalid search mode " + c);
}


OperationPlanState
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
      opplan->setQuantity(q, false, false);
      opplan->setStartAndEnd(s, e);
      return OperationPlanState(opplan);
    }
    else
      return OperationPlanState(
        s, e, opplan->setQuantity(q, false, false, false)
        );
  }
  else
    // Pass the call to the sub-operation
    return x->getOperation()->setOperationPlanParameters(
      x, q, s, e, preferEnd, execute
      );
}


bool OperationAlternate::extraInstantiate(OperationPlan* o)
{
  // Create a suboperationplan if one doesn't exist yet.
  // We use the first effective alternate by default.
  if (!o->lastsubopplan || o->lastsubopplan->getOperation() == OperationSetup::setupoperation)
  {
    // Find the right operation
    Operationlist::const_iterator altIter = getSubOperations().begin();
    for (; altIter != getSubOperations().end(); )
    {
      // Filter out alternates that are not suitable
      if ((*altIter)->getPriority() != 0 && (*altIter)->getEffective().within(o->getDates().getEnd()))
        break;
    }
    if (altIter != getSubOperations().end())
      // Create an operationplan instance
      (*altIter)->getOperation()->createOperationPlan(
        o->getQuantity(), o->getDates().getStart(),
        o->getDates().getEnd(), nullptr, o, 0, true);
  }
  return true;
}


OperationPlanState
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


bool OperationSplit::extraInstantiate(OperationPlan* o)
{
  if (o->lastsubopplan && o->lastsubopplan->getOperation() != OperationSetup::setupoperation)
    // Suboperationplans already exist. Nothing to do here.
    return true;

  // Compute the sum of all effective percentages.
  int sum_percent = 0;
  Date enddate = o->getDates().getEnd();
  for (Operation::Operationlist::const_iterator altIter = getSubOperations().begin();
    altIter != getSubOperations().end();
    ++altIter)
  {
    if ((*altIter)->getEffective().within(enddate))
      sum_percent += (*altIter)->getPriority();
  }
  if (!sum_percent)
    // Oops, no effective suboperations found.
    // Let's not create any suboperationplans then.
    return true;

  // Create all child operationplans
  for (Operation::Operationlist::const_iterator altIter = getSubOperations().begin();
    altIter != getSubOperations().end();
    ++altIter)
  {
    // Verify effectivity date and percentage > 0
    if (!(*altIter)->getPriority() || !(*altIter)->getEffective().within(enddate))
      continue;

    // Find the first producing flow.
    // In case the split suboperation produces multiple materials this code
    // is not foolproof...
    const Flow* f = nullptr;
    for (Operation::flowlist::const_iterator fiter = (*altIter)->getOperation()->getFlows().begin();
      fiter != (*altIter)->getOperation()->getFlows().end() && !f; ++fiter)
    {
      if (fiter->getQuantity() > 0.0 && fiter->getEffective().within(enddate))
        f = &*fiter;
    }

    // Create an operationplan instance
    (*altIter)->getOperation()->createOperationPlan(
      o->getQuantity() * (*altIter)->getPriority() / sum_percent / (f ? f->getQuantity() : 1.0),
      o->getDates().getStart(), enddate, nullptr, o, 0, true
      );
  }
  return true;
}


OperationPlanState OperationSetup::setOperationPlanParameters
(OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, bool execute) const
{
  // Find or create a loadplan
  OperationPlan::LoadPlanIterator i = opplan->beginLoadPlans();
  LoadPlan *ldplan = nullptr;
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
  const Load* lastld = nullptr;
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

  Duration duration(0L);
  if (lastsetup != ldplan->getLoad()->getSetup())
  {
    // Calculate the setup time
    SetupMatrixRule *conversionrule = ldplan->getLoad()->getResource()->getSetupMatrix()
        ->calculateSetup(lastsetup, ldplan->getLoad()->getSetup());
    duration = conversionrule ? conversionrule->getDuration() : Duration(365L*86400L);
  }

  // Set the start and end date.
  DateRange x;
  Duration actualduration;
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


void Operation::addSubOperationPlan(
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


void OperationSplit::addSubOperationPlan(
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
      if ((*i)->getOperation() == child->getOperation())
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


void OperationAlternate::addSubOperationPlan(
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
      if ((*i)->getOperation() == child->getOperation())
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
    //if (parent->firstsubopplan->getLocked())
    //  throw DataException("Can't replace locked alternate suboperationplan");
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
      //if (s->getLocked())
      //  throw DataException("Can't replace locked alternate suboperationplan");
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


void OperationRouting::addSubOperationPlan
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
    OperationPlan* matchingUnlocked = nullptr;
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
      if ((*i)->getOperation() == child->getOperation())
      {
        ok = true;
        break;
      }
      if (prevsub && (*i)->getOperation() == prevsub->getOperation())
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


double Operation::setOperationPlanQuantity
  (OperationPlan* oplan, double f, bool roundDown, bool upd, bool execute, Date end) const
{
  assert(oplan);

  // Invalid operationplan: the quantity must be >= 0.
  if (f < 0)
    throw DataException("Operationplans can't have negative quantities");

  // Locked operationplans don't respect sizing constraints
  if (oplan->getLocked())
  {
    if (execute)
    {
      oplan->quantity = f;
      if (upd) oplan->update();
    }
    return f;
  }

  // Setting a quantity is only allowed on a top operationplan.
  // Two exceptions: on alternate and split operations the sizing on the
  // sub-operations is respected.
  if (oplan->owner && oplan->owner->getOperation()->getType() != *OperationAlternate::metadata
    && oplan->owner->getOperation()->getType() != *OperationSplit::metadata)
    return oplan->owner->setQuantity(f, roundDown, upd, execute, end);

  // Compute the correct size for the operationplan
  if (oplan->getOperation()->getType() == *OperationSplit::metadata)
  {
    // A split operation doesn't respect any size constraints at the parent level
    if (execute)
    {
      oplan->quantity = f;
      if (upd)
        oplan->update();
    }
    return f;
  }
  else
  {
    // All others respect constraints
    double curmin;
    if (getSizeMinimumCalendar())
      // Minimum varies over time
      curmin = getSizeMinimumCalendar()->getValue(end ? end : oplan->getDates().getEnd());
    else
      // Minimum is constant
      curmin = getSizeMinimum();    
    if (f != 0.0 && curmin > 0.0 && f <= curmin - ROUNDING_ERROR)
    {
      if (roundDown)
      {
        // Smaller than the minimum quantity, rounding down means... nothing
        if (!execute)
          return 0.0;
        oplan->quantity = 0.0;
        // Update the flow and loadplans, and mark for problem detection
        if (upd)
          oplan->update();
        // Update the parent of an alternate operationplan
        if (oplan->owner && oplan->owner->getOperation()->getType() == *OperationAlternate::metadata)
        {
          oplan->owner->quantity = 0.0;
          if (upd)
            oplan->owner->resizeFlowLoadPlans();
        }
        return 0.0;
      }
      f = curmin;
    }
    if (f != 0.0 && f >= getSizeMaximum())
    {
      roundDown = true; // force rounddown to stay below the limit
      f = getSizeMaximum();
    }
    if (f != 0.0 && getSizeMultiple() > 0.0)
    {
      int mult = static_cast<int> (f / getSizeMultiple()
          + (roundDown ? 0.0 : 0.99999999));
      double q = mult * getSizeMultiple();
      if (q < curmin)
      {
        if (roundDown)
        {
          // Smaller than the minimum quantity, rounding down means... nothing
          if (!execute)
            return 0.0;
          oplan->quantity = 0.0;
          // Update the flow and loadplans, and mark for problem detection
          if (upd)
            oplan->update();
          // Update the parent of an alternate operationplan
          if (oplan->owner && oplan->owner->getOperation()->getType() == *OperationAlternate::metadata)
          {
            oplan->owner->quantity = 0.0;
            if (upd)
              oplan->owner->resizeFlowLoadPlans();
          }
          return 0.0;
        }
        else
        {
          q += getSizeMultiple();
          if (q > getSizeMaximum())
            throw DataException("Invalid sizing parameters for operation " + getName());
        }
      }
      else if (q > getSizeMaximum())
      {
        q -= getSizeMultiple();
        if (q < curmin)
          throw DataException("Invalid sizing parameters for operation " + getName());
      }
      if (!execute)
        return q;
      oplan->quantity = q;
    }
    else
    {
      if (!execute)
        return f;
      oplan->quantity = f;
    }
  }

  // Update the parent of an alternate operationplan
  if (execute && oplan->owner
      && oplan->owner->getOperation()->getType() == *OperationAlternate::metadata)
  {
    oplan->owner->quantity = oplan->quantity;
    if (upd)
      oplan->owner->resizeFlowLoadPlans();
  }

  // Apply the same size also to its unlocked children
  if (execute && oplan->firstsubopplan)
    for (OperationPlan *i = oplan->firstsubopplan; i; i = i->nextsubopplan)
      if (i->getOperation() != OperationSetup::setupoperation && !i->getLocked())
      {
        i->quantity = oplan->quantity;
        if (upd)
          i->resizeFlowLoadPlans();
      }

  // Update the flow and loadplans, and mark for problem detection
  if (upd)
    oplan->update();
  return oplan->quantity;
}


double OperationRouting::setOperationPlanQuantity
  (OperationPlan* oplan, double f, bool roundDown, bool upd, bool execute, Date end) const
{
  assert(oplan);
  // Call the default logic, implemented on the Operation class
  double newqty = Operation::setOperationPlanQuantity(oplan, f, roundDown, false, execute, end);
  if (!execute)
    return newqty;

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


void Operation::setItem(Item* i)
{
  // Unlink from previous item
  if (item)
  {
    if (item->firstOperation == this)
      // Remove from head
      item->firstOperation = next;
    else
    {
      // Remove from middle
      Operation *j = item->firstOperation;
      while (j->next && j->next != this)
        j = j->next;
      if (j)
        j->next = next;
      else
        throw LogicException("Corrupted Operation list on Item");
    }
  }

  // Update item
  item = i;

  // Link at the new owner.
  // We insert ourself at the head of the list.
  if (item)
  {
    next = item->firstOperation;
    item->firstOperation = this;
  }

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}

} // end namespace
