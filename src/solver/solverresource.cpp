/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/solver.h"

namespace frepple
{


/** @todo resource solver should be using a move command rather than direct move */
void SolverMRP::solve(const Resource* res, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_resource) userexit_resource.call(res, PythonData(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1)
  {
    if (!data->constrainedPlanning || !data->getSolver()->isConstrained())
      logger << indent(res->getLevel()) << "   Resource '" << res->getName()
        << "' is asked in unconstrained mode: "<< (-data->state->q_qty) << "  "
        << data->state->q_operationplan->getDates() << endl;
    else
      logger << indent(res->getLevel()) << "   Resource '" << res->getName()
        << "' is asked: "<< (-data->state->q_qty) << "  "
        << data->state->q_operationplan->getDates() << endl;
  }

  // Find the setup operationplan
  OperationPlan *setupOpplan = nullptr;
  DateRange currentSetupOpplanDates;
  LoadPlan *setupLdplan = nullptr;
  if (res->getSetupMatrix() && !data->state->q_loadplan->getLoad()->getSetup().empty())
    for (OperationPlan::iterator i(data->state->q_operationplan); i != OperationPlan::end(); ++i)
      if (i->getOperation() == OperationSetup::setupoperation)
      {
        setupOpplan = &*i;
        currentSetupOpplanDates = i->getDates();
        for (OperationPlan::LoadPlanIterator j = setupOpplan->beginLoadPlans();
          j != setupOpplan->endLoadPlans(); ++j)
          if (j->getLoad()->getResource() == res && !j->isStart())
          {
            setupLdplan = &*j;
            break;
          }
        if (!setupLdplan)
          throw LogicException("Can't find loadplan on setup operationplan");
        break;
      }

  // Initialize some variables
  double orig_q_qty = -data->state->q_qty;
  OperationPlanState currentOpplan(data->state->q_operationplan);
  Resource::loadplanlist::const_iterator cur = res->getLoadPlans().end();
  Date curdate;
  double curMax, prevMax;
  bool HasOverload;
  bool HasSetupOverload;
  bool noRestore = data->state->forceLate;

  // Initialize the default reply
  data->state->a_date = data->state->q_date;
  data->state->a_qty = orig_q_qty;
  Date prevdate;

  // Loop for a valid location by using EARLIER capacity
  if (!data->state->forceLate)
    do
    {
      // Check the leadtime constraints
      prevdate = data->state->q_operationplan->getDates().getEnd();
      noRestore = data->state->forceLate;

      if (isLeadTimeConstrained() || isFenceConstrained())
        // Note that the check function can update the answered date and quantity
         if (data->constrainedPlanning && !checkOperationLeadTime(data->state->q_operationplan,*data,false))
         {
           // Operationplan violates the lead time and/or fence constraint
           noRestore = true;
           break;
         }

      // Check if this operation overloads the resource at its current time
      HasOverload = false;
      HasSetupOverload = false;
      Date earliestdate = data->state->q_operationplan->getDates().getStart();
      curdate = data->state->q_loadplan->getDate();
      curMax = data->state->q_loadplan->getMax(false);
      prevMax = curMax;
      for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
        cur!=res->getLoadPlans().end() && cur->getDate()>=earliestdate;
        --cur)
      {
        // A change in the maximum capacity
        prevMax = curMax;
        if (cur->getEventType() == 4)
          curMax = cur->getMax(false);

        const LoadPlan* ldplan = nullptr;
        if (cur->getEventType() == 1)
          ldplan = static_cast<const LoadPlan*>(&*cur);
        if (ldplan && ldplan->getOperationPlan()->getOperation() == OperationSetup::setupoperation
          && ldplan->getOperationPlan()->getDates().overlap(data->state->q_operationplan->getDates()) > 0L
          && ldplan->getOperationPlan() != setupOpplan)
        {
          // Ongoing setup
          HasOverload = true;
          HasSetupOverload = true;
          break;
        }

        // Not interested if date doesn't change
        if (cur->getDate() == curdate) continue;

        if (cur->getOnhand() > prevMax + ROUNDING_ERROR)
        {
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

      // Check if the setup operationplan overloads the resource or if a
      // different setup is already active on the resource.
      if (setupOpplan && !HasOverload)
      {
        earliestdate = setupOpplan->getDates().getStart();
        for (cur = res->getLoadPlans().begin(setupLdplan);
          cur!=res->getLoadPlans().end() && cur->getDate()>=earliestdate;
          --cur)
        {
          // A change in the maximum capacity
          prevMax = curMax;
          if (cur->getEventType() == 4)
            curMax = cur->getMax(false);

          // Must be same setup
          const LoadPlan* ldplan = nullptr;
          if (cur->getEventType() == 1)
            ldplan = static_cast<const LoadPlan*>(&*cur);
          if (ldplan
            && ldplan->getOperationPlan()->getDates().overlap(setupOpplan->getDates()) > 0L
            && ldplan->getSetup() != setupLdplan->getSetup())
          {
            HasOverload = true;
            HasSetupOverload = true;
            break;
          }

          // Not interested if date doesn't change
          if (cur->getDate() == curdate) continue;
          if (cur->getOnhand() > prevMax + ROUNDING_ERROR)
          {
            // Overload: We are exceeding the limit!
            // At this point:
            //  - cur points to a loadplan where we exceed the capacity
            //  - curdate points to the latest date without overload
            //  - curdate != cur->getDate()
            HasOverload = true;
            HasSetupOverload = true;
            break;
          }
          curdate = cur->getDate();
        }
      }

      // Try solving the overload by resizing the operationplan.
      // The capacity isn't overloaded in the time between "curdate" and
      // "current end of the operationplan". We can try to resize the
      // operationplan to fit in this time period...
      if (HasOverload && !HasSetupOverload
        && curdate < data->state->q_loadplan->getDate()
        && data->getSolver()->getAllowSplits())
      {
        Date currentEnd = data->state->q_operationplan->getDates().getEnd();
        data->state->q_operationplan->getOperation()->setOperationPlanParameters(
          data->state->q_operationplan,
          currentOpplan.quantity,
          curdate,
          currentEnd
          );
        if (data->state->q_operationplan->getQuantity() > 0
          && data->state->q_operationplan->getDates().getEnd() <= currentEnd
          && data->state->q_operationplan->getDates().getStart() >= curdate)
        {
          // The squeezing did work!
          // The operationplan quantity is now reduced. The buffer solver will
          // ask again for the remaining short quantity, so we don't need to
          // bother about that here.
          HasOverload = false;
        }
        else
        {
          // It didn't work. Restore the original operationplan.
          // @todo this undoing is a performance bottleneck: trying to resize
          // and restoring the original are causing lots of updates in the
          // buffer and resource timelines...
          // We need an api that only checks the resizing.
          data->state->q_operationplan->getOperation()->setOperationPlanParameters(
            data->state->q_operationplan,
            currentOpplan.quantity,
            Date::infinitePast,
            currentEnd
            );
        }
      }

      // Try solving the overload by moving the operationplan to an earlier date
      if (HasOverload)
      {
        // Search backward in time for a period where there is no overload
        curMax = cur->getMax(false);
        prevMax = curMax;
        curdate = cur->getDate();
        for (; cur!=res->getLoadPlans().end() && curdate > currentOpplan.end - res->getMaxEarly(); --cur)
        {
          // A change in the maximum capacity
          prevMax = curMax;
          if (cur->getEventType() == 4) curMax = cur->getMax(false);

          // Ongoing setup
          const LoadPlan* ldplan = nullptr;
          if (cur->getEventType() == 1)
            ldplan = static_cast<const LoadPlan*>(&*cur);
          if (ldplan
            && ldplan->getOperationPlan()->getOperation() == OperationSetup::setupoperation
            && ldplan->isStart()
            && ldplan->getOperationPlan()->getDates().getDuration() > 0L
            && ldplan->getOperationPlan() != setupOpplan)
            continue;

          // Not interested if date doesn't change
          if (cur->getDate() == curdate) continue;

          // We are below the max limit now.
          if (cur->getOnhand() < prevMax + ROUNDING_ERROR && curdate < prevdate)
            break;
          curdate = cur->getDate();
        }
        assert (curdate != prevdate);

        // We found a date where the load goes below the maximum
        // At this point:
        //  - curdate is a latest date where we are above the maximum
        //  - cur is the first loadplan where we are below the max
        if (cur != res->getLoadPlans().end() && curdate > currentOpplan.end - res->getMaxEarly())
        {
          // Move the operationplan
          data->state->q_operationplan->setEnd(curdate);

          // Verify the move is successfull
          if (data->state->q_operationplan->getDates().getEnd() > curdate
            || data->state->q_operationplan->getQuantity() == 0.0)
            // If there isn't available time in the location calendar, the move
            // can fail.
            data->state->a_qty = 0.0;
          else if (data->constrainedPlanning && (isLeadTimeConstrained() || isFenceConstrained()))
            // Check the leadtime constraints after the move
            // Note that the check function can update the answered date
            // and quantity
            checkOperationLeadTime(data->state->q_operationplan,*data,false);
        }
        else
          // No earlier capacity found: get out of the loop
          data->state->a_qty = 0.0;
      }  // End of if-statement, solve by moving earlier
    }
    while (HasOverload && data->state->a_qty!=0.0);

  // Loop for a valid location by using LATER capacity
  // If the answered quantity is 0, the operationplan is moved into the past.
  // Or, the solver may be forced to produce a late reply.
  // In these cases we need to search for capacity at later dates.
  if (data->constrainedPlanning && (data->state->a_qty == 0.0 || data->state->forceLate))
  {
    // Put the operationplan back at its original end date
    if (!noRestore)
      data->state->q_operationplan->restore(currentOpplan);

    // Moving an operation earlier is driven by the ending loadplan,
    // while searching for later capacity is driven from the starting loadplan.
    LoadPlan* old_q_loadplan = data->state->q_loadplan;
    data->state->q_loadplan = data->state->q_loadplan->getOtherLoadPlan();

    // Loop to find a later date where the operationplan will fit
    Date newDate;
    do
    {
      // Search for a date where we go below the maximum load.
      // and verify whether there are still some overloads
      HasOverload = false;
      newDate = Date::infinitePast;
      curMax = data->state->q_loadplan->getMax();
      double curOnhand = data->state->q_loadplan->getOnhand();

      // Find how many uncommitted operationplans are loading the resource
      // before the loadplan.
      // If the same resource is used multiple times in the supply path of a
      // demand we need to use only the capacity used by other demands. Otherwise
      // our estimate is of the feasible next date is too pessimistic.
      // If the operation is the same, the operationplans are at the same stage
      // in the supply path and we need to include these in our estimate of the
      // next date.
      double ignored = 0.0;
      for (cur = res->getLoadPlans().begin(); cur!=res->getLoadPlans().begin(data->state->q_loadplan); ++cur)
      {
        const LoadPlan* ldplan = nullptr;
        if (cur->getEventType() == 1)
          ldplan = static_cast<const LoadPlan*>(&*cur);
        if (ldplan && !ldplan->getOperationPlan()->getRawIdentifier()
          && ldplan->getOperationPlan()->getOperation()!=data->state->q_operationplan->getOperation() )
          ignored += ldplan->getQuantity();
      }

      for (cur=res->getLoadPlans().begin(data->state->q_loadplan);
          !(HasOverload && newDate) && cur != res->getLoadPlans().end(); )
      {
        // New maximum
        if (cur->getEventType() == 4)
          curMax = cur->getMax();

        /* @todo is this required?
        const LoadPlan* ldplan = nullptr;
        if (cur->getType() == 1)
          ldplan = static_cast<const LoadPlan*>(&*cur);
        if (ldplan && ldplan->getOperationPlan()->getOperation() == OperationSetup::setupoperation
          && ldplan->getOperationPlan()->getDates().getDuration() > 0L)
        {
          // Ongoing setup
          HasOverload = true;
          ++cur;
          continue;
        }
        */
        const LoadPlan* ldplan = nullptr;
        if (cur->getEventType() == 1)
          ldplan = static_cast<const LoadPlan*>(&*cur);
        if (ldplan && !ldplan->getOperationPlan()->getRawIdentifier()
          && ldplan->getOperationPlan()->getOperation()!=data->state->q_operationplan->getOperation())
          ignored += ldplan->getQuantity();

        // Only consider the last loadplan for a certain date
        const TimeLine<LoadPlan>::Event *loadpl = &*(cur++);
        if (cur!=res->getLoadPlans().end() && cur->getDate()==loadpl->getDate())
          continue;
        curOnhand = loadpl->getOnhand();

        // Check if overloaded
        if (loadpl->getOnhand() - ignored > curMax + ROUNDING_ERROR)
          // There is still a capacity problem
          HasOverload = true;
        else if (!HasOverload && loadpl->getDate() > data->state->q_operationplan->getDates().getEnd())
          // Break out of loop if no overload and we're beyond the
          // operationplan end date.
          break;
        else if (!newDate && loadpl->getDate()!=data->state->q_loadplan->getDate() && curMax >= fabs(loadpl->getQuantity()))
        {
          // We are below the max limit for the first time now.
          // This means that the previous date may be a proper start.
          newDate = loadpl->getDate();
        }
      }

      // Found a date with available capacity
      if (HasOverload && newDate)
      {
        // Multiple operations could be executed in parallel
        int parallelOps = static_cast<int>((curMax - curOnhand) / data->state->q_loadplan->getQuantity());
        if (parallelOps <= 0) parallelOps = 1;
        // Move the operationplan to the new date
        data->state->q_operationplan->getOperation()->setOperationPlanParameters(
            data->state->q_operationplan,
            (currentOpplan.quantity ? currentOpplan.quantity : 0.001) / parallelOps, // 0.001  @todo this calculation doesn't give minimization of the lateness
            newDate,
            Date::infinitePast
            );
        HasOverload = true;
        if (data->state->q_operationplan->getDates().getStart() < newDate)
          // Moving to the new date turns out to be infeasible! Give it up.
          // For instance, this can happen when the location calendar doesn't
          // have any up-time after the specified date.
          break;
      }
    }
    while (HasOverload && newDate);
    data->state->q_loadplan = old_q_loadplan;

    // Set the date where a next trial date can happen
    if (HasOverload)
      // No available capacity found anywhere in the horizon
      data->state->a_date = Date::infiniteFuture;
    else
      data->state->a_date = data->state->q_operationplan->getDates().getEnd();

    // Create a zero quantity reply
    data->state->a_qty = 0.0;
  }

  // Force ok in unconstrained plan
  if (!data->constrainedPlanning && data->state->a_qty == 0.0)
  {
    data->state->q_operationplan->restore(currentOpplan);
    data->state->a_date = data->state->q_date;
    data->state->a_qty = orig_q_qty;
  }

  // Increment the cost
  if (data->state->a_qty > 0.0)
  {
    // Resource usage
    data->state->a_cost += data->state->a_qty * res->getCost()
       * (data->state->q_operationplan->getDates().getDuration() - data->state->q_operationplan->getUnavailable()) / 3600.0;
    // Setup penalty and cost
    if (setupOpplan)
    {
      data->state->a_cost += data->state->a_qty * res->getCost()
       * (setupOpplan->getDates().getDuration() - setupOpplan->getUnavailable()) / 3600.0;
      data->state->a_penalty += setupOpplan->getPenalty();
    }
    // Build-ahead penalty: 5% of the cost   @todo buildahead penalty is hardcoded
    if (currentOpplan.end > data->state->q_operationplan->getDates().getEnd())
      data->state->a_penalty +=
        (currentOpplan.end - data->state->q_operationplan->getDates().getEnd()) * res->getCost() * 0.05 / 3600.0;
  }

  // Maintain the constraint list
  if (data->state->a_qty == 0.0 && data->logConstraints && data->planningDemand)
    data->planningDemand->getConstraints().push(
      ProblemCapacityOverload::metadata,
      res, currentOpplan.start, currentOpplan.end, orig_q_qty);

  // Message
  if (data->getSolver()->getLogLevel()>1)
  {
    logger << indent(res->getLevel()) << "   Resource '" << res << "' answers: "
      << data->state->a_qty << "  " << data->state->a_date;
    if (currentOpplan.end > data->state->q_operationplan->getDates().getEnd())
      logger << " using earlier capacity "
        << data->state->q_operationplan->getDates().getEnd();
    if (data->state->a_qty>0.0 && data->state->q_operationplan->getQuantity() < currentOpplan.quantity)
      logger << " with reduced quantity " << data->state->q_operationplan->getQuantity();
    logger << endl;
  }

}


void SolverMRP::solve(const ResourceInfinite* res, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_resource) userexit_resource.call(res, PythonData(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "   Infinite resource '" << res << "' is asked: "
    << (-data->state->q_qty) << "  " << data->state->q_operationplan->getDates() << endl;

  // @todo Need to make the setups feasible - move to earlier dates till max_early fence is reached

  // Reply whatever is requested, regardless of date and quantity.
  data->state->a_qty = data->state->q_qty;
  data->state->a_date = data->state->q_date;
  data->state->a_cost += data->state->a_qty * res->getCost()
    * (data->state->q_operationplan->getDates().getDuration() - data->state->q_operationplan->getUnavailable())
    / 3600.0;

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "   Infinite resource '" << res << "' answers: "
    << (-data->state->a_qty) << "  " << data->state->a_date << endl;
}


void SolverMRP::solve(const ResourceBuckets* res, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_resource) userexit_resource.call(res, PythonData(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "   Bucketized resource '" << res << "' is asked: "
    << (-data->state->q_qty) << "  " << data->state->q_operationplan->getDates() << endl;

  // Initialize some variables
  double orig_q_qty = -data->state->q_qty;
  OperationPlanState currentOpplan(data->state->q_operationplan);
  Resource::loadplanlist::const_iterator cur = res->getLoadPlans().end();
  Date curdate;
  bool noRestore = data->state->forceLate;
  double overloadQty = 0.0;

  // Initialize the default reply
  data->state->a_date = data->state->q_date;
  data->state->a_qty = orig_q_qty;
  Date prevdate;

  // Compute the minimum free capacity we need in a bucket
  double min_free_quantity =
    data->state->q_loadplan->getLoad()->getEffective() ?
      // Conservative threshold when the load is date effective
      ROUNDING_ERROR :
      // Minimum operation size multiplied with load size
      (data->state->q_operationplan->getOperation()->setOperationPlanQuantity(
        data->state->q_operationplan, 0.01, false, false, false, Date::infinitePast
        ) * data->state->q_loadplan->getLoad()->getQuantity());

  // Loop for a valid location by using EARLIER capacity
  if (!data->state->forceLate)
    do
    {
      // Check the leadtime constraints
      prevdate = data->state->q_operationplan->getDates().getEnd();
      noRestore = data->state->forceLate;

      if (isLeadTimeConstrained() || isFenceConstrained())
        // Note that the check function can update the answered date and quantity
         if (data->constrainedPlanning && !checkOperationLeadTime(data->state->q_operationplan,*data,false))
         {
           // Operationplan violates the lead time and/or fence constraint
           noRestore = true;
           break;
         }

      // Check if this operation overloads the resource bucket
      overloadQty = 0.0;
      for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
        cur != res->getLoadPlans().end() && cur->getEventType() != 2;
        ++cur)
        if (cur->getOnhand() < overloadQty)
          overloadQty = cur->getOnhand();

      // Solve the overload in the bucket by resizing the operationplan.
      // If the complete operationplan is overload then we can skip this step.
      // Because of operation size constraints (minimum and multiple values)
      // it is possible that the resizing fails.
      if (overloadQty < 0 && orig_q_qty > -overloadQty - ROUNDING_ERROR
        && data->state->q_loadplan->getLoad()->getQuantity())
      {
        Date oldEnd = data->state->q_operationplan->getDates().getEnd();
        double oldQty = data->state->q_operationplan->getQuantity();
        double newQty = oldQty + overloadQty / data->state->q_loadplan->getLoad()->getQuantity();
        if (newQty > ROUNDING_ERROR)
        {
          data->state->q_operationplan->getOperation()->setOperationPlanParameters(
            data->state->q_operationplan,
            newQty,
            Date::infinitePast,
            oldEnd
            );
          if (data->state->q_operationplan->getQuantity() > 0
            && data->state->q_operationplan->getQuantity() <= newQty + ROUNDING_ERROR
            && data->state->q_operationplan->getDates().getEnd() <= oldEnd)
          {
            // The squeezing did work!
            // The operationplan quantity is now reduced. The buffer solver will
            // ask again for the remaining short quantity, so we don't need to
            // bother about that here.
            overloadQty = 0.0;
            data->state->a_qty = -data->state->q_loadplan->getQuantity();
            // With operations of type time_per, it is also possible that the
            // operation now consumes capacity in a different bucket.
            // If that's the case, we move it to start right at the end of the bucket.
            if (cur!=res->getLoadPlans().end() &&
              data->state->q_operationplan->getDates().getStart() > cur->getDate())
                data->state->q_operationplan->setStart(cur->getDate() - Duration(1L));
          }
          else
          {
            // It didn't work. Restore the original operationplan.
            // @todo this undoing is a performance bottleneck: trying to resize
            // and restoring the original are causing lots of updates in the
            // buffer and resource timelines...
            // We need an api that only checks the resizing.
            data->state->q_operationplan->getOperation()->setOperationPlanParameters(
              data->state->q_operationplan,
              oldQty,
              Date::infinitePast,
              oldEnd
              );
          }
        }
      }

      // Try solving the overload by moving the operationplan to an earlier date
      if (overloadQty < 0)
      {
        // Search backward in time for a bucket that still has capacity left
        Date bucketEnd;
        DateRange newStart;
        for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
          cur!=res->getLoadPlans().end() && cur->getDate() > currentOpplan.end - res->getMaxEarly();)
        {
          if (cur->getEventType() != 2)
          {
            --cur;
            continue;
          }
          bucketEnd = cur->getDate();
          --cur;  // Move to last loadplan in the previous bucket
          if (cur != res->getLoadPlans().end() && cur->getOnhand() > min_free_quantity)
          {
            // Find a suitable start date in this bucket
            Duration tmp;
            newStart = data->state->q_operationplan->getOperation()->calculateOperationTime(
              bucketEnd, Duration(1L), false, &tmp
              );
            // Move to the start of the bucket
            while (cur!=res->getLoadPlans().end() && cur->getEventType() != 2) --cur;
            // If the new start date is within this bucket we have found a
            // bucket with available capacity left
            if (cur==res->getLoadPlans().end() || cur->getDate() <= newStart.getStart())
              break;
          }
        }

        // We found a date where the load goes below the maximum
        // At this point newStart.getStart() is a date in a bucket where
        // capacity is still available.
        if (bucketEnd && newStart.getStart() >= currentOpplan.end - res->getMaxEarly())
        {
          // Move the operationplan to start 1 second in the bucket with available capacity
          data->state->q_operationplan->setStart(newStart.getStart());

          // Verify the move is successfull
          if (data->state->q_operationplan->getDates().getStart() != newStart.getStart())
            // Not sure if there are cases where this will fail, but just
            // in case...
            data->state->a_qty = 0.0;
          else if (data->constrainedPlanning && (isLeadTimeConstrained() || isFenceConstrained()))
            // Check the leadtime constraints after the move
            // Note that the check function can update the answered date
            // and quantity
            checkOperationLeadTime(data->state->q_operationplan,*data,false);
        }
        else
          // No earlier capacity found: get out of the loop
          data->state->a_qty = 0.0;
      }  // End of if-statement, solve by moving earlier
    }
    while (overloadQty < 0 && data->state->a_qty!=0.0);

  // Loop for a valid location by using LATER capacity
  // If the answered quantity is 0, the operationplan is moved into the past.
  // Or, the solver may be forced to produce a late reply.
  // In these cases we need to search for capacity at later dates.
  if (data->constrainedPlanning && (data->state->a_qty == 0.0 || data->state->forceLate))
  {
    // Put the operationplan back at its original end date
    if (!noRestore)
      data->state->q_operationplan->restore(currentOpplan);

    // Search for a bucket with available capacity.
    Date newDate;
    Date prevStart = data->state->q_loadplan->getDate();
    overloadQty = 0.0;
    for (cur = res->getLoadPlans().begin(data->state->q_loadplan);
      cur!=res->getLoadPlans().end(); ++cur)
    {
      if (cur->getEventType() != 2)
        // Not a new bucket
        overloadQty = cur->getOnhand();
      else if (overloadQty > min_free_quantity)
      {
        // Find a suitable start date in this bucket
        Duration tmp;
        DateRange newStart = data->state->q_operationplan->getOperation()->calculateOperationTime(
          prevStart, Duration(1L), true, &tmp
          );
        if (newStart.getStart() < cur->getDate())
        {
          // If the new start date is within this bucket we just left, then
          // we have found a bucket with available capacity left
          newDate = newStart.getStart();
          break;
        }
        else
        {
          // New bucket starts
          prevStart = cur->getDate();
          overloadQty = cur->getOnhand();
        }
      }
      else
      {
        // New bucket starts
        prevStart = cur->getDate();
        overloadQty = cur->getOnhand();
      }
    }
    if (newDate)
    {
      // Move the operationplan to the new bucket and resize to the minimum.
      // Set the date where a next trial date can happen.
      data->state->q_operationplan->getOperation()->setOperationPlanParameters(
        data->state->q_operationplan,
        data->state->q_operationplan->getOperation()->getSizeMinimum(),
        newDate,
        Date::infinitePast
        );
      data->state->a_date = data->state->q_operationplan->getDates().getEnd();
    }
    else
      // No available capacity found anywhere in the horizon
      data->state->a_date = Date::infiniteFuture;

    // Create a zero quantity reply
    data->state->a_qty = 0.0;
  }

  // Force ok in unconstrained plan
  if (!data->constrainedPlanning && data->state->a_qty == 0.0)
  {
    data->state->q_operationplan->restore(currentOpplan);
    data->state->a_date = data->state->q_date;
    data->state->a_qty = orig_q_qty;
  }

  // Increment the cost
  if (data->state->a_qty > 0.0)
  {
    // Resource usage
    data->state->a_cost += data->state->a_qty * res->getCost()
       * (data->state->q_operationplan->getDates().getDuration() - data->state->q_operationplan->getUnavailable()) / 3600.0;
    // Build-ahead penalty: 5% of the cost   @todo buildahead penalty is hardcoded
    if (currentOpplan.end > data->state->q_operationplan->getDates().getEnd())
      data->state->a_penalty +=
        (currentOpplan.end - data->state->q_operationplan->getDates().getEnd()) * res->getCost() * 0.05 / 3600.0;
  }

  // Maintain the constraint list
  if (data->state->a_qty == 0.0 && data->logConstraints && data->planningDemand)
    data->planningDemand->getConstraints().push(
      ProblemCapacityOverload::metadata,
      res, currentOpplan.start, currentOpplan.end, orig_q_qty);

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "   Bucketized resource '" << res << "' answers: "
    << data->state->a_qty << "  " << data->state->a_date << endl;
}


}
