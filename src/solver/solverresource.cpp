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

/* @todo resource solver should be using a move command rather than direct move
 */
void SolverCreate::solve(const Resource* res, void* v) {
  // Shortcut for unconstrained resources
  if (!res->getConstrained()) {
    solveUnconstrained(res, v);
    return;
  }

  auto* data = static_cast<SolverData*>(v);

  // Call the user exit
  if (userexit_resource)
    userexit_resource.call(res, PythonData(data->constrainedPlanning));

  // Message
  if (getLogLevel() > 1) {
    if (!data->constrainedPlanning || !isConstrained())
      logger << ++indentlevel << "Resource '" << res
             << "' is asked in unconstrained mode: " << (-data->state->q_qty)
             << "  " << data->state->q_operationplan->getDates() << '\n';
    else
      logger << ++indentlevel << "Resource '" << res
             << "' is asked: " << (-data->state->q_qty) << "  "
             << data->state->q_operationplan->getDates() << '\n';
  }

  // Initialize some variables
  double orig_q_qty = -data->state->q_qty;
  OperationPlanState currentOpplan(data->state->q_operationplan);
  Resource::loadplanlist::const_iterator cur = res->getLoadPlans().end();
  Date curdate;
  double curMax, prevMax;
  bool HasOverload;
  bool noRestore = data->state->forceLate;

  // Initialize the default reply
  data->state->a_date = data->state->q_date;
  data->state->a_qty = orig_q_qty;
  Date prevdate;

  // Loop for a valid location by using EARLIER capacity
  if (!data->state->forceLate) do {
      // Check the leadtime constraints
      prevdate = data->state->q_operationplan->getEnd();
      noRestore = data->state->forceLate;

      if (isLeadTimeConstrained(data->state->q_operationplan->getOperation()))
        // Note that the check function can update the answered date and
        // quantity
        if (data->constrainedPlanning &&
            !checkOperationLeadTime(data->state->q_operationplan, *data,
                                    false)) {
          // Operationplan violates the lead time and/or fence constraint
          noRestore = true;
          break;
        }

      // Check if this operation overloads the resource at its current time
      HasOverload = false;
      Date earliestdate = data->state->q_operationplan->getStart();
      curdate = data->state->q_loadplan->getDate();
      curMax = data->state->q_loadplan->getMax(false);
      prevMax = curMax;
      for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
           cur != res->getLoadPlans().end() && cur->getDate() >= earliestdate;
           --cur) {
        // A change in the maximum capacity
        prevMax = curMax;
        if (cur->getEventType() == 4) curMax = cur->getMax(false);

        // Skip setup change events
        if (cur->getEventType() == 5) continue;

        // Not interested if date doesn't change
        if (cur->getDate() == curdate) continue;

        if (cur->getOnhand() > prevMax + ROUNDING_ERROR) {
          // Overload: We are exceeding the limit!
          // At this point:
          //  - cur points to a loadplan where we exceed the capacity
          //  - curdate points to the latest date without overload
          //  - curdate != cur->getDate()
          HasOverload = true;
          break;
        }
        curdate = cur->getDate();
      }

      // Try solving the overload by moving the operationplan to an earlier date
      if (HasOverload) {
        // Search backward in time for a period where there is no overload
        curMax = cur->getMax(false);
        prevMax = curMax;
        curdate = cur->getDate();
        for (; cur != res->getLoadPlans().end() &&
               curdate > currentOpplan.end - res->getMaxEarly();
             --cur) {
          // A change in the maximum capacity
          prevMax = curMax;
          if (cur->getEventType() == 4) curMax = cur->getMax(false);

          // Not interested if date doesn't change or setup end events
          if (cur->getDate() == curdate || cur->getEventType() == 5) continue;

          // We are below the max limit now.
          if (cur->getOnhand() < prevMax + ROUNDING_ERROR && curdate < prevdate)
            break;
          curdate = cur->getDate();
        }
        assert(curdate != prevdate);

        // We found a date where the load goes below the maximum
        // At this point:
        //  - curdate is a latest date where we are above the maximum
        //  - cur is the first loadplan where we are below the max
        if (cur != res->getLoadPlans().end() &&
            curdate > currentOpplan.end - res->getMaxEarly()) {
          // Move the operationplan
          data->state->q_operationplan->setEnd(curdate);

          // Verify the move is successfull
          if (data->state->q_operationplan->getEnd() > curdate ||
              data->state->q_operationplan->getQuantity() == 0.0)
            // If there isn't available time in the location calendar, the move
            // can fail.
            data->state->a_qty = 0.0;
          else if (data->constrainedPlanning &&
                   isLeadTimeConstrained(
                       data->state->q_operationplan->getOperation()))
            // Check the leadtime constraints after the move
            // Note that the check function can update the answered date
            // and quantity
            checkOperationLeadTime(data->state->q_operationplan, *data, false);
        } else {
          // No earlier capacity found: get out of the loop
          data->state->a_qty = 0.0;
          if (res->getMaxEarly() > data->hitMaxEarly)
            data->hitMaxEarly = res->getMaxEarly();
        }
      }  // End of if-statement, solve by moving earlier
    } while (HasOverload && data->state->a_qty != 0.0);

  // Loop for a valid location by using LATER capacity
  // If the answered quantity is 0, the operationplan is moved into the past.
  // Or, the solver may be forced to produce a late reply.
  // In these cases we need to search for capacity at later dates.
  if (data->constrainedPlanning &&
      (data->state->a_qty == 0.0 || data->state->forceLate)) {
    // Put the operationplan back at its original end date
    if (!noRestore) data->state->q_operationplan->restore(currentOpplan);

    // Moving an operation earlier is driven by the ending loadplan,
    // while searching for later capacity is driven from the starting loadplan.
    LoadPlan* old_q_loadplan = data->state->q_loadplan;
    data->state->q_loadplan = data->state->q_loadplan->getOtherLoadPlan();

    // Loop to find a later date where the operationplan will fit
    Date newDate;
    unsigned long iterations = 0;
    do {
      // Search for a date where we go below the maximum load.
      // and verify whether there are still some overloads
      HasOverload = false;
      newDate = Date::infinitePast;
      curMax = data->state->q_loadplan->getMax();

      // Find how many uncommitted operationplans are loading the resource
      // before the loadplan.
      // If the same resource is used multiple times in the supply path of a
      // demand we need to use only the capacity used by other demands.
      // Otherwise our estimate is of the feasible next date is too pessimistic.
      // If the operation is the same, the operationplans are at the same stage
      // in the supply path and we need to include these in our estimate of the
      // next date.
      double ignored = 0.0;
      for (cur = res->getLoadPlans().begin();
           cur != res->getLoadPlans().end() &&
           cur != res->getLoadPlans().begin(data->state->q_loadplan);
           ++cur) {
        const LoadPlan* ldplan = nullptr;
        if (cur->getEventType() == 1)
          ldplan = static_cast<const LoadPlan*>(&*cur);
        if (ldplan && !ldplan->getOperationPlan()->getActivated() &&
            ldplan->getOperationPlan()->getOperation() !=
                data->state->q_operationplan->getOperation())
          ignored += ldplan->getQuantity();
      }

      for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
           !(HasOverload && newDate) && cur != res->getLoadPlans().end();) {
        // New maximum
        if (cur->getEventType() == 4) curMax = cur->getMax();
        const LoadPlan* ldplan = nullptr;
        if (cur->getEventType() == 1)
          ldplan = static_cast<const LoadPlan*>(&*cur);
        if (ldplan && !ldplan->getOperationPlan()->getActivated() &&
            ldplan->getOperationPlan()->getOperation() !=
                data->state->q_operationplan->getOperation())
          ignored += ldplan->getQuantity();

        // Only consider the last loadplan for a certain date
        const TimeLine<LoadPlan>::Event* loadpl = &*(cur++);
        if (cur != res->getLoadPlans().end() &&
            cur->getDate() == loadpl->getDate())
          continue;

        // Check if overloaded
        if (loadpl->getOnhand() - ignored > curMax + ROUNDING_ERROR)
          // There is still a capacity problem
          HasOverload = true;
        else if (!HasOverload &&
                 loadpl->getDate() > data->state->q_operationplan->getEnd())
          // Break out of loop if no overload and we're beyond the
          // operationplan end date.
          break;
        else if (!newDate &&
                 loadpl->getDate() != data->state->q_loadplan->getDate() &&
                 curMax >= fabs(loadpl->getQuantity()) &&
                 (loadpl->getDate() != data->state->q_operationplan->getEnd() ||
                  !loadpl->isOnlyEventOnDate())) {
          // We are below the max limit for the first time now.
          // This means that the previous date may be a proper start.
          newDate = loadpl->getDate();
        }
      }

      // Found a date with available capacity
      if (HasOverload && newDate) {
        data->state->q_operationplan->setOperationPlanParameters(
            currentOpplan.quantity, newDate, Date::infinitePast, true, true,
            false);
        HasOverload = true;
        if (data->state->q_operationplan->getStart() < newDate ||
            !data->state->q_operationplan->getQuantity() ||
            data->state->q_operationplan->getEnd() == Date::infiniteFuture)
          // Moving to the new date turns out to be infeasible! Give it up.
          // For instance, this can happen when the location calendar doesn't
          // have any up-time after the specified date.
          break;
      }
      ++iterations;
    } while (HasOverload && newDate && iterations < getResourceIterationMax());
    if (iterations >= getResourceIterationMax())
      logger << indentlevel << "Warning: no free capacity slot found on " << res
             << " after " << getResourceIterationMax()
             << " iterations. Last date: " << newDate << '\n';
    data->state->q_loadplan = old_q_loadplan;

    // Set the date where a next trial date can happen
    if (HasOverload)
      // No available capacity found anywhere in the horizon
      data->state->a_date = Date::infiniteFuture;
    else if (data->state->q_operationplan->getEnd() > currentOpplan.end)
      data->state->a_date = data->state->q_operationplan->getEnd();
    else
      data->state->a_date =
          currentOpplan.end + data->getSolver()->getMinimumDelay();

    // Create a zero quantity reply
    data->state->a_qty = 0.0;
  }

  // Force ok in unconstrained plan
  if (!data->constrainedPlanning && data->state->a_qty == 0.0) {
    data->state->q_operationplan->restore(currentOpplan);
    data->state->a_date = data->state->q_date;
    data->state->a_qty = orig_q_qty;
  }

  // Increment the cost
  if (data->state->a_qty > 0.0) {
    // Resource usage
    {
      auto tmp = data->state->a_qty * res->getCost() *
                 (data->state->q_operationplan->getDates().getDuration() -
                  data->state->q_operationplan->getUnavailable()) /
                 3600.0;
      data->state->a_cost += tmp;
      if (data->logcosts && data->incostevaluation)
        logger << indentlevel << "     + cost on resource '" << res
               << "': " << tmp << '\n';
    }

    // Setup cost
    data->state->a_penalty += data->state->q_operationplan->getSetupCost();
    // Build-ahead penalty: 5% of the cost   @todo buildahead penalty is
    // hardcoded
    if (currentOpplan.end > data->state->q_operationplan->getEnd())
      data->state->a_penalty +=
          (currentOpplan.end - data->state->q_operationplan->getEnd()) * 0.05 /
          3600.0 * (res->getCost() > 0 ? res->getCost() : 1.0);
  }

  // Maintain the constraint list
  if (data->state->a_qty == 0.0 && data->logConstraints && data->constraints)
    data->constraints->push(ProblemCapacityOverload::metadata, res,
                            currentOpplan.start, currentOpplan.end, 0.0,
                            data->state->q_operationplan->getOperation());

  if (currentOpplan.end > data->state->q_operationplan->getEnd() &&
      data->logConstraints && data->constraints) {
    // Using earlier capacity is logged as a constraint.
    // If the resource isn't on the critical path that constraint will later be
    // filtered out again.
    data->constraints->push(ProblemCapacityOverload::metadata, res,
                            currentOpplan.end,
                            data->state->q_operationplan->getEnd(), 0.0,
                            data->state->q_operationplan->getOperation(), true);
  }

  // Message
  if (getLogLevel() > 1) {
    logger << indentlevel-- << "Resource '" << res
           << "' answers: " << data->state->a_qty << "  "
           << data->state->a_date;
    if (currentOpplan.end > data->state->q_operationplan->getEnd())
      logger << " using earlier capacity "
             << data->state->q_operationplan->getEnd();
    if (data->state->a_qty > 0.0 &&
        data->state->q_operationplan->getQuantity() < currentOpplan.quantity)
      logger << " with reduced quantity "
             << data->state->q_operationplan->getQuantity();
    logger << '\n';
  }
}

void SolverCreate::solveUnconstrained(const Resource* res, void* v) {
  auto* data = static_cast<SolverData*>(v);

  // Call the user exit
  if (userexit_resource)
    userexit_resource.call(res, PythonData(data->constrainedPlanning));

  // Message
  if (getLogLevel() > 1 && data->state->q_qty < 0)
    logger << ++indentlevel << "Unconstrained resource '" << res
           << "' is asked: " << (-data->state->q_qty) << "  "
           << data->state->q_operationplan->getDates() << '\n';

  // @todo Need to make the setups feasible - move to earlier dates till
  // max_early fence is reached

  // Reply whatever is requested, regardless of date and quantity.
  data->state->a_qty = -data->state->q_qty;
  data->state->a_date = data->state->q_date;
  {
    auto tmp = data->state->a_qty * res->getCost() *
               (data->state->q_operationplan->getDates().getDuration() -
                data->state->q_operationplan->getUnavailable()) /
               3600.0;
    data->state->a_cost += tmp;
    if (data->logcosts && data->incostevaluation)
      logger << indentlevel << "     + cost on resource '" << res
             << "': " << tmp << '\n';
  }

  // Message
  if (getLogLevel() > 1 && data->state->q_qty < 0)
    logger << indentlevel-- << "Unconstrained resource '" << res
           << "' answers: " << data->state->a_qty << '\n';
}

void SolverCreate::solve(const ResourceBuckets* res, void* v) {
  auto* data = static_cast<SolverData*>(v);
  if (!res->getConstrained() || !data->state->q_loadplan->getLoad()) {
    solveUnconstrained(res, v);
    return;
  }
  auto opplan = data->state->q_operationplan;

  // Call the user exit
  if (userexit_resource)
    userexit_resource.call(res, PythonData(data->constrainedPlanning));

  // Message
  if (getLogLevel() > 1 && data->state->q_qty < 0)
    logger << ++indentlevel << "Bucketized resource '" << res
           << "' is asked: " << (-data->state->q_qty) << "  "
           << opplan->getDates() << '\n';

  // Set a flag for the checkOperation method to mark that bucketized resources
  // are involved
  data->state->has_bucketized_resources = true;

  // Initialize some variables
  bool time_per_logic =
      opplan->getOperation()->hasType<OperationTimePer>() &&
      static_cast<OperationTimePer*>(opplan->getOperation())
          ->getDurationPer() &&
      data->state->q_loadplan->getLoad()->hasType<LoadDefault>();
  double orig_q_qty = -data->state->q_qty;
  OperationPlanState originalOpplan(opplan);
  Resource::loadplanlist::const_iterator cur = res->getLoadPlans().end();
  Date curdate, prevdate, loaddate;
  bool noRestore = data->state->forceLate;
  double overloadQty = 0.0;
  double min_free_quantity = ROUNDING_ERROR;
  bool date_effective = false;

  // Initialize the default reply
  data->state->a_date = data->state->q_date;
  data->state->a_qty = orig_q_qty;

  if (time_per_logic) {
    auto bucketend = data->state->q_loadplan->getBucketEnd();
    overloadQty = get<0>(bucketend);
    if (!data->state->forceLate) {
      // TODO opportunity for performance optimization in situations where
      // everything happens in a single bucket

      // Reduce the operationplan to its minimum size
      opplan->setOperationPlanParameters(data->state->q_qty_min / 10,
                                         Date::infinitePast, originalOpplan.end,
                                         true, true, false);
      // See if it fits in that bucket
      bucketend = data->state->q_loadplan->getBucketEnd();
      overloadQty = get<0>(bucketend);

      // In the same bucket, we may be able to plan more than the minimum
      auto bucketstart = data->state->q_loadplan->getBucketStart();
      if (overloadQty > ROUNDING_ERROR &&
          opplan->getQuantity() < originalOpplan.quantity - ROUNDING_ERROR) {
        // Resize the operationplan to the maximum size that still fits in
        // this bucket

        // Fit the best operationplan in this bucket
        // If enough time is available we can plan the full requested quantity
        opplan->setOperationPlanParameters(
            originalOpplan.quantity, get<1>(bucketstart), originalOpplan.end,
            true, true, false);
        // There may not be enough capacity to support this quantity
        bucketend = data->state->q_loadplan->getBucketEnd();
        if (get<0>(bucketend) > -ROUNDING_ERROR) {
          overloadQty = 0.0;
          data->state->a_qty = -data->state->q_loadplan->getQuantity();
          data->state->a_date = data->state->q_loadplan->getDate();
        } else {
          // Resize to fit
          Date oldEnd = opplan->getEnd();
          double oldQty = opplan->getQuantity();
          double efficiency =
              data->state->q_loadplan->getResource()->getEfficiencyCalendar()
                  ? data->state->q_loadplan->getResource()
                        ->getEfficiencyCalendar()
                        ->getValue(data->state->q_loadplan->getDate())
                  : data->state->q_loadplan->getResource()->getEfficiency();
          double newQty =
              oldQty + get<0>(bucketend) /
                           data->state->q_loadplan->getLoad()->getQuantity() *
                           efficiency / 100.0;
          if (newQty > ROUNDING_ERROR) {
            opplan->setOperationPlanParameters(newQty, Date::infinitePast,
                                               oldEnd);
            if (opplan->getQuantity() > 0 &&
                opplan->getQuantity() <= newQty + ROUNDING_ERROR &&
                opplan->getEnd() <= oldEnd) {
              // The squeezing did work!
              // The operationplan quantity is now reduced. The buffer solver
              // will ask again for the remaining short quantity, so we don't
              // need to bother about that here.
              overloadQty = 0.0;
              data->state->a_qty = -data->state->q_loadplan->getQuantity();
              data->state->a_date = data->state->q_loadplan->getDate();
            }
          }
        }
      }
    } else {
      // Compute the minimum free capacity we need in a bucket
      // -> not fully correct if efficiency and effectivity come into the
      // picture
      // -> replace with a move to each bucket
      if (!date_effective) {
        min_free_quantity =
            opplan->getOperation()->setOperationPlanQuantity(
                opplan, 0.01, false, false, false, Date::infinitePast) *
                data->state->q_loadplan->getLoad()->getQuantity() +
            data->state->q_loadplan->getLoad()->getQuantityFixed();
        double efficiency =
            data->state->q_loadplan->getResource()->getEfficiencyCalendar()
                ? data->state->q_loadplan->getResource()
                      ->getEfficiencyCalendar()
                      ->getValue(data->state->q_loadplan->getDate())
                : data->state->q_loadplan->getResource()->getEfficiency();
        if (efficiency != 100.0) min_free_quantity /= efficiency * 100.0;
      }
      // TODO The logic is not symmetrical with time_per operations.
      // For time-per operations we already evaluated the current bucket.
    }
  } else {
    auto bucketend = data->state->q_loadplan->getBucketEnd();
    overloadQty = get<0>(bucketend);
  }

  // Loop for a valid location by using EARLIER capacity
  if (!data->state->forceLate && (overloadQty || !time_per_logic)) do {
      // Check the leadtime constraints
      prevdate = opplan->getEnd();
      noRestore = data->state->forceLate;

      if (isLeadTimeConstrained(opplan->getOperation()))
        // Note that the check function can update the answered date and
        // quantity
        if (data->constrainedPlanning &&
            !checkOperationLeadTime(opplan, *data, false)) {
          // Operationplan violates the lead time and/or fence constraint
          noRestore = true;
          break;
        }

      // Check if this operation overloads the resource bucket
      // TODO The line below is cleaner, but since the loop below also updates
      // cur we can't use it yet auto bucketend =
      // data->state->q_loadplan->getBucketEnd();
      overloadQty = 0.0;
      for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
           cur != res->getLoadPlans().end() && cur->getEventType() != 2; ++cur)
        if (cur->getOnhand() < overloadQty) overloadQty = cur->getOnhand();

      // Solve the overload in the bucket by resizing the operationplan.
      // If the complete operationplan is overload then
      // we can skip this step. Because of operation size constraints (minimum
      // and multiple values) it is possible that the resizing fails.
      if (overloadQty < -ROUNDING_ERROR &&
          orig_q_qty > -overloadQty + ROUNDING_ERROR &&
          data->state->q_loadplan->getLoad()->getQuantity() &&
          !time_per_logic) {
        OperationPlanState beforeSqueeze(opplan);
        Date oldEnd = opplan->getEnd();
        double oldQty = opplan->getQuantity();
        double efficiency =
            data->state->q_loadplan->getResource()->getEfficiencyCalendar()
                ? data->state->q_loadplan->getResource()
                      ->getEfficiencyCalendar()
                      ->getValue(data->state->q_loadplan->getDate())
                : data->state->q_loadplan->getResource()->getEfficiency();
        double newQty =
            oldQty + overloadQty /
                         data->state->q_loadplan->getLoad()->getQuantity() *
                         efficiency / 100.0;
        if (newQty > ROUNDING_ERROR) {
          opplan->setOperationPlanParameters(newQty, Date::infinitePast,
                                             oldEnd);
          if (opplan->getQuantity() > 0 &&
              opplan->getQuantity() <= newQty + ROUNDING_ERROR &&
              opplan->getEnd() <= oldEnd) {
            // The squeezing did work!
            // The operationplan quantity is now reduced. The buffer solver will
            // ask again for the remaining short quantity, so we don't need to
            // bother about that here.
            overloadQty = 0.0;
            data->state->a_qty = -data->state->q_loadplan->getQuantity();
            // With operations of type time_per, it is also possible that the
            // operation now consumes capacity in a different bucket.
            // If that's the case, we move it to start right at the end of the
            // bucket.
            if (cur != res->getLoadPlans().end() &&
                data->state->q_loadplan->getDate() >= cur->getDate()) {
              Date tmp =
                  data->state->q_loadplan->getLoad()->getOperationPlanDate(
                      data->state->q_loadplan, cur->getDate() - Duration(1L),
                      true);
              opplan->setStart(tmp);
            }
          } else {
            // It didn't work. Restore the original operationplan.
            // @todo this undoing is a performance bottleneck: trying to resize
            // and restoring the original are causing lots of updates in the
            // buffer and resource timelines...
            // We need an api that only checks the resizing.
            opplan->restore(beforeSqueeze);
          }
        }
      }

      // Try solving the overload by moving the operationplan to an earlier date
      if (overloadQty < -ROUNDING_ERROR) {
        // Search backward in time for a bucket that still has capacity left
        Date bucketEnd;
        DateRange newStart;
        cur = res->getLoadPlans().begin(data->state->q_loadplan);
        bool found = false;
        while (cur != res->getLoadPlans().end() &&
               cur->getDate() > originalOpplan.end - res->getMaxEarly()) {
          if (!data->state->q_loadplan->getLoad()->getEffective().within(
                  cur->getDate())) {
            // The load isn't effective any longer, and our problem is solved
            newStart = opplan->getOperation()->calculateOperationTime(
                opplan,
                data->state->q_loadplan->getLoad()->getEffective().getStart(),
                Duration(1L), false);
            break;
          }
          if (cur->getEventType() != 2) {
            --cur;
            continue;
          }
          bucketEnd = cur->getDate();
          --cur;  // Move to last loadplan in the previous bucket
          if (cur != res->getLoadPlans().end() &&
              cur->getOnhand() > min_free_quantity) {
            // Find a suitable loadplan date in this bucket
            newStart = opplan->getOperation()->calculateOperationTime(
                opplan, bucketEnd, Duration(1L), false);
            // Move to the start of the bucket
            while (cur != res->getLoadPlans().end() && cur->getEventType() != 2)
              --cur;
            // If the new start date is within this bucket we have found a
            // bucket with available capacity left
            if (cur == res->getLoadPlans().end() ||
                cur->getDate() <= newStart.getStart()) {
              found = true;
              break;
            }
          }
        }

        // We found a date where the load goes below the maximum.
        // newStart.getStart() is the last available date in a bucket
        // where capacity is still available.
        // cur.getDate points to the start date of that bucket.
        // bucketEnd points to the end date of that bucket.
        if ((bucketEnd ||
             !data->state->q_loadplan->getLoad()->getEffective().within(
                 newStart.getStart())) &&
            found &&
            newStart.getStart() >= originalOpplan.end - res->getMaxEarly()) {
          bool moved = true;
          if (time_per_logic) {
            // Resize the operationplan to the maximum quantity that is feasible
            // in this bucket
            opplan->setOperationPlanParameters(
                originalOpplan.quantity, newStart.getStart(),
                originalOpplan.end, false, true, true);
            auto overload = get<0>(data->state->q_loadplan->getBucketEnd());
            if (overload > -ROUNDING_ERROR) {
              // Requested quantity fits completely in this bucket
              overloadQty = 0.0;
              Date tmp =
                  data->state->q_loadplan->getLoad()->getOperationPlanDate(
                      data->state->q_loadplan, newStart.getStart(), true);
              opplan->setStart(tmp);
            } else {
              // Only a part of the requirement fits in the bucket
              double oldQty = opplan->getQuantity();
              double efficiency =
                  data->state->q_loadplan->getResource()
                          ->getEfficiencyCalendar()
                      ? data->state->q_loadplan->getResource()
                            ->getEfficiencyCalendar()
                            ->getValue(data->state->q_loadplan->getDate())
                      : data->state->q_loadplan->getResource()->getEfficiency();
              double newQty =
                  oldQty +
                  overload / data->state->q_loadplan->getLoad()->getQuantity() *
                      efficiency / 100.0;
              if (newQty < ROUNDING_ERROR ||
                  fabs(oldQty - newQty) < ROUNDING_ERROR)
                moved = false;
              else {
                OperationPlanState tmp(opplan);
                opplan->setOperationPlanParameters(newQty, newStart.getStart(),
                                                   Date::infinitePast, false,
                                                   true, true);
                if (opplan->getQuantity() > 0 &&
                    opplan->getQuantity() <= newQty + ROUNDING_ERROR &&
                    opplan->getEnd() <= originalOpplan.end) {
                  // The squeezing did work!
                  // The operationplan quantity is now reduced. The buffer
                  // solver will ask again for the remaining short quantity, so
                  // we don't need to bother about that here.
                  overloadQty = 0.0;
                  data->state->a_qty = -data->state->q_loadplan->getQuantity();
                } else {
                  // It didn't work. Restore the original operationplan.
                  opplan->restore(tmp);
                }
              }
            }
          } else {
            // Move the operationplan to load 1 second in the bucket with
            // available capacity
            Date tmp = data->state->q_loadplan->getLoad()->getOperationPlanDate(
                data->state->q_loadplan, newStart.getStart(), true);
            opplan->setStart(tmp);
          }

          // Verify the move is successfull
          if (!moved ||
              data->state->q_loadplan->getDate() > newStart.getStart())
            // The new loadplan is expected to be at the requested date or
            // earlier (eg in the presence of availability calendars)
            data->state->a_qty = 0.0;
          else if (data->constrainedPlanning &&
                   isLeadTimeConstrained(opplan->getOperation())) {
            // Check the leadtime constraints after the move
            // Note that the check function can update the answered date
            // and quantity
            checkOperationLeadTime(opplan, *data, false);
            if (data->state->a_qty && time_per_logic) {
              if (opplan->getStart() >= bucketEnd)
                // The lead time check moved the operationplan to a later bucket
                // again
                data->state->a_qty = 0.0;
              else {
                // Doublecheck whether there are overloads
                auto bckt = data->state->q_loadplan->getBucketEnd();
                overloadQty = get<0>(bckt);
              }
            }
          }
        } else {
          // No earlier capacity found: get out of the loop
          data->state->a_qty = 0.0;
          if (data->hitMaxEarly < res->getMaxEarly())
            data->hitMaxEarly = res->getMaxEarly();
        }
      }  // End of if-statement, solve by moving earlier
    } while (overloadQty < -ROUNDING_ERROR && data->state->a_qty != 0.0);

  // Loop for a valid location by using LATER capacity
  // If the answered quantity is 0, the operationplan is moved into the past.
  // Or, the solver may be forced to produce a late reply.
  // In these cases we need to search for capacity at later dates.
  if (data->state->a_qty == 0.0 ||
      (data->state->forceLate && overloadQty < -ROUNDING_ERROR)) {
    if (!data->constrainedPlanning)
      data->state->a_qty = 0.0;
    else {
      bool firstBucket = true;
      bool hasOverloadInFirstBucket = true;

      // Put the operationplan back at its original end date
      if (time_per_logic)
        opplan->setOperationPlanParameters(
            originalOpplan.quantity, Date::infinitePast, originalOpplan.end,
            true, true, false);
      else if (!noRestore)
        opplan->restore(originalOpplan);

      // Search for a bucket with available capacity.
      Date newDate;
      Date prevStart = data->state->q_loadplan->getDate();
      double availableQty = 0.0;
      for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
           cur != res->getLoadPlans().end(); ++cur) {
        if (cur->getEventType() != 2)
          // Not a new bucket
          availableQty = cur->getOnhand();
        else if (availableQty > ROUNDING_ERROR) {
          if (firstBucket) {
            if (data->state->a_qty && noRestore) {
              // Not a real overload
              hasOverloadInFirstBucket = false;
            }
            firstBucket = false;
          }
          if (time_per_logic) {
            // Move to the new bucket
            opplan->setOperationPlanParameters(originalOpplan.quantity,
                                               prevStart, Date::infinitePast,
                                               true, true, false);
            if (data->state->q_loadplan->getDate() < cur->getDate()) {
              auto bucketend = data->state->q_loadplan->getBucketEnd();
              if (get<0>(bucketend) > ROUNDING_ERROR) {
                // Valid new bucket found: has available time and capacity
                newDate = opplan->getStart();
                // Increase the size to use all available capacity in the bucket
                double newQty = originalOpplan.quantity;
                opplan->setOperationPlanParameters(newQty, opplan->getStart(),
                                                   Date::infinitePast, true,
                                                   true, true);
                break;
              } else {
                // New bucket starts
                prevStart = cur->getDate();
                availableQty = cur->getOnhand();
              }
            } else {
              // New bucket starts
              prevStart = cur->getDate();
              availableQty = cur->getOnhand();
            }
          } else {
            // Find a suitable start date in this bucket
            Duration tmp;
            DateRange newStart = opplan->getOperation()->calculateOperationTime(
                opplan, prevStart, Duration(1L), true, &tmp);
            if (newStart.getStart() < cur->getDate()) {
              // If the new start date is within this bucket we just left, then
              // we have found a bucket with available capacity left
              newDate = newStart.getStart();
              break;
            } else {
              // New bucket starts
              prevStart = cur->getDate();
              availableQty = cur->getOnhand();
            }
          }
        } else {
          // New bucket starts
          prevStart = cur->getDate();
          availableQty = cur->getOnhand();
        }
      }

      Date effective_end =
          data->state->q_loadplan->getLoad()->getEffective().getEnd();
      if ((!newDate || newDate > effective_end) &&
          effective_end != Date::infiniteFuture) {
        // The load has effectivity, and when it expires we can return a
        // positive reply
        if (effective_end > originalOpplan.end) newDate = effective_end;
      }

      if (!hasOverloadInFirstBucket && !data->state->forceLate) {
        // Actually, there was no problem
        data->state->a_date = data->state->q_date;
        data->state->a_qty = orig_q_qty;
      } else if (newDate || newDate == Date::infiniteFuture) {
        if (!time_per_logic) {
          // Move the operationplan to the new bucket and resize to the minimum.
          // Set the date where a next trial date can happen.
          double q = opplan->getOperation()->getSizeMinimum();
          if (opplan->getOperation()->getSizeMinimumCalendar()) {
            // Minimum size varies over time
            double curmin =
                opplan->getOperation()->getSizeMinimumCalendar()->getValue(
                    newDate);
            if (q < curmin) q = curmin;
          }
          if (q < data->state->q_qty_min) q = data->state->q_qty_min;
          opplan->setQuantity(q);
          Date tmp = data->state->q_loadplan->getLoad()->getOperationPlanDate(
              data->state->q_loadplan, newDate, true);
          opplan->setOperationPlanParameters(q, tmp, Date::infinitePast);
        }
        data->state->a_date = opplan->getEnd();
        data->state->a_qty = 0.0;
      } else {
        // No available capacity found anywhere in the horizon
        data->state->a_date = Date::infiniteFuture;
        data->state->a_qty = 0.0;
      }
    }
  }

  if (time_per_logic && !data->state->a_qty &&
      data->state->a_date <= originalOpplan.end) {
    data->state->a_date =
        originalOpplan.end + data->getSolver()->getLazyDelay();
  }

  // Force ok in unconstrained plan
  if (!data->constrainedPlanning && data->state->a_qty == 0.0) {
    opplan->restore(originalOpplan);
    data->state->a_date = data->state->q_date;
    data->state->a_qty = orig_q_qty;
  }

  // Increment the cost
  if (data->state->a_qty > 0.0) {
    // Resource usage
    auto tmp = data->state->a_qty * res->getCost() *
               (opplan->getDates().getDuration() - opplan->getUnavailable()) /
               3600.0;
    data->state->a_cost += tmp;
    if (data->logcosts && data->incostevaluation)
      logger << indentlevel << "     + cost on resource '" << res
             << "': " << tmp << '\n';

    // Build-ahead penalty: 5% of the cost   @todo buildahead penalty is
    // hardcoded
    if (originalOpplan.end > opplan->getEnd())
      data->state->a_penalty += (originalOpplan.end - opplan->getEnd()) *
                                (res->getCost() > 0 ? res->getCost() : 1.0) *
                                0.05 / 3600.0;
  }

  // Maintain the constraint list
  if (data->state->a_qty == 0.0 && data->logConstraints && data->constraints)
    data->constraints->push(ProblemCapacityOverload::metadata, res,
                            originalOpplan.start, originalOpplan.end, 0.0,
                            opplan->getOperation());

  if (data->state->a_qty < orig_q_qty - ROUNDING_ERROR)
    data->accept_partial_reply = true;

  if (originalOpplan.start > data->state->q_operationplan->getStart() &&
      data->logConstraints && data->constraints) {
    // Using earlier capacity is logged as a constraint.
    // If the resource isn't on the critical path that constraint will later be
    // filtered out again.
    data->constraints->push(ProblemCapacityOverload::metadata, res,
                            originalOpplan.start,
                            data->state->q_operationplan->getStart(), 0.0,
                            data->state->q_operationplan->getOperation(), true);
  }

  // Message
  if (getLogLevel() > 1 && data->state->q_qty < 0) {
    logger << indentlevel-- << "Bucketized resource '" << res
           << "' answers: " << data->state->a_qty;
    if (!data->state->a_qty)
      logger << "  " << data->state->a_date;
    else if (originalOpplan.start > data->state->q_operationplan->getStart())
      logger << " using earlier capacity "
             << data->state->q_operationplan->getStart();
    logger << '\n';
  }
}

}  // namespace frepple
