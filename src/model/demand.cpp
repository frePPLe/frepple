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


int Demand::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Demand>("demand", "demands", reader, writer, finder);
  registerFields<Demand>(const_cast<MetaCategory*>(metadata));

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
    for (OperationPlan_list::iterator i = deli.begin(); i!=deli.end(); ++i)
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
  OperationPlan_list::iterator j = deli.begin();
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


DECLARE_EXPORT const Demand::OperationPlan_list& Demand::getDelivery() const
{
  // We need to check the sorting order of the list first! It could be disturbed
  // when operationplans are being moved around.
  // The sorting routine isn't very efficient, but should suffice since the
  // list of delivery operationplans is short and isn't expected to be
  // disturbed very often.
  for (bool swapped(!deli.empty()); swapped; swapped=false)
  {
    OperationPlan_list::iterator j = const_cast<Demand*>(this)->deli.begin();
    ++j;
    for (OperationPlan_list::iterator i =
        const_cast<Demand*>(this)->deli.begin();
        j!=const_cast<Demand*>(this)->deli.end(); ++j)
    {
      if ((*i)->getDates().getEnd() < (*j)->getDates().getEnd())
      {
        // Oh yes, the ordering was disrupted indeed...
        iter_swap(i,j);
        // The Borland compiler doesn't understand that this variable is used.
        // It gives a incorrect warning message...
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
  const Demand::OperationPlan_list& l = getDelivery();
  return l.empty() ? NULL : *(l.begin());
}


DECLARE_EXPORT OperationPlan* Demand::getEarliestDelivery() const
{
  const Demand::OperationPlan_list& l = getDelivery();
  OperationPlan *last = NULL;
  for (Demand::OperationPlan_list::const_iterator i = l.begin(); i!=l.end(); ++i)
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
  for (OperationPlan_list::iterator i = deli.begin(); i!=deli.end(); ++i)
    if (*i == o) return;

  // Add to the list of delivery operationplans. The insertion is such
  // that the delivery list is sorted in terms of descending end time.
  // i.e. the opplan with the latest end date is on the front of the list.
  // Note: We're forcing resorting the deliveries with the getDelivery()
  // method. Operation plans dates could have changed, thus disturbing the
  // original order.
  getDelivery();
  OperationPlan_list::iterator j = deli.begin();
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
  // Operation can be specified on the demand itself,
  if (oper) return oper;
  // ... or on the item,
  if (it) return it->getOperation();
  // ... or it doesn't exist at all
  return NULL;
}


DECLARE_EXPORT double Demand::getPlannedQuantity() const
{
  double delivered(0.0);
  for (OperationPlan_list::const_iterator i=deli.begin(); i!=deli.end(); ++i)
    delivered += (*i)->getQuantity();
  return delivered;
}


int DemandPlanIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<DemandPlanIterator>::getPythonType();
  x.setName("demandplanIterator");
  x.setDoc("frePPLe iterator for demand delivery operationplans");
  x.supportiter();
  return x.typeReady();
}


PyObject* DemandPlanIterator::iternext()
{
  if (i == dem->getDelivery().end()) return NULL;
  PyObject* result = const_cast<OperationPlan*>(&**(i++));
  Py_INCREF(result);
  return result;
}

} // end namespace
