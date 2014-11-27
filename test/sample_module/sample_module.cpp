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

#include "sample_module.h"

namespace sample_module
{

const MetaClass *OperationTransport::metadata;
const Keyword tag_frombuffer("frombuffer");
const Keyword tag_tobuffer("tobuffer");


MODULE_EXPORT const char* initialize(const Environment::ParameterList& z)
{
  static const char* name = "sample";
  // Register the new class
  OperationTransport::metadata = new MetaClass(
    "operation",
    "operation_transport",
    Object::createString<OperationTransport>);

  // Register a callback when a buffer is removed from the model
  FunctorStatic<Buffer, OperationTransport>::connect(SIG_REMOVE);

  // Initialize the new Python class
  FreppleClass<OperationTransport,Operation>::initialize();

  // Return the name of the module
  return name;
}


void OperationTransport::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(tag_frombuffer) || pAttr.isA(tag_tobuffer))
    pIn.readto( Buffer::metadata->readFunction(Buffer::metadata,pIn.getAttributes()) );
  else
    OperationFixedTime::beginElement(pIn, pAttr);
}


void OperationTransport::writeElement
(Serializer *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL)
    o->BeginObject(tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  OperationFixedTime::writeElement(o, tag, NOHEADTAIL);
  o->writeElement(tag_frombuffer, fromBuf, REFERENCE);
  o->writeElement(tag_tobuffer, toBuf, REFERENCE);

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


void OperationTransport::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(tag_frombuffer))
  {
    Buffer *l = dynamic_cast<Buffer*>(pIn.getPreviousObject());
    if (l) setFromBuffer(l);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(tag_tobuffer))
  {
    Buffer *l = dynamic_cast<Buffer*>(pIn.getPreviousObject());
    if (l) setToBuffer(l);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
    OperationFixedTime::endElement(pIn, pAttr, pElement);
}


PyObject* OperationTransport::getattro(const Attribute& attr)
{
  if (attr.isA(tag_tobuffer))
    return PythonObject(getToBuffer());
  if (attr.isA(tag_frombuffer))
    return PythonObject(getFromBuffer());;
  return OperationFixedTime::getattro(attr);
}


int OperationTransport::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(tag_tobuffer))
  {
    if (!field.check(Buffer::metadata))
    {
      PyErr_SetString(PythonDataException, "ToBuffer must be of type buffer");
      return -1;
    }
    Buffer* y = static_cast<Buffer*>(static_cast<PyObject*>(field));
    setToBuffer(y);
  }
  else if (attr.isA(tag_frombuffer))
  {
    if (!field.check(Buffer::metadata))
    {
      PyErr_SetString(PythonDataException, "FromBuffer must be of type buffer");
      return -1;
    }
    Buffer* y = static_cast<Buffer*>(static_cast<PyObject*>(field));
    setFromBuffer(y);
  }
  else
    return OperationFixedTime::setattro(attr, field);
  return 0;
}


// This (static) method is called when an operation is being deleted.
// It loops over all operations, picks up the OperationTransports instances
// and verifies whether they are referring to the location being deleted.
// If they refer to the operation being deleted the transport operation
// is deleted itself: we don't want to transport from or to a non-existing
// location.
// Note:
// The execution time of this method is linear with the number of operations
// in the model. For large models where buffers are very frequently being
// deleted the current design is not very efficient. But since deletions of
// buffers are expected to be rare the current design should do just fine.
// Note:
// The use of a static subscription keeps the memory overhead of the cleanup
// method to a handfull of bytes, regardless of the model size.
bool OperationTransport::callback(Buffer* l, const Signal a)
{
  // Loop over all transport operations
  for (Operation::iterator i = Operation::begin(); i != Operation::end(); )
    if (typeid(*i) == typeid(OperationTransport))
    {
      OperationTransport& j = static_cast<OperationTransport&>(*i);
      if (l == j.fromBuf || l == j.toBuf)
      {
        // Delete the operation, but increment the iterator first!
        Operation::iterator k = i++;
        delete &*k;
        if (i == Operation::end()) break;
      }
      else ++i;
    }
    else ++i;
  // Always approve the deletion
  return true;
}


void OperationTransport::setFromBuffer(Buffer *b)
{
  // Don't update the operation if operationplans already exist
  if (OperationPlan::iterator(this) != OperationPlan::end())
    throw DataException("Can't update an initialized transport operation");

  // Create a flow
  fromBuf = b;
  new Flow(this, b, -1);
}

void OperationTransport::setToBuffer(Buffer *b)
{
  // Don't update the operation if operationplans already exist
  if (OperationPlan::iterator(this) != OperationPlan::end())
    throw DataException("Can't update an initialized transport operation");

  // Create a flow
  toBuf = b;
  new FlowEnd(this, b, 1);
}

}  // End namespace
