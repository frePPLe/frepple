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
#include "frepple/solver.h"

namespace frepple
{

bool sortFlow(const Flow* lhs, const Flow* rhs)
{
  return lhs->getPriority() < rhs->getPriority();
}


void SolverCreate::solve(const Flow* fl, void* v)  // @todo implement search mode
{
  // Note: This method is only called for:
  // - consuming flows
  // - for the leading flow of an alternate group
  // - for the first transfer batch in a series
  // See SolverCreate::checkOperation
  SolverData* data = static_cast<SolverData*>(v);

  if (fl->hasAlternates())
  {
    // CASE I: It is an alternate flow.
    // We ask each alternate flow in order of priority till we find a flow
    // that has a non-zero reply.

    // 1) collect a list of alternates
    list<const Flow*> thealternates;
    const Flow *x = fl->hasAlternates() ? fl : fl->getAlternate();
    for (Operation::flowlist::const_iterator i = fl->getOperation()->getFlows().begin();
        i != fl->getOperation()->getFlows().end(); ++i)
      if ((i->getAlternate() == x || &*i == x)
          && i->getEffective().within(data->state->q_flowplan->getDate()))
        thealternates.push_front(&*i);

    // 2) Sort the list
    thealternates.sort(sortFlow);

    // 3) Control the planning mode
    bool originalPlanningMode = data->constrainedPlanning;
    data->constrainedPlanning = true;
    Flow *firstAlternate = nullptr;
    double firstQuantity = 0.0;

    // Remember the top constraint
    bool originalLogConstraints = data->logConstraints;
    //Problem* topConstraint = data->planningDemand->getConstraints().top();

    // 4) Loop through the alternates till we find a non-zero reply
    Date min_next_date(Date::infiniteFuture);
    double ask_qty;
    FlowPlan *flplan = data->state->q_flowplan;
    for (auto i = thealternates.begin(); i != thealternates.end();)
    {
      const Flow *curflow = *i;
      data->state->q_flowplan = flplan; // because q_flowplan can change

      // 4a) Switch to this flow
      if (data->state->q_flowplan->getFlow() != curflow)
        data->state->q_flowplan->setFlow(const_cast<Flow*>(curflow));

      // 4b) Call the Python user exit if there is one
      if (userexit_flow)
      {
        PythonData result = userexit_flow.call(data->state->q_flowplan, PythonData(data->constrainedPlanning));
        if (!result.getBool())
        {
          // Return value is false, alternate rejected
          if (data->getSolver()->getLogLevel()>1)
            logger << indent(curflow->getOperation()->getLevel())
                << "   User exit disallows consumption from '"
                << (*i)->getBuffer()->getName() << "'" << endl;
          // Move to the next alternate
          if (++i != thealternates.end() && data->getSolver()->getLogLevel()>1)
            logger << indent(curflow->getOperation()->getLevel()) << "   Alternate flow switches from '"
                << curflow->getBuffer()->getName() << "' to '"
                << (*i)->getBuffer()->getName() << "'" << endl;
          continue;
        }
      }

      // Remember the first alternate
      if (!firstAlternate)
      {
        firstAlternate = const_cast<Flow*>(*i);
        firstQuantity = data->state->q_flowplan->getQuantity();
      }

      // Constraint tracking
      if (*i != firstAlternate)
        // Only enabled on first alternate
        data->logConstraints = false;
      else
        // Keep track of constraints, if enabled
        data->logConstraints = originalLogConstraints;

      // 4c) Ask the buffer
      double orig_q_qty_min = data->state->q_qty_min;
      data->state->q_qty_min = curflow->getQuantityFixed() + orig_q_qty_min * curflow->getQuantity();
      data->state->q_qty = ask_qty = - data->state->q_flowplan->getQuantity();
      data->state->q_date = data->state->q_flowplan->getDate();
      CommandManager::Bookmark* topcommand = data->getCommandManager()->setBookmark();
      curflow->getBuffer()->solve(*this,data);

      // 4d) A positive reply: exit the loop
      if (data->state->a_qty > ROUNDING_ERROR)
      {
        // Update the opplan, which is required to (1) update the flowplans
        // and to (2) take care of lot sizing constraints of this operation.
        if (data->state->a_qty < ask_qty - ROUNDING_ERROR)
        {
          flplan->setQuantity(-data->state->a_qty, true);
          data->state->a_qty = -flplan->getQuantity();
        }
        if (data->state->a_qty > ROUNDING_ERROR)
        {
          data->constrainedPlanning = originalPlanningMode;
          data->logConstraints = originalLogConstraints;
          data->state->q_qty_min = orig_q_qty_min;
          return;
        }
      }

      // 4e) Undo the plan on the alternate
      data->getCommandManager()->rollback(topcommand);

      // 4f) Prepare for the next alternate
      if (data->state->a_date < min_next_date)
        min_next_date = data->state->a_date;
      if (++i != thealternates.end() && data->getSolver()->getLogLevel()>1)
        logger << indent(curflow->getOperation()->getLevel()) << "   Alternate flow switches from '"
            << curflow->getBuffer()->getName() << "' to '"
            << (*i)->getBuffer()->getName() << "'" << endl;
    }

    // 5) No reply found, all alternates are infeasible
    if (!originalPlanningMode)
    {
      assert(firstAlternate);
      // Unconstrained plan: Plan on the primary alternate
      // Switch to this flow
      if (flplan->getFlow() != firstAlternate)
        flplan->setFlow(firstAlternate);
      // Message
      if (data->getSolver()->getLogLevel()>1)
        logger << indent(fl->getOperation()->getLevel())
            << "   Alternate flow plans unconstrained on alternate '"
            << firstAlternate->getBuffer()->getName() << "'" << endl;
      // Plan unconstrained
      data->constrainedPlanning = false;
      data->state->q_flowplan = flplan; // because q_flowplan can change
      flplan->setQuantity(firstQuantity, true);
      data->state->q_qty = ask_qty = - flplan->getQuantity();
      data->state->q_date = flplan->getDate();
      firstAlternate->getBuffer()->solve(*this,data);
      data->state->a_qty = -flplan->getQuantity();
      // Restore original planning mode
      data->constrainedPlanning = originalPlanningMode;
    }
    else
    {
      // Constrained plan: Return 0
      data->state->a_date = min_next_date;
      data->state->a_qty = 0;
      if (data->getSolver()->getLogLevel()>1)
        logger << indent(fl->getOperation()->getLevel()) <<
            "   Alternate flow doesn't find supply on any alternate : "
            << data->state->a_qty << "  " << data->state->a_date << endl;
    }
  }
  else
  {
    // CASE II: Not an alternate flow.
    // In this case, this method is passing control on to the buffer.
    double orig_q_qty_min = data->state->q_qty_min;
    data->state->q_qty = - data->state->q_flowplan->getQuantity();
    data->state->q_qty_min = - fl->getQuantityFixed() - data->state->q_qty_min * fl->getQuantity();
    data->state->q_date = data->state->q_flowplan->getDate();
    if (data->state->q_qty != 0.0)
    {
      fl->getBuffer()->solve(*this,data);
      if (data->state->a_date > fl->getEffective().getEnd())
      {
        // The reply date must be less than the effectivity end date: after
        // that date the flow in question won't consume any material any more.
        if (data->getSolver()->getLogLevel()>1
            && data->state->a_qty < ROUNDING_ERROR)
          logger << indent(fl->getBuffer()->getLevel()) << "  Buffer '"
              << fl->getBuffer()->getName() << "' answer date is adjusted to "
              << fl->getEffective().getEnd()
              << " because of a date effective flow" << endl;
        data->state->a_date = fl->getEffective().getEnd();
      }
    }
    else
    {
      // It's a zero quantity flowplan.
      // E.g. because it is not effective.
      data->state->a_date = data->state->q_date;
      data->state->a_qty = 0.0;
    }
    data->state->q_qty_min = orig_q_qty_min;
  }
}


}
