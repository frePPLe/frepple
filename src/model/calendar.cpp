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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Calendar> DECLARE_EXPORT Tree utils::HasName<Calendar>::st;

// Specialised template functions
template <> DECLARE_EXPORT bool CalendarValue<string>::getBool() const
  { return defaultValue.empty(); }
template <> DECLARE_EXPORT bool CalendarValue<string>::BucketValue::getBool() const
  { return val.empty(); }


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


DECLARE_EXPORT CalendarDouble::~CalendarDouble()
{
  // Remove all references from buffers
  for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
  {
    if (b->getMinimum()==this) b->setMinimum(NULL);
    if (b->getMaximum()==this) b->setMaximum(NULL);
  }

  // Remove all references from resources
  for (Resource::iterator r = Resource::begin(); r != Resource::end(); ++r)
    if (r->getMaximum()==this) r->setMaximum(NULL);
}


DECLARE_EXPORT CalendarBool::~CalendarBool()
{
  // Remove all references from locations
  for (Location::iterator l = Location::begin(); l != Location::end(); ++l)
  {
    if (l->getAvailable() == this) 
      l->setAvailable(NULL);
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


DECLARE_EXPORT Calendar::Bucket* Calendar::findBucket(Date d, bool fwd) const
{
  Calendar::Bucket *curBucket = NULL;
  double curPriority = DBL_MAX;
  for (Bucket *b = firstBucket; b; b = b->nextBucket)
  {
    if (b->getStart() > d) 
      // Buckets are sorted by the start date. Other entries definately 
      // won't be effective.
      break;
    else if (curPriority > b->getPriority() && b->checkValid(d)
      && ( (fwd && d >= b->getStart() && d < b->getEnd()) ||
           (!fwd && d > b->getStart() && d <= b->getEnd())
      ))
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


DECLARE_EXPORT void Calendar::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
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


DECLARE_EXPORT Calendar::Bucket* Calendar::createBucket(const AttributeList& atts)
{
  // Pick up the start, end and name attributes
  Date startdate = atts.get(Tags::tag_start)->getDate();
  const DataElement* d = atts.get(Tags::tag_end);
  Date enddate = *d ? d->getDate() : Date::infiniteFuture;
  string name = atts.get(Tags::tag_name)->getString();

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


DECLARE_EXPORT void Calendar::beginElement (XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_bucket)
      && pIn.getParentElement().first.isA(Tags::tag_buckets))
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
(XMLOutput *o, const Keyword& tag, mode m) const
{
  assert(m == DEFAULT || m == FULL);
  writeHeader(o);
  if (priority) o->writeElement(Tags::tag_priority, priority);
  o->EndObject(tag);
}


DECLARE_EXPORT void Calendar::Bucket::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_priority))
    pElement >> priority;
}


DECLARE_EXPORT Calendar::EventIterator& Calendar::EventIterator::operator++()
{
  // Go over all entries and ask them to update the iterator
  Date d = curDate;
  curDate = Date::infiniteFuture;  // Cause end date is not included
  curBucket = NULL;
  curPriority = DBL_MAX;
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
  curPriority = DBL_MAX;
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

  if (refDate > enddate && enddate >= iter->curDate)
  {
    // Previous event is the end date of the bucket
    iter->curDate = enddate;
    iter->curBucket = this;
    iter->curPriority = priority;
    return;
  }

  if (refDate > startdate && startdate > iter->curDate)
  {
    // Previous event is the start date of the bucket
    iter->curDate = startdate;   
    iter->curBucket = iter->theCalendar->findBucket(startdate,false);
    iter->curPriority = priority;
    return;
  }

}


DECLARE_EXPORT PyObject* PythonCalendar::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  if (attr.isA(Tags::tag_buckets))
    return new PythonCalendarBucketIterator(obj);
	return NULL;
}


DECLARE_EXPORT int PythonCalendar::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    obj->setName(field.getString());
  else
    return -1;  // Error
  return 0;  // OK
}


DECLARE_EXPORT PyObject* PythonCalendarVoid::getattro(const Attribute& attr)
{
  return PythonCalendar(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonCalendarVoid::setattro(const Attribute& attr, const PythonObject& field)
{
   return PythonCalendar(obj).setattro(attr, field);
}


DECLARE_EXPORT PyObject* PythonCalendarVoid::setValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarVoid *cal = static_cast<PythonCalendarVoid*>(self)->obj;
    if (!cal) throw LogicException("Can't set value of a NULL calendar");
  
    // Parse the arguments
    PyObject *pystart, *pyend, *pyval = NULL;
	  if (!PyArg_ParseTuple(args, "OO|O", &pystart, &pyend, &pyval))
      return NULL;

    // Update the calendar
    PythonObject start(pystart), end(pyend);
    cal->addBucket(start.getDate(), end.getDate(), "");
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* PythonCalendarBool::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_default))
    return PythonObject(obj->getDefault());
  return PythonCalendar(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonCalendarBool::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_default))
    obj->setDefault(field.getBool());
  else
    return PythonCalendar(obj).setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* PythonCalendarBool::setValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarBool *cal = static_cast<PythonCalendarBool*>(self)->obj;
    if (!cal) throw LogicException("Can't set value of a NULL calendar");
  
    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
	  if (!PyArg_ParseTuple(args, "OOO", &pystart, &pyend, &pyval))
      return NULL;

    // Update the calendar
    PythonObject start(pystart), end(pyend), val(pyval);
    cal->setValue(start.getDate(), end.getDate(), val.getBool());
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* PythonCalendarDouble::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_default))
    return PythonObject(obj->getDefault());
  return PythonCalendar(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonCalendarDouble::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_default))
    obj->setDefault(field.getDouble());
  else
    return PythonCalendar(obj).setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* PythonCalendarDouble::setValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarDouble *cal = static_cast<PythonCalendarDouble*>(self)->obj;
    if (!cal) throw LogicException("Can't set value of a NULL calendar");
  
    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
	  if (!PyArg_ParseTuple(args, "OOO", &pystart, &pyend, &pyval))
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


DECLARE_EXPORT PyObject* PythonCalendarString::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_default))
    return PythonObject(obj->getDefault());
  return PythonCalendar(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonCalendarString::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_default))
    obj->setDefault(field.getString());
  else
    return PythonCalendar(obj).setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* PythonCalendarString::setValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarString *cal = static_cast<PythonCalendarString*>(self)->obj;
    if (!cal) throw LogicException("Can't set value of a NULL calendar");
  
    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
	  if (!PyArg_ParseTuple(args, "OOO", &pystart, &pyend, &pyval))
      return NULL;

    // Update the calendar
    PythonObject start(pystart), end(pyend), val(pyval);
    cal->setValue(start.getDate(), end.getDate(), val.getString());
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* PythonCalendarInt::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_default))
    return PythonObject(obj->getDefault());
  return PythonCalendar(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonCalendarInt::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_default))
    obj->setDefault(field.getInt());
  else
    return PythonCalendar(obj).setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* PythonCalendarInt::setValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarInt *cal = static_cast<PythonCalendarInt*>(self)->obj;
    if (!cal) throw LogicException("Can't set value of a NULL calendar");
  
    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
	  if (!PyArg_ParseTuple(args, "OOO", &pystart, &pyend, &pyval))
      return NULL;

    // Update the calendar
    PythonObject start(pystart), end(pyend), val(pyval);
    cal->setValue(start.getDate(), end.getDate(), val.getInt());
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* PythonCalendarOperation::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_default))
    return PythonObject(obj->getDefault());
  return PythonCalendar(obj).getattro(attr); 
}


DECLARE_EXPORT int PythonCalendarOperation::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_default))
  {
    if (!field.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "calendar_operation stores values of type operation");
      return -1;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(field))->obj;
    obj->setDefault(y);
  }
  else
    return PythonCalendar(obj).setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* PythonCalendarOperation::setValue(PyObject* self, PyObject* args, PyObject* kwdict)
{
  try
  {
    // Pick up the calendar
    CalendarOperation *cal = static_cast<PythonCalendarOperation*>(self)->obj;
    if (!cal) throw LogicException("Can't set value of a NULL calendar");
  
    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
	  if (!PyArg_ParseTuple(args, "OOO", &pystart, &pyend, &pyval))
      return NULL;

    // Update the calendar
    PythonObject start(pystart), end(pyend), val(pyval);
    if (!val.check(PythonOperation::getType())) 
    {
      PyErr_SetString(PythonDataException, "calendar_operation stores values of type operation");
      return NULL;
    }
    Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(val))->obj;
    cal->setValue(start.getDate(), end.getDate(), y);
  }
  catch(...)
  {
    PythonType::evalException();
    return NULL;
  }
  return Py_BuildValue("");
}


int PythonCalendarBucketIterator::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonCalendarBucketIterator>::getType();
  x.setName("calendarBucketIterator");
  x.setDoc("frePPLe iterator for calendar buckets");
  x.supportiter();
  return x.typeReady(m);
}


PyObject* PythonCalendarBucketIterator::iternext()
{  
  if (i == cal->endBuckets()) return NULL;
  return new PythonCalendarBucket(cal, &*(i++));
}


int PythonCalendarBucket::initialize(PyObject* m)
{
  // Initialize the type
  PythonType& x = PythonExtension<PythonCalendarBucket>::getType();
  x.setName("calendarBucket");
  x.setDoc("frePPLe calendar bucket");
  x.supportgetattro();
  x.supportsetattro();
  return x.typeReady(m);
}


DECLARE_EXPORT PyObject* PythonCalendarBucket::getattro(const Attribute& attr)
{
  if (!obj) return Py_BuildValue("");
  if (attr.isA(Tags::tag_start))
    return PythonObject(obj->getStart());
  if (attr.isA(Tags::tag_end))
    return PythonObject(obj->getEnd());
  if (attr.isA(Tags::tag_value))
  {
    if (cal->getType() == *CalendarDouble::metadata)
      return PythonObject(dynamic_cast< CalendarValue<double>::BucketValue* >(obj)->getValue());
    if (cal->getType() == *CalendarBool::metadata)
      return PythonObject(dynamic_cast< CalendarValue<bool>::BucketValue* >(obj)->getValue());
    if (cal->getType() == *CalendarInt::metadata)
      return PythonObject(dynamic_cast< CalendarValue<int>::BucketValue* >(obj)->getValue());
    if (cal->getType() == *CalendarString::metadata)
      return PythonObject(dynamic_cast< CalendarValue<string>::BucketValue* >(obj)->getValue());
    if (cal->getType() == *CalendarOperation::metadata)
      return PythonObject(dynamic_cast< CalendarPointer<Operation>::BucketPointer* >(obj)->getValue());
    if (cal->getType() == *CalendarVoid::metadata) 
      return Py_BuildValue("");
    PyErr_SetString(PythonLogicException, "calendar type not recognized");
    return NULL;
  }
  if (attr.isA(Tags::tag_priority))
    return PythonObject(obj->getPriority());
  if (attr.isA(Tags::tag_name))
    return PythonObject(obj->getName());
  return NULL; 
}


DECLARE_EXPORT int PythonCalendarBucket::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_name))
    obj->setName(field.getString());
  else if (attr.isA(Tags::tag_start))
    obj->setStart(field.getDate());
  else if (attr.isA(Tags::tag_end))
    obj->setEnd(field.getDate());
  else if (attr.isA(Tags::tag_priority))
    obj->setPriority(field.getInt());
  else if (attr.isA(Tags::tag_value))
  {
    if (cal->getType() == *CalendarDouble::metadata)
      dynamic_cast< CalendarValue<double>::BucketValue* >(obj)->setValue(field.getDouble());
    else if (cal->getType() == *CalendarBool::metadata)
      dynamic_cast< CalendarValue<bool>::BucketValue* >(obj)->setValue(field.getBool());
    else if (cal->getType() == *CalendarInt::metadata)
      dynamic_cast< CalendarValue<int>::BucketValue* >(obj)->setValue(field.getInt());
    else if (cal->getType() == *CalendarString::metadata)
      dynamic_cast< CalendarValue<string>::BucketValue* >(obj)->setValue(field.getString());
    else if (cal->getType() == *CalendarOperation::metadata)
    {
      if (!field.check(PythonOperation::getType())) 
      {
        PyErr_SetString(PythonDataException, "calendar_operation stores values of type operation");
        return -1;
      }
      Operation* y = static_cast<PythonOperation*>(static_cast<PyObject*>(field))->obj;
      dynamic_cast< CalendarPointer<Operation>::BucketPointer* >(obj)->setValue(y);
    }
    else if (cal->getType() == *CalendarVoid::metadata) 
      return -1;
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


} // end namespace
