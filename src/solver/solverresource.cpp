/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/solver/solverresource.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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

#include "frepple/solver.h"

namespace frepple
{


/** @todo Solving for capacity can break an operationplan in multiple parts:
  * qty_per operations do this....
  * This disturbs the clean & simple flow we have here...
  * We can also not check one load after the other, because they need
  * simultaneous capacity.
  */
void MRPSolver::solve(Resource* res, void* v)
{

  MRPSolverdata* data = (MRPSolverdata*)v;

  // The loadplan is an increase in size, and the algorithm needs to process
  // the decreases.
  if (data->q_loadplan->getQuantity() > 0) return;

  // Message
  if (data->getSolver()->getVerbose())
  {
    for (int i=res->getLevel(); i; --i) clog << " ";
    clog << "   Resource '" << res->getName() << "' is asked: "
    << (-data->q_qty) << "  " << data->q_date << endl;
  }

  // Initialize the default reply
  data->a_qty = data->q_qty;
  data->a_date = data->q_date;

  // Loop until we found a valid location for the operationplan
  bool HasOverload;
  do
  {
    // Check if this operation overloads the resource
    HasOverload = false;
    Date earliestsearchdate = data->q_operationplan->getDates().getStart();
    Date curdate = data->q_loadplan->getDate();
    float curMax = data->q_loadplan->getMax();
    for(Resource::loadplanlist::const_iterator 
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
      if (cur->getOnhand() > curMax)
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

        // Create a new move command if there is capacity found
        if (cur!=res->getLoadPlans().end())
        {
          if (data->moveit)
            data->moveit->setDate(curdate);
          else
            data->moveit = 
              new CommandMoveOperationPlan(data->q_operationplan, curdate);

          // Check the leadtime constraints after the move
          if (isLeadtimeConstrained() || isFenceConstrained())
            // Note that the check function will update the answered date 
            // and quantity
            checkOperationLeadtime(data->q_operationplan,*data);
        }

        // If we are at the end, then there is no capacity available.
        // If the answered quantity is 0, the operationplan is moved into the 
        // past.
        // In both these cases we need to search for capacity at later dates.
        if (cur==res->getLoadPlans().end() || data->a_qty==0.0f)
        {
          // COMPUTE EARLIEST AVAILABLE CAPACITY

          // Delete and undo the movein command, if it exists.
          if (data->moveit)
          {
            // The deletion of the move command also undos the move.
            delete data->moveit;
            data->moveit = NULL;
          }

          // Find the starting loadplan. Moving an operation earlier is driven
          // by the ending loadplan, while searching for later capacity is
          // driven from the starting loadplan.
          for(slist<LoadPlan*>::const_iterator 
            h = data->q_operationplan->getLoadPlans().begin();
            h != data->q_operationplan->getLoadPlans().end(); 
            ++h)
          {
            if ((*h)!=data->q_loadplan && (*h)->getLoad()->getResource()==res)
            {
              data->q_loadplan = *h;
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
            newDate = 0l;
            curdate = data->q_loadplan->getDate();
            curMax = data->q_loadplan->getMax();
            double prevOnhand = data->q_loadplan->getOnhand();
            for(cur=res->getLoadPlans().begin(data->q_loadplan);
                cur!=res->getLoadPlans().end() && !(overloaded && newDate); 
                ++cur)
            {
              if (cur->getType() == 4)
                curMax = cur->getMax();
              if (cur->getDate() != curdate)
              {
                if (prevOnhand > curMax)
                  // There is still a capacity problem
                  overloaded = true;
                else if (!newDate && curdate!=data->q_loadplan->getDate())
                  // New date reached and we are below the max limit for the
                  // first time now.
                  // This means that the previous date may be a proper start.
                  newDate = curdate;
                curdate = cur->getDate();
              }
              prevOnhand = cur->getOnhand();
            }

            // Found a date with available capacity
            if (overloaded && newDate && newDate!=data->q_loadplan->getDate())
            {
              // Move the operationplan to the new date
              if (!data->moveit)
                data->moveit = 
                  new CommandMoveOperationPlan(data->q_operationplan, 
                    newDate, false);
              else
                data->moveit->setDate(newDate);
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
          data->AllLoadsOkay = false;
          break;
        }

        // Make sure the capacity check is redone, stay in do-while loop
        HasOverload = true;
        data->AllLoadsOkay = false;
        break;
      }   // end of if-statement
    }     // end of for-loop
  }       // end of while-loop
  while (HasOverload && data->a_qty!=0.0f);

  // Message
  if (data->getSolver()->getVerbose())
  {
    for (int i=res->getLevel(); i; --i) clog << " ";
    clog << "   Resource '" << res->getName() << "' answers: "
    << (-data->a_qty) << "  " << data->a_date << endl;
  }

}


void MRPSolver::solve(ResourceInfinite* r, void* v)
{
  MRPSolverdata* Solver = (MRPSolverdata*)v;

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=r->getLevel(); i; --i) clog << " ";
    clog << "  Resource '" << r << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Reply whatever is requested, regardless of date and quantity.
  Solver->a_qty = Solver->q_qty;
  Solver->a_date = Solver->q_date;

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=r->getLevel(); i; --i) clog << " ";
    clog << "  Resource '" << r << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


}
