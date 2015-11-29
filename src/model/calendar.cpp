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

template<class Calendar> DECLARE_EXPORT Tree utils::HasName<Calendar>::st;
DECLARE_EXPORT const MetaCategory* Calendar::metadata;
DECLARE_EXPORT const MetaClass *CalendarDefault::metadata;
DECLARE_EXPORT const MetaCategory* CalendarBucket::metacategory;
DECLARE_EXPORT const MetaClass* CalendarBucket::metadata;


int Calendar::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Calendar>("calendar", "calendars", reader, finder);
  registerFields<Calendar>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleCategory<Calendar>::getPythonType();
  x.addMethod(
    "addBucket", addPythonBucket, METH_VARARGS | METH_KEYWORDS,
    "find a bucket or create a new one"
    );
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
    "bucket", "buckets", createBucket
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
  // TODO x.supportcreate(create);
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
DECLARE_EXPORT void Calendar::setValue(Date start, Date end, const double v)
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
  x->setPriority(lowestPriority()-1);
}


DECLARE_EXPORT Calendar::~Calendar()
{
  // De-allocate all the dynamic memory used for the bucket objects
  while (firstBucket)
  {
    CalendarBucket* tmp = firstBucket;
    firstBucket = firstBucket->nextBucket;
    delete tmp;
  }

  // Remove all references from locations
  for (Location::iterator l = Location::begin(); l != Location::end(); ++l)
  {
    if (l->getAvailable() == this)
      l->setAvailable(NULL);
  }

  // Remove reference from buffers
  for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
  {
    if (b->getMaximumCalendar() == this)
      b->setMaximumCalendar(NULL);
    if (b->getMinimumCalendar() == this)
      b->setMinimumCalendar(NULL);
  }

  // Remove references from resources
  for (Resource::iterator r = Resource::begin(); r != Resource::end(); ++r)
  {
    if (r->getMaximumCalendar() == this)
      r->setMaximumCalendar(NULL);
  }
}


DECLARE_EXPORT void Calendar::removeBucket(CalendarBucket* bkt)
{
  // Verify the bucket is on this calendar indeed
  CalendarBucket *b = firstBucket;
  while (b && b != bkt) b = b->nextBucket;

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
  delete bkt;
}


DECLARE_EXPORT void CalendarBucket::setEnd(const Date d)
{
  // Check
  if (d < startdate)
    throw DataException("Calendar bucket end must be later than its start");

  // Update
  enddate = d;
}


DECLARE_EXPORT void CalendarBucket::setStart(const Date d)
{
  // Check
  if (d > enddate)
    throw DataException("Calendar bucket start must be earlier than its end");

  // Update the field
  startdate = d;

  // Keep the list in sorted order
  updateSort();
}


DECLARE_EXPORT void CalendarBucket::updateSort()
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


DECLARE_EXPORT CalendarBucket* Calendar::findBucket(Date d, bool fwd) const
{
  CalendarBucket *curBucket = NULL;
  double curPriority = DBL_MAX;
  long timeInWeek = INT_MIN;
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
      if (!b->offsetcounter)
      {
        // Continuously effective
        curPriority = b->getPriority();
        curBucket = &*b;
      }
      else
      {
        // There are ineffective periods during the week
        if (timeInWeek == INT_MIN)
        {
          // Lazy initialization
          timeInWeek = d.getSecondsWeek();
          // Special case: asking backward while at first second of the week
          if (!fwd && timeInWeek == 0L) timeInWeek = 604800L;
        }
        // Check all intervals
        for (short i=0; i<b->offsetcounter; i+=2)
          if ((fwd && timeInWeek >= b->offsets[i] && timeInWeek < b->offsets[i+1]) ||
              (!fwd && timeInWeek > b->offsets[i] && timeInWeek <= b->offsets[i+1]))
          {
            // All conditions are met!
            curPriority = b->getPriority();
            curBucket = &*b;
            break;
          }
      }
    }
  }
  return curBucket;
}


DECLARE_EXPORT CalendarBucket* Calendar::findBucket(int ident) const
{
  for (CalendarBucket *b = firstBucket; b; b = b->nextBucket)
    if (b->id == ident) return b;
  return NULL;
}


DECLARE_EXPORT CalendarBucket* Calendar::addBucket(Date st, Date nd, double val)
{
  CalendarBucket* bckt = new CalendarBucket();
  bckt->setCalendar(this);
  bckt->setStart(st);
  bckt->setEnd(nd);
  bckt->setValue(val);
  return bckt;
}


DECLARE_EXPORT Object* CalendarBucket::createBucket(
  const MetaClass* cat, const DataValueDict& atts
  )
{
  // Pick up the calendar and id fields
  const DataValue* cal_val = atts.get(Tags::calendar);
  Calendar *cal = cal_val ? static_cast<Calendar*>(cal_val->getObject()) : NULL;
  const DataValue* id_val = atts.get(Tags::id);
  int id = id_val ? id_val->getInt() : INT_MIN;

  // Check for existence of a bucket with the same identifier
  CalendarBucket* result = NULL;
  if (cal)
    result = cal->findBucket(id);

  // Pick up the action attribute and update the bucket accordingly
  switch (MetaClass::decodeAction(atts))
  {
    case ADD:
      // Only additions are allowed
      if (result)
      {
        ostringstream o;
        o << "Bucket " << id << " already exists in calendar '" << cal << "'";
        throw DataException(o.str());
      }
      result = new CalendarBucket();
      result->setId(id);
      if (cal) result->setCalendar(cal);
      return result;
    case CHANGE:
      // Only changes are allowed
      if (!result)
      {
        ostringstream o;
        o << "Bucket " << id << " doesn't exist in calendar '"
          << (cal ? cal->getName() : "NULL") << "'";
        throw DataException(o.str());
      }
      return result;
    case REMOVE:
      // Delete the entity
      if (!result)
      {
        ostringstream o;
        o << "Bucket " << id << " doesn't exist in calendar '"
          << (cal ? cal->getName() : "NULL") << "'";
        throw DataException(o.str());
      }
      else
      {
        // Delete it
        cal->removeBucket(result);
        return NULL;
      }
    case ADD_CHANGE:
      if (!result)
      {
        // Adding a new bucket
        result = new CalendarBucket();
        result->setId(id);
        if (cal) result->setCalendar(cal);
      }
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}


DECLARE_EXPORT void CalendarBucket::writeHeader(Serializer *o, const Keyword& tag) const
{
  // The header line has a variable number of attributes: start, end and/or name
  if (startdate != Date::infinitePast)
  {
    if (enddate != Date::infiniteFuture)
      o->BeginObject(tag, Tags::id, id, Tags::start, startdate, Tags::end, enddate);
    else
      o->BeginObject(tag, Tags::id, id, Tags::start, startdate);
  }
  else
  {
    if (enddate != Date::infiniteFuture)
      o->BeginObject(tag, Tags::id, id, Tags::end, enddate);
    else
      o->BeginObject(tag, Tags::id, id);
  }
}


DECLARE_EXPORT void CalendarBucket::setCalendar(Calendar* c)
{
  if (cal == c)
    return;
  if (cal)
    throw DataException("Can't reassign a calendar bucket to a new calendar");

  // Generate a unique id
  cal = c;
  setId(id);

  // Link in the list of buckets
  if (cal->firstBucket)
  {
    cal->firstBucket->prevBucket = this;
    nextBucket = cal->firstBucket;
  }
  cal->firstBucket = this;
  updateSort();
}


DECLARE_EXPORT void CalendarBucket::setId(int ident)
{
  if (cal)
  {
    if (ident == INT_MIN)
    {
      // Force generation of a new identifier.
      // This is done by taking the highest existing id and adding 1.
      for (CalendarBucket::iterator i = cal->getBuckets(); i != CalendarBucket::iterator::end(); ++i)
        if (i->id >= ident)
          ident = i->id + 1;
      if (ident == INT_MIN)
        ident = 1;
    }
    else
    {
      // Check & enforce uniqueness of the argument identifier
      bool unique;
      do
      {
        unique = true;
        for (CalendarBucket::iterator i = cal->getBuckets(); i != CalendarBucket::iterator::end(); ++i)
          if (i->id == ident && &(*i) != this)
          {
            // Update the identifier to avoid violating the uniqueness
            unique = false;
            ++ident;
            break;
          }
      }
      while (!unique);
    }
  }

  // Update the identifier
  id = ident;
}


DECLARE_EXPORT Calendar::EventIterator::EventIterator
  (const Calendar* c, Date d, bool forward)
  : theCalendar(c), curDate(d)
{
  curBucket = lastBucket = c ? c->findBucket(d,forward) : NULL;
  curPriority = lastPriority = curBucket ? curBucket->priority : INT_MAX;
}


DECLARE_EXPORT Calendar::EventIterator& Calendar::EventIterator::operator++()
{
  if (!theCalendar)
    throw LogicException("Can't walk forward on event iterator of NULL calendar.");

  // Go over all entries and ask them to update the iterator
  Date d = curDate;
  curDate = Date::infiniteFuture;
  for (const CalendarBucket *b = theCalendar->firstBucket; b; b = b->nextBucket)
    nextEvent(b, d);

  // Remember the bucket that won the evaluation
  lastBucket = curBucket;
  lastPriority = curPriority;
  return *this;
}


DECLARE_EXPORT Calendar::EventIterator& Calendar::EventIterator::operator--()
{
  if (!theCalendar)
    throw LogicException("Can't walk backward on event iterator of NULL calendar.");

  // Go over all entries and ask them to update the iterator
  Date d = curDate;
  curDate = Date::infinitePast;
  for (const CalendarBucket *b = theCalendar->firstBucket; b; b = b->nextBucket)
    prevEvent(b, d);

  // Remember the bucket that won the evaluation
  lastBucket = curBucket;
  lastPriority = curPriority;
  return *this;
}


DECLARE_EXPORT void Calendar::EventIterator::nextEvent(const CalendarBucket* b, Date refDate)
{
  // FIRST CASE: Bucket that is continuously effective
  if (!b->offsetcounter)
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
      return;
    }

    // Next evaluate the end date of the bucket
    if (refDate < b->enddate && b->enddate <= curDate && lastBucket == b)
    {
      curDate = b->enddate;
      curBucket = theCalendar->findBucket(b->enddate);
      curPriority = curBucket ? curBucket->priority : INT_MAX;
      return;
    }

    // End function: this bucket won't create next event
    return;
  }

  // SECOND CASE: Interruptions in effectivity.

  // Jump to the start date
  bool allowEqualAtStart = false;
  if (refDate < b->startdate && (
    b->startdate < curDate ||
    (b->startdate == curDate && b->priority <= curPriority)
    ))
  {
    refDate = b->startdate;
    allowEqualAtStart = true;
  }

  // Find position in the week
  long timeInWeek = refDate.getSecondsWeek();

  // Loop over all effective days in the week in which refDate falls
  for (short i=0; i<b->offsetcounter; i += 2)
  {
    // Start and end date of this effective period
    Date st = refDate + Duration(b->offsets[i] - timeInWeek);
    Date nd = refDate + Duration(b->offsets[i+1] - timeInWeek);

    // Move to next week if required
    bool canReturn = true;
    if (refDate >= nd)
    {
      st += Duration(86400L*7);
      nd += Duration(86400L*7);
      canReturn = false;
    }

    // Check enddate and startdate are not violated
    if (st < b->startdate)
    {
      if (nd < b->startdate)
        continue;  // No overlap with overall effective dates
      else
        st = b->startdate;
    }
    if (nd >= b->enddate)
    {
      if (st >= b->enddate)
        continue;  // No overlap with effective range
      else
        nd = b->enddate;
    }

    if ((refDate < st || (allowEqualAtStart && refDate == st)) && b->priority <= lastPriority)
    {
      if (st > curDate || (st == curDate && b->priority > curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // The effective start on this weekday qualifies as the next event
      curDate = st;
      curBucket = b;
      curPriority = b->priority;
      if (canReturn) return;
    }
    if (refDate < nd && lastBucket == b)
    {
      if (nd > curDate || (nd == curDate && b->priority > curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // This bucket is currently effective.
      // The effective end on this weekday qualifies as the next event.
      curDate = nd;
      curBucket = theCalendar->findBucket(nd);
      curPriority = curBucket ? curBucket->priority : INT_MAX;
      if (canReturn) return;
    }
  }
}


DECLARE_EXPORT void Calendar::EventIterator::prevEvent(const CalendarBucket* b, Date refDate)
{
  // FIRST CASE: Bucket that is continuously effective
  if (!b->offsetcounter)
  {
    // First evaluate the end date of the bucket
    if (refDate > b->enddate && b->priority <= lastPriority && (
       b->enddate > curDate ||
       (b->enddate == curDate && b->priority < curPriority)
      ))
    {
      curDate = b->enddate;
	    curBucket = b;
      curPriority = b->priority;
      return;
    }

    // Next evaluate the start date of the bucket
    if (refDate > b->startdate && b->startdate > curDate && lastBucket == b)
    {
      curDate = b->startdate;
      curBucket = theCalendar->findBucket(b->startdate, false);
      curPriority = curBucket ? curBucket->priority : INT_MAX;
      return;
    }

    // End function: this bucket won't create the previous event
    return;
  }

  // SECOND CASE: Interruptions in effectivity.

  // Jump to the end date
  bool allowEqualAtEnd = false;
  if (refDate > b->enddate && (
    b->enddate > curDate ||
    (b->enddate == curDate && b->priority < curPriority)
    ))
  {
    refDate = b->enddate;
    allowEqualAtEnd = true;
  }

  // Find position in the week
  long timeInWeek = refDate.getSecondsWeek();

  // Loop over all effective days in the week in which refDate falls
  for (short i=b->offsetcounter-1; i>=0; i-=2)
  {
    // Start and end date of this effective period
    Date st = refDate + Duration(b->offsets[i] - timeInWeek);
    Date nd = refDate + Duration(b->offsets[i+1] - timeInWeek);

    // Move to previous week if required
    bool canReturn = true;
    if (refDate <= st)
    {
      st -= Duration(86400L*7);
      nd -= Duration(86400L*7);
      canReturn = false;
    }

    // Check enddate and startdate are not violated
    if (st <= b->startdate)
    {
      if (nd <= b->startdate)
        continue;  // No overlap with overall effective dates
      else
        st = b->startdate;
    }
    if (nd > b->enddate)
    {
      if (st > b->enddate)
        continue;  // No overlap with effective range
      else
        nd = b->enddate;
    }

    if ((refDate > nd || (allowEqualAtEnd && refDate == nd))
      && b->priority <= lastPriority)
    {
      if (nd < curDate || (nd == curDate && b->priority <= curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // The effective end on this weekday qualifies as the next event
      curDate = nd;
      curBucket = b;
      if (canReturn) return;
    }
    if (refDate > st && lastBucket == b)
    {
      if (st < curDate || (st == curDate && b->priority <= curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // This bucket is currently effective.
      // The effective end on this weekday qualifies as the next event.
      curDate = st;
      curBucket = theCalendar->findBucket(st, false);
      curPriority = curBucket ? curBucket->priority : INT_MAX;
      if (canReturn) return;
    }
  }
}


DECLARE_EXPORT PyObject* Calendar::setPythonValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarDefault *cal = static_cast<CalendarDefault*>(self);
    if (!cal) throw LogicException("Can't set value of a NULL calendar");

    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
    if (!PyArg_ParseTuple(args, "OOO:setValue", &pystart, &pyend, &pyval))
      return NULL;

    // Update the calendar
    PythonData start(pystart), end(pyend), val(pyval);
    cal->setValue(start.getDate(), end.getDate(), val.getDouble());
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* Calendar::addPythonBucket(PyObject* self, PyObject* args, PyObject* kwdict) // TODO Remove this method. Calendarbuckets now have a good Python API
{
  try
  {
    // Pick up the calendar
    Calendar* cal = static_cast<Calendar*>(self);
    if (!cal) throw LogicException("Can't set value of a NULL calendar");

    // Parse the arguments
    int id = INT_MIN;
    if (!PyArg_ParseTuple(args, "|i:addBucket", &id))
      return NULL;

    // See if the bucket exists, or create it
    CalendarBucket * b = NULL;
    if (id != INT_MIN)
      b = cal->findBucket(id);
    if (!b)
    {
      b = new CalendarBucket();
      b->setCalendar(cal);
      if (id != INT_MIN)
        b->setId(id);
    }

    // Return a reference
    Py_INCREF(b);
    return b;
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* Calendar::getEvents(
  PyObject* self, PyObject* args
)
{
  try
  {
    // Pick up the calendar
    Calendar *cal = NULL;
    PythonData c(self);
    if (c.check(CalendarDefault::metadata))
      cal = static_cast<CalendarDefault*>(self);
    else
      throw LogicException("Invalid calendar type");

    // Parse the arguments
    PyObject* pystart = NULL;
    PyObject* pydirection = NULL;
    if (!PyArg_ParseTuple(args, "|OO:setvalue", &pystart, &pydirection))
      return NULL;
    Date startdate = pystart ? PythonData(pystart).getDate() : Date::infinitePast;
    bool forward = pydirection ? PythonData(pydirection).getBool() : true;

    // Return the iterator
    return new CalendarEventIterator(cal, startdate, forward);
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
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
    return NULL;
  PythonData x;
  if (dynamic_cast<CalendarDefault*>(cal))
  {
    if (eventiter.getBucket())
      x = PythonData(dynamic_cast<const CalendarBucket*>(eventiter.getBucket())->getValue());
    else
      x = PythonData(dynamic_cast<CalendarDefault*>(cal)->getDefault());
  }
  else
    // Unknown calendar type we can't iterate
    return NULL;
  PyObject* result = Py_BuildValue("(N,N)",
      static_cast<PyObject*>(PythonData(eventiter.getDate())),
      static_cast<PyObject*>(x)
      );
  if (forward)
    ++eventiter;
  else
    --eventiter;
  return result;
}


DECLARE_EXPORT void CalendarBucket::updateOffsets()
{
  if (days==127 && !starttime && endtime==Duration(86400L))
  {
    // Bucket is effective continuously. No need to update the structure.
    offsetcounter = 0;
    return;
  }

  offsetcounter = -1;
  short tmp = days;
  for (short i=0; i<=6; ++i)
  {
    // Loop over all days in the week
    if (tmp & 1)
    {
      if (offsetcounter>=1 && (offsets[offsetcounter] == 86400*i + starttime))
        // Special case: the start date of todays offset entry
        // is the end date yesterdays entry. We can just update the
        // end date of that entry.
        offsets[offsetcounter] = 86400*i + endtime;
      else
      {
        // New offset pair
        offsets[++offsetcounter] = 86400*i + starttime;
        offsets[++offsetcounter] = 86400*i + endtime;
      }
    }
    tmp = tmp>>1; // Shift to the next bit
  }

  // Special case: there is no gap between the end of the last event in the
  // week and the next event in the following week.
  if (offsetcounter >= 1 && offsets[0]==0 && offsets[offsetcounter]==86400*7)
  {
    offsets[0] = offsets[offsetcounter-1] - 86400*7;
    offsets[offsetcounter] = 86400*7 + offsets[1];
  }
}

} // end namespace
