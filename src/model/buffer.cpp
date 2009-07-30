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
#include <math.h>

// This is the name used for the dummy operation used to represent the
// inventory.
#define INVENTORY_OPERATION "Inventory of buffer '" + string(getName()) + "'"

// This is the name used for the dummy operation used to represent procurements
#define PROCURE_OPERATION "Procure for buffer '" + string(getName()) + "'"

namespace frepple
{

template<class Buffer> DECLARE_EXPORT Tree utils::HasName<Buffer>::st;


DECLARE_EXPORT void Buffer::setOnHand(double f)
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
    fl = const_cast<Flow*>(&*(o->getFlows().begin()));

  // Check valid pointers
  if (!fl || !o)
    throw LogicException("Failed creating inventory operation for '"
        + getName() + "'");

  // Make sure the sign of the flow is correct: +1 or -1.
  fl->setQuantity(f>=0.0 ? 1.0 : -1.0);

  // Create a dummy operationplan on the inventory operation
  OperationPlan::iterator i(o);
  if (i == OperationPlan::end())
  {
    // No operationplan exists yet
    OperationPlan *opplan = o->createOperationPlan(
      fabs(f), Date::infinitePast, Date::infinitePast);
    opplan->setLocked(true);
    opplan->initialize();
  }
  else
  {
    // Update the existing operationplan
    i->setLocked(false);
    i->setQuantity(fabs(f));
    i->setLocked(true);
  }
  setChanged();
}


DECLARE_EXPORT double Buffer::getOnHand(Date d) const
{
  double tmp(0.0);
  for (flowplanlist::const_iterator oo=flowplans.begin();
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


DECLARE_EXPORT double Buffer::getOnHand(Date d1, Date d2, bool min) const
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
  for (flowplanlist::const_iterator oo=flowplans.begin(); true; ++oo)
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


DECLARE_EXPORT void Buffer::writeElement(XMLOutput *o, const Keyword &tag, mode m) const
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
  o->writeElement(Tags::tag_item, it);
  o->writeElement(Tags::tag_location, loc);
  Plannable::writeElement(o, tag);

  // Flows
  if (!flows.empty())
  {
    o->BeginObject (Tags::tag_flows);
    for (flowlist::const_iterator i = flows.begin(); i != flows.end(); ++i)
      // We use the FULL mode, to force the flows being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_flow, &*i, FULL);
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

  // Minimum and maximum inventory targets, carrying cost
  o->writeElement(Tags::tag_minimum, min_cal);
  o->writeElement(Tags::tag_maximum, max_cal);
  if (getCarryingCost()!= 0.0) 
    o->writeElement(Tags::tag_carrying_cost, getCarryingCost());
  
  // Write extra plan information
  i = flowplans.begin();
  if ((o->getContentType() == XMLOutput::PLAN
      || o->getContentType() == XMLOutput::PLANDETAIL) && i!=flowplans.end())
  {
    o->BeginObject(Tags::tag_flowplans);
    for (; i!=flowplans.end(); ++i)
      if (i->getType()==1)
        dynamic_cast<const FlowPlan*>(&*i)->writeElement(o, Tags::tag_flowplan);
    o->EndObject(Tags::tag_flowplans);
  }

  // Ending tag
  o->EndObject(tag);
}


DECLARE_EXPORT void Buffer::beginElement (XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_flow)
      && pIn.getParentElement().first.isA(Tags::tag_flows))
  {
    Flow *f =
      dynamic_cast<Flow*>(MetaCategory::ControllerDefault(Flow::metadata,pIn.getAttributes()));
    if (f) f->setBuffer(this);
    pIn.readto (f);
  }
  else if (pAttr.isA(Tags::tag_producing))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_item))
    pIn.readto( Item::reader(Item::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_minimum) || pAttr.isA(Tags::tag_maximum))
    pIn.readto( Calendar::reader(Calendar::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_location))
    pIn.readto( Location::reader(Location::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_flowplans))
    pIn.IgnoreElement();
  else
    HasHierarchy<Buffer>::beginElement(pIn, pAttr);
}


DECLARE_EXPORT void Buffer::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_producing))
  {
    Operation *b = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (b) setProducingOperation(b);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_item))
  {
    Item *a = dynamic_cast<Item*>(pIn.getPreviousObject());
    if (a) setItem(a);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_onhand))
    setOnHand(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_minimum))
  {
    CalendarDouble *mincal =
      dynamic_cast<CalendarDouble*>(pIn.getPreviousObject());
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
  else if (pAttr.isA(Tags::tag_maximum))
  {
    CalendarDouble *maxcal =
      dynamic_cast<CalendarDouble*>(pIn.getPreviousObject());
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
  else if (pAttr.isA(Tags::tag_location))
  {
    Location * d = dynamic_cast<Location*>(pIn.getPreviousObject());
    if (d) setLocation(d);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_carrying_cost))
    setCarryingCost(pElement.getDouble());
  else
  {
    Plannable::endElement(pIn, pAttr, pElement);
    HasDescription::endElement(pIn, pAttr, pElement);
    HasHierarchy<Buffer>::endElement(pIn, pAttr, pElement);
  }
}


DECLARE_EXPORT void Buffer::setMinimum(CalendarDouble *cal)
{
  // Resetting the same calendar
  if (min_cal == cal) return;

  // Mark as changed
  setChanged();

  // Calendar is already set: delete previous events.
  if (min_cal)
  {
    for (flowplanlist::iterator oo=flowplans.begin(); oo!=flowplans.end(); )
      if (oo->getType() == 3)
      {
        flowplans.erase(&(*oo));
        delete &(*(oo++));
      }
      else ++oo;
  }

  // Null pointer passed
  if (!cal) return;

  // Create timeline structures for every event. A new entry is created only
  // when the value changes.
  min_cal = const_cast< CalendarDouble* >(cal);
  double curMin = 0.0;
  for (CalendarDouble::EventIterator x(min_cal); x.getDate()<Date::infiniteFuture; ++x)
    if (curMin != x.getValue())
    {
      curMin = x.getValue();
      flowplanlist::EventMinQuantity *newBucket =
        new flowplanlist::EventMinQuantity(x.getDate(), curMin);
      flowplans.insert(newBucket);
    }
}


DECLARE_EXPORT void Buffer::setMaximum(CalendarDouble *cal)
{
  // Resetting the same calendar
  if (max_cal == cal) return;

  // Mark as changed
  setChanged();

  // Calendar is already set: delete previous events.
  if (max_cal)
  {
    for (flowplanlist::iterator oo=flowplans.begin(); oo!=flowplans.end(); )
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
  max_cal = const_cast<CalendarDouble*>(cal);
  double curMax = 0.0;
  for (CalendarDouble::EventIterator x(min_cal); x.getDate()<Date::infiniteFuture; ++x)
    if (curMax != x.getValue())
    {
      curMax = x.getValue();
      flowplanlist::EventMaxQuantity *newBucket =
        new flowplanlist::EventMaxQuantity(x.getDate(), curMax);
      flowplans.insert(newBucket);
    }
}


DECLARE_EXPORT void Buffer::deleteOperationPlans(bool deleteLocked)
{
  // Delete the operationplans
  for (flowlist::iterator i=flows.begin(); i!=flows.end(); ++i)
    OperationPlan::deleteOperationPlans(i->getOperation(),deleteLocked);

  // Mark to recompute the problems
  setChanged();
}


DECLARE_EXPORT Buffer::~Buffer()
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


DECLARE_EXPORT void Buffer::followPegging
  (PeggingIterator& iter, FlowPlan* curflowplan, short nextlevel, double curqty, double curfactor)
{

  double peggedQty(0);
  Buffer::flowplanlist::const_iterator f = getFlowPlans().begin(curflowplan);

  if (curflowplan->getQuantity() < -ROUNDING_ERROR && !iter.isDownstream())
  {
    // CASE 1:
    // This is a flowplan consuming from a buffer. Navigating upstream means
    // finding the flowplans producing this consumed material.
    double endQty = f->getCumulativeConsumed();
    double startQty = endQty + f->getQuantity();
    if (f->getCumulativeProduced() <= startQty)
    {
      // CASE 1A: Not produced enough yet: move forward
      while (f!=getFlowPlans().end()
          && f->getCumulativeProduced() <= startQty) ++f;
      while (f!=getFlowPlans().end()
          && ( (f->getQuantity()<=0 && f->getCumulativeProduced() < endQty)
              || (f->getQuantity()>0
                  && f->getCumulativeProduced()-f->getQuantity() < endQty))
            )
      {
        if (f->getQuantity() > ROUNDING_ERROR)
        {
          double newqty = f->getQuantity();
          if (f->getCumulativeProduced()-f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeProduced()-f->getQuantity());
          if (f->getCumulativeProduced() > endQty)
            newqty -= f->getCumulativeProduced() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          iter.updateStack(nextlevel,
            -curqty*newqty/curflowplan->getQuantity(),
            curfactor*newqty/f->getQuantity(),
            curflowplan, x);
        }
        ++f;
      }
    }
    else
    {
      // CASE 1B: Produced too much already: move backward
      while ( f!=getFlowPlans().end()
          && ((f->getQuantity()<=0 && f->getCumulativeProduced() > endQty)
              || (f->getQuantity()>0
                  && f->getCumulativeProduced()-f->getQuantity() > endQty))) --f;
      while (f!=getFlowPlans().end() && f->getCumulativeProduced() > startQty)
      {
        if (f->getQuantity() > ROUNDING_ERROR)
        {
          double newqty = f->getQuantity();
          if (f->getCumulativeProduced()-f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeProduced()-f->getQuantity());
          if (f->getCumulativeProduced() > endQty)
            newqty -= f->getCumulativeProduced() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          iter.updateStack(nextlevel,
              -curqty*newqty/curflowplan->getQuantity(),
              curfactor*newqty/f->getQuantity(),
              curflowplan, x);
        }
        --f;
      }
    }
    if (peggedQty < endQty - startQty - ROUNDING_ERROR)
      // Unproduced material (i.e. material that is consumed but never
      // produced) is handled with a special entry on the stack.
      iter.updateStack(nextlevel,
          curqty*(peggedQty - endQty + startQty)/curflowplan->getQuantity(),
          curfactor,
          curflowplan,
          NULL,
          false);
    return;
  }

  if (curflowplan->getQuantity() > ROUNDING_ERROR && iter.isDownstream())
  {
    // CASE 2:
    // This is a flowplan producing in a buffer. Navigating downstream means
    // finding the flowplans consuming this produced material.
    double endQty = f->getCumulativeProduced();
    double startQty = endQty - f->getQuantity();
    if (f->getCumulativeConsumed() <= startQty)
    {
      // CASE 2A: Not consumed enough yet: move forward
      while (f!=getFlowPlans().end()
          && f->getCumulativeConsumed() <= startQty) ++f;
      while (f!=getFlowPlans().end()
          && ( (f->getQuantity()<=0
              && f->getCumulativeConsumed()+f->getQuantity() < endQty)
              || (f->getQuantity()>0 && f->getCumulativeConsumed() < endQty))
            )
      {
        if (f->getQuantity() < -ROUNDING_ERROR)
        {
          double newqty = - f->getQuantity();
          if (f->getCumulativeConsumed()+f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeConsumed()+f->getQuantity());
          if (f->getCumulativeConsumed() > endQty)
            newqty -= f->getCumulativeConsumed() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          iter.updateStack(nextlevel,
            curqty*newqty/curflowplan->getQuantity(),
            -curfactor*newqty/f->getQuantity(),
            x, curflowplan);
        }
        ++f;
      }
    }
    else
    {
      // CASE 2B: Consumed too much already: move backward
      while ( f!=getFlowPlans().end()
          && ((f->getQuantity()<=0 && f->getCumulativeConsumed()+f->getQuantity() < endQty)
              || (f->getQuantity()>0 && f->getCumulativeConsumed() < endQty))) --f;
      while (f!=getFlowPlans().end() && f->getCumulativeConsumed() > startQty)
      {
        if (f->getQuantity() < -ROUNDING_ERROR)
        {
          double newqty = - f->getQuantity();
          if (f->getCumulativeConsumed()+f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeConsumed()+f->getQuantity());
          if (f->getCumulativeConsumed() > endQty)
            newqty -= f->getCumulativeConsumed() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          iter.updateStack(nextlevel,
            curqty*newqty/curflowplan->getQuantity(),
            -curfactor*newqty/f->getQuantity(),
            x, curflowplan);
        }
        --f;
      }
    }
    if (peggedQty < endQty - startQty)
      // Unpegged material (i.e. material that is produced but never consumed)
      // is handled with a special entry on the stack.
      iter.updateStack(nextlevel,
        curqty*(endQty - startQty - peggedQty)/curflowplan->getQuantity(),
        curfactor,
        NULL, curflowplan,
        false);
    return;
  }
}


DECLARE_EXPORT void BufferInfinite::writeElement
(XMLOutput *o, const Keyword &tag, mode m) const
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

  // Write the fields and an ending tag
  Buffer::writeElement(o, tag, NOHEADER);
}


DECLARE_EXPORT void BufferProcure::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_leadtime))
    setLeadtime(pElement.getTimeperiod());
  else if (pAttr.isA(Tags::tag_fence))
    setFence(pElement.getTimeperiod());
  else if (pAttr.isA(Tags::tag_size_maximum))
    setSizeMaximum(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_size_minimum))
    setSizeMinimum(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_size_multiple))
    setSizeMultiple(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_mininterval))
    setMinimumInterval(pElement.getTimeperiod());
  else if (pAttr.isA(Tags::tag_maxinterval))
    setMaximumInterval(pElement.getTimeperiod());
  else if (pAttr.isA(Tags::tag_mininventory))
    setMinimumInventory(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_maxinventory))
    setMaximumInventory(pElement.getDouble());
  else
    Buffer::endElement(pIn, pAttr, pElement);
}


DECLARE_EXPORT void BufferProcure::writeElement(XMLOutput *o, const Keyword &tag, mode m) const
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

  // Write the extra fields
  if (leadtime) o->writeElement(Tags::tag_leadtime, leadtime);
  if (fence) o->writeElement(Tags::tag_fence, fence);
  if (size_maximum != DBL_MAX) o->writeElement(Tags::tag_size_maximum, size_maximum);
  if (size_minimum) o->writeElement(Tags::tag_size_minimum, size_minimum);
  if (size_multiple) o->writeElement(Tags::tag_size_multiple, size_multiple);
  if (min_interval) o->writeElement(Tags::tag_mininterval, min_interval);
  if (max_interval) o->writeElement(Tags::tag_maxinterval, max_interval);
  if (min_inventory) o->writeElement(Tags::tag_mininventory, min_inventory);
  if (max_inventory) o->writeElement(Tags::tag_maxinventory, max_inventory);

  // Write the fields and an ending tag
  Buffer::writeElement(o, tag, NOHEADER);
}


DECLARE_EXPORT Operation* BufferProcure::getOperation() const
{
  if (!oper)
  {
    Operation *o = Operation::find(PROCURE_OPERATION);
    if (!o)
    {
      // Create the operation if it didn't exist yet
      o = new OperationFixedTime(PROCURE_OPERATION);
      static_cast<OperationFixedTime*>(o)->setDuration(leadtime);
      // Ideally we would like to hide the procurement operation itself.
      // But in that case we need a different way to show the procurements
      // to the outside world.
      // o->setHidden(true);
      Operation::add(o);  // No need to check again for existance
      new FlowEnd(o, const_cast<BufferProcure*>(this), 1);
    }
    const_cast<BufferProcure*>(this)->oper = o;
  }
  return oper;
}


DECLARE_EXPORT PyObject* PythonBuffer::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (attr.isA(Tags::tag_description))
    return PythonObject(obj->getDescription());
  if (attr.isA(Tags::tag_category))
    return PythonObject(obj->getCategory());
  if (attr.isA(Tags::tag_subcategory))
    return PythonObject(obj->getSubCategory());
  if (attr.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (attr.isA(Tags::tag_location))
    return PythonObject(obj->getLocation());
  if (attr.isA(Tags::tag_producing))
    return PythonObject(obj->getProducingOperation());
  if (attr.isA(Tags::tag_item))
    return PythonObject(obj->getItem());
  if (attr.isA(Tags::tag_onhand))
    return PythonObject(obj->getOnHand());
  if (attr.isA(Tags::tag_flowplans))
    return new PythonFlowPlanIterator(obj);
  if (attr.isA(Tags::tag_maximum))
    return PythonObject(obj->getMaximum());
  if (attr.isA(Tags::tag_minimum))
    return PythonObject(obj->getMinimum());
  if (attr.isA(Tags::tag_carrying_cost))
    return PythonObject(obj->getCarryingCost());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  if (attr.isA(Tags::tag_flows))
    return new PythonFlowIterator(obj);
  if (attr.isA(Tags::tag_level))
    return PythonObject(obj->getLevel());
  if (attr.isA(Tags::tag_cluster))
    return PythonObject(obj->getCluster());
  // @todo support member iteration for buffer, res, dem, item, ...
  // PythonBufferIterator becomes an abstract class: defines the pytype and an abstract iternext.
  // 2 subclasses then implement it: an iterator over all buffers, and another one over all members.
	return NULL;
}


DECLARE_EXPORT int PythonBuffer::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    obj->setName(field.getString());
  else if (attr.isA(Tags::tag_description))
    obj->setDescription(field.getString());
  else if (attr.isA(Tags::tag_category))
    obj->setCategory(field.getString());
  else if (attr.isA(Tags::tag_subcategory))
    obj->setSubCategory(field.getString());
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(PythonBuffer::getType()))
    {
      PyErr_SetString(PythonDataException, "buffer owner must be of type buffer");
      return -1;
    }
    Buffer* y = static_cast<PythonBuffer*>(static_cast<PyObject*>(field))->obj;
    obj->setOwner(y);
  }
  else if (attr.isA(Tags::tag_location))
  {
    if (!field.check(PythonLocation::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer location must be of type location");
      return -1;
    }
    Location* y = static_cast<PythonLocation*>(static_cast<PyObject*>(field))->obj;
    obj->setLocation(y);
  }
  else if (attr.isA(Tags::tag_item))
  {
    if (!field.check(PythonItem::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer item must be of type item");
      return -1;
    }
    Item* y = static_cast<PythonItem*>(static_cast<PyObject*>(field))->obj;
    obj->setItem(y);
  }
  else if (attr.isA(Tags::tag_maximum))
  {
    if (!field.check(PythonCalendarDouble::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer maximum must be of type calendar_double");
      return -1;
    }
    CalendarDouble* y = static_cast<PythonCalendarDouble*>(static_cast<PyObject*>(field))->obj;
    obj->setMaximum(y);
  }
  else if (attr.isA(Tags::tag_minimum))
  {
    if (!field.check(PythonCalendarDouble::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer minimum must be of type calendar_double");
      return -1;
    }
    CalendarDouble* y = static_cast<PythonCalendarDouble*>(static_cast<PyObject*>(field))->obj;
    obj->setMinimum(y);
  }
  else if (attr.isA(Tags::tag_onhand))
    obj->setOnHand(field.getDouble());
  else if (attr.isA(Tags::tag_carrying_cost))
    obj->setCarryingCost(field.getDouble());
  else if (attr.isA(Tags::tag_producing))
  {
    if (!field.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "buffer producing must be of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(field))->obj;
    obj->setProducingOperation(y);
  }
  else if (attr.isA(Tags::tag_hidden))
    obj->setHidden(field.getBool());
  else
    return -1;  // Error
  return 0;  // OK
}


DECLARE_EXPORT PyObject* PythonBufferDefault::getattro(const Attribute& attr)
{
  return PythonBuffer(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonBufferDefault::setattro(const Attribute& attr, const PythonObject& field)
{
  // @todo avoid constructing a PythonBuffer object to call the base class
  // This is currently not really feasible (no casting between the classes is possible)
  // When the XML and Python framework will be unified, this will be solved: we'll basically
  // have a single call to the getAttribute() method of the default buffer, which can call
  // the getAttribute function of the parent class.
  return PythonBuffer(obj).setattro(attr, field);  
}


DECLARE_EXPORT PyObject* PythonBufferInfinite::getattro(const Attribute& attr)
{
  return PythonBuffer(obj).getattro(attr);
}


DECLARE_EXPORT int PythonBufferInfinite::setattro(const Attribute& attr, const PythonObject& field)
{
  return PythonBuffer(obj).setattro(attr, field);
}


DECLARE_EXPORT PyObject* PythonBufferProcure::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_leadtime))
    return PythonObject(obj->getLeadtime());
  if (attr.isA(Tags::tag_mininventory))
    return PythonObject(obj->getMinimumInventory());
  if (attr.isA(Tags::tag_maxinventory))
    return PythonObject(obj->getMaximumInventory());
  if (attr.isA(Tags::tag_mininterval))
    return PythonObject(obj->getMinimumInterval());
  if (attr.isA(Tags::tag_maxinterval))
    return PythonObject(obj->getMaximumInterval());
  if (attr.isA(Tags::tag_fence))
    return PythonObject(obj->getFence());
  if (attr.isA(Tags::tag_size_minimum))
    return PythonObject(obj->getSizeMinimum());
  if (attr.isA(Tags::tag_size_multiple))
    return PythonObject(obj->getSizeMultiple());
  if (attr.isA(Tags::tag_size_maximum))
    return PythonObject(obj->getSizeMaximum());
  return PythonBuffer(obj).getattro(attr);
}


DECLARE_EXPORT int PythonBufferProcure::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_leadtime))
    obj->setLeadtime(field.getTimeperiod());
  else if (attr.isA(Tags::tag_mininventory))
    obj->setMinimumInventory(field.getDouble());
  else if (attr.isA(Tags::tag_maxinventory))
    obj->setMaximumInventory(field.getDouble());
  else if (attr.isA(Tags::tag_mininterval))
    obj->setMinimumInterval(field.getTimeperiod());
  else if (attr.isA(Tags::tag_maxinterval))
    obj->setMaximumInterval(field.getTimeperiod());
  else if (attr.isA(Tags::tag_size_minimum))
    obj->setSizeMinimum(field.getDouble());
  else if (attr.isA(Tags::tag_size_multiple))
    obj->setSizeMultiple(field.getDouble());
  else if (attr.isA(Tags::tag_size_maximum))
    obj->setSizeMaximum(field.getDouble());
  else if (attr.isA(Tags::tag_fence))
    obj->setFence(field.getTimeperiod());
  else
    return PythonBuffer(obj).setattro(attr, field);
  return 0;
}

} // end namespace
