/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/solver/solverdemand.cpp $
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

#define FREPPLE_CORE 
#include "frepple/solver.h"


namespace frepple
{


void MRPSolver::solve (Demand* l, void* v)
{
  MRPSolverdata* Solver = (MRPSolverdata*)v;
  bool verbose = Solver->getSolver()->getVerbose();

  // Message
  if (verbose)
    clog << "Planning demand '" << l->getName() << "' (" << l->getPriority()
    << ", " << l->getDue() << ", " << l->getQuantity() << ")" << endl;

  // Unattach previous delivery operationplans.
  // Locked operationplans will NOT be deleted, and a part of the demand can
  // still remain planned.
  l->deleteOperationPlans();

  // Determine the quantity to be planned and the date for the planning loop
  float plan_qty = l->getQuantity() - l->getPlannedQuantity();
  Date plan_date = l->getDue();

  // Nothing to be planned any more (e.g. all deliveries are locked...)
  if (plan_qty < ROUNDING_ERROR)
  {
    if (verbose) clog << "Nothing to be planned." << endl;
    return;
  }

  // Which operation to use?
  Operation *deliveryoper = l->getDeliveryOperation();
  if (!deliveryoper)
    throw DataException("Demand '" + l->getName() + "' can't be planned");

  // Planning loop
  do
  {
    // Message
    if (verbose)
      clog << "Demand '" << l << "' asks: "
      << plan_qty << " - " << plan_date << endl;

    // Check whether the action list is empty
    assert( Solver->actions.empty() );

    // Plan the demand by asking the delivery operation to plan
    Solver->curBuffer = NULL;
    Solver->q_qty = plan_qty;
    Solver->q_date = plan_date;
    Solver->curDemand = l;
    deliveryoper->solve(*this,v);

    // Message
    if (verbose)
      clog << "Demand '" << l << "' gets answer: "
      << Solver->a_qty << " - " << Solver->a_date << endl;

    // Update for the next planning loop
    if (l->planMultiDelivery())
    {
      // Update the date to plan in the next loop
      Date copy_plan_date = plan_date;
      plan_date = Solver->a_date;

      if (Solver->a_qty > ROUNDING_ERROR)
      {
        if (Solver->a_qty + ROUNDING_ERROR < plan_qty)
        {
          // The demand was only partially planned. We need to do a new
          // 'coordinated' planning run.

          // Delete operationplans created in the 'testing round'
          Solver->actions.undo();

          // Create the correct operationplans
          bool tmp = Solver->getSolver()->getVerbose();
          double tmpqty = Solver->a_qty;
          if (tmp) clog << "Demand '" << l << "' plans coordination." << endl;
          Solver->getSolver()->setVerbose(false);
          Solver->q_qty = Solver->a_qty;
          Solver->q_date = copy_plan_date;
          Solver->curDemand = l;
          Solver->curBuffer = NULL;
          deliveryoper->solve(*this,v);
          Solver->getSolver()->setVerbose(tmp);

          // Message
          if (fabs(Solver->a_qty - tmpqty) > ROUNDING_ERROR)
            clog << "Demand '" << l << "' coordination screwed up: "
            << Solver->a_qty << " versus " << tmpqty << endl;
        }
        // Register the new operationplans
        Solver->actions.execute();

        // Update the quantity to plan in the next loop
        plan_qty -= Solver->a_qty;
      }
      else
      {
        // Nothing planned - Delete operationplans - Undo all changes
        Solver->actions.undo();
        // If there is no proper new date for the next loop, we need to exit
        if (Solver->a_date <= copy_plan_date) plan_qty = 0.0f;
      }
    }
    else if (l->planSingleDelivery())
    {
      // Only a single delivery of the complete quantity is allowed.
      if (Solver->a_qty + ROUNDING_ERROR > plan_qty)
      {
        // Yes, it is fully planned
        // Commit all changes
        Solver->actions.execute();
        // Update the quantity and date to plan in the next loop
        plan_qty -= Solver->a_qty;
        plan_date = Solver->a_date;
      }
      else
      {
        // Not fully planned. Try again at a new date
        // Undo all changes
        Solver->actions.undo();
        // If there is no proper new date for the next loop, we need to exit
        if (Solver->a_date <= plan_date) plan_qty = 0.0f;
        plan_date = Solver->a_date;
      }
    }
  }
  while (l->planLate()
         && plan_qty > ROUNDING_ERROR
         && plan_date < Date::infiniteFuture);
}

}
