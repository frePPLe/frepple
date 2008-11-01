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
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/


#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{


DECLARE_EXPORT LoadPlan::LoadPlan (OperationPlan *o, const Load *r)
{
  assert(o);
  ld = const_cast<Load*>(r);
  oper = o;
  start_or_end = START;
  nextLoadPlan = o->firstloadplan;
  o->firstloadplan = this;
  r->getResource()->loadplans.insert(
    this,
    ld->getLoadplanQuantity(this),
    ld->getLoadplanDate(this)
    );

  // Create a loadplan to mark the end of the operationplan.
  new LoadPlan(o, r, this);

  // Mark the operation and resource as being changed. This will trigger
  // the recomputation of their problems
  r->getResource()->setChanged();
  r->getOperation()->setChanged();
}


DECLARE_EXPORT LoadPlan::LoadPlan (OperationPlan *o, const Load *r, LoadPlan *lp)
{
  ld = const_cast<Load*>(r);
  oper = o;
  start_or_end = END;
  nextLoadPlan = o->firstloadplan;
  o->firstloadplan = this;

  r->getResource()->loadplans.insert(
    this,
    ld->getLoadplanQuantity(this),
    ld->getLoadplanDate(this)
    );
}


DECLARE_EXPORT LoadPlan* LoadPlan::getOtherLoadPlan() const
{
  for (LoadPlan *i = oper->firstloadplan; i; i = i->nextLoadPlan)
    if (i->ld == ld && i != this) return i;
  throw LogicException("No matching loadplan found");
}


DECLARE_EXPORT void LoadPlan::update()
{
  // Update the timeline data structure
  ld->getResource()->getLoadPlans().update(
    this,
    ld->getLoadplanQuantity(this),
    ld->getLoadplanDate(this)
    );

  // Mark the operation and resource as being changed. This will trigger
  // the recomputation of their problems
  ld->getResource()->setChanged();
  ld->getOperation()->setChanged();
}


int PythonLoadPlan::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("loadplan");
  x.setDoc("frePPLe loadplan");
  x.supportgetattro();
  return x.typeReady(m);
}


PyObject* PythonLoadPlan::getattro(const Attribute& attr)
{
  if (!fl) return Py_None;
  if (attr.isA(Tags::tag_operationplan))
    return PythonObject(fl->getOperationPlan());
  if (attr.isA(Tags::tag_quantity))
    return PythonObject(fl->getQuantity());
  if (attr.isA(Tags::tag_startdate))
    return PythonObject(fl->getDate());
  if (attr.isA(Tags::tag_enddate))
    return PythonObject(fl->getOtherLoadPlan()->getDate());
  if (attr.isA(Tags::tag_resource))
    return PythonObject(fl->getLoad()->getResource());
  return NULL;
}


int PythonLoadPlanIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonLoadPlanIterator>::getType();
  x.setName("loadplanIterator");
  x.setDoc("frePPLe iterator for loadplan");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonLoadPlanIterator::iternext()
{
  // Skip zero quantity loadplans and load ends
  while (i != res->getLoadPlans().end() && i->getQuantity()<=0.0)
    ++i;
  if (i == res->getLoadPlans().end()) return NULL;

  // Return result
  return new PythonLoadPlan(const_cast<LoadPlan*>(dynamic_cast<const LoadPlan*>(&*(i++))));
}

} // end namespace
