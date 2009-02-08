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

#ifndef MODEL_H
#define MODEL_H

/** @mainpage frePPLe Library API
  * The frePPLe class library provides a framework for modeling a
  * manufacturing environment.<br>
  * This document describes its C++ API.<P>
  *
  * @namespace frepple
  * @brief Core namespace
  */

#include "frepple/utils.h"
#include "frepple/timeline.h"
#include <float.h>
using namespace frepple::utils;

namespace frepple
{

class Flow;
class FlowEnd;
class FlowPlan;
class LoadPlan;
class Resource;
class ResourceInfinite;
class Problem;
class Demand;
class OperationPlan;
class Item;
class Operation;
class OperationFixedTime;
class OperationTimePer;
class OperationRouting;
class OperationAlternate;
class Buffer;
class BufferInfinite;
class BufferProcure;
class Plan;
class Plannable;
class Calendar;
class Load;
class Location;
class Customer;
class HasProblems;
class Solvable;
class PeggingIterator;


/** @brief This class is used for initialization. */
class LibraryModel
{
  public:
    static void initialize();
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
class Calendar : public HasName<Calendar>, public Object
{
  public:
    class BucketIterator; // Forward declaration
    class EventIterator; // Forward declaration

    /** @brief This class represents a time bucket as a part of a calendar.
      *
      * Manipulation of instances of this class need to be handled with the
      * methods on the friend class Calendar.
      * @see Calendar
      */
    class Bucket : public Object, public NonCopyable
    {
        friend class Calendar;
        friend class BucketIterator;
        friend class EventIterator;
      private:
        /** Name of the bucket. */
        string nm;

        /** Start date of the bucket. */
        Date startdate;

        /** End Date of the bucket. */
        Date enddate;

        /** A pointer to the next bucket. */
        Bucket* nextBucket;

        /** A pointer to the previous bucket. */
        Bucket* prevBucket;

        /** Priority of this bucket, compared to other buckets effective 
          * at a certain time. 
          */
        int priority;
        
        /** Increments an iterator to the next change event.<br>
          * A bucket will evaluate the current state of the iterator, and
          * update it if a valid next event can be generated. 
          */
        DECLARE_EXPORT void nextEvent(EventIterator*, Date) const;

        /** Increments an iterator to the previous change event.<br>
          * A bucket will evaluate the current state of the iterator, and
          * update it if a valid previous event can be generated. 
          */
        DECLARE_EXPORT void prevEvent(EventIterator*, Date) const;

      protected:
        /** Constructor. */
        Bucket(Date start, Date end, string name) : nm(name), startdate(start),
          enddate(end), nextBucket(NULL), prevBucket(NULL), priority(0) {}
        
        /** Auxilary function to write out the start of the XML. */
        DECLARE_EXPORT void writeHeader(XMLOutput *) const;

      public:
        /** This method is here only to keep the API of all calendar classes
          * consistent.
          * Note that this isn't exactly a virtual method, since the return
          * value is different for different calendar types.
          */
        void getValue() const {}

        /** This method is here only to keep the API of all calendar classes
          * consistent.
          */
        void setValue() {}

        /** Returns the name of the bucket. If no name was ever explicitly
          * specified with the setName() method, a default name is generated
          * by converting the start date into a string.
          * To reduce the memory needs, this default string is computed with
          * every call to the getName() method and never stored internally.
          * Only explicitly specified names are kept in memory.
          */
        string getName() const {return nm.empty() ? string(startdate) : nm;}

        /** Returns true if the name of the bucket has not been explicitly
          * specified. */
        bool useDefaultName() const {return nm.empty();}

        /** Updates the name of a bucket. */
        void setName(const string& s) {nm=s;}

        /** Returns the end date of the bucket. */
        Date getEnd() const {return enddate;}

        /** Updates the end date of the bucket. */
        void setEnd(const Date& d) {enddate = d;}

        /** Returns the start date of the bucket. */
        Date getStart() const {return startdate;}

        /** Updates the end date of the bucket. */
        void setStart(const Date& d) {startdate = d;}

        /** Returns the priority of this bucket, compared to other buckets 
          * effective at a certain time.<br>
          * Lower numbers indicate a higher priority level.<br>
          * The default value is 0.
          */
        int getPriority() const {return priority;}

        /** Updates the priority of this bucket, compared to other buckets 
          * effective at a certain time.<br>
          * Lower numbers indicate a higher priority level.<br>
          * The default value is 0.
          */
        void setPriority(int f) {priority = f;}

        /** Verifies whether this entry is effective on a given date. */
        bool checkValid(Date d) const
        {
          return true;
        }

        virtual DECLARE_EXPORT void writeElement
          (XMLOutput*, const Keyword&, mode=DEFAULT) const;

        /** Reads the bucket information from the input. Only the fields "name"
          * and "start" are read in. Other fields as also written out but these
          * are information-only fields.
          */
        DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

        virtual const MetaClass& getType() const
          {return metadata;}
        virtual size_t getSize() const
          {return sizeof(Bucket) + nm.size();}
        static DECLARE_EXPORT const MetaCategory metadata;
    };

    /** Default constructor. */
    Calendar(const string& n) : HasName<Calendar>(n), firstBucket(NULL) {}

    /** Destructor, which cleans up the buckets too and all references to the 
      * calendar from the core model. 
      */
    DECLARE_EXPORT ~Calendar();

    /** This is a factory method that creates a new bucket using the start
      * date as the key field. The fields are passed as an array of character
      * pointers.<br>
      * This method is intended to be used to create objects when reading
      * XML input data.
      */
    DECLARE_EXPORT Bucket* createBucket(const AttributeList&);

    /** Adds a new bucket to the list. */
    DECLARE_EXPORT Bucket* addBucket(Date, Date, string);

    /** Removes a bucket from the list. */
    DECLARE_EXPORT void removeBucket(Bucket* bkt);

    /** Returns the bucket where a certain date belongs to.
      * A bucket will always be returned, i.e. the data structure is such
      * that we all dates between infinitePast and infiniteFuture match
      * with one (and only one) bucket.
      */
    DECLARE_EXPORT Bucket* findBucket(Date d) const;

    /** Returns the bucket with a certain name.
      * A NULL pointer is returned in case no bucket can be found with the
      * given name.
      */
    DECLARE_EXPORT Bucket* findBucket(const string&) const;

    /** @brief An iterator class to go through all dates where the calendar
      * value changes.*/
    class EventIterator
    {
      friend class Calendar::Bucket;
      protected:
        const Calendar* theCalendar;
        const Bucket* curBucket;
        Date curDate;
        double curPriority;
      public:
        const Date& getDate() const {return curDate;}
        const Bucket* getBucket() const {return curBucket;}
        EventIterator(const Calendar* c, Date d = Date::infinitePast) 
          : theCalendar(c), curDate(d) 
        {
          if (!c) 
            throw LogicException("Creating iterator for NULL calendar.");
          curBucket = c->findBucket(d);
        };
        DECLARE_EXPORT EventIterator& operator++();
        DECLARE_EXPORT EventIterator& operator--();
        EventIterator operator++(int)
          {EventIterator tmp = *this; ++*this; return tmp;}
        EventIterator operator--(int)
          {EventIterator tmp = *this; --*this; return tmp;}        
    };

    /** @brief An iterator class to go through all buckets of the calendar. */
    class BucketIterator
    {
      private:
        Bucket* curBucket;
      public:
        BucketIterator(Bucket* b = NULL) : curBucket(b) {}
        bool operator != (const BucketIterator &b) const
          {return b.curBucket != curBucket;}
        bool operator == (const BucketIterator &b) const
          {return b.curBucket == curBucket;}
        BucketIterator& operator++()
          { if (curBucket) curBucket = curBucket->nextBucket; return *this; }
        BucketIterator operator++(int)
          {BucketIterator tmp = *this; ++*this; return tmp;}
        BucketIterator& operator--()
          { if(curBucket) curBucket = curBucket->prevBucket; return *this; }
        BucketIterator operator--(int)
          {BucketIterator tmp = *this; --*this; return tmp;}
        Bucket* operator ->() const {return curBucket;}
        Bucket& operator *() const {return *curBucket;}
    };

    /** Returns an iterator to go through the list of buffers. */
    BucketIterator beginBuckets() const { return BucketIterator(firstBucket); }

    /** Returns an iterator to go through the list of buffers. */
    BucketIterator endBuckets() const {return BucketIterator(NULL);}

    DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement) {}
    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

    virtual size_t getSize() const
    {
      size_t i = sizeof(Calendar);
      for (BucketIterator j = beginBuckets(); j!= endBuckets(); ++j)
        i += j->getSize();
      return i;
    }

  private:
    /** A pointer to the first bucket. The buckets are stored in a doubly
      * linked list. */
    Bucket* firstBucket;

    /** This is the factory method used to generate new buckets. Each subclass
      * should provide an override for this function. */
    virtual Bucket* createNewBucket(Date start, Date end, string name) 
      {return new Bucket(start,end,name);}
};


/** @brief This calendar type is used to store values in its buckets.
  *
  * The template type must statisfy the following requirements:
  *   - XML import supported by the operator >> of the class DataElement.
  *   - XML export supported by the method writeElement of the class XMLOutput.
  * Subclasses will need to implement the getType() method.
  * @see CalendarPointer
  */
template <typename T> class CalendarValue : public Calendar
{
  public:
    /** @brief A special type of calendar bucket, designed to hold a
      * a value.
      * @see Calendar::Bucket
      */
    class BucketValue : public Calendar::Bucket
    {
        friend class CalendarValue<T>;
      private:
        /** This is the value stored in this bucket. */
        T val;

        /** Constructor. */
        BucketValue(Date start, Date end, string name, T& v) 
          : Bucket(start,end,name) {val = v;};

      public:
        /** Returns the value of this bucket. */
        const T& getValue() const {return val;}

        /** Updates the value of this bucket. */
        void setValue(const T& v) {val = v;}

        void writeElement
        (XMLOutput *o, const Keyword& tag, mode m = DEFAULT) const
        {
          assert(m == DEFAULT || m == FULL);
          writeHeader(o);
          if (getPriority()) o->writeElement(Tags::tag_priority, getPriority());
          o->writeElement(Tags::tag_value, val);
          o->EndObject(tag);
        }

        void endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
        {
          if (pAttr.isA(Tags::tag_value))
            pElement >> val;
          else
            Bucket::endElement(pIn, pAttr, pElement);
        }

        virtual const MetaClass& getType() const
          {return Calendar::Bucket::metadata;}

        virtual size_t getSize() const
          {return sizeof(typename CalendarValue<T>::BucketValue) + getName().size();}
    };

    /** @brief A special event iterator, providing also access to the 
      * current value. */
    class EventIterator : public Calendar::EventIterator
    {
      public:
        /** Constructor. */
        EventIterator(const Calendar* c, Date d = Date::infinitePast) 
          : Calendar::EventIterator(c,d) {}

        /** Return the current value of the iterator at this date. */
        T getValue() 
        {
          typedef CalendarValue<T> calendarvaluetype;
          typedef typename CalendarValue<T>::BucketValue bucketvaluetype;
          return curBucket ? 
            static_cast<const bucketvaluetype*>(curBucket)->getValue() : 
            static_cast<const calendarvaluetype*>(theCalendar)->getDefault();
        }
    };

    /** Default constructor. */
    CalendarValue(const string& n) : Calendar(n) {}

    /** Returns the value on the specified date. */
    const T& getValue(const Date d) const
    {
      BucketValue* x = static_cast<BucketValue*>(findBucket(d));
      return x ? x->getValue() : defaultValue;
    }

    /** Updates the value in a certain time bucket. */
    void setValue(Date start, Date end, const T& v)
    {
      // @todo logic for setValue(start,end,value) not implemented - see python implementation
    }

    virtual const MetaClass& getType() const = 0;

    const T& getValue(Calendar::BucketIterator& i) const
      {return reinterpret_cast<BucketValue&>(*i).getValue();}
  
    /** Returns the default calendar value when no entry is matching. */
    virtual T getDefault() const {return defaultValue;}
  
    /** Update the default calendar value when no entry is matching. */
    virtual void setDefault(const T v) {defaultValue = v;}

    void writeElement(XMLOutput *o, const Keyword& tag, mode m) const
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

      // Write my own fields
      o->writeElement(Tags::tag_default, getDefault());

      // Write all buckets
      o->BeginObject (Tags::tag_buckets);
      for (BucketIterator i = beginBuckets(); i != endBuckets(); ++i)
        // We use the FULL mode, to force the buckets being written regardless
        // of the depth in the XML tree.
        o->writeElement(Tags::tag_bucket, *i, FULL);
      o->EndObject(Tags::tag_buckets);

      o->EndObject(tag);
    }

    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
    {
      if (pAttr.isA(Tags::tag_default))
        pElement >> defaultValue;
      else
        Calendar::endElement(pIn, pAttr, pElement);
    }

  private:
    /** Factory method to add new buckets to the calendar.
      * @see Calendar::addBucket()
      */
    Bucket* createNewBucket(Date start, Date end, string name) 
      {return new BucketValue(start,end,name,defaultValue);}

    /** Value when no bucket is matching a certain date. */
    T defaultValue;
};


/** @brief This calendar type is used to store object pointers in its buckets.
  *
  * The template type must statisfy the following requirements:
  *   - It must be a subclass of the Object class and implement the
  *     beginElement(), writeElement() and endElement() as appropriate.
  *   - Implement a metadata data element
  * Subclasses will need to implement the getType() method.
  * @see CalendarValue
  */
template <typename T> class CalendarPointer : public Calendar
{
  public:
    /** @brief A special type of calendar bucket, designed to hold a pointer
      * to an object.
      * @see Calendar::Bucket
      */
    class BucketPointer : public Calendar::Bucket
    {
        friend class CalendarPointer<T>;
      private:
        /** The object stored in this bucket. */
        T* val;

        /** Constructor. */
        BucketPointer(Date start, Date end, string name, T* v) 
          : Bucket(start,end,name), val(v) {};

      public:
        /** Returns the value stored in this bucket. */
        T* getValue() const {return val;}

        /** Updates the value of this bucket. */
        void setValue(T* v) {val = v;}

        void writeElement
        (XMLOutput *o, const Keyword& tag, mode m = DEFAULT) const
        {
          assert(m == DEFAULT || m == FULL);
          writeHeader(o);
          if (getPriority()) o->writeElement(Tags::tag_priority, getPriority());
          if (val) o->writeElement(Tags::tag_value, val);
          o->EndObject(tag);
        }

        void beginElement(XMLInput& pIn, const Attribute& pAttr)
        {
          if (pAttr.isA(Tags::tag_value))
            pIn.readto(
              MetaCategory::ControllerDefault(T::metadata,pIn.getAttributes())
            );
          else
            Bucket::beginElement(pIn, pAttr);
        }

        void endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
        {
          if (pAttr.isA(Tags::tag_value))
          {
            T *o = dynamic_cast<T*>(pIn.getPreviousObject());
            if (!o)
              throw LogicException
              ("Incorrect object type during read operation");
            val = o;
          }
          else
            Bucket::endElement(pIn, pAttr, pElement);
        }

        virtual const MetaClass& getType() const
          {return Calendar::Bucket::metadata;}

        virtual size_t getSize() const
          {return sizeof(typename CalendarPointer<T>::BucketPointer) + getName().size();}
    };

    /** @brief A special event iterator, providing also access to the 
      * current value. */
    class EventIterator : public Calendar::EventIterator
    {
      public:
        /** Constructor. */
        EventIterator(const Calendar* c, Date d = Date::infinitePast) 
          : Calendar::EventIterator(c,d) {}

        /** Return the current value of the iterator at this date. */
        const T* getValue() 
        {
          typedef CalendarPointer<T> calendarpointertype;
          typedef typename CalendarPointer<T>::BucketPointer bucketpointertype;
          return curBucket ? 
            static_cast<const bucketpointertype*>(curBucket)->getValue() : 
            static_cast<const calendarpointertype*>(theCalendar)->getDefault();
        }
    };
    /** Default constructor. */
    CalendarPointer(const string& n) : Calendar(n), defaultValue(NULL) {}

    /** Returns the value on the specified date. */
    T* getValue(const Date d) const
    {
      BucketPointer* x = static_cast<BucketPointer*>(findBucket(d));
      return x ? x->getValue() : defaultValue;
    }

    /** Updates the value in a certain time bucket. */
    void setValue(const Date d, T* v)
    {
      BucketPointer* x = static_cast<BucketPointer*>(findBucket(d));
      if (x) x->setValue(v);
      else defaultValue = x;
    }

    /** Returns the default calendar value when no entry is matching. */
    virtual T* getDefault() const {return defaultValue;}
  
    /** Update the default calendar value when no entry is matching. */
    virtual void setDefault(T* v) {defaultValue = v;}

    virtual const MetaClass& getType() const = 0;

    void writeElement(XMLOutput *o, const Keyword& tag, mode m) const
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

      // Write my own fields
      if (defaultValue) o->writeElement(Tags::tag_default, defaultValue);

      // Write all buckets
      o->BeginObject (Tags::tag_buckets);
      for (BucketIterator i = beginBuckets(); i != endBuckets(); ++i)
        // We use the FULL mode, to force the buckets being written regardless
        // of the depth in the XML tree.
        o->writeElement(Tags::tag_bucket, *i, FULL);
      o->EndObject(Tags::tag_buckets);

      o->EndObject(tag);
    }

    void beginElement (XMLInput& pIn, const Attribute& pAttr)
    {
      if (pAttr.isA (Tags::tag_default))
        pIn.readto(T::reader(T::metadata,pIn.getAttributes()));
      else
        Calendar::beginElement(pIn, pAttr);
    }

    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
    {
      if (pAttr.isA(Tags::tag_default))
      {
        T *o = dynamic_cast<T*>(pIn.getPreviousObject());
        if (!o)
          throw LogicException
            ("Incorrect object type during read operation");
        defaultValue = o;
      }
      else
        Calendar::endElement(pIn, pAttr, pElement); 
    }

  private:
    /** Factory method to add new buckets to the calendar.
      * @see Calendar::addBucket()
      */
    Bucket* createNewBucket(Date start, Date end, string name) 
      {return new BucketPointer(start,end,name,defaultValue);}

    /** Value when no bucket is matching a certain date. */
    T* defaultValue;
};


/** @brief A calendar only defining time buckets and not storing any data
  * fields. */
class CalendarVoid : public Calendar
{
  public:
    CalendarVoid(const string& n) : Calendar(n) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing double values in its buckets. */
class CalendarDouble : public CalendarValue<double>
{
  public:
    CalendarDouble(const string& n) : CalendarValue<double>(n) 
      { setDefault(0.0); }
    DECLARE_EXPORT ~CalendarDouble();
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing integer values in its buckets. */
class CalendarInt : public CalendarValue<int>
{
  public:
    CalendarInt(const string& n) : CalendarValue<int>(n)
      { setDefault(0); }
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing boolean values in its buckets. */
class CalendarBool : public CalendarValue<bool>
{
  public:
    CalendarBool(const string& n) : CalendarValue<bool>(n) 
      { setDefault(false); }
    DECLARE_EXPORT ~CalendarBool();
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing strings in its buckets. */
class CalendarString : public CalendarValue<string>
{
  public:
    CalendarString(const string& n) : CalendarValue<string>(n) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {
      size_t i = sizeof(CalendarString);
      for (BucketIterator j = beginBuckets(); j!= endBuckets(); ++j)
        i += j->getSize()
            + static_cast<CalendarValue<string>::BucketValue&>(*j).getValue().size();
      return i;
    }
};


/** @brief A calendar storing pointers to operations in its buckets. */
class CalendarOperation : public CalendarPointer<Operation>
{
  public:
    CalendarOperation(const string& n) : CalendarPointer<Operation>(n) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
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
  *  - Given the above, Problems are lightweight objects that consume
  *    limited memory.
  */
class Problem : public NonCopyable, public Object
{
  public:
    class const_iterator;
    friend class const_iterator;
    
    /** Constructor.
      * Note that this method can't manipulate the problem container, since
      * the problem objects aren't fully constructed yet.
      * @see addProblem
      */
    explicit Problem(HasProblems *p) : owner(p)
      { if (!owner) throw LogicException("Invalid problem creation");}

    /** Destructor.
      * @see removeProblem
      */
    virtual ~Problem() {}

    /** Returns the duration of this problem. */
    virtual const DateRange getDateRange() const = 0;

    /** Returns a text description of this problem. */
    virtual string getDescription() const = 0;

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

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    void endElement(XMLInput&, const Attribute&, const DataElement&) {}
    static DECLARE_EXPORT void writer(const MetaCategory&, XMLOutput*);

    /** Returns an iterator to the very first problem. The iterator can be
      * incremented till it points past the very last problem. */
    static DECLARE_EXPORT const_iterator begin();

    /** Return an iterator to the first problem of this entity. The iterator
      * can be incremented till it points past the last problem of this
      * plannable entity.<br>
      * The boolean argument specifies whether the problems need to be
      * recomputed as part of this method.
      */
    static DECLARE_EXPORT const_iterator begin(HasProblems*, bool = true);

    /** Return an iterator pointing beyond the last problem. */
    static DECLARE_EXPORT const const_iterator end();

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

    /** Returns a pointer to the plannable object that owns this problem. */
    HasProblems* getOwner() const {return owner;}

    /** Return a reference to the metadata structure. */
    virtual const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaCategory metadata;

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
    friend class Problem::const_iterator;
    friend class Problem;
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
    virtual ~HasProblems() {Problem::clearProblems(*this, false);}

    /** Returns the plannable entity relating to this problem container. */
    virtual Plannable* getEntity() const = 0;

    /** Called to update the list of problems. The function will only be
      * called when:
      *  - the list of problems is being recomputed
      *  - AND, problem detection is enabled for this object
      *  - AND, the object has changed since the last problem computation
      */
    virtual void updateProblems() = 0;

  private:
    /** A pointer to the first problem of this object. Problems are maintained
      * in a single linked list. */
    Problem* firstProblem;
};


/** @brief This class is an implementation of the "visitor" design pattern.
  * It is intended as a basis for different algoritms processing the frePPLe
  * data.
  *
  * The goal is to decouple the solver/algorithms from the model/data
  * representation. Different solvers can be easily be plugged in to work on
  * the same data.
  */
class Solver : public Object, public HasName<Solver>
{
  public:
    explicit Solver(const string& n) : HasName<Solver>(n), loglevel(0) {}
    virtual ~Solver() {}

    virtual DECLARE_EXPORT void writeElement (XMLOutput*, const Keyword&, mode=DEFAULT) const;
    virtual DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

    virtual void solve(void* = NULL) = 0;
    virtual void solve(const Demand*,void* = NULL)
      {throw LogicException("Called undefined solve(Demand*) method");}
    virtual void solve(const Operation*,void* = NULL)
      {throw LogicException("Called undefined solve(Operation*) method");}
    virtual void solve(const OperationFixedTime* o, void* v = NULL)
      {solve(reinterpret_cast<const Operation*>(o),v);}
    virtual void solve(const OperationTimePer* o, void* v = NULL)
      {solve(reinterpret_cast<const Operation*>(o),v);}
    virtual void solve(const OperationRouting* o, void* v = NULL)
      {solve(reinterpret_cast<const Operation*>(o),v);}
    virtual void solve(const OperationAlternate* o, void* v = NULL)
      {solve(reinterpret_cast<const Operation*>(o),v);}
    virtual void solve(const Resource*,void* = NULL)
      {throw LogicException("Called undefined solve(Resource*) method");}
    virtual void solve(const ResourceInfinite* r, void* v = NULL)
      {solve(reinterpret_cast<const Resource*>(r),v);}
    virtual void solve(const Buffer*,void* = NULL)
      {throw LogicException("Called undefined solve(Buffer*) method");}
    virtual void solve(const BufferInfinite* b, void* v = NULL)
      {solve(reinterpret_cast<const Buffer*>(b),v);}
    virtual void solve(const BufferProcure* b, void* v = NULL)
      {solve(reinterpret_cast<const Buffer*>(b),v);}
    virtual void solve(const Load* b, void* v = NULL)
      {throw LogicException("Called undefined solve(Load*) method");}
    virtual void solve(const Flow* b, void* v = NULL)
      {throw LogicException("Called undefined solve(Flow*) method");}
    virtual void solve(const FlowEnd* b, void* v = NULL)
      {solve(reinterpret_cast<const Flow*>(b),v);}
    virtual void solve(const Solvable*,void* = NULL)
      {throw LogicException("Called undefined solve(Solvable*) method");}

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
    unsigned short getLogLevel() const {return loglevel;}

    /** Controls whether verbose output will be generated. */
    void setLogLevel(unsigned short v) {loglevel = v;}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  protected:
    /** Controls the amount of tracing and debugging messages. */
    unsigned short loglevel;
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
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Destructor. */
    virtual ~Solvable() {}
};


/** @brief This command runs a specific solver. */
class CommandSolve : public Command
{
  private:
    /** Pointer to the solver being used. */
    Solver *sol;

  public:
    /** Constructor. */
    CommandSolve() : sol(NULL) {};

    /** The core of the execute method is a call to the solve() method of the
      * solver. */
    DECLARE_EXPORT void execute();

    /** This type of command can't be undone. */
    void undo() {}

    /** Running a solver can't be undone. */
    bool undoable() const {return false;}

    string getDescription() const {return "running a solver";}

    /** Returns the solver being run. */
    Solver* getSolver() const {return sol;}

    /** Updates the solver being used. */
    void setSolver(Solver* s) {sol = s;}
};


/** @brief This class needs to be implemented by all classes that implement
  * dynamic behavior in the plan.
  *
  * The problem detection logic is implemented in the detectProblems() method.
  * For performance reasons, problem detection is "lazy", i.e. problems are
  * computed only when somebody really needs the access to the list of
  * problems.
  */
class Plannable : public Object, public HasProblems, public Solvable
{
  public:
    /** Constructor. */
    Plannable() : useProblemDetection(true), changed(true)
     {anyChange = true;};

    /** Specify whether this entity reports problems. */
    DECLARE_EXPORT void setDetectProblems(bool b);

    /** Returns whether or not this object needs to detect problems. */
    bool getDetectProblems() const {return useProblemDetection;}

    /** Loops through all plannable objects and updates their problems if
      * required. */
    static DECLARE_EXPORT void computeProblems();

    /** See if this entity has changed since the last problem
      * problem detection run. */
    bool getChanged() const {return changed;}

    /** Mark that this entity has been updated and that the problem
      * detection needs to be redone. */
    void setChanged(bool b = true) {changed=b; if (b) anyChange=true;}

    /** Implement the pure virtual function from the HasProblem class. */
    Plannable* getEntity() const {return const_cast<Plannable*>(this);}

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    virtual DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

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
  * Clusters are helpful is multi-threading the planning problem, partial
  * replanning of the model, etc...
  */
class HasLevel
{

#if defined(_MSC_VER) || defined(__BORLANDC__)
    // Visual C++ 6.0 and Borland C++ 5.5. seem to get confused. Static
    // functions can't access private members.
    friend class HasLevel;
#endif

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
    static DECLARE_EXPORT unsigned short numberOfClusters;

    /** Stores the total number of hanging clusters in the model. */
    static DECLARE_EXPORT unsigned short numberOfHangingClusters;
   
    /** Stores the level of this entity. Higher numbers indicate more
      * upstream entities.
      * A value of -1 indicates an unused entity.
      */
    short lvl;

    /** Stores the cluster number of the current entity. */
    unsigned short cluster;

  protected:
    /** Default constructor. The initial level is -1 and basically indicates
      * that this HasHierarchy (either Operation, Buffer or Resource) is not
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
    ~HasLevel() {recomputeLevels = true;}

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
    /** Returns the total number of clusters.<br>
      * If not up to date the recomputation will be triggered. 
      */
    static unsigned short getNumberOfClusters()
    {
      if (recomputeLevels || computationBusy) computeLevels();
      return numberOfClusters;
    }

    /** Returns the total number of hanging clusters. A hanging cluster
      * is a cluster that consists of a single entity that isn't connected
      * to any other entity.<br>
      * If not up to date the recomputation will be triggered. 
      */
    static unsigned short getNumberOfHangingClusters()
    {
      if (recomputeLevels || computationBusy) computeLevels();
      return numberOfHangingClusters;
    }

    /** Return the level (and recompute first if required). */
    short getLevel() const
    {
      if (recomputeLevels || computationBusy) computeLevels();
      return lvl;
    }

    /** Return the cluster number (and recompute first if required). */
    unsigned short getCluster() const
    {
      if (recomputeLevels || computationBusy) computeLevels();
      return cluster;
    }

    /** This function should be called when something is changed in the network
      * structure. The notification sets a flag, but does not immediately
      * trigger the recomputation.
      * @see computeLevels
      */
    static void triggerLazyRecomputation() {recomputeLevels = true;}
};


/** @brief This abstract class is used to associate buffers and resources with
  * a physical location.
  *
  * Locations are useful for reporting.<br>
  * The 'available' calendar is used to model the working hours and holidays 
  * of resources, buffers and operations.
  */
class Location
      : public HasHierarchy<Location>, public HasDescription, public Object
{
  public:
    /** Constructor. */
    explicit Location(const string& n) : HasHierarchy<Location>(n), available(NULL) {}

    /** Destructor. */
    virtual DECLARE_EXPORT ~Location();

    /** Returns the availability calendar of the location.<br>
      * The availability calendar models the working hours and holidays. It 
      * applies to all operations, resources and buffers using this location.
      */
    CalendarBool *getAvailable() const { return available; }

    /** Updates the availability calend of the location. */
    void setAvailable(CalendarBool* b) { available = b; }

    DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    size_t extrasize() const 
    {return getName().size() + HasDescription::extrasize();}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  private:
    /** The availability calendar models the working hours and holidays. It 
      * applies to all operations, resources and buffers using this location.
      */
    CalendarBool* available;
};


/** @brief This class implements the abstract Location class. */
class LocationDefault : public Location
{
  public:
    explicit LocationDefault(const string& str) : Location(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {return sizeof(LocationDefault) + Location::extrasize();}
};


/** @brief This abstracts class represents customers.
  *
  * Demands can be associated with a customer, but there is no planning
  * behavior directly linked to customers.
  */
class Customer
      : public HasHierarchy<Customer>, public HasDescription, public Object
{
  public:
    DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    size_t extrasize() const 
    {return getName().size() + HasDescription::extrasize();}
    Customer(const string& n) : HasHierarchy<Customer>(n) {}
    virtual DECLARE_EXPORT ~Customer();
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
};


/** @brief This class implements the abstract Customer class. */
class CustomerDefault : public Customer
{
  public:
    explicit CustomerDefault(const string& str) : Customer(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {return sizeof(CustomerDefault) + Customer::extrasize();}
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
    friend class OperationRouting;   // to have access to superoplist
    friend class OperationAlternate; // to have access to superoplist

  protected:
    /** Constructor. Don't use it directly. */
    explicit Operation(const string& str) : HasName<Operation>(str),
        loc(NULL), size_minimum(1.0), size_multiple(0.0), cost(1.0), 
        hidden(false), first_opplan(NULL), last_opplan(NULL) {}

  public:
    /** Destructor. */
    virtual DECLARE_EXPORT ~Operation();

    /** Returns a pointer to the operationplan being instantiated. */
    OperationPlan* getFirstOpPlan() const {return first_opplan;}

    /** Returns the delay before this operation.
      * @see setPreTime
      */
    TimePeriod getPreTime() const {return pre_time;}

    /** Updates the delay before this operation.<br>
      * This delay is a soft constraint. This means that solvers should try to
      * respect this waiting time but can choose to leave a shorter time delay
      * if required.<br>
      * @see setPostTime
      */
    void setPreTime(TimePeriod t)
    {
      if (t<TimePeriod(0L))
        throw DataException("No negative pre-operation time allowed");
      pre_time=t;
      setChanged();
    }

    /** Returns the delay after this operation.
      * @see setPostTime
      */
    TimePeriod getPostTime() const {return post_time;}

    /** Updates the delay after this operation.<br>
      * This delay is a soft constraint. This means that solvers should try to
      * respect this waiting time but can choose to leave a shorter time delay
      * if required.
      * @see setPreTime
      */
    void setPostTime(TimePeriod t)
    {
      if (t<TimePeriod(0L))
        throw DataException("No negative post-operation time allowed");
      post_time=t;
      setChanged();
    }

    /** Return the operation cost.<br>
      * The cost of executing this operation, per unit of the 
      * operation_plan.<br>
      * The default value is 1.0.
      */
    double getCost() const {return cost;}

    /** Update the operation cost.<br>
      * The cost of executing this operation, per unit of the operation_plan.
      */
    void setCost(const double c) {cost = c;}

    typedef Association<Operation,Buffer,Flow>::ListA flowlist;
    typedef Association<Operation,Resource,Load>::ListA  loadlist;

    /** This is the factory method which creates all operationplans of the
      * operation. */
    virtual DECLARE_EXPORT OperationPlan* createOperationPlan (double, Date,
      Date, Demand* = NULL, OperationPlan* = NULL, unsigned long = 0,
      bool makeflowsloads=true) const;

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
    virtual void setOperationPlanParameters
      (OperationPlan*, double, Date, Date, bool = true) const = 0;

    /** Returns the location of the operation, which is used to model the 
      * working hours and holidays. */
    Location* getLocation() const {return loc;}

    /** Updates the location of the operation, which is used to model the 
      * working hours and holidays. */
    void setLocation(Location* l) {loc = l;}

    /** Returns an reference to the list of flows. */
    const flowlist& getFlows() const {return flowdata;}

    /** Returns an reference to the list of flows. */
    const loadlist& getLoads() const {return loaddata;}

    /** Return the flow that is associates a given buffer with this
      * operation. Returns NULL is no such flow exists. */
    Flow* findFlow(const Buffer* b, Date d) const 
    {return flowdata.find(b,d);}

    /** Return the load that is associates a given resource with this
      * operation. Returns NULL is no such load exists. */
    Load* findLoad(const Resource* r, Date d) const 
    {return loaddata.find(r,d);}

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
    double getSizeMinimum() const {return size_minimum;}

    /** Sets the multiple size of operationplans. */
    void setSizeMultiple(double f)
    {
      if (f<0)
        throw DataException("Operation can't have a negative multiple size");
      size_multiple = f;
      setChanged();
    }

    /** Returns the minimum size for operationplans. */
    double getSizeMultiple() const {return size_multiple;}

    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

    size_t extrasize() const 
    {return getName().size() + HasDescription::extrasize();}

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    typedef list<Operation*> Operationlist;

    /** Returns a reference to the list of sub operations of this operation. */
    virtual const Operationlist& getSubOperations() const {return nosubOperations;}

    /** Returns a reference to the list of super-operations, i.e. operations
      * using the current Operation as a sub-Operation.
      */
    const Operationlist& getSuperOperations() {return superoplist;}

    /** Register a super-operation, i.e. an operation having this one as a
      * sub-operation. */
    void addSuperOperation(Operation * o) {superoplist.push_front(o);}

    /** Removes a sub-operation from the list. This method will need to be
      * overridden by all operation types that acts as a super-operation. */
    virtual void removeSubOperation(Operation *o) {}

    /** Removes a super-operation from the list. */
    void removeSuperOperation(Operation *o)
    {superoplist.remove(o); o->removeSubOperation(this);}

    /** Return the release fence of this operation. */
    TimePeriod getFence() const {return fence;}

    /** Update the release fence of this operation. */
    void setFence(TimePeriod t) {if (fence!=t) setChanged(); fence=t;}

    virtual DECLARE_EXPORT void updateProblems();

    void setHidden(bool b) {if (hidden!=b) setChanged(); hidden = b;}
    bool getHidden() const {return hidden;}

    static DECLARE_EXPORT const MetaCategory metadata;

  protected:
    void initOperationPlan (OperationPlan*, double, const Date&, const Date&,
        Demand*, OperationPlan*, unsigned long, bool = true) const;

  private:
    /** List of operations using this operation as a sub-operation */
    Operationlist superoplist;

    /** Empty list of operations. For operation types which have no
      * suboperations this list is used as the list of suboperations.
      */
    static DECLARE_EXPORT Operationlist nosubOperations;

    /** Location of the operation.<br>
      * The location is used to model the working hours and holidays.
      */
    Location* loc;

    /** Represents the time between this operation and a next one. */
    TimePeriod post_time;

    /** Represents the time between this operation and a previous one. */
    TimePeriod pre_time;

    /** Represents the release fence of this operation, i.e. a period of time
      * (relative to the current date of the plan) in which normally no
      * operationplan is allowed to be created.
      */
    TimePeriod fence;

    /** Singly linked list of all flows of this operation. */
    flowlist flowdata;

    /** Singly linked list of all resources Loaded by this operation. */
    loadlist loaddata;

    /** Minimum size for operationplans.<br>
      * The default value is 1.0
      */
    double size_minimum;

    /** Multiple size for operationplans. */
    double size_multiple;

    /** Cost of the operation.<br>
      * The default value is 1.0.
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


/** @brief An operationplan is the key dynamic element of a plan. It
  * represents a certain quantity being planned along a certain operation
  * during a certain date range.
  *
  * From a coding perspective:
  *  - Operationplans are created by the factory method createOperationPlan()
  *    on the matching operation class.
  *  - The createLoadAndFlowplans() can optionally be called to also create
  *    the loadplans and flowplans, to take care of the material and
  *    capacity consumption.
  *  - Once you're sure about creating the operationplan, the initialize()
  *    method should be called. It will assign the operationplan a unique
  *    numeric identifier, register the operationplan in a container owned
  *    by the operation instance, and also create loadplans and flowplans
  *    if this hasn't been done yet.<br>
  *  - Operationplans can be organized in hierarchical structure, matching
  *    the operation hierarchies they belong to.
  */
class OperationPlan
      : public Object, public HasProblems, public NonCopyable
{
    friend class FlowPlan;
    friend class LoadPlan;
    friend class Demand;
    friend class Operation;
    friend class OperationPlanAlternate;
    friend class OperationPlanRouting;

  public:
    class FlowPlanIterator;

    typedef list<OperationPlan*> OperationPlanList;

    /** Returns a reference to the list of sub-operationplans.<br>
      * Subclasses where multiple sub-operationplans exist must override this
      * method.
      * @see getSubOperationPlan
      */
    virtual const OperationPlanList& getSubOperationPlans() const
      {return nosubOperationPlans;}

    /** Returns a reference to the list of sub-operationplans.<br>
      * Subclasses having only a single sub-operationplan must override this
      * method.
      * @see getSubOperationPlans
      */
    virtual OperationPlan* getSubOperationPlan() const {return NULL;}

    /** Returns an iterator pointing to the first flowplan. */
    FlowPlanIterator beginFlowPlans() const;

    /** Returns an iterator pointing beyond the last flowplan. */
    FlowPlanIterator endFlowPlans() const;

    /** Returns how many flowplans are created on an operationplan. */
    int sizeFlowPlans() const;

    class LoadPlanIterator;

    /** Returns an iterator pointing to the first loadplan. */
    LoadPlanIterator beginLoadPlans() const;

    /** Returns an iterator pointing beyond the last loadplan. */
    LoadPlanIterator endLoadPlans() const;

    /** Returns how many loadplans are created on an operationplan. */
    int sizeLoadPlans() const;

    /** @brief This class models an STL-like iterator that allows us to iterate over
      * the operationplans in a simple and safe way.
      *
      * Objects of this class are created by the begin() and end() functions.
      */
    class iterator
    {
      public:
        /** Constructor. The iterator will loop only over the operationplans
          * of the operation passed. */
        iterator(const Operation* x) : op(Operation::end())
        {
          if (x && !x->getHidden())
            opplan = x->getFirstOpPlan();
          else
            opplan = NULL;
        }

        /** Constructor. The iterator will loop over all operationplans. */
        iterator() : op(Operation::begin())
        {
          // The while loop is required since the first operation might not
          // have any operationplans at all or can be hidden
          while (op!=Operation::end()
            && (!op->getFirstOpPlan() || op->getHidden())) ++op;
          if (op!=Operation::end())
            opplan = op->getFirstOpPlan();
          else
            opplan = NULL;
        }

        /** Copy constructor. */
        iterator(const iterator& it) : opplan(it.opplan), op(it.op) {}

        /** Return the content of the current node. */
        OperationPlan& operator*() const {return *opplan;}

        /** Return the content of the current node. */
        OperationPlan* operator->() const {return opplan;}

        /** Pre-increment operator which moves the pointer to the next
          * element. */
        iterator& operator++()
        {
          opplan = opplan->next;
          // Move to a new operation
          if (!opplan && op!=Operation::end())
          {
            do ++op;
            while (op!=Operation::end() && (!op->getFirstOpPlan() || op->getHidden()));
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
          opplan = opplan->next;
          // Move to a new operation
          if (!opplan && op!=Operation::end())
          {
            do ++op; while (op!=Operation::end() && !op->getFirstOpPlan());
            if (op!=Operation::end())
              opplan = op->getFirstOpPlan();
            else
              opplan = NULL;
          }
          return tmp;
        }

        /** Comparison operator. */
        bool operator==(const iterator& y) const {return opplan == y.opplan;}

        /** Inequality operator. */
        bool operator!=(const iterator& y) const {return opplan != y.opplan;}

      private:
        /** A pointer to current operationplan. */
        OperationPlan* opplan;

        /** An iterator over the operations. */
        Operation::iterator op;
    };

    friend class iterator;

    static iterator end() {return iterator(NULL);}

    static iterator begin() {return iterator();}

    /** Returns true when not a single operationplan object exists. */
    static bool empty() {return begin()==end();}

    /** Returns the number of operationplans in the system. This method
      * is linear with the number of operationplans in the model, and should
      * therefore be used only with care.
      */
    static unsigned long size()
    {
      unsigned long cnt = 0;
      for (OperationPlan::iterator i = begin(); i != end(); ++i) ++cnt;
      return cnt;
    }

    /** This is a factory method that creates an operationplan pointer based
      * on the name and id, which are passed as an array of character pointers.
      * This method is intended to be used to create objects when reading
      * XML input data.
      */
    static DECLARE_EXPORT Object* createOperationPlan (const MetaClass&, const AttributeList&);

    /** Destructor. */
    virtual DECLARE_EXPORT ~OperationPlan();

    virtual DECLARE_EXPORT void setChanged(bool b = true);

    /** Returns the quantity. */
    double getQuantity() const {return quantity;}

    /** Updates the quantity.<br>
      * The operationplan quantity is subject to the following rules:
      *  - The quantity must be greater than the minimum size.<br>
      *    The value is rounded up to the minimum size ir required,
      *    or rounded down to 0.
      *  - The quantity must be a multiple of the multiple_size field.<br>
      *    The value is rounded up or down to meet this constraint.
      *  - There is no maximum size to an operationplan.
      *  - Setting the quantity of an operationplan to 0 is always possible,
      *    regardless of the minimum and multiples values.
      * This method can only be called on top operationplans. Sub operation
      * plans should pass on a call to the parent operationplan.
      */
    virtual DECLARE_EXPORT void setQuantity
      (double f, bool roundDown = false, bool update = true);

    /** Returns a pointer to the demand for which this operation is a delivery.
      * If the operationplan isn't a delivery operation, this is a NULL pointer.
      */
    Demand* getDemand() const {return dmd;}

    /** Updates the demand to which this operationplan is a solution. */
    DECLARE_EXPORT void setDemand(Demand* l);

    /** Returns whether the operationplan is locked. A locked operationplan
      * is never changed. 
      */
    bool getLocked() const {return locked;}

    /** Deletes all operationplans of a certain operation. A boolean flag
      * allows to specify whether locked operationplans are to be deleted too.
      */
    static DECLARE_EXPORT void deleteOperationPlans(Operation* o, bool deleteLocked=false);

    /** Locks/unlocks an operationplan. A locked operationplan is never
      * changed.
      */
    virtual DECLARE_EXPORT void setLocked(bool b = true);

    /** Returns a pointer to the operation being instantiated. */
    Operation* getOperation() const {return oper;}

    /** Sets the earliest possible start time (epst) of the operationplan. */
    void setEpst(Date d) {epst = d; setChanged();}

    /** Returns the earliest possible start time (epst) of the operationplan. */
    Date getEpst() const {return epst;}

    /** Sets the latest possible start time (lpst) of the operationplan. */
    void setLpst(Date d) {lpst = d; setChanged();}

    /** Returns the latest possible start time (lpst) of the operationplan. */
    Date getLpst() const {return lpst;}

    /** Fixes the start and end Date of an operationplan. Note that this
      * overrules the standard duration given on the operation, i.e. no logic
      * kicks in to verify the data makes sense. This is up to the user to
      * take care of.<br>
      * The methods setStart(Date) and setEnd(Date) are therefore preferred
      * since they properly apply all appropriate logic.
      */
    void setStartAndEnd(Date st, Date nd)
    {
      dates.setStartAndEnd(st,nd);
      OperationPlan::update();
    }

    /** Updates the operationplan owning this operationplan. In case of
      * a OperationRouting steps this will be the operationplan representing the
      * complete routing. */
    void DECLARE_EXPORT setOwner(OperationPlan* o);

    /** Returns a pointer to the operationplan for which this operationplan
      * a sub-operationplan.<br>
      * The method returns NULL if there is no owner defined.<br>
      * E.g. Sub-operationplans of a routing refer to the overall routing
      * operationplan.<br>
      * E.g. An alternate sub-operationplan refers to its parent.
      * @see getTopOwner
      */
    OperationPlan* getOwner() const {return owner;}

    /** Returns a pointer to the operationplan owning a set of
      * sub-operationplans. There can be multiple levels of suboperations.<br>
      * If no owner exists the method returns the current operationplan.
      * @see getOwner
      */
    const OperationPlan* getTopOwner() const
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
    const DateRange & getDates() const {return dates;}

    /** Returns a unique identifier of the operationplan.<br>
      * The identifier can be specified in the data input (in which case
      * we check for the uniqueness during the read operation).<br>
      * For operationplans created during a solver run, the identifier is
      * assigned in the initialize() function. The numbering starts with the
      * highest identifier read in from the input and is then incremented
      * for every operationplan that is registered.
      */
    unsigned long getIdentifier() const {return id;}

    /** Updates the end date of the operationplan. The start date is computed.
      * Locked operationplans are not updated by this function.
      */
    virtual DECLARE_EXPORT void setEnd(Date);

    /** Updates the start date of the operationplan. The end date is computed.
      * Locked operation_plans are not updated by this function.
      */
    virtual DECLARE_EXPORT void setStart(Date);

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

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
    virtual DECLARE_EXPORT bool initialize();

    /** Add a sub-operationplan to the list. For normal operationplans this
      * is only a dummy function. For alternates and routing operationplans
      * it does have a meaning.
      */
    virtual void addSubOperationPlan(OperationPlan* o)
    {
      throw LogicException("Adding a sub operationplan to "
          + oper->getName() + " not supported");
    };

    /** Remove a sub-operation_plan from the list. For normal operation_plans
      * this is only a dummy function. For alternates and routing
      * operationplans it does have a meaning.
      */
    virtual void eraseSubOperationPlan(OperationPlan* o)
    {
      throw LogicException("Removing a sub operationplan from "
          + oper->getName() + " not supported");
    };

    /** This function is used to create the proper loadplan and flowplan
      * objects associated with the operation. */
    DECLARE_EXPORT void createFlowLoads();

    bool getHidden() const {return getOperation()->getHidden();}

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
    Plannable* getEntity() const {return oper;}

    /** Return the metadata. We return the metadata of the operation class,
      * not the one of the operationplan class!
      */
    const MetaClass& getType() const {return metadata;}

    static DECLARE_EXPORT const MetaCategory metadata;

    virtual size_t getSize() const
      {return sizeof(OperationPlan);}

    /** Handles the persistence of operationplan objects. */
    static DECLARE_EXPORT void writer(const MetaCategory&, XMLOutput*);

    /** Comparison of 2 OperationPlans.
      * To garantuee that the problems are sorted in a consistent and stable
      * way, the following sorting criteria are used (in order of priority):
      * <ol><li>Operation</li>
      * <li>Start date (earliest dates first)</li>
      * <li>Quantity (biggest quantities first)</li></ol>
      * Multiple operationplans for the same values of the above keys can exist.
      */
    DECLARE_EXPORT bool operator < (const OperationPlan& a) const;

    /** This method should be called when an operationplan is updated in a way
      * that can affect it's position in the sorted list: ie changes of the
      * start date or quantity.<br>
      * The method will verify the correct sorting an update it if necessary.
      */
    DECLARE_EXPORT void updateSorting();

  protected:
    /** Updates the operationplan based on the latest information of quantity, 
      * date and locked flag. */
    virtual DECLARE_EXPORT void update();
    DECLARE_EXPORT void resizeFlowLoadPlans();

    /** Pointer to a higher level OperationPlan. */
    OperationPlan *owner;

    /** Quantity. */
    double quantity;

    /** Default constructor.
      * This way of creating operationplan objects is not intended for use by
      * any client applications. Client applications should use the factory
      * method on the operation class instead.<br>
      * Subclasses of the Operation class may use this constructor in their
      * own override of the createOperationPlan method.
      * @see Operation::createOperationPlan
      */
    OperationPlan() : owner(NULL), quantity(0.0), locked(false), dmd(NULL),
      id(0), oper(NULL), firstflowplan(NULL), firstloadplan(NULL),
      prev(NULL), next(NULL) {}

  private:
    /** Empty list of operationplans.<br>
      * For operationplan types without suboperationplans this list is used
      * as the list of suboperationplans.
      */
    static OperationPlanList nosubOperationPlans;

    /** Is this operationplan locked? A locked operationplan doesn't accept
      * any changes. This field is only relevant for top-operationplans. */
    bool locked;

    /** Counter of OperationPlans, which is used to automatically assign a
      * unique identifier for each operationplan.<br>
      * The value of the counter is the first available identifier value that
      * can be used for a new operationplan.
      * @see getIdentifier()
      */
    static DECLARE_EXPORT unsigned long counter;

    /** Pointer to the demand. Only delivery operationplans have this field
      * set. The field is NULL for all other operationplans. */
    Demand *dmd;

    /** Unique identifier. */
    unsigned long id;

    /** Start and end date. */
    DateRange dates;

    /** Pointer to the operation. */
    Operation *oper;

    /** Earliest possible start time. */
    Date epst;

    /** Earliest possible start time. */
    Date lpst;

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
};


/** @brief Models an operation that takes a fixed amount of time, independent
  * of the quantity. */
class OperationFixedTime : public Operation
{
  public:
    /** Constructor. */
    explicit OperationFixedTime(const string& s) : Operation(s) {}

    /** Returns the length of the operation. */
    const TimePeriod getDuration() const {return duration;}

    /** Updates the duration of the operation. Existing operation plans of this
      * operation are not automatically refreshed to reflect the change. */
    void setDuration(TimePeriod t) 
    {
      if (t<0L) 
        throw DataException("FixedTime operation can't have a negative duration");
      duration = t;
    }

    DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {return sizeof(OperationFixedTime) + Operation::extrasize();}

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
    DECLARE_EXPORT void setOperationPlanParameters
      (OperationPlan*, double, Date, Date, bool=true) const;

  private:
    /** Stores the lengh of the Operation. */
    TimePeriod duration;
};


/** @brief Models an operation whose duration is the sum of a constant time,
  * plus a cetain time per unit.
  */
class OperationTimePer : public Operation
{
  public:
    /** Constructor. */
    explicit OperationTimePer(const string& s) : Operation(s) {}

    /** Returns the constant part of the operation time. */
    TimePeriod getDuration() const {return duration;}

    /** Sets the constant part of the operation time. */
    void setDuration(TimePeriod t)
    { 
      if(t<0L) 
        throw DataException("TimePer operation can't have a negative duration");
      duration = t; 
    }

    /** Returns the time per unit of the operation time. */
    TimePeriod getDurationPer() const {return duration_per;}

    /** Sets the time per unit of the operation time. */
    void setDurationPer(TimePeriod t)
    { 
      if(t<0L) 
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
      * @see Operation::setOperationPlanParameters
      */
    DECLARE_EXPORT void setOperationPlanParameters
      (OperationPlan*, double, Date, Date, bool=true) const;

    DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {return sizeof(OperationTimePer) + Operation::extrasize();}

  private:
    /** Constant part of the operation time. */
    TimePeriod duration;

    /** Variable part of the operation time. */
    TimePeriod duration_per;
};


/** @brief Represents a routing operation, i.e. an operation consisting of
  * multiple, sequential sub-operations.
  */
class OperationRouting : public Operation
{
  public:
    /** Constructor. */
    explicit OperationRouting(const string& c) : Operation(c) {};

    /** Destructor. */
    DECLARE_EXPORT ~OperationRouting();

    /** Adds a new steps to routing at the start of the routing. */
    void addStepFront(Operation *o)
    {
      if (!o) throw DataException("Adding NULL operation to routing");
      steps.push_front(o);
      o->addSuperOperation(this);
    }

    /** Adds a new steps to routing at the end of the routing. */
    void addStepBack(Operation *o)
    {
      if (!o) throw DataException("Adding NULL operation to routing");
      steps.push_back(o);
      o->addSuperOperation(this);
    }

    void removeSubOperation(Operation *o)
    { steps.remove(o); o->superoplist.remove(this); }

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
    DECLARE_EXPORT void setOperationPlanParameters
      (OperationPlan*, double, Date, Date, bool=true) const;

    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Return a list of all sub-operationplans. */
    virtual const Operationlist& getSubOperations() const {return steps;}

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual DECLARE_EXPORT OperationPlan* createOperationPlan (double, Date,
      Date, Demand* = NULL, OperationPlan* = NULL, unsigned long = 0,
      bool makeflowsloads=true) const;

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {
      return sizeof(OperationRouting) + Operation::extrasize()
        + steps.size() * 2 * sizeof(Operation*);
    }

  private:
    Operationlist steps;
};


/** @brief OperationPlans for routing operation uses this subclass for
  * the instances. */
class OperationPlanRouting : public OperationPlan
{
    friend class OperationRouting;
  private:
    OperationPlan::OperationPlanList step_opplans;
    OperationPlanRouting() {};
  public:
    /** Updates the end date of the operation. Slack can be introduced in the
      * routing by this method, i.e. the sub operationplans are only moved if
      * required to meet the end date. */
    DECLARE_EXPORT void setEnd(Date d);

    /** Updates the start date of the operation. Slack can be introduced in the
      * routing by this method, i.e. the sub operationplans are only moved if
      * required to meet the start date.
      */
    DECLARE_EXPORT void setStart(Date d);
    virtual DECLARE_EXPORT void update();
    DECLARE_EXPORT void addSubOperationPlan(OperationPlan* o);
    DECLARE_EXPORT ~OperationPlanRouting();
    DECLARE_EXPORT void setQuantity(double f, bool roundDown = false, bool update = true);
    DECLARE_EXPORT void eraseSubOperationPlan(OperationPlan* o);
    virtual const OperationPlan::OperationPlanList& getSubOperationPlans() const {return step_opplans;}

    /** Locks/unlocks an operationplan. A locked operationplan is never
      * changed.
      */
    virtual DECLARE_EXPORT void setLocked(bool b = true);

    /** Initializes the operationplan and all steps in it.
      * If no step operationplans had been created yet this method will create
      * them. During this type of creation the end date of the routing
      * operationplan is used and step operationplans are created. After the
      * step operationplans are created the start date of the routing will be
      * equal to the start of the first step.
      */
    DECLARE_EXPORT bool initialize();

    void updateProblems();

    virtual size_t getSize() const
      {return sizeof(OperationPlanRouting) + step_opplans.size() * 2 * sizeof(OperationPlan*);}
};



/** @brief This class represents a choice between multiple operations. The
  * alternates are sorted in order of priority.
  */
class OperationAlternate : public Operation
{
  public:
    typedef pair<int,DateRange> alternateProperty;

    /** Constructor. */
    explicit OperationAlternate(const string& c) : Operation(c) {};

    /** Destructor. */
    DECLARE_EXPORT ~OperationAlternate();

    /** Add a new alternate operation.<br>
      * The lower the priority value, the more important this alternate 
      * operation is. */
    DECLARE_EXPORT void addAlternate
      (Operation*, int = 1, DateRange = DateRange());

    /** Removes an alternate from the list. */
    DECLARE_EXPORT void removeSubOperation(Operation *);

    /** Returns the properties of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     null or when it is not a sub-operation of this alternate.
      */
    DECLARE_EXPORT const alternateProperty& getProperties(Operation* o) const;

    /** Updates the properties of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     not null and not a sub-operation of this alternate.
      */
    DECLARE_EXPORT void setProperties(Operation*, int, DateRange);

    /** Updates the priority of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     not null and not a sub-operation of this alternate.
      */
    DECLARE_EXPORT void setPriority(Operation*, int);

    /** Updates the effective daterange of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     not null and not a sub-operation of this alternate.
      */
    DECLARE_EXPORT void setEffective(Operation*, DateRange);

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - Very simple, call the method with the same name on the alternate
      *    suboperationplan.
      * @see Operation::setOperationPlanParameters
      */
    DECLARE_EXPORT void setOperationPlanParameters
      (OperationPlan*, double, Date, Date, bool=true) const;

    DECLARE_EXPORT void beginElement (XMLInput&, const Attribute&);
    DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual const Operationlist& getSubOperations() const {return alternates;}

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual DECLARE_EXPORT OperationPlan* createOperationPlan (double, Date,
      Date, Demand* = NULL, OperationPlan* = NULL, unsigned long = 0,
      bool makeflowsloads=true) const;

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {
      return sizeof(OperationAlternate) + Operation::extrasize()
          + alternates.size() * (5*sizeof(Operation*)+sizeof(alternateProperty));
    }

  private:
    typedef list<alternateProperty> alternatePropertyList;

    /** List of the priorities of the different alternate operations. The list
      * is maintained such that it is sorted in ascending order of priority. */
    alternatePropertyList alternateProperties;

    /** List of all alternate operations. The list is sorted with the operation
      * with the highest priority at the start of the list.<br>
      * Note that the list of operations and the list of priorities go hand in
      * hand: they have an equal number of elements and the order of the
      * elements is matching in both lists.
      */
    Operationlist alternates;
};


/** @brief This class subclasses the OperationPlan class for operations of type
  * OperationAlternate.
  *
  * Such operationplans need an extra field to point to the suboperationplan.
  * @see OperationPlan, OperationAlternate
  */
class OperationPlanAlternate : public OperationPlan
{
    friend class OperationAlternate;

  private:
    OperationPlan* altopplan;

  public:
    /* Constructor. */
    OperationPlanAlternate() : altopplan(NULL) {};

    /** Destructor. */
    DECLARE_EXPORT ~OperationPlanAlternate();
    DECLARE_EXPORT void addSubOperationPlan(OperationPlan* o);
    DECLARE_EXPORT void setQuantity(double f, bool roundDown = false, bool update = true);
    DECLARE_EXPORT void eraseSubOperationPlan(OperationPlan* o);
    DECLARE_EXPORT void setEnd(Date d);
    DECLARE_EXPORT void setStart(Date d);
    DECLARE_EXPORT void update();

    /** Returns the sub-operationplan. */
    virtual OperationPlan* getSubOperationPlan() const {return altopplan;}

    /** Locks/unlocks an operationplan. A locked operationplan is never
      * changed.
      */
    virtual DECLARE_EXPORT void setLocked(bool b = true);

    /** Initializes the operationplan. If no suboperationplan was created
      * yet this method will create one, using the highest priority alternate.
      */
    DECLARE_EXPORT bool initialize();
};


/** @brief An item defines the products being planned, sold, stored and/or
  * manufactured. Buffers and demands have a reference an item.
  *
  * This is an abstract class.
  */
class Item
      : public HasHierarchy<Item>, public HasDescription, public Object
{
  public:
    /** Constructor. Don't use this directly! */
    explicit Item(const string& str) : HasHierarchy<Item> (str), 
      deliveryOperation(NULL), price(1.0) {}

    /** Returns the delivery operation.<br>
      * This field is inherited from a parent item, if it hasn't been
      * specified.
      */
    Operation* getOperation() const
    {
      // Current item has a non-empty deliveryOperation field
      if (deliveryOperation) return deliveryOperation;

      // Look for a non-empty deliveryOperation field on owners
      for (Item* i = getOwner(); i; i=i->getOwner())
        if (i->deliveryOperation) return i->deliveryOperation;

      // The field is not specified on the item or any of its parents.
      return NULL;
    }

    /** Updates the delivery operation.<br>
      * If some demands have already been planned using the old delivery
      * operation they are left untouched and won't be replanned.
      */
    void setOperation(Operation* o) {deliveryOperation = o;}

    /** Return the selling price of the item.<br>
      * The default value is 1.0.
      */
    double getPrice() const {return price;}

    /** Update the selling price of the item. */
    void setPrice(const double c) {price = c;}

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    DECLARE_EXPORT void beginElement (XMLInput&, const Attribute&);

    /** Destructor. */
    virtual DECLARE_EXPORT ~Item();

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  private:
    /** This is the operation used to satisfy a demand for this item.
      * @see Demand
      */
    Operation* deliveryOperation;

    /** Selling price of the item. */
    double price;
};


/** @brief This class is the default implementation of the abstract Item
  * class. */
class ItemDefault : public Item
{
  public:
    explicit ItemDefault(const string& str) : Item(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {
      return sizeof(ItemDefault) + getName().size() 
        + HasDescription::extrasize();
    }
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

    /** Constructor. Implicit creation of instances is disallowed. */
    explicit Buffer(const string& str) : HasHierarchy<Buffer>(str),
        hidden(false), producing_operation(NULL), loc(NULL), it(NULL),
        min_cal(NULL), max_cal(NULL), carrying_cost(1.0) {}

    /** Returns the operation that is used to supply extra supply into this
      * buffer. */
    Operation* getProducingOperation() const {return producing_operation;}

    /** Updates the operation that is used to supply extra supply into this
      * buffer. */
    void setProducingOperation(Operation* o)
      {producing_operation = o; setChanged();}

    /** Returns the item stored in this buffer. */
    Item* getItem() const {return it;}

    /** Updates the Item stored in this buffer. */
    void setItem(Item* i) {it = i; setChanged();}

    /** Returns the Location of this buffer. */
    Location* getLocation() const {return loc;}

    /** Updates the location of this buffer. */
    void setLocation(Location* i) {loc = i;}

    /** Returns a pointer to a calendar for storing the minimum inventory
      * level. */
    CalendarDouble* getMinimum() const {return min_cal;}

    /** Returns a pointer to a calendar for storing the maximum inventory
      * level. */
    CalendarDouble* getMaximum() const {return max_cal;}

    /** Updates the minimum inventory target for the buffer. */
    DECLARE_EXPORT void setMinimum(CalendarDouble *);

    /** Updates the minimum inventory target for the buffer. */
    DECLARE_EXPORT void setMaximum(CalendarDouble *);

    /** Return the carrying cost.<br>
      * The cost of carrying inventory in this buffer. The value is a 
      * percentage of the item sales price, per year and per unit.
      */
    double getCarryingCost() const {return carrying_cost;}

    /** Return the carrying cost.<br>
      * The cost of carrying inventory in this buffer. The value is a 
      * percentage of the item sales price, per year and per unit.<br>
      * The default value is 1.0.
      */
    void setCarryingCost(const double c) {carrying_cost = c;}

    DECLARE_EXPORT virtual void beginElement(XMLInput&, const Attribute&);
    DECLARE_EXPORT virtual void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT virtual void endElement(XMLInput&, const Attribute&, const DataElement&);

    size_t extrasize() const 
    {return getName().size() + HasDescription::extrasize();}

    /** Destructor. */
    virtual DECLARE_EXPORT ~Buffer();

    /** Returns the available material on hand immediately after the
      * given date.
      */
    DECLARE_EXPORT double getOnHand(Date d = Date::infinitePast) const;

    /** Update the on-hand inventory at the start of the planning horizon. */
    DECLARE_EXPORT void setOnHand(double f);

    /** Returns minimum or maximum available material on hand in the given
      * daterange. The third parameter specifies whether we return the
      * minimum (which is the default) or the maximum value.
      * The computation is INclusive the start and end dates.
      */
    DECLARE_EXPORT double getOnHand(Date, Date, bool min = true) const;

    /** Returns a reference to the list of all flows of this buffer. */
    const flowlist& getFlows() const {return flows;}

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Returns a reference to the list of all flow plans of this buffer. */
    const flowplanlist& getFlowPlans() const {return flowplans;}

    /** Returns a reference to the list of all flow plans of this buffer. */
    flowplanlist& getFlowPlans() {return flowplans;}

    /** Return the flow that is associates a given operation with this
      * buffer.<br>Returns NULL is no such flow exists. */
    Flow* findFlow(const Operation* o, Date d) const 
    {return flows.find(o,d);}

    /** Deletes all operationplans consuming from or producing from this
      * buffer. The boolean parameter controls whether we delete also locked
      * operationplans or not.
      */
    DECLARE_EXPORT void deleteOperationPlans(bool deleteLockedOpplans = false);

    virtual DECLARE_EXPORT void updateProblems();

    void setHidden(bool b) {if (hidden!=b) setChanged(); hidden = b;}
    bool getHidden() const {return hidden;}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

    /** This function matches producing and consuming operationplans
      * with each other, and updates the pegging iterator accordingly.
      */
    virtual DECLARE_EXPORT void followPegging
      (PeggingIterator&, FlowPlan*, short, double, double);

  private:
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

    /** Points to a calendar to store the minimum inventory level.<br>
      * The default value is NULL, resulting in a constant minimum level
      * of 0.
      */
    CalendarDouble *min_cal;

    /** Points to a calendar to store the maximum inventory level.<br>
      * The default value is NULL, resulting in a buffer without excess
      * inventory problems.
      */
    CalendarDouble *max_cal;

    /** Carrying cost.<br>
      * The cost of carrying inventory in this buffer. The value is a 
      * percentage of the item sales price, per year and per unit.
      */
    double carrying_cost;
};



/** @brief This class is the default implementation of the abstract Buffer class. */
class BufferDefault : public Buffer
{
  public:
    explicit BufferDefault(const string& str) : Buffer(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    virtual size_t getSize() const
    {return sizeof(BufferDefault) + Buffer::extrasize();}
    static DECLARE_EXPORT const MetaClass metadata;
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
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    virtual const MetaClass& getType() const {return metadata;}
    virtual size_t getSize() const
      {return sizeof(BufferInfinite) + Buffer::extrasize();}
    explicit BufferInfinite(const string& c) : Buffer(c)
      {setDetectProblems(false);}
    static DECLARE_EXPORT const MetaClass metadata;
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
  *  - <b>Leadtime</b>:<br>
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
    virtual DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    virtual const MetaClass& getType() const {return metadata;}
    virtual size_t getSize() const
      {return sizeof(BufferProcure) + Buffer::extrasize();}
    explicit BufferProcure(const string& c) : Buffer(c), min_inventory(0),
      max_inventory(0), size_minimum(0), size_maximum(DBL_MAX), size_multiple(0),
      oper(NULL) {}
    static DECLARE_EXPORT const MetaClass metadata;

    /** Return the purchasing leadtime. */
    TimePeriod getLeadtime() const {return leadtime;}

    /** Update the procurement leadtime. */
    void setLeadtime(TimePeriod p) 
    {
      if (p<0L) 
        throw DataException("Procurement buffer can't have a negative lead time");
      leadtime = p;
    }

    /** Return the release time fence. */
    TimePeriod getFence() const {return fence;}

    /** Update the release time fence. */
    void setFence(TimePeriod p) {fence = p;}

    /** Return the inventory level that will trigger creation of a
      * purchasing.
      */
    double getMinimumInventory() const {return min_inventory;}

    /** Update the minimum inventory level to trigger replenishments. */
    void setMinimumInventory(double f)
    {
      if (f<0) 
        throw DataException("Procurement buffer can't have a negative minimum inventory");
      min_inventory = f;
      // minimum is increased over the maximum: auto-increase the maximum
      if (max_inventory < min_inventory) max_inventory = min_inventory;
    }

    /** Return the maximum inventory level to which we wish to replenish. */
    double getMaximumInventory() const {return max_inventory;}

    /** Update the inventory level to replenish to. */
    void setMaximumInventory(double f)
    {
      if (f<0)
        throw DataException("Procurement buffer can't have a negative maximum inventory");
      max_inventory = f;
      // maximum is lowered below the minimum: auto-decrease the minimum
      if (max_inventory < min_inventory) min_inventory = max_inventory;
    }

    /** Return the minimum interval between purchasing operations.<br>
      * This parameter doesn't control the timing of the first purchasing
      * operation, but only to the subsequent ones.
      */
    TimePeriod getMinimumInterval() const {return min_interval;}

    /** Update the minimum time between replenishments. */
    void setMinimumInterval(TimePeriod p)
    {
      if (p<0L)
        throw DataException("Procurement buffer can't have a negative minimum interval");
      min_interval = p;
      // minimum is increased over the maximum: auto-increase the maximum
      if (max_interval < min_interval) max_interval = min_interval;
    }

    /** Return the maximum time interval between sytem-generated replenishment
      * operations.
      */
    TimePeriod getMaximumInterval() const {return max_interval;}

    /** Update the minimum time between replenishments. */
    void setMaximumInterval(TimePeriod p)
    {
      if (p<0L) 
        throw DataException("Procurement buffer can't have a negative maximum interval");
      max_interval = p;
      // maximum is lowered below the minimum: auto-decrease the minimum
      if (max_interval < min_interval) min_interval = max_interval;
    }

    /** Return the minimum quantity of a purchasing operation. */
    double getSizeMinimum() const {return size_minimum;}

    /** Update the minimum replenishment quantity. */
    void setSizeMinimum(double f)
    {
      if (f<0) 
        throw DataException("Procurement buffer can't have a negative minimum size");
      size_minimum = f;
      // minimum is increased over the maximum: auto-increase the maximum
      if (size_maximum < size_minimum) size_maximum = size_minimum;
   }

    /** Return the maximum quantity of a purchasing operation. */
    double getSizeMaximum() const {return size_maximum;}

    /** Update the maximum replenishment quantity. */
    void setSizeMaximum(double f)
    {
      if (f<0)
        throw DataException("Procurement buffer can't have a negative maximum size");
      size_maximum = f;
      // maximum is lowered below the minimum: auto-decrease the minimum
      if (size_maximum < size_minimum) size_minimum = size_maximum;
    }

    /** Return the multiple quantity of a purchasing operation. */
    double getSizeMultiple() const {return size_multiple;}

    /** Update the multiple quantity. */
    void setSizeMultiple(double f) 
    {
      if (f<0) 
        throw DataException("Procurement buffer can't have a negative multiple size");
      size_multiple = f;
    }

    /** Returns the operation that is automatically created to represent the
      * procurements.
      */
    DECLARE_EXPORT Operation* getOperation() const;

  private:
    /** Purchasing leadtime.<br>
      * Within this leadtime fence no additional purchase orders can be generated.
      */
    TimePeriod leadtime;

    /** Time window from the current date in which all procurements are expected
      * to be released.
      */
    TimePeriod fence;

    /** Inventory level that will trigger the creation of a replenishment.<br>
      * Because of the replenishment leadtime, the actual inventory will drop
      * below this value. It is up to the user to set an appropriate minimum
      * value.
      */
    double min_inventory;

    /** The maximum inventory level to which we plan to replenish.<br>
      * This is not a hard limit - other parameters can make that the actual
      * inventory either never reaches this value or always exceeds it.
      */
    double max_inventory;

    /** Minimum time interval between purchasing operations. */
    TimePeriod min_interval;

    /** Maximum time interval between purchasing operations. */
    TimePeriod max_interval;

    /** Minimum purchasing quantity.<br>
      * The default value is 0, meaning no minimum.
      */
    double size_minimum;

    /** Maximum purchasing quantity.<br>
      * The default value is 0, meaning no maximum limit.
      */
    double size_maximum;

    /** Purchases are always rounded up to a multiple of this quantity.<br>
      * The default value is 0, meaning no multiple needs to be applied.
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
      public Solvable
{
  public:
    /** Destructor. */
    virtual DECLARE_EXPORT ~Flow();

    /** Constructor. */
    explicit Flow(Operation* o, Buffer* b, double q) : quantity(q)
    {
      setOperation(o);
      setBuffer(b);
      validate(ADD);
    }

    /** Returns the operation. */
    Operation* getOperation() const {return getPtrA();}

    /** Updates the operation of this flow. This method can be called only ONCE
      * for each flow. In case that doesn't suit you, delete the existing flow
      * and create a new one.
      */
    void setOperation(Operation* o) { if (o) setPtrA(o,o->getFlows());}

    /** Returns true if this flow consumes material from the buffer. */
    bool isConsumer() const {return quantity < 0;}

    /** Returns true if this flow produces material into the buffer. */
    bool isProducer() const {return quantity >= 0;}

    /** Returns the material flow PER UNIT of the operationplan. */
    double getQuantity() const {return quantity;}

    /** Updates the material flow PER UNIT of the operationplan. Existing
      * flowplans are NOT updated to take the new quantity in effect. Only new
      * operationplans and updates to existing ones will use the new quantity
      * value.
      */
    void setQuantity(double f) {quantity = f;}

    /** Returns the buffer. */
    Buffer* getBuffer() const {return getPtrB();}

    /** Updates the buffer of this flow. This method can be called only ONCE
      * for each flow. In case that doesn't suit you, delete the existing flow
      * and create a new one.
      */
    void setBuffer(Buffer* b) { if (b) setPtrB(b,b->getFlows());}

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

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
    virtual size_t getSize() const {return sizeof(Flow);}

  protected:
    /** Default constructor. */
    explicit Flow() : quantity(0.0) {}

  private:
    /** Verifies whether a flow meets all requirements to be valid. */
    DECLARE_EXPORT void validate(Action action);

    /** Quantity of the flow. */
    double quantity;
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

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(FlowStart);}
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

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(FlowEnd);}
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
    /** Constructor. */
    explicit DECLARE_EXPORT FlowPlan(OperationPlan*, const Flow*);

    /** Returns the flow of which this is an plan instance. */
    Flow* getFlow() const {return fl;}

    /** Returns the operationplan owning this flowplan. */
    OperationPlan* getOperationPlan() const {return oper;}

    /** Destructor. */
    virtual ~FlowPlan()
    {
      Buffer* b = getFlow()->getBuffer();
      b->setChanged();
      b->flowplans.erase(this);
    }

    /** Writing the element.
      * This method has the same prototype as a usual instance of the Object
      * class, but this is only superficial: FlowPlan isn't a subclass of
      * Object at all.
      */
    void DECLARE_EXPORT writeElement
      (XMLOutput*, const Keyword&, mode=DEFAULT) const;

    /** Updates the quantity of the flowplan by changing the quantity of the
      * operationplan owning this flowplan.<br>
      * The boolean parameter is used to control whether to round up or down
      * in case the operation quantity must be a multiple.
      */
    void setQuantity(double qty, bool b=false, bool u = true)
    {
      if (getFlow()->getEffective().within(getDate()))
        oper->setQuantity(qty / getFlow()->getQuantity(), b, u);
    }

    /** This function needs to be called whenever the flowplan date or 
      * quantity are changed.
      */
    DECLARE_EXPORT void update();

    /** Return a pointer to the timeline data structure owning this flowplan. */
    TimeLine<FlowPlan>* getTimeLine() const 
    {return &(getFlow()->getBuffer()->flowplans);}

    /** Returns true when the flowplan is hidden.<br>
      * This is determined by looking at whether the flow is hidden or not. 
      */
    bool getHidden() const {return fl->getHidden();}
};


inline double Flow::getFlowplanQuantity(const FlowPlan* fl) const
{
  return getEffective().within(fl->getDate()) ?
    fl->getOperationPlan()->getQuantity() * getQuantity() : 
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


/** @brief This class represents a workcentre, a physical or logical
  * representation of capacity.
  */
class Resource : public HasHierarchy<Resource>,
      public HasLevel, public Plannable, public HasDescription
{
    friend class Load;
    friend class LoadPlan;

  public:
    /** Constructor. */
    explicit Resource(const string& str) : HasHierarchy<Resource>(str),
        max_cal(NULL), loc(NULL), cost(1.0), hidden(false) {};

    /** Destructor. */
    virtual DECLARE_EXPORT ~Resource();

    /** Updates the size of a resource. */
    DECLARE_EXPORT void setMaximum(CalendarDouble* c);

    /** Return a pointer to the maximum capacity profile. */
    CalendarDouble* getMaximum() const {return max_cal;}

    /** Returns the cost of using 1 unit of this resource for 1 hour.<br>
      * The default value is 1.0.
      */
    double getCost() const {return cost;}

    /** Update the cost of using 1 unit of this resource for 1 hour. */
    void setCost(const double c) {cost = c;}

    typedef Association<Operation,Resource,Load>::ListB loadlist;
    typedef TimeLine<LoadPlan> loadplanlist;

    /** Returns a reference to the list of loadplans. */
    const loadplanlist& getLoadPlans() const {return loadplans;}

    /** Returns a reference to the list of loadplans. */
    loadplanlist& getLoadPlans() {return loadplans;}

    /** Returns a constant reference to the list of loads. It defines
      * which operations are using the resource.
      */
    const loadlist& getLoads() const {return loads;}

    /** Return the load that is associates a given operation with this
      * resource. Returns NULL is no such load exists. */
    Load* findLoad(const Operation* o, Date d) const 
    {return loads.find(o,d);}

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    DECLARE_EXPORT void beginElement (XMLInput&, const Attribute&);

    size_t extrasize() const 
    {return getName().size() + HasDescription::extrasize();}

    /** Returns the location of this resource. */
    Location* getLocation() const {return loc;}

    /** Updates the location of this resource. */
    void setLocation(Location* i) {loc = i;}

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Deletes all operationplans loading this resource. The boolean parameter
      * controls whether we delete also locked operationplans or not.
      */
    DECLARE_EXPORT void deleteOperationPlans(bool = false);

    /** Recompute the problems of this resource. */
    virtual DECLARE_EXPORT void updateProblems();

    void setHidden(bool b) {if (hidden!=b) setChanged(); hidden = b;}
    bool getHidden() const {return hidden;}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  private:
    /** This calendar is used to updates to the resource size. */
    CalendarDouble* max_cal;

    /** Stores the collection of all loadplans of this resource. */
    loadplanlist loadplans;

    /** This is a list of all load models that are linking this resource with
      * operations. */
    loadlist loads;

    /** A pointer to the location of the resource. */
    Location* loc;

    /** The cost of using 1 unit of this resource for 1 hour. */
    double cost;

    /** Specifies whether this resource is hidden for serialization. */
    bool hidden;
};


/** @brief This class is the default implementation of the abstract
  * Resource class.
  */
class ResourceDefault : public Resource
{
  public:
    explicit ResourceDefault(const string& str) : Resource(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {return sizeof(ResourceDefault) + Resource::extrasize();}
};


/** @brief This class represents a resource that'll never have any
  * capacity shortage. */
class ResourceInfinite : public Resource
{
  public:
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    virtual const MetaClass& getType() const {return metadata;}
    explicit ResourceInfinite(const string& c) : Resource(c)
      {setDetectProblems(false);}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {return sizeof(ResourceInfinite) + Resource::extrasize();}
};


/** @brief This class links a resource to a certain operation. */
class Load
      : public Object, public Association<Operation,Resource,Load>::Node,
      public Solvable
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
      validate(ADD);
    }

    /** Destructor. */
    DECLARE_EXPORT ~Load();

    /** Returns the operation consuming the resource capacity. */
    Operation* getOperation() const {return getPtrA();}

    /** Updates the operation being loaded. This method can only be called
      * once for a load. */
    void setOperation(Operation* o) {if (o) setPtrA(o,o->getLoads());}

    /** Returns the capacity resource being consumed. */
    Resource* getResource() const {return getPtrB();}

    /** Updates the capacity being consumed. This method can only be called
      * once on a resource. */
    void setResource(Resource* r) {if (r) setPtrB(r,r->getLoads());}

    /** Returns how much capacity is consumed during the duration of the
      * operationplan. */
    double getQuantity() const {return qty;}

    /** Updates the quantity of the load.
      * @exception DataException When a negative number is passed.
      */
    void setQuantity(double f)
    {
      if (f < 0) throw DataException("Load quantity can't be negative");
      qty = f;
    }

    /** This method holds the logic the compute the date of a loadplan. */
    virtual Date getLoadplanDate(const LoadPlan*) const;

    /** This method holds the logic the compute the quantity of a loadplan. */
    virtual double getLoadplanQuantity(const LoadPlan*) const;

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    bool getHidden() const
     {
      return (getResource() && getResource()->getHidden())
        || (getOperation() && getOperation()->getHidden());
    }
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
    virtual size_t getSize() const {return sizeof(Load);}

    /** Default constructor. */
    Load() : qty(1.0) {}

  private:
    /** This method is called to check the validity of the object. It will
      * delete the invalid loads: be careful with the 'this' pointer after
      * calling this method!
      */
    DECLARE_EXPORT void validate(Action action);

    /** Stores how much capacity is consumed during the duration of an
      * operationplan. */
    double qty;
};




/** @brief This is the (logical) top class of the complete model.
  *
  * This is a singleton class: only a single instance can be created.
  * The data model has other limitations that make it not obvious to support
  * building multiple models/plans in memory of the same application: e.g.
  * the operations, resources, problems, operationplans... etc are all
  * implemented in static, global lists. An entity can't be simply linked with
  * a particular plan if multiple ones would exist.
  */
class Plan : public Plannable
{
    friend void LibraryModel::initialize();
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
    Plan() : cur_Date(Date::now()) {}

  public:
    /** Return a pointer to the singleton plan object.
      * The singleton object is created during the initialization of the
      * library.
      */
    static Plan& instance() {return *thePlan;}

    /** Destructor.
      * @warning In multi threaded applications, the destructor is never called
      * and the plan object leaks when we exit the application.
      * In single-threaded applications this function is called properly, when
      * the static plan variable is deleted.
      */
    DECLARE_EXPORT ~Plan();

    /** Returns the plan name. */
    const string& getName() const {return name;}

    /** Updates the plan name. */
    void setName(const string& s) {name = s;}

    /** Returns the current Date of the plan. */
    const Date & getCurrent() const {return cur_Date;}

    /** Updates the current date of the plan. This method can be relatively
      * heavy in a plan where operationplans already exist, since the
      * detection for BeforeCurrent problems needs to be rerun.
      */
    DECLARE_EXPORT void setCurrent(Date);

    /** Returns the description of the plan. */
    const string& getDescription() const {return descr;}

    /** Updates the description of the plan. */
    void setDescription(const string& str) {descr = str;}

    /** This method writes out the model information. Depending on a flag in
      * the XMLOutput object a complete model is written, or only the
      * dynamic plan information.
      * @see CommandSave, CommandSavePlan
      */
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);

    virtual void updateProblems() {};

    /** This method basically solves the whole planning problem. */
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
    virtual size_t getSize() const
      {return sizeof(Plan) + name.size() + descr.size();}
};


/** @brief This command is used for reading XML input. The input comes either
  * from a flatfile, or from the standard input.
  *
  * The command is not thread-safe: multiple threads can simultaneously access
  * the same objects.
  */
class CommandReadXMLFile : public Command
{
  public:
    /** Constructor. If no file or directory name is passed or specified later
      * the standard input will be read during execution of the command. */
    CommandReadXMLFile(const char* s = NULL, bool v = true, bool o = false)
        : validate(v), validate_only(o) {if (s) filename = s;}

    /** Constructor. */
    CommandReadXMLFile(const string& s, bool v = true, bool o = false)
        : filename(s), validate(v), validate_only(o) {}

    /** Update the name of the input file. */
    void setFileName(const string& v) {filename = v;}

    /** Returns the name of the input file. */
    string getFileName() {return filename;}

    /** Enables or disables the validation. */
    void setValidate(bool b) {validate = b;}

    /** Returns true if the schema validation has been enabled. */
    bool getValidate() {return validate;}

    /** Only validate the input, do not really execute it. */
    void setValidateOnly(bool b) {validate_only = b;}

    /** Returns whether we only need to validate to data, or really execute
      * them too. */
    bool getValidateOnly() {return validate_only;}

    /** The commit action reads the input. If a filename is specified (either
      * in the constructor or with the setFileName function), a flat file is
      * read. Otherwise, the standard input is read. */
    DECLARE_EXPORT void execute();

    /** Python interface for this command. */
    static DECLARE_EXPORT PyObject* executePython(PyObject*, PyObject*);

    string getDescription() const
    {
      if (filename.empty())
        return "parsing xml input from standard input";
      else
        return "parsing xml input from file '" + filename + "'";
    }

  private:
    /** Name of the input to be read. An empty string means that we want to
      * read from standard input rather than a file. */
    string filename;

    /** Specifies whether or not the input file needs to be validated against
      * the schema definition. The validation is switched ON by default.
      * Switching it ON is recommended in situations where there is not
      * 100% garantuee on the validity of the input data.
      */
    bool validate;

    /** If set to true the input data are validated against the schema, but the
      * contents isn't executed. The default value is false. */
    bool validate_only;
};


/** @brief This command is used for reading XML input from a certain string.
  *
  * The command is not thread-safe: multiple threads can simultaneously access
  * the same objects.
  */
class CommandReadXMLString : public Command
{
  public:
    /** Constructor. */
    CommandReadXMLString(const string& s, const bool v=true, const bool o=false)
        : data(s), validate(v), validate_only(o) {};

    /** Default constructor. */
    CommandReadXMLString(const bool v=true, const bool o=false)
        : validate(v), validate_only(o) {};

    /** Updates the data string. */
    void setData(const string& v) {data = v;}

    /** Returns the data string. */
    string getData() {return data;}

    /** Enables or disables the validation. */
    void setValidate(bool b) {validate = b;}

    /** Returns true if the schema validation has been enabled. */
    bool getValidate() {return validate;}

    /** Only validate the input, do not really execute it. */
    void setValidateOnly(bool b) {validate_only = b;}

    /** Returns whether we only need to validate to data, or really execute
      * them too. */
    bool getValidateOnly() {return validate_only;}

    /** The commit action reads the input. */
    DECLARE_EXPORT void execute();

    /** Python interface for this command. */
    static DECLARE_EXPORT PyObject* executePython(PyObject *, PyObject *);

    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    string getDescription() const {return "parsing xml input string";}

  private:
    /** Name of the input to be read. An empty string means that we want to
      * read from standard input rather than a file. */
    string data;

    /** Specifies whether or not the input file needs to be validated against
      * the schema definition. The validation is switched ON by default.
      * Switching it ON is recommended in situations where there is not
      * 100% garantuee on the validity of the input data.
      */
    bool validate;

    /** If set to true the input data are validated against the schema, but the
      * contents isn't executed. The default value is false. */
    bool validate_only;
};


/** @brief This command writes the complete model to an XML-file.
  *
  * Both the static model (i.e. items, locations, buffers, resources,
  * calendars, etc...) and the dynamic data (i.e. the actual plan including
  * the operationplans, demand, problems, etc...).<br>
  * The format is such that the output file can be re-read to restore the
  * very same model.<br>
  * The data is written by the execute() function.
  * @see CommandSavePlan
  */
class CommandSave : public Command
{
  public:
    CommandSave(const string& v = "plan.out")
        : filename(v), content(XMLOutput::STANDARD) {};
    virtual ~CommandSave() {};
    string getFileName() const {return filename;}
    void setFileName(const string& v) {filename = v;}
    DECLARE_EXPORT void execute();

    /** Python interface to this command. */
    static DECLARE_EXPORT PyObject* executePython(PyObject*, PyObject*);

    string getDescription() const
      {return "saving the complete model into file '" + filename + "'";}
    XMLOutput::content_type getContent() const {return content;}
    void setContent(XMLOutput::content_type t) {content = t;}
  private:
    string filename;
    string headerstart;
    string headeratts;
    XMLOutput::content_type content;
};


/** @brief This command writes the dynamic part of the plan to an  text file.
  *
  * This saved information covers the buffer flowplans, operationplans,
  * resource loading, demand, problems, etc...<br>
  * The main use of this function is in the test suite: a simple text file
  * comparison allows us to identify changes quickly. The output format is
  * only to be seen in this context of testing, and is not intended to be used
  * as an official method for publishing plans to other systems.<br>
  * The data file is written by the execute() function.
  * @see CommandSave
  */
class CommandSavePlan : public Command
{
  public:
    CommandSavePlan(const string& v = "plan.out") : filename(v) {};
    string getFileName() const {return filename;}
    void setFileName(const string& v) {filename = v;}
    DECLARE_EXPORT void execute();

    /** Python interface to this command. */
    static DECLARE_EXPORT PyObject* executePython(PyObject*, PyObject*);

    DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    string getDescription() const
      {return "saving the plan into text file '" + filename + "'";}
  private:
    string filename;
};


/** @brief This command prints a summary of the dynamically allocated memory
  * to the standard output. This is useful for understanding better the size
  * of your model.
  *
  * The numbers reported by this function won't match the memory size as
  * reported by the operating system, since the dynamically allocated memory
  * is only a part of the total memory used by a program.
  */
class CommandPlanSize : public Command
{
  public:
    CommandPlanSize() {};
    DECLARE_EXPORT void execute();
    static PyObject* executePython(PyObject* self, PyObject* args)
      {CommandPlanSize x;x.execute(); return Py_BuildValue("");}
    void undo() {}
    bool undoable() const {return true;}
    string getDescription() const {return "printing the model size";}
};


/** @brief This command deletes part of the model or the plan from memory.
  *
  * The class allows the following modes to control what to delete:
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
class CommandErase : public Command
{
  public:
    CommandErase(bool staticAlso = false) : deleteStaticModel(staticAlso) {};

    DECLARE_EXPORT void execute();

    /** Python interface to this command. */
    static DECLARE_EXPORT PyObject* executePython(PyObject*, PyObject*);

    string getDescription() const
    {
      return deleteStaticModel ? "Erasing the model" : "Erasing the plan";
    }
    bool getDeleteStaticModel() const {return deleteStaticModel;}
    void setDeleteStaticModel(bool b) {deleteStaticModel = b;}
  private:
    /** Flags whether to delete the complete static model or only the
      * dynamic plan information. */
    bool deleteStaticModel;
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
    typedef slist<OperationPlan*> OperationPlan_list;

    /** Constructor. */
    explicit Demand(const string& str) : HasHierarchy<Demand>(str),
      it(NULL), oper(NULL), cust(NULL), qty(0.0), prio(0),
      maxLateness(TimePeriod::MAX), minShipment(0), hidden(false) {}

    /** Destructor. Deleting the demand will also delete all delivery operation
      * plans */
    virtual ~Demand() {deleteOperationPlans(true);}

    /** Returns the quantity of the demand. */
    double getQuantity() const {return qty;}

    /** Updates the quantity of the demand. The quantity must be be greater
      * than or equal to 0. */
    virtual DECLARE_EXPORT void setQuantity(double);

    /** Returns the priority of the demand.<br>
      * Lower numbers indicate a higher priority level.
      */
    int getPriority() const {return prio;}

    /** Updates the due date of the demand.<br>
      * Lower numbers indicate a higher priority level.
      */
    virtual void setPriority(int i) {prio=i; setChanged();}

    /** Returns the item/product being requested. */
    Item* getItem() const {return it;}

    /** Updates the item/product being requested. */
    virtual void setItem(Item *i) {it=i; setChanged();}

    /** This fields points to an operation that is to be used to plan the
      * demand. By default, the field is left to NULL and the demand will then
      * be planned using the delivery operation of its item.
      * @see Item::getDelivery()
      */
    Operation* getOperation() const {return oper;}

    /** This function returns the operation that is to be used to satisfy this
      * demand. In sequence of priority this goes as follows:
      *   1) If the "operation" field on the demand is set, use it.
      *   2) Otherwise, use the "delivery" field of the requested item.
      *   3) Else, return NULL. This demand can't be satisfied!
      */
    DECLARE_EXPORT Operation* getDeliveryOperation() const;

    /** Returns the cluster which this demand belongs to. */
    int getCluster() const
    {
      Operation* o = getDeliveryOperation();
      return o ? o->getCluster() : 0;
    }

    /** Updates the operation being used to plan the demand. */
    virtual void setOperation(Operation* o) {oper=o; setChanged();}

    /** Returns the delivery operationplan list. */
    DECLARE_EXPORT const OperationPlan_list& getDelivery() const;

    /** Adds a delivery operationplan for this demand. If the policy
      * SINGLEDELIVERY is set, any previous delivery operationplan is
      * unregistered first.
      */
    DECLARE_EXPORT void addDelivery(OperationPlan *o);

    /** Removes a delivery operationplan for this demand. */
    DECLARE_EXPORT void removeDelivery(OperationPlan *o);

    /** Deletes all delivery operationplans of this demand. The boolean
      * parameter controls whether we delete also locked operationplans or not.
      */
    DECLARE_EXPORT void deleteOperationPlans(bool deleteLockedOpplans = false);

    /** Returns the due date of the demand. */
    const Date& getDue() const {return dueDate;}

    /** Updates the due date of the demand. */
    virtual void setDue(Date d) {dueDate = d; setChanged();}

    /** Returns the customer. */
    Customer* getCustomer() const { return cust; }

    /** Updates the customer. */
    virtual void setCustomer(Customer* c) { cust = c; setChanged(); }

    /** Returns the total amount that has been planned. */
    DECLARE_EXPORT double getPlannedQuantity() const;

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    virtual DECLARE_EXPORT void endElement(XMLInput&, const Attribute&, const DataElement&);
    virtual DECLARE_EXPORT void beginElement (XMLInput&, const Attribute&);

    size_t extrasize() const 
    {
      return getName().size() + HasDescription::extrasize() 
        + sizeof(void*) * 2 * deli.size();
    }

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Return the maximum delay allowed in satisfying this demand.<br>
      * The default value is infinite.
      */
    TimePeriod getMaxLateness() const {return maxLateness;}

    /** Updates the maximum allowed lateness for this demand.<br>
      * The default value is infinite.<br>
      * The argument must be a positive time period.
      */
    virtual void setMaxLateness(TimePeriod m)
    {
      if (m < 0L)
        throw DataException("The maximum demand lateness must be positive");
      maxLateness = m;
    }

    /** Return the minimum shipment quantity allowed in satisfying this 
      * demand.<br>
      * The default value is 0, which allows deliveries of any size.
      */
    double getMinShipment() const {return minShipment;}

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
    void setHidden(bool b) {hidden = b;}

    /** Returns true if this demand is to be hidden from serialization. */
    bool getHidden() const {return hidden;}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  private:
    /** Requested item. */
    Item *it;

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
      * The default value is TimePeriod::MAX.
      */
    TimePeriod maxLateness;

    /** Minimum size for a delivery operation plan satisfying this demand. */
    double minShipment;

    /** Hide this demand or not. */
    bool hidden;

    /** A list of operation plans to deliver this demand. */
    OperationPlan_list deli;
};


/** @brief This class is the default implementation of the abstract
  * Demand class. */
class DemandDefault : public Demand
{
  public:
    explicit DemandDefault(const string& str) : Demand(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {return sizeof(DemandDefault) + Demand::extrasize();}
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
    OperationPlan* getOperationPlan() const {return oper;}

    /** Return the load of which this is a plan instance. */
    Load* getLoad() const {return ld;}

    /** Return true when this loadplan marks the start of an operationplan. */
    bool isStart() const {return start_or_end == START;}

    /** Destructor. */
    virtual ~LoadPlan()
    {
      ld->getResource()->setChanged();
      ld->getResource()->loadplans.erase(this);
    }

    /** This function needs to be called whenever the loadplan date or 
      * quantity are changed.
      */
    DECLARE_EXPORT void update();
    
    /** Return a pointer to the timeline data structure owning this loadplan. */
    TimeLine<LoadPlan>* getTimeLine() const 
    {return &(ld->getResource()->loadplans);}
  
    /** Returns true when the loadplan is hidden.<br>
      * This is determined by looking at whether the load is hidden or not. 
      */
    bool getHidden() const {return ld->getHidden();}

    /** Each operationplan has 2 loadplans per load: one at the start,
      * when the capacity consumption starts, and one at the end, when the
      * capacity consumption ends.<br>
      * This method returns the "companion" loadplan. It is not very
      * scalable: the performance is linear with the number of loadplans
      * on the resource.
      */
    DECLARE_EXPORT LoadPlan* getOtherLoadPlan() const;

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
  if (!lp->getOperationPlan()->getDates().overlap(getEffective()))
    // Load is not effective during this time
    return 0.0;
  return lp->isStart() ? getQuantity() : -getQuantity();
}



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
      ch << "Job '" << static_cast<OperationPlan*>(getOwner())->getIdentifier()
      << "' planned in the past";
      return ch.str();
    }
    bool isFeasible() const {return false;}
    double getWeight() const
    {return dynamic_cast<OperationPlan*>(getOwner())->getQuantity();}
    explicit ProblemBeforeCurrent(OperationPlan* o) : Problem(o)
      {addProblem();}
    ~ProblemBeforeCurrent() {removeProblem();}
    const DateRange getDateRange() const
    {
      OperationPlan *o = dynamic_cast<OperationPlan*>(getOwner());
      if (o->getDates().getEnd() > Plan::instance().getCurrent())
        return DateRange(o->getDates().getStart(),
            Plan::instance().getCurrent());
      else
        return DateRange(o->getDates().getStart(),
            o->getDates().getEnd());
    }
    size_t getSize() const {return sizeof(ProblemBeforeCurrent);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
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
      ch << "Job '" << static_cast<OperationPlan*>(getOwner())->getIdentifier()
      << "' planned before fence";
      return ch.str();
    }
    bool isFeasible() const {return true;}
    double getWeight() const
    {return static_cast<OperationPlan*>(getOwner())->getQuantity();}
    explicit ProblemBeforeFence(OperationPlan* o) : Problem(o)
      {addProblem();}
    ~ProblemBeforeFence() {removeProblem();}
    const DateRange getDateRange() const
    {
      OperationPlan *o = static_cast<OperationPlan*>(getOwner());
      if (o->getDates().getEnd() > Plan::instance().getCurrent()
          + o->getOperation()->getFence())
        return DateRange(o->getDates().getStart(),
            Plan::instance().getCurrent() + o->getOperation()->getFence());
      else
        return DateRange(o->getDates().getStart(),
            o->getDates().getEnd());
    }
    size_t getSize() const {return sizeof(ProblemBeforeFence);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A problem of this class is created when the sequence of two
  * operationplans in a routing isn't respected.
  */
class ProblemPrecedence : public Problem
{
  public:
    string getDescription() const
    {
      return string("Operation '") + opplan2->getOperation()->getName()
          + "' starts before Operation '"
          + opplan1->getOperation()->getName() +"' ends";
    }
    bool isFeasible() const {return false;}
    /** The weight of the problem is equal to the duration in days. */
    double getWeight() const 
    {
      return static_cast<double>(getDateRange().getDuration()) / 86400;
    }
    explicit ProblemPrecedence
    (Operation* o, OperationPlan* op1, OperationPlan* op2)
        : Problem(o), opplan1(op1), opplan2(op2) {addProblem();}
    ~ProblemPrecedence() {removeProblem();}
    const DateRange getDateRange() const
    {
      return DateRange(opplan2->getDates().getStart(),
          opplan1->getDates().getEnd());
    }
    OperationPlan* getFirstOperationPlan() const {return opplan1;}
    OperationPlan* getSecondOperationPlan() const {return opplan2;}

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
    size_t getSize() const {return sizeof(ProblemPrecedence);} 

  private:
    /** Pointers to the operationplans which violate the sequence.
      * opplan1 is expected to finish before opplan2 starts. */
    OperationPlan *opplan1, *opplan2;
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
      {return string("Demand '") + getDemand()->getName() + "' is not planned";}
    bool isFeasible() const {return false;}
    double getWeight() const {return getDemand()->getQuantity();}
    explicit ProblemDemandNotPlanned(Demand* d) : Problem(d) {addProblem();}
    ~ProblemDemandNotPlanned() {removeProblem();}
    const DateRange getDateRange() const
      {return DateRange(getDemand()->getDue(),getDemand()->getDue());}
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemDemandNotPlanned);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A problem of this class is created when a demand is satisfied later
  * than the accepted tolerance after its due date.
  */
class ProblemLate : public Problem
{
  public:
    DECLARE_EXPORT string getDescription() const;
    bool isFeasible() const {return true;}

    /** The weight is equal to the delay, expressed in days.<br>
      * The quantity being delayed is not included.
      */
    double getWeight() const
    {
      return static_cast<double>(DateRange(
        getDemand()->getDue(),
        (*(getDemand()->getDelivery().begin()))->getDates().getEnd()
        ).getDuration()) / 86400;
    }
    explicit ProblemLate(Demand* d) : Problem(d) {addProblem();}
    ~ProblemLate() {removeProblem();}
    const DateRange getDateRange() const
    {
      assert(getDemand() && !getDemand()->getDelivery().empty());
      return DateRange(getDemand()->getDue(),
          (*(getDemand()->getDelivery().begin()))->getDates().getEnd());
    }
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemLate);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A problem of this class is created when a demand is planned earlier
  * than the accepted tolerance before its due date.
  */
class ProblemEarly : public Problem
{
  public:
    DECLARE_EXPORT string getDescription() const;
    bool isFeasible() const {return true;}
    double getWeight() const 
    {
      return static_cast<double>(DateRange(
        getDemand()->getDue(),
        (*(getDemand()->getDelivery().begin()))->getDates().getEnd()
        ).getDuration()) / 86400;
    }
    explicit ProblemEarly(Demand* d) : Problem(d) {addProblem();}
    ~ProblemEarly() {removeProblem();}
    const DateRange getDateRange() const
    {
      return DateRange(getDemand()->getDue(),
          (*(getDemand()->getDelivery().begin()))->getDates().getEnd());
    }
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemEarly);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
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
    bool isFeasible() const {return true;}
    double getWeight() const
      {return getDemand()->getQuantity() - getDemand()->getPlannedQuantity();}
    explicit ProblemShort(Demand* d) : Problem(d) {addProblem();}
    ~ProblemShort() {removeProblem();}
    const DateRange getDateRange() const
      {return DateRange(getDemand()->getDue(), getDemand()->getDue());}
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemShort);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
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
    bool isFeasible() const {return true;}
    double getWeight() const
      {return getDemand()->getPlannedQuantity() - getDemand()->getQuantity();}
    explicit ProblemExcess(Demand* d) : Problem(d) {addProblem();}
    ~ProblemExcess() {removeProblem();}
    const DateRange getDateRange() const
      {return DateRange(getDemand()->getDue(), getDemand()->getDue());}
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemExcess);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A problem of this class is created when an OperationPlan is planned
  * later than the accepted tolerance after its lpst Date.
  */
class ProblemPlannedLate : public Problem
{
  public:
    string getDescription() const
      {return "Operationplan planned after its lpst date";}
    bool isFeasible() const {return false;}
    /** The weight of the problem is equal to the duration in days. */
    double getWeight() const 
    {
      return static_cast<double>(getDateRange().getDuration()) / 86400;
    }
    explicit ProblemPlannedLate(OperationPlan* o) : Problem(o)
      {addProblem();}
    ~ProblemPlannedLate() {removeProblem();}
    const DateRange getDateRange() const
      {return dynamic_cast<OperationPlan*>(getOwner())->getDates();}

    /** Return the tolerance limit for problem detection. */
    static TimePeriod getAllowedLate() {return allowedLate;}

    /** Update the tolerance limit. Note that this will trigger re-evaluation of
      * all operationplans and existing problems, which can be expensive in a
      * big plan. */
    static void setAllowedLate(TimePeriod p);

    size_t getSize() const {return sizeof(ProblemPlannedLate);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

  private:
    /** This is the time that is allowed between the lpst date and the start
      * date of an operation before a problem is created.
      * The default value is 0. */
    static DECLARE_EXPORT TimePeriod allowedLate;
};


/** @brief A problem of this class is created when a demand is planned earlier
  * than the accepted tolerance before its epst date.
  */
class ProblemPlannedEarly : public Problem
{
  public:
    string getDescription() const
      {return "Operationplan planned before its epst date";}
    bool isFeasible() const {return false;}
    /** The weight of the problem is equal to the duration in days. */
    double getWeight() const 
    {
      return static_cast<double>(getDateRange().getDuration()) / 86400;
    }
    explicit ProblemPlannedEarly(OperationPlan* o) : Problem(o)
      {addProblem();}
    ~ProblemPlannedEarly() {removeProblem();}
    const DateRange getDateRange() const
      {return dynamic_cast<OperationPlan*>(getOwner())->getDates();}

    /** Return the tolerance limit for problem detection. */
    static TimePeriod getAllowedEarly() {return allowedEarly;}

    /** Update the tolerance limit. Note that this will trigger re-evaluation of
      * all operationplans and existing problems, which can be expensive in a
      * big plan. */
    static void setAllowedEarly(TimePeriod p);

    size_t getSize() const {return sizeof(ProblemPlannedEarly);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

  private:
    /** This is the time that is allowed between the epst date and the start
      * date of an operation before a problem is created.
      * The default value is 0. */
    static DECLARE_EXPORT TimePeriod allowedEarly;
};


/** @brief A problem of this class is created when a resource is being
  * overloaded during a certain period of time.
  */
class ProblemCapacityOverload : public Problem
{
  public:
    DECLARE_EXPORT string getDescription() const;
    bool isFeasible() const {return false;}
    double getWeight() const {return qty;}
    ProblemCapacityOverload(Resource* r, DateRange d, double q)
        : Problem(r), qty(q), dr(d) {addProblem();}
    ~ProblemCapacityOverload() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Resource* getResource() const {return dynamic_cast<Resource*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemCapacityOverload);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

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
    bool isFeasible() const {return true;}
    double getWeight() const {return qty;}
    ProblemCapacityUnderload(Resource* r, DateRange d, double q)
        : Problem(r), qty(q), dr(d) {addProblem();}
    ~ProblemCapacityUnderload() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Resource* getResource() const {return dynamic_cast<Resource*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemCapacityUnderload);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

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
    bool isFeasible() const {return false;}
    double getWeight() const {return qty;}
    ProblemMaterialShortage(Buffer* b, Date st, Date nd, double q)
        : Problem(b), qty(q), dr(st,nd) {addProblem();}
    ~ProblemMaterialShortage() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Buffer* getBuffer() const {return dynamic_cast<Buffer*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemMaterialShortage);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

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
    bool isFeasible() const {return true;}
    double getWeight() const {return qty;}
    ProblemMaterialExcess(Buffer* b, Date st, Date nd, double q)
        : Problem(b), qty(q), dr(st,nd) {addProblem();}
    ~ProblemMaterialExcess() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Buffer* getBuffer() const {return dynamic_cast<Buffer*>(getOwner());}
    size_t getSize() const {return sizeof(ProblemMaterialExcess);} 

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

  private:
    /** Excess quantity. */
    double qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** @brief This command is used to create an operationplan.
  *
  * The operationplan will have its load and loadplans created when the
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
    void execute()
    {
      if (opplan)
      {
        opplan->initialize();
        opplan = NULL; // Avoid executing / initializing more than once
      }
    }
    void undo() {delete opplan; opplan = NULL;}
    bool undoable() const {return true;}
    ~CommandCreateOperationPlan() {if (opplan) delete opplan;}
    OperationPlan *getOperationPlan() const {return opplan;}
    string getDescription() const
    {
      return "creating a new operationplan for operation '"
          + (opplan ? string(opplan->getOperation()->getName()) : string("NULL"))
          + "'";
    }

  private:
    /** Pointer to the newly created operationplan. */
    OperationPlan *opplan;
};


/** @brief This command is used to delete an operationplan.
  *
  * The operationplan will be deleted when the .
  */
class CommandDeleteOperationPlan : public Command
{
  public:
    /** Constructor.<br>
      * Unlike most other commands the constructor already executes the deletion.
      */
    DECLARE_EXPORT CommandDeleteOperationPlan(OperationPlan* o);
    void execute() {oper = NULL;}
    DECLARE_EXPORT void undo();
    bool undoable() const {return true;}
    ~CommandDeleteOperationPlan() {if (oper) undo();}
    DECLARE_EXPORT string getDescription() const;

  private:
    /** Operation pointer of the original operationplan. */
    Operation *oper;

    /** Daterange of the original operationplan. */
    DateRange dates;

    /** Quantity of the original operationplan. */
    double qty;

    /** Identifier of the original operationplan. */
    long unsigned id;

    /** Demand pointer of the original operationplan. */
    Demand *dmd;

    /** Owner of the original operationplan. */
    OperationPlan *ow;
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
      * @param newDate New date of the operationplan.
      * @param startOrEnd Specifies whether the new date is the start (=false)
      * or end date (=true). By default we use the end date.
      * @param newQty New quantity of the operationplan.The default is -1,
      * which indicates to leave the quantity unchanged.
      */
    DECLARE_EXPORT CommandMoveOperationPlan (OperationPlan* opplanptr,
      Date newDate, bool startOrEnd=true, double newQty = -1.0);
    void execute() { opplan=NULL; }
    DECLARE_EXPORT void undo();
    bool undoable() const {return true;}
    ~CommandMoveOperationPlan() { if (opplan) undo();}
    OperationPlan* getOperationPlan() const {return opplan;}
    DECLARE_EXPORT string getDescription() const;

    /** Set another date for the operationplan.
      * @param newdate New start- or end date.
      */
    DECLARE_EXPORT void setDate(Date newdate);

    /** Set another quantity for the operationplan.
      * @param newqty New quantity.
      */
    DECLARE_EXPORT void setQuantity(double newqty);

  private:
    /** This is a pointer to the operationplan being moved. */
    OperationPlan *opplan;

    /** This flag specifies whether we keep the new date is a new start or a
      * new end date for the operationplan. */
    bool prefer_end;

    /** These are the original dates of the operationplan before its move. */
    DateRange originaldates;

    /** This is the quantity of the operationplan before the command. */
    double originalqty;
};


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
    explicit EntityIterator(unsigned short i) : type(i) {}

    /** Copy constructor. */
    DECLARE_EXPORT EntityIterator(const EntityIterator& o);

    /** Assignment operator. */
    DECLARE_EXPORT EntityIterator& operator=(const EntityIterator& o);

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
    bool operator == (const EntityIterator& t) const {return !(*this != t);}

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
class Problem::const_iterator
{
    friend class Problem;
  private:
    /** A pointer to the current problem. If this pointer is NULL, we are
      * at the end of the list. */
    Problem* iter;
    HasProblems* owner;
    HasProblems::EntityIterator eiter;

  public:
    /** Creates an iterator that will loop through the problems of a
      * single entity only. <BR>
      * This constructor is also used to create a end-iterator, when passed
      * a NULL pointer as argument.
      */
    explicit const_iterator(HasProblems* o) : iter(o ? o->firstProblem : NULL),
      owner(o), eiter(4) {}

    /** Creates an iterator that will loop through the problems of all
      * entities. */
    explicit const_iterator() : owner(NULL)
    {
      // Loop till we find an entity with a problem
      while (eiter!=HasProblems::endEntity() && !(eiter->firstProblem))
        ++eiter;
      // Found a first problem, or no problem at all
      iter = (eiter!=HasProblems::endEntity()) ? eiter->firstProblem : NULL;
    }

    /** Pre-increment operator. */
    DECLARE_EXPORT const_iterator& operator++();

    /** Inequality operator. */
    bool operator != (const const_iterator& t) const {return iter!=t.iter;}

    /** Equality operator. */
    bool operator == (const const_iterator& t) const {return iter==t.iter;}

    Problem& operator*() const {return *iter;}
    Problem* operator->() const {return iter;}
};


/** @brief This class allows upstream and downstream navigation through
  * the plan.
  *
  * Downstream navigation follows the material stream from raw materials
  * towards the end item demand.<br>
  * Upstream navigation traces back the material flow from the end item till
  * the raw materials.<br>
  * The class is implemented as an STL-like iterator.
  */
class PeggingIterator
{
  public:
    /** Constructor. */
    DECLARE_EXPORT PeggingIterator(const Demand* e);

    /** Constructor. */
    PeggingIterator(const FlowPlan* e, bool b = true) : downstream(b)
    {
      if (!e) return;
      if (downstream)
        states.push(state(0,abs(e->getQuantity()),1.0,e,NULL));
      else
        states.push(state(0,abs(e->getQuantity()),1.0,NULL,e));
    }

    /** Return the operationplan consuming the material. */
    OperationPlan* getConsumingOperationplan() const
    {
      const FlowPlan* x = states.top().cons_flowplan;
      return x ? x->getOperationPlan() : NULL;
    }

    /** Return the material buffer through which we are pegging. */
    Buffer *getBuffer() const
    {
      const FlowPlan* x = states.top().prod_flowplan;
      if (!x) x = states.top().cons_flowplan;
      return x ? x->getFlow()->getBuffer() : NULL;
    }

    /** Return the operationplan producing the material. */
    OperationPlan* getProducingOperationplan() const
    {
      const FlowPlan* x = states.top().prod_flowplan;
      return x ? x->getOperationPlan() : NULL;
    }

    /** Return the date when the material is consumed. */
    Date getConsumingDate() const
    {
      const FlowPlan* x = states.top().cons_flowplan;
      return x ? x->getDate() : Date::infinitePast;
    }

    /** Return the date when the material is produced. */
    Date getProducingDate() const
    {
      const FlowPlan* x = states.top().prod_flowplan;
      return x ? x->getDate() : Date::infinitePast;
    }

    /** Returns the recursion depth of the iterator. The original flowplan
      * is at level 0, and each level (either upstream or downstream)
      * increments the value by 1.
      */
    short getLevel() const {return states.top().level;}

    /** Returns the quantity of the demand that is linked to this pegging
      * record.
      */
    double getQuantityDemand() const {return states.top().qty;}

    /** Returns the quantity of the buffer flowplans that is linked to this
      * pegging record.
      */
    double getQuantityBuffer() const
    {
      const state& t = states.top();
      return t.prod_flowplan
        ? t.factor * t.prod_flowplan->getOperationPlan()->getQuantity()
        : 0;
    }

    /** Returns which portion of the current flowplan is fed/supplied by the
      * original flowplan. */
    double getFactor() const {return states.top().factor;}

    /** Returns false if the flowplan remained unpegged, i.e. it wasn't
      * -either completely or paritally- unconsumed at the next level.
      */
    bool getPegged() const {return states.top().pegged;}

    /** Move the iterator foward to the next downstream flowplan. */
    DECLARE_EXPORT PeggingIterator& operator++();

    /** Move the iterator foward to the next downstream flowplan.<br>
      * This post-increment operator is less efficient than the pre-increment
      * operator.
      */
    PeggingIterator operator++(int)
      {PeggingIterator tmp = *this; ++*this; return tmp;}

    /** Move the iterator foward to the next upstream flowplan. */
    DECLARE_EXPORT PeggingIterator& operator--();

    /** Move the iterator foward to the next upstream flowplan.<br>
      * This post-increment operator is less efficient than the pre-decrement
      * operator.
      */
    PeggingIterator operator--(int)
      {PeggingIterator tmp = *this; --*this; return tmp;}

    /** Comparison operator. */
    bool operator==(const PeggingIterator& x) const {return states == x.states;}

    /** Inequality operator. */
    bool operator!=(const PeggingIterator& x) const {return states != x.states;}

    /** Conversion operator to a boolean value.
      * The return value is true when the iterator still has next elements to
      * explore. Returns false when the iteration is finished.
      */
    operator bool () const { return !states.empty(); }

    /** Update the stack. */
    DECLARE_EXPORT void updateStack(short, double, double, const FlowPlan*, const FlowPlan*, bool = true);

    /** Returns true if this is a downstream iterator. */
    bool isDownstream() {return downstream;}

  private:
    /** This structure is used to keep track of the iterator states during the
      * iteration. */
    struct state
    {
      /** Stores the quantity of this flowplan that is involved. */
      double qty;

      /** Stores what portion of the flowplan is involved with the root flowplan
        * where the recursion started.
        */
      double factor;

      /** Keeps track of the number of levels we're removed from the root
        * flowplan where the recursion started.
        */
      short level;

      /** The current flowplan. */
      const FlowPlan* cons_flowplan;

      /** The current flowplan. */
      const FlowPlan* prod_flowplan;

      /** Set to false when unpegged quantities are involved. */
      bool pegged;

      /** Constructor. */
      state(unsigned int l, double d, double f,
        const FlowPlan* fc, const FlowPlan* fp, bool p = true)
          : qty(d), factor(f), level(l),
          cons_flowplan(fc), prod_flowplan(fp), pegged(p) {};

      /** Inequality operator. */
      bool operator != (const state& s) const
      {
        return cons_flowplan != s.cons_flowplan
          || prod_flowplan != s.prod_flowplan
          || level != s.level;
      }

      /** Equality operator. */
      bool operator == (const state& s) const
      {
        return cons_flowplan == s.cons_flowplan
          && prod_flowplan == s.prod_flowplan
          && level == s.level;
      }
    };

    /** A type to hold the iterator state. */
    typedef stack < state > statestack;

    /** A stack is used to store the iterator state. */
    statestack states;

    /* Auxilary function to make recursive code possible. */
    DECLARE_EXPORT void followPegging(const OperationPlan*, short, double, double);

    /** Convenience variable during stack updates.
      * Depending on the value of this field, either the top element in the
      * stack is updated or a new state is pushed on the stack.
      */
    bool first;

    /** Downstream or upstream iterator. */
    bool downstream;
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
      {return b.curflowplan != curflowplan;}
    bool operator == (const FlowPlanIterator &b) const
      {return b.curflowplan == curflowplan;}
    FlowPlanIterator& operator++()
    {
      prevflowplan = curflowplan;
      if (curflowplan) curflowplan = curflowplan->nextFlowPlan;
      return *this;
    }
    FlowPlanIterator operator++(int)
      {FlowPlanIterator tmp = *this; ++*this; return tmp;}
    FlowPlan* operator ->() const {return curflowplan;}
    FlowPlan& operator *() const {return *curflowplan;}
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
};

inline OperationPlan::FlowPlanIterator OperationPlan::beginFlowPlans() const
  { return OperationPlan::FlowPlanIterator(firstflowplan); }

inline OperationPlan::FlowPlanIterator OperationPlan::endFlowPlans() const
  {return OperationPlan::FlowPlanIterator(NULL);}

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
      {return b.curloadplan != curloadplan;}
    bool operator == (const LoadPlanIterator &b) const
      {return b.curloadplan == curloadplan;}
    LoadPlanIterator& operator++()
    {
      prevloadplan = curloadplan;
      if (curloadplan) curloadplan = curloadplan->nextLoadPlan;
      return *this;
    }
    LoadPlanIterator operator++(int)
      {LoadPlanIterator tmp = *this; ++*this; return tmp;}
    LoadPlan* operator ->() const {return curloadplan;}
    LoadPlan& operator *() const {return *curloadplan;}
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
};

inline OperationPlan::LoadPlanIterator OperationPlan::beginLoadPlans() const
  { return OperationPlan::LoadPlanIterator(firstloadplan); }

inline OperationPlan::LoadPlanIterator OperationPlan::endLoadPlans() const
  {return OperationPlan::LoadPlanIterator(NULL);}

inline int OperationPlan::sizeLoadPlans() const
{
  int c = 0;
  for (LoadPlanIterator i = beginLoadPlans(); i != endLoadPlans(); ++i) ++c;
  return c;
}


//
// SETTINGS
//


/** @brief This class exposes global plan information to Python. */
class PythonPlan : public PythonExtension<PythonPlan>
{
  public:
    static int initialize(PyObject* m);
  private:
    DECLARE_EXPORT PyObject* getattro(const Attribute&);
    DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// PROBLEMS
//


class PythonProblem : public PythonExtension<PythonProblem>
{
  public:
    static int initialize(PyObject* m);
    PythonProblem(Problem* p) : prob(p) {}
    static PyObject* proxy(Object* p)
      {return static_cast<PyObject*>(new PythonProblem(static_cast<Problem*>(p)));}
    PyObject* str()
    {
      return PythonObject(prob ? prob->getDescription() : "None");
    }
  private:
    PyObject* getattro(const Attribute&);
    Problem* prob;
};


class PythonProblemIterator
  : public FreppleIterator<PythonProblemIterator,Problem::const_iterator,Problem,PythonProblem>
{
};


//
// BUFFERS
//


class PythonBuffer : public FreppleCategory<PythonBuffer,Buffer>
{
  public:
    PythonBuffer(Buffer* p) : FreppleCategory<PythonBuffer,Buffer>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonBufferIterator
  : public FreppleIterator<PythonBufferIterator,Buffer::iterator,Buffer,PythonBuffer>
{
};


class PythonBufferDefault : public FreppleClass<PythonBufferDefault,PythonBuffer,BufferDefault>
{
  public:
    PythonBufferDefault(BufferDefault* p)
      : FreppleClass<PythonBufferDefault,PythonBuffer,BufferDefault>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonBufferInfinite : public FreppleClass<PythonBufferInfinite,PythonBuffer,BufferInfinite>
{
  public:
    PythonBufferInfinite(BufferInfinite* p)
      : FreppleClass<PythonBufferInfinite,PythonBuffer,BufferInfinite>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonBufferProcure : public FreppleClass<PythonBufferProcure,PythonBuffer,BufferProcure>
{
  public:
    PythonBufferProcure(BufferProcure* p)
      : FreppleClass<PythonBufferProcure,PythonBuffer,BufferProcure>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// LOCATIONS
//


class PythonLocation : public FreppleCategory<PythonLocation,Location>
{
  public:
    PythonLocation(Location* p) : FreppleCategory<PythonLocation,Location>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonLocationIterator
  : public FreppleIterator<PythonLocationIterator,Location::iterator,Location,PythonLocation>
{
};


class PythonLocationDefault : public FreppleClass<PythonLocationDefault,PythonLocation,LocationDefault>
{
  public:
    PythonLocationDefault(LocationDefault* p)
      : FreppleClass<PythonLocationDefault,PythonLocation,LocationDefault>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// CUSTOMERS
//


class PythonCustomer : public FreppleCategory<PythonCustomer,Customer>
{
  public:
    PythonCustomer(Customer* p) : FreppleCategory<PythonCustomer,Customer>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonCustomerIterator
  : public FreppleIterator<PythonCustomerIterator,Customer::iterator,Customer,PythonCustomer>
{
};


class PythonCustomerDefault : public FreppleClass<PythonCustomerDefault,PythonCustomer,CustomerDefault>
{
  public:
    PythonCustomerDefault(CustomerDefault* p)
      : FreppleClass<PythonCustomerDefault,PythonCustomer,CustomerDefault>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// ITEMS
//


class PythonItem : public FreppleCategory<PythonItem,Item>
{
  public:
    PythonItem(Item* p) : FreppleCategory<PythonItem,Item>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonItemIterator
  : public FreppleIterator<PythonItemIterator,Item::iterator,Item,PythonItem>
{
};


class PythonItemDefault : public FreppleClass<PythonItemDefault,PythonItem,ItemDefault>
{
  public:
    PythonItemDefault(ItemDefault* p)
      : FreppleClass<PythonItemDefault,PythonItem,ItemDefault>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// CALENDARS
//


class PythonCalendar : public FreppleCategory<PythonCalendar,Calendar>
{
  public:
    PythonCalendar(Calendar* p) : FreppleCategory<PythonCalendar,Calendar>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonCalendarIterator
  : public FreppleIterator<PythonCalendarIterator,Calendar::iterator,Calendar,PythonCalendar>
{
};


class PythonCalendarBucketIterator
  : public PythonExtension<PythonCalendarBucketIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonCalendarBucketIterator(Calendar* c) : cal(c)
    {
      if (!c)
        throw LogicException("Creating bucket iterator for NULL calendar");
      i = c->beginBuckets();
    }

  private:
    Calendar* cal;
    Calendar::BucketIterator i;
    PyObject *iternext();
};


class PythonCalendarBucket
  : public PythonExtension<PythonCalendarBucket>
{
  public:
    static int initialize(PyObject* m);
    PythonCalendarBucket(Calendar* c, Calendar::Bucket* b) : obj(b), cal(c) {}
  private:
    Calendar::Bucket* obj;
    Calendar* cal;
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
    // @todo static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
};


class PythonCalendarVoid : public FreppleClass<PythonCalendarVoid,PythonCalendar,CalendarVoid>
{
  public:
    PythonCalendarVoid(CalendarVoid* p)
      : FreppleClass<PythonCalendarVoid,PythonCalendar,CalendarVoid>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonCalendarBool : public FreppleClass<PythonCalendarBool,PythonCalendar,CalendarBool>
{
  public:
    PythonCalendarBool(CalendarBool* p)
      : FreppleClass<PythonCalendarBool,PythonCalendar,CalendarBool>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonCalendarDouble : public FreppleClass<PythonCalendarDouble,PythonCalendar,CalendarDouble>
{
  public:
    PythonCalendarDouble(CalendarDouble* p)
      : FreppleClass<PythonCalendarDouble,PythonCalendar,CalendarDouble>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// DEMANDS
//


class PythonDemand : public FreppleCategory<PythonDemand,Demand>
{
  public:
    PythonDemand(Demand* p) : FreppleCategory<PythonDemand,Demand>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonDemandIterator
  : public FreppleIterator<PythonDemandIterator,Demand::iterator,Demand,PythonDemand>
{
};


class PythonDemandDefault : public FreppleClass<PythonDemandDefault,PythonDemand,DemandDefault>
{
  public:
    PythonDemandDefault(DemandDefault* p)
      : FreppleClass<PythonDemandDefault,PythonDemand,DemandDefault>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// RESOURCES
//


class PythonResource : public FreppleCategory<PythonResource,Resource>
{
  public:
    PythonResource(Resource* p) : FreppleCategory<PythonResource,Resource>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonResourceIterator
  : public FreppleIterator<PythonResourceIterator,Resource::iterator,Resource,PythonResource>
{
};


class PythonResourceDefault : public FreppleClass<PythonResourceDefault,PythonResource,ResourceDefault>
{
  public:
    PythonResourceDefault(ResourceDefault* p)
      : FreppleClass<PythonResourceDefault,PythonResource,ResourceDefault>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonResourceInfinite : public FreppleClass<PythonResourceInfinite,PythonResource,ResourceInfinite>
{
  public:
    PythonResourceInfinite(ResourceInfinite* p)
      : FreppleClass<PythonResourceInfinite,PythonResource,ResourceInfinite>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


//
// OPERATIONS
//


class PythonOperation : public FreppleCategory<PythonOperation,Operation>
{
  public:
    PythonOperation(Operation* p) : FreppleCategory<PythonOperation,Operation>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationIterator
  : public FreppleIterator<PythonOperationIterator,Operation::iterator,Operation,PythonOperation>
{
};


class PythonOperationAlternate : public FreppleClass<PythonOperationAlternate,PythonOperation,OperationAlternate>
{
  public:
    PythonOperationAlternate(OperationAlternate* p)
      : FreppleClass<PythonOperationAlternate,PythonOperation,OperationAlternate>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
    static int initialize(PyObject* m)
    {
      getType().addMethod("addAlternate", addAlternate, METH_KEYWORDS, "add and alternate");
      return FreppleClass<PythonOperationAlternate,PythonOperation,OperationAlternate>::initialize(m);
    }
  private:
    /** Add an alternate to the operation.<br>
      * The keyword arguments are "operation", "priority", "effective_start" 
      * and "effective_end"
      */
    static DECLARE_EXPORT PyObject* addAlternate(PyObject*, PyObject*, PyObject*);
};


class PythonOperationFixedTime : public FreppleClass<PythonOperationFixedTime,PythonOperation,OperationFixedTime>
{
  public:
    PythonOperationFixedTime(OperationFixedTime* p)
      : FreppleClass<PythonOperationFixedTime,PythonOperation,OperationFixedTime>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationTimePer : public FreppleClass<PythonOperationTimePer,PythonOperation,OperationTimePer>
{
  public:
    PythonOperationTimePer(OperationTimePer* p)
      : FreppleClass<PythonOperationTimePer,PythonOperation,OperationTimePer>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationRouting : public FreppleClass<PythonOperationRouting,PythonOperation,OperationRouting>
{
  public:
    static int initialize(PyObject* m)
    {
      getType().addMethod("addStep", addStep, METH_VARARGS , "add steps to the routing");
      return FreppleClass<PythonOperationRouting,PythonOperation,OperationRouting>::initialize(m);
    }
    PythonOperationRouting(OperationRouting* p)
      : FreppleClass<PythonOperationRouting,PythonOperation,OperationRouting>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
  private:
    /** Add one or more steps to a routing. */
    static DECLARE_EXPORT PyObject* addStep(PyObject*, PyObject*);
};


//
// OPERATIONPLANS
//


class PythonOperationPlan : public PythonExtension<PythonOperationPlan>
{
  public:
    static int initialize(PyObject* m);
    PythonOperationPlan(OperationPlan* p) : obj(p) {}
    static PyObject* proxy(Object* p)
      {return static_cast<PyObject*>(new PythonOperationPlan(static_cast<OperationPlan*>(p)));}
  private:
    OperationPlan* obj;
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationPlanIterator
  : public FreppleIterator<PythonOperationPlanIterator,OperationPlan::iterator,OperationPlan,PythonOperationPlan>
{
  public:
    /** Constructor to iterate over all operationplans. */
    PythonOperationPlanIterator() {}

    /** Constructor to iterate over the operationplans of a single operation. */
    PythonOperationPlanIterator(Operation* o)
      : FreppleIterator<PythonOperationPlanIterator,OperationPlan::iterator,OperationPlan,PythonOperationPlan>(o)
    {}
};


//
// FLOWPLANS
//


class PythonFlowPlan : public PythonExtension<PythonFlowPlan>
{
  public:
    static int initialize(PyObject* m);
    PythonFlowPlan(FlowPlan* p) : fl(p) {}
  private:
    PyObject* getattro(const Attribute&);
    FlowPlan* fl;
};


class PythonFlowPlanIterator : public PythonExtension<PythonFlowPlanIterator> 
{
  public:
    static int initialize(PyObject* m);

    PythonFlowPlanIterator(Buffer* b) : buf(b)
    {
      if (!b)
        throw LogicException("Creating flowplan iterator for NULL buffer");
      i = b->getFlowPlans().begin();
    }

  private:
    Buffer* buf;
    Buffer::flowplanlist::const_iterator i;
    PyObject *iternext();
};


//
// LOADPLANS
//


class PythonLoadPlan : public PythonExtension<PythonLoadPlan>
{
  public:
    static int initialize(PyObject* m);
    PythonLoadPlan(LoadPlan* p) : fl(p) {}
  private:
    PyObject* getattro(const Attribute&);
    LoadPlan* fl;
};


class PythonLoadPlanIterator : public PythonExtension<PythonLoadPlanIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonLoadPlanIterator(Resource* r) : res(r)
    {
      if (!r)
        throw LogicException("Creating loadplan iterator for NULL resource");
      i = r->getLoadPlans().begin();
    }

  private:
    Resource* res;
    Resource::loadplanlist::const_iterator i;
    PyObject *iternext();
};


//
// DEMAND DELIVERY OPERATIONPLANS
//


class PythonDemandPlanIterator : public PythonExtension<PythonDemandPlanIterator> 
{
  public:
    static int initialize(PyObject* m);

    PythonDemandPlanIterator(Demand* r) : dem(r)
    {
      if (!r)
        throw LogicException("Creating demandplan iterator for NULL demand");
      i = r->getDelivery().begin();
    }

  private:
    Demand* dem;
    Demand::OperationPlan_list::const_iterator i;
    PyObject *iternext();
};


//
// DEMAND PEGGING
//


class PythonPeggingIterator : public PythonExtension<PythonPeggingIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonPeggingIterator(Demand* r) : dem(r), i(r)
    {
      if (!r)
        throw LogicException("Creating pegging iterator for NULL demand");
    }

  private:
    Demand* dem;
    PeggingIterator i;
    PyObject *iternext();
};


//
// LOADS
//


class PythonLoad : public PythonExtension<PythonLoad>
{
  public:
    static int initialize(PyObject* m);
    PythonLoad(Load* p) : ld(p) {}
  private:
    DECLARE_EXPORT PyObject* getattro(const Attribute&);
    DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
    static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds);
    static PyObject* proxy(Object* p) {return static_cast<PyObject*>(new PythonLoad(static_cast<Load*>(p)));}
    Load* ld;
};


class PythonLoadIterator : public PythonExtension<PythonLoadIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonLoadIterator(Resource* r)
      : res(r), ir(r ? r->getLoads().begin() : NULL), oper(NULL), io(NULL)
    {
      if (!r)
        throw LogicException("Creating loadplan iterator for NULL resource");
    }

    PythonLoadIterator(Operation* o)
      : res(NULL), ir(NULL), oper(o), io(o ? o->getLoads().begin() : NULL)
    {
      if (!o)
        throw LogicException("Creating loadplan iterator for NULL operation");
    }

  private:
    Resource* res;
    Resource::loadlist::const_iterator ir;
    Operation* oper;
    Operation::loadlist::const_iterator io;
    PyObject *iternext();
};


//
// FLOW
//


class PythonFlow : public PythonExtension<PythonFlow>
{
  public:
    static int initialize(PyObject* m);
    PythonFlow(Flow* p) : fl(p) {}
  private:
    DECLARE_EXPORT PyObject* getattro(const Attribute&);
    static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds);
    DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
    static PyObject* proxy(Object* p) {return static_cast<PyObject*>(new PythonFlow(static_cast<Flow*>(p)));}
    Flow* fl;
};


class PythonFlowIterator : public PythonExtension<PythonFlowIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonFlowIterator(Buffer* b)
      : buf(b), ib(b ? b->getFlows().begin() : NULL), oper(NULL), io(NULL)
    {
      if (!b)
        throw LogicException("Creating flowplan iterator for NULL buffer");
    }

    PythonFlowIterator(Operation* o)
      : buf(NULL), ib(NULL), oper(o), io(o ? o->getFlows().begin() : NULL)
    {
      if (!o)
        throw LogicException("Creating flowplan iterator for NULL operation");
    }

  private:
    Buffer* buf;
    Buffer::flowlist::const_iterator ib;
    Operation* oper;
    Operation::flowlist::const_iterator io;
    PyObject *iternext();
};


//
// SOLVERS
//


class PythonSolver : public FreppleCategory<PythonSolver,Solver>
{
  public:
    static int initialize(PyObject* m)
    {
      getType().addMethod("solve", solve, METH_NOARGS, "run the solver");
      return FreppleCategory<PythonSolver,Solver>::initialize(m);
    }
    PythonSolver(Solver* p) : FreppleCategory<PythonSolver,Solver>(p) {}
    virtual DECLARE_EXPORT PyObject* getattro(const Attribute&);
    virtual DECLARE_EXPORT int setattro(const Attribute&, const PythonObject&);
    static DECLARE_EXPORT PyObject* solve(PyObject*, PyObject*);
};


class PythonSolverIterator
  : public FreppleIterator<PythonSolverIterator,Solver::iterator,Solver,PythonSolver>
{
};


}   // End namespace

#endif
