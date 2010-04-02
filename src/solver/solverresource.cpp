/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye                                    *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Lesser General Public License as published   *
 * by the Free Software Foundation; either version 2.1 of the License, or  *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser *
 * General Public License for more details.                                *
 *                                                                         *
 * You should have received a copy of the GNU Lesser General Public        *
 * License along with this library; if not, write to the Free Software     *
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/solver.h"

namespace frepple
{


/** @todo resource solver should be using a move command rather than direct move */
DECLARE_EXPORT void SolverMRP::solve(const Resource* res, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_resource) userexit_resource.call(res, PythonObject(data->constrainedPlanning));

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

  // Unconstrained plan
  if (!data->constrainedPlanning)
  {
    // Reply whatever is requested, regardless of date and quantity.
    data->state->a_qty = data->state->q_qty;
    data->state->a_date = data->state->q_date;
    data->state->a_cost += data->state->a_qty * res->getCost()
      * (data->state->q_operationplan->getDates().getDuration() - data->state->q_operationplan->getUnavailable()) 
      / 3600.0;

    // Message
    if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
      logger << indent(res->getLevel()) << "  Resource '" << res << "' answers: "
      << (-data->state->a_qty) << "  " << data->state->a_date << endl;
  }

  // Find the setup operationplan
  OperationPlan *setupOpplan = NULL;
  DateRange currentSetupOpplanDates;
  LoadPlan *setupLdplan = NULL;
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

      if (isLeadtimeConstrained() || isFenceConstrained())
        // Note that the check function can update the answered date and quantity
         if (data->constrainedPlanning && !checkOperationLeadtime(data->state->q_operationplan,*data,false))
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
        if (cur->getType() == 4)
          curMax = cur->getMax(false);

        const LoadPlan* ldplan = dynamic_cast<const LoadPlan*>(&*cur);
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
          if (cur->getType() == 4)
            curMax = cur->getMax(false);

          // Must be same setup
          const LoadPlan* ldplan = dynamic_cast<const LoadPlan*>(&*cur);
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
        && curdate < data->state->q_loadplan->getDate())
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
          if (cur->getType() == 4) curMax = cur->getMax(false);

          // Ongoing setup
          const LoadPlan* ldplan = dynamic_cast<const LoadPlan*>(&*cur);
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

          // Check the leadtime constraints after the move
          if (data->constrainedPlanning && (isLeadtimeConstrained() || isFenceConstrained()))
            // Note that the check function can update the answered date
            // and quantity
            checkOperationLeadtime(data->state->q_operationplan,*data,false);
        }
        else
          // No earlier capacity found: get out of the loop
          data->state->a_qty = 0.0;
      }  // End of if-statement, solve by moving earlier
    }
    while (HasOverload && data->state->a_qty!=0.0);

  // Loop for a valid location by using LATER capacity
  // If the answered quantity is 0, the operationplan is moved into the
  // past.
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
      for (cur=res->getLoadPlans().begin(data->state->q_loadplan);
          !(HasOverload && newDate) && cur != res->getLoadPlans().end(); )
      {
        // New maximum
        if (cur->getType() == 4)
          curMax = cur->getMax();

        /* xxx
        const LoadPlan* ldplan = dynamic_cast<const LoadPlan*>(&*cur);
        if (ldplan && ldplan->getOperationPlan()->getOperation() == OperationSetup::setupoperation
          && ldplan->getOperationPlan()->getDates().getDuration() > 0L)
        {
          // Ongoing setup
          HasOverload = true;
          ++cur;
          continue;
        }
        */

        // Only consider the last loadplan for a certain date
        const TimeLine<LoadPlan>::Event *loadpl = &*(cur++);
        if (cur!=res->getLoadPlans().end() && cur->getDate()==loadpl->getDate())
          continue;
        curOnhand = loadpl->getOnhand();

        // Check if overloaded
        if (loadpl->getOnhand() > curMax + ROUNDING_ERROR)
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
            currentOpplan.quantity / parallelOps, // 0.001  @todo this calculation doesn't give minimization of the lateness
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
    // Build-ahead penalty: 1 per day
    if (currentOpplan.end > data->state->q_operationplan->getDates().getEnd())
      data->state->a_penalty += 
        (currentOpplan.end - data->state->q_operationplan->getDates().getEnd()) / 86400.0;
  }
  else if (data->state->q_operationplan->getQuantity() > 0.0)
    data->state->q_operationplan->setQuantity(0.0);

  // Maintain the constraint list
  if (data->state->a_qty == 0.0 && data->logConstraints)
    data->planningDemand->getConstraints().push(
      new ProblemCapacityOverload(const_cast<Resource*>(res), 
        currentOpplan.start, currentOpplan.end, orig_q_qty, false)
      );

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


DECLARE_EXPORT void SolverMRP::solve(const ResourceInfinite* res, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_resource) userexit_resource.call(res, PythonObject(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "  Infinite resource '" << res << "' is asked: "
    << (-data->state->q_qty) << "  " << data->state->q_operationplan->getDates() << endl;

  // TODO xxx Need to make the setups feasible - move to earlier dates till max_early fence is reached

  // Reply whatever is requested, regardless of date and quantity.
  data->state->a_qty = data->state->q_qty;
  data->state->a_date = data->state->q_date;
  data->state->a_cost += data->state->a_qty * res->getCost()
    * (data->state->q_operationplan->getDates().getDuration() - data->state->q_operationplan->getUnavailable())
    / 3600.0;

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "  Infinite resource '" << res << "' answers: "
    << (-data->state->a_qty) << "  " << data->state->a_date << endl;
}


}
