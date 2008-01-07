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


#include "forecast.h"

namespace module_forecast
{

const XMLtag tag_total("total");
const XMLtag tag_net("net");
const XMLtag tag_consumed("consumed");


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


Forecast::~Forecast()
{
  // Update the dictionary
  for (MapOfForecasts::iterator x=
    ForecastDictionary.lower_bound(make_pair(&*getItem(),&*getCustomer()));
    x != ForecastDictionary.end(); ++x)
    if (x->second == this)
    {
      ForecastDictionary.erase(x);
      return;
    }

  // Delete all children demands
  for(memberIterator i = beginMember(); i != endMember(); i = beginMember())
    delete &*i;
}


void Forecast::initialize()
{
  if (!calptr) throw DataException("Missing forecast calendar");

  // Create a demand for every bucket. The weight value depends on the
  // calendar type: float, integer, bool or other
  const CalendarFloat* c = dynamic_cast<const CalendarFloat*>(calptr);
  ForecastBucket* prev = NULL;
  if (c)
    // Float calendar
    for (CalendarFloat::BucketIterator i = c->beginBuckets();
      i != c->endBuckets(); ++i)
    {
      if (c->getValue(i) > 0.0f)
        prev = new ForecastBucket
          (this, i->getStart(), i->getEnd(), c->getValue(i), prev);
      Demand::add(prev);
    }
  else
  {
    const CalendarInt* c = dynamic_cast<const CalendarInt*>(calptr);
    if (c)
      // Integer calendar
      for (CalendarInt::BucketIterator i = c->beginBuckets();
        i != c->endBuckets(); ++i)
      {
        if (c->getValue(i) > 0)
          prev = new ForecastBucket
            (this, i->getStart(), i->getEnd(), static_cast<float>(c->getValue(i)), prev);
        Demand::add(prev);
      }
    else
    {
      const CalendarBool* c = dynamic_cast<const CalendarBool*>(calptr);
      if (c)
        // Boolean calendar
        for (CalendarBool::BucketIterator i = c->beginBuckets();
          i != c->endBuckets(); ++i)
        {
          if (c->getValue(i))
            prev = new ForecastBucket
              (this, i->getStart(), i->getEnd(), 1.0f, prev);
          Demand::add(prev);
        }
      else
        // Other calendar
        for (Calendar::BucketIterator i = calptr->beginBuckets();
          i != calptr->endBuckets(); ++i)
        {
          prev = new ForecastBucket(this, i->getStart(), i->getEnd(), 1, prev);
          Demand::add(prev);
        }
    }
  }
}


void Forecast::setDiscrete(const bool b)
{
  // Update the flag
  discrete = b;

  // Round down any forecast demands that may already exist.
  if (discrete)
    for (memberIterator m = beginMember(); m!=endMember(); ++m)
      m->setQuantity(floor(m->getQuantity()));
}


void Forecast::setTotalQuantity(const DateRange& d, double f)
{
  // Initialize, if not done yet
  if (!isGroup()) initialize();

  // Find all forecast demands, and sum their weights
  double weights = 0;
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
  {
    ForecastBucket* x = dynamic_cast<ForecastBucket*>(&*m);
    if (!x)
      throw DataException("Invalid subdemand of forecast '" + getName() +"'");
    if (d.intersect(x->timebucket))
    {
      // Bucket intersects with daterange
      if (!d.getDuration())
      {
        // Single date provided. Update that one bucket.
        x->setQuantity(f>x->consumed ? static_cast<float>(f - x->consumed) : 0);
        x->total = static_cast<float>(f);
        return;
      }
      weights += x->weight * static_cast<long>(x->timebucket.overlap(d));
    }
  }

  // Expect to find at least one non-zero weight...
  if (!weights)
    throw DataException("No valid forecast date in range "
      + string(d) + " of forecast '" + getName() +"'");

  // Update the forecast quantity, respecting the weights
  f /= static_cast<float>(weights);
  double carryover = 0.0;
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
  {
    ForecastBucket* x = dynamic_cast<ForecastBucket*>(&*m);
    if (d.intersect(x->timebucket))
    {
      // Bucket intersects with daterange
      TimePeriod o = x->timebucket.overlap(d);
      double percent = x->weight * static_cast<long>(o);
      if (getDiscrete())
      {
        // Rounding to discrete numbers
        carryover += f * percent;
        int intdelta = static_cast<int>(ceil(carryover - 0.5));
        carryover -= intdelta;
        if (o < x->timebucket.getDuration())
          // The bucket is only partially updated
          x->total += static_cast<float>(intdelta);
        else
          // The bucket is completely updated
          x->total = static_cast<float>(intdelta);
      }
      else
      {
        // No rounding
        if (o < x->timebucket.getDuration())
          // The bucket is only partially updated
          x->total += static_cast<float>(f * percent);
        else
          // The bucket is completely updated
          x->total = static_cast<float>(f * percent);
      }
      x->setQuantity(x->total > x->consumed ? (x->total - x->consumed) : 0);
    }
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

  o->writeElement(Tags::tag_item, &*getItem());
  if (getPriority()) o->writeElement(Tags::tag_priority, getPriority());
  o->writeElement(Tags::tag_calendar, calptr);
  if (!getDiscrete()) o->writeElement(Tags::tag_discrete, getDiscrete());
  o->writeElement(Tags::tag_operation, &*getOperation());

  // Write all entries
  o->BeginObject (Tags::tag_buckets);
  for (memberIterator i = beginMember(); i != endMember(); ++i)
  {
    ForecastBucket* f = dynamic_cast<ForecastBucket*>(&*i);
    o->BeginObject(Tags::tag_bucket, Tags::tag_start, f->getDue());
    o->writeElement(tag_total, f->total);
    o->writeElement(tag_net, f->getQuantity());
    o->writeElement(tag_consumed, f->consumed);
    o->EndObject(Tags::tag_bucket);
  }
  o->EndObject(Tags::tag_buckets);

  o->EndObject(tag);
}


void Forecast::endElement(XMLInput& pIn, XMLElement& pElement)
{
  // While reading forecast buckets, we use the userarea field on the input
  // to cache the data. The temporary object is deleted when the bucket
  // tag is closed.
  if (pElement.isA(Tags::tag_calendar))
  {
    Calendar *b = dynamic_cast<Calendar*>(pIn.getPreviousObject());
    if (b) setCalendar(b);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pElement.isA(Tags::tag_discrete))
    setDiscrete(pElement.getBool());
  else if (pElement.isA(Tags::tag_bucket))
  {
    pair<DateRange,double> *d =
      static_cast< pair<DateRange,double>* >(pIn.getUserArea());
    if (d)
    {
      // Update the forecast quantities
      setTotalQuantity(d->first, d->second);
      // Clear the read buffer
      d->first.setStart(Date());
      d->first.setEnd(Date());
      d->second = 0;
    }
  }
  else if (pIn.getParentElement().isA(Tags::tag_bucket))
  {
    pair<DateRange,double> *d =
      static_cast< pair<DateRange,double>* >(pIn.getUserArea());
    if (pElement.isA(tag_total))
    {
      if (d) d->second = pElement.getFloat();
      else pIn.setUserArea(
        new pair<DateRange,double>(DateRange(),pElement.getDouble())
        );
    }
    else if (pElement.isA(Tags::tag_start))
    {
      Date x = pElement.getDate();
      if (d)
      {
        if (!d->first.getStart()) d->first.setStartAndEnd(x,x);
        else d->first.setStart(x);
      }
      else pIn.setUserArea(new pair<DateRange,double>(DateRange(x,x),0));
    }
    else if (pElement.isA(Tags::tag_end))
    {
      Date x = pElement.getDate();
      if (d)
      {
        if (!d->first.getStart()) d->first.setStartAndEnd(x,x);
        else d->first.setEnd(x);
      }
      else pIn.setUserArea(new pair<DateRange,double>(DateRange(x,x),0));
    }
  }
  else
    Demand::endElement(pIn, pElement);

  if (pIn.isObjectEnd())
  {
    // Delete dynamically allocated temporary read object
    if (pIn.getUserArea())
      delete static_cast< pair<DateRange,double>* >(pIn.getUserArea());
  }
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


void Forecast::setMaxLateness(TimePeriod i)
{
  Demand::setMaxLateness(i);
  // Update the maximum lateness for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setMaxLateness(i);
}


void Forecast::setMinShipment(float i)
{
  Demand::setMinShipment(i);
  // Update the minimum shipment for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setMinShipment(i);
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

}       // end namespace
