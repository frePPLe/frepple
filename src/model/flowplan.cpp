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
  auto fl_info = fl->getFlowplanDateQuantity(this);
  fl->getBuffer()->flowplans.insert(this, fl_info.second, fl_info.first);

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  fl->getBuffer()->setChanged();
  fl->getOperation()->setChanged();
}


FlowPlan::FlowPlan(OperationPlan *opplan, const Flow *f, Date d, double q)
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
  fl->getBuffer()->flowplans.insert(this, q, d);

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
  if (getOperationPlan()->getProposed() && s == "confirmed")
    throw DataException("OperationPlanMaterial locked while OperationPlan is not");
  if (s == "confirmed")
    flags |= STATUS_CONFIRMED;
  else if (s == "proposed")
    flags &= ~STATUS_CONFIRMED;
  else
    throw DataException("invalid operationplanmaterial status:" + s);
}


void FlowPlan::update()
{
  // Update the timeline data structure
  auto fl_info = fl->getFlowplanDateQuantity(this);
  fl->getBuffer()->flowplans.update(this, fl_info.second, fl_info.first);

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
  if (!newfl)
    throw DataException("Can't switch to nullptr flow");
  if (newfl->getType() != fl->getType())
    throw DataException("Flowplans can only switch to flows of the same type");

  if (&newfl->getType() != FlowTransferBatch::metadata || !fl)
  {
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
    auto fl_info = fl->getFlowplanDateQuantity(this);
    fl->getBuffer()->flowplans.insert(this, fl_info.second, fl_info.first);
    fl->getBuffer()->setChanged();
    fl->getOperation()->setChanged();
  }
  else
  {
    // Switch all flowplans of the same transfer batch
    auto oldFlow = fl;
    if (oldFlow->getOperation() != newfl->getOperation())
      throw DataException("Only switching to a flow on the same operation is allowed");
    for (auto flpln = getOperationPlan()->beginFlowPlans(); flpln != getOperationPlan()->endFlowPlans(); ++flpln)
    {
      if (flpln->getFlow() != oldFlow)
        continue;

      // Remove from the old buffer      
      flpln->getBuffer()->flowplans.erase(&*flpln);
      flpln->getBuffer()->setChanged();

      // Insert in the new buffer
      flpln->fl = newfl;
      auto fl_info = flpln->fl->getFlowplanDateQuantity(&*flpln);
      flpln->fl->getBuffer()->flowplans.insert(&*flpln, fl_info.second, fl_info.first);
      flpln->fl->getBuffer()->setChanged();
      flpln->fl->getOperation()->setChanged();
    }
  }
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


pair<double, double> FlowPlan::setQuantity(
  double quantity, bool rounddown, bool update, bool execute, short mode
  )
{
  // TODO argument "update" isn't used
  if (isConfirmed())
  {
    // Confirmed flowplans take any quantity, regardless of the
    // quantity of the owning operationplan.
    if (execute)
    {
      // Update the timeline data structure
      getFlow()->getBuffer()->flowplans.update(
        this,
        quantity,
        getDate()
      );

      // Mark the operation and buffer as having changed. This will trigger the
      // recomputation of their problems
      fl->getBuffer()->setChanged();
      fl->getOperation()->setChanged();
    }
    return make_pair(quantity, oper->getQuantity());
  }

  if (!getFlow()->getEffective().within(getDate()))
  {
    if (execute)
    {
      if (
        mode == 2 
        || (mode == 0 && getFlow()->getType() == *FlowEnd::metadata)
        )
      {
        oper->getOperation()->setOperationPlanParameters(
          oper, 0.0,
          Date::infinitePast, oper->getEnd(),
          true, execute, rounddown
        );
      }
      else if (
        mode == 1 
        || (mode == 0 && getFlow()->getType() == *FlowStart::metadata)
        )
      {
        oper->getOperation()->setOperationPlanParameters(
          oper, 0.0,
          oper->getStart(), Date::infinitePast,
          false, execute, rounddown
        );
      }
    }
    return make_pair(0.0, 0.0);
  }

  double opplan_quantity;
  bool less_than_fixed_qty = fabs(quantity) < fabs(getFlow()->getQuantityFixed()) + ROUNDING_ERROR;
  if (getFlow()->getQuantity() == 0.0 || less_than_fixed_qty)
  {
    // Fixed quantity flows only allow resizing to 0
    if (less_than_fixed_qty && oper->getQuantity() != 0.0)
    {
      if (mode == 2 || (mode == 0 && getFlow()->getType() == *FlowEnd::metadata))
        opplan_quantity = oper->getOperation()->setOperationPlanParameters(
          oper, 0.0, Date::infinitePast, oper->getEnd(),
          true, execute, rounddown
          ).quantity;
      else if (mode == 1 || (mode == 0 && getFlow()->getType() == *FlowStart::metadata))
        opplan_quantity = oper->getOperation()->setOperationPlanParameters(
          oper, 0.0, oper->getStart(), Date::infinitePast,
          false, execute, rounddown
          ).quantity;
      else
        throw LogicException("Unreachable code reached");
    }
    else if (!less_than_fixed_qty && oper->getQuantity() == 0.0)
    {
      if (mode == 2 || (mode == 0 && getFlow()->getType() == *FlowEnd::metadata))
        opplan_quantity = oper->getOperation()->setOperationPlanParameters(
          oper, 0.001, Date::infinitePast, oper->getEnd(),
          true, execute, rounddown
          ).quantity;
      else if (mode == 1 || (mode == 0 && getFlow()->getType() == *FlowStart::metadata))
        opplan_quantity = oper->getOperation()->setOperationPlanParameters(
          oper, 0.001, oper->getStart(), Date::infinitePast,
          false, execute, rounddown
          ).quantity;
      else
        throw LogicException("Unreachable code reached");
    }
  }
  else
  {
    // Proportional or transfer batch flows
    // For transfer batch flowplans the argument quantity is expected to be the
    // total quantity of all batches.
    if (mode == 2 || (mode == 0 && getFlow()->getType() == *FlowEnd::metadata))
      opplan_quantity = oper->getOperation()->setOperationPlanParameters(
        oper, (quantity - getFlow()->getQuantityFixed()) / getFlow()->getQuantity(),
        Date::infinitePast, oper->getEnd(),
        true, execute, rounddown
        ).quantity;
    else if (mode == 1 || (mode == 0 && getFlow()->getType() == *FlowStart::metadata))
      opplan_quantity = oper->getOperation()->setOperationPlanParameters(
        oper, (quantity - getFlow()->getQuantityFixed()) / getFlow()->getQuantity(),
        oper->getStart(), Date::infinitePast,
        false, execute, rounddown
        ).quantity;
    else
      throw LogicException("Unreachable code reached");
  }
  if (opplan_quantity)
    return make_pair(opplan_quantity * getFlow()->getQuantity() + getFlow()->getQuantityFixed(), opplan_quantity);
  else
    return make_pair(0.0, 0.0);
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


Duration FlowPlan::getPeriodOfCover() const
{
  double left_for_consumption = getOnhand();
  if (left_for_consumption < ROUNDING_ERROR)
    return Duration(0L);
  auto fpiter = getBuffer()->getFlowPlans().begin(this); 
  ++fpiter;
  while (fpiter != getBuffer()->getFlowPlans().end())
  {    
    if (fpiter->getQuantity() < 0.0)
    {
      left_for_consumption += fpiter->getQuantity();
      if (left_for_consumption < ROUNDING_ERROR)
        return fpiter->getDate() - getDate();
    }
    ++fpiter;
  }
  return Duration(999L * 86400L);
}

} // end namespace
