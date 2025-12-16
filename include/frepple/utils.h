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

#pragma once
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
#define PY_SSIZE_T_CLEAN
#ifdef _MSC_VER
#define HAVE_SNPRINTF
#endif
#if defined(_DEBUG) && defined(_MSC_VER)
#include <assert.h>
#include <basetsd.h>
#include <ctype.h>
#include <errno.h>
#include <float.h>
#include <io.h>
#include <limits.h>
#include <math.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <wchar.h>
#undef _DEBUG
#include "Python.h"
#define _DEBUG
#else
#include "Python.h"
#endif
#include "datetime.h"

// A dummy function to suppress warnings about the unused variable
// PyDateTimeAPI. Some of our source files do use it, some don't.
inline bool unused_function() { return PyDateTimeAPI == nullptr; }

#include <assert.h>
#include <float.h>

#include <algorithm>
#include <condition_variable>
#include <ctime>
#include <forward_list>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <list>
#include <map>
#include <mutex>
#include <set>
#include <sstream>
#include <stack>
#include <stdexcept>
#include <string>
#include <thread>
#include <typeinfo>
#include <unordered_map>
#include <vector>
using namespace std;

#include <config.h>

// For the disabled and ansi-challenged people...
#ifndef HAVE_STRNCASECMP
#ifdef _MSC_VER
#define strncasecmp _strnicmp
#else
#ifdef HAVE_STRNICMP
#define strncasecmp(s1, s2, n) strnicmp(s1, s2, n)
#else
// Last resort. Force it through...
#define strncasecmp(s1, s2, n) strnuppercmp(s1, s2, n)
#endif
#endif
#endif

constexpr double ROUNDING_ERROR = 0.000001;

/* - DECLARE_EXPORT
 *   Used to define which symbols to export from a Windows DLL.
 * - MODULE_EXPORT
 *   Signature used for a module initialization routine. It assures the
 *   function is exported appropriately when running on Windows.
 *   A module will need to define a function with the following prototype:
 *       MODULE_EXPORT string initialize();
 */
#undef DECLARE_EXPORT
#undef MODULE_EXPORT
#if defined(WIN32)
#if defined(FREPPLE_CORE)
#define DECLARE_EXPORT __declspec(dllexport)
#elif defined(FREPPLE_STATIC)
#define DECLARE_EXPORT
#else
#define DECLARE_EXPORT __declspec(dllimport)
#endif
#define MODULE_EXPORT extern "C" __declspec(dllexport)
#ifndef MODULE_IMPORT
#define MODULE_FUNCTION __declspec(dllexport)
#else
#define MODULE_FUNCTION __declspec(dllimport)
#endif
#else
#define DECLARE_EXPORT
#define MODULE_FUNCTION
#define MODULE_EXPORT extern "C"
#endif

namespace frepple {

// Forward declarations
class CommandMoveOperationPlan;

namespace utils {

// Forward declarations
class Object;
class Serializer;
class Keyword;
class PooledString;
class DataInput;
class DataValue;
class PythonFunction;
template <class T, class U>
class PythonIterator;
template <class T>
class PythonIteratorClass;
class DataValueDict;
class MetaClass;
class CommandManager;
class DateDetail;
template <class T>
class MetaFieldDate;
template <class T>
class MetaFieldDouble;
template <class T>
class MetaFieldBool;
template <class T>
class MetaFieldDuration;
template <class T>
class MetaFieldDurationDouble;
template <class T>
class MetaFieldString;
template <class T>
class MetaFieldFunction;
template <class T>
class MetaFieldStringRef;
template <class T, class u>
class MetaFieldEnum;
template <class T, class U>
class MetaFieldPointer;
template <class T>
class MetaFieldUnsignedLong;
template <class Cls, class Iter, class PyIter, class Ptr>
class MetaFieldIterator;
template <class Cls, class Iter>
class MetaFieldIteratorClass;
template <class T>
class MetaFieldInt;
template <class T>
class MetaFieldShort;
template <class T>
class MetaFieldCommand;
template <class T>
class MemoryPage;
template <class T>
class MemoryPagePool;

// Include the list of predefined tags
#include "frepple/tags.h"

/* This type defines what operation we want to do with the entity. */
enum class Action {
  /* or A.
   * Add an new entity, and report an error if the entity already exists. */
  ADD = 0,
  /* or C.
   * Change an existing entity, and report an error if the entity doesn't
   * exist yet. */
  CHANGE = 1,
  /* or D.
   * Delete an entity, and report an error if the entity doesn't exist. */
  REMOVE = 2,
  /* or AC.
   * Change an entity or create a new one if it doesn't exist yet.
   * This is the default action.
   */
  ADD_CHANGE = 3
};

enum tribool { BOOL_UNSET, BOOL_TRUE, BOOL_FALSE };

/* Writes an action description to an output stream. */
inline ostream& operator<<(ostream& os, const Action& d) {
  switch (d) {
    case Action::ADD:
      os << "ADD";
      return os;
    case Action::CHANGE:
      os << "CHANGE";
      return os;
    case Action::REMOVE:
      os << "REMOVE";
      return os;
    case Action::ADD_CHANGE:
      os << "ADD_CHANGE";
      return os;
    default:
      assert(false);
      return os;
  }
}

/* This type defines the types of callback events possible. */
enum Signal {
  /* Adding a new entity. */
  SIG_ADD = 0,
  /* Deleting an entity. */
  SIG_REMOVE = 1
};

/* Writes a signal description to an output stream. */
inline ostream& operator<<(ostream& os, const Signal& d) {
  switch (d) {
    case SIG_ADD:
      os << "ADD";
      return os;
    case SIG_REMOVE:
      os << "REMOVE";
      return os;
    default:
      assert(false);
      return os;
  }
}

/* This stream is the general output for all logging and debugging messages. */
extern ostream logger;

class StreambufWrapper : public filebuf {
 public:
  void setLogLimit(unsigned long long);

  unsigned long long getLogLimit() const { return max_size; }

  virtual int sync();

 private:
  unsigned long long start_size = 0;
  unsigned long long cur_size = 0;
  unsigned long long max_size = 0;
};

/* Auxilary structure for easy indenting in the log stream. */
class indent {
 public:
  short level = 0;

  indent(short l) : level(l) {}

  indent() {}

  indent operator()(short l) { return indent(l); }

  operator short() const { return level; }

  indent& operator++() {
    ++level;
    return *this;
  }

  indent operator++(int) {
    auto tmp = indent(level);
    ++level;
    return tmp;
  }

  indent& operator--() {
    --level;
    return *this;
  }

  indent operator--(int) {
    auto tmp = indent(level);
    --level;
    return tmp;
  }
};

/* Print a number of spaces to the output stream. */
inline ostream& operator<<(ostream& os, const indent& i) {
  for (auto c = (i.level > 30 ? 30 : i.level); c > 0; --c) os << "  ";
  return os;
}

//
// CUSTOM EXCEPTION CLASSES
//

/* An exception of this type is thrown when data errors are found.
 *
 * The normal handling of this error is to catch the exception and
 * continue execution of the rest of the program.
 * When a DataException is thrown the object is expected to remain in
 * valid and consistent state.
 */
class DataException : public logic_error {
 public:
  DataException(const char* c) : logic_error(c) {}
  DataException(const string s) : logic_error(s) {}
};

/* An exception of this type is thrown when the library gets in an
 * inconsistent state from which the normal course of action can't continue.
 *
 * The normal handling of this error is to exit the program, and report the
 * problem. This exception indicates a bug in the program code.
 */
class LogicException : public logic_error {
 public:
  LogicException(const char* c) : logic_error(c) {}
  LogicException(const string s) : logic_error(s) {}
};

/* An exception of this type is thrown when the library runs into
 * problems that are specific at runtime.
 * These could either be memory problems, threading problems, file system
 * problems, etc...
 *
 * Errors of this type can be caught by the client applications and the
 * application can continue in most cases.
 * This exception shouldn't be used for issueing warnings. Warnings should
 * simply be logged in the logfile and actions continue in some default way.
 */
class RuntimeException : public runtime_error {
 public:
  RuntimeException(const char* c) : runtime_error(c) {}
  RuntimeException(const string s) : runtime_error(s) {}
};

/* Python exception class matching with frepple::LogicException. */
extern PyObject* PythonLogicException;

/* Python exception class matching with frepple::DataException. */
extern PyObject* PythonDataException;

/* Python exception class matching with frepple::RuntimeException. */
extern PyObject* PythonRuntimeException;

//
// UTILITY CLASS "NON-COPYABLE"
//

/* Class NonCopyable is a base class. Derive your own class from
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
 * programmers.
 * The traditional way to deal with these is to declare a private copy
 * constructor and copy assignment, and then document why this is done. But
 * deriving from NonCopyable is simpler and clearer, and doesn't require
 * additional documentation.
 */
class NonCopyable {
 protected:
  NonCopyable() {}
  ~NonCopyable() {}

  /* This copy constructor doesn't exist. */
  NonCopyable(const NonCopyable&) = delete;

  /* This assignment operator doesn't exist. */
  NonCopyable& operator=(const NonCopyable&) = delete;
};

/* This class is used to maintain the Python interpreter.
 *
 * A single interpreter is used throughout the lifetime of the
 * application.
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
 * The technical implementation is inspired by and inherited from the following
 * article: "Embedding Python in Multi-Threaded C/C++ Applications", see
 * http://www.linuxjournal.com/article/3641
 */
class PythonInterpreter {
 public:
  /* Initializes the interpreter. */
  static void initialize();

  /* Execute some python code. */
  static void execute(const char*);

  /* Execute a file with Python code. */
  static void executeFile(string);

  /* Register a new method in the main extension module.
   * Arguments:
   * - The name of the built-in function/method
   * - The function that implements it.
   * - Combination of METH_* flags, which mostly describe the args
   *   expected by the C func.
   * - The __doc__ attribute, or nullptr.
   */
  static void registerGlobalMethod(const char*, PyCFunction, int, const char*,
                                   bool = true);

  /* Register a new method in the main extension module. */
  static void registerGlobalMethod(const char*, PyCFunctionWithKeywords, int,
                                   const char*, bool = true);

  /* Add a new object in the main extension module. */
  static void registerGlobalObject(const char*, PyObject*, bool = true);

  /* Return a pointer to the main extension module. */
  static DECLARE_EXPORT PyObject* getModule() { return module; }

 private:
  /* Callback function to create the extension module. */
  static PyObject* createModule();

  /* A pointer to the frePPLe extension module. */
  static PyObject* module;

  /* Python API: Used for redirecting the Python output to the same file
   * as the application.
   */
  static PyObject* python_log(PyObject*, PyObject*);

  /* Main thread info. */
  static PyThreadState* mainThreadState;
};

//
// UTILITY CLASSES "DATE", "DATE_RANGE" AND "TIME".
//

/* This class represents a time duration with an accuracy of
 * one second.
 *
 * The duration can be both positive and negative.
 */
class Duration {
  friend ostream& operator<<(ostream&, const Duration&);

 public:
  /* Default constructor and constructor with Duration passed. */
  Duration(const long l = 0) : lval(l) {}

  /* Constructor using a double value.
   * The double is rounded to the closest integer/second.
   */
  Duration(const double d) : lval(static_cast<long>(d + 0.499)) {}

  /* Constructor from a character string.
   * See the parse() method for details on the format of the argument.
   */
  Duration(const char* s) { parse(s); }

  bool operator<(const long& b) const { return lval < b; }

  bool operator>(const long& b) const { return lval > b; }

  bool operator<=(const long& b) const { return lval <= b; }

  bool operator>=(const long& b) const { return lval >= b; }

  bool operator<(const Duration& b) const { return lval < b.lval; }

  bool operator>(const Duration& b) const { return lval > b.lval; }

  bool operator<=(const Duration& b) const { return lval <= b.lval; }

  bool operator>=(const Duration& b) const { return lval >= b.lval; }

  bool operator==(const Duration& b) const { return lval == b.lval; }

  bool operator!=(const Duration& b) const { return lval != b.lval; }

  void operator+=(const Duration& l) { lval += l.lval; }

  void operator-=(const Duration& l) { lval -= l.lval; }

  bool operator!() const { return lval == 0L; }

  void operator*=(double f) { lval = static_cast<long>(lval * f); }

  void operator*=(int i) { lval *= i; }

  operator long() const { return lval; }

  double getSeconds() const { return lval; }

  /* Converts the date to a string, formatted according to ISO 8601. */
  operator string() const {
    char str[20];
    toCharBuffer(str);
    return string(str);
  }

  /* Function that parses a input string to a time value.
   * The string format is following the ISO 8601 specification for
   * durations: [-]P[nY][nM][nW][nD][T[nH][nM][nS]]
   * Some examples to illustrate how the string is converted to a
   * Duration, expressed in seconds:
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
  void parse(const char*);

  /* Function to parse a string to a double, representing the
   * number of seconds.
   * Compared to the parse() method it also processes the
   * decimal part of the duration.
   */
  static double parse2double(const char*);

  /* Write out a double as a time period string. */
  static void double2CharBuffer(double, char*);

  /* The maximum value for a Duration. */
  static const Duration MAX;

  /* The minimum value for a Duration. */
  static const Duration MIN;

 private:
  /* The time is stored as a number of seconds. */
  long lval;

  /* This function fills a character buffer with a text representation of
   * the Duration.
   * The character buffer passed MUST have room for at least 20 characters.
   * 20 characters is sufficient for even the most longest possible time
   * duration.
   * The output format is described with the string() method.
   */
  void toCharBuffer(char*) const;
};

/* Prints a Duration to the outputstream. */
inline ostream& operator<<(ostream& os, const Duration& t) {
  char str[20];
  t.toCharBuffer(str);
  return os << str;
}

/* This class represents a date and time with an accuracy of
 * one second. */
class Date {
  friend class DateDetail;
  friend ostream& operator<<(ostream&, const Date&);

 private:
  /* This string is a format string to be used to convert a date to and
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
  static string format;

  /* The internal representation of a date is a single long value. */
  time_t lval;

  /* Checks whether we stay within the boundaries of finite Dates. */
  void checkFinite(long long i) {
    if (i < infinitePast.lval)
      lval = infinitePast.lval;
    else if (i > infiniteFuture.lval)
      lval = infiniteFuture.lval;
    else
      lval = static_cast<long>(i);
  }

  /* A private constructor used to create the infinitePast and
   * infiniteFuture constants. */
  Date(const char* s, bool dummy) { parse(s); }

 public:
  /* A utility function that uses the C function localtime to compute the
   * details of the current time: day of the week, day of the month,
   * day of the year, hour, minutes, seconds
   */
  inline void getInfo(struct tm* tm_struct) const {
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

  /* Constructor initialized with a long value. */
  Date(const time_t l) : lval(l) { checkFinite(lval); }

  /* Default constructor. */
  // This constructor can skip the check for finite dates, and
  // thus gives the best performance.
  Date() : lval(infinitePast.lval) {}

  /* Constructor initialized with a string and an optional format string. */
  Date(const char* s, const char* f = format.c_str()) {
    parse(s, f);
    checkFinite(lval);
  }

  /* Comparison between dates. */
  bool operator<(const Date& b) const { return lval < b.lval; }

  /* Comparison between dates. */
  bool operator>(const Date& b) const { return lval > b.lval; }

  /* Equality of dates. */
  bool operator==(const Date& b) const { return lval == b.lval; }

  /* Inequality of dates. */
  bool operator!=(const Date& b) const { return lval != b.lval; }

  /* Comparison between dates. */
  bool operator>=(const Date& b) const { return lval >= b.lval; }

  /* Comparison between dates. */
  bool operator<=(const Date& b) const { return lval <= b.lval; }

  /* Adds some time to this date. */
  void operator+=(const Duration& l) {
    checkFinite(static_cast<long long>(l) + lval);
  }

  /* Subtracts some time to this date. */
  void operator-=(const Duration& l) {
    checkFinite(-static_cast<long long>(l) + lval);
  }

  /* Adding a time to a date returns a new date. */
  Date operator+(const Duration& l) const {
    Date d;
    d.checkFinite(static_cast<long long>(l) + lval);
    return d;
  }

  /* Subtracting a time from a date returns a new date. */
  Date operator-(const Duration& l) const {
    Date d;
    d.checkFinite(-static_cast<long>(l) + lval);
    return d;
  }

  /* Subtracting two date values returns the time difference in a
   * Duration object. */
  Duration operator-(const Date& l) const {
    return static_cast<long>(lval - l.lval);
  }

  /* Check whether the date has been initialized. */
  bool operator!() const { return lval == infinitePast.lval; }

  /* Check whether the date has been initialized. */
  operator bool() const { return lval != infinitePast.lval; }

  /* Static function returns a date object initialized with the current
   * Date and time. */
  static Date now() { return Date(time(0)); }

  /* Converts the date to a string. The format can be controlled by the
   * setFormat() function. */
  operator string() const {
    char str[30];
    toCharBuffer(str);
    return string(str);
  }

  /* This function fills a character buffer with a text representation of
   * the date.
   * The character buffer passed is expected to have room for
   * at least 30 characters. 30 characters should be sufficient for even
   * the most funky date format.
   */
  size_t toCharBuffer(char* str) const;

  /* Return the seconds since the epoch, which is also the internal
   * representation of a date. */
  time_t getTicks() const { return lval; }

  /* Function that parses a string according to the format string. */
  void parse(const char*, const char* = format.c_str());

  /* Updates the default date format. */
  static void setFormat(const string& n) { format = n; }

  /* Retrieves the default date format. */
  static string getFormat() { return format; }

  /* A constant representing the infinite past, i.e. the earliest time which
   * we can represent.
   * This value is normally 1971-01-01T00:00:00.
   */
  static const Date infinitePast;

  /* A constant representing the infinite future, i.e. the latest time which
   * we can represent.
   * This value is currently set to 2030-12-31T00:00:00.
   */
  static const Date infiniteFuture;

  string toString(const char* fmt) const;

#ifndef HAVE_STRPTIME
 private:
  char* strptime(const char*, const char*, struct tm*);
#endif
};

/* Auxilary class that allows calculations on dates.
 *
 * This class is nothing but a wrapper around a standard "struct tm".
 * Quoting from the C standard:
 *    The mktime function converts the broken-down time, expressed as local
 * time, in the structure pointed to by timeptr into a calendar time value with
 * the same encoding as that of the values returned by the time function. The
 * original values of the tm_wday and tm_yday components of the structure are
 * ignored, and the original values of the other components are not restricted
 * to the ranges indicated above. On successful completion, the values of the
 * tm_wday and tm_yday components of the structure are set appropriately, and
 * the other components are set to represent the specified calendar time, but
 * with their values forced to the ranges indicated above; the final value of
 * tm_mday is not set until tm_mon and tm_year are determined.
 */
class DateDetail {
  friend ostream& operator<<(ostream&, const DateDetail&);

 private:
  struct tm time_info;
  time_t val;

 public:
  /* Constructor from a date. */
  inline DateDetail(const Date& d) : val(d.lval) {
// The standard library function localtime() is not re-entrant: the same
// static structure is used for all calls. In a multi-threaded environment
// the function is not to be used.
#ifdef HAVE_LOCALTIME_R
    // The POSIX standard defines a re-entrant version of the function.
    localtime_r(&(d.lval), &time_info);
#elif defined(WIN32)
    // Microsoft uses another function name with, of course, a different
    // name and a different order of arguments.
    localtime_s(&time_info, &val);
#else
#error A multi-threading safe localtime function is required
#endif
  }

  inline DateDetail(const Date* d) : val(d->lval) {
// The standard library function localtime() is not re-entrant: the same
// static structure is used for all calls. In a multi-threaded environment
// the function is not to be used.
#ifdef HAVE_LOCALTIME_R
    // The POSIX standard defines a re-entrant version of the function.
    localtime_r(&(d->lval), &time_info);
#elif defined(WIN32)
    // Microsoft uses another function name with, of course, a different
    // name and a different order of arguments.
    localtime_s(&time_info, &val);
#else
#error A multi-threading safe localtime function is required
#endif
  }

  /* Convert a DateDetail object into a Date object. */
  inline operator Date() {
    if (val < 0) normalize();
    return Date(val);
  }

  /* Constructor with year, month and day as arguments. Hours, minutes
   * and seconds can optionally be passed too. */
  inline DateDetail(int year, int month, int day, int hr = 0, int min = 0,
                    int sec = 0)
      : val(-1) {
    time_info.tm_isdst = -1;
    time_info.tm_year = year - 1900;
    time_info.tm_mon = month - 1;
    time_info.tm_mday = day;
    time_info.tm_hour = hr;
    time_info.tm_min = min;
    time_info.tm_sec = sec;
  }

  inline size_t toCharBuffer(char* str) const {
    if (val < 0) normalize();
    return strftime(str, 30, Date::format.c_str(), &time_info);
  }

  string toString(const char* fmt) const {
    if (val < 0) normalize();
    char str[30];
    strftime(str, 30, fmt, &time_info);
    return str;
  }

  /* Converts the date to a string. The format can be controlled by the
   * setFormat() function. */
  operator string() const {
    char str[30];
    toCharBuffer(str);
    return string(str);
  }

  /* After calculations the values can go out of their
   * expected ranges. This method will bring them back within
   * these limits.
   */
  void normalize() const {
    const_cast<struct tm*>(&time_info)->tm_isdst = -1;
    const_cast<DateDetail*>(this)->val =
        mktime(const_cast<struct tm*>(&time_info));
  }

  /* Return the weekday: 0 = sunday, 6 = saturday */
  int getWeekDay() const {
    if (val < 0) normalize();
    return time_info.tm_wday;
  }

  /* Return the number of seconds since the start of the month. */
  long getSecondsMonth() const {
    if (val < 0) normalize();
    return (time_info.tm_mday - 1) * 86400 + time_info.tm_sec +
           time_info.tm_min * 60 + time_info.tm_hour * 3600;
  }

  /* Return the number of seconds since january 1st. */
  long getSecondsYear() const {
    if (val < 0) normalize();
    return time_info.tm_yday * 86400 + time_info.tm_sec +
           time_info.tm_min * 60 + time_info.tm_hour * 3600;
  }

  /* Return the number of seconds since the start of the week.
   * The week is starting on Sunday.
   */
  long getSecondsWeek() const {
    if (val < 0) normalize();
    return time_info.tm_wday * 86400 + time_info.tm_sec +
           time_info.tm_min * 60 + time_info.tm_hour * 3600;
  }

  /* Return the number of seconds since the start of the day.
   * The return value is constructed in a DST-insensitive way.
   */
  long getSecondsDay() const {
    if (val < 0) normalize();
    return time_info.tm_sec + time_info.tm_min * 60 + time_info.tm_hour * 3600;
  }

  /* Go back till midnight of the current day. */
  void roundDownDay() {
    if (val < 0) normalize();
    time_info.tm_sec = 0;
    time_info.tm_min = 0;
    time_info.tm_hour = 0;
    val = -1;
  }

  /* Go back till midnight of the next day. */
  void roundUpDay() {
    if (val < 0) normalize();
    time_info.tm_sec = 0;
    time_info.tm_min = 0;
    time_info.tm_hour = 0;
    time_info.tm_mday += 1;
    val = -1;
  }

  /* Change the offset within the day.
   * The argument is interpreted in a DST-insenstive way.
   */
  void setSecondsDay(int sec) {
    if (val < 0) normalize();
    time_info.tm_hour = sec / 3600;
    time_info.tm_min = (sec - time_info.tm_hour * 3600) / 60;
    time_info.tm_sec = sec - time_info.tm_min * 60 - time_info.tm_hour * 3600;
    val = -1;
  }

  /* Add a number of days.
   * Changes in daylight saving time are ignored. */
  void addDays(int days) {
    if (val < 0) normalize();
    time_info.tm_mday += days;
    val = -1;
  }
};

inline size_t Date::toCharBuffer(char* str) const {
  return DateDetail(*this).toCharBuffer(str);
}

inline string Date::toString(const char* fmt) const {
  DateDetail tmp(this);
  return tmp.toString(fmt);
}

/* Prints a date to the outputstream. */
inline ostream& operator<<(ostream& os, const Date& d) {
  char str[30];
  d.toCharBuffer(str);
  return os << str;
}

/* Prints a datedetail to the outputstream. */
inline ostream& operator<<(ostream& os, const DateDetail& d) {
  char str[30];
  d.toCharBuffer(str);
  return os << str;
}

/* This class defines a date-range, i.e. a start-date and end-date pair.
 *
 * The behavior is such that the start date is considered as included in
 * it, but the end date is excluded from it.
 * In other words, a daterange is a halfopen date interval: [start,end[
 * The start and end dates are always such that the start date is less than
 * or equal to the end date.
 */
class DateRange {
 public:
  /* Constructor with specified start and end dates.
   * If the start date is later than the end date parameter, the
   * parameters will be swapped. */
  DateRange(const Date& st, const Date& nd) : start(st), end(nd) {
    if (st > nd) {
      start = nd;
      end = st;
    }
  }

  /* Default constructor.
   * This will create a daterange covering the complete horizon.
   */
  DateRange() : start(Date::infinitePast), end(Date::infiniteFuture) {}

  /* Copy constructor. */
  DateRange(const DateRange& n) : start(n.start), end(n.end) {}

  /* Returns the start date. */
  const Date& getStart() const { return start; }

  /* Updates the start date.
   * If the new start date is later than the end date, the end date will
   * be set equal to the new start date.
   */
  void setStart(const Date& d) {
    start = d;
    if (start > end) end = start;
  }

  /* Returns the end date. */
  const Date& getEnd() const { return end; }

  /* Updates the end date.
   * If the new end date is earlier than the start date, the start date will
   * be set equal to the new end date.
   */
  void setEnd(const Date& d) {
    end = d;
    if (start > end) start = end;
  }

  /* Updates the start and end dates simultaneously. */
  void setStartAndEnd(const Date& st, const Date& nd) {
    if (st < nd) {
      start = st;
      end = nd;
    } else {
      start = nd;
      end = st;
    }
  }

  /* Returns the duration of the interval. Note that this number will always
   * be greater than or equal to 0, since the end date is always later than
   * the start date.
   */
  Duration getDuration() const { return end - start; }

  /* Bool conversion operator.
   * Returns true if the daterange is different from the default. */
  operator bool() const {
    return start != Date::infinitePast || end != Date::infiniteFuture;
  }

  /* Equality of date ranges. */
  bool operator==(const DateRange& b) const {
    return start == b.start && end == b.end;
  }

  /* Inequality of date ranges. */
  bool operator!=(const DateRange& b) const {
    return start != b.start || end != b.end;
  }

  /* Move the daterange later in time. */
  void operator+=(const Duration& l) {
    start += l;
    end += l;
  }

  /* Move the daterange earlier in time. */
  void operator-=(const Duration& l) {
    start -= l;
    end -= l;
  }

  /* Assignment operator. */
  void operator=(const DateRange& dr) {
    start = dr.start;
    end = dr.end;
  }

  /* Comparison operator. */
  bool operator<(const DateRange& dr) const {
    if (start != dr.start)
      // Comparison based on the start date
      return start < dr.start;
    else
      // Use end date as tie breaker
      return end < dr.end;
  }

  /* Return true if two date ranges are overlapping.
   * The start point of the first interval is included in the comparison,
   * whereas the end point isn't. As a result this method is not
   * symmetrical, ie when a.intersect(b) returns true b.intersect(a) is
   * not nessarily true.
   */
  bool intersect(const DateRange& dr) const {
    return dr.start <= end && dr.end > start;
  }

  /* Returns the number of seconds the two dateranges overlap. */
  Duration overlap(const DateRange& dr) const {
    long x =
        (dr.end < end ? dr.end : end) - (dr.start > start ? dr.start : start);
    return x > 0 ? x : 0;
  }

  /* Returns true if the date passed as argument does fall within the
   * daterange. */
  bool within(const Date& d) const { return d >= start && d < end; }

  /* Same as "within", but the end date is included in the range. */
  bool between(const Date& d) const { return d >= start && d <= end; }

  bool almostEqual(const DateRange& dr) const {
    return (start == dr.start || start == dr.start - Duration(1L) ||
            start == dr.start + Duration(1L)) &&
           (end == dr.end || start == dr.end - Duration(1L) ||
            end == dr.end + Duration(1L));
  }

  /* Convert the daterange to a string. */
  operator string() const;

  /* Updates the default seperator. */
  static void setSeparator(const string& n) {
    separator = n;
    separatorlength = n.size();
  }

  /* Retrieves the default seperator. */
  static const string& getSeparator() { return separator; }

 private:
  /* Start date of the interval. */
  Date start;

  /* End dat of the interval. */
  Date end;

  /* Separator to be used when printing this string. */
  static string separator;

  /* Separator to be used when printing this string. */
  static size_t separatorlength;
};

/* Prints a date range to the outputstream. */
inline ostream& operator<<(ostream& os, const DateRange& dr) {
  return os << dr.getStart() << DateRange::getSeparator() << dr.getEnd();
}

//
// METADATA AND OBJECT FACTORY
//

/* This class defines a keyword for the frePPLe data model.
 *
 * The keywords are used to define the attribute names for the objects.
 * They are used as:
 *  - Element and attribute names in XML documents
 *  - Attribute names in the Python extension.
 *
 * Special for this class is the requirement to have a "perfect" hash
 * function, i.e. a function that returns a distinct number for each
 * defined tag. The class prints a warning message when the hash
 * function doesn't satisfy this criterion.
 */
class Keyword : public NonCopyable {
 private:
  /* A function to verify the uniquess of our hashes. */
  void check();

  static std::hash<string> hasher;

  size_t dw;
  string strName;
  string fullname;

 public:
  /* Container for maintaining a list of all tags. */
  typedef map<size_t, Keyword*> tagtable;

  /* This is the constructor.
   * The tag doesn't belong to an XML namespace. */
  explicit Keyword(const string&);

  /* This is the constructor. The tag belongs to the XML namespace passed
   * as second argument.
   * Note that we still require the first argument to be unique, since it
   * is used as a keyword for the Python extensions.
   */
  explicit Keyword(const string&, const string&);

  /* Destructor. */
  ~Keyword();

  /* Returns the hash value of the tag. */
  size_t getHash() const { return dw; }

  const string& getName() const { return strName; }

  const string& getFullName() const { return fullname; }

  static size_t hash(const string& c) { return hasher(c); }

  static size_t hash(const char* c) { return hasher(c); }

  /* Finds a tag when passed a certain string. If no tag exists yet, it
   * will be created. */
  static const Keyword& find(const char*);

  /* Return a reference to a table with all defined tags. */
  static tagtable& getTags();

  /* Prints a list of all tags that have been defined. This can be useful
   * for debugging and also for creating a good hashing function.
   * GNU gperf is a program that can generate a perfect hash function for
   * a given set of symbols.
   */
  static void printTags();

  /* Equality operator. */
  bool operator==(const Keyword& k) const { return dw == k.dw; }

  /* Inequality operator. */
  bool operator!=(const Keyword& k) const { return dw != k.dw; }
};

/* This abstract class is the base class used for callbacks. */
class Functor : public NonCopyable {
 public:
  /* This is the callback method.
   * The return value should be true in case the action is allowed to
   * happen. In case a subscriber disapproves the action false is
   * returned.
   */
  virtual bool callback(Object* v, const Signal a) const = 0;

  /* Destructor. */
  virtual ~Functor() {}
};

// The following handler functions redirect the call from Python onto a
// matching virtual function in a Ojbect subclass.
extern "C" {
/* Handler function called from Python. Internal use only. */
PyObject* getattro_handler(PyObject*, PyObject*);

/* Handler function called from Python. Internal use only. */
int setattro_handler(PyObject*, PyObject*, PyObject*);

/* Handler function called from Python. Internal use only. */
PyObject* compare_handler(PyObject*, PyObject*, int);

/* Handler function called from Python. Internal use only. */
PyObject* iternext_handler(PyObject*);

/* Handler function called from Python. Internal use only. */
PyObject* call_handler(PyObject*, PyObject*, PyObject*);

/* Handler function called from Python. Internal use only. */
PyObject* str_handler(PyObject*);
}

/* This class is a thin wrapper around the type information in Python.
 *
 * This class defines a number of convenience functions to interact with the
 * PyTypeObject struct of the Python C API.
 */
class PythonType : public NonCopyable {
 private:
  /* This static variable is a template for cloning type definitions.
   * It is copied for each type object we create.
   */
  static const PyTypeObject PyTypeObjectTemplate;

  /* Incremental size of the method table.
   * We allocate memory for the method definitions per block, not
   * one-by-one.
   */
  static const unsigned short methodArraySize = 5;

  /* The Python type object which this class is wrapping. */
  PyTypeObject table;

 public:
  /* A static function that evaluates an exception and sets the Python
   * error string properly.
   * This function should only be called from within a catch-block, since
   * internally it rethrows the exception!
   */
  static void evalException();

  /* Constructor, sets the tp_base_size member. */
  PythonType(size_t, const type_info*);

  /* Return a pointer to the actual Python PyTypeObject. */
  inline PyTypeObject* type_object() const {
    return &const_cast<PythonType*>(this)->table;
  }

  /* Add a new method. */
  void addMethod(const char*, PyCFunction, int, const char*);

  /* Add a new method. */
  void addMethod(const char*, PyCFunctionWithKeywords, int, const char*);

  /* Updates tp_name. */
  void setName(const string& n) {
    string* name = new string("frepple." + n);
    table.tp_name = const_cast<char*>(name->c_str());
  }

  /* Updates tp_doc. */
  void setDoc(const string& n) {
    string* doc = new string(n);
    table.tp_doc = const_cast<char*>(doc->c_str());
  }

  /* Updates tp_base. */
  void setBase(PyTypeObject* b) { table.tp_base = b; }

  /* Updates the deallocator. */
  void supportdealloc(void (*f)(PyObject*)) { table.tp_dealloc = f; }

  /* Updates tp_getattro.
   * The extension class will need to define a member function with this
   * prototype:
   *   PythonData getattro(const XMLData& name)
   */
  void supportgetattro() { table.tp_getattro = getattro_handler; }

  /* Updates tp_setattro.
   * The extension class will need to define a member function with this
   * prototype:
   *   int setattro(const Attribute& attr, const PythonData& field)
   */
  void supportsetattro() { table.tp_setattro = setattro_handler; }

  /* Updates tp_richcompare.
   * The extension class will need to define a member function with this
   * prototype:
   *   int compare(const PyObject* other) const
   */
  void supportcompare() { table.tp_richcompare = compare_handler; }

  /* Updates tp_iter and tp_iternext.
   * The extension class will need to define a member function with this
   * prototype:
   *   PyObject* iternext()
   */
  void supportiter() {
    table.tp_iter = PyObject_SelfIter;
    table.tp_iternext = iternext_handler;
  }

  /* Updates tp_call.
   * The extension class will need to define a member function with this
   * prototype:
   *   PyObject* call(const PythonData& args, const PythonData& kwds)
   */
  void supportcall() { table.tp_call = call_handler; }

  /* Updates tp_str.
   * The extension class will need to define a member function with this
   * prototype:
   *   PyObject* str()
   */
  void supportstr() { table.tp_str = str_handler; }

  /* Type definition for create functions. */
  typedef PyObject* (*createfunc)(PyTypeObject*, PyObject*, PyObject*);

  /* Updates tp_new with the function passed as argument. */
  void supportcreate(createfunc c) { table.tp_new = c; }

  /* This method needs to be called after the type information has all
   * been updated. It adds the type to the frepple module. */
  int typeReady();

  /* Comparison operator. */
  bool operator==(const PythonType& i) const {
    return *cppClass == *(i.cppClass);
  }

  /* Comparison operator. */
  bool operator==(const type_info& i) const { return *cppClass == i; }

  /* Type info of the registering class. */
  const type_info* cppClass;
};

enum FieldCategory {
  MANDATORY = 1,       // Marks a key field of the object. This is
                       // used when we need to serialize only a reference
                       // to the object.
  BASE = 2,            // The default value. The field will be serialized
                       // and deserialized normally.
  PLAN = 4,            // Marks fields containing planning output. It is
                       // only serialized when we request such info.
  DETAIL = 8,          // Marks fields containing more detail than is
                       // required to restore all state.
  COMPUTED = 16,       // A computed field doesn't consume any storage
  PARENT = 32,         // If set, the constructor of the child object
                       // will get a pointer to the parent as extra
                       // argument.
  FORCE_BASE = 64,     // Force writing this object in base mode, even when
                       // the output is currently set in a different mode
  WRITE_HIDDEN = 128,  // Force writing hidden fields

  // Flags for default output mode
  WRITE_OBJECT_DFT =
      256,  // Force writing this field as an object when not in service mode
  WRITE_REFERENCE_DFT =
      512,  // Force writing this field as a reference when not in service mode
  DONT_SERIALIZE_DFT = 1024,  // Don't write this field when not in service mode

  // Flags for service output mode
  WRITE_OBJECT_SVC =
      2048,  // Force writing an object when we are in service mode
  WRITE_REFERENCE_SVC =
      4096,  // Force writing a reference when we are in service mode
  DONT_SERIALIZE_SVC = 8192,  // Don't write this field when in service mode

  // Combining flags
  WRITE_OBJECT = 2048 + 256,     // Force writing an object
  WRITE_REFERENCE = 4096 + 512,  // Force writing a reference
  DONT_SERIALIZE = 8192 + 1024   // Never write this field
};

/* This class stores metadata on a data field of a class. */
class MetaFieldBase {
 public:
  MetaFieldBase(const Keyword& k, unsigned int fl) : name(k), flags(fl) {}

  const Keyword& getName() const { return name; }

  /* Function to update a field given a data value. */
  virtual void setField(Object*, const DataValue&,
                        CommandManager* = nullptr) const = 0;

  /* Function to retrieve a field value. */
  virtual void getField(Object*, DataValue&) const = 0;

  /* Function to serialize a field value. */
  virtual void writeField(Serializer&) const = 0;

  /* Return the extra size used by this object.
   * Only the size that is additional to the class instance size needs
   * to be reported here.
   */
  virtual size_t getSize(const Object* o) const { return 0; }

  bool getFlag(unsigned int i) const { return (flags & i) != 0; }

  size_t getHash() const { return name.getHash(); }

  virtual bool isPointer() const { return false; }

  virtual bool isGroup() const { return false; }

  virtual const MetaClass* getClass() const { return nullptr; }

  virtual const Keyword* getKeyword() const { return nullptr; }

  typedef void (*HandlerFunction)(Object*, const DataValueDict&,
                                  CommandManager*);

  virtual HandlerFunction getFunction() const { return nullptr; }

 private:
  /* Field name. */
  const Keyword& name;

  /* A series of bit flags for specific behavior. */
  unsigned int flags;
};

class MetaCategory;
/* This class stores metadata about the classes in the library.
 * The stored information goes well beyond the standard 'type_info'.
 *
 * A MetaClass instance represents metadata for a specific instance type.
 * A MetaCategory instance represents metadata for a category of object.
 * For instance, 'Resource' is a category while 'ResourceDefault' and
 * 'ResourceInfinite' are specific classes.
 * The metadata class also maintains subscriptions to certain events.
 * Registered classes and objects will receive callbacks when objects are
 * being created, changed or deleted.
 * The proper usage is to include the following code snippet in every
 * class:
 *
 *  In the header file:
 *    class X : public Object
 *    {
 *      public:
 *        virtual const MetaClass& getType() {return *metadata;}
 *        static const MetaClass *metadata;
 *    }
 *  In the implementation file:
 *    const MetaClass *X::metadata;
 *
 * Creating a MetaClass object isn't sufficient. It needs to be registered,
 * typically in an initialization method:
 *
 *    void initialize()
 *    {
 *      ...
 *      Y::metadata = MetaCategory::registerCategory<CLS>("Y","Ys",
 * reader_method); X::metadata = MetaClass::registerClass<CLS>("Y","X",
 * factory_method);
 *      ...
 *    }
 */
class MetaClass : public NonCopyable {
  friend class MetaCategory;
  template <class T, class U>
  friend class FunctorStatic;
  template <class T, class U>
  friend class FunctorInstance;

 public:
  /* Type definition for a factory method that calls the
   * default constructor. */
  typedef Object* (*creatorDefault)();

  /* A string specifying the object type, i.e. the subclass within
   * the category. */
  string type;

  /* The size of an instance of this class. */
  size_t size = 0;

  /* A reference to a keyword of the base string. */
  const Keyword* typetag;

  /* The category of this class. */
  const MetaCategory* category = nullptr;

  /* A pointer to the Python type. */
  PyTypeObject* pythonClass = nullptr;

  /* A pointer to the Python type. */
  PyTypeObject* pythonBaseClass = nullptr;

  /* A factory method for the registered class. */
  creatorDefault factoryMethod = nullptr;

  /* A flag that tracks whether this object can inherit context from
   * its parent during creation.
   */
  bool parent = false;

  /* A flag whether this is the default class in its category. */
  bool isDefault = true;

  /* Destructor. */
  virtual ~MetaClass() {}

  void setPythonClass(PythonType& t) const {
    const_cast<MetaClass*>(this)->pythonClass = t.type_object();
    const_cast<MetaClass*>(this)->pythonBaseClass = pythonClass;
  }

  /* Initialize the data structure and register the class. */
  void addClass(const string&, const string&, bool = false,
                creatorDefault = nullptr);

  /* This constructor registers the metadata of a class. */
  template <class T>
  static inline MetaClass* registerClass(const string& cat, const string& cls,
                                         bool def = false) {
    return new MetaClass(cat, cls, sizeof(T), def);
  }

  /* This constructor registers the metadata of a class that is intended
   * only for internal use. */
  template <class T>
  static inline MetaClass* registerClass(const string& cls, creatorDefault f) {
    return new MetaClass(cls, sizeof(T), f);
  }

  /* This constructor registers the metadata of a class, with a factory
   * method that uses the default constructor of the class. */
  template <class T>
  static inline MetaClass* registerClass(const string& cat, const string& cls,
                                         creatorDefault f, bool def = false) {
    return new MetaClass(cat, cls, sizeof(T), f, def);
  }

  /* This function will analyze the string being passed, and return the
   * appropriate action.
   * The string is expected to be one of the following:
   *  - 'A' for action ADD
   *  - 'C' for action CHANGE
   *  - 'AC' for action ADD_CHANGE
   *  - 'R' for action REMOVE
   *  - Any other value will result in a data exception
   */
  static Action decodeAction(const char*);

  /* This method picks up the attribute named "ACTION" from the list and
   * calls the method decodeAction(const XML_Char*) to analyze it.
   */
  static Action decodeAction(const DataValueDict&);

  /* Sort two metaclass objects. This is used to sort entities on their
   * type information in a stable and platform independent way.
   */
  bool operator<(const MetaClass& b) const {
    return typetag->getName() < b.typetag->getName();
  }

  /* Compare two metaclass objects. We are not always sure that only a
   * single instance of a metadata object exists in the system, and a
   * pointer comparison is therefore not appropriate.
   */
  bool operator==(const MetaClass& b) const {
    return typetag->getHash() == b.typetag->getHash();
  }

  /* Compare two metaclass objects. We are not always sure that only a
   * single instance of a metadata object exists in the system, and a
   * pointer comparison is therefore not appropriate.
   */
  bool operator!=(const MetaClass& b) const {
    return typetag->getHash() != b.typetag->getHash();
  }

  /* This method should be called whenever objects of this class are being
   * created, updated or deleted. It will run the callback method of all
   * subscribers.
   * If the function returns true, all callback methods approved of the
   * event. If false is returned, one of the callbacks disapproved it and
   * the event action should be allowed to execute.
   */
  bool raiseEvent(Object* v, Signal a) const;

  /* Connect a new subscriber to the class. */
  void connect(Functor* c, Signal a) const {
    const_cast<MetaClass*>(this)->subscribers[a].push_front(c);
  }

  /* Disconnect a subscriber from the class. */
  void disconnect(Functor* c, Signal a) const {
    const_cast<MetaClass*>(this)->subscribers[a].remove(c);
  }

  /* Print all registered factory methods to the standard output for
   * debugging purposes. */
  static void printClasses();

  /* Find a particular class by its name. If it can't be located the return
   * value is nullptr. */
  static const MetaClass* findClass(const char*);

  static const MetaClass* findClass(PyObject*);

  /* Default constructor. */
  MetaClass() : type("unspecified"), typetag(&Keyword::find("unspecified")) {}

  /* Register a field. */
  template <class Cls>
  inline void addStringField(const Keyword& k,
                             string (Cls::*getfunc)(void) const,
                             void (Cls::*setfunc)(const string&) = nullptr,
                             string dflt = "", unsigned int c = BASE) {
    fields.push_back(new MetaFieldString<Cls>(k, getfunc, setfunc, dflt, c));
  }

  template <class Cls>
  inline void addStringRefField(const Keyword& k,
                                const string& (Cls::*getfunc)(void) const,
                                void (Cls::*setfunc)(const string&) = nullptr,
                                string dflt = "", unsigned int c = BASE) {
    fields.push_back(new MetaFieldStringRef<Cls>(k, getfunc, setfunc, dflt, c));
  }

  template <class Cls>
  inline void addIntField(const Keyword& k, int (Cls::*getfunc)(void) const,
                          void (Cls::*setfunc)(int) = nullptr, int d = 0,
                          unsigned int c = BASE) {
    fields.push_back(new MetaFieldInt<Cls>(k, getfunc, setfunc, d, c));
  }

  template <class Cls, class Enum>
  inline void addEnumField(const Keyword& k, Enum (Cls::*getfunc)(void) const,
                           void (Cls::*setfunc)(string), Enum d,
                           unsigned int c = BASE) {
    fields.push_back(new MetaFieldEnum<Cls, Enum>(k, getfunc, setfunc, d, c));
  }

  template <class Cls>
  inline void addShortField(const Keyword& k, short (Cls::*getfunc)(void) const,
                            void (Cls::*setfunc)(short) = nullptr, int d = 0,
                            unsigned int c = BASE) {
    fields.push_back(new MetaFieldShort<Cls>(k, getfunc, setfunc, d, c));
  }

  template <class Cls>
  inline void addUnsignedLongField(
      const Keyword& k, unsigned long (Cls::*getfunc)(void) const,
      void (Cls::*setfunc)(unsigned long) = nullptr, unsigned long d = 0.0,
      unsigned int c = BASE) {
    fields.push_back(new MetaFieldUnsignedLong<Cls>(k, getfunc, setfunc, d, c));
  }

  template <class Cls>
  inline void addDoubleField(const Keyword& k,
                             double (Cls::*getfunc)(void) const,
                             void (Cls::*setfunc)(double) = nullptr,
                             double d = 0.0, unsigned int c = BASE,
                             bool (Cls::*isdfltfunc)(void) const = nullptr) {
    fields.push_back(
        new MetaFieldDouble<Cls>(k, getfunc, setfunc, d, c, isdfltfunc));
  }

  template <class Cls, class Ptr>
  inline void addPointerField(const Keyword& k,
                              Ptr* (Cls::*getfunc)(void) const,
                              void (Cls::*setfunc)(Ptr*) = nullptr,
                              unsigned int c = BASE) {
    fields.push_back(new MetaFieldPointer<Cls, Ptr>(k, getfunc, setfunc, c));
    if (c & PARENT) parent = true;
  }

  template <class Cls>
  inline void addFunctionField(const Keyword& k,
                               MetaFieldBase::HandlerFunction f,
                               unsigned int c = DONT_SERIALIZE) {
    fields.push_back(new MetaFieldFunction<Cls>(k, f, c));
  }

  template <class Cls, class Iter, class Ptr>
  inline void addIteratorField(const Keyword& k1, const Keyword& k2,
                               Iter (Cls::*getfunc)(void) const = nullptr,
                               unsigned int c = BASE) {
    PythonIterator<Iter, Ptr>::initialize();
    fields.push_back(
        new MetaFieldIterator<Cls, Iter, PythonIterator<Iter, Ptr>, Ptr>(
            k1, k2, getfunc, c));
    if (c & PARENT) parent = true;
  }

  template <class Cls, class Iter, class Ptr>
  inline void addIteratorField(const Keyword& k1, const Keyword& k2, string nm,
                               string doc,
                               Iter (Cls::*getfunc)(void) const = nullptr,
                               unsigned int c = BASE) {
    PythonIterator<Iter, Ptr>::initialize(nm, doc);
    fields.push_back(
        new MetaFieldIterator<Cls, Iter, PythonIterator<Iter, Ptr>, Ptr>(
            k1, k2, getfunc, c));
    if (c & PARENT) parent = true;
  }

  template <class Cls, class Iter>
  inline void addIteratorClassField(const Keyword& k1, const Keyword& k2,
                                    Iter (Cls::*getfunc)(void) const = nullptr,
                                    unsigned int c = BASE) {
    fields.push_back(new MetaFieldIteratorClass<Cls, Iter>(k1, k2, getfunc, c));
    if (c & PARENT) parent = true;
  }

  template <class Cls>
  inline void addCommandField(const Keyword& k,
                              void (Cls::*cmdfunc)(const string&) = nullptr) {
    fields.push_back(new MetaFieldCommand<Cls>(k, cmdfunc));
  }

  template <class Cls>
  inline void addBoolField(const Keyword& k, bool (Cls::*getfunc)(void) const,
                           void (Cls::*setfunc)(bool) = nullptr,
                           tribool d = BOOL_UNSET, unsigned int c = BASE) {
    fields.push_back(new MetaFieldBool<Cls>(k, getfunc, setfunc, d, c));
  }

  template <class Cls>
  inline void addDateField(const Keyword& k, Date (Cls::*getfunc)(void) const,
                           void (Cls::*setfunc)(Date) = nullptr,
                           Date d = Date::infinitePast, unsigned int c = BASE) {
    fields.push_back(new MetaFieldDate<Cls>(k, getfunc, setfunc, d, c));
  }

  template <class Cls>
  inline void addDurationField(const Keyword& k,
                               Duration (Cls::*getfunc)(void) const,
                               void (Cls::*setfunc)(Duration), Duration d = 0L,
                               unsigned int c = BASE) {
    fields.push_back(new MetaFieldDuration<Cls>(k, getfunc, setfunc, d, c));
  }

  template <class Cls>
  inline void addDurationDoubleField(const Keyword& k,
                                     double (Cls::*getfunc)(void) const,
                                     void (Cls::*setfunc)(double),
                                     double d = 0L, unsigned int c = BASE) {
    fields.push_back(
        new MetaFieldDurationDouble<Cls>(k, getfunc, setfunc, d, c));
  }

  /* Search a field. */
  const MetaFieldBase* findField(const Keyword&) const;

  /* Search a field. */
  const MetaFieldBase* findField(size_t) const;

  typedef vector<MetaFieldBase*> fieldlist;

  /* Return a reference to a list of fields. */
  const fieldlist& getFields() const { return fields; }

 private:
  /* This constructor registers the metadata of a class. */
  MetaClass(const string& cls, size_t sz, creatorDefault f)
      : type(cls), size(sz), factoryMethod(f) {
    factoryMethod = f;
    typetag = &Keyword::find(cls.c_str());
  }

  /* This constructor registers the metadata of a class. */
  MetaClass(const string& cat, const string& cls, size_t sz, bool def = false)
      : size(sz), isDefault(def) {
    addClass(cat, cls, def);
  }

  /* This constructor registers the metadata of a class, with a factory
   * method that uses the default constructor of the class. */
  MetaClass(const string& cat, const string& cls, size_t sz, creatorDefault f,
            bool def = false)
      : size(sz), isDefault(def) {
    addClass(cat, cls, def);
    factoryMethod = f;
  }

  /* This is a list of objects that will receive a callback when the call
   * method is being used.
   * There is limited error checking in maintaining this list, and it is the
   * user's responsability of calling the connect() and disconnect() methods
   * correctly.
   * This design garantuees maximum performance, but assumes a properly
   * educated user.
   */
  list<Functor*> subscribers[4];

  /* Registry of all fields of the model. */
  fieldlist fields;
};

/* A MetaCategory instance represents metadata for a category of
 * object.
 *
 * A MetaClass instance represents metadata for a specific instance type.
 * For instance, 'Resource' is a category while 'ResourceDefault' and
 * 'ResourceInfinite' are specific classes.
 * A category has the following specific pieces of data:
 *  - A reader function for creating objects.
 *    The reader function creates objects for all classes registered with it.
 *  - A group tag used for the grouping objects of the category in the XML
 *    output stream.
 */
class MetaCategory : public MetaClass {
  friend class MetaClass;
  template <class T>
  friend class HasName;

 public:
  /* The name used to name a collection of objects of this category. */
  string group;

  /* A XML tag grouping objects of the category. */
  const Keyword* grouptag;

  /* Type definition for the find control function. */
  typedef Object* (*findController)(const DataValueDict&);

  /* Type definition for the read control function. */
  typedef Object* (*readController)(const MetaClass*, const DataValueDict&,
                                    CommandManager*);

  /* This template method is available as a object creation factory for
   * classes without key fields and which rely on a default constructor.
   */
  static Object* ControllerDefault(const MetaClass*, const DataValueDict&,
                                   CommandManager* = nullptr);

  /* Destructor. */
  virtual ~MetaCategory() {}

  /* Template constructor. */
  template <class cls>
  static inline MetaCategory* registerCategory(const string& t, const string& g,
                                               readController r = nullptr,
                                               findController f = nullptr) {
    return new MetaCategory(t, g, sizeof(cls), r, f);
  }

  /* Type definition for the map of all registered classes. */
  typedef map<size_t, const MetaClass*, less<size_t>> ClassMap;

  /* Type definition for the map of all categories. */
  typedef map<size_t, const MetaCategory*, less<size_t>> CategoryMap;

  /* Looks up a category name in the registry. If the category can't be
   * located the return value is nullptr. */
  static const MetaCategory* findCategoryByTag(const char*);

  /* Looks up a category name in the registry. If the category can't be
   * located the return value is nullptr. */
  static const MetaCategory* findCategoryByTag(const size_t);

  /* Looks up a category name in the registry. If the category can't be
   * located the return value is nullptr. */
  static const MetaCategory* findCategoryByGroupTag(const char*);

  /* Looks up a category name in the registry. If the category can't be
   * located the return value is nullptr. */
  static const MetaCategory* findCategoryByGroupTag(const size_t);

  void setDefaultClass(const MetaClass* i) {
    classes[Keyword::hash("default")] = i;
  }

  /* Find a class in this category with a specified name.
   * If the catrgory can't be found the return value is nullptr.
   */
  const MetaClass* findClass(const char*) const;

  /* Find a class in this category with a specified name.
   * If the catrgory can't be found the return value is nullptr.
   */
  const MetaClass* findClass(const size_t) const;

  /* Find an object given a dictionary of values. */
  Object* find(const DataValueDict& key) const {
    return findFunction ? findFunction(key) : nullptr;
  }

  /* A control function for reading objects of a category.
   * The controller function manages the creation and destruction of
   * objects in this category.
   */
  readController readFunction;

  /* Compute the hash for "default" once and store it in this variable for
   * efficiency. */
  static const size_t defaultHash;

 private:
  /* Private constructor, called by registerCategory. */
  MetaCategory(const string&, const string&, size_t, readController,
               findController);

  /* A map of all classes registered for this category. */
  ClassMap classes;

  /* This is the root for a linked list of all categories.
   * Categories are chained to the list in the order of their registration.
   */
  static const MetaCategory* firstCategory;

  /* A pointer to the next category in the singly linked list. */
  const MetaCategory* nextCategory;

  /* A control function to find an object given its primary key. */
  findController findFunction;

  /* A map of all categories by their name. */
  static CategoryMap categoriesByTag;

  /* A map of all categories by their group name. */
  static CategoryMap categoriesByGroupTag;
};

/* This class represents a static subscription to a signal.
 *
 * When the signal callback is triggered the static method callback() on the
 * parameter class will be called.
 */
template <class T, class U>
class FunctorStatic : public Functor {
  friend class MetaClass;

 public:
  /* Add a signal subscriber. */
  static void connect(const Signal a) {
    T::metadata->connect(new FunctorStatic<T, U>(), a);
  }

  /* Remove a signal subscriber. */
  static void disconnect(const Signal a) {
    MetaClass& t =
        const_cast<MetaClass&>(static_cast<const MetaClass&>(*T::metadata));
    // Loop through all subscriptions
    for (auto i = t.subscribers[a].begin(); i != t.subscribers[a].end(); ++i) {
      // Try casting the functor to the right type
      FunctorStatic<T, U>* f = dynamic_cast<FunctorStatic<T, U>*>(*i);
      if (f) {
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
  /* This is the callback method. The functor will call the static callback
   * method of the subscribing class.
   */
  virtual bool callback(Object* v, const Signal a) const {
    return U::callback(static_cast<T*>(v), a);
  }
};

/* This class represents an object subscribing to a signal.
 *
 * When the signal callback is triggered the method callback() on the
 * instance object will be called.
 */
template <class T, class U>
class FunctorInstance : public Functor {
 public:
  /* Connect a new subscriber to a signal.
   * It is the users' responsibility to call the disconnect method
   * when the subscriber is being deleted. Otherwise the application
   * will crash.
   */
  static void connect(U* u, const Signal a) {
    if (u) T::metadata.connect(new FunctorInstance(u), a);
  }

  /* Disconnect from a signal. */
  static void disconnect(U* u, const Signal a) {
    MetaClass& t =
        const_cast<MetaClass&>(static_cast<const MetaClass&>(T::metadata));
    // Loop through all subscriptions
    for (auto i = t.subscribers[a].begin(); i != t.subscribers[a].end(); ++i) {
      // Try casting the functor to the right type
      FunctorInstance<T, U>* f = dynamic_cast<FunctorInstance<T, U>*>(*i);
      if (f && f->instance == u) {
        // Casting was successfull. Delete the functor.
        delete *i;
        t.subscribers[a].erase(i);
        return;
      }
    }
    // Not found in the list of subscriptions
    throw LogicException("Subscription doesn't exist");
  }

  /* Constructor. */
  FunctorInstance(U* u) : instance(u) {}

 private:
  /* This is the callback method. */
  virtual bool callback(Object* v, const Signal a) const {
    return instance ? instance->callback(static_cast<T*>(v), a) : true;
  }

  /* The object whose callback method will be called. */
  U* instance;
};

//
// UTILITY CLASSES FOR INPUT AND OUTPUT
//

/* Abstract base class for writing serialized data to an output stream.
 *
 * Subclasses implement writing different formats and stream types.
 */
class Serializer {
 protected:
  /* Updating the output stream. */
  void setOutput(ostream& o) { m_fp = &o; }

 public:
  /* Returns which type of export is requested. */
  FieldCategory getContentType() const { return forceBase ? BASE : content; }

  /* Specify the type of export. */
  void setContentType(FieldCategory c) { content = c; }

  /* Set the content type, by parsing its text description. */
  void setContentType(const string&);

  /* Constructor with a given stream. */
  Serializer(ostream& os) { m_fp = &os; }

  /* Default constructor. */
  Serializer() { m_fp = &logger; }

  /* Update the flag to write references or not.
   * The value of the flag before the call is returned. This is useful
   * to restore the previous state later on.
   */
  bool setSaveReferences(bool b) {
    bool tmp = writeReference;
    writeReference = b;
    return tmp;
  }

  /* Returns whether we write only references for nested objects or not. */
  inline bool getSaveReferences() const { return writeReference; }

  inline bool getWriteHidden() const { return writeHidden; }

  inline bool getFlattenProperties() const { return flatten_properties; }

  /* Update the flag to write hidden objects or not.
   * The value of the flag before the call is returned. This is useful
   * to restore the previous state later on.
   */
  bool setWriteHidden(bool b) {
    bool tmp = writeHidden;
    writeHidden = b;
    return tmp;
  }

  inline bool getForceBase() const { return forceBase; }

  inline bool setForceBase(bool b = true) {
    bool tmp = forceBase;
    forceBase = b;
    return tmp;
  }

  /* Start writing a new list. */
  virtual void BeginList(const Keyword&) = 0;

  /* Write the closing tag of a list. */
  virtual void EndList(const Keyword& t) = 0;

  /* Start writing a new object. */
  virtual void BeginObject(const Keyword&) = 0;

  /* Write the closing tag of this object. */
  virtual void EndObject(const Keyword& t) = 0;

  /* Start writing a new object. */
  virtual void BeginObject(const Keyword&, const string&) = 0;
  virtual void BeginObject(const Keyword&, const Keyword&, const int) = 0;
  virtual void BeginObject(const Keyword&, const Keyword&, const Date) = 0;
  virtual void BeginObject(const Keyword&, const Keyword&, const string&) = 0;
  virtual void BeginObject(const Keyword&, const Keyword&, const string&,
                           const Keyword&, const string&) = 0;
  virtual void BeginObject(const Keyword&, const Keyword&, const unsigned long&,
                           const Keyword&, const string&) = 0;
  virtual void BeginObject(const Keyword&, const Keyword&, const int&,
                           const Keyword&, const Date, const Keyword&,
                           const Date) = 0;

  /* Write the string to the output. No tags are added, so this method
   * is used for passing text straight into the output file. */
  virtual void writeString(const string& c) = 0;

  /* Write an unsigned long value enclosed opening and closing tags.  */
  virtual void writeElement(const Keyword& t, const long unsigned int val) = 0;

  /* Write an integer value enclosed opening and closing tags. */
  virtual void writeElement(const Keyword& t, const int val) = 0;

  /* Write a double value enclosed opening and closing tags. */
  virtual void writeElement(const Keyword& t, const double val) = 0;

  virtual void writeElement(const Keyword& t, const PooledString& p,
                            const double val) = 0;

  virtual void writeElement(const string&, const string&) {
    throw LogicException("Not implemented");
  }

  /* Write a boolean value enclosed opening and closing tags. The boolean
   * is written out as the string 'true' or 'false'.
   */
  virtual void writeElement(const Keyword& t, const bool val) = 0;

  /* Write a string value enclosed opening and closing tags. Special
   * characters are appropriately escaped. */
  virtual void writeElement(const Keyword& t, const string& val) = 0;

  /* Writes an element with a string attribute. */
  virtual void writeElement(const Keyword& u, const Keyword& t,
                            const string& val) = 0;

  /* Writes an element with a long attribute. */
  virtual void writeElement(const Keyword& u, const Keyword& t,
                            const long val) = 0;

  /* Writes an element with a date attribute. */
  virtual void writeElement(const Keyword& u, const Keyword& t,
                            const Date& val) = 0;

  /* Writes an element with 2 string attributes. */
  virtual void writeElement(const Keyword& u, const Keyword& t1,
                            const string& val1, const Keyword& t2,
                            const string& val2) = 0;

  /* Writes an element with a string and an unsigned long attribute. */
  virtual void writeElement(const Keyword& u, const Keyword& t1,
                            unsigned long val1, const Keyword& t2,
                            const string& val2) = 0;

  /* Writes an element with a short, an unsigned long and a double attribute.
   */
  virtual void writeElement(const Keyword& u, const Keyword& t1, short val1,
                            const Keyword& t2, unsigned long val2,
                            const Keyword& t3, double val3) = 0;

  /* Writes a C-type character string. */
  virtual void writeElement(const Keyword& t, const char* val) = 0;

  /* Writes an Duration element. /> */
  virtual void writeElement(const Keyword& t, const Duration d) = 0;

  /* Writes an date element. */
  virtual void writeElement(const Keyword& t, const Date d) = 0;

  /* Writes an daterange element. */
  virtual void writeElement(const Keyword& t, const DateRange& d) = 0;

  /* This method writes a serializable object.
   * If an object is nested more than 2 levels deep only a reference
   * to it is written, rather than the complete object.
   * You should call this method for all objects in your XML document,
   * except for the root object.
   */
  virtual void writeElement(const Keyword&, const Object*,
                            FieldCategory = BASE);

  void writeElement(const Keyword& t, const Object& o) {
    writeElement(t, &o, forceBase ? BASE : content);
  }

  void writeElement(const Keyword& t, const Object& o, FieldCategory m) {
    writeElement(t, &o, m);
  }

  /* Returns a pointer to the object that is currently being saved. */
  Object* getCurrentObject() const {
    return const_cast<Object*>(currentObject);
  }

  Object* pushCurrentObject(Object* o) {
    Object* t = const_cast<Object*>(currentObject);
    currentObject = o;
    return t;
  }

  /* Returns a pointer to the parent of the object that is being saved. */
  Object* getPreviousObject() const {
    return const_cast<Object*>(parentObject);
  }

  /* Returns the number of objects that have been serialized. */
  unsigned long countObjects() const { return numObjects; }

  inline void skipHead(bool b = true) { skipHeader = b; }

  inline void skipTail(bool b = true) { skipFooter = b; }

  inline void setServiceMode(bool b = true) { service_mode = b; }

  inline bool getSkipHead() const { return skipHeader; }

  inline bool getSkipTail() const { return skipFooter; }

  inline bool getServiceMode() const { return service_mode; }

 protected:
  /* Output stream. */
  ostream* m_fp;

  /* Keep track of the number of objects being stored. */
  unsigned long numObjects = 0;

  /* This stores a pointer to the object that is currently being saved. */
  const Object* currentObject = nullptr;

  /* This stores a pointer to the object that has previously been saved. */
  const Object* parentObject = nullptr;

  /* Stores the type of data to be exported. */
  FieldCategory content = BASE;

  /* Flag allowing us to skip writing the head of the XML element.
   * The flag is reset to 'true'.
   */
  bool skipHeader = false;

  /* Flag allowing us to skip writing the tail of the XML element.
   * The flag is reset to 'true'.
   */
  bool skipFooter = false;

  /* Flag to mark whether hidden objects need to be written as well. */
  bool writeHidden = false;

  /* Flag to mark whether to save objects or their reference. */
  bool writeReference = false;

  /* Flag to force the output mode to be base. */
  bool forceBase = false;

  /* Flag whether or not we are in service mode.
   * In service mode, objects are serialized slightly different.
   */
  bool service_mode = false;

  bool flatten_properties = false;
};

/* A class to model a string to be interpreted as a keyword.
 *
 * The class uses hashes to do a fast comparison with the set of keywords.
 */
class DataKeyword {
 private:
  /* This string stores the hash value of the element. */
  size_t hash = 0;

  /* A pointer to the string representation of the keyword.
   * The string buffer is to be managed by the code creating this
   * instance.
   */
  const char* ch = nullptr;

 public:
  /* Default constructor. */
  explicit DataKeyword() {}

  /* Constructor. */
  explicit DataKeyword(const string& n)
      : hash(Keyword::hash(n)), ch(n.c_str()) {}

  /* Constructor. */
  explicit DataKeyword(const char* c) : hash(Keyword::hash(c)), ch(c) {}

  /* Returns the hash value of this tag. */
  size_t getHash() const { return hash; }

  /* Returns this tag. */
  void reset(const char* const c) {
    hash = Keyword::hash(c);
    ch = c;
  }

  /* Return the element name. Since this method involves a lookup in a
   * table with Keywords, it has some performance impact and should be
   * avoided where possible. Only the hash of an element can efficiently
   * be retrieved.
   */
  const char* getName() const;

  /* Returns true when this element is an instance of this tag. This method
   * doesn't involve a string comparison and is extremely efficient. */
  bool isA(const Keyword& t) const { return t.getHash() == hash; }

  /* Returns true when this element is an instance of this tag. This method
   * doesn't involve a string comparison and is extremely efficient. */
  bool isA(const Keyword* t) const { return t->getHash() == hash; }

  /* Comparison operator. */
  bool operator<(const DataKeyword& o) const { return hash < o.hash; }

  /* String comparison. */
  bool operator==(const string o) const { return o == ch; }
};

/* This abstract class represents a variant data type.
 *
 * It can hold a data value of the following types:
 *   - bool
 *   - date
 *   - double
 *   - duration
 *   - int
 *   - long
 *   - object pointer
 *   - Python function pointer
 *   - string
 *   - unsigned long
 *   - list of strings
 */
class DataValue {
 public:
  virtual operator bool() const {
    throw LogicException("DataValue is an abstract class");
  }

  /* Destructor. */
  virtual ~DataValue() {}

  void operator>>(unsigned long int& val) const { val = getUnsignedLong(); }

  void operator>>(long& val) const { val = getLong(); }

  void operator>>(Duration& val) const { val = getDuration(); }

  void operator>>(bool& v) const { v = getBool(); }

  void operator>>(int& val) const { val = getInt(); }

  void operator>>(double& val) const { val = getDouble(); }

  void operator>>(Date& val) const { val = getDate(); }

  void operator>>(string& val) const { val = getString(); }

  virtual long getLong() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual unsigned long getUnsignedLong() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual Duration getDuration() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual int getInt() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual double getDouble() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual Date getDate() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual const string& getString() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual vector<string> getStringList() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual bool getBool() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual Object* getObject() const {
    throw LogicException("DataValue is an abstract class");
  }

  virtual void setLong(const long) = 0;

  virtual void setUnsignedLong(const unsigned long) = 0;

  virtual void setDuration(const Duration) = 0;

  virtual void setInt(const int) = 0;

  virtual void setDouble(const double) = 0;

  virtual void setDate(const Date) = 0;

  virtual void setString(const string&) = 0;

  virtual void setBool(const bool) = 0;

  virtual void setObject(Object*) = 0;
};

/* This class represents an XML element being read in from the
 * input file. */
class XMLData : public DataValue {
 private:
  /* This string stores the XML input data. */
  string m_strData;

  /* Object pointer. */
  Object* m_obj = nullptr;

 public:
  virtual operator bool() const { return !m_strData.empty() && !m_obj; }

  /* Default constructor. */
  XMLData() {}

  /* Constructor. */
  XMLData(const string& v) : m_strData(v) {}

  /* Copy constructor from DataValue base class. */
  XMLData(const DataValue& d) {
    m_obj = d.getObject();
    if (!m_obj) m_strData = d.getString();
  }

  /* Destructor. */
  virtual ~XMLData() {}

  /* Re-initializes an existing element. Using this method we can avoid
   * destroying and recreating XMLData objects too frequently. Instead
   * we can manage them in a array.
   */
  void reset() {
    m_strData.clear();
    m_obj = nullptr;
  }

  /* Add some characters to this data field of this element.
   * The second argument is the number of bytes, not the number of
   * characters.
   */
  void appendString(const char* pData) { m_strData.append(pData); }

  /* Set the data value of this element. */
  void setData(const char* pData) { m_strData.assign(pData); }

  /* Return the data field. */
  const char* getData() const { return m_strData.c_str(); }

  virtual long getLong() const { return atol(getData()); }

  virtual unsigned long getUnsignedLong() const { return atol(getData()); }

  virtual Duration getDuration() const { return Duration(getData()); }

  virtual int getInt() const { return atoi(getData()); }

  // Return the value as a double.
  // This conversion should be done with the C-locale, where a dot is used
  // as a decimal separator. Otherwise values in XML data files will be
  // read incorrectly!
  virtual double getDouble() const { return atof(getData()); }

  virtual Date getDate() const { return Date(getData()); }

  /* Returns the string value of the XML data. The xerces library takes care
   * of appropriately unescaping special character sequences. */
  virtual const string& getString() const { return m_strData; }

  virtual vector<string> getStringList() const {
    throw LogicException("Not implemented");
  }

  /* Interprets the element as a boolean value.
   * <p>Our implementation is a bit more generous and forgiving than the
   * boolean datatype that is part of the XML schema v2 standard.
   * The standard expects the following literals:
   *   {true, false, 1, 0}</p>
   * <p>Our implementation uses only the first charater of the text, and is
   * case insensitive. It thus matches a wider range of values:
   *   {t.*, T.*, f.*, F.*, 1.*, 0.*}</p>
   */
  bool getBool() const;

  Object* getObject() const { return m_obj; }

  virtual void setLong(const long l) {
    std::ostringstream o;
    o << l;
    m_strData = o.str();
  }

  virtual void setUnsignedLong(const unsigned long l) {
    std::ostringstream o;
    o << l;
    m_strData = o.str();
  }

  virtual void setDuration(const Duration d) { m_strData = string(d); }

  virtual void setInt(const int i) {
    std::ostringstream o;
    o << i;
    m_strData = o.str();
  }

  virtual void setDouble(const double d) {
    std::ostringstream o;
    o << d;
    m_strData = o.str();
  }

  virtual void setDate(const Date d) { m_strData = string(d); }

  virtual void setString(const string& v) {
    m_strData = v;
    m_obj = nullptr;
  }

  virtual void setBool(const bool b) { m_strData = b ? "true" : "false"; }

  virtual void setObject(Object* o) { m_obj = o; }
};

/* This class groups some functions used to interact with the operating
 * system environment.
 *
 * It handles:
 *   - The location of the configuration files.
 *   - The maximum number of processors / threads to be used by frePPLe.
 *   - An output stream for logging all output.
 *   - Dynamic loading of a shared library.
 */
class Environment {
 private:
  /* Caches the number of processor cores. */
  static int processorcores;

  /* A file where output is directed to. */
  static StreambufWrapper logfile;

  /* The name of the log file. */
  static string logfilename;

 public:
  /* Search for a file with a given name.
   * The following directories are searched in sequence to find a match:
   *   - The current directory.
   *   - The directory referred to by the variable FREPPLE_HOME, if it
   *     is defined.
   *   - The data directory as configured during the compilation.
   *     This applies only to linux / unix.
   *   - The library directory as configured during the compilation.
   *     This applies only to linux / unix.
   */
  static string searchFile(const string);

  /* Returns the number of processor cores on your machine. */
  static int getProcessorCores();

  /* Returns the name of the logfile. */
  static const string& getLogFile() { return logfilename; }

  /* Updates the filename for logging error messages and warnings.
   * The file is also opened for writing and the standard output and
   * standard error output streams are redirected to it.
   * If the filename starts with '+' the log file is appended to
   * instead of being overwritten.
   */
  static void setLogFile(const string& x);

  /* Type for storing parameters passed to a module that is loaded. */
  typedef map<string, XMLData> ParameterList;

  /* Updates the process name on Linux when the environment variable
   * FREPPLE_PROCESSNAME is set. Maximum 7 characters are used. */
  static void setProcessName();

  static unsigned long getloglimit() {
    if (logfilename.empty()) return 0;
    auto s = logfile.getLogLimit();
    if (s > ULONG_MAX) s = ULONG_MAX;
    return static_cast<unsigned long>(s);
  }

  static void setloglimit(unsigned long l) {
    if (!logfilename.empty()) logfile.setLogLimit(l);
  }

  static void truncateLogFile(unsigned long long);

  static unsigned long getLogFileSize();
};

/* This class instantiates the abstract DataValue class, and is a
 * wrapper around a standard Python PyObject pointer.
 *
 * When creating a PythonData from a C++ object, make sure to increment
 * the reference count of the object.
 * When constructing a PythonData from an existing Python object, the
 * code that provided us the PyObject pointer should have incremented the
 * reference count already.
 */
class PythonData : public DataValue {
 private:
  PyObject* obj = nullptr;

  // Used by the getString method to store a string value
  string result;

 public:
  /* Default constructor. The default value is equal to Py_None. */
  explicit PythonData() : obj(Py_None) { Py_INCREF(obj); }

  /* Destructor. */
  ~PythonData() {
    if (obj) Py_DECREF(obj);
  }

  /* Copy constructor. */
  PythonData(const PythonData& o) : obj(o) {
    if (obj) Py_INCREF(obj);
  }

  /* Constructor from an existing Python object. */
  PythonData(const PyObject* o) : obj(o ? const_cast<PyObject*>(o) : Py_None) {
    Py_INCREF(obj);
  }

  /* Set the internal pointer to nullptr. */
  inline void setNull() {
    if (obj) Py_DECREF(obj);
    obj = nullptr;
  }

  /* Return true if a valid Python object is available. */
  inline bool isValid() const { return obj != nullptr; }

  /* This conversion operator casts the object back to a PyObject pointer.
   * The reference count of the Python object is increased, so you want to be
   * careful to apply this conversion.
   */
  operator PyObject*() const {
    if (obj) Py_INCREF(obj);
    return obj;
  }

  /* Check for null value. */
  operator bool() const { return obj != nullptr && obj != Py_None; }

  /* Assignment operator. */
  PythonData& operator=(const PythonData& o) {
    if (obj) Py_DECREF(obj);
    obj = o.obj;
    if (obj) Py_INCREF(obj);
    return *this;
  }

  /* Check whether the Python object is of a certain type.
   * Subclasses of the argument type will also give a true return value.
   */
  bool check(const MetaClass* c) const {
    return obj ? PyObject_TypeCheck(obj, c->pythonClass) : false;
  }

  /* Check whether the Python object is of a certain type.
   * Subclasses of the argument type will also give a true return value.
   */
  bool check(const PythonType& c) const {
    return obj ? PyObject_TypeCheck(obj, c.type_object()) : false;
  }

  /* Convert a Python string into a C++ string. */
  inline const string& getString() const {
    if (obj == Py_None)
      const_cast<PythonData*>(this)->result = "";
    else if (PyUnicode_Check(obj)) {
      // It's a Python unicode string
      PyObject* x = PyUnicode_AsEncodedString(obj, "UTF-8", "ignore");
      const_cast<PythonData*>(this)->result = PyBytes_AS_STRING(x);
      Py_DECREF(x);
    } else {
      // It's not a Python string object.
      // Call the repr() function on the object, and encode the result in UTF-8.
      PyObject* x1 = PyObject_Str(obj);
      PyObject* x2 = PyUnicode_AsEncodedString(x1, "UTF-8", "ignore");
      const_cast<PythonData*>(this)->result = PyBytes_AS_STRING(x2);
      Py_DECREF(x1);
      Py_DECREF(x2);
    }
    return result;
  }

  /* Return a list of strings.
   * We return values and not references, which is not the most efficient...
   */
  vector<string> getStringList() const;

  /* Extract an unsigned long from the Python object. */
  unsigned long getUnsignedLong() const {
    if (obj == Py_None) return 0;
    if (PyUnicode_Check(obj)) {
      PyObject* t = PyFloat_FromString(obj);
      if (!t) throw DataException("Invalid number");
      double x = PyFloat_AS_DOUBLE(t);
      Py_DECREF(t);
      if (x < 0 || x > ULONG_MAX) throw DataException("Invalid number");
      return static_cast<unsigned long>(x);
    } else if (PyLong_Check(obj)) {
      auto result = PyLong_AsUnsignedLong(obj);
      if (PyErr_Occurred()) throw DataException("Invalid number");
      return result;
    } else
      return getInt();
  }

  /* Convert a Python datetime.date or datetime.datetime object into a
   * frePPLe date. */
  Date getDate() const;

  /* Convert a Python number or string into a C++ double. */
  inline double getDouble() const {
    if (obj == Py_None) return 0;
    if (PyUnicode_Check(obj)) {
      PyObject* t = PyFloat_FromString(obj);
      if (!t) throw DataException("Invalid number");
      double x = PyFloat_AS_DOUBLE(t);
      Py_DECREF(t);
      return x;
    }
    return PyFloat_AsDouble(obj);
  }

  /* Convert a Python number or string into a C++ integer. */
  inline int getInt() const {
    if (obj == Py_None) return 0;
    if (PyUnicode_Check(obj)) {
      PyObject* t = PyFloat_FromString(obj);
      if (!t) throw DataException("Invalid number");
      double x = PyFloat_AS_DOUBLE(t);
      Py_DECREF(t);
      if (x < INT_MIN || x > INT_MAX) throw DataException("Invalid number");
      return static_cast<int>(x);
    } else if (PyLong_Check(obj)) {
      int result = PyLong_AsLong(obj);
      if (result == -1 && PyErr_Occurred())
        throw DataException("Invalid number");
      return result;
    } else {
      double result = PyFloat_AsDouble(obj);
      if ((result == -1 && PyErr_Occurred()) || result > INT_MAX ||
          result < INT_MIN)
        throw DataException("Invalid number");
      return static_cast<int>(result);
    }
  }

  /* Convert a Python number into a C++ long. */
  inline long getLong() const {
    if (obj == Py_None) return 0;
    if (PyUnicode_Check(obj)) {
      PyObject* t = PyFloat_FromString(obj);
      if (!t) throw DataException("Invalid number");
      double x = PyFloat_AS_DOUBLE(t);
      Py_DECREF(t);
      if (x < LONG_MIN || x > LONG_MIN) throw DataException("Invalid number");
      return static_cast<long>(x);
    } else if (PyLong_Check(obj)) {
      long result = PyLong_AsLong(obj);
      if (result == -1 && PyErr_Occurred())
        throw DataException("Invalid number");
      return result;
    } else {
      double result = PyFloat_AsDouble(obj);
      if ((result == -1 && PyErr_Occurred()) || result > LONG_MAX ||
          result < LONG_MIN)
        throw DataException("Invalid number");
      return static_cast<long>(result);
    }
  }

  /* Convert a Python number into a C++ bool. */
  inline bool getBool() const { return PyObject_IsTrue(obj) ? true : false; }

  /* Convert a Python number as a number of seconds into a frePPLe
   * Duration.
   * A Duration is represented as a number of seconds in Python.
   */
  Duration getDuration() const;

  /* Return the frePPle Object referred to by the Python value.
   * If it points to a non-frePPLe object, the return value is nullptr.
   */
  Object* getObject() const;

  /* Constructor from a pointer to an Object.
   * The metadata of the Object instances allow us to create a Python
   * object that works as a proxy for the C++ object.
   */
  PythonData(Object* p);

  /* Convert a C++ string into a Unicode Python string. */
  inline PythonData(const string& val) { setString(val); }

  /* Convert a C++ double into a Python number. */
  inline PythonData(const double val) { setDouble(val); }

  /* Convert a C++ integer into a Python integer. */
  inline PythonData(const int val) { setInt(val); }

  /* Convert a C++ unsigned integer into a Python integer. */
  inline PythonData(const unsigned int val) { setInt(val); }

  /* Convert a C++ long into a Python long. */
  inline PythonData(const long val) { setLong(val); }

  /* Convert a C++ unsigned long into a Python long. */
  inline PythonData(const unsigned long val) { setUnsignedLong(val); }

  /* Convert a C++ boolean into a Python boolean. */
  inline PythonData(const bool val) { setBool(val); }

  /* Convert a frePPLe duration into a Python number representing
   * the number of seconds. */
  inline PythonData(const Duration val) { setDuration(val); }

  /* Convert a frePPLe date into a Python datetime.datetime object. */
  PythonData(const Date val) { setDate(val); }

  virtual void setLong(const long val) {
    if (obj) Py_DECREF(obj);
    obj = PyLong_FromLong(val);
  }

  virtual void setUnsignedLong(const unsigned long val) {
    if (obj) Py_DECREF(obj);
    obj = PyLong_FromUnsignedLong(val);
  }

  virtual void setDuration(const Duration val) {
    if (obj) Py_DECREF(obj);
    // A duration is represented as a number of seconds in Python
    obj = PyLong_FromLong(val);
  }

  virtual void setInt(const int val) {
    if (obj) Py_DECREF(obj);
    obj = PyLong_FromLong(val);
  }

  virtual void setDouble(const double val) {
    if (obj) Py_DECREF(obj);
    obj = PyFloat_FromDouble(val);
  }

  virtual void setDate(const Date);

  virtual void setString(const string& val) {
    if (obj) Py_DECREF(obj);
    if (val.empty()) {
      obj = Py_None;
      Py_INCREF(obj);
    } else
      // Convert internal UTF-8 representation to unicode
      obj = PyUnicode_FromString(val.c_str());
  }

  virtual void setBool(const bool val) {
    if (obj) Py_DECREF(obj);
    obj = val ? Py_True : Py_False;
    Py_INCREF(obj);
  }

  virtual void setObject(Object*);
};

/* This call is a wrapper around a Python function that can be
 * called from the C++ code.
 */
class PythonFunction : public PythonData {
 public:
  /* Default constructor. */
  PythonFunction() {}

  /* Constructor. */
  PythonFunction(const string&);

  /* Constructor. */
  PythonFunction(PyObject*);

  /* Copy constructor. */
  PythonFunction(const PythonFunction& o) : func(o.func) {
    if (func) {
      Py_INCREF(func);
    }
  }

  /* Assignment operator. */
  PythonFunction& operator=(const PythonFunction& o) {
    if (func) {
      Py_DECREF(func);
    }
    func = o.func;
    if (func) {
      Py_INCREF(func);
    }
    return *this;
  }

  /* Destructor. */
  ~PythonFunction() {
    if (func) {
      Py_DECREF(func);
    }
  }

  /* Conversion operator to a Python pointer. */
  operator const PyObject*() const { return func; }

  /* Conversion operator to a string. */
  operator string() const {
    return func ? PyEval_GetFuncName(func) : "nullptr";
  }

  /* Conversion operator to bool. */
  operator bool() const { return func != nullptr; }

  /* Call the Python function without arguments. */
  PythonData call() const;

  /* Call the Python function with one argument. */
  PythonData call(const PyObject*) const;

  /* Call the Python function with two arguments. */
  PythonData call(const PyObject*, const PyObject*) const;

 private:
  /* A pointer to the Python object. */
  PyObject* func = nullptr;
};

/* This class represents a dictionary of keyword + value pairs.
 *
 * This abstract class can be instantiated as XML attributes, or as a
 * Python keyword dictionary.
 *  - XML:
 *    &lt;buffer name="a" onhand="10" category="A" /&gt;
 *  - Python:
 *    buffer(name="a", onhand="10", category="A")
 *
 * TODO adding an abstract iterator or visitor to this class allows further
 * abstraction and simplification
 */
class DataValueDict {
 public:
  /* Lookup function in the dictionary. */
  virtual const DataValue* get(const Keyword&) const = 0;

  /* Destructor. */
  virtual ~DataValueDict() {}
};

/* This class is a wrapper around a Python dictionary. */
class PythonDataValueDict : public DataValueDict {
 private:
  PyObject* kwds;
  PythonData result;

 public:
  PythonDataValueDict(PyObject* a) : kwds(a) {}

  virtual const DataValue* get(const Keyword& k) const {
    if (!kwds) return nullptr;
    PyObject* val = PyDict_GetItemString(kwds, k.getName().c_str());
    if (!val) return nullptr;
    const_cast<PythonDataValueDict*>(this)->result = PythonData(val);
    return &result;
  }
};

/* Object is the abstract base class for the main entities.
 *
 * It handles to following capabilities:
 * - <b>Metadata:</b> All subclasses publish metadata about their structure.
 * - <b>Python object:</b> All objects live a double life as a Python object.
 * - <b>Callbacks:</b> When objects are created or deleted,
 *   interested classes or objects can get a callback notification.
 * - <b>Serialization:</b> Objects need to be persisted and later restored.
 *   Subclasses that don't need to be persisted can skip the implementation
 *   of the writeElement method.
 *   Instances can be marked as hidden, which means that they are not
 *   serialized at all.
 *
 * It inherits from the PyObject C struct, defined in the Python C API.
 * These functions aren't called directly from Python. Python first calls a
 * handler C-function and the handler function will use a virtual call to
 * run the correct C++-method.
 */
class Object : public PyObject {
  friend PyObject* getattro_handler(PyObject*, PyObject*);
  friend int setattro_handler(PyObject*, PyObject*, PyObject*);

 public:
  /* Constructor. */
  explicit Object() {}

  /* Destructor. */
  virtual ~Object() {
    if (PyObject::ob_refcnt > 1)
      logger << "Warning: Deleting " << (PyObject*)(this)
             << (PyObject::ob_type && PyObject::ob_type->tp_name
                     ? PyObject::ob_type->tp_name
                     : "nullptr")
             << " object that is still referenced " << (PyObject::ob_refcnt - 1)
             << " times" << endl;
    if (dict) Py_DECREF(dict);
  }

  /* Called while serializing the object. */
  virtual void writeElement(Serializer*, const Keyword&,
                            FieldCategory = BASE) const;

  /* Mark the object as hidden or not. Hidden objects are not exported
   * and are used only as dummy constructs. */
  virtual void setHidden(bool b) {}

  /* Method to set a custom property.
   * Avaialable types:
   *   1: bool
   *   2: date
   *   3: double
   *   4: string
   */
  void setProperty(const string& name, const DataValue& value, short type,
                   CommandManager* mgr = nullptr);

  /* Set a custom property referring to a python object. */
  void setProperty(const string& name, PyObject* value);

  /* Update a boolean property. */
  void setBoolProperty(const string&, bool);

  /* Update a date property. */
  void setDateProperty(const string&, Date);

  /* Update a double property. */
  void setDoubleProperty(const string&, double);

  /* Update a string property. */
  void setStringProperty(const string&, string);

  /* Check whether a property with a certain name is set. */
  bool hasProperty(const string&) const;

  /* Retrieve a boolean property. */
  bool getBoolProperty(const string&, bool = true) const;

  /* Retrieve a date property. */
  Date getDateProperty(const string&, Date = Date::infinitePast) const;

  /* Retrieve a double property. */
  double getDoubleProperty(const string&, double = 0.0) const;

  /* Retrieve a double property. */
  PyObject* getPyObjectProperty(const string&) const;

  /* Delete a property if it is set. */
  void deleteProperty(const string&);

  /* Retrieve a string property.
   * This method needs to be defined inline. On windows the function
   * otherwise can allocate and release the string in different modules,
   * resulting in a nasty crash.
   */
  string getStringProperty(const string& name, const string& def = "") const {
    if (!dict)
      // Not a single property has been defined
      return def;
    auto pythonstate = PyGILState_Ensure();
    PyObject* lkp = PyDict_GetItemString(dict, name.c_str());
    if (!lkp) {
      // Value not found in the dictionary
      PyGILState_Release(pythonstate);
      return def;
    }
    PythonData val(lkp);
    string result = val.getString();
    PyGILState_Release(pythonstate);
    return result;
  }

  /* Method to write custom properties to a serializer. */
  virtual void writeProperties(Serializer&) const;

  /* Returns whether an entity is real or dummy. */
  virtual bool getHidden() const { return false; }

  /* This returns the type information on the object, a bit similar to
   * the standard type_info information. */
  virtual const MetaClass& getType() const {
    throw LogicException("No type information registered");
  }

  /* Return the number of bytes this object occupies in memory. */
  virtual size_t getSize() const;

  /* This template function can generate a factory method for objects that
   * can be constructed with their default constructor.  */
  template <class T>
  static Object* create() {
    return new T();
  }

  template <class T>
  inline bool hasType() const {
    return this->getType() == *T::metadata;
  }

  template <class T, class U>
  inline bool hasType() const {
    return this->getType() == *T::metadata || this->getType() == *U::metadata;
  }

  template <class T, class U, class V>
  inline bool hasType() const {
    return this->getType() == *T::metadata || this->getType() == *U::metadata ||
           this->getType() == *V::metadata;
  }

  /* Free the memory.
   * Our extensions don't use the usual Python heap allocator. They are
   * created and initialized with the regular C++ new and delete. A special
   * deallocator is called from Python to delete objects when their reference
   * count reaches zero.
   */
  template <class T>
  static void deallocator(PyObject* o) {
    delete static_cast<T*>(o);
  }

  /* Template function that generates a factory method callable
   * from Python. */
  template <class T>
  static PyObject* create(PyTypeObject* pytype, PyObject* args,
                          PyObject* kwds) {
    try {
      // Find or create the C++ object
      PythonDataValueDict atts(kwds);
      Object* x = T::reader(T::metadata, atts);
      // Object was deleted
      if (!x) {
        Py_INCREF(Py_None);
        return Py_None;
      }

      // Iterate over extra keywords, and set attributes.   @todo move this
      // responsability to the readers...
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value)) {
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        if (!attr.isA(Tags::name) && !attr.isA(Tags::type) &&
            !attr.isA(Tags::action)) {
          PythonData field(value);
          const MetaFieldBase* fmeta = x->getType().findField(attr.getHash());
          if (!fmeta && x->getType().category)
            fmeta = x->getType().category->findField(attr.getHash());
          if (fmeta)
            // Update the attribute
            fmeta->setField(x, field);
          else
            x->setProperty(attr.getName(), value);
        }
      };
      Py_INCREF(x);
      return x;
    } catch (...) {
      PythonType::evalException();
      return nullptr;
    }
  }

  /* Return a XML representation of the object.
   * Two arguments are optional:
   * - mode: "S" (standard, default), "P" (plan), "D" (detail)
   * - If a file object is passed as second argument, the representation is
   *   directly written to it.
   *   Without second argument the representation is returned as a string.
   */
  static PyObject* toXML(PyObject*, PyObject*);

  /* Return a JSON representation of the object.
   * Two arguments are optional:
   * - mode: "S" (standard, default), "P" (plan), "D" (detail)
   * - If a file object is passed as second argument, the representation is
   *   directly written to it.
   *   Without second argument the representation is returned as a string.
   */
  static PyObject* toJSON(PyObject*, PyObject*);

  /* A function to force an object to be destroyed by the Python garbage
   * collection.
   * Be very careful to use this!
   */
  void resetReferenceCount() { PyObject::ob_refcnt = 0; }

  /* Returns the current reference count. */
  Py_ssize_t getReferenceCount() const { return PyObject::ob_refcnt; }

  /* Initialize the object to a certain Python type. */
  inline void initType(const MetaClass* t) {
    PyObject_INIT(this, t->pythonBaseClass);
  }

  /* Initialize the object to a certain Python type. */
  inline void initType(PyTypeObject* t) { PyObject_INIT(this, t); }

  /* Default getattro method.
   * Subclasses are expected to implement an override if the type supports
   * gettattro.
   */
  virtual PyObject* getattro(const DataKeyword& attr) {
    PyErr_SetString(PythonLogicException, "Missing method 'getattro'");
    return nullptr;
  }

  /* Default compare method.
   * Subclasses are expected to implement an override if the type supports
   * compare.
   */
  virtual int compare(const PyObject* other) const {
    throw LogicException("Missing method 'compare'");
  }

  /* Default iternext method.
   * Subclasses are expected to implement an override if the type supports
   * iteration.
   */
  virtual PyObject* iternext() {
    PyErr_SetString(PythonLogicException, "Missing method 'iternext'");
    return nullptr;
  }

  /* Default call method.
   * Subclasses are expected to implement an override if the type supports
   * calls.
   */
  virtual PyObject* call(const PythonData& args, const PythonData& kwds) {
    PyErr_SetString(PythonLogicException, "Missing method 'call'");
    return nullptr;
  }

  /* Default str method.
   * Subclasses are expected to implement an override if the type supports
   * conversion to a string.
   */
  virtual PyObject* str() const {
    PyErr_SetString(PythonLogicException, "Missing method 'str'");
    return nullptr;
  }

  // TODO Only required to keep pointerfield to Object valid, used in
  // problem.getOwner()
  static const MetaCategory* metadata;

  static PythonType* registerPythonType(int, const type_info*);

 protected:
  static vector<PythonType*> table;

 private:
  PyObject* dict = nullptr;
};

/* Template class to define Python extensions.
 *
 * The template argument should be your extension class, inheriting from
 * this template class:
 *   class MyClass : PythonExtension<MyClass>
 *
 * The structure of the C++ wrappers around the C Python API is heavily
 * inspired on the design of PyCXX.
 * More information can be found on http://cxx.sourceforge.net
 *
 * TODO This class has become somewhat redundant, and we can do without.
 */
template <class T>
class PythonExtension : public Object, public NonCopyable {
 public:
  /* Constructor.
   * The Python metadata fields always need to be set correctly.
   */
  explicit PythonExtension() {
    PyObject_Init(this, getPythonType().type_object());
  }

  /* Destructor. */
  virtual ~PythonExtension() {}

  /* This method keeps the type information object for your extension. */
  static PythonType& getPythonType() {
    static PythonType* cachedTypePtr = nullptr;
    if (cachedTypePtr) return *cachedTypePtr;

    // Register a new type
    cachedTypePtr = registerPythonType(sizeof(T), &typeid(T));

    // Using our own memory deallocator
    cachedTypePtr->supportdealloc(deallocator);

    return *cachedTypePtr;
  }

  /* Free the memory.
   * Our extensions don't use the usual Python heap allocator. They are
   * created and initialized with the regular C++ new and delete. A special
   * deallocator is called from Python to delete objects when their reference
   * count reaches zero.
   */
  static void deallocator(PyObject* o) { delete static_cast<T*>(o); }
};

/* Wrapper class to expose frePPLe iterators to Python.
 *
 * The requirements for the argument classes are as follows:
 *  - ITERCLASS must implement a method:
 *         DATACLASS* next()
 *    This returns the current value of the iterator, and then
 *    advances it.
 *  - If the iteration ends, the above method should return nullptr.
 *  - DATACLASS must be a subclass of Object, implementing the
 *    type member to point to a MetaClass.
 */
template <class ITERCLASS, class DATACLASS>
class PythonIterator : public Object {
  typedef PythonIterator<ITERCLASS, DATACLASS> MYCLASS;

 public:
  /* This method keeps the type information object for your extension. */
  static PythonType& getPythonType() {
    static PythonType* cachedTypePtr = nullptr;
    if (cachedTypePtr) return *cachedTypePtr;

    // Register a new type
    cachedTypePtr = registerPythonType(sizeof(MYCLASS), &typeid(MYCLASS));

    // Using our own memory deallocator
    cachedTypePtr->supportdealloc(deallocator<MYCLASS>);

    return *cachedTypePtr;
  }

  static int initialize() {
    // Initialize the type
    auto& x = getPythonType();
    if (!DATACLASS::metadata)
      throw LogicException("Iterator for " + string(typeid(DATACLASS).name()) +
                           " initialized before its data class");
    x.setName(DATACLASS::metadata->type + "Iterator");
    x.setDoc("frePPLe iterator for " + DATACLASS::metadata->type);
    x.supportiter();
    return x.typeReady();
  }

  static int initialize(string nm, string doc) {
    // Initialize the type
    auto& x = getPythonType();
    x.setName(nm);
    x.setDoc(nm);
    x.supportiter();
    return x.typeReady();
  }

  /* Constructor from a pointer.
   * The underlying iterator must have a matching constructor.
   */
  template <class OTHER>
  PythonIterator(const OTHER* o) : iter(o) {
    this->initType(getPythonType().type_object());
  }

  /* Default constructor.
   * The underlying iterator must have a matching constructor.
   */
  PythonIterator() { this->initType(getPythonType().type_object()); }

  /* Constructor from a reference.
   * The underlying iterator must have a matching constructor.
   */
  template <class OTHER>
  PythonIterator(const OTHER& o) : iter(o) {
    this->initType(getPythonType().type_object());
  }

  static PyObject* create(PyObject* self, PyObject* args) {
    return new MYCLASS();
  }

 private:
  ITERCLASS iter;

  virtual PyObject* iternext() {
    PyObject* result = iter.next();
    if (!result) return nullptr;
    Py_INCREF(result);
    return result;
  }
};

template <class ITERCLASS>
class PythonIteratorClass : public Object {
  typedef PythonIteratorClass<ITERCLASS> MYCLASS;

 public:
  /* This method keeps the type information object for your extension. */
  static PythonType& getPythonType() {
    static PythonType* cachedTypePtr = nullptr;
    if (cachedTypePtr) return *cachedTypePtr;

    // Register a new type
    cachedTypePtr = registerPythonType(sizeof(MYCLASS), &typeid(MYCLASS));

    // Using our own memory deallocator
    cachedTypePtr->supportdealloc(deallocator<MYCLASS>);

    return *cachedTypePtr;
  }

  static int initialize() {
    // Initialize the type
    auto& x = getPythonType();
    x.setName(ITERCLASS::metadata->type);
    x.setDoc("frePPLe " + ITERCLASS::metadata->type);
    x.supportiter();
    return x.typeReady();
  }

  static int initialize(string nm, string doc) {
    // Initialize the type
    auto& x = getPythonType();
    x.setName(nm);
    x.setDoc(nm);
    x.supportiter();
    return x.typeReady();
  }

  /* Constructor from a pointer.
   * The underlying iterator must have a matching constructor.
   */
  template <class OTHER>
  PythonIteratorClass(const OTHER* o) : iter(o) {
    this->initType(getPythonType().type_object());
  }

  /* Default constructor.
   * The underlying iterator must have a matching constructor.
   */
  PythonIteratorClass() { this->initType(getPythonType().type_object()); }

  /* Constructor from a reference.
   * The underlying iterator must have a matching constructor.
   */
  template <class OTHER>
  PythonIteratorClass(const OTHER& o) : iter(o) {
    this->initType(getPythonType().type_object());
  }

  static PyObject* create(PyObject* self, PyObject* args) {
    return new MYCLASS();
  }

 private:
  ITERCLASS iter;

  virtual PyObject* iternext() {
    PyObject* result = iter.next();
    if (!result) return nullptr;
    Py_INCREF(result);
    return result;
  }
};

//
// UTILITY CLASSES FOR MULTITHREADING
//

/* This class supports parallel execution of a number of functions. */
class ThreadGroup : public NonCopyable {
 public:
  /* Prototype of the thread function. */
  typedef void (*callable)(void*, int, void*);

  /* Constructor which defaults to have as many worker threads as there are
   * cores on the machine.
   */
  ThreadGroup() { maxParallel = Environment::getProcessorCores(); };

  /* Constructor with a predefined number of worker threads. */
  ThreadGroup(int i) { setMaxParallel(i); };

  /* Add a new function to be called and its argument. */
  void add(callable func, void* arg1, int arg2 = 0, void* arg3 = nullptr) {
    callables.push(make_tuple(func, arg1, arg2, arg3));
  }

  /* Execute all functions and wait for them to finish. */
  void execute();

  /* Returns the number of parallel workers that is activated.
   * By default we activate as many worker threads as there are cores on
   * the machine.
   */
  int getMaxParallel() const { return maxParallel; }

  /* Updates the number of parallel workers that is activated. */
  void setMaxParallel(int b) {
    if (b < 1)
      throw DataException("Invalid number of parallel execution threads");
    maxParallel = b;
  }

 private:
  typedef tuple<callable, void*, int, void*> callableWithArgument;

  /* Mutex to protect the callable vector during multi-threaded execution. */
  mutex lock;

  /* Specifies the maximum number of commands in the list that can be
   * executed in parallel.
   * The default value is 1, i.e. sequential execution.
   * The value of this field is NOT inherited from parent command lists.
   * Note that the maximum applies to this command list only, and it isn't
   * a system-wide limit on the creation of threads.
   */
  int maxParallel;

  /* Stack with all registered functions and their invocation arguments. */
  stack<callableWithArgument> callables;

  /* This functions runs a single command execution thread. It is used as
   * a holder for the main routines of a trheaded routine.
   */
  static void wrapper(ThreadGroup*);

  /* This method selects the next function to be executed. */
  callableWithArgument selectNextCallable();
};

//
// RED-BLACK TREE CLASS
//

/* This class implements a binary tree data structure. It is used as a
 * container for entities keyed by their name.
 *
 * Technically, the data structure can be described as a red-black tree
 * with intrusive tree nodes.
 */
class Tree : public NonCopyable {
 public:
  /* The algorithm assigns a color to each node in the tree. The color is
   * used to keep the tree balanced.
   * A node with color 'none' is a node that hasn't been inserted yet in
   * the tree.
   */
  enum class Color { red, black, none, head };

  /* This class represents a node in the tree.
   *
   * Elements which we want to represent in the tree will need to inherit
   * from this class, since this tree container is intrusive.
   */
  class TreeNode {
    friend class Tree;

   public:
    /* Destructor. */
    virtual ~TreeNode() {}

    /* Returns the name of this node. This name is used to sort the
     * nodes. */
    inline const string& getName() const { return nm; }

    inline void setName(const string& i) { nm = i; }

    /* Return the color of this node: "red" or "black" for actual nodes,
     * and "none" for the root node and nodes not yet inserted.
     */
    Color getColor() const { return color; }

    /* Comparison operator. */
    bool operator<(const TreeNode& o) { return nm < o.nm; }

    /* Default constructor. */
    TreeNode() {}

    /* Return a pointer to the node following this one. */
    TreeNode* increment() const {
      TreeNode* node = const_cast<TreeNode*>(this);
      if (node->right != nullptr) {
        node = node->right;
        while (node->left != nullptr) node = node->left;
      } else {
        TreeNode* y = node->parent;
        while (node == y->right) {
          node = y;
          y = y->parent;
        }
        if (node->right != y) node = y;
      }
      return node;
    }

    /* Return a pointer to the node preceding this one. */
    TreeNode* decrement() const {
      TreeNode* node = const_cast<TreeNode*>(this);
      if (node->color == Color::red && node->parent->parent == node)
        node = node->right;
      else if (node->left != nullptr) {
        TreeNode* y = node->left;
        while (y->right != nullptr) y = y->right;
        node = y;
      } else {
        TreeNode* y = node->parent;
        while (node == y->left) {
          node = y;
          y = y->parent;
        }
        node = y;
      }
      return node;
    }

   private:
    /* Name. */
    string nm;

    /* Pointer to the parent node. */
    TreeNode* parent = nullptr;

    /* Pointer to the left child node. */
    TreeNode* left = nullptr;

    /* Pointer to the right child node. */
    TreeNode* right = nullptr;

    /* Color of the node. This is used to keep the tree balanced. */
    Color color = Color::none;
  };

  /* Default constructor. */
  Tree(bool b = false) : count(0), clearOnDestruct(b) {
    header.color = Color::head;  // Mark as special head
    header.parent = nullptr;
    header.left = &header;
    header.right = &header;
  }

  /* Destructor.
   * By default, the objects in the tree are not deleted when the tree
   * is deleted. This is done for performance reasons: the program can shut
   * down faster.
   */
  ~Tree() {
    if (clearOnDestruct) clear();
  }

  /* Returns an iterator to the start of the list.
   * The user will need to take care of properly acquiring a read lock on
   * on the tree object.
   */
  TreeNode* begin() const { return const_cast<TreeNode*>(header.left); }

  /* Returns an iterator pointing beyond the last element in the list.
   * The user will need to take care of properly acquiring a read lock on
   * on the tree object.
   */
  TreeNode* end() const { return const_cast<TreeNode*>(&header); }

  /* Returns true if the list is empty.
   * Its complexity is O(1). */
  bool empty() const { return header.parent == nullptr; }

  static inline int compare(const string& a, const string& b) {
    return a.compare(b);
  }

  /* Renames an existing node, and adjusts its position in the tree. */
  void rename(TreeNode* obj, const string& newname, TreeNode* hint = nullptr) {
    if (obj->nm == newname) return;
    if (!obj->nm.empty()) {
      bool found;
      findLowerBound(newname, &found);
      if (found) {
        ostringstream o;
        o << "Can't rename '" << obj->nm << newname << "': key already in use";
        throw DataException(o.str());
      }
      erase(obj);
    }
    obj->nm = newname;
    insert(obj, hint);
  };

  /* This method returns the number of nodes inserted in this tree.
   * Its complexity is O(1), so it can be called on large trees without any
   * performance impact.
   */
  size_t size() const { return count; }

  /* Verifies the integrity of the tree and returns true if everything
   * is correct.
   * The tree should be locked before calling this function.
   */
  void verify() const {
    // Checks for an empty tree
    if (empty() || begin() == end()) {
      bool ok = (empty() && begin() == end() && header.left == &header &&
                 header.right == &header);
      if (!ok) throw LogicException("Invalid empty tree");
      return;
    }

    unsigned int len = countBlackNodes(header.left);
    size_t counter = 0;
    for (auto x = begin(); x != end(); x = x->increment()) {
      TreeNode* L = x->left;
      TreeNode* R = x->right;
      ++counter;

      if (x->color == Color::none)
        // Nodes must have a color
        throw LogicException("Colorless node included in a tree");

      if (x->color == Color::red)
        if ((L && L->color == Color::red) || (R && R->color == Color::red))
          // A red node can have only nullptr and black children
          throw LogicException("Wrong color on node");

      if (L && x->nm < L->nm)
        // Left child isn't smaller
        throw LogicException("Wrong sorting on left node");

      if (R && R->nm < x->nm)
        // Right child isn't bigger
        throw LogicException("Wrong sorting on right node");

      if (!L && !R && countBlackNodes(x) != len)
        // All leaf nodes have the same number of black nodes on their path
        // to the root
        throw LogicException("Unbalanced count of black nodes");
    }

    // Check whether the header has a good pointer to the leftmost element
    if (header.left != minimum(header.parent))
      throw LogicException("Incorrect tree minimum");

    // Check whether the header has a good pointer to the rightmost element
    if (header.right != maximum(header.parent))
      throw LogicException("Incorrect tree maximum");

    // Check whether the measured node count match the expectation?
    if (counter != size()) throw LogicException("Incorrect tree size");

    // If we reach this point, then this tree is healthy
  }

  /* Remove all elements from the tree. */
  void clear() {
    // Tree is already empty
    if (empty()) return;

    // Erase all elements
    for (auto x = begin(); x != end(); x = begin()) {
      Object* o = dynamic_cast<Object*>(x);
      if (o && o->getType().raiseEvent(o, SIG_REMOVE))
        delete (x);  // The destructor calls the erase method
      else
        throw DataException("Can't delete object");
    }
  }

  /* Remove a node from the tree. */
  void erase(TreeNode* z) {
    // A colorless node was never inserted in the tree, and shouldn't be
    // removed from it either...
    if (!z || z->color == Color::none) return;

    TreeNode* y = z;
    TreeNode* x = nullptr;
    TreeNode* x_parent = nullptr;
    --count;
    if (y->left == nullptr)        // z has at most one non-null child. y == z.
      x = y->right;                // x might be null.
    else if (y->right == nullptr)  // z has exactly one non-null child. y == z.
      x = y->left;                 // x is not null.
    else {
      // z has two non-null children.  Set y to
      y = y->right;  //   z's successor.  x might be null.
      while (y->left != nullptr) y = y->left;
      x = y->right;
    }
    if (y != z) {
      // relink y in place of z.  y is z's successor
      z->left->parent = y;
      y->left = z->left;
      if (y != z->right) {
        x_parent = y->parent;
        if (x) x->parent = y->parent;
        y->parent->left = x;  // y must be a child of left
        y->right = z->right;
        z->right->parent = y;
      } else
        x_parent = y;
      if (header.parent == z)
        header.parent = y;
      else if (z->parent->left == z)
        z->parent->left = y;
      else
        z->parent->right = y;
      y->parent = z->parent;
      std::swap(y->color, z->color);
      y = z;
      // y now points to node to be actually deleted
    } else {
      // y == z
      x_parent = y->parent;
      if (x) x->parent = y->parent;
      if (header.parent == z)
        header.parent = x;
      else if (z->parent->left == z)
        z->parent->left = x;
      else
        z->parent->right = x;
      if (header.left == z) {
        if (z->right == nullptr)  // z->left must be null also
          header.left = z->parent;
        // makes leftmost == header if z == root
        else
          header.left = minimum(x);
      }
      if (header.right == z) {
        if (z->left == nullptr)  // z->right must be null also
          header.right = z->parent;
        // makes rightmost == header if z == root
        else  // x == z->left
          header.right = maximum(x);
      }
    }
    if (y->color != Color::red) {
      while (x != header.parent && (x == nullptr || x->color == Color::black))
        if (x == x_parent->left) {
          TreeNode* w = x_parent->right;
          if (w->color == Color::red) {
            w->color = Color::black;
            x_parent->color = Color::red;
            rotateLeft(x_parent);
            w = x_parent->right;
          }
          if ((w->left == nullptr || w->left->color == Color::black) &&
              (w->right == nullptr || w->right->color == Color::black)) {
            w->color = Color::red;
            x = x_parent;
            x_parent = x_parent->parent;
          } else {
            if (w->right == nullptr || w->right->color == Color::black) {
              w->left->color = Color::black;
              w->color = Color::red;
              rotateRight(w);
              w = x_parent->right;
            }
            w->color = x_parent->color;
            x_parent->color = Color::black;
            if (w->right) w->right->color = Color::black;
            rotateLeft(x_parent);
            break;
          }
        } else {
          // same as above, with right <-> left.
          TreeNode* w = x_parent->left;
          if (w && w->color == Color::red) {
            w->color = Color::black;
            x_parent->color = Color::red;
            rotateRight(x_parent);
            w = x_parent->left;
          }
          if (w && (w->right == nullptr || w->right->color == Color::black) &&
              (w->left == nullptr || w->left->color == Color::black)) {
            w->color = Color::red;
            x = x_parent;
            x_parent = x_parent->parent;
          } else if (w) {
            if (w->left == nullptr || w->left->color == Color::black) {
              w->right->color = Color::black;
              w->color = Color::red;
              rotateLeft(w);
              w = x_parent->left;
            }
            w->color = x_parent->color;
            x_parent->color = Color::black;
            if (w->left) w->left->color = Color::black;
            rotateRight(x_parent);
            break;
          }
        }
      if (x) x->color = Color::black;
    }
  }

  /* Search for an element in the tree.
   * Profiling shows this function has a significant impact on the CPU
   * time (mainly because of the string comparisons), and has been
   * optimized as much as possible.
   */
  TreeNode* find(const string& k) const {
    auto x = header.parent;
    while (x) {
      auto comp = compare(k, x->nm);
      if (!comp) return x;
      x = comp < 0 ? x->left : x->right;
    }
    TreeNode* result = end();
    return result;
  }

  /* Find the element with this given key or the element
   * immediately preceding it.
   * The second argument is a boolean that is set to true when the
   * element is found in the list.
   */
  TreeNode* findLowerBound(const string& k, bool* f) const {
    auto lower = end();
    for (auto x = header.parent; x;) {
      int comp = compare(k, x->nm);
      if (!comp) {
        // Found
        if (f) *f = true;
        return x;
      }
      if (comp < 0)
        x = x->left;
      else {
        lower = x;
        x = x->right;
      }
    }
    if (f) *f = false;
    return lower;
  }

  /* Insert a new node in the tree. */
  TreeNode* insert(TreeNode* v) { return insert(v, nullptr); }

  /* Insert a new node in the tree. The second argument is a hint on
   * the proper location in the tree.
   * Profiling shows this function has a significant impact on the cpu
   * time (mainly because of the string comparisons), and has been
   * optimized as much as possible.
   */
  TreeNode* insert(TreeNode* z, TreeNode* hint) {
    assert(z);

    // Use the hint to create the proper starting point in the tree
    int comp;
    TreeNode* y;
    if (!hint) {
      // Effectively no hint given
      hint = header.parent;
      y = &header;
    } else {
      // Check if the hint is a good starting point to descend
      while (hint->parent) {
        comp = compare(z->nm, hint->parent->nm);
        if ((comp > 0 && hint == hint->parent->left) ||
            (comp < 0 && hint == hint->parent->right))
          // Move the hint up to the parent node
          // If I'm left child of my parent && new node needs right insert
          // or I'm right child of my parent && new node needs left insert
          hint = hint->parent;
        else
          break;
      }
      y = hint->parent;
    }

    // Step down the tree till we found a proper empty leaf node in the tree
    for (; hint; hint = comp < 0 ? hint->left : hint->right) {
      y = hint;
      // Exit the function if the key is already found
      comp = compare(z->nm, hint->nm);
      if (!comp) return hint;
    }

    if (y == &header || z->nm < y->nm) {
      // Inserting as a new left child
      y->left = z;  // also makes leftmost() = z when y == header
      if (y == &header) {
        // Inserting a first element in the list
        header.parent = z;
        header.right = z;
      }
      // maintain leftmost() pointing to min node
      else if (y == header.left)
        header.left = z;
    } else {
      // Inserting as a new right child
      y->right = z;
      // Maintain rightmost() pointing to max node.
      if (y == header.right) header.right = z;
    }

    // Set parent and child pointers of the new node
    z->parent = y;
    z->left = nullptr;
    z->right = nullptr;

    // Increase the node count
    ++count;

    // Rebalance the tree
    rebalance(z);
    return z;
  }

 private:
  /* Restructure the tree such that the depth of the branches remains
   * properly balanced. This method is called during insertion. */
  inline void rebalance(TreeNode* x) {
    x->color = Color::red;

    while (x != header.parent && x->parent->color == Color::red) {
      if (x->parent == x->parent->parent->left) {
        TreeNode* y = x->parent->parent->right;
        if (y && y->color == Color::red) {
          x->parent->color = Color::black;
          y->color = Color::black;
          x->parent->parent->color = Color::red;
          x = x->parent->parent;
        } else {
          if (x == x->parent->right) {
            x = x->parent;
            rotateLeft(x);
          }
          x->parent->color = Color::black;
          x->parent->parent->color = Color::red;
          rotateRight(x->parent->parent);
        }
      } else {
        TreeNode* y = x->parent->parent->left;
        if (y && y->color == Color::red) {
          x->parent->color = Color::black;
          y->color = Color::black;
          x->parent->parent->color = Color::red;
          x = x->parent->parent;
        } else {
          if (x == x->parent->left) {
            x = x->parent;
            rotateRight(x);
          }
          x->parent->color = Color::black;
          x->parent->parent->color = Color::red;
          rotateLeft(x->parent->parent);
        }
      }
    }
    header.parent->color = Color::black;
  }

  /* Rebalancing operation used during the rebalancing. */
  inline void rotateLeft(TreeNode* x) {
    TreeNode* y = x->right;
    x->right = y->left;
    if (y->left != nullptr) y->left->parent = x;
    y->parent = x->parent;

    if (x == header.parent)
      // x was the root
      header.parent = y;
    else if (x == x->parent->left)
      // x was on the left of its parent
      x->parent->left = y;
    else
      // x was on the right of its parent
      x->parent->right = y;
    y->left = x;
    x->parent = y;
  }

  /* Rebalancing operation used during the rebalancing. */
  inline void rotateRight(TreeNode* x) {
    TreeNode* y = x->left;
    x->left = y->right;
    if (y->right != nullptr) y->right->parent = x;
    y->parent = x->parent;

    if (x == header.parent)
      // x was the root
      header.parent = y;
    else if (x == x->parent->right)
      // x was on the right of its parent
      x->parent->right = y;
    else
      // x was on the left of its parent
      x->parent->left = y;
    y->right = x;
    x->parent = y;
  }

  /* Method used internally by the verify() method. */
  unsigned int countBlackNodes(TreeNode* node) const {
    unsigned int sum = 0;
    for (; node != header.parent; node = node->parent)
      if (node->color == Color::black) ++sum;
    return sum;
  }

  TreeNode* minimum(TreeNode* x) const {
    while (x->left) x = x->left;
    return x;
  }

  TreeNode* maximum(TreeNode* x) const {
    while (x->right) x = x->right;
    return x;
  }

  /* This node stores the following data:
   *  - parent: root of the tree.
   *  - left: leftmost element in the tree.
   *  - right: rightmost element in the tree.
   *  - this node itself is used as an element beyond the end of the list.
   */
  TreeNode header;

  /* Stores the number of elements in the tree. */
  size_t count;

  /* Controls whether the destructor needs to be clear all objects in the
   * tree in its destructor.
   * The default is to skip this cleanup! This is fine when you are dealing
   * with a static tree that lives throughout your program.
   * When you create a tree with a shorter lifespan, you'll need to pass
   * the constructor 'true' as argument in order to avoid memory leaks.
   */
  bool clearOnDestruct;
};

//
// UTILITY CLASS "COMMAND": for executing & undoing actions
//

/* Abstract base class for all commands.
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
 */
class Command {
  friend class CommandList;
  friend class CommandManager;
  friend class frepple::CommandMoveOperationPlan;  // TODO update api to avoid
                                                   // this friend
 public:
  /* Default constructor. The creation of a command should NOT execute the
   * command yet. The execute() method needs to be called explicitly to
   * do so.
   */
  Command() {};

  /* This method makes the change permanent.
   * A couple of notes on how this method should be implemented by the
   * subclasses:
   *   - Calling the method multiple times is harmless. Only the first
   *     call is expected to do something.
   */
  virtual void commit() {};

  /* This method permanently undoes the change.
   * A couple of notes on how this method should be implemented by the
   * subclasses:
   *   - Calling the rollback() method multiple times is harmless. Only
   *     the first call is expected to do something.
   */
  virtual void rollback() {};

  virtual ~Command() {};

  Command* getNext() const { return next; }

  /* Returns an identifier for each subclass:
   *  - 1: CommandList (and BookMark)
   *  - 2: CommandSetField
   *  - 3: CommandSetProperty
   *  - 4: CommandCreateObject
   *  - 5: CommandCreateOperationPlan
   *  - 6: CommandDeleteOperationPlan
   *  - 7: CommandMoveOperationPlan
   */
  virtual short getType() const = 0;

 private:
  /* Points to the commandlist which owns this command. The default value
   * is nullptr, meaning there is no owner. */
  Command* owner = nullptr;

  /* Points to the next command in the owner command list.
   * The commands are chained in a double linked list data structure. */
  Command* next = nullptr;

  /* Points to the previous command in the owner command list.
   * The commands are chained in a double linked list data structure. */
  Command* prev = nullptr;
};

/* A command to update a field on an object. */
class CommandSetField : public Command {
 private:
  Object* obj;
  const MetaFieldBase* fld;
  XMLData olddata;

 public:
  /* Constructor. */
  CommandSetField(Object* o, const MetaFieldBase* f, const DataValue& d)
      : obj(o), fld(f) {
    if (!obj || !fld) return;
    fld->getField(obj, olddata);
  }

  /* Destructor. */
  virtual ~CommandSetField() {
    if (obj && fld) fld->setField(obj, olddata);
  }

  /* Undoes the field change. */
  virtual void rollback() {
    if (!obj || !fld) return;
    fld->setField(obj, olddata);
    obj = nullptr;
    fld = nullptr;
  }

  /* Committing the change - nothing to be done as the change
   * is realized when creating the command. */
  virtual void commit() {
    obj = nullptr;
    fld = nullptr;
  }

  void clearObject() { obj = nullptr; }

  Object* getObject() const { return obj; }

  virtual short getType() const { return 2; }
};

/* A command to update a property on an object. */
class CommandSetProperty : public Command {
 private:
  Object* obj;
  string name;
  double old_double;
  string old_string;
  Date old_date;
  short type;
  bool old_exists;
  bool old_bool;

 public:
  /* Constructor. */
  CommandSetProperty(Object*, const string&, const DataValue&, short);

  /* Destructor. */
  virtual ~CommandSetProperty() {
    if (obj && !name.empty()) rollback();
  }

  /* Undoes the field change. */
  virtual void rollback();

  /* Committing the change - nothing to be done as the change
   * is realized when creating the command. */
  virtual void commit() {
    obj = nullptr;
    name = "";
  }

  void clearObject() { obj = nullptr; }

  Object* getObject() const { return obj; }

  virtual short getType() const { return 3; }
};

/* A command to create a new object.
 *
 * The object is already created when the command is created. This command
 * then allows to undo that creation.
 * It doesn't support recreation of the object at a later stage.
 */
class CommandCreateObject : public Command {
 private:
  Object* obj;

 public:
  /* Constructor. */
  CommandCreateObject(Object* o) : obj(o) {}

  /* Destructor. */
  virtual ~CommandCreateObject() {
    if (obj) rollback();
  }

  /* Committing the change - nothing to be done as the change
   * is realized before the command is created.
   */
  virtual void commit() { obj = nullptr; }

  /* Undoes the creation change. */
  virtual void rollback() {
    if (obj) {
      // Check for setfield commands on this object, and invalidate them.
      for (auto cmd = getNext(); cmd; cmd = cmd->getNext()) {
        switch (cmd->getType()) {
          case 1:
            // TODO: The undo is limited to the current command list. If there
            // are multiple bookmarks in the command manager we only undo a
            // part of the commands. For most practical purposes the current
            // behavior will be sufficient.
            throw LogicException("Not implemented");
          case 2:
            // CommandSetField
            if (static_cast<CommandSetField*>(cmd)->getObject() == obj)
              static_cast<CommandSetField*>(cmd)->clearObject();
            break;
          case 3:
            // CommandSetProperty
            if (static_cast<CommandSetProperty*>(cmd)->getObject() == obj)
              static_cast<CommandSetProperty*>(cmd)->clearObject();
            break;
        }
      }

      // Actual deletion
      delete obj;
      obj = nullptr;
    }
    obj = nullptr;
  }

  virtual short getType() const { return 4; }
};

/* A container command to group a series of commands together.
 *
 * This class implements the "composite" design pattern in order to get an
 * efficient and intuitive hierarchical grouping of commands.
 * @todo handle exceptions during commit, rollback, undo, redo
 */
class CommandList : public Command {
 private:
  /* Points to the first command in the list.
   * Following commands can be found by following the next pointers
   * on the commands.
   * The commands are this chained in a double linked list data structure.
   */
  Command* firstCommand = nullptr;

  /* Points to the last command in the list. */
  Command* lastCommand = nullptr;

 public:
  class iterator {
   public:
    /* Constructor. */
    iterator(Command* x) : cur(x) {}

    /* Return the content of the current node. */
    Command& operator*() const { return *cur; }

    /* Return the content of the current node. */
    Command* operator->() const { return cur; }

    /* Pre-increment operator which moves the pointer to the next
     * element. */
    iterator& operator++() {
      cur = cur->next;
      return *this;
    }

    /* Post-increment operator which moves the pointer to the next
     * element. */
    iterator operator++(int) {
      iterator tmp = *this;
      cur = cur->next;
      return tmp;
    }

    /* Comparison operator. */
    bool operator==(const iterator& y) const { return cur == y.cur; }

    /* Inequality operator. */
    bool operator!=(const iterator& y) const { return cur != y.cur; }

   private:
    Command* cur;
  };

  /* Returns an iterator over all commands in the list. */
  iterator begin() const { return iterator(firstCommand); }

  /* Returns an iterator beyond the last command. */
  iterator end() const { return iterator(nullptr); }

  /* Append an additional command to the end of the list. */
  void add(Command* c);

  /* Undoes all actions on the list.
   * At the end it also clears the list of actions.
   */
  virtual void rollback();

  /* Commits all actions on its list.
   * At the end it also clears the list of actions.
   */
  virtual void commit();

  /* Returns true if no commands have been added yet to the list. */
  bool empty() const { return !firstCommand; }

  /* Default constructor. */
  explicit CommandList() {}

  /* Destructor.
   * A commandlist should only be deleted when all of its commands
   * have been committed or undone. If this is not the case a warning
   * will be printed.
   */
  virtual ~CommandList();

  virtual short getType() const { return 1; }
};

/* This class allows management of tasks with supporting commiting them,
 * rolling them back, and setting bookmarks which can be undone and redone.
 */
class CommandManager : public Object {
 public:
  /* A bookmark that keeps track of commands that can be undone and redone. */
  class Bookmark : public CommandList {
    friend class CommandManager;

   private:
    Bookmark* nextBookmark = nullptr;
    Bookmark* prevBookmark = nullptr;
    Bookmark* parent = nullptr;
    bool active = true;
    Bookmark(Bookmark* p = nullptr) : parent(p) {}

   public:
    /* Returns true if the bookmark commands are active. */
    bool isActive() const { return active; }

    /* Returns true if the bookmark is a child, grand-child or
     * grand-grand-child of the argument bookmark.
     */
    bool isChildOf(const Bookmark* b) const {
      for (auto p = this; p; p = p->parent)
        if (p == b) return true;
      return false;
    }
  };

  /* An STL-like iterator to move over all bookmarks in forward order. */
  class iterator {
   public:
    /* Constructor. */
    iterator(Bookmark* x) : cur(x) {}

    /* Copy constructor. */
    iterator(const iterator& it) { cur = it.cur; }

    /* Copy assignment operator. */
    iterator& operator=(const iterator& it) {
      cur = it.cur;
      return *this;
    }

    /* Return the content of the current node. */
    Bookmark& operator*() const { return *cur; }

    /* Return the content of the current node. */
    Bookmark* operator->() const { return cur; }

    /* Pre-increment operator which moves the pointer to the next
     * element. */
    iterator& operator++() {
      cur = cur->nextBookmark;
      return *this;
    }

    /* Post-increment operator which moves the pointer to the next
     * element. */
    iterator operator++(int) {
      iterator tmp = *this;
      cur = cur->nextBookmark;
      return tmp;
    }

    /* Comparison operator. */
    bool operator==(const iterator& y) const { return cur == y.cur; }

    /* Inequality operator. */
    bool operator!=(const iterator& y) const { return cur != y.cur; }

   private:
    Bookmark* cur;
  };

  /* An STL-like iterator to move over all bookmarks in reverse order. */
  class reverse_iterator {
   public:
    /* Constructor. */
    reverse_iterator(Bookmark* x) : cur(x) {}

    /* Copy constructor. */
    reverse_iterator(const reverse_iterator& it) { cur = it.cur; }

    /* Copy assignment operator. */
    reverse_iterator& operator=(const reverse_iterator& it) {
      cur = it.cur;
      return *this;
    }

    /* Return the content of the current node. */
    Bookmark& operator*() const { return *cur; }

    /* Return the content of the current node. */
    Bookmark* operator->() const { return cur; }

    /* Pre-increment operator which moves the pointer to the next
     * element. */
    reverse_iterator& operator++() {
      cur = cur->prevBookmark;
      return *this;
    }

    /* Post-increment operator which moves the pointer to the next
     * element. */
    reverse_iterator operator++(int) {
      reverse_iterator tmp = *this;
      cur = cur->prevBookmark;
      return tmp;
    }

    /* Comparison operator. */
    bool operator==(const reverse_iterator& y) const { return cur == y.cur; }

    /* Inequality operator. */
    bool operator!=(const reverse_iterator& y) const { return cur != y.cur; }

   private:
    Bookmark* cur;
  };

 private:
  /* Head of a list of bookmarks.
   * A command manager has always at least this default bookmark.
   */
  Bookmark firstBookmark;

  /* Tail of a list of bookmarks. */
  Bookmark* lastBookmark;

  /* Current bookmarks.
   * If commands are added to the manager, this is the bookmark where
   * they'll be appended to.
   */
  Bookmark* currentBookmark;

 public:
  static const MetaCategory* metacategory;
  static const MetaClass* metadata;

  static int initialize();

  /* Constructor. */
  CommandManager() {
    initType(metadata);
    lastBookmark = &firstBookmark;
    currentBookmark = &firstBookmark;
  }

  /* Destructor. */
  ~CommandManager() {
    for (auto i = lastBookmark; i && i != &firstBookmark;) {
      Bookmark* tmp = i;
      i = i->prevBookmark;
      delete tmp;
    }
  }

  /* Returns an iterator over all bookmarks in forward direction. */
  iterator begin() { return iterator(&firstBookmark); }

  /* Returns an iterator beyond the last bookmark in forward direction. */
  iterator end() { return iterator(nullptr); }

  /* Returns an iterator over all bookmarks in reverse direction. */
  reverse_iterator rbegin() { return reverse_iterator(lastBookmark); }

  /* Returns an iterator beyond the last bookmark in reverse direction. */
  reverse_iterator rend() { return reverse_iterator(nullptr); }

  /* Add a command to the active bookmark. */
  void add(Command* c) { currentBookmark->add(c); }

  /* Add new setField command to the active bookmark. */
  void addCommandSetField(Object* o, const MetaFieldBase* f,
                          const DataValue& d) {
    add(new CommandSetField(o, f, d));
  }

  /* Create a new bookmark. */
  Bookmark* setBookmark();

  /* Undo all commands in a bookmark (and its children).
   * It can no longer be redone. The bookmark does however still exist.
   */
  void rollback(Bookmark*);

  /* Commit all commands. */
  void commit();

  /* Rolling back all commands. */
  void rollback();

  bool empty() const;
};

//
// INPUT PROCESSING CLASSES
//

/* An abstract class that is instantiated for data input streams
 * in various formats.
 */
class DataInput {
 public:
  /* Default constructor. */
  explicit DataInput() {}

  /* Update the command manager used to track all changes. */
  void setCommandManager(CommandManager* c) { cmds = c; }

  /* Return the command manager used to track all changes. */
  CommandManager* getCommandManager() const { return cmds; }

  /* Return the source field that will be populated on each object created
   * or updated from the XML data.
   */
  string getSource() const { return source; }

  /* Update the source field that will be populated on each object created
   * or updated from the XML data.
   */
  void setSource(const string& s) { source = s; }

  /* Specify a Python callback function that is for every object read
   * from the input stream.
   */
  void setUserExit(PyObject* p) { userexit = p; }

  /* Return the Python callback function. */
  const PythonFunction& getUserExit() const { return userexit; }

  /* Type definition for callback functions defined in C++. */
  typedef void (*callback)(Object*, void* data);

  void setUserExitCpp(callback f, void* data = nullptr) {
    user_exit_cpp = f;
    user_exit_cpp_data = data;
  }

  void callUserExitCpp(Object* o) const {
    if (user_exit_cpp) user_exit_cpp(o, user_exit_cpp_data);
  }

 private:
  /* A value to populate on the source field of all entities being created
   * or updated from the input data.
   */
  string source;

  /* A Python callback function that is called once an object has been read
   * from the XML input. The return value is not used.
   */
  PythonFunction userexit;

  /* A second type of callback function. This time called from C++. */
  callback user_exit_cpp = nullptr;
  void* user_exit_cpp_data = nullptr;

  /* A command manager used to track changes applied from the input. */
  CommandManager* cmds = nullptr;
};

//
//  UTILITY CLASSES "HASNAME", "HASHIERARCHY", "HASDESCRIPTION"
//

/* Base class for objects using a string as their primary key.
 *
 * Instances of this class have the following properties:
 *   - Have a unique name.
 *   - A hashtable (keyed on the name) is maintained as a container with
 *     all active instances.
 */
template <class T>
class HasName : public NonCopyable, public Tree::TreeNode, public Object {
 private:
  /* Maintains a global list of all created entities. The list is keyed
   * by the name. */
  static Tree st;
  typedef T* type;

 public:
  /* This class models a STL-like iterator that allows us to
   * iterate over the named entities in a simple and safe way.
   *
   * Objects of this class are created by the begin() and end() functions.
   */
  class iterator {
   public:
    /* Constructor. */
    iterator(Tree::TreeNode* x) : node(x) {}

    /* Return the content of the current node. */
    T& operator*() const { return *static_cast<T*>(node); }

    /* Return the content of the current node. */
    T* operator->() const { return static_cast<T*>(node); }

    /* Return current value and advance the iterator. */
    T* next() {
      if (node->getColor() == Tree::Color::head) return nullptr;
      T* tmp = static_cast<T*>(node);
      node = node->increment();
      return tmp;
    }

    /* Pre-increment operator which moves the pointer to the next
     * element. */
    iterator& operator++() {
      node = node->increment();
      return *this;
    }

    /* Post-increment operator which moves the pointer to the next
     * element. */
    iterator operator++(int) {
      Tree::TreeNode* tmp = node;
      node = node->increment();
      return tmp;
    }

    /* Pre-decrement operator which moves the pointer to the previous
     * element. */
    iterator& operator--() {
      node = node->decrement();
      return *this;
    }

    /* Post-decrement operator which moves the pointer to the previous
     * element. */
    iterator operator--(int) {
      Tree::TreeNode* tmp = node;
      node = node->decrement();
      return tmp;
    }

    /* Comparison operator. */
    bool operator==(const iterator& y) const { return node == y.node; }

    /* Inequality operator. */
    bool operator!=(const iterator& y) const { return node != y.node; }

   private:
    Tree::TreeNode* node;
  };

  /* struct used for range-base iteration. */
  struct all {
    static iterator begin() { return st.begin(); }
    static iterator end() { return st.end(); }
  };

  /* Returns a STL-like iterator to the end of the entity list. */
  static iterator end() { return st.end(); }

  /* Returns a STL-like iterator to the start of the entity list. */
  static iterator begin() { return st.begin(); }

  static PyObject* createIterator(PyObject* self, PyObject* args) {
    return new PythonIterator<iterator, T>(st.begin());
  }

  /* Returns false if no named entities have been defined yet. */
  static bool empty() { return st.empty(); }

  /* Returns the number of defined entities. */
  static size_t size() { return st.size(); }

  /* Debugging method to verify the validity of the tree.
   * An exception is thrown when the tree is corrupted. */
  static void verify() { st.verify(); }

  /* Deletes all elements from the list. */
  static void clear() { st.clear(); }

  /* Default constructor. */
  explicit HasName() {}

  /* Rename the entity. */
  virtual void setName(const string& newname) { st.rename(this, newname); }

  /* Rename the entity.
   * The second argument is a hint: when passing an entity with
   * a name close to the new one, the insertion will be sped up
   * considerably.
   */
  void setName(const string& newname, TreeNode* hint) {
    st.rename(this, newname, hint);
  }

  /* Destructor. */
  ~HasName() { st.erase(this); }

  /* Return the name as the string representation in Python. */
  virtual PyObject* str() const { return PythonData(getName()); }

  /* Comparison operator for Python. */
  int compare(const PyObject* other) const {
    return getName().compare(static_cast<const T*>(other)->getName());
  }

  /* Find an entity given its name. In case it can't be found, a nullptr
   * pointer is returned. */
  static T* find(const string& k) {
    Tree::TreeNode* i = st.find(k);
    return (i != st.end() ? static_cast<T*>(i) : nullptr);
  }

  /* Find the element with this given key or the element
   * immediately preceding it.
   * The optional second argument is a boolean that is set to true when
   * the element is found in the list.
   */
  static T* findLowerBound(const string& k, bool* f = nullptr) {
    Tree::TreeNode* i = st.findLowerBound(k, f);
    return (i != st.end() ? static_cast<T*>(i) : nullptr);
  }

  /* This method is available as a object creation factory for
   * classes that are using a string as a key identifier, in particular
   * classes derived from the HasName base class.
   * The following attributes are recognized:
   * - name:
   *   Name of the entity to be created/changed/removed.
   *   The default value is "unspecified".
   * - type:
   *   Determines the subclass to be created.
   *   The default value is "default".
   * - action:
   *   Determines the action to be performed on the object.
   *   This can be A (for 'add'), C (for 'change'), AC (for 'add_change')
   *   or R (for 'remove').
   *   'add_change' is the default value.
   */
  static Object* reader(const MetaClass* cat, const DataValueDict& in,
                        CommandManager* mgr = nullptr) {
    // Pick up the action attribute
    Action act = MetaClass::decodeAction(in);

    // Pick up the name attribute. An error is reported if it's missing.
    const DataValue* nameElement = in.get(Tags::name);
    if (!nameElement) throw DataException("Missing name field");
    string name = nameElement->getString();

    // Check if it exists already
    bool found;
    T* i = T::findLowerBound(name, &found);

    // Validate the action
    switch (act) {
      case Action::ADD:
        // Only additions are allowed
        if (found) throw DataException("Object '" + name + "' already exists");
        break;

      case Action::CHANGE:
        // Only changes are allowed
        if (!found) throw DataException("Object '" + name + "' doesn't exist");
        return i;

      case Action::REMOVE:
        // Delete the entity
        if (found) {
          // Send out the notification to subscribers
          if (i->getType().raiseEvent(i, SIG_REMOVE)) {
            // Delete the object
            delete i;
            return nullptr;
          } else
            // The callbacks disallowed the deletion!
            throw DataException("Can't remove object '" + name + "'");
        } else
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
    else {
      // Category metadata passed: we need to look up the type
      const DataValue* type = in.get(Tags::type);
      j = static_cast<const MetaCategory&>(*cat).findClass(
          type ? Keyword::hash(type->getString()) : MetaCategory::defaultHash);
      if (!j) {
        string t(type ? type->getString() : "default");
        throw DataException("No type " + t + " registered for category " +
                            cat->type);
      }
    }

    // No factory method is available for this object
    if (!j->factoryMethod) throw DataException("Can't create object " + name);

    // Create a new instance
    T* x = static_cast<T*>(j->factoryMethod());

    // Insert into the tree
    x->setName(name);

    // Run creation callbacks
    // During the callback there is no write lock set yet, since we can
    // assume we are the only ones aware of this new object. We also want
    // to make sure the 'add' signal comes before the 'before_change'
    // callback that is part of the writelock.
    if (!x->getType().raiseEvent(x, SIG_ADD)) {
      // Creation isn't allowed
      delete x;
      throw DataException("Can't create object " + name);
    }

    // Report the creation of the object with the manager
    if (mgr) mgr->add(new CommandCreateObject(x));

    return x;
  }

  /* Find an entity given its name. In case it can't be found, a nullptr
   * pointer is returned. */
  static Object* finder(const DataValueDict& k) {
    const DataValue* val = k.get(Tags::name);
    if (!val) return nullptr;
    Tree::TreeNode* i = st.find(val->getString());
    return (i != st.end() ? static_cast<Object*>(static_cast<T*>(i)) : nullptr);
  }
};

/* Implements a pool of re-usable string values, following the
 * flyweight design pattern.
 * TODO The implementation of this class is not thread-proof. Either this class
 * needs to use a shared pointer, or we simplify the design to implement an
 * add-only pool.
 */
class PooledString {
 private:
  /* Pool of strings. */
  static set<string> pool;
  static mutex pool_lock;

  /* Pointer to an element in the pool. */
  string* ptr = nullptr;

  void insert(const string& v) {
    if (v.empty())
      ptr = nullptr;
    else {
      lock_guard exclusive(pool_lock);
      auto tmp = pool.insert(v);
      ptr = const_cast<string*>(&*(tmp.first));
    }
  }

 public:
  const static PooledString emptystring;
  const static string nullstring;
  const static char nullchar;

  static pair<size_t, size_t> getSize() {
    return make_pair(
        pool.size(),
        pool.size() * (sizeof(set<string>::value_type) + 4 * sizeof(void*)));
  }

  /* Default constructor with empty pointer. */
  PooledString() {}

  /* Constructor from string.
   * The constructor is explicit to avoid implicit calls to this
   * constructor, which is slow.
   */
  explicit PooledString(const string& val) { insert(val); }

  /* Constructor from a character pointer.
   * The constructor is explicit to avoid implicit calls to this
   * constructor, which is slow.
   */
  explicit PooledString(const char* val) { insert(string(val)); }

  /* Copy constructor. */
  PooledString(const PooledString& other) : ptr(other.ptr) {}

  /* Assignment operator. */
  PooledString& operator=(const PooledString& other) {
    ptr = other.ptr;
    return *this;
  }

  /* String assignment operator. */
  PooledString& operator=(const string& val) {
    insert(val);
    return *this;
  }

  ~PooledString() {}

  inline explicit operator bool() const { return ptr != nullptr; }

  size_t hash() const { return Keyword::hash(ptr ? *ptr : nullstring); }

  /* Equality operator. */
  inline bool operator==(const PooledString& other) const {
    return ptr == other.ptr;
  }

  /* Inequality operator. */
  inline bool operator!=(const PooledString& other) const {
    return ptr != other.ptr;
  }

  /* Conversion to string. */
  operator const string&() const { return ptr ? *ptr : nullstring; }

  /* Return true if the string is empty. */
  inline bool empty() const { return !ptr; }

  /* Return the character at a certain position in the string, or \0 if not
   * found. */
  const char& at(size_t pos) const { return ptr ? ptr->at(pos) : nullchar; }

  /* Returns true if the argument is found in the string. */
  bool contains(const string& c) const {
    return ptr ? (ptr->find(c) != string::npos) : false;
  }

  /* Return the first character in the string. Or \0 if the string is empty. */
  const char& front() const { return ptr ? ptr->front() : nullchar; }

  /* Return the last character in the string. Or \0 if the string is empty. */
  const char& back() const { return ptr ? ptr->back() : nullchar; }

  /* Return the length of the string. */
  size_t size() const { return ptr ? ptr->size() : 0; }

  /* Returns true if the string starts with the argument. */
  bool starts_with(const string& s) const {
    return ptr ? (ptr->rfind(s, 0) == 0) : false;
  }

  inline const string& getString() const { return ptr ? *ptr : nullstring; }

  bool operator<(const PooledString& other) const {
    return (ptr ? *ptr : nullstring) < (other.ptr ? *other.ptr : nullstring);
  }

  /* Debugging function. */
  static void print() {
    lock_guard exclusive(pool_lock);
    for (auto i = pool.begin(); i != pool.end(); ++i)
      logger << "   " << *i << endl;
  }
};

/* Prints a pooled string to the outputstream. */
inline ostream& operator<<(ostream& os, const PooledString& s) {
  return os << string(s);
}

/* Prints a pooled string to the outputstream. */
inline ostream& operator<<(ostream& os, const Keyword& s) {
  return os << s.getName();
}

/* This is a decorator class for all objects having a source field. */
class HasSource {
 private:
  PooledString source;

 public:
  /* Returns the source field. */
  const string& getSource() const { return source; }

  /* Sets the source field. */
  void setSource(const string& c) { source = c; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::source, &Cls::getSource, &Cls::setSource);
  }
};

/* This is a decorator class for the main objects.
 *
 * Instances of this class have a description, category and sub_category.
 */
class HasDescription : public HasSource {
 public:
  /* Returns the category. */
  const string& getCategory() const { return cat; }

  /* Returns the sub_category. */
  const string& getSubCategory() const { return subcat; }

  /* Returns the getDescription. */
  const string& getDescription() const { return descr; }

  /* Sets the category field. */
  void setCategory(const string& f) { cat = f; }

  /* Sets the sub_category field. */
  void setSubCategory(const string& f) { subcat = f; }

  /* Sets the description field. */
  void setDescription(const string& f) { descr = f; }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::category, &Cls::getCategory,
                              &Cls::setCategory, "", BASE + PLAN);
    m->addStringRefField<Cls>(Tags::subcategory, &Cls::getSubCategory,
                              &Cls::setSubCategory, "", BASE + PLAN);
    m->addStringRefField<Cls>(Tags::description, &Cls::getDescription,
                              &Cls::setDescription, "", BASE + PLAN);
    HasSource::registerFields<Cls>(m);
  }

 private:
  PooledString cat;
  PooledString subcat;
  PooledString descr;
};

/* This is a base class for the main objects.
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
template <class T>
class HasHierarchy : public HasName<T> {
 public:
  class memberIterator;
  class memberRecursiveIterator;
  friend class memberIterator;
  friend class memberRecursiveIterator;
  /* This class models an STL-like iterator that allows us to
   * iterate over the immediate members.
   *
   * Objects of this class are created by the getMembers() method.
   */
  class memberIterator {
   public:
    /* Constructor to iterate over member entities. */
    memberIterator(const HasHierarchy<T>* x) : member_iter(true) {
      curmember = x ? const_cast<HasHierarchy<T>*>(x)->first_child : nullptr;
    }

    /* Constructor to iterate over all entities. */
    memberIterator() : curmember(&*T::begin()), member_iter(false) {}

    /* Constructor. */
    memberIterator(const typename HasName<T>::iterator& it)
        : curmember(&*it), member_iter(false) {}

    /* Return the content of the current node. */
    T& operator*() const { return *static_cast<T*>(curmember); }

    /* Return the content of the current node. */
    T* operator->() const { return static_cast<T*>(curmember); }

    /* Pre-increment operator which moves the pointer to the next member. */
    memberIterator& operator++() {
      if (member_iter)
        curmember = curmember->next_brother;
      else
        curmember = static_cast<T*>(curmember->increment());
      return *this;
    }

    /* Post-increment operator which moves the pointer to the next member. */
    memberIterator operator++(int) {
      memberIterator tmp = *this;
      if (member_iter)
        curmember = curmember->next_brother;
      else
        curmember = static_cast<T*>(curmember->increment());
      return tmp;
    }

    /* Return current member and advance the iterator. */
    T* next() {
      if (!curmember) return nullptr;
      T* tmp = static_cast<T*>(curmember);
      if (member_iter)
        curmember = curmember->next_brother;
      else
        curmember = static_cast<T*>(curmember->increment());
      return tmp;
    }

    /* Comparison operator. */
    bool operator==(const memberIterator& y) const {
      return curmember == y.curmember;
    }

    /* Inequality operator. */
    bool operator!=(const memberIterator& y) const {
      return curmember != y.curmember;
    }

    /* Comparison operator. */
    bool operator==(const typename HasName<T>::iterator& y) const {
      return curmember ? (curmember == &*y) : (y == T::end());
    }

    /* Inequality operator. */
    bool operator!=(const typename HasName<T>::iterator& y) const {
      return curmember ? (curmember != &*y) : (y != T::end());
    }

    /* End iterator. */
    static memberIterator end() { return nullptr; }

   private:
    /* Points to a member. */
    HasHierarchy<T>* curmember;
    bool member_iter;
  };

  /* This class models an iterator that allows us to
   * iterate over the members across all levels.
   */
  class memberRecursiveIterator : public NonCopyable {
   public:
    /* Constructor. */
    memberRecursiveIterator(const HasHierarchy<T>* x = nullptr)
        : root(const_cast<HasHierarchy<T>*>(x)),
          current(const_cast<HasHierarchy<T>*>(x)) {}

    memberRecursiveIterator(const memberRecursiveIterator& other)
        : root(other.root), current(other.current) {}

    memberRecursiveIterator& operator=(const memberRecursiveIterator& other) {
      root = other.root;
      current = other.current;
      return *this;
    }

    /* Return the content of the current node. */
    T& operator*() const { return static_cast<T&>(*current); }

    /* Return the content of the current node. */
    T* operator->() const { return static_cast<T*>(current); }

    /* Pre-increment operator which moves the pointer to the next member. */
    memberRecursiveIterator& operator++() {
      if (!current)
        return *this;
      else if (current->first_child)
        current = current->first_child;
      else if (current == root)
        current = nullptr;
      else if (current->next_brother)
        current = current->next_brother;
      else
        do {
          current = current->parent;
          if (current == root)
            current = nullptr;
          else if (current && current->next_brother) {
            current = current->next_brother;
            return *this;
          }
        } while (current);
      return *this;
    }

    T* next() {
      ++(*this);
      return static_cast<T*>(current);
    }

    bool empty() const { return current == nullptr; }

   private:
    HasHierarchy<T>* root;
    HasHierarchy<T>* current = nullptr;
  };

  /* Default constructor. */
  HasHierarchy() {}

  /* Destructor.
   * When deleting a node of the hierarchy, the children will get the
   * current parent as the new parent.
   * In this way the deletion of nodes doesn't create "dangling branches"
   * in the hierarchy. We just "collapse" a certain level.
   */
  ~HasHierarchy();

  /* Return a member iterator. */
  memberIterator getMembers() const { return this; }

  /* Return an iterator over all members, across all member levels. */
  memberRecursiveIterator getAllMembers() const { return this; }

  /* Return the first child. */
  T* getFirstChild() const { return first_child; }

  /* Return my next brother. */
  T* getNextBrother() const { return next_brother; }

  /* Return true if an object is part of the children of a second object. */
  bool isMemberOf(T* p) const {
    for (auto tmp = this; tmp; tmp = tmp->parent)
      if (tmp == p)
        // Yes, we find the argument in the parent hierarchy
        return true;
    return false;
  }

  T* getTop() const {
    auto tmp = const_cast<T*>(static_cast<const T*>(this));
    while (tmp->parent) tmp = tmp->parent;
    return tmp;
  }

  /* Return the first root object. */
  static T* getRoot() { return !T::empty() ? T::begin()->getTop() : nullptr; }

  /* Returns true if this entity belongs to a higher hierarchical level.
   * An entity can have only a single owner, and can't belong to multiple
   * hierarchies.
   */
  bool hasOwner() const { return parent != nullptr; }

  /* Returns true if this entity has lower level entities belonging to
   * it. */
  bool isGroup() const { return first_child != nullptr; }

  /* Changes the owner of the entity.
   * The argument must be a valid pointer to an entity of the same type.
   * A nullptr pointer can be passed to clear the existing owner.
   */
  void setOwner(T* f);

  /* Returns the owning entity. */
  inline T* getOwner() const { return parent; }

  /* Returns the level in the hierarchy.
   * Level 0 means the entity doesn't have any parent.
   * Level 1 means the entity has a parent entity with level 0.
   * Level "x" means the entity has a parent entity whose level is "x-1".
   */
  unsigned short getHierarchyLevel() const;

  /* Bubble sort to get all members in order. */
  void sortMembers() const {
    bool swapped;
    do {
      swapped = false;
      T* prev = nullptr;
      for (auto iter = first_child; iter && iter->next_brother;
           iter = iter->next_brother) {
        if (*(iter->next_brother) < *iter) {
          swapped = true;
          auto tmp = iter->next_brother->next_brother;
          if (prev)
            prev->next_brother = iter->next_brother;
          else
            const_cast<HasHierarchy<T>*>(this)->first_child =
                iter->next_brother;
          iter->next_brother->next_brother = iter;
          iter->next_brother = tmp;
          if (!tmp) const_cast<HasHierarchy<T>*>(this)->last_child = iter;
        }
        prev = iter;
      }
    } while (swapped);
  }

  template <class Cls>
  static inline void registerFields(MetaClass* m) {
    m->addStringRefField<Cls>(Tags::name, &Cls::getName, &Cls::setName, "",
                              MANDATORY);
    m->addPointerField<Cls, Cls>(Tags::owner, &Cls::getOwner, &Cls::setOwner,
                                 BASE + PARENT);
    m->addIteratorField<Cls, typename Cls::memberIterator, Cls>(
        Tags::members, *(Cls::metadata->typetag), &Cls::getMembers, DETAIL);
    m->addPointerField<Cls, Cls>(Tags::root, &Cls::getTop, nullptr,
                                 DONT_SERIALIZE);
    m->addIteratorField<Cls, typename Cls::memberRecursiveIterator, Cls>(
        Tags::allmembers, *(Cls::metadata->typetag), &Cls::getAllMembers,
        DONT_SERIALIZE);
  }

 private:
  /* Children are linked as a single linked list. */
  T* parent = nullptr;
  T* first_child = nullptr;
  T* last_child = nullptr;
  T* next_brother = nullptr;
};

//
// ASSOCIATION
//

/* This template class represents a data structure for a load or flow
 * network.
 *
 * A node class has pointers to 2 root classes. The 2 root classes each
 * maintain a singly linked list of nodes.
 * An example to clarify the usage:
 *  - class "node" = a newspaper subscription.
 *  - class "person" = maintains a list of all his subscriptions.
 *  - class "newspaper" = maintains a list of all subscriptions for it.
 *
 * This data structure could be replaced with 2 linked lists, but this
 * specialized data type consumes considerably lower memory.
 *
 * Reading from the structure is safe in multi-threading mode.
 * Updates to the data structure in a multi-threading mode require the user
 * to properly lock and unlock the container.
 */
template <class A, class B, class C>
class Association {
 public:
  class Node;

 private:
  /* A abstract base class for the internal representation of the
   * association lists.
   */
  class List {
    friend class Node;

   public:
    C* first = nullptr;
    C* last = nullptr;

   public:
    List() {};

    bool empty() const { return first == nullptr; }
  };

 public:
  /* A list type of the "first" / "from" part of the association. */
  class ListA : public List {
   public:
    /* Constructor. */
    ListA() {};

    /* An iterator over the associated objects. */
    class iterator {
     protected:
      C* nodeptr;

     public:
      iterator(C* n) : nodeptr(n) {};

      C& operator*() const { return *nodeptr; }

      C* operator->() const { return nodeptr; }

      bool operator==(const iterator& x) const { return nodeptr == x.nodeptr; }

      bool operator!=(const iterator& x) const { return nodeptr != x.nodeptr; }

      iterator& operator++() {
        nodeptr = nodeptr->nextA;
        return *this;
      }

      iterator operator++(int i) {
        iterator j = *this;
        nodeptr = nodeptr->nextA;
        return j;
      }

      C* next() {
        C* tmp = nodeptr;
        if (nodeptr) nodeptr = nodeptr->nextA;
        return tmp;
      }
    };

    /* An iterator over the associated objects. */
    class const_iterator {
     protected:
      C* nodeptr;

     public:
      const_iterator(C* n) : nodeptr(n) {};

      const C& operator*() const { return *nodeptr; }

      const C* operator->() const { return nodeptr; }

      bool operator==(const const_iterator& x) const {
        return nodeptr == x.nodeptr;
      }

      bool operator!=(const const_iterator& x) const {
        return nodeptr != x.nodeptr;
      }

      const_iterator& operator++() {
        nodeptr = nodeptr->nextA;
        return *this;
      }

      const_iterator operator++(int i) {
        const_iterator j = *this;
        nodeptr = nodeptr->nextA;
        return j;
      }

      C* next() {
        C* tmp = nodeptr;
        if (nodeptr) nodeptr = nodeptr->nextA;
        return tmp;
      }
    };

    iterator begin() { return iterator(this->first); }

    const_iterator begin() const { return const_iterator(this->first); }

    iterator end() { return iterator(nullptr); }

    const_iterator end() const { return const_iterator(nullptr); }

    /* Destructor. */
    ~ListA() {
      C* next = nullptr;
      for (C* p = this->first; p; p = next) {
        next = p->nextA;
        delete p;
      }
    }

    /* Remove an association. */
    void erase(const C* n) {
      if (!n) return;
      if (n == this->first) {
        this->first = n->nextA;
        if (this->last == n) this->last = nullptr;
      } else
        for (C* p = this->first; p; p = p->nextA)
          if (p->nextA == n) {
            p->nextA = n->nextA;
            if (this->last == n) this->last = p;
            return;
          }
    }

    /* Return the number of associations. */
    size_t size() const {
      size_t i(0);
      for (C* p = this->first; p; p = p->nextA) ++i;
      return i;
    }

    /* Search for the association effective at a certain date. */
    C* find(const B* b, Date d = Date::infinitePast) const {
      for (C* p = this->first; p; p = p->nextA)
        if (p->ptrB == b && p->effectivity.within(d)) return p;
      return nullptr;
    }

    /* Search for the association with a certain name. */
    C* find(const string& n) const {
      for (C* p = this->first; p; p = p->nextA)
        if (p->name == n) return p;
      return nullptr;
    }
  };

  /* A list type of the "second" / "to" part of the association. */
  class ListB : public List {
   public:
    /* Constructor. */
    ListB() {};

    /* An iterator over the associated objects. */
    class iterator {
     protected:
      C* nodeptr;

     public:
      iterator(C* n) : nodeptr(n) {};

      C& operator*() const { return *nodeptr; }

      C* operator->() const { return nodeptr; }

      bool operator==(const iterator& x) const { return nodeptr == x.nodeptr; }

      bool operator!=(const iterator& x) const { return nodeptr != x.nodeptr; }

      iterator& operator++() {
        nodeptr = nodeptr->nextB;
        return *this;
      }

      iterator operator++(int i) {
        iterator j = *this;
        nodeptr = nodeptr->nextB;
        return j;
      }

      C* next() {
        C* tmp = nodeptr;
        if (nodeptr) nodeptr = nodeptr->nextB;
        return tmp;
      }
    };

    /* An iterator over the associated objects. */
    class const_iterator {
     protected:
      C* nodeptr;

     public:
      const_iterator(C* n) : nodeptr(n) {};

      const C& operator*() const { return *nodeptr; }

      const C* operator->() const { return nodeptr; }

      bool operator==(const const_iterator& x) const {
        return nodeptr == x.nodeptr;
      }

      bool operator!=(const const_iterator& x) const {
        return nodeptr != x.nodeptr;
      }

      const_iterator& operator++() {
        nodeptr = nodeptr->nextB;
        return *this;
      }

      const_iterator operator++(int i) {
        const_iterator j = *this;
        nodeptr = nodeptr->nextB;
        return j;
      }

      C* next() {
        C* tmp = nodeptr;
        if (nodeptr) nodeptr = nodeptr->nextB;
        return tmp;
      }
    };

    /* Destructor. */
    ~ListB() {
      C* next = nullptr;
      for (C* p = this->first; p; p = next) {
        next = p->nextB;
        delete p;
      }
    }

    iterator begin() { return iterator(this->first); }

    const_iterator begin() const { return const_iterator(this->first); }

    iterator end() { return iterator(nullptr); }

    const_iterator end() const { return const_iterator(nullptr); }

    /* Remove an association. */
    void erase(const C* n) {
      if (!n) return;
      if (n == this->first) {
        this->first = n->nextB;
        if (this->last == n) this->last = nullptr;
      } else
        for (C* p = this->first; p; p = p->nextB)
          if (p->nextB == n) {
            p->nextB = n->nextB;
            if (this->last == n) this->last = p;
            return;
          }
    }

    /* Return the number of associations. */
    size_t size() const {
      size_t i(0);
      for (C* p = this->first; p; p = p->nextB) ++i;
      return i;
    }

    /* Search for the association effective at a certain date. */
    C* find(const A* b, Date d = Date::infinitePast) const {
      for (C* p = this->first; p; p = p->nextB)
        if (p->ptrA == b && p->effectivity.within(d)) return p;
      return nullptr;
    }

    /* Search for the association with a certain name. */
    C* find(const string& n) const {
      for (C* p = this->first; p; p = p->nextB)
        if (p->name == n) return p;
      return nullptr;
    }
  };

  /* A base class for the class representing the association
   * itself.
   */
  class Node {
   public:
    A* ptrA = nullptr;
    B* ptrB = nullptr;
    C* nextA = nullptr;
    C* nextB = nullptr;
    DateRange effectivity;
    PooledString name;
    int priority = 1;

   public:
    /* Constructor. */
    Node() {};

    /* Constructor. */
    Node(A* a, B* b, const ListA& al, const ListB& bl) : ptrA(a), ptrB(b) {
      if (al.last)
        // Append at the end of the A-list
        al.last->nextA = static_cast<C*>(this);
      else
        // First on the A-list
        const_cast<ListA&>(al).first = static_cast<C*>(this);
      const_cast<ListA&>(al).last = static_cast<C*>(this);
      if (bl.last)
        // Append at the end of the B-list
        bl.last->nextB = static_cast<C*>(this);
      else
        // First on the B-list
        const_cast<ListB&>(bl).first = static_cast<C*>(this);
      const_cast<ListB&>(bl).last = static_cast<C*>(this);
    }

    void setPtrA(A* a, const ListA& al) {
      // Don't allow updating an already valid link
      if (ptrA) throw DataException("Can't reassign existing association");
      ptrA = a;
      if (al.last)
        // Append at the end of the A-list
        al.last->nextA = static_cast<C*>(this);
      else
        // First on the A-list
        const_cast<ListA&>(al).first = static_cast<C*>(this);
      const_cast<ListA&>(al).last = static_cast<C*>(this);
    }

    void setPtrB(B* b, const ListB& bl) {
      // Don't allow updating an already valid link
      if (ptrB) throw DataException("Can't reassign existing association");
      ptrB = b;
      if (bl.last)
        // Append at the end of the B-list
        bl.last->nextB = static_cast<C*>(this);
      else
        // First on the B-list
        const_cast<ListB&>(bl).first = static_cast<C*>(this);
      const_cast<ListB&>(bl).last = static_cast<C*>(this);
    }

    void setPtrAB(A* a, B* b, const ListA& al, const ListB& bl) {
      setPtrA(a, al);
      setPtrB(b, bl);
    }

    A* getPtrA() const { return ptrA; }

    B* getPtrB() const { return ptrB; }

    /* Update the start date of the effectivity range. */
    void setEffectiveStart(Date d) { effectivity.setStart(d); }

    /* Update the end date of the effectivity range. */
    void setEffectiveEnd(Date d) { effectivity.setEnd(d); }

    /* Update the effectivity range. */
    void setEffective(DateRange dr) { effectivity = dr; }

    /* Get the start date of the effectivity range. */
    Date getEffectiveStart() const { return effectivity.getStart(); }

    /* Get the end date of the effectivity range. */
    Date getEffectiveEnd() const { return effectivity.getEnd(); }

    /* Return the effectivity daterange.
     * The default covers the complete time horizon.
     */
    DateRange getEffective() const { return effectivity; }

    /* Sets an optional, non-unique name for the association.
     * All associations with the same name are considered alternates
     * of each other.
     */
    void setName(const string& x) { name = x; }

    /* Return the optional name of the association. */
    const string& getName() const { return name; }

    /* Update the priority. */
    void setPriority(int i) { priority = i; }

    /* Return the priority. */
    int getPriority() const { return priority; }
  };

  static Object* reader(const MetaClass* cat, const DataValueDict& in,
                        CommandManager* mgr = nullptr) {
    // Pick up the action attribute
    Action act = MetaClass::decodeAction(in);
    Object* obj = C::finder(in);

    switch (act) {
      case Action::REMOVE:
        if (!obj) throw DataException("Can't find object for removal");
        delete obj;
        return nullptr;
      case Action::CHANGE:
        if (!obj) throw DataException("Object doesn't exist");
        return obj;
      case Action::ADD:
        if (obj) throw DataException("Object already exists");
      default:
        /* Lookup the class in the map of registered classes. */
        const MetaClass* j;
        if (cat->category)
          // Class metadata passed: we already know what type to create
          j = cat;
        else {
          // Category metadata passed: we need to look up the type
          const DataValue* type = in.get(Tags::type);
          j = static_cast<const MetaCategory&>(*cat).findClass(
              type ? Keyword::hash(type->getString())
                   : MetaCategory::defaultHash);
          if (!j) {
            string t(type ? type->getString() : "default");
            throw LogicException("No type " + t + " registered for category " +
                                 cat->type);
          }
        }

        // Call the factory method
        assert(j->factoryMethod);
        Object* result = j->factoryMethod();

        // Run the callback methods
        if (!result->getType().raiseEvent(result, SIG_ADD)) {
          // Creation denied
          delete result;
          throw DataException("Can't create object");
        }

        // Report the object creation to the manager
        if (mgr) mgr->add(new CommandCreateObject(result));

        // Creation accepted
        return result;
    }
    throw LogicException("Unreachable code reached");
    return nullptr;
  }
};

template <class T>
inline ostream& operator<<(ostream& o, const HasName<T>& n) {
  return o << n.getName();
}

template <class T>
inline ostream& operator<<(ostream& o, const HasName<T>* n) {
  return o << (n ? n->getName() : string("NULL"));
}

template <class T>
void HasHierarchy<T>::setOwner(T* fam) {
  // Check if already set to the same entity
  if (parent == fam) return;

  // Avoid loops in the hierarchy. For instance, HasHierarchy A points to B
  // as its owner, and B points to A.
  for (T* t = fam; t; t = t->parent)
    if (t == this) {
      logger << "Warning: Ignoring invalid hierarchy relation between \""
             << this->getName() << "\" and \"" << fam->getName() << "\""
             << endl;
      return;
    }

  // Clean up previous owner, if any
  if (parent) {
    if (parent->first_child == this) {
      // We are the first child of our parent
      parent->first_child = next_brother;
      if (parent->last_child == this) parent->last_child = nullptr;
    } else {
      // Removed somewhere in the middle of the list of children
      T* i = parent->first_child;
      while (i && i->next_brother != this) i = i->next_brother;
      if (!i) throw LogicException("Invalid hierarchy data");
      if (parent->last_child == this) parent->last_child = i;
      i->next_brother = next_brother;
    }
    next_brother = nullptr;
  }

  // Set new owner
  parent = fam;

  // Register the new member at the owner
  if (fam) {
    if (fam->last_child)
      // We append it at the end of the list, preserving the insert order.
      fam->last_child->next_brother = static_cast<T*>(this);
    else
      // I am the first child of my parent
      fam->first_child = static_cast<T*>(this);
    fam->last_child = static_cast<T*>(this);
  }
}

template <class T>
HasHierarchy<T>::~HasHierarchy() {
  // All my members now point to my parent.
  T* last_child = nullptr;
  for (T* i = first_child; i; i = i->next_brother) {
    i->parent = parent;
    last_child = i;
  }

  if (parent && last_child) {
    // Extend the child list of my parent.
    // The new children are prepended to the list of existing children.
    last_child->next_brother = parent->first_child;
    parent->first_child = first_child;
  }
  if (!parent) {
    // If there is no new parent, we also clear the next-brother field of
    // the children.
    T* j;
    for (T* i = first_child; i; i = j) {
      j = i->next_brother;
      i->next_brother = nullptr;
    }
  } else
    // A parent exists and I have to remove myself as a member
    setOwner(nullptr);
}

template <class T>
unsigned short HasHierarchy<T>::getHierarchyLevel() const {
  unsigned short i(0);
  for (auto p = this; p->parent; p = p->parent) ++i;
  return i;
}

//
// META FIELD DEFINITIONS
//

template <class Cls>
class MetaFieldString : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(const string&);

  typedef string (Cls::*getFunction)(void) const;

  MetaFieldString(const Keyword& n, getFunction getfunc,
                  setFunction setfunc = nullptr, string dflt = "",
                  unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(dflt) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getString());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setString((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    string tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) output.writeElement(getName(), tmp);
  }

  virtual size_t getSize(const Object* o) const {
    return (static_cast<const Cls*>(o)->*getf)().size();
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Default value */
  string def;
};

template <class Cls>
class MetaFieldStringRef : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(const string&);

  typedef const string& (Cls::*getFunction)(void) const;

  MetaFieldStringRef(const Keyword& n, getFunction getfunc,
                     setFunction setfunc = nullptr, string dflt = "",
                     unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(dflt) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getString());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setString((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    string tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) output.writeElement(getName(), tmp);
  }

  virtual size_t getSize(const Object* o) const {
    return (static_cast<const Cls*>(o)->*getf)().size();
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Default value */
  string def;
};

template <class Cls>
class MetaFieldCommand : public MetaFieldBase {
 public:
  typedef void (Cls::*cmdFunction)(const string&);

  MetaFieldCommand(const Keyword& n, cmdFunction cmdfunc = nullptr)
      : MetaFieldBase(n, DONT_SERIALIZE), cmdf(cmdfunc) {
    if (!cmdf) throw DataException("Command function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    (static_cast<Cls*>(me)->*cmdf)(el.getString());
  }

  virtual void getField(Object* me, DataValue& el) const {}

  virtual void writeField(Serializer& output) const {}

 protected:
  cmdFunction cmdf;
};

template <class Cls>
class MetaFieldBool : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(bool);

  typedef bool (Cls::*getFunction)(void) const;

  MetaFieldBool(const Keyword& n, getFunction getfunc,
                setFunction setfunc = nullptr, tribool d = BOOL_UNSET,
                unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getBool());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setBool((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    bool tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (def == BOOL_UNSET || (def == BOOL_TRUE && !tmp) ||
        (def == BOOL_FALSE && tmp))
      output.writeElement(getName(), tmp);
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Default value */
  tribool def;
};

template <class Cls>
class MetaFieldDouble : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(double);

  typedef double (Cls::*getFunction)(void) const;

  typedef bool (Cls::*isDefaultFunction)(void) const;

  MetaFieldDouble(const Keyword& n, getFunction getfunc,
                  setFunction setfunc = nullptr, double d = 0.0,
                  unsigned int c = BASE, isDefaultFunction dfltfunc = nullptr)
      : MetaFieldBase(n, c),
        getf(getfunc),
        setf(setfunc),
        def(d),
        isDfltFunc(dfltfunc) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getDouble());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setDouble((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    if (isDfltFunc) {
      if (!(static_cast<Cls*>(output.getCurrentObject())->*isDfltFunc)())
        output.writeElement(
            getName(), (static_cast<Cls*>(output.getCurrentObject())->*getf)());
    } else {
      double tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
      if (tmp != def) output.writeElement(getName(), tmp);
    }
  }

 protected:
  /* Get function. */
  getFunction getf = nullptr;

  /* Set function. */
  setFunction setf = nullptr;

  /* Default value. */
  double def;

  /* Set function. */
  isDefaultFunction isDfltFunc = nullptr;
};

template <class Cls>
class MetaFieldInt : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(int);

  typedef int (Cls::*getFunction)(void) const;

  MetaFieldInt(const Keyword& n, getFunction getfunc,
               setFunction setfunc = nullptr, int d = 0, unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getInt());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setInt((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    int tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) output.writeElement(getName(), tmp);
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Defaut value. */
  int def;
};

template <class Cls, class Enum>
class MetaFieldEnum : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(string);

  typedef Enum (Cls::*getFunction)(void) const;

  MetaFieldEnum(const Keyword& n, getFunction getfunc, setFunction setfunc,
                Enum d, unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getString());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setInt(static_cast<std::underlying_type_t<Enum>>(
        (static_cast<Cls*>(me)->*getf)()));
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    Enum tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def)
      output.writeElement(getName(),
                          static_cast<std::underlying_type_t<Enum>>(tmp));
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Defaut value. */
  Enum def;
};

template <class Cls>
class MetaFieldShort : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(short);

  typedef short (Cls::*getFunction)(void) const;

  MetaFieldShort(const Keyword& n, getFunction getfunc,
                 setFunction setfunc = nullptr, short d = 0,
                 unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getInt());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setInt((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    int tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) output.writeElement(getName(), tmp);
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Defaut value. */
  short def;
};

template <class Cls>
class MetaFieldUnsignedLong : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(unsigned long);

  typedef unsigned long (Cls::*getFunction)(void) const;

  MetaFieldUnsignedLong(const Keyword& n, getFunction getfunc,
                        setFunction setfunc = nullptr, unsigned long d = 0,
                        unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getUnsignedLong());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setUnsignedLong((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    unsigned long tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) output.writeElement(getName(), tmp);
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Defaut value. */
  unsigned long def;
};

template <class Cls>
class MetaFieldDuration : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(Duration);

  typedef Duration (Cls::*getFunction)(void) const;

  MetaFieldDuration(const Keyword& n, getFunction getfunc,
                    setFunction setfunc = nullptr, Duration d = 0L,
                    unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getDuration());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setDuration((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    Duration tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) output.writeElement(getName(), tmp);
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Default value. */
  Duration def;
};

template <class Cls>
class MetaFieldDurationDouble : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(double);

  typedef double (Cls::*getFunction)(void) const;

  MetaFieldDurationDouble(const Keyword& n, getFunction getfunc,
                          setFunction setfunc = nullptr, double d = 0,
                          unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(
        Duration::parse2double(el.getString().c_str()));
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setDouble((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    double tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) {
      char t[65];
      Duration::double2CharBuffer(tmp, t);
      output.writeElement(getName(), t);
    }
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Default value. */
  double def;
};

template <class Cls>
class MetaFieldDate : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(Date);

  typedef Date (Cls::*getFunction)(void) const;

  MetaFieldDate(const Keyword& n, getFunction getfunc,
                setFunction setfunc = nullptr, Date d = Date::infinitePast,
                unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc), def(d) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    if (cmd) cmd->addCommandSetField(me, this, el);
    (static_cast<Cls*>(me)->*setf)(el.getDate());
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setDate((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    Date tmp = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (tmp != def) output.writeElement(getName(), tmp);
  }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;

  /* Default value. */
  Date def;
};

template <class Cls, class Ptr>
class MetaFieldPointer : public MetaFieldBase {
 public:
  typedef void (Cls::*setFunction)(Ptr*);

  typedef Ptr* (Cls::*getFunction)(void) const;

  MetaFieldPointer(const Keyword& n, getFunction getfunc,
                   setFunction setfunc = nullptr, unsigned int c = BASE)
      : MetaFieldBase(n, c), getf(getfunc), setf(setfunc) {
    if (getfunc == nullptr)
      throw DataException("Getter function can't be nullptr");
  };

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {
    if (setf == nullptr) {
      ostringstream o;
      o << "Can't set field " << getName().getName() << " on class "
        << me->getType().type;
      throw DataException(o.str());
    }
    Object* obj = el.getObject();
    if (!obj || (obj && ((obj->getType().category &&
                          *(obj->getType().category) == *(Ptr::metadata)) ||
                         obj->getType() == *(Ptr::metadata)))) {
      // Matching type
      if (cmd) cmd->addCommandSetField(me, this, el);
      (static_cast<Cls*>(me)->*setf)(static_cast<Ptr*>(obj));
    } else {
      Ptr* obj2 = dynamic_cast<Ptr*>(obj);
      if (obj2) {
        // Dynamic cast: category is different, but they still have the same
        // base class.
        if (cmd) cmd->addCommandSetField(me, this, el);
        (static_cast<Cls*>(me)->*setf)(obj2);
      } else {
        // Wrong type
        ostringstream o;
        o << "Expecting value of type " << Ptr::metadata->type << " for field "
          << getName().getName() << " on class " << me->getType().type;
        throw DataException(o.str());
      }
    }
  }

  virtual void getField(Object* me, DataValue& el) const {
    el.setObject((static_cast<Cls*>(me)->*getf)());
  }

  virtual void writeField(Serializer& output) const {
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }
    // Imagine object A refers to object B. Both objects have fields
    // referring the other. When serializing object A, we also serialize
    // object B but we skip saving the reference back to A.
    Ptr* c = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    if (c && (output.getPreviousObject() != c)) {
      // Update the serialization mode
      // Unless specified otherwise we save a reference.
      bool tmp_force_base = false;
      if (getFlag(FORCE_BASE)) tmp_force_base = output.setForceBase(true);
      bool tmp_refs;
      if (output.getServiceMode())
        tmp_refs =
            output.setSaveReferences(!getFlag(WRITE_OBJECT_SVC + FORCE_BASE));
      else
        tmp_refs =
            output.setSaveReferences(!getFlag(WRITE_OBJECT_DFT + FORCE_BASE));
      bool tmp_hidden = false;
      if (getFlag(WRITE_HIDDEN)) tmp_hidden = output.setWriteHidden(true);

      // Write the object
      output.writeElement(getName(), c);

      // Restore the original serialization mode
      if (output.getServiceMode()) {
        if (!getFlag(WRITE_OBJECT_SVC + FORCE_BASE))
          output.setSaveReferences(tmp_refs);
      } else {
        if (!getFlag(WRITE_OBJECT_DFT + FORCE_BASE))
          output.setSaveReferences(tmp_refs);
      }
      if (getFlag(WRITE_HIDDEN)) output.setWriteHidden(tmp_hidden);
      if (getFlag(FORCE_BASE)) output.setForceBase(tmp_force_base);
    }
  }

  virtual bool isPointer() const { return true; }

  virtual const MetaClass* getClass() const { return Ptr::metadata; }

 protected:
  /* Get function. */
  getFunction getf;

  /* Set function. */
  setFunction setf;
};

template <class Cls>
class MetaFieldFunction : public MetaFieldBase {
 public:
  MetaFieldFunction(const Keyword& n, HandlerFunction f,
                    unsigned int c = DONT_SERIALIZE)
      : MetaFieldBase(n, c), thefunction(f) {};

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {}

  virtual HandlerFunction getFunction() const { return thefunction; }

  virtual void getField(Object* me, DataValue& el) const {}

  virtual void writeField(Serializer& output) const {}

 protected:
  HandlerFunction thefunction;
};

template <class Cls, class Iter, class PyIter, class Ptr>
class MetaFieldIterator : public MetaFieldBase {
 public:
  typedef Iter (Cls::*getFunction)(void) const;

  MetaFieldIterator(const Keyword& g, const Keyword& n,
                    getFunction getfunc = nullptr, unsigned int c = BASE)
      : MetaFieldBase(g, c), getf(getfunc), singleKeyword(n) {};

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {}

  virtual void getField(Object* me, DataValue& el) const {
    // This code is Python-specific. Only from Python can we call
    // this method. Not generic, but good enough...
    // TODO avoid calling the copy constructor here to improve performance!
    PyIter* o = new PyIter((static_cast<Cls*>(me)->*getf)());
    el.setObject(o);
  }

  virtual void writeField(Serializer& output) const {
    // Check whether this field matches the intended content detail
    switch (output.getContentType()) {
      case MANDATORY:
        if (!getFlag(MANDATORY)) return;
        break;
      case BASE:
        if (!getFlag(BASE) && !getFlag(MANDATORY)) return;
        break;
      case DETAIL:
        if (!getFlag(DETAIL)) return;
        break;
      case PLAN:
        if (!getFlag(PLAN)) return;
        break;
      default:
        break;
    }
    if (!getf) return;
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }

    // Update the serialization mode
    bool tmp_refs = false;
    bool tmp_hidden = false;
    bool tmp_force_base = false;
    if (getFlag(FORCE_BASE)) tmp_force_base = output.setForceBase(true);
    if (output.getServiceMode()) {
      if (getFlag(WRITE_OBJECT_SVC))
        tmp_refs = output.setSaveReferences(false);
      else if (getFlag(WRITE_REFERENCE_SVC))
        tmp_refs = output.setSaveReferences(true);
    } else {
      if (getFlag(WRITE_OBJECT_DFT))
        tmp_refs = output.setSaveReferences(false);
      else if (getFlag(WRITE_REFERENCE_DFT))
        tmp_refs = output.setSaveReferences(true);
    }
    if (getFlag(WRITE_HIDDEN)) tmp_hidden = output.setWriteHidden(true);

    // Write all objects
    bool first = true;
    Iter it = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    while (Ptr* ob = static_cast<Ptr*>(it.next())) {
      if (ob->getHidden() && !getFlag(WRITE_HIDDEN)) continue;
      if (first) {
        output.BeginList(getName());
        first = false;
      }
      output.writeElement(singleKeyword, ob, output.getContentType());
    }
    if (!first) output.EndList(getName());

    // Restore the original serialization mode
    if (output.getServiceMode()) {
      if (getFlag(WRITE_OBJECT_SVC))
        output.setSaveReferences(tmp_refs);
      else if (getFlag(WRITE_REFERENCE_SVC))
        output.setSaveReferences(tmp_refs);
    } else {
      if (getFlag(WRITE_OBJECT_DFT))
        output.setSaveReferences(tmp_refs);
      else if (getFlag(WRITE_REFERENCE_DFT))
        output.setSaveReferences(tmp_refs);
    }
    if (getFlag(WRITE_HIDDEN)) output.setWriteHidden(tmp_hidden);
    if (getFlag(FORCE_BASE)) output.setForceBase(tmp_force_base);
  }

  virtual bool isGroup() const { return true; }

  virtual const MetaClass* getClass() const { return Ptr::metadata; }

  virtual const Keyword* getKeyword() const { return &singleKeyword; }

 protected:
  /* Get function. */
  getFunction getf;

  const Keyword& singleKeyword;
};

template <class Cls, class Iter>
class MetaFieldIteratorClass : public MetaFieldBase {
 public:
  typedef Iter (Cls::*getFunction)(void) const;

  MetaFieldIteratorClass(const Keyword& g, const Keyword& n,
                         getFunction getfunc = nullptr, unsigned int c = BASE)
      : MetaFieldBase(g, c), getf(getfunc), singleKeyword(n) {};

  virtual void setField(Object* me, const DataValue& el,
                        CommandManager* cmd) const {}

  virtual void getField(Object* me, DataValue& el) const {
    // This code is Python-specific. Only from Python can we call
    // this method. Not generic, but good enough...
    auto tmp = new Iter((static_cast<Cls*>(me)->*getf)());
    el.setObject(tmp);
  }

  virtual void writeField(Serializer& output) const {
    // Check whether this field matches the intended content detail
    switch (output.getContentType()) {
      case MANDATORY:
        if (!getFlag(MANDATORY)) return;
        break;
      case BASE:
        if (!getFlag(BASE) && !getFlag(MANDATORY)) return;
        break;
      case DETAIL:
        if (!getFlag(DETAIL)) return;
        break;
      case PLAN:
        if (!getFlag(PLAN)) return;
        break;
      default:
        break;
    }
    if (!getf) return;
    if (output.getServiceMode()) {
      if (getFlag(DONT_SERIALIZE_SVC)) return;
    } else {
      if (getFlag(DONT_SERIALIZE_DFT)) return;
    }

    // Update the serialization mode
    bool tmp_refs = false;
    bool tmp_hidden = false;
    bool tmp_force_base = false;
    if (getFlag(FORCE_BASE)) tmp_force_base = output.setForceBase(true);
    if (output.getServiceMode()) {
      if (getFlag(WRITE_OBJECT_SVC))
        tmp_refs = output.setSaveReferences(false);
      else if (getFlag(WRITE_REFERENCE_SVC))
        tmp_refs = output.setSaveReferences(true);
    } else {
      if (getFlag(WRITE_OBJECT_DFT))
        tmp_refs = output.setSaveReferences(false);
      else if (getFlag(WRITE_REFERENCE_DFT))
        tmp_refs = output.setSaveReferences(true);
    }
    if (getFlag(WRITE_HIDDEN)) tmp_hidden = output.setWriteHidden(true);

    // Write all objects
    bool first = true;
    Iter it = (static_cast<Cls*>(output.getCurrentObject())->*getf)();
    while (Iter* ob = static_cast<Iter*>(it.next())) {
      if (first) {
        output.BeginList(getName());
        first = false;
      }
      output.writeElement(singleKeyword, ob, output.getContentType());
    }
    if (!first) output.EndList(getName());

    // Restore the original serialization mode
    if (output.getServiceMode()) {
      if (getFlag(WRITE_OBJECT_SVC))
        output.setSaveReferences(tmp_refs);
      else if (getFlag(WRITE_REFERENCE_SVC))
        output.setSaveReferences(tmp_refs);
    } else {
      if (getFlag(WRITE_OBJECT_DFT))
        output.setSaveReferences(tmp_refs);
      else if (getFlag(WRITE_REFERENCE_DFT))
        output.setSaveReferences(tmp_refs);
    }
    if (getFlag(WRITE_HIDDEN)) output.setWriteHidden(tmp_hidden);
    if (getFlag(FORCE_BASE)) output.setForceBase(tmp_force_base);
  }

  virtual bool isGroup() const { return true; }

  virtual const MetaClass* getClass() const { return Iter::metadata; }

  virtual const Keyword* getKeyword() const { return &singleKeyword; }

 protected:
  /* Get function. */
  getFunction getf;

  const Keyword& singleKeyword;
};

//
// LIBRARY INITIALISATION
//

/* This class holds functions that used for maintenance of the library.
 *
 * Its static member function 'initialize' should be called BEFORE the
 * first use of any class in the library.
 * The member function 'finialize' will be called automatically at the
 * end of the program.
 */
class LibraryUtils {
 public:
  static void initialize();
};

/* A template class to expose category classes which use a string
 * as the key to Python. */
template <class T>
class FreppleCategory : public PythonExtension<FreppleCategory<T>> {
 public:
  /* Initialization method. */
  static int initialize() {
    // Initialize the type
    auto& x = PythonExtension<FreppleCategory<T>>::getPythonType();
    x.setName(T::metadata->type);
    x.setDoc("frePPLe " + T::metadata->type);
    x.supportgetattro();
    x.supportsetattro();
    x.supportstr();
    x.supportcompare();
    x.supportcreate(Object::create<T>);
    T::metadata->setPythonClass(x);
    return x.typeReady();
  }
};

/* A template class to expose classes to Python. */
template <class ME, class BASE>
class FreppleClass : public PythonExtension<FreppleClass<ME, BASE>> {
 public:
  static int initialize() {
    // Initialize the type
    PythonType& x = PythonExtension<FreppleClass<ME, BASE>>::getPythonType();
    x.setName(ME::metadata->type);
    x.setDoc("frePPLe " + ME::metadata->type);
    x.supportgetattro();
    x.supportsetattro();
    x.supportstr();
    x.supportcompare();
    x.supportcreate(Object::create<ME>);
    x.setBase(BASE::metadata->pythonClass);
    x.addMethod("toXML", ME::toXML, METH_VARARGS,
                "return a XML representation");
    x.addMethod("toJSON", ME::toJSON, METH_VARARGS,
                "return a JSON representation");
    ME::metadata->setPythonClass(x);
    return x.typeReady();
  }
};

/* A class to remember the last N objects, and verify whether a certain
 * object is part of that list.
 * Internally we use a circular array data structure to store the recent
 * entries.
 */
template <class OBJ, int N>
class RecentlyUsed {
 private:
  OBJ entries[N];
  int head = 0;

 public:
  RecentlyUsed() {}

  RecentlyUsed(const RecentlyUsed& o) : head(o.head) {
    for (int i = 0; i < head && i < N; ++i) entries[i] = o.entries[i];
  }

  RecentlyUsed& operator=(const RecentlyUsed& o) {
    head = o.head;
    for (int i = 0; i < head && i < N; ++i) entries[i] = o.entries[i];
    return *this;
  }

  /* Add a new entry to the list. */
  void push(const OBJ& o) {
    entries[head >= N ? head - N : head] = o;
    if (++head > 2 * N) head = N;
  }

  bool contains(const OBJ& o) const {
    for (int i = 0; i < head; ++i)
      if (entries[i] == o) return true;
    return false;
  }

  int size() const { return head > N ? N : head; }

  void clear() { head = 0; }

  void echoSince(ostream& out, const OBJ& o) const {
    bool first = true;
    for (int i = (head > N) ? (head - N - 1) : (head - 1); i >= 0; --i) {
      if (first)
        first = false;
      else
        out << ", ";
      out << entries[i];
      if (entries[i] == o) return;
    }
    if (head > N)
      for (int i = N - 1; i >= head - N; --i) {
        out << ", " << entries[i];
        if (entries[i] == o) return;
      }
  }
};

/* Memory allocation for small objects in pages.
 * Properties:
 * - The pool object needs to be declared as thread_local to assure things work
 *   in a multithreaded environment. Each thread maintains its own pool of
 *   objects.
 * - Each memory page allocates 2MB of memory.
 * - Pages in the pool are automatically added when needed.
 * - Pages in the pool are automatically destructed when the thread exits.
 *   We assume that all pool objects are then no longer referenced and can be
 *   deleted.
 */
template <class T>
class MemoryPool {
 private:
  class MemoryObject {
   public:
    T val;
    MemoryObject* prev;
    MemoryObject* next;
  };

 public:
  class MemoryObjectList {
   private:
    inline void append(MemoryObject* n) {
      n->next = nullptr;
      n->prev = last;
      if (last)
        last->next = n;
      else
        first = n;
      last = n;
    }

   public:
    MemoryObject* first = nullptr;
    MemoryObject* last = nullptr;
    MemoryPool& pool;

    MemoryObjectList(MemoryPool& m) : pool(m) {}

    MemoryObjectList(const MemoryObjectList& other) : pool(other.pool) {
      for (auto i = other.begin(); i != other.end(); ++i) insert(&*i);
    }

    MemoryObjectList& operator=(const MemoryObjectList& other) {
      while (first) {
        auto tmp = first;
        first = first->next;
        pool.addToFree(tmp);
      }
      last = nullptr;
      pool = other.pool;
      for (auto i = other.begin(); i != other.end(); ++i) insert(&*i);
      return *this;
    }

    ~MemoryObjectList() {
      while (first) {
        auto tmp = first;
        first = first->next;
        pool.addToFree(tmp);
      }
    }

    T& back() const { return last->val; }

    T& front() const { return first->val; }

    bool empty() const { return first == nullptr; }

    void pop_front() {
      if (first) {
        auto tmp = first;
        first = first->next;
        if (first)
          first->prev = nullptr;
        else
          last = nullptr;
        pool.addToFree(tmp);
      }
    }

    void pop_back() {
      if (last) {
        auto tmp = last;
        last = last->prev;
        if (last)
          last->next = nullptr;
        else
          first = nullptr;
        pool.addToFree(tmp);
      }
    }

    void sort() {
      // Bubble sort
      bool ok;
      do {
        ok = true;
        for (auto p = first; p && p->next; p = p->next) {
          if (*p->next < *p) {
            swap(p->val, p->next->val);
            ok = false;
          };
        }
      } while (!ok);
    }

    inline void insert(const T* t) {
      auto n = pool.alloc();
      new (&(n->val)) T(*t);
      append(n);
    }

    template <typename T1>
    inline void insert(T1& t1) {
      auto n = pool.alloc();
      new (&(n->val)) T(t1);
      append(n);
    }

    template <typename T1, typename T2>
    inline void insert(T1 t1, T2 t2) {
      auto n = pool.alloc();
      new (&(n->val)) T(t1, t2);
      append(n);
    }

    template <typename T1, typename T2, typename T3>
    inline void insert(T1 t1, T2 t2, T3 t3) {
      auto n = pool.alloc();
      new (&(n->val)) T(t1, t2, t3);
      append(n);
    }

    template <typename T1, typename T2, typename T3, typename T4>
    inline void insert(T1 t1, T2 t2, T3 t3, T4 t4) {
      auto n = pool.alloc();
      new (&(n->val)) T(t1, t2, t3, t4);
      append(n);
    }

    template <typename T1, typename T2, typename T3, typename T4, typename T5>
    inline void insert(T1 t1, T2 t2, T3 t3, T4 t4, T5 t5) {
      auto n = pool.alloc();
      new (&(n->val)) T(t1, t2, t3, t4, t5);
      append(n);
    }

    template <typename T1, typename T2, typename T3, typename T4, typename T5,
              typename T6>
    inline void insert(T1 t1, T2 t2, T3 t3, T4 t4, T5 t5, T6 t6) {
      auto n = pool.alloc();
      new (&(n->val)) T(t1, t2, t3, t4, t5, t6);
      append(n);
    }

    // void erase(T&) {
    // for (auto p = first; p; p = p->next)
    //   if (p->msr == k) {
    //     // Unlink from the list
    //     if (p->prev)
    //       p->prev->next = p->next;
    //     else
    //       first = p->next;
    //     if (p->next)
    //       p->next->prev = p->prev;
    //     else
    //       last = p->prev;

    //     // Add to free list
    //     p->addToFree();
    //     return;
    //   }
    //}

    // void MeasureList::erase(MeasureValue* p) {
    //   // Unlink from the list
    //   if (p->prev)
    //     p->prev->next = p->next;
    //   else
    //     first = p->next;
    //   if (p->next)
    //     p->next->prev = p->prev;
    //   else
    //     last = p->prev;

    //   // Add to free list
    //   p->addToFree();
    // }

    class iterator {
     private:
      MemoryObject* ptr = nullptr;

     public:
      iterator(MemoryObject* i) : ptr(i) {}

      iterator& operator++() {
        if (ptr) ptr = ptr->next;
        return *this;
      }

      bool operator!=(const iterator& t) const { return ptr != t.ptr; }

      bool operator==(const iterator& t) const { return ptr == t.ptr; }

      T& operator*() { return ptr->val; }

      T* operator->() { return &(ptr->val); }
    };

    iterator begin() const { return iterator(first); }

    iterator end() const { return iterator(nullptr); }
  };

 private:
  class MemoryPage {
   public:
    static const int DATA_PER_PAGE = 2 * 1024 * 1024 / sizeof(MemoryObject);
    MemoryPage* next = nullptr;
    MemoryPage* prev = nullptr;
    MemoryObject data[DATA_PER_PAGE];

    MemoryPage(MemoryPool& pool) : next(nullptr) {
      // Insert into page list
      if (pool.lastpage) {
        prev = pool.lastpage;
        pool.lastpage->next = this;
      } else {
        pool.firstpage = this;
        prev = nullptr;
      }
      pool.lastpage = this;

      // Extend the list of free pairs
      for (auto& v : data) pool.addToFree(&v);
    }
  };

  MemoryPage* firstpage = nullptr;
  MemoryPage* lastpage = nullptr;
  MemoryObject* firstfree = nullptr;
  MemoryObject* lastfree = nullptr;

  void addToFree(MemoryObject* o) {
    o->prev = lastfree;
    o->next = nullptr;
    if (lastfree)
      lastfree->next = o;
    else
      firstfree = o;
    lastfree = o;
  }

  MemoryObject* alloc() {
    // Get a free pair
    if (!firstfree) {
      new MemoryPage(*this);
      if (!firstfree) throw RuntimeException("No free memory");
    }
    auto n = firstfree;
    firstfree = firstfree->next;
    if (firstfree)
      firstfree->prev = nullptr;
    else
      lastfree = nullptr;
    return n;
  }

 public:
  MemoryPool() {}

  ~MemoryPool() {
    unsigned int cnt = 0;
    while (firstpage) {
      ++cnt;
      auto tmp = firstpage;
      firstpage = firstpage->next;
      delete tmp;
    }
  }
};

}  // namespace utils
}  // namespace frepple

#endif  // End of FREPPLE_UTILS_H
