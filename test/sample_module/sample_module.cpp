/***************************************************************************
  file : $HeadURL$
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

#include "sample_module.h"

namespace sample_module
{

const MetaClass OperationTransport::metadata;
const Keyword tag_from("from");
const Keyword tag_to("to");


MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z)
{
  static const char* name = "sample";
  // Register the new class
  OperationTransport::metadata.registerClass(
    "operation",
    "operation_transport",
    Object::createString<OperationTransport>);

  // Register a callback
  FunctorStatic<Buffer, OperationTransport>::connect(SIG_REMOVE);

  // Return the name of the module
  return name;
}


void OperationTransport::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(tag_from) || pAttr.isA(tag_to))
    pIn.readto( Buffer::reader(Buffer::metadata,pIn.getAttributes()) );
  else
    OperationFixedTime::beginElement(pIn, pAttr);
}


void OperationTransport::writeElement
(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEADER)
    o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  o->writeElement(tag_from, fromBuf, REFERENCE);
  o->writeElement(tag_to, toBuf, REFERENCE);

  // Pass over to the parent class for the remaining fields
  OperationFixedTime::writeElement(o, tag, NOHEADER);
}


void OperationTransport::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(tag_from))
  {
    Buffer *l = dynamic_cast<Buffer*>(pIn.getPreviousObject());
    if (l) setFromBuffer(l);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(tag_to))
  {
    Buffer *l = dynamic_cast<Buffer*>(pIn.getPreviousObject());
    if (l) setToBuffer(l);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
    OperationFixedTime::endElement(pIn, pAttr, pElement);
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
bool OperationTransport::callback(Buffer* l, Signal a)
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
