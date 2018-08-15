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

template<class Calendar> Tree<string> utils::HasName<Calendar>::st;
const MetaCategory* Calendar::metadata;
const MetaClass *CalendarDefault::metadata;
const MetaCategory* CalendarBucket::metacategory;
const MetaClass* CalendarBucket::metadata;


int Calendar::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Calendar>("calendar", "calendars", reader, finder);
  registerFields<Calendar>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<Calendar>::getPythonType();
  x.addMethod(
    "setValue", setPythonValue, METH_VARARGS | METH_KEYWORDS,
    "update the value in a date range"
    );
  x.addMethod(
    "events", getEvents, METH_VARARGS,
    "return an event iterator"
    );
  int ok = FreppleCategory<Calendar>::initialize();
  ok += CalendarEventIterator::initialize();
  return ok;
}


int CalendarBucket::initialize()
{
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<CalendarBucket>(
    "bucket", "buckets", reader
    );
  registerFields<CalendarBucket>(const_cast<MetaCategory*>(metacategory));
  metadata = MetaClass::registerClass<CalendarBucket>(
    "bucket", "bucket",
    Object::create<CalendarBucket>, true
    );

  // Initialize the Python class
  PythonType& x = FreppleCategory<CalendarBucket>::getPythonType();
  x.setName(metadata->type);
  x.setDoc("frePPLe " + metadata->type);
  x.supportgetattro();
  x.supportsetattro();
  x.supportstr();
  x.supportcompare();
  x.supportcreate(Object::create<CalendarBucket>);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


int CalendarDefault::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<CalendarDefault>("calendar", "calendar_default",
      Object::create<CalendarDefault>, true);

  // Initialize the Python class
  return FreppleClass<CalendarDefault, Calendar>::initialize();
}


/** Updates the value in a certain date range.<br>
  * This will create a new bucket if required. */
void Calendar::setValue(Date start, Date end, const double v)
{
  CalendarBucket* x = static_cast<CalendarBucket*>(findBucket(start));
  if (x && x->getStart() == start && x->getEnd() <= end)
    // We can update an existing bucket: it has the same start date
    // and ends before the new effective period ends.
    x->setEnd(end);
  else
  {
    // Creating a new bucket
    x = new CalendarBucket();
    x->setStart(start);
    x->setEnd(end);
    x->setCalendar(this);
  }
  x->setValue(v);
  x->setPriority(lowestPriority() - 1);
}


Calendar::~Calendar()
{
  // De-allocate all the dynamic memory used for the bucket objects
  while (firstBucket)
  {
    CalendarBucket* tmp = firstBucket;
    firstBucket = firstBucket->nextBucket;
    delete tmp;
  }

  // Remove all references from locations
  for (auto l = Location::begin(); l != Location::end(); ++l)
  {
    if (l->getAvailable() == this)
      l->setAvailable(nullptr);
  }

  // Remove reference from buffers
  for (auto b = Buffer::begin(); b != Buffer::end(); ++b)
  {
    if (b->getMaximumCalendar() == this)
      b->setMaximumCalendar(nullptr);
    if (b->getMinimumCalendar() == this)
      b->setMinimumCalendar(nullptr);
  }

  // Remove references from resources
  for (auto r = Resource::begin(); r != Resource::end(); ++r)
  {
    if (r->getMaximumCalendar() == this)
      r->setMaximumCalendar(nullptr);
    if (r->getEfficiencyCalendar() == this)
      r->setEfficiencyCalendar(nullptr);
    if (r->getAvailable() == this)
      r->setAvailable(nullptr);
  }

  // Remove references from operations
  for (auto o = Operation::begin(); o != Operation::end(); ++o)
  {
    if (o->getAvailable() == this)
      o->setAvailable(nullptr);
    if (o->getSizeMinimumCalendar() == this)
      o->setSizeMinimumCalendar(nullptr);
  }

  // Remove reference on plan
  if (Plan::instance().getCalendar() == this)
    Plan::instance().setCalendar(nullptr);
}


void Calendar::removeBucket(CalendarBucket* bkt, bool del)
{
  // Verify the bucket is on this calendar indeed
  CalendarBucket *b = firstBucket;
  while (b && b != bkt)
    b = b->nextBucket;

  // Error
  if (!b)
    throw DataException("Trying to remove unavailable bucket from calendar '"
        + getName() + "'");

  // Update the list
  if (bkt->prevBucket)
    // Previous bucket links to a new next bucket
    bkt->prevBucket->nextBucket = bkt->nextBucket;
  else
    // New head for the bucket list
    firstBucket = bkt->nextBucket;
  if (bkt->nextBucket)
    // Update the reference prevBucket of the next bucket
    bkt->nextBucket->prevBucket = bkt->prevBucket;

  // Delete the bucket
  bkt->nextBucket = nullptr;
  bkt->prevBucket = nullptr;
  bkt->cal = nullptr;
  if (del)
    delete bkt;
}


CalendarBucket::~CalendarBucket()
{
  if (!cal)
    return;

  // Update the list
  if (prevBucket)
    // Previous bucket links to a new next bucket
    prevBucket->nextBucket = nextBucket;
  else
    // New head for the bucket list
    cal->firstBucket = nextBucket;
  if (nextBucket)
    // Update the reference prevBucket of the next bucket
    nextBucket->prevBucket = prevBucket;
  cal->eventlist.clear();
}


void CalendarBucket::setEnd(const Date d)
{
  // Check
  if (d < startdate)
    throw DataException("Calendar bucket end must be later than its start");

  // Update
  enddate = d;
}


void CalendarBucket::setStart(const Date d)
{
  // Check
  if (d > enddate)
    throw DataException("Calendar bucket start must be earlier than its end");

  // Update the field
  startdate = d;

  // Keep the list in sorted order
  updateSort();
}


void CalendarBucket::updateSort()
{
  // Update the position in the list
  if (!cal) return;
  bool ok = true;
  do
  {
    ok = true;
    if (nextBucket && (
      nextBucket->startdate < startdate ||
      (nextBucket->startdate == startdate && nextBucket->priority < priority)
      ))
    {
      // Move a position later in the list
      if (nextBucket->nextBucket)
        nextBucket->nextBucket->prevBucket = this;
      if (prevBucket)
        prevBucket->nextBucket = nextBucket;
      else
        cal->firstBucket = nextBucket;
      nextBucket->prevBucket = prevBucket;
      prevBucket = nextBucket;
      CalendarBucket* tmp = nextBucket->nextBucket;
      nextBucket->nextBucket = this;
      nextBucket = tmp;
      ok = false;
    }
    else if (prevBucket && (
      prevBucket->startdate > startdate ||
      (prevBucket->startdate == startdate && prevBucket->priority > priority)
      ))
    {
      // Move a position earlier in the list
      if (prevBucket->prevBucket)
        prevBucket->prevBucket->nextBucket = this;
      if (nextBucket)
        nextBucket->prevBucket = prevBucket;
      prevBucket->nextBucket = nextBucket;
      nextBucket = prevBucket;
      CalendarBucket* tmp = prevBucket->prevBucket;
      prevBucket->prevBucket = this;
      prevBucket = tmp;
      ok = false;
    }
  }
  while (!ok); // Repeat till in place
}


double Calendar::getValue(const Date d, bool forward) const
{
  if (eventlist.empty())
  {
    CalendarBucket* x = findBucket(d, forward);
    return x ? x->getValue() : defaultValue;
  }
  else
  {
    auto event = forward ? eventlist.upper_bound(d) : eventlist.lower_bound(d);
    if (event != eventlist.begin())
    {
      --event;      
      if (event != eventlist.end())
        return event->second;
      else
        return getDefault();
      return event->second;
    }
    else if (eventlist.empty())
      return getDefault();
    else
      return eventlist.rbegin()->second;
  }
}


CalendarBucket* Calendar::findBucket(Date d, bool fwd) const
{
  CalendarBucket *curBucket = nullptr;
  double curPriority = DBL_MAX;
  int date_weekday = -1;
  Duration date_time;
  for (CalendarBucket *b = firstBucket; b; b = b->nextBucket)
  {
    if (b->getStart() > d)
      // Buckets are sorted by the start date. Other entries definitely
      // won't be effective.
      break;
    else if (curPriority > b->getPriority()
        && ( (fwd && d >= b->getStart() && d < b->getEnd()) ||
            (!fwd && d > b->getStart() && d <= b->getEnd())
           ))
    {
      if (b->isContinuouslyEffective())
      {
        // Continuously effective
        curPriority = b->getPriority();
        curBucket = &*b;
      }
      else
      {
        // There are ineffective periods during the week
        if (date_weekday < 0)
        {
          // Lazily get the details on the date, if not done already
          struct tm datedetail;
          d.getInfo(&datedetail);
          date_weekday = datedetail.tm_wday; // 0: sunday, 6: saturday
          date_time = long(datedetail.tm_sec + datedetail.tm_min * 60 + datedetail.tm_hour * 3600);
          if (!date_time && !fwd)
          {
            date_time = Duration(86400L);
            if (--date_weekday < 0)
              date_weekday = 6;
          }
        }
        if (b->days & (1 << date_weekday))
        {
          // Effective on the requested date
          if ((fwd && date_time >= b->starttime && date_time < b->endtime) ||
              (!fwd && date_time > b->starttime && date_time <= b->endtime))
          {
            // Also falls within the effective hours.
            // All conditions are met!
            curPriority = b->getPriority();
            curBucket = &*b;
          }
        }
      }
    }
  }
  return curBucket;
}


CalendarBucket* Calendar::addBucket(Date st, Date nd, double val)
{
  CalendarBucket* bckt = new CalendarBucket();
  bckt->setCalendar(this);
  bckt->setStart(st);
  bckt->setEnd(nd);
  bckt->setValue(val);
  return bckt;
}


Object* CalendarBucket::reader(
  const MetaClass* cat, const DataValueDict& atts, CommandManager* mgr
  )
{
  // Pick up the calendar
  const DataValue* cal_val = atts.get(Tags::calendar);
  Calendar *cal = cal_val ? static_cast<Calendar*>(cal_val->getObject()) : nullptr;

  // Pick up the start date.
  const DataValue* strtElement = atts.get(Tags::start);
  Date strt;
  if (strtElement)
    strt = strtElement->getDate();

  // Pick up the end date.
  const DataValue* endElement = atts.get(Tags::end);
  Date nd = Date::infiniteFuture;
  if (endElement)
    nd = endElement->getDate();

  // Pick up  the priority
  const DataValue* prioElement = atts.get(Tags::priority);
  int prio = 0;
  if (prioElement)
    prio = prioElement->getInt();

  // Check for existence of a bucket with the same start, end and priority
  CalendarBucket* result = nullptr;
  if (cal)
  {
    for (CalendarBucket::iterator i = cal->getBuckets(); i != CalendarBucket::iterator::end(); ++i)
      if (i->getStart() == strt && i->getEnd() == nd && i->getPriority() == prio)
      {
        result = &*i;
        break;
      }
  }

  // Pick up the action attribute and update the bucket accordingly
  switch (MetaClass::decodeAction(atts))
  {
    case ADD:
      // Only additions are allowed
      if (result)
      {
        ostringstream o;
        o << "Bucket already exists in calendar '" << cal << "'";
        throw DataException(o.str());
      }
      result = new CalendarBucket();
      result->setStart(strt);
      result->setEnd(nd);
      result->setPriority(prio);
      if (cal)
        result->setCalendar(cal);
      if (mgr)
        mgr->add(new CommandCreateObject(result));
      return result;
    case CHANGE:
      // Only changes are allowed
      if (!result)
        throw DataException("Bucket doesn't exist");
      return result;
    case REMOVE:
      // Delete the entity
      if (!result)
        throw DataException("Bucket doesn't exist");
      else
      {
        // Delete it
        cal->removeBucket(result);
        return nullptr;
      }
    case ADD_CHANGE:
      if (!result)
      {
        // Adding a new bucket
        result = new CalendarBucket();
        result->setStart(strt);
        result->setEnd(nd);
        result->setPriority(prio);
        if (cal)
          result->setCalendar(cal);
        if (mgr)
          mgr->add(new CommandCreateObject(result));
      }
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}


void CalendarBucket::setCalendar(Calendar* c)
{
  if (cal == c)
    return;

  // Unlink from the previous calendar
  if (cal)
  {
    cal->removeBucket(this, false);
    cal->eventlist.clear();
  }
  cal = c;

  // Link in the list of buckets of the new calendar
  if (cal)
  {
    if (cal->firstBucket)
    {
      cal->firstBucket->prevBucket = this;
      nextBucket = cal->firstBucket;
    }
    cal->firstBucket = this;
    updateSort();
    cal->eventlist.clear();
  }
}


Calendar::EventIterator::EventIterator
  (Calendar* c, Date d, bool forward)
  : theCalendar(c)
{
  if (!theCalendar)
    return;

  if (
    theCalendar->eventlist.empty() 
    || d < theCalendar->eventlist.begin()->first 
    || d > theCalendar->eventlist.rbegin()->first
    )
      theCalendar->buildEventList(d);
  
  curDate = d;
  if (forward)
  {
    cacheiter = theCalendar->eventlist.lower_bound(d);
    if (cacheiter != theCalendar->eventlist.end() && cacheiter->first > d)
      --cacheiter;
    if (cacheiter == theCalendar->eventlist.end())
      curValue = theCalendar->getDefault();
    else
      curValue = cacheiter->second;
  }
  else
  {
    cacheiter = theCalendar->eventlist.lower_bound(d);
    if (cacheiter != theCalendar->eventlist.end() && cacheiter->first > d)
      --cacheiter;
    if (cacheiter == theCalendar->eventlist.end())
      curValue = theCalendar->getDefault();
    else
      curValue = cacheiter->second;
  }
}


Calendar::EventIterator& Calendar::EventIterator::operator++()
{
  if (cacheiter != theCalendar->eventlist.end())
  {
    ++cacheiter;    
    if (cacheiter == theCalendar->eventlist.end())
    {
      // Extend the event list if possible
      auto lastDate = theCalendar->eventlist.rbegin()->first;
      if (!theCalendar->eventlist.empty() && lastDate != Date::infiniteFuture)
      {            
        theCalendar->buildEventList(lastDate);
        cacheiter = theCalendar->eventlist.find(lastDate);
        ++cacheiter;
      }
    }
  }
  if (cacheiter == theCalendar->eventlist.end())
  {
    curDate = Date::infiniteFuture;
    curValue = theCalendar->getDefault();
  }
  else
  {
    curDate = cacheiter->first;
    curValue = cacheiter->second;
  }
  return *this;
}


Calendar::EventIterator& Calendar::EventIterator::operator--()
{
  if (cacheiter == theCalendar->eventlist.end())
  {
    curValue = theCalendar->getDefault();
    curDate = Date::infinitePast;
  }
  else
  {
    curDate = cacheiter->first;
    --cacheiter;    
    if (cacheiter == theCalendar->eventlist.end())
    {
      auto firstDate = theCalendar->eventlist.begin()->first;
      if (!theCalendar->eventlist.empty() && firstDate != Date::infinitePast)
      {
        // Extend the event list     
        theCalendar->buildEventList(firstDate);
        cacheiter = theCalendar->eventlist.find(firstDate);
      }
    }
    if (cacheiter == theCalendar->eventlist.end())
      curValue = theCalendar->getDefault();
    else
      curValue = cacheiter->second;
  }
  return *this;
}


void Calendar::buildEventList(Date includedate)
{
  // Default start and end
  Date curDate;
  if (eventlist.empty())
    curDate = Plan::instance().getCurrent() - Duration(86400L * 365L);
  else
    curDate = eventlist.begin()->first;
  Date maxDate;
  if (eventlist.empty())
    maxDate = Plan::instance().getCurrent() + Duration(86400L * 365L);
  else
    maxDate = eventlist.rbegin()->first;

  // Assure the argument date is included
  if (includedate == Date::infinitePast)
    curDate = Date::infinitePast;
  else if (includedate <= curDate)
    curDate = includedate - Duration(86400L * 365L);
  if (includedate == Date::infiniteFuture)
    maxDate = Date::infiniteFuture;
  else if (includedate >= maxDate)
    maxDate = includedate + Duration(86400L * 365L);
  
  // Collect all event dates
  const CalendarBucket* curBucket = findBucket(curDate, true);
  const CalendarBucket* lastBucket = curBucket;
  int curPriority = curBucket ? curBucket->priority : INT_MAX;
  int lastPriority = curPriority;
  bool first = true;
  while (true)
  {
    if (first)
    {
      eventlist[Date::infinitePast] = curBucket ? curBucket->getValue() : getDefault();
      first = false;
    }
    else       
    {
      eventlist[curDate] = curBucket ? curBucket->getValue() : getDefault();
      if (curDate > maxDate || curDate == Date::infiniteFuture)
        break;
    }

    // Go over all entries and ask them to update the iterator
    Date refDate = curDate;
    curDate = Date::infiniteFuture;
    for (const CalendarBucket *b = firstBucket; b; b = b->nextBucket)
    {
      // FIRST CASE: Bucket that is continuously effective
      if (b->isContinuouslyEffective())
      {
        // Evaluate the start date of the bucket
        if (refDate < b->startdate && b->priority <= lastPriority && (
          b->startdate < curDate ||
          (b->startdate == curDate && b->priority <= curPriority)
          ))
        {
          curDate = b->startdate;
          curBucket = b;
          curPriority = b->priority;
          continue;
        }

        // Next evaluate the end date of the bucket
        if (refDate < b->enddate && b->enddate <= curDate && lastBucket == b)
        {
          curDate = b->enddate;
          curBucket = findBucket(b->enddate);
          curPriority = curBucket ? curBucket->priority : INT_MAX;
          continue;
        }

        // This bucket won't create next event
        continue;
      }

      // SECOND CASE: Interruptions in effectivity.

      // Find details on the reference date
      bool effectiveAtStart = false;
      Date tmp = refDate;
      struct tm datedetail;
      if (refDate < b->startdate)
        tmp = b->startdate;
      tmp.getInfo(&datedetail);
      int ref_weekday = datedetail.tm_wday; // 0: sunday, 6: saturday
      Duration ref_time = long(datedetail.tm_sec + datedetail.tm_min * 60 + datedetail.tm_hour * 3600);
      if (
        refDate < b->startdate && ref_time >= b->starttime
        && ref_time < b->endtime && (b->days & (1 << ref_weekday))
        )
        effectiveAtStart = true;

      if (ref_time >= b->starttime && !effectiveAtStart
        && ref_time < b->endtime && (b->days & (1 << ref_weekday)))
      {
        // Entry is currently effective.
        if (!b->starttime && b->endtime == Duration(86400L))
        {
          // The next event is the start of the next ineffective day
          tmp -= ref_time;
          while (b->days & (1 << ref_weekday) && tmp != Date::infiniteFuture)
          {
            if (++ref_weekday > 6)
              ref_weekday = 0;
            tmp += Duration(86400L);
          }
        }
        else
          // The next event is the end date on the current day
          tmp += b->endtime - ref_time;
        if (tmp > b->enddate)
          tmp = b->enddate;

        // Evaluate the result
        if (refDate < tmp && tmp <= curDate && lastBucket == b)
        {
          curDate = tmp;
          curBucket = findBucket(tmp);
          curPriority = curBucket ? curBucket->priority : INT_MAX;
        }
      }
      else
      {
        // Reference date is before the start time on an effective date
        // or it is after the end time of an effective date
        // or it is on an ineffective day.

        // The next event is the start date, either today or on the next
        // effective day.
        tmp += b->starttime - ref_time;
        if (ref_time >= b->endtime && (b->days & (1 << ref_weekday)))
        {
          if (++ref_weekday > 6)
            ref_weekday = 0;
          tmp += Duration(86400L);
        }
        while (!(b->days & (1 << ref_weekday)) && tmp != Date::infiniteFuture && tmp <= b->enddate)
        {
          if (++ref_weekday > 6)
            ref_weekday = 0;
          tmp += Duration(86400L);
        }
        if (tmp < b->startdate)
          tmp = b->startdate;
        if (tmp >= b->enddate)
          continue;

        // Evaluate the result
        if (refDate < tmp && b->priority <= lastPriority && (
          tmp < curDate ||
          (tmp == curDate && b->priority <= curPriority)
          ))
        {
          curDate = tmp;
          curBucket = b;
          curPriority = b->priority;
        }
      }
    }

    // Remember the bucket that won the evaluation
    lastBucket = curBucket;
    lastPriority = curPriority;
  }
}


PyObject* Calendar::setPythonValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarDefault *cal = static_cast<CalendarDefault*>(self);
    if (!cal) throw LogicException("Can't set value of a nullptr calendar");

    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
    if (!PyArg_ParseTuple(args, "OOO:setValue", &pystart, &pyend, &pyval))
      return nullptr;

    // Update the calendar
    PythonData start(pystart), end(pyend), val(pyval);
    cal->setValue(start.getDate(), end.getDate(), val.getDouble());
  }
  catch(...)
  {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}


PyObject* Calendar::getEvents(
  PyObject* self, PyObject* args
)
{
  try
  {
    // Pick up the calendar
    Calendar *cal = nullptr;
    PythonData c(self);
    if (c.check(CalendarDefault::metadata))
      cal = static_cast<CalendarDefault*>(self);
    else
      throw LogicException("Invalid calendar type");

    // Parse the arguments
    PyObject* pystart = nullptr;
    PyObject* pydirection = nullptr;
    if (!PyArg_ParseTuple(args, "|OO:getEvents", &pystart, &pydirection))
      return nullptr;
    Date startdate = pystart ? PythonData(pystart).getDate() : Date::infinitePast;
    bool forward = pydirection ? PythonData(pydirection).getBool() : true;

    // Return the iterator
    return new CalendarEventIterator(cal, startdate, forward);
  }
  catch(...)
  {
    PythonType::evalException();
    return nullptr;
  }
}


int CalendarEventIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<CalendarEventIterator>::getPythonType();
  x.setName("calendarEventIterator");
  x.setDoc("frePPLe iterator for calendar events");
  x.supportiter();
  return x.typeReady();
}


PyObject* CalendarEventIterator::iternext()
{
  if ((forward && eventiter.getDate() == Date::infiniteFuture)
      || (!forward && eventiter.getDate() == Date::infinitePast))
    return nullptr;
  PyObject* result = Py_BuildValue("(O,O)",
      static_cast<PyObject*>(PythonData(eventiter.getDate())),
      static_cast<PyObject*>(PythonData(eventiter.getValue()))
      );
  if (forward)
    ++eventiter;
  else
    --eventiter;
  return result;
}

} // end namespace
