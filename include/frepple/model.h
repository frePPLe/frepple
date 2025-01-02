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
 ***************************************************************************/

#pragma once
#ifndef MODEL_H
#define MODEL_H

#include <regex>

#include "frepple/utils.h"
#include "frepple/xml.h"
using namespace frepple::utils;

namespace frepple {

class Flow;
class FlowStart;
class FlowEnd;
class FlowTransferBatch;
class FlowPlan;
class LoadPlan;
class Resource;
class ResourceInfinite;
class ResourceBuckets;
class Problem;
class Demand;
class DemandGroup;
class OperationPlan;
class Item;
class ItemSupplier;
class ItemDistribution;
template <class T>
class TimeLine;
class Operation;
class OperationPlanState;
class OperationFixedTime;
class OperationTimePer;
class OperationRouting;
class OperationAlternate;
class OperationSplit;
class OperationItemSupplier;
class OperationItemDistribution;
class SubOperation;
class Buffer;
class BufferInfinite;
class Plan;
class Plannable;
class Calendar;
class CalendarBucket;
class Load;
class LoadDefault;
class LoadBucketizedFromEnd;
class LoadBucketizedFromStart;
class LoadBucketizedPercentage;
class Location;
class Customer;
class HasProblems;
class Solvable;
class PeggingIterator;
class PeggingDemandIterator;
class Skill;
class ResourceSkill;
class Supplier;
class SetupMatrix;
class SetupMatrixRule;

/* This class is used for initialization. */
class LibraryModel {
 public:
  static void initialize();
};

/* This class represents a time bucket as a part of a calendar.
 *
 * Manipulation of instances of this class need to be handled with the
 * methods on the friend class Calendar.
 * @see Calendar
 */
class CalendarBucket : public Object, public NonCopyable, public HasSource {
  friend class Calendar;

 private:
  /* Start date of the bucket. */
  Date startdate;

  /* End Date of the bucket. */
  Date enddate = Date::infiniteFuture;

  /* A pointer to the next bucket. */
  CalendarBucket* nextBucket = nullptr;

  /* A pointer to the previous bucket. */
  CalendarBucket* prevBucket = nullptr;

  /* A pointer to the owning calendar. */
  Calendar* cal = nullptr;

  /* Value of this bucket.*/
  double val = 0.0;

  /* Starting time on the effective days. */
  Duration starttime;

  /* Ending time on the effective days. */
  Duration endtime = 86400L;

  /* Priority of this bucket, compared to other buckets effective
   * at a certain time.
   */
  int priority = 0;

  /* Weekdays on which the entry is effective.
   * - Bit 0: Sunday
   * - Bit 1: Monday
   * - Bit 2: Tuesday
   * - Bit 3: Wednesday
   * - Bit 4: Thursday
   * - Bit 5: Friday
   * - Bit 6: Saturday
   */
  short days = 127;

  /* Keep all calendar buckets sorted in ascending order of start date
   * and use the priority as a tie breaker.
   */
  void updateSort();

  static map<string, CalendarBucket*> names;

 public:
  /* Default constructor. */
  CalendarBucket() { initType(metadata); }

  /* Destructor. */
  ~CalendarBucket();

  /* This is a factory method that creates a new bucket in a calendar.
   * It uses the calendar and id fields to identify existing buckets.
   */
  static Object* reader(const MetaClass*, const DataValueDict&,
                        CommandManager* = nullptr);

  /* Update the calendar owning the bucket. */
  void setCalendar(Calendar*);

  /* Return the calendar to whom the bucket belongs. */
  Calendar* getCalendar() const { return cal; }

  /* Returns the value of this bucket. */
  double getValue() const { return val; }

  /* Updates the value of this bucket. */
  void setValue(double v) { val = v; }

  /* Returns the end date of the bucket. */
  Date getEnd() const { return enddate; }

  /* Updates the end date of the bucket. */
  void setEnd(const Date d);

  /* Returns the start date of the bucket. */
  Date getStart() const { return startdate; }

  /* Updates the start date of the bucket. */
  void setStart(const Date d);

  /* Returns the priority of this bucket, compared to other buckets
   * effective at a certain time.
   * Lower numbers indicate a higher priority level.
   * The default value is 0.
   */
  int getPriority() const { return priority; }

  /* Updates the priority of this bucket, compared to other buckets
   * effective at a certain time.
   * Lower numbers indicate a higher priority level.
   * The default value is 0.
   */
  void setPriority(int f) {
    priority = f;
    updateSort();
  }

  /* Get the days on which the entry is valid.
   * The value is a bit pattern with bit 0 representing sunday, bit 1
   * monday, ... and bit 6 representing saturday.
   * The default value is 127.
   */
  short getDays() const { return days; }

  /* Update the days on which the entry is valid. */
  void setDays(short p) {
    if (p < 0 || p > 127)
      logger << "Warning: Calendar bucket days must be between 0 and 127"
             << endl;
    else
      days = p;
  }

  /* Return the time of the day when the entry becomes valid.
   * The default value is 0 or midnight.
   */
  Duration getStartTime() const { return starttime; }

  /* Update the time of the day when the entry becomes valid. */
  void setStartTime(Duration t) {
    if (t > 86400L || t < 0L) {
      logger << "Warning: Calendar bucket start time must be between 0 and "
                "86400 seconds"
             << endl;
      return;
    }
    starttime = t;
    if (starttime > endtime) swap(starttime, endtime);
  }

  /* Return the time of the day when the entry becomes invalid.
   * The default value is 23h59m59s.
   */
  Duration getEndTime() const { return endtime; }

  /* Update the time of the day when the entry becomes invalid. */
  void setEndTime(Duration t) {
    if (t > 86400L || t < 0L) {
      logger << "Warning: Calendar bucket end time must be between 0 and 86400 "
                "seconds"
             << endl;
      return;
    }
    endtime = t;
    if (starttime > endtime) swap(starttime, endtime);
  }

  /* Convert the value of the bucket to a boolean value. */
  virtual bool getBool() const { return val != 0; }

  /* Returns true if the bucket is continuously effective between
   * its start and end date, in other words it is effective 24 hours
   * a day and 7 days per week.
   */
  bool isContinuouslyEffective() const {
    return days == 127 && !starttime && endtime == Duration(86400L);
  }

  string getName() const;

  void setName(const string& nm) {
    auto f = names.find(nm);
    if (f == names.end()) names[nm] = this;
  }

  static inline CalendarBucket* getByName(const string& nm) {
    auto f = names.find(nm);
    return f != names.end() ? f->second : nullptr;
  }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metacategory;
  static const MetaClass* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDateField<Cls>(Tags::start, &Cls::getStart, &Cls::setStart);
    m->addDateField<Cls>(Tags::end, &Cls::getEnd, &Cls::setEnd,
                         Date::infiniteFuture);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
    m->addShortField<Cls>(Tags::days, &Cls::getDays, &Cls::setDays, 127);
    m->addDurationField<Cls>(Tags::starttime, &Cls::getStartTime,
                             &Cls::setStartTime);
    m->addDurationField<Cls>(Tags::endtime, &Cls::getEndTime, &Cls::setEndTime,
                             86400L);
    m->addDoubleField<Cls>(Tags::value, &Cls::getValue, &Cls::setValue);
    m->addPointerField<Cls, Calendar>(Tags::calendar, &Cls::getCalendar,
                                      &Cls::setCalendar,
                                      DONT_SERIALIZE + PARENT);
    HasSource::registerFields<Cls>(m);
    m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "",
                           BASE + COMPUTED);
  }

 public:
  /* An iterator class to go through all buckets of the calendar. */
  class iterator {
   private:
    CalendarBucket* curBucket;

   public:
    iterator(CalendarBucket* b = nullptr) : curBucket(b) {}

    bool operator!=(const iterator& b) const {
      return b.curBucket != curBucket;
    }

    bool operator==(const iterator& b) const {
      return b.curBucket == curBucket;
    }

    iterator& operator++() {
      if (curBucket) curBucket = curBucket->nextBucket;
      return *this;
    }

    iterator operator++(int) {
      iterator tmp = *this;
      ++*this;
      return tmp;
    }

    CalendarBucket* next() {
      CalendarBucket* tmp = curBucket;
      if (curBucket) curBucket = curBucket->nextBucket;
      return tmp;
    }

    iterator& operator--() {
      if (curBucket) curBucket = curBucket->prevBucket;
      return *this;
    }

    iterator operator--(int) {
      iterator tmp = *this;
      --*this;
      return tmp;
    }

    CalendarBucket* operator->() const { return curBucket; }

    CalendarBucket& operator*() const { return *curBucket; }

    static iterator end() { return nullptr; }
  };
};

/* This is the class used to represent variables that are
 * varying over time.
 *
 * Some example usages for calendars:
 *  - A calendar defining the available capacity of a resource
 *    week by week.
 *  - The minimum inventory desired in a buffer week by week.
 *  - The working hours and holidays at a certain location.
 */
class Calendar : public HasName<Calendar>, public HasSource {
 public:
  class EventIterator;  // Forward declaration
  friend class EventIterator;
  friend class CalendarBucket;

  /* Default constructor. */
  explicit Calendar() {}

  /* Destructor, which cleans up the buckets too and all references to the
   * calendar from the core model.
   */
  ~Calendar();

  /* Returns the value on the specified date. */
  double getValue(const Date, bool forward = true) const;

  /* Updates the value in a certain date range.
   * This will create a new bucket if required.
   */
  void setValue(Date start, Date end, const double);

  double getValue(CalendarBucket::iterator& i) const {
    return reinterpret_cast<CalendarBucket&>(*i).getValue();
  }

  /* Returns the default calendar value when no entry is matching. */
  double getDefault() const { return defaultValue; }

  /* Convert the value of the calendar to a boolean value. */
  virtual bool getBool() const { return defaultValue != 0; }

  /* Update the default calendar value when no entry is matching. */
  virtual void setDefault(double v) { defaultValue = v; }

  /* Removes a bucket from the list.
   * The first argument is the bucket to remove, and the second argument
   * is a flag indicating whether to delete the bucket or not.
   */
  void removeBucket(CalendarBucket* bckt, bool del = true);

  /* Returns the bucket where a certain date belongs to.
   * A nullptr pointer is returned when no bucket is effective.
   */
  CalendarBucket* findBucket(Date d, bool fwd = true) const;

  /* Add a new bucket to the calendar. */
  CalendarBucket* addBucket(Date, Date, double);

  /* Return the memory size, including the event list. */
  virtual size_t getSize() const {
    auto tmp = Object::getSize();
    tmp += (sizeof(pair<Date, double>) + sizeof(void*) * 3) * eventlist.size();
    return tmp;
  }

  /* An iterator class to go through all dates where the calendar
   * value changes.*/
  class EventIterator {
   protected:
    map<Date, double>::const_iterator cacheiter;
    Calendar* theCalendar = nullptr;
    Date curDate;
    double curValue = 0.0;
    double prevValue = 0.0;

   public:
    Date getDate() const { return curDate; }

    double getValue() const { return curValue; }

    const Calendar* getCalendar() const { return theCalendar; }

    double getPrevValue() const { return prevValue; }

    EventIterator() {}

    EventIterator(Calendar* c, Date d = Date::infinitePast,
                  bool forward = true);

    EventIterator& operator++();

    EventIterator& operator--();

    EventIterator operator++(int) {
      EventIterator tmp = *this;
      ++*this;
      return tmp;
    }

    EventIterator operator--(int) {
      EventIterator tmp = *this;
      --*this;
      return tmp;
    }
  };

  /* Returns an iterator to go through the list of buckets. */
  CalendarBucket::iterator getBuckets() const {
    return CalendarBucket::iterator(firstBucket);
  }

  static PyObject* setPythonValue(PyObject*, PyObject*, PyObject*);

  static int initialize();

  static PyObject* getEvents(PyObject*, PyObject*);

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "",
                              MANDATORY);
    HasSource::registerFields<Cls>(m);
    m->addDoubleField<Cls>(Tags::deflt, &Cls::getDefault, &Cls::setDefault);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addIteratorField<Cls, CalendarBucket::iterator, CalendarBucket>(
        Tags::buckets, Tags::bucket, &Cls::getBuckets, BASE + WRITE_OBJECT);
  }

  /* Build a list of dates where the calendar value changes.
   * By default we build the list for 1 year before and after the
   * current date.
   * If a date is passed as argument, we build/update a list to include
   * that date.
   */
  void buildEventList(Date include = Date::infinitePast);

  /* Erase the event list (to save memory).
   * The list will be rebuild the next time an iterator is created.
   */
  void clearEventList() { eventlist.clear(); }

 protected:
  /* Find the lowest priority of any bucket. */
  int lowestPriority() const {
    int min = 0;
    for (auto i = getBuckets(); i != CalendarBucket::iterator::end(); ++i)
      if (i->getPriority() < min) min = i->getPriority();
    return min;
  }

 private:
  /* A pointer to the first bucket. The buckets are stored in a doubly
   * linked list. */
  CalendarBucket* firstBucket = nullptr;

  /* Value used when no bucket is effective at all. */
  double defaultValue = 0.0;

  /* A cached list of all events. */
  map<Date, double> eventlist;
};

/* A calendar storing double values in its buckets. */
class CalendarDefault : public Calendar {
 public:
  /* Default constructor. */
  explicit CalendarDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* A problem represents infeasibilities, alerts and warnings in
 * the plan.
 *
 * Problems are maintained internally by the system. They are thus only
 * exported, meaning that you can't directly import or create problems.
 * This class is the pure virtual base class for all problem types.
 * The usage of the problem objects is based on the following principles:
 *  - Problems objects are passive. They don't actively change the model
 *    state.
 *  - Objects of the HasProblems class actively create and destroy Problem
 *    objects.
 *  - Problem objects are managed in a 'lazy' way, meaning they only are
 *    getting created when the list of problems is requested by the user.
 *    During normal planning activities we merely mark the planning entities
 *    that have changed, so we can easily pick up which entities to recompute
 *    the problems for. In this way we can avoid the cpu and memory overhead
 *    of keeping the problem list up to date at all times, while still
 *    providing the user with the correct list of problems when required.
 *  - Given the above, problems are lightweight objects that consume
 *    limited memory.
 */
class Problem : public NonCopyable, public Object {
 public:
  class iterator;
  friend class iterator;
  class List;
  friend class List;

  /* Constructor.
   * Note that this method can't manipulate the problem container, since
   * the problem objects aren't fully constructed yet.
   * @see addProblem
   */
  explicit Problem(HasProblems* p = nullptr) : owner(p) { initType(metadata); }

  /* Initialize the class. */
  static int initialize();

  /* Destructor.
   * @see removeProblem
   */
  virtual ~Problem() {}

  /* Return the category of the problem. */
  const string& getName() const { return getType().type; }

  /* Returns the duration of this problem. */
  virtual const DateRange getDates() const = 0;

  /* Get the start date of the problem. */
  Date getStart() const { return getDates().getStart(); }

  /* Get the start date of the problem. */
  Date getEnd() const { return getDates().getEnd(); }

  /* Returns a text description of this problem. */
  virtual string getDescription() const = 0;

  /* Returns the object type having this problem. */
  virtual string getEntity() const = 0;

  /* Returns true if the plan remains feasible even if it contains this
   * problem, i.e. if the problems flags only a warning.
   * Returns false if a certain problem points at an infeasibility of the
   * plan.
   */
  virtual bool isFeasible() const = 0;

  /* Returns a double number reflecting the magnitude of the problem. This
   * allows us to focus on the significant problems and filter out the
   * small ones.
   */
  virtual double getWeight() const = 0;

  PyObject* str() const { return PythonData(getDescription()); }

  /* Returns an iterator to the very first problem. The iterator can be
   * incremented till it points past the very last problem. */
  static iterator begin();

  /* Return an iterator to the first problem of this entity. The iterator
   * can be incremented till it points past the last problem of this
   * plannable entity.
   * The boolean argument specifies whether the problems need to be
   * recomputed as part of this method.
   */
  static iterator begin(HasProblems*, bool = true);

  /* Return an iterator pointing beyond the last problem. */
  static const iterator end();

  /* Erases the list of all problems. This methods can be used reduce the
   * memory consumption at critical points. The list of problems will be
   * recreated when the problem detection is triggered again.
   */
  static void clearProblems();

  /* Erases the list of problems linked with a certain plannable object.
   * If the second parameter is set to true, the problems will be
   * recreated when the next problem detection round is triggered.
   */
  static void clearProblems(HasProblems& p, bool setchanged = true,
                            bool includeInvalidData = true);

  /* Returns a pointer to the object that owns this problem. */
  virtual Object* getOwner() const = 0;

  /* Return a reference to the metadata structure. */
  virtual const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaCategory* metadata;

  /* An internal convenience method to return the next linked problem. */
  Problem* getNextProblem() const { return nextProblem; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, nullptr, "",
                              MANDATORY + COMPUTED);
    m->addStringField<Cls>(Tags::description, &Cls::getDescription, nullptr, "",
                           MANDATORY + COMPUTED);
    m->addDateField<Cls>(Tags::start, &Cls::getStart, nullptr,
                         Date::infinitePast, MANDATORY);
    m->addDateField<Cls>(Tags::end, &Cls::getEnd, nullptr, Date::infiniteFuture,
                         MANDATORY);
    m->addDoubleField<Cls>(Tags::weight, &Cls::getWeight, nullptr, 0.0,
                           MANDATORY);
    m->addStringField<Cls>(Tags::entity, &Cls::getEntity, nullptr, "",
                           DONT_SERIALIZE);
    m->addPointerField<Cls, Object>(Tags::owner, &Cls::getOwner, nullptr,
                                    DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::feasible, &Cls::isFeasible, nullptr, BOOL_UNSET,
                         COMPUTED);
  }

 protected:
  /* Each Problem object references a HasProblem object as its owner. */
  HasProblems* owner = nullptr;

  /* Each Problem contains a pointer to the next pointer for the same
   * owner. This class implements thus an intrusive single linked list
   * of Problem objects. */
  Problem* nextProblem = nullptr;

  /* Adds a newly created problem to the problem container.
   * This method needs to be called in the constructor of a problem
   * subclass. It can't be called from the constructor of the base
   * Problem class, since the object isn't fully created yet and thus
   * misses the proper information used by the compare method.
   * @see removeProblem
   */
  void addProblem();

  /* Removes a problem from the problem container.
   * This method needs to be called from the destructor of a problem
   * subclass.
   * Due to the single linked list data structure, this methods'
   * performance is linear with the number of problems of an entity.
   * This is acceptable since we don't expect entities with a huge amount
   * of problems.
   * @see addproblem
   */
  void removeProblem();

  /* Comparison of 2 problems.
   * To garantuee that the problems are sorted in a consistent and stable
   * way, the following sorting criteria are used (in order of priority):
   * - Entity
   *   This sort is to be ensured by the client. This method can't
   *   compare problems of different entities!
   * - Type
   *   Each problem type has a hashcode used for sorting.
   * - Start date
   * The sorting is expected such that it can be used as a key, i.e. no
   * two problems of will ever evaluate to be identical.
   */
  bool operator<(const Problem& a) const;
};

/* Classes that keep track of problem conditions need to implement
 * this class.
 *
 * This class is closely related to the Problem class.
 * @see Problem
 */
class HasProblems {
  friend class Problem::iterator;
  friend class Problem;
  friend class Plannable;
  friend class OperationPlan;

 public:
  class EntityIterator;

  /* Returns an iterator pointing to the first HasProblem object. */
  static EntityIterator beginEntity();

  /* Returns an iterator pointing beyond the last HasProblem object. */
  static EntityIterator endEntity();

  /* Constructor. */
  HasProblems() {}

  /* Destructor. It needs to take care of making sure all problems objects
   * are being deleted as well. */
  virtual ~HasProblems() { Problem::clearProblems(*this, false); }

  /* Returns the plannable entity relating to this problem container. */
  virtual Plannable* getEntity() const {
    // This method is implemented in all subclasses.
    return nullptr;
  }

  /* Called to update the list of problems. The function will only be
   * called when:
   *  - the list of problems is being recomputed
   *  - AND, problem detection is enabled for this object
   *  - AND, the object has changed since the last problem computation
   */
  virtual void updateProblems() = 0;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addBoolField<Cls>(Tags::detectproblems, &Cls::getDetectProblems,
                         &Cls::setDetectProblems, BOOL_TRUE);
  }

  bool hasNoProblems() {
    updateProblems();
    return firstProblem == nullptr;
  }

 private:
  /* A pointer to the first problem of this object. Problems are maintained
   * in a single linked list. */
  Problem* firstProblem = nullptr;
};

/* This auxilary class is used to maintain a list of problem models. */
class Problem::List {
 public:
  /* Constructor. */
  List(){};

  /* Destructor. */
  ~List() { clear(); }

  /* Empty the list.
   * If a problem is passed as argument, that problem and all problems
   * following it in the list are deleted.
   * If no argument is passed, the complete list is erased.
   */
  void clear(Problem* = nullptr);

  /* Add a problem to the list. */
  Problem* push(const MetaClass*, const Object*, Date, Date, double);

  /* Add a problem to the list. */
  void push(Problem* p);

  /* Remove all problems from the list that appear AFTER the one
   * passed as argument. */
  void pop(Problem*);

  /* Get the last problem on the list. */
  Problem* top() const;

  /* Cur the list in two parts . */
  Problem* unlink(Problem* p) {
    Problem* tmp = p->nextProblem;
    p->nextProblem = nullptr;
    return tmp;
  }

  /* Returns true if the list is empty. */
  bool empty() const { return first == nullptr; }

  typedef Problem::iterator iterator;

  /* Return an iterator to the start of the list. */
  Problem::iterator begin() const;

  /* End iterator. */
  Problem::iterator end() const;

  /* Move the problems from this list to a new owner. */
  void transfer(HasProblems*);

 private:
  /* Pointer to the head of the list. */
  Problem* first = nullptr;
};

/* This class is an implementation of the "visitor" design pattern.
 * It is intended as a basis for different algorithms processing the frePPLe
 * data.
 *
 * The goal is to decouple the solver/algorithms from the model/data
 * representation. Different solvers can be easily be plugged in to work on
 * the same data.
 */
class Solver : public Object {
 public:
  /* Constructor. */
  explicit Solver() {}

  /* Destructor. */
  virtual ~Solver() {}

  static int initialize();

  static PyObject* solve(PyObject*, PyObject*);

  virtual void solve(void* = nullptr) = 0;

  virtual void solve(const Plan*, void* = nullptr) {
    throw LogicException("Called undefined solve(Plan*) method");
  }

  virtual void solve(const Demand*, void* = nullptr) {
    throw LogicException("Called undefined solve(Demand*) method");
  }

  virtual void solve(const DemandGroup* o, void* v = nullptr) {
    solve(reinterpret_cast<const Demand*>(o), v);
  }

  virtual void solve(const Operation*, void* = nullptr) {
    throw LogicException("Called undefined solve(Operation*) method");
  }

  virtual void solve(const OperationFixedTime* o, void* v = nullptr) {
    solve(reinterpret_cast<const Operation*>(o), v);
  }

  virtual void solve(const OperationTimePer* o, void* v = nullptr) {
    solve(reinterpret_cast<const Operation*>(o), v);
  }

  virtual void solve(const OperationRouting* o, void* v = nullptr) {
    solve(reinterpret_cast<const Operation*>(o), v);
  }

  virtual void solve(const OperationAlternate* o, void* v = nullptr) {
    solve(reinterpret_cast<const Operation*>(o), v);
  }

  virtual void solve(const OperationSplit* o, void* v = nullptr) {
    solve(reinterpret_cast<const Operation*>(o), v);
  }

  virtual void solve(const OperationItemSupplier* o, void* v = nullptr) {
    solve(reinterpret_cast<const Operation*>(o), v);
  }

  virtual void solve(const OperationItemDistribution* o, void* v = nullptr) {
    solve(reinterpret_cast<const Operation*>(o), v);
  }

  virtual void solve(const Resource*, void* = nullptr) {
    throw LogicException("Called undefined solve(Resource*) method");
  }

  virtual void solve(const ResourceInfinite* r, void* v = nullptr) {
    solve(reinterpret_cast<const Resource*>(r), v);
  }

  virtual void solve(const ResourceBuckets* r, void* v = nullptr) {
    solve(reinterpret_cast<const Resource*>(r), v);
  }

  virtual void solve(const Buffer*, void* = nullptr) {
    throw LogicException("Called undefined solve(Buffer*) method");
  }

  virtual void solve(const BufferInfinite* b, void* v = nullptr) {
    solve(reinterpret_cast<const Buffer*>(b), v);
  }

  virtual void solve(const Load* b, void* v = nullptr) {
    throw LogicException("Called undefined solve(Load*) method");
  }

  virtual void solve(const LoadDefault* b, void* v = nullptr) {
    solve(reinterpret_cast<const Load*>(b), v);
  }

  virtual void solve(const LoadBucketizedFromStart* b, void* v = nullptr) {
    solve(reinterpret_cast<const Load*>(b), v);
  }

  virtual void solve(const LoadBucketizedFromEnd* b, void* v = nullptr) {
    solve(reinterpret_cast<const Load*>(b), v);
  }

  virtual void solve(const LoadBucketizedPercentage* b, void* v = nullptr) {
    solve(reinterpret_cast<const Load*>(b), v);
  }

  virtual void solve(const Flow* b, void* v = nullptr) {
    throw LogicException("Called undefined solve(Flow*) method");
  }

  virtual void solve(const FlowStart* b, void* v = nullptr) {
    solve(reinterpret_cast<const Flow*>(b), v);
  }

  virtual void solve(const FlowEnd* b, void* v = nullptr) {
    solve(reinterpret_cast<const Flow*>(b), v);
  }

  virtual void solve(const FlowTransferBatch* b, void* v = nullptr) {
    solve(reinterpret_cast<const Flow*>(b), v);
  }

  virtual void solve(const Solvable*, void* = nullptr) {
    throw LogicException("Called undefined solve(Solvable*) method");
  }

  /* Returns how elaborate and verbose output is requested.
   * As a guideline solvers should respect the following guidelines:
   * - 0:
   *   Completely silent.
   *   This is the default value.
   * - 1:
   *   Minimal and high-level messages on the progress that are sufficient
   *   for logging normal operation.
   * - 2:
   *   Higher numbers are solver dependent. These levels are typically
   *   used for debugging and tracing, and provide more detail on the
   *   solver's progress.
   */
  short getLogLevel() const { return loglevel; }

  /* Controls whether verbose output will be generated. */
  virtual void setLogLevel(short v) { loglevel = v; }

  /* Return whether or not we automatically commit the changes. */
  bool getAutocommit() const { return autocommit; }

  /* Update whether or not we automatically commit the changes. */
  void setAutocommit(const bool b) { autocommit = b; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addShortField<Cls>(Tags::loglevel, &Cls::getLogLevel, &Cls::setLogLevel);
    m->addBoolField<Cls>(Tags::autocommit, &Cls::getAutocommit,
                         &Cls::setAutocommit);
  }

 private:
  /* Controls the amount of tracing and debugging messages. */
  short loglevel = 0;

  /* Automatically commit any plan changes or not. */
  bool autocommit = true;
};

/* This class needs to be implemented by all classes that implement
 * dynamic behavior, and which can be called by a solver.
 */
class Solvable {
 public:
  /* This method is called by solver classes. The implementation of this
   * class simply calls the solve method on the solver class. Using the
   * polymorphism the solver can implement seperate methods for different
   * plannable subclasses.
   */
  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  /* Destructor. */
  virtual ~Solvable() {}
};

/* This class needs to be implemented by all classes that implement
 * dynamic behavior in the plan.
 *
 * The problem detection logic is implemented in the detectProblems() method.
 * For performance reasons, problem detection is "lazy", i.e. problems are
 * computed only when somebody really needs the access to the list of
 * problems.
 */
class Plannable : public HasProblems, public Solvable {
 public:
  /* Constructor. */
  Plannable() : useProblemDetection(true), changed(true) { anyChange = true; }

  /* Specify whether this entity reports problems. */
  void setDetectProblems(bool b);

  /* Returns whether or not this object needs to detect problems. */
  bool getDetectProblems() const { return useProblemDetection; }

  /* Loops through all plannable objects and updates their problems if
   * required. */
  static void computeProblems();

  /* See if this entity has changed since the last problem
   * problem detection run. */
  bool getChanged() const { return changed; }

  /* Mark that this entity has been updated and that the problem
   * detection needs to be redone. */
  void setChanged(bool b = true) {
    changed = b;
    if (b) anyChange = true;
  }

  /* Implement the pure virtual function from the HasProblem class. */
  Plannable* getEntity() const { return const_cast<Plannable*>(this); }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addIteratorField<Cls, Problem::iterator, Problem>(
        Tags::problems, Tags::problem, &Cls::getProblems, DETAIL + PLAN);
    HasProblems::registerFields<Cls>(m);
  }

  /* Return an iterator over the list of problems. */
  Problem::iterator getProblems() const;

 private:
  /* Stores whether this entity should be skip problem detection, or not. */
  bool useProblemDetection;

  /* Stores whether this entity has been updated since the last problem
   * detection run. */
  bool changed;

  /* Marks whether any entity at all has changed its status since the last
   * problem detection round.
   */
  static bool anyChange;

  /* This flag is set to true during the problem recomputation. It is
   * required to garantuee safe access to the problems in a multi-threaded
   * environment.
   */
  static bool computationBusy;
};

/* The purpose of this class is to compute the levels of all buffers,
 * operations and resources in the model, and to categorize them in clusters.
 *
 * Resources and buffers linked to the delivery operations of
 * the demand are assigned level 1. buffers one level upstream have
 * level 2, and so on...
 *
 * A cluster is group of planning entities (buffers, resources and operations)
 * that are linked together using loads and/or flows. Each cluster can be seen
 * as a completely independent part of the model and the planning problem.
 * There is no interaction possible between clusters.
 * Cluster 0 is a special case: it contains all entities not connected to any
 * other entity at all. Clusters are helpful in multi-threading the planning
 * problem, partial replanning of the model, etc...
 */
class HasLevel {
 private:
  /* Flags whether the current computation is still up to date or not.
   * The flag is set when new objects of this are created or updated.
   * Running the computeLevels function clears the flag.
   */
  static bool recomputeLevels;

  /* This flag is set to true during the computation of the levels. It is
   * required to ensure safe access to the level information in a
   * multi-threaded environment.
   */
  static bool computationBusy;

  /* Stores the total number of clusters in the model. */
  static int numberOfClusters;

  /* Stores the maximum level number in the model. */
  static short numberOfLevels;

  /* Stores the level of this entity. Higher numbers indicate more
   * upstream entities.
   * A value of -1 indicates an unused entity.
   */
  short lvl;

  /* Stores the cluster number of the current entity. */
  int cluster;

 protected:
  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addShortField<Cls>(Tags::level, &Cls::getLevel, nullptr, 0,
                          DONT_SERIALIZE);
    m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0,
                        DONT_SERIALIZE);
  }

  /* Default constructor. The initial level is -1 and basically indicates
   * that this object (either Operation, Buffer or Resource) is not
   * being used at all...
   */
  HasLevel() : lvl(0), cluster(0) {}

  /* Copy constructor. Since the characterictics of the new object are the
   * same as the original, the level and cluster are also the same.
   * No recomputation is required.
   */
  HasLevel(const HasLevel& o) : lvl(o.lvl), cluster(o.cluster) {}

  /** Disallow assignment */
  HasLevel& operator=(const HasLevel& rhs) = delete;

  /* Destructor. Deleting a HasLevel object triggers recomputation of the
   * level and cluster computation, since the network now has changed.
   */
  ~HasLevel() { recomputeLevels = true; }

  /* This function recomputes all levels in the model.
   * It is called automatically when the getLevel or getCluster() function
   * on a Buffer, Resource or Operation are called while the
   * "recomputeLevels" flag is set.
   * Right, this is an example of a 'lazy' algorithm: only compute the
   * information when it is required. Note however that the computation
   * is triggered over the complete model, not a subset...
   * The runtime of the algorithm is pretty much linear with the total
   * number of operations in the model. The cluster size also has some
   * (limited) impact on the performance: a network with larger cluster
   * size will take longer to analyze.
   * @exception LogicException Generated when there are too many clusters in
   *     your model. The maximum limit is USHRT_MAX, i.e. the greatest
   *     number that can be stored in a variable of type "unsigned short".
   *     The limit is platform dependent. On 32-bit platforms it will
   *     typically be 65535.
   */
  static void computeLevels();

 public:
  /* Returns the total number of levels.
   * If not up to date the recomputation will be triggered.
   */
  static short getNumberOfLevels() {
    if (recomputeLevels || computationBusy) computeLevels();
    return numberOfLevels;
  }

  /* Returns the total number of clusters.
   * If not up to date the recomputation will be triggered.
   */
  static int getNumberOfClusters() {
    if (recomputeLevels || computationBusy) computeLevels();
    return numberOfClusters;
  }

  /* Return the level (and recompute first if required). */
  short getLevel() const {
    if (recomputeLevels || computationBusy) computeLevels();
    return lvl;
  }

  /* Return the cluster number (and recompute first if required). */
  int getCluster() const {
    if (recomputeLevels || computationBusy) computeLevels();
    return cluster;
  }

  /* Copies the cluser and level information from another buffer.
   * This method assumes that you know what you're doing!
   * There is no check or validation of the data and it doesn't
   * trigger the recalculation.
   */
  void copyLevelAndCluster(const HasLevel* p) {
    if (!p) return;
    cluster = p->cluster;
    lvl = p->lvl;
  }

  /* This function should be called when something is changed in the network
   * structure. The notification sets a flag, but does not immediately
   * trigger the recomputation.
   * @see computeLevels
   */
  static void triggerLazyRecomputation() { recomputeLevels = true; }
};

/* This abstract class is used to associate buffers and resources with
 * a physical or logical location.
 *
 * The 'available' calendar is used to model the working hours and holidays
 * of resources, buffers and operations.
 */
class Location : public HasHierarchy<Location>, public HasDescription {
  friend class ItemDistribution;

 public:
  typedef Association<Location, Item, ItemDistribution>::ListA distributionlist;

  /* Default constructor. */
  explicit Location() { initType(metadata); }

  /* Destructor. */
  virtual ~Location();

  /* Returns the availability calendar of the location.
   * The availability calendar models the working hours and holidays. It
   * applies to all operations, resources and buffers using this location.
   */
  Calendar* getAvailable() const { return available; }

  /* Updates the availability calendar of the location. */
  void setAvailable(Calendar* b) { available = b; }

  /* Returns a constant reference to the item distributions pointing to
   * this location as origin. */
  const distributionlist& getDistributions() const { return distributions; }

  /* Returns an iterator over the list of item distributions pointing to
   * this location as origin. */
  distributionlist::const_iterator getDistributionIterator() const {
    return distributions.begin();
  }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    HasHierarchy<Cls>::template registerFields<Cls>(m);
    HasDescription::registerFields<Cls>(m);
    m->addPointerField<Cls, Calendar>(Tags::available, &Cls::getAvailable,
                                      &Cls::setAvailable);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
  }

 private:
  /* The availability calendar models the working hours and holidays. It
   * applies to all operations, resources and buffers using this location.
   */
  Calendar* available = nullptr;

  /* This is a list of item distributions pointing to this location as
   * destination.
   */
  distributionlist distributions;
};

/* This class implements the abstract Location class. */
class LocationDefault : public Location {
 public:
  explicit LocationDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This abstracts class represents customers.
 *
 * Demands can be associated with a customer, but there is no planning
 * behavior directly linked to customers.
 */
class Customer : public HasHierarchy<Customer>, public HasDescription {
 public:
  /* Default constructor. */
  explicit Customer() {}

  /* Destructor. */
  virtual ~Customer();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    HasHierarchy<Cls>::template registerFields<Cls>(m);
    HasDescription::registerFields<Cls>(m);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
  }

  int getNumberOfDemands() const { return numDemands; }

  void incNumberOfDemands() { ++numDemands; }

  void decNumberOfDemands() { --numDemands; }

 private:
  int numDemands = 0;
};

/* This class implements the abstract Customer class. */
class CustomerDefault : public Customer {
 public:
  /* Default constructor. */
  explicit CustomerDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This abstracts class represents a supplier. */
class Supplier : public HasHierarchy<Supplier>, public HasDescription {
  friend class ItemSupplier;

 public:
  typedef Association<Supplier, Item, ItemSupplier>::ListA itemlist;

  /* Default constructor. */
  explicit Supplier() {}

  /* Destructor. */
  virtual ~Supplier();

  /* Returns a constant reference to the list of items this supplier can
   * deliver. */
  const itemlist& getItems() const { return items; }

  /* Returns an iterator over the list of items this supplier can deliver. */
  itemlist::const_iterator getItemIterator() const { return items.begin(); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    HasHierarchy<Cls>::template registerFields<Cls>(m);
    HasDescription::registerFields<Cls>(m);
    m->addIteratorField<Cls, itemlist::const_iterator, ItemSupplier>(
        Tags::itemsuppliers, Tags::itemsupplier, &Cls::getItemIterator, DETAIL);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
  }

 private:
  /* This is a list of items this supplier has. */
  itemlist items;
};

/* This class implements the abstract Supplier class. */
class SupplierDefault : public Supplier {
 public:
  explicit SupplierDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* A suboperation is used in operation types which have child
 * operations.
 */
class SubOperation : public Object, public HasSource {
 private:
  /* Pointer to the parent operation. */
  Operation* owner = nullptr;

  /* Pointer to the child operation.
   * Note that the same child operation can be used in multiple parents.
   * The child operation is completely unaware of its parents.
   */
  Operation* oper = nullptr;

  /* Validity date range for the child operation. */
  DateRange effective;

  /* Priority index. */
  int prio = 1;

  /* Python constructor. */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

 public:
  typedef list<SubOperation*> suboperationlist;

  /* Default constructor. */
  explicit SubOperation() { initType(metadata); }

  /* Destructor. */
  ~SubOperation();

  Operation* getOwner() const { return owner; }

  void setOwner(Operation*);

  Operation* getOperation() const { return oper; }

  void setOperation(Operation*);

  int getPriority() const { return prio; }

  void setPriority(int);

  DateRange getEffective() const { return effective; }

  Date getEffectiveStart() const { return effective.getStart(); }

  void setEffectiveStart(Date d) { effective.setStart(d); }

  Date getEffectiveEnd() const { return effective.getEnd(); }

  void setEffectiveEnd(Date d) { effective.setEnd(d); }

  void setEffective(DateRange d) { effective = d; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metacategory;
  static const MetaClass* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Operation>(Tags::owner, &Cls::getOwner,
                                       &Cls::setOwner, MANDATORY + PARENT);
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       &Cls::setOperation, MANDATORY);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority,
                        1);
    m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart,
                         &Cls::setEffectiveStart);
    m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd,
                         &Cls::setEffectiveEnd, Date::infiniteFuture);
    HasSource::registerFields<Cls>(m);
  }

  class iterator {
   private:
    suboperationlist::const_iterator cur;
    suboperationlist::const_iterator nd;

   public:
    /* Constructor. */
    iterator(suboperationlist& l) : cur(l.begin()), nd(l.end()) {}

    /* Return current value and advance the iterator. */
    SubOperation* next() {
      if (cur == nd) return nullptr;
      SubOperation* tmp = *cur;
      ++cur;
      return tmp;
    }
  };
};

class OperationDependency : public Object, public HasSource {
 private:
  Operation* oper = nullptr;

  Operation* blockedby = nullptr;

  double quantity = 1.0;

  Duration safety_leadtime;

  Duration hard_safety_leadtime;

  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  static bool checkLoops(const Operation*, vector<const Operation*>&);

 public:
  typedef forward_list<OperationDependency*> operationdependencylist;

  explicit OperationDependency() { initType(metadata); }

  ~OperationDependency();

  Operation* getOperation() const { return oper; }

  void setOperation(Operation*);

  Operation* getBlockedBy() const { return blockedby; }

  void setBlockedBy(Operation*);

  double getQuantity() const { return quantity; }

  void setQuantity(double q) {
    if (q < 0.0)
      logger << "Warning: Dependency quantity must be greater than 1" << endl;
    else
      quantity = q;
  }

  Duration getSafetyLeadtime() const { return safety_leadtime; }

  Duration getHardSafetyLeadtime() const { return hard_safety_leadtime; }

  void setSafetyLeadtime(Duration d) {
    if (d < Duration(0L))
      logger << "Warning: No negative safety lead time allowed" << endl;
    else
      safety_leadtime = d;
  }

  void setHardSafetyLeadtime(Duration d) {
    if (d < Duration(0L))
      logger << "Warning: No negative hard safety lead time allowed" << endl;
    else
      hard_safety_leadtime = d;
  }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metacategory;
  static const MetaClass* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       &Cls::setOperation, MANDATORY + PARENT);
    m->addPointerField<Cls, Operation>(Tags::blockedby, &Cls::getBlockedBy,
                                       &Cls::setBlockedBy, MANDATORY);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity,
                           1);
    m->addDurationField<Cls>(Tags::safety_leadtime, &Cls::getSafetyLeadtime,
                             &Cls::setSafetyLeadtime);
    m->addDurationField<Cls>(Tags::hard_safety_leadtime,
                             &Cls::getHardSafetyLeadtime,
                             &Cls::setHardSafetyLeadtime);
    HasSource::registerFields<Cls>(m);
  }
};

#include "frepple/timeline.h"

/* A timeline event representing a setup change.
 *
 * The following rule applies to the event:
 * - No change in setup
 *   => No setup event is created
 * - Change in setup
 *   => Event is created with pointer to the new rule
 * - Change in setup, but no applicable rule is available
 *   => event may or may not be created
 *   => If an event is created it points to a dummy not-allowed rule
 */
class SetupEvent : public TimeLine<LoadPlan>::Event {
  friend class TimeLine<LoadPlan>::Event;
  friend class OperationPlanState;

 private:
  PooledString setup;
  TimeLine<LoadPlan>* tmline = nullptr;
  SetupMatrixRule* rule = nullptr;
  OperationPlan* opplan = nullptr;
  Duration setup_override = -1L;
  bool stateinfo = false;

 public:
  virtual TimeLine<LoadPlan>* getTimeLine() const { return tmline; }

  /* Default constructor. */
  SetupEvent() : TimeLine<LoadPlan>::Event(5) { initType(metadata); }

  /* Copy constructor. */
  SetupEvent(const SetupEvent& x)
      : TimeLine<LoadPlan>::Event(5), setup(x.setup), rule(x.rule) {
    initType(metadata);
    dt = x.getDate();
  }

  /* Constructor. */
  SetupEvent(const SetupEvent* x) : TimeLine<LoadPlan>::Event(5) {
    initType(metadata);
    if (x) {
      setup = x->setup;
      rule = x->rule;
      dt = x->getDate();
      setup_override = x->setup_override;
    }
  }

  SetupEvent(OperationPlan* x);

  /* Destructor. */
  virtual ~SetupEvent();

  void erase();

  void reset() {
    setup = PooledString();
    if (stateinfo)
      tmline = nullptr;
    else
      setTimeLine(nullptr);
    rule = nullptr;
  }

  /* Assignment operator.
   * We don't relink the event in the timeline yet.
   * We don't copy the operationplan field either.
   */
  SetupEvent& operator=(const SetupEvent& other) {
    assert(!tmline);
    setup = other.setup;
    tmline = other.tmline;
    rule = other.rule;
    setup_override = other.setup_override;
    return *this;
  }

  /* Constructor. */
  SetupEvent(TimeLine<LoadPlan>* t, Date d, const PooledString& s,
             SetupMatrixRule* r = nullptr, OperationPlan* o = nullptr,
             bool state = false)
      : TimeLine<LoadPlan>::Event(5),
        setup(s),
        tmline(t),
        opplan(o),
        stateinfo(state) {
    initType(metadata);
    dt = d;
    rule = r;
    if (opplan && tmline && !stateinfo) tmline->insert(this);
  }

  void setTimeLine(TimeLine<LoadPlan>* t) {
    if (stateinfo)
      tmline = t;
    else if (tmline != t) {
      if (tmline) tmline->erase(this);
      tmline = t;
      if (tmline) tmline->insert(this);
    }
  }

  virtual OperationPlan* getOperationPlan() const { return opplan; }

  void setOperationPlan(OperationPlan* o) { opplan = o; }

  SetupMatrixRule* getRule() const { return rule; }

  const PooledString& getSetup() const { return setup; }

  const string& getSetupString() const { return setup; }

  void setSetup(const PooledString& s) { setup = s; }

  SetupEvent* getSetupBefore() const;

  Duration getSetupOverride() const { return setup_override; }

  void setSetupOverride(Duration d) {
    if (d >= 0L) rule = nullptr;
    setup_override = d;
  }

  void update(TimeLine<LoadPlan>*, Date, const PooledString&, SetupMatrixRule*);

  Date getLoadplanDate(const LoadPlan* lp) const;

  double getLoadplanQuantity(const LoadPlan* lp) const;

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::setup, &Cls::getSetupString);
    m->addPointerField<Cls, SetupMatrixRule>(Tags::rule, &Cls::getRule);
    m->addDateField<Cls>(Tags::date, &Cls::getDate);
    m->addDurationField<Cls>(Tags::setupoverride, &Cls::getSetupOverride,
                             &Cls::setSetupOverride, -1L);
  }
};

class OperationPlanDependency : public Object {
  friend class OperationDependency;
  friend class Operation;

 public:
  OperationPlanDependency(OperationPlan* first, OperationPlan* second,
                          OperationDependency* d = nullptr);

  ~OperationPlanDependency();

  OperationPlan* getFirst() const { return first; }

  OperationPlan* getSecond() const { return second; }

  OperationDependency* getOperationDependency() const { return dpdcy; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metacategory;
  static const MetaClass* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, OperationPlan>(Tags::first, &Cls::getFirst, nullptr,
                                           DONT_SERIALIZE);
    m->addPointerField<Cls, OperationPlan>(Tags::second, &Cls::getSecond,
                                           nullptr, DONT_SERIALIZE);
    m->addPointerField<Cls, OperationDependency>(Tags::dependency,
                                                 &Cls::getOperationDependency,
                                                 nullptr, DONT_SERIALIZE);
  }

 private:
  OperationPlan* first = nullptr;
  OperationPlan* second = nullptr;
  OperationDependency* dpdcy = nullptr;
};

/* An operationplan is the key dynamic element of a plan. It
 * represents a certain quantity being planned along a certain operation
 * during a certain date range.
 *
 * From a coding perspective:
 *  - Operationplans are created by the factory method createOperationPlan()
 *    on the matching Operation class.
 *  - The createLoadAndFlowplans() can optionally be called to also create
 *    the loadplans and flowplans, to take care of the material and
 *    capacity consumption.
 *  - Once you're sure about creating the operationplan, the activate()
 *    method should be called. It will assign the operationplan a unique
 *    numeric identifier, register the operationplan in a container owned
 *    by the operation instance, and also create loadplans and flowplans
 *    if this hasn't been done yet.
 *  - Operationplans can be organized in hierarchical structure, matching
 *    the operation hierarchies they belong to.
 */
class OperationPlan : public Object,
                      public HasProblems,
                      public HasSource,
                      private Tree::TreeNode,
                      public NonCopyable {
  friend class FlowPlan;
  friend class LoadPlan;
  friend class Demand;
  friend class Operation;
  friend class OperationSplit;
  friend class OperationAlternate;
  friend class OperationRouting;
  friend class FlowTransferBatch;
  friend class OperationPlanDependency;
  friend class OperationDependency;

 public:
  // Forward declarations
  class iterator;
  class FlowPlanIterator;
  class LoadPlanIterator;
  class ProblemIterator;
  class InterruptionIterator;
  class AlternateIterator;

  // Type definitions
  typedef TimeLine<FlowPlan> flowplanlist;
  typedef TimeLine<LoadPlan> loadplanlist;

  /* Flowplan iteration. */
  inline FlowPlanIterator getFlowPlans() const;
  inline FlowPlanIterator beginFlowPlans() const;
  inline FlowPlanIterator endFlowPlans() const;
  int sizeFlowPlans() const;

  /* Loadplan iteration. */
  inline LoadPlanIterator getLoadPlans() const;
  LoadPlanIterator beginLoadPlans() const;
  LoadPlanIterator endLoadPlans() const;
  int sizeLoadPlans() const;

  typedef forward_list<OperationPlanDependency*> dependencylist;

  class dependencyIterator {
   private:
    const OperationPlan* opplan;
    dependencylist::const_iterator cur;
    bool blckby = false;

   public:
    /* Constructor. */
    dependencyIterator(const OperationPlan* o, bool d = false)
        : opplan(o), blckby(d) {
      if (o) cur = opplan->getDependencies().begin();
    }

    /* Return current value and advance the iterator. */
    OperationPlanDependency* next() {
      if (!opplan) return nullptr;
      OperationPlanDependency* tmp = nullptr;
      while (cur != opplan->getDependencies().end()) {
        tmp = *cur;
        ++cur;
        if ((tmp->getFirst() == opplan && blckby) ||
            (tmp->getSecond() == opplan && !blckby))
          return tmp;
      }
      return nullptr;
    }
  };

  dependencyIterator getBlockingIterator() const {
    return dependencyIterator(this, true);
  }

  dependencyIterator getBlockedbyIterator() const {
    return dependencyIterator(this, false);
  }

  /* Interruption iteration. */
  inline InterruptionIterator getInterruptions() const;

  /* Returns whether this operationplan is a PO, MO or DO. */
  inline string getOrderType() const;

  /* Return the lowest priority of the demands to which this operationplan
   * pegs. */
  double getPriority() const;

  /* Returns the criticality index of the operationplan, which reflects
   * its urgency.
   * If the operationplan is on the critical path of one or more orders
   * the criticality is high. If the operationplan is only used to satisfy
   * safety stock requirements it will have a low criticality.
   * Computing the criticality is complex, CPU-expensive and the result
   * will change when the plan changes. Caching the value may be in
   * order.
   * Criticality is currently implemented as the slack in the downstream
   * path. If the criticality is 2, it means the operationplan can be
   * delayed by 2 days without impacting the delivery of any demand.
   */
  int getCriticality() const;

  /* Returns the difference between:
   *  a) the end date of the this operationplan
   * and
   *  b) the due of the demand fed by this operationplan
   *     minus the sum all of all operation times between
   *     the demand delivery and this demand.
   *
   * The concepts of "criticality" and "delay" are related but distinct.
   * A delayed operationplan will have a low criticality (because
   * the solver will squeeze all slack to reduce the lateness).
   * However, an operationplan can be critical and still satisfy demands
   * on time or even early.
   * Example:
   *    Imagine a series of operationplans that are planned start-to-end to
   *    meet a customer demand.
   *    The criticality of the operationplans will be computed as 0
   *    (because there is no slack between the operationplans), regardless
   *    whether the demand is shipped on time, early or late.
   *    The delay of the operationplans on the other hand will reflect the
   *    relation to the due date of the customer order.
   */
  Duration getDelay() const;

  const dependencylist& getDependencies() const { return dependencies; }

  /* Merge this operationplan with another one if possible.
   * The return value is true when a merge was done.
   * Careful: When a merge is done this pointer object is deleted!
   */
  bool mergeIfPossible();

  friend class iterator;

  /* This is a factory method that creates an operationplan pointer based
   * on the operation and reference. */
  static Object* createOperationPlan(const MetaClass*, const DataValueDict&,
                                     CommandManager* = nullptr);

  PooledString getBatch() const { return batch; }

  const string& getBatchString() const { return batch; }

  void setBatch(const string& t) {
    PooledString tmp(t);
    setBatch(tmp);
  }

  void setBatch(const PooledString&, bool up = true);

  /* Shortcut method to the cluster. */
  int getCluster() const;

  /* Destructor. */
  virtual ~OperationPlan();

  virtual void setChanged(bool b = true);

  /* Returns the quantity. */
  double getQuantity() const { return quantity; }

  /* Update the quantity. */
  void setQuantity(double f) { setQuantity(f, false, true, true); }

  void setQuantityExternal(double f);

  double getQuantityCompleted() const {
    if (getCompleted() || getProposed())
      return 0.0;
    else
      return quantity_completed < quantity ? quantity_completed : quantity;
  }

  double getQuantityCompletedRaw() const { return quantity_completed; }

  void setQuantityCompletedRaw(double q) { quantity_completed = q; }

  void setQuantityCompleted(double);

  double getQuantityRemaining() const {
    if (getCompleted() || getProposed())
      return quantity;
    else
      return quantity_completed < quantity ? quantity - quantity_completed
                                           : 0.0;
  }

  /* Updates the quantity.
   * The operationplan quantity is subject to the following rules:
   *  - The quantity must be greater than or equal to the minimum size.
   *    The value is rounded up to the smallest multiple above the minimum
   *    size if required, or rounded down to 0.
   *  - The quantity must be a multiple of the multiple_size field.
   *    The value is rounded up or down to meet this constraint.
   *  - The quantity must be smaller than or equal to the maximum size.
   *    The value is limited to the smallest multiple below this limit.
   *  - Setting the quantity of an operationplan to 0 is always possible,
   *    regardless of the minimum, multiple and maximum values.
   * This method can only be called on top operationplans. Sub operation
   * plans should pass on a call to the parent operationplan.
   */
  inline double setQuantity(double f, bool roundDown, bool update = true,
                            bool execute = true, Date end = Date::infinitePast);

  /* Returns a pointer to the demand for which this operationplan is a
   * delivery. If the operationplan isn't a delivery, this is a nullptr pointer.
   */
  Demand* getDemand() const { return dmd; }

  /* Updates the demand to which this operationplan is a solution. */
  void setDemand(Demand* l);

  /* Calculate the unavailable time during the operationplan. The regular
   * duration is extended with this amount.
   */
  Duration getUnavailable() const;

  /* Returns whether or not this operationplan is linked to a demand that
   * is planned late or not.
   */
  bool isConstrained() const;

  /* Return the status of the operationplan.
   * The status string is one of the following:
   *   - proposed
   *   - approved
   *   - confirmed
   *   - closed, pretty much an alias for confirmed
   */
  string getStatus() const;

  /* Update the status of the operationplan. */
  void setStatus(const string&, bool propagate, bool update);

  void setStatusRaw(const string& s) { setStatus(s, false, false); }

  void setStatusNoPropagation(const string& s) { setStatus(s, false, true); }

  void setStatus(const string& s) { setStatus(s, true, true); }

  /* Enforce a specific start date, end date and quantity. There is
   * no validation whether the values are consistent with the operation
   * parameters.
   * This method only works for locked operationplans.
   */
  void freezeStatus(Date, Date, double);

  /* Return the list of problems of this operationplan. */
  inline OperationPlan::ProblemIterator getProblems() const;

  bool getForcedUpdate() const { return (flags & FORCED_UPDATE) != 0; }

  bool getNoSetup() const { return (flags & NO_SETUP) != 0; }

  bool getActivated() const { return (flags & ACTIVATED) != 0; }

  bool getCompleted() const { return (flags & STATUS_COMPLETED) != 0; }

  bool getConfirmed() const { return (flags & STATUS_CONFIRMED) != 0; }

  bool getApproved() const { return (flags & STATUS_APPROVED) != 0; }

  bool getProposed() const {
    return (flags & (STATUS_CONFIRMED + STATUS_COMPLETED + STATUS_APPROVED +
                     STATUS_CLOSED)) == 0;
  }

  bool getClosed() const { return (flags & STATUS_CLOSED) != 0; }

  bool getFeasible() const { return !(flags & FEASIBLE); }

  /* Returns true is this operationplan is allowed to consume material.
   * This field only has an impact for locked operationplans.
   */
  bool getConsumeMaterial() const { return !(flags & CONSUME_MATERIAL); }

  /* Returns true is this operationplan is allowed to produce material.
   * This field only has an impact for locked operationplans.
   */
  bool getProduceMaterial() const { return !(flags & PRODUCE_MATERIAL); }

  /* Returns true is this operationplan is allowed to consume capacity.
   * This field only has an impact for locked operationplans.
   */
  bool getConsumeCapacity() const { return !(flags & CONSUME_CAPACITY); }

  /* Deletes all operationplans of a certain operation. A boolean flag
   * allows to specify whether locked operationplans are to be deleted too.
   */
  static void deleteOperationPlans(Operation* o, bool deleteLocked = false);

  /* Update the status to CONFIRMED, or back to PROPOSED. */
  void setConfirmed(bool b);

  /* Update the status to APPROVED, or back to PROPOSED. */
  void setApproved(bool b);

  /* Update the status to PROPOSED, or back to APPROVED. */
  void setProposed(bool b);

  /* Update the status to COMPLETED, or back to APPROVED. */
  void setCompleted(bool b);

  /* Update the status to CLOSED, or back to APPROVED. */
  void setClosed(bool b);

  void setActivated(bool b) {
    if (b)
      flags |= ACTIVATED;
    else
      flags &= ~ACTIVATED;
  }

  void setForcedUpdate(bool b) {
    if (b)
      flags |= FORCED_UPDATE;
    else
      flags &= ~FORCED_UPDATE;
  }

  void setNoSetup(bool b) {
    if (b)
      flags |= NO_SETUP;
    else
      flags &= ~NO_SETUP;
    updateSetupTime();
  }

  /* Update flag which allow/disallows material consumption. */
  void setConsumeMaterial(bool b) {
    if (b)
      flags &= ~CONSUME_MATERIAL;
    else
      flags |= CONSUME_MATERIAL;
    resizeFlowLoadPlans();
    for (auto* i = firstsubopplan; i; i = i->nextsubopplan)
      i->setConsumeMaterial(b);
  }

  /* Update flag which allow/disallows material production. */
  void setProduceMaterial(bool b) {
    if (b)
      flags &= ~PRODUCE_MATERIAL;
    else
      flags |= PRODUCE_MATERIAL;
    resizeFlowLoadPlans();
    for (auto* i = firstsubopplan; i; i = i->nextsubopplan)
      i->setProduceMaterial(b);
  }

  /* Update flag which allow/disallows capacity consumption. */
  void setConsumeCapacity(bool b) {
    if (!getConfirmed()) return;
    if (b)
      flags &= ~CONSUME_CAPACITY;
    else
      flags |= CONSUME_CAPACITY;
    resizeFlowLoadPlans();
    for (auto* i = firstsubopplan; i; i = i->nextsubopplan)
      i->setConsumeCapacity(b);
  }

  void setFeasible(bool b) {
    if (b)
      flags &= ~FEASIBLE;
    else
      flags |= FEASIBLE;
  }

  /* Returns a pointer to the operation being instantiated. */
  Operation* getOperation() const { return oper; }

  /* Update the operation of an operationplan. */
  void setOperation(Operation* o);

  inline OperationPlanState setOperationPlanParameters(
      double qty, Date startdate, Date enddate, bool preferEnd = true,
      bool execute = true, bool roundDown = true, bool later = false);

  /* Fixes the start and end date of an operationplan. Note that this
   * overrules the standard duration given on the operation, i.e. no logic
   * kicks in to verify the data makes sense. This is up to the user to
   * take care of.
   * The methods setStart(Date) and setEnd(Date) are therefore preferred
   * since they properly apply all appropriate logic.
   */
  void setStartAndEnd(Date st, Date nd) {
    dates.setStartAndEnd(st, nd);
    update();
  }

  /* Fixes the start date, end date and quantity of an operationplan. Note that
   * this overrules the standard duration given on the operation, i.e. no logic
   * kicks in to verify the data makes sense. This is up to the user to
   * take care of.
   * The methods setStart(Date) and setEnd(Date) are therefore preferred
   * since they properly apply all appropriate logic.
   */
  void setStartEndAndQuantity(Date st, Date nd, double q) {
    quantity = q;
    if (owner) owner->quantity = q;
    dates.setStartAndEnd(st, nd);
    update();
  }

  /* A method to restore a previous state of an operationplan.
   * NO validity checks are done on the parameters.
   */
  void restore(const OperationPlanState& x);

  /* Updates the operationplan owning this operationplan.
   * The optional extra argument specifies whether we need to complete
   * validation of the parent-child operation or not. Validation is
   * necessary to validate input from the user. But when the owner field
   * is set in the solver internally, we can skip validation to keep
   * performance high.
   * @see Operation::addSubOperationPlan
   * @see OperationAlternate::addSubOperationPlan
   * @see OperationRouting::addSubOperationPlan
   */
  void setOwner(OperationPlan* o, bool);

  void setOwner(OperationPlan* o) { setOwner(o, false); }

  /* Returns a pointer to the operationplan for which this operationplan
   * a sub-operationplan.
   * The method returns nullptr if there is no owner defined.
   * E.g. Sub-operationplans of a routing refer to the overall routing
   * operationplan.
   * E.g. An alternate sub-operationplan refers to its parent.
   * @see getTopOwner
   */
  OperationPlan* getOwner() const { return owner; }

  SetupEvent* getSetupEvent() const { return setupevent; }

  SetupMatrixRule* getSetupRule() const {
    return setupevent ? setupevent->getRule() : nullptr;
  }

  Duration getSetupOverride() const {
    return setupevent ? setupevent->getSetupOverride() : Duration(-1L);
  }

  void setSetupOverride(Duration d) {
    if (!setupevent) setupevent = new SetupEvent(this);
    setupevent->setSetupOverride(d);
    update();
  }

  /* Return a pointer to the next suboperationplan of the owner. */
  OperationPlan* getNextSubOpplan() const { return nextsubopplan; }

  /* Return a pointer to the previous suboperationplan of the owner. */
  OperationPlan* getPrevSubOpplan() const { return prevsubopplan; }

  /* Returns a pointer to the operationplan owning a set of
   * sub-operationplans. There can be multiple levels of suboperations.
   * If no owner exists the method returns the current operationplan.
   * @see getOwner
   */
  OperationPlan* getTopOwner() const {
    if (owner) {
      // There is an owner indeed
      OperationPlan* o(owner);
      while (o->owner) o = o->owner;
      return o;
    } else
      // This operationplan is itself the top of a hierarchy
      return const_cast<OperationPlan*>(this);
  }

  /* Returns the start and end date of this operationplan. */
  const DateRange& getDates() const { return dates; }

  /* Return the start of the actual operation time. */
  Date getSetupEnd() const {
    return setupevent ? setupevent->getDate() : dates.getStart();
  }

  /* Return the setup cost. */
  double getSetupCost() const;

  /* Update the setup information. */
  void setSetupEvent(TimeLine<LoadPlan>*, Date, const PooledString&,
                     SetupMatrixRule* = nullptr);

  void setSetupEvent(Resource* r, Date d, const PooledString& s,
                     SetupMatrixRule* m = nullptr);

  /* Make sure that a status change is also reflected on related
   * operationplans. Note that the propagation of a status change is not
   * undoable: eg after changing the status from proposed to closed, we can't go
   * back to the previous situation any more.
   */
  void propagateStatus(bool log = false);

  /* Match linked operationplan dependencies. */
  void matchDependencies(bool log = false);

  /* Remove the setup event. */
  void clearSetupEvent() {
    if (!setupevent) return;
    setupevent->erase();
    if (getSetupOverride() != Duration(-1L))
      setupevent->reset();
    else {
      delete setupevent;
      setupevent = nullptr;
    }
  }

  /* Remove the setup event. */
  void nullSetupEvent() {
    if (setupevent && getSetupOverride() != Duration(-1L)) setupevent->reset();
    setupevent = nullptr;
  }

  /* Return true if the operationplan is redundant, ie all material
   * it produces is not used at all.
   * If the optional argument is false (which is the default value), we
   * check with the minimum stock level of the buffers. If the argument
   * is true, we check with 0.
   */
  double isExcess(bool = false) const;

  /* Returns a unique identifier of the operationplan.
   * The identifier can be specified in the data input (in which case
   * we check for the uniqueness during the read operation).
   * For operationplans created during a solver run, the identifier is
   * assigned in the instantiate() function. The numbering starts with the
   * highest identifier read in from the input and is then incremented
   * for every operationplan that is registered.
   *
   * This method is declared as constant. But actually, it can still update
   * the identifier field if it is wasn't set before.
   */
  const string& getReference() const {
    if (getName().empty()) {
      const_cast<OperationPlan*>(this)->assignReference();  // Lazy generation
      const_cast<OperationPlan*>(this)->setActivated(true);
    }
    return getName();
  }

  /* Update the external identifier. */
  void setReference(const string& s) {
    if (getName().empty()) {
      setName(s);
      assignReference();
      setActivated(true);
    } else
      st.rename(this, s);
  }

  void setRawReference(const string& s) { setName(s); }

  /* Update the next autogenerated reference number.
   * Only increases are allowed to avoid assigning duplicate references.
   */
  static void setCounterMin(unsigned long l) {
    if (counterMin < l) counterMin = l;
    if (counterMin >= ULONG_MAX)
      throw RuntimeException(
          "Exhausted the range of available operationplan references");
  }

  /* Return the next autogenerated id number. */
  static unsigned long getCounterMin() { return counterMin; }

  /* Return the end date. */
  Date getEnd() const { return dates.getEnd(); }

  /* Updates the end date of the operationplan and compute the start
   * date.
   * Locked operationplans are not updated by this function.
   * Slack can be introduced between sub operationaplans by this method,
   * i.e. the sub operationplans are only moved if required to meet the
   * end date.
   */
  void setEnd(Date, bool force);

  void setEnd(Date d) { setEnd(d, false); }

  void setEndForce(Date d) { setEnd(d, true); }

  /* Return the start date. */
  Date getStart() const { return dates.getStart(); }

  /* Updates the start date of the operationplan and compute the end
   * date.
   * Locked operation_plans are not updated by this function.
   * Slack can be introduced between sub operationaplans by this method,
   * i.e. the sub operationplans are only moved if required to meet the
   * start date.
   */
  void setStart(Date, bool force, bool preferend);

  void setStart(Date d) { setStart(d, false, true); }

  void setStartForce(Date d) { setStart(d, true, true); }

  /* Return the efficiency factor of the operationplan.
   * It's computed as the most inefficient of all resources loaded by the
   * operationplan.
   */
  double getEfficiency(Date = Date::infinitePast) const;

  static int initialize();

  static PyObject* calculateOperationTimePython(PyObject*, PyObject*);

  PyObject* str() const;

  /* Python factory method. */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  /* Initialize the operationplan. The initialization function should be
   * called when the operationplan is ready to be 'officially' added. The
   * initialization performs the following actions:
   *  - assign an identifier
   *  - create the flow and loadplans if these hadn't been created
   *    before
   *  - add the operationplan to the global list of operationplans
   *  - create a link with a demand object if this is a delivery
   *    operationplan
   *
   * The return value indicates whether the initialization was successfull.
   * If the operationplan is invalid, it will be DELETED and the return value
   * is false.
   */
  bool activate(bool createsubopplans = true, bool use_start = false);

  /* Remove an operationplan from the list of officially registered ones.
   * The operationplan will keep its loadplans and flowplans after
   * unregistration.
   */
  void deactivate();

  /* Convert a proposed end date to the date when material is produced. */
  Date computeOperationToFlowDate(Date) const;

  /* This method links the operationplan in the list of all operationplans
   * maintained on the operation.
   * In most cases calling this method is not required since it included
   * in the activate method. In exceptional cases the solver already
   * needs to see uncommitted operationplans in the list - eg for the
   * procurement buffer.
   * @see activate
   */
  void insertInOperationplanList();

  /* This method remove the operationplan from the list of all operationplans
   * maintained on the operation.
   * @see deactivate
   */
  void removeFromOperationplanList();

  /* Remove a sub-operation_plan from the list. */
  virtual void eraseSubOperationPlan(OperationPlan*);

  /* This function is used to create the loadplans, flowplans and
   * setup operationplans.
   */
  void createFlowLoads(const vector<Resource*>* = nullptr);

  /* A function to compute whether an operationplan is feasible or not. */
  bool updateFeasible();

  /* Python API for the above method. */
  static PyObject* updateFeasiblePython(PyObject*, PyObject*);

  /* This function is used to delete the loadplans, flowplans and
   * setup operationplans.
   */
  void deleteFlowLoads();

  /* Operationplans are never considered hidden, even if the operation they
   * instantiate is hidden. Only exception are stock operationplans.
   */
  inline bool getHidden() const;

  /* Searches for an OperationPlan with a given identifier.
   * Returns a nullptr pointer if no such OperationPlan can be found.
   * The method is of complexity O(n), i.e. involves a LINEAR search through
   * the existing operationplans, and can thus be quite slow in big models.
   * The method is O(1), i.e. constant time regardless of the model size,
   * when the parameter passed is bigger than the operationplan counter.
   */
  static OperationPlan* findReference(string const& l);

  /* Problem detection is actually done by the Operation class. That class
   * actually "delegates" the responsability to this class, for efficiency.
   */
  virtual void updateProblems();

  /* Implement the pure virtual function from the HasProblem class. */
  inline Plannable* getEntity() const;

  /* Return the metadata. We return the metadata of the operation class,
   * not the one of the operationplan class!
   */
  const MetaClass& getType() const { return *metadata; }

  static const MetaClass* metadata;

  static const MetaCategory* metacategory;

  /* Lookup a operationplan. */
  static Object* finder(const DataValueDict&);

  /* Comparison of 2 OperationPlans.
   * To garantuee that the problems are sorted in a consistent and stable
   * way, the following sorting criteria are used (in order of priority):
   * - Operation
   * - Start date (earliest dates first)
   * - Quantity (biggest quantities first)
   * Multiple operationplans for the same values of the above keys can exist.
   */
  bool operator<(const OperationPlan& a) const;

  /* Return the total quantity which this operationplan, its children
   * and its parents produce or consume from a given buffer.
   */
  double getTotalFlow(const Buffer* b) const {
    return getTopOwner()->getTotalFlowAux(b);
  }

  static inline iterator end();

  static inline iterator begin();

  // Delete all operationplans
  static void clear();

  inline OperationPlan::iterator getSubOperationPlans() const;

  PeggingIterator getPeggingDownstream() const;

  PeggingIterator getPeggingDownstreamFirstLevel() const;

  PeggingIterator getPeggingUpstream() const;

  PeggingIterator getPeggingUpstreamFirstLevel() const;

  PeggingDemandIterator getPeggingDemand() const;

  /* Return an iterator over alternate operations for this operationplan. */
  AlternateIterator getAlternates() const;

  /* Return the setup time on this operationplan. */
  Duration getSetup() const;

  /* Update the setup time in situations where it could have changed.
   * The return value is true when the time has changed.
   */
  bool updateSetupTime(bool report = false);

  /* Delete all existing loadplans. */
  void setResetResources(bool);

  /* Return the color of the operationplan. */
  static PyObject* getColorPython(PyObject*, PyObject*);

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::reference, &Cls::getReference,
                              &Cls::setReference, "", MANDATORY);
    m->addStringRefField<Cls>(Tags::id, &Cls::getReference, &Cls::setReference,
                              "", DONT_SERIALIZE);
    m->addPointerField<Cls, Operation>(
        Tags::operation, &Cls::getOperation, &Cls::setOperation,
        BASE + PLAN + WRITE_REFERENCE_DFT + WRITE_OBJECT_SVC + WRITE_HIDDEN);
    m->addPointerField<Cls, Demand>(Tags::demand, &Cls::getDemand,
                                    &Cls::setDemand, BASE + WRITE_HIDDEN);
    m->addDateField<Cls>(Tags::start, &Cls::getStart, &Cls::setStart,
                         Date::infiniteFuture);
    m->addDateField<Cls>(Tags::start_force, &Cls::getStart, &Cls::setStartForce,
                         Date::infiniteFuture, DONT_SERIALIZE);
    m->addDateField<Cls>(Tags::end, &Cls::getEnd, &Cls::setEnd,
                         Date::infiniteFuture);
    m->addDateField<Cls>(Tags::end_force, &Cls::getEnd, &Cls::setEndForce,
                         Date::infiniteFuture, DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::setup, &Cls::getSetup,
                             &Cls::setSetupOverride, -1L, PLAN);
    m->addDateField<Cls>(Tags::setupend, &Cls::getSetupEnd, nullptr,
                         Date::infinitePast, PLAN);
    m->addDoubleField<Cls>(Tags::priority, &Cls::getPriority, nullptr, 999.0,
                           PLAN);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity,
                           &Cls::setQuantityExternal);
    m->addIteratorField<Cls, OperationPlan::ProblemIterator, Problem>(
        Tags::problems, Tags::problem, &Cls::getProblems, PLAN + WRITE_OBJECT);
    m->addStringRefField<Cls>(Tags::batch, &Cls::getBatchString, &Cls::setBatch,
                              "");
    // Default of -999 to enforce serializing the value if it is 0
    m->addIntField<Cls>(Tags::criticality, &Cls::getCriticality, nullptr, -999,
                        PLAN);
    m->addStringField<Cls>(Tags::status, &Cls::getStatus, &Cls::setStatus,
                           "proposed");
    m->addStringField<Cls>(Tags::statusNoPropagation, &Cls::getStatus,
                           &Cls::setStatusNoPropagation, "proposed",
                           DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::approved, &Cls::getApproved, &Cls::setApproved,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::proposed, &Cls::getProposed, &Cls::setProposed,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::confirmed, &Cls::getConfirmed,
                         &Cls::setConfirmed, BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::closed, &Cls::getClosed, &Cls::setClosed,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::completed, &Cls::getCompleted,
                         &Cls::setCompleted, BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::consume_material, &Cls::getConsumeMaterial,
                         &Cls::setConsumeMaterial, BOOL_TRUE);
    m->addBoolField<Cls>(Tags::produce_material, &Cls::getProduceMaterial,
                         &Cls::setProduceMaterial, BOOL_TRUE);
    m->addBoolField<Cls>(Tags::consume_capacity, &Cls::getConsumeCapacity,
                         &Cls::setConsumeCapacity, BOOL_TRUE);
    m->addBoolField<Cls>(Tags::feasible, &Cls::getFeasible, &Cls::setFeasible,
                         BOOL_TRUE);
    m->addDoubleField<Cls>(Tags::quantity_completed, &Cls::getQuantityCompleted,
                           &Cls::setQuantityCompleted);
    HasSource::registerFields<Cls>(m);
    m->addPointerField<Cls, OperationPlan>(Tags::owner, &Cls::getOwner,
                                           &Cls::setOwner);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::unavailable, &Cls::getUnavailable, nullptr,
                             0L, DONT_SERIALIZE);
    m->addIteratorField<Cls, OperationPlan::InterruptionIterator,
                        OperationPlan::InterruptionIterator>(
        Tags::interruptions, Tags::interruption, &Cls::getInterruptions,
        DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::delay, &Cls::getDelay, nullptr, -999L, PLAN);
    m->addIteratorField<Cls, OperationPlan::FlowPlanIterator, FlowPlan>(
        Tags::flowplans, Tags::flowplan, &Cls::getFlowPlans,
        PLAN + WRITE_HIDDEN);
    m->addIteratorField<Cls, OperationPlan::LoadPlanIterator, LoadPlan>(
        Tags::loadplans, Tags::loadplan, &Cls::getLoadPlans, PLAN);
    m->addIteratorClassField<Cls, PeggingIterator>(
        Tags::pegging_downstream, Tags::pegging, &Cls::getPeggingDownstream,
        DONT_SERIALIZE);
    m->addIteratorClassField<Cls, PeggingIterator>(
        Tags::pegging_downstream_first_level, Tags::pegging,
        &Cls::getPeggingDownstreamFirstLevel, DONT_SERIALIZE);
    m->addIteratorClassField<Cls, PeggingIterator>(
        Tags::pegging_upstream, Tags::pegging, &Cls::getPeggingUpstream,
        DONT_SERIALIZE);
    m->addIteratorClassField<Cls, PeggingIterator>(
        Tags::pegging_upstream_first_level, Tags::pegging,
        &Cls::getPeggingUpstreamFirstLevel, DONT_SERIALIZE);
    m->addIteratorClassField<Cls, PeggingDemandIterator>(
        Tags::pegging_demand, Tags::pegging, &Cls::getPeggingDemand,
        PLAN + WRITE_OBJECT);
    m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(
        Tags::operationplans, Tags::operationplan, &Cls::getSubOperationPlans,
        DONT_SERIALIZE);
    m->addIteratorField<Cls, OperationPlan::AlternateIterator, Operation>(
        Tags::alternates, Tags::alternate, "AlternateOperationIterator",
        "Iterator over operation alternates", &Cls::getAlternates,
        PLAN + FORCE_BASE);
    m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0,
                        DONT_SERIALIZE);
    m->addStringField<Cls>(Tags::ordertype, &Cls::getOrderType,
                           &Cls::setOrderType, "MO");
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation);
    m->addPointerField<Cls, Location>(Tags::origin, &Cls::getOrigin,
                                      &Cls::setOrigin);
    m->addPointerField<Cls, Supplier>(Tags::supplier, &Cls::getSupplier,
                                      &Cls::setSupplier);
    m->addPointerField<Cls, SetupMatrixRule>(Tags::rule, &Cls::getSetupRule,
                                             nullptr, DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::setupoverride, &Cls::getSetupOverride,
                             &Cls::setSetupOverride, -1L);
    m->addIteratorField<Cls, dependencyIterator, OperationPlanDependency>(
        Tags::blockedby, Tags::dependency, &Cls::getBlockedbyIterator,
        DONT_SERIALIZE);
    m->addIteratorField<Cls, dependencyIterator, OperationPlanDependency>(
        Tags::blocking, Tags::dependency, &Cls::getBlockingIterator,
        DONT_SERIALIZE);
  }

  static PyObject* createIterator(PyObject* self, PyObject* args);

  static bool getPropagateSetups() { return propagatesetups; }

  static bool setPropagateSetups(bool b) {
    auto tmp = propagatesetups;
    propagatesetups = b;
    return tmp;
  }

  /* Update the loadplans and flowplans of the operationplan based on the
   * latest information of quantity, date and locked flag.
   * This method will NOT update parent or child operationplans.
   *
   * Only intended for internal use by update()
   */
  void resizeFlowLoadPlans();

 private:
  /* A tree structure with all operationplans to allow a fast lookup by id. */
  static Tree st;

  /* Updates the operationplan based on the latest information of quantity,
   * date and locked flag.
   * This method will also update parent and child operationplans.
   * @see resizeFlowLoadPlans
   */
  void update();

  /* Generates a unique identifier for the operationplan.
   * The field is 0 while the operationplan is not fully registered yet.
   * The field is 1 when the operationplan is fully registered but only a
   * temporary id is generated.
   * A unique value for each operationplan is created lazily when the
   * method getIdentifier() is called.
   */
  bool assignReference();

  /* Recursive auxilary function for getTotalFlow.
   * @ see getTotalFlow
   */
  double getTotalFlowAux(const Buffer*) const;

  /* Maintain the operationplan list in sorted order.
   *
   * Only intended for internal use by update()
   */
  void updateOperationplanList();

  /* Update the setup time on all neighbouring operationplans.
   *
   * This method leaves the setup end date constant, which also
   * keeps all material production and consumption at their original
   * dates. The resource loading can be adjusted however.
   *
   * Only intended for internal use by update().
   */
  void scanSetupTimes();

 private:
  /* Default constructor.
   * This way of creating operationplan objects is not intended for use by
   * any client applications. Client applications should use the factory
   * method on the operation class instead.
   * Subclasses of the Operation class may use this constructor in their
   * own override of the createOperationPlan method.
   * @see Operation::createOperationPlan
   */
  OperationPlan() { initType(metadata); }

  OperationPlan(Operation* o) : oper(o) { initType(metadata); }

  static const unsigned short STATUS_APPROVED = 1;
  static const unsigned short STATUS_CONFIRMED = 2;
  static const unsigned short STATUS_COMPLETED = 4;
  static const unsigned short STATUS_CLOSED = 8;
  // TODO Conceptually this may not ideal: Rather than a
  // quantity-based distinction (between CONSUME_MATERIAL and
  // PRODUCE_MATERIAL) having a time-based distinction may be more
  // appropriate (between PROCESS_MATERIAL_AT_START and
  // PROCESS_MATERIAL_AT_END).
  static const unsigned short CONSUME_MATERIAL = 16;
  static const unsigned short PRODUCE_MATERIAL = 32;
  static const unsigned short CONSUME_CAPACITY = 64;
  static const unsigned short FEASIBLE = 128;
  static const unsigned short ACTIVATED = 256;
  static const unsigned short FORCED_UPDATE = 512;
  static const unsigned short NO_SETUP = 1024;

  /* Counter of OperationPlans, which is used to automatically assign a
   * unique identifier for each operationplan.
   * The value of the counter is the first available identifier value that
   * can be used for a new operationplan.
   * The first value is 1, and each operationplan increases it by 1.
   * @see assignIdentifier()
   */
  static unsigned long counterMin;
  static string referenceMax;

  /* Flag controlling where setup time verification should be performed. */
  static bool propagatesetups;

  /* Pointer to a higher level OperationPlan. */
  OperationPlan* owner = nullptr;

  /* Pointer to the demand.
   * Only delivery operationplans have this field set. The field is nullptr
   * for all other operationplans.
   */
  Demand* dmd = nullptr;

  /* External identifier for this operationplan. */
  string ref;

  /* Start and end date. */
  DateRange dates;

  /* Pointer to the operation. */
  Operation* oper = nullptr;

  /* Root of a single linked list of flowplans. */
  FlowPlan* firstflowplan = nullptr;

  /* Single linked list of loadplans. */
  LoadPlan* firstloadplan = nullptr;

  /* Pointer to the previous operationplan.
   * Operationplans are chained in a doubly linked list for each operation.
   * @see next
   */
  OperationPlan* prev = nullptr;

  /* Pointer to the next operationplan.
   * Operationplans are chained in a doubly linked list for each operation.
   * @see prev
   */
  OperationPlan* next = nullptr;

  /* Pointer to the first suboperationplan of this operationplan. */
  OperationPlan* firstsubopplan = nullptr;

  /* Pointer to the last suboperationplan of this operationplan. */
  OperationPlan* lastsubopplan = nullptr;

  /* Pointer to the next suboperationplan of the parent operationplan. */
  OperationPlan* nextsubopplan = nullptr;

  /* Pointer to the previous suboperationplan of the parent operationplan. */
  OperationPlan* prevsubopplan = nullptr;

  /* Setup event of this operationplan. */
  SetupEvent* setupevent = nullptr;

  /* Serial number, batch or sales order for MTO production. */
  PooledString batch;

  dependencylist dependencies;

  /* Quantity. */
  double quantity = 0.0;

  /* Completed quantity. */
  double quantity_completed = 0.0;

  /* Flags on the operationplan: status, consumematerial, consumecapacity,
   * infeasible. */
  unsigned short flags = 0;

  /* Hidden, static field to store the location during import. */
  static Location* loc;

  /* Hidden, static field to store the origin during import. */
  static Location* ori;

  /* Hidden, static field to store the supplier during import. */
  static Supplier* sup;

  /* Hidden, static field to store the order type during import. */
  static string ordertype;

  /* Hidden, static field to store the item during import. */
  static Item* itm;

  void setLocation(Location*);

  inline Location* getLocation() const;

  void setOrigin(Location*);

  inline Location* getOrigin() const;

  void setSupplier(Supplier*);

  inline Supplier* getSupplier() const;

  void setOrderType(const string& o) { ordertype = o; }

  void setItem(Item*);

  inline Item* getItem() const;

  /* Called when the item, location or supplier of an existing purchase order is
   * changed */
  void updatePurchaseOrder(Item*, Location*, Supplier*);

  /* Called when the item, origin or location of an existing distribution order
   * is changed */
  void updateDistributionOrder(Item*, Location*, Location*);
};

template <class type>
bool TimeLine<type>::Event::operator<(const Event& fl2) const {
  if (getDate() != fl2.getDate())
    return getDate() < fl2.getDate();
  else if (getEventType() == 5 || fl2.getEventType() == 5) {
    if (getEventType() == 5 && fl2.getEventType() == 5) {
      auto o1 = getOperationPlan();
      auto o2 = fl2.getOperationPlan();
      if (o1 && o2)
        return *getOperationPlan() < *fl2.getOperationPlan();
      else
        return o2 ? true : false;
    } else
      return getEventType() > fl2.getEventType();
  } else if (getEventType() != fl2.getEventType())
    return getEventType() > fl2.getEventType();
  else if (fabs(getQuantity() - fl2.getQuantity()) > ROUNDING_ERROR)
    return getQuantity() > fl2.getQuantity();
  else {
    OperationPlan* op1 = getOperationPlan();
    OperationPlan* op2 = fl2.getOperationPlan();
    if (op1 && op2)
      return *op1 < *op2;
    else
      return op1 == nullptr;
  }
}

/* This type defines what mode used to search the alternates. */
enum class SearchMode {
  /* Select the alternate with the lowest priority number.
   * This is the default.
   */
  PRIORITY = 0,
  /* Select the alternate which gives the lowest cost. */
  MINCOST = 1,
  /* Select the alternate which gives the lowest penalty. */
  MINPENALTY = 2,
  /* Select the alternate which gives the lowest sum of the cost and
   * penalty. */
  MINCOSTPENALTY = 3
};

/* Writes a search mode to an output stream. */
inline ostream& operator<<(ostream& os, const SearchMode& d) {
  switch (d) {
    case SearchMode::PRIORITY:
      os << "PRIORITY";
      return os;
    case SearchMode::MINCOST:
      os << "MINCOST";
      return os;
    case SearchMode::MINPENALTY:
      os << "MINPENALTY";
      return os;
    case SearchMode::MINCOSTPENALTY:
      os << "MINCOSTPENALTY";
      return os;
    default:
      assert(false);
      return os;
  }
}

/* Translate a string to a search mode value. */
SearchMode decodeSearchMode(const string& c);

/* An operation represents an activity: these consume and produce
 * material, take time and also require capacity.
 *
 * An operation consumes and produces material, modeled through flows.
 * An operation requires capacity, modeled through loads.
 *
 * This is an abstract base class for all different operation types.
 */
class Operation : public HasName<Operation>,
                  public HasLevel,
                  public Plannable,
                  public HasDescription {
  friend class Flow;
  friend class Load;
  friend class OperationPlan;
  friend class SubOperation;
  friend class Item;

 protected:
  /* Extra logic called when instantiating an operationplan.
   * When the function returns false the creation of the operationplan
   * is denied and it is deleted.
   */
  virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true,
                                bool use_start = false) {
    return true;
  }

 public:
  /* Default constructor. */
  explicit Operation() {}

  /* Destructor. */
  virtual ~Operation();

  virtual string getOrderType() const { return "MO"; }

  OperationPlan* getFirstOpPlan() const { return first_opplan; }

  OperationPlan* getLastOpPlan() const { return last_opplan; }

  /* Returns the delay after this operation. */
  Duration getPostTime() const { return post_time; }

  /* Updates the delay after this operation.
   * This delay is a soft constraint. This means that solvers should try to
   * respect this waiting time but can choose to leave a shorter time delay
   * if required.
   */
  void setPostTime(Duration t) {
    if (t < Duration(0L))
      logger << "Warning: No negative post-operation time allowed" << endl;
    else {
      post_time = t;
      setChanged();
    }
  }

  /* Return the operation cost.
   * The cost of executing this operation, per unit of the
   * operation_plan.
   * The default value is 0.0.
   */
  double getCost() const { return cost; }

  /* Update the operation cost.
   * The cost of executing this operation, per unit of the operation_plan.
   */
  void setCost(const double c) { cost = max(c, 0.0); }

  typedef Association<Operation, Buffer, Flow>::ListA flowlist;
  typedef Association<Operation, Resource, Load>::ListA loadlist;
  typedef forward_list<OperationDependency*> dependencylist;

  /* This is the factory method which creates all operationplans of the
   * operation. */
  OperationPlan* createOperationPlan(
      double, Date, Date, const PooledString&, Demand* = nullptr,
      OperationPlan* = nullptr, bool makeflowsloads = true,
      bool roundDown = true, const string& ref = PooledString::nullstring,
      double = 0.0, const string& = PooledString::nullstring,
      const vector<Resource*>* = nullptr) const;

  /* Returns true for operation types that own suboperations. */
  virtual bool hasSubOperations() const { return false; }

  /* Calculates the daterange starting from (or ending at) a certain date
   * and using a certain amount of effective available time on the
   * operation.
   *
   * This calculation considers the availability calendars of:
   * - the availability calendar of the operation and its location
   * - the availability calendar of all resources loaded by the operation,
   *   plus the availability calendar of their location
   *
   * @param[in] thedate  The date from which to start searching.
   * @param[in] duration The amount of available time we are looking for.
   * @param[in] forward  The search direction
   * @param[out] actualduration This variable is updated with the actual
   *             amount of available time found.
   */
  DateRange calculateOperationTime(const OperationPlan* opplan, Date thedate,
                                   Duration duration, bool forward,
                                   Duration* actualduration = nullptr,
                                   bool considerResourceCalendars = true) const;

  /* Calculates the effective, available time between two dates.
   *
   * This calculation considers the availability calendars of:
   * - the availability calendar of the operation and its location
   * - the availability calendar of all resources loaded by the operation,
   *   plus the availability calendar of their location
   *
   * @param[in] start  The date from which to start searching.
   * @param[in] end    The date where to stop searching.
   * @param[out] actualduration This variable is updated with the actual
   *             amount of available time found.
   */
  DateRange calculateOperationTime(const OperationPlan* opplan, Date start,
                                   Date end, Duration* actualduration = nullptr,
                                   bool considerResourceCalendars = true) const;

  /* This method stores ALL logic the operation needs to compute the
   * correct relationship between the quantity, startdate and enddate
   * of an operationplan.
   *
   * The parameters "startdate", "enddate" and "quantity" can be
   * conflicting if all are specified together.
   * Typically, one would use one of the following combinations:
   *  - specify quantity and start date, and let the operation compute the
   *    end date.
   *  - specify quantity and end date, and let the operation compute the
   *    start date.
   *  - specify both the start and end date, and let the operation compute
   *    the quantity.
   *  - specify quantity, start and end date. In this case, you need to
   *    be aware that the operationplan that is created can be different
   *    from the parameters you requested.
   *
   * The following priority rules apply upon conflicts.
   *  - respecting the end date has the first priority.
   *  - respecting the start date has second priority.
   *  - respecting the quantity should be done if the specified dates can
   *    be respected.
   *  - if the quantity is being computed to meet the specified dates, the
   *    quantity being passed as argument is to be treated as a maximum
   *    limit. The created operationplan can have a smaller quantity, but
   *    not bigger...
   *  - at all times, we expect to have an operationplan that is respecting
   *    the constraints set by the operation. If required, some of the
   *    specified parameters may need to be violated. In case of such a
   *    violation we expect the operationplan quantity to be 0.
   *
   * The pre- and post-operation times are NOT considered in this method.
   * This method only enforces "hard" constraints. "Soft" constraints are
   * considered as 'hints' by the solver.
   *
   * Subclasses need to override this method to implement the correct
   * logic.
   */
  virtual OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd = true, bool execute = true, bool roundDown = true,
      bool later = false) const = 0;

  /* Updates the quantity of an operationplan.
   * This method considers the lot size constraints and also propagates
   * the new quantity to child operationplans.
   */
  virtual double setOperationPlanQuantity(OperationPlan* oplan, double f,
                                          bool roundDown, bool upd,
                                          bool execute, Date start) const;

  /* Returns the location of the operation, which is used to model the
   * working hours and holidays. */
  Location* getLocation() const { return loc; }

  /* Updates the location of the operation, which is used to model the
   * working hours and holidays. */
  void setLocation(Location* l) { loc = l; }

  /* Returns the item. */
  Item* getItem() const { return item; }

  /* Updates the item. */
  void setItem(Item*);

  /* Update the priority. */
  void setPriority(int i) { priority = i; }

  /* Return the priority. */
  int getPriority() const { return priority; }

  /* Get the start date of the effectivity range. */
  Date getEffectiveStart() const { return effectivity.getStart(); }

  /* Get the end date of the effectivity range. */
  Date getEffectiveEnd() const { return effectivity.getEnd(); }

  /* Return the effectivity daterange.
   * The default covers the complete time horizon.
   */
  DateRange getEffective() const { return effectivity; }

  Duration getBatchWindow() const { return batchwindow; }

  void setBatchWindow(Duration d) { batchwindow = d; }

  /* Update the start date of the effectivity range. */
  void setEffectiveStart(Date d) { effectivity.setStart(d); }

  /* Update the end date of the effectivity range. */
  void setEffectiveEnd(Date d) { effectivity.setEnd(d); }

  /* Update the effectivity range. */
  void setEffective(DateRange dr) { effectivity = dr; }

  /* Returns the availability calendar of the operation. */
  Calendar* getAvailable() const { return available; }

  /* Updates the availability calendar of the operation. */
  void setAvailable(Calendar* b) { available = b; }

  /* Returns the minimum maxearly of any load. */
  virtual Duration getMaxEarly() const;

  /* Returns an reference to the list of flows.
   * TODO get rid of this method.
   */
  const flowlist& getFlows() const { return flowdata; }

  /* Returns an reference to the list of flows. */
  flowlist::const_iterator getFlowIterator() const { return flowdata.begin(); }

  /* Returns an reference to the list of loads.
   * TODO get rid of this method.
   */
  const loadlist& getLoads() const { return loaddata; }

  /* Returns an reference to the list of loads. */
  loadlist::const_iterator getLoadIterator() const { return loaddata.begin(); }

  class dependencyIterator {
   private:
    const Operation* oper;
    dependencylist::const_iterator cur;
    bool blckby = false;

   public:
    /* Constructor. */
    dependencyIterator(const Operation* o, bool d = false)
        : oper(o), blckby(d) {
      if (o) cur = o->getDependencies().begin();
    }

    /* Return current value and advance the iterator. */
    OperationDependency* next() {
      if (!oper) return nullptr;
      OperationDependency* tmp = nullptr;
      while (cur != oper->getDependencies().end()) {
        tmp = *cur;
        ++cur;
        if ((tmp->getOperation() == oper && blckby) ||
            (tmp->getBlockedBy() == oper && !blckby))
          return tmp;
      }
      return nullptr;
    }
  };

  dependencyIterator getBlockingIterator() const {
    return dependencyIterator(this, false);
  }

  dependencyIterator getBlockedbyIterator() const {
    return dependencyIterator(this, true);
  }

  OperationPlan::iterator getOperationPlans() const;

  /* Return the flow that is associates a given buffer with this
   * operation. Returns nullptr is no such flow exists. */
  Flow* findFlow(const Buffer* b, Date d) const;

  /* Return the load that is associates a given resource with this
   * operation. Returns nullptr is no such load exists. */
  Load* findLoad(const Resource* r, Date d) const {
    return loaddata.find(r, d);
  }

  /* Deletes all operationplans of this operation. The boolean parameter
   * controls whether we delete also locked operationplans or not.
   */
  void deleteOperationPlans(bool deleteLockedOpplans = false);

  /* Sets the minimum size of operationplans.
   * The default value is 1.0
   */
  void setSizeMinimum(double f) {
    if (f < 0)
      logger << "Warning: Operation can't have a negative minimum size" << endl;
    else {
      size_minimum = f;
      setChanged();
    }
  }

  /* Returns the minimum size for operationplans. */
  double getSizeMinimum() const { return size_minimum; }

  /* Returns the calendar defining the minimum size of operationplans. */
  Calendar* getSizeMinimumCalendar() const { return size_minimum_calendar; }

  /* Sets the multiple size of operationplans. */
  void setSizeMultiple(double f) {
    if (f < 0)
      logger << "Warning: Operation can't have a negative multiple size"
             << endl;
    else {
      size_multiple = f;
      setChanged();
    }
  }

  /* Sets a calendar to defining the minimum size of operationplans. */
  virtual void setSizeMinimumCalendar(Calendar* c) {
    size_minimum_calendar = c;
    setChanged();
  }

  /* Returns the mutiple size for operationplans. */
  double getSizeMultiple() const { return size_multiple; }

  /* Sets the maximum size of operationplans. */
  void setSizeMaximum(double f) {
    if (f < size_minimum)
      logger << "Warning: Operation maximum size must be higher than the "
                "minimum size"
             << endl;
    else if (f <= 0)
      logger << "Warning: Operation maximum size must be greater than 0"
             << endl;
    else {
      size_maximum = f;
      setChanged();
    }
  }

  /* Returns the maximum size for operationplans. */
  double getSizeMaximum() const { return size_maximum; }

  /* Return the decoupled lead time of this operation. */
  virtual pair<Duration, Date> getDecoupledLeadTime(double, Date) const = 0;

  static PyObject* getDecoupledLeadTimePython(PyObject* self, PyObject* args);

  /* Add a new child operationplan.
   * By default an operationplan can have only a single suboperation,
   * representing a changeover.
   * Operation subclasses can implement their own restrictions on the
   * number and structure of the suboperationplans.
   * @see OperationAlternate::addSubOperationPlan
   * @see OperationRouting::addSubOperationPlan
   * @see OperationSplit::addSubOperationPlan
   */
  virtual void addSubOperationPlan(OperationPlan*, OperationPlan*, bool = true);

  static int initialize();

  /* Auxilary method to initialize an vector of availability calendar
   * iterators related to an operation.
   */
  unsigned short collectCalendars(Calendar::EventIterator[], Date,
                                  const OperationPlan*, bool forward = true,
                                  bool considerResourceCalendars = true) const;

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  typedef list<SubOperation*> Operationlist;

  /* Returns a reference to the list of sub operations of this operation.
   * The list is always sorted with the operation with the lowest priority
   * value at the start of the list.
   */
  virtual Operationlist& getSubOperations() const { return nosubOperations; }

  SubOperation::iterator getSubOperationIterator() const {
    return SubOperation::iterator(getSubOperations());
  }

  const forward_list<OperationDependency*>& getDependencies() const {
    return dependencies;
  }

  void removeDependency(OperationDependency* d) { dependencies.remove(d); };

  void addDependency(OperationDependency*);

  Operation* getOwner() const { return owner; }

  /* Return the release fence, expressed in calendar days, of this operation. */
  Duration getFence() const { return fence; }

  /* Return the release fence, expressed in available time, of this operation.
   * The difference with the previous method is that it considers the working
   * hour and holiday calendars. */
  Date getFence(const OperationPlan* opplan) const;

  /* Update the release fence of this operation. */
  void setFence(Duration t) {
    if (fence != t) setChanged();
    fence = t;
  }

  /* Update the release fence, given a certain date.
   * This method will internally convert the date into a duration (considering
   * the available time on the operation).
   */
  void setFence(Date);

  static PyObject* setFencePython(PyObject* self, PyObject* args);

  static PyObject* getFencePython(PyObject* self, PyObject* args);

  /* Return the search mode. */
  SearchMode getSearch() const { return search; }

  /* Update the search mode. */
  void setSearch(const string a) { search = decodeSearchMode(a); }

  /* Update the search mode. */
  void setSearch(SearchMode a) { search = a; }

  virtual void updateProblems();

  void setHidden(bool b) {
    auto hidden = getHidden();
    if (hidden != b) setChanged();
    if (b)
      flags |= FLAGS_HIDDEN;
    else
      flags &= ~FLAGS_HIDDEN;
  }

  bool getHidden() const { return (flags & FLAGS_HIDDEN) != 0; }

  bool getMTO() const { return (flags & FLAGS_MTO) != 0; }

  bool getNoLocationCalendar() const {
    return (flags & FLAGS_NOLOCATIONCALENDAR) != 0;
  }

  void setNoLocationCalendar(bool b) {
    if (b)
      flags |= FLAGS_NOLOCATIONCALENDAR;
    else
      flags &= ~FLAGS_NOLOCATIONCALENDAR;
  }

  void updateMTO();

  static Operation* findFromName(string);

  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "",
                              MANDATORY);
    HasDescription::registerFields<Cls>(m);
    Plannable::registerFields<Cls>(m);
    m->addDurationField<Cls>(Tags::posttime, &Cls::getPostTime,
                             &Cls::setPostTime);
    m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
    m->addDurationField<Cls>(Tags::fence, &Cls::getFence, &Cls::setFence);
    m->addDurationField<Cls>(Tags::batchwindow, &Cls::getBatchWindow,
                             &Cls::setBatchWindow);
    m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum,
                           &Cls::setSizeMinimum, 1);
    m->addPointerField<Cls>(Tags::size_minimum_calendar,
                            &Cls::getSizeMinimumCalendar,
                            &Cls::setSizeMinimumCalendar);
    m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple,
                           &Cls::setSizeMultiple);
    m->addDoubleField<Cls>(Tags::size_maximum, &Cls::getSizeMaximum,
                           &Cls::setSizeMaximum, DBL_MAX);
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem,
                                  BASE + PLAN + WRITE_OBJECT_SVC);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority,
                        1);
    m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart,
                         &Cls::setEffectiveStart);
    m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd,
                         &Cls::setEffectiveEnd, Date::infiniteFuture);
    m->addPointerField<Cls, Calendar>(Tags::available, &Cls::getAvailable,
                                      &Cls::setAvailable);
    m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(
        Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans,
        PLAN + DETAIL + DONT_SERIALIZE_SVC);
    m->addIteratorField<Cls, loadlist::const_iterator, Load>(
        Tags::loads, Tags::load, &Cls::getLoadIterator, BASE + WRITE_OBJECT);
    m->addIteratorField<Cls, flowlist::const_iterator, Flow>(
        Tags::flows, Tags::flow, &Cls::getFlowIterator, BASE + WRITE_OBJECT);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::nolocationcalendar, &Cls::getNoLocationCalendar,
                         &Cls::setNoLocationCalendar, BOOL_FALSE, BASE);
    m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch,
                                     &Cls::setSearch, SearchMode::PRIORITY);
    m->addPointerField<Cls, Operation>(Tags::owner, &Cls::getOwner, nullptr,
                                       DONT_SERIALIZE);
    m->addIteratorField<Cls, dependencyIterator, OperationDependency>(
        Tags::dependencies, Tags::dependency, &Cls::getBlockedbyIterator,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Cls, dependencyIterator, OperationDependency>(
        Tags::blockedby, Tags::dependency, &Cls::getBlockedbyIterator,
        DONT_SERIALIZE);
    m->addIteratorField<Cls, dependencyIterator, OperationDependency>(
        Tags::blocking, Tags::dependency, &Cls::getBlockingIterator,
        DONT_SERIALIZE);
    HasLevel::registerFields<Cls>(m);
  }

  /* Empty list of operations.
   * For operation types which have no suboperations this list is
   * used as the list of suboperations.
   */
  static Operationlist nosubOperations;

 protected:
  typedef tuple<Resource*, SetupMatrixRule*, PooledString> SetupInfo;

  /* Calculate the setup time of an operationplan.
   * The date argument can either be the start or the end date
   * of a setup, depending on the value of the third argument.
   */
  SetupInfo calculateSetup(OperationPlan*, Date, SetupEvent* = nullptr,
                           SetupEvent** = nullptr) const;

 private:
  /* Parent operation. */
  Operation* owner = nullptr;

  /* A list operations that are blocking this one. */
  forward_list<OperationDependency*> dependencies;

  /* Item produced by the operation. */
  Item* item = nullptr;

  /* Location of the operation.
   * The location is used to model the working hours and holidays.
   */
  Location* loc = nullptr;

  /* Represents the time between this operation and a next one. */
  Duration post_time;

  /* Represents the release fence of this operation, i.e. a period of time
   * (relative to the current date of the plan) in which normally no
   * operationplan is allowed to be created.
   */
  Duration fence;

  /* Singly linked list of all flows of this operation. */
  flowlist flowdata;

  /* Singly linked list of all resources Loaded by this operation. */
  loadlist loaddata;

  /* Minimum size for operationplans. */
  double size_minimum = 1.0;

  /* Minimum size for operationplans when this size varies over time.
   * If this field is specified, the size_minimum field is ignored.
   */
  Calendar* size_minimum_calendar = nullptr;

  /* Multiple size for operationplans. */
  double size_multiple = 0.0;

  /* Maximum size for operationplans. */
  double size_maximum = DBL_MAX;

  /* Cost of the operation. */
  double cost = 0.0;

  /* A pointer to the first operationplan of this operation.
   * All operationplans of this operation are stored in a sorted
   * doubly linked list.
   */
  OperationPlan* first_opplan = nullptr;

  /* A pointer to the last operationplan of this operation.
   * All operationplans of this operation are stored in a sorted
   * doubly linked list.
   */
  OperationPlan* last_opplan = nullptr;

  /* A pointer to the next operation producing the item. */
  Operation* next = nullptr;

  /* Availability calendar of the operation. */
  Calendar* available = nullptr;

  /* Effectivity of the operation. */
  DateRange effectivity;

  /* Time window to scan for setup optimization and batching opportunities. */
  Duration batchwindow;

  /* Priority of the operation among alternates. */
  int priority = 1;

  /* Bit fields. */
  static const unsigned short FLAGS_HIDDEN = 1;
  static const unsigned short FLAGS_MTO = 2;
  static const unsigned short FLAGS_NOLOCATIONCALENDAR = 4;
  unsigned short flags = 0;

  /* Mode to select the preferred alternates. */
  SearchMode search = SearchMode::PRIORITY;
};

/* Writes an operationplan to an output stream. */
inline ostream& operator<<(ostream& os, const OperationPlan* o) {
  if (o) {
    os << static_cast<const void*>(o) << " (";
    if (o->getOperation())
      os << o->getOperation()->getName();
    else
      os << "nullptr";
    os << ", " << o->getQuantity() << ", " << o->getStart();
    if (o->getSetupEnd() != o->getStart()) os << " - " << o->getSetupEnd();
    os << " - " << o->getEnd();
    if (o->getBatch()) os << ", " << o->getBatch();
    if (o->getProposed())
      os << ")";
    else
      os << ", " << o->getStatus() << ", " << o->getReference() << ")";
  } else
    os << "nullptr";
  return os;
}

inline string OperationPlan::getOrderType() const {
  return oper ? oper->getOrderType() : "Unknown";
}

inline double OperationPlan::setQuantity(double f, bool roundDown, bool update,
                                         bool execute, Date end) {
  return oper ? oper->setOperationPlanQuantity(this, f, roundDown, update,
                                               execute, end)
              : f;
}

inline int OperationPlan::getCluster() const {
  return oper ? oper->getCluster() : 0;
}

Plannable* OperationPlan::getEntity() const { return oper; }

/* A class to iterator over operationplans.
 *
 * Different modes are supported:
 *   - iterate over all operationplans of a single operation.
 *   - iterate over all sub-operationplans of a single operationplan.
 *   - iterate over all operationplans.
 */
class OperationPlan::iterator {
 public:
  /* Constructor. The iterator will loop only over the operationplans
   * of the operation passed. */
  iterator(const Operation* x, bool forward = true)
      : op(Operation::end()), mode(forward ? 1 : 4) {
    if (!x)
      opplan = nullptr;
    else if (forward)
      opplan = x->getFirstOpPlan();
    else
      opplan = x->getLastOpPlan();
  }

  /* Constructor. The iterator will loop only over the suboperationplans
   * of the operationplan passed. */
  iterator(const OperationPlan* x) : op(Operation::end()), mode(2) {
    opplan = x ? x->firstsubopplan : nullptr;
  }

  /* Constructor. The iterator will loop over all operationplans. */
  iterator() : op(Operation::begin()), mode(3) {
    // The while loop is required since the first operation might not
    // have any operationplans at all
    while (op != Operation::end()) {
      if (op->getFirstOpPlan()) {
        opplan = op->getFirstOpPlan();
        return;
      }
      ++op;
    }
    opplan = nullptr;
  }

  /* Copy constructor. */
  iterator(const iterator& it) : opplan(it.opplan), op(it.op), mode(it.mode) {}

  /* Copy assignment operator. */
  iterator& operator=(const iterator& it) {
    opplan = it.opplan;
    op = it.op;
    mode = it.mode;
    return *this;
  }

  /* Return the content of the current node. */
  OperationPlan& operator*() const { return *opplan; }

  /* Return the content of the current node. */
  OperationPlan* operator->() const { return opplan; }

  /* Pre-increment operator which moves the pointer to the next
   * element. */
  iterator& operator++() {
    if (opplan) {
      if (mode == 2)
        opplan = opplan->nextsubopplan;
      else if (mode == 4)
        opplan = opplan->prev;
      else
        opplan = opplan->next;
    }
    // Move to a new operation
    if (!opplan && mode == 3) {
      while (op != Operation::end()) {
        ++op;
        if (op->getFirstOpPlan()) break;
      }
      opplan = (op == Operation::end() ? nullptr : op->getFirstOpPlan());
    }
    return *this;
  }

  /* Post-increment operator which moves the pointer to the next
   * element. */
  iterator operator++(int) {
    iterator tmp(*this);
    if (mode == 2)
      opplan = opplan->nextsubopplan;
    else if (mode == 4)
      opplan = opplan->prev;
    else
      opplan = opplan->next;
    // Move to a new operation
    if (!opplan && mode == 3) {
      while (op != Operation::end()) {
        ++op;
        if (op->getFirstOpPlan()) break;
      }
      opplan = (op == Operation::end() ? nullptr : op->getFirstOpPlan());
    }
    return tmp;
  }

  /* Return current element and advance the iterator. */
  OperationPlan* next() {
    OperationPlan* tmp = opplan;
    operator++();
    return tmp;
  }

  /* Comparison operator. */
  bool operator==(const iterator& y) const { return opplan == y.opplan; }

  /* Inequality operator. */
  bool operator!=(const iterator& y) const { return opplan != y.opplan; }

 private:
  /* A pointer to current operationplan. */
  OperationPlan* opplan;

  /* An iterator over the operations. */
  Operation::iterator op;

  /* Describes the type of iterator.
   * 1) iterate over operationplan instances of operation
   * 2) iterate over suboperationplans of an operationplan
   * 3) iterate over all operationplans
   * 4) iterate over operationplan instances of operation, same as 1 but
   * backward in time
   */
  short mode;
};

inline OperationPlan::iterator OperationPlan::end() {
  return iterator(static_cast<Operation*>(nullptr));
}

inline OperationPlan::iterator OperationPlan::begin() { return iterator(); }

inline OperationPlan::iterator OperationPlan::getSubOperationPlans() const {
  return OperationPlan::iterator(this);
}

/* A simple class to easily remember the date, quantity, setup and owner
 * of an operationplan.
 */
class OperationPlanState  // @todo should also be able to remember and restore
                          // suboperationplans, loadplans and flowplans!!!
{
 public:
  Date start;
  Date end;
  SetupEvent setup;
  TimeLine<LoadPlan>* tmline = nullptr;
  double quantity = 0.0;

  /* Default constructor. */
  OperationPlanState() { setup.stateinfo = true; }

  /* Constructor. */
  OperationPlanState(const OperationPlan* x) : setup(x->getSetupEvent()) {
    if (!x) return;
    start = x->getStart();
    end = x->getEnd();
    quantity = x->getQuantity();
    setup.stateinfo = true;
    tmline = x->getSetupEvent() ? x->getSetupEvent()->getTimeLine() : nullptr;
  }

  /* Copy constructor. */
  OperationPlanState(const OperationPlanState& x)
      : start(x.start),
        end(x.end),
        setup(x.setup),
        tmline(x.tmline),
        quantity(x.quantity) {
    setup.stateinfo = true;
  }

  /* Constructor. */
  OperationPlanState(const Date x, const Date y, double q,
                     SetupEvent* z = nullptr)
      : start(x), end(y), setup(z), quantity(q) {
    if (z) tmline = z->getTimeLine();
    setup.stateinfo = true;
  }

  /* Constructor. */
  OperationPlanState(const DateRange& x, double q, SetupEvent* z = nullptr)
      : start(x.getStart()), end(x.getEnd()), setup(z), quantity(q) {
    if (z) tmline = z->getTimeLine();
    setup.stateinfo = true;
  }

  /* Assignment operator. */
  OperationPlanState& operator=(const OperationPlanState& other) {
    start = other.start;
    end = other.end;
    setup = other.setup;
    quantity = other.quantity;
    tmline = other.tmline;
    setup.stateinfo = true;
    return *this;
  }
};

inline OperationPlanState OperationPlan::setOperationPlanParameters(
    double qty, Date startdate, Date enddate, bool preferEnd, bool execute,
    bool roundDown, bool later) {
  return getOperation()->setOperationPlanParameters(
      this, qty, startdate, enddate, preferEnd, execute, roundDown, later);
}

/* Models an operation that takes a fixed amount of time, independent
 * of the quantity. */
class OperationFixedTime : public Operation {
 public:
  /* Default constructor. */
  explicit OperationFixedTime() { initType(metadata); }

  /* Returns the length of the operation. */
  Duration getDuration() const { return duration; }

  /* Updates the duration of the operation. Existing operation plans of this
   * operation are not automatically refreshed to reflect the change. */
  void setDuration(Duration t) {
    if (t < 0L)
      logger << "Warning: FixedTime operation can't have a negative duration"
             << endl;
    else
      duration = t;
  }

  /* Return the decoupled lead time of this operation. */
  virtual pair<Duration, Date> getDecoupledLeadTime(double, Date) const;

  static int initialize();

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  /* A operation of this type enforces the following rules on its
   * operationplans:
   *  - The duration is always constant.
   *  - If the end date is specified, we use that and ignore the start
   *    date that could have been passed.
   *  - If no end date but only a start date are specified, we'll use
   *    that date.
   *  - If no dates are specified, we don't update the dates of the
   *    operationplan.
   *  - The quantity can be any positive number.
   *  - Locked operationplans can't be updated.
   * @see Operation::setOperationPlanParameters
   */
  OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd = true, bool execute = true, bool roundDown = true,
      bool later = false) const;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDurationField<Cls>(Tags::duration, &Cls::getDuration,
                             &Cls::setDuration);
  }

 protected:
  virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true,
                                bool use_start = false);

 private:
  /* Stores the lengh of the Operation. */
  Duration duration;
};

/* Models an operation whose duration is the sum of a constant time,
 * plus a certain time per unit.
 */
class OperationTimePer : public Operation {
 public:
  /* Default constructor. */
  explicit OperationTimePer() : duration_per(0.0) { initType(metadata); }

  /* Returns the constant part of the operation time. */
  Duration getDuration() const { return duration; }

  /* Sets the constant part of the operation time. */
  void setDuration(Duration t) {
    if (t < 0L)
      logger << "Warning: TimePer operation can't have a negative duration"
             << endl;
    else
      duration = t;
  }

  /* Returns the time per unit of the operation time. */
  double getDurationPer() const { return duration_per; }

  /* Sets the time per unit of the operation time. */
  void setDurationPer(double t) {
    if (t < 0.0)
      logger << "Warning: TimePer operation can't have a negative duration-per"
             << endl;
    else
      duration_per = t;
  }

  /* A operation of this type enforces the following rules on its
   * operationplans:
   *   - If both the start and end date are specified, the quantity is
   *     computed to match these dates.
   *     If the time difference between the start and end date is too
   *     small to fit the fixed duration, the quantity is set to 0.
   *   - If only an end date is specified, it will be respected and we
   *     compute a start date based on the quantity.
   *   - If only a start date is specified, it will be respected and we
   *     compute an end date based on the quantity.
   *   - If no date is specified, we respect the quantity and the end
   *     date of the operation. A new start date is being computed.
   *
   * Tricky situations can arise when the minimum size is varying over
   * time, ie min_size_calendar field is used.
   *
   * @see Operation::setOperationPlanParameters
   */
  OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd = true, bool execute = true, bool roundDown = true,
      bool later = false) const;

  /* Return the decoupled lead time of this operation. */
  virtual pair<Duration, Date> getDecoupledLeadTime(double, Date) const;

  static int initialize();

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDurationField<Cls>(Tags::duration, &Cls::getDuration,
                             &Cls::setDuration);
    m->addDurationDoubleField<Cls>(Tags::duration_per, &Cls::getDurationPer,
                                   &Cls::setDurationPer);
  }

 private:
  /* Constant part of the operation time. */
  Duration duration;

  /* Variable part of the operation time.
   * We store the value as a double value rather than a Duration to
   * be able to store fractional duration_per value. Duration can only
   * represent seconds.
   */
  double duration_per;
};

/* Represents a routing operation, i.e. an operation consisting of
 * multiple, sequential sub-operations.
 */
class OperationRouting : public Operation {
 public:
  /* Default constructor. */
  explicit OperationRouting() { initType(metadata); }

  /* Destructor. */
  ~OperationRouting();

  virtual bool hasSubOperations() const { return true; }

  /* Returns the minimum maxearly of any load. */
  virtual Duration getMaxEarly() const;

  bool getHardPostTime() const { return hardposttime; }

  void setHardPostTime(bool b) { hardposttime = b; }

  // Check whether to plan based on dependencies or priority.
  // If we find a single step-to-step dependency in the routing, we will
  // plan the complete routing using the dependencies.
  bool useDependencies() const;

  /* A operation of this type enforces the following rules on its
   * operationplans:
   *  - If an end date is given, sequentially use this method on the
   *    different steps. The steps are stepped through starting from the
   *    last step, and each step will adjust to meet the requested end date.
   *    If there is slack between the routings' step operationplans, it can
   *    be used to "absorb" the change.
   *  - When a start date is given, the behavior is similar to the previous
   *    case, except that we step through the operationplans from the
   *    first step this time.
   *  - If both a start and an end date are given, we use only the end date.
   *  - If there are no sub operationplans yet, apply the requested changes
   *    blindly.
   * @see Operation::setOperationPlanParameters
   */
  OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd = true, bool execute = true, bool roundDown = true,
      bool later = false) const;

  double setOperationPlanQuantity(OperationPlan* oplan, double f,
                                  bool roundDown, bool upd, bool execute,
                                  Date end) const;

  /* Add a new child operationplan.
   * When the third argument is true, we don't validate the insertion and just
   * insert it at the front of the unlocked operationplans.
   * When the third argument is false, we do a full validation. This means:
   * - The operation must be present in the routing
   * - An existing suboperationplan of the same operation is replaced with the
   *   the new child.
   * - The dates of subsequent suboperationplans in the routing are updated
   *   to start after the newly inserted one (except for confirmed
   * operationplans) that can't be touched.
   */
  virtual void addSubOperationPlan(OperationPlan*, OperationPlan*, bool = true);

  /* Return the decoupled lead time of this operation. */
  virtual pair<Duration, Date> getDecoupledLeadTime(double, Date) const;

  static int initialize();

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  /* Return a list of all sub-operations. */
  virtual Operationlist& getSubOperations() const {
    return const_cast<Operationlist&>(steps);
  }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(
        Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator,
        BASE + WRITE_OBJECT);
    m->addBoolField<Cls>(Tags::hard_posttime, &Cls::getHardPostTime,
                         &Cls::setHardPostTime, BOOL_FALSE, BASE);
  }

  /* Return the memory size. */
  virtual size_t getSize() const {
    size_t tmp = Operation::getSize();
    // Add the memory for the steps: 3 pointers per step
    tmp += steps.size() * 3 * sizeof(Operation*);
    return tmp;
  }

 protected:
  /* Extra logic to be used when instantiating an operationplan. */
  virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true,
                                bool use_start = false);

 private:
  /* Stores a double linked list of all step suboperations. */
  Operationlist steps;

  bool hardposttime = false;
};

/* This class represents a split between multiple operations. */
class OperationSplit : public Operation {
 public:
  /* Default constructor. */
  explicit OperationSplit() { initType(metadata); }

  /* Destructor. */
  ~OperationSplit();

  virtual bool hasSubOperations() const { return true; }

  /* Returns the minimum maxearly of any load. */
  virtual Duration getMaxEarly() const;

  /* A operation of this type enforces the following rules on its
   * operationplans:
   *  - Very simple, accept any value. Ignore any lot size constraints
   *    since we use the ones on the sub operationplans.
   * @see Operation::setOperationPlanParameters
   */
  OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd = true, bool execute = true, bool roundDown = true,
      bool later = false) const;

  /* Add a new child operationplan.
   * An alternate operationplan plan can have a maximum of 2
   * suboperationplans:
   *  - A setup operationplan if the alternate top-operation loads a
   *    resource requiring a specific setup.
   *  - An operationplan of any of the allowed suboperations.
   */
  virtual void addSubOperationPlan(OperationPlan*, OperationPlan*, bool = true);

  /* Return the decoupled lead time of this operation.
   * Take the lead time of the longest operation.
   */
  virtual pair<Duration, Date> getDecoupledLeadTime(double, Date) const;

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual Operationlist& getSubOperations() const {
    return const_cast<Operationlist&>(alternates);
  }

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(
        Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator,
        BASE + WRITE_OBJECT);
  }

  /* Return the memory size. */
  virtual size_t getSize() const {
    size_t tmp = Operation::getSize();
    // Add the memory for the suboperation list: 3 pointers per alternates
    tmp += alternates.size() * 3 * sizeof(Operation*);
    return tmp;
  }

 protected:
  /* Extra logic to be used when instantiating an operationplan. */
  virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true,
                                bool use_start = false);

 private:
  /* List of all alternate operations. */
  Operationlist alternates;
};

/* This class represents a choice between multiple operations. The
 * alternates are sorted in order of priority.
 */
class OperationAlternate : public Operation {
 public:
  /* Default constructor. */
  explicit OperationAlternate() { initType(metadata); }

  /* Destructor. */
  ~OperationAlternate();

  virtual bool hasSubOperations() const { return true; }

  /* Returns the minimum maxearly of any load. */
  virtual Duration getMaxEarly() const;

  virtual string getOrderType() const { return "ALT"; }

  /* A operation of this type enforces the following rules on its
   * operationplans:
   *  - Very simple, call the method with the same name on the alternate
   *    suboperationplan.
   * @see Operation::setOperationPlanParameters
   */
  OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd = true, bool execute = true, bool roundDown = true,
      bool later = false) const;

  /* Add a new child operationplan.
   * An alternate operationplan plan can have a maximum of 2
   * suboperationplans:
   *  - A setup operationplan if the alternate top-operation loads a
   *    resource requiring a specific setup.
   *  - An operationplan of any of the allowed suboperations.
   */
  virtual void addSubOperationPlan(OperationPlan*, OperationPlan*, bool = true);

  /* Return the decoupled lead time of this operation:
   * Take the lead time of the preferred operation
   */
  virtual pair<Duration, Date> getDecoupledLeadTime(double, Date) const;

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual Operationlist& getSubOperations() const {
    return const_cast<Operationlist&>(alternates);
  }

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(
        Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator,
        BASE + WRITE_OBJECT);
  }

  /* Return the memory size. */
  virtual size_t getSize() const {
    size_t tmp = Operation::getSize();
    // Add the memory for the suboperation list: 3 pointers per alternates
    tmp += alternates.size() * 3 * sizeof(Operation*);
    return tmp;
  }

 protected:
  /* Extra logic to be used when instantiating an operationplan. */
  virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true,
                                bool use_start = false);

 private:
  /* List of all alternate operations. */
  Operationlist alternates;
};

/* A class to iterato over alternates of an operationplan. */
class OperationPlan::AlternateIterator {
 private:
  const OperationPlan* opplan = nullptr;
  vector<Operation*> opers;
  vector<Operation*>::iterator operIter;

 public:
  AlternateIterator(const OperationPlan* o);

  /* Copy constructor. */
  AlternateIterator(const AlternateIterator& other) : opplan(other.opplan) {
    for (auto i = other.opers.begin(); i != other.opers.end(); ++i)
      opers.push_back(*i);
    operIter = opers.begin();
  }

  /* Copy assignment operator. */
  AlternateIterator& operator=(const AlternateIterator& other) {
    opplan = other.opplan;
    opers.clear();
    for (auto i = other.opers.begin(); i != other.opers.end(); ++i)
      opers.push_back(*i);
    operIter = opers.begin();
    return *this;
  }

  Operation* next();
};

inline OperationPlan::AlternateIterator OperationPlan::getAlternates() const {
  return OperationPlan::AlternateIterator(this);
}

/* This class holds the definition of distribution replenishments. */
class ItemDistribution
    : public Object,
      public Association<Location, Item, ItemDistribution>::Node,
      public HasSource {
  friend class OperationItemDistribution;
  friend class Item;

 public:
  class OperationIterator {
   private:
    OperationItemDistribution* curOper;

   public:
    /* Constructor. */
    OperationIterator(const ItemDistribution* i) {
      curOper = i ? i->firstOperation : nullptr;
    }

    /* Return current value and advance the iterator. */
    inline OperationItemDistribution* next();
  };

  /* Factory method. */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  /* Constructor. */
  explicit ItemDistribution();

  /* Destructor. */
  virtual ~ItemDistribution();

  /* Search an existing object. */
  static Object* finder(const DataValueDict& k);

  /* Remove all shipping operationplans. */
  void deleteOperationPlans(bool deleteLockedOpplans = false);

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static const MetaCategory* metacategory;

  /* Returns the item. */
  Item* getItem() const { return getPtrB(); }

  /* Update the item. */
  void setItem(Item*);

  /* Returns the origin location. */
  Location* getOrigin() const { return orig; }

  /* Returns the destination location. */
  Location* getDestination() const { return getPtrA(); }

  /* Updates the origin Location. This method can only be called once on each
   * instance. */
  void setOrigin(Location* s) {
    if (!s) return;
    if (getDestination() == s)
      throw LogicException(
          "Source and destination of an ItemDistribution must be different");
    orig = s;
    HasLevel::triggerLazyRecomputation();
  }

  /* Updates the destination location. This method can only be called once on
   * each instance. */
  void setDestination(Location* i) {
    if (!i) return;
    if (getOrigin() == i)
      throw LogicException(
          "Source and destination of an ItemDistribution must be different");
    setPtrA(i, i->getDistributions());
    HasLevel::triggerLazyRecomputation();
  }

  Duration getBatchWindow() const { return batchwindow; }

  void setBatchWindow(Duration d) {
    // todo: also update the batchwindow of the existing
    // operationitemdistributions
    batchwindow = d;
  }

  /* Update the resource representing the supplier capacity. */
  void setResource(Resource* r) {
    res = r;
    HasLevel::triggerLazyRecomputation();
  }

  /* Return the resource representing the distribution capacity. */
  Resource* getResource() const { return res; }

  /* Update the resource capacity used per distributed unit. */
  void setResourceQuantity(double d) {
    if (d < 0)
      logger << "Warning: Resource_quantity must be positive" << endl;
    else
      res_qty = d;
  }

  /* Return the resource capacity used per distributed unit. */
  double getResourceQuantity() const { return res_qty; }

  /* Return the purchasing leadtime. */
  Duration getLeadTime() const { return leadtime; }

  /* Update the shipping lead time.
   * Note that any already existing purchase operations and their
   * operationplans are NOT updated.
   */
  void setLeadTime(Duration p) {
    if (p < 0L)
      logger << "Warning: ItemDistribution can't have a negative lead time"
             << endl;
    else
      leadtime = p;
  }

  /* Sets the minimum size for shipments.
   * The default value is 1.0
   */
  void setSizeMinimum(double f) {
    if (f < 0)
      logger << "Warning: ItemDistribution can't have a negative minimum size"
             << endl;
    else
      size_minimum = f;
  }

  /* Returns the minimum size for shipments. */
  double getSizeMinimum() const { return size_minimum; }

  /* Sets the multiple size for shipments. */
  void setSizeMultiple(double f) {
    if (f < 0)
      logger << "Warning: ItemDistribution can't have a negative multiple size"
             << endl;
    else
      size_multiple = f;
  }

  /* Returns the mutiple size for shipments. */
  double getSizeMultiple() const { return size_multiple; }

  /* Sets the maximum size for shipments. */
  void setSizeMaximum(double f) {
    if (f < size_minimum)
      logger << "Warning: ItemDistribution maximum size must be higher than "
                "the minimum size"
             << endl;
    else if (f < 0)
      logger << "Warning: ItemDistribution can't have a negative maximum size"
             << endl;
    else
      size_maximum = f;
  }

  /* Returns the mutiple size for shipments. */
  double getSizeMaximum() const { return size_maximum; }

  /* Returns the cost of shipping 1 unit of this item.
   * The default value is 0.0.
   */
  double getCost() const { return cost; }

  /* Update the cost of shipping 1 unit. */
  void setCost(const double c) { cost = max(c, 0.0); }

  OperationIterator getOperations() const { return OperationIterator(this); }

  Duration getFence() const { return fence; }

  void setFence(Duration d) { fence = d; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem,
                                  MANDATORY + PARENT);
    m->addPointerField<Cls, Location>(Tags::origin, &Cls::getOrigin,
                                      &Cls::setOrigin);
    m->addPointerField<Cls, Location>(Tags::destination, &Cls::getDestination,
                                      &Cls::setDestination, BASE + PARENT);
    m->addDurationField<Cls>(Tags::leadtime, &Cls::getLeadTime,
                             &Cls::setLeadTime);
    m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum,
                           &Cls::setSizeMinimum, 1.0);
    m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple,
                           &Cls::setSizeMultiple, 1.0);
    m->addDoubleField<Cls>(Tags::size_maximum, &Cls::getSizeMaximum,
                           &Cls::setSizeMaximum, DBL_MAX);
    m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority,
                        1);
    m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart,
                         &Cls::setEffectiveStart);
    m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd,
                         &Cls::setEffectiveEnd, Date::infiniteFuture);
    m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource,
                                      &Cls::setResource);
    m->addDoubleField<Cls>(Tags::resource_qty, &Cls::getResourceQuantity,
                           &Cls::setResourceQuantity, 1.0);
    m->addDurationField<Cls>(Tags::fence, &Cls::getFence, &Cls::setFence);
    m->addDurationField<Cls>(Tags::batchwindow, &Cls::getBatchWindow,
                             &Cls::setBatchWindow);
    m->addIteratorField<Cls, OperationIterator, OperationItemDistribution>(
        Tags::operations, Tags::operation, &Cls::getOperations, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    HasSource::registerFields<Cls>(m);
  }

 private:
  /* Source location. */
  Location* orig = nullptr;

  /* Shipping lead time. */
  Duration leadtime;

  /* Minimum procurement quantity. */
  double size_minimum = 1.0;

  /* Procurement multiple quantity. */
  double size_multiple = 1.0;

  /* Procurement maximum quantity. */
  double size_maximum = DBL_MAX;

  /* Procurement cost. */
  double cost = 0.0;

  /* Pointer to the head of the auto-generated shipping operation list.*/
  OperationItemDistribution* firstOperation = nullptr;

  /* Resource to model distribution capacity. */
  Resource* res = nullptr;

  /* Consumption on the distribution capacity resource. */
  double res_qty = 1.0;

  /* Release fence for the distribution operation. */
  Duration fence;

  Duration batchwindow;
};

/* An item defines the products being planned, sold, stored and/or
 * manufactured. Buffers and demands have a reference an item.
 *
 * This is an abstract class.
 */
class Item : public HasHierarchy<Item>, public HasDescription {
  friend class Buffer;
  friend class ItemSupplier;
  friend class ItemDistribution;
  friend class Demand;
  friend class Operation;

 public:
  class bufferIterator;
  friend class bufferIterator;

  class demandIterator;
  friend class demandIterator;

  typedef Association<Supplier, Item, ItemSupplier>::ListB supplierlist;
  typedef Association<Location, Item, ItemDistribution>::ListB distributionlist;

  /* Default constructor. */
  explicit Item() {}

  /* Return the cost of the item.
   * The default value is 0.0.
   */
  double getCost() const { return cost; }

  /* Update the cost of the item. */
  void setCost(const double c) { cost = max(c, 0.0); }

  /* Return the weight of the item.
   * The default value is 0.0.
   */
  double getWeight() const { return weight; }

  /* Update the weight of the item. */
  void setWeight(const double w) {
    if (w >= 0)
      weight = w;
    else
      logger << "Warning: Item weight must be positive" << endl;
  }

  /* Return the volume of the item.
   * The default value is 0.0.
   */
  double getVolume() const { return volume; }

  /* Update the volume of the item. */
  void setVolume(const double v) {
    if (v >= 0)
      volume = v;
    else
      logger << "Warning: Item volume must be positive" << endl;
  }

  /* Returns the unit of measure. */
  PooledString getUOM() const { return uom; }

  const string& getUOMString() const { return uom; }

  /* Sets the uom field. */
  void setUOM(const PooledString& u) { uom = u; }

  void setUOM(const string& u) { uom = u; }

  /* Returns a constant reference to the list of items this supplier can
   * deliver. */
  const supplierlist& getSuppliers() const { return suppliers; }

  /* Returns an iterator over the list of items this supplier can deliver. */
  supplierlist::const_iterator getSupplierIterator() const {
    return suppliers.begin();
  }

  const distributionlist& getDistributions() const { return distributions; }

  distributionlist::const_iterator getDistributionIterator() const {
    return distributions.begin();
  }

  /* Nested class to iterate of Operation objects producing this item. */
  class operationIterator {
   private:
    Operation* cur;

   public:
    /* Constructor. */
    operationIterator(const Item* c) { cur = c ? c->firstOperation : nullptr; }

    /* Return current value and advance the iterator. */
    Operation* next() {
      Operation* tmp = cur;
      if (cur) cur = cur->next;
      return tmp;
    }
  };

  operationIterator getOperationIterator() const { return this; }

  // Return an iterator over all buffers of this item
  inline bufferIterator getBufferIterator() const;

  // Return an iterator over all demands of this item
  inline demandIterator getDemandIterator() const;

  static int initialize();

  /* Return the receipt date of the earliest proposed purchase
   * order for this item.
   * When none is found, the function returns Date::InfiniteFuture
   */
  Date findEarliestPurchaseOrder(const PooledString&) const;

  /* Return the cluster of this item. */
  int getCluster() const;

  /* Destructor. */
  virtual ~Item();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    HasHierarchy<Cls>::template registerFields<Cls>(m);
    HasDescription::registerFields<Cls>(m);
    m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost, 0);
    m->addDoubleField<Cls>(Tags::volume, &Cls::getVolume, &Cls::setVolume, 0);
    m->addDoubleField<Cls>(Tags::weight, &Cls::getWeight, &Cls::setWeight, 0);
    m->addStringRefField<Cls>(Tags::uom, &Cls::getUOMString, &Cls::setUOM);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addIteratorField<Cls, supplierlist::const_iterator, ItemSupplier>(
        Tags::itemsuppliers, Tags::itemsupplier, &Cls::getSupplierIterator,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Cls, distributionlist::const_iterator,
                        ItemDistribution>(
        Tags::itemdistributions, Tags::itemdistribution,
        &Cls::getDistributionIterator, BASE + WRITE_OBJECT);
    m->addIteratorField<Cls, operationIterator, Operation>(
        Tags::operations, Tags::operation, &Cls::getOperationIterator,
        DONT_SERIALIZE);
    m->addIteratorField<Cls, bufferIterator, Buffer>(
        Tags::buffers, Tags::buffer, &Cls::getBufferIterator, DONT_SERIALIZE);
    m->addIteratorField<Cls, demandIterator, Demand>(
        Tags::demands, Tags::demand, &Cls::getDemandIterator, DONT_SERIALIZE);
    m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0,
                        DONT_SERIALIZE);
  }

 private:
  /* This is the operation used to satisfy a demand for this item.
   * @see Demand
   */
  Operation* deliveryOperation = nullptr;

  /* Cost of the item. */
  double cost = 0.0;

  /* Volume of the item. */
  double volume = 0.0;

  /* Weight of the item. */
  double weight = 0.0;

  /* uom of the item. */
  PooledString uom;

  /* This is a list of suppliers this item has. */
  supplierlist suppliers;

  /* This is the list of itemdistributions of this item. */
  distributionlist distributions;

  /* Maintain a list of buffers. */
  Buffer* firstItemBuffer = nullptr;

  /* Maintain a list of demands. */
  Demand* firstItemDemand = nullptr;

  /* Maintain a list of operations producing this item. */
  Operation* firstOperation = nullptr;
};

/* This class is the default implementation of the abstract Item
 * class. */
class ItemMTS : public Item {
 public:
  /* Default constructor. */
  explicit ItemMTS() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class is the default implementation of the abstract Item
 * class. */
class ItemMTO : public Item {
 public:
  /* Default constructor. */
  explicit ItemMTO() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class represents an item that can be purchased from a supplier.
 */
class ItemSupplier : public Object,
                     public Association<Supplier, Item, ItemSupplier>::Node,
                     public HasSource {
  friend class OperationItemSupplier;

 public:
  /* Default constructor. */
  explicit ItemSupplier();

  /* Constructor. */
  explicit ItemSupplier(Supplier*, Item*, int);

  /* Constructor. */
  explicit ItemSupplier(Supplier*, Item*, int, DateRange);

  /* Destructor. */
  ~ItemSupplier();

  /* Search an existing object. */
  static Object* finder(const DataValueDict&);

  /* Initialize the class. */
  static int initialize();

  /* Returns the supplier. */
  Supplier* getSupplier() const { return getPtrA(); }

  /* Returns the item. */
  Item* getItem() const { return getPtrB(); }

  /* Updates the supplier. This method can only be called on an instance. */
  void setSupplier(Supplier* s) {
    if (s) setPtrA(s, s->getItems());
    HasLevel::triggerLazyRecomputation();
  }

  /* Updates the item. This method can only be called on an instance. */
  void setItem(Item* i) {
    if (i) setPtrB(i, i->getSuppliers());
    HasLevel::triggerLazyRecomputation();
  }

  /* Sets the minimum size for procurements.
   * The default value is 1.0
   */
  void setSizeMinimum(double f) {
    if (f < 0)
      logger << "Warning: ItemSupplier can't have a negative minimum size"
             << endl;
    else
      size_minimum = f;
  }

  /* Returns the minimum size for procurements. */
  double getSizeMinimum() const { return size_minimum; }

  /* Sets the multiple size for procurements. */
  void setSizeMultiple(double f) {
    if (f < 0)
      logger << "Warning: ItemSupplier can't have a negative multiple size"
             << endl;
    else
      size_multiple = f;
  }

  /* Returns the mutiple size for procurements. */
  double getSizeMultiple() const { return size_multiple; }

  /* Sets the maximum size for procurements. */
  void setSizeMaximum(double f) {
    if (f < size_minimum)
      logger << "Warning: ItemSupplier maximum size must be higher than the "
                "minimum size"
             << endl;
    else if (f < 0)
      logger << "Warning: ItemSupplier can't have a negative maximum size"
             << endl;
    else
      size_maximum = f;
  }

  /* Returns the maximum size for procurements. */
  double getSizeMaximum() const { return size_maximum; }

  /* Returns the cost of purchasing 1 unit of this item from this supplier.
   * The default value is 0.0.
   */
  double getCost() const { return cost; }

  /* Update the cost of purchasing 1 unit. */
  void setCost(const double c) { cost = max(c, 0.0); }

  Duration getBatchWindow() const { return batchwindow; }

  void setBatchWindow(Duration d) {
    // todo: also update the batchwindow of the existing operationitemsuppliers
    batchwindow = d;
  }

  Duration getExtraSafetyLeadTime() const { return extra_safety_leadtime; }

  void setExtraSafetyLeadTime(Duration d) { extra_safety_leadtime = d; }

  Duration getHardSafetyLeadTime() const { return hard_safety_leadtime; }

  void setHardSafetyLeadTime(Duration d) { hard_safety_leadtime = d; }

  /* Return the applicable location. */
  Location* getLocation() const { return loc; }

  /* Update the applicable locations.
   * Note that any already existing purchase operations and their
   * operationplans are NOT updated.
   */
  void setLocation(Location* l) { loc = l; }

  /* Update the resource representing the supplier capacity. */
  void setResource(Resource* r) {
    res = r;
    HasLevel::triggerLazyRecomputation();
  }

  /* Return the resource representing the supplier capacity. */
  Resource* getResource() const { return res; }

  /* Update the resource capacity used per purchased unit. */
  void setResourceQuantity(double d) {
    if (d < 0)
      logger << "Warning: Resource_quantity must be positive" << endl;
    else
      res_qty = d;
  }

  /* Return the resource capacity used per purchased unit. */
  double getResourceQuantity() const { return res_qty; }

  Duration getFence() const { return fence; }

  void setFence(Duration d) { fence = d; }

  /* Return the purchasing lead time. */
  Duration getLeadTime() const { return leadtime; }

  /* Update the procurement lead time.
   * Note that any already existing purchase operations and their
   * operationplans are NOT updated.
   */
  void setLeadTime(Duration p) {
    if (p < 0L)
      logger << "Warning: ItemSupplier can't have a negative lead time" << endl;
    else
      leadtime = p;
  }

  /* Remove all purchasing operationplans. */
  void deleteOperationPlans(bool deleteLockedOpplans = false);

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static const MetaCategory* metacategory;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Supplier>(Tags::supplier, &Cls::getSupplier,
                                      &Cls::setSupplier, MANDATORY + PARENT);
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem,
                                  MANDATORY + PARENT);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation);
    m->addDurationField<Cls>(Tags::leadtime, &Cls::getLeadTime,
                             &Cls::setLeadTime);
    m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum,
                           &Cls::setSizeMinimum, 1.0);
    m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple,
                           &Cls::setSizeMultiple, 1.0);
    m->addDurationField<Cls>(Tags::batchwindow, &Cls::getBatchWindow,
                             &Cls::setBatchWindow);
    m->addDurationField<Cls>(Tags::extra_safety_leadtime,
                             &Cls::getExtraSafetyLeadTime,
                             &Cls::setExtraSafetyLeadTime);
    m->addDurationField<Cls>(Tags::hard_safety_leadtime,
                             &Cls::getHardSafetyLeadTime,
                             &Cls::setHardSafetyLeadTime);
    m->addDoubleField<Cls>(Tags::size_maximum, &Cls::getSizeMaximum,
                           &Cls::setSizeMaximum, DBL_MAX);
    m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority,
                        1);
    m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart,
                         &Cls::setEffectiveStart);
    m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd,
                         &Cls::setEffectiveEnd, Date::infiniteFuture);
    m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource,
                                      &Cls::setResource);
    m->addDoubleField<Cls>(Tags::resource_qty, &Cls::getResourceQuantity,
                           &Cls::setResourceQuantity, 1.0);
    m->addDurationField<Cls>(Tags::fence, &Cls::getFence, &Cls::setFence);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    HasSource::registerFields<Cls>(m);
  }

 private:
  /* Factory method. */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  /* Location where the supplier item applies to. */
  Location* loc = nullptr;

  /* Procurement lead time. */
  Duration leadtime;

  /* Minimum procurement quantity. */
  double size_minimum = 1.0;

  /* Procurement multiple quantity. */
  double size_multiple = 1.0;

  /* Procurement multiple quantity. */
  double size_maximum = DBL_MAX;

  /* Procurement cost. */
  double cost = 0.0;

  Duration batchwindow;

  Duration hard_safety_leadtime;

  Duration extra_safety_leadtime;

  /* Pointer to the head of the auto-generated purchase operation list.*/
  OperationItemSupplier* firstOperation = nullptr;

  /* Resource to model supplier capacity. */
  Resource* res = nullptr;

  /* Consumption on the supplier capacity resource. */
  double res_qty = 1.0;

  /* Release fence for the purchasing operation. */
  Duration fence;
};

/* An internally generated operation that ships material from an
 * origin location to a destinationLocation.
 */
class OperationItemDistribution : public OperationFixedTime {
  friend class ItemDistribution;

 private:
  /* Pointer to the ItemDistribution that 'owns' this operation. */
  ItemDistribution* itemdist;

  /* Pointer to the next operation of the supplier item. */
  OperationItemDistribution* nextOperation;

 public:
  ItemDistribution* getItemDistribution() const { return itemdist; }

  virtual string getOrderType() const { return "DO"; }

  Buffer* getOrigin() const;

  Buffer* getDestination() const;

  static Operation* findOrCreate(ItemDistribution*, Buffer*, Buffer*);

  /* Constructor. */
  explicit OperationItemDistribution(ItemDistribution*, Buffer*, Buffer*);

  /* Destructor. */
  virtual ~OperationItemDistribution();

  static int initialize();

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, ItemDistribution>(
        Tags::itemdistribution, &Cls::getItemDistribution, nullptr);
    m->addPointerField<Cls, Buffer>(Tags::origin, &Cls::getOrigin, nullptr,
                                    MANDATORY);
    m->addPointerField<Cls, Buffer>(Tags::destination, &Cls::getDestination,
                                    nullptr, MANDATORY);
  }

  /* Scan and trim operationplans creating excess inventory in the
   * buffer.
   */
  void trimExcess() const;
};

OperationItemDistribution* ItemDistribution::OperationIterator::next() {
  OperationItemDistribution* tmp = curOper;
  if (curOper) curOper = curOper->nextOperation;
  return tmp;
}

/* An internally generated operation that supplies procured material
 * into a buffer.
 */
class OperationItemSupplier : public OperationFixedTime {
  friend class ItemSupplier;

 private:
  /* Pointer to the ItemSupplier that 'owns' this operation. */
  ItemSupplier* supitem;

  /* Pointer to the next operation of the ItemSupplier. */
  OperationItemSupplier* nextOperation;

 public:
  ItemSupplier* getItemSupplier() const { return supitem; }

  virtual string getOrderType() const { return "PO"; }

  Buffer* getBuffer() const;

  static OperationItemSupplier* findOrCreate(ItemSupplier*, Buffer*);

  /* Constructor. */
  explicit OperationItemSupplier(ItemSupplier*, Buffer*);

  /* Destructor. */
  virtual ~OperationItemSupplier();

  static int initialize();

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, ItemSupplier>(Tags::itemsupplier,
                                          &Cls::getItemSupplier, nullptr);
    m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, nullptr,
                                    DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::duration, &Cls::getDuration,
                             &Cls::setDuration);
  }

  /* Scan and trim operationplans creating excess inventory in the
   * buffer.
   */
  void trimExcess(bool zero_or_minimum) const;
};

inline Location* OperationPlan::getOrigin() const {
  if (!oper || !oper->hasType<OperationItemDistribution>()) return nullptr;
  return static_cast<OperationItemDistribution*>(oper)
      ->getItemDistribution()
      ->getOrigin();
}

Supplier* OperationPlan::getSupplier() const {
  if (!oper || !oper->hasType<OperationItemSupplier>()) return nullptr;
  return static_cast<OperationItemSupplier*>(oper)
      ->getItemSupplier()
      ->getSupplier();
}

/* A buffer represents a combination of a item and location.
 * It is the entity for keeping modeling inventory.
 */
class Buffer : public HasHierarchy<Buffer>,
               public HasLevel,
               public Plannable,
               public HasDescription {
  friend class Flow;
  friend class FlowPlan;

 public:
  typedef TimeLine<FlowPlan> flowplanlist;
  typedef Association<Operation, Buffer, Flow>::ListB flowlist;

  /* Default constructor. */
  explicit Buffer() {}

  static Buffer* findOrCreate(Item*, Location*);

  static Buffer* findOrCreate(Item*, Location*, const PooledString&);

  static Buffer* findFromName(string nm);

  /* Builds a producing operation for a buffer.
   * The logic used is based on the following:
   *   - If specified explicitly, don't do anything.
   *   - Add an operation for every supplier that can supply this item to
   *     this location.
   *     The new operation is called "Purchase X from Y", where X is the
   *     buffer name and Y is the supplier.
   *   - If multiple suppliers are found, an alternate operation is created
   *     on top of them. The search is by priority.
   *     TODO Make the creation of the superoperation flexible & configurable
   *   - All new operations are marked as hidden.
   *   - This method can be incrementally build up the producing operation.
   */
  void buildProducingOperation();

  /* Creates a producing FlowEnd if missing for that operation */
  void correctProducingFlow(Operation* itemoper);

  bool hasConsumingFlows() const;

  /* Return the decoupled lead time of this buffer. */
  virtual pair<Duration, Date> getDecoupledLeadTime(
      double, Date, bool recurse_ip_buffers = true) const;

  static PyObject* getDecoupledLeadTimePython(PyObject* self, PyObject* args);

  /* Returns the minimum onhand between the argument date and infinite future.
   * This inventory is freely available and unallocated. */
  static PyObject* availableOnhandPython(PyObject* self, PyObject* args);

  /* Returns the operation that is used to supply extra supply into this
   * buffer. */
  Operation* getProducingOperation() const {
    if (producing_operation == uninitializedProducing)
      const_cast<Buffer*>(this)->buildProducingOperation();
    return producing_operation;
  }

  /* Updates the operation that is used to supply extra supply into this
   * buffer. */
  void setProducingOperation(Operation* o) {
    if (o && o->getHidden())
      logger << "Warning: avoid setting the producing operation to a hidden "
                "operation"
             << endl;
    producing_operation = o;
    setChanged();
  }

  /* Returns the item stored in this buffer. */
  Item* getItem() const { return it; }

  /* Updates the Item stored in this buffer. */
  void setItem(Item*, bool);
  void setItem(Item* i) { setItem(i, true); }

  /* Returns the Location of this buffer. */
  Location* getLocation() const { return loc; }

  /* Updates the location of this buffer. */
  void setLocation(Location* i, bool recompute) {
    loc = i;
    // Trigger level recomputation
    if (recompute) HasLevel::triggerLazyRecomputation();
  }

  void setLocation(Location* i) {
    loc = i;
    // Trigger level recomputation
    HasLevel::triggerLazyRecomputation();
  }

  PooledString getBatch() const { return batch; }

  const string& getBatchString() const { return batch; }

  void setBatch(const string& s) { batch = s; }

  void setBatch(const PooledString& s) { batch = s; }

  /* Returns the minimum inventory level. */
  double getMinimum() const { return min_val; }

  /* Return true if this buffer represents a tool. */
  bool getTool() const { return (flags & TOOL) != 0; }

  /* Marks the buffer as a tool. */
  void setTool(bool b) {
    if (b)
      flags |= TOOL;
    else
      flags &= ~TOOL;
  }

  bool getAutofence() const { return (flags & AUTOFENCE) != 0; }

  void setAutofence(bool b) {
    if (b)
      flags |= AUTOFENCE;
    else
      flags &= ~AUTOFENCE;
  }

  /* Debugging function. */
  void inspect(const string& = "", const short = 0) const;

  static PyObject* inspectPython(PyObject*, PyObject*);

  /* Return a pointer to the next buffer for the same item. */
  Buffer* getNextItemBuffer() const { return nextItemBuffer; }

  /* Returns a pointer to a calendar for storing the minimum inventory
   * level. */
  Calendar* getMinimumCalendar() const { return min_cal; }

  /* Returns the maximum inventory level. */
  double getMaximum() const { return max_val; }

  /* Returns a pointer to a calendar for storing the maximum inventory
   * level. */
  Calendar* getMaximumCalendar() const { return max_cal; }

  /* Updates the minimum inventory target for the buffer. */
  void setMinimum(double);

  /* Updates the minimum inventory target for the buffer. */
  void setMinimumCalendar(Calendar*);

  /* Updates the minimum inventory target for the buffer. */
  void setMaximum(double);

  /* Updates the minimum inventory target for the buffer. */
  void setMaximumCalendar(Calendar*);

  /* Initialize the class. */
  static int initialize();

  /* Destructor. */
  virtual ~Buffer();

  /* Returns the available material on hand immediately after (which is the
   * default) or immediately before a given date.
   */
  double getOnHand(Date d, bool after = true) const;

  /* Return the current on hand value, using the instance of the inventory
   * operation.
   */
  double getOnHand() const;

  /* Update the on-hand inventory at the start of the planning horizon. */
  void setOnHand(double f);

  /* Returns minimum or maximum available material on hand in the given
   * daterange. The third parameter specifies whether we return the
   * minimum (which is the default) or the maximum value.
   * The fourth parameter specifies if we need to compare against 0
   * or against the safety stock.
   * The fifth argument allows to ignore any proposed purchase orders
   * in the calculation.
   * The computation is INclusive the start and end dates.
   */
  double getOnHand(Date, Date, bool min = true, bool use_safetystock = false,
                   bool include_proposed_po = true) const;

  /* Returns a reference to the list of all flows of this buffer. */
  const flowlist& getFlows() const { return flows; }

  flowlist::const_iterator getFlowIterator() const { return flows.begin(); }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  /* Returns a reference to the list of all flow plans of this buffer. */
  const flowplanlist& getFlowPlans() const { return flowplans; }

  flowplanlist::const_iterator getFlowPlanIterator() const {
    return flowplans.begin();
  }

  /* Returns a reference to the list of all flow plans of this buffer. */
  flowplanlist& getFlowPlans() { return flowplans; }

  /* Return the flow that is associates a given operation with this buffer.
   * Returns nullptr is no such flow exists. */
  Flow* findFlow(const Operation* o, Date d) const {
    return o ? o->findFlow(this, d) : nullptr;
  }

  /* Deletes all operationplans consuming from or producing from this
   * buffer. The boolean parameter controls whether we delete also locked
   * operationplans or not.
   */
  void deleteOperationPlans(bool deleteLockedOpplans = false);

  virtual void updateProblems();

  void setHidden(bool b) {
    if (hidden != b) setChanged();
    hidden = b;
  }

  bool getHidden() const { return hidden; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  /* This function matches producing and consuming operationplans
   * with each other, and updates the pegging iterator accordingly.
   */
  void followPegging(PeggingIterator&, FlowPlan*, double, double, short);

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    HasHierarchy<Cls>::template registerFields<Cls>(m);
    HasDescription::registerFields<Cls>(m);
    m->addPointerField<Cls, Operation>(Tags::producing,
                                       &Cls::getProducingOperation,
                                       &Cls::setProducingOperation);
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem,
                                  MANDATORY + WRITE_OBJECT_SVC);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation, MANDATORY);
    m->addStringRefField<Cls>(Tags::batch, &Cls::getBatchString, &Cls::setBatch,
                              "", MANDATORY);
    Plannable::registerFields<Cls>(m);
    m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnHand, &Cls::setOnHand);
    m->addDoubleField<Cls>(Tags::minimum, &Cls::getMinimum, &Cls::setMinimum);
    m->addPointerField<Cls, Calendar>(Tags::minimum_calendar,
                                      &Cls::getMinimumCalendar,
                                      &Cls::setMinimumCalendar);
    m->addDoubleField<Cls>(Tags::maximum, &Cls::getMaximum, &Cls::setMaximum,
                           0);
    m->addPointerField<Cls, Calendar>(Tags::maximum_calendar,
                                      &Cls::getMaximumCalendar,
                                      &Cls::setMaximumCalendar);
    m->addIteratorField<Cls, flowlist::const_iterator, Flow>(
        Tags::flows, Tags::flow, &Cls::getFlowIterator, DETAIL);
    m->addBoolField<Cls>(Tags::tool, &Cls::getTool, &Cls::setTool, BOOL_FALSE);
    m->addBoolField<Cls>(Tags::autofence, &Cls::getAutofence,
                         &Cls::setAutofence, BOOL_TRUE);
    m->addIteratorField<Cls, flowplanlist::const_iterator, FlowPlan>(
        Tags::flowplans, Tags::flowplan, &Cls::getFlowPlanIterator,
        PLAN + WRITE_OBJECT + WRITE_HIDDEN);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    HasLevel::registerFields<Cls>(m);
    m->addBoolField<Cls>(Tags::ip_flag, &Cls::getIPFlag, &Cls::setIPFlag,
                         BOOL_FALSE);
  }

  /* A dummy producing operation to mark uninitialized ones. */
  static OperationFixedTime* uninitializedProducing;

  /* Returns true if this buffer is a decoupling point. */
  bool getIPFlag() const { return ip_data; }

  /* Marks a buffer as a decoupling point. */
  void setIPFlag(bool b) { ip_data = b; }

 private:
  /* This models the dynamic part of the plan, representing all planned
   * material flows on this buffer. */
  flowplanlist flowplans;

  /* This models the defined material flows on this buffer. */
  flowlist flows;

  /* Hide this entity from serialization or not. */
  bool hidden = false;

  /* This is the operation used to create extra material in this buffer. */
  Operation* producing_operation = uninitializedProducing;

  /* Location of this buffer.
   * This field is only used as information.
   * The default is nullptr.
   */
  Location* loc = nullptr;

  /* Item being stored in this buffer.
   * The default value is nullptr.
   */
  Item* it = nullptr;

  /* Minimum inventory target.
   * If a minimum calendar is specified this field is ignored.
   * @see min_cal
   */
  double min_val = 0.0;

  /* Maximum inventory target.
   * If a maximum calendar is specified this field is ignored.
   */
  double max_val = 0;

  /* Points to a calendar to store the minimum inventory level.
   * The default value is nullptr, resulting in a constant minimum level
   * of 0.
   */
  Calendar* min_cal = nullptr;

  /* Points to a calendar to store the maximum inventory level.
   * The default value is nullptr, resulting in a buffer without excess
   * inventory problems.
   */
  Calendar* max_cal = nullptr;

  /* Maintain a linked list of buffers per item. */
  Buffer* nextItemBuffer = nullptr;

  /* Marks MTO buffers. */
  PooledString batch;

  /* A flag that marks whether this buffer represents a tool or not. */
  static const unsigned short TOOL = 1;
  static const unsigned short AUTOFENCE = 2;
  unsigned short flags = AUTOFENCE;

  /* Marks decoupling points. */
  bool ip_data = false;
};

/* An internally generated operation to represent inventory. */
class OperationInventory : public OperationFixedTime {
  friend class Buffer;

 private:
  virtual ~OperationInventory() {}

 public:
  explicit OperationInventory(Buffer*);

  Buffer* getBuffer() const;

  static int initialize();

  virtual string getOrderType() const { return "STCK"; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, nullptr,
                                    DONT_SERIALIZE);
  }
};

/* An internally generated operation to represent a zero time delivery.
 */
class OperationDelivery : public OperationFixedTime {
  friend class Demand;

 public:
  /* Default constructor. */
  explicit OperationDelivery();

  /* Destructor. */
  virtual ~OperationDelivery() {}

  /* Return the delivery buffer. */
  Buffer* getBuffer() const;

  /* Update the delivery buffer. */
  void setBuffer(Buffer*);

  static int initialize();

  virtual string getOrderType() const { return "DLVR"; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer,
                                    &Cls::setBuffer, MANDATORY);
    m->addDurationField<Cls>(Tags::duration, &Cls::getDuration,
                             &Cls::setDuration);
  }

  static Duration getDeliveryDuration() { return deliveryduration; }

  static void setDeliveryDuration(Duration d) {
    if (d < 0L)
      logger << "Warning: Delivery duration must be >= 0." << endl;
    else
      deliveryduration = d;
  }

 private:
  static Duration deliveryduration;
};

inline bool OperationPlan::getHidden() const {
  if (getOperation() && getOperation()->hasType<OperationInventory>())
    return true;
  else
    return false;
}

inline Location* OperationPlan::getLocation() const {
  if (!oper)
    return nullptr;
  else if (oper->hasType<OperationItemSupplier>())
    return static_cast<OperationItemSupplier*>(oper)
        ->getBuffer()
        ->getLocation();
  else if (oper->hasType<OperationItemDistribution>())
    return static_cast<OperationItemDistribution*>(oper)->getDestination()
               ? static_cast<OperationItemDistribution*>(oper)
                     ->getDestination()
                     ->getLocation()
               : static_cast<OperationItemDistribution*>(oper)
                     ->getOrigin()
                     ->getLocation();
  else if (oper->hasType<OperationInventory>())
    return static_cast<OperationInventory*>(oper)->getBuffer()->getLocation();
  else if (oper->hasType<OperationDelivery>())
    return static_cast<OperationDelivery*>(oper)->getBuffer()->getLocation();
  else
    return nullptr;
}

Item* OperationPlan::getItem() const {
  if (!oper)
    return nullptr;
  else if (oper->hasType<OperationItemSupplier>())
    return static_cast<OperationItemSupplier*>(oper)->getBuffer()->getItem();
  else if (oper->hasType<OperationItemDistribution>())
    return static_cast<OperationItemDistribution*>(oper)->getDestination()
               ? static_cast<OperationItemDistribution*>(oper)
                     ->getDestination()
                     ->getItem()
               : static_cast<OperationItemDistribution*>(oper)
                     ->getOrigin()
                     ->getItem();
  else if (oper->hasType<OperationInventory>())
    return static_cast<OperationInventory*>(oper)->getBuffer()->getItem();
  else if (oper->hasType<OperationDelivery>())
    return static_cast<OperationDelivery*>(oper)->getBuffer()->getItem();
  else
    return nullptr;
}

class Item::bufferIterator {
 private:
  Buffer* cur;

 public:
  /* Constructor. */
  bufferIterator(const Item* i) : cur(i ? i->firstItemBuffer : nullptr) {}

  bool operator!=(const bufferIterator& b) const { return b.cur != cur; }

  bool operator==(const bufferIterator& b) const { return b.cur == cur; }

  bufferIterator& operator++() {
    if (cur) cur = cur->getNextItemBuffer();
    return *this;
  }

  bufferIterator operator++(int) {
    bufferIterator tmp = *this;
    ++*this;
    return tmp;
  }

  Buffer* next() {
    Buffer* tmp = cur;
    if (cur) cur = cur->getNextItemBuffer();
    return tmp;
  }

  Buffer* operator->() const { return cur; }

  Buffer& operator*() const { return *cur; }
};

inline Item::bufferIterator Item::getBufferIterator() const { return this; }

inline int Item::getCluster() const {
  return firstItemBuffer ? firstItemBuffer->getCluster() : 0;
}

/* This class is the default implementation of the abstract Buffer
 * class. */
class BufferDefault : public Buffer {
 public:
  explicit BufferDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/*  This class represents a material buffer with an infinite supply of
 * extra material.
 *
 * In other words, it never constrains the plan and it doesn't propagate any
 * requirements upstream.
 */
class BufferInfinite : public Buffer {
 public:
  explicit BufferInfinite() {
    setDetectProblems(false);
    setProducingOperation(nullptr);
    initType(metadata);
  }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }
  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class defines a material flow to/from a buffer, linked with an
 * operation. This default implementation plans the material flow at the
 * start of the operation, after the setup time has been completed.
 */
class Flow : public Object,
             public Association<Operation, Buffer, Flow>::Node,
             public Solvable,
             public HasSource {
 public:
  /* Destructor. */
  virtual ~Flow();

  /* Constructor. */
  explicit Flow(Operation* o, Buffer* b, double q) : quantity(q) {
    setBuffer(b);
    setOperation(o);
    initType(metadata);
    HasLevel::triggerLazyRecomputation();
  }

  /* Constructor. */
  explicit Flow(Operation* o, Buffer* b, double q, DateRange e) : quantity(q) {
    setBuffer(b);
    setOperation(o);
    setEffective(e);
    initType(metadata);
    HasLevel::triggerLazyRecomputation();
  }

  /* Search an existing object. */
  static Object* finder(const DataValueDict&);

  /* Returns the operation. */
  Operation* getOperation() const { return getPtrA(); }

  /* Updates the operation of this flow. This method can be called only ONCE
   * for each flow. In case that doesn't suit you, delete the existing flow
   * and create a new one.
   */
  void setOperation(Operation* o) {
    if (!o) return;
    if (o->hasType<OperationAlternate>()) {
      logger << "Deprecation warning: alternate operation '" << o
             << "' shouldn't consume or produce material" << endl;
    }
    setPtrA(o, o->getFlows());
    // Note: This MTO update is called for every flow that is created.
    // For models with many flows per operation this makes up some overhead that
    // scales quadratically.
    o->updateMTO();
  }

  /* Returns true if this flow consumes material from the buffer. */
  bool isConsumer() const { return quantity < 0 || quantity_fixed < 0; }

  /* Returns true if this flow produces material into the buffer. */
  bool isProducer() const {
    return quantity > 0 || quantity_fixed > 0 ||
           (quantity == 0 && quantity_fixed == 0);
  }

  /* Returns the material flow PER UNIT of the operationplan. */
  double getQuantity() const { return quantity; }

  /* Updates the material flow PER UNIT of the operationplan. Existing
   * flowplans are NOT updated to take the new quantity in effect. Only new
   * operationplans and updates to existing ones will use the new quantity
   * value.
   */
  void setQuantity(double f) {
    if ((quantity > 0.0 && quantity_fixed < 0) ||
        (quantity < 0.0 && quantity_fixed > 0))
      logger << "Warning: Quantity and quantity_fixed must have equal sign"
             << endl;
    else
      quantity = f;
  }

  /* Returns the CONSTANT material flow PER UNIT of the operationplan. */
  double getQuantityFixed() const { return quantity_fixed; }

  /* Updates the CONSTANT material flow of the operationplan. Existing
   * flowplans are NOT updated to take the new quantity in effect. Only new
   * operationplans and updates to existing ones will use the new quantity
   * value.
   */
  void setQuantityFixed(double f) {
    if ((quantity > 0.0 && quantity_fixed < 0) ||
        (quantity < 0.0 && quantity_fixed > 0))
      logger << "Warning: Quantity and quantity_fixed must have equal sign"
             << endl;
    else
      quantity_fixed = f;
  }

  Duration getOffset() const { return offset; }

  void setOffset(Duration s) { offset = s; }

  virtual Date computeFlowToOperationDate(const OperationPlan*, Date) = 0;

  virtual Date computeOperationToFlowDate(const OperationPlan*, Date) = 0;

  /* Returns the buffer. */
  Buffer* getBuffer() const {
    Buffer* b = getPtrB();
    if (b) return b;

    // Dynamically set the buffer
    if (item &&
        (getLocation() || (getOperation() && getOperation()->getLocation()))) {
      b = Buffer::findOrCreate(
          item, getLocation() ? getLocation() : getOperation()->getLocation());
      if (b) const_cast<Flow*>(this)->setPtrB(b, b->getFlows());
    }
    if (!b) throw DataException("Flow doesn't have a buffer");
    return b;
  }

  /* Updates the buffer of this flow. This method can be called only ONCE
   * for each flow. In case that doesn't suit you, delete the existing flow
   * and create a new one.
   */
  void setBuffer(Buffer* b) {
    if (b) setPtrB(b, b->getFlows());
  }

  Item* getItem() const { return getPtrB() ? getPtrB()->getItem() : item; }

  void setItem(Item* i) {
    if (getPtrB() && getPtrB()->getItem() != i)
      throw DataException("Invalid update of operationmaterial");
    item = i;
  }

  Location* getLocation() const { return loc; }

  void setLocation(Location* l) { loc = l; }

  /* Return the leading flow of this group.
   * When the flow has no alternate or if the flow is itself leading
   * then nullptr is returned.
   */
  Flow* getAlternate() const {
    if (getName().empty() || !getOperation()) return nullptr;
    for (auto h = getOperation()->getFlows().begin();
         h != getOperation()->getFlows().end(); ++h) {
      if (this == &*h && getPriority()) return nullptr;
      if (getName() == h->getName() && h->getPriority())
        return const_cast<Flow*>(&*h);
    }
    return nullptr;
  }

  /* Return whether the flow has alternates. */
  bool hasAlternates() const {
    if (getName().empty() || !getOperation()) return false;
    for (auto h = getOperation()->getFlows().begin();
         h != getOperation()->getFlows().end(); ++h)
      if (this != &*h && getName() == h->getName() && h->getPriority())
        return true;
    return false;
  }

  /* Return the search mode. */
  SearchMode getSearch() const { return search; }

  /* Update the search mode. */
  void setSearch(const string a) { search = decodeSearchMode(a); }

  /* A flow is considered hidden when either its buffer or operation
   * are hidden. */
  virtual bool getHidden() const {
    return (getBuffer() && getBuffer()->getHidden()) ||
           (getOperation() && getOperation()->getHidden());
  }

  /* This method holds the logic the compute the date and quantity of a
   * flowplan. */
  virtual pair<Date, double> getFlowplanDateQuantity(const FlowPlan*) const = 0;

  static int initialize();

  string getTypeName() const { return getType().type; }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       &Cls::setOperation, MANDATORY + PARENT);
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem,
                                  MANDATORY + PARENT);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation, PARENT);
    m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer,
                                    &Cls::setBuffer, DONT_SERIALIZE + PARENT);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity,
                           &Cls::setQuantity);
    m->addDoubleField<Cls>(Tags::quantity_fixed, &Cls::getQuantityFixed,
                           &Cls::setQuantityFixed);
    m->addDurationField<Cls>(Tags::offset, &Cls::getOffset, &Cls::setOffset);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority,
                        1);
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName);
    m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch,
                                     &Cls::setSearch, SearchMode::PRIORITY);
    m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart,
                         &Cls::setEffectiveStart);
    m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd,
                         &Cls::setEffectiveEnd, Date::infiniteFuture);
    HasSource::registerFields<Cls>(m);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    // Not very nice: all flow subclasses appear to Python as instance of a
    // single Python class. We use this method to distinguish them.
    m->addStringField<Cls>(Tags::type, &Cls::getTypeName, nullptr, "",
                           DONT_SERIALIZE);
  }

 protected:
  /* Default constructor. */
  explicit Flow() {
    initType(metadata);
    HasLevel::triggerLazyRecomputation();
  }

 private:
  /* Item of the flow. This can be used to automatically generate the buffer
   * when and if needed.
   */
  Item* item = nullptr;

  Location* loc = nullptr;

  /* Variable quantity of the material consumption/production. */
  double quantity = 0.0;

  /* Constant quantity of the material consumption/production. */
  double quantity_fixed = 0.0;

  /* Mode to select the preferred alternates. */
  SearchMode search = SearchMode::PRIORITY;

  /* Offset from the start or end of the operation. */
  Duration offset;

  static PyObject* create(PyTypeObject* pytype, PyObject*, PyObject*);
};

/* This class defines a material flow to/from a buffer, linked with an
 * operation. This subclass represents a flow that is at the start date of
 * the operation.
 */
class FlowStart : public Flow {
 public:
  /* Constructor. */
  explicit FlowStart(Operation* o, Buffer* b, double q) : Flow(o, b, q) {}

  /* This constructor is called from the plan begin_element function. */
  explicit FlowStart() {}

  virtual pair<Date, double> getFlowplanDateQuantity(const FlowPlan*) const;

  virtual Date computeFlowToOperationDate(const OperationPlan*, Date);

  virtual Date computeOperationToFlowDate(const OperationPlan*, Date);

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }
};

/* This class defines a material flow to/from a buffer, linked with an
 * operation. This subclass represents a flow that is at end date of the
 * operation.
 */
class FlowEnd : public Flow {
 public:
  /* Constructor. */
  explicit FlowEnd(Operation* o, Buffer* b, double q) : Flow(o, b, q) {}

  /* This constructor is called from the plan begin_element function. */
  explicit FlowEnd() {}

  /* This method holds the logic the compute the date and quantity of a
   * flowplan. */
  virtual pair<Date, double> getFlowplanDateQuantity(const FlowPlan*) const;

  virtual Date computeFlowToOperationDate(const OperationPlan*, Date);

  virtual Date computeOperationToFlowDate(const OperationPlan*, Date);

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
};

/* This class represents a flow producing/material of a fixed quantity
 * spread across the total duration of the operationplan
 *
 * TODO The implementation of this class ignores date effectivity.
 */
class FlowTransferBatch : public Flow {
 private:
  double transferbatch = 0;

 public:
  /* Constructor. */
  explicit FlowTransferBatch(Operation* o, Buffer* b, double q)
      : Flow(o, b, q) {
    initType(metadata);
  }

  /* This constructor is called from the plan begin_element function. */
  explicit FlowTransferBatch() { initType(metadata); }

  double getTransferBatch() const { return transferbatch; }

  void setTransferBatch(double d) {
    if (d < 0.0)
      logger
          << "Warning: Transfer batch size must be greater than or equal to 0"
          << endl;
    else
      transferbatch = d;
  }

  virtual Date computeFlowToOperationDate(const OperationPlan*, Date);

  virtual Date computeOperationToFlowDate(const OperationPlan*, Date);

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDoubleField<Cls>(Tags::transferbatch, &Cls::getTransferBatch,
                           &Cls::setTransferBatch);
  }

  /* This method holds the logic the compute the date and quantity of a
   * flowplan. */
  virtual pair<Date, double> getFlowplanDateQuantity(const FlowPlan*) const;

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
};

/* A flowplan represents a planned material flow in or out of a buffer.
 *
 * Flowplans are owned by operationplans, which manage a container to store
 * them.
 */
class FlowPlan : public TimeLine<FlowPlan>::EventChangeOnhand {
  friend class OperationPlan::FlowPlanIterator;
  friend class OperationPlan;
  friend class FlowTransferBatch;

 private:
  /* Points to the flow instantiated by this flowplan. */
  Flow* fl = nullptr;

  /* Points to the operationplan owning this flowplan. */
  OperationPlan* oper = nullptr;

  /* Points to the next flowplan owned by the same operationplan. */
  FlowPlan* nextFlowPlan = nullptr;

  /* For MTS items: flowplan.getBuffer() == flow->getBuffer()
   * For MTO items: flowplan.getBuffer() != flow->getBuffer()
   */
  Buffer* buf = nullptr;

  /* Finds the flowplan on the operationplan when we read data. */
  static Object* reader(const MetaClass*, const DataValueDict&,
                        CommandManager*);
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  /* Is this operationplanmaterial locked?
      LEAVE THIS VARIABLE DECLARATION BELOW THE OTHERS
  */
  // Flag bits
  static const unsigned short STATUS_CONFIRMED = 1;
  static const unsigned short STATUS_CLOSED = 2;
  static const unsigned short FOLLOWING_BATCH = 4;
  unsigned short flags = 0;

  /* Internal use only from OperationPlan::setBatch() */
  void updateBatch();

 public:
  static const MetaClass* metadata;
  static const MetaCategory* metacategory;
  static int initialize();
  virtual const MetaClass& getType() const { return *metadata; }

  explicit FlowPlan(OperationPlan*, const Flow*);

  explicit FlowPlan(OperationPlan*, const Flow*, Date, double);

  bool isFollowingBatch() const { return (flags & FOLLOWING_BATCH) != 0; }

  void setFollowingBatch(bool b) {
    if (b)
      flags |= FOLLOWING_BATCH;
    else
      flags &= ~FOLLOWING_BATCH;
  }

  /* Returns the flow of which this is an plan instance. */
  Flow* getFlow() const { return fl; }

  /* Returns the buffer. */
  Buffer* getBuffer() const { return buf; }

  /* Returns the operation, a convenient shortcut. */
  Operation* getOperation() const { return fl ? fl->getOperation() : nullptr; }

  /* Returns the item being produced or consumed. */
  Item* getItem() const { return buf ? buf->getItem() : nullptr; }

  /* Update the flowplan to a different item.
   * The new flow must belong to the same operation.
   */
  void setItem(Item*);

  inline Date computeFlowToOperationDate(Date d) const {
    return fl->computeFlowToOperationDate(oper, d);
  }

  inline Date computeOperationToFlowDate(Date d) const {
    return fl->computeOperationToFlowDate(oper, d);
  }

  /* Update the operationplan.
   * This can only be called once.
   */
  void setOperationPlan(OperationPlan* o) {
    if (!oper) oper = o;
  }

  /* Update the flow of an already existing flowplan.
   * The new flow must belong to the same operation.
   */
  void setFlow(Flow*);

  /* Update the buffer of an already existing flowplan.
   * The new buffer can only have a different batch, but item and location
   * must match.
   */
  void setBuffer(Buffer*);

  /* Returns the operationplan owning this flowplan. */
  virtual OperationPlan* getOperationPlan() const { return oper; }

  /* Return the status of the operationplanmaterial.
   * The status string is one of the following:
   * - proposed
   * - confirmed
   * - closed
   */
  string getStatus() const;

  /* Update the status of the operationplanmaterial. */
  void setStatus(const string&);

  bool getProposed() const {
    return (flags & (STATUS_CONFIRMED + STATUS_CLOSED)) == 0;
  }

  void setProposed(bool b) {
    if (b)
      flags &= ~(STATUS_CLOSED + STATUS_CONFIRMED);
    else {
      flags |= STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    }
  }

  bool getConfirmed() const { return (flags & STATUS_CONFIRMED) != 0; }

  void setConfirmed(bool b) {
    if (b) {
      flags |= STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    } else {
      flags &= ~STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    }
  }

  bool getClosed() const { return (flags & STATUS_CLOSED) != 0; }

  void setClosed(bool b) {
    if (b) {
      flags &= ~STATUS_CONFIRMED;
      flags |= STATUS_CLOSED;
    } else {
      flags |= ~STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    }
  }

  /* Returns the duration before the current onhand will be completely
   * consumed. */
  Duration getPeriodOfCover() const;

  /* Destructor. */
  virtual ~FlowPlan() {
    assert(buf);
    buf->setChanged();
    buf->flowplans.erase(this);
  }

  void setQuantityAPI(double quantity) {
    setQuantity(quantity, false, true, true);
  }

  /* Updates the quantity of the flowplan by changing the quantity of the
   * operationplan owning this flowplan.
   * The boolean parameter is used to control whether to round up (false)
   * or down (true) in case the operation quantity must be a multiple.
   * The second parameter is to flag whether we want to actually perform
   * the resizing, or only to simulate it.
   *
   * Possible resizing modes:
   *  - 0: keep the flowplan at its current date during the resize
   *  - 1: keep the start date constant when resizing the flowplan
   *  - 2: keep the end date constant when resizing the flowplan
   *
   * The return value is a pair with:
   *   1) flowplan quantity
   *   2) operationplan quantity
   *
   * @TODO: update parameter is not used any longer. Anybody calling this method
   * with update=false isn't getting what he expects.
   */
  pair<double, double> setQuantity(double quantity, bool rounddown = false,
                                   bool update = true, bool execute = true,
                                   short mode = 2);

  void setQuantityRaw(double);

  /* This function needs to be called whenever the flowplan date or
   * quantity are changed.
   */
  void update();

  bool getFeasible() const;

  /* Return a pointer to the timeline data structure owning this flowplan. */
  TimeLine<FlowPlan>* getTimeLine() const { return &(buf->flowplans); }

  /* Returns true when the flowplan is hidden.
   * This is determined by looking at whether the flow is hidden or not.
   */
  bool getHidden() const { return fl->getHidden(); }

  void setDate(Date d) {
    if (getConfirmed()) {
      // Update the timeline data structure
      buf->flowplans.update(this, getQuantity(), d);

      // Mark the operation and buffer as having changed. This will trigger the
      // recomputation of their problems
      buf->setChanged();
      fl->getOperation()->setChanged();
    } else {
      throw DataException(
          "Unhandled case: Cannot change a date of a proposed FlowPlan");
    }
  }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDateField<Cls>(Tags::date, &Cls::getDate, &Cls::setDate);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity,
                           &Cls::setQuantityAPI);
    m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnhand, nullptr, -666);
    m->addDoubleField<Cls>(Tags::minimum, &Cls::getMin);
    m->addDoubleField<Cls>(Tags::maximum, &Cls::getMax);
    m->addDurationField<Cls>(Tags::period_of_cover, &Cls::getPeriodOfCover,
                             nullptr);
    m->addStringField<Cls>(Tags::status, &Cls::getStatus, &Cls::setStatus,
                           "proposed");
    m->addPointerField<Cls, OperationPlan>(
        Tags::operationplan, &Cls::getOperationPlan, &Cls::setOperationPlan,
        BASE + WRITE_OBJECT + PARENT);
    m->addPointerField<Cls, Flow>(Tags::flow, &Cls::getFlow, &Cls::setFlow,
                                  DONT_SERIALIZE);
    m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, nullptr);
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem,
                                  DONT_SERIALIZE);
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       nullptr, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, nullptr, BOOL_FALSE,
                         DONT_SERIALIZE);
  }
};

/* An specific changeover rule in a setup matrix. */
class SetupMatrixRule : public Object, public HasSource {
  friend class SetupMatrix;

 public:
  /* Default constructor. */
  SetupMatrixRule() {}

  /* Constructor. */
  SetupMatrixRule(SetupMatrix* m, const PooledString& f, const PooledString& t,
                  Duration d, double c, int p)
      : matrix(m), from(f), to(t), duration(d), cost(c), priority(p) {}

  /* Update the matrix pointer. */
  void setSetupMatrix(SetupMatrix*);

  /* Destructor. */
  ~SetupMatrixRule();

  static int initialize();

  static const MetaCategory* metadata;

  /* Factory method. */
  static Object* reader(const MetaClass*, const DataValueDict&,
                        CommandManager* = nullptr);

  /* Update the priority.
   * The priority value is a key field. If multiple rules have the
   * same priority a data exception is thrown.
   */
  void setPriority(const int);

  /* Return the matrix owning this rule. */
  SetupMatrix* getSetupMatrix() const { return matrix; }

  Resource* getResource() const { return resource; }

  void setResource(Resource* r) { resource = r; }

  /* Return the priority. */
  int getPriority() const { return priority; }

  /* Update the from setup. */
  void setFromSetup(const string& f) {
    from = f;
    updateExpression();
  }

  /* Return the from setup. */
  const string& getFromSetupString() const { return from; }

  const PooledString& getFromSetup() const { return from; }

  /* Update the to setup. */
  void setToSetup(const string& f) {
    to = f;
    updateExpression();
  }

  /* Return the to setup. */
  const string& getToSetupString() const { return to; }

  const PooledString& getToSetup() const { return to; }

  /* Update the conversion duration. */
  void setDuration(Duration p) { duration = p; }

  /* Return the conversion duration. */
  Duration getDuration() const { return duration; }

  /* Update the conversion cost. */
  void setCost(double c) { cost = max(c, 0.0); }

  /* Return the conversion cost. */
  double getCost() const { return cost; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::fromsetup, &Cls::getFromSetupString,
                              &Cls::setFromSetup);
    m->addStringRefField<Cls>(Tags::tosetup, &Cls::getToSetupString,
                              &Cls::setToSetup);
    m->addDurationField<Cls>(Tags::duration, &Cls::getDuration,
                             &Cls::setDuration);
    m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
    m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource,
                                      &Cls::setResource);
    m->addPointerField<Cls, SetupMatrix>(
        Tags::setupmatrix, &Cls::getSetupMatrix, &Cls::setSetupMatrix,
        DONT_SERIALIZE + PARENT);
    HasSource::registerFields<Cls>(m);
  }

  /* Returns true if this rule matches with the from-setup and to-setup being
   * passed. */
  bool matches(const string& from_to) const {
    return regex_match(from_to, expression);
  }

 private:
  /* Pointer to the owning matrix. */
  SetupMatrix* matrix = nullptr;

  /* Pointer to the next rule in this matrix. */
  SetupMatrixRule* nextRule = nullptr;

  /* Pointer to the previous rule in this matrix. */
  SetupMatrixRule* prevRule = nullptr;

  /* Additional resource needed during the changeover. */
  Resource* resource = nullptr;

  /* Original setup. */
  PooledString from;

  /* New setup. */
  PooledString to;

  /* Changeover time. */
  Duration duration;

  /* Changeover cost. */
  double cost = 0.0;

  /* Priority of the rule.
   * This field is the key field, i.e. within a setup matrix all rules
   * need to have different priorities.
   */
  int priority = 0;

  void updateSort();

  void updateExpression();

  /* A compiled regular expression for the from-to definition. */
  regex expression;

 public:
  /* An iterator class to go through all rules of a setup matrix. */
  class iterator {
   private:
    SetupMatrixRule* curRule;

   public:
    /* Constructor. */
    iterator(SetupMatrixRule* c = nullptr) : curRule(c) {}

    bool operator!=(const iterator& b) const { return b.curRule != curRule; }

    bool operator==(const iterator& b) const { return b.curRule == curRule; }

    iterator& operator++() {
      if (curRule) curRule = curRule->nextRule;
      return *this;
    }

    iterator operator++(int) {
      iterator tmp = *this;
      ++*this;
      return tmp;
    }

    SetupMatrixRule* next() {
      SetupMatrixRule* tmp = curRule;
      if (curRule) curRule = curRule->nextRule;
      return tmp;
    }

    iterator& operator--() {
      if (curRule) curRule = curRule->prevRule;
      return *this;
    }

    iterator operator--(int) {
      iterator tmp = *this;
      --*this;
      return tmp;
    }

    SetupMatrixRule* operator->() const { return curRule; }

    SetupMatrixRule& operator*() const { return *curRule; }

    static iterator end() { return nullptr; }
  };
};

/* This class is the default implementation of the abstract
 * SetupMatrixRule class.
 */
class SetupMatrixRuleDefault : public SetupMatrixRule {
 public:
  /* Default constructor. */
  explicit SetupMatrixRuleDefault() { initType(metadata); }

  /* Constructor. */
  SetupMatrixRuleDefault(SetupMatrix* m, const PooledString& f,
                         const PooledString& t, Duration d, double c, int p)
      : SetupMatrixRule(m, f, t, d, c, p) {
    initType(metadata);
  }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class is used to represent a matrix defining the changeover
 * times between setups.
 */
class SetupMatrix : public HasName<SetupMatrix>, public HasSource {
  friend class SetupMatrixRule;

 public:
  class RuleIterator;  // Forward declaration

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "",
                              MANDATORY);
    HasSource::registerFields<Cls>(m);
    m->addIteratorField<Cls, SetupMatrixRule::iterator, SetupMatrixRule>(
        Tags::rules, Tags::rule, &Cls::getRules, BASE + WRITE_OBJECT);
  }

 public:
  /* Default constructor. */
  explicit SetupMatrix()
      : ChangeOverNotAllowed(this, PooledString("NotAllowed"),
                             PooledString("NotAllowed"), 7L * 86400L, DBL_MAX,
                             INT_MAX) {}

  /* Destructor. */
  ~SetupMatrix();

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  /* Returns an iterator to go through the list of rules. */
  SetupMatrixRule::iterator getRules() const {
    return SetupMatrixRule::iterator(firstRule);
  }

  /* Computes the changeover time and cost between 2 setup values.
   *
   * To compute the time of a changeover the algorithm will evaluate all
   * rules in sequence (in order of priority).
   * For a rule to match the changeover between the original setup X to
   * a new setup Y, two conditions need to be fulfilled:
   *  - The original setup X must match with the fromsetup of the rule.
   *    If the fromsetup field is empty, it is considered a match.
   *  - The new setup Y must match with the tosetup of the rule.
   *    If the tosetup field is empty, it is considered a match.
   * As soon as a matching rule is found, it is applied and subsequent
   * rules are not evaluated.
   * If no matching rule is found, the changeover is not allowed: a pointer
   * to a dummy changeover with a very high cost and duration is returned.
   */
  SetupMatrixRule* calculateSetup(const PooledString&, const PooledString&,
                                  Resource* = nullptr) const;

  static PyObject* calculateSetupPython(PyObject*, PyObject*);

 private:
  /* Head of the list of rules. */
  SetupMatrixRule* firstRule = nullptr;

  /* A dummy rule to mark disallowed changeovers. */
  const SetupMatrixRuleDefault ChangeOverNotAllowed;

  /* A cache with information on changeovers.
   * This speeds up the expensive evaluation of the regular expressions
   * in the setup matrix rules.
   */
  typedef pair<PooledString, PooledString> from_to;
  struct from_to_hash {
   public:
    size_t operator()(const from_to& x) const {
      return x.first.hash() ^ x.second.hash();
    }
  };
  typedef unordered_map<from_to, SetupMatrixRule*, from_to_hash> cachedrules;
  cachedrules cachedChangeovers;
};

/* This class is the default implementation of the abstract
 * SetupMatrix class.
 */
class SetupMatrixDefault : public SetupMatrix {
 public:
  explicit SetupMatrixDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class models skills that can be assigned to resources. */
class Skill : public HasName<Skill>, public HasSource {
  friend class ResourceSkill;

 public:
  /* Default constructor. */
  explicit Skill() { initType(metadata); }

  /* Destructor. */
  ~Skill();

  typedef Association<Resource, Skill, ResourceSkill>::ListB resourcelist;

  /* Returns an iterator over the list of resources having this skill. */
  resourcelist::const_iterator getResources() const {
    return resources.begin();
  }

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "",
                              MANDATORY);
    m->addIteratorField<Cls, resourcelist::const_iterator, ResourceSkill>(
        Tags::resourceskills, Tags::resourceskill, &Cls::getResources);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    HasSource::registerFields<Cls>(m);
  }

 private:
  /* This is a list of resources having this skill. */
  resourcelist resources;
};

/* this class is the default implementation of the abstract
 * Skill class.
 */
class SkillDefault : public Skill {
 public:
  explicit SkillDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class represents a workcentre, a physical or logical
 * representation of capacity.
 */
class Resource : public HasHierarchy<Resource>,
                 public HasLevel,
                 public Plannable,
                 public HasDescription {
  friend class Load;
  friend class LoadPlan;
  friend class ResourceSkill;

 public:
  // Forward declaration of inner classes
  class PlanIterator;
  class OperationPlanIterator;

  /* The default time window before the ask date where we look for
   * available capacity. */
  static Duration defaultMaxEarly;

  /* Default constructor. */
  explicit Resource() { setMaximum(1); }

  /* Destructor. */
  virtual ~Resource();

  /* Updates the size of a resource, when it is time-dependent. */
  virtual void setMaximumCalendar(Calendar*);

  /* Updates the size of a resource. */
  void setMaximum(double);

  /* Return a pointer to the maximum capacity profile. */
  Calendar* getMaximumCalendar() const { return size_max_cal; }

  /* Return a pointer to the maximum capacity. */
  double getMaximum() const { return size_max; }

  /* Returns the availability calendar of the resource. */
  Calendar* getAvailable() const { return available; }

  /* Updates the availability calendar of the resource. */
  void setAvailable(Calendar* b) { available = b; }

  double getEfficiency() const { return efficiency; }

  void setEfficiency(const double c) {
    if (c > 0)
      efficiency = c;
    else
      logger << "Warning: Resource efficiency must be positive" << endl;
  }

  bool getConstrained() const { return is_constrained; }

  void setConstrained(bool b) {
    if (!hasType<ResourceInfinite>()) is_constrained = b;
  }

  bool getFrozenSetups() const { return frozen_setups; }

  void setFrozenSetups(bool b) const {
    const_cast<Resource*>(this)->frozen_setups = b;
    if (!b) updateSetupTime();
  }

  Calendar* getEfficiencyCalendar() const { return efficiency_calendar; }

  void setEfficiencyCalendar(Calendar* c) { efficiency_calendar = c; }

  /* Returns the cost of using 1 unit of this resource for 1 hour.
   * The default value is 0.0.
   */
  double getCost() const { return cost; }

  /* Update the cost of using 1 unit of this resource for 1 hour. */
  void setCost(const double c) { cost = max(c, 0.0); }

  typedef Association<Operation, Resource, Load>::ListB loadlist;
  typedef Association<Resource, Skill, ResourceSkill>::ListA skilllist;
  typedef TimeLine<LoadPlan> loadplanlist;

  /* Returns a reference to the list of loadplans. */
  const loadplanlist& getLoadPlans() const { return loadplans; }

  /* Returns a reference to the list of loadplans. */
  loadplanlist::const_iterator getLoadPlanIterator() const {
    return loadplans.begin();
  }

  /* Returns a reference to the list of loadplans. */
  loadplanlist& getLoadPlans() { return loadplans; }

  inline OperationPlanIterator getOperationPlans() const;

  double getUtilization(Date, Date) const;

  /* Returns a constant reference to the list of loads. It defines
   * which operations are using the resource.
   * TODO Get rid of this
   */
  const loadlist& getLoads() const { return loads; }

  /* Debugging function. */
  void inspect(const string& = "", const short = 0) const;

  static PyObject* inspectPython(PyObject*, PyObject*);

  /* Returns a constant reference to the list of loads. It defines
   * which operations are using the resource.
   */
  loadlist::const_iterator getLoadIterator() const { return loads.begin(); }

  /* Returns a constant reference to the list of skills. */
  skilllist::const_iterator getSkills() const { return skills.begin(); }

  /* Returns true when an resource has a certain skill between the specified
   * dates. */
  bool hasSkill(Skill*, Date = Date::infinitePast, Date = Date::infinitePast,
                ResourceSkill** = nullptr) const;

  /* Return the load that is associates a given operation with this
   * resource. Returns nullptr is no such load exists. */
  Load* findLoad(const Operation* o, Date d) const { return loads.find(o, d); }

  /* Initialize the class. */
  static int initialize();

  /* Returns the location of this resource. */
  Location* getLocation() const { return loc; }

  /* Updates the location of this resource. */
  void setLocation(Location* i) { loc = i; }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  /* Deletes all operationplans loading this resource. The boolean parameter
   * controls whether we delete also locked operationplans or not.
   */
  void deleteOperationPlans(bool = false);

  /* Recompute the problems of this resource. */
  virtual void updateProblems();

  /* Update the setup time of all operationplans on the resource. */
  void updateSetupTime() const;

  void setOwner(Resource*);

  void setHidden(bool b) {
    if (hidden != b) setChanged();
    hidden = b;
  }

  bool getHidden() const { return hidden; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  /* Returns true when this resource capacity represents time.
   * This is used by the resourceplan export.
   */
  virtual bool isTime() { return true; }

  /* Returns the maximum inventory buildup allowed in case of capacity
   * shortages. */
  Duration getMaxEarly() const { return maxearly; }

  /* Updates the maximum inventory buildup allowed in case of capacity
   * shortages. */
  void setMaxEarly(Duration c) {
    if (c >= 0L)
      maxearly = c;
    else
      logger << "Warning: MaxEarly must be positive" << endl;
  }

  /* Returns the available time between the two dates. */
  Duration getAvailable(Date, Date) const;

  /* Return a pointer to the setup matrix. */
  SetupMatrix* getSetupMatrix() const { return setupmatrix; }

  /* Update the reference to the setup matrix. */
  void setSetupMatrix(SetupMatrix* s);

  /* Return the current setup. */
  PooledString getSetup() const {
    return setup ? setup->getSetup() : PooledString();
  }

  /* Return the current setup. */
  const string& getSetupString() const {
    if (setup)
      return setup->getSetup();
    else
      return PooledString::nullstring;
  }

  /* Update the current setup. */
  void setSetup(const string& s) {
    if (setup)
      // Updated existing event
      setup->setSetup(PooledString(s));
    else {
      setup =
          new SetupEvent(&getLoadPlans(), Date::infinitePast, PooledString(s));
      getLoadPlans().insert(setup);
    }
  }

  bool getTool() const { return tool; }

  void setTool(bool b);

  bool getToolPerPiece() const { return toolperpiece; }

  void setToolPerPiece(bool b);

  /* Return the setup of the resource on a specific date.
   * To avoid any ambiguity about the current setup of a resource
   * the calculation is based only on the latest *setup end* event
   * before (or at, when the parameter is true) the argument date.
   * @see LoadPlan::getSetupBefore
   */
  SetupEvent* getSetupAt(Date, OperationPlan* = nullptr) const;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    HasHierarchy<Cls>::template registerFields<Cls>(m);
    HasDescription::registerFields<Cls>(m);
    m->addDoubleField<Cls>(Tags::maximum, &Cls::getMaximum, &Cls::setMaximum,
                           1);
    m->addPointerField<Cls, Calendar>(Tags::maximum_calendar,
                                      &Cls::getMaximumCalendar,
                                      &Cls::setMaximumCalendar);
    m->addDurationField<Cls>(Tags::maxearly, &Cls::getMaxEarly,
                             &Cls::setMaxEarly, defaultMaxEarly);
    m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
    m->addDoubleField<Cls>(Tags::efficiency, &Cls::getEfficiency,
                           &Cls::setEfficiency, 100.0);
    m->addPointerField<Cls, Calendar>(Tags::efficiency_calendar,
                                      &Cls::getEfficiencyCalendar,
                                      &Cls::setEfficiencyCalendar);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation);
    m->addBoolField<Cls>(Tags::constrained, &Cls::getConstrained,
                         &Cls::setConstrained, BOOL_TRUE);
    m->addStringRefField<Cls>(Tags::setup, &Cls::getSetupString,
                              &Cls::setSetup);
    m->addPointerField<Cls, SetupMatrix>(
        Tags::setupmatrix, &Cls::getSetupMatrix, &Cls::setSetupMatrix);
    m->addPointerField<Cls, Calendar>(Tags::available, &Cls::getAvailable,
                                      &Cls::setAvailable);
    Plannable::registerFields<Cls>(m);
    m->addIteratorField<Cls, loadlist::const_iterator, Load>(
        Tags::loads, Tags::load, &Cls::getLoadIterator, DETAIL);
    m->addIteratorField<Cls, skilllist::const_iterator, ResourceSkill>(
        Tags::resourceskills, Tags::resourceskill, &Cls::getSkills,
        DETAIL + WRITE_OBJECT);
    m->addIteratorField<Cls, loadplanlist::const_iterator, LoadPlan>(
        Tags::loadplans, Tags::loadplan, &Cls::getLoadPlanIterator,
        DONT_SERIALIZE);
    m->addIteratorField<Cls, OperationPlanIterator, OperationPlan>(
        Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans,
        PLAN + WRITE_OBJECT + WRITE_HIDDEN);
    m->addBoolField<Cls>(Tags::tool, &Cls::getTool, &Cls::setTool, BOOL_FALSE);
    m->addBoolField<Cls>(Tags::toolperpiece, &Cls::getToolPerPiece,
                         &Cls::setToolPerPiece, BOOL_FALSE);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    HasLevel::registerFields<Cls>(m);
  }

 protected:
  /* This calendar is used to updates to the resource size. */
  Calendar* size_max_cal = nullptr;

  /* Stores the collection of all loadplans of this resource. */
  loadplanlist loadplans;

 private:
  /* The maximum resource size.
   * If a calendar is specified, this field is ignored.
   */
  double size_max = 0.0;

  /* This is a list of all load models that are linking this resource with
   * operations. */
  loadlist loads;

  /* This is a list of skills this resource has. */
  skilllist skills;

  /* A pointer to the location of the resource. */
  Location* loc = nullptr;

  /* The cost of using 1 unit of this resource for 1 hour. */
  double cost = 0.0;

  /* The efficiency percentage of this resource. */
  double efficiency = 100.0;

  /* Time phased efficiency percentage. */
  Calendar* efficiency_calendar = nullptr;

  /* Maximum inventory buildup allowed in case of capacity shortages. */
  Duration maxearly = defaultMaxEarly;

  /* Reference to the setup matrix. */
  SetupMatrix* setupmatrix = nullptr;

  /* Current setup. */
  SetupEvent* setup = nullptr;

  /* Availability calendar of the buffer. */
  Calendar* available = nullptr;

  /* Specifies whether this resource is hidden for serialization. */
  bool hidden = false;

  /* Controls whether this resource */
  bool is_constrained = true;

  /* When set the setup rule of existing operationplans isn't recalculated. */
  bool frozen_setups = false;

  /* Tools stay with an operationplan during steps in a routing. */
  bool tool = false;

  /* Resources of this type are tools which are needed proportional to
   * operationplan size. */
  bool toolperpiece = false;

  /* Python method that returns an iterator over the resource plan. */
  static PyObject* plan(PyObject*, PyObject*);
};

inline void OperationPlan::setSetupEvent(Resource* r, Date d,
                                         const PooledString& s,
                                         SetupMatrixRule* m) {
  setSetupEvent(r ? &(r->getLoadPlans()) : nullptr, d, s, m);
}

/* This class provides an efficient way to iterate over
 * the plan of a resource aggregated in time buckets.
 * For resources of type default, a list of dates needs to be passed as
 * argument to define the time buckets.
 * For resources of type buckets, the time buckets are defined on the
 * resource and the argument is ignored.
 */
class Resource::PlanIterator : public PythonExtension<Resource::PlanIterator> {
 public:
  static int initialize();

  /* Constructor.
   * The first argument is the resource whose plan we're looking at.
   * The second argument is a Python iterator over a list of dates. These
   * dates define the buckets at which we aggregate the resource plan.
   */
  PlanIterator(Resource*, PyObject*);

  /* Destructor. */
  ~PlanIterator();

 private:
  /* Structure for iterating over a resource. */
  struct _res {
    Resource* res;
    Resource::loadplanlist::iterator ldplaniter;
    Calendar::EventIterator unavailIter;
    Calendar::EventIterator unavailLocIter;
    Date cur_date;
    Date prev_date;
    double cur_size;
    double cur_load;
    bool prev_value;
    bool bucketized;
  };

  vector<_res> res_list;

  /* A Python object pointing to a list of start dates of buckets. */
  PyObject* bucketiterator;

  /* Python function to iterate over the periods. */
  PyObject* iternext();

  double bucket_available;
  double bucket_load;
  double bucket_setup;
  double bucket_unavailable;

  void update(_res*, Date till);

  /* Python object pointing to the start date of the plan bucket. */
  PyObject* start_date = nullptr;

  /* Python object pointing to the start date of the plan bucket. */
  PyObject* end_date = nullptr;
};

/* This class is the default implementation of the abstract
 * Resource class.
 */
class ResourceDefault : public Resource {
 public:
  explicit ResourceDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class represents a resource that'll never have any
 * capacity shortage. */
class ResourceInfinite : public Resource {
 public:
  explicit ResourceInfinite() {
    setDetectProblems(false);
    setConstrained(false);
    initType(metadata);
  }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }
  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};

/* This class represents a resource whose capacity is defined per
    time bucket. */
class ResourceBuckets : public Resource {
 public:
  /* Default constructor. */
  explicit ResourceBuckets() { initType(metadata); }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }
  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  virtual void updateProblems();

  virtual bool isTime() { return computedFromCalendars; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDoubleField<Cls>(Tags::maxbucketcapacity, &Cls::getMaxBucketCapacity,
                           nullptr, 0.0, DONT_SERIALIZE);
  }

  double getMaxBucketCapacity() const;

  /* Updates the time buckets and the quantity per time bucket. */
  virtual void setMaximumCalendar(Calendar*);

  /* Compute the availability of the resource per bucket. */
  static PyObject* computeBucketAvailability(PyObject*, PyObject*);

 private:
  bool computedFromCalendars = false;
};

/* This class associates a resource with its skills. */
class ResourceSkill : public Object,
                      public Association<Resource, Skill, ResourceSkill>::Node,
                      public HasSource {
 public:
  /* Default constructor. */
  explicit ResourceSkill() { initType(metadata); }

  /* Constructor. */
  explicit ResourceSkill(Skill*, Resource*, int);

  /* Constructor. */
  explicit ResourceSkill(Skill*, Resource*, int, DateRange);

  /* Destructor. */
  ~ResourceSkill();

  /* Initialize the class. */
  static int initialize();

  /* Search an existing object. */
  static Object* finder(const DataValueDict&);

  /* Returns the resource. */
  Resource* getResource() const { return getPtrA(); }

  /* Updates the resource. This method can only be called on an instance. */
  void setResource(Resource* r) {
    if (r) setPtrA(r, r->skills);
  }

  /* Returns the skill. */
  Skill* getSkill() const { return getPtrB(); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  /* Updates the skill. This method can only be called on an instance. */
  void setSkill(Skill* s) {
    if (s) setPtrB(s, s->resources);
  }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource,
                                      &Cls::setResource, MANDATORY + PARENT);
    m->addPointerField<Cls, Skill>(Tags::skill, &Cls::getSkill, &Cls::setSkill,
                                   MANDATORY + PARENT);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority,
                        1);
    m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart,
                         &Cls::setEffectiveStart);
    m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd,
                         &Cls::setEffectiveEnd, Date::infiniteFuture);
    HasSource::registerFields<Cls>(m);
  }

 private:
  /* Factory method. */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
};

/* This class implements the abstract ResourceSkill class. */
class ResourceSkillDefault : public ResourceSkill {
 public:
  /* This constructor is called from the plan begin_element function. */
  explicit ResourceSkillDefault() {}

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
};

/* This class links a resource to a certain operation. */
class Load : public Object,
             public Association<Operation, Resource, Load>::Node,
             public Solvable,
             public HasSource {
  friend class Resource;
  friend class Operation;

 public:
  /* Constructor. */
  explicit Load(Operation* o, Resource* r, double u) {
    setOperation(o);
    Load::setResource(r);
    setQuantity(u);
    initType(metadata);
    HasLevel::triggerLazyRecomputation();
  }

  /* Constructor. */
  explicit Load(Operation* o, Resource* r, double u, DateRange e) {
    setOperation(o);
    Load::setResource(r);
    setQuantity(u);
    setEffective(e);
    initType(metadata);
    HasLevel::triggerLazyRecomputation();
  }

  /* Destructor. */
  ~Load();

  /* Search an existing object. */
  static Object* finder(const DataValueDict& k);

  /* Returns the operation consuming the resource capacity. */
  Operation* getOperation() const { return getPtrA(); }

  /* Updates the operation being loaded. This method can only be called
   * once for a load. */
  void setOperation(Operation*);

  /* Returns the capacity resource being consumed. */
  Resource* getResource() const { return getPtrB(); }

  /* Updates the capacity being consumed. This method can only be called
   * once on a resource. */
  virtual void setResource(Resource* r) {
    if (r) setPtrB(r, r->getLoads());
  }

  /* Returns how much capacity is consumed during the duration of the
   * operationplan. */
  double getQuantity() const { return qty; }

  /* Updates the quantity of the load. */
  void setQuantity(double f) {
    if (f < 0)
      logger << "Warning: OperationResource quantity can't be negative" << endl;
    else
      qty = f;
  }

  double getQuantityFixed() const { return qtyfixed; }

  void setQuantityFixed(double f) {
    if (f < 0)
      logger << "Warning: OperationResource quantity_fixed can't be negative"
             << endl;
    else
      qtyfixed = f;
  }

  /* Return the leading load of this group.
   * When the load has no alternate or if the load is itself leading
   * then nullptr is returned.
   */
  Load* getAlternate() const {
    if (getName().empty() || !getOperation()) return nullptr;
    Load* first_zero = nullptr;
    for (auto h = getOperation()->getLoads().begin();
         h != getOperation()->getLoads().end(); ++h)
      if (getName() == h->getName()) {
        if (h->getPriority())
          return (this == &*h) ? nullptr : const_cast<Load*>(&*h);
        else if (!first_zero)
          first_zero = const_cast<Load*>(&*h);
      }
    return (this == first_zero) ? nullptr : first_zero;
  }

  /* Return whether the load has alternates. */
  bool hasAlternates() const {
    if (getName().empty() || !getOperation()) return false;
    for (auto h = getOperation()->getLoads().begin();
         h != getOperation()->getLoads().end(); ++h)
      if (this != &*h && getName() == h->getName()) return true;
    return false;
  }

  /* Return the required resource setup. */
  PooledString getSetup() const { return setup; }

  /* Update the required resource setup. */
  void setSetupString(const string&);

  /* Return the required resource setup. */
  const string& getSetupString() const { return setup; }

  /* Update the required skill. */
  void setSkill(Skill* s) { skill = s; }

  /* Return the required skill. */
  Skill* getSkill() const { return skill; }

  /* Find the preferred resource in a resource pool to assign a load to.
   * This method is only useful when the loadplan is not created yet.
   */
  Resource* findPreferredResource(Date, OperationPlan*) const;

  /* This method holds the logic the compute the date of a loadplan. */
  virtual Date getLoadplanDate(const LoadPlan*) const;

  /* This method holds the logic the compute the quantity of a loadplan. */
  double getLoadplanQuantity(const LoadPlan*) const;

  /* This method allows computing the operationplan start or end date
   * when given the date of the loadplan.
   */
  virtual Date getOperationPlanDate(const LoadPlan*, Date, bool = true) const;

  static int initialize();

  bool getHidden() const {
    return hidden || (getResource() && getResource()->getHidden()) ||
           (getOperation() && getOperation()->getHidden());
  }

  bool getHiddenLoad() const { return hidden; }

  void setHidden(bool b) { hidden = b; }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  /* Default constructor. */
  Load() {
    initType(metadata);
    HasLevel::triggerLazyRecomputation();
  }

  /* Return the search mode. */
  SearchMode getSearch() const { return search; }

  /* Update the search mode. */
  void setSearch(const string a) { search = decodeSearchMode(a); }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       &Cls::setOperation, MANDATORY + PARENT);
    m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource,
                                      &Cls::setResource, MANDATORY + PARENT);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity,
                           1.0);
    m->addDoubleField<Cls>(Tags::quantity_fixed, &Cls::getQuantityFixed,
                           &Cls::setQuantityFixed, 0.0);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority,
                        1);
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName);
    m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch,
                                     &Cls::setSearch, SearchMode::MINPENALTY);
    m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart,
                         &Cls::setEffectiveStart);
    m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd,
                         &Cls::setEffectiveEnd, Date::infiniteFuture);
    m->addStringRefField<Cls>(Tags::setup, &Cls::getSetupString,
                              &Cls::setSetupString);
    m->addPointerField<Cls, Skill>(Tags::skill, &Cls::getSkill, &Cls::setSkill);
    HasSource::registerFields<Cls>(m);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
  }

 private:
  /* Stores how much capacity is consumed during the duration of an
   * operationplan. */
  double qty = 1.0;

  /* Constant capacity consumption for bucketized resources only. */
  double qtyfixed = 0.0;

  /* Required setup. */
  PooledString setup;

  /* Required skill. */
  Skill* skill = nullptr;

  /* Mode to select the preferred alternates. */
  SearchMode search = SearchMode::MINPENALTY;

  bool hidden = false;

 protected:
  /* Factory method. */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
};

/* This class implements the abstract Load class. */
class LoadDefault : public Load {
 public:
  /* Constructor. */
  explicit LoadDefault(Operation* o, Resource* r, double q) : Load(o, r, q) {}

  /* Constructor. */
  explicit LoadDefault(Operation* o, Resource* r, double q, DateRange e)
      : Load(o, r, q, e) {}

  /* This constructor is called from the plan begin_element function. */
  explicit LoadDefault() {}

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
};

/* This class a load that loads a bucketized resource at a percentage of
 * the operationplan duration. An offset of 0 means loading the resource at the
 * start of the operationplan. An offset of 100 means loading the resource at
 * the end of the operationplan. The calculations consider the available periods
 * of the operationplan, and skip unavailable periods.
 */
class LoadBucketizedPercentage : public Load {
 public:
  /* Constructor. */
  explicit LoadBucketizedPercentage(Operation* o, Resource* r, double q) {
    setOperation(o);
    setResource(r);
    setQuantity(q);
  }

  /* Constructor. */
  explicit LoadBucketizedPercentage(Operation* o, Resource* r, double q,
                                    DateRange e) {
    setOperation(o);
    setResource(r);
    setQuantity(q);
    setEffective(e);
  }

  /* This constructor is called from the plan begin_element function. */
  explicit LoadBucketizedPercentage() {}

  void setResource(Resource* r) {
    if (r && !r->hasType<ResourceBuckets>())
      logger << "Warning: LoadBucketizedPercentage can only be associated with "
                "ResourceBuckets"
             << endl;
    else
      Load::setResource(r);
  }

  double getOffset() const { return offset; }

  void setOffset(double d) {
    if (d < 0 || d > 100)
      logger << "Warning: Load offset must be between 0 and 100" << endl;
    else
      offset = d;
  }

  Date getLoadplanDate(const LoadPlan*) const;

  Date getOperationPlanDate(const LoadPlan*, Date, bool = true) const;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDoubleField<Cls>(Tags::offset, &Cls::getOffset, &Cls::setOffset);
  }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

 private:
  double offset = 0;
};

/* This class a load that loads a bucketized resource at a specified
 * offset from the start of the operationplan.
 * An offset of 0 means loading the resource at the start of the operationplan.
 * An offset of 1 day means loading the resource 1 day after the operationplan
 * start date. If the operationplan takes less than 1 day we load the resource
 * at the end date.
 * The offset is computed based on the available periods of the operationplan,
 * and skips unavailable periods.
 */
class LoadBucketizedFromStart : public Load {
 public:
  /* Constructor. */
  explicit LoadBucketizedFromStart(Operation* o, Resource* r, double q) {
    setOperation(o);
    setResource(r);
    setQuantity(q);
  }

  /* Constructor. */
  explicit LoadBucketizedFromStart(Operation* o, Resource* r, double q,
                                   DateRange e) {
    setOperation(o);
    setResource(r);
    setQuantity(q);
    setEffective(e);
  }

  /* This constructor is called from the plan begin_element function. */
  explicit LoadBucketizedFromStart() {}

  void setResource(Resource* r) {
    if (r && !r->hasType<ResourceBuckets>())
      logger << "Warning: LoadBucketizedFromStart can only be associated with "
                "ResourceBuckets"
             << endl;
    else
      Load::setResource(r);
  }

  Date getLoadplanDate(const LoadPlan*) const;

  Date getOperationPlanDate(const LoadPlan*, Date, bool = true) const;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDurationField<Cls>(Tags::offset, &Cls::getOffset, &Cls::setOffset);
  }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  Duration getOffset() const { return offset; }

  void setOffset(Duration d) {
    if (d < Duration(0L))
      logger << "Warning: Load offset must be positive" << endl;
    else
      offset = d;
  }

 private:
  Duration offset;
};

/* This class a load that loads a bucketized resource at a specified
 * offset from the end of the operationplan.
 * An offset of 0 means loading the resource at the end of the operationplan.
 * An offset of 1 day means loading the resource 1 day before the operationplan
 * end date. If the operationplan takes less than 1 day we load the resource
 * at the start date.
 * The offset is computed based on the available periods of the operationplan,
 * and skips unavailable periods.
 */
class LoadBucketizedFromEnd : public Load {
 public:
  /* Constructor. */
  explicit LoadBucketizedFromEnd(Operation* o, Resource* r, double q) {
    setOperation(o);
    setResource(r);
    setQuantity(q);
  }

  /* Constructor. */
  explicit LoadBucketizedFromEnd(Operation* o, Resource* r, double q,
                                 DateRange e) {
    setOperation(o);
    setResource(r);
    setQuantity(q);
    setEffective(e);
  }

  /* This constructor is called from the plan begin_element function. */
  explicit LoadBucketizedFromEnd() {}

  void setResource(Resource* r) {
    if (r && !r->hasType<ResourceBuckets>())
      logger << "Warning: LoadBucketizedFromEnd can only be associated with "
                "ResourceBuckets"
             << endl;
    else
      Load::setResource(r);
  }

  Date getLoadplanDate(const LoadPlan*) const;

  Date getOperationPlanDate(const LoadPlan*, Date, bool = true) const;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDurationField<Cls>(Tags::offset, &Cls::getOffset, &Cls::setOffset);
  }

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;

  Duration getOffset() const { return offset; }

  void setOffset(Duration d) {
    if (d < Duration(0L))
      logger << "Warning: Load offset must be positive" << endl;
    else
      offset = d;
  }

 private:
  Duration offset;
};

/* Represents the (independent) demand in the system. It can represent a
 * customer order or a forecast.
 *
 * This is an abstract class.
 */
class Demand : public HasHierarchy<Demand>,
               public Plannable,
               public HasDescription {
  friend class Item;

 public:
  static const unsigned short STATUS_QUOTE = 1;
  static const unsigned short STATUS_INQUIRY = 2;
  static const unsigned short STATUS_OPEN = 4;
  static const unsigned short STATUS_CLOSED = 16;
  static const unsigned short STATUS_CANCELED = 32;
  static const unsigned short POLICY_INDEPENDENT = 64;
  static const unsigned short POLICY_ALLTOGETHER = 128;
  static const unsigned short POLICY_INRATIO = 256;
  static const unsigned short HIDDEN = 512;

  typedef forward_list<OperationPlan*> OperationPlanList;

  class DeliveryIterator {
   private:
    OperationPlanList::const_iterator cur;
    OperationPlanList::const_iterator end;

   public:
    /* Constructor. */
    DeliveryIterator(const Demand* d)
        : cur(d->getDelivery().begin()), end(d->getDelivery().end()) {}

    /* Return current value and advance the iterator. */
    OperationPlan* next() {
      if (cur == end) return nullptr;
      OperationPlan* tmp = *cur;
      ++cur;
      return tmp;
    }
  };

  /* Default constructor. */
  explicit Demand() {}

  /* Destructor.
   * Deleting the demand will also delete all delivery operation
   * plans (including locked ones).
   */
  virtual ~Demand();

  /* Return the memory size. */
  virtual size_t getSize() const {
    auto tmp = Object::getSize() + sizeof(list<OperationPlan*>);
    // Add the memory for the list of deliveries: 2 pointers per delivery
    for (auto iter = deli.begin(); iter != deli.end(); ++iter)
      tmp += 2 * sizeof(OperationPlan*);
    return tmp;
  }

  /* Returns the quantity of the demand. */
  virtual double getQuantity() const { return qty; }

  /* Updates the quantity of the demand. The quantity must be be greater
   * than or equal to 0. */
  virtual void setQuantity(double);

  /* Returns the priority of the demand.
   * Lower numbers indicate a higher priority level.
   */
  virtual int getPriority() const { return prio; }

  /* Updates the priority of the forecast.
   * Lower numbers indicate a higher priority level.
   */
  virtual void setPriority(int i) {
    prio = i;
    setChanged();
  }

  /* Returns the item/product being requested. */
  Item* getItem() const { return it; }

  /* Update the item being requested. */
  virtual void setItem(Item*);

  /* Returns the location where the demand is shipped from. */
  Location* getLocation() const { return loc; }

  /* Update the location where the demand is shipped from. */
  void setLocation(Location* l) {
    if (loc == l) return;
    if (oper && oper->getHidden()) {
      oper = uninitializedDelivery;
      HasLevel::triggerLazyRecomputation();
    }
    loc = l;
    setChanged();
  }

  /* Update the location where the demand is shipped from.
   * This method does not trigger level or problem recalculation.
   */
  void setLocationNoRecalc(Location* l) {
    loc = l;
    oper = uninitializedDelivery;
  }

  /* This fields points to an operation that is to be used to plan the
   * demand. By default, the field is left to nullptr and the demand will then
   * be planned using the delivery operation of its item.
   * @see Item::getDelivery()
   */
  Operation* getOperation() const {
    if (oper == uninitializedDelivery)
      return nullptr;
    else
      return oper;
  }

  /* Updates the operation being used to plan the demand. */
  virtual void setOperation(Operation* o) {
    if (oper == o) return;
    oper = o;
    setChanged();
  }

  /* This function returns the operation that is to be used to satisfy this
   * demand. In sequence of priority this goes as follows:
   *   1) If the "operation" field on the demand is explicitly set, use it.
   *   2) Otherwise, use the "delivery" field of the requested item, if
   *      that field is explicitly set.
   *   3) Otherwise, we try creating a new delivery.
   *      a) Location specified
   *         Search a buffer for the requested item and location. If found
   *         create a delivery operation consuming from it.
   *         If not found create a new buffer.
   *      b) No location specified.
   *         If only a single location exists in the model, use that
   *         to use the same logic as in case a.
   *         If multiple locations exist, we can't resolve the case.
   *   4) If the previous step fails, return nullptr.
   *      This demand can't be satisfied!
   */
  Operation* getDeliveryOperation() const;

  /* Returns the cluster which this demand belongs to. */
  virtual int getCluster() const {
    auto o = getDeliveryOperation();
    return o ? o->getCluster() : 0;
  }

  /* Returns the delivery operationplan list. */
  const OperationPlanList& getDelivery() const;

  DeliveryIterator getOperationPlans() const { return DeliveryIterator(this); }

  /* Return the status. */
  unsigned short getStatus() const {
    return flags &
           (STATUS_CLOSED + STATUS_INQUIRY + STATUS_OPEN + STATUS_QUOTE);
  }

  /* Update the status. */
  void setStatus(unsigned int s) {
    if (s & STATUS_OPEN) {
      flags &=
          ~(STATUS_QUOTE + STATUS_INQUIRY + STATUS_CLOSED + STATUS_CANCELED);
      flags |= STATUS_OPEN;
    } else if (s & STATUS_CLOSED) {
      flags &= ~(STATUS_QUOTE + STATUS_INQUIRY + STATUS_OPEN + STATUS_CANCELED);
      flags |= STATUS_CLOSED;
      deleteOperationPlans();
    } else if (s & STATUS_QUOTE) {
      flags &=
          ~(STATUS_OPEN + STATUS_INQUIRY + STATUS_CLOSED + STATUS_CANCELED);
      flags |= STATUS_QUOTE;
    } else if (s & STATUS_INQUIRY) {
      flags &= ~(STATUS_QUOTE + STATUS_OPEN + STATUS_CLOSED + STATUS_CANCELED);
      flags |= STATUS_INQUIRY;
    } else if (s & STATUS_CANCELED) {
      flags &= ~(STATUS_OPEN + STATUS_QUOTE + STATUS_INQUIRY + STATUS_CLOSED);
      flags |= STATUS_CANCELED;
      deleteOperationPlans();
    } else {
      logger << "Warning: Demand status not recognized" << endl;
      return;
    }
    setChanged();
  }

  /* Return the status as a string. */
  string getStatusString() const {
    if (flags & STATUS_OPEN)
      return "open";
    else if (flags & STATUS_QUOTE)
      return "quote";
    else if (flags & STATUS_INQUIRY)
      return "inquiry";
    else if (flags & STATUS_CLOSED)
      return "closed";
    else if (flags & STATUS_CANCELED)
      return "canceled";
    else
      throw LogicException("Demand status not recognized");
  }

  /* Update the demand status from a string. */
  void setStatusString(const string& s) {
    if (s == "open" || s.empty()) {
      flags &=
          ~(STATUS_QUOTE + STATUS_INQUIRY + STATUS_CLOSED + STATUS_CANCELED);
      flags |= STATUS_OPEN;
    } else if (s == "closed") {
      flags &= ~(STATUS_QUOTE + STATUS_INQUIRY + STATUS_OPEN + STATUS_CANCELED);
      flags |= STATUS_CLOSED;
      deleteOperationPlans();
    } else if (s == "quote") {
      flags &=
          ~(STATUS_OPEN + STATUS_INQUIRY + STATUS_CLOSED + STATUS_CANCELED);
      flags |= STATUS_QUOTE;
    } else if (s == "inquiry") {
      flags &= ~(STATUS_QUOTE + STATUS_OPEN + STATUS_CLOSED + STATUS_CANCELED);
      flags |= STATUS_INQUIRY;
    } else if (s == "canceled") {
      flags &= ~(STATUS_OPEN + STATUS_QUOTE + STATUS_INQUIRY + STATUS_CLOSED);
      flags |= STATUS_CANCELED;
      deleteOperationPlans();
    } else {
      logger << "Warning: Demand status not recognized" << endl;
      return;
    }
    setChanged();
  }

  PooledString getBatch() const { return batch; }

  const string& getBatchString() const { return batch; }

  void setBatch(const string& s) { batch = s; }

  void setBatch(const PooledString& s) { batch = s; }

  /* Return a pointer to the next demand for the same item. */
  Demand* getNextItemDemand() const { return nextItemDemand; }

  /* Returns the latest delivery operationplan. */
  OperationPlan* getLatestDelivery() const;

  /* Returns the earliest delivery operationplan. */
  OperationPlan* getEarliestDelivery() const;

  /* Adds a delivery operationplan for this demand. */
  void addDelivery(OperationPlan* o);

  /* Removes a delivery operationplan for this demand. */
  void removeDelivery(OperationPlan* o);

  /* Deletes all delivery operationplans of this demand.
   * The (optional) boolean parameter controls whether we delete also locked
   * operationplans or not.
   * The second (optional) argument is a command list that can be used to
   * remove the operationplans in an undo-able way.
   */
  void deleteOperationPlans(bool deleteLockedOpplans = false,
                            CommandManager* = nullptr);

  /* Python method for adding a constraint. */
  static PyObject* addConstraint(PyObject*, PyObject*, PyObject*);

  /* Returns the due date of the demand. */
  virtual Date getDue() const { return dueDate; }

  /* Updates the due date of the demand. */
  virtual void setDue(Date d) {
    dueDate = d;
    setChanged();
  }

  /* Returns the customer. */
  Customer* getCustomer() const { return cust; }

  /* Updates the customer. */
  virtual void setCustomer(Customer* c) {
    if (cust) cust->decNumberOfDemands();
    cust = c;
    if (cust) cust->incNumberOfDemands();
    setChanged();
  }

  /* Return a reference to the constraint list. */
  const Problem::List& getConstraints() const { return constraints; }

  /* Return a reference to the constraint list. */
  Problem::List& getConstraints() { return constraints; }

  /* Return an iterator over the constraints encountered when planning
   * this demand. */
  Problem::List::iterator getConstraintIterator() const;

  /* Returns the total amount that has been planned. */
  double getPlannedQuantity() const;

  /* Return an iterator over the problems of this demand. */
  Problem::List::iterator getProblemIterator() const;

  static int initialize();

  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  /* Return the maximum delay allowed in satisfying this demand.
   * The default value is infinite.
   */
  Duration getMaxLateness() const { return maxLateness; }

  /* Updates the maximum allowed lateness for this demand.
   * The default value is infinite.
   * The argument must be a positive time period.
   */
  virtual void setMaxLateness(Duration m) {
    if (m < 0L)
      logger << "Warning: The maximum demand lateness must be positive" << endl;
    else
      maxLateness = m;
  }

  /* Return the minimum shipment quantity allowed in satisfying this
   * demand.
   * The default value is -1.0. In this case we apply a minimum shipment
   * such that we have at most "DefaultMaxShipments" partial deliveries.
   */
  double getMinShipment() const {
    if (minShipment >= 0.0)
      // Explicitly set value of the field
      return minShipment;
    else
      // Automatically suggest a value
      return floor(getQuantity() / DefaultMaxShipments);
  }

  double getRawMinShipment() const { return minShipment; }

  bool isMinShipmentDefault() const { return minShipment == -1.0; }

  /* Updates the maximum allowed lateness for this demand.
   * The default value is infinite.
   * The argument must be a positive time period.
   */
  virtual void setMinShipment(double m) {
    if (m < 0.0 && m != -1.0)
      logger << "Warning: The minimum demand shipment quantity must be positive"
             << endl;
    else
      minShipment = m;
  }

  /* Recompute the problems. */
  virtual void updateProblems();

  /* Specifies whether of not this demand is to be hidden from
   * serialization. The default value is false. */
  void setHidden(bool b) {
    if (b)
      flags |= HIDDEN;
    else
      flags &= ~HIDDEN;
  }

  /* Returns true if this demand is to be hidden from serialization. */
  bool getHidden() const { return flags & HIDDEN; }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  PeggingIterator getPegging() const;

  PeggingIterator getPeggingFirstLevel() const;

  /* Return the latest delivery date for the demand. */
  Date getDeliveryDate() const {
    OperationPlan* op = getLatestDelivery();
    return op ? op->getEnd() : Date::infiniteFuture;
  }

  /* Return the delay of the latest delivery compared to the due date. */
  Duration getDelay() const {
    OperationPlan* op = getLatestDelivery();
    return (op ? op->getEnd() : Date::infiniteFuture) - getDue();
  }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    HasHierarchy<Cls>::template registerFields<Cls>(m);
    HasDescription::registerFields<Cls>(m);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity,
                           &Cls::setQuantity);
    m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem,
                                  BASE + WRITE_OBJECT_SVC);
    m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation,
                                      &Cls::setLocation);
    m->addPointerField<Cls, Customer>(Tags::customer, &Cls::getCustomer,
                                      &Cls::setCustomer,
                                      BASE + WRITE_OBJECT_SVC);
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       &Cls::setOperation);
    Plannable::registerFields<Cls>(m);
    m->addDateField<Cls>(Tags::due, &Cls::getDue, &Cls::setDue);
    m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
    m->addDurationField<Cls>(Tags::maxlateness, &Cls::getMaxLateness,
                             &Cls::setMaxLateness, Duration(5L * 365L * 86400L),
                             BASE + PLAN);
    m->addStringField<Cls>(Tags::status, &Cls::getStatusString,
                           &Cls::setStatusString, "open");
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden,
                         BOOL_FALSE, DONT_SERIALIZE);
    m->addIteratorClassField<Cls, PeggingIterator>(
        Tags::pegging, Tags::pegging, &Cls::getPegging, PLAN + WRITE_OBJECT);
    m->addIteratorClassField<Cls, PeggingIterator>(
        Tags::pegging_first_level, Tags::pegging, &Cls::getPeggingFirstLevel,
        PLAN + WRITE_OBJECT);
    m->addIteratorField<Cls, DeliveryIterator, OperationPlan>(
        Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans,
        DETAIL + WRITE_OBJECT + WRITE_HIDDEN);
    m->addIteratorField<Cls, Problem::List::iterator, Problem>(
        Tags::constraints, Tags::problem, &Cls::getConstraintIterator, PLAN);
    m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0,
                        DONT_SERIALIZE);
    m->addPointerField<Cls, Operation>(Tags::delivery_operation,
                                       &Cls::getDeliveryOperation, nullptr,
                                       DONT_SERIALIZE);
    m->addDurationField<Cls>(Tags::delay, &Cls::getDelay, nullptr, -999L, PLAN);
    m->addDateField<Cls>(Tags::delivery, &Cls::getDeliveryDate, nullptr,
                         Date::infiniteFuture, PLAN);
    m->addDoubleField<Cls>(Tags::planned_quantity, &Cls::getPlannedQuantity,
                           nullptr, -1.0, PLAN);
    m->addStringRefField<Cls>(Tags::batch, &Cls::getBatchString,
                              &Cls::setBatch);
  }

 private:
  static OperationFixedTime* uninitializedDelivery;

  /* Maximum number of partial shipments we use by default.
   * Unless the user specified a value for the minshipments field, we use
   * this default to compute a minshipment value.
   */
  static const int DefaultMaxShipments = 10;

  /* Requested item. */
  Item* it = nullptr;

  /* Location. */
  Location* loc = nullptr;

  /* Delivery Operation. Can be left nullptr, in which case the delivery
   * operation can be specified on the requested item. */
  Operation* oper = uninitializedDelivery;

  /* Customer creating this demand. */
  Customer* cust = nullptr;

  /* Requested quantity. Only positive numbers are allowed. */
  double qty = 0.0;

  /* Due date. */
  Date dueDate;

  /* Maximum lateness allowed when planning this demand.
   * The default value is 5 years.
   */
  Duration maxLateness = Duration(5L * 365L * 86400L);

  /* Minimum size for a delivery operation plan satisfying this demand. */
  double minShipment = -1.0;

  /* A list of operation plans to deliver this demand.
   * The list is sorted by the end date of the deliveries. The sorting is
   * done lazily in the getDelivery() method.
   */
  OperationPlanList deli;

  /* A list of constraints preventing this demand from being planned in
   * full and on time. */
  Problem::List constraints;

  /* A linked list with all demands of an item. */
  Demand* nextItemDemand = nullptr;

  /* Priority. Lower numbers indicate a higher priority level.*/
  int prio = 0;

  /* Batch name */
  PooledString batch;

 protected:
  unsigned short flags = STATUS_OPEN + POLICY_INDEPENDENT;
};

class Item::demandIterator {
 private:
  Demand* cur;

 public:
  /* Constructor. */
  demandIterator(const Item* i) : cur(i ? i->firstItemDemand : nullptr) {}

  bool operator!=(const demandIterator& b) const { return b.cur != cur; }

  bool operator==(const demandIterator& b) const { return b.cur == cur; }

  demandIterator& operator++() {
    if (cur) cur = cur->getNextItemDemand();
    return *this;
  }

  demandIterator operator++(int) {
    demandIterator tmp = *this;
    ++*this;
    return tmp;
  }

  Demand* next() {
    Demand* tmp = cur;
    if (cur) cur = cur->getNextItemDemand();
    return tmp;
  }

  Demand* operator->() const { return cur; }

  Demand& operator*() const { return *cur; }
};

inline Item::demandIterator Item::getDemandIterator() const { return this; }

/* This class is the default implementation of the abstract
 * Demand class. */
class DemandDefault : public Demand {
 public:
  explicit DemandDefault() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDoubleField<Cls>(Tags::minshipment, &Cls::getMinShipment,
                           &Cls::setMinShipment, -1, BASE + PLAN,
                           &Cls::isMinShipmentDefault);
  }
};

class DemandGroup : public Demand {
 public:
  explicit DemandGroup() { initType(metadata); }

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();

  unsigned short getPolicy() const {
    return flags & (POLICY_ALLTOGETHER + POLICY_INDEPENDENT + POLICY_INRATIO);
  }

  string getPolicyString() const {
    if (flags & POLICY_INDEPENDENT)
      return "independent";
    else if (flags & POLICY_ALLTOGETHER)
      return "alltogether";
    else if (flags & POLICY_INRATIO)
      return "inratio";
    else
      throw LogicException("Demand policy not recognized");
  }

  void setPolicyString(const string& s) {
    if (s == "independent" || s.empty()) {
      flags &= ~(POLICY_ALLTOGETHER + POLICY_INRATIO);
      flags |= POLICY_INDEPENDENT;
    } else if (s == "alltogether") {
      flags &= ~(POLICY_INDEPENDENT + POLICY_INRATIO);
      flags |= POLICY_ALLTOGETHER;
    } else if (s == "inratio") {
      flags &= ~(POLICY_ALLTOGETHER + POLICY_INDEPENDENT);
      flags |= POLICY_INRATIO;
    } else {
      logger << "Warning: Demand policy not recognized" << endl;
      return;
    }
    setChanged();
  }

  virtual int getCluster() const {
    auto firstmember = getFirstChild();
    if (!firstmember) return 0;
    auto dlvr = firstmember->getDeliveryOperation();
    return dlvr ? dlvr->getCluster() : 0;
  }

  virtual double getQuantity() const { return 0.0; }

  virtual int getPriority() const;

  virtual void setPriority(int i);

  virtual Date getDue() const;

  virtual void setDue(Date d);

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDoubleField<Cls>(Tags::minshipment, &Cls::getMinShipment,
                           &Cls::setMinShipment, -1, BASE + PLAN,
                           &Cls::isMinShipmentDefault);
    m->addStringField<Cls>(Tags::policy, &Cls::getPolicyString,
                           &Cls::setPolicyString, "independent");
  }
};

/* This class represents the resource capacity of an operationplan.
 *
 * For both the start and the end date of the operationplan, a loadplan
 * object is created. These are then inserted in the timeline structure
 * associated with a resource.
 */
class LoadPlan : public TimeLine<LoadPlan>::EventChangeOnhand {
  friend class OperationPlan::LoadPlanIterator;

 public:
  // Forward declarations
  class AlternateIterator;

  /* Public constructor.
   * This constructor constructs the starting loadplan and will
   * also call a private constructor to creates the ending loadplan.
   * In other words, a single call to the constructor will create
   * two loadplan objects.
   */
  explicit LoadPlan(OperationPlan*, const Load*, Resource* = nullptr);

  explicit LoadPlan(OperationPlan*, SetupEvent*, bool start = true);

  /* Return the operationplan owning this loadplan. */
  virtual OperationPlan* getOperationPlan() const { return oper; }

  /* Return the operation. */
  Operation* getOperation() const { return oper->getOperation(); }

  /* Return the start date of the operationplan. */
  Date getStartDate() const { return oper->getStart(); }

  /* Return the start date of the operationplan. */
  Date getEndDate() const { return ld ? oper->getEnd() : oper->getSetupEnd(); }

  /* Return the load of which this is a plan instance. */
  Load* getLoad() const { return ld; }

  /* Update the resource.
   * The optional second argument specifies whether or not we need to verify
   * if the assigned resource is valid. A valid resource must a) be a
   * subresource of the resource specified on the load, and b) must also
   * have the skill specified on the resource.
   */
  void setResource(Resource* res) { setResource(res, true); }

  /* Update the resource.
   * The optional second argument specifies whether or not we need to verify
   * if the assigned resource is valid. A valid resource must a) be a
   * subresource of the resource specified on the load, and b) must also
   * have the skill specified on the resource.
   */
  void setResource(Resource* res, bool check, bool use_start = true);

  /* Return the resource. */
  Resource* getResource() const { return res; }

  /* Update the load of an already existing flowplan.
   * The new load must belong to the same operation.
   */
  void setLoad(Load*);

  /* Return true when this loadplan marks the start of an operationplan. */
  bool isStart() const { return (flags & TYPE_END) == 0; }

  /* Return the status of the operationplanresource.
   * The status string is one of the following:
   *   - proposed: when the owning operationplan has the status proposed
   *   - confirmed: for all other situations
   */
  string getStatus() const;

  /* Update the status of the operationplanresource. */
  void setStatus(const string&);

  /* Destructor. */
  virtual ~LoadPlan();

  /* This function needs to be called whenever the loadplan date or
   * quantity are changed.
   */
  void update();

  /* Return a pointer to the timeline data structure owning this loadplan. */
  TimeLine<LoadPlan>* getTimeLine() const { return &(res->loadplans); }

  /* Returns the current setup of the resource. */
  string getSetup() const {
    auto tmp = getSetup(true);
    return tmp ? tmp->getSetup().getString() : "";
  }

  /* Returns the required setup for the operation. */
  const string& getSetupLoad() const {
    if (getLoad())
      return getLoad()->getSetup();
    else
      return PooledString::nullstring;
  }

  /* Returns the current setup of the resource.
   * When the argument is true the setup of this loadplan is returned.
   * When the argument is false the setup just before the loadplan is returned.
   */
  SetupEvent* getSetup(bool) const;

  bool isSetupOnly() const { return getLoad() == nullptr; }

  /* Returns true when the loadplan is hidden.
   * This is determined by looking at whether the load is hidden or not.
   */
  bool getHidden() const {
    return getQuantity() < 0 || (getLoad() && getLoad()->getHidden());
  }

  bool getFeasible() const;

  /* Override the setQuantity of the TimeLine class, this is needed for the
   * registerFields function.
   */
  void setQuantity(double quantity) {
    if (getProposed()) return;
    getResource()->getLoadPlans().update(this, quantity, getDate());
    auto t = getOtherLoadPlan();
    if (t) getResource()->getLoadPlans().update(t, -quantity, t->getDate());
  }

  void setOperationPlan(OperationPlan* o) {
    if (oper && oper != o)
      logger << "Warning: Can't change the operationplan of a loadplan" << endl;
    else
      oper = o;
  }

  /* Each operationplan on a default resource has 2 loadplans per load:
   *  - one at the start, when the capacity consumption starts
   *  - one at the end, when the capacity consumption ends
   */
  LoadPlan* getOtherLoadPlan() const { return otherLoadPlan; }

  /* Auxilary method for bucketized resources.
   * Returns the date and onhand at the end of this bucket.
   */
  tuple<double, Date, double> getBucketEnd() const;

  /* Auxilary method for bucketized resources.
   * Returns starting date and quantity of this bucket.
   */
  tuple<double, Date, double> getBucketStart() const;

  inline AlternateIterator getAlternates() const;

  static int initialize();
  static const MetaCategory* metacategory;
  static const MetaClass* metadata;
  virtual const MetaClass& getType() const { return *metadata; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addIteratorField<Cls, AlternateIterator, Resource>(
        Tags::alternates, Tags::alternate, "AlternateResourceIterator",
        "Iterator over loadplan alternates", &Cls::getAlternates,
        PLAN + FORCE_BASE);
    m->addDateField<Cls>(Tags::date, &Cls::getDate);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity,
                           &Cls::setQuantity);
    m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnhand);
    m->addDoubleField<Cls>(Tags::minimum, &Cls::getMin);
    m->addDoubleField<Cls>(Tags::maximum, &Cls::getMax);
    m->addStringField<Cls>(Tags::status, &Cls::getStatus, &Cls::setStatus,
                           "proposed");
    m->addPointerField<Cls, OperationPlan>(
        Tags::operationplan, &Cls::getOperationPlan, &Cls::setOperationPlan,
        BASE + PARENT);
    m->addPointerField<Cls, Load>(Tags::load, &Cls::getLoad, &Cls::setLoad,
                                  DONT_SERIALIZE);
    m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource,
                                      &Cls::setResource, BASE);
    m->addPointerField<Cls, Resource>(Tags::alternate, &Cls::getResource,
                                      &Cls::setResource, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::setuponly, &Cls::isSetupOnly, nullptr,
                         BOOL_FALSE);
    m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, nullptr, BOOL_FALSE,
                         DONT_SERIALIZE);
    m->addDateField<Cls>(Tags::startdate, &Cls::getStartDate, nullptr,
                         Date::infiniteFuture, DONT_SERIALIZE);
    m->addDateField<Cls>(Tags::enddate, &Cls::getEndDate, nullptr,
                         Date::infiniteFuture, DONT_SERIALIZE);
    m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation,
                                       nullptr, DONT_SERIALIZE);
    m->addStringRefField<Cls>(Tags::setup, &Cls::getSetupLoad, nullptr, "",
                              PLAN);
  }

  /* Finds the loadplan on the operationplan when we read data. */
  static Object* reader(const MetaClass*, const DataValueDict&,
                        CommandManager* = nullptr);

  bool getProposed() const {
    return (flags & (STATUS_CONFIRMED + STATUS_CLOSED)) == 0;
  }

  void setProposed(bool b) {
    if (b)
      flags &= ~(STATUS_CLOSED + STATUS_CONFIRMED);
    else {
      flags |= STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    }
  }

  bool getConfirmed() const { return (flags & STATUS_CONFIRMED) != 0; }

  void setConfirmed(bool b) {
    if (b) {
      flags |= STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    } else {
      flags &= ~STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    }
  }

  bool getClosed() const { return (flags & STATUS_CLOSED) != 0; }

  void setClosed(bool b) {
    if (b) {
      flags &= ~STATUS_CONFIRMED;
      flags |= STATUS_CLOSED;
    } else {
      flags |= ~STATUS_CONFIRMED;
      flags &= ~STATUS_CLOSED;
    }
  }

 private:
  /* Private constructor. It is called from the public constructor.
   * The public constructor constructs the starting loadplan, while this
   * constructor creates the ending loadplan.
   */
  LoadPlan(OperationPlan*, const Load*, LoadPlan*);

  /* A pointer to the load model.
   * Watch out: This pointer is null for loadplans of a setup resource!
   */
  Load* ld = nullptr;

  /* A pointer to the selected resource.
   * In case we use skills, the resource of the loadplan can be different
   * than the resource on the load.
   */
  Resource* res;

  /* A pointer to the operationplan owning this loadplan. */
  OperationPlan* oper;

  /* Points to the next loadplan owned by the same operationplan. */
  LoadPlan* nextLoadPlan;

  /* Points to the other half of a loadplan pair. */
  LoadPlan* otherLoadPlan = nullptr;

  /* flag bits. */
  static const unsigned short STATUS_CONFIRMED = 1;
  static const unsigned short STATUS_CLOSED = 2;
  static const unsigned short TYPE_END = 4;
  unsigned short flags = 0;

  /* Factory method. */
  static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
};

inline Date SetupEvent::getLoadplanDate(const LoadPlan* lp) const {
  return lp->isStart() ? opplan->getStart() : opplan->getSetupEnd();
}

inline double SetupEvent::getLoadplanQuantity(const LoadPlan* lp) const {
  return lp->isStart() ? 1 : -1;
};

/* This class allows iteration over alternate resources for a loadplan. */
class LoadPlan::AlternateIterator {
 private:
  const LoadPlan* ldplan;
  vector<Resource*> resources;
  vector<Resource*>::iterator resIter;

 public:
  AlternateIterator(const LoadPlan*);

  AlternateIterator(const AlternateIterator&& other)
      : ldplan(other.ldplan), resources(move(other.resources)) {
    resIter = resources.begin();
  }

  /* Copy constructor. */
  AlternateIterator(const AlternateIterator& other) : ldplan(other.ldplan) {
    for (auto& i : other.resources) resources.push_back(i);
    resIter = resources.begin();
  }

  /* Copy assignment operator. */
  AlternateIterator& operator=(const AlternateIterator& other) {
    resources.clear();
    for (auto& i : other.resources) resources.push_back(i);
    resIter = resources.begin();
    return *this;
  }

  Resource* next();
};

inline LoadPlan::AlternateIterator LoadPlan::getAlternates() const {
  return LoadPlan::AlternateIterator(this);
}

class Resource::OperationPlanIterator {
 private:
  Resource::loadplanlist::const_iterator iter;

 public:
  /* Constructor. */
  OperationPlanIterator(const Resource* r) : iter(r->getLoadPlanIterator()) {}

  /* Return current value and advance the iterator. */
  OperationPlan* next() {
    Resource::loadplanlist::Event* i = iter.next();
    while (i && i->getEventType() == 1 && i->getQuantity() <= 0)
      i = iter.next();
    return i ? i->getOperationPlan() : nullptr;
  }
};

inline Resource::OperationPlanIterator Resource::getOperationPlans() const {
  return Resource::OperationPlanIterator(this);
}

/* This class models a iterator that walks over all available
 * HasProblem entities.
 *
 * This class hard-codes the subclasses that are implementing HasProblems.
 * It's not ideal, but we don't have an explicit container of the objects
 * (and we don't want one either) and this allows us also to re-use the
 * sorting used for the container classes.
 */
class HasProblems::EntityIterator {
 private:
  /* This union contains iterators through the different entity types.
   * Only one of the different iterators will be active at a time, and
   * can thus save memory by collapsing the iterators into a single
   * union. */
  union {
    Buffer::iterator* bufIter;
    Resource::iterator* resIter;
    OperationPlan::iterator* operIter;
    Demand::iterator* demIter;
    Operation::iterator* opIter;
  };

  /* This type indicates which type of entity we are currently recursing
   * through.
   *  - 0: buffers
   *  - 1: resources
   *  - 2: operationplans
   *  - 3: demands
   *  - 4: operations
   */
  unsigned short type;

 public:
  /* Default constructor, which creates an iterator to the first
   * HasProblems object. */
  explicit EntityIterator();

  /* Used to create an iterator pointing beyond the last HasProblems
   * object. */
  explicit EntityIterator(unsigned short i) : bufIter(nullptr), type(i) {}

  /* Copy constructor. */
  EntityIterator(const EntityIterator&);

  /* Assignment operator. */
  EntityIterator& operator=(const EntityIterator&);

  /* Destructor. */
  ~EntityIterator();

  /* Pre-increment operator. */
  EntityIterator& operator++();

  /* Inequality operator.
   * Two iterators are different when they point to different objects.
   */
  bool operator!=(const EntityIterator& t) const;

  /* Equality operator.
   * Two iterators are equal when they point to the same object.
   */
  bool operator==(const EntityIterator& t) const { return !(*this != t); }

  /* Dereference operator. */
  HasProblems& operator*() const;

  /* Dereference operator. */
  HasProblems* operator->() const;
};

/* This class models an STL-like iterator that allows us to iterate
 * over the named entities in a simple and safe way.
 *
 * Objects of this class are returned by the begin() and end() functions.
 * @see Problem::begin()
 * @see Problem::begin(HasProblem*)
 * @see Problem::end()
 */
class Problem::iterator {
  friend class Problem;

 protected:
  /* A pointer to the current problem. If this pointer is nullptr, we are
   * at the end of the list. */
  Problem* iter = nullptr;
  const HasProblems* owner = nullptr;
  HasProblems::EntityIterator* eiter = nullptr;

 public:
  /* Creates an iterator that will loop through the problems of a
   * single entity only.
   * This constructor is also used to create a end-iterator, when passed
   * a nullptr pointer as argument.
   */
  explicit iterator(const HasProblems* o)
      : iter(o ? o->firstProblem : nullptr), owner(o) {}

  /* Creates an iterator that will loop through the constraints of
   * a demand.
   */
  explicit iterator(Problem* o) : iter(o) {}

  /* Creates an iterator that will loop through the problems of all
   * entities. */
  explicit iterator() {
    // Update problems
    Plannable::computeProblems();

    // Loop till we find an entity with a problem
    eiter = new HasProblems::EntityIterator();
    while (*eiter != HasProblems::endEntity() && !((*eiter)->firstProblem))
      ++(*eiter);
    // Found a first problem, or no problem at all
    iter =
        (*eiter != HasProblems::endEntity()) ? (*eiter)->firstProblem : nullptr;
  }

  /* Copy constructor. */
  iterator(const iterator& i) : iter(i.iter), owner(i.owner) {
    if (i.eiter)
      eiter = new HasProblems::EntityIterator(*(i.eiter));
    else
      eiter = nullptr;
  }

  /* Copy assignment operator. */
  iterator& operator=(const iterator& i) {
    if (eiter) delete eiter;
    iter = i.iter;
    owner = i.owner;
    if (i.eiter)
      eiter = new HasProblems::EntityIterator(*(i.eiter));
    else
      eiter = nullptr;
    return *this;
  }

  /* Destructor. */
  virtual ~iterator() {
    if (eiter) delete eiter;
  }

  /* Pre-increment operator. */
  virtual iterator& operator++();

  /* Return current problem and advance the iterator. */
  Problem* next() {
    Problem* tmp = iter;
    operator++();
    return tmp;
  }

  /* Inequality operator. */
  bool operator!=(const iterator& t) const { return iter != t.iter; }

  /* Equality operator. */
  bool operator==(const iterator& t) const { return iter == t.iter; }

  Problem& operator*() const { return *iter; }

  Problem* operator->() const { return iter; }
};

/* Retrieve an iterator for the list. */
inline Problem::iterator Problem::List::begin() const {
  return Problem::iterator(first);
}

/* Stop iterator. */
inline Problem::iterator Problem::List::end() const {
  return Problem::iterator(static_cast<Problem*>(nullptr));
}

class OperationPlan::ProblemIterator : public Problem::iterator {
 private:
  vector<Problem*> relatedproblems;
  const OperationPlan* opplan;

 public:
  /* Constructor. */
  ProblemIterator(const OperationPlan*, bool include_related = true);

  /* Advance the iterator. */
  ProblemIterator& operator++();
};

inline OperationPlan::ProblemIterator OperationPlan::getProblems() const {
  const_cast<OperationPlan*>(this)->updateProblems();
  return OperationPlan::ProblemIterator(this);
}

/* This is the (logical) top class of the complete model.
 *
 * This is a singleton class: only a single instance can be created.
 * The data model has other limitations that make it not obvious to support
 * building multiple models/plans in memory of the same application: e.g.
 * the operations, resources, problems, operationplans... etc are all
 * implemented in static, global lists. An entity can't be simply linked with
 * a particular plan if multiple ones would exist.
 */
class Plan : public Plannable, public Object {
 private:
  /* Current Date of this plan. */
  Date cur_Date;

  /* Current Date for the forecast of this plan. */
  Date fcst_cur_Date;

  /* A name for this plan. */
  string name;

  /* A getDescription of this plan. */
  string descr;

  /* A calendar to which all operationplans will align. */
  Calendar* cal = nullptr;

  Duration autofence;

  bool completed_allow_future = false;

  bool wip_produce_full_quantity = false;

  string dbconnection;

  /* Defines the behavior of operator pools. A load with quantity 2 for
   * an aggregate resource pool can mean either:
   * - find a resource with size 2 in the pool. Default behavior.
   * - find 2 resources of size 1 in the pool.
   */
  bool individual_pool_resources = false;

  bool suppress_flowplan_creation = false;

  bool minimal_before_current_constraints = false;

  string timezone;

  /* Pointer to the singleton plan object. */
  static Plan* thePlan;

  /* The only constructor of this class is made private. An object of this
   * class is created by the instance() member function.
   */
  Plan() : cur_Date(Date::now()) { initType(metadata); }

  static PyObject* setBaseClass(PyObject*, PyObject*);

 public:
  /* Return a pointer to the singleton plan object.
   * The singleton object is created during the initialization of the
   * library.
   */
  static Plan& instance() { return *thePlan; }

  /* Destructor.
   * @warning In multi threaded applications, the destructor is never called
   * and the plan object leaks when we exit the application.
   * In single-threaded applications this function is called properly, when
   * the static plan variable is deleted.
   */
  ~Plan();

  /* Returns the plan name. */
  const string& getName() const { return name; }

  /* Updates the plan name. */
  void setName(const string& s) { name = s; }

  /* Returns the current date of the plan. */
  Date getCurrent() const { return cur_Date; }

  /* Updates the current date of the plan. This method can be relatively
   * heavy in a plan where operationplans already exist, since the
   * detection for BeforeCurrent problems needs to be rerun.
   */
  void setCurrent(Date);

  /* Returns the current date of the plan for the forecast solver. */
  Date getFcstCurrent() const { return fcst_cur_Date; }

  /* Updates the current date of the forecast plan
   */
  void setFcstCurrent(Date);

  string getTimeZone() const { return timezone; }

  void setTimeZone(const string& s) { timezone = s; }

  Duration getAutoFence() const { return autofence; }

  /* the time we wait for existing confirmed supply before
   * triggering a new replenishment.
   */
  void setAutoFence(Duration l) {
    if (l < 0L)
      logger << "Warning: Invalid autofence" << endl;
    else
      autofence = l;
  }

  Duration getDeliveryDuration() const {
    return OperationDelivery::getDeliveryDuration();
  }

  void setDeliveryDuration(Duration l) {
    OperationDelivery::setDeliveryDuration(l);
  }

  /* Returns the description of the plan. */
  const string& getDescription() const { return descr; }

  /* Updates the description of the plan. */
  void setDescription(const string& str) { descr = str; }

  const string& getDBconnection() const { return dbconnection; }

  void setDBconnection(const string& str) { dbconnection = str; }

  bool getCompletedAllowFuture() const { return completed_allow_future; }

  void setCompletedAllowFuture(bool b) { completed_allow_future = b; }

  bool getWipProduceFullQuantity() const { return wip_produce_full_quantity; }

  void setWipProduceFullQuantity(bool b) { wip_produce_full_quantity = b; }

  bool getIndividualPoolResources() const { return individual_pool_resources; }

  void setIndividualPoolResources(bool b) { individual_pool_resources = b; }

  bool getSuppressFlowplanCreation() const {
    return suppress_flowplan_creation;
  }

  void setSuppressFlowplanCreation(bool b);

  bool getMinimalBeforeCurrentConstraints() const {
    return minimal_before_current_constraints;
  }

  void setMinimalBeforeCurrentConstraints(bool b) {
    minimal_before_current_constraints = b;
  }

  void setLogFile(const string& s) { Environment::setLogFile(s); }

  const string& getLogFile() const { return Environment::getLogFile(); }

  /* Initialize the class. */
  static int initialize();

  virtual void updateProblems() {};

  /* This method basically solves the whole planning problem. */
  virtual void solve(Solver& s, void* v = nullptr) const { s.solve(this, v); }

  Location::iterator getLocations() const { return Location::begin(); }

  Customer::iterator getCustomers() const { return Customer::begin(); }

  Supplier::iterator getSuppliers() const { return Supplier::begin(); }

  Calendar::iterator getCalendars() const { return Calendar::begin(); }

  Operation::iterator getOperations() const { return Operation::begin(); }

  Item::iterator getItems() const { return Item::begin(); }

  Buffer::iterator getBuffers() const { return Buffer::begin(); }

  Demand::iterator getDemands() const { return Demand::begin(); }

  SetupMatrix::iterator getSetupMatrices() const {
    return SetupMatrix::begin();
  }

  Skill::iterator getSkills() const { return Skill::begin(); }

  Resource::iterator getResources() const { return Resource::begin(); }

  Problem::iterator getProblems() const { return Problem::iterator(); }

  OperationPlan::iterator getOperationPlans() const {
    return OperationPlan::iterator();
  }

  unsigned long getOperationPlanCounterMin() const {
    return OperationPlan::getCounterMin();
  }

  void setOperationPlanCounterMin(unsigned long l) {
    OperationPlan::setCounterMin(l);
  }

  unsigned long getloglimit() const { return Environment::getloglimit(); }

  void setloglimit(unsigned long l) { Environment::setloglimit(l); }

  const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static const MetaCategory* metacategory;

  void erase(const string& e);

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Plan>(Tags::name, &Plan::getName, &Plan::setName);
    m->addDurationField<Plan>(Tags::autofence, &Plan::getAutoFence,
                              &Plan::setAutoFence);
    m->addDurationField<Plan>(Tags::deliveryduration,
                              &Plan::getDeliveryDuration,
                              &Plan::setDeliveryDuration);
    m->addStringRefField<Plan>(Tags::description, &Plan::getDescription,
                               &Plan::setDescription);
    m->addStringRefField<Plan>(Tags::dbconnection, &Plan::getDBconnection,
                               &Plan::setDBconnection);
    m->addDateField<Plan>(Tags::current, &Plan::getCurrent, &Plan::setCurrent);
    m->addDateField<Plan>(Tags::fcst_current, &Plan::getFcstCurrent,
                          &Plan::setFcstCurrent);
    m->addStringRefField<Plan>(Tags::logfile, &Plan::getLogFile,
                               &Plan::setLogFile, "", DONT_SERIALIZE);
    m->addUnsignedLongField(Tags::loglimit, &Plan::getloglimit,
                            &Plan::setloglimit, 0UL, DONT_SERIALIZE);
    m->addUnsignedLongField(Tags::id, &Plan::getOperationPlanCounterMin,
                            &Plan::setOperationPlanCounterMin, 0UL,
                            DONT_SERIALIZE);
    m->addBoolField<Plan>(
        Tags::completed_allow_future, &Plan::getCompletedAllowFuture,
        &Plan::setCompletedAllowFuture, BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Plan>(
        Tags::wip_produce_full_quantity, &Plan::getWipProduceFullQuantity,
        &Plan::setWipProduceFullQuantity, BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(
        Tags::individualPoolResources, &Cls::getIndividualPoolResources,
        &Cls::setIndividualPoolResources, BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(
        Tags::suppressFlowplanCreation, &Cls::getSuppressFlowplanCreation,
        &Cls::setSuppressFlowplanCreation, BOOL_FALSE, DONT_SERIALIZE);
    m->addBoolField<Cls>(Tags::minimalBeforeCurrentConstraints,
                         &Cls::getMinimalBeforeCurrentConstraints,
                         &Cls::setMinimalBeforeCurrentConstraints, BOOL_FALSE,
                         DONT_SERIALIZE);
    m->addStringField<Cls>(Tags::timezone, &Cls::getTimeZone, &Cls::setTimeZone,
                           "", DONT_SERIALIZE);
    Plannable::registerFields<Plan>(m);
    m->addIteratorField<Plan, Location::iterator, Location>(
        Tags::locations, Tags::location, &Plan::getLocations,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Customer::iterator, Customer>(
        Tags::customers, Tags::customer, &Plan::getCustomers,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Supplier::iterator, Supplier>(
        Tags::suppliers, Tags::supplier, &Plan::getSuppliers,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Calendar::iterator, Calendar>(
        Tags::calendars, Tags::calendar, &Plan::getCalendars,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Resource::iterator, Resource>(
        Tags::resources, Tags::resource, &Plan::getResources,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Item::iterator, Item>(
        Tags::items, Tags::item, &Plan::getItems, BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Buffer::iterator, Buffer>(
        Tags::buffers, Tags::buffer, &Plan::getBuffers, BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Operation::iterator, Operation>(
        Tags::operations, Tags::operation, &Plan::getOperations,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Demand::iterator, Demand>(
        Tags::demands, Tags::demand, &Plan::getDemands, BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, SetupMatrix::iterator, SetupMatrix>(
        Tags::setupmatrices, Tags::setupmatrix, &Plan::getSetupMatrices,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Skill::iterator, Skill>(
        Tags::skills, Tags::skill, &Plan::getSkills, BASE + WRITE_OBJECT);
    m->addIteratorField<Plan, Resource::skilllist::iterator, ResourceSkill>(
        Tags::resourceskills, Tags::resourceskill);  // Only for XML import
    m->addIteratorField<Plan, Operation::loadlist::iterator, Load>(
        Tags::loads, Tags::load);  // Only for XML import
    m->addIteratorField<Plan, Operation::flowlist::iterator, Flow>(
        Tags::flows, Tags::flow);  // Only for XML import
    m->addIteratorField<Plan, Item::supplierlist::iterator, ItemSupplier>(
        Tags::itemsuppliers, Tags::itemsupplier);  // Only for XML import
    m->addIteratorField<Plan, Location::distributionlist::iterator,
                        ItemDistribution>(
        Tags::itemdistributions,
        Tags::itemdistribution);  // Only for XML import
    m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(
        Tags::operationplans, Tags::operationplan, &Plan::getOperationPlans,
        BASE + WRITE_OBJECT);
    m->addIteratorField<Cls, Problem::iterator, Problem>(
        Tags::problems, Tags::problem, &Plan::getProblems, DONT_SERIALIZE);
    m->addCommandField<Cls>(Tags::erase, &Plan::erase);
  }
};

/* A problem of this class is created when an operationplan is being
 * planned in the past, i.e. it starts before the "current" date of
 * the plan.
 */
class ProblemBeforeCurrent : public Problem {
 public:
  string getDescription() const {
    ostringstream ch;
    ch << "Operation '"
       << (oper ? oper
                : static_cast<OperationPlan*>(getOwner())->getOperation())
       << "' planned in the past";
    return ch.str();
  }

  bool isFeasible() const {
    return oper ? false
                : static_cast<OperationPlan*>(getOwner())->getConfirmed();
  }

  double getWeight() const {
    return oper ? qty : static_cast<OperationPlan*>(getOwner())->getQuantity();
  }

  explicit ProblemBeforeCurrent(OperationPlan* o, bool add = true)
      : Problem(o) {
    if (add) addProblem();
  }

  explicit ProblemBeforeCurrent(Operation* o, Date st, Date nd, double q)
      : oper(o), start(st), end(nd), qty(q) {}

  ~ProblemBeforeCurrent() { removeProblem(); }

  string getEntity() const { return "operation"; }

  Object* getOwner() const {
    return oper ? static_cast<Object*>(oper)
                : static_cast<OperationPlan*>(owner);
  }

  const DateRange getDates() const {
    if (oper) return DateRange(start, end);
    OperationPlan* o = static_cast<OperationPlan*>(getOwner());
    if (o->getConfirmed())
      return DateRange(o->getEnd(), Plan::instance().getCurrent());
    else {
      if (o->getEnd() > Plan::instance().getCurrent())
        return DateRange(o->getStart(), Plan::instance().getCurrent());
      else
        return o->getDates();
    }
  }

  void update(Operation* o, Date st, Date nd, double q) {
    oper = o;
    start = st;
    end = nd;
    qty = q;
  }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  Operation* oper = nullptr;
  Date start;
  Date end;
  double qty = 0;
};

/* A problem of this class is created when an operationplan is being
 * planned before its fence date, i.e. it starts 1) before the "current"
 * date of the plan plus the release fence of the operation and 2) after the
 * current date of the plan.
 */
class ProblemBeforeFence : public Problem {
 public:
  string getDescription() const {
    ostringstream ch;
    ch << "Operation '"
       << (oper ? oper
                : static_cast<OperationPlan*>(getOwner())->getOperation())
       << "' planned before fence";
    return ch.str();
  }

  bool isFeasible() const { return true; }

  double getWeight() const {
    return oper ? qty : static_cast<OperationPlan*>(getOwner())->getQuantity();
  }

  explicit ProblemBeforeFence(OperationPlan* o, bool add = true) : Problem(o) {
    if (add) addProblem();
  }

  explicit ProblemBeforeFence(Operation* o, Date st, Date nd, double q)
      : oper(o), start(st), end(nd), qty(q) {}

  ~ProblemBeforeFence() { removeProblem(); }

  string getEntity() const { return "operation"; }

  Object* getOwner() const {
    return oper ? static_cast<Object*>(oper)
                : static_cast<OperationPlan*>(owner);
  }

  const DateRange getDates() const {
    if (oper) return DateRange(start, end);
    OperationPlan* o = static_cast<OperationPlan*>(owner);
    auto tmp = o->getOperation()->getFence(o);
    if (o->getEnd() > tmp)
      return DateRange(o->getStart(), tmp);
    else
      return o->getDates();
  }

  void update(Operation* o, Date st, Date nd, double q) {
    oper = o;
    start = st;
    end = nd;
    qty = q;
  }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  Operation* oper = nullptr;
  Date start;
  Date end;
  double qty = 0.0;
};

/* An instance of this class is used to flag constraints where a
 * replenishment isn't created and we wait for later supply instead.
 */
class ProblemAwaitSupply : public Problem {
 public:
  string getDescription() const {
    ostringstream ch;
    if (for_buffer)
      ch << "Buffer '" << static_cast<Buffer*>(getOwner());
    else
      ch << "Operation  '" << static_cast<Operation*>(getOwner());
    ch << "' awaits confirmed supply";
    return ch.str();
  }

  bool isFeasible() const { return true; }

  double getWeight() const { return qty; }

  explicit ProblemAwaitSupply(Buffer* b, Date st, Date nd, double q)
      : Problem(b), dates(st, nd), qty(q), for_buffer(true) {}

  explicit ProblemAwaitSupply(Operation* b, Date st, Date nd, double q)
      : Problem(b), dates(st, nd), qty(q), for_buffer(false) {}

  ~ProblemAwaitSupply() { removeProblem(); }

  string getEntity() const { return "material"; }

  Object* getOwner() const {
    if (for_buffer)
      return static_cast<Buffer*>(owner);
    else
      return static_cast<Operation*>(owner);
  }

  const DateRange getDates() const { return dates; }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  DateRange dates;
  double qty = 0.0;
  bool for_buffer;
};

/* An instance of this class is used to flag constraints where a
 * demand isn't planned because the delivery needs to be synchronized with
 * other demands in the same group.
 */
class ProblemSyncDemand : public Problem {
 public:
  string getDescription() const {
    ostringstream ch;
    ch << "Demand '" << static_cast<Demand*>(getOwner())
       << "' is synchronized with " << synced_with;
    return ch.str();
  }

  bool isFeasible() const { return true; }

  double getWeight() const { return 1; }

  explicit ProblemSyncDemand(Demand* b, Date st, Date nd, double q)
      : synced_with(b), dates(st, nd) {}

  explicit ProblemSyncDemand(Demand* b, Demand* s)
      : Problem(b), synced_with(s) {
    if (b) dates.setStartAndEnd(b->getDue(), b->getDeliveryDate());
  }

  ~ProblemSyncDemand() { removeProblem(); }

  string getEntity() const { return "demand"; }

  Object* getOwner() const { return static_cast<Demand*>(owner); }

  const DateRange getDates() const { return dates; }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  Demand* synced_with = nullptr;
  DateRange dates;
};

/* A problem of this class is created when the sequence of two
 * operationplans in a routing isn't respected.
 */
class ProblemPrecedence : public Problem {
 public:
  string getDescription() const {
    OperationPlan* o = static_cast<OperationPlan*>(getOwner());
    return string("Operation '") + o->getOperation()->getName() +
           "' starts before preceding operation ends";
  }

  bool isFeasible() const { return false; }

  /* The weight of the problem is equal to the duration in days. */
  double getWeight() const {
    return static_cast<double>(getDates().getDuration()) / 86400;
  }

  explicit ProblemPrecedence(OperationPlan* o, bool add = true) : Problem(o) {
    if (add) addProblem();
  }

  ~ProblemPrecedence() { removeProblem(); }

  string getEntity() const { return "operation"; }

  Object* getOwner() const { return static_cast<OperationPlan*>(owner); }

  const DateRange getDates() const {
    auto o = static_cast<OperationPlan*>(getOwner());
    if (o->getNextSubOpplan())
      return DateRange(o->getNextSubOpplan()->getStart(), o->getEnd());
    else
      return DateRange(o->getEnd(), o->getEnd());
  }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;
};

/* A Problem of this class is created in the model when a new demand is
 * brought in the system, but it hasn't been planned yet.
 *
 * As a special case, a demand with a requested quantity of 0.0 doesn't create
 * this type of problem.
 */
class ProblemDemandNotPlanned : public Problem {
 public:
  string getDescription() const {
    return string("Demand '") + getDemand()->getName() + "' is not planned";
  }

  bool isFeasible() const { return false; }

  double getWeight() const { return getDemand()->getQuantity(); }

  explicit ProblemDemandNotPlanned(Demand* d, bool add = true) : Problem(d) {
    if (add) addProblem();
  }

  ~ProblemDemandNotPlanned() { removeProblem(); }

  string getEntity() const { return "demand"; }

  const DateRange getDates() const {
    return DateRange(getDemand()->getDue(), getDemand()->getDue());
  }

  Object* getOwner() const { return static_cast<Demand*>(owner); }

  Demand* getDemand() const { return static_cast<Demand*>(owner); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;
};

/* A problem of this class is created when a demand is satisfied later
 * than the accepted tolerance after its due date.
 */
class ProblemLate : public Problem {
 public:
  string getDescription() const;
  bool isFeasible() const { return true; }

  /* The weight is quantity that is delivered late.
   * It doesn't matter how much it is delayed.
   */
  double getWeight() const {
    double tmp = getDemand()->getQuantity();
    for (auto dlvr = getDemand()->getDelivery().begin();
         dlvr != getDemand()->getDelivery().end(); ++dlvr)
      if ((*dlvr)->getEnd() <= getDemand()->getDue())
        tmp -= (*dlvr)->getQuantity();
    return tmp;
  }

  /* Constructor. */
  explicit ProblemLate(Demand* d, bool add = true) : Problem(d) {
    if (add) addProblem();
  }

  /* Destructor. */
  ~ProblemLate() { removeProblem(); }

  const DateRange getDates() const {
    assert(getDemand() && !getDemand()->getDelivery().empty());
    return DateRange(getDemand()->getDue(),
                     getDemand()->getLatestDelivery()->getEnd());
  }

  Demand* getDemand() const { return static_cast<Demand*>(getOwner()); }

  string getEntity() const { return "demand"; }

  Object* getOwner() const { return static_cast<Demand*>(owner); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;
};

/* A problem of this class is created when a demand is planned earlier
 * than the accepted tolerance before its due date.
 */
class ProblemEarly : public Problem {
 public:
  string getDescription() const;

  bool isFeasible() const { return true; }

  double getWeight() const {
    assert(getDemand() && !getDemand()->getDelivery().empty());
    return static_cast<double>(
               DateRange(getDemand()->getDue(),
                         getDemand()->getEarliestDelivery()->getEnd())
                   .getDuration()) /
           86400;
  }

  explicit ProblemEarly(Demand* d, bool add = true) : Problem(d) {
    if (add) addProblem();
  }

  ~ProblemEarly() { removeProblem(); }

  string getEntity() const { return "demand"; }

  Object* getOwner() const { return static_cast<Demand*>(owner); }

  const DateRange getDates() const {
    assert(getDemand() && !getDemand()->getDelivery().empty());
    return DateRange(getDemand()->getDue(),
                     getDemand()->getEarliestDelivery()->getEnd());
  }

  Demand* getDemand() const { return static_cast<Demand*>(getOwner()); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;
};

/* A Problem of this class is created in the model when a data exception
 * prevents planning of certain objects
 */
class ProblemInvalidData : public Problem {
 public:
  string getDescription() const { return description; }

  bool isFeasible() const { return false; }

  double getWeight() const { return qty; }

  explicit ProblemInvalidData(HasProblems* o, const string& d, const string& e,
                              Date st, Date nd, double q, bool add = true)
      : Problem(o), description(d), entity(e), dates(st, nd), qty(q) {
    if (add) addProblem();
  }

  ~ProblemInvalidData() { removeProblem(); }

  string getEntity() const { return entity; }

  const DateRange getDates() const { return dates; }

  Object* getOwner() const {
    if (entity == "demand") return static_cast<Demand*>(owner);
    if (entity == "buffer" || entity == "material")
      return static_cast<Buffer*>(owner);
    if (entity == "resource" || entity == "capacity")
      return static_cast<Resource*>(owner);
    if (entity == "operation") return static_cast<Operation*>(owner);
    if (entity == "operationplan") return static_cast<OperationPlan*>(owner);
    throw LogicException("Unknown problem entity type");
  }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  /* Description of the data issue. */
  string description;
  string entity;
  DateRange dates;
  double qty;
};

/* A problem of this class is created when a demand is planned for less
 * than the requested quantity.
 */
class ProblemShort : public Problem {
 public:
  string getDescription() const {
    ostringstream ch;
    ch << "Demand '" << getDemand()->getName() << "' planned "
       << (getDemand()->getQuantity() - getDemand()->getPlannedQuantity())
       << " units short";
    return ch.str();
  }

  bool isFeasible() const { return true; }

  double getWeight() const {
    return getDemand()->getQuantity() - getDemand()->getPlannedQuantity();
  }

  explicit ProblemShort(Demand* d, bool add = true) : Problem(d) {
    if (add) addProblem();
  }

  ~ProblemShort() { removeProblem(); }

  string getEntity() const { return "demand"; }

  const DateRange getDates() const {
    return DateRange(getDemand()->getDue(), getDemand()->getDue());
  }

  Object* getOwner() const { return static_cast<Demand*>(owner); }

  Demand* getDemand() const { return static_cast<Demand*>(owner); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;
};

/* A problem of this class is created when a demand is planned for more
 * than the requested quantity.
 */
class ProblemExcess : public Problem {
 public:
  string getDescription() const {
    ostringstream ch;
    ch << "Demand '" << getDemand()->getName() << "' planned "
       << (getDemand()->getPlannedQuantity() - getDemand()->getQuantity())
       << " units excess";
    return ch.str();
  }

  bool isFeasible() const { return true; }

  double getWeight() const {
    return getDemand()->getPlannedQuantity() - getDemand()->getQuantity();
  }

  explicit ProblemExcess(Demand* d, bool add = true) : Problem(d) {
    if (add) addProblem();
  }

  string getEntity() const { return "demand"; }

  Object* getOwner() const { return static_cast<Demand*>(owner); }

  ~ProblemExcess() { removeProblem(); }

  const DateRange getDates() const {
    return DateRange(getDemand()->getDue(), getDemand()->getDue());
  }

  Demand* getDemand() const { return static_cast<Demand*>(getOwner()); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;
};

/* A problem of this class is created when a resource is being
 * overloaded during a certain period of time.
 */
class ProblemCapacityOverload : public Problem {
 public:
  string getDescription() const;

  bool isFeasible() const { return false; }

  double getWeight() const { return qty; }

  ProblemCapacityOverload(Resource* r, Date st, Date nd, double q,
                          bool add = true)
      : Problem(r), qty(q), dr(st, nd) {
    if (add) addProblem();
  }

  ~ProblemCapacityOverload() { removeProblem(); }

  string getEntity() const { return "capacity"; }

  Object* getOwner() const { return static_cast<Resource*>(owner); }

  const DateRange getDates() const { return dr; }

  Resource* getResource() const { return static_cast<Resource*>(getOwner()); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  /* Overload quantity. */
  double qty;

  /* The daterange of the problem. */
  DateRange dr;
};

/* A problem of this class is created when a resource is loaded below
 * its minimum during a certain period of time.
 */
class ProblemCapacityUnderload : public Problem {
 public:
  string getDescription() const;

  bool isFeasible() const { return true; }

  double getWeight() const { return qty; }

  ProblemCapacityUnderload(Resource* r, DateRange d, double q, bool add = true)
      : Problem(r), qty(q), dr(d) {
    if (add) addProblem();
  }

  ~ProblemCapacityUnderload() { removeProblem(); }

  string getEntity() const { return "capacity"; }

  Object* getOwner() const { return static_cast<Resource*>(owner); }

  const DateRange getDates() const { return dr; }

  Resource* getResource() const { return static_cast<Resource*>(getOwner()); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  /* Underload quantity. */
  double qty;

  /* The daterange of the problem. */
  DateRange dr;
};

/* A problem of this class is created when a buffer is having a
 * material shortage during a certain period of time.
 */
class ProblemMaterialShortage : public Problem {
 public:
  string getDescription() const;

  bool isFeasible() const { return false; }

  double getWeight() const { return qty; }

  ProblemMaterialShortage(Buffer* b, Date st, Date nd, double q,
                          bool add = true)
      : Problem(b), qty(q), dr(st, nd) {
    if (add) addProblem();
  }

  string getEntity() const { return "material"; }

  Object* getOwner() const { return static_cast<Buffer*>(owner); }

  ~ProblemMaterialShortage() { removeProblem(); }

  const DateRange getDates() const { return dr; }

  Buffer* getBuffer() const { return static_cast<Buffer*>(getOwner()); }

  /* Return a reference to the metadata structure. */
  const MetaClass& getType() const { return *metadata; }

  /* Storing metadata on this class. */
  static const MetaClass* metadata;

 private:
  /* Shortage quantity. */
  double qty;

  /* The daterange of the problem. */
  DateRange dr;
};

/* This command is used to create an operationplan.
 *
 * The operationplan will have its loadplans and flowplans created when the
 * command is created. It is assigned an id and added to the list of all
 * operationplans when the command is committed.
 */
class CommandCreateOperationPlan : public Command {
 public:
  /* Constructor. */
  CommandCreateOperationPlan(const Operation* o, double q, Date d1, Date d2,
                             Demand* l, const PooledString& batch,
                             OperationPlan* ow = nullptr,
                             bool makeflowsloads = true,
                             bool roundDown = true) {
    opplan = o ? o->createOperationPlan(q, d1, d2, batch, l, ow, makeflowsloads,
                                        roundDown)
               : nullptr;
  }

  void commit() {
    if (opplan) {
      opplan->activate();
      opplan = nullptr;  // Avoid executing / initializing more than once
    }
  }

  virtual void rollback() {
    delete opplan;
    opplan = nullptr;
  }

  virtual ~CommandCreateOperationPlan() {
    if (opplan) delete opplan;
  }

  OperationPlan* getOperationPlan() const { return opplan; }

  virtual short getType() const { return 5; }

 private:
  /* Pointer to the newly created operationplan. */
  OperationPlan* opplan;
};

/* This command is used to delete an operationplan.
 * The implementation assumes there is only a single level of child
 * sub operationplans.
 */
class CommandDeleteOperationPlan : public Command {
 public:
  /* Constructor. */
  CommandDeleteOperationPlan(OperationPlan* o);

  virtual void commit() {
    if (opplan) delete opplan;
    opplan = nullptr;
  }

  virtual void rollback() {
    if (opplan) {
      opplan->createFlowLoads();
      opplan->insertInOperationplanList();
      if (opplan->getDemand()) opplan->getDemand()->addDelivery(opplan);
      OperationPlan::iterator x(opplan);
      while (OperationPlan* i = x.next()) {
        // TODO the recreation of the flows and loads can recreate them on a
        // different resource from the pool. This results in a different
        // resource loading, setup time and duration.
        i->createFlowLoads();
        i->insertInOperationplanList();
      }
    }
    opplan = nullptr;
  }

  virtual ~CommandDeleteOperationPlan() { rollback(); }

  virtual short getType() const { return 6; }

 private:
  /* Pointer to the operationplan being deleted.
   * Until the command is committed we don't deallocate the memory for the
   * operationplan, but only remove all pointers to it from various places.
   */
  OperationPlan* opplan;
};

/* This class represents the command of moving an operationplan to a
 * new date and/or resizing it.
 * @todo Moving in a routing operation can't be undone with the current
 * implementation! The command will need to store all original dates of
 * the suboperationplans...
 */
class CommandMoveOperationPlan : public Command {
 public:
  /* Constructor.
   * Unlike most other commands the constructor already executes the change.
   * @param opplanptr Pointer to the operationplan being moved.
   * @param newStart New start date of the operationplan.
   * @param newEnd New end date of the operationplan.
   * @param newQty New quantity of the operationplan.The default is -1,
   * which indicates to leave the quantity unchanged.
   */
  CommandMoveOperationPlan(OperationPlan* opplanptr, Date newStart, Date newEnd,
                           double newQty = -1.0, bool roundDown = false,
                           bool later = false);

  /* Default constructor. */
  CommandMoveOperationPlan(OperationPlan*);

  /* Commit the changes. */
  virtual void commit() {
    opplan->mergeIfPossible();
    opplan = nullptr;
  }

  /* Undo the changes. */
  virtual void rollback() {
    restore(true);
    opplan = nullptr;
  }

  /* Undo the changes.
   * When the argument is true, subcommands for suboperationplans are deleted.
   */
  void restore(bool = false);

  /* Destructor. */
  virtual ~CommandMoveOperationPlan() {
    if (opplan) rollback();
  }

  /* Returns the operationplan being manipulated. */
  OperationPlan* getOperationPlan() const { return opplan; }

  /* Set another start date for the operationplan. */
  void setStart(Date d) {
    if (opplan) opplan->setStart(d);
  }

  /* Set another start date, end date and quantity for the operationplan. */
  void setParameters(Date s, Date e, double q, bool b, bool roundDown = true) {
    assert(opplan->getOperation());
    if (opplan) opplan->setOperationPlanParameters(q, s, e, b, true, roundDown);
  }

  /* Set another start date for the operationplan. */
  void setEnd(Date d) {
    if (opplan) opplan->setEnd(d);
  }

  /* Set another quantity for the operationplan. */
  void setQuantity(double q) {
    if (opplan) opplan->setQuantity(q);
  }

  /* Return the quantity of the original operationplan. */
  double getQuantity() const { return state.quantity; }

  /* Return the dates of the original operationplan. */
  DateRange getDates() const { return DateRange(state.start, state.end); }

  virtual short getType() const { return 7; }

 private:
  /* This is a pointer to the operationplan being moved. */
  OperationPlan* opplan = nullptr;

  /* Store the state of the operation plan. */
  OperationPlanState state;

  /* A pointer to a list of suboperationplan commands. */
  Command* firstCommand = nullptr;
};

/* This class allows upstream and downstream navigation through
 * the plan.
 *
 * Downstream navigation follows the material flow from raw materials
 * towards the produced end item.
 * Upstream navigation traces back the material flow from the end item up to
 * the consumed raw materials.
 * The class is implemented as an STL-like iterator.
 */
class PeggingIterator : public NonCopyable, public Object {
 public:
  /* Assignment operator. */
  PeggingIterator& operator=(const PeggingIterator&);

  /* Constructor for demand pegging. */
  PeggingIterator(const Demand*, short = -1);

  /* Constructor for operationplan pegging, downstream (default) or upstream. */
  PeggingIterator(const OperationPlan*, bool = true, short = -1);

  /* Constructor for flowplan pegging, downstream (default) or upstream. */
  PeggingIterator(const FlowPlan*, bool = true);

  /* Constructor for loadplan pegging, downstream (default) or upstream. */
  PeggingIterator(LoadPlan*, bool = true);

  /* Return the operationplan. */
  OperationPlan* getOperationPlan() const {
    return second_pass
               ? const_cast<OperationPlan*>(states_sorted.front().opplan)
               : const_cast<OperationPlan*>(states.back().opplan);
  }

  Duration getGap() const {
    return second_pass ? states_sorted.front().gap : states.back().gap;
  }

  /* Destructor. */
  virtual ~PeggingIterator() {}

  /* Return true if this is a downstream iterator. */
  inline bool isDownstream() const { return downstream; }

  /* Return the pegged quantity. */
  double getQuantity() const {
    return second_pass ? states_sorted.front().quantity
                       : states.back().quantity;
  }

  /* Return the max level of depth allowed*/
  inline short getMaxLevel() const { return maxlevel; }

  double getOffset() const {
    return second_pass ? states_sorted.front().offset : states.back().offset;
  }

  /* Returns the recursion depth of the iterator.*/
  short getLevel() const {
    return second_pass ? states_sorted.front().level : states.back().level;
  }

  /* Move the iterator downstream. */
  PeggingIterator& operator++();

  /* Move the iterator upstream. */
  PeggingIterator& operator--();

  /* Conversion operator to a boolean value.
   * The return value is true when the iterator still has next elements to
   * explore. Returns false when the iteration is finished.
   */
  operator bool() const {
    return second_pass ? !states_sorted.empty() : !states.empty();
  }

  PeggingIterator* next();

  PyObject* iternext() {
    auto tmp = next();
    if (tmp) Py_IncRef(this);
    return tmp;
  }

  /* Add an entry on the stack. */
  void updateStack(const OperationPlan*, double, double, short, Duration);

  /* Initialize the class. */
  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, OperationPlan>(Tags::operationplan,
                                           &Cls::getOperationPlan, nullptr,
                                           PLAN + WRITE_OBJECT + WRITE_HIDDEN);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, nullptr, -1,
                           MANDATORY);
    m->addShortField<Cls>(Tags::level, &Cls::getLevel, nullptr, -1, MANDATORY);
    m->addDoubleField<Cls>(Tags::offset, &Cls::getOffset, nullptr, -1,
                           MANDATORY);
  }

 private:
  /* This structure is used to keep track of the iterator states during the
   * iteration. */
  struct state {
    const OperationPlan* opplan;
    double quantity;
    double offset;
    short level;
    Duration gap;

    state(){};

    state(const OperationPlan* op, double q, double o, short l, Duration g)
        : opplan(op), quantity(q), offset(o), level(l), gap(g){};

    state(const state& other)
        : opplan(other.opplan),
          quantity(other.quantity),
          offset(other.offset),
          level(other.level),
          gap(other.gap){};

    // Comparison operator
    bool operator<(const state& other) const {
      if (opplan->getStart() == other.opplan->getStart())
        return other.opplan->getEnd() < opplan->getEnd();
      else
        return other.opplan->getStart() < opplan->getStart();
    }
  };

  /* Auxilary function to make recursive code possible. */
  void followPegging(const OperationPlan*, double, double, short);

  static thread_local MemoryPool<state> peggingpool;

  /* Store a list of all operations still to peg. */
  MemoryPool<state>::MemoryObjectList states;
  MemoryPool<state>::MemoryObjectList states_sorted;

  /* Follow the pegging upstream or downstream. */
  bool downstream;

  /* Used by the Python iterator to mark the first call. */
  bool firstIteration;

  /* Optimization to reuse elements on the stack. */
  bool first;
  set<OperationPlan*> visited;

  /* Extra data structure to avoid duplicate operationplan ids in the list. */
  bool second_pass;

  /* The maximum level of depth allowed*/
  short maxlevel;
};

/* An iterator that shows all demands linked to an operationplan. */
class PeggingDemandIterator : public NonCopyable, public Object {
 private:
  typedef map<Demand*, double> demandmap;
  demandmap dmds;
  demandmap::const_iterator iter;
  bool first = true;

  double sumOfIntervals(vector<pair<double, double>>& intervals);

 public:
  /* Constructor. */
  PeggingDemandIterator(const OperationPlan*);

  /* Advance to the next demand. */
  PeggingDemandIterator* next();

  PyObject* iternext() {
    auto tmp = next();
    if (tmp) Py_IncRef(this);
    return tmp;
  }

  /* Initialize the class. */
  static int initialize();

  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaCategory* metadata;

  Demand* getDemand() const {
    return iter != dmds.end() ? iter->first : nullptr;
  }

  double getQuantity() const { return iter != dmds.end() ? iter->second : 0.0; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addPointerField<Cls, Demand>(Tags::demand, &Cls::getDemand, nullptr,
                                    MANDATORY + WRITE_REFERENCE + WRITE_HIDDEN);
    m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, nullptr, -1,
                           MANDATORY);
  }
};

/* An iterator class to go through all flowplans of an operationplan.
 * @see OperationPlan::beginFlowPlans
 * @see OperationPlan::endFlowPlans
 */
class OperationPlan::FlowPlanIterator {
  friend class OperationPlan;

 private:
  FlowPlan* curflowplan = nullptr;
  FlowPlan* prevflowplan = nullptr;

  FlowPlanIterator(FlowPlan* b) : curflowplan(b) {}

 public:
  bool operator!=(const FlowPlanIterator& b) const {
    return b.curflowplan != curflowplan;
  }

  bool operator==(const FlowPlanIterator& b) const {
    return b.curflowplan == curflowplan;
  }

  FlowPlanIterator& operator++() {
    prevflowplan = curflowplan;
    if (curflowplan) curflowplan = curflowplan->nextFlowPlan;
    return *this;
  }

  FlowPlanIterator operator++(int) {
    FlowPlanIterator tmp = *this;
    ++*this;
    return tmp;
  }

  FlowPlan* operator->() const { return curflowplan; }

  FlowPlan& operator*() const { return *curflowplan; }

  void deleteFlowPlan() {
    if (!curflowplan) return;
    if (prevflowplan)
      prevflowplan->nextFlowPlan = curflowplan->nextFlowPlan;
    else
      curflowplan->oper->firstflowplan = curflowplan->nextFlowPlan;
    FlowPlan* tmp = curflowplan;
    // Move the iterator to the next element
    curflowplan = curflowplan->nextFlowPlan;
    delete tmp;
  }

  FlowPlan* next() {
    prevflowplan = curflowplan;
    if (curflowplan) curflowplan = curflowplan->nextFlowPlan;
    return prevflowplan;
  }
};

inline OperationPlan::FlowPlanIterator OperationPlan::beginFlowPlans() const {
  return OperationPlan::FlowPlanIterator(firstflowplan);
}

inline OperationPlan::FlowPlanIterator OperationPlan::endFlowPlans() const {
  return OperationPlan::FlowPlanIterator(nullptr);
}

inline OperationPlan::FlowPlanIterator OperationPlan::getFlowPlans() const {
  return OperationPlan::FlowPlanIterator(firstflowplan);
}

inline int OperationPlan::sizeFlowPlans() const {
  int c = 0;
  for (auto i = beginFlowPlans(); i != endFlowPlans(); ++i) ++c;
  return c;
}

/* An iterator class to go through all loadplans of an operationplan.
 * @see OperationPlan::beginLoadPlans
 * @see OperationPlan::endLoadPlans
 */
class OperationPlan::LoadPlanIterator {
  friend class OperationPlan;

 private:
  LoadPlan* curloadplan = nullptr;
  LoadPlan* prevloadplan = nullptr;
  LoadPlanIterator(LoadPlan* b) : curloadplan(b) {}

 public:
  bool operator!=(const LoadPlanIterator& b) const {
    return b.curloadplan != curloadplan;
  }

  bool operator==(const LoadPlanIterator& b) const {
    return b.curloadplan == curloadplan;
  }

  LoadPlanIterator& operator++() {
    prevloadplan = curloadplan;
    if (curloadplan) curloadplan = curloadplan->nextLoadPlan;
    return *this;
  }

  LoadPlanIterator operator++(int) {
    LoadPlanIterator tmp = *this;
    ++*this;
    return tmp;
  }

  LoadPlan* operator->() const { return curloadplan; }

  LoadPlan& operator*() const { return *curloadplan; }

  void deleteLoadPlan() {
    if (!curloadplan) return;
    if (prevloadplan)
      prevloadplan->nextLoadPlan = curloadplan->nextLoadPlan;
    else
      curloadplan->oper->firstloadplan = curloadplan->nextLoadPlan;
    LoadPlan* tmp = curloadplan;
    // Move the iterator to the next element
    curloadplan = curloadplan->nextLoadPlan;
    delete tmp;
  }

  LoadPlan* next() {
    prevloadplan = curloadplan;
    if (curloadplan) curloadplan = curloadplan->nextLoadPlan;
    return prevloadplan;
  }
};

inline OperationPlan::LoadPlanIterator OperationPlan::beginLoadPlans() const {
  return OperationPlan::LoadPlanIterator(firstloadplan);
}

inline OperationPlan::LoadPlanIterator OperationPlan::endLoadPlans() const {
  return OperationPlan::LoadPlanIterator(nullptr);
}

inline OperationPlan::LoadPlanIterator OperationPlan::getLoadPlans() const {
  return OperationPlan::LoadPlanIterator(firstloadplan);
}

inline int OperationPlan::sizeLoadPlans() const {
  int c = 0;
  for (auto i = beginLoadPlans(); i != endLoadPlans(); ++i) ++c;
  return c;
}

class OperationPlan::InterruptionIterator : public Object {
 private:
  Calendar::EventIterator cals[10];
  unsigned short numCalendars;
  Date curdate;
  const OperationPlan* opplan;
  Date start;
  Date end;
  bool status = false;

 public:
  InterruptionIterator(const OperationPlan* o) : opplan(o) {
    if (!opplan || !opplan->getOperation())
      throw LogicException(
          "Can't initialize an iterator over an uninitialized operationplan");
    numCalendars = opplan->getOperation()->collectCalendars(
        cals, opplan->getStart(), opplan);
    curdate = opplan->getStart();
    start = curdate;
    initType(metadata);
  }

  InterruptionIterator* next();

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addDateField<Cls>(Tags::start, &Cls::getStart);
    m->addDateField<Cls>(Tags::end, &Cls::getEnd);
  }

  Date getStart() const { return start; }

  Date getEnd() const { return end; }

  /* Return a reference to the metadata structure. */
  virtual const MetaClass& getType() const { return *metadata; }

  static int intitialize();
  static const MetaCategory* metacategory;
  static const MetaClass* metadata;
};

inline OperationPlan::InterruptionIterator OperationPlan::getInterruptions()
    const {
  return OperationPlan::InterruptionIterator(this);
}

class CalendarEventIterator : public PythonExtension<CalendarEventIterator> {
 public:
  static int initialize();

  CalendarEventIterator(Calendar* c, Date d = Date::infinitePast, bool f = true)
      : eventiter(c, d, f), forward(f) {}

 private:
  Calendar::EventIterator eventiter;
  bool forward;
  PyObject* iternext();
};

class FlowPlanIterator : public PythonExtension<FlowPlanIterator> {
 public:
  /* Registration of the Python class and its metadata. */
  static int initialize();

  /* Constructor to iterate over the flowplans of a buffer. */
  FlowPlanIterator(Buffer* b) : buf(b), buffer_or_opplan(true) {
    if (!b)
      throw LogicException("Creating flowplan iterator for nullptr buffer");
    bufiter =
        new Buffer::flowplanlist::const_iterator(b->getFlowPlans().begin());
  }

  /* Constructor to iterate over the flowplans of an operationplan. */
  FlowPlanIterator(OperationPlan* o) : opplan(o), buffer_or_opplan(false) {
    if (!o)
      throw LogicException(
          "Creating flowplan iterator for nullptr operationplan");
    opplaniter = new OperationPlan::FlowPlanIterator(o->beginFlowPlans());
  }

  ~FlowPlanIterator() {
    if (buffer_or_opplan)
      delete bufiter;
    else
      delete opplaniter;
  }

 private:
  union {
    Buffer* buf;
    OperationPlan* opplan;
  };

  union {
    Buffer::flowplanlist::const_iterator* bufiter;
    OperationPlan::FlowPlanIterator* opplaniter;
  };

  /* Flags whether we are browsing over the flowplans in a buffer or in an
   * operationplan. */
  bool buffer_or_opplan;

  PyObject* iternext();
};

class LoadPlanIterator : public PythonExtension<LoadPlanIterator> {
 public:
  static int initialize();

  LoadPlanIterator(Resource* r) : res(r), resource_or_opplan(true) {
    if (!r)
      throw LogicException("Creating loadplan iterator for nullptr resource");
    resiter =
        new Resource::loadplanlist::const_iterator(r->getLoadPlans().begin());
  }

  LoadPlanIterator(OperationPlan* o) : opplan(o), resource_or_opplan(false) {
    if (!opplan)
      throw LogicException(
          "Creating loadplan iterator for nullptr operationplan");
    opplaniter = new OperationPlan::LoadPlanIterator(o->beginLoadPlans());
  }

  ~LoadPlanIterator() {
    if (resource_or_opplan)
      delete resiter;
    else
      delete opplaniter;
  }

 private:
  union {
    Resource* res;
    OperationPlan* opplan;
  };

  union {
    Resource::loadplanlist::const_iterator* resiter;
    OperationPlan::LoadPlanIterator* opplaniter;
  };

  /* Flags whether we are browsing over the flowplans in a buffer or in an
   * operationplan. */
  bool resource_or_opplan;

  PyObject* iternext();
};

/* This Python function is used for reading XML input.
 *
 * The function takes up to three arguments:
 *   - XML data file to be processed.
 *     If this argument is omitted or None, the standard input is read.
 *   - Optional validate flag, defining whether or not the input data needs to
 * be validated against the XML schema definition. The validation is switched ON
 * by default. Switching it ON is recommended in situations where there is no
 * 100% guarantee on the validity of the input data.
 *   - Optional validate_only flag, which allows us to validate the data but
 *     skip any processing.
 */
PyObject* readXMLfile(PyObject*, PyObject*);

/* This Python function is used for processing XML input data from a
 * string.
 *
 * The function takes up to three arguments:
 *   - XML data string to be processed
 *   - Optional validate flag, defining whether or not the input data needs to
 * be validated against the XML schema definition. The validation is switched ON
 * by default. Switching it ON is recommended in situations where there is no
 * 100% guarantee on the validity of the input data.
 *   - Optional validate_only flag, which allows us to validate the data but
 *     skip any processing.
 *   - Optional loglevel flag, which writes out a verbose trace of the parsing.
 */
PyObject* readXMLdata(PyObject*, PyObject*);

/* This Python function writes the dynamic part of the plan to an text
 * file.
 *
 * This saved information covers the buffer flowplans, operationplans,
 * resource loading, demand, problems, etc...
 * The main use of this function is in the test suite: a simple text file
 * comparison allows us to identify changes quickly. The output format is
 * only to be seen in this context of testing, and is not intended to be used
 * as an official method for publishing plans to other systems.
 */
PyObject* savePlan(PyObject*, PyObject*);

/* This Python function prints a summary of the dynamically allocated
 * memory to the standard output. This is useful for understanding better the
 * size of your model.
 *
 * The numbers reported by this function won't match the memory size as
 * reported by the operating system, since the dynamically allocated memory
 * is only a part of the total memory used by a program.
 */
PyObject* printModelSize(PyObject* self, PyObject* args);

/* This python function writes the complete model to a XML-file.
 *
 * Both the static model (i.e. items, locations, buffers, resources,
 * calendars, etc...) and the dynamic data (i.e. the actual plan including
 * the operationplans, demand, problems, etc...).
 * The format is such that the output file can be re-read to restore the
 * very same model.
 * The function takes the following arguments:
 *   - Name of the output file
 *   - Type of output desired: BASE, PLAN or DETAIL.
 *     The default value is BASE.
 */
PyObject* saveXMLfile(PyObject*, PyObject*);

/* This Python function erases the model or the plan from memory.
 *
 * The function allows the following modes to control what to delete:
 *  - plan:
 *    Deletes the dynamic modelling constructs, such as operationplans,
 *    loadplans and flowplans only. Locked operationplans are not
 *    deleted.
 *    The static model is left intact.
 *    This is the default mode.
 *  - model:
 *    The dynamic as well as the static objects are removed. You'll end
 *    up with a completely empty model.
 *    Due to the logic required in the object destructors this mode doesn't
 *    scale linear with the model size.
 */
PyObject* eraseModel(PyObject* self, PyObject* args);

}  // namespace frepple

#endif
