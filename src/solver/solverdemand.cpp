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

#define FREPPLE_CORE
#include "frepple/solver.h"

namespace frepple {

bool compare_location(const pair<Location*, double>& a,
                      const pair<Location*, double>& b) {
  return a.second > b.second;
}

void SolverCreate::solve(const Demand* salesorder, void* v) {
  typedef list<pair<Location*, double> > SortedLocation;
  // Set a bookmark at the current command
  SolverData* data = static_cast<SolverData*>(v);
  auto topcommand = data->getCommandManager()->setBookmark();
  auto topstate = data->state;

  try {
    // Call the user exit
    if (userexit_demand)
      userexit_demand.call(salesorder, PythonData(data->constrainedPlanning));
    short loglevel = getLogLevel();

    bool isGroup = salesorder->hasType<DemandGroup>();
    auto policy = isGroup
                      ? static_cast<const DemandGroup*>(salesorder)->getPolicy()
                      : Demand::POLICY_INDEPENDENT;
    if (policy == Demand::POLICY_INDEPENDENT) isGroup = false;

    // Message
    if (loglevel > 0) {
      logger << "Planning demand '" << salesorder
             << "': " << salesorder->getPriority() << ", "
             << salesorder->getDue();
      if (isGroup) {
        logger << ", group";
        indentlevel.level = 1;
      } else {
        logger << ", " << salesorder->getQuantity();
        indentlevel.level = 0;
      }
      if (!data->constrainedPlanning || !isConstrained())
        logger << " in unconstrained mode";
      logger << endl;
    }

    // Collect sales order lines in the group
    vector<Demand*> salesorderlines;
    if (isGroup) {
      for (auto m = salesorder->getMembers(); m != Demand::end(); ++m)
        if (m->getQuantity() - m->getPlannedQuantity() > ROUNDING_ERROR &&
            m->getDue() < Date::infiniteFuture &&
            (m->getStatus() == Demand::STATUS_OPEN ||
             m->getStatus() == Demand::STATUS_QUOTE)) {
          salesorderlines.push_back(&*m);
        }
    } else if (salesorder->getQuantity() - salesorder->getPlannedQuantity() >
                   ROUNDING_ERROR &&
               salesorder->getDue() < Date::infiniteFuture)
      salesorderlines.push_back(const_cast<Demand*>(salesorder));
    if (salesorderlines.empty()) {
      if (loglevel > 0) logger << "  Nothing to be planned." << endl;
      return;
    }

    // Unattach previous delivery operationplans, if required.
    if (getErasePreviousFirst()) {
      for (auto l : salesorderlines) {
        // Locked operationplans will NOT be deleted, and a part of the demand
        // can still remain planned.
        l->deleteOperationPlans(false, data->getCommandManager());

        // Empty constraint list
        l->getConstraints().clear();
      }
    }

    auto delivery_date = salesorder->getDue();
    delivery_date -= getAdministrativeLeadTime();
    Date next_delivery_date = delivery_date;
    Demand* group_buster = nullptr;
    do {
      bool group_ok = true;

      for (auto l : salesorderlines) {
        if (!group_ok)
          // Another sales order line already failed.
          // We can stop here and retry at another date.
          break;

        // Message
        data->push();
        if (isGroup && loglevel > 0) {
          logger << indentlevel << "Planning demand '" << l
                 << "': " << l->getPriority() << ", " << l->getDue() << ", "
                 << l->getQuantity();
          if (!data->constrainedPlanning || !isConstrained())
            logger << " in unconstrained mode";
          logger << endl;
        }

        // Track constraints or not
        data->logConstraints = (getPlanType() == 1);

        // Determine quantity and date for the planning loop
        Date plan_date = delivery_date;
        double plan_qty = l->getQuantity() - l->getPlannedQuantity();
        if (plan_qty < l->getMinShipment()) plan_qty = l->getMinShipment();
        auto minshipment = (policy == Demand::POLICY_ALLTOGETHER)
                               ? plan_qty
                               : l->getMinShipment();

        // Temporary values to store the 'best-reply' so far
        double best_q_qty = 0.0, best_a_qty = 0.0;
        Date best_q_date;

        // Check delivery operation
        Operation* deliveryoper = l->getDeliveryOperation();
        {
          string problemtext =
              string("Demand '") + l->getName() + "' has no delivery operation";
          Problem::iterator j = Problem::begin(const_cast<Demand*>(l), false);
          while (j != Problem::end()) {
            if (j->hasType<ProblemInvalidData>() &&
                j->getDescription() == problemtext)
              break;
            ++j;
          }
          if (!deliveryoper) {
            // Create a problem
            if (j == Problem::end())
              new ProblemInvalidData(const_cast<Demand*>(l), problemtext,
                                     "demand", l->getDue(), l->getDue(),
                                     l->getQuantity());
            // Abort planning of this demand
            throw DataException("Demand '" + l->getName() +
                                "' can't be planned");
          } else
            // Remove problem that may already exist
            delete &*j;
        }

        // Plan over different locations if global_purchase flag is set
        // Store the original location in a variable
        Location* originalLocation = l->getLocation();
        SortedLocation sortedLocation;
        bool globalPurchase = l->getItem() ? l->getItem()->getBoolProperty(
                                                 "global_purchase", false) &&
                                                 data->constrainedPlanning
                                           : false;
        if (globalPurchase &&
            plan_date >= l->getItem()->findEarliestPurchaseOrder(l->getBatch()))
          // Global purchasing is only active until the receipt of the first
          // proposed purchase order of this item. Beyond that date the initial
          // excess is burnt off / redistributed, and every location buys for
          // its local needs again.
          globalPurchase = false;
        if (globalPurchase) {
          // iterate over locations and store them using the excess as a
          // priority excess being onhand minus safety stock
          Item* item = l->getItem();
          Item::bufferIterator iter(item);

          while (Buffer* buffer = iter.next()) {
            // Make sure we don't pick original location.
            // Also skip buffers that have a different batch.
            if (buffer->getLocation() == originalLocation ||
                buffer->getBatch() != l->getBatch())
              continue;

            // We need to calculate the excess
            Calendar* ss_calendar = buffer->getMinimumCalendar();
            double excess = 0;
            if (ss_calendar) {
              CalendarBucket* calendarBucket =
                  ss_calendar->findBucket(data->state->q_date, true);
              if (calendarBucket)
                excess =
                    buffer->getOnHand(l->getDue()) - calendarBucket->getValue();
            } else
              excess = buffer->getOnHand(l->getDue()) - buffer->getMinimum();
            sortedLocation.push_front(
                pair<Location*, double>(buffer->getLocation(), excess));
          }
          // Let's now order the list of location
          sortedLocation.sort(compare_location);
        }

        // Main planning loop for a sales order line
        ++indentlevel;
        do {    // Loop over global-purchasing locations
          do {  // Multiple plan iterations
            // Message
            if (loglevel > 0)
              logger << indentlevel << "Demand '" << l << "' asks: " << plan_qty
                     << "  " << plan_date << endl;

            // Store the last command in the list, in order to undo the
            // following commands if required.
            auto loopcommand = data->getCommandManager()->setBookmark();

            // Plan the demand by asking the delivery operation to plan
            double q_qty = plan_qty;
            data->broken_path = false;
            data->state->curBuffer = nullptr;
            data->state->q_qty = plan_qty;
            data->state->q_qty_min = minshipment;
            data->state->forceAccept = false;
            data->state->q_date = plan_date;
            data->constraints = &(const_cast<Demand*>(l)->getConstraints());
            data->state->curDemand = const_cast<Demand*>(l);
            data->state->curOwnerOpplan = nullptr;
            data->state->curBatch = l->getBatch();
            data->state->dependency = nullptr;
            data->state->blockedOpplan = nullptr;
            data->coordination_run = false;
            data->accept_partial_reply = false;
            data->recent_buffers.clear();
            data->dependency_list.clear();
            deliveryoper->solve(*this, v);
            Date next_date = data->state->a_date;
            bool broken_path = data->broken_path;

            if (data->state->a_qty < ROUNDING_ERROR && plan_qty > minshipment &&
                minshipment > 0 && policy != Demand::POLICY_ALLTOGETHER) {
              bool originalLogConstraints = data->logConstraints;
              data->logConstraints = false;
              try {
                // The full asked quantity is not possible.
                // Try with the minimum shipment quantity.
                if (loglevel > 1)
                  logger << indentlevel << "Demand '" << l
                         << "' tries planning minimum quantity " << minshipment
                         << endl;
                data->getCommandManager()->rollback(loopcommand);
                data->state->curBuffer = nullptr;
                data->state->q_qty = minshipment;
                data->state->q_date = plan_date;
                data->state->curDemand = const_cast<Demand*>(l);
                data->state->curBatch = l->getBatch();
                data->state->dependency = nullptr;
                data->state->blockedOpplan = nullptr;
                data->recent_buffers.clear();
                data->dependency_list.clear();
                deliveryoper->solve(*this, v);
                if (data->state->a_date < next_date)
                  next_date = data->state->a_date;
                if (data->state->a_qty > ROUNDING_ERROR) {
                  // The minimum shipment quantity is feasible.
                  // Now try iteratively different quantities to find the best
                  // we can do.
                  double min_qty = minshipment;
                  double max_qty = plan_qty;
                  double delta = fabs(max_qty - min_qty);
                  while (delta > getIterationAccuracy() * l->getQuantity() &&
                         delta > getIterationThreshold()) {
                    // Note: we're kind of assuming that the demand is an
                    // integer value here.
                    double new_qty = floor((min_qty + max_qty) / 2);
                    if (new_qty == min_qty) {
                      // Required to avoid an infinite loop on the same value...
                      new_qty += 1;
                      if (new_qty > max_qty) break;
                    }
                    if (loglevel > 0)
                      logger << indentlevel << "Demand '" << l
                             << "' tries planning a different quantity "
                             << new_qty << endl;
                    data->getCommandManager()->rollback(loopcommand);
                    data->state->curBuffer = nullptr;
                    data->state->q_qty = new_qty;
                    data->state->q_date = plan_date;
                    data->state->curDemand = const_cast<Demand*>(l);
                    data->state->curBatch = l->getBatch();
                    data->state->dependency = nullptr;
                    data->state->blockedOpplan = nullptr;
                    data->recent_buffers.clear();
                    data->dependency_list.clear();
                    deliveryoper->solve(*this, v);
                    if (data->state->a_date < next_date)
                      next_date = data->state->a_date;
                    if (data->state->a_qty > ROUNDING_ERROR)
                      // Too small: new min
                      min_qty = new_qty;
                    else
                      // Too big: new max
                      max_qty = new_qty;
                    delta = fabs(max_qty - min_qty);
                  }
                  q_qty = min_qty;  // q_qty is the biggest Q quantity giving a
                                    // positive reply
                  if (data->state->a_qty <= ROUNDING_ERROR) {
                    if (loglevel > 0)
                      logger << indentlevel << "Demand '" << l
                             << "' restores plan for quantity " << min_qty
                             << endl;
                    // Restore the last feasible plan
                    data->getCommandManager()->rollback(loopcommand);
                    data->state->curBuffer = nullptr;
                    data->state->q_qty = min_qty;
                    data->state->q_date = plan_date;
                    data->state->curDemand = const_cast<Demand*>(l);
                    data->state->curBatch = l->getBatch();
                    data->state->dependency = nullptr;
                    data->state->blockedOpplan = nullptr;
                    data->recent_buffers.clear();
                    data->dependency_list.clear();
                    deliveryoper->solve(*this, v);
                  }
                }
              } catch (...) {
                data->logConstraints = originalLogConstraints;
                throw;
              }
              data->logConstraints = originalLogConstraints;
            }

            // Message
            if (loglevel > 0) {
              logger << indentlevel << "Demand '" << l
                     << "' gets answer: " << data->state->a_qty;
              if (!data->state->a_qty) logger << "  " << next_date;
              logger << "  " << data->state->a_cost << "  "
                     << data->state->a_penalty << endl;
            }

            // Update the date to plan in the next loop
            Date copy_plan_date = plan_date;

            // Compare the planned quantity with the minimum allowed shipment
            // quantity We don't accept the answer in case:
            // 1) Nothing is planned
            // 2) The planned quantity is less than the minimum shipment
            //    quantity
            // 3) The remaining quantity after accepting this answer is less
            //    than the minimum quantity.
            if (data->state->a_qty < ROUNDING_ERROR ||
                (data->state->a_qty + ROUNDING_ERROR < minshipment &&
                 !data->state->forceAccept) ||
                (plan_qty - data->state->a_qty < minshipment &&
                 fabs(plan_qty - data->state->a_qty) > ROUNDING_ERROR &&
                 !data->state->forceAccept)) {
              if (plan_qty - data->state->a_qty < minshipment &&
                  data->state->a_qty + ROUNDING_ERROR >= minshipment &&
                  !data->state->forceAccept &&
                  data->state->a_qty > best_a_qty) {
                // The remaining quantity after accepting this answer is less
                // than the minimum quantity. Therefore, we delay accepting it
                // now, but still keep track of this best offer.
                best_a_qty = data->state->a_qty;
                best_q_qty = q_qty;
                best_q_date = plan_date;
              }

              // Set the ask date for the next pass through the loop
              if (data->state->a_qty > ROUNDING_ERROR &&
                  plan_qty - data->state->a_qty < minshipment &&
                  plan_qty - data->state->a_qty > ROUNDING_ERROR) {
                // Check whether the reply is based purely on onhand or not
                if (broken_path) {
                  // Not more supply will ever be found here!
                  plan_date = Date::infiniteFuture;
                } else if (hasOperationPlans(data->getCommandManager()) ||
                           next_date <= copy_plan_date + getLazyDelay()) {
                  // Oops, we didn't get a proper answer we can use for the next
                  // loop. Print a warning and simply a bit later.
                  plan_date = copy_plan_date + getLazyDelay();
                  if (loglevel > 1)
                    logger << indentlevel << "Demand '" << l
                           << "': Easy retry on " << plan_date
                           << " rather than " << next_date << endl;
                } else
                  // We can trust the next date returned by the search if the
                  // shipment quantity was purely based on some onhand.
                  plan_date = next_date;
              } else if (next_date <= copy_plan_date ||
                         data->state->a_qty > ROUNDING_ERROR ||
                         (next_date == Date::infiniteFuture &&
                          data->state->a_qty > ROUNDING_ERROR)) {
                // Oops, we didn't get a proper answer we can use for the next
                // loop. Print a warning and simply try a bit later.
                plan_date = copy_plan_date + getLazyDelay();
                if (loglevel > 1)
                  logger << indentlevel << "Demand '" << l
                         << "': Easy retry on " << plan_date << " rather than "
                         << next_date << endl;
              } else if (getMinimumDelay()) {
                Date tmp = copy_plan_date + getMinimumDelay();
                if (tmp > next_date) {
                  // Assures that the next planning round advances for at least
                  // the minimum acceptable delay.
                  if (loglevel > 0)
                    logger << indentlevel << "Demand '" << l
                           << "': Minimum retry on " << tmp << " rather than "
                           << next_date << endl;
                  plan_date = tmp;
                } else
                  // Use the next-date answer from the solver
                  plan_date = next_date;
              } else
                // Use the next-date answer from the solver
                plan_date = next_date;

              // Tracking for synching demands
              if (isGroup && policy == Demand::POLICY_ALLTOGETHER) {
                group_ok = false;
                group_buster = l;
                next_delivery_date = plan_date;
              }

              // Delete operationplans - Undo all changes
              data->getCommandManager()->rollback(loopcommand);
            } else {
              // Accepting this answer
              if (data->state->a_qty + ROUNDING_ERROR < q_qty) {
                // The demand was only partially planned. We need to do a new
                // 'coordinated' planning run.

                // Delete operationplans created in the 'testing round'
                data->getCommandManager()->rollback(loopcommand);

                // Create the correct operationplans
                if (loglevel >= 2)
                  logger << indentlevel << "Demand '" << l
                         << "' plans coordination." << endl;
                setLogLevel(0);
                double tmpresult = 0;
                try {
                  for (double remainder = data->state->a_qty;
                       remainder > ROUNDING_ERROR;
                       remainder -= data->state->a_qty) {
                    data->state->q_qty = remainder;
                    data->state->q_date = copy_plan_date;
                    data->state->curDemand = const_cast<Demand*>(l);
                    data->state->curBatch = l->getBatch();
                    data->state->curBuffer = nullptr;
                    data->state->dependency = nullptr;
                    data->state->blockedOpplan = nullptr;
                    data->coordination_run = true;
                    data->accept_partial_reply = false;
                    data->recent_buffers.clear();
                    data->dependency_list.clear();
                    deliveryoper->solve(*this, v);
                    if (data->state->a_qty < ROUNDING_ERROR) {
                      logger << indentlevel << "Warning: Demand '" << l
                             << "': Failing coordination" << endl;
                      break;
                    }
                    tmpresult += data->state->a_qty;
                  }
                } catch (...) {
                  setLogLevel(loglevel);
                  throw;
                }
                setLogLevel(loglevel);
                data->state->a_qty = tmpresult;
                if (tmpresult == 0) break;
              }

              // Register the new operationplans. We need to make sure that the
              // correct execute method is called!
              if (getAutocommit() && policy != Demand::POLICY_ALLTOGETHER) {
                scanExcess(data->getCommandManager());
                data->getCommandManager()->commit();
              }

              // Update the quantity to plan in the next loop
              plan_qty -= data->state->a_qty;
              best_a_qty = 0.0;  // Reset 'best-answer' remember
            }

          }
          // Repeat while there is still a quantity left to plan and we aren't
          // exceeding the maximum delivery delay.
          while (plan_qty > ROUNDING_ERROR && group_ok &&
                 ((getPlanType() != 2 &&
                   plan_date < l->getDue() + l->getMaxLateness()) ||
                  (getPlanType() == 2 && !data->constrainedPlanning &&
                   plan_date < l->getDue() + l->getMaxLateness()) ||
                  (getPlanType() == 2 && data->constrainedPlanning &&
                   plan_date == delivery_date)));

          if (l->getLatestDelivery() &&
              l->getLatestDelivery()->getEnd() <= l->getDue() &&
              l->getPlannedQuantity() >= l->getQuantity() - ROUNDING_ERROR)
            const_cast<Demand*>(l)->getConstraints().clear();

          if (globalPurchase) {
            if (sortedLocation.empty() ||
                (l->getPlannedQuantity() + ROUNDING_ERROR >= l->getQuantity()))
              break;

            if (getLogLevel() > 1)
              logger << indentlevel << "Changing demand location for " << l
                     << " from " << l->getLocation() << " to "
                     << sortedLocation.front().first << endl;

            // Prepare for planning on the next location
            const_cast<Demand*>(l)->setLocationNoRecalc(
                sortedLocation.front().first);
            deliveryoper = l->getDeliveryOperation();
            plan_date = delivery_date;

            // Remove first element of the sorted location
            sortedLocation.pop_front();
          }
        } while (globalPurchase);

        if (globalPurchase) {
          // Switch demand back to original location
          const_cast<Demand*>(l)->setLocationNoRecalc(originalLocation);
          l->getDeliveryOperation();
        }

        // Accept the best possible answer.
        // We may have skipped it in the previous loop, awaiting a still better
        // answer
        if (best_a_qty > 0.0 && data->constrainedPlanning &&
            policy != Demand::POLICY_ALLTOGETHER) {
          if (loglevel >= 2)
            logger << indentlevel << "Demand '" << l
                   << "' accepts a best answer." << endl;
          setLogLevel(0);
          try {
            for (double remainder = best_q_qty;
                 remainder > ROUNDING_ERROR && remainder > minshipment;
                 remainder -= data->state->a_qty) {
              data->state->q_qty = remainder;
              data->state->q_date = best_q_date;
              data->state->curDemand = const_cast<Demand*>(l);
              data->state->curBatch = l->getBatch();
              data->state->curBuffer = nullptr;
              data->state->dependency = nullptr;
              data->state->blockedOpplan = nullptr;
              data->coordination_run = true;
              data->accept_partial_reply = false;
              data->recent_buffers.clear();
              data->dependency_list.clear();
              deliveryoper->solve(*this, v);
              if (data->state->a_qty < ROUNDING_ERROR) {
                logger << indentlevel << "Warning: Demand '" << l
                       << "': Failing accepting best answer" << endl;
                break;
              }
            }
            if (getAutocommit() && policy != Demand::POLICY_ALLTOGETHER) {
              scanExcess(data->getCommandManager());
              data->getCommandManager()->commit();
            }
          } catch (...) {
            setLogLevel(loglevel);
            throw;
          }
          setLogLevel(loglevel);
        }

        indentlevel--;

        // Reset the state stack to the position we found it at.
        while (data->state > topstate) data->pop();
      }

      if (policy == Demand::POLICY_ALLTOGETHER) {
        if (group_ok) {
          // All lines planned in full at this date
          if (getAutocommit()) {
            scanExcess(data->getCommandManager());
            data->getCommandManager()->commit();
          }
          if (group_buster) {
            for (auto l : salesorderlines)
              if (l != group_buster) {
                l->getConstraints().clear();
                l->getConstraints().push(
                    new ProblemSyncDemand(l, group_buster));
              }
          }
          break;
        } else if (next_delivery_date == Date::infiniteFuture) {
          // Give it up
          if (loglevel > 1)
            logger << indentlevel << "Warning: Demand group '" << salesorder
                   << "' can't be planned." << endl;
          break;
        } else {
          // Repeat at a new date
          delivery_date = next_delivery_date;
          data->getCommandManager()->rollback(topcommand);
        }
      } else if (policy == Demand::POLICY_INRATIO) {
        break;  // TODO
      } else if (policy != Demand::POLICY_INDEPENDENT)
        throw LogicException("Unknown demand policy!");
    } while (isGroup);
  } catch (...) {
    // Clean up if any exception happened during the planning of the demand
    while (data->state > topstate) data->pop();
    data->getCommandManager()->rollback(topcommand);
    throw;
  }
}

void SolverCreate::scanExcess(CommandManager* mgr) {
  for (auto i = mgr->begin(); i != mgr->end(); ++i)
    if (i->isActive()) scanExcess(&*i);
}

void SolverCreate::scanExcess(CommandList* l) {
  // Loop over all newly created operationplans found in the command stack
  for (auto cmd = l->begin(); cmd != l->end(); ++cmd) {
    switch (cmd->getType()) {
      case 1:
        // Recurse deeper into command lists
        scanExcess(static_cast<CommandList*>(&*cmd));
        break;
      case 5:
        // Detect excess operationplans and undo them
        auto createcmd = static_cast<CommandCreateOperationPlan*>(&*cmd);
        if (createcmd->getOperationPlan()) {
          if (createcmd->getOperationPlan()->getQuantity() -
                  createcmd->getOperationPlan()->isExcess() <
              ROUNDING_ERROR) {
            if (getLogLevel() > 1)
              logger << "Denying creation of redundant operationplan "
                     << createcmd->getOperationPlan()->getOperation() << "  "
                     << createcmd->getOperationPlan()->getDates() << "  "
                     << createcmd->getOperationPlan()->getQuantity() << endl;
            createcmd->rollback();
          } else if (!createcmd->getOperationPlan()
                          ->getOperation()
                          ->hasType<OperationItemSupplier>()) {
            // Check if any later operationplans have become excess
            auto o = createcmd->getOperationPlan()
                         ->getOperation()
                         ->getOperationPlans();
            while (o != OperationPlan::end()) {
              if (createcmd->getOperationPlan()->getEnd() < o->getEnd() &&
                  o->getProposed() &&
                  (o->getQuantity() - o->isExcess() < ROUNDING_ERROR)) {
                auto tmp = &*o;
                ++o;
                if (getLogLevel() > 1)
                  logger << "Removing previously created redundant "
                            "operationplan "
                         << tmp << endl;
                delete tmp;
              } else
                ++o;
            }
          }
        }
        break;
    }
  }
}

bool SolverCreate::hasOperationPlans(CommandManager* mgr) {
  for (auto i = mgr->begin(); i != mgr->end(); ++i) {
    if (i->isActive()) {
      if (hasOperationPlans(&*i)) return true;
    }
  }
  return false;
}

bool SolverCreate::hasOperationPlans(CommandList* l) {
  // Loop over all newly created operationplans found in the command stack
  for (auto cmd = l->begin(); cmd != l->end(); ++cmd) {
    switch (cmd->getType()) {
      case 1:
        // Recurse deeper into command lists
        if (hasOperationPlans(static_cast<CommandList*>(&*cmd))) return true;
        break;
      case 5:
        // Command creating an operationplan
        auto opplan =
            static_cast<CommandCreateOperationPlan*>(&*cmd)->getOperationPlan();
        if (opplan->getQuantity() > 0.0 && !opplan->getDemand() &&
            !opplan->getOperation()->hasType<OperationItemDistribution>())
          // Return ok when we find an operation that is producing material
          // (and not only consuming or moving inventory)
          return true;
        break;
    }
  }
  return false;
}

}  // namespace frepple
