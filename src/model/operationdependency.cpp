/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
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

namespace frepple {

const MetaCategory* OperationDependency::metacategory;
const MetaClass* OperationDependency::metadata;

int OperationDependency::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SubOperation>(
      "operationdependency", "operationdependency",
      MetaCategory::ControllerDefault);
  metadata = MetaClass::registerClass<OperationDependency>(
      "operationdependency", "operationdependency",
      Object::create<OperationDependency>, true);
  registerFields<OperationDependency>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python class
  PythonType& x = FreppleCategory<OperationDependency>::getPythonType();
  x.setName("operationdependency");
  x.setDoc("frePPLe operation dependency");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(OperationDependency::metadata)->pythonClass =
      x.type_object();
  return x.typeReady();
}

OperationDependency::~OperationDependency() {
  if (blockedby) {
    blockedby->removeDependency(this);
    for (auto o = oper->getOperationPlans(); o != OperationPlan::end(); ++o) {
      for (auto d : o->dependencies) d->dpdcy = nullptr;
    }
  }
  if (oper) {
    oper->removeDependency(this);
    for (auto o = oper->getOperationPlans(); o != OperationPlan::end(); ++o) {
      for (auto d : o->dependencies) d->dpdcy = nullptr;
    }
  }
}

void OperationDependency::setOperation(Operation* o) {
  if (o == oper) return;
  if (oper && blockedby) oper->removeDependency(this);
  if (!oper && o) {
    oper = o;
    oper->addDependency(this);
    blockedby->addDependency(this);
  } else if (o && blockedby) {
    oper = o;
    oper->addDependency(this);
  } else if (blockedby)
    blockedby->removeDependency(this);
}

void OperationDependency::setBlockedBy(Operation* o) {
  if (o == blockedby) return;
  if (blockedby && oper) blockedby->removeDependency(this);
  if (!blockedby && o) {
    blockedby = o;
    blockedby->addDependency(this);
    oper->addDependency(this);
  } else if (o && oper) {
    blockedby = o;
    blockedby->addDependency(this);
  } else if (oper)
    oper->removeDependency(this);
}

PyObject* OperationDependency::create(PyTypeObject* pytype, PyObject* args,
                                      PyObject* kwds) {
  try {
    // Pick up the operation
    PyObject* oper = PyDict_GetItemString(kwds, "operation");
    if (!oper) throw DataException("Missing operation on SubOperation");
    if (!PyObject_TypeCheck(oper, Operation::metadata->pythonClass))
      throw DataException(
          "field 'operation' of operationdependency must be of type operation");

    // Pick up the owner
    PyObject* blockedby = PyDict_GetItemString(kwds, "blockedby");
    if (!blockedby)
      throw DataException("Missing blockedby on operationdependency");
    if (!PyObject_TypeCheck(blockedby, Operation::metadata->pythonClass))
      throw DataException(
          "field 'blockedby' of operationdependency must be of type operation");

    // Pick up the type and create the dependency
    auto l = new OperationDependency();
    if (oper) l->setOperation(static_cast<Operation*>(oper));
    if (blockedby) l->setBlockedBy(static_cast<Operation*>(blockedby));

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
        if (!attr.isA(Tags::operation) && !attr.isA(Tags::blockedby) &&
            !attr.isA(Tags::type) && !attr.isA(Tags::action)) {
          const MetaFieldBase* fmeta =
              OperationDependency::metacategory->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(l, field);
          else
            l->setProperty(attr.getName(), value);
        }
      }
    }

    // Return the object
    Py_INCREF(l);
    return static_cast<PyObject*>(l);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

void Operation::addDependency(OperationDependency* dpd) {
  if (!dpd->getOperation() || !dpd->getBlockedBy()) return;
  for (auto& iter : dependencies) {
    if (iter->getOperation() == dpd->getOperation() &&
        iter->getBlockedBy() == dpd->getBlockedBy())
      throw DataException("Duplicate dependency between '" +
                          iter->getOperation()->getName() + "' and '" +
                          iter->getBlockedBy()->getName() + "'");
  }
  // Insert at the end of the list. Scales O(n).
  auto before_end = dependencies.before_begin();
  for (auto& _ : dependencies) ++before_end;
  dependencies.insert_after(before_end, dpd);
}

OperationPlanDependency::OperationPlanDependency(OperationPlan* blckby,
                                                 OperationPlan* blckng,
                                                 OperationDependency* d)
    : blockedby(blckby), blocking(blckng), dpdcy(d) {
  if (blockedby) blockedby->dependencies.push_front(this);
  if (blocking) blocking->dependencies.push_front(this);
}

OperationPlanDependency::~OperationPlanDependency() {
  if (blockedby) blockedby->dependencies.remove(this);
  if (blocking) blocking->dependencies.remove(this);
}

}  // namespace frepple