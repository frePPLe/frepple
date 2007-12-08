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


/** @todo Solving for capacity can break an operationplan in multiple parts:
  * qty_per operations do this....
  * This disturbs the clean & simple flow we have here...
  * We can also not check one load after the other, because they need
  * simultaneous capacity.
  */
DECLARE_EXPORT void MRPSolver::solve(const Resource* res, void* v)
{

  MRPSolverdata* data = static_cast<MRPSolverdata*>(v);

  // The loadplan is an increase in size, and the algorithm needs to process
  // the decreases.
  if (data->q_qty >= 0)
  {
    data->a_qty = data->q_qty;
    data->a_date = data->q_date;
    return;
  }

  // Message
  if (data->getSolver()->getLogLevel()>1)
  {
    for (int i=res->getLevel(); i>0; --i) logger << " ";
    logger << "   Resource '" << res->getName() << "' is asked: "
    << (-data->q_qty) << "  " << data->q_date << endl;
  }

  // Initialize the default reply
  data->a_qty = data->q_qty;
  data->a_date = data->q_date;
  Date currentOpplanEnd = data->q_operationplan->getDates().getEnd();
  float currentQuantity = data->q_operationplan->getQuantity();

  // Loop until we found a valid location for the operationplan
  bool HasOverload;
  do
  {
    // Check if this operation overloads the resource
    HasOverload = false;
    Date earliestsearchdate = data->q_operationplan->getDates().getStart();
    Date curdate = data->q_loadplan->getDate();
    float curMax = data->q_loadplan->getMax();
    for (Resource::loadplanlist::const_iterator
        cur=res->getLoadPlans().begin(data->q_loadplan);
        cur!=res->getLoadPlans().end() && cur->getDate()>=earliestsearchdate;
        --cur)
    {

      // Process changes in the maximum capacity
      if (cur->getType() == 4)
        curMax = cur->getMax();

      // Not interested if date doesn't change
      if (cur->getDate() == curdate) continue;
      curdate = cur->getDate();

      // Check overloads: New date reached, and we are exceeding the limit!
      if (cur->getOnhand() > curMax || data->forceLate)
      {
        if (!data->forceLate)
        {
          // Search backward in time to a period where there is no overload
          for (; cur!=res->getLoadPlans().end(); --cur)
          {

            if (cur->getType() == 4)
              curMax = cur->getMax();
            if (cur->getDate() != curdate)
            {
              if (cur->getOnhand()<=curMax)
                // New date reached and we are below the max limit now
                break;
              curdate = cur->getDate();
            }
          }

          // Move the operation plan if there is capacity found
          if (cur!=res->getLoadPlans().end())
          {
            // Move the operationplan
            data->q_operationplan->setEnd(curdate); // @todo resource solver should be using a move command rather than direct move

            // Check the leadtime constraints after the move
            if (isLeadtimeConstrained() || isFenceConstrained())
              // Note that the check function will update the answered date
              // and quantity
              checkOperationLeadtime(data->q_operationplan,*data,false);
          }
        }

        // If we are at the end, then there is no capacity available.
        // If the answered quantity is 0, the operationplan is moved into the
        // past.
        // In both these cases we need to search for capacity at later dates.
        if (data->forceLate || cur==res->getLoadPlans().end() || data->a_qty==0.0f)
        {
          // COMPUTE EARLIEST AVAILABLE CAPACITY

          // Put the operationplan back at its original end date
          if (!data->forceLate)
          {
            data->q_operationplan->setQuantity(currentQuantity); // @todo resource solver should be using a move command rather than direct move
            data->q_operationplan->setEnd(currentOpplanEnd);
          }

          // Find the starting loadplan. Moving an operation earlier is driven
          // by the ending loadplan, while searching for later capacity is
          // driven from the starting loadplan.
          for (OperationPlan::LoadPlanIterator
              h = data->q_operationplan->beginLoadPlans();
              h != data->q_operationplan->endLoadPlans();
              ++h)
          {
            if (&*h!=data->q_loadplan && h->getLoad()->getResource()==res)
            {
              data->q_loadplan = &*h;
              break;
            }
          }

          // Loop to find a later date where the operationplan will fit
          bool overloaded;
          Date newDate;
          do
          {
            // Search for a date where we go below the maximum load.
            // and verify whether there are still some overloads
            overloaded = false;
            newDate = Date::infinitePast;
            curdate = data->q_loadplan->getDate();
            curMax = data->q_loadplan->getMax();
            double prevOnhand = data->q_loadplan->getOnhand();
            for (cur=res->getLoadPlans().begin(data->q_loadplan);
                !(overloaded && newDate); ++cur)
            {
              if (cur!=res->getLoadPlans().end() && cur->getType() == 4)
                curMax = cur->getMax();
              if (cur==res->getLoadPlans().end() || cur->getDate() != curdate)
              {
                if (prevOnhand > curMax)
                  // There is still a capacity problem
                  overloaded = true;
                else if (!newDate && curdate!=data->q_loadplan->getDate())
                  // New date reached and we are below the max limit for the
                  // first time now.
                  // This means that the previous date may be a proper start.
                  newDate = curdate;
                if (cur == res->getLoadPlans().end()) break;
                curdate = cur->getDate();
              }
              prevOnhand = cur->getOnhand();
            }

            // Found a date with available capacity
            if (overloaded && newDate && newDate!=data->q_loadplan->getDate())
            {
              // Move the operationplan to the new date
              data->q_operationplan->setStart(newDate);  // @todo resource solver should be using a move command rather than direct move
              // Force checking for overloads again
              overloaded = true;
            }
          }
          while (overloaded && newDate);

          // Set the date where a next trial date can happen
          if (overloaded)
            // No available capacity found anywhere in the horizon
            data->a_date = Date::infiniteFuture;
          else
            data->a_date = data->q_operationplan->getDates().getEnd();

          // Create a zero quantity reply
          data->a_qty = 0.0f;
          break;
        }

        // Make sure the capacity check is redone, stay in do-while loop
        HasOverload = true;
        break;
      }   // end of if-statement
    }     // end of for-loop
  }       // end of while-loop
  while (HasOverload && data->a_qty!=0.0f);

  // In case of a zero reply, we resize the operationplan to 0 right away.
  // This is required to make sure that the buffer inventory profile also
  // respects this answer.
  if (data->a_qty == 0.0f) data->q_operationplan->setQuantity(0);

  // Message
  if (data->getSolver()->getLogLevel()>1)
  {
    for (int i=res->getLevel(); i>0; --i) logger << " ";
    logger << "   Resource '" << res->getName() << "' answers: "
      << (-data->a_qty) << "  " << data->a_date;
    if (currentOpplanEnd > data->q_operationplan->getDates().getEnd())
      logger << " using earlier capacity "
        << data->q_operationplan->getDates().getEnd();
    logger << endl;
  }

}


DECLARE_EXPORT void MRPSolver::solve(const ResourceInfinite* r, void* v)
{
  MRPSolverdata* data = static_cast<MRPSolverdata*>(v);

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->q_qty < 0)
  {
    for (int i=r->getLevel(); i>0; --i) logger << " ";
    logger << "  Resource '" << r << "' is asked: "
    << (-data->q_qty) << "  " << data->q_date << endl;
  }

  // Reply whatever is requested, regardless of date and quantity.
  data->a_qty = data->q_qty;
  data->a_date = data->q_date;

  // Message
  if (data->getSolver()->getLogLevel()>1 && data->q_qty < 0)
  {
    for (int i=r->getLevel(); i>0; --i) logger << " ";
    logger << "  Resource '" << r << "' answers: "
    << (-data->a_qty) << "  " << data->a_date << endl;
  }
}


}
