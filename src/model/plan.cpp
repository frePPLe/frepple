/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/plan.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : johan_de_taeye@yahoo.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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


#include "frepple/model.h"

namespace frepple
{


Plan* Plan::thePlan;


Plan::~Plan()
{
  // Closing the logfile
  Plan::setLogFile("");

	// Clear the pointer to this singleton object
	thePlan = NULL;
}


void Plan::setCurrent (Date l)
{
  // Update the time
  cur_Date = l;

  // Let all operationplans check for new ProblemBeforeCurrent and
  // ProblemBeforeFence problems.
  for(Operation::iterator i = Operation::begin();
      i != Operation::end(); ++i)
    (*i)->setChanged();
}


void Plan::writeElement (XMLOutput *o, const XMLtag& tag, mode m) const
{
  // No references
  assert(m != REFERENCE);

  // Opening tag
  if (m!=NOHEADER) o->BeginObject(tag);

  // Write all own fields
  o->writeElement(Tags::tag_name, name);
  o->writeElement(Tags::tag_description, descr);
  o->writeElement(Tags::tag_current, cur_Date);
  o->writeElement(Tags::tag_logfile, logfilename);
  o->writeElement(Tags::tag_default_calendar, def_Calendar);
  Plannable::writeElement(o, tag);

  // Solvers
  if (!Solver::empty())
  {
    o->BeginObject(Tags::tag_solvers);
    for (Solver::iterator gsolv = Solver::begin(); 
      gsolv != Solver::end(); ++gsolv)
        o->writeElement(Tags::tag_solver, *gsolv);
    o->EndObject(Tags::tag_solvers);
  }

  // Locations
  if (!Location::empty())
  {
    o->BeginObject(Tags::tag_locations);
    for (Location::iterator gloc = Location::begin(); 
      gloc != Location::end(); ++gloc)
        o->writeElement(Tags::tag_location, *gloc);
    o->EndObject(Tags::tag_locations);
  }

  // Customers
  if (!Customer::empty())
  {
    o->BeginObject(Tags::tag_customers);
    for (Customer::iterator gcust = Customer::begin(); 
      gcust != Customer::end(); ++gcust)
        o->writeElement(Tags::tag_customer, *gcust);
    o->EndObject(Tags::tag_customers);
  }

  // Calendars
  if (!Calendar::empty())
  {
    o->BeginObject(Tags::tag_calendars);
    for (Calendar::iterator gcal = Calendar::begin(); 
      gcal != Calendar::end(); ++gcal)
        o->writeElement(Tags::tag_calendar, *gcal);
    o->EndObject(Tags::tag_calendars);
  }

  // Operations
  if (!Operation::empty())
  {
    o->BeginObject(Tags::tag_operations);
    for (Operation::iterator goper = Operation::begin(); 
      goper != Operation::end(); ++goper)
        o->writeElement(Tags::tag_operation, *goper);
    o->EndObject(Tags::tag_operations);
  }

  // Items
  if (!Item::empty())
  {
    o->BeginObject(Tags::tag_items);
    for (Item::iterator gitem = Item::begin(); 
      gitem != Item::end(); ++gitem)
        o->writeElement(Tags::tag_item, *gitem);
    o->EndObject(Tags::tag_items);
  }

  // Buffers
  if (!Buffer::empty())
  {
    o->BeginObject(Tags::tag_buffers);
    for (Buffer::iterator gbuf = Buffer::begin(); 
      gbuf != Buffer::end(); ++gbuf)
        o->writeElement(Tags::tag_buffer, *gbuf);
    o->EndObject(Tags::tag_buffers);
  }

  // Demands
  if (!Demand::empty())
  {
    o->BeginObject(Tags::tag_demands);
    for (Demand::iterator gdem = Demand::begin(); 
      gdem != Demand::end(); ++gdem)
        o->writeElement(Tags::tag_demand, *gdem);
    o->EndObject(Tags::tag_demands);
  }

  // Resources
  if (!Resource::empty())
  {
    o->BeginObject(Tags::tag_resources);
    for (Resource::iterator gres = Resource::begin(); 
      gres != Resource::end(); ++gres)
        o->writeElement(Tags::tag_resource, *gres);
    o->EndObject(Tags::tag_resources);
  }

  // Operationplans
  if (!OperationPlan::empty())
  {
    o->BeginObject(Tags::tag_operation_plans);
    for(OperationPlan::iterator i = OperationPlan::begin();
        i!=OperationPlan::end(); ++i)
        o->writeElement(Tags::tag_operation_plan, *i);
    o->EndObject(Tags::tag_operation_plans);
  }

  // Problems
  Problem::const_iterator piter = Problem::begin();
  if (piter != Problem::end())
  {
    o->BeginObject(Tags::tag_problems);
    for(; piter!=Problem::end(); ++piter)
      // Note: not the regular write, but a fast write to speed things up.
      // This is possible since problems aren't nested and are never 
      // referenced.
      (*piter)->writeElement(o, Tags::tag_problem);
    o->EndObject(Tags::tag_problems);
  }

  o->EndObject(tag);
}


void Plan::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_current))
    setCurrent(pElement.getDate());
  else if (pElement.isA(Tags::tag_description))
    pElement >> descr;
  else if (pElement.isA(Tags::tag_name))
    pElement >> name;
  else if (pElement.isA(Tags::tag_default_calendar))
  {
    Calendar * c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
    if (c) setCalendar(c);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_logfile))
    setLogFile(pElement.getString());
  else
    Plannable::endElement(pIn, pElement);
}


void Plan::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  // Note: This if-statement should be ordered such that statements that
  //       have a relatively high percentage to evaluate 'true' are on top.
  if (pElement.isA(Tags::tag_demand)
      && pIn.getParentElement().isA(Tags::tag_demands))
    pIn.readto(MetaCategory::ControllerString<Demand>(Demand::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_operation_plan)
           && pIn.getParentElement().isA(Tags::tag_operation_plans))
    pIn.readto(OperationPlan::createOperationPlan(pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_item)
           && pIn.getParentElement().isA(Tags::tag_items))
    pIn.readto(MetaCategory::ControllerString<Item>(Item::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_buffer)
           && pIn.getParentElement().isA(Tags::tag_buffers))
    pIn.readto(MetaCategory::ControllerString<Buffer>(Buffer::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_resource)
           && pIn.getParentElement().isA(Tags::tag_resources))
    pIn.readto(MetaCategory::ControllerString<Resource>(Resource::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_operation)
           && pIn.getParentElement().isA(Tags::tag_operations))
    pIn.readto(MetaCategory::ControllerString<Operation>(Operation::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_solver)
           && pIn.getParentElement().isA(Tags::tag_solvers))
    pIn.readto(MetaCategory::ControllerString<Solver>(Solver::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_flow)
           && pIn.getParentElement().isA(Tags::tag_flows))
    pIn.readto(MetaCategory::ControllerDefault(Flow::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_location)
           && pIn.getParentElement().isA(Tags::tag_locations))
    pIn.readto(MetaCategory::ControllerString<Location>(Location::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_calendar)
           && pIn.getParentElement().isA(Tags::tag_calendars))
    pIn.readto(MetaCategory::ControllerString<Calendar>(Calendar::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_customer)
           && pIn.getParentElement().isA(Tags::tag_customers))
    pIn.readto(MetaCategory::ControllerString<Customer>(Customer::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_default_calendar))
    pIn.readto(MetaCategory::ControllerString<Calendar>(Calendar::metadata,pIn.getAttributes()));
  else if (pElement.isA(Tags::tag_commands))
  {
    LockManager::getManager().obtainWriteLock(&(pIn.getCommands()));
    pIn.readto(&(pIn.getCommands()));
  }
  else if (pElement.isA(Tags::tag_problems))
    pIn.IgnoreElement();
  /* @todo next block of code is wanted, but doesn't work now. 'own' fields
   like "current" put the plan object in ignore state...
  else if (!pElement.isA(Tags::tag_plan))
    // If we come across unknown tags, we simply ignore them. This allows you
    // to add your own additional fields to the XML data, when required.
    pIn.IgnoreElement();
  */ 
}


void Plan::setLogFile(string x)
{
    // Close an eventual existing log file.
  	if (!logfilename.empty()) clog << "Closing plan on " << Date::now() << endl;
    if (log) log.close();

    // Pick up the file name
    logfilename = x;

    // No new logfile specified
    if (x.empty()) return;

    // Open the file
    log.open(x.c_str(), ios::out);
    if (log.bad())
      // The log file could not be opened
      throw RuntimeException("Could not open log file '" + x + "'");

    // Redirect the clog output channel.
    clog.rdbuf(log.rdbuf());

    // Print a nice header
#ifdef VERSION
    clog << "Start logging PLANNER " << VERSION << " ("
      << __DATE__ << ") on " << Date::now() << endl;
#else
    clog << "Start logging PLANNER (" << __DATE__
      << ") on " << Date::now() << endl;
#endif
}


}
