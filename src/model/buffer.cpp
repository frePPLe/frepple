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
#include <math.h>

#include "frepple/model.h"

namespace frepple {

template <class Buffer>
Tree utils::HasName<Buffer>::st;
const MetaCategory* Buffer::metadata;
const MetaClass *BufferDefault::metadata, *BufferInfinite::metadata,
    *OperationInventory::metadata, *OperationDelivery::metadata;
OperationFixedTime* Buffer::uninitializedProducing = nullptr;
Duration OperationDelivery::deliveryduration = 0L;

int Buffer::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Buffer>("buffer", "buffers", reader,
                                                    finder);
  registerFields<Buffer>(const_cast<MetaCategory*>(metadata));

  uninitializedProducing = new OperationFixedTime();

  // Initialize the Python class
  auto& x = FreppleCategory<Buffer>::getPythonType();
  x.addMethod("decoupledLeadTime", &getDecoupledLeadTimePython, METH_VARARGS,
              "return the decoupled lead time");
  x.addMethod("availableonhand", &availableOnhandPython, METH_VARARGS,
              "return the available onhand at a specific date");
  x.addMethod("inspect", inspectPython, METH_VARARGS,
              "debugging function to print the inventory profile");
  return FreppleCategory<Buffer>::initialize();
}

int BufferDefault::initialize() {
  // Initialize the metadata
  BufferDefault::metadata = MetaClass::registerClass<BufferDefault>(
      "buffer", "buffer_default", Object::create<BufferDefault>, true);

  // Initialize the Python class
  return FreppleClass<BufferDefault, Buffer>::initialize();
}

int BufferInfinite::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<BufferInfinite>(
      "buffer", "buffer_infinite", Object::create<BufferInfinite>);

  // Initialize the Python class
  return FreppleClass<BufferInfinite, Buffer>::initialize();
}

int OperationInventory::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationInventory>(
      "operation", "operation_inventory");
  registerFields<OperationInventory>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleCategory<OperationInventory>::getPythonType();
  x.setName("operation_inventory");
  x.setDoc("frePPLe operation_inventory");
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

int OperationDelivery::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<OperationDelivery>(
      "operation", "operation_delivery", Object::create<OperationDelivery>);
  registerFields<OperationDelivery>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = PythonExtension<
      FreppleClass<OperationDelivery, Operation>>::getPythonType();
  x.addMethod("decoupledLeadTime", &getDecoupledLeadTimePython, METH_VARARGS,
              "return the total lead time");
  x.addMethod("setFence", &setFencePython, METH_VARARGS,
              "Update the fence based on date");
  x.addMethod("getFence", &getFencePython, METH_NOARGS,
              "Retrieve the fence date");
  return FreppleClass<OperationDelivery, Operation>::initialize();
}

OperationDelivery::OperationDelivery() {
  setHidden(true);
  setDetectProblems(false);
  // When we set the size minimum to 0 for the automatically created
  // delivery operations, they will be constrained by the minimum shipment
  // size specified on the demand.
  setSizeMinimum(0.0);
  initType(metadata);
  setDuration(deliveryduration);
}

void OperationDelivery::setBuffer(Buffer* buf) {
  // Validate the input
  if (getBuffer() == buf)
    return;
  else if (!buf)
    throw DataException("A delivery operation can't point to a null buffer");
  else if (getBuffer())
    throw DataException("Buffer can be set only once on a delivery operation");

  // Update the operation
  setName("Ship " + string(buf->getName()));
  setLocation(buf->getLocation());

  // Add a flow consuming from the buffer
  new FlowStart(this, buf, -1);
}

Buffer* OperationDelivery::getBuffer() const {
  auto tmp = getFlows().begin();
  return tmp == getFlows().end() ? nullptr : tmp->getBuffer();
}

void Buffer::inspect(const string& msg, const short i) const {
  indent indentstring(i);
  logger << indentstring << "  Inspecting buffer " << getName() << ": ";
  if (!msg.empty()) logger << msg;
  logger << endl;

  double curmin = 0.0;
  double curmax = 0.0;
  for (auto oo = getFlowPlans().begin(); oo != getFlowPlans().end(); ++oo) {
    if (oo->getEventType() == 3)
      curmin = oo->getMin();
    else if (oo->getEventType() == 4)
      curmax = oo->getMax();
    logger << indentstring << "    " << oo->getDate()
           << " qty:" << oo->getQuantity() << ", oh:" << oo->getOnhand();
    if (curmin) logger << ", min:" << curmin;
    if (curmax) logger << ", max:" << curmax;
    switch (oo->getEventType()) {
      case 1:
        logger << ", " << oo->getOperationPlan() << endl;
        break;
      case 2:
        logger << ", set onhand to " << oo->getOnhand() << endl;
        break;
      case 3:
        logger << ", update minimum to " << oo->getMin() << endl;
        break;
      case 4:
        logger << ", update maximum to " << oo->getMax() << endl;
    }
  }
}

PyObject* Buffer::inspectPython(PyObject* self, PyObject* args) {
  try {
    // Pick up the buffer
    Buffer* buf = nullptr;
    PythonData c(self);
    if (c.check(Buffer::metadata))
      buf = static_cast<Buffer*>(self);
    else
      throw LogicException("Invalid buffer type");

    // Parse the argument
    char* msg = nullptr;
    if (!PyArg_ParseTuple(args, "|s:inspect", &msg)) return nullptr;

    buf->inspect(msg ? msg : "");

    return Py_BuildValue("");
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

void Buffer::setItem(Item* i, bool recompute) {
  if (it == i)
    // No change
    return;

  // Unlink from previous item
  if (it) {
    if (it->firstItemBuffer == this)
      it->firstItemBuffer = nextItemBuffer;
    else {
      Buffer* buf = it->firstItemBuffer;
      while (buf && buf->nextItemBuffer != this) buf = buf->nextItemBuffer;
      if (!buf) throw LogicException("corrupted buffer list for an item");
      buf->nextItemBuffer = nextItemBuffer;
    }
  }

  // Link at new item
  it = i;
  if (it) {
    nextItemBuffer = it->firstItemBuffer;
    it->firstItemBuffer = this;
  }

  // Mark changed
  setChanged();
  if (recompute) HasLevel::triggerLazyRecomputation();
}

void Buffer::setOnHand(double f) {
  // The dummy operation to model the inventory may need to be created
  Operation* o = Operation::find("Inventory " + string(getName()));
  Flow* fl;
  if (!o) {
    // Stop here if the quantity is 0
    if (!f) return;
    // Create a fixed time operation with zero leadtime, hidden from the xml
    // output, hidden for the solver, and without problem detection.
    o = new OperationInventory(this);
    fl = new FlowEnd(o, this, 1);
  } else
    // Find the flow of this operation
    fl = const_cast<Flow*>(&*(o->getFlows().begin()));

  // Check valid pointers
  if (!fl || !o)
    throw LogicException("Failed creating inventory operation for '" +
                         getName() + "'");

  // Make sure the sign of the flow is correct: +1 or -1.
  fl->setQuantity(f >= 0.0 ? 1.0 : -1.0);

  // Create a dummy operationplan on the inventory operation
  OperationPlan::iterator i(o);
  if (i == OperationPlan::end()) {
    // No operationplan exists yet
    auto opplan = o->createOperationPlan(fabs(f), Date::infinitePast,
                                         Date::infinitePast, getBatch());
    opplan->setClosed(true);
    opplan->activate();
    opplan->setRawReference(getName());
  } else {
    // Update the existing operationplan
    i->setClosed(false);
    i->setQuantity(fabs(f));
    i->setClosed(true);
  }
  setChanged();
}

OperationInventory::OperationInventory(Buffer* buf) {
  setName("Inventory " + string(buf->getName()));
  setHidden(true);
  setDetectProblems(false);
  setSizeMinimum(0);
  initType(metadata);
}

Buffer* OperationInventory::getBuffer() const {
  return getFlows().begin()->getBuffer();
}

double Buffer::getOnHand() const {
  string invop = "Inventory " + string(getName());
  for (auto i = flowplans.begin(); i != flowplans.end(); ++i) {
    if (i->getDate())
      return 0.0;  // Inventory event is always at start of horizon
    if (i->getEventType() != 1) continue;
    const FlowPlan* fp = static_cast<const FlowPlan*>(&*i);
    if (fp->getFlow()->getOperation()->getName() == invop &&
        fabs(fp->getQuantity()) > ROUNDING_ERROR)
      return fp->getQuantity();
  }
  return 0.0;
}

double Buffer::getOnHand(Date d, bool after) const {
  if (d == Date::infiniteFuture) {
    auto tmp = flowplans.rbegin();
    return tmp == flowplans.end() ? 0.0 : tmp->getOnhand();
  }
  double tmp(0.0);
  for (auto oo = flowplans.begin(); oo != flowplans.end(); ++oo) {
    if ((after && oo->getDate() > d) || (!after && oo->getDate() >= d))
      // Found a flowplan with a later date.
      // Return the onhand after the previous flowplan.
      return tmp;
    tmp = oo->getOnhand();
  }
  // Found no flowplan: either we have specified a date later than the
  // last flowplan, either there are no flowplans at all.
  return tmp;
}

double Buffer::getOnHand(Date d1, Date d2, bool min, bool use_safetystock,
                         bool include_proposed_po) const {
  // Swap parameters if required
  if (d2 < d1) swap(d1, d2);

  // Loop through all flowplans
  double tmp(0.0), record(0.0), safetystock(0.0), proposed_po(0.0);
  Date d, prev_Date;
  for (auto oo = flowplans.begin(); true; ++oo) {
    if (oo == flowplans.end() || oo->getDate() > d) {
      // Date has now changed or we have arrived at the end

      if (prev_Date <= d1)
        // Not in active Date range: we simply follow the onhand profile
        record = tmp;
      else {
        // In the active range: check if new record
        if (min) {
          if (tmp < record) record = tmp;
        } else {
          if (tmp > record) record = tmp;
        }
      }

      // Are we done now?
      if (prev_Date > d2 || oo == flowplans.end()) return record;
      d = oo->getDate();
    }
    // new safety stock value
    if (use_safetystock && oo->getEventType() == 3) safetystock = oo->getMin();

    // Proposed purchase orders special case
    if (oo != flowplans.end()) {
      auto opplan = oo->getOperationPlan();
      if (opplan && oo->getQuantity() > 0.0 && opplan->getProposed() &&
          opplan->getOperation()->hasType<OperationItemSupplier>())
        proposed_po += oo->getQuantity();
    }

    tmp = oo->getOnhand() - (use_safetystock ? safetystock : 0);
    if (!include_proposed_po) tmp -= proposed_po;
    prev_Date = oo->getDate();
  }
  // The above for-loop controls the exit. This line of code is never reached.
  throw LogicException("Unreachable code reached");
}

void Buffer::setMinimum(double m) {
  // There is already a minimum calendar.
  if (min_cal) {
    // We update the field, but don't use it yet.
    min_val = m;
    return;
  }

  // Mark as changed
  setChanged();

  // Set field
  min_val = m;

  // Create or update a single timeline min event
  for (auto oo = flowplans.begin(); oo != flowplans.end(); oo++)
    if (oo->getEventType() == 3) {
      // Update existing event
      static_cast<flowplanlist::EventMinQuantity*>(&*oo)->setMin(min_val);
      return;
    }

  // Create new event
  auto newEvent = new flowplanlist::EventMinQuantity(
      Plan::instance().getCurrent(), &flowplans, min_val);
  flowplans.insert(newEvent);
}

void Buffer::setMinimumCalendar(Calendar* cal) {
  // Resetting the same calendar
  if (min_cal == cal) return;

  // Mark as changed
  setChanged();

  // Delete previous events.
  for (auto oo = flowplans.begin(); oo != flowplans.end();) {
    flowplanlist::Event* tmp = &*oo;
    ++oo;
    if (tmp->getEventType() == 3) {
      flowplans.erase(tmp);
      delete tmp;
    }
  }

  // Null pointer passed. Change back to time independent min.
  if (!cal) {
    min_cal = nullptr;
    setMinimum(min_val);
    return;
  }

  // Create timeline structures for every event. A new entry is created only
  // when the value changes.
  min_cal = cal;
  double curMin = 0.0;
  for (Calendar::EventIterator x(min_cal); x.getDate() < Date::infiniteFuture;
       ++x)
    if (curMin != x.getValue()) {
      curMin = x.getValue();
      flowplanlist::EventMinQuantity* newBucket =
          new flowplanlist::EventMinQuantity(x.getDate(), &flowplans, curMin);
      flowplans.insert(newBucket);
    }
  min_cal->clearEventList();
}

void Buffer::setMaximum(double m) {
  // There is already a maximum calendar.
  if (max_cal) {
    // We update the field, but don't use it yet.
    max_val = m;
    return;
  }

  // Mark as changed
  setChanged();

  // Set field
  max_val = m;

  // Create or update a single timeline max event
  for (auto oo = flowplans.begin(); oo != flowplans.end(); oo++)
    if (oo->getEventType() == 4) {
      if (max_val > ROUNDING_ERROR) {
        // Update existing event
        static_cast<flowplanlist::EventMaxQuantity*>(&*oo)->setMax(max_val);
      } else {
        // Delete existing event
        flowplans.erase(&(*oo));
        delete &(*(oo++));
      }
      return;
    }
  // Create new event
  if (max_val > ROUNDING_ERROR) {
    auto newEvent = new flowplanlist::EventMaxQuantity(
        Plan::instance().getCurrent(), &flowplans, max_val);
    flowplans.insert(newEvent);
  }
}

void Buffer::setMaximumCalendar(Calendar* cal) {
  // Resetting the same calendar
  if (max_cal == cal) return;

  // Mark as changed
  setChanged();

  // Delete previous events.
  for (auto oo = flowplans.begin(); oo != flowplans.end();)
    if (oo->getEventType() == 4) {
      flowplans.erase(&(*oo));
      delete &(*(oo++));
    } else
      ++oo;

  // Null pointer passed. Change back to time independent max.
  if (!cal) {
    setMaximum(max_val);
    return;
  }

  // Create timeline structures for every bucket. A new entry is created only
  // when the value changes.
  max_cal = cal;
  double curMax = 0.0;
  for (Calendar::EventIterator x(max_cal); x.getDate() < Date::infiniteFuture;
       ++x)
    if (curMax != x.getValue()) {
      curMax = x.getValue();
      flowplanlist::EventMaxQuantity* newBucket =
          new flowplanlist::EventMaxQuantity(x.getDate(), &flowplans, curMax);
      flowplans.insert(newBucket);
    }
  max_cal->clearEventList();
}

void Buffer::deleteOperationPlans(bool deleteLocked) {
  // Delete the operationplans
  for (auto i = flows.begin(); i != flows.end(); ++i)
    OperationPlan::deleteOperationPlans(i->getOperation(), deleteLocked);

  // Mark to recompute the problems
  setChanged();
}

Buffer::~Buffer() {
  // Delete all operationplans.
  // An alternative logic would be to delete only the flowplans for this
  // buffer and leave the rest of the plan untouched. The currently
  // implemented method is way more drastic...
  deleteOperationPlans(true);

  // The Flow objects are automatically deleted by the destructor of the
  // Association list class.

  // Unlink from the item
  if (it) {
    if (it->firstItemBuffer == this)
      it->firstItemBuffer = nextItemBuffer;
    else {
      Buffer* buf = it->firstItemBuffer;
      while (buf && buf->nextItemBuffer != this) buf = buf->nextItemBuffer;
      if (!buf)
        logger << "Error: Corrupted buffer list for an item" << endl;
      else
        buf->nextItemBuffer = nextItemBuffer;
    }
  }

  // Remove the inventory operation
  Operation* invoper = Operation::find("Inventory " + string(getName()));
  if (invoper) delete invoper;

  // Problems are automatically deleted by the HasProblem class.
  // Constraints need to be cleared explicitly.
  Problem::clearConstraints(*this);
}

void Buffer::followPegging(PeggingIterator& iter, FlowPlan* curflowplan,
                           double qty, double offset, short lvl) {
  if (!curflowplan->getOperationPlan()->getQuantity() ||
      curflowplan->getBuffer()->getTool())
    // Flowplans with quantity 0 have no pegging.
    // Flowplans for buffers representing tools have no pegging either.
    return;

  // Did we reach the maximum depth we want to visit
  if (iter.getMaxLevel() != -1 && lvl > iter.getMaxLevel()) return;

  if (curflowplan->getBuffer()->hasType<BufferInfinite>() &&
      ((curflowplan->getQuantity() < 0 && !iter.isDownstream()) ||
       (curflowplan->getQuantity() > 0 && iter.isDownstream())))
    // No pegging across infinite buffers
    return;

  Buffer::flowplanlist::iterator f = getFlowPlans().begin(curflowplan);
  if (curflowplan->getQuantity() < -ROUNDING_ERROR && !iter.isDownstream()) {
    // CASE 1:
    // This is a flowplan consuming from a buffer. Navigating upstream means
    // finding the flowplans producing this consumed material.
    double scale = -curflowplan->getQuantity() /
                   curflowplan->getOperationPlan()->getQuantity();
    double startQty =
        f->getCumulativeConsumed() + f->getQuantity() + offset * scale;
    double endQty = startQty + qty * scale;
    if (f->getCumulativeProduced() <= startQty + ROUNDING_ERROR) {
      // CASE 1A: Not produced enough yet: move forward
      while (f != getFlowPlans().end() &&
             f->getCumulativeProduced() <= startQty)
        ++f;
      while (f != getFlowPlans().end() &&
             ((f->getQuantity() <= 0 && f->getCumulativeProduced() < endQty) ||
              (f->getQuantity() > 0 &&
               f->getCumulativeProduced() - f->getQuantity() < endQty))) {
        if (f->getQuantity() > ROUNDING_ERROR) {
          double newqty = f->getQuantity();
          double newoffset = 0.0;
          if (f->getCumulativeProduced() - f->getQuantity() < startQty) {
            newoffset =
                startQty - (f->getCumulativeProduced() - f->getQuantity());
            newqty -= newoffset;
          }
          if (f->getCumulativeProduced() > endQty)
            newqty -= f->getCumulativeProduced() - endQty;
          OperationPlan* opplan =
              dynamic_cast<const FlowPlan*>(&(*f))->getOperationPlan();
          OperationPlan* topopplan = opplan->getTopOwner();
          if (topopplan->getOperation()->hasType<OperationSplit>() ||
              (iter.getMaxLevel() > 0))
            if (opplan->getOwner() &&
                opplan->getOwner()
                    ->getOperation()
                    ->hasType<OperationRouting>() &&
                !(iter.getMaxLevel() > 0))
              topopplan = opplan->getOwner();
            else
              topopplan = opplan;
          iter.updateStack(
              topopplan, topopplan->getQuantity() * newqty / f->getQuantity(),
              topopplan->getQuantity() * newoffset / f->getQuantity(), lvl,
              curflowplan->getDate() - f->getDate());
        }
        ++f;
      }
    } else {
      // CASE 1B: Produced too much already: move backward
      while (f != getFlowPlans().end() &&
             ((f->getQuantity() <= 0 && f->getCumulativeProduced() > endQty) ||
              (f->getQuantity() > 0 &&
               f->getCumulativeProduced() - f->getQuantity() > endQty)))
        --f;
      while (f != getFlowPlans().end() &&
             f->getCumulativeProduced() > startQty) {
        if (f->getQuantity() > ROUNDING_ERROR) {
          double newqty = f->getQuantity();
          double newoffset = 0.0;
          if (f->getCumulativeProduced() - f->getQuantity() < startQty) {
            newoffset =
                startQty - (f->getCumulativeProduced() - f->getQuantity());
            newqty -= newoffset;
          }
          if (f->getCumulativeProduced() > endQty)
            newqty -= f->getCumulativeProduced() - endQty;
          OperationPlan* opplan =
              dynamic_cast<FlowPlan*>(&(*f))->getOperationPlan();
          OperationPlan* topopplan = opplan->getTopOwner();
          if (topopplan->getOperation()->hasType<OperationSplit>() ||
              (iter.getMaxLevel() > 0))
            if (opplan->getOwner() &&
                opplan->getOwner()
                    ->getOperation()
                    ->hasType<OperationRouting>() &&
                !(iter.getMaxLevel() > 0))
              topopplan = opplan->getOwner();
            else
              topopplan = opplan;
          iter.updateStack(
              topopplan, topopplan->getQuantity() * newqty / f->getQuantity(),
              topopplan->getQuantity() * newoffset / f->getQuantity(), lvl,
              curflowplan->getDate() - f->getDate());
        }
        --f;
      }
    }
    return;
  }

  if (curflowplan->getQuantity() > ROUNDING_ERROR && iter.isDownstream()) {
    // CASE 2:
    // This is a flowplan producing in a buffer. Navigating downstream means
    // finding the flowplans consuming this produced material.
    double scale = curflowplan->getQuantity() /
                   curflowplan->getOperationPlan()->getQuantity();
    double startQty =
        f->getCumulativeProduced() - f->getQuantity() + offset * scale;
    double endQty = startQty + qty * scale;
    if ((f->getQuantity() <= 0 &&
         f->getCumulativeConsumed() + f->getQuantity() < endQty) ||
        (f->getQuantity() > 0 && f->getCumulativeConsumed() < endQty)) {
      // CASE 2A: Not consumed enough yet: move forward
      while (f != getFlowPlans().end() &&
             f->getCumulativeConsumed() <= startQty)
        ++f;
      while (f != getFlowPlans().end() &&
             ((f->getQuantity() <= 0 &&
               f->getCumulativeConsumed() + f->getQuantity() < endQty) ||
              (f->getQuantity() > 0 && f->getCumulativeConsumed() < endQty))) {
        if (f->getQuantity() < -ROUNDING_ERROR) {
          double newqty = -f->getQuantity();
          double newoffset = 0.0;
          if (f->getCumulativeConsumed() + f->getQuantity() < startQty) {
            newoffset =
                startQty - (f->getCumulativeConsumed() + f->getQuantity());
            newqty -= newoffset;
          }
          if (f->getCumulativeConsumed() > endQty)
            newqty -= f->getCumulativeConsumed() - endQty;
          OperationPlan* opplan =
              dynamic_cast<FlowPlan*>(&(*f))->getOperationPlan();
          OperationPlan* topopplan = opplan->getTopOwner();
          if (topopplan->getOperation()->hasType<OperationSplit>() ||
              (iter.getMaxLevel() > 0))
            if (opplan->getOwner() && opplan->getOwner()
                                          ->getOperation()
                                          ->hasType<OperationRouting>()) {
              for (OperationPlan::iterator j(opplan->getOwner());
                   j != OperationPlan::end(); ++j) {
                if (j->getReference() == opplan->getReference())
                  topopplan = opplan->getOwner();
                else
                  topopplan = opplan;
                break;
              }

            } else
              topopplan = opplan;
          iter.updateStack(
              topopplan, -topopplan->getQuantity() * newqty / f->getQuantity(),
              -topopplan->getQuantity() * newoffset / f->getQuantity(), lvl,
              f->getDate() - curflowplan->getDate());
        }
        ++f;
      }
    } else {
      // CASE 2B: Consumed too much already: move backward
      while (f != getFlowPlans().end() &&
             ((f->getQuantity() <= 0 &&
               f->getCumulativeConsumed() + f->getQuantity() < endQty) ||
              (f->getQuantity() > 0 && f->getCumulativeConsumed() < endQty)))
        --f;
      while (f != getFlowPlans().end() &&
             f->getCumulativeConsumed() > startQty) {
        if (f->getQuantity() < -ROUNDING_ERROR) {
          double newqty = -f->getQuantity();
          double newoffset = 0.0;
          if (f->getCumulativeConsumed() + f->getQuantity() < startQty)
            newqty -=
                startQty - (f->getCumulativeConsumed() + f->getQuantity());
          if (f->getCumulativeConsumed() > endQty)
            newqty -= f->getCumulativeConsumed() - endQty;
          OperationPlan* opplan =
              dynamic_cast<FlowPlan*>(&(*f))->getOperationPlan();
          OperationPlan* topopplan = opplan->getTopOwner();
          if (topopplan->getOperation()->hasType<OperationSplit>() ||
              (iter.getMaxLevel() > 0))
            if (opplan->getOwner() && opplan->getOwner()
                                          ->getOperation()
                                          ->hasType<OperationRouting>()) {
              for (OperationPlan::iterator j(opplan->getOwner());
                   j != OperationPlan::end(); ++j) {
                if (j->getReference() == opplan->getReference())
                  topopplan = opplan->getOwner();
                else
                  topopplan = opplan;
                break;
              }
            } else
              topopplan = opplan;
          iter.updateStack(
              topopplan, -topopplan->getQuantity() * newqty / f->getQuantity(),
              -topopplan->getQuantity() * newoffset / f->getQuantity(), lvl,
              f->getDate() - curflowplan->getDate());
        }
        --f;
      }
    }
  }
}

Buffer* Buffer::findOrCreate(Item* itm, Location* loc) {
  if (!itm || !loc) return nullptr;

  // Return existing buffer if it exists
  Item::bufferIterator buf_iter(itm);
  while (Buffer* tmpbuf = buf_iter.next()) {
    if (tmpbuf->getLocation() == loc && !tmpbuf->getBatch()) return tmpbuf;
  }

  // Create a new buffer with a unique name
  stringstream o;
  o << itm->getName() << " @ " << loc->getName();
  Buffer* b;
  while ((b = find(o.str()))) o << '*';
  b = new BufferDefault();
  b->setItem(itm);
  b->setLocation(loc);
  b->setName(o.str());
  return b;
}

Buffer* Buffer::findOrCreate(Item* itm, Location* loc,
                             const PooledString& batch) {
  if (!itm || !loc) return nullptr;

  // Return existing buffer if it exists
  Buffer* generic = nullptr;
  Item::bufferIterator buf_iter(itm);
  while (Buffer* tmpbuf = buf_iter.next()) {
    if (tmpbuf->getLocation() == loc) {
      if (tmpbuf->getBatch() == batch)
        return tmpbuf;
      else if (!tmpbuf->getBatch())
        generic = tmpbuf;
    }
  }

  // Create a new buffer with a unique name
  stringstream o;
  o << itm->getName();
  if (batch && itm->hasType<ItemMTO>()) o << " @ " << batch;
  o << " @ " << loc->getName();
  Buffer* b = find(o.str());
  if (!b) {
    b = new BufferDefault();
    b->setName(o.str());
  }
  b->setItem(itm, !batch && !itm->hasType<ItemMTO>());
  b->setLocation(loc, !batch && !itm->hasType<ItemMTO>());
  if (batch && itm->hasType<ItemMTO>()) {
    b->setBatch(batch);
    if (generic) b->copyLevelAndCluster(generic);
  }
  return b;
}

bool Buffer::hasConsumingFlows() const {
  for (auto fl = getFlows().begin(); fl != getFlows().end(); ++fl)
    if (fl->isConsumer()) return true;
  return false;
}

void Buffer::buildProducingOperation() {
  if (producing_operation && producing_operation != uninitializedProducing &&
      !producing_operation->getHidden())
    // Leave manually specified producing operations alone
    return;

  // Loop over this item and all its parent items
  Item* item = getItem();
  while (item) {
    // Loop over all suppliers of this item+location combination
    Item::supplierlist::const_iterator supitem_iter =
        item->getSupplierIterator();
    while (ItemSupplier* supitem = supitem_iter.next()) {
      if (supitem->getPriority() == 0) continue;

      // Verify whether the ItemSupplier is applicable to the buffer location
      // We need to reject the following 2 mismatches:
      //   - buffer location is not null, and is not the ItemSupplier location
      //   - buffer location is null, and the ItemSupplier location isn't
      if (supitem->getLocation()) {
        if ((getLocation() && getLocation() != supitem->getLocation()) ||
            !getLocation())
          continue;
      }

      // Check if there is already a producing operation referencing this
      // ItemSupplier
      if (producing_operation &&
          producing_operation != uninitializedProducing) {
        if (producing_operation->hasType<OperationItemSupplier>()) {
          OperationItemSupplier* o =
              static_cast<OperationItemSupplier*>(producing_operation);
          if (o->getItemSupplier() == supitem)
            // Already exists
            continue;
        } else {
          bool exists = false;
          SubOperation::iterator subiter(
              producing_operation->getSubOperations());
          while (SubOperation* o = subiter.next())
            if (o->getOperation()->hasType<OperationItemSupplier>()) {
              OperationItemSupplier* s =
                  static_cast<OperationItemSupplier*>(o->getOperation());
              if (s->getItemSupplier() == supitem) {
                // Already exists
                exists = true;
                break;
              }
            }
          if (exists) continue;
        }
      }

      // New operation needs to be created
      OperationItemSupplier* oper =
          OperationItemSupplier::findOrCreate(supitem, this);

      // Merge the new operation in an alternate operation if required
      if (producing_operation &&
          producing_operation != uninitializedProducing) {
        // We're not the first
        SubOperation* subop = new SubOperation();
        subop->setOperation(oper);
        subop->setPriority(supitem->getPriority());
        subop->setEffective(supitem->getEffective());
        if (!producing_operation->hasType<OperationAlternate>()) {
          // We are the second: create an alternate and add 2 suboperations
          OperationAlternate* superop = new OperationAlternate();
          stringstream o;
          o << "Replenish " << getName();
          superop->setName(o.str());
          superop->setHidden(true);
          if (oper->getSearch() != SearchMode::PRIORITY)
            superop->setSearch(oper->getSearch());
          SubOperation* subop2 = new SubOperation();
          subop2->setOperation(producing_operation);
          // Note that priority and effectivity are at default values.
          // If not, the alternate would already have been created.
          subop2->setOwner(superop);
          producing_operation = superop;
          subop->setOwner(producing_operation);
        } else {
          // We are third or later: just add a suboperation
          if (producing_operation->getSubOperations().size() > 100) {
            new ProblemInvalidData(
                this,
                string("Excessive replenishments defined for '") + getName() +
                    "'",
                "material", Date::infinitePast, Date::infiniteFuture, 1);
            return;
          } else {
            subop->setOwner(producing_operation);
            if (oper->getSearch() != SearchMode::PRIORITY)
              producing_operation->setSearch(oper->getSearch());
          }
        }
      } else {
        // We are the first: only create an operationItemSupplier instance
        if (supitem->getEffective() == DateRange() &&
            supitem->getPriority() == 1 &&
            oper->getSearch() == SearchMode::PRIORITY)
          // Use a single operation. If an alternate is required later on
          // we know it has the default priority, serach mode and effectivity.
          producing_operation = oper;
        else {
          // Already create an alternate now
          OperationAlternate* superop = new OperationAlternate();
          producing_operation = superop;
          stringstream o;
          o << "Replenish " << getName();
          superop->setName(o.str());
          superop->setHidden(true);
          if (oper->getSearch() != SearchMode::PRIORITY)
            superop->setSearch(oper->getSearch());
          SubOperation* subop = new SubOperation();
          subop->setOperation(oper);
          subop->setPriority(supitem->getPriority());
          subop->setEffective(supitem->getEffective());
          subop->setOwner(superop);
        }
      }
    }  // End loop over itemsuppliers

    // Loop over all item distributions to replenish this item+location
    // combination
    auto itemdist_iter = item->getDistributionIterator();
    while (ItemDistribution* itemdist = itemdist_iter.next()) {
      if (itemdist->getPriority() == 0) continue;

      // Verify whether the ItemDistribution is applicable to the buffer
      // location We need to reject the following 2 mismatches:
      //   - buffer location is not null, and is the ItemDistribution
      //   destination location
      //   - buffer location is null, and the ItemDistribution destination
      //   location isn't
      if (getLocation() == itemdist->getOrigin()) continue;
      if (itemdist->getDestination()) {
        if ((getLocation() && getLocation() != itemdist->getDestination()) ||
            !getLocation())
          continue;
      }
      if (!itemdist->getOrigin()) continue;

      // Check if there is already a producing operation referencing this
      // ItemDistribution
      if (producing_operation &&
          producing_operation != uninitializedProducing) {
        if (producing_operation->hasType<OperationItemDistribution>()) {
          OperationItemDistribution* o =
              static_cast<OperationItemDistribution*>(producing_operation);
          if (o->getItemDistribution() == itemdist)
            // Already exists
            continue;
        } else {
          bool exists = false;
          SubOperation::iterator subiter(
              producing_operation->getSubOperations());
          while (SubOperation* o = subiter.next())
            if (o->getOperation()->hasType<OperationItemDistribution>()) {
              OperationItemDistribution* s =
                  static_cast<OperationItemDistribution*>(o->getOperation());
              if (s->getItemDistribution() == itemdist) {
                // Already exists
                exists = true;
                break;
              }
            }
          if (exists) continue;
        }
      }

      // New operation needs to be created
      Buffer* originbuf = findOrCreate(getItem(), &*itemdist->getOrigin());
      Operation* oper =
          OperationItemDistribution::findOrCreate(itemdist, originbuf, this);

      // Merge the new operation in an alternate operation if required
      if (producing_operation &&
          producing_operation != uninitializedProducing) {
        // We're not the first
        SubOperation* subop = new SubOperation();
        subop->setOperation(oper);
        subop->setPriority(itemdist->getPriority());
        subop->setEffective(itemdist->getEffective());
        if (!producing_operation->hasType<OperationAlternate>()) {
          // We are the second: create an alternate and add 2 suboperations
          OperationAlternate* superop = new OperationAlternate();
          stringstream o;
          o << "Replenish " << getName();
          superop->setName(o.str());
          superop->setHidden(true);
          if (oper->getSearch() != SearchMode::PRIORITY)
            superop->setSearch(oper->getSearch());
          SubOperation* subop2 = new SubOperation();
          subop2->setOperation(producing_operation);
          // Note that priority and effectivity are at default values.
          // If not, the alternate would already have been created.
          subop2->setOwner(superop);
          producing_operation = superop;
          subop->setOwner(producing_operation);
        } else {
          // We are third or later: just add a suboperation
          if (producing_operation->getSubOperations().size() > 100) {
            new ProblemInvalidData(
                this,
                string("Excessive replenishments defined for '") + getName() +
                    "'",
                "material", Date::infinitePast, Date::infiniteFuture, 1);
            return;
          } else {
            subop->setOwner(producing_operation);
            if (oper->getSearch() != SearchMode::PRIORITY)
              producing_operation->setSearch(oper->getSearch());
          }
        }
      } else {
        // We are the first: only create an OperationItemDistribution instance
        if (itemdist->getEffective() == DateRange() &&
            itemdist->getPriority() == 1 &&
            oper->getSearch() == SearchMode::PRIORITY)
          // Use a single operation. If an alternate is required later on
          // we know it has the default priority, search mode and effectivity.
          producing_operation = oper;
        else {
          // Already create an alternate now
          OperationAlternate* superop = new OperationAlternate();
          producing_operation = superop;
          stringstream o;
          o << "Replenish " << getName();
          superop->setName(o.str());
          superop->setHidden(true);
          if (oper->getSearch() != SearchMode::PRIORITY)
            superop->setSearch(oper->getSearch());
          SubOperation* subop = new SubOperation();
          subop->setOperation(oper);
          subop->setPriority(itemdist->getPriority());
          subop->setEffective(itemdist->getEffective());
          subop->setOwner(superop);
        }
      }

    }  // End loop over itemdistributions

    // While-loop to add suppliers defined at parent items
    item = item->getOwner();
  }

  // Loop over all item operations to replenish this item+location combination
  if (getItem()) {
    Item::operationIterator itemoper_iter = getItem()->getOperationIterator();
    while (Operation* itemoper = itemoper_iter.next()) {
      if (itemoper->getPriority() == 0) continue;

      // Verify whether the operation is applicable to the buffer
      Location* l = itemoper->getLocation();
      for (auto flow_iter = itemoper->getFlowIterator();
           flow_iter != itemoper->getFlows().end(); ++flow_iter)
        if (flow_iter->getItem() == getItem() && flow_iter->getLocation() &&
            flow_iter->isProducer()) {
          l = flow_iter->getLocation();
          break;
        }
      if (l && l != getLocation()) continue;

      // Make sure a producing flow record exists
      correctProducingFlow(itemoper);

      // Check if there is already a producing operation referencing this
      // operation
      if (producing_operation &&
          producing_operation != uninitializedProducing) {
        if (!producing_operation->hasType<OperationAlternate>()) {
          if (producing_operation == itemoper)
            // Already exists
            continue;
        } else {
          SubOperation::iterator subiter(
              producing_operation->getSubOperations());
          while (SubOperation* o = subiter.next())
            if (o->getOperation() == itemoper)
              // Already exists
              continue;
        }
      }

      // Merge the new operation in an alternate operation if required
      if (producing_operation &&
          producing_operation != uninitializedProducing) {
        // We're not the first
        SubOperation* subop = new SubOperation();
        subop->setOperation(itemoper);
        subop->setPriority(itemoper->getPriority());
        subop->setEffective(itemoper->getEffective());
        if (!producing_operation->hasType<OperationAlternate>()) {
          // We are the second: create an alternate and add 2 suboperations
          OperationAlternate* superop = new OperationAlternate();
          stringstream o;
          o << "Replenish " << getName();
          superop->setName(o.str());
          superop->setHidden(true);
          if (itemoper->getSearch() != SearchMode::PRIORITY)
            superop->setSearch(itemoper->getSearch());
          SubOperation* subop2 = new SubOperation();
          subop2->setOperation(producing_operation);
          // Note that priority and effectivity are at default values.
          // If not, the alternate would already have been created.
          subop2->setOwner(superop);
          producing_operation = superop;
          subop->setOwner(producing_operation);
        } else {
          // We are third or later: just add a suboperation
          if (producing_operation->getSubOperations().size() > 100) {
            new ProblemInvalidData(
                this,
                string("Excessive replenishments defined for '") + getName() +
                    "'",
                "material", Date::infinitePast, Date::infiniteFuture, 1);
            return;
          } else {
            subop->setOwner(producing_operation);
            if (itemoper->getSearch() != SearchMode::PRIORITY)
              producing_operation->setSearch(itemoper->getSearch());
          }
        }
      } else {
        // We are the first
        if (itemoper->getEffective() == DateRange() &&
            itemoper->getPriority() == 1 &&
            (itemoper->getSearch() == SearchMode::PRIORITY ||
             itemoper->hasType<OperationAlternate>()))
          // Use a single operation. If an alternate is required later on
          // we know it has the default priority, search mode and effectivity.
          producing_operation = itemoper;
        else {
          // Already create an alternate now
          OperationAlternate* superop = new OperationAlternate();
          producing_operation = superop;
          stringstream o;
          o << "Replenish " << getName();
          superop->setName(o.str());
          superop->setHidden(true);
          if (itemoper->getSearch() != SearchMode::PRIORITY)
            superop->setSearch(itemoper->getSearch());
          SubOperation* subop = new SubOperation();
          subop->setOperation(itemoper);
          subop->setPriority(itemoper->getPriority());
          subop->setEffective(itemoper->getEffective());
          subop->setOwner(superop);
        }
      }
    }  // End loop over operations
  }

  // Last resort: check if there are already operations producing in this
  // buffer. If there exists only 1 we use that operation. Inventory operation
  // or operations with 0 priority are skipped.
  if (producing_operation == uninitializedProducing) {
    const Flow* found = nullptr;
    for (auto tmp = getFlows().begin(); tmp != getFlows().end(); ++tmp) {
      if (tmp->getQuantity() > 0 &&
          !tmp->getOperation()->hasType<OperationInventory>() &&
          tmp->getOperation()->getPriority()) {
        if (found) {
          // Found a second operation producing this item. Abort the mission...
          found = nullptr;
          break;
        } else
          // Found a first operation producing this item
          found = &*tmp;
      }
    }
    if (found) producing_operation = found->getOperation();
  }

  if (producing_operation == uninitializedProducing) {
    // No producer could be generated. No replenishment will be possible.
    new ProblemInvalidData(
        this, string("No replenishment defined for '") + getName() + "'",
        "material", Date::infinitePast, Date::infiniteFuture, 1);
    producing_operation = nullptr;
  } else {
    // Remove eventual existing problem on the buffer
    for (auto j = Problem::begin(this, false); j != Problem::end(); ++j) {
      if (typeid(*j) == typeid(ProblemInvalidData)) {
        delete &*j;
        break;
      }
    }
  }
}

void Buffer::correctProducingFlow(Operation* itemoper) {
  // if operation is of type routing or alternate or split then look if flow
  // exists at parent level
  if (itemoper
          ->hasType<OperationRouting, OperationAlternate, OperationSplit>()) {
    // check if routing has a flow into the buffer
    for (auto flow_iter = itemoper->getFlowIterator();
         flow_iter != itemoper->getFlows().end(); ++flow_iter)
      if (flow_iter->getItem() == getItem() &&
          (!flow_iter->getLocation() ||
           flow_iter->getLocation() == getLocation()))
        // Flow for this item exists, nothing to do
        return;
  }

  // Operation is of type routing, check if any step is producing into this
  // buffer
  if (itemoper->hasType<OperationRouting>()) {
    // a first loop to look for the max priority to get the last step
    auto subs = itemoper->getSubOperationIterator();
    SubOperation* lastStep = nullptr;
    while (SubOperation* sub = subs.next()) {
      auto flow_iter = sub->getOperation()->getFlowIterator();
      while (flow_iter != sub->getOperation()->getFlows().end()) {
        if (flow_iter->getItem() == getItem() &&
            (!flow_iter->getLocation() ||
             flow_iter->getLocation() == getLocation()))
          return;
        ++flow_iter;
      }
      lastStep = sub;
    }

    // correct the last step
    if (lastStep) {
      correctProducingFlow(lastStep->getOperation());
      return;
    }
    // else: an empty routing, where the code below will add a top-level
    // producing flow
  }

  // if operation is of type alternate or split then apply logic to all
  // suboperations (which might be a routing)
  if (itemoper->hasType<OperationAlternate, OperationSplit>()) {
    auto subs = itemoper->getSubOperationIterator();
    while (SubOperation* sub = subs.next()) {
      correctProducingFlow(sub->getOperation());
    }
    return;
  }

  // "Regular" case : operation is of type fixed time, time per...
  auto flow_iter = itemoper->getFlowIterator();
  bool foundFlow = false;
  while (flow_iter != itemoper->getFlows().end()) {
    if (flow_iter->getItem() == getItem() &&
        (!flow_iter->getLocation() ||
         flow_iter->getLocation() == getLocation())) {
      foundFlow = true;
      break;
    }
    ++flow_iter;
  }
  if (!foundFlow) {
    if (getBatch())
      new FlowEnd(itemoper, Buffer::findOrCreate(getItem(), getLocation()), 1);
    else
      new FlowEnd(itemoper, this, 1);
  }
}

pair<Duration, Date> Buffer::getDecoupledLeadTime(
    double qty, Date startdate, bool recurse_ip_buffers) const {
  if (!recurse_ip_buffers || hasType<BufferInfinite>())
    // Abort the recursion
    return make_pair(Duration(0L), startdate);

  Operation* oper = getProducingOperation();
  if (!oper)
    // Infinite lead time if no producing operation is found.
    // Setting an extremely long lead time, which results in a huge
    // safety stock that covers the entire horizon.
    return make_pair(Duration(999L * 86400L), Date::infiniteFuture);
  else
    return oper->getDecoupledLeadTime(qty, startdate);
}

PyObject* Buffer::getDecoupledLeadTimePython(PyObject* self, PyObject* args) {
  // Pick up arguments
  double qty = 1.0;
  PyObject* py_startdate = nullptr;
  Date startdate = Plan::instance().getCurrent();
  if (!PyArg_ParseTuple(args, "|dO:decoupledLeadTime", &qty, &py_startdate))
    return nullptr;
  if (py_startdate) startdate = PythonData(py_startdate).getDate();

  try {
    auto lt =
        static_cast<Buffer*>(self)->getDecoupledLeadTime(qty, startdate, true);
    return PythonData(lt.first);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

PyObject* Buffer::availableOnhandPython(PyObject* self, PyObject* args) {
  PyObject* dateobj = nullptr;
  if (!PyArg_ParseTuple(args, "|O:availableonhand", &dateobj)) return nullptr;

  try {
    Date refdate;
    if (dateobj) {
      PythonData tmp(dateobj);
      refdate = tmp.getDate();
    } else
      refdate = Plan::instance().getCurrent();
    auto available = static_cast<Buffer*>(self)->getOnHand(
        refdate, Date::infiniteFuture, true);
    return PythonData(available);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

Buffer* Buffer::findFromName(string nm) {
  // Check if it exists
  Buffer* buf = Buffer::find(nm);
  if (buf) return buf;

  size_t pos = nm.find(" @ ");
  if (pos == string::npos) return nullptr;
  Item* it = Item::find(nm.substr(0, pos));
  if (!it) return nullptr;
  auto locstring = nm.substr(pos + 3, string::npos);
  pos = locstring.find(" @ ");
  if (pos == string::npos) {
    // Buffer name matches "item @ location"
    Location* loc = Location::find(locstring);
    if (!loc) return nullptr;
    buf = new BufferDefault();
    static_cast<BufferDefault*>(buf)->setName(nm);
    static_cast<BufferDefault*>(buf)->setItem(it);
    static_cast<BufferDefault*>(buf)->setLocation(loc);
    return buf;
  } else {
    // Buffer name matches "item @ batch @ location"
    Location* loc = Location::find(locstring.substr(pos + 3, string::npos));
    if (!loc) return nullptr;
    auto batch = locstring.substr(0, pos);
    buf = new BufferDefault();
    static_cast<BufferDefault*>(buf)->setName(nm);
    static_cast<BufferDefault*>(buf)->setBatch(batch);
    static_cast<BufferDefault*>(buf)->setItem(it);
    static_cast<BufferDefault*>(buf)->setLocation(loc);
    return buf;
  }
  return nullptr;
}

}  // namespace frepple
