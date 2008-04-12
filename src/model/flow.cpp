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


DECLARE_EXPORT void Flow::validate(Action action)
{
  // Catch null operation and buffer pointers
  Operation* oper = getOperation();
  Buffer* buf = getBuffer();
  if (!oper || !buf)
  {
    // This flow is not a valid one since it misses essential information
    delete this;
    if (!oper && !buf)
      throw DataException("Missing operation and buffer on a flow");
    else if (!oper)
      throw DataException("Missing operation on a flow with buffer '"
          + buf->getName() + "'");
    else
      throw DataException("Missing buffer on a flow with operation '"
          + oper->getName() + "'");
  }

  // Check if a flow with 1) identical buffer, 2) identical operation and 
  // 3) overlapping effectivity dates already exists
  Operation::flowlist::const_iterator i = oper->getFlows().begin();
  for (; i != oper->getFlows().end(); ++i)
    if (i->getBuffer() == buf 
      && i->getEffective().overlap(getEffective()) 
      && &*i != this) 
        break;

  // Apply the appropriate action
  switch (action)
  {
    case ADD:
      if (i != oper->getFlows().end())
      {
        delete this;
        throw DataException("Flow of '" + oper->getName() + "' and '" +
            buf->getName() + "' already exists.");
      }
      break;
    case CHANGE:
      delete this;
      throw DataException("Can't update a flow");
    case ADD_CHANGE:
      // ADD is handled in the code after the switch statement
      if (i == oper->getFlows().end()) break;
      delete this;
      throw DataException("Can't update a flow");
    case REMOVE:
      // Delete the temporary flow object
      delete this;
      // Nothing to delete
      if (i == oper->getFlows().end())
        throw DataException("Can't remove nonexistent flow of '"
            + oper->getName() + "' and '" + buf->getName() + "'");
      // Delete
      delete &*i;
 }

  // Attach to buffers higher up in the hierarchy
  // Note that the owner can create more loads if it has an owner too.
  if (buf->hasOwner() && action!=REMOVE) new Flow(oper, buf->getOwner(), quantity);

  // Set a flag to make sure the level computation is triggered again
  HasLevel::triggerLazyRecomputation();
}


DECLARE_EXPORT Flow::~Flow()
{
  // Set a flag to make sure the level computation is triggered again
  HasLevel::triggerLazyRecomputation();

  // Delete existing flowplans
  if (getOperation() && getBuffer())
  {
    // Loop over operationplans
	  for(OperationPlan::iterator i(getOperation()); i != OperationPlan::end(); ++i)
      // Loop over flowplans
      for(OperationPlan::FlowPlanIterator j = i->beginFlowPlans(); j != i->endFlowPlans(); )
        if (j->getFlow() == this) j.deleteFlowPlan();
        else ++j;
  }

  // Delete the flow from the operation and the buffer
  if (getOperation()) getOperation()->flowdata.erase(this);
  if (getBuffer()) getBuffer()->flows.erase(this);
}


DECLARE_EXPORT void Flow::writeElement (XMLOutput *o, const Keyword& tag, mode m) const
{
  // If the flow has already been saved, no need to repeat it again
  // A 'reference' to a flow is not useful to be saved.
  if (m == REFERENCE) return;
  assert(m != NOHEADER);

  // Write the header
  o->BeginObject(tag, Tags::tag_type, getType().type);

  // If the flow is defined inside of an operation tag, we don't need to save
  // the operation. Otherwise we do save it...
  if (!dynamic_cast<Operation*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_operation, getOperation());

  // If the flow is defined inside of an buffer tag, we don't need to save
  // the buffer. Otherwise we do save it...
  if (!dynamic_cast<Buffer*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_buffer, getBuffer());

  // Write the quantity
  o->writeElement(Tags::tag_quantity, quantity);

  // Write the effective daterange
  if (getEffective().getStart() != Date::infinitePast)
    o->writeElement(Tags::tag_effective_start, getEffective().getStart());
  if (getEffective().getEnd() != Date::infiniteFuture)
    o->writeElement(Tags::tag_effective_end, getEffective().getEnd());

  // End of flow object
  o->EndObject(tag);
}


DECLARE_EXPORT void Flow::beginElement (XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_buffer))
    pIn.readto( Buffer::reader(Buffer::metadata,pIn) );
  else if (pAttr.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn) );
}


DECLARE_EXPORT void Flow::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA (Tags::tag_buffer))
  {
    Buffer * b = dynamic_cast<Buffer*>(pIn.getPreviousObject());
    if (b) setBuffer(b);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA (Tags::tag_operation))
  {
    Operation * o = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (o) setOperation(o);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_quantity))
    setQuantity(pElement.getDouble());
  else if (pAttr.isA(Tags::tag_action))
  {
    delete static_cast<Action*>(pIn.getUserArea());
    pIn.setUserArea(
      new Action(MetaClass::decodeAction(pElement.getString().c_str()))
    );
  }
  else if (pAttr.isA(Tags::tag_effective_end))
    setEffectiveEnd(pElement.getDate());
  else if (pAttr.isA(Tags::tag_effective_start))
    setEffectiveStart(pElement.getDate());
  else if (pIn.isObjectEnd())
  {
    // The flow data are now all read in. See if it makes sense now...
    Action a = pIn.getUserArea() ?
      *static_cast<Action*>(pIn.getUserArea()) :
      ADD_CHANGE;
    delete static_cast<Action*>(pIn.getUserArea());
    validate(a);
  }
}


DECLARE_EXPORT void FlowEnd::writeElement
(XMLOutput *o, const Keyword& tag, mode m) const
{
  // If the flow has already been saved, no need to repeat it again
  // A 'reference' to a flow is not useful to be saved.
  if (m == REFERENCE) return;
  assert(m != NOHEADER);

  // Write the header
  o->BeginObject(tag, Tags::tag_type, getType().type);

  // If the flow is defined inside of an operation tag, we don't need to save
  // the operation. Otherwise we do save it...
  if (!dynamic_cast<Operation*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_operation, getOperation());

  // If the flow is defined inside of an buffer tag, we don't need to save
  // the buffer. Otherwise we do save it...
  if (!dynamic_cast<Buffer*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_buffer, getBuffer());

  // Write the quantity
  o->writeElement(Tags::tag_quantity, getQuantity());

  // End of flow object
  o->EndObject(tag);
}


}
