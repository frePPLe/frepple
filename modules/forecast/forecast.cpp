/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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


#include "forecast.h"

namespace module_forecast
{

const MetaClass Forecast::metadata;
const MetaClass ForecastSolver::metadata;
Forecast::MapOfForecasts Forecast::ForecastDictionary;
bool Forecast::Customer_Then_Item_Hierarchy = true;
bool Forecast::Match_Using_Delivery_Operation = true;


MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  static const char* name = "forecast";
  if (init)
  {
    cout << "Warning: Initializing module forecast more than once." << endl;
    return name;
  }
  init = true;

  // Process the parameter "Customer_Then_Item_Hierarchy"
  CommandLoadLibrary::ParameterList::const_iterator x 
    = z.find("Customer_Then_Item_Hierarchy");
  if (x != z.end())
  {
    switch (x->second[0])
    {
      case 'T':
      case 't':
      case '1':
        Forecast::setCustomerThenItemHierarchy(true);
        break;
      case 'F':
      case 'f':
      case '0':
        Forecast::setCustomerThenItemHierarchy(false);
        break;
      default:
        // We can't throw an exception in a module initialization routine...
        cout << "Error initializing " << name << " module: Invalid value '" 
          << x->second 
          << "' for parameter 'Customer_Then_Item_Hierarchy'" << endl;
    }
  }

  // Process the parameter "Match_Using_Delivery_Operation"
  x = z.find("Match_Using_Delivery_Operation");
  if (x != z.end())
  {
    switch (x->second[0])
    {
      case 'T':
      case 't':
      case '1':
        Forecast::setMatchUsingDeliveryOperation(true);
        break;
      case 'F':
      case 'f':
      case '0':
        Forecast::setMatchUsingDeliveryOperation(false);
        break;
      default:
        // We can't throw an exception in a module initialization routine...
        cout << "Error initializing " << name << " module: Invalid value '" 
          << x->second 
          << "' for parameter 'Match_Using_Delivery_Operation'" << endl;
    }
  }

  // Initialize the metadata.
  Forecast::metadata.registerClass(
    "DEMAND",
    "DEMAND_FORECAST",
    Object::createString<Forecast>);
  ForecastSolver::metadata.registerClass(
    "SOLVER",
    "SOLVER_FORECAST",
    Object::createString<ForecastSolver>);

  // Get notified when a calendar is deleted
  FunctorStatic<Calendar,Forecast>::connect(SIG_REMOVE);

  // Return the name of the module
  return name;
}


bool Forecast::callback(Calendar* l, const Signal a)
{
  // This function is called when a calendar is about to be deleted.
  // If that calendar is being used for a forecast we reset the calendar
  // pointer to null.
  for (MapOfForecasts::iterator x = ForecastDictionary.begin();
    x != ForecastDictionary.end(); ++x)
    if (x->second->calptr == l) 
      // Calendar in use for this forecast
      x->second->calptr = NULL;
  return true;
}


void Forecast::initialize()
{
  if (!calptr) throw DataException("Missing forecast calendar");

  // Create a demand for every bucket
  for (Calendar::BucketIterator i = calptr->beginBuckets();
    i != calptr->endBuckets(); ++i)
  {
    // C
    //cout << xxx
  }
}


void Forecast::setQuantity(Date d, float f)
{
  // Does a calendar exist already
  if (!calptr) throw DataException("Missing forecast calendar");

  // Look up the bucket and call auxilary function
  setQuantity(*(calptr->findBucket(d)), f);
}


void Forecast::setQuantity(const Calendar::Bucket& b, float qty)
{
  // See if a subdemand already exists for this bucket
  memberIterator m = beginMember();
  while (m!=endMember() && m->getDue()!=b.getStart()) ++m;

  if (m != endMember())
    // Update existing subdemand
    m->setQuantity(qty);
  else
  {
    // Create a new subdemand
    Demand *l = new DemandDefault(getName() + " - " + string(b.getStart()));
    Demand::add(l);
    l->setOwner(this);
    l->setHidden(true);  // Avoid the subdemands show up in the output
    l->setItem(&*getItem());
    l->setQuantity(qty);
    l->setDue(b.getStart());
    l->setPriority(getPriority());
    l->addPolicy(planLate() ? "PLANLATE" : "PLANSHORT");
    l->addPolicy(planSingleDelivery() ? "SINGLEDELIVERY" : "MULTIDELIVERY");
    l->setOperation(&*getOperation());
  }
}


void Forecast::writeElement(XMLOutput *o, const XMLtag &tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  o->writeElement(Tags::tag_item, getItem());
  o->writeElement(Tags::tag_calendar, calptr);
  if (getPriority()) o->writeElement(Tags::tag_priority, getPriority());
  o->writeElement(Tags::tag_operation, getOperation());
  if (!planLate() && planSingleDelivery())
    o->writeElement(Tags::tag_policy, "PLANSHORT SINGLEDELIVERY");
  else if (!planLate())
    o->writeElement(Tags::tag_policy, "PLANSHORT");
  else if (planSingleDelivery())
    o->writeElement(Tags::tag_policy, "SINGLEDELIVERY");

  // Write all entries
  o->BeginObject (Tags::tag_buckets);
  for (memberIterator i = beginMember(); i != endMember(); ++i)
  {
    o->BeginObject (Tags::tag_bucket, Tags::tag_dates, i->getDue());
    o->writeElement (Tags::tag_quantity, i->getQuantity());
    o->EndObject (Tags::tag_bucket);
  }
  o->EndObject(Tags::tag_buckets);

  o->EndObject(tag);
}


void Forecast::endElement(XMLInput& pIn, XMLElement& pElement)
{
  // While reading the date and quantity of a bucket, we use the date and
  // quantity fields of the forecast parent. When the bucket tag is closed
  // we copy the values to a new lot and clear the values on the parent
  // forecast.
  if (pElement.isA(Tags::tag_calendar))
  {
    Calendar *b = dynamic_cast<Calendar*>(pIn.getPreviousObject());
    if (b) setCalendar(b);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_bucket))
  {
    setQuantity(getDue(), getQuantity());
    Demand::setDue(Date::infinitePast);
    Demand::setQuantity(0.0f);
  }
  else if (pElement.isA (Tags::tag_quantity))
    Demand::setQuantity (pElement.getFloat());
  else if (pElement.isA (Tags::tag_due))
    Demand::setDue(pElement.getDate());
  else if (pIn.isObjectEnd())
  {
    // Clear the quantity and date.
    Demand::setDue(Date::infinitePast);
    Demand::setQuantity(0.0f);
    // Update the dictionary
    ForecastDictionary.insert(make_pair(
      make_pair(&*getItem(),&*getCustomer()),
      this
      ));
  }
  else
    Demand::endElement (pIn, pElement);
}


void Forecast::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_calendar))
    pIn.readto( Calendar::reader(Calendar::metadata, pIn) );
  else
    Demand::beginElement(pIn,pElement);
}


void Forecast::setCalendar(const Calendar* c)
{
  if (isGroup())
    throw DataException(
      "Changing the calendar of an initialized forecast isn't allowed.");
  calptr = c;
}


void Forecast::setItem(const Item* i)
{
  // No change
  if (getItem() == i) return;

  // Update the dictionary
  for (MapOfForecasts::iterator x = 
    ForecastDictionary.lower_bound(make_pair(
      &*getItem(),&*getCustomer()
      ));
    x != ForecastDictionary.end(); ++x)
    if (x->second == this) 
    {
      ForecastDictionary.erase(x); 
      break;
    }
  ForecastDictionary.insert(make_pair(make_pair(i,&*getCustomer()),this));

  // Update data field
  Demand::setItem(i);

  // Update the item for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setItem(i);
}


void Forecast::setCustomer(const Customer* i)
{
  // No change
  if (getCustomer() == i) return;

  // Update the dictionary
  for (MapOfForecasts::iterator x = 
    ForecastDictionary.lower_bound(make_pair(
      &*getItem(), &*getCustomer()
      ));
    x != ForecastDictionary.end(); ++x)
    if (x->second == this) 
    {
      ForecastDictionary.erase(x); 
      break;
    }
  ForecastDictionary.insert(make_pair(make_pair(&*getItem(),i),this));

  // Update data field
  Demand::setCustomer(i);

  // Update the customer for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setCustomer(i);
}


void Forecast::setPriority(int i)
{
  Demand::setPriority(i);
  // Update the priority for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setPriority(i);
}


void Forecast::setOperation(const Operation *o)
{
  Demand::setOperation(o);
  // Update the priority for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setOperation(o);
}


void Forecast::setPolicy(const string& i)
{
  Demand::setPolicy(i);
  // Update the priority for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setPolicy(i);
}


void Forecast::addPolicy(const string& i)
{
  Demand::addPolicy(i);
  // Update the priority for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->addPolicy(i);
}

}       // end namespace
