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


DECLARE_EXPORT void SolverMRP::checkOperationCapacity
  (OperationPlan* opplan, SolverMRP::SolverMRPdata& data)
{
  bool hasMultipleLoads(opplan->sizeLoadPlans() > 2);
  DateRange orig;

  // Loop through all loadplans, and solve for the resource.
  // This may move an operationplan early or late.
  do
  {
    orig = opplan->getDates();
    for (OperationPlan::LoadPlanIterator h=opplan->beginLoadPlans();
      h!=opplan->endLoadPlans() && opplan->getDates()==orig; ++h)
    {
      data.state->q_operationplan = opplan;
      data.state->q_loadplan = &*h;
      data.state->q_qty = h->getQuantity();
      data.state->q_date = h->getDate();
      // Call the load solver - which will call the resource solver.
      h->getLoad()->solve(*this,&data);
    }
  }
  // Imagine there are multiple loads. As soon as one of them is moved, we
  // need to redo the capacity check for the ones we already checked.
  // Repeat until no load has touched the opplan, or till proven infeasible.
  // No need to reloop if there is only a single load (= 2 loadplans)
  while (hasMultipleLoads && opplan->getDates()!=orig && (data.state->a_qty!=0.0 || data.state->forceLate));
}


DECLARE_EXPORT bool SolverMRP::checkOperation
(OperationPlan* opplan, SolverMRP::SolverMRPdata& data)
{
  // The default answer...
  data.state->a_date = Date::infiniteFuture;
  data.state->a_qty = data.state->q_qty;

  // Handle unavailable time.
  // Note that this unavailable time is checked also in an unconstrained plan.
  // This means that also an unconstrained plan can plan demand late!
  if (opplan->getQuantity() == 0.0)
  {
    // It is possible that the operation could not be created properly.
    // This happens when the operation is not available for enough time.
    // Eg. A fixed time operation needs 10 days on jan 20 on an operation
    //     that is only available only 2 days since the start of the horizon.
    // Resize to the minimum quantity
    opplan->setQuantity(0.0001,false);
    // Move to the earliest start date
    opplan->setStart(Plan::instance().getCurrent());
    // Pick up the earliest date we can reply back
    data.state->a_date = opplan->getDates().getEnd();
    data.state->a_qty = 0.0;
    return false;
  }

  // Store the last command in the list, in order to undo the following
  // commands if required.
  Command* topcommand = data.getLastCommand();

  // Check the leadtime constraints
  if (!checkOperationLeadtime(opplan,data,true))
    // This operationplan is a wreck. It is impossible to make it meet the
    // leadtime constraints
    return false;

  // Loop till everything is okay. During this loop the operationplan can be
  // moved early or late, and its quantity can be changed.
  // However, it cannot be split.
  DateRange orig_dates = opplan->getDates();
  bool okay = true;
  Date a_date;
  Date prev_a_date;
  double a_qty;
  Date orig_q_date = data.state->q_date;
  double orig_opplan_qty = data.state->q_qty;
  double q_qty_Flow;
  Date q_date_Flow;
  TimePeriod delay;
  bool incomplete;
  bool tmp_forceLate = data.state->forceLate;
  data.state->forceLate = false;
  bool isPlannedEarly;
  do
  {
    if (isCapacityConstrained())
    {
      // Verify the capacity. This can move the operationplan early or late.
      checkOperationCapacity(opplan,data);
      // Return false if no capacity is available
      if (data.state->a_qty==0.0) return false;
    }

    // Check material
    data.state->q_qty = opplan->getQuantity();
    data.state->q_date = opplan->getDates().getEnd();
    a_qty = opplan->getQuantity();
    a_date = data.state->q_date;
    incomplete = false;
    delay = 0L;

    // Loop through all flowplans
    for (OperationPlan::FlowPlanIterator g=opplan->beginFlowPlans();
        g!=opplan->endFlowPlans(); ++g)
      if (g->getFlow()->isConsumer())
      {
        // Trigger the flow solver, which will call the buffer solver
        data.state->q_flowplan = &*g;
        q_qty_Flow = - data.state->q_flowplan->getQuantity();
        q_date_Flow = data.state->q_flowplan->getDate();
        g->getFlow()->solve(*this,&data);

        // Validate the answered quantity
        if (data.state->a_qty < q_qty_Flow)
        {
          // Update the opplan, which is required to (1) update the flowplans
          // and to (2) take care of lot sizing constraints of this operation.
          g->setQuantity(-data.state->a_qty, true);
          a_qty = opplan->getQuantity();
          incomplete = true;

          // Validate the answered date of the most limiting flowplan.
          // Note that the delay variable only reflects the delay due to
          // material constraints. If the operationplan is moved early or late
          // for capacity constraints, this is not included.
          delay = data.state->a_date - q_date_Flow;

          // Jump out of the loop if the answered quantity is 0. There is
          // absolutely no need to check other flowplans.
          if (a_qty <= ROUNDING_ERROR) break;
        }
        else if (data.state->a_qty >+ q_qty_Flow + ROUNDING_ERROR)
          // Never answer more than asked.
          // The actual operationplan could be bigger because of lot sizing.
          a_qty = - q_qty_Flow / g->getFlow()->getQuantity();
      }

    isPlannedEarly = opplan->getDates().getEnd() < orig_dates.getEnd();

    if (delay>0L && a_qty <= ROUNDING_ERROR
      && a_date + delay <= data.state->q_date_max && a_date + delay > orig_q_date)
    {
      // The reply is 0, but the next-date is still less than the maximum
      // ask date. In this case we will violate the post-operation -soft-
      // constraint.
      data.state->q_date = a_date + delay;
      data.state->q_qty = orig_opplan_qty;
      data.state->a_date = Date::infiniteFuture;
      data.state->a_qty = data.state->q_qty;
      opplan->getOperation()->setOperationPlanParameters(
        opplan, orig_opplan_qty, Date::infinitePast, a_date + delay
        );
      okay = false;
      // Pop actions from the command "stack" in the command list
      data.undo(topcommand);
      // Echo a message
      if (data.getSolver()->getLogLevel()>1)
        logger << indent(opplan->getOperation()->getLevel()) 
          << "   Retrying new date." << endl;
    }
    else if (delay>0L && a_qty <= ROUNDING_ERROR
      && delay < orig_dates.getDuration())
    {
      // The reply is 0, but the next-date is not too far out.
      // If the operationplan would fit in a smaller timeframe we can potentially
      // create a non-zero reply...
      // Resize the operationplan
      opplan->getOperation()->setOperationPlanParameters(
        opplan, orig_opplan_qty, orig_dates.getStart() + delay, 
        orig_dates.getEnd()
        );
      if (opplan->getDates().getStart() >= orig_dates.getStart() + delay
        && opplan->getDates().getEnd() <= orig_dates.getEnd()
        && opplan->getQuantity() > ROUNDING_ERROR)
      {
        // It worked
        orig_dates = opplan->getDates();
        data.state->q_date = a_date;
        data.state->q_qty = opplan->getQuantity();
        data.state->a_date = Date::infiniteFuture;
        data.state->a_qty = data.state->q_qty;
        okay = false;
        // Pop actions from the command stack in the command list
        data.undo(topcommand);
        // Echo a message
        if (data.getSolver()->getLogLevel()>1)
          logger << indent(opplan->getOperation()->getLevel()) 
            << "   Retrying with a smaller quantity: "
            << opplan->getQuantity() << endl;
      }
      else
      {
        // It didn't work
        opplan->setQuantity(0);
        okay = true;
      }
    }
    else
      okay = true;
  }
  while (!okay);  // Repeat the loop if the operation was moved and the
                  // feasibility needs to be rechecked.

  if (a_qty <= ROUNDING_ERROR && !data.state->forceLate
      && isPlannedEarly
      && a_date != Date::infiniteFuture && isCapacityConstrained())
    {
      // The operationplan was moved early (because of a resource constraint)
      // and we can't properly trust the reply date in such cases...
      // We want to enforce rechecking the next date.

      // Move the operationplan to the next date where the material is feasible
      opplan->getOperation()->setOperationPlanParameters
        (opplan, orig_opplan_qty, a_date + delay, Date::infinitePast);

      // Move the operationplan to a later date where it is feasible.
      data.state->forceLate = true;
      checkOperationCapacity(opplan,data);

      // Reply of this function
      a_qty = 0.0;
      delay = 0L;
      a_date = opplan->getDates().getEnd();
    }

  // Compute the final reply
  data.state->a_date = incomplete ? (a_date + delay) : Date::infiniteFuture;
  data.state->a_qty = a_qty;
  data.state->forceLate = tmp_forceLate;
  if (a_qty > ROUNDING_ERROR)
    return true;
  else
  {
    // Undo the plan
    data.undo(topcommand);
    return false;
  }
}


DECLARE_EXPORT bool SolverMRP::checkOperationLeadtime
(OperationPlan* opplan, SolverMRP::SolverMRPdata& data, bool extra)
{
  // No lead time constraints
  if (!isFenceConstrained() && !isLeadtimeConstrained()) return true;

  // Compute offset from the current date: A fence problem uses the release
  // fence window, while a leadtimeconstrained constraint has an offset of 0.
  // If both constraints apply, we need the bigger of the two (since it is the
  // most constraining date.
  TimePeriod delta;
  if (isFenceConstrained())
  {
    delta = opplan->getOperation()->getFence();
    // Both constraints are used, and the fence is negative (which is an
    // unusual value for a fence)
    if (isLeadtimeConstrained() && delta<0L) delta = 0L;
  }

  // Compare the operation plan start with the threshold date
  if (opplan->getDates().getStart() >= Plan::instance().getCurrent() + delta)
    // There is no problem
    return true;

  // Compute how much we can supply in the current timeframe.
  // In other words, we try to resize the operation quantity to fit the
  // available timeframe: used for e.g. time-per operations
  // Note that we allow the complete post-operation time to be eaten
  if (extra)
    // Leadtime check during operation resolver
    opplan->getOperation()->setOperationPlanParameters(
      opplan, opplan->getQuantity(),
      Plan::instance().getCurrent() + delta,
      opplan->getDates().getEnd() + opplan->getOperation()->getPostTime(),
      false
    );
  else
    // Leadtime check during capacity resolver
    opplan->getOperation()->setOperationPlanParameters(
      opplan, opplan->getQuantity(),
      Plan::instance().getCurrent() + delta,
      opplan->getDates().getEnd(),
      true
    );

  // Check the result of the resize
  if (opplan->getDates().getStart() >= Plan::instance().getCurrent() + delta
    && (!extra || opplan->getDates().getEnd() <= data.state->q_date_max)
    && opplan->getQuantity() > ROUNDING_ERROR)
  {
    // Resizing did work! The operation now fits within constrained limits
    data.state->a_qty = opplan->getQuantity();
    data.state->a_date = opplan->getDates().getEnd();
    // Acknowledge creation of operationplan
    return true;
  }
  else
  {
    // This operation doesn't fit at all within the constrained window.
    data.state->a_qty = 0.0;
    // Resize to the minimum quantity
    if (opplan->getQuantity() + ROUNDING_ERROR < opplan->getOperation()->getSizeMinimum())
      opplan->setQuantity(0.0001,false);
    // Move to the earliest start date
    opplan->setStart(Plan::instance().getCurrent() + delta);
    // Pick up the earliest date we can reply back
    data.state->a_date = opplan->getDates().getEnd();
    // Set the quantity to 0 (to make sure the buffer doesn't see the supply).
    opplan->setQuantity(0.0);
    // Deny creation of the operationplan
    return false;
  }
}


DECLARE_EXPORT void SolverMRP::solve(const Operation* oper, void* v)
{
  // Make sure we have a valid operation
  assert(oper);

  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);
  OperationPlan *z;

  // Find the flow for the quantity-per. This can throw an exception if no
  // valid flow can be found.
  double flow_qty_per = 1.0;
  if (data->state->curBuffer)
  {
    Flow* f = oper->findFlow(data->state->curBuffer, data->state->q_date);
    if (f && f->getQuantity()>0.0)
      flow_qty_per = f->getQuantity();
    else
      // The producing operation doesn't have a valid flow into the current
      // buffer. Either it is missing or it is producing a negative quantity.
      throw DataException("Invalid producing operation '" + oper->getName()
          + "' for buffer '" + data->state->curBuffer->getName() + "'");
  }

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Operation '" << oper->getName() 
      << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Subtract the post-operation time
  Date prev_q_date_max = data->state->q_date_max;
  data->state->q_date_max = data->state->q_date;
  data->state->q_date -= oper->getPostTime();

  // Create the operation plan.
  if (data->state->curOwnerOpplan)
  {
    // There is already an owner and thus also an owner command
    assert(!data->state->curDemand);
    z = oper->createOperationPlan(
          data->state->q_qty / flow_qty_per, 
          Date::infinitePast, data->state->q_date, data->state->curDemand, 
          data->state->curOwnerOpplan, 0
          );
  }
  else
  {
    // There is no owner operationplan yet. We need a new command.
    CommandCreateOperationPlan *a =
      new CommandCreateOperationPlan(
        oper, data->state->q_qty / flow_qty_per,
        Date::infinitePast, data->state->q_date, data->state->curDemand, 
        data->state->curOwnerOpplan
        );
    data->state->curDemand = NULL;
    z = a->getOperationPlan();
    data->add(a);
  }
  assert(z);

  // Check the constraints
  data->getSolver()->checkOperation(z,*data);
  data->state->q_date_max = prev_q_date_max;

  // Multiply the operation reqply with the flow quantity to get a final reply
  if (data->state->curBuffer) data->state->a_qty *= flow_qty_per;

  // Check positive reply quantity
  assert(data->state->a_qty >= 0);

  // Increment the cost
  if (data->state->a_qty > 0.0)
    data->state->a_cost += z->getQuantity() * oper->getCost();

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Operation '" << oper->getName() 
      << "' answers: " << data->state->a_qty << "  " << data->state->a_date 
      << "  " << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


// No need to take post- and pre-operation times into account
DECLARE_EXPORT void SolverMRP::solve(const OperationRouting* oper, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Operation '" << oper->getName() 
      << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Find the total quantity to flow into the buffer.
  // Multiple suboperations can all produce into the buffer.
  double flow_qty = 1.0;
  if (data->state->curBuffer)
  {
    flow_qty = 0.0;
    Flow *f = oper->findFlow(data->state->curBuffer, data->state->q_date);
    if (f) flow_qty += f->getQuantity();
    for (Operation::Operationlist::const_iterator
        e = oper->getSubOperations().begin();
        e != oper->getSubOperations().end();
        ++e)
    {
      f = (*e)->findFlow(data->state->curBuffer, data->state->q_date);
      if (f) flow_qty += f->getQuantity();
    }
    if (flow_qty <= 0.0)
      throw DataException("Invalid producing operation '" + oper->getName()
          + "' for buffer '" + data->state->curBuffer->getName() + "'");
  }
  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation
  data->state->curBuffer = NULL;
  double a_qty(data->state->q_qty / flow_qty);

  // Create the top operationplan
  CommandCreateOperationPlan *a = new CommandCreateOperationPlan(
    oper, a_qty, Date::infinitePast, 
    data->state->q_date, data->state->curDemand, data->state->curOwnerOpplan, false
    );
  data->state->curDemand = NULL;

  // Make sure the subopplans know their owner & store the previous value
  OperationPlan *prev_owner_opplan = data->state->curOwnerOpplan;
  data->state->curOwnerOpplan = a->getOperationPlan();

  // Loop through the steps
  Date max_Date;
  for (Operation::Operationlist::const_reverse_iterator
      e = oper->getSubOperations().rbegin();
      e != oper->getSubOperations().rend() && a_qty > 0.0;
      ++e)
  {
    // Plan the next step
    data->state->q_qty = a_qty;
    data->state->q_date = data->state->curOwnerOpplan->getDates().getStart();
    (*e)->solve(*this,v);
    a_qty = data->state->a_qty;
    // Update the top operationplan
    data->state->curOwnerOpplan->setQuantity(a_qty,true);
    // Maximum for the next date
    if (data->state->a_date > max_Date && data->state->a_date != Date::infiniteFuture)
      max_Date = data->state->a_date;
  }

  // Multiply the operationplan quantity with the flow quantity to get the
  // final reply quantity
  data->state->a_qty = a_qty * flow_qty;

  // Check the flows and loads on the top operationplan.
  // This can happen only after the suboperations have been dealt with
  // because only now we know how long the operation lasts in total.
  // Solving for the top operationplan can resize and move the steps that are
  // in the routing!
  /** @todo moving routing opplan doesn't recheck for feasibility of steps... */
  data->state->curOwnerOpplan->createFlowLoads();
  if (data->state->curOwnerOpplan->getQuantity() > 0.0)
  {
    data->getSolver()->checkOperation(data->state->curOwnerOpplan,*data);
    // The reply date is the combination of the reply date of all steps and the
    // reply date of the top operationplan.
    if (data->state->a_date > max_Date && data->state->a_date != Date::infiniteFuture)
      max_Date = data->state->a_date;
  }
  data->state->a_date = (max_Date ? max_Date : Date::infiniteFuture);
  if (data->state->a_date < data->state->q_date)
    data->state->a_date = data->state->q_date;

  // Add to the list (even if zero-quantity!)
  data->add(a);

  // Increment the cost
  if (data->state->a_qty > 0.0)
    data->state->a_cost += data->state->curOwnerOpplan->getQuantity() * oper->getCost();

  // Make other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be NULL.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Check positive reply quantity
  assert(data->state->a_qty >= 0);

  // Check reply date is later than requested date
  assert(data->state->a_date >= data->state->q_date);

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Operation '" << oper->getName() 
      << "' answers: " << data->state->a_qty << "  " << data->state->a_date << "  "
      << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


// No need to take post- and pre-operation times into account
DECLARE_EXPORT void SolverMRP::solve(const OperationAlternate* oper, void* v)
{
  SolverMRPdata *data = static_cast<SolverMRPdata*>(v);
  Date origQDate = data->state->q_date;
  double origQqty = data->state->q_qty;
  const Buffer *buf = data->state->curBuffer;

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Operation '" << oper->getName() 
      << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Make sure sub-operationplans know their owner & store the previous value
  OperationPlan *prev_owner_opplan = data->state->curOwnerOpplan;
  const Demand *d = data->state->curDemand;

  // Find the flow into the requesting buffer for the quantity-per
  double top_flow_qty_per = 0.0;
  bool top_flow_exists = false;
  if (buf)
  {
    Flow* f = oper->findFlow(buf, data->state->q_date);
    if (f && f->getQuantity() > 0.0)
    {
      top_flow_qty_per = f->getQuantity();
      top_flow_exists = true;
    }
  }

  // Try all alternates:
  // - First, all alternates that are fully effective in the order of priority.
  // - Next, the alternates beyond their effectivity date.
  //   We loop through these since they can help in meeting a demand on time, 
  //   but using them will also create extra inventory or delays.
  double a_qty = data->state->q_qty;
  bool effectiveOnly = true;
  Date a_date = Date::infiniteFuture;
  Date ask_date;
  for (Operation::Operationlist::const_iterator altIter
      = oper->getSubOperations().begin();
      altIter != oper->getSubOperations().end(); )
  {
    // Operations with 0 priority are considered unavailable
    const OperationAlternate::alternateProperty& props 
      = oper->getProperties(*altIter);

    // Filter out alternates that are not suitable
    if (props.first == 0.0
      || (effectiveOnly && !props.second.within(data->state->q_date))
      || (!effectiveOnly && props.second.getEnd() > data->state->q_date)
      )
    {
      ++altIter;
      if (altIter == oper->getSubOperations().end() && effectiveOnly)
      {
        // Prepare for a second iteration over all alternates
        effectiveOnly = false;
        altIter = oper->getSubOperations().begin();
      }
      continue;
    }

    // Establish the ask date
    ask_date = effectiveOnly ? origQDate : props.second.getEnd(); 

    // Find the flow into the requesting buffer. It may or may not exist, since
    // the flow could already exist on the top operationplan
    double sub_flow_qty_per = 0.0;
    if (buf)
    {
      Flow* f = (*altIter)->findFlow(buf, ask_date);
      if (f && f->getQuantity() > 0.0)
        sub_flow_qty_per = f->getQuantity();
      else if (!top_flow_exists)
        // Neither the top nor the sub operation have a flow in the buffer,
        // we're in trouble...
        throw DataException("Invalid producing operation '" + oper->getName()
            + "' for buffer '" + buf->getName() + "'");
    }
    else
      // Default value is 1.0, if no matching flow is required
      sub_flow_qty_per = 1.0;

    // Create the top operationplan.
    // Note that both the top- and the sub-operation can have a flow in the
    // requested buffer
    data->state->q_qty = a_qty / (sub_flow_qty_per + top_flow_qty_per);
    data->state->q_date = ask_date;
    data->state->curDemand = const_cast<Demand*>(d);
    CommandCreateOperationPlan *a = new CommandCreateOperationPlan(
        oper, a_qty, Date::infinitePast, ask_date,
        data->state->curDemand, prev_owner_opplan, false
        );
    data->add(a);
    data->state->curDemand = NULL;
    data->state->curOwnerOpplan = a->getOperationPlan();

    // Create a sub operationplan
    data->state->curBuffer = NULL;  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation
    data->state->q_qty = a_qty / (sub_flow_qty_per + top_flow_qty_per);

    // Solve constraints
    (*altIter)->solve(*this,v);

    // Keep the lowest of all next-date answers on the effective alternates
    if (effectiveOnly && data->state->a_date < a_date && data->state->a_date > ask_date)
      a_date = data->state->a_date;

    // Process the result
    if (data->state->a_qty < ROUNDING_ERROR)
      // Undo all operationplans along this alternate
      data->undo(a);
    else
    {
      // Multiply the operation reply with the flow quantity to obtain the
      // reply to return
      data->state->a_qty *= (sub_flow_qty_per + top_flow_qty_per);

      // Prepare for the next loop
      a_qty -= data->state->a_qty;

      // Now solve for loads and flows of the top operationplan.
      // Only now we know how long that top-operation lasts in total.
      data->state->q_qty = data->state->a_qty;
      data->state->q_date = origQDate;
      data->state->curOwnerOpplan->createFlowLoads();
      data->getSolver()->checkOperation(data->state->curOwnerOpplan,*data);

      // Combine the reply date of the top-opplan with the alternate check: we
      // need to return the minimum next-date.
      if (data->state->a_date < a_date && data->state->a_date > ask_date)
        a_date = data->state->a_date;

      // Are we at the end already?
      if (a_qty < ROUNDING_ERROR)
      {
        a_qty = 0.0;
        break;
      }
    }

    // Select the next alternate
    ++altIter;
    if (altIter == oper->getSubOperations().end() && effectiveOnly)
    {
      // Prepare for a second iteration over all alternates
      effectiveOnly = false;
      altIter = oper->getSubOperations().begin();
    }

  } // End loop over all alternates
  data->state->a_qty = origQqty - a_qty;
  data->state->a_date = a_date;

  // Increment the cost
  if (data->state->a_qty > 0.0)
    data->state->a_cost += data->state->curOwnerOpplan->getQuantity() * oper->getCost();

  // Make other opplans don't take this one as owner any more.
  // We restore the previous owner, which could be NULL.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Check positive reply quantity
  assert(data->state->a_qty >= 0);

  // Check reply date is later than requested date
  assert(data->state->a_date >= data->state->q_date);

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Operation '" << oper->getName() 
      << "' answers: " << data->state->a_qty << "  " << data->state->a_date 
      << "  " << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


}
