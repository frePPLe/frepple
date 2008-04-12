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

const Keyword tag_total("total");
const Keyword tag_net("net");
const Keyword tag_consumed("consumed");


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
  // calendar type: double, integer, bool or other
  const CalendarDouble* c = dynamic_cast<const CalendarDouble*>(calptr);
  ForecastBucket* prev = NULL;
  Date prevDate;
  double prevValue(0.0);
  if (c)
    // Double calendar
    for (CalendarDouble::EventIterator i(c); i.getDate()<=Date::infiniteFuture; ++i)
    {
      if ((prevDate || i.getDate() == Date::infiniteFuture) && prevValue > 0.0)
      {
        prev = new ForecastBucket
          (this, prevDate, i.getDate(), prevValue, prev);
        Demand::add(prev);
      }
      if (i.getDate() == Date::infiniteFuture) break;
      prevDate = i.getDate();
      prevValue = i.getValue();
    }
  else
  {
    const CalendarInt* c = dynamic_cast<const CalendarInt*>(calptr);
    if (c)
      // Integer calendar
      for (CalendarInt::EventIterator i(c); i.getDate()<=Date::infiniteFuture; ++i)
      {
        if ((prevDate || i.getDate() == Date::infiniteFuture) && prevValue > 0)
        {
          prev = new ForecastBucket
            (this, prevDate, i.getDate(), prevValue, prev);
          Demand::add(prev);
        }
        if (i.getDate() == Date::infiniteFuture) break;
        prevDate = i.getDate();
        prevValue = static_cast<double>(i.getValue());
      }
    else
    {
      const CalendarBool* c = dynamic_cast<const CalendarBool*>(calptr);
      bool prevValueBool = false;
      if (c)
        // Boolean calendar
        for (CalendarBool::EventIterator i(c); i.getDate()<=Date::infiniteFuture; ++i)
        {
          if ((prevDate || i.getDate() == Date::infiniteFuture) && prevValueBool)
          {
            prev = new ForecastBucket
                (this, prevDate, i.getDate(), 1.0, prev);
            Demand::add(prev);         
            }
          if (i.getDate() == Date::infiniteFuture) break;
          prevDate = i.getDate();
          prevValueBool = i.getValue();
        }
      else
      {
        // Other calendar
        for (Calendar::EventIterator i(calptr); i.getDate()<=Date::infiniteFuture; ++i)
        {
          if (prevDate || i.getDate() == Date::infiniteFuture)
          {
            prev = new ForecastBucket(this, prevDate, i.getDate(), 1.0, prev);
            Demand::add(prev);
            if (i.getDate() == Date::infiniteFuture) break;
          }
          prevDate = i.getDate();
        }
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
  double weights = 0.0;
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
        x->setQuantity(f>x->consumed ? (f - x->consumed) : 0);
        x->total = f;
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
  f /= weights;
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
          x->total += static_cast<double>(intdelta);
        else
          // The bucket is completely updated
          x->total = static_cast<double>(intdelta);
      }
      else
      {
        // No rounding
        if (o < x->timebucket.getDuration())
          // The bucket is only partially updated
          x->total += f * percent;
        else
          // The bucket is completely updated
          x->total = f * percent;
      }
      x->setQuantity(x->total > x->consumed ? (x->total - x->consumed) : 0);
    }
  }
}


void Forecast::writeElement(XMLOutput *o, const Keyword &tag, mode m) const
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
    o->BeginObject(Tags::tag_bucket, Tags::tag_start, string(f->getDue()));
    o->writeElement(tag_total, f->total);
    o->writeElement(tag_net, f->getQuantity());
    o->writeElement(tag_consumed, f->consumed);
    o->EndObject(Tags::tag_bucket);
  }
  o->EndObject(Tags::tag_buckets);

  o->EndObject(tag);
}


void Forecast::endElement(XMLInput& pIn, const Attribute& pAttr, DataElement& pElement)
{
  // While reading forecast buckets, we use the userarea field on the input
  // to cache the data. The temporary object is deleted when the bucket
  // tag is closed.
  if (pAttr.isA(Tags::tag_calendar))
  {
    Calendar *b = dynamic_cast<Calendar*>(pIn.getPreviousObject());
    if (b) setCalendar(b);
    else throw LogicException("Incorrect object type during read operation");
  }
  else if (pAttr.isA(Tags::tag_discrete))
    setDiscrete(pElement.getBool());
  else if (pAttr.isA(Tags::tag_bucket))
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
  else if (pIn.getParentElement().first.isA(Tags::tag_bucket))
  {
    pair<DateRange,double> *d =
      static_cast< pair<DateRange,double>* >(pIn.getUserArea());
    if (pAttr.isA(tag_total))
    {
      if (d) d->second = pElement.getDouble();
      else pIn.setUserArea(
        new pair<DateRange,double>(DateRange(),pElement.getDouble())
        );
    }
    else if (pAttr.isA(Tags::tag_start))
    {
      Date x = pElement.getDate();
      if (d)
      {
        if (!d->first.getStart()) d->first.setStartAndEnd(x,x);
        else d->first.setStart(x);
      }
      else pIn.setUserArea(new pair<DateRange,double>(DateRange(x,x),0));
    }
    else if (pAttr.isA(Tags::tag_end))
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
    Demand::endElement(pIn, pAttr, pElement);

  if (pIn.isObjectEnd())
  {
    // Delete dynamically allocated temporary read object
    if (pIn.getUserArea())
      delete static_cast< pair<DateRange,double>* >(pIn.getUserArea());
  }
}


void Forecast::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA(Tags::tag_calendar))
    pIn.readto( Calendar::reader(Calendar::metadata, pIn) );
  else
    Demand::beginElement(pIn, pAttr);
}


void Forecast::setCalendar(Calendar* c)
{
  if (isGroup())
    throw DataException(
      "Changing the calendar of an initialized forecast isn't allowed.");
  calptr = c;
}


void Forecast::setItem(Item* i)
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


void Forecast::setCustomer(Customer* i)
{
  // No change
  if (getCustomer() == i) return;

  // Update the dictionary
  for (MapOfForecasts::iterator x =
    ForecastDictionary.lower_bound(make_pair(
      getItem(), getCustomer()
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


void Forecast::setMinShipment(double i)
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


void Forecast::setOperation(Operation *o)
{
  Demand::setOperation(o);
  // Update the priority for all buckets/subdemands
  for (memberIterator m = beginMember(); m!=endMember(); ++m)
    m->setOperation(o);
}

}       // end namespace
