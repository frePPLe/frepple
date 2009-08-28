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


DECLARE_EXPORT void SolverMRP::solve(const Demand* l, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);
  unsigned int loglevel = data->getSolver()->getLogLevel();
  
  // Note: This solver method does not push/pop states on the stack.
  // We continue to work on the top element of the stack.

  // Message
  if (data->getSolver()->getLogLevel()>0)
    logger << "Planning demand '" << l->getName() << "' (" << l->getPriority()
    << ", " << l->getDue() << ", " << l->getQuantity() << ")" << endl;

  // Unattach previous delivery operationplans.
  // Locked operationplans will NOT be deleted, and a part of the demand can
  // still remain planned.
  const_cast<Demand*>(l)->deleteOperationPlans();  // xxx should use a delete command instead, in order to be undoable!!!

  // Determine the quantity to be planned and the date for the planning loop
  double plan_qty = l->getQuantity() - l->getPlannedQuantity();
  Date plan_date = l->getDue();

  // Nothing to be planned any more (e.g. all deliveries are locked...)
  if (plan_qty < ROUNDING_ERROR)
  {
    if (loglevel>0) logger << "  Nothing to be planned." << endl;
    return;
  }

  // Temporary values to store the 'best-reply' so far
  double best_q_qty = 0.0, best_a_qty = 0.0;
  Date best_q_date;

  // Which operation to use?
  Operation* deliveryoper = l->getDeliveryOperation();
  if (!deliveryoper)
    throw DataException("Demand '" + l->getName() + "' can't be planned");

  // Planning loop
  do
  {
    // Message
    if (loglevel>0)
      logger << "Demand '" << l << "' asks: "
      << plan_qty << "  " << plan_date << endl;

    // Store the last command in the list, in order to undo the following
    // commands if required.
    Command* topcommand = data->getLastCommand();

    // Plan the demand by asking the delivery operation to plan
    data->state->curBuffer = NULL;
    data->state->q_qty = plan_qty;
    data->state->q_date = plan_date;
    data->state->curDemand = const_cast<Demand*>(l);
    deliveryoper->solve(*this,v);

    // Message
    if (loglevel>0)
      logger << "Demand '" << l << "' gets answer: "
      << data->state->a_qty << "  " << data->state->a_date << "  "
      << data->state->a_cost << "  " << data->state->a_penalty << endl;

    // Update the date to plan in the next loop
    Date copy_plan_date = plan_date;

    // Compare the planned quantity with the minimum allowed shipment quantity
    // We don't accept the answer in case:
    // 1) Nothing is planned
    // 2) The planned quantity is less than the minimum shipment quantity
    // 3) The remaining quantity after accepting this answer is less than
    //    the minimum quantity. 
    if (data->state->a_qty < ROUNDING_ERROR 
      || data->state->a_qty + ROUNDING_ERROR < l->getMinShipment()
      || (plan_qty - data->state->a_qty < l->getMinShipment()
          && plan_qty - data->state->a_qty > ROUNDING_ERROR))
    {
      if (plan_qty - data->state->a_qty < l->getMinShipment()
        
        && data->state->a_qty + ROUNDING_ERROR >= l->getMinShipment()
        && data->state->a_qty > best_a_qty )
      {
        // The remaining quantity after accepting this answer is less than
        // the minimum quantity. Therefore, we delay accepting it now, but
        // still keep track of this best offer.
        best_a_qty = data->state->a_qty;
        best_q_qty = plan_qty;
        best_q_date = plan_date;
      }

      // Delete operationplans - Undo all changes
      data->undo(topcommand);

      // Set the ask date for the next pass through the loop
      if (data->state->a_date <= copy_plan_date)
      {
        // Oops, we didn't get a proper answer we can use for the next loop.
        // Print a warning and simply try one day later.
        if (loglevel>0)
          logger << "Warning: Demand '" << l << "': Lazy retry" << endl;
        plan_date = copy_plan_date + data->sol->getLazyDelay();
      }
      else 
        // Use the next-date answer from the solver
        plan_date = data->state->a_date;
    }    
    else
    {
      // Accepting this answer
      if (data->state->a_qty + ROUNDING_ERROR < plan_qty)
      {
        // The demand was only partially planned. We need to do a new
        // 'coordinated' planning run.

        // Delete operationplans created in the 'testing round'
        data->undo(topcommand);

        // Create the correct operationplans
        if (loglevel>=2) logger << "Demand '" << l << "' plans coordination." << endl;
        data->getSolver()->setLogLevel(0);
        double tmpresult = data->state->a_qty;
        try
        {
          for(double remainder = data->state->a_qty;
            remainder > ROUNDING_ERROR; remainder -= data->state->a_qty)
          {
            data->state->q_qty = remainder;
            data->state->q_date = copy_plan_date;
            data->state->curDemand = const_cast<Demand*>(l);
            data->state->curBuffer = NULL;
            deliveryoper->solve(*this,v);
            if (data->state->a_qty < ROUNDING_ERROR)
            {
              logger << "Warning: Demand '" << l << "': Failing coordination" << endl;
              break;
            }
          }
        }
        catch (...)
        {
          data->getSolver()->setLogLevel(loglevel);
          throw;
        }
        data->getSolver()->setLogLevel(loglevel);
        data->state->a_qty = tmpresult;
      }

      // Register the new operationplans. We need to make sure that the
      // correct execute method is called!
      if (data->getSolver()->getAutocommit())
        data->CommandList::execute();

      // Update the quantity to plan in the next loop
      plan_qty -= data->state->a_qty;
      best_a_qty = 0.0;  // Reset 'best-answer' remember
    }

  }
  // Repeat while there is still a quantity left to plan and we aren't
  // exceeding the maximum delivery delay.
  while (plan_qty > ROUNDING_ERROR
      && plan_date < l->getDue() + l->getMaxLateness());

  // Accept the best possible answer.
  // We may have skipped it in the previous loop, awaiting a still better answer
  if (best_a_qty > 0.0)
  {
    if (loglevel>=2) logger << "Demand '" << l << "' accepts a best answer." << endl;
    data->getSolver()->setLogLevel(0);
    try
    {
      for(double remainder = best_q_qty;
        remainder > ROUNDING_ERROR; remainder -= data->state->a_qty)
      {
        data->state->q_qty = remainder;
        data->state->q_date = best_q_date;
        data->state->curDemand = const_cast<Demand*>(l);
        data->state->curBuffer = NULL;
        deliveryoper->solve(*this,v);
        if (data->state->a_qty < ROUNDING_ERROR)
        {
          logger << "Warning: Demand '" << l << "': Failing accepting best answer" << endl;
          break;
        }
      }
      if (data->getSolver()->getAutocommit())
        data->CommandList::execute();
    }
    catch (...)
    {
      data->getSolver()->setLogLevel(loglevel);
      throw;
    }
    data->getSolver()->setLogLevel(loglevel);
  }
}

}