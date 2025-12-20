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

void SolverCreate::checkOperationCapacity(OperationPlan* opplan,
                                          SolverCreate::SolverData& data) {
  unsigned short constrainedLoads = 0;
  for (auto h = opplan->beginLoadPlans(); h != opplan->endLoadPlans(); ++h)
    if (h->getResource()->getConstrained() && h->isStart() && h->getLoad() &&
        h->getLoad()->getQuantity() != 0.0) {
      if (++constrainedLoads > 1) break;
    }
  if (!constrainedLoads) return;  // Stop here if no resource is loaded

  DateRange orig;
  bool backuplogconstraints = data.logConstraints;
  bool backupForceLate = data.state->forceLate;
  bool recheck, first;

  // Loop through all loadplans, and solve for the resource.
  // This may move an operationplan early or late.
  unsigned short counter = 0;
  Date orig_q_date_max = data.state->q_date_max;
  bool first_iteration = true;
  bool delayed_reply = false;
  do {
    if (getLogLevel() > 1) {
      if (!first_iteration)
        logger << indentlevel << "  Rechecking capacity\n";
      else
        first_iteration = false;
    }
    orig = opplan->getDates();
    recheck = false;
    first = true;
    for (auto h = opplan->beginLoadPlans();
         h != opplan->endLoadPlans() && opplan->getDates() == orig; ++h) {
      if (!h->getLoad() || h->getLoad()->getQuantity() == 0.0 ||
          h->getQuantity() == 0.0) {
        // Empty load or loadplan (eg when load is not effective)
        first = false;
        continue;
      }
      if (h->getQuantity() > 0.0)
        // The loadplan is an increase in size, and the resource solver only
        // works on decreases
        continue;

      // Call the load solver - which will call the resource solver.
      data.state->q_operationplan = opplan;
      data.state->q_loadplan = &*h;
      data.state->q_qty = h->getQuantity();
      data.state->q_date = h->getDate();
      h->getLoad()->solve(*this, &data);
      if (opplan->getDates() != orig || data.state->a_qty == 0) {
        if (data.state->a_qty == 0) {
          if (data.state->a_date == Date::infiniteFuture) {
            // Game over
            data.logConstraints =
                backuplogconstraints;  // restore the original value
            data.state->forceLate = backupForceLate;
            if (opplan->getQuantity() > 0.0) opplan->setQuantity(0.0);
            return;
          }
          // One of the resources is late. We want to prevent that other
          // resources are trying to pull in the operationplan again. It can
          // only be delayed from now on in this loop.
          data.state->forceLate = true;
          delayed_reply = true;
        } else if (first)
          // First load is ok, but moved the operationplan.
          // We can continue to check the second loadplan.
          orig = opplan->getDates();
        if (!first && data.state->a_qty) recheck = true;
      }
      first = false;
    }
    data.logConstraints = false;  // Only first loop collects constraint info
    if (++counter >= 20) {
      if (data.constrainedPlanning && isCapacityConstrained())
        data.state->a_qty = 0.0;
      if (data.state->a_date > orig_q_date_max)
        data.state->a_date += getMinimumDelay();
      else
        data.state->a_date = orig_q_date_max + getMinimumDelay();
      if (getLogLevel() > 1)
        logger << indentlevel << "Quitting capacity checking loop\n";
      break;
    }
  }
  // Imagine there are multiple loads. As soon as one of them is moved, we
  // need to redo the capacity check for the ones we already checked.
  // Repeat until no load has touched the opplan, or till proven infeasible.
  // No need to reloop if there is only a single load (= 2 loadplans)
  while (constrainedLoads > 1 && !opplan->getDates().almostEqual(orig) &&
         data.constrainedPlanning &&
         ((data.state->a_qty == 0.0 && data.state->a_date < orig_q_date_max) ||
          recheck));
  // TODO doesn't this loop increment a_penalty incorrectly???

  // Restore original flags
  data.logConstraints = backuplogconstraints;  // restore the original value
  data.state->forceLate = backupForceLate;

  // A late reply was forced, which always means a reply of 0
  if ((delayed_reply || data.state->forceLate) && data.state->a_qty > 0.0)
    data.state->a_qty = 0.0;

  // In case of a zero reply, we resize the operationplan to 0 right away.
  // This is required to make sure that the buffer inventory profile also
  // respects this answer.
  if (data.state->a_qty == 0.0 && opplan->getQuantity() > 0.0)
    opplan->setQuantity(0.0);
}

bool SolverCreate::checkOperation(OperationPlan* opplan,
                                  SolverCreate::SolverData& data,
                                  bool checkCapacity) {
  // The default answer...
  data.state->a_date = Date::infiniteFuture;
  data.state->a_qty = data.state->q_qty;

  // Handle unavailable time.
  // Note that this unavailable time is checked also in an unconstrained plan.
  // This means that also an unconstrained plan can plan demand late!
  if (opplan->getQuantity() == 0.0) {
    // It is possible that the operation could not be created properly.
    // This happens when the operation is not available for enough time.
    // Eg. A fixed time operation needs 10 days on jan 20 on an operation
    //     that is only available only 2 days since the start of the horizon.
    // Resize to the minimum quantity
    opplan->setQuantity(data.state->q_qty_min, false);
    // Move to the earliest start date
    opplan->setStart(Plan::instance().getCurrent());
    // No availability found anywhere in the horizon - data error
    if (opplan->getEnd() == Date::infiniteFuture) {
      string msg = "No available time found on operation '" +
                   opplan->getOperation()->getName() + "'";
      if (data.logConstraints && data.constraints) {
        auto j = data.constraints->begin();
        while (j != data.constraints->end()) {
          if (j->hasType<ProblemInvalidData>() && j->getDescription() == msg)
            break;
          ++j;
        }
        if (j == data.constraints->end())
          data.constraints->push(new ProblemInvalidData(
              opplan->getOperation(), msg, "operation",
              Plan::instance().getCurrent(), Date::infiniteFuture, false));
      }
      bool problem_already_exists = false;
      auto probiter = Problem::iterator(opplan->getOperation());
      while (Problem* prob = probiter.next()) {
        if (typeid(*prob) == typeid(ProblemInvalidData) &&
            prob->getDescription() == msg) {
          problem_already_exists = true;
          break;
        }
      }
      if (!problem_already_exists)
        new ProblemInvalidData(opplan->getOperation(), msg, "operation",
                               Date::infinitePast, Date::infiniteFuture);
    }
    // Pick up the earliest date we can reply back
    data.state->a_date = opplan->getEnd();
    data.state->a_qty = 0.0;
    opplan->setQuantity(0.0);
    return false;
  }

  // Check the leadtime constraints
  if (data.constrainedPlanning && !checkOperationLeadTime(opplan, data, true))
    // This operationplan is a wreck. It is impossible to make it meet the
    // leadtime constraints
    return false;

  // Set a bookmark in the command list.
  auto topcommand = data.getCommandManager()->setBookmark();

  // Temporary variables
  DateRange orig_dates = opplan->getDates();
  bool okay = true;
  Date a_date;
  double a_qty;
  Date orig_q_date = data.state->q_date;
  Date orig_q_date_max = data.state->q_date_max;
  double orig_opplan_qty = opplan->getQuantity();
  double q_qty_Flow;
  Date q_date_Flow;
  bool incomplete;
  bool tmp_forceLate = data.state->forceLate;
  bool isPlannedEarly;
  DateRange matnext;
  bool flow_at_start = true;

  // Loop till everything is okay. During this loop the quantity and date of the
  // operationplan can be updated, but it cannot be split or deleted.
  data.state->forceLate = false;
  unsigned short counter = 0;
  do {
    data.state->has_bucketized_resources = false;
    if (isCapacityConstrained() && checkCapacity) {
      // Verify the capacity. This can move the operationplan early or late.
      checkOperationCapacity(opplan, data);
      while (data.state->a_date <= orig_q_date_max &&
             data.state->a_qty == 0.0 &&
             opplan->getEnd() < Date::infiniteFuture) {
        // Try a new date, until we are above the acceptable date
        Date prev = data.state->a_date;
        opplan->setOperationPlanParameters(orig_opplan_qty, Date::infinitePast,
                                           data.state->a_date, true, true,
                                           false);
        checkOperationCapacity(opplan, data);
        if (data.state->a_date <= prev && data.state->a_qty == 0.0) {
          // Tough luck
          opplan->setOperationPlanParameters(orig_opplan_qty, orig_q_date_max,
                                             Date::infinitePast, true, true,
                                             false);
          data.state->forceLate = true;
          checkOperationCapacity(opplan, data);
        }
      }
      if (data.state->a_qty == 0.0)
        // Return false if no capacity is available
        return false;
    }
    Date opplan_strt_capacity = data.state->has_bucketized_resources
                                    ? opplan->getStart()
                                    : Date::infinitePast;

    data.state->q_qty = opplan->getQuantity();
    data.state->q_date = opplan->getEnd();
    a_qty = opplan->getQuantity();
    a_date = data.state->q_date;
    incomplete = false;
    matnext.setStartAndEnd(Date::infinitePast, Date::infiniteFuture);

    // Loop through all dependencies, if needed
    if (a_qty && !opplan->getOperation()->getDependencies().empty())
      checkDependencies(opplan, data, incomplete, a_qty, matnext);
    data.state->blockedOpplan = nullptr;
    data.state->dependency = nullptr;

    // Loop through all flowplans, if needed
    // @todo need some kind of coordination run here!!! see test
    // alternate_flow_1
    if (getPropagate() && a_qty) {
      for (auto g = opplan->beginFlowPlans(); g != opplan->endFlowPlans();
           ++g) {
        if (g->getFlow()->isConsumer() && !g->isFollowingBatch() &&
            ((g->getBuffer()->getItem() &&
              !g->getBuffer()->getItem()->hasType<ItemMTO>()) ||
             !g->getBuffer()->getBatch().empty())) {
          // Switch back to the main alternate if this flowplan was already //
          // @todo is this really required? If yes, in this place? planned on an
          // alternate
          if (g->getFlow()->getAlternate())
            g->setFlow(g->getFlow()->getAlternate());

          // Trigger the flow solver, which will call the buffer solver
          data.state->q_flowplan = &*g;
          q_qty_Flow = -data.state->q_flowplan
                            ->getQuantity();  // @todo flow quantity can change
                                              // when using alternate flows ->
                                              // move to flow solver!
          q_date_Flow = data.state->q_flowplan->getDate();
          g->getFlow()->solve(*this, &data);

          // Validate the answered quantity
          if (data.state->a_qty < q_qty_Flow) {
            // Update the opplan, which is required to (1) update the flowplans
            // and to (2) take care of lot sizing constraints of this operation.
            g->setQuantity(-data.state->a_qty, true);
            a_qty = opplan->getQuantity();
            incomplete = true;

            // Validate the answered date of the most limiting flowplan.
            // Note that the delay variable only reflects the delay due to
            // material constraints. If the operationplan is moved early or late
            // for capacity constraints, this is not included.
            if (data.state->a_date < Date::infiniteFuture) {
              OperationPlanState at =
                  g->getFlow()->hasType<FlowEnd>()
                      ? opplan->setOperationPlanParameters(
                            orig_opplan_qty, Date::infinitePast,
                            g->computeFlowToOperationDate(data.state->a_date),
                            false, false, false)
                      : opplan->setOperationPlanParameters(
                            orig_opplan_qty,
                            g->computeFlowToOperationDate(data.state->a_date),
                            Date::infinitePast, false, false, false);
              if (at.end < matnext.getEnd()) {
                matnext = DateRange(at.start, at.end);
                flow_at_start = !g->getFlow()->hasType<FlowEnd>();
              }
            } else if (data.state->a_qty > ROUNDING_ERROR) {
              // Quantity replied was less the minimum size of the operation,
              // but the producing operation didn't give a next-date.
              matnext.setEnd(orig_q_date + getMinimumDelay());
            }

            // Jump out of the loop if the answered quantity is 0.
            if (a_qty <= ROUNDING_ERROR) {
              // @TODO disabled To speed up the planning the constraining flow
              // is moved up a position in the list of flows. It'll thus be
              // checked earlier when this operation is asked again
              // const_cast<Operation::flowlist&>(g->getFlow()->getOperation()->getFlows()).promote(g->getFlow());
              // There is absolutely no need to check other flowplans if the
              // operationplan quantity is already at 0.
              break;
            }
          } else if (data.state->a_qty > q_qty_Flow + ROUNDING_ERROR)
            // Never answer more than asked.
            // The actual operationplan could be bigger because of lot sizing.
            a_qty = -q_qty_Flow /
                    g->getFlow()
                        ->getQuantity();  // TODO include fixed quantity here
        }
      }
    }

    isPlannedEarly = opplan->getEnd() < orig_dates.getEnd();

    if (matnext.getEnd() != Date::infiniteFuture && a_qty <= ROUNDING_ERROR &&
        matnext.getEnd() <= orig_q_date_max && matnext.getEnd() > orig_q_date) {
      // The reply is 0, but the next-date is still less than the maximum
      // ask date. In this case we will violate the post-operation -soft-
      // constraint.
      if (matnext.getEnd() < orig_q_date + getMinimumDelay()) {
        matnext.setEnd(orig_q_date + getMinimumDelay());
        if (matnext.getEnd() > orig_q_date_max) matnext.setEnd(orig_q_date_max);
      }
      data.state->q_date = matnext.getEnd();
      orig_q_date = data.state->q_date;
      data.state->q_qty = orig_opplan_qty;
      data.state->a_date = Date::infiniteFuture;
      data.state->a_qty = data.state->q_qty;
      opplan->setOperationPlanParameters(orig_opplan_qty, Date::infinitePast,
                                         matnext.getEnd(), true, true, false);
      okay = false;
      // Pop actions from the command "stack" in the command list
      data.getCommandManager()->rollback(topcommand);
      // Echo a message
      if (getLogLevel() > 1) logger << indentlevel << "  Retrying new date.\n";
    } else if (opplan_strt_capacity &&
               opplan_strt_capacity != opplan->getStart() &&
               opplan->getQuantity() > ROUNDING_ERROR && data.state->a_qty)
      // The start date has moved and bucketized resources need to be rechecked
      okay = false;
    else
      okay = true;
    if (!okay && ++counter >= 20) {
      a_qty = 0.0;
      matnext.setEnd(orig_q_date_max + data.getSolver()->getMinimumDelay());
      if (data.getSolver()->getLogLevel() > 1)
        logger << indentlevel << "Quitting operation checking loop\n";
      break;
    }
  } while (!okay);  // Repeat the loop if the operation was moved and the
                    // feasibility needs to be rechecked.

  if (a_qty <= ROUNDING_ERROR && !data.state->forceLate && isPlannedEarly &&
      matnext.getStart() != Date::infiniteFuture &&
      matnext.getStart() != Date::infinitePast &&
      (data.constrainedPlanning && isCapacityConstrained())) {
    // The operationplan was moved early (because of a resource constraint)
    // and we can't properly trust the reply date in such cases...
    // We want to enforce rechecking the next date.
    if (getLogLevel() > 1) logger << indentlevel << "  Recheck capacity\n";

    // Move the operationplan to the next date where the material is feasible
    if (flow_at_start)
      opplan->setOperationPlanParameters(
          orig_opplan_qty,
          matnext.getStart() > orig_dates.getStart() ? matnext.getStart()
                                                     : orig_dates.getStart(),
          Date::infinitePast, true, true, false);
    else
      opplan->setOperationPlanParameters(orig_opplan_qty, Date::infinitePast,
                                         matnext.getEnd() > orig_dates.getEnd()
                                             ? matnext.getEnd()
                                             : orig_dates.getEnd(),
                                         true, true, false);

    // Move the operationplan to a later date where it is feasible.
    data.state->forceLate = true;
    checkOperationCapacity(opplan, data);

    // Reply isn't late enough
    if (opplan->getEnd() <= orig_q_date_max) {
      opplan->setOperationPlanParameters(orig_opplan_qty, Date::infinitePast,
                                         orig_q_date_max);
      data.state->forceLate = true;
      checkOperationCapacity(opplan, data);
    }

    // Reply of this function
    a_qty = 0.0;
    matnext.setEnd(opplan->getEnd());
  }

  // Compute the final reply
  data.state->a_date = incomplete ? matnext.getEnd() : Date::infiniteFuture;
  data.state->a_qty = a_qty;
  data.state->forceLate = tmp_forceLate;
  if (a_qty > ROUNDING_ERROR)
    return true;
  else {
    // Undo the plan
    data.getCommandManager()->rollback(topcommand);
    return false;
  }
}

bool SolverCreate::checkOperationLeadTime(OperationPlan* opplan,
                                          SolverCreate::SolverData& data,
                                          bool extra) {
  // No lead time constraints
  if (!data.constrainedPlanning ||
      !isLeadTimeConstrained(opplan->getOperation()))
    return true;

  // Compute offset from the current date: A fence problem uses the release
  // fence window, while a leadtimeconstrained constraint has an offset of 0.
  // If both constraints apply, we need the bigger of the two (since it is the
  // most constraining date.
  Date threshold = Plan::instance().getCurrent();
  if (isLeadTimeConstrained(opplan->getOperation()))
    threshold = opplan->getOperation()->getFence(opplan);

  // Compare the operation plan start with the threshold date
  if (opplan->getStart() >= threshold)
    // There is no problem
    return true;

  // Compute how much we can supply in the current timeframe.
  // In other words, we try to resize the operation quantity to fit the
  // available timeframe: used for e.g. time-per operations
  // Note that we allow the complete post-operation time to be eaten
  OperationPlanState original(opplan);

  // This operation doesn't fit at all within the constrained window.
  data.state->a_qty = 0.0;
  // Resize to the minimum quantity
  double min_q = data.state->q_qty_min;
  if (min_q < opplan->getOperation()->getSizeMinimum())
    min_q = opplan->getOperation()->getSizeMinimum();
  if (opplan->getQuantity() + ROUNDING_ERROR < min_q)
    opplan->setQuantity(min_q, false);

  // The earliest date may not be achieved on the current resource if the
  // operation loads a pool:
  // - There can be more efficient resources in the pool
  // - Other resources in the pool can have a lower setup time
  LoadPlan* setuploadplan = nullptr;
  if (extra && data.state->keepAssignments != opplan) {
    // First, switch all pools to their most efficient resource
    for (auto ldplan = opplan->beginLoadPlans();
         ldplan != opplan->endLoadPlans(); ++ldplan) {
      if (ldplan->getQuantity() < 0.0 && ldplan->getLoad() &&
          ldplan->getLoad()->getResource()->isGroup()) {
        auto most_efficient = ldplan->getLoad()->findPreferredResource(
            opplan->getStart(), opplan);
        if (!ldplan->getLoad()->getSetup().empty())
          setuploadplan = &*ldplan;
        else if (ldplan->getResource() != most_efficient)
          ldplan->setResource(most_efficient, false, false);
      }
    }
  }
  if (setuploadplan) {
    // Try out resources in the pool if setups are involved
    Date earliest_date = Date::infiniteFuture;

    // Loop over all qualified possible resources
    stack<Resource*> res_stack;
    res_stack.push(setuploadplan->getLoad()->getResource());
    while (!res_stack.empty()) {
      // Pick next resource
      Resource* res = res_stack.top();
      res_stack.pop();

      // If it's an aggregate, push it's members on the stack
      if (res->isGroup()) {
        for (auto x = res->getMembers(); x != Resource::end(); ++x)
          res_stack.push(&*x);
        continue;
      }

      // Check if the resource has the right skill
      if (setuploadplan->getLoad()->getSkill() &&
          !res->hasSkill(setuploadplan->getLoad()->getSkill(), threshold,
                         threshold))
        continue;

      // Efficiency must be higher than 0
      auto my_eff = res->getEfficiencyCalendar()
                        ? res->getEfficiencyCalendar()->getValue(original.start)
                        : res->getEfficiency();
      if (my_eff <= 0.0) continue;

      // Try this resource
      if (setuploadplan->getResource() != res) {
        opplan->clearSetupEvent();
        opplan->setStartEndAndQuantity(original.start, original.end,
                                       original.quantity);
        setuploadplan->setResource(res, false, false);
      }
      opplan->setStart(threshold, false, false);
      if (opplan->getEnd() < earliest_date) earliest_date = opplan->getEnd();
    }

    // Pick up the earliest date of all qualified resources
    data.state->a_date = earliest_date;
  } else {
    // No setup is involved
    opplan->setStart(threshold);
    data.state->a_date = opplan->getEnd();
  }

  // Log the constraint
  if (data.logConstraints && data.constraints)
    data.constraints->push(ProblemBeforeCurrent::metadata,
                           opplan->getOperation(), original.start,
                           opplan->getStart());

  // Set the quantity to 0 to make sure the buffer doesn't see any supply
  opplan->setQuantity(0.0);

  // Deny creation of the operationplan
  return false;
}

void SolverCreate::solve(const Operation* oper, void* v) {
  auto* data = static_cast<SolverData*>(v);
  data->state->a_date = Date::infiniteFuture;

  // Call the user exit
  if (userexit_operation)
    userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  // Message
  if (getLogLevel() > 1)
    logger << ++indentlevel << "Operation '" << oper
           << "' is asked: " << data->state->q_qty << "  "
           << data->state->q_date << '\n';

  auto asked_date = data->state->q_date;
  auto asked_qty = data->state->q_qty;
  auto original_q_qty = asked_qty;
  bool repeat;
  auto ask_early = oper->getPostTime();
  bool hard_posttime = false;
  if (ask_early && data->state->curOwnerOpplan &&
      data->state->curOwnerOpplan->getOperation()
          ->hasType<OperationRouting>()) {
    auto rtg = static_cast<OperationRouting*>(
        data->state->curOwnerOpplan->getOperation());
    hard_posttime = rtg->getHardPostTime();
    if (hard_posttime) {
      // Subtract the post-operation time as hard constraint
      asked_date -= ask_early;
      data->state->q_date -= ask_early;
    }
  }
  auto delta = data->getSolver()->getMinimumDelay();
  if (!delta) delta = Duration(3600L);
  do {
    repeat = false;
    auto bm = data->getCommandManager()->setBookmark();
    data->push(asked_qty, asked_date, true);
    // Subtract the post-operation time as soft constraint
    if (!hard_posttime) data->state->q_date -= ask_early;
    auto tmpopplan = createOperation(oper, data, true, true);
    data->pop(true);
    if (!data->state->a_qty) {
      bm->rollback();
      if (data->state->curOwnerOpplan &&
          data->state->curOwnerOpplan->getOperation()
              ->hasType<OperationRouting>() &&
          tmpopplan) {
        // This routing sub-operation opplan is about to be recreated
        tmpopplan->setOwner(nullptr);
        delete tmpopplan;
      }
      if (data->state->a_date <= asked_date && ask_early > Duration(0L) &&
          !hard_posttime) {
        repeat = true;
        if (ask_early > delta)
          ask_early -= delta;
        else
          ask_early = Duration(0L);
        if (getLogLevel() > 1)
          logger << indentlevel << "Operation '" << oper
                 << "' repeats ask with smaller post-operation delay: "
                 << asked_qty << "  " << (asked_date - ask_early) << '\n';
      }
    }
  } while (repeat);
  if (!oper->getOwner() || !oper->getOwner()->hasType<OperationRouting>()) {
    data->hitMaxSize = data->state->a_qty == oper->getSizeMaximum();
    if (data->hitMaxSize &&
        data->state->a_qty < original_q_qty - ROUNDING_ERROR)
      data->accept_partial_reply = true;
  }

  // Message
  if (getLogLevel() > 1) {
    logger << indentlevel-- << "Operation '" << oper
           << "' answers: " << data->state->a_qty;
    if (!data->state->a_qty) logger << "  " << data->state->a_date;
    logger << '\n';
  }
}

OperationPlan* SolverCreate::createOperation(const Operation* oper,
                                             SolverCreate::SolverData* data,
                                             bool propagate, bool start_or_end,
                                             double* qty_per, double* qty_fixed,
                                             bool use_offset) {
  OperationPlan* z = nullptr;

  // Find the flow for the quantity-per. This can throw an exception if no
  // valid flow can be found.
  Date orig_q_date = data->state->q_date;
  double flow_qty_per = 0.0;
  double flow_qty_fixed = 0.0;
  bool transferbatch_flow = false;
  Flow* producing_flow = nullptr;
  if (data->state->dependency) {
    flow_qty_per = 1.0;
  } else if (data->state->curBuffer) {
    producing_flow =
        oper->findFlow(data->state->curBuffer, data->state->q_date);
    if (producing_flow && producing_flow->isProducer()) {
      flow_qty_per += producing_flow->getQuantity();
      flow_qty_fixed += producing_flow->getQuantityFixed();
      producing_flow = producing_flow;
      if (producing_flow->hasType<FlowTransferBatch>())
        transferbatch_flow = true;
    } else {
      // The producing operation doesn't have a valid flow into the current
      // buffer. Either it is missing or it is producing a negative quantity.
      data->state->a_qty = 0.0;
      data->state->a_date = Date::infiniteFuture;
      string problemtext = string("Invalid producing operation '") +
                           oper->getName() + "' for buffer '" +
                           data->state->curBuffer->getName() + "'";
      auto dmd = data->constraints;
      if (dmd) {
        auto j = dmd->begin();
        while (j != dmd->end()) {
          if (j->hasType<ProblemInvalidData>() &&
              j->getDescription() == problemtext)
            break;
          ++j;
        }
        if (j == dmd->end()) {
          dmd->push(new ProblemInvalidData(data->state->curBuffer, problemtext,
                                           "material", Date::infinitePast,
                                           Date::infiniteFuture, false));
        }
      }
      if (getLogLevel() > 1) {
        logger << indentlevel << problemtext << '\n';
        logger << indentlevel << "Operation '" << oper
               << "' answers: " << data->state->a_qty;
        if (!data->state->a_qty) logger << "  " << data->state->a_date;
        logger << '\n';
      }
      if (qty_per) *qty_per = flow_qty_per;
      if (qty_fixed) *qty_fixed = flow_qty_fixed;
      return nullptr;
    }
  } else
    // Using this operation as a delivery operation for a demand
    flow_qty_per = 1.0;

  if (qty_per) *qty_per = flow_qty_per;
  if (qty_fixed) *qty_fixed = flow_qty_fixed;

  // Split operations are unavoidable in this case
  if (flow_qty_fixed && !flow_qty_per) data->accept_partial_reply = true;

  // If transferbatch, then recompute the operation quantity and date here
  if (transferbatch_flow) {
    // Find maximum shortage in the buffer, and the date on which it happens
    Date max_short_date = Date::infiniteFuture;
    double max_short_qty = -ROUNDING_ERROR;
    for (auto flpln = data->state->curBuffer->getFlowPlans().rbegin();
         flpln != data->state->curBuffer->getFlowPlans().end(); --flpln) {
      if (flpln->isLastOnDate() && flpln->getOnhand() < max_short_qty) {
        max_short_date = flpln->getDate();
        max_short_qty = flpln->getOnhand();
      }
      if (flpln->getDate() < data->state->q_date) break;
    }

    // Create an operationplan to solve for the maximum shortage at its date
    double opplan_qty;
    if (!flow_qty_per || -max_short_qty < flow_qty_fixed + ROUNDING_ERROR)
      // Minimum size if sufficient
      opplan_qty = 0.001;
    else
      opplan_qty = (-max_short_qty - flow_qty_fixed) / flow_qty_per;
    if (data->state->curOwnerOpplan) {
      // There is already an owner and thus also an owner command
      assert(!data->state->curDemand);
      z = oper->createOperationPlan(
          opplan_qty, Date::infinitePast, max_short_date, data->state->curBatch,
          data->state->curDemand, data->state->curOwnerOpplan, true, false);
    } else {
      // There is no owner operationplan yet. We need a new command.
      auto* a = new CommandCreateOperationPlan(
          oper, opplan_qty, Date::infinitePast, max_short_date,
          data->state->curDemand, data->state->curBatch,
          data->state->curOwnerOpplan, true, false);
      data->state->curDemand = nullptr;
      z = a->getOperationPlan();
      data->getCommandManager()->add(a);
    }

    // Move the newly created operationplan early if shortages are left
    while (true) {
      bool repeat = false;
      Date shortage_d;
      double shortage_q = 0.0;
      double z_produced = 0.0;
      for (auto& flpln : data->state->curBuffer->getFlowPlans()) {
        if (flpln.isLastOnDate() && flpln.getOnhand() < -ROUNDING_ERROR &&
            !shortage_q) {
          // Loop mode 1: Scan for the start of a shortage period
          shortage_q = flpln.getOnhand();
          shortage_d = flpln.getDate();
        } else if (shortage_q && flpln.getOperationPlan() == z) {
          // Loop mode 2: See how many transfer batches are required to fill the
          // shortage
          z_produced += flpln.getQuantity();
          if (shortage_q + z_produced < -ROUNDING_ERROR)
            // Not enough yet
            continue;

          // Now we need to move the operationplan such that the current
          // transfer batch aligns with the shortage date.
          Duration delta;
          oper->calculateOperationTime(z, shortage_d, flpln.getDate(), &delta);
          DateRange newdate =
              oper->calculateOperationTime(z, z->getStart(), delta, false);
          z->setStart(newdate.getStart(), false, false);
          repeat = true;
          break;
        }
      }
      if (!repeat) break;
    };
  }

  // Find the current list of constraints
  Problem* topConstraint =
      data->constraints ? data->constraints->top() : nullptr;

  // Subtract offset between operationplan end and flowplan date
  if (use_offset && producing_flow && producing_flow->getOffset()) {
    if (getLogLevel() > 1)
      logger << indentlevel << "  Adjusting requirement date for offset from "
             << data->state->q_date;
    data->state->q_date = data->state->q_date_max =
        producing_flow->computeFlowToOperationDate(z, data->state->q_date);
    if (getLogLevel() > 1) logger << " to " << data->state->q_date << '\n';
  }

  // Create the operation plan.
  if (!z) {
    double opplan_qty;
    if (!flow_qty_per || data->state->q_qty < flow_qty_fixed + ROUNDING_ERROR)
      // Minimum size if sufficient
      opplan_qty = 0.001;
    else
      opplan_qty = (data->state->q_qty - flow_qty_fixed) / flow_qty_per;
    if (data->state->curOwnerOpplan) {
      // There is already an owner and thus also an owner command
      assert(!data->state->curDemand);
      if (start_or_end)
        z = oper->createOperationPlan(
            opplan_qty, Date::infinitePast, data->state->q_date,
            data->state->curBatch, data->state->curDemand,
            data->state->curOwnerOpplan, true, false);
      else
        z = oper->createOperationPlan(opplan_qty, data->state->q_date,
                                      Date::infinitePast, data->state->curBatch,
                                      data->state->curDemand,
                                      data->state->curOwnerOpplan, true, false);
    } else {
      // There is no owner operationplan yet. We need a new command.
      CommandCreateOperationPlan* a;
      if (start_or_end)
        a = new CommandCreateOperationPlan(
            oper, opplan_qty, Date::infinitePast, data->state->q_date,
            data->state->curDemand, data->state->curBatch,
            data->state->curOwnerOpplan, true, false);
      else
        a = new CommandCreateOperationPlan(
            oper, opplan_qty, data->state->q_date, Date::infinitePast,
            data->state->curDemand, data->state->curBatch,
            data->state->curOwnerOpplan, true, false);
      data->state->curDemand = nullptr;
      z = a->getOperationPlan();
      data->getCommandManager()->add(a);
    }
  }
  if (data->state->blockedOpplan) {
    new OperationPlanDependency(z, data->state->blockedOpplan,
                                data->state->dependency);
    data->state->blockedOpplan = nullptr;
    data->state->dependency = nullptr;
  }
  assert(z);
  double orig_q_qty = z->getQuantity();

  if (!propagate) return z;

  // Adjust the min quantity we expect the reply to cover
  double orig_q_qty_min = data->state->q_qty_min;
  if (!flow_qty_per || data->state->q_qty_min < flow_qty_fixed + ROUNDING_ERROR)
    data->state->q_qty_min = 1.0;
  else
    data->state->q_qty_min =
        (data->state->q_qty_min - flow_qty_fixed) / flow_qty_per;

  // Check the constraints
  checkOperation(z, *data);
  if (!propagate) return z;
  if (!data->state->forceAccept) data->state->q_qty_min = orig_q_qty_min;

  // Multiply the operation reply with the flow quantity to get a final reply
  if (data->state->curBuffer && data->state->a_qty)
    data->state->a_qty = data->state->a_qty * flow_qty_per + flow_qty_fixed;

  // Add offset between operationplan end and flowplan date
  if (use_offset && data->state->a_date != Date::infiniteFuture &&
      !data->state->a_qty && producing_flow && producing_flow->getOffset()) {
    if (getLogLevel() > 1)
      logger << indentlevel << "  Adjusting answer date for offset from "
             << data->state->a_date;
    data->state->a_date =
        producing_flow->computeOperationToFlowDate(z, data->state->a_date);
    if (getLogLevel() > 1) logger << " to " << data->state->a_date << '\n';
  }

  // Ignore any constraints if we get a complete reply.
  // Sometimes constraints are flagged due to a pre- or post-operation time.
  // Such constraints ultimately don't result in lateness and can be ignored.
  if (data->state->a_qty >= orig_q_qty - ROUNDING_ERROR && data->constraints)
    data->constraints->pop(topConstraint);

  // Increment the cost
  if (data->state->a_qty > 0.0) {
    auto tmp = z->getQuantity() * oper->getCost();
    data->state->a_cost += tmp;
    if (data->logcosts && data->incostevaluation)
      logger << indentlevel << "     + cost on operation '" << oper
             << "': " << tmp << '\n';
  }

  // Verify the reply
  if (data->state->a_qty == 0 && data->state->a_date <= orig_q_date) {
    if (getLogLevel() > 1)
      logger << indentlevel << "Applying lazy delay " << getLazyDelay() << '\n';
    data->state->a_date = orig_q_date + getLazyDelay();
  }
  assert(data->state->a_qty >= 0);

  // Optionally add a penalty depending on the amount of quantity already
  // planned on this operation. This is useful to create a plan where the
  // loading is divided equally over the different available resources, when the
  // search mode MINCOSTPENALTY is used.
  if (getRotateResources())
    for (auto rr = oper->getOperationPlans(); rr != OperationPlan::end(); ++rr)
      data->state->a_penalty += rr->getQuantity();

  return z;
}

void SolverCreate::solve(const OperationItemSupplier* o, void* v) {
  auto* data = static_cast<SolverData*>(v);
  if (o->getPriority() && o->getBuffer()) {
    bool all_po = true;
    if (o->getOwner() &&
        o->getOwner()->hasType<OperationSplit, OperationAlternate>()) {
      for (auto& alt : o->getOwner()->getSubOperations()) {
        if (alt->getOperation()->getPriority() &&
            !alt->getOperation()->hasType<OperationItemSupplier>()) {
          all_po = false;
          break;
        }
      }
    }
    if (all_po) data->purchase_buffers.insert(o->getBuffer());
  }

  // Manage global replenishment
  Item* item = o->getBuffer()->getItem();
  if (item && item->getBoolProperty("global_purchase", false) &&
      data->constrainedPlanning &&
      data->state->q_date <=
          item->findEarliestPurchaseOrder(data->state->curBatch)) {
    double total_onhand = 0;
    double total_ss = 0;

    Item::bufferIterator iter(item);
    // iterate over all the buffers to compute the sum on hand and the sum ssl
    while (Buffer* buffer = iter.next()) {
      double tmp = buffer->getOnHand(data->state->q_date);
      if (tmp > 0) total_onhand += tmp;
      Calendar* ss_calendar = buffer->getMinimumCalendar();
      if (ss_calendar) {
        CalendarBucket* calendarBucket =
            ss_calendar->findBucket(data->state->q_date, true);
        if (calendarBucket) {
          total_ss += calendarBucket->getValue();
        }
      } else {
        total_ss += buffer->getMinimum();
      }
    }
    if (total_ss + ROUNDING_ERROR < total_onhand) {
      data->state->a_qty = 0;
      data->state->a_date = Date::infiniteFuture;
      if (getLogLevel() > 1) {
        logger << ++indentlevel << "Operation '" << o
               << "' is asked: " << data->state->q_qty << "  "
               << data->state->q_date << '\n';
        logger << indentlevel-- << "Purchasing operation '" << o
               << "' replies 0. Requested qty/date: " << data->state->q_qty
               << "/" << data->state->q_date
               << " Total OH/SS : " << total_onhand << "/" << total_ss << '\n';
      }
      return;
    }
  }

  solve(static_cast<const Operation*>(o), v);
}

// No need to take post- and pre-operation times into account
void SolverCreate::solve(const OperationRouting* oper, void* v) {
  auto* data = static_cast<SolverData*>(v);
  auto useDependencies = oper->useDependencies();

  // Call the user exit
  if (userexit_operation)
    userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  // Message
  if (getLogLevel() > 1) {
    logger << ++indentlevel << "Routing operation '" << oper
           << "' is asked: " << data->state->q_qty << "  "
           << data->state->q_date;
    if (useDependencies) logger << " using step dependencies";
    logger << '\n';
  }

  // Find the total quantity to flow into the buffer.
  // Multiple suboperations can all produce into the buffer.
  double flow_qty_per = 0.0;
  double flow_qty_fixed = 0.0;
  Flow* offset_flow = nullptr;
  if (data->state->curBuffer) {
    Flow* f = oper->findFlow(data->state->curBuffer, data->state->q_date);
    if (f && f->isProducer()) {
      // Flow on routing operation
      flow_qty_per += f->getQuantity();
      flow_qty_fixed += f->getQuantityFixed();
      if (f->getOffset() &&
          (!offset_flow || offset_flow->getOffset() < f->getOffset()))
        offset_flow = &*f;
      logger << "Deprecation warning: routing operation '" << oper
             << "' shouldn't produce material\n";
    }
    for (auto& e : oper->getSubOperations()) {
      f = e->getOperation()->findFlow(data->state->curBuffer,
                                      data->state->q_date);
      if (f && f->isProducer()) {
        // Flow on routing steps
        flow_qty_per += f->getQuantity();
        flow_qty_fixed += f->getQuantityFixed();
        if (f->getOffset() &&
            (!offset_flow || offset_flow->getOffset() < f->getOffset()))
          offset_flow = &*f;
      }
    }
    if (!flow_qty_fixed && !flow_qty_per) {
      string msg =
          "Operation doesn't produce into " + data->state->curBuffer->getName();
      if (data->logConstraints && data->constraints) {
        auto j = data->constraints->begin();
        while (j != data->constraints->end()) {
          if (j->hasType<ProblemInvalidData>() && j->getDescription() == msg)
            break;
          ++j;
        }
        if (j == data->constraints->end())
          data->constraints->push(new ProblemInvalidData(
              const_cast<OperationRouting*>(oper), msg, "operation",
              Plan::instance().getCurrent(), Date::infiniteFuture, false));
      }
      bool problem_already_exists = false;
      auto probiter = Problem::iterator(oper);
      while (Problem* prob = probiter.next()) {
        if (typeid(*prob) == typeid(ProblemInvalidData) &&
            prob->getDescription() == msg) {
          problem_already_exists = true;
          break;
        }
      }
      if (!problem_already_exists)
        new ProblemInvalidData(const_cast<OperationRouting*>(oper), msg,
                               "operation", Date::infinitePast,
                               Date::infiniteFuture);
    }
  } else
    // Using the routing as the delivery operation of a demand
    flow_qty_per = 1.0;

  // Because we already took care of it... @todo not correct if the suboperation
  // is again a owning operation
  data->state->curBuffer = nullptr;
  double a_qty;
  if (!flow_qty_per || data->state->q_qty < flow_qty_fixed + ROUNDING_ERROR)
    a_qty = 0.001;
  else
    a_qty = (data->state->q_qty - flow_qty_fixed) / flow_qty_per;

  // Split operations are unavoidable in this case
  if (flow_qty_fixed && !flow_qty_per) data->accept_partial_reply = true;

  // Create the top operationplan
  auto* a = new CommandCreateOperationPlan(
      oper, a_qty, Date::infinitePast, data->state->q_date,
      data->state->curDemand, data->state->curBatch,
      data->state->curOwnerOpplan, false, false);
  data->state->curDemand = nullptr;

  // Subtract offset between operationplan end and flowplan date
  if (offset_flow) {
    if (getLogLevel() > 1)
      logger << indentlevel << "  Adjusting requirement date from "
             << data->state->q_date;
    data->state->q_date = offset_flow->computeFlowToOperationDate(
        a->getOperationPlan(), data->state->q_date);
    a->getOperationPlan()->setEnd(data->state->q_date);
    if (getLogLevel() > 1) logger << " to " << data->state->q_date << '\n';
  }

  // Quantity can be changed because of size constraints on the top operation
  a_qty = a->getOperationPlan()->getQuantity();

  // Make sure the subopplans know their owner & store the previous value
  OperationPlan* prev_owner_opplan = data->state->curOwnerOpplan;
  data->state->curOwnerOpplan = a->getOperationPlan();

  // Reset the max date on the state.
  data->state->q_date_max = data->state->q_date;
  Date max_Date;
  Duration delay;
  Date top_q_date(data->state->q_date);
  Date q_date;

  try {
    if (useDependencies) {
      if (data->dependency_list.empty())
        // Starting a new dependency list.
        data->populateDependencies(oper);

      // Plan all final steps (i.e. steps without blockedby dependency)
      // It will recursively plan into the preceding steps.
      for (auto& e : oper->getSubOperations()) {
        bool isblocked = false;
        for (auto& dpd : e->getOperation()->getDependencies()) {
          if (dpd->getBlockedBy() == e->getOperation()) {
            isblocked = true;
            break;
          }
        }
        if (isblocked)
          // Not a final step
          continue;

        // Check if this is the last time it appears in the dependency list
        data->state->q_date = top_q_date;
        auto occurences = data->dependency_list.find(e->getOperation());
        if (occurences != data->dependency_list.end()) {
          if (occurences->second.first > 1) {
            // Not ready to explore this dependency yet.
            // We just record the requirement date.
            --occurences->second.first;
            if (getLogLevel() > 1) {
              logger << indentlevel << "  Delay following dependency '"
                     << e->getOperation();
              if (occurences->second.second > data->state->q_date)
                logger << "' - setting requirement date to "
                       << data->state->q_date;
              logger << '\n';
            }
            if (occurences->second.second > data->state->q_date)
              occurences->second.second = data->state->q_date;
            continue;
          } else {
            // OK to to explore this dependency
            if (occurences->second.second < data->state->q_date) {
              if (getLogLevel() > 1) {
                logger << indentlevel
                       << "  Dependency updates requirement date to "
                       << occurences->second.second << '\n';
              }
              data->state->q_date = occurences->second.second;
            }
            data->dependency_list.erase(occurences);
          }
        }

        data->state->q_qty = a_qty;
        data->state->curOwnerOpplan = a->getOperationPlan();
        Buffer* tmpBuf = data->state->curBuffer;
        q_date = data->state->q_date;
        e->getOperation()->solve(*this, v);
        a_qty = data->state->a_qty;
        data->state->curBuffer = tmpBuf;
        if (a_qty <= 0.0) {
          break;
        }
      }

      // Loop through the top level dependencies
      if (data->state->a_qty > 0.0 && !oper->getDependencies().empty()) {
        bool tmp1 = false;
        double tmp2;
        DateRange tmp3;
        checkDependencies(data->state->curOwnerOpplan, *data, tmp1, tmp2, tmp3);
      }
    } else {
      // Loop through the steps in sequence
      for (auto e = oper->getSubOperations().rbegin();
           e != oper->getSubOperations().rend() && a_qty > 0.0; ++e) {
        // Plan the next step
        data->state->q_qty = a_qty;
        data->state->q_date = data->state->curOwnerOpplan->getStart();
        Buffer* tmpBuf = data->state->curBuffer;
        q_date = data->state->q_date;
        (*e)->getOperation()->solve(*this, v);
        a_qty = data->state->a_qty;
        data->state->curBuffer = tmpBuf;

        // Update the top operationplan
        data->state->curOwnerOpplan->setQuantity(a_qty, true);

        // Maximum for the next date
        if (data->state->a_date != Date::infiniteFuture) {
          if (delay < data->state->a_date - q_date)
            delay = data->state->a_date - q_date;
          OperationPlanState at =
              data->state->curOwnerOpplan->setOperationPlanParameters(
                  0.01, data->state->a_date, Date::infinitePast, false, false);
          if (at.end < top_q_date + (data->state->a_date - q_date))
            // Minimum routing delay is assumed to be equal to the delay of
            // the step.
            // TODO this assumption is not really generic
            at.end = top_q_date + (data->state->a_date - q_date);
          if (at.end > max_Date) max_Date = at.end;
        }
      }

      // Check the flows and loads on the top operationplan.
      // This can happen only after the suboperations have been dealt with
      // because only now we know how long the operation lasts in total.
      // Solving for the top operationplan can resize and move the steps that
      // are in the routing!
      /* @todo moving routing opplan doesn't recheck for feasibility of
       * steps...
       */
      data->state->curOwnerOpplan->createFlowLoads();
      if (data->state->curOwnerOpplan->getQuantity() > 0.0) {
        data->state->q_qty = a_qty;
        data->state->q_date = data->state->curOwnerOpplan->getEnd();
        q_date = data->state->q_date;
        checkOperation(data->state->curOwnerOpplan, *data);
        a_qty = data->state->a_qty;
        if (a_qty == 0.0 && data->state->a_date != Date::infiniteFuture) {
          // The reply date is the combination of the reply date of all steps
          // and the reply date of the top operationplan.
          if (data->state->a_date > q_date &&
              delay < data->state->a_date - q_date)
            delay = data->state->a_date - q_date;
          if (data->state->a_date > max_Date ||
              max_Date == Date::infiniteFuture)
            max_Date = data->state->a_date;
        }
      }
      data->state->a_date = (max_Date ? max_Date : Date::infiniteFuture);

      if (data->state->a_qty > 0.0)
        data->state->a_qty = flow_qty_fixed + a_qty * flow_qty_per;
      else
        data->state->a_qty = 0.0;
    }
  } catch (...) {
    if (!prev_owner_opplan) data->getCommandManager()->add(a);
    throw;
  }

  // Add to the list (even if zero-quantity!)
  if (!prev_owner_opplan) data->getCommandManager()->add(a);

  // Increment the cost
  if (data->state->a_qty > 0.0) {
    auto tmp = data->state->curOwnerOpplan->getQuantity() * oper->getCost();
    data->state->a_cost += tmp;
    if (data->logcosts && data->incostevaluation)
      logger << indentlevel << "     + cost on operation '" << oper
             << "': " << tmp << '\n';
  }

  // Make other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be nullptr.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Add offset between operationplan end and flowplan date
  if (data->state->a_date != Date::infiniteFuture && !data->state->a_qty &&
      offset_flow) {
    if (getLogLevel() > 1)
      logger << indentlevel << "  Adjusting answer date for offset from "
             << data->state->a_date;
    data->state->a_date = offset_flow->computeOperationToFlowDate(
        a->getOperationPlan(), data->state->a_date);
    if (getLogLevel() > 1) logger << " to " << data->state->a_date << '\n';
  }

  if (data->state->a_qty == 0.0 && data->state->a_date <= top_q_date) {
    // At least one of the steps is late, but the reply date at the overall
    // routing level is not late. This situation is possible when capacity or
    // material constraints of routing steps create slack in the routing. The
    // real constrained next date becomes very hard to estimate.
    delay = getLazyDelay();
    if (getLogLevel() > 1)
      logger << indentlevel << "Applying lazy delay " << delay << " in routing"
             << '\n';
    data->state->a_date = top_q_date + delay;
  }
  data->hitMaxSize = data->state->a_qty == oper->getSizeMaximum();

  // Message
  if (getLogLevel() > 1) {
    logger << indentlevel-- << "Routing operation '" << oper
           << "' answers: " << data->state->a_qty;
    if (!data->state->a_qty) logger << "  " << data->state->a_date;
    logger << '\n';
  }
}

// No need to take post- and pre-operation times into account
// @todo This method should only be allowed to create 1 operationplan
void SolverCreate::solve(const OperationAlternate* oper, void* v) {
  {
    Operation* curAlt = nullptr;
    for (auto& altIter : oper->getSubOperations()) {
      if (altIter->getPriority() && !altIter->getEffective()) {
        if (curAlt) {
          // Multiple alternates operations are found.
          curAlt = nullptr;
          break;
        } else
          curAlt = altIter->getOperation();
      }
    }
    if (curAlt) {
      // There is only a single suboperation. This is a dummy alternate
      // operation which we can shortcut to save some CPU cycles.
      curAlt->solve(*this, v);
      return;
    }
  }

  auto* data = static_cast<SolverData*>(v);
  Date origQDate = data->state->q_date;
  double origQqty = data->state->q_qty;
  double origQtyMin = data->state->q_qty_min;
  Buffer* buf = data->state->curBuffer;
  Demand* d = data->state->curDemand;

  // Call the user exit
  if (userexit_operation)
    userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  short loglevel = getLogLevel();
  SearchMode search = oper->getSearch();

  // Message
  if (loglevel > 1)
    logger << ++indentlevel << "Alternate operation '" << oper
           << "' is asked: " << data->state->q_qty << "  "
           << data->state->q_date << '\n';

  // Make sure sub-operationplans know their owner & store the previous value
  OperationPlan* prev_owner_opplan = data->state->curOwnerOpplan;

  // Control the planning mode
  bool originalPlanningMode = data->constrainedPlanning;
  data->constrainedPlanning = true;

  // Remember the top constraint
  bool originalLogConstraints = data->logConstraints;
  Problem* topConstraint =
      data->constraints ? data->constraints->top() : nullptr;
  bool originalAcceptPartialReply = data->accept_partial_reply;

  // Try all alternates:
  // - First, all alternates that are a) fully effective and b) fit within the
  //    size-min and size-max quantity range in the order of priority.
  // - Next, the alternates beyond their effective end date and outside of
  //   quantity range.
  //   We loop through these since they can help in meeting a demand on time,
  //   but using them will also create extra inventory or delays.
  double a_qty = data->state->q_qty;
  bool effectiveOnly = true;
  Date a_date = Date::infiniteFuture;
  Date ask_date;
  SubOperation* firstAlternate = nullptr;
  Flow* firstFlow = nullptr;
  while (a_qty > 0) {
    // Evaluate all alternates
    double bestAlternateValue = DBL_MAX;
    double bestAlternateQuantity = 0;
    bool bestAcceptPartialReply = false;
    Operation* bestAlternateSelection = nullptr;
    Flow* bestFlow = nullptr;
    Date bestQDate;
    for (auto altIter = oper->getSubOperations().begin();
         altIter != oper->getSubOperations().end();) {
      // Set a bookmark in the command list.
      auto topcommand = data->getCommandManager()->setBookmark();
      bool nextalternate = true;

      // Filter out alternates that are not suitable
      bool bad = false;
      bool goodalt = (*altIter)->getEffective().within(data->state->q_date);
      if (goodalt &&
          !(*altIter)
               ->getOperation()
               ->hasType<OperationItemDistribution, OperationItemSupplier>())
        goodalt =
            data->state->q_qty >=
                (*altIter)->getOperation()->getSizeMinimum() &&
            data->state->q_qty <= (*altIter)->getOperation()->getSizeMaximum();
      if ((*altIter)->getPriority() == 0)
        bad = true;
      else if (!effectiveOnly && goodalt)
        bad = true;
      else if (effectiveOnly && !goodalt)
        bad = true;
      if (bad) {
        ++altIter;
        if (altIter == oper->getSubOperations().end() && effectiveOnly) {
          // Prepare for a second iteration over all alternates
          effectiveOnly = false;
          altIter = oper->getSubOperations().begin();
        }
        continue;
      }

      // Establish the ask date
      if (!effectiveOnly && origQDate > (*altIter)->getEffectiveEnd())
        ask_date = (*altIter)->getEffectiveEnd();
      else
        ask_date = origQDate;

      // Find the flow into the requesting buffer. It may or may not exist,
      // since the flow could already exist on the top operationplan
      data->state->q_qty_min = origQtyMin;
      Flow* sub_flow = nullptr;
      if (buf) {
        // Flow quantity on the suboperation
        sub_flow = (*altIter)->getOperation()->findFlow(buf, ask_date);
        if (sub_flow && !sub_flow->isProducer()) sub_flow = nullptr;

        // Flow quantity on the suboperations of a routing suboperation
        if ((*altIter)->getOperation()->hasType<OperationRouting>()) {
          SubOperation::iterator subiter(
              (*altIter)->getOperation()->getSubOperations());
          while (SubOperation* o = subiter.next()) {
            Flow* g = o->getOperation()->findFlow(buf, ask_date);
            if (g && g->isProducer()) sub_flow = g;
          }
        }

        if (!sub_flow ||
            (!sub_flow->getQuantityFixed() && !sub_flow->getQuantity())) {
          // The sub operation doesn't have a flow in the buffer, we're in
          // trouble... Restore the planning mode
          data->constrainedPlanning = originalPlanningMode;
          string msg = "Operation doesn't produce into " + buf->getName();
          if (data->logConstraints && data->constraints) {
            auto j = data->constraints->begin();
            while (j != data->constraints->end()) {
              if (j->hasType<ProblemInvalidData>() &&
                  j->getDescription() == msg)
                break;
              ++j;
            }
            if (j == data->constraints->end())
              data->constraints->push(new ProblemInvalidData(
                  const_cast<OperationAlternate*>(oper), msg, "operation",
                  Plan::instance().getCurrent(), Date::infiniteFuture, false));
          }
          bool problem_already_exists = false;
          auto probiter = Problem::iterator(oper);
          while (Problem* prob = probiter.next()) {
            if (typeid(*prob) == typeid(ProblemInvalidData) &&
                prob->getDescription() == msg) {
              problem_already_exists = true;
              break;
            }
          }
          if (!problem_already_exists)
            new ProblemInvalidData(const_cast<OperationAlternate*>(oper), msg,
                                   "operation", Date::infinitePast,
                                   Date::infiniteFuture);
        }
      }

      // Remember the first alternate
      if (!firstAlternate) {
        firstAlternate = *altIter;
        firstFlow = sub_flow;
      }

      // Constraint tracking
      if (*altIter != firstAlternate)
        // Only enabled on first alternate
        data->logConstraints = false;
      else {
        // Forget previous constraints if we are replanning the first alternate
        // multiple times
        if (data->constraints) data->constraints->pop(topConstraint);
        // Potentially keep track of constraints
        data->logConstraints = originalLogConstraints;
      }

      // Create the top operationplan.
      // Note that both the top- and the sub-operation can have a flow in the
      // requested buffer
      auto* a = new CommandCreateOperationPlan(
          oper, a_qty, Date::infinitePast, ask_date, d, data->state->curBatch,
          prev_owner_opplan, false, false);
      if (!prev_owner_opplan) data->getCommandManager()->add(a);

      // Create a sub operationplan
      data->state->q_date = ask_date;
      data->state->q_date_max = ask_date;
      data->state->curDemand = nullptr;
      data->state->curOwnerOpplan = a->getOperationPlan();
      data->state->curBuffer =
          nullptr;  // Because we already took care of it... @todo not correct
                    // if the suboperation is again a owning operation
      if (!sub_flow)
        data->state->q_qty = a_qty;
      else if (!sub_flow->getQuantity() ||
               a_qty < sub_flow->getQuantityFixed() + ROUNDING_ERROR)
        // The minimum operation size will suffice
        data->state->q_qty = 0.001;
      else
        data->state->q_qty =
            (a_qty - sub_flow->getQuantityFixed()) / sub_flow->getQuantity();

      // Adjust minimum quantity
      if (sub_flow) {
        if (!sub_flow->getQuantity() ||
            data->state->q_qty_min <
                sub_flow->getQuantityFixed() + ROUNDING_ERROR)
          data->state->q_qty_min = 0.001;
        else
          data->state->q_qty_min =
              (data->state->q_qty_min - sub_flow->getQuantityFixed()) /
              sub_flow->getQuantity();
      }

      // Subtract offset between operationplan end and flowplan date
      if (sub_flow && sub_flow->getOffset()) {
        if (getLogLevel() > 1)
          logger << indentlevel
                 << "  Adjusting requirement date for offset from "
                 << data->state->q_date;
        data->state->q_date = data->state->q_date_max =
            sub_flow->computeFlowToOperationDate(nullptr, data->state->q_date);
        if (getLogLevel() > 1) logger << " to " << data->state->q_date << '\n';
      }

      // Solve constraints on the sub operationplan
      double beforeCost = data->state->a_cost;
      double beforePenalty = data->state->a_penalty;
      if (origQDate < (*altIter)->getEffectiveStart()) {
        // Force a reply at the start of the effective period
        if (loglevel > 1)
          logger << indentlevel << "Operation '" << (*altIter)->getOperation()
                 << "' answers: 0 " << (*altIter)->getEffectiveStart() << '\n';
        data->state->a_qty = 0.0;
        data->state->a_date = (*altIter)->getEffectiveStart();
        if (data->logConstraints && data->constraints)
          data->constraints->push(ProblemBeforeCurrent::metadata,
                                  (*altIter)->getOperation(), origQDate,
                                  (*altIter)->getEffectiveStart());
      } else if (search == SearchMode::PRIORITY) {
        if (loglevel > 1)
          logger << indentlevel << "Alternate operation '" << oper
                 << "' tries alternate '" << (*altIter)->getOperation() << "' "
                 << '\n';
        auto tmp_askQ = data->state->q_qty;
        auto tmp_askD = data->state->q_date;
        auto tmp_accept_partial_reply = data->accept_partial_reply;
        data->accept_partial_reply = false;
        (*altIter)->getOperation()->solve(*this, v);
        if (data->state->a_qty > ROUNDING_ERROR &&
            data->state->a_qty <= tmp_askQ - ROUNDING_ERROR &&
            !data->accept_partial_reply) {
          // Reject a partial reply
          auto maxq = (*altIter)->getOperation()->getSizeMaximum();
          auto multq = (*altIter)->getOperation()->getSizeMultiple();
          auto reject = true;
          if (maxq && maxq != DBL_MAX) {
            if (multq) maxq = floor(maxq / multq) * multq;
            if (fabs(maxq - data->state->a_qty) < ROUNDING_ERROR)
              // Answer was limited by the sizemaximum. We shouldn't reject it.
              reject = false;
          }
          if (reject) {
            data->state->a_qty = 0.0;
            data->state->a_date = tmp_askD + getLazyDelay();
          }
        }
        if (tmp_accept_partial_reply) data->accept_partial_reply = true;
      } else {
        setLogLevel(0);
        data->incostevaluation = true;
        auto original_accept_partial_reply = data->accept_partial_reply;
        try {
          data->accept_partial_reply = false;
          (*altIter)->getOperation()->solve(*this, v);
        } catch (...) {
          setLogLevel(loglevel);
          // Restore the planning mode
          data->constrainedPlanning = originalPlanningMode;
          data->logConstraints = originalLogConstraints;
          data->accept_partial_reply = original_accept_partial_reply;
          throw;
        }
        setLogLevel(loglevel);
      }
      double deltaCost;
      if (data->state->a_qty > ROUNDING_ERROR)
        deltaCost = data->state->a_cost - beforeCost;
      else {
        deltaCost = 0.0;
        if (data->state->a_date > (*altIter)->getEffectiveEnd())
          data->state->a_date = Date::infiniteFuture;
      }
      double deltaPenalty = data->state->a_penalty - beforePenalty;
      if (search != SearchMode::PRIORITY) {
        data->state->a_cost = beforeCost;
        data->state->a_penalty = beforePenalty;
      }

      // Now solve for loads and flows of the top operationplan.
      // Only now we know how long that top-operation lasts in total.
      if (data->state->a_qty > ROUNDING_ERROR) {
        // Multiply the operation reply with the flow quantity to obtain the
        // reply to return
        data->state->q_qty = data->state->a_qty;
        data->state->q_date = origQDate;
        data->state->q_date_max = origQDate;
        data->state->curOwnerOpplan->createFlowLoads();
        checkOperation(data->state->curOwnerOpplan, *data);
        if (sub_flow)
          data->state->a_qty = sub_flow->getQuantityFixed() +
                               data->state->a_qty * sub_flow->getQuantity();
      }

      // Add offset between operationplan end and flowplan date
      if (data->state->a_date != Date::infiniteFuture && sub_flow &&
          sub_flow->getOffset()) {
        if (getLogLevel() > 1)
          logger << indentlevel << "  Adjusting answer date for offset from "
                 << data->state->a_date;
        data->state->a_date =
            sub_flow->computeOperationToFlowDate(nullptr, data->state->a_date);
        if (getLogLevel() > 1) logger << " to " << data->state->a_date << '\n';
      }

      // Keep the lowest of all next-date answers on the effective alternates
      if (data->state->a_date < a_date && data->state->a_date > ask_date)
        a_date = data->state->a_date;

      // Message
      if (loglevel && search != SearchMode::PRIORITY) {
        data->incostevaluation = false;
        logger << indentlevel << "Alternate operation '" << oper
               << "' evaluates alternate '" << (*altIter)->getOperation()
               << "': quantity " << data->state->a_qty << ", cost " << deltaCost
               << ", penalty " << deltaPenalty << '\n';
      }

      // Process the result
      if (search == SearchMode::PRIORITY) {
        // Undo the operationplans of this alternate
        if (data->state->a_qty < ROUNDING_ERROR)
          data->getCommandManager()->rollback(topcommand);

        // Prepare for the next loop
        a_qty -= data->state->a_qty;

        // As long as we get a positive reply we replan on this alternate
        if (data->state->a_qty > 0) nextalternate = false;

        // Are we at the end already?
        if (a_qty < ROUNDING_ERROR) {
          a_qty = 0.0;
          break;
        }
      } else {
        double val = 0.0;
        switch (search) {
          case SearchMode::MINCOST:
            val = deltaCost / data->state->a_qty;
            break;
          case SearchMode::MINPENALTY:
            val = deltaPenalty / data->state->a_qty;
            break;
          case SearchMode::MINCOSTPENALTY:
            val = (deltaCost + deltaPenalty) / data->state->a_qty;
            break;
          default:
            LogicException("Unsupported search mode for alternate operation '" +
                           oper->getName() + "'");
        }
        if (data->state->a_qty > ROUNDING_ERROR &&
            (val + ROUNDING_ERROR < bestAlternateValue ||
             (fabs(val - bestAlternateValue) < ROUNDING_ERROR &&
              data->state->a_qty > bestAlternateQuantity))) {
          // Found a better alternate
          bestAlternateValue = val;
          bestAlternateSelection = (*altIter)->getOperation();
          bestAlternateQuantity = data->state->a_qty;
          bestAcceptPartialReply = data->accept_partial_reply;
          bestFlow = sub_flow;
          bestQDate = ask_date;
        }
        // This was only an evaluation
        data->state->q_qty = origQqty;
        data->getCommandManager()->rollback(topcommand);
      }

      // Select the next alternate
      if (nextalternate) {
        ++altIter;
        if (altIter == oper->getSubOperations().end() && effectiveOnly) {
          // Prepare for a second iteration over all alternates
          effectiveOnly = false;
          altIter = oper->getSubOperations().begin();
        }
      }
    }  // End loop over all alternates

    // Replan on the best alternate
    if (bestAlternateQuantity > ROUNDING_ERROR &&
        search != SearchMode::PRIORITY) {
      // Message
      if (loglevel > 1)
        logger << indentlevel << "Alternate operation '" << oper
               << "' chooses alternate '" << bestAlternateSelection << "' "
               << search << '\n';

      // Create the top operationplan.
      // Note that both the top- and the sub-operation can have a flow in the
      // requested buffer
      auto* a = new CommandCreateOperationPlan(
          oper, a_qty, Date::infinitePast, bestQDate, d, data->state->curBatch,
          prev_owner_opplan, false, false);
      if (!prev_owner_opplan) data->getCommandManager()->add(a);

      // Recreate the ask
      if (!bestFlow)
        data->state->q_qty = a_qty;
      else if (!bestFlow->getQuantity() ||
               a_qty < bestFlow->getQuantityFixed() + ROUNDING_ERROR)
        data->state->q_qty = 0.001;
      else
        data->state->q_qty =
            (a_qty - bestFlow->getQuantityFixed()) / bestFlow->getQuantity();
      data->state->q_date = bestQDate;
      data->state->q_date_max = bestQDate;
      data->state->curDemand = nullptr;
      data->state->curOwnerOpplan = a->getOperationPlan();
      data->state->curBuffer =
          nullptr;  // Because we already took care of it... @todo not correct
                    // if the suboperation is again a owning operation

      // Create a sub operationplan and solve constraints
      bestAlternateSelection->solve(*this, v);
      data->accept_partial_reply =
          originalAcceptPartialReply || bestAcceptPartialReply;

      // Now solve for loads and flows of the top operationplan.
      // Only now we know how long that top-operation lasts in total.
      data->state->q_qty = data->state->a_qty;
      data->state->q_date = origQDate;
      data->state->q_date_max = origQDate;
      data->state->curOwnerOpplan->createFlowLoads();
      checkOperation(data->state->curOwnerOpplan, *data);

      // Multiply the operation reply with the flow quantity to obtain the
      // reply to return
      if (data->state->a_qty < ROUNDING_ERROR)
        data->state->a_qty = 0.0;
      else
        data->state->a_qty = bestFlow->getQuantityFixed() +
                             data->state->a_qty * bestFlow->getQuantity();

      // Combine the reply date of the top-opplan with the alternate check: we
      // need to return the minimum next-date.
      if (data->state->a_date < a_date && data->state->a_date > ask_date)
        a_date = data->state->a_date;

      // Prepare for the next loop
      a_qty -= data->state->a_qty;

      // Are we at the end already?
      if (a_qty < ROUNDING_ERROR) {
        a_qty = 0.0;
        break;
      }
    } else
      // No alternate can plan anything any more
      break;

  }  // End while loop until the a_qty > 0

  // Forget any constraints if we are not short or are planning unconstrained
  if (data->constraints && (a_qty < ROUNDING_ERROR || !originalLogConstraints))
    data->constraints->pop(topConstraint);

  // Unconstrained plan: If some unplanned quantity remains, switch to
  // unconstrained planning on the first alternate.
  // If something could be planned, we expect the caller to re-ask this
  // operation.
  if (!originalPlanningMode && fabs(origQqty - a_qty) < ROUNDING_ERROR &&
      firstAlternate) {
    // Message
    if (loglevel > 1)
      logger << indentlevel << "Alternate operation '" << oper
             << "' plans unconstrained on alternate '"
             << firstAlternate->getOperation() << "' " << search << '\n';

    // Current behaviour:
    //   Unconstrained plan violates effective dates and generates a JIT
    //   material plan
    // Functional variation:
    //   Respect the effectivity dates in the unconstrained plan, which will
    //   distort the material plan from the JIT pattern
    // if (origQDate > firstAlternate->getEffectiveEnd())
    //  origQDate = firstAlternate->getEffectiveEnd();
    // if (origQDate < firstAlternate->getEffectiveStart())
    //  origQDate = firstAlternate->getEffectiveStart();

    while (a_qty > ROUNDING_ERROR) {
      // Switch to unconstrained planning
      data->constrainedPlanning = false;
      data->logConstraints = false;

      // Create the top operationplan.
      // Note that both the top- and the sub-operation can have a flow in the
      // requested buffer
      auto* a = new CommandCreateOperationPlan(
          oper, a_qty, Date::infinitePast, origQDate, d, data->state->curBatch,
          prev_owner_opplan, false, false);
      if (!prev_owner_opplan) data->getCommandManager()->add(a);

      // Recreate the ask
      if (!firstFlow)
        data->state->q_qty = a_qty;
      else if (!firstFlow->getQuantity() ||
               a_qty < firstFlow->getQuantityFixed() + ROUNDING_ERROR)
        data->state->q_qty = 0.001;
      else
        data->state->q_qty =
            (a_qty - firstFlow->getQuantityFixed()) / firstFlow->getQuantity();
      data->state->q_date = origQDate;
      data->state->q_date_max = origQDate;
      data->state->curDemand = nullptr;
      data->state->curOwnerOpplan = a->getOperationPlan();
      data->state->curBuffer =
          nullptr;  // Because we already took care of it... @todo not correct
                    // if the suboperation is again a owning operation

      // Create a sub operationplan and solve constraints
      firstAlternate->getOperation()->solve(*this, v);

      // Expand flows of the top operationplan.
      data->state->q_qty = data->state->a_qty;
      data->state->q_date = origQDate;
      data->state->q_date_max = origQDate;
      data->state->curOwnerOpplan->createFlowLoads();
      checkOperation(data->state->curOwnerOpplan, *data);

      // Repeat until we have all material we need (or not making any progress)
      if (firstFlow) {
        auto tmp = data->state->a_qty * firstFlow->getQuantity() +
                   firstFlow->getQuantityFixed();
        if (!tmp) break;
        a_qty -= tmp;
      } else
        a_qty -= data->state->a_qty;
    }

    // Fully planned
    a_qty = 0.0;
    data->state->a_date = origQDate;
  }

  // Set up the reply
  data->state->a_qty = origQqty - a_qty;  // a_qty is the unplanned quantity
  data->state->a_date = a_date;
  data->state->q_qty_min = origQtyMin;
  if (data->state->a_qty == 0 && data->state->a_date <= origQDate) {
    if (getLogLevel() > 1)
      logger << indentlevel << "Applying lazy delay " << getLazyDelay()
             << " in alternate\n";
    data->state->a_date = origQDate + getLazyDelay();
  }
  assert(data->state->a_qty >= 0);

  // Restore the planning mode
  data->constrainedPlanning = originalPlanningMode;
  data->logConstraints = originalLogConstraints;

  // Increment the cost
  if (data->state->a_qty > 0.0) {
    auto tmp = data->state->curOwnerOpplan->getQuantity() * oper->getCost();
    data->state->a_cost += tmp;
    if (data->logcosts && data->incostevaluation)
      logger << indentlevel << "     + cost on operation '" << oper
             << "': " << tmp << '\n';
  }

  // Make sure other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be nullptr.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Optimization for detection of broken supply paths is disabled when we have
  // alternate operations. Only when all alternates report a broken path could
  // we use it.
  // TODO Not implemented.
  data->broken_path = false;

  // Message
  if (loglevel > 1) {
    logger << indentlevel-- << "Alternate operation '" << oper
           << "' answers: " << data->state->a_qty;
    if (!data->state->a_qty) logger << "  " << data->state->a_date;
    logger << '\n';
  }
}

void SolverCreate::solve(const OperationSplit* oper, void* v) {
  auto* data = static_cast<SolverData*>(v);
  Date origQDate = data->state->q_date;
  double origQqty = data->state->q_qty;
  Buffer* buf = data->state->curBuffer;
  Demand* dmd = data->state->curDemand;
  short loglevel = getLogLevel();

  // Call the user exit
  if (userexit_operation)
    userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  // Message
  if (loglevel > 1)
    logger << ++indentlevel << "Split operation '" << oper
           << "' is asked: " << data->state->q_qty << "  "
           << data->state->q_date << '\n';

  // Make sure sub-operationplans know their owner & store the previous value
  OperationPlan* prev_owner_opplan = data->state->curOwnerOpplan;

  double top_flow_qty_per = 0.0;
  if (buf) {
    // Find the flow into the requesting buffer for the quantity-per
    Flow* f = oper->findFlow(buf, data->state->q_date);
    if (f && f->isProducer()) {
      top_flow_qty_per += f->getQuantity();
      if (f->getQuantityFixed())
        logger << "Ignoring fixed operationmaterial production on a split "
                  "operation\n";
      logger << "Deprecation warning: split operation '" << oper
             << "' shouldn't produce material\n";
    }
  } else
    // We have a split operation as the delivery operation of a demand
    top_flow_qty_per = 1.0;

  // Compute the sum of all effective percentages
  int sum_percent = 0;
  for (auto& iter : oper->getSubOperations()) {
    if (iter->getEffective().within(data->state->q_date))
      sum_percent += iter->getPriority();
  }
  if (!sum_percent)
    // Oops, no effective suboperations found.
    // TODO Alternative: Look for an earlier date where at least one operation
    // is effective
    throw DataException("No operation is effective for split operation '" +
                        oper->getName() + "' at " +
                        string(data->state->q_date));

  // Loop until we find quantity that can be planned on each alternate.
  bool recheck = true;
  double loop_qty = data->state->q_qty;
  CommandCreateOperationPlan* top_cmd = nullptr;
  while (recheck) {
    // Set a bookmark in the command list.
    auto topcommand = data->getCommandManager()->setBookmark();

    // Create the top operationplan.
    top_cmd = new CommandCreateOperationPlan(
        oper, top_flow_qty_per ? origQqty / top_flow_qty_per : origQqty,
        Date::infinitePast, origQDate, dmd, data->state->curBatch,
        prev_owner_opplan, false, false);
    if (!prev_owner_opplan) data->getCommandManager()->add(top_cmd);

    recheck = false;
    int planned_percentages = 0;
    double planned_quantity = 0.0;
    for (auto iter = oper->getSubOperations().rbegin();
         iter != oper->getSubOperations().rend(); ++iter) {
      // Verify effectivity date and percentage > 0
      if (!(*iter)->getPriority() || !(*iter)->getEffective().within(origQDate))
        continue;

      // Find the flow
      double flow_qty_per = 0.0;
      if (buf) {
        Flow* f = (*iter)->getOperation()->findFlow(buf, data->state->q_date);
        if (f && f->isProducer()) {
          flow_qty_per += f->getQuantity();
          if (f->getQuantityFixed())
            logger << "Ignoring fixed operationmaterial production on a split "
                      "suboperation"
                   << '\n';
        }
      }
      auto flow_per = flow_qty_per + top_flow_qty_per;
      if (!flow_per) {
        // Neither the top nor the sub operation have a flow in the buffer,
        // we're in trouble...
        string msg = "  Operation doesn't produce into " +
                     data->state->curBuffer->getName();
        if (data->logConstraints && data->constraints) {
          auto j = data->constraints->begin();
          while (j != data->constraints->end()) {
            if (j->hasType<ProblemInvalidData>() && j->getDescription() == msg)
              break;
            ++j;
          }
          if (j == data->constraints->end())
            data->constraints->push(new ProblemInvalidData(
                const_cast<OperationSplit*>(oper), msg, "operation",
                Plan::instance().getCurrent(), Date::infiniteFuture, false));
        }
        bool problem_already_exists = false;
        auto probiter = Problem::iterator(oper);
        while (Problem* prob = probiter.next()) {
          if (typeid(*prob) == typeid(ProblemInvalidData) &&
              prob->getDescription() == msg) {
            problem_already_exists = true;
            break;
          }
        }
        if (!problem_already_exists)
          new ProblemInvalidData(const_cast<OperationSplit*>(oper), msg,
                                 "operation", Date::infinitePast,
                                 Date::infiniteFuture);
      }

      // Plan along this alternate
      double asked = (loop_qty - planned_quantity) * (*iter)->getPriority() /
                     (sum_percent - planned_percentages) / flow_per;
      if (asked > 0) {
        // Message
        if (loglevel > 1)
          logger << indentlevel << "  Split operation '" << oper
                 << "' asks alternate '" << (*iter)->getOperation()
                 << "': " << asked << '\n';

        // Due to minimum, maximum and multiple size constraints alternates can
        // plan a different quantity than requested. Asked quantity can thus go
        // negative and we skip some alternate.
        data->state->q_qty = asked;
        data->state->q_date = origQDate;
        data->state->curDemand = nullptr;
        data->state->curOwnerOpplan = top_cmd->getOperationPlan();
        data->state->curBuffer =
            nullptr;  // Because we already took care of it... @todo not correct
                      // if the suboperation is again a owning operation
        ++indentlevel;
        (*iter)->getOperation()->solve(*this, v);
        --indentlevel;

        if (loglevel > 1)
          logger << indentlevel << "  Split operation '" << oper
                 << "' gets answer from alternate '" << (*iter)->getOperation()
                 << "': " << data->state->a_qty << '\n';
      }

      // Evaluate the reply
      if (asked <= 0.0)
        // No intention to plan along this alternate
        continue;
      else if (data->state->a_qty == 0) {
        // Nothing can be planned here: break out of the loop and don't recheck.
        // The a_date is used below as reply from the top operation.
        loop_qty = 0.0;
        // Undo all plans done on any of the previous alternates
        data->getCommandManager()->rollback(topcommand);
        top_cmd = nullptr;
        break;
      } else if (data->state->a_qty <= asked - ROUNDING_ERROR) {
        // Planned short along this alternate. Replan all alternates
        // for a smaller quantity.
        recheck = true;
        loop_qty *= data->state->a_qty / asked;
        // Undo all plans done on any of the previous alternates
        data->getCommandManager()->rollback(topcommand);
        top_cmd = nullptr;
        break;
      } else {
        // Successfully planned along this alternate.
        planned_quantity += data->state->a_qty * flow_per;
        planned_percentages += (*iter)->getPriority();
      }
    }
  }

  if (loop_qty && top_cmd) {
    // Expand flows of the top operationplan.
    data->state->q_qty = top_cmd->getOperationPlan()->getQuantity();
    data->state->q_date = origQDate;
    data->state->curOwnerOpplan->createFlowLoads();
    checkOperation(top_cmd->getOperationPlan(), *data);
  }

  // Make sure other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be nullptr.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Final reply
  data->state->a_qty = loop_qty;
  if (loop_qty) data->state->a_date = Date::infiniteFuture;

  // Message
  if (loglevel > 1) {
    logger << indentlevel-- << "Split operation '" << oper
           << "' answers: " << data->state->a_qty;
    if (!data->state->a_qty) logger << "  " << data->state->a_date;
    logger << '\n';
  }
}

PyObject* Solver::createsBatches(PyObject* self, PyObject* args) {
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;
  try {
    auto* me = static_cast<SolverCreate*>(self);
    for (auto& o : Operation::all()) me->createsBatches(&o, &me->getCommands());
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void Solver::createsBatches(Operation* oper, void* v) {
  // Filter applicable operations:
  //  - batch window is positive
  //  - not loading any constrained resources
  //  - consumed material is already available at the source location
  //  - fixed duration
  if (!oper || oper->getBatchWindow() <= Duration(0L)) return;
  if (oper->hasType<OperationTimePer>()) {
    if (static_cast<OperationTimePer*>(oper)->getDurationPer()) return;
  } else if (!oper->hasType<OperationFixedTime, OperationItemSupplier,
                            OperationItemDistribution>())
    return;
  for (auto ld = oper->getLoads().begin(); ld != oper->getLoads().end(); ++ld)
    if (!oper->hasProperty("enforceBatchWindow") &&
        ld->getResource()->getConstrained())
      return;

  auto* solver = static_cast<Solver*>(v);
  auto loglevel = solver->getLogLevel();

  // Loop over all operationplans of the operation
  //   Scan for others that are within batching window and have same batch.
  //   If found:
  //      - delete them
  //      - increase quantity of the first one
  if (loglevel > 1) logger << "Batch grouping " << oper << '\n';
  auto opplan = oper->getOperationPlans();
  while (opplan != OperationPlan::end()) {
    if (opplan->getProposed()) {
      double added = 0;
      auto limit_date = max(opplan->getStart(), Plan::instance().getCurrent()) +
                        oper->getBatchWindow();
      auto next = opplan;
      ++next;
      while (next != OperationPlan::end() && next->getStart() < limit_date) {
        auto tmp = &*next;
        ++next;
        if (!tmp->getProposed() ||
            tmp->getQuantity() + opplan->getQuantity() + added >
                oper->getSizeMaximum() - ROUNDING_ERROR ||
            tmp->getBatch() != opplan->getBatch())
          continue;

        // Check the availability of all consumed materials between their
        // current date and the intended new date.
        auto flplniter = tmp->getFlowPlans();
        FlowPlan* flpln;
        bool ok = true;
        while ((flpln = flplniter.next()) && ok) {
          if (flpln->getQuantity() > -ROUNDING_ERROR ||
              flpln->getBuffer()->hasType<BufferInfinite>())
            continue;
          auto flpln_check = flpln->getBuffer()->getFlowPlans().begin(flpln);
          for (--flpln_check;
               flpln_check != flpln->getBuffer()->getFlowPlans().end() && ok;
               --flpln_check) {
            if (flpln_check->isLastOnDate() &&
                flpln_check->getOnhand() <
                    added - flpln->getQuantity() - ROUNDING_ERROR)
              ok = false;
            if (flpln_check->getOperationPlan() == &*opplan) break;
          }
        }
        if (!ok) continue;

        if (loglevel > 1)
          logger << "  Grouping " << tmp << " with " << &*opplan << '\n';
        added += tmp->getQuantity();
        delete tmp;
      }
      if (added > 0.0) {
        opplan->setQuantity(opplan->getQuantity() + added);
        // we found some operationplans to aggregate
        // but did we generate some excess, typically by summing some
        // unnecessary sizeminimum quantities ?
        auto flplniter = opplan->getFlowPlans();
        FlowPlan* flpln;
        double excess = DBL_MAX;
        while ((flpln = flplniter.next())) {
          if (flpln->getQuantity() < ROUNDING_ERROR) continue;
          auto tmp = flpln->getBuffer()->getOnHand(
              opplan->getEnd(), Date::infiniteFuture, true, true);
          if (tmp >= 0 && tmp < excess) excess = tmp;
        }

        // some security
        if (excess > 0) {
          if (excess > opplan->getQuantity()) excess = opplan->getQuantity();

          // handle operation size minimum that might slightly decrease the
          // excess
          if (opplan->getQuantity() - excess <
              opplan->getOperation()->getSizeMinimum()) {
            excess = max(opplan->getOperation()->getSizeMinimum() -
                             opplan->getQuantity(),
                         0.0);
          }
          // handle operation size multiple that might also slightly
          // decrease the onhand
          if (excess > 0 && opplan->getOperation()->getSizeMultiple() > 0.0) {
            auto oldvalue = opplan->getQuantity() - excess;
            auto newvalue =
                ceil(oldvalue / opplan->getOperation()->getSizeMultiple()) *
                opplan->getOperation()->getSizeMultiple();
            excess = max(excess - (newvalue - oldvalue), 0.0);
          }

          // Apply the excess we found
          if (excess > 0) opplan->setQuantity(opplan->getQuantity() - excess);
        }
      }
    }
    ++opplan;
  }
}

void SolverCreate::SolverData::populateDependencies(const Operation* o) {
  for (auto dpd : o->getDependencies()) {
    if (dpd->getOperation() != o) continue;
    auto l = dependency_list.find(dpd->getBlockedBy());
    if (l == dependency_list.end()) {
      dependency_list[dpd->getBlockedBy()] =
          pair<unsigned short, Date>(1, Date::infiniteFuture);
      // Recursive call
      populateDependencies(dpd->getBlockedBy());
    } else
      ++l->second.first;
  }
  if (o->hasType<OperationRouting>()) {
    for (auto sub : o->getSubOperations()) {
      // Recursive call for end-of-chain suboperations
      bool isblocked = false;
      for (auto& dpd : sub->getOperation()->getDependencies()) {
        if (dpd->getBlockedBy() == sub->getOperation()) {
          isblocked = true;
          break;
        }
      }
      if (!isblocked) populateDependencies(sub->getOperation());
    }
  } else if (!o->getSubOperations().empty()) {
    for (auto sub : o->getSubOperations())
      // Recursive call
      populateDependencies(sub->getOperation());
  }
}

void SolverCreate::checkDependencies(OperationPlan* opplan, SolverData& data,
                                     bool& incomplete, double& a_qty,
                                     DateRange& matnext) {
  if (!opplan->getOperation()->getDependencies().empty() &&
      data.dependency_list.empty())
    // Starting a new dependency list.
    data.populateDependencies(opplan->getOperation());

  for (auto dpd : opplan->getOperation()->getDependencies()) {
    if (dpd->getOperation() != opplan->getOperation() || !dpd->getQuantity())
      continue;

    // Compute ask date
    data.state->q_date = opplan->getStart();
    auto needed_date = data.state->q_date - dpd->getHardSafetyLeadtime();
    auto wished_date = needed_date;
    if (dpd->getSafetyLeadtime() > dpd->getHardSafetyLeadtime())
      wished_date = opplan->getStart() - dpd->getSafetyLeadtime();
    data.state->q_date = wished_date;

    // Check if this is the last time it appears in the dependency list
    auto occurences = data.dependency_list.find(dpd->getBlockedBy());
    if (occurences != data.dependency_list.end()) {
      if (occurences->second.first > 1) {
        // Not ready to explore this dependency yet.
        // We just record the requirement date.
        --occurences->second.first;
        if (getLogLevel() > 1) {
          logger << indentlevel << "  Delay following dependency '"
                 << dpd->getBlockedBy();
          if (occurences->second.second > data.state->q_date)
            logger << "' - setting requirement date to " << data.state->q_date;
          logger << '\n';
        }
        if (occurences->second.second > data.state->q_date)
          occurences->second.second = data.state->q_date;
        continue;
      } else {
        // OK to to explore this dependency
        if (occurences->second.second < data.state->q_date) {
          if (getLogLevel() > 1) {
            logger << indentlevel << "  Dependency updates requirement date to "
                   << occurences->second.second << '\n';
          }
          data.state->q_date = occurences->second.second;
        }
        data.dependency_list.erase(occurences);
      }
    }

    // Net available quantities from the required quantity.
    data.state->q_qty = opplan->getQuantity() * dpd->getQuantity();
    auto required = data.state->q_qty;
    auto allocated = 0.0;
    for (auto e : opplan->getDependencies()) {
      // Subtract existing allocations
      if (e->getSecond() == opplan &&
          e->getFirst()->getOperation() == dpd->getBlockedBy()) {
        allocated += e->getFirst()->getQuantity();
      }
    }
    auto o = dpd->getBlockedBy()->getOperationPlans();
    while (o != OperationPlan::end() && required > allocated + ROUNDING_ERROR) {
      // Create new allocations from available supply
      if (opplan->getBatch() && o->getBatch() != opplan->getBatch()) {
        ++o;
        continue;
      }
      auto unpegged = o->getQuantity();
      for (auto d : o->getDependencies()) {
        if (d->getFirst() == &*o) unpegged -= d->getQuantity();
      }

      // Allocate from unpegged quantity
      if (unpegged > ROUNDING_ERROR) {
        Date refuse = Date::infinitePast;
        if (o->getEnd() > needed_date && getConstraints() &&
            data.constrainedPlanning) {
          if (o->getConfirmed() || ((o->getProposed() || o->getApproved()) &&
                                    !Plan::instance().getMoveApprovedEarly())) {
            // We need to wait for this dependency
            opplan->setStart(o->getEnd());
            refuse = opplan->getEnd() + dpd->getHardSafetyLeadtime();
            if (getLogLevel() > 1) {
              logger << indentlevel << "  Waiting for dependency on " << &*o
                     << '\n';
            }
          } else if (o->getProposed() || o->getApproved()) {
            // Try to reschedule the depencency
            if (getLogLevel() > 1)
              logger << indentlevel << "  Moving dependency early: " << &*o
                     << '\n';
            auto bm = data.getCommandManager()->setBookmark();
            data.getCommandManager()->add(new CommandMoveOperationPlan(
                &*o, Date::infinitePast, wished_date));
            checkOperation(&*o, data);
            if (o->getEnd() > needed_date) {
              // Rescheduling wasn't feasible.
              if (getLogLevel() > 1)
                logger << indentlevel
                       << "  Moving dependency failed. Earliest "
                          "date is "
                       << (o->getEnd() + dpd->getHardSafetyLeadtime()) << '\n';
              refuse = o->getEnd() + dpd->getHardSafetyLeadtime();
              data.getCommandManager()->rollback(bm);
            } else {
              // Rescheduling was feasible
              if (getLogLevel() > 1)
                logger << indentlevel
                       << "  Moving approved dependency succeeded\n";
            }
          }
        }
        if (refuse) {
          // Wait for this predecessor
          a_qty = 0.0;
          incomplete = true;
          if (data.logConstraints && data.constraints)
            data.constraints->push(ProblemAwaitSupply::metadata,
                                   o->getOperation(), opplan->getStart(),
                                   refuse);
          data.state->a_date = refuse;
          matnext = DateRange(refuse, refuse);
          return;
        }

        // Note: we count on the rollback to undo this allocation if needed
        if (getLogLevel() > 1) {
          logger << indentlevel << "  Allocating from available supply on "
                 << &*o << '\n';
        }
        new OperationPlanDependency(&*o, opplan, dpd);
        allocated += unpegged;
        if (required < allocated + ROUNDING_ERROR) {
          allocated = required;
          break;
        }
      }
      ++o;
    }

    if (required > allocated + ROUNDING_ERROR) {
      // Plan net required quantity
      auto orig_q_qty = required;
      bool repeat = false;
      auto bm = data.getCommandManager()->setBookmark();
      auto prevOwnerOpplan = data.state->curOwnerOpplan;
      do {
        repeat = false;
        data.state->q_qty = orig_q_qty - allocated;
        double my_q_qty = data.state->q_qty;
        data.state->blockedOpplan = opplan;
        data.state->dependency = dpd;
        data.state->curOwnerOpplan =
            (dpd->getBlockedBy()->getOwner() &&
             dpd->getBlockedBy()->getOwner() == dpd->getOperation()->getOwner())
                ? prevOwnerOpplan
                : nullptr;
        dpd->getBlockedBy()->solve(*this, &data);
        a_qty = (data.state->a_qty + allocated) / dpd->getQuantity();
        if (data.state->a_qty < ROUNDING_ERROR) {
          if (dpd->getSafetyLeadtime() > dpd->getHardSafetyLeadtime() &&
              data.state->a_date <=
                  opplan->getStart() - dpd->getHardSafetyLeadtime() &&
              orig_q_qty) {
            if (getLogLevel() > 1) {
              logger << indentlevel
                     << "  Compressing safety lead time between '"
                     << dpd->getOperation() << "' and '" << dpd->getBlockedBy()
                     << "'\n";
            }
            data.state->q_date = data.state->a_date;
            bm->rollback();
            repeat = true;
          } else {
            a_qty = 0.0;
            if (dpd->getHardSafetyLeadtime())
              data.state->a_date += dpd->getHardSafetyLeadtime();
            // Compute my end date if the blocked-by operation is delayed.
            // In case the case this operation isn't the critical dependency
            // path, this code isn't enough and we'll get a lazy delay loop.
            opplan->setStart(data.state->a_date);
            matnext = DateRange(opplan->getEnd(), opplan->getEnd());
            incomplete = true;
            data.dependency_list.clear();
            break;
          }
        } else if (!data.state->curOwnerOpplan &&
                   my_q_qty - data.state->a_qty > ROUNDING_ERROR) {
          // Partially planned across a dependency.
          allocated += data.state->a_qty;
          if (allocated < orig_q_qty - ROUNDING_ERROR) repeat = true;
        }
      } while (repeat);
      data.state->curOwnerOpplan = prevOwnerOpplan;
      if (incomplete) break;
    }
  }
}

}  // namespace frepple
