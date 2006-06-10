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
  // De-allocate all the dynamic memory used for the Bucket objects
  for(Bucketlist::iterator i = buckets.begin(); i != buckets.end(); ++i)
    delete *i;
}


Calendar::Bucket* Calendar::addBucket (Date d)
{
  // Create new bucket and insert in the list
  Bucketlist::iterator i = buckets.begin(), j = buckets.end();
  while (i!=buckets.end() && (*i)->startdate < d) j=i++;
  if (i!=buckets.end() && (*i)->startdate == d)
  {
    clog << "Warning: Trying to create two buckets with start date " << d
      << " in calendar '" << this << "'" << endl;
    return *i;
  }
  Bucket *c = createNewBucket(d);

  // Set end date of previous bucket to the start of this one...
  if (j != buckets.end()) (*j)->enddate = d;

  // Set end date of this bucket equal to the start of the next one...
  if (i != buckets.end())
  {
    // Inserting in the middle
    buckets.insert(i,c);
    c->enddate = (*i)->startdate;
  }
  else
  {
    // Append at end
    buckets.push_back(c);
    c->enddate = Date::infiniteFuture;
  }
  return c;
}


void Calendar::removeBucket(Calendar::Bucket* bkt)
{
  // Find the bucket in the list
  Bucketlist::iterator i = buckets.begin(), j = buckets.end();
  while (i!=buckets.end() && *i != bkt) j = i++;

  // Error
  if (i==buckets.end())
    throw DataException("Trying to remove unavailable bucket from calendar '" 
      + getName() + "'");

  // Previous bucket (if there is one) gets a new end date
  if (j!=buckets.end()) (*j)->enddate = bkt->enddate;

  // Delete the bucket
  delete bkt;

  // Remove from the list of buckets
  buckets.erase(i);
}


Calendar::Bucket* Calendar::findBucket(Date d) const
{
  for (Bucketlist::const_iterator x = buckets.begin();
       x != buckets.end(); ++x)
    if (d <= (*x)->enddate) return *x;
  throw LogicException("Unreachable code reached");
}


int Calendar::findBucketIndex(Date d) const
{
  int i = 1;
  for (Bucketlist::const_iterator x = buckets.begin();
       x != buckets.end(); ++x)
  {
    if (d <= (*x)->enddate) return i;
    ++i;
  }
  throw LogicException("Unreachable code reached");
}


Calendar::Bucket* Calendar::findBucket(const string& d) const
{
  for (Bucketlist::const_iterator x = buckets.begin(); x != buckets.end(); ++x)
    if ((*x)->getName() == d) return *x;
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
  for (Bucketlist::const_iterator i = buckets.begin(); i != buckets.end();)
    // We use the FULL mode, to force the buckets being written regardless
    // of the depth in the XML tree.
    o->writeElement(Tags::tag_bucket, *(i++), FULL);
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
  Bucketlist::iterator x = buckets.begin();
  while (x!=buckets.end() && (*x)->startdate!=d) ++x;

  // Pick up the action attribute and update the bucket accordingly
  Calendar::Bucket* result = *x;
  switch (MetaData::decodeAction(atts))
  {
    case ADD:
      // Only additions are allowed
      if (x==buckets.begin())
      {
        // The first bucket (starting at minus infinite) is automatically
        // created in a calendar. In this special case, we can allow an add
        // action on a bucket that already exists.
        LockManager::getManager().obtainWriteLock(*x);
        return *x;
      }
      if (x!=buckets.end()) 
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
      if (x==buckets.end())
        throw DataException("Bucket " + string(d)
          + " doesn't exist in calendar '" + getName() + "'");
      LockManager::getManager().obtainWriteLock(*x);
      return *x;
    case REMOVE:
      // Delete the entity
      if (x==buckets.end())
        throw DataException("Bucket " + string(d)
          + " doesn't exist in calendar '" + getName() + "'");
      else
      {
        // Send out the notification to subscribers
        LockManager::getManager().obtainWriteLock(*x);
        if (!(*x)->getType().raiseEvent(*x, SIG_REMOVE))
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
      if (x!=buckets.end())
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
