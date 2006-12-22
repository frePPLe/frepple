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
 * under the terms of the GNU Lesser General Public License as Objecthed   *
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

/** @file utils.h
  * @brief Header file for auxilary classes.
  */

#ifndef UTILS_H
#define UTILS_H

#include <iostream>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <ctime>
#include <assert.h>

// We want to use singly linked lists, but these are not part of the C++
// standard though. Sigh...
#ifdef HAVE_EXT_SLIST
// Singly linked lists as extension: gcc 3.x
#include <ext/slist>
using namespace gnu_cxx;
#else
#ifdef HAVE_SLIST
// Singly linked lists available in std stl: gcc 2.95
#include <slist>
#else
// Not available: use a double linked list instead
#define slist list
#endif
#endif

// STL include files
#include <list>
#include <map>
#include <set>
#include <string>
#include <stack>
#include <vector>
#include <algorithm>
#include <bitset>
using namespace std;

// Configuration file created by autoconf
#ifdef HAVE_CONFIG_H
#undef PACKAGE_BUGREPORT
#undef PACKAGE_NAME
#undef PACKAGE_STRING
#undef PACKAGE_TARNAME
#undef PACKAGE_VERSION
#include <config.h>
#endif

// Header for multithreading
#if defined(MT) 
#if defined(HAVE_PTHREAD_H)
#include <pthread.h>
#elif defined(WIN32) 
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <process.h>
#else
#error Multithreading not supported on your platform
#endif
#endif

// For the disabled and ansi-challenged people...
#ifndef HAVE_STRNCASECMP
# ifdef _MSC_VER
#   define strncasecmp _strnicmp
# else
#   ifdef HAVE_STRNICMP
#     define strncasecmp(s1,s2,n) strnicmp(s1,s2,n)
#   else
      // Last resort. Force it through...
#     define strncasecmp(s1,s2,n) strnuppercmp(s1,s2,n)
#   endif
# endif
#endif

/** This constant defines what can still be considered as a rounding error. */
#define ROUNDING_ERROR   0.0001f

// Header files for the Xerces-c XML parser.
#define XERCES_NEW_IOSTREAMS
#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/sax2/SAX2XMLReader.hpp>
#include <xercesc/sax2/Attributes.hpp>
#include <xercesc/sax2/DefaultHandler.hpp>
#include <xercesc/framework/MemBufInputSource.hpp>
#include <xercesc/sax2/XMLReaderFactory.hpp>
#include <xercesc/util/XMLUni.hpp>
#include <xercesc/framework/MemBufInputSource.hpp>
#include <xercesc/framework/LocalFileInputSource.hpp>
#include <xercesc/framework/StdInInputSource.hpp>
#include <xercesc/framework/URLInputSource.hpp>
#include <xercesc/util/XMLException.hpp>
using namespace xercesc;

#undef DECLARE_EXPORT
#if defined(WIN32) && !defined(STATIC) && !defined(DOXYGEN_SHOULD_SKIP_THIS)
  #ifdef FREPPLE_CORE
    #define DECLARE_EXPORT __declspec (dllexport)
  #else
    #define DECLARE_EXPORT __declspec (dllimport)
  #endif
  #define MODULE_EXPORT  extern "C" __declspec (dllexport)
#else
  #define DECLARE_EXPORT
  #define MODULE_EXPORT extern "C" 
#endif


namespace frepple
{


// Forward declarations
class Object;
class XMLtag;
class XMLInput;

// Include the list of predefined tags
#include "tags.h"


/** This type defines what operation we want to do with the entity. */
enum Action 
{
  /** or A.<br>
    * Add an new entity, and report an error if the entity already exists. */
  ADD = 0,
  /** or C.<br>
    * Change an existing entity, and report an error if the entity doesn't 
    * exist yet. */
  CHANGE = 1, 
  /** or D.<br>
    * Delete an entity, and report an error if the entity doesn't exist. */
  REMOVE = 2, 
  /** or AC.<br>
    * Change an entity or create a new one if it doesn't exist yet.<br>
    * This is the default action. 
    */
  ADD_CHANGE = 3
};


/** Writes an action description to an output stream. */
inline ostream & operator << (ostream & os, const Action & d)
{
  switch (d)
  {
    case ADD: os << "ADD"; return os;
    case CHANGE: os << "CHANGE"; return os;
    case REMOVE: os << "REMOVE"; return os;
    case ADD_CHANGE: os << "ADD_CHANGE"; return os;
    default: assert(false); return os;
  }
}


/** This type defines the types of callback events possible. */
enum Signal 
{
  /** Adding a new entity. */
  SIG_ADD = 0,
  /** Before changing an entity. */
  SIG_BEFORE_CHANGE = 1,
  /** After changing an entity. */
  SIG_AFTER_CHANGE = 2,
  /** Deleting an entity. */
  SIG_REMOVE = 3 
};


/** Writes a signal description to an output stream. */
inline ostream & operator << (ostream & os, const Signal & d)
{
  switch (d)
  {
    case SIG_ADD: os << "ADD"; return os;
    case SIG_BEFORE_CHANGE: os << "BEFORE_CHANGE"; return os;
    case SIG_AFTER_CHANGE: os << "AFTER_CHANGE"; return os;
    case SIG_REMOVE: os << "REMOVE"; return os;
    default: assert(false); return os;
  }
}


/** This is the datatype used for hashing an XML-element to a numeric value. */
typedef unsigned int hashtype;


/** This class groups some functions used to interact with the operating 
  * system environment. 
  */
class Environment
{
  private:
    /** Stores the frepple home directory. */
    static DECLARE_EXPORT string home;

    /** Stores the number of processors on your machine.<br>
      * On windows it is automatically initialized to the value of the 
      * environment variable NUMBER_OF_PROCESSORS.
      */
    static DECLARE_EXPORT int processors;

  public:
    /** Return the home directory. */
    static const string getHomeDirectory() {return home;}

    /** Updates the home directory.
      * A runtime exception is thrown when the string points to an invalid 
      * directory. 
      */
    static void setHomeDirectory(const string);

    /** Returns the number of processors on your machine. */
    static int getProcessors() {return processors;}

    /** Updates the number of processors available on your machine. */
    static void setProcessors(int i) {if(i>=1) processors = i;}
};


//
// CUSTOM EXCEPTION CLASSES
//


/** An exception of this type is thrown when data errors are found.<br>
  * The normal handling of this error is to catch the exception and
  * continue execution of the rest of the program.<br>
  * When a DataException is thrown the object is expected to remain in
  * valid and consistent state.
  */
class DataException : public logic_error
{
  public:
    DataException(const char * c) : logic_error(c) {}
    DataException(const string s) : logic_error(s) {}
};


/** An exception of this type is thrown when the library gets in an
  * inconsistent state from which the normal course of action can't continue.
  * The normal handling of this error is to exit the program, and report the
  * problem. This exception indicates a bug in the program code.
  */
class LogicException: public logic_error
{
  public:
    LogicException(const char * c) : logic_error(c) {}
    LogicException(const string s) : logic_error(s) {}
};


/** An exception of this type is thrown when the library runs into problems
  * that are specific at runtime. These could either be memory problems,
  * threading problems, file system problems, etc...<br>
  * Errors of this type can be caught by the client applications and the
  * application can continue in most cases.<br>
  * This exception shouldn't be used for issueing warnings. Warnings should
  * simply be logged in the logfile and actions continue in some default way.
  */
class RuntimeException: public runtime_error
{
  public:
    RuntimeException(const char * c) : runtime_error(c) {}
    RuntimeException(const string s) : runtime_error(s) {}
};


//
// UTILITY CLASS "NON-COPYABLE"
//

/** Class NonCopyable is a base class. Derive your own class from NonCopyable
  * when you want to prohibit copy construction and copy assignment.<br>
  * Some objects, particularly those which hold complex resources like files
  * or network connections, have no sensible copy semantics.  Sometimes there
  * are possible copy semantics, but these would be of very limited usefulness
  * and be very difficult to implement correctly. Sometimes you're implementing
  * a class that doesn't need to be copied just yet and you don't want to 
  * take the time to write the appropriate functions.  Deriving from
  * noncopyable will prevent the otherwise implicitly-generated functions
  * (which don't have the proper semantics) from becoming a trap for other
  * programmers.<br>
  * The traditional way to deal with these is to declare a private copy
  * constructor and copy assignment, and then document why this is done. But
  * deriving from NonCopyable is simpler and clearer, and doesn't require
  * additional documentation.
  */
class NonCopyable
{
  protected:
    NonCopyable() {}
    ~NonCopyable(){}
  private:
    /** This copy constructor isn't implemented.<br>
      * It's here just so we can declare them as private so that this, and
      * any derived class, do not have copy constructors.
      */
    NonCopyable(const NonCopyable&);
    /** This assignment operator isn't implemented.<br>
      * It's here just so we can declare them as private so that this, and
      * any derived class, do not have copy constructors.
      */
    NonCopyable& operator=(const NonCopyable&);
};


//
// UTILITY CLASS "POOL"
//

/** This is an object pool which holds objects of a given type.<br>
  * The parameter type should have a default constructor.<br>
  * The size of the pool is extended automatically as additional objects are 
  * requested. There is no maximum to the number of objects allocated in the 
  * pool.<br> 
  * Allocations from the pool objects is O(1), while de-allocations 
  * are O(log(N)).<br>
  * The class is NOT thread-safe. The user is reponsible to allow only a 
  * single thread using a pool at the same time.
  */
template <class T> class Pool
{
  private:
    /** List of allocated objects. */
    set<T*> alloced;

    /** List of previously allocated, but now unused objects. */
    stack<T*> freed;

  public:
    /** Allocate a new object in the pool. */
    T* Alloc();

    /** Free an object and put it back in the pool.
      * Note that it is only legal to free objects which were
      * allocated from the pool.
      */
    void Free(T* Item);

    /** Constructor.<br>
      * The argument specifies the initial size of the pool. There is
      * no maximum to the number of objects in the pool.
      */
    Pool (int i = 0)
    {
      for ( ; i>0; --i) freed.push(new T());
    }

    /** Destructor. */
    ~Pool()
    {
      // Delete the allocated objects in use. The elements are not deleted 
      // from the set. The set destructor will clear the set.
      for(typename set<T*>::iterator i=alloced.begin(); i!=alloced.end(); ++i)
        delete *i;
      // Delete the objects on the free stack
      while (!freed.empty())
      {
        delete freed.top();
        freed.pop();
      }
    }
};


template <class T> T* Pool<T>::Alloc ()
{
  T* obj;
  if (freed.empty())
    // Create a new object
    obj = new T();
  else
  {
    // Re-use exisiting object
    obj = freed.top();
    freed.pop();
  }
  alloced.insert(obj);
  return obj;
}


template <class T> void Pool<T>::Free (T* it)
{
  // Erase the element from the stack
  if (alloced.erase(it))
  {
    // Found! Push the object on the stack of free objects.
    freed.push(it);
    return;
    };
  throw LogicException("Pool frees object it didn't allocate");
}


//
// UTILITY CLASSES FOR MULTITHREADING
//

/** This class is a wrapper around platform specific mutex functions. */
class Mutex: public NonCopyable
{
  public:
#ifndef MT
    // No threading support, empty class
    Mutex() {}
    ~Mutex()  {}
    void lock() {}
    void unlock() {}
#elif defined(HAVE_PTHREAD_H)
    // Pthreads
    Mutex()         { pthread_mutex_init(&mtx, 0); }
    ~Mutex()        { pthread_mutex_destroy(&mtx); }
    void lock()    { pthread_mutex_lock(&mtx); }
    void unlock()    { pthread_mutex_unlock(&mtx); }
  private:
    pthread_mutex_t mtx;
#else
    // Windows critical section
    Mutex() { InitializeCriticalSection(&critsec); }
    ~Mutex()  { DeleteCriticalSection(&critsec); }
    void lock() { EnterCriticalSection(&critsec); }
    void unlock() { LeaveCriticalSection(&critsec); }
  private:
    CRITICAL_SECTION critsec;
#endif
};


/** This is a convenience class that makes it easy (and exception-safe) to 
  * lock a mutex in a scope. 
  */
class ScopeMutexLock: public NonCopyable
{
  protected:
    Mutex* mtx;
  public:
    ScopeMutexLock(Mutex& imtx): mtx(&imtx) { mtx->lock(); }
    ~ScopeMutexLock() { mtx->unlock(); }
};


class MetaClass;

/** This enum defines the different priority values for threads. */
enum priority 
{
  /** Tasks with this priority are only executed when the system is idle. */
  IDLE = 0, 
  /** Priority is lower than normal. */
  LOW = 1, 
  /** The default priority level. */
  NORMAL = 2, 
  /** Priority is higher than normal. */
  HIGH = 3
};


class Lock 
{
  private:
    unsigned int readers;
    //Thread* writer;  @todo need to add a mutex or condition
    //Object* object;
  public:
    Lock() : readers(0) {}
    //~Lock() {object->lock = NULL;}
};


/** @todo Lock manager. First a single mngr class, later subclasses... */
class LockManager : public NonCopyable
{
  friend class LibraryUtils;
  private:
    static LockManager* mgr;
  public:
    static LockManager& getManager() {return *mgr;}
    void obtainReadLock(const Object*, priority = NORMAL);
    void obtainWriteLock(Object*, priority = NORMAL);
    void releaseReadLock(const Object*);
    void releaseWriteLock(Object*);
    void obtainReadLock(const Lock&, priority = NORMAL);
    void obtainWriteLock(Lock&, priority = NORMAL);
    void releaseReadLock(const Lock&);
    void releaseWriteLock(Lock&);
  private:
    /** Return a lock handle for this object. The locks are managed in a pool
      * to avoid constant freeing and allocating of memory. 
      * @todo needs to be atomic...
      */
    //Lock* getLock() const 
    //  { if (!l) const_cast<Object*>(this)->l = pool_locks.Alloc(); return l;}

    //typedef map <Lockable*, pair<unsigned int, unsigned int> > table;
    //static table locked;

    /** A pool of lock objects. */
    //static Pool<Lock> pool_locks;
};


//
// METADATA AND OBJECT FACTORY
//

/** This class defines an XML-tag.
  * Special for this class is the requirement to have a "perfect" hash
  * function, i.e. a function that returns a distinct number for each
  * defined tag. The class prints a warning message when the hash
  * function doesn't satisfy this criterion.
  */
class XMLtag : public NonCopyable
{
  private:
    /** Stores the hash value of this tag. */
    hashtype dw;

    /** Store different preprocessed variations of the name of the tag.
      * These are all stored in memory for improved performance. */
    string strName, strStartElement, strEndElement, strElement, strAttribute;

    /** Name of the string transcoded to its Xerces-internal representation. */
    XMLCh* xmlname;

  public:
    /** Container for maintaining a list of all tags. */
    typedef map<hashtype,XMLtag*> tagtable;

    /** This is the only constructor. */
    XMLtag(string n);

    /** Destructor. */
    ~XMLtag();

    /** Returns the hash value of the tag. */
    hashtype getHash() const {return dw;}

    /** Returns the name of the tag. */
    const string& getName() const {return strName;}

    /** Returns a pointer to an array of XML characters. This format is used
      * by Xerces for the internal representation of character strings. */
    const XMLCh* getXMLCharacters() const {return xmlname;}

    /** Returns a string to start an XML element with this tag: \<TAG */
    const string& stringStartElement() const {return strStartElement;}

    /** Returns a string to end an XML element with this tag: \</TAG\> */
    const string& stringEndElement() const {return strEndElement;}

    /** Returns a string to start an XML element with this tag: \<TAG\> */
    const string& stringElement() const {return strElement;}

    /** Returns a string to start an XML attribute with this tag: TAG=" */
    const string& stringAttribute() const {return strAttribute;}

    /** This is the hash function. See the note on the perfectness of
      * this function at the start. This function should be as simple
      * as possible while still garantueeing the perfectness.
      * Currently we use the hash functions provided by Xerces. We use
      * 954991 as the hash modulus (954991 being the first prime number higher
      * than 1000000)
      */
    static hashtype hash(const char* c) {return XMLString::hash(c,954991);}

    /** This is the hash function taken an XML character string as input.
      * The function is expected to return exactly the same result as when a
      * character pointer is passed as argument.
      * @see hash(const char*)
      */
    static hashtype hash(const XMLCh* c) {return XMLString::hash(c,954991);}

    /** Finds a tag when passed a certain string. If no tag exists yet, it
      * will be created. */
    static const XMLtag& find(char const*);

	  /** Return a reference to a table with all defined tags. */
	  static DECLARE_EXPORT tagtable& getTags();

    /** Prints a list of all tags that have been defined. This can be useful
      * for debugging and also for creating a good hashing function.<br>
      * GNU gperf is a program that can generate a perfect hash function for
      * a given set of symbols.
      */
    static void printTags();
};


/** This abstract class is the base class used for callbacks. 
  * @see MetaClass::callback
  * @see FunctorStatic
  * @see FunctorInstance
  */
class Functor : public NonCopyable
{
  public:
    /** This is the callback method.<br>
      * The return value should be true in case the action is allowed to 
      * happen. In case a subscriber disapproves the action false is
      * returned.<br>
      * It is important that the callback methods are implemented in a 
      * thread-safe and re-entrant way!!!
      */
    virtual bool callback(Object* v, Signal a) const = 0;
    virtual ~Functor() {}
};


class MetaCategory;
/** This class stores metadata about the classes in the library. The stored
  * information goes well beyond the standard 'type_info'.<br>
  * A MetaClass instance represents metadata for a specific instance type.
  * A MetaCategory instance represents metadata for a category of object.
  * For instance, 'Resource' is a category while 'ResourceDefault' and 
  * 'ResourceInfinite' are specific classes.<br>
  * The metadata class also maintains subscriptions to certain events. 
  * Registered classes and objects will receive callbacks when objects are
  * being created, changed or deleted.<br>
  * The proper usage is to include the following code snippet in every 
  * class:<br>
  * @code
  *  In the header file:
  *    class X : public Object
  *    {
  *      public:
  *        virtual const MetaClass& getType() {return metadata;}
  *        static const MetaClass metadata;
  *    }
  *  In the implementation file:
  *    const MetaClass X::metadata;
  * @endcode
  * Creating a MetaClass object isn't sufficient. It needs to be registered, 
  * typically in an initialization method:
  * @code
  *    void initialize()
  *    {
  *      ...
  *      Y::metadata.registerCategory("Y","Ys", reader_method, writer_method);
  *      X::metadata.registerClass("Y","X", factory_method);
  *      ...
  *    }
  * @endcode
  * @see MetaCategory
  */
class MetaClass : public NonCopyable
{

  friend class MetaCategory;
  template <class T, class U> friend class FunctorStatic;
  public:
    /** A string specifying the object type, i.e. the subclass within the
      * category. */
    string type;

    /** A reference to an XMLtag of the base string. */
    const XMLtag* typetag;

    /** This function will analyze the string being passed, and return the
      * appropriate action.
      * The string is expected to be one of the following:
      *  - 'A' for action ADD
      *  - 'C' for action CHANGE
      *  - 'AC' for action ADD_CHANGE
      *  - 'R' for action REMOVE
      *  - Any other value will result in a data exception
      */
    static Action decodeAction(const char*);

    /** This method picks up the attribute named "ACTION" from the list and
      * calls the method decodeAction(const XML_Char*) to analyze it.
      * @see decodeAction(const XML_Char*)
      */
    static Action decodeAction(const Attributes*);

    /** Sort two metaclass objects. This is used to sort entities on their
      * type information in a stable and platform independent way.
      * @see operator !=
      * @see operator ==
      */
    bool operator < (const MetaClass& b) const
    {
      return typetag->getHash() < b.typetag->getHash();
    }

    /** Compare two metaclass objects. We are not always sure that only a
      * single instance of a metadata object exists in the system, and a
      * pointer comparison is therefore not appropriate.
      * @see operator !=
      * @see operator <
      */
    bool operator == (const MetaClass& b) const
    {
      return typetag->getHash() == b.typetag->getHash();
    }

    /** Compare two metaclass objects. We are not always sure that only a
      * single instance of a metadata object exists in the system, and a
      * pointer comparison is therefore not appropriate.
      * @see operator ==
      * @see operator <
      */
    bool operator != (const MetaClass& b) const
    {
      return typetag->getHash() != b.typetag->getHash();
    } 

    /** This method should be called whenever objects of this class are being
      * created, updated or deleted. It will run the callback method of all
      * subscribers.<br>
      * If the function returns true, all callback methods approved of the
      * event. If false is returned, one of the callbacks disapproved it and
      * the event action should be allowed to execute.
      */
    bool raiseEvent(Object* v, Signal a) const;

    /** Connect a new subscriber to the class. */
    void connect(Functor *c, Signal a) const
      {const_cast<MetaClass*>(this)->subscribers[a].push_front(c);}

    /** Disconnect a subscriber from the class. */
    void disconnect(Functor *c, Signal a) const
      {const_cast<MetaClass*>(this)->subscribers[a].remove(c);}

  private:
    /** This is a list of objects that will receive a callback when the call 
      * method is being used.<br>
      * There is limited error checking in maintaining this list, and it is the 
      * user's responsability of calling the connect() and disconnect() methods 
      * correctly.<br>
      * This design garantuees maximum performance, but assumes a properly 
      * educated user.
      */
    list<Functor*> subscribers[4];

  public:
    /** Type definition for a factory method calling the default 
      * constructor.. */
    typedef Object* (*creatorDefault)();

    /** Type definition for a factory method calling the constructor that 
      * takes a string as argument. */
    typedef Object* (*creatorString)(string);

    /** A factory method for the registered class. */
    union 
    {
      creatorDefault factoryMethodDefault;
      creatorString factoryMethodString;
    };

    /** The category of this class. */
    const MetaCategory* category;

    /** Default constructor. */
    MetaClass() : type("UNSPECIFIED"), typetag(&XMLtag::find("UNSPECIFIED")), 
      factoryMethodDefault(NULL), category(NULL) {}

    /** Destructor. */
    virtual ~MetaClass() {}

    /** This constructor registers the metadata of a class. */
    void registerClass(const char*, const char*, bool = false) const;

    /** This constructor registers the metadata of a class, with a factory 
      * method that uses the default constructor of the class. */
    void registerClass (const char* cat, const char* cls, creatorDefault f, 
      bool def = false) const
    { 
      const_cast<MetaClass*>(this)->factoryMethodDefault = f; 
      registerClass(cat,cls,def); 
    }

    /** This constructor registers the metadata of a class, with a factory 
      * method that uses a constructor with a string argument. */
    void registerClass (const char* cat, const char* cls, creatorString f, 
      bool def = false) const
    { 
      const_cast<MetaClass*>(this)->factoryMethodString = f; 
      registerClass(cat,cls,def); 
    }

    /** Print all registered factory methods to the standard output for 
      * debugging purposes. */
    static void printClasses();

    /** Find a particular class by its name. If it can't be located the return 
      * value is NULL. */
    static const MetaClass* findClass(const char*);
};


class XMLOutput;
/** A MetaCategory instance represents metadata for a category of object.
  * A MetaClass instance represents metadata for a specific instance type.
  * For instance, 'Resource' is a category while 'ResourceDefault' and 
  * 'ResourceInfinite' are specific classes.<br>
  * A category has the following specific pieces of data:
  *  - A reader function for creating objects.<br>
  *    The reader function creates objects for all classes registered with it.
  *  - A writer function for persisting objects.<br>
  *    The writer function will typically iterate over all objects of the 
  *    category and call the writeElement method on them.
  *  - A group tag used for the grouping objects of the category in the XML 
  *    output stream.
  * @see MetaClass
  */
class MetaCategory : public MetaClass
{
  friend class MetaClass;
  friend class XMLInput;
  template<class T> friend class HasName;
  public:
    /** The name used to name a collection of objects of this category. */
    string group;

    /** A XML tag grouping objects of the category. */
    const XMLtag* grouptag;

    /** Type definition for the read control function. */
    typedef Object* (*readController)(const MetaCategory&, const XMLInput& in);

    /** Type definition for the write control function. */
    typedef void (*writeController)(const MetaCategory&, XMLOutput *o);

    /** This template method is available as a object creation factory for 
      * classes without key fields and which rely on a default constructor.
      */
    static Object* ControllerDefault (const MetaCategory&, const XMLInput& in);

    /** Default constructor. <br>
      * Calling the registerCategory method is required after creating a 
      * category object. 
      * @see registerCategory
      */
    MetaCategory() : group("UNSPECIFIED"), 
      grouptag(&XMLtag::find("UNSPECIFIED")), nextCategory(NULL), 
      writeFunction(NULL) {};

    /** Destructor. */
    virtual ~MetaCategory() {}

    /** This method is required to register the category of classes. */
    void registerCategory (const char* t, const char* g = NULL, 
      readController = NULL, writeController = NULL) const;

    /** Type definition for the map of all registered classes. */
    typedef map < hashtype, const MetaClass*, less<hashtype> > ClassMap;

    /** Type definition for the map of all categories. */
    typedef map < hashtype, const MetaCategory*, less<hashtype> > CategoryMap;

    /** Looks up a category name in the registry. If the catgory can't be 
      * located the return value is NULL. */
    static const MetaCategory* findCategoryByTag(const char*);

    /** Looks up a category name in the registry. If the catgory can't be 
      * located the return value is NULL. */
    static const MetaCategory* findCategoryByTag(const hashtype);

    /** Looks up a category name in the registry. If the catgory can't be 
      * located the return value is NULL. */
    static const MetaCategory* findCategoryByGroupTag(const char*);

    /** Looks up a category name in the registry. If the catgory can't be 
      * located the return value is NULL. */
    static const MetaCategory* findCategoryByGroupTag(const hashtype);

    /** This method takes care of the persistence of all categories. It loops
      * through all registered categories (in the order of their registration)
      * and calls the persistance handler.
      */
    static void persist(XMLOutput *);

    /** A control function for reading objects of a category. 
      * The controller function manages the creation and destruction of  
      * objects in this category. 
      */
    readController readFunction;

  private:
    /** A map of all classes registered for this category. */
    ClassMap classes;
    
    /** Compute the hash for "DEFAULT" once and store it in this variable for 
      * efficiency. */
    static const hashtype defaultHash;

    /** This is the root for a linked list of all categories. 
      * Categories are chained to the list in the order of their registration.
      */
    static DECLARE_EXPORT const MetaCategory* firstCategory;

    /** A pointer to the next category in the singly linked list. */
    const MetaCategory* nextCategory;

    /** A control function for writing the category. 
      * The controller function will loop over the objects in the category and
      * call write them one by one. 
      */
    writeController writeFunction;

    static DECLARE_EXPORT CategoryMap categoriesByTag;
    static DECLARE_EXPORT CategoryMap categoriesByGroupTag;
};


/** This class represents a static subscription to a signal.<br>
  * When the signal callback is triggered the static method callback() on the 
  * parameter class will be called.
  */
template <class T, class U> class FunctorStatic : public Functor
{
  friend class MetaClass;
  public:
    /** Add a signal subscriber. */
    static void connect(const Signal a) 
      {T::metadata.connect(new FunctorStatic<T,U>(), a);}

    /** Remove a signal subscriber. */
    static void disconnect(const Signal a) 
    {
      MetaClass &t = 
        const_cast<MetaClass&>(static_cast<const MetaClass&>(T::metadata));
      // Loop through all subscriptions
      for (list<Functor*>::iterator i = t.subscribers[a].begin(); 
        i != t.subscribers[a].end(); ++i)
      {
        // Try casting the functor to the right type
        FunctorStatic<T,U> *f = dynamic_cast< FunctorStatic<T,U>* >(*i);
        if (f)
        {
          // Casting was successfull. Delete the functor.
          delete *i;
          t.subscribers[a].erase(i);
          return;
        }
      }
      // Not found in the list of subscriptions
      throw LogicException("Subscription doesn't exist");
    }

  private:
    /** This is the callback method. The functor will call the static callback
      * method of the subscribing class.
      */
    virtual bool callback(Object* v, Signal a) const
      {return U::callback(static_cast<T*>(v),a);}
};


/** This class represents an object subscribing to a signal.<br>
  * When the signal callback is triggered the method callback() on the 
  * instance object will be called.
  * @todo incomplete implementation of class FunctorInstance
  */
template <class T, class U> class FunctorInstance : public Functor
{
  public: 
    /** Connect a new subscriber to a signal.<br>
      * It is the users' responsibility to call the disconnect method
      * when the subscriber is being deleted. Otherwise the application
      * will crash.
      */
    static void connect(U* u, Signal a) 
      {U::metadata.connect(new FunctorInstance(u), a);}

    /** Disconnect from a signal. */
    static void disconnect(U *u, Signal a)
    {} // U::metadata.disconnect(this, a);}

    /** Constructor. */
    FunctorInstance(U* up) : u(up) {assert(up);}

  private:
    /** This is the callback method. */
    virtual bool callback(void* v, Signal a) const
      {return u->call(static_cast<T*>(v),a);}

    /** The object whose callback method will be called. */
    U* u;
};


//
// UTILITY CLASS "TIMER".
//

/** This class is used to measure the processor time used by the program.
  * The accuracy of the timer is dependent on the implementation of the
  * ANSI C-function clock() by your compiler and your platform.
  * You may count on milli-second accuracy. Different platforms provide
  * more accurate timer functions, which can be used if the accuracy is a
  * prime objective.<br>
  * When compiled with Visual C++, the timer is returning the elapsed
  * time - which is not the expected ANSI behavior!<br>
  * Other compilers and platforms return the consumed cpu time, as expected.
  * When the load on a machine is low, the consumed cpu-time and the elapsed
  * time are close to each other. On a system with a higher load, the
  * elapsed time deviates a lot from the consumed cpu-time.
  */
class Timer
{
  public:
    /** Default constructor. Creating the timer object sets the start point
      * for the time measurement. */
    explicit Timer() : start_time(clock()) {}

    /** Reset the time counter to 0. */
    void restart() { start_time = clock(); }

    /** Return the cpu-time in seconds consumed since the creation or the last
      * reset of the timer. */
    double elapsed() const {return double(clock()-start_time)/CLOCKS_PER_SEC;}

  private:
    /** Stores the time when the timer is started. */
    clock_t start_time;
};


/** Prints a timer to the outputstream. The output is formatted as a double. */
inline ostream & operator << (ostream& os, const Timer& t)
{
  return os << t.elapsed();
}


//
// UTILITY CLASSES "DATE", "DATE_RANGE" AND "TIME".
//


/** This class represents a time duration with an accuracy of 1 second.
  * The duration can be both positive and negative. */
class TimePeriod
{
  friend ostream& operator << (ostream &, const TimePeriod &);
  public:
    /** Default constructor and constructor with timeperiod passed. */
    TimePeriod(const long l = 0) : lval(l) {}

    /** Comparison between periods of time. */
    bool operator < (const long& b) const {return lval < b;}

    /** Comparison between periods of time. */
    bool operator > (const long& b) const {return lval > b;}

    /** Comparison between periods of time. */
    bool operator <= (const long& b) const {return lval <= b;}

    /** Comparison between periods of time. */
    bool operator >= (const long& b) const {return lval >= b;}

    /** Comparison between periods of time. */
    bool operator < (const TimePeriod& b) const {return lval < b.lval;}

    /** Comparison between periods of time. */
    bool operator > (const TimePeriod& b) const {return lval > b.lval;}

    /** Comparison between periods of time. */
    bool operator <= (const TimePeriod& b) const {return lval <= b.lval;}

    /** Comparison between periods of time. */
    bool operator >= (const TimePeriod& b) const {return lval >= b.lval;}

    /** Equality operator. */
    bool operator == (const TimePeriod& b) const {return lval == b.lval;}

    /** Inequality operator. */
    bool operator != (const TimePeriod& b) const {return lval != b.lval;}

    /** Increase the timeperiod. */
    void operator += (const TimePeriod& l) {lval += l.lval;}

    /** Decrease the timeperiod. */
    void operator -= (const TimePeriod& l) {lval -= l.lval;}

    /** Returns true of the duration is equal to 0. */
    bool operator ! () const {return lval == 0L;}

    /** This conversion operator creates a long value from a timeperiod. */
    operator long() const {return lval;}

    /** Converts the date to a string. The string is formatted -HHH:MM:SS.
      * The sign is only shown for negative times.
      * The HHH: part is left out when the period is less than an hour, and
      * similarly the MM: part is left out if the period is less than a
      * minute.
      */
    operator string() const
    {
      char str[20];
      toCharBuffer(str);
      return string(str);
    }

    /** Function that parses a input string to a time value.
      * The function expects the following input pattern:<br>
      *    (\+\-)?(([0-9]*:)?([0-9]*:))?[0-9]*<br>
      * Here some different input examples, all for a time period of 2 days:
      *  - 48:00:00
      *  - +48:0:0
      *  - 47:60:00
      *  - 46:120:00
      *  - -2880:00
      *  - 172800
      */
    void parse(const char*);

  private:
    /** The time is stored as a number of seconds. */
    long lval;

    /** This function fills a character buffer with a text representation of
      * the TimePeriod.<br>
      * The character buffer passed is expected to have room for
      * at least 20 characters. 20 characters should be sufficient for even
      * the most longest possible time duration.<br>
      * The output format is described with the string() method.
      * @see string()
      */
    void toCharBuffer(char*) const;
};


/** Prints a Timeperiod to the outputstream.
  * @see TimePeriod::string()
  */
inline ostream & operator << (ostream & os, const TimePeriod & t)
{
  char str[20];
  t.toCharBuffer(str);
  return os << str;
}


/** This class represents a date and time with an accuracy of 1 second. */
class Date
{
  friend ostream& operator << (ostream &, const Date &);
  private:
    /** This string is a format string to be used to convert a date to and
      * from a string format. The formats codes that are allowed are the
      * ones recognized by the standard C function strftime:
      *  - %a short name of day
      *  - %A full name of day
      *  - %b short name of month
      *  - %B full name of month
      *  - %c standard string for Date and time
      *  - %d day of month (between 1 and 31)
      *  - %H hour (between 0 and 23)
      *  - %I hour (between 1 and 12)
      *  - %j day of the year (between 1 and 366)
      *  - %m month as number (between 1 and 12)
      *  - %M minutes (between 0 and 59)
      *  - %p AM/PM
      *  - %S seconds (between o and 59)
      *  - %U week of the year (between 0 and 52, sunday as start of week)
      *  - %w day of the week (between 0 and 6, sunday as start of week)
      *  - %W week of the year (monday as first day of week)
      *  - %x standard string for Date
      *  - %X standard string for time
      *  - %y year (between 0 and 99, without century)
      *  - %Y year (complete)
      *  - %Z time zone
      *  - %% percentage sign
      * The default date format is %Y-%m-%dT%H:%M:%S, which is the standard
      * format defined in the XML Schema standard.
      */
    static DECLARE_EXPORT string format;

    /** The internal representation of a date is a single long value. */
    time_t lval;

    /** Checks whether we stay within the boundaries of finite Dates. */
    void checkFinite();

    /** This function fills a character buffer with a text representation of
      * the date.<br>
      * The character buffer passed is expected to have room for
      * at least 30 characters. 30 characters should be sufficient for even
      * the most funky date format.
      */
    void toCharBuffer(char*) const;

    /** A private constructor used to create the infinitePast and 
      * infiniteFuture constants. */
    Date(const char* s, bool dummy) {parse(s);}

    /** Constructor initialized with a long value. */
    Date(const time_t l) : lval(l) {checkFinite();}

  public:
    /** Default constructor. */
    // This is the only constructor that can skip the check for finite dates,
    // and thus gives the best performance.
    Date() : lval(infinitePast.lval) {}

    /** Copy constructor. */
    Date(const Date& l) : lval(l.lval) {}

    /** Constructor initialized with a string. The string needs to be in
      * the format specified by the "format". */
    Date(const char* s) {parse(s); checkFinite();}

    /** Comparison between dates. */
    bool operator < (const Date& b) const {return lval < b.lval;}

    /** Comparison between dates. */
    bool operator > (const Date& b) const {return lval > b.lval;}

    /** Equality of dates. */
    bool operator == (const Date& b) const {return lval == b.lval;}

    /** Inequality of dates. */
    bool operator != (const Date& b) const {return lval != b.lval;}

    /** Comparison between dates. */
    bool operator >= (const Date& b) const {return lval >= b.lval;}

    /** Comparison between dates. */
    bool operator <= (const Date& b) const {return lval <= b.lval;}

    /** Assignment operator. */
    void operator = (const Date& b) {lval = b.lval;}

    /** Adds some time to this date. */
    void operator += (const TimePeriod& l)
    {lval += static_cast<long>(l); checkFinite();}

    /** Subtracts some time to this date. */
    void operator -= (const TimePeriod& l)
    {lval -= static_cast<long>(l); checkFinite();}

    /** Adding a time to a date returns a new date. */
    Date operator + (const TimePeriod& l) const
      {return lval + static_cast<long>(l);}

    /** Subtracting a time to a date returns a new date. */
    Date operator - (const TimePeriod& l) const
      {return lval - static_cast<long>(l);}

    /** Subtracting two date values returns the time difference in a
      * TimePeriod object. */
    TimePeriod operator - (const Date& l) const
      {return static_cast<long>(lval - l.lval);}

    /** Check whether the date has been initialized. */
    bool operator ! () const {return lval == infinitePast.lval;}

    /** Check whether the date has been initialized. */
    operator bool() const {return lval != infinitePast.lval;}

    /** Static function returns a date object initialized with the current
      * Date and time. */
    static Date now() {return Date(time(0));}

    /** Converts the date to a string. The format can be controlled by the
      * setFormat() function. */
    operator string() const
    {
      char str[30];
      toCharBuffer(str);
      return string(str);
    }

    /** Function that parses a string according to the format string. */
    void parse(const char*, const string& = format);

    /** Updates the default date format. */
    static void setFormat(string& n) {format = n;}

    /** Retrieves the default date format. */
    static string getFormat() {return format;}

    /** A constant representing the infinite past, i.e. the earliest time which
      * we can represent.<br>
      * This value is normally 1971-01-01T00:00:00.
      */
    static DECLARE_EXPORT const Date infinitePast;

    /** A constant representing the infinite future, i.e. the latest time which
      * we can represent.<br>
      * This value is currently set to 2030-12-31T00:00:00.
      */
    static DECLARE_EXPORT const Date infiniteFuture;

#ifndef HAVE_STRPTIME
  private:
    char* strptime(const char *buf, const char *fmt, struct tm *tm);
#endif
};


/** Prints a date to the outputstream. */
inline ostream & operator << (ostream & os, const Date & d)
{
  char str[30];
  d.toCharBuffer(str);
  return os << str;
}


/** This class defines a date-range, i.e. a start-date and end-date pair.<br>
  * The behavior is such that the start date is considered as included in
  * it, but the end date is excluded from it.
  * In other words, a daterange is a halfopen date interval: [start,end[<br>
  * The start and end dates are always such that the start date is less than
  * or equal to the end date.
  */
class DateRange
{
  public:
    /** Constructor with specified start and end dates.<br>
      * If the start date is later than the end date parameter, the parameters
      * will be swapped. */
    DateRange(const Date& st, const Date& nd) : start(st), end(nd)
    {if(st>nd) {start=nd; end=st;}}

    /** Default constructor. Both the start and end time will be set to 0. */
    DateRange() {}

    /** Copy constructor. */
    DateRange(const DateRange& n) : start(n.start), end(n.end) {}

    /** Returns the start date. */
    const Date& getStart() const {return start;}

    /** Updates the start date.<br>
      * If the new start date is later than the end date, the end date will
      * be set equal to the new start date.
      */
    void setStart(const Date& d) {start=d; if(start>end) end=start;}

    /** Returns the end date. */
    const Date & getEnd() const {return end;}

    /** Updates the end date.<br>
      * If the new end date is earlier than the start date, the start date will
      * be set equal to the new end date.
      */
    void setEnd(const Date& d) {end=d; if(start>end) start=end;}

    /** Updates the start and end dates simultaneously. */
    void setStartAndEnd(const Date& st, const Date& nd)
    {if (st<nd) {start=st; end=nd;} else {start=nd; end=st;}}

    /** Returns the duration of the interval. Note that this number will always
      * be greater than or equal to 0, since the end date is always later than
      * the start date.
      */
    TimePeriod getDuration() const {return end - start;}

    /** Equality of date ranges. */
    bool operator == (const DateRange& b) const 
      {return start==b.start && end==b.end;}

    /** Inequality of date ranges. */
    bool operator != (const DateRange& b) const 
      {return start!=b.start || end!=b.end;}

    /** Move the daterange later in time. */
    void operator += (const TimePeriod& l) {start += l; end += l;}

    /** Move the daterange earlier in time. */
    void operator -= (const TimePeriod& l) {start -= l; end -= l;}

    /** Assignment operator. */
    void operator = (const DateRange& dr) {start = dr.start; end = dr.end;}

    /** Return true if two date ranges are overlapping. */
    bool intersect(const DateRange& dr) const
      {return dr.start<end && dr.end>start;}

    /** Returns true if the date passed as argument does fall within the
      * daterange. */
    bool within(const Date& d) const {return d>=start && d<end;}

    /** Convert the daterange to a string. */
    operator string() const;

    /** Updates the default seperator. */
    static void setSeparator(const string& n) {separator = n;}

    /** Retrieves the default seperator. */
    static const string& getSeparator() {return separator;}

  private:
    /** Start date of the interval. */
    Date start;

    /** End dat of the interval. */
    Date end;

    /** Separator to be used when printing this string. */
    static DECLARE_EXPORT string separator;
};


/** Prints a date range to the outputstream.
  * @see DateRange::string() */
inline ostream & operator << (ostream & os, const DateRange & dr)
{
  return os << dr.getStart() << DateRange::getSeparator() << dr.getEnd();
}


//
// UTILITY CLASSES FOR INPUT AND OUTPUT
//


/** This type is used to define different ways of persisting an object. */
enum mode 
{
  /** Write the full object or a reference. If the object is nested more 
    * than one level deep a reference is written, otherwise the complete 
    * object is written.<br>
    * This mode is the one to be used when dumping all objects to be restored
    * later. The other modes can dump too little or too much data.
    * Eg: \<MODEL NAME="POL" TYPE="a"\>\<FIELD\>value\</FIELD\>\</MODEL\>
    */
  DEFAULT = 0,   
  /** Write only the key fields of the object.<br>
    * Eg: \<MODEL NAME="POL" TYPE="a"/\> 
    */
  REFERENCE = 1, 
  /** Write the full object, but without a header line. This method is
    * typically used when a subclass calls the write method of its parent
    * class.<br>
    * Eg: \<FIELD\>value\</FIELD\>\</MODEL\> 
    */
  NOHEADER = 2,
  /** Write the full object, with all its fields and a header line.<br>
    * Eg: \<MODEL NAME="POL" TYPE="a"\>\<FIELD\>value\</FIELD\>\</MODEL\>
    */
  FULL = 3
};


/** This class writes XML formatted data to a output stream. Subclasses will
  * implement writing to specific stream types, such as files and strings.
  */
class XMLOutput
{
  protected:
    /** Updating the output stream. */
    void setOutput(ostream& o) {m_fp = &o;}

  public:
    /** This type is used to define different types of output.
      * @see STANDARD
      * @see PLAN
      * @see PLANDETAIL
      */
    typedef unsigned short content_type;

    /** Constant used to mark standard export for the export.
      * The standard export saves just enough information to persist the full
      * state of the model as brief as possible.
      * @see PLAN
      * @see PLANDETAIL
      */
    static const content_type STANDARD;

    /** Constant to mark an export of the standard information plus the plan 
      * information. In this format, every entity is saved with the details 
      * on how it is used in the plan.<br>
      * E.g. a resource will be saved with a reference to all its loadplans.
      * E.g. an operation will be saved with all its operationplans.
      * @see STANDARD
      * @see PLANDETAIL
      */
    static const content_type PLAN;

    /** Constant to mark an export of the lowest level of plan information.
      * In addition to the plan information pegging information is now saved.
      * @see STANDARD
      * @see PLAN
      */
    static const content_type PLANDETAIL;

    /** Returns which type of export is requested. 
      * Constants have been defined for each type.
      * @see STANDARD
      * @see PLAN
      * @see PLANDETAIL
      */
    content_type getContentType() const {return content;}

    /** Specify the type of export. 
      * @see STANDARD
      * @see PLAN
      * @see PLANDETAIL
      */
    void setContentType(content_type c) {content = c;}

    /** Updates the string that is printed as the first line of each XML
      * document.
      * The default value is:
      *   <?xml version="1.0" encoding="UTF-8"?>
      */
    void setHeaderStart(const string& s) {headerStart = s;}

    /** Returns the string that is printed as the first line of each XML
      * document. */
    const string& getHeaderStart() {return headerStart;}

    /** Updates the attributes that are written for the root element of each
      * XML document. The default value is an empty string. */
    void setHeaderAtts(const string& s) {headerAtts = s;}

    /** Returns the attributes that are written for the root element of each
      * XML document. */
    const string& getHeaderAtts() {return headerAtts;}

    /** Constructor with a given stream. */
    XMLOutput(ostream& os) : m_nIndent(0), numObjects(0), numParents(0), 
      currentObject(NULL), parentObject(NULL), content(STANDARD),
      headerStart("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"),
      headerAtts("xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"")
      {m_fp = &os; indentstring[0] = '\0';}

    /** Default constructor. */
    XMLOutput() : m_nIndent(0), numObjects(0), numParents(0), 
      currentObject(NULL), parentObject(NULL), content(STANDARD),
      headerStart("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"),
      headerAtts("xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"")
    {m_fp = &clog; indentstring[0] = '\0';}

    /** Escape a char string - remove the characters & < > " ' and replace with
      * the proper escape codes. The reverse process of un-escaping the special
      * character sequences is taken care of by the xml library.
      * @param  pstr character pointer to a the character string to be processed
      * @return string with escaped characters
      */
    string XMLEscape(const char *pstr);

    /** Start writing a new object. This method will open a new XML-tag.
      * Output: \<TAG_T\> */
    void BeginObject(const XMLtag& t)
    {
      *m_fp << indentstring << t.stringElement() << "\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.
      * Output: \<TAG_T TAG_U="date"\> */
    void BeginObject(const XMLtag& t, const XMLtag& attr1, const Date val1)
    {
      *m_fp << indentstring << t.stringStartElement()
      << attr1.stringAttribute() << string(val1) << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.
      * Output: \<TAG_T TAG_U="string"\> */
    void BeginObject(const XMLtag& t, const XMLtag& attr1, const string& val1)
    {
      *m_fp << indentstring << t.stringStartElement()
      << attr1.stringAttribute() << XMLEscape(val1.c_str()) << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag. */
    void BeginObject(const XMLtag& t, const string& atts)
    {
      *m_fp << indentstring << t.stringStartElement() << " " << atts << ">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.
      * Output: \<TAG_T TAG_U="long"\> */
    void BeginObject(const XMLtag& t, const XMLtag& attr1, const long val1)
    {
      *m_fp << indentstring << t.stringStartElement()
      << attr1.stringAttribute() << val1 << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.
      * Output: \<TAG_T TAG_T1="val1" TAG_T2="val2"\> */
    void BeginObject(const XMLtag& t, const XMLtag& attr1, const string& val1,
                     const XMLtag& attr2, const string& val2)
    {
      *m_fp << indentstring << t.stringStartElement()
      << attr1.stringAttribute() << XMLEscape(val1.c_str()) << "\""
      << attr2.stringAttribute() << XMLEscape(val2.c_str()) << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.
      * Output: \<TAG_T TAG_T1="val1" TAG_T2="val2"\> */
    void BeginObject(const XMLtag& t, const XMLtag& attr1, unsigned long val1,
                     const XMLtag& attr2, const string& val2)
    {
      *m_fp << indentstring << t.stringStartElement()
      << attr1.stringAttribute() << val1 << "\""
      << attr2.stringAttribute() << XMLEscape(val2.c_str()) << "\">\n";
      incIndent();
    }

    /** Write the closing tag of this object and decrease the indentation
      * level.
      * Output: \</TAG_T\>
      */
    void EndObject(const XMLtag& t)
    {
      decIndent();
      *m_fp << indentstring << t.stringEndElement();
    }

    /** Write the string to the output. No XML-tags are added, so this method
      * is used for passing text straight into the output file. */
    void writeString(const string& c)
    {
      *m_fp << indentstring << c << "\n";
    }

    /** Write an unsigned long value enclosed opening and closing tags.
      * Output: \<TAG_T\>uint\</TAG_T\> */
    void writeElement(const XMLtag& t, const long unsigned int val)
    {
      *m_fp << indentstring << t.stringElement() << val << t.stringEndElement();
    }

    /** Write an integer value enclosed opening and closing tags.
      * Output: \<TAG_T\>integer\</TAG_T\> */
    void writeElement(const XMLtag& t, const int val)
    {
      *m_fp << indentstring << t.stringElement() << val << t.stringEndElement();
    }

    /** Write a double value enclosed opening and closing tags.
      * Output: \<TAG_T\>double\</TAG_T\> */
    void writeElement(const XMLtag& t, const double val)
    {
      *m_fp << indentstring << t.stringElement() << val << t.stringEndElement();
    }

    /** Write a boolean value enclosed opening and closing tags. The boolean
      * is written out as the string 'true' or 'false'.
      * Output: \<TAG_T\>true\</TAG_T\>
      */
    void writeElement(const XMLtag& t, const bool val)
    {
      *m_fp << indentstring << t.stringElement()
      << (val ? "true" : "false") << t.stringEndElement();
    }

    /** Write a string value enclosed opening and closing tags. Special
      * characters (i.e. & < > " ' ) are appropriately escaped.
      * Output: \<TAG_T\>val\</TAG_T\> */
    void writeElement(const XMLtag& t, const string& val)
    {
      if (!val.empty())
        *m_fp << indentstring << t.stringElement()
        << XMLEscape(val.c_str()).c_str() << t.stringEndElement();
    }

    /** Writes an element with a string attribute.
      * Output: \<TAG_U TAG_T="string"/\> */
    void writeElement(const XMLtag& u, const XMLtag& t, const string& val)
    {
      if (val.empty())
        *m_fp << indentstring << u.stringStartElement() << "/>\n";
      else
        *m_fp << indentstring << u.stringStartElement()
        << t.stringAttribute() << XMLEscape(val.c_str())
        << "\"/>\n";
    }

    /** Writes an element with a long attribute.
      * Output: \<TAG_U TAG_T="val"/\> */
    void writeElement(const XMLtag& u, const XMLtag& t, const long val)
    {
      *m_fp << indentstring << u.stringStartElement()
      << t.stringAttribute() << val << "\"/>\n";
    }

    /** Writes an element with a date attribute.
      * Output: \<TAG_U TAG_T="val"/\> */
    void writeElement(const XMLtag& u, const XMLtag& t, const Date& val)
    {
      *m_fp << indentstring << u.stringStartElement()
      << t.stringAttribute() << string(val) << "\"/>\n";
    }

    /** Writes an element with 2 string attributes.
      * Output: \<TAG_U TAG_T1="val1" TAG_T2="val2"/\> */
    void writeElement(const XMLtag& u, const XMLtag& t1, const string& val1,
      const XMLtag& t2, const string& val2)
    {
      if(val1.empty())
        *m_fp << indentstring << u.stringStartElement() << "/>\n";
      else
        *m_fp << indentstring << u.stringStartElement()
        << t1.stringAttribute() << XMLEscape(val1.c_str()) << "\""
        << t2.stringAttribute() << XMLEscape(val2.c_str())
        << "\"/>\n";
    }

    /** Writes an element with a string and a long attribute.
      * Output: \<TAG_U TAG_T1="val1" TAG_T2="val2"/\> */
    void writeElement(const XMLtag& u, const XMLtag& t1, unsigned long val1,
      const XMLtag& t2, const string& val2)
    {
      *m_fp << indentstring << u.stringStartElement()
      << t1.stringAttribute() << val1 << "\""
      << t2.stringAttribute() << XMLEscape(val2.c_str())
      << "\"/>\n";
    }

    /** Writes a C-type character string.
      * Output: \<TAG_T\>val\</TAG_T\> */
    void writeElement(const XMLtag& t, const char* val)
    {
      if (val)
        *m_fp << indentstring << t.stringElement()
        << XMLEscape(val).c_str() << t.stringEndElement();
    }

    /** Writes an timeperiod element.
      * Output: \<TAG_T\>d\</TAG_T\> /> */
    void writeElement(const XMLtag& t, const TimePeriod d)
    {
      *m_fp << indentstring << t.stringElement() << d << t.stringEndElement();
    }

    /** Writes an date element.
      * Output: \<TAG_T\>d\</TAG_T\> /> */
    void writeElement(const XMLtag& t, const Date d)
    {
      *m_fp << indentstring << t.stringElement() << d << t.stringEndElement();
    }

    /** Writes an daterange element.
      * Output: \<TAG_T\>d\</TAG_T\> */
    void writeElement(const XMLtag& t, const DateRange& d)
    {
      *m_fp << indentstring << t.stringElement() << d << t.stringEndElement();
    }

    /** This method writes a serializable object. It maintains a STL-map of
      * all objects that have been saved already. For objects that have
      * already been saved earlier, the method will instruct the serializable
      * object to write only a reference, rather than the complete object.
      * You should call this method for all objects in your xml document,
      * except for the root object.
      * @see writeElementWithHeader(const XMLtag&, Object*)
      */
    void writeElement(const XMLtag& tag, const Object* object, mode = DEFAULT);

    /** @see writeElement(const XMLtag&, const Object*, mode) */
    void writeElement(const XMLtag& t, const Object& o, mode m = DEFAULT)
      {writeElement(t,&o,m);}

    /** This method writes a serializable object with a complete XML compliant
      * header.
      * You should call this method for the root object of your xml document,
      * and writeElement for all objects nested in it.
      * @see writeElement(const XMLtag&, Object*)
      * @see writeHeader
      * @exception RuntimeException Generated when multiple root elements
      *    are available for the output document.
      */
    void writeElementWithHeader(const XMLtag& tag, const Object* object);

    /** This method writes the opening tag for an XML output.
      * You should call this method or writeElementWithHeader() when writing
      * the first element of an xml document,
      * @see writeElementWithHeader
      * @exception RuntimeException Generated when multiple root elements
      *    are available for the output document.
      */
    void writeHeader(const XMLtag& tag);

    /** Returns a pointer to the object that is currently being saved. */
    Object* getCurrentObject() const
      {return const_cast<Object*>(currentObject);}

    /** Returns a pointer to the parent of the object that is being saved. */
    Object* getPreviousObject() const
      {return const_cast<Object*>(parentObject);}

    /** Returns the number of objects that have been serialized. */
    unsigned long countObjects() const {return numObjects;}

  private:
    /** Output stream. */
    ostream* m_fp;

    /** This variable keeps track of the indentation level.
      * @see incIndent, decIndent
      */
    short int m_nIndent;

    /** This string is a null terminated string containing as many spaces as
      * indicated by the m_indent.
      * @see incIndent, decIndent
      */
    char indentstring[41];

    /** Keep track of the number of objects being stored. */
    unsigned long numObjects;

    /** Keep track of the number of objects currently in the save stack. */
    unsigned int numParents;

    /** This stores a pointer to the object that is currently being saved. */
    const Object *currentObject;

    /** This stores a pointer to the object that has previously been saved. */
    const Object *parentObject;

    /** Increase the indentation level. The indentation level is between
      * 0 and 40. */
    void incIndent();

    /** Decrease the indentation level. */
    void decIndent();

    /** Stores the type of data to be exported. */
    content_type content;

    /** This string defines what will be printed at the start of each XML
      * document. The default value is:
      *   \<?xml version="1.0" encoding="UTF-8"?\>
      */
    string headerStart;

    /** This string defines what will be attributes are printed for the root
      * element of each XML document.
      * The default value is:
      *    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      */
    string headerAtts;
};


/** This class writes XML data to a flat file.
  * Note that an object of this class can write only to a single file. If
  * multiple files are required multiple XMLOutputFile objects will be
  * required too.
  * @see XMLOutput
  */
class XMLOutputFile : public XMLOutput
{
  public:
    /** Constructor with a filename as argument. An exception will be
      * thrown if the output file can't be properly initialized. */
    XMLOutputFile(const string& chFilename)
    {
      of.open(chFilename.c_str(), ios::out);
      if(!of) throw RuntimeException("Could not open output file");     
      setOutput(of);
    }

    /** Destructor. */
    ~XMLOutputFile() {of.close();}

  private:
    ofstream of;
};


/** This class writes XML data to a string.
  * The generated output is stored internally in the class, and can be
  * accessed by converting the XMLOutputString object to a string object.
  * This class can consume a lot of memory if large sets of objects are
  * being saved in this way.
  * @see XMLOutput
  */
class XMLOutputString : public XMLOutput
{
  public:
    /** Constructor with a starting string as argument. */
    XMLOutputString(const string& str) : os(str) {setOutput(os);}

    /** Default constructor. */
    XMLOutputString() {setOutput(os);}

    /** Return the output string. */
    const string getData() const {return os.str();}
    
  private:
    ostringstream os;
};


/** This class represents an XML element being read in from the input file. */
class XMLElement
{
  private:
    /** This string stores the XML input data. */
    string m_strData;

    /** This string stores the hash value of the element. */
    hashtype m_dwTagHash;

  public:
    /** Re-initializes an existing element. Using this method we can avoid
      * destroying and recreating XMLelement objects too frequently. Instead
      * we can manage them in a array.
      * Since we consistently use this method, the auto-generated default
      * constructor and copy constructor are okay and safe.
      */
    void initialize(const char *c)
    {
      m_dwTagHash = XMLtag::hash(c);
      m_strData.clear();
    }

    /** This method is used to expand environment variables.<br>
      * When a data field contains a construct ${ABC} the environment variable
      * ABC is picked up from the operating system to replace it. If the
      * environment variable doesn't exist an empty string is used.<br>
      * Note that (for performance and security reasons) this kind of 
      * environment variable expansion isn't enabled by default. This method 
      * needs to be called explicitly for fields where such expansion is 
      * desired.
      */
    void resolveEnvironment();

    /** Re-initializes an existing element.
      * @see initialize(const char*)
      */
    void initialize(const XMLCh *c)
    {
      m_dwTagHash = XMLtag::hash(c);
      m_strData.clear();
    }

    /** Returns the hash value of this tag. */
    hashtype getTagHash() const {return m_dwTagHash;}

    /** Add some characters to this data field of this element. */
    void addData(const char *pData, size_t len) {m_strData.append(pData,len);}

    /** Set the data value of this element. */
    void setData(const char *pData) {m_strData.assign(pData);}

    /** Return the data field. */
    const char *getData() const {return m_strData.c_str();}

    /** Return the element name. Since this method involves a lookup in a
      * table with XMLtags, it has some performance impact and should be
      * avoided where possible. Only the hash of an element can efficiently
      * be retrieved.
      */
    string getName() const;

    /** Returns true when this element is an instance of this tag. This method
      * doesn't involve a string comparison and is extremely efficient. */
    bool isA(const XMLtag& t) const {return t.getHash() == m_dwTagHash;}

    /** Returns true when this element is an instance of this tag. This method
      * doesn't involve a string comparison and is extremely efficient. */
    bool isA(const XMLtag* t) const {return t->getHash() == m_dwTagHash;}

    void operator >> (unsigned long int& val) const {val = atol(getData());}

    void operator >> (long& val) const {val = atol(getData());}

    long getLong() const {return atol(getData());}

    void operator >> (TimePeriod& val) const {val.parse(getData());}

    void operator >> (bool& v) const {v=getBool();}

    TimePeriod getTimeperiod() const
      {TimePeriod x; x.parse(getData()); return x;}

    void operator >> (int& val) const {val = atoi(getData());}

    int getInt() const {return atoi(getData());}

    void operator >> (float& val) const
      {val = static_cast<float>(atof(getData()));}

    float getFloat() const {return static_cast<float>(atof(getData()));}

    void operator >> (double& val) const {val = atof(getData());}

    double getDouble() const {return atof(getData());}

    void operator >> (Date& val) const {val.parse(getData());}

    Date getDate() const {Date x; x.parse(getData()); return x;}

    /** Fills in the string with the XML input. The xerces library takes care
      * of appropriately unescaping special character sequences. */
    void operator >> (string& val) const {val = getData();}

    /** Returns the string value of the XML data. The xerces library takes care
      * of appropriately unescaping special character sequences. */
    const string& getString() const {return m_strData;}

    /** Interprets the element as a boolean value.<br>
      * <p>Our implementation is a bit more generous and forgiving than the
      * boolean datatype that is part of the XML schema v2 standard.
      * The standard expects the following literals:<br>
      *   {true, false, 1, 0}</p>
      * <p>Our implementation uses only the first charater of the text, and is
      * case insensitive. It thus matches a wider range of values:<br>
      *   {t.*, T.*, f.*, F.*, 1.*, 0.*}</p>
      */
    bool getBool() const;
};


/** Object is the abstract base class for the main entities.
  * It handles to following capabilities:
  * - Metadata: All subclasses publish metadata about their structure.
  * - Concurrency: Locking of objects is required in multithreaded 
  *   environments. The implementation of the locking algorithm is delegated
  *   to the LockManager class, and the base class provides only a pointer
  *   to a lock object and convenience guard classes.
  * - Callbacks: When objects are created, changing or deleted, interested 
  *   classes or objects can get a callback notification.
  * - Serialization: Objects need to be persisted and later restored.
  *   Subclasses that don't need to be persisted can skip the implementation
  *   of the writeElement method.
  * Objects of this class can be marked as hidden, which means that they
  * are not being exported at all.
  */
class Object
{
  friend class LockManager;
  public:
    /** Constructor. */
    explicit Object() : lock(NULL) {}

    /** Destructor. */
    virtual ~Object() {}

    /** Called while writing the model into an XML-file.
      * The user class should write itself out, using the IOutStream
      * members for its "simple" members and calling writeElement
      * recursively for any contained objects.
      * Not all classes are expected to implement this method. In instances
      * of such a class can be created but can't be persisted.
      * E.g. Command
      */
    virtual void writeElement(XMLOutput *, const XMLtag &, mode=DEFAULT) const
      {throw LogicException("Class can't be persisted");}

    /** Called while restoring the model from an XML-file.
      * This is called for each element within the "this" element,
      * for which the "this" element is immediate parent.
      * It is called when the open element tag is encountered.
      */
    virtual void beginElement(XMLInput&, XMLElement&) {}

    /** Called while restoring the model from an XML-file.
      * This is called when the corresponding close element
      * tag is encountered, and the Data() member of pElement is
      * also valid.
      * NOTE: each object receives both its own beginElement so it can
      * process its own element tag attributes, and its own endElement
      * so it can process its own character data.
      */
    virtual void endElement(XMLInput&, XMLElement&) = 0;

    /** Mark the object as hidden or not. Hidden objects are not exported
      * and are used only as dummy constructs. */
    virtual void setHidden(bool b) {}

    /** Returns whether an entity is real or dummy. */
    virtual bool getHidden() const {return false;}

    /** This the subclass field. */
    virtual const MetaClass& getType() const = 0;

    /** Return the memory size of the object in bytes. */
    virtual size_t getSize() const = 0;

    /** The RLock class provides an exception safe way of getting a read lock 
      * on a Object object.<br>
      * The constructor acquires the read lock and the destructor will release 
      * it again.<br>
      * RLocks should be used as temporary objects on the stack, and should
      * be accessed by a single thread only.
      */
    template <class T> class RLock
    {
      public:
	      /** Constructs a read-lock. This method blocks till the object
          * lock can be obtained.
          */
        explicit RLock(const T* l) : obj(l) 
          {LockManager::getManager().obtainReadLock(obj);}

        /** Copy constructor. 
          * You should only copy a lock within the same thread!
          */
        explicit RLock(const RLock<T>& p) : obj(p.obj) {}

	      /** Destructor. The lock is released upon deletion of this object. */
  	    ~RLock() {LockManager::getManager().releaseReadLock(obj);}

        /** Returns a pointer to the locked object. */
        const T* getObject() const {return obj;}

        T& operator*() const {return *obj;}
        T* operator->() const {return obj;}

      private:
	      /** A pointer to the object being locked. */
        const T* obj;
    };


    /** The WLock class provides an exception safe way of getting 
      * a write lock on a Object object.<br>
      * The constructor acquires the write lock and the destructor will release 
      * it again.<br>
      * WLocks should be used as temporary objects on the stack, and should
      * be accessed by a single thread only.
      */
    template <class T> class WLock
    {
      public:
	      /** Constructs a write-lock. This method blocks till the object
          * lock can be obtained.
          */
        explicit WLock(T* l)  : obj(l)
          {LockManager::getManager().obtainWriteLock(obj);}

        /** Copy constructor.
          * You should only copy a lock within the same thread!
          */
        explicit WLock(const WLock<T>& p) : obj(p.obj) {}

	      /** Destructor. The write lock is released when the WLock object is 
          * deleted. */
  	    ~WLock() {LockManager::getManager().releaseWriteLock(obj);}

        /** Returns a pointer to the locked object. */
        T* getObject() const {return obj;}

        T& operator*() const {return *obj;}
        T* operator->() const {return obj;}

      private:
	      /** A reference to the object being locked. */
        T* obj;
    };

    /** This template function can generate a factory method for objects that
      * can be constructed with their default constructor.  */
    template <class T> static Object* createDefault() 
      {return new T();}

    /** This template function can generate a factory method for objects that
      * need a string argument in their constructor. */
    template <class T> static Object* createString(string n) 
      {return new T(n);}

  private:
    /** This is a pointer to a object maintaining the locking status.<br>
      * The Lock object is assigned from a pool when required.
      */
    Lock *lock;
};


//
// RED-BLACK TREE CLASSES
//

/** This class implements a binary tree data structure. It is used as a
  * container for entities keyed by their name.
  * Technically, the data structure can be described as an red-black tree
  * with intrusive tree nodes.
  * @see HasName
  */
class Tree : public NonCopyable
{
  public:
    /** The algorithm assigns a color to each node in the tree. The color is
      * used to keep the tree balanced.
      * A node with color 'none' is a node that hasn't been inserted yet in
      * the tree.
      */
    enum NodeColor { red, black, none };

    /** This class represents a node in the tree. Elements which we want to
      * represent in the tree will need to inherit from this class, since
      * this tree container is intrusive.
      */
    class TreeNode
    {
      friend class Tree;

      public:
        /** Destructor. */
        virtual ~TreeNode() {}

        /** Returns the name of this node. This name is used to sort the
          * nodes. */
        const string& getName() const {return nm;}

        /** Constructor. */
        TreeNode(const string& n) : nm(n), color(none)
        {
          if (n.empty())
            throw DataException("Can't create entity without name");
        }

        /** Return a pointer to the node following this one. */
        TreeNode* increment() const
        {
          TreeNode *node = const_cast<TreeNode*>(this);
          if (node->right != NULL)
          {
            node = node->right;
            while (node->left != NULL) node = node->left;
          }
          else
          {
            TreeNode* y = node->parent;
            while (node == y->right)
            {
              node = y;
              y = y->parent;
            }
            if (node->right != y) node = y;
          }
          return node;
        }

        /** Return a pointer to the node preceding this one. */
        TreeNode* decrement() const 
        {
          TreeNode *node = const_cast<TreeNode*>(this);
          if (node->color == red && node->parent->parent == node)
            node = node->right;
          else if (node->left != NULL)
          {
            TreeNode* y = node->left;
            while (y->right != NULL) y = y->right;
            node = y;
          }
          else
          {
            TreeNode* y = node->parent;
            while (node == y->left)
            {
              node = y;
              y = y->parent;
            }
            node = y;
          }
          return node;
        }

      private:
        /** Constructor. */
        TreeNode() {}

        /** Name. */
        string nm;

        /** Color of the node. This is used to keep the tree balanced. */
        NodeColor color;

        /** Pointer to the parent node. */
        TreeNode* parent;

        /** Pointer to the left child node. */
        TreeNode* left;

        /** Pointer to the right child node. */
        TreeNode* right;
    };

    /** Default constructor. */
    Tree(bool b = false) : count(0), clearOnDestruct(b)
    {
      // Color is used to distinguish header from root, in iterator.operator++
      header.color = red;
      header.parent = NULL;
      header.left = &header;
      header.right = &header;
    }

    // Destructor.
    // The destructor is called 
    ~Tree() { if(clearOnDestruct) clear(); }

    /** Returns an iterator to the start of the list.<br>
      * The user will need to take care of properly acquiring a read lock on
      * on the tree object. @todo the iterator needs proper locking
      */
    TreeNode* begin() const {return const_cast<TreeNode*>(header.left);}

    /** Returns an iterator pointing beyond the last element in the list.<br>
      * The user will need to take care of properly acquiring a read lock on
      * on the tree object.
      */
    TreeNode* end() const {return const_cast<TreeNode*>(&header);}

    /** Returns true if the list is empty.
      * Its complexity is O(1). */
    bool empty() const 
    {
      LockManager::getManager().obtainReadLock(l);
      bool result = (header.parent == NULL);
      LockManager::getManager().releaseReadLock(l);
      return result;
    }

    /** This method returns the number of nodes inserted in this tree.
      * Its complexity is O(1).
      * In other words:
      *   - avoid calling it too often for large lists.
      *   - Cache the results if possible.
      *   - Use the method empty() if you only want to check whether the
      *     list is empty or not.
      */
    size_t size() const
    {
      LockManager::getManager().obtainReadLock(l);
      size_t result = count;
      LockManager::getManager().releaseReadLock(l);
      return result;
    }

    /** Verifies the integrity of the tree and returns true if all is okay. */
    void verify() const;

    /** Remove all elements from the tree. */
    void clear();

    /** Remove a node from the tree. */
    void erase(TreeNode* x);

    /** Search for an element in the tree. Profiling shows this function has
      * a significant impact on the cpu time (mainly because of the string
      * comparisons), and has been optimized as much as possible.
      */
    TreeNode* find(const string& k) const
    {
      LockManager::getManager().obtainReadLock(l);
      int comp;
	    for (TreeNode* x = header.parent; x; x = comp<0 ? x->left : x->right)
      {
		    comp = k.compare(x->nm);
		    if (!comp) return x;
	    }
      TreeNode* result = end();
      LockManager::getManager().releaseReadLock(l);
      return result;
    }

    /** Find the element with this given key or the element
      * immediately preceding it. */
    TreeNode* findLowerBound(const string& k) const
    {
      LockManager::getManager().obtainReadLock(l);
      TreeNode* lower = end();
      for (TreeNode* x = header.parent; x;)
      {
        int comp = k.compare(x->nm);
        if (!comp) 
        {
          LockManager::getManager().releaseReadLock(l);
          return x; // Found
        }
        if (comp<0) x = x->left;
        else lower = x, x = x->right;
      }
      LockManager::getManager().releaseReadLock(l);
      return lower;    
    }

    /** Find the element with this given key or the element
      * immediately preceding it.<br>
      * The second argument is a boolean that is set to true when the 
      * element is found in the list.
      */
    TreeNode* findLowerBound(const string& k, bool* f) const
    {
      LockManager::getManager().obtainReadLock(l);
      TreeNode* lower = end();
      for (TreeNode* x = header.parent; x;)
      {
        int comp = k.compare(x->nm);
        if (!comp)
        {
          // Found
          *f = true;
          LockManager::getManager().releaseReadLock(l);
          return x; 
        }
        if (comp<0) x = x->left;
        else lower = x, x = x->right;
      }
      *f = false;
      LockManager::getManager().releaseReadLock(l);
      return lower;
    }

    /** Insert a new node in the tree. */
    TreeNode* insert(TreeNode* v) {return insert(v, NULL);}

    /** Insert a new node in the tree. The second argument is a hint on
      * the proper location in the tree.
      * Profiling shows this function has a significant impact on the cpu
      * time (mainly because of the string comparisons), and has been
      * optimized as much as possible.
      */
    TreeNode* insert(TreeNode* v, TreeNode* hint);

  private:
    /** Restructure the tree such that the depth of the branches remains
      * properly balanced. This method is called during insertion. */
    inline void rebalance(TreeNode* x);

    /** Rebalancing operation used during the rebalancing. */
    inline void rotateLeft(TreeNode* x);

    /** Rebalancing operation used during the rebalancing. */
    inline void rotateRight(TreeNode* x);

    /** Method used internally by the verify() method. */
    unsigned int countBlackNodes(TreeNode* node) const
    {
      unsigned int sum = 0;
      for ( ; node != header.parent; node=node->parent)
        if (node->color == black) ++sum;
      return sum;
    }

    TreeNode* minimum(TreeNode* x) const
    {
      while (x->left) x = x->left;
      return x;
    }

    TreeNode* maximum(TreeNode* x) const
    {
      while (x->right) x = x->right;
      return x;
    }

    /** This node stores the following data:
      *  - parent: root of the tree.
      *  - left: leftmost element in the tree.
      *  - right: rightmost element in the tree.
      *  - this node itself is used as an element beyond the end of the list.
      */
    TreeNode header;

    /** Stores the number of elements in the tree. */
    size_t count;

    /** Controls concurrencny during use of the tree. */
    Lock l;

    /** Controls whether the destructor needs to be clear all objects in the 
      * tree in its destructor.<br>
      * The default is to skip this cleanup! This is fine when you are dealing
      * with a static tree that lives throughout your program.<br>
      * When you create a tree with a shorter lifespan, you'll need to pass
      * the constructor 'true' as argument in order to avoid memory leaks.
      */
    bool clearOnDestruct;
};


//
// UTILITY CLASS "COMMAND": for executing & undoing actions
//

/** This is the abstract base class for all commands. All changes in the system
  * state are expected to be wrapped in a command object. The execute() and
  * undo() methods update the model.<br>
  * Adhering to this principle make is easy to trace, time and log changes
  * appropriately.<br>
  * Command objects can't be persisted.
  */
class Command : public Object
{
  friend class CommandList;
  friend class CommandIf;
  public:
    /** This structure defines a boolean value that can be set to TRUE,
      * FALSE or INHERITed from a higher level.
      * - INHERIT: Inherit the value from a higher level list.
      * - YES: true = 1
      * - NO: false = 0
      */
    enum inheritableBool {
      INHERIT = -1,
      YES = 0,
      NO = 1
    };

    /** Default constructor. The creation of a command should NOT execute the
      * command yet. The execute() method needs to be called explicitly to
      * do so.
      */
    Command() : verbose(INHERIT), owner(NULL), next(NULL) {};

    /** This method is used to actually execute the action.<br>
      * A couple of notes on how this method should be implemented by the
      * subclasses:
      *   - Calling the method multiple times is harmless and results in the
      *     same state change as calling it only once.
      */
    virtual void execute() = 0;

    /** This method is undoing the state change of the execute() method.<br>
      * Reversing the action is not possible for all commands. Command
      * subclasses should override the undo() and undoable() method in case
      * they are reversible.<br>
      * A couple of notes on how this method should be implemented by the
      * subclasses:
      *   - Calling the undo() method is harmless if the execute() hasn't
      *     been called yet.
      *   - Calling the undo() method multiple times is harmless and results
      *     in the same state change as calling it only once.
      */
    virtual void undo()
    {clog << "Warning: Can't undo command" << getDescription() << endl;}

    /** Returns true if the execution of this command can be undone. */
    virtual bool undoable() const {return false;}

    virtual void endElement(XMLInput& pIn, XMLElement& pElement);
    virtual string getDescription() const {return "No description available";}
    virtual ~Command() {};

    /** Returns whether verbose output is required during the execution of
      * the command. */
    bool getVerbose() const;

    /** Controls whether verbose output will be generated during execution. */
    void setVerbose(bool b) {verbose = (b ? YES : NO);}

    static const MetaCategory metadata;

  private:
    /** Specifies whether the execution of the command should remain silent
      * (which is the default), or whether verbose output on the command
      * execution is requested.
      * The default value is to inherit from a higher level, and false if
      * unspecified.
      */
    inheritableBool verbose;

    /** Points to the commandlist which owns this command. The default value
      * is NULL, meaning there is no owner. */
    Command *owner;

    /** Points to the next command in the owner command list. The commands of
      * command list are chained in a singly linked list data structure.*/
    Command *next;
};


/** This class allows conditional execution of commands.<br>
  * The condition is an expression that is evaluated on the operating system.
  */
class CommandIf : public Command
{
  private:
    /** Command to be executed if the condition returns true. */
    Command *thenCommand;

    /** Command to be executed if the condition returns false. */
    Command *elseCommand;

    /** Condition expression. */
    string condition;

  public:
    /** Returns true if both the if- and else-command are undoable if they
      * are specified. */
    bool undoable() 
    {
      return (thenCommand ? thenCommand->undoable() : true) 
        && (elseCommand ? elseCommand->undoable() : true);
    }

    /** Undoes either the if- or the else-clause, depending on the 
      * condition.<br>
      * Note that calling execute() before undo() isn't enforced. 
      */
    void undo();

    /** Executes either the if- or the else-clause, depending on the 
      * condition. */
    void execute();

    /** Returns a descriptive string. */
    string getDescription() const {return "Command if";}

    /** Default constructor. */
    explicit CommandIf() : thenCommand(NULL), elseCommand(NULL) {}

    /** Destructor. */
    virtual ~CommandIf() 
    {
      delete thenCommand;
      delete elseCommand;
    }

    /** Returns the condition statement. */
    string getCondition() {return condition;}

    /** Updates the condition. */
    void setCondition(const string s) {condition = s;}

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandIf);}

    void beginElement(XMLInput&, XMLElement& pElement);
    void endElement(XMLInput& pIn, XMLElement& pElement);
};


/** This class is used to group a series commands together. This class
  * implements the "composite" design pattern in order to get an efficient
  * and intuitive hierarchical grouping of tasks.<br>
  * A command list can be executed in three different modes:
  *   - Run the commands in parallel with each other, in seperate threads.<br>
  *     This is achieved by setting the sequential field to false.
  *   - Run the commands in sequence, and abort the command sequence when one
  *     of the commands in the list fails.<BR>
  *     This mode requires the sequential field to be set to true, and the
  *     AbortOnError field to true.
  *   - Run the commands in sequence, and continue the command sequence when
  *     some commands in the sequence fail.<BR>
  *     This mode requires the sequential field to be set to true, and the
  *     AbortOnError field to false.
  * Currently Pthreads and Windows threads are supported as the implementation 
  * of the multithreading.
  */
class CommandList : public Command
{
  private:
    /** Points to the first command in the list.
      * Following commands can be found by following the nextCommand pointers
      * on the commands.
      * The commands are this chained in a single linked list data structure.
      */
    Command* firstCommand;

    /** Points to the last command in the list. */
    Command* lastCommand;

    /** Current command to be executed. */
    Command* curCommand;

    /** Mutex to protect the curCommand data field during multi-threaded 
      * execution. 
      * @see selectCommand
      */
    Mutex lock;

    /** Specifies whether the command list is undoable or not. */
    bool can_undo;

    /** Specifies the maximum number of commands in the list that can be 
      * executed in parallel. 
      * The default value is 1, i.e. sequential execution.<br>
      * The value of this field is NOT inherited from parent command lists.<br>
      * Note that the maximum applies to this command list only, and it isn't
      * a system-wide limit on the creation of threads.
      */
    int maxparallel;

    /** Specifies whether or not a single failure aborts the complete command
      * list. The value is inherited from parent command lists, and will
      * default to true if left unspecified.
      * Note that this field is only relevant in case of sequential execution
      * of the command list.
      */
    inheritableBool abortOnError;

    /** This functions runs a single command execution thread. It is used as
      * a holder for the main routines of a trheaded routine. 
      */
#if defined(HAVE_PTHREAD_H) || !defined(MT)
     static void* wrapper(void *arg);
#else
     static unsigned __stdcall wrapper(void *);
#endif

    /** This method selects the next command to be executed.
      * @see wrapper
      */
    Command* selectCommand();

  public:
    /** Returns the number of commands stored in this list. */
    int getNumberOfCommands() const
    {
      int cnt = 0;
      for(Command *i=firstCommand; i; i=i->next) ++cnt;
      return cnt;
    }

    /** Append an additional command to the end of the list. */
    void add(Command* c);

    /** Undoes all actions on the list. At the end it also clears the list of
      * actions. If one of the actions on the list is not undo-able, the whole
      * list is non-undoable and a warning message will be printed.
      */
    void undo() {undo(NULL);}

    /** Undoes all actions in the list beyond the argument and clear the list 
      * of actions.<br>
      * As soon as one of the actions on the list is not undo-able or the 
      * execution is not sequential, the undo is aborted and a warning message 
      * is printed.<br>
      * There is no need that the actions have actually been executed before 
      * the undo() is called.
      */
    void undo(Command *c);

    /** Commits all actions on its list. At the end it also clear the list
      * of actions. */
    void execute();

    /** Returns whether or not a single failure aborts the complete command
      * list. */
    bool getAbortOnError() const;

    /** If this field is set to true the failure of a single command in the
      * list will abort the complete list of command.<br>
      * If set to false, the remaining commands will still be run in case
      * of a failure.
      */
    void setAbortOnError(bool b) {abortOnError = (b ? YES : NO);}

    /** Returns whether the command list processes its commands sequentially or
      * in parallel. The default is sequentially, and this field is NOT
      * inherited down nested command list hierarchies. */
    int getMaxParallel() const {return maxparallel;}

    /** Updates whether the command list process its commands sequentially or
      * in parallel. */
    void setMaxParallel(int b) 
    {
      if (b<1) 
        throw DataException("Invalid number of parallel execution threads");
#ifndef MT
      maxparallel = (b>1 ? 1 : b);
#else
      // Impose a hard limit of twice the number of available processors.
      int max = Environment::getProcessors() * 2;
      maxparallel = (b>max ? max : b);
#endif
    }

    /** Returns whether this command can be undone or not. */
    bool undoable() const {return can_undo;}

    /** Returns true when all commands beyond the argument can be undone. */
    bool undoable(const Command *c) const;

    /** Returns a descriptive string on the command list. */
    string getDescription() const {return "Command list";}

    /** Returns true if no commands have been added yet to the list. */
    bool empty() const {return firstCommand==NULL;}

    /** Default constructor. */
    explicit CommandList() : firstCommand(NULL), lastCommand(NULL), 
      curCommand(NULL), can_undo(true), maxparallel(1), 
      abortOnError(INHERIT) {}

    /** Destructor. An actionlist should only be deleted when all of its
      * actions have been committed or undone. If this is not the case a
      * warning will be printed.
      */
    virtual ~CommandList();

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandList);}

    void beginElement(XMLInput&, XMLElement& pElement);
    void endElement(XMLInput& pIn, XMLElement& pElement);
};


/** This command allows a user to run a system command on your operating
  * system. The command will spawn a child process to execute the command, and
  * will wait for that process to finish before continue.
  * The class is using the standard C function system() to spawn the command.
  * The behavior of this function will depend on your platform and the
  * compiler used: the command shell spawned will vary (e.g. cmd, /bin/sh, ...)
  * and the exit codes returned are also not standardized.
  * Note that access to this command can pose a <B> security threat</B>! It
  * allows anybody with access to the planner application to run operating
  * system commands with the same user rights as the planner application.
  */
class CommandSystem : public Command
{
  private:
    /** System command to be executed. */
    string cmdLine;

  public:
    /** Constructor.
      * @param cmd Command line to execute on your operating system.
      */
    explicit CommandSystem(const string& cmd) : cmdLine(cmd) {};

    /** Default constructor. */
    explicit CommandSystem() {};

    /** Updates the command line to be executed.
      * @param cmd Command line to execute on your operating system.
      */
    void setCmdLine(const string& cmd) {cmdLine = cmd;}

    /** Returns the command line that will be run. */
    string getCmdLine() {return cmdLine;}

    /** Executes the command line.
      * @exception RuntimeException Generated when the command can't be 
      *    launched, or when it's exit code is non-zero.
      */
    void execute();

    void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const 
      {return "Run operating system command '" + cmdLine + "'";}

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandSystem);}
};


/** This class dynamically loads a shared library in Frepple.
  * After loading, the function "initialize" is executed. 
  * The function works on the following platforms:
  *  - Windows
  *  - Linux
  *  - Unix systems supporting the dlopen function in the standard way.
  *    Some unix systems have other or deviating APIs. Actually, this is a
  *    messy topic. :-<
  */
class CommandLoadLibrary : public Command
{
  public:
    /** Type for storing parameters. */
    typedef map<string,string> ParameterList;

    /** Constructor.
      * @param libname File name of the library
      */
    explicit CommandLoadLibrary(const string& libname) : lib(libname) {};

    /** Default constructor. */
    explicit CommandLoadLibrary() {};

    /** Updates the command line to be executed.<br>
      * @param libname Path of the library to be loaded
      */
    void setLibraryName(const string& libname) {lib = libname;}

    /** Returns the command line that will be run. */
    string getLibraryName() {return lib;}

    /** Load the library, and execute the initialize() method.
      * @exception RuntimeException When the library can't be loaded 
      *     or when the initialize() method doesn't exist in the library.
      */
    void execute();

    void endElement(XMLInput& pIn, XMLElement& pElement);
    string getDescription() const {return "Loading shared library " + lib;}

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CommandLoadLibrary);}

  private:
    /** Name of the library to be loaded. */
    string lib;

    /** List of parameters passed to the library. */
    ParameterList parameters;

    /** Temporary string used during the reading of the parameters. */
    string tempName;

    /** Temporary string used during the reading of the parameters. */
    string tempValue;
};


//
// INPUT PROCESSING CLASSES
//

/** This abstract class is the used for defining classes that are used to
  * implement processing functionality linked to XML processing
  * instructions.<br>
  * Such a processing instruction looks as follows:<br>
  *   \<?TARGET data ?\>  <br>
  * Upon reading this from the XML input, the parser will look for the class
  * registered with base "INSTRUCTION" and type "TARGET". The parser will
  * instantiate an object of that class and call the method
  * processInstruction on it. The call will include a pointer to the parser
  * and the data string.<br>
  * Note that these instructions are never validated by the parser against
  * an XML schema. They are only processed inside frepple, and extreme care
  * should be taken to develop robust and secure processing instructions.
  * @see XMLInput
  * @see XMLInput::processingInstruction
  */
class XMLinstruction : public NonCopyable
{
  public:
    /** Handler function called by the XML parser. */
    virtual void processInstruction(XMLInput &i, const char *d) = 0;

    /** Destructor. */
    virtual ~XMLinstruction() {}

    /** Metadata, registering the base tag "INSTRUCTION". */
    static const MetaCategory metadata;
};


/** This class will read in an XML-file and call the appropriate handler
  * functions of the Object classes and objects.<br>
  * This class is implemented based on the Xerces SAX XML parser.
  * For debugging purposes a flag is defined at the start of the file
  * "status.cpp". Uncomment the line and recompile to use it.
  */
class XMLInput : public NonCopyable,  private DefaultHandler
{
  private:
    /** A pointer to an XML parser for processing the input. */
    SAX2XMLReader* parser;

    /** This type defines the different states the parser can have. */
    enum state {READOBJECT, IGNOREINPUT, SHUTDOWN, INIT};

    /** This variable defines the maximum depth of the object creation stack.
      * This maximum is intended to protect us from malicious malformed
      * xml-documents, and also for allocating efficient data structures for
      * the parser.
      */
    const unsigned short maxdepth;

    /** A list of commands that are to be executed at the end of processing
      * the input data. */
    CommandList cmds;

    /** Stack of states. */
    stack <state> states;

    /** Previous object in stack. */
    Object* prev;

    /** Stack of pairs. The pairs contain:
      *  - A pointer to an event handler object. The beginElement and
      *    endElement methods of this object will be called.
      *  - A user definable pointer. The purpose of this pointer is to store
      *    status information between calls to the handler.
      */
    stack< pair<Object*,void*> > m_EHStack;

    /** Stack of elements.
      * The expression m_EStack[numElements+1] returns the current element.
      * The expression m_EStack[numElements] returns the parent element.
      * @see numElements
      */
    vector<XMLElement> m_EStack;

    /** A variable to keep track of the size of the element stack. It is used
      * together with the variable m_EStack.
      * @see m_EStack
      */
    short numElements;

    /** This field counts how deep we are in a nested series of ignored input.
      * It is represented as a counter since the ignored element could contain
      * itself.
      */
    unsigned short ignore;

    /** Hash value of the current element. */
    stack<hashtype> endingHashes;

    /** This variable is normally false. It is switched to true only a) in
      * the method endElement() of Object objects and b) when an object
      * is processing its closing tag.
      */
    bool objectEnded;

    /** This field controls whether we continue processing after data errors
      * or whether we abort processing the remaining XML data.<br>
      * Selecting the right mode is important:
      *  - Setting the flag to false is appropriate for processing large
      *    amounts of a bulk-load operation. In this mode a single, potentially
      *    minor, data problem won't abort the complete process.
      *  - Setting the flag to true is most appropriate to process smal and
      *    frequent messages from client applications. In this mode client
      *    applications are notified about data problems.
      *  - The default setting is true, in order to provide a maximum level of
      *    security for the application.
      */
    bool abortOnDataException;

    /** This is a pointer to the attributes.
      * See the xerces API documentation for further information on the usage
      * of the attribute list.
      */
    const Attributes* attributes;

    /** Handler called when a new element tag is encountered.
      * It pushes a new element on the stack and calls the current handler.
      */
    void startElement (const XMLCh* const, const XMLCh* const,
      const XMLCh* const, const Attributes&);

    /** Handler called when closing element tag is encountered.
      * If this is the closing tag for the current event handler, pop it
      * off the handler stack. If this empties the stack, shut down parser.
      * Otherwise, just feed the element with the already completed
      * data section to the current handler, then pop it off the element
      * stack.
      */
    void endElement
      (const XMLCh* const, const XMLCh* const s, const XMLCh* const qname);

    /** Handler called when character data are read in.
      * The data string is add it to the current element data.
      */
    void characters(const XMLCh *const, const unsigned int);

    /** Handler called by Xerces in fatal error conditions. It throws an
      * exception to abort the parsing procedure. */
    void fatalError (const SAXParseException& e) {throw e;}

    /** Handler called by Xercess when reading a processing instruction. The
      * handler looks up the target in the repository and will call the
      * registered XMLinstruction.
      * @see XMLinstruction
      */
    void processingInstruction (const XMLCh *const, const XMLCh *const);

    /** Handler called by Xerces in error conditions. It throws an exception
      * to abort the parsing procedure. */
    void error (const SAXParseException& e) {throw e;}

    /** Handler called by Xerces for warnings. */
    void warning (const SAXParseException&);

    /** This method cleans up the parser state to get it ready for processing
      * a new document. */
    void reset();

  public:
    /** Constructor.
      * @param maxNestedElmnts Defines the maximum depth of elements an XML
      * document is allowed to have. The default is 20.
      */
    XMLInput(unsigned short maxNestedElmnts = 20)
     : parser(NULL), maxdepth(maxNestedElmnts), m_EStack(maxNestedElmnts+2),
       numElements(-1), ignore(0), objectEnded(false),
       abortOnDataException(true), attributes(NULL) {}

    /** Destructor. */
    virtual ~XMLInput() {reset();}

    /** Return a pointer to an array of character pointer which point
      * to the attributes. See the xerces documentation if this description
      * doesn't satisfy you...
      */
    const Attributes* getAttributes() const {return attributes;}

    /** Redirect event stream into a new Object.<br>
      * It is also possible to pass a NULL pointer to the function. In
      * that situation, we simple ignore the content of that element.<br>
      * Important: The user is reponsible of making sure the argument 
      * object has a proper write-lock. The release of that lock is handled
      * by the parser.
      */
    void readto(Object*);

    /** Abort the parsing.
      * The actual shutdown cannot be called inside a SAX handler function,
      * so actual shutdown is deferred until the next iteration of the feed
      * loop.
      */
    void shutdown();

    /** Ignore an element. */
    void IgnoreElement() {readto(NULL);}

    /** Returns true if the current object is finishing with the current
      * tag. This method should only be used in the endElement() method. */
    bool isObjectEnd() {return objectEnded;}

    /** Return a pointer to the current object being read in.  */
    Object* getCurrentObject() const {return m_EHStack.top().first;}

    /** Return a pointer to the previous object being read in.
      * In a typical use the returned pointer will require a dynamic_cast
      * to a subclass type.
      * A typical use will be as follows:
      * E.g.
      *   Operation *o = dynamic_cast<Operation*>(pIn.getPreviousObject());
      *   if (o) doSomeThing(o);
      *   else throw LogicException("Incorrect object type");
      */
    Object* getPreviousObject() const {return prev;}

    /** Returns a reference to the parent element. */
    const XMLElement& getParentElement() const
      {return m_EStack[numElements>0 ? numElements : 0];}

    /** Returns a reference to the current element. */
    const XMLElement& getCurrentElement() const
      {return m_EStack[numElements>-1 ? numElements+1 : 0];}

    /** This is the core parsing function, which triggers the XML parser to
      * start processing the input. It is normally called from the method
      * parse(Object*) once a proper stream has been created.
      * @see parse(Object*)
      */
    void parse(InputSource&, Object*, bool=false);

    /** Updates the user definable pointer. This pointer is used to store
      * status information between handler calls. */
    void setUserArea(void* v) {m_EHStack.top().second = v;}

    /** Returns the user definable pointer. */
    void* getUserArea() const {return m_EHStack.top().second;}

    /** Updates whether we ignore data exceptions or whether we abort the
      * processing of the XML data stream. */
    void setAbortOnDataError(bool i) {abortOnDataException = i;}

    /** Returns the behavior of the parser in case of data errors. When true
      * is returned, the processing of the XML stream continues after a data
      * exception. False indicates that the processing of the XML stream is
      * aborted.
      */
    bool getAbortOnDataError() const {return abortOnDataException;}

    /** Return a reference to the list of commands. */
    CommandList& getCommands() {return cmds;}

  protected:
    /** The real parsing job is delegated to subclasses.
      * Subclass can then define the specifics for parsing a flat file,
      * a string, a SOAP message, etc...
      * @exception RuntimeException Thrown in the following situations:
      *    - the xml-document is incorrectly formatted
      *    - the xml-parser librabry can't be initialized
      *    - no memory can be allocated to the xml-parser
      * @exception DataException Thrown when the data can't be processed
      *   normally by the objects being created or updated.
      */
    virtual void parse(Object* s, bool b=false) {assert(false);}

    /** Execute the commands that have been read from the input stream. */
    void executeCommands();
};


/** This class is used to read data from a CSV-formatted data - instead
  * of the regular XML-format.
  */
class CSVInput : public XMLinstruction, private DefaultHandler, public Object
{
  private:
    /** Comment character. A line starting with this character will not be 
      * processed and skipped.<br>
      * The default is #.
      */
    char comment;

    /** The character to delimit fields in the data input.
      * The default is ,
      */
    char fieldseparator;

  public:
    void processInstruction(XMLInput &i, const char *d);

    /** Default constructor. */
    CSVInput() : comment('#'), fieldseparator(',') {}

    const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(CSVInput);}

    char getFieldSeparator() const {return fieldseparator;}
    void setFieldSeparator(const char c) {fieldseparator = c;}
    char getCommentChar() const {return comment;}
    void setCommentChar(const char c) {comment = c;}

    void readTemplate
      (string &header, string &rep, string &footer, Object *pRoot);

  private:
    void endElement(XMLInput& pIn, XMLElement& pElement) {};

    /** Handler called when a new element tag is encountered.
      * It pushes a new element on the stack and calls the current handler.
      */
    void startElement (const XMLCh* const, const XMLCh* const,
      const XMLCh* const, const Attributes&);

    /** Handler called when closing element tag is encountered.
      * If this is the closing tag for the current event handler, pop it
      * off the handler stack. If this empties the stack, shut down parser.
      * Otherwise, just feed the element with the already completed
      * data section to the current handler, then pop it off the element
      * stack.
      */
    void endElement
      (const XMLCh* const, const XMLCh* const s, const XMLCh* const qname);

    /** Handler called when character data are read in.
      * The data string is add it to the current element data.
      */
    void characters(const XMLCh *const, const unsigned int);

    /** Handler called by Xerces in fatal error conditions.It throws an 
      * exception to abort the parsing procedure. */
    void fatalError (const SAXParseException& e) {throw e;}

    /** Handler called by Xerces in error conditions. It throws an exception
      * to abort the parsing procedure. */
    void error (const SAXParseException& e) {throw e;}

    /** Handler called by Xerces for warnings. */
    void warning (const SAXParseException&);
};


/** This class reads XML data from a string. */
class XMLInputString : public XMLInput
{
  public:
    /** Default constructor. */
    XMLInputString(string& s) : data(s) {};

    /** Parse the specified string. */
    void parse(Object* pRoot, bool v = false)
    {
      /* The MemBufInputSource expects the number of bytes as second parameter.
       * In our case this is the same as the number of characters, but this
       * will not apply any more for character sets with multi-byte
       * characters.
       */
      MemBufInputSource a(
        reinterpret_cast<const XMLByte*>(data.c_str()),
        static_cast<const unsigned int>(data.size()),
        "memory data",
        false);
      XMLInput::parse(a,pRoot,v);
    }

  private:
    /** String containing the data to be parsed. Note that NO local copy of the
      * data is made, only a reference is stored. The class relies on the code
      * calling the command to correctly create and destroy the string being
      * used.
      */
    const string data;
};


/** This class reads XML data from an HTTP connection.<br>
  * The Xerces parser supports only the simplest possible setup: no proxy,
  * no caching, no ssl, no authentication, etc...  
  */
class XMLInputURL : public XMLInput
{
  public:
    /** Default constructor. */
    XMLInputURL(const string& s) : url(s) {};

    /** Parse the specified url. */
    void parse(Object* pRoot, bool v = false)
    {
      if (url.empty()) 
        throw DataException("Missing URL when parsing remote XML"); 
      URLInputSource a(reinterpret_cast<const XMLCh *>(NULL), url.c_str());
      XMLInput::parse(a,pRoot,v);
    }

  private:
    /** The url to be loaded. */
    const string url;
};


/** This class reads XML data from a file system.
  * The filename argument can be the name of a file or a directory.
  * If a directory is passed, all files with the extension ".xml"
  * will be read from it. Subdirectories are not recursed.
  */
class XMLInputFile : public XMLInput
{
  public:
    /** Constructor. The argument passed is the name of a
      * file or a directory. */
    XMLInputFile(const string& s) : filename(s) {};

    /** Default constructor. */
    XMLInputFile() {};

    /** Update the name of the file to be processed. */
    void setFileName(const string& s) {filename = s;}

    /** Returns the name of the file or directory to process. */
    string getFileName() {return filename;}

    /** Parse the specified file.
      * When a directory was passed as the argument a failure is
      * flagged as soon as a single file returned a failure. All
      * files in an directory are processed however, regardless of
      * failure with one of the files.
      * @exception RuntimeException Generated in the following conditions:
      *    - no input file or directory has been specified.
      *    - read access to the input file is not available
      *    - the program doesn't support reading directories on your platform
      */
    void parse(Object*, bool=false);

  private:
    /** Name of the file to be opened. */
    string filename;
};


//
//  UTILITY CLASSES "HASNAME", "HASHIERARCHY", "HASDESCRIPTION"
//


/** This is the base class for the main objects.
 *  Instances of this class have the following properties:
 *    - Have a unique name.
 *    - A hashtable (keyed on the name) is maintained as a container with 
 *      all active instances.
 */
template <class T> class HasName : public NonCopyable, public Tree::TreeNode
{
  private:
    /** Maintains a global list of all created entities. The list is keyed
      * by the name. */
    static DECLARE_EXPORT Tree st;
    typedef T* type;

  public:
    /** This class models an STL-like iterator that allows us to iterate over
      * the named entities in a simple and safe way.<br>
      * Objects of this class are created by the begin() and end() functions.
      */
    class iterator
    {
      public:
        /** Constructor. */
        iterator(Tree::TreeNode* x) : node(x) {}

        /** Copy constructor. */
        iterator(const iterator& it) {node = it.node;}

        /** Return the content of the current node. */
        T& operator*() const {return *static_cast<T*>(node);}

        /** Return the content of the current node. */
        T* operator->() const {return static_cast<T*>(node);}

        /** Pre-increment operator which moves the pointer to the next
          * element. */
        iterator& operator++() {node = node->increment(); return *this;}

        /** Post-increment operator which moves the pointer to the next
          * element. */
        iterator operator++(int)
        {
          Tree::TreeNode* tmp = node;
          node = node->increment();
          return tmp;
        }

        /** Pre-decrement operator which moves the pointer to the previous
          * element. */
        iterator& operator--() {node = node->decrement(); return *this;}

        /** Post-decrement operator which moves the pointer to the previous
          * element. */
        iterator operator--(int)
        {
          Tree::TreeNode* tmp = node;
	        node = node->decrement();
	        return tmp;
        }

        /** Comparison operator. */
        bool operator==(const iterator& y) const {return node==y.node;}

        /** Inequality operator. */
        bool operator!=(const iterator& y) const {return node!=y.node;}

      private:
        Tree::TreeNode* node;
    };

    /** Returns an STL-like iterator to the end of the entity list. */
    static iterator end() {return st.end();}

    /** Returns an STL-like iterator to the start of the entity list. */
    static iterator begin() {return st.begin();}

    /** Returns false if no named entities have been defined yet. */
    static bool empty() {return st.empty();}

    /** Returns the number of defined entities. */
    static size_t size() {return st.size();}

    /** Debugging method to verify the validity of the tree.
      * An exception is thrown when the tree is corrupted. */
    static void verify() {st.verify();}

    /** Deletes all elements from the list. */
    static void clear() {st.clear();}

    /** One and only constructor. */
    explicit HasName(const string& n) : Tree::TreeNode(n) {}

    /** Destructor. */
    ~HasName() {st.erase(this);}

    /** Find an entity given its name. In case it can't be found, a NULL
      * pointer is returned. */
    static T* find(const string& k)
    {
      Tree::TreeNode *i = st.find(k);
      return (i!=st.end() ? static_cast<T*>(i) : NULL);
    }

    /** Find .*/
    static T* findLowerBound(const string& k)
    {
      Tree::TreeNode *i = st.findLowerBound(k);
      return (i!=st.end() ? static_cast<T*>(i) : NULL);
    }

    /** Find .*/
    static T* findLowerBound(const string& k, bool *f)
    {
      Tree::TreeNode *i = st.findLowerBound(k, f);
      return (i!=st.end() ? static_cast<T*>(i) : NULL);
    }

    /** Creates a new entity. */
    static T* add(const string& k)
    {
      Tree::TreeNode *i = st.find(k);
      if (i!=st.end()) return static_cast<T*>(i); // Exists already
      T *t= new T(k);
      st.insert(t);
      return t;
    }

    /** Registers an entity created by the default constructor. */
    static T* add(T* t) {return static_cast<T*>(st.insert(t));}

    /** Registers an entity created by the default constructor. The second
      * argument is a hint: when passing an entity with a name close to
      * the new one, the insertion will be sped up considerably.
      */
    static T* add(T* t, T* hint) {return static_cast<T*>(st.insert(t,hint));}

    void endElement(XMLInput& pIn, XMLElement& pElement) {};

    /** This method is available as a object creation factory for 
      * classes that are using a string as a key identifier, in particular 
      * classes derived from the HasName base class.
      * The following attributes are recognized:
      * - NAME:<br>
      *   Name of the entity to be created/changed/removed.
      *   The default value is "unspecified".
      * - TYPE:<br>
      *   Determines the subclass to be created.
      *   The default value is "DEFAULT".
    	* - ACTION:<br>
      *   Determines the action to be performed on the object.
      *   This can be A (for 'add'), C (for 'change'), AC (for 'add_change') 
      *   or R (for 'remove').
      *   'add_change' is the default value.
      * @see HasName
      */
    static Object* reader (const MetaCategory& cat, const XMLInput& in)
    {
      // Pick up the name attribute. An error is reported if it's missing.
      char* name = XMLString::transcode(
        in.getAttributes()->getValue(Tags::tag_name.getXMLCharacters())
        );
      if (!name) 
      {
        XMLString::release(&name);
        throw DataException("Missing NAME attribute");
      }

      // Pick up the action attribute
      Action act = MetaClass::decodeAction(in.getAttributes());

      // Check if it exists already
      bool found;
      T *i = T::findLowerBound(name, &found);

      // Validate the action
      switch (act)
      {
        case ADD:
          // Only additions are allowed
          if (found)
          {
            XMLString::release(&name);
            throw DataException("Object '" + string(name) + "' already exists.");
          }
          break;

        case CHANGE:
          // Only changes are allowed
          if (!found) 
          {
            string msg = string("Object '") + name + "' doesn't exist.";
            XMLString::release(&name);
            throw DataException(msg);
          }
          XMLString::release(&name);

          // Lock the object, which includes also the callback
          LockManager::getManager().obtainWriteLock(i);
          return i;
         
        case REMOVE:
          // Delete the entity
          if (found) 
          {
            // Send out the notification to subscribers
            LockManager::getManager().obtainWriteLock(i);   // @todo this lock shouldn't trigger callbacks?
            if (i->getType().raiseEvent(i,SIG_REMOVE))
            {
              XMLString::release(&name);
              // Delete the object
              delete i;
              return NULL;
            }
            else
            {
              // The callbacks disallowed the deletion!
              LockManager::getManager().releaseWriteLock(i);
              string msg = string("Can't remove object '") + name + "'";
              XMLString::release(&name);
              throw DataException(msg);
            }
          }
          else
          {
            // Not found
            string msg = string("Can't find object '") + name + "' for removal";
            XMLString::release(&name);
            throw DataException(msg);
          }
        default:
          // case ADD_CHANGE doesn't have special cases.
          ;
      }

      // Return the existing instance
      if (found) 
      {
        // Lock the object, which includes the callbacks
        XMLString::release(&name);
        LockManager::getManager().obtainWriteLock(i);
        return i;
      }

      // Lookup the type in the map
      char* type = XMLString::transcode(
          in.getAttributes()->getValue(Tags::tag_type.getXMLCharacters())
          );
      string type2;
      if (!type && in.getParentElement().isA(cat.grouptag))
      {
        if (in.getCurrentElement().isA(cat.typetag)) type2 = "DEFAULT";
        else type2 = in.getCurrentElement().getName();
      }
      MetaCategory::ClassMap::const_iterator j = 
        cat.classes.find(type ? XMLtag::hash(type) : (type2.empty() ? MetaCategory::defaultHash : XMLtag::hash(type2.c_str())));
      if (j == cat.classes.end())
      {
        string msg = "No type " + string(type ? type : (type2.empty() ? "DEFAULT" : type2.c_str()))
          + " registered for category " + cat.type;
        XMLString::release(&name);
        XMLString::release(&type);
        throw LogicException(msg);
      }

      // Create a new instance
      T* x = dynamic_cast<T*>(j->second->factoryMethodString(name));
      XMLString::release(&type);

      // Run creation callbacks
      // During the callback there is no write lock set yet, since we can
      // assume we are the only ones aware of this new object. We also want
      // to make sure the 'add' signal comes before the 'before_change'
      // callback that is part of the writelock.
      if (!x->getType().raiseEvent(x,SIG_ADD))
      {
        // Creation isn't allowed
        string msg = string("Can't create object") + name;
        delete x;
        XMLString::release(&name);
        throw DataException(msg);
      }
      XMLString::release(&name);

      // Lock the object, which includes the before-change callback
      LockManager::getManager().obtainWriteLock(x);

      // Insert in the tree
      T::add(x, i);
      return x;
    }

    /** A handler that is used to persist the tree. */
    static void writer(const MetaCategory& c, XMLOutput* o)
    {
      if (empty()) return;
      o->BeginObject(*(c.grouptag));
      for (iterator i = begin(); i != end(); ++i)
          o->writeElement(*(c.typetag), *i);
      o->EndObject(*(c.grouptag));
    }
};


/** This is a decorator class for the main objects.
  * Instances of this class have a description, category and sub_category.
  */
class HasDescription
{
  public:
    /** Returns the category. */
    string getCategory() const {return cat;}

    /** Returns the sub_category. */
    string getSubCategory() const {return subcat;}

    /** Returns the getDescription. */
    string getDescription() const {return descr;}

    /** Sets the category field. */
    void setCategory(const string& f) {cat = f;}

    /** Sets the sub_category field. */
    void setSubCategory(const string& f) {subcat = f;}

    /** Sets the description field. */
    void setDescription(const string& f) {descr = f;}

    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

  protected:
    /** Returns the memory size in bytes. */
    size_t memsize() const {return cat.size() + subcat.size() + descr.size();}

  private:
    string cat;
    string subcat;
    string descr;
};


/** This is a base class for the main objects.
  * Instances of this class have the following properties:
  *  - Unique name and global hashtable are inherited from the class HasName.
  *  - Belongs to a hierarchy.
  *  - Instantiations of this template can build up hierarchical trees of
  *    arbitrary depth.
  *  - Each object can have a single parent only.
  *  - Each object has a parent and can have children.
  *    This class thus implements the 'composite' design pattern.
  * The internal data structure is a singly linked linear list, which is
  * efficient provided the number of childre remains limited.
  */
template <class T> class HasHierarchy : public HasName<T>
{
#if  (defined _MSC_VER) || (defined __BORLANDC__)
  // Visual C++ 6.0 and Borland C++ 5.5 seem to get confused with the private
  // template members
  friend class HasHierarchy<T>;
#endif

  public:
    class memberIterator;
    friend class memberIterator;
    /** This class models an STL-like iterator that allows us to iterate over
      * the members.
      * Objects of this class are created by the begin() and end() functions.
      */
    class memberIterator
    {
      public:
        /** Constructor. */
        memberIterator(HasHierarchy<T>* x) : curmember(x) {}

        /** Copy constructor. */
        memberIterator(const memberIterator& it) {curmember = it.curmember;}

        /** Return the content of the current node. */
        T& operator*() const {return *static_cast<T*>(curmember);}

        /** Return the content of the current node. */
        T* operator->() const {return static_cast<T*>(curmember);}

        /** Pre-increment operator which moves the pointer to the next
          * member. */
        memberIterator& operator++()
          {curmember = curmember->next_brother; return *this;}

        /** Post-increment operator which moves the pointer to the next
          * element. */
        memberIterator operator++(int)
        {
          memberIterator tmp = *this;
          curmember = curmember->next_brother;
          return tmp;
        }

        /** Comparison operator. */
        bool operator==(const memberIterator& y) const
          {return curmember == y.curmember;}

        /** Inequality operator. */
        bool operator!=(const memberIterator& y) const
          {return curmember != y.curmember;}

      private:
        /** Points to a member. */
        HasHierarchy<T>* curmember;
    };

    /** The one and only constructor. */
    HasHierarchy(const string& n) : HasName<T>(n), parent(NULL),
      first_child(NULL), next_brother(NULL) {}

    /** Destructor.
      * When deleting a node of the hierarchy, the children will get the
      * current parent as the new parent.
      * In this way the deletion of nodes doesn't create "dangling branches"
      * in the hierarchy. We just "collapse" a certain level.
      */
    ~HasHierarchy();

    memberIterator beginMember() const {return first_child;}

    memberIterator endMember() const {return NULL;}

    /** Returns true if this entity belongs to a higher hierarchical level.
      * An entity can have only a single owner, and can't belong to multiple
      * hierarchies.
      */
    bool hasOwner() const {return parent!=NULL;}

    /** Returns true if this entity has lower level entities belonging to
      * it. */
    bool isGroup() const {return first_child!=NULL;}

    /** Changes the owner of the entity.
      * The argument must be a valid pointer to an entity of the same type.
      * A NULL pointer can be passe to clear the existing owner.
      */
    void setOwner(T* f);

    /** Returns the owning entity. */
    T* getOwner() const {return parent;}

    /** Returns the level in the hierarchy.
      * Level 0 means the entity doesn't have any parent.
      * Level 1 means the entity has a parent entity with level 0.
      * Level "x" means the entity has a parent entity whose level is "x-1".
      */
    unsigned short getHierarchyLevel() const;

    void beginElement(XMLInput&, XMLElement& pElement);
    void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput&, XMLElement&);

  private:
    T *parent;
    T *first_child;
    T *next_brother;
};


//
// ASSOCIATION
//

/** This template class represents a data structure for a load or flow network.
  * A node class has pointers to 2 root classes. The 2 root classes each
  * maintain a singly linked list of nodes.
  * An example to clarify the usage:
  *     class node = a newspaper subscription.
  *     class person = maintains a list of all his scubscriptions.
  *     class newspaper = maintains a list of all subscriptions for it.
  * This data structure could be replaced with 2 linked lists, but this
  * specialized data type consumes considerably lower memory.
  * Reading from the structure is safe in multi-threading mode. Updates to the
  * data structure in a multi-threading mode require the user to properly lock
  * and unlock the container.
  */
template <class A, class B, class C> class Association
{
  public:
    class Node;
  private:
    class List
    {
      friend class Node;
      public:
        C* first;
      public:
        List() : first(NULL) {};
        bool empty() const {return first==NULL;}
    };
  public:
	  class ListA : public List
    {
      public:
        ListA() {};
        class iterator
        {
          protected:
            C* nodeptr;
          public:
            iterator(C* n) : nodeptr(n) {};
            C& operator*() const {return *nodeptr;}
            C* operator->() const {return nodeptr;}
            bool operator==(const iterator& x) const
              {return nodeptr == x.nodeptr;}
            bool operator!=(const iterator& x) const
              {return nodeptr != x.nodeptr;}
            iterator& operator++()
              {nodeptr = nodeptr->nextA; return *this;}
            iterator operator++(int i)
            {
              iterator j = *this;
              nodeptr = nodeptr->nextA;
              return j;
            }
        };
        class const_iterator
        {
          protected:
            C* nodeptr;
          public:
            const_iterator(C* n) : nodeptr(n) {};
            const C& operator*() const {return *nodeptr;}
            const C* operator->() const {return nodeptr;}
            bool operator==(const const_iterator& x) const
              {return nodeptr == x.nodeptr;}
            bool operator!=(const const_iterator& x) const
              {return nodeptr != x.nodeptr;}
            const_iterator& operator++()
              {nodeptr = nodeptr->nextA; return *this;}
            const_iterator operator++(int i)
            {
              const_iterator j = *this;
              nodeptr = nodeptr->nextA;
              return j;
            }
        };
        iterator begin() {return iterator(this->first);}
        const_iterator begin() const {return const_iterator(this->first);}
        iterator end() {return iterator(NULL);}
        const_iterator end() const {return const_iterator(NULL);}
        ~ListA()
        {
          C* next;
          for (C* p=this->first; p; p=next)
          {
            next = p->nextA;
            delete p;
          }
        }
        void erase(const C* n)
        {
          if (!n) return;
          if (n==this->first)
            this->first = n->nextA;
          else
            for (C* p=this->first; p; p=p->nextA)
              if(p->nextA == n)
              {
                p->nextA = n->nextA;
                return;
              }
        }
        size_t size() const
        {
          size_t i(0);
          for (C* p = this->first; p; p=p->nextA) ++i;
          return i;
        }
        C* find(const B* b) const
        {
          for (C* p=this->first; p; p=p->nextA)
            if (p->ptrB == b) return p;
          return NULL;
        }
    };
    class ListB : public List
    {
      public:
        ListB() {};
        class iterator
        {
          protected:
            C* nodeptr;
          public:
            iterator(C* n) : nodeptr(n) {};
            C& operator*() const {return *nodeptr;}
            C* operator->() const {return nodeptr;}
            bool operator==(const iterator& x) const
              {return nodeptr == x.nodeptr;}
            bool operator!=(const iterator& x) const
              {return nodeptr != x.nodeptr;}
            iterator& operator++()
              {nodeptr = nodeptr->nextB; return *this;}
            iterator operator++(int i)
            {
              iterator j = *this;
              nodeptr = nodeptr->nextA;
              return j;
            }
        };
        class const_iterator
        {
          protected:
            C* nodeptr;
          public:
            const_iterator(C* n) : nodeptr(n) {};
            const C& operator*() const {return *nodeptr;}
            const C* operator->() const {return nodeptr;}
            bool operator==(const const_iterator& x) const
              {return nodeptr == x.nodeptr;}
            bool operator!=(const const_iterator& x) const
              {return nodeptr != x.nodeptr;}
            const_iterator& operator++()
              {nodeptr = nodeptr->nextB; return *this;}
            const_iterator operator++(int i)
            {
              const_iterator j = *this;
              nodeptr = nodeptr->nextA;
              return j;
            }
        };
        ~ListB()
        {
          C* next;
          for (C* p=this->first; p; p=next)
          {
            next = p->nextB;
            delete p;
          }
        }
        iterator begin() {return iterator(this->first);}
        const_iterator begin() const {return const_iterator(this->first);}
        iterator end() {return iterator(NULL);}
        const_iterator end() const {return const_iterator(NULL);}
        void erase(const C* n)
        {
          if (!n) return;
          if (n==this->first)
            this->first = n->nextB;
          else
            for (C* p=this->first; p; p=p->nextB)
              if(p->nextB == n)
              {
                p->nextB = n->nextB;
                return;
              }
        }
        size_t size() const
        {
          size_t i(0);
          for (C* p=this->first; p; p=p->nextB) ++i;
          return i;
        }
        C* find(const A* b) const
        {
          for (C* p=this->first; p; p=p->nextB)
            if (p->ptrA == b) return p;
          return NULL;
        }
    };
    class Node
    {
      public:
        A* ptrA;
        B* ptrB;
        C* nextA;
        C* nextB;
      public:
        Node() : ptrA(NULL), ptrB(NULL), nextA(NULL), nextB(NULL) {};
        Node(A* a, B* b, const ListA& al, const ListB& bl)
            : ptrA(a), ptrB(b), nextA(al.first), nextB(bl.first)
        {
          ((ListA&)al).first = static_cast<C*>(this);
          ((ListB&)bl).first = static_cast<C*>(this);
        }
        void setPtrA(A* a, const ListA& al)
        {
          // Don't allow updating an already valid link
          if (ptrA) return;
          ptrA = a;
          nextA = al.first;
          ((ListA&)al).first = static_cast<C*>(this);
        }
        void setPtrB(B* b, const ListB& bl)
        {
          // Don't allow updating an already valid link
          if (ptrB) return;
          ptrB = b;
          nextB = bl.first;
          ((ListB&)bl).first = static_cast<C*>(this);
        }
        void setPtrAB(A* a, B* b, const ListA& al, const ListB& bl)
        {
          setPtrA(a, al);
          setPtrB(b, bl);
        }
        A* getPtrA() const {return ptrA;}
        B* getPtrB() const {return ptrB;}
    };
};


#include "frepple/entity.h"


//
// LIBRARY INITIALISATION
//

/** This class holds functions that used for maintenance of the library.
  * Its static member function 'initialize' should be called BEFORE the
  * first use of any class in the library.
  * The member function 'finialize' will be called automatically at the
  * end of the program.
  */
class LibraryUtils
{
  public:
    static void initialize();
    static void finalize();
  private:
    static bool init;
};

}
#endif  // End of UTILS_H
