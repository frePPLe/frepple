/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/calendar.cpp $
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

template<class Calendar> DECLARE_EXPORT Tree HasName<Calendar>::st;


Calendar::~Calendar()
{
  // De-allocate all the dynamic memory used for the bucket objects
  while (firstBucket) 
  {
    Bucket* tmp = firstBucket;
    firstBucket = firstBucket->nextBucket;
    delete tmp;
  }
}


Calendar::Bucket* Calendar::addBucket (Date d)
{
  // Create new bucket and insert in the list
  Bucket *next = firstBucket, *prev = NULL;
  while (next && next->startdate < d) 
  {
    prev = next;
    next = next->nextBucket;
  }
  if (next && next->startdate == d)
  {
    clog << "Warning: Trying to create two buckets with start date " << d
      << " in calendar '" << getName() << "'" << endl;  // @todo or throw excpetion
    return next;
  }

  // Create the new bucket
  Bucket *c = createNewBucket(d);
  c->nextBucket = next;
  c->prevBucket = prev;

  if (prev) 
  {
    // Set end date of previous bucket to the start of this one...
    prev->enddate = d;
    prev->nextBucket = c;
  }
  else
    // This bucket is the first in the list
    firstBucket = c;

  // Set end date of this bucket equal to the start of the next one...
  if (next)
  {
    next->prevBucket = c;
    c->enddate = next->startdate;
  }
  else
    c->enddate = Date::infiniteFuture;

  // Return the new bucket
  return c;
}


void Calendar::removeBucket(Calendar::Bucket* bkt)
{
  // Verify the bucket is on this calendar indeed
  Bucket *b = firstBucket;
  while (b && b != bkt) b = b->nextBucket;

  // Error
  if (!b)
    throw DataException("Trying to remove unavailable bucket from calendar '" 
      + getName() + "'");

  if (bkt->prevBucket) 
  {
    // Previous bucket (if there is one) gets a new end date
    bkt->prevBucket->enddate = bkt->enddate;
    bkt->prevBucket->nextBucket = bkt->nextBucket;
  }
  else
    // Removing the first bucket, and give new head to the bucket list
    firstBucket = bkt->nextBucket;

  // Update the reference prevBucket of the next bucket
  if (bkt->nextBucket)
    bkt->nextBucket->prevBucket = bkt->prevBucket;

  // Delete the bucket
  delete bkt;
}


Calendar::Bucket* Calendar::findBucket(Date d) const
{
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
    if (d <= b->enddate) return b;
  throw LogicException("Unreachable code reached");
}


int Calendar::findBucketIndex(Date d) const
{
  int i = 1;
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
  {
    if (d <= b->enddate) return i;
    ++i;
  }
  throw LogicException("Unreachable code reached");
}


Calendar::Bucket* Calendar::findBucket(const string& d) const
{
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
    if (b->getName() == d) return b;
  return NULL;
}


void Calendar::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
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


Calendar::Bucket* Calendar::createBucket(const Attributes* atts)
{
  // Pick up the start attribute
  char* start =
  	XMLString::transcode(atts->getValue(Tags::tag_start.getXMLCharacters()));
	if (!start)
  {
		XMLString::release(&start);
    throw DataException("Missing the attribute START for creating a bucket");
  }
  Date d;
	d = Date(start);
	XMLString::release(&start);

  // Check for existence of the bucket
  BucketIterator x = beginBuckets();
  while (x!=endBuckets() && x->startdate!=d) ++x;

  // Pick up the action attribute and update the bucket accordingly
  Calendar::Bucket* result = *x;
  switch (MetaData::decodeAction(atts))
  {
    case ADD:
      // Only additions are allowed
      if (x==beginBuckets())
      {
        // The first bucket (starting at minus infinite) is automatically
        // created in a calendar. In this special case, we can allow an add
        // action on a bucket that already exists.
        LockManager::getManager().obtainWriteLock(*x);
        return *x;
      }
      if (x!=endBuckets()) 
        throw("Bucket " + string(d) 
          + " already exists in calenar '" + getName() + "'");
      result = addBucket(d);
      LockManager::getManager().obtainWriteLock(result);
      if (!result->getType().raiseEvent(result, SIG_ADD))
      {
        LockManager::getManager().releaseWriteLock(result);
        removeBucket(result);
        throw DataException("Can't create bucket " + string(d) 
          + " in calendar '" + getName() + "'");
      }
      return result;
    case CHANGE:
      // Only changes are allowed
      if (x==endBuckets())
        throw DataException("Bucket " + string(d)
          + " doesn't exist in calendar '" + getName() + "'");
      LockManager::getManager().obtainWriteLock(*x);
      return *x;
    case REMOVE:
      // Delete the entity
      if (x==endBuckets())
        throw DataException("Bucket " + string(d)
          + " doesn't exist in calendar '" + getName() + "'");
      else
      {
        // Send out the notification to subscribers
        LockManager::getManager().obtainWriteLock(*x);
        if (!x->getType().raiseEvent(*x, SIG_REMOVE))
        {
          // The callbacks disallowed the deletion!
          LockManager::getManager().releaseWriteLock(*x);
          throw DataException("Can't delete calendar bucket " + string(d)
            + " in calendar '" + getName() + "'");
        }
        // Delete it
        removeBucket(*x);
        return NULL;
      }
    case ADD_CHANGE:
      if (x!=endBuckets())
      {
        // Returning existing bucket
        LockManager::getManager().obtainWriteLock(*x);
        return *x;
      }
      // Adding a new bucket
      result = addBucket(d);
      LockManager::getManager().obtainWriteLock(result);
      if (!result->getType().raiseEvent(result, SIG_ADD))
      {
        LockManager::getManager().releaseWriteLock(result);
        removeBucket(result);
        throw DataException("Can't create bucket " + string(d) 
          + " in calendar '" + getName() + "'");
      }
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}


void Calendar::beginElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_bucket)
      && pIn.getParentElement().isA(Tags::tag_buckets))
    // A new bucket
    pIn.readto(createBucket(pIn.getAttributes()));
}


void Calendar::Bucket::writeElement
  (XMLOutput *o, const XMLtag& tag, mode m) const
{
  assert(m == DEFAULT || m == FULL);
  o->BeginObject(Tags::tag_bucket, Tags::tag_start, startdate);
  o->writeElement(Tags::tag_name, nm);
  o->writeElement(Tags::tag_end, enddate);
  o->EndObject(tag);
}


void Calendar::Bucket::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_name))
    pElement >> nm;
}

} // end namespace
