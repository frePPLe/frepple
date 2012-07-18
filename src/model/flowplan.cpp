/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba                 *
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

DECLARE_EXPORT const MetaCategory* FlowPlan::metadata;


int FlowPlan::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("flowplan", "flowplans");

  // Initialize the Python type
  PythonType& x = FreppleCategory<FlowPlan>::getType();
  x.setName("flowplan");
  x.setDoc("frePPLe flowplan");
  x.supportgetattro();
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT FlowPlan::FlowPlan (OperationPlan *opplan, const Flow *f)
{
  assert(opplan && f);
  fl = const_cast<Flow*>(f);

  // Initialize the Python type
  initType(metadata);

  // Link the flowplan to the operationplan
  oper = opplan;
  nextFlowPlan = NULL;
  if (opplan->firstflowplan)
  {
    // Append to the end
    FlowPlan *c = opplan->firstflowplan;
    while (c->nextFlowPlan) c = c->nextFlowPlan;
    c->nextFlowPlan = this;
  }
  else
    // First in the list
    opplan->firstflowplan = this;

  // Compute the flowplan quantity
  fl->getBuffer()->flowplans.insert(
    this,
    fl->getFlowplanQuantity(this),
    fl->getFlowplanDate(this)
  );

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  fl->getBuffer()->setChanged();
  fl->getOperation()->setChanged();
}


DECLARE_EXPORT void FlowPlan::update()
{
  // Update the timeline data structure
  fl->getBuffer()->flowplans.update(
    this,
    fl->getFlowplanQuantity(this),
    fl->getFlowplanDate(this)
  );

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  fl->getBuffer()->setChanged();
  fl->getOperation()->setChanged();
}


DECLARE_EXPORT void FlowPlan::setFlow(const Flow* newfl)
{
  // No change
  if (newfl == fl) return;

  // Verify the data
  if (!newfl) throw LogicException("Can't switch to NULL flow");

  // Remove from the old buffer, if there is one
  if (fl)
  {
    if (fl->getOperation() != newfl->getOperation())
      throw LogicException("Only switching to a flow on the same operation is allowed");
    fl->getBuffer()->flowplans.erase(this);
    fl->getBuffer()->setChanged();
  }

  // Insert in the new buffer
  fl = newfl;
  fl->getBuffer()->flowplans.insert(
    this,
    fl->getFlowplanQuantity(this),
    fl->getFlowplanDate(this)
  );
  fl->getBuffer()->setChanged();
  fl->getOperation()->setChanged();
}


// Remember that this method only superficially looks like a normal
// writeElement() method.
DECLARE_EXPORT void FlowPlan::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  o->BeginObject(tag);
  o->writeElement(Tags::tag_date, getDate());
  o->writeElement(Tags::tag_quantity, getQuantity());
  o->writeElement(Tags::tag_onhand, getOnhand());
  o->writeElement(Tags::tag_minimum, getMin());
  o->writeElement(Tags::tag_maximum, getMax());
  if (!dynamic_cast<OperationPlan*>(o->getCurrentObject()))
    o->writeElement(Tags::tag_operationplan, &*getOperationPlan());

  // Write pegging info
  if (o->getContentType() == XMLOutput::PLANDETAIL)
  {
    // Write the upstream pegging
    PeggingIterator k(this, false);
    if (k) --k;
    for (; k; --k)
    {
      o->BeginObject(Tags::tag_pegging, Tags::tag_level, k.getLevel());
      o->writeElement(Tags::tag_quantity, k.getQuantityDemand());
      o->writeElement(Tags::tag_factor, k.getFactor());
      if (!k.getPegged()) o->writeElement(Tags::tag_id, "unpegged");
      o->writeElement(Tags::tag_buffer, Tags::tag_name, k.getBuffer()->getName());
      if (k.getConsumingOperationplan())
        o->writeElement(Tags::tag_consuming,
            Tags::tag_id, k.getConsumingOperationplan()->getIdentifier(),
            Tags::tag_operation, k.getConsumingOperationplan()->getOperation()->getName());
      if (k.getProducingOperationplan())
        o->writeElement(Tags::tag_producing,
            Tags::tag_id, k.getProducingOperationplan()->getIdentifier(),
            Tags::tag_operation, k.getProducingOperationplan()->getOperation()->getName());
      o->writeElement(Tags::tag_dates, DateRange(k.getProducingDate(),k.getConsumingDate()));
      o->EndObject(Tags::tag_pegging);
    }

    // Write the downstream pegging
    PeggingIterator l(this, true);
    if (l) ++l;
    for (; l; ++l)
    {
      o->BeginObject(Tags::tag_pegging, Tags::tag_level, l.getLevel());
      o->writeElement(Tags::tag_quantity, l.getQuantityDemand());
      o->writeElement(Tags::tag_factor, l.getFactor());
      if (!l.getPegged()) o->writeElement(Tags::tag_id, "unpegged");
      o->writeElement(Tags::tag_buffer, Tags::tag_name, l.getBuffer()->getName());
      if (l.getConsumingOperationplan())
        o->writeElement(Tags::tag_consuming,
            Tags::tag_id, l.getConsumingOperationplan()->getIdentifier(),
            Tags::tag_operation, l.getConsumingOperationplan()->getOperation()->getName());
      if (l.getProducingOperationplan())
        o->writeElement(Tags::tag_producing,
            Tags::tag_id, l.getProducingOperationplan()->getIdentifier(),
            Tags::tag_operation, l.getProducingOperationplan()->getOperation()->getName());
      o->writeElement(Tags::tag_dates, DateRange(l.getProducingDate(),l.getConsumingDate()));
      o->EndObject(Tags::tag_pegging);
    }
  }

  o->EndObject(tag);
}


PyObject* FlowPlan::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_operationplan))
    return PythonObject(getOperationPlan());
  if (attr.isA(Tags::tag_quantity))
    return PythonObject(getQuantity());
  if (attr.isA(Tags::tag_flow))
    return PythonObject(getFlow());
  if (attr.isA(Tags::tag_date))
    return PythonObject(getDate());
  if (attr.isA(Tags::tag_onhand))
    return PythonObject(getOnhand());
  if (attr.isA(Tags::tag_buffer)) // Convenient shortcut
    return PythonObject(getFlow()->getBuffer());
  if (attr.isA(Tags::tag_operation)) // Convenient shortcut
    return PythonObject(getFlow()->getOperation());
  return NULL;
}


int FlowPlanIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<FlowPlanIterator>::getType();
  x.setName("flowplanIterator");
  x.setDoc("frePPLe iterator for flowplan");
  x.supportiter();
  return x.typeReady();
}


PyObject* FlowPlanIterator::iternext()
{
  FlowPlan* fl;
  if (buffer_or_opplan)
  {
    // Skip uninteresting entries
    while (*bufiter != buf->getFlowPlans().end() && (*bufiter)->getQuantity()==0.0)
      ++(*bufiter);
    if (*bufiter == buf->getFlowPlans().end()) return NULL;
    fl = const_cast<FlowPlan*>(static_cast<const FlowPlan*>(&*((*bufiter)++)));
  }
  else
  {
    // Skip uninteresting entries
    while (*opplaniter != opplan->endFlowPlans() && (*opplaniter)->getQuantity()==0.0)
      ++(*opplaniter);
    if (*opplaniter == opplan->endFlowPlans()) return NULL;
    fl = static_cast<FlowPlan*>(&*((*opplaniter)++));
  }
  Py_INCREF(fl);
  return const_cast<FlowPlan*>(fl);
}

} // end namespace
