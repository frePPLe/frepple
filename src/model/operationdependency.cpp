/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
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

#include "frepple/model.h"

namespace frepple {

const MetaCategory* OperationDependency::metacategory;
const MetaClass* OperationDependency::metadata;
const MetaCategory* OperationPlanDependency::metacategory;
const MetaClass* OperationPlanDependency::metadata;

int OperationPlanDependency::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<SubOperation>(
      "operationplandependency", "operationplandependency",
      MetaCategory::ControllerDefault);
  metadata = MetaClass::registerClass<OperationPlanDependency>(
      "operationplandependency", "operationplandependency", nullptr, true);
  registerFields<OperationPlanDependency>(
      const_cast<MetaCategory*>(metacategory));

  // Initialize the Python class
  auto& x = FreppleCategory<OperationPlanDependency>::getPythonType();
  x.setName("operationplandependency");
  x.setDoc("frePPLe operationplan dependency");
  x.supportgetattro();
  x.supportsetattro();
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  OperationPlanDependency::metadata->setPythonClass(x);
  return x.typeReady();
}

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
  auto& x = FreppleCategory<OperationDependency>::getPythonType();
  x.setName("operationdependency");
  x.setDoc("frePPLe operation dependency");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  OperationDependency::metadata->setPythonClass(x);
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
  if (oper && blockedby) {
    vector<const Operation*> path;
    if (!checkLoops(oper, path)) {
      blockedby->removeDependency(this);
      oper->removeDependency(this);
      oper = nullptr;
      blockedby = nullptr;
    }
  }
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
  if (oper && blockedby) {
    vector<const Operation*> path;
    if (!checkLoops(oper, path)) {
      blockedby->removeDependency(this);
      oper->removeDependency(this);
      oper = nullptr;
      blockedby = nullptr;
    }
  }
}

PyObject* OperationDependency::create(PyTypeObject*, PyObject*,
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
  for (auto& _ : dependencies) {
    (void)_;
    ++before_end;
  }
  dependencies.insert_after(before_end, dpd);
}

OperationPlanDependency::OperationPlanDependency(OperationPlan* op1,
                                                 OperationPlan* op2,
                                                 OperationDependency* d)
    : first(op1), second(op2), dpdcy(d) {
  initType(metadata);
  if (first) {
    first->dependencies.push_front(this);
    first->setChanged();
  }
  if (second) {
    second->dependencies.push_front(this);
    second->setChanged();
  }
}

OperationPlanDependency::~OperationPlanDependency() {
  if (first) first->dependencies.remove(this);
  if (second) second->dependencies.remove(this);
}

double OperationPlanDependency::getQuantity() const {
  // Assumes complete allocation of first or second operationplan
  if (!first || !second) return 0.0;
  double p = dpdcy ? second->getQuantity() * dpdcy->getQuantity()
                   : second->getQuantity();
  return min(p, first->getQuantity());
}

bool OperationDependency::checkLoops(const Operation* o,
                                     vector<const Operation*>& path) {
  auto found = find(path.begin(), path.end(), o);
  if (found != path.end()) {
    logger << "Data error: Ignoring looping blocked-by dependencies among:"
           << '\n';
    while (found != path.end()) {
      logger << "    " << *found << '\n';
      ++found;
    }
    logger << "    " << o << '\n';
    return false;
  }
  path.push_back(o);
  for (auto dpd : o->getDependencies()) {
    if (dpd->getOperation() != o) continue;
    // Recursive call
    if (!checkLoops(dpd->getBlockedBy(), path)) return false;
  }
  for (auto sub : o->getSubOperations()) {
    if (!checkLoops(sub->getOperation(), path)) return false;
  }
  if (path.back() != o) throw LogicException("Corrupt dependency loop check");
  path.pop_back();
  return true;
}

void OperationPlan::matchDependencies(bool log) {
  if (!getOperation() || getOperation()->getDependencies().empty() ||
      getCompleted() || getClosed())
    return;
  if (log) logger << "Scanning dependencies of " << this << '\n';
  for (auto dpd : getOperation()->getDependencies()) {
    if (dpd->getBlockedBy() == getOperation()) continue;
    auto needed = getQuantity() * dpd->getQuantity();
    auto o = dpd->getBlockedBy()->getOperationPlans();
    while (o != OperationPlan::end()) {
      if (getBatch() && o->getBatch() != getBatch()) {
        // No match
        ++o;
        continue;
      }
      auto unpegged = o->getQuantity();
      for (auto d : o->getDependencies()) {
        if (d->getFirst()->getOperation() != dpd->getOperation() ||
            d->getSecond()->getOperation() != getOperation()) {
          continue;
        }
        if (d->getOperationDependency())
          unpegged -= d->getSecond()->getQuantity() *
                      d->getOperationDependency()->getQuantity();
        else
          unpegged -= d->getSecond()->getQuantity();
      }
      if (unpegged > ROUNDING_ERROR) {
        new OperationPlanDependency(&*o, this, dpd);
        if (log) logger << "  Matching " << &*o << '\n';
        needed -= unpegged;
        if (needed < ROUNDING_ERROR) break;
      }
      ++o;
    }
    if (log && needed > ROUNDING_ERROR)
      logger << "  Unmatched " << needed << " on operation '"
             << dpd->getBlockedBy() << "'\n";
  }
}

}  // namespace frepple
