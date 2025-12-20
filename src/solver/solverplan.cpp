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

#include "frepple/solver.h"
namespace frepple {

const MetaClass* SolverPropagateStatus::metadata;
const MetaClass* SolverCreate::metadata;
const Keyword SolverCreate::tag_iterationthreshold("iterationthreshold");
const Keyword SolverCreate::tag_iterationaccuracy("iterationaccuracy");
const Keyword SolverCreate::tag_lazydelay("lazydelay");
const Keyword SolverCreate::tag_createdeliveries("createdeliveries");
const Keyword SolverCreate::tag_administrativeleadtime(
    "administrativeleadtime");
const Keyword SolverCreate::tag_minimumdelay("minimumdelay");
const Keyword SolverCreate::tag_rotateresources("rotateresources");
const Keyword SolverCreate::tag_iterationmax("iterationmax");
const Keyword SolverCreate::tag_resourceiterationmax("resourceiterationmax");
const Keyword SolverCreate::tag_erasePreviousFirst("erasePreviousFirst");

void LibrarySolver::initialize() {
  // Initialize only once
  static bool init = false;
  if (init) {
    logger << "Warning: Calling frepple::LibrarySolver::initialize() more "
           << "than once." << endl;
    return;
  }
  init = true;

  // Register all classes.
  int nok = 0;
  nok += SolverCreate::initialize();
  nok += OperatorDelete::initialize();
  nok += SolverPropagateStatus::initialize();
  if (nok) throw RuntimeException("Error registering new Python types");
}

int SolverCreate::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<SolverCreate>(
      "solver", "solver_mrp", Object::create<SolverCreate>, true);
  registerFields<SolverCreate>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleClass<SolverCreate, Solver>::getPythonType();
  x.setName("solver_mrp");
  x.setDoc("frePPLe solver_mrp");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("solve", solve, METH_VARARGS, "run the solver");
  x.addMethod("commit", commit, METH_NOARGS, "commit the plan changes");
  x.addMethod("rollback", rollback, METH_NOARGS, "rollback the plan changes");
  x.addMethod("createsBatches", createsBatches, METH_NOARGS,
              "group operationplans");
  x.addMethod("markAutofence", markAutofence, METH_NOARGS,
              "recognize buffers to which autofence applies");
  metadata->setPythonClass(x);
  return x.typeReady();
}

PyObject* SolverCreate::create(PyTypeObject*, PyObject*, PyObject* kwds) {
  try {
    // Create the solver
    auto* s = new SolverCreate();

    // Iterate over extra keywords, and set attributes.   @todo move this
    // responsibility to the readers...
    if (kwds) {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value)) {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        const MetaFieldBase* fmeta =
            SolverCreate::metadata->findField(attr.getHash());
        if (!fmeta) fmeta = Solver::metadata->findField(attr.getHash());
        if (fmeta)
          // Update the attribute
          fmeta->setField(s, field);
        else
          s->setProperty(attr.getName(), value);
      };
    }

    // Return the object. The reference count doesn't need to be increased
    // as we do with other objects, because we want this object to be available
    // for the garbage collector of Python.
    return static_cast<PyObject*>(s);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

SolverCreate::SolverData::SolverData(SolverCreate* s, int c, deque<Demand*>* d)
    : sol(s),
      cluster(c),
      demands(d),
      constrainedPlanning(true),
      logConstraints(true),
      state(statestack),
      prevstate(statestack - 1) {
  assert(s);

  // Delete operator
  operator_delete = new OperatorDelete();
  operator_delete->setLogLevel(s->getLogLevel());
}

void SolverCreate::SolverData::setCommandManager(CommandManager* a) {
  if (mgr == a) return;
  mgr = a;
  if (operator_delete) operator_delete->setCommandManager(a);
}

SolverCreate::SolverData::~SolverData() { delete operator_delete; };

bool SolverCreate::isLeadTimeConstrained(const Operation* oper) const {
  if (oper && (oper->hasType<OperationItemSupplier>() ||
               oper->getCategory() == "subcontractor"))
    return (constrts & PO_LEADTIME) > 0;
  else if (oper && oper->hasType<OperationSplit, OperationAlternate>()) {
    bool all_po = true;
    for (auto & alt : oper->getSubOperations()) {
      if (alt->getOperation()->getPriority() &&
          !(alt->getOperation()->hasType<OperationItemSupplier>() ||
            alt->getOperation()->getCategory() == "subcontractor")) {
        all_po = false;
        break;
      }
    }
    if (all_po)
      return (constrts & PO_LEADTIME) > 0;
    else
      return (constrts & MFG_LEADTIME) > 0;
  } else
    return (constrts & MFG_LEADTIME) > 0;
}

bool SolverCreate::demand_comparison(const Demand* l1, const Demand* l2) {
  if ((l1->getStatus() == Demand::STATUS_QUOTE ||
       l1->getStatus() == Demand::STATUS_INQUIRY) &&
      l2->getStatus() != Demand::STATUS_QUOTE &&
      l2->getStatus() != Demand::STATUS_INQUIRY)
    return false;
  else if ((l2->getStatus() == Demand::STATUS_QUOTE ||
            l2->getStatus() == Demand::STATUS_INQUIRY) &&
           l1->getStatus() != Demand::STATUS_QUOTE &&
           l1->getStatus() != Demand::STATUS_INQUIRY)
    return true;
  else if (l1->getPriority() != l2->getPriority())
    return l1->getPriority() < l2->getPriority();
  else if (l1->getDue() != l2->getDue())
    return l1->getDue() < l2->getDue();
  else if (l1->getQuantity() != l2->getQuantity())
    return l1->getQuantity() < l2->getQuantity();
  else
    return l1->getName() < l2->getName();
}

void SolverCreate::SolverData::push(double q, Date d, bool full) {
  if (state >= statestack + MAXSTATES)
    throw RuntimeException("Maximum recursion depth exceeded");
  ++state;
  ++prevstate;
  state->q_qty = q;
  state->q_date = d;
  state->q_date_max = d;
  if (full) {
    state->q_loadplan = prevstate->q_loadplan;
    state->q_flowplan = prevstate->q_flowplan;
    state->q_operationplan = prevstate->q_operationplan;
    state->curOwnerOpplan = prevstate->curOwnerOpplan;
    state->blockedOpplan = prevstate->blockedOpplan;
    state->dependency = prevstate->dependency;
    state->curDemand = prevstate->curDemand;
    state->curBuffer = prevstate->curBuffer;
    state->q_qty_min = prevstate->q_qty_min;
    state->forceLate = prevstate->forceLate;
    state->a_cost = prevstate->a_cost;
    state->a_penalty = prevstate->a_penalty;
    state->curBatch = prevstate->curBatch;
    state->forceAccept = prevstate->forceAccept;
    state->has_bucketized_resources = prevstate->has_bucketized_resources;
    state->keepAssignments = prevstate->keepAssignments;
  } else {
    state->q_loadplan = nullptr;
    state->q_flowplan = nullptr;
    state->q_operationplan = nullptr;
    state->curOwnerOpplan = nullptr;
    state->blockedOpplan = nullptr;
    state->dependency = nullptr;
    state->curDemand = nullptr;
    state->curBuffer = nullptr;
    state->q_qty_min = 1.0;
    state->forceLate = false;
    state->a_cost = 0.0;
    state->a_penalty = 0.0;
    state->curBatch = PooledString::emptystring;
    state->forceAccept = false;
    state->has_bucketized_resources = false;
    state->keepAssignments = nullptr;
  }
  state->a_date = Date::infiniteFuture;
  state->a_qty = 0.0;
}

void SolverCreate::SolverData::pop(bool copy_answer) {
  if (state < statestack) throw LogicException("State stack empty");
  if (copy_answer) {
    prevstate->a_qty = state->a_qty;
    prevstate->a_date = state->a_date;
    prevstate->a_penalty = state->a_penalty;
    prevstate->a_cost = state->a_cost;
    prevstate->forceAccept = state->forceAccept;
  }
  --state;
  --prevstate;
}

void SolverCreate::SolverData::commit() {
  // Check
  SolverCreate* solver = getSolver();
  if (!solver || (!demands && solver->getCreateDeliveries()))
    throw LogicException("Missing demands or solver.");

  // Message
  if (solver->getLogLevel() > 0)
    logger << "Start solving cluster " << cluster << endl;

  maskTemporaryShortages();

  // Solve the planning problem
  try {
    if (!solver->getConstraints()) {
      // Special case to use a single sweep for truely unconstrained plans

      // Step 1: Create a delivery operationplan for all demands
      solver->setPropagate(false);
      if (solver->getCreateDeliveries()) {
        for (auto & demand : *demands) {
          if (solver->userexit_demand)
            solver->userexit_demand.call(demand, PythonData(constrainedPlanning));

          // Determine the quantity to be planned and the date for the planning
          // loop
          double plan_qty = demand->getQuantity() - demand->getPlannedQuantity();
          if (demand->getDue() == Date::infiniteFuture ||
              demand->getDue() == Date::infinitePast)
            continue;

          // Select delivery operation
          Operation* deliveryoper = demand->getDeliveryOperation();
          if (!deliveryoper) continue;

          auto isGroupMember =
              demand->getOwner() && demand->getOwner()->hasType<DemandGroup>() &&
              static_cast<DemandGroup*>(demand->getOwner())->getPolicy() !=
                  Demand::POLICY_INDEPENDENT;
          auto due =
              isGroupMember ? demand->getOwner()->getDue() : demand->getDue();
          while (plan_qty > ROUNDING_ERROR) {
            // Respect minimum shipment quantities
            if (plan_qty < demand->getMinShipment())
              plan_qty = demand->getMinShipment();
            state->curBuffer = nullptr;
            state->q_qty = plan_qty;
            state->q_date = due;
            state->a_cost = 0.0;
            state->a_penalty = 0.0;
            state->curDemand = demand;
            state->curOwnerOpplan = nullptr;
            state->blockedOpplan = nullptr;
            state->dependency = nullptr;
            state->curBatch = demand->getBatch();
            dependency_list.clear();
            state->a_qty = 0;
            try {
              deliveryoper->solve(*solver, this);
              getCommandManager()->commit();
              plan_qty -= state->a_qty;
              if (!state->a_qty) {
                if (state->a_date == Date::infiniteFuture ||
                    state->a_date <= due)
                  break;
                else
                  // Also unconstrained plan may need to repeat the loop.
                  // Can be caused with complete lack of any availability
                  // before the requirement date.
                  due = state->a_date;
              }
            } catch (const exception& e) {
              logger << "Error creating delivery for '" << demand
                     << "': " << e.what() << endl;
              getCommandManager()->rollback();
              break;
            }
          }
        }
      }

      // Step 3: Solve buffer by buffer, ordered by level
      buffer_solve_shortages_only = false;
      for (short lvl = -1; lvl <= HasLevel::getNumberOfLevels(); ++lvl) {
        // Step 1: Allocate from generic-MTO buffers to MTO-batch buffers
        /*
        for (auto& b : Buffer::all()) {
          if (b.getLevel() != lvl ||
              (cluster != -1 && cluster != b.getCluster()) || !b.getItem() ||
              !b.getItem()->hasType<ItemMTO>() || !b.getBatch().empty())
            // Not your turn yet...
            continue;

          // Loop while we still have available material
          bool changed = true;
          while (changed &&
                 b.getOnHand(Date::infiniteFuture) > ROUNDING_ERROR) {
            changed = false;
            // Find the first available material
            OperationPlan::flowplanlist::Event* producer = nullptr;
            double available = 0.0;
            for (auto& flpln : b.getFlowPlans()) {
              if (flpln.getQuantity() <= 0) continue;
              available = flpln.getAvailable();
              if (available > ROUNDING_ERROR) {
                producer = &flpln;
                break;
              }
            }
            if (!producer) break;

            // Loop through all batch-MTO buffers and see which one has the
            // earliest requirement for that material
            FlowPlan* consumer = nullptr;
            auto bufiter = b.getItem()->getBufferIterator();
            while (auto batchbuf = bufiter.next()) {
              if (batchbuf->getBatch().empty()) continue;
              for (auto& flpln : batchbuf->getFlowPlans()) {
                if (flpln.getQuantity() >= 0 ||
                    flpln.getDate() < producer->getDate())
                  continue;
                if (flpln.getOnhandAfterDate() < -ROUNDING_ERROR &&
                    (!consumer || consumer->getDate() > flpln.getDate())) {
                  consumer = static_cast<FlowPlan*>(&flpln);
                  break;
                }
              }
            }
            if (!consumer) break;

            // Flip the consumer from the batch-MTO to the generic-MTO buffer
            changed = true;
            if (available > -consumer->getQuantity()) {
              if (getLogLevel() > 1)
                logger << solver->indentlevel << "  Buffer '" << b
                       << "' allocates from generic MTO buffer '"
                       << consumer->getBuffer()
                       << "' : " << -consumer->getQuantity() << " on "
                       << consumer->getDate() << endl;
              consumer->setBuffer(&b);
            } else {
              if (getLogLevel() > 1)
                logger << solver->indentlevel << "  Buffer '" << b
                       << "' allocates from generic MTO buffer '"
                       << consumer->getBuffer() << "' : " << available << " on "
                       << consumer->getDate() << endl;
              auto extraflpln = new FlowPlan(consumer->getOperationPlan(),
                                             consumer->getFlow(),
                                             consumer->getDate(), -available);
              extraflpln->setBuffer(&b);
              consumer->setQuantityRaw(consumer->getQuantity() + available);
            }
          }
        }
        */

        // Step 2: propagate through this level of buffers
        for (auto& b : Buffer::all()) {
          if (b.getLevel() != lvl ||
              (cluster != -1 && cluster != b.getCluster()))
            // Not your turn yet...
            continue;

          // Given the demand, ROQ and safety stock, we resolve the shortage
          // with an unconstrained propagation to the next level.
          state->curBuffer = nullptr;
          state->q_qty = -1.0;
          state->q_date = Date::infinitePast;
          state->a_cost = 0.0;
          state->a_penalty = 0.0;
          state->curDemand = nullptr;
          state->curOwnerOpplan = nullptr;
          state->blockedOpplan = nullptr;
          state->dependency = nullptr;
          state->a_qty = 0;
          try {
            b.solve(*solver, this);
            getCommandManager()->commit();
          } catch (const exception& e) {
            logger << "Error propagating through buffer '" << b
                   << "': " << e.what() << endl;
            getCommandManager()->rollback();
          }
        }
      }

      // Clean up excess inventory
      scanExcess(false);
    } else {
      // Normal case: demand-per-demand loop

      // Sort the demands of this problem.
      // We use a stable sort to get reproducible results between platforms
      // and STL implementations.
      if (!solver->userexit_nextdemand)
        stable_sort(demands->begin(), demands->end(), demand_comparison);

      // Solve for safety stock in buffers.
      constrainedPlanning = (solver->getPlanType() == 1);
      safety_stock_planning = true;
      buffer_solve_shortages_only = false;
      solveSafetyStock(solver, true);

      // Loop through the list of all demands in this planning problem
      safety_stock_planning = false;
      Demand* curdmd;
      auto iterdmd = demands->begin();
      do {
        // Find the next demand to plan
        if (solver->userexit_nextdemand) {
          auto obj =
              solver->userexit_nextdemand.call(PythonData(cluster)).getObject();
          if (!obj || obj == Py_None)
            break;
          else if (obj->getType().category == Demand::metadata ||
                   obj->getType().type == "demand_forecastbucket")
            curdmd = static_cast<Demand*>(obj);
          else
            throw DataException("User exit nextdemand must return a demand");
        } else if (iterdmd == demands->end())
          break;
        else {
          curdmd = *iterdmd;
          ++iterdmd;
        }

        // Plan the demand
        iteration_count = 0;
        try {
          curdmd->solve(*solver, this);
        } catch (...) {
          // Log the exception as the only reason for the demand not being
          // planned
          curdmd->getConstraints().clear();
          // Error message
          logger << "Error: Caught an exception while solving demand '"
                 << curdmd << "':" << endl;
          try {
            throw;
          } catch (const bad_exception&) {
            curdmd->getConstraints().push(new ProblemInvalidData(
                curdmd, "Error: bad exception", "demand", curdmd->getDue(),
                curdmd->getDue(), false));
            logger << "  bad exception" << endl;
          } catch (const exception& e) {
            curdmd->getConstraints().push(new ProblemInvalidData(
                curdmd, "Error: " + string(e.what()), "demand",
                curdmd->getDue(), curdmd->getDue(), false));
            logger << "  " << e.what() << endl;
          } catch (...) {
            curdmd->getConstraints().push(new ProblemInvalidData(
                curdmd, "Error: unknown type", "demand", curdmd->getDue(),
                curdmd->getDue(), false));
            logger << "  Unknown type" << endl;
          }
        }
      } while (true);

      // Completely recreate all purchasing operation plans
      for (auto o : purchase_buffers) {
        // Erase existing proposed purchases
        const_cast<Buffer*>(o)->getProducingOperation()->deleteOperationPlans(
            false);
        // Create new proposed purchases
        auto tmp_buffer_solve_shortages_only = buffer_solve_shortages_only;
        try {
          safety_stock_planning = true;
          buffer_solve_shortages_only = false;
          state->curBuffer = nullptr;
          state->q_qty = -1.0;
          state->q_date = Date::infinitePast;
          state->a_cost = 0.0;
          state->a_penalty = 0.0;
          state->curDemand = nullptr;
          state->curOwnerOpplan = nullptr;
          state->blockedOpplan = nullptr;
          state->dependency = nullptr;
          state->a_qty = 0;
          state->curBatch = o->getBatch();
          o->solve(*solver, this);
          getCommandManager()->commit();
        } catch (...) {
          getCommandManager()->rollback();
        }
        buffer_solve_shortages_only = tmp_buffer_solve_shortages_only;
      }
      purchase_buffers.clear();

      // Second run to solve for safety stock in buffers.
      constrainedPlanning = (solver->getPlanType() == 1);
      safety_stock_planning = true;
      buffer_solve_shortages_only = false;
      solveSafetyStock(solver, false);
    }

    // Operation batching postprocessing
    for (auto& o : Operation::all()) {
      if (cluster == -1 || o.getCluster() == cluster)
        solver->createsBatches(&o, this);
    }

    // Clean the list of demands of this cluster
    demands->clear();

    // Clean up excess inventory
    scanExcess(solver->getPlanType() == 1);
  } catch (...) {
    // We come in this exception handling code only if there is a problem with
    // with this cluster that goes beyond problems with single orders.
    // If the problem is with single orders, the exception handling code above
    // will do a proper rollback.

    // Error message
    logger << "Error: Caught an exception while solving cluster " << cluster
           << ":" << endl;
    try {
      throw;
    } catch (const bad_exception&) {
      logger << "  bad exception" << endl;
    } catch (const exception& e) {
      logger << "  " << e.what() << endl;
    } catch (...) {
      logger << "  Unknown type" << endl;
    }

    // Clean up the operationplans of this cluster
    for (auto& f : Operation::all())
      if (f.getCluster() == cluster) f.deleteOperationPlans();

    // Clean the list of demands of this cluster
    demands->clear();
  }

  unmaskTemporaryShortages();

  // Message
  if (solver->getLogLevel() > 0)
    logger << "End solving cluster " << cluster << endl;
}

void SolverCreate::SolverData::solveSafetyStock(SolverCreate* solver,
                                                bool first_pass) {
  safety_stock_planning = true;
  if (getLogLevel() > 0)
    logger << "Start safety stock replenishment pass for cluster " << cluster
           << endl;
  vector<list<Buffer*> > bufs(HasLevel::getNumberOfLevels() + 1);
  for (auto& buf : Buffer::all())
    if ((buf.getCluster() == cluster || cluster == -1) &&
        !buf.hasType<BufferInfinite>() && buf.getProducingOperation() &&
        (buf.getMinimum() || buf.getMinimumCalendar() ||
         buf.getFlowPlans().begin() != buf.getFlowPlans().end())) {
      if (!first_pass) {
        auto last = buf.getFlowPlans().rbegin();
        if (last != buf.getFlowPlans().end() &&
            last->getOnhand() >= last->getMin() - ROUNDING_ERROR)
          // Second pass should only pick up buffers with a remaining safety
          // stock shortage at the end of the horizon
          continue;
      }
      bufs[(buf.getLevel() >= 0) ? buf.getLevel() : 0].push_back(&buf);
    }
  State* mystate = state;
  for (auto& b_list : bufs)
    for (auto& b : b_list) {
      try {
        state->curBuffer = nullptr;
        // A quantity of -1 is a flag for the buffer solver to solve safety
        // stock.
        state->q_qty = -1.0;
        state->q_date = Date::infinitePast;
        state->a_cost = 0.0;
        state->a_penalty = 0.0;
        constraints = nullptr;
        state->curDemand = nullptr;
        state->curOwnerOpplan = nullptr;
        state->blockedOpplan = nullptr;
        state->dependency = nullptr;
        buffer_solve_shortages_only = false;
        state->curBatch = (*b).getBatch();
        // Call the buffer safety stock solver
        iteration_count = 0;
        b->solve(*solver, this);
        getCommandManager()->commit();
      } catch (const bad_exception&) {
        logger << "Error: bad exception solving safety stock for " << *b
               << endl;
        while (state > mystate) pop();
        getCommandManager()->rollback();
      } catch (const exception& e) {
        logger << "Error: exception solving safety stock for " << *b << ": "
               << e.what() << endl;
        while (state > mystate) pop();
        getCommandManager()->rollback();
      } catch (...) {
        logger << "Error: unknown exception solving safety stock for " << *b
               << endl;
        while (state > mystate) pop();
        getCommandManager()->rollback();
      }
    }
  if (getLogLevel() > 0)
    logger << "Finished safety stock replenishment pass" << endl;
  safety_stock_planning = false;
}

void SolverCreate::SolverData::scanExcess(bool constrained) {
  OperatorDelete cleanup(getCommandManager());
  cleanup.setConstrained(constrained);
  cleanup.setPropagate(false);
  if (getLogLevel() > 0) {
    logger << "Start scanning excess in cluster " << cluster << endl;
    cleanup.setLogLevel(getLogLevel());
  }
  vector<list<Buffer*> > bufs(HasLevel::getNumberOfLevels() + 1);
  for (auto& buf : Buffer::all())
    if ((buf.getCluster() == cluster || cluster == -1) &&
        !buf.hasType<BufferInfinite>() && buf.getProducingOperation() &&
        (buf.getMinimum() || buf.getMinimumCalendar() ||
         buf.getFlowPlans().begin() != buf.getFlowPlans().end()))
      bufs[(buf.getLevel() >= 0) ? buf.getLevel() : 0].push_back(&buf);
  State* mystate = state;
  for (auto& b_list : bufs) {
    for (auto& b : b_list) {
      try {
        b->solve(cleanup, this);
      } catch (const bad_exception&) {
        logger << "Error: bad exception scanning excess for " << *b << endl;
        while (state > mystate) pop();
        getCommandManager()->rollback();
      } catch (const exception& e) {
        logger << "Error: exception scanning excess for " << *b << ": "
               << e.what() << endl;
        while (state > mystate) pop();
        getCommandManager()->rollback();
      } catch (...) {
        logger << "Error: unknown exception scanning excess for " << *b << endl;
        while (state > mystate) pop();
        getCommandManager()->rollback();
      }
    }
    getCommandManager()->commit();
  }
  if (getLogLevel() > 0) logger << "Finished excess scan" << endl;
}

void SolverCreate::SolverData::maskTemporaryShortages() {
  for (auto& buf : Buffer::all())
    if ((buf.getCluster() == cluster || cluster == -1) &&
        !buf.hasType<BufferInfinite>() && buf.getProducingOperation()) {
      auto fence = Plan::instance().getAutoFence();
      if (!fence)
        // Autofence value of 0 doesn't mask any temporary shortages
        return;
      Operation* correction = nullptr;
      for (auto flpln = buf.getFlowPlans().begin();
           flpln != buf.getFlowPlans().end(); ++flpln) {
        if (flpln->isLastOnDate() && flpln->getOnhand() < -ROUNDING_ERROR) {
          // Scan to see the end of the shortage period
          auto qty = -flpln->getOnhand();
          Date shortage_ends;
          for (Buffer::flowplanlist::const_iterator scanner = flpln;
               scanner != buf.getFlowPlans().end(); ++scanner) {
            if (scanner->getDate() >
                max(flpln->getDate(), Plan::instance().getCurrent()) + fence)
              break;
            else if (scanner->getOnhand() > -qty && scanner->isLastOnDate()) {
              shortage_ends = scanner->getDate();
              break;
            }
          }

          // Correct inventory
          if (shortage_ends) {
            if (!correction) {
              correction = new OperationFixedTime();
              correction->setName("Correction for " + buf.getName());
              correction->setHidden(true);
              new FlowEnd(correction, &buf, -1);
              new FlowStart(correction, &buf, 1);
            }
            auto opplan = correction->createOperationPlan(
                qty, flpln->getDate(), shortage_ends, buf.getBatch());
            opplan->setConfirmed(true);
            opplan->setStartAndEnd(flpln->getDate(), shortage_ends);
            maskedShortages.push_back(opplan);
            if (getLogLevel() > 0)
              logger << "Warning: Masking temporary material shortage on '"
                     << buf.getName() << "' for " << opplan->getQuantity()
                     << " during " << opplan->getDates() << endl;
          }
        }
      }
    }
}

void SolverCreate::SolverData::unmaskTemporaryShortages() {
  while (!maskedShortages.empty()) {
    auto o = maskedShortages.back();
    maskedShortages.pop_back();
    delete o;
  }
}

void SolverCreate::update_user_exits() {
  setUserExitBuffer(getPyObjectProperty(Tags::userexit_buffer.getName()));
  setUserExitDemand(getPyObjectProperty(Tags::userexit_demand.getName()));
  setUserExitNextDemand(
      getPyObjectProperty(Tags::userexit_nextdemand.getName()));
  setUserExitFlow(getPyObjectProperty(Tags::userexit_flow.getName()));
  setUserExitOperation(getPyObjectProperty(Tags::userexit_operation.getName()));
  setUserExitResource(getPyObjectProperty(Tags::userexit_resource.getName()));
}

void SolverCreate::solve(void*) {
  // Configure user exits
  update_user_exits();

  // Count how many clusters we have to plan
  int cl = 1;
  if (cluster == -1 && getConstraints() && getCreateDeliveries())
    cl = HasLevel::getNumberOfClusters() + 1;

  // Categorize all demands in their cluster
  demands_per_cluster.resize(cl);
  if (getCreateDeliveries()) {
    if (!getConstraints()) {
      // Dumb unconstrained plan is running in a single thread
      for (auto& i : Demand::all())
        if (i.getQuantity() > 0 &&
            (i.getStatus() == Demand::STATUS_OPEN ||
             i.getStatus() == Demand::STATUS_QUOTE ||
             (i.getStatus() == Demand::STATUS_INQUIRY && i.getOwner() &&
              i.getOwner()->hasType<DemandGroup>() &&
              i.getOwner()->getStatus() == Demand::STATUS_INQUIRY &&
              static_cast<DemandGroup*>(i.getOwner())->getPolicy() !=
                  Demand::POLICY_INDEPENDENT)))
          demands_per_cluster[0].push_back(&i);
    } else if (cluster == -1 && !userexit_nextdemand) {
      // Many clusters to solve
      for (auto& i : Demand::all()) {
        bool isGroup = i.hasType<DemandGroup>() &&
                       static_cast<DemandGroup&>(i).getPolicy() !=
                           Demand::POLICY_INDEPENDENT;
        bool isMemberOfGroup =
            i.getOwner() && i.getOwner()->hasType<DemandGroup>() &&
            static_cast<DemandGroup*>(i.getOwner())->getPolicy() !=
                Demand::POLICY_INDEPENDENT;
        if ((isGroup || (i.getQuantity() > 0 && !isMemberOfGroup)) &&
            (i.getStatus() == Demand::STATUS_OPEN ||
             i.getStatus() == Demand::STATUS_QUOTE ||
             i.getStatus() == Demand::STATUS_INQUIRY))
          demands_per_cluster[i.getCluster()].push_back(&i);
      }
    } else if (!userexit_nextdemand) {
      // Only a single cluster to plan
      for (auto& i : Demand::all()) {
        if (i.getCluster() != cluster) continue;
        bool isGroup = i.hasType<DemandGroup>() &&
                       static_cast<DemandGroup&>(i).getPolicy() !=
                           Demand::POLICY_INDEPENDENT;
        bool isMemberOfGroup =
            i.getOwner() && i.getOwner()->hasType<DemandGroup>() &&
            static_cast<DemandGroup*>(i.getOwner())->getPolicy() !=
                Demand::POLICY_INDEPENDENT;
        if ((isGroup || (i.getQuantity() > 0 && !isMemberOfGroup)) &&
            (i.getStatus() == Demand::STATUS_OPEN ||
             i.getStatus() == Demand::STATUS_QUOTE))
          demands_per_cluster[0].push_back(&i);
      }
    }
  }

  // Delete of operationplans
  // This deletion is not multi-threaded... But on the other hand we need to
  // loop through the operations only once
  if (getErasePreviousFirst()) {
    if (getLogLevel() > 0) logger << "Deleting previous plan" << endl;
    for (auto& e : Operation::all())
      if (cluster == -1 || e.getCluster() == cluster) e.deleteOperationPlans();
  }

  // Solve in parallel threads.
  // When not solving in silent and autocommit mode, we only use a single
  // solver thread.
  // We also avoid solving the unconstrained single-sweep plan to run in
  // multiple threads (the overhead of using multiple threads is then too high)
  // Otherwise we use as many worker threads as processor cores.
  ThreadGroup threads;
  if (getLogLevel() > 0 || !getAutocommit() || cluster != -1 ||
      !getConstraints() || !getCreateDeliveries())
    threads.setMaxParallel(1);

  // Register all clusters to be solved
  for (int j = 0; j < cl; ++j) {
    int tmp;
    if (!getCreateDeliveries())
      tmp = -1;
    else if (!getConstraints() && cluster == -1)
      tmp = -1;
    else if (cluster == -1)
      tmp = j;
    else
      tmp = cluster;
    threads.add(SolverData::runme, this, tmp, &(demands_per_cluster[j]));
  }
  // Run the planning command threads and wait for them to exit
  threads.execute();
}

PyObject* SolverCreate::solve(PyObject* self, PyObject* args,
                              PyObject* kwargs) {
  // Parse the argument
  static const char* kwlist[] = {"object", "cluster", nullptr};
  PyObject* dem = nullptr;
  int cluster = -1;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|Oi:solve",
                                   const_cast<char**>(kwlist), &dem, &cluster))
    return nullptr;
  if (dem && !PyObject_TypeCheck(dem, Demand::metadata->pythonClass) &&
      !PyObject_TypeCheck(dem, Buffer::metadata->pythonClass)) {
    PyErr_SetString(PythonDataException,
                    "object argument must be a demand or a buffer");
    return nullptr;
  }

  // Free Python interpreter for other threads
  auto* sol = static_cast<SolverCreate*>(self);
  auto prev_cluster = sol->getCluster();
  Py_BEGIN_ALLOW_THREADS;
  try {
    if (!dem) {
      // Complete replan or cluster replan
      sol->setCluster(cluster);
      sol->setAutocommit(true);
      sol->solve();
    } else {
      // Incrementally plan a single demand or buffer
      sol->setCluster(-1);
      sol->setAutocommit(false);
      sol->update_user_exits();
      if (PyObject_TypeCheck(dem, Demand::metadata->pythonClass))
        static_cast<Demand*>(dem)->solve(*sol, &(sol->getCommands()));
      else if (PyObject_TypeCheck(dem, Buffer::metadata->pythonClass)) {
        auto state = sol->getCommands().state;
        state->q_qty = -1.0;
        state->curBuffer = static_cast<Buffer*>(dem);
        state->q_date = Date::infinitePast;
        state->a_cost = 0.0;
        state->a_penalty = 0.0;
        state->curDemand = nullptr;
        state->curOwnerOpplan = nullptr;
        state->blockedOpplan = nullptr;
        state->dependency = nullptr;
        state->curBatch = state->curBuffer->getBatch();
        state->curBuffer->solve(*sol, &(sol->getCommands()));
      }
    }
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    sol->setCluster(prev_cluster);
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  sol->setCluster(prev_cluster);
  return Py_BuildValue("");
}

PyObject* SolverCreate::commit(PyObject* self, PyObject*) {
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    auto* me = static_cast<SolverCreate*>(self);
    assert(me->commands.getCommandManager());
    me->scanExcess(me->commands.getCommandManager());
    me->commands.getCommandManager()->commit();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

PyObject* SolverCreate::rollback(PyObject* self, PyObject*) {
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    auto* me = static_cast<SolverCreate*>(self);
    assert(me->commands.getCommandManager());
    me->commands.getCommandManager()->rollback();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

PyObject* SolverCreate::markAutofence(PyObject* self, PyObject*) {
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    auto* me = static_cast<SolverCreate*>(self);
    for (auto& buf : Buffer::all()) {
      // A buffer should have autofence active if it doesn't have proposed
      // replenishments
      bool has_proposed_supply = false;
      for (auto& flpln : buf.getFlowPlans()) {
        if (flpln.getQuantity() > 0 &&
            flpln.getOperationPlan()->getProposed()) {
          has_proposed_supply = true;
          break;
        }
      }
      buf.setAutofence(!has_proposed_supply);
      if (has_proposed_supply && me->getLogLevel() > 1)
        logger << buf << " deactivates autofence" << endl;
    }
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

int SolverPropagateStatus::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<SolverPropagateStatus>(
      "solver", "solver_propagateStatus", Object::create<SolverPropagateStatus>,
      false);
  registerFields<SolverPropagateStatus>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  auto& x = FreppleClass<SolverPropagateStatus, Solver>::getPythonType();
  x.setName("solver_propagateStatus");
  x.setDoc("frePPLe solver_propagateStatus");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("solve", solve, METH_NOARGS, "run the solver");
  metadata->setPythonClass(x);
  return x.typeReady();
}

PyObject* SolverPropagateStatus::create(PyTypeObject*, PyObject*,
                                        PyObject* kwds) {
  try {
    // Create the solver
    auto* s = new SolverPropagateStatus();

    // Iterate over extra keywords, and set attributes.   @todo move this
    // responsibility to the readers...
    if (kwds) {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value)) {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        const MetaFieldBase* fmeta =
            SolverCreate::metadata->findField(attr.getHash());
        if (!fmeta) fmeta = Solver::metadata->findField(attr.getHash());
        if (fmeta)
          // Update the attribute
          fmeta->setField(s, field);
        else
          s->setProperty(attr.getName(), value);
      };
    }

    // Return the object. The reference count doesn't need to be increased
    // as we do with other objects, because we want this object to be available
    // for the garbage collector of Python.
    return static_cast<PyObject*>(s);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

PyObject* SolverPropagateStatus::solve(PyObject* self, PyObject*) {
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    static_cast<SolverPropagateStatus*>(self)->solve();
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void SolverPropagateStatus::solve(void*) {
  bool log = getLogLevel() > 0;
  for (short lvl = 0; lvl <= HasLevel::getNumberOfLevels(); ++lvl) {
    for (auto& oper : Operation::all()) {
      if (oper.getLevel() != lvl) continue;
      for (auto opplan = oper.getOperationPlans();
           opplan != OperationPlan::end(); ++opplan) {
        if (!oper.getDependencies().empty()) opplan->matchDependencies(log);
        if (opplan->getSubOperationPlans() == OperationPlan::end() &&
            (opplan->getClosed() || opplan->getCompleted()))
          opplan->propagateStatus(log);
      }
    }
  }
  for (auto& buf : Buffer::all()) {
    auto oh = buf.getOnHand(Date::infinitePast, Date::infiniteFuture);
    if (oh < 0.0) {
      unsigned int cnt = 0;
      for (auto oo = buf.getFlowPlans().begin(); oo != buf.getFlowPlans().end();
           ++oo)
        ++cnt;
      if (oh > -ROUNDING_ERROR * cnt) buf.setOnHand(buf.getOnHand() - oh);
    }
  }
}

}  // namespace frepple
