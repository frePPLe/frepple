/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/flow_plan.cpp $
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


FlowPlan::FlowPlan (OperationPlan * opplan, const Flow * f)
    : TimeLine<FlowPlan>::EventChangeOnhand(
        f->getQuantity() * opplan->getQuantity())
{
  fl = const_cast<Flow*>(f);
  oper = opplan;
  oper->flowplans.push_front(this);   // @todo need a better data structure
  f->getBuffer()->flowplans.insert(this);

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  f->getBuffer()->setChanged();
  f->getOperation()->setChanged();
}


void FlowPlan::update()
{
  // Update the timeline data structure
  fl->getBuffer()->flowplans.setQuantity(
    this,
    oper->getQuantity() * fl->getQuantity()
  );

  // Mark the operation and buffer as having changed. This will trigger the
  // recomputation of their problems
  fl->getBuffer()->setChanged();
  fl->getOperation()->setChanged();

  // Check validity
  assert( check() );
}


bool FlowPlan::check()
{
  // Quantity must match with the operationplan
  if (fabs(oper->getQuantity() * fl->getQuantity() - getQuantity()) 
    > ROUNDING_ERROR)
    return false;
  else
	return true;
}


}
