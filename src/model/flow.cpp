/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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
  metadata = new MetaCategory
  ("flow", "flows", MetaCategory::ControllerDefault, writer);
  FlowStart::metadata = new MetaClass("flow", "flow_start",
      Object::createDefault<FlowStart>, true);
  FlowEnd::metadata = new MetaClass("flow", "flow_end",
      Object::createDefault<FlowEnd>);
  FlowFixedStart::metadata = new MetaClass("flow", "flow_fixed_start",
      Object::createDefault<FlowFixedStart>);
  FlowFixedEnd::metadata = new MetaClass("flow", "flow_fixed_end",
      Object::createDefault<FlowFixedEnd>);

  // Initialize the type
  PythonType& x = FreppleCategory<Flow>::getType();
  x.setName("flow");
  x.setDoc("frePPLe flow");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


void Flow::writer(const MetaCategory* c, XMLOutput* o)
{
  bool firstflow = true;
  for (Operation::iterator i = Operation::begin(); i != Operation::end(); ++i)
    for (Operation::flowlist::const_iterator j = i->getFlows().begin(); j != i->getFlows().end(); ++j)
    {
      if (firstflow)
      {
        o->BeginObject(Tags::tag_flows);
        firstflow = false;
      }
      // We use the FULL mode, to force the flows being written regardless
      // of the depth in the XML tree.
      o->writeElement(Tags::tag_flow, &*j, FULL);
    }
  if (!firstflow) o->EndObject(Tags::tag_flows);
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


DECLARE_EXPORT void Flow::setAlternate(const string& n)
{
  if (!getOperation())
    throw LogicException("Can't set an alternate flow before setting the operation");
  Flow *x = getOperation()->flowdata.find(n);
  if (!x) throw DataException("Can't find flow with name '" + n + "'");
  setAlternate(x);
}


DECLARE_EXPORT void Flow::writeElement (XMLOutput *o, const Keyword& tag, mode m) const
{
  // If the flow has already been saved, no need to repeat it again
  // A 'reference' to a flow is not useful to be saved.
  if (m == REFERENCE) return;
  assert(m != NOHEAD);

  // Write the head
  o->BeginObject(tag, Tags::tag_type, getType().type);

  // If the flow is defined inside of an operation tag, we don't need to save
  // the operation. Otherwise we do save it...
  if (!dynamic_cast<Operation*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_operation, getOperation());

  // If the flow is defined inside of an buffer tag, we don't need to save
  // the buffer. Otherwise we do save it...
  if (!dynamic_cast<Buffer*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_buffer, getBuffer());

  // Write the quantity, priority, name and alternate
  o->writeElement(Tags::tag_quantity, getQuantity());
  if (getPriority()!=1) o->writeElement(Tags::tag_priority, getPriority());
  if (!getName().empty()) o->writeElement(Tags::tag_name, getName());
  if (getAlternate())
    o->writeElement(Tags::tag_alternate, getAlternate()->getName());

  // Write the effective daterange
  if (getEffective().getStart() != Date::infinitePast)
    o->writeElement(Tags::tag_effective_start, getEffective().getStart());
  if (getEffective().getEnd() != Date::infiniteFuture)
    o->writeElement(Tags::tag_effective_end, getEffective().getEnd());

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void Flow::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_buffer))
    pIn.readto( Buffer::reader(Buffer::metadata,pIn.getAttributes()) );
  else if (pAttr.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else
    PythonDictionary::read(pIn, pAttr, getDict());
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
  else if (pAttr.isA(Tags::tag_priority))
    setPriority(pElement.getInt());
  else if (pAttr.isA(Tags::tag_name))
    setName(pElement.getString());
  else if (pAttr.isA(Tags::tag_alternate))
    setAlternate(pElement.getString());
  else if (pAttr.isA(Tags::tag_search))
    setSearch(pElement.getString());
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
  else if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
  else if (pIn.isObjectEnd())
  {
    // The flow data are now all read in. See if it makes sense now...
    Action a = pIn.getUserArea() ?
        *static_cast<Action*>(pIn.getUserArea()) :
        ADD_CHANGE;
    delete static_cast<Action*>(pIn.getUserArea());
    try { validate(a); }
    catch (...)
    {
      delete this;
      throw;
    }
  }
}


DECLARE_EXPORT void FlowEnd::writeElement
(XMLOutput *o, const Keyword& tag, mode m) const
{
  // If the flow has already been saved, no need to repeat it again
  // A 'reference' to a flow is not useful to be saved.
  if (m == REFERENCE) return;
  assert(m != NOHEAD);

  // Write the head
  o->BeginObject(tag, Tags::tag_type, getType().type);

  // If the flow is defined inside of an operation tag, we don't need to save
  // the operation. Otherwise we do save it...
  if (!dynamic_cast<Operation*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_operation, getOperation());

  // If the flow is defined inside of an buffer tag, we don't need to save
  // the buffer. Otherwise we do save it...
  if (!dynamic_cast<Buffer*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_buffer, getBuffer());

  // Write the quantity, priority name and alternate
  o->writeElement(Tags::tag_quantity, getQuantity());
  if (getPriority()!=1) o->writeElement(Tags::tag_priority, getPriority());
  if (!getName().empty()) o->writeElement(Tags::tag_name, getName());
  if (getAlternate())
    o->writeElement(Tags::tag_alternate, getAlternate()->getName());

  // Write the effective daterange
  if (getEffective().getStart() != Date::infinitePast)
    o->writeElement(Tags::tag_effective_start, getEffective().getStart());
  if (getEffective().getEnd() != Date::infiniteFuture)
    o->writeElement(Tags::tag_effective_end, getEffective().getEnd());

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT PyObject* Flow::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_buffer))
    return PythonObject(getBuffer());
  if (attr.isA(Tags::tag_operation))
    return PythonObject(getOperation());
  if (attr.isA(Tags::tag_quantity))
    return PythonObject(getQuantity());
  if (attr.isA(Tags::tag_priority))
    return PythonObject(getPriority());
  if (attr.isA(Tags::tag_effective_end))
    return PythonObject(getEffective().getEnd());
  if (attr.isA(Tags::tag_effective_start))
    return PythonObject(getEffective().getStart());
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(getHidden());
  if (attr.isA(Tags::tag_alternate))
    return PythonObject(getAlternate());
  if (attr.isA(Tags::tag_search))
  {
    ostringstream ch;
    ch << getSearch();
    return PythonObject(ch.str());
  }
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  return NULL;
}


DECLARE_EXPORT int Flow::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_buffer))
  {
    if (!field.check(Buffer::metadata))
    {
      PyErr_SetString(PythonDataException, "flow buffer must be of type buffer");
      return -1;
    }
    Buffer* y = static_cast<Buffer*>(static_cast<PyObject*>(field));
    setBuffer(y);
  }
  else if (attr.isA(Tags::tag_operation))
  {
    if (!field.check(Operation::metadata))
    {
      PyErr_SetString(PythonDataException, "flow operation must be of type operation");
      return -1;
    }
    Operation* y = static_cast<Operation*>(static_cast<PyObject*>(field));
    setOperation(y);
  }
  else if (attr.isA(Tags::tag_quantity))
    setQuantity(field.getDouble());
  else if (attr.isA(Tags::tag_priority))
    setPriority(field.getInt());
  else if (attr.isA(Tags::tag_effective_end))
    setEffectiveEnd(field.getDate());
  else if (attr.isA(Tags::tag_effective_start))
    setEffectiveStart(field.getDate());
  else if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_alternate))
  {
    if (!field.check(Flow::metadata))
      setAlternate(field.getString());
    else
    {
      Flow *y = static_cast<Flow*>(static_cast<PyObject*>(field));
      setAlternate(y);
    }
  }
  else if (attr.isA(Tags::tag_search))
    setSearch(field.getString());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;
  return 0;
}


/** @todo method implementation not generic and doesn't support clean subclassing. */
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
    double q2 = q1 ? PythonObject(q1).getDouble() : 1.0;

    // Pick up the effectivity dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonObject d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonObject d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Pick up the type and create the flow
    Flow *l;
    PyObject* t = PyDict_GetItemString(kwds,"type");
    if (t)
    {
      PythonObject d(t);
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
  PythonType& x = PythonExtension<FlowIterator>::getType();
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
