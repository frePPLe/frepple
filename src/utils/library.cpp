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

// These headers are required for the loading of dynamic libraries and the
// detection of the number of cores.
#ifdef WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#include <unistd.h>
#endif

#include <sys/stat.h>

#include "frepple/utils.h"
#include "frepple/xml.h"
#ifdef HAVE_SYS_PRCTL_H
#include <sys/prctl.h>
#endif

namespace frepple {
namespace utils {

// Static stringpool table
set<string> PooledString::pool;
mutex PooledString::pool_lock;
const PooledString PooledString::emptystring;
const string PooledString::nullstring;
const char PooledString::nullchar = '\0';

// Repository of all categories and commands
const MetaCategory* MetaCategory::firstCategory = nullptr;
MetaCategory::CategoryMap MetaCategory::categoriesByTag;
MetaCategory::CategoryMap MetaCategory::categoriesByGroupTag;

const MetaCategory* Object::metadata = nullptr;

// Number of processors.
// The value initialized here is updated when the getProcessorCores function
// is called the first time.
int Environment::processorcores = -1;

// Output logging stream, whose input buffer is shared with either
// Environment::logfile or cout.
ostream logger(cout.rdbuf());

// Output file stream
StreambufWrapper Environment::logfile;

// Name of the log file
string Environment::logfilename;

// Hash value computed only once
const size_t MetaCategory::defaultHash(Keyword::hash("default"));

vector<PythonType*> Object::table;

void LibraryUtils::initialize() {
  // Initialize only once
  static bool init = false;
  if (init) {
    logger << "Warning: Calling frepple::LibraryUtils::initialize() more "
           << "than once." << endl;
    return;
  }
  init = true;

  // Set the process name
  Environment::setProcessName();

  // Initialize Xerces parser
  xercesc::XMLPlatformUtils::Initialize();
  PythonInterpreter::initialize();
  if (CommandManager::initialize())
    throw RuntimeException("Error registering command manager");
}

string Environment::searchFile(const string filename) {
#ifdef _MSC_VER
  static char pathseperator = '\\';
#else
  static char pathseperator = '/';
#endif

  // First: check the current directory
  struct stat stat_p;
  int result = stat(filename.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD)) return filename;

  // Second: check the FREPPLE_HOME directory, if it is defined
  string fullname;
  char* envvar = getenv("FREPPLE_HOME");
  if (envvar) {
    fullname = envvar;
    if (*fullname.rbegin() != pathseperator) fullname += pathseperator;
    fullname += filename;
    result = stat(fullname.c_str(), &stat_p);
    if (!result && (stat_p.st_mode & S_IREAD)) return fullname;
  }

#ifdef DATADIRECTORY
  // Third: check the data directory
  fullname = DATADIRECTORY;
  if (*fullname.rbegin() != pathseperator) fullname += pathseperator;
  fullname.append(filename);
  result = stat(fullname.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD)) return fullname;
#endif

#ifdef LIBDIRECTORY
  // Fourth: check the lib directory
  fullname = LIBDIRECTORY;
  if (*fullname.rbegin() != pathseperator) fullname += pathseperator;
  fullname += "frepple";
  fullname += pathseperator;
  fullname += filename;
  result = stat(fullname.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD)) return fullname;
#endif

#ifdef SYSCONFDIRECTORY
  // Fifth: check the sysconf directory
  fullname = SYSCONFDIRECTORY;
  if (*fullname.rbegin() != pathseperator) fullname += pathseperator;
  fullname += filename;
  result = stat(fullname.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD)) return fullname;
#endif

  // Not found
  return "";
}

int Environment::getProcessorCores() {
  // Previously detected already
  if (processorcores >= 1) return processorcores;

  char* envvar = getenv("FREPPLE_CPU");
  if (envvar)
    // Environment variable overrides the default (if it is a valid number)
    processorcores = atoi(envvar);
  if (processorcores < 0)
    // Autodetect the number of cores on your machine
    processorcores = thread::hardware_concurrency();
  if (processorcores < 1) processorcores = 1;
  return processorcores;
}

void StreambufWrapper::setLogLimit(unsigned long long i) {
  if (!max_size) {
    start_size = Environment::getLogFileSize();
    cur_size = 0;
  }
  max_size = i;
}

int StreambufWrapper::sync() {
  if (max_size && ++cur_size > max_size) {
    cur_size = 0;
    auto r = filebuf::sync();
    Environment::truncateLogFile(start_size);
    logger << "\nTruncated some output here...\n" << endl;
    return r;
  } else
    return filebuf::sync();
}

void Environment::setLogFile(const string& x) {
  // Bye bye message
  if (!logfilename.empty()) logger << "Stop logging at " << Date::now() << endl;

  // Close an eventual existing log file.
  if (logfile.is_open()) logfile.close();

  // No new logfile specified: redirect to the standard output stream
  if (x.empty() || x == "+") {
    logfilename = x;
    logger.rdbuf(cout.rdbuf());
    return;
  }

  // Open the file: either as a new file, either appending to existing file
  if (x[0] == '+')
    throw RuntimeException("Appending to a log file is no longer supported");
  auto status = logfile.open(x.c_str(), ios::out);
  if (!status) {
    // Redirect to the previous logfile (or cout if that's not possible)
    if (logfile.is_open()) logfile.close();
    status = logfile.open(logfilename.c_str(), ios::app);
    if (status)
      logger.rdbuf(&logfile);
    else
      logger.rdbuf(cout.rdbuf());
    // The log file could not be opened
    throw RuntimeException("Could not open log file '" + x + "'");
  }

  // Store the file name
  logfilename = x;

  // Redirect the log file.
  logger.rdbuf(&logfile);

  // Print a nice header
  logger << "Start logging frePPLe " << PACKAGE_VERSION << " (" << __DATE__
         << ") at " << Date::now() << endl;
}

void Environment::truncateLogFile(unsigned long long sz) {
  if (logfilename.empty()) return;

  // Close an eventual existing log file.
  if (logfile.is_open()) logfile.close();

#ifdef HAVE_TRUNCATE
  // Resize the file
  if (truncate(logfilename.c_str(), sz))
    logger << "Error: Failed to truncate log file" << endl;
#else
#error "This platform doesn't have a file resizing api."
#endif

  // Reopen the file
  logfile.open(logfilename.c_str(), ios::app);
}

unsigned long Environment::getLogFileSize() {
  if (logfilename.empty()) return 0;
  struct stat statbuf;
  auto f = stat(logfilename.c_str(), &statbuf);
  return f != -1 ? statbuf.st_size : 0;
}

void Environment::setProcessName() {
#ifdef HAVE_PRCTL
  char* envvar = getenv("FREPPLE_PROCESSNAME");
  if (envvar) {
    string nm = "frepple ";
    nm += envvar;
    prctl(PR_SET_NAME, nm.c_str());
  }
#endif
}

void MetaClass::addClass(const string& a, const string& b, bool def,
                         creatorDefault f) {
  // Find or create the category
  MetaCategory* cat =
      const_cast<MetaCategory*>(MetaCategory::findCategoryByTag(a.c_str()));

  // Check for a valid category
  if (!cat)
    throw LogicException("Category " + a +
                         " not found when registering class " + b);

  // Update fields
  type = b.empty() ? "unspecified" : b;
  typetag = &Keyword::find(type.c_str());
  category = cat;

  // Update the metadata table
  cat->classes[Keyword::hash(b)] = this;

  // Register this tag also as the default one, if requested
  if (isDefault) cat->classes[Keyword::hash("default")] = this;

  // Set method pointers to nullptr
  factoryMethod = f;
}

MetaCategory::MetaCategory(const string& a, const string& gr, size_t sz,
                           readController f, findController s) {
  // Update registry
  if (!a.empty()) categoriesByTag[Keyword::hash(a)] = this;
  if (!gr.empty()) categoriesByGroupTag[Keyword::hash(gr)] = this;

  // Update fields
  size = sz;
  readFunction = f;
  findFunction = s;
  type = a.empty() ? "unspecified" : a;
  typetag = &Keyword::find(type.c_str());
  group = gr.empty() ? "unspecified" : gr;
  grouptag = &Keyword::find(group.c_str());

  // Maintain a linked list of all registered categories
  nextCategory = nullptr;
  if (!firstCategory)
    firstCategory = this;
  else {
    const MetaCategory* i = firstCategory;
    while (i->nextCategory) i = i->nextCategory;
    const_cast<MetaCategory*>(i)->nextCategory = this;
  }
}

const MetaCategory* MetaCategory::findCategoryByTag(const char* c) {
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByTag.find(Keyword::hash(c));
  return (i != categoriesByTag.end()) ? i->second : nullptr;
}

const MetaCategory* MetaCategory::findCategoryByTag(const size_t h) {
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByTag.find(h);
  return (i != categoriesByTag.end()) ? i->second : nullptr;
}

const MetaCategory* MetaCategory::findCategoryByGroupTag(const char* c) {
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(Keyword::hash(c));
  return (i != categoriesByGroupTag.end()) ? i->second : nullptr;
}

const MetaCategory* MetaCategory::findCategoryByGroupTag(const size_t h) {
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(h);
  return (i != categoriesByGroupTag.end()) ? i->second : nullptr;
}

const MetaClass* MetaCategory::findClass(const char* c) const {
  // Look up in the registered classes
  MetaCategory::ClassMap::const_iterator j = classes.find(Keyword::hash(c));
  return (j == classes.end()) ? nullptr : j->second;
}

const MetaClass* MetaCategory::findClass(const size_t h) const {
  // Look up in the registered classes
  auto j = classes.find(h);
  return (j == classes.end()) ? nullptr : j->second;
}

const MetaClass* MetaClass::findClass(const char* c) {
  for (auto i : MetaCategory::categoriesByTag) {
    auto j = i.second->classes.find(Keyword::hash(c));
    if (j != i.second->classes.end()) return j->second;
  }
  return nullptr;
}

const MetaClass* MetaClass::findClass(PyObject* pytype) {
  for (auto i : MetaCategory::categoriesByTag)
    for (auto& j : i.second->classes)
      if ((PyObject*)(j.second->pythonClass) == pytype) return j.second;
  return nullptr;
}

void MetaClass::printClasses() {
  logger << "Registered classes:" << endl;
  // Loop through all categories
  for (auto i = MetaCategory::categoriesByTag.begin();
       i != MetaCategory::categoriesByTag.end(); ++i) {
    logger << "  " << i->second->type << endl;
    // Loop through the classes for the category
    for (auto j = i->second->classes.begin(); j != i->second->classes.end();
         ++j)
      if (j->first == Keyword::hash("default"))
        logger << "    default ( = " << j->second->type << " )" << j->second
               << endl;
      else
        logger << "    " << j->second->type << j->second << endl;
  }
}

const MetaFieldBase* MetaClass::findField(const Keyword& key) const {
  for (auto i = fields.begin(); i != fields.end(); ++i)
    if ((*i)->getName() == key) return *i;
  return nullptr;
}

const MetaFieldBase* MetaClass::findField(size_t h) const {
  for (auto i = fields.begin(); i != fields.end(); ++i)
    if ((*i)->getHash() == h) return *i;
  return nullptr;
}

Action MetaClass::decodeAction(const char* x) {
  // Validate the action
  if (!x)
    throw LogicException("Invalid action nullptr");
  else if (!strcmp(x, "AC"))
    return Action::ADD_CHANGE;
  else if (!strcmp(x, "A"))
    return Action::ADD;
  else if (!strcmp(x, "C"))
    return Action::CHANGE;
  else if (!strcmp(x, "R"))
    return Action::REMOVE;
  else
    throw DataException("Invalid action '" + string(x) + "'");
}

Action MetaClass::decodeAction(const DataValueDict& atts) {
  // Decode the string and return the default in the absence of the attribute
  const DataValue* c = atts.get(Tags::action);
  return c ? decodeAction(c->getString().c_str()) : Action::ADD_CHANGE;
}

bool MetaClass::raiseEvent(Object* v, Signal a) const {
  bool result(true);
  for (auto i = subscribers[a].begin(); i != subscribers[a].end(); ++i)
    // Note that we always call all subscribers, even if one or more
    // already replied negatively. However, an exception thrown from a
    // callback method will break the publishing chain.
    if (!(*i)->callback(v, a)) result = false;

  // Raise the event also on the category, if there is a valid one
  return (category && category != this) ? (result && category->raiseEvent(v, a))
                                        : result;
}

Object* MetaCategory::ControllerDefault(const MetaClass* cat,
                                        const DataValueDict& in,
                                        CommandManager* mgr) {
  Action act = MetaClass::decodeAction(in);
  switch (act) {
    case Action::REMOVE:
      throw DataException("Entity " + cat->type +
                          " doesn't support REMOVE action");
    case Action::CHANGE:
      throw DataException("Entity " + cat->type +
                          " doesn't support CHANGE action");
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

      // Report the creation to the manager
      if (mgr) mgr->add(new CommandCreateObject(result));

      // Creation accepted
      return result;
  }
  throw LogicException("Unreachable code reached");
  return nullptr;
}

}  // namespace utils
}  // namespace frepple
