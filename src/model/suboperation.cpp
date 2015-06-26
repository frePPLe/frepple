/***************************************************************************
 *                                                                         *
 * Copyright (C) 2015 by frePPLe bvba                                      *
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

DECLARE_EXPORT const MetaCategory* SubOperation::metacategory;
DECLARE_EXPORT const MetaClass* SubOperation::metadata;


int SubOperation::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SubOperation>(
	  "suboperation", "suboperations", MetaCategory::ControllerDefault
	  );
  metadata = MetaClass::registerClass<SupplierItem>(
    "suboperation", "suboperation", Object::create<SubOperation>, true
  );
  registerFields<SubOperation>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<SubOperation>::getPythonType();
  x.setName("suboperation");
  x.setDoc("frePPLe suboperation");
  x.supportgetattro();
  x.supportsetattro();
  // TODO x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(SubOperation::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


int SubOperationIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<SubOperationIterator>::getPythonType();
  x.setName("suboperationIterator");
  x.setDoc("frePPLe iterator for suboperations");
  x.supportiter();
  return x.typeReady();
}


DECLARE_EXPORT SubOperation::~SubOperation()
{
  if (owner)
    owner->getSubOperations().remove(this);
  if (oper)
    oper->superoplist.remove(owner);
}


DECLARE_EXPORT void SubOperation::setOwner(Operation* o)
{
  if (o == owner) return;

  // Remove from previous owner
  if (oper && owner)
    oper->removeSuperOperation(owner);
  if (owner)
    owner->getSubOperations().remove(this);

  // Update 
  owner = o;

  // Insert at new owner
  if (oper && owner)
    oper->addSuperOperation(owner);
  if (owner)
  {
    Operation::Operationlist::iterator iter = owner->getSubOperations().begin();
    while (iter != owner->getSubOperations().end() && prio >= (*iter)->getPriority())
      ++iter;
    owner->getSubOperations().insert(iter, this);
  }
}


DECLARE_EXPORT void SubOperation::setOperation(Operation* o)
{
  if (o == oper) return;

  // Remove from previous oper
  if (oper && owner)
    oper->removeSuperOperation(owner);

  // Update
  oper = o;

  // Insert at new oper
  if (owner)
    oper->addSuperOperation(owner);
}


DECLARE_EXPORT void SubOperation::setPriority(int pr)
{
  if (prio == pr) return;

  if (pr < 0)
    throw DataException("Suboperation priority must be greater or equal to 0");

  prio = pr;

  if (owner)
  {
    // Maintain the list in order of priority
    owner->getSubOperations().remove(this);
    Operation::Operationlist::iterator iter = owner->getSubOperations().begin();
    while (iter != owner->getSubOperations().end() && prio >= (*iter)->getPriority())
      ++iter;
    owner->getSubOperations().insert(iter, this);
  }
}


PyObject *SubOperationIterator::iternext()
{
  // TODO XXX missing implementation
  return NULL;
}

}