/***************************************************************************
  file : $URL$
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

#define FREPPLE_CORE 
#include "frepple/utils.h"
#include <sys/stat.h>


namespace frepple
{


DECLARE_EXPORT const MetaCategory* MetaCategory::firstCategory = NULL;
DECLARE_EXPORT MetaCategory::CategoryMap MetaCategory::categoriesByTag;
DECLARE_EXPORT MetaCategory::CategoryMap MetaCategory::categoriesByGroupTag;


// Command metadata
const MetaCategory Command::metadata;
const MetaClass CommandList::metadata;
const MetaClass CommandSystem::metadata;
const MetaClass CommandLoadLibrary::metadata;

// Processing instruction metadata
const MetaCategory XMLinstruction::metadata;
const MetaClass CSVInput::metadata;

// Home directory
DECLARE_EXPORT string Environment::home("[unspecified]");

// Number of processors.
// The value initialized here is overwritten in the library initialization.
DECLARE_EXPORT int Environment::processors = 2;

// Hash value computed only once
const hashtype MetaCategory::defaultHash(XMLtag::hash("DEFAULT"));


void Environment::setHomeDirectory(const string dirname)
{
  // Check if the parameter is the name of a directory
  struct stat stat_p;
  if (stat(dirname.c_str(), &stat_p))
    // Can't verify the status, directory doesn't exist
    throw RuntimeException("Home directory '" + dirname + "' doesn't exist");
  else if (stat_p.st_mode & S_IFDIR)
    // Ok, valid directory
    home = dirname;
  else
    // Exists but it's not a directory
    throw RuntimeException("Invalid home directory '" + dirname + "'");

  // Make sure the directory ends with a slash
  if (!home.empty() && *home.rbegin() != '/') home += '/';  
}


void LibraryUtils::initialize()
{
  static bool init = false;
  if(init)
  {
    clog << "Warning: Calling Frepple::LibraryUtils::initialize() more " 
      << "than once." << endl;
    return;
  }
  init = true;

  // Initialize Xerces parser
	XMLPlatformUtils::Initialize();

  // Create a lock manager
  LockManager::mgr = new LockManager();

  // Don't use the same buffer for C and C++ stream operations. This should
  // provide better performance on some platforms.
  ios::sync_with_stdio(false);

  // Initialize the command metadata.
  Command::metadata.registerCategory("COMMAND", "COMMANDS");
  CommandList::metadata.registerClass(
    "COMMAND", 
    "COMMAND_LIST",
    Object::createDefault<CommandList>);
  CommandSystem::metadata.registerClass(
    "COMMAND", 
    "COMMAND_SYSTEM",
    Object::createDefault<CommandSystem>);
  CommandLoadLibrary::metadata.registerClass(
    "COMMAND", 
    "COMMAND_LOADLIB",
    Object::createDefault<CommandLoadLibrary>);

  // Initialize the processing instruction metadata.
  XMLinstruction::metadata.registerCategory
    ("INSTRUCTION", NULL, MetaCategory::ControllerDefault);
  CSVInput::metadata.registerClass(
    "INSTRUCTION",
    "CSV",
    Object::createDefault<CSVInput>);

  // Query the system for the number of available processors
  // The environment variable NUMBER_OF_PROCESSORS is defined automatically on
  // windows platforms. On other platforms it'll have to be explicitly set
  // since there isn't an easy and portable way of querying this system 
  // information.
  const char *c = getenv("NUMBER_OF_PROCESSORS");
  if (c)
  {
    int p = atoi(c);
    Environment::setProcessors(p);
  }

#ifdef HAVE_ATEXIT
  atexit(finalize);
#endif
}


void LibraryUtils::finalize()
{
	// Shut down the Xerces parser
	XMLPlatformUtils::Terminate();
}


void MetaClass::registerClass (const char* a, const char* b, bool def) const
{
  // Re-initializing isn't okay
  if (category) 
    throw LogicException("Reinitializing class '" + type + "' isn't allowed");

  // Find or create the category
  MetaCategory* cat 
    = const_cast<MetaCategory*>(MetaCategory::findCategoryByTag(a));

  // Check for a valid category
  if (!cat)
    throw LogicException("Category " + string(a) 
      + " not found when registering class " + string(b)); 

  // Update fields
  MetaClass& me = const_cast<MetaClass&>(*this);
  me.type = b;
  me.typetag = &XMLtag::find(b);
  me.category = cat;

  // Update the metadata table
  cat->classes[XMLtag::hash(b)] = this;

  // Register this tag also as the default one, if requested
  if (def) cat->classes[XMLtag::hash("DEFAULT")] = this;
}


void MetaCategory::registerCategory (const char* a, const char* gr, 
  readController f, writeController w) const
{
  // Initialize only once
  if (type != "UNSPECIFIED") 
    throw LogicException("Reinitializing category " + type + " isn't allowed");

  // Update registry
  if (a) categoriesByTag[XMLtag::hash(a)] = this;
  if (gr) categoriesByGroupTag[XMLtag::hash(gr)] = this;

  // Update fields
  MetaCategory& me = const_cast<MetaCategory&>(*this);
  me.readFunction = f;
  me.writeFunction = w;
  if (a)
  {
    // Type tag
    me.type = a;
    me.typetag = &XMLtag::find(a);
  }
  if (gr)
  {
    // Group tag
    me.group = gr;
    me.grouptag = &XMLtag::find(gr);
  }
  
  // Maintain a linked list of all registered categories
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
  CategoryMap::const_iterator i = categoriesByTag.find(XMLtag::hash(c));
  return (i!=categoriesByTag.end()) ? i->second : NULL;
}


const MetaCategory* MetaCategory::findCategoryByTag(const hashtype h)
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByTag.find(h);
  return (i!=categoriesByTag.end()) ? i->second : NULL;
}


const MetaCategory* MetaCategory::findCategoryByGroupTag(const char* c)  
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(XMLtag::hash(c));
  return (i!=categoriesByGroupTag.end()) ? i->second : NULL;
}


const MetaCategory* MetaCategory::findCategoryByGroupTag(const hashtype h)  
{
  // Loop through all categories
  CategoryMap::const_iterator i = categoriesByGroupTag.find(h);
  return (i!=categoriesByGroupTag.end()) ? i->second : NULL;
}


void MetaCategory::persist(XMLOutput *o)
{
  for(const MetaCategory *i = firstCategory; i; i = i->nextCategory)
    if (i->writeFunction) i->writeFunction(*i, o);
}


const MetaClass* MetaClass::findClass(const char* c)
{
  // Loop through all categories
  for (MetaCategory::CategoryMap::const_iterator i = MetaCategory::categoriesByTag.begin(); 
    i != MetaCategory::categoriesByTag.end(); ++i)
  {
    // Look up in the registered classes
    MetaCategory::ClassMap::const_iterator j 
      = i->second->classes.find(XMLtag::hash(c));
    if (j != i->second->classes.end()) return j->second;
  }
  // Not found...
  return NULL;
}


void MetaClass::printClasses()
{
  clog << "Registered classes:" << endl;
  // Loop through all categories
  for (MetaCategory::CategoryMap::const_iterator i = MetaCategory::categoriesByTag.begin(); 
    i != MetaCategory::categoriesByTag.end(); ++i)
  {
	 	clog << "  " << i->second->type << endl;
    // Loop through the classes for the category
    for (MetaCategory::ClassMap::const_iterator 
      j = i->second->classes.begin();
    	j != i->second->classes.end(); 
      ++j)
        if (j->first == XMLtag::hash("DEFAULT"))
          clog << "    DEFAULT ( = " << j->second->type << " )" << endl;
        else
          clog << "    " << j->second->type << endl;
  }
}


Action MetaData::decodeAction(const char *x)
{
  // Validate the action
  if (!x) throw LogicException("Invalid action NULL");
  else if (!strcmp(x,"AC")) return ADD_CHANGE;
  else if (!strcmp(x,"A")) return ADD;
  else if (!strcmp(x,"C")) return CHANGE;
  else if (!strcmp(x,"R")) return REMOVE;
  else throw LogicException("Invalid action '" + string(x) + "'");
}


Action MetaData::decodeAction(const Attributes* atts)
{
  const XMLCh * c = atts ?
  	atts->getValue(Tags::tag_action.getXMLCharacters()) :
  	NULL;

  // Return the default in the absence of the attribute
  if (!c) return ADD_CHANGE;

  // Decode the attribute
  char* ac = XMLString::transcode(c);
	Action a = decodeAction(ac);
	XMLString::release(&ac);
  return a;
}


bool MetaClass::raiseEvent(Object* v, Signal a) const
{
  bool res1 = MetaData::raiseEvent(v,a);
  return (category && category!=this) ? 
    (res1 && category->raiseEvent(v,a)) : 
    res1;
}


Object* MetaCategory::ControllerDefault (const MetaCategory& cat, const XMLInput& in)
{
  const Attributes* atts = in.getAttributes();
  Action act = ADD;
  switch (act)
  {
    case REMOVE:
      throw DataException
        ("Entity " + cat.type + " doesn't support REMOVE action.");
    case CHANGE:
      throw DataException
        ("Entity " + cat.type + " doesn't support CHANGE action.");
    default:
      /* Lookup for the class in the map of registered classes. */
      char* type = 
        XMLString::transcode(atts->getValue(Tags::tag_type.getXMLCharacters()));
      string type2;
      if (!type && in.getParentElement().isA(cat.grouptag))
      {
        if (in.getCurrentElement().isA(cat.typetag)) type2 = "DEFAULT";
        else type2 = in.getCurrentElement().getName();
      }
      ClassMap::const_iterator j 
        = cat.classes.find(type ? XMLtag::hash(type) : (type2.empty() ? MetaCategory::defaultHash : XMLtag::hash(type2.c_str())));
      if (j == cat.classes.end())
      {
        XMLString::release(&type);
        throw LogicException("No type " + string(type ? type : (type2.empty() ? "DEFAULT" : type2.c_str())) 
          + " registered for category " + cat.type);
      }
      XMLString::release(&type);

      // Call the factory method
      Object* result = j->second->factoryMethodDefault();

      // Run the callback methods
      if (!result->getType().raiseEvent(result, SIG_ADD))
      {
        // Creation denied
        delete result;
        throw DataException("Can't create object");
      }

      // Lock the object
      LockManager::getManager().obtainWriteLock(result);

      // Creation accepted
      return result;
  }
  assert("Unreachable code reached");
  return NULL;
}


void HasDescription::writeElement(XMLOutput *o, const XMLtag &t, mode m) const
{
  // Note that this function is never called on its own. It is always called
  // from the writeElement() method of a subclass. 
  // Hence, we don't bother about the mode.
  o->writeElement(Tags::tag_category, cat);
  o->writeElement(Tags::tag_subcategory, subcat);
  o->writeElement(Tags::tag_description, descr);
}


void HasDescription::endElement (XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_category))
    setCategory(pElement.getData());
  else if (pElement.isA(Tags::tag_subcategory))
    setSubCategory(pElement.getData());
  else if (pElement.isA(Tags::tag_description))
    setDescription(pElement.getData());
}

}
