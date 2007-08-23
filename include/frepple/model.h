/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
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

/** @mainpage Frepple Library API
  * The Frepple class library provides a framework for modeling a
  * manufacturing environment.<br>
  * This document describes its C++ API.<P>
  *
  * @namespace frepple
  * @brief Core namespace
  */

#include "frepple/utils.h"
#include "frepple/timeline.h"
#include <float.h>

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
class OperationEffective;
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


/** @brief This class is used for initialization and finalization. */
class LibraryModel
{
  public:
    static void initialize();
    static void finalize() {}
};


/** @brief This is the class used to 1) represent varisables that are
  * varying over time, and 2) to divide a time horizon into
  * multiple buckets.
  *
  * Some example usages for calendars:
  *  - A calendar defining the available capacity of a resource
  *    week by week.
  *  - The minimum inventory desired in a buffer week by week.
  *  - Defining weekly, monthly and quarterly buckets for
  *    reporting purposes.
  */
class Calendar : public HasName<Calendar>, public Object
{
    TYPEDEF(Calendar);
  public:
    class BucketIterator; // Forward declaration

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
      private:
        /** Name of the bucket. */
        string nm;

        /** Start date of the bucket. */
        Date startdate;

        /** End Date of the bucket.
          * This field is never read in from the input files, but always
          * computed based on the start dates of the adjacent buckets.
          */
        Date enddate;

        /** A pointer to the next bucket. */
        Bucket* nextBucket;

        /** A pointer to the previous bucket. */
        Bucket* prevBucket;

      protected:
        /** Constructor. */
        Bucket(Date n) : startdate(n), nextBucket(NULL), prevBucket(NULL) {}

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

        /** Returns the start date of the bucket. */
        Date getStart() const {return startdate;}

        virtual DECLARE_EXPORT void writeElement
          (XMLOutput*, const XMLtag&, mode=DEFAULT) const;

        /** Reads the bucket information from the input. Only the fields NAME
          * and START are read in. Other fields as also written out but these
          * are information-only fields.
          */
        DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement&  pElement);

        virtual const MetaClass& getType() const
          {return metadata;}
        virtual size_t getSize() const
          {return sizeof(Bucket) + nm.size();}
        static DECLARE_EXPORT const MetaCategory metadata;
    };

    /** Default constructor. */
    Calendar(const string& n) : HasName<Calendar>(n), firstBucket(NULL)
      { createNewBucket(Date()); }

    /** Destructor, which needs to clean up the buckets too. */
    DECLARE_EXPORT ~Calendar();

    /** This is a factory method that creates a new bucket using the start
      * date as the key field. The fields are passed as an array of character
      * pointers.<br>
      * This method is intended to be used to create objects when reading
      * XML input data.
      */
    DECLARE_EXPORT Bucket* createBucket(const Attributes* atts);

    /** Adds a new bucket to the list. */
    DECLARE_EXPORT Bucket* addBucket(Date);

    /** Removes a bucket from the list. */
    DECLARE_EXPORT void removeBucket(Bucket* bkt);

    /** Returns the bucket where a certain date belongs to.
      * A bucket will always be returned, i.e. the data structure is such
      * that we all dates between infinitePast and infiniteFuture match
      * with one (and only one) bucket.
      * @see findBucketIndex()
      */
    DECLARE_EXPORT Bucket* findBucket(Date d) const;

    /** Returns the index of the bucket where a certain date belongs to.
      * A bucket (and bucket index) will always be found.
      * @see findBucket()
      */
    DECLARE_EXPORT int findBucketIndex(Date d) const;

    /** Returns the bucket with a certain name.
      * A NULL pointer is returned in case no bucket can be found with the
      * given name.
      */
    DECLARE_EXPORT Bucket* findBucket(const string&) const;

    /** @brief An iterator class to go through all buckets of the calendar. */
    class BucketIterator
    {
      private:
        Bucket* curBucket;
      public:
        BucketIterator(Bucket* b) : curBucket(b) {}
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

    DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, XMLElement&  pElement) {}
    DECLARE_EXPORT void beginElement(XMLInput& pIn, XMLElement&  pElement);

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
    virtual Bucket* createNewBucket(Date n) {return new Bucket(n);}
};


/** @brief This calendar type is used to store values in its buckets.
  *
  * The template type must statisfy the following requirements:
  *   - XML import supported by the operator >> of the class XMLElement.
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
        BucketValue(Date& n) : Bucket(n) {};
      public:
        /** Returns the value of this bucket. */
        const T& getValue() const {return val;}

        /** Updates the value of this bucket. */
        void setValue(const T& v) {val = v;}

        void writeElement
        (XMLOutput *o, const XMLtag& tag, mode m = DEFAULT) const
        {
          assert(m == DEFAULT || m == FULL);
          o->BeginObject(Tags::tag_bucket, Tags::tag_start, getStart());
          if (!useDefaultName()) o->writeElement(Tags::tag_name, getName());
          o->writeElement(Tags::tag_end, getEnd());
          o->writeElement(Tags::tag_value, val);
          o->EndObject(tag);
        }

        void endElement (XMLInput& pIn, XMLElement& pElement)
        {
          if (pElement.isA(Tags::tag_value))
            pElement >> val;
          else
            Bucket::endElement(pIn,pElement);
        }

        virtual const MetaClass& getType() const
          {return Calendar::Bucket::metadata;}
        virtual size_t getSize() const
          {return sizeof(typename CalendarValue<T>::BucketValue) + getName().size();}
    };

    /** Default constructor. */
    CalendarValue(const string& n) : Calendar(n) {}

    /** Returns the value on the specified date. */
    const T& getValue(const Date d) const
      {return static_cast<BucketValue*>(findBucket(d))->getValue();}

    /** Updates the value in a certain time bucket. */
    void setValue(const Date d, const T& v)
      {static_cast<BucketValue*>(findBucket(d))->setValue(v);}

    virtual const MetaClass& getType() const = 0;

    const T& getValue(Calendar::BucketIterator& i) const
      {return reinterpret_cast<BucketValue&>(*i).getValue();}

  private:
    /** Factory method to add new buckets to the calendar.
      * @see Calendar::addBucket()
      */
    Bucket* createNewBucket(Date n) {return new BucketValue(n);}
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
        BucketPointer(Date& n) : Bucket(n), val(NULL) {};
      public:
        /** Returns the value stored in this bucket. */
        T* getValue() const {return val;}

        /** Updates the value of this bucket. */
        void setValue(T* v) {val = v;}

        void writeElement
        (XMLOutput *o, const XMLtag& tag, mode m = DEFAULT) const
        {
          assert(m == DEFAULT || m == FULL);
          o->BeginObject(Tags::tag_bucket, Tags::tag_start, getStart());
          if (!useDefaultName()) o->writeElement(Tags::tag_name, getName());
          o->writeElement(Tags::tag_end, getEnd());
          if (val) o->writeElement(Tags::tag_value, val);
          o->EndObject(tag);
        }

        void beginElement (XMLInput& pIn, XMLElement& pElement)
        {
          if (pElement.isA(Tags::tag_value))
            pIn.readto(
              MetaCategory::ControllerDefault(T::metadata,pIn)
            );
        }

        void endElement (XMLInput& pIn, XMLElement& pElement)
        {
          if (pElement.isA(Tags::tag_value))
          {
            T *o = dynamic_cast<T*>(pIn.getPreviousObject());
            if (!o)
              throw LogicException
              ("Incorrect object type during read operation");
            val = o;
          }
          else
            Bucket::endElement(pIn,pElement);
        }

        virtual const MetaClass& getType() const
          {return Calendar::Bucket::metadata;}
        virtual size_t getSize() const
          {return sizeof(typename CalendarPointer<T>::BucketPointer) + getName().size();}
    };

    /** Default constructor. */
    CalendarPointer(const string& n) : Calendar(n) {}

    /** Returns the value on the specified date. */
    T* getValue(const Date d) const
      {return static_cast<BucketPointer*>(findBucket(d))->getValue();}

    /** Updates the value in a certain time bucket. */
    void setValue(const Date d, T* v)
      {static_cast<BucketPointer*>(findBucket(d))->setValue(v);}

    virtual const MetaClass& getType() const = 0;

  private:
    /** Factory method to add new buckets to the calendar.
      * @see Calendar::addBucket()
      */
    Bucket* createNewBucket(Date n) {return new BucketPointer(n);}
};


/** @brief A calendar only defining time buckets and not storing any data 
  * fields. */
class CalendarVoid : public Calendar
{
    TYPEDEF(CalendarVoid);
  public:
    CalendarVoid(const string& n) : Calendar(n) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing float values in its buckets. */
class CalendarFloat : public CalendarValue<float>
{
    TYPEDEF(CalendarFloat);
  public:
    CalendarFloat(const string& n) : CalendarValue<float>(n) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing integer values in its buckets. */
class CalendarInt : public CalendarValue<int>
{
    TYPEDEF(CalendarInt);
  public:
    CalendarInt(const string& n) : CalendarValue<int>(n) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing boolean values in its buckets. */
class CalendarBool : public CalendarValue<bool>
{
    TYPEDEF(CalendarBool);
  public:
    CalendarBool(const string& n) : CalendarValue<bool>(n) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
};


/** @brief A calendar storing strings in its buckets. */
class CalendarString : public CalendarValue<string>
{
    TYPEDEF(CalendarString);
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
    TYPEDEF(CalendarOperation);
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
class Problem : public NonCopyable
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
    virtual bool isFeasible() = 0;

    /** Returns a float number reflecting the magnitude of the problem. This
      * allows us to focus on the significant problems and filter out the
      * small ones.
      */
    virtual float getWeight() = 0;

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, XMLElement&  pElement) {}
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

    /** Erases the list of problems linked with a certain plannable object.
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
  * It is intended as a basis for different algoritms processing the frepple
  * data.
  *
  * The goal is to decouple the solver/algorithms from the model/data
  * representation. Different solvers can be easily be plugged in to work on
  * the same data.
  */
class Solver : public Object, public HasName<Solver>
{
    TYPEDEF(Solver);
  public:
    explicit Solver(const string& n) : HasName<Solver>(n), verbose(false) {}
    virtual ~Solver() {}

    virtual DECLARE_EXPORT void writeElement (XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);

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
    virtual void solve(const OperationEffective* o, void* v = NULL)
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

    /** Returns true if elaborate and verbose output is requested. */
    bool getVerbose() const {return verbose;}

    /** Controls whether verbose output will be generated. */
    void setVerbose(bool b) {verbose = b;}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  protected:
    /** Controls how much messages we want to generate.<br>
      * The default value is false. */
    bool verbose;
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
    const Solver *sol;

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

    DECLARE_EXPORT void beginElement(XMLInput& pIn, XMLElement& pElement);
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);

    string getDescription() const {return "running a solver";}

    /** Returns the solver being run. */
    Solver::pointer getSolver() const {return sol;}

    /** Updates the solver being used. */
    void setSolver(Solver* s) {sol = s;}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandSolve);}
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

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);

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
    /** Returns the total number of clusters in the system. If not up to date
      * the recomputation will be triggered. */
    static unsigned short getNumberOfClusters()
    {
      if (recomputeLevels || computationBusy) computeLevels();
      return numberOfClusters;
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
  * This is useful for reporting but has no direct impact on the planning 
  * behavior.
  */
class Location
      : public HasHierarchy<Location>, public HasDescription, public Object
{
    TYPEDEF(Location);
  public:
    DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput& pIn, XMLElement& pElement);
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);
    explicit Location(const string& n) : HasHierarchy<Location>(n) {}
    virtual DECLARE_EXPORT ~Location();
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
};


/** @brief This class implements the abstract Location class. */
class LocationDefault : public Location
{
    TYPEDEF(LocationDefault);
  public:
    explicit LocationDefault(const string& str) : Location(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(LocationDefault) 
        + getName().size() 
        + HasDescription::memsize();}
};


/** @brief This abstracts class represents customers.
  * 
  * Demands can be associated with a customer, but there is no planning 
  * behavior directly linked to customers.
  */
class Customer
      : public HasHierarchy<Customer>, public HasDescription, public Object
{
    TYPEDEF(Customer);
  public:
    DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput& pIn, XMLElement& pElement);
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);
    Customer(const string& n) : HasHierarchy<Customer>(n) {}
    virtual DECLARE_EXPORT ~Customer();
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
};


/** @brief This class implements the abstract Customer class. */
class CustomerDefault : public Customer
{
    TYPEDEF(CustomerDefault);
  public:
    explicit CustomerDefault(const string& str) : Customer(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(CustomerDefault) + getName().size() + HasDescription::memsize();}
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
    TYPEDEF(Operation);
    friend class Flow;
    friend class Load;
    friend class OperationPlan;
    friend class OperationRouting;   // to have access to superoplist
    friend class OperationAlternate; // to have access to superoplist

  protected:
    /** Constructor. Don't use it directly. */
    explicit Operation(const string& str) : HasName<Operation>(str),
        size_minimum(0.0f), size_multiple(0.0f), hidden(false), opplan(NULL) {}

  public:
    /** Destructor. */
    virtual DECLARE_EXPORT ~Operation();

    /** Returns a pointer to the operationplan being instantiated. */
    OperationPlan* getFirstOpPlan() const {return opplan;}

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

    typedef Association<Operation,Buffer,Flow>::ListA flowlist;
    typedef Association<Operation,Resource,Load>::ListA  loadlist;

    /** This is the factory method which creates all operationplans of the
      * operation. */
    virtual DECLARE_EXPORT OperationPlan* createOperationPlan (float q, Date s,
        Date e, const Demand* l, bool updates_okay=true, OperationPlan* ow=NULL,
        unsigned long i=0, bool makeflowsloads=true) const;

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
      (OperationPlan*, float, Date, Date, bool = true) const = 0;

    /** Returns an reference to the list of flows. */
    const flowlist& getFlows() const {return flowdata;}

    /** Returns an reference to the list of flows. */
    const loadlist& getLoads() const {return loaddata;}

    /** Return the flow that is associates a given buffer with this
      * operation. Returns NULL is no such flow exists. */
    Flow* findFlow(const Buffer* b) const {return flowdata.find(b);}

    /** Return the load that is associates a given resource with this
      * operation. Returns NULL is no such load exists. */
    Load* findLoad(const Resource* r) const {return loaddata.find(r);}

    /** Deletes all operationplans of this operation. The boolean parameter
      * controls whether we delete also locked operationplans or not.
      */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    /** Sets the minimum size of operationplans. */
    void setSizeMinimum(float f)
    {
      if (f<0) return;
      size_minimum = f;
      setChanged();
    }

    /** Returns the minimum size for operationplans. */
    float getSizeMinimum() const {return size_minimum;}

    /** Sets the multiple size of operationplans. */
    void setSizeMultiple(float f)
    {
      if (f<0) return;
      size_multiple = f;
      setChanged();
    }

    /** Returns the minimum size for operationplans. */
    float getSizeMultiple() const {return size_multiple;}

    DECLARE_EXPORT void beginElement(XMLInput& , XMLElement& );
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);

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
    void initOperationPlan (OperationPlan*, float, const Date&, const Date&,
        const Demand*, bool, OperationPlan*, unsigned long, bool = true) const;

  private:
    /** List of operations using this operation as a sub-operation */
    Operationlist superoplist;

    /** Empty list of operations. For operation types which have no
      * suboperations this list is used as the list of suboperations.
      */
    static DECLARE_EXPORT Operationlist nosubOperations;

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

    /** Minimum size for operationplans. */
    float size_minimum;

    /** Multiple size for operationplans. */
    float size_multiple;

    /** Does the operation require serialization or not. */
    bool hidden;

    /** A pointer to the first operationplan of this operation.
      * All operationplans of this operation are stored in a doubly linked
      * list. The list is sorted in descending id's.
      */
    OperationPlan* opplan;
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
    TYPEDEF(OperationPlan);
    friend class FlowPlan;
    friend class LoadPlan;
    friend class Demand;
    friend class Operation;
    friend class OperationPlanAlternate;
    friend class OperationPlanRouting;
    friend class OperationPlanEffective;
    friend class OperationEffective;

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
          {
            OperationPlan::sortOperationPlans(*x);
            opplan = x->getFirstOpPlan();
          }
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
          {
            OperationPlan::sortOperationPlans(*op);
            opplan = op->getFirstOpPlan();
          }
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
            {
              OperationPlan::sortOperationPlans(*op);
              opplan = op->getFirstOpPlan();
            }
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
            {
              OperationPlan::sortOperationPlans(*op);
              opplan = op->getFirstOpPlan();
            }
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
    static DECLARE_EXPORT Object* createOperationPlan (const MetaCategory&, const XMLInput&);

    /** Destructor. */
    virtual DECLARE_EXPORT ~OperationPlan();

    virtual DECLARE_EXPORT void setChanged(bool b = true);

    /** Returns the quantity. */
    float getQuantity() const {return quantity;}

    /** Updates the quantity.<br>
      * The quantity of an operationplan must be greater than to 0.<br>
      * This method can only be called on top operationplans. Sub operation
      * plans should pass on a call to the parent operationplan.
      */
    virtual DECLARE_EXPORT void setQuantity(float f, bool roundDown=false);

    /** Returns a pointer to the demand for which this operation is a delivery.
      * If the operationplan isn't a delivery operation, this is a NULL pointer.
      */
    const Demand* getDemand() const {return lt;}

    /** Updates the demand to which this operationplan is a solution. */
    DECLARE_EXPORT void setDemand(const Demand* l);

    /** This function allows the operationplan to propagate all changes
      * to its flowplans, loadplans and problems.
      * Temporarily disabling updates can be handy if multiple changes to the
      * operationplan are required. Using this feature we can then propagate
      * all changes in one go.
      */
    void setAllowUpdates(bool u = true) {runupdate = u; if (u) update();}

    /** Returns whether the operationplan is locked. A locked operationplan
      * is never changed. Only top-operationplans can be locked.
      * Sub-operationplans pass on a call to this function to their owner.
      */
    bool getLocked() const
    {
      if (owner) return owner->getLocked();
      else return locked;
    }

    /** Deletes all operationplans of a certain operation. A boolean flag
      * allows to specify whether locked operationplans are to be deleted too.
      */
    static DECLARE_EXPORT void deleteOperationPlans(Operation* o, bool deleteLocked=false);

    /** Locks/unlocks an operationplan. A locked operationplan is never
      * changed. Only top-operationplans can be locked. Sub-operationplans
      * pass on a call to this function to their owner.
      */
    void setLocked(bool b = true)
    {
      if (owner) WLock<OperationPlan>(owner)->setLocked(b);
      else if (locked!=b)
      {
        setChanged();
        locked = b;
      }
    }

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
      * take care of.
      * The methods setStart(Date) and setEnd(Date) are therefore preferred
      * since they properly apply all appropriate logic.
      */
    void setStartAndEnd(Date st, Date nd)
    {
      dates.setStartAndEnd(st,nd);
      if (runupdate) OperationPlan::update();
      else setChanged();
    }

    /** Updates the operationplan owning this operationplan. In case of
      * a OperationRouting steps this will be the operationplan representing the
      * complete routing. */
    void DECLARE_EXPORT setOwner(const OperationPlan* o);

    /** Returns a pointer to the operationplan for which this operationplan
      * a sub-operationplan.<br>
      * The method returns NULL if there is no owner defined.<br>
      * E.g. Sub-operationplans of a routing refer to the overall routing
      * operationplan.<br>
      * E.g. An alternate sub-operationplan refers to its parent.
      * @see getTopOwner
      */
    OperationPlan::pointer getOwner() const {return owner;}

    /** Returns a pointer to the operationplan owning a set of
      * sub-operationplans. There can be multiple levels of suboperations.<br>
      * If no owner exists the method returns the current operationplan.
      * @see getOwner
      */
    OperationPlan::pointer getTopOwner() const
    {
      if (owner)
      {
        // There is an owner indeed
        OperationPlan::pointer o(owner);
        while (o->owner) o = o->owner;
        return o;
      }
      else
        // This operationplan is itself the top of a hierarchy
        return this;
    }

    /** Returns the start and end date of this operation_plan. */
    const DateRange & getDates() const {return dates;}

    /** Returns a unique identifier of the operationplan.
      * The identifier can be specified in the data input (in which case
      * we check for the uniqueness during the read operation).
      * For operationplans created during a solver run, we start with the
      * highest identifier read in from the input and start incrementing for
      * every operationplan.
      * The identifier is assigned when the  function is called.
      */
    unsigned long getIdentifier() const {return id;}

    /** Updates the end date of the operation_plan. The start date is computed.
      * Locked operation_plans are not updated by this function.
      */
    virtual DECLARE_EXPORT void setEnd(Date);

    /** Updates the start date of the operation_plan. The end date is computed.
      * Locked operation_plans are not updated by this function.
      */
    virtual DECLARE_EXPORT void setStart(Date);

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, XMLElement&);
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);

    /** Initialize the operation_plan. The initialization function should be
      * called when the operation_plan is ready to be 'officially' added. The
      * initialization performs the following actions:
      * <ol>
      * <li> assign an identifier</li>
      * <li> create the flow and loadplans if these hadn't been created
      * before</li>
      * <li> add the operation_plan to the global list of operation_plans</li>
      * <li> create a link with a demand object if this is a delivery
      * operation_plan</li>
      * </ol>
      * Every operation_plan subclass that has sub-operations will normally
      * need to create an override of this function.
      * Calling this function will DELETE the current operationplan. The object
      * on which this function is called could not exist any more after the
      * call to this function!
      */
    virtual DECLARE_EXPORT void initialize();

    /** Add a sub_operation_plan to the list. For normal operation_plans this
      * is only a dummy function. For alternates and routing operation_plans
      * it does have a meaning.
      */
    virtual void addSubOperationPlan(OperationPlan* o)
    {
      throw LogicException("Adding a sub operationplan to "
          + oper->getName() + " not supported");
    };

    /** Remove a sub_operation_plan from the list. For normal operation_plans
      * this is only a dummy function. For alternates and routing
      * operation_plans it does have a meaning.
      */
    virtual void eraseSubOperationPlan(OperationPlan* o)
    {
      throw LogicException("Removing a sub operationplan from "
          + oper->getName() + " not supported");
    };

    /** This method is used to check the validity of the operationplan. */
    DECLARE_EXPORT bool check() const;

    /** This function is used to create the proper loadplan and flowplan
      * objects associated with the operation. */
    DECLARE_EXPORT void createFlowLoads();

    bool getHidden() const {return getOperation()->getHidden();}

    /** Searches for an OperationPlan with a given identifier. Returns a NULL
      * pointer if no such OperationPlan can be found.
      * The method is of complexity O(n), i.e. involves a LINEAR search through
      * the existing operationplans, and can thus be quite slow in big models.
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
    const MetaClass& getType() const {return getOperation()->getType();}
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

  protected:
    virtual DECLARE_EXPORT void update();
    DECLARE_EXPORT void resizeFlowLoadPlans();

    /** Pointer to a higher level OperationPlan. */
    const OperationPlan *owner;

    /** Quantity. */
    float quantity;

    /** Run the update method after each change? Settingthis field to false
      * allows you to do a number of changes after another and then run the
      * update method only once.<br>
      * This field is only relevant for top-operationplans.
      * @todo try to get rid of this field to reduce memory consumption
      */
    bool runupdate;

    /** Default constructor.
      * This way of creating operationplan objects is not intended for use by
      * any client applications. Client applications should use the factory
      * method on the operation class instead.<br>
      * Subclasses of the Operation class may use this constructor in their
      * own override of the createOperationPlan method.
      * @see Operation::createOperationPlan
      */
    OperationPlan() : owner(NULL), quantity(0.0), runupdate(false),
        locked(false), lt(NULL), id(0), oper(NULL), firstflowplan(NULL),
        firstloadplan(NULL), prev(NULL), next(NULL) {}

  private:
    /** Sort the list of operationplans. */
    static DECLARE_EXPORT void sortOperationPlans(const Operation&);

    /** Empty list of operationplans.<br>
      * For operationplan types without suboperationplans this list is used
      * as the list of suboperationplans.
      */
    static OperationPlanList nosubOperationPlans;

    /** Is this operationplan locked? A locked operationplan doesn't accept
      * any changes. This field is only relevant for top-operationplans. */
    bool locked;

    /** Counter of OperationPlans, which is used to automatically assign a
      * unique identifier for each operationplan.
      * @see getIdentifier()
      */
    static DECLARE_EXPORT unsigned long counter;

    /** Pointer to the demand. Only delivery operationplans have this field
      * set. The field is NULL for all other operationplans. */
    const Demand *lt;

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
    TYPEDEF(OperationFixedTime);
  public:
    /** Constructor. */
    explicit OperationFixedTime(const string& s) : Operation(s) {}

    /** Returns the length of the operation. */
    const TimePeriod getDuration() const {return duration;}

    /** Updates the duration of the operation. Existing operation plans of this
      * operation are not automatically refreshed to reflect the change. */
    void setDuration(TimePeriod t) {if (t>=TimePeriod(0L)) duration = t;}

    DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(OperationFixedTime) + getName().size() + HasDescription::memsize();}

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
    DECLARE_EXPORT void setOperationPlanParameters(OperationPlan*, float, Date, Date, bool=true) const;

  private:
    /** Stores the lengh of the Operation. */
    TimePeriod duration;
};


/** @brief Models an operation whose duration is the sum of a constant time, 
  * plus a cetain time per unit. 
  */
class OperationTimePer : public Operation
{
    TYPEDEF(OperationTimePer);
  public:
    /** Constructor. */
    explicit OperationTimePer(const string& s) : Operation(s) {}

    /** Returns the constant part of the operation time. */
    TimePeriod getDuration() const {return duration;}

    /** Sets the constant part of the operation time. */
    void setDuration(TimePeriod t)
    { if(t>=TimePeriod(0L)) duration = t; }

    /** Returns the time per unit of the operation time. */
    TimePeriod getDurationPer() const {return duration_per;}

    /** Sets the time per unit of the operation time. */
    void setDurationPer(TimePeriod t)
    { if(t>=TimePeriod(0L)) duration_per = t; }

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
    (OperationPlan*, float, Date, Date, bool=true) const;

    DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(OperationTimePer) + getName().size() + HasDescription::memsize();}

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
    TYPEDEF(OperationRouting);
  public:
    /** Constructor. */
    explicit OperationRouting(const string& c) : Operation(c) {};

    /** Destructor. */
    DECLARE_EXPORT ~OperationRouting();

    /** Adds a new steps to routing at the start of the routing. */
    void addStepFront(Operation *o)
    {
      if (!o) return;
      steps.push_front(o);
      o->addSuperOperation(this);
    }

    /** Adds a new steps to routing at the end of the routing. */
    void addStepBack(Operation *o)
    {
      if (!o) return;
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
    DECLARE_EXPORT void setOperationPlanParameters(OperationPlan*, float, Date, Date, bool=true) const;

    DECLARE_EXPORT void beginElement(XMLInput& , XMLElement&  );
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Return a list of all sub-operation_plans. */
    virtual const Operationlist& getSubOperations() const {return steps;}

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual DECLARE_EXPORT OperationPlan* createOperationPlan (float q, Date s,
        Date e, const Demand* l, bool updates_okay = true, OperationPlan* ow = NULL,
        unsigned long i = 0, bool makeflowsloads=true) const;

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {
      return sizeof(OperationRouting) + getName().size() 
        + HasDescription::memsize()
        + steps.size() * 2 * sizeof(Operation*);
    }

  private:
    Operationlist steps;
};


/** @brief OperationPlans for routing operation uses this subclass for
  * the instances. */
class OperationPlanRouting : public OperationPlan
{
    TYPEDEF(OperationPlanRouting);
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
    DECLARE_EXPORT void setQuantity(float f, bool roundDown=false);
    DECLARE_EXPORT void eraseSubOperationPlan(OperationPlan* o);
    virtual const OperationPlan::OperationPlanList& getSubOperationPlans() const {return step_opplans;}

    /** Initializes the operationplan and all steps in it.
      * If no step operationplans had been created yet this method will create
      * them. During this type of creation the end date of the routing
      * operationplan is used and step operationplans are created. After the
      * step operationplans are created the start date of the routing will be
      * equal to the start of the first step.
      */
    DECLARE_EXPORT void initialize();
    void updateProblems();

    virtual size_t getSize() const
      {return sizeof(OperationPlanRouting) + step_opplans.size() * 2 * sizeof(OperationPlan*);}
};



/** @brief This class represents a choice between multiple operations. The
  * alternates are sorted in order of priority.
  */
class OperationAlternate : public Operation
{
    TYPEDEF(OperationAlternate);
  public:
    /** Constructor. */
    explicit OperationAlternate(const string& c) : Operation(c) {};

    /** Destructor. */
    DECLARE_EXPORT ~OperationAlternate();

    /** Add a new alternate operation. The higher the priority value, the more
      * important this alternate operation is. */
    DECLARE_EXPORT void addAlternate(Operation* o, float prio = 1.0f);

    /** Removes an alternate from the list. */
    DECLARE_EXPORT void removeSubOperation(Operation *);

    /** Returns the priority of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     null or when it is not a sub-operation of this alternate.
      */
    DECLARE_EXPORT float getPriority(Operation* o) const;

    /** Updates the priority of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     not null and not a sub-operation of this alternate.
      */
    DECLARE_EXPORT void setPriority(Operation* o, float f);

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - Very simple, call the method with the same name on the alternate
      *    suboperationplan.
      * @see Operation::setOperationPlanParameters
      */
    DECLARE_EXPORT void setOperationPlanParameters
      (OperationPlan*, float, Date, Date, bool=true) const;

    DECLARE_EXPORT void beginElement (XMLInput&, XMLElement&);
    DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual const Operationlist& getSubOperations() const {return alternates;}

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual DECLARE_EXPORT OperationPlan* createOperationPlan (float q, Date s,
        Date e, const Demand* l, bool updates_okay = true, OperationPlan* ow = NULL,
        unsigned long i = 0, bool makeflowsloads=true) const;

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {
      return sizeof(OperationAlternate) + getName().size() + HasDescription::memsize()
          + alternates.size() * 2 * (sizeof(Operation*)+sizeof(float));
    }

  private:
    typedef list<float> priolist;

    /** List of the priorities of the different alternate operations. The list
      * is maintained such that it is sorted in descending order of priority. */
    priolist priorities;

    /** List of all alternate operations. The list is sorted with the operation
      * with the highest priority at the start of the list.
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
    TYPEDEF(OperationPlanAlternate);
    friend class OperationAlternate;

  private:
    OperationPlan* altopplan;

  public:
    /* Constructor. */
    OperationPlanAlternate() : altopplan(NULL) {};

    /** Destructor. */
    DECLARE_EXPORT ~OperationPlanAlternate();
    DECLARE_EXPORT void addSubOperationPlan(OperationPlan* o);
    DECLARE_EXPORT void setQuantity(float f, bool roundDown=false);
    DECLARE_EXPORT void eraseSubOperationPlan(OperationPlan* o);
    DECLARE_EXPORT void setEnd(Date d);
    DECLARE_EXPORT void setStart(Date d);
    DECLARE_EXPORT void update();

    /** Returns the sub-operationplan. */
    virtual OperationPlan* getSubOperationPlan() const {return altopplan;}

    /** Initializes the operationplan. If no suboperationplan was created
      * yet this method will create one, using the highest priority alternate.
      */
    DECLARE_EXPORT void initialize();
};


/** @brief Models an operation which has to use different operations depending
  * on the dates. */
class OperationEffective : public Operation
{
    TYPEDEF(OperationEffective);
  public:
    /** Constructor. */
    explicit OperationEffective(const string& s)
        : Operation(s), cal(NULL), useEndDate(true) {}

    /** Returns the calendar that specifies which operation to use during
      * which time period. */
    CalendarOperation::pointer getCalendar() const {return cal;}

    /** Updates the calendar. Existing operation plans are not automatically
      * getting updated to fit the new calendar. */
    void setCalendar(const CalendarOperation* t) {cal = t;}

    /** Returns whether the end or the start date of operationplans is used
    * to determine the effective operation. */
    bool getUseEndDate() const {return useEndDate;}

    /** Updates whether the end or the start date of operationplans is used
    * to determine the effective operation. */
    void setUseEndDate(const bool b) {useEndDate = b;}

    void DECLARE_EXPORT beginElement (XMLInput&, XMLElement&);
    void DECLARE_EXPORT writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void DECLARE_EXPORT endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(OperationEffective) + getName().size() + HasDescription::memsize();}

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual DECLARE_EXPORT OperationPlan* createOperationPlan (float, Date,
        Date, const Demand*, bool updates_okay=true, OperationPlan* = NULL,
        unsigned long i=0, bool makeflowsloads=true) const;

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - The calendar is used to determine the right operation. Either the
      *    start or the end date is used to search in the calendar buckets.
      *  - After determining the right operation, that sub operation determines
      *    the rest.
      *  - Calling this function when the calendar is still NULL has no
      *    effect at all.
      * @see Operation::setOperationPlanParameters
      */
    DECLARE_EXPORT void setOperationPlanParameters
      (OperationPlan* opplan, float q, Date s, Date e, bool = true) const;

  private:
    /** Stores the calendar. This calendar stores for each date in the horizon
    * which operation is to be used. */
    const CalendarOperation* cal;

    /** Specifies whether to use the start or the end date as the date to use.
      * The default is to use the end date.
      */
    bool useEndDate;
};


/** @brief This class subclasses the OperationPlan class for operations of type
  * OperationEffective. 
  *
  * Such operationplans need an extra field to point to the suboperationplan.
  * @see OperationPlan, OperationEffective
  */
class OperationPlanEffective : public OperationPlan
{
    TYPEDEF(OperationPlanEffective);
    friend class OperationEffective;

  private:
    OperationPlan* effopplan;

  public:
    OperationPlanEffective() : effopplan(NULL) {};
    DECLARE_EXPORT ~OperationPlanEffective();
    DECLARE_EXPORT void addSubOperationPlan(OperationPlan* o);
    DECLARE_EXPORT void setQuantity(float f, bool roundDown=false);
    DECLARE_EXPORT void eraseSubOperationPlan(OperationPlan* o);
    DECLARE_EXPORT void setEnd(Date d);
    DECLARE_EXPORT void setStart(Date d);
    DECLARE_EXPORT void update();
    DECLARE_EXPORT void initialize();

    /** Returns the sub-operationplan. */
    virtual OperationPlan* getSubOperationPlan() const {return effopplan;}
};


/** @brief An item defines the products being planned, sold, stored and/or
  * manufactured. Buffers and demands have a reference an item.
  *
  * This is an abstract class.
  */
class Item
      : public HasHierarchy<Item>, public HasDescription, public Object
{
    TYPEDEF(Item);
  public:
    /** Constructor. Don't use this directly! */
    explicit Item(const string& str)
        : HasHierarchy<Item> (str), deliveryOperation(NULL) {}

    /** Returns the delivery operation.<br>
      * This field is inherited from a parent item, if it hasn't been
      * specified.
      */
    Operation::pointer getDelivery() const
    {
      // Current item has a non-empty deliveryOperation field
      if (deliveryOperation) return deliveryOperation;

      // Look for a non-empty deliveryOperation field on owners
      for (Item::pointer i = getOwner(); i; i=i->getOwner())
        if (i->deliveryOperation) return i->deliveryOperation;

      // The field is not specified on the item or any of its parents.
      return NULL;
    }

    /** Updates the delivery operation.<br>
      * If some demands have already been planned using the old delivery
      * operation they are left untouched and won't be replanned.
      */
    void setDelivery(const Operation* o) {deliveryOperation = o;}

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);
    DECLARE_EXPORT void beginElement (XMLInput&, XMLElement&);

    /** Destructor. */
    virtual DECLARE_EXPORT ~Item();

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  private:
    /** This is the operation used to satisfy a demand for this item.
      * @see Demand
      */
    const Operation* deliveryOperation;
};


/** @brief This class is the default implementation of the abstract Item 
  * class. */
class ItemDefault : public Item
{
    TYPEDEF(ItemDefault);
  public:
    explicit ItemDefault(const string& str) : Item(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(ItemDefault) + getName().size() + HasDescription::memsize();}
};


/** @brief A buffer represents a combination of a item and location.<br>
  * It is the entity for keeping modeling inventory.
  */
class Buffer : public HasHierarchy<Buffer>, public HasLevel,
      public Plannable, public HasDescription
{
    TYPEDEF(Buffer);
    friend class Flow;
    friend class FlowPlan;

  public:
    typedef TimeLine<FlowPlan> flowplanlist;
    typedef Association<Operation,Buffer,Flow>::ListB flowlist;

    /** Constructor. Implicit creation of instances is disallowed. */
    explicit Buffer(const string& str) : HasHierarchy<Buffer>(str),
        hidden(false), producing_operation(NULL), loc(NULL), it(NULL),
        min_cal(NULL), max_cal(NULL) {}

    /** Returns the operation that is used to supply extra supply into this
      * buffer. */
    Operation::pointer getProducingOperation() const {return producing_operation;}

    /** Updates the operation that is used to supply extra supply into this
      * buffer. */
    void setProducingOperation(const Operation* o)
      {producing_operation = o; setChanged();}

    /** Returns the item stored in this buffer. */
    Item::pointer getItem() const {return it;}

    /** Updates the Item stored in this buffer. */
    void setItem(const Item* i) {it = i; setChanged();}

    /** Returns the Location of this buffer. */
    Location::pointer getLocation() const {return loc;}

    /** Updates the location of this buffer. */
    void setLocation(const Location* i) {loc = i;}

    /** Returns a pointer to a calendar for storing the minimum inventory
      * level. */
    CalendarFloat::pointer getMinimum() const {return min_cal;}

    /** Returns a pointer to a calendar for storing the maximum inventory
      * level. */
    CalendarFloat::pointer getMaximum() const {return max_cal;}

    /** Updates the minimum inventory target for the buffer. */
    DECLARE_EXPORT void setMinimum(const CalendarFloat *cal);

    /** Updates the minimum inventory target for the buffer. */
    DECLARE_EXPORT void setMaximum(const CalendarFloat *cal);

    DECLARE_EXPORT virtual void beginElement(XMLInput&, XMLElement&);
    DECLARE_EXPORT virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT virtual void endElement(XMLInput&, XMLElement&);

    /** Destructor. */
    virtual DECLARE_EXPORT ~Buffer();

    /** Returns the available material on hand immediately after the
      * given date.
      */
    DECLARE_EXPORT double getOnHand(Date d = Date::infinitePast) const;

    /** Update the on-hand inventory at the start of the planning horizon. */
    DECLARE_EXPORT void setOnHand(float f);

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
    Flow* findFlow(const Operation* o) const {return flows.find(o);}

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

  private:
    /** This models the dynamic part of the plan, representing all planned
      * material flows on this buffer. */
    flowplanlist flowplans;

    /** This models the defined material flows on this buffer. */
    flowlist flows;

    /** Hide this entity from serialization or not. */
    bool hidden;

    /** This is the operation used to create extra material in this buffer. */
    const Operation *producing_operation;

    /** Location of this buffer.<br>
      * This field is only used as information.<br>
      * The default is NULL.
      */
    const Location* loc;

    /** Item being stored in this buffer.<br>
      * The default value is NULL.
      */
    const Item* it;

    /** Points to a calendar to store the minimum inventory level.<br>
      * The default value is NULL, resulting in a constant minimum level
      * of 0.
      */
    const CalendarFloat *min_cal;

    /** Points to a calendar to store the maximum inventory level.<br>
      * The default value is NULL, resulting in a buffer without excess
      * inventory problems.
      */
    const CalendarFloat *max_cal;
};



/** @brief This class is the default implementation of the abstract Buffer class. */
class BufferDefault : public Buffer
{
    TYPEDEF(BufferDefault);
  public:
    explicit BufferDefault(const string& str) : Buffer(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    virtual size_t getSize() const
      {return sizeof(BufferDefault) + getName().size() + HasDescription::memsize();}
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
    TYPEDEF(BufferInfinite);
  public:
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual const MetaClass& getType() const {return metadata;}
    virtual size_t getSize() const
      {return sizeof(BufferInfinite) + getName().size() + HasDescription::memsize();}
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
    TYPEDEF(BufferProcure);
  public:
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual const MetaClass& getType() const {return metadata;}
    virtual size_t getSize() const
      {return sizeof(BufferProcure) + getName().size() + HasDescription::memsize();}
    explicit BufferProcure(const string& c) : Buffer(c), min_inventory(0), 
      max_inventory(0), size_minimum(0), size_maximum(FLT_MAX), size_multiple(0), 
      oper(NULL) {}
    static DECLARE_EXPORT const MetaClass metadata;

    /** Return the purchasing leadtime. */
    TimePeriod getLeadtime() const {return leadtime;}

    /** Update the procurement leadtime. */
    void setLeadtime(TimePeriod p) {if (p>=0L) leadtime = p;}

    /** Return the release time fence. */
    TimePeriod getFence() const {return fence;}

    /** Update the release time fence. */
    void setFence(TimePeriod p) {if (p>=0L) fence = p;}

    /** Return the inventory level that will trigger creation of a 
      * purchasing.
      */
    float getMinimumInventory() const {return min_inventory;}

    /** Update the minimum inventory level to trigger replenishments. */
    void setMinimumInventory(float f) 
    {
      if (f<0) return;
      min_inventory = f;
      // minimum is increased over the maximum: auto-increase the maximum
      if (max_inventory < min_inventory) max_inventory = min_inventory;
    }

    /** Return the maximum inventory level to which we wish to replenish. */
    float getMaximumInventory() const {return max_inventory;}

    /** Update the inventory level to replenish to. */
    void setMaximumInventory(float f) 
    {
      if (f<0) return;
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
      if (p<0L) return;
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
      if (p<0L) return;
      max_interval = p;
      // maximum is lowered below the minimum: auto-decrease the minimum
      if (max_interval < min_interval) min_interval = max_interval;
    }

    /** Return the minimum quantity of a purchasing operation. */
    float getSizeMinimum() const {return size_minimum;}

    /** Update the minimum replenishment quantity. */
    void setSizeMinimum(float f) 
    {
      if (f<0) return;
      size_minimum = f;
      // minimum is increased over the maximum: auto-increase the maximum
      if (size_maximum < size_minimum) size_maximum = size_minimum;
   }

    /** Return the maximum quantity of a purchasing operation. */
    float getSizeMaximum() const {return size_maximum;}

    /** Update the maximum replenishment quantity. */
    void setSizeMaximum(float f) 
    {
      if (f<0) return;
      size_maximum = f;
      // maximum is lowered below the minimum: auto-decrease the minimum
      if (size_maximum < size_minimum) size_minimum = size_maximum;
    }

    /** Return the multiple quantity of a purchasing operation. */
    float getSizeMultiple() const {return size_multiple;}

    /** Update the multiple quantity. */
    void setSizeMultiple(float f) {if (f>=0) size_multiple = f;}

    /** Returns the operation that is automatically created to represent the 
      * procurements. 
      */
    DECLARE_EXPORT Operation* getOperation() const;

  private:
    /** Purchasing leadtime.<br/>
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
    float min_inventory;

    /** The maximum inventory level to which we plan to replenish.<br>
      * This is not a hard limit - other parameters can make that the actual 
      * inventory either never reaches this value or always exceeds it.
      */
    float max_inventory;

    /** Minimum time interval between purchasing operations. */
    TimePeriod min_interval;

    /** Maximum time interval between purchasing operations. */
    TimePeriod max_interval;

    /** Minimum purchasing quantity.<br>
      * The default value is 0, meaning no minimum. 
      */
    float size_minimum;

    /** Maximum purchasing quantity.<br>
      * The default value is 0, meaning no maximum limit. 
      */
    float size_maximum;

    /** Purchases are always rounded up to a multiple of this quantity.<br>
      * The default value is 0, meaning no multiple needs to be applied. 
      */
    float size_multiple;

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
    TYPEDEF(Flow);
  public:
    /** Destructor. */
    virtual DECLARE_EXPORT ~Flow();

    /** Constructor. */
    explicit Flow(Operation* o, Buffer* b, float q) : quantity(q)
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
    float getQuantity() const {return quantity;}

    /** Updates the material flow PER UNIT of the operationplan. Existing
      * flowplans are NOT updated to take the new quantity in effect. Only new
      * operationplans and updates to existing ones will use the new quantity
      * value.
      */
    void setQuantity(float f) {quantity = f;}

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

    /** Returns the date to be used for this flowplan. */
    virtual const Date& getFlowplanDate(const OperationPlan* o) const
      {return o->getDates().getStart();}

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, XMLElement&);
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
    virtual size_t getSize() const {return sizeof(Flow);}

  protected:
    /** Default constructor. */
    explicit Flow() : quantity(0.0f) {}

  private:
    /** Verifies whether a flow meets all requirements to be valid. */
    DECLARE_EXPORT void validate(Action action);

    /** Quantity of the flow. */
    float quantity;
};


/** @brief This class defines a material flow to/from a buffer, linked with an
  * operation. This subclass represents a flow that is at the start date of
  * the operation.
  */
class FlowStart : public Flow
{
    TYPEDEF(FlowStart);
  public:
    /** Constructor. */
    explicit FlowStart(Operation* o, Buffer* b, float q) : Flow(o,b,q) {}

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
    TYPEDEF(FlowEnd);
  public:
    /** Constructor. */
    explicit FlowEnd(Operation* o, Buffer* b, float q) : Flow(o,b,q) {}

    /** This constructor is called from the plan begin_element function. */
    explicit FlowEnd() {}

    /** Returns the date to be used for this flowplan. */
    const Date& getFlowplanDate(const OperationPlan* o) const
      {return o->getDates().getEnd();}

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;

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
    TYPEDEF(FlowPlan);
    friend class OperationPlan::FlowPlanIterator;
  private:
    /** Points to the flow instantiated by this flowplan. */
    const Flow *fl;

    /** Points to the operationplan owning this flowplan. */
    const OperationPlan *oper;

    /** Points to the next flowplan owned by the same operationplan. */
    FlowPlan *nextFlowPlan;

  public:
    /** Constructor. */
    explicit DECLARE_EXPORT FlowPlan(OperationPlan*, const Flow*);

    /** Returns the Flow of which this is an planning instance. */
    Flow::pointer getFlow() const {return fl;}

    /** Returns the operationplan owning this flowplan. */
    OperationPlan::pointer getOperationPlan() const {return oper;}

    /** Destructor. */
    virtual ~FlowPlan()
    {
      Object::WLock<Buffer> b = getFlow()->getBuffer();
      b->setChanged(); 
      b->flowplans.erase(this);
    }

    /** Writing the element.
      * This method has the same prototype as a usual instance of the Object
      * class, but this is only superficial: FlowPlan isn't a subclass of
      * Object at all.
      */
    void DECLARE_EXPORT writeElement(XMLOutput*, const XMLtag&, mode =DEFAULT) const;

    /** Updates the quantity of the flowplan by changing the quantity of the
      * operationplan owning this flowplan.
      * The boolean parameter is used to control whether to round up or down
      * in case the operation quantity must be a multiple.
      */
    void setQuantity(float qty, bool b=false)
    {Object::WLock<OperationPlan>(oper)->setQuantity(qty / getFlow()->getQuantity(), b);}

    /** Returns the date of the flowplan. */
    const Date& getDate() const {return getFlow()->getFlowplanDate(oper);}

    DECLARE_EXPORT void update();

    /** Returns whether the flowplan needs to be serialized. This is
      * determined by looking at whether the flow is hidden or not. */
    bool getHidden() const {return fl->getHidden();}

    /** Verifies whether the flowplan is properly in-line with its owning
      * operationplan. */
    DECLARE_EXPORT bool check() const;
};


/** @brief This class represents a workcentre, a physical or logical 
  * representation of capacity.
  */
class Resource : public HasHierarchy<Resource>,
      public HasLevel, public Plannable, public HasDescription
{
    TYPEDEF(Resource);
    friend class Load;
    friend class LoadPlan;

  public:
    /** Constructor. */
    explicit Resource(const string& str) : HasHierarchy<Resource>(str),
        max_cal(NULL), loc(NULL), hidden(false) {};

    /** Destructor. */
    virtual DECLARE_EXPORT ~Resource();

    /** Updates the size of a resource. */
    DECLARE_EXPORT void setMaximum(CalendarFloat* c);

    /** Return a pointer to the maximum capacity profile. */
    CalendarFloat::pointer getMaximum() const {return max_cal;}

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
    Load* findLoad(const Operation* o) const {return loads.find(o);}

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);
    DECLARE_EXPORT void beginElement (XMLInput&, XMLElement&);

    /** Returns the location of this resource. */
    Location::pointer getLocation() const {return loc;}

    /** Updates the location of this resource. */
    void setLocation(const Location* i) {loc = i;}

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
    const CalendarFloat* max_cal;

    /** Stores the collection of all loadplans of this resource. */
    loadplanlist loadplans;

    /** This is a list of all load models that are linking this resource with
      * operations. */
    loadlist loads;

    /** A pointer to the location of the resource. */
    const Location* loc;

    /** Specifies whether this resource is hidden for serialization. */
    bool hidden;
};


/** @brief This class is the default implementation of the abstract 
  * Resource class. 
  */
class ResourceDefault : public Resource
{
    TYPEDEF(ResourceDefault);
  public:
    explicit ResourceDefault(const string& str) : Resource(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(ResourceDefault) 
        + getName().size() + HasDescription::memsize();}
};


/** @brief This class represents a resource that'll never have any 
  * capacity shortage. */
class ResourceInfinite : public Resource
{
    TYPEDEF(ResourceInfinite);
  public:
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual const MetaClass& getType() const {return metadata;}
    explicit ResourceInfinite(const string& c) : Resource(c)
      {setDetectProblems(false);}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(ResourceInfinite) + getName().size() + HasDescription::memsize();}
};


/** @brief This class links a resource to a certain operation. */
class Load
      : public Object, public Association<Operation,Resource,Load>::Node,
      public Solvable
{
    TYPEDEF(Load);
    friend class Resource;
    friend class Operation;

  public:
    /** Constructor. */
    explicit Load(Operation* o, Resource* r, float u)
    {
      setOperation(o);
      setResource(r);
      setUsageFactor(u);
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
    float getUsageFactor() const {return usage;}

    /** Updates the usage factor of the load.
      * @exception DataException When a negative number is passed.
      */
    void setUsageFactor(float f)
    {
      if (usage < 0) throw DataException("Load usage can't be negative");
      usage = f;
    }

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void beginElement(XMLInput&, XMLElement&);
    DECLARE_EXPORT void endElement(XMLInput&, XMLElement&);
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
    Load() : usage(1.0f) {}

  private:
    /** This method is called to check the validity of the object. It will
      * delete the invalid loads: be careful with the 'this' pointer after
      * calling this method!
      */
    DECLARE_EXPORT void validate(Action action);

    /** Stores how much capacity is consumed during the duration of an
      * operationplan. */
    float usage;
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
    TYPEDEF(Plan);
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
    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement&  pElement);
    DECLARE_EXPORT void beginElement(XMLInput& pIn, XMLElement&  pElement);

    virtual void updateProblems() {};

    /** This method basically solves the whole planning problem. */
    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;
    virtual size_t getSize() const
      {return sizeof(Plan) + name.size() + descr.size();}
};


/** @brief This command is used for reading XML input. The input comes either
  * from a flatfile, or from the standard input. */
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

    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);

    string getDescription() const
    {
      if (filename.empty())
        return "parsing xml input from standard input";
      else
        return "parsing xml input from file '" + filename + "'";
    }
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(CommandReadXMLFile) + filename.size();}

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


/** @brief This command is used for reading XML input from a certain string. */
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
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const {return "parsing xml input string";}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(CommandReadXMLString) + data.size();}

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
  * the operation_plans, demand, problems, etc...).<br>
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
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const
      {return "saving the complete model into file '" + filename + "'";}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
    {
      return sizeof(CommandSave)
          + filename.size() + headerstart.size() + headeratts.size();
    }
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
  * This saved information covers the buffer flowplans, operation_plans, 
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
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const
      {return "saving the plan into text file '" + filename + "'";}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(CommandSavePlan) + filename.size();}
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
    void undo() {}
    bool undoable() const {return true;}
    string getDescription() const {return "printing the model size";}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandPlanSize);}
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
    CommandErase() : deleteStaticModel(false) {};
    DECLARE_EXPORT void execute();
    DECLARE_EXPORT void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const
    {
      return deleteStaticModel ? "Erasing the model" : "Erasing the plan";
    }
    bool getDeleteStaticModel() const {return deleteStaticModel;}
    void setDeleteStaticModel(bool b) {deleteStaticModel = b;}
    virtual const MetaClass& getType() const {return metadata;}
    virtual size_t getSize() const {return sizeof(CommandErase);}
    static DECLARE_EXPORT const MetaClass metadata;
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
    TYPEDEF(Demand);
  public:
    typedef slist<OperationPlan*> OperationPlan_list;

    /** Constructor. */
    explicit Demand(const string& str) : HasHierarchy<Demand>(str),
        it(NULL), oper(NULL), cust(NULL), qty(0.0), prio(0) {}

    /** Destructor. Deleting the demand will also delete all delivery operation
      * plans */
    virtual ~Demand() {deleteOperationPlans(true);}

    /** Returns the quantity of the demand. */
    float getQuantity() const {return qty;}

    /** Updates the quantity of the demand. The quantity must be be greater
      * than or equal to 0. */
    virtual DECLARE_EXPORT void setQuantity(float);

    /** Returns the priority of the demand.<br>
      * Lower numbers indicate a higher priority level.
      */
    int getPriority() const {return prio;}

    /** Updates the due date of the demand.<br>
      * Lower numbers indicate a higher priority level.
      */
    virtual void setPriority(int i) {prio=i; setChanged();}

    /** Returns the item/product being requested. */
    Item::pointer getItem() const {return it;}

    /** Updates the item/product being requested. */
    virtual void setItem(const Item *i) {it=i; setChanged();}

    /** This fields points to an operation that is to be used to plan the
      * demand. By default, the field is left to NULL and the demand will then
      * be planned using the delivery operation of its item.
      * @see Item::getDelivery()
      */
    Operation::pointer getOperation() const {return oper;}

    /** This function returns the operation that is to be used to satisfy this
      * demand. In sequence of priority this goes as follows:
      *   1) If the "operation" field on the demand is set, use it.
      *   2) Otherwise, use the "delivery" field of the requested item.
      *   3) Else, return NULL. This demand can't be satisfied!
      */
    DECLARE_EXPORT Operation::pointer getDeliveryOperation() const;

    /** Returns the cluster which this demand belongs to. */
    int getCluster() const
    {
      Operation::pointer o = getDeliveryOperation();
      return o ? o->getCluster() : 0;
    }

    /** Updates the operation being used to plan the demand. */
    virtual void setOperation(const Operation* o) {oper=o; setChanged();}

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
    Date getDue() const {return dueDate;}

    /** Updates the due date of the demand. */
    virtual void setDue(Date d) {dueDate = d; setChanged();}

    /** Returns the customer. */
    Customer::pointer getCustomer() const { return cust; }

    /** Updates the customer. */
    void setCustomer(const Customer* c) { cust = c; setChanged(); }

    /** Returns the total amount that has been planned. */
    DECLARE_EXPORT float getPlannedQuantity() const;

    virtual DECLARE_EXPORT void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual DECLARE_EXPORT void endElement(XMLInput& , XMLElement&  );
    virtual DECLARE_EXPORT void beginElement (XMLInput& , XMLElement&  );

    virtual void solve(Solver &s, void* v = NULL) const {s.solve(this,v);}

    /** Returns true if this demand is allowed to be planned late.
      * If so, the system will try to satisfy the demand at a later date.
      * If not, only a delivery at the requested date is allowed.
      * @see planShort
      */
    bool planLate() const {return !policy.test(0);}

    /** Returns true if this demand isn't allowed to be planned late.
      * If not, only a delivery at the requested date is allowed.
      * @see planLate
      */
    bool planShort() const {return policy.test(0);}

    /** Returns true if multiple delivery operationplans for this demand are
      * allowed.
      * @see planSingleDelivery
      */
    bool planMultiDelivery() const {return !policy.test(1);}

    /** Returns true if only a single delivery operationplan is allowed for this
      * demand.
      * @see planMultiDelivery
      */
    bool planSingleDelivery() const {return policy.test(1);}

    /** Resets the demand policies to the default values, and then applies the
      * policies specified in the argument string.
      * @see addPolicy
      */
    virtual void setPolicy(const string& s)
    {
      policy.reset();
      addPolicy(s);
    }

    /** The argument string is parsed in a valid policy number. The format
      * of the instput string is:<br>
      *   [[whitespace][policy]]*<br>
      * where:
      * <ul>
      * <li> 'whitespace' is a series of seperators (spaces, tabs, punctuations)
      * <li> 'policy' is one of the values:
      *    <ul>
      *    <li>PLANSHORT<br>
      *      A demand with this policy will be planned short if it can't be
      *      planned on time.<br>
      *      Opposite of PLANLATE policy.
      *    <li>PLANLATE<br>
      *      A demand with this policy will be planned late if it can't be
      *      planned on time.<br>
      *      Opposite of PLANSHORT policy.<br>
      *      This policy is applied by default.
      *    <li>SINGLEDELIVERY<br>
      *      A demand with this policy can have only a single delivery
      *      operationplan.<br>
      *      Opposite of the MULTIDELIVERY policy.
      *    <li>MULTIDELIVERY<br>
      *      A demand with this policy can have multiple delivery
      *      operationplans.<br>
      *      Opposite of the SINGLEDELIVERY policy.<br>
      *      This policy is applied by default.
      *    </ul>
      * </ul>
      * The policy string is case INsensitive.<br>
      * The default policy string is "PLANLATE MULTIDELIVERY"
      */
    virtual DECLARE_EXPORT void addPolicy(const string&);

    /** Recompute the problems. */
    virtual DECLARE_EXPORT void updateProblems();

    /** Specifies whether of not this demand is to be hidden from
      * serialization. The default value is false. */
    void setHidden(bool b) {policy.set(2,b);}

    /** Returns true if this demand is to be hidden from serialization. */
    bool getHidden() const {return policy.test(2);}

    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaCategory metadata;

  private:
    /** Requested item. */
    const Item *it;

    /** Delivery Operation. Can be left NULL, in which case the delivery
      * operation can be specified on the requested item. */
    const Operation *oper;

    /** Customer creating this demand. */
    const Customer *cust;

    /** Requested quantity. Only positive numbers are allowed. */
    float qty;

    /** Priority. Lower numbers indicate a higher priority level.*/
    int prio;

    /** Due date. */
    Date dueDate;

    /** Efficiently stores a number of different policy values for the demand.
      * The default value for each policy bit is 0 / false.
      * The bits have the following meaning:
      *  - 0: Late (false) or Short (true)
      *  - 1: Multi (false) or Single (true) delivery
      *  - 2: Hidden
      */
    bitset<3> policy;

    /** A list of operation plans to deliver this demand. */
    OperationPlan_list deli;
};


/** @brief This class is the default implementation of the abstract 
  * Demand class. */
class DemandDefault : public Demand
{
    TYPEDEF(DemandDefault);
  public:
    explicit DemandDefault(const string& str) : Demand(str) {}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const
      {return sizeof(DemandDefault) + getName().size() + HasDescription::memsize();}
};


/** @brief This class represents the resource capacity of an operation_plan.
  *
  * For both the start and the end date of the operation_plan, a load_plan
  * object is created. These are then inserted in the timeline structure
  * associated with a resource.
  */
class LoadPlan : public TimeLine<LoadPlan>::EventChangeOnhand
{
    TYPEDEF(LoadPlan);
    friend class OperationPlan::LoadPlanIterator;
  public:
    /** Public constructor.<br>
      * This constructor constructs the starting loadplan and will
      * also call a private constructor to creates the ending loadplan.
      * In other words, a single call to the constructor will create
      * two loadplan objects.
      */
    explicit DECLARE_EXPORT LoadPlan(OperationPlan*, const Load*);

    /** Return the date of the loadplan. */
    const Date & getDate() const
    {
      if (start_or_end == START) return oper->getDates().getStart();
      else return oper->getDates().getEnd();
    }

    OperationPlan* getOperationPlan() const {return oper;}
    Load* getLoad() const {return ld;}
    bool isStart() {return start_or_end == START;}
    virtual ~LoadPlan()
    {
      ld->getResource()->setChanged();
      ld->getResource()->loadplans.erase(this);
    }
    DECLARE_EXPORT void update();
    bool getHidden() const {return ld->getHidden();}

    /** Validates the consistency of the loadplan. */
    DECLARE_EXPORT bool check() const;

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

    /** A pointer to the operation_plan owning this load_plan. */
    OperationPlan *oper;

    /** Points to the next loadplan owned by the same operationplan. */
    LoadPlan *nextLoadPlan;
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
      ch << "Job '" << static_cast<OperationPlan*>(getOwner())->getIdentifier()
      << "' planned in the past";
      return ch.str();
    }
    bool isFeasible() {return false;}
    float getWeight()
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
    bool isFeasible() {return true;}
    float getWeight()
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
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
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
    bool isFeasible() {return false;}
    float getWeight() {return getDemand()->getQuantity();}
    explicit ProblemDemandNotPlanned(Demand* d) : Problem(d) {addProblem();}
    ~ProblemDemandNotPlanned() {removeProblem();}
    const DateRange getDateRange() const
      {return DateRange(getDemand()->getDue(),getDemand()->getDue());}
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}

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
    bool isFeasible() {return true;}

    /** The weight is equal to the delay, expressed in days.<br>
      * The quantity being delayed is not included.
      */
    float getWeight() 
    {
      return static_cast<float>(DateRange(
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
    bool isFeasible() {return true;}
    float getWeight() {return 1.0f;}
    explicit ProblemEarly(Demand* d) : Problem(d) {addProblem();}
    ~ProblemEarly() {removeProblem();}
    const DateRange getDateRange() const
    {
      return DateRange(getDemand()->getDue(),
          (*(getDemand()->getDelivery().begin()))->getDates().getEnd());
    }
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}

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
    bool isFeasible() {return true;}
    float getWeight()
      {return getDemand()->getQuantity() - getDemand()->getPlannedQuantity();}
    explicit ProblemShort(Demand* d) : Problem(d) {addProblem();}
    ~ProblemShort() {removeProblem();}
    const DateRange getDateRange() const
      {return DateRange(getDemand()->getDue(), getDemand()->getDue());}
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}

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
    bool isFeasible() {return true;}
    float getWeight()
      {return getDemand()->getPlannedQuantity() - getDemand()->getQuantity();}
    explicit ProblemExcess(Demand* d) : Problem(d) {addProblem();}
    ~ProblemExcess() {removeProblem();}
    const DateRange getDateRange() const
      {return DateRange(getDemand()->getDue(), getDemand()->getDue());}
    Demand* getDemand() const {return dynamic_cast<Demand*>(getOwner());}

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
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    explicit ProblemPlannedLate(OperationPlan* o) : Problem(o)
      {addProblem();}
    ~ProblemPlannedLate() {removeProblem();}
    const DateRange getDateRange() const
      {return dynamic_cast<OperationPlan*>(getOwner())->getDates();}

    /** Return the tolerance limit for problem detection. */
    static TimePeriod getAllowedLate() {return allowedLate;}

    /** Update the tolerance limit. Note that this will trigger re-evaluation of
      * all operation_plans and existing problems, which can be expensive in a
      * big plan. */
    static void setAllowedLate(TimePeriod p);

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
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    explicit ProblemPlannedEarly(OperationPlan* o) : Problem(o)
      {addProblem();}
    ~ProblemPlannedEarly() {removeProblem();}
    const DateRange getDateRange() const
      {return dynamic_cast<OperationPlan*>(getOwner())->getDates();}

    /** Return the tolerance limit for problem detection. */
    static TimePeriod getAllowedEarly() {return allowedEarly;}

    /** Update the tolerance limit. Note that this will trigger re-evaluation of
      * all operation_plans and existing problems, which can be expensive in a
      * big plan. */
    static void setAllowedEarly(TimePeriod p);

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
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    ProblemCapacityOverload(Resource* r, DateRange d, float q)
        : Problem(r), qty(q), dr(d) {addProblem();}
    ~ProblemCapacityOverload() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Resource* getResource() const {return dynamic_cast<Resource*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

  private:
    /** Overload quantity. */
    float qty;

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
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    ProblemCapacityUnderload(Resource* r, DateRange d, float q)
        : Problem(r), qty(q), dr(d) {addProblem();}
    ~ProblemCapacityUnderload() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Resource* getResource() const {return dynamic_cast<Resource*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

  private:
    /** Underload quantity. */
    float qty;

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
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    ProblemMaterialShortage(Buffer* b, Date st, Date nd, float q)
        : Problem(b), qty(q), dr(st,nd) {addProblem();}
    ~ProblemMaterialShortage() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Buffer* getBuffer() const {return dynamic_cast<Buffer*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

  private:
    /** Shortage quantity. */
    float qty;

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
    bool isFeasible() {return true;}
    float getWeight() {return 1.0f;}
    ProblemMaterialExcess(Buffer* b, Date st, Date nd, float q)
        : Problem(b), qty(q), dr(st,nd) {addProblem();}
    ~ProblemMaterialExcess() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Buffer* getBuffer() const {return dynamic_cast<Buffer*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaClass& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static DECLARE_EXPORT const MetaClass metadata;

  private:
    /** Excess quantity. */
    float qty;

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
      (const Operation* o, float q, Date d1, Date d2, const Demand* l,
      OperationPlan* ow=NULL, bool makeflowsloads=true)
    {
      opplan = o ?
          o->createOperationPlan(q, d1, d2, l, true, ow, 0, makeflowsloads)
          : NULL;
    }
    void execute()
    {
      if (opplan)
      {
        opplan->setAllowUpdates(true);
        opplan->initialize();
        opplan=NULL;
      }
    }
    void undo() {if (opplan) delete opplan; opplan=NULL;}
    bool undoable() const {return true;}
    ~CommandCreateOperationPlan() {delete opplan;}
    OperationPlan *getOperationPlan() const {return opplan;}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandCreateOperationPlan);}
    string getDescription() const
    {
      return "creating a new operationplan for operation '"
          + (opplan ? string(opplan->getOperation()->getName()) : string("NULL"))
          + "'";
    }

  private:
    /** Pointer to the newly created operation_plan. */
    OperationPlan *opplan;
};


/** @brief This class represents the command of moving an operationplan to a 
  * new date.
  * @todo Moving in a routing operation can't be undone with the current
  * implementation! The command will need to store all original dates of
  * the suboperationplans...
  */
class CommandMoveOperationPlan : public Command
{
  public:
    /** Constructor.<br>
      * Unlike the other commands the constructor already executes the change.
      * @param opplanptr Pointer to the operationplan being moved.
      * @param newDate New date of the operationplan.
      * @param startOrEnd Specifies whether the new date is the start (=false)
      * or end date (=true). By default we use the end date.
      */
    DECLARE_EXPORT CommandMoveOperationPlan
      (const OperationPlan* opplanptr, Date newDate, bool startOrEnd=true);
    void execute()
    {
      if (!opplan) return;
      WLock<OperationPlan>(opplan)->setAllowUpdates(true);
      opplan=NULL;
    }
    DECLARE_EXPORT void undo();
    bool undoable() const {return true;}
    ~CommandMoveOperationPlan() {if (opplan) undo();}
    OperationPlan::pointer getOperationPlan() const {return opplan;}
    virtual const MetaClass& getType() const {return metadata;}
    static DECLARE_EXPORT const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandMoveOperationPlan);}
    DECLARE_EXPORT string getDescription() const;
    /** Set another date for the operation.
      * @param newdate New start- or end date.
      */
    DECLARE_EXPORT void setDate(Date newdate);

  private:
    /** This is a pointer to the operation_plan being moved. */
    const OperationPlan *opplan;

    /** This flag specifies whether we keep the new date is a new start or a
      * new end date for the operation_plan. */
    bool use_end;

    /** This is the start- or enddate of the operation_plan before its move. */
    Date originaldate;
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

    /** Resets the iterator.<br>
      * This is usefull to initialize an iterator in uninitialized memory.
      * Calling this method on a properly initialized iterator will leak memory!
      */
    void reset() {type=4;}

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

  public:
    /** Resetting the iterator to some dummy value.<br>
      * This is useful when initializing an iterator in uninitialized memory.
      */
    void reset() {eiter.reset();}
    DECLARE_EXPORT const_iterator& operator++();
    bool operator != (const const_iterator& t) const {return iter!=t.iter;}
    bool operator == (const const_iterator& t) const {return iter==t.iter;}
    Problem* operator*() const {return iter;}
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
    PeggingIterator(const FlowPlan* e)
    {
      if (e)
        stack.push(state(0,e->getQuantity()>0 ? e->getQuantity() : -e->getQuantity(),1,e));
    }

    /** Assignment operator. */    
    PeggingIterator& operator=(const FlowPlan* x) 
    {
      while (!stack.empty()) stack.pop();
      if (x)
        stack.push(state(0,x->getQuantity()>0 ? x->getQuantity() : -x->getQuantity(),1,x));
      return *this;
    }

    /** Returns a reference to the flowplan pointed to by the iterator. */
    const FlowPlan& operator*() const {return *(stack.top().fl);}

    /** Returns a pointer to the flowplan pointed to by the iterator. */
    const FlowPlan* operator->() const {return stack.top().fl;}

    /** Returns the recursion depth of the iterator. The original flowplan
      * is at level 0, and each level (either upstream or downstream)
      * increments the value by 1.
      */
    short getLevel() const {return stack.top().level;}

    /** Returns the absolute quantity of the original flowplan that can still
      * be traced in the current flowplan.
      */
    double getQuantity() const {return stack.top().qty;}

    /** Returns which portion of the current flowplan is fed/supplied by the
      * original flowplan. */
    double getFactor() const {return stack.top().factor;}

    /** Returns false if the flowplan remained unpegged, i.e. it wasn't
      * -either completely or paritally- unconsumed at the next level.
      */
    bool getPegged() const {return stack.top().pegged;}

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
    bool operator==(const PeggingIterator& x) const {return stack == x.stack;}

    /** Inequality operator. */
    bool operator!=(const PeggingIterator& x) const {return stack != x.stack;}

    /** Conversion operator to a boolean value.
      * The return value is true when the iterator still has next elements to
      * explore. Returns false when the iteration is finished.
      */
    operator bool () const { return !stack.empty(); }

    /** This is useful when initializing an iterator in uninitialized memory. */
    void reset() 
    {
      statestack x;
      memcpy(&stack,&x,sizeof(statestack));
    }

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
      const FlowPlan* fl;
      /** Set to false when unpegged quantities are involved. */
      bool pegged;
      /** Constructor. */
      state(unsigned int l, double d, double f, const FlowPlan* ff, bool p = true)
          : qty(d), factor(f), level(l), fl(ff), pegged(p) {};
      /** Inequality operator. */
      bool operator != (const state& s) const
        {return fl!=s.fl || level!=s.level;}
      /** Equality operator. */
      bool operator == (const state& s) const
        {return fl==s.fl && level==s.level;}
    };

    typedef stack < state > statestack;

    /** A stack is used to store the iterator state. */
    statestack stack;

    /** Update the stack. */
    DECLARE_EXPORT void updateStack(short, double, double, const FlowPlan*, bool = true);

    /** Auxilary function to make recursive code possible. */
    DECLARE_EXPORT void pushflowplans(const OperationPlan*, bool, short, double, double, bool=false);

    /** Convenience variable during stack updates.
      * Depending on the value of this field, either the top element in the
      * stack is updated or a new state is pushed on the stack.
      */
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
    FlowPlanIterator(FlowPlan* b) : curflowplan(b) {}
  public:
    FlowPlanIterator(const FlowPlanIterator& b) {curflowplan = b.curflowplan;}
    bool operator != (const FlowPlanIterator &b) const
    {return b.curflowplan != curflowplan;}
    bool operator == (const FlowPlanIterator &b) const
      {return b.curflowplan == curflowplan;}
    FlowPlanIterator& operator++()
    {
      if (curflowplan) curflowplan = curflowplan->nextFlowPlan;
      return *this;
    }
    FlowPlanIterator operator++(int)
      {FlowPlanIterator tmp = *this; ++*this; return tmp;}
    FlowPlan* operator ->() const {return curflowplan;}
    FlowPlan& operator *() const {return *curflowplan;}
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
    LoadPlanIterator(LoadPlan* b) : curloadplan(b) {}
  public:
    LoadPlanIterator(const LoadPlanIterator& b) {curloadplan = b.curloadplan;}
    bool operator != (const LoadPlanIterator &b) const
      {return b.curloadplan != curloadplan;}
    bool operator == (const LoadPlanIterator &b) const
      {return b.curloadplan == curloadplan;}
    LoadPlanIterator& operator++()
    {
      if (curloadplan) curloadplan = curloadplan->nextLoadPlan;
      return *this;
    }
    LoadPlanIterator operator++(int)
      {LoadPlanIterator tmp = *this; ++*this; return tmp;}
    LoadPlan* operator ->() const {return curloadplan;}
    LoadPlan& operator *() const {return *curloadplan;}
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

}   // End namespace

#endif
