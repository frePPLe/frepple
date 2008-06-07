/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye                                    *
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
DECLARE_EXPORT Operation::Operationlist Operation::nosubOperations;


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
    if (m->getProducingOperation() == this)
      m->setProducingOperation(NULL);

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


void Operation::initOperationPlan (OperationPlan* opplan, double q,
    const Date& s, const Date& e, Demand* l, OperationPlan* ow,
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


void Operation::deleteOperationPlans(bool deleteLockedOpplans)
{
  OperationPlan::deleteOperationPlans(this, deleteLockedOpplans);
}


DECLARE_EXPORT void Operation::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Note that this class is abstract and never instantiated directly. There is
  // therefore no reason to ever write a header.
  assert(m == NOHEADER);

  // Write the fields
  HasDescription::writeElement(o, tag);
  Plannable::writeElement(o, tag);
  if (post_time)
    o->writeElement(Tags::tag_posttime, post_time);
  if (pre_time)
    o->writeElement(Tags::tag_pretime, pre_time);
  if (getCost() != 1.0)
    o->writeElement(Tags::tag_cost, getCost());
  if (fence)
    o->writeElement(Tags::tag_fence, fence);
  if (size_minimum != 1.0)
    o->writeElement(Tags::tag_size_minimum, size_minimum);
  if (size_multiple > 0.0)
    o->writeElement(Tags::tag_size_multiple, size_multiple);
  if (loc)
    o->writeElement(Tags::tag_location, loc);

  // Write extra plan information
  if ((o->getContentType() == XMLOutput::PLAN
      || o->getContentType() == XMLOutput::PLANDETAIL) && first_opplan)
  {
    o->BeginObject(Tags::tag_operationplans);
    for (OperationPlan::iterator i(this); i!=OperationPlan::end(); ++i)
      o->writeElement(Tags::tag_operationplan, *i, FULL);
    o->EndObject(Tags::tag_operationplans);
  }
}


DECLARE_EXPORT void Operation::beginElement (XMLInput& pIn, const Attribute& pAttr)
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
  else if (pAttr.isA (Tags::tag_pretime))
    setPreTime(pElement.getTimeperiod());
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


DECLARE_EXPORT void OperationFixedTime::setOperationPlanParameters
(OperationPlan* oplan, double q, Date s, Date e, bool preferEnd) const
{
  // Invalid call to the function, or locked operationplan.
  if (!oplan || q<0 || oplan->getLocked()) return;

  // All quantities are valid
  if (fabs(q - oplan->getQuantity()) > ROUNDING_ERROR)
    oplan->setQuantity(q, false, false);

  // Set the start and end date.
  if (e && s)
  {
    if (preferEnd) oplan->setStartAndEnd(e - duration, e);
    else oplan->setStartAndEnd(s, s + duration);
  }
  else if (s) oplan->setStartAndEnd(s, s + duration);
  else oplan->setStartAndEnd(e - duration, e);
}


DECLARE_EXPORT void OperationFixedTime::writeElement
(XMLOutput *o, const Keyword& tag, mode m) const
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


DECLARE_EXPORT void OperationFixedTime::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_duration))
    setDuration (pElement.getTimeperiod());
  else
    Operation::endElement (pIn, pAttr, pElement);
}


DECLARE_EXPORT void OperationTimePer::setOperationPlanParameters
(OperationPlan* oplan, double q, Date s, Date e, bool preferEnd) const
{
  // Invalid call to the function.
  if (!oplan || q<0) return;

  // Respect minimum size
  if (q < getSizeMinimum() && q>0) q = getSizeMinimum();

  // The logic depends on which dates are being passed along
  if (s && e)
  {
    if (s > e)
    {
      // End date is later than the start. Swap the dates.
      Date tmp = s;
      s = e;
      e = tmp;
    }
    // Case 1: Both the start and end date are specified: Compute the quantity
    if (e - s < duration)
    {
      // Start and end aren't far enough from each other to fit the constant
      // part of the operation duration. This is infeasible.
      oplan->setQuantity(0,false,false);
      oplan->setEnd(e);
    }
    else
    {
      // Divide the variable duration by the duration_per time, to compute the
      // maximum number of pieces that can be produced in the timeframe
      double max_q = duration_per ?
        static_cast<double>(e - s - duration) / duration_per :
        q;

      // Set the quantity to either the maximum or the requested quantity,
      // depending on which one is smaller.
      oplan->setQuantity(q < max_q ? q : max_q, true, false);

      // Updates the dates
      TimePeriod d = static_cast<long>(oplan->getQuantity()*static_cast<long>(duration_per)) + duration;
      if (preferEnd) oplan->setStartAndEnd(e-d, e);
      else oplan->setStartAndEnd(s, s+d);
    }
  }
  else if (e)
  {
    // Case 2: Only an end date is specified. Respect the quantity and
    // compute the start date
    oplan->setQuantity(q,true,false);
    TimePeriod t(static_cast<long>(duration_per * oplan->getQuantity()));
    oplan->setStartAndEnd(e - duration - t, e);
  }
  else if (s)
  {
    // Case 3: Only a start date is specified. Respect the quantity and compute
    // the end date
    oplan->setQuantity(q,true,false);
    TimePeriod t(static_cast<long>(duration_per * oplan->getQuantity()));
    oplan->setStartAndEnd(s, s + duration + t);
  }
  else
  {
    // Case 4: No date was given at all. Respect the quantity and the existing
    // end date of the operationplan.
    oplan->setQuantity(q,true,false);
    TimePeriod t(static_cast<long>(duration_per * oplan->getQuantity()));
    oplan->setStartAndEnd(
      oplan->getDates().getEnd() - duration - t,
      oplan->getDates().getEnd()
    );
  }
}


DECLARE_EXPORT void OperationTimePer::writeElement
(XMLOutput *o, const Keyword& tag, mode m) const
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


DECLARE_EXPORT void OperationTimePer::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_duration))
    setDuration (pElement.getTimeperiod());
  else if (pAttr.isA (Tags::tag_duration_per))
    setDurationPer (pElement.getTimeperiod());
  else
    Operation::endElement (pIn, pAttr, pElement);
}


DECLARE_EXPORT void OperationRouting::writeElement
(XMLOutput *o, const Keyword& tag, mode m) const
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


DECLARE_EXPORT void OperationRouting::beginElement (XMLInput& pIn, const Attribute& pAttr)
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


DECLARE_EXPORT void OperationRouting::setOperationPlanParameters
(OperationPlan* oplan, double q, Date s, Date e, bool preferEnd) const
{
  OperationPlanRouting *op = dynamic_cast<OperationPlanRouting*>(oplan);

  // Invalid call to the function
  if (!op || q<0)
    throw LogicException("Incorrect parameters for routing operationplan");

  if (op->step_opplans.empty())
  {
    // No step operationplans to work with. Just apply the requested quantity
    // and dates.
    oplan->setQuantity(q,false,false);
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
        (*i)->getOperation()->setOperationPlanParameters(*i,q,Date::infinitePast,e,preferEnd);
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
        (*i)->getOperation()->setOperationPlanParameters(*i,q,s,Date::infinitePast,preferEnd);
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


DECLARE_EXPORT OperationPlan* OperationRouting::createOperationPlan 
  (double q, Date s, Date e, Demand* l, OperationPlan* ow, 
    unsigned long i, bool makeflowsloads) const
{
  // Note that the created operationplan is of a specific subclass
  OperationPlan *opplan = new OperationPlanRouting();
  initOperationPlan(opplan,q,s,e,l,ow,i,makeflowsloads);
  return opplan;
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
(XMLOutput *o, const Keyword& tag, mode m) const
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

  // Write the standard fields
  Operation::writeElement(o, tag, NOHEADER);

  // Write the extra fields
  o->BeginObject(Tags::tag_alternates);
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
  o->EndObject(Tags::tag_alternates);

  // Ending tag
  o->EndObject(tag);
}


DECLARE_EXPORT void OperationAlternate::beginElement (XMLInput& pIn, const Attribute& pAttr)
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
    pIn.setUserArea(new tempData(NULL,alternateProperty(1,DateRange())));
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


DECLARE_EXPORT OperationPlan* OperationAlternate::createOperationPlan (double q,
    Date s, Date e, Demand* l, OperationPlan* ow,
    unsigned long i, bool makeflowsloads) const
{
  // Note that the operationplan created is of a different subclass.
  OperationPlan *opplan = new OperationPlanAlternate();
  if (!s) s = e;
  if (!e) e = s;
  initOperationPlan(opplan,q,s,e,l,ow,i,makeflowsloads);
  return opplan;
}


DECLARE_EXPORT void OperationAlternate::setOperationPlanParameters
(OperationPlan* oplan, double q, Date s, Date e, bool preferEnd) const
{
  // Argument passed must be a alternate operationplan
  OperationPlanAlternate *oa = dynamic_cast<OperationPlanAlternate*>(oplan);

  // Invalid calls to this function
  if (!oa || q<0)
    throw LogicException("Incorrect parameters for alternate operationplan");

  if (!oa->altopplan)
  {
    // Blindly accept the parameters if there is no suboperationplan
    oplan->setQuantity(q,false,false);
    oplan->setStartAndEnd(s, e);
  }
  else
    // Pass the call to the sub-operation
    oa->altopplan->getOperation()
      ->setOperationPlanParameters(oa->altopplan,q,s,e,preferEnd);
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

}
