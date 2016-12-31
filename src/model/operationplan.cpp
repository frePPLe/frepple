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

const MetaClass* OperationPlan::metadata;
const MetaCategory* OperationPlan::metacategory;
unsigned long OperationPlan::counterMin = 2;

Location* OperationPlan::loc = NULL;
Location* OperationPlan::ori = NULL;
Supplier* OperationPlan::sup = NULL;
string OperationPlan::ordertype;
Item* OperationPlan::itm = NULL;

int OperationPlan::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<OperationPlan>(
    "operationplan", "operationplans", createOperationPlan, OperationPlan::finder
    );
  OperationPlan::metadata = MetaClass::registerClass<OperationPlan>("operationplan", "operationplan", true);
  registerFields<OperationPlan>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python type
  PythonType& x = FreppleCategory<OperationPlan>::getPythonType();
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


void OperationPlan::setChanged(bool b)
{
  if (owner)
    owner->setChanged(b);
  else
  {
    oper->setChanged(b);
    if (dmd) dmd->setChanged();
  }
}


Object* OperationPlan::createOperationPlan(
  const MetaClass* cat, const DataValueDict& in, CommandManager* mgr
  )
{
  // Pick up the action attribute
  Action action = MetaClass::decodeAction(in);

  // Check the order type
  string ordtype;
  const DataValue* ordtypeval = in.get(Tags::ordertype);
  if (ordtypeval)
    ordtype = ordtypeval->getString();
  
  // Decode the attributes
  Object *oper = nullptr;
  Object *itemval = nullptr;
  Object *locval = nullptr;
  Object *supval = nullptr;
  Object *orival = nullptr;
  Object *dmdval = nullptr;
  if (ordtype == "MO" || ordtype.empty())
  {
    const DataValue* val = in.get(Tags::operation);
    if (!val && action == ADD)
      throw DataException("Missing operation field");
    if (val)
    {
      oper = val->getObject();
      if (oper && oper->getType().category != Operation::metadata)
        throw DataException("Operation field on operationplan must be of type operation");
    }
  }
  else if (ordtype == "PO")
  {
    const DataValue* val = in.get(Tags::supplier);
    if (!val && action == ADD)
      throw DataException("Missing supplier field");
    if (val)
    {
      supval = val->getObject();
      if (supval && supval->getType().category != Supplier::metadata)
        throw DataException("Supplier field on operationplan must be of type supplier");
    }
    val = in.get(Tags::item);
    if (!val && action == ADD)
      throw DataException("Missing item field");
    if (val)
    {
      itemval = val->getObject();
      if (itemval && itemval->getType().category != Item::metadata)
        throw DataException("Item field on operationplan must be of type item");
    }
    val = in.get(Tags::location);
    if (!val && action == ADD)
      throw DataException("Missing location field");
    if (val)
    {
      locval = val->getObject();
      if (locval && locval->getType().category != Location::metadata)
        throw DataException("Location field on operationplan must be of type location");
    }
  }
  else if (ordtype == "DO")
  {
    const DataValue* val = in.get(Tags::origin);
    if (!val && action == ADD)
      throw DataException("Missing origin field");
    if (val)
    {
      orival = val->getObject();
      if (orival && orival->getType().category != Location::metadata)
        throw DataException("Origin field on operationplan must be of type location");
    }
    val = in.get(Tags::item);
    if (!val && action == ADD)
      throw DataException("Missing item field");
    if (val)
    {
      itemval = val->getObject();
      if (itemval && itemval->getType().category != Item::metadata)
        throw DataException("Item field on operationplan must be of type item");
    }
    val = in.get(Tags::location);
    if (!val && action == ADD)
      throw DataException("Missing location field");
    if (val)
    {
      locval = val->getObject();
      if (locval && locval->getType().category != Location::metadata)
        throw DataException("Location field on operationplan must be of type location");
    }
  }
  else if (ordtype == "DLVR")
  {
    const DataValue* val = in.get(Tags::demand);
    if (!val && action == ADD)
      throw DataException("Missing demand field");
    if (val)
    {
      dmdval = val->getObject();      
      if (!dmdval)
        throw DataException("Empty demand field");
      else if (dmdval->getType().category != Demand::metadata)
      {
        Demand* tmp = dynamic_cast<Demand*>(dmdval);
        if (!tmp)
          throw DataException("Demand field on operationplan must be of type demand");
      }
    }
    val = in.get(Tags::item);
    if (!val && action == ADD)
      throw DataException("Missing item field");
    if (val)
    {
      itemval = val->getObject();
      if (itemval && itemval->getType().category != Item::metadata)
        throw DataException("Item field on operationplan must be of type item");
    }
    val = in.get(Tags::location);
    if (!val && action == ADD)
      throw DataException("Missing location field");
    if (val)
    {
      locval = val->getObject();
      if (locval && locval->getType().category != Location::metadata)
        throw DataException("Location field on operationplan must be of type location");
    }
  }
  else
    // Unknown order type for operationplan. We won't read it.
    return nullptr; 

  // Decode the operationplan identifier
  unsigned long id = 0;
  const DataValue* idfier = in.get(Tags::id);
  if (idfier)
    id = idfier->getUnsignedLong();
  if (!id && (action==CHANGE || action==REMOVE))
    // Identifier is required
    throw DataException("Missing identifier field");

  // If an identifier is specified, we look up this operation plan
  OperationPlan* opplan = nullptr;
  if (id)
  {
    if (id == ULONG_MAX)
    {
      ostringstream ch;
      ch << "Operationplan id can't be equal to " << ULONG_MAX;
      throw DataException(ch.str());
    }
    opplan = OperationPlan::findId(id);
    if (opplan)
    {
      // Check whether previous and current operations match.
      if (ordtype.empty())
        ordtype = opplan->getOrderType();
      else if (ordtype != opplan->getOrderType())
      {
        ostringstream ch;
        ch << "Operationplan identifier " << id
          << " defined multiple times for different order types";
        throw DataException(ch.str());
      }
      if (!ordtype.empty() && ordtype == "MO" && oper && opplan->getOperation() != static_cast<Operation*>(oper))
      {
        ostringstream ch;
        ch << "Operationplan identifier " << id
          << " defined multiple times for different operations";
        throw DataException(ch.str());
      }
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
      return nullptr;
    case ADD:
      if (opplan)
      {
        ostringstream ch;
        ch << "Operationplan with identifier " << id
            << " already exists and can't be added again";
        throw DataException(ch.str());
      }
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

  // Get start, end, quantity and status fields
  const DataValue* startfld = in.get(Tags::start);
  Date start;
  if (startfld)
    start = startfld->getDate();
  const DataValue* endfld = in.get(Tags::end);
  Date end;
  if (endfld)
    end = endfld->getDate();
  const DataValue* quantityfld = in.get(Tags::quantity);
  double quantity = quantityfld ? quantityfld->getDouble() : 0.0;
  const DataValue* statusfld = in.get(Tags::status);

  // Return the existing operationplan
  if (opplan)
  {
    if (quantityfld || startfld || endfld)
      opplan->getOperation()->setOperationPlanParameters(
        opplan, quantityfld ? quantity : opplan->getQuantity(),
        start, end
      );
    return opplan;
  }

  // Create a new operation plan
  if (ordtype == "PO")
  {
    // Find or create the destination buffer.
    if (!itemval)
      throw DataException("Missing item field");
    if (!locval)
      throw DataException("Missing location field");
    Buffer* destbuffer = nullptr;
    Item::bufferIterator buf_iter(static_cast<Item*>(itemval));
    while (Buffer* tmpbuf = buf_iter.next())
    {
      if (tmpbuf->getLocation() == static_cast<Location*>(locval))
      {
        if (destbuffer)
        {
          stringstream o;
          o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "'' and location'" << static_cast<Location*>(locval) << "'";
          throw DataException(o.str());
        }
        destbuffer = tmpbuf;
      }
    }
    if (!destbuffer)
      // Create the destination buffer
      destbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval), static_cast<Location*>(locval));

    // Build the producing operation for this buffer.
    destbuffer->getProducingOperation();

    // Look for a matching operation replenishing this buffer.
    for (Buffer::flowlist::const_iterator flowiter = destbuffer->getFlows().begin();
      flowiter != destbuffer->getFlows().end() && !oper; ++flowiter)
    {
      if (flowiter->getOperation()->getType() != *OperationItemSupplier::metadata)
        continue;
      OperationItemSupplier* opitemsupplier = static_cast<OperationItemSupplier*>(flowiter->getOperation());
      if (supval)
      {
        if (static_cast<Supplier*>(supval)->isMemberOf(opitemsupplier->getItemSupplier()->getSupplier()))
          oper = opitemsupplier;
      }
      else
        oper = opitemsupplier;
    }

    // No matching operation is found.
    if (!oper)
    {
      // We'll create one now, but that requires that we have a supplier defined.
      if (!supval)
        throw DataException("Supplier is needed on this purchase order");
      // Note: We know that we need to create a new one. An existing one would
      // have created an operation on the buffer already.
      ItemSupplier *itemsupplier = new ItemSupplier();
      itemsupplier->setSupplier(static_cast<Supplier*>(supval));
      itemsupplier->setItem(static_cast<Item*>(itemval));
      itemsupplier->setLocation(static_cast<Location*>(locval));
      itemsupplier->setHidden(true);
      itemsupplier->setPriority(0);
      oper = new OperationItemSupplier(itemsupplier, destbuffer);
      // Create operation plan
      opplan = static_cast<Operation*>(oper)->createOperationPlan(quantity, start, end);
      new ProblemInvalidData(
        opplan, 
        "Purchase orders on unauthorized supplier", "operationplan",
        start, end, quantity
        );
    }
    else
      // Create the operationplan
      opplan = static_cast<Operation*>(oper)->createOperationPlan(quantity, start, end);

    // Set operationplan fields
    if (id)
      opplan->setRawIdentifier(id);  // We can use this fast method because we call activate later
    if (statusfld)
      opplan->setStatus(statusfld->getString());
    // Reset quantity after the status update to assure that
    // also non-valid quantities are getting accepted.
    opplan->setQuantity(quantity);
    opplan->activate();
  }
  else if (ordtype == "DO")
  {
    // Find or create the destination buffer.
    if (!itemval)
      throw DataException("Missing item field");
    if (!locval)
      throw DataException("Missing location field");
    Buffer* destbuffer = nullptr;
    Item::bufferIterator buf_iter(static_cast<Item*>(itemval));
    while (Buffer* tmpbuf = buf_iter.next())
    {
      if (tmpbuf->getLocation() == static_cast<Location*>(locval))
      {
        if (destbuffer)
        {
          stringstream o;
          o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "'' and location '" << static_cast<Location*>(locval) << "'";
          throw DataException(o.str());
        }
        destbuffer = tmpbuf;
      }
    }
    if (!destbuffer)
      // Create the destination buffer
      destbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval), static_cast<Location*>(locval));

    // Build the producing operation for this buffer.
    destbuffer->getProducingOperation();

    // Look for a matching operation replenishing this buffer.
    for (Buffer::flowlist::const_iterator flowiter = destbuffer->getFlows().begin();
      flowiter != destbuffer->getFlows().end() && !oper; ++flowiter)
    {
      if (flowiter->getOperation()->getType() != *OperationItemDistribution::metadata
        || flowiter->getQuantity() <= 0)
        continue;
      OperationItemDistribution* opitemdist = static_cast<OperationItemDistribution*>(flowiter->getOperation());
      if (orival)
      {
        // Origin must match as well
        for (Operation::flowlist::const_iterator fl = opitemdist->getFlows().begin();
          fl != opitemdist->getFlows().end(); ++fl)
        {
          if (fl->getQuantity() < 0 && fl->getBuffer()->getLocation()->isMemberOf(static_cast<Location*>(orival)))
            oper = opitemdist;
        }
      }
      else
        oper = opitemdist;
    }

    // No matching operation is found.
    if (!oper)
    {
      // We'll create one now, but that requires that we have an origin defined.
      if (!orival)
        throw DataException("Origin location is needed on this distribution order");
      Buffer* originbuffer = nullptr;
      for (Buffer::iterator bufiter = Buffer::begin(); bufiter != Buffer::end(); ++bufiter)
      {
        if (bufiter->getLocation() == static_cast<Location*>(orival) && bufiter->getItem() == static_cast<Item*>(itemval))
        {
          if (originbuffer)
          {
            stringstream o;
            o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "'' and location '" << static_cast<Location*>(orival) << "'";
            throw DataException(o.str());
          }
          originbuffer = &*bufiter;
        }
      }
      if (!originbuffer)
        // Create the origin buffer
        originbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval), static_cast<Location*>(orival));

      // Note: We know that we need to create a new one. An existing one would
      // have created an operation on the buffer already.
      ItemDistribution *itemdist = new ItemDistribution();
      itemdist->setOrigin(static_cast<Location*>(orival));
      itemdist->setItem(static_cast<Item*>(itemval));
      itemdist->setDestination(static_cast<Location*>(locval));
      itemdist->setPriority(0);
      oper = new OperationItemDistribution(itemdist, originbuffer, destbuffer);
      // Create operation plan
      opplan = static_cast<Operation*>(oper)->createOperationPlan(quantity, start, end, nullptr, nullptr, 0, false);
      new ProblemInvalidData(opplan, "Distribution orders on unauthorized lanes", "operationplan",
        start, end, quantity);
    }
    else
      // Create operation plan
      opplan = static_cast<Operation*>(oper)->createOperationPlan(quantity, start, end, nullptr, nullptr, 0, false);

    // Set operationplan fields
    if (id)
      opplan->setRawIdentifier(id);  // We can use this fast method because we call activate later
    if (statusfld)
      opplan->setStatus(statusfld->getString());
    // Reset quantity after the status update to assure that
    // also non-valid quantities are getting accepted.
    opplan->setQuantity(quantity);
    opplan->activate();
  }
  else if (ordtype == "DLVR")
  {
    // Find or create the destination buffer.
    if (!itemval)
      throw DataException("Missing item field");
    if (!locval)
      throw DataException("Missing location field");
    Buffer* destbuffer = nullptr;
    Item::bufferIterator buf_iter(static_cast<Item*>(itemval));
    while (Buffer* tmpbuf = buf_iter.next())
    {
      if (tmpbuf->getLocation() == static_cast<Location*>(locval))
      {
        if (destbuffer)
        {
          stringstream o;
          o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "'' and location '" << static_cast<Location*>(locval) << "'";
          throw DataException(o.str());
        }
        destbuffer = tmpbuf;
      }
    }
    if (!destbuffer)
      // Create the destination buffer
      destbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval), static_cast<Location*>(locval));
    
    // Create new operation if not found
    oper = Operation::find("Ship " + string(destbuffer->getName()));
    if (!oper)
      oper = new OperationDelivery(destbuffer);

    // Create operation plan
    opplan = static_cast<Operation*>(oper)->createOperationPlan(quantity, start, end);
    static_cast<Demand*>(dmdval)->addDelivery(opplan);

    // Set operationplan fields
    if (id)
      opplan->setRawIdentifier(id);  // We can use this fast method because we call activate later
    if (statusfld)
      opplan->setStatus(statusfld->getString());
    // Reset quantity after the status update to assure that
    // also non-valid quantities are getting accepted.
    opplan->setQuantity(quantity);
    opplan->activate();
  }
  else
  {
    if (!oper)
      // Can't create operationplan because the operation doesn't exist
      throw DataException("Missing operation field");

    // Create an operationplan
    opplan = static_cast<Operation*>(oper)->createOperationPlan(
      quantity, start, end, nullptr, nullptr, id, false
      );
    if (!opplan->getType().raiseEvent(opplan, SIG_ADD))
    {
      delete opplan;
      throw DataException("Can't create operationplan");
    }

    // Special case: if the operation plan is locked, we need to
    // process the start and end date before locking it.
    // Subsequent calls won't affect the operationplan any longer.    
    if (statusfld && statusfld->getString() != "proposed")
    {
      string status = statusfld->getString();
      if (start && end)
      {
        // Any start date, end date and quantity combination will be accepted
        opplan->setStatus(status);
        opplan->freezeStatus(start, end, quantity);
      }
      else
        opplan->setStatus(status);
    }
    opplan->activate();

    // Report the operationplan creation to the manager
    if (mgr)
        mgr->add(new CommandCreateObject(opplan));
  }
  return opplan;
}


OperationPlan* OperationPlan::findId(unsigned long l)
{
  // We are garantueed that there are no operationplans that have an id equal
  // or higher than the current counter. This is garantueed by the
  // instantiate() method.
  if (l >= counterMin) return nullptr;

  // Loop through all operationplans.
  for (OperationPlan::iterator i = begin(); i != end(); ++i)
    if (i->id == l) return &*i;

  // This ID was not found
  return nullptr;
}


bool OperationPlan::assignIdentifier()
{
  // Need to assure that ids are unique!
  static mutex onlyOne;  
  if (id && id != ULONG_MAX)
  {
    // An identifier was read in from input
    lock_guard<mutex> l(onlyOne);  
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
  else {
    // Fresh operationplan with blank id
    lock_guard<mutex> l(onlyOne);  // Need to assure that ids are unique!
    id = counterMin++;
  }

  // Check whether the counter is still okay
  if (counterMin >= ULONG_MAX)
    throw RuntimeException("Exhausted the range of available operationplan identifiers");

  return true;
}


bool OperationPlan::activate()
{
  // At least a valid operation pointer must exist
  if (!oper)
    throw LogicException("Initializing an invalid operationplan");

  // Avoid negative quantities, and call operation specific activation code
  if (getQuantity() < 0.0 || !oper->extraInstantiate(this))
  {
    delete this;
    return false;
  }

  // Instantiate all suboperationplans as well
  OperationPlan::iterator x(this);
  if (x != end())
  {
    while (x != end()) {
      OperationPlan* tmp = &*x;
      ++x;
      tmp->activate();
    }
    x = this;
    if (x == end()) {
      delete this;
      return false;
    }
  }

  // Mark as activated by assigning a unique identifier.
  if (id && id != ULONG_MAX)
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


void OperationPlan::deactivate()
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


void OperationPlan::insertInOperationplanList()
{

  // Check if already linked, or nothing to link
  if (prev || !oper || oper->first_opplan == this)
    return;

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
    OperationPlan *y = nullptr;
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


void OperationPlan::removeFromOperationplanList()
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
  prev = nullptr;
  next = nullptr;
}


void OperationPlan::updateOperationplanList()
{
  if (!oper) return;

  // Check ordering on the left
  while (prev && !(*prev < *this))
  {
    OperationPlan* n = next;
    OperationPlan* p = prev;
    if (p->prev)
      p->prev->next = this;
    else
      oper->first_opplan = this;
    p->next = n;
    next = p;
    prev = p->prev;
    if (n)
      n->prev = p;
    else
      oper->last_opplan = p;
    p->prev = this;
  }

  // Check ordering on the right
  while (next && !(*this < *next))
  {
    OperationPlan* n = next;
    OperationPlan* p = prev;
    next = n->next;
    if (n->next)
      n->next->prev = this;
    else
      oper->last_opplan = this;
    if (p)
      p->next = n;
    else
      oper->first_opplan = n;
    n->next = this;
    n->prev = p;
    prev = n;
  }
}


void OperationPlan::eraseSubOperationPlan(OperationPlan* o)
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
  o->owner = nullptr;
  prevsubopplan = nullptr;
  nextsubopplan = nullptr;
};


bool OperationPlan::operator < (const OperationPlan& a) const
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


void OperationPlan::createFlowLoads()
{
  // Initialized already, or nothing to initialize
  if (firstflowplan || firstloadplan || !oper)
    return;

  // Create setup suboperationplans and loadplans
  for (Operation::loadlist::const_iterator g=oper->getLoads().begin();
      g!=oper->getLoads().end(); ++g)
    if (!g->getAlternate())
    {
      new LoadPlan(this, &*g);
      if (!g->getSetup().empty() && g->getResource()->getSetupMatrix())
        OperationSetup::setupoperation->createOperationPlan(
          1, getDates().getStart(), getDates().getStart(), nullptr, this);
    }

  // Create flowplans for flows
  for (Operation::flowlist::const_iterator h=oper->getFlows().begin();
      h!=oper->getFlows().end(); ++h)
  {
    if (!h->getAlternate())
      // Only the primary flow is instantiated.
      // Flow creation can also be explicitly switched off.
      new FlowPlan(this, &*h);
  }
}


void OperationPlan::deleteFlowLoads()
{
  // If no flowplans and loadplans, the work is already done
  if (!firstflowplan && !firstloadplan) return;

  FlowPlanIterator e = beginFlowPlans();
  firstflowplan = nullptr;    // Important to do this before the delete!
  LoadPlanIterator f = beginLoadPlans();
  firstloadplan = nullptr;  // Important to do this before the delete!

  // Delete the flowplans
  while (e != endFlowPlans())
    delete &*(e++);

  // Delete the loadplans (including the setup suboperationplan)
  while (f != endLoadPlans())
    delete &*(f++);
}


double OperationPlan::getTotalFlowAux(const Buffer* b) const
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


OperationPlan::~OperationPlan()
{
  // Delete the flowplans and loadplan
  deleteFlowLoads();

  // Initialize
  OperationPlan *x = firstsubopplan;
  firstsubopplan = nullptr;
  lastsubopplan = nullptr;

  // Delete the sub operationplans
  while (x)
  {
    OperationPlan *y = x->nextsubopplan;
    x->owner = nullptr; // Need to clear before destroying the suboperationplan
    delete x;
    x = y;
  }

  // Delete also the owner
  if (owner)
  {
    const OperationPlan* o = owner;
    setOwner(nullptr);
    delete o;
  }

  // Delete from the list of deliveries
  if (dmd) dmd->removeDelivery(this);

  // Delete from the operationplan list
  removeFromOperationplanList();
}


void OperationPlan::setOwner(OperationPlan* o, bool fast)
{
  // Special case: the same owner is set twice
  if (owner == o) return;
  if (o)
    // Register with the new owner
    o->getOperation()->addSubOperationPlan(o, this, fast);
  else if (owner)
    // Setting the owner field to nullptr
    owner->eraseSubOperationPlan(this);
}


void OperationPlan::setStart (Date d)
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
      if (i->getOperation() == OperationSetup::setupoperation)
        continue;
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


void OperationPlan::setEnd(Date d)
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
      if (!i->getDates().getEnd() || i->getDates().getEnd() > d)
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


void OperationPlan::resizeFlowLoadPlans()
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


OperationPlan::OperationPlan(const OperationPlan& src, bool init)
{
  if (src.owner)
    throw LogicException("Can't copy suboperationplans. Copy the owner instead.");

  // Identifier and reference aren't inherited.
  // A new identifier will be generated when we activate the operationplan.
  // The reference remains blank.
  id = 0;

  // Copy the fields
  quantity = src.quantity;
  flags = src.flags;
  dmd = src.dmd;
  oper = src.oper;
  firstflowplan = nullptr;
  firstloadplan = nullptr;
  dates = src.dates;
  prev = nullptr;
  next = nullptr;
  owner = nullptr;
  firstsubopplan = nullptr;
  lastsubopplan = nullptr;
  nextsubopplan = nullptr;
  prevsubopplan = nullptr;
  initType(metadata);

  // Clone the suboperationplans
  for (OperationPlan::iterator x(&src); x != end(); ++x)
    new OperationPlan(*x, this);

  // Activate
  if (init) activate();
}


OperationPlan::OperationPlan(const OperationPlan& src,
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
  firstflowplan = nullptr;
  firstloadplan = nullptr;
  dates = src.dates;
  prev = nullptr;
  next = nullptr;
  owner = nullptr;
  firstsubopplan = nullptr;
  lastsubopplan = nullptr;
  nextsubopplan = nullptr;
  prevsubopplan = nullptr;
  initType(metadata);

  // Set owner
  setOwner(newOwner);

  // Clone the suboperationplans
  for (OperationPlan::iterator x(&src); x != end(); ++x)
    new OperationPlan(*x, this);
}


void OperationPlan::update()
{
  if (lastsubopplan && lastsubopplan->getOperation() != OperationSetup::setupoperation)
  {
    // Set the start and end date of the parent.
    Date st = Date::infiniteFuture;
    Date nd = Date::infinitePast;
    for (OperationPlan *f = firstsubopplan; f; f = f->nextsubopplan)
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

  // Keep the operationplan list sorted
  updateOperationplanList();

  // Notify the owner operationplan
  if (owner)
    owner->update();

  // Mark as changed
  setChanged();
}


void OperationPlan::deleteOperationPlans(Operation* o, bool deleteLockedOpplans)
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


double OperationPlan::getPenalty() const
{
  double penalty = 0;
  for (OperationPlan::LoadPlanIterator i = beginLoadPlans();
      i != endLoadPlans(); ++i)
    if (i->isStart() && !i->getLoad()->getSetup().empty() && i->getResource()->getSetupMatrix())
    {
      SetupMatrixRule *rule = i->getResource()->getSetupMatrix()
          ->calculateSetup(i->getSetup(false), i->getSetup(true));
      if (rule) penalty += rule->getCost();
    }
  return penalty;
}


bool OperationPlan::isExcess(bool strict) const
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
      if (j->getEventType() == 4 && !strict)
        current_maximum = j->getMax(false);
      if (j->getEventType() == 3 && !strict)
        current_minimum = j->getMin(false);
      if (&*j == &*i) break;
    }
  }

  // Handle operationplan already being deleted by a deleteOperation command
  if (!hasFlowplans && getOperation()->getFlows().begin() != getOperation()->getFlows().end())
    return false;

  // If we remove this operationplan the onhand in all buffers remains positive.
  return true;
}


Duration OperationPlan::getUnavailable() const
{
  Duration x;
  getOperation()->calculateOperationTime(dates.getStart(), dates.getEnd(), &x);
  return dates.getDuration() - x;
}


Object* OperationPlan::finder(const DataValueDict& key)
{
  const DataValue* val = key.get(Tags::id);
  return val ?
    OperationPlan::findId(val->getUnsignedLong()) :
    nullptr;
}


void OperationPlan::setConfirmed(bool b)
{
  if (b)
  {
    flags |= STATUS_CONFIRMED;
    flags &= ~STATUS_APPROVED;
  }
  else
  {
    flags &= ~STATUS_CONFIRMED;
    flags |= STATUS_APPROVED;
  }
  for (OperationPlan *x = firstsubopplan; x; x = x->nextsubopplan)
    x->setConfirmed(b);
  update();
}


void OperationPlan::setApproved(bool b)
{
  if (b)
  {
    flags |= STATUS_CONFIRMED;
    flags &= ~STATUS_APPROVED;
  }
  else
  {
    flags &= ~STATUS_CONFIRMED;
    flags |= STATUS_APPROVED;
  }
  for (OperationPlan *x = firstsubopplan; x; x = x->nextsubopplan)
    x->setApproved(b);
  update();
}


void OperationPlan::setProposed(bool b)
{
  if (b)
  {
    flags &= ~STATUS_CONFIRMED;
    flags &= ~STATUS_APPROVED;
  }
  else
  {
    flags &= ~STATUS_CONFIRMED;
    flags |= STATUS_APPROVED;
  }
  for (OperationPlan *x = firstsubopplan; x; x = x->nextsubopplan)
    x->setProposed(b);
  update();
}


string OperationPlan::getStatus() const
{
  if (flags & STATUS_APPROVED)
    return "approved";
  else if (flags & STATUS_CONFIRMED)
    return "confirmed";
  else
    return "proposed";
}


bool OperationPlan::isConstrained() const
{
  for (PeggingIterator p(this); p; ++p)
  {
    const OperationPlan* m = p.getOperationPlan();
    Demand* dmd = m ? m->getTopOwner()->getDemand() : nullptr;
    if (dmd && dmd->getDue() < m->getEnd())
      return true;
  }
  return false;
}


void OperationPlan::setStatus(const string& s)
{
  if (s == "approved")
  {
    flags |= STATUS_APPROVED;
    flags &= ~STATUS_CONFIRMED;
  }
  else if (s == "confirmed")
  {
    flags |= STATUS_CONFIRMED;
    flags &= ~STATUS_APPROVED;
  }
  else if (s == "proposed")
  {
    flags &= ~STATUS_APPROVED;
    flags &= ~STATUS_CONFIRMED;
  }
  else
    throw DataException("invalid operationplan status:" + s);
  update();
  for (OperationPlan *x = firstsubopplan; x; x = x->nextsubopplan)
    x->setStatus(s);
}


void OperationPlan::freezeStatus(Date st, Date nd, double q)
{
  if (!getLocked()) return;
  dates = DateRange(st, nd);
  quantity = q > 0 ? q : 0.0;
}


void OperationPlan::setDemand(Demand* l)
{
  // No change
  if (l == dmd)
    return;

  // Unregister from previous demand
  if (dmd)
    dmd->removeDelivery(this);

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
    PythonDataValueDict atts(kwds);
    Object* x = createOperationPlan(OperationPlan::metadata, atts);
    Py_INCREF(x);

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (x)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::operation) && !attr.isA(Tags::id)
          && !attr.isA(Tags::action) && !attr.isA(Tags::type)
          && !attr.isA(Tags::start) && !attr.isA(Tags::end)
          && !attr.isA(Tags::quantity))
        {
          const MetaFieldBase* fmeta = x->getType().findField(attr.getHash());
          if (!fmeta && x->getType().category)
            fmeta = x->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(x, field);
          else
            x->setProperty(attr.getName(), value);
        }
      };
    }
    return x;
  }
  catch (...)
  {
    PythonType::evalException();
    return nullptr;
  }
}


double OperationPlan::getCriticality() const
{
  // Operationplan hasn't been set up yet
  if (!oper)
    return 86313600L; // 999 days in seconds;

  // Child operationplans have the same criticality as the parent
  // TODO: Slack between routing sub operationplans isn't recognized.
  if (getOwner() && getOwner()->getOperation()->getType() != *OperationSplit::metadata)
    return getOwner()->getCriticality();

  // Handle demand delivery operationplans
  if (getTopOwner()->getDemand())
  {

    long early = getTopOwner()->getDemand()->getDue() - getDates().getEnd();
    return ((early<=0L) ? 0.0 : early) / 86400.0; // Convert to days
  }

  // Handle an upstream operationplan
  Duration minslack = 86313600L; // 999 days in seconds
  vector<const OperationPlan*> opplans(HasLevel::getNumberOfLevels() + 5);
  for (PeggingIterator p(const_cast<OperationPlan*>(this)); p; ++p)
  {
    unsigned int lvl = p.getLevel();
    if (lvl >= opplans.size())
      opplans.resize(lvl + 5);
    opplans[lvl] = p.getOperationPlan();
    const OperationPlan* m = p.getOperationPlan();
    if (m && m->getTopOwner()->getDemand())
    {
      // Reached a demand. Get the total slack now.
      Duration myslack = m->getTopOwner()->getDemand()->getDue() - m->getDates().getEnd();
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


Duration OperationPlan::getDelay() const
{
  // Operationplan hasn't been set up yet. On time by default. 
  if (!oper)
    return 0L;

  // Child operationplans have the same delay as the parent
  // TODO for routing steps this is not really as accurrate as we could do it
  if (getOwner() && getOwner()->getOperation()->getType() != *OperationSplit::metadata)
    return getOwner()->getDelay();

  // Handle demand delivery operationplans
  if (getTopOwner()->getDemand())
    return getDates().getEnd() - getTopOwner()->getDemand()->getDue();

  // Handle an upstream operationplan
  Duration maxdelay = Duration::MIN;
  vector<const OperationPlan*> opplans(HasLevel::getNumberOfLevels() + 5);
  for (PeggingIterator p(const_cast<OperationPlan*>(this)); p; ++p)
  {
    unsigned int lvl = p.getLevel();
    if (lvl >= opplans.size())
      opplans.resize(lvl + 5);
    opplans[lvl] = p.getOperationPlan();
    const OperationPlan* m = p.getOperationPlan();
    if (m && m->getTopOwner()->getDemand())
    {
      // Reached a demand. Get the total slack now.
      Duration mydelay = getDates().getEnd() - m->getTopOwner()->getDemand()->getDue();
      for (unsigned int i = 0; i < lvl; i++)
      {
        if (opplans[i]->getOwner())
          // Don't count operation times on child operationplans
          continue;
        mydelay -= opplans[i]->getDates().getDuration();
      }
      if (mydelay > maxdelay)
        maxdelay = mydelay;
    }
  }
  return maxdelay;
}


PyObject* OperationPlan::createIterator(PyObject* self, PyObject* args)
{
  // Check arguments
  PyObject *pyoper = nullptr;
  int ok = PyArg_ParseTuple(args, "|O:operationplans", &pyoper);
  if (!ok)
    return nullptr;

  if (!pyoper)
    // First case: Iterate over all operationplans
    return new PythonIterator<OperationPlan::iterator, OperationPlan>();

  // Second case: Iterate over the operationplans of a single operation
  PythonData oper(pyoper);
  if (!oper.check(Operation::metadata))
  {
    PyErr_SetString(PythonDataException, "optional argument must be of type operation");
    return nullptr;
  }
  return new PythonIterator<OperationPlan::iterator, OperationPlan>(static_cast<Operation*>(pyoper));
}


PeggingIterator OperationPlan::getPeggingDownstream() const
{
  return PeggingIterator(this, true);
}


PeggingIterator OperationPlan::getPeggingUpstream() const
{
  return PeggingIterator(this, false);
}


PeggingDemandIterator OperationPlan::getPeggingDemand() const
{
  return PeggingDemandIterator(this);
}


} // end namespace
