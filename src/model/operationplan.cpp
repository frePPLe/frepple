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

DECLARE_EXPORT unsigned long OperationPlan::counter = 1;

OperationPlan::OperationPlanList OperationPlan::nosubOperationPlans;


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
(const MetaClass& cat, const AttributeList& in)
{
  // Pick up the action attribute
  Action action = MetaClass::decodeAction(in);

  // Decode the attributes
  const DataElement* opnameElement = in.get(Tags::tag_operation);
  if (!*opnameElement && action!=REMOVE) 
    throw DataException("Missing operation attribute");
  string opname = *opnameElement ? opnameElement->getString() : "";

  // Decode the operationplan identifier
  unsigned long id = 0;
  const DataElement* idfier = in.get(Tags::tag_id);
  if (*idfier) id = idfier->getUnsignedLong();

  // If an ID is specified, we look up this operation plan
  OperationPlan* opplan = NULL;
  if (idfier)
  {
    opplan = OperationPlan::findId(id);
    if (opplan && !opname.empty()
        && opplan->getOperation()->getName()==opname)
    {
      // Previous and current operations don't match.
      ostringstream ch;
      ch << "Operationplan id " << id
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
      logger << "START DELET" << endl;
        // Send out the notification to subscribers
        if (opplan->getType().raiseEvent(opplan, SIG_REMOVE))
          // Delete it
          delete opplan;
        else
        {
          // The callbacks disallowed the deletion!
          ostringstream ch;
          ch << "Can't delete operationplan with id " << id;
          throw DataException(ch.str());
        }
      }
      else
      {
        ostringstream ch;
        ch << "Can't find operationplan with identifier "
        << id << " for removal";
        throw DataException(ch.str());
      }
      logger << "END DELET" << endl;
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
  // initialize() method.
  if (l >= counter) return NULL;

  // Loop through all operationplans.
  for (OperationPlan::iterator i = begin(); i != end(); ++i)
    if (i->id == l) return &*i;

  // This ID was not found
  return NULL;
}


DECLARE_EXPORT bool OperationPlan::initialize()
{
  // At least a valid operation pointer must exist
  if (!oper) throw LogicException("Initializing an invalid operationplan");

  // Avoid zero quantity on top-operationplans
  if (getQuantity() <= 0.0 && !owner)
  {
    delete this;
    return false;
  }

  // See if we can consolidate this operationplan with an existing one.
  // Merging is possible only when all the following conditions are met:
  //   - id is not set
  //   - it is a fixedtime operation
  //   - it doesn't load any resources
  //   - both operationplans aren't locked
  //   - both operationplans have no owner
  //   - start and end date of both operationplans are the same
  //   - demand of both operationplans are the same
  if (!id && getOperation()->getType() == OperationFixedTime::metadata 
    && !getLocked() && !getOwner() && getOperation()->getLoads().empty())
  {
    // Loop through candidates
    OperationPlan *x = oper->last_opplan;
    OperationPlan *y = NULL;
    while (x && !(*x < *this))
    {
      y = x;
      x = x->prev;
    }
    if (y && y->getDates() == getDates() && !y->getOwner() 
      && y->getDemand() == getDemand() && !y->getLocked())
    {
      // Merging with the 'next' operationplan
      y->setQuantity(y->getQuantity() + getQuantity());
      delete this;
      return false;
    }
    if (x && x->getDates() == getDates() && !x->getOwner() 
      && x->getDemand() == getDemand() && !x->getLocked())
    {
      // Merging with the 'previous' operationplan
      x->setQuantity(x->getQuantity() + getQuantity());
      delete this;
      return false;
    }
  }

  // Create unique identifier
  // Having an identifier assigned is an important flag.
  // Only operation plans with an id :
  //   - can be linked in the global operation plan list.
  //   - can have problems (this results from the previous point).
  //   - can be linked with a demand.
  // These properties allow us to delete operation plans without an id faster.
  static Mutex onlyOne;
  {
  ScopeMutexLock l(onlyOne);  // Need to assure that ids are unique!
  if (id)
  {
    // An identifier was read in from input
    if (id < counter)
    {
      // The assigned id potentially clashes with an existing operationplan.
      // Check whether it clashes with existing operationplans
      OperationPlan* opplan = findId(id);
      if (opplan && opplan->getOperation()!=oper)
      {
        ostringstream ch;
        ch << "Operationplan id " << id
          << " defined multiple times with different operations: '"
          << opplan->getOperation() << "' & '" << oper << "'";
        delete this;   
        throw DataException(ch.str());
      }
    }
    else
      // The new operationplan definately doesn't clash with existing id's.
      // The counter need updating to garantuee that counter is always
      // a safe starting point for tagging new operationplans.
      counter = id+1;
  }
  else
    // Fresh operationplan with blank id
    id = counter++;
  }

  // Insert into the doubly linked list of operationplans.
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

  // If we used the lazy creator, the flow- and loadplans have not been
  // created yet. We do it now...
  createFlowLoads();

  // Extra registration step if this is a delivery operation
  if (getDemand() && getDemand()->getDeliveryOperation() == oper)
    dmd->addDelivery(this);

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


DECLARE_EXPORT void OperationPlan::updateSorting()
{
  // Get out right away if this operationplan isn't initialized yet
  if (!(next || prev || oper->last_opplan==this || oper->first_opplan==this))
    return;

  // Verify that we are smaller than the next operationplan
  while (next && !(*this < *next))
  {
    // Swap places with the next
    OperationPlan *tmp = next;
    if (oper->first_opplan == this)
      // New first operationplan
      oper->first_opplan = tmp;
    if (tmp->next) tmp->next->prev = this;
    if (prev) prev->next = tmp;
    tmp->prev = prev;
    next = tmp->next;
    tmp->next = this;
    prev = tmp;
  }

  // Verify that we are bigger than the previous operationplan
  while (prev && !(*prev < *this))
  {
    // Swap places with the previous
    OperationPlan *tmp = prev;
    if (oper->last_opplan == this)
      // New last operationplan
      oper->last_opplan = tmp;
    if (tmp->prev) tmp->prev->next = this;
    if (next) next->prev = tmp;
    prev = tmp->prev;
    tmp->prev = this;
    tmp->next = next;
    next = tmp;
  }

  // Update operation if we have become the first or the last operationplan
  if (!next) oper->last_opplan = this;
  if (!prev) oper->first_opplan = this;
}


DECLARE_EXPORT void OperationPlan::createFlowLoads()
{
  // Has been initialized already, it seems
  if (firstflowplan || firstloadplan) return;

  // Create loadplans
  for (Operation::loadlist::const_iterator g=oper->getLoads().begin();
      g!=oper->getLoads().end(); ++g)
    new LoadPlan(this, &*g);

  // Create flowplans
  for (Operation::flowlist::const_iterator h=oper->getFlows().begin();
      h!=oper->getFlows().end(); ++h)
    new FlowPlan(this, &*h);
}


DECLARE_EXPORT OperationPlan::~OperationPlan()
{
  // Delete the flowplans
  for (FlowPlanIterator e = beginFlowPlans(); e != endFlowPlans();)
    delete &*(e++);

  // Delete the loadplans
  for (LoadPlanIterator f = beginLoadPlans(); f != endLoadPlans();)
    delete &*(f++);

  // Delete also the owner
  if (owner)
  {
    const OperationPlan* o = owner;
    setOwner(NULL);
    delete o;
  }

  // The following actions are only required for registered operation plans.
  // Only those are linked in the list and can have problems: see the
  // documentation in the initialize() method.
  if (getIdentifier())
  {
    // Delete from the list of deliveries
    if (dmd) dmd->removeDelivery(this);

    // Delete from the operationplan list
    if (prev) prev->next = next;
    else oper->first_opplan = next; // First opplan in the list of this operation
    if (next) next->prev = prev;
    else oper->last_opplan = prev; // Last opplan in the list of this operation
  }
}


void DECLARE_EXPORT OperationPlan::setOwner(OperationPlan* o)
{
  // Special case: the same owner is set twice
  if (owner == o) return;
  // Erase the previous owner if there is one
  if (owner) owner->eraseSubOperationPlan(this);
  // Set new owner
  owner = o;
  // Register with the new owner
  if (owner) owner->addSubOperationPlan(this);
}


void DECLARE_EXPORT OperationPlan::setStart (Date d)
{
  if (getLocked()) return;
  oper->setOperationPlanParameters(this,quantity,d,Date::infinitePast);

  // Update flow and loadplans
  update();
}


void DECLARE_EXPORT OperationPlan::setEnd (Date d)
{
  if (getLocked()) return;
  oper->setOperationPlanParameters(this,quantity,Date::infinitePast,d);

  // Update flow and loadplans
  update();
}


DECLARE_EXPORT void OperationPlan::setQuantity (double f, bool roundDown, bool upd)
{
  // No impact on locked operationplans
  if (getLocked()) return;

  // Invalid operationplan: the quantity must be >= 0.
  if (f < 0)
    throw DataException("Operationplans can't have negative quantities");

  // Setting a quantity is only allowed on a top operationplan
  if (owner)
  {
    owner->setQuantity(f,roundDown,upd);
    return;
  }

  // Compute the correct size for the operationplan
  if (f!=0.0 && getOperation()->getSizeMinimum()>0.0
      && f < getOperation()->getSizeMinimum())
  {
    if (roundDown)
    {
      // Smaller than the minimum quantity, rounding down means... nothing
      quantity = 0.0;
      // Update the flow and loadplans, and mark for problem detection
      if (upd) update();
      return;
    }
    f = getOperation()->getSizeMinimum();
  }
  if (f!=0.0 && getOperation()->getSizeMultiple()>0.0)
  {
    int mult = static_cast<int> (f / getOperation()->getSizeMultiple()
        + (roundDown ? 0.0 : 0.99999999));
    quantity = mult * getOperation()->getSizeMultiple();
  }
  else
    quantity = f;

  // Update the flow and loadplans, and mark for problem detection
  if (upd) update();
}


DECLARE_EXPORT void OperationPlan::resizeFlowLoadPlans()
{
  // Update all flowplans
  for (FlowPlanIterator ee = beginFlowPlans(); ee != endFlowPlans(); ++ee)
    ee->update();

  // Update all loadplans
  for (LoadPlanIterator e = beginLoadPlans(); e != endLoadPlans(); ++e)
    e->update();

  // Allow the operation length to be changed now that the quantity has changed
  // Note that we assume that the end date remains fixed. This assumption makes
  // sense if the operationplan was created to satisfy a demand.
  // It is not valid though when the purpose of the operationplan was to push
  // some material downstream.

  // Notify the demand of the changed delivery
  if (dmd) dmd->setChanged();

  // Update the sorting of the operationplan in the list
  updateSorting();
}


DECLARE_EXPORT void OperationPlan::update()
{
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


DECLARE_EXPORT void OperationPlan::writer(const MetaCategory& c, XMLOutput* o)
{
  if (!empty())
  {
    o->BeginObject(*c.grouptag);
    for (iterator i=begin(); i!=end(); ++i)
      o->writeElement(*c.typetag, *i);
    o->EndObject(*c.grouptag);
  }
}


DECLARE_EXPORT void OperationPlan::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Don't export operationplans of hidden operations
  if (oper->getHidden()) return;

  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
      (tag, Tags::tag_id, id, Tags::tag_operation, oper->getName());
    return;
  }

  if (m != NOHEADER)
    o->BeginObject(tag, Tags::tag_id, id, Tags::tag_operation,oper->getName());

  // The demand reference is only valid for delivery operationplans,
  // and it should only be written if this tag is not being written
  // as part of a demand+delivery tag.
  if (dmd && !dynamic_cast<Demand*>(o->getPreviousObject()))
    o->writeElement(Tags::tag_demand, dmd);

  o->writeElement(Tags::tag_start, dates.getStart());
  o->writeElement(Tags::tag_end, dates.getEnd());
  o->writeElement(Tags::tag_quantity, quantity);
  if (getLocked()) o->writeElement (Tags::tag_locked, getLocked());
  if (epst) o->writeElement(Tags::tag_epst, epst);
  if (lpst) o->writeElement(Tags::tag_lpst, lpst);
  o->writeElement(Tags::tag_owner, owner);

  // Write out the flowplans and their pegging
  if (o->getContentType() == XMLOutput::PLANDETAIL)
  {
    o->BeginObject(Tags::tag_flowplans);
    for (FlowPlanIterator qq = beginFlowPlans(); qq != endFlowPlans(); ++qq)
      qq->writeElement(o, Tags::tag_flowplan);
    o->EndObject(Tags::tag_flowplans);
  }

  o->EndObject(tag);
}


DECLARE_EXPORT void OperationPlan::beginElement (XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_demand))
    pIn.readto( Demand::reader(Demand::metadata,pIn.getAttributes()) );
  else if (pAttr.isA(Tags::tag_owner))
    pIn.readto(createOperationPlan(metadata,pIn.getAttributes()));
  else if (pAttr.isA(Tags::tag_flowplans))
    pIn.IgnoreElement();
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
    if (o) setOwner(o);
  }
  else if (pIn.isObjectEnd())
  {
    // Initialize the operationplan
    if (!initialize())
      // Initialization failed and the operationplan is deleted
      pIn.invalidateCurrentObject();
  }
  else if (pAttr.isA (Tags::tag_demand))
  {
    Demand * d = dynamic_cast<Demand*>(pIn.getPreviousObject());
    if (d) d->addDelivery(this);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_locked))
    setLocked(pElement.getBool());
  else if (pAttr.isA(Tags::tag_epst))
    pElement >> epst;
  else if (pAttr.isA(Tags::tag_lpst))
    pElement >> lpst;
}


DECLARE_EXPORT void OperationPlan::setDemand(Demand* l)
{
  // No change
  if (l==dmd) return;

  // Unregister from previous lot
  if (dmd) dmd->removeDelivery(this);

  // Register the new demand and mark it changed
  dmd = l;
  if (l) l->setChanged();
}


DECLARE_EXPORT void OperationPlanRouting::addSubOperationPlan(OperationPlan* o)
{
  // The sub opplan must point to this operationplan
  assert(o->getOwner() == this);

  // Add in the list
  step_opplans.push_front(o);

  // Update the top operationplan
  setStartAndEnd(
    step_opplans.front()->getDates().getStart(),
    step_opplans.back()->getDates().getEnd()
  );

  // Update the flow and loadplans
  update();
}


DECLARE_EXPORT OperationPlanRouting::~OperationPlanRouting()
{
  // Delete all children
  for (list<OperationPlan*>::iterator i = step_opplans.begin();
      i != step_opplans.end(); ++i)
  {
    // We need to set the owner to NULL first to prevent the sub-operationplan
    // from RE-deleting its parent.
    (*i)->owner = NULL;
    delete (*i);
  }
  step_opplans.clear();
}


DECLARE_EXPORT void OperationPlanRouting::setQuantity (double f, bool roundDown, bool update)
{
  // First the normal resizing
  OperationPlan::setQuantity(f,roundDown,update);

  // Apply the same size also to its children
  for (list<OperationPlan*>::const_iterator i = step_opplans.begin();
      i != step_opplans.end(); ++i)
  {
    (*i)->quantity = quantity;
    if (update) (*i)->resizeFlowLoadPlans();
  }
}


DECLARE_EXPORT void OperationPlanRouting::eraseSubOperationPlan(OperationPlan* o)
{
  step_opplans.remove(o);
}


DECLARE_EXPORT void OperationPlanRouting::setEnd(Date d)
{
  if (step_opplans.empty())
    OperationPlan::setEnd(d);
  else
  {
    // Move all sub-operationplans in an orderly fashion
    bool firstMove = true;
    for (list<OperationPlan*>::reverse_iterator i = step_opplans.rbegin();
        i != step_opplans.rend(); ++i)
    {
      if ((*i)->getDates().getEnd() > d || firstMove)
      {
        (*i)->setEnd(d);
        firstMove = false;
        d = (*i)->getDates().getStart();
      }
      else
        // There is sufficient slack in the routing
        break;
    }
    // Set the dates on the top operationplan
    setStartAndEnd(
      step_opplans.front()->getDates().getStart(),
      step_opplans.back()->getDates().getEnd()
    );
  }
}


DECLARE_EXPORT void OperationPlanRouting::setStart(Date d)
{
  if (step_opplans.empty())
    OperationPlan::setStart(d);
  else
  {
    // Move all sub-operationplans in an orderly fashion
    bool firstMove = true;
    for (list<OperationPlan*>::const_iterator i = step_opplans.begin();
        i != step_opplans.end(); ++i)
    {
      if ((*i)->getDates().getStart() < d || firstMove)
      {
        (*i)->setStart(d);
        firstMove = false;
        d = (*i)->getDates().getEnd();
      }
      else
        // There is sufficient slack in the routing
        break;
    }
    // Set the dates on the top operationplan
    setStartAndEnd(
      step_opplans.front()->getDates().getStart(),
      step_opplans.back()->getDates().getEnd()
    );
  }
}


DECLARE_EXPORT void OperationPlanRouting::update()
{
  if (!step_opplans.empty())
    // Set the dates on the top operationplan
    setStartAndEnd(
      step_opplans.front()->getDates().getStart(),
      step_opplans.back()->getDates().getEnd()
    );
  OperationPlan::update();
}


DECLARE_EXPORT bool OperationPlanRouting::initialize()
{
  // Create step suboperationplans if they don't exist yet.
  if (step_opplans.empty())
  {
    Date d = getDates().getEnd();
    OperationPlan *p = NULL;
    if (d)
    {
      // Using the end date
      for (Operation::Operationlist::const_reverse_iterator e =
            getOperation()->getSubOperations().rbegin();
          e != getOperation()->getSubOperations().rend(); ++e)
      {
        p = (*e)->createOperationPlan(getQuantity(), Date::infinitePast,
            d, NULL, this, 0, true);
        d = p->getDates().getStart();
      }
    }
    else
    {
      // Using the start date when there is no end date
      d = getDates().getStart();
      // Using the current date when both the start and end date are missing
      if (!d) d = Plan::instance().getCurrent();
      for (Operation::Operationlist::const_iterator e =
            getOperation()->getSubOperations().begin();
          e != getOperation()->getSubOperations().end(); ++e)
      {
        p = (*e)->createOperationPlan(getQuantity(), d,
            Date::infinitePast, NULL, this, 0, true);
        d = p->getDates().getEnd();
      }
    }
  }

  // Initialize the suboperationplans
  for (list<OperationPlan*>::const_iterator i = step_opplans.begin();
      i != step_opplans.end(); ++i)
    (*i)->initialize();

  // Initialize myself
  return OperationPlan::initialize();
}


DECLARE_EXPORT void OperationPlanAlternate::addSubOperationPlan(OperationPlan* o)
{
  // The sub opplan must point to this operationplan
  assert(o->getOwner() == this);

  // Add in the list
  altopplan = o;

  // Update the top operationplan
  setStartAndEnd(
    altopplan->getDates().getStart(),
    altopplan->getDates().getEnd()
  );

  // Update the flow and loadplans
  update();
}


DECLARE_EXPORT OperationPlanAlternate::~OperationPlanAlternate()
{
  if (!altopplan) return;
  altopplan->owner = NULL;
  delete altopplan;
}


DECLARE_EXPORT void OperationPlanAlternate::setEnd(Date d)
{
  if (!altopplan) return;
  altopplan->setEnd(d);
  setStartAndEnd(
    altopplan->getDates().getStart(),
    altopplan->getDates().getEnd()
  );
}


DECLARE_EXPORT void OperationPlanAlternate::setStart(Date d)
{
  if (!altopplan) return;
  altopplan->setStart(d);
  setStartAndEnd(
    altopplan->getDates().getStart(),
    altopplan->getDates().getEnd()
  );
}


DECLARE_EXPORT void OperationPlanAlternate::update()
{
  if (altopplan)
    setStartAndEnd(
      altopplan->getDates().getStart(),
      altopplan->getDates().getEnd()
    );
  OperationPlan::update();
}


DECLARE_EXPORT bool OperationPlanAlternate::initialize()
{
  // Create an alternate suboperationplan if one doesn't exist yet.
  // We use the first alternate by default.
  if (!altopplan && !getOperation()->getSubOperations().empty())
  {
    altopplan = getOperation()->getSubOperations().front()->
      createOperationPlan(getQuantity(), getDates().getStart(),
      getDates().getEnd(), NULL, this, 0, true);
  }

  // Initialize this operationplan and its child
  if (altopplan) altopplan->initialize();
  return OperationPlan::initialize();
}


DECLARE_EXPORT void OperationPlanAlternate::setQuantity(double f, bool roundDown, bool update)
{
  // First the normal resizing
  OperationPlan::setQuantity(f,roundDown,update);

  // Apply the same size also to the children operationplan
  if (altopplan)
  {
    altopplan->quantity = quantity;
    if (update) altopplan->resizeFlowLoadPlans();
  }
}


DECLARE_EXPORT void OperationPlanAlternate::eraseSubOperationPlan(OperationPlan* o)
{
  if (altopplan == o)
    altopplan = NULL;
  else if (o)
    logger << "Warning: Trying to remove a sub operationplan '"
      << *(o->getOperation()) << "' that is not registered with"
      << " its parent '" << *getOperation() << "'" << endl;
}


int PythonOperationPlan::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = getType();
  x.setName("operationplan");
  x.setDoc("frePPLe operationplan");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  const_cast<MetaCategory&>(OperationPlan::metadata).factoryPythonProxy = proxy;
  return x.typeReady(m);
}


PyObject* PythonOperationPlan::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Find or create the C++ object
    PythonAttributeList atts(kwds);
    Object* x = OperationPlan::createOperationPlan(OperationPlan::metadata,atts);

    // Create a python proxy
    PythonExtensionBase* pr = static_cast<PythonExtensionBase*>(static_cast<PyObject*>(*(new PythonObject(x))));

    // Iterate over extra keywords, and set attributes.   @todo move this responsability to the readers...
    if (x) 
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonObject field(value);
        Attribute attr(PyString_AsString(key));
        if (!attr.isA(Tags::tag_operation) && !attr.isA(Tags::tag_id) && !attr.isA(Tags::tag_action))
        {
          int result = pr->setattro(attr, field);
          if (result)
            PyErr_Format(PyExc_AttributeError,
              "attribute '%s' on '%s' can't be updated",
              PyString_AsString(key), pr->ob_type->tp_name);
        }
      };
    }

    if (x && !static_cast<OperationPlan*>(x)->initialize()) 
      static_cast<PythonOperationPlan*>(pr)->obj = NULL;
    return pr;
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
}


DECLARE_EXPORT PyObject* PythonOperationPlan::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_id))
    return PythonObject(obj->getIdentifier());
  if (attr.isA(Tags::tag_operation))
    return PythonObject(obj->getOperation());
  if (attr.isA(Tags::tag_quantity))
    return PythonObject(obj->getQuantity());
  if (attr.isA(Tags::tag_start))
    return PythonObject(obj->getDates().getStart());
  if (attr.isA(Tags::tag_end))
    return PythonObject(obj->getDates().getEnd());
  if (attr.isA(Tags::tag_demand))
    return PythonObject(obj->getDemand());
  if (attr.isA(Tags::tag_locked))
    return PythonObject(obj->getLocked());
  if (attr.isA(Tags::tag_owner))
    return PythonObject(obj->getOwner());
  if (attr.isA(Tags::tag_hidden))
    return PythonObject(obj->getHidden());
  return NULL;
}


DECLARE_EXPORT int PythonOperationPlan::setattro(const Attribute& attr, const PythonObject& field)
{
  if (!obj) return -1;
  if (attr.isA(Tags::tag_quantity))
    obj->setQuantity(field.getDouble());
  else if (attr.isA(Tags::tag_start))
    obj->setStart(field.getDate());
  else if (attr.isA(Tags::tag_end))
    obj->setEnd(field.getDate());
  else if (attr.isA(Tags::tag_locked))
    obj->setLocked(field.getBool());
  else if (attr.isA(Tags::tag_demand))
  {
    if (!field.check(PythonDemand::getType())) 
    {
      PyErr_SetString(PythonDataException, "operationplan demand must be of type demand");
      return -1;
    }
    Demand* y = static_cast<PythonDemand*>(static_cast<PyObject*>(field))->obj;
    obj->setDemand(y);
  }
  else if (attr.isA(Tags::tag_owner))
  {
    if (!field.check(PythonOperationPlan::getType())) 
    {
      PyErr_SetString(PythonDataException, "operationplan demand must be of type demand");
      return -1;
    }
    OperationPlan* y = static_cast<PythonOperationPlan*>(static_cast<PyObject*>(field))->obj;
    obj->setOwner(y);
  }
  else
    return -1;
  return 0;  
}

} // end namespace
