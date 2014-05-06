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
#include "frepple/model.h"

namespace frepple
{

DECLARE_EXPORT const MetaCategory* PeggingIterator::metadata;


int PeggingIterator::initialize()
{
  // Initialize the pegging metadata
  PeggingIterator::metadata = new MetaCategory("pegging","peggings");

  // Initialize the Python type
  PythonType& x = PythonExtension<PeggingIterator>::getType();
  x.setName("peggingIterator");
  x.setDoc("frePPLe iterator for demand pegging");
  x.supportgetattro();
  x.supportiter();
  const_cast<MetaCategory*>(PeggingIterator::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


DECLARE_EXPORT PeggingIterator::PeggingIterator(const Demand* d)
  : downstream(false), firstIteration(true)
{
  // Loop through all delivery operationplans
  first = false;  // ... because the stack is still empty
  for (Demand::OperationPlan_list::const_iterator opplaniter = d->getDelivery().begin();
      opplaniter != d->getDelivery().end(); ++opplaniter)
    followPegging(*opplaniter, 0, (*opplaniter)->getQuantity(), 1.0);

  // Initialize Python type information
  initType(metadata);
}


DECLARE_EXPORT PeggingIterator::PeggingIterator(const OperationPlan* opplan, bool b)
  : downstream(b), firstIteration(true)
{
  first = false;  // ... because the stack is still empty
  followPegging(opplan, 0, opplan->getQuantity(), 1.0);
  initType(metadata);
}


DECLARE_EXPORT void PeggingIterator::updateStack
(short l, double q, double f, const FlowPlan* fc, const FlowPlan* fp, bool p)
{
  // Avoid very small pegging quantities
  if (q < 0.1) return;

  if (first)
  {
    // We can update the current top element of the stack
    state& t = states.top();
    t.cons_flowplan = fc;
    t.prod_flowplan = fp;
    t.qty = q;
    t.factor = f;
    t.level = l;
    t.pegged = p;
    t.opplan = NULL;
    first = false;
  }
  else
    // We need to create a new element on the stack
    states.push(state(l, q, f, fc, fp, NULL, p));
}


DECLARE_EXPORT void PeggingIterator::updateStack
(short l, double q, double f, const OperationPlan* op, bool p)
{
  // Avoid very small pegging quantities
  if (q < 0.1) return;

  if (first)
  {
    // We can update the current top element of the stack
    state& t = states.top();
    t.cons_flowplan = NULL;
    t.prod_flowplan = NULL;
    t.qty = q;
    t.factor = f;
    t.level = l;
    t.pegged = p;
    t.opplan = op;
    first = false;
  }
  else
    // We need to create a new element on the stack
    states.push(state(l, q, f, NULL, NULL, op, p));
}


DECLARE_EXPORT PeggingIterator& PeggingIterator::operator++()
{
  // Validate
  if (states.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (!downstream)
    throw LogicException("Incrementing a downstream iterator");
  state& st = states.top();

  // Handle unconsumed material entries on the stack
  if (!st.pegged)
  {
    states.pop();
    return *this;
  }

  // Mark the top entry in the stack as invalid, so it can be reused
  first = true;

  // Take the consuming flowplan and follow the pegging
  if (st.cons_flowplan)
    followPegging(st.cons_flowplan->getOperationPlan()->getTopOwner(),
        st.level-1, st.qty, st.factor);

  // Pop invalid entries from the stack
  if (first) states.pop();

  return *this;
}


DECLARE_EXPORT PeggingIterator& PeggingIterator::operator--()
{
  // Validate
  if (states.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (downstream)
    throw LogicException("Decrementing an upstream iterator");
  state& st = states.top();

  // Handle unconsumed material entries on the stack
  if (!st.pegged)
  {
    states.pop();
    return *this;
  }

  // Mark the top entry in the stack as invalid, so it can be reused
  first = true;

  // Take the producing flowplan and follow the pegging
  if (st.prod_flowplan)
    followPegging(st.prod_flowplan->getOperationPlan()->getTopOwner(),
        st.level+1, st.qty, st.factor);

  // Pop invalid entries from the stack
  if (first) states.pop();

  return *this;
}


DECLARE_EXPORT void PeggingIterator::followPegging
(const OperationPlan* op, short nextlevel, double qty, double factor)
{
  // For each flowplan (producing or consuming depending on whether we go
  // upstream or downstream) ask the buffer to give us the pegged flowplans.
  bool noFlowPlans = true;
  if (downstream)
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      // We're interested in producing flowplans of an operationplan when
      // walking downstream.
      if (i->getQuantity()>ROUNDING_ERROR)
      {
        i->getFlow()->getBuffer()->followPegging(*this, &*i, nextlevel, qty, factor);
        noFlowPlans = false;
      }
    }
  else
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      // We're interested in consuming flowplans of an operationplan when
      // walking upstream.
      if (i->getQuantity()<-ROUNDING_ERROR)
      {
        i->getFlow()->getBuffer()->followPegging(*this, &*i, nextlevel, qty, factor);
        noFlowPlans = false;
      }
    }

  // Special case: upstream pegging for a delivery operationplan which
  // doesn't have any flowplans
  if (noFlowPlans && op->getDemand() && !downstream)
  {
    updateStack(nextlevel, qty, factor, op);
    first = false;
  }

  // Recursively call this function for all sub-operationplans.
  for (OperationPlan::iterator j(op); j != OperationPlan::end(); ++j)
    followPegging(&*j, nextlevel, qty, factor);
}


DECLARE_EXPORT PyObject* PeggingIterator::iternext()
{
  if (firstIteration)
    firstIteration = false;
  else
    operator--();
  if (!operator bool()) return NULL;
  Py_INCREF(this);
  return static_cast<PyObject*>(this);
}


DECLARE_EXPORT PyObject* PeggingIterator::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_level))
    return PythonObject(getLevel());
  if (attr.isA(Tags::tag_consuming))
    return PythonObject(getConsumingOperationplan());
  if (attr.isA(Tags::tag_producing))
    return PythonObject(getProducingOperationplan());
  if (attr.isA(Tags::tag_buffer))
    return PythonObject(getBuffer());
  if (attr.isA(Tags::tag_quantity_demand))
    return PythonObject(getQuantityDemand());
  if (attr.isA(Tags::tag_quantity_buffer))
    return PythonObject(getQuantityBuffer());
  if (attr.isA(Tags::tag_pegged))
    return PythonObject(getPegged());
  if (attr.isA(Tags::tag_consuming_date))
    return PythonObject(getConsumingDate());
  if (attr.isA(Tags::tag_producing_date))
    return PythonObject(getProducingDate());
  return NULL;
}


} // End namespace
