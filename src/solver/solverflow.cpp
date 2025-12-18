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

bool sortFlow(const Flow* lhs, const Flow* rhs) {
  return lhs->getPriority() < rhs->getPriority();
}

void SolverCreate::solve(const Flow* fl,
                         void* v)  // @todo implement search mode
{
  // Note: This method is only called for:
  // - consuming flows
  // - for the leading flow of an alternate group
  // - for the first transfer batch in a series
  // See SolverCreate::checkOperation
  SolverData* data = static_cast<SolverData*>(v);

  if (fl->hasAlternates()) {
    // CASE I: It is an alternate flow.
    // We ask each alternate flow in order of priority till we find a flow
    // that has a non-zero reply.

    // 1) collect a list of alternates
    list<const Flow*> thealternates;
    const Flow* x = fl->hasAlternates() ? fl : fl->getAlternate();
    for (auto i = fl->getOperation()->getFlows().begin();
         i != fl->getOperation()->getFlows().end(); ++i)
      if ((i->getAlternate() == x || &*i == x) &&
          i->getEffective().within(data->state->q_flowplan->getDate()))
        thealternates.push_front(&*i);

    // 2) Sort the list
    thealternates.sort(sortFlow);

    // 3) Control the planning mode
    bool originalPlanningMode = data->constrainedPlanning;
    data->constrainedPlanning = true;
    Flow* firstAlternate = nullptr;
    double firstQuantity = 0.0;

    // Remember the top constraint
    bool originalLogConstraints = data->logConstraints;

    // 4) Loop through the alternates till we find a non-zero reply
    Date min_next_date(Date::infiniteFuture);
    double ask_qty;
    FlowPlan* flplan = data->state->q_flowplan;
    for (auto i = thealternates.begin(); i != thealternates.end();) {
      const Flow* curflow = *i;
      data->state->q_flowplan = flplan;  // because q_flowplan can change

      // 4a) Switch to this flow
      if (data->state->q_flowplan->getFlow() != curflow)
        data->state->q_flowplan->setFlow(const_cast<Flow*>(curflow));

      // 4b) Call the Python user exit if there is one
      if (userexit_flow) {
        PythonData result = userexit_flow.call(
            data->state->q_flowplan, PythonData(data->constrainedPlanning));
        if (!result.getBool()) {
          // Return value is false, alternate rejected
          if (getLogLevel() > 1)
            logger << indentlevel << "User exit disallows consumption from '"
                   << (*i)->getBuffer() << "'" << endl;
          // Move to the next alternate
          if (++i != thealternates.end() && getLogLevel() > 1)
            logger << indentlevel << "Operation switches from '"
                   << curflow->getBuffer() << "' to alternate material '"
                   << (*i)->getBuffer() << "'" << endl;
          continue;
        }
      }

      // Remember the first alternate
      if (!firstAlternate) {
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
      data->state->q_qty_min = -curflow->getQuantityFixed() -
                               orig_q_qty_min * curflow->getQuantity();
      data->state->q_qty = ask_qty = -data->state->q_flowplan->getQuantity();
      data->state->q_date = data->state->q_flowplan->getDate();
      auto topcommand = data->getCommandManager()->setBookmark();
      data->state->q_flowplan->getBuffer()->solve(*this, data);

      // 4d) A positive reply: exit the loop
      if (data->state->a_qty > ROUNDING_ERROR) {
        // Update the opplan, which is required to (1) update the flowplans
        // and to (2) take care of lot sizing constraints of this operation.
        if (data->state->a_qty < ask_qty - ROUNDING_ERROR) {
          flplan->setQuantity(-data->state->a_qty, true);
          data->state->a_qty = -flplan->getQuantity();
        }
        if (data->state->a_qty > ROUNDING_ERROR) {
          data->constrainedPlanning = originalPlanningMode;
          data->logConstraints = originalLogConstraints;
          data->accept_partial_reply = true;
          data->state->q_qty_min = orig_q_qty_min;
          // Optimization for detection of broken supply paths is disabled when
          // we have alternate flows. Only when all alternates report a broken
          // path could we use it.
          // TODO Not implemented.
          data->broken_path = false;
          return;
        } else {
          // Got rounded down to zero, which is not good for the iteration on
          // the next flow. Restore to the original quantity.
          flplan->setQuantity(-ask_qty, false);
        }
      }

      // 4e) Undo the plan on the alternate
      data->getCommandManager()->rollback(topcommand);

      // 4f) Prepare for the next alternate
      if (data->state->a_date < min_next_date)
        min_next_date = data->state->a_date;
      if (++i != thealternates.end() && getLogLevel() > 1)
        logger << indentlevel << "Operation switches from '"
               << curflow->getBuffer() << "' to alternate material '"
               << (*i)->getBuffer() << "'" << endl;
    }

    // 5) No reply found, all alternates are infeasible
    if (!originalPlanningMode) {
      assert(firstAlternate);
      // Unconstrained plan: Plan on the primary alternate
      // Switch to this flow
      if (flplan->getFlow() != firstAlternate) flplan->setFlow(firstAlternate);
      // Message
      if (getLogLevel() > 1)
        logger << indentlevel
               << "Alternate flow plans unconstrained on alternate '"
               << firstAlternate->getBuffer() << "'" << endl;
      // Plan unconstrained
      data->constrainedPlanning = false;
      data->state->q_flowplan = flplan;  // because q_flowplan can change
      flplan->setQuantity(firstQuantity, true);
      data->state->q_qty = ask_qty = -flplan->getQuantity();
      data->state->q_date = flplan->getDate();
      firstAlternate->getBuffer()->solve(*this, data);
      data->state->a_qty = -flplan->getQuantity();
      // Restore original planning mode
      data->constrainedPlanning = originalPlanningMode;
    } else {
      // Constrained plan: Return 0
      data->state->a_date = min_next_date;
      data->state->a_qty = 0;
      if (getLogLevel() > 1)
        logger << indentlevel
               << "Alternate flow doesn't find supply on any alternate : "
               << data->state->a_qty << "  " << data->state->a_date << endl;
    }

    // Optimization for detection of broken supply paths is disabled when we
    // have alternate flows. Only when all alternates report a broken path could
    // we use it.
    // TODO Not implemented.
    data->broken_path = false;
  } else {
    // CASE II: Not an alternate flow.
    // In this case, this method is passing control on to the buffer.
    double orig_q_qty_min = data->state->q_qty_min;
    double orig_q_qty = -data->state->q_flowplan->getQuantity();
    data->state->q_qty = orig_q_qty;
    data->state->q_qty_min =
        -fl->getQuantityFixed() - data->state->q_qty_min * fl->getQuantity();
    data->state->q_date = data->state->q_flowplan->getDate();
    double extra_supply = 0.0;
    auto orig_q_date = data->state->q_date;

    if (data->state->q_qty != 0.0) {
      /*
      if (fl->getBuffer()->getItem()->hasType<ItemMTO>()) {
        auto free_specific = data->state->q_flowplan->getBuffer()->getOnHand(
            data->state->q_date, Date::infiniteFuture, true);
        if (free_specific < -ROUNDING_ERROR) {
          auto free_generic = fl->getBuffer()->getOnHand(
              data->state->q_date, Date::infiniteFuture, true);
          if (free_generic > ROUNDING_ERROR) {
            // Special case with all following conditions:
            // - MTO item
            // - MTO buffer doesn't have sufficient existing supply
            // - generic buffer has available existing supply
            if (free_generic > data->state->q_qty) {
              // Generic supply is sufficient
              if (getLogLevel() > 1)
                logger << indentlevel-- << "  Buffer '"
                       << data->state->q_flowplan->getBuffer()
                       << "' answers from generic MTO buffer '"
                       << fl->getBuffer() << "' : " << data->state->q_qty
                       << endl;
              data->state->q_flowplan->setBuffer(fl->getBuffer());
              data->state->a_date = data->state->q_date;
              data->state->a_qty = data->state->q_qty;
              data->state->q_qty_min = orig_q_qty_min;
              return;
            } else {
              // Partially use the generic supply
              if (getLogLevel() > 1)
                logger << indentlevel << "  Buffer '"
                       << data->state->q_flowplan->getBuffer()
                       << "' answers from generic MTO buffer '"
                       << fl->getBuffer() << "' : " << free_generic << endl;
              auto extraflpln = new FlowPlan(
                  data->state->q_flowplan->getOperationPlan(), fl,
                  data->state->q_flowplan->getDate(), -free_generic);
              extraflpln->setBuffer(fl->getBuffer());
              data->state->q_flowplan->setQuantityRaw(
                  data->state->q_flowplan->getQuantity() + free_generic);
              extra_supply = free_generic;
              data->state->q_qty -= free_generic;
              data->state->q_qty_min -= free_generic;
            }
          }
        }
      }
      */

      // Call the buffer solver
      auto thebuf = data->state->q_flowplan->getBuffer();
      thebuf->solve(*this, data);

      // MTO buffer using supply on generic buffer
      /*
      if (fl->getBuffer()->getItem()->hasType<ItemMTO>()) {
        if (extra_supply)
          // Merge extra supply quantity from the generic buffer
          data->state->a_qty += extra_supply;
        else if (!data->state->a_qty) {
          // Merge extra supply quantity from the generic buffer
          Date await_extra;
          for (auto extra = fl->getBuffer()->getFlowPlans().begin();
               extra != fl->getBuffer()->getFlowPlans().end(); ++extra) {
            if (!extra->isLastOnDate() || extra->getDate() <= orig_q_date)
              continue;
            if (extra->getDate() > orig_q_date + getAutoFence()) break;
            if (extra->getOnhand() > ROUNDING_ERROR)
              await_extra = extra->getDate();
          }
          if (await_extra && await_extra < data->state->a_date) {
            data->state->a_date = await_extra;
            if (getLogLevel() > 1)
              logger << indentlevel << "  Buffer '"
                     << data->state->q_flowplan->getBuffer()
                     << "' answers from generic MTO buffer '" << fl->getBuffer()
                     << "' : 0 " << await_extra << endl;
          }
        }
      }
      */

      if (data->state->a_date > fl->getEffective().getEnd()) {
        // The reply date must be less than the effectivity end date: after
        // that date the flow in question won't consume any material any more.
        if (getLogLevel() > 1 && data->state->a_qty < ROUNDING_ERROR)
          logger << indentlevel << "Buffer '" << thebuf
                 << "' answer date is adjusted to "
                 << fl->getEffective().getEnd()
                 << " because of a date effective flow" << endl;
        data->state->a_date = fl->getEffective().getEnd();
      }
    } else {
      // It's a zero quantity flowplan.
      // E.g. because it is not effective.
      data->state->a_date = data->state->q_date;
      data->state->a_qty = 0.0;
    }
    data->state->q_qty_min = orig_q_qty_min;
  }
}

}  // namespace frepple
