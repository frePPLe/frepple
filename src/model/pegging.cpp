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
#include "frepple/model.h"

namespace frepple
{

const MetaCategory* PeggingIterator::metadata;
const MetaCategory* PeggingDemandIterator::metadata;


int PeggingIterator::initialize()
{
  // Initialize the pegging metadata
  PeggingIterator::metadata = MetaCategory::registerCategory<PeggingIterator>("pegging","peggings");
  registerFields<PeggingIterator>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python type
  PythonType& x = PythonExtension<PeggingIterator>::getPythonType();
  x.setName("peggingIterator");
  x.setDoc("frePPLe iterator for operationplan pegging");
  x.supportgetattro();
  x.supportiter();
  const_cast<MetaCategory*>(PeggingIterator::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


int PeggingDemandIterator::initialize()
{
  // Initialize the pegging metadata
  PeggingDemandIterator::metadata = MetaCategory::registerCategory<PeggingDemandIterator>("demandpegging", "demandpeggings");
  registerFields<PeggingDemandIterator>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python type
  PythonType& x = PythonExtension<PeggingDemandIterator>::getPythonType();
  x.setName("peggingDemandIterator");
  x.setDoc("frePPLe iterator for demand pegging");
  x.supportgetattro();
  x.supportiter();
  const_cast<MetaCategory*>(PeggingDemandIterator::metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


PeggingIterator::PeggingIterator(const PeggingIterator& c)
: downstream(c.downstream), firstIteration(c.firstIteration), first(c.first), second_pass(c.second_pass)
{
  initType(metadata);
  for (statestack::const_iterator i = c.states.begin(); i != c.states.end(); ++i)
    states.push_back( state(i->opplan, i->quantity, i->offset, i->level) );
  for (deque<state>::const_iterator i = c.states_sorted.begin(); i != c.states_sorted.end(); ++i)
    states_sorted.push_back(state(i->opplan, i->quantity, i->offset, i->level));
}


PeggingIterator::PeggingIterator(const Demand* d)
  : downstream(false), firstIteration(true), first(false), second_pass(false)
{
  initType(metadata);
  const Demand::OperationPlanList &deli = d->getDelivery();
  for (Demand::OperationPlanList::const_iterator opplaniter = deli.begin();
      opplaniter != deli.end(); ++opplaniter)
  {
    OperationPlan *t = (*opplaniter)->getTopOwner();
    updateStack(t, t->getQuantity(), 0.0, 0);
  }

  // Bring all pegging information to a second stack.
  // Only in this way can we avoid that the same operationplan is returned
  // multiple times
  while (operator bool())
  {
    /** Check if already found in the vector. */
    bool found = false;
    state& curtop = states.back();
    for (deque<state>::iterator it = states_sorted.begin(); it != states_sorted.end() && !found; ++it)
      if (it->opplan == curtop.opplan)
      {
        // Update existing element in sorted stack
        it->quantity += curtop.quantity;
        if (it->level > curtop.level)
          it->level = curtop.level;
        found = true;
      }
    if (!found)
      // New element in sorted stack
      states_sorted.push_back( state(curtop.opplan, curtop.quantity, curtop.offset, curtop.level) );

    if (downstream)
      ++*this;
    else
      --*this;
  }

  // The normal iteration will use the sorted results
  second_pass = true;
}


PeggingIterator::PeggingIterator(const OperationPlan* opplan, bool b)
  : downstream(b), firstIteration(true), first(false), second_pass(false)
{
  initType(metadata);
  if (!opplan) return;
  if (opplan->getTopOwner()->getOperation()->getType() == *OperationSplit::metadata)
    updateStack(
      opplan,
      opplan->getQuantity(),
      0.0,
      0
      );
  else
    updateStack(
      opplan->getTopOwner(),
      opplan->getTopOwner()->getQuantity(),
      0.0,
      0
      );
}


PeggingIterator::PeggingIterator(FlowPlan* fp, bool b)
  : downstream(b), firstIteration(true), first(false), second_pass(false)
{
  initType(metadata);
  if (!fp) return;
  updateStack(
    fp->getOperationPlan()->getTopOwner(),
    fp->getOperationPlan()->getQuantity(),
    0.0,
    0
    );
}


PeggingIterator::PeggingIterator(LoadPlan* lp, bool b)
  : downstream(b), firstIteration(true), first(false), second_pass(false)
{
  initType(metadata);
  if (!lp) return;
  updateStack(
    lp->getOperationPlan()->getTopOwner(),
    lp->getOperationPlan()->getQuantity(),
    0.0,
    0
    );
}


PeggingIterator& PeggingIterator::operator--()
{
  // Second pass
  if (second_pass)
  {
    states_sorted.pop_front();
    return *this;
  }

  // Validate
  if (states.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (downstream)
    throw LogicException("Decrementing a downstream iterator");

  // Mark the top entry in the stack as invalid, so it can be reused.
  first = true;

  // Find other operationplans to add to the stack
  state t = states.back(); // Copy the top element
  followPegging(t.opplan, t.quantity, t.offset, t.level);

  // Pop invalid top entry from the stack.
  // This will happen if we didn't find an operationplan to replace the
  // top entry.
  if (first) states.pop_back();

  return *this;
}


PeggingIterator& PeggingIterator::operator++()
{
  // Second pass
  if (second_pass)
  {
    states_sorted.pop_front();
    return *this;
  }

  // Validate
  if (states.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (!downstream)
    throw LogicException("Incrementing an upstream iterator");

  // Mark the top entry in the stack as invalid, so it can be reused.
  first = true;

  // Find other operationplans to add to the stack
  state t = states.back(); // Copy the top element
  followPegging(t.opplan, t.quantity, t.offset, t.level);

  // Pop invalid top entry from the stack.
  // This will happen if we didn't find an operationplan to replace the
  // top entry.
  if (first) states.pop_back();

  return *this;
}


void PeggingIterator::followPegging
(const OperationPlan* op, double qty, double offset, short lvl)
{
  // Zero quantity operationplans don't have further pegging
  if (!op->getQuantity()) return;

  // For each flowplan ask the buffer to find the pegged operationplans.
  if (downstream)
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      if (i->getQuantity() > ROUNDING_ERROR) // Producing flowplan
        i->getFlow()->getBuffer()->followPegging(*this, &*i, qty, offset, lvl+1);
    }
  else
    for (OperationPlan::FlowPlanIterator i = op->beginFlowPlans();
        i != op->endFlowPlans(); ++i)
    {
      if (i->getQuantity() < -ROUNDING_ERROR) // Consuming flowplan
        i->getFlow()->getBuffer()->followPegging(*this, &*i, qty, offset, lvl+1);
    }

  // Push child operationplans on the stack.
  // The pegged quantity is equal to the ratio of the quantities of the
  // parent and child operationplan.
  for (OperationPlan::iterator j(op); j != OperationPlan::end(); ++j)
    updateStack(
      &*j,
      qty * j->getQuantity() / op->getQuantity(),
      offset * j->getQuantity() / op->getQuantity(),
      lvl+1
      );
}


PeggingIterator* PeggingIterator::next()
{
  if (firstIteration)
    firstIteration = false;
  else if (downstream)
    ++*this;
  else
    --*this;
  if (!operator bool())
    return nullptr;
  else
    return this;
}


void PeggingIterator::updateStack
(const OperationPlan* op, double qty, double o, short lvl)
{
  // Avoid very small pegging quantities
  if (qty < ROUNDING_ERROR) return;

  if (first)
  {
    // Update the current top element of the stack
    state& t = states.back();
    t.opplan = op;
    t.quantity = qty;
    t.offset = o;
    t.level = lvl;
    first = false;
  }
  else
    // We need to create a new element on the stack
    states.push_back( state(op, qty, o, lvl) );
}


PeggingDemandIterator::PeggingDemandIterator(const PeggingDemandIterator& c)
{
  initType(metadata);
  dmds.insert(c.dmds.begin(), c.dmds.end());
}


PeggingDemandIterator::PeggingDemandIterator(const OperationPlan* opplan)
{
  initType(metadata);
  // Walk over all downstream operationplans till demands are found
  for (PeggingIterator p(opplan); p; ++p)
  {
    const OperationPlan* m = p.getOperationPlan();
    if (!m)
      continue;
    Demand* dmd = m->getTopOwner()->getDemand();
    if (!dmd || p.getQuantity() < ROUNDING_ERROR)
      continue;
    map<Demand*, double>::iterator i = dmds.lower_bound(dmd);
    if (i != dmds.end() && i->first == dmd)
      // Pegging to the same demand multiple times
      i->second += p.getQuantity();
    else
      // Adding demand
      dmds.insert(i, make_pair(dmd, p.getQuantity()));
  }
}


PeggingDemandIterator* PeggingDemandIterator::next()
{
  if (first)
  {
    iter = dmds.begin();
    first = false;
  }
  else
    ++iter;
  if (iter == dmds.end())
    return nullptr;
  return this;
}

} // End namespace
