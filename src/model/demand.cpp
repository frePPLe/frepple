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

template<class Demand> Tree<string> utils::HasName<Demand>::st;
const MetaCategory* Demand::metadata;
const MetaClass* DemandDefault::metadata;

OperationFixedTime *Demand::uninitializedDelivery = nullptr;


int Demand::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Demand>("demand", "demands", reader, finder);
  registerFields<Demand>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<Demand>::getPythonType();
  x.addMethod("addConstraint", addConstraint, METH_VARARGS, "add a constraint to the demand");

  uninitializedDelivery = new OperationFixedTime();
  
  // Initialize the Python class
  return FreppleCategory<Demand>::initialize();
}


int DemandDefault::initialize()
{
  // Initialize the metadata
  DemandDefault::metadata = MetaClass::registerClass<DemandDefault>(
    "demand",
    "demand_default",
    Object::create<DemandDefault>, true);
  registerFields<DemandDefault>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  return FreppleClass<DemandDefault,Demand>::initialize();
}


void Demand::setQuantity(double f)
{
  // Reject negative quantities, and no-change updates
  double delta(f - qty);
  if (f < 0.0 || fabs(delta)<ROUNDING_ERROR) return;

  // Update the quantity
  qty = f;
  setChanged();
}


Demand::~Demand()
{
  // Remove the delivery operationplans
  deleteOperationPlans(true);

  // Unlink from the item
  if (it)
  {
    if (it->firstItemDemand == this)
      it->firstItemDemand = nextItemDemand;
    else
    {
      Demand* dmd = it->firstItemDemand;
      while (dmd && dmd->nextItemDemand != this)
        dmd = dmd->nextItemDemand;
      if (!dmd)
        logger << "corrupted demand list for an item" << endl;
      dmd->nextItemDemand = nextItemDemand;
    }
  }
}


void Demand::deleteOperationPlans
(bool deleteLocked, CommandManager* cmds)
{
  // Delete all delivery operationplans.
  // Note that an extra loop is used to assure that our iterator doesn't get
  // invalidated during the deletion.
  while (true)
  {
    // Find a candidate to delete
    OperationPlan *candidate = nullptr;
    for (OperationPlanList::iterator i = deli.begin(); i!=deli.end(); ++i)
      if (deleteLocked || (*i)->getProposed())
      {
        candidate = *i;
        break;
      }
    if (!candidate) break;
    if (cmds)
      // Use delete command
      cmds->add(new CommandDeleteOperationPlan(candidate));
    else
      // Delete immediately
      delete candidate;
  }


  // Mark the demand as being changed, so the problems can be redetected
  setChanged();
}


void Demand::removeDelivery(OperationPlan *o)
{
  // Valid opplan check
  if (!o)
    return;

  // See if the demand field on the operationplan points to this demand
  if (o->dmd != this)
    throw LogicException("Delivery operationplan incorrectly registered");

  // Remove the reference on the operationplan
  o->dmd = nullptr;  // Required to avoid endless loop
  o->setDemand(nullptr);

  // Remove from the list
  deli.remove(o);
  setChanged();
}


const Demand::OperationPlanList& Demand::getDelivery() const
{
  // Sorting the deliveries by the end date
  const_cast<Demand*>(this)->deli.sort(
    [](OperationPlan*& lhs, OperationPlan*& rhs) {
      return lhs->getEnd() != rhs->getEnd() ?
        lhs->getEnd() > rhs->getEnd() :
        *lhs < *rhs;
      }
    );
  return deli;
}


OperationPlan* Demand::getLatestDelivery() const
{
  const Demand::OperationPlanList& l = getDelivery();
  return l.empty() ? nullptr : *(l.begin());
}


OperationPlan* Demand::getEarliestDelivery() const
{
  const Demand::OperationPlanList& l = getDelivery();
  OperationPlan *last = nullptr;
  for (Demand::OperationPlanList::const_iterator i = l.begin(); i!=l.end(); ++i)
    last = *i;
  return last;
}


void Demand::addDelivery (OperationPlan * o)
{
  // Dummy call to this function
  if (!o)
    return;

  // Check if it is already in the list.
  // If it is, simply exit the function. No need to give a warning message
  // since it's harmless.
  for (auto i = deli.begin(); i != deli.end(); ++i)
    if (*i == o)
      return;

  // Add to the list of delivery operationplans.
  deli.push_front(o);

  // Mark the demand as being changed, so the problems can be redetected
  setChanged();

  // Create link between operationplan and demand
  o->setDemand(this);

  // Check validity of operation being used
  Operation* tmpOper = getDeliveryOperation();
  if (tmpOper && tmpOper != o->getOperation())
    logger << "Warning: Delivery Operation '" << o->getOperation()
        << "' different than expected '" << tmpOper
        << "' for demand '" << this << "'" << endl;
}


Operation* Demand::getDeliveryOperation() const
{
  // Case 1: Operation specified on the demand itself,
  // or the delivery operation was computed earlier.
  if (oper && oper != uninitializedDelivery)
    return oper;

  // Case 2: Create a delivery operation automatically
  if (!getItem())
  {
    // Not possible to create an operation when we don't know the item
    const_cast<Demand*>(this)->oper = nullptr;
    return nullptr;
  }
  Location *l = getLocation();
  if (!l)
  {
    // Single location only?
    Location::iterator l_iter = Location::begin();
    if (l_iter != Location::end())
    {
      l = &*l_iter;
      if (++l_iter != Location::end())
        // No, multiple locations
        l = nullptr;
    }
  }
  if (l)
  {
    // Search for buffers for the requested item and location.
    bool ok = true;
    Buffer* buf = nullptr;
    Item::bufferIterator buf_iter(getItem());
    while (Buffer* tmpbuf = buf_iter.next())
    {
      if (tmpbuf->getLocation() == l)
      {
        if (buf)
        {
          // Second buffer found. We don't know which one to pick - abort.
          ok = false;
          break;
        }
        else
          buf = tmpbuf;
      }
    }

    if (ok)
    {
      if (!buf)
        // Create a new buffer
        buf = Buffer::findOrCreate(getItem(), l);

      // Find an existing operation consuming from this buffer
      const_cast<Demand*>(this)->oper = Operation::find("Ship " + string(buf->getName()));
      if (!oper)
      {
        const_cast<Demand*>(this)->oper = new OperationDelivery();
        static_cast<OperationDelivery*>(const_cast<Demand*>(this)->oper)->setBuffer(buf);
      }

      // Success!
      return oper;
    }
  }

  // Case 4: Tough luck. Not possible to ship this demand.
  const_cast<Demand*>(this)->oper = nullptr;
  return nullptr;
}


double Demand::getPlannedQuantity() const
{
  double delivered(0.0);
  for (OperationPlanList::const_iterator i=deli.begin(); i!=deli.end(); ++i)
    delivered += (*i)->getQuantity();
  return delivered;
}


PyObject* Demand::addConstraint(PyObject* self, PyObject* args, PyObject* kwds)
{
  try
  {
    // Pick up the demand
    Demand *dmd = static_cast<Demand*>(self);
    if (!dmd)
      throw LogicException("Can't add a contraint to a null demand");

    // Parse the arguments
    char *pytype = nullptr;
    char *pyowner = nullptr;
    PyObject *pystart = nullptr;
    PyObject *pyend = nullptr;
    double cnstrnt_weight = 0;
    static const char *kwlist[] = { "type", "owner", "start", "end", "weight", nullptr };
    if (!PyArg_ParseTupleAndKeywords(
      args, kwds, "ss|OOd:addConstraint",
      const_cast<char**>(kwlist), &pytype, &pyowner, &pystart, &pyend, &cnstrnt_weight
      ))
        return nullptr;
    string cnstrnt_type;
    if (pytype) 
      cnstrnt_type = pytype;
    string cnstrnt_owner;
    if (pyowner)
      cnstrnt_owner = pyowner;
    Date cnstrnt_start = Date::infinitePast;
    if (pystart)
      cnstrnt_start = PythonData(pystart).getDate();
    Date cnstrnt_end = Date::infiniteFuture;
    if (pyend)
      cnstrnt_end = PythonData(pyend).getDate();

    // Add the new constraint
    Problem* cnstrnt = nullptr;
    if (cnstrnt_type == ProblemBeforeCurrent::metadata->type)
    {
      Operation* obj = Operation::findFromName(cnstrnt_owner);
      if (!obj)
        throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemBeforeCurrent::metadata, obj, cnstrnt_start, cnstrnt_end, cnstrnt_weight);
    }
    else if (cnstrnt_type == ProblemCapacityOverload::metadata->type)
    {
      Resource* obj = Resource::find(cnstrnt_owner);
      if (!obj)
        throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemCapacityOverload::metadata, obj, cnstrnt_start, cnstrnt_end, cnstrnt_weight);
    }
    else if (cnstrnt_type == ProblemMaterialShortage::metadata->type)
    {
      Buffer* obj = Buffer::findFromName(cnstrnt_owner);
      if (!obj)
        throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemMaterialShortage::metadata, obj, cnstrnt_start, cnstrnt_end, cnstrnt_weight);
    }
    else if (cnstrnt_type == ProblemBeforeFence::metadata->type)
    {
      Operation* obj = Operation::findFromName(cnstrnt_owner);
      if (!obj)
        throw DataException("Can't find constraint owner");
      cnstrnt = dmd->getConstraints().push(ProblemBeforeFence::metadata, obj, cnstrnt_start, cnstrnt_end, cnstrnt_weight);
    }
    else
      throw DataException("Invalid constraint type");
    return cnstrnt;
  }
  catch (...)
  {
    PythonType::evalException();
    return nullptr;
  }
}


PeggingIterator Demand::getPegging() const
{
  return PeggingIterator(this);
}


Problem::List::iterator Demand::getConstraintIterator() const
{
  return constraints.begin();
}

} // end namespace
