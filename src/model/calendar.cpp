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

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Calendar> DECLARE_EXPORT Tree HasName<Calendar>::st;


DECLARE_EXPORT Calendar::~Calendar()
{
  // De-allocate all the dynamic memory used for the bucket objects
  while (firstBucket)
  {
    Bucket* tmp = firstBucket;
    firstBucket = firstBucket->nextBucket;
    delete tmp;
  }
}


DECLARE_EXPORT CalendarFloat::~CalendarFloat()
{
  // Remove all references from buffers
  for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
  {
    if (b->getMinimum()==this) Buffer::writepointer(&*b)->setMinimum(NULL);
    if (b->getMaximum()==this) Buffer::writepointer(&*b)->setMaximum(NULL);
  }

  // Remove all references from resources
  for (Resource::iterator r = Resource::begin(); r != Resource::end(); ++r)
    if (r->getMaximum()==this) Resource::writepointer(&*r)->setMaximum(NULL);
}


DECLARE_EXPORT CalendarBool::~CalendarBool()
{
  // Remove all references from locations
  for (Location::iterator l = Location::begin(); l != Location::end(); ++l)
  {
    if (l->getAvailable() == this) 
      Location::writepointer(&*l)->setAvailable(NULL);
  }
}


DECLARE_EXPORT Calendar::Bucket* Calendar::addBucket 
  (Date start, Date end, string name)
{
  // Assure the start is before the end.
  if (start > end)
  {
    // Switch arguments
    Date tmp = end;
    end = start;
    start = end;
  }

  // Create new bucket and insert in the list
  Bucket *next = firstBucket, *prev = NULL;
  while (next && next->startdate < start)
  {
    prev = next;
    next = next->nextBucket;
  }

  // Create the new bucket
  Bucket *c = createNewBucket(start,end,name);
  c->nextBucket = next;
  c->prevBucket = prev;

  // Maintain linked list
  if (prev) prev->nextBucket = c;
  else firstBucket = c;
  if (next) next->prevBucket = c;

  // Return the new bucket
  return c;
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


DECLARE_EXPORT Calendar::Bucket* Calendar::findBucket(Date d) const
{
  Calendar::Bucket *curBucket = NULL;
  float curPriority;
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
  {
    if (b->getStart() > d) 
      // Buckets are sorted by the start date. Other entries definately 
      // won't be effective
      break;
    else if ((!curBucket || curPriority > b->getPriority()) 
      && d >= b->getStart() && d < b->getEnd()
      && b->checkValid(d) )
    {
      // Bucket is effective and has lower priority than other effective ones.
      curPriority = b->getPriority();
      curBucket = &*b;
    }
  }
  return curBucket;
}


DECLARE_EXPORT Calendar::Bucket* Calendar::findBucket(const string& d) const
{
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
    if (b->getName() == d) return b;
  return NULL;
}


DECLARE_EXPORT void Calendar::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
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

  // Write all buckets
  o->BeginObject (Tags::tag_buckets);
  for (BucketIterator i = beginBuckets(); i != endBuckets(); ++i)
    // We use the FULL mode, to force the buckets being written regardless
    // of the depth in the XML tree.
    o->writeElement(Tags::tag_bucket, *i, FULL);
  o->EndObject(Tags::tag_buckets);

  o->EndObject(tag);
}


DECLARE_EXPORT Calendar::Bucket* Calendar::createBucket(const Attributes* atts)
{
  // Pick up the start, end and name attributes
  char* s;
  s = XMLString::transcode(atts->getValue(Tags::tag_start.getXMLCharacters()));
  Date startdate(s);
  XMLString::release(&s);
  s = XMLString::transcode(atts->getValue(Tags::tag_end.getXMLCharacters()));
  Date enddate = Date::infiniteFuture;
  if (s) enddate = Date(s);
  XMLString::release(&s);
  s = XMLString::transcode(atts->getValue(Tags::tag_name.getXMLCharacters()));
  string name;
  if (s) name = s;
  XMLString::release(&s);

  // Check for existence of the bucket: same name, start date and end date
  Calendar::Bucket* result = NULL;
  for (BucketIterator x = beginBuckets(); x!=endBuckets(); ++x)
  {
    if ((!name.empty() && x->nm==name)
      || (name.empty() && x->startdate==startdate && x->enddate==enddate))
    {
      // Found!
      result = &*x;
      break;
    }
  }  

  // Pick up the action attribute and update the bucket accordingly
  switch (MetaClass::decodeAction(atts))
  {
    case ADD:
      // Only additions are allowed
      if (result)
        throw("Bucket " + string(startdate) + " " + string(enddate) + " " + name
            + " already exists in calendar '" + getName() + "'");
      result = addBucket(startdate, enddate, name);
      return result;
    case CHANGE:
      // Only changes are allowed
      if (!result)
        throw DataException("Bucket " + string(startdate) + " " + string(enddate) 
            + " " + name + " doesn't exist in calendar '" + getName() + "'");
      return result;
    case REMOVE:
      // Delete the entity
      if (!result)
        throw DataException("Bucket " + string(startdate) + " " + string(enddate) 
            + " " + name + " doesn't exist in calendar '" + getName() + "'");
      else
      {
        // Delete it
        removeBucket(result);
        return NULL;
      }
    case ADD_CHANGE:
      if (!result)
        // Adding a new bucket
        result = addBucket(startdate, enddate, name);
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}


DECLARE_EXPORT void Calendar::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_bucket)
      && pIn.getParentElement().isA(Tags::tag_buckets))
    // A new bucket
    pIn.readto(createBucket(pIn.getAttributes()));
}


DECLARE_EXPORT void Calendar::Bucket::writeHeader(XMLOutput *o) const
{
  // The header line has a variable number of attributes: start, end and/or name
  if (startdate != Date::infinitePast)
  {
    if (enddate != Date::infiniteFuture)
    {
      if (!nm.empty())
        o->BeginObject(Tags::tag_bucket, Tags::tag_start, string(startdate), Tags::tag_end, string(enddate), Tags::tag_name, nm);
      else
        o->BeginObject(Tags::tag_bucket, Tags::tag_start, string(startdate), Tags::tag_end, string(enddate));
    }
    else
    {
      if (!nm.empty())
        o->BeginObject(Tags::tag_bucket, Tags::tag_start, string(startdate), Tags::tag_name, nm);
      else
        o->BeginObject(Tags::tag_bucket, Tags::tag_start, string(startdate));
    }
  }
  else
  {
    if (enddate != Date::infiniteFuture)
    {
      if (!nm.empty())
        o->BeginObject(Tags::tag_bucket, Tags::tag_end, string(enddate), Tags::tag_name, nm);
      else
        o->BeginObject(Tags::tag_bucket, Tags::tag_end, string(enddate));
    }
    else
    {
      if (!nm.empty())
        o->BeginObject(Tags::tag_bucket, Tags::tag_name, nm);
      else
        o->BeginObject(Tags::tag_bucket);
    }
  }  
}


DECLARE_EXPORT void Calendar::Bucket::writeElement
(XMLOutput *o, const XMLtag& tag, mode m) const
{
  assert(m == DEFAULT || m == FULL);
  writeHeader(o);
  if (priority) o->writeElement(Tags::tag_priority, priority);
  o->EndObject(tag);
}


DECLARE_EXPORT void Calendar::Bucket::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_priority))
    pElement >> priority;
}


DECLARE_EXPORT Calendar::EventIterator& Calendar::EventIterator::operator++()
{
  // Go over all entries and ask them to update the iterator
  Date d = curDate;
  curDate = Date::infiniteFuture;  // Cause end date is not included
  curBucket = NULL;
  curPriority = FLT_MAX;
  for (const Calendar::Bucket *b = theCalendar->firstBucket; b; b = b->nextBucket)
    b->nextEvent(this, d);
  return *this;
}


DECLARE_EXPORT Calendar::EventIterator& Calendar::EventIterator::operator--()
{
  // Go over all entries and ask them to update the iterator
  Date d = curDate;
  curDate = Date::infinitePast;
  curBucket = NULL;
  curPriority = FLT_MAX;
  for (const Calendar::Bucket *b = theCalendar->firstBucket; b; b = b->nextBucket)
    b->prevEvent(this, d);
  return *this;
}


DECLARE_EXPORT void Calendar::Bucket::nextEvent(EventIterator* iter, Date refDate) const
{
  if (iter->curPriority < priority)
    // Priority isn't low enough to overrule current date
    return;

  if (refDate < startdate && startdate <= iter->curDate)
  {
    // Next event is the start date of the bucket
    iter->curDate = startdate; 
    iter->curBucket = this;
    iter->curPriority = priority;
    return;
  }

  if (refDate < enddate && enddate < iter->curDate)
  {
    // Next event is the end date of the bucket
    iter->curDate = enddate;
    iter->curBucket = iter->theCalendar->findBucket(enddate);
    iter->curPriority = priority;
    return;
  }
}


DECLARE_EXPORT void Calendar::Bucket::prevEvent(EventIterator* iter, Date refDate) const
{
  if (iter->curPriority < priority)
    // Priority isn't low enough to overrule current date
    return;

  if (refDate >= enddate && enddate > iter->curDate)
  {
    // Previous event is the end date of the bucket
    iter->curDate = enddate;
    iter->curBucket = iter->theCalendar->findBucket(enddate);
    iter->curPriority = priority;
    return;
  }

  if (refDate >= startdate && startdate >= iter->curDate)
  {
    // Previous event is the start date of the bucket
    iter->curDate = startdate;   
    iter->curBucket = this;
    iter->curPriority = priority;
    return;
  }
}


} // end namespace
