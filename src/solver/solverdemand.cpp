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


bool compare_location(const pair<Location*, double>& a, const pair<Location*, double>& b)
{
  return a.second > b.second;
}


void SolverCreate::solve(const Demand* l, void* v)
{
  typedef list<pair<Location* , double > > SortedLocation;
  // Set a bookmark at the current command
  SolverData* data = static_cast<SolverData*>(v);
  CommandManager::Bookmark* topcommand = data->getCommandManager()->setBookmark();

  // Create a state stack
  State* mystate = data->state;
  data->push();

  try
  {
    // Call the user exit
    if (userexit_demand) userexit_demand.call(l, PythonData(data->constrainedPlanning));
    short loglevel = data->getSolver()->getLogLevel();

    // Note: This solver method does not push/pop states on the stack.
    // We continue to work on the top element of the stack.

    // Message
    if (loglevel>0)
    {
      logger << "Planning demand '" << l->getName() << "' (" << l->getPriority()
          << ", " << l->getDue() << ", " << l->getQuantity() << ")";
      if (!data->constrainedPlanning || !data->getSolver()->isConstrained())
        logger << " in unconstrained mode";
      logger << endl;
    }

    // Unattach previous delivery operationplans, if required.
    if (data->getSolver()->getErasePreviousFirst())
    {
      // Locked operationplans will NOT be deleted, and a part of the demand can
      // still remain planned.
      const_cast<Demand*>(l)->deleteOperationPlans(false, data->getCommandManager());

      // Empty constraint list
      const_cast<Demand*>(l)->getConstraints().clear();
    }

    // Track constraints or not
    data->logConstraints = (getPlanType() == 1);

    // Determine the quantity to be planned and the date for the planning loop
    double plan_qty = l->getQuantity() - l->getPlannedQuantity();
    Date plan_date = l->getDue();
    if (getAdministrativeLeadTime())
      plan_date -= getAdministrativeLeadTime();
    if (plan_qty < ROUNDING_ERROR || plan_date == Date::infiniteFuture)
    {
      if (loglevel>0) logger << "  Nothing to be planned." << endl;
      data->pop();
      return;
    }
    if (plan_qty < l->getMinShipment())
      plan_qty = l->getMinShipment();

    // Temporary values to store the 'best-reply' so far
    double best_q_qty = 0.0, best_a_qty = 0.0;
    Date best_q_date;

    // Select delivery operation
    Operation* deliveryoper = l->getDeliveryOperation();

    // Handle invalid or missing delivery operations
    {
    string problemtext = string("Demand '") + l->getName() + "' has no delivery operation";
    Problem::iterator j = Problem::begin(const_cast<Demand*>(l), false);
    while (j != Problem::end())
    {
      if (&(j->getType()) == ProblemInvalidData::metadata
          && j->getDescription() == problemtext)
        break;
      ++j;
    }
    if (!deliveryoper)
    {
      // Create a problem
      if (j == Problem::end())
      new ProblemInvalidData(const_cast<Demand*>(l), problemtext, "demand",
          l->getDue(), l->getDue(), l->getQuantity());
      // Abort planning of this demand
      throw DataException("Demand '" + l->getName() + "' can't be planned");
    }
    else
      // Remove problem that may already exist
      delete &*j;
    }

    // Plan over different locations if global_purchase flag is set
    // Store the original location in a variable
    Location* originalLocation = l->getLocation();
    SortedLocation sortedLocation;
    bool globalPurchase = l->getItem() ?
      l->getItem()->getBoolProperty("global_purchase", false) && data->constrainedPlanning :
      false;
    if (globalPurchase) {
      // iterate over locations and store them using the excess as a priority
      // excess being onhand minus safety stock
      Item* item = l->getItem();
      Item::bufferIterator iter(item);

      while (Buffer *buffer = iter.next()) {
        // Make sure we don't pick original location
        if (buffer->getLocation() == originalLocation)
          continue;

        // We need to calculate the excess
        Calendar* ss_calendar = buffer->getMinimumCalendar();
        double excess = 0;
        if (ss_calendar) {
          CalendarBucket* calendarBucket = ss_calendar->findBucket(data->state->q_date, true);
          if (calendarBucket)
            excess = buffer->getOnHand(l->getDue()) - calendarBucket->getValue();
        }
        else {
          excess = buffer->getOnHand(l->getDue()) - buffer->getMinimum();
        }
        sortedLocation.push_front(pair<Location*, double> (buffer->getLocation(), excess));

      }
      // Let's now order the list of location
      sortedLocation.sort(compare_location);
    }


    // Planning loop
    do
    {
      do
      {
        // Message
        if (loglevel > 0)
          logger << "Demand '" << l << "' asks: "
          << plan_qty << "  " << plan_date << endl;

        // Store the last command in the list, in order to undo the following
        // commands if required.
        CommandManager::Bookmark* topcommand = data->getCommandManager()->setBookmark();

        // Plan the demand by asking the delivery operation to plan
        double q_qty = plan_qty;
        data->state->curBuffer = nullptr;
        data->state->q_qty = plan_qty;
        data->state->q_qty_min = l->getMinShipment();
        data->state->q_date = plan_date;
        data->planningDemand = const_cast<Demand*>(l);
        data->state->curDemand = const_cast<Demand*>(l);
        data->state->curOwnerOpplan = nullptr;
        deliveryoper->solve(*this, v);
        Date next_date = data->state->a_date;

        if (data->state->a_qty < ROUNDING_ERROR
          && plan_qty > l->getMinShipment() && l->getMinShipment() > 0
          && getAllowSplits()
          )
        {
          bool originalLogConstraints = data->logConstraints;
          data->logConstraints = false;
          try
          {
            // The full asked quantity is not possible.
            // Try with the minimum shipment quantity.
            if (loglevel > 1)
              logger << "Demand '" << l << "' tries planning minimum quantity " << l->getMinShipment() << endl;
            data->getCommandManager()->rollback(topcommand);
            data->state->curBuffer = nullptr;
            data->state->q_qty = l->getMinShipment();
            data->state->q_date = plan_date;
            data->state->curDemand = const_cast<Demand*>(l);
            deliveryoper->solve(*this, v);
            if (data->state->a_date < next_date)
              next_date = data->state->a_date;
            if (data->state->a_qty > ROUNDING_ERROR)
            {
              // The minimum shipment quantity is feasible.
              // Now try iteratively different quantities to find the best we can do.
              double min_qty = l->getMinShipment();
              double max_qty = plan_qty;
              double delta = fabs(max_qty - min_qty);
              while (delta > data->getSolver()->getIterationAccuracy() * l->getQuantity()
                && delta > data->getSolver()->getIterationThreshold())
              {
                // Note: we're kind of assuming that the demand is an integer value here.
                double new_qty = floor((min_qty + max_qty) / 2);
                if (new_qty == min_qty)
                {
                  // Required to avoid an infinite loop on the same value...
                  new_qty += 1;
                  if (new_qty > max_qty) break;
                }
                if (loglevel > 0)
                  logger << "Demand '" << l << "' tries planning a different quantity " << new_qty << endl;
                data->getCommandManager()->rollback(topcommand);
                data->state->curBuffer = nullptr;
                data->state->q_qty = new_qty;
                data->state->q_date = plan_date;
                data->state->curDemand = const_cast<Demand*>(l);
                deliveryoper->solve(*this, v);
                if (data->state->a_date < next_date)
                  next_date = data->state->a_date;
                if (data->state->a_qty > ROUNDING_ERROR)
                  // Too small: new min
                  min_qty = new_qty;
                else
                  // Too big: new max
                  max_qty = new_qty;
                delta = fabs(max_qty - min_qty);
              }
              q_qty = min_qty;  // q_qty is the biggest Q quantity giving a positive reply
              if (data->state->a_qty <= ROUNDING_ERROR)
              {
                if (loglevel > 0)
                  logger << "Demand '" << l << "' restores plan for quantity " << min_qty << endl;
                // Restore the last feasible plan
                data->getCommandManager()->rollback(topcommand);
                data->state->curBuffer = nullptr;
                data->state->q_qty = min_qty;
                data->state->q_date = plan_date;
                data->state->curDemand = const_cast<Demand*>(l);
                deliveryoper->solve(*this, v);
              }
            }
          }
          catch (...)
          {
            data->logConstraints = originalLogConstraints;
            throw;
          }
          data->logConstraints = originalLogConstraints;
        }

        // Message
        if (loglevel > 0)
          logger << "Demand '" << l << "' gets answer: "
          << data->state->a_qty << "  " << next_date << "  "
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
            && fabs(plan_qty - data->state->a_qty) > ROUNDING_ERROR))
        {
          if (plan_qty - data->state->a_qty < l->getMinShipment()
            && data->state->a_qty + ROUNDING_ERROR >= l->getMinShipment()
            && data->state->a_qty > best_a_qty)
          {
            // The remaining quantity after accepting this answer is less than
            // the minimum quantity. Therefore, we delay accepting it now, but
            // still keep track of this best offer.
            best_a_qty = data->state->a_qty;
            best_q_qty = q_qty;
            best_q_date = plan_date;
          }

          // Set the ask date for the next pass through the loop
          if (data->state->a_qty > ROUNDING_ERROR && plan_qty - data->state->a_qty < l->getMinShipment()
            && plan_qty - data->state->a_qty > ROUNDING_ERROR)
          {
            // Check whether the reply is based purely on onhand or not
            if (data->getSolver()->hasOperationPlans(data->getCommandManager()) || next_date <= copy_plan_date)
            {
              // Oops, we didn't get a proper answer we can use for the next loop.
              // Print a warning and simply a bit later.
              plan_date = copy_plan_date + data->getSolver()->getLazyDelay();
              if (loglevel > 0)
                logger << "Demand '" << l << "': Easy retry on " << plan_date << " rather than " << next_date << endl;              
            }
            else
              // The shipment quantity was purely based on onhand in some buffers.
              // In this case we can still trust the next date returned by the search.
              plan_date = next_date;
          }
          else if (next_date <= copy_plan_date
            || (!data->getSolver()->getAllowSplits() && data->state->a_qty > ROUNDING_ERROR)
            || (next_date == Date::infiniteFuture && data->state->a_qty > ROUNDING_ERROR))
          {
            // Oops, we didn't get a proper answer we can use for the next loop.
            // Print a warning and simply try a bit later.
            plan_date = copy_plan_date + data->getSolver()->getLazyDelay();
            if (loglevel > 0)
              logger << "Demand '" << l << "': Easy retry on " << plan_date << " rather than " << next_date << endl;
          }
          else if (getMinimumDelay())
          { 
            Date tmp = copy_plan_date + getMinimumDelay();
            if (tmp > next_date)
            {
              // Assures that the next planning round advances for at least the
              // minimum acceptable delay.
              if (loglevel > 0)
                logger << "Demand '" << l << "': Minimum retry on " << tmp << " rather than " << next_date << endl;
              plan_date = tmp;
            }
            else
              // Use the next-date answer from the solver            
              plan_date = next_date;
          }
          else
            // Use the next-date answer from the solver            
            plan_date = next_date;

          // Delete operationplans - Undo all changes
          data->getCommandManager()->rollback(topcommand);
        }
        else
        {
          // Accepting this answer
          if (data->state->a_qty + ROUNDING_ERROR < q_qty)
          {
            // The demand was only partially planned. We need to do a new
            // 'coordinated' planning run.

            // Delete operationplans created in the 'testing round'
            data->getCommandManager()->rollback(topcommand);

            // Create the correct operationplans
            if (loglevel >= 2)
              logger << "Demand '" << l << "' plans coordination." << endl;
            data->getSolver()->setLogLevel(0);
            double tmpresult = 0;
            try
            {
              for (double remainder = data->state->a_qty;
                remainder > ROUNDING_ERROR; remainder -= data->state->a_qty)
              {
                data->state->q_qty = remainder;
                data->state->q_date = copy_plan_date;
                data->state->curDemand = const_cast<Demand*>(l);
                data->state->curBuffer = nullptr;
                deliveryoper->solve(*this, v);
                if (data->state->a_qty < ROUNDING_ERROR)
                {
                  logger << "Warning: Demand '" << l << "': Failing coordination" << endl;
                  break;
                }
                tmpresult += data->state->a_qty;
              }
            }
            catch (...)
            {
              data->getSolver()->setLogLevel(loglevel);
              throw;
            }
            data->getSolver()->setLogLevel(loglevel);
            data->state->a_qty = tmpresult;
            if (tmpresult == 0) break;
          }

          // Register the new operationplans. We need to make sure that the
          // correct execute method is called!
          if (data->getSolver()->getAutocommit())
          {
            data->getSolver()->scanExcess(data->getCommandManager());
            data->getCommandManager()->commit();
          }

          // Update the quantity to plan in the next loop
          plan_qty -= data->state->a_qty;
          best_a_qty = 0.0;  // Reset 'best-answer' remember
        }

      }
      // Repeat while there is still a quantity left to plan and we aren't
      // exceeding the maximum delivery delay.
      while (plan_qty > ROUNDING_ERROR
        && ((data->getSolver()->getPlanType() != 2 && plan_date < l->getDue() + l->getMaxLateness())
          || (data->getSolver()->getPlanType() == 2 && !data->constrainedPlanning && plan_date < l->getDue() + l->getMaxLateness())
          || (data->getSolver()->getPlanType() == 2 && data->constrainedPlanning && plan_date == l->getDue())
          ));

      if (globalPurchase)
      {
        if (sortedLocation.empty() || (l->getPlannedQuantity() + ROUNDING_ERROR >= l->getQuantity()))
          break;

        if (getLogLevel()>1)
          logger << "Changing demand location for " << l->getName()
          <<  " from "
          << l->getLocation() << " to "
          << sortedLocation.front().first << endl;

        // Prepare for planning on the next location
        const_cast<Demand*>(l)->setLocationNoRecalc(sortedLocation.front().first);
        deliveryoper = l->getDeliveryOperation();
        plan_date = l->getDue();

        // Remove first element of the sorted location
        sortedLocation.pop_front();
      }
    }
    while (globalPurchase);

    if (globalPurchase) {
      // Switch demand back to original location
      const_cast<Demand*>(l)->setLocationNoRecalc(originalLocation);
      l->getDeliveryOperation();
    }

    // Accept the best possible answer.
    // We may have skipped it in the previous loop, awaiting a still better answer
    if (best_a_qty > 0.0 && data->constrainedPlanning)
    {
      if (loglevel>=2) logger << "Demand '" << l << "' accepts a best answer." << endl;
      data->getSolver()->setLogLevel(0);
      try
      {
        for (double remainder = best_q_qty;
          remainder > ROUNDING_ERROR && remainder > l->getMinShipment();
          remainder -= data->state->a_qty)
        {
          data->state->q_qty = remainder;
          data->state->q_date = best_q_date;
          data->state->curDemand = const_cast<Demand*>(l);
          data->state->curBuffer = nullptr;
          deliveryoper->solve(*this,v);
          if (data->state->a_qty < ROUNDING_ERROR)
          {
            logger << "Warning: Demand '" << l << "': Failing accepting best answer" << endl;
            break;
          }
        }
        if (data->getSolver()->getAutocommit())
        {
          data->getSolver()->scanExcess(data->getCommandManager());
          data->getCommandManager()->commit();
        }
      }
      catch (...)
      {
        data->getSolver()->setLogLevel(loglevel);
        throw;
      }
      data->getSolver()->setLogLevel(loglevel);
    }

    // Reset the state stack to the position we found it at.
    while (data->state > mystate) data->pop();

  }
  catch (...)
  {
    // Clean up if any exception happened during the planning of the demand
    while (data->state > mystate) data->pop();
    data->getCommandManager()->rollback(topcommand);
    throw;
  }
}


void SolverCreate::scanExcess(CommandManager* mgr)
{
  for(CommandManager::iterator i = mgr->begin(); i != mgr->end(); ++i)
    if (i->isActive()) scanExcess(&*i);
}


void SolverCreate::scanExcess(CommandList* l)
{
  // Loop over all newly created operationplans found in the command stack
  for(CommandList::iterator cmd = l->begin(); cmd != l->end(); ++cmd)
  {
    switch (cmd->getType())
    {
      case 1:
        // Recurse deeper into command lists
        scanExcess(static_cast<CommandList*>(&*cmd));
        break;
      case 5:
        // Detect excess operationplans and undo them
        auto createcmd = static_cast<CommandCreateOperationPlan*>(&*cmd);
        if (createcmd->getOperationPlan() && createcmd->getOperationPlan()->isExcess())
        {
          if (getLogLevel()>1)
            logger << "Denying creation of redundant operationplan "
                << createcmd->getOperationPlan()->getOperation() << "  "
                << createcmd->getOperationPlan()->getDates() << "  "
                << createcmd->getOperationPlan()->getQuantity() << endl;
          createcmd->rollback();
        }
        break;
    }
  }
}


bool SolverCreate::hasOperationPlans(CommandManager* mgr)
{
  for (CommandManager::iterator i = mgr->begin(); i != mgr->end(); ++i)
  {
    if (i->isActive())
    {
      if (hasOperationPlans(&*i))
        return true;
    }
  }
  return false;
}


bool SolverCreate::hasOperationPlans(CommandList* l)
{
  // Loop over all newly created operationplans found in the command stack
  for (CommandList::iterator cmd = l->begin(); cmd != l->end(); ++cmd)
  {
    switch (cmd->getType())
    {
      case 1:
        // Recurse deeper into command lists
        if (hasOperationPlans(static_cast<CommandList*>(&*cmd)))
          return true;
        break;
      case 5:
        // Command creating an operationplan
        auto opplan = static_cast<CommandCreateOperationPlan*>(&*cmd)->getOperationPlan();
        if (opplan->getQuantity() > 0.0 && !opplan->getDemand())
          return true;
        break;
    }
  }
  return false;
}

}
