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


void SolverMRP::checkOperationCapacity
  (OperationPlan* opplan, SolverMRP::SolverMRPdata& data)
{
  unsigned short constrainedLoads = 0;
  for (OperationPlan::LoadPlanIterator h=opplan->beginLoadPlans();
    h!=opplan->endLoadPlans(); ++h)
    if (h->getResource()->getType() != *(ResourceInfinite::metadata)
      && h->isStart() && h->getLoad()->getQuantity() != 0.0)
    {
      if (++constrainedLoads > 1) break;
    }
  DateRange orig;
  Date minimumEndDate = opplan->getDates().getEnd();
  bool backuplogconstraints = data.logConstraints;
  bool backupForceLate = data.state->forceLate;
  bool recheck, first;

  // Loop through all loadplans, and solve for the resource.
  // This may move an operationplan early or late.
  do
  {
    orig = opplan->getDates();
    recheck = false;
    first = true;
    for (OperationPlan::LoadPlanIterator h=opplan->beginLoadPlans();
      h!=opplan->endLoadPlans() && opplan->getDates()==orig; ++h)
    {
      if (h->getLoad()->getQuantity() == 0.0 || h->getQuantity() == 0.0)
        // Empty load or loadplan (eg when load is not effective)
        continue;
      // Call the load solver - which will call the resource solver.
      data.state->q_operationplan = opplan;
      data.state->q_loadplan = &*h;
      data.state->q_qty = h->getQuantity();
      data.state->q_date = h->getDate();
      h->getLoad()->solve(*this,&data);
      if (opplan->getDates()!=orig)
      {
        if (data.state->a_qty == 0)
          // One of the resources is late. We want to prevent that other resources
          // are trying to pull in the operationplan again. It can only be delayed
          // from now on in this loop.
          data.state->forceLate = true;
        else if (first)
          // First load is ok, but moved the operationplan.
          // We can continue to check the second loadplan.
          orig = opplan->getDates();
        if (!first)
          recheck = true;
      }
      first = false;
    }
    data.logConstraints = false; // Only first loop collects constraint info
  }
  // Imagine there are multiple loads. As soon as one of them is moved, we
  // need to redo the capacity check for the ones we already checked.
  // Repeat until no load has touched the opplan, or till proven infeasible.
  // No need to reloop if there is only a single load (= 2 loadplans)
  while (constrainedLoads>1 && opplan->getDates()!=orig
    && ((data.state->a_qty==0.0 && data.state->a_date > minimumEndDate)
        || recheck));
  // TODO doesn't this loop increment a_penalty incorrectly???

  // Restore original flags
  data.logConstraints = backuplogconstraints; // restore the original value
  data.state->forceLate = backupForceLate;

  // In case of a zero reply, we resize the operationplan to 0 right away.
  // This is required to make sure that the buffer inventory profile also
  // respects this answer.
  if (data.state->a_qty==0.0 && opplan->getQuantity() > 0.0)
    opplan->setQuantity(0.0);
}


bool SolverMRP::checkOperation
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

  // Check the leadtime constraints
  if (data.constrainedPlanning && !checkOperationLeadTime(opplan,data,true))
    // This operationplan is a wreck. It is impossible to make it meet the
    // leadtime constraints
    return false;

  // Set a bookmark in the command list.
  CommandManager::Bookmark* topcommand = data.setBookmark();

  // Temporary variables
  DateRange orig_dates = opplan->getDates();
  bool okay = true;
  Date a_date;
  double a_qty;
  Date orig_q_date = data.state->q_date;
  Date orig_q_date_max = data.state->q_date_max;
  double orig_opplan_qty = data.state->q_qty;
  double q_qty_Flow;
  Date q_date_Flow;
  bool incomplete;
  bool tmp_forceLate = data.state->forceLate;
  bool isPlannedEarly;
  DateRange matnext;

  // Loop till everything is okay. During this loop the quanity and date of the
  // operationplan can be updated, but it cannot be split or deleted.
  data.state->forceLate = false;
  do
  {
    if (isCapacityConstrained())
    {
      // Verify the capacity. This can move the operationplan early or late.
      checkOperationCapacity(opplan,data);
      // Return false if no capacity is available
      if (data.state->a_qty==0.0)
      {
        while (data.state->a_date <= orig_q_date_max)
        {
          opplan->getOperation()->setOperationPlanParameters
            (opplan, orig_opplan_qty,
             orig_q_date_max,
             Date::infinitePast);
          data.state->forceLate = true;
          checkOperationCapacity(opplan,data);
        }
        return false;
      }
    }

    // Check material
    data.state->q_qty = opplan->getQuantity();
    data.state->q_date = opplan->getDates().getEnd();
    a_qty = opplan->getQuantity();
    a_date = data.state->q_date;
    incomplete = false;
    matnext.setStart(Date::infinitePast);
    matnext.setEnd(Date::infiniteFuture);

    // Loop through all flowplans, if propagation is required  // @todo need some kind of coordination run here!!! see test alternate_flow_1
    if (data.getSolver()->getPropagate())
    {
      for (OperationPlan::FlowPlanIterator g=opplan->beginFlowPlans();
          g!=opplan->endFlowPlans(); ++g)
      {
        if (g->getFlow()->isConsumer())
        {
          // Switch back to the main alternate if this flowplan was already    // @todo is this really required? If yes, in this place?
          // planned on an alternate
          if (g->getFlow()->getAlternate())
            g->setFlow(g->getFlow()->getAlternate());

          // Trigger the flow solver, which will call the buffer solver
          data.state->q_flowplan = &*g;
          q_qty_Flow = - data.state->q_flowplan->getQuantity(); // @todo flow quantity can change when using alternate flows -> move to flow solver!
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
            if (data.state->a_date < Date::infiniteFuture)
            {
              OperationPlanState at = opplan->getOperation()->setOperationPlanParameters(
                opplan, 0.01, data.state->a_date, Date::infinitePast, false, false
                );
              if (at.end < matnext.getEnd()) matnext = DateRange(at.start, at.end);
              //xxxif (matnext.getEnd() <= orig_q_date) logger << "STRANGE" << matnext << "  " << orig_q_date << "  " << at.second << "  " << opplan->getQuantity() << endl;
            }

            // Jump out of the loop if the answered quantity is 0.
            if (a_qty <= ROUNDING_ERROR)
            {
              // @TODO disabled To speed up the planning the constraining flow is moved up a
              // position in the list of flows. It'll thus be checked earlier
              // when this operation is asked again
              //const_cast<Operation::flowlist&>(g->getFlow()->getOperation()->getFlows()).promote(g->getFlow());
              // There is absolutely no need to check other flowplans if the
              // operationplan quantity is already at 0.
              break;
            }
          }
          else if (data.state->a_qty >+ q_qty_Flow + ROUNDING_ERROR)
            // Never answer more than asked.
            // The actual operationplan could be bigger because of lot sizing.
            a_qty = - q_qty_Flow / g->getFlow()->getQuantity();
        }
      }
    }

    isPlannedEarly = opplan->getDates().getEnd() < orig_dates.getEnd();

    if (matnext.getEnd() != Date::infiniteFuture && a_qty <= ROUNDING_ERROR
      && matnext.getEnd() <= orig_q_date_max && matnext.getEnd() > orig_q_date)
    {
      // The reply is 0, but the next-date is still less than the maximum
      // ask date. In this case we will violate the post-operation -soft-
      // constraint.
      data.state->q_date = matnext.getEnd();
      orig_q_date = data.state->q_date;
      data.state->q_qty = orig_opplan_qty;
      data.state->a_date = Date::infiniteFuture;
      data.state->a_qty = data.state->q_qty;
      opplan->getOperation()->setOperationPlanParameters(
        opplan, orig_opplan_qty, Date::infinitePast, matnext.getEnd()
        );
      okay = false;
      // Pop actions from the command "stack" in the command list
      data.rollback(topcommand);
      // Echo a message
      if (data.getSolver()->getLogLevel()>1)
        logger << indent(opplan->getOperation()->getLevel())
          << "   Retrying new date." << endl;
    }
    else if (matnext.getEnd() != Date::infiniteFuture && a_qty <= ROUNDING_ERROR
      && matnext.getStart() < a_date && orig_opplan_qty > opplan->getOperation()->getSizeMinimum()
      && (!opplan->getDemand() || orig_opplan_qty > opplan->getDemand()->getMinShipment())
      && data.getSolver()->getAllowSplits()
      && !data.safety_stock_planning)
    {
      // The reply is 0, but the next-date is not too far out.
      // If the operationplan would fit in a smaller timeframe we can potentially
      // create a non-zero reply...
      // Resize the operationplan
      opplan->getOperation()->setOperationPlanParameters(
        opplan, orig_opplan_qty, matnext.getStart(),
        a_date
        );
      if (opplan->getDates().getStart() >= matnext.getStart()
        && opplan->getDates().getEnd() <= a_date
        && opplan->getQuantity() > ROUNDING_ERROR
        && (!opplan->getDemand() || opplan->getQuantity() > opplan->getDemand()->getMinShipment())
        )
      {
        // It worked
        orig_dates = opplan->getDates();
        data.state->q_date = orig_dates.getEnd();
        data.state->q_qty = opplan->getQuantity();
        data.state->a_date = Date::infiniteFuture;
        data.state->a_qty = data.state->q_qty;
        okay = false;
        // Pop actions from the command stack in the command list
        data.rollback(topcommand);
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
      && matnext.getStart() != Date::infiniteFuture
      && matnext.getStart() != Date::infinitePast
      && (data.constrainedPlanning && isCapacityConstrained()))
    {
	    // The operationplan was moved early (because of a resource constraint)
      // and we can't properly trust the reply date in such cases...
      // We want to enforce rechecking the next date.
	    if (data.getSolver()->getLogLevel()>1)
        logger << indent(opplan->getOperation()->getLevel())
               << "   Recheck capacity" << endl;

      // Move the operationplan to the next date where the material is feasible
      opplan->getOperation()->setOperationPlanParameters
        (opplan, orig_opplan_qty,
         matnext.getStart()>orig_dates.getStart() ? matnext.getStart() : orig_dates.getStart(),
         Date::infinitePast);

      // Move the operationplan to a later date where it is feasible.
      data.state->forceLate = true;
      checkOperationCapacity(opplan,data);

      // Reply isn't late enough
      if (opplan->getDates().getEnd() <= orig_q_date_max)
      {
        opplan->getOperation()->setOperationPlanParameters
          (opplan, orig_opplan_qty,
           Date::infinitePast,
           orig_q_date_max);
        data.state->forceLate = true;
        checkOperationCapacity(opplan,data);
      }

      // Reply of this function
      a_qty = 0.0;
      matnext.setEnd(opplan->getDates().getEnd());
    }

  // Compute the final reply
  data.state->a_date = incomplete ? matnext.getEnd() : Date::infiniteFuture;
  data.state->a_qty = a_qty;
  data.state->forceLate = tmp_forceLate;
  if (a_qty > ROUNDING_ERROR)
    return true;
  else
  {
    // Undo the plan
    data.rollback(topcommand);
    return false;
  }
}


bool SolverMRP::checkOperationLeadTime
(OperationPlan* opplan, SolverMRP::SolverMRPdata& data, bool extra)
{
  // No lead time constraints
  if (!data.constrainedPlanning || (!isFenceConstrained() && !isLeadTimeConstrained()))
    return true;

  // Compute offset from the current date: A fence problem uses the release
  // fence window, while a leadtimeconstrained constraint has an offset of 0.
  // If both constraints apply, we need the bigger of the two (since it is the
  // most constraining date.
  Date threshold = Plan::instance().getCurrent();
  if (isFenceConstrained()
    && !(isLeadTimeConstrained() && opplan->getOperation()->getFence()<0L))
    threshold += opplan->getOperation()->getFence();

  // Check the setup operationplan
  OperationPlanState original(opplan);
  bool ok = true;
  bool checkSetup = true;

  // If there are alternate loads we take the best case and assume that
  // at least one of those can give us a zero-time setup.
  // When evaluating the leadtime when solving for capacity we don't use
  // this assumption. The resource solver takes care of the constraints.
  if (extra && isCapacityConstrained())
    for (Operation::loadlist::const_iterator j = opplan->getOperation()->getLoads().begin();
      j != opplan->getOperation()->getLoads().end(); ++j)
      if (j->hasAlternates())
      {
        checkSetup = false;
        break;
      }
  if (checkSetup)
  {
    OperationPlan::iterator i(opplan);
    if (i != opplan->end()
      && i->getOperation() == OperationSetup::setupoperation
      && i->getDates().getStart() < threshold)
    {
      // The setup operationplan is violating the lead time and/or fence
      // constraint. We move it to start on the earliest allowed date,
      // which automatically also moves the owner operationplan.
      i->setStart(threshold);
      threshold = i->getDates().getEnd();
      ok = false;
    }
  }

  // Compare the operation plan start with the threshold date
  if (ok && opplan->getDates().getStart() >= threshold)
    // There is no problem
    return true;

  // Compute how much we can supply in the current timeframe.
  // In other words, we try to resize the operation quantity to fit the
  // available timeframe: used for e.g. time-per operations
  // Note that we allow the complete post-operation time to be eaten
  if (extra)
    // Lead time check during operation resolver
    opplan->getOperation()->setOperationPlanParameters(
      opplan, opplan->getQuantity(),
      threshold,
      original.end + opplan->getOperation()->getPostTime(),
      false
    );
  else
    // Lead time check during capacity resolver
    opplan->getOperation()->setOperationPlanParameters(
      opplan, opplan->getQuantity(),
      threshold,
      original.end,
      true
    );

  // Check the result of the resize
  if (opplan->getDates().getStart() >= threshold
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
    opplan->setStart(threshold);
    // Pick up the earliest date we can reply back
    data.state->a_date = opplan->getDates().getEnd();
    // Set the quantity to 0 (to make sure the buffer doesn't see the supply).
    opplan->setQuantity(0.0);

    // Log the constraint
    if (data.logConstraints && data.planningDemand)
      data.planningDemand->getConstraints().push(
        (threshold == Plan::instance().getCurrent()) ?
          ProblemBeforeCurrent::metadata :
          ProblemBeforeFence::metadata,
         opplan->getOperation(), original.start, original.end,
         original.quantity
        );

    // Deny creation of the operationplan
    return false;
  }
}


void SolverMRP::solve(const Operation* oper, void* v)
{
  // Make sure we have a valid operation
  assert(oper);

  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);
  OperationPlan *z;

  // Call the user exit
  if (userexit_operation) userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  // Find the flow for the quantity-per. This can throw an exception if no
  // valid flow can be found.
  Date orig_q_date = data->state->q_date;
  double flow_qty_per = 1.0;
  double flow_qty_fixed = 0.0;
  bool fixed_flow = false;
  if (data->state->curBuffer)
  {
    Flow* f = oper->findFlow(data->state->curBuffer, data->state->q_date);
    if (f && f->getQuantity()>0.0)
    {
      if (f->getType() == *FlowFixedEnd::metadata || f->getType() == *FlowFixedStart::metadata)
      {
        fixed_flow = true;
        flow_qty_fixed = (oper->getSizeMinimum()<=0 ? 0.001 : oper->getSizeMinimum());
      }
      flow_qty_per = f->getQuantity();
    }
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

  // Find the current list of constraints
  Problem* topConstraint = data->planningDemand ?
    data->planningDemand->getConstraints().top() :
    nullptr;

  // Subtract the post-operation time.
  // Note that we subtract it BEFORE we have snapped the requirement date
  // to our calendar.
  Date prev_q_date_max = data->state->q_date_max;
  data->state->q_date_max = data->state->q_date;
  data->state->q_date -= oper->getPostTime();

  // Align the date to the specified calendar .
  // This alignment is a soft constraint: q_date_max is already set earlier and
  // remains unchanged at the true requirement date.
  Calendar* alignment_cal = Plan::instance().getCalendar();
  if (alignment_cal && !data->state->curDemand)
  {
    // Find the calendar event "at" or "just before" the requirement date
    Calendar::EventIterator evt(alignment_cal, data->state->q_date + Duration(1L), false);
    data->state->q_date = (--evt).getDate();
  }

  // Create the operation plan.
  if (data->state->curOwnerOpplan)
  {
    // There is already an owner and thus also an owner command
    assert(!data->state->curDemand);
    z = oper->createOperationPlan(
          fixed_flow ? flow_qty_fixed : data->state->q_qty / flow_qty_per,
          Date::infinitePast, data->state->q_date, data->state->curDemand,
          data->state->curOwnerOpplan, 0
          );
  }
  else
  {
    // There is no owner operationplan yet. We need a new command.
    CommandCreateOperationPlan *a =
      new CommandCreateOperationPlan(
        oper, fixed_flow ? flow_qty_fixed : data->state->q_qty / flow_qty_per,
        Date::infinitePast, data->state->q_date, data->state->curDemand,
        data->state->curOwnerOpplan
        );
    data->state->curDemand = nullptr;
    z = a->getOperationPlan();
    data->add(a);
  }
  assert(z);
  double orig_q_qty = z->getQuantity();

  // Check the constraints
  data->getSolver()->checkOperation(z,*data);
  data->state->q_date_max = prev_q_date_max;

  // Multiply the operation reply with the flow quantity to get a final reply
  if (data->state->curBuffer)
  {
    if (fixed_flow)
    {
      if (data->state->a_qty > 0.0)
        data->state->a_qty = flow_qty_per;
    }
    else
      data->state->a_qty *= flow_qty_per;
  }

  // Ignore any constraints if we get a complete reply.
  // Sometimes constraints are flagged due to a pre- or post-operation time.
  // Such constraints ultimately don't result in lateness and can be ignored.
  if (data->state->a_qty >= orig_q_qty - ROUNDING_ERROR && data->planningDemand)
    data->planningDemand->getConstraints().pop(topConstraint);

  // Increment the cost
  if (data->state->a_qty > 0.0)
    data->state->a_cost += z->getQuantity() * oper->getCost();

  // Verify the reply
  if (data->state->a_qty == 0 && data->state->a_date <= orig_q_date)
  {
    if (data->getSolver()->getLogLevel()>1)
      logger << indent(oper->getLevel()) << "   Applying lazy delay " << data->getSolver()->getLazyDelay() << endl;
    data->state->a_date = orig_q_date + data->getSolver()->getLazyDelay();
  }
  assert(data->state->a_qty >= 0);

  // Optionally add a penalty depending on the amount of quantity already planned on
  // this operation. This is useful to create a plan where the loading is divided
  // equally over the different available resources, when the search mode MINCOSTPENALTY
  // is used.
  if (data->getSolver()->getRotateResources())
    for (OperationPlan::iterator rr = oper->getOperationPlans(); rr != OperationPlan::end(); ++rr)
      data->state->a_penalty += rr->getQuantity();

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Operation '" << oper->getName()
      << "' answers: " << data->state->a_qty << "  " << data->state->a_date
      << "  " << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


void SolverMRP::solve(const OperationItemSupplier* o, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);
  if (v)
    data->purchase_operations.insert(o);

	// Manage global replenishment
  Item* item = o->getBuffer()->getItem();
  if (item && item->getBoolProperty("global_purchase",false) && data->constrainedPlanning)
  {
	  double total_onhand = 0;
	  double total_ss = 0;

	  Item::bufferIterator iter(item);
	  // iterate over all the buffers to compute the sum on hand and the sum ssl
	  while (Buffer *buffer = iter.next()) {
      double tmp = buffer->getOnHand(data->state->q_date);
		  if (tmp > 0)
        total_onhand += tmp;
		  Calendar* ss_calendar = buffer->getMinimumCalendar();
		  if (ss_calendar) {
			  CalendarBucket* calendarBucket = ss_calendar->findBucket(data->state->q_date, true);
			  if (calendarBucket) {
				  total_ss += calendarBucket->getValue();
			  }
		  }
		  else {
			  total_ss += buffer->getMinimum();
		  }
	  }
	  if (total_ss + ROUNDING_ERROR < total_onhand) {
		  data->state->a_qty = 0;
		  data->state->a_date = Date::infiniteFuture;
		  if (data->getSolver()->getLogLevel()>1)
			  logger << indent(o->getLevel()) << "   Purchasing operation '" << o->getName()
			  << "' replies 0. Requested qty/date: " << data->state->q_qty
			  << "/" << data->state->q_date
			  << " Total OH/SS : " << total_onhand
			  << "/" << total_ss << endl;
		  return;
		}
	}

  solve(static_cast<const Operation*>(o), v);
}


// No need to take post- and pre-operation times into account
void SolverMRP::solve(const OperationRouting* oper, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_operation) userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Routing operation '" << oper->getName()
      << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Find the total quantity to flow into the buffer.
  // Multiple suboperations can all produce into the buffer.
  double flow_qty = 1.0;
  double flow_qty_fixed = 0.0;
  short fixed_flow = -1;
  if (data->state->curBuffer)
  {
    flow_qty = 0.0;
    Flow *f = oper->findFlow(data->state->curBuffer, data->state->q_date);
    if (f)
    {
      // Flow on routing operation
      if (f->getType() == *FlowFixedEnd::metadata || f->getType() == *FlowFixedStart::metadata)
      {
        fixed_flow = 1;
        flow_qty_fixed = f->getQuantity();
      }
      else
      {
        fixed_flow = 0;
        flow_qty += f->getQuantity();
      }
    }
    for (Operation::Operationlist::const_iterator
        e = oper->getSubOperations().begin();
        e != oper->getSubOperations().end();
        ++e)
    {
      f = (*e)->getOperation()->findFlow(data->state->curBuffer, data->state->q_date);
      if (f)
      {
        // Flow on routing steps
        if (f->getType() == *FlowFixedEnd::metadata || f->getType() == *FlowFixedStart::metadata)
        {
          if (fixed_flow == 0)
            throw DataException("Can't mix fixed and proportional quantity flows on operation '" + oper->getName()
                + "' for buffer '" + data->state->curBuffer->getName() + "'");
          fixed_flow = 1;
          flow_qty_fixed += f->getQuantity();
        }
        else
        {
          if (fixed_flow == 1)
            throw DataException("Can't mix fixed and proportional quantity flows on operation '" + oper->getName()
                + "' for buffer '" + data->state->curBuffer->getName() + "'");
          fixed_flow = 0;
          flow_qty += f->getQuantity();
        }
      }
    }
    if ((fixed_flow == 0 && flow_qty <= 0.0) || (fixed_flow == 1 && flow_qty_fixed <= 0.0) || (fixed_flow == -1))
      throw DataException("Invalid producing operation '" + oper->getName()
          + "' for buffer '" + data->state->curBuffer->getName() + "'");
  }
  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation
  data->state->curBuffer = nullptr;
  double a_qty;
  if (fixed_flow == -1) fixed_flow = 0;
  if (fixed_flow)
    a_qty = (oper->getSizeMinimum()<=0) ? 0.001 : oper->getSizeMinimum();
  else
    a_qty = data->state->q_qty / flow_qty;

  // Create the top operationplan
  CommandCreateOperationPlan *a = new CommandCreateOperationPlan(
    oper, a_qty, Date::infinitePast,
    data->state->q_date, data->state->curDemand, data->state->curOwnerOpplan, false
    );
  data->state->curDemand = nullptr;

  // Quantity can be changed because of size constraints on the top operation
  a_qty = a->getOperationPlan()->getQuantity();

  // Make sure the subopplans know their owner & store the previous value
  OperationPlan *prev_owner_opplan = data->state->curOwnerOpplan;
  data->state->curOwnerOpplan = a->getOperationPlan();

  // Reset the max date on the state.
  data->state->q_date_max = data->state->q_date;

  // Loop through the steps
  Date max_Date;
  Duration delay;
  Date top_q_date(data->state->q_date);
  Date q_date;
  for (Operation::Operationlist::const_reverse_iterator
      e = oper->getSubOperations().rbegin();
      e != oper->getSubOperations().rend() && a_qty > 0.0;
      ++e)
  {
    // Plan the next step
    data->state->q_qty = a_qty;
    data->state->q_date = data->state->curOwnerOpplan->getDates().getStart();
    Buffer *tmpBuf = data->state->curBuffer;
    q_date = data->state->q_date;
    (*e)->getOperation()->solve(*this,v);  // @todo if the step itself has child operations, the curOwnerOpplan field is changed here!!!
    a_qty = data->state->a_qty;
    data->state->curBuffer = tmpBuf;

    // Update the top operationplan
    data->state->curOwnerOpplan->setQuantity(a_qty,true);

    // Maximum for the next date
    if (data->state->a_date != Date::infiniteFuture)
    {
      if (delay < data->state->a_date - q_date)
        delay = data->state->a_date - q_date;
      OperationPlanState at = data->state->curOwnerOpplan->getOperation()->setOperationPlanParameters(
        data->state->curOwnerOpplan, 0.01, //data->state->curOwnerOpplan->getQuantity(),
        data->state->a_date, Date::infinitePast, false, false
        );
      if (at.end > max_Date) max_Date = at.end;
    }
  }

  // Check the flows and loads on the top operationplan.
  // This can happen only after the suboperations have been dealt with
  // because only now we know how long the operation lasts in total.
  // Solving for the top operationplan can resize and move the steps that are
  // in the routing!
  /** @todo moving routing opplan doesn't recheck for feasibility of steps... */
  data->state->curOwnerOpplan->createFlowLoads();
  if (data->state->curOwnerOpplan->getQuantity() > 0.0)
  {
    data->state->q_qty = a_qty;
    data->state->q_date = data->state->curOwnerOpplan->getDates().getEnd();
    q_date = data->state->q_date;
    data->getSolver()->checkOperation(data->state->curOwnerOpplan,*data);
    a_qty = data->state->a_qty;
    if (a_qty == 0.0 && data->state->a_date != Date::infiniteFuture)
    {
      // The reply date is the combination of the reply date of all steps and the
      // reply date of the top operationplan.
      if (data->state->a_date > q_date && delay < data->state->a_date - q_date)
        delay = data->state->a_date - q_date;
      if (data->state->a_date > max_Date || max_Date == Date::infiniteFuture)
        max_Date = data->state->a_date;
    }
  }
  data->state->a_date = (max_Date ? max_Date : Date::infiniteFuture);

  if (fixed_flow)
  {
    // Final reply of fixed quantity flow
    if (data->state->a_qty > 0.0)
      data->state->a_qty = flow_qty_fixed;
  }
  else
    // Multiply the operationplan quantity with the flow quantity to get the
    // final reply quantity
    data->state->a_qty = a_qty * flow_qty;

  // Add to the list (even if zero-quantity!)
  if (!prev_owner_opplan) data->add(a);

  // Increment the cost
  if (data->state->a_qty > 0.0)
    data->state->a_cost += data->state->curOwnerOpplan->getQuantity() * oper->getCost();

  // Make other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be nullptr.
  data->state->curOwnerOpplan = prev_owner_opplan;

  if (data->state->a_qty == 0 && data->state->a_date <= top_q_date)
  {
    // At least one of the steps is late, but the reply date at the overall routing level is not late.
    // This situation is possible when capacity or material constraints of routing steps create
    // slack in the routing. The real constrained next date becomes very hard to estimate.
    delay = data->getSolver()->getLazyDelay();
    if (data->getSolver()->getLogLevel()>1)
      logger << indent(oper->getLevel()) << "   Applying lazy delay " << delay << " in routing" << endl;
    data->state->a_date = top_q_date + delay;
  }

  // Check reply date is later than requested date
  assert(data->state->a_date >= top_q_date);
  assert(data->state->a_qty >= 0);

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(oper->getLevel()) << "   Routing operation '" << oper->getName()
      << "' answers: " << data->state->a_qty << "  " << data->state->a_date << "  "
      << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


// No need to take post- and pre-operation times into account
// @todo This method should only be allowed to create 1 operationplan
void SolverMRP::solve(const OperationAlternate* oper, void* v)
{
  SolverMRPdata *data = static_cast<SolverMRPdata*>(v);
  Date origQDate = data->state->q_date;
  double origQqty = data->state->q_qty;
  Buffer *buf = data->state->curBuffer;
  Demand *d = data->state->curDemand;

  // Call the user exit
  if (userexit_operation) userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  short loglevel = data->getSolver()->getLogLevel();
  SearchMode search = oper->getSearch();

  // Message
  if (loglevel>1)
    logger << indent(oper->getLevel()) << "   Alternate operation '" << oper->getName()
      << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Make sure sub-operationplans know their owner & store the previous value
  OperationPlan *prev_owner_opplan = data->state->curOwnerOpplan;

  // Find the flow into the requesting buffer for the quantity-per
  double top_flow_qty_per = 0.0;
  bool top_flow_exists = false;
  bool fixed_flow = false;
  if (buf)
  {
    Flow* f = oper->findFlow(buf, data->state->q_date);
    if (f && f->getQuantity() > 0.0)
    {
      if (f->getType() == *FlowFixedEnd::metadata || f->getType() == *FlowFixedStart::metadata)
        fixed_flow = true;
      top_flow_qty_per = f->getQuantity();
      top_flow_exists = true;
    }
  }

  // Control the planning mode
  bool originalPlanningMode = data->constrainedPlanning;
  data->constrainedPlanning = true;

  // Remember the top constraint
  bool originalLogConstraints = data->logConstraints;
  Problem* topConstraint = data->planningDemand ?
    data->planningDemand->getConstraints().top() :
    nullptr;

  // Try all alternates:
  // - First, all alternates that are fully effective in the order of priority.
  // - Next, the alternates beyond their effective end date.
  //   We loop through these since they can help in meeting a demand on time,
  //   but using them will also create extra inventory or delays.
  double a_qty = data->state->q_qty;
  bool effectiveOnly = true;
  Date a_date = Date::infiniteFuture;
  Date ask_date;
  SubOperation *firstAlternate = nullptr;
  double firstFlowPer;
  while (a_qty > 0)
  {
    // Evaluate all alternates
    double bestAlternateValue = DBL_MAX;
    double bestAlternateQuantity = 0;
    Operation* bestAlternateSelection = nullptr;
    double bestFlowPer = 1.0;
    Date bestQDate;
    for (Operation::Operationlist::const_iterator altIter
        = oper->getSubOperations().begin();
        altIter != oper->getSubOperations().end(); )
    {
      // Set a bookmark in the command list.
      CommandManager::Bookmark* topcommand = data->setBookmark();
      bool nextalternate = true;

      // Filter out alternates that are not suitable
      if ((*altIter)->getPriority() == 0
        || (effectiveOnly && !(*altIter)->getEffective().within(data->state->q_date))
        || (!effectiveOnly && (*altIter)->getEffectiveEnd() > data->state->q_date)
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
      ask_date = effectiveOnly ? origQDate : (*altIter)->getEffectiveEnd();

      // Find the flow into the requesting buffer. It may or may not exist, since
      // the flow could already exist on the top operationplan
      double sub_flow_qty_per = 0.0;
      if (buf)
      {
        // Flow quantity on the suboperation
        Flow* f = (*altIter)->getOperation()->findFlow(buf, ask_date);
        if (f && f->getQuantity() > 0.0)
        {
          sub_flow_qty_per = f->getQuantity();
          bool f_is_fixed = f->getType() == *FlowFixedEnd::metadata || f->getType() == *FlowFixedStart::metadata;
          if (top_flow_exists && fixed_flow != f_is_fixed)
              throw DataException("Can't mix fixed and proportional quantity flows on operation '" + oper->getName()
                + "' for buffer '" + data->state->curBuffer->getName() + "'");
          fixed_flow = f_is_fixed;
        }

        // Flow quantity on the suboperations of a routing suboperation
        if ((*altIter)->getOperation()->getType() == *OperationRouting::metadata)
        {
          SubOperation::iterator subiter((*altIter)->getOperation()->getSubOperations());
          while (SubOperation *o = subiter.next())
          {
            Flow *g = o->getOperation()->findFlow(buf, ask_date);            
            if (g && g->getQuantity() > 0.0)
            {
              sub_flow_qty_per += g->getQuantity();
              bool g_is_fixed = g->getType() == *FlowFixedEnd::metadata || g->getType() == *FlowFixedStart::metadata;
              if ((top_flow_exists || f) && fixed_flow != g_is_fixed)
                throw DataException("Can't mix fixed and proportional quantity flows on operation '" + oper->getName()
                  + "' for buffer '" + data->state->curBuffer->getName() + "'");
              fixed_flow = g_is_fixed;
            }              
          }
        }

        if (!sub_flow_qty_per && !top_flow_exists)
        {
          // Neither the top nor the sub operation have a flow in the buffer,
          // we're in trouble...
          // Restore the planning mode
          data->constrainedPlanning = originalPlanningMode;
          throw DataException("Invalid producing operation '" + oper->getName()
              + "' for buffer '" + buf->getName() + "'");
        }       
      }
      else
        // Default value is 1.0, if no matching flow is required
        sub_flow_qty_per = 1.0;

      // Remember the first alternate
      if (!firstAlternate)
      {
        firstAlternate = *altIter;
        firstFlowPer = sub_flow_qty_per + top_flow_qty_per;
      }

      // Constraint tracking
      if (*altIter != firstAlternate)
        // Only enabled on first alternate
        data->logConstraints = false;
      else
      {
        // Forget previous constraints if we are replanning the first alternate
        // multiple times
        if (data->planningDemand)
          data->planningDemand->getConstraints().pop(topConstraint);
        // Potentially keep track of constraints
        data->logConstraints = originalLogConstraints;
      }

      // Create the top operationplan.
      // Note that both the top- and the sub-operation can have a flow in the
      // requested buffer
      CommandCreateOperationPlan *a = new CommandCreateOperationPlan(
          oper, a_qty, Date::infinitePast, ask_date,
          d, prev_owner_opplan, false
          );
      if (!prev_owner_opplan) data->add(a);

      // Create a sub operationplan
      data->state->q_date = ask_date;
      data->state->curDemand = nullptr;
      data->state->curOwnerOpplan = a->getOperationPlan();
      data->state->curBuffer = nullptr;  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation
      if (fixed_flow)
        data->state->q_qty = (oper->getSizeMinimum()<=0) ? 0.001 : oper->getSizeMinimum();
      else
        data->state->q_qty = a_qty / (sub_flow_qty_per + top_flow_qty_per);

      // Solve constraints on the sub operationplan
      double beforeCost = data->state->a_cost;
      double beforePenalty = data->state->a_penalty;
      if (search == PRIORITY)
      {
        // Message
        if (loglevel>1)
          logger << indent(oper->getLevel()) << "   Alternate operation '" << oper->getName()
            << "' tries alternate '" << (*altIter)->getOperation() << "' " << endl;
        (*altIter)->getOperation()->solve(*this,v);
      }
      else
      {
        data->getSolver()->setLogLevel(0);
        try
        {
          (*altIter)->getOperation()->solve(*this,v);
        }
        catch (...)
        {
          data->getSolver()->setLogLevel(loglevel);
          // Restore the planning mode
          data->constrainedPlanning = originalPlanningMode;
          data->logConstraints = originalLogConstraints;
          throw;
        }
        data->getSolver()->setLogLevel(loglevel);
      }
      double deltaCost = data->state->a_cost - beforeCost;
      double deltaPenalty = data->state->a_penalty - beforePenalty;
      data->state->a_cost = beforeCost;
      data->state->a_penalty = beforePenalty;

      // Keep the lowest of all next-date answers on the effective alternates
      if (effectiveOnly && data->state->a_date < a_date && data->state->a_date > ask_date)
        a_date = data->state->a_date;

      // Now solve for loads and flows of the top operationplan.
      // Only now we know how long that top-operation lasts in total.
      if (data->state->a_qty > ROUNDING_ERROR)
      {
        // Multiply the operation reply with the flow quantity to obtain the
        // reply to return
        data->state->q_qty = data->state->a_qty;
        data->state->q_date = origQDate;
        data->state->curOwnerOpplan->createFlowLoads();
        data->getSolver()->checkOperation(data->state->curOwnerOpplan,*data);
        if (fixed_flow)
          data->state->a_qty = (sub_flow_qty_per + top_flow_qty_per);
        else
          data->state->a_qty *= (sub_flow_qty_per + top_flow_qty_per);

        // Combine the reply date of the top-opplan with the alternate check: we
        // need to return the minimum next-date.
        if (data->state->a_date < a_date && data->state->a_date > ask_date)
          a_date = data->state->a_date;
      }

      // Message
      if (loglevel && search != PRIORITY)
        logger << indent(oper->getLevel()) << "   Alternate operation '" << oper->getName()
          << "' evaluates alternate '" << (*altIter)->getOperation() << "': quantity " << data->state->a_qty
          << ", cost " << deltaCost << ", penalty " << deltaPenalty << endl;

      // Process the result
      if (search == PRIORITY)
      {
        // Undo the operationplans of this alternate
        if (data->state->a_qty < ROUNDING_ERROR) data->rollback(topcommand);

        // Prepare for the next loop
        a_qty -= data->state->a_qty;

        // As long as we get a positive reply we replan on this alternate
        if (data->state->a_qty > 0) nextalternate = false;

        // Are we at the end already?
        if (a_qty < ROUNDING_ERROR)
        {
          a_qty = 0.0;
          break;
        }
      }
      else
      {
        double val = 0.0;
        switch (search)
        {
          case MINCOST:
            val = deltaCost / data->state->a_qty;
            break;
          case MINPENALTY:
            val = deltaPenalty / data->state->a_qty;
            break;
          case MINCOSTPENALTY:
            val = (deltaCost + deltaPenalty) / data->state->a_qty;
            break;
          default:
            LogicException("Unsupported search mode for alternate operation '"
              +  oper->getName() + "'");
        }
        if (data->state->a_qty > ROUNDING_ERROR && (
          val + ROUNDING_ERROR < bestAlternateValue
          || (fabs(val - bestAlternateValue) < ROUNDING_ERROR
              && data->state->a_qty > bestAlternateQuantity)
          ))
        {
          // Found a better alternate
          bestAlternateValue = val;
          bestAlternateSelection = (*altIter)->getOperation();
          bestAlternateQuantity = data->state->a_qty;
          bestFlowPer = sub_flow_qty_per + top_flow_qty_per;
          bestQDate = ask_date;
        }
        // This was only an evaluation
        data->rollback(topcommand);
      }

      // Select the next alternate
      if (nextalternate)
      {
        ++altIter;
        if (altIter == oper->getSubOperations().end() && effectiveOnly)
        {
          // Prepare for a second iteration over all alternates
          effectiveOnly = false;
          altIter = oper->getSubOperations().begin();
        }
      }
    } // End loop over all alternates

    // Replan on the best alternate
    if (bestAlternateQuantity > ROUNDING_ERROR && search != PRIORITY)
    {
      // Message
      if (loglevel>1)
        logger << indent(oper->getLevel()) << "   Alternate operation '" << oper->getName()
          << "' chooses alternate '" << bestAlternateSelection << "' " << search << endl;

      // Create the top operationplan.
      // Note that both the top- and the sub-operation can have a flow in the
      // requested buffer
      CommandCreateOperationPlan *a = new CommandCreateOperationPlan(
          oper, a_qty, Date::infinitePast, bestQDate,
          d, prev_owner_opplan, false
          );
      if (!prev_owner_opplan) data->add(a);

      // Recreate the ask
      if (fixed_flow)
        data->state->q_qty = (oper->getSizeMinimum()<=0) ? 0.001 : oper->getSizeMinimum();
      else
        data->state->q_qty = a_qty / bestFlowPer;
      data->state->q_date = bestQDate;
      data->state->curDemand = nullptr;
      data->state->curOwnerOpplan = a->getOperationPlan();
      data->state->curBuffer = nullptr;  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation

      // Create a sub operationplan and solve constraints
      bestAlternateSelection->solve(*this,v);

      // Now solve for loads and flows of the top operationplan.
      // Only now we know how long that top-operation lasts in total.
      data->state->q_qty = data->state->a_qty;
      data->state->q_date = origQDate;
      data->state->curOwnerOpplan->createFlowLoads();
      data->getSolver()->checkOperation(data->state->curOwnerOpplan,*data);

      // Multiply the operation reply with the flow quantity to obtain the
      // reply to return
      if (fixed_flow)
        data->state->q_qty = bestFlowPer;
      else
        data->state->a_qty *= bestFlowPer;

      // Combine the reply date of the top-opplan with the alternate check: we
      // need to return the minimum next-date.
      if (data->state->a_date < a_date && data->state->a_date > ask_date)
        a_date = data->state->a_date;

      // Prepare for the next loop
      a_qty -= data->state->a_qty;

      // Are we at the end already?
      if (a_qty < ROUNDING_ERROR)
      {
        a_qty = 0.0;
        break;
      }
    }
    else
      // No alternate can plan anything any more
      break;

  } // End while loop until the a_qty > 0

  // Forget any constraints if we are not short or are planning unconstrained
  if (data->planningDemand && (a_qty < ROUNDING_ERROR || !originalLogConstraints))
    data->planningDemand->getConstraints().pop(topConstraint);

  // Unconstrained plan: If some unplanned quantity remains, switch to
  // unconstrained planning on the first alternate.
  // If something could be planned, we expect the caller to re-ask this
  // operation.
  if (!originalPlanningMode && fabs(origQqty - a_qty) < ROUNDING_ERROR && firstAlternate)
  {
    // Switch to unconstrained planning
    data->constrainedPlanning = false;
    data->logConstraints = false;

    // Message
    if (loglevel)
      logger << indent(oper->getLevel()) << "   Alternate operation '" << oper->getName()
        << "' plans unconstrained on alternate '" << firstAlternate->getOperation() << "' " << search << endl;

    // Create the top operationplan.
    // Note that both the top- and the sub-operation can have a flow in the
    // requested buffer
    CommandCreateOperationPlan *a = new CommandCreateOperationPlan(
        oper, a_qty, Date::infinitePast, origQDate,
        d, prev_owner_opplan, false
        );
    if (!prev_owner_opplan) data->add(a);

    // Recreate the ask
    data->state->q_qty = a_qty / firstFlowPer;
    data->state->q_date = origQDate;
    data->state->curDemand = nullptr;
    data->state->curOwnerOpplan = a->getOperationPlan();
    data->state->curBuffer = nullptr;  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation

    // Create a sub operationplan and solve constraints
    firstAlternate->getOperation()->solve(*this,v);

    // Expand flows of the top operationplan.
    data->state->q_qty = data->state->a_qty;
    data->state->q_date = origQDate;
    data->state->curOwnerOpplan->createFlowLoads();
    data->getSolver()->checkOperation(data->state->curOwnerOpplan,*data);

    // Fully planned
    a_qty = 0.0;
    data->state->a_date = origQDate;
  }

  // Set up the reply
  data->state->a_qty = origQqty - a_qty; // a_qty is the unplanned quantity
  data->state->a_date = a_date;
  if (data->state->a_qty == 0 && data->state->a_date <= origQDate)
  {
    if (data->getSolver()->getLogLevel()>1)
      logger << indent(oper->getLevel()) << "   Applying lazy delay " <<
        data->getSolver()->getLazyDelay() << " in alternate" << endl;
    data->state->a_date = origQDate + data->getSolver()->getLazyDelay();
  }
  assert(data->state->a_qty >= 0);

  // Restore the planning mode
  data->constrainedPlanning = originalPlanningMode;
  data->logConstraints = originalLogConstraints;

  // Increment the cost
  if (data->state->a_qty > 0.0)
    data->state->a_cost += data->state->curOwnerOpplan->getQuantity() * oper->getCost();

  // Make sure other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be nullptr.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Message
  if (loglevel>1)
    logger << indent(oper->getLevel()) << "   Alternate operation '" << oper->getName()
      << "' answers: " << data->state->a_qty << "  " << data->state->a_date
      << "  " << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


void SolverMRP::solve(const OperationSplit* oper, void* v)
{
  SolverMRPdata *data = static_cast<SolverMRPdata*>(v);
  Date origQDate = data->state->q_date;
  double origQqty = data->state->q_qty;
  Buffer *buf = data->state->curBuffer;
  Demand *dmd = data->state->curDemand;

  // Call the user exit
  if (userexit_operation) userexit_operation.call(oper, PythonData(data->constrainedPlanning));

  short loglevel = data->getSolver()->getLogLevel();

  // Message
  if (loglevel>1)
    logger << indent(oper->getLevel()) << "   Split operation '" << oper->getName()
      << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Make sure sub-operationplans know their owner & store the previous value
  OperationPlan *prev_owner_opplan = data->state->curOwnerOpplan;

  double top_flow_qty_per = 0.0;
  if (buf)
  {
    // Find the flow into the requesting buffer for the quantity-per
    Flow* f = oper->findFlow(buf, data->state->q_date);
    if (f && f->getQuantity() > 0.0)
    {
      if (f->getType() == *FlowFixedEnd::metadata || f->getType() == *FlowFixedStart::metadata)
        throw DataException("Fixed flows on a split operation are not supported");
      top_flow_qty_per = f->getQuantity();
    }
  }
  else
    // We have a split operation as the delivery operation of a demand.
    top_flow_qty_per = 1.0;

  // Compute the sum of all effective percentages.
  int sum_percent = 0;
  for (Operation::Operationlist::const_iterator iter = oper->getSubOperations().begin();
    iter != oper->getSubOperations().end();
    ++iter)
  {
    if ((*iter)->getEffective().within(data->state->q_date))
      sum_percent += (*iter)->getPriority();
  }
  if (!sum_percent)
    // Oops, no effective suboperations found.
    // TODO Alternative: Look for an earlier date where at least one operation is effective
    throw DataException("No operation is effective for split operation '" + oper->getName() + "' at " + string(data->state->q_date));

  // Loop until we find quantity that can be planned on each alternate.
  bool recheck = true;
  double loop_qty = data->state->q_qty;
  CommandCreateOperationPlan *top_cmd = nullptr;
  while (recheck)
  {
    // Set a bookmark in the command list.
    CommandManager::Bookmark* topcommand = data->setBookmark();

    // Create the top operationplan.
    top_cmd = new CommandCreateOperationPlan(
      oper, top_flow_qty_per ? origQqty / top_flow_qty_per : origQqty,
      Date::infinitePast, origQDate, dmd, prev_owner_opplan, false
      );
    if (!prev_owner_opplan) data->add(top_cmd);

    recheck = false;
    int planned_percentages = 0;
    double planned_quantity = 0.0;
    for (Operation::Operationlist::const_reverse_iterator iter = oper->getSubOperations().rbegin();
      iter != oper->getSubOperations().rend();
      ++iter)
    {
      // Verify effectivity date and percentage > 0
      if (!(*iter)->getPriority() || !(*iter)->getEffective().within(origQDate))
        continue;

      // Message
      if (loglevel>1)
        logger << indent(oper->getLevel()) << "   Split operation '" << oper->getName()
          << "' asks alternate '" << (*iter)->getOperation() << "' " << endl;

      // Find the flow
      Flow* f = (*iter)->getOperation()->findFlow(buf, data->state->q_date);
      double flow_qty_per = 0.0;
      if (f && f->getQuantity()>0.0)
      {
        if (top_flow_qty_per)
          throw DataException("Split operation must have producing flow on the parent opration OR the child operations");
        if (f->getType() == *FlowFixedEnd::metadata || f->getType() == *FlowFixedStart::metadata)
          throw DataException("Fixed flows on a split operation are not supported");
        flow_qty_per = f->getQuantity();
      }
      else if (!top_flow_qty_per)
        // The producing operation doesn't have a valid flow into the current
        // buffer. Either it is missing or it is producing a negative quantity.
        throw DataException("Invalid producing operation '" + oper->getName()
            + "' for buffer '" + data->state->curBuffer->getName() + "'");

      // Plan along this alternate
      double asked = (loop_qty - planned_quantity)
        * (*iter)->getPriority() / (sum_percent - planned_percentages)
        / (flow_qty_per + top_flow_qty_per);
      if (asked > 0)
      {
        // Due to minimum, maximum and multiple size constraints alternates can
        // plan a different quantity than requested. Asked quantity can thus go
        // negative and we skip some alternate.
        data->state->q_qty = asked;
        data->state->q_date = origQDate;
        data->state->curDemand = nullptr;
        data->state->curOwnerOpplan = top_cmd->getOperationPlan();
        data->state->curBuffer = nullptr;  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation
        (*iter)->getOperation()->solve(*this,v);
      }

      // Evaluate the reply
      if (asked <= 0.0)
        // No intention to plan along this alternate
        continue;
      else if (data->state->a_qty == 0)
      {
        // Nothing can be planned here: break out of the loop and don't recheck.
        // The a_date is used below as reply from the top operation.
        loop_qty = 0.0;
        // Undo all plans done on any of the previous alternates
        data->rollback(topcommand);
        top_cmd = nullptr;
        break;
      }
      else if (data->state->a_qty <= asked - ROUNDING_ERROR)
      {
        // Planned short along this alternate. Replan all alternates
        // for a smaller quantity.
        recheck = true;
        loop_qty *= data->state->a_qty / asked;
        // Undo all plans done on any of the previous alternates
        data->rollback(topcommand);
        top_cmd = nullptr;
        break;
      }
      else
      {
        // Successfully planned along this alternate.
        planned_quantity += data->state->a_qty * (flow_qty_per + top_flow_qty_per);
        planned_percentages += (*iter)->getPriority();
      }
    }
  }

  if (loop_qty && top_cmd)
  {
    // Expand flows of the top operationplan.
    data->state->q_qty = top_cmd->getOperationPlan()->getQuantity();
    data->state->q_date = origQDate;
    data->state->curOwnerOpplan->createFlowLoads();
    data->getSolver()->checkOperation(top_cmd->getOperationPlan(), *data);
  }

  // Make sure other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be nullptr.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Final reply
  data->state->a_qty = loop_qty;
  if (loop_qty)
    data->state->a_date = Date::infiniteFuture;

  // Message
  if (loglevel>1)
    logger << indent(oper->getLevel()) << "   Split operation '" << oper->getName()
      << "' answers: " << data->state->a_qty << "  " << data->state->a_date
      << "  " << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


}
