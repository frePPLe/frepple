/***************************************************************************
 *                                                                         *
 * Copyright (C) 2026 by frePPLe bv                                        *
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
#include "frepple/solver.h"

namespace frepple {

void OperatorBackward::solve(const ResourceBuckets* res, void* v) {
  auto& indentlevel = data->getSolver()->indentlevel;
  // No propagation on unconstrained resources
  if (!res->getConstrained() || !data->getSolver()->isCapacityConstrained())
    return;

  set<OperationPlan*> propagationList;

  // Debugging log
  ++indentlevel;
  if (getLogLevel() > 0) {
    logger << indentlevel << "Backward propagation of bucketized resource "
           << res;
    if (curOperationPlan) logger << " for operationplan " << curOperationPlan;
    if (curLoadPlan) logger << " on " << curLoadPlan->getDate();
    logger << "\n";
  }

  // Loop until all overloads are resolved
  Date lastloop = Date::infiniteFuture;
  while (true) {
    // Step 1: Find the end date of the latest overload.
    Resource::loadplanlist::const_iterator ldpln_iter =
        res->getLoadPlans().rbegin();
    for (; ldpln_iter != res->getLoadPlans().end(); --ldpln_iter) {
      if (ldpln_iter->getEventType() == 2 &&
          ldpln_iter->getOnhandBeforeDate() < -ROUNDING_ERROR &&
          ldpln_iter->getDate() < lastloop)
        break;
    }
    if (ldpln_iter == res->getLoadPlans().end())
      // Resource doesn't have a single overload
      break;
    double overload = -ldpln_iter->getOnhandBeforeDate();

    // Step 2: Scan for candidates using capacity in this bucket
    map<OperationPlan*, double> candidates;
    for (--ldpln_iter; ldpln_iter != res->getLoadPlans().end(); --ldpln_iter) {
      if (ldpln_iter->getEventType() == 2) break;
      const LoadPlan* ldpln = static_cast<const LoadPlan*>(&*ldpln_iter);
      if (isValidCandidate(ldpln->getOperationPlan()))
        candidates.insert(
            make_pair(ldpln->getOperationPlan(), ldpln->getQuantity()));
    }
    if (ldpln_iter != res->getLoadPlans().end())
      lastloop = ldpln_iter->getDate();
    else
      lastloop = Date::infinitePast;

    // Step 3: Evaluate candidates
    while (overload > ROUNDING_ERROR) {
      double curload;
      OperationPlan* candidate = nullptr;
      for (auto x = candidates.begin(); x != candidates.end(); ++x) {
        if (!candidate ||
            compareCandidates(candidate, x->first,
                              ldpln_iter->getDate() - Duration(1L))) {
          candidate = x->first;
          curload = x->second;
        }
        if (getLogLevel() > 5)
          logger << indentlevel << "   candidate " << x->first << ": "
                 << ((candidate == x->first) ? "*" : "") << "\n";
      }

      // Step 4: Move the candidate early
      if (candidate) {
        if (getLogLevel() > 1)
          logger << indentlevel << "Moving operationplan " << candidate
                 << " to start on " << ldpln_iter->getDate() - Duration(1L)
                 << "\n";
        addMoveStartDate(candidate, ldpln_iter->getDate() - Duration(1L));
        candidate->appendInfo(
            "Moved the start early to resolve resource overload on " +
            res->getName());

        // Propagate
        solve(candidate);

        // Remove from the candidate list
        auto search = candidates.find(candidate);
        if (search != candidates.end()) candidates.erase(search);

        // Propagate the change
        if (getPropagate()) propagationList.insert(candidate);

        // Reduce overload size
        overload += curload;
      } else {
        logger << "Can't find candidate operationplans\n";
        overload = 0.0;
        break;
      }
    }
  };

  --indentlevel;
}

bool OperatorBackward::compareLoadPlans::operator()(const LoadPlan*& a,
                                                    const LoadPlan*& b) {
  if (a->getDate() != b->getDate())
    return b->getDate() < a->getDate();
  else {
    // a. User the original date as a tie breaker
    auto t1 = data->original_dates.find(a->getOperationPlan());
    auto t2 = data->original_dates.find(b->getOperationPlan());
    if (t1 != data->original_dates.end() && t2 == data->original_dates.end())
      return true;
    else if (t1 == data->original_dates.end() &&
             t2 != data->original_dates.end())
      return false;
    else if (t1 != data->original_dates.end() &&
             t2 != data->original_dates.end() && t1->second != t2->second)
      return t2->second < t1->second;
    else
      // b. Default ordering of operationplans
      return a->getOperationPlan() < b->getOperationPlan();
  }
}

void OperatorBackward::solve(const Resource* res, void* v) {
  auto& indentlevel = data->getSolver()->indentlevel;
  // No propagation on unconstrained resources
  if (!res->getConstrained() || !data->getSolver()->isCapacityConstrained())
    return;

  set<OperationPlan*> propagationList;
  map<OperationPlan*, Date> candidates_orginal;

  // Debugging log
  ++indentlevel;
  bool first_action = true;

  // Loop until all overloads are resolved
  unsigned short iterationcount = 0;
  original_dates.clear();
  while (true) {
    list<const LoadPlan*> current_loadplans;
    list<const LoadPlan*> accepted_loadplans;
    double overload = 0.0;
    const LoadPlan* cur = nullptr;
    double accepted_load = 0.0;

    // Step 1: Find the end date of the latest overload.
    Resource::loadplanlist::const_iterator ldpln_iter =
        res->getLoadPlans().rbegin();
    double curMax =
        (ldpln_iter == res->getLoadPlans().end() ? 0
                                                 : ldpln_iter->getMax(false));
    Resource::loadplanlist::const_iterator overload_iter;
    for (; ldpln_iter != res->getLoadPlans().end(); --ldpln_iter) {
      if (ldpln_iter->getEventType() == 4) {
        // Change of the maximum. We need to pick the value of the previous
        // max!
        curMax = ldpln_iter->getMax(false);
        overload = ldpln_iter->getOnhandBeforeDate() - curMax;
        if (overload > ROUNDING_ERROR) overload_iter = ldpln_iter;
        cur = nullptr;
      } else if (ldpln_iter->getEventType() == 1)
        cur = static_cast<const LoadPlan*>(&*ldpln_iter);
      else
        cur = nullptr;

      // Track all operationplans currently loading the resource
      if (cur) {
        if (cur->getOperationPlan()->getConfirmed()) {
          accepted_load -= cur->getQuantity();
          if (cur->getQuantity() < 0)
            accepted_loadplans.push_back(cur);
          else if (cur->getQuantity() > 0) {
            for (auto f = accepted_loadplans.begin();
                 f != accepted_loadplans.end(); ++f) {
              if (cur->getOperationPlan() == (*f)->getOperationPlan()) {
                accepted_loadplans.erase(f);
                break;
              }
            }
          }
        } else {
          if (cur->getQuantity() < 0)
            current_loadplans.push_back(cur);
          else if (cur->getQuantity() > 0) {
            for (auto f = current_loadplans.begin();
                 f != current_loadplans.end(); ++f) {
              if (cur->getOperationPlan() == (*f)->getOperationPlan()) {
                current_loadplans.erase(f);
                break;
              }
            }
          }
        }
      }

      // Detect overload status
      if (!ldpln_iter->isFirstOnDate()) continue;
      overload = ldpln_iter->getOnhandBeforeDate() - curMax;
      if (overload > ROUNDING_ERROR && !current_loadplans.empty()) break;
    }
    if (overload < ROUNDING_ERROR)
      // Resource has not a single overload
      break;

    if (getLogLevel() > 0) {
      if (first_action) {
        logger << indentlevel << "Backward propagation of resource " << res;
        if (curOperationPlan)
          logger << " for operationplan " << curOperationPlan;
        if (curLoadPlan) logger << " on " << curLoadPlan->getDate();
        logger << "\n";
        first_action = false;
      }
      logger << indentlevel << "  Overload of " << overload
             << " detected ending at " << ldpln_iter->getDate() << "\n";
    }

    // Step 2: Establish accepted load at the problem end.
    // All confirmed loadplans are already accepted. We now add approved &
    // proposed to fit the size.
    // We first try to accept the tabu operationplans.
    current_loadplans.sort(compareLoadPlans(this));
    for (short pass = 0; pass <= 1 && !current_loadplans.empty(); ++pass) {
      for (auto f = current_loadplans.begin(); f != current_loadplans.end();) {
        auto is_tabu = tabu.find((*f)->getOperationPlan()) != tabu.end();
        if ((pass == 0 && !is_tabu) || (pass == 1 && is_tabu)) {
          ++f;
          continue;
        }
        if (accepted_load - (*f)->getQuantity() < curMax + ROUNDING_ERROR) {
          auto tmp = f;
          accepted_loadplans.push_back(*f);
          accepted_load -= (*f)->getQuantity();
          ++f;
          current_loadplans.erase(tmp);
        } else
          ++f;
      }
    }

    // Ldpln_iter is now pointing to first event within the overload period.
    if (ldpln_iter != res->getLoadPlans().end()) --ldpln_iter;

    // Step 3: Scan backward till this overload is over.
    res->setFrozenSetups(true);
    for (;
         ldpln_iter != res->getLoadPlans().end() && !current_loadplans.empty();
         --ldpln_iter) {
      if (ldpln_iter->getEventType() == 1)
        cur = static_cast<const LoadPlan*>(&*ldpln_iter);
      else
        cur = nullptr;

      // Track all operationplans currently loading the resource
      if (cur) {
        if (cur->getOperationPlan()->getConfirmed()) {
          // Confirmed loadplans are always accepted immediately
          accepted_load -= cur->getQuantity();
          if (cur->getQuantity() < 0)
            accepted_loadplans.push_back(cur);
          else if (cur->getQuantity() > 0) {
            bool found = false;
            for (auto f = accepted_loadplans.begin();
                 f != accepted_loadplans.end(); ++f) {
              if (cur->getOperationPlan() == (*f)->getOperationPlan()) {
                accepted_load -= cur->getQuantity();
                accepted_loadplans.erase(f);
                found = true;
                break;
              }
            }
            if (!found)
              logger << "Couldn't find confirmed operationplan in the list\n";
          }
        } else if (cur->getQuantity() < 0)
          // New candidates are collected here
          current_loadplans.push_back(cur);
        else if (cur->getQuantity() > 0) {
          for (auto f = accepted_loadplans.begin();
               f != accepted_loadplans.end(); ++f) {
            if (cur->getOperationPlan() == (*f)->getOperationPlan()) {
              // One of the accepted operationplans starts here
              accepted_load -= cur->getQuantity();
              accepted_loadplans.erase(f);
              break;
            }
          }
        }
      }

      // Evaluate at the end of this date
      if (!ldpln_iter->isFirstOnDate()) continue;

      // Done resolving this overload
      if (current_loadplans.empty()) break;

      // Fill up free capacity with available candidates.
      // First non-tabu, then tabu.
      for (short check_limit = 1; check_limit >= 0; --check_limit) {
        for (short pass = 0; pass <= 1; ++pass) {
          for (auto f = current_loadplans.begin();
               f != current_loadplans.end();) {
            auto is_tabu = tabu.find((*f)->getOperationPlan()) != tabu.end();
            if ((pass == 0 && is_tabu) || (pass == 1 && !is_tabu)) {
              ++f;
              continue;
            }
            // Move this candidate if a) it fits within the available size or
            // b) the candidate will never fit anyway.
            if (accepted_load - (*f)->getQuantity() < curMax + ROUNDING_ERROR ||
                -(*f)->getQuantity() > curMax + ROUNDING_ERROR ||
                !check_limit) {
              auto opplan = (*f)->getOperationPlan();

              if (opplan->getEnd() <= ldpln_iter->getDate()) {
                ++f;
                continue;
              }

              if (getLogLevel() > 1)
                logger << indentlevel << "    Moving operationplan " << opplan
                       << " to end on " << ldpln_iter->getDate() << "\n";

              // Move the candidate early
              addMoveEndDate(opplan, ldpln_iter->getDate());
              opplan->appendInfo("Moved early to resolve resource overload on" +
                                 res->getName());

              // Propagate
              solve(opplan);

              // Maintain list of accepted and waiting loads
              accepted_loadplans.push_back(*f);
              accepted_load -= (*f)->getQuantity();
              auto tmp = f;
              ++f;
              current_loadplans.erase(tmp);
              if (accepted_load > curMax - ROUNDING_ERROR ||
                  current_loadplans.empty()) {
                break;
              }
            } else
              ++f;
          }
        }
      }
    }
    res->setFrozenSetups(false);

    if (++iterationcount >= MAX_LOOP) {
      logger << indentlevel
             << "Error: Leaving resource backward propagation loop on " << res
             << " after " << MAX_LOOP << " iterations\n";
      break;
    }
  }
  original_dates.clear();
  --indentlevel;
}

void OperatorBackward::solve(OperationPlan* opplan, void*) {
  auto& indentlevel = data->getSolver()->indentlevel;

  // Keep routing sequence correct after the move
  if (opplan->getOwner() &&
      opplan->getOwner()->getOperation()->hasType<OperationRouting>()) {
    OperationPlan* tmp = opplan;
    OperationPlan* other = tmp->getPrevSubOpplan();
    auto hard_posttime =
        static_cast<OperationRouting*>(tmp->getOwner()->getOperation())
            ->getHardPostTime();
    auto posttime = hard_posttime && other
                        ? other->getOperation()->getPostTime()
                        : Duration(0L);
    if (other && (other->getProposed() || other->getApproved()) &&
        tmp->getStart() < other->getEnd() + posttime) {
      if (getLogLevel() > 1)
        logger << indentlevel << "Moving operationplan " << other
               << " early to end on " << (tmp->getStart() - posttime)
               << " to keep the sequence in the routing\n";
      addMoveEndDate(other, tmp->getStart() - posttime);
      other->appendInfo("Moved the end early to follow a predecessor");
      // Propagate
      solve(other);
    };
  }

  // Keep synchronised deliveries together
  if (opplan->getDemand() && opplan->getDemand()->getOwner() &&
      opplan->getDemand()->getOwner()->hasType<DemandGroup>() &&
      static_cast<DemandGroup*>(opplan->getDemand()->getOwner())->getPolicy() !=
          Demand::POLICY_INDEPENDENT) {
    for (auto dmd = opplan->getDemand()->getOwner()->getMembers();
         dmd != Demand::end(); ++dmd) {
      for (auto dlvr : dmd->getDelivery()) {
        if (dlvr != opplan && dlvr->getEnd() != opplan->getEnd()) {
          addMoveEndDate(dlvr, opplan->getEnd());
          dlvr->appendInfo("Moved to synchronise deliveries");
          // Propagate
          solve(dlvr);
        }
      }
    }
  }

  // Keep dependencies correct TODO
  for (auto d : opplan->getDependencies()) {
    if (opplan != d->getSecond()) continue;
    Date nd = d->getSecond()->getStart();
    if (d->getOperationDependency())
      nd -= d->getOperationDependency()->getHardSafetyLeadtime();
    if (nd < d->getFirst()->getEnd() &&
        (d->getFirst()->getProposed() || d->getFirst()->getApproved())) {
      if (getLogLevel() > 1)
        logger << indentlevel << "Moving operationplan " << d->getFirst()
               << " early to end on " << nd << " to maintain dependencies\n";
      addMoveEndDate(d->getFirst(), nd);
      d->getFirst()->appendInfo("Moved the end early to precede a successor");
      // Propagate
      solve(d->getFirst());
    }
  }
}

bool OperatorBackward::isValidCandidate(OperationPlan* opplan) const {
  if (!getAcceptTabuCandidate()) {
    auto t = tabu.find(opplan);
    if (t != tabu.end()) return false;
  }
  return (opplan->getProposed() || opplan->getApproved()) &&
         opplan->getEnd() != Date::infiniteFuture;
};

bool OperatorBackward::compareCandidates(OperationPlan* opplan1,
                                         OperationPlan* opplan2, Date) const {
  auto t1 = tabu.find(opplan1);
  auto t2 = tabu.find(opplan2);

  if ((t1 != tabu.end() && t2 == tabu.end()) || opplan1 == opplan2)
    return true;
  else if (t1 == tabu.end() && t2 != tabu.end())
    return false;
  else if (opplan1->getEnd() != opplan2->getEnd())
    return opplan2->getEnd() < opplan1->getEnd();

  // If there are dependency links between both operationplans, we should move
  // the predecessor first. Failing to do so can create vicious endless loops of
  // moves.
  // Check 1: walk downstream from opplan1
  stack<OperationPlan*> deps;
  deps.push(opplan1);
  while (!deps.empty()) {
    auto o = deps.top();
    deps.pop();
    if (o == opplan2) {
      // Force moving the first one
      return true;
    }
    for (auto e : o->getDependencies()) {
      if (e->getFirst() == o) deps.push(e->getSecond());
    }
  }
  // Check 2: walk upstream from opplan2
  deps.push(opplan2);
  while (!deps.empty()) {
    auto o = deps.top();
    deps.pop();
    if (o == opplan1) {
      // Force moving the second one
      return false;
    }
    for (auto e : o->getDependencies()) {
      if (e->getSecond() == o) deps.push(e->getFirst());
    }
  }

  double score1;
  if (t1 != tabu.end())
    score1 = t1->second;
  else
    score1 = -static_cast<double>(opplan1->getDelay()) / 86400;

  double score2;
  if (t2 != tabu.end())
    score2 = t2->second;
  else
    score2 = -static_cast<double>(opplan2->getDelay()) / 86400;

  // Final result
  if (fabs(score1 - score2) > ROUNDING_ERROR)
    return score1 > score2;
  else
    return *opplan1 < *opplan2;
}

}  // namespace frepple
