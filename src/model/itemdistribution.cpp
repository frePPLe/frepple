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

const MetaCategory* ItemDistribution::metacategory;
const MetaClass* ItemDistribution::metadata;
const MetaClass* OperationItemDistribution::metadata;

int ItemDistribution::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<ItemDistribution>(
      "itemdistribution", "itemdistributions",
      Association<Location, Location, ItemDistribution>::reader, finder);
  metadata = MetaClass::registerClass<ItemDistribution>(
      "itemdistribution", "itemdistribution", Object::create<ItemDistribution>,
      true);
  registerFields<ItemDistribution>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleCategory<ItemDistribution>::getPythonType();
  x.setName("itemdistribution");
  x.setDoc("frePPLe itemdistribution");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  metadata->setPythonClass(x);
  return x.typeReady();
}

ItemDistribution::ItemDistribution() {
  initType(metadata);

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}

ItemDistribution::~ItemDistribution() {
  // Delete the association from the related objects
  if (getItem()) getItem()->distributions.erase(this);
  if (getDestination()) getDestination()->distributions.erase(this);

  // Delete all owned distribution operations
  while (firstOperation) delete firstOperation;

  // Trigger level and cluster recomputation
  HasLevel::triggerLazyRecomputation();
}

PyObject* ItemDistribution::create(PyTypeObject* pytype, PyObject* args,
                                   PyObject* kwds) {
  try {
    // Pick up the item
    PyObject* it = PyDict_GetItemString(kwds, "item");
    if (!it) throw DataException("missing item on ItemDistribution");
    if (!PyObject_TypeCheck(it, Item::metadata->pythonClass))
      throw DataException("ItemDistribution item must be of type item");

    /* XXX
    // Pick up the priority
    PyObject* q1 = PyDict_GetItemString(kwds,"priority");
    int q2 = q1 ? PythonData(q1).getInt() : 1;

    // Pick up the effective dates
    DateRange eff;
    PyObject* eff_start = PyDict_GetItemString(kwds,"effective_start");
    if (eff_start)
    {
      PythonData d(eff_start);
      eff.setStart(d.getDate());
    }
    PyObject* eff_end = PyDict_GetItemString(kwds,"effective_end");
    if (eff_end)
    {
      PythonData d(eff_end);
      eff.setEnd(d.getDate());
    }
    */

    // Create the ItemDistribution
    auto* l = new ItemDistribution();
    l->setItem(static_cast<Item*>(it));

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
        if (!attr.isA(Tags::item) && !attr.isA(Tags::type) &&
            !attr.isA(Tags::action)) {
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

void ItemDistribution::setItem(Item* i) {
  if (!i) return;
  setPtrB(i, i->getDistributions());
  HasLevel::triggerLazyRecomputation();
}

void ItemDistribution::deleteOperationPlans(bool b) {
  for (OperationItemDistribution* i = firstOperation; i; i = i->nextOperation)
    i->deleteOperationPlans(b);
}

int OperationItemDistribution::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationItemDistribution>(
      "operation", "operation_itemdistribution");
  registerFields<OperationItemDistribution>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleCategory<OperationItemDistribution>::getPythonType();
  x.setName("operation_itemdistribution");
  x.setDoc("frePPLe operation_itemdistribution");
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

Operation* OperationItemDistribution::findOrCreate(ItemDistribution* i,
                                                   Buffer* src, Buffer* dest) {
  if (!i || !src || !dest)
    throw LogicException(
        "An OperationItemDistribution always needs to point to "
        "a ItemDistribution, a source buffer and a destination buffer");
  if (dest == src)
    throw LogicException(
        "Source and destination of an OperationItemDistribution must be "
        "different");
  stringstream o;
  o << "Ship " << dest->getItem()->getName();
  if (src->getBatch())
    o << " @ " << src->getBatch();
  else if (dest->getBatch())
    o << " @ " << dest->getBatch();
  o << " from " << src->getLocation()->getName() << " to "
    << dest->getLocation()->getName();
  if (i->getEffectiveStart()) o << " valid from " << i->getEffectiveStart();
  auto oper = Operation::find(o.str());
  if (oper) {
    if (!oper->hasType<OperationItemDistribution>())
      throw DataException("Name clash on operation " + o.str());
    return oper;
  } else
    return new OperationItemDistribution(i, src, dest);
}

OperationItemDistribution::OperationItemDistribution(ItemDistribution* i,
                                                     Buffer* src, Buffer* dest)
    : itemdist(i) {
  if (!i)
    throw LogicException(
        "An OperationItemDistribution always needs to point to an "
        "ItemDistribution");
  if (!dest && !src)
    throw LogicException(
        "An OperationItemDistribution always needs to point to a destination "
        "and/or a source buffer");
  if (dest == src)
    throw LogicException(
        "Source and destination of an OperationItemDistribution must be "
        "different");
  stringstream o;
  auto item = dest ? dest->getItem() : src->getItem();
  o << "Ship " << item->getName();
  if (src && src->getBatch())
    o << " @ " << src->getBatch();
  else if (dest && dest->getBatch())
    o << " @ " << dest->getBatch();
  if (src && src->getLocation()) o << " from " << src->getLocation()->getName();
  if (dest && dest->getLocation())
    o << " to " << dest->getLocation()->getName();
  if (i->getEffectiveStart()) o << " valid from " << i->getEffectiveStart();
  setName(o.str());
  setDuration(i->getLeadTime());
  setSizeMultiple(i->getSizeMultiple());
  setSizeMinimum(i->getSizeMinimum());
  setSizeMaximum(i->getSizeMaximum());
  setLocation(dest ? dest->getLocation() : src->getLocation());
  setSource(i->getSource());
  setCost(i->getCost());
  setFence(i->getFence());
  setBatchWindow(i->getBatchWindow());
  setHidden(true);
  if (dest) new FlowEnd(this, dest, 1);
  if (src) new FlowStart(this, src, -1);
  initType(metadata);

  // Optionally, create a load
  if (i->getResource())
    new LoadDefault(this, i->getResource(), i->getResourceQuantity());

  // Insert in the list of ItemDistribution operations.
  // The list is not sorted (for performance reasons).
  nextOperation = i->firstOperation;
  const_cast<ItemDistribution*>(i)->firstOperation = this;
}

OperationItemDistribution::~OperationItemDistribution() {
  // Remove from the list of operations of this item distribution
  if (itemdist) {
    if (itemdist->firstOperation == this) {
      // We were at the head
      itemdist->firstOperation = nextOperation;
    } else {
      // We were in the middle
      OperationItemDistribution* i = itemdist->firstOperation;
      while (i->nextOperation != this && i->nextOperation) i = i->nextOperation;
      if (!i)
        logger << "Error: ItemDistribution operation list corrupted" << endl;
      else
        i->nextOperation = nextOperation;
    }
  }
}

Buffer* OperationItemDistribution::getOrigin() const {
  for (const auto & i : getFlows())
    if (i.getQuantity() < 0.0) return i.getBuffer();
  return nullptr;
}

Buffer* OperationItemDistribution::getDestination() const {
  for (const auto & i : getFlows())
    if (i.getQuantity() > 0.0) return i.getBuffer();
  return nullptr;
}

Object* ItemDistribution::finder(const DataValueDict& d) {
  // Check item field
  const DataValue* tmp = d.get(Tags::item);
  if (!tmp) return nullptr;
  Item* item = static_cast<Item*>(tmp->getObject());

  // Check origin field
  tmp = d.get(Tags::origin);
  if (!tmp) return nullptr;
  Location* origin = tmp ? static_cast<Location*>(tmp->getObject()) : nullptr;

  // Check destination field
  tmp = d.get(Tags::destination);
  if (!tmp) return nullptr;
  auto* destination = static_cast<Location*>(tmp->getObject());

  // Walk over all suppliers of the item, and return
  // the first one with matching
  const DataValue* hasEffectiveStart = d.get(Tags::effective_start);
  Date effective_start;
  if (hasEffectiveStart) effective_start = hasEffectiveStart->getDate();
  const DataValue* hasEffectiveEnd = d.get(Tags::effective_end);
  Date effective_end;
  if (hasEffectiveEnd) effective_end = hasEffectiveEnd->getDate();
  const DataValue* hasPriority = d.get(Tags::priority);
  int priority = 0;
  if (hasPriority) priority = hasPriority->getInt();
  auto itemdist_iter = item->getDistributionIterator();
  while (ItemDistribution* i = itemdist_iter.next()) {
    if (i->getOrigin() != origin) continue;
    if (i->getDestination() != destination) continue;
    if (hasEffectiveStart && i->getEffectiveStart() != effective_start)
      continue;
    if (hasEffectiveEnd && i->getEffectiveEnd() != effective_end) continue;
    if (hasPriority && i->getPriority() != priority) continue;
    return const_cast<ItemDistribution*>(&*i);
  }
  return nullptr;
}

}  // namespace frepple
