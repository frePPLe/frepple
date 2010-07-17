/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2010 by Johan De Taeye                               *
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


double suggestQuantity(const BufferProcure* b, double f)
{
  // Standard answer
  double order_qty = f;

  // Round to a multiple
  if (b->getSizeMultiple()>0.0)
  {
    int mult = static_cast<int>(order_qty / b->getSizeMultiple() + 0.99999999);
    order_qty = mult * b->getSizeMultiple();
  }

  // Respect minimum size
  if (order_qty < b->getSizeMinimum())
  {
    order_qty = b->getSizeMinimum();
    // round up to multiple
    if (b->getSizeMultiple()>0.0)
    {
      int mult = static_cast<int>(order_qty / b->getSizeMultiple() + 0.99999999);
      order_qty = mult * b->getSizeMultiple();
    }
    // if now bigger than max -> infeasible
    if (order_qty > b->getSizeMaximum())
      throw DataException("Inconsistent procurement parameters on buffer '"
        + b->getName() + "'");
  }

  // Respect maximum size
  if (order_qty > b->getSizeMaximum())
  {
    order_qty = b->getSizeMaximum();
    // round down
    if (b->getSizeMultiple()>0.0)
    {
      int mult = static_cast<int>(order_qty / b->getSizeMultiple());
      order_qty = mult * b->getSizeMultiple();
    }
    // if now smaller than min -> infeasible
    if (order_qty < b->getSizeMinimum())
      throw DataException("Inconsistent procurement parameters on buffer '"
        + b->getName() + "'");
  }

  // Reply
  return order_qty;
}


DECLARE_EXPORT void SolverMRP::solve(const BufferProcure* b, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_buffer) userexit_buffer.call(b, PythonObject(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(b->getLevel()) << "  Procurement buffer '" << b->getName()
    << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Standard reply date
  data->state->a_date = Date::infiniteFuture;

  // Initialize an iterator over reusable existing procurements
  OperationPlan *last_operationplan = NULL;
  OperationPlan::iterator curProcure(b->getOperation());
  while (curProcure != OperationPlan::end() && curProcure->getLocked())
      ++curProcure;
  set<OperationPlan*> moved;

  // Find the latest locked procurement operation. It is used to know what
  // the earliest date is for a new procurement.
  Date earliest_next;
  for (OperationPlan::iterator procs(b->getOperation());
    procs != OperationPlan::end(); ++procs)
      if (procs->getLocked())
        earliest_next = procs->getDates().getEnd();
  Date latest_next = Date::infiniteFuture;

  // Find constraints on earliest and latest date for the next procurement
  if (earliest_next && b->getMaximumInterval())
    latest_next = earliest_next + b->getMaximumInterval();
  if (earliest_next && b->getMinimumInterval())
    earliest_next += b->getMinimumInterval();
  if (data->constrainedPlanning)
  {
    if (data->getSolver()->isLeadtimeConstrained()
      && earliest_next < Plan::instance().getCurrent() + b->getLeadtime())
      earliest_next = Plan::instance().getCurrent() + b->getLeadtime();
    if (data->getSolver()->isFenceConstrained()
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
    // size of the latest procurement.
    if (current_date == earliest_next
      && last_operationplan
      && current_inventory < b->getMinimumInventory())
    {
      double origqty = last_operationplan->getQuantity();
      last_operationplan->setQuantity(suggestQuantity(b,
        last_operationplan->getQuantity()
          + b->getMinimumInventory() - current_inventory));
      produced += last_operationplan->getQuantity() - origqty;
      current_inventory = produced - consumed;
      if (current_inventory < -ROUNDING_ERROR
        && data->state->a_date > earliest_next + b->getMinimumInterval()
        && earliest_next + b->getMinimumInterval() > data->state->q_date
        && data->getSolver()->isMaterialConstrained()
        && data->constrainedPlanning)
          // Resizing didn't work, and we still have shortage
          data->state->a_date = earliest_next + b->getMinimumInterval();
    }

    // At this point, we know we need to reorder...
    earliest_next = Date::infinitePast;
    double order_qty = suggestQuantity(b,
      b->getMaximumInventory() - current_inventory);
    if (order_qty > 0)
    {
      // Create a procurement or update an existing one
      if (curProcure == OperationPlan::end())
      {
        // No existing procurement can be reused. Create a new one.
        CommandCreateOperationPlan *a =
          new CommandCreateOperationPlan(b->getOperation(), order_qty,
            Date::infinitePast, current_date, data->state->curDemand);
        last_operationplan = a->getOperationPlan();
        last_operationplan->insertInOperationplanList();
        produced += last_operationplan->getQuantity();
        data->add(a);
      }
      else if (curProcure->getDates().getEnd() == current_date
        && curProcure->getQuantity() == order_qty)
      {
        // We can reuse this existing procurement unchanged.
        produced += order_qty;
        last_operationplan = &*curProcure;
        moved.insert(last_operationplan);
        do
          ++curProcure;
        while (curProcure != OperationPlan::end()
          && curProcure->getLocked() && moved.find(&*curProcure)!=moved.end());
      }
      else
      {
        // Update an existing procurement to meet current needs
        CommandMoveOperationPlan *a =
          new CommandMoveOperationPlan(&*curProcure, Date::infinitePast, current_date, order_qty);
        last_operationplan = a->getOperationPlan();
        moved.insert(last_operationplan);
        data->add(a);
        produced += last_operationplan->getQuantity();
        do
          ++curProcure;
        while (curProcure != OperationPlan::end()
          && curProcure->getLocked() && moved.find(&*curProcure)!=moved.end());
      }
      if (b->getMinimumInterval())
        earliest_next = current_date + b->getMinimumInterval();
    }
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
  while (curProcure != OperationPlan::end())
  {
    OperationPlan *opplan = &*(curProcure++);
    if (!opplan->getLocked() && moved.find(opplan)!=moved.end())
      data->add(new CommandDeleteOperationPlan(opplan));
  }

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
      if (data->logConstraints)
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
          data->state->a_date = Plan::instance().getCurrent() + b->getLeadtime();
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
