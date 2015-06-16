/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by Johan De Taeye, frePPLe bvba                 *
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

DECLARE_EXPORT const MetaCategory* Flow::metadata;
DECLARE_EXPORT const MetaClass* FlowStart::metadata;
DECLARE_EXPORT const MetaClass* FlowEnd::metadata;
DECLARE_EXPORT const MetaClass* FlowFixedStart::metadata;
DECLARE_EXPORT const MetaClass* FlowFixedEnd::metadata;


int Flow::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Flow>("flow", "flows", MetaCategory::ControllerDefault, writer);
  registerFields<Flow>(const_cast<MetaCategory*>(metadata));
  FlowStart::metadata = MetaClass::registerClass<FlowStart>(
    "flow", "flow_start", Object::create<FlowStart>, true
    );
  FlowEnd::metadata = MetaClass::registerClass<FlowEnd>(
    "flow", "flow_end", Object::create<FlowEnd>
    );
  FlowFixedStart::metadata = MetaClass::registerClass<FlowFixedStart>(
    "flow", "flow_fixed_start", Object::create<FlowFixedStart>
    );
  FlowFixedEnd::metadata = MetaClass::registerClass<FlowFixedEnd>(
    "flow", "flow_fixed_end", Object::create<FlowFixedEnd>
    );

  // Initialize the type
  PythonType& x = FreppleCategory<Flow>::getPythonType();
  x.setName("flow");
  x.setDoc("frePPLe flow");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


void Flow::writer(const MetaCategory* c, Serializer* o)
{
  bool firstflow = true;
  for (Operation::iterator i = Operation::begin(); i != Operation::end(); ++i)
    for (Operation::flowlist::const_iterator j = i->getFlows().begin(); j != i->getFlows().end(); ++j)
    {
      if (firstflow)
      {
        o->BeginList(Tags::tag_flows);
        firstflow = false;
      }
      // We use the FULL mode, to force the flows being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_flow, &*j, FULL);
    }
  if (!firstflow) o->EndList(Tags::tag_flows);
}


DECLARE_EXPORT void Flow::validate(Action action)
{
  // Catch null operation and buffer pointers
  Operation* oper = getOperation();
  Buffer* buf = getBuffer();
  if (!oper || !buf)
  {
    // This flow is not a valid one since it misses essential information
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
  // 3) overlapping effectivity dates already exists, and 4) same
  // flow type.
  Operation::flowlist::const_iterator i = oper->getFlows().begin();
  for (; i != oper->getFlows().end(); ++i)
    if (i->getBuffer() == buf
        && i->getEffective().overlap(getEffective())
        && i->getType() == getType()
        && &*i != this)
      break;

  // Apply the appropriate action
  switch (action)
  {
    case ADD:
      if (i != oper->getFlows().end())
        throw DataException("Flow of '" + oper->getName() + "' and '" +
            buf->getName() + "' already exists");
      break;
    case CHANGE:
      throw DataException("Can't update a flow");
    case ADD_CHANGE:
      // ADD is handled in the code after the switch statement
      if (i == oper->getFlows().end()) break;
      throw DataException("Can't update a flow between '" +
        oper->getName() + "' and '" + buf->getName() + "')");
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

  // Clean up alternate flows
  if (hasAlts)
  {
    // The flow has alternates.
    // Make a new flow the leading one. Or if there is only one alternate
    // present it is not marked as an alternate any more.
    unsigned short cnt = 0;
    int minprio = INT_MAX;
    Flow* newLeader = NULL;
    for (Operation::flowlist::iterator i = getOperation()->flowdata.begin();
        i != getOperation()->flowdata.end(); ++i)
      if (i->altFlow == this)
      {
        cnt++;
        if (i->priority < minprio)
        {
          newLeader = &*i;
          minprio = i->priority;
        }
      }
    if (cnt < 1)
      throw LogicException("Alternate flows update failure");
    else if (cnt == 1)
      // No longer an alternate any more
      newLeader->altFlow = NULL;
    else
    {
      // Mark a new leader flow
      newLeader->hasAlts = true;
      newLeader->altFlow = NULL;
      for (Operation::flowlist::iterator i = getOperation()->flowdata.begin();
          i != getOperation()->flowdata.end(); ++i)
        if (i->altFlow == this) i->altFlow = newLeader;
    }
  }
  if (altFlow)
  {
    // The flow is an alternate of another one.
    // If it was the only alternate, then the hasAlts flag on the parent
    // flow needs to be set back to false
    bool only_one = true;
    for (Operation::flowlist::iterator i = getOperation()->flowdata.begin();
        i != getOperation()->flowdata.end(); ++i)
      if (i->altFlow == altFlow)
      {
        only_one = false;
        break;
      }
    if (only_one) altFlow->hasAlts = false;
  }
}


DECLARE_EXPORT void Flow::setAlternate(Flow *f)
{
  // Can't be an alternate to oneself.
  // No need to flag as an exception.
  if (f == this) return;

  // Validate the argument
  if (!f)
    throw DataException("Setting NULL alternate flow");
  if (hasAlts || f->altFlow)
    throw DataException("Nested alternate flows are not allowed");
  if (!f->isConsumer() || !isConsumer())
    throw DataException("Only consuming alternate flows are supported");

  // Update both flows
  f->hasAlts = true;
  altFlow = f;
}


DECLARE_EXPORT void Flow::setAlternate(string n)
{
  if (!getOperation())
    throw LogicException("Can't set an alternate flow before setting the operation");
  Flow *x = getOperation()->flowdata.find(n);
  if (!x) throw DataException("Can't find flow with name '" + n + "'");
  setAlternate(x);
}


PyObject* Flow::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds,"operation");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("flow operation must be of type operation");

    // Pick up the resource
    PyObject* buf = PyDict_GetItemString(kwds,"buffer");
    if (!PyObject_TypeCheck(buf, Buffer::metadata->pythonClass))
      throw DataException("flow buffer must be of type buffer");

    // Pick up the quantity
    PyObject* q1 = PyDict_GetItemString(kwds,"quantity");
    double q2 = q1 ? PythonData(q1).getDouble() : 1.0;

    // Pick up the effectivity dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonData d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonData d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Pick up the type and create the flow
    Flow *l;
    PyObject* t = PyDict_GetItemString(kwds,"type");
    if (t)
    {
      PythonData d(t);
      if (d.getString() == "flow_end")
        l = new FlowEnd(
          static_cast<Operation*>(oper),
          static_cast<Buffer*>(buf),
          q2, eff
        );
      else if (d.getString() == "flow_fixed_end")
        l = new FlowFixedEnd(
          static_cast<Operation*>(oper),
          static_cast<Buffer*>(buf),
          q2, eff
        );
      else if (d.getString() == "flow_fixed_start")
        l = new FlowFixedStart(
          static_cast<Operation*>(oper),
          static_cast<Buffer*>(buf),
          q2, eff
        );
      else
        l = new FlowStart(
          static_cast<Operation*>(oper),
          static_cast<Buffer*>(buf),
          q2, eff
        );
    }
    else
      l = new FlowStart(
        static_cast<Operation*>(oper),
        static_cast<Buffer*>(buf),
        q2, eff
      );

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (l)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        Attribute attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::tag_effective_end) && !attr.isA(Tags::tag_effective_start)
          && !attr.isA(Tags::tag_operation) && !attr.isA(Tags::tag_buffer)
          && !attr.isA(Tags::tag_quantity) && !attr.isA(Tags::tag_type)
          && !attr.isA(Tags::tag_action))
        {
          const MetaFieldBase* fmeta = l->getType().findField(attr.getHash());
          if (!fmeta && l->getType().category)
            fmeta = l->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(l, field);
          else
            PyErr_Format(PyExc_AttributeError,
                "attribute '%S' on '%s' can't be updated",
                key, Py_TYPE(l)->tp_name);
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
    return NULL;
  }
}


int FlowIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<FlowIterator>::getPythonType();
  x.setName("flowIterator");
  x.setDoc("frePPLe iterator for flows");
  x.supportiter();
  return x.typeReady();
}


PyObject* FlowIterator::iternext()
{
  PyObject* result;
  if (buf)
  {
    // Iterate over flows on a buffer
    if (ib == buf->getFlows().end()) return NULL;
    result = const_cast<Flow*>(&*ib);
    ++ib;
  }
  else
  {
    // Iterate over flows on an operation
    if (io == oper->getFlows().end()) return NULL;
    result = const_cast<Flow*>(&*io);
    ++io;
  }
  Py_INCREF(result);
  return result;
}

} // end namespace
