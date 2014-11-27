/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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
DECLARE_EXPORT const MetaCategory* Calendar::Bucket::metadata;
DECLARE_EXPORT const MetaClass *CalendarDouble::metadata;
DECLARE_EXPORT const MetaClass *CalendarDouble::BucketDouble::metadata;


int Calendar::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("calendar", "calendars", reader, writer);

  // Initialize the Python class
  FreppleCategory<Calendar>::getType().addMethod(
    "addBucket", addPythonBucket, METH_VARARGS | METH_KEYWORDS,
    "find a bucket or create a new one"
    );
  int ok = Calendar::Bucket::initialize();
  ok +=  FreppleCategory<Calendar>::initialize();
  ok += CalendarBucketIterator::initialize();
  ok += CalendarEventIterator::initialize();
  ok += CalendarDouble::BucketDouble::initialize();
  return ok;
}


int Calendar::Bucket::initialize()
{
  // Initialize the metadata
  metadata = new MetaCategory("bucket", "buckets");

  // Initialize the Python class
  PythonType& x = FreppleCategory<Calendar::Bucket>::getType();
  x.setName(metadata->type);
  x.setDoc("frePPLe " + metadata->type);
  x.supportgetattro();
  x.supportsetattro();
  x.supportstr();
  x.supportcompare();
  const_cast<MetaCategory*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


void Calendar::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_source))
    setSource(pElement.getString());
}


int CalendarDouble::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass("calendar", "calendar_double",
      Object::createString<CalendarDouble>, true);

  // Initialize the Python class
  FreppleClass<CalendarDouble,Calendar>::getType().addMethod(
    "setValue", setPythonValue, METH_VARARGS | METH_KEYWORDS,
    "update the value in a date range"
    );
  FreppleClass<CalendarDouble,Calendar>::getType().addMethod("events",
    getEvents, METH_VARARGS, "return an event iterator");
  return FreppleClass<CalendarDouble,Calendar>::initialize();
}


int CalendarDouble::BucketDouble::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass("bucket", "bucket_double");

  // Initialize the Python class
  PythonType& x = FreppleClass<CalendarDouble::BucketDouble,Calendar::Bucket>::getType();
  x.setName(metadata->type);
  x.setDoc("frePPLe " + metadata->type);
  x.supportgetattro();
  x.supportsetattro();
  x.supportstr();
  x.supportcompare();
  x.setBase(Calendar::Bucket::metadata->pythonClass);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


/** Updates the value in a certain date range.<br>
  * This will create a new bucket if required. */
void CalendarDouble::setValue(Date start, Date end, const double v)
{
  BucketDouble* x = static_cast<BucketDouble*>(findBucket(start));
  if (x && x->getStart() == start && x->getEnd() <= end)
    // We can update an existing bucket: it has the same start date
    // and ends before the new effective period ends.
    x->setEnd(end);
  else
    // Creating a new bucket
    x = static_cast<BucketDouble*>(addBucket(start,end));
  x->setValue(v);
  x->setPriority(lowestPriority()-1);
}


void CalendarDouble::writeElement(Serializer *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL)
    o->BeginObject(tag, Tags::tag_name, getName());

  // Write the source field
  o->writeElement(Tags::tag_source, getSource());

  // Write the default value
  if (getDefault()) o->writeElement(Tags::tag_default, getDefault());

  // Write all buckets
  o->BeginList (Tags::tag_buckets);
  for (BucketIterator i = beginBuckets(); i != endBuckets(); ++i)
    // We use the FULL mode, to force the buckets being written regardless
    // of the depth in the XML tree.
    o->writeElement(Tags::tag_bucket, *i, FULL);
  o->EndList(Tags::tag_buckets);

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


void CalendarDouble::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_default))
    pElement >> defaultValue;
  else
    Calendar::endElement(pIn, pAttr, pElement);
}


DECLARE_EXPORT Calendar::~Calendar()
{
  // De-allocate all the dynamic memory used for the bucket objects
  while (firstBucket)
  {
    Bucket* tmp = firstBucket;
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


DECLARE_EXPORT CalendarDouble::~CalendarDouble()
{
  // Remove all references from buffers
  for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
  {
    if (b->getMinimumCalendar()==this) b->setMinimumCalendar(NULL);
    if (b->getMaximumCalendar()==this) b->setMaximumCalendar(NULL);
  }

  // Remove all references from resources
  for (Resource::iterator r = Resource::begin(); r != Resource::end(); ++r)
    if (r->getMaximumCalendar()==this) r->setMaximumCalendar(NULL);
}


DECLARE_EXPORT Calendar::Bucket* Calendar::addBucket
(Date start, Date end, int id)
{
  // Assure the start is before the end.
  if (start > end)
    return createNewBucket(end, start, id);
  else
    return createNewBucket(start, end, id);
}


DECLARE_EXPORT void Calendar::removeBucket(Calendar::Bucket* bkt)
{
  // Verify the bucket is on this calendar indeed
  Bucket *b = firstBucket;
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


DECLARE_EXPORT void Calendar::Bucket::setEnd(const Date d)
{
  // Check
  if (d < startdate)
    throw DataException("Calendar bucket end must be later than its start");

  // Update
  enddate = d;
}


DECLARE_EXPORT void Calendar::Bucket::setStart(const Date d)
{
  // Check
  if (d > enddate)
    throw DataException("Calendar bucket start must be earlier than its end");

  // Update the field
  startdate = d;

  // Keep the list in sorted order
  updateSort();
}


DECLARE_EXPORT void Calendar::Bucket::updateSort()
{
  // Update the position in the list
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
      Calendar::Bucket* tmp = nextBucket->nextBucket;
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
      Calendar::Bucket* tmp = prevBucket->prevBucket;
      prevBucket->prevBucket = this;
      prevBucket = tmp;
      ok = false;
    }
  }
  while (!ok); // Repeat till in place
}


DECLARE_EXPORT Calendar::Bucket* Calendar::findBucket(Date d, bool fwd) const
{
  Calendar::Bucket *curBucket = NULL;
  double curPriority = DBL_MAX;
  long timeInWeek = INT_MIN;
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
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


DECLARE_EXPORT Calendar::Bucket* Calendar::findBucket(int ident) const
{
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
    if (b->id == ident) return b;
  return NULL;
}


DECLARE_EXPORT void Calendar::writeElement(Serializer *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the head
  if (m != NOHEAD && m != NOHEADTAIL) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write source field
  o->writeElement(Tags::tag_source, getSource());

  // Write all buckets
  o->BeginList (Tags::tag_buckets);
  for (BucketIterator i = beginBuckets(); i != endBuckets(); ++i)
    // We use the FULL mode, to force the buckets being written regardless
    // of the depth in the XML tree.
    o->writeElement(Tags::tag_bucket, *i, FULL);
  o->EndList(Tags::tag_buckets);

  // Write the custom fields
  PythonDictionary::write(o, getDict());

  // Write the tail
  if (m != NOHEADTAIL && m != NOTAIL) o->EndObject(tag);
}


DECLARE_EXPORT Calendar::Bucket* Calendar::createBucket(const AttributeList& atts)
{
  // Pick up the start, end and name attributes
  const DataElement* d = atts.get(Tags::tag_start);
  Date startdate = *d ? d->getDate() : Date::infinitePast;
  d = atts.get(Tags::tag_end);
  Date enddate = *d ? d->getDate() : Date::infiniteFuture;
  d = atts.get(Tags::tag_id);
  int id = *d ? d->getInt() : INT_MIN;

  // Check for existence of the bucket with the same identifier
  Calendar::Bucket* result = findBucket(id);

  // Pick up the action attribute and update the bucket accordingly
  switch (MetaClass::decodeAction(atts))
  {
    case ADD:
      // Only additions are allowed
      if (result)
      {
        ostringstream o;
        o << "Bucket " << id << " already exists in calendar '" << getName() << "'";
        throw DataException(o.str());
      }
      result = addBucket(startdate, enddate, id);
      return result;
    case CHANGE:
      // Only changes are allowed
      if (!result)
      {
        ostringstream o;
        o << "Bucket " << id << " doesn't exist in calendar '" << getName() << "'";
        throw DataException(o.str());
      }
      return result;
    case REMOVE:
      // Delete the entity
      if (!result)
      {
        ostringstream o;
        o << "Bucket " << id << " doesn't exist in calendar '" << getName() << "'";
        throw DataException(o.str());
      }
      else
      {
        // Delete it
        removeBucket(result);
        return NULL;
      }
    case ADD_CHANGE:
      if (!result)
        // Adding a new bucket
        result = addBucket(startdate, enddate, id);
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}


DECLARE_EXPORT void Calendar::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_bucket)
      && pIn.getParentElement().first.isA(Tags::tag_buckets))
    // A new bucket
    pIn.readto(createBucket(pIn.getAttributes()));
  else
    PythonDictionary::read(pIn, pAttr, getDict());
}


DECLARE_EXPORT void Calendar::Bucket::writeHeader(Serializer *o, const Keyword& tag) const
{
  // The header line has a variable number of attributes: start, end and/or name
  if (startdate != Date::infinitePast)
  {
    if (enddate != Date::infiniteFuture)
      o->BeginObject(tag, Tags::tag_id, id, Tags::tag_start, startdate, Tags::tag_end, enddate);
    else
      o->BeginObject(tag, Tags::tag_id, id, Tags::tag_start, startdate);
  }
  else
  {
    if (enddate != Date::infiniteFuture)
      o->BeginObject(tag, Tags::tag_id, id, Tags::tag_end, enddate);
    else
      o->BeginObject(tag, Tags::tag_id, id);
  }
}


DECLARE_EXPORT void Calendar::Bucket::writeElement
(Serializer *o, const Keyword& tag, mode m) const
{
  assert(m == DEFAULT || m == FULL);
  writeHeader(o,tag);
  if (priority) o->writeElement(Tags::tag_priority, priority);
  if (days != 127) o->writeElement(Tags::tag_days, days);
  if (starttime)
    o->writeElement(Tags::tag_starttime, starttime);
  if (endtime != TimePeriod(86400L))
    o->writeElement(Tags::tag_endtime, endtime);
  PythonDictionary::write(o, getDict());
  o->EndObject(tag);
}


DECLARE_EXPORT void Calendar::Bucket::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_priority))
    pElement >> priority;
  else if (pAttr.isA(Tags::tag_days))
    setDays(pElement.getInt());
  else if (pAttr.isA(Tags::tag_starttime))
    setStartTime(pElement.getTimeperiod());
  else if (pAttr.isA(Tags::tag_endtime))
    setEndTime(pElement.getTimeperiod());
}


DECLARE_EXPORT void Calendar::Bucket::setId(int ident)
{
  // Check non-null calendar
  if (!cal)
    throw LogicException("Generating calendar bucket without calendar");

  if (ident == INT_MIN)
  {
    // Force generation of a new identifier.
    // This is done by taking the highest existing id and adding 1.
    for (BucketIterator i = cal->beginBuckets(); i != cal->endBuckets(); ++i)
      if (i->id >= ident) ident = i->id + 1;
    if (ident == INT_MIN) ident = 1;
  }
  else
  {
    // Check & enforce uniqueness of the argument identifier
    bool unique;
    do
    {
      unique = true;
      for (BucketIterator i = cal->beginBuckets(); i != cal->endBuckets(); ++i)
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

  // Update the identifier
  id = ident;
}


DECLARE_EXPORT Calendar::EventIterator& Calendar::EventIterator::operator++()
{
  if (!theCalendar)
    throw LogicException("Can't walk forward on event iterator of NULL calendar.");

  // Go over all entries and ask them to update the iterator
  Date d = curDate;
  curDate = Date::infiniteFuture;
  for (const Calendar::Bucket *b = theCalendar->firstBucket; b; b = b->nextBucket)
    b->nextEvent(this, d);

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
  for (const Calendar::Bucket *b = theCalendar->firstBucket; b; b = b->nextBucket)
    b->prevEvent(this, d);

  // Remember the bucket that won the evaluation
  lastBucket = curBucket;
  lastPriority = curPriority;
  return *this;
}


DECLARE_EXPORT void Calendar::Bucket::nextEvent(EventIterator* iter, Date refDate) const
{
  // FIRST CASE: Bucket that is continuously effective
  if (!offsetcounter)
  {
    // Evaluate the start date of the bucket
    if (refDate < startdate && priority <= iter->lastPriority && (
      startdate < iter->curDate ||
      (startdate == iter->curDate && priority <= iter->curPriority)
      ))
    {
      iter->curDate = startdate;
      iter->curBucket = this;
      iter->curPriority = priority;
      return;
    }

    // Next evaluate the end date of the bucket
    if (refDate < enddate && enddate <= iter->curDate && iter->lastBucket == this)
    {
      iter->curDate = enddate;
      iter->curBucket = iter->theCalendar->findBucket(enddate);
      iter->curPriority = iter->curBucket ? iter->curBucket->priority : INT_MAX;
      return;
    }

    // End function: this bucket won't create next event
    return;
  }

  // SECOND CASE: Interruptions in effectivity.

  // Jump to the start date
  bool allowEqualAtStart = false;
  if (refDate < startdate && (
    startdate < iter->curDate ||
    (startdate == iter->curDate && priority <= iter->curPriority)
    ))
  {
    refDate = startdate;
    allowEqualAtStart = true;
  }

  // Find position in the week
  long timeInWeek = refDate.getSecondsWeek();

  // Loop over all effective days in the week in which refDate falls
  for (short i=0; i<offsetcounter; i+=2)
  {
    // Start and end date of this effective period
    Date st = refDate + TimePeriod(offsets[i] - timeInWeek);
    Date nd = refDate + TimePeriod(offsets[i+1] - timeInWeek);

    // Move to next week if required
    bool canReturn = true;
    if (refDate >= nd)
    {
      st += TimePeriod(86400L*7);
      nd += TimePeriod(86400L*7);
      canReturn = false;
    }

    // Check enddate and startdate are not violated
    if (st < startdate)
    {
      if (nd < startdate)
        continue;  // No overlap with overall effective dates
      else
        st = startdate;
    }
    if (nd >= enddate)
    {
      if (st >= enddate)
        continue;  // No overlap with effective range
      else
        nd = enddate;
    }

    if ((refDate < st || (allowEqualAtStart && refDate == st)) && priority <= iter->lastPriority)
    {
      if (st > iter->curDate || (st == iter->curDate && priority > iter->curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // The effective start on this weekday qualifies as the next event
      iter->curDate = st;
      iter->curBucket = this;
      iter->curPriority = priority;
      if (canReturn) return;
    }
    if (refDate < nd && iter->lastBucket == this)
    {
      if (nd > iter->curDate || (nd == iter->curDate && priority > iter->curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // This bucket is currently effective.
      // The effective end on this weekday qualifies as the next event.
      iter->curDate = nd;
      iter->curBucket = iter->theCalendar->findBucket(nd);
      iter->curPriority = iter->curBucket ? iter->curBucket->priority : INT_MAX;
      if (canReturn) return;
    }
  }
}


DECLARE_EXPORT void Calendar::Bucket::prevEvent(EventIterator* iter, Date refDate) const
{
  // FIRST CASE: Bucket that is continuously effective
  if (!offsetcounter)
  {
    // First evaluate the end date of the bucket
    if (refDate > enddate && priority <= iter->lastPriority && (
       enddate > iter->curDate ||
       (enddate == iter->curDate && priority < iter->curPriority)
      ))
    {
      iter->curDate = enddate;
	    iter->curBucket = this;
      iter->curPriority = priority;
      return;
    }

    // Next evaluate the start date of the bucket
    if (refDate > startdate && startdate > iter->curDate && iter->lastBucket == this)
    {
      iter->curDate = startdate;
      iter->curBucket = iter->theCalendar->findBucket(startdate, false);
      iter->curPriority = iter->curBucket ? iter->curBucket->priority : INT_MAX;
      return;
    }

    // End function: this bucket won't create the previous event
    return;
  }

  // SECOND CASE: Interruptions in effectivity.

  // Jump to the end date
  bool allowEqualAtEnd = false;
  if (refDate > enddate && (
    enddate > iter->curDate ||
    (enddate == iter->curDate && priority < iter->curPriority)
    ))
  {
    refDate = enddate;
    allowEqualAtEnd = true;
  }

  // Find position in the week
  long timeInWeek = refDate.getSecondsWeek();

  // Loop over all effective days in the week in which refDate falls
  for (short i=offsetcounter-1; i>=0; i-=2)
  {
    // Start and end date of this effective period
    Date st = refDate + TimePeriod(offsets[i] - timeInWeek);
    Date nd = refDate + TimePeriod(offsets[i+1] - timeInWeek);

    // Move to previous week if required
    bool canReturn = true;
    if (refDate <= st)
    {
      st -= TimePeriod(86400L*7);
      nd -= TimePeriod(86400L*7);
      canReturn = false;
    }

    // Check enddate and startdate are not violated
    if (st <= startdate)
    {
      if (nd <= startdate)
        continue;  // No overlap with overall effective dates
      else
        st = startdate;
    }
    if (nd > enddate)
    {
      if (st > enddate)
        continue;  // No overlap with effective range
      else
        nd = enddate;
    }

    if ((refDate > nd || (allowEqualAtEnd && refDate == nd))
      && priority <= iter->lastPriority)
    {
      if (nd < iter->curDate || (nd == iter->curDate && priority <= iter->curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // The effective end on this weekday qualifies as the next event
      iter->curDate = nd;
      iter->curBucket = this;
      if (canReturn) return;
    }
    if (refDate > st && iter->lastBucket == this)
    {
      if (st < iter->curDate || (st == iter->curDate && priority <= iter->curPriority))
      {
        // Another bucket is doing better already
        if (canReturn) break;
        else continue;
      }
      // This bucket is currently effective.
      // The effective end on this weekday qualifies as the next event.
      iter->curDate = st;
      iter->curBucket = iter->theCalendar->findBucket(st, false);
      iter->curPriority = iter->curBucket ? iter->curBucket->priority : INT_MAX;
      if (canReturn) return;
    }
  }
}


DECLARE_EXPORT PyObject* Calendar::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_name))
    return PythonObject(getName());
  if (attr.isA(Tags::tag_buckets))
    return new CalendarBucketIterator(this);
  if (attr.isA(Tags::tag_source))
    return PythonObject(getSource());
  return NULL;
}


DECLARE_EXPORT int Calendar::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    setName(field.getString());
  else if (attr.isA(Tags::tag_source))
    setSource(field.getString());
  else
    return -1;  // Error
  return 0;  // OK
}


DECLARE_EXPORT PyObject* CalendarDouble::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_default))
    return PythonObject(getDefault());
  return Calendar::getattro(attr);
}


DECLARE_EXPORT int CalendarDouble::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_default))
    setDefault(field.getDouble());
  else
    return Calendar::setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* CalendarDouble::setPythonValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarDouble *cal = static_cast<CalendarDouble*>(self);
    if (!cal) throw LogicException("Can't set value of a NULL calendar");

    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
    if (!PyArg_ParseTuple(args, "OOO:setValue", &pystart, &pyend, &pyval))
      return NULL;

    // Update the calendar
    PythonObject start(pystart), end(pyend), val(pyval);
    cal->setValue(start.getDate(), end.getDate(), val.getDouble());
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* Calendar::addPythonBucket(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    Calendar* cal = static_cast<Calendar*>(self);
    if (!cal) throw LogicException("Can't set value of a NULL calendar");

    // Parse the arguments
    int id = 1;
    if (!PyArg_ParseTuple(args, "|i:addBucket", &id))
      return NULL;

    // See if the bucket exists, or create it
    Bucket * b = cal->findBucket(id);
    if (!b) b = cal->addBucket(Date::infinitePast, Date::infiniteFuture, id);

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


int CalendarBucketIterator::initialize()
{
  // Initialize the type
  PythonType& x = PythonExtension<CalendarBucketIterator>::getType();
  x.setName("calendarBucketIterator");
  x.setDoc("frePPLe iterator for calendar buckets");
  x.supportiter();
  return x.typeReady();
}


PyObject* CalendarBucketIterator::iternext()
{
  if (i == cal->endBuckets()) return NULL;
  PyObject *result = &*(i++);
  Py_INCREF(result);
  return result;
}


DECLARE_EXPORT PyObject* Calendar::Bucket::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_start))
    return PythonObject(getStart());
  if (attr.isA(Tags::tag_end))
    return PythonObject(getEnd());
  if (attr.isA(Tags::tag_value))
  {
    if (cal->getType() == *CalendarDouble::metadata)
      return PythonObject(dynamic_cast< CalendarDouble::BucketDouble* >(this)->getValue());
    PyErr_SetString(PythonLogicException, "calendar type not recognized");
    return NULL;
  }
  if (attr.isA(Tags::tag_priority))
    return PythonObject(getPriority());
  if (attr.isA(Tags::tag_days))
    return PythonObject(getDays());
  if (attr.isA(Tags::tag_starttime))
    return PythonObject(getStartTime());
  if (attr.isA(Tags::tag_endtime))
    return PythonObject(getEndTime());
  if (attr.isA(Tags::tag_id))
    return PythonObject(getId());
  if (attr.isA(Tags::tag_calendar))
    return PythonObject(getCalendar());
  return NULL;
}


DECLARE_EXPORT int Calendar::Bucket::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_id))
    setId(field.getInt());
  else if (attr.isA(Tags::tag_start))
    setStart(field.getDate());
  else if (attr.isA(Tags::tag_end))
    setEnd(field.getDate());
  else if (attr.isA(Tags::tag_priority))
    setPriority(field.getInt());
  else if (attr.isA(Tags::tag_days))
    setDays(field.getInt());
  else if (attr.isA(Tags::tag_starttime))
    setStartTime(field.getTimeperiod());
  else if (attr.isA(Tags::tag_endtime))
    setEndTime(field.getTimeperiod());
  else if (attr.isA(Tags::tag_value))
  {
    if (cal->getType() == *CalendarDouble::metadata)
      dynamic_cast< CalendarDouble::BucketDouble* >(this)->setValue(field.getDouble());
    else
    {
      PyErr_SetString(PythonLogicException, "calendar type not recognized");
      return -1;
    }
  }
  else
    return -1;
  return 0;
}


DECLARE_EXPORT PyObject* Calendar::getEvents(
  PyObject* self, PyObject* args
)
{
  try
  {
    // Pick up the calendar
    Calendar *cal = NULL;
    PythonObject c(self);
    if (c.check(CalendarDouble::metadata))
      cal = static_cast<CalendarDouble*>(self);
    else
      throw LogicException("Invalid calendar type");

    // Parse the arguments
    PyObject* pystart = NULL;
    PyObject* pydirection = NULL;
    if (!PyArg_ParseTuple(args, "|OO:setvalue", &pystart, &pydirection))
      return NULL;
    Date startdate = pystart ? PythonObject(pystart).getDate() : Date::infinitePast;
    bool forward = pydirection ? PythonObject(pydirection).getBool() : true;

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
  PythonType& x = PythonExtension<CalendarEventIterator>::getType();
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
  PythonObject x;
  if (dynamic_cast<CalendarDouble*>(cal))
  {
    if (eventiter.getBucket())
      x = PythonObject(dynamic_cast<const CalendarDouble::BucketDouble*>(eventiter.getBucket())->getValue());
    else
      x = PythonObject(dynamic_cast<CalendarDouble*>(cal)->getDefault());
  }
  else
    // Unknown calendar type we can't iterate
    return NULL;
  PyObject* result = Py_BuildValue("(N,N)",
      static_cast<PyObject*>(PythonObject(eventiter.getDate())),
      static_cast<PyObject*>(x)
      );
  if (forward)
    ++eventiter;
  else
    --eventiter;
  return result;
}


DECLARE_EXPORT void Calendar::Bucket::updateOffsets()
{
  if (days==127 && !starttime && endtime==TimePeriod(86400L))
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
