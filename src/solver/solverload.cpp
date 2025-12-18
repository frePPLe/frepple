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

#include "frepple/solver.h"

namespace frepple {

bool sortLoad(const Load* lhs, const Load* rhs) {
  auto l = lhs->getPriority();
  auto r = rhs->getPriority();
  if (!l) l = INT_MAX;
  if (!r) r = INT_MAX;
  if (l == r)
    return lhs->getResource()->getEfficiency() <
           rhs->getResource()->getEfficiency();
  else
    return l < r;
}

bool sortResource(const Resource* lhs, const Resource* rhs) {
  if (lhs->getEfficiency() == rhs->getEfficiency())
    return lhs->getName() < rhs->getName();
  else
    return lhs->getEfficiency() < rhs->getEfficiency();
}

void SolverCreate::chooseResource(
    const Load* l, void* v)  // @todo handle unconstrained plan!!!!
{
  auto data = static_cast<SolverData*>(v);
  auto lplan = data->state->q_loadplan;
  if ((l->getResource()->getTool() || l->getResource()->getToolPerPiece()) &&
      lplan->getOperationPlan()->getOwner() &&
      lplan->getResource()->getOwner() &&
      lplan->getOperationPlan()
          ->getOwner()
          ->getOperation()
          ->hasType<OperationRouting>()) {
    // Scan for other steps that use the same tool and same skill
    auto routingopplan = lplan->getOperationPlan()->getOwner();
    auto subopplans = routingopplan->getSubOperationPlans();
    while (auto subopplan = subopplans.next()) {
      if (subopplan == lplan->getOperationPlan()) continue;
      auto subldplniter = subopplan->getLoadPlans();
      while (auto subldpln = subldplniter.next()) {
        if (subldpln->getLoad()->getResource() == l->getResource() &&
            subldpln->getLoad()->getSkill() == l->getSkill()) {
          // CASE 0: forced to use the same tool as other steps in this routing
          // Switch to this resource and call the resource solver
          auto originalend = lplan->getOperationPlan()->getEnd();
          lplan->setResource(subldpln->getResource(), false, false);
          lplan->getOperationPlan()->setEnd(originalend);
          data->state->q_qty = lplan->getQuantity();
          data->state->q_date = lplan->getDate();
          lplan->getResource()->solve(*this, v);
          return;
        }
      }
    }
  }

  if ((!l->getSkill() && !l->getResource()->isGroup()) ||
      lplan->getConfirmed() ||
      lplan->getOperationPlan() == data->state->keepAssignments) {
    // CASE 1: No skill involved, no aggregate resource and forced to keep
    // the current resource assignments
    lplan->getResource()->solve(*this, v);
    return;
  }

  // CASE 2: Skill involved, or aggregate resource
  short loglevel = getLogLevel();

  // Control the planning mode
  bool originalPlanningMode = data->constrainedPlanning;
  data->constrainedPlanning = true;

  // Don't keep track of the constraints right now
  bool originalLogConstraints = data->logConstraints;
  data->logConstraints = false;

  // Initialize
  Date min_next_date(Date::infiniteFuture);
  Date original_q_date = data->state->q_date;
  Resource* bestAlternateSelection = nullptr;
  OperationPlanState bestAlternateState, firstAlternateState;
  Resource* firstAlternate = nullptr;
  bool qualified_resource_exists = false;
  double bestAlternateValue = DBL_MAX;
  double bestAlternateQuantity = DBL_MIN;
  double beforeCost = data->state->a_cost;
  double beforePenalty = data->state->a_penalty;
  OperationPlanState originalOpplan(lplan->getOperationPlan());
  double originalLoadplanQuantity = lplan->getQuantity();
  setLogLevel(0);  // Silence during this loop

  // Create flow and loadplans
  if (lplan->getOperationPlan()->beginLoadPlans() ==
      lplan->getOperationPlan()->endLoadPlans())
    lplan->getOperationPlan()->createFlowLoads();

  // Build a list of candidate resources
  vector<Resource*> res_stack;
  if (l->getResource()->isGroup()) {
    for (auto c1 = l->getResource()->getMembers(); c1 != Resource::end();
         ++c1) {
      if (c1->isGroup()) {
        for (auto c2 = c1->getMembers(); c2 != Resource::end(); ++c2) {
          if (c2->isGroup()) {
            for (auto c3 = c2->getMembers(); c3 != Resource::end(); ++c3) {
              if (c3->isGroup()) {
                for (auto c4 = c3->getMembers(); c4 != Resource::end(); ++c4) {
                  if (c4->isGroup()) {
                    for (auto c5 = c4->getMembers(); c5 != Resource::end();
                         ++c5) {
                      if (c5->isGroup())
                        logger << "Warning: Resource "
                                  "hierarchies can only have up to 5 levels"
                               << endl;
                      else
                        res_stack.push_back(&*c5);
                    }
                  } else
                    res_stack.push_back(&*c4);
                }
              } else
                res_stack.push_back(&*c3);
            }
          } else
            res_stack.push_back(&*c2);
        }
      } else
        res_stack.push_back(&*c1);
    }
    // Sort the list by efficiciency and name
    sort(res_stack.begin(), res_stack.end(), sortResource);
  } else
    res_stack.push_back(l->getResource());

  // Loop over all candidate resources
  while (!res_stack.empty()) {
    // Pick next resource
    Resource* res = res_stack.back();
    res_stack.pop_back();

    // Check if the resource has the right skill
    // TODO if there is a date effective skill, we need to consider it in the
    // reply
    ResourceSkill* rscSkill = nullptr;
    if (l->getSkill() && !res->hasSkill(l->getSkill(), originalOpplan.start,
                                        originalOpplan.end, &rscSkill))
      continue;
    if (rscSkill && !rscSkill->getPriority())
      // Skip 0-priority alternates
      continue;

    // Avoid double allocations to the same resource
    if (lplan->getLoad()->getResource()->isGroup() &&
        Plan::instance().getIndividualPoolResources()) {
      bool exists = false;
      for (auto g = lplan->getOperationPlan()->getLoadPlans();
           g != lplan->getOperationPlan()->endLoadPlans() && &*g != lplan &&
           g->getQuantity() < 0.0;
           ++g) {
        if (g->getResource() == res) {
          exists = true;
          break;
        }
      }
      if (exists) {
        qualified_resource_exists = true;
        continue;
      }
    }

    // Switch to this resource
    data->state->q_loadplan = lplan;  // because q_loadplan can change!
    lplan->getOperationPlan()->setStartEndAndQuantity(
        originalOpplan.start, originalOpplan.end, originalOpplan.quantity);
    lplan->setResource(res, false, false);
    if (lplan->getResource()->getToolPerPiece() &&
        lplan->getLoad()->getQuantity()) {
      double mx = lplan->getMax();
      if (-lplan->getQuantity() > mx + ROUNDING_ERROR) {
        lplan->getOperationPlan()->setQuantity(
            mx / lplan->getLoad()->getQuantity(), true);
        if (!lplan->getOperationPlan()->getQuantity())
          // We have less tools available than the operation size minimum
          continue;
        lplan->getOperationPlan()->setEnd(originalOpplan.end);
        if (data->state->q_qty_min > lplan->getOperationPlan()->getQuantity()) {
          // Assure we don't reject this answer as too small!
          data->state->forceAccept = true;
          data->state->q_qty_min = lplan->getOperationPlan()->getQuantity();
        }
      }
    } else
      lplan->getOperationPlan()->setEnd(originalOpplan.end);
    data->state->q_qty = lplan->getQuantity();
    data->state->q_date = lplan->getDate();
    qualified_resource_exists = true;

    // Remember the first alternate
    if (!firstAlternate) {
      firstAlternate = res;
      firstAlternateState = lplan->getOperationPlan();
    }

    // Plan the resource
    auto topcommand = data->getCommandManager()->setBookmark();
    try {
      res->solve(*this, data);
    } catch (...) {
      setLogLevel(loglevel);
      data->constrainedPlanning = originalPlanningMode;
      data->logConstraints = originalLogConstraints;
      data->getCommandManager()->rollback(topcommand);
      throw;
    }
    data->getCommandManager()->rollback(topcommand);

    // Evaluate the result
    if (data->state->a_qty > ROUNDING_ERROR &&
        lplan->getOperationPlan()->getQuantity() > 0) {
      double deltaCost = data->state->a_cost - beforeCost;
      double deltaPenalty = data->state->a_penalty - beforePenalty;
      // Message
      if (loglevel > 1)
        logger << indentlevel << "  Operation '" << l->getOperation()
               << "' evaluates alternate '" << res << "': cost " << deltaCost
               << ", penalty " << deltaPenalty << endl;
      data->state->a_cost = beforeCost;
      data->state->a_penalty = beforePenalty;
      double val = 0.0;
      switch (l->getSearch()) {
        case SearchMode::PRIORITY:
          val = rscSkill ? rscSkill->getPriority() : 0;
          break;
        case SearchMode::MINCOST:
          val = deltaCost / lplan->getOperationPlan()->getQuantity();
          break;
        case SearchMode::MINPENALTY:
          val = deltaPenalty / lplan->getOperationPlan()->getQuantity();
          break;
        case SearchMode::MINCOSTPENALTY:
          val = (deltaCost + deltaPenalty) /
                lplan->getOperationPlan()->getQuantity();
          break;
        default:
          throw LogicException("Unsupported search mode for alternate load");
      }
      if (val + ROUNDING_ERROR < bestAlternateValue ||
          (fabs(val - bestAlternateValue) < ROUNDING_ERROR &&
           lplan->getOperationPlan()->getQuantity() > bestAlternateQuantity)) {
        // Found a better alternate
        bestAlternateValue = val;
        bestAlternateSelection = res;
        bestAlternateState = OperationPlanState(lplan->getOperationPlan());
        bestAlternateQuantity = lplan->getOperationPlan()->getQuantity();
      }
    } else if (loglevel > 1)
      logger << indentlevel << "  Operation '" << l->getOperation()
             << "' evaluates alternate '" << lplan->getResource()
             << "': not available before " << data->state->a_date << endl;

    // Keep track of best next date
    if (data->state->a_date < min_next_date)
      min_next_date = data->state->a_date;
  }
  setLogLevel(loglevel);

  // Not a single resource has the appropriate skills. You're joking?
  if (!qualified_resource_exists) {
    stringstream s;
    s << "No subresource of '" << l->getResource() << "' has the skill '"
      << l->getSkill() << "' required for operation '" << l->getOperation()
      << "'";
    throw DataException(s.str());
  }

  // Restore the best candidate we found in the loop above
  if (bestAlternateSelection) {
    // Message
    if (loglevel > 1)
      logger << indentlevel << "  Operation '" << l->getOperation()
             << "' chooses alternate '" << bestAlternateSelection << "' "
             << l->getSearch() << endl;

    // Switch back
    data->state->q_loadplan = lplan;  // because q_loadplan can change!
    data->state->a_cost = beforeCost;
    data->state->a_penalty = beforePenalty;

    if (lplan->getResource() != bestAlternateSelection) {
      lplan->getOperationPlan()->clearSetupEvent();
      lplan->getOperationPlan()->setStartEndAndQuantity(
          bestAlternateState.start, bestAlternateState.end,
          bestAlternateState.quantity);
      lplan->setResource(bestAlternateSelection, false, false);
    }
    data->state->q_qty = lplan->getQuantity();
    data->state->q_date = lplan->getDate();
    bestAlternateSelection->solve(*this, data);

    // Restore the planning mode
    data->constrainedPlanning = originalPlanningMode;
    data->logConstraints = originalLogConstraints;
    return;
  }

  if (!originalPlanningMode) {
    // No alternate gave a good result in an unconstrained plan
    if (lplan->getResource() != firstAlternate ||
        !lplan->getOperationPlan()->getQuantity()) {
      lplan->getOperationPlan()->clearSetupEvent();
      lplan->getOperationPlan()->setStartEndAndQuantity(
          firstAlternateState.start, firstAlternateState.end,
          firstAlternateState.quantity);
      lplan->setResource(firstAlternate, false, false);
    }
    data->state->a_qty = lplan->getQuantity();
    data->state->a_date = lplan->getDate();

    // Restore the planning mode
    data->constrainedPlanning = originalPlanningMode;
    data->logConstraints = originalLogConstraints;

    if (loglevel > 1)
      logger << indentlevel << "Alternate load overloads alternate "
             << firstAlternate << endl;
  } else {
    // No alternate gave a good result in a constrained plan
    data->state->a_date = max(min_next_date, original_q_date);
    data->state->a_qty = 0;

    // Maintain the constraint list
    if (originalLogConstraints && data->constraints)
      data->constraints->push(ProblemCapacityOverload::metadata,
                              l->getResource(), originalOpplan.start,
                              originalOpplan.end, 0.0, l->getOperation());

    // Restore the planning mode
    data->constrainedPlanning = originalPlanningMode;
    data->logConstraints = originalLogConstraints;

    if (loglevel > 1)
      logger << indentlevel
             << "  Alternate load doesn't find supply on any alternate: "
             << "not available before " << data->state->a_date << endl;
  }
}

void SolverCreate::solve(const Load* l, void* v) {
  // Note: This method is only called for decrease loadplans and for the leading
  // load of an alternate group. See SolverCreate::checkOperation
  SolverData* data = static_cast<SolverData*>(v);

  if ((!l->hasAlternates() && !l->getAlternate()) ||
      data->state->q_loadplan->getConfirmed()) {
    // CASE I: It is not an alternate load.
    // Delegate the answer immediately to the resource
    chooseResource(l, data);
    return;
  }

  // CASE II: It is an alternate load.
  // We ask each alternate load in order of priority till we find a load
  // that has a non-zero reply.
  short loglevel = getLogLevel();

  // 1) collect a list of alternates
  list<const Load*> thealternates;
  const Load* x = l->hasAlternates() ? l : l->getAlternate();
  SearchMode search = l->getSearch();
  for (auto i = l->getOperation()->getLoads().begin();
       i != l->getOperation()->getLoads().end(); ++i)
    if ((i->getAlternate() == x || &*i == x) && i->getPriority() &&
        i->getEffective().within(data->state->q_loadplan->getDate()))
      thealternates.push_back(&*i);

  // 2) Sort the list
  thealternates.sort(sortLoad);  // @todo cpu-intensive - better is to maintain
                                 // the list in the correct order

  // 3) Control the planning mode
  bool originalPlanningMode = data->constrainedPlanning;
  data->constrainedPlanning = true;

  // Don't keep track of the constraints right now
  bool originalLogConstraints = data->logConstraints;
  data->logConstraints = false;

  // 4) Loop through all alternates or till we find a non-zero
  // reply (priority search)
  Date min_next_date(Date::infiniteFuture);
  LoadPlan* lplan = data->state->q_loadplan;
  double bestAlternateValue = DBL_MAX;
  double bestAlternateQuantity = DBL_MIN;
  const Load* bestAlternateSelection = nullptr;
  double beforeCost = data->state->a_cost;
  double beforePenalty = data->state->a_penalty;
  OperationPlanState originalOpplan(lplan->getOperationPlan());
  double originalLoadplanQuantity = data->state->q_loadplan->getQuantity();
  for (auto i = thealternates.begin(); i != thealternates.end();) {
    const Load* curload = *i;
    data->state->q_loadplan = lplan;  // because q_loadplan can change!

    // 4a) Switch to this load
    if (lplan->getLoad() != curload) lplan->setLoad(const_cast<Load*>(curload));
    lplan->getOperationPlan()->setQuantity(originalOpplan.quantity);
    lplan->getOperationPlan()->setEnd(originalOpplan.end);
    data->state->q_qty = lplan->getQuantity();
    data->state->q_date = lplan->getDate();

    // 4b) Ask the resource
    // TODO XXX Need to insert another loop here! It goes over all resources
    // qualified for the required skill. The qualified resources need to be
    // sorted based on their cost. If the cost is the same we should use a
    // decent tie breaker, eg number of skills or number of loads. The first
    // resource with the qualified skill that is available will be used.
    auto topcommand = data->getCommandManager()->setBookmark();
    if (search == SearchMode::PRIORITY)
      curload->getResource()->solve(*this, data);
    else {
      setLogLevel(0);
      try {
        curload->getResource()->solve(*this, data);
      } catch (...) {
        setLogLevel(loglevel);
        // Restore the planning mode
        data->constrainedPlanning = originalPlanningMode;
        data->logConstraints = originalLogConstraints;
        throw;
      }
      setLogLevel(loglevel);
    }

    // 4c) Evaluate the result
    if (data->state->a_qty > ROUNDING_ERROR &&
        lplan->getOperationPlan()->getQuantity() > 0) {
      if (search == SearchMode::PRIORITY) {
        // Priority search: accept any non-zero reply
        // Restore the planning mode
        data->constrainedPlanning = originalPlanningMode;
        data->logConstraints = originalLogConstraints;
        return;
      } else {
        // Other search modes: evaluate all
        double deltaCost = data->state->a_cost - beforeCost;
        double deltaPenalty = data->state->a_penalty - beforePenalty;
        // Message
        if (loglevel > 1 && search != SearchMode::PRIORITY)
          logger << indentlevel << "Operation '" << l->getOperation()
                 << "' evaluates alternate '" << curload->getResource()
                 << "': cost " << deltaCost << ", penalty " << deltaPenalty
                 << endl;
        if (deltaCost < ROUNDING_ERROR && deltaPenalty < ROUNDING_ERROR) {
          // Zero cost and zero penalty on this alternate. It won't get any
          // better than this, so we accept this alternate.
          if (loglevel > 1)
            logger << indentlevel << "Operation '" << l->getOperation()
                   << "' chooses alternate '" << curload->getResource() << "' "
                   << search << endl;
          // Restore the planning mode
          data->constrainedPlanning = originalPlanningMode;
          data->logConstraints = originalLogConstraints;
          return;
        }
        data->state->a_cost = beforeCost;
        data->state->a_penalty = beforePenalty;
        double val = 0.0;
        switch (search) {
          case SearchMode::MINCOST:
            val = deltaCost / lplan->getOperationPlan()->getQuantity();
            break;
          case SearchMode::MINPENALTY:
            val = deltaPenalty / lplan->getOperationPlan()->getQuantity();
            break;
          case SearchMode::MINCOSTPENALTY:
            val = (deltaCost + deltaPenalty) /
                  lplan->getOperationPlan()->getQuantity();
            break;
          default:
            throw LogicException("Unsupported search mode for alternate load");
        }
        if (val + ROUNDING_ERROR < bestAlternateValue ||
            (fabs(val - bestAlternateValue) < ROUNDING_ERROR &&
             lplan->getOperationPlan()->getQuantity() >
                 bestAlternateQuantity)) {
          // Found a better alternate
          bestAlternateValue = val;
          bestAlternateSelection = curload;
          bestAlternateQuantity = lplan->getOperationPlan()->getQuantity();
        }
      }
    } else if (loglevel > 1 && search != SearchMode::PRIORITY)
      logger << indentlevel << "Operation '" << l->getOperation()
             << "' evaluates alternate '" << curload->getResource()
             << "': not available before " << data->state->a_date << endl;

    // 4d) Undo the plan on the alternate
    data->getCommandManager()->rollback(topcommand);

    // 4e) Prepare for the next alternate
    if (data->state->a_date < min_next_date)
      min_next_date = data->state->a_date;
    if (++i != thealternates.end() && loglevel > 1 &&
        search == SearchMode::PRIORITY)
      logger << indentlevel << "  Alternate load switches from '"
             << curload->getResource() << "' to '" << (*i)->getResource() << "'"
             << endl;
  }

  // 5) Unconstrained plan: plan on the first alternate
  if (!originalPlanningMode &&
      !(search != SearchMode::PRIORITY && bestAlternateSelection)) {
    // Switch to unconstrained planning
    data->constrainedPlanning = false;
    bestAlternateSelection = *(thealternates.begin());
  }

  // 6) Finally replan on the best alternate
  if (!originalPlanningMode ||
      (search != SearchMode::PRIORITY && bestAlternateSelection)) {
    // Message
    if (loglevel > 1)
      logger << indentlevel << "  Operation '" << l->getOperation()
             << "' chooses alternate '" << bestAlternateSelection->getResource()
             << "' " << search << endl;

    // Switch back
    data->state->q_loadplan = lplan;  // because q_loadplan can change!
    data->state->a_cost = beforeCost;
    data->state->a_penalty = beforePenalty;
    if (lplan->getLoad() != bestAlternateSelection)
      lplan->setLoad(const_cast<Load*>(bestAlternateSelection));
    lplan->getOperationPlan()->restore(originalOpplan);
    // TODO XXX need to restore also the selected resource with the right skill!
    data->state->q_qty = lplan->getQuantity();
    data->state->q_date = lplan->getDate();
    bestAlternateSelection->getResource()->solve(*this, data);

    // Restore the planning mode
    data->constrainedPlanning = originalPlanningMode;
    data->logConstraints = originalLogConstraints;
    return;
  }

  // 7) No alternate gave a good result
  data->state->a_date = min_next_date;
  data->state->a_qty = 0;

  // Restore the planning mode
  data->constrainedPlanning = originalPlanningMode;

  // Maintain the constraint list
  if (originalLogConstraints && data->constraints) {
    const Load* primary = *(thealternates.begin());
    data->constraints->push(ProblemCapacityOverload::metadata,
                            primary->getResource(), originalOpplan.start,
                            originalOpplan.end, 0.0, primary->getOperation());
  }
  data->logConstraints = originalLogConstraints;

  if (loglevel > 1)
    logger << indentlevel
           << "  Alternate load doesn't find supply on any alternate: "
           << "not available before " << data->state->a_date << endl;
}

}  // namespace frepple
