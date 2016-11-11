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

const MetaCategory* SubOperation::metacategory;
const MetaClass* SubOperation::metadata;


int SubOperation::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SubOperation>(
	  "suboperation", "suboperations", MetaCategory::ControllerDefault  // TODO Need controller to find suboperations. Currently can only add
	  );
  metadata = MetaClass::registerClass<SubOperation>(
    "suboperation", "suboperation", Object::create<SubOperation>, true
  );
  registerFields<SubOperation>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python class
  PythonType& x = FreppleCategory<SubOperation>::getPythonType();
  x.setName("suboperation");
  x.setDoc("frePPLe suboperation");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(SubOperation::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


SubOperation::~SubOperation()
{
  if (owner)
    owner->getSubOperations().remove(this);
  if (oper)
    oper->superoplist.remove(owner);
}


void SubOperation::setOwner(Operation* o)
{
  if (o == owner)
    // No change
    return;

  if (o && !o->hasSubOperations())
    // Some operation types don't have suboperations
    throw DataException("Operation '" + o->getName() + "' can't have suboperations");

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


void SubOperation::setOperation(Operation* o)
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


void SubOperation::setPriority(int pr)
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


PyObject* SubOperation::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds, "operation");
    if (!oper)
      throw DataException("Missing operation on SubOperation");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException("field 'operation' of suboperation must be of type operation");

    // Pick up the owner
    PyObject* owner = PyDict_GetItemString(kwds, "owner");
    if (!owner)
      throw DataException("Missing owner on SubOperation");
    if (!PyObject_TypeCheck(owner, Operation::metadata->pythonClass))
      throw DataException("field 'operation' of suboperation must be of type operation");

    // Pick up the type and create the suboperation
    SubOperation *l = new SubOperation();
    if (oper) l->setOperation(static_cast<Operation*>(oper));
    if (owner) l->setOwner(static_cast<Operation*>(owner));

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (l)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::operation) && !attr.isA(Tags::owner)
           && !attr.isA(Tags::type) && !attr.isA(Tags::action))
        {
          const MetaFieldBase* fmeta = SubOperation::metacategory->findField(attr.getHash());
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


}