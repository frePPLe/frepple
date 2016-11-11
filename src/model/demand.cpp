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

template<class Demand> Tree utils::HasName<Demand>::st;
const MetaCategory* Demand::metadata;
const MetaClass* DemandDefault::metadata;

OperationFixedTime *Demand::uninitializedDelivery = nullptr;


int Demand::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Demand>("demand", "demands", reader, finder);
  registerFields<Demand>(const_cast<MetaCategory*>(metadata));

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
      if (deleteLocked || !(*i)->getLocked())
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


void Demand::removeDelivery(OperationPlan * o)
{
  // Valid opplan check
  if (!o) return;

  // See if the demand field on the operationplan points to this demand
  if (o->dmd != this)
    throw LogicException("Delivery operationplan incorrectly registered");

  // Remove the reference on the operationplan
  o->dmd = nullptr;  // Required to avoid endless loop
  o->setDemand(nullptr);

  // Find in the list of deliveries
  OperationPlanList::iterator j = deli.begin();
  while (j!=deli.end() && *j!=o) ++j;

  // Check that the operation is found
  // It is possible it is not found! This happens if e.g. an operationplan
  // is created but destroyed again before it is initialized.
  if (j!=deli.end())
  {
    // Remove from the list
    deli.erase(j);
    // Mark the demand as being changed, so the problems can be redetected
    setChanged();
  }
}


const Demand::OperationPlanList& Demand::getDelivery() const
{
  // We need to check the sorting order of the list first! It could be disturbed
  // when operationplans are being moved around.
  // The sorting routine isn't very efficient, but should suffice since the
  // list of delivery operationplans is short and isn't expected to be
  // disturbed very often.
  for (bool swapped(!deli.empty()); swapped; swapped=false)
  {
    OperationPlanList::iterator j = const_cast<Demand*>(this)->deli.begin();
    ++j;
    for (OperationPlanList::iterator i =
        const_cast<Demand*>(this)->deli.begin();
        j!=const_cast<Demand*>(this)->deli.end(); ++j)
    {
      if ((*i)->getDates().getEnd() < (*j)->getDates().getEnd())
      {
        // Oh yes, the ordering was disrupted indeed...
        iter_swap(i,j);
        swapped = true;
        break;
      }
      ++i;
    }
  }

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
  if (!o) return;

  // Check if it is already in the list.
  // If it is, simply exit the function. No need to give a warning message
  // since it's harmless.
  for (OperationPlanList::iterator i = deli.begin(); i!=deli.end(); ++i)
    if (*i == o) return;

  // Add to the list of delivery operationplans. The insertion is such
  // that the delivery list is sorted in terms of descending end time.
  // i.e. the opplan with the latest end date is on the front of the list.
  // Note: We're forcing resorting the deliveries with the getDelivery()
  // method. Operation plans dates could have changed, thus disturbing the
  // original order.
  getDelivery();
  OperationPlanList::iterator j = deli.begin();
  while (j!=deli.end() && (*j)->getDates().getEnd()>o->getDates().getEnd()) ++j;
  deli.insert(j, o);

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
        const_cast<Demand*>(this)->oper = new OperationDelivery(buf);

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


PeggingIterator Demand::getPegging() const
{
  return PeggingIterator(this);
}


Problem::List::iterator Demand::getConstraintIterator() const
{
  return constraints.begin();
}

} // end namespace
