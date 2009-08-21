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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"
namespace frepple
{

DECLARE_EXPORT const MetaCategory* Flow::metadata;
DECLARE_EXPORT const MetaClass* FlowStart::metadata,
  *FlowEnd::metadata;


int Flow::initialize(PyObject* m)
{
  // Initialize the metadata
  metadata = new MetaCategory
    ("flow", "flows", MetaCategory::ControllerDefault);
  FlowStart::metadata = new MetaClass("flow", "flow_start",
    Object::createDefault<FlowStart>, true);
  FlowEnd::metadata = new MetaClass("flow", "flow_end",
    Object::createDefault<FlowEnd>);

  // Initialize the type
  PythonType& x = FreppleCategory<Flow,Flow>::getType();
  x.setName("flow");
  x.setDoc("frePPLe flow");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", FreppleCategory<Flow,Flow>::toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaCategory*>(Flow::metadata)->pythonClass = x.type_object();
  return x.typeReady(m);
}


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
            buf->getName() + "' already exists");
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
    pIn.readto( Buffer::reader(Buffer::metadata,pIn.getAttributes()) );
  else if (pAttr.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
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


DECLARE_EXPORT PyObject* Flow::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_buffer))
    return PythonObject(getBuffer());
  if (attr.isA(Tags::tag_operation))
    return PythonObject(getOperation());
  if (attr.isA(Tags::tag_quantity))
    return PythonObject(getQuantity());
  if (attr.isA(Tags::tag_effective_end))
    return PythonObject(getEffective().getEnd());
  if (attr.isA(Tags::tag_effective_start))
    return PythonObject(getEffective().getStart());
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
  else if (attr.isA(Tags::tag_effective_end))
    setEffectiveEnd(field.getDate());
  else if (attr.isA(Tags::tag_effective_start))
    setEffectiveStart(field.getDate());
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

    // Pick up the effective start date
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonObject d(eff_start);
      l->setEffectiveStart(d.getDate());
    }

    // Pick up the effective end date
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonObject d(eff_end);
      l->setEffectiveEnd(d.getDate());
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


int PythonFlowIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonFlowIterator>::getType();
  x.setName("flowIterator");
  x.setDoc("frePPLe iterator for flows");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonFlowIterator::iternext()
{  
  if (buf) 
  {
    // Iterate over flows on a buffer 
    if (ib == buf->getFlows().end()) return NULL;
    return PythonObject(const_cast<Flow*>(&*(ib++)));
  }
  else
  {
    // Iterate over flows on an operation 
    if (io == oper->getFlows().end()) return NULL;
    return PythonObject(const_cast<Flow*>(&*(io++)));
  }
}

} // end namespace
