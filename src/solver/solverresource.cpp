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

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(res->getLevel()) << "   Resource '" << res->getName() 
      << "' is asked: " << (-data->state->q_qty) << "  " 
      << data->state->q_operationplan->getDates() << endl;

  // Initialize some variables
  double orig_q_qty = -data->state->q_qty;
  Date currentOpplanEnd = data->state->q_operationplan->getDates().getEnd();
  double currentQuantity = data->state->q_operationplan->getQuantity();
  Resource::loadplanlist::const_iterator cur = res->getLoadPlans().end();
  Date curdate;
  double curMax, prevMax;
  bool HasOverload;
  
  // Initialize the default reply
  data->state->a_date = data->state->q_date;
  data->state->a_qty = orig_q_qty;

  // Loop for a valid location by using EARLIER capacity
  if (!data->state->forceLate)
    do
    {
      // Check if this operation overloads the resource at its current time
      HasOverload = false;
      Date earliestdate = data->state->q_operationplan->getDates().getStart();
      curdate = data->state->q_loadplan->getDate(); //Date::infiniteFuture;
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

      // Try solving the overload by resizing the operationplan.
      // The capacity isn't overloaded in the time between "curdate" and 
      // "current end of the operationplan". We can try to resize the 
      // operationplan to fit in this time period...
      if (HasOverload && curdate < data->state->q_loadplan->getDate())
      {
        Date currentEnd = data->state->q_operationplan->getDates().getEnd();
        data->state->q_operationplan->getOperation()->setOperationPlanParameters(
          data->state->q_operationplan,
          currentQuantity,
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
            currentQuantity,
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
        for (; cur!=res->getLoadPlans().end() && curdate > currentOpplanEnd - res->getMaxEarly(); --cur)
        {
          // A change in the maximum capacity          
          prevMax = curMax;          
          if (cur->getType() == 4) 
            curMax = cur->getMax(false);

          // Not interested if date doesn't change
          if (cur->getDate() == curdate) continue;

          // Stop if a new date reached and we are below the max limit now
          if (cur->getOnhand() < prevMax + ROUNDING_ERROR) break;
          curdate = cur->getDate();
        }

        // We found a date where the load goes below the maximum
        // At this point:
        //  - curdate is a latest date where we drop below the maximum
        //  - cur is the first loadplan where we are below the max
        if (cur != res->getLoadPlans().end() && curdate > currentOpplanEnd - res->getMaxEarly())
        {
          // Move the operationplan
          data->state->q_operationplan->setEnd(curdate);

          // Check the leadtime constraints after the move
          if (isLeadtimeConstrained() || isFenceConstrained())
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
  if (data->state->a_qty == 0.0 || data->state->forceLate)
  {
    // Put the operationplan back at its original end date
    if (!data->state->forceLate)
    {
      data->state->q_operationplan->setQuantity(currentQuantity); 
      data->state->q_operationplan->setEnd(currentOpplanEnd);
    }

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
            currentQuantity / parallelOps, // 0.001  @todo this calculation doesn't give minimization of the lateness
            newDate,
            Date::infinitePast
            );  
        HasOverload = true;
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

  // Increment the cost  @todo also during unavailable time the cost is incremented
  if (data->state->a_qty > 0.0)
    data->state->a_cost += data->state->a_qty * res->getCost()
       * data->state->q_operationplan->getDates().getDuration() / 3600.0;

  // Message
  if (data->getSolver()->getLogLevel()>1)
  {
    logger << indent(res->getLevel()) << "   Resource '" << res << "' answers: "
      << data->state->a_qty << "  " << data->state->a_date;
    if (currentOpplanEnd > data->state->q_operationplan->getDates().getEnd())
      logger << " using earlier capacity "
        << data->state->q_operationplan->getDates().getEnd();
    if (data->state->a_qty>0.0 && data->state->q_operationplan->getQuantity() < currentQuantity)
      logger << " with reduced quantity " << data->state->q_operationplan->getQuantity();
    logger << endl;
  }

}


DECLARE_EXPORT void SolverMRP::solve(const ResourceInfinite* res, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "  Resource '" << res << "' is asked: "
    << (-data->state->q_qty) << "  " << data->state->q_operationplan->getDates() << endl;

  // Reply whatever is requested, regardless of date and quantity.
  data->state->a_qty = data->state->q_qty;
  data->state->a_date = data->state->q_date;
  data->state->a_cost += data->state->a_qty * res->getCost() // @todo also during unavailable time the cost is incremented
    * data->state->q_operationplan->getDates().getDuration() / 3600.0;  

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->state->q_qty < 0)
    logger << indent(res->getLevel()) << "  Resource '" << res << "' answers: "
    << (-data->state->a_qty) << "  " << data->state->a_date << endl;
}


}
