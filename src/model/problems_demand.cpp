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

void Demand::updateProblems() {
  // The relation between the demand and the related problem classes is such
  // that the demand object is the only active one. The problem objects are
  // fully controlled and managed by the associated demand object.

  // A flag for each problem type that may need to be created
  bool needsNotPlanned(false);
  bool needsEarly(false);
  bool needsLate(false);
  bool needsShort(false);
  bool needsExcess(false);

  // Problem detection disabled on this demand
  if (!getDetectProblems()) return;

  // Closed or canceled demands don't have any problems.
  // Demand groups also don't have problems.
  auto tmp_status = getStatus();
  if (tmp_status != STATUS_CLOSED && tmp_status != STATUS_CANCELED &&
      !hasType<DemandGroup>()) {
    // Check which problems need to be created
    if (deli.empty()) {
      // Check if a new ProblemDemandNotPlanned needs to be created
      if (getQuantity() > ROUNDING_ERROR) needsNotPlanned = true;
    } else {
      // Loop through the deliveries
      for (auto i = deli.begin(); i != deli.end(); ++i) {
        long d(getDue() - (*i)->getEnd());
        if (d < 0L)
          // Check for ProblemLate problem
          needsLate = true;
        else if (d > 0L)
          // Check for ProblemEarly problem
          needsEarly = true;
      }

      // Check for ProblemShort problem
      double plannedqty = getPlannedQuantity();
      if (plannedqty + ROUNDING_ERROR < qty) needsShort = true;

      // Check for ProblemExcess Problem
      if (plannedqty - ROUNDING_ERROR > qty) needsExcess = true;
    }
  }

  // Loop through the existing problems
  for (Problem::iterator j = Problem::begin(this, false);
       j != Problem::end();) {
    // Need to increment now and define a pointer to the problem, since the
    // problem can be deleted soon (which invalidates the iterator).
    Problem& curprob = *j;
    ++j;
    // The if-statement keeps the problem detection code concise and
    // concentrated. However, a drawback of this design is that a new Problem
    // subclass will also require a new Demand subclass. I think such a link
    // is acceptable.
    if (typeid(curprob) == typeid(ProblemEarly)) {
      // if: problem needed and it exists already
      if (needsEarly) needsEarly = false;
      // else: problem not needed but it exists already
      else
        delete &curprob;
    } else if (typeid(curprob) == typeid(ProblemDemandNotPlanned)) {
      if (needsNotPlanned)
        needsNotPlanned = false;
      else
        delete &curprob;
    } else if (typeid(curprob) == typeid(ProblemLate)) {
      if (needsLate)
        needsLate = false;
      else
        delete &curprob;
    } else if (typeid(curprob) == typeid(ProblemShort)) {
      if (needsShort)
        needsShort = false;
      else
        delete &curprob;
    } else if (typeid(curprob) == typeid(ProblemExcess)) {
      if (needsExcess)
        needsExcess = false;
      else
        delete &curprob;
    }
    // Note that there may be other demand exceptions that are not caught in
    // this loop. These are problems defined and managed by subclasses.
  }

  // Create the problems that are required but aren't existing yet.
  if (needsNotPlanned) new ProblemDemandNotPlanned(this);
  if (needsLate) new ProblemLate(this);
  if (needsEarly) new ProblemEarly(this);
  if (needsShort) new ProblemShort(this);
  if (needsExcess) new ProblemExcess(this);
}

string ProblemLate::getDescription() const {
  Demand* dmd = getDemand();
  assert(dmd && !dmd->getDelivery().empty());
  Duration delay;
  double plannedlate = 0;
  for (auto i = dmd->getDelivery().begin(); i != dmd->getDelivery().end();
       ++i) {
    Duration tmp = (*i)->getEnd() - getDemand()->getDue();
    if (tmp > 0L) {
      if (tmp > delay) delay = tmp;
      plannedlate += (*i)->getQuantity();
    }
  }
  ostringstream ch;
  ch << (int)(plannedlate + 0.5) << " units of demand '"
     << getDemand()->getName() << "' planned up to " << fixed << setprecision(1)
     << (delay / 86400.0) << " days after its due date";
  return ch.str();
}

string ProblemEarly::getDescription() const {
  assert(getDemand() && !getDemand()->getDelivery().empty());
  Duration t(getDemand()->getDue() -
             getDemand()->getEarliestDelivery()->getEnd());
  return string("Demand '") + getDemand()->getName() + "' planned " +
         string(t) + " before its due date";
}

}  // namespace frepple
