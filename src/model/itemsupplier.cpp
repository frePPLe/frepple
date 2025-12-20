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

#include "frepple/model.h"

namespace frepple {

const MetaCategory* ItemSupplier::metacategory;
const MetaClass* ItemSupplier::metadata;
const MetaClass* OperationItemSupplier::metadata;

int ItemSupplier::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<ItemSupplier>(
      "itemsupplier", "itemsuppliers",
      Association<Supplier, Item, ItemSupplier>::reader, finder);
  metadata = MetaClass::registerClass<ItemSupplier>(
      "itemsupplier", "itemsupplier", Object::create<ItemSupplier>, true);
  registerFields<ItemSupplier>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleCategory<ItemSupplier>::getPythonType();
  x.setName("itemsupplier");
  x.setDoc("frePPLe itemsupplier");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  ItemSupplier::metadata->setPythonClass(x);
  return x.typeReady();
}

ItemSupplier::~ItemSupplier() {
  // Delete the association from the related objects
  if (getSupplier()) getSupplier()->items.erase(this);
  if (getItem()) getItem()->suppliers.erase(this);

  // Delete all owned purchase operations
  while (firstOperation) delete firstOperation;

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}

ItemSupplier::ItemSupplier() {
  initType(metadata);

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}

ItemSupplier::ItemSupplier(Supplier* s, Item* r, int u) {
  setSupplier(s);
  setItem(r);
  setPriority(u);
  initType(metadata);

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}

ItemSupplier::ItemSupplier(Supplier* s, Item* r, int u, const DateRange& e) {
  setSupplier(s);
  setItem(r);
  setPriority(u);
  setEffective(e);
  initType(metadata);

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}

PyObject* ItemSupplier::create(PyTypeObject* pytype, PyObject* args,
                               PyObject* kwds) {
  try {
    // Pick up the supplier
    PyObject* sup = PyDict_GetItemString(kwds, "supplier");
    if (!sup) throw DataException("missing supplier on ItemSupplier");
    if (!PyObject_TypeCheck(sup, Supplier::metadata->pythonClass))
      throw DataException("ItemSupplier supplier must be of type supplier");

    // Pick up the item
    PyObject* it = PyDict_GetItemString(kwds, "item");
    if (!it) throw DataException("missing item on ItemSupplier");
    if (!PyObject_TypeCheck(it, Item::metadata->pythonClass))
      throw DataException("ItemSupplier item must be of type item");

    // Pick up the priority
    PyObject* q1 = PyDict_GetItemString(kwds, "priority");
    int q2 = q1 ? PythonData(q1).getInt() : 1;

    // Pick up the effective dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds, "effective_start");
    if (eff_start) {
      PythonData d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds, "effective_end");
    if (eff_end) {
      PythonData d(eff_end);
      eff.setEnd(d.getDate());
    }

    // Create the ItemSupplier
    auto* l = new ItemSupplier(static_cast<Supplier*>(sup),
                               static_cast<Item*>(it), q2, eff);

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
        if (!attr.isA(Tags::effective_end) &&
            !attr.isA(Tags::effective_start) && !attr.isA(Tags::supplier) &&
            !attr.isA(Tags::item) && !attr.isA(Tags::type) &&
            !attr.isA(Tags::priority) && !attr.isA(Tags::action)) {
          const MetaFieldBase* fmeta = l->getType().findField(attr.getHash());
          if (!fmeta && l->getType().category)
            fmeta = l->getType().category->findField(attr.getHash());
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

void ItemSupplier::deleteOperationPlans(bool b) {
  for (auto i = firstOperation; i; i = i->nextOperation)
    i->deleteOperationPlans(b);
}

int OperationItemSupplier::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationItemSupplier>(
      "operation", "operation_itemsupplier");
  registerFields<OperationItemSupplier>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleCategory<OperationItemSupplier>::getPythonType();
  x.setName("operation_itemsupplier");
  x.setDoc("frePPLe operation_itemsupplier");
  x.supportgetattro();
  x.supportsetattro();
  x.addMethod("decoupledLeadTime", &getDecoupledLeadTimePython, METH_VARARGS,
              "return the total lead time");
  x.addMethod("setFence", &setFencePython, METH_VARARGS,
              "Update the fence based on date");
  x.addMethod("getFence", &getFencePython, METH_NOARGS,
              "Retrieve the fence date");
  metadata->setPythonClass(x);
  return x.typeReady();
}

OperationItemSupplier* OperationItemSupplier::findOrCreate(ItemSupplier* i,
                                                           Buffer* b) {
  if (!i || !b || !i->getSupplier())
    throw LogicException(
        "An OperationItemSupplier always needs to point to "
        "a itemsupplier and a buffer");
  stringstream o;
  o << "Purchase " << b->getName() << " from " << i->getSupplier()->getName();
  if (i->getEffectiveStart()) o << " valid from " << i->getEffectiveStart();
  Operation* oper = Operation::find(o.str());
  if (oper) {
    // Reuse existing operation
    if (oper->hasType<OperationItemSupplier>())
      return static_cast<OperationItemSupplier*>(oper);
    else
      throw DataException(
          "Unexpected operation type for item supplier operation");
  } else
    // Create new operation
    return new OperationItemSupplier(i, b);
}

OperationItemSupplier::OperationItemSupplier(ItemSupplier* i, Buffer* b)
    : supitem(i) {
  if (!i || !b || !i->getSupplier())
    throw LogicException(
        "An OperationItemSupplier always needs to point to "
        "a itemsupplier and a buffer");
  stringstream o;
  o << "Purchase " << b->getName() << " from " << i->getSupplier()->getName();
  if (i->getEffectiveStart()) o << " valid from " << i->getEffectiveStart();
  setName(o.str());
  setDuration(i->getLeadTime());
  setSizeMultiple(i->getSizeMultiple());
  setSizeMinimum(i->getSizeMinimum());
  setSizeMaximum(i->getSizeMaximum());
  setBatchWindow(i->getBatchWindow());
  setPostTime(i->getExtraSafetyLeadTime());
  setSource(i->getSource());
  setCost(i->getCost());
  setFence(i->getFence());
  setHidden(true);
  auto fl = new FlowEnd(this, b, 1);
  fl->setOffset(i->getHardSafetyLeadTime());
  initType(metadata);

  // Optionally, link with a supplier location and related availability
  // calendar. A location must exist with the same name as the supplier.
  auto supplierLocation = Location::find(i->getSupplier()->getName());
  if (supplierLocation) setLocation(supplierLocation);

  // Optionally, create a load
  if (i->getResource())
    new LoadDefault(this, i->getResource(), i->getResourceQuantity());

  // Insert in the list of ItemSupplier operations.
  // The list is not sorted (for performance reasons).
  nextOperation = i->firstOperation;
  i->firstOperation = this;
}

OperationItemSupplier::~OperationItemSupplier() {
  // Remove from the list of operations of this supplier item
  if (supitem) {
    if (supitem->firstOperation == this) {
      // We were at the head
      supitem->firstOperation = nextOperation;
    } else {
      // We were in the middle
      OperationItemSupplier* i = supitem->firstOperation;
      while (i->nextOperation != this && i->nextOperation) i = i->nextOperation;
      if (!i)
        logger << "Error: ItemSupplier operation list corrupted\n";
      else
        i->nextOperation = nextOperation;
    }
  }
}

Buffer* OperationItemSupplier::getBuffer() const {
  return getFlows().begin()->getBuffer();
}

void OperationItemSupplier::trimExcess(bool zero_or_minimum) const {
  // This method can only trim operations not loading a resource
  if (getLoads().begin() != getLoads().end()) return;

  for (const auto& fliter : getFlows()) {
    if (fliter.getQuantity() <= 0)
      // Strange, shouldn't really happen
      continue;
    FlowPlan* candidate = nullptr;
    double curmin = 0;
    double oh = 0;
    double excess_min = DBL_MAX;

    for (auto flplniter = fliter.getBuffer()->getFlowPlans().begin();
         flplniter != fliter.getBuffer()->getFlowPlans().end(); ++flplniter) {
      // For any operationplan we get the onhand when its successor
      // replenishment arrives. If that onhand is higher than the minimum
      // onhand value we can resize it.
      // This is only valid in unconstrained plans and when there are
      // no upstream activities.
      if (flplniter->getEventType() == 3 && zero_or_minimum)
        curmin = flplniter->getMin();
      else if (flplniter->getEventType() == 1) {
        const auto* flpln = static_cast<const FlowPlan*>(&*flplniter);
        if (oh - curmin < excess_min) {
          excess_min = oh - curmin;
          if (excess_min < 0) excess_min = 0;
        }
        if (flpln->getQuantity() > 0 &&
            flpln->getOperationPlan()->getProposed() &&
            (!candidate || candidate->getDate() != flpln->getDate())) {
          if (candidate && excess_min > ROUNDING_ERROR &&
              candidate->getQuantity() > excess_min + ROUNDING_ERROR &&
              candidate->getQuantity() > getSizeMinimum() + ROUNDING_ERROR) {
            // This candidate can now be resized
            candidate->setQuantity(candidate->getQuantity() - excess_min,
                                   false);
            candidate = nullptr;
          } else if (flpln->getOperation() == this)
            candidate = const_cast<FlowPlan*>(flpln);
          else
            candidate = nullptr;
          excess_min = DBL_MAX;
        }
      }
      oh = flplniter->getOnhand();
    }
    if (candidate && excess_min > ROUNDING_ERROR &&
        candidate->getQuantity() > excess_min + ROUNDING_ERROR &&
        candidate->getQuantity() > getSizeMinimum() + ROUNDING_ERROR)
      // Resize the last candidate at the end of the horizon
      candidate->setQuantity(candidate->getQuantity() - excess_min, false);
  }
}

Object* ItemSupplier::finder(const DataValueDict& d) {
  // Check item
  const DataValue* tmp = d.get(Tags::item);
  if (!tmp) return nullptr;
  Item* item = static_cast<Item*>(tmp->getObject());

  // Check supplier field
  tmp = d.get(Tags::supplier);
  if (!tmp) return nullptr;
  auto* sup = static_cast<Supplier*>(tmp->getObject());

  // Walk over all suppliers of the item, and return
  // the first one with matching
  const DataValue* hasEffectiveStart = d.get(Tags::effective_start);
  Date effective_start;
  if (hasEffectiveStart) effective_start = hasEffectiveStart->getDate();
  const DataValue* hasEffectiveEnd = d.get(Tags::effective_end);
  Date effective_end;
  if (hasEffectiveEnd) effective_end = hasEffectiveEnd->getDate();
  const DataValue* hasPriority = d.get(Tags::priority);
  int priority;
  if (hasPriority) priority = hasPriority->getInt();
  for (const auto& fl : item->getSuppliers()) {
    if (fl.getSupplier() != sup) continue;
    if (hasEffectiveStart && fl.getEffectiveStart() != effective_start)
      continue;
    if (hasEffectiveEnd && fl.getEffectiveEnd() != effective_end) continue;
    if (hasPriority && fl.getPriority() != priority) continue;
    return const_cast<ItemSupplier*>(&fl);
  }
  return nullptr;
}

}  // namespace frepple
