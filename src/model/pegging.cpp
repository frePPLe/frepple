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
#include "frepple/model.h"

namespace frepple
{


DECLARE_EXPORT PeggingIterator::PeggingIterator(const Demand* d) : downstream(false)
{
  // Loop through all delivery operationplans
  first = false;  // ... because the stack is still empty
  for (Demand::OperationPlan_list::const_iterator opplaniter = d->getDelivery().begin();
    opplaniter != d->getDelivery().end(); ++opplaniter)
    followPegging(*opplaniter, 0, (*opplaniter)->getQuantity(), 1.0);
}


DECLARE_EXPORT void PeggingIterator::updateStack
  (short l, double q, double f, const FlowPlan* fc, const FlowPlan* fp, bool p)
{
  // Avoid very small pegging quantities
  if (q < ROUNDING_ERROR) return;

  if (first)
  {
    // We can update the current top element of the stack
    state& t = stack.top();
    t.cons_flowplan = fc;
    t.prod_flowplan = fp;
    t.qty = q;
    t.factor = f;
    t.level = l;
    t.pegged = p;
    first = false;
  }
  else
    // We need to create a new element on the stack
    stack.push(state(l, q, f, fc, fp, p));
}


DECLARE_EXPORT PeggingIterator& PeggingIterator::operator++()
{
  // Validate
  if (stack.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (!downstream)
    throw LogicException("Incrementing a downstream iterator");
  state& st = stack.top();

  // Handle unconsumed material entries on the stack
  if (!st.pegged)
  {
    stack.pop();
    return *this;
  }

  // Mark the top entry in the stack as invalid, so it can be reused
  first = true;

  // Take the consuming flowplan and follow the pegging
  if (st.cons_flowplan)
    followPegging(st.cons_flowplan->getOperationPlan()->getTopOwner(),
      st.level-1, st.qty, st.factor);

  // Pop invalid entries from the stack
  if (first) stack.pop();

  return *this;
}


DECLARE_EXPORT PeggingIterator& PeggingIterator::operator--()
{
  // Validate
  if (stack.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (downstream)
    throw LogicException("Decrementing an upstream iterator");
  state& st = stack.top();

  // Handle unconsumed material entries on the stack
  if (!st.pegged)
  {
    stack.pop();
    return *this;
  }

  // Mark the top entry in the stack as invalid, so it can be reused
  first = true;

  // Take the producing flowplan and follow the pegging
  if (st.prod_flowplan)
    followPegging(st.prod_flowplan->getOperationPlan()->getTopOwner(),
      st.level+1, st.qty, st.factor);

  // Pop invalid entries from the stack
  if (first) stack.pop();

  return *this;
}


DECLARE_EXPORT void PeggingIterator::followPegging
  (OperationPlan::pointer op, short nextlevel, double qty, double factor)
{
  // For each flowplan (producing or consuming depending on whether we go
  // upstream or downstream) ask the buffer to give us the pegged flowplans.
  if (downstream)
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      // We're interested in consuming flowplans of an operationplan when
      // walking upstream.
      if (i->getQuantity()>ROUNDING_ERROR)
        i->getFlow()->getBuffer()->followPegging(*this, &*i, nextlevel, qty, factor);
    }
  else
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      // We're interested in consuming flowplans of an operationplan when
      // walking upstream.
      if (i->getQuantity()<-ROUNDING_ERROR)
        i->getFlow()->getBuffer()->followPegging(*this, &*i, nextlevel, qty, factor);
    }

  // Recursively call this function for all sub-operationplans.
  if (op->getSubOperationPlan())
    // There is only a single suboperationplan
    followPegging(op->getSubOperationPlan(), nextlevel, qty, factor);
  for (OperationPlan::OperationPlanList::const_iterator
      j = op->getSubOperationPlans().begin();
      j != op->getSubOperationPlans().end(); ++j)
    // There is a linked list of suboperationplans
    followPegging(*j, nextlevel, qty, factor);
}

} // End namespace
