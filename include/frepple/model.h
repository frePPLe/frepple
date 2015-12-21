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
#include "frepple/timeline.h"
using namespace frepple::utils;

namespace frepple
{

class Flow;
class FlowEnd;
class FlowFixedStart;
class FlowFixedEnd;
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
class BufferProcure;
class Plan;
class Plannable;
class Calendar;
class CalendarBucket;
class Load;
class LoadDefault;
class Location;
class Customer;
class HasProblems;
class Solvable;
class PeggingIterator;
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
    /** Unique identifier of the bucket within the calendar. */
    int id;

    /** Start date of the bucket. */
    Date startdate;

    /** End Date of the bucket. */
    Date enddate;

    /** A pointer to the next bucket. */
    CalendarBucket* nextBucket;

    /** A pointer to the previous bucket. */
    CalendarBucket* prevBucket;

    /** Priority of this bucket, compared to other buckets effective
      * at a certain time.
      */
    int priority;

    /** Weekdays on which the entry is effective.
      * - Bit 0: Sunday
      * - Bit 1: Monday
      * - Bit 2: Tueday
      * - Bit 3: Wednesday
      * - Bit 4: Thursday
      * - Bit 5: Friday
      * - Bit 6: Saturday
      */
    short days;

    /** Starting time on the effective days. */
    Duration starttime;

    /** Ending time on the effective days. */
    Duration endtime;

    /** A pointer to the owning calendar. */
    Calendar *cal;

    /** Value of this bucket.*/
    double val;

    /** An internally managed data structure to keep the offsets
      * inside the week where the entry changes effectivity.
      * TODO This type of data structure is not good when the DST changes during the week. Need to reimplement without this offset data structure!
      */
    long offsets[14];

    /** An internal counter for the number of indices used in the
      * offset array. */
    short offsetcounter;

    /** Updates the offsets data structure. */
    DECLARE_EXPORT void updateOffsets();

    /** Keep all calendar buckets sorted in ascending order of start date
      * and use the priority as a tie breaker.
      */
    DECLARE_EXPORT void updateSort();

  protected:
    /** Auxilary function to write out the start of the XML. */
    DECLARE_EXPORT void writeHeader(Serializer *, const Keyword&) const;

  public:
    /** Default constructor. */
    DECLARE_EXPORT CalendarBucket() : id(INT_MIN), enddate(Date::infiniteFuture),
      nextBucket(NULL), prevBucket(NULL), priority(0), days(127),
      starttime(0L), endtime(86400L), cal(NULL), val(0.0), offsetcounter(0)
    {
      initType(metadata);
    }

    /** This is a factory method that creates a new bucket in a calendar.<br>
      * It uses the calendar and id fields to identify existing buckets.
      */
    static DECLARE_EXPORT Object* createBucket(const MetaClass*, const DataValueDict&);

    /** Update the calendar owning the bucket.<br>
      * TODO You cannot reassign a bucket once it's assigned to a calendar.
      */
    DECLARE_EXPORT void setCalendar(Calendar*);

    /** Return the calendar to whom the bucket belongs. */
    Calendar* getCalendar() const
    {
      return cal;
    }

    /** Get the identifier. */
    int getId() const
    {
      return id;
    }

    /** Generate the identfier.<br>
      * If a bucket with the given identifier already exists a unique
      * number is generated instead. This is done by incrementing the
      * value passed until it is unique.
      */
    DECLARE_EXPORT void setId(int ident=INT_MIN);

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
    DECLARE_EXPORT void setEnd(const Date d);

    /** Returns the start date of the bucket. */
    Date getStart() const
    {
      return startdate;
    }

    /** Updates the start date of the bucket. */
    DECLARE_EXPORT void setStart(const Date d);

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
      updateOffsets();
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
      updateOffsets();
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
      updateOffsets();
    }

    /** Convert the value of the bucket to a boolean value. */
    virtual bool getBool() const
    {
      return val != 0;
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metacategory;
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addIntField<Cls>(Tags::id, &Cls::getId, &Cls::setId, INT_MIN, MANDATORY);
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
        iterator(CalendarBucket* b = NULL) : curBucket(b) {}

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
          return NULL;
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
  friend class CalendarBucket;
  public:
    class EventIterator; // Forward declaration

    /** Default constructor. */
    explicit DECLARE_EXPORT Calendar() : firstBucket(NULL), defaultValue(0.0) {}

    /** Destructor, which cleans up the buckets too and all references to the
      * calendar from the core model.
      */
    DECLARE_EXPORT ~Calendar();

    /** Returns the value on the specified date. */
    double getValue(const Date d) const
    {
      CalendarBucket* x = static_cast<CalendarBucket*>(findBucket(d));
      return x ? x->getValue() : defaultValue;
    }

    /** Updates the value in a certain date range.<br>
      * This will create a new bucket if required.
      */
    DECLARE_EXPORT void setValue(Date start, Date end, const double v);

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

    /** Removes a bucket from the list. */
    DECLARE_EXPORT void removeBucket(CalendarBucket* bkt);

    /** Returns the bucket where a certain date belongs to.
      * A NULL pointer is returned when no bucket is effective.
      */
    DECLARE_EXPORT CalendarBucket* findBucket(Date d, bool fwd = true) const;

    /** Returns the bucket with a certain identifier.
      * A NULL pointer is returned in case no bucket can be found with the
      * given identifier.
      */
    DECLARE_EXPORT CalendarBucket* findBucket(int ident) const;

    /** Add a new bucket to the calendar. */
    DECLARE_EXPORT CalendarBucket* addBucket(Date, Date, double);

    /** Find an existing bucket with a given identifier, or create a new one.
      * If no identifier is passed, we always create a new bucket and automatically
      * generate a unique identifier for it.
      */
    static DECLARE_EXPORT PyObject* addPythonBucket(PyObject*, PyObject*, PyObject*);

    /** @brief An iterator class to go through all dates where the calendar
      * value changes.*/
    class EventIterator
    {
        friend class CalendarBucket;
      protected:
        const Calendar* theCalendar;
        const CalendarBucket* curBucket;
        const CalendarBucket* lastBucket;
        Date curDate;
        int curPriority;
        int lastPriority;
      public:
        const Date& getDate() const
        {
          return curDate;
        }

        const CalendarBucket* getBucket() const
        {
          return curBucket;
        }

        const Calendar* getCalendar() const
        {
          return theCalendar;
        }

        DECLARE_EXPORT EventIterator(const Calendar* c = NULL,
          Date d = Date::infinitePast, bool forward = true);

        DECLARE_EXPORT EventIterator& operator++();

        DECLARE_EXPORT EventIterator& operator--();

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

        /** Return the current value of the iterator at this date. */
        double getValue()
        {
          return curBucket ?
              static_cast<const CalendarBucket*>(curBucket)->getValue() :
              static_cast<const Calendar*>(theCalendar)->getDefault();
        }

      private:
        /** Increments an iterator to the next change event.<br>
          * A bucket will evaluate the current state of the iterator, and
          * update it if a valid next event can be generated.
          */
        DECLARE_EXPORT void nextEvent(const CalendarBucket*, Date);

        /** Increments an iterator to the previous change event.<br>
          * A bucket will evaluate the current state of the iterator, and
          * update it if a valid previous event can be generated.
          */
        DECLARE_EXPORT void prevEvent(const CalendarBucket*, Date);
    };

    /** Returns an iterator to go through the list of buckets. */
    CalendarBucket::iterator getBuckets() const
    {
      return CalendarBucket::iterator(firstBucket);
    }

    static DECLARE_EXPORT PyObject* setPythonValue(PyObject*, PyObject*, PyObject*);

    static int initialize();

    static DECLARE_EXPORT PyObject* getEvents(PyObject*, PyObject*);

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "", MANDATORY);
      HasSource::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::deflt, &Cls::getDefault, &Cls::setDefault);
      m->addIteratorField<Cls, CalendarBucket::iterator, CalendarBucket>(Tags::buckets, Tags::bucket, &Cls::getBuckets, BASE + WRITE_FULL);
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
    CalendarBucket* firstBucket;

    /** Value used when no bucket is effective at all. */
    double defaultValue;
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
    static DECLARE_EXPORT const MetaClass* metadata;
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
    explicit Problem(HasProblems *p = NULL) : owner(p), nextProblem(NULL)
    {
      initType(metadata);
    }

    /** Initialize the class. */
    static int initialize();

    /** Destructor.
      * @see removeProblem
      */
    virtual DECLARE_EXPORT ~Problem() {}

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
    static DECLARE_EXPORT iterator begin();

    /** Return an iterator to the first problem of this entity. The iterator
      * can be incremented till it points past the last problem of this
      * plannable entity.<br>
      * The boolean argument specifies whether the problems need to be
      * recomputed as part of this method.
      */
    static DECLARE_EXPORT iterator begin(HasProblems*, bool = true);

    /** Return an iterator pointing beyond the last problem. */
    static DECLARE_EXPORT const iterator end();

    /** Erases the list of all problems. This methods can be used reduce the
      * memory consumption at critical points. The list of problems will be
      * recreated when the problem detection is triggered again.
      */
    static DECLARE_EXPORT void clearProblems();

    /** Erases the list of problems linked with a certain plannable object.<br>
      * If the second parameter is set to true, the problems will be
      * recreated when the next problem detection round is triggered.
      */
    static DECLARE_EXPORT void clearProblems(HasProblems& p, bool setchanged = true);

    /** Returns a pointer to the object that owns this problem. */
    virtual Object* getOwner() const = 0;

    /** Return a reference to the metadata structure. */
    virtual const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, NULL, "", MANDATORY + COMPUTED);
      m->addStringField<Cls>(Tags::description, &Cls::getDescription, NULL, "", MANDATORY + COMPUTED);
      m->addDateField<Cls>(Tags::start, &Cls::getStart, NULL, Date::infinitePast, MANDATORY);
      m->addDateField<Cls>(Tags::end, &Cls::getEnd, NULL, Date::infiniteFuture, MANDATORY);
      m->addDoubleField<Cls>(Tags::weight, &Cls::getWeight, NULL, 0.0, MANDATORY);
      m->addStringField<Cls>(Tags::entity, &Cls::getEntity, NULL, "", DONT_SERIALIZE);
      m->addPointerField<Cls, Object>(Tags::owner, &Cls::getOwner, NULL, DONT_SERIALIZE);
    }
  protected:
    /** Each Problem object references a HasProblem object as its owner. */
    HasProblems *owner;

    /** Each Problem contains a pointer to the next pointer for the same
      * owner. This class implements thus an intrusive single linked list
      * of Problem objects. */
    Problem *nextProblem;

    /** Adds a newly created problem to the problem container.
      * This method needs to be called in the constructor of a problem
      * subclass. It can't be called from the constructor of the base
      * Problem class, since the object isn't fully created yet and thus
      * misses the proper information used by the compare method.
      * @see removeProblem
      */
    DECLARE_EXPORT void addProblem();

    /** Removes a problem from the problem container.
      * This method needs to be called from the destructor of a problem
      * subclass.<br>
      * Due to the single linked list data structure, this methods'
      * performance is linear with the number of problems of an entity.
      * This is acceptable since we don't expect entities with a huge amount
      * of problems.
      * @see addproblem
      */
    DECLARE_EXPORT void removeProblem();

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
    DECLARE_EXPORT bool operator < (const Problem& a) const;
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
  public:
    class EntityIterator;

    /** Returns an iterator pointing to the first HasProblem object. */
    static DECLARE_EXPORT EntityIterator beginEntity();

    /** Returns an iterator pointing beyond the last HasProblem object. */
    static DECLARE_EXPORT EntityIterator endEntity();

    /** Constructor. */
    HasProblems() : firstProblem(NULL) {}

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
    Problem* firstProblem;
};


/** @brief This auxilary class is used to maintain a list of problem models. */
class Problem::List
{
  public:
    /** Constructor. */
    List() : first(NULL) {};

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
    DECLARE_EXPORT void clear(Problem * = NULL);

    /** Add a problem to the list. */
    DECLARE_EXPORT Problem* push
    (const MetaClass*, const Object*, Date, Date, double);

    /** Remove all problems from the list that appear AFTER the one
      * passed as argument. */
    DECLARE_EXPORT void pop(Problem *);

    /** Get the last problem on the list. */
    DECLARE_EXPORT Problem* top() const;

    /** Cur the list in two parts . */
    DECLARE_EXPORT Problem* unlink(Problem* p)
    {
      Problem *tmp = p->nextProblem;
      p->nextProblem = NULL;
      return tmp;
    }

    /** Returns true if the list is empty. */
    bool empty() const
    {
      return first == NULL;
    }

    typedef Problem::iterator iterator;

    /** Return an iterator to the start of the list. */
    Problem::iterator begin() const;

    /** End iterator. */
    Problem::iterator end() const;

  private:
    /** Pointer to the head of the list. */
    Problem* first;
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
    explicit DECLARE_EXPORT Solver() : loglevel(0) {}

    /** Destructor. */
    virtual DECLARE_EXPORT ~Solver() {}

    static int initialize();

    static DECLARE_EXPORT PyObject* solve(PyObject*, PyObject*);

    virtual void solve(void* = NULL) = 0;

    virtual void solve(const Demand*,void* = NULL)
    {
      throw LogicException("Called undefined solve(Demand*) method");
    }

    virtual void solve(const Operation*,void* = NULL)
    {
      throw LogicException("Called undefined solve(Operation*) method");
    }

    virtual void solve(const OperationFixedTime* o, void* v = NULL)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationTimePer* o, void* v = NULL)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationRouting* o, void* v = NULL)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationAlternate* o, void* v = NULL)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationSplit* o, void* v = NULL)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationItemSupplier* o, void* v = NULL)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const OperationItemDistribution* o, void* v = NULL)
    {
      solve(reinterpret_cast<const Operation*>(o),v);
    }

    virtual void solve(const Resource*,void* = NULL)
    {
      throw LogicException("Called undefined solve(Resource*) method");
    }

    virtual void solve(const ResourceInfinite* r, void* v = NULL)
    {
      solve(reinterpret_cast<const Resource*>(r),v);
    }

    virtual void solve(const ResourceBuckets* r, void* v = NULL)
    {
      solve(reinterpret_cast<const Resource*>(r),v);
    }

    virtual void solve(const Buffer*,void* = NULL)
    {
      throw LogicException("Called undefined solve(Buffer*) method");
    }

    virtual void solve(const BufferInfinite* b, void* v = NULL)
    {
      solve(reinterpret_cast<const Buffer*>(b),v);
    }

    virtual void solve(const BufferProcure* b, void* v = NULL)
    {
      solve(reinterpret_cast<const Buffer*>(b),v);
    }

    virtual void solve(const Load* b, void* v = NULL)
    {
      throw LogicException("Called undefined solve(Load*) method");
    }

    virtual void solve(const LoadDefault* b, void* v = NULL)
    {
      solve(reinterpret_cast<const Load*>(b),v);
    }
    virtual void solve(const Flow* b, void* v = NULL)
    {
      throw LogicException("Called undefined solve(Flow*) method");
    }

    virtual void solve(const FlowEnd* b, void* v = NULL)
    {
      solve(reinterpret_cast<const Flow*>(b),v);
    }

    virtual void solve(const FlowFixedStart* b, void* v = NULL)
    {
      solve(reinterpret_cast<const Flow*>(b),v);
    }

    virtual void solve(const FlowFixedEnd* b, void* v = NULL)
    {
      solve(reinterpret_cast<const Flow*>(b),v);
    }

    virtual void solve(const Solvable*,void* = NULL)
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
    void setLogLevel(short v)
    {
      loglevel = v;
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addShortField<Cls>(Tags::loglevel, &Cls::getLogLevel, &Cls::setLogLevel);
    }

  private:
    /** Controls the amount of tracing and debugging messages. */
    short loglevel;
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
    virtual void solve(Solver &s, void* v = NULL) const
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
    DECLARE_EXPORT void setDetectProblems(bool b);

    /** Returns whether or not this object needs to detect problems. */
    bool getDetectProblems() const
    {
      return useProblemDetection;
    }

    /** Loops through all plannable objects and updates their problems if
      * required. */
    static DECLARE_EXPORT void computeProblems();

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
    DECLARE_EXPORT Problem::iterator getProblems() const;

  private:
    /** Stores whether this entity should be skip problem detection, or not. */
    bool useProblemDetection;

    /** Stores whether this entity has been updated since the last problem
      * detection run. */
    bool changed;

    /** Marks whether any entity at all has changed its status since the last
      * problem detection round.
      */
    static DECLARE_EXPORT bool anyChange;

    /** This flag is set to true during the problem recomputation. It is
      * required to garantuee safe access to the problems in a multi-threaded
      * environment.
      */
    static DECLARE_EXPORT bool computationBusy;
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
    static DECLARE_EXPORT bool recomputeLevels;

    /** This flag is set to true during the computation of the levels. It is
      * required to ensure safe access to the level information in a
      * multi-threaded environment.
      */
    static DECLARE_EXPORT bool computationBusy;

    /** Stores the total number of clusters in the model. */
    static DECLARE_EXPORT int numberOfClusters;

    /** Stores the maximum level number in the model. */
    static DECLARE_EXPORT short numberOfLevels;

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
      m->addShortField<Cls>(Tags::level, &Cls::getLevel, NULL, 0, DONT_SERIALIZE);
      m->addIntField<Cls>(Tags::cluster, &Cls::getCluster, NULL, 0, DONT_SERIALIZE);
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
    static DECLARE_EXPORT void computeLevels();

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
    typedef Association<Location,Location,ItemDistribution>::ListA distributionoriginlist;
    typedef Association<Location,Location,ItemDistribution>::ListB distributiondestinationlist;

    /** Default constructor. */
    explicit DECLARE_EXPORT Location() : available(NULL)
    {
      initType(metadata);
    }

    /** Destructor. */
    virtual DECLARE_EXPORT ~Location();

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
    const distributionoriginlist& getDistributionOrigins() const
    {
      return origins;
    }

    /** Returns an iterator over the list of item distributions pointing to
      * this location as origin. */
    distributionoriginlist::const_iterator getDistributionOriginIterator() const
    {
      return origins.begin();
    }

    /** Returns a constant reference to the item distributions pointing to
      * this location as origin. */
    const distributiondestinationlist& getDistributionDestinations() const
    {
      return destinations;
    }

    /** Returns an iterator over the list of item distributions pointing to
      * this location as origin. */
    distributiondestinationlist::const_iterator getDistributionDestinationIterator() const
    {
      return destinations.begin();
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;
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
    Calendar* available;

    /** This is a list of item distributions pointing to this location as
      * origin.
      */
    distributionoriginlist origins;

    /** This is a list of item distributions pointing to this location as
      * destination.
      */
    distributiondestinationlist destinations;
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
    static DECLARE_EXPORT const MetaClass* metadata;
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
    explicit DECLARE_EXPORT Customer() {}

    /** Destructor. */
    virtual DECLARE_EXPORT ~Customer();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;
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
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();
};


/** @brief This abstracts class represents a supplier. */
class Supplier : public HasHierarchy<Supplier>, public HasDescription
{
  friend class ItemSupplier;
  public:
    typedef Association<Supplier,Item,ItemSupplier>::ListA itemlist;

    /** Default constructor. */
    explicit DECLARE_EXPORT Supplier() {}

    /** Destructor. */
    virtual DECLARE_EXPORT ~Supplier();

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
    static DECLARE_EXPORT const MetaCategory* metadata;
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
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();
};


/** @brief A suboperation is used in operation types which have child
  * operations.
  */
class SubOperation : public Object, public HasSource
{
  private:
    /** Pointer to the parent operation. */
    Operation* owner;

    /** Pointer to the child operation.
      * Note that the same child operation can be used in multiple parents.
      * The child operation is completely unaware of its parents.
      */
    Operation* oper;

    /** Priority index. */
    int prio;

    /** Validity date range for the child operation. */
    DateRange effective;

    /** Python constructor. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

  public:

    typedef list<SubOperation*> suboperationlist;

    /** Default constructor. */
    explicit SubOperation() : owner(NULL), oper(NULL), prio(1)
    {
      initType(metadata);
    }

    /** Destructor. */
    DECLARE_EXPORT ~SubOperation();

    Operation* getOwner() const
    {
      return owner;
    }

    DECLARE_EXPORT void setOwner(Operation*);

    Operation* getOperation() const
    {
      return oper;
    }

    DECLARE_EXPORT void setOperation(Operation*);

    int getPriority() const
    {
      return prio;
    }

    DECLARE_EXPORT void setPriority(int);

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
    static DECLARE_EXPORT const MetaCategory* metacategory;
    static DECLARE_EXPORT const MetaClass* metadata;
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
            return NULL;
          SubOperation *tmp = *cur;
          ++cur;
          return tmp;
        }
    };
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
  : public Object, public HasProblems, public NonCopyable, public HasSource
{
    friend class FlowPlan;
    friend class LoadPlan;
    friend class Demand;
    friend class Operation;
    friend class OperationSplit;
    friend class OperationAlternate;
    friend class OperationRouting;
    friend class ProblemPrecedence;

  public:
    // Forward declarations
    class iterator;
    class FlowPlanIterator;
    class LoadPlanIterator;

    // Type definitions
    typedef TimeLine<FlowPlan> flowplanlist;
    typedef TimeLine<LoadPlan> loadplanlist;

    /** Returns an iterator pointing to the first flowplan. */
    inline FlowPlanIterator beginFlowPlans() const;
    inline FlowPlanIterator getFlowPlans() const;

    /** Returns an iterator pointing beyond the last flowplan. */
    inline FlowPlanIterator endFlowPlans() const;
    inline LoadPlanIterator getLoadPlans() const;

    /** Returns how many flowplans are created on an operationplan. */
    int sizeFlowPlans() const;

    /** Returns an iterator pointing to the first loadplan. */
    LoadPlanIterator beginLoadPlans() const;

    /** Returns an iterator pointing beyond the last loadplan. */
    LoadPlanIterator endLoadPlans() const;

    /** Returns how many loadplans are created on an operationplan. */
    int sizeLoadPlans() const;

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
    DECLARE_EXPORT double getCriticality() const;

    friend class iterator;

    /** This is a factory method that creates an operationplan pointer based
      * on the operation and id. */
    static DECLARE_EXPORT Object* createOperationPlan(const MetaClass*, const DataValueDict&);

    /** Destructor. */
    virtual DECLARE_EXPORT ~OperationPlan();

    virtual DECLARE_EXPORT void setChanged(bool b = true);

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
      * If the operationplan isn't a delivery, this is a NULL pointer.
      */
    Demand* getDemand() const
    {
      return dmd;
    }

    /** Updates the demand to which this operationplan is a solution. */
    DECLARE_EXPORT void setDemand(Demand* l);

    /** Calculate the penalty of an operationplan.<br>
      * It is the sum of all setup penalties of the resources it loads. */
    DECLARE_EXPORT double getPenalty() const;

    /** Calculate the unavailable time during the operationplan. The regular
      * duration is extended with this amount.
      */
    DECLARE_EXPORT Duration getUnavailable() const;

    /** Return the status of the operationplan.
      * The status string is one of the following:
      *   - proposed
      *   - approved
      *   - confirmed
      */
    DECLARE_EXPORT string getStatus() const;

    /** Return the status of the operationplan. */
    DECLARE_EXPORT void setStatus(const string&);

    /** Returns whether the operationplan is locked, ie the status is APPROVED
      * or confirmed. A locked operationplan is never changed.
      */
    bool getLocked() const
    {
      return (flags & (STATUS_CONFIRMED + STATUS_APPROVED)) != 0;
    }

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
    static DECLARE_EXPORT void deleteOperationPlans(Operation* o, bool deleteLocked=false);

    /** Deprecated method. Use the setStatus method instead. */
    inline void setLocked(bool b)
    {
      setConfirmed(b);
    }

    /** Update the status to CONFIRMED, or back to PROPOSED. */
    virtual DECLARE_EXPORT void setConfirmed(bool b);

    /** Update the status to APPROVED, or back to PROPOSED. */
    virtual DECLARE_EXPORT void setApproved(bool b);

    /** Update the status to PROPOSED, or back to APPROVED. */
    virtual DECLARE_EXPORT void setProposed(bool b);

    /** Update flag which allow/disallows material consumption. */
    void setConsumeMaterial(bool b)
    {
      if (b)
        flags &= ~CONSUME_MATERIAL;
      else
        flags |= CONSUME_MATERIAL;
    }

    /** Update flag which allow/disallows material production. */
    void setProduceMaterial(bool b)
    {
      if (b)
        flags &= ~PRODUCE_MATERIAL;
      else
        flags |= PRODUCE_MATERIAL;
    }

    /** Update flag which allow/disallows capacity consumption. */
    void setConsumeCapacity(bool b)
    {
      if (b)
        flags &= ~CONSUME_CAPACITY;
      else
        flags |= CONSUME_CAPACITY;
    }

    /** Returns a pointer to the operation being instantiated. */
    Operation* getOperation() const
    {
      return oper;
    }

    /** Update the operation of an operationplan.<br>
      * This method can only be called once for each operationplan.
      */
    void setOperation(Operation* o)
    {
      if (oper == o)
        return;
      if (oper)
        throw DataException("Can't update operation of initialized operationplan");
      oper = o;
      activate();
    }

    /** Fixes the start and end date of an operationplan. Note that this
      * overrules the standard duration given on the operation, i.e. no logic
      * kicks in to verify the data makes sense. This is up to the user to
      * take care of.<br>
      * The methods setStart(Date) and setEnd(Date) are therefore preferred
      * since they properly apply all appropriate logic.
      */
    void setStartAndEnd(Date st, Date nd)
    {
      dates.setStartAndEnd(st,nd);
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
    void DECLARE_EXPORT setOwner(OperationPlan* o, bool);

    void setOwner(OperationPlan* o)
    {
      setOwner(o, true);
    }

    /** Returns a pointer to the operationplan for which this operationplan
      * a sub-operationplan.<br>
      * The method returns NULL if there is no owner defined.<br>
      * E.g. Sub-operationplans of a routing refer to the overall routing
      * operationplan.<br>
      * E.g. An alternate sub-operationplan refers to its parent.
      * @see getTopOwner
      */
    OperationPlan* getOwner() const
    {
      return owner;
    }

    /** Returns a pointer to the operationplan owning a set of
      * sub-operationplans. There can be multiple levels of suboperations.<br>
      * If no owner exists the method returns the current operationplan.
      * @see getOwner
      */
    inline const OperationPlan* getTopOwner() const
    {
      return const_cast<OperationPlan*>(this)->getTopOwner();
    }

    /** Returns a pointer to the operationplan owning a set of
      * sub-operationplans. There can be multiple levels of suboperations.<br>
      * If no owner exists the method returns the current operationplan.
      * @see getOwner
      */
    OperationPlan* getTopOwner()
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
        return this;
    }

    /** Returns the start and end date of this operationplan. */
    const DateRange & getDates() const
    {
      return dates;
    }

    /** Return true if the operationplan is redundant, ie all material
      * it produces is not used at all.<br>
      * If the optional argument is false (which is the default value), we
      * check with the minimum stock level of the buffers. If the argument
      * is true, we check with 0.
      */
    DECLARE_EXPORT bool isExcess(bool = false) const;

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
    DECLARE_EXPORT unsigned long getIdentifier() const
    {
      if (id==ULONG_MAX)
        const_cast<OperationPlan*>(this)->assignIdentifier(); // Lazy generation
      return id;
    }

    void setIdentifier(unsigned long i)
    {
      id = i;
      assignIdentifier();
    }

    /** Return the identifier. This method can return the lazy identifier 1. */
    unsigned long getRawIdentifier() const
    {
      return id;
    }

    /** Return the external identifier. */
    string getReference() const
    {
      return ref;
    }

    /** Update the external identifier. */
    DECLARE_EXPORT void setReference(const string& s)
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
    virtual DECLARE_EXPORT void setEnd(Date);

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
    virtual DECLARE_EXPORT void setStart(Date);

    static int initialize();

    PyObject* str() const
    {
      ostringstream ch;
      ch << id;
      return PythonData(ch.str());
    }

    /** Python factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

    /** Initialize the operationplan. The initialization function should be
      * called when the operationplan is ready to be 'officially' added. The
      * initialization performs the following actions:
      * <ol>
      * <li> assign an identifier</li>
      * <li> create the flow and loadplans if these hadn't been created
      * before</li>
      * <li> add the operationplan to the global list of operationplans</li>
      * <li> create a link with a demand object if this is a delivery
      * operationplan</li>
      * </ol>
      * Every operationplan subclass that has sub-operations will normally
      * need to create an override of this function.<br>
      *
      * The return value indicates whether the initialization was successfull.
      * If the operationplan is invalid, it will be DELETED and the return value
      * is 'false'.
      */
    DECLARE_EXPORT bool activate();

    /** Remove an operationplan from the list of officially registered ones.<br>
      * The operationplan will keep its loadplans and flowplans after unregistration.
      */
    DECLARE_EXPORT void deactivate();

    /** This method links the operationplan in the list of all operationplans
      * maintained on the operation.<br>
      * In most cases calling this method is not required since it included
      * in the activate method. In exceptional cases the solver already
      * needs to see uncommitted operationplans in the list - eg for the
      * procurement buffer.
      * @see activate
      */
    DECLARE_EXPORT void insertInOperationplanList();

    /** This method remove the operationplan from the list of all operationplans
      * maintained on the operation.<br>
      * @see deactivate
      */
    DECLARE_EXPORT void removeFromOperationplanList();

    /** Maintain the operationplan list in sorted order. */
    DECLARE_EXPORT void updateOperationplanList();

    /** Remove a sub-operation_plan from the list. */
    virtual DECLARE_EXPORT void eraseSubOperationPlan(OperationPlan*);

    /** This function is used to create the loadplans, flowplans and
      * setup operationplans.
      */
    DECLARE_EXPORT void createFlowLoads();

    /** This function is used to delete the loadplans, flowplans and
      * setup operationplans.
      */
    DECLARE_EXPORT void deleteFlowLoads();

    inline bool getHidden() const;

    /** Searches for an OperationPlan with a given identifier.<br>
      * Returns a NULL pointer if no such OperationPlan can be found.<br>
      * The method is of complexity O(n), i.e. involves a LINEAR search through
      * the existing operationplans, and can thus be quite slow in big models.<br>
      * The method is O(1), i.e. constant time regardless of the model size,
      * when the parameter passed is bigger than the operationplan counter.
      */
    static DECLARE_EXPORT OperationPlan* findId(unsigned long l);

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

    static DECLARE_EXPORT const MetaClass* metadata;

    static DECLARE_EXPORT const MetaCategory* metacategory;

    /** Lookup a operationplan. */
    static DECLARE_EXPORT Object* finder(const DataValueDict&);

    /** Comparison of 2 OperationPlans.
      * To garantuee that the problems are sorted in a consistent and stable
      * way, the following sorting criteria are used (in order of priority):
      * <ol><li>Operation</li>
      * <li>Start date (earliest dates first)</li>
      * <li>Quantity (biggest quantities first)</li></ol>
      * Multiple operationplans for the same values of the above keys can exist.
      */
    DECLARE_EXPORT bool operator < (const OperationPlan& a) const;

    /** Copy constructor.<br>
      * If the optional argument is false, the new copy is not initialized
      * and won't have flowplans and loadplans.
      */
    DECLARE_EXPORT OperationPlan(const OperationPlan&, bool = true);

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

    DECLARE_EXPORT PeggingIterator getPeggingDownstream() const;

    DECLARE_EXPORT PeggingIterator getPeggingUpstream() const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addUnsignedLongField<Cls>(Tags::id, &Cls::getIdentifier, &Cls::setIdentifier, 0, MANDATORY);
      m->addStringField<Cls>(Tags::reference, &Cls::getReference, &Cls::setReference);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation);
      m->addPointerField<Cls, Demand>(Tags::demand, &Cls::getDemand, &Cls::setDemand);
      m->addDateField<Cls>(Tags::start, &Cls::getStart, &Cls::setStart, Date::infiniteFuture);
      m->addDateField<Cls>(Tags::end, &Cls::getEnd, &Cls::setEnd, Date::infiniteFuture);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity);
      // Default of -999 to enforce serializing the value if it is 0
      m->addDoubleField<Cls>(Tags::criticality, &Cls::getCriticality, NULL, -999, PLAN + DETAIL);
      m->addStringField<Cls>(Tags::status, &Cls::getStatus, &Cls::setStatus, "proposed");
      m->addBoolField<Cls>(Tags::locked, &Cls::getLocked, &Cls::setLocked, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::approved, &Cls::getApproved, &Cls::setApproved, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::proposed, &Cls::getProposed, &Cls::setProposed, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::confirmed, &Cls::getConfirmed, &Cls::setConfirmed, BOOL_FALSE, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::consume_material, &Cls::getConsumeMaterial, &Cls::setConsumeMaterial, BOOL_TRUE);
      m->addBoolField<Cls>(Tags::produce_material, &Cls::getProduceMaterial, &Cls::setProduceMaterial, BOOL_TRUE);
      m->addBoolField<Cls>(Tags::consume_capacity, &Cls::getConsumeCapacity, &Cls::setConsumeCapacity, BOOL_TRUE);
      HasSource::registerFields<Cls>(m);
      m->addPointerField<Cls, OperationPlan>(Tags::owner, &Cls::getOwner, &Cls::setOwner);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addDurationField<Cls>(Tags::unavailable, &Cls::getUnavailable, NULL, 0L, DONT_SERIALIZE);
      m->addIteratorField<Cls, OperationPlan::FlowPlanIterator, FlowPlan>(Tags::flowplans, Tags::flowplan, &Cls::getFlowPlans, DONT_SERIALIZE);
      m->addIteratorField<Cls, OperationPlan::LoadPlanIterator, LoadPlan>(Tags::loadplans, Tags::loadplan, &Cls::getLoadPlans, DONT_SERIALIZE);
      m->addIteratorField<Cls, PeggingIterator, PeggingIterator>(Tags::pegging_downstream, Tags::pegging, &Cls::getPeggingDownstream, DONT_SERIALIZE);
      m->addIteratorField<Cls, PeggingIterator, PeggingIterator>(Tags::pegging_upstream, Tags::pegging, &Cls::getPeggingUpstream, DONT_SERIALIZE);
      m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getSubOperationPlans, DONT_SERIALIZE);
    }

    DECLARE_EXPORT static PyObject* createIterator(PyObject* self, PyObject* args);

  private:
    /** Private copy constructor.<br>
      * It is used in the public copy constructor to make a deep clone of suboperationplans.
      * @see OperationPlan(const OperationPlan&, bool = true)
      */
    DECLARE_EXPORT OperationPlan(const OperationPlan&, OperationPlan*);

    /** Updates the operationplan based on the latest information of quantity,
      * date and locked flag.<br>
      * This method will also update parent and child operationplans.
      * @see resizeFlowLoadPlans
      */
    virtual DECLARE_EXPORT void update();

    /** Generates a unique identifier for the operationplan. */
    DECLARE_EXPORT bool assignIdentifier();

    /** Recursive auxilary function for getTotalFlow.
      * @ see getTotalFlow
      */
    DECLARE_EXPORT double getTotalFlowAux(const Buffer*) const;

    /** Update the loadplans and flowplans of the operationplan based on the
      * latest information of quantity, date and locked flag.<br>
      * This method will NOT update parent or child operationplans.
      * @see update
      */
    DECLARE_EXPORT void resizeFlowLoadPlans();

    /** Default constructor.<br>
      * This way of creating operationplan objects is not intended for use by
      * any client applications. Client applications should use the factory
      * method on the operation class instead.<br>
      * Subclasses of the Operation class may use this constructor in their
      * own override of the createOperationPlan method.
      * @see Operation::createOperationPlan
      */
    OperationPlan() : owner(NULL), quantity(0.0), flags(0), dmd(NULL),
      id(0), oper(NULL), firstflowplan(NULL), firstloadplan(NULL),
      prev(NULL), next(NULL), firstsubopplan(NULL), lastsubopplan(NULL),
      nextsubopplan(NULL), prevsubopplan(NULL)
    {
      initType(metadata);
    }

  private:
    static const short STATUS_APPROVED = 1;
    static const short STATUS_CONFIRMED = 2;
    static const short IS_SETUP = 4;
    static const short HAS_SETUP = 8;
    static const short CONSUME_MATERIAL = 16;
    static const short PRODUCE_MATERIAL = 32;
    static const short CONSUME_CAPACITY = 64;

    /** Pointer to a higher level OperationPlan. */
    OperationPlan *owner;

    /** Quantity. */
    double quantity;

    /** Is this operationplan locked? A locked operationplan doesn't accept
      * any changes. This field is only relevant for top-operationplans. */
    short flags;

    /** Counter of OperationPlans, which is used to automatically assign a
      * unique identifier for each operationplan.<br>
      * The value of the counter is the first available identifier value that
      * can be used for a new operationplan.<br>
      * The first value is 1, and each operationplan increases it by 1.
      * @see assignIdentifier()
      */
    static DECLARE_EXPORT unsigned long counterMin;

    /** Pointer to the demand.<br>
      * Only delivery operationplans have this field set. The field is NULL
      * for all other operationplans.
      */
    Demand *dmd;

    /** Unique identifier.<br>
      * The field is 0 while the operationplan is not fully registered yet.
      * The field is 1 when the operationplan is fully registered but only a
      * temporary id is generated.
      * A unique value for each operationplan is created lazily when the
      * method getIdentifier() is called.
      */
    unsigned long id;

    /** External identifier for this operationplan. */
    string ref;

    /** Start and end date. */
    DateRange dates;

    /** Pointer to the operation. */
    Operation *oper;

    /** Root of a single linked list of flowplans. */
    FlowPlan* firstflowplan;

    /** Single linked list of loadplans. */
    LoadPlan* firstloadplan;

    /** Pointer to the previous operationplan.<br>
      * Operationplans are chained in a doubly linked list for each operation.
      * @see next
      */
    OperationPlan* prev;

    /** Pointer to the next operationplan.<br>
      * Operationplans are chained in a doubly linked list for each operation.
      * @see prev
      */
    OperationPlan* next;

    /** Pointer to the first suboperationplan of this operationplan. */
    OperationPlan* firstsubopplan;

    /** Pointer to the last suboperationplan of this operationplan. */
    OperationPlan* lastsubopplan;

    /** Pointer to the next suboperationplan of the parent operationplan. */
    OperationPlan* nextsubopplan;

    /** Pointer to the previous suboperationplan of the parent operationplan. */
    OperationPlan* prevsubopplan;
};


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

  protected:
    /** Extra logic called when instantiating an operationplan.<br>
      * When the function returns false the creation of the operationplan
      * is denied and it is deleted.
      */
    virtual bool extraInstantiate(OperationPlan* o)
    {
      return true;
    }

  public:
    /** Default constructor. */
    explicit DECLARE_EXPORT Operation() :
      loc(NULL), size_minimum(1.0), size_minimum_calendar(NULL),
      size_multiple(0.0), size_maximum(DBL_MAX), cost(0.0), hidden(false),
      first_opplan(NULL), last_opplan(NULL)
      {}

    /** Destructor. */
    virtual DECLARE_EXPORT ~Operation();

    /** Returns a pointer to the operationplan being instantiated. */
    OperationPlan* getFirstOpPlan() const
    {
      return first_opplan;
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
    DECLARE_EXPORT OperationPlan* createOperationPlan(double, Date,
        Date, Demand* = NULL, OperationPlan* = NULL, unsigned long = 0,
        bool makeflowsloads=true) const;

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
      * - the availability calendar of the operation's location
      * - the availability calendar of all resources loaded by the operation @todo not implemented yet
      * - the availability calendar of the locations of all resources loaded @todo not implemented yet
      *   by the operation
      *
      * @param[in] thedate  The date from which to start searching.
      * @param[in] duration The amount of available time we are looking for.
      * @param[in] forward  The search direction
      * @param[out] actualduration This variable is updated with the actual
      *             amount of available time found.
      */
    DECLARE_EXPORT DateRange calculateOperationTime
    (Date thedate, Duration duration, bool forward,
     Duration* actualduration = NULL) const;

    /** Calculates the effective, available time between two dates.
      *
      * This calculation considers the availability calendars of:
      * - the availability calendar of the operation's location
      * - the availability calendar of all resources loaded by the operation @todo not implemented yet
      * - the availability calendar of the locations of all resources loaded @todo not implemented yet
      *   by the operation
      *
      * @param[in] start  The date from which to start searching.
      * @param[in] end    The date where to stop searching.
      * @param[out] actualduration This variable is updated with the actual
      *             amount of available time found.
      */
    DECLARE_EXPORT DateRange calculateOperationTime
    (Date start, Date end, Duration* actualduration = NULL) const;

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
    virtual OperationPlanState setOperationPlanParameters
    (OperationPlan*, double, Date, Date, bool=true, bool=true) const = 0;

    /** Updates the quantity of an operationplan.<br>
      * This method considers the lot size constraints and also propagates
      * the new quantity to child operationplans.
      */
    virtual DECLARE_EXPORT double setOperationPlanQuantity(
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

    DECLARE_EXPORT OperationPlan::iterator getOperationPlans() const;

    /** Return the flow that is associates a given buffer with this
      * operation. Returns NULL is no such flow exists. */
    Flow* findFlow(const Buffer* b, Date d) const
    {
      return flowdata.find(b,d);
    }

    /** Return the load that is associates a given resource with this
      * operation. Returns NULL is no such load exists. */
    Load* findLoad(const Resource* r, Date d) const
    {
      return loaddata.find(r,d);
    }

    /** Deletes all operationplans of this operation. The boolean parameter
      * controls whether we delete also locked operationplans or not.
      */
    DECLARE_EXPORT void deleteOperationPlans(bool deleteLockedOpplans = false);

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

    /** Add a new child operationplan.
      * By default an operationplan can have only a single suboperation,
      * representing a changeover.
      * Operation subclasses can implement their own restrictions on the
      * number and structure of the suboperationplans.
      * @see OperationAlternate::addSubOperationPlan
      * @see OperationRouting::addSubOperationPlan
      * @see OperationSplit::addSubOperationPlan
      */
    virtual DECLARE_EXPORT void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool=true
      );

    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const
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

    /** Register a super-operation, i.e. an operation having this one as a
      * sub-operation. */
    DECLARE_EXPORT void addSuperOperation(Operation * o)
    {
      superoplist.push_front(o);
    }

    /** Removes a super-operation from the list. */
    DECLARE_EXPORT void removeSuperOperation(Operation*);

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

    virtual DECLARE_EXPORT void updateProblems();

    void setHidden(bool b)
    {
      if (hidden!=b) setChanged();
      hidden = b;
    }

    bool getHidden() const
    {
      return hidden;
    }

    static DECLARE_EXPORT const MetaCategory* metadata;

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
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans, PLAN + DETAIL);
      m->addIteratorField<Cls, loadlist::const_iterator, Load>(Tags::loads, Tags::load, &Cls::getLoadIterator, BASE + WRITE_FULL);
      m->addIteratorField<Cls, flowlist::const_iterator, Flow>(Tags::flows, Tags::flow, &Cls::getFlowIterator, BASE + WRITE_FULL);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasLevel::registerFields<Cls>(m);
    }

  protected:
    DECLARE_EXPORT void initOperationPlan(OperationPlan*, double,
        const Date&, const Date&, Demand*, OperationPlan*, unsigned long,
        bool = true) const;

  private:
    /** List of operations using this operation as a sub-operation */
    list<Operation*> superoplist;

    /** Empty list of operations.<br>
      * For operation types which have no suboperations this list is
      * used as the list of suboperations.
      */
    static DECLARE_EXPORT Operationlist nosubOperations;

    /** Location of the operation.<br>
      * The location is used to model the working hours and holidays.
      */
    Location* loc;

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

    /** Minimum size for operationplans.<br>
      * The default value is 1.0
      */
    double size_minimum;

    /** Minimum size for operationplans when this size varies over time.
      * If this field is specified, the size_minimum field is ignored.
      */
    Calendar *size_minimum_calendar;

    /** Multiple size for operationplans. */
    double size_multiple;

    /** Maximum size for operationplans. */
    double size_maximum;

    /** Cost of the operation.<br>
      * The default value is 0.0.
      */
    double cost;

    /** Does the operation require serialization or not. */
    bool hidden;

    /** A pointer to the first operationplan of this operation.<br>
      * All operationplans of this operation are stored in a sorted
      * doubly linked list.
      */
    OperationPlan* first_opplan;

    /** A pointer to the last operationplan of this operation.<br>
      * All operationplans of this operation are stored in a sorted
      * doubly linked list.
      */
    OperationPlan* last_opplan;
};


inline double OperationPlan::setQuantity(double f, bool roundDown,
  bool update, bool execute, Date end)
{
  return oper ?
    oper->setOperationPlanQuantity(this, f, roundDown, update, execute, end) :
    f;
}


Plannable* OperationPlan::getEntity() const
{
  return oper;
}


inline bool OperationPlan::getHidden() const
{
  return getOperation()->getHidden();
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
    iterator(const Operation* x) : op(Operation::end()), mode(1)
    {
      opplan = x ? x->getFirstOpPlan() : NULL;
    }

    /** Constructor. The iterator will loop only over the suboperationplans
      * of the operationplan passed. */
    iterator(const OperationPlan* x) : op(Operation::end()), mode(2)
    {
      opplan = x ? x->firstsubopplan : NULL;
    }

    /** Constructor. The iterator will loop over all operationplans. */
    iterator() : op(Operation::begin()), mode(3)
    {
      // The while loop is required since the first operation might not
      // have any operationplans at all
      while (op!=Operation::end() && !op->getFirstOpPlan()) ++op;
      if (op!=Operation::end())
        opplan = op->getFirstOpPlan();
      else
        opplan = NULL;
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
        else
          opplan = opplan->next;
      }
      // Move to a new operation
      if (!opplan && mode == 3)
      {
        do ++op;
        while (op!=Operation::end() && (!op->getFirstOpPlan()));
        if (op!=Operation::end())
          opplan = op->getFirstOpPlan();
        else
          opplan = NULL;
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
      else
        opplan = opplan->next;
      // Move to a new operation
      if (!opplan && mode==3)
      {
        do ++op; while (op!=Operation::end() && !op->getFirstOpPlan());
        if (op!=Operation::end())
          opplan = op->getFirstOpPlan();
        else
          opplan = NULL;
      }
      return tmp;
    }

    /** Return current elemetn and advance the iterator. */
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
      */
    short mode;
};


inline OperationPlan::iterator OperationPlan::end()
{
  return iterator(static_cast<Operation*>(NULL));
}


inline OperationPlan::iterator OperationPlan::begin()
{
  return iterator();
}


inline OperationPlan::iterator OperationPlan::getSubOperationPlans() const
{
  return OperationPlan::iterator(this);
}


/** @brief A simple class to easily remember the date, quantity and owner of
  * an operationplan. */
class OperationPlanState  // @todo should also be able to remember and restore suboperationplans!!!
{
  public:
    Date start;
    Date end;
    double quantity;

    /** Default constructor. */
    OperationPlanState() : quantity(0.0) {}

    /** Constructor. */
    OperationPlanState(const OperationPlan* x)
    {
      if (!x)
      {
        quantity = 0.0;
        return;
      }
      else
      {
        start = x->getDates().getStart();
        end = x->getDates().getEnd();
        quantity = x->getQuantity();
      }
    }

    /** Constructor. */
    OperationPlanState(const Date x, const Date y, double q)
      : start(x), end(y), quantity(q) {}

    /** Constructor. */
    OperationPlanState(const DateRange& x, double q)
      : start(x.getStart()), end(x.getEnd()), quantity(q) {}
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

    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

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
    DECLARE_EXPORT OperationPlanState setOperationPlanParameters
    (OperationPlan*, double, Date, Date, bool=true, bool=true) const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDurationField<Cls>(Tags::duration, &Cls::getDuration, &Cls::setDuration);
    }
  protected:
    DECLARE_EXPORT virtual bool extraInstantiate(OperationPlan* o);

  private:
    /** Stores the lengh of the Operation. */
    Duration duration;
};


/** @brief Models an operation to convert a setup on a resource. */
class OperationSetup : public Operation
{
  public:
    /** Default constructor. */
    explicit OperationSetup()
    {
      initType(metadata);
      setHidden(true);
    }

    // Never write the setup operation
    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const
    {
      s.solve(this,v);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - The duration is calculated based on the conversion type.
      */
    DECLARE_EXPORT OperationPlanState setOperationPlanParameters
    (OperationPlan*, double, Date, Date, bool=true, bool=true) const;

    /** A pointer to the operation that is instantiated for all conversions. */
    static DECLARE_EXPORT Operation* setupoperation;
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

    /** Sets a calendar to defining the minimum size of operationplans.
      * It overrides the method defined at the base class by printing an
      * additional warning.
      */
    virtual void setSizeMinimumCalendar(Calendar *c)
    {
      logger << "Warning: using a minimum size calendar on an operation of "
         << "type timeper is tricky. Planning results can be incorrect "
         << "around changes of the minimum size." << endl;
      Operation::setSizeMinimumCalendar(c);
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
    DECLARE_EXPORT OperationPlanState setOperationPlanParameters
    (OperationPlan*, double, Date, Date, bool=true, bool=true) const;

    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

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
    DECLARE_EXPORT ~OperationRouting();

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
    DECLARE_EXPORT OperationPlanState setOperationPlanParameters
    (OperationPlan*, double, Date, Date, bool=true, bool=true) const;

    DECLARE_EXPORT double setOperationPlanQuantity(
      OperationPlan* oplan, double f, bool roundDown, bool upd,
      bool execute, Date end
      ) const;

    /** Add a new child operationplan.
      * A routing operationplan has a series of suboperationplans:
      *   - A setup operationplan if the routing operation loads a resource
      *     which requires a specific setup.
      *   - A number of unlocked operationplans (one for each step in the
      *     routing) representing production not yet started.
      *   - A number of locked operationplan (one for each step in the routing)
      *     representing production which is already started or finished.
      * The sum of the quantity of the locked and unlocked operationplans of
      * each step should be equal to the quantity of top routing operationplan.<br>
      * The fast insert does insertion at the front of the unlocked operationplans.
      */
    virtual DECLARE_EXPORT void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool = true
      );

    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Return a list of all sub-operations. */
    virtual Operationlist& getSubOperations() const
    {
      return const_cast<Operationlist&>(steps);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator, BASE + WRITE_FULL);
    }

  protected:
    /** Extra logic to be used when instantiating an operationplan. */
    virtual DECLARE_EXPORT bool extraInstantiate(OperationPlan* o);

  private:
    /** Stores a double linked list of all step suboperations. */
    Operationlist steps;
};


inline void OperationPlan::restore(const OperationPlanState& x)
{
  getOperation()->setOperationPlanParameters(this, x.quantity, x.start, x.end, true);
  if (quantity != x.quantity) quantity = x.quantity;
  assert(dates.getStart() == x.start || x.start!=x.end);
  assert(dates.getEnd() == x.end || x.start!=x.end);
}


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
DECLARE_EXPORT SearchMode decodeSearchMode(const string& c);


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
    DECLARE_EXPORT ~OperationSplit();

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
    DECLARE_EXPORT OperationPlanState setOperationPlanParameters
    (OperationPlan*, double, Date, Date, bool=true, bool=true) const;

    /** Add a new child operationplan.
      * An alternate operationplan plan can have a maximum of 2
      * suboperationplans:
      *  - A setup operationplan if the alternate top-operation loads a
      *    resource requiring a specific setup.
      *  - An operationplan of any of the allowed suboperations.
      */
    virtual DECLARE_EXPORT void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool=true
      );

    virtual void solve(Solver &s, void* v = NULL) const
    {
      s.solve(this,v);
    }

    virtual Operationlist& getSubOperations() const
    {
      return const_cast<Operationlist&>(alternates);
    }

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator, BASE + WRITE_FULL);
    }

  protected:
    /** Extra logic to be used when instantiating an operationplan. */
    virtual DECLARE_EXPORT bool extraInstantiate(OperationPlan* o);

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
    explicit DECLARE_EXPORT OperationAlternate() : search(PRIORITY)
    {
      initType(metadata);
    }

    /** Destructor. */
    DECLARE_EXPORT ~OperationAlternate();

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

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - Very simple, call the method with the same name on the alternate
      *    suboperationplan.
      * @see Operation::setOperationPlanParameters
      */
    DECLARE_EXPORT OperationPlanState setOperationPlanParameters
    (OperationPlan*, double, Date, Date, bool=true, bool=true) const;

    /** Add a new child operationplan.
      * An alternate operationplan plan can have a maximum of 2
      * suboperationplans:
      *  - A setup operationplan if the alternate top-operation loads a
      *    resource requiring a specific setup.
      *  - An operationplan of any of the allowed suboperations.
      */
    virtual DECLARE_EXPORT void addSubOperationPlan(
      OperationPlan*, OperationPlan*, bool=true
      );

    virtual void solve(Solver &s, void* v = NULL) const
    {
      s.solve(this,v);
    }

    virtual Operationlist& getSubOperations() const
    {
      return const_cast<Operationlist&>(alternates);
    }

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch, &Cls::setSearch, PRIORITY);
      m->addIteratorField<Cls, SubOperation::iterator, SubOperation>(Tags::suboperations, Tags::suboperation, &Cls::getSubOperationIterator, BASE + WRITE_FULL);
    }

  protected:
    /** Extra logic to be used when instantiating an operationplan. */
    virtual DECLARE_EXPORT bool extraInstantiate(OperationPlan* o);

  private:
    /** List of all alternate operations. */
    Operationlist alternates;

    /** Mode to select the preferred alternates. */
    SearchMode search;
};


/** @brief This class holds the definition of distribution replenishments. */
class ItemDistribution : public Object,
  public Association<Location,Location,ItemDistribution>::Node, public HasSource
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
          curOper = i ? i->firstOperation : NULL;
        }

        /** Return current value and advance the iterator. */
        inline OperationItemDistribution* next();
    };

    /** Factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

    /** Constructor. */
    explicit DECLARE_EXPORT ItemDistribution();

    /** Destructor. */
    virtual DECLARE_EXPORT ~ItemDistribution();

    /** Search an existing object. */
    DECLARE_EXPORT static Object* finder(const DataValueDict& k);

    /** Remove all shipping operationplans. */
    DECLARE_EXPORT void deleteOperationPlans(bool deleteLockedOpplans = false);

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
    static DECLARE_EXPORT const MetaCategory* metacategory;

    /** Returns the item. */
    Item* getItem() const
    {
      return it;
    }

    /** Update the item. */
    DECLARE_EXPORT void setItem(Item*);

    /** Returns the origin location. */
    Location* getOrigin() const
    {
      return getPtrA();
    }

    /** Returns the destination location. */
    Location* getDestination() const
    {
      return getPtrB();
    }

    /** Updates the origin Location. This method can only be called once on each instance. */
    void setOrigin(Location* s)
    {
      if (s)
        setPtrA(s, s->getDistributionOrigins());
      HasLevel::triggerLazyRecomputation();
    }

    /** Updates the destination location. This method can only be called once on each instance. */
    void setDestination(Location* i)
    {
      if (i)
        setPtrB(i, i->getDistributionDestinations());
      HasLevel::triggerLazyRecomputation();
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

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, MANDATORY + PARENT);
      m->addPointerField<Cls, Location>(Tags::origin, &Cls::getOrigin, &Cls::setOrigin);
      m->addPointerField<Cls, Location>(Tags::destination, &Cls::getDestination, &Cls::setDestination, BASE + PARENT);
      m->addDurationField<Cls>(Tags::leadtime, &Cls::getLeadTime, &Cls::setLeadTime);
      m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum, &Cls::setSizeMinimum, 1.0);
      m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple, &Cls::setSizeMultiple);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      m->addIteratorField<Cls, OperationIterator, OperationItemDistribution>(Tags::operations, Tags::operation, &Cls::getOperations, DONT_SERIALIZE);
      HasSource::registerFields<Cls>(m);
    }

  private:
    /** Item being distributed. */
    Item* it;

    /** Shipping lead time. */
    Duration leadtime;

    /** Minimum procurement quantity. */
    double size_minimum;

    /** Procurement multiple quantity. */
    double size_multiple;

    /** Procurement cost. */
    double cost;

    /** Pointer to the head of the auto-generated shipping operation list.*/
    OperationItemDistribution* firstOperation;

    /** Pointer to the next ItemDistribution for the same item. */
    ItemDistribution* next;
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

  public:
    class bufferIterator;
    friend class bufferIterator;

    typedef Association<Supplier,Item,ItemSupplier>::ListB supplierlist;

    /** Default constructor. */
    explicit DECLARE_EXPORT Item() : deliveryOperation(NULL), price(0.0),
      firstItemDistribution(NULL), firstItemBuffer(NULL) {}

    /** Returns the delivery operation.<br>
      * This field is inherited from a parent item, if it hasn't been
      * specified.
      */
    Operation* getOperation() const
    {
      // Current item has a non-empty deliveryOperation field
      if (deliveryOperation)
        return deliveryOperation;

      // Look for a non-empty deliveryOperation field on owners
      for (Item* i = getOwner(); i; i = i->getOwner())
        if (i->deliveryOperation)
          return i->deliveryOperation;

      // The field is not specified on the item or any of its parents.
      return NULL;
    }

    /** Updates the delivery operation.<br>
      * If some demands have already been planned using the old delivery
      * operation they are left untouched and won't be replanned.
      */
    void setOperation(Operation* o)
    {
      deliveryOperation = o;
    }

    /** Return the selling price of the item.<br>
      * The default value is 0.0.
      */
    double getPrice() const
    {
      return price;
    }

    /** Update the selling price of the item. */
    void setPrice(const double c)
    {
      if (c >= 0)
        price = c;
      else
        throw DataException("Item price must be positive");
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

    /** Nested class to iterate of ItemDistribution objects of this item. */
    class distributionIterator
    {
      private:
        ItemDistribution* cur;

      public:
        /** Constructor. */
        distributionIterator(const Item *c)
        {
          cur = c ? c->firstItemDistribution : NULL;
        }

        /** Return current value and advance the iterator. */
        ItemDistribution* next()
        {
          ItemDistribution* tmp = cur;
          if (cur)
            cur = cur->next;
          return tmp;
        }
    };

    distributionIterator getDistributionIterator() const
    {
      return this;
    }

    inline bufferIterator getBufferIterator() const;

    static int initialize();

    /** Destructor. */
    virtual DECLARE_EXPORT ~Item();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::price, &Cls::getPrice, &Cls::setPrice, 0);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addIteratorField<Cls, supplierlist::const_iterator, ItemSupplier>(Tags::itemsuppliers, Tags::itemsupplier, &Cls::getSupplierIterator, BASE + WRITE_FULL);
      m->addIteratorField<Cls, distributionIterator, ItemDistribution>(Tags::itemdistributions, Tags::itemdistribution, &Cls::getDistributionIterator, BASE + WRITE_FULL);
      m->addIteratorField<Cls, bufferIterator, Buffer>(Tags::buffers, Tags::buffer, &Cls::getBufferIterator, DONT_SERIALIZE);
    }

  private:
    /** This is the operation used to satisfy a demand for this item.
      * @see Demand
      */
    Operation* deliveryOperation;

    /** Selling price of the item. */
    double price;

    /** This is a list of suppliers this item has. */
    supplierlist suppliers;

    /** Maintain a list of ItemDistributions. */
    ItemDistribution *firstItemDistribution;

    /** Maintain a list of buffers. */
    Buffer *firstItemBuffer;
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
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();
};


/** @brief This class represents an item that can be purchased from a supplier. */
class ItemSupplier : public Object,
  public Association<Supplier,Item,ItemSupplier>::Node, public HasSource
{
  friend class OperationItemSupplier;
  public:
    /** Default constructor. */
    explicit DECLARE_EXPORT ItemSupplier();

    /** Constructor. */
    explicit DECLARE_EXPORT ItemSupplier(Supplier*, Item*, int);

    /** Constructor. */
    explicit DECLARE_EXPORT ItemSupplier(Supplier*, Item*, int, DateRange);

    /** Destructor. */
    DECLARE_EXPORT ~ItemSupplier();

    /** Search an existing object. */
    DECLARE_EXPORT static Object* finder(const DataValueDict&);

    /** Initialize the class. */
    static int initialize();
    static void writer(const MetaCategory*, Serializer*);

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

    /** Updates the resource. This method can only be called on an instance. */
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
    DECLARE_EXPORT void deleteOperationPlans(bool deleteLockedOpplans = false);

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
    static DECLARE_EXPORT const MetaCategory* metacategory;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Supplier>(Tags::supplier, &Cls::getSupplier, &Cls::setSupplier, MANDATORY + PARENT);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem, MANDATORY + PARENT);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addDurationField<Cls>(Tags::leadtime, &Cls::getLeadTime, &Cls::setLeadTime);
      m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum, &Cls::setSizeMinimum, 1.0);
      m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple, &Cls::setSizeMultiple);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      HasSource::registerFields<Cls>(m);
    }

  private:
    /** Factory method. */
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);

    /** Location where the supplier item applies to. */
    Location* loc;

    /** Procurement lead time. */
    Duration leadtime;

    /** Minimum procurement quantity. */
    double size_minimum;

    /** Procurement multiple quantity. */
    double size_multiple;

    /** Procurement cost. */
    double cost;

    /** Pointer to the head of the auto-generated purchase operation list.*/
    OperationItemSupplier* firstOperation;
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

    DECLARE_EXPORT Buffer* getOrigin() const;

    DECLARE_EXPORT Buffer* getDestination() const;

    /** Constructor. */
    explicit DECLARE_EXPORT OperationItemDistribution(ItemDistribution*, Buffer*, Buffer*);

    /** Destructor. */
    virtual DECLARE_EXPORT ~OperationItemDistribution();

    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, ItemDistribution>(Tags::itemdistribution, &Cls::getItemDistribution, NULL);
      m->addPointerField<Cls, Buffer>(Tags::origin, &Cls::getOrigin, NULL, DONT_SERIALIZE);
      m->addPointerField<Cls, Buffer>(Tags::destination, &Cls::getDestination, NULL, DONT_SERIALIZE);
    }

    /** Create a new transfer operationplan.
      * This method will link the operationplan to the correct ItemDistribution
      * model and its operation.
      * If none can be found, an ItemDistribution model is created
      * automatically and a data problem is also generated.
      */
    static PyObject* createOrder(PyObject*, PyObject*, PyObject*);
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

    DECLARE_EXPORT Buffer* getBuffer() const;

    static DECLARE_EXPORT OperationItemSupplier* findOrCreate(ItemSupplier*, Buffer*);

    /** Constructor. */
    explicit DECLARE_EXPORT OperationItemSupplier(ItemSupplier*, Buffer*);

    /** Destructor. */
    virtual DECLARE_EXPORT ~OperationItemSupplier();

    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, ItemSupplier>(Tags::itemsupplier, &Cls::getItemSupplier, NULL);
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, NULL, DONT_SERIALIZE);
    }

    /** Create a new purchase operationplan.
      * This method will link the operationplan to the correct ItemSupplier
      * model and its operation.
      * If none can be found, an ItemSupplier model is created automatically
      * and a data problem is also generated.
      */
    static PyObject* createOrder(PyObject*, PyObject*, PyObject*);
};


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
    explicit DECLARE_EXPORT Buffer() :
      hidden(false), producing_operation(uninitializedProducing), loc(NULL), it(NULL),
      min_val(0), max_val(default_max), min_cal(NULL), max_cal(NULL),
      min_interval(-1), tool(false), nextItemBuffer(NULL) {}

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
    DECLARE_EXPORT void buildProducingOperation();

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
    DECLARE_EXPORT void setItem(Item*);

    /** Returns the Location of this buffer. */
    Location* getLocation() const
    {
      return loc;
    }

    /** Updates the location of this buffer. */
    void setLocation(Location* i)
    {
      loc = i;
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
    DECLARE_EXPORT void setMinimum(double);

    /** Updates the minimum inventory target for the buffer. */
    DECLARE_EXPORT void setMinimumCalendar(Calendar*);

    /** Updates the minimum inventory target for the buffer. */
    DECLARE_EXPORT void setMaximum(double);

    /** Updates the minimum inventory target for the buffer. */
    DECLARE_EXPORT void setMaximumCalendar(Calendar*);

    /** Initialize the class. */
    static int initialize();

    /** Destructor. */
    virtual DECLARE_EXPORT ~Buffer();

    /** Returns the available material on hand immediately after the
      * given date.
      */
    DECLARE_EXPORT double getOnHand(Date d) const;

    /** Return the current on hand value, using the instance of the inventory
      * operation.
      */
    DECLARE_EXPORT double getOnHand() const;

    /** Update the on-hand inventory at the start of the planning horizon. */
    DECLARE_EXPORT void setOnHand(double f);

    /** Returns minimum or maximum available material on hand in the given
      * daterange. The third parameter specifies whether we return the
      * minimum (which is the default) or the maximum value.
      * The computation is INclusive the start and end dates.
      */
    DECLARE_EXPORT double getOnHand(Date, Date, bool min = true) const;

    /** Returns a reference to the list of all flows of this buffer. */
    const flowlist& getFlows() const
    {
      return flows;
    }

    flowlist::const_iterator getFlowIterator() const
    {
      return flows.begin();
    }

    virtual void solve(Solver &s, void* v = NULL) const
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

    /** Return the flow that is associates a given operation with this
      * buffer.<br>Returns NULL is no such flow exists. */
    Flow* findFlow(const Operation* o, Date d) const
    {
      return flows.find(o,d);
    }

    /** Deletes all operationplans consuming from or producing from this
      * buffer. The boolean parameter controls whether we delete also locked
      * operationplans or not.
      */
    DECLARE_EXPORT void deleteOperationPlans(bool deleteLockedOpplans = false);

    virtual DECLARE_EXPORT void updateProblems();

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
    static DECLARE_EXPORT const MetaCategory* metadata;

    /** This function matches producing and consuming operationplans
      * with each other, and updates the pegging iterator accordingly.
      */
    DECLARE_EXPORT void followPegging
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
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      Plannable::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnHand, &Cls::setOnHand);
      m->addDoubleField<Cls>(Tags::minimum, &Cls::getMinimum, &Cls::setMinimum);
      m->addPointerField<Cls, Calendar>(Tags::minimum_calendar, &Cls::getMinimumCalendar, &Cls::setMinimumCalendar);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMaximum, &Cls::setMaximum, default_max);
      m->addPointerField<Cls, Calendar>(Tags::maximum_calendar, &Cls::getMaximumCalendar, &Cls::setMaximumCalendar);
      m->addDurationField<Cls>(Tags::mininterval, &Cls::getMinimumInterval, &Cls::setMinimumInterval, -1);
      m->addDurationField<Cls>(Tags::maxinterval, &Cls::getMaximumInterval, &Cls::setMaximumInterval);
      m->addIteratorField<Cls, flowlist::const_iterator, Flow>(Tags::flows, Tags::flow, &Cls::getFlowIterator, DETAIL);
      m->addBoolField<Cls>(Tags::tool, &Cls::getTool, &Cls::setTool, BOOL_FALSE);
      m->addIteratorField<Cls, flowplanlist::const_iterator, FlowPlan>(Tags::flowplans, Tags::flowplan, &Cls::getFlowPlanIterator, PLAN);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasLevel::registerFields<Cls>(m);
    }

    /** A dummy producing operation to mark uninitialized ones. */
    static DECLARE_EXPORT OperationFixedTime *uninitializedProducing;

  private:
    /** A constant defining the default max inventory target.\\
      * Theoretically we should set this to DBL_MAX, but then the results
      * are not portable across platforms.
      */
    static DECLARE_EXPORT const double default_max;

    /** This models the dynamic part of the plan, representing all planned
      * material flows on this buffer. */
    flowplanlist flowplans;

    /** This models the defined material flows on this buffer. */
    flowlist flows;

    /** Hide this entity from serialization or not. */
    bool hidden;

    /** This is the operation used to create extra material in this buffer. */
    Operation *producing_operation;

    /** Location of this buffer.<br>
      * This field is only used as information.<br>
      * The default is NULL.
      */
    Location* loc;

    /** Item being stored in this buffer.<br>
      * The default value is NULL.
      */
    Item* it;

    /** Minimum inventory target.<br>
      * If a minimum calendar is specified this field is ignored.
      * @see min_cal
      */
    double min_val;

    /** Maximum inventory target. <br>
      * If a maximum calendar is specified this field is ignored.
      * @see max_cal
      */
    double max_val;

    /** Points to a calendar to store the minimum inventory level.<br>
      * The default value is NULL, resulting in a constant minimum level
      * of 0.
      */
    Calendar *min_cal;

    /** Points to a calendar to store the maximum inventory level.<br>
      * The default value is NULL, resulting in a buffer without excess
      * inventory problems.
      */
    Calendar *max_cal;

    /** Minimum time interval between purchasing operations. */
    Duration min_interval;

    /** Maximum time interval between purchasing operations. */
    Duration max_interval;

    /** A flag that marks whether this buffer represents a tool or not. */
    bool tool;

    /** Maintain a linked list of buffers per item. */
    Buffer *nextItemBuffer;
};


class Item::bufferIterator
{
  private:
    Buffer* cur;

  public:
    /** Constructor. */
    bufferIterator(const Item* i) : cur(i ? i->firstItemBuffer : NULL) {}

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


/** @brief This class is the default implementation of the abstract Buffer class. */
class BufferDefault : public Buffer
{
  public:
    explicit BufferDefault()
    {
      initType(metadata);
    }

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
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
      setProducingOperation(NULL);
      initType(metadata);
    }

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();
};


/** @brief This class models a buffer that is replenish by an external supplier
  * using a reorder-point policy.
  *
  * It represents a material buffer where a replenishment is triggered
  * whenever the inventory drops below the minimum level. The buffer is then
  * replenished to the maximum inventory level.<br>
  * A leadtime is taken into account for the replenishments.<br>
  * The following parameters control this replenishment:
  *  - <b>MinimumInventory</b>:<br>
  *    Inventory level triggering a new replenishment.<br>
  *    The actual inventory can drop below this value.
  *  - <b>MaximumInventory</b>:<br>
  *    Inventory level to which we try to replenish.<br>
  *    The actual inventory can exceed this value.
  *  - <b>LeadTime</b>:<br>
  *    Time taken between placing the purchase order with the supplier and the
  *    delivery of the material.
  *
  * Using the additional parameters described below the replenishments can be
  * controlled in more detail. The resulting inventory profile can end up
  * to be completely different from the classical saw-tooth pattern!
  *
  * The timing of the replenishments can be constrained by the following
  * parameters:
  *  - <b>MinimumInterval</b>:<br>
  *    Minimum time between replenishments.<br>
  *    The order quantity will be increased such that it covers at least
  *    the demand in the minimum interval period. The actual inventory can
  *    exceed the target set by the MinimumInventory parameter.
  *  - <b>MaximumInterval</b>:<br>
  *    Maximum time between replenishments.<br>
  *    The order quantity will replenish to an inventory value less than the
  *    maximum when this maximum interval is reached.
  * When the minimum and maximum interval are equal we basically define a fixed
  * schedule replenishment policy.
  *
  * The quantity of the replenishments can be constrained by the following
  * parameters:
  *  - <b>MinimumQuantity</b>:<br>
  *    Minimum quantity for a replenishment.<br>
  *    This parameter can cause the actual inventory to exceed the target set
  *    by the MinimumInventory parameter.
  *  - <b>MaximumQuantity</b>:<br>
  *    Maximum quantity for a replenishment.<br>
  *    This parameter can cause the maximum inventory target never to be
  *    reached.
  *  - <b>MultipleQuantity</b>:<br>
  *    All replenishments are rounded up to a multiple of this value.
  * When the minimum and maximum quantity are equal we basically define a fixed
  * quantity replenishment policy.
  */
class BufferProcure : public Buffer
{
  public:
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual const MetaClass& getType() const {return *metadata;}
    static int initialize();

    /** Default constructor. */
    explicit BufferProcure() : size_minimum(0), size_maximum(DBL_MAX),
      size_multiple(0), oper(NULL)
    {
      initType(metadata);
    }

    static DECLARE_EXPORT const MetaClass* metadata;

    /** Return the purchasing leadtime. */
    Duration getLeadTime() const
    {
      return leadtime;
    }

    /** Update the procurement leadtime. */
    void setLeadTime(Duration p)
    {
      if (p<0L)
        throw DataException("Procurement buffer can't have a negative lead time");
      if (!getProducingOperation())
        static_cast<OperationFixedTime*>(getOperation())->setDuration(p);
      leadtime = p;
    }

    /** Return the release time fence. */
    Duration getFence() const
    {
      return fence;
    }

    /** Update the release time fence. */
    void setFence(Duration p)
    {
      if (!getProducingOperation())
        getOperation()->setFence(p);
      fence = p;
    }

    /** Return the inventory level that will trigger creation of a
      * purchasing.
      */
    double getMinimumInventory() const
    {
      return getFlowPlans().getMin(Date::infiniteFuture);
    }

    /** Update the inventory level that will trigger the creation of a
      * replenishment.<br>
      * Because of the replenishment leadtime, the actual inventory will drop
      * below this value. It is up to the user to set an appropriate minimum
      * value.
      */
    void setMinimumInventory(double f)
    {
      if (f<0)
        throw DataException("Procurement buffer can't have a negative minimum inventory");
      flowplanlist::EventMinQuantity* min = getFlowPlans().getMinEvent(Date::infiniteFuture);
      if (min)
        min->setMin(f);
      else
      {
        // Create and insert a new minimum event
        min = new flowplanlist::EventMinQuantity(Date::infinitePast, &getFlowPlans(), f);
        getFlowPlans().insert(min);
      }
      // The minimum is increased over the maximum: auto-increase the maximum.
      if (getFlowPlans().getMax(Date::infiniteFuture) < f)
        setMaximumInventory(f);
    }

    /** Return the maximum inventory level to which we wish to replenish. */
    double getMaximumInventory() const
    {
      return getFlowPlans().getMax(Date::infiniteFuture);
    }

    /** Update the maximum inventory level to which we plan to replenish.<br>
      * This is not a hard limit - other parameters can make that the actual
      * inventory either never reaches this value or always exceeds it.
      */
    void setMaximumInventory(double f)
    {
      if (f<0)
        throw DataException("Procurement buffer can't have a negative maximum inventory");
      flowplanlist::EventMaxQuantity* max = getFlowPlans().getMaxEvent(Date::infiniteFuture);
      if (max)
        max->setMax(f);
      else
      {
        // Create and insert a new maximum event
        max = new flowplanlist::EventMaxQuantity(Date::infinitePast, &getFlowPlans(), f);
        getFlowPlans().insert(max);
      }
      // The maximum is lowered below the minimum: auto-decrease the minimum
      if (f < getFlowPlans().getMin(Date::infiniteFuture))
        setMinimumInventory(f);
    }

    /** Return the minimum quantity of a purchasing operation. */
    double getSizeMinimum() const
    {
      return size_minimum;
    }

    /** Update the minimum replenishment quantity. */
    void setSizeMinimum(double f)
    {
      if (f<0)
        throw DataException("Procurement buffer can't have a negative minimum size");
      size_minimum = f;
      if (!getProducingOperation())
        getOperation()->setSizeMinimum(f);
      // minimum is increased over the maximum: auto-increase the maximum
      if (size_maximum < size_minimum) size_maximum = size_minimum;
    }

    /** Return the maximum quantity of a purchasing operation. */
    double getSizeMaximum() const
    {
      return size_maximum;
    }

    /** Update the maximum replenishment quantity. */
    void setSizeMaximum(double f)
    {
      if (f<0)
        throw DataException("Procurement buffer can't have a negative maximum size");
      size_maximum = f;
      if (!getProducingOperation())
        getOperation()->setSizeMaximum(f);
      // maximum is lowered below the minimum: auto-decrease the minimum
      if (size_maximum < size_minimum) size_minimum = size_maximum;
    }

    /** Return the multiple quantity of a purchasing operation. */
    double getSizeMultiple() const
    {
      return size_multiple;
    }

    /** Update the multiple quantity. */
    void setSizeMultiple(double f)
    {
      if (f<0)
        throw DataException("Procurement buffer can't have a negative multiple size");
      size_multiple = f;
      if (!getProducingOperation())
        getOperation()->setSizeMultiple(f);
    }

    /** Returns the operation that is automatically created to represent the
      * procurements.
      */
    DECLARE_EXPORT Operation* getOperation() const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDurationField<Cls>(Tags::leadtime, &Cls::getLeadTime, &Cls::setLeadTime);
      m->addDurationField<Cls>(Tags::fence, &Cls::getFence, &Cls::setFence);
      m->addDoubleField<Cls>(Tags::size_maximum, &Cls::getSizeMaximum, &Cls::setSizeMaximum, DBL_MAX);
      m->addDoubleField<Cls>(Tags::size_minimum, &Cls::getSizeMinimum, &Cls::setSizeMinimum);
      m->addDoubleField<Cls>(Tags::size_multiple, &Cls::getSizeMultiple, &Cls::setSizeMultiple);
      m->addDoubleField<Cls>(Tags::mininventory, &Cls::getMinimumInventory, &Cls::setMinimumInventory);
      m->addDoubleField<Cls>(Tags::maxinventory, &Cls::getMaximumInventory, &Cls::setMaximumInventory);
    }

  private:
    /** Purchasing leadtime.<br>
      * Within this leadtime fence no additional purchase orders can be generated.
      * TODO The lead time should be a property of the operation, not the buffer.
      */
    Duration leadtime;

    /** Time window from the current date in which all procurements are expected
      * to be released.
      * TODO The fence should be a property of the operation, not the buffer.
      */
    Duration fence;

    /** Minimum purchasing quantity.<br>
      * The default value is 0, meaning no minimum.
      * TODO The fence should be a property of the operation, not the buffer.
      */
    double size_minimum;

    /** Maximum purchasing quantity.<br>
      * The default value is 0, meaning no maximum limit.
      * TODO The fence should be a property of the operation, not the buffer.
      */
    double size_maximum;

    /** Purchases are always rounded up to a multiple of this quantity.<br>
      * The default value is 0, meaning no multiple needs to be applied.
      * TODO The fence should be a property of the operation, not the buffer.
      */
    double size_multiple;

    /** A pointer to the procurement operation. */
    Operation* oper;
};


/** @brief This class defines a material flow to/from a buffer, linked with an
  * operation. This default implementation plans the material flow at the
  * start of the operation.
  */
class Flow : public Object, public Association<Operation,Buffer,Flow>::Node,
  public Solvable, public HasSource
{
  public:
    /** Destructor. */
    virtual DECLARE_EXPORT ~Flow();

    /** Constructor. */
    explicit Flow(Operation* o, Buffer* b, double q)
      : quantity(q), search(PRIORITY)
    {
      setOperation(o);
      setBuffer(b);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Constructor. */
    explicit Flow(Operation* o, Buffer* b, double q, DateRange e)
      : quantity(q), search(PRIORITY)
    {
      setOperation(o);
      setBuffer(b);
      setEffective(e);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Search an existing object. */
    DECLARE_EXPORT static Object* finder(const DataValueDict&);

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
      return quantity < 0;
    }

    /** Returns true if this flow produces material into the buffer. */
    bool isProducer() const
    {
      return quantity >= 0;
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
    }

    /** Returns the buffer. */
    Buffer* getBuffer() const
    {
      return getPtrB();
    }

    /** Updates the buffer of this flow. This method can be called only ONCE
      * for each flow. In case that doesn't suit you, delete the existing flow
      * and create a new one.
      */
    void setBuffer(Buffer* b)
    {
      if (b) setPtrB(b,b->getFlows());
    }

    /** Return the leading flow of this group.
      * When the flow has no alternate or if the flow is itself leading
      * then NULL is returned.
      */
    Flow* getAlternate() const
    {
      if (getName().empty() || !getOperation())
        return NULL;
      for (Operation::flowlist::const_iterator h=getOperation()->getFlows().begin();
        h!=getOperation()->getFlows().end() && this != &*h; ++h)
        if (getName() == h->getName())
          return const_cast<Flow*>(&*h);
      return NULL;
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

    /** This method holds the logic the compute the date of a flowplan. */
    virtual Date getFlowplanDate(const FlowPlan*) const;

    /** This method holds the logic the compute the quantity of a flowplan. */
    virtual double getFlowplanQuantity(const FlowPlan*) const;

    static int initialize();

    string getTypeName() const
    {
      return getType().type;
    }

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation, MANDATORY + PARENT);
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, &Cls::setBuffer, MANDATORY + PARENT);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority, 1);
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName);
      m->addEnumField<Cls, SearchMode>(Tags::search, &Cls::getSearch, &Cls::setSearch, PRIORITY);
      m->addDateField<Cls>(Tags::effective_start, &Cls::getEffectiveStart, &Cls::setEffectiveStart);
      m->addDateField<Cls>(Tags::effective_end, &Cls::getEffectiveEnd, &Cls::setEffectiveEnd, Date::infiniteFuture);
      HasSource::registerFields<Cls>(m);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
    	// Not very nice: all flow subclasses appear to Python as instance of a
	    // single Python class. We use this method to distinguish them.
      m->addStringField<Cls>(Tags::type, &Cls::getTypeName, NULL, "", DONT_SERIALIZE);
    }

  protected:
    /** Default constructor. */
    explicit DECLARE_EXPORT Flow() : quantity(0.0), search(PRIORITY)
    {
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

  private:
    /** Quantity of the flow. */
    double quantity;

    /** Mode to select the preferred alternates. */
    SearchMode search;

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
    static DECLARE_EXPORT const MetaClass* metadata;
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
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

    /** This method holds the logic the compute the date of a flowplan. */
    virtual Date getFlowplanDate(const FlowPlan* fl) const;

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
};


/** @brief This class represents a flow at end date of the
  * operation and with a fiwed quantity.
  */
class FlowFixedEnd : public FlowEnd
{
  public:
    /** Constructor. */
    explicit FlowFixedEnd(Operation* o, Buffer* b, double q) : FlowEnd(o,b,q) {}

    /** This constructor is called from the plan begin_element function. */
    explicit FlowFixedEnd() {}

    /** This method holds the logic the compute the quantity of a flowplan. */
    virtual double getFlowplanQuantity(const FlowPlan*) const;

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
};


/** @brief This class represents a flow at start date of the
  * operation and with a fiwed quantity.
  */
class FlowFixedStart : public FlowStart
{
  public:
    /** Constructor. */
    explicit FlowFixedStart(Operation* o, Buffer* b, double q) : FlowStart(o,b,q) {}

    /** This constructor is called from the plan begin_element function. */
    explicit FlowFixedStart() {}

    /** This method holds the logic the compute the quantity of a flowplan. */
    virtual double getFlowplanQuantity(const FlowPlan*) const;

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
};


/** @brief A flowplan represents a planned material flow in or out of a buffer.
  *
  * Flowplans are owned by operationplans, which manage a container to store
  * them.
  */
class FlowPlan : public TimeLine<FlowPlan>::EventChangeOnhand
{
    friend class OperationPlan::FlowPlanIterator;
  private:
    /** Points to the flow instantiated by this flowplan. */
    Flow *fl;

    /** Points to the operationplan owning this flowplan. */
    OperationPlan *oper;

    /** Points to the next flowplan owned by the same operationplan. */
    FlowPlan *nextFlowPlan;

  public:

    static DECLARE_EXPORT const MetaCategory* metadata;
    static int initialize();
    virtual const MetaClass& getType() const { return *metadata; }

    /** Constructor. */
    explicit DECLARE_EXPORT FlowPlan(OperationPlan*, const Flow*);

    /** Returns the flow of which this is an plan instance. */
    Flow* getFlow() const
    {
      return fl;
    }

    /** Returns the buffer, a convenient shortcut. */
    Buffer* getBuffer() const
    {
      return fl->getBuffer();
    }

    /** Returns the operation, a convenient shortcut. */
    Operation* getOperation() const
    {
      return fl->getOperation();
    }

    /** Update the flow of an already existing flowplan.<br>
      * The new flow must belong to the same operation.
      */
    DECLARE_EXPORT void setFlow(Flow*);

    /** Returns the operationplan owning this flowplan. */
    OperationPlan* getOperationPlan() const
    {
      return oper;
    }

    /** Destructor. */
    virtual ~FlowPlan()
    {
      Buffer* b = getFlow()->getBuffer();
      b->setChanged();
      b->flowplans.erase(this);
    }

    /** Updates the quantity of the flowplan by changing the quantity of the
      * operationplan owning this flowplan.<br>
      * The boolean parameter is used to control whether to round up (false)
      * or down (true) in case the operation quantity must be a multiple.<br>
      * The second parameter is to flag whether we want to actually perform
      * the resizing, or only to simulate it.
      */
    double setQuantity(double qty, bool b=false, bool u=true, bool e=true)
    {
      if (!getFlow()->getEffective().within(getDate())) return 0.0;
      if (getFlow()->getType() == *FlowFixedEnd::metadata
        || getFlow()->getType() == *FlowFixedStart::metadata)
      {
        // Fixed quantity flows only allow resizing to 0
        if (qty == 0.0 && oper->getQuantity()!= 0.0)
          return oper->setQuantity(0.0, b, u) ? getFlow()->getQuantity() : 0.0;
        else if (qty != 0.0 && oper->getQuantity()== 0.0)
          return oper->setQuantity(
            (oper->getOperation()->getSizeMinimum()<=0) ? 0.001
              : oper->getOperation()->getSizeMinimum(),
            b, u, e) ? getFlow()->getQuantity() : 0.0;
      }
      else
        // Normal, proportional flows
        return oper->setQuantity(qty / getFlow()->getQuantity(), b, u, e) * getFlow()->getQuantity();
      throw LogicException("Unreachable code reached");
    }

    /** This function needs to be called whenever the flowplan date or
      * quantity are changed.
      */
    DECLARE_EXPORT void update();

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

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDateField<Cls>(Tags::date, &Cls::getDate);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity);
      m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnhand);
      m->addDoubleField<Cls>(Tags::minimum, &Cls::getMin);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMax);
      m->addPointerField<Cls, OperationPlan>(Tags::operationplan, &Cls::getOperationPlan);
      m->addPointerField<Cls, Flow>(Tags::flow, &Cls::getFlow, &Cls::setFlow, DONT_SERIALIZE);
      m->addPointerField<Cls, Buffer>(Tags::buffer, &Cls::getBuffer, NULL, DONT_SERIALIZE);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, NULL, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, NULL, BOOL_FALSE, DONT_SERIALIZE);
      /*  TODO XXX write pegging?
  // Write pegging info.
  if (o->getContentType() == Serializer::PLANDETAIL)
  {
    // Write the upstream pegging
    PeggingIterator k(this, false);
    if (k) --k;
    for (; k; --k)
      o->writeElement(Tags::pegging,
        Tags::level, -k.getLevel(),
        Tags::operationplan, k.getOperationPlan()->getIdentifier(),
        Tags::quantity, k.getQuantity()
        );

    // Write the downstream pegging
    PeggingIterator l(this, true);
    if (l) ++l;
    for (; l; ++l)
      o->writeElement(Tags::pegging,
        Tags::level, l.getLevel(),
        Tags::operationplan, l.getOperationPlan()->getIdentifier(),
        Tags::quantity, l.getQuantity()
        );
        */
    }
};


inline double Flow::getFlowplanQuantity(const FlowPlan* fl) const
{
  return getEffective().within(fl->getDate()) ?
    fl->getOperationPlan()->getQuantity() * getQuantity() :
    0.0;
}


inline double FlowFixedStart::getFlowplanQuantity(const FlowPlan* fl) const
{
  return getEffective().within(fl->getDate()) ?
    getQuantity() :
    0.0;
}


inline double FlowFixedEnd::getFlowplanQuantity(const FlowPlan* fl) const
{
  return getEffective().within(fl->getDate()) ?
    getQuantity() :
    0.0;
}


inline Date Flow::getFlowplanDate(const FlowPlan* fl) const
{
  return fl->getOperationPlan()->getDates().getStart();
}


inline Date FlowEnd::getFlowplanDate(const FlowPlan* fl) const
{
  return fl->getOperationPlan()->getDates().getEnd();
}


/** @brief An specific changeover rule in a setup matrix. */
class SetupMatrixRule : public Object
{
    friend class SetupMatrix;
  public:

    /** Default constructor. */
    SetupMatrixRule() : cost(0), priority(0), matrix(NULL), nextRule(NULL), prevRule(NULL)
    {
      initType(metadata);
    }

    /** Update the matrix pointer. */
    DECLARE_EXPORT void setSetupMatrix(SetupMatrix*);

    /** Destructor. */
    DECLARE_EXPORT ~SetupMatrixRule();

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
    static DECLARE_EXPORT const MetaCategory* metacategory;

    /** Update the priority.<br>
      * The priority value is a key field. If multiple rules have the
      * same priority a data exception is thrown.
      */
    DECLARE_EXPORT void setPriority(const int);

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
    string getFromSetup() const
    {
      return from;
    }

    /** Update the from setup. */
    void setToSetup(const string& f)
    {
      to = f;
    }

    /** Return the from setup. */
    string getToSetup() const
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
      m->addStringField<Cls>(Tags::fromsetup, &Cls::getFromSetup, &Cls::setFromSetup);
      m->addStringField<Cls>(Tags::tosetup, &Cls::getToSetup, &Cls::setToSetup);
      m->addDurationField<Cls>(Tags::duration, &Cls::getDuration, &Cls::setDuration);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
      m->addPointerField<Cls, SetupMatrix>(Tags::setupmatrix, &Cls::getSetupMatrix, &Cls::setSetupMatrix, DONT_SERIALIZE + PARENT);
    }
  private:
    /** Original setup. */
    string from;

    /** New setup. */
    string to;

    /** Changeover time. */
    Duration duration;

    /** Changeover cost. */
    double cost;

    /** Priority of the rule.<br>
      * This field is the key field, i.e. within a setup matrix all rules
      * need to have different priorities.
      */
    int priority;

    /** Pointer to the owning matrix. */
    SetupMatrix *matrix;

    /** Pointer to the next rule in this matrix. */
    SetupMatrixRule *nextRule;

    /** Pointer to the previous rule in this matrix. */
    SetupMatrixRule *prevRule;

  public:
    /** @brief An iterator class to go through all rules of a setup matrix. */
    class iterator
    {
      private:
        SetupMatrixRule* curRule;

      public:
        /** Constructor. */
        iterator(SetupMatrixRule* c = NULL) : curRule(c) {}

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

        SetupMatrixRule *next()
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
          return NULL;
        }
    };
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
      m->addIteratorField<Cls, SetupMatrixRule::iterator, SetupMatrixRule>(Tags::rules, Tags::rule, &Cls::getRules, BASE + WRITE_FULL);
    }

  public:
    /** Default constructor. */
    explicit DECLARE_EXPORT SetupMatrix() : firstRule(NULL) {}

    /** Destructor. */
    DECLARE_EXPORT ~SetupMatrix();

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    /** Returns an iterator to go through the list of rules. */
    SetupMatrixRule::iterator getRules() const
    {
      return SetupMatrixRule::iterator(firstRule);
    }

    /** Python interface to add a new rule. */
    static DECLARE_EXPORT PyObject* addPythonRule(PyObject*, PyObject*, PyObject*);

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
      * If no matching rule is found, the changeover is not allowed: a NULL
      * pointer is returned.
      */
    DECLARE_EXPORT SetupMatrixRule* calculateSetup(const string, const string) const;

  private:
    /** Head of the list of rules. */
    SetupMatrixRule *firstRule;
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
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();
};


/** @brief This class models skills that can be assigned to resources. */
class Skill : public HasName<Skill>, public HasSource
{
  friend class ResourceSkill;

  public:
    /** Default constructor. */
    explicit DECLARE_EXPORT Skill()
    {
      initType(metadata);
    }

    /** Destructor. */
    DECLARE_EXPORT ~Skill();

    typedef Association<Resource,Skill,ResourceSkill>::ListB resourcelist;

    /** Returns an iterator over the list of resources having this skill. */
    resourcelist::const_iterator getResources() const
    {
      return resources.begin();
    }

    /** Python interface to add a new resource. */
    static DECLARE_EXPORT PyObject* addPythonResource(PyObject*, PyObject*);

    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "", MANDATORY);
      m->addIteratorField<Cls, resourcelist::const_iterator, ResourceSkill>(Tags::resourceskills, Tags::resourceskill, &Cls::getResources);
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
    static DECLARE_EXPORT const MetaClass* metadata;
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
    explicit DECLARE_EXPORT Resource() :
      size_max_cal(NULL), size_max(0), loc(NULL), cost(0.0), hidden(false),
      maxearly(defaultMaxEarly), setupmatrix(NULL)
    {
      setMaximum(1);
    }

    /** Destructor. */
    virtual DECLARE_EXPORT ~Resource();

    /** Updates the size of a resource, when it is time-dependent. */
    virtual DECLARE_EXPORT void setMaximumCalendar(Calendar*);

    /** Updates the size of a resource. */
    DECLARE_EXPORT void setMaximum(double);

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

    /** Return the load that is associates a given operation with this
      * resource. Returns NULL is no such load exists. */
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

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Deletes all operationplans loading this resource. The boolean parameter
      * controls whether we delete also locked operationplans or not.
      */
    DECLARE_EXPORT void deleteOperationPlans(bool = false);

    /** Recompute the problems of this resource. */
    virtual DECLARE_EXPORT void updateProblems();

    /** Scan the setups of this resource. */
    virtual DECLARE_EXPORT void updateSetups(const LoadPlan* = NULL);

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
    static DECLARE_EXPORT const MetaCategory* metadata;

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
    void setSetupMatrix(SetupMatrix *s)
    {
      setupmatrix = s;
    }

    /** Return the current setup. */
    string getSetup() const
    {
      return setup;
    }

    /** Update the current setup. */
    DECLARE_EXPORT void setSetup(const string& s)
    {
      setup = s;
    }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMaximum, &Cls::setMaximum, 1);
      m->addPointerField<Cls, Calendar>(Tags::maximum_calendar, &Cls::getMaximumCalendar, &Cls::setMaximumCalendar);
      m->addDurationField<Cls>(Tags::maxearly, &Cls::getMaxEarly, &Cls::setMaxEarly, defaultMaxEarly);
      m->addDoubleField<Cls>(Tags::cost, &Cls::getCost, &Cls::setCost);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addStringField<Cls>(Tags::setup, &Cls::getSetup, &Cls::setSetup);
      m->addPointerField<Cls, SetupMatrix>(Tags::setupmatrix, &Cls::getSetupMatrix, &Cls::setSetupMatrix);
      Plannable::registerFields<Cls>(m);
      m->addIteratorField<Cls, loadlist::const_iterator, Load>(Tags::loads, Tags::load, &Cls::getLoadIterator, DETAIL);
      m->addIteratorField<Cls, skilllist::const_iterator, ResourceSkill>(Tags::resourceskills, Tags::resourceskill, &Cls::getSkills, DETAIL);
      m->addIteratorField<Cls, loadplanlist::const_iterator, LoadPlan>(Tags::loadplans, Tags::loadplan, &Cls::getLoadPlanIterator, DETAIL);
      m->addIteratorField<Cls, OperationPlanIterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans, PLAN);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      HasLevel::registerFields<Cls>(m);
    }
  protected:
    /** This calendar is used to updates to the resource size. */
    Calendar* size_max_cal;

    /** Stores the collection of all loadplans of this resource. */
    loadplanlist loadplans;

  private:
    /** The maximum resource size.<br>
      * If a calendar is specified, this field is ignored.
      */
    double size_max;

    /** This is a list of all load models that are linking this resource with
      * operations. */
    loadlist loads;

    /** This is a list of skills this resource has. */
    skilllist skills;

    /** A pointer to the location of the resource. */
    Location* loc;

    /** The cost of using 1 unit of this resource for 1 hour. */
    double cost;

    /** Specifies whether this resource is hidden for serialization. */
    bool hidden;

    /** Maximum inventory buildup allowed in case of capacity shortages. */
    Duration maxearly;

    /** Reference to the setup matrix. */
    SetupMatrix *setupmatrix;

    /** Current setup. */
    string setup;

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
    /** Pointer to the resource we're investigating. */
    Resource* res;

    /** A Python object pointing to a list of start dates of buckets. */
    PyObject* bucketiterator;

    /** An iterator over all events in the resource timeline. */
    Resource::loadplanlist::iterator ldplaniter;

    /** Python function to iterate over the periods. */
    PyObject* iternext();

    double cur_setup;
    double cur_load;
    double cur_size;
    bool bucketized;
    Date cur_date;
    Date prev_date;
    bool prev_value;
    Calendar::EventIterator unavailableIterator;
    bool hasUnavailability;
    double bucket_available;
    double bucket_load;
    double bucket_setup;
    double bucket_unavailable;

    void update(Date till);

    /** Python object pointing to the start date of the plan bucket. */
    PyObject* start_date;

    /** Python object pointing to the start date of the plan bucket. */
    PyObject* end_date;
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
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();
};


/** @brief This class represents a resource that'll never have any
  * capacity shortage. */
class ResourceInfinite : public Resource
{
  public:
    explicit DECLARE_EXPORT ResourceInfinite()
    {
      setDetectProblems(false);
      initType(metadata);
    }

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
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

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();

    virtual DECLARE_EXPORT void updateProblems();

    /** Updates the time buckets and the quantity per time bucket. */
    virtual DECLARE_EXPORT void setMaximumCalendar(Calendar*);
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
    explicit DECLARE_EXPORT ResourceSkill(Skill*, Resource*, int);

    /** Constructor. */
    explicit DECLARE_EXPORT ResourceSkill(Skill*, Resource*, int, DateRange);

    /** Destructor. */
    DECLARE_EXPORT ~ResourceSkill();

    /** Initialize the class. */
    static int initialize();

    /** Search an existing object. */
    DECLARE_EXPORT static Object* finder(const DataValueDict&);

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
    static DECLARE_EXPORT const MetaCategory* metadata;

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
    static DECLARE_EXPORT const MetaClass* metadata;
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
      : search(PRIORITY), skill(NULL)
    {
      setOperation(o);
      setResource(r);
      setQuantity(u);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Constructor. */
    explicit Load(Operation* o, Resource* r, double u, DateRange e)
      : search(PRIORITY), skill(NULL)
    {
      setOperation(o);
      setResource(r);
      setQuantity(u);
      setEffective(e);
      initType(metadata);
      HasLevel::triggerLazyRecomputation();
    }

    /** Destructor. */
    DECLARE_EXPORT ~Load();

    /** Search an existing object. */
    DECLARE_EXPORT static Object* finder(const DataValueDict& k);

    /** Returns the operation consuming the resource capacity. */
    Operation* getOperation() const
    {
      return getPtrA();
    }

    /** Updates the operation being loaded. This method can only be called
      * once for a load. */
    DECLARE_EXPORT void setOperation(Operation*);

    /** Returns the capacity resource being consumed. */
    Resource* getResource() const
    {
      return getPtrB();
    }

    /** Updates the capacity being consumed. This method can only be called
      * once on a resource. */
    void setResource(Resource* r)
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
      * then NULL is returned.
      */
    Load* getAlternate() const
    {
      if (getName().empty() || !getOperation())
        return NULL;
      for (Operation::loadlist::const_iterator h=getOperation()->getLoads().begin();
        h!=getOperation()->getLoads().end() && this != &*h; ++h)
        if (getName() == h->getName())
          return const_cast<Load*>(&*h);
      return NULL;
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

    /** Update the required resource setup. */
    DECLARE_EXPORT void setSetup(const string&);

    /** Return the required resource setup. */
    string getSetup() const
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

    /** This method holds the logic the compute the date of a loadplan. */
    virtual Date getLoadplanDate(const LoadPlan*) const;

    /** This method holds the logic the compute the quantity of a loadplan. */
    virtual double getLoadplanQuantity(const LoadPlan*) const;

    static int initialize();

    bool getHidden() const
    {
      return (getResource() && getResource()->getHidden())
          || (getOperation() && getOperation()->getHidden());
    }
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    /** Default constructor. */
    Load() : qty(1.0), search(PRIORITY), skill(NULL)
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
      m->addStringField<Cls>(Tags::setup, &Cls::getSetup, &Cls::setSetup);
      m->addPointerField<Cls, Skill>(Tags::skill, &Cls::getSkill, &Cls::setSkill);
      HasSource::registerFields<Cls>(m);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
    }

  private:
    /** Stores how much capacity is consumed during the duration of an
      * operationplan. */
    double qty;

    /** Required setup. */
    string setup;

    /** Mode to select the preferred alternates. */
    SearchMode search;

    /** Required skill. */
    Skill* skill;

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

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaClass* metadata;
};


/** @brief Represents the (independent) demand in the system. It can represent a
  * customer order or a forecast.
  *
  * This is an abstract class.
  */
class Demand
  : public HasHierarchy<Demand>, public Plannable, public HasDescription
{
  public:
    typedef slist<OperationPlan*> OperationPlanList;

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
            return NULL;
          OperationPlan* tmp = *cur;
          ++cur;
          return tmp;
        }
    };

    /** Default constructor. */
    explicit DECLARE_EXPORT Demand() :
      it(NULL), loc(NULL), oper(uninitializedDelivery), cust(NULL), qty(0.0),
      prio(0), maxLateness(Duration::MAX), minShipment(1), hidden(false)
      {}

    /** Destructor.
      * Deleting the demand will also delete all delivery operation
      * plans (including locked ones).
      */
    virtual DECLARE_EXPORT ~Demand();

    /** Returns the quantity of the demand. */
    double getQuantity() const
    {
      return qty;
    }

    /** Updates the quantity of the demand. The quantity must be be greater
      * than or equal to 0. */
    virtual DECLARE_EXPORT void setQuantity(double);

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

    /** Updates the item/product being requested. */
    virtual void setItem(Item *i)
    {
      if (it == i)
        return;
      it=i;
      if (oper && oper->getHidden())
        oper = uninitializedDelivery;
      setChanged();
    }

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

    /** This fields points to an operation that is to be used to plan the
      * demand. By default, the field is left to NULL and the demand will then
      * be planned using the delivery operation of its item.
      * @see Item::getDelivery()
      */
    Operation* getOperation() const
    {
      if (oper == uninitializedDelivery)
        return NULL;
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
      *   4) If the previous step fails, return NULL.
      *      This demand can't be satisfied!
      */
    DECLARE_EXPORT Operation* getDeliveryOperation() const;

    /** Returns the cluster which this demand belongs to. */
    unsigned int getCluster() const
    {
      Operation* o = getDeliveryOperation();
      return o ? o->getCluster() : 0;
    }

    /** Returns the delivery operationplan list. */
    DECLARE_EXPORT const OperationPlanList& getDelivery() const;

    DeliveryIterator getOperationPlans() const
    {
      return DeliveryIterator(this);
    }

    /** Returns the latest delivery operationplan. */
    DECLARE_EXPORT OperationPlan* getLatestDelivery() const;

    /** Returns the earliest delivery operationplan. */
    DECLARE_EXPORT OperationPlan* getEarliestDelivery() const;

    /** Adds a delivery operationplan for this demand. */
    DECLARE_EXPORT void addDelivery(OperationPlan *o);

    /** Removes a delivery operationplan for this demand. */
    DECLARE_EXPORT void removeDelivery(OperationPlan *o);

    /** Deletes all delivery operationplans of this demand.<br>
      * The (optional) boolean parameter controls whether we delete also locked
      * operationplans or not.<br>
      * The second (optional) argument is a command list that can be used to
      * remove the operationplans in an undo-able way.
      */
    DECLARE_EXPORT void deleteOperationPlans
    (bool deleteLockedOpplans = false, CommandManager* = NULL);

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
    DECLARE_EXPORT Problem::List::iterator getConstraintIterator() const;

    /** Returns the total amount that has been planned. */
    DECLARE_EXPORT double getPlannedQuantity() const;

    /** Return an iterator over the problems of this demand. */
    DECLARE_EXPORT Problem::List::iterator getProblemIterator() const;

    static int initialize();

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

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
      * The default value is 1.
      */
    double getMinShipment() const
    {
      return minShipment;
    }

    /** Updates the maximum allowed lateness for this demand.<br>
      * The default value is infinite.<br>
      * The argument must be a positive time period.
      */
    virtual void setMinShipment(double m)
    {
      if (m < 0.0)
        throw DataException("The minumum demand shipment quantity must be positive");
      minShipment = m;
    }

    /** Recompute the problems. */
    virtual DECLARE_EXPORT void updateProblems();

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
    static DECLARE_EXPORT const MetaCategory* metadata;

    DECLARE_EXPORT PeggingIterator getPegging() const;

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      HasHierarchy<Cls>:: template registerFields<Cls>(m);
      HasDescription::registerFields<Cls>(m);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, &Cls::setQuantity);
      m->addPointerField<Cls, Item>(Tags::item, &Cls::getItem, &Cls::setItem);
      m->addPointerField<Cls, Location>(Tags::location, &Cls::getLocation, &Cls::setLocation);
      m->addPointerField<Cls, Customer>(Tags::customer, &Cls::getCustomer, &Cls::setCustomer);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, &Cls::setOperation);
      Plannable::registerFields<Cls>(m);
      m->addDateField<Cls>(Tags::due, &Cls::getDue, &Cls::setDue);
      m->addIntField<Cls>(Tags::priority, &Cls::getPriority, &Cls::setPriority);
      m->addDurationField<Cls>(Tags::maxlateness, &Cls::getMaxLateness, &Cls::setMaxLateness, Duration::MAX);
      m->addDoubleField<Cls>(Tags::minshipment, &Cls::getMinShipment, &Cls::setMinShipment, 1);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, &Cls::setHidden, BOOL_FALSE, DONT_SERIALIZE);
      m->addIteratorField<Cls, PeggingIterator, PeggingIterator>(Tags::pegging, Tags::pegging, &Cls::getPegging, PLAN + WRITE_FULL);
      m->addIteratorField<Cls, DeliveryIterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Cls::getOperationPlans, DETAIL + WRITE_FULL + WRITE_HIDDEN);
      m->addIteratorField<Cls, Problem::List::iterator, Problem>(Tags::constraints, Tags::problem, &Cls::getConstraintIterator, DETAIL);
    }

  private:
    static DECLARE_EXPORT OperationFixedTime *uninitializedDelivery;

    /** Requested item. */
    Item *it;

    /** Location. */
    Location * loc;

    /** Delivery Operation. Can be left NULL, in which case the delivery
      * operation can be specified on the requested item. */
    Operation *oper;

    /** Customer creating this demand. */
    Customer *cust;

    /** Requested quantity. Only positive numbers are allowed. */
    double qty;

    /** Priority. Lower numbers indicate a higher priority level.*/
    int prio;

    /** Due date. */
    Date dueDate;

    /** Maximum lateness allowed when planning this demand.<br>
      * The default value is Duration::MAX.
      */
    Duration maxLateness;

    /** Minimum size for a delivery operation plan satisfying this demand. */
    double minShipment;

    /** Hide this demand or not. */
    bool hidden;

    /** A list of operation plans to deliver this demand. */
    OperationPlanList deli;

    /** A list of constraints preventing this demand from being planned in
      * full and on time. */
    Problem::List constraints;
};


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
    static DECLARE_EXPORT const MetaClass* metadata;
    static int initialize();
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
    /** Public constructor.<br>
      * This constructor constructs the starting loadplan and will
      * also call a private constructor to creates the ending loadplan.
      * In other words, a single call to the constructor will create
      * two loadplan objects.
      */
    explicit DECLARE_EXPORT LoadPlan(OperationPlan*, const Load*);

    /** Return the operationplan owning this loadplan. */
    OperationPlan* getOperationPlan() const
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
      return oper->getDates().getStart();
    }

    /** Return the start date of the operationplan. */
    Date getEndDate() const
    {
      return oper->getDates().getEnd();
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
      setResource(res, false);
    }

    /** Update the resource.<br>
      * The optional second argument specifies whether or not we need to verify
      * if the assigned resource is valid. A valid resource must a) be a
      * subresource of the resource specified on the load, and b) must also
      * have the skill specified on the resource.
      */
    DECLARE_EXPORT void setResource(Resource*, bool);

    /** Return the resource. */
    Resource* getResource() const
    {
      return res;
    }

    /** Update the load of an already existing flowplan.<br>
      * The new load must belong to the same operation.
      */
    DECLARE_EXPORT void setLoad(Load*);

    /** Return true when this loadplan marks the start of an operationplan. */
    bool isStart() const
    {
      return start_or_end == START;
    }

    /** Destructor. */
    DECLARE_EXPORT virtual ~LoadPlan();

    /** This function needs to be called whenever the loadplan date or
      * quantity are changed.
      */
    DECLARE_EXPORT void update();

    /** Return a pointer to the timeline data structure owning this loadplan. */
    TimeLine<LoadPlan>* getTimeLine() const
    {
      return &(res->loadplans);
    }

    /** Returns the current setup of the resource. */
    string getSetup() const
    {
      return getSetup(true);
    }

    /** Returns the current setup of the resource.<br>/
      * When the argument is true (= default) the current setup is returned.<br>
      * When the argument is false the setup just before the loadplan is returned.
      */
    DECLARE_EXPORT string getSetup(bool) const;

    /** Returns true when the loadplan is hidden.<br>
      * This is determined by looking at whether the load is hidden or not.
      */
    bool getHidden() const
    {
      return ld->getHidden();
    }

    /** Each operationplan has 2 loadplans per load: one at the start,
      * when the capacity consumption starts, and one at the end, when the
      * capacity consumption ends.<br>
      * This method returns the "companion" loadplan. It is not very
      * scalable: the performance is linear with the number of loadplans
      * on the resource.
      */
    DECLARE_EXPORT LoadPlan* getOtherLoadPlan() const;

    static int initialize();
    static DECLARE_EXPORT const MetaCategory* metadata;
    virtual const MetaClass& getType() const { return *metadata; }

    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addDateField<Cls>(Tags::date, &Cls::getDate);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity);
      m->addDoubleField<Cls>(Tags::onhand, &Cls::getOnhand);
      m->addDoubleField<Cls>(Tags::minimum, &Cls::getMin);
      m->addDoubleField<Cls>(Tags::maximum, &Cls::getMax);
      m->addPointerField<Cls, OperationPlan>(Tags::operationplan, &Cls::getOperationPlan);
      m->addPointerField<Cls, Load>(Tags::load, &Cls::getLoad, &Cls::setLoad, DONT_SERIALIZE);
      m->addPointerField<Cls, Resource>(Tags::resource, &Cls::getResource, &Cls::setResource, DONT_SERIALIZE);
      m->addBoolField<Cls>(Tags::hidden, &Cls::getHidden, NULL, BOOL_FALSE, DONT_SERIALIZE);
      m->addDateField<Cls>(Tags::startdate, &Cls::getStartDate, NULL, Date::infiniteFuture, DONT_SERIALIZE);
      m->addDateField<Cls>(Tags::enddate, &Cls::getEndDate, NULL, Date::infiniteFuture, DONT_SERIALIZE);
      m->addPointerField<Cls, Operation>(Tags::operation, &Cls::getOperation, NULL, DONT_SERIALIZE);
      m->addStringField<Cls>(Tags::setup, &Cls::getSetup, NULL, "", DONT_SERIALIZE);
    }

  private:
    /** Private constructor. It is called from the public constructor.<br>
      * The public constructor constructs the starting loadplan, while this
      * constructor creates the ending loadplan.
      */
    DECLARE_EXPORT LoadPlan(OperationPlan*, const Load*, LoadPlan*);

    /** This type is used to differentiate loadplans aligned with the START date
      * or the END date of operationplan. */
    enum type {START, END};

    /** Is this loadplan a starting one or an ending one. */
    type start_or_end;

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
};


inline Date Load::getLoadplanDate(const LoadPlan* lp) const
{
  const DateRange & dr = lp->getOperationPlan()->getDates();
  if (lp->isStart())
    return dr.getStart() > getEffective().getStart() ?
        dr.getStart() :
        getEffective().getStart();
  else
    return dr.getEnd() < getEffective().getEnd() ?
        dr.getEnd() :
        getEffective().getEnd();
}


inline double Load::getLoadplanQuantity(const LoadPlan* lp) const
{
  if (!lp->getOperationPlan()->getQuantity())
    // Operationplan has zero size, and so should the capacity it needs
    return 0.0;
  if (!lp->getOperationPlan()->getDates().overlap(getEffective())
      && (lp->getOperationPlan()->getDates().getDuration()
          || !getEffective().within(lp->getOperationPlan()->getDates().getStart())))
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
      while (i && i->getEventType() == 1 && i->getQuantity() >= 0)
        i = iter.next();
      return i ? static_cast<LoadPlan*>(i)->getOperationPlan() : NULL;
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
    explicit DECLARE_EXPORT EntityIterator();

    /** Used to create an iterator pointing beyond the last HasProblems
      * object. */
    explicit EntityIterator(unsigned short i) : bufIter(NULL), type(i) {}

    /** Copy constructor. */
    DECLARE_EXPORT EntityIterator(const EntityIterator&);

    /** Assignment operator. */
    DECLARE_EXPORT EntityIterator& operator=(const EntityIterator&);

    /** Destructor. */
    DECLARE_EXPORT ~EntityIterator();

    /** Pre-increment operator. */
    DECLARE_EXPORT EntityIterator& operator++();

    /** Inequality operator.<br>
      * Two iterators are different when they point to different objects.
      */
    DECLARE_EXPORT bool operator != (const EntityIterator& t) const;

    /** Equality operator.<br>
      * Two iterators are equal when they point to the same object.
      */
    bool operator == (const EntityIterator& t) const
    {
      return !(*this != t);
    }

    /** Dereference operator. */
    DECLARE_EXPORT HasProblems& operator*() const;

    /** Dereference operator. */
    DECLARE_EXPORT HasProblems* operator->() const;
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
  private:
    /** A pointer to the current problem. If this pointer is NULL, we are
      * at the end of the list. */
    Problem* iter;
    HasProblems* owner;
    HasProblems::EntityIterator *eiter;

  public:
    /** Creates an iterator that will loop through the problems of a
      * single entity only. <BR>
      * This constructor is also used to create a end-iterator, when passed
      * a NULL pointer as argument.
      */
    explicit iterator(HasProblems* o) : iter(o ? o->firstProblem : NULL),
      owner(o), eiter(NULL) {}

    /** Creates an iterator that will loop through the constraints of
      * a demand.
      */
    explicit iterator(Problem* o) : iter(o), owner(NULL), eiter(NULL) {}

    /** Creates an iterator that will loop through the problems of all
      * entities. */
    DECLARE_EXPORT explicit iterator() : owner(NULL)
    {
      // Update problems
      Plannable::computeProblems();

      // Loop till we find an entity with a problem
      eiter = new HasProblems::EntityIterator();
      while (*eiter != HasProblems::endEntity() && !((*eiter)->firstProblem))
        ++(*eiter);
      // Found a first problem, or no problem at all
      iter = (*eiter != HasProblems::endEntity()) ? (*eiter)->firstProblem : NULL;
    }

    /** Copy constructor. */
    DECLARE_EXPORT iterator(const iterator& i) : iter(i.iter), owner(i.owner)
    {
      if (i.eiter)
        eiter = new HasProblems::EntityIterator(*(i.eiter));
      else
        eiter = NULL;
    }

    /** Destructor. */
    DECLARE_EXPORT ~iterator()
    {
      if (eiter)
        delete eiter;
    }

    /** Pre-increment operator. */
    DECLARE_EXPORT iterator& operator++();

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
  return Problem::iterator(static_cast<Problem*>(NULL));
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

    /** Pointer to the singleton plan object. */
    static DECLARE_EXPORT Plan* thePlan;

    /** The only constructor of this class is made private. An object of this
      * class is created by the instance() member function.
      */
    Plan() : cur_Date(Date::now())
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
    DECLARE_EXPORT ~Plan();

    /** Returns the plan name. */
    string getName() const
    {
      return name;
    }

    /** Updates the plan name. */
    DECLARE_EXPORT void setName(const string& s)
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
    DECLARE_EXPORT void setCurrent(Date);

    /** Returns the description of the plan. */
    string getDescription() const
    {
      return descr;
    }

    /** Updates the description of the plan. */
    DECLARE_EXPORT void setDescription(const string& str)
    {
      descr = str;
    }

    DECLARE_EXPORT void setLogFile(const string& s)
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
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

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

    const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;

    template<class Cls>static inline void registerFields(MetaClass* m)
    {
      m->addStringField<Plan>(Tags::name, &Plan::getName, &Plan::setName);
      m->addStringField<Plan>(Tags::description, &Plan::getDescription, &Plan::setDescription);
      m->addDateField<Plan>(Tags::current, &Plan::getCurrent, &Plan::setCurrent);
      m->addStringField<Plan>(Tags::logfile, &Plan::getLogFile, &Plan::setLogFile, "", DONT_SERIALIZE);
      Plannable::registerFields<Plan>(m);
      m->addIteratorField<Plan, Location::iterator, Location>(Tags::locations, Tags::location, &Plan::getLocations);
      m->addIteratorField<Plan, Customer::iterator, Customer>(Tags::customers, Tags::customer, &Plan::getCustomers);
      m->addIteratorField<Plan, Supplier::iterator, Supplier>(Tags::suppliers, Tags::supplier, &Plan::getSuppliers);
      m->addIteratorField<Plan, Calendar::iterator, Calendar>(Tags::calendars, Tags::calendar, &Plan::getCalendars);
      m->addIteratorField<Plan, Resource::iterator, Resource>(Tags::resources, Tags::resource, &Plan::getResources);
      m->addIteratorField<Plan, Item::iterator, Item>(Tags::items, Tags::item, &Plan::getItems);
      m->addIteratorField<Plan, Buffer::iterator, Buffer>(Tags::buffers, Tags::buffer, &Plan::getBuffers);
      m->addIteratorField<Plan, Operation::iterator, Operation>(Tags::operations, Tags::operation, &Plan::getOperations);
      m->addIteratorField<Plan, Demand::iterator, Demand>(Tags::demands, Tags::demand, &Plan::getDemands);
      m->addIteratorField<Plan, SetupMatrix::iterator, SetupMatrix>(Tags::setupmatrices, Tags::setupmatrix, &Plan::getSetupMatrices);
      m->addIteratorField<Plan, Skill::iterator, Skill>(Tags::skills, Tags::skill, &Plan::getSkills);
      m->addIteratorField<Plan, Resource::skilllist::iterator, ResourceSkill>(Tags::resourceskills, Tags::resourceskill); // Only for XML import
      m->addIteratorField<Plan, Operation::loadlist::iterator, Load>(Tags::loads, Tags::load); // Only for XML import
      m->addIteratorField<Plan, Operation::flowlist::iterator, Flow>(Tags::flows, Tags::flow); // Only for XML import
      m->addIteratorField<Plan, Item::supplierlist::iterator, ItemSupplier>(Tags::itemsuppliers, Tags::itemsupplier); // Only for XML import
      m->addIteratorField<Plan, Location::distributionoriginlist::iterator, ItemDistribution>(Tags::itemdistributions, Tags::itemdistribution);
      m->addIteratorField<Cls, OperationPlan::iterator, OperationPlan>(Tags::operationplans, Tags::operationplan, &Plan::getOperationPlans);
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
      return oper ? state.quantity : static_cast<OperationPlan*>(getOwner())->getQuantity();
    }

    explicit ProblemBeforeCurrent(OperationPlan* o, bool add = true) : Problem(o), oper(NULL)
    {
      if (add) addProblem();
    }

    explicit ProblemBeforeCurrent(Operation* o, Date st, Date nd, double q)
      : oper(o), state(st, nd, q) {}

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
      if (oper) return DateRange(state.start, state.end);
      OperationPlan *o = static_cast<OperationPlan*>(getOwner());
      if (o->getDates().getEnd() > Plan::instance().getCurrent())
        return DateRange(o->getDates().getStart(),
            Plan::instance().getCurrent());
      else
        return DateRange(o->getDates().getStart(),
            o->getDates().getEnd());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass* metadata;

  private:
    Operation* oper;
    OperationPlanState state;
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
      return oper ? state.quantity : static_cast<OperationPlan*>(getOwner())->getQuantity();
    }

    explicit ProblemBeforeFence(OperationPlan* o, bool add = true)
      : Problem(o), oper(NULL)
    {
      if (add) addProblem();
    }

    explicit ProblemBeforeFence(Operation* o, Date st, Date nd, double q)
      : oper(o), state(st, nd, q) {}

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
      if (oper) return DateRange(state.start, state.end);
      OperationPlan *o = static_cast<OperationPlan*>(owner);
      if (o->getDates().getEnd() > Plan::instance().getCurrent()
          + o->getOperation()->getFence())
        return DateRange(o->getDates().getStart(),
            Plan::instance().getCurrent() + o->getOperation()->getFence());
      else
        return DateRange(o->getDates().getStart(),
            o->getDates().getEnd());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass* metadata;

  private:
    Operation* oper;
    OperationPlanState state;
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
      if (!o->nextsubopplan)
        return string("Bogus precedence problem on '")
            + o->getOperation()->getName() + "'";
      else
        return string("Operation '") + o->getOperation()->getName()
            + "' starts before operation '"
            + o->nextsubopplan->getOperation()->getName() +"' ends";
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
      return DateRange(o->nextsubopplan->getDates().getStart(),
          o->getDates().getEnd());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass* metadata;
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
    static DECLARE_EXPORT const MetaClass* metadata;
};


/** @brief A problem of this class is created when a demand is satisfied later
  * than the accepted tolerance after its due date.
  */
class ProblemLate : public Problem
{
  public:
    DECLARE_EXPORT string getDescription() const;
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
          getDemand()->getLatestDelivery()->getDates().getEnd()
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
          getDemand()->getLatestDelivery()->getDates().getEnd());
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
    static DECLARE_EXPORT const MetaClass* metadata;
};


/** @brief A problem of this class is created when a demand is planned earlier
  * than the accepted tolerance before its due date.
  */
class ProblemEarly : public Problem
{
  public:
    DECLARE_EXPORT string getDescription() const;

    bool isFeasible() const
    {
      return true;
    }

    double getWeight() const
    {
      assert(getDemand() && !getDemand()->getDelivery().empty());
      return static_cast<double>(DateRange(
          getDemand()->getDue(),
          getDemand()->getEarliestDelivery()->getDates().getEnd()
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
          getDemand()->getEarliestDelivery()->getDates().getEnd());
    }

    Demand* getDemand() const
    {
      return static_cast<Demand*>(getOwner());
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass* metadata;
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
      if (entity == "demand") return static_cast<Demand*>(owner);
      if (entity == "buffer") return static_cast<Buffer*>(owner);
      if (entity == "resource") return static_cast<Resource*>(owner);
      if (entity == "operation") return static_cast<Operation*>(owner);
      throw LogicException("Unknown problem entity type");
    }

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return *metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass* metadata;

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
    static DECLARE_EXPORT const MetaClass* metadata;
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
    static DECLARE_EXPORT const MetaClass* metadata;
};


/** @brief A problem of this class is created when a resource is being
  * overloaded during a certain period of time.
  */
class ProblemCapacityOverload : public Problem
{
  public:
    DECLARE_EXPORT string getDescription() const;

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
    static DECLARE_EXPORT const MetaClass* metadata;

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
    DECLARE_EXPORT string getDescription() const;

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
    static DECLARE_EXPORT const MetaClass* metadata;

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
    DECLARE_EXPORT string getDescription() const;

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
    static DECLARE_EXPORT const MetaClass* metadata;

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
    DECLARE_EXPORT string getDescription() const;

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
    static DECLARE_EXPORT const MetaClass* metadata;

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
     OperationPlan* ow=NULL, bool makeflowsloads=true)
    {
      opplan = o ?
          o->createOperationPlan(q, d1, d2, l, ow, 0, makeflowsloads)
          : NULL;
    }

    void commit()
    {
      if (opplan)
      {
        opplan->activate();
        opplan = NULL; // Avoid executing / initializing more than once
      }
    }

    virtual void rollback()
    {
      delete opplan;
      opplan = NULL;
    }

    virtual void undo()
    {
      if (opplan) opplan->deleteFlowLoads();
    }

    virtual void redo()
    {
      if (opplan) opplan->createFlowLoads();
    }

    virtual ~CommandCreateOperationPlan()
    {
      if (opplan) delete opplan;
    }

    OperationPlan *getOperationPlan() const
    {
      return opplan;
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
    DECLARE_EXPORT CommandDeleteOperationPlan(OperationPlan* o);

    virtual void commit()
    {
      if (opplan) delete opplan;
      opplan = NULL;
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
        i->createFlowLoads();
        i->insertInOperationplanList();
      }
    }

    virtual void redo()
    {
      if (!opplan) return;
      opplan->deleteFlowLoads();
      opplan->removeFromOperationplanList();
      if (opplan->getDemand())
        opplan->getDemand()->removeDelivery(opplan);
      OperationPlan::iterator x(opplan);
      while (OperationPlan* i = x.next())
      {
        i->deleteFlowLoads();
        i->removeFromOperationplanList();
      }
    }

    virtual void rollback()
    {
      undo();
      opplan = NULL;
    }

    virtual ~CommandDeleteOperationPlan()
    {
      undo();
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
    DECLARE_EXPORT CommandMoveOperationPlan(OperationPlan* opplanptr,
        Date newStart, Date newEnd, double newQty = -1.0);

    /** Default constructor. */
    DECLARE_EXPORT CommandMoveOperationPlan(OperationPlan*);

    /** Commit the changes. */
    virtual void commit()
    {
      opplan=NULL;
    }

    /** Undo the changes. */
    virtual void rollback()
    {
      restore(true); opplan = NULL;
    }

    virtual void undo()
    {
      restore(false);
    }

    virtual DECLARE_EXPORT void redo();

    /** Undo the changes.<br>
      * When the argument is true, subcommands for suboperationplans are deleted. */
    DECLARE_EXPORT void restore(bool = false);

    /** Destructor. */
    virtual ~CommandMoveOperationPlan()
    {
      if (opplan) rollback();
    }

    /** Returns the operationplan being manipulated. */
    OperationPlan* getOperationPlan() const
    {
      return opplan;
    }

    /** Set another start date for the operationplan. */
    void setStart(Date d)
    {
      if (opplan) opplan->setStart(d);
    }

    /** Set another start date, end date and quantity for the operationplan. */
    void setParameters(Date s, Date e, double q, bool b)
    {
      assert(opplan->getOperation());
      if (opplan)
        opplan->getOperation()->setOperationPlanParameters(opplan, q, s, e, b);
    }

    /** Set another start date for the operationplan. */
    void setEnd(Date d)
    {
      if (opplan) opplan->setEnd(d);
    }

    /** Set another quantity for the operationplan. */
    void setQuantity(double q)
    {
      if (opplan) opplan->setQuantity(q);
    }

    /** Return the quantity of the original operationplan. */
    double getQuantity() const
    {
      return originalqty;
    }

    /** Return the dates of the original operationplan. */
    DateRange getDates() const
    {
      return originaldates;
    }

  private:
    /** This is a pointer to the operationplan being moved. */
    OperationPlan *opplan;

    /** These are the original dates of the operationplan before its move. */
    DateRange originaldates;

    /** This is the quantity of the operationplan before the command. */
    double originalqty;

    /** A pointer to a list of suboperationplan commands. */
    Command* firstCommand;
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
    DECLARE_EXPORT PeggingIterator(const PeggingIterator& c);

    /** Constructor for demand pegging. */
    DECLARE_EXPORT PeggingIterator(const Demand*);

    /** Constructor for operationplan pegging. */
    DECLARE_EXPORT PeggingIterator(const OperationPlan*, bool=true);

    /** Constructor for flowplan pegging. */
    DECLARE_EXPORT PeggingIterator(FlowPlan*, bool=true);

    /** Constructor for loadplan pegging. */
    DECLARE_EXPORT PeggingIterator(LoadPlan*, bool=true);

    /** Return the operationplan. */
    OperationPlan* getOperationPlan() const
    {
      return const_cast<OperationPlan*>(states.back().opplan);
    }

    /** Destructor. */
    DECLARE_EXPORT virtual ~PeggingIterator() {}

    /** Return true if this is a downstream iterator. */
    inline bool isDownstream() const
    {
      return downstream;
    }

    /** Return the pegged quantity. */
    double getQuantity() const
    {
      return states.back().quantity;
    }

    /** Returns the recursion depth of the iterator.*/
    short getLevel() const
    {
      return states.back().level;
    }

    /** Move the iterator downstream. */
    DECLARE_EXPORT PeggingIterator& operator++();

    /** Move the iterator upstream. */
    DECLARE_EXPORT PeggingIterator& operator--();

    /** Conversion operator to a boolean value.
      * The return value is true when the iterator still has next elements to
      * explore. Returns false when the iteration is finished.
      */
    operator bool() const
    {
      return !states.empty();
    }

    DECLARE_EXPORT PeggingIterator* next();

    /** Add an entry on the stack. */
    DECLARE_EXPORT void updateStack(const OperationPlan*, double, double, short);

    /** Initialize the class. */
    static int initialize();

    virtual const MetaClass& getType() const {return *metadata;}
    static DECLARE_EXPORT const MetaCategory* metadata;


    template<class Cls> static inline void registerFields(MetaClass* m)
    {
      m->addPointerField<Cls, OperationPlan>(Tags::operationplan, &Cls::getOperationPlan, NULL, MANDATORY + WRITE_FULL);
      m->addDoubleField<Cls>(Tags::quantity, &Cls::getQuantity, NULL, MANDATORY);
      m->addShortField<Cls>(Tags::level, &Cls::getLevel, NULL, MANDATORY);
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
    };
    typedef vector<state> statestack;

    /* Auxilary function to make recursive code possible. */
    DECLARE_EXPORT void followPegging(const OperationPlan*, double, double, short);

    /** Store a list of all operations still to peg. */
    statestack states;

    /** Follow the pegging upstream or downstream. */
    bool downstream;

    /** Used by the Python iterator to mark the first call. */
    bool firstIteration;

    /** Optimization to reuse elements on the stack. */
    bool first;
};


/** @brief An iterator class to go through all flowplans of an operationplan.
  * @see OperationPlan::beginFlowPlans
  * @see OperationPlan::endFlowPlans
  */
class OperationPlan::FlowPlanIterator
{
    friend class OperationPlan;
  private:
    FlowPlan* curflowplan;
    FlowPlan* prevflowplan;

    FlowPlanIterator(FlowPlan* b) : curflowplan(b), prevflowplan(NULL) {}

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
      if (!curflowplan) return;
      if (prevflowplan) prevflowplan->nextFlowPlan = curflowplan->nextFlowPlan;
      else curflowplan->oper->firstflowplan = curflowplan->nextFlowPlan;
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
  return OperationPlan::FlowPlanIterator(NULL);
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
    LoadPlan* curloadplan;
    LoadPlan* prevloadplan;
    LoadPlanIterator(LoadPlan* b) : curloadplan(b), prevloadplan(NULL) {}
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
  return OperationPlan::LoadPlanIterator(NULL);
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


class CalendarEventIterator
  : public PythonExtension<CalendarEventIterator>
{
  public:
    static int initialize();

    CalendarEventIterator(Calendar* c, Date d=Date::infinitePast, bool f=true)
      : cal(c), eventiter(c,d,f), forward(f) {}

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
        throw LogicException("Creating flowplan iterator for NULL buffer");
      bufiter = new Buffer::flowplanlist::const_iterator(b->getFlowPlans().begin());
    }

    /** Constructor to iterate over the flowplans of an operationplan. */
    FlowPlanIterator(OperationPlan* o) : opplan(o), buffer_or_opplan(false)
    {
      if (!o)
        throw LogicException("Creating flowplan iterator for NULL operationplan");
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
        throw LogicException("Creating loadplan iterator for NULL resource");
      resiter = new Resource::loadplanlist::const_iterator(r->getLoadPlans().begin());
    }

    LoadPlanIterator(OperationPlan* o) : opplan(o), resource_or_opplan(false)
    {
      if (!opplan)
        throw LogicException("Creating loadplan iterator for NULL operationplan");
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
DECLARE_EXPORT PyObject* readXMLfile(PyObject*, PyObject*);


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
DECLARE_EXPORT PyObject* readXMLdata(PyObject *, PyObject *);


/** @brief This Python function writes the dynamic part of the plan to an text file.
  *
  * This saved information covers the buffer flowplans, operationplans,
  * resource loading, demand, problems, etc...<br>
  * The main use of this function is in the test suite: a simple text file
  * comparison allows us to identify changes quickly. The output format is
  * only to be seen in this context of testing, and is not intended to be used
  * as an official method for publishing plans to other systems.
  */
DECLARE_EXPORT PyObject* savePlan(PyObject*, PyObject*);


/** @brief This Python function prints a summary of the dynamically allocated
  * memory to the standard output. This is useful for understanding better the
  * size of your model.
  *
  * The numbers reported by this function won't match the memory size as
  * reported by the operating system, since the dynamically allocated memory
  * is only a part of the total memory used by a program.
  */
DECLARE_EXPORT PyObject* printModelSize(PyObject* self, PyObject* args);


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
DECLARE_EXPORT PyObject* saveXMLfile(PyObject*, PyObject*);


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
DECLARE_EXPORT PyObject* eraseModel(PyObject* self, PyObject* args);


}   // End namespace

#endif
