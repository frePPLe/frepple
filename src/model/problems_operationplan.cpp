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


void Operation::updateProblems()
{
  // Find all operationplans, and delegate the problem detection to them
  if (getDetectProblems())
    for (OperationPlan *o = first_opplan; o; o = o->next)
      o->updateProblems();
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

  if (!firstsubopplan)
  {
    // Avoid duplicating problems on child and owner operationplans
    // Check if a BeforeCurrent or BeforeFence problem is required.
    // Note that we either detect of beforeCurrent or a beforeFence problem,
    // never both simultaneously.
    if (getConfirmed())
    {
      if (dates.getEnd() < Plan::instance().getCurrent())
        needsBeforeCurrent = true;
    }
    else
    {
      if (dates.getStart() < Plan::instance().getCurrent())
        needsBeforeCurrent = true;
      else if (dates.getStart() < Plan::instance().getCurrent() + oper->getFence() && getProposed())
        needsBeforeFence = true;
    }
  }
  // Note: 1 second grace period for precedence problems to avoid rounding issues
  if (nextsubopplan
    && getEnd() > nextsubopplan->getStart() + Duration(1L)
    && !nextsubopplan->getConfirmed()
    && owner && owner->getOperation()->getType() != *OperationSplit::metadata
    )
    needsPrecedence = true;

  // Loop through the existing problems
  for (Problem::iterator j = Problem::begin(this, false);
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
      if (needsBeforeCurrent)
        needsBeforeCurrent = false;
      else
        delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemBeforeFence))
    {
      if (needsBeforeFence)
        needsBeforeFence = false;
      else
        delete &curprob;
    }
    else if (typeid(curprob) == typeid(ProblemPrecedence))
    {
      if (needsPrecedence)
        needsPrecedence = false;
      else
        delete &curprob;
    }
  }

  // Create the problems that are required but aren't existing yet.
  if (needsBeforeCurrent)
    new ProblemBeforeCurrent(this);
  if (needsBeforeFence)
    new ProblemBeforeFence(this);
  if (needsPrecedence)
    new ProblemPrecedence(this);
}


OperationPlan::ProblemIterator::ProblemIterator(const OperationPlan* opplan)
  : Problem::iterator(opplan->firstProblem)
{
  // Adding related material problems
  for (FlowPlanIterator flpln = opplan->beginFlowPlans(); flpln != opplan->endFlowPlans(); ++flpln)
  {
    for (Problem::iterator prob(flpln->getBuffer()); prob != Problem::end(); ++prob)
      if (prob->getDates().overlap(opplan->getDates()) && !prob->isFeasible())
        relatedproblems.push(&*prob);
  }

  // Adding related capacity problems
  for (LoadPlanIterator ldpln = opplan->beginLoadPlans(); ldpln != opplan->endLoadPlans(); ++ldpln)
  {
    for (Problem::iterator prob(ldpln->getResource()); prob != Problem::end(); ++prob)
      if (prob->getDates().overlap(opplan->getDates()) && !prob->isFeasible())
        relatedproblems.push(&*prob);
  }

  // Update the first problem pointer
  if (!iter && !relatedproblems.empty())
    iter = relatedproblems.top();
}


OperationPlan::ProblemIterator& OperationPlan::ProblemIterator::operator++()
{
  // Incrementing beyond the end
  if (!iter) return *this;

  if (!relatedproblems.empty())
  {
    relatedproblems.pop();
    iter = relatedproblems.top();
    return *this;
  }

  // Move to the next problem
  iter = iter->getNextProblem();
  return *this;
}


bool OperationPlan::updateFeasible()
{
  if (!getOperation()->getDetectProblems())
  {
    // No problems to be flagged on this operation
    setFeasible(true);
    return true;
  }

  // The implementation of this method isn't really cleanly object oriented. It uses
  // logic which only the different resource and buffer implementation classes should be
  // aware.
  if (firstsubopplan)
  {
    // Check feasibility of child operationplans
    for (OperationPlan *i = firstsubopplan; i; i = i->nextsubopplan)
    {
      if (!i->updateFeasible())
      {
        setFeasible(false);
        return false;
      }
    }
  }
  else
  {
    // Before current and before fence problems are only detected on child operationplans
    if (getConfirmed())
    {
      if (dates.getEnd() < Plan::instance().getCurrent())
      {
        // Before current violation
        setFeasible(false);
        return false;
      }
    }
    else
    {
      if (dates.getStart() < Plan::instance().getCurrent())
      {
        // Before current violation
        setFeasible(false);
        return false;
      }
      else if (dates.getStart() < Plan::instance().getCurrent() + oper->getFence() && getProposed())
      {
        // Before fence violation
        setFeasible(false);
        return false;
      }
    }
  }
  if (nextsubopplan
    && getEnd() > nextsubopplan->getStart() + Duration(1L)
    && !nextsubopplan->getConfirmed()
    && owner && owner->getOperation()->getType() != *OperationSplit::metadata
    )
  {
    // Precedence violation
    // Note: 1 second grace period for precedence problems to avoid rounding issues
    setFeasible(false);
    return false;
  }

  // Verify the capacity constraints
  for (auto ldplan = getLoadPlans(); ldplan != endLoadPlans(); ++ldplan)
  {
    if (ldplan->getResource()->getType() == *ResourceDefault::metadata && ldplan->getQuantity() > 0)
    {
      auto curMax = ldplan->getMax();
      for (
        auto cur = ldplan->getResource()->getLoadPlans().begin(&*ldplan);
        cur != ldplan->getResource()->getLoadPlans().end();
        ++cur
        )
      {
        if (cur->getOperationPlan() == this && cur->getQuantity() < 0)
          break;
        if (cur->getEventType() == 4)
          curMax = cur->getMax(false);
        if (
          cur->getEventType() != 5
          && cur->isLastOnDate()
          && cur->getOnhand() > curMax + ROUNDING_ERROR
          )
        {
          // Overload on default resource
          setFeasible(false);
          return false;
        }
      }
    }
    else if (ldplan->getResource()->getType() == *ResourceBuckets::metadata)
    {
      for (
        auto cur = ldplan->getResource()->getLoadPlans().begin(&*ldplan);
        cur != ldplan->getResource()->getLoadPlans().end() && cur->getEventType() != 2;
        ++cur
        )
      {
        if (cur->getOnhand() < -ROUNDING_ERROR)
        {
          // Overloaded capacity on bucketized resource
          setFeasible(false);
          return false;
        }
      }
    }
  }

  // Verify the material constraints
  for (auto flplan = beginFlowPlans(); flplan != endFlowPlans(); ++flplan)
  {
    if (
      !flplan->getFlow()->isConsumer()
      || flplan->getBuffer()->getType() == *BufferInfinite::metadata
      )
      continue;
    auto flplaniter = flplan->getBuffer()->getFlowPlans();
    for (auto cur = flplaniter.begin(&*flplan); cur != flplaniter.end(); ++cur)
    {
      if (cur->getOnhand() < -ROUNDING_ERROR && cur->isLastOnDate())
      {
        // Material shortage
        setFeasible(false);
        return false;
      }
    }
  }

  // After all checks, it turns out to be feasible
  setFeasible(true);
  return true;
}


PyObject* OperationPlan::updateFeasiblePython(PyObject* self, PyObject* args)
{
  return PythonData(static_cast<OperationPlan*>(self)->updateFeasible());
}


}
