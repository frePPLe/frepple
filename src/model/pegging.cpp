/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple {

const MetaCategory* PeggingIterator::metadata;
const MetaCategory* PeggingDemandIterator::metadata;

thread_local MemoryPool<PeggingIterator::state> PeggingIterator::peggingpool;

int PeggingIterator::initialize() {
  // Initialize the pegging metadata
  PeggingIterator::metadata =
      MetaCategory::registerCategory<PeggingIterator>("pegging", "peggings");
  registerFields<PeggingIterator>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python type
  auto& x = PythonExtension<PeggingIterator>::getPythonType();
  x.setName("peggingIterator");
  x.setDoc("frePPLe iterator for operationplan pegging");
  x.supportgetattro();
  x.supportiter();
  PeggingIterator::metadata->setPythonClass(x);
  return x.typeReady();
}

int PeggingDemandIterator::initialize() {
  // Initialize the pegging metadata
  PeggingDemandIterator::metadata =
      MetaCategory::registerCategory<PeggingDemandIterator>("demandpegging",
                                                            "demandpeggings");
  registerFields<PeggingDemandIterator>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python type
  auto& x = PythonExtension<PeggingDemandIterator>::getPythonType();
  x.setName("peggingDemandIterator");
  x.setDoc("frePPLe iterator for demand pegging");
  x.supportgetattro();
  x.supportiter();
  PeggingDemandIterator::metadata->setPythonClass(x);
  return x.typeReady();
}

PeggingIterator& PeggingIterator::operator=(const PeggingIterator& c) {
  downstream = c.downstream;
  firstIteration = c.firstIteration;
  first = c.first;
  second_pass = c.second_pass;
  maxlevel = c.maxlevel;
  states = c.states;
  states_sorted = c.states_sorted;
  return *this;
}

PeggingIterator::PeggingIterator(const Demand* d, short maxLvl)
    : states(PeggingIterator::peggingpool),
      states_sorted(PeggingIterator::peggingpool),
      downstream(false),
      firstIteration(true),
      first(false),
      second_pass(false),
      maxlevel(maxLvl) {
  initType(metadata);
  const Demand::OperationPlanList& deli = d->getDelivery();
  for (auto opplaniter = deli.begin(); opplaniter != deli.end(); ++opplaniter) {
    OperationPlan* t = (*opplaniter)->getTopOwner();
    updateStack(t, t->getQuantity(), 0.0, 0, 0L);
  }

  // Bring all pegging information to a second stack.
  // Only in this way can we avoid that the same operationplan is returned
  // multiple times
  while (operator bool()) {
    /* Check if already found in the vector. */
    bool found = false;
    state& curtop = states.back();
    for (auto it = states_sorted.begin(); it != states_sorted.end() && !found;
         ++it)
      if (it->opplan == curtop.opplan) {
        // Update existing element in sorted stack
        it->quantity += curtop.quantity;
        if (it->level > curtop.level) it->level = curtop.level;
        found = true;
      }
    if (!found)
      // New element in sorted stack
      states_sorted.insert(curtop.opplan, curtop.quantity, curtop.offset,
                           curtop.level, curtop.gap);

    if (downstream)
      ++*this;
    else
      --*this;
  }

  // The normal iteration will use the sorted results
  second_pass = true;
}

PeggingIterator::PeggingIterator(const OperationPlan* opplan, bool b,
                                 short maxlevel)
    : states(PeggingIterator::peggingpool),
      states_sorted(PeggingIterator::peggingpool),
      downstream(b),
      firstIteration(true),
      first(false),
      second_pass(false),
      maxlevel(maxlevel) {
  initType(metadata);
  if (!opplan) return;
  if (opplan->getTopOwner()->getOperation()->hasType<OperationSplit>() ||
      maxlevel > 0)
    updateStack(opplan, opplan->getQuantity(), 0.0, 0, 0L);
  else
    updateStack(opplan->getTopOwner(), opplan->getTopOwner()->getQuantity(),
                0.0, 0, 0L);
}

PeggingIterator::PeggingIterator(const FlowPlan* fp, bool b)
    : states(PeggingIterator::peggingpool),
      states_sorted(PeggingIterator::peggingpool),
      downstream(b),
      firstIteration(true),
      first(false),
      second_pass(false),
      maxlevel(-1) {
  initType(metadata);
  if (!fp) return;
  if (maxlevel > 0)
    updateStack(fp->getOperationPlan(), fp->getOperationPlan()->getQuantity(),
                0.0, 0, 0L);
  else
    updateStack(fp->getOperationPlan()->getTopOwner(),
                fp->getOperationPlan()->getQuantity(), 0.0, 0, 0L);
}

PeggingIterator::PeggingIterator(LoadPlan* lp, bool b)
    : states(PeggingIterator::peggingpool),
      states_sorted(PeggingIterator::peggingpool),
      downstream(b),
      firstIteration(true),
      first(false),
      second_pass(false),
      maxlevel(-1) {
  initType(metadata);
  if (!lp) return;
  if (maxlevel > 0)
    updateStack(lp->getOperationPlan(), lp->getOperationPlan()->getQuantity(),
                0.0, 0, 0L);
  else
    updateStack(lp->getOperationPlan()->getTopOwner(),
                lp->getOperationPlan()->getQuantity(), 0.0, 0, 0L);
}

PeggingIterator& PeggingIterator::operator--() {
  // Second pass
  if (second_pass) {
    states_sorted.pop_front();
    return *this;
  }

  // Validate
  if (states.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (downstream) throw LogicException("Decrementing a downstream iterator");

  // Mark the top entry in the stack as invalid, so it can be reused.
  first = true;

  // Find other operationplans to add to the stack
  state& t = states.back();  // Copy the top element
  followPegging(t.opplan, t.quantity, t.offset, t.level);

  // Pop invalid top entry from the stack.
  // This will happen if we didn't find an operationplan to replace the
  // top entry.
  if (first) states.pop_back();

  return *this;
}

PeggingIterator& PeggingIterator::operator++() {
  // Second pass
  if (second_pass) {
    states_sorted.pop_front();
    return *this;
  }

  // Validate
  if (states.empty())
    throw LogicException("Incrementing the iterator beyond it's end");
  if (!downstream) throw LogicException("Incrementing an upstream iterator");

  // Mark the top entry in the stack as invalid, so it can be reused.
  first = true;

  // Find other operationplans to add to the stack
  state& t = states.back();  // Copy the top element
  followPegging(t.opplan, t.quantity, t.offset, t.level);

  // Pop invalid top entry from the stack.
  // This will happen if we didn't find an operationplan to replace the
  // top entry.
  if (first) states.pop_back();

  return *this;
}

void PeggingIterator::followPegging(const OperationPlan* op, double qty,
                                    double offset, short lvl) {
  // Zero quantity operationplans don't have further pegging
  if (!op->getQuantity()) return;

  // Did we reach the maximum depth we want to visit
  // If the operation is hidden, we allow one more level
  if (maxlevel != -1 && lvl > maxlevel && !op->getOperation()->getHidden())
    return;

  // For each flowplan ask the buffer to find the pegged operationplans.
  if (downstream)
    for (auto i = op->beginFlowPlans(); i != op->endFlowPlans(); ++i) {
      if (i->getQuantity() > ROUNDING_ERROR)  // Producing flowplan
        i->getFlow()->getBuffer()->followPegging(*this, &*i, qty, offset,
                                                 lvl + 1);
    }
  else
    for (auto i = op->beginFlowPlans(); i != op->endFlowPlans(); ++i) {
      if (i->getQuantity() < -ROUNDING_ERROR)  // Consuming flowplan
        i->getFlow()->getBuffer()->followPegging(*this, &*i, qty, offset,
                                                 lvl + 1);
    }

  // Push child operationplans on the stack.
  // The pegged quantity is equal to the ratio of the quantities of the
  // parent and child operationplan.

  if (maxlevel > 0) {
    if (lvl <= maxlevel - 1 || op->getOperation()->getHidden()) {
      // DOWNSTREAM
      if (downstream) {
        // In downstream, a routing operation will send its first step
        if (op->getOperation()->hasType<OperationRouting>()) {
          for (OperationPlan::iterator j(op); j != OperationPlan::end(); ++j) {
            updateStack(&*j, qty * j->getQuantity() / op->getQuantity(),
                        offset * j->getQuantity() / op->getQuantity(), lvl + 1,
                        0L);
            break;
          }
        }

        // In downstream, a routing suboperation will send the next suboperation
        if (op->getOwner() &&
            op->getOwner()->getOperation()->hasType<OperationRouting>() &&
            op->getNextSubOpplan()) {
          updateStack(
              op->getNextSubOpplan(),
              qty * op->getNextSubOpplan()->getQuantity() / op->getQuantity(),
              offset * op->getNextSubOpplan()->getQuantity() /
                  op->getQuantity(),
              lvl + 1, 0L);
        }
      } else {
        // UPSTREAM
        // In upstream, a routing operation will send its last step
        if (op->getOperation()->hasType<OperationRouting>()) {
          OperationPlan* opplan_last;
          for (OperationPlan::iterator j(op); j != OperationPlan::end(); ++j) {
            opplan_last = &*j;
          }
          if (opplan_last)
            updateStack(opplan_last,
                        qty * opplan_last->getQuantity() / op->getQuantity(),
                        offset * opplan_last->getQuantity() / op->getQuantity(),
                        lvl + 1, 0L);
        }

        // In upstream, a routing suboperation will send the previous
        // suboperation
        if (op->getOwner() &&
            op->getOwner()->getOperation()->hasType<OperationRouting>() &&
            op->getPrevSubOpplan()) {
          updateStack(
              op->getPrevSubOpplan(),
              qty * op->getPrevSubOpplan()->getQuantity() / op->getQuantity(),
              offset * op->getPrevSubOpplan()->getQuantity() /
                  op->getQuantity(),
              lvl + 1, 0L);
        }
      }
    }
  } else {
    for (OperationPlan::iterator j(op); j != OperationPlan::end(); ++j) {
      updateStack(&*j, qty * j->getQuantity() / op->getQuantity(),
                  offset * j->getQuantity() / op->getQuantity(), lvl + 1, 0L);
    }
  }

  // Push dependencies on the stack.
  for (auto d : op->getDependencies()) {
    auto o = downstream ? d->getSecond() : d->getFirst();
    auto exists = visited.find(o);
    if (exists != visited.end()) continue;
    visited.insert(o);
    if (downstream && d->getFirst() == op && (maxlevel == -1 || lvl < maxlevel))
      updateStack(d->getSecond(),
                  qty * d->getSecond()->getQuantity() / op->getQuantity(),
                  offset * d->getSecond()->getQuantity() / op->getQuantity(),
                  lvl + 1, 0L);
    else if (!downstream && d->getSecond() == op &&
             (maxlevel == -1 || lvl < maxlevel))
      updateStack(d->getFirst(),
                  qty * d->getFirst()->getQuantity() / op->getQuantity(),
                  offset * d->getFirst()->getQuantity() / op->getQuantity(),
                  lvl + 1, 0L);
  }
}

PeggingIterator* PeggingIterator::next() {
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

void PeggingIterator::updateStack(const OperationPlan* op, double qty, double o,
                                  short lvl, Duration gap) {
  // Avoid very small pegging quantities
  if (qty < ROUNDING_ERROR) return;

  // Check for loops in the pegging
  for (auto e = states.begin(); e != states.end(); ++e) {
    if (e->opplan == op && abs(e->quantity - qty) < ROUNDING_ERROR &&
        abs(e->offset - o) < ROUNDING_ERROR)  // We've been here before...
      return;
  }

  if (first) {
    // Update the current top element of the stack
    state& t = states.back();
    t.opplan = op;
    t.quantity = qty;
    t.offset = o;
    t.level = lvl;
    t.gap = gap;
    first = false;
  } else
    // We need to create a new element on the stack
    states.insert(op, qty, o, lvl, gap);
}

PeggingDemandIterator::PeggingDemandIterator(const OperationPlan* opplan) {
  initType(metadata);

  // a map to track the demands pegged to that opplan
  // for every demand we are also tracking the different delivery orders
  // in another map with the pegged offet and qty from that delivery order
  map<Demand*, map<const OperationPlan*, vector<pair<double, double>>>> mapvar;

  // Walk over all downstream operationplans till demands are found
  for (PeggingIterator p(opplan); p; ++p) {
    const OperationPlan* m = p.getOperationPlan();
    if (!m || (m != m->getTopOwner())) continue;
    Demand* dmd = m->getTopOwner()->getDemand();

    if (!dmd || p.getQuantity() < ROUNDING_ERROR) continue;
    double x = p.getOffset();
    double y = p.getOffset() + p.getQuantity();
    auto elem = mapvar.find(dmd);

    if (elem == mapvar.end()) {
      // 1) This is a new demand
      vector<pair<double, double>> vec{{x, y}};
      map<const OperationPlan*, vector<pair<double, double>>> dlvr_map;
      dlvr_map.insert({m, vec});
      mapvar.insert({dmd, dlvr_map});
    } else {
      // 2) We already saw that demand
      map<const OperationPlan*, vector<pair<double, double>>> dlvr_map =
          elem->second;
      auto elem2 = dlvr_map.find(m);
      // 2.a) We already saw that demand but we never saw that delivery order
      if (elem2 == dlvr_map.end()) {
        vector<pair<double, double>> vec{{x, y}};
        dlvr_map.insert({m, vec});
      } else {
        // 2.b) We already saw that demand and we also saw that delivery order
        elem2->second.emplace_back(make_pair(x, y));
      }
    }
  }
  // iterate over all demands and compute the pegged quantity
  // by excluding overlapping intervals
  for (const auto& it : mapvar) {
    double quantity = 0;
    for (auto& it2 : it.second) {
      quantity +=
          sumOfIntervals(const_cast<vector<pair<double, double>>&>(it2.second));
    }
    dmds.insert({it.first, quantity});
  }
}

PeggingDemandIterator* PeggingDemandIterator::next() {
  if (first) {
    iter = dmds.begin();
    first = false;
  } else
    ++iter;
  if (iter == dmds.end()) return nullptr;
  return this;
}

double PeggingDemandIterator::sumOfIntervals(
    vector<pair<double, double>>& intervals) {
  if (intervals.empty()) return 0;

  // Sort intervals by their starting point
  sort(intervals.begin(), intervals.end());

  double totalSum = 0;
  double currentStart = intervals[0].first;
  double currentEnd = intervals[0].second;

  for (auto& i : intervals) {
    double start = i.first;
    double end = i.second;

    if (start <= currentEnd) {  // Overlapping intervals
      currentEnd = max(currentEnd, end);
    } else {  // Non-overlapping interval
      totalSum += (currentEnd - currentStart);
      currentStart = start;
      currentEnd = end;
    }
  }

  // Add the last merged interval
  totalSum += (currentEnd - currentStart);

  return totalSum;
}

}  // namespace frepple
