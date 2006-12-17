/***************************************************************************
  file : $URL$
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


/** @todo use of the variable AllLoadsOkay is not nice and clean */
bool MRPSolver::checkOperation
    (OperationPlan* opplan, MRPSolver::MRPSolverdata& data)
{
  // The default answer...
  data.a_date = Date::infiniteFuture;
  data.a_qty = data.q_qty;

  // Check the leadtime constraints
  if(!checkOperationLeadtime(opplan,data))
    // This operationplan is a wreck. It is impossible to make it meet the
    // leadtime constraints
    return false;

  // Loop till everything is okay. During this loop the operationplan can be 
  // moved early or late, and its quantity can be changed. 
  // However, it cannot be split.
  bool okay = true;
  do
  {

    if (isCapacityConstrained())
    {
      // Loop through all loadplans, and solve for the resource.
      // This may move an operationplan early.
      bool hasMultipleLoads(opplan->sizeLoadPlans() > 2);
      do
      {
        data.AllLoadsOkay = true;
        for(OperationPlan::LoadPlanIterator h=opplan->beginLoadPlans();
            h!=opplan->endLoadPlans() && data.AllLoadsOkay; ++h)
        {
          data.q_operationplan = opplan;
          data.q_loadplan = &*h;
          data.q_qty = h->getQuantity();
          data.q_date = h->getDate();
          // Call the resource resolver. Note that it will update the variable
          // data.AllLoadsOkay if it moves the operationplan.
          h->getLoad()->solve(*this,&data);
        }
      }
      // Imagine there are multiple loads. As soon as one of them is moved, we 
      // need to redo the capacity check for the ones we already checked
      // Repeat until no load has touched the opplan, or till proven infeasible
      // No need to reloop if there is only a single load (= 2 loadplans)
      while (hasMultipleLoads && !data.AllLoadsOkay && data.a_qty!=0.0f); 

      // Return false if no capacity is available
      if (data.a_qty==0.0f) return false;
    }

    // Check material
    data.q_qty = opplan->getQuantity();
    data.q_date = opplan->getDates().getEnd();

    Date a_date = data.q_date;
    Date prev_a_date = data.a_date;
    float a_qty = opplan->getQuantity();
    float q_qty_Flow;
    Date q_date_Flow;
    TimePeriod delay;
    bool incomplete = false;

    // Loop through all flowplans
    for(OperationPlan::FlowPlanIterator g=opplan->beginFlowPlans();
        g!=opplan->endFlowPlans(); ++g)
      if (g->getFlow()->isConsumer())
      {
        // Trigger the flow solver, which will call the buffer solver
        data.q_flowplan = &*g;
        q_qty_Flow = - data.q_flowplan->getQuantity();
        q_date_Flow = data.q_flowplan->getDate();
        g->getFlow()->solve(*this,&data);

        // Validate the answered quantity
        if (data.a_qty < q_qty_Flow)
        {
          // Update the opplan, which is required to (1) update the flowplans
          // and to (2) take care of lot sizing constraints of this operation.
          g->setQuantity(-data.a_qty, true);
          a_qty = opplan->getQuantity();
          incomplete = true;
        }
        else
          // Never answer more than asked. The actual operationplan
          // could be bigger because of lot sizing.
          a_qty = - q_qty_Flow / g->getFlow()->getQuantity();

        // Validate the answered date
        if ((data.a_qty < q_qty_Flow) //data.a_date != Date::infiniteFuture xxx
            && (!delay || delay > data.a_date - q_date_Flow))
          // Late supply of material. We expect the end of the operation to be
          // delayed with the same amount of time as the delay.      @todo for a time_per operation this is incorrect!!!
          delay = data.a_date - q_date_Flow;
      }

    // Recheck  xxx
    if (false && delay && a_qty <= ROUNDING_ERROR && a_date + delay <= data.q_date_max)
    {
      data.q_date = a_date + delay;
      opplan->setStart(a_date + delay);
      return checkOperation(opplan, data);
    }

    // Compute the final reply
    Date tmp = incomplete ? (a_date + delay) : Date::infiniteFuture;
    if (tmp==Date::infiniteFuture) data.a_date = prev_a_date;
    else if (prev_a_date == Date::infiniteFuture) data.a_date = tmp;
    else data.a_date = (tmp>prev_a_date) ? tmp : prev_a_date;
    data.a_qty = a_qty;
    // Reply OK/NOK
    return a_qty > ROUNDING_ERROR;   // xxx unconditionally leaves the loop

    if (!okay)
    {
      // xxx clean up propagated operation plans before going into the loop again?
      // Pop actions from the command "stack" in the command list
    }
  }
  while (!okay);  // Repeat the loop if the operation was moved and the 
                  // feasibility needs to be rechecked.
}


bool MRPSolver::checkOperationLeadtime
  (OperationPlan* opplan, MRPSolver::MRPSolverdata& data)
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
  opplan->getOperation()->setOperationPlanParameters(
    opplan,opplan->getQuantity(),
    Plan::instance().getCurrent() + delta,
    opplan->getDates().getEnd() + opplan->getOperation()->getPostTime(),
    opplan->getOperation()->getPostTime() ? false : true
    );

  // Check the result of the resize
  if (opplan->getDates().getStart() >= Plan::instance().getCurrent() + delta
      && opplan->getDates().getEnd() <= data.q_date_max
      && opplan->getQuantity() > 0)
  {
    // Resizing did work! The operation now fits within constrained limits
    data.a_qty = opplan->getQuantity();
    data.a_date = opplan->getDates().getEnd(); 
    // Acknowledge creation of operationplan
    return true;
  }
  else
  {
    // This operation doesn't fit at all within the constrained window.
    data.a_qty = 0.0f;
    // Move to the current date
    opplan->setStart(Plan::instance().getCurrent());
    // Pick up the earliest date we can reply back
    data.a_date = opplan->getDates().getEnd();
    // Set the quantity to 0 (to make sure the buffer doesn't see the supply)
    opplan->setQuantity(0.0f);
    // Deny creation of the operationplan
    return false;
  }
}


void MRPSolver::solve(Operation* oper, void* v)
{
  // Make sure we have a valid operation
  assert(oper);

  MRPSolverdata* Solver = static_cast<MRPSolverdata*>(v);
  OperationPlan *z;
  CommandCreateOperationPlan *a = NULL;

  // Find the flow for the quantity-per. This can throw an exception if no
  // valid flow can be found.
  float flow_qty_per = 1.0f;
  if (Solver->curBuffer)
  {
    Flow* f = oper->findFlow(Solver->curBuffer);
    if (f && f->getQuantity() > 0.0f)
      flow_qty_per = f->getQuantity();
    else
      // The producing operation doesn't have a valid flow into the current
      // buffer. Either it is missing or it is producing a negative quantity.
      throw DataException("Invalid producing operation '" + oper->getName()
        + "' for buffer '" + Solver->curBuffer->getName() + "'");
  }

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Subtract the post-operation time
  Solver->q_date_max = Solver->q_date;
  Solver->q_date -= oper->getPostTime();

  // Create the operation plan.
  if (Solver->curOwnerOpplan)
  {
    // There is already an owner and thus also an owner command
    assert(!Solver->curDemand);
    z = oper->createOperationPlan(Solver->q_qty / flow_qty_per, Date::infinitePast,
         Solver->q_date, Solver->curDemand, true, Solver->curOwnerOpplan, 0);
  }
  else
  {
    // There is no owner operationplan yet. We need a new command.
    a = new CommandCreateOperationPlan(oper,Solver->q_qty / flow_qty_per, Date::infinitePast,
          Solver->q_date,Solver->curDemand,Solver->curOwnerOpplan);
    Solver->curDemand = NULL;
    z = a->getOperationPlan();
  }
  assert(z);

  // Check the constraints
  Solver->getSolver()->checkOperation(z,*Solver);
  if (a) Solver->actions.add(a);

  // Multiply the operation reqply with the flow quantity to get a final reply
  if (Solver->curBuffer) Solver->a_qty *= flow_qty_per;

  // Check positive reply quantity
  assert(Solver->a_qty >= 0);

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


// No need to take post- and pre-operation times into account
void MRPSolver::solve(OperationRouting* oper, void* v)
{
  MRPSolverdata* Solver = static_cast<MRPSolverdata*>(v);

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Find the total quantity to flow into the buffer.
  // Multiple suboperations can all produce into the buffer.
  float flow_qty = 1.0f;
  if (Solver->curBuffer)
  {
    flow_qty = 0.0f;
    Flow *f = oper->findFlow(Solver->curBuffer);
    if (f) flow_qty += f->getQuantity();
    for (Operation::Operationlist::const_iterator 
      e = oper->getSubOperations().begin(); 
      e != oper->getSubOperations().end(); 
      ++e)
    {
      f = (*e)->findFlow(Solver->curBuffer);
      if (f) flow_qty += f->getQuantity();
    }
    if (flow_qty <= 0.0f)
      throw DataException("Invalid producing operation '" + oper->getName()
          + "' for buffer '" + Solver->curBuffer->getName() + "'");
  }
  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation
  Solver->curBuffer = NULL;  
  float a_qty(Solver->q_qty / flow_qty);

  // Create the top operationplan
  CommandCreateOperationPlan *a = new CommandCreateOperationPlan(oper, a_qty,
    Date::infinitePast, Solver->q_date, Solver->curDemand, Solver->curOwnerOpplan, false);
  Solver->curDemand = NULL;

  // Make sure the subopplans know their owner & store the previous value
  OperationPlan *prev_owner_opplan = Solver->curOwnerOpplan;
  Solver->curOwnerOpplan = a->getOperationPlan();

  // Loop through the steps
  Date max_Date;
  for (Operation::Operationlist::const_reverse_iterator 
    e = oper->getSubOperations().rbegin();
    e != oper->getSubOperations().rend() && a_qty > 0.0f; 
    ++e)
  {
    // Plan the next step
    Solver->q_qty = a_qty;
    Solver->q_date = Solver->curOwnerOpplan->getDates().getStart();
    (*e)->solve(*this,v);
    a_qty = Solver->a_qty;
    // Update the top operationplan
    Solver->curOwnerOpplan->setQuantity(a_qty,true);
    // Maximum for the next date
    if (Solver->a_date > max_Date && Solver->a_date != Date::infiniteFuture)
      max_Date = Solver->a_date;
  }

  // Multiply the operationplan quantity with the flow quantity to get the
  // final reply quantity
  Solver->a_qty = a_qty * flow_qty;

  // Check the flows and loads on the top operationplan.
  // This can happen only after the suboperations have been dealt with
  // because only now we know how long the operation lasts in total.
  // Solving for the top operationplan can resize and move the steps that are
  // in the routing!
  /** @todo moving routing opplan doesn't recheck for feasibility of steps... */
  Solver->curOwnerOpplan->createFlowLoads();
  Solver->getSolver()->checkOperation(Solver->curOwnerOpplan,*Solver);

  // The reply date is the combination of the reply date of all steps and the
  // reply date of the top operationplan.
  if (Solver->a_date > max_Date && Solver->a_date != Date::infiniteFuture)
    max_Date = Solver->a_date;
  Solver->a_date = (max_Date ? max_Date : Date::infiniteFuture);

  // Add to the list (even if zero-quantity!)
  Solver->actions.add(a);

  // Make other operationplans don't take this one as owner any more.
  // We restore the previous owner, which could be NULL.
  Solver->curOwnerOpplan = prev_owner_opplan;

  // Check positive reply quantity
  assert(Solver->a_qty >= 0);

  // Check reply date is later than requested date
  assert(Solver->a_date >= Solver->q_date);

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


// No need to take post- and pre-operation times into account
void MRPSolver::solve(OperationAlternate* oper, void* v)
{
  MRPSolverdata *Solver = static_cast<MRPSolverdata*>(v);
  Date origQDate = Solver->q_date;
  float origQqty = Solver->q_qty;
  Buffer *buf = Solver->curBuffer;

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Make sure sub-operationplans know their owner & store the previous value
  OperationPlan *prev_owner_opplan = Solver->curOwnerOpplan;
  Demand *d = Solver->curDemand;

  // Find the flow into the requesting buffer for the quantity-per
  float top_flow_qty_per = 0.0f;
  bool top_flow_exists = false;
  if (buf)
  {
    Flow* f = oper->findFlow(buf);
    if (f && f->getQuantity() > 0.0f)
    {
      top_flow_qty_per = f->getQuantity();
      top_flow_exists = true;
    }
  }

  // Try all alternates
  float a_qty = Solver->q_qty;
  Date a_date = Date::infiniteFuture;
  for (Operation::Operationlist::const_iterator altIter
       = oper->getSubOperations().begin();
       altIter != oper->getSubOperations().end(); ++altIter)
  {
    // Operations with 0 priority are considered unavailable
    if (oper->getPriority(*altIter) == 0.0f) continue;

    // Find the flow into the requesting buffer. It may or may not exist, since
    // the flow could already exist on the top operationplan
    float sub_flow_qty_per = 0.0f;
    if (buf)
    {
      Flow* f = (*altIter)->findFlow(buf);
      if (f && f->getQuantity() > 0.0f)
        sub_flow_qty_per = f->getQuantity();
      else if (!top_flow_exists)
        // Neither the top nor the sub operation have a flow in the buffer,
        // we're in trouble...
        throw DataException("Invalid producing operation '" + oper->getName()
          + "' for buffer '" + buf->getName() + "'");
    }
    else
      // Default value is 1.0, if no matching flow is required
      sub_flow_qty_per = 1.0f;

    // Create the top operationplan.
    // Note that both the top- and the sub-operation can have a flow in the
    // requested buffer
    Solver->q_qty = a_qty / (sub_flow_qty_per + top_flow_qty_per);
    Solver->q_date = origQDate;
    Solver->curDemand = d;
    CommandCreateOperationPlan *a = new CommandCreateOperationPlan(oper, a_qty,
      Date::infinitePast, origQDate, d, prev_owner_opplan, false);
    Solver->curDemand = NULL;
    Solver->curOwnerOpplan = a->getOperationPlan();

    // Create a sub operationplan
    Solver->curBuffer = NULL;  // Because we already took care of it... @todo not correct if the suboperation is again a owning operation
    Solver->q_qty = a_qty / (sub_flow_qty_per + top_flow_qty_per);
    (*altIter)->solve(*this,v);
    if (Solver->a_date < a_date) a_date = Solver->a_date;
    if (Solver->a_qty < ROUNDING_ERROR)
      // Nothing could be planned on this alternate. Need to keep the
      // create command anyway, since there may exist move commands for the
      // created operationplans!
      Solver->actions.add(a);
    else
    {
      // Multiply the operation reply with the flow quantity to obtain the
      // reply to return
      Solver->a_qty *= (sub_flow_qty_per + top_flow_qty_per);

      // Prepare for the next loop
      a_qty -= Solver->a_qty;

      // Now solve for loads and flows of the top operationplan.
      // Only now we know how long that top-operation lasts in total.
      Solver->q_qty = Solver->a_qty;
      Solver->q_date = origQDate;
      Solver->curOwnerOpplan->createFlowLoads();
      Solver->getSolver()->checkOperation(Solver->curOwnerOpplan,*Solver);

      // Combine the reply date of the top-opplan with the alternate check: we
      // need to return the maximum date.
      if (Solver->a_date > a_date) a_date = Solver->a_date;

      // Operationplan accepted
      Solver->actions.add(a);

      // Are we at the end already?
      if (a_qty < ROUNDING_ERROR)
      {
        a_qty = 0.0f;
        break;
      }
    }
  }
  Solver->a_qty = origQqty - a_qty;
  Solver->a_date = a_date;

  // Make other opplans don't take this one as owner any more.
  // We restore the previous owner, which could be NULL.
  Solver->curOwnerOpplan = prev_owner_opplan;

  // Check positive reply quantity
  assert(Solver->a_qty >= 0);

  // Check reply date is later than requested date
  assert(Solver->a_date >= Solver->q_date);

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


// No need to take post- and pre-operation times into account
void MRPSolver::solve(OperationEffective* oper, void* v)
{
  MRPSolverdata *Solver = static_cast<MRPSolverdata*>(v);

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Create the operationplan. This automatically creates the proper 
  // suboperationplan too.
  CommandCreateOperationPlan *a = new CommandCreateOperationPlan(oper, 
    Solver->q_qty, Date::infinitePast, Solver->q_date, Solver->curDemand, 
    Solver->curOwnerOpplan, false);
  OperationPlanEffective *opplan = 
    dynamic_cast<OperationPlanEffective*>(a->getOperationPlan());

  Solver->curDemand = NULL;
  Solver->actions.add(a);

  // Check the child operationplan
  Date origQDate = Solver->q_date;
  opplan->getSubOperationPlan()->getOperation()->solve(*this,v);
  Date aDate = Solver->a_date;

  // Check the top operationplan
  Solver->q_qty = Solver->a_qty;
  Solver->q_date = origQDate;
  opplan->createFlowLoads();
  Solver->getSolver()->checkOperation(opplan,*Solver);
  if (Solver->a_date < aDate) Solver->a_date = aDate;

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=(oper->getLevel()>0?oper->getLevel():0); i; --i) clog << " ";
    clog << "   Operation '" << oper->getName() << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


}
