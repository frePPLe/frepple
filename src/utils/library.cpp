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

#define FREPPLE_CORE
#include "frepple/utils.h"
#include "frepple/xml.h"
#include <sys/stat.h>

// These headers are required for the loading of dynamic libraries and the
// detection of the number of cores.
#ifdef WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#include <unistd.h>
#endif


namespace frepple
{
namespace utils
{

// Static stringpool table
PooledString::pool_type PooledString::pool;
string PooledString::nullstring;

// Repository of all categories and commands
const MetaCategory* MetaCategory::firstCategory = nullptr;
MetaCategory::CategoryMap MetaCategory::categoriesByTag;
MetaCategory::CategoryMap MetaCategory::categoriesByGroupTag;

const MetaCategory* Object::metadata = nullptr;

// Repository of loaded modules
set<string> Environment::moduleRegistry;

// Number of processors.
// The value initialized here is updated when the getProcessorCores function
// is called the first time.
int Environment::processorcores = -1;

// Output logging stream, whose input buffer is shared with either
// Environment::logfile or cout.
ostream logger(cout.rdbuf());

// Output file stream
ofstream Environment::logfile;

// Name of the log file
string Environment::logfilename;

// Hash value computed only once
const hashtype MetaCategory::defaultHash(Keyword::hash("default"));

vector<PythonType*> Object::table;


void LibraryUtils::initialize()
{
  // Initialize only once
  static bool init = false;
  if (init)
  {
    logger << "Warning: Calling frepple::LibraryUtils::initialize() more "
        << "than once." << endl;
    return;
  }
  init = true;

  // Initialize Xerces parser
  xercesc::XMLPlatformUtils::Initialize();

  // Initialize the Python interpreter
  PythonInterpreter::initialize();

  // Register new methods in Python
  PythonInterpreter::registerGlobalMethod(
    "loadmodule", loadModule, METH_VARARGS,
    "Dynamically load a module in memory.");
}


string Environment::searchFile(const string filename)
{
#ifdef _MSC_VER
  static char pathseperator = '\\';
#else
  static char pathseperator = '/';
#endif

  // First: check the current directory
  struct stat stat_p;
  int result = stat(filename.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD))
    return filename;

  // Second: check the FREPPLE_HOME directory, if it is defined
  string fullname;
  char * envvar = getenv("FREPPLE_HOME");
  if (envvar)
  {
    fullname = envvar;
    if (*fullname.rbegin() != pathseperator)
      fullname += pathseperator;
    fullname += filename;
    result = stat(fullname.c_str(), &stat_p);
    if (!result && (stat_p.st_mode & S_IREAD))
      return fullname;
  }

#ifdef DATADIRECTORY
  // Third: check the data directory
  fullname = DATADIRECTORY;
  if (*fullname.rbegin() != pathseperator)
    fullname += pathseperator;
  fullname.append(filename);
  result = stat(fullname.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD))
    return fullname;
#endif

#ifdef LIBDIRECTORY
  // Fourth: check the lib directory
  fullname = LIBDIRECTORY;
  if (*fullname.rbegin() != pathseperator)
    fullname += pathseperator;
  fullname += "frepple";
  fullname += pathseperator;
  fullname += filename;
  result = stat(fullname.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD))
    return fullname;
#endif

#ifdef SYSCONFDIRECTORY
  // Fifth: check the sysconf directory
  fullname = SYSCONFDIRECTORY;
  if (*fullname.rbegin() != pathseperator)
    fullname += pathseperator;
  fullname += filename;
  result = stat(fullname.c_str(), &stat_p);
  if (!result && (stat_p.st_mode & S_IREAD))
    return fullname;
#endif

  // Not found
  return "";
}


int Environment::getProcessorCores()
{
  // Previously detected already
  if (processorcores >= 1) return processorcores;

  char *envvar = getenv("FREPPLE_CPU");
  if (envvar)
    // Environment variable overrides the default (if it is a valid number)
    processorcores = atoi(envvar);
  if (processorcores < 0)
    // Autodetect the number of cores on your machine
    processorcores = thread::hardware_concurrency();
  if (processorcores < 1)
    processorcores = 1;
  return processorcores;
}


void Environment::setLogFile(const string& x)
{
  // Bye bye message
  if (!logfilename.empty())
    logger << "Stop logging at " << Date::now() << endl;

  // Close an eventual existing log file.
  if (logfile.is_open()) logfile.close();

  // No new logfile specified: redirect to the standard output stream
  if (x.empty() || x == "+")
  {
    logfilename = x;
    logger.rdbuf(cout.rdbuf());
    return;
  }

  // Open the file: either as a new file, either appending to existing file
  if (x[0] != '+') logfile.open(x.c_str(), ios::out);
  else logfile.open(x.c_str()+1, ios::app);
  if (!logfile.good())
  {
    // Redirect to the previous logfile (or cout if that's not possible)
    if (logfile.is_open()) logfile.close();
    logfile.open(logfilename.c_str(), ios::app);
    logger.rdbuf(logfile.is_open() ? logfile.rdbuf() : cout.rdbuf());
    // The log file could not be opened
    throw RuntimeException("Could not open log file '" + x + "'");
  }

  // Store the file name
  logfilename = x;

  // Redirect the log file.
  logger.rdbuf(logfile.rdbuf());

  // Print a nice header
  logger << "Start logging frePPLe " << PACKAGE_VERSION << " ("
      << __DATE__ << ") at " << Date::now() << endl;
}


void Environment::loadModule(string lib)
{
  // Type definition of the initialization function
  typedef const char* (*func)();

  // Validate
  if (lib.empty())
    throw DataException("Error: No library name specified for loading");

#ifdef WIN32
  // Load the library - The windows way

  // Change the error mode: we handle errors now, not the operating system
  UINT em = SetErrorMode(SEM_FAILCRITICALERRORS);
  HINSTANCE handle = LoadLibraryEx(lib.c_str(),nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
  if (!handle) handle = LoadLibraryEx(lib.c_str(), nullptr, 0);
  if (!handle)
  {
    // Get the error description
    char error[256];
    FormatMessage(
      FORMAT_MESSAGE_IGNORE_INSERTS | FORMAT_MESSAGE_FROM_SYSTEM,
      nullptr,
      GetLastError(),
      0,
      error,
      256,
      nullptr );
    throw RuntimeException(error);
  }
  SetErrorMode(em);  // Restore the previous error mode

  // Find the initialization routine
  func inithandle =
    reinterpret_cast<func>(GetProcAddress(HMODULE(handle), "initialize"));
  if (!inithandle)
  {
    // Get the error description
    char error[256];
    FormatMessage(
      FORMAT_MESSAGE_IGNORE_INSERTS | FORMAT_MESSAGE_FROM_SYSTEM,
      nullptr,
      GetLastError(),
      0,
      error,
      256,
      nullptr );
    throw RuntimeException(error);
  }

#else
  // Load the library - The UNIX way

  // Search the frePPLe directories for the library
  string fullpath = Environment::searchFile(lib);
  if (fullpath.empty())
    throw RuntimeException("Module '" + lib + "' not found");
  dlerror(); // Clear the previous error
  void *handle = dlopen(fullpath.c_str(), RTLD_NOW | RTLD_GLOBAL);
  const char *err = dlerror();  // Pick up the error string
  if (err)
  {
    // Search the normal path for the library
    dlerror(); // Clear the previous error
    handle = dlopen(lib.c_str(), RTLD_NOW | RTLD_GLOBAL);
    err = dlerror();  // Pick up the error string
    if (err) throw RuntimeException(err);
  }

  // Find the initialization routine
  func inithandle = (func)(dlsym(handle, "initialize"));
  err = dlerror(); // Pick up the error string
  if (err) throw RuntimeException(err);
#endif

  // Call the initialization routine with the parameter list
  string x = (inithandle)();
  if (x.empty()) throw DataException("Invalid module");

  // Insert the new module in the registry
  moduleRegistry.insert(x);
}


void MetaClass::addClass (const string& a, const string& b,
    bool def, creatorDefault f)
{
  // Find or create the category
  MetaCategory* cat
    = const_cast<MetaCategory*>(MetaCategory::findCategoryByTag(a.c_str()));

  // Check for a valid category
  if (!cat)
    throw LogicException("Category " + a
        + " not found when registering class " + b);

  // Update fields
  type = b.empty() ? "unspecified" : b;
  typetag = &Keyword::find(type.c_str());
  category = cat;

  // Update the metadata table
  cat->classes[Keyword::hash(b)] = this;

  // Register this tag also as the default one, if requested
  if (isDefault)
    cat->classes[Keyword::hash("default")] = this;

  // Set method pointers to nullptr
  factoryMethod = f;
}


MetaCategory::MetaCategory (const string& a, const string& gr,
    size_t sz, readController f, findController s)
{
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
  else
  {
    const MetaCategory *i = firstCategory;
    while (i->nextCategory) i = i->nextCategory;
    const_cast<MetaCategory*>(i)->nextCategory = this;
  }
}


const MetaCategory* MetaCategory::findCategoryByTag(const char* c)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByTag.find(Keyword::hash(c));
  return (i!=categoriesByTag.end()) ? i->second : nullptr;
}


const MetaCategory* MetaCategory::findCategoryByTag(const hashtype h)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByTag.find(h);
  return (i!=categoriesByTag.end()) ? i->second : nullptr;
}


const MetaCategory* MetaCategory::findCategoryByGroupTag(const char* c)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(Keyword::hash(c));
  return (i!=categoriesByGroupTag.end()) ? i->second : nullptr;
}


const MetaCategory* MetaCategory::findCategoryByGroupTag(const hashtype h)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(h);
  return (i!=categoriesByGroupTag.end()) ? i->second : nullptr;
}


const MetaClass* MetaCategory::findClass(const char* c) const
{
  // Look up in the registered classes
  MetaCategory::ClassMap::const_iterator j = classes.find(Keyword::hash(c));
  return (j == classes.end()) ? nullptr : j->second;
}


const MetaClass* MetaCategory::findClass(const hashtype h) const
{
  // Look up in the registered classes
  MetaCategory::ClassMap::const_iterator j = classes.find(h);
  return (j == classes.end()) ? nullptr : j->second;
}


const MetaClass* MetaClass::findClass(const char* c)
{
  // Loop through all categories
  for (MetaCategory::CategoryMap::const_iterator i = MetaCategory::categoriesByTag.begin();
      i != MetaCategory::categoriesByTag.end(); ++i)
  {
    // Look up in the registered classes
    MetaCategory::ClassMap::const_iterator j
      = i->second->classes.find(Keyword::hash(c));
    if (j != i->second->classes.end()) return j->second;
  }
  // Not found...
  return nullptr;
}


void MetaClass::printClasses()
{
  logger << "Registered classes:" << endl;
  // Loop through all categories
  for (MetaCategory::CategoryMap::const_iterator i = MetaCategory::categoriesByTag.begin();
      i != MetaCategory::categoriesByTag.end(); ++i)
  {
    logger << "  " << i->second->type << endl;
    // Loop through the classes for the category
    for (MetaCategory::ClassMap::const_iterator
        j = i->second->classes.begin();
        j != i->second->classes.end();
        ++j)
      if (j->first == Keyword::hash("default"))
        logger << "    default ( = " << j->second->type << " )" << j->second << endl;
      else
        logger << "    " << j->second->type << j->second << endl;
  }
}


const MetaFieldBase* MetaClass::findField(const Keyword& key) const
{
  for (fieldlist::const_iterator i = fields.begin(); i != fields.end(); ++i)
    if ((*i)->getName() == key)
      return *i;
  return nullptr;
}


const MetaFieldBase* MetaClass::findField(hashtype h) const
{
  for (fieldlist::const_iterator i = fields.begin(); i != fields.end(); ++i)
    if ((*i)->getHash() == h)
      return *i;
  return nullptr;
}


Action MetaClass::decodeAction(const char *x)
{
  // Validate the action
  if (!x)
    throw LogicException("Invalid action nullptr");
  else if (!strcmp(x, "AC"))
    return ADD_CHANGE;
  else if (!strcmp(x, "A"))
    return ADD;
  else if (!strcmp(x, "C"))
    return CHANGE;
  else if (!strcmp(x, "R"))
    return REMOVE;
  else
    throw DataException("Invalid action '" + string(x) + "'");
}


Action MetaClass::decodeAction(const DataValueDict& atts)
{
  // Decode the string and return the default in the absence of the attribute
  const DataValue* c = atts.get(Tags::action);
  return c ? decodeAction(c->getString().c_str()) : ADD_CHANGE;
}


bool MetaClass::raiseEvent(Object* v, Signal a) const
{
  bool result(true);
  for (list<Functor*>::const_iterator i = subscribers[a].begin();
      i != subscribers[a].end(); ++i)
    // Note that we always call all subscribers, even if one or more
    // already replied negatively. However, an exception thrown from a
    // callback method will break the publishing chain.
    if (!(*i)->callback(v,a)) result = false;

  // Raise the event also on the category, if there is a valid one
  return (category && category!=this) ?
      (result && category->raiseEvent(v,a)) :
      result;
}


Object* MetaCategory::ControllerDefault (
  const MetaClass* cat, const DataValueDict& in, CommandManager* mgr
  )
{
  Action act = MetaClass::decodeAction(in);
  switch (act)
  {
    case REMOVE:
      throw DataException
      ("Entity " + cat->type + " doesn't support REMOVE action");
    case CHANGE:
      throw DataException
      ("Entity " + cat->type + " doesn't support CHANGE action");
    default:
      /* Lookup the class in the map of registered classes. */
      const MetaClass* j;
      if (cat->category)
        // Class metadata passed: we already know what type to create
        j = cat;
      else
      {
        // Category metadata passed: we need to look up the type
        const DataValue* type = in.get(Tags::type);
        j = static_cast<const MetaCategory&>(*cat).findClass(
          type ? Keyword::hash(type->getString()) : MetaCategory::defaultHash
          );
        if (!j)
        {
          string t(type ? type->getString() : "default");
          throw LogicException("No type " + t + " registered for category " + cat->type);
        }
      }

      // Call the factory method
      assert(j->factoryMethod);
      Object* result = j->factoryMethod();

      // Run the callback methods
      if (!result->getType().raiseEvent(result, SIG_ADD))
      {
        // Creation denied
        delete result;
        throw DataException("Can't create object");
      }

      // Report the creation to the manager
      if (mgr)
        mgr->add(new CommandCreateObject(result));

      // Creation accepted
      return result;
  }
  throw LogicException("Unreachable code reached");
  return nullptr;
}


bool matchWildcard(const char* wild, const char *str)
{
  // Empty arguments: always return a match
  if (!wild || !str) return 1;

  const char *cp = nullptr, *mp = nullptr;

  while ((*str) && *wild != '*')
  {
    if (*wild != *str && *wild != '?')
      // Does not match
      return 0;
    wild++;
    str++;
  }

  while (*str)
  {
    if (*wild == '*')
    {
      if (!*++wild) return 1;
      mp = wild;
      cp = str+1;
    }
    else if (*wild == *str || *wild == '?')
    {
      wild++;
      str++;
    }
    else
    {
      wild = mp;
      str = cp++;
    }
  }

  while (*wild == '*') wild++;
  return !*wild;
}

} // end namespace
} // end namespace

