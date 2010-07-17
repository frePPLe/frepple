/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2010 by Johan De Taeye                               *
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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,*
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"
namespace frepple
{


DECLARE_EXPORT void Operation::updateProblems()
{
  // Find all operationplans, and delegate the problem detection to them
  if (getDetectProblems())
    for (OperationPlan *o = first_opplan; o; o = o->next) o->updateProblems();
}


//
// BEFORECURRENT, BEFOREFENCE, PRECEDENCE
//


void OperationPlan::updateProblems()
{
  // A flag for each problem type that may need to be created
  bool needsBeforeCurrent(false);
  bool needsBeforeFence(false);
  bool needsPrecedence(false);

  // The following categories of operation plans can't have problems:
  //  - locked opplans
  //  - opplans of hidden operations
  if (!getLocked() && getOperation()->getDetectProblems())
  {
    if (!getOwner() || getOperation() == OperationSetup::setupoperation) 
    {
      // Avoid duplicating problems on child and owner operationplans
      // Check if a BeforeCurrent problem is required.
      if (dates.getStart() < Plan::instance().getCurrent())
        needsBeforeCurrent = true;

      // Check if a BeforeFence problem is required.
      // Note that we either detect of beforeCurrent or a beforeFence problem,
      // never both simultaneously.
      else if
      (dates.getStart() < Plan::instance().getCurrent() + oper->getFence())
        needsBeforeFence = true;
    }
    if (nextsubopplan && getDates().getEnd() > nextsubopplan->getDates().getStart())
      needsPrecedence = true;
  }

  // Loop through the existing problems
  for (Problem::const_iterator j = Problem::begin(this, false);
      j!=Problem::end();)
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
    else if (typeid(curprob) == typeid(ProblemPrecedence))
    {
      if (needsPrecedence) needsPrecedence = false;
      else delete &curprob;
    }
  }

  // Create the problems that are required but aren't existing yet.
  // There is a little trick involved here... Normally problems are owned
  // by objects of the Plannable class. OperationPlan isn't a subclass of
  // Plannable, so we need a dirty cast.
  if (needsBeforeCurrent) new ProblemBeforeCurrent(this);
  if (needsBeforeFence) new ProblemBeforeFence(this);
  if (needsPrecedence) new ProblemPrecedence(this);
}

}
