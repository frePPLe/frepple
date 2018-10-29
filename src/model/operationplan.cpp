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

Tree<unsigned long> OperationPlan::st;

const MetaClass* OperationPlan::metadata;
const MetaCategory* OperationPlan::metacategory;
const MetaClass* OperationPlan::InterruptionIterator::metadata;
const MetaCategory* OperationPlan::InterruptionIterator::metacategory;
unsigned long OperationPlan::counterMin = 2;
bool OperationPlan::propagatesetups = true;


const MetaCategory* SetupEvent::metadata;


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
  x.addMethod(
    "calculateOperationTime", &calculateOperationTimePython, METH_VARARGS,
    "add or subtract a duration of operation hours from a date"
    );
  x.addMethod(
    "updateFeasible", &updateFeasiblePython, METH_NOARGS,
    "updates the flag whether this operationplan is feasible or not"
  );
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


PyObject* OperationPlan::calculateOperationTimePython(PyObject *self, PyObject *args)
{
  // Pick up the argument
  PyObject *datepy;
  PyObject *durationpy;
  int forward = 1;

  if (!PyArg_ParseTuple(args, "OO|p:calculateOperationTime", &datepy, &durationpy, &forward))
    return nullptr;

  try
  {
    auto opplan = static_cast<OperationPlan*>(self);
    Date dt = PythonData(datepy).getDate();
    Duration dur = PythonData(durationpy).getDuration();
    if (!opplan->getOperation())
      return PythonData(dt + dur);
    else
    {
      DateRange res = opplan->getOperation()->calculateOperationTime(opplan, dt, dur, (forward==1));
      return PythonData(forward ? res.getEnd() : res.getStart());
    }
  }
  catch (...)
  {
    PythonType::evalException();
    return nullptr;
  }
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


void OperationPlan::restore(const OperationPlanState& x)
{
  setStartEndAndQuantity(x.start, x.end, x.quantity);
  if (quantity != x.quantity) quantity = x.quantity;
  //assert(dates.getStart() == x.start || x.start != x.end);
  //assert(dates.getEnd() == x.end || x.start != x.end);
  if (!SetupMatrix::empty())
    scanSetupTimes();
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
  Object *itemdistributionval = nullptr;
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
    const DataValue* val = in.get(Tags::itemdistribution);
    if (val)
    {
      itemdistributionval = val->getObject();
      if (itemdistributionval && itemdistributionval->getType().category != ItemDistribution::metacategory)
        throw DataException("Itemdistribution field on operationplan must be of type itemdistribution");
    }
    else
    {
      val = in.get(Tags::origin);
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

  // Flag whether or not to create sub operationplans
  bool create = true;
  const DataValue* py_create = in.get(Tags::create);
  if (py_create)
    create = py_create->getBool();

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
    if (!ordtype.empty() && ordtype == "MO" && oper && opplan->getOperation() != static_cast<Operation*>(oper))
      // Change the operation
      opplan->setOperation(static_cast<Operation*>(oper));
    if (quantityfld || startfld || endfld)
      opplan->getOperation()->setOperationPlanParameters(
        opplan, quantityfld ? quantity : opplan->getQuantity(),
        start, end
      );
    return opplan;
  }

  // Create a new operation plan
  if (!start && !end)
    start = Plan::instance().getCurrent();
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
          o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "' and location'" << static_cast<Location*>(locval) << "'";
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
    if (!opplan->activate(create))
      throw DataException("Can't create operationplan");
  }
  else if (ordtype == "DO")
  {
    // Find or create the destination buffer.
    if (itemdistributionval)
    {
      itemval = static_cast<ItemDistribution*>(itemdistributionval)->getItem();
      locval = static_cast<ItemDistribution*>(itemdistributionval)->getDestination();
      orival = static_cast<ItemDistribution*>(itemdistributionval)->getOrigin();
    }
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
          o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "' and location '" << static_cast<Location*>(locval) << "'";
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
      Item::bufferIterator bufiter = static_cast<Item*>(itemval)->getBufferIterator();
      while (Buffer* tmpbuf = bufiter.next())
      {
        if (tmpbuf->getLocation() == static_cast<Location*>(orival))
        {
          if (originbuffer)
          {
            stringstream o;
            o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "' and location '" << static_cast<Location*>(orival) << "'";
            throw DataException(o.str());
          }
          originbuffer = tmpbuf;
        }
      }
      if (!originbuffer)
        // Create the origin buffer
        originbuffer = Buffer::findOrCreate(static_cast<Item*>(itemval), static_cast<Location*>(orival));

      // Create itemdistribution when not provided
      if (!itemdistributionval)
      {
        itemdistributionval = new ItemDistribution();
        static_cast<ItemDistribution*>(itemdistributionval)->setOrigin(static_cast<Location*>(orival));
        static_cast<ItemDistribution*>(itemdistributionval)->setItem(static_cast<Item*>(itemval));
        static_cast<ItemDistribution*>(itemdistributionval)->setDestination(static_cast<Location*>(locval));
        static_cast<ItemDistribution*>(itemdistributionval)->setPriority(0);
      }

      // Create operation when it doesn't exist yet
      oper = nullptr;
      auto oper_iter = static_cast<ItemDistribution*>(itemdistributionval)->getOperations();
      while (OperationItemDistribution* oper2 = oper_iter.next())
      {
        if (oper2->getOrigin() == originbuffer && oper2->getDestination() == destbuffer)
        {
          oper = oper2;
          break;
        }
      }
      if (!oper)
        oper = new OperationItemDistribution(
          static_cast<ItemDistribution*>(itemdistributionval), originbuffer, destbuffer
          );

      // Create operation plan
      opplan = static_cast<Operation*>(oper)->createOperationPlan(quantity, start, end, nullptr, nullptr, 0, false);
      // Make sure no problem is reported when item distribution priority is 0 (Rebalancing)
      // Checking that no item distribution in reverse mode exists
      bool found = false;
      auto itemdist_iter = (static_cast<Item*>(itemval))->getDistributionIterator();
      while (ItemDistribution *i = itemdist_iter.next())
      {
        if (i->getOrigin() == static_cast<ItemDistribution*>(itemdistributionval)->getDestination()
          && i->getDestination() == static_cast<ItemDistribution*>(itemdistributionval)->getOrigin())
        {
          found = true;
          break;
        }
      }
      if (!found)
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
    if (!opplan->activate(create))
      throw DataException("Can't create operationplan");
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
          o << "Multiple buffers found for item '" << static_cast<Item*>(itemval) << "' and location '" << static_cast<Location*>(locval) << "'";
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
    {
      oper = new OperationDelivery();
      static_cast<OperationDelivery*>(oper)->setBuffer(destbuffer);
    }

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
    if (!opplan->activate(create))
      throw DataException("Can't activate operationplan");
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
      opplan->setStatus(status);
      opplan->freezeStatus(
        start ? start : opplan->getStart(), 
        end ? end : opplan->getEnd(),
        quantity
        );
    }
    if (!opplan->activate(create, start))
      throw DataException("Can't create operationplan");

    // Report the operationplan creation to the manager
    if (mgr)
        mgr->add(new CommandCreateObject(opplan));
  }
  return opplan;
}


OperationPlan* OperationPlan::findId(unsigned long l)
{
  if (l >= counterMin)
    // We are garantueed that there are no operationplans that have an id equal
    // or higher than the current counter. This is garantueed by the
    // instantiate() method.
    return nullptr;
  else
  {
    auto tmp = st.find(l);
    // Look up in the tree structure
    return tmp == st.end() ? nullptr : static_cast<OperationPlan*>(tmp);
  }
}


bool OperationPlan::assignIdentifier()
{
  // Need to assure that ids are unique!
  static mutex onlyOne;
  if (getName() && getName() != ULONG_MAX)
  {
    // An identifier was read in from input
    lock_guard<mutex> l(onlyOne);
    if (getName() < counterMin)
    {
      // The assigned id potentially clashes with an existing operationplan.
      // Check whether it clashes with existing operationplans
      OperationPlan* opplan = static_cast<OperationPlan*>(st.find(getName()));
      if (opplan != st.end() && opplan->getOperation() != oper)
        return false;
    }
    // The new operationplan definitely doesn't clash with existing id's.
    // The counter need updating to garantuee that counter is always
    // a safe starting point for tagging new operationplans.
    else
      counterMin = getName() + 1;
  }
  else 
  {
    // Fresh operationplan with blank id
    lock_guard<mutex> l(onlyOne);  // Need to assure that ids are unique!
    setName(counterMin++);
  }

  // Check whether the counter is still okay
  if (counterMin >= ULONG_MAX)
    throw RuntimeException("Exhausted the range of available operationplan identifiers");

  // Insert in the tree of operationplans
  st.insert(this);

  return true;
}


void OperationPlan::setOperation(Operation* o)
{
  if (oper == o)
    return;
  if (oper)
  {
    // Switching operations
    deleteFlowLoads();
    removeFromOperationplanList();
    oper = o;
    oper->setOperationPlanParameters(
      this, quantity, dates.getStart(), dates.getEnd(), false, true
    );
  }
  else
    // First initialization of the operationplan
    oper = o;
  activate();
}


bool OperationPlan::activate(bool createsubopplans, bool use_start)
{
  // At least a valid operation pointer must exist
  if (!oper)
    throw LogicException("Initializing an invalid operationplan");

  // Avoid negative quantities, and call operation specific activation code
  if (getQuantity() < 0.0 || !oper->extraInstantiate(this, createsubopplans, use_start))
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
  if (getName() && getName() != ULONG_MAX)
  {
    // Validate the user provided id.
    if (!assignIdentifier())
    {
      ostringstream ch;
      ch << "Operationplan id " << getName() << " assigned multiple times";
      delete this;
      throw DataException(ch.str());
    }
  }
  else
    // The id given at this point is only a temporary one. The final id is
    // created lazily when the getIdentifier method is called.
    // In this way, 1) we avoid clashes between auto-generated and
    // user-provided in the input and 2) we keep performance high.
    setName(ULONG_MAX);

  // Insert into the doubly linked list of operationplans.
  insertInOperationplanList();

  // If we used the lazy creator, the flow- and loadplans have not been
  // created yet. We do it now...
  createFlowLoads();

  // Update the feasibility flag.
  updateFeasible();

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
  st.erase(this);
  setName(0);

  // Delete from the list of deliveries
  if (dmd)
    dmd->removeDelivery(this);

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

  // Different setup end date
  if (getSetupEnd() != a.getSetupEnd())
    return getSetupEnd() < a.getSetupEnd();

  // Sort based on quantity
  if (fabs(quantity - a.quantity) > ROUNDING_ERROR)
    return quantity >= a.quantity;

  if ((getRawIdentifier() && !a.getRawIdentifier())
    || (!getRawIdentifier() && a.getRawIdentifier()))
    // Keep uninitialized operationplans (whose id = 0) seperate
    return getRawIdentifier() > a.getRawIdentifier();
  
  if (getEnd() != a.getEnd())
    // Use the end date
    return getEnd() < a.getEnd();
  
  // Using a pointer comparison as tie breaker. This can give
  // results that are not reproducible across platforms and runs.
  return this < &a;
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
      new LoadPlan(this, &*g);

  // Create flowplans for flows
  for (Operation::flowlist::const_iterator h=oper->getFlows().begin();
      h!=oper->getFlows().end(); ++h)
  {
    // Only the primary flow is instantiated.
    if (h->getAlternate())
      continue;
    // Also for transfer batches, we only need to create the first flowplan.
    // The getFlowplanDateQuantity method will be called during the creation, and
    // create additional flowplans as required.
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

  // Delete setup event
  clearSetupEvent();
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
  // Delete from the operationplan tree
  st.erase(this);

  // Delete the setup event
  if (setupevent)
  {
    setupevent->erase();
    delete setupevent;
  }

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


void OperationPlan::setStart (Date d, bool force, bool preferEnd)
{
  // Confirmed opplans don't move
  if (getConfirmed())
  {
    if (force)
      setStartAndEnd(d, getEnd());
    return;
  }

  if (!lastsubopplan)
    // No sub operationplans
    oper->setOperationPlanParameters(this, quantity, d, Date::infinitePast, preferEnd, true, false);
  else
  {
    // Move all sub-operationplans in an orderly fashion
    for (OperationPlan* i = firstsubopplan; i; i = i->nextsubopplan)
    {
      if (i->getStart() < d)
      {
        i->setStart(d, force, preferEnd);
        d = i->getEnd();
      }
      else
        // There is sufficient slack between the suboperationplans
        break;
    }
  }

  // Update flow and loadplans
  update();
}


void OperationPlan::setEnd(Date d, bool force)
{

  // Locked opplans don't move
  if (getConfirmed())
  {
    if (force)
      setStartAndEnd(getStart(), d);
    return;
  }
    

  if (!lastsubopplan)
    // No sub operationplans
    oper->setOperationPlanParameters(this, quantity, Date::infinitePast, d, true, true, false);
  else
  {
    // Move all sub-operationplans in an orderly fashion
    for (OperationPlan* i = lastsubopplan; i; i = i->prevsubopplan)
    {
      if (!i->getEnd() || i->getEnd() > d)
      {
        i->setEnd(d, force);
        d = i->getStart();
      }
      else
        // There is sufficient slack between the suboperationplans
        break;
    }
  }

  // Update flow and loadplans
  update();
  //assert(getEnd() <= d);
}


void OperationPlan::resizeFlowLoadPlans()
{
  // Update all flowplans
  for (auto flpln = firstflowplan; flpln; flpln = flpln->nextFlowPlan)
    flpln->update();

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
}


OperationPlan::OperationPlan(const OperationPlan& src, bool init) : Tree<unsigned long>::TreeNode(0)
{
  if (src.owner)
    throw LogicException("Can't copy suboperationplans. Copy the owner instead.");

  // Copy all fields, except identifier and reference.
  // A new identifier will be generated when we activate the operationplan.
  // The reference remains blank.
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
    OperationPlan* newOwner) : Tree<unsigned long>::TreeNode(0)
{
  if (!newOwner)
    throw LogicException("No new owner passed in private copy constructor.");

  // Copy all fields, except the identifier can't be inherited.
  // A new identifier will be generated when we activate the operationplan
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


bool OperationPlan::mergeIfPossible()
{
  // Verify a merge with another operationplan.
  // TODO The logic duplicates much of OperationFixedTime::extraInstantiate. Combine as single code.
  // See if we can consolidate this operationplan with an existing one.
  // Merging is possible only when all the following conditions are met:
  //   - it is a subclass of a fixedtime operation
  //   - it doesn't load any resources of type default
  //   - both operationplans are proposed
  //   - both operationplans have no owner
  //     or both have an owner of the same operation and is of type operation_alternate
  //   - start and end date of both operationplans are exactly the same
  //   - demand of both operationplans are the same
  //   - maximum operation size is not exceeded
  //   - alternate flowplans need to be on the same alternate
  if (!getProposed())
    return false;

  if (oper->getType() != *OperationFixedTime::metadata
    && oper->getType() != *OperationItemDistribution::metadata
    && oper->getType() != *OperationItemSupplier::metadata
    )
    return false;

  // Verify we load no resources of type "default".
  // It's ok to merge operationplans which load "infinite" or "buckets" resources.
  for (Operation::loadlist::const_iterator i = oper->getLoads().begin(); i != oper->getLoads().end(); ++i)
    if (i->getResource()->getType() == *ResourceDefault::metadata)
      return false;

  // Loop through candidates
  for (OperationPlan::iterator x(oper); x != OperationPlan::end(); ++x)
  {
    if (x->getStart() > getStart())
      // No candidates will be found in what follows
      return false;
    if (x->getDates() != getDates() || &*x == this)
      continue;
    if (x->getDemand() != getDemand())
      continue;
    if (!x->getProposed())
      continue;
    if (x->getQuantity() + getQuantity() > oper->getSizeMaximum() + ROUNDING_ERROR)
      continue;
    if (getOwner())
    {
      // Both must have the same owner operation of type alternate
      if (!x->getOwner())
        continue;
      else if (getOwner()->getOperation() != x->getOwner()->getOperation())
        continue;
      else if (getOwner()->getOperation()->getType() != *OperationAlternate::metadata)
        continue;
      else if (getOwner()->getDemand() != x->getOwner()->getDemand())
        continue;
    }

    // Check that the flowplans are on identical alternates and not of type fixed
    OperationPlan::FlowPlanIterator fp1 = beginFlowPlans();
    OperationPlan::FlowPlanIterator fp2 = x->beginFlowPlans();
    if (fp1 == endFlowPlans() || fp2 == endFlowPlans())
      // Operationplan without flows are already deleted. Leave them alone.
      continue;
    bool ok = true;
    while (fp1 != endFlowPlans())
    {
      if (fp1->getBuffer() != fp2->getBuffer()
        || fp1->getFlow()->getQuantityFixed()
        || fp2->getFlow()->getQuantityFixed())
        // No merge possible
      {
        ok = false;
        break;
      }
      ++fp1;
      ++fp2;
    }
    if (!ok)
      continue;

    // All checks passed, we can merge!
    x->setQuantity(x->getQuantity() + getQuantity());
    if (getOwner())
      setOwner(nullptr);
    delete this;
    return true;
  }
  return false;
}


void OperationPlan::scanSetupTimes()
{
  for (auto ldplan = beginLoadPlans(); ldplan != endLoadPlans(); ++ldplan)
  {
    if (!ldplan->isStart() && !ldplan->getLoad()->getSetup().empty() && ldplan->getResource()->getSetupMatrix())
    {
      // Not a starting loadplan or there is no setup on this loadplan
      ldplan->getResource()->updateSetupTime();
      break;  // Only 1 load can have a setup
    }
  }

  // TODO We can do much faster than the above loop: where we reconsider all loadplans on a 
  // resource. We just need to scans the ones around the old date and the ones around the new date.
  // It requires deeper changes to the solver to pass on the information on the old date.
  /*
  // Loop over all loadplans
  for (auto ldplan = beginLoadPlans(); ldplan != endLoadPlans(); ++ldplan)
  {
    if (!ldplan->isStart() || ldplan->getLoad()->getSetup().empty() || !ldplan->getResource()->getSetupMatrix())
      // Not a starting loadplan or there is no setup on this loadplan
      continue;

    // Scan backward for loadplans at the same date
    auto resldplan = ldplan->getResource()->getLoadPlans().begin(&*ldplan);
    --resldplan;
    while (resldplan != ldplan->getResource()->getLoadPlans().end())
    {
      if (resldplan->getDate() != ldplan->getDate())
        break;
      if (resldplan->getEventType() == 1)
      {
        auto tmp = static_cast<LoadPlan*>(&*resldplan);
        if (tmp->isStart() && !static_cast<LoadPlan*>(&*resldplan)->getLoad()->getSetup().empty())
        {
          // The setup time of this operationplan potentially changes
          resldplan->getOperationPlan()->updateSetupTime();
        }
      }
      --resldplan;
    }
    
    // Scan forward until the first operationplan with a setup.    
    resldplan = ldplan->getResource()->getLoadPlans().begin(&*ldplan);
    ++resldplan;
    while (resldplan != ldplan->getResource()->getLoadPlans().end())
    {
      if (resldplan->getEventType() == 1)
      {
        auto tmp = static_cast<LoadPlan*>(&*resldplan);
        if (tmp->isStart() && !static_cast<LoadPlan*>(&*resldplan)->getLoad()->getSetup().empty())
        {
          // The setup time of this operationplan potentially changes
          resldplan->getOperationPlan()->updateSetupTime();
          if (resldplan->getDate() > getEnd())
            break;
        }
      }
      ++resldplan;
    }      
  }
  */
}


bool OperationPlan::updateSetupTime(bool report)
{
  // TODO The setOperationplanParameter methods are a better/more generic/more robust place to put this logic
  Date end_of_setup = getSetupEnd();
  bool changed = false;

  // Keep the setup end date constant during the update 
  Operation::SetupInfo setup = oper->calculateSetup(this, end_of_setup, setupevent);
  if (get<0>(setup))
  {
    // Setup event required
    if (get<1>(setup))
    {
      // Apply setup rule duration
      DateRange tmp = oper->calculateOperationTime(this, end_of_setup, get<1>(setup)->getDuration(), false);
      setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup), get<1>(setup));
      if (tmp.getStart() != getStart())
      {
        setStartAndEnd(tmp.getStart(), getEnd());
        changed = true;
      }
    }
    else if (getStart() != end_of_setup)
    {
      // Zero time event
      setSetupEvent(get<0>(setup), end_of_setup, get<2>(setup), get<1>(setup));
      setStartAndEnd(end_of_setup, getEnd());
      changed = true;
    }
  
  }
  else
  {
    // No setup event required
    if (setupevent)
    {
      clearSetupEvent();
      changed = true;
    }
    if (end_of_setup != getStart())
    {
      setStartAndEnd(end_of_setup, getEnd());
      changed = true;
    }
  }
  return changed;
}


void OperationPlan::update()
{
  if (lastsubopplan)
  {
    // Set the start and end date of the parent.
    Date st = Date::infiniteFuture;
    Date nd = Date::infinitePast;
    for (OperationPlan *f = firstsubopplan; f; f = f->nextsubopplan)
    {
      if (f->getStart() < st)
        st = f->getStart();
      if (f->getEnd() > nd)
        nd = f->getEnd();
    }
    if (nd)
      dates.setStartAndEnd(st, nd);
  }

  // Update the flow and loadplans
  resizeFlowLoadPlans();

  // Keep the operationplan list sorted
  updateOperationplanList();

  // Update the setup time on all neighbouring operationplans
  if (!SetupMatrix::empty() && getPropagateSetups())
    scanSetupTimes();

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
    
    // Advance to the next operation plan
    opplan = opplan->next;
    if (tmp->getOwner())
      // Deleting a child operationplan will delete the parent.
      // It is possible that also the next operationplan in the list gets deleted by the 
      // delete statement that follows.
      while (opplan && tmp->getOwner() == opplan->getOwner())
        opplan = opplan->next;

    // Note that the deletion of the operationplan also updates the opplan list
    if (deleteLockedOpplans || tmp->getProposed())
      delete tmp;
  }
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
  getOperation()->calculateOperationTime(this, dates.getStart(), dates.getEnd(), &x);
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
  if (getProposed())
    return;
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
          && !attr.isA(Tags::quantity) && !attr.isA(Tags::create))
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

    long early = getTopOwner()->getDemand()->getDue() - getEnd();
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
      Duration myslack = m->getTopOwner()->getDemand()->getDue() - m->getEnd();
      if (myslack < 0L) myslack = 0L;
      for (unsigned int i=1; i<=lvl; i++)
      {
        if (opplans[i-1]->getOwner() == opplans[i] || opplans[i-1] == opplans[i]->getOwner())
          // Times between parent and child opplans isn't slack
          continue;
        Date st = opplans[i-1]->getEnd();
        if (!st) st = Plan::instance().getCurrent();
        Date nd = opplans[i]->getStart();
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
    return getEnd() - getTopOwner()->getDemand()->getDue();

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
      // Reached a demand. Get the total delay now.
      Duration mydelay = getEnd() - m->getTopOwner()->getDemand()->getDue();
      for (unsigned int i = 0; i < lvl; i++)
      {
        if (opplans[i]->getOwner())
          // Don't count operation times on child operationplans
          continue;
        if (opplans[i] != this)
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


int OperationPlan::InterruptionIterator::intitialize()
{
  // Initialize the metadata.
  metacategory = MetaCategory::registerCategory<OperationPlan::InterruptionIterator>("interruption", "interruptions");
  metadata = MetaClass::registerClass<OperationPlan::InterruptionIterator>("interruption", "operationplan interruption", true);
  registerFields<OperationPlan::InterruptionIterator>(const_cast<MetaCategory*>(metacategory));

  // Initialize the Python type
  PythonType& x = PythonExtension<OperationPlan::InterruptionIterator>::getPythonType();
  x.setName("interruption");
  x.setDoc("frePPLe operationplan interruption");
  x.supportgetattro();
  x.supportstr();
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


OperationPlan::AlternateIterator::AlternateIterator(const OperationPlan* o) : opplan(o)
{  
  if (!o)
    return;
  if (o->getOwner() && o->getOwner()->getOperation()->getType() == *OperationAlternate::metadata)
  {
    auto subs = o->getOwner()->getOperation()->getSubOperationIterator();
    while (SubOperation* sub = subs.next())
    {
      if (sub->getOperation() != o->getOperation())
        opers.push_back(sub->getOperation());
    }
  }
  else
  {
    for (
      auto super = o->getOperation()->getSuperOperations().begin();
      super != o->getOperation()->getSuperOperations().end();
      ++super
      )
    {
      if ((*super)->getType() != *OperationAlternate::metadata)
        return;
      auto subs = (*super)->getSubOperationIterator();
      while (SubOperation* sub = subs.next())
      {
        if (sub->getOperation() != opplan->getOperation()) 
          opers.push_back(sub->getOperation());
      }
        
    }
  }
  operIter = opers.begin();
}


Operation* OperationPlan::AlternateIterator::next()
{
  if (operIter == opers.end())
    return nullptr;
  auto tmp = *operIter;
  ++operIter;
  return tmp;
}


OperationPlan::InterruptionIterator* OperationPlan::InterruptionIterator::next()
{
  while (true)
  {
    // Check whether all calendars are available
    bool available = true;
    Date selected = Date::infiniteFuture;
    for (auto t = cals.begin(); t != cals.end(); ++t)
    {
      if (t->getDate() < selected)
        selected = t->getDate();
    }
    curdate = selected;
    for (auto t = cals.begin(); t != cals.end() && available; ++t)
      // TODO next line does a pretty expensive lookup in the calendar, which we might be available to avoid
      available = (t->getCalendar()->getValue(selected) != 0);

    if (available && !status)
    {
      // Becoming available after unavailable period
      status = true;
      end = (curdate > opplan->getEnd()) ? opplan->getEnd() : curdate;
      return this;
    }
    else if (!available && status)
    {
      // Becoming unavailable after available period
      status = false;
      if (curdate >= opplan->getEnd())
        // Leaving the desired date range
        return nullptr;
      start = curdate;
    }
    else if (curdate >= opplan->getEnd())
      return nullptr;

    // Advance to the next event
    for (auto t = cals.begin(); t != cals.end(); ++t)
      if (t->getDate() == selected)
        ++(*t);
  }
}


double OperationPlan::getEfficiency(Date d) const
{
  double best = DBL_MAX;
  LoadPlanIterator e = beginLoadPlans();
  if (e == endLoadPlans())
  {
    // Use the operation loads
    for (auto h = getOperation()->getLoads().begin(); h != getOperation()->getLoads().end(); ++h)
    {
      double best_eff = 0.0;
      for (Resource::memberRecursiveIterator mmbr(h->getResource()); !mmbr.empty(); ++mmbr)
      {
        if (
          !mmbr->isGroup()
          && (!h->getSkill() || mmbr->hasSkill(h->getSkill()))
          )
        {
          auto my_eff = mmbr->getEfficiencyCalendar()
            ? mmbr->getEfficiencyCalendar()->getValue(d ? d : getStart())
            : mmbr->getEfficiency();
          if (my_eff > best_eff)
            best_eff = my_eff;
        }
      }
      if (best_eff < best)
        best = best_eff;
    }
  }
  else
  {
    // Use the operationplan loadplans
    while (e != endLoadPlans())
    {
      if (e->getQuantity() <= 0)
      {
        auto tmp = e->getResource()->getEfficiencyCalendar()
          ? e->getResource()->getEfficiencyCalendar()->getValue(d ? d : getStart())
          : e->getResource()->getEfficiency();
        if (tmp < best)
          best = tmp;
      }
      ++e;
    }
  }
  return best == DBL_MAX ? 1.0 : best / 100.0;
}


Duration OperationPlan::getSetup() const
{
  if (setupevent)
  {
    if (getOperation())
    {
      // Convert date difference back to active time
      Duration actual;
      getOperation()->calculateOperationTime(this, dates.getStart(), setupevent->getDate(), &actual);
      return actual;
    }
    else 
      return setupevent->getDate() - dates.getStart();
  }
  else
    // No setup event
    return 0L;
}


void OperationPlan::setSetupEvent(Resource* res, Date d, PooledString s, SetupMatrixRule* r)
{
  if (setupevent)
    setupevent->update(res, d, s, r);
  else
    setupevent = new SetupEvent(res->getLoadPlans(), d, s, r, this);
}


double OperationPlan::getSetupCost() const
{
  if (setupevent)
    return setupevent->getRule() ? setupevent->getRule()->getCost() : 0.0;
  else
    return 0.0;
}


SetupEvent::~SetupEvent()
{
  if (opplan)
    opplan->nullSetupEvent();
}


void SetupEvent::update(Resource* res, Date d, PooledString s, SetupMatrixRule* r)
{
  setup = s;
  rule = r;
  if (!tmline)
  {
    // First insert
    tmline = &res->getLoadPlans();
    tmline->insert(this);
  }
  else if (&res->getLoadPlans() != tmline)
  {
    // Reinsert at another resource
    tmline->erase(this);
    tmline = &res->getLoadPlans();
    tmline->insert(this);
  }
  else
    // Update the position in the list
    tmline->update(this, d);
}


SetupEvent* SetupEvent::getSetupBefore() const
{
  auto i = getTimeLine()->begin(this);
  --i;
  while (i != getTimeLine()->end())
  {
    if (i->getEventType() == 5)
      return const_cast<SetupEvent*>(static_cast<const SetupEvent*>(&*i));
    --i;
  }
  return nullptr;
}


int SetupEvent::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<SetupEvent>("setupevent", "setupevents");
  registerFields<SetupEvent>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python type
  PythonType& x = FreppleCategory<LoadPlan>::getPythonType();
  x.setName("setupeven");
  x.setDoc("frePPLe setup event");
  x.supportgetattro();
  x.supportsetattro();
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}

} // end namespace
