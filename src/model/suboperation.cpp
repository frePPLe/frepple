/***************************************************************************
 *                                                                         *
 * Copyright (C) 2015 by frePPLe bv                                        *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple {

const MetaCategory* SubOperation::metacategory;
const MetaClass* SubOperation::metadata;

int SubOperation::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SubOperation>(
      "suboperation", "suboperations",
      MetaCategory::ControllerDefault  // TODO Need controller to find
                                       // suboperations. Currently can only add
  );
  metadata = MetaClass::registerClass<SubOperation>(
      "suboperation", "suboperation", Object::create<SubOperation>, true);
  registerFields<SubOperation>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python class
  auto& x = FreppleCategory<SubOperation>::getPythonType();
  x.setName("suboperation");
  x.setDoc("frePPLe suboperation");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  metadata->setPythonClass(x);
  return x.typeReady();
}

SubOperation::~SubOperation() {
  if (owner) owner->getSubOperations().remove(this);
  if (oper) oper->owner = nullptr;
}

void SubOperation::setOwner(Operation* o) {
  if (o == owner)
    // No change
    return;

  if (o && !o->hasSubOperations()) {
    // Some operation types don't have suboperations
    logger << "Warning: Operation '" << o << "' can't have suboperations"
           << endl;
    return;
  }

  // Remove from previous owner
  if (oper && owner) oper->owner = nullptr;
  if (owner) owner->getSubOperations().remove(this);

  // Update
  owner = o;

  // Insert at new owner
  if (oper && owner) oper->owner = owner;
  if (owner) {
    Operation::Operationlist::iterator iter = owner->getSubOperations().begin();
    while (iter != owner->getSubOperations().end() &&
           prio >= (*iter)->getPriority())
      ++iter;
    owner->getSubOperations().insert(iter, this);
  }
}

void SubOperation::setOperation(Operation* o) {
  if (o == oper) return;

  // Remove from previous oper
  if (oper && owner) oper->owner = nullptr;

  // Update
  oper = o;

  // Insert at new oper
  if (owner) oper->owner = owner;
}

void SubOperation::setPriority(int pr) {
  if (prio == pr) return;
  prio = pr;
  if (owner) {
    // Maintain the list in order of priority
    owner->getSubOperations().remove(this);
    Operation::Operationlist::iterator iter = owner->getSubOperations().begin();
    while (iter != owner->getSubOperations().end() &&
           prio >= (*iter)->getPriority())
      ++iter;
    owner->getSubOperations().insert(iter, this);
  }
}

PyObject* SubOperation::create(PyTypeObject* pytype, PyObject* args,
                               PyObject* kwds) {
  try {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds, "operation");
    if (!oper) throw DataException("Missing operation on SubOperation");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException(
          "field 'operation' of suboperation must be of type operation");

    // Pick up the owner
    PyObject* owner = PyDict_GetItemString(kwds, "owner");
    if (!owner) throw DataException("Missing owner on SubOperation");
    if (!PyObject_TypeCheck(owner, Operation::metadata->pythonClass))
      throw DataException(
          "field 'operation' of suboperation must be of type operation");

    // Pick up the type and create the suboperation
    SubOperation* l = new SubOperation();
    if (oper) l->setOperation(static_cast<Operation*>(oper));
    if (owner) l->setOwner(static_cast<Operation*>(owner));

    // Iterate over extra keywords, and set attributes.   @todo move this
    // responsibility to the readers...
    if (l) {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value)) {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::operation) && !attr.isA(Tags::owner) &&
            !attr.isA(Tags::type) && !attr.isA(Tags::action)) {
          const MetaFieldBase* fmeta =
              SubOperation::metacategory->findField(attr.getHash());
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
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

}  // namespace frepple
