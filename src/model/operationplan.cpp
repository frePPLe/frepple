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
#include "frepple/model.h"

namespace frepple
{

DECLARE_EXPORT const MetaClass* OperationPlan::metadata;
DECLARE_EXPORT const MetaCategory* OperationPlan::metacategory;
DECLARE_EXPORT unsigned long OperationPlan::counterMin = 2;


int OperationPlan::initialize()
{
  // Initialize the metadata
  OperationPlan::metacategory = new MetaCategory("operationplan", "operationplans",
      OperationPlan::createOperationPlan, OperationPlan::writer);
  OperationPlan::metadata = new MetaClass("operationplan", "operationplan");

  // Initialize the Python type
  PythonType& x = FreppleCategory<OperationPlan>::getType();
  x.setName("operationplan");
  x.setDoc("frePPLe operationplan");
  x.supportgetattro();
  x.supportsetattro();
  x.supportstr();
  x.supportcreate(create);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


void DECLARE_EXPORT OperationPlan::setChanged(bool b)
{
  if (owner)
    owner->setChanged(b);
  else
  {
    oper->setChanged(b);
    if (dmd) dmd->setChanged();
  }
}


DECLARE_EXPORT Object* OperationPlan::createOperationPlan
(const MetaClass* cat, const AttributeList& in)
{
  // Pick up the action attribute
  Action action = MetaClass::decodeAction(in);

  // Decode the attributes
  const DataElement* opnameElement = in.get(Tags::tag_operation);
  if (!*opnameElement && action==ADD)
    // Operation name required
    throw DataException("Missing operation attribute");
  string opname = *opnameElement ? opnameElement->getString() : "";

  // Decode the operationplan identifier
  unsigned long id = 0;
  const DataElement* idfier = in.get(Tags::tag_id);
  if (*idfier) id = idfier->getUnsignedLong();
  if (!id && (action==CHANGE || action==REMOVE))
    // Identifier is required
    throw DataException("Missing operationplan identifier");

  // If an identifier is specified, we look up this operation plan
  OperationPlan* opplan = NULL;
  if (id)
  {
    if (id == ULONG_MAX)
    {
      ostringstream ch;
      ch << "Operationplan id can't be equal to " << ULONG_MAX;
      throw DataException(ch.str());
    }
    opplan = OperationPlan::findId(id);
    if (opplan && !opname.empty()
        && opplan->getOperation()->getName()!=opname)
    {
      // Previous and current operations don't match.
      ostringstream ch;
      ch << "Operationplan identifier " << id
          << " defined multiple times with different operations: '"
          << opplan->getOperation() << "' & '" << opname << "'";
      throw DataException(ch.str());
    }
  }

  // Execute the proper action
  switch (action)
  {
    case REMOVE:
      if (opplan)
      {
        // Send out the notification to subscribers
        if (opplan->getType().raiseEvent(opplan, SIG_REMOVE))
          // Delete it
          delete opplan;
        else
        {
          // The callbacks disallowed the deletion!
          ostringstream ch;
          ch << "Can't delete operationplan with identifier " << id;
          throw DataException(ch.str());
        }
      }
      else
      {
        ostringstream ch;
        ch << "Operationplan with identifier " << id << " doesn't exist";
        throw DataException(ch.str());
      }
      return NULL;
    case ADD:
      if (opplan)
      {
        ostringstream ch;
        ch << "Operationplan with identifier " << id
            << " already exists and can't be added again";
        throw DataException(ch.str());
      }
      if (opname.empty())
        throw DataException
        ("Operation name missing for creating an operationplan");
      break;
    case CHANGE:
      if (!opplan)
      {
        ostringstream ch;
        ch << "Operationplan with identifier " << id << " doesn't exist";
        throw DataException(ch.str());
      }
      break;
    case ADD_CHANGE: ;
  }

  // Return the existing operationplan
  if (opplan) return opplan;

  // Create a new operation plan
  Operation* oper = Operation::find(opname);
  if (!oper)
  {
    // Can't create operationplan because the operation doesn't exist
    throw DataException("Operation '" + opname + "' doesn't exist");
  }
  else
  {
    // Create an operationplan
    opplan = oper->createOperationPlan(0.0,Date::infinitePast,Date::infinitePast,NULL,NULL,id,false);
    if (!opplan->getType().raiseEvent(opplan, SIG_ADD))
    {
      delete opplan;
      throw DataException("Can't create operationplan");
    }
    return opplan;
  }
}


DECLARE_EXPORT OperationPlan* OperationPlan::findId(unsigned long l)
{
  // We are garantueed that there are no operationplans that have an id equal
  // or higher than the current counter. This is garantueed by the
  // instantiate() method.
  if (l >= counterMin) return NULL;

  // Loop through all operationplans.
  for (OperationPlan::iterator i = begin(); i != end(); ++i)
    if (i->id == l) return &*i;

  // This ID was not found
  return NULL;
}


DECLARE_EXPORT bool OperationPlan::assignIdentifier()
{
  static Mutex onlyOne;
  ScopeMutexLock l(onlyOne);  // Need to assure that ids are unique!
  if (id && id!=ULONG_MAX)
  {
    // An identifier was read in from input
    if (id < counterMin)
    {
      // The assigned id potentially clashes with an existing operationplan.
      // Check whether it clashes with existing operationplans
      OperationPlan* opplan = findId(id);
      if (opplan && opplan->getOperation()!=oper)
        return false;
    }
    // The new operationplan definitely doesn't clash with existing id's.
    // The counter need updating to garantuee that counter is always
    // a safe starting point for tagging new operationplans.
    else
      counterMin = id+1;
  }
  else
    // Fresh operationplan with blank id
    id = counterMin++;

  // Check whether the counter is still okay
  if (counterMin >= ULONG_MAX)
    throw RuntimeException("Exhausted the range of available operationplan identifiers");

  return true;
}


DECLARE_EXPORT bool OperationPlan::activate()
{
  // At least a valid operation pointer must exist
  if (!oper) throw LogicException("Initializing an invalid operationplan");

  // Avoid negative quantities, and call operation specific activation code
  if (getQuantity() < 0.0 || !oper->extraInstantiate(this))
  {
    delete this;
    return false;
  }

  // Instantiate all suboperationplans as well
  for (OperationPlan::iterator x(this); x != end(); ++x)
    x->activate();

  // Mark as activated by assigning a unique identifier.
  if (id && id!=ULONG_MAX)
  {
    // Validate the user provided id.
    if (!assignIdentifier())
    {
      ostringstream ch;
      ch << "Operationplan id " << id << " assigned multiple times";
      delete this;
      throw DataException(ch.str());
    }
  }
  else
    // The id given at this point is only a temporary one. The final id is
    // created lazily when the getIdentifier method is called.
    // In this way, 1) we avoid clashes between auto-generated and
    // user-provided in the input and 2) we keep performance high.
    id = ULONG_MAX;

  // Insert into the doubly linked list of operationplans.
  insertInOperationplanList();

  // If we used the lazy creator, the flow- and loadplans have not been
  // created yet. We do it now...
  createFlowLoads();

  // Mark the operation to detect its problems
  // Note that a single operationplan thus retriggers the problem computation
  // for all operationplans of this operation. For models with 1) a large
  // number of operationplans per operation and 2) very frequent problem
  // detection, this could constitute a scalability problem. This combination
  // is expected to be unusual and rare, justifying this design choice.
  oper->setChanged();

  // The operationplan is valid
  return true;
}


DECLARE_EXPORT void OperationPlan::deactivate()
{
  // Mark as not activated
  id = 0;

  // Delete from the list of deliveries
  if (dmd) dmd->removeDelivery(this);

  // Delete from the operationplan list
  removeFromOperationplanList();

  // Mark the operation to detect its problems
  oper->setChanged();
}


DECLARE_EXPORT void OperationPlan::insertInOperationplanList()
{

  // Check if already linked
  if (prev || oper->first_opplan == this) return;

  if (!oper->first_opplan)
  {
    // First operationplan in the list
    oper->first_opplan = this;
    oper->last_opplan = this;
  }
  else if (*this < *(oper->first_opplan))
  {
    // First in the list
    next = oper->first_opplan;
    next->prev = this;
    oper->first_opplan = this;
  }
  else if (*(oper->last_opplan) < *this)
  {
    // Last in the list
    prev = oper->last_opplan;
    prev->next = this;
    oper->last_opplan = this;
  }
  else
  {
    // Insert in the middle of the list
    OperationPlan *x = oper->last_opplan;
    OperationPlan *y = NULL;
    while (!(*x < *this))
    {
      y = x;
      x = x->prev;
    }
    next = y;
    prev = x;
    if (x) x->next = this;
    if (y) y->prev = this;
  }
}


DECLARE_EXPORT void OperationPlan::removeFromOperationplanList()
{
  if (prev)
    // In the middle
    prev->next = next;
  else if (oper->first_opplan == this)
    // First opplan in the list of this operation
    oper->first_opplan = next;
  if (next)
    // In the middle
    next->prev = prev;
  else if (oper->last_opplan == this)
    // Last opplan in the list of this operation
    oper->last_opplan = prev;
  // Clear existing pointers to become an orphan
  prev = NULL;
  next = NULL;
}


DECLARE_EXPORT void OperationPlan::eraseSubOperationPlan(OperationPlan* o)
{
  // Check
  if (!o) return;

  // Check valid ownership
  if (o->owner != this)
    throw LogicException("Suboperationplan has a different owner");

  // Remove from the list
  if (o->prevsubopplan)
    o->prevsubopplan->nextsubopplan = o->nextsubopplan;
  else
    firstsubopplan = o->nextsubopplan;
  if (o->nextsubopplan)
    o->nextsubopplan->prevsubopplan = o->prevsubopplan;
  else
    lastsubopplan = o->prevsubopplan;

  // Clear fields
  o->owner = NULL;
  prevsubopplan = NULL;
  nextsubopplan = NULL;
};


DECLARE_EXPORT bool OperationPlan::operator < (const OperationPlan& a) const
{
  // Different operations
  if (oper != a.oper)
    return *oper < *(a.oper);

  // Different start date
  if (dates.getStart() != a.dates.getStart())
    return dates.getStart() < a.dates.getStart();

  // Sort based on quantity
  return quantity >= a.quantity;
}


DECLARE_EXPORT void OperationPlan::createFlowLoads()
{
  // Has been initialized already, it seems
  if (firstflowplan || firstloadplan) return;

  // Create setup suboperationplans and loadplans
  if (getConsumeCapacity() || !getLocked())
    for (Operation::loadlist::const_iterator g=oper->getLoads().begin();
        g!=oper->getLoads().end(); ++g)
      if (!g->getAlternate())
      {
        new LoadPlan(this, &*g);
        if (!g->getSetup().empty() && g->getResource()->getSetupMatrix())
          OperationSetup::setupoperation->createOperationPlan(
            1, getDates().getStart(), getDates().getStart(), NULL, this);
      }

  // Create flowplans for flows
  bool cons = getLocked() ? getConsumeMaterial() : true;
  bool prod = getLocked() ? getProduceMaterial() : true;
  if (cons || prod)
    for (Operation::flowlist::const_iterator h=oper->getFlows().begin();
        h!=oper->getFlows().end(); ++h)
    {
      if (h->getAlternate()) continue; // Only the primary flow is instantiated
      if (h->getQuantity() > 0 ? prod : cons)
        new FlowPlan(this, &*h);
    }
}


DECLARE_EXPORT void OperationPlan::deleteFlowLoads()
{
  // If no flowplans and loadplans, the work is already done
  if (!firstflowplan && !firstloadplan) return;

  FlowPlanIterator e = beginFlowPlans();
  firstflowplan = NULL;    // Important to do this before the delete!
  LoadPlanIterator f = beginLoadPlans();
  firstloadplan = NULL;  // Important to do this before the delete!

  // Delete the flowplans
  while (e != endFlowPlans()) delete &*(e++);

  // Delete the loadplans (including the setup suboperationplan)
  while (f != endLoadPlans()) delete &*(f++);
}


DECLARE_EXPORT double OperationPlan::getTotalFlowAux(const Buffer* b) const
{
  double q = 0.0;

  // Add my own quantity
  for (FlowPlanIterator f = beginFlowPlans(); f != endFlowPlans(); ++f)
    if (f->getBuffer() == b)
      q += f->getQuantity();

  // Add the quantity of all children
  for (OperationPlan* c = firstsubopplan; c; c = c->nextsubopplan)
    q += c->getTotalFlowAux(b);

  // Return result
  return q;
}


DECLARE_EXPORT OperationPlan::~OperationPlan()
{
  // Delete the flowplans and loadplan
  deleteFlowLoads();

  // Initialize
  OperationPlan *x = firstsubopplan;
  firstsubopplan = NULL;
  lastsubopplan = NULL;

  // Delete the sub operationplans
  while (x)
  {
    OperationPlan *y = x->nextsubopplan;
    x->owner = NULL; // Need to clear before destroying the suboperationplan
    delete x;
    x = y;
  }

  // Delete also the owner
  if (owner)
  {
    const OperationPlan* o = owner;
    setOwner(NULL);
    delete o;
  }

  // Delete from the list of deliveries
  if (dmd) dmd->removeDelivery(this);

  // Delete from the operationplan list
  removeFromOperationplanList();
}


void DECLARE_EXPORT OperationPlan::setOwner(OperationPlan* o, bool fast)
{
  // Special case: the same owner is set twice
  if (owner == o) return;
  if (o)
    // Register with the new owner
    o->getOperation()->addSubOperationPlan(o, this, fast);
  else if (owner)
    // Setting the owner field to NULL
    owner->eraseSubOperationPlan(this);
}


void DECLARE_EXPORT OperationPlan::setStart (Date d)
{
  // Locked opplans don't move
  if (getLocked()) return;

  if (!lastsubopplan || lastsubopplan->getOperation() == OperationSetup::setupoperation)
    // No sub operationplans
    oper->setOperationPlanParameters(this,quantity,d,Date::infinitePast);
  else
  {
    // Move all sub-operationplans in an orderly fashion
    for (OperationPlan* i = firstsubopplan; i; i = i->nextsubopplan)
    {
      if (i->getOperation() == OperationSetup::setupoperation) continue;
      if (i->getDates().getStart() < d)
      {
        i->setStart(d);
        d = i->getDates().getEnd();
      }
      else
        // There is sufficient slack between the suboperationplans
        break;
    }
  }

  // Update flow and loadplans
  update();
}


void DECLARE_EXPORT OperationPlan::setEnd(Date d)
{
  // Locked opplans don't move
  if (getLocked()) return;

  if (!lastsubopplan || lastsubopplan->getOperation() == OperationSetup::setupoperation)
    // No sub operationplans
    oper->setOperationPlanParameters(this,quantity,Date::infinitePast,d);
  else
  {
    // Move all sub-operationplans in an orderly fashion
    for (OperationPlan* i = lastsubopplan; i; i = i->prevsubopplan)
    {
      if (i->getOperation() == OperationSetup::setupoperation) break;
      if (i->getDates().getEnd() > d)
      {
        i->setEnd(d);
        d = i->getDates().getStart();
      }
      else
        // There is sufficient slack between the suboperationplans
        break;
    }
  }

  // Update flow and loadplans
  update();
}


DECLARE_EXPORT void OperationPlan::resizeFlowLoadPlans()
{
  // Update all flowplans
  for (FlowPlanIterator ee = beginFlowPlans(); ee != endFlowPlans(); ++ee)
    ee->update();

  // Update all loadplans
  for (LoadPlanIterator e = beginLoadPlans(); e != endLoadPlans(); ++e)
    e->update();

  // Align the end of the setup operationplan with the start of the operation
  if (firstsubopplan && firstsubopplan->getOperation() == OperationSetup::setupoperation
      && firstsubopplan->getDates().getEnd() != getDates().getStart())
    firstsubopplan->setEnd(getDates().getStart());
  else if (getOperation() == OperationSetup::setupoperation
      && getDates().getEnd() != getOwner()->getDates().getStart())
    getOwner()->setStart(getDates().getEnd());

  // Allow the operation length to be changed now that the quantity has changed
  // Note that we assume that the end date remains fixed. This assumption makes
  // sense if the operationplan was created to satisfy a demand.
  // It is not valid though when the purpose of the operationplan was to push
  // some material downstream.

  // Notify the demand of the changed delivery
  if (dmd) dmd->setChanged();
}


DECLARE_EXPORT OperationPlan::OperationPlan(const OperationPlan& src, bool init)
{
  if (src.owner)
    throw LogicException("Can't copy suboperationplans. Copy the owner instead.");

  // Identifier can't be inherited, but a new one will be generated when we activate the operationplan
  id = 0;

  // Copy the fields
  quantity = src.quantity;
  flags = src.flags;
  dmd = src.dmd;
  oper = src.oper;
  firstflowplan = NULL;
  firstloadplan = NULL;
  dates = src.dates;
  prev = NULL;
  next = NULL;
  owner = NULL;
  firstsubopplan = NULL;
  lastsubopplan = NULL;
  nextsubopplan = NULL;
  prevsubopplan = NULL;
  motive = NULL;
  initType(metadata);

  // Clone the suboperationplans
  for (OperationPlan::iterator x(&src); x != end(); ++x)
    new OperationPlan(*x, this);

  // Activate
  if (init) activate();
}


DECLARE_EXPORT OperationPlan::OperationPlan(const OperationPlan& src,
    OperationPlan* newOwner)
{
  if (!newOwner)
    throw LogicException("No new owner passed in private copy constructor.");

  // Identifier can't be inherited, but a new one will be generated when we activate the operationplan
  id = 0;

  // Copy the fields
  quantity = src.quantity;
  flags = src.flags;
  dmd = src.dmd;
  oper = src.oper;
  firstflowplan = NULL;
  firstloadplan = NULL;
  dates = src.dates;
  prev = NULL;
  next = NULL;
  owner = NULL;
  firstsubopplan = NULL;
  lastsubopplan = NULL;
  nextsubopplan = NULL;
  prevsubopplan = NULL;
  motive = NULL;
  initType(metadata);

  // Set owner
  setOwner(newOwner);

  // Clone the suboperationplans
  for (OperationPlan::iterator x(&src); x != end(); ++x)
    new OperationPlan(*x, this);
}


DECLARE_EXPORT void OperationPlan::update()
{
  if (lastsubopplan && lastsubopplan->getOperation() != OperationSetup::setupoperation)
  {
    // Set the start and end date of the parent.
    Date st = Date::infiniteFuture;
    Date nd = Date::infinitePast;
    for (OperationPlan *f=firstsubopplan; f; f=f->nextsubopplan)
    {
      if (f->getOperation() == OperationSetup::setupoperation)
        continue;
      if (f->getDates().getStart() < st)
        st = f->getDates().getStart();
      if (f->getDates().getEnd() > nd)
        nd = f->getDates().getEnd();
    }
    if (nd)
      dates.setStartAndEnd(st, nd);
  }

  // Update the flow and loadplans
  resizeFlowLoadPlans();

  // Notify the owner operationplan
  if (owner) owner->update();

  // Mark as changed
  setChanged();
}


DECLARE_EXPORT void OperationPlan::deleteOperationPlans(Operation* o, bool deleteLockedOpplans)
{
  if (!o) return;
  for (OperationPlan *opplan = o->first_opplan; opplan; )
  {
    OperationPlan *tmp = opplan;
    opplan = opplan->next;
    // Note that the deletion of the operationplan also updates the opplan list
    if (deleteLockedOpplans || !tmp->getLocked()) delete tmp;
  }
}


DECLARE_EXPORT double OperationPlan::getPenalty() const
{
  double penalty = 0;
  for (OperationPlan::LoadPlanIterator i = beginLoadPlans();
      i != endLoadPlans(); ++i)
    if (i->isStart() && !i->getLoad()->getSetup().empty() && i->getResource()->getSetupMatrix())
    {
      SetupMatrix::Rule *rule = i->getResource()->getSetupMatrix()
          ->calculateSetup(i->getSetup(false), i->getSetup(true));
      if (rule) penalty += rule->getCost();
    }
  return penalty;
}


DECLARE_EXPORT bool OperationPlan::isExcess(bool strict) const
{
  // Delivery operationplans aren't excess
  if (getDemand()) return false;

  // Recursive call for suboperationplans
  for (OperationPlan* subopplan = firstsubopplan; subopplan; subopplan = subopplan->nextsubopplan)
    if (!subopplan->isExcess()) return false;

  // Loop over all producing flowplans
  bool hasFlowplans = false;
  for (OperationPlan::FlowPlanIterator i = beginFlowPlans();
      i != endFlowPlans(); ++i)
  {
    hasFlowplans = true;
    // Skip consuming flowplans
    if (i->getQuantity() <= 0) continue;

    // Find the total produced quantity, including all suboperationplans
    double prod_qty = i->getQuantity();
    for (OperationPlan* subopplan = firstsubopplan; subopplan; subopplan = subopplan->nextsubopplan)
      for (OperationPlan::FlowPlanIterator k = subopplan->beginFlowPlans();
        k != subopplan->endFlowPlans(); ++k)
        if (k->getBuffer() == i->getBuffer())
          prod_qty += k->getQuantity();
    if (prod_qty <= 0) continue;

    // Loop over all flowplans in the buffer (starting at the end) and verify
    // that the onhand is bigger than the flowplan quantity
    double current_maximum(0.0);
    double current_minimum(0.0);
    Buffer::flowplanlist::const_iterator j = i->getBuffer()->getFlowPlans().rbegin();
    if (!strict && j != i->getBuffer()->getFlowPlans().end())
    {
      current_maximum = i->getBuffer()->getFlowPlans().getMax(&*j);
      current_minimum = i->getBuffer()->getFlowPlans().getMin(&*j);
    }
    for (; j != i->getBuffer()->getFlowPlans().end(); --j)
    {
      if ( (current_maximum > 0
          && j->getOnhand() < prod_qty + current_maximum - ROUNDING_ERROR)
          || j->getOnhand() < prod_qty + current_minimum - ROUNDING_ERROR )
        return false;
      if (j->getType() == 4 && !strict) current_maximum = j->getMax(false);
      if (j->getType() == 3 && !strict) current_minimum = j->getMin(false);
      if (&*j == &*i) break;
    }
  }

  // Handle operationplan already being deleted by a deleteOperation command
  if (!hasFlowplans && getOperation()->getFlows().begin() != getOperation()->getFlows().end())
    return false;

  // If we remove this operationplan the onhand in all buffers remains positive.
  return true;
}


DECLARE_EXPORT TimePeriod OperationPlan::getUnavailable() const
{
  TimePeriod x;
  DateRange y = getOperation()->calculateOperationTime(dates.getStart(), dates.getEnd(), &x);
  return dates.getDuration() - x;
}


DECLARE_EXPORT void OperationPlan::writer(const MetaCategory* c, XMLOutput* o)
{
  if (!empty())
  {
    o->BeginObject(*c->grouptag);
    for (iterator i=begin(); i!=end(); ++i)
      o->writeElement(*c->typetag, *i);
    o->EndObject(*c->grouptag);
  }
}


DECLARE_EXPORT void OperationPlan::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Don't export operationplans of hidden operations
  if (oper->getHidden()) return;

  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(
      tag, Tags::tag_id, const_cast<OperationPlan*>(this)->getIdentifier(),
      Tags::tag_operation, oper->getName()
      );
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL)
    o->BeginObject(
      tag, Tags::tag_id, const_cast<OperationPlan*>(this)->getIdentifier(),
      Tags::tag_operation, XMLEscape(oper->getName())
      );

  // The demand reference is only valid for delivery operationplans,
  // and it should only be written if this tag is not being written
  // as part of a demand+delivery tag.
  if (dmd && !dynamic_cast<Demand*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_demand, dmd);

  o->writeElement(Tags::tag_start, dates.getStart());
  o->writeElement(Tags::tag_end, dates.getEnd());
  o->writeElement(Tags::tag_quantity, quantity);
  o->writeElement(Tags::tag_criticality, getCriticality());
  if (getLocked()) o->writeElement (Tags::tag_locked, true);
  if (!getConsumeMaterial()) o->writeElement(Tags::tag_consume_material, false);
  if (!getProduceMaterial()) o->writeElement(Tags::tag_produce_material, false);
  if (!getConsumeCapacity()) o->writeElement(Tags::tag_consume_capacity, false);
  o->writeElement(Tags::tag_source, getSource());
  o->writeElement(Tags::tag_owner, owner);

  // Write out the flowplans and their pegging
  if (o->getContentType() == XMLOutput::PLANDETAIL)
  {
    o->BeginObject(Tags::tag_flowplans);
    for (FlowPlanIterator qq = beginFlowPlans(); qq != endFlowPlans(); ++qq)
      qq->writeElement(o, Tags::tag_flowplan);
    o->EndObject(Tags::tag_flowplans);
  }

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT void OperationPlan::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_demand))
    pIn.readto( Demand::reader(Demand::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_owner))
    pIn.readto(createOperationPlan(metadata,pIn.getAttributes()));
  else if (pAttr.isA(Tags::tag_flowplans))
    pIn.IgnoreElement();
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT void OperationPlan::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  // Note that the fields have been ordered more or less in the order
  // of their expected frequency.
  // Note that id and operation are handled already during the
  // operationplan creation. They don't need to be handled here...
  if (pAttr.isA(Tags::tag_quantity))
    pElement >> quantity;
  else if (pAttr.isA(Tags::tag_start))
    dates.setStart(pElement.getDate());
  else if (pAttr.isA(Tags::tag_end))
    dates.setEnd(pElement.getDate());
  else if (pAttr.isA(Tags::tag_owner) && !pIn.isObjectEnd())
  {
    OperationPlan* o = dynamic_cast<OperationPlan*>(pIn.getPreviousObject());
    if (o) setOwner(o, false); // Extra argument is used to trigger validation of the new owner
  }
  else if (pIn.isObjectEnd())
  {
    // Initialize the operationplan
    if (!activate())
      // Initialization failed and the operationplan is deleted
      pIn.invalidateCurrentObject();
  }
  else if (pAttr.isA (Tags::tag_demand))
  {
    Demand *d = dynamic_cast<Demand*>(pIn.getPreviousObject());
    if (d) d->addDelivery(this);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
  else if (pAttr.isA(Tags::tag_locked))
    setLocked(pElement.getBool());
  else if (pAttr.isA(Tags::tag_consume_material))
    setConsumeMaterial(pElement.getBool());
  else if (pAttr.isA(Tags::tag_consume_capacity))
    setConsumeCapacity(pElement.getBool());
  else if (pAttr.isA(Tags::tag_produce_material))
    setProduceMaterial(pElement.getBool());
}


DECLARE_EXPORT void OperationPlan::setLocked(bool b)
{
  if (b)
    flags |= IS_LOCKED;
  else
    flags &= ~IS_LOCKED;
  for (OperationPlan *x = firstsubopplan; x; x = x->nextsubopplan)
    x->setLocked(b);
  update();
}


DECLARE_EXPORT void OperationPlan::setDemand(Demand* l)
{
  // No change
  if (l==dmd) return;

  // Unregister from previous demand
  if (dmd) dmd->removeDelivery(this);

  // Register at the new demand and mark it changed
  dmd = l;
  if (l)
  {
    l->addDelivery(this);
    l->setChanged();
  }
}


PyObject* OperationPlan::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Find or create the C++ object
    PythonAttributeList atts(kwds);
    Object* x = createOperationPlan(OperationPlan::metadata,atts);
    Py_INCREF(x);

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (x)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonObject field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        Attribute attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::tag_operation) && !attr.isA(Tags::tag_id)
          && !attr.isA(Tags::tag_action) && !attr.isA(Tags::tag_type))
        {
          int result = x->setattro(attr, field);
          if (result && !PyErr_Occurred())
            PyErr_Format(PyExc_AttributeError,
                "attribute '%S' on '%s' can't be updated",
                key, Py_TYPE(x)->tp_name);
        }
      };
    }

    if (x && !static_cast<OperationPlan*>(x)->activate())
    {
      PyErr_SetString(PythonRuntimeException, "operationplan activation failed");
      return NULL;
    }
    return x;
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}


DECLARE_EXPORT PyObject* OperationPlan::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_id))
    return PythonObject(getIdentifier());
  if (attr.isA(Tags::tag_operation))
    return PythonObject(getOperation());
  if (attr.isA(Tags::tag_flowplans))
    return new frepple::FlowPlanIterator(this);
  if (attr.isA(Tags::tag_loadplans))
    return new frepple::LoadPlanIterator(this);
  if (attr.isA(Tags::tag_quantity))
    return PythonObject(getQuantity());
  if (attr.isA(Tags::tag_start))
    return PythonObject(getDates().getStart());
  if (attr.isA(Tags::tag_end))
    return PythonObject(getDates().getEnd());
  if (attr.isA(Tags::tag_demand))
    return PythonObject(getDemand());
  if (attr.isA(Tags::tag_locked))
    return PythonObject(getLocked());
  if (attr.isA(Tags::tag_owner))
    return PythonObject(getOwner());
  if (attr.isA(Tags::tag_operationplans))
    return new OperationPlanIterator(this);
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(getHidden());
  if (attr.isA(Tags::tag_unavailable))
    return PythonObject(getUnavailable());
  if (attr.isA(Tags::tag_criticality))
    return PythonObject(getCriticality());
  if (attr.isA(Tags::tag_consume_material))
    return PythonObject(getConsumeMaterial());
  if (attr.isA(Tags::tag_consume_capacity))
    return PythonObject(getConsumeCapacity());
  if (attr.isA(Tags::tag_produce_material))
    return PythonObject(getProduceMaterial());
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  if (attr.isA(Tags::tag_motive))
  {
    // Null
    if (!getMotive())
    {
      Py_INCREF(Py_None);
      return Py_None;
    }

    // Demand
    Demand* d = dynamic_cast<Demand*>(getMotive());
    if (d) return PythonObject(d);

    // Buffer
    Buffer* b = dynamic_cast<Buffer*>(getMotive());
    if (b) return PythonObject(b);

    // Resource
    Resource* r = dynamic_cast<Resource*>(getMotive());
    if (r) return PythonObject(r);

    // Unknown type
    PyErr_SetString(PythonLogicException, "Unhandled motive type");
    return NULL;
  }
  return NULL;
}


DECLARE_EXPORT int OperationPlan::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_quantity))
    setQuantity(field.getDouble());
  else if (attr.isA(Tags::tag_start))
    setStart(field.getDate());
  else if (attr.isA(Tags::tag_end))
    setEnd(field.getDate());
  else if (attr.isA(Tags::tag_locked))
    setLocked(field.getBool());
  else if (attr.isA(Tags::tag_demand))
  {
    if (!field.check(Demand::metadata))
    {
      PyErr_SetString(PythonDataException, "operationplan demand must be of type demand");
      return -1;
    }
    Demand* y = static_cast<Demand*>(static_cast<PyObject*>(field));
    setDemand(y);
  }
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(OperationPlan::metadata))
    {
      PyErr_SetString(PythonDataException, "operationplan demand must be of type demand");
      return -1;
    }
    OperationPlan* y = static_cast<OperationPlan*>(static_cast<PyObject*>(field));
    setOwner(y, false); // Extra argument is used to trigger validation of the new owner
  }
  else if (attr.isA(Tags::tag_motive))
  {
    Plannable* y;
    if (static_cast<PyObject*>(field) == Py_None)
      y = NULL;
    if (field.check(Demand::metadata))
      y = static_cast<Demand*>(static_cast<PyObject*>(field));
    else if (field.check(Buffer::metadata))
      y = static_cast<Buffer*>(static_cast<PyObject*>(field));
    else if (field.check(Resource::metadata))
      y = static_cast<Resource*>(static_cast<PyObject*>(field));
    else
    {
      PyErr_SetString(PythonDataException, "operationplan motive must be of type demand, buffer or resource");
      return -1;
    }
    setMotive(y);
  }
  else if (attr.isA(Tags::tag_consume_material))
    setConsumeMaterial(field.getBool());
  else if (attr.isA(Tags::tag_consume_capacity))
    setConsumeCapacity(field.getBool());
  else if (attr.isA(Tags::tag_produce_material))
    setProduceMaterial(field.getBool());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;
  return 0;
}


DECLARE_EXPORT double OperationPlan::getCriticality() const
{
  // Child operationplans have the same criticality as the parent
  // TODO: Slack between routing sub operationplans isn't recognized. 
  if (getOwner() && getOwner()->getOperation()->getType() != *OperationSplit::metadata)
    return getOwner()->getCriticality();

  // Handle demand delivery operationplans
  if (getTopOwner()->getDemand())
  {

    long early = getDemand()->getDue() - getDates().getEnd();
    return ((early<=0L) ? 0.0 : early) / 86400.0; // Convert to days
  }

  // Upstream operationplan
  TimePeriod minslack = 86313600L; // 999 days in seconds
  vector<const OperationPlan*> opplans(HasLevel::getNumberOfLevels() + 5);
  for (PeggingIterator p(this); p; p++)
  {
    unsigned int lvl = p.getLevel();
    if (lvl >= opplans.size())
      opplans.resize(lvl + 5);
    opplans[lvl] = p.getOperationPlan();
    const OperationPlan* m = p.getOperationPlan();
    if (m && m->getTopOwner()->getDemand())
    {
      // Reached a demand. Get the total slack now.
      TimePeriod myslack = m->getTopOwner()->getDemand()->getDue() - m->getDates().getEnd();
      if (myslack < 0L) myslack = 0L;
      for (unsigned int i=1; i<=lvl; i++)
      {
        if (opplans[i-1]->getOwner() == opplans[i] || opplans[i-1] == opplans[i]->getOwner())
          // Times between parent and child opplans isn't slack
          continue;
        Date st = opplans[i-1]->getDates().getEnd();
        if (!st) st = Plan::instance().getCurrent();
        Date nd = opplans[i]->getDates().getStart();
        if (!nd) nd = Plan::instance().getCurrent();
        if (nd > st)
          myslack += nd - st;
      }
      if (myslack < minslack)
        minslack = myslack;
    }
  }
  return minslack / 86400.0; // Convert to days
}

} // end namespace
