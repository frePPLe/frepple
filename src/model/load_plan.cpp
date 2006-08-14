/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/load_plan.cpp $
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


LoadPlan::LoadPlan (OperationPlan *o, const Load *r)
    : TimeLine<LoadPlan>::EventChangeOnhand(r->getUsageFactor())
{
  ld = const_cast<Load*>(r);
  oper = o;
  start_or_end = START;
  o->LoadPlans.push_front(this);    // @todo need a better data structure
  r->getResource()->loadplans.insert(this);
  new LoadPlan(o, r, this);

  // Mark the operation and resource as being changed. This will trigger
  // the recomputation of their problems
  r->getResource()->setChanged();
  r->getOperation()->setChanged();
}


LoadPlan::LoadPlan (OperationPlan *o, const Load *r, LoadPlan *lp)
    : TimeLine<LoadPlan>::EventChangeOnhand(- r->getUsageFactor())
{
  ld = const_cast<Load*>(r);
  oper = o;
  start_or_end = END;
  o->LoadPlans.push_front(this);  // @todo need a better data structure
  r->getResource()->loadplans.insert(this);
}


void LoadPlan::update()
{
  // Update the timeline
  ld->getResource()->getLoadPlans().setQuantity(
    this,
    start_or_end==START ? ld->getUsageFactor() : - ld->getUsageFactor()
  );

  // Mark the operation and resource as being changed. This will trigger
  // the recomputation of their problems
  ld->getResource()->setChanged();
  ld->getOperation()->setChanged();
}


bool LoadPlan::check()
{
  // 1. Quantity must match with the operationplan
  if (fabs((start_or_end==START ? ld->getUsageFactor() : - ld->getUsageFactor())
           - getQuantity()) > ROUNDING_ERROR)
    return false;
  // 2. Date must match with the operationplan
  if(start_or_end==START)
    return getDate() == oper->getDates().getStart();
  else
    return getDate() == oper->getDates().getEnd();
}

}
