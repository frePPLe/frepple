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


void Buffer::updateProblems()
{
  // Delete existing problems for this buffer
  Problem::clearProblems(*this, true, false);

  // Problem detection disabled on this buffer
  if (!getDetectProblems()) return;

  // Loop through the flowplans
  Date excessProblemStart;
  Date shortageProblemStart;
  bool shortageProblem = false;
  bool excessProblem = false;
  double curMax(0.0);
  double shortageQty(0.0);
  double curMin(0.0);
  double excessQty(0.0);
  for (flowplanlist::const_iterator iter = flowplans.begin();
      iter != flowplans.end(); )
  {
    // Process changes in the maximum or minimum targets
    if (iter->getEventType() == 4)
      curMax = iter->getMax();
    else if (iter->getEventType() == 3)
      curMin = iter->getMin();

    // Only consider the last flowplan for a certain date
    const TimeLine<FlowPlan>::Event *f = &*(iter++);
    if (iter!=flowplans.end() && iter->getDate()==f->getDate()) continue;

    // Check against minimum target
    double delta = f->getOnhand() - curMin;
    if (delta < -ROUNDING_ERROR)
    {
      if (!shortageProblem)
      {
        // Start of a problem
        shortageProblemStart = f->getDate();
        shortageQty = delta;
        shortageProblem = true;
      }
      else if (delta < shortageQty)
        // New shortage qty
        shortageQty = delta;
    }
    else
    {
      if (shortageProblem)
      {
        // New problem now ends
        if (f->getDate() != shortageProblemStart)
          new ProblemMaterialShortage
          (this, shortageProblemStart, f->getDate(), -shortageQty);
        shortageProblem = false;
      }
    }

    // Check against maximum target
    delta = f->getOnhand() - (curMin<curMax ? curMax : curMin);
    if (delta > ROUNDING_ERROR)
    {
      if (!excessProblem)
      {
        // New problem starts here
        excessProblemStart = f->getDate();
        excessQty = delta;
        excessProblem = true;
      }
      else if (delta > excessQty)
        excessQty = delta;
    }
    else
    {
      if (excessProblem)
      {
        // New excess qty
        // New problem now ends
        if (f->getDate() != excessProblemStart)
          new ProblemMaterialExcess
          (this, excessProblemStart, f->getDate(), excessQty);
        excessProblem = false;
      }
    }

  }  // End of for-loop through the flowplans

  // The excess lasts till the end of the horizon...
  if (excessProblem)
    new ProblemMaterialExcess
    (this, excessProblemStart, Date::infiniteFuture, excessQty);

  // The shortage lasts till the end of the horizon...
  if (shortageProblem)
    new ProblemMaterialShortage
    (this, shortageProblemStart, Date::infiniteFuture, -shortageQty);
}



string ProblemMaterialExcess::getDescription() const
{
  ostringstream ch;
  ch << "Buffer '" << getBuffer() << "' has material excess of " << qty;
  return ch.str();
}


string ProblemMaterialShortage::getDescription() const
{
  ostringstream ch;
  ch << "Buffer '" << getBuffer() << "' has material shortage of " << qty;
  return ch.str();
}


}
