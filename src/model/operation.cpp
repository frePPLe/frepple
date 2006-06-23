/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/operation.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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


#define FREPPLE_CORE 
#include "frepple/model.h"

namespace frepple
{

template<class Operation> DECLARE_EXPORT Tree HasName<Operation>::st;
Operation::Operationlist Operation::nosubOperations;


Operation::~Operation()
{
  // Delete all existing operationplans (even locked ones)
  deleteOperationPlans(true);

  // The Flow and Load objects are automatically deleted by the destructor
  // of the Association list class.

  // Remove the reference to this operation from all items
  for (Item::iterator k = Item::begin(); k != Item::end(); ++k)
    if ((*k)->getDelivery() == this) (*k)->setDelivery(NULL);

  // Remove the reference to this operation from all demands
  for (Demand::iterator l = Demand::begin(); l != Demand::end(); ++l)
    if ((*l)->getOperation() == this) (*l)->setOperation(NULL);

  // Remove the reference to this operation from all buffers
  for (Buffer::iterator m = Buffer::begin(); m != Buffer::end(); ++m)
  {
    if ((*m)->getProducingOperation() == this)
      (*m)->setProducingOperation(NULL);
    if ((*m)->getConsumingOperation() == this)
    	(*m)->setConsumingOperation(NULL);
  }

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
    removeSubOperation(*getSubOperations().begin());
}


OperationAlternate::~OperationAlternate()
{
  // Note that we are not using a for-loop since our function is actually
  // updating the list of super-operations at the same time as we move
  // through it.
  while (!getSubOperations().empty())
    removeSubOperation(*getSubOperations().begin());
}


OperationPlan* Operation::createOperationPlan (float q, Date s, Date e,
    Demand* l, bool updates_okay, OperationPlan* ow, unsigned long i,
    bool makeflowsloads) const
{
  OperationPlan *opplan = new OperationPlan();
  initOperationPlan(opplan,q,s,e,l,updates_okay,ow,i,makeflowsloads);
  return opplan;
}


void Operation::initOperationPlan (OperationPlan* opplan, float q,
   const Date& s, const Date& e, Demand* l, bool updates_okay,
   OperationPlan* ow, unsigned long i, bool makeflowsloads) const
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

  // Allow immediate propagation of changes, or not
  opplan->setAllowUpdates(updates_okay);
}


void Operation::deleteOperationPlans(bool deleteLockedOpplans)
{
  OperationPlan::deleteOperationPlans(this, deleteLockedOpplans);
}


void Operation::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Note that this class is abstract and never instantiated directly. There is
  // therefore no reason to ever write a header.
  assert(m == NOHEADER);

  // Write the fields
  HasDescription::writeElement(o, tag);
  Plannable::writeElement(o, tag);
  if (delaytime)
    o->writeElement(Tags::tag_delay, delaytime);
  if (fence)
    o->writeElement(Tags::tag_fence, fence);
  if (size_minimum>0.0f)
    o->writeElement(Tags::tag_size_minimum, size_minimum);
  if (size_multiple>0.0f)
    o->writeElement(Tags::tag_size_multiple, size_multiple);
}


void Operation::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_flow)
      && pIn.getParentElement().isA(Tags::tag_flows))
  {
    Flow *f = 
      dynamic_cast<Flow*>(MetaCategory::ControllerDefault(Flow::metadata,pIn.getAttributes()));
    if (f) f->setOperation(this);
    pIn.readto(f);
  }
  else if (pElement.isA (Tags::tag_load)
      && pIn.getParentElement().isA(Tags::tag_loads))
  {
    Load * l = new Load();
    LockManager::getManager().obtainWriteLock(l);
    l->setOperation(this);
    pIn.readto(l);
  }
}


void Operation::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_delay))
    setDelay(pElement.getTimeperiod());
  else if (pElement.isA (Tags::tag_fence))
    setFence(pElement.getTimeperiod());
  else if (pElement.isA (Tags::tag_size_minimum))
    setSizeMinimum(pElement.getFloat());
  else if (pElement.isA (Tags::tag_size_multiple))
    setSizeMultiple(pElement.getFloat());
  else
  {
    Plannable::endElement(pIn, pElement);
    HasDescription::endElement(pIn, pElement);
  }
}


void OperationFixedTime::setOperationPlanParameters
  (OperationPlan* oplan, float q, Date s, Date e) const
{
  // Invalid call to the function, or locked operationplan.
  if (!oplan || q<0 || oplan->getLocked()) return;

  // All quantities are valid
  if (fabs(q - oplan->getQuantity()) > ROUNDING_ERROR)
    oplan->setQuantity(q);

  // Respect end date and duration, when an end date is given.
  if (e) oplan->setStartAndEnd(e - duration, e);
  else oplan->setStartAndEnd(s, s + duration);
}


void OperationFixedTime::writeElement
  (XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
      (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }
    
  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Operation::writeElement(o, tag, NOHEADER);
  if (duration) o->writeElement (Tags::tag_duration, duration);
  o->EndObject (tag);
}


void OperationFixedTime::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_duration))
    setDuration (pElement.getTimeperiod());
  else
    Operation::endElement (pIn, pElement);
}


void OperationTimePer::setOperationPlanParameters
      (OperationPlan* oplan, float q, Date s, Date e) const
{
  // Invalid call to the function.
  if (!oplan || q<0) return;

  // The logic depends on which dates are being passed along
  if (s && e && s<=e)
  {
    // Case 1: Both the start and end date are specified: Compute the quantity
    if (e - s <= duration)
      // Start and end aren't far enough from each other to fit the constant
      // part of the operation duration. This is infeasible.
      oplan->setQuantity(0);
    else
    {
      // Divide the variable duration by the duration_per time, to compute the
      // maximum number of pieces that can be produced in the timeframe
      float max_q = (float)(e - s - duration) / duration_per;

      // Set the quantity to either the maximum or the requested quantity,
      // depending on which one is smaller.
      oplan->setQuantity(q>max_q ? max_q : q);
    }

    // Set the start and end date, as specified
    oplan->setStartAndEnd(s,e);
  }
  else if (e)
  {
    // Case 2: Only an end date is specified. Respect the quantity and
    // compute the start date
    oplan->setQuantity(q);
    TimePeriod t(static_cast<long>(duration_per * q));
    oplan->setStartAndEnd(e - duration - t, e);
  }
  else if (s)
  {
    // Case 3: Only a start date is specified. Respect the quantity and compute
    // the end date
    oplan->setQuantity(q);
    TimePeriod t(static_cast<long>(duration_per * q));
    oplan->setStartAndEnd(s, s + duration + t);
  }
  else
  {
    // Case 4: No date was given at all. Respect the quantity and the existing
    // end date of the operationplan.
    oplan->setQuantity(q);
    TimePeriod t(static_cast<long>(duration_per * q));
    oplan->setStartAndEnd(
      oplan->getDates().getEnd() - duration - t,
      oplan->getDates().getEnd()
      );
  }
}


void OperationTimePer::writeElement
  (XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
      (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject 
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the complete object
  Operation::writeElement(o, tag, NOHEADER);
  o->writeElement(Tags::tag_duration, duration);
  o->writeElement(Tags::tag_duration_per, duration_per);
  o->EndObject(tag);
}


void OperationTimePer::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_duration))
    setDuration (pElement.getTimeperiod());
  else if (pElement.isA (Tags::tag_duration_per))
    setDurationPer (pElement.getTimeperiod());
  else
    Operation::endElement (pIn, pElement);
}


void OperationRouting::writeElement
  (XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
      (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }
    
  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Operation::writeElement(o, tag, NOHEADER);
  if (steps.size())
  {
    o->BeginObject(Tags::tag_steps);
    for (Operationlist::const_iterator i = steps.begin(); i!=steps.end(); ++i)
      o->writeElement(Tags::tag_operation, *i, REFERENCE);
    o->EndObject(Tags::tag_steps);
  }
  o->EndObject(tag);
}


void OperationRouting::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
    Operation::beginElement(pIn, pElement);
}


void OperationRouting::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_operation)
  && pIn.getParentElement().isA(Tags::tag_steps))
  {
    Operation *oper = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (oper) addStepBack (oper);
    else throw LogicException("Incorrect object type during read operation");
  }
  Operation::endElement (pIn, pElement);
}


void OperationRouting::setOperationPlanParameters
  (OperationPlan* oplan, float q, Date s, Date e) const
{
  OperationPlanRouting *op = dynamic_cast<OperationPlanRouting*>(oplan);

  // Invalid call to the function
  if (!op || q<0)
    throw LogicException("Incorrect parameters for routing operationplan");

  if (op->step_opplans.empty())
  {
    // No step operationplans to work with. Just apply the requested quantity
    // and dates.
    oplan->setQuantity(q);
    if (!s && e) s = e;
    if (s && !e) e = s;
    oplan->setStartAndEnd(s,e);
    return;
  }

  // Behavior depends on the dates being passed.
  // Move all sub-operationplans in an orderly fashion, either starting from
  // the specified end date or the specified start date.
  bool firstOp = true;
  if (e)
  {
    // Case 1: an end date is specified
    for (list<OperationPlan*>::reverse_iterator i = op->step_opplans.rbegin();
         i != op->step_opplans.rend(); ++i)
    {
      if ((*i)->getDates().getEnd() > e || firstOp)
      {
        (*i)->getOperation()->setOperationPlanParameters(*i,q,Date::infinitePast,e);
        e = (*i)->getDates().getStart();
        firstOp = false;
      }
      else
        // There is sufficient slack in the routing, and the start
        // date doesn't need to be changed
        return;
    }
  }
  else
  {
    // Case 2: a start date is specified
    for (list<OperationPlan*>::const_iterator i = op->step_opplans.begin();
         i != op->step_opplans.end(); ++i)
    {
      if ((*i)->getDates().getStart() < s || firstOp)
      {
        (*i)->getOperation()->setOperationPlanParameters(*i,q,s,Date::infinitePast);
        s = (*i)->getDates().getEnd();
        firstOp = false;
      }
      else
        // There is sufficient slack in the routing, and the start
        // date doesn't need to be changed
        return;
    }
  }
}


OperationPlan* OperationRouting::createOperationPlan (float q, Date s, Date e,
    Demand* l, bool updates_okay, OperationPlan* ow, unsigned long i,
    bool makeflowsloads) const
{
  // Note that the created operationplan is of a specific subclass
  OperationPlan *opplan = new OperationPlanRouting();
  initOperationPlan(opplan,q,s,e,l,updates_okay,ow,i,makeflowsloads);
  return opplan;
}


void OperationAlternate::addAlternate(Operation* o, float prio)
{
  if (!o) return;
  Operationlist::iterator altIter = alternates.begin();
  priolist::iterator prioIter = priorities.begin();
  while (prioIter!=priorities.end() && prio >= *prioIter)
  {
    ++prioIter;
    ++altIter;
  }
  priorities.insert(prioIter,prio);
  alternates.insert(altIter,o);
  o->addSuperOperation(this);
}


float OperationAlternate::getPriority(Operation* o) const
{
  if (!o)
    throw LogicException("Null pointer passed when searching for a \
      suboperation of alternate operation '" + getName() + "'");
  Operationlist::const_iterator altIter = alternates.begin();
  priolist::const_iterator prioIter = priorities.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++prioIter;
    ++altIter;
  }
  if (*altIter == o)
    return *prioIter;
  throw DataException("Operation '" + o->getName() +
    "' isn't a suboperation of alternate operation '" + getName() + "'");
}


void OperationAlternate::setPriority(Operation* o, float f)
{
  if (!o) return;
  Operationlist::const_iterator altIter = alternates.begin();
  priolist::iterator prioIter = priorities.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++prioIter;
    ++altIter;
  }
  if (*altIter == o)
    *prioIter = f;
  else
    throw DataException("Operation '" + o->getName() +
      "' isn't a suboperation of alternate operation '" + getName() + "'");
}


void OperationAlternate::writeElement
  (XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
      (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Operation::writeElement(o, tag, NOHEADER);
  o->BeginObject(Tags::tag_alternates);
  priolist::const_iterator prioIter = priorities.begin();
  for (Operationlist::const_iterator i = alternates.begin();
       i != alternates.end(); ++i)
  {
    o->BeginObject(Tags::tag_alternate);
    o->writeElement(Tags::tag_operation, *i, REFERENCE);
    o->writeElement(Tags::tag_priority, *(prioIter++));
    o->EndObject (Tags::tag_alternate);
  }
  o->EndObject(Tags::tag_alternates);
  o->EndObject(tag);
}


void OperationAlternate::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
    Operation::beginElement(pIn, pElement);
}


void OperationAlternate::endElement (XMLInput& pIn, XMLElement& pElement)
{
	// Saving me some typing...
	typedef pair<float,Operation*> tempData;

  /** Create a temporary object */
  if (!pIn.getUserArea()) pIn.setUserArea(new tempData(1.0,NULL));

  if (pElement.isA(Tags::tag_alternate))
  {
    addAlternate(
    	static_cast<tempData*>(pIn.getUserArea())->second,
    	static_cast<tempData*>(pIn.getUserArea())->first);
    // Reset the defaults
    static_cast<tempData*>(pIn.getUserArea())->first = 1.0f;
    static_cast<tempData*>(pIn.getUserArea())->second = NULL;
  }
  else if (pElement.isA(Tags::tag_priority))
    static_cast<tempData*>(pIn.getUserArea())->first = pElement.getFloat();
  else if (pElement.isA(Tags::tag_operation)
  && pIn.getParentElement().isA(Tags::tag_alternate))
  {
    Operation * b = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (b) static_cast<tempData*>(pIn.getUserArea())->second = b;
    else throw LogicException("Incorrect object type during read operation");
  }
  Operation::endElement (pIn, pElement);

  // Delete the temporary object
  if (pIn.isObjectEnd()) delete static_cast<tempData*>(pIn.getUserArea());
}


OperationPlan* OperationAlternate::createOperationPlan (float q, Date s, 
  Date e, Demand* l, bool updates_okay, OperationPlan* ow, unsigned long i,
  bool makeflowsloads) const
{
  // Note that the operationplan created is of a different subclass.
  OperationPlan *opplan = new OperationPlanAlternate();
  if (!s) s = e;
  if (!e) e = s;
  initOperationPlan(opplan,q,s,e,l,updates_okay,ow,i,makeflowsloads);
  return opplan;
}


void OperationAlternate::setOperationPlanParameters
  (OperationPlan* oplan, float q, Date s, Date e) const
{
  // Argument passed must be a alternate operationplan
  OperationPlanAlternate *oa = dynamic_cast<OperationPlanAlternate*>(oplan);

  // Invalid calls to this function
  if (!oa || q<0)
    throw LogicException("Incorrect parameters for alternate operationplan");

  if(!oa->altopplan)
  {
    // Blindly accept the parameters if there is no suboperationplan
    oplan->setQuantity(q);
    oplan->setStartAndEnd(s, e);
  }
  else
    // Pass the call to the sub-operation
    oa->altopplan->getOperation()
      ->setOperationPlanParameters(oa->altopplan,q,s,e);
}


void OperationAlternate::removeSubOperation(Operation *o)
{
  Operationlist::iterator altIter = alternates.begin();
  priolist::iterator prioIter = priorities.begin();
  while (altIter!=alternates.end() && *altIter != o)
  {
    ++prioIter;
    ++altIter;
  }
  if (*altIter == o)
  {
    alternates.erase(altIter);
    priorities.erase(prioIter);
    o->superoplist.remove(this);
    setChanged();
  }
  else
    clog << "Warning: operation '" << *o
    << "' isn't a suboperation of alternate operation '" << *this
    << "'" << endl;
}


void OperationEffective::writeElement
  (XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
      (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }
    
  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  Operation::writeElement(o, tag, NOHEADER);
  o->writeElement(Tags::tag_calendar, cal);
  if (!useEndDate) o->writeElement(Tags::tag_startorend, useEndDate);
  o->EndObject(tag);
}


void OperationEffective::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_calendar))
    pIn.readto( Calendar::reader(Calendar::metadata,pIn.getAttributes()) );
  else
    Operation::beginElement(pIn, pElement);
}


void OperationEffective::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_calendar))
  {
    CalendarOperation* c = 
      dynamic_cast<CalendarOperation*>(pIn.getPreviousObject());
    if (c)
      setCalendar(c);
    else
    {
      Calendar *c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
      if (!c)
        throw LogicException("Incorrect object type during read operation");
      throw DataException("Calendar '" + c->getName() +
        "' has invalid type for use as effective operation calendar");
    }
  }
  else if (pElement.isA(Tags::tag_startorend))
    setUseEndDate(pElement.getBool());
  else
    Operation::endElement (pIn, pElement);
}


OperationPlan* OperationEffective::createOperationPlan 
  (float q, Date s, Date e, Demand* l, bool updates_okay, OperationPlan* ow, 
  unsigned long i, bool makeflowsloads) const
{
  // Note that the operationplan created is of a different subclass.
  OperationPlan *opplan = new OperationPlanEffective();
  initOperationPlan(opplan,q,s,e,l,updates_okay,ow,i,makeflowsloads);
  return opplan;
}


void OperationEffective::setOperationPlanParameters
  (OperationPlan* opplan, float q, Date s, Date e) const
{
  // Argument passed must be a alternate operationplan
  OperationPlanEffective *oa = dynamic_cast<OperationPlanEffective*>(opplan);

  // Invalid calls to this function
  if (!oa || q<0) return;

  // Need a calendar
  if (!cal)
    throw DataException("Effective operation '" + getName()
      + "' with unspecified calendar");

  // Need at least 1 date
  if (!e && !s)
    throw LogicException ("Need at least 1 date when creating " \
      "suboperationplans for operation '" + getName() + "'");

  // Loop till we have an suboperationplan that is valid
  do
  {
    if (oa->effopplan)
    {
      // Update existing suboperationplan to meet new quantity, start and end
      oa->effopplan->getOperation()
        ->setOperationPlanParameters(oa->effopplan,q,s,e);

      // Look up the correct operation to use
      Operation* oper = cal->getValue( useEndDate ?
          oa->effopplan->getDates().getEnd() :
          oa->effopplan->getDates().getStart() );

      // Compare current suboperation with the expected one
      if (oper == oa->effopplan->getOperation())
        // Suboperationplan is still valid indeed. Mission accomplished.
        return;

      // Use dates of the existing operationplan for new creation
      if (!s && !useEndDate) s = oa->effopplan->getDates().getStart();
      if (!e && useEndDate) e = oa->effopplan->getDates().getEnd();

      // We need to clear the owner pointer before deleting the
      // suboperationplan. Otherwise oa will get deleted itself...
      oa->effopplan->owner = NULL;
      delete oa->effopplan;
      oa->effopplan = NULL;
    }

    // Need to create a new suboperationplan
    if (useEndDate)
    {
      Operation* oper = cal->getValue(e ? e : s);
      if (oper)
        oa->effopplan = oper->createOperationPlan(q, Date::infinitePast, e, NULL, true, oa);
      else
        throw LogicException
          ("Invalid effective calendar for operation " + getName());
    }
    else
    {
      Operation* oper = cal->getValue(s ? s : e);
      if (oper)
        oa->effopplan = oper->createOperationPlan(q, s, Date::infinitePast, NULL, true, oa);
      else
        throw LogicException
          ("Invalid effective calendar for operation " + getName());
    }

    // Verify the newly created operationplan
    Operation* oper = cal->getValue(
      useEndDate ?
        oa->effopplan->getDates().getEnd() :
        oa->effopplan->getDates().getStart() );

    // Compare current suboperation with the expected one
    if (oper == oa->effopplan->getOperation())
      // Suboperationplan is still valid indeed. Mission accomplished.
      return;

    // If the created operationplan turns out to be invalid, we loop again.
    // This could happen if e.g. the effective operation is based on the end
    // start, while the call to this function was passed a start date instead.
    // After the creation we need to double-check the result, and potentially
    // even redo it.
  }
  while (true);
}


}
