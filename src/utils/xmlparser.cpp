/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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

DECLARE_EXPORT const Serializer::content_type Serializer::STANDARD = 1;
DECLARE_EXPORT const Serializer::content_type Serializer::PLAN = 2;
DECLARE_EXPORT const Serializer::content_type Serializer::PLANDETAIL = 4;
xercesc::XMLTranscoder* XMLInput::utf8_encoder = NULL;


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


DECLARE_EXPORT XMLInput::XMLInput(unsigned short maxNestedElmnts)
  : parser(NULL), maxdepth(maxNestedElmnts), m_EStack(maxNestedElmnts+2),
    numElements(-1), ignore(0), objectEnded(false),
    abortOnDataException(true), attributes(NULL, this)
{
  if (!utf8_encoder)
  {
    xercesc::XMLTransService::Codes resCode;
    utf8_encoder = xercesc::XMLPlatformUtils::fgTransService->makeNewTranscoderFor("UTF-8", resCode, 4*1024);
    if (!XMLInput::utf8_encoder)
      logger << "Can't initialize UTF-8 transcoder: reason " << resCode << endl;
  }
}


DECLARE_EXPORT void  XMLInput::processingInstruction
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
        else logger << "Continuing after data error: " << e.what() << endl;
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


DECLARE_EXPORT void XMLInput::startElement(const XMLCh* const uri,
  const XMLCh* const n, const XMLCh* const qname,
  const xercesc::Attributes& atts)
{
  // Validate the state
  assert(!states.empty());

  // Check for excessive number of open objects
  if (numElements >= maxdepth)
    throw DataException("XML-document with elements nested excessively deep");

  // Push the element on the stack
  datapair *pElement = &m_EStack[numElements+1];
  pElement->first.reset(n);
  pElement->second.reset();

  // Store a pointer to the attributes
  attributes.setAtts(&atts);

  switch (states.top())
  {
    case SHUTDOWN:
      // STATE: Parser is shutting down, and we can ignore all input that
      // is still coming
      return;

    case IGNOREINPUT:
      // STATE: Parser is ignoring a part of the input
      if (pElement->first.getHash() == endingHashes.top())
        // Increase the count of occurences before the ignore section ends
        ++ignore;
      ++numElements;
      return;

    case INIT:
      // STATE: The only time the parser comes in this state is when we read
      // opening tag of the ROOT tag.
#ifdef PARSE_DEBUG
      if (!m_EHStack.empty())
        logger << "Initialize root tag for reading object "
            << getCurrentObject() << " ("
            << typeid(*getCurrentObject()).name() << ")" << endl;
      else
        logger << "Initialize root tag for reading object NULL" << endl;
#endif
      states.top() = READOBJECT;
      endingHashes.push(pElement->first.getHash());
      // Note that there is no break or return here. We also execute the
      // statements of the following switch-case.

    case READOBJECT:
      // STATE: Parser is reading data elements of an object
      // Debug
#ifdef PARSE_DEBUG
      logger << "   Start element " << pElement->first.getName()
          << " - object " << getCurrentObject() << endl;
#endif

      // Call the handler of the object
      assert(!m_EHStack.empty());
      try {getCurrentObject()->beginElement(*this, pElement->first);}
      catch (const DataException& e)
      {
        if (abortOnDataException) throw;
        else logger << "Continuing after data error: " << e.what() << endl;
      }

      // Now process all attributes. For attributes we only call the
      // endElement() member and skip the beginElement() method.
      numElements += 1;
      if (states.top() != IGNOREINPUT)
        for (XMLSize_t i=0, cnt=atts.getLength(); i<cnt; i++)
        {
          char* val = transcodeUTF8(atts.getValue(i));
          m_EStack[numElements+1].first.reset(atts.getLocalName(i));
          m_EStack[numElements+1].second.setData(val);
#ifdef PARSE_DEBUG
          char* attname = xercesc::XMLString::transcode(atts.getQName(i));
          logger << "   Processing attribute " << attname
              << " - object " << getCurrentObject() << endl;
          xercesc::XMLString::release(&attname);
#endif
          try {getCurrentObject()->endElement(*this, m_EStack[numElements+1].first, m_EStack[numElements+1].second);}
          catch (const DataException& e)
          {
            if (abortOnDataException) throw;
            else logger << "Continuing after data error: " << e.what() << endl;
          }
          // Stop processing attributes if we are now in the ignore mode
          if (states.top() == IGNOREINPUT) break;
        }
  }  // End of switch statement

  // Outside of this handler, no attributes are available
  attributes.setAtts(NULL);
}


DECLARE_EXPORT void XMLInput::endElement(const XMLCh* const uri,
    const XMLCh* const s,
    const XMLCh* const qname)
{
  // Validate the state
  assert(numElements >= 0);
  assert(!states.empty());
  assert(numElements < maxdepth);

  // Remove an element from the stack
  datapair *pElement = &(m_EStack[numElements--]);

  switch (states.top())
  {
    case INIT:
      // This should never happen!
      throw LogicException("Unreachable code reached");

    case SHUTDOWN:
      // STATE: Parser is shutting down, and we can ignore all input that is
      // still coming
      return;

    case IGNOREINPUT:
      // STATE: Parser is ignoring a part of the input
#ifdef PARSE_DEBUG
      logger << "   End element " << pElement->first.getName()
          << " - IGNOREINPUT state" << endl;
#endif
      // Continue if we aren't dealing with the tag being ignored
      if (pElement->first.getHash() != endingHashes.top()) return;
      if (ignore == 0)
      {
        // Finished ignoring now
        states.pop();
        endingHashes.pop();
#ifdef PARSE_DEBUG
        logger << "Finish IGNOREINPUT state" << endl;
#endif
      }
      else
        --ignore;
      break;

    case READOBJECT:
      // STATE: Parser is reading data elements of an object
#ifdef PARSE_DEBUG
      logger << "   End element " << pElement->first.getName()
          << " - object " << getCurrentObject() << endl;
#endif

      // Check if we finished with the current handler
      assert(!m_EHStack.empty());
      if (pElement->first.getHash() == endingHashes.top())
      {
        // Call the ending handler of the Object, with a special
        // flag to specify that this object is now ended
        objectEnded = true;
        try
        {
          getCurrentObject()->endElement(*this, pElement->first, pElement->second);
          if (userexit) userexit.call(getCurrentObject());
        }
        catch (const DataException& e)
        {
          if (abortOnDataException) throw;
          else logger << "Continuing after data error: " << e.what() << endl;
        }
        objectEnded = false;
#ifdef PARSE_DEBUG
        logger << "Finish reading object " << getCurrentObject() << endl;
#endif
        // Pop from the handler object stack
        prev = getCurrentObject();
        m_EHStack.pop_back();
        endingHashes.pop();

        // Pop from the state stack
        states.pop();
        if (m_EHStack.empty())
          shutdown();
        else
        {
          // Call also the endElement function on the owning object
          try {getCurrentObject()->endElement(*this, pElement->first, pElement->second);}
          catch (const DataException& e)
          {
            if (abortOnDataException) throw;
            else logger << "Continuing after data error: " << e.what() << endl;
          }
#ifdef PARSE_DEBUG
          logger << "   End element " << pElement->first.getName()
              << " - object " << getCurrentObject() << endl;
#endif
        }
      }
      else
        // This tag is not the ending tag of an object
        // Call the function of the Object
        try {getCurrentObject()->endElement(*this, pElement->first, pElement->second);}
        catch (const DataException& e)
        {
          if (abortOnDataException) throw;
          else logger << "Continuing after data error: " << e.what() << endl;
        }
  }
}


// Unfortunately the prototype for this handler function differs between
// Xerces-c 2.x and 3.x
#if XERCES_VERSION_MAJOR==2
DECLARE_EXPORT void XMLInput::characters(const XMLCh *const c, const unsigned int n)
#else
DECLARE_EXPORT void XMLInput::characters(const XMLCh *const c, const XMLSize_t n)
#endif
{
  // No data capture during the ignore state
  if (states.top()==IGNOREINPUT) return;

  // Process the data
  char* name = transcodeUTF8(c);
  m_EStack[numElements].second.addData(name, strlen(name));
}


DECLARE_EXPORT void XMLInput::warning(const xercesc::SAXParseException& e)
{
  char* message = xercesc::XMLString::transcode(e.getMessage());
  logger << "Warning: " << message;
  if (e.getLineNumber() > 0) logger << " at line: " << e.getLineNumber();
  logger << endl;
  xercesc::XMLString::release(&message);
}


DECLARE_EXPORT void XMLInput::fatalError(const xercesc::SAXParseException& e)
{
  char* message = xercesc::XMLString::transcode(e.getMessage());
  ostringstream ch;
  ch << message;
  if (e.getLineNumber() > 0) ch << " at line " << e.getLineNumber();
  xercesc::XMLString::release(&message);
  throw DataException(ch.str());
}


DECLARE_EXPORT void XMLInput::error(const xercesc::SAXParseException& e)
{
  char* message = xercesc::XMLString::transcode(e.getMessage());
  ostringstream ch;
  ch << message;
  if (e.getLineNumber() > 0) ch << " at line " << e.getLineNumber();
  xercesc::XMLString::release(&message);
  throw DataException(ch.str());
}


DECLARE_EXPORT void XMLInput::readto(Object * pPI)
{
  // Keep track of the tag where this object will end
  assert(numElements >= -1);
  endingHashes.push(m_EStack[numElements+1].first.getHash());
  if (pPI)
  {
    // Push a new object on the handler stack
#ifdef PARSE_DEBUG
    logger << "Start reading object " << pPI
        << " (" << typeid(*pPI).name() << ")" << endl;
#endif
    prev = getCurrentObject();
    m_EHStack.push_back(make_pair(pPI,static_cast<void*>(NULL)));
    states.push(READOBJECT);

    // Update the source field of the new object
    if (!source.empty())
    {
      HasSource *x = dynamic_cast<HasSource*>(pPI);
      if (x) x->setSource(source);
    }
  }
  else
  {
    // Ignore the complete content of this element
#ifdef PARSE_DEBUG
    logger << "Start ignoring input" << endl;
#endif
    states.push(IGNOREINPUT);
  }
}


void XMLInput::shutdown()
{
  // Already shutting down...
  if (states.empty() || states.top() == SHUTDOWN) return;

  // Message
#ifdef PARSE_DEBUG
  logger << "   Forcing a shutdown - SHUTDOWN state" << endl;
#endif

  // Change the state
  states.push(SHUTDOWN);

  // Done if we have no elements on the stack, i.e. a normal end.
  if (numElements<0) return;

  // Call the ending handling of all objects on the stack
  // This allows them to finish off in a valid state, and delete any temporary
  // objects they may have allocated.
  objectEnded = true;
  m_EStack[numElements].first.reset("Not a real tag");
  m_EStack[numElements].second.reset();
  while (!m_EHStack.empty())
  {
    try
    {
      getCurrentObject()->endElement(*this, m_EStack[numElements].first, m_EStack[numElements].second);
      if (userexit) userexit.call(getCurrentObject());
    }
    catch (const DataException& e)
    {
      if (abortOnDataException) throw;
      else logger << "Continuing after data error: " << e.what() << endl;
    }
    m_EHStack.pop_back();
  }
}


DECLARE_EXPORT void XMLInput::reset()
{
  // Delete the xerces parser object
  delete parser;
  parser = NULL;

  // Call the ending handling of all objects on the stack
  // This allows them to finish off in a valid state, and delete any temporary
  // objects they may have allocated.
  if (!m_EHStack.empty())
  {
    // The next line is to avoid calling the endElement handler twice for the
    // last object. E.g. endElement handler causes and exception, and as part
    // of the exception handling we call the reset method.
    if (objectEnded) m_EHStack.pop_back();
    objectEnded = true;
    m_EStack[++numElements].first.reset("Not a real tag");
    m_EStack[++numElements].second.reset();
    while (!m_EHStack.empty())
    {
      try
      {
        getCurrentObject()->endElement(*this, m_EStack[numElements].first, m_EStack[numElements].second);
        if (userexit) userexit.call(getCurrentObject());
      }
      catch (const DataException& e)
      {
        if (abortOnDataException) throw;
        else logger << "Continuing after data error: " << e.what() << endl;
      }
      m_EHStack.pop_back();
    }
  }

  // Cleanup of stacks
  while (!states.empty()) states.pop();
  while (!endingHashes.empty()) endingHashes.pop();

  // Set all variables back to their starting values
  numElements = -1;
  ignore = 0;
  objectEnded = false;
  attributes.setAtts(NULL);
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
    parser->setFeature(xercesc::XMLUni::fgXercesValidationErrorAsFatal,true);
    parser->setFeature(xercesc::XMLUni::fgXercesIgnoreAnnotations,true);

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

    // If we are reading into a NULL object, there is no need to use a
    // content handler or a handler stack.
    if (pRoot)
    {
      // Set the event handler. If we are reading into a NULL object, there is
      // no need to use a content handler.
      parser->setContentHandler(this);

      // Get the parser to read data into the object pRoot.
      m_EHStack.push_back(make_pair(pRoot,static_cast<void*>(NULL)));
      states.push(INIT);
    }

    // Set the error handler
    parser->setErrorHandler(this);

    // Parse the input
    parser->parse(in);
  }
  // Note: the reset() method needs to be called in all circumstances. The
  // reset method allows all objects to finish in a valid state and clean up
  // any memory they may have allocated.
  catch (const xercesc::XMLException& toCatch)
  {
    char* message = xercesc::XMLString::transcode(toCatch.getMessage());
    string msg(message);
    xercesc::XMLString::release(&message);
    reset();
    throw RuntimeException("Parsing error: " + msg);
  }
  catch (const exception& toCatch)
  {
    reset();
    ostringstream msg;
    msg << "Error during XML parsing: " << toCatch.what();
    throw RuntimeException(msg.str());
  }
  catch (...)
  {
    reset();
    throw RuntimeException(
      "Parsing error: Unexpected exception during XML parsing");
  }
  reset();
}


DECLARE_EXPORT void SerializerXML::escape(const string& x)
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


DECLARE_EXPORT void SerializerXML::incIndent()
{
  indentstring[m_nIndent++] = '\t';
  if (m_nIndent > 40) m_nIndent = 40;
  indentstring[m_nIndent] = '\0';
}


DECLARE_EXPORT void SerializerXML::decIndent()
{
  if (--m_nIndent < 0) m_nIndent = 0;
  indentstring[m_nIndent] = '\0';
}


DECLARE_EXPORT void Serializer::writeElement
(const Keyword& tag, const Object* object, mode m)
{
  // Avoid NULL pointers and skip hidden objects
  if (!object || object->getHidden()) return;

  // Adjust current and parent object pointer
  const Object *previousParent = parentObject;
  parentObject = currentObject;
  currentObject = object;
  ++numObjects;
  ++numParents;

  // Call the write method on the object
  if (m != DEFAULT)
    // Mode is overwritten
    object->writeElement(this, tag, m);
  else
    // Choose wether to save a reference of the object.
    // The root object can't be saved as a reference.
    object->writeElement(this, tag, numParents>2 ? REFERENCE : DEFAULT);

  // Adjust current and parent object pointer
  --numParents;
  currentObject = parentObject;
  parentObject = previousParent;
}


DECLARE_EXPORT void SerializerXML::writeElementWithHeader(const Keyword& tag, const Object* object)
{
  // Root object can't be null...
  if (!object)
    throw RuntimeException("Can't accept a NULL object as XML root");

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
  ++numParents;
  BeginObject(tag, getHeaderAtts());
  object->writeElement(this, tag, NOHEAD);

  // Adjust current and parent object pointer
  currentObject = NULL;
  parentObject = NULL;
}


DECLARE_EXPORT void SerializerXML::writeHeader(const Keyword& t)
{
  // Write the first line and the opening tag
  writeString(getHeaderStart());
  *m_fp << indentstring << t.stringStartElement() << " " << headerAtts << ">\n";
  incIndent();

  // Fake a dummy parent
  numParents += 2;
}


DECLARE_EXPORT void SerializerXML::writeHeader(const Keyword& t, const Keyword& t1, const string& val1)
{
  // Write the first line and the opening tag
  writeString(getHeaderStart());
  *m_fp << indentstring << t.stringStartElement() << " " << headerAtts
    << t1.stringAttribute() << val1 << "\">\n";
  incIndent();

  // Fake a dummy parent
  numParents += 2;
}


DECLARE_EXPORT const XMLElement* XMLAttributeList::get(const Keyword& key) const
{
  char* s = in->transcodeUTF8(atts->getValue(key.getXMLCharacters()));
  const_cast<XMLAttributeList*>(this)->result.setData(s ? s : "");
  return &result;
}


DECLARE_EXPORT bool XMLElement::getBool() const
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


DECLARE_EXPORT const char* Attribute::getName() const
{
  if (ch) return ch;
  Keyword::tagtable::const_iterator i = Keyword::getTags().find(hash);
  if (i == Keyword::getTags().end())
    throw LogicException("Undefined element keyword");
  return i->second->getName().c_str();
}


DECLARE_EXPORT Keyword::Keyword(const string& name) : strName(name)
{
  // Error condition: name is empty
  if (name.empty()) throw LogicException("Creating keyword without name");

  // Create a number of variations of the tag name   TODO GET RID OF THESE XML SPECIFIC SHIT
  strStartElement = string("<") + name;
  strEndElement = string("</") + name + ">\n";
  strElement = string("<") + name + ">";
  strAttribute = string(" ") + name + "=\"";

  // Compute the hash value
  dw = hash(name.c_str());

  // Create a properly encoded Xerces string
  xercesc::XMLPlatformUtils::Initialize();
  xmlname = xercesc::XMLString::transcode(name.c_str());

  // Verify that the hash is "perfect".
  check();
}


DECLARE_EXPORT Keyword::Keyword(const string& name, const string& nspace)
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

  // Compute the hash value
  dw = hash(name);

  // Create a properly encoded Xerces string
  xercesc::XMLPlatformUtils::Initialize();
  xmlname = xercesc::XMLString::transcode(string(nspace + ":" + name).c_str());

  // Verify that the hash is "perfect".
  check();
}


void Keyword::check()
{
  // To be thread-safe we make sure only a single thread at a time
  // can execute this check.
  static Mutex dd;
  {
    ScopeMutexLock l(dd);
    tagtable::const_iterator i = getTags().find(dw);
    if (i!=getTags().end() && i->second->getName()!=strName)
      throw LogicException("Tag XML-tag hash function clashes for "
          + i->second->getName() + " and " + strName);
    getTags().insert(make_pair(dw,this));
  }
}


DECLARE_EXPORT Keyword::~Keyword()
{
  // Remove from the tag list
  tagtable::iterator i = getTags().find(dw);
  if (i!=getTags().end()) getTags().erase(i);

  // Destroy the xerces string
  xercesc::XMLString::release(&xmlname);
  xercesc::XMLPlatformUtils::Terminate();
}


DECLARE_EXPORT const Keyword& Keyword::find(const char* name)
{
  tagtable::const_iterator i = getTags().find(hash(name));
  return *(i!=getTags().end() ? i->second : new Keyword(name));
}


DECLARE_EXPORT Keyword::tagtable& Keyword::getTags()
{
  static tagtable alltags;
  return alltags;
}


DECLARE_EXPORT hashtype Keyword::hash(const char* c)
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


DECLARE_EXPORT hashtype Keyword::hash(const XMLCh* t)
{
  char* c = xercesc::XMLString::transcode(t);
  if (c == 0 || *c == 0)
  {
    xercesc::XMLString::release(&c);
    return 0;
  }

  // Compute hash
  const char* curCh = c;
  hashtype hashVal = *curCh;
  while (*curCh)
    hashVal = (hashVal * 37) + (hashVal >> 24) + *curCh++;

  // Divide by modulus
  xercesc::XMLString::release(&c);
  return hashVal % 954991;
}


DECLARE_EXPORT void Keyword::printTags()
{
  for (tagtable::iterator i = getTags().begin(); i != getTags().end(); ++i)
    logger << i->second->getName() << "   " << i->second->dw << endl;
}


DECLARE_EXPORT void XMLInputFile::parse(Object *pRoot, bool validate)
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
    while (NULL != (dir_entry_p = readdir(dir_p)))
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
