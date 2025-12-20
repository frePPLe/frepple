/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#include "frepple/model.h"

namespace frepple {

template <class Calendar>
Tree utils::HasName<Calendar>::st;
const MetaCategory* Calendar::metadata;
const MetaCategory* Calendar::metadata_alias;
const MetaClass* CalendarDefault::metadata;
const MetaCategory* CalendarBucket::metacategory;
const MetaClass* CalendarBucket::metadata;
map<string, CalendarBucket*> CalendarBucket::names;

int Calendar::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Calendar>("calendar", "calendars",
                                                      reader, finder);
  registerFields<Calendar>(const_cast<MetaCategory*>(metadata));

  // An alias for the calendar
  metadata_alias = MetaCategory::registerCategory<Calendar>(
      "calendar_reorderpoints", "calendars_reorderpoints", reader, finder);
  registerFields<Calendar>(const_cast<MetaCategory*>(metadata_alias));

  // Initialize the Python class
  auto& x = FreppleCategory<Calendar>::getPythonType();
  x.addMethod("setValue", setPythonValue, METH_VARARGS | METH_KEYWORDS,
              "update the value in a date range");
  x.addMethod("events", getEvents, METH_VARARGS, "return an event iterator");
  int ok = FreppleCategory<Calendar>::initialize();
  ok += CalendarEventIterator::initialize();
  return ok;
}

int CalendarBucket::initialize() {
  // Initialize the metadata
  metacategory = MetaCategory::registerCategory<CalendarBucket>(
      "bucket", "buckets", reader);
  registerFields<CalendarBucket>(const_cast<MetaCategory*>(metacategory));
  metadata = MetaClass::registerClass<CalendarBucket>(
      "bucket", "bucket", Object::create<CalendarBucket>, true);

  // Initialize the Python class
  auto& x = FreppleCategory<CalendarBucket>::getPythonType();
  x.setName(metadata->type);
  x.setDoc("frePPLe " + metadata->type);
  x.supportgetattro();
  x.supportsetattro();
  x.supportstr();
  x.supportcompare();
  x.supportcreate(Object::create<CalendarBucket>);
  x.addMethod("toXML", toXML, METH_VARARGS, "return a XML representation");
  metadata->setPythonClass(x);
  return x.typeReady();
}

int CalendarDefault::initialize() {
  // Initialize the metadata
  metadata = MetaClass::registerClass<CalendarDefault>(
      "calendar", "calendar_default", Object::create<CalendarDefault>, true);

  const_cast<MetaCategory*>(Calendar::metadata_alias)
      ->setDefaultClass(CalendarDefault::metadata);

  // Initialize the Python class
  return FreppleClass<CalendarDefault, Calendar>::initialize();
}

/* Updates the value in a certain date range.
 * This will create a new bucket if required. */
void Calendar::setValue(Date start, Date end, const double v) {
  auto* x = static_cast<CalendarBucket*>(findBucket(start));
  if (x && x->getStart() == start && x->getEnd() <= end)
    // We can update an existing bucket: it has the same start date
    // and ends before the new effective period ends.
    x->setEnd(end);
  else {
    // Creating a new bucket
    x = new CalendarBucket();
    x->setStart(start);
    x->setEnd(end);
    x->setCalendar(this);
  }
  x->setValue(v);
  x->setPriority(lowestPriority() - 1);
}

Calendar::~Calendar() {
  // De-allocate all the dynamic memory used for the bucket objects
  while (firstBucket) {
    CalendarBucket* tmp = firstBucket;
    firstBucket = firstBucket->nextBucket;
    delete tmp;
  }

  // Remove all references from locations
  for (auto& l : Location::all()) {
    if (l.getAvailable() == this) l.setAvailable(nullptr);
  }

  // Remove reference from buffers
  for (auto& b : Buffer::all()) {
    if (b.getMaximumCalendar() == this) b.setMaximumCalendar(nullptr);
    if (b.getMinimumCalendar() == this) b.setMinimumCalendar(nullptr);
  }

  // Remove references from resources
  for (auto& r : Resource::all()) {
    if (r.getMaximumCalendar() == this) r.setMaximumCalendar(nullptr);
    if (r.getEfficiencyCalendar() == this) r.setEfficiencyCalendar(nullptr);
    if (r.getAvailable() == this) r.setAvailable(nullptr);
  }

  // Remove references from operations
  for (auto& o : Operation::all()) {
    if (o.getAvailable() == this) o.setAvailable(nullptr);
    if (o.getSizeMinimumCalendar() == this) o.setSizeMinimumCalendar(nullptr);
  }
}

void Calendar::removeBucket(CalendarBucket* bkt, bool del) {
  // Verify the bucket is on this calendar indeed
  CalendarBucket* b = firstBucket;
  while (b && b != bkt) b = b->nextBucket;

  // Error
  if (!b)
    throw DataException("Trying to remove unavailable bucket from calendar '" +
                        getName() + "'");

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
  if (del) delete bkt;
}

CalendarBucket::~CalendarBucket() {
  if (!cal) return;

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

void CalendarBucket::setEnd(const Date d) {
  if (d < startdate)
    logger << "Warning: Calendar bucket end must be later than its start\n";
  else
    enddate = d;
}

void CalendarBucket::setStart(const Date d) {
  if (d > enddate)
    logger << "Warning: Calendar bucket start must be earlier than its end\n";
  else {
    startdate = d;
    updateSort();
  }
}

void CalendarBucket::updateSort() {
  // Update the position in the list
  if (!cal) return;
  bool ok = true;
  do {
    ok = true;
    if (nextBucket && (nextBucket->startdate < startdate ||
                       (nextBucket->startdate == startdate &&
                        nextBucket->priority < priority))) {
      // Move a position later in the list
      if (nextBucket->nextBucket) nextBucket->nextBucket->prevBucket = this;
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
    } else if (prevBucket && (prevBucket->startdate > startdate ||
                              (prevBucket->startdate == startdate &&
                               prevBucket->priority > priority))) {
      // Move a position earlier in the list
      if (prevBucket->prevBucket) prevBucket->prevBucket->nextBucket = this;
      if (nextBucket) nextBucket->prevBucket = prevBucket;
      prevBucket->nextBucket = nextBucket;
      nextBucket = prevBucket;
      CalendarBucket* tmp = prevBucket->prevBucket;
      prevBucket->prevBucket = this;
      prevBucket = tmp;
      ok = false;
    }
  } while (!ok);  // Repeat till in place
}

double Calendar::getValue(const Date d, bool forward) const {
  if (eventlist.empty()) {
    CalendarBucket* x = findBucket(d, forward);
    return x ? x->getValue() : defaultValue;
  } else {
    auto event = forward ? eventlist.upper_bound(d) : eventlist.lower_bound(d);
    if (event != eventlist.begin()) {
      --event;
      if (event != eventlist.end())
        return event->second;
      else
        return getDefault();
      return event->second;
    } else if (eventlist.empty())
      return getDefault();
    else
      return eventlist.rbegin()->second;
  }
}

CalendarBucket* Calendar::findBucket(Date d, bool fwd) const {
  CalendarBucket* curBucket = nullptr;
  double curPriority = DBL_MAX;
  int date_weekday = -1;
  Duration date_time;
  for (auto b = firstBucket; b; b = b->nextBucket) {
    if (b->getStart() == b->getEnd())
      continue;
    else if (b->getStart() > d)
      // Buckets are sorted by the start date. Other entries definitely
      // won't be effective.
      break;
    else if (curPriority > b->getPriority() &&
             ((fwd && d >= b->getStart() && d < b->getEnd()) ||
              (fwd && d == Date::infiniteFuture &&
               b->getEnd() == Date::infiniteFuture) ||
              (!fwd && d > b->getStart() && d <= b->getEnd()))) {
      if (b->isContinuouslyEffective()) {
        // Continuously effective
        curPriority = b->getPriority();
        curBucket = &*b;
      } else {
        // There are ineffective periods during the week
        if (date_weekday < 0) {
          // Lazily get the details on the date, if not done already
          struct tm datedetail;
          d.getInfo(&datedetail);
          date_weekday = datedetail.tm_wday;  // 0: sunday, 6: saturday
          date_time = long(datedetail.tm_sec + datedetail.tm_min * 60 +
                           datedetail.tm_hour * 3600);
          if (!date_time && !fwd) {
            date_time = Duration(86400L);
            if (--date_weekday < 0) date_weekday = 6;
          }
        }
        if (b->days & (1 << date_weekday)) {
          // Effective on the requested date
          if ((fwd && date_time >= b->starttime && date_time < b->endtime) ||
              (!fwd && date_time > b->starttime && date_time <= b->endtime)) {
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

CalendarBucket* Calendar::addBucket(Date st, Date nd, double val) {
  auto* bckt = new CalendarBucket();
  bckt->setCalendar(this);
  bckt->setStart(st);
  bckt->setEnd(nd);
  bckt->setValue(val);
  return bckt;
}

Object* CalendarBucket::reader(const MetaClass* cat, const DataValueDict& atts,
                               CommandManager* mgr) {
  // Pick up the calendar
  const DataValue* cal_val = atts.get(Tags::calendar);
  Calendar* cal =
      cal_val ? static_cast<Calendar*>(cal_val->getObject()) : nullptr;

  // Pick up the start date.
  const DataValue* strtElement = atts.get(Tags::start);
  Date strt;
  if (strtElement) strt = strtElement->getDate();

  // Pick up the end date.
  const DataValue* endElement = atts.get(Tags::end);
  Date nd = Date::infiniteFuture;
  if (endElement) nd = endElement->getDate();

  // Pick up  the priority
  const DataValue* prioElement = atts.get(Tags::priority);
  int prio = 0;
  if (prioElement) prio = prioElement->getInt();

  // Check for existence of a bucket with the same start, end and priority
  CalendarBucket* result = nullptr;
  if (cal) {
    for (auto i = cal->getBuckets(); i != CalendarBucket::iterator::end(); ++i)
      if (i->getStart() == strt && i->getEnd() == nd &&
          i->getPriority() == prio) {
        result = &*i;
        break;
      }
  }

  // Pick up the action attribute and update the bucket accordingly
  switch (MetaClass::decodeAction(atts)) {
    case Action::ADD:
      // Only additions are allowed
      if (result) {
        ostringstream o;
        o << "Bucket already exists in calendar '" << cal << "'";
        throw DataException(o.str());
      }
      result = new CalendarBucket();
      result->setStart(strt);
      result->setEnd(nd);
      result->setPriority(prio);
      if (cal) result->setCalendar(cal);
      if (mgr) mgr->add(new CommandCreateObject(result));
      return result;
    case Action::CHANGE:
      // Only changes are allowed
      if (!result) throw DataException("Bucket doesn't exist");
      return result;
    case Action::REMOVE:
      // Delete the entity
      if (!result)
        throw DataException("Bucket doesn't exist");
      else {
        // Delete it
        cal->removeBucket(result);
        return nullptr;
      }
    case Action::ADD_CHANGE:
      if (!result) {
        // Adding a new bucket
        result = new CalendarBucket();
        result->setStart(strt);
        result->setEnd(nd);
        result->setPriority(prio);
        if (cal) result->setCalendar(cal);
        if (mgr) mgr->add(new CommandCreateObject(result));
      }
      return result;
  }

  // This part of the code isn't expected not be reached
  throw LogicException("Unreachable code reached");
}

void CalendarBucket::setCalendar(Calendar* c) {
  if (cal == c) return;

  // Unlink from the previous calendar
  if (cal) {
    cal->eventlist.clear();
    cal->removeBucket(this, false);
  }
  cal = c;

  // Link in the list of buckets of the new calendar
  if (cal) {
    if (cal->firstBucket) {
      cal->firstBucket->prevBucket = this;
      nextBucket = cal->firstBucket;
    }
    cal->firstBucket = this;
    updateSort();
    cal->eventlist.clear();
  }
}

Calendar::EventIterator::EventIterator(Calendar* c, Date d, bool forward)
    : theCalendar(c) {
  if (!theCalendar) return;

  if (theCalendar->eventlist.empty() ||
      d < theCalendar->eventlist.begin()->first ||
      d > theCalendar->eventlist.rbegin()->first)
    theCalendar->buildEventList(d);

  curDate = d;
  if (forward) {
    cacheiter = theCalendar->eventlist.lower_bound(d);
    if (cacheiter != theCalendar->eventlist.end() && cacheiter->first > d)
      --cacheiter;
    if (cacheiter == theCalendar->eventlist.end())
      curValue = theCalendar->getDefault();
    else
      curValue = cacheiter->second;
  } else {
    cacheiter = theCalendar->eventlist.lower_bound(d);
    if (cacheiter != theCalendar->eventlist.end() && cacheiter->first > d)
      --cacheiter;
    if (cacheiter == theCalendar->eventlist.end())
      curValue = theCalendar->getDefault();
    else
      curValue = cacheiter->second;
  }
  prevValue = curValue;
}

Calendar::EventIterator& Calendar::EventIterator::operator++() {
  if (theCalendar && cacheiter != theCalendar->eventlist.end()) {
    ++cacheiter;
    if (cacheiter == theCalendar->eventlist.end()) {
      // Extend the event list if possible
      auto lastDate = theCalendar->eventlist.rbegin()->first;
      if (!theCalendar->eventlist.empty() && lastDate != Date::infiniteFuture) {
        theCalendar->buildEventList(lastDate);
        cacheiter = theCalendar->eventlist.find(lastDate);
        ++cacheiter;
      }
    }
  }
  prevValue = curValue;
  if (!theCalendar || cacheiter == theCalendar->eventlist.end()) {
    curDate = Date::infiniteFuture;
    curValue = theCalendar ? theCalendar->getDefault() : 0.0;
  } else {
    curDate = cacheiter->first;
    curValue = cacheiter->second;
  }
  return *this;
}

Calendar::EventIterator& Calendar::EventIterator::operator--() {
  prevValue = curValue;
  if (!theCalendar || cacheiter == theCalendar->eventlist.end()) {
    curValue = theCalendar ? theCalendar->getDefault() : 0.0;
    curDate = Date::infinitePast;
  } else {
    curDate = cacheiter->first;
    --cacheiter;
    if (cacheiter == theCalendar->eventlist.end()) {
      auto firstDate = theCalendar->eventlist.begin()->first;
      if (!theCalendar->eventlist.empty() && firstDate != Date::infinitePast) {
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

void Calendar::buildEventList(Date includedate) {
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
  while (true) {
    if (first) {
      eventlist[Date::infinitePast] =
          curBucket ? curBucket->getValue() : getDefault();
      first = false;
    } else {
      eventlist[curDate] = curBucket ? curBucket->getValue() : getDefault();
      if (curDate > maxDate || curDate == Date::infiniteFuture) break;
    }

    // Go over all entries and ask them to update the iterator
    Date refDate = curDate;
    struct tm datedetail_refdate;
    refDate.getInfo(&datedetail_refdate);
    struct tm datedetail_startdata;
    struct tm* datedetail;
    curDate = Date::infiniteFuture;
    for (auto b = firstBucket; b; b = b->nextBucket) {
      if (b->getStart() == b->getEnd() || !b->getDays()) continue;
      // FIRST CASE: Bucket that is continuously effective
      if (b->isContinuouslyEffective()) {
        // Evaluate the start date of the bucket
        if (refDate < b->startdate && b->priority <= lastPriority &&
            (b->startdate < curDate ||
             (b->startdate == curDate && b->priority <= curPriority))) {
          curDate = b->startdate;
          curBucket = b;
          curPriority = b->priority;
          continue;
        }

        // Next evaluate the end date of the bucket
        if (refDate < b->enddate && b->enddate <= curDate && lastBucket == b) {
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
      if (refDate < b->startdate) {
        tmp = b->startdate;
        tmp.getInfo(&datedetail_startdata);
        datedetail = &datedetail_startdata;
      } else
        datedetail = &datedetail_refdate;
      DateDetail tmp_detail = tmp;
      int ref_weekday = datedetail->tm_wday;  // 0: sunday, 6: saturday
      Duration ref_time = long(datedetail->tm_sec + datedetail->tm_min * 60 +
                               datedetail->tm_hour * 3600);
      if (refDate < b->startdate && ref_time >= b->starttime &&
          ref_time < b->endtime && (b->days & (1 << ref_weekday)))
        effectiveAtStart = true;

      if (ref_time >= b->starttime && !effectiveAtStart &&
          ref_time < b->endtime && (b->days & (1 << ref_weekday))) {
        // Entry is currently effective.
        if (!b->starttime && b->endtime == Duration(86400L)) {
          // The next event is the start of the next ineffective day
          tmp_detail.setSecondsDay(0L);
          tmp = tmp_detail;
          while ((b->days & (1 << ref_weekday)) &&
                 tmp != Date::infiniteFuture) {
            if (++ref_weekday > 6) ref_weekday = 0;
            tmp_detail = tmp;
            tmp_detail.addDays(1);
            tmp = tmp_detail;
          }
        } else {
          // The next event is the end date on the current day
          tmp_detail.setSecondsDay(b->endtime);
          tmp = tmp_detail;
        }
        if (tmp > b->enddate) tmp = b->enddate;

        // Evaluate the result
        if (refDate < tmp && tmp <= curDate && lastBucket == b) {
          curDate = tmp;
          curBucket = findBucket(tmp);
          curPriority = curBucket ? curBucket->priority : INT_MAX;
        }
      } else {
        // Reference date is before the start time on an effective date
        // or it is after the end time of an effective date
        // or it is on an ineffective day.

        // The next event is the start date, either today or on the next
        // effective day.
        tmp_detail.setSecondsDay(b->starttime);
        tmp = tmp_detail;
        if (ref_time >= b->endtime && (b->days & (1 << ref_weekday))) {
          if (++ref_weekday > 6) ref_weekday = 0;
          tmp_detail.setSecondsDay(b->starttime);
          tmp_detail.addDays(1);
          tmp = tmp_detail;
        }
        while (!(b->days & (1 << ref_weekday)) && tmp != Date::infiniteFuture &&
               tmp <= b->enddate) {
          if (++ref_weekday > 6) ref_weekday = 0;
          tmp_detail = tmp;
          tmp_detail.addDays(1);
          tmp = tmp_detail;
        }
        if (tmp < b->startdate) tmp = b->startdate;
        if (tmp >= b->enddate) continue;

        // Evaluate the result
        if (refDate < tmp && b->priority <= lastPriority &&
            (tmp < curDate || (tmp == curDate && b->priority <= curPriority))) {
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

PyObject* Calendar::setPythonValue(PyObject* self, PyObject* args,
                                   PyObject* kwdict) {
  try {
    // Pick up the calendar
    auto* cal = static_cast<CalendarDefault*>(self);
    if (!cal) throw LogicException("Can't set value of a nullptr calendar");

    // Parse the arguments
    PyObject *pystart, *pyend, *pyval;
    if (!PyArg_ParseTuple(args, "OOO:setValue", &pystart, &pyend, &pyval))
      return nullptr;

    // Update the calendar
    PythonData start(pystart), end(pyend), val(pyval);
    cal->setValue(start.getDate(), end.getDate(), val.getDouble());
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
  return Py_BuildValue("");
}

PyObject* Calendar::getEvents(PyObject* self, PyObject* args) {
  try {
    // Pick up the calendar
    Calendar* cal = nullptr;
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
    Date startdate =
        pystart ? PythonData(pystart).getDate() : Date::infinitePast;
    bool forward = pydirection ? PythonData(pydirection).getBool() : true;

    // Return the iterator
    return new CalendarEventIterator(cal, startdate, forward);
  } catch (...) {
    PythonType::evalException();
    return nullptr;
  }
}

int CalendarEventIterator::initialize() {
  // Initialize the type
  auto& x = PythonExtension<CalendarEventIterator>::getPythonType();
  x.setName("calendarEventIterator");
  x.setDoc("frePPLe iterator for calendar events");
  x.supportiter();
  return x.typeReady();
}

PyObject* CalendarEventIterator::iternext() {
  if ((forward && eventiter.getDate() == Date::infiniteFuture) ||
      (!forward && eventiter.getDate() == Date::infinitePast))
    return nullptr;
  PyObject* result = Py_BuildValue(
      "(O,O)", static_cast<PyObject*>(PythonData(eventiter.getDate())),
      static_cast<PyObject*>(PythonData(eventiter.getValue())));
  if (forward)
    ++eventiter;
  else
    --eventiter;
  return result;
}

string CalendarBucket::getName() const {
  // We don't store the name field on the calendar bucket.
  // We just do an inefficient linear loop here (since you won't call this
  // method too often anyway).
  for (auto f : names)
    if (f.second == this) return f.first;
  return "";
}

}  // namespace frepple
