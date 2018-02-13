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

/* Uncomment the next line to create a lot of debugging messages during
 * the parsing of XML-data. */
//#define PARSE_DEBUG

// With VC++ we use the Win32 functions to browse a directory
#ifdef _MSC_VER
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
// With Unix-like systems we use a check suggested by the autoconf tools
#if HAVE_DIRENT_H
# include <dirent.h>
# define NAMLEN(dirent) strlen((dirent)->d_name)
#else
# define dirent direct
# define NAMLEN(dirent) (dirent)->d_namlen
# if HAVE_SYS_NDIR_H
#  include <sys/ndir.h>
# endif
# if HAVE_SYS_DIR_H
#  include <sys/dir.h>
# endif
# if HAVE_NDIR_H
#  include <ndir.h>
# endif
#endif
#endif


namespace frepple
{
namespace utils
{

xercesc::XMLTranscoder* XMLInput::utf8_encoder = nullptr;


char* XMLInput::transcodeUTF8(const XMLCh* xercesChars)
{
  XMLSize_t charsEaten;
  XMLSize_t charsReturned = utf8_encoder->transcodeTo(xercesChars,
    xercesc::XMLString::stringLen(xercesChars),
    (XMLByte*) encodingbuffer, 4*1024,
    charsEaten, xercesc::XMLTranscoder::UnRep_RepChar );
  encodingbuffer[charsReturned] = 0;
  return encodingbuffer;
}


XMLInput::XMLInput() : objects(maxobjects), data(maxdata)
{
  if (!utf8_encoder)
  {
    xercesc::XMLTransService::Codes resCode;
    utf8_encoder = xercesc::XMLPlatformUtils::fgTransService->makeNewTranscoderFor("UTF-8", resCode, 4*1024);
    if (!XMLInput::utf8_encoder)
      logger << "Can't initialize UTF-8 transcoder: reason " << resCode << endl;
  }
}


void  XMLInput::processingInstruction
(const XMLCh *const target, const XMLCh *const data)
{
  char* type = xercesc::XMLString::transcode(target);
  char* value = xercesc::XMLString::transcode(data);
  try
  {
    if (!strcmp(type,"python"))
    {
      // "python" is the only processing instruction which we process.
      // Others will be silently ignored
      try
      {
        // Execute the processing instruction
        PythonInterpreter::execute(value);
      }
      catch (const DataException& e)
      {
        if (abortOnDataException)
        {
          xercesc::XMLString::release(&type);
          xercesc::XMLString::release(&value);
          throw;
        }
        else
          logger << "Continuing after data error: " << e.what() << endl;
      }
    }
    xercesc::XMLString::release(&type);
    xercesc::XMLString::release(&value);
  }
  catch (...)
  {
    xercesc::XMLString::release(&type);
    xercesc::XMLString::release(&value);
    throw;
  }
}


void XMLInput::startElement(const XMLCh* const uri,
  const XMLCh* const ename, const XMLCh* const qname,
  const xercesc::Attributes& atts)
{
  string ename_utf8 = transcodeUTF8(ename);

  // Currently ignoring all input?
  if (ignore)
  {
    if (data[dataindex].hash == Keyword::hash(ename_utf8))
    {
      // Ignoring elements one level deeper
      ++ignore;
      if (ignore >= USHRT_MAX)
        throw DataException("XML-document nested excessively deep");
    }
    return;
  }

  // Use new data value
  data[++dataindex].value.setString("");
  reading = true;

  #ifdef PARSE_DEBUG
  logger << "Start XML element #" << dataindex << " '" << ename_utf8
    << "' for object #" << objectindex << " ("
    << ((objectindex >= 0 && objects[objectindex].cls) ? objects[objectindex].cls->type : "none")
    << ")" << endl;
  #endif

  // Look up the field
  data[dataindex].hash = Keyword::hash(ename_utf8);
  data[dataindex].field = nullptr;
  if (dataindex >= 1 && data[dataindex-1].field && data[dataindex-1].field->isGroup()
    && data[dataindex].hash == data[dataindex-1].field->getKeyword()->getHash())
  {
    // New element to create in the group
    // Increment object index
    if (++objectindex >= maxobjects)
      // You're joking?
      throw DataException("XML-document nested excessively deep");
    // New object on the stack
    objects[objectindex].object = nullptr;
    objects[objectindex].start = dataindex;
    objects[objectindex].cls = data[dataindex-1].field->getClass();
    objects[objectindex].hash = data[dataindex].hash;
    reading = false;

    // Debugging message
    #ifdef PARSE_DEBUG
    logger << "Starting object #" << objectindex << " ("
      << objects[objectindex].cls->type << ")" << endl;
    #endif

    if (!objects[objectindex].cls->category)
    {
      // Category metadata passed: replace it with the concrete type
      // We start at the last attribute. Putting the type attribute at the end
      // will thus give a (very small) performance improvement.
      for (XMLSize_t i = atts.getLength(); i > 0; --i)
      {
        string attr_name = transcodeUTF8(atts.getLocalName(i - 1));
        if (Keyword::hash(attr_name) == Tags::type.getHash())
        {
          string tp = transcodeUTF8(atts.getValue(i - 1));
          objects[objectindex].cls = static_cast<const MetaCategory&>(*objects[objectindex].cls).findClass(
            Keyword::hash(tp)
          );
          if (!objects[objectindex].cls)
            throw DataException("No type " + tp + " registered");
          break;
        }
      }
      if (!objects[objectindex].cls->category)
      {
        // No type attribute was registered, and we use the default of the category
        const MetaCategory& cat = static_cast<const MetaCategory&>(*objects[objectindex].cls);
        objects[objectindex].cls = cat.findClass(Tags::deflt.getHash());
        if (!objects[objectindex].cls)
          throw DataException("No default type registered for category " + cat.type);
      }
    }
    // Skip the opening tag of this object
    --dataindex;

    // Push all attributes on the data stack.
    for (XMLSize_t i = 0, cnt = atts.getLength(); i < cnt; ++i)
    {
      // Look up the field
      ++dataindex;
      string attr_name = transcodeUTF8(atts.getLocalName(i));
      data[dataindex].hash = Keyword::hash(attr_name);
      if (data[dataindex].hash == Tags::type.getHash())
      {
        // Skip attribute called "type"
        --dataindex;
        continue;
      }
      else if (data[dataindex].hash == Tags::action.getHash())
      {
        // Action attribute is special, as it's not a field
        data[dataindex].field = nullptr;
      }
      else
      {
        data[dataindex].field = objects[objectindex].cls->findField(data[dataindex].hash);
        if (!data[dataindex].field && objects[objectindex].cls->category)
          data[dataindex].field = objects[objectindex].cls->category->findField(data[dataindex].hash);
        if (!data[dataindex].field)
          throw DataException("Attribute '" + attr_name + "' not defined");
      }

      // Set the data value
      data[dataindex].value.setString(transcodeUTF8(atts.getValue(i)));
    }
    return;
  }

  // Look up the field
  assert(objects[objectindex].cls);
  data[dataindex].field = objects[objectindex].cls->findField(data[dataindex].hash);
  if (!data[dataindex].field && objects[objectindex].cls->category)
    data[dataindex].field = objects[objectindex].cls->category->findField(data[dataindex].hash);

  // Field not found
  if (!data[dataindex].field)
  {
    if (!dataindex && data[dataindex].hash == objects[0].hash)
    {
      // Special case: root element
      --dataindex;
      for (XMLSize_t i = 0, cnt = atts.getLength(); i < cnt; ++i)
      {
        string attr_name = transcodeUTF8(atts.getLocalName(i));
        if (attr_name == "source")
          // Special case: Source specified as attribute of the root element
          setSource(transcodeUTF8(atts.getValue(i)));
      }
    }
    else if (data[dataindex].hash == Tags::booleanproperty.getHash()
      || data[dataindex].hash == Tags::stringproperty.getHash()
      || data[dataindex].hash == Tags::doubleproperty.getHash()
      || data[dataindex].hash == Tags::dateproperty.getHash()
      )
    {
      // Special case: custom properties
      short ok = 0;
      for (XMLSize_t i = 0, cnt = atts.getLength(); i < cnt; ++i)
      {
        string attr_name = transcodeUTF8(atts.getLocalName(i));
        if (attr_name == "name")
        {
          data[dataindex].name = transcodeUTF8(atts.getValue(i));
          ok += 1;
        }
        else if (attr_name == "value")
        {
          data[dataindex].value.setString(transcodeUTF8(atts.getValue(i)));
          ok += 2;
        }
      }
      if (ok != 3)
      {
        data[dataindex].hash = 0; // Mark the field as invalid
        logger << "Warning: property missing name and/or value field" << endl;
      }
    }
    else
    {
      // Ignore this element
      reading = false;
      ++ignore;
      logger << "Warning: Ignoring XML element '" << ename_utf8 << "'" << endl;
    }
  }
  else if (data[dataindex].field->isPointer())
  {
    // Increment object index
    if (++objectindex >= maxobjects)
      // You're joking?
      throw DataException("XML-document with elements nested excessively deep");

    // New object on the stack
    objects[objectindex].object = nullptr;
    objects[objectindex].cls = data[dataindex].field->getClass();
    objects[objectindex].start = dataindex + 1;
    objects[objectindex].hash = Keyword::hash(ename_utf8);
    reading = false;

    // Debugging message
    #ifdef PARSE_DEBUG
    logger << "Starting object #" << objectindex << " ("
      << objects[objectindex].cls->type << ")" << endl;
    #endif

    if (!objects[objectindex].cls->category)
    {
      // Category metadata passed: replace it with the concrete type
      // We start at the last attribute. Putting the type attribute at the end
      // will thus give a (very small) performance improvement.
      for (XMLSize_t i = atts.getLength(); i > 0; --i)
      {
        string attr_name = transcodeUTF8(atts.getLocalName(i - 1));
        if (Keyword::hash(attr_name) == Tags::type.getHash())
        {
          string tp = transcodeUTF8(atts.getValue(i - 1));
          objects[objectindex].cls = static_cast<const MetaCategory&>(*objects[objectindex].cls).findClass(
            Keyword::hash(tp)
          );
          if (!objects[objectindex].cls)
            throw DataException("No type " + tp + " registered for category " + objects[objectindex].cls->type);
          break;
        }
      }
      if (!objects[objectindex].cls->category)
      {
        // No type attribute was registered, and we use the default of the category
        objects[objectindex].cls = static_cast<const MetaCategory&>(*objects[objectindex].cls).findClass(
            Tags::deflt.getHash()
            );
        if (!objects[objectindex].cls)
          throw DataException("No default type registered for category " + objects[objectindex].cls->type);
      }
    }

    // Push all attributes on the data stack.
    for (XMLSize_t i = 0, cnt = atts.getLength(); i < cnt; ++i)
    {
      // Use new data value
      ++dataindex;

      // Look up the field
      string attr_name = transcodeUTF8(atts.getLocalName(i));
      data[dataindex].hash = Keyword::hash(attr_name);
      if (data[dataindex].hash == Tags::type.getHash() || data[dataindex].hash == Tags::action.getHash())
      {
        // Skip attribute called "type"
        --dataindex;
        continue;
      }
      else if (data[dataindex].hash == Tags::action.getHash())
      {
        // Action attribute is special, as it's not a field
        data[dataindex].field = nullptr;
      }
      else
      {
        data[dataindex].field = objects[objectindex].cls->findField(data[dataindex].hash);
        if (!data[dataindex].field && objects[objectindex].cls->category)
          data[dataindex].field = objects[objectindex].cls->category->findField(data[dataindex].hash);
        if (!data[dataindex].field)
          throw DataException("Attribute '" + attr_name + "' not defined");
      }

      // Set the data value
      data[dataindex].value.setString(transcodeUTF8(atts.getValue(i)));
    }
  }
  else if (data[dataindex].field->isGroup())
    reading = false;
}


void XMLInput::endElement(const XMLCh* const uri,
    const XMLCh* const ename,
    const XMLCh* const qname)
{
  string ename_utf8 = transcodeUTF8(ename);

  // Currently ignoring all input?
  hashtype h = Keyword::hash(ename_utf8);
  if (ignore)
  {
    if (data[dataindex].hash == h)
    {
      // Finishing ignored element level
      --ignore;
      if (!ignore)
        --dataindex;
    }
    return;
  }

  #ifdef PARSE_DEBUG
  logger << "End XML element #" << dataindex << " '" << ename_utf8
    << "' for object #" << objectindex << " ("
    << ((objectindex >= 0 && objects[objectindex].cls) ? objects[objectindex].cls->type : "none")
    << ")" << endl;
  #endif

  // Ignore content between tags
  reading = false;

  if (objectindex == 0 && objects[objectindex].object && dataindex >= 0
    && data[dataindex].field && !data[dataindex].field->isGroup())
  {
    // Immediately process updates to the root object
    #ifdef PARSE_DEBUG
    logger << "Updating field " << data[dataindex].field->getName().getName() << " on the root object" << endl;
    #endif
    data[dataindex].field->setField(objects[objectindex].object, data[dataindex].value, getCommandManager());
    --dataindex;
  }

  if (h != objects[objectindex].hash || dataindex < 0)
    // Continue reading more fields until we'll have read the complete object
    return;

  try
  {
    XMLDataValueDict dict(data, objects[objectindex].start, dataindex);

    // Push also the source field in the attributes.
    // This is only required if 1) it's not in the dict yet, and 2) there
    // is a value set at the interface level, 3) the class has a source field.
    if (!getSource().empty())
    {
      const XMLData* s = dict.get(Tags::source);
      if (!s)
      {
        const MetaFieldBase* f = objects[objectindex].cls->findField(Tags::source);
        if (!f && objects[objectindex].cls->category)
          f = objects[objectindex].cls->category->findField(Tags::source);
        if (f)
        {
          data[++dataindex].field = f;
          data[dataindex].hash = Tags::source.getHash();
          data[dataindex].value.setString(getSource());
          dict.enlarge();
        }
      }
    }

    // Check if we need to add a parent object to the dict
    bool found_parent = false;
    if (objectindex > 0 && objects[objectindex].cls->parent)
    {
      assert(objects[objectindex-1].cls);
      const MetaClass* cl = objects[objectindex-1].cls;
      for (MetaClass::fieldlist::const_iterator i = objects[objectindex].cls->getFields().begin();
        i != objects[objectindex].cls->getFields().end(); ++i)
        if ((*i)->getFlag(PARENT) && objectindex >= 1)
        {
          const MetaFieldBase* fld = data[objects[objectindex].start-1].field;
          if (fld && !fld->isGroup())
            // Only under a group field can we inherit from a parent object
            continue;
          if (*((*i)->getClass()) == *cl
            || (cl->category && *((*i)->getClass()) == *(cl->category)))
          {
            // Parent object matches expected type as parent field
            // First, create the parent object. It is normally created only
            // AFTER all its fields are read in, and that's too late for us.
            if (!objects[objectindex-1].object)
            {
              XMLDataValueDict dict_parent(data, objects[objectindex-1].start, dataindex-1);
              if (objects[objectindex-1].cls->category)
              {
                assert(objects[objectindex-1].cls->category->readFunction);
                objects[objectindex-1].object =
                  objects[objectindex-1].cls->category->readFunction(
                    objects[objectindex-1].cls,
                    dict_parent,
                    getCommandManager()
                    );
              }
              else
              {
                assert(static_cast<const MetaCategory*>(objects[objectindex-1].cls)->readFunction);
                objects[objectindex-1].object =
                  static_cast<const MetaCategory*>(objects[objectindex-1].cls)->readFunction(
                    objects[objectindex-1].cls,
                    dict_parent,
                    getCommandManager()
                    );
              }
              // Set fields already available now on the parent object
              for (int idx = objects[objectindex-1].start; idx < objects[objectindex].start; ++idx)
              {
                if (data[idx].hash == Tags::type.getHash() || data[idx].hash == Tags::action.getHash())
                  continue;
                if (data[idx].field && !data[idx].field->isGroup())
                {
                    data[idx].field->setField(objects[objectindex-1].object, data[idx].value, getCommandManager());
                    data[idx].field = nullptr; // Mark as already applied
                }
                else if (data[idx].hash == Tags::booleanproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 1, getCommandManager()
                    );
                else if (data[idx].hash == Tags::dateproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 2, getCommandManager()
                    );
                else if (data[idx].hash == Tags::doubleproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 3, getCommandManager()
                    );
                else if (data[idx].hash == Tags::stringproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 4, getCommandManager()
                    );
              }

            }
            // Add reference to parent to the current dict
            data[++dataindex].field = *i;
            data[dataindex].hash = (*i)->getHash();
            data[dataindex].value.setObject(objects[objectindex-1].object);
            dict.enlarge();
            found_parent = true;
            break;
          }
        }
    }
    if (!found_parent && objectindex > 0 && objects[objectindex].cls->category && objects[objectindex].cls->category->parent)
    {
      assert(objects[objectindex-1].cls);
      const MetaClass* cl = objects[objectindex-1].cls;
      for (MetaClass::fieldlist::const_iterator i = objects[objectindex].cls->category->getFields().begin();
        i != objects[objectindex].cls->category->getFields().end(); ++i)
        if ((*i)->getFlag(PARENT) && objectindex >= 1)
        {
          const MetaFieldBase* fld = data[objects[objectindex].start-1].field;
          if (fld && !fld->isGroup())
            // Only under a group field can we inherit from a parent object
            continue;
          if (*((*i)->getClass()) == *cl
            || (cl->category && *((*i)->getClass()) == *(cl->category)))
          {
            // Parent object matches expected type as parent field
            // First, create the parent object. It is normally created only
            // AFTER all its fields are read in, and that's too late for us.
            if (!objects[objectindex-1].object)
            {
              XMLDataValueDict dict_parent(data, objects[objectindex-1].start, dataindex-1);
              if (objects[objectindex-1].cls->category)
              {
                assert(objects[objectindex-1].cls->category->readFunction);
                objects[objectindex-1].object =
                  objects[objectindex-1].cls->category->readFunction(
                    objects[objectindex-1].cls,
                    dict_parent,
                    getCommandManager()
                    );
              }
              else
              {
                assert(static_cast<const MetaCategory*>(objects[objectindex-1].cls)->readFunction);
                objects[objectindex-1].object =
                  static_cast<const MetaCategory*>(objects[objectindex-1].cls)->readFunction(
                    objects[objectindex-1].cls,
                    dict_parent,
                    getCommandManager()
                    );
              }
              // Set fields already available now on the parent object
              for (int idx = objects[objectindex-1].start; idx < objects[objectindex].start; ++idx)
              {
                if (data[idx].hash == Tags::type.getHash() || data[idx].hash == Tags::action.getHash())
                  continue;
                if (data[idx].field && !data[idx].field->isGroup())
                {
                    data[idx].field->setField(objects[objectindex-1].object, data[idx].value, getCommandManager());
                    data[idx].field = nullptr; // Mark as already applied
                }
                else if (data[idx].hash == Tags::booleanproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 1, getCommandManager()
                    );
                else if (data[idx].hash == Tags::dateproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 2, getCommandManager()
                    );
                else if (data[idx].hash == Tags::doubleproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 3, getCommandManager()
                    );
                else if (data[idx].hash == Tags::stringproperty.getHash())
                  objects[objectindex].object->setProperty(
                    data[idx].name, data[idx].value, 4, getCommandManager()
                    );
              }
            }
            // Add reference to parent to the current dict
            data[++dataindex].field = *i;
            data[dataindex].hash = (*i)->getHash();
            data[dataindex].value.setObject(objects[objectindex-1].object);
            dict.enlarge();
            break;
          }
        }
    }

    // Root object never gets created
    if (!objectindex)
      return;

    #ifdef PARSE_DEBUG
    logger << "Creating object " << objects[objectindex].cls->type << endl;
    dict.print();
    #endif

    // Call the object factory for the category and pass all field values
    // in a dictionary.
    // In some cases, the reading of the child fields already triggered the
    // creation of the parent. In such cases we can skip the creation step
    // here.
    if (!objects[objectindex].object)
    {
      if (objects[objectindex].cls->category)
      {
        assert(objects[objectindex].cls->category->readFunction);
        objects[objectindex].object =
          objects[objectindex].cls->category->readFunction(
            objects[objectindex].cls,
            dict,
            getCommandManager()
            );
      }
      else
      {
        assert(static_cast<const MetaCategory*>(objects[objectindex].cls)->readFunction);
        objects[objectindex].object =
          static_cast<const MetaCategory*>(objects[objectindex].cls)->readFunction(
            objects[objectindex].cls,
            dict,
            getCommandManager()
            );
      }
    }

    // Update all fields on the new object
    if (objects[objectindex].object)
    {
      for (int idx = objects[objectindex].start; idx <= dataindex; ++idx)
      {
        if (data[idx].hash == Tags::type.getHash() || data[idx].hash == Tags::action.getHash())
          continue;
        if (data[idx].field && !data[idx].field->isGroup())
          data[idx].field->setField(objects[objectindex].object, data[idx].value, getCommandManager());
        else if (data[idx].hash == Tags::booleanproperty.getHash())
          objects[objectindex].object->setProperty(
            data[idx].name, data[idx].value, 1, getCommandManager()
            );
        else if (data[idx].hash == Tags::dateproperty.getHash())
          objects[objectindex].object->setProperty(
            data[idx].name, data[idx].value, 2, getCommandManager()
            );
        else if (data[idx].hash == Tags::doubleproperty.getHash())
          objects[objectindex].object->setProperty(
            data[idx].name, data[idx].value, 3, getCommandManager()
            );
        else if (data[idx].hash == Tags::stringproperty.getHash())
          objects[objectindex].object->setProperty(
            data[idx].name, data[idx].value, 4, getCommandManager()
            );
      }
    }

    if (objectindex && dataindex && data[objects[objectindex].start-1].field && data[objects[objectindex].start-1].field->isPointer())
      // Update parent object
      data[objects[objectindex].start-1].value.setObject(objects[objectindex].object);
    if (getUserExit())
      getUserExit().call(objects[objectindex].object);
    callUserExitCpp(objects[objectindex].object);
  }
  catch (const DataException& e)
  {
    if (abortOnDataException) throw;
    else logger << "Continuing after data error: " << e.what() << endl;
  }

  // Update indexes for data and object
  dataindex = objects[objectindex--].start - 1;
}


void XMLInput::characters(const XMLCh *const c, const XMLSize_t n)
{
  if (reading && dataindex >= 0)
    data[dataindex].value.appendString(transcodeUTF8(c));
}


void XMLInput::warning(const xercesc::SAXParseException& e)
{
  char* message = xercesc::XMLString::transcode(e.getMessage());
  logger << "Warning: " << message;
  if (e.getLineNumber() > 0)
    logger << " at line: " << e.getLineNumber();
  logger << endl;
  xercesc::XMLString::release(&message);
}


void XMLInput::fatalError(const xercesc::SAXParseException& e)
{
  char* message = xercesc::XMLString::transcode(e.getMessage());
  ostringstream ch;
  ch << message;
  if (e.getLineNumber() > 0)
    ch << " at line " << e.getLineNumber();
  xercesc::XMLString::release(&message);
  throw DataException(ch.str());
}


void XMLInput::error(const xercesc::SAXParseException& e)
{
  char* message = xercesc::XMLString::transcode(e.getMessage());
  ostringstream ch;
  ch << message;
  if (e.getLineNumber() > 0)
    ch << " at line " << e.getLineNumber();
  xercesc::XMLString::release(&message);
  throw DataException(ch.str());
}


XMLInput::~XMLInput()
{
  // Delete the xerces parser object
  delete parser;
}


void XMLInput::parse(xercesc::InputSource &in, Object *pRoot, bool validate)
{
  try
  {
    // Create a Xerces parser
    parser = xercesc::XMLReaderFactory::createXMLReader();

    // Set the features of the parser. A bunch of the options are dependent
    // on whether we want to validate the input or not.
    parser->setProperty(xercesc::XMLUni::fgXercesScannerName, const_cast<XMLCh*>
        (validate ? xercesc::XMLUni::fgSGXMLScanner : xercesc::XMLUni::fgWFXMLScanner));
    parser->setFeature(xercesc::XMLUni::fgSAX2CoreValidation, validate);
    parser->setFeature(xercesc::XMLUni::fgSAX2CoreNameSpacePrefixes, false);
    parser->setFeature(xercesc::XMLUni::fgXercesIdentityConstraintChecking, false);
    parser->setFeature(xercesc::XMLUni::fgXercesDynamic, false);
    parser->setFeature(xercesc::XMLUni::fgXercesSchema, validate);
    parser->setFeature(xercesc::XMLUni::fgXercesSchemaFullChecking, false);
    parser->setFeature(xercesc::XMLUni::fgXercesValidationErrorAsFatal, true);
    parser->setFeature(xercesc::XMLUni::fgXercesIgnoreAnnotations, true);

    if (validate)
    {
      // Specify the no-namespace schema file
      string schema = Environment::searchFile("frepple.xsd");
      if (schema.empty())
        throw RuntimeException("Can't find XML schema file 'frepple.xsd'");
      XMLCh *c = xercesc::XMLString::transcode(schema.c_str());
      parser->setProperty(
        xercesc::XMLUni::fgXercesSchemaExternalNoNameSpaceSchemaLocation, c
      );
      xercesc::XMLString::release(&c);
    }

    if (pRoot)
    {
      // Set the event handler. If we are reading into a nullptr object, there is
      // no need to use a content handler.
      parser->setContentHandler(this);

      // Get the parser to read data into the object pRoot.
      objectindex = 0;
      dataindex = -1;
      objects[0].start = 0;
      objects[0].object = pRoot;
      objects[0].cls = &pRoot->getType();
      objects[0].hash = pRoot->getType().typetag->getHash();

      #ifdef PARSE_DEBUG
      logger << "Starting root object #" << objectindex << " ("
        << objects[objectindex].cls->type << ")" << endl;
      #endif
    }
    else
    {
      // Don't process any of the input data. We'll just let the parser
      // check the validity of the XML document.
      ignore = true;
      objectindex = -1;
      dataindex = 0;
    }

    // Set the error handler
    parser->setErrorHandler(this);

    // Parse the input
    parser->parse(in);
  }
  catch (const xercesc::XMLException& toCatch)
  {
    char* message = xercesc::XMLString::transcode(toCatch.getMessage());
    string msg(message);
    xercesc::XMLString::release(&message);
    delete parser;
    parser = nullptr;
    throw RuntimeException("Parsing error: " + msg);
  }
  catch (const exception& toCatch)
  {
    delete parser;
    parser = nullptr;
    ostringstream msg;
    msg << "Error during XML parsing: " << toCatch.what();
    throw RuntimeException(msg.str());
  }
  catch (...)
  {
    delete parser;
    parser = nullptr;
    throw RuntimeException(
      "Parsing error: Unexpected exception during XML parsing");
  }
  delete parser;
  parser = nullptr;
}


void XMLSerializer::escape(const string& x)
{
  for (const char* p = x.c_str(); *p; ++p)
  {
    switch (*p)
    {
      case '&': *m_fp << "&amp;"; break;
      case '<': *m_fp << "&lt;"; break;
      case '>': *m_fp << "&gt;"; break;
      case '"': *m_fp << "&quot;"; break;
      case '\'': *m_fp << "&apos;"; break;
      default: *m_fp << *p;
    }
  }
}


void XMLSerializer::incIndent()
{
  indentstring[m_nIndent++] = '\t';
  if (m_nIndent > 40) m_nIndent = 40;
  indentstring[m_nIndent] = '\0';
}


void XMLSerializer::decIndent()
{
  if (--m_nIndent < 0) m_nIndent = 0;
  indentstring[m_nIndent] = '\0';
}


void Serializer::setContentType(const string& c)
{
  if (c == "base")
    setContentType(BASE);
  else if (c == "plan")
    setContentType(PLAN);
  else if (c == "detail")
    setContentType(DETAIL);
  else
    // Silently fallback to the default value
    setContentType(BASE);
}


void Serializer::writeElement
(const Keyword& tag, const Object* object, FieldCategory m)
{
  // Avoid nullptr pointers and skip hidden objects
  if (!object || (object->getHidden() && !writeHidden))
    return;

  // Adjust current and parent object pointer
  const Object *previousParent = parentObject;
  parentObject = currentObject;
  currentObject = object;
  ++numObjects;

  // Call the write method on the object
  if (m != BASE)
    // Mode is overwritten
    object->writeElement(this, tag, m);
  else
    // Choose wether to save a reference of the object.
    // The root object can't be saved as a reference.
    object->writeElement(
      this, tag, getSaveReferences() ? MANDATORY : content
      );

  // Adjust current and parent object pointer
  currentObject = parentObject;
  parentObject = previousParent;
}


void XMLSerializer::writeElementWithHeader(const Keyword& tag, const Object* object)
{
  // Root object can't be null...
  if (!object)
    throw RuntimeException("Can't accept a nullptr object as XML root");

  // There should not be any saved objects yet
  if (numObjects > 0)
    throw LogicException("Can't have multiple headers in a document");
  assert(!parentObject);
  assert(!currentObject);

  // Write the first line for the xml document
  writeString(getHeaderStart());

  // Adjust current object pointer
  currentObject = object;

  // Write the object
  ++numObjects;
  BeginObject(tag, getHeaderAtts());
  skipHead();
  object->writeElement(this, tag, getContentType());

  // Adjust current and parent object pointer
  currentObject = nullptr;
  parentObject = nullptr;
}


const XMLData* XMLDataValueDict::get(const Keyword& key) const
{
  for (int i = strt; i <= nd; ++i)
    if (fields[i].hash == key.getHash())
      return &fields[i].value;
  return nullptr;
}


void XMLDataValueDict::print()
{
  for (int i = strt; i <= nd; ++i)
  {
    if (fields[i].field)
      logger << "   " << fields[i].field->getName().getName() << ": ";
    else
      logger << "   null: ";
    Object *obj = static_cast<Object*>(fields[i].value.getObject());
    if (obj)
      logger << "pointer to " << obj->getType().type << endl;
    else
      logger << fields[i].value.getString() << endl;
  }
}


bool XMLData::getBool() const
{
  switch (getData()[0])
  {
    case 'T':
    case 't':
    case '1':
      return true;
    case 'F':
    case 'f':
    case '0':
      return false;
  }
  throw DataException("Invalid boolean value: " + string(getData()));
}


const char* DataKeyword::getName() const
{
  if (ch) return ch;
  Keyword::tagtable::const_iterator i = Keyword::getTags().find(hash);
  if (i == Keyword::getTags().end())
    throw LogicException("Undefined element keyword");
  return i->second->getName().c_str();
}


Keyword::Keyword(const string& name) : strName(name)
{
  // Error condition: name is empty
  if (name.empty()) throw LogicException("Creating keyword without name");

  // Create a number of variations of the tag name   TODO GET RID OF THESE XML SPECIFIC SHIT
  strStartElement = string("<") + name;
  strEndElement = string("</") + name + ">\n";
  strElement = string("<") + name + ">";
  strAttribute = string(" ") + name + "=\"";
  strQuoted = string("\"") + name + "\":";

  // Compute the hash value
  dw = hash(name.c_str());

  // Verify that the hash is "perfect".
  check();
}


Keyword::Keyword(const string& name, const string& nspace)
  : strName(name)
{
  // Error condition: name is empty
  if (name.empty())
    throw LogicException("Creating keyword without name");
  if (nspace.empty())
    throw LogicException("Creating keyword with empty namespace");

  // Create a number of variations of the tag name
  strStartElement = string("<") + nspace + ":" + name;
  strEndElement = string("</") + nspace + ":" + name + ">\n";
  strElement = string("<") + nspace + ":" + name + ">";
  strAttribute = string(" ") + nspace + ":" + name + "=\"";
  strQuoted = string("\"") + name + "\":";

  // Compute the hash value
  dw = hash(name);

  // Verify that the hash is "perfect".
  check();
}


void Keyword::check()
{
  // To be thread-safe we make sure only a single thread at a time
  // can execute this check.
  static mutex dd;
  {
    lock_guard<mutex> l(dd);
    tagtable::const_iterator i = getTags().find(dw);
    if (i!=getTags().end() && i->second->getName()!=strName)
      throw LogicException("Tag XML-tag hash function clashes for "
          + i->second->getName() + " and " + strName);
    getTags().insert(make_pair(dw,this));
  }
}


Keyword::~Keyword()
{
  // Remove from the tag list
  tagtable::iterator i = getTags().find(dw);
  if (i!=getTags().end()) getTags().erase(i);
}


const Keyword& Keyword::find(const char* name)
{
  tagtable::const_iterator i = getTags().find(hash(name));
  return *(i!=getTags().end() ? i->second : new Keyword(name));
}


Keyword::tagtable& Keyword::getTags()
{
  static tagtable alltags;
  return alltags;
}


hashtype Keyword::hash(const char* c)
{
  if (c == 0 || *c == 0) return 0;

  // Compute hash
  const char* curCh = c;
  hashtype hashVal = *curCh;
  while (*curCh)
    hashVal = (hashVal * 37) + (hashVal >> 24) + *curCh++;

  // Divide by modulus
  return hashVal % 954991;
}


void Keyword::printTags()
{
  for (tagtable::iterator i = getTags().begin(); i != getTags().end(); ++i)
    logger << i->second->getName() << "   " << i->second->dw << endl;
}


void XMLInputFile::parse(Object *pRoot, bool validate)
{
  // Check if string has been set
  if (filename.empty())
    throw DataException("Missing input file or directory");

  // Check if the parameter is the name of a directory
  struct stat stat_p;
  if (stat(filename.c_str(), &stat_p))
    // Can't verify the status
    throw RuntimeException("Couldn't open input file '" + filename + "'");
  else if (stat_p.st_mode & S_IFDIR)
  {
    // Data is a directory: loop through all *.xml files now. No recursion in
    // subdirectories is done.
    // The code is unfortunately different for Windows & Linux. Sigh...
  #ifdef _MSC_VER
    string f = filename + "\\*.xml";
    WIN32_FIND_DATA dir_entry_p;
    HANDLE h = FindFirstFile(f.c_str(), &dir_entry_p);
    if (h == INVALID_HANDLE_VALUE)
      throw RuntimeException("Couldn't open input file '" + f + "'");
    do
    {
      f = filename + '/' + dir_entry_p.cFileName;
      XMLInputFile(f.c_str()).parse(pRoot);
    }
    while (FindNextFile(h, &dir_entry_p));
    FindClose(h);
  #elif HAVE_DIRENT_H
    struct dirent *dir_entry_p;
    DIR *dir_p = opendir(filename.c_str());
    while (nullptr != (dir_entry_p = readdir(dir_p)))
    {
      int n = NAMLEN(dir_entry_p);
      if (n > 4 && !strcmp(".xml", dir_entry_p->d_name + n - 4))
      {
        string f = filename + '/' + dir_entry_p->d_name;
        XMLInputFile(f.c_str()).parse(pRoot, validate);
      }
    }
    closedir(dir_p);
  #else
    throw RuntimeException("Can't process a directory on your platform");
  #endif
  }
  else
  {
    // Normal file
    // Parse the file
    XMLCh *f = xercesc::XMLString::transcode(filename.c_str());
    xercesc::LocalFileInputSource in(f);
    xercesc::XMLString::release(&f);
    XMLInput::parse(in, pRoot, validate);
  }
}

} // end namespace
} // end namespace
