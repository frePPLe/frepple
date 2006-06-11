/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/include/frepple/model.h $
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

#ifndef MODEL_H
#define MODEL_H

/** @mainpage Frepple Library API
  * The Frepple class library provides a framework for modeling a
  * manufacturing environment. This document describes its C++ API.<P>
  *
  * @namespace frepple
  * @brief Core namespace
  */

// Visual C++ gives annoying warnings while compiling frepple:
//  4800 "'int': forcing value to bool 'true' or 'false' (performance warning)"
// The root cause is the method "typeinfo::operator==(const typeinfo&)" which
// returns an INT rather than the expected BOOL. Myabe Bill can explain why...
#ifdef _MSC_VER
#pragma warning( disable : 4800 )
#endif

#include "frepple/utils.h"
#include "frepple/timeline.h"

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
class BufferMinMax;
class Plan;
class Plannable;
class Calendar;
class Load;
class Location;
class Customer;
class HasProblems;
class Solvable;


/** This class is used for initialization and finalization of functionality. */
class LibraryModel
{
  public:
    static void initialize();
    static void finalize() {}
};


/** This is the class used to divide a time horizon in a number
  * of discrete time buckets.
  * Typical calendars are "weeks", "months", "quarters", ...
  */
class Calendar : public HasName<Calendar>, public Object
{
  public:
    /** This class represents a time bucket as a part of a calendar.
      * Manipulation of instances of this class need to be handled with the
      * methods on the friend class Calendar.
      * @see Calendar
      */
    class Bucket : public Object, public NonCopyable
    {
      friend class Calendar;
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

      protected:
        /** Constructor. */
        Bucket(Date n) : startdate(n) {}

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

        virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;

        /** Reads the bucket information from the input. Only the fields NAME
          * and START are read in. Other fields as also written out but these
          * are information-only fields.
          */
        void endElement(XMLInput& pIn, XMLElement&  pElement);

        virtual const MetaData& getType() const
          {return Calendar::metadata;}
    };

    /** Singly linked list of all buckets. */
    typedef list<Bucket*> Bucketlist;  // @todo replace by intrusive bucketlist

		/** An STL-like iterator to recurse over the list of buckets. */
		typedef Bucketlist::const_iterator bucket_iterator;

    /** Default constructor. */
    Calendar(const string& n) : HasName<Calendar>(n) {createNewBucket(Date());}

    /** Destructor, which needs to clean up the buckets too. */
    ~Calendar();

    /** This is a factory method that creates a new bucket using the start
      * date as the key field. The fields are passed as an array of character
      * pointers.
      * This method is intended to be used to create objects when reading
      * XML input data.
      */
    Bucket* createBucket(const Attributes* atts);

    /** Adds a new bucket to the list. */
    Bucket* addBucket(Date);

    /** Removes a bucket from the list. */
    void removeBucket(Bucket* bkt);

    /** Returns the bucket where a certain date belongs to.
      * A bucket will always be returned, i.e. the data structure is such
      * that we all dates between infinitePast and infiniteFuture match
      * with one (and only one) bucket.
      * @see findBucketIndex()
      */
    Bucket* findBucket(Date d) const;

    /** Returns the index of the bucket where a certain date belongs to. 
      * A bucket (and bucket index) will always be found. 
      * @see findBucket()
      */
    int findBucketIndex(Date d) const;

    /** Returns the bucket with a certain name. 
      * A NULL pointer is returned in case no bucket can be found with the
      * given name.
      */
    Bucket* findBucket(const string&) const;

    /** Returns a pointer to the list of buckets. Note that this list is
      * read-only, i.e. you can use it to browse through the buckets but
      * you can use it to update it.
      */
    const Bucketlist& getBuckets() const {return buckets;}

    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, XMLElement&  pElement) {}
    void beginElement(XMLInput& pIn, XMLElement&  pElement);

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

  private:
    /** List of buckets. */
    Bucketlist buckets;

    /** This is the factory method used to generate new buckets. Each subclass
      * should provide an override for this function. */
    virtual Bucket* createNewBucket(Date n) {return new Bucket(n);}
};


/**
  * The template type must statisfy the following requirements:
  *   - XML import supported by the operator >> of the class XMLElement.
  *   - XML export supported by the method writeElement of the class XMLOutput.
  * Subclasses will need to implement the getType() method.
  */
template <typename T> class CalendarValue : public Calendar
{
  public:
    /** @see Calendar::Bucket */
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

        virtual const MetaData& getType() const
          {return CalendarValue<T>::metadata;}
    };

    /** Default constructor. */
    CalendarValue(const string& n) : Calendar(n) {}

    /** Returns the value on the specified date. */
    const T& getValue(const Date d) const
      {return static_cast<BucketValue*>(findBucket(d))->getValue();}

    /** Updates the value in a certain time bucket. */
    void setValue(const Date d, const T& v)
      {static_cast<BucketValue*>(findBucket(d))->setValue(v);}

    virtual const MetaData& getType() const = 0;

	  const T& getValue(Calendar::Bucketlist::const_iterator& i) const
		  {return reinterpret_cast<BucketValue*>(*i)->getValue();}

  private:
    /** Factory method to add new buckets to the calendar.
      * @see Calendar::addBucket()
      */
    Bucket* createNewBucket(Date n) {return new BucketValue(n);}
};


/**
  * The template type must statisfy the following requirements:
  *   - subclass the Object class and implement the beginElement(),
  *     writeElement() and endElement() as appropriate.
  *   - Implement a metadata data element
  */
template <typename T> class CalendarPointer : public Calendar
{
  public:
    /** @see Calendar::Bucket */
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
              MetaCategory::ControllerDefault(T::metadata,pIn.getAttributes())
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

        virtual const MetaData& getType() const
          {return CalendarPointer<T>::metadata;}
    };

    /** Default constructor. */
    CalendarPointer(const string& n) : Calendar(n) {}

    /** Returns the value on the specified date. */
    T* getValue(const Date d) const
      {return static_cast<BucketPointer*>(findBucket(d))->getValue();}

    /** Updates the value in a certain time bucket. */
    void setValue(const Date d, T* v)
      {static_cast<BucketPointer*>(findBucket(d))->setValue(v);}

    virtual const MetaData& getType() const = 0;

  private:
    /** Factory method to add new buckets to the calendar.
      * @see Calendar::addBucket()
      */
    Bucket* createNewBucket(Date n) {return new BucketPointer(n);}
};


/** A calendar only defining time buckets and not storing any data fields. */
class CalendarVoid : public Calendar
{
  public:
    CalendarVoid(const string& n) : Calendar(n) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** A calendar storing float values in its buckets. */
class CalendarFloat : public CalendarValue<float>
{
  public:
    CalendarFloat(const string& n) : CalendarValue<float>(n) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** A calendar storing integer values in its buckets. */
class CalendarInt : public CalendarValue<int>
{
  public:
    CalendarInt(const string& n) : CalendarValue<int>(n) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** A calendar storing boolean values in its buckets. */
class CalendarBool : public CalendarValue<bool>
{
  public:
    CalendarBool(const string& n) : CalendarValue<bool>(n) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** A calendar storing strings in its buckets. */
class CalendarString : public CalendarValue<string>
{
  public:
    CalendarString(const string& n) : CalendarValue<string>(n) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** A calendar storing pointers to operations in its buckets. */
class CalendarOperation : public CalendarPointer<Operation>
{
  public:
    CalendarOperation(const string& n) : CalendarPointer<Operation>(n) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** A problem represents inconsistencies, alerts and warnings in the model.
  * Problems are maintained internally by the system. They are thus 
  * export-only, meaning that we can't directly import or build problems.
  * This class is the pure virtual base class for all problem types.
  * The usage of the problem objects is based on the following principles:
  *   - Problems objects are passive. They don't actively change the model
  *     state.
  *   - Objects of the HasProblems class actively create and destroy Problem
  *     objects.
  *   - Problem objects are managed in a lazy way, meaning they only are
  *     getting created when the list of problems is requested by the user.
  *   - Given all the above, Problems are lightweight objects that consume 
  *     limited memory.
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

    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, XMLElement&  pElement) {}

    /** Returns an iterator to the very first problem. The iterator can be 
      * incremented till it points past the very last problem. */
    static const_iterator begin();

    /** Return an iterator to the first problem of this entity. The iterator
      * can be incremented till it points past the last problem of this
      * plannable entity.<br>
      * The boolean argument specifies whether the problems need to be 
      * recomputed as part of this method.
      */
    static const_iterator begin(HasProblems*, bool = true); 

    /** Return an iterator pointing beyond the last problem. */
    static const const_iterator end();

    /** Erases the list of all problems. This methods can be used reduce the
      * memory consumption at critical points. The list of problems will be
      * recreated when the problem detection is triggered again.
      */
    static void clearProblems();

    /** Erases the list of problems linked with a certain plannable object.
      * If the second parameter is set to true, the problems will be 
      * recreated when the next problem detection round is triggered. 
      */
    static void clearProblems(HasProblems* p, bool setchanged = true);

    /** Returns a pointer to the plannable object that owns this problem. */
    HasProblems* getOwner() const {return owner;}

    /** Return a reference to the metadata structure. */
    virtual const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaCategory metadata;

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

    /** Comparison of 2 problems.
      * To garantuee that the problems are sorted in a consistent and stable 
      * way, the following sorting criteria are used (in order of priority):
      *   1) Entity  
      *      This sort is to be ensured by the client. This method can't 
      *      compare problems of different entities!
      *   2) Type
      *      Each problem type has a hashcode used for sorting.
      *   3) Start date  
      * The sorting is expected such that it can be used as a key, i.e. no 
      * two problems of will ever evaluate to be identical.
      */
    bool operator < (const Problem& a) const;
};


/** Classes that keep track of problem conditions need to implment this class.
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
    static EntityIterator beginEntity();

    /** Returns an iterator pointing beyond the last HasProblem object. */
    static EntityIterator endEntity();

    /** Constructor. */
    HasProblems() : firstProblem(NULL) {}

    /** Destructor. It needs to take care of making sure all problems objects
      * are being deleted as well. */
    virtual ~HasProblems() {Problem::clearProblems(this, false);}

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


/** This class is an implementation of the "visitor" design pattern.
  * The goal is to decouple the solver/algorithms from the model/data
  * representation. Different solvers can be easily be plugged in to work on
  * the same data.
  */
class Solver : public Object, public HasName<Solver>
{
  public:
    explicit Solver(const string& n) : HasName<Solver>(n), verbose(false) {}
    virtual ~Solver() {}

    virtual void writeElement (XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual void endElement(XMLInput& pIn, XMLElement& pElement);

    virtual void solve(void* = NULL) = 0;
    virtual void solve(Demand*,void* = NULL)
      {throw LogicException("Called undefined solve(Demand*) method");}
    virtual void solve(Operation*,void* = NULL)
      {throw LogicException("Called undefined solve(Operation*) method");}
    virtual void solve(OperationFixedTime* o, void* v = NULL)
      {solve(reinterpret_cast<Operation*>(o),v);}
    virtual void solve(OperationTimePer* o, void* v = NULL)
      {solve(reinterpret_cast<Operation*>(o),v);}
    virtual void solve(OperationRouting* o, void* v = NULL)
      {solve(reinterpret_cast<Operation*>(o),v);}
    virtual void solve(OperationAlternate* o, void* v = NULL)
      {solve(reinterpret_cast<Operation*>(o),v);}
    virtual void solve(OperationEffective* o, void* v = NULL)
      {solve(reinterpret_cast<Operation*>(o),v);}
    virtual void solve(Resource*,void* = NULL)
      {throw LogicException("Called undefined solve(Resource*) method");}
    virtual void solve(ResourceInfinite* r, void* v = NULL)
      {solve(reinterpret_cast<Resource*>(r),v);}
    virtual void solve(Buffer*,void* = NULL)
      {throw LogicException("Called undefined solve(Buffer*) method");}
    virtual void solve(BufferInfinite* b, void* v = NULL)
      {solve(reinterpret_cast<Buffer*>(b),v);}
    virtual void solve(BufferMinMax* b, void* v = NULL)
      {solve(reinterpret_cast<Buffer*>(b),v);}
    virtual void solve(Load* b, void* v = NULL)
      {throw LogicException("Called undefined solve(Load*) method");}
    virtual void solve(Flow* b, void* v = NULL)
      {throw LogicException("Called undefined solve(Flow*) method");}
    virtual void solve(FlowEnd* b, void* v = NULL)
      {solve(reinterpret_cast<Flow*>(b),v);}
    virtual void solve(Solvable*,void* = NULL)
      {throw LogicException("Called undefined solve(Solvable*) method");}

    /** Returns true if elaborate and verbose output is requested. */
    bool getVerbose() const {return verbose;}

    /** Controls whether verbose output will be generated. */
    void setVerbose(bool b) {verbose = b;}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

  protected:
    /** Controls how much messages we want to generate. The default value
      * is false. */
    bool verbose;
};


/** This class needs to be implemented by all classes that implement dynamic
  * behavior, and which can be called by a solver.
  */
class Solvable
{
  public:
    /** This method is called by solver classes. The implementation of this
      * class simply calls the solve method on the solver class. Using the
      * polymorphism the solver can implement seperate methods for different
      * plannable subclasses.
      */
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    /** Destructor. */
    virtual ~Solvable() {}
};


/** This command runs a specific solver. */
class CommandSolve : public Command
{
  private:
    Solver *sol;
  public:
    CommandSolve() : sol(NULL) {};

    /** The core of the execute method is a call to the solve() method of the
      * solver. */
    void execute();

    /** This type of command can't be undone. */
    void undo() {}
    bool undoable() const {return false;}
    void beginElement(XMLInput& pIn, XMLElement& pElement);
    void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const {return "running a solver";}
    Solver* getSolver() const {return sol;}
    void setSolver(Solver* s) {sol = s;}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This class needs to be implemented by all classes that implement dynamic
  * behavior in the plan. 
  * The problem detection logic is implemented in the detectProblems() method.
  * For performance reasons, problem detection is "lazy", i.e. problems are
  * computed only when somebody really needs the access to the list of
  * problems.
  **/
class Plannable : public Object, public HasProblems, public Solvable
{
  public:
    /** Constructor. */
    Plannable() : useProblemDetection(true), changed(true)
     {anyChange = true;};

    /** Specify whether this entity reports problems. */
    void setDetectProblems(bool b);

    /** Returns whether or not this object needs to detect problems. */
    bool getDetectProblems() const {return useProblemDetection;}

    /** Loops through all plannable objects and updates their problems if
      * required. */
    static void computeProblems();

    /** See if this entity has changed since the last problem
      * problem detection run. */
    bool getChanged() const {return changed;}

    /** Mark that this entity has been updated and that the problem
      * detection needs to be redone. */
    void setChanged(bool b = true) {changed=b; if (b) anyChange=true;}

    /** Implement the pure virtual function from the HasProblem class. */
    Plannable* getEntity() const {return const_cast<Plannable*>(this);}

    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual void endElement(XMLInput& pIn, XMLElement& pElement);

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


/** The purpose of this class is to compute the levels of all buffers,
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
    static bool recomputeLevels;

    /** This flag is set to true during the computation of the levels. It is
      * required to ensure safe access to the level information in a
      * multi-threaded environment.
      */
    static bool computationBusy;

    /** Stores the total number of clusters in the model. */
    static unsigned short numberOfClusters;

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
    static void computeLevels();

  public:
    /** Returns the total number of clusters in the system. If not up to date
      * the recomputation will be triggered. */
    static unsigned short getNumberOfClusters()
    {
      if(recomputeLevels || computationBusy) computeLevels();
      return numberOfClusters;
    }

    /** Return the level (and recompute first if required). */
    short getLevel() const
    {
      if(recomputeLevels || computationBusy) computeLevels();
      return lvl;
    }

    /** Return the cluster number (and recompute first if required). */
    unsigned short getCluster() const
    {
      if(recomputeLevels || computationBusy) computeLevels();
      return cluster;
    }

    /** This function should be called when something is changed in the network
      * structure. The notification sets a flag, but does not immediately
      * trigger the recomputation.
      * @see computeLevels
      */
    static void triggerLazyRecomputation() {recomputeLevels = true;}
};


/** This class is used to associate buffers and resources with a physical
  * location. This is useful for reporting but has no direct impact on the
  * planning behavior of buffers or resources.
  */
class Location
  : public HasHierarchy<Location>, public HasDescription, public Object
{
  public:
    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void beginElement(XMLInput& pIn, XMLElement& pElement);
    void endElement(XMLInput& pIn, XMLElement& pElement);
    explicit Location(const string& n) : HasHierarchy<Location>(n) {}
    virtual ~Location();
    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;
};


class LocationDefault : public Location
{
  public:
    explicit LocationDefault(const string& str) : Location(str) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This class represents customers, and link them to certain demands. */
class Customer
  : public HasHierarchy<Customer>, public HasDescription, public Object
{
  public:
    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void beginElement(XMLInput& pIn, XMLElement& pElement);
    void endElement(XMLInput& pIn, XMLElement& pElement);
    Customer(const string& n) : HasHierarchy<Customer>(n) {}
    virtual ~Customer();
    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;
};


class CustomerDefault : public Customer
{
  public:
    explicit CustomerDefault(const string& str) : Customer(str) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This class represents an Operation. It's a pure virtual class. */
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
      size_minimum(0.0f), size_multiple(0.0f), hidden(false), opplan(NULL) {}

  public:
    /** Destructor. */
    virtual ~Operation();

    /** Returns the delay after this operation. */
    TimePeriod getDelay() const {return delaytime;}

    /** Updates the delay after this operation. */
    void setDelay(TimePeriod t)
    {
      if(t<TimePeriod(0L)) return;
      delaytime=t;
      setChanged();
    }

    typedef Association<Operation,Buffer,Flow>::ListA flowlist;
    typedef Association<Operation,Resource,Load>::ListA  loadlist;

    /** This is the factory method which creates all operationplans of the
      * operation. */
    virtual OperationPlan* createOperationPlan (float q, Date s, Date e,
      Demand* l, bool updates_okay=true, OperationPlan* ow=NULL,
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
      * Subclasses need to override this method to implement the correct
      * logic.
      */
    virtual void setOperationPlanParameters
      (OperationPlan*, float, Date, Date) const = 0;

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

    void beginElement(XMLInput& , XMLElement& );
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    typedef list<Operation*> Operationlist;

    /** Returns a reference to the list of sub operations of this operation. */
    virtual const Operationlist& getSubOperations() {return nosubOperations;}

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

    void removeSuperOperation(Operation *o)
    {superoplist.remove(o); o->removeSubOperation(this);}

    /** Return the relase fence of this operation. */
    TimePeriod getFence() const {return fence;}

    /** Update the release fence of this operation. */
    void setFence(TimePeriod t) {if(fence!=t) setChanged(); fence=t;}

    virtual void updateProblems();

    void setHidden(bool b) {if(hidden!=b) setChanged(); hidden = b;}
    bool getHidden() const {return hidden;}

    static const MetaCategory metadata;

  protected:
    void initOperationPlan (OperationPlan*, float, const Date&, const Date&,
      Demand*, bool, OperationPlan*, unsigned long, bool = true) const;

  private:
    /** List of operations using this operation as a sub-operation */
    Operationlist superoplist;

    /** Empty list of operations. For operation types which have no
      * suboperations this list is used as the list of suboperations.
      */
    static Operationlist nosubOperations;

    /** Represents the time between this operation and a next one. */
    TimePeriod delaytime;

    /** Represents the release fence of this operation, i.e. a period of time
      * (relative to the current date of the plan) in which no operationplan
      * is allowed to be created. */
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

    /** A pointer to the first OperationPlan. */
    OperationPlan* opplan;
};


/** An operationplan is the key dynamic element of a plan. It represents
  * a certain quantity being planned along a certain operation during
  * a certain date range.
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
    friend class OperationPlanEffective; 
    friend class OperationEffective;  

  public:
    /** This class models an STL-like iterator that allows us to iterate over
      * the operationplans in a simple and safe way.<br>
      * Objects of this class are created by the begin() and end() functions.
      */
    class iterator
    {
      public:
        /** Constructor. The iterator will loop only over the operationplans
          * of the operation passed. */
        iterator(Operation* x) : op(Operation::end()) 
          {opplan = x ? getFirstOpPlan(x) : NULL;}

        /** Constructor. The iterator will loop over all operationplans. */
        iterator() : op(Operation::begin())
        {
          while (op!=Operation::end() && !getFirstOpPlan(*op)) ++op; 
          opplan = (op!=Operation::end()) ? getFirstOpPlan(*op) : NULL; 
        }

        /** Copy constructor. */
        iterator(const iterator& it) : opplan(it.opplan), op(it.op) {}

        /** Return the content of the current node. */
        OperationPlan* operator*() const {return opplan;}

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
            do ++op; while (op!=Operation::end() && !getFirstOpPlan(*op));
            opplan = (op!=Operation::end()) ? getFirstOpPlan(*op) : NULL; 
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
            do ++op; while (op!=Operation::end() && !getFirstOpPlan(*op));
            opplan = (op!=Operation::end()) ? getFirstOpPlan(*op) : NULL; 
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
    static Object* createOperationPlan 
      (const MetaCategory&, const Attributes* atts);

    /** Destructor. */
    virtual ~OperationPlan();

    virtual void setChanged(bool b = true);

    /** Returns the quantity. */
    float getQuantity() const {return quantity;}

    /** Updates the quantity.
      * The quantity of an operationplan must be greater than to 0.
      * This method can only be called on top operationplans. Sub operation
      * plans should pass on a call to the parent operationplan.
      */
    virtual void setQuantity(float f, bool roundDown=false);

    /** Returns a pointer to the demand for which this operation is a delivery.
      * If the operationplan isn't a delivery operation, this is a NULL pointer.
      */
    Demand* getDemand() const {return lt;}

    /** Updates the demand to which this operationplan is a solution. */
    void setDemand(Demand* l);

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
    static void deleteOperationPlans(Operation* o, bool deleteLocked=false);

    /** Locks/unlocks an operationplan. A locked operationplan is never
      * changed. Only top-operationplans can be locked. Sub-operationplans
      * pass on a call to this function to their owner.
      */
    void setLocked(bool b = true)
    {
      if (owner) owner->setLocked(b);
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
    void setOwner(OperationPlan* o);

    /** Returns a pointer to the operationplan for which this operationplan
      * a sub-operationplan.
      * E.g. Sub-operationplans of a routing refer to the overall routing
      * operationplan.
      * E.g. An alternate sub-operationplan refers to its parent.
      */
    OperationPlan* getOwner() const {return owner;}

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
    virtual void setEnd(Date);

    /** Updates the start date of the operation_plan. The end date is computed.
      * Locked operation_plans are not updated by this function.
      */
    virtual void setStart(Date);

    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void beginElement(XMLInput&, XMLElement&);
    void endElement(XMLInput&, XMLElement&);

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
    virtual void initialize();

    /** Returns a reference to the list of flowplans. */
    const slist<FlowPlan*>& getflowplans() {return flowplans;}

    /** Returns a reference to the list of LoadPlans. */
    const slist<LoadPlan*>& getLoadPlans() {return LoadPlans;}

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
    bool check();

    /** This function is used to create the proper loadplan and flowplan
      * objects associated with the operation. */
    void createFlowLoads();

    bool getHidden() const {return getOperation()->getHidden();}

    /** Searches for an OperationPlan with a given identifier. Returns a NULL
      * pointer if no such OperationPlan can be found.
      * The method is of complexity O(n), i.e. involves a LINEAR search through
      * the existing operationplans, and can thus be quite slow in big models.
      */
    static OperationPlan* findId(unsigned long l);

    /** Problem detection is actually done by the Operation class. That class
      * actually "delegates" the responsability to this class, for efficiency.
      */
    virtual void updateProblems();

    /** Implement the pure virtual function from the HasProblem class. */
    Plannable* getEntity() const {return oper;}

    /** Return the metadata. We return the metadata of the operation class, 
      * not the one of the operationplan class! 
      */
    const MetaData& getType() const {return getOperation()->getType();}
    
    static const MetaCategory metadata;

  protected:
    virtual void update();
    void resizeFlowLoadPlans();

    /** Pointer to a higher level OperationPlan. */
    OperationPlan *owner;

    /** Quantity. */
    float quantity;

    /** Run the update method after each change? Settingthis field to false
      * allows you to do a number of changes after another and then run the
      * update method only once.
      * This field is only relevant for top-operationplans.
      */
    bool runupdate;

    /** Default constructor.
      * This way of creating operationplan objects is not intended for use by
      * any client applications. Client applications should use the factory
      * method on the operation class instead.
      * Subclasses of the Operation class may use this constructor in their
      * own override of the createOperationPlan method.
      * @see Operation::createOperationPlan
      */
    OperationPlan() : owner(NULL), quantity(0.0), runupdate(false), 
      locked(false), lt(NULL), id(0), oper(NULL), prev(NULL), next(NULL) {}

  private:
    /** Returns a pointer to the operation being instantiated. */
    static OperationPlan* getFirstOpPlan(Operation* o) {return o->opplan;}

    /** Is this operationplan locked? A locked operationplan doesn't accept
      * any changes. This field is only relevant for top-operationplans. */
    bool locked;

    /** Counter of OperationPlans, which is used to automatically assign a
      * unique identifier for each operationplan.
      * @see getIdentifier()
      */
    static unsigned long counter;

    /** Pointer to the demand. Only delivery operationplans have this field
      * set. The field is NULL for all other operationplans. */
    Demand *lt;

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

    /** Single linked list of flowplans. */
    slist<FlowPlan*> flowplans;

    /** Single linked list of loadplans. */
    slist<LoadPlan*> LoadPlans;

    /** Pointer to the previous operationplan. Operationplans are chained in
      * a doubly linked list for each operation. 
      * @see next 
      */
    OperationPlan* prev;

    /** Pointer to the next operationplan. Operationplans are chained in
      * a doubly linked list for each operation. 
      * @see prev
      */
    OperationPlan* next;
};


/** Models an operation that takes a fixed amount of time, independent
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
    void setDuration(TimePeriod t) {if (t>=TimePeriod(0L)) duration = t;}

    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

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
    void setOperationPlanParameters(OperationPlan*, float, Date, Date) const;

  private:
    /** Stores the lengh of the Operation. */
    TimePeriod duration;
};


/** Models an operation whose duration is the sum of a constant time, plus
  * a cetain time per unit. */
class OperationTimePer : public Operation
{
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
    void setOperationPlanParameters
      (OperationPlan*, float, Date, Date) const;

    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

  private:
    /** Constant part of the operation time. */
    TimePeriod duration;

    /** Variable part of the operation time. */
    TimePeriod duration_per;
};


/** Represents a routing operation, i.e. an operation consisting of multiple,
  * sequential sub-operations. */
class OperationRouting : public Operation
{
  public:
    /** Constructor. */
    explicit OperationRouting(const string& c) : Operation(c) {};

    /** Destructor. */
    ~OperationRouting();

    /** Adds a new steps to routing at the start of the routing. */
    void addStepFront(Operation *o)
    {
      if(!o) return;
      steps.push_front(o);
      o->addSuperOperation(this);
    }

    /** Adds a new steps to routing at the end of the routing. */
    void addStepBack(Operation *o)
    {
      if(!o) return;
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
    void setOperationPlanParameters(OperationPlan*, float, Date, Date) const;

    void beginElement(XMLInput& , XMLElement&  );
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    /** Return a list of all sub-operation_plans. */
    virtual const Operationlist& getSubOperations() {return steps;}

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual OperationPlan* createOperationPlan (float q, Date s, Date e, 
      Demand* l, bool updates_okay = true, OperationPlan* ow = NULL, 
      unsigned long i = 0, bool makeflowsloads=true) const;

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

  private:
    Operationlist steps;
};


class OperationPlanRouting : public OperationPlan
{
    friend class OperationRouting;
  private:
    list<OperationPlan*> step_opplans;
    OperationPlanRouting() {};
  public:
    /** Updates the end date of the operation. Slack can be introduced in the
      * routing by this method, i.e. the sub operationplans are only moved if
      * required to meet the end date. */
    void setEnd(Date d);

    /** Updates the start date of the operation. Slack can be introduced in the
      * routing by this method, i.e. the sub operationplans are only moved if
      * required to meet the start date. 
      */
    void setStart(Date d);
    virtual void update();
    void addSubOperationPlan(OperationPlan* o);
    ~OperationPlanRouting();
    void setQuantity(float f, bool roundDown=false);
    void eraseSubOperationPlan(OperationPlan* o);

    /** Initializes the operationplan and all steps in it. 
      * If no step operationplans had been created yet this method will create
      * them. During this type of creation the end date of the routing 
      * operationplan is used and step operationplans are created. After the 
      * step operationplans are created the start date of the routing will be 
      * equal to the start of the first step.
      */
    void initialize();
    void updateProblems();
};



/** This class represents a choice between multiple operations. The
  * alternates are sorted in order of priority.
  */
class OperationAlternate : public Operation
{
  public:
    /** Constructor. */
    explicit OperationAlternate(const string& c) : Operation(c) {};

    /** Destructor. */
    ~OperationAlternate();

    /** Add a new alternate operation. The higher the priority value, the more
      * important this alternate operation is. */
    void addAlternate(Operation* o, float prio = 1.0f);

    /** Removes an alternate from the list. */
    void removeSubOperation(Operation *);

    /** Returns the priority of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     null or when it is not a sub-operation of this alternate.
      */
    float getPriority(Operation* o) const;

    /** Updates the priority of a certain suboperation.
      * @exception LogicException Generated when the argument operation is
      *     not null and not a sub-operation of this alternate.
      */
    void setPriority(Operation* o, float f);

    /** A operation of this type enforces the following rules on its
      * operationplans:
      *  - Very simple, call the method with the same name on the alternate
      *    suboperationplan.
      * @see Operation::setOperationPlanParameters
      */
    void setOperationPlanParameters(OperationPlan*, float, Date, Date) const;

    void beginElement (XMLInput&, XMLElement&);
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}
    virtual const Operationlist& getSubOperations() {return alternates;}

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual OperationPlan* createOperationPlan (float q, Date s, Date e, 
      Demand* l, bool updates_okay = true, OperationPlan* ow = NULL, 
      unsigned long i = 0, bool makeflowsloads=true) const;

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

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


/** This class subclasses the OperationPlan class for operations of type
  * OperationAlternate. Such operationplans need an extra field to point to
  * the suboperationplan.
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
    ~OperationPlanAlternate();
    void addSubOperationPlan(OperationPlan* o);
    void setQuantity(float f, bool roundDown=false);
    void eraseSubOperationPlan(OperationPlan* o);
    void setEnd(Date d);
    void setStart(Date d);
    void update();

    /** Initializes the operationplan. If no suboperationplan was created
      * yet this method will create one, using the highest priority alternate.
      */
    void initialize();
};


/** Models an operation which has to use different operations depending
  * on the dates. */
class OperationEffective : public Operation
{
  public:
    /** Constructor. */
    explicit OperationEffective(const string& s)
      : Operation(s), cal(NULL), useEndDate(true) {}

    /** Returns the calendar that specifies which operation to use during
      * which time period. */
    CalendarOperation* getCalendar() const {return cal;}

    /** Updates the calendar. Existing operation plans are not automatically
      * getting updated to fit the new calendar. */
    void setCalendar(CalendarOperation* t) {cal = t;}

	  /** Returns whether the end or the start date of operationplans is used
	  * to determine the effective operation. */
    bool getUseEndDate() const {return useEndDate;}

	  /** Updates whether the end or the start date of operationplans is used
	  * to determine the effective operation. */
	  void setUseEndDate(const bool b) {useEndDate = b;}

    void beginElement (XMLInput&, XMLElement&);
    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

    /** This is the factory method which creates all operationplans of the
      * operation.
      * @see Operation::createOperationPlan
      */
    virtual OperationPlan* createOperationPlan (float, Date, Date, Demand*,
        bool updates_okay=true, OperationPlan* = NULL, unsigned long i=0,
		    bool makeflowsloads=true) const;

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
    void setOperationPlanParameters
      (OperationPlan* opplan, float q, Date s, Date e) const;

  private:
    /** Stores the calendar. This calendar stores for each date in the horizon
	  * which operation is to be used. */
    CalendarOperation* cal;

    /** Specifies whether to use the start or the end date as the date to use.
      * The default is to use the end date.
      */
    bool useEndDate;
};


/** This class subclasses the OperationPlan class for operations of type
  * OperationEffective. Such operationplans need an extra field to point to
  * the suboperationplan.
  * @see OperationPlan, OperationEffective
  */
class OperationPlanEffective : public OperationPlan
{
  friend class OperationEffective;

  private:
    OperationPlan* effopplan;

  public:
    OperationPlanEffective() : effopplan(NULL) {};
    ~OperationPlanEffective();
    void addSubOperationPlan(OperationPlan* o);
    void setQuantity(float f, bool roundDown=false);
    void eraseSubOperationPlan(OperationPlan* o);
    OperationPlan* getSubOperationPlan() {return effopplan;}
    void setEnd(Date d);
    void setStart(Date d);
    void update();
    void initialize();
};


/** A buffer represents a combination of a item and location. It is the 
  * entity for keeping modeling inventory.
  * A synonyme is SKU or stock-keeping-unit.
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
      hidden(false), producing_operation(NULL), consuming_operation(NULL), 
      loc(NULL), it(NULL), min_cal(NULL), max_cal(NULL) {}

    /** Returns the operation that is used to supply extra supply into this
      * buffer. */
    Operation* getProducingOperation() const {return producing_operation;}

    /** Updates the operation that is used to supply extra supply into this
      * buffer. */
    void setProducingOperation(Operation* o)
      {producing_operation = o; setChanged();}

    /** Returns the operation that is used to consume more material from this
      * buffer. */
    Operation* getConsumingOperation() const {return consuming_operation;}

    /** Updates the operation that is used to consume more material from this
      * buffer. */
    void setConsumingOperation(Operation* o)
      {consuming_operation = o; setChanged();}

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
    CalendarFloat *getMinimum() const {return min_cal;}

    /** Returns a pointer to a calendar for storing the maximum inventory
      * level. */
    CalendarFloat *getMaximum() const {return max_cal;}

    /** Updates the minimum inventory target for the buffer. */
    void setMinimum(const CalendarFloat *cal);

    /** Updates the minimum inventory target for the buffer. */
    void setMaximum(const CalendarFloat *cal);

    virtual void beginElement(XMLInput&, XMLElement&);
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void writeProfile(XMLOutput*, Calendar* = NULL) const;
    virtual void endElement(XMLInput&, XMLElement&);

    /** Destructor. */
    virtual ~Buffer();

    /** Returns the available material on hand immediately after the
      * given date.
      */
    double getOnHand(Date) const;

    /** Update the on-hand inventory at the start of the planning horizon. */
    void setOnHand(float f);

    /** Returns minimum or maximum available material on hand in the given
      * daterange. The third parameter specifies whether we return the
      * minimum (which is the default) or the maximum value.
      * The computation is INclusive the start and end dates.
      */
    double getOnHand(Date, Date, bool min = true) const;

    /** Returns a reference to the list of all flows of this buffer. */
    const flowlist& getFlows() const {return flows;}
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    /** Returns a reference to the list of all flow plans of this buffer. */
    const flowplanlist& getflowplans() {return flowplans;}

    /** Return the flow that is associates a given operation with this
      * buffer. Returns NULL is no such flow exists. */
    Flow* findFlow(const Operation* o) const {return flows.find(o);}

    /** Deletes all operationplans consuming from or producing from this
      * buffer. The boolean parameter controls whether we delete also locked
      * operationplans or not.
      */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    virtual void updateProblems();

    void setHidden(bool b) {if (hidden!=b) setChanged(); hidden = b;}
    bool getHidden() const {return hidden;}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

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

    /** This is the operation used to consume material from this buffer. */
    Operation *consuming_operation;

    /** Location of this buffer. This field is only used as information. The
      * default is NULL. */
    Location* loc;

    /** Item being stored in this buffer. The default is NULL. */
    Item* it;

    /** Points to a calendar to store the minimum inventory level. The default
      * value is NULL, resulting in a constant minimum level of 0. */
    CalendarFloat *min_cal;

    /** Points to a calendar to store the minimum inventory level. The default
      * value is NULL, resulting in a buffer without excess inventory problems.
      */
    CalendarFloat *max_cal;
};


class BufferDefault : public Buffer
{
  public:
    explicit BufferDefault(const string& str) : Buffer(str) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This class represents a material buffer with an infinite supply of extra
  * material. In other words, it never constrains the plan and it doesn't
  * propagate requirements upstream.
  */
class BufferInfinite : public Buffer
{
  public:
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual const MetaData& getType() const {return metadata;}
    explicit BufferInfinite(const string& c) : Buffer(c)
      {setDetectProblems(false);}
    static const MetaClass metadata;
};


/** This class represents a material buffer where a replenishment is triggered
  * whenever the inventory drops below the minimum level. The buffer is then
  * replenished to the maximum inventory level.
  */
class BufferMinMax : public Buffer
{
  public:
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual const MetaData& getType() const {return metadata;}
    explicit BufferMinMax(const string& c) : Buffer(c) {}
    static const MetaClass metadata;
};


/** This class defines a material flow to/from a buffer, linked with an
  * operation. This default implementation plans the material flow at the
  * start of the operation.
  * @todo make the flow class really abstract
  */
class Flow : public Object, public Association<Operation,Buffer,Flow>::Node,
  public Solvable
{
  public:
	  /** Destructor. */
    virtual ~Flow();

	  /** Constructor. */
    explicit Flow(Operation* o, Buffer* b, float q) :
      Association<Operation,Buffer,Flow>::Node(o,b,o->getFlows(),b->getFlows()),
      quantity(q) {validate(ADD);}

	  /** Returns the operation. */
    Operation* getOperation() const {return getPtrA();}

    /** Updates the operation of this flow. This method can be called only ONCE
      * for each flow. In case that doesn't suit you, delete the existing flow
      * and create a new one.
      */
    void setOperation(Operation* o) {if (!getPtrA()) setPtrA(o,o->getFlows());}

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
    void setBuffer(Buffer* b) {if (!getPtrB()) setPtrB(b,b->getFlows());}

	  /** A flow is considered hidden when either its buffer or operation 
	    * are hidden. */
	  bool getHidden() const
      {return getBuffer()->getHidden() || getOperation()->getHidden();}

    /** Returns the date to be used for this flowplan. */
	  virtual const Date& getFlowplanDate(const OperationPlan* o) const 
	    {return o->getDates().getStart();}

	  virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void beginElement(XMLInput&, XMLElement&);
    void endElement(XMLInput&, XMLElement&);

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

  protected:    
    /** Default constructor. */
    explicit Flow() : quantity(0.0f) {}

  private:
    /** Verifies whether a flow meets all requirements to be valid. */
    void validate(Action action);

	  /** Quantity of the flow. */
    float quantity;
};


/** This class defines a material flow to/from a buffer, linked with an
  * operation. This subclass represents a flow that is at the start date of 
  * the operation.
  */
class FlowStart : public Flow
{
  public:
	  /** Constructor. */
	  explicit FlowStart(Operation* o, Buffer* b, float q) : Flow(o,b,q) {}

    /** This constructor is called from the plan begin_element function. */
    explicit FlowStart() {}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This class defines a material flow to/from a buffer, linked with an
  * operation. This subclass represents a flow that is at end date of the 
  * operation.
  */
class FlowEnd : public Flow
{
  public:
	  /** Constructor. */
	  explicit FlowEnd(Operation* o, Buffer* b, float q) : Flow(o,b,q) {}

    /** This constructor is called from the plan begin_element function. */
    explicit FlowEnd() {}

    /** Returns the date to be used for this flowplan. */
	  const Date& getFlowplanDate(const OperationPlan* o) const
	  {return o->getDates().getEnd();}

	  virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** A flowplan represents a planned material flow in or out of a buffer. 
  * Flowplans are owned by operationplans, which manage a container to store 
  * them. 
  */
class FlowPlan : public TimeLine<FlowPlan>::EventChangeOnhand
{
  private:
    Flow *fl;
    OperationPlan *oper;

  public:
    /** Constructor. */
    explicit FlowPlan(OperationPlan*, const Flow*);

    /** Returns the Flow of which this is an planning instance. */
    Flow* getFlow() const {return fl;}

    /** Returns the operationplan owning this flowplan. */
    OperationPlan* getOperationPlan() const {return oper;}

    virtual ~FlowPlan()
      {fl->getBuffer()->setChanged(); fl->getBuffer()->flowplans.erase(this);}

    /** Updates the quantity of the flowplan by changing the quantity of the
      * operationplan owning this flowplan.
      * The boolean parameter is used to control whether to round up or down
      * in case the operation quantity must be a multiple.
      */
    void setQuantity(float qty, bool b=false)
    {oper->setQuantity(qty / fl->getQuantity(), b);}

    /** Returns the date of the flowplan. */
	const Date& getDate() const {return fl->getFlowplanDate(oper);} 

	void update();

    /** Returns whether the flowplan needs to be serialized. This is
      * determined by looking at whether the flow is hidden or not. */
    bool getHidden() const {return fl->getHidden();}

    /** Verifies whether the flowplan is properly in-line with its owning
      * operationplan. */
    bool check();
};


/** This class represents a workcentre, a physical or logical representation
  * of capacity.
  */
class Resource : public HasHierarchy<Resource>,
  public HasLevel, public Plannable, public HasDescription
{
    friend class Load;
    friend class LoadPlan;

  public:
    /** Constructor. */
    explicit Resource(const string& str) : HasHierarchy<Resource>(str), 
      max_cal(NULL), loc(NULL), hidden(false) {};

    /** Destructor. */
    virtual ~Resource();

    /** Returns the size of of the resource. */
    Calendar* getSize() const {return max_cal;}

    /** Updates the size of a resource. */
    void setMaximum(CalendarFloat* c);

    /** Return a pointer to the maximum capacity profile. */
    CalendarFloat* getMaximum() const {return max_cal;}

    typedef Association<Operation,Resource,Load>::ListB loadlist;
    typedef TimeLine<LoadPlan> loadplanlist;

    /** Returns a reference to the list of loadplans. */
    loadplanlist& getLoadPlans() {return loadplans;}

    /** Returns a constant reference to the list of loads. It defines
      * which operations are using the resource.
      */
    const loadlist& getLoads() const {return loads;}

    /** Return the load that is associates a given operation with this
      * resource. Returns NULL is no such load exists. */
    Load* findLoad(const Operation* o) const {return loads.find(o);}

    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);
    void beginElement (XMLInput&, XMLElement&);

    /** Returns the location of this resource. */
    Location* getLocation() const {return loc;}

    /** Updates the location of this resource. */
    void setLocation(Location* i) {loc = i;}

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    /** Deletes all operationplans loading this resource. The boolean parameter
      * controls whether we delete also locked operationplans or not.
      */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    /** Recompute the problems of this resource. */
    virtual void updateProblems();

    void setHidden(bool b) {if (hidden!=b) setChanged(); hidden = b;}
    bool getHidden() const {return hidden;}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

  private:
    /** This calendar is used to updates to the resource size. */
    CalendarFloat* max_cal;

    /** Stores the collection of all loadplans of this resource. */
    loadplanlist loadplans;

    /** This is a list of all load models that are linking this resource with
      * operations. */
    loadlist loads;

    /** A pointer to the location of the resource. */
    Location* loc;

    /** Specifies whether this resource is hidden for serialization. */
    bool hidden;
};


class ResourceDefault : public Resource
{
  public:
    explicit ResourceDefault(const string& str) : Resource(str) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This class represents a resource that'll never have any capacity shortage.
  */
class ResourceInfinite : public Resource
{
  public:
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual const MetaData& getType() const {return metadata;}
    explicit ResourceInfinite(const string& c) : Resource(c)
      {setDetectProblems(false);}
    static const MetaClass metadata;
};


/** This class links a resource to a certain operation. */
class Load 
  : public Object, public Association<Operation,Resource,Load>::Node,
    public Solvable
{
    friend class Resource;
    friend class Operation;

  public:
    explicit Load(Operation* o, Resource* r, float u) :
    Association<Operation,Resource,Load>::Node(o,r,o->getLoads(),r->getLoads()),
      usage(u)
      {validate(ADD);}
    ~Load();
    Operation* getOperation() const {return getPtrA();}
    void setOperation(Operation* o) {if (!getPtrA()) setPtrA(o,o->getLoads());}
    Resource* getResource() const {return getPtrB();}
    void setResource(Resource* r) {if (!getPtrB()) setPtrB(r,r->getLoads());}
    float getUsageFactor() const {return usage;}
    void setUsageFactor(float f) {usage = f;}
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void beginElement(XMLInput&, XMLElement&);
    void endElement(XMLInput&, XMLElement&);
    bool getHidden() const
      {return getResource()->getHidden() || getOperation()->getHidden();}
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

  private:
    /** This private constructor is called from the plan begin_element
      * function. */
    Load() : usage(1.0f) {}

    /** This method is called to check the validity of the object. It will
      * delete the invalid loads: be careful with the 'this' pointer after
      * calling this method!
      */
    void validate(Action action);

  private:
    float usage;
};


/** An item defines the products being planned, sold, stored and/or 
  * manufactured. Buffers and demands have a reference an item. 
  */
class Item
  : public HasHierarchy<Item>, public HasDescription, public Object
{
  public:
    /** Constructor. Don't use this directly! */
    explicit Item(const string& str) 
      : HasHierarchy<Item> (str), deliveryOperation(NULL) {}

    /** Returns the delivery operation. */
    Operation* getDelivery() const {return deliveryOperation;}

    /** Updates the delivery operation.<br>
      * If some demands have already been planned using the old delivery
      * operation they are left untouched and won't be replanned.
      */
    void setDelivery(Operation* o) {deliveryOperation = o;}

    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);
    void beginElement (XMLInput&, XMLElement&);

    /** Destructor. */
    virtual ~Item();

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

  private:
    /** This is the operation used to satisfy a demand for this Item. */
    Operation* deliveryOperation;
};


class ItemDefault : public Item
{
  public:
    explicit ItemDefault(const string& str) : Item(str) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This is the top class of the complete model.
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

    /** A file where output is directed to. */
    ofstream log;

    /** The name of the log file. */
    string logfilename;

    /** This is the default bucketization of the plan. */
    Calendar* def_Calendar;

    /** Pointer to the singleton plan object. */
    static Plan* thePlan;

    /** The only constructor of this class is made private. An object of this
      * class is created by the instance() member function.
      */
    Plan() : cur_Date(Date::now()), def_Calendar(NULL) {}

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
    ~Plan();

    /** Returns the plan name. */
    const string& getName() const {return name;}

    /** Updates the plan name. */
    void setName(const string& s) {name = s;}

    /** Returns the default Bucketization Calendar of the plan. */
    Calendar* getCalendar() const {return def_Calendar;}

    /** Updates the default bucketization. */
    void setCalendar(Calendar* h) {def_Calendar = h;}

    /** Returns the current Date of the plan. */
    const Date & getCurrent() const {return cur_Date;}

    /** Updates the current date of the plan. This method can be relatively
      * heavy in a plan where operationplans already exist, since the
      * detection for BeforeCurrent problems needs to be rerun.
      */
    void setCurrent(Date);

    /** Returns the description of the plan. */
    const string& getDescription() const {return descr;}

    /** Updates the description of the plan. */
    void setDescription(const string& str) {descr = str;}

    /** Returns the name of the logfile. */
    const string& getLogFile() const {return logfilename;}

    /** Updates the filename for logging error messages and warnings.
      * The file is also opened for writing and the standard output and
      * standard error output streams are redirected to it.
      */
    void setLogFile(string x);

    /** This method writes out the model information. Depending on a flag in
      * the XMLOutput object a complete model is written, or only the
      * dynamic plan information.
      * @see CommandSave, CommandSavePlan
      */
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, XMLElement&  pElement);
    void beginElement(XMLInput& pIn, XMLElement&  pElement);

    virtual void updateProblems() {};

    /** This method basically solves the whole planning problem. */
    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    /** This method gives a summary of all models being stored in the plan
      * with a summary of their memory use.
      * The memory size esimate is only an approximation, since quite a few
      * things are not taken into account and only roughly guessed:
      *   - The subclasses may use extra data fields, while we measure only
      *     the base class.
      *   - Some size parameters are hard-coded in the script. Depending on
      *     your platform and STL implementation different constants may
      *     need to be used in the file plan.cpp.
      *   - Additional memory will be required during certain commands, e.g.
      *     solving the model, saving to a file, etc...
      * The implementation of this class requires in-depth understanding of
      * the data structures of the classes it is measuring. Strictly speaking
      * this is against the principles of object oriented programming, but
      * I estimated this to be a better/easier/good enough approach.
      * The alternative would be to add additional sizing methods in all
      * classes...
      */
    void size() const;

    const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;
};


/** This command is used for reading XML input. The input comes either from
  * a flatfile, or from the standard input. */
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
    void execute();

    void endElement(XMLInput& pIn, XMLElement& pElement);

    string getDescription() const
    {
      if (filename.empty())
        return "parsing xml input from standard input";
      else
        return "parsing xml input from file '" + filename + "'";
    }
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

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


/** This command is used for reading XML input from a certain string. */
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
    void execute();
    void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const {return "parsing xml input string";}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;

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


/** This command writes the complete model to an XML-file, both the static model
  * (i.e. items, locations, buffers, resources, calendars, etc...) and the
  * dynamic data (i.e. the actual plan including the operation_plans, demand,
  * problems, etc...).
  * The data is written by the execute() function.
  * @see CommandSavePlan
  */
class CommandSave : public Command
{
  public:
    CommandSave(const string& v = "plan.out") : filename(v){};
    virtual ~CommandSave() {};
    string getFileName() const {return filename;}
    void setFileName(const string& v) {filename = v;}
    void execute();
    void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const
      {return "saving the complete model into file '" + filename + "'";}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
  private:
    string filename;
};


/** This command writes the dynamic part of the plan to an  text file. This
  * covers the buffer flowplans, operation_plans, resource loading, demand,
  * problems, etc...
  * The main use of this function is in the test suite: a simple text file
  * comparison allows us to identify changes quickly. The output format is
  * only to be seen in this context of testing, and is not intended to be used
  * as an official method for publishing plans to other systems.
  * The data file is written by the execute function.
  * @see CommandSave
  */
class CommandSavePlan : public CommandSave
{
  public:
    CommandSavePlan(const string& v = "plan.out") : CommandSave(v) {};
    void execute();
    string getDescription() const
      {return "saving the plan into text file '" + getFileName() + "'";}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This command prints out the model size to the standard output. */
class CommandPlanSize : public Command
{
  public:
    CommandPlanSize() {};
    void execute() {Plan::instance().size();}
    void undo() {}
    bool undoable() const {return true;}
    string getDescription() const {return "printing the model size";}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This command deletes part of the model or the plan from memory.
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
  */
class CommandErase : public Command
{
  public:
    CommandErase() : deleteStaticModel(false) {};
    void execute();
    void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const
    {
      return deleteStaticModel ? "Erasing the model" : "Erasing the plan";
    }
    bool getDeleteStaticModel() const {return deleteStaticModel;}
    void setDeleteStaticModel(bool b) {deleteStaticModel = b;}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
  private:
    /** Flags whether to delete the complete static model or only the
      * dynamic plan information. */
    bool deleteStaticModel;
};


/** Represents the (independent) demand in the system. 
  * It can represent a customer order or a forecast.
  */
class Demand
  : public HasHierarchy<Demand>, public Plannable, public HasDescription
{
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
    virtual void setQuantity(float);

    /** Returns the priority of the demand. Lower numbers indicate a
      * higher priority level.
      */
    int getPriority() const {return prio;}

    /** Updates the due date of the demand. Lower numbers indicate a
      * higher priority level.
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
    Operation* getDeliveryOperation() const;

    /** Returns the cluster which this demand belongs to. */
    int getCluster() const
      {Operation* o = getDeliveryOperation(); return o ? o->getCluster() : 0;}

    /** Updates the operation being used to plan the demand. */
    virtual void setOperation(Operation* o) {oper=o; setChanged();}

    /** Returns the delivery operationplan list. */
    const OperationPlan_list& getDelivery() const;

    /** Adds a delivery operationplan for this demand. If the policy
      * SINGLEDELIVERY is set, any previous delivery operationplan is
      * unregistered first.
      */
    void addDelivery(OperationPlan *o);

    /** Removes a delivery operationplan for this demand. */
    void removeDelivery(OperationPlan *o);

    /** Deletes all delivery operationplans of this demand. The boolean
      * parameter controls whether we delete also locked operationplans or not.
      */
    void deleteOperationPlans(bool deleteLockedOpplans = false);

    /** Returns the due date of the demand. */
    Date getDue() const {return dueDate;}

    /** Updates the due date of the demand. */
    virtual void setDue(Date d) {dueDate = d; setChanged();}

    /** Returns the customer. */
    Customer* getCustomer() const { return cust; }

    /** Updates the customer. */
    void setCustomer(Customer* c) { cust = c; setChanged(); }

    /** Returns the total amount that has been planned. */
    float getPlannedQuantity() const;

    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    virtual void endElement(XMLInput& , XMLElement&  );
    virtual void beginElement (XMLInput& , XMLElement&  );

    virtual void solve(Solver &s, void* v = NULL) {s.solve(this,v);}

    /** Returns true if this demand is allowed to be planned late.
      * If so, the system will try to satisfy the demand at a later date.
      * If not, only a delivery at the requested date is allowed.
      * @see planShort
      */
    bool planLate() const {return !policy.test(2);}

    /** Returns true if this demand isn't allowed to be planned late.
      * If not, only a delivery at the requested date is allowed.
      * @see planLate
      */
    bool planShort() const {return policy.test(2);}

    /** Returns true if multiple delivery operationplans for this demand are
      * allowed.
      * @see planSingleDelivery
      */
    bool planMultiDelivery() const {return !policy.test(3);}

    /** Returns true if only a single delivery operationplan is allowed for this
      * demand.
      * @see planMultiDelivery
      */
    bool planSingleDelivery() const {return policy.test(3);}

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
    virtual void addPolicy(const string&);

    /** Recompute the problems. */
    virtual void updateProblems();

    /** Specifies whether of not this demand is to be hidden from
      * serialization. The default value is false. */
    void setHidden(bool b) {policy.set(5,b);}

    /** Returns true if this demand is to be hidden from serialization. */
    bool getHidden() const {return policy.test(5);}

    virtual const MetaData& getType() const {return metadata;}
    static const MetaCategory metadata;

  private:
    /** Requested item. */
    Item *it;

    /** Delivery Operation. Can be left NULL, in which case the delivery
      * operation can be specified on the requested item. */
    Operation *oper;

    /** Customer creating this demand. */
    Customer *cust;

    /** Requested quantity. Only positive numbers are allowed. */
    float qty;

    /** Priority. Lower numbers indicate a higher priority level.*/
    int prio;

    /** Due date. */
    Date dueDate;

    /** Effiently stores a number of different policy values for the demand.
      * The default value for each policy bit is 0.
      * The bits have the following meaning:
      *  - 0: Unused
      *  - 1: Unused
      *  - 2: Late (false) or Short (true)
      *  - 3: Multi (false) or Single (true) delivery
      *  - 4: Unused
      *  - 5: Hidden
      */
    bitset<6> policy;

    /** A list of operation plans to deliver this demand. */
    OperationPlan_list deli;
};


class DemandDefault : public Demand
{
  public:
    explicit DemandDefault(const string& str) : Demand(str) {}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
};


/** This class represents the resource capacity of an operation_plan.
  * For both the start and the end date of the operation_plan, a load_plan
  * object is created. These are then inserted in the timeline structure
  * associated with a resource.
  */
class LoadPlan : public TimeLine<LoadPlan>::EventChangeOnhand
{
  public:
    /** Public constructor.
      * This constructor constructs the starting loadplan and will
      * also call a private constructor to creates the ending loadplan.
      * In other words, a single call to the constructor will create
      * two loadplan objects.
      */
    explicit LoadPlan(OperationPlan*, Load*);
    const Date & getDate() const 
    {
      if(start_or_end == START) return oper->getDates().getStart(); 
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
    void update();
    bool getHidden() const {return ld->getHidden();}

    /** Validates the consistency of the loadplan. */
    bool check();

  private:
    /** Private constructor. It is called from the public constructor.
      * The public constructor constructs the starting loadplan, while this
      * constructor creates the ending loadplan.
      */
    LoadPlan(OperationPlan*, Load*, LoadPlan*);

    /** This type is used to differentiate loadplans aligned with the START date
      * or the END date of operationplan. */
    enum type {START, END};

    /** Is this loadplan a starting one or an ending one. */
    type start_or_end;

    /** A pointer to the load model. */
    Load *ld;

    /** A pointer to the operation_plan owning this load_plan. */
    OperationPlan *oper;
};


/** A problem of this class is created when an operationplan is being
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;
};


/** A problem of this class is created when an operationplan is being
  * planned its fence, i.e. it starts 1) before the "current" date of
  * the plan plus the release fence of the operation and 2) after the
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;
};


/** A problem of this class is created when the sequence of two
  * operationplans isn't respected.
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
      {return DateRange(opplan2->getDates().getStart(),
                        opplan1->getDates().getEnd());}
    OperationPlan* getFirstOperationPlan() const {return opplan1;}
    OperationPlan* getSecondOperationPlan() const {return opplan2;}

    /** Return a reference to the metadata structure. */
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;

  private:
    /** Pointers to the operationplans which violate the sequence.
      * opplan1 is expected to finish before opplan2 starts. */
    OperationPlan *opplan1, *opplan2;
};


/** A Problem of this class is created in the model when a new demand is
  * brought in the system, but it hasn't been planned yet.
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;
};


/** A problem of this class is created when a demand is planned later than
  * the accepted tolerance after its due date.
  */
class ProblemLate : public Problem
{
  public:
    string getDescription() const;
    bool isFeasible() {return true;}
    float getWeight() {return 1.0f;}
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;
};


/** A problem of this class is created when a demand is planned earlier than
  * the accepted tolerance before its due date.
  */
class ProblemEarly : public Problem
{
  public:
    string getDescription() const;
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;
};


/** A problem of this class is created when a demand is planned for less than 
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;
};


/** A problem of this class is created when a demand is planned for more than
  * the requested quantity.
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;
};


/** A problem of this class is created when an OperationPlan is planned
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;

  private:
    /** This is the time that is allowed between the lpst date and the start
      * date of an operation before a problem is created.
      * The default value is 0. */
    static TimePeriod allowedLate;
};


/** A problem of this class is created when a demand is planned earlier than
  * the accepted tolerance before its epst date.
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
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;

  private:
    /** This is the time that is allowed between the epst date and the start
      * date of an operation before a problem is created.
      * The default value is 0. */
    static TimePeriod allowedEarly;
};


/** A problem of this class is created when a resource is being overloaded
  * during a certain period of time.
  */
class ProblemCapacityOverload : public Problem
{
  public:
    string getDescription() const;
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    ProblemCapacityOverload(Resource* r, DateRange d, float q)
      : Problem(r), qty(q), dr(d) {addProblem();}
    ~ProblemCapacityOverload() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Resource* getResource() const {return dynamic_cast<Resource*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;

  private:
    /** Overload quantity. */
    float qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** A problem of this class is created when a resource is loaded below its
  * minimum during a certain period of time.
  */
class ProblemCapacityUnderload : public Problem
{
  public:
    string getDescription() const;
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    ProblemCapacityUnderload(Resource* r, DateRange d, float q)
      : Problem(r), qty(q), dr(d) {addProblem();}
    ~ProblemCapacityUnderload() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Resource* getResource() const {return dynamic_cast<Resource*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;

  private:
    /** Underload quantity. */
    float qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** A problem of this class is created when a buffer is having a material
  * shortage during a certain period of time.
  */
class ProblemMaterialShortage : public Problem
{
  public:
    string getDescription() const;
    bool isFeasible() {return false;}
    float getWeight() {return 1.0f;}
    ProblemMaterialShortage(Buffer* b, DateRange d, float q)
      : Problem(b), qty(q), dr(d) {addProblem();}
    ~ProblemMaterialShortage() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Buffer* getBuffer() const {return dynamic_cast<Buffer*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;

  private:
    /** Shortage quantity. */
    float qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** A problem of this class is created when a buffer is carrying too much
  * material during a certain period of time.
  */
class ProblemMaterialExcess : public Problem
{
  public:
    string getDescription() const;
    bool isFeasible() {return true;}
    float getWeight() {return 1.0f;}
    ProblemMaterialExcess(Buffer* b, DateRange d, float q)
      : Problem(b), qty(q), dr(d) {addProblem();}
      ~ProblemMaterialExcess() {removeProblem();}
    const DateRange getDateRange() const {return dr;}
    Buffer* getBuffer() const {return dynamic_cast<Buffer*>(getOwner());}

    /** Return a reference to the metadata structure. */
    const MetaData& getType() const {return metadata;}

    /** Storing metadata on this class. */
    static const MetaClass metadata;

  private:
    /** Excess quantity. */
    float qty;

    /** The daterange of the problem. */
    DateRange dr;
};


/** This class represents the command linked with the creation of an
  * operationplan. The operationplan will have its load and loadplans created
  * when the command is created. It is assigned an id and added to the list of
  * all operationplans when the command is committed.
  */
class CommandCreateOperationPlan : public Command
{
  public:
    CommandCreateOperationPlan
      (Operation* o, float q, Date d1, Date d2, Demand* l, 
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
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
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


/** This class represents the command of moving an operationplan to a new date.
  * @todo Moving in a routing operation can't be undone with the current
  * implementation! The command will need to store all original dates of
  * the suboperationplans...
  */
class CommandMoveOperationPlan : public Command
{
  public:
    /** Constructor.
      * Unlike the other commands the constructor already executes the change.
      * @param opplanptr Pointer to the operationplan being moved.
      * @param newDate New date of the operationplan.
      * @param startOrEnd Specifies whether the new date is the start (=false)
      * or end date (=true). By default we use the end date.
      */
    CommandMoveOperationPlan
      (OperationPlan* opplanptr, Date newDate, bool startOrEnd=true);
    void execute() 
      {if (!opplan) return; opplan->setAllowUpdates(true); opplan=NULL;}
    void undo();
    bool undoable() const {return true;}
    ~CommandMoveOperationPlan() {if (opplan) undo();}
    OperationPlan *getOperationPlan() const {return opplan;}
    virtual const MetaData& getType() const {return metadata;}
    static const MetaClass metadata;
    string getDescription() const;
    /** Set another date for the operation.
      * @param newdate New start- or end date.
      */
    void setDate(Date newdate);

  private:
    /** This is a pointer to the operation_plan being moved. */
    OperationPlan *opplan;

    /** This flag specifies whether we keep the new date is a new start or a
      * new end date for the operation_plan. */
    bool use_end;

    /** This is the start- or enddate of the operation_plan before its move. */
    Date originaldate;
};


/** This class models a iterator that walks over all available HasProblem
  * entities.
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
    explicit EntityIterator(unsigned short i) : type(i) {}

    /** Destructor. */
    ~EntityIterator();

    /** Pre-increment operator. */
    EntityIterator& operator++();

    bool operator != (const EntityIterator& t) const;
    bool operator == (const EntityIterator& t) const {return !(*this != t);}
    HasProblems* operator*() const;
    HasProblems* operator->() const;
};


/** This class models an STL-like iterator that allows us to iterate over
  * the named entities in a simple and safe way.<br>
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
    const_iterator& operator++();
    bool operator != (const const_iterator& t) const {return iter!=t.iter;}
    bool operator == (const const_iterator& t) const {return iter==t.iter;}
    Problem* operator*() const {return iter;}
    Problem* operator->() const {return iter;}
};


}   // End namespace

#endif
