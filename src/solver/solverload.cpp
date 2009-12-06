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
  for (Operation::loadlist::const_iterator i = l->getOperation()->getLoads().begin();
    i != l->getOperation()->getLoads().end(); ++i)
    if ((i->getAlternate() == x || &*i == x)
      && i->getEffective().within(data->state->q_loadplan->getDate()))
      thealternates.push_front(&*i);

  // 2) Sort the list
  thealternates.sort(sortLoad);

  // 3) Loop through the alternates till we find a non-zero reply
  Date min_next_date(Date::infiniteFuture);
  LoadPlan *lplan = data->state->q_loadplan;

  for (list<const Load*>::const_iterator i = thealternates.begin();
    i != thealternates.end();)
  {
    const Load *curload = *i;
    data->state->q_loadplan = lplan; // because q_loadplan can change!
    // 3a) Switch to this load
    if (data->state->q_loadplan->getLoad() != curload)
    {
      data->state->q_loadplan->setLoad(curload);
      data->state->q_qty = data->state->q_loadplan->getQuantity();
      data->state->q_date = data->state->q_loadplan->getDate();
    }
    // 3b) Ask the resource
    Command* topcommand = data->getLastCommand();
    curload->getResource()->solve(*this,data);
    // 3c) A positive reply: exit the loop
    if (data->state->a_qty > ROUNDING_ERROR) return;
    // 3d) Undo the plan on the alternate
    data->undo(topcommand);
    // 3e) Prepare for the next alternate
    if (data->state->a_date < min_next_date)
      min_next_date = data->state->a_date;
    if (++i != thealternates.end() && data->getSolver()->getLogLevel()>1)
      logger << indent(curload->getOperation()->getLevel()) << "   Alternate load switches from '"
            << curload->getResource()->getName() << "' to '"
            << (*i)->getResource()->getName() << "'" << endl;
  }

  // 4) No alternate gave a good result
  data->state->a_date = min_next_date;
  data->state->a_qty = 0;
  if (data->state->q_operationplan->getQuantity() != 0.0)
    // In case of a zero reply, we resize the operationplan to 0 right away.
    // This is required to make sure that the buffer inventory profile also
    // respects this answer.
    data->state->q_operationplan->setQuantity(0.0);
  if (data->getSolver()->getLogLevel()>1)
    logger << indent(data->state->q_loadplan->getLoad()->getOperation()->getLevel()) <<
      "   Alternate load doesn't find supply on any alternate : "
      << data->state->a_qty << "  " << data->state->a_date << endl;
}


}
