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

#include "frepple/model.h"

namespace frepple {

void Resource::updateProblems() {
  // Delete existing problems for this resource
  Problem::clearProblems(*this, false, false);
  setChanged(false);

  // Problem detection disabled on this resource
  if (!getDetectProblems() || !getConstrained()) return;

  // Loop through the loadplans
  Date excessProblemStart;
  Date shortageProblemStart;
  bool excessProblem = false;
  double curMax(0.0);
  double excessQty(0.0);
  for (auto iter = loadplans.begin(); iter != loadplans.end();) {
    // Process changes in the maximum or minimum targets
    if (iter->getEventType() == 4)
      curMax = iter->getMax();

    // Only consider the last loadplan for a certain date
    const TimeLine<LoadPlan>::Event* f = &*(iter++);
    if (iter != loadplans.end() && iter->getDate() == f->getDate()) continue;

    // Note that theoretically we can have a minimum and a maximum problem for
    // the same moment in time.

    // Check against maximum target
    auto delta = f->getOnhand() - curMax;
    if (delta > ROUNDING_ERROR) {
      if (!excessProblem) {
        excessProblemStart = f->getDate();
        excessQty = delta;
        excessProblem = true;
      } else if (delta > excessQty)
        excessQty = delta;
    } else {
      if (excessProblem) {
        // New problem now ends
        if (f->getDate() != excessProblemStart)
          new ProblemCapacityOverload(this, excessProblemStart, f->getDate(),
                                      excessQty);
        excessProblem = false;
      }
    }

  }  // End of for-loop through the loadplans

  // The excess lasts till the end of the horizon...
  if (excessProblem)
    new ProblemCapacityOverload(this, excessProblemStart, Date::infiniteFuture,
                                excessQty);
}

void ResourceBuckets::updateProblems() {
  // Delete existing problems for this resource
  Problem::clearProblems(*this, true, false);

  // Problem detection disabled on this resource
  if (!getDetectProblems() || !getConstrained()) return;

  // Loop over all events
  Date startdate = Date::infinitePast;
  double load = 0.0;
  for (auto & loadplan : loadplans) {
    if (loadplan.getEventType() != 2)
      load = loadplan.getOnhand();
    else {
      // Evaluate previous bucket
      if (load < -ROUNDING_ERROR)
        new ProblemCapacityOverload(this, startdate, loadplan.getDate(), -load);
      // Reset evaluation for the new bucket
      startdate = loadplan.getDate();
      load = 0.0;
    }
  }
  // Evaluate the final bucket
  if (load < -ROUNDING_ERROR)
    new ProblemCapacityOverload(this, startdate, Date::infiniteFuture, -load);
}

string ProblemCapacityOverload::getDescription() const {
  ostringstream ch;
  ch << "Resource '" << getResource() << "' has capacity shortage";
  if (qty) ch << " of " << qty;
  return ch.str();
}

}  // namespace frepple
