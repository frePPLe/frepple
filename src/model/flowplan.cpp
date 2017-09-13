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

  const MetaClass* FlowPlan::metadata;
  const MetaCategory* FlowPlan::metacategory;


int FlowPlan::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<FlowPlan>("flowplan", "flowplans", reader);
  metadata = MetaClass::registerClass<FlowPlan>(
    "flowplan", "flowplan"
    );
  registerFields<FlowPlan>(const_cast<MetaClass*>(metadata));

  // Initialize the Python type
  PythonType& x = FreppleCategory<FlowPlan>::getPythonType();
  x.setName("flowplan");
  x.setDoc("frePPLe flowplan");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


FlowPlan::FlowPlan (OperationPlan *opplan, const Flow *f)
  : fl(const_cast<Flow*>(f)), oper(opplan)
{
  assert(opplan && f);

  // Initialize the Python type
  initType(metadata);

  // Link the flowplan to the operationplan
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


string FlowPlan::getStatus() const
{
  if (flags & STATUS_CONFIRMED)
    return "confirmed";
  else
    return "proposed";
}

void FlowPlan::setStatus(const string& s)
{
  if (!getOperationPlan()->getLocked() && s=="confirmed")
    throw DataException("OperationPlanMaterial locked while OperationPlan is not");
  if (s == "confirmed")
  {
    flags |= STATUS_CONFIRMED;
  }
  else if (s == "proposed")
  {
    flags &= ~STATUS_CONFIRMED;
  }
  else
    throw DataException("invalid operationplanmaterial status:" + s);
}

void FlowPlan::update()
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


void FlowPlan::setFlow(Flow* newfl)
{
  // No change
  if (newfl == fl) return;

  // Verify the data
  if (!newfl) throw DataException("Can't switch to nullptr flow");

  // Remove from the old buffer, if there is one
  if (fl)
  {
    if (fl->getOperation() != newfl->getOperation())
      throw DataException("Only switching to a flow on the same operation is allowed");
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


void FlowPlan::setItem(Item* newItem)
{
  // Verify the data
  if (!newItem)
    throw DataException("Can't switch to nullptr flow");

  if (fl && fl->getBuffer())
  {
    if (newItem == fl->getBuffer()->getItem())
      // No change
      return;
    else
      // Already set
      throw DataException("Item can be set only once on a flowplan");
  }

  // We are not expecting to use this method in this way...
  throw LogicException("Not implemented");
}


int FlowPlanIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<FlowPlanIterator>::getPythonType();
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
    if (*bufiter == buf->getFlowPlans().end()) return nullptr;
    fl = const_cast<FlowPlan*>(static_cast<const FlowPlan*>(&*((*bufiter)++)));
  }
  else
  {
    // Skip uninteresting entries
    while (*opplaniter != opplan->endFlowPlans() && (*opplaniter)->getQuantity()==0.0)
      ++(*opplaniter);
    if (*opplaniter == opplan->endFlowPlans()) return nullptr;
    fl = static_cast<FlowPlan*>(&*((*opplaniter)++));
  }
  Py_INCREF(fl);
  return const_cast<FlowPlan*>(fl);
}


Object* FlowPlan::reader(
  const MetaClass* cat, const DataValueDict& in, CommandManager* mgr
)
{
  // Pick up the operationplan attribute. An error is reported if it's missing.
  const DataValue* opplanElement = in.get(Tags::operationplan);
  if (!opplanElement)
    throw DataException("Missing operationplan field");
  Object* opplanobject = opplanElement->getObject();
  if (!opplanobject || opplanobject->getType() != *OperationPlan::metadata)
    throw DataException("Invalid operationplan field");
  OperationPlan* opplan = static_cast<OperationPlan*>(opplanobject);

  // Pick up the item.
  const DataValue* itemElement = in.get(Tags::item);
  if (!itemElement)
    throw DataException("Item must be provided");
  Object* itemobject = itemElement->getObject();
  if (!itemobject || itemobject->getType().category != Item::metadata)
    throw DataException("Invalid item field");
  Item* itm = static_cast<Item*>(itemobject);

  // Find the flow for this item on the operationplan.
  // If multiple exist, we pick up the first one.
  // If none is found, we throw a data error.
  auto flplniter = opplan->getFlowPlans();
  FlowPlan* flpln;
  while ((flpln = flplniter.next() ))
  {
    if (flpln->getItem() == itm)
      return flpln;
  }
  return nullptr;
}


} // end namespace
