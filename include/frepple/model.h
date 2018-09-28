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

#pragma once
#ifndef MODEL_H
#define MODEL_H

/** @mainpage
  * FrePPLe provides a framework for modeling a manufacturing environment
  * and generating production plans.<br>
  * This document describes its C++ API.<P>
  *
  * @namespace frepple
  * @brief Core namespace
  */

#include "frepple/utils.h"
#include "frepple/xml.h"
using namespace frepple::utils;

namespace frepple
{

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
class OperationPlan;
class Item;
class ItemSupplier;
class ItemDistribution;
template <class T> class TimeLine;
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


/** @brief This class is used for initialization. */
class LibraryModel
{
  public:
    static void initialize();
};


/** @brief This class represents a time bucket as a part of a calendar.
  *
  * Manipulation of instances of this class need to be handled with the
  * methods on the friend class Calendar.
  * @see Calendar
  */
class CalendarBucket : public Object, public NonCopyable, public HasSource
{
    friend class Calendar;
  private:
    /** Start date of the bucket. */
    Date startdate;

    /** End Date of the bucket. */
    Date enddate = Date::infiniteFuture;

    /** A pointer to the next bucket. */
    CalendarBucket* nextBucket = nullptr;

    /** A pointer to the previous bucket. */
    CalendarBucket* prevBucket = nullptr;

    /** A pointer to the owning calendar. */
    Calendar *cal = nullptr;

    /** Value of this bucket.*/
    double val = 0.0;

    /** Starting time on the effective days. */
    Duration starttime;

    /** Ending time on the effective days. */
    Duration endtime = 86400L;

    /** Priority of this bucket, compared to other buckets effective
      * at a certain time.
      */
    int priority = 0;

    /** Weekdays on which the entry is effective.
      * - Bit 0: Sunday
      * - Bit 1: Monday
      * - Bit 2: Tueday
      * - Bit 3: Wednesday
      * - Bit 4: Thursday
      * - Bit 5: Friday
      * - Bit 6: Saturday
      */
    short days = 127;

    /** Keep all calendar buckets sorted in ascending order of start date
      * and use the priority as a tie breaker.
      */
    void updateSort();

  public:
    /** Default constructor. */
    CalendarBucket()
    {
      initType(metadata);
    }

    /** Destructor. */
    ~CalendarBucket();

    /** This is a factory method that creates a new bucket in a calendar.<br>
      * It uses the calendar and id fields to identify existing buckets.
      */
    static Object* reader(
      const MetaClass*, const DataValueDict&, CommandManager* = nullptr
      );

    /** Update the calendar owning the bucket. */
    void setCalendar(Calendar*);

    /** Return the calendar to whom the bucket belongs. */
    Calendar* getCalendar() const
    {
      return cal;
    }

    /** Returns the value of this bucket. */
    double getValue() const
    {
      return val;
    }

    /** Updates the value of this bucket. */
    void setValue(double v)
    {
      val = v;
    }

    /** Returns the end date of the bucket. */
    Date getEnd() const
    {
      return enddate;
    }

    /** Updates the end date of the bucket. */
    void setEnd(const Date d);

    /** Returns the start date of the bucket. */
    Date getStart() const
    {
      return startdate;
    }

    /** Updates the start date of the bucket. */
    void setStart(const Date d);

    /** Returns the priority of this bucket, compared to other buckets
      * effective at a certain time.<br>
      * Lower numbers indicate a higher priority level.<br>
      * The default value is 0.
      */
    int getPriority() const
    {
      return priority;
    }

    /** Updates the priority of this bucket, compared to other buckets
      * effective at a certain time.<br>
      * Lower numbers indicate a higher priority level.<br>
      * The default value is 0.
      */
    void setPriority(int f)
    {
      priority = f;
      updateSort();
    }

    /** Get the days on which the entry is valid.<br>
      * The value is a bit pattern with bit 0 representing sunday, bit 1
      * monday, ... and bit 6 representing saturday.<br>
      * The default value is 127.
      */
    short getDays() const
    {
      return days;
    }

    /** Update the days on which the entry is valid. */
    void setDays(short p)
    {
      if (p<0 || p>127)
        throw DataException("Calendar bucket days must be between 0 and 127");
      days = p;
    }

    /** Return the time of the day when the entry becomes valid.<br>
      * The default value is 0 or midnight.
      */
    Duration getStartTime() const
    {
      return starttime;
    }

    /** Update the time of the day when the entry becomes valid. */
    void setStartTime(Duration t)
    {
      if (t > 86400L || t < 0L)
        throw DataException("Calendar bucket start time must be between 0 and 86400 seconds");
      starttime = t;
      if (starttime > endtime)
      {
        // Swap the start and end time
        Duration tmp = starttime;
        starttime = endtime;
        endtime = tmp;
      }
    }

    /** Return the time of the day when the entry becomes invalid.<br>
      * The default value is 23h59m59s.
      */
    Duration getEndTime() const
    {
      return endtime;
    }

    /** Update the time of the day when the entry becomes invalid. */
    void setEndTime(Duration t)
    {
      if (t > 86400L || t < 0L)
        throw DataException("Calendar bucket end time must be between 0 and 86400 seconds");
      endtime = t;
      if (starttime > endtime)
      {
        // Swap the start and end time
        Duration tmp = starttime;
        starttime = endtime;
        endtime = tmp;
      }
    }

    /** Convert the value of the bucket to a boolean value. */
    virtual bool getBool() const
    {
      return val != 0;
    }

    /** Returns true if the bucket is continuously effective between
      * its start and end date, in other words it is effective 24 hours
      * a day and 7 days per week.
      */
    bool isContinuouslyEffective() const
    {
      return days == 127 && !starttime && endtime == Duration(86400L);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metacategory;
    static const MetaClass* metadata;
    static int initialize();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDateField<Cls>(Tags::start, &Cls::getStart, &Cls::setStart);
      m->addDateField<Cls>(Tags::end, &Cls::getEnd, &Cls::setEnd, Date::infiniteFuture);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
      m->addShortField<Cls>(Tags::days, &Cls::getDays, &Cls::setDays, 127);
      m->addDurationField<Cls>(Tags::starttime, &Cls::getStartTime, &Cls::setStartTime);
      m->addDurationField<Cls>(Tags::endtime, &Cls::getEndTime, &Cls::setEndTime, 86400L);
      m->addDoubleField<Cls>(Tags::value, &Cls::getValue, &Cls::setValue);
      m->addPointerField<Cls, Calendar>(Tags::calendar, &Cls::getCalendar, &Cls::setCalendar, DONT_SERIALIZE + PARENT);
      HasSource::registerFields<Cls>(m);
    }

  public:
    /** @brief An iterator class to go through all buckets of the calendar. */
    class iterator
    {
      private:
        CalendarBucket* curBucket;

      public:
        iterator(CalendarBucket* b = nullptr) : curBucket(b) {}

        bool operator != (const iterator &b) const
        {
          return b.curBucket != curBucket;
        }

        bool operator == (const iterator &b) const
        {
          return b.curBucket == curBucket;
        }

        iterator& operator++()
        {
          if (curBucket)
            curBucket = curBucket->nextBucket;
          return *this;
        }

        iterator operator++(int)
        {
          iterator tmp = *this;
          ++*this;
          return tmp;
        }

        CalendarBucket *next()
        {
          CalendarBucket *tmp = curBucket;
          if (curBucket)
            curBucket = curBucket->nextBucket;
          return tmp;
        }

        iterator& operator--()
        {
          if(curBucket) curBucket = curBucket->prevBucket;
          return *this;
        }

        iterator operator--(int)
        {
          iterator tmp = *this;
          --*this;
          return tmp;
        }

        CalendarBucket* operator ->() const
        {
          return curBucket;
        }

        CalendarBucket& operator *() const
        {
          return *curBucket;
        }

        static iterator end()
        {
          return nullptr;
        }
    };
};


/** @brief This is the class used to represent variables that are
  * varying over time.
  *
  * Some example usages for calendars:
  *  - A calendar defining the available capacity of a resource
  *    week by week.
  *  - The minimum inventory desired in a buffer week by week.
  *  - The working hours and holidays at a certain location.
  */
class Calendar : public HasName<Calendar>, public HasSource
{
  public:
    class EventIterator; // Forward declaration
    friend class EventIterator;
    friend class CalendarBucket;

    /** Default constructor. */
    explicit Calendar() {}

    /** Destructor, which cleans up the buckets too and all references to the
      * calendar from the core model.
      */
    ~Calendar();

    /** Returns the value on the specified date. */
    double getValue(const Date, bool forward = true) const;

    /** Updates the value in a certain date range.<br>
      * This will create a new bucket if required.
      */
    void setValue(Date start, Date end, const double);

    double getValue(CalendarBucket::iterator& i) const
    {
      return reinterpret_cast<CalendarBucket&>(*i).getValue();
    }

    /** Returns the default calendar value when no entry is matching. */
    double getDefault() const
    {
      return defaultValue;
    }

    /** Convert the value of the calendar to a boolean value. */
    virtual bool getBool() const
    {
      return defaultValue != 0;
    }

    /** Update the default calendar value when no entry is matching. */
    virtual void setDefault(double v)
    {
      defaultValue = v;
    }

    /** Removes a bucket from the list.
      * The first argument is the bucket to remove, and the second argument
      * is a flag indicating whether to delete the bucket or not.
      */
    void removeBucket(CalendarBucket* bckt, bool del = true);

    /** Returns the bucket where a certain date belongs to.
      * A nullptr pointer is returned when no bucket is effective.
      */
    CalendarBucket* findBucket(Date d, bool fwd = true) const;

    /** Add a new bucket to the calendar. */
    CalendarBucket* addBucket(Date, Date, double);

    /** Return the memory size, including the event list. */
    virtual size_t getSize() const
    {
      auto tmp = Object::getSize();
      tmp += (sizeof(pair<Date, double>) + sizeof(void*) * 3) * eventlist.size();
      return tmp;
    }

    /** @brief An iterator class to go through all dates where the calendar
      * value changes.*/
    class EventIterator
    {
      protected:
        map<Date, double>::const_iterator cacheiter;
        Calendar* theCalendar = nullptr;
        Date curDate;
        double curValue = 0.0;
      public:
        const Date& getDate() const
        { 
          return curDate;
        }

        double getValue()
        {
          return curValue;
        }

        const Calendar* getCalendar() const
        {
          return theCalendar;
        }

        EventIterator(
          Calendar* c = nullptr,Date d = Date::infinitePast, bool forward = true
          );

        EventIterator& operator++();

        EventIterator& operator--();

        EventIterator operator++(int)
        {
          EventIterator tmp = *this;
          ++*this;
          return tmp;
        }

        EventIterator operator--(int)
        {
          EventIterator tmp = *this;
          --*this;
          return tmp;
        }
    };

    /** Returns an iterator to go through the list of buckets. */
    CalendarBucket::iterator getBuckets() const
    {
      return CalendarBucket::iterator(firstBucket);
    }

    static PyObject* setPythonValue(PyObject*, PyObject*, PyObject*);

    static int initialize();

    static PyObject* getEvents(PyObject*, PyObject*);

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "", MANDATORY);
      HasSource::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::deflt, &Cls::getDefault, &Cls::setDefault);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addIteratorField<Cls, CalendarBucket::iterator, CalendarBucket>(Tags::buckets, Tags::bucket, &Cls::getBuckets, BASE + WRITE_OBJECT);
    }

    /** Build a list of dates where the calendar value changes.
      * By default we build the list for 1 year before and after the
      * current date.
      * If a date is passed as argument, we build/update a list to include
      * that date.
      */
    void buildEventList(Date include = Date::infinitePast);

    /** Erase the event list (to save memory).
      * The list will be rebuild the next time an iterator is created.
      */
    void clearEventList()
    {
      eventlist.clear();
    }

  protected:
    /** Find the lowest priority of any bucket. */
    int lowestPriority() const
    {
      int min = 0;
      for (CalendarBucket::iterator i = getBuckets(); i != CalendarBucket::iterator::end(); ++i)
        if (i->getPriority() < min) min = i->getPriority();
      return min;
    }

  private:
    /** A pointer to the first bucket. The buckets are stored in a doubly
      * linked list. */
    CalendarBucket* firstBucket = nullptr;

    /** Value used when no bucket is effective at all. */
    double defaultValue = 0.0;

    /** A cached list of all events. */
    map<Date, double> eventlist;
};


/** @brief A calendar storing double values in its buckets. */
class CalendarDefault : public Calendar
{
  public:
    /** Default constructor. */
    explicit CalendarDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief A problem represents infeasibilities, alerts and warnings in
  * the plan.
  *
  * Problems are maintained internally by the system. They are thus only
  * exported, meaning that you can't directly import or create problems.<br>
  * This class is the pure virtual base class for all problem types.<br>
  * The usage of the problem objects is based on the following principles:
  *  - Problems objects are passive. They don't actively change the model
  *    state.
  *  - Objects of the HasProblems class actively create and destroy Problem
  *    objects.
  *  - Problem objects are managed in a 'lazy' way, meaning they only are
  *    getting created when the list of problems is requested by the user.<br>
  *    During normal planning activities we merely mark the planning entities
  *    that have changed, so we can easily pick up which entities to recompute
  *    the problems for. In this way we can avoid the cpu and memory overhead
  *    of keeping the problem list up to date at all times, while still
  *    providing the user with the correct list of problems when required.
  *  - Given the above, problems are lightweight objects that consume
  *    limited memory.
  */
class Problem : public NonCopyable, public Object
{
  public:
    class iterator;
    friend class iterator;
    class List;
    friend class List;

    /** Constructor.<br>
      * Note that this method can't manipulate the problem container, since
      * the problem objects aren't fully constructed yet.
      * @see addProblem
      */
    explicit Problem(HasProblems *p = nullptr) : owner(p)
    {
      initType(metadata);
    }

    /** Initialize the class. */
    static int initialize();

    /** Destructor.
      * @see removeProblem
      */
    virtual ~Problem() {}

    /** Return the category of the problem. */
    string getName() const
    {
      return getType().type;
    }

    /** Returns the duration of this problem. */
    virtual const DateRange getDates() const = 0;

    /** Get the start date of the problem. */
    Date getStart() const
    {
      return getDates().getStart();
    }

    /** Get the start date of the problem. */
    Date getEnd() const
    {
      return getDates().getEnd();
    }

    /** Returns a text description of this problem. */
    virtual string getDescription() const = 0;

    /** Returns the object type having this problem. */
    virtual string getEntity() const = 0;

    /** Returns true if the plan remains feasible even if it contains this
      * problem, i.e. if the problems flags only a warning.
      * Returns false if a certain problem points at an infeasibility of the
      * plan.
      */
    virtual bool isFeasible() const = 0;

    /** Returns a double number reflecting the magnitude of the problem. This
      * allows us to focus on the significant problems and filter out the
      * small ones.
      */
    virtual double getWeight() const = 0;

    PyObject* str() const
    {
      return PythonData(getDescription());
    }

    /** Returns an iterator to the very first problem. The iterator can be
      * incremented till it points past the very last problem. */
    static iterator begin();

    /** Return an iterator to the first problem of this entity. The iterator
      * can be incremented till it points past the last problem of this
      * plannable entity.<br>
      * The boolean argument specifies whether the problems need to be
      * recomputed as part of this method.
      */
    static iterator begin(HasProblems*, bool = true);

    /** Return an iterator pointing beyond the last problem. */
    static const iterator end();

    /** Erases the list of all problems. This methods can be used reduce the
      * memory consumption at critical points. The list of problems will be
      * recreated when the problem detection is triggered again.
      */
    static void clearProblems();

    /** Erases the list of problems linked with a certain plannable object.<br>
      * If the second parameter is set to true, the problems will be
      * recreated when the next problem detection round is triggered.
      */
    static void clearProblems(
      HasProblems& p, bool setchanged = true, bool includeInvalidData = true
      );

    /** Returns a pointer to the object that owns this problem. */
    virtual Object* getOwner() const = 0;

    /** Return a reference to the metadata structure. */
    virtual const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaCategory* metadata;

    /** An internal convenience method to return the next linked problem. */
    Problem* getNextProblem() const
    {
      return nextProblem;
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, nullptr, "", MANDATORY + COMPUTED);
      m->addStringField<Cls>(Tags::description, &Cls::getDescription, nullptr, "", MANDATORY + COMPUTED);
      m->addDateField<Cls>(Tags::start, &Cls::getStart, nullptr, Date::infinitePast, MANDATORY);
      m->addDateField<Cls>(Tags::end, &Cls::getEnd, nullptr, Date::infiniteFuture, MANDATORY);
      m->addDoubleField<Cls>(Tags::weight, &Cls::getWeight, nullptr, 0.0, MANDATORY);
      m->addStringField<Cls>(Tags::entity, &Cls::getEntity, nullptr, "", DONT_SERIALIZE);
      m->addPointerField<Cls, Object>(Tags::owner, &Cls::getOwner, nullptr, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::feasible, &Cls::isFeasible, nullptr, BOOL_UNSET, COMPUTED);
    }
  protected:
    /** Each Problem object references a HasProblem object as its owner. */
    HasProblems *owner = nullptr;

    /** Each Problem contains a pointer to the next pointer for the same
      * owner. This class implements thus an intrusive single linked list
      * of Problem objects. */
    Problem *nextProblem = nullptr;

    /** Adds a newly created problem to the problem container.
      * This method needs to be called in the constructor of a problem
      * subclass. It can't be called from the constructor of the base
      * Problem class, since the object isn't fully created yet and thus
      * misses the proper information used by the compare method.
      * @see removeProblem
      */
    void addProblem();

    /** Removes a problem from the problem container.
      * This method needs to be called from the destructor of a problem
      * subclass.<br>
      * Due to the single linked list data structure, this methods'
      * performance is linear with the number of problems of an entity.
      * This is acceptable since we don't expect entities with a huge amount
      * of problems.
      * @see addproblem
      */
    void removeProblem();

    /** Comparison of 2 problems.<br>
      * To garantuee that the problems are sorted in a consistent and stable
      * way, the following sorting criteria are used (in order of priority):
      * <ol><li>Entity<br>
      *    This sort is to be ensured by the client. This method can't
      *    compare problems of different entities!</li>
      * <li>Type<br>
      *    Each problem type has a hashcode used for sorting.</li>
      * <li>Start date</li></ol>
      * The sorting is expected such that it can be used as a key, i.e. no
      * two problems of will ever evaluate to be identical.
      */
    bool operator < (const Problem& a) const;
};


/** @brief Classes that keep track of problem conditions need to implement
  * this class.
  *
  * This class is closely related to the Problem class.
  * @see Problem
  */
class HasProblems
{
    friend class Problem::iterator;
    friend class Problem;
    friend class Plannable;
    friend class OperationPlan;
  public:
    class EntityIterator;

    /** Returns an iterator pointing to the first HasProblem object. */
    static EntityIterator beginEntity();

    /** Returns an iterator pointing beyond the last HasProblem object. */
    static EntityIterator endEntity();

    /** Constructor. */
    HasProblems() {}

    /** Destructor. It needs to take care of making sure all problems objects
      * are being deleted as well. */
    virtual ~HasProblems()
    {
      Problem::clearProblems(*this, false);
    }

    /** Returns the plannable entity relating to this problem container. */
    virtual Plannable* getEntity() const = 0;

    /** Called to update the list of problems. The function will only be
      * called when:
      *  - the list of problems is being recomputed
      *  - AND, problem detection is enabled for this object
      *  - AND, the object has changed since the last problem computation
      */
    virtual void updateProblems() = 0;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addBoolField<Cls>(Tags::detectproblems, &Cls::getDetectProblems, &Cls::setDetectProblems, BOOL_TRUE);
    }

  private:
    /** A pointer to the first problem of this object. Problems are maintained
      * in a single linked list. */
    Problem* firstProblem = nullptr;
};


/** @brief This auxilary class is used to maintain a list of problem models. */
class Problem::List
{
  public:
    /** Constructor. */
    List() {};

    /** Destructor. */
    ~List()
    {
      clear();
    }

    /** Empty the list.<br>
      * If a problem is passed as argument, that problem and all problems
      * following it in the list are deleted.<br>
      * If no argument is passed, the complete list is erased.
      */
    void clear(Problem * = nullptr);

    /** Add a problem to the list. */
    Problem* push(const MetaClass*, const Object*, Date, Date, double);

    /* Add a problem to the list. */
    void push(Problem* p);

    /** Remove all problems from the list that appear AFTER the one
      * passed as argument. */
    void pop(Problem *);

    /** Get the last problem on the list. */
    Problem* top() const;

    /** Cur the list in two parts . */
    Problem* unlink(Problem* p)
    {
      Problem *tmp = p->nextProblem;
      p->nextProblem = nullptr;
      return tmp;
    }

    /** Returns true if the list is empty. */
    bool empty() const
    {
      return first == nullptr;
    }

    typedef Problem::iterator iterator;

    /** Return an iterator to the start of the list. */
    Problem::iterator begin() const;

    /** End iterator. */
    Problem::iterator end() const;

  private:
    /** Pointer to the head of the list. */
    Problem* first = nullptr;
};


/** @brief This class is an implementation of the "visitor" design pattern.
  * It is intended as a basis for different algorithms processing the frePPLe
  * data.
  *
  * The goal is to decouple the solver/algorithms from the model/data
  * representation. Different solvers can be easily be plugged in to work on
  * the same data.
  */
class Solver : public Object
{
  public:
    /** Constructor. */
    explicit Solver() : loglevel(0) {}

    /** Destructor. */
    virtual ~Solver() {}

    static int initialize();

    static PyObject* solve(PyObject*, PyObject*);

    virtual void solve(void* = nullptr) = 0;

    virtual void solve(const Plan*, void* = nullptr)
    {
      throw LogicException("Called undefined solve(Plan*) method");
    }

    virtual void solve(const Demand*,void* = nullptr)
    {
      throw LogicException("Called undefined solve(Demand*) method");
    }

    virtual void solve(const Operation*,void* = nullptr)
    {
      throw LogicException("Called undefined solve(Operation*) method");
    }

    virtual void solve(const OperationFixedTime* o, void* v = nullptr)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationTimePer* o, void* v = nullptr)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationRouting* o, void* v = nullptr)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationAlternate* o, void* v = nullptr)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationSplit* o, void* v = nullptr)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationItemSupplier* o, void* v = nullptr)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationItemDistribution* o, void* v = nullptr)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const Resource*,void* = nullptr)
    {
      throw LogicException("Called undefined solve(Resource*) method");
    }

    virtual void solve(const ResourceInfinite* r, void* v = nullptr)
    {
      solve(reinterpret_cast<const Resource*>(r),v);
    }

    virtual void solve(const ResourceBuckets* r, void* v = nullptr)
    {
      solve(reinterpret_cast<const Resource*>(r),v);
    }

    virtual void solve(const Buffer*,void* = nullptr)
    {
      throw LogicException("Called undefined solve(Buffer*) method");
    }

    virtual void solve(const BufferInfinite* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Buffer*>(b),v);
    }

    virtual void solve(const Load* b, void* v = nullptr)
    {
      throw LogicException("Called undefined solve(Load*) method");
    }

    virtual void solve(const LoadDefault* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Load*>(b),v);
    }

    virtual void solve(const LoadBucketizedFromStart* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Load*>(b), v);
    }

    virtual void solve(const LoadBucketizedFromEnd* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Load*>(b), v);
    }

    virtual void solve(const LoadBucketizedPercentage* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Load*>(b), v);
    }

    virtual void solve(const Flow* b, void* v = nullptr)
    {
      throw LogicException("Called undefined solve(Flow*) method");
    }

    virtual void solve(const FlowStart* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Flow*>(b), v);
    }

    virtual void solve(const FlowEnd* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Flow*>(b),v);
    }

    virtual void solve(const FlowTransferBatch* b, void* v = nullptr)
    {
      solve(reinterpret_cast<const Flow*>(b), v);
    }

    virtual void solve(const Solvable*,void* = nullptr)
    {
      throw LogicException("Called undefined solve(Solvable*) method");
    }

    /** Returns how elaborate and verbose output is requested.<br>
      * As a guideline solvers should respect the following guidelines:
      * - 0:<br>
      *   Completely silent.<br>
      *   This is the default value.
      * - 1:<br>
      *   Minimal and high-level messages on the progress that are sufficient
      *   for logging normal operation.<br>
      * - 2:<br>
      *   Higher numbers are solver dependent. These levels are typically
      *   used for debugging and tracing, and provide more detail on the
      *   solver's progress.
      */
    short getLogLevel() const
    {
      return loglevel;
    }

    /** Controls whether verbose output will be generated. */
    virtual void setLogLevel(short v)
    {
      loglevel = v;
    }

    /** Return whether or not we automatically commit the changes. */
    bool getAutocommit() const
    {
      return autocommit;
    }

    /** Update whether or not we automatically commit the changes. */
    void setAutocommit(const bool b)
    {
      autocommit = b;
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addShortField<Cls>(Tags::loglevel, &Cls::getLogLevel, &Cls::setLogLevel);
      m->addBoolField<Cls>(Tags::autocommit, &Cls::getAutocommit, &Cls::setAutocommit);
    }

  private:
    /** Controls the amount of tracing and debugging messages. */
    short loglevel;

    /** Automatically commit any plan changes or not. */
    bool autocommit = true;
};


/** @brief This class needs to be implemented by all classes that implement
  * dynamic behavior, and which can be called by a solver.
  */
class Solvable
{
  public:
    /** This method is called by solver classes. The implementation of this
      * class simply calls the solve method on the solver class. Using the
      * polymorphism the solver can implement seperate methods for different
      * plannable subclasses.
      */
    virtual void solve(Solver &s, void* v = nullptr) const
    {
      s.solve(this,v);
    }

    /** Destructor. */
    virtual ~Solvable() {}
};


/** @brief This class needs to be implemented by all classes that implement
  * dynamic behavior in the plan.
  *
  * The problem detection logic is implemented in the detectProblems() method.
  * For performance reasons, problem detection is "lazy", i.e. problems are
  * computed only when somebody really needs the access to the list of
  * problems.
  */
class Plannable : public HasProblems, public Solvable
{
  public:
    /** Constructor. */
    Plannable() : useProblemDetection(true), changed(true)
    {
      anyChange = true;
    }

    /** Specify whether this entity reports problems. */
    void setDetectProblems(bool b);

    /** Returns whether or not this object needs to detect problems. */
    bool getDetectProblems() const
    {
      return useProblemDetection;
    }

    /** Loops through all plannable objects and updates their problems if
      * required. */
    static void computeProblems();

    /** See if this entity has changed since the last problem
      * problem detection run. */
    bool getChanged() const
    {
      return changed;
    }

    /** Mark that this entity has been updated and that the problem
      * detection needs to be redone. */
    void setChanged(bool b = true)
    {
      changed=b;
      if (b) anyChange=true;
    }

    /** Implement the pure virtual function from the HasProblem class. */
    Plannable* getEntity() const
    {
      return const_cast<Plannable*>(this);
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addIteratorField<Cls, Problem::iterator, Problem>(Tags::problems, Tags::problem, &Cls::getProblems, DETAIL + PLAN);
      HasProblems::registerFields<Cls>(m);
    }

    /** Return an iterator over the list of problems. */
    Problem::iterator getProblems() const;

  private:
    /** Stores whether this entity should be skip problem detection, or not. */
    bool useProblemDetection;

    /** Stores whether this entity has been updated since the last problem
      * detection run. */
    bool changed;

    /** Marks whether any entity at all has changed its status since the last
      * problem detection round.
      */
    static bool anyChange;

    /** This flag is set to true during the problem recomputation. It is
      * required to garantuee safe access to the problems in a multi-threaded
      * environment.
      */
    static bool computationBusy;
};


/** @brief The purpose of this class is to compute the levels of all buffers,
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
  * Cluster 0 is a special case: it contains all entities not connected to any other
  * entity at all.
  * Clusters are helpful in multi-threading the planning problem, partial
  * replanning of the model, etc...
  */
class HasLevel
{
  private:
    /** Flags whether the current computation is still up to date or not.
      * The flag is set when new objects of this are created or updated.
      * Running the computeLevels function clears the flag.
      */
    static bool recomputeLevels;

    /** This flag is set to true during the computation of the levels. It is
      * required to ensure safe access to the level information in a
      * multi-threaded environment.
      */
    static bool computationBusy;

    /** Stores the total number of clusters in the model. */
    static int numberOfClusters;

    /** Stores the maximum level number in the model. */
    static short numberOfLevels;

    /** Stores the level of this entity. Higher numbers indicate more
      * upstream entities.
      * A value of -1 indicates an unused entity.
      */
    short lvl;

    /** Stores the cluster number of the current entity. */
    int cluster;

  protected:
    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addShortField<Cls>(Tags::level, &Cls::getLevel, nullptr, 0, DONT_SERIALIZE);
      m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0, DONT_SERIALIZE);
    }

    /** Default constructor. The initial level is -1 and basically indicates
      * that this object (either Operation, Buffer or Resource) is not
      * being used at all...
      */
    HasLevel() : lvl(0), cluster(0) {}

    /** Copy constructor. Since the characterictics of the new object are the
      * same as the original, the level and cluster are also the same.
      * No recomputation is required.
      */
    HasLevel(const HasLevel& o) : lvl(o.lvl), cluster(o.cluster) {}

    /** Destructor. Deleting a HasLevel object triggers recomputation of the
      * level and cluster computation, since the network now has changed.
      */
    ~HasLevel()
    {
      recomputeLevels = true;
    }

    /** This function recomputes all levels in the model.
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
    /** Returns the total number of levels.<br>
      * If not up to date the recomputation will be triggered.
      */
    static short getNumberOfLevels()
    {
      if (recomputeLevels || computationBusy) computeLevels();
      return numberOfLevels;
    }

    /** Returns the total number of clusters.<br>
      * If not up to date the recomputation will be triggered.
      */
    static int getNumberOfClusters()
    {
      if (recomputeLevels || computationBusy) computeLevels();
      return numberOfClusters;
    }

    /** Return the level (and recompute first if required). */
    short getLevel() const
    {
      if (recomputeLevels || computationBusy)
        computeLevels();
      return lvl;
    }

    /** Return the cluster number (and recompute first if required). */
    int getCluster() const
    {
      if (recomputeLevels || computationBusy)
        computeLevels();
      return cluster;
    }

    /** This function should be called when something is changed in the network
      * structure. The notification sets a flag, but does not immediately
      * trigger the recomputation.
      * @see computeLevels
      */
    static void triggerLazyRecomputation()
    {
      recomputeLevels = true;
    }
};


/** @brief This abstract class is used to associate buffers and resources with
  * a physical or logical location.
  *
  * The 'available' calendar is used to model the working hours and holidays
  * of resources, buffers and operations.
  */
class Location : public HasHierarchy<Location>, public HasDescription
{
  friend class ItemDistribution;
  public:
    typedef Association<Location, Item, ItemDistribution>::ListA distributionlist;

    /** Default constructor. */
    explicit Location()
    {
      initType(metadata);
    }

    /** Destructor. */
    virtual ~Location();

    /** Returns the availability calendar of the location.<br>
      * The availability calendar models the working hours and holidays. It
      * applies to all operations, resources and buffers using this location.
      */
    Calendar *getAvailable() const
    {
      return available;
    }

    /** Updates the availability calendar of the location. */
    void setAvailable(Calendar* b)
    {
      available = b;
    }

    /** Returns a constant reference to the item distributions pointing to
      * this location as origin. */
    const distributionlist& getDistributions() const
    {
      return distributions;
    }

    /** Returns an iterator over the list of item distributions pointing to
      * this location as origin. */
    distributionlist::const_iterator getDistributionIterator() const
    {
      return distributions.begin();
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;
    static int initialize();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addPointerField<Cls, Calendar>(Tags::available, &Cls::getAvailable, &Cls::setAvailable);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
    }

  private:
    /** The availability calendar models the working hours and holidays. It
      * applies to all operations, resources and buffers using this location.
      */
    Calendar* available = nullptr;

    /** This is a list of item distributions pointing to this location as
      * destination.
      */
    distributionlist distributions;
};


/** @brief This class implements the abstract Location class. */
class LocationDefault : public Location
{
  public:
    explicit LocationDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This abstracts class represents customers.
  *
  * Demands can be associated with a customer, but there is no planning
  * behavior directly linked to customers.
  */
class Customer : public HasHierarchy<Customer>, public HasDescription
{
  public:
    /** Default constructor. */
    explicit Customer() {}

    /** Destructor. */
    virtual ~Customer();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;
    static int initialize();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
    }
};


/** @brief This class implements the abstract Customer class. */
class CustomerDefault : public Customer
{
  public:
    /** Default constructor. */
    explicit CustomerDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This abstracts class represents a supplier. */
class Supplier : public HasHierarchy<Supplier>, public HasDescription
{
  friend class ItemSupplier;
  public:
    typedef Association<Supplier,Item,ItemSupplier>::ListA itemlist;

    /** Default constructor. */
    explicit Supplier() {}

    /** Destructor. */
    virtual ~Supplier();

    /** Returns a constant reference to the list of items this supplier can deliver. */
    const itemlist& getItems() const
    {
      return items;
    }

    /** Returns an iterator over the list of items this supplier can deliver. */
    itemlist::const_iterator getItemIterator() const
    {
      return items.begin();
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;
    static int initialize();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addIteratorField<Cls, itemlist::const_iterator, ItemSupplier>(Tags::itemsuppliers, Tags::itemsupplier, &Cls::getItemIterator, DETAIL);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
    }

  private:
    /** This is a list of items this supplier has. */
    itemlist items;
};


/** @brief This class implements the abstract Supplier class. */
class SupplierDefault : public Supplier
{
  public:
    explicit SupplierDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief A suboperation is used in operation types which have child
  * operations.
  */
class SubOperation : public Object, public HasSource
{
  private:
    /** Pointer to the parent operation. */
    Operation* owner = nullptr;

    /** Pointer to the child operation.
      * Note that the same child operation can be used in multiple parents.
      * The child operation is completely unaware of its parents.
      */
    Operation* oper = nullptr;

    /** Validity date range for the child operation. */
    DateRange effective;

    /** Priority index. */
    int prio = 1;

    /** Python constructor. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  public:

    typedef list<SubOperation*> suboperationlist;

    /** Default constructor. */
    explicit SubOperation()
    {
      initType(metadata);
    }

    /** Destructor. */
    ~SubOperation();

    Operation* getOwner() const
    {
      return owner;
    }

    void setOwner(Operation*);

    Operation* getOperation() const
    {
      return oper;
    }

    void setOperation(Operation*);

    int getPriority() const
    {
      return prio;
    }

    void setPriority(int);

    DateRange getEffective() const
    {
      return effective;
    }

    Date getEffectiveStart() const
    {
      return effective.getStart();
    }

    void setEffectiveStart(Date d)
    {
      effective.setStart(d);
    }

    Date getEffectiveEnd() const
    {
      return effective.getEnd();
    }

    void setEffectiveEnd(Date d)
    {
      effective.setEnd(d);
    }

    void setEffective(DateRange d)
    {
      effective = d;
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metacategory;
    static const MetaClass* metadata;
    static int initialize();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Operation>(Tags::owner, &Cls::getOwner, &Cls::setOwner, MANDATORY + PARENT);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation, MANDATORY);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      HasSource::registerFields<Cls>(m);
    }

    class iterator
    {
      private:
        suboperationlist::const_iterator cur;
        suboperationlist::const_iterator nd;
      public:
        /** Constructor. */
        iterator(suboperationlist& l) : cur(l.begin()), nd(l.end()) {}

        /** Return current value and advance the iterator. */
        SubOperation* next()
        {
          if (cur == nd)
            return nullptr;
          SubOperation *tmp = *cur;
          ++cur;
          return tmp;
        }
    };
};


#include "frepple/timeline.h"


/** @brief A timeline event representing a setup change. 
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
class SetupEvent : public TimeLine<LoadPlan>::Event
{
  friend class TimeLine<LoadPlan>::Event;

  private:
    PooledString setup;
    TimeLine<LoadPlan>* tmline = nullptr;
    SetupMatrixRule* rule = nullptr;
    OperationPlan* opplan = nullptr;

  public:
    virtual TimeLine<LoadPlan>* getTimeLine() const
    {
      return tmline;
    }
  
    /** Default constructor. */
    SetupEvent() : TimeLine<LoadPlan>::Event(5)
    {
      initType(metadata);    
    }

    /** Copy constructor. */
    SetupEvent(const SetupEvent& x) 
      : TimeLine<LoadPlan>::Event(5), setup(x.setup), rule(x.rule)
    {
      initType(metadata);
      dt = x.getDate();
    }

    /** Constructor. */
    SetupEvent(const SetupEvent* x) : TimeLine<LoadPlan>::Event(5)
    {
      initType(metadata);
      if (x)
      {
        setup = x->setup;
        rule = x->rule;
        dt = x->getDate();
      }
    }

    /** Destructor. */
    virtual ~SetupEvent();

    void erase()
    {
      if (tmline)
        tmline->erase(this);
    }

    /** Assignment operator. 
      * We don't relink the event in the timeline yet.
      * We don't copy the operationplan field either.
      */
    SetupEvent& operator =(const SetupEvent & other)
    {
      assert(!tmline);
      setup = other.setup;
      tmline = other.tmline;
      rule = other.rule;
      return *this;
    }

    /** Constructor. */
    SetupEvent(TimeLine<LoadPlan>& t, Date d, PooledString s, SetupMatrixRule* r=nullptr, OperationPlan* o=nullptr)
      : TimeLine<LoadPlan>::Event(5), setup(s), tmline(&t), opplan(o)
    {
      initType(metadata);
      dt = d;
      if (opplan)
        tmline->insert(this);
    }

    virtual OperationPlan* getOperationPlan() const
    {
      return opplan;
    }

    void setOperationPlan(OperationPlan* o)
    {
      opplan = o;
    }

    SetupMatrixRule* getRule() const
    {
      return rule;
    }

    PooledString getSetup() const
    {
      return setup;
    }

    string getSetupString() const
    {
      return setup;
    }

    void setSetup(PooledString s)
    {
      setup = s;
    }

    SetupEvent* getSetupBefore() const;

    void update(Resource*, Date, PooledString, SetupMatrixRule*);

    static int initialize();

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::setup, &Cls::getSetupString);
      m->addPointerField<Cls, SetupMatrixRule>(Tags::rule, &Cls::getRule);
      m->addDateField<Cls>(Tags::date, &Cls::getDate);
    }
};


/** @brief An operationplan is the key dynamic element of a plan. It
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
  *    if this hasn't been done yet.<br>
  *  - Operationplans can be organized in hierarchical structure, matching
  *    the operation hierarchies they belong to.
  */
class OperationPlan
  : public Object, public HasProblems, public HasSource, private Tree<unsigned long>::TreeNode
{
    friend class FlowPlan;
    friend class LoadPlan;
    friend class Demand;
    friend class Operation;
    friend class OperationSplit;
    friend class OperationAlternate;
    friend class OperationRouting;
    friend class FlowTransferBatch;

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

    /** Flowplan iteration. */
    inline FlowPlanIterator getFlowPlans() const;
    inline FlowPlanIterator beginFlowPlans() const;
    inline FlowPlanIterator endFlowPlans() const;
    int sizeFlowPlans() const;

    /** Loadplan iteration. */
    inline LoadPlanIterator getLoadPlans() const;
    LoadPlanIterator beginLoadPlans() const;
    LoadPlanIterator endLoadPlans() const;
    int sizeLoadPlans() const;

    /** Interruption iteration. */
    inline InterruptionIterator getInterruptions() const;

    /** Returns whether this operationplan is a PO, MO or DO. */
    inline string getOrderType() const;

    /** Returns the criticality index of the operationplan, which reflects
      * its urgency.<br>
      * If the operationplan is on the critical path of one or more orders
      * the criticality is high. If the operationplan is only used to satisfy
      * safety stock requirements it will have a low criticality.<br>
      * Computing the criticality is complex, CPU-expensive and the result
      * will change when the plan changes. Caching the value may be in
      * order.<br>
      * Criticality is currently implemented as the slack in the downstream
      * path. If the criticality is 2, it means the operationplan can be
      * delayed by 2 days without impacting the delivery of any demand.
      * TODO should criticality also include priority of demand and critical quantity?
      */
    double getCriticality() const;

    /** Returns the difference between:
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

    /** Merge this operationplan with another one if possible. 
      * The return value is true when a merge was done. 
      * Careful: When a merge is done this pointer object is deleted! 
      */
    bool mergeIfPossible();

    friend class iterator;

    /** This is a factory method that creates an operationplan pointer based
      * on the operation and id. */
    static Object* createOperationPlan(
      const MetaClass*, const DataValueDict&, CommandManager* = nullptr
      );

    /** Shortcut method to the cluster. */
    int getCluster() const;

    /** Destructor. */
    virtual ~OperationPlan();

    virtual void setChanged(bool b = true);

    /** Returns the quantity. */
    double getQuantity() const
    {
      return quantity;
    }

    /** Update the quantity. */
    void setQuantity(double f)
    {
      setQuantity(f, false, true, true);
    }

    /** Updates the quantity.<br>
      * The operationplan quantity is subject to the following rules:
      *  - The quantity must be greater than or equal to the minimum size.<br>
      *    The value is rounded up to the smallest multiple above the minimum
      *    size if required, or rounded down to 0.
      *  - The quantity must be a multiple of the multiple_size field.<br>
      *    The value is rounded up or down to meet this constraint.
      *  - The quantity must be smaller than or equal to the maximum size.<br>
      *    The value is limited to the smallest multiple below this limit.
      *  - Setting the quantity of an operationplan to 0 is always possible,
      *    regardless of the minimum, multiple and maximum values.
      * This method can only be called on top operationplans. Sub operation
      * plans should pass on a call to the parent operationplan.
      */
    inline double setQuantity(double f, bool roundDown,
      bool update = true, bool execute = true, Date end = Date::infinitePast);

    /** Returns a pointer to the demand for which this operationplan is a delivery.
      * If the operationplan isn't a delivery, this is a nullptr pointer.
      */
    Demand* getDemand() const
    {
      return dmd;
    }

    /** Updates the demand to which this operationplan is a solution. */
    void setDemand(Demand* l);

    /** Calculate the unavailable time during the operationplan. The regular
      * duration is extended with this amount.
      */
    Duration getUnavailable() const;

    /** Return the status of the operationplan.
      * The status string is one of the following:
      *   - proposed
      *   - approved
      *   - confirmed
      */
    string getStatus() const;

    /** Update the status of the operationplan. */
    void setStatus(const string&);

    /** Enforce a specific start date, end date and quantity. There is
      * no validation whether the values are consistent with the operation
      * parameters.
      * This method only works for locked operationplans.
      */
    void freezeStatus(Date, Date, double);

    /** Return the list of problems of this operationplan. */
    inline OperationPlan::ProblemIterator getProblems() const;

    bool getConfirmed() const
    {
      return (flags & STATUS_CONFIRMED) != 0;
    }

    bool getApproved() const
    {
      return (flags & STATUS_APPROVED) != 0;
    }

    bool getProposed() const
    {
      return (flags & (STATUS_CONFIRMED + STATUS_APPROVED)) == 0;
    }

    bool getFeasible() const
    {
      return !(flags & FEASIBLE);
    }

    /** Returns true is this operationplan is allowed to consume material.
      * This field only has an impact for locked operationplans.
      */
    bool getConsumeMaterial() const
    {
      return !(flags & CONSUME_MATERIAL);
    }

    /** Returns true is this operationplan is allowed to produce material.
      * This field only has an impact for locked operationplans.
      */
    bool getProduceMaterial() const
    {
      return !(flags & PRODUCE_MATERIAL);
    }

    /** Returns true is this operationplan is allowed to consume capacity.
      * This field only has an impact for locked operationplans.
      */
    bool getConsumeCapacity() const
    {
      return !(flags & CONSUME_CAPACITY);
    }

    /** Deletes all operationplans of a certain operation. A boolean flag
      * allows to specify whether locked operationplans are to be deleted too.
      */
    static void deleteOperationPlans(Operation* o, bool deleteLocked=false);

    /** Update the status to CONFIRMED, or back to PROPOSED. */
    virtual void setConfirmed(bool b);

    /** Update the status to APPROVED, or back to PROPOSED. */
    virtual void setApproved(bool b);

    /** Update the status to PROPOSED, or back to APPROVED. */
    virtual void setProposed(bool b);

    /** Update flag which allow/disallows material consumption. */
    void setConsumeMaterial(bool b)
    {
      if (b)
        flags &= ~CONSUME_MATERIAL;
      else
        flags |= CONSUME_MATERIAL;
      resizeFlowLoadPlans();
    }

    /** Update flag which allow/disallows material production. */
    void setProduceMaterial(bool b)
    {
      if (b)
        flags &= ~PRODUCE_MATERIAL;
      else
        flags |= PRODUCE_MATERIAL;
      resizeFlowLoadPlans();
    }

    /** Update flag which allow/disallows capacity consumption. */
    void setConsumeCapacity(bool b)
    {
      if (b)
        flags &= ~CONSUME_CAPACITY;
      else
        flags |= CONSUME_CAPACITY;
      resizeFlowLoadPlans();
    }

    void setFeasible(bool b)
    {
      if (b)
        flags &= ~FEASIBLE;
      else
        flags |= FEASIBLE;
    }

    /** Returns a pointer to the operation being instantiated. */
    Operation* getOperation() const
    {
      return oper;
    }

    /** Update the operation of an operationplan. */
    void setOperation(Operation* o);

    /** Fixes the start and end date of an operationplan. Note that this
      * overrules the standard duration given on the operation, i.e. no logic
      * kicks in to verify the data makes sense. This is up to the user to
      * take care of.<br>
      * The methods setStart(Date) and setEnd(Date) are therefore preferred
      * since they properly apply all appropriate logic.
      */
    void setStartAndEnd(Date st, Date nd)
    {
      dates.setStartAndEnd(st, nd);
      update();
      //assert(getStart() <= getSetupEnd() && getSetupEnd() <= getEnd());
      if (getStart() > getSetupEnd() || getSetupEnd() > getEnd())
        logger << "Warning: strange dates on " << this << ": " << getStart() << " - " << getSetupEnd() << " - " << getEnd() << endl;
    }

    /** Fixes the start date, end date and quantity of an operationplan. Note that this
      * overrules the standard duration given on the operation, i.e. no logic
      * kicks in to verify the data makes sense. This is up to the user to
      * take care of.<br>
      * The methods setStart(Date) and setEnd(Date) are therefore preferred
      * since they properly apply all appropriate logic.
      */
    void setStartEndAndQuantity(Date st, Date nd, double q)
    {
      quantity = q;
      dates.setStartAndEnd(st, nd);
      update();
    }

    /** A method to restore a previous state of an operationplan.<br>
      * NO validity checks are done on the parameters.
      */
    void restore(const OperationPlanState& x);

    /** Updates the operationplan owning this operationplan.<br>
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

    void setOwner(OperationPlan* o)
    {
      setOwner(o, false);
    }

    /** Returns a pointer to the operationplan for which this operationplan
      * a sub-operationplan.<br>
      * The method returns nullptr if there is no owner defined.<br>
      * E.g. Sub-operationplans of a routing refer to the overall routing
      * operationplan.<br>
      * E.g. An alternate sub-operationplan refers to its parent.
      * @see getTopOwner
      */
    OperationPlan* getOwner() const
    {
      return owner;
    }

    SetupEvent* getSetupEvent() const
    {
      return setupevent;
    }

    /** Return a pointer to the next suboperationplan of the owner. */
    OperationPlan* getNextSubOpplan() const
    {
      return nextsubopplan;
    }

    /** Return a pointer to the previous suboperationplan of the owner. */
    OperationPlan* getPrevSubOpplan() const
    {
      return prevsubopplan;
    }

    /** Returns a pointer to the operationplan owning a set of
      * sub-operationplans. There can be multiple levels of suboperations.<br>
      * If no owner exists the method returns the current operationplan.
      * @see getOwner
      */
    OperationPlan* getTopOwner() const
    {
      if (owner)
      {
        // There is an owner indeed
        OperationPlan* o(owner);
        while (o->owner) o = o->owner;
        return o;
      }
      else
        // This operationplan is itself the top of a hierarchy
        return const_cast<OperationPlan*>(this);
    }

    /** Returns the start and end date of this operationplan. */
    const DateRange& getDates() const
    {
      return dates;
    }

    /** Return the start of the actual operation time. */
    Date getSetupEnd() const
    {
      return setupevent ? setupevent->getDate() : dates.getStart();
    }

    /** Return the setup cost. */
    double getSetupCost() const;

    /** Update the setup information. */
    void setSetupEvent(Resource*, Date, PooledString, SetupMatrixRule* = nullptr);

    /** Remove the setup event. */
    void clearSetupEvent()
    {
      if (!setupevent)
        return;
      setupevent->erase();
      delete setupevent;
      setupevent = nullptr;
    }

    /** Remove the setup event. */
    void nullSetupEvent()
    {
      setupevent = nullptr;
    }

    /** Return true if the operationplan is redundant, ie all material
      * it produces is not used at all.<br>
      * If the optional argument is false (which is the default value), we
      * check with the minimum stock level of the buffers. If the argument
      * is true, we check with 0.
      */
    bool isExcess(bool = false) const;

    /** Returns a unique identifier of the operationplan.<br>
      * The identifier can be specified in the data input (in which case
      * we check for the uniqueness during the read operation).<br>
      * For operationplans created during a solver run, the identifier is
      * assigned in the instantiate() function. The numbering starts with the
      * highest identifier read in from the input and is then incremented
      * for every operationplan that is registered.
      *
      * This method is declared as constant. But actually, it can still update
      * the identifier field if it is wasn't set before.
      */
    unsigned long getIdentifier() const
    {
      if (getName() == ULONG_MAX)
        const_cast<OperationPlan*>(this)->assignIdentifier(); // Lazy generation
      return getName();
    }

    void setIdentifier(unsigned long i)
    {
      setName(i);
      assignIdentifier();
    }

    void setRawIdentifier(unsigned long i)
    {
      setName(i);
    }

    /** Return the identifier. This method can return the lazy identifiers 0 or U_LONGMAX. */
    unsigned long getRawIdentifier() const
    {
      return getName();
    }

    /** Update the next-id number.
      * Only increases are allowed to avoid duplicate id assignments.
      */
    static void setIDCounter(unsigned long l)
    {
      if (l > counterMin)
        counterMin = l;
    }

    /** Return the next-id number. */
    static unsigned long getIDCounter()
    {
      return counterMin;
    }

    /** Return the external identifier. */
    string getReference() const
    {
      return ref;
    }

    /** Update the external identifier. */
    void setReference(const string& s)
    {
      ref = s;
    }

    /** Return the end date. */
    Date getEnd() const
    {
      return dates.getEnd();
    }

    /** Updates the end date of the operationplan and compute the start
      * date.<br>
      * Locked operationplans are not updated by this function.<br>
      * Slack can be introduced between sub operationaplans by this method,
      * i.e. the sub operationplans are only moved if required to meet the
      * end date.
      */
    void setEnd(Date, bool force);
    
    void setEnd(Date d)
    {
      setEnd(d, false);
    }

    void setEndForce(Date d)
    {
      setEnd(d, true);
    }

    /** Return the end date. */
    Date getStart() const
    {
      return dates.getStart();
    }

    /** Updates the start date of the operationplan and compute the end
      * date.<br>
      * Locked operation_plans are not updated by this function.<br>
      * Slack can be introduced between sub operationaplans by this method,
      * i.e. the sub operationplans are only moved if required to meet the
      * start date.
      */
    void setStart(Date, bool force, bool preferend);

	  void setStart(Date d)
    {
      setStart(d, false, true);
    }

    void setStartForce(Date d)
    {
      setStart(d, true, true);
    }

    /** Return the efficiency factor of the operationplan.
      * It's computed as the most inefficient of all resources loaded by the operationplan.
      */
    double getEfficiency(Date = Date::infinitePast) const;

    static int initialize();

    static PyObject* calculateOperationTimePython(PyObject*, PyObject*);

    PyObject* str() const
    {
      ostringstream ch;
      ch << getName();
      return PythonData(ch.str());
    }

    /** Python factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

    /** Initialize the operationplan. The initialization function should be
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
    bool activate(bool createsubopplans=true, bool use_start=false);

    /** Remove an operationplan from the list of officially registered ones.<br>
      * The operationplan will keep its loadplans and flowplans after unregistration.
      */
    void deactivate();

    /** This method links the operationplan in the list of all operationplans
      * maintained on the operation.<br>
      * In most cases calling this method is not required since it included
      * in the activate method. In exceptional cases the solver already
      * needs to see uncommitted operationplans in the list - eg for the
      * procurement buffer.
      * @see activate
      */
    void insertInOperationplanList();

    /** This method remove the operationplan from the list of all operationplans
      * maintained on the operation.<br>
      * @see deactivate
      */
    void removeFromOperationplanList();

    /** Remove a sub-operation_plan from the list. */
    virtual void eraseSubOperationPlan(OperationPlan*);

    /** This function is used to create the loadplans, flowplans and
      * setup operationplans.
      */
    void createFlowLoads();

    /** A function to compute whether an operationplan is feasible or not. */
    bool updateFeasible();

    /** Python API for the above method. */
    static PyObject* updateFeasiblePython(PyObject*, PyObject*);

    /** This function is used to delete the loadplans, flowplans and
      * setup operationplans.
      */
    void deleteFlowLoads();

    /** Operationplans are never considered hidden, even if the operation they
      * instantiate is hidden. Only exception are stock operationplans.
      */
    inline bool getHidden() const;

    /** Searches for an OperationPlan with a given identifier.<br>
      * Returns a nullptr pointer if no such OperationPlan can be found.<br>
      * The method is of complexity O(n), i.e. involves a LINEAR search through
      * the existing operationplans, and can thus be quite slow in big models.<br>
      * The method is O(1), i.e. constant time regardless of the model size,
      * when the parameter passed is bigger than the operationplan counter.
      */
    static OperationPlan* findId(unsigned long l);

    /** Problem detection is actually done by the Operation class. That class
      * actually "delegates" the responsability to this class, for efficiency.
      */
    virtual void updateProblems();

    /** Implement the pure virtual function from the HasProblem class. */
    inline Plannable* getEntity() const;

    /** Return the metadata. We return the metadata of the operation class,
      * not the one of the operationplan class!
      */
    const MetaClass& getType() const {return *metadata;}

    static const MetaClass* metadata;

    static const MetaCategory* metacategory;

    /** Lookup a operationplan. */
    static Object* finder(const DataValueDict&);

    /** Comparison of 2 OperationPlans.
      * To garantuee that the problems are sorted in a consistent and stable
      * way, the following sorting criteria are used (in order of priority):
      * <ol><li>Operation</li>
      * <li>Start date (earliest dates first)</li>
      * <li>Quantity (biggest quantities first)</li></ol>
      * Multiple operationplans for the same values of the above keys can exist.
      */
    bool operator < (const OperationPlan& a) const;

    /** Copy constructor.<br>
      * If the optional argument is false, the new copy is not initialized
      * and won't have flowplans and loadplans.
      */
    OperationPlan(const OperationPlan&, bool = true);

    /** Return the total quantity which this operationplan, its children
      * and its parents produce or consume from a given buffer.
      */
    double getTotalFlow(const Buffer* b) const
    {
      return getTopOwner()->getTotalFlowAux(b);
    }

    static inline OperationPlan::iterator end();

    static inline OperationPlan::iterator begin();

    inline OperationPlan::iterator getSubOperationPlans() const;

    PeggingIterator getPeggingDownstream() const;

    PeggingIterator getPeggingUpstream() const;

    PeggingDemandIterator getPeggingDemand() const;

    /** Return an iterator over alternate operations for this operationplan. */
    AlternateIterator getAlternates() const;

    /** Return the setup time on this operationplan. */
    Duration getSetup() const;

    /** Update the setup time in situations where it could have changed.
      * The return value is true when the time has changed.
      */
    bool updateSetupTime(bool report = false);

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addUnsignedLongField<Cls>(Tags::id, &Cls::getIdentifier, &Cls::setIdentifier, 0, MANDATORY);
      m->addStringField<Cls>(Tags::reference, &Cls::getReference, &Cls::setReference);
      m->addPointerField<Cls, Operation>(
        Tags::operation, &Cls::getOperation, &Cls::setOperation, 
        BASE + PLAN + WRITE_REFERENCE_DFT + WRITE_OBJECT_SVC + WRITE_HIDDEN
        );
      m->addPointerField<Cls, Demand>(Tags::demand, &Cls::getDemand, &Cls::setDemand, BASE + WRITE_HIDDEN);
      m->addDateField<Cls>(Tags::start, &Cls::getStart, &Cls::setStart, Date::infiniteFuture);
      m->addDateField<Cls>(Tags::end, &Cls::getEnd, &Cls::setEnd, Date::infiniteFuture);
      m->addDateField<Cls>(Tags::end_force, &Cls::getEnd, &Cls::setEndForce, Date::infiniteFuture, DONT_SERIALIZE);
      m->addDurationField<Cls>(Tags::setup, &Cls::getSetup, nullptr, 0L, PLAN);
      m->addDateField<Cls>(Tags::setupend, &Cls::getSetupEnd, nullptr, Date::infinitePast, PLAN);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity);
      m->addIteratorField<Cls, OperationPlan::ProblemIterator, Problem>(Tags::problems, Tags::problem, &Cls::getProblems, PLAN + WRITE_OBJECT);

      // Default of -999 to enforce serializing the value if it is 0
      m->addDoubleField<Cls>(Tags::criticality, &Cls::getCriticality, nullptr, -999, PLAN);
      m->addStringField<Cls>(Tags::status, &Cls::getStatus, &Cls::setStatus, "proposed");
      m->addBoolField<Cls>(Tags::approved, &Cls::getApproved, &Cls::setApproved, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::proposed, &Cls::getProposed, &Cls::setProposed, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::confirmed, &Cls::getConfirmed, &Cls::setConfirmed, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::consume_material, &Cls::getConsumeMaterial, &Cls::setConsumeMaterial, BOOL_TRUE);
      m->addBoolField<Cls>(Tags::produce_material, &Cls::getProduceMaterial, &Cls::setProduceMaterial, BOOL_TRUE);
      m->addBoolField<Cls>(Tags::consume_capacity, &Cls::getConsumeCapacity, &Cls::setConsumeCapacity, BOOL_TRUE);
      m->addBoolField<Cls>(Tags::feasible, &Cls::getFeasible, &Cls::setFeasible, BOOL_TRUE);
      HasSource::registerFields<Cls>(m);
      m->addPointerField<Cls, OperationPlan>(Tags::owner, &Cls::getOwner, &Cls::setOwner);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addDurationField<Cls>(Tags::unavailable, &Cls::getUnavailable, nullptr, 0L, DONT_SERIALIZE);
      m->addIteratorField<Cls, OperationPlan::InterruptionIterator, OperationPlan::InterruptionIterator>(Tags::interruptions, Tags::interruption, &Cls::getInterruptions, DONT_SERIALIZE);
      m->addDurationField<Cls>(Tags::delay, &Cls::getDelay, nullptr, -999L, PLAN);
      m->addIteratorField<Cls, OperationPlan::FlowPlanIterator, FlowPlan>(Tags::flowplans, Tags::flowplan, &Cls::getFlowPlans, PLAN + WRITE_HIDDEN);
      m->addIteratorField<Cls, OperationPlan::LoadPlanIterator, LoadPlan>(Tags::loadplans, Tags::loadplan, &Cls::getLoadPlans, PLAN);
      m->addIteratorField<Cls, PeggingIterator, PeggingIterator>(Tags::pegging_downstream, Tags::pegging, &Cls::getPeggingDownstream, DONT_SERIALIZE);
      m->addIteratorField<Cls, PeggingIterator, PeggingIterator>(Tags::pegging_upstream, Tags::pegging, &Cls::getPeggingUpstream, DONT_SERIALIZE);
      m->addIteratorField<Cls, PeggingDemandIterator, PeggingDemandIterator>(Tags::pegging_demand, Tags::pegging, &Cls::getPeggingDemand, PLAN + WRITE_OBJECT);
      m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getSubOperationPlans, DONT_SERIALIZE);
      m->addIteratorField<Cls, OperationPlan::AlternateIterator, Operation>(Tags::alternates, Tags::alternate, "AlternateOperationIterator", "Iterator over operation alternates", &Cls::getAlternates, PLAN + FORCE_BASE);
      m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0, DONT_SERIALIZE);
      m->addStringField<Cls>(Tags::ordertype, &Cls::getOrderType, &Cls::setOrderType, "MO");
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addPointerField<Cls, Location>(Tags::origin, &Cls::getOrigin, &Cls::setOrigin);
      m->addPointerField<Cls, Supplier>(Tags::supplier, &Cls::getSupplier, &Cls::setSupplier);
    }

    static PyObject* createIterator(PyObject* self, PyObject* args);

    static bool getPropagateSetups()
    {
      return propagatesetups;
    }

    static bool setPropagateSetups(bool b)
    {
      auto tmp = propagatesetups;
      propagatesetups = b;
      return tmp;
    }

  private:
    /** A tree structure with all operationplans to allow a fast lookup by id. */
    static Tree<unsigned long> st;

    /** Private copy constructor.<br>
      * It is used in the public copy constructor to make a deep clone of suboperationplans.
      * @see OperationPlan(const OperationPlan&, bool = true)
      */
    OperationPlan(const OperationPlan&, OperationPlan*);

    /** Updates the operationplan based on the latest information of quantity,
      * date and locked flag.<br>
      * This method will also update parent and child operationplans.
      * @see resizeFlowLoadPlans
      */
    void update();

    /** Generates a unique identifier for the operationplan.
      * The field is 0 while the operationplan is not fully registered yet.
      * The field is 1 when the operationplan is fully registered but only a
      * temporary id is generated.
      * A unique value for each operationplan is created lazily when the
      * method getIdentifier() is called.
      */
    bool assignIdentifier();

    /** Recursive auxilary function for getTotalFlow.
      * @ see getTotalFlow
      */
    double getTotalFlowAux(const Buffer*) const;

    /** Update the loadplans and flowplans of the operationplan based on the
      * latest information of quantity, date and locked flag.<br>
      * This method will NOT update parent or child operationplans.
      * 
      * Only intended for internal use by update()
      */
    void resizeFlowLoadPlans();

    /** Maintain the operationplan list in sorted order.
      *
      * Only intended for internal use by update()
      */
    void updateOperationplanList();

    /** Update the setup time on all neighbouring operationplans.
      *
      * This method leaves the setup end date constant, which also
      * keeps all material production and consumption at their original
      * dates. The resource loading can be adjusted however.
      *
      * Only intended for internal use by update().
      */
    void scanSetupTimes();

  private:
    /** Default constructor.<br>
      * This way of creating operationplan objects is not intended for use by
      * any client applications. Client applications should use the factory
      * method on the operation class instead.<br>
      * Subclasses of the Operation class may use this constructor in their
      * own override of the createOperationPlan method.
      * @see Operation::createOperationPlan
      */
    OperationPlan() : Tree<unsigned long>::TreeNode(0)
    {
      initType(metadata);
    }

    static const unsigned short STATUS_APPROVED = 1;
    static const unsigned short STATUS_CONFIRMED = 2;
    // TODO Conceptually this may not ideal: Rather than a
    // quantity-based distinction (between CONSUME_MATERIAL and
    // PRODUCE_MATERIAL) having a time-based distinction may be more
    // appropriate (between PROCESS_MATERIAL_AT_START and
    // PROCESS_MATERIAL_AT_END).
    static const unsigned short CONSUME_MATERIAL = 4;
    static const unsigned short PRODUCE_MATERIAL = 8;
    static const unsigned short CONSUME_CAPACITY = 16;
    static const unsigned short FEASIBLE = 32;

    /** Counter of OperationPlans, which is used to automatically assign a
      * unique identifier for each operationplan.<br>
      * The value of the counter is the first available identifier value that
      * can be used for a new operationplan.<br>
      * The first value is 1, and each operationplan increases it by 1.
      * @see assignIdentifier()
      */
    static unsigned long counterMin;

    /** Flag controlling where setup time verification should be performed. */
    static bool propagatesetups;

    /** Pointer to a higher level OperationPlan. */
    OperationPlan *owner = nullptr;

    /** Pointer to the demand.<br>
      * Only delivery operationplans have this field set. The field is nullptr
      * for all other operationplans.
      */
    Demand *dmd = nullptr;

    /** External identifier for this operationplan. */
    string ref;

    /** Start and end date. */
    DateRange dates;

    /** Pointer to the operation. */
    Operation *oper = nullptr;

    /** Root of a single linked list of flowplans. */
    FlowPlan* firstflowplan = nullptr;

    /** Single linked list of loadplans. */
    LoadPlan* firstloadplan = nullptr;

    /** Pointer to the previous operationplan.<br>
      * Operationplans are chained in a doubly linked list for each operation.
      * @see next
      */
    OperationPlan* prev = nullptr;

    /** Pointer to the next operationplan.<br>
      * Operationplans are chained in a doubly linked list for each operation.
      * @see prev
      */
    OperationPlan* next = nullptr;

    /** Pointer to the first suboperationplan of this operationplan. */
    OperationPlan* firstsubopplan = nullptr;

    /** Pointer to the last suboperationplan of this operationplan. */
    OperationPlan* lastsubopplan = nullptr;

    /** Pointer to the next suboperationplan of the parent operationplan. */
    OperationPlan* nextsubopplan = nullptr;

    /** Pointer to the previous suboperationplan of the parent operationplan. */
    OperationPlan* prevsubopplan = nullptr;

    /** Setup event of this operationplan. */
    SetupEvent* setupevent = nullptr;

    /** Quantity. */
    double quantity = 0.0;

    /** Flags on the operationplan: status, consumematerial, consumecapacity, infeasible. */
    unsigned short flags = 0;

    /** Hidden, static field to store the location during import. */
    static Location* loc;

    /** Hidden, static field to store the origin during import. */
    static Location* ori;

    /** Hidden, static field to store the supplier during import. */
    static Supplier* sup;

    /** Hidden, static field to store the order type during import. */
    static string ordertype;

    /** Hidden, static field to store the item during import. */
    static Item *itm;

    void setLocation(Location* l)
    {
      loc = l;
    }

    inline Location* getLocation() const;

    void setOrigin(Location* l)
    {
      ori = l;
    }

    inline Location* getOrigin() const;

    void setSupplier(Supplier* l)
    {
      sup = l;
    }

    inline Supplier* getSupplier() const;

    void setOrderType(const string& o)
    {
      ordertype = o;
    }

    void setItem(Item* i)
    {
      itm = i;
    }

    inline Item* getItem() const;
 };

 
template <class type> bool TimeLine<type>::Event::operator < (const Event& fl2) const
{
  if (getDate() != fl2.getDate())
    return getDate() < fl2.getDate();
  else if (getEventType() == 5 || fl2.getEventType() == 5)
  {
    if (getEventType() == 5 && fl2.getEventType() == 5)
    {
      auto o1 = getOperationPlan();
      auto o2 = fl2.getOperationPlan();
      if (o1 && o2)
        return *getOperationPlan() < *fl2.getOperationPlan();
      else
        return o2 ? true : false;
    }
    else
      return getEventType() > fl2.getEventType();
  }
  else if (fabs(getQuantity() - fl2.getQuantity()) > ROUNDING_ERROR)
	  return getQuantity() > fl2.getQuantity();
  else
  {
	  OperationPlan* op1 = getOperationPlan();
	  OperationPlan* op2 = fl2.getOperationPlan();
	  if (op1 && op2)
	    return *op1 < *op2;
	  else
	    return op1 == nullptr;
  }
}

		
/** @brief An operation represents an activity: these consume and produce material,
  * take time and also require capacity.
  *
  * An operation consumes and produces material, modeled through flows.<br>
  * An operation requires capacity, modeled through loads.
  *
  * This is an abstract base class for all different operation types.
  */
class Operation : public HasName<Operation>,
  public HasLevel, public Plannable, public HasDescription
{
    friend class Flow;
    friend class Load;
    friend class OperationPlan;
    friend class SubOperation;
    friend class Item;

  protected:
    /** Extra logic called when instantiating an operationplan.<br>
      * When the function returns false the creation of the operationplan
      * is denied and it is deleted.
      */
    virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true, bool use_start = false)
    {
      return true;
    }

  public:
    /** Default constructor. */
    explicit Operation() {}

    /** Destructor. */
    virtual ~Operation();

    virtual string getOrderType() const
    {
      return "MO";
    }

    OperationPlan* getFirstOpPlan() const
    {
      return first_opplan;
    }

    OperationPlan* getLastOpPlan() const
    {
      return last_opplan;
    }

    /** Returns the delay after this operation. */
    Duration getPostTime() const
    {
      return post_time;
    }

    /** Updates the delay after this operation.<br>
      * This delay is a soft constraint. This means that solvers should try to
      * respect this waiting time but can choose to leave a shorter time delay
      * if required.
      */
    void setPostTime(Duration t)
    {
      if (t<Duration(0L))
        throw DataException("No negative post-operation time allowed");
      post_time=t;
      setChanged();
    }

    /** Return the operation cost.<br>
      * The cost of executing this operation, per unit of the
      * operation_plan.<br>
      * The default value is 0.0.
      */
    double getCost() const
    {
      return cost;
    }

    /** Update the operation cost.<br>
      * The cost of executing this operation, per unit of the operation_plan.
      */
    void setCost(const double c)
    {
      if (c >= 0) cost = c;
      else throw DataException("Operation cost must be positive");
    }

    typedef Association<Operation,Buffer,Flow>::ListA flowlist;
    typedef Association<Operation,Resource,Load>::ListA loadlist;

    /** This is the factory method which creates all operationplans of the
      * operation. */
    OperationPlan* createOperationPlan(double, Date,
        Date, Demand* = nullptr, OperationPlan* = nullptr, unsigned long = 0,
        bool makeflowsloads=true, bool roundDown=true) const;

    /** Returns true for operation types that own suboperations. */
    virtual bool hasSubOperations() const
    {
      return false;
    }

    /** Calculates the daterange starting from (or ending at) a certain date
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
    DateRange calculateOperationTime(
      const OperationPlan* opplan, Date thedate, Duration duration,
      bool forward, Duration* actualduration = nullptr
    ) const;

    /** Calculates the effective, available time between two dates.
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
    DateRange calculateOperationTime(
      const OperationPlan* opplan, Date start, Date end, Duration* actualduration = nullptr
    ) const;

    /** This method stores ALL logic the operation needs to compute the
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
      bool preferEnd=true, bool execute=true, bool roundDown=true
      ) const = 0;

    /** Updates the quantity of an operationplan.<br>
      * This method considers the lot size constraints and also propagates
      * the new quantity to child operationplans.
      */
    virtual double setOperationPlanQuantity(
      OperationPlan* oplan, double f, bool roundDown, bool upd,
      bool execute, Date start
      ) const;

    /** Returns the location of the operation, which is used to model the
      * working hours and holidays. */
    Location* getLocation() const
    {
      return loc;
    }

    /** Updates the location of the operation, which is used to model the
      * working hours and holidays. */
    void setLocation(Location* l)
    {
      loc = l;
    }

    /** Returns the item. */
    Item* getItem() const
    {
      return item;
    }

    /** Updates the item. */
    void setItem(Item*);

    /** Update the priority. */
    void setPriority(int i)
    {
      priority = i;
    }

    /** Return the priority. */
    int getPriority() const
    {
      return priority;
    }

    /** Get the start date of the effectivity range. */
    Date getEffectiveStart() const
    {
      return effectivity.getStart();
    }

    /** Get the end date of the effectivity range. */
    Date getEffectiveEnd() const
    {
      return effectivity.getEnd();
    }

    /** Return the effectivity daterange.<br>
      * The default covers the complete time horizon.
      */
    DateRange getEffective() const
    {
      return effectivity;
    }

    /** Update the start date of the effectivity range. */
    void setEffectiveStart(Date d)
    {
      effectivity.setStart(d);
    }

    /** Update the end date of the effectivity range. */
    void setEffectiveEnd(Date d)
    {
      effectivity.setEnd(d);
    }

    /** Update the effectivity range. */
    void setEffective(DateRange dr)
    {
      effectivity = dr;
    }

    /** Returns the availability calendar of the operation. */
    Calendar *getAvailable() const
    {
      return available;
    }

    /** Updates the availability calendar of the operation. */
    void setAvailable(Calendar* b)
    {
      available = b;
    }

    /** Returns an reference to the list of flows.
      * TODO get rid of this method.
      */
    const flowlist& getFlows() const
    {
      return flowdata;
    }

    /** Returns an reference to the list of flows. */
    flowlist::const_iterator getFlowIterator() const
    {
      return flowdata.begin();
    }

    /** Returns an reference to the list of loads.
      * TODO get rid of this method.
      */
    const loadlist& getLoads() const
    {
      return loaddata;
    }

    /** Returns an reference to the list of loads. */
    loadlist::const_iterator getLoadIterator() const
    {
      return loaddata.begin();
    }

    OperationPlan::iterator getOperationPlans() const;

    /** Return the flow that is associates a given buffer with this
      * operation. Returns nullptr is no such flow exists. */
    Flow* findFlow(const Buffer* b, Date d) const;

    /** Return the load that is associates a given resource with this
      * operation. Returns nullptr is no such load exists. */
    Load* findLoad(const Resource* r, Date d) const
    {
      return loaddata.find(r,d);
    }

    /** Deletes all operationplans of this operation. The boolean parameter
      * controls whether we delete also locked operationplans or not.
      */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    /** Sets the minimum size of operationplans.<br>
      * The default value is 1.0
      */
    void setSizeMinimum(double f)
    {
      if (f<0)
        throw DataException("Operation can't have a negative minimum size");
      size_minimum = f;
      setChanged();
    }

    /** Returns the minimum size for operationplans. */
    double getSizeMinimum() const
    {
      return size_minimum;
    }

    /** Returns the calendar defining the minimum size of operationplans. */
    Calendar* getSizeMinimumCalendar() const
    {
      return size_minimum_calendar;
    }

    /** Sets the multiple size of operationplans. */
    void setSizeMultiple(double f)
    {
      if (f<0)
        throw DataException("Operation can't have a negative multiple size");
      size_multiple = f;
      setChanged();
    }

    /** Sets a calendar to defining the minimum size of operationplans. */
    virtual void setSizeMinimumCalendar(Calendar *c)
    {
      size_minimum_calendar = c;
      setChanged();
    }

    /** Returns the mutiple size for operationplans. */
    double getSizeMultiple() const
    {
      return size_multiple;
    }

    /** Sets the maximum size of operationplans. */
    void setSizeMaximum(double f)
    {
      if (f < size_minimum)
        throw DataException("Operation maximum size must be higher than the minimum size");
      if (f <= 0)
        throw DataException("Operation maximum size must be greater than 0");
      size_maximum = f;
      setChanged();
    }

    /** Returns the maximum size for operationplans. */
    double getSizeMaximum() const
    {
      return size_maximum;
    }

    /** Return the decoupled lead time of this operation.
      * TODO the decoupled lead time could vary over time, wich we don't handle now
      */
    virtual Duration getDecoupledLeadTime(double qty) const = 0;

    static PyObject* getDecoupledLeadTimePython(PyObject *self, PyObject *args);

    /** Add a new child operationplan.
      * By default an operationplan can have only a single suboperation,
      * representing a changeover.
      * Operation subclasses can implement their own restrictions on the
      * number and structure of the suboperationplans.
      * @see OperationAlternate::addSubOperationPlan
      * @see OperationRouting::addSubOperationPlan
      * @see OperationSplit::addSubOperationPlan
      */
    virtual void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool=true
      );

    static int initialize();

    /** Auxilary method to initialize an vector of availability calendar
      * iterators related to an operation.
      */
    void collectCalendars(
      vector<Calendar::EventIterator>&, Date, const OperationPlan*, bool forward = true
    ) const;
    
    virtual void solve(Solver &s, void* v = nullptr) const
    {
      s.solve(this,v);
    }

    typedef list<SubOperation*> Operationlist;

    /** Returns a reference to the list of sub operations of this operation.
      * The list is always sorted with the operation with the lowest priority
      * value at the start of the list.
      */
    virtual Operationlist& getSubOperations() const
    {
      return nosubOperations;
    }

    SubOperation::iterator getSubOperationIterator() const
    {
      return SubOperation::iterator(getSubOperations());
    }

    /** Returns a reference to the list of super-operations, i.e. operations
      * using the current Operation as a sub-Operation.
      */
    const list<Operation*>& getSuperOperations() const
    {
      return superoplist;
    }

    /** Returns a reference to the list of super-operations, i.e. operations
    * using the current Operation as a sub-Operation.
    */
    bool hasSuperOperations() const
    {
      return !superoplist.empty();
    }

    /** Register a super-operation, i.e. an operation having this one as a
      * sub-operation. */
    void addSuperOperation(Operation * o)
    {
      superoplist.push_front(o);
    }

    /** Removes a super-operation from the list. */
    void removeSuperOperation(Operation*);

    /** Return the release fence of this operation. */
    Duration getFence() const
    {
      return fence;
    }

    /** Update the release fence of this operation. */
    void setFence(Duration t)
    {
      if (fence!=t) setChanged();
      fence=t;
    }

    virtual void updateProblems();

    void setHidden(bool b)
    {
      if (hidden!=b) setChanged();
      hidden = b;
    }

    bool getHidden() const
    {
      return hidden;
    }

    static Operation* findFromName(string);

    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "", MANDATORY);
      HasDescription::registerFields<Cls>(m);
      Plannable::registerFields<Cls>(m);
      m->addDurationField<Cls>(Tags::posttime, &Cls::getPostTime, &Cls::setPostTime);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addDurationField<Cls>(Tags::fence, &Cls::getFence, &Cls::setFence);
      m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum, &Cls::setSizeMinimum, 1);
      m->addPointerField<Cls>(Tags::size_minimum_calendar, &Cls::getSizeMinimumCalendar, &Cls::setSizeMinimumCalendar);
      m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple, &Cls::setSizeMultiple);
      m->addDoubleField<Cls>(Tags::size_maximum, &Cls::getSizeMaximum, &Cls::setSizeMaximum, DBL_MAX);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, BASE + PLAN + WRITE_OBJECT_SVC);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      m->addPointerField<Cls, Calendar>(Tags::available, &Cls::getAvailable, &Cls::setAvailable);
      m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans, PLAN + DETAIL + DONT_SERIALIZE_SVC);
      m->addIteratorField<Cls, loadlist::const_iterator, Load>(Tags::loads, Tags::load, &Cls::getLoadIterator, BASE + WRITE_OBJECT);
      m->addIteratorField<Cls, flowlist::const_iterator, Flow>(Tags::flows, Tags::flow, &Cls::getFlowIterator, BASE + WRITE_OBJECT);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::hasSuperOperations, &Cls::hasSuperOperations, nullptr, BOOL_FALSE, DONT_SERIALIZE);
      HasLevel::registerFields<Cls>(m);
    }

    /** Return the memory size. */
    virtual size_t getSize() const
    {
      size_t tmp = Object::getSize();
      // Add the memory for the superoperation list: 3 pointers per superoperation
      tmp += superoplist.size() * 3 * sizeof(Operation*);
      return tmp;
    }

    /** Empty list of operations.<br>
    * For operation types which have no suboperations this list is
    * used as the list of suboperations.
    */
    static Operationlist nosubOperations;

  protected:
    void initOperationPlan(OperationPlan*, double,
        const Date&, const Date&, Demand*, OperationPlan*, unsigned long,
        bool = true, bool=true) const;

    typedef tuple<Resource*, SetupMatrixRule*, PooledString> SetupInfo;

    /** Calculate the setup time of an operationplan.
      * The date argument can either be the start or the end date
      * of a setup, depending on the value of the third argument.
      */
    SetupInfo calculateSetup(OperationPlan*, Date, SetupEvent* = nullptr, SetupEvent** = nullptr) const;

  private:
    /** List of operations using this operation as a sub-operation */
    list<Operation*> superoplist;

    /** Item produced by the operation. */
    Item* item = nullptr;

    /** Location of the operation.<br>
      * The location is used to model the working hours and holidays.
      */
    Location* loc = nullptr;

    /** Represents the time between this operation and a next one. */
    Duration post_time;

    /** Represents the release fence of this operation, i.e. a period of time
      * (relative to the current date of the plan) in which normally no
      * operationplan is allowed to be created.
      */
    Duration fence;

    /** Singly linked list of all flows of this operation. */
    flowlist flowdata;

    /** Singly linked list of all resources Loaded by this operation. */
    loadlist loaddata;

    /** Minimum size for operationplans. */
    double size_minimum = 1.0;

    /** Minimum size for operationplans when this size varies over time.
      * If this field is specified, the size_minimum field is ignored.
      */
    Calendar *size_minimum_calendar = nullptr;

    /** Multiple size for operationplans. */
    double size_multiple = 0.0;

    /** Maximum size for operationplans. */
    double size_maximum = DBL_MAX;

    /** Cost of the operation. */
    double cost = 0.0;

    /** A pointer to the first operationplan of this operation.<br>
      * All operationplans of this operation are stored in a sorted
      * doubly linked list.
      */
    OperationPlan* first_opplan = nullptr;

    /** A pointer to the last operationplan of this operation.<br>
      * All operationplans of this operation are stored in a sorted
      * doubly linked list.
      */
    OperationPlan* last_opplan = nullptr;

    /** A pointer to the next operation producing the item. */
    Operation* next = nullptr;

    /** Availability calendar of the operation. */
    Calendar* available = nullptr;

    /** Effectivity of the operation. */
    DateRange effectivity;

    /** Priority of the operation among alternates. */
    int priority = 1;

    /** Does the operation require serialization or not. */
    bool hidden = false;
};


/** Writes an operationplan to an output stream. */
inline ostream & operator << (ostream & os, const OperationPlan* o)
{
  if (o)
  {
    os << static_cast<const void*>(o) << " (";
    if (o->getOperation())
      os << o->getOperation()->getName();
    else
      os << "nullptr";
    os << ", " << o->getQuantity()
      << ", " << o->getStart();
    if (o->getSetupEnd() != o->getStart())
      os << " - " << o->getSetupEnd();
    os << " - " << o->getEnd();
    if (o->getApproved())
      os << ", approved)";
    else if (o->getConfirmed())
      os << ", confirmed)";
    else
      os << ")";
  }
  else
    os << "nullptr";
  return os;
}


inline string OperationPlan::getOrderType() const
{
  return oper ? oper->getOrderType() : "Unknown";
}


inline double OperationPlan::setQuantity(double f, bool roundDown,
  bool update, bool execute, Date end)
{
  return oper ?
    oper->setOperationPlanQuantity(this, f, roundDown, update, execute, end) :
    f;
}


inline int OperationPlan::getCluster() const
{
  return oper ? oper->getCluster() : 0;
}


Plannable* OperationPlan::getEntity() const
{
  return oper;
}


/** @brief A class to iterator over operationplans.
  *
  * Different modes are supported:
  *   - iterate over all operationplans of a single operation.
  *   - iterate over all sub-operationplans of a single operationplan.
  *   - iterate over all operationplans.
  */
class OperationPlan::iterator
{
  public:
    /** Constructor. The iterator will loop only over the operationplans
      * of the operation passed. */
    iterator(const Operation* x, bool forward = true) : op(Operation::end()), mode(forward ? 1 : 4)
    {
      if (!x)
        opplan = nullptr;
      else if (forward)
        opplan = x->getFirstOpPlan();
      else
        opplan = x->getLastOpPlan();
    }

    /** Constructor. The iterator will loop only over the suboperationplans
      * of the operationplan passed. */
    iterator(const OperationPlan* x) : op(Operation::end()), mode(2)
    {
      opplan = x ? x->firstsubopplan : nullptr;
    }

    /** Constructor. The iterator will loop over all operationplans. */
    iterator() : op(Operation::begin()), mode(3)
    {
      // The while loop is required since the first operation might not
      // have any operationplans at all
      while (op != Operation::end())
      {
        if (op->getFirstOpPlan())
        {
          opplan = op->getFirstOpPlan();
          return;
        }
        ++op;
      }
      opplan = nullptr;
    }

    /** Copy constructor. */
    iterator(const iterator& it) : opplan(it.opplan), op(it.op), mode(it.mode) {}

    /** Return the content of the current node. */
    OperationPlan& operator*() const
    {
      return *opplan;
    }

    /** Return the content of the current node. */
    OperationPlan* operator->() const
    {
      return opplan;
    }

    /** Pre-increment operator which moves the pointer to the next
      * element. */
    iterator& operator++()
    {
      if (opplan)
      {
        if (mode == 2)
          opplan = opplan->nextsubopplan;
        else if (mode == 4)
          opplan = opplan->prev;
        else
          opplan = opplan->next;
      }
      // Move to a new operation
      if (!opplan && mode == 3)
      {
        while (op != Operation::end())
        {
          ++op;
          if (op->getFirstOpPlan())
            break;
        }
        opplan = (op == Operation::end() ? nullptr : op->getFirstOpPlan());
      }
      return *this;
    }

    /** Post-increment operator which moves the pointer to the next
      * element. */
    iterator operator++(int)
    {
      iterator tmp(*this);
      if (mode == 2)
        opplan = opplan->nextsubopplan;
      else if (mode == 4)
        opplan = opplan->prev;
      else
        opplan = opplan->next;
      // Move to a new operation
      if (!opplan && mode == 3)
      {
        while (op != Operation::end())
        {
          ++op;
          if (op->getFirstOpPlan())
            break;
        }
        opplan = (op == Operation::end() ? nullptr : op->getFirstOpPlan());
      }
      return tmp;
    }

    /** Return current element and advance the iterator. */
    OperationPlan* next()
    {
      OperationPlan* tmp = opplan;
      operator++();
      return tmp;
    }

    /** Comparison operator. */
    bool operator==(const iterator& y) const
    {
      return opplan == y.opplan;
    }

    /** Inequality operator. */
    bool operator!=(const iterator& y) const
    {
      return opplan != y.opplan;
    }

  private:
    /** A pointer to current operationplan. */
    OperationPlan* opplan;

    /** An iterator over the operations. */
    Operation::iterator op;

    /** Describes the type of iterator.<br>
      * 1) iterate over operationplan instances of operation
      * 2) iterate over suboperationplans of an operationplan
      * 3) iterate over all operationplans
      * 4) iterate over operationplan instances of operation, same as 1 but backward in time
      */
    short mode;
};


inline OperationPlan::iterator OperationPlan::end()
{
  return iterator(static_cast<Operation*>(nullptr));
}


inline OperationPlan::iterator OperationPlan::begin()
{
  return iterator();
}


inline OperationPlan::iterator OperationPlan::getSubOperationPlans() const
{
  return OperationPlan::iterator(this);
}


/** A simple class to easily remember the date, quantity, setup and owner
  * of an operationplan.
  */
class OperationPlanState  // @todo should also be able to remember and restore suboperationplans!!!
{
  public:
    Date start;
    Date end;
    SetupEvent setup;
    double quantity;

    /** Default constructor. */
    OperationPlanState() : quantity(0.0) {}

    /** Constructor. */
    OperationPlanState(const OperationPlan* x) : setup(x->getSetupEvent())
    {
      if (!x)
      {
        quantity = 0.0;
        return;
      }
      else
      {
        start = x->getStart();
        end = x->getEnd();
        quantity = x->getQuantity();
      }
    }

    /** Copy constructor. */
    OperationPlanState(const OperationPlanState& x)
      : start(x.start), end(x.end), setup(x.setup), quantity(x.quantity) {}

    /** Constructor. */
    OperationPlanState(const Date x, const Date y, double q, SetupEvent* z = nullptr)
      : start(x), end(y), setup(z), quantity(q) {}

    /** Constructor. */
    OperationPlanState(const DateRange& x, double q, SetupEvent* z = nullptr)
      : start(x.getStart()), end(x.getEnd()), setup(z), quantity(q) {}

    /* Assignment operator. */
    OperationPlanState& operator =(const OperationPlanState & other)
    {
      start = other.start;
      end = other.end;
      setup = other.setup;
      quantity = other.quantity;
      return *this;
    }
};


/** @brief Models an operation that takes a fixed amount of time, independent
  * of the quantity. */
class OperationFixedTime : public Operation
{
  public:
    /** Default constructor. */
    explicit OperationFixedTime()
    {
      initType(metadata);
    }

    /** Returns the length of the operation. */
    Duration getDuration() const
    {
      return duration;
    }

    /** Updates the duration of the operation. Existing operation plans of this
      * operation are not automatically refreshed to reflect the change. */
    void setDuration(Duration t)
    {
      if (t < 0L)
        throw DataException("FixedTime operation can't have a negative duration");
      duration = t;
    }

    /** Return the decoupled lead time of this operation. */
    virtual Duration getDecoupledLeadTime(double qty) const;

    static int initialize();

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    /** A operation of this type enforces the following rules on its
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
      bool preferEnd=true, bool execute=true, bool roundDown=true
      ) const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDurationField<Cls>(Tags::duration, &Cls::getDuration, &Cls::setDuration);
    }
  protected:
    virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true, bool use_start = false);

  private:
    /** Stores the lengh of the Operation. */
    Duration duration;
};


/** @brief Models an operation whose duration is the sum of a constant time,
  * plus a certain time per unit.
  */
class OperationTimePer : public Operation
{
  public:
    /** Default constructor. */
    explicit OperationTimePer() : duration_per(0.0)
    {
      initType(metadata);
    }

    /** Returns the constant part of the operation time. */
    Duration getDuration() const
    {
      return duration;
    }

    /** Sets the constant part of the operation time. */
    void setDuration(Duration t)
    {
      if(t<0L)
        throw DataException("TimePer operation can't have a negative duration");
      duration = t;
    }

    /** Returns the time per unit of the operation time. */
    double getDurationPer() const
    {
      return duration_per;
    }

    /** Sets the time per unit of the operation time. */
    void setDurationPer(double t)
    {
      if(t < 0.0)
        throw DataException("TimePer operation can't have a negative duration-per");
      duration_per = t;
    }

    /** A operation of this type enforces the following rules on its
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
      bool preferEnd=true, bool execute=true, bool roundDown=true
      ) const;

    /** Return the decoupled lead time of this operation. */
    virtual Duration getDecoupledLeadTime(double qty) const;

    static int initialize();

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDurationField<Cls>(Tags::duration, &Cls::getDuration, &Cls::setDuration);
      m->addDurationDoubleField<Cls>(Tags::duration_per, &Cls::getDurationPer, &Cls::setDurationPer);
    }

  private:
    /** Constant part of the operation time. */
    Duration duration;

    /** Variable part of the operation time.
      * We store the value as a double value rather than a Duration to
      * be able to store fractional duration_per value. Duration can only
      * represent seconds.
      */
    double duration_per;
};


/** @brief Represents a routing operation, i.e. an operation consisting of
  * multiple, sequential sub-operations.
  */
class OperationRouting : public Operation
{
  public:
    /** Default constructor. */
    explicit OperationRouting()
    {
      initType(metadata);
    }

    /** Destructor. */
    ~OperationRouting();

    virtual bool hasSubOperations() const
    {
      return true;
    }

    /** A operation of this type enforces the following rules on its
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
      bool preferEnd=true, bool execute=true, bool roundDown=true
      ) const;

    double setOperationPlanQuantity(
      OperationPlan* oplan, double f, bool roundDown, bool upd,
      bool execute, Date end
      ) const;

    /** Add a new child operationplan.
      * When the third argument is true, we don't validate the insertion and just
      * insert it at the front of the unlocked operationplans.
      * When the third argument is false, we do a full validation. This means:
      * - The operation must be present in the routing
      * - An existing suboperationplan of the same operation is replaced with the
      *   the new child.
      * - The dates of subsequent suboperationplans in the routing are updated
      *   to start after the newly inserted one (except for confirmed operationplans)
      *   that can't be touched.
      */
    virtual void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool = true
      );

    /** Return the decoupled lead time of this operation. */
    virtual Duration getDecoupledLeadTime(double qty) const;

    static int initialize();

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    /** Return a list of all sub-operations. */
    virtual Operationlist& getSubOperations() const
    {
      return const_cast<Operationlist&>(steps);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator, BASE + WRITE_OBJECT);
    }

    /** Return the memory size. */
    virtual size_t getSize() const
    {
      size_t tmp = Operation::getSize();
      // Add the memory for the steps: 3 pointers per step
      tmp += steps.size() * 3 * sizeof(Operation*);
      return tmp;
    }

  protected:
    /** Extra logic to be used when instantiating an operationplan. */
    virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true, bool use_start = false);

  private:
    /** Stores a double linked list of all step suboperations. */
    Operationlist steps;
};


/** This type defines what mode used to search the alternates. */
enum SearchMode
{
  /** Select the alternate with the lowest priority number.<br>
    * This is the default.
    */
  PRIORITY = 0,
  /** Select the alternate which gives the lowest cost. */
  MINCOST = 1,
  /** Select the alternate which gives the lowest penalty. */
  MINPENALTY = 2,
  /** Select the alternate which gives the lowest sum of the cost and
    * penalty. */
  MINCOSTPENALTY = 3
};


/** Writes a search mode to an output stream. */
inline ostream & operator << (ostream & os, const SearchMode & d)
{
  switch (d)
  {
    case PRIORITY: os << "PRIORITY"; return os;
    case MINCOST: os << "MINCOST"; return os;
    case MINPENALTY: os << "MINPENALTY"; return os;
    case MINCOSTPENALTY: os << "MINCOSTPENALTY"; return os;
    default: assert(false); return os;
  }
}


/** Translate a string to a search mode value. */
SearchMode decodeSearchMode(const string& c);


/** @brief This class represents a split between multiple operations. */
class OperationSplit : public Operation
{
  public:
    /** Default constructor. */
    explicit OperationSplit()
    {
      initType(metadata);
    }

    /** Destructor. */
    ~OperationSplit();

    virtual bool hasSubOperations() const
    {
      return true;
    }

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - Very simple, accept any value. Ignore any lot size constraints
      *    since we use the ones on the sub operationplans.
      * @see Operation::setOperationPlanParameters
      */
    OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd=true, bool execute=true, bool roundDown=true
      ) const;

    /** Add a new child operationplan.
      * An alternate operationplan plan can have a maximum of 2
      * suboperationplans:
      *  - A setup operationplan if the alternate top-operation loads a
      *    resource requiring a specific setup.
      *  - An operationplan of any of the allowed suboperations.
      */
    virtual void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool=true
      );

    /** Return the decoupled lead time of this operation. 
      * Take the lead time of the longest operation.
      */
    virtual Duration getDecoupledLeadTime(double qty) const;

    virtual void solve(Solver &s, void* v = nullptr) const
    {
      s.solve(this,v);
    }

    virtual Operationlist& getSubOperations() const
    {
      return const_cast<Operationlist&>(alternates);
    }

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator, BASE + WRITE_OBJECT);
    }

    /** Return the memory size. */
    virtual size_t getSize() const
    {
      size_t tmp = Operation::getSize();
      // Add the memory for the suboperation list: 3 pointers per alternates
      tmp += alternates.size() * 3 * sizeof(Operation*);
      return tmp;
    }

  protected:
    /** Extra logic to be used when instantiating an operationplan. */
    virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true, bool use_start = false);

  private:
    /** List of all alternate operations. */
    Operationlist alternates;
};


/** @brief This class represents a choice between multiple operations. The
  * alternates are sorted in order of priority.
  */
class OperationAlternate : public Operation
{
  public:
    /** Default constructor. */
    explicit OperationAlternate() : search(PRIORITY)
    {
      initType(metadata);
    }

    /** Destructor. */
    ~OperationAlternate();

    virtual bool hasSubOperations() const
    {
      return true;
    }

    /** Return the search mode. */
    SearchMode getSearch() const
    {
      return search;
    }

    /** Update the search mode. */
    void setSearch(const string a)
    {
      search = decodeSearchMode(a);
    }

    virtual string getOrderType() const
    {
      return "ALT";
    }

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - Very simple, call the method with the same name on the alternate
      *    suboperationplan.
      * @see Operation::setOperationPlanParameters
      */
    OperationPlanState setOperationPlanParameters(
      OperationPlan* opplan, double qty, Date startdate, Date enddate,
      bool preferEnd=true, bool execute=true, bool roundDown=true
      ) const;

    /** Add a new child operationplan.
      * An alternate operationplan plan can have a maximum of 2
      * suboperationplans:
      *  - A setup operationplan if the alternate top-operation loads a
      *    resource requiring a specific setup.
      *  - An operationplan of any of the allowed suboperations.
      */
    virtual void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool=true
      );

    /** Return the decoupled lead time of this operation: 
      * Take the lead time of the preferred operation
      */
    virtual Duration getDecoupledLeadTime(double qty) const;

    virtual void solve(Solver &s, void* v = nullptr) const
    {
      s.solve(this,v);
    }

    virtual Operationlist& getSubOperations() const
    {
      return const_cast<Operationlist&>(alternates);
    }

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch, &Cls::setSearch, PRIORITY);
      m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator, BASE + WRITE_OBJECT);
    }

    /** Return the memory size. */
    virtual size_t getSize() const
    {
      size_t tmp = Operation::getSize();
      // Add the memory for the suboperation list: 3 pointers per alternates
      tmp += alternates.size() * 3 * sizeof(Operation*);
      return tmp;
    }

  protected:
    /** Extra logic to be used when instantiating an operationplan. */
    virtual bool extraInstantiate(OperationPlan* o, bool createsubopplans = true, bool use_start = false);

  private:
    /** List of all alternate operations. */
    Operationlist alternates;

    /** Mode to select the preferred alternates. */
    SearchMode search;
};


/** A class to iterato over alternates of an operationplan. */
class OperationPlan::AlternateIterator
{
  private:
    const OperationPlan* opplan = nullptr;
    vector<Operation*> opers;
    vector<Operation*>::iterator operIter;

  public:
    AlternateIterator(const OperationPlan* o);

    /** Copy constructor. */
    AlternateIterator(const AlternateIterator& other) : opplan(other.opplan)
    {
      for (auto i = other.opers.begin(); i != other.opers.end(); ++i)
        opers.push_back(*i);
      operIter = opers.begin();
    }

    Operation* next();
};


inline OperationPlan::AlternateIterator OperationPlan::getAlternates() const
{
  return OperationPlan::AlternateIterator(this);
}


/** @brief This class holds the definition of distribution replenishments. */
class ItemDistribution : public Object,
  public Association<Location,Item,ItemDistribution>::Node, public HasSource
{
  friend class OperationItemDistribution;
  friend class Item;
  public:
    class OperationIterator
    {
      private:
        OperationItemDistribution* curOper;

      public:
        /** Constructor. */
        OperationIterator(const ItemDistribution* i)
        {
          curOper = i ? i->firstOperation : nullptr;
        }

        /** Return current value and advance the iterator. */
        inline OperationItemDistribution* next();
    };

    /** Factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

    /** Constructor. */
    explicit ItemDistribution();

    /** Destructor. */
    virtual ~ItemDistribution();

    /** Search an existing object. */
    static Object* finder(const DataValueDict& k);

    /** Remove all shipping operationplans. */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static const MetaCategory* metacategory;

    /** Returns the item. */
    Item* getItem() const
    {
      return getPtrB();
    }

    /** Update the item. */
    void setItem(Item*);

    /** Returns the origin location. */
    Location* getOrigin() const
    {
      return orig;
    }

    /** Returns the destination location. */
    Location* getDestination() const
    {
      return getPtrA();
    }

    /** Updates the origin Location. This method can only be called once on each instance. */
    void setOrigin(Location* s)
    {
      if (!s) return;
      orig = s;
      HasLevel::triggerLazyRecomputation();
    }

    /** Updates the destination location. This method can only be called once on each instance. */
    void setDestination(Location* i)
    {
      if (!i) return;
      setPtrA(i, i->getDistributions());
      HasLevel::triggerLazyRecomputation();
    }

    /** Update the resource representing the supplier capacity. */
    void setResource(Resource* r)
    {
      res = r;
      HasLevel::triggerLazyRecomputation();
    }

    /** Return the resource representing the distribution capacity. */
    Resource* getResource() const
    {
      return res;
    }

    /** Update the resource capacity used per distributed unit. */
    void setResourceQuantity(double d)
    {
      if (d < 0)
        throw DataException("Resource_quantity must be positive");
      res_qty = d;
    }

    /** Return the resource capacity used per distributed unit. */
    double getResourceQuantity() const
    {
      return res_qty;
    }

    /** Return the purchasing leadtime. */
    Duration getLeadTime() const
    {
      return leadtime;
    }

    /** Update the shipping lead time.<br>
      * Note that any already existing purchase operations and their
      * operationplans are NOT updated.
      */
    void setLeadTime(Duration p)
    {
      if (p<0L)
        throw DataException("ItemDistribution can't have a negative lead time");
      leadtime = p;
    }

    /** Sets the minimum size for shipments.<br>
      * The default value is 1.0
      */
    void setSizeMinimum(double f)
    {
      if (f<0)
        throw DataException("ItemDistribution can't have a negative minimum size");
      size_minimum = f;
    }

    /** Returns the minimum size for shipments. */
    double getSizeMinimum() const
    {
      return size_minimum;
    }

    /** Sets the multiple size for shipments. */
    void setSizeMultiple(double f)
    {
      if (f<0)
        throw DataException("ItemDistribution can't have a negative multiple size");
      size_multiple = f;
    }

    /** Returns the mutiple size for shipments. */
    double getSizeMultiple() const
    {
      return size_multiple;
    }

    /** Returns the cost of shipping 1 unit of this item.<br>
      * The default value is 0.0.
      */
    double getCost() const
    {
      return cost;
    }

    /** Update the cost of shipping 1 unit. */
    void setCost(const double c)
    {
      if (c >= 0)
        cost = c;
      else
        throw DataException("ItemDistribution cost must be positive");
    }

    OperationIterator getOperations() const
    {
      return OperationIterator(this);
    }

    Duration getFence() const
    {
      return fence;
    }

    void setFence(Duration d)
    {
      fence = d;
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, MANDATORY + PARENT);
      m->addPointerField<Cls, Location>(Tags::origin, &Cls::getOrigin, &Cls::setOrigin);
      m->addPointerField<Cls, Location>(Tags::destination, &Cls::getDestination, &Cls::setDestination, BASE + PARENT);
      m->addDurationField<Cls>(Tags::leadtime, &Cls::getLeadTime, &Cls::setLeadTime);
      m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum, &Cls::setSizeMinimum, 1.0);
      m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple, &Cls::setSizeMultiple, 1.0);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource, &Cls::setResource);
      m->addDoubleField<Cls>(Tags::resource_qty, &Cls::getResourceQuantity, &Cls::setResourceQuantity, 1.0);
      m->addDurationField<Cls>(Tags::fence, &Cls::getFence, &Cls::setFence);
      m->addIteratorField<Cls, OperationIterator, OperationItemDistribution>(Tags::operations, Tags::operation, &Cls::getOperations, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasSource::registerFields<Cls>(m);
    }

  private:
    /** Source location. */
    Location* orig = nullptr;

    /** Shipping lead time. */
    Duration leadtime;

    /** Minimum procurement quantity. */
    double size_minimum = 1.0;

    /** Procurement multiple quantity. */
    double size_multiple = 1.0;

    /** Procurement cost. */
    double cost = 0.0;

    /** Pointer to the head of the auto-generated shipping operation list.*/
    OperationItemDistribution* firstOperation = nullptr;

    /** Resource to model distribution capacity. */
    Resource *res = nullptr;

    /** Consumption on the distribution capacity resource. */
    double res_qty = 1.0;

    /** Release fence for the distribution operation. */
    Duration fence;
};


/** @brief An item defines the products being planned, sold, stored and/or
  * manufactured. Buffers and demands have a reference an item.
  *
  * This is an abstract class.
  */
class Item : public HasHierarchy<Item>, public HasDescription
{
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

    /** Default constructor. */
    explicit Item() {}

    /** Return the cost of the item.<br>
      * The default value is 0.0.
      */
    double getCost() const
    {
      return cost;
    }

    /** Update the cost of the item. */
    void setCost(const double c)
    {
      if (c >= 0)
        cost = c;
      else
        throw DataException("Item cost must be positive");
    }

    /** Returns a constant reference to the list of items this supplier can deliver. */
    const supplierlist& getSuppliers() const
    {
      return suppliers;
    }

    /** Returns an iterator over the list of items this supplier can deliver. */
    supplierlist::const_iterator getSupplierIterator() const
    {
      return suppliers.begin();
    }

    const distributionlist& getDistributions() const
    {
      return distributions;
    }

    distributionlist::const_iterator getDistributionIterator() const
    {
      return distributions.begin();
    }

    /** Nested class to iterate of Operation objects producing this item. */
    class operationIterator
    {
      private:
        Operation* cur;

      public:
        /** Constructor. */
        operationIterator(const Item *c)
        {
          cur = c ? c->firstOperation : nullptr;
        }

        /** Return current value and advance the iterator. */
        Operation* next()
        {
          Operation* tmp = cur;
          if (cur)
            cur = cur->next;
          return tmp;
        }
    };

    operationIterator getOperationIterator() const
    {
      return this;
    }

    // Return an iterator over all buffers of this item
    inline bufferIterator getBufferIterator() const;

    // Return an iterator over all demands of this item
    inline demandIterator getDemandIterator() const;

    static int initialize();

    /** Return the cluster of this item. */
    int getCluster() const;

    /** Destructor. */
    virtual ~Item();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost, 0);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addIteratorField<Cls, supplierlist::const_iterator, ItemSupplier>(Tags::itemsuppliers, Tags::itemsupplier, &Cls::getSupplierIterator, BASE + WRITE_OBJECT);
      m->addIteratorField<Cls, distributionlist::const_iterator, ItemDistribution>(Tags::itemdistributions, Tags::itemdistribution, &Cls::getDistributionIterator, BASE + WRITE_OBJECT);
      m->addIteratorField<Cls, operationIterator, Operation>(Tags::operations, Tags::operation, &Cls::getOperationIterator, DONT_SERIALIZE);
      m->addIteratorField<Cls, bufferIterator, Buffer>(Tags::buffers, Tags::buffer, &Cls::getBufferIterator, DONT_SERIALIZE);
      m->addIteratorField<Cls, demandIterator, Demand>(Tags::demands, Tags::demand, &Cls::getDemandIterator, DONT_SERIALIZE);
      m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0, DONT_SERIALIZE);
    }

  private:
    /** This is the operation used to satisfy a demand for this item.
      * @see Demand
      */
    Operation* deliveryOperation = nullptr;

    /** Cost of the item. */
    double cost = 0.0;

    /** This is a list of suppliers this item has. */
    supplierlist suppliers;

    /** This is the list of itemdistributions of this item. */
    distributionlist distributions;

    /** Maintain a list of buffers. */
    Buffer *firstItemBuffer = nullptr;

    /** Maintain a list of demands. */
    Demand *firstItemDemand = nullptr;

    /** Maintain a list of operations producing this item. */
    Operation *firstOperation = nullptr;
};


/** @brief This class is the default implementation of the abstract Item
  * class. */
class ItemDefault : public Item
{
  public:
    /** Default constructor. */
    explicit ItemDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This class represents an item that can be purchased from a supplier. */
class ItemSupplier : public Object,
  public Association<Supplier,Item,ItemSupplier>::Node, public HasSource
{
  friend class OperationItemSupplier;
  public:
    /** Default constructor. */
    explicit ItemSupplier();

    /** Constructor. */
    explicit ItemSupplier(Supplier*, Item*, int);

    /** Constructor. */
    explicit ItemSupplier(Supplier*, Item*, int, DateRange);

    /** Destructor. */
    ~ItemSupplier();

    /** Search an existing object. */
    static Object* finder(const DataValueDict&);

    /** Initialize the class. */
    static int initialize();

    /** Returns the supplier. */
    Supplier* getSupplier() const
    {
      return getPtrA();
    }

    /** Returns the item. */
    Item* getItem() const
    {
      return getPtrB();
    }

    /** Updates the supplier. This method can only be called on an instance. */
    void setSupplier(Supplier* s)
    {
      if (s)
        setPtrA(s, s->getItems());
      HasLevel::triggerLazyRecomputation();
    }

    /** Updates the item. This method can only be called on an instance. */
    void setItem(Item* i)
    {
      if (i)
        setPtrB(i, i->getSuppliers());
      HasLevel::triggerLazyRecomputation();
    }

    /** Sets the minimum size for procurements.<br>
      * The default value is 1.0
      */
    void setSizeMinimum(double f)
    {
      if (f<0)
        throw DataException("ItemSupplier can't have a negative minimum size");
      size_minimum = f;
    }

    /** Returns the minimum size for procurements. */
    double getSizeMinimum() const
    {
      return size_minimum;
    }

    /** Sets the multiple size for procurements. */
    void setSizeMultiple(double f)
    {
      if (f<0)
        throw DataException("ItemSupplier can't have a negative multiple size");
      size_multiple = f;
    }

    /** Returns the mutiple size for procurements. */
    double getSizeMultiple() const
    {
      return size_multiple;
    }

    /** Returns the cost of purchasing 1 unit of this item from this supplier.<br>
      * The default value is 0.0.
      */
    double getCost() const
    {
      return cost;
    }

    /** Update the cost of purchasing 1 unit. */
    void setCost(const double c)
    {
      if (c >= 0)
        cost = c;
      else
        throw DataException("ItemSupplier cost must be positive");
    }

    /** Return the applicable location. */
    Location *getLocation() const
    {
      return loc;
    }

    /** Update the applicable locations.
      * Note that any already existing purchase operations and their
      * operationplans are NOT updated.
      */
    void setLocation(Location* l)
    {
      loc = l;
    }

    /** Update the resource representing the supplier capacity. */
    void setResource(Resource* r)
    {
      res = r;
      HasLevel::triggerLazyRecomputation();
    }

    /** Return the resource representing the supplier capacity. */
    Resource* getResource() const
    {
      return res;
    }

    /** Update the resource capacity used per purchased unit. */
    void setResourceQuantity(double d)
    {
      if (d < 0)
        throw DataException("Resource_quantity must be positive");
      res_qty = d;
    }

    /** Return the resource capacity used per purchased unit. */
    double getResourceQuantity() const
    {
      return res_qty;
    }

    Duration getFence() const
    {
      return fence;
    }

    void setFence(Duration d)
    {
      fence = d;
    }

    /** Return the purchasing lead time. */
    Duration getLeadTime() const
    {
      return leadtime;
    }

    /** Update the procurement lead time.<br>
      * Note that any already existing purchase operations and their
      * operationplans are NOT updated.
      */
    void setLeadTime(Duration p)
    {
      if (p<0L)
        throw DataException("ItemSupplier can't have a negative lead time");
      leadtime = p;
    }

    /** Remove all purchasing operationplans. */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static const MetaCategory* metacategory;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Supplier>(Tags::supplier, &Cls::getSupplier, &Cls::setSupplier, MANDATORY + PARENT);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, MANDATORY + PARENT);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addDurationField<Cls>(Tags::leadtime, &Cls::getLeadTime, &Cls::setLeadTime);
      m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum, &Cls::setSizeMinimum, 1.0);
      m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple, &Cls::setSizeMultiple, 1.0);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource, &Cls::setResource);
      m->addDoubleField<Cls>(Tags::resource_qty, &Cls::getResourceQuantity, &Cls::setResourceQuantity, 1.0);
      m->addDurationField<Cls>(Tags::fence, &Cls::getFence, &Cls::setFence);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasSource::registerFields<Cls>(m);
    }

  private:
    /** Factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

    /** Location where the supplier item applies to. */
    Location* loc = nullptr;

    /** Procurement lead time. */
    Duration leadtime;

    /** Minimum procurement quantity. */
    double size_minimum = 1.0;

    /** Procurement multiple quantity. */
    double size_multiple = 1.0;

    /** Procurement cost. */
    double cost = 0.0;

    /** Pointer to the head of the auto-generated purchase operation list.*/
    OperationItemSupplier* firstOperation = nullptr;

    /** Resource to model supplier capacity. */
    Resource *res = nullptr;

    /** Consumption on the supplier capacity resource. */
    double res_qty = 1.0;

    /** Release fence for the purchasing operation. */
    Duration fence;
};


/** @brief An internally generated operation that ships material from an
  * origin location to a destinationLocation.
  */
class OperationItemDistribution : public OperationFixedTime
{
  friend class ItemDistribution;
  private:
    /** Pointer to the ItemDistribution that 'owns' this operation. */
    ItemDistribution* itemdist;

    /** Pointer to the next operation of the supplier item. */
    OperationItemDistribution* nextOperation;

  public:
    ItemDistribution* getItemDistribution() const
    {
      return itemdist;
    }

    virtual string getOrderType() const
    {
      return "DO";
    }

    Buffer* getOrigin() const;

    Buffer* getDestination() const;

    static Operation* findOrCreate(ItemDistribution*, Buffer*, Buffer*);

    /** Constructor. */
    explicit OperationItemDistribution(ItemDistribution*, Buffer*, Buffer*);

    /** Destructor. */
    virtual ~OperationItemDistribution();

    static int initialize();

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, ItemDistribution>(Tags::itemdistribution, &Cls::getItemDistribution, nullptr);
      m->addPointerField<Cls, Buffer>(Tags::origin, &Cls::getOrigin, nullptr, MANDATORY);
      m->addPointerField<Cls, Buffer>(Tags::destination, &Cls::getDestination, nullptr, MANDATORY);
    }

    /** Scan and trim operationplans creating excess inventory in the
      * buffer.
      */
    void trimExcess() const;
};


OperationItemDistribution* ItemDistribution::OperationIterator::next()
{
  OperationItemDistribution* tmp = curOper;
  if (curOper)
    curOper = curOper->nextOperation;
  return tmp;
}


/** @brief An internally generated operation that supplies procured material
  * into a buffer.
  */
class OperationItemSupplier : public OperationFixedTime
{
  friend class ItemSupplier;
  private:
    /** Pointer to the ItemSupplier that 'owns' this operation. */
    ItemSupplier* supitem;

    /** Pointer to the next operation of the ItemSupplier. */
    OperationItemSupplier* nextOperation;

  public:
    ItemSupplier* getItemSupplier() const
    {
      return supitem;
    }

    virtual string getOrderType() const
    {
      return "PO";
    }

    Buffer* getBuffer() const;

    static OperationItemSupplier* findOrCreate(ItemSupplier*, Buffer*);

    /** Constructor. */
    explicit OperationItemSupplier(ItemSupplier*, Buffer*);

    /** Destructor. */
    virtual ~OperationItemSupplier();

    static int initialize();

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, ItemSupplier>(Tags::itemsupplier, &Cls::getItemSupplier, nullptr);
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, nullptr, DONT_SERIALIZE);
    }

    /** Scan and trim operationplans creating excess inventory in the
      * buffer.
      */
    void trimExcess(bool zero_or_minimum) const;
};


inline Location* OperationPlan::getOrigin() const
{
  if (!oper || oper->getType() != *OperationItemDistribution::metadata)
    return nullptr;
  return static_cast<OperationItemDistribution*>(oper)->getItemDistribution()->getOrigin();
}


Supplier* OperationPlan::getSupplier() const
{
  if (!oper || oper->getType() != *OperationItemSupplier::metadata)
    return nullptr;
  return static_cast<OperationItemSupplier*>(oper)->getItemSupplier()->getSupplier();
}


/** @brief A buffer represents a combination of a item and location.<br>
  * It is the entity for keeping modeling inventory.
  */
class Buffer : public HasHierarchy<Buffer>, public HasLevel,
  public Plannable, public HasDescription
{
    friend class Flow;
    friend class FlowPlan;

  public:
    typedef TimeLine<FlowPlan> flowplanlist;
    typedef Association<Operation,Buffer,Flow>::ListB flowlist;

    /** Default constructor. */
    explicit Buffer() {}

    static Buffer* findOrCreate(Item*, Location*);

    static Buffer* findFromName(string nm);

    /** Builds a producing operation for a buffer.
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

    /** Return the decoupled lead time of this buffer. */
    virtual Duration getDecoupledLeadTime(double qty, bool recurse_ip_buffers = true) const;

    static PyObject* getDecoupledLeadTimePython(PyObject *self, PyObject *args);
    
    /** Returns the operation that is used to supply extra supply into this
      * buffer. */
    Operation* getProducingOperation() const
    {
      if (producing_operation == uninitializedProducing)
        const_cast<Buffer*>(this)->buildProducingOperation();
      return producing_operation;
    }

    /** Updates the operation that is used to supply extra supply into this
      * buffer. */
    void setProducingOperation(Operation* o)
    {
      if (o && o->getHidden())
        logger << "Warning: avoid setting the producing operation to a hidden operation" << endl;
      producing_operation = o;
      setChanged();
    }

    /** Returns the item stored in this buffer. */
    Item* getItem() const
    {
      return it;
    }

    /** Updates the Item stored in this buffer. */
    void setItem(Item*);

    /** Returns the Location of this buffer. */
    Location* getLocation() const
    {
      return loc;
    }

    /** Updates the location of this buffer. */
    void setLocation(Location* i)
    {
      loc = i;
      // Trigger level recomputation
      HasLevel::triggerLazyRecomputation();
    }

    /** Returns the minimum inventory level. */
    double getMinimum() const
    {
      return min_val;
    }

    /** Return true if this buffer represents a tool. */
    bool getTool() const
    {
      return tool;
    }

    /** Marks the buffer a tool. */
    void setTool(bool b)
    {
      tool = b;
    }

    /** Debugging function. */
    void inspect(string msg = "") const;

    static PyObject* inspectPython(PyObject*, PyObject*);

    /** Return a pointer to the next buffer for the same item. */
    Buffer* getNextItemBuffer() const
    {
      return nextItemBuffer;
    }

    /** Returns a pointer to a calendar for storing the minimum inventory
      * level. */
    Calendar* getMinimumCalendar() const
    {
      return min_cal;
    }

    /** Returns the maximum inventory level. */
    double getMaximum() const
    {
      return max_val;
    }

    /** Returns a pointer to a calendar for storing the maximum inventory
      * level. */
    Calendar* getMaximumCalendar() const
    {
      return max_cal;
    }

    /** Updates the minimum inventory target for the buffer. */
    void setMinimum(double);

    /** Updates the minimum inventory target for the buffer. */
    void setMinimumCalendar(Calendar*);

    /** Updates the minimum inventory target for the buffer. */
    void setMaximum(double);

    /** Updates the minimum inventory target for the buffer. */
    void setMaximumCalendar(Calendar*);

    /** Initialize the class. */
    static int initialize();

    /** Destructor. */
    virtual ~Buffer();

    /** Returns the available material on hand immediately after the
      * given date.
      */
    double getOnHand(Date d) const;

    /** Return the current on hand value, using the instance of the inventory
      * operation.
      */
    double getOnHand() const;

    /** Update the on-hand inventory at the start of the planning horizon. */
    void setOnHand(double f);

    /** Returns minimum or maximum available material on hand in the given
      * daterange. The third parameter specifies whether we return the
      * minimum (which is the default) or the maximum value.
      * The computation is INclusive the start and end dates.
      */
    double getOnHand(Date, Date, bool min = true) const;

    /** Returns a reference to the list of all flows of this buffer. */
    const flowlist& getFlows() const
    {
      return flows;
    }

    flowlist::const_iterator getFlowIterator() const
    {
      return flows.begin();
    }

    virtual void solve(Solver &s, void* v = nullptr) const
    {
      s.solve(this,v);
    }

    /** Returns a reference to the list of all flow plans of this buffer. */
    const flowplanlist& getFlowPlans() const
    {
      return flowplans;
    }

    flowplanlist::const_iterator getFlowPlanIterator() const
    {
      return flowplans.begin();
    }

    /** Returns a reference to the list of all flow plans of this buffer. */
    flowplanlist& getFlowPlans()
    {
      return flowplans;
    }

    /** Return the flow that is associates a given operation with this buffer.
      * Returns nullptr is no such flow exists. */
    Flow* findFlow(const Operation* o, Date d) const
    {
      return o ? o->findFlow(this, d) : nullptr;
    }

    /** Deletes all operationplans consuming from or producing from this
      * buffer. The boolean parameter controls whether we delete also locked
      * operationplans or not.
      */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    virtual void updateProblems();

    void setHidden(bool b)
    {
      if (hidden!=b) setChanged();
      hidden = b;
    }

    bool getHidden() const
    {
      return hidden;
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    /** This function matches producing and consuming operationplans
      * with each other, and updates the pegging iterator accordingly.
      */
    void followPegging
      (PeggingIterator&, FlowPlan*, double, double, short);

    /** Return the minimum interval between purchasing operations.<br>
      * This parameter doesn't control the timing of the first purchasing
      * operation, but only to the subsequent ones.
      */
    Duration getMinimumInterval() const
    {
      return min_interval;
    }

    /** Update the minimum time between replenishments. */
    void setMinimumInterval(Duration p)
    {
      min_interval = p;
      // Minimum is increased over the maximum: auto-increase the maximum
      if (max_interval && max_interval < min_interval)
        max_interval = min_interval;
    }

    /** Return the maximum time interval between sytem-generated replenishment
      * operations.
      */
    Duration getMaximumInterval() const
    {
      return max_interval;
    }

    /** Update the minimum time between replenishments. */
    void setMaximumInterval(Duration p)
    {
      max_interval = p;
      // Maximum is lowered below the minimum: auto-decrease the minimum
      if (min_interval && max_interval < min_interval)
        min_interval = max_interval;
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addPointerField<Cls, Operation>(Tags::producing, &Cls::getProducingOperation, &Cls::setProducingOperation);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, BASE + WRITE_OBJECT_SVC);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      Plannable::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnHand, &Cls::setOnHand);
      m->addDoubleField<Cls>(Tags::minimum, &Cls::getMinimum, &Cls::setMinimum);
      m->addPointerField<Cls, Calendar>(Tags::minimum_calendar, &Cls::getMinimumCalendar, &Cls::setMinimumCalendar);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMaximum, &Cls::setMaximum, default_max);
      m->addPointerField<Cls, Calendar>(Tags::maximum_calendar, &Cls::getMaximumCalendar, &Cls::setMaximumCalendar);
      m->addDurationField<Cls>(Tags::mininterval, &Cls::getMinimumInterval, &Cls::setMinimumInterval, -1L);
      m->addDurationField<Cls>(Tags::maxinterval, &Cls::getMaximumInterval, &Cls::setMaximumInterval);
      m->addIteratorField<Cls, flowlist::const_iterator, Flow>(Tags::flows, Tags::flow, &Cls::getFlowIterator, DETAIL);
      m->addBoolField<Cls>(Tags::tool, &Cls::getTool, &Cls::setTool, BOOL_FALSE);
      m->addIteratorField<Cls, flowplanlist::const_iterator, FlowPlan>(Tags::flowplans, Tags::flowplan, &Cls::getFlowPlanIterator, PLAN + WRITE_OBJECT + WRITE_HIDDEN);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasLevel::registerFields<Cls>(m);
    }

    /** A dummy producing operation to mark uninitialized ones. */
    static OperationFixedTime *uninitializedProducing;

  private:
    /** A constant defining the default max inventory target.\\
      * Theoretically we should set this to DBL_MAX, but then the results
      * are not portable across platforms.
      */
    static const double default_max;

    /** This models the dynamic part of the plan, representing all planned
      * material flows on this buffer. */
    flowplanlist flowplans;

    /** This models the defined material flows on this buffer. */
    flowlist flows;

    /** Hide this entity from serialization or not. */
    bool hidden = false;

    /** This is the operation used to create extra material in this buffer. */
    Operation *producing_operation = uninitializedProducing;

    /** Location of this buffer.<br>
      * This field is only used as information.<br>
      * The default is nullptr.
      */
    Location* loc = nullptr;

    /** Item being stored in this buffer.<br>
      * The default value is nullptr.
      */
    Item* it = nullptr;

    /** Minimum inventory target.<br>
      * If a minimum calendar is specified this field is ignored.
      * @see min_cal
      */
    double min_val = 0.0;

    /** Maximum inventory target. <br>
      * If a maximum calendar is specified this field is ignored.
      * @see max_cal
      */
    double max_val = default_max;

    /** Points to a calendar to store the minimum inventory level.<br>
      * The default value is nullptr, resulting in a constant minimum level
      * of 0.
      */
    Calendar *min_cal = nullptr;

    /** Points to a calendar to store the maximum inventory level.<br>
      * The default value is nullptr, resulting in a buffer without excess
      * inventory problems.
      */
    Calendar *max_cal = nullptr;

    /** Minimum time interval between purchasing operations. */
    Duration min_interval = -1L;

    /** Maximum time interval between purchasing operations. */
    Duration max_interval;

    /** Maintain a linked list of buffers per item. */
    Buffer *nextItemBuffer = nullptr;

    /** A flag that marks whether this buffer represents a tool or not. */
    bool tool = false;
};


/** @brief An internally generated operation to represent inventory. */
class OperationInventory : public OperationFixedTime
{
  friend class Buffer;
  private:
    /** Constructor. */
    explicit OperationInventory(Buffer*);

    /** Destructor. */
    virtual ~OperationInventory() {}

  public:
    Buffer *getBuffer() const;

    static int initialize();

    virtual string getOrderType() const
    {
      return "STCK";
    }

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, nullptr, DONT_SERIALIZE);
    }
};


/** @brief An internally generated operation to represent a zero time delivery. */
class OperationDelivery : public OperationFixedTime
{
  friend class Demand;
  public:
    /** Default constructor. */
    explicit OperationDelivery();

    /** Destructor. */
    virtual ~OperationDelivery() {}

    /** Return the delivery buffer. */
    Buffer *getBuffer() const;

    /** Update the delivery buffer. */
    void setBuffer(Buffer*);

    static int initialize();

    virtual string getOrderType() const
    {
      return "DLVR";
    }

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, &Cls::setBuffer, MANDATORY);
    }
};


inline bool OperationPlan::getHidden() const
{
  if (getOperation() && getOperation()->getType() == *OperationInventory::metadata)
    return true;
  else
    return false;
}


inline Location* OperationPlan::getLocation() const
{
  if (!oper)
    return nullptr;
  else if (oper->getType() == *OperationItemSupplier::metadata)
    return static_cast<OperationItemSupplier*>(oper)->getBuffer()->getLocation();
  else if (oper->getType() == *OperationItemDistribution::metadata)
    return static_cast<OperationItemDistribution*>(oper)->getDestination()->getLocation();
  else if (oper->getType() == *OperationInventory::metadata)
    return static_cast<OperationInventory*>(oper)->getBuffer()->getLocation();
  else if (oper->getType() == *OperationDelivery::metadata)
    return static_cast<OperationDelivery*>(oper)->getBuffer()->getLocation();
  else
    return nullptr;
}


Item* OperationPlan::getItem() const
{
  if (!oper)
    return nullptr;
  else if (oper->getType() == *OperationItemSupplier::metadata)
    return static_cast<OperationItemSupplier*>(oper)->getBuffer()->getItem();
  else if (oper->getType() == *OperationItemDistribution::metadata)
    return static_cast<OperationItemDistribution*>(oper)->getDestination()->getItem();
  else if (oper->getType() == *OperationInventory::metadata)
    return static_cast<OperationInventory*>(oper)->getBuffer()->getItem();
  else if (oper->getType() == *OperationDelivery::metadata)
    return static_cast<OperationDelivery*>(oper)->getBuffer()->getItem();
  else
    return nullptr;
}


class Item::bufferIterator
{
  private:
    Buffer* cur;

  public:
    /** Constructor. */
    bufferIterator(const Item* i) : cur(i ? i->firstItemBuffer : nullptr) {}

    bool operator != (const bufferIterator &b) const
    {
      return b.cur != cur;
    }

    bool operator == (const bufferIterator &b) const
    {
      return b.cur == cur;
    }

    bufferIterator& operator++()
    {
      if (cur)
        cur = cur->getNextItemBuffer();
      return *this;
    }

    bufferIterator operator++(int)
    {
      bufferIterator tmp = *this;
      ++*this;
      return tmp;
    }

    Buffer* next()
    {
      Buffer *tmp = cur;
      if (cur)
        cur = cur->getNextItemBuffer();
      return tmp;
    }

    Buffer* operator ->() const
    {
      return cur;
    }

    Buffer& operator *() const
    {
      return *cur;
    }
};


inline Item::bufferIterator Item::getBufferIterator() const
{
  return this;
}


inline int Item::getCluster() const
{
  return firstItemBuffer ? firstItemBuffer->getCluster() : 0;
}


/** @brief This class is the default implementation of the abstract Buffer class. */
class BufferDefault : public Buffer
{
  public:
    explicit BufferDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief  This class represents a material buffer with an infinite supply of extra
  * material.
  *
  * In other words, it never constrains the plan and it doesn't propagate any
  * requirements upstream.
  */
class BufferInfinite : public Buffer
{
  public:
    explicit BufferInfinite()
    {
      setDetectProblems(false);
      setProducingOperation(nullptr);
      initType(metadata);
    }

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}
    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This class defines a material flow to/from a buffer, linked with an
  * operation. This default implementation plans the material flow at the
  * start of the operation, after the setup time has been completed.
  */
class Flow : public Object, public Association<Operation,Buffer,Flow>::Node,
  public Solvable, public HasSource
{
  public:
    /** Destructor. */
    virtual ~Flow();

    /** Constructor. */
    explicit Flow(Operation* o, Buffer* b, double q) : quantity(q)
    {
      setOperation(o);
      setBuffer(b);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Constructor. */
    explicit Flow(Operation* o, Buffer* b, double q, DateRange e) : quantity(q)
    {
      setOperation(o);
      setBuffer(b);
      setEffective(e);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Search an existing object. */
    static Object* finder(const DataValueDict&);

    /** Returns the operation. */
    Operation* getOperation() const
    {
      return getPtrA();
    }

    /** Updates the operation of this flow. This method can be called only ONCE
      * for each flow. In case that doesn't suit you, delete the existing flow
      * and create a new one.
      */
    void setOperation(Operation* o)
    {
      if (o) setPtrA(o,o->getFlows());
    }

    /** Returns true if this flow consumes material from the buffer. */
    bool isConsumer() const
    {
      return quantity < 0 || quantity_fixed < 0;
    }

    /** Returns true if this flow produces material into the buffer. */
    bool isProducer() const
    {
      return quantity > 0 || quantity_fixed > 0 || (quantity == 0 && quantity_fixed == 0);
    }

    /** Returns the material flow PER UNIT of the operationplan. */
    double getQuantity() const
    {
      return quantity;
    }

    /** Updates the material flow PER UNIT of the operationplan. Existing
      * flowplans are NOT updated to take the new quantity in effect. Only new
      * operationplans and updates to existing ones will use the new quantity
      * value.
      */
    void setQuantity(double f)
    {
      quantity = f;
      if ((quantity > 0.0 && quantity_fixed < 0)
        || (quantity < 0.0 && quantity_fixed > 0))
        throw DataException("Quantity and quantity_fixed must have equal sign");
    }

    /** Returns the CONSTANT material flow PER UNIT of the operationplan. */
    double getQuantityFixed() const
    {
      return quantity_fixed;
    }

    /** Updates the CONSTANT material flow of the operationplan. Existing
      * flowplans are NOT updated to take the new quantity in effect. Only new
      * operationplans and updates to existing ones will use the new quantity
      * value.
      */
    void setQuantityFixed(double f)
    {
      quantity_fixed = f;
      if ((quantity > 0.0 && quantity_fixed < 0)
        || (quantity < 0.0 && quantity_fixed > 0))
        throw DataException("Quantity and quantity_fixed must have equal sign");
    }

    /** Returns the buffer. */
    Buffer* getBuffer() const
    {
      Buffer* b = getPtrB();
      if (b) return b;

      // Dynamically set the buffer
      if (item && getOperation() && getOperation()->getLocation())
      {
        b = Buffer::findOrCreate(item, getOperation()->getLocation());
        if (b)
          const_cast<Flow*>(this)->setPtrB(b, b->getFlows());
      }
      if (!b)
        throw DataException("Flow doesn't have a buffer");
      return b;
    }

    /** Updates the buffer of this flow. This method can be called only ONCE
      * for each flow. In case that doesn't suit you, delete the existing flow
      * and create a new one.
      */
    void setBuffer(Buffer* b)
    {
      if (b) setPtrB(b,b->getFlows());
    }

    Item* getItem() const
    {
      return getPtrB() ? getPtrB()->getItem() : item;
    }

    void setItem(Item* i)
    {
      if (getPtrB() && getPtrB()->getItem() != i)
        throw DataException("Invalid update of operationmaterial");
      item = i;
    }

    /** Return the leading flow of this group.
      * When the flow has no alternate or if the flow is itself leading
      * then nullptr is returned.
      */
    Flow* getAlternate() const
    {
      if (getName().empty() || !getOperation())
        return nullptr;
      for (Operation::flowlist::const_iterator h=getOperation()->getFlows().begin();
        h!=getOperation()->getFlows().end() && this != &*h; ++h)
        if (getName() == h->getName())
          return const_cast<Flow*>(&*h);
      return nullptr;
    }

    /** Return whether the flow has alternates. */
    bool hasAlternates() const
    {
      if (getName().empty() || !getOperation())
        return false;
      for (Operation::flowlist::const_iterator h=getOperation()->getFlows().begin();
        h!=getOperation()->getFlows().end(); ++h)
        if (getName() == h->getName() && this != &*h)
          return true;
      return false;
    }

    /** Return the search mode. */
    SearchMode getSearch() const
    {
      return search;
    }

    /** Update the search mode. */
    void setSearch(const string a)
    {
      search = decodeSearchMode(a);
    }

    /** A flow is considered hidden when either its buffer or operation
      * are hidden. */
    virtual bool getHidden() const
    {
      return (getBuffer() && getBuffer()->getHidden())
          || (getOperation() && getOperation()->getHidden());
    }

    /** This method holds the logic the compute the date and quantity of a flowplan. */
    virtual pair<Date, double> getFlowplanDateQuantity(const FlowPlan*) const;

    static int initialize();

    string getTypeName() const
    {
      return getType().type;
    }

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation, MANDATORY + PARENT);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, MANDATORY + PARENT);
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, &Cls::setBuffer, DONT_SERIALIZE + PARENT);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity);
      m->addDoubleField<Cls>(Tags::quantity_fixed, &Cls::getQuantityFixed, &Cls::setQuantityFixed);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName);
      m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch, &Cls::setSearch, PRIORITY);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      HasSource::registerFields<Cls>(m);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
    	// Not very nice: all flow subclasses appear to Python as instance of a
	    // single Python class. We use this method to distinguish them.
      m->addStringField<Cls>(Tags::type, &Cls::getTypeName, nullptr, "", DONT_SERIALIZE);
    }

  protected:
    /** Default constructor. */
    explicit Flow()
    {
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

  private:
    /** Item of the flow. This can be used to automatically generate the buffer
      * when and if needed.
      */
    Item *item = nullptr;

    /** Variable quantity of the material consumption/production. */
    double quantity = 0.0;

    /** Constant quantity of the material consumption/production. */
    double quantity_fixed = 0.0;

    /** Mode to select the preferred alternates. */
    SearchMode search = PRIORITY;

    static PyObject* create(PyTypeObject* pytype, PyObject*, PyObject*);
};


/** @brief This class defines a material flow to/from a buffer, linked with an
  * operation. This subclass represents a flow that is at the start date of
  * the operation.
  */
class FlowStart : public Flow
{
  public:
    /** Constructor. */
    explicit FlowStart(Operation* o, Buffer* b, double q) : Flow(o,b,q) {}

    /** This constructor is called from the plan begin_element function. */
    explicit FlowStart() {}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}
};


/** @brief This class defines a material flow to/from a buffer, linked with an
  * operation. This subclass represents a flow that is at end date of the
  * operation.
  */
class FlowEnd : public Flow
{
  public:
    /** Constructor. */
    explicit FlowEnd(Operation* o, Buffer* b, double q) : Flow(o,b,q) {}

    /** This constructor is called from the plan begin_element function. */
    explicit FlowEnd() {}

    /** This method holds the logic the compute the date and quantity of a flowplan. */
    virtual pair<Date, double> getFlowplanDateQuantity(const FlowPlan*) const;

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
};


/** @brief This class represents a flow producing/material of a fixed quantity
  * spread across the total duration of the operationplan
  *
  * TODO The implementation of this class ignores date effectivity.
  */
class FlowTransferBatch : public Flow
{
  private:
    double transferbatch = 0;

  public:
    /** Constructor. */
    explicit FlowTransferBatch(Operation* o, Buffer* b, double q) : Flow(o, b, q) 
    {
      initType(metadata);
    }

    /** This constructor is called from the plan begin_element function. */
    explicit FlowTransferBatch() 
    {
      initType(metadata);
    }

    double getTransferBatch() const
    {
      return transferbatch;
    }

    void setTransferBatch(double d)
    {
      if (d < 0.0)
        throw DataException("Transfer batch size must be greater than or equal to 0");
      transferbatch = d;
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDoubleField<Cls>(Tags::transferbatch, &Cls::getTransferBatch, &Cls::setTransferBatch);
    }

    /** This method holds the logic the compute the date and quantity of a flowplan. */
    virtual pair<Date, double> getFlowplanDateQuantity(const FlowPlan*) const;

    virtual void solve(Solver &s, void* v = nullptr) const { s.solve(this, v); }

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaClass* metadata;
};


/** @brief A flowplan represents a planned material flow in or out of a buffer.
  *
  * Flowplans are owned by operationplans, which manage a container to store
  * them.
  */
class FlowPlan : public TimeLine<FlowPlan>::EventChangeOnhand
{
    friend class OperationPlan::FlowPlanIterator;
    friend class OperationPlan;
    friend class FlowTransferBatch;
  private:
    // Static constants
    static const short STATUS_CONFIRMED = 1;
    static const short FOLLOWING_BATCH = 2;

    /** Points to the flow instantiated by this flowplan. */
    Flow *fl = nullptr;

    /** Points to the operationplan owning this flowplan. */
    OperationPlan *oper = nullptr;

    /** Points to the next flowplan owned by the same operationplan. */
    FlowPlan *nextFlowPlan = nullptr;

    /** Finds the flowplan on the operationplan when we read data. */
    static Object* reader(const MetaClass*, const DataValueDict&, CommandManager*);

    /** Is this operationplanmaterial locked?
        LEAVE THIS VARIABLE DECLARATION BELOW THE OTHERS
    */
    short flags = 0;

  public:

    static const MetaClass *metadata;
    static const MetaCategory *metacategory;
    static int initialize();
    virtual const MetaClass& getType() const { return *metadata; }

    /** Constructor. */
    explicit FlowPlan(OperationPlan*, const Flow*);

    /** Constructor. */
    explicit FlowPlan(OperationPlan*, const Flow*, Date, double);

    bool isConfirmed() const
    {
      return (flags & STATUS_CONFIRMED) != 0;
    }

    bool isFollowingBatch() const
    {
      return (flags & FOLLOWING_BATCH) != 0;
    }

    void setFollowingBatch(bool b)
    {
      if (b)
        flags |= FOLLOWING_BATCH;
      else
        flags &= ~FOLLOWING_BATCH;
    }

    /** Returns the flow of which this is an plan instance. */
    Flow* getFlow() const
    {
      return fl;
    }

    /** Returns the buffer, a convenient shortcut. */
    Buffer* getBuffer() const
    {
      return fl ? fl->getBuffer() : nullptr;
    }

    /** Returns the operation, a convenient shortcut. */
    Operation* getOperation() const
    {
      return fl ? fl->getOperation() : nullptr;
    }

    /** Returns the item being produced or consumed. */
    Item* getItem() const
    {
      return (fl && fl->getBuffer()) ? fl->getBuffer()->getItem() : nullptr;
    }

    /** Update the flowplan to a different item.
    * The new flow must belong to the same operation.
    */
    void setItem(Item*);

    /** Update the operationplan.
      * This can only be called once.
      */
    void setOperationPlan(OperationPlan* o)
    {
      if (oper && oper != o)
        throw DataException("Can't change the operationplan of a flowplan");
      else
        oper = o;
    }

    /** Update the flow of an already existing flowplan.<br>
      * The new flow must belong to the same operation.
      */
    void setFlow(Flow*);

    /** Returns the operationplan owning this flowplan. */
    virtual OperationPlan* getOperationPlan() const
    {
      return oper;
    }

    /** Return the status of the operationplanmaterial.
    * The status string is one of the following:
    *   - proposed
    *   - confirmed
    */
    string getStatus() const;

    /** Update the status of the operationplanmaterial. */
    void setStatus(const string&);

    /** Returns the duration before the current onhand will be completely consumed. */
    Duration getPeriodOfCover() const;

    /** Destructor. */
    virtual ~FlowPlan()
    {
      Buffer* b = getFlow()->getBuffer();
      b->setChanged();
      b->flowplans.erase(this);
    }

    void setQuantityAPI(double quantity)
    {
      setQuantity(quantity, false, true, true);
    }

    /** Updates the quantity of the flowplan by changing the quantity of the
      * operationplan owning this flowplan.<br>
      * The boolean parameter is used to control whether to round up (false)
      * or down (true) in case the operation quantity must be a multiple.<br>
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
      */
    pair<double, double> setQuantity(
      double quantity, bool rounddown=false, bool update=true,
      bool execute=true, short mode = 2
      );

    /** This function needs to be called whenever the flowplan date or
      * quantity are changed.
      */
    void update();

    /** Return a pointer to the timeline data structure owning this flowplan. */
    TimeLine<FlowPlan>* getTimeLine() const
    {
      return &(getFlow()->getBuffer()->flowplans);
    }

    /** Returns true when the flowplan is hidden.<br>
      * This is determined by looking at whether the flow is hidden or not.
      */
    bool getHidden() const
    {
      return fl->getHidden();
    }

    void setDate(Date d)
    {
      if (isConfirmed())
      {
        // Update the timeline data structure
        getFlow()->getBuffer()->flowplans.update(
          this,
          getQuantity(),
          d
        );

        // Mark the operation and buffer as having changed. This will trigger the
        // recomputation of their problems
        fl->getBuffer()->setChanged();
        fl->getOperation()->setChanged();
      }
      else {
        throw DataException("Unhandled case: Cannot change a date of a proposed FlowPlan");
      }
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDateField<Cls>(Tags::date, &Cls::getDate, &Cls::setDate);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantityAPI);
      m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnhand, nullptr, -666);
      m->addDoubleField<Cls>(Tags::minimum, &Cls::getMin);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMax);
      m->addDurationField<Cls>(Tags::period_of_cover, &Cls::getPeriodOfCover, nullptr);
      m->addStringField<Cls>(Tags::status, &Cls::getStatus, &Cls::setStatus, "proposed");
      m->addPointerField<Cls, OperationPlan>(Tags::operationplan, &Cls::getOperationPlan, &Cls::setOperationPlan, BASE + WRITE_OBJECT + PARENT);
      m->addPointerField<Cls, Flow>(Tags::flow, &Cls::getFlow, &Cls::setFlow, DONT_SERIALIZE);
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, nullptr);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, DONT_SERIALIZE);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, nullptr, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, nullptr, BOOL_FALSE, DONT_SERIALIZE);
    }
};


/** @brief An specific changeover rule in a setup matrix. */
class SetupMatrixRule : public Object
{
    friend class SetupMatrix;
  public:

    /** Default constructor. */
    SetupMatrixRule() {}

    /** Constructor. */
    SetupMatrixRule(SetupMatrix* m, PooledString f, PooledString t, Duration d, double c, int p)
      : matrix(m), from(f), to(t), duration(d), cost(c), priority(p) {}

    /** Update the matrix pointer. */
    void setSetupMatrix(SetupMatrix*);

    /** Destructor. */
    ~SetupMatrixRule();

    static int initialize();

    static const MetaCategory* metadata;

    /** Factory method. */
    static Object* reader(
      const MetaClass*, const DataValueDict&, CommandManager* = nullptr
    );

    /** Update the priority.<br>
      * The priority value is a key field. If multiple rules have the
      * same priority a data exception is thrown.
      */
    void setPriority(const int);

    /** Return the matrix owning this rule. */
    SetupMatrix* getSetupMatrix() const
    {
      return matrix;
    }

    /** Return the priority. */
    int getPriority() const
    {
      return priority;
    }

    /** Update the from setup. */
    void setFromSetup(const string& f)
    {
      from = f;
    }

    /** Return the from setup. */
    string getFromSetupString() const
    {
      return from;
    }

    PooledString getFromSetup() const
    {
      return from;
    }

    /** Update the to setup. */
    void setToSetup(const string& f)
    {
      to = f;
    }

    /** Return the to setup. */
    string getToSetupString() const
    {
      return to;
    }

    PooledString getToSetup() const
    {
      return to;
    }

    /** Update the conversion duration. */
    void setDuration(Duration p)
    {
      duration = p;
    }

    /** Return the conversion duration. */
    Duration getDuration() const
    {
      return duration;
    }

    /** Update the conversion cost. */
    void setCost(double p)
    {
      cost = p;
    }

    /** Return the conversion cost. */
    double getCost() const
    {
      return cost;
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::fromsetup, &Cls::getFromSetupString, &Cls::setFromSetup);
      m->addStringField<Cls>(Tags::tosetup, &Cls::getToSetupString, &Cls::setToSetup);
      m->addDurationField<Cls>(Tags::duration, &Cls::getDuration, &Cls::setDuration);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
      m->addPointerField<Cls, SetupMatrix>(Tags::setupmatrix, &Cls::getSetupMatrix, &Cls::setSetupMatrix, DONT_SERIALIZE + PARENT);
    }

  private:
    /** Pointer to the owning matrix. */
    SetupMatrix *matrix = nullptr;

    /** Pointer to the next rule in this matrix. */
    SetupMatrixRule *nextRule = nullptr;

    /** Pointer to the previous rule in this matrix. */
    SetupMatrixRule *prevRule = nullptr;

    /** Original setup. */
    PooledString from;

    /** New setup. */
    PooledString to;

    /** Changeover time. */
    Duration duration;

    /** Changeover cost. */
    double cost = 0.0;

    /** Priority of the rule.<br>
      * This field is the key field, i.e. within a setup matrix all rules
      * need to have different priorities.
      */
    int priority = 0;

    void updateSort();

  public:
    /** @brief An iterator class to go through all rules of a setup matrix. */
    class iterator
    {
      private:
        SetupMatrixRule* curRule;

      public:
        /** Constructor. */
        iterator(SetupMatrixRule* c = nullptr) : curRule(c) {}

        bool operator != (const iterator &b) const
        {
          return b.curRule != curRule;
        }

        bool operator == (const iterator &b) const
        {
          return b.curRule == curRule;
        }

        iterator& operator++()
        {
          if (curRule)
            curRule = curRule->nextRule;
          return *this;
        }

        iterator operator++(int)
        {
          iterator tmp = *this;
          ++*this;
          return tmp;
        }

        SetupMatrixRule* next()
        {
          SetupMatrixRule *tmp = curRule;
          if (curRule)
            curRule = curRule->nextRule;
          return tmp;
        }

        iterator& operator--()
        {
          if(curRule) curRule = curRule->prevRule;
          return *this;
        }

        iterator operator--(int)
        {
          iterator tmp = *this;
          --*this;
          return tmp;
        }

        SetupMatrixRule* operator ->() const
        {
          return curRule;
        }

        SetupMatrixRule& operator *() const
        {
          return *curRule;
        }

        static iterator end()
        {
          return nullptr;
        }
    };
};


/** @brief This class is the default implementation of the abstract
  * SetupMatrixRule class.
  */
class SetupMatrixRuleDefault : public SetupMatrixRule
{
public:
  /** Default constructor. */
  explicit SetupMatrixRuleDefault()
  {
    initType(metadata);
  }

  /** Constructor. */
  SetupMatrixRuleDefault(SetupMatrix* m, PooledString f, PooledString t, Duration d, double c, int p)
    : SetupMatrixRule(m, f, t, d, c, p)
  {
    initType(metadata);
  }


  virtual const MetaClass& getType() const { return *metadata; }
  static const MetaClass* metadata;
  static int initialize();
};


/** @brief This class is used to represent a matrix defining the changeover
  * times between setups.
  */
class SetupMatrix : public HasName<SetupMatrix>, public HasSource
{
  friend class SetupMatrixRule;
  public:
    class RuleIterator; // Forward declaration

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "", MANDATORY);
      HasSource::registerFields<Cls>(m);
      m->addIteratorField<Cls, SetupMatrixRule::iterator, SetupMatrixRule>(Tags::rules, Tags::rule, &Cls::getRules, BASE + WRITE_OBJECT);
    }

  public:
    /** Default constructor. */
    explicit SetupMatrix() 
      : ChangeOverNotAllowed(this, "NotAllowed", "NotAllowed", 365L * 86400L, DBL_MAX, INT_MAX) {}

    /** Destructor. */
    ~SetupMatrix();

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    /** Returns an iterator to go through the list of rules. */
    SetupMatrixRule::iterator getRules() const
    {
      return SetupMatrixRule::iterator(firstRule);
    }

    /** Computes the changeover time and cost between 2 setup values.
      *
      * To compute the time of a changeover the algorithm will evaluate all
      * rules in sequence (in order of priority).<br>
      * For a rule to match the changeover between the original setup X to
      * a new setup Y, two conditions need to be fulfilled:
      *  - The original setup X must match with the fromsetup of the rule.<br>
      *    If the fromsetup field is empty, it is considered a match.
      *  - The new setup Y must match with the tosetup of the rule.<br>
      *    If the tosetup field is empty, it is considered a match.
      * The wildcard characters * and ? can be used in the fromsetup and
      * tosetup fields.<br>
      * As soon as a matching rule is found, it is applied and subsequent
      * rules are not evaluated.<br>
      * If no matching rule is found, the changeover is not allowed: a pointer 
      * to a dummy changeover with a very high cost and duration is returned.
      */
    SetupMatrixRule* calculateSetup(PooledString, PooledString, Resource*) const;

  private:
    /** Head of the list of rules. */
    SetupMatrixRule *firstRule = nullptr;

    /** A dummy rule to mark disallowed changeovers. */
    const SetupMatrixRuleDefault ChangeOverNotAllowed;
};


/** @brief This class is the default implementation of the abstract
  * SetupMatrix class.
  */
class SetupMatrixDefault : public SetupMatrix
{
  public:
    explicit SetupMatrixDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This class models skills that can be assigned to resources. */
class Skill : public HasName<Skill>, public HasSource
{
  friend class ResourceSkill;

  public:
    /** Default constructor. */
    explicit Skill()
    {
      initType(metadata);
    }

    /** Destructor. */
    ~Skill();

    typedef Association<Resource,Skill,ResourceSkill>::ListB resourcelist;

    /** Returns an iterator over the list of resources having this skill. */
    resourcelist::const_iterator getResources() const
    {
      return resources.begin();
    }

    /** Python interface to add a new resource. */
    static PyObject* addPythonResource(PyObject*, PyObject*);

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "", MANDATORY);
      m->addIteratorField<Cls, resourcelist::const_iterator, ResourceSkill>(Tags::resourceskills, Tags::resourceskill, &Cls::getResources);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasSource::registerFields<Cls>(m);
    }
  private:
    /** This is a list of resources having this skill. */
    resourcelist resources;
};


/** @brief this class is the default implementation of the abstract
  * Skill class.
  */
class SkillDefault : public Skill
{
  public:
    explicit SkillDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This class represents a workcentre, a physical or logical
  * representation of capacity.
  */
class Resource : public HasHierarchy<Resource>,
  public HasLevel, public Plannable, public HasDescription
{
    friend class Load;
    friend class LoadPlan;
    friend class ResourceSkill;

  public:
    // Forward declaration of inner classes
    class PlanIterator;
    class OperationPlanIterator;

    /** The default time window before the ask date where we look for
      * available capacity. */
    static Duration defaultMaxEarly;

    /** Default constructor. */
    explicit Resource()
    {
      setMaximum(1);
    }

    /** Destructor. */
    virtual ~Resource();

    /** Updates the size of a resource, when it is time-dependent. */
    virtual void setMaximumCalendar(Calendar*);

    /** Updates the size of a resource. */
    void setMaximum(double);

    /** Return a pointer to the maximum capacity profile. */
    Calendar* getMaximumCalendar() const
    {
      return size_max_cal;
    }

    /** Return a pointer to the maximum capacity. */
    double getMaximum() const
    {
      return size_max;
    }

    /** Returns the availability calendar of the resource. */
    Calendar *getAvailable() const
    {
      return available;
    }

    /** Updates the availability calendar of the resource. */
    void setAvailable(Calendar* b)
    {
      available = b;
    }

    double getEfficiency() const
    {
      return efficiency;
    }

    void setEfficiency(const double c)
    {
      if (c > 0)
        efficiency = c;
      else
        throw DataException("Resource efficiency must be positive");
    }

    Calendar* getEfficiencyCalendar() const
    {
      return efficiency_calendar;
    }

    void setEfficiencyCalendar(Calendar* c)
    {
      efficiency_calendar = c;
    }

    /** Returns the cost of using 1 unit of this resource for 1 hour.<br>
      * The default value is 0.0.
      */
    double getCost() const
    {
      return cost;
    }

    /** Update the cost of using 1 unit of this resource for 1 hour. */
    void setCost(const double c)
    {
      if (c >= 0)
        cost = c;
      else
        throw DataException("Resource cost must be positive");
    }

    typedef Association<Operation,Resource,Load>::ListB loadlist;
    typedef Association<Resource,Skill,ResourceSkill>::ListA skilllist;
    typedef TimeLine<LoadPlan> loadplanlist;

    /** Returns a reference to the list of loadplans. */
    const loadplanlist& getLoadPlans() const
    {
      return loadplans;
    }

    /** Returns a reference to the list of loadplans. */
    loadplanlist::const_iterator getLoadPlanIterator() const
    {
      return loadplans.begin();
    }

    /** Returns a reference to the list of loadplans. */
    loadplanlist& getLoadPlans()
    {
      return loadplans;
    }

    inline OperationPlanIterator getOperationPlans() const;

    /** Returns a constant reference to the list of loads. It defines
      * which operations are using the resource.
      * TODO Get rid of this
      */
    const loadlist& getLoads() const
    {
      return loads;
    }

    /** Debugging function. */
    void inspect(string msg = "") const;
    
    static PyObject* inspectPython(PyObject*, PyObject*);

    /** Returns a constant reference to the list of loads. It defines
      * which operations are using the resource.
      */
    loadlist::const_iterator getLoadIterator() const
    {
      return loads.begin();
    }

    /** Returns a constant reference to the list of skills. */
    skilllist::const_iterator getSkills() const
    {
      return skills.begin();
    }

    /** Returns true when an resource has a certain skill between the specified dates. */
    bool hasSkill(Skill*, Date = Date::infinitePast, Date = Date::infinitePast, ResourceSkill** = nullptr) const;

    /** Return the load that is associates a given operation with this
      * resource. Returns nullptr is no such load exists. */
    Load* findLoad(const Operation* o, Date d) const
    {
      return loads.find(o,d);
    }

    /** Initialize the class. */
    static int initialize();

    /** Returns the location of this resource. */
    Location* getLocation() const
    {
      return loc;
    }

    /** Updates the location of this resource. */
    void setLocation(Location* i)
    {
      loc = i;
    }

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    /** Deletes all operationplans loading this resource. The boolean parameter
      * controls whether we delete also locked operationplans or not.
      */
    void deleteOperationPlans(bool = false);

    /** Recompute the problems of this resource. */
    virtual void updateProblems();

    /** Update the setup time of all operationplans on the resource. */
    void updateSetupTime() const;

    void setHidden(bool b)
    {
      if (hidden!=b)
        setChanged();
      hidden = b;
    }

    bool getHidden() const
    {
      return hidden;
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    /** Returns the maximum inventory buildup allowed in case of capacity
      * shortages. */
    Duration getMaxEarly() const
    {
      return maxearly;
    }

    /** Updates the maximum inventory buildup allowed in case of capacity
      * shortages. */
    void setMaxEarly(Duration c)
    {
      if (c >= 0L)
        maxearly = c;
      else
        throw DataException("MaxEarly must be positive");
    }

    /** Return a pointer to the setup matrix. */
    SetupMatrix* getSetupMatrix() const
    {
      return setupmatrix;
    }

    /** Update the reference to the setup matrix. */
    void setSetupMatrix(SetupMatrix *s);

    /** Return the current setup. */
    PooledString getSetup() const
    {
      return setup ? setup->getSetup() : PooledString();
    }

    /** Return the current setup. */
    string getSetupString() const
    {
      return setup ? setup->getSetup() : "";
    }

    /** Update the current setup. */
    void setSetup(const string& s)
    {
      if (setup)
        // Updated existing event
        setup->setSetup(s);
      else
      {
        setup = new SetupEvent(getLoadPlans(), Date::infinitePast, s);
        getLoadPlans().insert(setup);
      }
    }

    /** Return the setup of the resource on a specific date. 
      * To avoid any ambiguity about the current setup of a resource
      * the calculation is based only on the latest *setup end* event
      * before (or at, when the parameter is true) the argument date.
      * @see LoadPlan::getSetupBefore
      */
    SetupEvent* getSetupAt(Date, OperationPlan* = nullptr);

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMaximum, &Cls::setMaximum, 1);
      m->addPointerField<Cls, Calendar>(Tags::maximum_calendar, &Cls::getMaximumCalendar, &Cls::setMaximumCalendar);
      m->addDurationField<Cls>(Tags::maxearly, &Cls::getMaxEarly, &Cls::setMaxEarly, defaultMaxEarly);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addDoubleField<Cls>(Tags::efficiency, &Cls::getEfficiency, &Cls::setEfficiency, 100.0);
      m->addPointerField<Cls, Calendar>(Tags::efficiency_calendar, &Cls::getEfficiencyCalendar, &Cls::setEfficiencyCalendar);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addStringField<Cls>(Tags::setup, &Cls::getSetupString, &Cls::setSetup);
      m->addPointerField<Cls, SetupMatrix>(Tags::setupmatrix, &Cls::getSetupMatrix, &Cls::setSetupMatrix);
      m->addPointerField<Cls, Calendar>(Tags::available, &Cls::getAvailable, &Cls::setAvailable);
      Plannable::registerFields<Cls>(m);
      m->addIteratorField<Cls, loadlist::const_iterator, Load>(Tags::loads, Tags::load, &Cls::getLoadIterator, DETAIL);
      m->addIteratorField<Cls, skilllist::const_iterator, ResourceSkill>(Tags::resourceskills, Tags::resourceskill, &Cls::getSkills, DETAIL + WRITE_OBJECT);
      m->addIteratorField<Cls, loadplanlist::const_iterator, LoadPlan>(Tags::loadplans, Tags::loadplan, &Cls::getLoadPlanIterator, DONT_SERIALIZE);
      m->addIteratorField<Cls, OperationPlanIterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans, PLAN + WRITE_OBJECT + WRITE_HIDDEN);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasLevel::registerFields<Cls>(m);
    }

  protected:
    /** This calendar is used to updates to the resource size. */
    Calendar* size_max_cal = nullptr;

    /** Stores the collection of all loadplans of this resource. */
    loadplanlist loadplans;

  private:
    /** The maximum resource size.<br>
      * If a calendar is specified, this field is ignored.
      */
    double size_max = 0.0;

    /** This is a list of all load models that are linking this resource with
      * operations. */
    loadlist loads;

    /** This is a list of skills this resource has. */
    skilllist skills;

    /** A pointer to the location of the resource. */
    Location* loc = nullptr;

    /** The cost of using 1 unit of this resource for 1 hour. */
    double cost = 0.0;

    /** The efficiency percentage of this resource. */
    double efficiency = 100.0;

    /** Time phased efficiency percentage. */
    Calendar* efficiency_calendar = nullptr;

    /** Maximum inventory buildup allowed in case of capacity shortages. */
    Duration maxearly = defaultMaxEarly;

    /** Reference to the setup matrix. */
    SetupMatrix *setupmatrix = nullptr;

    /** Current setup. */
    SetupEvent* setup = nullptr;

    /** Availability calendar of the buffer. */
    Calendar* available = nullptr;

    /** Specifies whether this resource is hidden for serialization. */
    bool hidden = false;

    /** Python method that returns an iterator over the resource plan. */
    static PyObject* plan(PyObject*, PyObject*);
};


/** @brief This class provides an efficient way to iterate over
  * the plan of a resource aggregated in time buckets.<br>
  * For resources of type default, a list of dates needs to be passed as
  * argument to define the time buckets.<br>
  * For resources of type buckets, the time buckets are defined on the
  * resource and the argument is ignored.
  */
class Resource::PlanIterator : public PythonExtension<Resource::PlanIterator>
{
  public:
    static int initialize();

    /** Constructor.
      * The first argument is the resource whose plan we're looking at.
      * The second argument is a Python iterator over a list of dates. These
      * dates define the buckets at which we aggregate the resource plan.
      */
    PlanIterator(Resource*, PyObject*);

    /** Destructor. */
    ~PlanIterator();

  private:

    /** Structure for iterating over a resource. */
    struct _res 
    {
      Resource* res;
      Resource::loadplanlist::iterator ldplaniter;
      Calendar::EventIterator unavailIter;
      Calendar::EventIterator unavailLocIter;
      const LoadPlan* setup_loadplan;
      Date cur_date;
      Date prev_date;
      double cur_size;
      double cur_load;
      bool prev_value;
      bool bucketized;
    };

    vector<_res> res_list;

    /** A Python object pointing to a list of start dates of buckets. */
    PyObject* bucketiterator;

    /** Python function to iterate over the periods. */
    PyObject* iternext();

    double bucket_available;
    double bucket_load;
    double bucket_setup;
    double bucket_unavailable;

    void update(_res*, Date till);

    /** Python object pointing to the start date of the plan bucket. */
    PyObject* start_date = nullptr;

    /** Python object pointing to the start date of the plan bucket. */
    PyObject* end_date = nullptr;
};


/** @brief This class is the default implementation of the abstract
  * Resource class.
  */
class ResourceDefault : public Resource
{
  public:
    explicit ResourceDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This class represents a resource that'll never have any
  * capacity shortage. */
class ResourceInfinite : public Resource
{
  public:
    explicit ResourceInfinite()
    {
      setDetectProblems(false);
      initType(metadata);
    }

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}
    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();
};


/** @brief This class represents a resource whose capacity is defined per
    time bucket. */
class ResourceBuckets : public Resource
{
  public:
    /** Default constructor. */
    explicit ResourceBuckets()
    {
      initType(metadata);
    }

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}
    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();

    virtual void updateProblems();

    /** Updates the time buckets and the quantity per time bucket. */
    virtual void setMaximumCalendar(Calendar*);
};


/** @brief This class associates a resource with its skills. */
class ResourceSkill : public Object,
  public Association<Resource,Skill,ResourceSkill>::Node, public HasSource
{
  public:
    /** Default constructor. */
    explicit ResourceSkill()
    {
      initType(metadata);
    }

    /** Constructor. */
    explicit ResourceSkill(Skill*, Resource*, int);

    /** Constructor. */
    explicit ResourceSkill(Skill*, Resource*, int, DateRange);

    /** Destructor. */
    ~ResourceSkill();

    /** Initialize the class. */
    static int initialize();

    /** Search an existing object. */
    static Object* finder(const DataValueDict&);

    /** Returns the resource. */
    Resource* getResource() const
    {
      return getPtrA();
    }

    /** Updates the resource. This method can only be called on an instance. */
    void setResource(Resource* r)
    {
      if (r) setPtrA(r, r->skills);
    }

    /** Returns the skill. */
    Skill* getSkill() const
    {
      return getPtrB();
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    /** Updates the skill. This method can only be called on an instance. */
    void setSkill(Skill* s)
    {
      if (s) setPtrB(s, s->resources);
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource, &Cls::setResource, MANDATORY + PARENT);
      m->addPointerField<Cls, Skill>(Tags::skill, &Cls::getSkill, &Cls::setSkill, MANDATORY + PARENT);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      HasSource::registerFields<Cls>(m);
    }

  private:
    /** Factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
};


/** @brief This class implements the abstract ResourceSkill class. */
class ResourceSkillDefault : public ResourceSkill
{
  public:
    /** This constructor is called from the plan begin_element function. */
    explicit ResourceSkillDefault() {}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
};


/** @brief This class links a resource to a certain operation. */
class Load
  : public Object, public Association<Operation,Resource,Load>::Node,
  public Solvable, public HasSource
{
    friend class Resource;
    friend class Operation;

  public:
    /** Constructor. */
    explicit Load(Operation* o, Resource* r, double u)
    {
      setOperation(o);
      setResource(r);
      setQuantity(u);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Constructor. */
    explicit Load(Operation* o, Resource* r, double u, DateRange e)
    {
      setOperation(o);
      setResource(r);
      setQuantity(u);
      setEffective(e);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Destructor. */
    ~Load();

    /** Search an existing object. */
    static Object* finder(const DataValueDict& k);

    /** Returns the operation consuming the resource capacity. */
    Operation* getOperation() const
    {
      return getPtrA();
    }

    /** Updates the operation being loaded. This method can only be called
      * once for a load. */
    void setOperation(Operation*);

    /** Returns the capacity resource being consumed. */
    Resource* getResource() const
    {
      return getPtrB();
    }

    /** Updates the capacity being consumed. This method can only be called
      * once on a resource. */
    virtual void setResource(Resource* r)
    {
      if (r) setPtrB(r,r->getLoads());
    }

    /** Returns how much capacity is consumed during the duration of the
      * operationplan. */
    double getQuantity() const
    {
      return qty;
    }

    /** Updates the quantity of the load.
      * @exception DataException When a negative number is passed.
      */
    void setQuantity(double f)
    {
      if (f < 0) throw DataException("Load quantity can't be negative");
      qty = f;
    }

    /** Return the leading load of this group.
      * When the load has no alternate or if the flow is itself leading
      * then nullptr is returned.
      */
    Load* getAlternate() const
    {
      if (getName().empty() || !getOperation())
        return nullptr;
      for (Operation::loadlist::const_iterator h=getOperation()->getLoads().begin();
        h!=getOperation()->getLoads().end() && this != &*h; ++h)
        if (getName() == h->getName())
          return const_cast<Load*>(&*h);
      return nullptr;
    }

    /** Return whether the load has alternates. */
    bool hasAlternates() const
    {
      if (getName().empty() || !getOperation())
        return false;
      for (Operation::loadlist::const_iterator h=getOperation()->getLoads().begin();
        h!=getOperation()->getLoads().end(); ++h)
        if (getName() == h->getName() && this != &*h)
          return true;
      return false;
    }

    /** Return the required resource setup. */
    PooledString getSetup() const
    {
      return setup;
    }

    /** Update the required resource setup. */
    void setSetupString(const string&);

    /** Return the required resource setup. */
    string getSetupString() const
    {
      return setup;
    }

    /** Update the required skill. */
    void setSkill(Skill* s)
    {
      skill = s;
    }

    /** Return the required skill. */
    Skill* getSkill() const
    {
      return skill;
    }

    /** Find the preferred resource in a resource pool to assign a load to. 
      * This method is only useful when the loadplan is not created yet.
      */
    Resource* findPreferredResource(Date d) const;

    /** This method holds the logic the compute the date of a loadplan. */
    virtual Date getLoadplanDate(const LoadPlan*) const;

    /** This method holds the logic the compute the quantity of a loadplan. */
    virtual double getLoadplanQuantity(const LoadPlan*) const;

    /** This method allows computing the operationplan start or end date 
      * when given the date of the loadplan.
      */
    virtual Date getOperationPlanDate(const LoadPlan*, Date, bool=true) const;

    static int initialize();

    bool getHidden() const
    {
      return (getResource() && getResource()->getHidden())
          || (getOperation() && getOperation()->getHidden());
    }
    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    /** Default constructor. */
    Load()
    {
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Return the search mode. */
    SearchMode getSearch() const
    {
      return search;
    }

    /** Update the search mode. */
    void setSearch(const string a)
    {
      search = decodeSearchMode(a);
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation, MANDATORY + PARENT);
      m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource, &Cls::setResource, MANDATORY + PARENT);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity, 1.0);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName);
      m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch, &Cls::setSearch, PRIORITY);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      m->addStringField<Cls>(Tags::setup, &Cls::getSetupString, &Cls::setSetupString);
      m->addPointerField<Cls, Skill>(Tags::skill, &Cls::getSkill, &Cls::setSkill);
      HasSource::registerFields<Cls>(m);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
    }

  private:
    /** Stores how much capacity is consumed during the duration of an
      * operationplan. */
    double qty = 1.0;

    /** Required setup. */
    PooledString setup;

    /** Required skill. */
    Skill* skill = nullptr;

    /** Mode to select the preferred alternates. */
    SearchMode search = PRIORITY;

  protected:
    /** Factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
};


/** @brief This class implements the abstract Load class. */
class LoadDefault : public Load
{
  public:
    /** Constructor. */
    explicit LoadDefault(Operation* o, Resource* r, double q) : Load(o, r, q) {}

    /** Constructor. */
    explicit LoadDefault(Operation* o, Resource* r, double q, DateRange e) : Load(o, r, q,e) {}

    /** This constructor is called from the plan begin_element function. */
    explicit LoadDefault() {}

    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
};


/** @brief This class a load that loads a bucketized resource at a percentage of the
  * operationplan duration.
  * An offset of 0 means loading the resource at the start of the operationplan.
  * An offset of 100 means loading the resource at the end of the operationplan.
  * The calculations consider the available periods of the operationplan, and
  * skip unavailable periods.
  */
class LoadBucketizedPercentage : public Load
{
  public:
    /** Constructor. */
    explicit LoadBucketizedPercentage(Operation* o, Resource* r, double q) : Load(o, r, q) {}

    /** Constructor. */
    explicit LoadBucketizedPercentage(Operation* o, Resource* r, double q, DateRange e) : Load(o, r, q, e) {}

    /** This constructor is called from the plan begin_element function. */
    explicit LoadBucketizedPercentage() {}

    void setResource(Resource* r)
    {
      if (r && r->getType() != *ResourceBuckets::metadata)
        throw DataException("LoadBucketizedPercentage can only be associated with ResourceBuckets");
      Load::setResource(r);
    }

    double getOffset() const
    {
      return offset;
    }

    void setOffset(double d)
    {
      if (d < 0 || d > 100)
        throw DataException("load offset must be between 0 and 100");
      offset = d;
    }

    Date getLoadplanDate(const LoadPlan*) const;

    Date getOperationPlanDate(const LoadPlan*, Date, bool = true) const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDoubleField<Cls>(Tags::offset, &Cls::getOffset, &Cls::setOffset);
    }

    virtual void solve(Solver &s, void* v = nullptr) const { s.solve(this, v); }

    static int initialize();

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaClass* metadata;

  private:
    double offset = 0;
};


/** @brief This class a load that loads a bucketized resource at a specified
  * offset from the start of the operationplan.
  * An offset of 0 means loading the resource at the start of the operationplan.
  * An offset of 1 day means loading the resource 1 day after the operationplan
  * start date. If the operationplan takes less than 1 day we load the resource
  * at the end date.
  * The offset is computed based on the available periods of the operationplan,
  * and skips unavailable periods.
  */
class LoadBucketizedFromStart : public Load
{
  public:
    /** Constructor. */
    explicit LoadBucketizedFromStart(Operation* o, Resource* r, double q) : Load(o, r, q) {}

    /** Constructor. */
    explicit LoadBucketizedFromStart(Operation* o, Resource* r, double q, DateRange e) : Load(o, r, q, e) {}

    /** This constructor is called from the plan begin_element function. */
    explicit LoadBucketizedFromStart() {}

    void setResource(Resource* r)
    {
      if (r && r->getType() != *ResourceBuckets::metadata)
        throw DataException("LoadBucketizedFromStart can only be associated with ResourceBuckets");
      Load::setResource(r);
    }

    Date getLoadplanDate(const LoadPlan*) const;

    Date getOperationPlanDate(const LoadPlan*, Date, bool = true) const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDurationField<Cls>(Tags::offset, &Cls::getOffset, &Cls::setOffset);
    }

    virtual void solve(Solver &s, void* v = nullptr) const { s.solve(this, v); }

    static int initialize();

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaClass* metadata;

    Duration getOffset() const
    {
      return offset;
    }

    void setOffset(Duration d)
    {
      if (d < Duration(0L))
        throw DataException("load offset must be positive");
      offset = d;
    }

  private:
    Duration offset;
};


/** @brief This class a load that loads a bucketized resource at a specified
  * offset from the end of the operationplan.
  * An offset of 0 means loading the resource at the end of the operationplan.
  * An offset of 1 day means loading the resource 1 day before the operationplan
  * end date. If the operationplan takes less than 1 day we load the resource
  * at the start date.
  * The offset is computed based on the available periods of the operationplan,
  * and skips unavailable periods.
  */
class LoadBucketizedFromEnd : public Load
{
  public:
    /** Constructor. */
    explicit LoadBucketizedFromEnd(Operation* o, Resource* r, double q) : Load(o, r, q) {}

    /** Constructor. */
    explicit LoadBucketizedFromEnd(Operation* o, Resource* r, double q, DateRange e) : Load(o, r, q, e) {}

    /** This constructor is called from the plan begin_element function. */
    explicit LoadBucketizedFromEnd() {}

    void setResource(Resource* r)
    {
      if (r && r->getType() != *ResourceBuckets::metadata)
        throw DataException("LoadBucketizedFromEnd can only be associated with ResourceBuckets");
      Load::setResource(r);
    }

    Date getLoadplanDate(const LoadPlan*) const;

    Date getOperationPlanDate(const LoadPlan*, Date, bool = true) const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDurationField<Cls>(Tags::offset, &Cls::getOffset, &Cls::setOffset);
    }

    virtual void solve(Solver &s, void* v = nullptr) const { s.solve(this, v); }

    static int initialize();

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaClass* metadata;

    Duration getOffset() const
    {
      return offset;
    }

    void setOffset(Duration d)
    {
      if (d < Duration(0L))
        throw DataException("load offset must be positive");
      offset = d;
    }

  private:
    Duration offset;
};


/** @brief Represents the (independent) demand in the system. It can represent a
  * customer order or a forecast.
  *
  * This is an abstract class.
  */
class Demand
  : public HasHierarchy<Demand>, public Plannable, public HasDescription
{
  friend class Item;
  public:
    enum status {
      QUOTE, INQUIRY, OPEN, CLOSED, CANCELED
    };

    typedef forward_list<OperationPlan*> OperationPlanList;

    class DeliveryIterator
    {
      private:
        OperationPlanList::const_iterator cur;
        OperationPlanList::const_iterator end;

      public:
        /** Constructor. */
        DeliveryIterator(const Demand* d)
          : cur(d->getDelivery().begin()), end(d->getDelivery().end()) {}

        /** Return current value and advance the iterator. */
        OperationPlan* next()
        {
          if (cur == end)
            return nullptr;
          OperationPlan* tmp = *cur;
          ++cur;
          return tmp;
        }
    };

    /** Default constructor. */
    explicit Demand() {}

    /** Destructor.
      * Deleting the demand will also delete all delivery operation
      * plans (including locked ones).
      */
    virtual ~Demand();

    /** Return the memory size. */
    virtual size_t getSize() const
    {
      size_t tmp = Object::getSize();
      // Add the memory for the list of deliveries: 2 pointers per delivery
      for (auto iter = deli.begin(); iter != deli.end(); ++iter)
        tmp += 2 * sizeof(OperationPlan*);
      return tmp;
    }

    /** Returns the quantity of the demand. */
    double getQuantity() const
    {
      return qty;
    }

    /** Updates the quantity of the demand. The quantity must be be greater
      * than or equal to 0. */
    virtual void setQuantity(double);

    /** Returns the priority of the demand.<br>
      * Lower numbers indicate a higher priority level.
      */
    int getPriority() const
    {
      return prio;
    }

    /** Updates the due date of the demand.<br>
      * Lower numbers indicate a higher priority level.
      */
    virtual void setPriority(int i)
    {
      prio=i;
      setChanged();
    }

    /** Returns the item/product being requested. */
    Item* getItem() const
    {
      return it;
    }

    /** Update the item being requested. */
    virtual void setItem(Item*);

    /** Returns the location where the demand is shipped from. */
    Location* getLocation() const
    {
      return loc;
    }

    /** Update the location where the demand is shipped from. */
    void setLocation(Location* l)
    {
      if (loc == l)
        return;
      if (oper && oper->getHidden())
      {
        oper = uninitializedDelivery;
        HasLevel::triggerLazyRecomputation();
      }
      loc = l;
      setChanged();
    }

    /** Update the location where the demand is shipped from. 
      * This method does not trigger level or problem recalculation.
      */
    void setLocationNoRecalc(Location* l)
    {
      loc = l;
      oper = uninitializedDelivery;
    }

    /** This fields points to an operation that is to be used to plan the
      * demand. By default, the field is left to nullptr and the demand will then
      * be planned using the delivery operation of its item.
      * @see Item::getDelivery()
      */
    Operation* getOperation() const
    {
      if (oper == uninitializedDelivery)
        return nullptr;
      else
        return oper;
    }

    /** Updates the operation being used to plan the demand. */
    virtual void setOperation(Operation* o)
    {
      if (oper == o)
        return;
      oper=o;
      setChanged();
    }

    /** This function returns the operation that is to be used to satisfy this
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

    /** Returns the cluster which this demand belongs to. */
    int getCluster() const
    {
      Operation* o = getDeliveryOperation();
      return o ? o->getCluster() : 0;
    }

    /** Returns the delivery operationplan list. */
    const OperationPlanList& getDelivery() const;

    DeliveryIterator getOperationPlans() const
    {
      return DeliveryIterator(this);
    }

    /** Return the status. */
    status getStatus() const
    {
      return state;
    }

    /** Update the status. */
    void setStatus(status s)
    {
      state = s;
      setChanged();
    }

    /** Return the status as a string. */
    string getStatusString() const
    {
      switch (state)
      {
        case QUOTE: return "quote";
        case INQUIRY: return "inquiry";
        case OPEN: return "open";
        case CLOSED: return "closed";
        case CANCELED: return "canceled";
        default: throw LogicException("Demand status not recognized");
      }
    }

    /** Update the demand status from a string. */
    void setStatusString(const string& s)
    {
      if (s == "open" || s.empty())
        state = OPEN;
      else if (s == "closed")
        state = CLOSED;
      else if (s == "quote")
        state = QUOTE;
      else if (s == "inquiry")
        state = INQUIRY;
      else if (s == "canceled")
        state = CANCELED;
      else
        throw DataException("Demand status not recognized");
    }

    /** Return a pointer to the next demand for the same item. */
    Demand* getNextItemDemand() const
    {
      return nextItemDemand;
    }

    /** Returns the latest delivery operationplan. */
    OperationPlan* getLatestDelivery() const;

    /** Returns the earliest delivery operationplan. */
    OperationPlan* getEarliestDelivery() const;

    /** Adds a delivery operationplan for this demand. */
    void addDelivery(OperationPlan *o);

    /** Removes a delivery operationplan for this demand. */
    void removeDelivery(OperationPlan *o);

    /** Deletes all delivery operationplans of this demand.<br>
      * The (optional) boolean parameter controls whether we delete also locked
      * operationplans or not.<br>
      * The second (optional) argument is a command list that can be used to
      * remove the operationplans in an undo-able way.
      */
    void deleteOperationPlans
    (bool deleteLockedOpplans = false, CommandManager* = nullptr);

    /** Python method for adding a constraint. */
    static PyObject* addConstraint(PyObject*, PyObject*, PyObject*);

    /** Returns the due date of the demand. */
    Date getDue() const
    {
      return dueDate;
    }

    /** Updates the due date of the demand. */
    virtual void setDue(Date d)
    {
      dueDate = d;
      setChanged();
    }

    /** Returns the customer. */
    Customer* getCustomer() const
    {
      return cust;
    }

    /** Updates the customer. */
    virtual void setCustomer(Customer* c)
    {
      cust = c;
      setChanged();
    }

    /** Return a reference to the constraint list. */
    const Problem::List& getConstraints() const
    {
      return constraints;
    }

    /** Return a reference to the constraint list. */
    Problem::List& getConstraints()
    {
      return constraints;
    }

    /** Return an iterator over the constraints encountered when planning
      * this demand. */
    Problem::List::iterator getConstraintIterator() const;

    /** Returns the total amount that has been planned. */
    double getPlannedQuantity() const;

    /** Return an iterator over the problems of this demand. */
    Problem::List::iterator getProblemIterator() const;

    static int initialize();

    virtual void solve(Solver &s, void* v = nullptr) const 
    {
      s.solve(this,v);
    }

    /** Return the maximum delay allowed in satisfying this demand.<br>
      * The default value is infinite.
      */
    Duration getMaxLateness() const
    {
      return maxLateness;
    }

    /** Updates the maximum allowed lateness for this demand.<br>
      * The default value is infinite.<br>
      * The argument must be a positive time period.
      */
    virtual void setMaxLateness(Duration m)
    {
      if (m < 0L)
        throw DataException("The maximum demand lateness must be positive");
      maxLateness = m;
    }

    /** Return the minimum shipment quantity allowed in satisfying this
      * demand.<br>
      * The default value is -1.0. In this case we apply a minimum shipment
      * such that we have at most "DefaultMaxShipments" partial deliveries.
      */
    double getMinShipment() const
    {
      if (minShipment >= 0.0)
        // Explicitly set value of the field
        return minShipment;
      else
        // Automatically suggest a value
        return ceil(getQuantity() / DefaultMaxShipments);
    }

    bool isMinShipmentDefault() const
    {
      return minShipment == -1.0;
    }

    /** Updates the maximum allowed lateness for this demand.<br>
      * The default value is infinite.<br>
      * The argument must be a positive time period.
      */
    virtual void setMinShipment(double m)
    {
      if (m < 0.0 && m != -1.0)
        throw DataException("The minimum demand shipment quantity must be positive");
      minShipment = m;
    }

    /** Recompute the problems. */
    virtual void updateProblems();

    /** Specifies whether of not this demand is to be hidden from
      * serialization. The default value is false. */
    void setHidden(bool b)
    {
      hidden = b;
    }

    /** Returns true if this demand is to be hidden from serialization. */
    bool getHidden() const
    {
      return hidden;
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    PeggingIterator getPegging() const;

    /** Return the latest delivery date for the demand. */
    Date getDeliveryDate() const
    {
      OperationPlan* op = getLatestDelivery();
      return op ? op->getEnd() : Date::infiniteFuture;
    }

    /** Return the delay of the latest delivery compared to the due date. */
    Duration getDelay() const
    {
      OperationPlan* op = getLatestDelivery();
      return (op ? op->getEnd() : Date::infiniteFuture) - getDue();
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, BASE + WRITE_OBJECT_SVC);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addPointerField<Cls, Customer>(Tags::customer, &Cls::getCustomer, &Cls::setCustomer);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation);
      Plannable::registerFields<Cls>(m);
      m->addDateField<Cls>(Tags::due, &Cls::getDue, &Cls::setDue);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
      m->addDurationField<Cls>(Tags::maxlateness, &Cls::getMaxLateness, &Cls::setMaxLateness, Duration::MAX, BASE + PLAN);
      m->addStringField<Cls>(Tags::status, &Cls::getStatusString, &Cls::setStatusString, "open");
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addIteratorField<Cls, PeggingIterator, PeggingIterator>(Tags::pegging, Tags::pegging, &Cls::getPegging, PLAN + WRITE_OBJECT);
      m->addIteratorField<Cls, DeliveryIterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans, DETAIL + WRITE_OBJECT + WRITE_HIDDEN);
      m->addIteratorField<Cls, Problem::List::iterator, Problem>(Tags::constraints, Tags::problem, &Cls::getConstraintIterator, DETAIL);
      m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, nullptr, 0, DONT_SERIALIZE);
      m->addPointerField<Cls, Operation>(Tags::delivery_operation, &Cls::getDeliveryOperation, nullptr, DONT_SERIALIZE);
      m->addDurationField<Cls>(Tags::delay, &Cls::getDelay, nullptr, -999L, PLAN);
      m->addDateField<Cls>(Tags::delivery, &Cls::getDeliveryDate, nullptr, Date::infiniteFuture, PLAN);
      m->addDoubleField<Cls>(Tags::planned_quantity, &Cls::getPlannedQuantity, nullptr, -1.0, PLAN);
    }

  private:
    static OperationFixedTime *uninitializedDelivery;

    /** Maximum number of partial shipments we use by default.
      * Unless the user specified a value for the minshipments field, we use
      * this default to compute a minshipment value.
      */
    static const int DefaultMaxShipments = 10;

    /** Requested item. */
    Item *it = nullptr;

    /** Location. */
    Location *loc = nullptr;

    /** Delivery Operation. Can be left nullptr, in which case the delivery
      * operation can be specified on the requested item. */
    Operation *oper = uninitializedDelivery;

    /** Customer creating this demand. */
    Customer *cust = nullptr;

    /** Requested quantity. Only positive numbers are allowed. */
    double qty = 0.0;

    /** Due date. */
    Date dueDate;

    /** Maximum lateness allowed when planning this demand.<br>
      * The default value is Duration::MAX.
      */
    Duration maxLateness = Duration::MAX;

    /** Minimum size for a delivery operation plan satisfying this demand. */
    double minShipment = -1.0;

    /** A list of operation plans to deliver this demand. 
      * The list is sorted by the end date of the deliveries. The sorting is
      * done lazily in the getDelivery() method.
      */
    OperationPlanList deli;

    /** A list of constraints preventing this demand from being planned in
      * full and on time. */
    Problem::List constraints;

    /** A linked list with all demands of an item. */
    Demand* nextItemDemand = nullptr;

    /** Status of the demand. */
    status state = OPEN;

    /** Priority. Lower numbers indicate a higher priority level.*/
    int prio = 0;

    /** Hide this demand or not. */
    bool hidden = false;
};


class Item::demandIterator
{
  private:
    Demand* cur;

  public:
    /** Constructor. */
    demandIterator(const Item* i) : cur(i ? i->firstItemDemand : nullptr) {}

    bool operator != (const demandIterator &b) const
    {
      return b.cur != cur;
    }

    bool operator == (const demandIterator &b) const
    {
      return b.cur == cur;
    }

    demandIterator& operator++()
    {
      if (cur)
        cur = cur->getNextItemDemand();
      return *this;
    }

    demandIterator operator++(int)
    {
      demandIterator tmp = *this;
      ++*this;
      return tmp;
    }

    Demand* next()
    {
      Demand *tmp = cur;
      if (cur)
        cur = cur->getNextItemDemand();
      return tmp;
    }

    Demand* operator ->() const
    {
      return cur;
    }

    Demand& operator *() const
    {
      return *cur;
    }
};


inline Item::demandIterator Item::getDemandIterator() const
{
  return this;
}


/** @brief This class is the default implementation of the abstract
  * Demand class. */
class DemandDefault : public Demand
{
  public:
    explicit DemandDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static int initialize();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDoubleField<Cls>(Tags::minshipment, &Cls::getMinShipment, &Cls::setMinShipment, -1, BASE + PLAN, &Cls::isMinShipmentDefault);
    }
};


/** @brief This class represents the resource capacity of an operationplan.
  *
  * For both the start and the end date of the operationplan, a loadplan
  * object is created. These are then inserted in the timeline structure
  * associated with a resource.
  */
class LoadPlan : public TimeLine<LoadPlan>::EventChangeOnhand
{
    friend class OperationPlan::LoadPlanIterator;
  public:
    // Forward declarations
    class AlternateIterator;

    /** Public constructor.<br>
      * This constructor constructs the starting loadplan and will
      * also call a private constructor to creates the ending loadplan.
      * In other words, a single call to the constructor will create
      * two loadplan objects.
      */
    explicit LoadPlan(OperationPlan*, const Load*);

    /** Return the operationplan owning this loadplan. */
    virtual OperationPlan* getOperationPlan() const
    {
      return oper;
    }

    /** Return the operation. */
    Operation* getOperation() const
    {
      return oper->getOperation();
    }

    /** Return the start date of the operationplan. */
    Date getStartDate() const
    {
      return oper->getStart();
    }

    /** Return the start date of the operationplan. */
    Date getEndDate() const
    {
      return oper->getEnd();
    }

    /** Return the load of which this is a plan instance. */
    Load* getLoad() const
    {
      return ld;
    }

    /** Update the resource.<br>
      * The optional second argument specifies whether or not we need to verify
      * if the assigned resource is valid. A valid resource must a) be a
      * subresource of the resource specified on the load, and b) must also
      * have the skill specified on the resource.
      */
    void setResource(Resource* res)
    {
      setResource(res, true);
    }

    /** Update the resource.<br>
      * The optional second argument specifies whether or not we need to verify
      * if the assigned resource is valid. A valid resource must a) be a
      * subresource of the resource specified on the load, and b) must also
      * have the skill specified on the resource.
      */
    void setResource(Resource* res, bool check, bool use_start = true);

    /** Return the resource. */
    Resource* getResource() const
    {
      return res;
    }

    /** Update the load of an already existing flowplan.<br>
      * The new load must belong to the same operation.
      */
    void setLoad(Load*);

    /** Return true when this loadplan marks the start of an operationplan. */
    bool isStart() const
    {
      return start_or_end == START;
    }

    /** Return the status of the operationplanresource.
      * The status string is one of the following:
      *   - proposed
      *   - confirmed
      */
    string getStatus() const;

    /** Update the status of the operationplanresource. */
    void setStatus(const string&);

    /** Destructor. */
    virtual ~LoadPlan();

    /** This function needs to be called whenever the loadplan date or
      * quantity are changed.
      */
    void update();

    /** Return a pointer to the timeline data structure owning this loadplan. */
    TimeLine<LoadPlan>* getTimeLine() const
    {
      return &(res->loadplans);
    }

    /** Returns the current setup of the resource. */
    string getSetup() const
    {
      auto tmp = getSetup(true);
      return tmp ? tmp->getSetup() : "";
    }

    /** Returns the required setup for the operation. */
    string getSetupLoad() const
    {
      return getLoad() ? getLoad()->getSetup() : "";
    }

    /** Returns the current setup of the resource.<br>
      * When the argument is true the setup of this loadplan is returned.
      * When the argument is false the setup just before the loadplan is returned.
      */
    SetupEvent* getSetup(bool) const;

    /** Returns true when the loadplan is hidden.<br>
      * This is determined by looking at whether the load is hidden or not.
      */
    bool getHidden() const
    {
      return getQuantity() < 0 || ld->getHidden();
    }

    /** Override the setQuantity of the TimeLine class, this is needed for the
      * registerFields function.
      */
    void setQuantity(double quantity)
    {
      qty = quantity;
    }

    void setOperationPlan(OperationPlan* o)
    {
      if (oper && oper != o)
        throw DataException("Can't change the operationplan of a loadplan");
      else
        oper = o;
    }

    /** Each operationplan has 2 loadplans per load: one at the start,
      * when the capacity consumption starts, and one at the end, when the
      * capacity consumption ends.<br>
      * This method returns the "companion" loadplan. It is not very
      * scalable: the performance is linear with the number of loadplans
      * on the resource.
      */
    LoadPlan* getOtherLoadPlan() const;

    inline AlternateIterator getAlternates() const;

    static int initialize();
    static const MetaCategory* metadata;
    virtual const MetaClass& getType() const { return *metadata; }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addIteratorField<Cls, AlternateIterator, Resource>(
        Tags::alternates, Tags::alternate,
        "AlternateResourceIterator", "Iterator over loadplan alternates",
        &Cls::getAlternates, PLAN + FORCE_BASE
        );
      m->addDateField<Cls>(Tags::date, &Cls::getDate);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity);
      m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnhand);
      m->addDoubleField<Cls>(Tags::minimum, &Cls::getMin);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMax);
      m->addStringField<Cls>(Tags::status, &Cls::getStatus, &Cls::setStatus, "proposed");
      m->addPointerField<Cls, OperationPlan>(Tags::operationplan, &Cls::getOperationPlan, &Cls::setOperationPlan, BASE + PARENT);
      m->addPointerField<Cls, Load>(Tags::load, &Cls::getLoad, &Cls::setLoad, DONT_SERIALIZE);
      m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource, &Cls::setResource, BASE);
      m->addPointerField<Cls, Resource>(Tags::alternate, &Cls::getResource, &Cls::setResource, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, nullptr, BOOL_FALSE, DONT_SERIALIZE);
      m->addDateField<Cls>(Tags::startdate, &Cls::getStartDate, nullptr, Date::infiniteFuture, DONT_SERIALIZE);
      m->addDateField<Cls>(Tags::enddate, &Cls::getEndDate, nullptr, Date::infiniteFuture, DONT_SERIALIZE);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, nullptr, DONT_SERIALIZE);
      m->addStringField<Cls>(Tags::setup, &Cls::getSetupLoad, nullptr, "", PLAN);
    }

    /** Finds the loadplan on the operationplan when we read data. */
    static Object* reader(const MetaClass*, const DataValueDict&, CommandManager*);

    bool isConfirmed() const
    {
      return (flags & STATUS_CONFIRMED) != 0;
    }

    void setConfirmed(bool b)
    {
      if (b)
        flags |= STATUS_CONFIRMED;
      else
        flags &= ~STATUS_CONFIRMED;
    }

    bool isApproved() const
    {
      return (flags & STATUS_APPROVED) != 0;
    }

    void setApproved(bool b)
    {
      if (b)
        flags |= STATUS_APPROVED;
      else
        flags &= ~STATUS_APPROVED;
    }

  private:
    /** Private constructor. It is called from the public constructor.<br>
      * The public constructor constructs the starting loadplan, while this
      * constructor creates the ending loadplan.
      */
    LoadPlan(OperationPlan*, const Load*, LoadPlan*);

    /** A pointer to the load model. */
    Load *ld;

    /** A pointer to the selected resource.<br>
      * In case we use skills, the resource of the loadplan can be different
      * than the resource on the load.
      */
    Resource *res;

    /** A pointer to the operationplan owning this loadplan. */
    OperationPlan *oper;

    /** Points to the next loadplan owned by the same operationplan. */
    LoadPlan *nextLoadPlan;
    static const short STATUS_CONFIRMED = 1;
    static const short STATUS_APPROVED = 2;

    /** Is this operationplanmaterial locked? */
    short flags = 0;
    /** This type is used to differentiate loadplans aligned with the START date
      * or the END date of operationplan. */
    enum type {START, END};

    /** Is this loadplan a starting one or an ending one. */
    type start_or_end;
};


/** This class allows iteration over alternate resources for a loadplan. */
class LoadPlan::AlternateIterator
{
  private:
    const LoadPlan* ldplan;
    vector<Resource*> resources;
    vector<Resource*>::iterator resIter;

  public:
    AlternateIterator(const LoadPlan*);

    /** Copy constructor. */
    AlternateIterator(const AlternateIterator& other) : ldplan(other.ldplan)
    {
      for (auto i = other.resources.begin(); i != other.resources.end(); ++i)
        resources.push_back(*i);
      resIter = resources.begin();
    }

    Resource* next();
};


inline LoadPlan::AlternateIterator LoadPlan::getAlternates() const
{
  return LoadPlan::AlternateIterator(this);
}


inline double Load::getLoadplanQuantity(const LoadPlan* lp) const
{
  if (!lp->getOperationPlan()->getProposed() && !lp->getOperationPlan()->getConsumeCapacity())
    // No capacity consumption required
    return 0.0;
  if (!lp->getOperationPlan()->getQuantity())
    // Operationplan has zero size, and so should the capacity it needs
    return 0.0;
  if (!lp->getOperationPlan()->getDates().overlap(getEffective())
      && (lp->getOperationPlan()->getDates().getDuration()
          || !getEffective().within(lp->getOperationPlan()->getStart())))
    // Load is not effective during this time.
    // The extra check is required to make sure that zero duration operationplans
    // operationplans don't get resized to 0
    return 0.0;
  if (getResource()->getType() == *ResourceBuckets::metadata)
    // Bucketized resource
    return - getQuantity() * lp->getOperationPlan()->getQuantity();
  else
    // Continuous resource
    return lp->isStart() ? getQuantity() : -getQuantity();
}


class Resource::OperationPlanIterator
{
  private:
    Resource::loadplanlist::const_iterator iter;

  public:
    /** Constructor. */
    OperationPlanIterator(const Resource* r) : iter(r->getLoadPlanIterator()) {}

    /** Return current value and advance the iterator. */
    OperationPlan* next()
    {
      Resource::loadplanlist::Event* i = iter.next();
      while (i && i->getEventType() == 1 && i->getQuantity() <= 0)
        i = iter.next();
      return i ? i->getOperationPlan() : nullptr;
    }
};


inline Resource::OperationPlanIterator Resource::getOperationPlans() const
{
  return Resource::OperationPlanIterator(this);
}


/** @brief This class models a iterator that walks over all available
  * HasProblem entities.
  *
  * This list is containing hard-coding the classes that are implementing
  * this class. It's not ideal, but we don't have an explicit container
  * of the objects (and we don't want one either) and this allows us also
  * to re-use the sorting used for the container classes.
  */
class HasProblems::EntityIterator
{
  private:
    /** This union contains iterators through the different entity types.
      * Only one of the different iterators will be active at a time, and
      * can thus save memory by collapsing the iterators into a single
      * union. */
    union
    {
      Buffer::iterator *bufIter;
      Resource::iterator *resIter;
      OperationPlan::iterator *operIter;
      Demand::iterator *demIter;
    };

    /** This type indicates which type of entity we are currently recursing
      * through.
      *  - 0: buffers
      *  - 1: resources
      *  - 2: operationplans
      *  - 3: demands
      */
    unsigned short type;

  public:
    /** Default constructor, which creates an iterator to the first
      * HasProblems object. */
    explicit EntityIterator();

    /** Used to create an iterator pointing beyond the last HasProblems
      * object. */
    explicit EntityIterator(unsigned short i) : bufIter(nullptr), type(i) {}

    /** Copy constructor. */
    EntityIterator(const EntityIterator&);

    /** Assignment operator. */
    EntityIterator& operator=(const EntityIterator&);

    /** Destructor. */
    ~EntityIterator();

    /** Pre-increment operator. */
    EntityIterator& operator++();

    /** Inequality operator.<br>
      * Two iterators are different when they point to different objects.
      */
    bool operator != (const EntityIterator& t) const;

    /** Equality operator.<br>
      * Two iterators are equal when they point to the same object.
      */
    bool operator == (const EntityIterator& t) const
    {
      return !(*this != t);
    }

    /** Dereference operator. */
    HasProblems& operator*() const;

    /** Dereference operator. */
    HasProblems* operator->() const;
};


/** @brief This class models an STL-like iterator that allows us to iterate
  * over the named entities in a simple and safe way.
  *
  * Objects of this class are returned by the begin() and end() functions.
  * @see Problem::begin()
  * @see Problem::begin(HasProblem*)
  * @see Problem::end()
  */
class Problem::iterator
{
    friend class Problem;

  protected:
    /** A pointer to the current problem. If this pointer is nullptr, we are
      * at the end of the list. */
    Problem* iter = nullptr;
    HasProblems* owner = nullptr;
    HasProblems::EntityIterator *eiter = nullptr;

  public:
    /** Creates an iterator that will loop through the problems of a
      * single entity only. <BR>
      * This constructor is also used to create a end-iterator, when passed
      * a nullptr pointer as argument.
      */
    explicit iterator(HasProblems* o) : iter(o ? o->firstProblem : nullptr),
      owner(o) {}

    /** Creates an iterator that will loop through the constraints of
      * a demand.
      */
    explicit iterator(Problem* o) : iter(o) {}

    /** Creates an iterator that will loop through the problems of all
      * entities. */
    explicit iterator()
    {
      // Update problems
      Plannable::computeProblems();

      // Loop till we find an entity with a problem
      eiter = new HasProblems::EntityIterator();
      while (*eiter != HasProblems::endEntity() && !((*eiter)->firstProblem))
        ++(*eiter);
      // Found a first problem, or no problem at all
      iter = (*eiter != HasProblems::endEntity()) ? (*eiter)->firstProblem : nullptr;
    }

    /** Copy constructor. */
    iterator(const iterator& i) : iter(i.iter), owner(i.owner)
    {
      if (i.eiter)
        eiter = new HasProblems::EntityIterator(*(i.eiter));
      else
        eiter = nullptr;
    }

    /** Destructor. */
    ~iterator()
    {
      if (eiter)
        delete eiter;
    }

    /** Pre-increment operator. */
    iterator& operator++();

    /** Return current problem and advance the iterator. */
    Problem* next()
    {
      Problem *tmp = iter;
      operator++();
      return tmp;
    }

    /** Inequality operator. */
    bool operator != (const iterator& t) const
    {
      return iter!=t.iter;
    }

    /** Equality operator. */
    bool operator == (const iterator& t) const
    {
      return iter==t.iter;
    }

    Problem& operator*() const
    {
      return *iter;
    }

    Problem* operator->() const
    {
      return iter;
    }
};


/** Retrieve an iterator for the list. */
inline Problem::iterator Problem::List::begin() const
{
  return Problem::iterator(first);
}


/** Stop iterator. */
inline Problem::iterator Problem::List::end() const
{
  return Problem::iterator(static_cast<Problem*>(nullptr));
}


class OperationPlan::ProblemIterator : public Problem::iterator
{
  private:
    stack<Problem*> relatedproblems;

  public:
    /** Constructor. */
    ProblemIterator(const OperationPlan*);

    /** Advance the iterator. */
    ProblemIterator& operator++();
};


inline OperationPlan::ProblemIterator OperationPlan::getProblems() const
{
  const_cast<OperationPlan*>(this)->updateProblems();
  return OperationPlan::ProblemIterator(this);
}


/** @brief This is the (logical) top class of the complete model.
  *
  * This is a singleton class: only a single instance can be created.
  * The data model has other limitations that make it not obvious to support
  * building multiple models/plans in memory of the same application: e.g.
  * the operations, resources, problems, operationplans... etc are all
  * implemented in static, global lists. An entity can't be simply linked with
  * a particular plan if multiple ones would exist.
  */
class Plan : public Plannable, public Object
{
  private:
    /** Current Date of this plan. */
    Date cur_Date;

    /** A name for this plan. */
    string name;

    /** A getDescription of this plan. */
    string descr;

    /** A calendar to which all operationplans will align. */
    Calendar* cal;

    /** Pointer to the singleton plan object. */
    static Plan* thePlan;

    /** The only constructor of this class is made private. An object of this
      * class is created by the instance() member function.
      */
    Plan() : cur_Date(Date::now()), cal(nullptr)
    {
      initType(metadata);
    }

  public:
    /** Return a pointer to the singleton plan object.
      * The singleton object is created during the initialization of the
      * library.
      */
    static Plan& instance()
    {
      return *thePlan;
    }

    /** Destructor.
      * @warning In multi threaded applications, the destructor is never called
      * and the plan object leaks when we exit the application.
      * In single-threaded applications this function is called properly, when
      * the static plan variable is deleted.
      */
    ~Plan();

    /** Returns the plan name. */
    string getName() const
    {
      return name;
    }

    /** Updates the plan name. */
    void setName(const string& s)
    {
      name = s;
    }

    /** Returns the current date of the plan. */
    Date getCurrent() const
    {
      return cur_Date;
    }

    /** Updates the current date of the plan. This method can be relatively
      * heavy in a plan where operationplans already exist, since the
      * detection for BeforeCurrent problems needs to be rerun.
      */
    void setCurrent(Date);

    /** Return the calendar to which operationplans are aligned. */
    Calendar* getCalendar() const
    {
      return cal;
    }

    /** Set a calendar to align operationplans to. */
    void setCalendar(Calendar* c)
    {
      cal = c;
    }

    /** Returns the description of the plan. */
    string getDescription() const
    {
      return descr;
    }

    /** Updates the description of the plan. */
    void setDescription(const string& str)
    {
      descr = str;
    }

    void setLogFile(const string& s)
    {
      Environment::setLogFile(s);
    }

    string getLogFile() const
    {
      return Environment::getLogFile();
    }

    /** Initialize the class. */
    static int initialize();

    virtual void updateProblems() {};

    /** This method basically solves the whole planning problem. */
    virtual void solve(Solver &s, void* v = nullptr) const {s.solve(this,v);}

    Location::iterator getLocations() const
    {
      return Location::begin();
    }

    Customer::iterator getCustomers() const
    {
      return Customer::begin();
    }

    Supplier::iterator getSuppliers() const
    {
      return Supplier::begin();
    }

    Calendar::iterator getCalendars() const
    {
      return Calendar::begin();
    }

    Operation::iterator getOperations() const
    {
      return Operation::begin();
    }

    Item::iterator getItems() const
    {
      return Item::begin();
    }

    Buffer::iterator getBuffers() const
    {
      return Buffer::begin();
    }

    Demand::iterator getDemands() const
    {
      return Demand::begin();
    }

    SetupMatrix::iterator getSetupMatrices() const
    {
      return SetupMatrix::begin();
    }

    Skill::iterator getSkills() const
    {
      return Skill::begin();
    }

    Resource::iterator getResources() const
    {
      return Resource::begin();
    }

    Problem::iterator getProblems() const
    {
      return Problem::iterator();
    }

    OperationPlan::iterator getOperationPlans() const
    {
      return OperationPlan::iterator();
    }

    unsigned long getOperationPlanID() const
    {
      return OperationPlan::getIDCounter();
    }

    void setOperationPlanID(unsigned long l)
    {
      OperationPlan::setIDCounter(l);
    }

    const MetaClass& getType() const {return *metadata;}
    static const MetaClass* metadata;
    static const MetaCategory* metacategory;

    template<class Cls>static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Plan>(Tags::name, &Plan::getName, &Plan::setName);
      m->addStringField<Plan>(Tags::description, &Plan::getDescription, &Plan::setDescription);
      m->addDateField<Plan>(Tags::current, &Plan::getCurrent, &Plan::setCurrent);
      m->addStringField<Plan>(Tags::logfile, &Plan::getLogFile, &Plan::setLogFile, "", DONT_SERIALIZE);
      m->addUnsignedLongField(Tags::id, &Plan::getOperationPlanID, &Plan::setOperationPlanID, 0, DONT_SERIALIZE);
      m->addPointerField<Cls, Calendar>(Tags::calendar, &Cls::getCalendar, &Cls::setCalendar, DONT_SERIALIZE);
      Plannable::registerFields<Plan>(m);
      m->addIteratorField<Plan, Location::iterator, Location>(Tags::locations, Tags::location, &Plan::getLocations, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Customer::iterator, Customer>(Tags::customers, Tags::customer, &Plan::getCustomers, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Supplier::iterator, Supplier>(Tags::suppliers, Tags::supplier, &Plan::getSuppliers, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Calendar::iterator, Calendar>(Tags::calendars, Tags::calendar, &Plan::getCalendars, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Resource::iterator, Resource>(Tags::resources, Tags::resource, &Plan::getResources, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Item::iterator, Item>(Tags::items, Tags::item, &Plan::getItems, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Buffer::iterator, Buffer>(Tags::buffers, Tags::buffer, &Plan::getBuffers, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Operation::iterator, Operation>(Tags::operations, Tags::operation, &Plan::getOperations, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Demand::iterator, Demand>(Tags::demands, Tags::demand, &Plan::getDemands, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, SetupMatrix::iterator, SetupMatrix>(Tags::setupmatrices, Tags::setupmatrix, &Plan::getSetupMatrices, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Skill::iterator, Skill>(Tags::skills, Tags::skill, &Plan::getSkills, BASE + WRITE_OBJECT);
      m->addIteratorField<Plan, Resource::skilllist::iterator, ResourceSkill>(Tags::resourceskills, Tags::resourceskill); // Only for XML import
      m->addIteratorField<Plan, Operation::loadlist::iterator, Load>(Tags::loads, Tags::load); // Only for XML import
      m->addIteratorField<Plan, Operation::flowlist::iterator, Flow>(Tags::flows, Tags::flow); // Only for XML import
      m->addIteratorField<Plan, Item::supplierlist::iterator, ItemSupplier>(Tags::itemsuppliers, Tags::itemsupplier); // Only for XML import
      m->addIteratorField<Plan, Location::distributionlist::iterator, ItemDistribution>(Tags::itemdistributions, Tags::itemdistribution); // Only for XML import
      m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Plan::getOperationPlans, BASE + WRITE_OBJECT);
    }
};


/** @brief A problem of this class is created when an operationplan is being
  * planned in the past, i.e. it starts before the "current" date of
  * the plan.
  */
class ProblemBeforeCurrent : public Problem
{
  public:
    string getDescription() const
    {
      ostringstream ch;
      ch << "Operation '"
          << (oper ? oper : static_cast<OperationPlan*>(getOwner())->getOperation())
          << "' planned in the past";
      return ch.str();
    }

    bool isFeasible() const
    {
      return false;
    }

    double getWeight() const
    {
      return oper ? qty : static_cast<OperationPlan*>(getOwner())->getQuantity();
    }

    explicit ProblemBeforeCurrent(OperationPlan* o, bool add = true) : Problem(o)
    {
      if (add) addProblem();
    }

    explicit ProblemBeforeCurrent(Operation* o, Date st, Date nd, double q)
      : oper(o), start(st), end(nd), qty(q) {}

    ~ProblemBeforeCurrent()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "operation";
    }

    Object* getOwner() const
    {
      return oper ? static_cast<Object*>(oper) : static_cast<OperationPlan*>(owner);
    }

    const DateRange getDates() const
    {
      if (oper)
        return DateRange(start, end);
      OperationPlan *o = static_cast<OperationPlan*>(getOwner());
      if (o->getConfirmed())
        return DateRange(o->getEnd(), Plan::instance().getCurrent());
      else
      {
        if (o->getEnd() > Plan::instance().getCurrent())
          return DateRange(o->getStart(), Plan::instance().getCurrent());
        else
          return o->getDates();
      }
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;

  private:
    Operation* oper = nullptr;
    Date start;
    Date end;
    double qty;
};


/** @brief A problem of this class is created when an operationplan is being
  * planned before its fence date, i.e. it starts 1) before the "current"
  * date of the plan plus the release fence of the operation and 2) after the
  * current date of the plan.
  */
class ProblemBeforeFence : public Problem
{
  public:
    string getDescription() const
    {
      ostringstream ch;
      ch << "Operation '"
          << (oper ? oper : static_cast<OperationPlan*>(getOwner())->getOperation())
          << "' planned before fence";
      return ch.str();
    }

    bool isFeasible() const
    {
      return true;
    }

    double getWeight() const
    {
      return oper ? qty : static_cast<OperationPlan*>(getOwner())->getQuantity();
    }

    explicit ProblemBeforeFence(OperationPlan* o, bool add = true)
      : Problem(o)
    {
      if (add) addProblem();
    }

    explicit ProblemBeforeFence(Operation* o, Date st, Date nd, double q)
      : oper(o), start(st), end(nd), qty(q) {}

    ~ProblemBeforeFence()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "operation";
    }

    Object* getOwner() const
    {
      return oper ? static_cast<Object*>(oper) : static_cast<OperationPlan*>(owner);
    }

    const DateRange getDates() const
    {
      if (oper)
        return DateRange(start, end);
      OperationPlan *o = static_cast<OperationPlan*>(owner);
      if (o->getEnd() > Plan::instance().getCurrent()
          + o->getOperation()->getFence())
        return DateRange(
          o->getStart(), 
          Plan::instance().getCurrent() + o->getOperation()->getFence()
          );
      else
        return o->getDates();
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;

  private:
    Operation* oper = nullptr;
    Date start;
    Date end;
    double qty;
};


/** @brief A problem of this class is created when the sequence of two
  * operationplans in a routing isn't respected.
  */
class ProblemPrecedence : public Problem
{
  public:
    string getDescription() const
    {
      OperationPlan *o = static_cast<OperationPlan*>(getOwner());
      if (!o->getNextSubOpplan())
        return string("Bogus precedence problem on '")
            + o->getOperation()->getName() + "'";
      else
        return string("Operation '") + o->getOperation()->getName()
            + "' starts before operation '"
            + o->getNextSubOpplan()->getOperation()->getName() +"' ends";
    }

    bool isFeasible() const
    {
      return false;
    }

    /** The weight of the problem is equal to the duration in days. */
    double getWeight() const
    {
      return static_cast<double>(getDates().getDuration()) / 86400;
    }

    explicit ProblemPrecedence(OperationPlan* o, bool add = true) : Problem(o)
    {
      if (add) addProblem();
    }

    ~ProblemPrecedence()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "operation";
    }

    Object* getOwner() const
    {
      return static_cast<OperationPlan*>(owner);
    }

    const DateRange getDates() const
    {
      OperationPlan *o = static_cast<OperationPlan*>(getOwner());
      return DateRange(o->getNextSubOpplan()->getStart(), o->getEnd());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;
};


/** @brief A Problem of this class is created in the model when a new demand is
  * brought in the system, but it hasn't been planned yet.
  *
  * As a special case, a demand with a requested quantity of 0.0 doesn't create
  * this type of problem.
  */
class ProblemDemandNotPlanned : public Problem
{
  public:
    string getDescription() const
    {
      return string("Demand '") + getDemand()->getName() + "' is not planned";
    }

    bool isFeasible() const
    {
      return false;
    }

    double getWeight() const
    {
      return getDemand()->getQuantity();
    }

    explicit ProblemDemandNotPlanned(Demand* d, bool add = true) : Problem(d)
    {
      if (add) addProblem();
    }

    ~ProblemDemandNotPlanned()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "demand";
    }

    const DateRange getDates() const
    {
      return DateRange(getDemand()->getDue(),getDemand()->getDue());
    }

    Object* getOwner() const
    {
      return static_cast<Demand*>(owner);
    }

    Demand* getDemand() const
    {
      return static_cast<Demand*>(owner);
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;
};


/** @brief A problem of this class is created when a demand is satisfied later
  * than the accepted tolerance after its due date.
  */
class ProblemLate : public Problem
{
  public:
    string getDescription() const;
    bool isFeasible() const
    {
      return true;
    }

    /** The weight is equal to the delay, expressed in days.<br>
      * The quantity being delayed is not included.
      */
    double getWeight() const
    {
      assert(getDemand() && !getDemand()->getDelivery().empty());
      return static_cast<double>(DateRange(
          getDemand()->getDue(),
          getDemand()->getLatestDelivery()->getEnd()
          ).getDuration()) / 86400;
    }

    /** Constructor. */
    explicit ProblemLate(Demand* d, bool add = true) : Problem(d)
    {
      if (add) addProblem();
    }

    /** Destructor. */
    ~ProblemLate()
    {
      removeProblem();
    }

    const DateRange getDates() const
    {
      assert(getDemand() && !getDemand()->getDelivery().empty());
      return DateRange(getDemand()->getDue(),
          getDemand()->getLatestDelivery()->getEnd());
    }

    Demand* getDemand() const
    {
      return static_cast<Demand*>(getOwner());
    }

    string getEntity() const
    {
      return "demand";
    }

    Object* getOwner() const
    {
      return static_cast<Demand*>(owner);
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;
};


/** @brief A problem of this class is created when a demand is planned earlier
  * than the accepted tolerance before its due date.
  */
class ProblemEarly : public Problem
{
  public:
    string getDescription() const;

    bool isFeasible() const
    {
      return true;
    }

    double getWeight() const
    {
      assert(getDemand() && !getDemand()->getDelivery().empty());
      return static_cast<double>(DateRange(
          getDemand()->getDue(),
          getDemand()->getEarliestDelivery()->getEnd()
          ).getDuration()) / 86400;
    }

    explicit ProblemEarly(Demand* d, bool add = true) : Problem(d)
    {
      if (add) addProblem();
    }

    ~ProblemEarly()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "demand";
    }

    Object* getOwner() const
    {
      return static_cast<Demand*>(owner);
    }

    const DateRange getDates() const
    {
      assert(getDemand() && !getDemand()->getDelivery().empty());
      return DateRange(getDemand()->getDue(),
          getDemand()->getEarliestDelivery()->getEnd());
    }

    Demand* getDemand() const
    {
      return static_cast<Demand*>(getOwner());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;
};


/** @brief A Problem of this class is created in the model when a data exception
  * prevents planning of certain objects
  */
class ProblemInvalidData : public Problem
{
  public:
    string getDescription() const
    {
      return description;
    }

    bool isFeasible() const
    {
      return false;
    }

    double getWeight() const
    {
      return qty;
    }

    explicit ProblemInvalidData(HasProblems* o, string d, string e,
        Date st, Date nd, double q, bool add = true)
      : Problem(o), description(d), entity(e), dates(st,nd), qty(q)
    {
      if (add) addProblem();
    }

    ~ProblemInvalidData()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return entity;
    }

    const DateRange getDates() const
    {
      return dates;
    }

    Object* getOwner() const
    {
      if (entity == "demand")
        return static_cast<Demand*>(owner);
      if (entity == "buffer" || entity == "material")
        return static_cast<Buffer*>(owner);
      if (entity == "resource" || entity == "capacity")
        return static_cast<Resource*>(owner);
      if (entity == "operation")
        return static_cast<Operation*>(owner);
      if (entity == "operationplan")
        return static_cast<OperationPlan*>(owner);
      throw LogicException("Unknown problem entity type");
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;

  private:
    /** Description of the data issue. */
    string description;
    string entity;
    DateRange dates;
    double qty;
};


/** @brief A problem of this class is created when a demand is planned for less than
  * the requested quantity.
  */
class ProblemShort : public Problem
{
  public:
    string getDescription() const
    {
      ostringstream ch;
      ch << "Demand '" << getDemand()->getName() << "' planned "
          << (getDemand()->getQuantity() - getDemand()->getPlannedQuantity())
          << " units short";
      return ch.str();
    }

    bool isFeasible() const
    {
      return true;
    }

    double getWeight() const
    {
      return getDemand()->getQuantity() - getDemand()->getPlannedQuantity();
    }

    explicit ProblemShort(Demand* d, bool add = true) : Problem(d)
    {
      if (add) addProblem();
    }

    ~ProblemShort()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "demand";
    }

    const DateRange getDates() const
    {
      return DateRange(getDemand()->getDue(), getDemand()->getDue());
    }

    Object* getOwner() const
    {
      return static_cast<Demand*>(owner);
    }

    Demand* getDemand() const
    {
      return static_cast<Demand*>(owner);
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;
};


/** @brief A problem of this class is created when a demand is planned for more
  * than the requested quantity.
  */
class ProblemExcess : public Problem
{
  public:
    string getDescription() const
    {
      ostringstream ch;
      ch << "Demand '" << getDemand()->getName() << "' planned "
          << (getDemand()->getPlannedQuantity() - getDemand()->getQuantity())
          << " units excess";
      return ch.str();
    }

    bool isFeasible() const
    {
      return true;
    }

    double getWeight() const
    {
      return getDemand()->getPlannedQuantity() - getDemand()->getQuantity();
    }

    explicit ProblemExcess(Demand* d, bool add = true) : Problem(d)
    {
      if (add) addProblem();
    }

    string getEntity() const
    {
      return "demand";
    }

    Object* getOwner() const
    {
      return static_cast<Demand*>(owner);
    }

    ~ProblemExcess()
    {
      removeProblem();
    }

    const DateRange getDates() const
    {
      return DateRange(getDemand()->getDue(), getDemand()->getDue());
    }

    Demand* getDemand() const
    {
      return static_cast<Demand*>(getOwner());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;
};


/** @brief A problem of this class is created when a resource is being
  * overloaded during a certain period of time.
  */
class ProblemCapacityOverload : public Problem
{
  public:
    string getDescription() const;

    bool isFeasible() const
    {
      return false;
    }

    double getWeight() const
    {
      return qty;
    }

    ProblemCapacityOverload(Resource* r, Date st, Date nd, double q, bool add = true)
      : Problem(r), qty(q), dr(st,nd)
    {
      if (add) addProblem();
    }

    ~ProblemCapacityOverload()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "capacity";
    }

    Object* getOwner() const
    {
      return static_cast<Resource*>(owner);
    }

    const DateRange getDates() const
    {
      return dr;
    }

    Resource* getResource() const
    {
      return static_cast<Resource*>(getOwner());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;

  private:
    /** Overload quantity. */
    double qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** @brief A problem of this class is created when a resource is loaded below
  * its minimum during a certain period of time.
  */
class ProblemCapacityUnderload : public Problem
{
  public:
    string getDescription() const;

    bool isFeasible() const
    {
      return true;
    }

    double getWeight() const
    {
      return qty;
    }

    ProblemCapacityUnderload(Resource* r, DateRange d, double q, bool add = true)
      : Problem(r), qty(q), dr(d)
    {
      if (add) addProblem();
    }

    ~ProblemCapacityUnderload()
    {
      removeProblem();
    }

    string getEntity() const
    {
      return "capacity";
    }

    Object* getOwner() const
    {
      return static_cast<Resource*>(owner);
    }

    const DateRange getDates() const
    {
      return dr;
    }

    Resource* getResource() const
    {
      return static_cast<Resource*>(getOwner());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;

  private:
    /** Underload quantity. */
    double qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** @brief A problem of this class is created when a buffer is having a
  * material shortage during a certain period of time.
  */
class ProblemMaterialShortage : public Problem
{
  public:
    string getDescription() const;

    bool isFeasible() const
    {
      return false;
    }

    double getWeight() const
    {
      return qty;
    }

    ProblemMaterialShortage(Buffer* b, Date st, Date nd, double q, bool add = true)
      : Problem(b), qty(q), dr(st,nd)
    {
      if (add) addProblem();
    }

    string getEntity() const
    {
      return "material";
    }

    Object* getOwner() const
    {
      return static_cast<Buffer*>(owner);
    }

    ~ProblemMaterialShortage()
    {
      removeProblem();
    }

    const DateRange getDates() const
    {
      return dr;
    }

    Buffer* getBuffer() const
    {
      return static_cast<Buffer*>(getOwner());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;

  private:
    /** Shortage quantity. */
    double qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** @brief A problem of this class is created when a buffer is carrying too
  * much material during a certain period of time.
  */
class ProblemMaterialExcess : public Problem
{
  public:
    string getDescription() const;

    bool isFeasible() const
    {
      return true;
    }

    double getWeight() const
    {
      return qty;
    }

    ProblemMaterialExcess(Buffer* b, Date st, Date nd, double q, bool add = true)
      : Problem(b), qty(q), dr(st,nd)
    {
      if (add) addProblem();
    }

    string getEntity() const
    {
      return "material";
    }

    ~ProblemMaterialExcess()
    {
      removeProblem();
    }

    const DateRange getDates() const
    {
      return dr;
    }

    Object* getOwner() const
    {
      return static_cast<Buffer*>(owner);
    }

    Buffer* getBuffer() const
    {
      return static_cast<Buffer*>(owner);
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static const MetaClass* metadata;

  private:
    /** Excess quantity. */
    double qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** @brief This command is used to create an operationplan.
  *
  * The operationplan will have its loadplans and flowplans created when the
  * command is created. It is assigned an id and added to the list of all
  * operationplans when the command is committed.
  */
class CommandCreateOperationPlan : public Command
{
  public:
    /** Constructor. */
    CommandCreateOperationPlan
    (const Operation* o, double q, Date d1, Date d2, Demand* l,
     OperationPlan* ow=nullptr, bool makeflowsloads=true, bool roundDown=true)
    {
      opplan = o ?
          o->createOperationPlan(q, d1, d2, l, ow, 0, makeflowsloads, roundDown)
          : nullptr;
    }

    void commit()
    {
      if (opplan)
      {
        opplan->activate();
        opplan = nullptr; // Avoid executing / initializing more than once
      }
    }

    virtual void rollback()
    {
      delete opplan;
      opplan = nullptr;
    }

    virtual void undo()
    {
      if (opplan) opplan->deleteFlowLoads();
    }

    virtual ~CommandCreateOperationPlan()
    {
      if (opplan) delete opplan;
    }

    OperationPlan *getOperationPlan() const
    {
      return opplan;
    }

    virtual short getType() const
    {
      return 5;
    }
  private:
    /** Pointer to the newly created operationplan. */
    OperationPlan *opplan;
};


/** @brief This command is used to delete an operationplan.<br>
  * The implementation assumes there is only a single level of child
  * sub operationplans.
  */
class CommandDeleteOperationPlan : public Command
{
  public:
    /** Constructor. */
    CommandDeleteOperationPlan(OperationPlan* o);

    virtual void commit()
    {
      if (opplan) delete opplan;
      opplan = nullptr;
    }

    virtual void undo()
    {
      if (!opplan) return;
      opplan->createFlowLoads();
      opplan->insertInOperationplanList();
      if (opplan->getDemand())
        opplan->getDemand()->addDelivery(opplan);
      OperationPlan::iterator x(opplan);
      while (OperationPlan* i = x.next())
      {
        // TODO the recreation of the flows and loads can recreate them on a different 
        // resource from the pool. This results in a different resource loading, setup time
        // and duration.
        i->createFlowLoads();
        i->insertInOperationplanList();
      }
    }

    virtual void rollback()
    {
      undo();
      opplan = nullptr;
    }

    virtual ~CommandDeleteOperationPlan()
    {
      undo();
    }

    virtual short getType() const
    {
      return 6;
    }
  private:
    /** Pointer to the operationplan being deleted.<br>
      * Until the command is committed we don't deallocate the memory for the
      * operationplan, but only remove all pointers to it from various places.
      */
    OperationPlan *opplan;
};


/** @brief This class represents the command of moving an operationplan to a
  * new date and/or resizing it.
  * @todo Moving in a routing operation can't be undone with the current
  * implementation! The command will need to store all original dates of
  * the suboperationplans...
  */
class CommandMoveOperationPlan : public Command
{
  public:
    /** Constructor.<br>
      * Unlike most other commands the constructor already executes the change.
      * @param opplanptr Pointer to the operationplan being moved.
      * @param newStart New start date of the operationplan.
      * @param newEnd New end date of the operationplan.
      * @param newQty New quantity of the operationplan.The default is -1,
      * which indicates to leave the quantity unchanged.
      */
    CommandMoveOperationPlan(OperationPlan* opplanptr,
        Date newStart, Date newEnd, double newQty = -1.0);

    /** Default constructor. */
    CommandMoveOperationPlan(OperationPlan*);

    /** Commit the changes. */
    virtual void commit()
    {
      opplan->mergeIfPossible();
      opplan = nullptr;
    }

    /** Undo the changes. */
    virtual void rollback()
    {
      restore(true);
      opplan = nullptr;
    }

    virtual void undo()
    {
      restore(false);
    }

    /** Undo the changes.<br>
      * When the argument is true, subcommands for suboperationplans are deleted. */
    void restore(bool = false);

    /** Destructor. */
    virtual ~CommandMoveOperationPlan()
    {
      if (opplan)
        rollback();
    }

    /** Returns the operationplan being manipulated. */
    OperationPlan* getOperationPlan() const
    {
      return opplan;
    }

    /** Set another start date for the operationplan. */
    void setStart(Date d)
    {
      if (opplan)
        opplan->setStart(d);
    }

    /** Set another start date, end date and quantity for the operationplan. */
    void setParameters(Date s, Date e, double q, bool b, bool roundDown=true)
    {
      assert(opplan->getOperation());
      if (opplan)
        opplan->getOperation()->setOperationPlanParameters(opplan, q, s, e, b, true, roundDown);
    }

    /** Set another start date for the operationplan. */
    void setEnd(Date d)
    {
      if (opplan)
        opplan->setEnd(d);
    }

    /** Set another quantity for the operationplan. */
    void setQuantity(double q)
    {
      if (opplan) opplan->setQuantity(q);
    }

    /** Return the quantity of the original operationplan. */
    double getQuantity() const
    {
      return state.quantity;
    }

    /** Return the dates of the original operationplan. */
    DateRange getDates() const
    {
      return DateRange(state.start, state.end);
    }

    virtual short getType() const
    {
      return 7;
    }
  private:
    /** This is a pointer to the operationplan being moved. */
    OperationPlan *opplan = nullptr;

    /** Store the state of the operation plan. */
    OperationPlanState state;

    /** A pointer to a list of suboperationplan commands. */
    Command* firstCommand = nullptr;
};


/** @brief This class allows upstream and downstream navigation through
  * the plan.
  *
  * Downstream navigation follows the material flow from raw materials
  * towards the produced end item.<br>
  * Upstream navigation traces back the material flow from the end item up to
  * the consumed raw materials.<br>
  * The class is implemented as an STL-like iterator.
  */
class PeggingIterator : public Object
{
  public:
    /** Copy constructor. */
    PeggingIterator(const PeggingIterator& c);

    /** Constructor for demand pegging. */
    PeggingIterator(const Demand*);

    /** Constructor for operationplan pegging. */
    PeggingIterator(const OperationPlan*, bool=true);

    /** Constructor for flowplan pegging. */
    PeggingIterator(FlowPlan*, bool=true);

    /** Constructor for loadplan pegging. */
    PeggingIterator(LoadPlan*, bool=true);

    /** Return the operationplan. */
    OperationPlan* getOperationPlan() const
    {
      return second_pass ?
        const_cast<OperationPlan*>(states_sorted.front().opplan) :
        const_cast<OperationPlan*>(states.back().opplan);
    }

    /** Destructor. */
    virtual ~PeggingIterator() {}

    /** Return true if this is a downstream iterator. */
    inline bool isDownstream() const
    {
      return downstream;
    }

    /** Return the pegged quantity. */
    double getQuantity() const
    {
      return second_pass ?
        states_sorted.front().quantity :
        states.back().quantity;
    }

    /** Returns the recursion depth of the iterator.*/
    short getLevel() const
    {
      return second_pass ?
        states_sorted.front().level :
        states.back().level;
    }

    /** Move the iterator downstream. */
    PeggingIterator& operator++();

    /** Move the iterator upstream. */
    PeggingIterator& operator--();

    /** Conversion operator to a boolean value.
      * The return value is true when the iterator still has next elements to
      * explore. Returns false when the iteration is finished.
      */
    operator bool() const
    {
      return second_pass ? !states_sorted.empty() : !states.empty();
    }

    PeggingIterator* next();

    /** Add an entry on the stack. */
    void updateStack(const OperationPlan*, double, double, short);

    /** Initialize the class. */
    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, OperationPlan>(Tags::operationplan, &Cls::getOperationPlan, nullptr, PLAN + WRITE_OBJECT + WRITE_HIDDEN);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, nullptr, -1, MANDATORY);
      m->addShortField<Cls>(Tags::level, &Cls::getLevel, nullptr, -1, MANDATORY);
    }

  private:
    /** This structure is used to keep track of the iterator states during the
      * iteration. */
    struct state
    {
      const OperationPlan* opplan;
      double quantity;
      double offset;
      short level;

      // Constructor
      state(const OperationPlan* op, double q, double o, short l)
        : opplan(op), quantity(q), offset(o), level(l) {};

      // Copy constructor
      state(const state& o)
        : opplan(o.opplan), quantity(o.quantity), offset(o.offset), level(o.level) {};

      // Comparison operator
      bool operator < (const state& other) const
      {
        if (opplan->getStart() == other.opplan->getStart())
          return other.opplan->getEnd() < opplan->getEnd();
        else
          return other.opplan->getStart() < opplan->getStart();
      }
    };
    typedef vector<state> statestack;

    /* Auxilary function to make recursive code possible. */
    void followPegging(const OperationPlan*, double, double, short);

    /** Store a list of all operations still to peg. */
    statestack states;

    deque<state> states_sorted;

    /** Follow the pegging upstream or downstream. */
    bool downstream;

    /** Used by the Python iterator to mark the first call. */
    bool firstIteration;

    /** Optimization to reuse elements on the stack. */
    bool first;

    /** Extra data structure to avoid duplicate operationplan ids in the list. */
    bool second_pass;    
};


/** An iterator that shows all demands linked to an operationplan. */
class PeggingDemandIterator : public Object
{
  private:
    typedef map<Demand*, double> demandmap;
    demandmap dmds;
    demandmap::const_iterator iter;
    bool first = true;

  public:
    /** Constructor. */
    PeggingDemandIterator(const OperationPlan*);

    /** Copy constructor. */
    PeggingDemandIterator(const PeggingDemandIterator&);

    /** Advance to the next demand. */
    PeggingDemandIterator* next();

    /** Initialize the class. */
    static int initialize();

    virtual const MetaClass& getType() const { return *metadata; }
    static const MetaCategory* metadata;

    Demand* getDemand() const
    {
      return iter != dmds.end() ? iter->first : nullptr;
    }

    double getQuantity() const
    {
      return iter != dmds.end() ? iter->second : 0.0;
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Demand>(Tags::demand, &Cls::getDemand, nullptr, MANDATORY + WRITE_REFERENCE + WRITE_HIDDEN);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, nullptr, -1, MANDATORY);
    }
};


/** @brief An iterator class to go through all flowplans of an operationplan.
  * @see OperationPlan::beginFlowPlans
  * @see OperationPlan::endFlowPlans
  */
class OperationPlan::FlowPlanIterator
{
    friend class OperationPlan;
  private:
    FlowPlan* curflowplan = nullptr;
    FlowPlan* prevflowplan = nullptr;

    FlowPlanIterator(FlowPlan* b) : curflowplan(b) {}

  public:
    FlowPlanIterator(const FlowPlanIterator& b)
    {
      curflowplan = b.curflowplan;
      prevflowplan = b.prevflowplan;
    }

    bool operator != (const FlowPlanIterator &b) const
    {
      return b.curflowplan != curflowplan;
    }

    bool operator == (const FlowPlanIterator &b) const
    {
      return b.curflowplan == curflowplan;
    }

    FlowPlanIterator& operator++()
    {
      prevflowplan = curflowplan;
      if (curflowplan) curflowplan = curflowplan->nextFlowPlan;
      return *this;
    }

    FlowPlanIterator operator++(int)
    {
      FlowPlanIterator tmp = *this;
      ++*this;
      return tmp;
    }

    FlowPlan* operator ->() const
    {
      return curflowplan;
    }

    FlowPlan& operator *() const
    {
      return *curflowplan;
    }

    void deleteFlowPlan()
    {
      if (!curflowplan)
        return;
      if (prevflowplan)
        prevflowplan->nextFlowPlan = curflowplan->nextFlowPlan;
      else
        curflowplan->oper->firstflowplan = curflowplan->nextFlowPlan;
      FlowPlan* tmp = curflowplan;
      // Move the iterator to the next element
      curflowplan = curflowplan->nextFlowPlan;
      delete tmp;
    }

    FlowPlan* next()
    {
      prevflowplan = curflowplan;
      if (curflowplan)
        curflowplan = curflowplan->nextFlowPlan;
      return prevflowplan;
    }
};


inline OperationPlan::FlowPlanIterator OperationPlan::beginFlowPlans() const
{
  return OperationPlan::FlowPlanIterator(firstflowplan);
}


inline OperationPlan::FlowPlanIterator OperationPlan::endFlowPlans() const
{
  return OperationPlan::FlowPlanIterator(nullptr);
}


inline OperationPlan::FlowPlanIterator OperationPlan::getFlowPlans() const
{
  return OperationPlan::FlowPlanIterator(firstflowplan);
}


inline int OperationPlan::sizeFlowPlans() const
{
  int c = 0;
  for (FlowPlanIterator i = beginFlowPlans(); i != endFlowPlans(); ++i) ++c;
  return c;
}


/** @brief An iterator class to go through all loadplans of an operationplan.
  * @see OperationPlan::beginLoadPlans
  * @see OperationPlan::endLoadPlans
  */
class OperationPlan::LoadPlanIterator
{
    friend class OperationPlan;
  private:
    LoadPlan* curloadplan = nullptr;
    LoadPlan* prevloadplan = nullptr;
    LoadPlanIterator(LoadPlan* b) : curloadplan(b) {}
  public:
    LoadPlanIterator(const LoadPlanIterator& b)
    {
      curloadplan = b.curloadplan;
      prevloadplan = b.prevloadplan;
    }

    bool operator != (const LoadPlanIterator &b) const
    {
      return b.curloadplan != curloadplan;
    }

    bool operator == (const LoadPlanIterator &b) const
    {
      return b.curloadplan == curloadplan;
    }

    LoadPlanIterator& operator++()
    {
      prevloadplan = curloadplan;
      if (curloadplan) curloadplan = curloadplan->nextLoadPlan;
      return *this;
    }

    LoadPlanIterator operator++(int)
    {
      LoadPlanIterator tmp = *this;
      ++*this;
      return tmp;
    }

    LoadPlan* operator ->() const
    {
      return curloadplan;
    }

    LoadPlan& operator *() const
    {
      return *curloadplan;
    }

    void deleteLoadPlan()
    {
      if (!curloadplan) return;
      if (prevloadplan) prevloadplan->nextLoadPlan = curloadplan->nextLoadPlan;
      else curloadplan->oper->firstloadplan = curloadplan->nextLoadPlan;
      LoadPlan* tmp = curloadplan;
      // Move the iterator to the next element
      curloadplan = curloadplan->nextLoadPlan;
      delete tmp;
    }

    LoadPlan* next()
    {
      prevloadplan = curloadplan;
      if (curloadplan)
        curloadplan = curloadplan->nextLoadPlan;
      return prevloadplan;
    }
};


inline OperationPlan::LoadPlanIterator OperationPlan::beginLoadPlans() const
{
  return OperationPlan::LoadPlanIterator(firstloadplan);
}


inline OperationPlan::LoadPlanIterator OperationPlan::endLoadPlans() const
{
  return OperationPlan::LoadPlanIterator(nullptr);
}


inline OperationPlan::LoadPlanIterator OperationPlan::getLoadPlans() const
{
  return OperationPlan::LoadPlanIterator(firstloadplan);
}


inline int OperationPlan::sizeLoadPlans() const
{
  int c = 0;
  for (LoadPlanIterator i = beginLoadPlans(); i != endLoadPlans(); ++i) ++c;
  return c;
}


class OperationPlan::InterruptionIterator : public Object
{
  private:
    vector<Calendar::EventIterator> cals;
    Date curdate;
    const OperationPlan* opplan;
    Date start;
    Date end;
    bool status = false;

  public:
    InterruptionIterator(const OperationPlan* o) : opplan(o) 
    {
      if (!opplan || !opplan->getOperation())
        throw LogicException("Can't initialize an iterator over an uninitialized operationplan");
      opplan->getOperation()->collectCalendars(cals, opplan->getStart(), opplan);
      curdate = opplan->getStart();
      start = curdate;
      initType(metadata);
    }

    InterruptionIterator* next();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDateField<Cls>(Tags::start, &Cls::getStart);
      m->addDateField<Cls>(Tags::end, &Cls::getEnd);
    }

    Date getStart() const
    {
      return start;
    }

    Date getEnd() const
    {
      return end;
    }

    /** Return a reference to the metadata structure. */
    virtual const MetaClass& getType() const { return *metadata; }

    static int intitialize();
    static const MetaCategory* metacategory;
    static const MetaClass* metadata;
};


inline OperationPlan::InterruptionIterator OperationPlan::getInterruptions() const
{
  return OperationPlan::InterruptionIterator(this);
}


class CalendarEventIterator
  : public PythonExtension<CalendarEventIterator>
{
  public:
    static int initialize();

    CalendarEventIterator(Calendar* c, Date d=Date::infinitePast, bool f=true)
      : cal(c), eventiter(c, d, f), forward(f) {}

  private:
    Calendar* cal;
    Calendar::EventIterator eventiter;
    bool forward;
    PyObject *iternext();
};


class FlowPlanIterator : public PythonExtension<FlowPlanIterator>
{
  public:
    /** Registration of the Python class and its metadata. */
    static int initialize();

    /** Constructor to iterate over the flowplans of a buffer. */
    FlowPlanIterator(Buffer* b) : buf(b), buffer_or_opplan(true)
    {
      if (!b)
        throw LogicException("Creating flowplan iterator for nullptr buffer");
      bufiter = new Buffer::flowplanlist::const_iterator(b->getFlowPlans().begin());
    }

    /** Constructor to iterate over the flowplans of an operationplan. */
    FlowPlanIterator(OperationPlan* o) : opplan(o), buffer_or_opplan(false)
    {
      if (!o)
        throw LogicException("Creating flowplan iterator for nullptr operationplan");
      opplaniter = new OperationPlan::FlowPlanIterator(o->beginFlowPlans());
    }

    ~FlowPlanIterator()
    {
      if (buffer_or_opplan) delete bufiter;
      else delete opplaniter;
    }

  private:
    union
    {
      Buffer* buf;
      OperationPlan* opplan;
    };

    union
    {
      Buffer::flowplanlist::const_iterator *bufiter;
      OperationPlan::FlowPlanIterator *opplaniter;
    };

    /** Flags whether we are browsing over the flowplans in a buffer or in an
      * operationplan. */
    bool buffer_or_opplan;

    PyObject *iternext();
};


class LoadPlanIterator : public PythonExtension<LoadPlanIterator>
{
  public:
    static int initialize();

    LoadPlanIterator(Resource* r) : res(r), resource_or_opplan(true)
    {
      if (!r)
        throw LogicException("Creating loadplan iterator for nullptr resource");
      resiter = new Resource::loadplanlist::const_iterator(r->getLoadPlans().begin());
    }

    LoadPlanIterator(OperationPlan* o) : opplan(o), resource_or_opplan(false)
    {
      if (!opplan)
        throw LogicException("Creating loadplan iterator for nullptr operationplan");
      opplaniter = new OperationPlan::LoadPlanIterator(o->beginLoadPlans());
    }

    ~LoadPlanIterator()
    {
      if (resource_or_opplan) delete resiter;
      else delete opplaniter;
    }

  private:
    union
    {
      Resource* res;
      OperationPlan* opplan;
    };

    union
    {
      Resource::loadplanlist::const_iterator *resiter;
      OperationPlan::LoadPlanIterator *opplaniter;
    };

    /** Flags whether we are browsing over the flowplans in a buffer or in an
      * operationplan. */
    bool resource_or_opplan;

    PyObject *iternext();
};


/** @brief This Python function is used for reading XML input.
  *
  * The function takes up to three arguments:
  *   - XML data file to be processed.
  *     If this argument is omitted or None, the standard input is read.
  *   - Optional validate flag, defining whether or not the input data needs to be
  *     validated against the XML schema definition.
  *     The validation is switched ON by default.
  *     Switching it ON is recommended in situations where there is no 100% guarantee
  *     on the validity of the input data.
  *   - Optional validate_only flag, which allows us to validate the data but
  *     skip any processing.
  */
PyObject* readXMLfile(PyObject*, PyObject*);


/** @brief This Python function is used for processing XML input data from a string.
  *
  * The function takes up to three arguments:
  *   - XML data string to be processed
  *   - Optional validate flag, defining whether or not the input data needs to be
  *     validated against the XML schema definition.
  *     The validation is switched ON by default.
  *     Switching it ON is recommended in situations where there is no 100% guarantee
  *     on the validity of the input data.
  *   - Optional validate_only flag, which allows us to validate the data but
  *     skip any processing.
  */
PyObject* readXMLdata(PyObject *, PyObject *);


/** @brief This Python function writes the dynamic part of the plan to an text file.
  *
  * This saved information covers the buffer flowplans, operationplans,
  * resource loading, demand, problems, etc...<br>
  * The main use of this function is in the test suite: a simple text file
  * comparison allows us to identify changes quickly. The output format is
  * only to be seen in this context of testing, and is not intended to be used
  * as an official method for publishing plans to other systems.
  */
PyObject* savePlan(PyObject*, PyObject*);


/** @brief This Python function prints a summary of the dynamically allocated
  * memory to the standard output. This is useful for understanding better the
  * size of your model.
  *
  * The numbers reported by this function won't match the memory size as
  * reported by the operating system, since the dynamically allocated memory
  * is only a part of the total memory used by a program.
  */
PyObject* printModelSize(PyObject* self, PyObject* args);


/** @brief This python function writes the complete model to a XML-file.
  *
  * Both the static model (i.e. items, locations, buffers, resources,
  * calendars, etc...) and the dynamic data (i.e. the actual plan including
  * the operationplans, demand, problems, etc...).<br>
  * The format is such that the output file can be re-read to restore the
  * very same model.<br>
  * The function takes the following arguments:
  *   - Name of the output file
  *   - Type of output desired: BASE, PLAN or DETAIL.
  *     The default value is BASE.
  */
PyObject* saveXMLfile(PyObject*, PyObject*);


/** @brief This Python function erases the model or the plan from memory.
  *
  * The function allows the following modes to control what to delete:
  *  - plan:<br>
  *    Deletes the dynamic modelling constructs, such as operationplans,
  *    loadplans and flowplans only. Locked operationplans are not
  *    deleted.<br>
  *    The static model is left intact.<br>
  *    This is the default mode.
  *  - model:<br>
  *    The dynamic as well as the static objects are removed. You'll end
  *    up with a completely empty model.
  *    Due to the logic required in the object destructors this mode doesn't
  *    scale linear with the model size.
  */
PyObject* eraseModel(PyObject* self, PyObject* args);


}   // End namespace

#endif
