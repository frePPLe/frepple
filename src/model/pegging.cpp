/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/buffer.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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

#define FREPPLE_CORE 
#include "frepple/model.h"

namespace frepple
{


PeggingIterator& PeggingIterator::operator++() 
{
  if (stack.top().fl->getQuantity() > ROUNDING_ERROR)
  {
    // CASE 1:
    // This is a flowplan producing in a buffer. Navigating downstream means
    // finding the flowplans consuming this produced material.
    //xxx @todo missing implementation
  }
  else if (stack.top().fl->getQuantity() < ROUNDING_ERROR)
  {
    // CASE 2:
    // This is a consuming flowplan. Navigating downstream means taking the 
    // producing flowplans of the owning operationplan(s).
    // @todo handle opplan hierarchies
    bool first = true;
    for (slist<FlowPlan*>::const_iterator i 
      = stack.top().fl->getOperationPlan()->getFlowPlans().begin();
      i != stack.top().fl->getOperationPlan()->getFlowPlans().end();
      ++i)
      if ((*i)->getQuantity()>0)
      {
        if (first)
        {
          stack.top().fl = *i;
          ++(stack.top().level);
          first = false;
        }
        else      
          stack.push(state(stack.top().cumqty, stack.top().level, *i));
      }
  }
  return *this;
}


PeggingIterator& PeggingIterator::operator--() 
{
  if (stack.top().fl->getQuantity() < ROUNDING_ERROR)
  {
    // CASE 3:
    // This is a flowplan consuming from a buffer. Navigating upstream means
    // finding the flowplans producing this consumed material.
    //xxx @todo missing implementation
  }
  else if (stack.top().fl->getQuantity() > ROUNDING_ERROR)
  {
    // CASE 4:
    // This is a producing flowplan. Navigating upstream means taking the 
    // consuming flowplans of the owning operationplan(s).
    // @todo handle opplan hierarchies
    bool first = true;
    for (slist<FlowPlan*>::const_iterator i 
      = stack.top().fl->getOperationPlan()->getFlowPlans().begin();
      i != stack.top().fl->getOperationPlan()->getFlowPlans().end();
      ++i)
      if ((*i)->getQuantity()<0)
      {
        if (first)
        {
          // First new flowplan: re-use existing stack top
          stack.top().fl = *i;
          ++(stack.top().level);
          first = false;
        }
        else      
          // Push a new element on the stack
          stack.push(state(stack.top().cumqty, stack.top().level, *i));
        // @todo also need to pop from the stack 
      }
  }
  return *this;
}

} // End namespace
