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

const MetaCategory* Flow::metadata;
const MetaClass* FlowStart::metadata;
const MetaClass* FlowEnd::metadata;
const MetaClass* FlowTransferBatch::metadata;


int Flow::initialize()
{
  // Initialize the metadata
  int ok = 0;
  metadata = MetaCategory::registerCategory<Flow>(
    "flow", "flows",
    Association<Operation,Buffer,Flow>::reader, finder
    );
  registerFields<Flow>(const_cast<MetaCategory*>(metadata));
  FlowStart::metadata = MetaClass::registerClass<FlowStart>(
    "flow", "flow_start", Object::create<FlowStart>, true
    );
  FlowEnd::metadata = MetaClass::registerClass<FlowEnd>(
    "flow", "flow_end", Object::create<FlowEnd>
    );
  FlowTransferBatch::metadata = MetaClass::registerClass<FlowTransferBatch>(
    "flow", "flow_transfer_batch", Object::create<FlowTransferBatch>
    );
  FlowTransferBatch::registerFields<FlowTransferBatch>(
    const_cast<MetaClass*>(FlowTransferBatch::metadata)
    );

  // Initialize the FlowTransferBatch type
  PythonType& t = FreppleClass<FlowTransferBatch, Flow>::getPythonType();
  t.setName(FlowTransferBatch::metadata->type);
  t.setDoc("frePPLe " + FlowTransferBatch::metadata->type);
  t.supportgetattro();
  t.supportsetattro();
  t.supportstr();
  t.supportcompare();
  t.supportcreate(FlowTransferBatch::create);
  t.setBase(Flow::metadata->pythonClass);
  t.addMethod("toXML", FlowTransferBatch::toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(FlowTransferBatch::metadata)->pythonClass = t.type_object();
  ok += t.typeReady();

  // Initialize the Flow type
  PythonType& x = FreppleCategory<Flow>::getPythonType();
  x.setName("flow");
  x.setDoc("frePPLe flow");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return ok + x.typeReady();
}


Flow::~Flow()
{
  // Set a flag to make sure the level computation is triggered again
  HasLevel::triggerLazyRecomputation();

  // Delete existing flowplans
  if (getOperation() && getBuffer())
  {
    // Loop over operationplans
    for(OperationPlan::iterator i(getOperation()); i != OperationPlan::end(); ++i)
      // Loop over flowplans
      for (auto j = i->beginFlowPlans(); j != i->endFlowPlans(); )
      {
        if (j->getFlow() == this)
          j.deleteFlowPlan();
        else
          ++j;
      }
  }

  // Delete the flow from the operation and the buffer
  if (getOperation())
    getOperation()->flowdata.erase(this);
  if (getBuffer())
    getBuffer()->flows.erase(this);
}


PyObject* Flow::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds, "operation");
    if (!oper)
      throw DataException("missing operation on Flow");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("flow operation must be of type operation");
    else if (!static_cast<Operation*>(oper)->getLocation())
      throw DataException("operation location is unspecified");

    // Pick up the item
    PyObject* item = PyDict_GetItemString(kwds, "item");
    if (!item)
      throw DataException("missing item on Flow");
    if (!PyObject_TypeCheck(item, Item::metadata->pythonClass))
      throw DataException("flow item must be of type item");

    // Pick up the quantity
    PyObject* q1 = PyDict_GetItemString(kwds, "quantity");
    double q2 = q1 ? PythonData(q1).getDouble() : 1.0;

    // Pick up the effectivity dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds, "effective_start");
    if (eff_start)
    {
      PythonData d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds, "effective_end");
    if (eff_end)
    {
      PythonData d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Find or create a buffer for the item at the operation location
    Buffer* buf = Buffer::findOrCreate(
      static_cast<Item*>(item),
      static_cast<Operation*>(oper)->getLocation()
      );

    // Pick up the type and create the flow
    Flow *l;
    PyObject* t = PyDict_GetItemString(kwds, "type");
    if (t)
    {
      PythonData d(t);
      if (d.getString() == "flow_end")
        l = new FlowEnd(
          static_cast<Operation*>(oper),
          static_cast<Buffer*>(buf),
          q2
        );
      else if (d.getString() == "flow_transfer_batch")
        l = new FlowTransferBatch(
          static_cast<Operation*>(oper),
          static_cast<Buffer*>(buf),
          q2
        );
      else
        l = new FlowStart(
          static_cast<Operation*>(oper),
          static_cast<Buffer*>(buf),
          q2
        );
    }
    else
      l = new FlowStart(
        static_cast<Operation*>(oper),
        static_cast<Buffer*>(buf),
        q2
      );

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (l)
    {
      l->setEffective(eff);
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::effective_end) && !attr.isA(Tags::effective_start)
          && !attr.isA(Tags::operation) && !attr.isA(Tags::buffer)
          && !attr.isA(Tags::quantity) && !attr.isA(Tags::type)
          && !attr.isA(Tags::action))
        {
          const MetaFieldBase* fmeta = l->getType().findField(attr.getHash());
          if (!fmeta && l->getType().category)
            fmeta = l->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(l, field);
          else
            l->setProperty(attr.getName(), value);
        }
      };
    }

    // Return the object
    Py_INCREF(l);
    return static_cast<PyObject*>(l);
  }
  catch (...)
  {
    PythonType::evalException();
    return nullptr;
  }
}


Object* Flow::finder(const DataValueDict& d)
{
  // Check operation
  const DataValue* tmp = d.get(Tags::operation);
  if (!tmp)
    return nullptr;
  Operation* oper = static_cast<Operation*>(tmp->getObject());

  // Check buffer field
  tmp = d.get(Tags::buffer);
  if (!tmp)
    return nullptr;
  Buffer* buf = static_cast<Buffer*>(tmp->getObject());

  // Walk over all flows of the operation, and return
  // the first one with matching
  const DataValue* hasEffectiveStart = d.get(Tags::effective_start);
  Date effective_start;
  if (hasEffectiveStart)
    effective_start = hasEffectiveStart->getDate();
  const DataValue* hasEffectiveEnd = d.get(Tags::effective_end);
  Date effective_end;
  if (hasEffectiveEnd)
    effective_end = hasEffectiveEnd->getDate();
  const DataValue* hasPriority = d.get(Tags::priority);
  int priority = 1;
  if (hasPriority)
    priority = hasPriority->getInt();
  const DataValue* hasName = d.get(Tags::name);
  string name;
  if (hasName)
    name = hasName->getString();
  for (Operation::flowlist::const_iterator fl = oper->getFlows().begin();
    fl != oper->getFlows().end(); ++fl)
  {
    if (fl->getBuffer() != buf)
      continue;
    if (hasEffectiveStart && fl->getEffectiveStart() != effective_start)
      continue;
    if (hasEffectiveEnd && fl->getEffectiveEnd() != effective_end)
      continue;
    if (hasPriority && fl->getPriority() != priority)
      continue;
    if (hasName && fl->getName() != name)
      continue;
    return const_cast<Flow*>(&*fl);
  }
  return nullptr;
}


pair<Date, double> Flow::getFlowplanDateQuantity(const FlowPlan* fl) const
{
  if (fl->isConfirmed())
    return make_pair(
      fl->getOperationPlan()->getSetupEnd(),
      fl->getQuantity()
    );
  else
    return make_pair(
      fl->getOperationPlan()->getSetupEnd(),
      getEffective().within(fl->getDate()) && fl->getOperationPlan()->getQuantity() ?
      getQuantityFixed() + fl->getOperationPlan()->getQuantity() * getQuantity() : 0.0
    );
}


pair<Date, double> FlowEnd::getFlowplanDateQuantity(const FlowPlan* fl) const
{
  if (fl->isConfirmed())
    return make_pair(
      fl->getOperationPlan()->getEnd(),
      fl->getQuantity()
    );
  else
    return make_pair(
      fl->getOperationPlan()->getEnd(),
      getEffective().within(fl->getDate()) && fl->getOperationPlan()->getQuantity() ?
      getQuantityFixed() + fl->getOperationPlan()->getQuantity() * getQuantity() : 0.0
    );
}


pair<Date, double> FlowTransferBatch::getFlowplanDateQuantity(const FlowPlan* fl) const
{
  double batch_quantity = getTransferBatch();
  if (!batch_quantity || fl->getOperationPlan()->getSetupEnd() == fl->getOperationPlan()->getEnd())
    // Default to a simple flowplan at the start or end
    return make_pair(
      (getQuantity() < 0 || getQuantityFixed() < 0) ? fl->getOperationPlan()->getSetupEnd() : fl->getOperationPlan()->getEnd(),
      getQuantityFixed() + getQuantity() * fl->getOperationPlan()->getQuantity()
      );
  
  // Compute the number of batches
  double total_quantity = getQuantityFixed() + fl->getOperationPlan()->getQuantity() * getQuantity();
  double batches = ceil((getQuantity() > 0 ? total_quantity : -total_quantity) / getTransferBatch());
  if (!batches)
    batches = 1;
  else if (batches > 50)
  {
    // Put a limit to the number of batches
    batches = 50;
    batch_quantity = (getQuantity() > 0 ? total_quantity : -total_quantity) / 50;
  }

  // Count the index of this batch
  bool found = false;
  long count = 0;
  long totalcount = 0;
  FlowPlan* cur_flpln = fl->getOperationPlan()->firstflowplan;
  FlowPlan* prev_flpln = nullptr;
  while (cur_flpln)
  {
    if (cur_flpln == fl)
      found = true;
    if (cur_flpln->getFlow() == fl->getFlow())
    {
      ++totalcount;
      if (totalcount > batches && !count)
      {
        if (cur_flpln->oper->firstflowplan == cur_flpln)
          cur_flpln->oper->firstflowplan = cur_flpln->nextFlowPlan;
        else
          prev_flpln->nextFlowPlan = cur_flpln->nextFlowPlan;
        auto almost_dead = cur_flpln;
        cur_flpln = cur_flpln->nextFlowPlan;
        delete almost_dead;
        continue;
      }
      if (!found)
        ++count;
    }
    prev_flpln = cur_flpln;
    cur_flpln = cur_flpln->nextFlowPlan;
  }

  Duration op_delta;
  Date op_date = fl->getOperation()->calculateOperationTime(
    fl->getOperationPlan(), fl->getOperationPlan()->getSetupEnd(), 
    fl->getOperationPlan()->getEnd(), &op_delta
    ).getStart();

  if (!count)
  {
    // The first flowplan in the list will always be there, even when the quantity becomes 0.
    // It is responsible for creating extra flowplans when required.
    while (totalcount < batches)
    {
      auto newflowplan = new FlowPlan(fl->getOperationPlan(), this);
      newflowplan->setFollowingBatch(true);
      ++totalcount;
    }
  }

  if (getQuantity() > 0 || getQuantityFixed() > 0)
  {
    // Producing a batch
    op_delta = static_cast<long>(op_delta) / static_cast<long>(batches) * (count + 1);
    total_quantity -= count * batch_quantity;
    if (total_quantity < 0.0)
      total_quantity = 0.0;
    return make_pair(
      fl->getOperation()->calculateOperationTime(
        fl->getOperationPlan(), op_date, op_delta, true
        ).getEnd(),
      total_quantity > batch_quantity ? batch_quantity : total_quantity
    );
  }
  else
  {
    // Consuming a batch
    op_delta = static_cast<long>(op_delta) / static_cast<long>(batches) * count;
    total_quantity += count * getTransferBatch();
    if (total_quantity > 0.0)
      total_quantity = 0.0;
    return make_pair(
      fl->getOperation()->calculateOperationTime(
        fl->getOperationPlan(), op_date, op_delta, true
      ).getEnd(),
      total_quantity < -batch_quantity ? -batch_quantity : total_quantity
    );
  }
}

} // end namespace
