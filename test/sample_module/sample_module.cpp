/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by frePPLe bvba                                 *
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
const Keyword OperationTransport::tag_frombuffer("frombuffer");
const Keyword OperationTransport::tag_tobuffer("tobuffer");


MODULE_EXPORT const char* initialize(const Environment::ParameterList& z)
{
  static const char* name = "sample";
  // Register the new class
  OperationTransport::metadata = MetaClass::registerClass<OperationTransport>(
    "operation",
    "operation_transport",
    Object::create<OperationTransport>
    );
  OperationTransport::registerFields<OperationTransport>(
    const_cast<MetaClass*>(OperationTransport::metadata)
    );

  // Register a callback when a buffer is removed from the model
  FunctorStatic<Buffer, OperationTransport>::connect(SIG_REMOVE);

  // Initialize the new Python class
  FreppleClass<OperationTransport, Operation>::initialize();

  // Return the name of the module
  return name;
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
