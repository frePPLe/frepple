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

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple {

template <class Demand>
Tree utils::HasName<Demand>::st;
const MetaCategory* Demand::metadata;
const MetaClass* DemandDefault::metadata;
const MetaClass* DemandGroup::metadata;

OperationFixedTime* Demand::uninitializedDelivery = nullptr;
Duration Demand::DefaultDeliveryDuration = 0L;

int Demand::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Demand>("demand", "demands", reader,
                                                    finder);
  registerFields<Demand>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  auto& x = FreppleCategory<Demand>::getPythonType();
  x.addMethod("addConstraint", addConstraint, METH_VARARGS,
              "add a constraint to the demand");

  uninitializedDelivery = new OperationFixedTime();

  // Initialize the Python class
  return FreppleCategory<Demand>::initialize();
}

int DemandDefault::initialize() {
  // Initialize the metadata
  DemandDefault::metadata = MetaClass::registerClass<DemandDefault>(
      "demand", "demand_default", Object::create<DemandDefault>, true);
  registerFields<DemandDefault>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<DemandDefault, Demand>::initialize();
}

int DemandGroup::initialize() {
  // Initialize the metadata
  DemandGroup::metadata = MetaClass::registerClass<DemandGroup>(
      "demand", "demand_group", Object::create<DemandGroup>);
  registerFields<DemandGroup>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<DemandGroup, Demand>::initialize();
}

void Demand::setQuantity(double f) {
  // Reject negative quantities, and no-change updates
  double delta(f - qty);
  if (f < 0.0 || fabs(delta) < ROUNDING_ERROR) return;

  // Update the quantity
  qty = f;
}

Demand::~Demand() {
  // Remove the delivery operationplans
  deleteOperationPlans(true);

  // Unlink from the item
  if (it) {
    if (it->firstItemDemand == this)
      it->firstItemDemand = nextItemDemand;
    else {
      Demand* dmd = it->firstItemDemand;
      while (dmd && dmd->nextItemDemand != this) dmd = dmd->nextItemDemand;
      if (!dmd)
        logger << "corrupted demand list for an item" << endl;
      else
        dmd->nextItemDemand = nextItemDemand;
    }
  }

  // Decrement demand count on the customer
  if (cust) cust->decNumberOfDemands();
}

void Demand::deleteOperationPlans(bool deleteLocked, CommandManager* cmds) {
  // Delete all delivery operationplans.
  // Note that an extra loop is used to assure that our iterator doesn't get
  // invalidated during the deletion.
  while (true) {
    // Find a candidate to delete
    OperationPlan* candidate = nullptr;
    for (auto i = deli.begin(); i != deli.end(); ++i)
      if (deleteLocked || (*i)->getProposed()) {
        candidate = *i;
        break;
      }
    if (!candidate) break;
    if (cmds)
      // Use delete command
      cmds->add(new CommandDeleteOperationPlan(candidate));
    else
      // Delete immediately
      delete candidate;
  }
}

void Demand::removeDelivery(OperationPlan* o) {
  // Valid opplan check
  if (!o) return;

  // See if the demand field on the operationplan points to this demand
  if (o->dmd != this)
    throw LogicException("Delivery operationplan incorrectly registered");

  // Remove the reference on the operationplan
  o->dmd = nullptr;  // Required to avoid endless loop
  o->setDemand(nullptr);

  // Remove from the list
  deli.remove(o);
}

const Demand::OperationPlanList& Demand::getDelivery() const {
  // Sorting the deliveries by the end date
  const_cast<Demand*>(this)->deli.sort(
      [](OperationPlan*& lhs, OperationPlan*& rhs) {
        return lhs->getEnd() != rhs->getEnd() ? lhs->getEnd() > rhs->getEnd()
                                              : *lhs < *rhs;
      });
  return deli;
}

OperationPlan* Demand::getLatestDelivery() const {
  const Demand::OperationPlanList& l = getDelivery();
  return l.empty() ? nullptr : *(l.begin());
}

OperationPlan* Demand::getEarliestDelivery() const {
  const Demand::OperationPlanList& l = getDelivery();
  OperationPlan* last = nullptr;
  for (auto i = l.begin(); i != l.end(); ++i) last = *i;
  return last;
}

void Demand::addDelivery(OperationPlan* o) {
  // Dummy call to this function
  if (!o) return;

  // Check if it is already in the list.
  // If it is, simply exit the function. No need to give a warning message
  // since it's harmless.
  for (auto i = deli.begin(); i != deli.end(); ++i)
    if (*i == o) return;

  // Add to the list of delivery operationplans.
  deli.push_front(o);

  // Create link between operationplan and demand
  o->setDemand(this);

  // Check validity of operation being used
  Operation* tmpOper = getDeliveryOperation();
  if (tmpOper && tmpOper != o->getOperation())
    logger << "Warning: Delivery Operation '" << o->getOperation()
           << "' different than expected '" << tmpOper << "' for demand '"
           << this << "'" << endl;
}

Operation* Demand::getDeliveryOperation() const {
  // Case 1: Operation specified on the demand itself,
  // or the delivery operation was computed earlier.
  if (oper && oper != uninitializedDelivery) return oper;

  // Case 2: Create a delivery operation automatically
  if (!getItem()) {
    // Not possible to create an operation when we don't know the item
    const_cast<Demand*>(this)->oper = nullptr;
    return nullptr;
  }
  Location* l = getLocation();
  if (!l) {
    // Single location only?
    Location::iterator l_iter = Location::begin();
    if (l_iter != Location::end()) {
      l = &*l_iter;
      if (++l_iter != Location::end())
        // No, multiple locations
        l = nullptr;
    }
  }
  if (l) {
    // Search for buffers for the requested item and location.
    // We want the generic buffer, and not any of the mto-buffers.
    bool ok = true;
    Buffer* buf = nullptr;
    Item::bufferIterator buf_iter(getItem());
    while (Buffer* tmpbuf = buf_iter.next()) {
      if (tmpbuf->getLocation() == l && !tmpbuf->getBatch()) {
        if (buf) {
          // Second buffer found. We don't know which one to pick - abort.
          ok = false;
          break;
        } else
          buf = tmpbuf;
      }
    }

    if (ok) {
      if (!buf)
        // Create a new buffer
        buf = Buffer::findOrCreate(getItem(), l);

      // Find an existing operation consuming from this buffer
      const_cast<Demand*>(this)->oper =
          Operation::find("Ship " + string(buf->getName()));
      if (!oper) {
        const_cast<Demand*>(this)->oper = new OperationDelivery();
        static_cast<OperationDelivery*>(const_cast<Demand*>(this)->oper)
            ->setBuffer(buf);
      }

      // Success!
      return oper;
    }
  }

  // Case 4: Tough luck. Not possible to ship this demand.
  const_cast<Demand*>(this)->oper = nullptr;
  return nullptr;
}

double Demand::getPlannedQuantity() const {
  double delivered(0.0);
  for (auto i = deli.begin(); i != deli.end(); ++i)
    delivered += (*i)->getQuantity();
  return delivered;
}

PyObject* Demand::addConstraint(PyObject* self, PyObject* args,
                                PyObject* kwds) {
  try {
    // Pick up the demand
    Demand* dmd = static_cast<Demand*>(self);
    if (!dmd) throw LogicException("Can't add a contraint to a null demand");

    // Parse the arguments
    char* pytype = nullptr;
    char* pyowner = nullptr;
    PyObject* pystart = nullptr;
    PyObject* pyend = nullptr;
    double cnstrnt_weight = 0;
    static const char* kwlist[] = {"type", "owner",  "start",
                                   "end",  "weight", nullptr};
    if (!PyArg_ParseTupleAndKeywords(
            args, kwds, "ss|OOd:addConstraint", const_cast<char**>(kwlist),
            &pytype, &pyowner, &pystart, &pyend, &cnstrnt_weight))
      return nullptr;
    string cnstrnt_type;
    if (pytype) cnstrnt_type = pytype;
    string cnstrnt_owner;
    if (pyowner) cnstrnt_owner = pyowner;
    Date cnstrnt_start = Date::infinitePast;
    if (pystart) cnstrnt_start = PythonData(pystart).getDate();
    Date cnstrnt_end = Date::infiniteFuture;
    if (pyend) cnstrnt_end = PythonData(pyend).getDate();

    // Add the new constraint
    Problem* cnstrnt = nullptr;
    if (cnstrnt_type == ProblemBeforeCurrent::metadata->type) {
      Operation* obj = Operation::findFromName(cnstrnt_owner);
      if (!obj) throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemBeforeCurrent::metadata, obj,
                                           cnstrnt_start, cnstrnt_end,
                                           cnstrnt_weight);
    } else if (cnstrnt_type == ProblemCapacityOverload::metadata->type) {
      Resource* obj = Resource::find(cnstrnt_owner);
      if (!obj) throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemCapacityOverload::metadata,
                                           obj, cnstrnt_start, cnstrnt_end,
                                           cnstrnt_weight);
    } else if (cnstrnt_type == ProblemMaterialShortage::metadata->type) {
      Buffer* obj = Buffer::findFromName(cnstrnt_owner);
      if (!obj) throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemMaterialShortage::metadata,
                                           obj, cnstrnt_start, cnstrnt_end,
                                           cnstrnt_weight);
    } else if (cnstrnt_type == ProblemAwaitSupply::metadata->type) {
      Buffer* obj_buffer = Buffer::findFromName(cnstrnt_owner);
      if (obj_buffer)
        cnstrnt = dmd->getConstraints().push(ProblemAwaitSupply::metadata,
                                             obj_buffer, cnstrnt_start,
                                             cnstrnt_end, cnstrnt_weight);
      else {
        Operation* obj_operation = Operation::findFromName(cnstrnt_owner);
        if (obj_operation)
          cnstrnt = dmd->getConstraints().push(ProblemAwaitSupply::metadata,
                                               obj_operation, cnstrnt_start,
                                               cnstrnt_end, cnstrnt_weight);
        else
          throw DataException("Can't find constraint owner");
      }
    } else if (cnstrnt_type == ProblemSyncDemand::metadata->type) {
      Demand* obj = Demand::find(cnstrnt_owner);
      if (!obj) throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemSyncDemand::metadata, obj,
                                           cnstrnt_start, cnstrnt_end,
                                           cnstrnt_weight);
    } else
      throw DataException("Invalid constraint type");
    Py_IncRef(cnstrnt);
    return cnstrnt;
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

PeggingIterator Demand::getPegging() const { return PeggingIterator(this); }

PeggingIterator Demand::getPeggingFirstLevel() const {
  return PeggingIterator(this, 0);
}

Problem::List::iterator Demand::getConstraintIterator() const {
  return constraints.begin();
}

int DemandGroup::getPriority() const {
  int lowest = INT_MAX;
  for (auto m = getMembers(); m != end(); ++m) {
    if (m->getPriority() < lowest) lowest = m->getPriority();
  };
  return lowest;
}

void DemandGroup::setPriority(int i) {
  Demand::setPriority(i);
  for (auto m = getMembers(); m != end(); ++m) m->setPriority(i);
}

Date DemandGroup::getDue() const {
  auto latest = Date::infiniteFuture;
  for (auto m = getMembers(); m != end(); ++m) {
    if (m->getDue() < latest) latest = m->getDue();
  };
  return latest;
}

void DemandGroup::setDue(Date d) {
  for (auto m = getMembers(); m != end(); ++m) m->setDue(d);
}

}  // namespace frepple
