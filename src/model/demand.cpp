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

template<class Demand> DECLARE_EXPORT Tree utils::HasName<Demand>::st;
DECLARE_EXPORT const MetaCategory* Demand::metadata;
DECLARE_EXPORT const MetaClass* DemandDefault::metadata;

DECLARE_EXPORT OperationFixedTime *Demand::uninitializedDelivery = NULL;


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

  // Initialize the Python class
  return FreppleClass<DemandDefault,Demand>::initialize();
}


DECLARE_EXPORT void Demand::setQuantity(double f)
{
  // Reject negative quantities, and no-change updates
  double delta(f - qty);
  if (f < 0.0 || fabs(delta)<ROUNDING_ERROR) return;

  // Update the quantity
  qty = f;
  setChanged();
}


DECLARE_EXPORT Demand::~Demand()
{
  // Remove the delivery operationplans
  deleteOperationPlans(true);
}


DECLARE_EXPORT void Demand::deleteOperationPlans
(bool deleteLocked, CommandManager* cmds)
{
  // Delete all delivery operationplans.
  // Note that an extra loop is used to assure that our iterator doesn't get
  // invalidated during the deletion.
  while (true)
  {
    // Find a candidate to delete
    OperationPlan *candidate = NULL;
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


DECLARE_EXPORT void Demand::removeDelivery(OperationPlan * o)
{
  // Valid opplan check
  if (!o) return;

  // See if the demand field on the operationplan points to this demand
  if (o->dmd != this)
    throw LogicException("Delivery operationplan incorrectly registered");

  // Remove the reference on the operationplan
  o->dmd = NULL;  // Required to avoid endless loop
  o->setDemand(NULL);

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


DECLARE_EXPORT const Demand::OperationPlanList& Demand::getDelivery() const
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


DECLARE_EXPORT OperationPlan* Demand::getLatestDelivery() const
{
  const Demand::OperationPlanList& l = getDelivery();
  return l.empty() ? NULL : *(l.begin());
}


DECLARE_EXPORT OperationPlan* Demand::getEarliestDelivery() const
{
  const Demand::OperationPlanList& l = getDelivery();
  OperationPlan *last = NULL;
  for (Demand::OperationPlanList::const_iterator i = l.begin(); i!=l.end(); ++i)
    last = *i;
  return last;
}


DECLARE_EXPORT void Demand::addDelivery (OperationPlan * o)
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


DECLARE_EXPORT Operation* Demand::getDeliveryOperation() const
{
  // Case 1: Operation specified on the demand itself,
  // or the delivery operation was computed earlier.
  if (oper && oper != uninitializedDelivery)
    return oper;

  // Case 2: Operation specified on the item.
  // Note that we don't accept a delivery operation at the parent level
  // as a valid operation to plan the demand.
  if (it && it->getOperation())
    return it->getOperation();

  // Case 3: Create a delivery operation automatically
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
        l = NULL;
    }
  }
  if (l)
  {
    // Search for buffers for the requested item and location.
    bool ok = true;
    Buffer* buf = NULL;
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
      {
        // Create a new buffer
        buf = new BufferDefault();
        buf->setItem(getItem());
        buf->setLocation(l);
        stringstream o;
        o << getItem() << " @ " << l;
        buf->setName(o.str());
      }

      // Find an existing operation consuming from this buffer
      stringstream o;
      o << "Ship " << buf;
      const_cast<Demand*>(this)->oper = Operation::find(o.str());
      if (!oper)
      {
        const_cast<Demand*>(this)->oper = new OperationFixedTime();
        oper->setName(o.str());
        oper->setHidden(true);
        FlowStart* fl = new FlowStart(oper, buf, -1);
      }

      // Success!
      return oper;
    }
  }

  // Case 4: Tough luck. Not possible to ship this demand.
  const_cast<Demand*>(this)->oper = NULL;
  return NULL;
}


DECLARE_EXPORT double Demand::getPlannedQuantity() const
{
  double delivered(0.0);
  for (OperationPlanList::const_iterator i=deli.begin(); i!=deli.end(); ++i)
    delivered += (*i)->getQuantity();
  return delivered;
}


DECLARE_EXPORT PeggingIterator Demand::getPegging() const
{
  return PeggingIterator(this);
}


DECLARE_EXPORT Problem::List::iterator Demand::getConstraintIterator() const
{
  return constraints.begin();
}

} // end namespace
