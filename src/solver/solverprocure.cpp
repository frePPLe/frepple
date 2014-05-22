/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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


DECLARE_EXPORT void SolverMRP::solve(const BufferProcure* b, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // TODO create a more performant procurement solver. Instead of creating a list of operationplans
  // moves and creations, we can create a custom command "updateProcurements". The commit of
  // this command will update the operationplans.
  // The solve method is only worried about getting a Yes/No reply. The reply is almost always yes,
  // except a) when the request is inside max(current + the lead time, latest procurement + min time
  // after locked procurement), or b) when the min time > 0 and max qty > 0

  // TODO Procurement solver doesn't consider working days of the supplier.

  // Call the user exit
  if (userexit_buffer) userexit_buffer.call(b, PythonObject(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(b->getLevel()) << "  Procurement buffer '" << b->getName()
        << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Standard reply date
  data->state->a_date = Date::infiniteFuture;

  // Collect all reusable existing procurements in a vector data structure.
  // Also find the latest locked procurement operation. It is used to know what
  // the earliest date is for a new procurement.
  int countProcurements = 0;
  int indexProcurements = -1;
  Date earliest_next;
  Date latest_next = Date::infiniteFuture;
  vector<OperationPlan*> procurements;
  for (OperationPlan::iterator i(b->getOperation()); i!=OperationPlan::end(); ++i)
  {
    if (i->getLocked())
      earliest_next = i->getDates().getEnd();
    else
    {
      procurements.push_back(&*i);
      ++countProcurements;
    }
  }
  Date latestlocked = earliest_next;

  // Find constraints on earliest and latest date for the next procurement
  if (earliest_next && b->getMaximumInterval())
    latest_next = earliest_next + b->getMaximumInterval();
  if (earliest_next && b->getMinimumInterval())
    earliest_next += b->getMinimumInterval();
  if (data->constrainedPlanning)
  {
    if (data->getSolver()->isLeadtimeConstrained() && data->getSolver()->isFenceConstrained()
        && earliest_next < Plan::instance().getCurrent() + b->getLeadtime() + b->getFence())
      earliest_next = Plan::instance().getCurrent() + b->getLeadtime() + b->getFence();
    else if (data->getSolver()->isLeadtimeConstrained()
        && earliest_next < Plan::instance().getCurrent() + b->getLeadtime())
      earliest_next = Plan::instance().getCurrent() + b->getLeadtime();
    else if (data->getSolver()->isFenceConstrained()
        && earliest_next < Plan::instance().getCurrent() + b->getFence())
      earliest_next = Plan::instance().getCurrent() + b->getFence();
  }

  // Loop through all flowplans
  Date current_date;
  double produced = 0.0;
  double consumed = 0.0;
  double current_inventory = 0.0;
  const FlowPlan* current_flowplan = NULL;
  for (Buffer::flowplanlist::const_iterator cur=b->getFlowPlans().begin();
      latest_next != Date::infiniteFuture || cur != b->getFlowPlans().end(); )
  {
    if (cur==b->getFlowPlans().end() || latest_next < cur->getDate())
    {
      // Latest procument time is reached
      current_date = latest_next;
      current_flowplan = NULL;
    }
    else if (earliest_next && earliest_next < cur->getDate())
    {
      // Earliest procument time was reached
      current_date = earliest_next;
      current_flowplan = NULL;
    }
    else
    {
      // Date with flowplans found
      if (current_date && current_date >= cur->getDate())
      {
        // When procurements are being moved, it happens that we revisit the
        // same consuming flowplans twice. This check catches this case.
        cur++;
        continue;
      }
      current_date = cur->getDate();
      bool noConsumers = true;
      do
      {
        if (cur->getType() != 1)
        {
          cur++;
          continue;
        }
        current_flowplan = static_cast<const FlowPlan*>(&*(cur++));
        if (current_flowplan->getQuantity() < 0)
        {
          consumed -= current_flowplan->getQuantity();
          noConsumers = false;
        }
        else if (current_flowplan->getOperationPlan()->getLocked())
          produced += current_flowplan->getQuantity();
      }
      // Loop to pick up the last consuming flowplan on the given date
      while (cur != b->getFlowPlans().end() && cur->getDate() == current_date);
      // No further interest in dates with only producing flowplans.
      if (noConsumers) continue;
    }

    // Compute current inventory. The actual onhand in the buffer may be
    // different since we count only consumers and *locked* producers.
    current_inventory = produced - consumed;

    // Hard limit: respect minimum interval
    if (current_date < earliest_next)
    {
      if (current_inventory < -ROUNDING_ERROR
          && current_date >= data->state->q_date
          && b->getMinimumInterval()
          && data->state->a_date > earliest_next
          && data->getSolver()->isMaterialConstrained()
          && data->constrainedPlanning)
        // The inventory goes negative here and we can't procure more
        // material because of the minimum interval...
        data->state->a_date = earliest_next;
      continue;
    }

    // Now the normal reorder check
    if (current_inventory >= b->getMinimumInventory()
        && current_date < latest_next)
    {
      if (current_date == earliest_next) earliest_next = Date::infinitePast;
      continue;
    }

    // When we are within the minimum interval, we may need to increase the
    // size of the previous procurements.
    if (current_date == earliest_next
        && current_inventory < b->getMinimumInventory() - ROUNDING_ERROR)
    {
      for (int cnt=indexProcurements;
        cnt>=0 && current_inventory < b->getMinimumInventory() - ROUNDING_ERROR;
        cnt--)
      {
        double origqty = procurements[cnt]->getQuantity();
        procurements[cnt]->setQuantity(
            procurements[cnt]->getQuantity()
            + b->getMinimumInventory() - current_inventory);
        produced += procurements[cnt]->getQuantity() - origqty;
        current_inventory = produced - consumed;
      }
      if (current_inventory < -ROUNDING_ERROR
          && data->state->a_date > earliest_next
          && earliest_next > data->state->q_date
          && data->getSolver()->isMaterialConstrained()
          && data->constrainedPlanning)
        // Resizing didn't work, and we still have shortage (not only compared
        // to the minimum, but also to 0.
        data->state->a_date = earliest_next;
    }

    // At this point, we know we need to reorder...
    earliest_next = Date::infinitePast;
    double order_qty = b->getMaximumInventory() - current_inventory;
    do
    {
      if (order_qty <= 0)
      {
        if (latest_next == current_date && b->getSizeMinimum())
          // Forced to buy the minumum quantity
          order_qty = b->getSizeMinimum();
        else
          break;
      }
      // Create a procurement or update an existing one
      indexProcurements++;
      if (indexProcurements >= countProcurements)
      {
        // No existing procurement can be reused. Create a new one.
        CommandCreateOperationPlan *a =
          new CommandCreateOperationPlan(b->getOperation(), order_qty,
              Date::infinitePast, current_date, data->state->curDemand);
        a->getOperationPlan()->setMotive(data->state->motive);
        a->getOperationPlan()->insertInOperationplanList(); // TODO Not very nice: unregistered opplan in the list!
        produced += a->getOperationPlan()->getQuantity();
        order_qty -= a->getOperationPlan()->getQuantity();
        data->add(a);
        procurements.push_back(a->getOperationPlan());
        ++countProcurements;
      }
      else if (procurements[indexProcurements]->getDates().getEnd() == current_date
        && procurements[indexProcurements]->getQuantity() == order_qty)
      {
        // Reuse existing procurement unchanged.
        produced += order_qty;
        order_qty = 0;
      }
      else
      {
        // Update an existing procurement to meet current needs
        CommandMoveOperationPlan *a =
          new CommandMoveOperationPlan(procurements[indexProcurements], Date::infinitePast, current_date, order_qty);
        produced += procurements[indexProcurements]->getQuantity();
        order_qty -= procurements[indexProcurements]->getQuantity();
        data->add(a);
      }
      if (b->getMinimumInterval())
      {
        earliest_next = current_date + b->getMinimumInterval();
        break;  // Only 1 procurement allowed at this time...
      }
    }
    while (order_qty > 0 && order_qty >= b->getSizeMinimum());
    if (b->getMaximumInterval())
    {
      current_inventory = produced - consumed;
      if (current_inventory >= b->getMaximumInventory()
          && cur == b->getFlowPlans().end())
        // Nothing happens any more further in the future.
        // Abort procuring based on the max inteval
        latest_next = Date::infiniteFuture;
      else
        latest_next = current_date + b->getMaximumInterval();
    }
  }

  // Get rid of extra procurements that have become redundant
  indexProcurements++;
  while (indexProcurements < countProcurements)
    data->add(new CommandDeleteOperationPlan(procurements[indexProcurements++]));

  // Create the answer
  if (data->constrainedPlanning && (data->getSolver()->isFenceConstrained()
      || data->getSolver()->isLeadtimeConstrained()
      || data->getSolver()->isMaterialConstrained()))
  {
    // Check if the inventory drops below zero somewhere
    double shortage = 0;
    Date startdate;
    for (Buffer::flowplanlist::const_iterator cur = b->getFlowPlans().begin();
        cur != b->getFlowPlans().end(); ++cur)
      if (cur->getDate() >= data->state->q_date
          && cur->getOnhand() < -ROUNDING_ERROR
          && cur->getOnhand() < shortage)
      {
        shortage = cur->getOnhand();
        if (-shortage >= data->state->q_qty) break;
        if (startdate == Date::infinitePast) startdate = cur->getDate();
      }
    if (shortage < 0)
    {
      // Answer a shorted quantity
      data->state->a_qty = data->state->q_qty + shortage;
      // Log a constraint
      if (data->logConstraints && data->planningDemand)
        data->planningDemand->getConstraints().push(
          ProblemMaterialShortage::metadata, b, startdate, Date::infiniteFuture, // @todo calculate a better end date
          -shortage);
      // Nothing to promise...
      if (data->state->a_qty < 0) data->state->a_qty = 0;
      // Check the reply date
      if (data->constrainedPlanning)
      {
        if (data->getSolver()->isFenceConstrained()
            && data->state->q_date < Plan::instance().getCurrent() + b->getFence()
            && data->state->a_date > Plan::instance().getCurrent() + b->getFence())
          data->state->a_date = Plan::instance().getCurrent() + b->getFence();
        if (data->getSolver()->isLeadtimeConstrained()
            && data->state->q_date < Plan::instance().getCurrent() + b->getLeadtime()
            && data->state->a_date > Plan::instance().getCurrent() + b->getLeadtime())
          data->state->a_date = Plan::instance().getCurrent() + b->getLeadtime();   // TODO Doesn't consider calendar of the procurement operation...
        if (latestlocked
            && data->state->q_date < latestlocked
            && data->state->a_date > latestlocked)
          data->state->a_date = latestlocked;
      }
    }
    else
      // Answer the full quantity
      data->state->a_qty = data->state->q_qty;
  }
  else
    // Answer the full quantity
    data->state->a_qty = data->state->q_qty;

  // Increment the cost
  if (b->getItem() && data->state->a_qty > 0.0)
    data->state->a_cost += data->state->a_qty * b->getItem()->getPrice();

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(b->getLevel()) << "  Procurement buffer '" << b
        << "' answers: " << data->state->a_qty << "  " << data->state->a_date
        << "  " << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


}
