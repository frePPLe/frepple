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

void OperatorForward::solve(void*) {
  // Detect whether this cluster has operation dependencies.
  auto has_dependencies = false;
  for (auto& o : Operation::all()) {
    if ((cluster == -1 || o.getCluster() == cluster) &&
        !o.getDependencies().empty()) {
      has_dependencies = true;
      break;
    }
  }

  Date current = Plan::instance().getCurrent();
  for (auto& o : Operation::all()) {
    if ((cluster != -1 && o.getCluster() != cluster) ||
        o.hasType<OperationInventory>())
      continue;
    OperationPlan::iterator opplan_iter(&o);
    while (OperationPlan* opplan = opplan_iter.next()) {
      auto tmp =
          data->getSolver()->isLeadTimeConstrained(opplan->getOperation());
      if (
          // Maintain dependencies
          !o.getDependencies().empty()
          // Maintain the sequence in a routing
          || (opplan->getOwner() &&
              opplan->getOwner()->getOperation()->hasType<OperationRouting>())
          // Move operationplans planned in the past
          || (opplan->getProposed() &&
              opplan->getStart() < o.getFence(opplan) && tmp) ||
          (opplan->getApproved() && opplan->getStart() < current && tmp))
        solve(opplan, data);
    }
  }

  // Propagate the shortage across all buffers, starting from the deepest
  // level
  for (short lvl = HasLevel::getNumberOfLevels(); lvl; --lvl) {
    bool action_at_level = false;
    for (auto& b : Buffer::all()) {
      if ((cluster != -1 && b.getCluster() != cluster) || b.getLevel() != lvl ||
          b.getFlowPlans().empty())
        continue;
      try {
        b.solve(*this, data);
        if (!data->getCommandManager()->empty()) action_at_level = true;
        data->getCommandManager()->commit();
      } catch (...) {
        data->getCommandManager()->rollback();
        logger << "Error: Caught an exception while solving buffer '" << b
               << "':\n";
        try {
          throw;
        } catch (const bad_exception&) {
          logger << "  bad exception\n";
        } catch (const exception& e) {
          logger << "  " << e.what() << "\n";
        } catch (...) {
          logger << "  Unknown type\n";
        }
      }
    }

    // TODO We can drastically limit the list of resources to visit in every
    // level sweep. That would require keeping track of a list of resources to
    // propagate. Initially all resources would be in that list for an first,
    // initial sweep. After the initial move only resource whose plan is
    // changing should be put back on the propagation list.
    action_at_level = true;
    while (action_at_level || has_dependencies) {
      // One or more shortages got resolved. We propagate to the resources
      // before solving the next level.
      action_at_level = false;
      for (auto& res : Resource::all()) {
        if ((cluster != -1 && res.getCluster() != cluster) ||
            res.getLoadPlans().empty() || res.isGroup())
          continue;
        try {
          res.solve(*this, nullptr);
          if (!data->getCommandManager()->empty()) action_at_level = true;
          data->getCommandManager()->commit();
        } catch (...) {
          data->getCommandManager()->rollback();
          logger << "Error: Caught an exception while solving resource '" << res
                 << "':\n";
          try {
            throw;
          } catch (const bad_exception&) {
            logger << "  bad exception\n";
          } catch (const exception& e) {
            logger << "  " << e.what() << "\n";
          } catch (...) {
            logger << "  Unknown type\n";
          }
        }
      }
      if (!action_at_level) break;
    }
  }
}

void OperatorForward::solve(OperationPlan* opplan, void*) {
  if (opplan->getEnd() == Date::infiniteFuture)
    // Can't more forward than 2031
    return;
  auto& indentlevel = data->getSolver()->indentlevel;

  // Debugging log
  ++indentlevel;
  if (indentlevel > 30000) throw RuntimeException("Excessive recursion depth");
  if (getLogLevel() > 0 && getPropagate())
    logger << indentlevel << "Forward propagation of operationplan " << opplan
           << "\n";

  OperationPlan* tmp_operationplan = curOperationPlan;
  FlowPlan* tmp_flowplan = curFlowPlan;
  LoadPlan* tmp_loadplan = curLoadPlan;

  // Move the operationplan to be feasible
  if (data->getSolver()->isLeadTimeConstrained(opplan->getOperation())) {
    if (opplan->getProposed()) {
      Date earliest = opplan->getOperation()->getFence(opplan);
      if (opplan->getStart() < earliest) {
        addMoveStartDate(opplan, earliest);
        if (getLogLevel() > 1)
          logger << indentlevel << "Delaying operationplan " << opplan
                 << " till " << opplan->getDates() << "\n";
        opplan->appendInfo("Moved the start late after the release fence");
      }
    } else if (opplan->getApproved() &&
               opplan->getStart() < Plan::instance().getCurrent()) {
      addMoveStartDate(opplan, Plan::instance().getCurrent());
      opplan->appendInfo("Moved the start late to the current date");
      if (getLogLevel() > 1)
        logger << indentlevel << "Delaying operationplan " << opplan << " till "
               << opplan->getDates() << "\n";
    }
  }

  if (getPropagate()) {
    if (data->getSolver()->isCapacityConstrained()) {
      // Propagate resource overloads by delaying other operationplans
      auto ldpln_iter2 = opplan->getLoadPlans();
      curLoadPlan = nullptr;
      while ((curLoadPlan = ldpln_iter2.next())) {
        if (curLoadPlan->getQuantity() < 0 && curLoadPlan->getResource() &&
            curLoadPlan->getLoad())
          break;
      };
      while (curLoadPlan) {
        LoadPlan* nextLoadPlan = nullptr;
        while ((nextLoadPlan = ldpln_iter2.next())) {
          if (nextLoadPlan->getQuantity() < 0 && nextLoadPlan->getResource() &&
              nextLoadPlan->getLoad())
            break;
        };
        curFlowPlan = nullptr;
        curOperationPlan = opplan;
        curLoadPlan->getResource()->solve(*this, nullptr);
        curLoadPlan = nextLoadPlan;
      };
    };

    // Propagate the changes downstream
    auto flwpln_iter = opplan->getFlowPlans();
    while ((curFlowPlan = flwpln_iter.next())) {
      curLoadPlan = nullptr;
      curOperationPlan = opplan;
      solve(curFlowPlan->getBuffer(), nullptr);
    }
  }

  // Propagate dependencies
  for (auto d : opplan->getDependencies()) {
    if (opplan != d->getFirst()) continue;
    Date nd = d->getFirst()->getEnd();
    if (d->getOperationDependency())
      nd += d->getOperationDependency()->getHardSafetyLeadtime();
    if (nd > d->getSecond()->getStart() &&
        (d->getSecond()->getProposed() || d->getSecond()->getApproved())) {
      if (getLogLevel() > 1)
        logger << indentlevel << "Moving operationplan " << d->getSecond()
               << " late to start on " << nd << " to maintain dependencies\n";
      addMoveStartDate(d->getSecond(), nd);
      d->getSecond()->appendInfo(
          "Moved the start late to follow a predecessor");
      solve(d->getSecond(), nullptr);
    }
  }

  // Keep routing sequence correct and with minimal slack
  if (opplan->getOwner() &&
      opplan->getOwner()->getOperation()->hasType<OperationRouting>()) {
    OperationPlan* other = opplan->getNextSubOpplan();
    auto hard_posttime =
        static_cast<OperationRouting*>(opplan->getOwner()->getOperation())
            ->getHardPostTime();
    auto posttime =
        hard_posttime ? opplan->getOperation()->getPostTime() : Duration(0L);
    if (other && (other->getApproved() || other->getProposed())) {
      if (opplan->getEnd() + posttime > other->getStart()) {
        if (getLogLevel() > 1)
          logger << indentlevel << "Moving operationplan " << other
                 << " late to start on " << (opplan->getEnd() + posttime)
                 << " to keep the sequence in the routing\n";
        addMoveStartDate(other, opplan->getEnd() + posttime);
        other->appendInfo("Moved the start late to follow a predecessor");
        solve(other, nullptr);
      } else if (other->getStart() - opplan->getEnd() >
                     opplan->getOperation()->getMaxEarly() &&
                 (excess_scanner == direction::both ||
                  excess_scanner == direction::downstream)) {
        if (getLogLevel() > 1)
          logger << indentlevel << "Moving operationplan " << other
                 << " late to start on " << opplan->getEnd()
                 << " to reduce slack in the routing\n";
        addMoveStartDate(other, opplan->getEnd());
        other->appendInfo("Moved the start late to reduce slack");
        auto tmp = excess_scanner;
        excess_scanner = direction::downstream;
        solve(other, nullptr);
        excess_scanner = tmp;
      }
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
          dlvr->appendInfo("Moved to synchronize deliveries");
          solve(dlvr, nullptr);
        }
      }
    }
  }

  // Apply to the sub-operations
  auto subopplaniter = opplan->getSubOperationPlans();
  while (auto subopplan = subopplaniter.next()) solve(subopplan, nullptr);

  // Apply to the super-operationplan
  // TODO if (opplan->getOwner())
  //  solve(opplan->getOwner(), nullptr);

  // Restore solver state to original situation
  curFlowPlan = tmp_flowplan;
  curLoadPlan = tmp_loadplan;
  curOperationPlan = tmp_operationplan;
  --indentlevel;
}

void OperatorForward::solve(const Operation* oper, void*) {
  // Debugging log
  auto& indentlevel = data->getSolver()->indentlevel;

  ++indentlevel;
  if (getLogLevel() > 0)
    logger << indentlevel << "Forward propagation of operation " << oper
           << "\n";

  // Loop over operationplans
  OperationPlan::iterator opplan_iter(oper);
  while (OperationPlan* opplan = opplan_iter.next()) {
    solve(opplan, nullptr);
  }
  --indentlevel;
}

void OperatorForward::solve(const ResourceBuckets* res, void*) {
  // No propagation on unconstrained resources
  if (!res->getConstrained() || !data->getSolver()->isCapacityConstrained())
    return;

  set<OperationPlan*> propagationList;
  auto& indentlevel = data->getSolver()->indentlevel;

  // Debugging log
  ++indentlevel;
  bool first_action = true;

  // Loop until all overloads are resolved
  Date lastloop;
  while (true) {
    // Step 1: Find the end date of the earliest overloaded bucket.
    auto ldpln_iter = res->getLoadPlans().begin();
    for (; ldpln_iter != res->getLoadPlans().end(); ++ldpln_iter) {
      if (ldpln_iter->getEventType() == 2 &&
          ldpln_iter->getOnhandBeforeDate() < -ROUNDING_ERROR &&
          ldpln_iter->getDate() > lastloop)
        break;
    }
    if (ldpln_iter == res->getLoadPlans().end())
      // Resource doesn't have a single overload
      break;
    double overload = -ldpln_iter->getOnhandBeforeDate();
    Date nextBucket = ldpln_iter->getDate();
    lastloop = nextBucket;

    // Step 2: Scan for candidates using capacity in this bucket
    map<OperationPlan*, double> candidates;
    for (--ldpln_iter; ldpln_iter != res->getLoadPlans().end(); --ldpln_iter) {
      if (ldpln_iter->getEventType() == 2) break;
      if (ldpln_iter->getEventType() != 1) continue;
      const LoadPlan* ldpln = static_cast<const LoadPlan*>(&*ldpln_iter);
      if (isValidCandidate(ldpln->getOperationPlan()))
        candidates.insert(
            make_pair(ldpln->getOperationPlan(), ldpln->getQuantity()));
    }
    auto available = (ldpln_iter != res->getLoadPlans().end() &&
                      ldpln_iter->getEventType() == 2)
                         ? ldpln_iter->getOnhand()
                         : 0.0;

    // Step 3: Evaluate candidates
    while (overload > ROUNDING_ERROR) {
      double curload;
      OperationPlan* candidate = nullptr;
      for (auto x = candidates.begin(); x != candidates.end(); ++x) {
        if (!candidate || -x->second > available + ROUNDING_ERROR ||
            compareCandidates(candidate, x->first, nextBucket)) {
          candidate = x->first;
          curload = x->second;
        }
        if (getLogLevel() > 5) {
          if (first_action) {
            logger << indentlevel
                   << "Forward propagation of bucketized resource " << res;
            if (curOperationPlan)
              logger << " for operationplan " << curOperationPlan;
            if (curLoadPlan) logger << " on " << curLoadPlan->getDate();
            logger << "\n";
            first_action = false;
          }
          logger << indentlevel << "   candidate " << x->first << ": "
                 << ((candidate == x->first) ? "*" : "") << "\n";
        }
        if (-x->second > available + ROUNDING_ERROR) {
          // This candidate is already bigger than the availability in the
          // bucket. No need to look further.
          break;
        }
      }

      /*
      if (candidate && - curload > available && available > ROUNDING_ERROR){
        // TODO  Step 4: Split the candidate
      }
      else
      */
      if (candidate) {
        // Step 4: Move the candidate late
        if (getLogLevel() > 1) {
          if (first_action) {
            logger << indentlevel
                   << "Forward propagation of bucketized resource " << res;
            if (curOperationPlan)
              logger << " for operationplan " << curOperationPlan;
            if (curLoadPlan) logger << " on " << curLoadPlan->getDate();
            logger << "\n";
            first_action = false;
          }
          logger << indentlevel << "Moving operationplan " << candidate
                 << " to start on " << nextBucket << "\n";
        }
        addMoveStartDate(candidate, nextBucket);
        candidate->appendInfo(
            "Moved the start late due to a capacity shortage on " +
            res->getName());

        // Propagate dependencies
        for (auto d : candidate->getDependencies()) {
          if (candidate != d->getFirst()) continue;
          Date nd = d->getFirst()->getEnd();
          if (d->getOperationDependency())
            nd += d->getOperationDependency()->getHardSafetyLeadtime();
          if (nd > d->getSecond()->getStart() &&
              (d->getSecond()->getApproved() ||
               d->getSecond()->getProposed())) {
            if (getLogLevel() > 1)
              logger << indentlevel << "Moving operationplan " << d->getSecond()
                     << " late to start on " << nd
                     << " to maintain dependencies\n";
            addMoveStartDate(d->getSecond(), nd);
            propagationList.insert(d->getSecond());
            d->getSecond()->appendInfo(
                "Moved the start late to follow a predecessor");
          }
        }

        // Keep routing sequence correct
        if (candidate->getOwner() && candidate->getOwner()
                                         ->getOperation()
                                         ->hasType<OperationRouting>()) {
          OperationPlan* tmp = candidate;
          OperationPlan* other = tmp->getNextSubOpplan();
          auto hard_posttime =
              static_cast<OperationRouting*>(tmp->getOwner()->getOperation())
                  ->getHardPostTime();
          auto posttime =
              hard_posttime ? tmp->getOperation()->getPostTime() : Duration(0L);
          while (other && (other->getApproved() || other->getProposed()) &&
                 tmp->getEnd() + posttime > other->getStart()) {
            addMoveStartDate(other, tmp->getEnd() + posttime);
            other->appendInfo("Moved the start late to follow a predecessor");
            if (getPropagate()) propagationList.insert(other);
            tmp = other;
            other = tmp->getNextSubOpplan();
            if (hard_posttime) posttime = tmp->getOperation()->getPostTime();
          };
        }

        // Keep synchronised deliveries together
        if (candidate->getDemand() && candidate->getDemand()->getOwner() &&
            candidate->getDemand()->getOwner()->hasType<DemandGroup>() &&
            static_cast<DemandGroup*>(candidate->getDemand()->getOwner())
                    ->getPolicy() != Demand::POLICY_INDEPENDENT) {
          for (auto dmd = candidate->getDemand()->getOwner()->getMembers();
               dmd != Demand::end(); ++dmd) {
            for (auto dlvr : dmd->getDelivery()) {
              if (dlvr != candidate && dlvr->getEnd() != candidate->getEnd()) {
                addMoveEndDate(dlvr, candidate->getEnd());
                dlvr->appendInfo("Moved to synchronize deliveries");
                if (getPropagate()) propagationList.insert(dlvr);
              }
            }
          }
        }

        // Remove from the candidate list
        auto search = candidates.find(candidate);
        if (search != candidates.end()) candidates.erase(search);

        // Propagate the change
        if (getPropagate()) propagationList.insert(candidate);

        // Reduce overload size
        overload += curload;
      } else {
        if (getLogLevel() > 0) {
          if (first_action) {
            logger << indentlevel
                   << "Forward propagation of bucketized resource " << res;
            if (curOperationPlan)
              logger << " for operationplan " << curOperationPlan;
            if (curLoadPlan) logger << " on " << curLoadPlan->getDate();
            logger << "\n";
            first_action = false;
          }
          logger << "Can't find candidate operationplans\n";
        }
        overload = 0.0;
        break;
      }
    }
  };

  // Propagate all collected changes
  while (!propagationList.empty()) {
    // Find the earliest operationplan in the list.
    auto sel = propagationList.end();
    for (auto cd = propagationList.begin(); cd != propagationList.end(); ++cd)
      if (sel == propagationList.end() || **cd < **sel) sel = cd;

    // Propagate the operationplan
    solve(*sel, nullptr);

    // Remove from the list
    propagationList.erase(sel);
  }

  --indentlevel;
}

bool OperatorForward::compareLoadPlans::operator()(const LoadPlan*& a,
                                                   const LoadPlan*& b) {
  if (a->getDate() != b->getDate())
    // a. Order by date
    return a->getDate() < b->getDate();
  else {
    // b. Prefer moving based on setup time
    auto setup_a = a->getOperationPlan()->getSetupEnd() -
                   a->getOperationPlan()->getStart();
    auto setup_b = b->getOperationPlan()->getSetupEnd() -
                   b->getOperationPlan()->getStart();
    if (setup_a != setup_b) return setup_a < setup_b;

    // c. User the original date as a tie breaker
    auto t1 = data->original_dates.find(a->getOperationPlan());
    auto t2 = data->original_dates.find(b->getOperationPlan());
    if (t1 != data->original_dates.end() && t2 == data->original_dates.end())
      return true;
    else if (t1 == data->original_dates.end() &&
             t2 != data->original_dates.end())
      return false;
    else if (t1 != data->original_dates.end() &&
             t2 != data->original_dates.end() && t1->second != t2->second)
      return t1->second < t2->second;
    else
      // d. Default ordering of operationplans
      return a->getOperationPlan() < b->getOperationPlan();
  }
}

void OperatorForward::solve(const Resource* res, void*) {
  // No propagation on unconstrained resources
  if (!res->getConstrained() || !data->getSolver()->isCapacityConstrained())
    return;

  indent& indentlevel = data->getSolver()->indentlevel;
  set<OperationPlan*> propagationList;
  map<OperationPlan*, Date> candidates_orginal;

  // Debugging log
  ++indentlevel;
  bool first_action = true;

  // Loop until all overloads are resolved
  original_dates.clear();
  unsigned short iterationcount = 0;
  while (true) {
    list<const LoadPlan*> current_loadplans;
    list<const LoadPlan*> accepted_loadplans;
    double overload = 0.0;
    const LoadPlan* cur = nullptr;
    double accepted_load = 0.0;

    // Step 1: Find the start of the first overload.
    Resource::loadplanlist::const_iterator ldpln_iter =
        res->getLoadPlans().begin();
    double curMax =
        (ldpln_iter == res->getLoadPlans().end()) ? 0 : ldpln_iter->getMax();
    for (; ldpln_iter != res->getLoadPlans().end(); ++ldpln_iter) {
      if (ldpln_iter->getEventType() == 4) {
        // Change of the maximum
        curMax = ldpln_iter->getMax();
        cur = nullptr;
      } else if (ldpln_iter->getEventType() == 1)
        cur = static_cast<const LoadPlan*>(&*ldpln_iter);
      else
        cur = nullptr;

      // Track all operationplans currently loading the resource
      if (cur) {
        if (cur->getOperationPlan()->getConfirmed()) {
          accepted_load += cur->getQuantity();
          if (cur->getQuantity() > 0)
            accepted_loadplans.push_back(cur);
          else if (cur->getQuantity() < 0) {
            for (auto f = accepted_loadplans.begin();
                 f != accepted_loadplans.end(); ++f) {
              if (cur->getOperationPlan() == (*f)->getOperationPlan()) {
                accepted_loadplans.erase(f);
                break;
              }
            }
          }
        } else {
          if (cur->getQuantity() > 0)
            current_loadplans.push_back(cur);
          else if (cur->getQuantity() < 0) {
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
      if (!ldpln_iter->isLastOnDate()) continue;
      overload = ldpln_iter->getOnhandAfterDate() - curMax;
      if (overload > ROUNDING_ERROR && !current_loadplans.empty()) break;
    }
    if (overload < ROUNDING_ERROR)
      // Resource has not a single overload
      break;

    if (getLogLevel() > 0) {
      if (first_action) {
        logger << indentlevel << "Forward propagation of resource " << res;
        if (curOperationPlan)
          logger << " for operationplan " << curOperationPlan;
        if (curLoadPlan) logger << " on " << curLoadPlan->getDate();
        logger << "\n";
        first_action = false;
      }
      logger << indentlevel << "  Overload of " << overload
             << " detected starting at " << ldpln_iter->getDate() << "\n";
    }

    // Step 2: Establish accepted load at the problem start.
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
        if (accepted_load + (*f)->getQuantity() < curMax + ROUNDING_ERROR) {
          auto tmp = f;
          accepted_loadplans.push_back(*f);
          accepted_load += (*f)->getQuantity();
          ++f;
          current_loadplans.erase(tmp);
        } else
          ++f;
      }
    }

    // Ldpln_iter is now pointing to first event within the overload period.
    if (ldpln_iter != res->getLoadPlans().end()) ++ldpln_iter;

    // Step 3: Scan forward till this overload is over.
    res->setFrozenSetups(true);
    for (;
         ldpln_iter != res->getLoadPlans().end() && !current_loadplans.empty();
         ++ldpln_iter) {
      if (ldpln_iter->getEventType() == 4) {
        // Change of the maximum
        curMax = ldpln_iter->getMax();
        cur = nullptr;
      } else if (ldpln_iter->getEventType() == 1)
        cur = static_cast<const LoadPlan*>(&*ldpln_iter);
      else
        cur = nullptr;

      // Track all operationplans currently loading the resource
      if (cur) {
        if (cur->getOperationPlan()->getConfirmed()) {
          // Confirmed loadplans are always accepted immediately
          accepted_load += cur->getQuantity();
          if (cur->getQuantity() > 0)
            accepted_loadplans.push_back(cur);
          else if (cur->getQuantity() < 0) {
            bool found = false;
            for (auto f = accepted_loadplans.begin();
                 f != accepted_loadplans.end(); ++f) {
              if (cur->getOperationPlan() == (*f)->getOperationPlan()) {
                accepted_load += cur->getQuantity();
                accepted_loadplans.erase(f);
                found = true;
                break;
              }
            }
            if (!found)
              logger << "Couldn't find confirmed operationplan in the list\n";
          }
        } else if (cur->getQuantity() > 0)
          // New candidates are collected here
          current_loadplans.push_back(cur);
        else if (cur->getQuantity() < 0) {
          for (auto f = accepted_loadplans.begin();
               f != accepted_loadplans.end(); ++f) {
            if (cur->getOperationPlan() == (*f)->getOperationPlan()) {
              // One of the accepted operationplans ends here
              accepted_load += cur->getQuantity();
              accepted_loadplans.erase(f);
              break;
            }
          }
        }
      }

      // Evaluate at the end of this date
      if (!ldpln_iter->isLastOnDate()) continue;

      // Done resolving this overload
      if (current_loadplans.empty()) break;

      // Fill up free capacity with available candidates.
      // First non-tabu, then tabu.
      bool done = false;
      for (short check_limit = 1; check_limit >= 0; --check_limit) {
        for (short pass = 0; pass <= 1 && !done; ++pass) {
          for (auto f = current_loadplans.begin();
               f != current_loadplans.end();) {
            auto is_tabu = tabu.find((*f)->getOperationPlan()) != tabu.end();
            if ((pass == 0 && is_tabu) || (pass == 1 && !is_tabu)) {
              ++f;
              continue;
            }
            if (accepted_load + (*f)->getQuantity() < curMax + ROUNDING_ERROR ||
                (*f)->getQuantity() > curMax + ROUNDING_ERROR || !check_limit) {
              // Move this candidate if a) it fits within the available size or
              // b) the candidate will never fit anyway.
              auto opplan = (*f)->getOperationPlan();

              if (opplan->getStart() >= ldpln_iter->getDate()) {
                ++f;
                continue;
              }

              if (getLogLevel() > 1)
                logger << indentlevel << "    Moving operationplan " << opplan
                       << " to start on " << ldpln_iter->getDate() << "\n";

              // Move the candidate late
              addMoveStartDate(opplan, ldpln_iter->getDate());
              opplan->appendInfo(
                  "Moved the start late due to a capacity shortage on " +
                  res->getName());

              // Propagate dependencies
              for (auto d : opplan->getDependencies()) {
                if (opplan != d->getFirst()) continue;
                Date nd = d->getFirst()->getEnd();
                if (d->getOperationDependency())
                  nd += d->getOperationDependency()->getHardSafetyLeadtime();
                if (nd > d->getSecond()->getStart() &&
                    (d->getSecond()->getProposed() ||
                     d->getSecond()->getApproved())) {
                  if (getLogLevel() > 1)
                    logger << indentlevel << "Moving operationplan "
                           << d->getSecond() << " late to start on " << nd
                           << " to maintain dependencies\n";
                  addMoveStartDate(d->getSecond(), nd);
                  d->getSecond()->appendInfo(
                      "Moved the start late to follow a predecessor");
                  propagationList.insert(d->getSecond());
                }
              }

              // Keep routing sequence correct
              if (opplan->getOwner() && opplan->getOwner()
                                            ->getOperation()
                                            ->hasType<OperationRouting>()) {
                OperationPlan* tmp = opplan;
                OperationPlan* other = tmp->getNextSubOpplan();
                auto hard_posttime = static_cast<OperationRouting*>(
                                         tmp->getOwner()->getOperation())
                                         ->getHardPostTime();
                auto posttime = hard_posttime
                                    ? tmp->getOperation()->getPostTime()
                                    : Duration(0L);
                while (other &&
                       (other->getApproved() || other->getProposed()) &&
                       tmp->getEnd() + posttime > other->getStart()) {
                  if (getLogLevel() > 1)
                    logger << indentlevel << "    Moving operationplan "
                           << other << " late to start on "
                           << (tmp->getEnd() + posttime)
                           << " to keep the sequence in the routing\n";
                  addMoveStartDate(other, tmp->getEnd() + posttime);
                  other->appendInfo(
                      "Moved the start late to follow a predecessor");
                  if (getPropagate()) propagationList.insert(other);
                  tmp = other;
                  other = tmp->getNextSubOpplan();
                  if (hard_posttime)
                    posttime = tmp->getOperation()->getPostTime();
                };
              }

              // Keep synchronised deliveries together
              if (opplan->getDemand() && opplan->getDemand()->getOwner() &&
                  opplan->getDemand()->getOwner()->hasType<DemandGroup>() &&
                  static_cast<DemandGroup*>(opplan->getDemand()->getOwner())
                          ->getPolicy() != Demand::POLICY_INDEPENDENT) {
                for (auto dmd = opplan->getDemand()->getOwner()->getMembers();
                     dmd != Demand::end(); ++dmd) {
                  for (auto dlvr : dmd->getDelivery()) {
                    if (dlvr != opplan && dlvr->getEnd() != opplan->getEnd()) {
                      addMoveEndDate(dlvr, opplan->getEnd());
                      dlvr->appendInfo("Moved to synchronize deliveries");
                      if (getPropagate()) propagationList.insert(dlvr);
                    }
                  }
                }
              }

              // Propagate changes
              if (getPropagate()) propagationList.insert(opplan);

              // Maintain list of accepted and waiting loads
              accepted_loadplans.push_back(*f);
              accepted_load += (*f)->getQuantity();
              auto tmp = f;
              ++f;
              current_loadplans.erase(tmp);

              if (accepted_load > curMax - ROUNDING_ERROR ||
                  current_loadplans.empty()) {
                done = true;
                break;
              }
            } else
              ++f;
          }
        }
      }
      if (done) break;
    }
    res->setFrozenSetups(false);

    if (++iterationcount >= MAX_LOOP) {
      logger << indentlevel
             << "Error: Leaving resource forward propagation loop on " << res
             << " after " << MAX_LOOP << " iterations\n";
      break;
    }
  }
  original_dates.clear();

  // Propagate all collected changes
  while (!propagationList.empty()) {
    // Find the earliest operationplan in the list.
    auto sel = propagationList.end();
    for (auto cd = propagationList.begin(); cd != propagationList.end(); ++cd)
      if (sel == propagationList.end() || **cd < **sel) sel = cd;

    // Propagate the operationplan
    solve(*sel, nullptr);

    // Remove from the list
    propagationList.erase(sel);
  }

  --indentlevel;
}

void OperatorForward::solve(const Buffer* buf, void*) {
  if (buf->hasType<BufferInfinite>()) return;

  if ((data->getSolver()->getConstraints() &
       (SolverCreate::MFG_LEADTIME + SolverCreate::PO_LEADTIME)) == 0)
    // Material shortages are ok in this type of plan.
    return;

  auto& indentlevel = data->getSolver()->indentlevel;
  set<OperationPlan*> propagationList;

  // Debugging log
  ++indentlevel;
  bool first_action = true;

  // Loop until all downstream shortages are resolved
  bool ok = false;
  unsigned short iterationcount = 0;
  do {
    // Scan for shortages since the start of the horizon.
    auto flpln_iter = buf->getFlowPlanIterator();
    const FlowPlan* candidate = nullptr;
    while (flpln_iter != buf->getFlowPlans().end()) {
      if (flpln_iter->getEventType() == 1 && flpln_iter->getQuantity() < 0.0) {
        auto tmp =
            static_cast<const FlowPlan*>(&*flpln_iter)->getOperationPlan();
        if (isValidCandidate(tmp)) {
          if (!candidate ||
              compareCandidates(candidate->getOperationPlan(), tmp))
            candidate = static_cast<const FlowPlan*>(&*flpln_iter);
        }
      }
      if (flpln_iter->isLastOnDate() &&
          flpln_iter->getOnhand() < -ROUNDING_ERROR)
        // Shortage to solve
        break;
      ++flpln_iter;
    }

    if (flpln_iter == buf->getFlowPlans().end()) {
      // Hurray, no shortages found
      ok = true;
      break;
    }

    // Candidate to move: last acceptable consuming flowplan at or before the
    // date when shortage starts.
    // The candidate will be moved to the  date when the next supply arrives
    // in the buffer. It is possible that at that date the shortage isn't solved
    // yet.
    if (!candidate) {
      // We can't resolve the shortage by moving operationplans late.
      // Put the producers on the list to propagate by moving early again.
      ok = true;
      auto flpln_iter_candidate = flpln_iter;
      while (flpln_iter_candidate != buf->getFlowPlans().end()) {
        if (flpln_iter_candidate->getEventType() == 1 &&
            flpln_iter_candidate->getQuantity() > 0) {
          candidate = static_cast<const FlowPlan*>(&*flpln_iter_candidate);
          if (!candidate->getOperationPlan()->getConfirmed()) {
            if (getLogLevel() > 1) {
              if (first_action) {
                logger << indentlevel << "Forward propagation of buffer "
                       << buf;
                if (curOperationPlan)
                  logger << " for operationplan " << curOperationPlan;
                if (curFlowPlan) logger << " on " << curFlowPlan->getDate();
                logger << "\n";
                first_action = false;
              }
              logger << indentlevel << "Adding operationplan "
                     << candidate->getOperationPlan()
                     << " as candidate to resolve in opposite direction\n";
            }
            unresolvables.insert(candidate->getOperationPlan());
          }
        }
        ++flpln_iter_candidate;
      }
      break;
    } else {
      auto flpln_iter2 = flpln_iter;
      while (flpln_iter2 != buf->getFlowPlans().end()) {
        if (flpln_iter2->getQuantity() > 0) break;
        ++flpln_iter2;
      }
      if (flpln_iter2 == buf->getFlowPlans().end()) {
        auto newsize = candidate->getQuantity() - flpln_iter->getOnhand();
        if (newsize > -ROUNDING_ERROR) newsize = 0.0;
        if (getLogLevel() > 0) {
          if (first_action) {
            first_action = false;
            logger << indentlevel << "Forward propagation of buffer " << buf;
            if (curOperationPlan)
              logger << " for operationplan " << curOperationPlan;
            if (curFlowPlan) logger << " on " << curFlowPlan->getDate();
            logger << "\n";
          }
          logger << indentlevel << "Resizing operationplan "
                 << candidate->getOperationPlan() << " to consume only "
                 << newsize << "\n";
        }
        addResize(const_cast<FlowPlan*>(candidate), newsize, true);
        candidate->getOperationPlan()->appendInfo(
            "Reduced the quantity to match material supply of " +
            candidate->getItem()->getName());
        continue;
      }

      // Resolving (part of) the shortage by moving this operationplan
      // TODO consider splitting the consumer if (shortage <
      // candidate->getQuantity() ) or to find a smarter match on the quantity
      if (candidate->getFlow()->hasType<FlowStart, FlowTransferBatch>()) {
        if (candidate->getFlow()->hasType<FlowTransferBatch>()) {
          // Some calculation is required to translate the date of the candidate
          // transfer batch into a new start date of the operation.
          Duration delta;
          candidate->getOperation()->calculateOperationTime(
              candidate->getOperationPlan(), candidate->getDate(),
              flpln_iter2->getDate(), &delta);
          DateRange newdate = candidate->getOperation()->calculateOperationTime(
              candidate->getOperationPlan(),
              candidate->getOperationPlan()->getStart(), delta, true);
          if (getLogLevel() > 1) {
            if (first_action) {
              first_action = false;
              logger << indentlevel << "Forward propagation of buffer " << buf;
              if (curOperationPlan)
                logger << " for operationplan " << curOperationPlan;
              if (curFlowPlan) logger << " on " << curFlowPlan->getDate();
              logger << "\n";
            }
            logger << indentlevel << "Moving operationplan "
                   << candidate->getOperationPlan() << " to start on "
                   << newdate.getEnd() << " to move a transfer batch to "
                   << flpln_iter2->getDate() << "\n";
          }
          addMoveStartDate(candidate->getOperationPlan(), newdate.getEnd());
          candidate->getOperationPlan()->appendInfo(
              "Moved the start late to match material supply of " +
              candidate->getItem()->getName());
        } else {
          // We know the date where we need to move the operationplan to
          Date newopplandate =
              candidate->computeFlowToOperationDate(flpln_iter2->getDate());
          if (getLogLevel() > 1) {
            if (first_action) {
              first_action = false;
              logger << indentlevel << "Forward propagation of buffer " << buf;
              if (curOperationPlan)
                logger << " for operationplan " << curOperationPlan;
              if (curFlowPlan) logger << " on " << curFlowPlan->getDate();
              logger << "\n";
            }
            logger << indentlevel << "Moving operationplan "
                   << candidate->getOperationPlan() << " to start on "
                   << newopplandate << "\n";
          }
          addMoveStartDate(candidate->getOperationPlan(), newopplandate);
          candidate->getOperationPlan()->appendInfo(
              "Moved the start late to match material supply of " +
              candidate->getItem()->getName());
        }

        // Propagate dependencies
        for (auto d : candidate->getOperationPlan()->getDependencies()) {
          if (candidate->getOperationPlan() != d->getFirst()) continue;
          Date nd = d->getFirst()->getEnd();
          if (d->getOperationDependency())
            nd += d->getOperationDependency()->getHardSafetyLeadtime();
          if (nd > d->getSecond()->getStart() &&
              (d->getSecond()->getApproved() ||
               d->getSecond()->getProposed())) {
            if (getLogLevel() > 1)
              logger << indentlevel << "Moving operationplan " << d->getSecond()
                     << " late to start on " << nd
                     << " to maintain dependencies\n";
            addMoveStartDate(d->getSecond(), nd);
            d->getSecond()->appendInfo(
                "Moved the start late to follow a predecessor");
            propagationList.insert(d->getSecond());
          }
        }

        // Keep routing sequence correct
        if (candidate->getOperationPlan()->getOwner() &&
            candidate->getOperationPlan()
                ->getOwner()
                ->getOperation()
                ->hasType<OperationRouting>()) {
          OperationPlan* tmp = candidate->getOperationPlan();
          OperationPlan* other = tmp->getNextSubOpplan();
          auto hard_posttime =
              static_cast<OperationRouting*>(tmp->getOwner()->getOperation())
                  ->getHardPostTime();
          auto posttime =
              hard_posttime ? tmp->getOperation()->getPostTime() : Duration(0L);
          while (other && (other->getApproved() || other->getProposed()) &&
                 tmp->getEnd() + posttime > other->getStart()) {
            if (getLogLevel() > 1)
              logger << indentlevel << "Moving operationplan " << other
                     << " late to start on " << (tmp->getEnd() + posttime)
                     << " to keep the sequence in the routing\n";
            addMoveStartDate(other, tmp->getEnd() + posttime);
            other->appendInfo("Moved the start late to follow a predecessor");
            if (getPropagate()) propagationList.insert(other);
            tmp = other;
            other = tmp->getNextSubOpplan();
            if (hard_posttime) posttime = tmp->getOperation()->getPostTime();
          };
        }

        // Keep synchronised deliveries together
        if (candidate->getOperationPlan()->getDemand() &&
            candidate->getOperationPlan()->getDemand()->getOwner() &&
            candidate->getOperationPlan()
                ->getDemand()
                ->getOwner()
                ->hasType<DemandGroup>() &&
            static_cast<DemandGroup*>(
                candidate->getOperationPlan()->getDemand()->getOwner())
                    ->getPolicy() != Demand::POLICY_INDEPENDENT) {
          for (auto dmd = candidate->getOperationPlan()
                              ->getDemand()
                              ->getOwner()
                              ->getMembers();
               dmd != Demand::end(); ++dmd) {
            for (auto dlvr : dmd->getDelivery()) {
              if (dlvr != candidate->getOperationPlan() &&
                  dlvr->getEnd() != candidate->getOperationPlan()->getEnd()) {
                addMoveEndDate(dlvr, candidate->getOperationPlan()->getEnd());
                dlvr->appendInfo("Moved to synchronize deliveries");
                if (getPropagate()) propagationList.insert(dlvr);
              }
            }
          }
        }
      } else {
        Date newopplandate =
            candidate->computeFlowToOperationDate(flpln_iter2->getDate());
        if (getLogLevel() > 1) {
          if (first_action) {
            first_action = false;
            logger << indentlevel << "Forward propagation of buffer " << buf;
            if (curOperationPlan)
              logger << " for operationplan " << curOperationPlan;
            if (curFlowPlan) logger << " on " << curFlowPlan->getDate();
            logger << "\n";
          }
          logger << indentlevel << "Moving operationplan "
                 << candidate->getOperationPlan() << " to end on "
                 << newopplandate << "\n";
        }
        addMoveEndDate(candidate->getOperationPlan(), newopplandate);
        candidate->getOperationPlan()->appendInfo(
            "Moved the end late to match material supply of " +
            candidate->getItem()->getName());

        // Propagate dependencies
        for (auto d : candidate->getOperationPlan()->getDependencies()) {
          if (candidate->getOperationPlan() != d->getFirst()) continue;
          Date nd = d->getFirst()->getEnd();
          if (d->getOperationDependency())
            nd += d->getOperationDependency()->getHardSafetyLeadtime();
          if (nd > d->getSecond()->getStart() &&
              (d->getSecond()->getApproved() ||
               d->getSecond()->getProposed())) {
            if (getLogLevel() > 1)
              logger << indentlevel << "Moving operationplan " << d->getSecond()
                     << " late to start on " << nd
                     << " to maintain dependencies\n";
            addMoveStartDate(d->getSecond(), nd);
            d->getSecond()->appendInfo(
                "Moved the start late to follow a predecessor");
            propagationList.insert(d->getSecond());
          }
        }

        // Keep routing sequence correct
        if (candidate->getOperationPlan()->getOwner() &&
            candidate->getOperationPlan()
                ->getOwner()
                ->getOperation()
                ->hasType<OperationRouting>()) {
          OperationPlan* tmp = candidate->getOperationPlan();
          OperationPlan* other = tmp->getNextSubOpplan();
          auto hard_posttime =
              static_cast<OperationRouting*>(tmp->getOwner()->getOperation())
                  ->getHardPostTime();
          auto posttime =
              hard_posttime ? tmp->getOperation()->getPostTime() : Duration(0L);
          while (other && (other->getApproved() || other->getProposed()) &&
                 tmp->getEnd() + posttime > other->getStart()) {
            if (getLogLevel() > 1)
              logger << indentlevel << "Moving operationplan " << other
                     << " late to start on " << (tmp->getEnd() + posttime)
                     << " to keep the sequence in the routing\n";
            addMoveStartDate(other, tmp->getEnd() + posttime);
            other->appendInfo("Moved the start late to follow a predecessor");
            if (getPropagate()) propagationList.insert(other);
            tmp = other;
            other = tmp->getNextSubOpplan();
            if (hard_posttime) posttime = tmp->getOperation()->getPostTime();
          };
        }

        // Keep synchronised deliveries together
        if (candidate->getOperationPlan()->getDemand() &&
            candidate->getOperationPlan()->getDemand()->getOwner() &&
            candidate->getOperationPlan()
                ->getDemand()
                ->getOwner()
                ->hasType<DemandGroup>() &&
            static_cast<DemandGroup*>(
                candidate->getOperationPlan()->getDemand()->getOwner())
                    ->getPolicy() != Demand::POLICY_INDEPENDENT) {
          for (auto dmd = candidate->getOperationPlan()
                              ->getDemand()
                              ->getOwner()
                              ->getMembers();
               dmd != Demand::end(); ++dmd) {
            for (auto dlvr : dmd->getDelivery()) {
              if (dlvr != candidate->getOperationPlan() &&
                  dlvr->getEnd() != candidate->getOperationPlan()->getEnd()) {
                addMoveEndDate(dlvr, candidate->getOperationPlan()->getEnd());
                dlvr->appendInfo("Moved to synchronize deliveries");
                if (getPropagate()) propagationList.insert(dlvr);
              }
            }
          }
        }
      }
      // Propagate the candidates postponement
      if (getPropagate()) propagationList.insert(candidate->getOperationPlan());
    }

    if (++iterationcount >= MAX_LOOP) {
      logger << indentlevel
             << "Error: Leaving buffer forward propagation loop on " << buf
             << " after " << MAX_LOOP << " iterations\n";
      break;
    }
  } while (!ok);

  // Propagate all changes
  while (!propagationList.empty()) {
    auto cd = *propagationList.begin();
    solve(cd, nullptr);
    propagationList.erase(propagationList.begin());
  }
  --indentlevel;
}

bool OperatorForward::isValidCandidate(OperationPlan* opplan) const {
  if (!getAcceptTabuCandidate()) {
    auto t = tabu.find(opplan);
    if (t != tabu.end()) return false;
  }
  return (opplan->getProposed() || opplan->getApproved()) &&
         opplan->getEnd() != Date::infiniteFuture;
};

bool OperatorForward::compareCandidates(OperationPlan* opplan1,
                                        OperationPlan* opplan2,
                                        Date refDate) const {
  // Selecting the current operation only as a last resort.
  if (opplan1 == curOperationPlan || opplan1 == opplan2)
    return true;
  else if (opplan2 == curOperationPlan)
    return false;
  auto t1 = tabu.find(opplan1);
  auto t2 = tabu.find(opplan2);

  // If there are dependency links between both operationplans, we should move
  // the successor first. Failing to do so can create vicious endless loops of
  // moves.
  // Check 1: walk downstream from opplan1
  stack<OperationPlan*> deps;
  deps.push(opplan1);
  while (!deps.empty()) {
    auto o = deps.top();
    deps.pop();
    if (o == opplan2) {
      // Force moving the second one
      return false;
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
      // Force moving the first one
      return true;
    }
    for (auto e : o->getDependencies()) {
      if (e->getSecond() == o) deps.push(e->getFirst());
    }
  }

  // First, easy criteria: tabu and start date
  if (t1 != tabu.end() && t2 == tabu.end())
    return true;
  else if (t1 == tabu.end() && t2 != tabu.end())
    return false;
  else if (opplan1->getStart() != opplan2->getStart())
    return opplan1->getStart() < opplan2->getStart();

  // Second, complex criteria: delay and setup score.
  // A low score indicates a good candidate.
  double score1;
  if (t1 != tabu.end())
    score1 = (opplan1 == curOperationPlan) ? t1->second + 1000 : t1->second;
  else if (opplan1 == curOperationPlan)
    score1 = static_cast<double>(opplan1->getDelay()) / 86400 + 1000;
  else
    score1 = static_cast<double>(opplan1->getDelay()) / 86400;

  double score2;
  if (t2 != tabu.end())
    score2 = (opplan2 == curOperationPlan) ? t2->second + 1000 : t2->second;
  else if (opplan2 == curOperationPlan)
    score2 = static_cast<double>(opplan2->getDelay()) / 86400 + 1000;
  else
    score2 = static_cast<double>(opplan2->getDelay()) / 86400;

  // Adjust the scores for the impact on the setup time
  // We only want to favor keeping in place operationplans that have require no
  // setup cost or setup duration. We don't want to interfere with about the
  // sequence, eg by favoring short setups.
  if (!SetupMatrix::empty() && refDate) {
    // opplan1->updateSetupTime();
    // opplan2->updateSetupTime();
    static PooledString emptystring;
    for (auto ldpln1 = opplan1->beginLoadPlans();
         ldpln1 != opplan1->endLoadPlans(); ++ldpln1) {
      if (ldpln1->getQuantity() >= 0.0 || !ldpln1->getLoad() ||
          ldpln1->getLoad()->getSetup().empty() ||
          !ldpln1->getResource()->getSetupMatrix())
        continue;
      auto setupbefore1 = ldpln1->getResource()->getSetupAt(refDate, opplan1);
      auto setuprule1 = ldpln1->getResource()->getSetupMatrix()->calculateSetup(
          setupbefore1 ? setupbefore1->getSetup() : emptystring,
          ldpln1->getLoad() ? ldpln1->getLoad()->getSetup()
                            : PooledString::emptystring,
          ldpln1->getResource());
      if (setuprule1) {
        // Bad choice if the changeover takes time or costs money
        if (setuprule1->getCost()) score1 -= 1000;
        if (setuprule1->getDuration() > Duration(0L)) score1 -= 500;
      } else
        // Oh dear, no changeover possible. Please move this candidate!
        score1 += 10000;
    }
    for (auto ldpln2 = opplan2->beginLoadPlans();
         ldpln2 != opplan1->endLoadPlans(); ++ldpln2) {
      if (ldpln2->getQuantity() >= 0.0 || !ldpln2->getLoad() ||
          ldpln2->getLoad()->getSetup().empty() ||
          !ldpln2->getResource()->getSetupMatrix())
        continue;
      auto setupbefore2 = ldpln2->getResource()->getSetupAt(refDate, opplan2);
      auto setuprule2 = ldpln2->getResource()->getSetupMatrix()->calculateSetup(
          setupbefore2 ? setupbefore2->getSetup() : emptystring,
          ldpln2->getLoad() ? ldpln2->getLoad()->getSetup()
                            : PooledString::emptystring,
          ldpln2->getResource());
      if (setuprule2) {
        // Bad choice if the changeover takes time or costs money
        if (setuprule2->getCost()) score2 -= 1000;
        if (setuprule2->getDuration() > Duration(0L)) score2 -= 500;
      } else
        // Oh dear, no changeover possible. Please move this candidate!
        score2 += 10000;
    }
  }

  // Final result:
  if (fabs(score1 - score2) > ROUNDING_ERROR)
    return score1 < score2;
  else
    return *opplan1 < *opplan2;
}

}  // namespace frepple
