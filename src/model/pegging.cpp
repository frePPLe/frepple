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
#include "frepple/model.h"

namespace frepple
{


DECLARE_EXPORT PeggingIterator::PeggingIterator(const Demand* d)
{
  // Loop through all delivery operationplans
  first = false;  // ... because the stack is still empty
  for (Demand::OperationPlan_list::const_iterator opplaniter = d->getDelivery().begin();
    opplaniter != d->getDelivery().end(); ++opplaniter)
    pushflowplans(*opplaniter,true,0,1.0,1.0,true);
} 


DECLARE_EXPORT void PeggingIterator::updateStack
(short l, double q, double f, const FlowPlan* fl, bool p)
{
  // Avoid very small pegging quantities
  if (q < ROUNDING_ERROR) return;

  if (first)
  {
    // We can update the current top element of the stack
    state& t = stack.top();
    t.fl = fl;
    t.qty = q;
    t.factor = f;
    t.level = l;
    t.pegged = p;
    first = false;
  }
  else
    // We need to create a new element on the stack
    stack.push(state(l, q, f, fl, p));
}

//@todo hidden entities should be hidden in the pegging!!!
DECLARE_EXPORT PeggingIterator& PeggingIterator::operator++()
{
  // Validate
  if (stack.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  state& st = stack.top();
  if (st.level > 0)
    throw LogicException("Don't yoyo a pegging iterator");

  first = true;  // The next element can overwrite the existing stack top
  short nextlevel = st.level - 1;
  const FlowPlan *curflowplan = st.fl;
  double curfactor = st.factor;
  double curqty = st.qty;
  if (!stack.top().pegged)
  {
    // Handle unpegged material entries on the stack
    stack.pop();
    return *this;
  }
  else if (curflowplan->getQuantity() > ROUNDING_ERROR)
  {
    // CASE 1:
    // This is a flowplan producing in a buffer. Navigating downstream means
    // finding the flowplans consuming this produced material.

    double peggedQty(0);
    Buffer::flowplanlist::const_iterator f
      = st.fl->getFlow()->getBuffer()->getFlowPlans().begin(st.fl);
    double endQty = f->getCumulativeProduced();
    double startQty = endQty - f->getQuantity();
    if (f->getCumulativeConsumed() <= startQty)
    {
      // CASE 1A: Not consumed enough yet: move forward
      while (f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && f->getCumulativeConsumed() <= startQty) ++f;
      while (f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && ( (f->getQuantity()<=0
              && f->getCumulativeConsumed()+f->getQuantity() < endQty)
              || (f->getQuantity()>0 && f->getCumulativeConsumed() < endQty))
            )
      {
        if (f->getQuantity() < -ROUNDING_ERROR)
        {
          double newqty = - f->getQuantity();
          if (f->getCumulativeConsumed()+f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeConsumed()+f->getQuantity());
          if (f->getCumulativeConsumed() > endQty)
            newqty -= f->getCumulativeConsumed() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          updateStack(nextlevel, curqty*newqty/curflowplan->getQuantity(), -curfactor*newqty/f->getQuantity(), x);
        }
        ++f;
      }
    }
    else
    {
      // CASE 1B: Consumed too much already: move backward
      while ( f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && ((f->getQuantity()<=0 && f->getCumulativeConsumed()+f->getQuantity() < endQty)
              || (f->getQuantity()>0 && f->getCumulativeConsumed() < endQty))) --f;
      while (f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && f->getCumulativeConsumed() > startQty)
      {
        if (f->getQuantity() < -ROUNDING_ERROR)
        {
          double newqty = - f->getQuantity();
          if (f->getCumulativeConsumed()+f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeConsumed()+f->getQuantity());
          if (f->getCumulativeConsumed() > endQty)
            newqty -= f->getCumulativeConsumed() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          updateStack(nextlevel, curqty*newqty/curflowplan->getQuantity(), -curfactor*newqty/f->getQuantity(), x);
        }
        --f;
      }
    }
    if (peggedQty < endQty - startQty)
      // Unpegged material (i.e. material that is produced but never consumed)
      // is handled with a special entry on the stack.
      updateStack(nextlevel, curqty*(endQty - startQty - peggedQty)/curflowplan->getQuantity(), st.factor, curflowplan, false);
  }
  else if (st.fl->getQuantity() < -ROUNDING_ERROR)
  {
    // CASE 2:
    // This is a consuming flowplan. Navigating downstream means taking the
    // producing flowplans of the owning operationplan(s).
    pushflowplans(&*(st.fl->getOperationPlan()->getTopOwner()), false, nextlevel, st.qty, st.factor);
  }
  // No matching flow found
  if (first) stack.pop();
  return *this;
}


DECLARE_EXPORT PeggingIterator& PeggingIterator::operator--()
{
  // Validate
  if (stack.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  state& st = stack.top();
  if (st.level < 0)
    throw LogicException("Dont yoyo a pegging iterator");

  first = true;  // The next element can overwrite the existing stack top
  short nextlevel = st.level + 1;
  const FlowPlan *curflowplan = st.fl;
  double curfactor = st.factor;
  double curqty = st.qty;
  if (!st.pegged)
  {
    // Handle unconsumed material entries on the stack
    stack.pop();
    return *this;
  }
  else if (curflowplan->getQuantity() < -ROUNDING_ERROR)
  {
    // CASE 3:
    // This is a flowplan consuming from a buffer. Navigating upstream means
    // finding the flowplans producing this consumed material.
    double peggedQty(0);
    Buffer::flowplanlist::const_iterator f
      = st.fl->getFlow()->getBuffer()->getFlowPlans().begin(st.fl);
    double endQty = f->getCumulativeConsumed();
    double startQty = endQty + f->getQuantity();
    if (f->getCumulativeProduced() <= startQty)
    {
      // CASE 3A: Not produced enough yet: move forward
      while (f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && f->getCumulativeProduced() <= startQty) ++f;
      while (f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && ( (f->getQuantity()<=0 && f->getCumulativeProduced() < endQty)
              || (f->getQuantity()>0
                  && f->getCumulativeProduced()-f->getQuantity() < endQty))
            )
      {
        if (f->getQuantity() > ROUNDING_ERROR)
        {
          double newqty = f->getQuantity();
          if (f->getCumulativeProduced()-f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeProduced()-f->getQuantity());
          if (f->getCumulativeProduced() > endQty)
            newqty -= f->getCumulativeProduced() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          updateStack(nextlevel, -curqty*newqty/curflowplan->getQuantity(), curfactor*newqty/f->getQuantity(), x);
        }
        ++f;
      }
    }
    else
    {
      // CASE 3B: Produced too much already: move backward
      while ( f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && ((f->getQuantity()<=0 && f->getCumulativeProduced() > endQty)
              || (f->getQuantity()>0
                  && f->getCumulativeProduced()-f->getQuantity() > endQty))) --f;
      while (f!=st.fl->getFlow()->getBuffer()->getFlowPlans().end()
          && f->getCumulativeProduced() > startQty)
      {
        if (f->getQuantity() > ROUNDING_ERROR)
        {
          double newqty = f->getQuantity();
          if (f->getCumulativeProduced()-f->getQuantity() < startQty)
            newqty -= startQty - (f->getCumulativeProduced()-f->getQuantity());
          if (f->getCumulativeProduced() > endQty)
            newqty -= f->getCumulativeProduced() - endQty;
          peggedQty += newqty;
          const FlowPlan *x = dynamic_cast<const FlowPlan*>(&(*f));
          updateStack(nextlevel,
              -curqty*newqty/curflowplan->getQuantity(),
              curfactor*newqty/f->getQuantity(),
              x);
        }
        --f;
      }
    }
    if (peggedQty < endQty - startQty - ROUNDING_ERROR)
      // Unproduced material (i.e. material that is consumed but never
      // produced) is handled with a special entry on the stack.
      updateStack(nextlevel,
          curqty*(peggedQty - endQty + startQty)/curflowplan->getQuantity(),
          st.factor,
          curflowplan,
          false);
  }
  else if (curflowplan->getQuantity() > ROUNDING_ERROR)
  {
    // CASE 4:
    // This is a producing flowplan. Navigating upstream means taking the
    // consuming flowplans of the owning operationplan(s).
    pushflowplans(&*(st.fl->getOperationPlan()->getTopOwner()), true, nextlevel, st.qty, st.factor);
  }
  // No matching flow found
  if (first) stack.pop();
  return *this;
}


DECLARE_EXPORT void PeggingIterator::pushflowplans
(const OperationPlan* op, bool downstream, short nextlevel, double qty, double factor, bool initial)
{
  // Push all flowplans on the stack
  if (downstream)
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      if (i->getQuantity()<0) 
        updateStack(nextlevel, initial?-i->getQuantity():qty, factor, &*i);
    }
  else
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      if (i->getQuantity()>0) 
        updateStack(nextlevel, initial?i->getQuantity():qty, factor, &*i);
    }

  // Recursively call this function for all sub-operationplans.
  if (op->getSubOperationPlan())
    // Only a single suboperationplan
    pushflowplans(op->getSubOperationPlan(), downstream, nextlevel, qty, factor, initial);
  for (OperationPlan::OperationPlanList::const_iterator
      j = op->getSubOperationPlans().begin();
      j != op->getSubOperationPlans().end(); ++j)
    // A linked list of suboperationplans
    pushflowplans(*j, downstream, nextlevel, qty, factor, initial);
}

} // End namespace
