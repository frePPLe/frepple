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

template<class Operation> Tree<string> utils::HasName<Operation>::st;
const MetaCategory* Operation::metadata;
const MetaClass* OperationFixedTime::metadata,
               *OperationTimePer::metadata,
               *OperationRouting::metadata,
               *OperationSplit::metadata,
               *OperationAlternate::metadata;
Operation::Operationlist Operation::nosubOperations;


int Operation::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Operation>(
    "operation", "operations", reader, finder
    );
  registerFields<Operation>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<Operation>::getPythonType();
  x.addMethod("decoupledLeadTime", &getDecoupledLeadTimePython, METH_VARARGS, "return the total lead time");
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
    bool makeflowsloads, bool roundDown) const
{
  OperationPlan *opplan = new OperationPlan();
  initOperationPlan(opplan, q, s, e, l, ow, i, makeflowsloads, roundDown);
  return opplan;
}


DateRange Operation::calculateOperationTime(
  const OperationPlan* opplan, Date thedate, Duration duration, bool forward, Duration *actualduration
) const
{
  // Default actual duration
  if (actualduration)
    *actualduration = duration;

  // Step 1: Create an iterator over all involved calendars
  vector<Calendar::EventIterator> cals;
  collectCalendars(cals, thedate, opplan, forward);

  // Special case: no calendars at all
  if (cals.empty())
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
    Date selected = forward ? Date::infiniteFuture : Date::infinitePast;
    for (auto t = cals.begin(); t != cals.end(); ++t)
    {
      if (
        (forward && t->getDate() < selected)
        || (!forward && t->getDate() > selected)
        )
      {
        selected = t->getDate();
        if (forward && available && t->getValue() == 0)
          available = false;
      }
    }
    if (!forward)
    {
      for (auto t = cals.begin(); t != cals.end(); ++t)
      {
        if (available && t->getCalendar()->getValue(selected, forward) == 0)
          available = false;
      }
    }
    if (!duration && !available)
    {
      // A special case for 0-time operations.
      available = true;
      for (auto t = cals.begin(); t != cals.end() && available; ++t)
        available = (t->getCalendar()->getValue(selected, !forward) != 0);
      if (available)
      {
        result.setEnd(curdate);
        result.setStart(curdate);
        return result;
      }
    }
    curdate = selected;

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
    if (forward)
    {
      for (auto t = cals.begin(); t != cals.end(); ++t)
        if (t->getDate() == selected)
          ++(*t);
    }
    else
    {
      for (auto t = cals.begin(); t != cals.end(); ++t)
        if (t->getDate() == selected)
          --(*t);
    }
  }

  return result;
}


void Operation::collectCalendars(
  vector<Calendar::EventIterator>& cals, Date start, const OperationPlan* opplan, bool forward
) const
{
  // a) operation
  if (available)
    cals.push_back(Calendar::EventIterator(available, start, forward));
  // b) operation location
  if (loc && loc->getAvailable() && getAvailable() != loc->getAvailable())
    cals.push_back(Calendar::EventIterator(loc->getAvailable(), start, forward));

  if (opplan && opplan->getLoadPlans() != opplan->endLoadPlans())
  {
    // Iterate over loads
    for (auto g = opplan->getLoadPlans(); g != opplan->endLoadPlans(); ++g)
    {
      Resource* res = g->getResource();
      if (res->getAvailable())
      {
        // c) resource
        bool exists = false;
        for (auto t = cals.begin(); t != cals.end(); ++t)
        {
          if (t->getCalendar() == res->getAvailable())
          {
            exists = true;
            break;
          }
        }
        if (!exists)
          cals.push_back(Calendar::EventIterator(res->getAvailable(), start, forward));
      }
      if (res->getLocation() && res->getLocation()->getAvailable())
      {
        bool exists = false;
        for (auto t = cals.begin(); t != cals.end(); ++t)
        {
          // d) resource location
          if (t->getCalendar() == res->getLocation()->getAvailable())
          {
            exists = true;
            break;
          }
        }
        if (!exists)
          cals.push_back(Calendar::EventIterator(res->getLocation()->getAvailable(), start, forward));
      }
    }
  }
  else
  {
    // Iterate over loads
    for (auto g = loaddata.begin(); g != loaddata.end(); ++g)
    {
      Resource* res = g->getResource();
      if (res->getAvailable())
      {
        // c) resource
        bool exists = false;
        for (auto t = cals.begin(); t != cals.end(); ++t)
        {
          if (t->getCalendar() == res->getAvailable())
          {
            exists = true;
            break;
          }
        }
        if (!exists)
          cals.push_back(Calendar::EventIterator(res->getAvailable(), start, forward));
      }
      if (res->getLocation() && res->getLocation()->getAvailable())
      {
        bool exists = false;
        for (auto t = cals.begin(); t != cals.end(); ++t)
        {
          // d) resource location
          if (t->getCalendar() == res->getLocation()->getAvailable())
          {
            exists = true;
            break;
          }
        }
        if (!exists)
          cals.push_back(Calendar::EventIterator(res->getLocation()->getAvailable(), start, forward));
      }
    }
  }
}


DateRange Operation::calculateOperationTime(
  const OperationPlan* opplan, Date start, Date end, Duration *actualduration
) const
{
  // Switch start and end if required
  if (end < start)
  {
    Date tmp = start;
    start = end;
    end = tmp;
  }

  // Default actual duration
  if (actualduration)
    *actualduration = 0L;

  // Step 1: Create an iterator over all involved calendars
  vector<Calendar::EventIterator> cals;
  collectCalendars(cals, start, opplan);

  // Special case: no calendars at all
  if (!cals.size())
  {
    if (actualduration)
      *actualduration = end - start;
    return DateRange(start, end);
  }

  // Step 2: Iterate over the calendar dates to find periods where all
  // calendars are simultaneously effective.
  DateRange result;
  Date curdate = start;
  bool status = false;
  while (true)
  {
    // Check whether all calendars are available
    bool available = true;
    Date selected = Date::infiniteFuture;
    for (auto t = cals.begin(); t != cals.end(); ++t)
    {
      if (t->getDate() < selected)
        selected = t->getDate();
    }
    curdate = selected;
    for (auto t = cals.begin(); t != cals.end() && available; ++t)
      // TODO next line does a pretty expensive lookup in the calendar, which we might be available to avoid
      available = (t->getCalendar()->getValue(selected) != 0);
    
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
        if (actualduration)
          *actualduration += end - start;
        result.setEnd(end);
        break;
      }
      status = false;
      if (actualduration)
        *actualduration += curdate - start;
      start = curdate;
    }
    else if (curdate >= end)
    {
      // Leaving the desired date range
      if (available)
      {
        if (actualduration)
          *actualduration += end - start;
        result.setEnd(end);
        break;
      }
      else
        result.setEnd(start);
      break;
    }

    // Advance to the next event
    for (auto t = cals.begin(); t != cals.end(); ++t)
      if (t->getDate() == selected)
        ++(*t);
  }
  return result;
}


Operation::SetupInfo Operation::calculateSetup(
  OperationPlan* opplan, Date setupend, SetupEvent* setupevent, SetupEvent** prevevent
  ) const
{
  // Shortcuts: there are no setup matrices or resources
  if (SetupMatrix::empty() || getLoads().empty() || !opplan || !opplan->getQuantity())
    return SetupInfo(nullptr, nullptr, PooledString());

  // Loop over each load or loadplan and see check what setup time they need
  bool firstResourceWithSetup = true;
  auto ldplan = opplan->beginLoadPlans();
  if (ldplan == opplan->endLoadPlans())
  {
    // First case: This operationplan doesn't have any loadplans yet.
    for (auto ld = getLoads().begin(); ld != getLoads().end(); ++ld)
    {
      if (ld->getSetup().empty() || !ld->getResource()->getSetupMatrix())
        // There is no setup on this load
        continue;

      // An operation can load only a single resource with a setup matrix
      if (firstResourceWithSetup)
        firstResourceWithSetup = false;
      else
        throw DataException("Only a single resource with a setup matrix is allowed per operation");

      // Calculate the setup time
      SetupEvent* cursetup = setupevent ?
        setupevent->getSetupBefore() :
        ld->getResource()->getSetupAt(setupend, opplan);
      if (prevevent)
        *prevevent = cursetup;
      return SetupInfo(
        ld->getResource(),
        ld->getResource()->getSetupMatrix()->calculateSetup(cursetup ? cursetup->getSetup() : "", ld->getSetup(), ld->getResource()),
        ld->getSetup()
        );
    }
  }
  else
  {
    // Second case: This operationplan already has loadplans. Using them
    // is more efficient, and some of them may already be switched to 
    // alternate resources.
    for (; ldplan != opplan->endLoadPlans(); ++ldplan)
    {
      if (ldplan->getQuantity() < 0 || ldplan->getLoad()->getSetup().empty() || !ldplan->getResource()->getSetupMatrix())
        // Not a consuming loadplan or there is no setup on this loadplan
        continue;

      // An operation can load only a single resource with a setup matrix
      if (firstResourceWithSetup)
        firstResourceWithSetup = false;
      else
        throw DataException("Only a single resource with a setup matrix is allowed per operation");

      // Calculate the setup time
      SetupEvent* cursetup = ldplan->getResource()->getSetupAt(setupend, opplan);
      if (prevevent)
        *prevevent = cursetup;
      return SetupInfo(
        ldplan->getResource(),
        ldplan->getResource()->getSetupMatrix()
        ->calculateSetup(cursetup ? cursetup->getSetup() : "", ldplan->getLoad()->getSetup(), ldplan->getResource()),
        ldplan->getLoad()->getSetup()
        );  
    }
  }
  return SetupInfo(nullptr, nullptr, PooledString());
}


void Operation::initOperationPlan (
  OperationPlan* opplan, double q, const Date& s, const Date& e, Demand* l,
  OperationPlan* ow, unsigned long i, bool makeflowsloads, bool roundDown
  ) const
{
  opplan->oper = const_cast<Operation*>(this);
  if (l)
    opplan->setDemand(l);
  opplan->setName(i);

  // Setting the owner first. Note that the order is important here!
  // For alternates & routings the quantity needs to be set through the owner.
  if (ow)
    opplan->setOwner(ow, true);

  // Setting the dates and quantity
  setOperationPlanParameters(opplan, q, s, e, true, true, roundDown);

  // Create the loadplans and flowplans, if allowed
  if (makeflowsloads)
    opplan->createFlowLoads();

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


OperationPlanState OperationFixedTime::setOperationPlanParameters(
  OperationPlan* opplan, double q, Date s, Date e, bool preferEnd, 
  bool execute, bool roundDown
  ) const
{
  // Invalid call to the function
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for fixedtime operationplan");

  // Confirmed operationplans are untouchable
  if (opplan->getConfirmed())
    return OperationPlanState(opplan);

  // Compute the start and end date
  Duration production_duration;
  Duration setup_duration;
  DateRange production_dates;
  DateRange setup_dates;
  Operation::SetupInfo setuptime_required(nullptr, nullptr, PooledString());
  double efficiency = opplan->getEfficiency(s ? s : e);
  bool forward;
  if (e && s)
  {
    if (preferEnd)
      forward = false;
    else
      forward = true;
  }
  else if (s)
    forward = true;
  else
    forward = false;
  Date d = s;

  bool repeat;
  Duration production_wanted_duration = double(duration) / efficiency;
  Duration setup_wanted_duration;
  do
  {
  if (forward)
  {
    // Compute forward from the start date
    setuptime_required = calculateSetup(opplan, d, opplan->getSetupEvent());
    if (get<0>(setuptime_required))
    {
      if (get<1>(setuptime_required))
      {
        // Apply a setup matrix rule
        setup_wanted_duration = double(get<1>(setuptime_required)->getDuration()) / efficiency;
        setup_dates = calculateOperationTime(opplan, d, setup_wanted_duration, true, &setup_duration);
        if (setup_duration != setup_wanted_duration)
          // Damned, not enough time to setup the resource
          production_dates = DateRange(setup_dates.getEnd(), setup_dates.getEnd());
        else
          production_dates = calculateOperationTime(opplan, setup_dates.getEnd(), production_wanted_duration, true, &production_duration);
      }
      else
      {
        // Dummy changeover
        setup_dates = DateRange(d, d);
        production_dates = calculateOperationTime(opplan, d, production_wanted_duration, true, &production_duration);
      }
    }
    else
    {
      // No setup required
      production_dates = calculateOperationTime(opplan, d, production_wanted_duration, true, &production_duration);
      setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
    }    
  }
  else
  {
    // Compute backward from the end date
    production_dates = calculateOperationTime(opplan, e, production_wanted_duration, false, &production_duration);
    if (production_duration != production_wanted_duration)
      // Damned, not enough time for the production
      setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
    else
    {
      setuptime_required = calculateSetup(opplan, production_dates.getStart());      
      if (get<1>(setuptime_required))
      {
        // Apply setup matrix rule
        setup_wanted_duration = double(get<1>(setuptime_required)->getDuration()) / efficiency;
        setup_dates = calculateOperationTime(
          opplan, production_dates.getStart(), setup_wanted_duration, false, &setup_duration
        );
      }
      else
        // Dummy or no setup required
        setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
    }
  }

  if (
    production_duration != production_wanted_duration
    || (get<1>(setuptime_required) && setup_duration != setup_wanted_duration)
    )
  {
    // Not enough time found for the setup and the operation duration
    if (!execute)
      return OperationPlanState(production_dates, setup_dates.getEnd(), 0);
    else
      opplan->setQuantity(0);
  }
  else if (opplan->getProposed())
  {
    // All quantities are valid, as long as they are above the minimum size and
    // below the maximum size
    if (q > 0)
    {
      if (getSizeMinimumCalendar())
      {
        // Minimum size varies over time
        double curmin = getSizeMinimumCalendar()->getValue(production_dates.getEnd());
        if (q < curmin)
          q = roundDown ? 0.0 : curmin;
      }
      if (q < getSizeMinimum())
        // Minimum size is constant over time
        q = roundDown ? 0.0 : getSizeMinimum();
    }
    if (q > getSizeMaximum())
      q = getSizeMaximum();
    if (fabs(q - opplan->getQuantity()) > ROUNDING_ERROR)
      q = opplan->setQuantity(q, roundDown, false, execute, production_dates.getEnd());
  }

  if (!execute)
  {
    // Simulation only
    if (get<1>(setuptime_required))
    {
      SetupEvent tmp(
        get<0>(setuptime_required)->getLoadPlans(),
        setup_dates.getEnd(),
        get<2>(setuptime_required),
        get<1>(setuptime_required)
        );
      return OperationPlanState(setup_dates.getStart(), production_dates.getEnd(), q, &tmp);
    }
    else
      return OperationPlanState(production_dates, q);
  }

  // Update the operationplan
  if (get<0>(setuptime_required))
    opplan->setSetupEvent(
      get<0>(setuptime_required),
      setup_dates.getEnd(),
      get<2>(setuptime_required),
      get<1>(setuptime_required)
      );
  else
    opplan->clearSetupEvent();
  opplan->setStartAndEnd(production_dates.getStart(), production_dates.getEnd());

  if (forward && preferEnd && opplan->getStart() < s && s != Date::infiniteFuture &&  d != Date::infiniteFuture)
  {
    d += Duration(3600L);
    repeat = true;  
  }
  else if (!forward && !preferEnd && opplan->getStart() > s && s != Date::infinitePast && d != Date::infinitePast)
  {
    d -= Duration(3600L);
    repeat = true;
  }
  else
    repeat = false;
  }
  while (repeat);
  return OperationPlanState(opplan);
}


bool OperationFixedTime::extraInstantiate(OperationPlan* o, bool createsubopplans, bool use_start)
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
  if (!o->getRawIdentifier() && o->getProposed())
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
        && y->getDemand() == o->getDemand() && y->getProposed() && y->getRawIdentifier()
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
          || fp1->getFlow()->getQuantityFixed()
          || fp2->getFlow()->getQuantityFixed())
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
        && x->getDemand() == o->getDemand() && x->getProposed() && x->getRawIdentifier()
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
OperationTimePer::setOperationPlanParameters(
  OperationPlan* opplan, double q, Date s, Date e, 
  bool preferEnd, bool execute, bool roundDown
) const
{
  // Invalid call to the function.
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for timeper operationplan");

  // Confirmed operationplans are untouchable
  if (opplan->getConfirmed())
    return OperationPlanState(opplan);

  if (opplan->getProposed())
  {
    // Proposed operationplans need to respect minimum and maximum size
    if (q > 0)
    {
      if (getSizeMinimumCalendar())
      {
        // Respect time varying minimum.
        // This configuration is not really supported: when the size changes
        // a different minimum size could be effective. The planning results
        // in a constrained plan can be not optimal or incorrect.
        Duration tmp1;
        DateRange tmp2 = calculateOperationTime(opplan, s, e, &tmp1);
        double curmin = getSizeMinimumCalendar()->getValue(tmp2.getEnd());
        if (q < curmin)
          q = roundDown ? 0.0 : curmin;
      }
      if (q < getSizeMinimum())
        // Respect constant minimum value
        q = roundDown ? 0.0 : getSizeMinimum();
    }
    if (q > getSizeMaximum())
      q = getSizeMaximum();
  }

  // The logic depends on which dates are being passed along
  Duration production_duration;
  Duration production_wanted_duration;
  Duration setup_duration;
  Duration setup_wanted_duration;
  DateRange production_dates;
  DateRange setup_dates;
  Operation::SetupInfo setuptime_required;
  double efficiency = opplan->getEfficiency(s ? s : e);
  if (s && e)
  {
    // Case 1: Both the start and end date are specified: Compute the quantity.
    // Calculate the available time between those dates
    setuptime_required = calculateSetup(opplan, s);
    if (get<1>(setuptime_required))
    {
      setup_wanted_duration = double(get<1>(setuptime_required)->getDuration()) / efficiency;
      setup_dates = calculateOperationTime(opplan, s, setup_wanted_duration, true, &setup_duration);
      if (setup_dates.getEnd() > e || setup_duration != setup_wanted_duration)
      {
        // Damned, not enough time to setup the resource
        if (!execute)
          return OperationPlanState(setup_dates, 0.0);
        opplan->setQuantity(0, true, false, execute);
        opplan->clearSetupEvent();
        opplan->setStartAndEnd(setup_dates.getStart(), setup_dates.getEnd());
        return OperationPlanState(opplan);
      }
      else
        // Calculate duration available for actual production
        production_dates = calculateOperationTime(opplan, setup_dates.getEnd(), e, &production_duration);
    }
    else
    {
      // Dummy or no setup required
      production_dates = calculateOperationTime(opplan, s, e, &production_duration);
      setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
    }

    if (production_duration < Duration(double(duration) / efficiency))
    {
      // Start and end aren't far enough from each other to fit the constant
      // part of the operation duration and/or the setup time.
      // This is infeasible.
      if (!execute)
        return OperationPlanState(production_dates, 0.0);
      opplan->setQuantity(0, true, false, execute);
      opplan->clearSetupEvent();
      opplan->setStartAndEnd(production_dates.getStart(), production_dates.getEnd());
      return OperationPlanState(opplan);
    }
    else
    {
      // Calculate the quantity, respecting minimum, maximum and multiple size.
      if (duration_per)
      {
        if (q * duration_per / efficiency < (double(production_duration) - double(duration) / efficiency) + 0.5)
          // Provided quantity is acceptable.
          // Note that we allow a margin of 0.5 second to accept.
          q = opplan->setQuantity(q, roundDown, false, execute);
        else
          // Calculate the maximum operationplan that will fit in the window
          q = opplan->setQuantity(
            (double(production_duration) - double(duration) / efficiency) / duration_per * efficiency,
            roundDown, false, execute
            );
      }
      else
        // No duration_per field given, so any quantity will go
        q = opplan->setQuantity(q, roundDown, false, execute);

      // Updates the dates
      production_wanted_duration = (double(duration) + duration_per * q) / efficiency;
      if (preferEnd)
        production_dates = calculateOperationTime(opplan, e, production_wanted_duration, false, &production_duration);
      else
        production_dates = calculateOperationTime(opplan, setup_dates.getEnd(), production_wanted_duration, true, &production_duration);
      if (production_dates.getStart() != setup_dates.getEnd())
      {
        // TODO It is even possible that the setup time is now different...
        if (setup_duration)
          setup_dates = calculateOperationTime(opplan, production_dates.getStart(), setup_duration, false);
        else
          setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
      }
      if (!execute)
      {
        if (get<0>(setuptime_required))
        {
          SetupEvent tmp(
            get<0>(setuptime_required)->getLoadPlans(),
            setup_dates.getEnd(),
            get<2>(setuptime_required),
            get<1>(setuptime_required)
          );
          return OperationPlanState(setup_dates.getStart(), production_dates.getEnd(), q, &tmp);
        }
        else
          return OperationPlanState(production_dates, q);
      }
      if (get<0>(setuptime_required))
        opplan->setSetupEvent(
          get<0>(setuptime_required),
          setup_dates.getEnd(),
          get<2>(setuptime_required),
          get<1>(setuptime_required)
          );
      else
        opplan->clearSetupEvent();
      opplan->setStartAndEnd(setup_dates.getStart(), production_dates.getEnd());
    }
  }
  else if (e || !s)
  {
    // Case 2: Only an end date is specified. Respect the quantity and
    // compute the start date
    // Case 4: No date was given at all. Respect the quantity and the
    // existing end date of the operationplan.
    q = opplan->setQuantity(q, roundDown, false, execute);
    // Round and size the quantity
    production_wanted_duration = (double(duration) + duration_per * q) / efficiency;
    production_dates = calculateOperationTime(opplan, e, production_wanted_duration, false, &production_duration);
    if (production_duration == production_wanted_duration)
    {
      // Size is as desired
      setuptime_required = calculateSetup(opplan, production_dates.getStart());
      if (get<1>(setuptime_required))
      {
        setup_wanted_duration = double(get<1>(setuptime_required)->getDuration()) / efficiency;
        setup_dates = calculateOperationTime(opplan, production_dates.getStart(), setup_wanted_duration, false, &setup_duration);
        if (setup_duration != setup_wanted_duration)
        {
          // No time to do the setup
          if (!execute)
            return OperationPlanState(production_dates, 0.0);
          opplan->setQuantity(0, true, false);
          opplan->clearSetupEvent();
          opplan->setStartAndEnd(e, e);
        }
      }
      else
        // Dummy or no setup involved
        setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
      if (!execute)
      {
        if (get<0>(setuptime_required))
        {
          SetupEvent tmp(
            get<0>(setuptime_required)->getLoadPlans(),
            setup_dates.getEnd(),
            get<2>(setuptime_required),
            get<1>(setuptime_required)
          );
          return OperationPlanState(setup_dates.getStart(), production_dates.getEnd(), q, &tmp);
        }
        else
          return OperationPlanState(production_dates, q);
      }
      if (get<0>(setuptime_required))
        opplan->setSetupEvent(
          get<0>(setuptime_required),
          setup_dates.getEnd(),
          get<2>(setuptime_required),
          get<1>(setuptime_required)
          );
      else
        opplan->clearSetupEvent();
      opplan->setStartAndEnd(setup_dates.getStart(), production_dates.getEnd());
    }
    else if (production_duration < Duration(double(duration) / efficiency))
    {
      // Not feasible
      if (!execute)
        return OperationPlanState(production_dates, 0);
      opplan->setQuantity(0, true, false);
      opplan->clearSetupEvent();
      opplan->setStartAndEnd(e, e);
    }
    else
    {
      // Resize the quantity to be feasible

      // Compute the required setup time
      setuptime_required = calculateSetup(opplan, production_dates.getStart());
      if (get<1>(setuptime_required))
      {
        setup_wanted_duration = double(get<1>(setuptime_required)->getDuration()) / efficiency;
        setup_dates = calculateOperationTime(
          opplan, production_dates.getStart(), setup_wanted_duration, false, &setup_duration
          );
        if (setup_duration != setup_wanted_duration)
        {
          // No time to do the setup
          if (!execute)
            return OperationPlanState(production_dates, 0.0);
          opplan->setQuantity(0, true, false);
          opplan->clearSetupEvent();
          opplan->setStartAndEnd(e, e);
        }
      }
      else
      {
        // Dummy or no setup involved
        setup_duration = Duration(0L);
        setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
      }

      double max_q = duration_per ?
          static_cast<double>(production_duration - setup_duration - duration) / duration_per :
          q;
      q = opplan->setQuantity(q < max_q ? q : max_q, true, false, execute);
      production_wanted_duration = (double(duration) + duration_per * q) / efficiency;
      production_dates = calculateOperationTime(opplan, e, production_wanted_duration, false, &production_duration);
      if (production_dates.getStart() != setup_dates.getEnd())
      {
        // TODO It is even possible that the setup time is now different...
        if (setup_duration)
          setup_dates = calculateOperationTime(opplan, production_dates.getStart(), setup_duration, false);
        else
          setup_dates = DateRange(production_dates.getStart(), production_dates.getStart());
      }
      if (!execute)
      {
        if (get<0>(setuptime_required))
        {
          SetupEvent tmp(
            get<0>(setuptime_required)->getLoadPlans(),
            setup_dates.getEnd(),
            get<2>(setuptime_required),
            get<1>(setuptime_required)
          );
          return OperationPlanState(setup_dates.getStart(), production_dates.getEnd(), q, &tmp);
        }
        else
          return OperationPlanState(production_dates, q);
      }
      if (get<0>(setuptime_required))
        opplan->setSetupEvent(
          get<0>(setuptime_required),
          setup_dates.getEnd(),
          get<2>(setuptime_required),
          get<1>(setuptime_required)
          );
      else
        opplan->clearSetupEvent();
      opplan->setStartAndEnd(setup_dates.getStart(), production_dates.getEnd());
    }
  }
  else
  {
    Date d = s;

    // Case 3: Only a start date is specified. Respect the quantity and
    // compute the end date
    q = opplan->setQuantity(q, roundDown, false, execute);
    // Round and size the quantity
    production_wanted_duration = (double(duration) + duration_per * q) / efficiency;

    bool repeat;
    do
    {
    // Compute the setup time
    setuptime_required = calculateSetup(opplan, d, nullptr);
    if (get<0>(setuptime_required) && get<1>(setuptime_required))
    {
      setup_wanted_duration = double(get<1>(setuptime_required)->getDuration()) / efficiency;
      setup_dates = calculateOperationTime(opplan, d, setup_wanted_duration, true, &setup_duration);
      if (setup_duration != setup_wanted_duration)
      {
        // No time to do the setup
        if (!execute)
          return OperationPlanState(setup_dates, 0);
        opplan->setQuantity(0, true, false);
        opplan->clearSetupEvent();
        opplan->setStartAndEnd(setup_dates.getStart(), setup_dates.getEnd());
        return OperationPlanState(opplan);
      }
    }
    else
      // No setup involved
      setup_dates = DateRange(d, d);

    Duration actual;
    production_dates = calculateOperationTime(
      opplan, setup_dates.getEnd(), production_wanted_duration, true, &production_duration
      );
    if (production_duration == production_wanted_duration)
    {
      // Size is as desired
      if (!execute)
      {
        if (get<0>(setuptime_required))
        {
          SetupEvent tmp(
            get<0>(setuptime_required)->getLoadPlans(),
            setup_dates.getEnd(),
            get<2>(setuptime_required),
            get<1>(setuptime_required)
          );
          return OperationPlanState(setup_dates.getStart(), production_dates.getEnd(), q, &tmp);
        }
        else
          return OperationPlanState(production_dates, q);
      }
      if (get<0>(setuptime_required))
        opplan->setSetupEvent(
          get<0>(setuptime_required),
          setup_dates.getEnd(),
          get<2>(setuptime_required),
          get<1>(setuptime_required)
        );
      else
        opplan->clearSetupEvent();
      opplan->setStartAndEnd(setup_dates.getStart(), production_dates.getEnd());
    }
    else if (production_duration < Duration(double(duration) / efficiency))
    {
      // Not feasible
      if (!execute)
        return OperationPlanState(production_dates, 0.0);
      opplan->setQuantity(0, true, false);
      opplan->clearSetupEvent();
      opplan->setStartAndEnd(d, d);
    }
    else
    {
      // Resize the quantity to be feasible
      double max_q = duration_per ?
          static_cast<double>(production_duration - duration) / duration_per :
          q;
      q = opplan->setQuantity(q < max_q ? q : max_q, roundDown, false, execute);
      production_wanted_duration = (double(duration) + duration_per * q) / efficiency;
      production_dates = calculateOperationTime(
        opplan, setup_dates.getEnd(), production_wanted_duration, true, &production_duration
        );
      if (!execute)
      {
        if (get<0>(setuptime_required))
        {
          SetupEvent tmp(
            get<0>(setuptime_required)->getLoadPlans(),
            setup_dates.getEnd(),
            get<2>(setuptime_required),
            get<1>(setuptime_required)
          );
          return OperationPlanState(setup_dates.getStart(), production_dates.getEnd(), q, &tmp);
        }
        else
          return OperationPlanState(production_dates, q);
      }
      if (get<0>(setuptime_required))
        opplan->setSetupEvent(
          get<0>(setuptime_required),
          setup_dates.getEnd(),
          get<2>(setuptime_required),
          get<1>(setuptime_required)
          );
      else
        opplan->clearSetupEvent();
      opplan->setStartAndEnd(production_dates.getStart(), production_dates.getEnd());
    }
    if (preferEnd && opplan->getStart() < s && s != Date::infiniteFuture && d != Date::infiniteFuture)
    {
      d += Duration(3600L);
      repeat = true;
    }
    else if (!preferEnd && opplan->getStart() > s && s != Date::infinitePast && d != Date::infinitePast)
    {
      d -= Duration(3600L);
      repeat = true;
    }
    else
      repeat = false;
    }
    while (repeat);
  }
  return OperationPlanState(opplan);
}


OperationPlanState OperationRouting::setOperationPlanParameters(
  OperationPlan* opplan, double q, Date s, Date e, 
  bool preferEnd, bool execute, bool roundDown
) const
{
  // Invalid call to the function
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for routing operationplan");

  // Confirmed operationplans are untouchable
  if (opplan->getConfirmed())
    return OperationPlanState(opplan);

  if (!opplan->lastsubopplan) // @todo replace with proper iterator
  {
    // No step operationplans to work with. Just apply the requested quantity
    // and dates.
    q = opplan->setQuantity(q, roundDown, false, execute);
    if (!s && e)
      s = e;
    if (s && !e)
      e = s;
    if (!execute)
      return OperationPlanState(s, e, q);
    opplan->clearSetupEvent();
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
      x = i->getOperation()->setOperationPlanParameters(
        i, q, Date::infinitePast, e, preferEnd, execute, roundDown
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
      x = i->getOperation()->setOperationPlanParameters(
        i, q, s, Date::infinitePast, preferEnd, execute, roundDown
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


bool OperationRouting::extraInstantiate(OperationPlan* o, bool createsubopplans, bool use_start)
{
  // Create step suboperationplans if they don't exist yet.
  if (createsubopplans && !o->lastsubopplan)
  {
    Date d = o->getEnd();
    OperationPlan *p = nullptr;
    if (!use_start)
    {
      // Using the end date
      for (auto e = getSubOperations().rbegin(); e != getSubOperations().rend(); ++e)
      {
        if (p)
          d -= (*e)->getOperation()->getPostTime();
        p = (*e)->getOperation()->createOperationPlan(
          o->getQuantity(), Date::infinitePast, d, nullptr, o, 0, true
          );
        d = p->getStart();
      }
    }
    else
    {
      // Using the start date when there is no end date
      d = o->getStart();
      // Using the current date when both the start and end date are missing
      if (!d)
        d = Plan::instance().getCurrent();
      for (auto e = getSubOperations().begin(); e != getSubOperations().end(); ++e)
      {
        p = (*e)->getOperation()->createOperationPlan(
          o->getQuantity(), d, Date::infinitePast, nullptr, nullptr, 0, true
          );
        d = p->getEnd() + (*e)->getOperation()->getPostTime();
        p->setOwner(o); // Required to get the correct ordering of the steps
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
OperationAlternate::setOperationPlanParameters(
  OperationPlan* opplan, double q, Date s, Date e, 
  bool preferEnd, bool execute, bool roundDown
) const
{
  // Invalid calls to this function
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for alternate operationplan");

  // Confirmed operationplans are untouchable
  if (opplan->getConfirmed())
    return OperationPlanState(opplan);

  OperationPlan *x = opplan->lastsubopplan;
  if (!x)
  {
    // Blindly accept the parameters if there is no suboperationplan
    if (execute)
    {
      opplan->setQuantity(q, roundDown, false);
      opplan->clearSetupEvent();
      opplan->setStartAndEnd(s, e);
      return OperationPlanState(opplan);
    }
    else
      return OperationPlanState(
        s, e, opplan->setQuantity(q, roundDown, false, false)
        );
  }
  else
    // Pass the call to the sub-operation
    return x->getOperation()->setOperationPlanParameters(
      x, q, s, e, preferEnd, execute, roundDown
      );
}


bool OperationAlternate::extraInstantiate(OperationPlan* o, bool createsubopplans, bool use_start)
{
  // Create a suboperationplan if one doesn't exist yet.
  // We use the first effective alternate by default.
  if (createsubopplans && !o->lastsubopplan)
  {
    // Find the right operation
    Operationlist::const_iterator altIter = getSubOperations().begin();
    for (; altIter != getSubOperations().end(); )
    {
      // Filter out alternates that are not suitable
      if ((*altIter)->getPriority() != 0 && (*altIter)->getEffective().within(o->getEnd()))
        break;
    }
    if (altIter != getSubOperations().end())
      // Create an operationplan instance
      (*altIter)->getOperation()->createOperationPlan(
        o->getQuantity(), o->getStart(),
        o->getEnd(), nullptr, o, 0, true);
  }
  return true;
}


OperationPlanState
OperationSplit::setOperationPlanParameters(
  OperationPlan* opplan, double q, Date s, Date e,
  bool preferEnd, bool execute, bool roundDown
) const
{
  // Invalid calls to this function
  if (!opplan || q<0)
    throw LogicException("Incorrect parameters for split operationplan");

  // Confirmed operationplans are untouchable
  if (opplan->getConfirmed())
    return OperationPlanState(opplan);

  // Blindly accept the parameters: only sizing constraints from the child
  // operations are respected.
  if (execute)
  {
    opplan->setQuantity(q, roundDown, false);
    opplan->clearSetupEvent();
    opplan->setStartAndEnd(s, e);
    return OperationPlanState(opplan);
  }
  else
    return OperationPlanState(s, e, q);
}


bool OperationSplit::extraInstantiate(OperationPlan* o, bool createsubopplans, bool use_start)
{
  if (!createsubopplans || o->lastsubopplan)
    // Suboperationplans already exist. Nothing to do here.
    return true;

  // Compute the sum of all effective percentages.
  int sum_percent = 0;
  Date enddate = o->getEnd();
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
      o->getStart(), enddate, nullptr, o, 0, true
      );
  }
  return true;
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
  else
  {
    // New head
    child->nextsubopplan = parent->firstsubopplan;
    parent->firstsubopplan->prevsubopplan = child;
    parent->firstsubopplan = child;
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
  else
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
  if (child->owner == parent)
    return;

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
    else
    {
      // New head
      child->nextsubopplan = parent->firstsubopplan;
      parent->firstsubopplan->prevsubopplan = child;
      parent->firstsubopplan = child;
    }
  }
  else
  {
    // Method 2: full validation
    // We verify that the new operationplan is a valid step in the routing.
    // The child element is inserted at the right place in the list.
    // Search if an existing operationplan matches
    bool ok = false;
    OperationPlan* subopplan = parent->firstsubopplan;
    for (; subopplan; subopplan = subopplan->nextsubopplan)
      if (subopplan->getOperation() == child->getOperation())
      {
        ok = true;
        break;
      }

    // If not existing yet, find the correct position in the list
    if (!subopplan)
    {
      subopplan = parent->firstsubopplan;
      for (auto rtgstep = steps.begin(); rtgstep != steps.end(); ++rtgstep)
      {
        if (subopplan && (*rtgstep)->getOperation() == subopplan->getOperation())
          subopplan = subopplan->nextsubopplan;
        if ((*rtgstep)->getOperation() == child->getOperation())
        {
          ok = true;
          break;
        }
      }
    }

    // Stop if this is not a valid step
    if (!ok)
      throw DataException("Invalid routing suboperationplan");

    // Remove existing suboperationplan
    if (subopplan && subopplan->getOperation() == child->getOperation())
    {      
      parent->eraseSubOperationPlan(subopplan);
      OperationPlan* tmp = subopplan->nextsubopplan;
      delete subopplan;
      subopplan = tmp;
    }

    // Insert the new suboperationplan.
    // The variable subopplan points to the suboperationplan before which we 
    // need to insert the new suboperationplan.
    if (subopplan)
    {
      // Append in middle of suboperationplan list
      child->nextsubopplan = subopplan;
      child->prevsubopplan = subopplan->prevsubopplan;
      if (subopplan->prevsubopplan)
        subopplan->prevsubopplan->nextsubopplan = child;
      else
        parent->firstsubopplan = child;
      subopplan->prevsubopplan = child;
      // Propagate backward to assure the timing of the preceding routing steps
      for (auto prevstep = child; prevstep; prevstep = prevstep->prevsubopplan)
      {
        if (prevstep->getConfirmed())
          continue;
        else if (prevstep->prevsubopplan && prevstep->prevsubopplan->getEnd() > prevstep->getStart())
          prevstep->prevsubopplan->setEnd(prevstep->getStart());
      }
      // Propagate forward to assure the timing of the preceding routing steps
      for (auto followingsteps = child; followingsteps; followingsteps = followingsteps->nextsubopplan)
      {
        if (followingsteps->getConfirmed())
          continue;
        else if (followingsteps->prevsubopplan && followingsteps->prevsubopplan->getEnd() > followingsteps->getStart())
          followingsteps->setStart(followingsteps->prevsubopplan->getEnd());
      }
    }
    else if (parent->lastsubopplan)
    {
      // Append at end of suboperationplan list
      child->prevsubopplan = parent->lastsubopplan;
      parent->lastsubopplan->nextsubopplan = child;
      parent->lastsubopplan = child;
      // Propagate backward to assure the timing of the preceding routing steps
      for (auto prevstep = child; prevstep; prevstep = prevstep->prevsubopplan)
      {
        if (prevstep->getConfirmed())
          continue;
        else if (prevstep->prevsubopplan && prevstep->prevsubopplan->getEnd() > prevstep->getStart())
          prevstep->prevsubopplan->setEnd(prevstep->getStart());
      }
      // Propagate forward to assure the timing of the subsequent routing steps
      if (child->prevsubopplan && child->prevsubopplan->getEnd() > child->getStart() && !child->getConfirmed())
        child->setStart(child->prevsubopplan->getEnd());
    }
    else
    {
      // First suboperationplan
      parent->lastsubopplan = child;
      parent->firstsubopplan = child;
    }
  }

  // Update the owner
  if (child->owner)
    child->owner->eraseSubOperationPlan(child);
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

  // Confirmed and approved operationplans don't respect sizing constraints
  if (!oplan->getProposed())
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
  else if (fabs(f - oplan->quantity) < ROUNDING_ERROR)
  {
    // No real change
    if (!execute)
      return oplan->quantity;
  }
  else
  {
    // All others respect constraints
    bool applied_minimum = false;
    double curmin = 0.0;
    if (getSizeMinimumCalendar())
      // Minimum varies over time
      curmin = getSizeMinimumCalendar()->getValue(end ? end : oplan->getEnd());
    if (curmin < getSizeMinimum())
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
      applied_minimum = true;
    }
    if (f != 0.0 && f >= getSizeMaximum())
    {
      if (applied_minimum && f > getSizeMaximum() + ROUNDING_ERROR)
        throw DataException("Invalid sizing parameters for operation " + getName());
      // If min and max are conflicting, we respect the maximum
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
      if (!i->getConfirmed())
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
    if (!i->getProposed())
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
  if (i == item)
    return;

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



Duration OperationAlternate::getDecoupledLeadTime(double qty) const
{
  Duration leadtime;

  // Find the preferred alternate
  int curPrio = INT_MAX;
  Operation* suboper = nullptr;
  for (Operation::Operationlist::const_iterator
    sub = getSubOperations().begin();
    sub != getSubOperations().end();
    ++sub)
  {
    if (
      (*sub)->getPriority() < curPrio
      && (*sub)->getEffective().within(Plan::instance().getCurrent())
      )
    {
      suboper = (*sub)->getOperation();
      curPrio = (*sub)->getPriority();
    }
  }
  
  // Handle the case where no sub-operation is effective at all
  if (!suboper)
    return Duration(999L * 86400L);

  // Respect the size constraint of the child operation
  double qty2 = qty;
  if (qty2 < suboper->getSizeMinimum())
    qty2 = suboper->getSizeMinimum();
  if (suboper->getSizeMinimumCalendar())
  {
    double curmin = suboper->getSizeMinimumCalendar()->getValue(Plan::instance().getCurrent());
    if (qty2 < curmin)
      qty2 = curmin;
  }

  // Find the longest supply path for all flows on the top operation
  for (auto fl = getFlows().begin(); fl != getFlows().end(); ++fl)
  {
    if (fl->getQuantity() >= 0)
      continue;
    Duration tmp = fl->getBuffer()->getDecoupledLeadTime(qty2, false);
    if (tmp > leadtime)
      leadtime = tmp;
  }

  // Also loop over the flows of the suboperation
  for (auto fl = suboper->getFlows().begin(); fl != suboper->getFlows().end(); ++fl)
  {
    if (fl->getQuantity() >= 0)
      continue;
    Duration tmp = fl->getBuffer()->getDecoupledLeadTime(qty2, false);
    if (tmp > leadtime)
      leadtime = tmp;
  }

  // Add the operation's own duration
  if (
    suboper->getType() == *OperationFixedTime::metadata
    || suboper->getType() == *OperationItemDistribution::metadata
    || suboper->getType() == *OperationItemSupplier::metadata
    )
  {
    // Fixed duration operation types
    OperationFixedTime* op = static_cast<OperationFixedTime*>(suboper);
    leadtime += op->getDuration();
  }
  else if (suboper->getType() == *OperationTimePer::metadata)
  {
    // Variable duration operation types
    OperationTimePer* op = static_cast<OperationTimePer*>(suboper);
    leadtime += op->getDuration() + static_cast<long>(op->getDurationPer() * qty2);
  }
  else
    logger << "Warning: suboperation of unsupported type for an alternate operation" << endl;
  return leadtime;
}


Duration OperationSplit::getDecoupledLeadTime(double qty) const
{
  Duration totalmax;
  for (Operation::Operationlist::const_iterator
    sub = getSubOperations().begin();
    sub != getSubOperations().end();
    ++sub)
  {
    if (!(*sub)->getEffective().within(Plan::instance().getCurrent()))
      // This suboperation is not effective
      continue;

    // Respect the size constraint of the child operation
    Operation* suboper = (*sub)->getOperation();
    Duration maxSub;
    double qty2 = qty;
    if (qty2 < suboper->getSizeMinimum())
      qty2 = suboper->getSizeMinimum();
    if (suboper->getSizeMinimumCalendar())
    {
      double curmin = suboper->getSizeMinimumCalendar()->getValue(Plan::instance().getCurrent());
      if (qty2 < curmin)
        qty2 = curmin;
    }

    // Find the longest supply path for all flows on the top operation
    for (auto fl = getFlows().begin(); fl != getFlows().end(); ++fl)
    {
      if (fl->getQuantity() >= 0)
        continue;
      Duration tmp = fl->getBuffer()->getDecoupledLeadTime(qty2, false);
      if (tmp > maxSub)
        maxSub = tmp;
    }

    // Also loop over the flows of the suboperation
    for (auto fl = suboper->getFlows().begin(); fl != suboper->getFlows().end(); ++fl)
    {
      if (fl->getQuantity() >= 0)
        continue;
      Duration tmp = fl->getBuffer()->getDecoupledLeadTime(qty2, false);
      if (tmp > maxSub)
        maxSub = tmp;
    }

    // Add the operation's own duration
    if (
      suboper->getType() == *OperationFixedTime::metadata
      || suboper->getType() == *OperationItemDistribution::metadata
      || suboper->getType() == *OperationItemSupplier::metadata
      )
    {
      // Fixed duration operation types
      OperationFixedTime* op = static_cast<OperationFixedTime*>(suboper);
      maxSub += op->getDuration();
    }
    else if (suboper->getType() == *OperationTimePer::metadata)
    {
      // Variable duration operation types
      OperationTimePer* op = static_cast<OperationTimePer*>(suboper);
      maxSub += op->getDuration() + static_cast<long>(op->getDurationPer() * qty2);
    }
    else
      logger << "Warning: suboperation of unsupported type for a split operation" << endl;

    // Keep track of the longest of all suboperations
    if (maxSub > totalmax)
      totalmax = maxSub;
  }
  return totalmax;
}


Duration OperationRouting::getDecoupledLeadTime(double qty) const
{
  // Validate the quantity
  if (qty < getSizeMinimum())
    qty = getSizeMinimum();
  if (getSizeMinimumCalendar())
  {
    double curmin = getSizeMinimumCalendar()->getValue(Plan::instance().getCurrent());
    if (qty < curmin)
      qty = curmin;
  }
  // The lead time of a routing step is the sum of:
  //  - Duration of any subsequent routing steps
  //  - Its own duration
  //  - Longest lead time of all its flows
  //
  // The lead time of the longest step is taken as the lead time of the
  // total routing.
  Duration nextStepsDuration;
  Duration totalmax;
  for (Operation::Operationlist::const_reverse_iterator
    sub = getSubOperations().rbegin();
    sub != getSubOperations().rend();
    ++sub)
  {
    Duration maxSub;
    Operation* suboper = (*sub)->getOperation();

    // Find the longest supply path for all flows
    for (auto fl = suboper->getFlows().begin(); fl != suboper->getFlows().end(); ++fl)
    {
      if (fl->getQuantity() >= 0)
        continue;
      Duration tmp = fl->getBuffer()->getDecoupledLeadTime(qty, false);
      if (tmp > maxSub)
        maxSub = tmp;
    }

    // Add the operation's own duration to the duration of all
    // routing steps
    if (
      suboper->getType() == *OperationFixedTime::metadata
      || suboper->getType() == *OperationItemDistribution::metadata
      || suboper->getType() == *OperationItemSupplier::metadata
      )
    {
      // Fixed duration operation types
      OperationFixedTime* op = static_cast<OperationFixedTime*>(suboper);
      nextStepsDuration += op->getDuration();
    }
    else if (suboper->getType() == *OperationTimePer::metadata)
    {
      // Variable duration operation types
      OperationTimePer* op = static_cast<OperationTimePer*>(suboper);
      nextStepsDuration += op->getDuration() + static_cast<long>(op->getDurationPer() * qty);
    }
    else
      logger << "Warning: suboperation of unsupported type for a routing operation" << endl;

    // Take the longest of all routing steps
    if (maxSub + nextStepsDuration > totalmax)
      totalmax = maxSub + nextStepsDuration;
  }
  return totalmax;
}


Duration OperationFixedTime::getDecoupledLeadTime(double qty) const
{
  Duration leadtime;

  // Validate the quantity
  if (qty < getSizeMinimum())
    qty = getSizeMinimum();
  if (getSizeMinimumCalendar())
  {
    double curmin = getSizeMinimumCalendar()->getValue(Plan::instance().getCurrent());
    if (qty < curmin)
      qty = curmin;
  }

  // Find the longest supply path for all flows
  for (auto fl = getFlows().begin(); fl != getFlows().end(); ++fl)
  {
    if (fl->getQuantity() >= 0)
      continue;
    Duration tmp = fl->getBuffer()->getDecoupledLeadTime(qty, false);
    if (tmp > leadtime)
      leadtime = tmp;
  }

  // Add the operation's own duration
  leadtime += getDuration();

  return leadtime;
}


Duration OperationTimePer::getDecoupledLeadTime(double qty) const
{
  Duration leadtime;

  // Validate the quantity
  if (qty < getSizeMinimum())
    qty = getSizeMinimum();
  if (getSizeMinimumCalendar())
  {
    double curmin = getSizeMinimumCalendar()->getValue(Plan::instance().getCurrent());
    if (qty < curmin)
      qty = curmin;
  }

  // Find the longest supply path for all flows
  for (auto fl = getFlows().begin(); fl != getFlows().end(); ++fl)
  {
    if (fl->getQuantity() >= 0)
      continue;
    Duration tmp = fl->getBuffer()->getDecoupledLeadTime(qty, false);
    if (tmp > leadtime)
      leadtime = tmp;
  }

  // Add the operation's own duration
  leadtime += getDuration() + static_cast<long>(qty * getDurationPer());

  return leadtime;
}


PyObject* Operation::getDecoupledLeadTimePython(PyObject *self, PyObject *args)
{
  // Pick up the quantity argument
  double qty = 1.0;
  int ok = PyArg_ParseTuple(args, "|d:decoupledLeadTime", &qty);
  if (!ok) return nullptr;

  try
  {
    Duration lt = static_cast<Operation*>(self)->getDecoupledLeadTime(qty);
    return PythonData(lt);
  }
  catch (...)
  {
    PythonType::evalException();
    return nullptr;
  }
}


Operation* Operation::findFromName(string nm)
{
  Operation* oper = Operation::find(nm);
  if (oper)
    // The operation already exists
    return oper;
  else if (nm.substr(0, 5) == "Ship ")
  {
    size_t pos1 = nm.rfind(" from ");
    size_t pos2 = nm.rfind(" to ");
    if (pos1 != string::npos && pos2 != string::npos)
    {
      // Build a transfer operation: "Ship ITEM from LOCATION to LOCATION"
      string item_name = nm.substr(5, pos1 - 5);
      string orig_name = nm.substr(pos1 + 6, pos2 - pos1 - 6);
      string dest_name = nm.substr(pos2 + 4, string::npos);
      Item* item = Item::find(item_name);
      Location* origin = Location::find(orig_name);
      Location* destination = Location::find(dest_name);
      if (item && origin && destination)
      {
        // Find itemdistribution
        const ItemDistribution* item_dist = nullptr;
        for (auto dist = item->getDistributions().begin(); dist != item->getDistributions().end(); ++dist)
        {
          if (origin == dist->getOrigin() && (
            !dist->getDestination() || destination == dist->getDestination()
            ))
          {
            item_dist = &*dist;
            break;
          }
        }
        if (!item_dist)
          // Create the operation
          return new OperationItemDistribution(
            const_cast<ItemDistribution*>(item_dist),
            Buffer::findOrCreate(item, origin),
            Buffer::findOrCreate(item, destination)
            );
      }
    }
    else
    {
      // Build a delivery operation: "Ship ITEM @ LOC" 
      string buf_name = nm.substr(5, string::npos);
      Buffer *buf = Buffer::findFromName(buf_name);
      if (buf)
      {
        // Create the operation
        oper = new OperationDelivery();
        oper->setName(nm);
        static_cast<OperationDelivery*>(oper)->setBuffer(buf);
        return oper;
      }
    }
  }
  else if (nm.substr(0, 9) == "Purchase ")
  {
    // Build a purchasing operation: "Purchase ITEM @ LOCATION from SUPPLIER"
    size_t pos = nm.rfind(" from ");
    if (pos != string::npos)
    {
      string buf_name = nm.substr(9, pos - 9);
      string supplier_name = nm.substr(pos + 6, string::npos);
      Buffer* buf = Buffer::findFromName(buf_name);
      Supplier* sup = Supplier::find(supplier_name);
      if (buf && sup && buf->getItem() && buf->getLocation())
      {
        // Find itemsupplier
        ItemSupplier* item_sup = nullptr;
        for (Item* it = buf->getItem(); it && !item_sup; it = it->getOwner())
        {
          Item::supplierlist::const_iterator supitem_iter = it->getSupplierIterator();
          while (ItemSupplier *i = supitem_iter.next())
          {
            if (!i->getLocation() || buf->getLocation() == i->getLocation())
              item_sup = i;
          }
        }
        if (item_sup)
          // Create the operation
          return new OperationItemSupplier(item_sup, buf);
      }
    }
  }
  return nullptr;
}

} // end namespace
