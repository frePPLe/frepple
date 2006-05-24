/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/solver/solverbuffer.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : johan_de_taeye@yahoo.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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
void MRPSolver::solve(Buffer* b, void* v)
{
  MRPSolverdata* Solver = (MRPSolverdata*)v;
  Date requested_date(Solver->q_date);
  float requested_qty(Solver->q_qty);
  bool tried_requested_date(false);
  // The Microsoft C++ compiler gives a warning on the following line of code. 
  // That's because for that compiler the comparison operator returns an int 
  // value, not the bool one would expect.
  bool isMinMaxBuffer( typeid(*b)==typeid(BufferMinMax) );

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=b->getLevel(); i; --i) clog << " ";
    clog << "  Buffer '" << b->getName() << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Make sure the new operationplans don't inherit an owner.
  // When an operation calls the solve method of suboperations, this field is
  // used to pass the information about the owner operationplan down. When
  // solving for buffers we must make sure NOT to pass owner information.
  // At the end of solving for a buffer we need to restore the original
  // settings...
  OperationPlan *prev_owner_opplan = Solver->curOwnerOpplan;
  Solver->curOwnerOpplan = NULL;

  // Evaluate the buffer profile and solve shortages by asking more material.
  // The loop goes from the requested date till the very end. Whenever the
  // event date changes, we evaluate if a shortage exists.
  Date currentDate;
  const TimeLine<FlowPlan>::Event *prev = NULL;
  double shortage(0.0f);
  Date extraSupplyDate(Date::infiniteFuture);
  Date extraInventoryDate(Date::infiniteFuture);
  float current_minimum(0.0f);
  float current_maximum(0.0f);
  for(Buffer::flowplanlist::const_iterator cur=b->getflowplans().begin(); 
    ; ++cur)
  {
    // Iterator has now changed to a new date or we have arrived at the end
    // If multiple flows are at the same moment in time, we are not interested
    // in the inventory changes. It gets interesting only when a certain
    // inventory level remains unchanged for a certain time.
    if ((cur == b->getflowplans().end() || cur->getDate()>currentDate) && prev)
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
        if (b->getProducingOperation() && theDate >= requested_date)
        {
          // Create supply
          Solver->curBuffer = b;
          Solver->q_qty = static_cast<float>(
          	isMinMaxBuffer ?
          		(current_maximum - shortage - theOnHand) :
          		-theDelta
          	);
          Solver->q_date = prev->getDate();

          // Check whether this date doesn't match with the requested date.
          // See a bit further why this is required.
          if (Solver->q_date == requested_date) tried_requested_date = true;

          // Note that the supply created with the next line changes the
          // onhand value at all later dates!
          b->getProducingOperation()->solve(*this,v);

          // Evaluate the reply date. The variable extraSupplyDate will store
          // the date when the producing operation tells us it can get extra
          // supply.
          if (Solver->a_date < extraSupplyDate)
            extraSupplyDate = Solver->a_date;
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
      else if (theDelta > ROUNDING_ERROR)
        // There is excess material at this date (coming from planned/frozen
        // material arrivals, surplus material created by lotsized operations,
        // etc...)
        if (theDate > requested_date
            && extraInventoryDate == Date::infiniteFuture)
          extraInventoryDate = theDate;
    }

    // We have reached the end of the flowplans. Breaking out of the loop
    // needs to be done here because in the next statements we are accessing
    // *cur, which isn't valid at the end of the list
    if (cur == b->getflowplans().end()) break;

    // The minimum or the maximum have changed
    // Note that these limits can be updated only after the processing of the
    // date change in the statement above. Otherwise the code above would
    // already use the new value before the intended date.
    if (cur->getType() == 3) current_minimum = cur->getMin();
    if (cur->getType() == 4) current_maximum = cur->getMax();

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
  //             |                                  |
  //             +------                            +---+
  //                                                    |
  //      -------x------ 0                      0 --y---x-----
  //                                                    |
  //                                                    +-----
  // The first loop only checks for supply at times x and later. If it is not
  // feasible, we now check for supply at time y. It will create some extra
  // inventory, but at least the demand is met.
  // @todo The buffer solver could move backward in time from x till time y,
  // and try multiple dates.
  if (shortage>ROUNDING_ERROR
      && b->getProducingOperation() && !tried_requested_date)
  {
    // Create supply at the requested date
    Solver->curBuffer = b;
    Solver->q_qty = static_cast<float>(shortage);
    Solver->q_date = requested_date;
    // Note that the supply created with the next line changes the onhand value
    // at all later dates!
    // Note that asking at the requested date doesn't keep the material on 
    // stock to a minimum.
    b->getProducingOperation()->solve(*this,v);
    // Evaluate the reply
    if (Solver->a_date < extraSupplyDate) extraSupplyDate = Solver->a_date;
    shortage -= Solver->a_qty;
  }

  // Final evaluation of the replenishment
  if (shortage < ROUNDING_ERROR
      || !Solver->getSolver()->isMaterialConstrained())
  {
    // Enough inventory or supply available, or not material constrained
    // In case of a plan that is not material constrained, the buffer tries to
    // solve for shortages as good as possible. Only in the end we 'lie' about
    // the result to the calling function. Material shortages will then remain
    // in the buffer.
    Solver->a_qty = requested_qty;
    Solver->a_date = Date::infiniteFuture;
  }
  else
  {
    // We are short on supply
    Solver->a_qty = static_cast<float>(requested_qty - shortage);
    if (Solver->a_qty < 0) Solver->a_qty = 0.0;
    Solver->a_date = (extraInventoryDate < extraSupplyDate) ? 
      extraInventoryDate : 
      extraSupplyDate;
  }

  // Restore the owning operationplan.
  Solver->curOwnerOpplan = prev_owner_opplan;

  // Reply date can never be earlier than the requested date
  assert( Solver->a_date >= Solver->q_date );

  // Reply quantity must be greater than 0
  assert( Solver->a_qty >= 0 );

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=b->getLevel(); i; --i) clog << " ";
    clog << "  Buffer '" << b->getName() << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


void MRPSolver::solve(Flow* fl, void* v)
{
  MRPSolverdata* data = static_cast<MRPSolverdata*>(v);
  data->q_qty = - data->q_flowplan->getQuantity();
  data->q_date = data->q_flowplan->getDate();
  fl->getBuffer()->solve(*this,data);
}


void MRPSolver::solve(BufferInfinite* b, void* v)
{
  MRPSolverdata* Solver = (MRPSolverdata*)v;

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=b->getLevel(); i; --i) clog << " ";
    clog << "  Buffer '" << b << "' is asked: "
    << Solver->q_qty << "  " << Solver->q_date << endl;
  }

  // Reply whatever is requested, regardless of date, quantity or supply.
  // The demand is not propagated upstream either.
  Solver->a_qty = Solver->q_qty;
  Solver->a_date = Solver->q_date;

  // Message
  if (Solver->getSolver()->getVerbose())
  {
    for (int i=b->getLevel(); i; --i) clog << " ";
    clog << "  Buffer '" << b << "' answers: "
    << Solver->a_qty << "  " << Solver->a_date << endl;
  }
}


}
