/***************************************************************************
  file : $URL$
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


#include "forecast.h"

namespace module_forecast
{

const MetaClass Forecast::metadata;


MODULE_EXPORT void initialize(const CommandLoadLibrary::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  if (init)
  {
    clog << "Warning: Initializing module forecast more than one." << endl;
    return;
  }
  init = true;

  // Print the parameters
  /*
  for (CommandLoadLibrary::ParameterList::const_iterator 
    j = z.begin(); j!= z.end(); ++j)
    clog << "Parameter " << j->first << " = " << j->second << endl;
  */

  // Initialize the metadata.
  Forecast::metadata.registerClass(
    "DEMAND", 
    "DEMAND_FORECAST", 
    Object::createString<Forecast>);
}


void Forecast::setQuantity(Date d, float f)
{
  // Does a calendar exist already
  if (!calptr)
    throw DataException("Need to specify a forecast calendar first");

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
    l->setItem(getItem());
    l->setQuantity(qty);
    l->setDue(b.getStart());
    l->setPriority(getPriority());
    l->addPolicy(planLate() ? "PLANLATE" : "PLANSHORT");
    l->addPolicy(planSingleDelivery() ? "SINGLEDELIVERY" : "MULTIDELIVERY");
    l->setOperation(getOperation());
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


void Forecast::setCalendar(Calendar* c)
{
  if (isGroup())
  {
    clog << "Warning: Changing the calendar of an initialized forecast isn't " 
     << "allowed." << endl;
    return;
  }
  calptr = c;
}


void Forecast::setItem(Item* i)
{
  Demand::setItem(i);
  // Update the item for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setItem(i);
}


void Forecast::setPriority(int i)
{
  Demand::setPriority(i);
  // Update the priority for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setPriority(i);
}


void Forecast::setOperation(Operation *o)
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
