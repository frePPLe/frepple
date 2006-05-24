/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/buffer.cpp $
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
#include <cmath>

// This is the name used for the dummy operation used to represent the
// inventory.
#define INVENTORY_OPERATION "Inventory of buffer '" + string(getName()) + "'"

namespace frepple
{

template<class Buffer> Tree HasName<Buffer>::st;


void Buffer::setOnHand(float f)
{
  // The dummy operation to model the inventory may need to be created
  Operation *o = Operation::find(INVENTORY_OPERATION);
  Flow *fl;
  if (!o)
  {
    // Create a fixed time operation with zero leadtime, hidden from the xml
    // output, hidden for the solver, and without problem detection.
    o = new OperationFixedTime(INVENTORY_OPERATION);
    Operation::add(o);  // No need to check again for existance
    o->setHidden(true);
    o->setDetectProblems(false);
    fl = new FlowEnd(o, this, 1);
  }
  else
    // Find the flow of this operation
    fl = *(o->getFlows().begin());

  // Check valid pointers
  if (!fl || !o) 
    throw LogicException("Failed creating inventory operation for '" 
    + getName() + "'");

  // Make sure the sign of the flow is correct: +1 or -1.
  fl->setQuantity(f>0.0f ? 1.0f : -1.0f);

  // Create a dummy operationplan on the inventory operation
  OperationPlan::iterator i(o);
  if (i == OperationPlan::end())
  {
    // No operationplan exists yet
    OperationPlan *opplan = o->createOperationPlan(
        static_cast<float>(fabs(f)), 0L, 0L, NULL, false
        );
    opplan->setLocked(true);
    opplan->initialize();
    opplan->setAllowUpdates(true);
  }
  else
  {
    // Update the existing operationplan
    i->setLocked(false);
    i->setQuantity(static_cast<float>(fabs(f)));
    i->setLocked(true);
  }
  setChanged();
}


double Buffer::getOnHand(Date d) const
{
  double tmp(0.0);
  for(flowplanlist::const_iterator oo=flowplans.begin();
      oo!=flowplans.end(); ++oo)
  {
    if (oo->getDate() > d)
      // Found a flowplan with a later date.
      // Return the onhand after the previous flowplan.
      return tmp;
    tmp = oo->getOnhand();
  }
  // Found no flowplan: either we have specified a date later than the
  // last flowplan, either there are no flowplans at all.
  return tmp;
}


double Buffer::getOnHand(Date d1, Date d2, bool min) const
{
  // Swap parameters if required
  if (d2 < d1)
  {
    Date x(d1);
    d2 = d1;
    d2 = x;
  }

  // Loop through all flowplans
  double tmp(0.0), record(0.0);
  Date d, prev_Date;
  for(flowplanlist::const_iterator oo=flowplans.begin(); true; ++oo)
  {
    if (oo==flowplans.end() || oo->getDate() > d)
    {
      // Date has now changed or we have arrived at the end

      // New max?
      if (prev_Date < d1)
        // Not in active Date range: we simply follow the onhand profile
        record = tmp;
      else
      {
        // In the active range
        // New extreme?
        if (min) {if (tmp < record) record = tmp;}
        else {if (tmp > record) record = tmp;}
      }

      // Are we done now?
      if (prev_Date > d2 || oo==flowplans.end()) return record;

      // Set the variable with the new Date
      d = oo->getDate();
    }
    tmp = oo->getOnhand();
    prev_Date = oo->getDate();
  }
  // The above for-loop controls the exit. This line of code is never reached.
  throw LogicException("Unreachable code reached");
}


void Buffer::writeProfile(XMLOutput* o, Calendar* hor) const
{
  // Check whether we need to bucketize or not
  if (hor)
  {
    // Mode 2: Aggregate the supply and demand per bucket

    // Write the header
    o->BeginObject
      (Tags::tag_bucket_profile, Tags::tag_calendar, hor->getName());

    // Loop through both the flowplans and the buckets
    double onhand(0.0);
    float demand, supply;
    flowplanlist::const_iterator f = flowplans.begin();
    for (Calendar::Bucketlist::const_iterator b = hor->getBuckets().begin();
         b != hor->getBuckets().end(); ++b)
    {
      o->BeginObject(Tags::tag_bucket);
      o->writeElement(Tags::tag_name, (*b)->getName());
      o->writeElement(Tags::tag_start, (*b)->getStart());
      o->writeElement(Tags::tag_end, (*b)->getEnd());
      o->writeElement(Tags::tag_start_onhand, onhand);
      o->writeElement(Tags::tag_minimum, 
         f!=flowplans.end() ? f->getMin() : 0.0);
      demand = 0.0f;
      supply = 0.0f;
      for (; f!=flowplans.end() && f->getDate()<(*b)->getEnd(); ++f)
      {
        if (f->getQuantity() > 0.0f) supply += f->getQuantity();
        else demand -= f->getQuantity();
        onhand = f->getOnhand();
      }
      o->writeElement(Tags::tag_demand, demand);
      o->writeElement(Tags::tag_supply, supply);
      o->writeElement(Tags::tag_end_onhand, onhand);
      o->EndObject(Tags::tag_bucket);
    }

    // Finish
    o->EndObject (Tags::tag_bucket_profile);
  }
  else
  {
    // Mode 1: No bucketization required. Simply dump all flowplans.

    // Write the header
    o->BeginObject (Tags::tag_profile);

    // Loop through both the flowplans and the buckets
    for(flowplanlist::const_iterator oo=flowplans.begin();
        oo!=flowplans.end(); ++oo)
      if (oo->getType() == 1)
      {
        o->BeginObject (Tags::tag_flow);
        o->writeElement (Tags::tag_date, oo->getDate());
        o->writeElement (Tags::tag_quantity, oo->getQuantity());
        o->writeElement (Tags::tag_onhand, oo->getOnhand());
        o->writeElement (Tags::tag_minimum, oo->getMin());
        const FlowPlan* x = dynamic_cast<const FlowPlan*>(&*oo);
        if (x && x->getOperationPlan()->getIdentifier())
          o->writeElement(Tags::tag_id, x->getOperationPlan()->getIdentifier());
        o->EndObject (Tags::tag_flow);
      }

    // Finish
    o->EndObject (Tags::tag_profile);
  }
}


void Buffer::writeElement(XMLOutput *o, const XMLtag &tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }
    
  // Write the complete object
  if (m!= NOHEADER) o->BeginObject(tag, Tags::tag_name, getName());

  // Write own fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Buffer>::writeElement(o, tag);
  o->writeElement(Tags::tag_producing, producing_operation);
  o->writeElement(Tags::tag_consuming, consuming_operation);
  o->writeElement(Tags::tag_item, it);
  o->writeElement(Tags::tag_location, loc);
  Plannable::writeElement(o, tag);

  // Flows
  if (!flows.empty())
  {
    o->BeginObject (Tags::tag_flows);
    for (flowlist::const_iterator i = flows.begin(); i != flows.end();)
      // We use the FULL mode, to force the flows being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_flow, *(i++), FULL);
    o->EndObject (Tags::tag_flows);
  }

  // Onhand
  flowplanlist::const_iterator i = flowplans.begin();
  // Loop through the flowplans at the start of the horizon
  for (; i!=flowplans.end() && i->getType()!=1 && !i->getDate(); ++i) ;
  if (i!=flowplans.end() && i->getType()==1)
  {
    // A flowplan has been found
    const FlowPlan *fp = dynamic_cast<const FlowPlan*>(&*i);
    if (fp
      && fp->getFlow()->getOperation()->getName() == string(INVENTORY_OPERATION)
      && fabs(fp->getQuantity()) > ROUNDING_ERROR)
      o->writeElement(Tags::tag_onhand, fp->getQuantity());
  }

  // Minimum and maximum inventory targets
  o->writeElement(Tags::tag_minimum, min_cal);
  o->writeElement(Tags::tag_maximum, max_cal);

  // Ending tag
  o->EndObject(tag);
}


void Buffer::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_flow)
      && pIn.getParentElement().isA(Tags::tag_flows))
  {
    Flow *f = 
      dynamic_cast<Flow*>(MetaCategory::ControllerDefault(Flow::metadata,pIn.getAttributes()));
    if (f) f->setBuffer(this);
    pIn.readto (f);
  }
  else if (pElement.isA(Tags::tag_producing))
    pIn.readto( MetaCategory::ControllerString<Operation>(Operation::metadata,pIn.getAttributes()) );
  else if (pElement.isA(Tags::tag_consuming))
    pIn.readto( MetaCategory::ControllerString<Operation>(Operation::metadata,pIn.getAttributes()) );
  else if (pElement.isA(Tags::tag_item))
    pIn.readto( MetaCategory::ControllerString<Item>(Item::metadata,pIn.getAttributes()) );
  else if (pElement.isA(Tags::tag_minimum) || pElement.isA(Tags::tag_maximum))
    pIn.readto( MetaCategory::ControllerString<Calendar>(Calendar::metadata,pIn.getAttributes()) );
  else if (pElement.isA(Tags::tag_location))
    pIn.readto( MetaCategory::ControllerString<Location>(Location::metadata,pIn.getAttributes()) );
  else if (pElement.isA(Tags::tag_profile)
    || pElement.isA(Tags::tag_bucket_profile))
    pIn.IgnoreElement();
  else
    HasHierarchy<Buffer>::beginElement(pIn, pElement);
}


void Buffer::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_producing))
  {
    Operation *b = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (b) setProducingOperation(b);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_item))
  {
    Item *a = dynamic_cast<Item*>(pIn.getPreviousObject());
    if (a) setItem(a);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_onhand))
  {
    float f = pElement.getFloat();
    setOnHand(f);
  }
  else if (pElement.isA(Tags::tag_minimum))
  {
    CalendarFloat *mincal = 
      dynamic_cast<CalendarFloat*>(pIn.getPreviousObject());
    if (mincal)
      setMinimum(mincal);
    else
    {
      Calendar *c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
      if (!c) 
        throw LogicException("Incorrect object type during read operation");
      throw DataException("Calendar '" + c->getName() +
        "' has invalid type for use as buffer min calendar");
    }
  }
  else if (pElement.isA(Tags::tag_maximum))
  {
    CalendarFloat *maxcal = 
      dynamic_cast<CalendarFloat*>(pIn.getPreviousObject());
    if (maxcal)
      setMaximum(maxcal);
    else
    {
      Calendar *c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
      if (!c) 
        throw LogicException("Incorrect object type during read operation");
      throw DataException("Calendar '" + c->getName() +
        "' has invalid type for use as buffer max calendar");
    }
  }
  else if (pElement.isA(Tags::tag_location))
  {
    Location * d = dynamic_cast<Location*>(pIn.getPreviousObject());
    if (d) setLocation(d);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_consuming))
  {
    Operation *c = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (c) setConsumingOperation(c);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
  {
    Plannable::endElement(pIn, pElement);
    HasDescription::endElement(pIn, pElement);
    HasHierarchy<Buffer>::endElement(pIn, pElement);
  }
}


void Buffer::setMinimum(const CalendarFloat *cal)
{
  // Resetting the same calendar
  if (min_cal == cal) return;

  // Mark as changed
  setChanged();

  // Calendar is already set.
  if(min_cal)
  {
    for(flowplanlist::iterator oo=flowplans.begin(); oo!=flowplans.end(); )
      if (oo->getType() == 3)
      {
        flowplans.erase(&(*oo));
        delete &(*(oo++));
      }
      else ++oo;
  }

  // Null pointer passed
  if (!cal) return;

  // Create timeline structures for every bucket. A new entry is created only
  // when the value changes.
  min_cal = const_cast< CalendarFloat* >(cal);
  float curMin = 0.0f;
  for (Calendar::Bucketlist::const_iterator x = min_cal->getBuckets().begin();
       x != min_cal->getBuckets().end(); ++x)
         if (curMin != min_cal->getValue(x))
    {
      curMin = min_cal->getValue(x);
      flowplanlist::EventMinQuantity *newBucket =
        new flowplanlist::EventMinQuantity((*x)->getStart(), curMin);
      flowplans.insert(newBucket);
    }
}


void Buffer::setMaximum(const CalendarFloat *cal)
{
  // Resetting the same calendar
  if (max_cal == cal) return;

  // Mark as changed
  setChanged();

  // Calendar is already set.
  if(max_cal)
  {
    for(flowplanlist::iterator oo=flowplans.begin(); oo!=flowplans.end(); )
      if (oo->getType() == 4)
      {
        flowplans.erase(&(*oo));
        delete &(*(oo++));
      }
      else ++oo;
  }

  // Null pointer passed
  if (!cal) return;

  // Create timeline structures for every bucket. A new entry is created only
  // when the value changes.
  max_cal = const_cast<CalendarFloat*>(cal);
  float curMax = 0.0f;
  for (Calendar::Bucketlist::const_iterator x = max_cal->getBuckets().begin();
       x != max_cal->getBuckets().end(); ++x)
    if (curMax != max_cal->getValue(x))
    {
      curMax = max_cal->getValue(x);
      flowplanlist::EventMaxQuantity *newBucket =
        new flowplanlist::EventMaxQuantity((*x)->getStart(), curMax);
      flowplans.insert(newBucket);
    }
}


void Buffer::deleteOperationPlans(bool deleteLocked)
{
  // Delete the operationplans
  for(flowlist::iterator i=flows.begin(); i!=flows.end(); ++i)
    OperationPlan::deleteOperationPlans((*i)->getOperation(),deleteLocked);

  // Mark to recompute the problems
  setChanged();
}


Buffer::~Buffer()
{
  // Delete all operationplans.
  // An alternative logic would be to delete only the flowplans for this
  // buffer and leave the rest of the plan untouched. The currently
  // implemented method is way more drastic...
  deleteOperationPlans(true);

  // The Flow objects are automatically deleted by the destructor of the
  // Association list class.

  // Remove the inventory operation
  Operation *invoper = Operation::find(INVENTORY_OPERATION);
  if (invoper) delete invoper;
}


void BufferInfinite::writeElement
  (XMLOutput *o, const XMLtag &tag, mode m) const
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
  Buffer::writeElement(o, tag, NOHEADER);
}



void BufferMinMax::writeElement(XMLOutput *o, const XMLtag &tag, mode m) const
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
  Buffer::writeElement(o, tag, NOHEADER);
}


}

