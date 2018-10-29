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
#include "frepple/model.h"

namespace frepple
{

const MetaCategory* LoadPlan::metadata;


int LoadPlan::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<LoadPlan>("loadplan", "loadplans", reader);
  registerFields<LoadPlan>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python type
  PythonType& x = FreppleCategory<LoadPlan>::getPythonType();
  x.setName("loadplan");
  x.setDoc("frePPLe loadplan");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


LoadPlan::LoadPlan(OperationPlan *o, const Load *r)
{
  // Initialize the Python type
  initType(metadata);

  assert(o);
  ld = const_cast<Load*>(r);
  oper = o;
  start_or_end = START;

  // Update the resource field
  res = r->findPreferredResource(o->getSetupEnd());

  // Add to the operationplan
  nextLoadPlan = nullptr;
  if (o->firstloadplan)
  {
    // Append to the end
    LoadPlan *c = o->firstloadplan;
    while (c->nextLoadPlan) c = c->nextLoadPlan;
    c->nextLoadPlan = this;
  }
  else
    // First in the list
    o->firstloadplan = this;

  // Insert in the resource timeline
  getResource()->loadplans.insert(
    this,
    ld->getLoadplanQuantity(this),
    ld->getLoadplanDate(this)
  );

  // For continuous resources, create a loadplan to mark
  // the end of the operationplan.
  if (getResource()->getType() != *ResourceBuckets::metadata)
    new LoadPlan(o, r, this);

  // Mark the operation and resource as being changed. This will trigger
  // the recomputation of their problems
  getResource()->setChanged();
  r->getOperation()->setChanged();
}


LoadPlan::LoadPlan(OperationPlan *o, const Load *r, LoadPlan *lp)
{
  ld = const_cast<Load*>(r);
  oper = o;
  start_or_end = END;

  // Update the resource field
  res = lp->getResource();

  // Add to the operationplan
  nextLoadPlan = nullptr;
  if (o->firstloadplan)
  {
    // Append to the end
    LoadPlan *c = o->firstloadplan;
    while (c->nextLoadPlan) c = c->nextLoadPlan;
    c->nextLoadPlan = this;
  }
  else
    // First in the list
    o->firstloadplan = this;

  // Insert in the resource timeline
  getResource()->loadplans.insert(
    this,
    ld->getLoadplanQuantity(this),
    ld->getLoadplanDate(this)
  );

  // Initialize the Python type
  initType(metadata);
}


void LoadPlan::setResource(Resource* newres, bool check, bool use_start)
{
  // Nothing to do
  if (res == newres)
    return;

  // Validate the argument
  if (!newres)
    throw DataException("Can't switch to nullptr resource");
  if (check)
  {
    // New resource must be a subresource of the load's resource.
    bool ok = false;
    for (const Resource* i = newres; i && !ok; i = i->getOwner())
      if (i == getLoad()->getResource()) ok = true;
    if (!ok)
      throw DataException("Resource isn't matching the resource specified on the load");

    // New resource must have the required skill
    if (getLoad()->getSkill())
    {
      ok = false;
      Resource::skilllist::const_iterator s = newres->getSkills();
      while(ResourceSkill *rs = s.next())
        if (rs->getSkill() == getLoad()->getSkill())
        {
          ok = true;
          break;
        }
      if (!ok)
        throw DataException("Resource misses the skill specified on the load");
    }
  }

  // Mark entities as changed
  Resource* oldRes = res;
  if (oper)
    oper->getOperation()->setChanged();
  if (res && res!=newres)
    res->setChanged();
  newres->setChanged();

  // Change this loadplan and its brother
  for (LoadPlan *ldplan = getOtherLoadPlan(); true; )
  {
    // Remove from the old resource, if there is one
    if (res)
    {
      res->loadplans.erase(ldplan);
      res->setChanged();
    }

    // Insert in the new resource.
    // This code assumes the date and quantity of the loadplan don't change
    // when a new resource is assigned.
    ldplan->res = newres;
    newres->loadplans.insert(
      ldplan,
      ld->getLoadplanQuantity(ldplan),
      ld->getLoadplanDate(ldplan)
    );

    // Repeat for the brother loadplan or exit
    if (ldplan != this)
      ldplan = this;
    else
      break;
  }

  // Clear the setup event
  oper->setStartEndAndQuantity(oper->getSetupEnd(), oper->getEnd(), oper->getQuantity());
  oper->clearSetupEvent();

  // The new resource may have a different availability calendar,
  // and we need to make sure to respect it.
  if (use_start)
    oper->setStart(oper->getStart());
  else
    oper->setEnd(oper->getEnd());

  // Update the setup time on the old resource
  if (oldRes)
    oldRes->updateSetupTime();

  // Change the resource
  newres->setChanged();
}


LoadPlan* LoadPlan::getOtherLoadPlan() const
{
  for (LoadPlan *i = oper->firstloadplan; i; i = i->nextLoadPlan)
    if (i->ld == ld && i != this && i->getEventType() == 1)
      return i;
  throw LogicException("No matching loadplan found");
}


string LoadPlan::getStatus() const
{
  if (flags & STATUS_CONFIRMED)
    return "confirmed";
  else if (flags & STATUS_APPROVED)
    return "approved";
  else
    return "proposed";
}


void LoadPlan::setStatus(const string& s)
{
  if (getOperationPlan()->getProposed() && s == "confirmed")
    throw DataException("OperationPlanResource locked while OperationPlan is not");
  if (s == "confirmed")
    flags |= STATUS_CONFIRMED;
  else if (s == "proposed")
    flags &= ~STATUS_CONFIRMED;
  else
    throw DataException("invalid operationplanresource status:" + s);
}


void LoadPlan::update()
{
  // Update the timeline data structure
  getResource()->getLoadPlans().update(
    this,
    ld->getLoadplanQuantity(this),
    ld->getLoadplanDate(this)
  );

  // Mark the operation and resource as being changed. This will trigger
  // the recomputation of their problems
  getResource()->setChanged();
  ld->getOperation()->setChanged();
}


SetupEvent* LoadPlan::getSetup(bool myself_only) const
{
  auto opplan = getOperationPlan();
  if (!getResource()->getSetupMatrix() || !opplan)
    return nullptr;
  if (myself_only)
    return opplan->getSetupEvent();
  Resource::loadplanlist::const_iterator tmp;
  if (opplan->getSetupEvent())
    // Setup event being used
    tmp = opplan->getSetupEvent();
  else if (isStart())
    // Start loadplan
    tmp = this;
  else
    // End loadplan
    tmp = getOtherLoadPlan();
  while (tmp != getResource()->getLoadPlans().end())
  {
    if (tmp->getEventType() == 5 && (
      tmp->getDate() < opplan->getSetupEnd()
      || (tmp->getOperationPlan() && tmp->getDate() == opplan->getSetupEnd() && *(tmp->getOperationPlan()) < *opplan)
      ))
       return const_cast<SetupEvent*>(static_cast<const SetupEvent*>(&*tmp));
    --tmp;
  }
  return nullptr;
}


LoadPlan::~LoadPlan()
{
  getResource()->setChanged();
  getResource()->loadplans.erase(this);
}


void LoadPlan::setLoad(Load* newld)
{
  // No change
  if (newld == ld) return;

  // Verify the data
  if (!newld) throw DataException("Can't switch to nullptr load");
  if (ld && ld->getOperation() != newld->getOperation())
    throw DataException("Only switching to a load on the same operation is allowed");

  // Update the load and resource fields
  LoadPlan* o = getOtherLoadPlan();
  if (o) o->ld = newld;
  ld = newld;
  setResource(newld->getResource());
}


Object* LoadPlan::reader(
  const MetaClass* cat, const DataValueDict& in, CommandManager* mgr
)
{
  // Pick up the operationplan attribute. An error is reported if it's missing.
  const DataValue* opplanElement = in.get(Tags::operationplan);
  if (!opplanElement)
    throw DataException("Missing operationplan field");
  Object* opplanobject = opplanElement->getObject();
  if (!opplanobject || opplanobject->getType() != *OperationPlan::metadata)
    throw DataException("Invalid operationplan field");
  OperationPlan* opplan = static_cast<OperationPlan*>(opplanobject);

  // Pick up the resource.
  const DataValue* resourceElement = in.get(Tags::resource);
  if (!resourceElement)
    throw DataException("Resource must be provided");
  Object* resourceobject = resourceElement->getObject();
  if (!resourceobject || resourceobject->getType().category != Resource::metadata)
    throw DataException("Invalid item field");
  Resource* res = static_cast<Resource*>(resourceobject);

  // Find the load for this resource on the operationplan.
  // If multiple exist, we pick up the first one.
  // If none is found, we throw a data error.
  auto flplniter = opplan->getLoadPlans();
  LoadPlan* flpln;
  while ((flpln = flplniter.next()))
  {
    if (flpln->getResource() == res)
      return flpln;
  }
  return nullptr;
}


int LoadPlanIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<LoadPlanIterator>::getPythonType();
  x.setName("loadplanIterator");
  x.setDoc("frePPLe iterator for loadplan");
  x.supportiter();
  return x.typeReady();
}


PyObject* LoadPlanIterator::iternext()
{
  LoadPlan* ld;
  if (resource_or_opplan)
  {
    // Skip zero quantity loadplans
    while (*resiter != res->getLoadPlans().end() && (*resiter)->getQuantity()==0.0)
      ++(*resiter);
    if (*resiter == res->getLoadPlans().end()) return nullptr;

    // Return result
    ld = const_cast<LoadPlan*>(static_cast<const LoadPlan*>(&*((*resiter)++)));
  }
  else
  {
    while (*opplaniter != opplan->endLoadPlans() && (*opplaniter)->getQuantity()==0.0)
      ++(*opplaniter);
    if (*opplaniter == opplan->endLoadPlans()) return nullptr;
    ld = static_cast<LoadPlan*>(&*((*opplaniter)++));
  }
  Py_INCREF(ld);
  return const_cast<LoadPlan*>(ld);
}


LoadPlan::AlternateIterator::AlternateIterator(const LoadPlan* o) : ldplan(o)
{
  if (ldplan->getLoad() && ldplan->getLoad()->getResource()->isGroup())
  {
    for (Resource::memberRecursiveIterator i(ldplan->getLoad()->getResource()); !i.empty(); ++i)
    {
      if (ldplan->getResource() == &*i)
        continue;
      Skill* sk = ldplan->getLoad()->getSkill();
      if (!sk || i->hasSkill(sk, ldplan->getDate(), ldplan->getDate()))
      {
        auto my_eff = i->getEfficiencyCalendar()
          ? i->getEfficiencyCalendar()->getValue(ldplan->getOperationPlan()->getStart())
          : i->getEfficiency();
        if (my_eff > 0)
          resources.push_back(&*i);
      }
    }
  }
  resIter = resources.begin();
}


Resource* LoadPlan::AlternateIterator::next()
{
  if (resIter == resources.end())
    return nullptr;
  auto tmp = *resIter;
  ++resIter;
  return tmp;
}


} // end namespace
