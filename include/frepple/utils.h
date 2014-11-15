/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as Objecthed   *
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

/** @file utils.h
  * @brief Header file for auxilary classes.
  *
  * @namespace frepple::utils
  * @brief Utilities for the frePPle core
  */

#ifndef FREPPLE_UTILS_H
#define FREPPLE_UTILS_H

/* Python.h has to be included first.
   For a debugging build on windows we avoid using the debug version of Python
   since that also requires Python and all its modules to be compiled in debug
   mode.
   Visual Studio will complain if system headers are #included both with
   and without _DEBUG defined, so we have to #include all the system headers
   used by pyconfig.h right here.
*/
#if defined(_DEBUG) && defined(_MSC_VER)
#include <stddef.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <errno.h>
#include <ctype.h>
#include <wchar.h>
#include <basetsd.h>
#include <io.h>
#include <limits.h>
#include <float.h>
#include <string.h>
#include <math.h>
#include <time.h>
#undef _DEBUG
#include "Python.h"
#define _DEBUG
#else
#include "Python.h"
#endif
#include "datetime.h"

// For compatibility with earlier Python releases
#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
#endif

#ifndef DOXYGEN
#include <iostream>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <ctime>
#include <assert.h>
#include <typeinfo>
#include <float.h>
#endif

// We want to use singly linked lists, but these are not part of the C++
// standard though. Sigh...
#ifndef DOXYGEN
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
#endif

// STL include files
#ifndef DOXYGEN
#include <list>
#include <map>
#include <set>
#include <string>
#include <stack>
#include <vector>
#include <algorithm>
#endif
using namespace std;

/** @def PACKAGE_VERSION
  * Defines the version of frePPLe.
  */
#ifdef HAVE_CONFIG_H
#undef PACKAGE_BUGREPORT
#undef PACKAGE_NAME
#undef PACKAGE_STRING
#undef PACKAGE_TARNAME
#undef PACKAGE_VERSION
#include <config.h>
#else
// Define the version for (windows) compilers that don't use autoconf
#define PACKAGE_VERSION "3.0.beta"
#endif

// Header for multithreading
#if defined(HAVE_PTHREAD_H)
#include <pthread.h>
#elif defined(WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <process.h>
#else
#error Multithreading not supported on your platform
#endif

// For the disabled and ansi-challenged people...
#ifndef DOXYGEN
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
#endif

/** @def ROUNDING_ERROR
  * This constant defines the magnitude of what can still be considered
  * as a rounding error.
  */
#define ROUNDING_ERROR   0.000001

// Header files for the Xerces-c XML parser.
#ifndef DOXYGEN
#define XERCES_STATIC_LIBRARY
#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/util/TransService.hpp>
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
#endif

/** @def DECLARE_EXPORT
  * Used to define which symbols to export from a Windows DLL.
  * @def MODULE_EXPORT
  * Signature used for a module initialization routine. It assures the
  * function is exported appropriately when running on Windows.<br>
  * A module will need to define a function with the following prototype:
  * @code
  * MODULE_EXPORT string initialize(const CommandLoadLibrary::ParameterList&);
  * @endcode
  */
#undef DECLARE_EXPORT
#undef MODULE_EXPORT
#if defined(WIN32) && !defined(DOXYGEN)
  #if defined(FREPPLE_CORE)
    #define DECLARE_EXPORT __declspec (dllexport)
  #elif defined(FREPPLE_STATIC)
    #define DECLARE_EXPORT
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
class CommandMoveOperationPlan;

namespace utils
{

// Forward declarations
class Object;
class Keyword;
class XMLInput;
class AttributeList;

// Include the list of predefined tags
#include "frepple/tags.h"


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
  /** Deleting an entity. */
  SIG_REMOVE = 1
};


/** Writes a signal description to an output stream. */
inline ostream & operator << (ostream & os, const Signal & d)
{
  switch (d)
  {
    case SIG_ADD: os << "ADD"; return os;
    case SIG_REMOVE: os << "REMOVE"; return os;
    default: assert(false); return os;
  }
}


/** This is the datatype used for hashing an XML-element to a numeric value. */
typedef unsigned int hashtype;

/** This stream is the general output for all logging and debugging messages. */
extern DECLARE_EXPORT ostream logger;

/** Auxilary structure for easy indenting in the log stream. */
struct indent
{
  short level;
  indent(short l) : level(l) {}
  indent operator() (short l) {return indent(l);}
};

/** Print a number of spaces to the output stream. */
inline ostream& operator <<(ostream &os, const indent& i)
{
  for (short c = i.level; c>0; --c) os << ' ';
  return os;
}



//
// CUSTOM EXCEPTION CLASSES
//


/** @brief An exception of this type is thrown when data errors are found.
  *
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


/** @brief An exception of this type is thrown when the library gets in an
  * inconsistent state from which the normal course of action can't continue.
  *
  * The normal handling of this error is to exit the program, and report the
  * problem. This exception indicates a bug in the program code.
  */
class LogicException: public logic_error
{
  public:
    LogicException(const char * c) : logic_error(c) {}
    LogicException(const string s) : logic_error(s) {}
};


/** @brief An exception of this type is thrown when the library runs into
  * problems that are specific at runtime. <br>
  * These could either be memory problems, threading problems, file system
  * problems, etc...
  *
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


/** @brief Python exception class matching with frepple::LogicException. */
extern DECLARE_EXPORT PyObject* PythonLogicException;

/** @brief Python exception class matching with frepple::DataException. */
extern DECLARE_EXPORT PyObject* PythonDataException;

/** @brief Python exception class matching with frepple::RuntimeException. */
extern DECLARE_EXPORT PyObject* PythonRuntimeException;


//
// UTILITY CLASS "NON-COPYABLE"
//

/** @brief Class NonCopyable is a base class.<br>Derive your own class from
  * it when you want to prohibit copy construction and copy assignment.
  *
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
    ~NonCopyable() {}

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


/** @brief This class is used to maintain the Python interpreter.
  *
  * A single interpreter is used throughout the lifetime of the
  * application.<br>
  * The implementation is implemented in a thread-safe way (within the
  * limitations of the Python threading model, of course).
  *
  * During the initialization the code checks for a file 'init.py' in its
  * search path and, if it does exist, the statements in the file will be
  * executed. In this way a library of globally available functions
  * can easily be initialized.
  *
  * The stderr and stdout streams of Python are redirected by default to
  * the frePPLe log stream.
  *
  * The following frePPLe functions are available from within Python.<br>
  * All of these are in the module called frePPLe.
  *   - The following <b>classes</b> and their attributes are accessible for
  *     reading and writing.<br>
  *     Each object has a toXML() method that returns its XML representation
  *     as a string, or writes it to a file is a file is passed as argument.
  *       - buffer
  *       - buffer_default
  *       - buffer_infinite
  *       - buffer_procure
  *       - calendar
  *           - addBucket(integer identifier)
  *           - events()
  *       - calendarBucket
  *       - calendar_boolean
  *       - calendar_double
  *       - calendar_void
  *       - customer
  *       - customer_default
  *       - demand
  *       - demand_default
  *       - flow
  *       - flowplan
  *       - item
  *       - item_default
  *       - load
  *       - loadplan
  *       - location
  *       - location_default
  *       - operation
  *       - operation_alternate
  *           - addAlternate(operation=x, priority=y, effective_start=z1, effective_end=z2)
  *       - operation_fixed_time
  *       - operation_routing
  *           - addStep(tuple of operations)
  *       - operation_time_per
  *       - operationplan
  *       - parameters
  *       - problem  (read-only)
  *       - resource
  *           - plan(list of dates to define the time periods)
  *       - resource_default
  *       - resource_infinite
  *       - setup_matrix
  *       - setup_matrix_default
  *       - solver
  *           - solve()
  *       - solver_mrp
  *           - commit()
  *           - rollback()
  *   - The following functions or attributes return <b>iterators</b> over the
  *     frePPLe objects:<br>
  *       - buffers()
  *       - buffer.members
  *       - buffer.flows
  *       - buffer.flowplans
  *       - calendar.buckets
  *       - calendars()
  *       - customers()
  *       - customer.members
  *       - demands()
  *       - demand.operationplans
  *       - demand.pegging
  *       - demand.members
  *       - operation.flows
  *       - operation.loads
  *       - items()
  *       - item.members
  *       - locations()
  *       - location.members
  *       - operations()
  *       - operation.operationplans
  *       - problems()
  *       - resources()
  *       - resource.members
  *       - resource.loads
  *       - resource.loadplans
  *       - setup_matrices()
  *       - solvers()
  *   - <b>printsize()</b>:<br>
  *     Prints information about the memory consumption.
  *   - <b>loadmodule(string [,parameter=value, ...])</b>:<br>
  *     Dynamically load a module in memory.
  *   - <b>readXMLdata(string [,bool] [,bool])</b>:<br>
  *     Processes an XML string passed as argument.
  *   - <b>log(string)</b>:<br>
  *     Prints a string to the frePPLe log file.<br>
  *     This is used for redirecting the stdout and stderr of Python.
  *   - <b>readXMLfile(string [,bool] [,bool])</b>:<br>
  *     Read an XML-file.
  *   - <b>saveXMLfile(string)</b>:<br>
  *     Save the model to an XML-file.
  *   - <b>saveplan(string)</b>:<br>
  *     Save the main plan information to a file.
  *   - <b>erase(boolean)</b>:<br>
  *     Erase the model (arg true) or only the plan (arg false, default).
  *   - <b>version</b>:<br>
  *     A string variable with the version number.
  *
  * The technical implementation is inspired by and inherited from the following
  * article: "Embedding Python in Multi-Threaded C/C++ Applications", see
  * http://www.linuxjournal.com/article/3641
  */
class PythonInterpreter
{
  public:
    /** Initializes the interpreter. */
    static DECLARE_EXPORT void initialize();

    /** Finalizes the interpreter. */
    static DECLARE_EXPORT void finalize();

    /** Execute some python code. */
    static DECLARE_EXPORT void execute(const char*);

    /** Execute a file with Python code. */
    static DECLARE_EXPORT void executeFile(string);

    /** Register a new method in the main extension module.<br>
      * Arguments:
      * - The name of the built-in function/method
      * - The function that implements it.
      * - Combination of METH_* flags, which mostly describe the args
      *   expected by the C func.
      * - The __doc__ attribute, or NULL.
      */
    static DECLARE_EXPORT void registerGlobalMethod(
      const char*, PyCFunction, int, const char*, bool = true
    );

    /** Register a new method in the main extension module. */
    static DECLARE_EXPORT void registerGlobalMethod
    (const char*, PyCFunctionWithKeywords, int, const char*, bool = true);

    /** Add a new object in the main extension module. */
    static DECLARE_EXPORT void registerGlobalObject(const char*, PyObject*, bool = true);

    /** Return a pointer to the main extension module. */
    static PyObject* getModule() {return module;}

    /** Create a new Python thread state.<br>
      * Each OS-level thread needs to initialize a Python thread state as well.
      * When a new thread is created in the OS, this method should be called
      * to create a Python thread state as well.<br>
      * See the Python PyGILState_Ensure API.
      */
    static DECLARE_EXPORT void addThread();

    /** Delete a Python thread state.<br>
      * Each OS-level thread has a Python thread state.
      * When an OS thread is deleted, this method should be called
      * to delete the Python thread state as well.<br>
      * See the Python PyGILState_Release API.
      */
    static DECLARE_EXPORT void deleteThread();

  private:
    /** Callback function to create the extension module. */
    static PyObject* createModule();

    /** A pointer to the frePPLe extension module. */
    static DECLARE_EXPORT PyObject *module;

    /** Python API: Used for redirecting the Python output to the same file
      * as the application.
      */
    static DECLARE_EXPORT PyObject *python_log(PyObject*, PyObject*);

    /** Main thread info. */
    static DECLARE_EXPORT PyThreadState* mainThreadState;
};


/** A utility function to do wildcard matching in strings.<br>
  * The function recognizes two wildcard characaters:
  *   - ?: matches any single character
  *   - *: matches any sequence of characters
  *
  * The code is written by Jack Handy (jakkhandy@hotmail.com) and published
  * on http://www.codeproject.com/KB/string/wildcmp.aspx. No specific license
  * constraints apply on using the code.
  */
DECLARE_EXPORT bool matchWildcard(const char*, const char*);


//
// METADATA AND OBJECT FACTORY
//

/** @brief This class defines a keyword for the frePPLe data model.
  *
  * The keywords are used to define the attribute names for the objects.<br>
  * They are used as:
  *  - Element and attribute names in XML documents
  *  - Attribute names in the Python extension.
  *
  * Special for this class is the requirement to have a "perfect" hash
  * function, i.e. a function that returns a distinct number for each
  * defined tag. The class prints a warning message when the hash
  * function doesn't satisfy this criterion.
  */
class Keyword : public NonCopyable
{
  private:
    /** Stores the hash value of this tag. */
    hashtype dw;

    /** Store different preprocessed variations of the name of the tag.
      * These are all stored in memory for improved performance. */
    string strName, strStartElement, strEndElement, strElement, strAttribute;

    /** Name of the string transcoded to its Xerces-internal representation. */
    XMLCh* xmlname;

    /** A function to verify the uniquess of our hashes. */
    void check();

  public:
    /** Container for maintaining a list of all tags. */
    typedef map<hashtype,Keyword*> tagtable;

    /** This is the constructor.<br>
      * The tag doesn't belong to an XML namespace. */
    DECLARE_EXPORT Keyword(const string&);

    /** This is the constructor. The tag belongs to the XML namespace passed
      * as second argument.<br>
      * Note that we still require the first argument to be unique, since it
      * is used as a keyword for the Python extensions.
      */
    DECLARE_EXPORT Keyword(const string&, const string&);

    /** Destructor. */
    DECLARE_EXPORT ~Keyword();

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
      * as possible while still garantueeing the perfectness.<br>
      * The hash function is based on the Xerces-C implementation,
      * with the difference that the hash calculated by our function is
      * portable between platforms.<br>
      * The hash modulus is 954991 (which is the biggest prime number
      * lower than 1000000).
      */
    static DECLARE_EXPORT hashtype hash(const char*);

    /** This is the hash function.
      * @see hash(const char*)
      */
    static hashtype hash(const string& c) {return hash(c.c_str());}

    /** This is the hash function taken an XML character string as input.<br>
      * The function is expected to return exactly the same result as when a
      * character pointer is passed as argument.
      * @see hash(const char*)
      */
    static DECLARE_EXPORT hashtype hash(const XMLCh*);

    /** Finds a tag when passed a certain string. If no tag exists yet, it
      * will be created. */
    static DECLARE_EXPORT const Keyword& find(const char*);

    /** Return a reference to a table with all defined tags. */
    static DECLARE_EXPORT tagtable& getTags();

    /** Prints a list of all tags that have been defined. This can be useful
      * for debugging and also for creating a good hashing function.<br>
      * GNU gperf is a program that can generate a perfect hash function for
      * a given set of symbols.
      */
    static DECLARE_EXPORT void printTags();
};


/** @brief This abstract class is the base class used for callbacks.
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
    virtual bool callback(Object* v, const Signal a) const = 0;

    /** Destructor. */
    virtual ~Functor() {}
};


// The following handler functions redirect the call from Python onto a
// matching virtual function in a PythonExtensionBase subclass.
extern "C"
{
  /** Handler function called from Python. Internal use only. */
  DECLARE_EXPORT PyObject* getattro_handler (PyObject*, PyObject*);
  /** Handler function called from Python. Internal use only. */
  DECLARE_EXPORT int setattro_handler (PyObject*, PyObject*, PyObject*);
  /** Handler function called from Python. Internal use only. */
  DECLARE_EXPORT PyObject* compare_handler (PyObject*, PyObject*, int);
  /** Handler function called from Python. Internal use only. */
  DECLARE_EXPORT PyObject* iternext_handler (PyObject*);
  /** Handler function called from Python. Internal use only. */
  DECLARE_EXPORT PyObject* call_handler(PyObject*, PyObject*, PyObject*);
  /** Handler function called from Python. Internal use only. */
  DECLARE_EXPORT PyObject* str_handler(PyObject*);
}


/** @brief This class is a thin wrapper around the type information in Python.
  *
  * This class defines a number of convenience functions to interact with the
  * PyTypeObject struct of the Python C API.
  */
class PythonType : public NonCopyable
{
  private:
    /** This static variable is a template for cloning type definitions.<br>
      * It is copied for each type object we create.
      */
    static const PyTypeObject PyTypeObjectTemplate;

    /** Incremental size of the method table.<br>
      * We allocate memory for the method definitions per block, not
      * one-by-one.
      */
    static const unsigned short methodArraySize = 5;

    /** The Python type object which this class is wrapping. */
    PyTypeObject* table;

  public:
    /** A static function that evaluates an exception and sets the Python
       * error string properly.<br>
       * This function should only be called from within a catch-block, since
       * internally it rethrows the exception!
       */
    static DECLARE_EXPORT void evalException();

    /** Constructor, sets the tp_base_size member. */
    DECLARE_EXPORT PythonType(size_t, const type_info*);

    /** Return a pointer to the actual Python PyTypeObject. */
    PyTypeObject* type_object() const {return table;}

    /** Add a new method. */
    DECLARE_EXPORT void addMethod(const char*, PyCFunction, int, const char*);

    /** Add a new method. */
    DECLARE_EXPORT void addMethod(const char*, PyCFunctionWithKeywords, int, const char*);

    /** Updates tp_name. */
    void setName (const string n)
    {
      string *name = new string("frepple." + n);
      table->tp_name = const_cast<char*>(name->c_str());
    }

    /** Updates tp_doc. */
    void setDoc (const string n)
    {
      string *doc = new string(n);
      table->tp_doc = const_cast<char*>(doc->c_str());
    }

    /** Updates tp_base. */
    void setBase(PyTypeObject* b)
    {
      table->tp_base = b;
    }

    /** Updates the deallocator. */
    void supportdealloc(void (*f)(PyObject*))
    {
      table->tp_dealloc = f;
    }

    /** Updates tp_getattro.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PythonObject getattro(const XMLElement& name)
      */
    void supportgetattro()
    {table->tp_getattro = getattro_handler;}

    /** Updates tp_setattro.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   int setattro(const Attribute& attr, const PythonObject& field)
      */
    void supportsetattro()
    {table->tp_setattro = setattro_handler;}

    /** Updates tp_richcompare.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   int compare(const PyObject* other) const
      */
    void supportcompare()
    {
      table->tp_richcompare = compare_handler;
    }

    /** Updates tp_iter and tp_iternext.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* iternext()
      */
    void supportiter()
    {
      table->tp_iter = PyObject_SelfIter;
      table->tp_iternext = iternext_handler;
    }

    /** Updates tp_call.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* call(const PythonObject& args, const PythonObject& kwds)
      */
    void supportcall()
    {table->tp_call = call_handler;}

    /** Updates tp_str.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* str()
      */
    void supportstr()
    {table->tp_str = str_handler;}

    /** Type definition for create functions. */
    typedef PyObject* (*createfunc)(PyTypeObject*, PyObject*, PyObject*);

    /** Updates tp_new with the function passed as argument. */
    void supportcreate(createfunc c) {table->tp_new = c;}

    /** This method needs to be called after the type information has all
      * been updated. It adds the type to the frepple module. */
    DECLARE_EXPORT int typeReady();

    /** Comparison operator. */
    bool operator == (const PythonType& i) const
    {
      return *cppClass == *(i.cppClass);
    }

    /** Comparison operator. */
    bool operator == (const type_info& i) const
    {
      return *cppClass == i;
    }

    /** Type info of the registering class. */
    const type_info* cppClass;
};


class MetaCategory;
/** @brief This class stores metadata about the classes in the library.
  * The stored information goes well beyond the standard 'type_info'.
  *
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
  *        virtual const MetaClass& getType() {return *metadata;}
  *        static const MetaClass *metadata;
  *    }
  *  In the implementation file:
  *    const MetaClass *X::metadata;
  * @endcode
  * Creating a MetaClass object isn't sufficient. It needs to be registered,
  * typically in an initialization method:
  * @code
  *    void initialize()
  *    {
  *      ...
  *      Y::metadata = new MetaCategory("Y","Ys", reader_method, writer_method);
  *      X::metadata = new MetaClass("Y","X", factory_method);
  *      ...
  *    }
  * @endcode
  * @see MetaCategory
  */
class MetaClass : public NonCopyable
{
    friend class MetaCategory;
    template <class T, class U> friend class FunctorStatic;
    template <class T, class U> friend class FunctorInstance;

  public:
    /** Type definition for a factory method calling the default
     * constructor.. */
    typedef Object* (*creatorDefault)();

    /** Type definition for a factory method calling the constructor that
      * takes a string as argument. */
    typedef Object* (*creatorString)(const string&);

    /** A string specifying the object type, i.e. the subclass within the
      * category. */
    string type;

    /** A reference to an Keyword of the base string. */
    const Keyword* typetag;

    /** The category of this class. */
    const MetaCategory* category;

    /** A pointer to the Python type. */
    PyTypeObject* pythonClass;

    /** A factory method for the registered class. */
    union
    {
      creatorDefault factoryMethodDefault;
      creatorString factoryMethodString;
    };

    /** Destructor. */
    virtual ~MetaClass() {}

    /** Initialize the data structure and register the class. */
    DECLARE_EXPORT void registerClass(const string&, const string&,
        bool = false, creatorDefault = NULL);

    /** This constructor registers the metadata of a class. */
    MetaClass (const string& cat, const string& cls, bool def = false)
      : pythonClass(NULL)
    {
      registerClass(cat,cls,def);
    }

    /** This constructor registers the metadata of a class, with a factory
      * method that uses the default constructor of the class. */
    MetaClass (const string& cat, const string& cls, creatorDefault f,
        bool def = false) : pythonClass(NULL)
    {
      registerClass(cat,cls,def);
      factoryMethodDefault = f;
    }

    /** This constructor registers the metadata of a class, with a factory
      * method that uses a constructor with a string argument. */
    MetaClass (const string& cat, const string& cls, creatorString f,
        bool def = false) : pythonClass(NULL)
    {
      registerClass(cat,cls,def);
      factoryMethodString = f;
    }

    /** This function will analyze the string being passed, and return the
      * appropriate action.
      * The string is expected to be one of the following:
      *  - 'A' for action ADD
      *  - 'C' for action CHANGE
      *  - 'AC' for action ADD_CHANGE
      *  - 'R' for action REMOVE
      *  - Any other value will result in a data exception
      */
    static DECLARE_EXPORT Action decodeAction(const char*);

    /** This method picks up the attribute named "ACTION" from the list and
      * calls the method decodeAction(const XML_Char*) to analyze it.
      * @see decodeAction(const XML_Char*)
      */
    static DECLARE_EXPORT Action decodeAction(const AttributeList&);

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
    DECLARE_EXPORT bool raiseEvent(Object* v, Signal a) const;

    /** Connect a new subscriber to the class. */
    void connect(Functor *c, Signal a) const
    {const_cast<MetaClass*>(this)->subscribers[a].push_front(c);}

    /** Disconnect a subscriber from the class. */
    void disconnect(Functor *c, Signal a) const
    {const_cast<MetaClass*>(this)->subscribers[a].remove(c);}

    /** Print all registered factory methods to the standard output for
      * debugging purposes. */
    static DECLARE_EXPORT void printClasses();

    /** Find a particular class by its name. If it can't be located the return
      * value is NULL. */
    static DECLARE_EXPORT const MetaClass* findClass(const char*);

    /** Default constructor. */
    MetaClass() : type("unspecified"), typetag(&Keyword::find("unspecified")),
      category(NULL), pythonClass(NULL), factoryMethodDefault(NULL) {}

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
};


class XMLOutput;

/** @brief This class stores metadata on a data field of a class.
  *
  * A field
  */
//class MetaField : public NonCopyable
//{
//  private:
//    Keyword& name;
//
//  public:
//    typedef double (*getDouble)() const;
//    typedef void (*setDouble)(double);
//    typedef int (*getInt)() const;
//    typedef void (*setInt)(int);
//    typedef long (*getLong)() const;
//    typedef void (*setLong)(long);
//    typedef unsigned long (*getUnsignedLong)() const;
//    typedef void (*setUnsignedLong)(unsigned long);
//    typedef bool (*getBool)() const;
//    typedef void (*setBool)(int);
//    typedef bool (*getString)() const;
//    typedef void (*setString)(string);
//    typedef Date (*getDate)() const;
//    typedef void (*setDate)(Date);
//    typedef TimePeriod (*getTimePeriod)() const;
//    typedef void (*setTimePeriod)(TimePeriod);
//    /* Other types: list of things... */
//
//    /** Constructor. */
//    MetaField(Keyword&, getDouble, setDouble);
//    MetaField(Keyword&, getInt, setInt);
//    MetaField(Keyword&, getBool, setBool);
//    MetaField(Keyword&, getString, setString );
//    template <class T> MetaField(Keyword&, T*(*getFunction)() const, void (*setFunction)(T*));
//
//    bool get(Object*);
//    int get(Object*);
//    double get(Object*);
//    string get(Object*);
//
//    void set(Object*, bool);
//    void set(Object*, int);
//    void set(Object*, double);
//    void set(Object*, string);
//
//    /* for class MetaClass: */
//    void write(writer, object*);
//    void read(reader, Object*);
//};


/** @brief A MetaCategory instance represents metadata for a category of
  * object.
  *
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
    template<class T> friend class HasName;
  public:
    /** The name used to name a collection of objects of this category. */
    string group;

    /** A XML tag grouping objects of the category. */
    const Keyword* grouptag;

    /** Type definition for the read control function. */
    typedef Object* (*readController)(const MetaClass*, const AttributeList&);

    /** Type definition for the write control function. */
    typedef void (*writeController)(const MetaCategory*, XMLOutput *o);

    /** This template method is available as a object creation factory for
      * classes without key fields and which rely on a default constructor.
      */
    static Object* ControllerDefault (const MetaClass*, const AttributeList&);

    /** Destructor. */
    virtual ~MetaCategory() {}

    /** Constructor. */
    DECLARE_EXPORT MetaCategory (const string& t, const string& g,
        readController = NULL, writeController = NULL);

    /** Type definition for the map of all registered classes. */
    typedef map < hashtype, const MetaClass*, less<hashtype> > ClassMap;

    /** Type definition for the map of all categories. */
    typedef map < hashtype, const MetaCategory*, less<hashtype> > CategoryMap;

    /** Looks up a category name in the registry. If the catgory can't be
      * located the return value is NULL. */
    static DECLARE_EXPORT const MetaCategory* findCategoryByTag(const char*);

    /** Looks up a category name in the registry. If the catgory can't be
      * located the return value is NULL. */
    static DECLARE_EXPORT const MetaCategory* findCategoryByTag(const hashtype);

    /** Looks up a category name in the registry. If the catgory can't be
      * located the return value is NULL. */
    static DECLARE_EXPORT const MetaCategory* findCategoryByGroupTag(const char*);

    /** Looks up a category name in the registry. If the category can't be
      * located the return value is NULL. */
    static DECLARE_EXPORT const MetaCategory* findCategoryByGroupTag(const hashtype);

    /** Find a class in this category with a specified name.<br>
      * If the catrgory can't be found the return value is NULL.
      */
    DECLARE_EXPORT const MetaClass* findClass(const char*) const;

    /** Find a class in this category with a specified name.<br>
      * If the catrgory can't be found the return value is NULL.
      */
    DECLARE_EXPORT const MetaClass* findClass(const hashtype) const;

    /** This method takes care of the persistence of all categories. It loops
      * through all registered categories (in the order of their registration)
      * and calls the persistance handler.
      */
    static DECLARE_EXPORT void persist(XMLOutput *);

    /** A control function for reading objects of a category.
      * The controller function manages the creation and destruction of
      * objects in this category.
      */
    readController readFunction;

  private:
    /** A map of all classes registered for this category. */
    ClassMap classes;

    /** Compute the hash for "default" once and store it in this variable for
      * efficiency. */
    static DECLARE_EXPORT const hashtype defaultHash;

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

    /** A map of all categories by their name. */
    static DECLARE_EXPORT CategoryMap categoriesByTag;

    /** A map of all categories by their group name. */
    static DECLARE_EXPORT CategoryMap categoriesByGroupTag;
};


/** @brief This class represents a static subscription to a signal.
  *
  * When the signal callback is triggered the static method callback() on the
  * parameter class will be called.
  */
template <class T, class U> class FunctorStatic : public Functor
{
    friend class MetaClass;
  public:
    /** Add a signal subscriber. */
    static void connect(const Signal a)
    {T::metadata->connect(new FunctorStatic<T,U>(), a);}

    /** Remove a signal subscriber. */
    static void disconnect(const Signal a)
    {
      MetaClass &t =
        const_cast<MetaClass&>(static_cast<const MetaClass&>(*T::metadata));
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
    virtual bool callback(Object* v, const Signal a) const
    {return U::callback(static_cast<T*>(v),a);}
};


/** @brief This class represents an object subscribing to a signal.
  *
  * When the signal callback is triggered the method callback() on the
  * instance object will be called.
  */
template <class T, class U> class FunctorInstance : public Functor
{
  public:
    /** Connect a new subscriber to a signal.<br>
      * It is the users' responsibility to call the disconnect method
      * when the subscriber is being deleted. Otherwise the application
      * will crash.
      */
    static void connect(U* u, const Signal a)
    {if (u) T::metadata.connect(new FunctorInstance(u), a);}

    /** Disconnect from a signal. */
    static void disconnect(U *u, const Signal a)
    {
      MetaClass &t =
        const_cast<MetaClass&>(static_cast<const MetaClass&>(T::metadata));
      // Loop through all subscriptions
      for (list<Functor*>::iterator i = t.subscribers[a].begin();
          i != t.subscribers[a].end(); ++i)
      {
        // Try casting the functor to the right type
        FunctorInstance<T,U> *f = dynamic_cast< FunctorInstance<T,U>* >(*i);
        if (f && f->instance == u)
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

    /** Constructor. */
    FunctorInstance(U* u) : instance(u) {}

  private:
    /** This is the callback method. */
    virtual bool callback(Object* v, const Signal a) const
    {return instance ? instance->callback(static_cast<T*>(v),a) : true;}

    /** The object whose callback method will be called. */
    U* instance;
};


//
// UTILITY CLASS "TIMER".
//

/** @brief This class is used to measure the processor time used by the
  * program.
  *
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
    void restart() {start_time = clock();}

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


/** @brief This class represents a time duration with an accuracy of
  * one second.
  *
  * The duration can be both positive and negative.
  */
class TimePeriod
{
    friend ostream& operator << (ostream &, const TimePeriod &);
  public:
    /** Default constructor and constructor with timeperiod passed. */
    TimePeriod(const long l = 0) : lval(l) {}

    /** Constructor from a character string.<br>
      * See the parse() method for details on the format of the argument.
      */
    TimePeriod(const char* s) {parse(s);}

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

    /** Converts the date to a string, formatted according to ISO 8601. */
    operator string() const
    {
      char str[20];
      toCharBuffer(str);
      return string(str);
    }

    /** Function that parses a input string to a time value.<br>
      * The string format is following the ISO 8601 specification for
      * durations: [-]P[nY][nM][nW][nD][T[nH][nM][nS]]<br>
      * Some examples to illustrate how the string is converted to a
      * timeperiod, expressed in seconds:<br>
      *    P1Y = 1 year = 365 days = 31536000 seconds
      *    P1M = 365/12 days = 2628000 seconds
      *    P1W = 1 week = 7 days = 604800 seconds
      *    -P1D = -1 day = -86400 seconds
      *    PT1H = 1 hour = 3600 seconds
      *    -PT1000000S = 1000000 seconds
      *    P1M1WT1H = 1 month + 1 week + 1 hour = 3236400 seconds
      * It pretty strictly checks the spec, with a few exceptions:
      *  - A week field ('W') may coexist with other units.
      *  - Decimal values are not supported.
      *  - The alternate format as a date and time is not supported.
      */
    DECLARE_EXPORT void parse(const char*);

    /** Function to parse a string to a double, representing the
      * number of seconds.<br>
      * Compared to the parse() method it also processes the
      * decimal part of the duration.
      * @see parse(const char*)
      */
    static DECLARE_EXPORT double parse2double(const char*);

    /** Write out a double as a time period string.
      * @see toCharBuffer()
      */
    static DECLARE_EXPORT void double2CharBuffer(double, char*);

    /** The maximum value for a timeperiod. */
    DECLARE_EXPORT static const TimePeriod MAX;

    /** The minimum value for a timeperiod. */
    DECLARE_EXPORT static const TimePeriod MIN;

  private:
    /** The time is stored as a number of seconds. */
    long lval;

    /** This function fills a character buffer with a text representation of
      * the TimePeriod.<br>
      * The character buffer passed MUST have room for at least 20 characters.
      * 20 characters is sufficient for even the most longest possible time
      * duration.<br>
      * The output format is described with the string() method.
      * @see string()
      */
    DECLARE_EXPORT void toCharBuffer(char*) const;
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


/** @brief This class represents a date and time with an accuracy of
  * one second. */
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
    void checkFinite(long long i)
    {
      if (i < infinitePast.lval) lval = infinitePast.lval;
      else if (i > infiniteFuture.lval) lval = infiniteFuture.lval;
      else lval = static_cast<long>(i);
    }

    /** A private constructor used to create the infinitePast and
      * infiniteFuture constants. */
    Date(const char* s, bool dummy) {parse(s);}

    /** A utility function that uses the C function localtime to compute the
      * details of the current time: day of the week, day of the month,
      * day of the year, hour, minutes, seconds
      */
    inline void getInfo(struct tm* tm_struct) const
    {
      // The standard library function localtime() is not re-entrant: the same
      // static structure is used for all calls. In a multi-threaded environment
      // the function is not to be used.
      #ifdef HAVE_LOCALTIME_R
        // The POSIX standard defines a re-entrant version of the function.
        localtime_r(&lval, tm_struct);
      #elif defined(WIN32)
        // Microsoft uses another function name with, of course, a different
        // name and a different order of arguments.
        localtime_s(tm_struct, &lval);
      #else
        #error A multi-threading safe localtime function is required
      #endif
    }

  public:

    /** Constructor initialized with a long value. */
    Date(const time_t l) : lval(l) {checkFinite(lval);}

    /** Default constructor. */
    // This constructor can skip the check for finite dates, and
    // thus gives the best performance.
    Date() : lval(infinitePast.lval) {}

    /* Note: the automatic copy constructor works fine and is faster than
       writing our own. */

    /** Constructor initialized with a string. The string needs to be in
      * the format specified by the "format". */
    Date(const char* s) {parse(s); checkFinite(lval);}

    /** Constructor with year, month and day as arguments. Hours, minutes
      * and seconds can optionally be passed too.
      */
    DECLARE_EXPORT Date(int year, int month, int day,
        int hr=0, int min=0, int sec=0
                       );

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
    {checkFinite(static_cast<long long>(l) + lval);}

    /** Subtracts some time to this date. */
    void operator -= (const TimePeriod& l)
    {checkFinite(- static_cast<long long>(l) + lval);}

    /** Adding a time to a date returns a new date. */
    Date operator + (const TimePeriod& l) const
    {
      Date d;
      d.checkFinite(static_cast<long long>(l) + lval);
      return d;
    }

    /** Subtracting a time from a date returns a new date. */
    Date operator - (const TimePeriod& l) const
    {
      Date d;
      d.checkFinite(- static_cast<long>(l) + lval);
      return d;
    }

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

    /** This function fills a character buffer with a text representation of
      * the date.<br>
      * The character buffer passed is expected to have room for
      * at least 30 characters. 30 characters should be sufficient for even
      * the most funky date format.
      */
    size_t toCharBuffer(char* str) const
    {
      struct tm t;
      getInfo(&t);
      return strftime(str, 30, format.c_str(), &t);
    }

    /** Return the seconds since the epoch, which is also the internal
      * representation of a date. */
    time_t getTicks() const {return lval;}

    /** Function that parses a string according to the format string. */
    DECLARE_EXPORT void parse(const char*, const string& = format);

    /** Updates the default date format. */
    static void setFormat(const string& n) {format = n;}

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

    /** Return the number of seconds since january 1st. */
    long getSecondsYear() const
    {
      struct tm t;
      getInfo(&t);
      return t.tm_yday * 86400 + t.tm_sec + t.tm_min * 60 + t.tm_hour * 3600;
    }

    /** Return the number of seconds since the start of the month. */
    long getSecondsMonth() const
    {
      struct tm t;
      getInfo(&t);
      return (t.tm_mday-1) * 86400 + t.tm_sec + t.tm_min * 60 + t.tm_hour * 3600;
    }

    /** Return the number of seconds since the start of the week.
      * The week is starting on Sunday.
      */
    long getSecondsWeek() const
    {
      struct tm t;
      getInfo(&t);
      int result = t.tm_wday * 86400 + t.tm_sec + t.tm_min * 60 + t.tm_hour * 3600;
      assert(result >= 0 && result < 604800L);
      return result;
    }

    /** Return the number of seconds since the start of the day. */
    long getSecondsDay() const
    {
      struct tm t;
      getInfo(&t);
      int result = t.tm_sec + t.tm_min * 60 + t.tm_hour * 3600;
      assert(result >= 0 && result < 86400L);
      return result;
    }

#ifndef HAVE_STRPTIME
  private:
    DECLARE_EXPORT char* strptime(const char *, const char *, struct tm *);
#endif
};


/** Prints a date to the outputstream. */
inline ostream & operator << (ostream & os, const Date & d)
{
  char str[30];
  d.toCharBuffer(str);
  return os << str;
}


/** @brief This class defines a date-range, i.e. a start-date and end-date pair.
  *
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
      * If the start date is later than the end date parameter, the
      * parameters will be swapped. */
    DateRange(const Date& st, const Date& nd) : start(st), end(nd)
    {
      if(st>nd)
      {
        start=nd;
        end=st;
      }
    }

    /** Default constructor.<br>
      * This will create a daterange covering the complete horizon.
      */
    DateRange() : start(Date::infinitePast), end(Date::infiniteFuture) {}

    /** Copy constructor. */
    DateRange(const DateRange& n) : start(n.start), end(n.end) {}

    /** Returns the start date. */
    const Date& getStart() const {return start;}

    /** Updates the start date.<br>
      * If the new start date is later than the end date, the end date will
      * be set equal to the new start date.
      */
    void setStart(const Date& d)
    {
      start=d;
      if(start>end) end=start;
    }

    /** Returns the end date. */
    const Date & getEnd() const {return end;}

    /** Updates the end date.<br>
      * If the new end date is earlier than the start date, the start date will
      * be set equal to the new end date.
      */
    void setEnd(const Date& d)
    {
      end=d;
      if (start>end) start=end;
    }

    /** Updates the start and end dates simultaneously. */
    void setStartAndEnd(const Date& st, const Date& nd)
    {
      if (st<nd)
      {
        start=st;
        end=nd;
      }
      else
      {
        start=nd;
        end=st;
      }
    }

    /** Returns the duration of the interval. Note that this number will always
      * be greater than or equal to 0, since the end date is always later than
      * the start date.
      */
    TimePeriod getDuration() const
    {
      return end - start;
    }

    /** Bool conversion operator.<br>
      * Returns true if the daterange is different from the default. */
    operator bool() const
    {
      return start != Date::infinitePast || end != Date::infiniteFuture;
    }

    /** Equality of date ranges. */
    bool operator == (const DateRange& b) const
    {
      return start==b.start && end==b.end;
    }

    /** Inequality of date ranges. */
    bool operator != (const DateRange& b) const
    {
      return start!=b.start || end!=b.end;
    }

    /** Move the daterange later in time. */
    void operator += (const TimePeriod& l)
    {
      start += l;
      end += l;
    }

    /** Move the daterange earlier in time. */
    void operator -= (const TimePeriod& l)
    {
      start -= l;
      end -= l;
    }

    /** Assignment operator. */
    void operator = (const DateRange& dr)
    {
      start = dr.start;
      end = dr.end;
    }

    /** Return true if two date ranges are overlapping.<br>
      * The start point of the first interval is included in the comparison,
      * whereas the end point isn't. As a result this method is not
      * symmetrical, ie when a.intersect(b) returns true b.intersect(a) is
      * not nessarily true.
      */
    bool intersect(const DateRange& dr) const
    {
      return dr.start<=end && dr.end>start;
    }

    /** Returns the number of seconds the two dateranges overlap. */
    TimePeriod overlap(const DateRange& dr) const
    {
      long x = (dr.end<end ? dr.end : end)
          - (dr.start>start ? dr.start : start);
      return x>0 ? x : 0;
    }

    /** Returns true if the date passed as argument does fall within the
      * daterange. */
    bool within(const Date& d) const
    {
      return d>=start && d<end;
    }

    /** Convert the daterange to a string. */
    DECLARE_EXPORT operator string() const;

    /** Updates the default seperator. */
    static void setSeparator(const string& n)
    {
      separator = n;
      separatorlength = n.size();
    }

    /** Retrieves the default seperator. */
    static const string& getSeparator() {return separator;}

  private:
    /** Start date of the interval. */
    Date start;

    /** End dat of the interval. */
    Date end;

    /** Separator to be used when printing this string. */
    static DECLARE_EXPORT string separator;

    /** Separator to be used when printing this string. */
    static DECLARE_EXPORT size_t separatorlength;
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
  NOHEAD = 2,
  /** Write the full object, with all its fields and a header line.<br>
    * Eg: \<MODEL NAME="POL" TYPE="a"\>\<FIELD\>value\</FIELD\>\</MODEL\>
    */
  FULL = 3,
  /** Write the full object, but without a closing tag. This method is
    * typically used when a subclass calls the write method of its parent
    * class.<br>
    * Eg: \<MODEL NAME="POL" TYPE="a"\>\<FIELD\>value\</FIELD\>
    */
  NOTAIL = 4,
  /** Write the core fields, but without a starting and closing tag. This
    * method is typically used when a subclass calls the write method of
    * its parent class.<br>
    * Eg: \<FIELD\>value\</FIELD\>
    */
  NOHEADTAIL = 5
};


/** @ brief This utility class escapes special characters from a string.
  *
  *  The following characters are replaced:
  *    - &: replaced with &amp;
  *    - <: replaced with &lt;
  *    - >: replaced with &gt;
  *    - ": replaced with &quot;
  *    - ': replaced with &apos;
  *    - all other characters are left unchanged
  * The reverse process of un-escaping the special character sequences is
  * taken care of by the Xerces library.
  *
  * This class works fine with UTF-8 and single-byte encodings, but will
  * NOT work with other multibyte encodings (such as UTF-116 or UTF-32).
  * FrePPLe consistently uses UTF-8 in its internal representation.
  */
class XMLEscape
{
    friend DECLARE_EXPORT ostream& operator << (ostream&, const XMLEscape&);
  private:
    const char* data;
  public:
    XMLEscape(const char* p) {data = p;}
    XMLEscape(const string& p) {data = p.c_str();}
};


/** Prints the escaped value of the string to the outputstream. */
DECLARE_EXPORT ostream & operator << (ostream&, const XMLEscape&);


/** @brief Base class for writing XML formatted data to an output stream.
  *
  * Subclasses implement writing to specific stream types, such as files
  * and strings.
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
    static DECLARE_EXPORT const content_type STANDARD;

    /** Constant to mark an export of the standard information plus the plan
      * information. In this format, every entity is saved with the details
      * on how it is used in the plan.<br>
      * E.g. a resource will be saved with a reference to all its loadplans.
      * E.g. an operation will be saved with all its operationplans.
      * @see STANDARD
      * @see PLANDETAIL
      */
    static DECLARE_EXPORT const content_type PLAN;

    /** Constant to mark an export of the lowest level of plan information.
      * In addition to the plan information pegging information is now saved.
      * @see STANDARD
      * @see PLAN
      */
    static DECLARE_EXPORT const content_type PLANDETAIL;

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
      * document.<br>
      * The default value is:
      *   <?xml version="1.0" encoding="UTF-8"?>
      */
    void setHeaderStart(const string& s) {headerStart = s;}

    /** Returns the string that is printed as the first line of each XML
      * document. */
    string getHeaderStart() const {return headerStart;}

    /** Updates the attributes that are written for the root element of each
      * XML document.<br>
      * The default value is an empty string.
      */
    void setHeaderAtts(const string& s) {headerAtts = s;}

    /** Returns the attributes that are written for the root element of each
      * XML document. */
    string getHeaderAtts() const {return headerAtts;}

    /** Constructor with a given stream. */
    XMLOutput(ostream& os) : m_nIndent(0), numObjects(0),
      numParents(0), currentObject(NULL), parentObject(NULL), content(STANDARD),
      headerStart("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"),
      headerAtts("xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"")
    {m_fp = &os; indentstring[0] = '\0';}

    /** Default constructor. */
    XMLOutput() : m_nIndent(0), numObjects(0), numParents(0),
      currentObject(NULL), parentObject(NULL), content(STANDARD),
      headerStart("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"),
      headerAtts("xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"")
    {m_fp = &logger; indentstring[0] = '\0';}

    /** Force writing only references for nested objects. */
    void setReferencesOnly(bool b) {numParents = b ? 2 : 0;}

    /** Returns whether we write only references for nested objects or not. */
    bool getReferencesOnly() const {return numParents>0;}

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * Output: \<TAG\>
      */
    void BeginObject(const Keyword& t)
    {
      *m_fp << indentstring << t.stringElement() << "\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.
      * Output: \<TAG attributes\>
      */
    void BeginObject(const Keyword& t, const string& atts)
    {
      *m_fp << indentstring << t.stringStartElement() << " " << atts << ">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * The user is responsible to assure string values are escaped correctly with the XMLEscape class.<br>
      * Output: \<TAG TAG1="val1"\>
      * @see XMLEscape
      */
    template <class T>
    void BeginObject(const Keyword& t, const Keyword& attr1, const T& val1)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute() << val1 << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * The user is responsible to assure string values are escaped correctly with the XMLEscape class.<br>
      * Output: \<TAG TAG1="val1" TAG2="val2"\>
      * @see XMLEscape
      */
    template <class T, class U>
    void BeginObject(const Keyword& t, const Keyword& attr1, const T& val1,
      const Keyword& attr2, const U& val2)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute() << val1 << "\""
          << attr2.stringAttribute() << val2 << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * The user is responsible to assure string values are escaped correctly with the XMLEscape class.<br>
      * Output: \<TAG TAG1="val1" TAG2="val2" TAG3="val3"\>
      * @see XMLEscape
      */
    template <class T, class U, class V>
    void BeginObject(const Keyword& t, const Keyword& attr1, const T& val1,
      const Keyword& attr2, const U& val2,
      const Keyword& attr3, const V& val3)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute() << val1 << "\""
          << attr2.stringAttribute() << val2 << "\""
          << attr3.stringAttribute() << val3 << "\">\n";
      incIndent();
    }

    /** Write the closing tag of this object and decrease the indentation
      * level.<br>
      * Output: \</TAG_T\>
      */
    void EndObject(const Keyword& t)
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

    /** Write an unsigned long value enclosed opening and closing tags.<br>
      * Output: \<TAG_T\>uint\</TAG_T\> */
    void writeElement(const Keyword& t, const long unsigned int val)
    {
      *m_fp << indentstring << t.stringElement() << val << t.stringEndElement();
    }

    /** Write an integer value enclosed opening and closing tags.<br>
      * Output: \<TAG_T\>integer\</TAG_T\> */
    void writeElement(const Keyword& t, const int val)
    {
      *m_fp << indentstring << t.stringElement() << val << t.stringEndElement();
    }

    /** Write a double value enclosed opening and closing tags.<br>
      * Output: \<TAG_T\>double\</TAG_T\> */
    void writeElement(const Keyword& t, const double val)
    {
      *m_fp << indentstring << t.stringElement() << val << t.stringEndElement();
    }

    /** Write a boolean value enclosed opening and closing tags. The boolean
      * is written out as the string 'true' or 'false'.<br>
      * Output: \<TAG_T\>true\</TAG_T\>
      */
    void writeElement(const Keyword& t, const bool val)
    {
      *m_fp << indentstring << t.stringElement()
          << (val ? "true" : "false") << t.stringEndElement();
    }

    /** Write a string value enclosed opening and closing tags. Special
      * characters (i.e. & < > " ' ) are appropriately escaped.<br>
      * Output: \<TAG_T\>val\</TAG_T\> */
    void writeElement(const Keyword& t, const string& val)
    {
      if (!val.empty())
        *m_fp << indentstring << t.stringElement()
            << XMLEscape(val) << t.stringEndElement();
    }

    /** Writes an element with a string attribute.<br>
      * Output: \<TAG_U TAG_T="string"/\> */
    void writeElement(const Keyword& u, const Keyword& t, const string& val)
    {
      if (val.empty())
        *m_fp << indentstring << u.stringStartElement() << "/>\n";
      else
        *m_fp << indentstring << u.stringStartElement()
            << t.stringAttribute() << XMLEscape(val)
            << "\"/>\n";
    }

    /** Writes an element with a long attribute.<br>
      * Output: \<TAG_U TAG_T="val"/\> */
    void writeElement(const Keyword& u, const Keyword& t, const long val)
    {
      *m_fp << indentstring << u.stringStartElement()
          << t.stringAttribute() << val << "\"/>\n";
    }

    /** Writes an element with a date attribute.<br>
      * Output: \<TAG_U TAG_T="val"/\> */
    void writeElement(const Keyword& u, const Keyword& t, const Date& val)
    {
      *m_fp << indentstring << u.stringStartElement()
          << t.stringAttribute() << string(val) << "\"/>\n";
    }

    /** Writes an element with 2 string attributes.<br>
      * Output: \<TAG_U TAG_T1="val1" TAG_T2="val2"/\> */
    void writeElement(const Keyword& u, const Keyword& t1, const string& val1,
        const Keyword& t2, const string& val2)
    {
      if(val1.empty())
        *m_fp << indentstring << u.stringStartElement() << "/>\n";
      else
        *m_fp << indentstring << u.stringStartElement()
            << t1.stringAttribute() << XMLEscape(val1.c_str()) << "\""
            << t2.stringAttribute() << XMLEscape(val2.c_str())
            << "\"/>\n";
    }

    /** Writes an element with a string and an unsigned long attribute.<br>
      * Output: \<TAG_U TAG_T1="val1" TAG_T2="val2"/\> */
    void writeElement(const Keyword& u, const Keyword& t1, unsigned long val1,
        const Keyword& t2, const string& val2)
    {
      *m_fp << indentstring << u.stringStartElement()
          << t1.stringAttribute() << val1 << "\""
          << t2.stringAttribute() << XMLEscape(val2.c_str())
          << "\"/>\n";
    }

    /** Writes an element with a short, an unsigned long and a double attribute.<br>
      * Output: \<TAG_U TAG_T1="val1" TAG_T2="val2" TAG_T3="val3"/\> */
    void writeElement(const Keyword& u, const Keyword& t1, short val1,
        const Keyword& t2, unsigned long val2, const Keyword& t3, double val3)
    {
      *m_fp << indentstring << u.stringStartElement()
          << t1.stringAttribute() << val1 << "\""
          << t2.stringAttribute() << val2 << "\""
          << t3.stringAttribute() << val3
          << "\"/>\n";
    }

    /** Writes a C-type character string.<br>
      * Output: \<TAG_T\>val\</TAG_T\> */
    void writeElement(const Keyword& t, const char* val)
    {
      if (val)
        *m_fp << indentstring << t.stringElement()
            << XMLEscape(val) << t.stringEndElement();
    }

    /** Writes an timeperiod element.<br>
      * Output: \<TAG_T\>d\</TAG_T\> /> */
    void writeElement(const Keyword& t, const TimePeriod d)
    {
      *m_fp << indentstring << t.stringElement() << d << t.stringEndElement();
    }

    /** Writes an date element.<br>
      * Output: \<TAG_T\>d\</TAG_T\> /> */
    void writeElement(const Keyword& t, const Date d)
    {
      *m_fp << indentstring << t.stringElement() << d << t.stringEndElement();
    }

    /** Writes an daterange element.<br>
      * Output: \<TAG_T\>d\</TAG_T\> */
    void writeElement(const Keyword& t, const DateRange& d)
    {
      *m_fp << indentstring << t.stringElement() << d << t.stringEndElement();
    }

    /** This method writes a serializable object.<br>
      * If an object is nested more than 2 levels deep only a reference
      * to it is written, rather than the complete object.
      * You should call this method for all objects in your xml document,
      * except for the root object.
      * @see writeElementWithHeader(const Keyword&, Object*)
      */
    DECLARE_EXPORT void writeElement(const Keyword&, const Object*, mode = DEFAULT);

    /** @see writeElement(const Keyword&, const Object*, mode) */
    void writeElement(const Keyword& t, const Object& o, mode m = DEFAULT)
    {writeElement(t,&o,m);}

    /** This method writes a serializable object with a complete XML compliant
      * header.<br>
      * You should call this method for the root object of your xml document,
      * and writeElement for all objects nested in it.
      * @see writeElement(const Keyword&, Object*)
      * @see writeHeader
      * @exception RuntimeException Generated when multiple root elements
      *    are available for the output document.
      */
    DECLARE_EXPORT void writeElementWithHeader(const Keyword& tag, const Object* object);

    /** This method writes the opening tag for an XML output.<br>
      * You should call this method or writeElementWithHeader() when writing
      * the first element of an xml document.
      * @see writeElementWithHeader
      * @exception RuntimeException Generated when multiple root elements
      *    are available for the output document.
      */
    DECLARE_EXPORT void writeHeader(const Keyword&);
    DECLARE_EXPORT void writeHeader(const Keyword&, const Keyword&, const string&);

    /** Returns a pointer to the object that is currently being saved. */
    Object* getCurrentObject() const
    {return const_cast<Object*>(currentObject);}

    /** Returns a pointer to the parent of the object that is being saved. */
    Object* getPreviousObject() const
    {return const_cast<Object*>(parentObject);}

    /** Returns the number of objects that have been serialized. */
    unsigned long countObjects() const {return numObjects;}

    /** Get a string suitable for correctly indenting the output. */
    const char* getIndent() {return indentstring;}

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
    DECLARE_EXPORT void incIndent();

    /** Decrease the indentation level. */
    DECLARE_EXPORT void decIndent();

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


/** @brief This class writes XML data to a flat file.
  *
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


/** @brief This class writes XML data to a string.
  *
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


/** @brief A class to model keyword instances.
  *
  * The class uses hashes to do a fast comparison with the set of keywords.
  */
class Attribute
{
  private:
    /** This string stores the hash value of the element. */
    hashtype hash;

    /** A pointer to the string representation of the keyword.<br>
      * The string buffer is to be managed by the code creating this
      * instance.
      */
    const char* ch;

  public:
    /** Default constructor. */
    explicit Attribute() : hash(0), ch(NULL) {}

    /** Constructor. */
    explicit Attribute(const string& n)
      : hash(Keyword::hash(n)), ch(n.c_str()) {}

    /** Constructor. */
    explicit Attribute(const char* c) : hash(Keyword::hash(c)), ch(c) {}

    /** Copy constructor. */
    Attribute(const Attribute& o) : hash(o.hash), ch(o.ch) {}

    /** Returns the hash value of this tag. */
    hashtype getHash() const {return hash;}

    /** Returns this tag. */
    void reset(const char *const c)
    {
      hash = Keyword::hash(c);
      ch = c;
    }

    /** Returns this tag. */
    void reset(const XMLCh *const c)
    {
      hash = Keyword::hash(c);
      // An XMLCh is normally a wchar, and would need to be transcoded
      // to a char. We won't bother...
      ch = NULL;
    }

    /** Return the element name. Since this method involves a lookup in a
      * table with Keywords, it has some performance impact and should be
      * avoided where possible. Only the hash of an element can efficiently
      * be retrieved.
      */
    DECLARE_EXPORT const char* getName() const;

    /** Returns true when this element is an instance of this tag. This method
      * doesn't involve a string comparison and is extremely efficient. */
    bool isA(const Keyword& t) const {return t.getHash() == hash;}

    /** Returns true when this element is an instance of this tag. This method
      * doesn't involve a string comparison and is extremely efficient. */
    bool isA(const Keyword* t) const {return t->getHash() == hash;}

    /** Comparison operator. */
    bool operator < (const Attribute& o) const {return hash < o.hash;}

    /** String comparison. */
    bool operator == (const string o) const {return o == ch;}
};


/** @brief This abstract class represents a attribute and value pair for
  * updating objects in frePPLe.
  *
  * It is instantiated in the XMLElement and PythonObject classes.
  * @todo only takes care of transformation from external format to C++. Not the C++ to external format yet.
  */
class DataElement
{
  public:
    virtual operator bool() const
    {throw LogicException("DataElement is an abstract class");}

    /** Destructor. */
    virtual ~DataElement() {}

    void operator >> (unsigned long int& val) const {val = getUnsignedLong();}

    void operator >> (long& val) const {val = getLong();}

    void operator >> (TimePeriod& val) const {val = getTimeperiod();}

    void operator >> (bool& v) const {v=getBool();}

    void operator >> (int& val) const {val = getInt();}

    void operator >> (double& val) const {val = getDouble();}

    void operator >> (Date& val) const {val = getDate();}

    void operator >> (string& val) const {val = getString();}

    virtual long getLong() const
    {throw LogicException("DataElement is an abstract class");}

    virtual unsigned long getUnsignedLong() const
    {throw LogicException("DataElement is an abstract class");}

    virtual TimePeriod getTimeperiod() const
    {throw LogicException("DataElement is an abstract class");}

    virtual int getInt() const
    {throw LogicException("DataElement is an abstract class");}

    virtual double getDouble() const
    {throw LogicException("DataElement is an abstract class");}

    virtual Date getDate() const
    {throw LogicException("DataElement is an abstract class");}

    virtual string getString() const
    {throw LogicException("DataElement is an abstract class");}

    virtual bool getBool() const
    {throw LogicException("DataElement is an abstract class");}
};


/** @brief This class represents an XML element being read in from the
  * input file. */
class XMLElement : public DataElement
{
  private:
    /** This string stores the XML input data. */
    string m_strData;

  public:
    virtual operator bool() const {return !m_strData.empty();}

    /** Default constructor. */
    XMLElement() {}

    /** Constructor. */
    XMLElement(const string& v) : m_strData(v) {}

    /** Destructor. */
    virtual ~XMLElement() {}

    /** Re-initializes an existing element. Using this method we can avoid
      * destroying and recreating XMLelement objects too frequently. Instead
      * we can manage them in a array.
      */
    void reset() {m_strData.clear();}

    /** Add some characters to this data field of this element.<br>
      * The second argument is the number of bytes, not the number of
      * characters.
      */
    void addData(const char *pData, size_t len) {m_strData.append(pData,len);}

    /** Set the data value of this element. */
    void setData(const char *pData) {m_strData.assign(pData);}

    /** Return the data field. */
    const char *getData() const {return m_strData.c_str();}

    virtual long getLong() const {return atol(getData());}

    virtual unsigned long getUnsignedLong() const {return atol(getData());}

    virtual TimePeriod getTimeperiod() const {return TimePeriod(getData());}

    virtual int getInt() const {return atoi(getData());}

    // Return the value as a double.
    // This conversion should be done with the C-locale, where a dot is used
    // as a decimal separator. Otherwise values in XML data files will be
    // read incorrectly!
    virtual double getDouble() const
    {
      return atof(getData());
    }

    virtual Date getDate() const {return Date(getData());}

    /** Returns the string value of the XML data. The xerces library takes care
      * of appropriately unescaping special character sequences. */
    virtual string getString() const {return m_strData;}

    /** Interprets the element as a boolean value.<br>
      * <p>Our implementation is a bit more generous and forgiving than the
      * boolean datatype that is part of the XML schema v2 standard.
      * The standard expects the following literals:<br>
      *   {true, false, 1, 0}</p>
      * <p>Our implementation uses only the first charater of the text, and is
      * case insensitive. It thus matches a wider range of values:<br>
      *   {t.*, T.*, f.*, F.*, 1.*, 0.*}</p>
      */
    DECLARE_EXPORT bool getBool() const;
};


/** @brief This class groups some functions used to interact with the operating
  * system environment.
  *
  * It handles:
  *   - The location of the configuration files.
  *   - The maximum number of processors / threads to be used by frePPLe.
  *   - An output stream for logging all output.
  *   - Dynamic loading of a shared library.
  */
class Environment
{
  private:
    /** Caches the number of processor cores. */
    static DECLARE_EXPORT int processorcores;

    /** A file where output is directed to. */
    static DECLARE_EXPORT ofstream logfile;

    /** The name of the log file. */
    static DECLARE_EXPORT string logfilename;

    /** A list of all loaded modules. */
    static DECLARE_EXPORT set<string> moduleRegistry;

  public:
    /** Search for a file with a given name.<br>
      * The following directories are searched in sequence to find a match:
      *   - The current directory.
      *   - The directory referred to by the variable FREPPLE_HOME, if it
      *     is defined.
      *   - The data directory as configured during the compilation.
      *     This applies only to linux / unix.
      *   - The library directory as configured during the compilation.
      *     This applies only to linux / unix.
      */
    static DECLARE_EXPORT string searchFile(const string);

    /** Returns the number of processor cores on your machine. */
    static DECLARE_EXPORT int getProcessorCores();

    /** Returns the name of the logfile. */
    static const string& getLogFile() {return logfilename;}

    /** Updates the filename for logging error messages and warnings.
      * The file is also opened for writing and the standard output and
      * standard error output streams are redirected to it.<br>
      * If the filename starts with '+' the log file is appended to
      * instead of being overwritten.
      */
    static DECLARE_EXPORT void setLogFile(const string& x);

    /** Type for storing parameters passed to a module that is loaded. */
    typedef map<string,XMLElement> ParameterList;

    /** @brief Function to dynamically load a shared library in frePPLe.
      *
      * After loading the library, the function "initialize" of the module
      * is executed.
      *
      * The current implementation supports the following platforms:
      *  - Windows
      *  - Linux
      *  - Unix systems supporting the dlopen function in the standard way.
      *    Some unix systems have other or deviating APIs. A pretty messy story :-<
      */
    static DECLARE_EXPORT void loadModule(string lib, ParameterList& parameters); //@todo replace argument with a AttributeList instead

    /** Print all modules that have been loaded. */
    static DECLARE_EXPORT void printModules();
};


/** @brief This class handles two-way translation between the data types
  * in C++ and Python.
  *
  * This class is basically a wrapper around a PyObject pointer.
  *
  * When creating a PythonObject from a C++ object, make sure to increment
  * the reference count of the object.<br>
  * When constructing a PythonObject from an existing Python object, the
  * code that provided us the PyObject pointer should have incremented the
  * reference count already.
  *
  * @todo endelement function should be shared with setattro function.
  * Unifies the python and xml worlds: shared code base to update objects!
  * (Code for extracting info is still python specific, and writeElement
  * is also xml-specific)
  * xml->prevObject = python->cast value to a different type
  *
  * @todo object creator should be common with the XML reader, which uses
  * the registered factory method.
  * Also supports add/add_change/remove.
  * Tricky: flow/load which use an additional validate() method
  */
class PythonObject : public DataElement
{
  private:
    PyObject* obj;

  public:
    /** Default constructor. The default value is equal to Py_None. */
    explicit PythonObject() : obj(Py_None) {Py_INCREF(obj);}

    /** Constructor from an existing Python object.<br>
      * The reference count isn't increased.
      */
    PythonObject(const PyObject* o)
      : obj(o ? const_cast<PyObject*>(o) : Py_None) {Py_INCREF(obj);}

    /** This conversion operator casts the object back to a PyObject pointer. */
    operator PyObject*() const {return obj;}

    /** Check for null value. */
    operator bool() const {return obj != NULL && obj != Py_None;}

    /** Assignment operator. */
    PythonObject& operator = (const PythonObject& o)
    {
      if (obj) {Py_DECREF(obj);}
      obj = o.obj;
      if (obj) {Py_INCREF(obj);}
      return *this;
    }

    /** Check whether the Python object is of a certain type.<br>
      * Subclasses of the argument type will also give a true return value.
      */
    bool check(const MetaClass* c) const
    {
      return obj ?
          PyObject_TypeCheck(obj, c->pythonClass) :
          false;
    }

    /** Check whether the Python object is of a certain type.<br>
      * Subclasses of the argument type will also give a true return value.
      */
    bool check(const PythonType& c) const
    {
      return obj ?
          PyObject_TypeCheck(obj, c.type_object()) :
          false;
    }

    /** Convert a Python string into a C++ string. */
    inline string getString() const
    {
      if (obj == Py_None)
        return string();
      else if (PyUnicode_Check(obj))
      {
        // It's a Python unicode string
        PyObject* x = PyUnicode_AsEncodedString(obj, "UTF-8", "ignore");
        string result = PyBytes_AS_STRING(x);
        Py_DECREF(x);
        return result;
      }
      else
      {
        // It's not a Python string object.
        // Call the repr() function on the object, and encode the result in UTF-8.
        PyObject* x1 = PyObject_Str(obj);
        PyObject* x2 = PyUnicode_AsEncodedString(x1, "UTF-8", "ignore");
        string result = PyBytes_AS_STRING(x2);
        Py_DECREF(x1);
        Py_DECREF(x2);
        return result;
      }
    }

    /** Extract an unsigned long from the Python object. */
    unsigned long getUnsignedLong() const
    {
      if (obj == Py_None) return 0;
      if (PyUnicode_Check(obj))
      {
        PyObject* t = PyFloat_FromString(obj);
        if (!t) throw DataException("Invalid number");
        double x = PyFloat_AS_DOUBLE(t);
        Py_DECREF(t);
        if (x < 0 || x > ULONG_MAX)
          throw DataException("Invalid number");
        return static_cast<unsigned long>(x);
      }
      return PyLong_AsUnsignedLong(obj);
    }

    /** Convert a Python datetime.date or datetime.datetime object into a
      * frePPLe date. */
    DECLARE_EXPORT Date getDate() const;

    /** Convert a Python number or string into a C++ double. */
    inline double getDouble() const
    {
      if (obj == Py_None) return 0;
      if (PyUnicode_Check(obj))
      {
        PyObject* t = PyFloat_FromString(obj);
        if (!t) throw DataException("Invalid number");
        double x = PyFloat_AS_DOUBLE(t);
        Py_DECREF(t);
        return x;
      }
      return PyFloat_AsDouble(obj);
    }

    /** Convert a Python number or string into a C++ integer. */
    inline int getInt() const
    {
      if (obj == Py_None) return 0;
      if (PyUnicode_Check(obj))
      {
        PyObject* t = PyFloat_FromString(obj);
        if (!t) throw DataException("Invalid number");
        double x = PyFloat_AS_DOUBLE(t);
        Py_DECREF(t);
        if (x < INT_MIN || x > INT_MAX)
          throw DataException("Invalid number");
        return static_cast<int>(x);
      }
      int result = PyLong_AsLong(obj);
      if (result == -1 && PyErr_Occurred())
        throw DataException("Invalid number");
      return result;
    }

    /** Convert a Python number into a C++ long. */
    inline long getLong() const
    {
      if (obj == Py_None) return 0;
      if (PyUnicode_Check(obj))
      {
        PyObject* t = PyFloat_FromString(obj);
        if (!t) throw DataException("Invalid number");
        double x = PyFloat_AS_DOUBLE(t);
        Py_DECREF(t);
        if (x < LONG_MIN || x > LONG_MIN)
          throw DataException("Invalid number");
        return static_cast<long>(x);
      }
      long result = PyLong_AsLong(obj);
      if (result == -1 && PyErr_Occurred())
        throw DataException("Invalid number");
      return result;
    }

    /** Convert a Python number into a C++ bool. */
    inline bool getBool() const
    {
      return PyObject_IsTrue(obj) ? true : false;
    }

    /** Convert a Python number as a number of seconds into a frePPLe
      * TimePeriod.<br>
      * A TimePeriod is represented as a number of seconds in Python.
      */
    TimePeriod getTimeperiod() const
    {
      if (PyUnicode_Check(obj))
      {
        // Replace the unicode object with a string encoded in the correct locale
        PyObject * utf8_string = PyUnicode_AsUTF8String(obj);
        TimePeriod t(PyBytes_AsString(utf8_string));
        Py_DECREF(utf8_string);
        return t;
      }
      long result = PyLong_AsLong(obj);
      if (result == -1 && PyErr_Occurred())
        throw DataException("Invalid number");
      return result;
    }

    /** Constructor from a pointer to an Object.<br>
      * The metadata of the Object instances allow us to create a Python
      * object that works as a proxy for the C++ object.
      */
    DECLARE_EXPORT PythonObject(Object* p);

    /** Convert a C++ string into a Unicode Python string. */
    inline PythonObject(const string& val)
    {
      if (val.empty())
      {
        obj = Py_None;
        Py_INCREF(obj);
      }
      else
        // Convert internal UTF-8 representation to unicode
        obj = PyUnicode_FromString(val.c_str());
    }

    /** Convert a C++ double into a Python number. */
    inline PythonObject(const double val)
    {
      obj = PyFloat_FromDouble(val);
    }

    /** Convert a C++ integer into a Python integer. */
    inline PythonObject(const int val)
    {
      obj = PyLong_FromLong(val);
    }

    /** Convert a C++ unsigned integer into a Python integer. */
    inline PythonObject(const unsigned int val)
    {
      obj = PyLong_FromLong(val);
    }

    /** Convert a C++ long into a Python long. */
    inline PythonObject(const long val)
    {
      obj = PyLong_FromLong(val);
    }

    /** Convert a C++ unsigned long into a Python long. */
    inline PythonObject(const unsigned long val)
    {
      obj = PyLong_FromUnsignedLong(val);
    }

    /** Convert a C++ boolean into a Python boolean. */
    inline PythonObject(const bool val)
    {
      obj = val ? Py_True : Py_False;
      Py_INCREF(obj);
    }

    /** Convert a frePPLe TimePeriod into a Python number representing
      * the number of seconds. */
    inline PythonObject(const TimePeriod val)
    {
      // A TimePeriod is represented as a number of seconds in Python
      obj = PyLong_FromLong(val);
    }

    /** Convert a frePPLe date into a Python datetime.datetime object. */
    DECLARE_EXPORT PythonObject(const Date& val);
};


/** @brief This call is a wrapper around a Python function that can be
  * called from the C++ code.
  */
class PythonFunction : public PythonObject
{
  public:
    /** Default constructor. */
    PythonFunction() : func(NULL) {}

    /** Constructor. */
    DECLARE_EXPORT PythonFunction(const string&);

    /** Constructor. */
    DECLARE_EXPORT PythonFunction(PyObject*);

    /** Copy constructor. */
    PythonFunction(const PythonFunction& o) : func(o.func)
    {
      if (func) {Py_INCREF(func);}
    }

    /** Assignment operator. */
    PythonFunction& operator= (const PythonFunction& o)
    {
      if (func) {Py_DECREF(func);}
      func = o.func;
      if (func) {Py_INCREF(func);}
      return *this;
    }

    /** Destructor. */
    ~PythonFunction() {if (func) {Py_DECREF(func);}}

    /** Conversion operator to a Python pointer. */
    operator const PyObject*() const {return func;}

    /** Conversion operator to a string. */
    operator string() const {return func ? PyEval_GetFuncName(func) : "NULL";}

    /** Conversion operator to bool. */
    operator bool() const {return func != NULL;}

    /** Call the Python function without arguments. */
    DECLARE_EXPORT PythonObject call() const;

    /** Call the Python function with one argument. */
    DECLARE_EXPORT PythonObject call(const PyObject*) const;

    /** Call the Python function with two arguments. */
    DECLARE_EXPORT PythonObject call(const PyObject*, const PyObject*) const;

  private:
    /** A pointer to the Python object. */
    PyObject* func;
};


/** @brief This class represents a dictionary of keyword + value pairs.
  *
  * This abstract class can be instantiated as XML attributes, or as a
  * Python keyword dictionary.
  *  - XML:<br>
  *    &lt;buffer name="a" onhand="10" category="A" /&gt;
  *  - Python:<br>
  *    buffer(name="a", onhand="10", category="A")
  */
class AttributeList
{
  public:
    virtual const DataElement* get(const Keyword&) const = 0;
    // @todo Iterator???

    /** Destructor. */
    virtual ~AttributeList() {}
};



/** @brief This class represents a list of XML attributes. */
class XMLAttributeList : public AttributeList
{
  private:
    XMLElement result;
    XMLInput *in;
    const xercesc::Attributes* atts;
  public:
    void setAtts(const xercesc::Attributes* c) {atts = c;}
    XMLAttributeList(const xercesc::Attributes* a, XMLInput* i) : in(i), atts(a) {}

    DECLARE_EXPORT const XMLElement* get(const Keyword& key) const;
};


/** @brief This class is a wrapper around a Python dictionary. */
class PythonAttributeList : public AttributeList
{
  private:
    PyObject* kwds;
    PythonObject result;

  public:
    PythonAttributeList(PyObject* a) : kwds(a) {}

    virtual const DataElement* get(const Keyword& k) const
    {
      if (!kwds)
      {
        const_cast<PythonAttributeList*>(this)->result = PythonObject();
        return &result;
      }
      PyObject* val = PyDict_GetItemString(kwds,k.getName().c_str());
      const_cast<PythonAttributeList*>(this)->result = PythonObject(val);
      return &result;
    }
};


/** @brief This is a base class for all Python extension types.
  *
  * When creating you own extensions, inherit from the PythonExtension
  * template class instead of this one.
  *
  * It inherits from the PyObject C struct, defined in the Python C API.<br>
  * These functions aren't called directly from Python. Python first calls a
  * handler C-function and the handler function will use a virtual call to
  * run the correct C++-method.
  *
  * Our extensions don't use the usual Python heap allocator. They are
  * created and initialized with the regular C++ new and delete. A special
  * deallocator is called from Python to delete objects when their reference
  * count reaches zero.
  */
class PythonExtensionBase : public PyObject
{
  friend DECLARE_EXPORT PyObject* getattro_handler(PyObject*, PyObject*);
  friend DECLARE_EXPORT int setattro_handler(PyObject*, PyObject*, PyObject*);
  private:
    PyObject* dict;

  public:
    /** Default constructor */
    PythonExtensionBase() : dict(NULL) {}

    /** Destructor. */
    virtual ~PythonExtensionBase()
    {
      if (PyObject::ob_refcnt > 1)
        logger << "Warning: Deleting "
          << (PyObject::ob_type->tp_name && PyObject::ob_type ? PyObject::ob_type->tp_name : "NULL")
            << " object that is still referenced "
            << (PyObject::ob_refcnt-1) << " times" << endl;
      if (dict) Py_DECREF(dict);
    }

    /** A function to force an object to be destroyed by the Python garbage
      * collection.<br>
      * Be very careful to use this!
      */
    void resetReferenceCount() {PyObject::ob_refcnt = 0;}

    /** Returns the current reference count. */
    Py_ssize_t getReferenceCount() const {return PyObject::ob_refcnt;}

    /** Initialize the object to a certain Python type. */
    inline void initType(const MetaClass *t)
    {
      PyObject_INIT(this,t->pythonClass);
    }

    /** Initialize the object to a certain Python type. */
    inline void initType(PyTypeObject *t)
    {
      PyObject_INIT(this,t);
    }

    /** Default getattro method. <br>
      * Subclasses are expected to implement an override if the type supports
      * gettattro.
      */
    virtual PyObject* getattro(const Attribute& attr)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'getattro'");
      return NULL;
    }

    /** Default setattro method. <br>
      * Subclasses are expected to implement an override if the type supports
      * settattro.
      */
    virtual int setattro(const Attribute& attr, const PythonObject& field)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'setattro'");
      return -1;
    }

    /** Default compare method. <br>
      * Subclasses are expected to implement an override if the type supports
      * compare.
      */
    virtual int compare(const PyObject* other) const
    {
      throw LogicException("Missing method 'compare'");
    }

    /** Default iternext method. <br>
      * Subclasses are expected to implement an override if the type supports
      * iteration.
      */
    virtual PyObject* iternext()
    {
      PyErr_SetString(PythonLogicException, "Missing method 'iternext'");
      return NULL;
    }

    /** Default call method. <br>
      * Subclasses are expected to implement an override if the type supports
      * calls.
      */
    virtual PyObject* call(const PythonObject& args, const PythonObject& kwds)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'call'");
      return NULL;
    }

    /** Default str method. <br>
      * Subclasses are expected to implement an override if the type supports
      * conversion to a string.
      */
    virtual PyObject* str() const
    {
      PyErr_SetString(PythonLogicException, "Missing method 'str'");
      return NULL;
    }

    /** Return the Python dictionary. */
    PyObject* const* getDict() const {return &dict;}
    PyObject** getDict() {return &dict;}

  protected:
    static vector<PythonType*> table;

    DECLARE_EXPORT static PythonType* registerPythonType(int, const type_info*);

};


/** @brief Template class to define Python extensions.
  *
  * The template argument should be your extension class, inheriting from
  * this template class:
  *   class MyClass : PythonExtension<MyClass>
  *
  * The structure of the C++ wrappers around the C Python API is heavily
  * inspired on the design of PyCXX.<br>
  * More information can be found on http://cxx.sourceforge.net
  */
template<class T>
class PythonExtension: public PythonExtensionBase, public NonCopyable
{
  public:
    /** Constructor.<br>
      * The Python metadata fields always need to be set correctly.
      */
    explicit PythonExtension()
    {
      PyObject_Init(this, getType().type_object());
    }

    /** Destructor. */
    virtual ~PythonExtension() {}

    /** This method keeps the type information object for your extension. */
    static PythonType& getType()
    {
      static PythonType* cachedTypePtr = NULL;
      if (cachedTypePtr) return *cachedTypePtr;

      // Register a new type
      cachedTypePtr = registerPythonType(sizeof(T), &typeid(T));

      // Using our own memory deallocator
      cachedTypePtr->supportdealloc( deallocator );

      return *cachedTypePtr;
    }

    /** Free the memory.<br>
      * See the note on the memory management in the class documentation
      * for PythonExtensionBase.
      */
    static void deallocator(PyObject* o) {delete static_cast<T*>(o);}
};


/** @brief Object is the abstract base class for the main entities.
  *
  * It handles to following capabilities:
  * - <b>Metadata:</b> All subclasses publish metadata about their structure.
  * - <b>Python object:</b> All objects live a double life as a Python object.
  * - <b>Callbacks:</b> When objects are created or deleted,
  *   interested classes or objects can get a callback notification.
  * - <b>Serialization:</b> Objects need to be persisted and later restored.
  *   Subclasses that don't need to be persisted can skip the implementation
  *   of the writeElement method.<br>
  *   Instances can be marked as hidden, which means that they are not
  *   serialized at all.
  */
class Object : public PythonExtensionBase
{
  public:
    /** Constructor. */
    explicit Object() {}

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
    virtual void writeElement(XMLOutput *, const Keyword &, mode=DEFAULT) const
    {throw LogicException("Class can't be persisted");}

    /** Called while restoring the model from an XML-file.<br>
      * This is called for each element within the "this" element,
      * for which the "this" element is immediate parent.<br>
      * It is called when the open element tag is encountered.
      */
    virtual DECLARE_EXPORT void beginElement(XMLInput&, const Attribute&);

    /** Called while restoring the model from an XML-file.<br>
      * This is called when the corresponding close element tag
      * is encountered, and the Data() member of pElement is valid.
      */
    virtual void endElement(XMLInput&, const Attribute&, const DataElement&) = 0;

    /** Mark the object as hidden or not. Hidden objects are not exported
      * and are used only as dummy constructs. */
    virtual void setHidden(bool b) {}

    /** Returns whether an entity is real or dummy. */
    virtual bool getHidden() const {return false;}

    /** This returns the type information on the object, a bit similar to
      * the standard type_info information. */
    virtual const MetaClass& getType() const = 0;

    /** Return the memory size of the object in bytes. */
    virtual size_t getSize() const = 0;

    /** This template function can generate a factory method for objects that
      * can be constructed with their default constructor.  */
    template <class T>
    static Object* createDefault()
    {
      return new T();
    }

    /** This template function can generate a factory method for objects that
      * need a string argument in their constructor. */
    template <class T>
    static Object* createString(const string& n)
    {
      return new T(n);
    }

    /** Template function that generates a factory method callable
      * from Python. */
    template<class T>
    static PyObject* create
    (PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    {
      try
      {
        // Find or create the C++ object
        PythonAttributeList atts(kwds);
        Object* x = T::reader(T::metadata, atts);
        // Object was deleted
        if (!x)
        {
          Py_INCREF(Py_None);
          return Py_None;
        }

        // Iterate over extra keywords, and set attributes.   @todo move this responsability to the readers...
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(kwds, &pos, &key, &value))
        {
          PythonObject field(value);
          PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
		      Attribute attr(PyBytes_AsString(key_utf8));
          Py_DECREF(key_utf8);
          if (!attr.isA(Tags::tag_name) && !attr.isA(Tags::tag_type) && !attr.isA(Tags::tag_action))
          {
            int result = x->setattro(attr, field);
            if (result && !PyErr_Occurred())
              PyErr_Format(PyExc_AttributeError,
                  "attribute '%S' on '%s' can't be updated",
                  key, Py_TYPE(x)->tp_name);
          }
        };
        Py_INCREF(x);
        return x;
      }
      catch (...)
      {
        PythonType::evalException();
        return NULL;
      }
    }

    /** Return an XML representation of the object.<br>
      * If a file object is passed as argument, the representation is directly
      * written to it.<br>
      * If no argument is given the representation is returned as a string.
      */
    static DECLARE_EXPORT PyObject* toXML(PyObject*, PyObject*);
};


/** @brief A wrapper class for a Python dictionary, thats allows serialization
  * to and from XML.
  *
  * Note that the dictionary isn't owned by this class. It remains fully owned
  * by code constructing an instance of the PythonDictionary class, following
  * the flyweight design pattern.
  */
class PythonDictionary : public Object
{
  private:
    /** Python dictionary being wrapped. */
    PyObject** dict;

    /** Temporary storage while reading. */
    string name;

    /** Temporary storage while reading. */
    string value_string;
    bool value_bool;
    Date value_date;
    double value_double;

    /** Temporary storage of the data type. */
    short type;

  public:
    /** Constructor.<br>
      * We *assume* the Python object passed is a dictionary.
      */
    explicit PythonDictionary(PyObject** d, short i) : dict(d), type(i)
      {initType(metadata);}

    /** This static method is used to read XML data into a dictionary.<br>
      * It is normally called from the beginElement() method of an object.
      */
    static DECLARE_EXPORT void read(XMLInput&, const Attribute&, PyObject**);

    /** This static method is used to write a dictionary as XML.
      * It is normally called from the writeElement() method of an object.
      */
    static DECLARE_EXPORT void write(XMLOutput*, PyObject* const*);

    void endElement(XMLInput&, const Attribute&, const DataElement&);

    static const MetaCategory *metadata;
    const MetaClass& getType() const {return *metadata;}
    size_t getSize(void) const
    {
      return sizeof(PythonDictionary) + name.size() + value_string.size();
    }
};


//
// UTILITY CLASSES FOR MULTITHREADING
//


/** @brief This class is a wrapper around platform specific mutex functions. */
class Mutex: public NonCopyable
{
  public:
#if defined(HAVE_PTHREAD_H)
    // Pthreads
    Mutex()         {pthread_mutex_init(&mtx, 0);}
    ~Mutex()        {pthread_mutex_destroy(&mtx);}
    void lock()     {pthread_mutex_lock(&mtx);}
    void unlock()   {pthread_mutex_unlock(&mtx);}
  private:
    pthread_mutex_t mtx;
#else
    // Windows critical section
    Mutex() {InitializeCriticalSection(&critsec);}
    ~Mutex()  {DeleteCriticalSection(&critsec);}
    void lock() {EnterCriticalSection(&critsec);}
    void unlock() {LeaveCriticalSection(&critsec);}
  private:
    CRITICAL_SECTION critsec;
#endif
};


/** @brief This is a convenience class that makes it easy (and
  * exception-safe) to lock a mutex in a scope.
  */
class ScopeMutexLock: public NonCopyable
{
  protected:
    Mutex& mtx;
  public:
    ScopeMutexLock(Mutex& imtx): mtx(imtx) {mtx.lock ();}
    ~ScopeMutexLock() {mtx.unlock();}
};


/** @brief This class supports parallel execution of a number of functions.
  *
  * Currently Pthreads and Windows threads are supported as the implementation
  * of the multithreading.
  */
class ThreadGroup : public NonCopyable
{
  public:
    /** Prototype of the thread function. */
    typedef void (*callable)(void*);

    /** Constructor which defaults to have as many worker threads as there are
      * cores on the machine.
      */
    ThreadGroup() : countCallables(0)
    {
      maxParallel = Environment::getProcessorCores();
    };

    /** Constructor with a predefined number of worker threads. */
    ThreadGroup(int i) : countCallables(0)
    {
      setMaxParallel(i);
    };

    /** Add a new function to be called and its argument. */
    void add(callable func, void* args)
    {
      callables.push( make_pair(func,args) );
      ++countCallables;
    }

    /** Execute all functions and wait for them to finish. */
    DECLARE_EXPORT void execute();

    /** Returns the number of parallel workers that is activated.<br>
      * By default we activate as many worker threads as there are cores on
      * the machine.
      */
    int getMaxParallel() const {return maxParallel;}

    /** Updates the number of parallel workers that is activated. */
    void setMaxParallel(int b)
    {
      if (b<1)
        throw DataException("Invalid number of parallel execution threads");
      maxParallel = b;
    }

  private:
    typedef pair<callable,void*> callableWithArgument;

    /** Mutex to protect the curCommand data field during multi-threaded
      * execution.
      * @see selectCommand
      */
    Mutex lock;

    /** Specifies the maximum number of commands in the list that can be
      * executed in parallel.
      * The default value is 1, i.e. sequential execution.<br>
      * The value of this field is NOT inherited from parent command lists.<br>
      * Note that the maximum applies to this command list only, and it isn't
      * a system-wide limit on the creation of threads.
      */
    int maxParallel;

    /** Stack with all registered functions and their invocation arguments. */
    stack<callableWithArgument> callables;

    /** Count registered callables. */
    unsigned int countCallables;

    /** This functions runs a single command execution thread. It is used as
      * a holder for the main routines of a trheaded routine.
      */
#if defined(HAVE_PTHREAD_H)
    static void* wrapper(void *arg);
#else
    static unsigned __stdcall wrapper(void *);
#endif

    /** This method selects the next function to be executed.
      * @see wrapper
      */
    DECLARE_EXPORT callableWithArgument selectNextCallable();
};


//
// RED-BLACK TREE CLASS
//

/** @brief This class implements a binary tree data structure. It is used as a
  * container for entities keyed by their name.
  *
  * Technically, the data structure can be described as a red-black tree
  * with intrusive tree nodes.
  * @see HasName
  */
class Tree : public NonCopyable
{
  public:
    /** The algorithm assigns a color to each node in the tree. The color is
      * used to keep the tree balanced.<br>
      * A node with color 'none' is a node that hasn't been inserted yet in
      * the tree.
      */
    enum NodeColor {red, black, none };

    /** @brief This class represents a node in the tree.
      *
      * Elements which we want to represent in the tree will need to inherit
      * from this class, since this tree container is intrusive.
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

        /** Comparison operator. */
        bool operator < (const TreeNode& o) {return nm < o.nm;}

        /** Constructor. */
        TreeNode(const string& n)
          : nm(n), color(none), parent(NULL), left(NULL), right(NULL)
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
        TreeNode() : color(none), parent(NULL), left(NULL), right(NULL) {}

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

    /** Destructor.<br>
      * By default, the objects in the tree are not deleted when the tree
      * is deleted. This is done for performance reasons: the program can shut
      * down faster.
      */
    ~Tree() {if(clearOnDestruct) clear();}

    /** Returns an iterator to the start of the list.<br>
      * The user will need to take care of properly acquiring a read lock on
      * on the tree object.
      */
    TreeNode* begin() const {return const_cast<TreeNode*>(header.left);}

    /** Returns an iterator pointing beyond the last element in the list.<br>
      * The user will need to take care of properly acquiring a read lock on
      * on the tree object.
      */
    TreeNode* end() const {return const_cast<TreeNode*>(&header);}

    /** Returns true if the list is empty.<br>
      * Its complexity is O(1). */
    bool empty() const {return header.parent == NULL;}

    /** Renames an existing node, and adjusts its position in the tree. */
    void rename(TreeNode* obj, string newname)
    {
      bool found;
      findLowerBound(newname, &found);
      if (found)
        throw DataException("Can't rename '" + obj->nm + "' to '"
            + newname + "': name already in use");
      erase(obj);
      // @todo: there is a small risk for multithreading trouble when the tree is unlocked between the delete and re-insert
      obj->nm = newname;
      insert(obj);
    };

    /** This method returns the number of nodes inserted in this tree.<br>
      * Its complexity is O(1), so it can be called on large trees without any
      * performance impact.
      */
    size_t size() const {return count;}

    /** Verifies the integrity of the tree and returns true if everything
      * is correct.<br>
      * The tree should be locked before calling this function.
      */
    DECLARE_EXPORT void verify() const;

    /** Remove all elements from the tree. */
    DECLARE_EXPORT void clear();

    /** Remove a node from the tree. */
    DECLARE_EXPORT void erase(TreeNode* x);

    /** Search for an element in the tree.<br>
      * Profiling shows this function has a significant impact on the CPU
      * time (mainly because of the string comparisons), and has been
      * optimized as much as possible.
      */
    TreeNode* find(const string& k) const
    {
      int comp;
      for (TreeNode* x = header.parent; x; x = comp<0 ? x->left : x->right)
      {
        comp = k.compare(x->nm);
        if (!comp) return x;
      }
      TreeNode* result = end();
      return result;
    }

    /** Find the element with this given key or the element
      * immediately preceding it.<br>
      * The second argument is a boolean that is set to true when the
      * element is found in the list.
      */
    TreeNode* findLowerBound(const string& k, bool* f) const
    {
      TreeNode* lower = end();
      for (TreeNode* x = header.parent; x;)
      {
        int comp = k.compare(x->nm);
        if (!comp)
        {
          // Found
          if (f) *f = true;
          return x;
        }
        if (comp<0) x = x->left;
        else lower = x, x = x->right;
      }
      if (f) *f = false;
      return lower;
    }

    /** Insert a new node in the tree. */
    TreeNode* insert(TreeNode* v) {return insert(v, NULL);}

    /** Insert a new node in the tree. The second argument is a hint on
      * the proper location in the tree.<br>
      * Profiling shows this function has a significant impact on the cpu
      * time (mainly because of the string comparisons), and has been
      * optimized as much as possible.
      */
    DECLARE_EXPORT TreeNode* insert(TreeNode* v, TreeNode* hint);

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

/** @brief Abstract base class for all commands.
  *
  * Command objects are designed for algorithms that need to keep track of
  * their decision, efficiently undo them and redo them.
  *
  * The key methods are:
  *   - The constructor or other methods on the concrete subclasses
  *     implement the state change.
  *   - commit():
  *     Makes the change permanently.
  *     Undoing the change is no longer possible after calling this method.
  *   - rollback():
  *     Reverts the change permanently.
  *     Redoing the change is no longer possible after calling this method.
  *   - undo():
  *     Temporarily reverts the change.
  *     Redoing the change is still possible.
  *   - redo():
  *     Reactivates the change that was previously undone.
  */
class Command
{
    friend class CommandList;
    friend class CommandManager;
    friend class frepple::CommandMoveOperationPlan;
  public:
    /** Default constructor. The creation of a command should NOT execute the
      * command yet. The execute() method needs to be called explicitly to
      * do so.
      */
    Command() : owner(NULL), next(NULL), prev(NULL) {};

    /** This method makes the change permanent.<br>
      * A couple of notes on how this method should be implemented by the
      * subclasses:
      *   - Calling the method multiple times is harmless. Only the first
      *     call is expected to do something.
      */
    virtual void commit() {};

    /** This method permanently undoes the change.<br>
      * A couple of notes on how this method should be implemented by the
      * subclasses:
      *   - Calling the rollback() method multiple times is harmless. Only
      *     the first call is expected to do something.
      */
    virtual void rollback() {};

    /** This method temporarily undoes the change. The concrete subclasses
      * most maintain information that enables redoing the changes
      * efficiently.<br>
      * A couple of notes on how this method should be implemented by the
      * subclasses:
      *   - Calling the method multiple times is harmless and results in the
      *     same state change as calling it only once.
      */
    virtual void undo() {};

    /** This method reproduces a previously undone change.<br>
      * A couple of notes on how this method should be implemented by the
      * subclasses:
      *   - Calling the method multiple times is harmless and results in the
      *     same state change as calling it only once.
      */
    virtual void redo() {};

    /** Destructor. */
    virtual ~Command() {};

  private:
    /** Points to the commandlist which owns this command. The default value
      * is NULL, meaning there is no owner. */
    Command *owner;

    /** Points to the next command in the owner command list.<br>
      * The commands are chained in a double linked list data structure. */
    Command *next;

    /** Points to the previous command in the owner command list.<br>
      * The commands are chained in a double linked list data structure. */
    Command *prev;
};


/** @brief A container command to group a series of commands together.
  *
  * This class implements the "composite" design pattern in order to get an
  * efficient and intuitive hierarchical grouping of commands.
  * @todo handle exceptions during commit, rollback, undo, redo
  */
class CommandList : public Command
{
  private:
    /** Points to the first command in the list.<br>
      * Following commands can be found by following the next pointers
      * on the commands.<br>
      * The commands are this chained in a double linked list data structure.
      */
    Command* firstCommand;

    /** Points to the last command in the list. */
    Command* lastCommand;
  public:
    class iterator
    {
      public:
        /** Constructor. */
        iterator(Command* x) : cur(x) {}

        /** Copy constructor. */
        iterator(const iterator& it) {cur = it.cur;}

        /** Return the content of the current node. */
        Command& operator*() const {return *cur;}

        /** Return the content of the current node. */
        Command* operator->() const {return cur;}

        /** Pre-increment operator which moves the pointer to the next
          * element. */
        iterator& operator++()
        {
          cur = cur->next;
          return *this;
        }

        /** Post-increment operator which moves the pointer to the next
          * element. */
        iterator operator++(int)
        {
          iterator tmp = *this;
          cur = cur->next;
          return tmp;
        }

        /** Comparison operator. */
        bool operator==(const iterator& y) const {return cur==y.cur;}

        /** Inequality operator. */
        bool operator!=(const iterator& y) const {return cur!=y.cur;}

      private:
        Command* cur;
    };

    /** Returns an iterator over all commands in the list. */
    iterator begin() const {return iterator(firstCommand);}

    /** Returns an iterator beyond the last command. */
    iterator end() const {return iterator(NULL);}

    /** Append an additional command to the end of the list. */
    DECLARE_EXPORT void add(Command* c);

    /** Undoes all actions on the list.<br>
      * At the end it also clears the list of actions.
      */
    virtual DECLARE_EXPORT void rollback();

    /** Commits all actions on its list.<br>
      * At the end it also clears the list of actions.
      */
    virtual DECLARE_EXPORT void commit();

    /** Undoes all actions on its list.<br>
      * The list of actions is left intact, so the changes can still be redone.
      */
    virtual DECLARE_EXPORT void undo();

    /** Redoes all actions on its list.<br>
      * The list of actions is left intact, so the changes can still be undone.
      */
    DECLARE_EXPORT void redo();

    /** Returns true if no commands have been added yet to the list. */
    bool empty() const {return firstCommand==NULL;}

    /** Default constructor. */
    explicit CommandList() : firstCommand(NULL), lastCommand(NULL) {}

    /** Destructor.<br>
      * A commandlist should only be deleted when all of its commands
      * have been committed or undone. If this is not the case a warning
      * will be printed.
      */
    virtual DECLARE_EXPORT ~CommandList();
};


/** @brief This class allows management of tasks with supporting commiting them,
  * rolling them back, and setting bookmarks which can be undone and redone.
  */
class CommandManager
{
  public:
    /** A bookmark that keeps track of commands that can be undone and redone. */
    class Bookmark : public CommandList
    {
        friend class CommandManager;
      private:
        bool active;
        Bookmark* nextBookmark;
        Bookmark* prevBookmark;
        Bookmark* parent;
        Bookmark(Bookmark* p=NULL) : active(true),
          nextBookmark(NULL), prevBookmark(NULL), parent(p) {}
      public:
        /** Returns true if the bookmark commands are active. */
        bool isActive() const {return active;}

        /** Returns true if the bookmark is a child, grand-child or
          * grand-grand-child of the argument bookmark.
          */
        bool isChildOf(const Bookmark* b) const
        {
          for (const Bookmark* p = this; p; p = p->parent)
            if (p == b) return true;
          return false;
        }
    };

    /** An STL-like iterator to move over all bookmarks in forward order. */
    class iterator
    {
      public:
        /** Constructor. */
        iterator(Bookmark* x) : cur(x) {}

        /** Copy constructor. */
        iterator(const iterator& it) {cur = it.cur;}

        /** Return the content of the current node. */
        Bookmark& operator*() const {return *cur;}

        /** Return the content of the current node. */
        Bookmark* operator->() const {return cur;}

        /** Pre-increment operator which moves the pointer to the next
          * element. */
        iterator& operator++()
        {
          cur = cur->nextBookmark;
          return *this;
        }

        /** Post-increment operator which moves the pointer to the next
          * element. */
        iterator operator++(int)
        {
          iterator tmp = *this;
          cur = cur->nextBookmark;
          return tmp;
        }

        /** Comparison operator. */
        bool operator==(const iterator& y) const {return cur==y.cur;}

        /** Inequality operator. */
        bool operator!=(const iterator& y) const {return cur!=y.cur;}

      private:
        Bookmark* cur;
    };

    /** An STL-like iterator to move over all bookmarks in reverse order. */
    class reverse_iterator
    {
      public:
        /** Constructor. */
        reverse_iterator(Bookmark* x) : cur(x) {}

        /** Copy constructor. */
        reverse_iterator(const reverse_iterator& it) {cur = it.cur;}

        /** Return the content of the current node. */
        Bookmark& operator*() const {return *cur;}

        /** Return the content of the current node. */
        Bookmark* operator->() const {return cur;}

        /** Pre-increment operator which moves the pointer to the next
          * element. */
        reverse_iterator& operator++()
        {
          cur = cur->prevBookmark;
          return *this;
        }

        /** Post-increment operator which moves the pointer to the next
          * element. */
        reverse_iterator operator++(int)
        {
          reverse_iterator tmp = *this;
          cur = cur->prevBookmark;
          return tmp;
        }

        /** Comparison operator. */
        bool operator==(const reverse_iterator& y) const {return cur==y.cur;}

        /** Inequality operator. */
        bool operator!=(const reverse_iterator& y) const {return cur!=y.cur;}

      private:
        Bookmark* cur;
    };

  private:
    /** Head of a list of bookmarks.<br>
      * A command manager has always at least this default bookmark.
      */
    Bookmark firstBookmark;

    /** Tail of a list of bookmarks. */
    Bookmark* lastBookmark;

    /** Current bookmarks.<br>
      * If commands are added to the manager, this is the bookmark where
      * they'll be appended to.
      */
    Bookmark* currentBookmark;

  public:
    /** Constructor. */
    CommandManager()
    {
      lastBookmark = &firstBookmark;
      currentBookmark = &firstBookmark;
    }

    /** Destructor. */
    ~CommandManager()
    {
      for (Bookmark* i = lastBookmark; i && i != &firstBookmark; )
      {
        Bookmark* tmp = i;
        i = i->prevBookmark;
        delete tmp;
      }
    }

    /** Returns an iterator over all bookmarks in forward direction. */
    iterator begin() {return iterator(&firstBookmark);}

    /** Returns an iterator beyond the last bookmark in forward direction. */
    iterator end() {return iterator(NULL);}

    /** Returns an iterator over all bookmarks in reverse direction. */
    reverse_iterator rbegin() {return reverse_iterator(lastBookmark);}

    /** Returns an iterator beyond the last bookmark in reverse direction. */
    reverse_iterator rend() {return reverse_iterator(NULL);}

    /** Add a command to the active bookmark. */
    void add(Command* c) {currentBookmark->add(c);}

    /** Create a new bookmark. */
    DECLARE_EXPORT Bookmark* setBookmark();

    /** Undo all commands in a bookmark (and its children).<br>
      * It can later be redone.<br>
      * The active bookmark in the manager is set to the parent of
      * argument bookmark.
      */
    DECLARE_EXPORT void undoBookmark(Bookmark*);

    /** Redo all commands in a bookmark (and its children).<br>
      * It can later still be undone.<br>
      * The active bookmark in the manager is set to the argument bookmark.
      */
    DECLARE_EXPORT void redoBookmark(Bookmark*);

    /** Undo all commands in a bookmark (and its children).<br>
      * It can no longer be redone. The bookmark does however still exist.
      */
    DECLARE_EXPORT void rollback(Bookmark*);

    /** Commit all commands. */
    DECLARE_EXPORT void commit();

    /** Rolling back all commands. */
    DECLARE_EXPORT void rollback();
};


//
// INPUT PROCESSING CLASSES
//


/** @brief This class will read in an XML-file and call the appropriate
  * handler functions of the Object classes and objects.
  *
  * This class is implemented based on the Xerces SAX XML parser.
  * For debugging purposes a flag is defined at the start of the file
  * "xmlparser.cpp". Uncomment the line and recompile to use it.
  *
  * FrePPLe creates a new parser and loads the XML schema every time
  * XML data need to be parsed. When this happens only a few times during a
  * run this is good enough.<br>
  * However, when the libary has to parse plenty of small XML messages this
  * will create a significant overhead. The code would need to be enhanced
  * to maintain a pool of parsers and cache their grammars.
  */
class XMLInput : public NonCopyable,  private xercesc::DefaultHandler
{
  public:
    typedef pair<Attribute,XMLElement> datapair;

  private:
    /** A transcoder to encoding to UTF-8. */
    static xercesc::XMLTranscoder* utf8_encoder;

    /** A pointer to an XML parser for processing the input. */
    xercesc::SAX2XMLReader* parser;

    /** This type defines the different states the parser can have. */
    enum state
    {
      /** The parser is sending input to an object handler. */
      READOBJECT,
      /** The parser has been instructed to ignore a tag. */
      IGNOREINPUT,
      /** The parser is shutting down, and will ignore all further data. */
      SHUTDOWN,
      /** This state is only used when the parser starts processing its first
        * tag. */
      INIT
    };

    /** This variable defines the maximum depth of the object creation stack.
      * This maximum is intended to protect us from malicious malformed
      * xml-documents, and also for allocating efficient data structures for
      * the parser.
      */
    const unsigned short maxdepth;

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
    vector< pair<Object*,void*> > m_EHStack;

    /** Stack of elements.<br>
      * The expression m_EStack[numElements+1] returns the current element.<br>
      * The expression m_EStack[numElements] returns the parent element.
      * @see numElements
      */
    vector<datapair> m_EStack;

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
      *  - Setting the flag to true is most appropriate to process small and
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
    XMLAttributeList attributes;

    /** A buffer used for transcoding XML data. */
    char encodingbuffer[4*1024];

    /** A Python callback function that is called once an object has been read
      * from the XML input. The return value is not used.
      */
    PythonFunction userexit;

    /** Handler called when a new element tag is encountered.
      * It pushes a new element on the stack and calls the current handler.
      */
    DECLARE_EXPORT void startElement (const XMLCh* const, const XMLCh* const,
        const XMLCh* const, const xercesc::Attributes&);

    /** A value to populate on the source field of all entities being created
      * or updated from the XML input data.
      */
    string source;

    /** Handler called when closing element tag is encountered.
      * If this is the closing tag for the current event handler, pop it
      * off the handler stack. If this empties the stack, shut down parser.
      * Otherwise, just feed the element with the already completed
      * data section to the current handler, then pop it off the element
      * stack.
      */
    DECLARE_EXPORT void endElement
    (const XMLCh* const, const XMLCh* const, const XMLCh* const);

    /** Handler called when character data are read in.
      * The data string is add it to the current element data.
      */
#if XERCES_VERSION_MAJOR==2
    DECLARE_EXPORT void characters(const XMLCh *const, const unsigned int);
#else
    DECLARE_EXPORT void characters(const XMLCh *const, const XMLSize_t);
#endif

    /** Handler called by Xerces in fatal error conditions. It throws an
      * exception to abort the parsing procedure. */
    DECLARE_EXPORT void fatalError (const xercesc::SAXParseException&);

    /** Handler called by Xercess when reading a processing instruction. The
      * handler looks up the target in the repository and will call the
      * registered XMLinstruction.
      * @see XMLinstruction
      */
    DECLARE_EXPORT void processingInstruction (const XMLCh *const, const XMLCh *const);

    /** Handler called by Xerces in error conditions. It throws an exception
      * to abort the parsing procedure. */
    DECLARE_EXPORT void error (const xercesc::SAXParseException&);

    /** Handler called by Xerces for warnings. */
    DECLARE_EXPORT void warning (const xercesc::SAXParseException&);

    /** This method cleans up the parser state to get it ready for processing
      * a new document. */
    DECLARE_EXPORT void reset();

    /** Return a pointer to the current object being read in.  */
    inline Object* getCurrentObject() const {return m_EHStack[m_EHStack.size()-1].first;}

  public:
    /** Constructor.
      * @param maxNestedElmnts Defines the maximum depth of elements an XML
      * document is allowed to have. The default is 20.
      */
    DECLARE_EXPORT XMLInput(unsigned short maxNestedElmnts = 20);

    /** Destructor. */
    virtual ~XMLInput() {reset();}

    /** Return a pointer to an array of character pointer which point
      * to the attributes. See the xerces documentation if this description
      * doesn't satisfy you...
      */
    const AttributeList& getAttributes() const {return attributes;}

    /** Redirect event stream into a new Object.<br>
      * It is also possible to pass a NULL pointer to the function. In
      * that situation, we simple ignore the content of that element.<br>
      * Important: The user is reponsible of making sure the argument
      * object has a proper write-lock. The release of that lock is handled
      * by the parser.
      */
    DECLARE_EXPORT void readto(Object*);

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

    /** Invalidates the current object.<br>
      * This method is useful when, for instance, the object being parsed
      * is being deleted.
      */
    void invalidateCurrentObject()
    {
      if (!m_EHStack.empty())
        m_EHStack[m_EHStack.size()-1].first = NULL;
    }

    /** Return a pointer to the previous object being read in.<br>
      * In a typical use the returned pointer will require a dynamic_cast
      * to a subclass type.<br>
      * The typical usage is as follows:
      * <pre>
      *   Operation *o = dynamic_cast<Operation*>(pIn.getPreviousObject());
      *   if (o) doSomeThing(o);
      *   else throw LogicException("Incorrect object type");
      * </pre>
      */
    Object* getPreviousObject() const {return prev;}

    /** Clears the previously read object. */
    Object* getParentObject() const
    {
      size_t x = m_EHStack.size();
      return x>1 ? m_EHStack[x-2].first : NULL;
    }

    /** Returns a reference to the parent element. */
    const datapair& getParentElement() const
    {return m_EStack[numElements>0 ? numElements : 0];}

    /** Returns a reference to the current element. */
    const datapair& getCurrentElement() const
    {return m_EStack[numElements>-1 ? numElements+1 : 0];}

    /** This is the core parsing function, which triggers the XML parser to
      * start processing the input. It is normally called from the method
      * parse(Object*) once a proper stream has been created.
      * @see parse(Object*)
      */
    void parse(xercesc::InputSource&, Object*, bool=false);

    /** Updates the user definable pointer. This pointer is used to store
      * status information between handler calls. */
    void setUserArea(void* v)
    {if (!m_EHStack.empty()) m_EHStack[m_EHStack.size()-1].second = v;}

    /** Returns the user definable pointer. */
    void* getUserArea() const
    {return m_EHStack.empty() ? NULL : m_EHStack[m_EHStack.size()-1].second;}

    /** Updates whether we ignore data exceptions or whether we abort the
      * processing of the XML data stream. */
    void setAbortOnDataError(bool i) {abortOnDataException = i;}

    /** Returns the behavior of the parser in case of data errors.<br>
      * When true is returned, the processing of the XML stream continues
      * after a DataException. Other, more critical, exceptions types will
      * still abort the parsing process.<br>
      * False indicates that the processing of the XML stream is aborted.
      */
    bool getAbortOnDataError() const {return abortOnDataException;}

    /** Specify a Python callback function that is for every object read
      * from the input stream.
      */
    void setUserExit(PyObject* p) {userexit = p;}

    /** Return the Python callback function. */
    PythonFunction getUserExit() const {return userexit;}

    /** Transcode the Xerces XML characters to our UTF8 encoded buffer. */
    char* transcodeUTF8(const XMLCh*);

    /** Return the source field that will be populated on each object created
      * or updated from the XML data.
      */
    string getSource() const {return source;}

    /** Update the source field that will be populated on each object created
      * or updated from the XML data.
      */
    void setSource(string s) {source = s;}

  protected:
    /** The real parsing job is delegated to subclasses.
      * Subclass can then define the specifics for parsing a flat file,
      * a string, a SOAP message, etc...
      * @exception RuntimeException Thrown in the following situations:
      *    - the XML-document is incorrectly formatted
      *    - the XML-parser librabry can't be initialized
      *    - no memory can be allocated to the xml-parser
      * @exception DataException Thrown when the data can't be processed
      *   normally by the objects being created or updated.
      */
    virtual void parse(Object* s, bool b=false)
    {
      throw LogicException("Unreachable code reached");
    }
};


/** @brief This class reads XML data from a string. */
class XMLInputString : public XMLInput
{
  public:
    /** Default constructor. */
    XMLInputString(const string& s) : data(s) {};

    /** Parse the specified string. */
    void parse(Object* pRoot, bool v = false)
    {
      /* The MemBufInputSource expects the number of bytes as second parameter.
       * In our case this is the same as the number of characters, but this
       * will not apply any more for character sets with multi-byte
       * characters.
       */
      xercesc::MemBufInputSource a(
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


/** @brief This class reads XML data from a file system.
  *
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
    DECLARE_EXPORT void parse(Object*, bool=false);

  private:
    /** Name of the file to be opened. */
    string filename;
};


//
//  UTILITY CLASSES "HASNAME", "HASHIERARCHY", "HASDESCRIPTION"
//


/** @brief Base class for objects using a string as their primary key.
  *
  * Instances of this class have the following properties:
  *   - Have a unique name.
  *   - A hashtable (keyed on the name) is maintained as a container with
  *     all active instances.
  */
template <class T> class HasName : public NonCopyable, public Tree::TreeNode, public Object
{
  private:
    /** Maintains a global list of all created entities. The list is keyed
      * by the name. */
    static DECLARE_EXPORT Tree st;
    typedef T* type;

  public:
    /** @brief This class models a STL-like iterator that allows us to
      * iterate over the named entities in a simple and safe way.
      *
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

    /** Returns a STL-like iterator to the end of the entity list. */
    static iterator end() {return st.end();}

    /** Returns a STL-like iterator to the start of the entity list. */
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

    /** Constructor. */
    explicit HasName(const string& n) : Tree::TreeNode(n) {}

    /** Constructor. */
    explicit HasName(const char* n) : Tree::TreeNode(n) {}

    /** Rename the entity. */
    void setName(const string& newname) {st.rename(this, newname);}

    /** Destructor. */
    DECLARE_EXPORT ~HasName() {st.erase(this);}

    /** Return the name as the string representation in Python. */
    virtual PyObject* str() const {return PythonObject(getName());}

    /** Comparison operator for Python. */
    int compare(const PyObject* other) const
    {
      return getName().compare(static_cast<const T*>(other)->getName());
    }

    /** Find an entity given its name. In case it can't be found, a NULL
      * pointer is returned. */
    static T* find(const string& k)
    {
      Tree::TreeNode *i = st.find(k);
      return (i!=st.end() ? static_cast<T*>(i) : NULL);
    }

    /** Find the element with this given key or the element
      * immediately preceding it.<br>
      * The optional second argument is a boolean that is set to true when
      * the element is found in the list.
      */
    static T* findLowerBound(const string& k, bool *f = NULL)
    {
      Tree::TreeNode *i = st.findLowerBound(k, f);
      return (i!=st.end() ? static_cast<T*>(i) : NULL);
    }

    /** Creates a new entity. */
    static T* add(const string& k, const MetaClass& cls)
    {
      Tree::TreeNode *i = st.find(k);
      if (i!=st.end()) return static_cast<T*>(i); // Exists already
      if (*(cls.category) != T::metadata)
        throw LogicException("Invalid type " + cls.type +
            " for creating an object of category " + T::metadata.type);
      T *t = static_cast<T*>(cls.factoryMethodString(k));
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

    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement) {};

    /** This method is available as a object creation factory for
      * classes that are using a string as a key identifier, in particular
      * classes derived from the HasName base class.
      * The following attributes are recognized:
      * - name:<br>
      *   Name of the entity to be created/changed/removed.<br>
      *   The default value is "unspecified".
      * - type:<br>
      *   Determines the subclass to be created.<br>
      *   The default value is "default".
      * - action:<br>
      *   Determines the action to be performed on the object.<br>
      *   This can be A (for 'add'), C (for 'change'), AC (for 'add_change')
      *   or R (for 'remove').<br>
      *   'add_change' is the default value.
      * @see HasName
      */
    static Object* reader (const MetaClass* cat, const AttributeList& in)
    {
      // Pick up the action attribute
      Action act = MetaClass::decodeAction(in);

      // Pick up the name attribute. An error is reported if it's missing.
      const DataElement* nameElement = in.get(Tags::tag_name);
      if (!*nameElement) throw DataException("Missing name attribute");
      string name = nameElement->getString();

      // Check if it exists already
      bool found;
      T *i = T::findLowerBound(name, &found);

      // Validate the action
      switch (act)
      {
        case ADD:
          // Only additions are allowed
          if (found)
            throw DataException("Object '" + name + "' already exists");
          break;

        case CHANGE:
          // Only changes are allowed
          if (!found)
            throw DataException("Object '" + name + "' doesn't exist");
          return i;

        case REMOVE:
          // Delete the entity
          if (found)
          {
            // Send out the notification to subscribers
            if (i->getType().raiseEvent(i,SIG_REMOVE))
            {
              // Delete the object
              delete i;
              return NULL;
            }
            else
              // The callbacks disallowed the deletion!
              throw DataException("Can't remove object '" + name + "'");
          }
          else
            // Not found
            throw DataException("Can't find object '" + name + "' for removal");
        default:
          // case ADD_CHANGE doesn't have special cases.
          ;
      }

      // Return the existing instance
      if (found) return i;

      // Lookup the type in the map
      const MetaClass* j;
      if (cat->category)
        // Class metadata passed: we already know what type to create
        j = cat;
      else
      {
        // Category metadata passed: we need to look up the type
        const DataElement* type = in.get(Tags::tag_type);
        j = static_cast<const MetaCategory&>(*cat).findClass(
            *type ? Keyword::hash(type->getString()) : MetaCategory::defaultHash
            );
        if (!j)
        {
          string t(*type ? type->getString() : "default");
          throw DataException("No type " + t + " registered for category " + cat->type);
        }
      }

      // Create a new instance
      T* x = static_cast<T*>(j->factoryMethodString(name));

      // Run creation callbacks
      // During the callback there is no write lock set yet, since we can
      // assume we are the only ones aware of this new object. We also want
      // to make sure the 'add' signal comes before the 'before_change'
      // callback that is part of the writelock.
      if (!x->getType().raiseEvent(x,SIG_ADD))
      {
        // Creation isn't allowed
        delete x;
        throw DataException("Can't create object " + name);
      }

      // Insert in the tree
      T::add(x, i);
      return x;
    }

    /** A handler that is used to persist the tree. */
    static void writer(const MetaCategory* c, XMLOutput* o)
    {
      if (empty()) return;
      o->BeginObject(*(c->grouptag));
      for (iterator i = begin(); i != end(); ++i)
        o->writeElement(*(c->typetag), *i);
      o->EndObject(*(c->grouptag));
    }
};


/** @brief This is a decorator class for all objects having a source field. */
class HasSource
{
  private:
    string source;
  public:
    /** Returns the source field. */
    string getSource() const {return source;}

    /** Sets the source field. */
    void setSource(string c) {source = c;}
};


/** @brief This is a decorator class for the main objects.
  *
  * Instances of this class have a description, category and sub_category.
  */
class HasDescription : public HasSource
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

    void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    void endElement(XMLInput&, const Attribute&, const DataElement&);

  protected:
    /** Returns the memory size in bytes. */
    size_t extrasize() const {return cat.size() + subcat.size() + descr.size() + getSource().size();}

  private:
    string cat;
    string subcat;
    string descr;
};


/** @brief This is a base class for the main objects.
  *
  * Instances of this class have the following properties:
  *  - Unique name and global hashtable are inherited from the class HasName.
  *  - Instances build up hierarchical trees of arbitrary depth.
  *  - Each object can have a single parent only.
  *  - Each object has a parent and can have children.
  *    This class thus implements the 'composite' design pattern.
  * The internal data structure is a singly linked linear list, which is
  * efficient provided the number of childre remains limited.
  */
template <class T> class HasHierarchy : public HasName<T>
{
  public:
    class memberIterator;
    friend class memberIterator;
    /** @brief This class models an STL-like iterator that allows us to
      * iterate over the members.
      *
      * Objects of this class are created by the beginMember() method.
      */
    class memberIterator
    {
      public:
        /** Constructor to iterate over member entities. */
        memberIterator(const HasHierarchy<T>* x) : member_iter(true)
        {curmember = const_cast<HasHierarchy<T>*>(x)->first_child;}

        /** Constructor to iterate over all entities. */
        memberIterator() : curmember(&*T::begin()), member_iter(false) {}

        /** Constructor. */
        memberIterator(const typename HasName<T>::iterator& it) : curmember(&*it), member_iter(false) {}

        /** Copy constructor. */
        memberIterator(const memberIterator& it)
        {
          curmember = it.curmember;
          member_iter = it.member_iter;
        }

        /** Return the content of the current node. */
        T& operator*() const {return *static_cast<T*>(curmember);}

        /** Return the content of the current node. */
        T* operator->() const {return static_cast<T*>(curmember);}

        /** Pre-increment operator which moves the pointer to the next member. */
        memberIterator& operator++()
        {
          if (member_iter)
            curmember = curmember->next_brother;
          else
            curmember = static_cast<T*>(curmember->increment());
          return *this;
        }

        /** Post-increment operator which moves the pointer to the next member. */
        memberIterator operator++(int)
        {
          memberIterator tmp = *this;
          if (member_iter)
            curmember = curmember->next_brother;
          else
            curmember = static_cast<T*>(curmember->increment());
          return tmp;
        }

        /** Comparison operator. */
        bool operator==(const memberIterator& y) const
        {return curmember == y.curmember;}

        /** Inequality operator. */
        bool operator!=(const memberIterator& y) const
        {return curmember != y.curmember;}

        /** Comparison operator. */
        bool operator==(const typename HasName<T>::iterator& y) const
        {return curmember ? (curmember == &*y) : (y == T::end());}

        /** Inequality operator. */
        bool operator!=(const typename HasName<T>::iterator& y) const
        {return curmember ? (curmember != &*y) : (y != T::end());}

      private:
        /** Points to a member. */
        HasHierarchy<T>* curmember;
        bool member_iter;
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

    /** Return a member iterator. */
    memberIterator beginMember() const {return this;}

    /** Returns true if this entity belongs to a higher hierarchical level.<br>
      * An entity can have only a single owner, and can't belong to multiple
      * hierarchies.
      */
    bool hasOwner() const {return parent!=NULL;}

    /** Returns true if this entity has lower level entities belonging to
      * it. */
    bool isGroup() const {return first_child!=NULL;}

    /** Changes the owner of the entity.<br>
      * The argument must be a valid pointer to an entity of the same type.<br>
      * A NULL pointer can be passed to clear the existing owner.<br>
      */
    void setOwner(T* f);

    /** Returns the owning entity. */
    T* getOwner() const {return parent;}

    /** Returns the level in the hierarchy.<br>
      * Level 0 means the entity doesn't have any parent.<br>
      * Level 1 means the entity has a parent entity with level 0.<br>
      * Level "x" means the entity has a parent entity whose level is "x-1".
      */
    unsigned short getHierarchyLevel() const;

    void beginElement(XMLInput&, const Attribute&);
    void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    void endElement(XMLInput&, const Attribute&, const DataElement&);

  private:
    /** A pointer to the parent object. */
    T *parent;

    /** A pointer to the first child object. */
    T *first_child;

    /** A pointer to the next brother object, ie an object having the
      * same parent.<br>
      * The brothers are all linked as a single linked list, with the
      * first_child pointer on the parent being the root pointer of the list.
      */
    T *next_brother;
};


//
// ASSOCIATION
//

/** @brief This template class represents a data structure for a load or flow
  * network.
  *
  * A node class has pointers to 2 root classes.<br> The 2 root classes each
  * maintain a singly linked list of nodes.<br>
  * An example to clarify the usage:
  *  - class "node" = a newspaper subscription.
  *  - class "person" = maintains a list of all his subscriptions.
  *  - class "newspaper" = maintains a list of all subscriptions for it.
  *
  * This data structure could be replaced with 2 linked lists, but this
  * specialized data type consumes considerably lower memory.
  *
  * Reading from the structure is safe in multi-threading mode.<br>
  * Updates to the data structure in a multi-threading mode require the user
  * to properly lock and unlock the container.
  */
template <class A, class B, class C> class Association
{
  public:
    class Node;
  private:
    /** @brief A abstract base class for the internal representation of the
      * association lists.
      */
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
    /** @brief A list type of the "first" / "from" part of the association. */
    class ListA : public List
    {
      public:
        ListA() {};
        /** @brief An iterator over the associated objects. */
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
        /** @brief An iterator over the associated objects. */
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

        /** Destructor. */
        ~ListA()
        {
          C* next;
          for (C* p=this->first; p; p=next)
          {
            next = p->nextA;
            delete p;
          }
        }

        /** Remove an association. */
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

        /** Return the number of associations. */
        size_t size() const
        {
          size_t i(0);
          for (C* p = this->first; p; p=p->nextA) ++i;
          return i;
        }

        /** Search for the association effective at a certain date. */
        C* find(const B* b, Date d = Date::infinitePast) const
        {
          for (C* p=this->first; p; p=p->nextA)
            if (p->ptrB == b && p->effectivity.within(d)) return p;
          return NULL;
        }

        /** Search for the association with a certain name. */
        C* find(const string& n) const
        {
          for (C* p=this->first; p; p=p->nextA)
            if (p->name == n) return p;
          return NULL;
        }

        /** Move an association a position up in the list of associations. */
        void promote(C* p)
        {
          // Already at the head
          if (p == this->first) return;

          // Scan the list
          C* prev = NULL;
          for (C* ptr = this->first; ptr; ptr = ptr->nextA)
          {
            if (ptr->nextA == p)
            {
              if (prev)
                prev->nextA = p;
              else
                this->first = p;
              ptr->nextA = p->nextA;
              p->nextA = ptr;
              return;
            }
            prev = ptr;
          }
          throw LogicException("Association not found in the list");
        }
    };

    /** @brief A list type of the "second" / "to" part of the association. */
    class ListB : public List
    {
      public:
        ListB() {};
        /** @brief An iterator over the associated objects. */
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
        /** @brief An iterator over the associated objects. */
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

        /** Destructor. */
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

        /** Remove an association. */
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

        /** Return the number of associations. */
        size_t size() const
        {
          size_t i(0);
          for (C* p=this->first; p; p=p->nextB) ++i;
          return i;
        }

        /** Search for the association effective at a certain date. */
        C* find(const A* b, Date d = Date::infinitePast) const
        {
          for (C* p=this->first; p; p=p->nextB)
            if (p->ptrA == b && p->effectivity.within(d)) return p;
          return NULL;
        }

        /** Search for the association with a certain name. */
        C* find(const string& n) const
        {
          for (C* p=this->first; p; p=p->nextB)
            if (p->name == n) return p;
          return NULL;
        }

        /** Move an association a position up in the list of associations. */
        void promote(C* p)
        {
          // Already at the head
          if (p == this->first) return;

          // Scan the list
          C* prev = NULL;
          for (C* ptr = this->first; ptr; ptr = ptr->nextB)
          {
            if (ptr->nextB == p)
            {
              if (prev)
                prev->nextB = p;
              else
                this->first = p;
              ptr->nextB = p->nextB;
              p->nextB = ptr;
              return;
            }
            prev = ptr;
          }
          throw LogicException("Association not found in the list");
        }
    };

    /** @brief A base class for the class representing the association
      * itself.
      */
    class Node
    {
      public:
        A* ptrA;
        B* ptrB;
        C* nextA;
        C* nextB;
        DateRange effectivity;
        string name;
        int priority;
      public:
        /** Constructor. */
        Node() : ptrA(NULL), ptrB(NULL), nextA(NULL), nextB(NULL), priority(1) {};

        /** Constructor. */
        Node(A* a, B* b, const ListA& al, const ListB& bl)
          : ptrA(a), ptrB(b), nextA(NULL), nextB(NULL), priority(1)
        {
          if (al.first)
          {
            // Append at the end of the A-list
            C* x = al.first;
            while (x->nextA) x = x->nextA;
            x->nextA = static_cast<C*>(this);
          }
          else
            // New start of the A-list
            const_cast<ListA&>(al).first = static_cast<C*>(this);
          if (bl.first)
          {
            // Append at the end of the B-list
            C* x = bl.first;
            while (x->nextB) x = x->nextB;
            x->nextB = static_cast<C*>(this);
          }
          else
            // New start of the B-list
            const_cast<ListB&>(bl).first = static_cast<C*>(this);
        }

        void setPtrA(A* a, const ListA& al)
        {
          // Don't allow updating an already valid link
          if (ptrA) throw DataException("Can't update existing entity");
          ptrA = a;
          if (al.first)
          {
            // Append at the end of the A-list
            C* x = al.first;
            while (x->nextA) x = x->nextA;
            x->nextA = static_cast<C*>(this);
          }
          else
            // New start of the A-list
            const_cast<ListA&>(al).first = static_cast<C*>(this);
        }

        void setPtrB(B* b, const ListB& bl)
        {
          // Don't allow updating an already valid link
          if (ptrB) throw DataException("Can't update existing entity");
          ptrB = b;
          if (bl.first)
          {
            // Append at the end of the B-list
            C* x = bl.first;
            while (x->nextB) x = x->nextB;
            x->nextB = static_cast<C*>(this);
          }
          else
            // New start of the B-list
            const_cast<ListB&>(bl).first = static_cast<C*>(this);
        }

        void setPtrAB(A* a, B* b, const ListA& al, const ListB& bl)
        {
          setPtrA(a, al);
          setPtrB(b, bl);
        }

        A* getPtrA() const {return ptrA;}

        B* getPtrB() const {return ptrB;}

        /** Update the start date of the effectivity range. */
        void setEffectiveStart(Date d) {effectivity.setStart(d);}

        /** Update the end date of the effectivity range. */
        void setEffectiveEnd(Date d) {effectivity.setEnd(d);}

        /** Update the effectivity range. */
        void setEffective(DateRange dr) {effectivity = dr;}

        /** Return the effectivity daterange.<br>
          * The default covers the complete time horizon.
          */
        DateRange getEffective() const {return effectivity;}

        /** Sets an optional name for the association.<br>
          * There is no garantuee of the uniqueness of this name.
          */
        void setName(const string x) {name = x;}

        /** Return the optional name of the association. */
        const string& getName() const {return name;}

        /** Update the priority. */
        void setPriority(int i) {priority = i;}

        /** Return the priority. */
        int getPriority() const {return priority;}
    };
};


#include "frepple/entity.h"


//
// LIBRARY INITIALISATION
//

/** @brief This class holds functions that used for maintenance of the library.
  *
  * Its static member function 'initialize' should be called BEFORE the
  * first use of any class in the library.
  * The member function 'finialize' will be called automatically at the
  * end of the program.
  */
class LibraryUtils
{
  public:
    static void initialize();
};

/** @brief A template class to expose iterators to Python. */
template <class ME, class ITERCLASS, class DATACLASS>
class FreppleIterator : public PythonExtension<ME>
{
  public:
    static int initialize()
    {
      // Initialize the type
      PythonType& x = PythonExtension<ME>::getType();
      x.setName(DATACLASS::metadata->type + "Iterator");
      x.setDoc("frePPLe iterator for " + DATACLASS::metadata->type);
      x.supportiter();
      return x.typeReady();
    }

    FreppleIterator() : i(DATACLASS::begin())
    {this->initType(PythonExtension<ME>::getType().type_object());}

    template <class OTHER> FreppleIterator(const OTHER *o) : i(o)
    {this->initType(PythonExtension<ME>::getType().type_object());}

    template <class OTHER> FreppleIterator(const OTHER &o) : i(o)
    {this->initType(PythonExtension<ME>::getType().type_object());}

    virtual ~FreppleIterator() {}

    static PyObject* create(PyObject* self, PyObject* args)
    {return new ME();}

  private:
    ITERCLASS i;

    virtual PyObject* iternext()
    {
      if (i == DATACLASS::end()) return NULL;
      PyObject* result = &*i;
      ++i;
      Py_INCREF(result);
      return result;
    }
};


/** @brief This Python function loads a frepple extension module in memory. */
DECLARE_EXPORT PyObject* loadModule(PyObject*, PyObject*, PyObject*);


} // end namespace
} // end namespace

#include "pythonutils.h"

#endif  // End of FREPPLE_UTILS_H
