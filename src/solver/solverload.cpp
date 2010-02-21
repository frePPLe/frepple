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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/solver.h"

namespace frepple
{


bool sortLoad(const Load* lhs, const Load* rhs)
{
  return lhs->getPriority() < rhs->getPriority();
}


void SolverMRP::solve(const Load* l, void* v)
{
  // Note: This method is only called for decrease loadplans and for the leading
  // load of an alternate group. See SolverMRP::checkOperation
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);
  unsigned int loglevel = data->getSolver()->getLogLevel();

  if (data->state->q_qty >= 0.0)
  {
    // The loadplan is an increase in size, and the resource solver only needs
    // the decreases.
    // Or, it's a zero quantity loadplan. E.g. because it is not effective.
    data->state->a_qty = data->state->q_qty;
    data->state->a_date = data->state->q_date;
    return;
  }

  if (!l->hasAlternates() && !l->getAlternate())
  {
    // CASE I: It is not an alternate load.
    // Delegate the answer to the resource
    l->getResource()->solve(*this,v);
    if (data->state->a_qty == 0.0
      && data->state->q_operationplan->getQuantity() != 0.0)
      // In case of a zero reply, we resize the operationplan to 0 right away.
      // This is required to make sure that the buffer inventory profile also
      // respects this answer.
      data->state->q_operationplan->setQuantity(0.0);
    return;
  }

  // CASE II: It is an alternate load.
  // We ask each alternate load in order of priority till we find a flow
  // that has a non-zero reply.

  // 1) collect a list of alternates
  list<const Load*> thealternates;
  const Load *x = l->hasAlternates() ? l : l->getAlternate();
  SearchMode search = l->getSearch();
  for (Operation::loadlist::const_iterator i = l->getOperation()->getLoads().begin();
    i != l->getOperation()->getLoads().end(); ++i)
    if ((i->getAlternate() == x || &*i == x)
      && i->getEffective().within(data->state->q_loadplan->getDate()))
      thealternates.push_back(&*i);

  // 2) Sort the list
  thealternates.sort(sortLoad);  // @todo cpu-intensive - better is to maintain the list in the correct order

  // 3) Control the planning mode
  bool originalPlanningMode = data->constrainedPlanning;
  data->constrainedPlanning = true;

  // 4) Loop through all alternates or till we find a non-zero 
  // reply (priority search)
  Date min_next_date(Date::infiniteFuture);
  LoadPlan *lplan = data->state->q_loadplan;
  double bestAlternateValue = DBL_MAX;
  double bestAlternateQuantity = DBL_MIN;
  const Load* bestAlternateSelection = NULL;
  double beforeCost = data->state->a_cost;
  double beforePenalty = data->state->a_penalty;
  OperationPlanState originalOpplan(lplan->getOperationPlan());
  for (list<const Load*>::const_iterator i = thealternates.begin();
    i != thealternates.end();)
  {
    const Load *curload = *i;
    data->state->q_loadplan = lplan; // because q_loadplan can change!

    // 4a) Switch to this load
    if (lplan->getLoad() != curload) lplan->setLoad(curload);
    lplan->getOperationPlan()->restore(originalOpplan);
    data->state->q_qty = lplan->getQuantity();
    data->state->q_date = lplan->getDate();

    // 4b) Ask the resource
    Command* topcommand = data->getLastCommand();
    if (search == PRIORITY) 
      curload->getResource()->solve(*this,data);
    else
    {
      data->getSolver()->setLogLevel(0);
      try {curload->getResource()->solve(*this,data);}
      catch (...)
      {
        data->getSolver()->setLogLevel(loglevel);
        // Restore the planning mode
        data->constrainedPlanning = originalPlanningMode;
        throw;
      }
      data->getSolver()->setLogLevel(loglevel);
    }

    // 4c) Evaluate the result
    if (data->state->a_qty > ROUNDING_ERROR 
      && lplan->getOperationPlan()->getQuantity() > 0) 
    {
      if (search == PRIORITY)
      {
        // Priority search: accept any non-zero reply
        // Restore the planning mode
        data->constrainedPlanning = originalPlanningMode;
        return;
      }
      else
      {
        // Other search modes: evaluate all
        double deltaCost = data->state->a_cost - beforeCost;
        double deltaPenalty = data->state->a_penalty - beforePenalty;
        // Message
        if (loglevel>1 && search != PRIORITY)
          logger << indent(l->getOperation()->getLevel()) << "   Operation '" 
            << l->getOperation()->getName() << "' evaluates alternate '"
            << curload->getResource() << "': cost " << deltaCost
            << ", penalty " << deltaPenalty << endl;
        if (deltaCost < ROUNDING_ERROR && deltaPenalty < ROUNDING_ERROR)
        {
          // Zero cost and zero penalty on this alternate. It won't get any better
          // than this, so we accept this alternate.
          if (loglevel)
            logger << indent(l->getOperation()->getLevel()) << "   Operation '" 
              << l->getOperation()->getName() << "' chooses alternate '"
              << curload->getResource() << "' " << search << endl;
          // Restore the planning mode
          data->constrainedPlanning = originalPlanningMode;
          return;
        }
        data->state->a_cost = beforeCost;
        data->state->a_penalty = beforePenalty;
        double val;
        switch (search)
        {
          case MINCOST:
            val = deltaCost / lplan->getOperationPlan()->getQuantity();
            break;
          case MINPENALTY:
            val = deltaPenalty / lplan->getOperationPlan()->getQuantity();
            break;
          case MINCOSTPENALTY:
            val = (deltaCost + deltaPenalty) / lplan->getOperationPlan()->getQuantity();
            break;
          default:
            LogicException("Unsupported search mode for alternate load");
        }    
        if (val + ROUNDING_ERROR < bestAlternateValue 
          || (fabs(val - bestAlternateValue) < ROUNDING_ERROR 
              && lplan->getOperationPlan()->getQuantity() > bestAlternateQuantity))
        {
          // Found a better alternate
          bestAlternateValue = val;
          bestAlternateSelection = curload;
          bestAlternateQuantity = lplan->getOperationPlan()->getQuantity();
        }
      }
    }
    else if (loglevel>1 && search != PRIORITY)
      logger << indent(l->getOperation()->getLevel()) << "   Operation '" 
        << l->getOperation()->getName() << "' evaluates alternate '"
        << curload->getResource() << "': not available before " 
        << data->state->a_date << endl;

    // 4d) Undo the plan on the alternate
    data->undo(topcommand);

    // 4e) Prepare for the next alternate
    if (data->state->a_date < min_next_date)
      min_next_date = data->state->a_date;
    if (++i != thealternates.end() && loglevel>1 && search == PRIORITY)
      logger << indent(curload->getOperation()->getLevel()) << "   Alternate load switches from '"
            << curload->getResource()->getName() << "' to '"
            << (*i)->getResource()->getName() << "'" << endl;
  }

  // 5) Unconstrained plan: plan on the first alternate
  if (!originalPlanningMode && !(search != PRIORITY && bestAlternateSelection))
  {
    // Switch to unconstrained planning 
    data->constrainedPlanning = false;
    bestAlternateSelection = *(thealternates.begin());
  }

  // 6) Finally replan on the best alternate
  if (!originalPlanningMode || (search != PRIORITY && bestAlternateSelection))
  {
    // Message
    if (loglevel)
      logger << indent(l->getOperation()->getLevel()) << "   Operation '" 
        << l->getOperation()->getName() << "' chooses alternate '"
        << bestAlternateSelection->getResource() << "' " << search << endl;

    // Switch back
    data->state->q_loadplan = lplan; // because q_loadplan can change!
    data->state->a_cost = beforeCost;
    data->state->a_penalty = beforePenalty;
    if (lplan->getLoad() != bestAlternateSelection)
      lplan->setLoad(bestAlternateSelection);
    lplan->getOperationPlan()->restore(originalOpplan);
    data->state->q_qty = lplan->getQuantity();
    data->state->q_date = lplan->getDate();
    //xxxif (originalPlanningMode)
      bestAlternateSelection->getResource()->solve(*this,data);

    // Restore the planning mode
    data->constrainedPlanning = originalPlanningMode;
    return;
  }

  // 7) No alternate gave a good result
  data->state->a_date = min_next_date;
  data->state->a_qty = 0;
  // Restore the planning mode
  data->constrainedPlanning = originalPlanningMode;
  if (lplan->getOperationPlan()->getQuantity() != 0.0)
    // In case of a zero reply, we resize the operationplan to 0 right away.
    // This is required to make sure that the buffer inventory profile also
    // respects this answer.
    lplan->getOperationPlan()->setQuantity(0.0);
  if (loglevel>1)
    logger << indent(lplan->getOperationPlan()->getOperation()->getLevel()) <<
      "   Alternate load doesn't find supply on any alternate : "
      << data->state->a_qty << "  " << data->state->a_date << endl;
}


}
