/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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
#include "frepple/solver.h"

namespace frepple
{


/** @todo The flow quantity is handled at the wrong place. It needs to be
  * handled by the operation, since flows can exist on multiple suboperations
  * with different quantities. The buffer solve can't handle this, because
  * it only calls the solve() for the producing operation...
  * Are there some situations where the operation solver doesn't know enough
  * on the buffer behavior???
  */
DECLARE_EXPORT void SolverMRP::solve(const Buffer* b, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);
  Date requested_date(data->state->q_date);
  double requested_qty(data->state->q_qty);
  bool tried_requested_date(false);

  // Call the user exit
  if (userexit_buffer) userexit_buffer.call(b, PythonObject(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(b->getLevel()) << "  Buffer '" << b->getName()
        << "' is asked: " << data->state->q_qty << "  " << data->state->q_date << endl;

  // Store the last command in the list, in order to undo the following
  // commands if required.
  CommandManager::Bookmark* topcommand = data->setBookmark();
  OperationPlan *prev_owner_opplan = data->state->curOwnerOpplan;

  // Evaluate the buffer profile and solve shortages by asking more material.
  // The loop goes from the requested date till the very end. Whenever the
  // event date changes, we evaluate if a shortage exists.
  Date currentDate;
  const TimeLine<FlowPlan>::Event *prev = NULL;
  double shortage(0.0);
  Date extraSupplyDate(Date::infiniteFuture);
  Date extraInventoryDate(Date::infiniteFuture);
  double cumproduced = b->getFlowPlans().rbegin()->getCumulativeProduced();
  double current_minimum(0.0);
  double unconfirmed_supply(0.0);
  for (Buffer::flowplanlist::const_iterator cur=b->getFlowPlans().begin();
      ; ++cur)
  {
    const FlowPlan* fplan = dynamic_cast<const FlowPlan*>(&*cur);
    if (fplan && !fplan->getOperationPlan()->getIdentifier()
        && fplan->getQuantity()>0
        && fplan->getOperationPlan()->getOperation() != b->getProducingOperation())
      unconfirmed_supply += fplan->getQuantity();

    // Iterator has now changed to a new date or we have arrived at the end.
    // If multiple flows are at the same moment in time, we are not interested
    // in the inventory changes. It gets interesting only when a certain
    // inventory level remains unchanged for a certain time.
    if ((cur == b->getFlowPlans().end() || cur->getDate()>currentDate) && prev)
    {
      // Some variables
      Date theDate = prev->getDate();
      double theOnHand = prev->getOnhand();
      double theDelta = theOnHand - current_minimum + shortage;

      // Evaluate the situation at the last flowplan before the date change.
      // Is there a shortage at that date?
      if (theDelta < -ROUNDING_ERROR)
      {
        // Can we get extra supply to solve the problem, or part of it?
        // If the shortage already starts before the requested date, it
        // was not created by the newly added flowplan, but existed before.
        // We don't consider this as a shortage for the current flowplan,
        // and we want our flowplan to try to repair the previous problems
        // if it can...
        bool loop = true;
        while (b->getProducingOperation() && theDate >= requested_date && loop)
        {
          // Create supply
          data->state->curBuffer = const_cast<Buffer*>(b);
          data->state->q_qty = -theDelta;
          data->state->q_date = prev->getDate();

          // Check whether this date doesn't match with the requested date.
          // See a bit further why this is required.
          if (data->state->q_date == requested_date) tried_requested_date = true;

          // Make sure the new operationplans don't inherit an owner.
          // When an operation calls the solve method of suboperations, this field is
          // used to pass the information about the owner operationplan down. When
          // solving for buffers we must make sure NOT to pass owner information.
          // At the end of solving for a buffer we need to restore the original
          // settings...
          data->state->curOwnerOpplan = NULL;

          // Note that the supply created with the next line changes the
          // onhand value at all later dates!
          b->getProducingOperation()->solve(*this,v);

          // Evaluate the reply date. The variable extraSupplyDate will store
          // the date when the producing operation tells us it can get extra
          // supply.
          if (data->state->a_date < extraSupplyDate
              && data->state->a_date > requested_date)
            extraSupplyDate = data->state->a_date;

          // If we got some extra supply, we retry to get some more supply.
          // Only when no extra material is obtained, we give up.
          if (data->state->a_qty > ROUNDING_ERROR
              && data->state->a_qty < -theDelta - ROUNDING_ERROR)
            theDelta += data->state->a_qty;
          else
            loop = false;
        }

        // Not enough supply was received to repair the complete problem
        if (prev->getOnhand() + shortage < -ROUNDING_ERROR)
        {
          // Keep track of the shorted quantity.
          // Only consider shortages later than the requested date.
          if (theDate >= requested_date)
            shortage = -prev->getOnhand();

          // Reset the date from which excess material is in the buffer. This
          // excess material can be used to compute the date when the buffer
          // can be asked again for additional supply.
          extraInventoryDate = Date::infiniteFuture;
        }
      }
      else if (theDelta > unconfirmed_supply + ROUNDING_ERROR)
        // There is excess material at this date (coming from planned/frozen
        // material arrivals, surplus material created by lotsized operations,
        // etc...)
        // The unconfirmed_supply element is required to exclude any of the
        // excess inventory we may have caused ourselves. Such situations are
        // possible when there are loops in the supply chain.
        if (theDate > requested_date
            && extraInventoryDate == Date::infiniteFuture)
          extraInventoryDate = theDate;
    }

    // We have reached the end of the flowplans. Breaking out of the loop
    // needs to be done here because in the next statements we are accessing
    // *cur, which isn't valid at the end of the list
    if (cur == b->getFlowPlans().end()) break;

    // The minimum or the maximum have changed
    // Note that these limits can be updated only after the processing of the
    // date change in the statement above. Otherwise the code above would
    // already use the new value before the intended date.
    if (cur->getType() == 3) current_minimum = cur->getMin();

    // Update the pointer to the previous flowplan.
    prev = &*cur;
    currentDate = cur->getDate();
  }

  // Note: the variable extraInventoryDate now stores the date from which
  // excess material is available in the buffer. The excess
  // We don't need to care how much material is lying there.

  // Check for supply at the requested date
  // Isn't this included in the normal loop? In some cases it is indeed, but
  // sometimes it isn't because in the normal loop there may still have been
  // onhand available and the shortage only shows at a later date than the
  // requested date.
  // E.g. Initial situation:              After extra consumer at time y:
  //      -------+                                --+
  //             |                                  |
  //             +------                            +---+
  //                                                    |
  //    0 -------y------                        0 --y---x-----
  //                                                    |
  //                                                    +-----
  // The first loop only checks for supply at times x and later. If it is not
  // feasible, we now check for supply at time y. It will create some extra
  // inventory, but at least the demand is met.
  // @todo The buffer solver could move backward in time from x till time y,
  // and try multiple dates. This would minimize the excess inventory created.
  while (shortage > ROUNDING_ERROR
      && b->getProducingOperation() && !tried_requested_date)
  {
    // Create supply at the requested date
    data->state->curBuffer = const_cast<Buffer*>(b);
    data->state->q_qty = shortage;
    data->state->q_date = requested_date;
    // Make sure the new operationplans don't inherit an owner.
    // When an operation calls the solve method of suboperations, this field is
    // used to pass the information about the owner operationplan down. When
    // solving for buffers we must make sure NOT to pass owner information.
    // At the end of solving for a buffer we need to restore the original
    // settings...
    data->state->curOwnerOpplan = NULL;
    // Note that the supply created with the next line changes the onhand value
    // at all later dates!
    // Note that asking at the requested date doesn't keep the material on
    // stock to a minimum.
    b->getProducingOperation()->solve(*this,v);
    // Evaluate the reply
    if (data->state->a_date < extraSupplyDate
        && data->state->a_date > requested_date)
      extraSupplyDate = data->state->a_date;
    if (data->state->a_qty > ROUNDING_ERROR)
      shortage -= data->state->a_qty;
    else
      tried_requested_date = true;
  }

  // Final evaluation of the replenishment
  if (data->constrainedPlanning && data->getSolver()->isConstrained())
  {
    // Use the constrained planning result
    data->state->a_qty = requested_qty - shortage;
    if (data->state->a_qty < ROUNDING_ERROR)
    {
      data->rollback(topcommand);
      data->state->a_qty = 0.0;
    }
    data->state->a_date = (extraInventoryDate < extraSupplyDate) ?
        extraInventoryDate :
        extraSupplyDate;
    // Monitor as a constraint if there is no producing operation.
    // Note that if there is a producing operation the constraint is flagged
    // on the operation instead of on this buffer.
    if (!b->getProducingOperation() && data->logConstraints && shortage > ROUNDING_ERROR)
      data->planningDemand->getConstraints().push(ProblemMaterialShortage::metadata,
          b, requested_date, Date::infiniteFuture, shortage);
  }
  else
  {
    // Enough inventory or supply available, or not material constrained.
    // In case of a plan that is not material constrained, the buffer tries to
    // solve for shortages as good as possible. Only in the end we 'lie' about
    // the result to the calling function. Material shortages will then remain
    // in the buffer.
    data->state->a_qty = requested_qty;
    data->state->a_date = Date::infiniteFuture;
  }

  // Restore the owning operationplan.
  data->state->curOwnerOpplan = prev_owner_opplan;

  // Reply quantity must be greater than 0
  assert( data->state->a_qty >= 0 );

  // Increment the cost
  // Only the quantity consumed directly from the buffer is counted.
  // The cost of the material supply taken from producing operations is
  // computed seperately and not considered here.
  if (b->getItem() && data->state->a_qty > 0)
  {
    cumproduced = b->getFlowPlans().rbegin()->getCumulativeProduced() - cumproduced;
    if (data->state->a_qty > cumproduced)
      data->state->a_cost += (data->state->a_qty - cumproduced) * b->getItem()->getPrice();
  }

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(b->getLevel()) << "  Buffer '" << b->getName()
        << "' answers: " << data->state->a_qty << "  " << data->state->a_date << "  "
        << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


DECLARE_EXPORT void SolverMRP::solve(const BufferInfinite* b, void* v)
{
  SolverMRPdata* data = static_cast<SolverMRPdata*>(v);

  // Call the user exit
  if (userexit_buffer) userexit_buffer.call(b, PythonObject(data->constrainedPlanning));

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(b->getLevel()) << "  Infinite buffer '" << b << "' is asked: "
        << data->state->q_qty << "  " << data->state->q_date << endl;

  // Reply whatever is requested, regardless of date, quantity or supply.
  // The demand is not propagated upstream either.
  data->state->a_qty = data->state->q_qty;
  data->state->a_date = data->state->q_date;
  if (b->getItem())
    data->state->a_cost += data->state->q_qty * b->getItem()->getPrice();

  // Message
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(b->getLevel()) << "  Infinite buffer '" << b << "' answers: "
        << data->state->a_qty << "  " << data->state->a_date << "  "
        << data->state->a_cost << "  " << data->state->a_penalty << endl;
}


}
