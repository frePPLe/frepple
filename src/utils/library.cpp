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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/utils.h"
#include <sys/stat.h>


namespace frepple
{
namespace utils
{

// Repository of all categories and commands
DECLARE_EXPORT const MetaCategory* MetaCategory::firstCategory = NULL;
DECLARE_EXPORT MetaCategory::CategoryMap MetaCategory::categoriesByTag;
DECLARE_EXPORT MetaCategory::CategoryMap MetaCategory::categoriesByGroupTag;

// Repository of loaded modules
set<string> CommandLoadLibrary::registry;

// Processing instruction metadata
DECLARE_EXPORT const MetaCategory* Command::metadataInstruction;

// Number of processors.
// The value initialized here is overwritten in the library initialization.
DECLARE_EXPORT int Environment::processors = 1;

// Output logging stream, whose input buffer is shared with either
// Environment::logfile or cout.
DECLARE_EXPORT ostream logger(cout.rdbuf());

// Output file stream
DECLARE_EXPORT ofstream Environment::logfile;

// Name of the log file
DECLARE_EXPORT string Environment::logfilename;

// Hash value computed only once
DECLARE_EXPORT const hashtype MetaCategory::defaultHash(Keyword::hash("default"));

DECLARE_EXPORT vector<PythonType*> PythonExtensionBase::table;


DECLARE_EXPORT string Environment::searchFile(const string filename)
{
#ifdef _MSC_VER
  static char pathseperator = '\\';
#else
  static char pathseperator = '/';
#endif

  // First: check the current directory
  struct stat stat_p;
  int result = stat(filename.c_str(), &stat_p);
  if (!result && stat_p.st_mode & S_IREAD)
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
    if (!result && stat_p.st_mode & S_IREAD)
      return fullname;
  }

#ifdef DATADIRECTORY
  // Third: check the data directory
  fullname = DATADIRECTORY;
  if (*fullname.rbegin() != pathseperator) 
    fullname += pathseperator;
  fullname.append(filename);
  result = stat(fullname.c_str(), &stat_p);
  if (!result && stat_p.st_mode & S_IREAD)
    return fullname;
#endif

#ifdef LIBDIRECTORY
  // Fourth: check the lib directory
  fullname = LIBDIRECTORY;
  if (*fullname.rbegin() != pathseperator) 
    fullname += pathseperator;
  fullname += "frepple/";
  fullname += filename;
  result = stat(fullname.c_str(), &stat_p);
  if (!result && stat_p.st_mode & S_IREAD)
    return fullname;
#endif

  // Not found
  return "";
}


DECLARE_EXPORT void Environment::setLogFile(const string& x)
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

  // Set the locale to the default setting.
  // When not executed, the locale is the "C-locale", which restricts us to
  // ascii data in the input.
  // For Posix platforms the environment variable LC_ALL controls the locale.
  // Most Linux distributions these days have a default locale that supports
  // UTF-8 encoding, meaning that every unicode character can be
  // represented.
  // On Windows, the default is the system-default ANSI code page. The number
  // of characters that frePPLe supports on Windows is constrained by this...
  #if defined(HAVE_SETLOCALE) || defined(_MSC_VER)
  setlocale(LC_ALL, "" );
  #endif

  // Initialize Xerces parser
  xercesc::XMLPlatformUtils::Initialize();

  // Initialize the processing instruction metadata.
  Command::metadataInstruction = new MetaCategory
    ("instruction", "");

  // Register Python as a processing instruction.
  CommandPython::metadata2 = new MetaClass(
    "instruction", "python", CommandPython::processorXMLInstruction);

  // Initialize the Python interpreter
  PythonInterpreter::initialize();

  // Query the system for the number of available processors.
  // The environment variable NUMBER_OF_PROCESSORS is defined automatically on
  // Windows platforms. On other platforms it'll have to be explicitly set
  // since there isn't an easy and portable way of querying this system
  // information.
  const char *c = getenv("NUMBER_OF_PROCESSORS");
  if (c)
  {
    int p = atoi(c);
    Environment::setProcessors(p);
  }
}


DECLARE_EXPORT void MetaClass::registerClass (const string& a, const string& b, 
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
  if (def) cat->classes[Keyword::hash("default")] = this;

  // Set method pointers to NULL
  factoryMethodDefault = f;
}


DECLARE_EXPORT MetaCategory::MetaCategory (const string& a, const string& gr,
  readController f, writeController w) 
{
  // Update registry
  if (!a.empty()) categoriesByTag[Keyword::hash(a)] = this; 
  if (!gr.empty()) categoriesByGroupTag[Keyword::hash(gr)] = this;

  // Update fields
  readFunction = f;
  writeFunction = w;
  type = a.empty() ? "unspecified" : a;
  typetag = &Keyword::find(type.c_str());
  group = gr.empty() ? "unspecified" : gr;
  grouptag = &Keyword::find(group.c_str());

  // Maintain a linked list of all registered categories
  nextCategory = NULL;
  if (!firstCategory)
    firstCategory = this;
  else
  {
    const MetaCategory *i = firstCategory;
    while (i->nextCategory) i = i->nextCategory;
    const_cast<MetaCategory*>(i)->nextCategory = this;
  }
}


DECLARE_EXPORT const MetaCategory* MetaCategory::findCategoryByTag(const char* c)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByTag.find(Keyword::hash(c));
  return (i!=categoriesByTag.end()) ? i->second : NULL;
}


DECLARE_EXPORT const MetaCategory* MetaCategory::findCategoryByTag(const hashtype h)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByTag.find(h);
  return (i!=categoriesByTag.end()) ? i->second : NULL;
}


DECLARE_EXPORT const MetaCategory* MetaCategory::findCategoryByGroupTag(const char* c)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(Keyword::hash(c));
  return (i!=categoriesByGroupTag.end()) ? i->second : NULL;
}


DECLARE_EXPORT const MetaCategory* MetaCategory::findCategoryByGroupTag(const hashtype h)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(h);
  return (i!=categoriesByGroupTag.end()) ? i->second : NULL;
}


DECLARE_EXPORT const MetaClass* MetaCategory::findClass(const char* c) const
{
  // Look up in the registered classes
  MetaCategory::ClassMap::const_iterator j = classes.find(Keyword::hash(c));
  return (j == classes.end()) ? NULL : j->second;
}


DECLARE_EXPORT const MetaClass* MetaCategory::findClass(const hashtype h) const
{
  // Look up in the registered classes
  MetaCategory::ClassMap::const_iterator j = classes.find(h);
  return (j == classes.end()) ? NULL : j->second;
}


DECLARE_EXPORT void MetaCategory::persist(XMLOutput *o)
{
  for (const MetaCategory *i = firstCategory; i; i = i->nextCategory)
    if (i->writeFunction) i->writeFunction(i, o);
}


DECLARE_EXPORT const MetaClass* MetaClass::findClass(const char* c)
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
  return NULL;
}


DECLARE_EXPORT void MetaClass::printClasses()
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


DECLARE_EXPORT Action MetaClass::decodeAction(const char *x)
{
  // Validate the action
  if (!x) throw LogicException("Invalid action NULL");
  else if (!strcmp(x,"AC")) return ADD_CHANGE;
  else if (!strcmp(x,"A")) return ADD;
  else if (!strcmp(x,"C")) return CHANGE;
  else if (!strcmp(x,"R")) return REMOVE;
  else throw LogicException("Invalid action '" + string(x) + "'");
}


DECLARE_EXPORT Action MetaClass::decodeAction(const AttributeList& atts)
{
  // Decode the string and return the default in the absence of the attribute
  const DataElement* c = atts.get(Tags::tag_action);
  return *c ? decodeAction(c->getString().c_str()) : ADD_CHANGE;
}


DECLARE_EXPORT bool MetaClass::raiseEvent(Object* v, Signal a) const
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


Object* MetaCategory::ControllerDefault (const MetaClass* cat, const AttributeList& in)
{
  Action act = ADD;
  switch (act)
  {
    case REMOVE:
      throw DataException
      ("Entity " + cat->type + " doesn't support REMOVE action");
    case CHANGE:
      throw DataException
      ("Entity " + cat->type + " doesn't support CHANGE action");
    default:
      /* Lookup for the class in the map of registered classes. */
      const MetaClass* j;
      if (cat->category)
        // Class metadata passed: we already know what type to create
        j = cat;
      else
      {
        // Category metadata passed: we need to look up the type
        const DataElement* type = in.get(Tags::tag_type);
        j = static_cast<const MetaCategory&>(*cat).findClass(*type ? Keyword::hash(type->getString()) : MetaCategory::defaultHash);
        if (!j)
        {
          string t(*type ? type->getString() : "default");
          throw LogicException("No type " + t + " registered for category " + cat->type);
        }
      }

      // Call the factory method
      Object* result = j->factoryMethodDefault();

      // Run the callback methods
      if (!result->getType().raiseEvent(result, SIG_ADD))
      {
        // Creation denied
        delete result;
        throw DataException("Can't create object");
      }

      // Creation accepted
      return result;
  }
  throw LogicException("Unreachable code reached");
  return NULL;
}


void HasDescription::writeElement(XMLOutput *o, const Keyword &t, mode m) const
{
  // Note that this function is never called on its own. It is always called
  // from the writeElement() method of a subclass.
  // Hence, we don't bother about the mode.
  o->writeElement(Tags::tag_category, cat);
  o->writeElement(Tags::tag_subcategory, subcat);
  o->writeElement(Tags::tag_description, descr);
}


void HasDescription::endElement (XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_category))
    setCategory(pElement.getString());
  else if (pAttr.isA(Tags::tag_subcategory))
    setSubCategory(pElement.getString());
  else if (pAttr.isA(Tags::tag_description))
    setDescription(pElement.getString());
}

} // end namespace
} // end namespace

