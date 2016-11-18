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


void Demand::updateProblems()
{
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

  // Closed demands don't have any problems
  if (getStatus() != CLOSED)
  {
    // Check which problems need to be created
    if (deli.empty())
    {
      // Check if a new ProblemDemandNotPlanned needs to be created
      if (getQuantity() > 0.0) needsNotPlanned = true;
    }
    else
    {
      // Loop through the deliveries
      for (OperationPlanList::iterator i = deli.begin(); i != deli.end(); ++i)
      {
        // Check for ProblemLate problem
        long d(getDue() - (*i)->getDates().getEnd());
        if (d < 0L) needsLate = true;
        // Check for ProblemEarly problem
        else if (d > 0L) needsEarly = true;
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
      j!=Problem::end(); )
  {
    // Need to increment now and define a pointer to the problem, since the
    // problem can be deleted soon (which invalidates the iterator).
    Problem& curprob = *j;
    ++j;
    // The if-statement keeps the problem detection code concise and
    // concentrated. However, a drawback of this design is that a new Problem
    // subclass will also require a new Demand subclass. I think such a link
    // is acceptable.
    if (typeid(curprob) == typeid(ProblemEarly))
    {
      // if: problem needed and it exists already
      if (needsEarly) needsEarly = false;
      // else: problem not needed but it exists already
      else delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemDemandNotPlanned))
    {
      if (needsNotPlanned) needsNotPlanned = false;
      else delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemLate))
    {
      if (needsLate) needsLate = false;
      else delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemShort))
    {
      if (needsShort) needsShort = false;
      else delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemExcess))
    {
      if (needsExcess) needsExcess = false;
      else delete &curprob;
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


string ProblemLate::getDescription() const
{
  assert(getDemand() && !getDemand()->getDelivery().empty());
  Duration t(getDemand()->getLatestDelivery()->getDates().getEnd()
      - getDemand()->getDue());
  return string("Demand '") + getDemand()->getName() + "' planned "
      + string(t) + " after its due date";
}


string ProblemEarly::getDescription() const
{
  assert(getDemand() && !getDemand()->getDelivery().empty());
  Duration t(getDemand()->getDue()
      - getDemand()->getEarliestDelivery()->getDates().getEnd());
  return string("Demand '") + getDemand()->getName() + "' planned "
      + string(t) + " before its due date";
}

}
