/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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


void Resource::updateProblems()
{
  // Delete existing problems for this resource
  Problem::clearProblems(*this);

  // Hidden entities don't have problems
  if (getHidden()) return;

  // Loop through the loadplans
  Date excessProblemStart;
  Date shortageProblemStart;
  bool excessProblem = false;
  bool shortageProblem = false;
  float curMax(0.0);
  float shortageQty(0.0);
  float curMin(0.0);
  float excessQty(0.0);
  for (loadplanlist::const_iterator f=loadplans.begin(); f!=loadplans.end();++f)
  {
    // Process changes in the maximum or minimum targets
    if (f->getType() == 4)
      curMax = f->getMax();
    else if (f->getType() == 3)
      curMin = f->getMin();

    // Check against minimum target
    float delta = static_cast<float>(f->getOnhand() - curMin);
    if (delta < -ROUNDING_ERROR)
    {
      if (!shortageProblem)
      {
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
          new ProblemCapacityUnderload(this, DateRange(shortageProblemStart, 
          	f->getDate()), -shortageQty);
        shortageProblem = false;
      }
    }

    // Note that theoretically we can have a minimum and a maximum problem for
    // the same moment in time.

    // Check against maximum target
    delta = static_cast<float>(f->getOnhand() - curMax);
    if (delta > ROUNDING_ERROR)
    {
      if (!excessProblem)
      {
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
        // New problem now ends
        if (f->getDate() != excessProblemStart)
          new ProblemCapacityOverload(this, DateRange(excessProblemStart, 
          	f->getDate()), excessQty);
        excessProblem = false;
      }
    }

  }  // End of for-loop through the flowplans

  // The excess lasts till the end of the horizon...
  if (excessProblem)
    new ProblemCapacityOverload(this, DateRange(excessProblemStart, 
    	Date::infiniteFuture), excessQty);

  // The shortage lasts till the end of the horizon...
  if (shortageProblem)
    new ProblemCapacityUnderload(this, DateRange(shortageProblemStart, 
    	Date::infiniteFuture), -shortageQty);
}


string ProblemCapacityUnderload::getDescription() const
{
  ostringstream ch;
  ch << "Resource '" << getResource() << "' has excess capacity of " << qty;
  return ch.str();
}


string ProblemCapacityOverload::getDescription() const
{
  ostringstream ch;
  ch << "Resource '" << getResource() << "' has capacity shortage of " << qty;
  return ch.str();
}

}
