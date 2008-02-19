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
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/solver.h"

namespace frepple
{


void MRPSolver::solve(const Load* l, void* v)
{
  MRPSolverdata* data = static_cast<MRPSolverdata*>(v);
  if (data->q_qty >= 0.0)
  {
    // The loadplan is an increase in size, and the resource solver only needs
    // the decreases.
    // Or, it's a zero quantity loadplan. E.g. because it is not effective.
    data->a_qty = data->q_qty;
    data->a_date = data->q_date;
  }
  else
    // Delegate the answer to the resource
    l->getResource()->solve(*this,v);
}


/** @todo resource solver should be using a move command rather than direct move */
DECLARE_EXPORT void MRPSolver::solve(const Resource* res, void* v)
{
  MRPSolverdata* data = static_cast<MRPSolverdata*>(v);

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(res->getLevel()) << "   Resource '" << res->getName() 
      << "' is asked: " << (-data->q_qty) << "  " 
      << data->q_operationplan->getDates() << endl;

  // Initialize some variables
  double orig_q_qty = -data->q_qty;
  Date currentOpplanEnd = data->q_operationplan->getDates().getEnd();
  float currentQuantity = data->q_operationplan->getQuantity();
  Resource::loadplanlist::const_iterator cur = res->getLoadPlans().end();
  Date curdate;
  float curMax;
  bool HasOverload;
  
  // Initialize the default reply
  data->a_date = data->q_date;
  data->a_qty = orig_q_qty;

  // Loop for a valid location by using EARLIER capacity
  if (!data->forceLate)
    do
    {
      // Check if this operation overloads the resource at its current time
      HasOverload = false;
      Date earliestdate = data->q_operationplan->getDates().getStart();
      curdate = data->q_loadplan->getDate();
      curMax = data->q_loadplan->getMax();
      for (cur = res->getLoadPlans().begin(data->q_loadplan);
        cur!=res->getLoadPlans().end() && cur->getDate()>=earliestdate; 
        --cur)
      {
        // A change in the maximum capacity
        if (cur->getType() == 4) curMax = cur->getMax();

        // Not interested if date doesn't change
        if (cur->getDate() == curdate) continue;
        
        if (cur->getOnhand() > curMax)
        {
          // Overload: New date reached, and we are exceeding the limit!
          HasOverload = true;
          break;
        }
        curdate = cur->getDate();
      }

      // Try solving the overload by resizing the operationplan.
      // The capacity isn't overloaded in the time between "curdate" and 
      // "current end of the operationplan". We can try to resize the 
      // operationplan to fit in this time period...
      if (HasOverload && curdate < data->q_loadplan->getDate())
      {
        Date currentEnd = data->q_operationplan->getDates().getEnd();
        data->q_operationplan->getOperation()->setOperationPlanParameters(
          data->q_operationplan,
          currentQuantity,
          curdate,
          currentEnd
          );
        if (data->q_operationplan->getQuantity() > 0
          && data->q_operationplan->getDates().getEnd() <= currentEnd
          && data->q_operationplan->getDates().getStart() >= curdate)
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
          data->q_operationplan->getOperation()->setOperationPlanParameters(
            data->q_operationplan,
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
        for (; cur!=res->getLoadPlans().end(); --cur)
        {
          // A change in the maximum capacity
          if (cur->getType() == 4) curMax = cur->getMax();

          // Not interested if date doesn't change
          if (cur->getDate() == curdate) continue;

          // Stop if a new date reached and we are below the max limit now
          if (cur->getOnhand() <= curMax) break;
          curdate = cur->getDate();
        }

        // We found a date where the load goes below the maximum
        if (cur != res->getLoadPlans().end())
        {
          // Move the operationplan
          data->q_operationplan->setEnd(curdate); 

          // Check the leadtime constraints after the move
          if (isLeadtimeConstrained() || isFenceConstrained())
            // Note that the check function can update the answered date
            // and quantity
            checkOperationLeadtime(data->q_operationplan,*data,false);
        }
        else
          // No earlier capacity found: get out of the loop
          data->a_qty = 0.0;
      }  // End of if-statement, solve by moving earlier
    }
    while (HasOverload && data->a_qty!=0.0);

  // Loop for a valid location by using LATER capacity
  // If the answered quantity is 0, the operationplan is moved into the
  // past.
  // Or, the solver may be forced to produce a late reply.
  // In these cases we need to search for capacity at later dates.
  if (data->a_qty == 0.0 || data->forceLate)
  {
    // Put the operationplan back at its original end date
    if (!data->forceLate)
    {
      data->q_operationplan->setQuantity(currentQuantity); 
      data->q_operationplan->setEnd(currentOpplanEnd);
    }

    // Moving an operation earlier is driven by the ending loadplan,
    // while searching for later capacity is driven from the starting loadplan.
    data->q_loadplan = data->q_loadplan->getOtherLoadPlan();

    // Loop to find a later date where the operationplan will fit
    Date newDate;
    do
    {
      // Search for a date where we go below the maximum load.
      // and verify whether there are still some overloads
      HasOverload = false;
      newDate = Date::infinitePast;
      curMax = data->q_loadplan->getMax();
      double curOnhand = data->q_loadplan->getOnhand();
      for (cur=res->getLoadPlans().begin(data->q_loadplan);
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
        //xxxif ((loadpl->getDate() <= data->q_operationplan->getDates().getEnd() && loadpl->getOnhand() > curMax)
        //  || (loadpl->getDate() > data->q_operationplan->getDates().getEnd() && loadpl->getOnhand() + data->q_loadplan->getQuantity() > curMax))
        if (loadpl->getOnhand() > curMax)
          // There is still a capacity problem
          HasOverload = true;   
        //else if (!HasOverload && loadpl->getDate() > data->q_operationplan->getDates().getEnd())
          // Break out of loop if no overload and date is after operationplan end date
         // break;
        else if (!newDate && loadpl->getDate()!=data->q_loadplan->getDate())
        {
          // We are below the max limit for the first time now.
          // This means that the previous date may be a proper start.
          newDate = loadpl->getDate();
          //break;
        }
      }

      // Found a date with available capacity
      if (HasOverload && newDate)
      {
        // Multiple operations could be executed in parallel
        int parallelOps = (int)((curMax - curOnhand) / data->q_loadplan->getQuantity());
        if (parallelOps <= 0) parallelOps = 1;
        // Move the operationplan to the new date
        data->q_operationplan->getOperation()->setOperationPlanParameters(
            data->q_operationplan,
            currentQuantity / parallelOps,
            newDate,
            Date::infinitePast
            );  
        HasOverload = true;
      }
    }
    while (HasOverload && newDate);

    // Set the date where a next trial date can happen
    if (HasOverload)
      // No available capacity found anywhere in the horizon
      data->a_date = Date::infiniteFuture;
    else
      data->a_date = data->q_operationplan->getDates().getEnd();

    // Create a zero quantity reply
    data->a_qty = 0.0;
  }

  if (data->a_qty == 0.0 && data->q_operationplan->getQuantity() != 0.0)
    // In case of a zero reply, we resize the operationplan to 0 right away.
    // This is required to make sure that the buffer inventory profile also
    // respects this answer.
    data->q_operationplan->setQuantity(0.0);

  // Message
  if (data->getSolver()->getLogLevel()>1)
  {
    logger << indent(res->getLevel()) << "   Resource '" << res->getName() << "' answers: "
      << data->a_qty << "  " << data->a_date;
    if (currentOpplanEnd > data->q_operationplan->getDates().getEnd())
      logger << " using earlier capacity "
        << data->q_operationplan->getDates().getEnd();
    if (data->a_qty>0.0 && data->q_operationplan->getQuantity() < currentQuantity)
      logger << " with reduced quantity " << data->q_operationplan->getQuantity();
    logger << endl;
  }

}


DECLARE_EXPORT void MRPSolver::solve(const ResourceInfinite* r, void* v)
{
  MRPSolverdata* data = static_cast<MRPSolverdata*>(v);

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->q_qty < 0)
    logger << indent(r->getLevel()) << "  Resource '" << r << "' is asked: "
    << (-data->q_qty) << "  " << data->q_operationplan->getDates() << endl;

  // Reply whatever is requested, regardless of date and quantity.
  data->a_qty = data->q_qty;
  data->a_date = data->q_date;

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->q_qty < 0)
    logger << indent(r->getLevel()) << "  Resource '" << r << "' answers: "
    << (-data->a_qty) << "  " << data->a_date << endl;
}


}
