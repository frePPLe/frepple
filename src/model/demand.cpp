/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/demand.cpp $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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

template<class Demand> DECLARE_EXPORT Tree HasName<Demand>::st;


void Demand::setQuantity(float f)
{
  // Reject negative quantities, and no-change updates
  float delta(f - qty);
  if (f < 0.0f || fabs(delta)<ROUNDING_ERROR) return;

  // Update the quantity
  qty = f;
  setChanged();
}


void Demand::deleteOperationPlans (bool deleteLockedOpplans)
{
  // Delete all opplans
  for(OperationPlan_list::iterator i = deli.begin(); i!=deli.end(); )
    if (deleteLockedOpplans || !(*i)->getLocked())
    {
      // Setting the demand pointer to NULL is required to prevent the
      // deletion of the operationplan calling the function removeDelivery.
      // We can't use the regular method setDemand() to do this!
      (*i)->lt = NULL;
      delete *i;
      // Remove from the list - while trying to maintain a valid iterator to
      // the next element.
      OperationPlan_list::iterator todelete = i;
      ++i;
      deli.erase(todelete);
    }
    else ++i;

  // Mark the demand as being changed, so the problems can be redetected
  setChanged();
}


void Demand::removeDelivery(OperationPlan * o)
{
  // Valid opplan check
  if (!o) return;

  // See if the demand field on the operationplan points to this demand
  if (o->lt != this) 
    throw LogicException("Delivery operationplan incorrectly registered");

  // Remove the reference on the operationplan
  o->lt = NULL;  // Required to avoid endless loop
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


const Demand::OperationPlan_list& Demand::getDelivery() const
{
	// We need to check the sorting order of the list first! It could be disturbed
	// when operationplans are being moved around.
	// The sorting routine isn't very efficient, but should suffice since the
	// list of delivery operationplans is short and isn't expected to be
  // disturbed very often.
  for(bool swapped(!deli.empty()); swapped; swapped=false)
	{
		OperationPlan_list::iterator j = const_cast<Demand*>(this)->deli.begin();
	  ++j;
	  for (OperationPlan_list::iterator i =
            const_cast<Demand*>(this)->deli.begin();
         j!=const_cast<Demand*>(this)->deli.end(); ++j)
	  {
	  	if ((*i)->getDates().getEnd() < (*j)->getDates().getEnd())
	  	{
        // Oh yes, the ordering was disruped indeed...
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


void Demand::addDelivery (OperationPlan * o)
{
	// If the policy is SINGLEDELIVERY then we need to unregister the previous
	// delivery operationplan
	if (planSingleDelivery() && !deli.empty()) removeDelivery(*deli.begin());

  // Dummy call to this function
  if (!o) return;

  // Check if it is already in the list.
  // If it is, simply exit the function. No need to give a warning message
  // since it's harmless.
  for(OperationPlan_list::iterator i = deli.begin(); i!=deli.end(); ++i)
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
  Operation *tmpOper = getDeliveryOperation();
  if (tmpOper && tmpOper != o->getOperation())
    clog << "Warning: Delivery Operation '" << o->getOperation()
    << "' different than expected '" << tmpOper
    << "' for demand '" << this << "'" << endl;
}


Operation* Demand::getDeliveryOperation() const
{
  // Operation can be specified on the demand itself,
  if (oper) return oper;
  // ... or on the item, 
  if (it) return it->getDelivery();
  // ... or it doesn't exist at all
  return NULL;
}


float Demand::getPlannedQuantity() const
{
  float delivered(0.0f);
  for(OperationPlan_list::const_iterator i=deli.begin(); i!=deli.end(); ++i)
    delivered += (*i)->getQuantity();
  return delivered;
}


void Demand::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }
    
  // Write the complete object
  if (m != NOHEADER) o->BeginObject(tag, Tags::tag_name, getName());

  // Write the fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Demand>::writeElement(o, tag);
  o->writeElement(Tags::tag_operation, oper);
  o->writeElement(Tags::tag_customer, cust);
  if (policy.any())
  {
    // We only need to save if the policy is different from the default.
    // It is important to stick to the convention that the default is a zero!
    string p;
    if (planShort()) p += "PLANSHORT ";
    if (planSingleDelivery()) p += "SINGLEDELIVERY ";
    o->writeElement(Tags::tag_policy, p);
  }
  Plannable::writeElement(o, tag);

  o->writeElement(Tags::tag_quantity, qty);
  o->writeElement(Tags::tag_item, it);
  o->writeElement(Tags::tag_due, dueDate);
  if (prio) o->writeElement(Tags::tag_priority, prio);

  // Write extra plan information
  if (o->getContentType() == XMLOutput::PLAN  && !deli.empty())
  {
    o->BeginObject(Tags::tag_operation_plans);
    for(OperationPlan_list::const_iterator i=deli.begin(); i!=deli.end(); ++i)
      o->writeElement(Tags::tag_operation_plan, *i, FULL);
    o->EndObject(Tags::tag_operation_plans);
  }

  o->EndObject(tag);
}


void Demand::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_item))
    pIn.readto( Item::reader(Item::metadata,pIn.getAttributes()) );
  else if (pElement.isA (Tags::tag_operation))
    pIn.readto( Operation::reader(Operation::metadata,pIn.getAttributes()) );
  else if (pElement.isA (Tags::tag_customer))
    pIn.readto( Customer::reader(Customer::metadata,pIn.getAttributes()) );
  else if (pElement.isA(Tags::tag_operation_plan))
    pIn.readto(OperationPlan::createOperationPlan(OperationPlan::metadata, pIn.getAttributes()));
  else
    HasHierarchy<Demand>::beginElement(pIn, pElement);
}


void Demand::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_quantity))
    setQuantity (pElement.getFloat());
  else if (pElement.isA (Tags::tag_priority))
    setPriority (pElement.getInt());
  else if (pElement.isA (Tags::tag_due))
    setDue(pElement.getDate());
  else if (pElement.isA (Tags::tag_operation))
  {
    Operation *o = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (o) oper = o;
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA (Tags::tag_customer))
  {
    Customer *c = dynamic_cast<Customer*>(pIn.getPreviousObject());
    if (c) cust = c;
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA (Tags::tag_policy))
    addPolicy(pElement.getString());
  else if (pElement.isA (Tags::tag_item))
  {
    Item *i = dynamic_cast<Item*>(pIn.getPreviousObject());
    if (i) it = i;
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_operation_plan))
  {
    OperationPlan* opplan 
      = dynamic_cast<OperationPlan*>(pIn.getPreviousObject());
    if (opplan) addDelivery(opplan);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
  {
    Plannable::endElement(pIn, pElement);
    HasDescription::endElement(pIn, pElement);
    HasHierarchy<Demand>::endElement (pIn, pElement);
  }
}


void Demand::addPolicy(const string& s)
{
  // Find words till we are the end of the string
  for(const char* ptr = s.c_str(); *ptr; ++ptr)
  {
    // Skip whitespace
    while (isspace(*ptr) || ispunct(*ptr)) ++ptr;

    // Jump to the right string comparison, depending on the first character
    bool notfound = true;
    switch (*ptr)
    {
      case 'P':
        if (!strncasecmp(ptr, "PLANSHORT", 9))
        {
          // planshort
          ptr += 9;
          if (planShort()) break;
          setChanged();
          policy.set(2);
        }
        else if (!strncasecmp(ptr, "PLANLATE", 8))
        {
          // planlate
          ptr += 8;
          if (planLate()) break;
          setChanged();
          policy.reset(2);
        }
        else
          notfound = false;
        break;
      case 'S':
        if (strncasecmp(ptr, "SINGLEDELIVERY", 14) == 0)
        {
          // singledelivery
          ptr += 14;
          if (planSingleDelivery() ) break;
          setChanged();
          policy.set(3);
        }
        else
          notfound = false;
        break;
      case 'M':
        if (strncasecmp(ptr, "MULTIDELIVERY", 13) == 0)
        {
          // multidelivery
          ptr += 13;
          if (planMultiDelivery()) break;
          setChanged();
          policy.reset(3);
        }
        else
          notfound = false;
        break;
      default:
        notfound = false;
    }
    if (!*ptr) return;

    // Unrecognized policy name...
    if (notfound)
      throw DataException("Unrecognized policy for demand '" + getName()
        + "' in value: '" + ptr + "'");
  }
}

}
