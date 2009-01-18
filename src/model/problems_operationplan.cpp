/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
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


DECLARE_EXPORT void Operation::updateProblems()
{
  // Find all operationplans, and delegate the problem detection to them
  for (OperationPlan *o = first_opplan; o; o = o->next) o->updateProblems();
}


//
// BEFORECURRENT, BEFOREFENCE, PLANNEDEARLY, PLANNEDLATE
//


void OperationPlan::updateProblems()
{
  // A flag for each problem type that may need to be created
  bool needsBeforeCurrent(false);
  bool needsBeforeFence(false);
  bool needsEarly(false);
  bool needsLate(false);

  // The following categories of operation plans can't have problems:
  //  - locked opplans
  //  - opplans having an owner
  //  - opplans of hidden operations
  if (!getOwner() && !getLocked() && getOperation()->getDetectProblems())
  {
    // Check if a BeforeCurrent problem is required.
    if (dates.getStart() < Plan::instance().getCurrent())
      needsBeforeCurrent = true;

    // Check if a BeforeFence problem is required.
    // Note that we either detect of beforeCurrent or a beforeFence problem,
    // never both simultaneously.
    else if
    (dates.getStart() < Plan::instance().getCurrent() + oper->getFence())
      needsBeforeFence = true;

    // Check if a PlannedEarly problem is required
    if (getEpst()
        && getDates().getStart()
           < getEpst() - ProblemPlannedEarly::getAllowedEarly())
      needsEarly = true;

    // Check if a PlannedLate problem is required
    if (getLpst()
        && getDates().getStart()
           > getLpst() + ProblemPlannedLate::getAllowedLate())
      needsLate = true;
  }

  // Loop through the existing problems
  for (Problem::const_iterator j = Problem::begin(this, false);
      j!=Problem::end(); ++j)
  {
    // Need to increment now and define a pointer to the problem, since the
    // problem can be deleted soon (which invalidates the iterator).
    Problem& curprob = *j;
    ++j;
    // The if-statement keeps the problem detection code concise and
    // concentrated. However, a drawback of this design is that a new problem
    // subclass will also require a new demand subclass. I think such a link
    // is acceptable.
    if (typeid(curprob) == typeid(ProblemBeforeCurrent))
    {
      // if: problem needed and it exists already
      if (needsBeforeCurrent) needsBeforeCurrent = false;
      // else: problem not needed but it exists already
      else delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemBeforeFence))
    {
      if (needsBeforeFence) needsBeforeFence = false;
      else delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemPlannedEarly))
    {
      if (needsEarly) needsEarly = false;
      else delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemPlannedLate))
    {
      if (needsLate) needsLate = false;
      else delete &curprob;
    }
  }

  // Create the problems that are required but aren't existing yet.
  // There is a little trick involved here... Normally problems are owned
  // by objects of the Plannable class. OperationPlan isn't a subclass of
  // Plannable, so we need a dirty cast.
  if (needsBeforeCurrent) new ProblemBeforeCurrent(this);
  if (needsBeforeFence) new ProblemBeforeFence(this);
  if (needsEarly) new ProblemPlannedEarly(this);
  if (needsLate) new ProblemPlannedLate(this);
}


DECLARE_EXPORT TimePeriod ProblemPlannedEarly::allowedEarly;
DECLARE_EXPORT TimePeriod ProblemPlannedLate::allowedLate;


void ProblemPlannedEarly::setAllowedEarly(TimePeriod p)
{
  allowedEarly = p;

  // Let all operationplans check for new problems
  // Note that ProblemPlannedEarly problems are subscribing to their
  // operationplan and the update() method is notifying them.
  for (OperationPlan::iterator i = OperationPlan::begin();
      i != OperationPlan::end(); ++i)
    i->getOperation()->setChanged();
}


void ProblemPlannedLate::setAllowedLate(TimePeriod p)
{
  allowedLate = p;

  // Let all operationplans check for new problems
  // Note that ProblemPlannedLate problems are subscribing to their
  // operationplan and the update() method is notifying them.
  for (OperationPlan::iterator i = OperationPlan::begin();
      i != OperationPlan::end(); ++i)
    i->getOperation()->setChanged();
}


//
// PRECEDENCE
//


void OperationPlanRouting::updateProblems()  // @todo test! may well be broken
{
  // Make a list of all existing precedence problems
  list<ProblemPrecedence*> currentproblems;
  for (Problem::const_iterator j = Problem::begin(this, false);
      j!=Problem::end(); ++j)
    if (typeid(*j) == typeid(ProblemPrecedence))
      currentproblems.push_front(static_cast<ProblemPrecedence*>(&*j));

  // Problem detection: Check for new precedence_before problem
  OperationPlan* prev = NULL;
  for (list<OperationPlan*>::const_iterator i = step_opplans.begin();
      i != step_opplans.end(); ++i)
  {
    if (prev && prev->getDates().getEnd() > (*i)->getDates().getStart())
    {
      // We need a precedence problem. It could already exist or we need a
      // new one...
      list<ProblemPrecedence*>::iterator l;
      for (l = currentproblems.begin(); l != currentproblems.end(); ++l)
        if ((*l)->getFirstOperationPlan() == prev)
        {
          // It already exists
          currentproblems.erase(l);
          break;
        }
      if (l == currentproblems.end())
        // It is a new problem
        new ProblemPrecedence (getOperation(), prev, *i);
    }
    prev = *i;
  }

  // Erase old problems that have now become obsolete
  while (!currentproblems.empty())
  {
    delete currentproblems.front();
    currentproblems.pop_front();
  }

  // Continue with the normal problem detection
  OperationPlan::updateProblems();
}

}
