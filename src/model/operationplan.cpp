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

Tree OperationPlan::st;

const MetaClass* OperationPlan::metadata;
const MetaCategory* OperationPlan::metacategory;
const MetaClass* OperationPlan::InterruptionIterator::metadata;
const MetaCategory* OperationPlan::InterruptionIterator::metacategory;
unsigned long OperationPlan::counterMin = 1;
string OperationPlan::referenceMax;
bool OperationPlan::propagatesetups = true;

const MetaCategory* SetupEvent::metadata;

Location* OperationPlan::loc = nullptr;
Location* OperationPlan::ori = nullptr;
Supplier* OperationPlan::sup = nullptr;
string OperationPlan::ordertype;
Item* OperationPlan::itm = nullptr;

int OperationPlan::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<OperationPlan>(
      "operationplan", "operationplans", createOperationPlan,
      OperationPlan::finder);
  OperationPlan::metadata = MetaClass::registerClass<OperationPlan>(
      "operationplan", "operationplan", true);
  registerFields<OperationPlan>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python type
  auto& x = FreppleCategory<OperationPlan>::getPythonType();
  x.setName("operationplan");
  x.setDoc("frePPLe operationplan");
  x.supportgetattro();
  x.supportsetattro();
  x.supportstr();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  x.addMethod("calculateOperationTime", &calculateOperationTimePython,
              METH_VARARGS,
              "add or subtract a duration of operation hours from a date");
  x.addMethod("updateFeasible", &updateFeasiblePython, METH_NOARGS,
              "updates the flag whether this operationplan is feasible or not");
  x.addMethod("getColor", &getColorPython, METH_NOARGS,
              "returs a pair<double color, IP buffer>");
  metadata->setPythonClass(x);
  return x.typeReady();
}

PyObject* OperationPlan::str() const {
  ostringstream ch;
  ch << this;
  return PythonData(ch.str());
}

PyObject* OperationPlan::calculateOperationTimePython(PyObject* self,
                                                      PyObject* args) {
  // Pick up the argument
  PyObject* datepy;
  PyObject* durationpy;
  int forward = 1;

  if (!PyArg_ParseTuple(args, "OO|p:calculateOperationTime", &datepy,
                        &durationpy, &forward))
    return nullptr;

  try {
    auto opplan = static_cast<OperationPlan*>(self);
    Date dt = PythonData(datepy).getDate();
    Duration dur = PythonData(durationpy).getDuration();
    if (!opplan->getOperation())
      return PythonData(dt + dur);
    else {
      DateRange res = opplan->getOperation()->calculateOperationTime(
          opplan, dt, dur, (forward == 1));
      return PythonData(forward ? res.getEnd() : res.getStart());
    }
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

void OperationPlan::setChanged(bool b) {
  // Opplan itself
  if (owner)
    owner->setChanged(b);
  else {
    oper->setChanged(b);
    if (dmd) dmd->setChanged();
  }

  // Next routing step
  if (nextsubopplan) {
    if (nextsubopplan->owner)
      nextsubopplan->owner->setChanged(b);
    else {
      nextsubopplan->oper->setChanged(b);
      if (nextsubopplan->dmd) nextsubopplan->dmd->setChanged();
    }
  }

  // Previous step
  if (prevsubopplan) {
    if (prevsubopplan->owner)
      prevsubopplan->owner->setChanged(b);
    else {
      prevsubopplan->oper->setChanged(b);
      if (prevsubopplan->dmd) prevsubopplan->dmd->setChanged();
    }
  }

  // All dependencies
  for (auto i : dependencies) {
    if (i->getFirst() == this && i->getSecond()) {
      if (i->getSecond()->owner && i->getSecond()->owner != getOwner() &&
          i->getSecond()->owner != this)
        i->getSecond()->owner->setChanged(b);
      else {
        i->getSecond()->oper->setChanged(b);
        if (i->getSecond()->dmd) i->getSecond()->dmd->setChanged();
      }
    }
    if (i->getSecond() == this && i->getFirst()) {
      if (i->getFirst()->owner && i->getFirst()->owner != getOwner() &&
          i->getFirst()->owner != this)
        i->getFirst()->owner->setChanged(b);
      else {
        i->getFirst()->oper->setChanged(b);
        if (i->getFirst()->dmd) i->getFirst()->dmd->setChanged();
      }
    }
  }
}

void OperationPlan::restore(const OperationPlanState& x) {
  setSetupEvent(x.tmline, x.setup.getDate(), x.setup.getSetup(),
                x.setup.getRule());
  setStartEndAndQuantity(x.start, x.end, x.quantity);
  if (!SetupMatrix::empty()) scanSetupTimes();
}

Object* OperationPlan::createOperationPlan(const MetaClass*,
                                           const DataValueDict& in,
                                           CommandManager* mgr) {
  // Pick up the action attribute
  Action action = MetaClass::decodeAction(in);

  // Check the order type
  string ordtype;
  const DataValue* ordtypeval = in.get(Tags::ordertype);
  if (ordtypeval) ordtype = ordtypeval->getString();

  // Decode the operationplan identifier
  string id;
  const DataValue* ref = in.get(Tags::reference);
  if (ref) id = ref->getString();
  if (id.empty()) {
    const DataValue* idfier = in.get(Tags::id);
    if (idfier) id = idfier->getString();
  }
  if (id.empty() && (action == Action::CHANGE || action == Action::REMOVE))
    // Identifier is required
    throw DataException("Missing reference or identifier field");

  // If an identifier is specified, we look up this operation plan
  OperationPlan* opplan = nullptr;
  if (!id.empty()) {
    opplan = OperationPlan::findReference(id);
    if (opplan) {
      // Check whether previous and current operations match.
      if (ordtype.empty()) {
        ordtype = opplan->getOrderType();
        if (ordtype == "ALT") ordtype = "MO";
      } else if (ordtype != opplan->getOrderType()) {
        ostringstream ch;
        ch << "Operationplan identifier " << id
           << " defined multiple times for different order types";
        throw DataException(ch.str());
      }
    }
  }

  // Decode the attributes
  Object* operval = nullptr;
  Object* itemval = nullptr;
  Object* locval = nullptr;
  Object* supval = nullptr;
  Object* orival = nullptr;
  Object* dmdval = nullptr;
  Object* itemdistributionval = nullptr;
  if (ordtype == "MO" || ordtype.empty()) {
    const DataValue* val = in.get(Tags::operation);
    if (!val && action == Action::ADD)
      throw DataException("Missing operation field");
    if (val) {
      operval = val->getObject();
      if (operval && operval->getType().category != Operation::metadata)
        throw DataException(
            "Operation field on operationplan must be of type operation");
    }
  } else if (ordtype == "PO") {
    const DataValue* val = in.get(Tags::supplier);
    if (!val && action == Action::ADD)
      throw DataException("Missing supplier field");
    if (val) {
      supval = val->getObject();
      if (supval && supval->getType().category != Supplier::metadata)
        throw DataException(
            "Supplier field on operationplan must be of type supplier");
    }
    val = in.get(Tags::item);
    if (!val && action == Action::ADD)
      throw DataException("Missing item field");
    if (val) {
      itemval = val->getObject();
      if (itemval && itemval->getType().category != Item::metadata)
        throw DataException("Item field on operationplan must be of type item");
    }
    val = in.get(Tags::location);
    if (!val && action == Action::ADD)
      throw DataException("Missing location field");
    if (val) {
      locval = val->getObject();
      if (locval && locval->getType().category != Location::metadata)
        throw DataException(
            "Location field on operationplan must be of type location");
    }
  } else if (ordtype == "DO") {
    const DataValue* val = in.get(Tags::itemdistribution);
    if (val) {
      itemdistributionval = val->getObject();
      if (itemdistributionval && itemdistributionval->getType().category !=
                                     ItemDistribution::metacategory)
        throw DataException(
            "Itemdistribution field on operationplan must be of type "
            "itemdistribution");
    } else {
      val = in.get(Tags::origin);
      if (val) {
        orival = val->getObject();
        if (orival && orival->getType().category != Location::metadata)
          throw DataException(
              "Origin field on a distribution order must be of type location");
      }
      val = in.get(Tags::item);
      if (!val && action == Action::ADD)
        throw DataException("Missing item field");
      if (val) {
        itemval = val->getObject();
        if (itemval && itemval->getType().category != Item::metadata)
          throw DataException(
              "Item field on distribution order must be of type item");
      }
      val = in.get(Tags::location);
      if (!val && action == Action::ADD)
        throw DataException("Missing location field");
      if (val) {
        locval = val->getObject();
        if (locval && locval->getType().category != Location::metadata)
          throw DataException(
              "Location field on distribution order must be of type location");
      }
    }
  } else if (ordtype == "DLVR") {
    const DataValue* val = in.get(Tags::demand);
    if (!val && action == Action::ADD)
      throw DataException("Missing demand field");
    if (val) {
      dmdval = val->getObject();
      if (!dmdval)
        throw DataException("Empty demand field");
      else if (dmdval->getType().category != Demand::metadata) {
        Demand* tmp = dynamic_cast<Demand*>(dmdval);
        if (!tmp)
          throw DataException(
              "Demand field on operationplan must be of type demand");
      }
    }
    val = in.get(Tags::item);
    if (!val && action == Action::ADD)
      throw DataException("Missing item field");
    if (val) {
      itemval = val->getObject();
      if (itemval && itemval->getType().category != Item::metadata)
        throw DataException("Item field on operationplan must be of type item");
    }
    val = in.get(Tags::location);
    if (!val && action == Action::ADD)
      throw DataException("Missing location field");
    if (val) {
      locval = val->getObject();
      if (locval && locval->getType().category != Location::metadata)
        throw DataException(
            "Location field on operationplan must be of type location");
    }
  } else
    // Unknown order type for operationplan. We won't read it.
    return nullptr;

  // Execute the proper action
  switch (action) {
    case Action::REMOVE:
      if (opplan) {
        // Send out the notification to subscribers
        if (opplan->getType().raiseEvent(opplan, SIG_REMOVE))
          // Delete it
          delete opplan;
        else {
          // The callbacks disallowed the deletion!
          ostringstream ch;
          ch << "Can't delete operationplan with reference " << id;
          throw DataException(ch.str());
        }
      } else {
        ostringstream ch;
        ch << "Operationplan with reference " << id << " doesn't exist";
        throw DataException(ch.str());
      }
      return nullptr;
    case Action::ADD:
      if (opplan) {
        ostringstream ch;
        ch << "Operationplan with reference " << id
           << " already exists and can't be added again";
        throw DataException(ch.str());
      }
      break;
    case Action::CHANGE:
      if (!opplan) {
        ostringstream ch;
        ch << "Operationplan with reference " << id << " doesn't exist";
        throw DataException(ch.str());
      }
      break;
    case Action::ADD_CHANGE:;
  }

  // Flag whether or not to create sub operationplans
  bool create = true;
  const DataValue* py_create = in.get(Tags::create);
  if (py_create) create = py_create->getBool();

  // Get start, end, quantity, status and batch fields
  const DataValue* startfld = in.get(Tags::start);
  Date start;
  if (startfld) start = startfld->getDate();
  const DataValue* endfld = in.get(Tags::end);
  Date end;
  if (endfld) {
    end = endfld->getDate();
    if (startfld && start > end && start && end && end != Date::infiniteFuture)
      start = end;
  }
  const DataValue* quantityfld = in.get(Tags::quantity);
  double quantity = quantityfld ? quantityfld->getDouble() : 0.0;
  bool statuspropagation = true;
  const DataValue* statusfld = in.get(Tags::status);
  string status;
  if (statusfld)
    status = statusfld->getString();
  else {
    statusfld = in.get(Tags::statusNoPropagation);
    if (statusfld) status = statusfld->getString();
    statuspropagation = false;
  }
  PooledString batch;
  const DataValue* batchfld = in.get(Tags::batch);
  if (batchfld) batch = batchfld->getString();
  const DataValue* quantityCompletedfld = in.get(Tags::quantity_completed);
  double quantity_completed =
      quantityCompletedfld ? quantityCompletedfld->getDouble() : 0.0;

  // Get list of assigned resources
  vector<Resource*> assigned_resources;
  const DataValue* reslist = in.get(Tags::resources);
  if (reslist) {
    for (auto& resname : reslist->getStringList()) {
      auto r = Resource::find(resname);
      if (r) assigned_resources.push_back(r);
    }
  }

  // Return the existing operationplan
  if (opplan) {
    if (operval) opplan->setOperation(static_cast<Operation*>(operval));
    if (locval) opplan->setLocation(dynamic_cast<Location*>(locval));
    if (itemval) opplan->setItem(dynamic_cast<Item*>(itemval));
    if (supval) opplan->setSupplier(dynamic_cast<Supplier*>(supval));
    if (orival) opplan->setOrigin(dynamic_cast<Location*>(orival));
    opplan->setForcedUpdate(true);
    if (batchfld) opplan->setBatch(batch);
    if (statusfld) opplan->setStatus(status);
    if (quantityCompletedfld) opplan->setQuantityCompleted(quantity_completed);
    if (!assigned_resources.empty()) {
      opplan->setResetResources(true);
      opplan->createFlowLoads(&assigned_resources);
    }
    if ((quantityfld || !assigned_resources.empty()) && !startfld && !endfld)
      opplan->setOperationPlanParameters(
          quantityfld ? quantity : opplan->getQuantity(), opplan->getStart(),
          Date::infinitePast);
    else if ((quantityfld || !assigned_resources.empty()) || startfld || endfld)
      opplan->setOperationPlanParameters(
          quantityfld ? quantity : opplan->getQuantity(), start, end);
    opplan->setForcedUpdate(false);
    return opplan;
  }

  // Create a new operation plan
  if (!start && !end) start = Plan::instance().getCurrent();
  if (ordtype == "PO") {
    // Find or create the destination buffer.
    if (!itemval) throw DataException("Missing item field");
    if (!locval) throw DataException("Missing location field");
    Buffer* destbuffer = nullptr;
    Item::bufferIterator buf_iter(static_cast<Item*>(itemval));
    while (Buffer* tmpbuf = buf_iter.next()) {
      if (tmpbuf->getLocation() == static_cast<Location*>(locval) &&
          !tmpbuf->getBatch()) {
        if (destbuffer) {
          stringstream o;
          o << "Multiple buffers found for item '"
            << static_cast<Item*>(itemval) << "' and location'"
            << static_cast<Location*>(locval) << "'";
          throw DataException(o.str());
        }
        destbuffer = tmpbuf;
      }
    }
    if (!destbuffer)
      // Create the destination buffer
      destbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval),
                                        static_cast<Location*>(locval));

    // Build the producing operation for this buffer.
    destbuffer->getProducingOperation();

    // Look for a matching operation replenishing this buffer.
    for (auto flowiter = destbuffer->getFlows().begin();
         flowiter != destbuffer->getFlows().end() && !operval; ++flowiter) {
      if (!flowiter->getOperation()->hasType<OperationItemSupplier>()) continue;
      OperationItemSupplier* opitemsupplier =
          static_cast<OperationItemSupplier*>(flowiter->getOperation());
      if (supval) {
        if (static_cast<Supplier*>(supval)->isMemberOf(
                opitemsupplier->getItemSupplier()->getSupplier()))
          operval = opitemsupplier;
      } else
        operval = opitemsupplier;
    }

    // No matching operation is found.
    if (!operval) {
      // We'll create one now, but that requires that we have a supplier
      // defined.
      if (!supval)
        throw DataException("Supplier is needed on this purchase order");
      // Note: We know that we need to create a new one. An existing one would
      // have created an operation on the buffer already.
      ItemSupplier* itemsupplier = new ItemSupplier();
      itemsupplier->setSupplier(static_cast<Supplier*>(supval));
      itemsupplier->setItem(static_cast<Item*>(itemval));
      itemsupplier->setLocation(static_cast<Location*>(locval));
      itemsupplier->setHidden(true);
      itemsupplier->setPriority(0);
      operval = new OperationItemSupplier(itemsupplier, destbuffer);
      // Create operation plan
      opplan = static_cast<Operation*>(operval)->createOperationPlan(
          quantity, start, end, batch, nullptr, nullptr, 0, false, id);
      new ProblemInvalidData(opplan,
                             "Purchase order '" + opplan->getReference() +
                                 "' on unauthorized supplier ",
                             "operationplan", start, end);
    } else
      // Create the operationplan
      opplan = static_cast<Operation*>(operval)->createOperationPlan(
          quantity, start, end, batch, nullptr, nullptr, 0, false, id);
  } else if (ordtype == "DO") {
    // Find or create the destination buffer.
    if (itemdistributionval) {
      itemval = static_cast<ItemDistribution*>(itemdistributionval)->getItem();
      locval =
          static_cast<ItemDistribution*>(itemdistributionval)->getDestination();
      orival = static_cast<ItemDistribution*>(itemdistributionval)->getOrigin();
    }
    if (!itemval) throw DataException("Missing item field");
    if (!locval && !orival)
      throw DataException("Missing both origin and location field");
    Buffer* destbuffer = nullptr;
    if (locval) {
      // Use the destination location
      Item::bufferIterator buf_iter(static_cast<Item*>(itemval));
      while (Buffer* tmpbuf = buf_iter.next()) {
        if (tmpbuf->getLocation() == static_cast<Location*>(locval) &&
            !tmpbuf->getBatch()) {
          if (destbuffer) {
            stringstream o;
            o << "Multiple buffers found for item '"
              << static_cast<Item*>(itemval) << "' and location '"
              << static_cast<Location*>(locval) << "'";
            throw DataException(o.str());
          }
          destbuffer = tmpbuf;
        }
      }
      if (!destbuffer)
        // Create the destination buffer
        destbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval),
                                          static_cast<Location*>(locval));

      // Build the producing operation for this buffer.
      destbuffer->getProducingOperation();

      // Look for a matching operation replenishing this buffer.
      for (auto flowiter = destbuffer->getFlows().begin();
           flowiter != destbuffer->getFlows().end() && !operval; ++flowiter) {
        if (!flowiter->getOperation()->hasType<OperationItemDistribution>() ||
            flowiter->getQuantity() <= 0)
          continue;
        OperationItemDistribution* opitemdist =
            static_cast<OperationItemDistribution*>(flowiter->getOperation());
        // Origin must match as well
        if (orival) {
          for (auto fl = opitemdist->getFlows().begin();
               fl != opitemdist->getFlows().end(); ++fl) {
            if (fl->getQuantity() < 0 &&
                fl->getBuffer()->getLocation()->isMemberOf(
                    static_cast<Location*>(orival)) &&
                !fl->getBuffer()->getBatch())
              operval = opitemdist;
          }
        } else if (!opitemdist->getOrigin())
          operval = opitemdist;
      }
    } else {
      // Use only the source location to find an operation
      stringstream o;
      o << "Ship " << static_cast<Item*>(itemval)->getName() << " from "
        << static_cast<Location*>(orival)->getName();
      operval = Operation::find(o.str());
    }

    // No matching operation is found.
    if (!operval) {
      // We'll create one now if an origin is defined
      Buffer* originbuffer = nullptr;
      if (orival) {
        auto bufiter = static_cast<Item*>(itemval)->getBufferIterator();
        while (Buffer* tmpbuf = bufiter.next()) {
          if (tmpbuf->getLocation() == static_cast<Location*>(orival) &&
              !tmpbuf->getBatch()) {
            if (originbuffer) {
              stringstream o;
              o << "Multiple buffers found for item '"
                << static_cast<Item*>(itemval) << "' and location '"
                << static_cast<Location*>(orival) << "'";
              throw DataException(o.str());
            }
            originbuffer = tmpbuf;
          }
        }
        if (!originbuffer)
          // Create the origin buffer
          originbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval),
                                              static_cast<Location*>(orival));
      }

      // Create itemdistribution when not provided
      if (!itemdistributionval) {
        itemdistributionval = new ItemDistribution();
        if (orival)
          static_cast<ItemDistribution*>(itemdistributionval)
              ->setOrigin(static_cast<Location*>(orival));
        static_cast<ItemDistribution*>(itemdistributionval)
            ->setItem(static_cast<Item*>(itemval));
        if (locval)
          static_cast<ItemDistribution*>(itemdistributionval)
              ->setDestination(static_cast<Location*>(locval));
        static_cast<ItemDistribution*>(itemdistributionval)->setPriority(0);
      }

      // Create operation when it doesn't exist yet
      operval = nullptr;
      auto oper_iter =
          static_cast<ItemDistribution*>(itemdistributionval)->getOperations();
      while (OperationItemDistribution* oper2 = oper_iter.next()) {
        if (oper2->getOrigin() == originbuffer &&
            oper2->getDestination() == destbuffer) {
          operval = oper2;
          break;
        }
      }
      if (!operval)
        operval = new OperationItemDistribution(
            static_cast<ItemDistribution*>(itemdistributionval), originbuffer,
            destbuffer);

      // Create operation plan
      opplan = static_cast<Operation*>(operval)->createOperationPlan(
          quantity, start, end, batch, nullptr, nullptr, 0, false, id);

      // Make sure no problem is reported when item distribution priority is 0
      // (Rebalancing) Checking that no item distribution in reverse mode exists
      bool found = false;
      auto itemdist_iter =
          (static_cast<Item*>(itemval))->getDistributionIterator();
      while (ItemDistribution* i = itemdist_iter.next()) {
        if (i->getOrigin() ==
                static_cast<ItemDistribution*>(itemdistributionval)
                    ->getDestination() &&
            i->getDestination() ==
                static_cast<ItemDistribution*>(itemdistributionval)
                    ->getOrigin()) {
          found = true;
          break;
        }
      }
      if (!found)
        new ProblemInvalidData(opplan,
                               "Distribution order '" + opplan->getReference() +
                                   "' on unknown item distribution",
                               "operationplan", start, end);
    } else
      // Create operation plan
      opplan = static_cast<Operation*>(operval)->createOperationPlan(
          quantity, start, end, batch, nullptr, nullptr, 0, false, id);
  } else if (ordtype == "DLVR") {
    // Find or create the destination buffer.
    if (!itemval) throw DataException("Missing item field");
    if (!locval) throw DataException("Missing location field");
    Buffer* destbuffer = nullptr;
    Item::bufferIterator buf_iter(static_cast<Item*>(itemval));
    while (Buffer* tmpbuf = buf_iter.next()) {
      if (tmpbuf->getLocation() == static_cast<Location*>(locval) &&
          !tmpbuf->getBatch()) {
        if (destbuffer) {
          stringstream o;
          o << "Multiple buffers found for item '"
            << static_cast<Item*>(itemval) << "' and location '"
            << static_cast<Location*>(locval) << "'";
          throw DataException(o.str());
        }
        destbuffer = tmpbuf;
      }
    }
    if (!destbuffer)
      // Create the destination buffer
      destbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval),
                                        static_cast<Location*>(locval));

    // Create new operation if not found
    operval =
        Operation::find("Ship " + static_cast<Item*>(itemval)->getName() +
                        " @ " + static_cast<Location*>(locval)->getName());
    if (!operval) {
      operval = new OperationDelivery();
      static_cast<OperationDelivery*>(operval)->setBuffer(destbuffer);
    }

    // Create operation plan
    opplan = static_cast<Operation*>(operval)->createOperationPlan(
        quantity, start, end, batch, nullptr, nullptr, 0, false, id);
    static_cast<Demand*>(dmdval)->addDelivery(opplan);
  } else {
    if (!operval)
      // Can't create operationplan because the operation doesn't exist
      throw DataException("Missing operation field");

    // Create an operationplan
    if (static_cast<Operation*>(operval)->getItem() &&
        static_cast<Operation*>(operval)->getLocation()) {
      auto buf =
          Buffer::findOrCreate(static_cast<Operation*>(operval)->getItem(),
                               static_cast<Operation*>(operval)->getLocation());
      buf->correctProducingFlow(static_cast<Operation*>(operval));
    }
    opplan = static_cast<Operation*>(operval)->createOperationPlan(
        quantity, start, end, batch, nullptr, nullptr, 0, false, id,
        quantity_completed, status, &assigned_resources);
    if (!opplan->getType().raiseEvent(opplan, SIG_ADD)) {
      delete opplan;
      throw DataException("Can't create operationplan");
    }
  }

  // Special case: if the operation plan is locked, we need to
  // process the start and end date before locking it.
  // Subsequent calls won't affect the operationplan any longer.
  if (statusfld && status != "proposed") {
    opplan->setStatus(status, statuspropagation, true);
    if (opplan->getApproved() ||
        (opplan->getConfirmed() && opplan->getQuantityCompleted())) {
      if (assigned_resources.empty())
        opplan->createFlowLoads();
      else
        opplan->createFlowLoads(&assigned_resources);
      // The end date of the approved operationplan needs to be computed in
      // function of the start date and the quantity completed.
      opplan->setOperationPlanParameters(
          quantity, start ? start : opplan->getStart(), Date::infinitePast,
          false, true, false, true);
    } else
      opplan->freezeStatus(start ? start : opplan->getStart(),
                           end ? end : opplan->getEnd(), quantity);
  }
  if (!opplan->activate(create, start))
    throw DataException("Can't create operationplan");

  // Report the operationplan creation to the manager
  if (mgr) mgr->add(new CommandCreateObject(opplan));

  return opplan;
}

OperationPlan* OperationPlan::findReference(string const& l) {
  bool guarantueed = false;

  // Compare with the max reference string
  if (referenceMax < l) guarantueed = true;

  // Compare with the max counter
  try {
    unsigned long idx = stoul(l);
    if (idx > counterMin)
      guarantueed = true;
    else
      guarantueed = false;
  } catch (...) { /* The reference isn't a numeric value */
  }

  // We are sure not to find it
  if (guarantueed) return nullptr;

  // Look up in the tree
  auto tmp = st.find(l);
  return tmp == st.end() ? nullptr : static_cast<OperationPlan*>(tmp);
}

bool OperationPlan::assignReference() {
  // Need to assure that ids are unique!
  static mutex onlyOne;
  lock_guard<mutex> l(onlyOne);
  if (!getName().empty()) {
    // An identifier was read in from input
    if (getName() < referenceMax) {
      // The assigned id potentially clashes with an existing operationplan.
      // Check whether it clashes with existing operationplans
      OperationPlan* opplan = static_cast<OperationPlan*>(st.find(getName()));
      if (opplan != st.end() && opplan->getOperation() != oper) return false;
    } else
      // The new operationplan definitely doesn't clash with existing id's.
      // The counter need updating to garantuee that counter is always
      // a safe starting point for tagging new operationplans.
      referenceMax = getName();
    try {
      unsigned long idx = stoul(getName());
      if (idx >= counterMin) {
        if (idx >= ULONG_MAX)
          throw RuntimeException(
              "Exhausted the range of available operationplan references");
        counterMin = idx + 1;
      }
    } catch (...) { /* The reference isn't a numeric value */
    }
  } else {
    // Fresh operationplan with blank id
    setName(to_string(counterMin++));
    if (counterMin >= ULONG_MAX)
      throw RuntimeException(
          "Exhausted the range of available operationplan references");
  }

  // Insert in the tree of operationplans
  st.insert(this);

  return true;
}

void OperationPlan::setOperation(Operation* o) {
  if (oper == o) return;
  if (oper) {
    // Switching operations
    deleteFlowLoads();
    removeFromOperationplanList();

    // Delete existing sub operationplans
    auto x = firstsubopplan;
    while (x) {
      auto* y = x->nextsubopplan;
      x->owner =
          nullptr;  // Need to clear before destroying the suboperationplan
      delete x;
      x = y;
    }
    firstsubopplan = nullptr;
    lastsubopplan = nullptr;

    // Apply the change
    oper = o;
    oper->setOperationPlanParameters(this, quantity, dates.getStart(),
                                     Date::infinitePast, false, true, false);
  } else
    // First initialization of the operationplan
    oper = o;
  activate();
}

bool OperationPlan::activate(bool createsubopplans, bool use_start) {
  // At least a valid operation pointer must exist
  if (!oper) throw LogicException("Initializing an invalid operationplan");

  // Avoid negative quantities, and call operation specific activation code
  if (getQuantity() < 0.0 ||
      !oper->extraInstantiate(this, createsubopplans, use_start) ||
      (getQuantity() == 0.0 && getProposed() && !getOwner())) {
    delete this;
    return false;
  }

  // Instantiate all suboperationplans as well
  OperationPlan::iterator x(this);
  if (x != end()) {
    while (x != end()) {
      OperationPlan* tmp = &*x;
      ++x;
      tmp->activate();
    }
    x = OperationPlan::iterator(this);
    if (x == end()) {
      delete this;
      return false;
    }
  }

  // Mark as activated by assigning a unique identifier.
  setActivated(true);
  if (!getName().empty()) {
    // Validate the user provided id.
    if (!assignReference()) {
      ostringstream ch;
      ch << "Operationplan id " << getName() << " assigned multiple times";
      delete this;
      throw DataException(ch.str());
    }
  }

  // Insert into the doubly linked list of operationplans.
  insertInOperationplanList();

  // If we used the lazy creator, the flow- and loadplans have not been
  // created yet. We do it now...
  createFlowLoads();

  // Update the feasibility flag.
  updateFeasible();

  // Mark the operation to detect its problems
  // Note that a single operationplan thus retriggers the problem computation
  // for all operationplans of this operation. For models with 1) a large
  // number of operationplans per operation and 2) very frequent problem
  // detection, this could constitute a scalability problem. This combination
  // is expected to be unusual and rare, justifying this design choice.
  oper->setChanged();

  // The operationplan is valid
  return true;
}

void OperationPlan::deactivate() {
  // Mark as not activated
  st.erase(this);
  setName("0");

  // Delete from the list of deliveries
  if (dmd) dmd->removeDelivery(this);

  // Delete from the operationplan list
  removeFromOperationplanList();

  // Mark the operation to detect its problems
  oper->setChanged();
}

void OperationPlan::insertInOperationplanList() {
  // Check if already linked, or nothing to link
  if (prev || !oper || oper->first_opplan == this) return;

  if (!oper->first_opplan) {
    // First operationplan in the list
    oper->first_opplan = this;
    oper->last_opplan = this;
  } else if (*this < *(oper->first_opplan)) {
    // First in the list
    next = oper->first_opplan;
    next->prev = this;
    oper->first_opplan = this;
  } else if (*(oper->last_opplan) < *this) {
    // Last in the list
    prev = oper->last_opplan;
    prev->next = this;
    oper->last_opplan = this;
  } else {
    // Insert in the middle of the list
    OperationPlan* x = oper->last_opplan;
    OperationPlan* y = nullptr;
    while (!(*x < *this)) {
      y = x;
      x = x->prev;
    }
    next = y;
    prev = x;
    if (x) x->next = this;
    if (y) y->prev = this;
  }
}

void OperationPlan::removeFromOperationplanList() {
  if (prev)
    // In the middle
    prev->next = next;
  else if (oper->first_opplan == this)
    // First opplan in the list of this operation
    oper->first_opplan = next;
  if (next)
    // In the middle
    next->prev = prev;
  else if (oper->last_opplan == this)
    // Last opplan in the list of this operation
    oper->last_opplan = prev;
  // Clear existing pointers to become an orphan
  prev = nullptr;
  next = nullptr;
}

void OperationPlan::updateOperationplanList() {
  if (!oper) return;

  // Check ordering on the left
  while (prev && !(*prev < *this)) {
    OperationPlan* n = next;
    OperationPlan* p = prev;
    if (p->prev)
      p->prev->next = this;
    else
      oper->first_opplan = this;
    p->next = n;
    next = p;
    prev = p->prev;
    if (n)
      n->prev = p;
    else
      oper->last_opplan = p;
    p->prev = this;
  }

  // Check ordering on the right
  while (next && !(*this < *next)) {
    OperationPlan* n = next;
    OperationPlan* p = prev;
    next = n->next;
    if (n->next)
      n->next->prev = this;
    else
      oper->last_opplan = this;
    if (p)
      p->next = n;
    else
      oper->first_opplan = n;
    n->next = this;
    n->prev = p;
    prev = n;
  }
}

void OperationPlan::eraseSubOperationPlan(OperationPlan* o) {
  // Check
  if (!o) return;

  // Check valid ownership
  if (o->owner != this)
    throw LogicException("Suboperationplan has a different owner");

  // Remove from the list
  if (o->prevsubopplan)
    o->prevsubopplan->nextsubopplan = o->nextsubopplan;
  else
    firstsubopplan = o->nextsubopplan;
  if (o->nextsubopplan)
    o->nextsubopplan->prevsubopplan = o->prevsubopplan;
  else
    lastsubopplan = o->prevsubopplan;

  // Clear fields
  o->owner = nullptr;
  prevsubopplan = nullptr;
  nextsubopplan = nullptr;
};

bool OperationPlan::operator<(const OperationPlan& a) const {
  // Different operations
  if (oper != a.oper) return *oper < *(a.oper);

  // Different setup end date
  if (getSetupEnd() != a.getSetupEnd()) return getSetupEnd() < a.getSetupEnd();

  // Sort based on quantity
  if (fabs(quantity - a.quantity) > ROUNDING_ERROR)
    return quantity >= a.quantity;

  if (getActivated() != a.getActivated())
    // Keep unactivated operationplans separate
    return getActivated() > a.getActivated();

  if (getEnd() != a.getEnd())
    // Use the end date
    return getEnd() < a.getEnd();

  if (getName() != a.getName())
    // Use the reference (without auto-generating new ones)
    return getName() < a.getName();

  // Using a pointer comparison as tie breaker. This can give
  // results that are not reproducible across platforms and runs.
  return this < &a;
}

void OperationPlan::createFlowLoads(
    const vector<Resource*>* assigned_resources) {
  // Initialized already, or nothing to initialize
  if (!oper) return;
  if ((firstflowplan || firstloadplan) && !assigned_resources) return;

  if (oper->getMTO() && !getBatch() && getProposed() &&
      !oper->hasType<OperationInventory>())
    // Automagically generate a batch for proposed operationplans
    setBatch(getReference());

  // Create loadplans
  if (getConsumeCapacity()) {
    if (!assigned_resources) {
      // No previous assignments to restore
      for (auto& g : oper->getLoads()) {
        if (!g.getAlternate() && !g.getHiddenLoad()) new LoadPlan(this, &g);
      }
    } else {
      // Restore previous assignments
      setResetResources(true);
      for (auto& res : *assigned_resources) {
        Resource* backup_res = nullptr;
        const Load* backup_ld = nullptr;
        bool found = false;
        for (Resource::memberRecursiveIterator mmbr(res); !mmbr.empty();
             ++mmbr) {
          if (mmbr->isGroup()) continue;
          for (auto& g : oper->getLoads()) {
            if (!g.getAlternate() && mmbr->isMemberOf(g.getResource())) {
              if (!g.getSkill() || mmbr->hasSkill(g.getSkill(), getStart())) {
                new LoadPlan(this, &g, &*mmbr);
                found = true;
                break;
              } else if (!backup_res) {
                backup_res = &*mmbr;
                backup_ld = &g;
              }
            }
          }
        }
        if (!found && backup_res)
          new LoadPlan(this, backup_ld, backup_res);
        else if (!found) {
          // Operation has no load for this resource yet.
          auto hanging_load = new Load(oper, res, 1.0);
          hanging_load->setHidden(true);
          new LoadPlan(this, backup_ld, res);
        }
      }
    }
  }

  // Create flowplans for flows
  if (!Plan::instance().getSuppressFlowplanCreation() && !firstflowplan)
    for (auto& h : oper->getFlows()) {
      // Only the primary flow is instantiated.
      // Also for transfer batches, we only need to create the first flowplan.
      // The getFlowplanDateQuantity method will be called during the creation,
      // and create additional flowplans as required.
      if (!h.getAlternate()) new FlowPlan(this, &h);
    }
}

void OperationPlan::deleteFlowLoads() {
  // If no flowplans and loadplans, the work is already done
  if (!firstflowplan && !firstloadplan) return;

  FlowPlanIterator e = beginFlowPlans();
  firstflowplan = nullptr;  // Important to do this before the delete!
  LoadPlanIterator f = beginLoadPlans();
  firstloadplan = nullptr;  // Important to do this before the delete!

  // Delete the flowplans
  while (e != endFlowPlans()) delete &*(e++);

  // Delete the loadplans (including the setup suboperationplan)
  while (f != endLoadPlans()) delete &*(f++);

  // Delete setup event
  clearSetupEvent();
}

double OperationPlan::getTotalFlowAux(const Buffer* b) const {
  double q = 0.0;

  // Add my own quantity
  for (auto f = beginFlowPlans(); f != endFlowPlans(); ++f)
    if (f->getBuffer() == b) q += f->getQuantity();

  // Add the quantity of all children
  for (auto c = firstsubopplan; c; c = c->nextsubopplan)
    q += c->getTotalFlowAux(b);

  // Return result
  return q;
}

OperationPlan::~OperationPlan() {
  // Delete from the operationplan tree
  st.erase(this);

  // Delete the setup event
  if (setupevent) {
    setupevent->erase();
    delete setupevent;
  }

  // Delete the flowplans and loadplan
  deleteFlowLoads();

  // Initialize
  OperationPlan* x = firstsubopplan;
  firstsubopplan = nullptr;
  lastsubopplan = nullptr;

  // Delete the sub operationplans
  while (x) {
    OperationPlan* y = x->nextsubopplan;
    x->owner = nullptr;  // Need to clear before destroying the suboperationplan
    delete x;
    x = y;
  }

  // Delete also the owner
  if (owner) {
    const OperationPlan* o = owner;
    setOwner(nullptr);
    delete o;
  }

  // Delete from the list of deliveries
  if (dmd) dmd->removeDelivery(this);

  // Delete from the operationplan list
  removeFromOperationplanList();

  // Delete dependencies
  while (!dependencies.empty()) delete dependencies.front();
}

void OperationPlan::setOwner(OperationPlan* o, bool fast) {
  // Special case: the same owner is set twice
  if (owner == o) return;
  if (o) {
    // Check if the parent operation can have children
    if (!o->getOperation()
             ->hasType<OperationAlternate, OperationSplit, OperationRouting>())
      throw DataException("Invalid parent operationplan");
    // Register with the new owner
    o->getOperation()->addSubOperationPlan(o, this, fast);
    if (o->getBatch())
      setBatch(o->getBatch(), false);
    else if (!getBatch())
      o->setBatch(getBatch());
  } else if (owner)
    // Setting the owner field to nullptr
    owner->eraseSubOperationPlan(this);
}

void OperationPlan::setStart(Date d, bool force, bool preferEnd) {
  // Confirmed opplans don't move
  if (getConfirmed()) {
    if (force) setStartAndEnd(d, getEnd() > d ? getEnd() : d);
    return;
  }

  if (!lastsubopplan)
    // No sub operationplans
    oper->setOperationPlanParameters(this, quantity, d, Date::infinitePast,
                                     preferEnd, true, false);
  else {
    // Move all sub-operationplans in an orderly fashion
    for (auto i = firstsubopplan; i; i = i->nextsubopplan) {
      if (i->getStart() < d) {
        i->setStart(d, force, preferEnd);
        d = i->getEnd();
      } else
        // There is sufficient slack between the suboperationplans
        break;
    }
  }

  // Keep dependencies ordered
  if (force)
    for (auto i : dependencies) {
      if (i->getFirst() == this) {
        auto tmp = getEnd();
        if (i->getOperationDependency())
          tmp += i->getOperationDependency()->getHardSafetyLeadtime();
        if (i->getSecond()->getStart() < tmp) {
          i->getSecond()->setStart(tmp);
        }
      } else if (i->getSecond() == this) {
        auto tmp = getStart();
        if (i->getOperationDependency())
          tmp -= i->getOperationDependency()->getHardSafetyLeadtime();
        if (i->getFirst()->getEnd() > tmp) {
          i->getFirst()->setEnd(tmp);
        }
      } else
        throw LogicException("Invalid operationplan depedency data");
    }

  // Update flow and loadplans
  update();
}

void OperationPlan::setEnd(Date d, bool force) {
  // Locked opplans don't move
  if (getConfirmed()) {
    if (force) setStartAndEnd(getStart() < d ? getStart() : d, d);
    return;
  }

  if (!lastsubopplan)
    // No sub operationplans
    oper->setOperationPlanParameters(this, quantity, Date::infinitePast, d,
                                     true, true, false);
  else {
    // Move all sub-operationplans in an orderly fashion
    for (auto i = lastsubopplan; i; i = i->prevsubopplan) {
      if (!i->getEnd() || i->getEnd() > d) {
        i->setEnd(d, force);
        d = i->getStart();
      } else
        // There is sufficient slack between the suboperationplans
        break;
    }
  }

  if (force)
    for (auto i : dependencies) {
      if (i->getFirst() == this) {
        auto tmp = getEnd();
        if (i->getOperationDependency())
          tmp += i->getOperationDependency()->getHardSafetyLeadtime();
        if (i->getSecond()->getStart() < tmp) {
          i->getSecond()->setStart(tmp);
        }
      } else if (i->getSecond() == this) {
        auto tmp = getStart();
        if (i->getOperationDependency())
          tmp -= i->getOperationDependency()->getHardSafetyLeadtime();
        if (i->getFirst()->getEnd() > tmp) {
          i->getFirst()->setEnd(tmp);
        }
      } else
        throw LogicException("Invalid operationplan depedency data");
    }

  // Update flow and loadplans
  update();
  // assert(getEnd() <= d);
}

void OperationPlan::resizeFlowLoadPlans() {
  // Update all flowplans
  for (auto flpln = firstflowplan; flpln; flpln = flpln->nextFlowPlan)
    flpln->update();

  // Update all loadplans
  if (getConsumeCapacity())
    for (auto e = beginLoadPlans(); e != endLoadPlans(); ++e) e->update();
  else {
    LoadPlanIterator f = beginLoadPlans();
    firstloadplan = nullptr;  // Important to do this before the delete!
    while (f != endLoadPlans()) delete &*(f++);
  }

  // Allow the operation length to be changed now that the quantity has changed
  // Note that we assume that the end date remains fixed. This assumption makes
  // sense if the operationplan was created to satisfy a demand.
  // It is not valid though when the purpose of the operationplan was to push
  // some material downstream.

  // Notify the demand of the changed delivery
  if (dmd) dmd->setChanged();
}

bool OperationPlan::mergeIfPossible() {
  // Verify a merge with another operationplan.
  // TODO The logic duplicates much of OperationFixedTime::extraInstantiate.
  // Combine as single code. See if we can consolidate this operationplan with
  // an existing one. Merging is possible only when all the following conditions
  // are met:
  //   - it is a subclass of a fixedtime operation
  //   - it doesn't load any resources of type default
  //   - both operationplans are proposed
  //   - both operationplans have no owner
  //     or both have an owner of the same operation and is of type
  //     operation_alternate
  //   - start and end date of both operationplans are exactly the same
  //   - demand of both operationplans are the same
  //   - maximum operation size is not exceeded
  //   - alternate flowplans need to be on the same alternate
  if (!getProposed()) return false;

  if (!oper->hasType<OperationFixedTime, OperationItemDistribution,
                     OperationItemSupplier>())
    return false;

  // Verify we load no resources of type "default".
  // It's ok to merge operationplans which load "infinite" or "buckets"
  // resources.
  for (Operation::loadlist::const_iterator i = oper->getLoads().begin();
       i != oper->getLoads().end(); ++i)
    if (i->getResource()->hasType<ResourceDefault>()) return false;

  // Loop through candidates
  for (OperationPlan::iterator x(oper); x != OperationPlan::end(); ++x) {
    if (x->getStart() > getStart())
      // No candidates will be found in what follows
      return false;
    if (x->getDates() != getDates() || &*x == this) continue;
    if (x->getDemand() != getDemand()) continue;
    if (!x->getProposed()) continue;
    if (x->getQuantity() + getQuantity() >
        oper->getSizeMaximum() + ROUNDING_ERROR)
      continue;
    if (getOwner()) {
      // Both must have the same owner operation of type alternate
      if (!x->getOwner())
        continue;
      else if (getOwner()->getOperation() != x->getOwner()->getOperation())
        continue;
      else if (!getOwner()->getOperation()->hasType<OperationAlternate>())
        continue;
      else if (getOwner()->getDemand() != x->getOwner()->getDemand())
        continue;
    }

    // Check that the flowplans are on identical alternates and not of type
    // fixed
    OperationPlan::FlowPlanIterator fp1 = beginFlowPlans();
    OperationPlan::FlowPlanIterator fp2 = x->beginFlowPlans();
    if (fp1 == endFlowPlans() || fp2 == endFlowPlans())
      // Operationplan without flows are already deleted. Leave them alone.
      continue;
    bool ok = true;
    while (fp1 != endFlowPlans()) {
      if (fp1->getBuffer() != fp2->getBuffer() ||
          fp1->getFlow()->getQuantityFixed() ||
          fp2->getFlow()->getQuantityFixed())
      // No merge possible
      {
        ok = false;
        break;
      }
      ++fp1;
      ++fp2;
    }
    if (!ok) continue;

    // All checks passed, we can merge!
    x->setQuantity(x->getQuantity() + getQuantity());
    if (getOwner()) setOwner(nullptr);
    delete this;
    return true;
  }
  return false;
}

void OperationPlan::scanSetupTimes() {
  for (auto ldplan = beginLoadPlans(); ldplan != endLoadPlans(); ++ldplan) {
    if (!ldplan->isStart() && ldplan->getLoad() &&
        !ldplan->getLoad()->getSetup().empty() &&
        ldplan->getResource()->getSetupMatrix()) {
      // Not a starting loadplan or there is no setup on this loadplan
      ldplan->getResource()->updateSetupTime();
      break;  // Only 1 load can have a setup
    }
  }

  // TODO We can do much faster than the above loop: where we reconsider all
  // loadplans on a resource. We just need to scans the ones around the old date
  // and the ones around the new date. It requires deeper changes to the solver
  // to pass on the information on the old date.
  /*
  // Loop over all loadplans
  for (auto ldplan = beginLoadPlans(); ldplan != endLoadPlans(); ++ldplan)
  {
    if (!ldplan->isStart() || ldplan->getLoad()->getSetup().empty() ||
  !ldplan->getResource()->getSetupMatrix())
      // Not a starting loadplan or there is no setup on this loadplan
      continue;

    // Scan backward for loadplans at the same date
    auto resldplan = ldplan->getResource()->getLoadPlans().begin(&*ldplan);
    --resldplan;
    while (resldplan != ldplan->getResource()->getLoadPlans().end())
    {
      if (resldplan->getDate() != ldplan->getDate())
        break;
      if (resldplan->getEventType() == 1)
      {
        auto tmp = static_cast<LoadPlan*>(&*resldplan);
        if (tmp->isStart() &&
  !static_cast<LoadPlan*>(&*resldplan)->getLoad()->getSetup().empty())
        {
          // The setup time of this operationplan potentially changes
          resldplan->getOperationPlan()->updateSetupTime();
        }
      }
      --resldplan;
    }

    // Scan forward until the first operationplan with a setup.
    resldplan = ldplan->getResource()->getLoadPlans().begin(&*ldplan);
    ++resldplan;
    while (resldplan != ldplan->getResource()->getLoadPlans().end())
    {
      if (resldplan->getEventType() == 1)
      {
        auto tmp = static_cast<LoadPlan*>(&*resldplan);
        if (tmp->isStart() &&
  !static_cast<LoadPlan*>(&*resldplan)->getLoad()->getSetup().empty())
        {
          // The setup time of this operationplan potentially changes
          resldplan->getOperationPlan()->updateSetupTime();
          if (resldplan->getDate() > getEnd())
            break;
        }
      }
      ++resldplan;
    }
  }
  */
}

bool OperationPlan::updateSetupTime() {
  // TODO The setOperationplanParameter methods are a better/more generic/more
  // robust place to put this logic
  Date end_of_setup = getSetupEnd();
  bool changed = false;

  // Keep the setup end date constant during the update
  auto setup = oper->calculateSetup(this, end_of_setup, setupevent);

  if (setupevent && getSetupOverride() >= 0L && !getNoSetup()) {
    auto ldplan = beginLoadPlans();
    if (ldplan == endLoadPlans()) {
      for (auto ld = getOperation()->getLoads().begin();
           ld != getOperation()->getLoads().end(); ++ld)
        if (ld->getResource() && ld->getResource()->getSetupMatrix()) {
          if (!setupevent->getTimeLine() && !getNoSetup()) {
            setupevent->setTimeLine(&(ld->getResource()->getLoadPlans()));
          }
          get<0>(setup) = ld->getResource();
          break;
        }
    } else {
      for (; ldplan != endLoadPlans(); ++ldplan)
        if (ldplan->getResource() && ldplan->getResource()->getSetupMatrix()) {
          if (!setupevent->getTimeLine() && !getNoSetup()) {
            setupevent->setTimeLine(&(ldplan->getResource()->getLoadPlans()));
          }
          get<0>(setup) = ldplan->getResource();
          break;
        }
    }
  }

  if (get<0>(setup) || getSetupOverride() >= 0L) {
    // Setup event required
    if (get<1>(setup) || getSetupOverride() >= 0L) {
      // Apply setup rule duration
      if (getConfirmed()) {
        if (getStart() != end_of_setup || !setupevent) {
          setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup),
                        get<1>(setup));
          setStartAndEnd(end_of_setup, getEnd());
          changed = true;
        } else
          setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup),
                        get<1>(setup));
      } else {
        DateRange tmp = oper->calculateOperationTime(
            this, end_of_setup,
            getSetupOverride() >= 0L ? getSetupOverride()
                                     : get<1>(setup)->getDuration(),
            false);
        if (tmp.getStart() != getStart() || !setupevent) {
          setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup),
                        get<1>(setup));
          setStartAndEnd(tmp.getStart(), getEnd());
          changed = true;
        } else
          setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup),
                        get<1>(setup));
      }
    } else {
      // Zero time event
      if (getStart() != end_of_setup || !setupevent) {
        setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup),
                      get<1>(setup));
        setStartAndEnd(end_of_setup, getEnd());
        changed = true;
      } else
        setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup),
                      get<1>(setup));
    }
  } else {
    // No setup event required
    if (setupevent && getSetupOverride() < 0L) {
      clearSetupEvent();
      changed = true;
    }
    if (end_of_setup != getStart()) {
      setStartAndEnd(end_of_setup, getEnd());
      changed = true;
    }
  }
  return changed;
}

void OperationPlan::update() {
  if (lastsubopplan) {
    // Set the start and end date of the parent.
    Date st = Date::infiniteFuture;
    Date nd = Date::infinitePast;
    for (auto f = firstsubopplan; f; f = f->nextsubopplan) {
      if (f->getStart() < st) st = f->getStart();
      if (f->getEnd() > nd) nd = f->getEnd();
    }
    if (nd) dates.setStartAndEnd(st, nd);
  }

  // Update the flow and loadplans
  resizeFlowLoadPlans();

  // Keep the operationplan list sorted
  updateOperationplanList();

  // Update the setup time on all neighbouring operationplans
  if (!SetupMatrix::empty() && getPropagateSetups()) scanSetupTimes();

  // Notify the owner operationplan
  if (owner) owner->update();

  // Mark as changed
  setChanged();
}

void OperationPlan::deleteOperationPlans(Operation* o,
                                         bool deleteLockedOpplans) {
  if (!o) return;
  for (auto opplan = o->first_opplan; opplan;) {
    OperationPlan* tmp = opplan;

    // Advance to the next operation plan
    opplan = opplan->next;
    if (tmp->getOwner())
      // Deleting a child operationplan will delete the parent.
      // It is possible that also the next operationplan in the list gets
      // deleted by the delete statement that follows.
      while (opplan && tmp->getOwner() == opplan->getOwner())
        opplan = opplan->next;

    // Note that the deletion of the operationplan also updates the opplan list
    bool del = deleteLockedOpplans;
    if (!del && tmp->getProposed()) {
      del = tmp->getOwner() ? tmp->getOwner()->getProposed() : true;
    }
    if (del) delete tmp;
  }
}

double OperationPlan::isExcess(bool use_zero) const {
  // Delivery operationplans or operationplans with dependencies aren't excess
  if (getDemand() || !dependencies.empty()) return 0.0;

  // Recursive call for suboperationplans
  double opplan_excess_qty = getQuantity();
  for (auto subopplan = firstsubopplan; subopplan;
       subopplan = subopplan->nextsubopplan) {
    auto tmp = subopplan->isExcess(use_zero);
    if (tmp < opplan_excess_qty) opplan_excess_qty = tmp;
  }

  // Loop over all producing flowplans
  bool hasFlowplans = false;
  for (auto i = beginFlowPlans(); i != endFlowPlans(); ++i) {
    hasFlowplans = true;
    // Skip consuming flowplans
    if (i->getQuantity() <= 0) continue;

    // Find the total produced quantity, including all suboperationplans
    double flpln_excess_qty = i->getQuantity();
    for (auto subopplan = firstsubopplan; subopplan;
         subopplan = subopplan->nextsubopplan)
      for (auto k = subopplan->beginFlowPlans(); k != subopplan->endFlowPlans();
           ++k)
        if (k->getBuffer() == i->getBuffer())
          flpln_excess_qty += k->getQuantity();
    if (flpln_excess_qty <= 0) continue;

    // Loop over all flowplans in the buffer (starting at the end) and verify
    // that the onhand is bigger than the flowplan quantity
    double current_maximum(0.0);
    double current_minimum(0.0);
    Buffer::flowplanlist::const_iterator j =
        i->getBuffer()->getFlowPlans().rbegin();
    if (!use_zero && j != i->getBuffer()->getFlowPlans().end()) {
      current_maximum = i->getBuffer()->getFlowPlans().getMax(&*j);
      current_minimum = i->getBuffer()->getFlowPlans().getMin(&*j);
    }
    for (; j != i->getBuffer()->getFlowPlans().end(); --j) {
      if (!j->isLastOnDate()) {
        if (&*j == &*i) break;
        continue;
      }
      if (current_maximum > 0.0) {
        auto above_max = j->getOnhand() - current_maximum;
        if (above_max < ROUNDING_ERROR) return 0.0;
        if (above_max < flpln_excess_qty) flpln_excess_qty = above_max;
      } else {
        auto above_min = j->getOnhand() - current_minimum;
        if (above_min < ROUNDING_ERROR) return 0.0;
        if (above_min < flpln_excess_qty) flpln_excess_qty = above_min;
      }
      if (!use_zero) {
        if (j->getEventType() == 4) current_maximum = j->getMax(false);
        if (j->getEventType() == 3) current_minimum = j->getMin(false);
      }
      if (&*j == &*i) break;
    }

    // Convert excess on this flowplan to excess on operationplan
    auto topopplan = i->getOperationPlan();
    if (topopplan->getOwner() &&
        topopplan->getOwner()->getOperation()->hasType<OperationRouting>())
      topopplan = topopplan->getOwner();

    flpln_excess_qty -= i->getFlow()->getQuantityFixed();
    if (flpln_excess_qty < topopplan->getOperation()->getSizeMultiple() *
                                   i->getFlow()->getQuantity() +
                               ROUNDING_ERROR)
      // Not excess or an unavoidable leftover
      return 0.0;
    if (i->getFlow()->getQuantity()) {
      flpln_excess_qty /= i->getFlow()->getQuantity();
      if (flpln_excess_qty < opplan_excess_qty)
        opplan_excess_qty = flpln_excess_qty;
    }
  }

  // Handle operationplan already being deleted by a deleteOperation command
  if (!hasFlowplans && !getOperation()->getFlows().empty()) return 0.0;

  // If we remove/reduce this operationplan the onhand in all buffers remains
  // positive.
  return opplan_excess_qty;
}

Duration OperationPlan::getUnavailable() const {
  Duration x;
  getOperation()->calculateOperationTime(this, dates.getStart(), dates.getEnd(),
                                         &x);
  return dates.getDuration() - x;
}

Object* OperationPlan::finder(const DataValueDict& key) {
  auto val = key.get(Tags::reference);
  if (!val) val = key.get(Tags::id);
  return val ? OperationPlan::findReference(val->getString()) : nullptr;
}

void OperationPlan::setConfirmed(bool b) {
  if (b) {
    flags |= STATUS_CONFIRMED;
    flags &= ~(STATUS_APPROVED + STATUS_COMPLETED + STATUS_CLOSED);
    if (owner && owner->getProposed()) owner->flags |= STATUS_APPROVED;
  } else {
    // Change to proposed
    flags &= ~(STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_CLOSED);
    flags |= STATUS_APPROVED;
  }
  for (auto x = firstsubopplan; x; x = x->nextsubopplan) x->setConfirmed(b);
  update();
  propagateStatus();
}

void OperationPlan::setApproved(bool b) {
  if (b) {
    flags |= STATUS_APPROVED;
    flags &= ~(STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_CLOSED);
    if (owner && owner->getProposed()) owner->flags |= STATUS_APPROVED;
  } else
    // Change to proposed
    flags &= ~(STATUS_APPROVED + STATUS_CONFIRMED + STATUS_COMPLETED +
               STATUS_CLOSED);
  for (auto x = firstsubopplan; x; x = x->nextsubopplan) x->setApproved(b);
  update();
  propagateStatus();
}

void OperationPlan::setProposed(bool b) {
  if (b)
    flags &= ~(STATUS_APPROVED + STATUS_CONFIRMED + STATUS_COMPLETED +
               STATUS_CLOSED);
  else {
    // Change to approved
    flags &= ~(STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_CLOSED);
    flags |= STATUS_APPROVED;
  }
  for (auto x = firstsubopplan; x; x = x->nextsubopplan) x->setProposed(b);
  update();
  propagateStatus();
}

void OperationPlan::setCompleted(bool b) {
  if (b) {
    flags |= STATUS_CONFIRMED + STATUS_COMPLETED;
    flags &= ~(STATUS_APPROVED + STATUS_CLOSED);
    if (owner && owner->getProposed()) owner->flags |= STATUS_APPROVED;
  } else {
    // Change to approved
    flags &= ~(STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_CLOSED);
    flags |= STATUS_APPROVED;
  }
  for (auto x = firstsubopplan; x; x = x->nextsubopplan) x->setClosed(b);
  update();
  propagateStatus();
}

void OperationPlan::setClosed(bool b) {
  if (b) {
    flags |= STATUS_CONFIRMED + STATUS_CLOSED;
    flags &= ~(STATUS_APPROVED + STATUS_COMPLETED);
  } else {
    // Change to approved
    flags &= ~(STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_CLOSED);
    flags |= STATUS_APPROVED;
  }
  for (auto x = firstsubopplan; x; x = x->nextsubopplan) x->setClosed(b);
  update();
  propagateStatus();
}

void OperationPlan::propagateStatus(bool log) {
  if (getOperation()->hasType<OperationInventory>()) return;

  // Assure that all child operationplans also get the same status
  auto mystatus = getStatus();
  for (auto subopplan = firstsubopplan; subopplan;
       subopplan = subopplan->nextsubopplan)
    if (subopplan->getStatus() != mystatus) {
      subopplan->setStatus(mystatus);
      subopplan->appendInfo("Status propagated from parent");
      subopplan->propagateStatus(log);
    }

  if (getSource().rfind("odoo", 0) == 0 ||
      (mystatus != "completed" && mystatus != "closed"))
    return;

  bool firstlog = true;

  // Assure the start and end date are in the past
  if (!Plan::instance().getCompletedAllowFuture() &&
      getEnd() > Plan::instance().getCurrent()) {
    if (log) {
      if (firstlog) {
        firstlog = false;
        logger << "Propagating " << this << endl;
      }
      logger << "    Adjusting end date to " << Plan::instance().getCurrent()
             << endl;
    }
    setEnd(Plan::instance().getCurrent(), true);
  }

  if (getOwner() && getOwner()->getOperation()->hasType<OperationRouting>()) {
    // Assure that previous routing steps are also marked closed or completed
    for (auto prev = prevsubopplan; prev; prev = prev->prevsubopplan)
      if (prev->getStatus() != mystatus) {
        if (log) {
          if (firstlog) {
            firstlog = false;
            logger << "Propagating " << this << endl;
          }
          logger << "    Changing status of previous routing step " << prev
                 << endl;
        }
        prev->appendInfo("Status propagated from following step");
        prev->setStatus(mystatus);
      }
    // Assure that the parent routing gets at least the status approved
    bool all_steps_completed = true;
    bool all_steps_closed = true;
    for (auto subopplan = getOwner()->firstsubopplan; subopplan;
         subopplan = subopplan->nextsubopplan) {
      if (!subopplan->getCompleted()) all_steps_completed = false;
      if (!subopplan->getClosed()) all_steps_closed = false;
    }
    if (all_steps_closed && !getOwner()->getClosed()) {
      getOwner()->appendInfo(
          "Status changed to closed because all steps are closed");
      getOwner()->flags |= STATUS_CONFIRMED + STATUS_CLOSED;
      getOwner()->flags &= ~(STATUS_APPROVED + STATUS_COMPLETED);
      if (log) {
        if (firstlog) {
          firstlog = false;
          logger << "Propagating " << this << endl;
        }
        logger << "    Marking routing as closed " << getOwner() << endl;
      }
    } else if (all_steps_completed && !getOwner()->getCompleted()) {
      getOwner()->appendInfo(
          "Status changed to completed because all steps are completed");
      getOwner()->flags |= STATUS_CONFIRMED + STATUS_COMPLETED;
      getOwner()->flags &= ~(STATUS_APPROVED + STATUS_CLOSED);
      if (log) {
        if (firstlog) {
          firstlog = false;
          logger << "Propagating " << this << endl;
        }
        logger << "    Marking routing as completed " << getOwner() << endl;
      }
    } else if (getOwner()->getProposed()) {
      for (auto subopplan = getOwner()->firstsubopplan; subopplan;
           subopplan = subopplan->nextsubopplan)
        if (subopplan->getProposed()) {
          subopplan->appendInfo("Setting status to approved");
          subopplan->setApproved(true);
        }
      getOwner()->appendInfo("Setting status to approved");
      getOwner()->flags |= STATUS_APPROVED;
      getOwner()->flags &=
          ~(STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_CLOSED);
      if (log) {
        if (firstlog) {
          firstlog = false;
          logger << "Propagating " << this << endl;
        }
        logger << "    Marking routing as approved " << getOwner() << endl;
      }
    }
  }

  // Check that upstream buffers have enough supply in the closed or completed
  // status
  for (auto myflpln = beginFlowPlans(); myflpln != endFlowPlans(); ++myflpln) {
    if (myflpln->getQuantity() >= 0 ||
        myflpln->getBuffer()->hasType<BufferInfinite>())
      continue;

    // Get current status
    double closed_balance = 0.0;
    flowplanlist& tmline = myflpln->getBuffer()->getFlowPlans();
    for (auto flpln = tmline.begin(); flpln != tmline.end(); ++flpln)
      if (flpln->getOperationPlan() &&
          (flpln->getOperationPlan()->getClosed() ||
           flpln->getOperationPlan()->getCompleted()) &&
          flpln->getDate() <= myflpln->getDate())
        closed_balance += flpln->getQuantity();

    if (closed_balance < -ROUNDING_ERROR) {
      // Things don't add up here.
      // We'll close some upstream supply to make things match up
      if (log) {
        if (firstlog) {
          firstlog = false;
          logger << "Propagating " << this << endl;
        }
        logger << "    Available material balance on " << myflpln->getBuffer()
               << " short of " << closed_balance << " on " << myflpln->getDate()
               << endl;
      }
      // 1) Correct the date of existing completed supply
      for (auto flpln = tmline.begin(); flpln != tmline.end(); ++flpln)
        if (flpln->getQuantity() > 0.0 && flpln->getOperationPlan() &&
            (flpln->getOperationPlan()->getClosed() ||
             flpln->getOperationPlan()->getCompleted()) &&
            flpln->getDate() > myflpln->getDate()) {
          if (log) {
            if (firstlog) {
              firstlog = false;
              logger << "Propagating " << this << endl;
            }
            logger << "      Adjusting end date of "
                   << flpln->getOperationPlan() << endl;
          }
          flpln->getOperationPlan()->setStartAndEnd(
              flpln->getOperationPlan()->getStart() < myflpln->getDate()
                  ? flpln->getOperationPlan()->getStart()
                  : myflpln->getDate(),
              myflpln->getDate());
          flpln->getOperationPlan()->appendInfo(
              "Changed end date to keep the inventory positive");
          closed_balance += flpln->getQuantity();
          if (closed_balance >= -ROUNDING_ERROR) break;
        }
      if (closed_balance < -ROUNDING_ERROR) {
        // 2) try changing the status of confirmed supply
        for (auto flpln = tmline.begin(); flpln != tmline.end(); ++flpln)
          if (flpln->getQuantity() > 0.0 && flpln->getOperationPlan() &&
              flpln->getOperationPlan()->getConfirmed() &&
              !flpln->getOperationPlan()->getClosed() &&
              !flpln->getOperationPlan()->getCompleted()) {
            if (log) {
              if (firstlog) {
                firstlog = false;
                logger << "Propagating " << this << endl;
              }
              logger << "      Changing status of " << flpln->getOperationPlan()
                     << endl;
            }
            flpln->getOperationPlan()->setStatus(mystatus);
            flpln->getOperationPlan()->appendInfo(
                "Changed status to keep the inventory positive");
            closed_balance += flpln->getQuantity();
            if (closed_balance >= -ROUNDING_ERROR) break;
          }
        if (closed_balance < -ROUNDING_ERROR) {
          // 3) try changing the status of approved supply
          for (auto flpln = tmline.begin(); flpln != tmline.end(); ++flpln)
            if (flpln->getQuantity() > 0.0 && flpln->getOperationPlan() &&
                flpln->getOperationPlan()->getApproved()) {
              if (log) {
                if (firstlog) {
                  firstlog = false;
                  logger << "Propagating " << this << endl;
                }
                logger << "      Changing status of "
                       << flpln->getOperationPlan() << endl;
              }
              flpln->getOperationPlan()->appendInfo(
                  "Changed status to keep the inventory positive");
              flpln->getOperationPlan()->setStatus(mystatus);
              closed_balance += flpln->getQuantity();
              if (closed_balance >= -ROUNDING_ERROR) break;
            }
          if (closed_balance < -ROUNDING_ERROR) {
            // 4) Try changing the status of proposed supply
            for (auto flpln = tmline.begin(); flpln != tmline.end(); ++flpln)
              if (flpln->getQuantity() > 0.0 && flpln->getOperationPlan() &&
                  flpln->getOperationPlan()->getProposed()) {
                if (log) {
                  if (firstlog) {
                    firstlog = false;
                    logger << "Propagating " << this << endl;
                  }
                  logger << "      Changing status of "
                         << flpln->getOperationPlan() << endl;
                }
                flpln->getOperationPlan()->appendInfo(
                    "Changed status to keep the inventory positive");
                flpln->getOperationPlan()->setStatus(mystatus);
                closed_balance += flpln->getQuantity();
                if (closed_balance >= -ROUNDING_ERROR) break;
              }
            // 5) Finally, update the initial inventory
            if (closed_balance < -ROUNDING_ERROR) {
              if (log) {
                if (firstlog) {
                  firstlog = false;
                  logger << "Propagating " << this << endl;
                }
                logger << "      Incrementing initial inventory with "
                       << -closed_balance << endl;
              }
              myflpln->getBuffer()->setOnHand(
                  myflpln->getBuffer()->getOnHand() - closed_balance);
            }
          }
        }
      }
    }
  }
}

string OperationPlan::getStatus() const {
  if (flags & STATUS_APPROVED)
    return "approved";
  else if (flags & STATUS_COMPLETED)
    return "completed";
  else if (flags & STATUS_CLOSED)
    return "closed";
  else if (flags & STATUS_CONFIRMED)
    return "confirmed";
  else
    return "proposed";
}

bool OperationPlan::isConstrained() const {
  for (PeggingIterator p(this); p; ++p) {
    const OperationPlan* m = p.getOperationPlan();
    Demand* dmd = m ? m->getTopOwner()->getDemand() : nullptr;
    if (dmd && dmd->getDue() < m->getEnd()) return true;
  }
  return false;
}

void OperationPlan::setStatus(const string& s, bool propagate, bool u) {
  if (s == "approved") {
    flags |= STATUS_APPROVED;
    flags &= ~(STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_CLOSED);
  } else if (s == "confirmed") {
    flags |= STATUS_CONFIRMED;
    flags &= ~(STATUS_APPROVED + STATUS_COMPLETED + STATUS_CLOSED);
  } else if (s == "proposed")
    flags &= ~(STATUS_APPROVED + STATUS_CONFIRMED + STATUS_COMPLETED +
               STATUS_CLOSED);
  else if (s == "completed") {
    flags &= ~(STATUS_APPROVED + STATUS_CLOSED);
    flags |= STATUS_CONFIRMED + STATUS_COMPLETED;
  } else if (s == "closed") {
    flags &= ~(STATUS_APPROVED + STATUS_COMPLETED);
    flags |= STATUS_CONFIRMED + STATUS_CLOSED;
  } else
    throw DataException("invalid operationplan status:" + s);
  if (!getProposed() && owner && owner->getProposed())
    owner->flags |= STATUS_APPROVED;
  if (u) {
    update();
    for (auto x = firstsubopplan; x; x = x->nextsubopplan)
      x->setStatus(s, propagate, u);
    if (propagate) propagateStatus();
  }
}

void OperationPlan::freezeStatus(Date st, Date nd, double q) {
  if (getProposed()) return;
  dates = DateRange(st, nd);
  quantity = q > 0 ? q : 0.0;
}

void OperationPlan::setDemand(Demand* l) {
  // No change
  if (l == dmd) return;

  // Unregister from previous demand
  if (dmd) dmd->removeDelivery(this);

  // Register at the new demand and mark it changed
  dmd = l;
  if (l) {
    l->addDelivery(this);
    l->setChanged();
  }
}

PyObject* OperationPlan::create(PyTypeObject* pytype, PyObject* args,
                                PyObject* kwds) {
  try {
    // Find or create the C++ object
    PythonDataValueDict atts(kwds);
    Object* x = createOperationPlan(OperationPlan::metadata, atts);
    if (!x) {
      Py_INCREF(Py_None);
      return Py_None;
    }
    Py_INCREF(x);

    // Iterate over extra keywords, and set attributes.   @todo move this
    // responsibility to the readers...
    if (x) {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value)) {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::operation) && !attr.isA(Tags::id) &&
            !attr.isA(Tags::reference) && !attr.isA(Tags::action) &&
            !attr.isA(Tags::type) && !attr.isA(Tags::start) &&
            !attr.isA(Tags::end) && !attr.isA(Tags::quantity) &&
            !attr.isA(Tags::create) && !attr.isA(Tags::batch) &&
            !attr.isA(Tags::status) && !attr.isA(Tags::statusNoPropagation) &&
            !attr.isA(Tags::location) && !attr.isA(Tags::item) &&
            !attr.isA(Tags::ordertype) && !attr.isA(Tags::origin) &&
            !attr.isA(Tags::batch) && !attr.isA(Tags::supplier) &&
            !attr.isA(Tags::resources)) {
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

double OperationPlan::getPriority() const {
  // Operationplan hasn't been set up yet
  if (!oper) return 999.0;

  // Child operationplans have the same priority as the parent
  if (getOwner() && !getOwner()->getOperation()->hasType<OperationSplit>())
    return getOwner()->getPriority();

  // Handle demand delivery operationplans
  if (getTopOwner()->getDemand())
    return getTopOwner()->getDemand()->getPriority();

  // Handle an upstream operationplan
  double lowestPriority = 999.0;
  for (PeggingIterator p(const_cast<OperationPlan*>(this)); p; ++p) {
    const OperationPlan* m = p.getOperationPlan();
    if (!m) continue;
    auto dmd = m->getTopOwner()->getDemand();
    if (dmd && dmd->getPriority() < lowestPriority)
      lowestPriority = dmd->getPriority();
  }
  return lowestPriority;
}

int OperationPlan::getCriticality() const {
  // Operationplan hasn't been set up yet
  if (!oper) return 86313600L;  // 999 days in seconds;

  // Child operationplans have the same criticality as the parent
  // TODO: Slack between routing sub operationplans isn't recognized.
  if (getOwner() && !getOwner()->getOperation()->hasType<OperationSplit>())
    return getOwner()->getCriticality();

  // Handle demand delivery operationplans
  if (getTopOwner()->getDemand()) {
    long early = getTopOwner()->getDemand()->getDue() - getEnd();
    return ((early <= 0L) ? 0.0 : early) / 86400.0;  // Convert to days
  }

  // Handle an upstream operationplan
  Duration minslack = 86313600L;  // 999 days in seconds
  vector<Duration> gaps(HasLevel::getNumberOfLevels() + 5);
  set<const OperationPlan*> opplans;
  for (PeggingIterator p(const_cast<OperationPlan*>(this)); p; ++p) {
    const OperationPlan* m = p.getOperationPlan();
    if (opplans.find(m) != opplans.end())
      continue;
    else
      opplans.insert(m);
    vector<Duration>::size_type lvl = p.getLevel();
    if (lvl >= gaps.size()) gaps.resize(lvl + 5);
    gaps[lvl] = p.getGap();
    if (m && m->getTopOwner()->getDemand()) {
      // Reached a demand. Get the total slack now.
      Duration myslack = m->getTopOwner()->getDemand()->getDue() - m->getEnd();
      if (myslack < 0L) myslack = 0L;
      for (unsigned int i = 1; i <= lvl; i++) myslack += gaps[i];
      if (myslack < minslack) minslack = myslack;
    }
  }
  return floor(minslack / 86400.0);  // Convert to days
}

Duration OperationPlan::getDelay() const {
  // Operationplan hasn't been set up yet. On time by default.
  if (!oper) return 0L;

  // Child operationplans have the same delay as the parent
  // TODO for routing steps this is not really as accurrate as we could do it
  if (getOwner() && !getOwner()->getOperation()->hasType<OperationSplit>())
    return getOwner()->getDelay();

  // Handle demand delivery operationplans
  if (getTopOwner()->getDemand())
    return getEnd() - getTopOwner()->getDemand()->getDue();

  // Handle an upstream operationplan
  Duration maxdelay = Duration::MIN;
  vector<Duration> gaps(HasLevel::getNumberOfLevels() + 5);
  set<const OperationPlan*> opplans;
  for (PeggingIterator p(const_cast<OperationPlan*>(this)); p; ++p) {
    const OperationPlan* m = p.getOperationPlan();
    if (opplans.find(m) != opplans.end())
      continue;
    else
      opplans.insert(m);
    vector<Duration>::size_type lvl = p.getLevel();
    if (lvl >= gaps.size()) gaps.resize(lvl + 5);
    gaps[lvl] = p.getGap();
    if (m && m->getTopOwner()->getDemand()) {
      // Reached a demand. All time is processing except the gaps
      Duration mydelay = m->getEnd() - m->getTopOwner()->getDemand()->getDue();
      for (unsigned int i = 1; i <= lvl; i++) mydelay -= gaps[i];
      if (mydelay > maxdelay) maxdelay = mydelay;
    }
  }
  return maxdelay;
}

void OperationPlan::setQuantityExternal(double f) {
  if (fabs(f - quantity) < ROUNDING_ERROR) return;
  auto q = setQuantity(f, false, true, true);
  if (oper)
    oper->setOperationPlanParameters(this, q, getStart(), Date::infinitePast,
                                     true, true, true);
}

void OperationPlan::setQuantityCompleted(double q) {
  if (fabs(q - quantity_completed) < ROUNDING_ERROR) return;
  quantity_completed = q;
  if (oper && !getProposed())
    oper->setOperationPlanParameters(this, getQuantity(), getStart(),
                                     Date::infinitePast, true, true, true);
}

void OperationPlan::updatePurchaseOrder(Item* newitem, Location* newlocation,
                                        Supplier* newsupplier) {
  if (!newitem) throw DataException("Purchase order item can't be empty");
  if (!newlocation)
    throw DataException("Purchase order location can't be empty");

  // Find or create the destination buffer.
  Buffer* destbuffer = nullptr;
  Item::bufferIterator buf_iter(newitem);
  while (Buffer* tmpbuf = buf_iter.next()) {
    if (tmpbuf->getLocation() == newlocation && !tmpbuf->getBatch()) {
      destbuffer = tmpbuf;
      break;
    }
  }
  if (!destbuffer) destbuffer = Buffer::findOrCreate(newitem, newlocation);

  // Look for a matching operation replenishing this buffer.
  Operation* newoper = nullptr;
  destbuffer->getProducingOperation();
  for (auto flowiter = destbuffer->getFlows().begin();
       flowiter != destbuffer->getFlows().end(); ++flowiter) {
    if (!flowiter->getOperation()->hasType<OperationItemSupplier>()) continue;
    OperationItemSupplier* opitemsupplier =
        static_cast<OperationItemSupplier*>(flowiter->getOperation());
    if (newsupplier) {
      if (newsupplier->isMemberOf(
              opitemsupplier->getItemSupplier()->getSupplier()))
        newoper = opitemsupplier;
    } else
      newoper = opitemsupplier;
  }

  // No matching operation is found.
  if (!newoper && getSupplier()) {
    ItemSupplier* itemsupplier = new ItemSupplier();
    itemsupplier->setSupplier(newsupplier);
    itemsupplier->setItem(newitem);
    itemsupplier->setLocation(newlocation);
    itemsupplier->setHidden(true);
    itemsupplier->setPriority(0);
    newoper = new OperationItemSupplier(itemsupplier, destbuffer);
  }

  // Switch the operation, keeping the receipt date the same
  if (newoper && newoper != oper) {
    oper = newoper;
    oper->setOperationPlanParameters(this, quantity, Date::infinitePast,
                                     dates.getEnd(), false, true, false);
  }
}

void OperationPlan::updateDistributionOrder(Item* newitem, Location* neworigin,
                                            Location* newlocation) {
  if (!newlocation)
    throw DataException("Distribution order location can't be empty");

  // Find or create the destination buffer.
  Buffer* destbuffer = nullptr;
  Item::bufferIterator buf_iter(newitem);
  while (Buffer* tmpbuf = buf_iter.next()) {
    if (tmpbuf->getLocation() == newlocation && !tmpbuf->getBatch()) {
      destbuffer = tmpbuf;
      break;
    }
  }
  if (!destbuffer) destbuffer = Buffer::findOrCreate(newitem, newlocation);

  // Look for a matching operation replenishing this buffer.
  Operation* newoper = nullptr;
  destbuffer->getProducingOperation();
  for (auto flowiter = destbuffer->getFlows().begin();
       flowiter != destbuffer->getFlows().end(); ++flowiter) {
    if (!flowiter->getOperation()->hasType<OperationItemDistribution>() ||
        flowiter->getQuantity() <= 0)
      continue;
    OperationItemDistribution* opitemdist =
        static_cast<OperationItemDistribution*>(flowiter->getOperation());
    // Origin must match as well
    if (neworigin) {
      for (auto fl = opitemdist->getFlows().begin();
           fl != opitemdist->getFlows().end(); ++fl) {
        if (fl->getQuantity() < 0 &&
            fl->getBuffer()->getLocation()->isMemberOf(neworigin) &&
            !fl->getBuffer()->getBatch())
          newoper = opitemdist;
      }
    } else if (!opitemdist->getOrigin())
      newoper = opitemdist;
  }

  // Create a new operation
  if (!newoper) {
    Buffer* originbuffer = nullptr;
    if (neworigin) {
      auto bufiter = newitem->getBufferIterator();
      while (Buffer* tmpbuf = bufiter.next()) {
        if (tmpbuf->getLocation() == neworigin && !tmpbuf->getBatch()) {
          originbuffer = tmpbuf;
        }
      }
      if (!originbuffer)
        originbuffer = Buffer::findOrCreate(newitem, neworigin);
    }

    // Create itemdistribution
    auto itemdist = new ItemDistribution();
    if (neworigin) itemdist->setOrigin(neworigin);
    itemdist->setItem(newitem);
    if (newlocation) itemdist->setDestination(newlocation);
    itemdist->setPriority(0);

    // Create operation
    newoper = new OperationItemDistribution(itemdist, originbuffer, destbuffer);
  }

  // Switch the operation, keeping the receipt date the same
  if (newoper && newoper != oper) {
    oper = newoper;
    oper->setOperationPlanParameters(this, quantity, Date::infinitePast,
                                     getEnd(), true, true, false);
  }
}

void OperationPlan::setItem(Item* newitem) {
  if (oper && oper->hasType<OperationItemSupplier>()) {
    if (getItem() != newitem)
      updatePurchaseOrder(newitem, getLocation(), getSupplier());
  } else if (oper && oper->hasType<OperationItemDistribution>()) {
    if (getItem() != newitem)
      updateDistributionOrder(newitem, getOrigin(), getLocation());
  } else
    // Dummy update during input parsing
    itm = newitem;
}

void OperationPlan::setOrigin(Location* neworigin) {
  if (oper && oper->hasType<OperationItemDistribution>()) {
    if (getOrigin() != neworigin)
      updateDistributionOrder(getItem(), neworigin, getLocation());
  } else
    // Dummy update during input parsing
    ori = neworigin;
}

void OperationPlan::setLocation(Location* newlocation) {
  if (oper && oper->hasType<OperationItemSupplier>()) {
    if (getLocation() != newlocation)
      updatePurchaseOrder(getItem(), newlocation, getSupplier());
  } else if (oper && oper->hasType<OperationItemDistribution>()) {
    if (getLocation() != newlocation)
      updateDistributionOrder(getItem(), getOrigin(), newlocation);
  } else
    // Dummy update during input parsing
    loc = newlocation;
}

void OperationPlan::setSupplier(Supplier* newsupplier) {
  if (oper && oper->hasType<OperationItemSupplier>()) {
    if (getSupplier() != newsupplier)
      updatePurchaseOrder(getItem(), getLocation(), newsupplier);
  } else
    // Dummy update during input parsing
    sup = newsupplier;
}

void OperationPlan::clear() {
  for (auto& o : Operation::all()) o.deleteOperationPlans();
}

PyObject* OperationPlan::createIterator(PyObject* self, PyObject* args) {
  // Check arguments
  PyObject* pyoper = nullptr;
  if (!PyArg_ParseTuple(args, "|O:operationplans", &pyoper)) return nullptr;
  if (!pyoper)
    // First case: Iterate over all operationplans
    return new PythonIterator<OperationPlan::iterator, OperationPlan>();

  // Second case: Iterate over the operationplans of a single operation
  PythonData oper(pyoper);
  if (!oper.check(Operation::metadata)) {
    PyErr_SetString(PythonDataException,
                    "optional argument must be of type operation");
    return nullptr;
  }
  return new PythonIterator<OperationPlan::iterator, OperationPlan>(
      static_cast<Operation*>(pyoper));
}

PeggingIterator OperationPlan::getPeggingDownstream() const {
  return PeggingIterator(this, true);
}

PeggingIterator OperationPlan::getPeggingDownstreamFirstLevel() const {
  return PeggingIterator(this, true, 1);
}

PeggingIterator OperationPlan::getPeggingUpstream() const {
  return PeggingIterator(this, false);
}

PeggingIterator OperationPlan::getPeggingUpstreamFirstLevel() const {
  return PeggingIterator(this, false, 1);
}

PeggingDemandIterator OperationPlan::getPeggingDemand() const {
  return PeggingDemandIterator(this);
}

int OperationPlan::InterruptionIterator::intitialize() {
  // Initialize the metadata.
  metacategory =
      MetaCategory::registerCategory<OperationPlan::InterruptionIterator>(
          "interruption", "interruptions");
  metadata = MetaClass::registerClass<OperationPlan::InterruptionIterator>(
      "interruption", "operationplan interruption", true);
  registerFields<OperationPlan::InterruptionIterator>(
      const_cast<MetaCategory*>(metacategory));

  // Initialize the Python type
  auto& x =
      PythonExtension<OperationPlan::InterruptionIterator>::getPythonType();
  x.setName("interruption");
  x.setDoc("frePPLe operationplan interruption");
  x.supportgetattro();
  x.supportstr();
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  metadata->setPythonClass(x);
  return x.typeReady();
}

OperationPlan::AlternateIterator::AlternateIterator(const OperationPlan* o)
    : opplan(o) {
  if (!o) return;
  if (o->getOwner() &&
      o->getOwner()->getOperation()->hasType<OperationAlternate>()) {
    auto subs = o->getOwner()->getOperation()->getSubOperationIterator();
    while (SubOperation* sub = subs.next()) {
      if (sub->getOperation() != o->getOperation())
        opers.push_back(sub->getOperation());
    }
  }
  operIter = opers.begin();
}

Operation* OperationPlan::AlternateIterator::next() {
  if (operIter == opers.end()) return nullptr;
  auto tmp = *operIter;
  ++operIter;
  return tmp;
}

OperationPlan::InterruptionIterator*
OperationPlan::InterruptionIterator::next() {
  while (true) {
    // Check whether all calendars are available
    bool available = true;
    Date selected = Date::infiniteFuture;
    for (unsigned short t = 0; t < numCalendars; ++t) {
      if (cals[t].getDate() < selected) selected = cals[t].getDate();
    }
    curdate = selected;
    for (unsigned short t = 0; t < numCalendars && available; ++t)
      // TODO next line does a pretty expensive lookup in the calendar, which we
      // might be available to avoid
      available = (cals[t].getCalendar()->getValue(selected) != 0);

    if (available && !status) {
      // Becoming available after unavailable period
      status = true;
      end = (curdate > opplan->getEnd()) ? opplan->getEnd() : curdate;
      if (start != end) return this;
    } else if (!available && status) {
      // Becoming unavailable after available period
      status = false;
      if (curdate >= opplan->getEnd())
        // Leaving the desired date range
        return nullptr;
      start = curdate;
    } else if (curdate >= opplan->getEnd())
      return nullptr;

    // Advance to the next event
    for (unsigned short t = 0; t < numCalendars; ++t)
      if (cals[t].getDate() == selected) ++cals[t];
  }
}

double OperationPlan::getEfficiency(Date d) const {
  double best = DBL_MAX;
  LoadPlanIterator e = beginLoadPlans();
  if (e == endLoadPlans()) {
    // Use the operation loads
    for (auto h = getOperation()->getLoads().begin();
         h != getOperation()->getLoads().end(); ++h) {
      double best_eff = 0.0;
      for (Resource::memberRecursiveIterator mmbr(h->getResource());
           !mmbr.empty(); ++mmbr) {
        if (!mmbr->isGroup() &&
            (!h->getSkill() || mmbr->hasSkill(h->getSkill(), d))) {
          auto my_eff =
              mmbr->getEfficiencyCalendar()
                  ? mmbr->getEfficiencyCalendar()->getValue(d ? d : getStart())
                  : mmbr->getEfficiency();
          if (my_eff > best_eff) best_eff = my_eff;
        }
      }
      if (best_eff < best) best = best_eff;
    }
  } else {
    // Use the operationplan loadplans
    double parallel_factor = 0.0;
    auto individual = Plan::instance().getIndividualPoolResources();
    while (e != endLoadPlans()) {
      if (e->getQuantity() <= 0) {
        if (e->getResource()->getOwner() && individual) {
          // Planning with individual resources from a pool.
          // Efficiency depends on sum of all efficiencies.
          // Eg Allocating 1 resource with 100% efficiencies is the same
          // as allocating 2 resource each with 50% efficiency.
          auto total_allocated = 0.0;
          for (LoadPlanIterator inner = beginLoadPlans();
               inner != endLoadPlans(); ++inner)
            if (e->getResource()->getTop() == inner->getResource()->getTop() &&
                inner->getQuantity() < 0) {
              total_allocated +=
                  inner->getResource()->getEfficiencyCalendar()
                      ? inner->getResource()->getEfficiencyCalendar()->getValue(
                            d ? d : getStart())
                      : inner->getResource()->getEfficiency();
            }
          double load_quantity = 1.0;
          for (auto h = getOperation()->getLoads().begin();
               h != getOperation()->getLoads().end(); ++h) {
            if (e->getResource()->isMemberOf(h->getResource())) {
              load_quantity = h->getQuantity();
              break;
            }
          }
          total_allocated /= load_quantity;
          if (!parallel_factor || total_allocated < parallel_factor)
            parallel_factor = total_allocated;
        } else {
          auto tmp = e->getResource()->getEfficiencyCalendar()
                         ? e->getResource()->getEfficiencyCalendar()->getValue(
                               d ? d : getStart())
                         : e->getResource()->getEfficiency();
          if (tmp < best) best = tmp;
        }
      }
      ++e;
    }
    if (parallel_factor) {
      if (best == DBL_MAX)
        best = parallel_factor;
      else
        best *= parallel_factor / 100;
    }
  }
  if (best == DBL_MAX)
    return 1.0;
  else if (best > 0.0)
    return best / 100.0;
  else
    return 0.0;
}

void OperationPlan::setBatch(const PooledString& s, bool up) {
  if (getTopOwner() != this && up)
    getTopOwner()->setBatch(s, false);
  else {
    auto subopplans = getSubOperationPlans();
    while (auto subopplan = subopplans.next()) subopplan->setBatch(s, false);
    if (batch != s) {
      batch = s;
      auto flplniter = getFlowPlans();
      FlowPlan* flpln;
      while ((flpln = flplniter.next())) flpln->updateBatch();
    }
  }
}

Date OperationPlan::computeOperationToFlowDate(Date d) const {
  for (auto g = beginFlowPlans(); g != endFlowPlans(); ++g)
    if (g->getFlow()->isProducer() &&
        !g->getFlow()->hasType<FlowTransferBatch>())
      return g->getFlow()->getOffset()
                 ? g->getFlow()->computeOperationToFlowDate(this, d)
                 : d;
  return d;
}

Duration OperationPlan::getSetup() const {
  if (!setupevent) return Duration(-1L);
  if (setupevent->getSetupOverride() >= Duration(0L))
    return setupevent->getSetupOverride();
  if (getConfirmed()) return Duration(0L);
  if (getSetupRule()) return getSetupRule()->getDuration();
  for (auto ldplan = beginLoadPlans(); ldplan != endLoadPlans(); ++ldplan) {
    if (!ldplan->getLoad()->getSetup().empty() &&
        ldplan->getResource()->getSetupMatrix())
      return Duration(0L);
  }
  return Duration(-1L);
}

void OperationPlan::setSetupEvent(TimeLine<LoadPlan>* res, Date d,
                                  const PooledString& s, SetupMatrixRule* r) {
  if (setupevent && setupevent->getRule() &&
      setupevent->getRule()->getResource()) {
    for (auto l = beginLoadPlans(); l != endLoadPlans();) {
      if (l->getLoad())
        ++l;
      else
        l.deleteLoadPlan();
    }
  }
  if (!res && (!setupevent || setupevent->getSetupOverride() < 0L)) {
    delete setupevent;
    setupevent = nullptr;
    return;
  } else if (setupevent)
    setupevent->update(res, d, s, r);
  else
    setupevent = new SetupEvent(res, d, s, r, this);
  if (r && r->getResource()) new LoadPlan(this, setupevent);
}

double OperationPlan::getSetupCost() const {
  if (setupevent)
    return setupevent->getRule() ? setupevent->getRule()->getCost() : 0.0;
  else
    return 0.0;
}

PyObject* OperationPlan::getColorPython(PyObject* self, PyObject* args) {
  OperationPlan* opplan = static_cast<OperationPlan*>(self);
  // No color for delivery, stock or alternate operationplans
  if (opplan->getOrderType() == "DLVR")
    return Py_BuildValue("(dO)", 999999.0, Py_None);
  if (opplan->getOrderType() == "STCK")
    return Py_BuildValue("(dO)", 999999.0, Py_None);
  if (opplan->getOrderType() == "ALT")
    return Py_BuildValue("(dO)", 999999.0, Py_None);

  if (opplan->getConfirmed() || opplan->getApproved())
    return Py_BuildValue("(dO)", 100.0 - opplan->getDelay() / 86400, Py_None);

  // Routing suboperations are getting a color
  // if the routing is the first proposed to produce
  bool isRoutingSubop = false, isFirstRoutingMO = true;
  if (opplan->getStatus() == "proposed" &&
      opplan->getOperation()->getOwner() and
      opplan->getOperation()->getOwner()->hasType<OperationRouting>()) {
    isRoutingSubop = true;
    Date end = opplan->getOwner()->getEnd();
    for (auto rr = opplan->getOperation()->getOwner()->getOperationPlans();
         rr != OperationPlan::end(); ++rr) {
      if ((&*rr)->getStatus() != "proposed") continue;
      if ((&*rr) != opplan->getOwner() && rr->getEnd() < end) {
        isFirstRoutingMO = false;
        break;
      }
    }
  }

  // This is a routing suboperation and the owner is the first MO of the plan
  if (isRoutingSubop && isFirstRoutingMO) {
    // Find the last step
    OperationPlan* lastStepOpPlan = nullptr;
    for (auto rr = opplan->getOwner()->getSubOperationPlans();
         rr != OperationPlan::end(); ++rr) {
      lastStepOpPlan = (&*rr);
    }
    return Py_BuildValue("(dO)", 100.0 - lastStepOpPlan->getDelay() / 86400,
                         Py_None);
  }

  // This is routing suboperation and the owner is NOT the first MO of the
  // plan
  if (isRoutingSubop && !isFirstRoutingMO) {
    /*color less*/
    return Py_BuildValue("(dO)", 999999.0, Py_None);
  }

  // This is a routing MO, make sure it's the first one to produce
  isFirstRoutingMO = true;
  if (opplan->getStatus() == "proposed" &&
      opplan->getOperation()->hasType<OperationRouting>()) {
    for (auto rr = opplan->getOperation()->getOperationPlans();
         rr != OperationPlan::end(); ++rr) {
      if ((&*rr)->getStatus() != "proposed") continue;
      if ((&*rr) != opplan && rr->getEnd() < opplan->getEnd()) {
        isFirstRoutingMO = false;
        break;
      }
    }

    if (isFirstRoutingMO) {
      OperationPlan* lastStepOpPlan = nullptr;
      for (auto rr = opplan->getSubOperationPlans(); rr != OperationPlan::end();
           ++rr) {
        lastStepOpPlan = (&*rr);
      }
      if (lastStepOpPlan)
        return Py_BuildValue("(dO)", 100.0 - lastStepOpPlan->getDelay() / 86400,
                             Py_None);
      else
        return Py_BuildValue("(dO)", 999999.0, Py_None);
    } else
      return Py_BuildValue("(dO)", 999999.0, Py_None);
  }

  // Remaining possibilities now, POs, DOs and regular timer_per, fixed_time
  // MOs, no subops
  Date firstProposedStart;
  for (auto rr = opplan->getOperation()->getOperationPlans();
       rr != OperationPlan::end(); ++rr) {
    if (!(&*rr)->getProposed()) continue;
    if (!firstProposedStart && (&*rr) == opplan)
      return Py_BuildValue("(dO)", 100.0 - opplan->getDelay() / 86400, Py_None);
    else if (!firstProposedStart)
      firstProposedStart = (&*rr)->getStart();
    else if (firstProposedStart && opplan->getStart() <= firstProposedStart)
      return Py_BuildValue("(dO)", 100.0 - opplan->getDelay() / 86400, Py_None);
    else
      return Py_BuildValue("(dO)", 999999.0, Py_None);
  }
  return Py_BuildValue("(dO)", 999999.0, Py_None);
}

SetupEvent::SetupEvent(OperationPlan* x)
    : TimeLine<LoadPlan>::Event(5), opplan(x) {
  initType(metadata);
  if (opplan) dt = x->getStart();
}

SetupEvent::~SetupEvent() {
  if (opplan) opplan->nullSetupEvent();
}

void SetupEvent::erase() {
  if (stateinfo) return;
  if (tmline) tmline->erase(this);
  if (opplan && rule && rule->getResource()) {
    for (auto l = opplan->beginLoadPlans(); l != opplan->endLoadPlans();) {
      if (l->getLoad())
        ++l;
      else
        l.deleteLoadPlan();
    }
  }
}

void SetupEvent::update(TimeLine<LoadPlan>* res, Date d, const PooledString& s,
                        SetupMatrixRule* r) {
  setup = s;
  rule = r;
  if (stateinfo) {
    dt = d;
    tmline = res;
  } else if (res != tmline)
    // Insert in resource timeling
    setTimeLine(res);
  else
    // Update the position in the list
    tmline->update(this, d);
}

SetupEvent* SetupEvent::getSetupBefore() const {
  auto i = getTimeLine()->begin(this);
  --i;
  while (i != getTimeLine()->end()) {
    if (i->getEventType() == 5)
      return const_cast<SetupEvent*>(static_cast<const SetupEvent*>(&*i));
    --i;
  }
  return nullptr;
}

int SetupEvent::initialize() {
  // Initialize the metadata
  metadata =
      MetaCategory::registerCategory<SetupEvent>("setupevent", "setupevents");
  registerFields<SetupEvent>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python type
  auto& x = FreppleCategory<SetupEvent>::getPythonType();
  x.setName("setupevent");
  x.setDoc("frePPLe setup event");
  x.supportgetattro();
  x.supportsetattro();
  metadata->setPythonClass(x);
  return x.typeReady();
}

void OperationPlan::setResetResources(bool b) {
  if (!b) return;
  LoadPlanIterator f = beginLoadPlans();
  while (f != endLoadPlans()) {
    auto tmp = &*f;
    ++f;
    delete tmp;
  }
  firstloadplan = nullptr;
}

void OperationPlan::appendInfo(const string& s) {
  if (info.empty())
    info = s;
  else if (!info.contains(s))
    info = PooledString(static_cast<string>(info) + "\n" + s);
}

}  // namespace frepple
