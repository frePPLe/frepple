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

void Buffer::updateProblems() {
  // Delete existing problems for this buffer
  Problem::clearProblems(*this, false, false);
  setChanged(false);

  // Problem detection disabled on this buffer
  if (!getDetectProblems()) return;

  // Loop through the flowplans
  Date shortageProblemStart;
  bool shortageProblem = false;
  // double curMax(0.0);
  double shortageQty(0.0);
  double curMin(0.0);
  for (flowplanlist::const_iterator iter = flowplans.begin();
       iter != flowplans.end();) {
    // Process changes in the maximum or minimum targets
    if (iter->getEventType() == 3) curMin = iter->getMin();
    // else if (iter->getEventType() == 4)
    //   curMax = iter->getMax();

    // Only consider the last flowplan for a certain date
    const TimeLine<FlowPlan>::Event *f = &*(iter++);
    if (iter != flowplans.end() && iter->getDate() == f->getDate()) continue;

    // Check against minimum target
    double delta = f->getOnhand() - curMin;
    if (delta < -ROUNDING_ERROR) {
      if (!shortageProblem) {
        // Start of a problem
        shortageProblemStart = f->getDate();
        shortageQty = delta;
        shortageProblem = true;
      } else if (delta < shortageQty)
        // New shortage qty
        shortageQty = delta;
    } else {
      if (shortageProblem) {
        // New problem now ends
        if (f->getDate() != shortageProblemStart)
          new ProblemMaterialShortage(this, shortageProblemStart, f->getDate(),
                                      -shortageQty);
        shortageProblem = false;
      }
    }

  }  // End of for-loop through the flowplans

  // The shortage lasts till the end of the horizon...
  if (shortageProblem)
    new ProblemMaterialShortage(this, shortageProblemStart,
                                Date::infiniteFuture, -shortageQty);
}

string ProblemMaterialShortage::getDescription() const {
  ostringstream ch;
  ch << "Buffer '" << getBuffer() << "' has material shortage of " << qty;
  return ch.str();
}

}  // namespace frepple
