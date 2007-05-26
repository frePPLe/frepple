/***************************************************************************
  file : $URL: https://frepple.svn.sourceforge.net/svnroot/frepple/trunk/src/solver/solverbuffer.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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

float suggestQuantity(const BufferProcure* b, float f)
{
  // Standard answer
  float order_qty = f;

  // Round to a multiple
  if (b->getSizeMultiple()>0.0f)
  {
    int mult = (int) (order_qty / b->getSizeMultiple() + 0.99999f);
    order_qty = mult * b->getSizeMultiple();  
  } 

  // Respect minimum size
  if (order_qty < b->getSizeMinimum())
  {
    order_qty = b->getSizeMinimum();
    // round up to multiple
    if (b->getSizeMultiple()>0.0f)
    {
      int mult = (int) (order_qty / b->getSizeMultiple() + 0.99999f);
      order_qty = mult * b->getSizeMultiple();  
    } 
    // if now bigger than max -> infeasible
    if (order_qty > b->getSizeMaximum()) 
      throw DataException("Inconsistent procurement parameters on buffer '" + b->getName() + "'");
  }

  // Respect maximum size
  if (order_qty > b->getSizeMaximum())
  {
    order_qty = b->getSizeMaximum();
    // round down
    if (b->getSizeMultiple()>0.0f)
    {
      int mult = (int) (order_qty / b->getSizeMultiple());
      order_qty = mult * b->getSizeMultiple();  
    } 
    // if now smaller than min -> infeasible
    if (order_qty < b->getSizeMinimum()) 
      throw DataException("Inconsistent procurement parameters on buffer '" + b->getName() + "'");
  }

  // Reply
  return order_qty;
}


DECLARE_EXPORT void MRPSolver::solve(const BufferProcure* b, void* v)
{
  MRPSolverdata* Solver = static_cast<MRPSolverdata*>(v);

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=b->getLevel(); i>0; --i) cout << " ";
    cout << "  Procurement buffer '" << b->getName() << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Standard reply date
  Solver->a_date = Date::infiniteFuture;

  // Find the latest locked procurement operation
  Date prev_supply;
  for (OperationPlan::iterator procs(b->getOperation());
    procs != OperationPlan::iterator(NULL); ++procs)
      if (procs->getLocked()) 
        prev_supply = procs->getDates().getEnd();

  // Loop through all flowplans
  OperationPlan *last_operationplan = NULL;
  Date next_date;
  double current_inventory = 0.0;
  Date current_date;
  const FlowPlan* current_flowplan = NULL;
  for (Buffer::flowplanlist::const_iterator cur=b->getFlowPlans().begin(); 
    next_date || cur != b->getFlowPlans().end(); )
  {
   if (cur==b->getFlowPlans().end() || (next_date && next_date<cur->getDate()))
    {
     // Go through the loop based on the next_date variable
      // The cur iterator points to a flowplan beyond the next_date
      if (next_date <= current_date) break;
      current_date = next_date;
      current_inventory = b->getOnHand(current_date);
      current_flowplan = NULL;
      next_date = Date::infinitePast;
    }
    else
    {
      // Go through the loop based on consuming flowplan
      current_date = cur->getDate();
      current_inventory = cur->getOnhand();
      current_flowplan = dynamic_cast<const FlowPlan*>(&*(cur++));
    }

    // Delete producers
    if (current_flowplan 
      && current_flowplan->getQuantity() > 0.0f
      && !current_flowplan->getOperationPlan()->getLocked())
        delete &*(current_flowplan->getOperationPlan());
    
    // Hard limit: respect minimum interval
    if (b->getMinimumInterval() && prev_supply &&
      current_date < prev_supply + b->getMinimumInterval())
      continue;

    // Hard limit: respect the leadtime xxx
    //   if prevsupplydate and time < prevsupply  and leadtimeconstrained
    //      May need to stop before the next date: order at fence...
    //      skip to next  
    
    // Already higher than the maximum - allow skipping this procurement
    if (current_inventory >= b->getMaximumInventory()) continue;

    // Now the normal reorder check
    if (b->getMaximumInterval() && current_date>=prev_supply+b->getMaximumInterval())
    {
      if (b->getSizeMinimum()>0.0f 
        && b->getMaximumInventory()-current_inventory < b->getSizeMinimum())
          current_date = prev_supply+b->getMaximumInterval();
    }
    else if (current_inventory > b->getMinimumInventory())
      continue;
    
    // When we have just exceeded the minimum interval, we may need to increase the latest procurement
    if (current_date==prev_supply+b->getMinimumInterval() && last_operationplan)
      last_operationplan->setQuantity(suggestQuantity(b,
        static_cast<float>(last_operationplan->getQuantity()+b->getMinimumInventory()-current_inventory))); 

    // At this point, we know we need to reorder...

    // Create operation plan
    float order_qty = suggestQuantity(b,static_cast<float>(b->getMaximumInventory() - current_inventory));
    if (order_qty > 0)
    {
      last_operationplan = b->getOperation()->createOperationPlan(
          order_qty, 
          Date::infinitePast, current_date, NULL);
      last_operationplan->initialize();
      prev_supply = current_date;
      if (b->getMinimumInterval())
        next_date = prev_supply + b->getMinimumInterval();
    }
  }

  // Create the answer
  if (Solver->getSolver()->isConstrained())
  {
    // Check if the inventory drops below zero somewhere
    float shortage = 0;
    for (Buffer::flowplanlist::const_iterator cur=b->getFlowPlans().begin(); 
      cur != b->getFlowPlans().end(); ++cur)
      if (cur->getDate() >= Solver->q_date 
        && cur->getOnhand() < -ROUNDING_ERROR 
        && cur->getOnhand() < shortage)
      {
        shortage = static_cast<float>(cur->getOnhand());
        if (-shortage >= Solver->q_qty) break;
      }
    if (shortage < 0)
    {
      // Answer a shorted quantity
      Solver->a_qty = Solver->q_qty + shortage;
      if (Solver->a_qty < 0) Solver->a_qty = 0;
    }
    else
      // Answer the full quantity
      Solver->a_qty = Solver->q_qty;
  }
  else
    // Answer the full quantity
    Solver->a_qty = Solver->q_qty;

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=b->getLevel(); i>0; --i) cout << " ";
    cout << "  Procurement buffer '" << b->getName() << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


}
