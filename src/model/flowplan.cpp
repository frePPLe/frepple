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

const MetaClass* FlowPlan::metadata;
const MetaCategory* FlowPlan::metacategory;

int FlowPlan::initialize() {
  // Initialize the metadata
  metacategory =
      MetaCategory::registerCategory<FlowPlan>("flowplan", "flowplans", reader);
  metadata = MetaClass::registerClass<FlowPlan>("flowplan", "flowplan", true);
  registerFields<FlowPlan>(const_cast<MetaClass*>(metadata));

  // Initialize the Python type
  auto& x = FreppleCategory<FlowPlan>::getPythonType();
  x.setName("flowplan");
  x.setDoc("frePPLe flowplan");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  metadata->setPythonClass(x);
  return x.typeReady();
}

FlowPlan::FlowPlan(OperationPlan* opplan, const Flow* f)
    : fl(const_cast<Flow*>(f)), oper(opplan) {
  assert(opplan && f);

  // Initialize the Python type
  initType(metadata);

  // Link the flowplan to the operationplan
  if (opplan->firstflowplan) {
    // Append to the end
    FlowPlan* c = opplan->firstflowplan;
    while (c->nextFlowPlan) c = c->nextFlowPlan;
    c->nextFlowPlan = this;
  } else
    // First in the list
    opplan->firstflowplan = this;

  // Find the buffer
  if (fl->getBuffer() && fl->getBuffer()->getItem() &&
      fl->getBuffer()->getItem()->hasType<ItemMTO>()) {
    buf = Buffer::findOrCreate(fl->getBuffer()->getItem(),
                               fl->getBuffer()->getLocation(),
                               opplan->getBatch());
  } else
    buf = fl->getBuffer();
  assert(buf);

  // Compute the flowplan quantity
  auto fl_info = fl->getFlowplanDateQuantity(this);
  buf->flowplans.insert(this, fl_info.second, fl_info.first);

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  buf->setChanged();
  fl->getOperation()->setChanged();
}

FlowPlan::FlowPlan(OperationPlan* opplan, const Flow* f, Date d, double q)
    : fl(const_cast<Flow*>(f)), oper(opplan) {
  assert(opplan && f);

  // Initialize the Python type
  initType(metadata);

  // Link the flowplan to the operationplan
  if (opplan->firstflowplan) {
    // Append to the end
    FlowPlan* c = opplan->firstflowplan;
    while (c->nextFlowPlan) c = c->nextFlowPlan;
    c->nextFlowPlan = this;
  } else
    // First in the list
    opplan->firstflowplan = this;

  // Find the buffer
  if (fl->getBuffer() && fl->getBuffer()->getItem() &&
      fl->getBuffer()->getItem()->hasType<ItemMTO>()) {
    if (fl->getBuffer()->getItem()->hasType<ItemMTO>() && opplan->getBatch())
      buf = Buffer::findOrCreate(fl->getBuffer()->getItem(),
                                 fl->getBuffer()->getLocation(),
                                 opplan->getBatch());
  } else
    buf = fl->getBuffer();
  assert(buf);

  // Compute the flowplan quantity
  buf->flowplans.insert(this, q, d);

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  buf->setChanged();
  fl->getOperation()->setChanged();
}

string FlowPlan::getStatus() const {
  if (flags & STATUS_CONFIRMED)
    return "confirmed";
  else
    return "proposed";
}

void FlowPlan::setStatus(const string& s) {
  if (getOperationPlan()->getProposed() && s == "confirmed")
    throw DataException(
        "OperationPlanMaterial locked while OperationPlan is not");
  if (s == "confirmed")
    flags |= STATUS_CONFIRMED;
  else if (s == "proposed")
    flags &= ~STATUS_CONFIRMED;
  else
    throw DataException("invalid operationplanmaterial status:" + s);
}

void FlowPlan::update() {
  // Update the timeline data structure
  auto fl_info = fl->getFlowplanDateQuantity(this);
  buf->flowplans.update(this, fl_info.second, fl_info.first);

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  buf->setChanged();
  fl->getOperation()->setChanged();
}

void FlowPlan::updateBatch() {
  // Remove from the old buffer, if there is one
  if (buf) {
    buf->flowplans.erase(this);
    buf->setChanged();
  }

  // Insert in the new buffer
  PooledString batch = getOperationPlan()->getBatch();
  if (fl->getBuffer()->getItem()->hasType<ItemMTO>() && batch)
    buf = Buffer::findOrCreate(fl->getBuffer()->getItem(),
                               fl->getBuffer()->getLocation(), batch);
  else
    buf = fl->getBuffer();
  buf->flowplans.insert(this, getQuantity(), getDate());
  buf->setChanged();
}

void FlowPlan::setBuffer(Buffer* newbuf) {
  if (newbuf == buf) return;

  if (!newbuf) throw DataException("Can't switch to nullptr buffer");
  if (!buf) throw DataException("Can't switch from nullptr buffer");
  if (newbuf->getItem() != buf->getItem() ||
      newbuf->getLocation() != buf->getLocation())
    throw DataException(
        "Flowplans can only switch to buffers with the same item and location");

  if (fl && fl->hasType<FlowTransferBatch>()) {
    // Switch all flowplans of the same transfer batch
    auto oldbuf = buf;
    for (auto flpln = getOperationPlan()->beginFlowPlans();
         flpln != getOperationPlan()->endFlowPlans(); ++flpln) {
      if (flpln->buf != oldbuf) continue;

      // Remove from the old buffer
      flpln->buf->flowplans.erase(&*flpln);

      // Insert in the new buffer
      flpln->buf = newbuf;
      flpln->buf->flowplans.insert(&*flpln, flpln->getQuantity(),
                                   flpln->getDate());
    }
    oldbuf->setChanged();
  } else {
    // Remove from the old buffer
    buf->flowplans.erase(this);
    buf->setChanged();

    // Insert in the new buffer
    buf = newbuf;
    buf->flowplans.insert(this, getQuantity(), getDate());
  }
  buf->setChanged();
}

void FlowPlan::setFlow(Flow* newfl) {
  // No change
  if (newfl == fl) return;

  // Verify the data
  if (!newfl) throw DataException("Can't switch to nullptr flow");
  if (newfl->getType() != fl->getType())
    throw DataException("Flowplans can only switch to flows of the same type");

  PooledString batch;
  if (buf) batch = buf->getBatch();
  if (!newfl->hasType<FlowTransferBatch>() || !fl) {
    // Remove from the old buffer, if there is one
    if (fl) {
      if (fl->getOperation() != newfl->getOperation())
        throw DataException(
            "Only switching to a flow on the same operation is allowed");
      if (buf) {
        buf->flowplans.erase(this);
        buf->setChanged();
      }
    }

    // Insert in the new buffer
    fl = newfl;
    auto fl_info = fl->getFlowplanDateQuantity(this);
    if (fl->getBuffer()->getItem()->hasType<ItemMTO>() && !batch.empty())
      buf = Buffer::findOrCreate(fl->getBuffer()->getItem(),
                                 fl->getBuffer()->getLocation(), batch);
    else
      buf = fl->getBuffer();
    buf->flowplans.insert(this, fl_info.second, fl_info.first);
    buf->setChanged();
    fl->getOperation()->setChanged();
  } else {
    // Switch all flowplans of the same transfer batch
    auto oldFlow = fl;
    if (oldFlow->getOperation() != newfl->getOperation())
      throw DataException(
          "Only switching to a flow on the same operation is allowed");
    if (fl->getBuffer()->getItem()->hasType<ItemMTO>() && !batch.empty())
      buf = Buffer::findOrCreate(fl->getBuffer()->getItem(),
                                 fl->getBuffer()->getLocation(), batch);
    else
      buf = fl->getBuffer();
    for (auto flpln = getOperationPlan()->beginFlowPlans();
         flpln != getOperationPlan()->endFlowPlans(); ++flpln) {
      if (flpln->getFlow() != oldFlow) continue;

      // Remove from the old buffer
      flpln->buf->flowplans.erase(&*flpln);
      flpln->buf->setChanged();

      // Insert in the new buffer
      flpln->fl = newfl;
      auto fl_info = flpln->fl->getFlowplanDateQuantity(&*flpln);
      buf->flowplans.insert(&*flpln, fl_info.second, fl_info.first);
      buf->setChanged();
      flpln->fl->getOperation()->setChanged();
    }
  }
}

void FlowPlan::setItem(Item* newItem) {
  // Verify the data
  if (!newItem) throw DataException("Can't switch to nullptr flow");

  if (fl && fl->getBuffer()) {
    if (newItem == fl->getBuffer()->getItem())
      // No change
      return;
    else
      // Already set
      throw DataException("Item can be set only once on a flowplan");
  }

  // We are not expecting to use this method in this way...
  throw LogicException("Not implemented");
}

void FlowPlan::setQuantityRaw(double q) {
  if (buf) buf->flowplans.update(this, q, getDate());
}

pair<double, double> FlowPlan::setQuantity(double quantity, bool rounddown,
                                           bool, bool execute, short mode) {
  // TODO argument "update" isn't used
  if (getConfirmed()) {
    // Confirmed flowplans take any quantity, regardless of the
    // quantity of the owning operationplan.
    if (execute) {
      // Update the timeline data structure
      buf->flowplans.update(this, quantity, getDate());

      // Mark the operation and buffer as having changed. This will trigger the
      // recomputation of their problems
      buf->setChanged();
      fl->getOperation()->setChanged();
    }
    return make_pair(quantity, oper->getQuantity());
  }

  if (!getFlow()->getEffective().within(getDate())) {
    if (execute) {
      if (mode == 2 || (mode == 0 && getFlow()->hasType<FlowEnd>())) {
        oper->setOperationPlanParameters(
            0.0, Date::infinitePast, computeFlowToOperationDate(oper->getEnd()),
            true, execute, rounddown);
      } else if (mode == 1 || (mode == 0 && getFlow()->hasType<FlowStart>())) {
        oper->setOperationPlanParameters(
            0.0,
            (mode == 1 && getFlow()->hasType<FlowEnd>())
                ? oper->getStart()
                : computeFlowToOperationDate(oper->getStart()),
            Date::infinitePast, false, execute, rounddown);
      }
    }
    return make_pair(0.0, 0.0);
  }

  double opplan_quantity;
  bool less_than_fixed_qty =
      fabs(getFlow()->getQuantityFixed()) &&
      fabs(quantity) < fabs(getFlow()->getQuantityFixed()) + ROUNDING_ERROR;
  if (getFlow()->getQuantity() == 0.0 || less_than_fixed_qty) {
    // Fixed quantity flows only allow resizing to 0
    if (less_than_fixed_qty && oper->getQuantity() != 0.0) {
      if (mode == 2 || (mode == 0 && getFlow()->hasType<FlowEnd>()))
        opplan_quantity = oper->setOperationPlanParameters(
                                  0.0, Date::infinitePast,
                                  computeFlowToOperationDate(oper->getEnd()),
                                  true, execute, rounddown)
                              .quantity;
      else if (mode == 1 || (mode == 0 && getFlow()->hasType<FlowStart>()))
        opplan_quantity =
            oper->setOperationPlanParameters(
                    0.0,
                    (mode == 1 && getFlow()->hasType<FlowEnd>())
                        ? oper->getStart()
                        : computeFlowToOperationDate(oper->getStart()),
                    Date::infinitePast, false, execute, rounddown)
                .quantity;
      else
        throw LogicException("Unreachable code reached");
    } else if (!less_than_fixed_qty && oper->getQuantity() == 0.0) {
      if (mode == 2 || (mode == 0 && getFlow()->hasType<FlowEnd>()))
        opplan_quantity = oper->setOperationPlanParameters(
                                  0.001, Date::infinitePast,
                                  computeFlowToOperationDate(oper->getEnd()),
                                  true, execute, rounddown)
                              .quantity;
      else if (mode == 1 || (mode == 0 && getFlow()->hasType<FlowStart>()))
        opplan_quantity =
            oper->setOperationPlanParameters(
                    0.001,
                    (mode == 1 && getFlow()->hasType<FlowEnd>())
                        ? oper->getStart()
                        : computeFlowToOperationDate(oper->getStart()),
                    Date::infinitePast, false, execute, rounddown)
                .quantity;
      else
        throw LogicException("Unreachable code reached");
    }
  } else {
    // Proportional or transfer batch flows
    // For transfer batch flowplans the argument quantity is expected to be the
    // total quantity of all batches.
    if (mode == 2 || (mode == 0 && getFlow()->hasType<FlowEnd>()))
      opplan_quantity = oper->setOperationPlanParameters(
                                (quantity - getFlow()->getQuantityFixed()) /
                                    getFlow()->getQuantity(),
                                Date::infinitePast,
                                (mode == 2 || getFlow()->hasType<FlowStart>())
                                    ? oper->getEnd()
                                    : computeFlowToOperationDate(getDate()),
                                true, execute, rounddown)
                            .quantity;
    else if (mode == 1 || (mode == 0 && getFlow()->hasType<FlowStart>()))
      opplan_quantity = oper->setOperationPlanParameters(
                                (quantity - getFlow()->getQuantityFixed()) /
                                    getFlow()->getQuantity(),
                                (mode == 1 || getFlow()->hasType<FlowEnd>())
                                    ? oper->getStart()
                                    : computeFlowToOperationDate(getDate()),
                                Date::infinitePast, false, execute, rounddown)
                            .quantity;
    else
      throw LogicException("Unreachable code reached");
  }

  if (execute && oper->getOwner()) {
    // Update all sibling operationplans
    for (auto i = oper->getOwner()->firstsubopplan; i; i = i->nextsubopplan)
      if (i != oper) i->update();
  }

  if (opplan_quantity)
    return make_pair(opplan_quantity * getFlow()->getQuantity() +
                         getFlow()->getQuantityFixed(),
                     opplan_quantity);
  else
    return make_pair(0.0, 0.0);
}

int FlowPlanIterator::initialize() {
  // Initialize the type
  auto& x = PythonExtension<FlowPlanIterator>::getPythonType();
  x.setName("flowplanIterator");
  x.setDoc("frePPLe iterator for flowplan");
  x.supportiter();
  return x.typeReady();
}

PyObject* FlowPlanIterator::iternext() {
  FlowPlan* fl;
  if (buffer_or_opplan) {
    // Skip uninteresting entries
    while (*bufiter != buf->getFlowPlans().end() &&
           (*bufiter)->getQuantity() == 0.0)
      ++(*bufiter);
    if (*bufiter == buf->getFlowPlans().end()) return nullptr;
    fl = const_cast<FlowPlan*>(static_cast<const FlowPlan*>(&*((*bufiter)++)));
  } else {
    // Skip uninteresting entries
    while (*opplaniter != opplan->endFlowPlans() &&
           (*opplaniter)->getQuantity() == 0.0)
      ++(*opplaniter);
    if (*opplaniter == opplan->endFlowPlans()) return nullptr;
    fl = static_cast<FlowPlan*>(&*((*opplaniter)++));
  }
  Py_INCREF(fl);
  return const_cast<FlowPlan*>(fl);
}

Object* FlowPlan::reader(const MetaClass*, const DataValueDict& in,
                         CommandManager*) {
  // Pick up the operationplan attribute. An error is reported if it's missing.
  const DataValue* opplanElement = in.get(Tags::operationplan);
  if (!opplanElement) throw DataException("Missing operationplan field");
  Object* opplanobject = opplanElement->getObject();
  if (!opplanobject || !opplanobject->hasType<OperationPlan>())
    throw DataException("Invalid operationplan field");
  auto* opplan = static_cast<OperationPlan*>(opplanobject);

  // Pick up the item.
  const DataValue* itemElement = in.get(Tags::item);
  if (!itemElement) throw DataException("Item must be provided");
  Object* itemobject = itemElement->getObject();
  if (!itemobject || itemobject->getType().category != Item::metadata)
    throw DataException("Invalid item field");
  Item* itm = static_cast<Item*>(itemobject);

  // Find the flow for this item on the operationplan.
  // If multiple exist, we pick up the first one.
  // TODO detect situations where the flowplan is on an alternate material
  auto flplniter = opplan->getFlowPlans();
  FlowPlan* flpln;
  while ((flpln = flplniter.next())) {
    if (flpln->getItem() == itm) return flpln;
  }
  OperationPlan* correctowner = nullptr;
  Flow* correctflow = nullptr;
  for (auto& f : opplan->getOperation()->getFlows()) {
    if (f.getItem() == itm) {
      correctowner = opplan;
      correctflow = const_cast<Flow*>(&f);
      break;
    }
  }
  auto subopplans = opplan->getSubOperationPlans();
  OperationPlan* firstChildOpplan = nullptr;
  while (auto subopplan = subopplans.next()) {
    if (!firstChildOpplan) firstChildOpplan = subopplan;
    auto subflplniter = subopplan->getFlowPlans();
    FlowPlan* subflpln;
    while ((subflpln = subflplniter.next())) {
      if (subflpln->getItem() == itm) return subflpln;
    }
    if (!correctowner)
      for (auto& f : subopplan->getOperation()->getFlows()) {
        if (f.getItem() == itm) {
          correctowner = subopplan;
          correctflow = const_cast<Flow*>(&f);
          break;
        }
      }
  }

  // No existing flowplans is found, create a new one.
  // TODO code assumes consuming flowplans
  if (correctowner) opplan = correctowner;
  if (!correctowner && firstChildOpplan) opplan = firstChildOpplan;
  auto loc = opplan->getLocation();
  if (!loc) {
    loc = opplan->getOperation()->getLocation();
    if (!loc) return nullptr;
  }
  auto buf = Buffer::findOrCreate(itm, loc, opplan->getBatch());
  if (!correctflow) {
    correctflow = new FlowStart(opplan->getOperation(), buf, -1);
    correctflow->setHidden(true);
    correctflow->setEffectiveEnd(Date::infinitePast);
  }
  return new FlowPlan(opplan, correctflow);
}

PyObject* FlowPlan::create(PyTypeObject*, PyObject* , PyObject* kwds) {
  try {
    // Find or create the C++ object
    PythonDataValueDict atts(kwds);
    Object* x = reader(FlowPlan::metadata, atts, nullptr);
    if (!x) {
      Py_INCREF(Py_None);
      return Py_None;
    }
    Py_INCREF(x);

    // Iterate over extra keywords, and set attributes.
    if (x) {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value)) {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::operationplan) && !attr.isA(Tags::item)) {
          const MetaFieldBase* fmeta = x->getType().findField(attr.getHash());
          if (!fmeta && x->getType().category)
            fmeta = x->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(x, field);
          else
            x->setProperty(attr.getName(), value);
        }
      };
    }
    return x;
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

Duration FlowPlan::getPeriodOfCover() const {
  // Case 1: If the backlog is more than the onhand => period of cover is 0
  // We consider the initial stock - all confirmed consumptions - all overdue
  // demand
  double left_for_consumption = getBuffer()->getOnHand();
  auto fpiter = getBuffer()->getFlowPlans().begin(this);
  fpiter++;
  bool found = false;
  while (fpiter != getBuffer()->getFlowPlans().end()) {
    // subtract deliveries
    if (fpiter->getQuantity() < 0.0 && fpiter->getDate() >= getDate() &&
        fpiter->getOperationPlan()
            ->getOperation()
            ->hasType<OperationDelivery>() &&
        fpiter->getOperationPlan()->getDemand()->getDue() < getDate()) {
      left_for_consumption += fpiter->getQuantity();
      found = true;
    }
    // add confirmed/completed/approved replenishments
    if (fpiter->getQuantity() > 0.0 &&
        fpiter->getDate() <= getDate() + Duration(1L) &&
        (fpiter->getOperationPlan()->getStatus() == "approved" ||
         fpiter->getOperationPlan()->getStatus() == "confirmed" ||
         fpiter->getOperationPlan()->getStatus() == "completed"))
      left_for_consumption += fpiter->getQuantity();
    ++fpiter;
  }
  if (found && left_for_consumption < ROUNDING_ERROR) return Duration(0L);

  // Case 2: Regular case
  left_for_consumption = getOnhand();
  if (left_for_consumption > 0) {
    auto fpiter2 = getBuffer()->getFlowPlans().begin(this);
    ++fpiter2;
    while (fpiter2 != getBuffer()->getFlowPlans().end()) {
      if (fpiter2->getQuantity() < 0.0) {
        left_for_consumption += fpiter2->getQuantity();
        if (left_for_consumption < ROUNDING_ERROR)
          return fpiter2->getDate() - getDate();
      }
      ++fpiter2;
    }
  } else {
    // Case 3:
    // On hand is 0 so we display the next consumer's date
    auto fpiter2 = getBuffer()->getFlowPlans().begin(this);
    ++fpiter2;
    while (fpiter2 != getBuffer()->getFlowPlans().end()) {
      if (fpiter2->getQuantity() < 0.0) {
        return max(0L, fpiter2->getDate() - getDate() -
                           fpiter2->getOperationPlan()->getDelay());
      }
      ++fpiter2;
    }
  }

  return Duration(999L * 86400L);
}

bool FlowPlan::getFeasible() const {
  if (getBuffer()->hasType<BufferInfinite>()) return true;
  auto flplaniter = getBuffer()->getFlowPlans();
  for (auto cur = flplaniter.begin(this); cur != flplaniter.end(); ++cur) {
    if (cur->getOnhand() < -ROUNDING_ERROR && cur->isLastOnDate())
      // Material shortage
      return false;
  }
  return true;
}

}  // namespace frepple
