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


DECLARE_EXPORT void MRPSolver::solve (const Demand* l, void* v)
{
  MRPSolverdata* Solver = static_cast<MRPSolverdata*>(v);
  unsigned int loglevel = Solver->getSolver()->getLogLevel();

  // Message
  if (loglevel>0)
    logger << "Planning demand '" << l->getName() << "' (" << l->getPriority()
    << ", " << l->getDue() << ", " << l->getQuantity() << ")" << endl;

  // Unattach previous delivery operationplans.
  // Locked operationplans will NOT be deleted, and a part of the demand can
  // still remain planned.
  WLock<Demand>(l)->deleteOperationPlans();

  // Determine the quantity to be planned and the date for the planning loop
  float plan_qty = l->getQuantity() - l->getPlannedQuantity();
  Date plan_date = l->getDue();

  // Nothing to be planned any more (e.g. all deliveries are locked...)
  if (plan_qty < ROUNDING_ERROR)
  {
    if (loglevel>0) logger << "  Nothing to be planned." << endl;
    return;
  }

  // Which operation to use?
  Operation::pointer deliveryoper = l->getDeliveryOperation();
  if (!deliveryoper)
    throw DataException("Demand '" + l->getName() + "' can't be planned");

  // Planning loop
  do
  {
    // Message
    if (loglevel>0)
      logger << "Demand '" << l << "' asks: "
      << plan_qty << " - " << plan_date << endl;

    // Check whether the action list is empty
    assert( Solver->empty() );

    // Plan the demand by asking the delivery operation to plan
    Solver->curBuffer = NULL;
    Solver->q_qty = plan_qty;
    Solver->q_date = plan_date;
    Solver->curDemand = l;
    deliveryoper->solve(*this,v);

    // Message
    if (loglevel>0)
      logger << "Demand '" << l << "' gets answer: "
      << Solver->a_qty << " - " << Solver->a_date << endl;

    // Update for the next planning loop
    if (l->planMultiDelivery())
    {
      // Update the date to plan in the next loop
      Date copy_plan_date = plan_date;

      if (Solver->a_qty > ROUNDING_ERROR)
      {
        if (Solver->a_qty + ROUNDING_ERROR < plan_qty)
        {
          // The demand was only partially planned. We need to do a new
          // 'coordinated' planning run.

          // Delete operationplans created in the 'testing round'
          Solver->undo();

          // Create the correct operationplans
          double tmpqty = Solver->a_qty;
          if (loglevel>=2) logger << "Demand '" << l << "' plans coordination." << endl;
          Solver->getSolver()->setLogLevel(0);
          float tmpresult = Solver->a_qty;
          for(float remainder = Solver->a_qty;
            remainder > ROUNDING_ERROR; remainder -= Solver->a_qty)
          {
            Solver->q_qty = remainder;
            Solver->q_date = copy_plan_date;
            Solver->curDemand = l;
            Solver->curBuffer = NULL;
            deliveryoper->solve(*this,v);
            if (Solver->a_qty < ROUNDING_ERROR)
            {
              logger << "Warning: Demand '" << l << "': Failing coordination" << endl;
              break;
            }
          }
          Solver->getSolver()->setLogLevel(loglevel);
          Solver->a_qty = tmpresult;
        }

        // Register the new operationplans. We need to make sure that the
        // correct execute method is called!
        Solver->CommandList::execute();

        // Update the quantity to plan in the next loop
        plan_qty -= Solver->a_qty;
      }
      else
      {
        // Nothing planned - Delete operationplans - Undo all changes
        Solver->undo();
        // If there is no proper new date for the next loop, we need to exit
        if (Solver->a_date <= copy_plan_date)
        {
          if (copy_plan_date < l->getDue() + TimePeriod(60L*86400L)) // @todo hardcoded max!!!
          {
            // Try a day later
            logger << "Warning: Demand '" << l << "': Lazy retry" << endl;
            plan_date = copy_plan_date + TimePeriod(1*86400L); // @todo hardcoded increments of 1 day
          }
          // Don't try it any more
          else plan_qty = 0.0f;
        }
        else plan_date = Solver->a_date;
      }
    }
    else if (l->planSingleDelivery())
    {
      // Only a single delivery of the complete quantity is allowed.
      if (Solver->a_qty + ROUNDING_ERROR > plan_qty)
      {
        // Yes, it is fully planned
        // Commit all changes. We need to make sure that the correct execute
        // method is called!
        Solver->CommandList::execute();
        // Update the quantity and date to plan in the next loop
        plan_qty -= Solver->a_qty;
      }
      else
      {
        // Not fully planned. Try again at a new date
        // Undo all changes
        Solver->undo();
        // If there is no proper new date for the next loop, we need to exit
        if (Solver->a_date <= plan_date) plan_qty = 0.0f;
        plan_date = Solver->a_date;
      }
    }
  }
  // Repeat while there is still a quantity left to plan and we aren't
  // exceeding the maximum delivery delay.
  while (plan_qty > ROUNDING_ERROR
      && plan_date < l->getDue() + l->getMaxLateness());
}

}
