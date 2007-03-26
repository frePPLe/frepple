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

/* Uncomment the next line to create a lot of debugging messages during
 * the parsing of XML-data. */
//#define PARSE_DEBUG

namespace frepple
{


const XMLOutput::content_type XMLOutput::STANDARD = 1;
const XMLOutput::content_type XMLOutput::PLAN = 2;
const XMLOutput::content_type XMLOutput::PLANDETAIL = 4;


void 	XMLInput::processingInstruction
(const XMLCh *const target, const XMLCh *const data)
{
  char* type = XMLString::transcode(target);
  char* value = XMLString::transcode(data);
  XMLinstruction *x = NULL;
  try
  {
    // Lookup the class
    MetaCategory::ClassMap::const_iterator j =
      XMLinstruction::metadata.classes.find(XMLtag::hash(type));
    if (j == XMLinstruction::metadata.classes.end())
    {
      string msg = string("Unknown processing instruction ") + type;
      XMLString::release(&type);
      XMLString::release(&value);
      throw LogicException(msg);
    }
    x = dynamic_cast<XMLinstruction*>(j->second->factoryMethodDefault());
    try {x->processInstruction(*this, value);}
    catch (DataException e)
    {
      if (abortOnDataException)
      {
        XMLString::release(&type);
        XMLString::release(&value);
        throw;
      }
      else cout << "Continuing after data error: " << e.what() << endl;
    }
    delete x;
    XMLString::release(&type);
    XMLString::release(&value);
  }
  catch (...)
  {
    delete x;
    XMLString::release(&type);
    XMLString::release(&value);
    throw;
  }
}


void XMLInput::startElement(const XMLCh* const uri, const XMLCh* const n,
    const XMLCh* const qname, const Attributes& atts)
{
  // Validate the state
  assert(!states.empty());

  // Check for excessive number of open objects
  if (numElements >= maxdepth)
    throw DataException("XML-document with elements nested excessively deep");

  // Push the element on the stack
  XMLElement *pElement = &m_EStack[numElements+1];
  pElement->initialize(n);

  // Store a pointer to the attributes
  attributes = &atts;

  switch (states.top())
  {
    case SHUTDOWN:
      // STATE: Parser is shutting down, and we can ignore all input that
      // is still coming
      return;

    case IGNOREINPUT:
      // STATE: Parser is ignoring a part of the input
      if (pElement->getTagHash() == endingHashes.top())
        // Increase the count of occurences before the ignore section ends
        ++ignore;
      ++numElements;
      return;

    case INIT:
      // STATE: The only time the parser comes in this state is when we read
      // opening tag of the ROOT tag.
#ifdef PARSE_DEBUG
      if (getCurrentObject())
        cout << "Initialize root tag for reading object "
        << getCurrentObject() << " ("
        << typeid(*getCurrentObject()).name() << ")" << endl;
      else
        cout << "Initialize root tag for reading object NULL" << endl;
#endif
      states.top() = READOBJECT;
      endingHashes.push(pElement->getTagHash());
      // Note that there is no break or return here. We also execute the
      // statements of the following switch-case.

    case READOBJECT:
      // STATE: Parser is reading data elements of an object
      // Debug
#ifdef PARSE_DEBUG
      cout << "   Start element " << pElement->getName()
      << " - object " << getCurrentObject() << endl;
#endif

      // Call the handler of the object
      assert(!m_EHStack.empty());
      try { getCurrentObject()->beginElement(*this, *pElement); }
      catch (DataException e)
      {
        if (abortOnDataException) throw;
        else cout << "Continuing after data error: " << e.what() << endl;
      }

      // We only increase the number of elements at the very end. Otherwise
      // the method getParentElement() returns the wrong element.
      // We increment by 2 to include also an element for the attributes that
      // will be processed in the next loop.
      numElements += 2;

      // Now process all attributes. For attributes we only call the
      // endElement() member and skip the beginElement() method.
      if (states.top() != IGNOREINPUT)
        for (unsigned int i=0, cnt=atts.getLength(); i<cnt; i++)
        {
          char* val = XMLString::transcode(atts.getValue(i));
          m_EStack[numElements].initialize(atts.getQName(i));
          m_EStack[numElements].setData(val);
          #ifdef PARSE_DEBUG
          char* attname = XMLString::transcode(atts.getQName(i));
          cout << "   Processing attribute " << attname
          << " - object " << getCurrentObject() << endl;
          XMLString::release(&attname);
          #endif
          try { getCurrentObject()->endElement(*this, m_EStack[numElements]); }
          catch (DataException e)
          {
            if (abortOnDataException) throw;
            else cout << "Continuing after data error: " << e.what() << endl;
          }
          XMLString::release(&val);
          // Stop processing attributes if we are now in the ignore mode
          if (states.top() == IGNOREINPUT) break;
        }
      // Remove element used for attribute processing
      --numElements;
  }  // End of switch statement

  // Outside of this handler, no attributes are available
  attributes = NULL;
}


void XMLInput::endElement(const XMLCh* const uri,
    const XMLCh* const s,
    const XMLCh* const qname)
{
  // Validate the state
  assert(numElements >= 0);
  assert(!states.empty());
  assert(numElements < maxdepth);

  // Remove an element from the stack
  XMLElement *pElement = &(m_EStack[numElements--]);

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
      cout << "   End element " << pElement->getName()
      << " - IGNOREINPUT state" << endl;
#endif
      // Continue if we aren't dealing with the tag being ignored
      if (pElement->getTagHash() != endingHashes.top()) return;
      if (ignore == 0)
      {
        // Finished ignoring now
        states.pop();
        endingHashes.pop();
#ifdef PARSE_DEBUG
        cout << "Finish IGNOREINPUT state" << endl;
#endif
      }
      else
        --ignore;
      break;

    case READOBJECT:
      // STATE: Parser is reading data elements of an object
#ifdef PARSE_DEBUG
      cout << "   End element " << pElement->getName()
      << " - object " << getCurrentObject() << endl;
#endif

      // Check if we finished with the current handler
      assert(!m_EHStack.empty());
      if (pElement->getTagHash() == endingHashes.top())
      {
        // Call the ending handler of the Object, with a special
        // flag to specify that this object is now ended
        objectEnded = true;
        try { getCurrentObject()->endElement(*this, *pElement); }
        catch (DataException e)
        {
          if (abortOnDataException) throw;
          else cout << "Continuing after data error: " << e.what() << endl;
        }
        objectEnded = false;
#ifdef PARSE_DEBUG
        cout << "Finish reading object " << getCurrentObject() << endl;
#endif
        // Pop from the handler object stack
        prev = getCurrentObject();
        LockManager::getManager().releaseWriteLock(prev);
        m_EHStack.pop();
        endingHashes.pop();

        // Pop from the state stack
        states.pop();
        if (m_EHStack.empty())
          shutdown();
        else
        {
          // Call also the endElement function on the owning object
          try { getCurrentObject()->endElement(*this, *pElement); }
          catch (DataException e)
          {
            if (abortOnDataException) throw;
            else cout << "Continuing after data error: " << e.what() << endl;
          }
#ifdef PARSE_DEBUG
          cout << "   End element " << pElement->getName()
          << " - object " << getCurrentObject() << endl;
#endif
        }
      }
      else
        // This tag is not the ending tag of an object
        // Call the function of the Object
        try { getCurrentObject()->endElement(*this, *pElement); }
        catch (DataException e)
        {
          if (abortOnDataException) throw;
          else cout << "Continuing after data error: " << e.what() << endl;
        }
  }
}


void XMLInput::characters(const XMLCh *const c, const unsigned int n)
{
  // No data capture during the ignore state
  if (states.top()==IGNOREINPUT) return;

  // Process the data
  char* name = XMLString::transcode(c);
  m_EStack[numElements].addData(name, strlen(name));
  XMLString::release(&name);
}


void XMLInput::warning(const SAXParseException& exception)
{
  char* message = XMLString::transcode(exception.getMessage());
  cout << "Warning: " << message
  << " at line: " << exception.getLineNumber() << endl;
  XMLString::release(&message);
}


DECLARE_EXPORT void XMLInput::readto(Object * pPI)
{
  // Keep track of the tag where this object will end
  assert(numElements >= -1);
  endingHashes.push(m_EStack[numElements+1].getTagHash());
  if (pPI)
  {
    // Push a new object on the handler stack
#ifdef PARSE_DEBUG
    cout << "Start reading object " << pPI
    << " (" << typeid(*pPI).name() << ")" << endl;
#endif
    prev = getCurrentObject();
    m_EHStack.push(make_pair(pPI, static_cast<void*>(NULL)));
    states.push(READOBJECT);
  }
  else
  {
    // Ignore the complete content of this element
#ifdef PARSE_DEBUG
    cout << "Start ignoring input" << endl;
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
  cout << "   Forcing a shutdown - SHUTDOWN state" << endl;
#endif

  // Change the state
  states.push(SHUTDOWN);

  // Done if we have no elements on the stack, i.e. a normal end.
  if (numElements<0) return;

  // Call the ending handling of all objects on the stack
  // This allows them to finish off in a valid state, and delete any temporary
  // objects they may have allocated.
  objectEnded = true;
  m_EStack[numElements].initialize("Not a real tag");
  while (!m_EHStack.empty())
  {
    try { getCurrentObject()->endElement(*this, m_EStack[numElements]); }
    catch (DataException e)    // @todo this exception handler can leak locked objects
    {
      if (abortOnDataException) throw;
      else cout << "Continuing after data error: " << e.what() << endl;
    }
    LockManager::getManager().releaseWriteLock(getCurrentObject());
    m_EHStack.pop();
  }
}


void XMLInput::reset()
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
    if (objectEnded) m_EHStack.pop();
    objectEnded = true;
    m_EStack[++numElements].initialize("Not a real tag");
    while (!m_EHStack.empty())
    {
      try { getCurrentObject()->endElement(*this, m_EStack[numElements]); }
      catch (DataException e)  //@todo leaks locks...
      {
        if (abortOnDataException) throw;
        else cout << "Continuing after data error: " << e.what() << endl;
      }
      LockManager::getManager().releaseWriteLock(getCurrentObject());
      m_EHStack.pop();
    }
  }

  // Cleanup of stacks
  while (!states.empty()) states.pop();
  while (!endingHashes.empty()) endingHashes.pop();

  // Set all variables back to their starting values
  numElements = -1;
  ignore = 0;
  objectEnded = false;
  attributes = NULL;
}


void XMLInput::parse(InputSource &in, Object *pRoot, bool validate)
{
  try
  {
    // Create a Xerces parser
    parser = XMLReaderFactory::createXMLReader();

    // Set the features of the parser. A bunch of the options are dependent
    // on whether we want to validate the input or not.
    parser->setProperty(XMLUni::fgXercesScannerName, const_cast<XMLCh*>
        (validate ? XMLUni::fgSGXMLScanner : XMLUni::fgWFXMLScanner));
    parser->setFeature(XMLUni::fgSAX2CoreNameSpaces, validate);
    parser->setFeature(XMLUni::fgSAX2CoreValidation, validate);
    parser->setFeature(XMLUni::fgSAX2CoreNameSpacePrefixes, false);
    parser->setFeature(XMLUni::fgXercesIdentityConstraintChecking, false);
    parser->setFeature(XMLUni::fgXercesDynamic, false);
    parser->setFeature(XMLUni::fgXercesSchema, validate);
    parser->setFeature(XMLUni::fgXercesSchemaFullChecking, false);
    parser->setFeature(XMLUni::fgXercesValidationErrorAsFatal,true);
    parser->setFeature(XMLUni::fgXercesIgnoreAnnotations,true);

    if (validate)
    {
      // Specify the no-namespace schema file
      string schema = Environment::getHomeDirectory();
      schema += "frepple.xsd";
      XMLCh *c = XMLString::transcode(schema.c_str());
      parser->setProperty(
        XMLUni::fgXercesSchemaExternalNoNameSpaceSchemaLocation, c
      );
      XMLString::release(&c);
      // Preload the schema @todo
      // Xerces stores the grammars on the parser, which we dynamically create and
      // destroy. Preloading the schema requires using a parser pool.
      //Grammar *g =
      //   parser->loadGrammar("plan.xsd", Grammar::SchemaGrammarType, true);
    }

    // If we are reading into a NULL object, there is no need to use a
    // content handler or a handler stack.
    if (pRoot)
    {
      // Set the event handler. If we are reading into a NULL object, there is
      // no need to use a content handler.
      parser->setContentHandler(this);

      // Get the parser to read data into the object pRoot.
      m_EHStack.push(make_pair(pRoot,static_cast<void*>(NULL)));
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
  catch (const XMLException& toCatch)
  {
    char* message = XMLString::transcode(toCatch.getMessage());
    string msg(message);
    XMLString::release(&message);
    reset();
    throw RuntimeException("Parsing error: " + msg);
  }
  catch (const SAXParseException& toCatch)
  {
    char* message = XMLString::transcode(toCatch.getMessage());
    ostringstream msg;
    if (toCatch.getLineNumber() > 0)
      msg << "Parsing error: " << message << " at line " << toCatch.getLineNumber();
    else
      msg << "Parsing error: " << message;
    XMLString::release(&message);
    reset();
    throw RuntimeException(msg.str());
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

  // Execute the commands defined in the input stream.
  // The commands are executed only after a successful parsing.
  executeCommands();
}


DECLARE_EXPORT string XMLOutput::XMLEscape(const char *p)
{
  string ret(p);
  for (string::size_type pos = ret.find_first_of("&<>\"\'", 0);
      pos < string::npos;
      pos = ret.find_first_of("&<>\"\'", pos))
  {
    switch (ret[pos])
    {
      case '&': ret.replace(pos,1,"&amp;",5); pos+=5; break;
      case '<': ret.replace(pos,1,"&lt;",4); pos+=4; break;
      case '>': ret.replace(pos,1,"&gt;",4); pos+=4; break;
      case '"': ret.replace(pos,1,"&quot;",6); pos+=6; break;
      case '\'': ret.replace(pos,1,"&apos;",6); pos+=6;
    }
  }
  return ret;
}


DECLARE_EXPORT void XMLOutput::incIndent()
{
  indentstring[m_nIndent++] = '\t';
  if (m_nIndent > 40) m_nIndent = 40;
  indentstring[m_nIndent] = '\0';
}


DECLARE_EXPORT void XMLOutput::decIndent()
{
  if (--m_nIndent < 0) m_nIndent = 0;
  indentstring[m_nIndent] = '\0';
}


DECLARE_EXPORT void XMLOutput::writeElement
(const XMLtag& tag, const Object* object, mode m)
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
    // Choose wether to save a reference of the object
    object->writeElement(this, tag, numParents>2 ? REFERENCE : DEFAULT);  // @todo not nice and generic

  // Adjust current and parent object pointer
  --numParents;
  currentObject = parentObject;
  parentObject = previousParent;
}


DECLARE_EXPORT void XMLOutput::writeElementWithHeader(const XMLtag& tag, const Object* object)
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
  object->writeElement(this, tag, NOHEADER);

  // Adjust current and parent object pointer
  currentObject = NULL;
  parentObject = NULL;
}


DECLARE_EXPORT void XMLOutput::writeHeader(const XMLtag& tag)
{
  // There should not be any saved objects yet
  if (numObjects > 0)
    throw LogicException("Can't have multiple headers in a document");
  assert(!parentObject);
  assert(!currentObject);

  // Write the first line and the opening tag
  writeString(getHeaderStart());
  BeginObject(tag, getHeaderAtts());

  // Fake a dummy parent
  numParents += 2;   // @todo not nice and generic
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


DECLARE_EXPORT string XMLElement::getName() const
{
  XMLtag::tagtable::const_iterator i = XMLtag::getTags().find(m_dwTagHash);
  if (i == XMLtag::getTags().end())
    throw LogicException("Undefined element tag");
  return i->second->getName();
}


DECLARE_EXPORT XMLtag::XMLtag(string name) : strName(name)
{
  // Error condition: name is empty
  if (name.empty()) throw LogicException("Creating XMLtag without name");

  // Create a number of variations of the tag name
  strStartElement = string("<") + name;
  strEndElement = string("</") + name + ">\n";
  strElement = string("<") + name + ">";
  strAttribute = string(" ") + name + "=\"";

  // Compute the hash value
  dw = hash(name.c_str());

  // Create a properly encoded Xerces string
  XMLPlatformUtils::Initialize();
  xmlname =XMLString::transcode(name.c_str());

  // Verify that the hash is "perfect".
  // To be thread-safe we make sure only a single thread at a time
  // can execute this check.
  static Mutex dd;
  {
    ScopeMutexLock l(dd);
    tagtable::const_iterator i = getTags().find(dw);
    if (i!=getTags().end() && i->second->getName()!=name)
      throw LogicException("Tag XML-tag hash function clashes for "
          + i->second->getName() + " and " + name);
    getTags().insert(make_pair(dw,this));
  }
}


DECLARE_EXPORT XMLtag::~XMLtag()
{
  // Remove from the tag list
  tagtable::iterator i = getTags().find(dw);
  if (i!=getTags().end()) getTags().erase(i);

  // Destroy the xerces string
  XMLString::release(&xmlname);
  XMLPlatformUtils::Terminate();
}


DECLARE_EXPORT const XMLtag& XMLtag::find(char const* name)
{
  tagtable::const_iterator i = getTags().find(hash(name));
  return *(i!=getTags().end() ? i->second : new XMLtag(name));
}


DECLARE_EXPORT XMLtag::tagtable& XMLtag::getTags()
{
  static tagtable alltags;
  return alltags;
}


DECLARE_EXPORT void XMLtag::printTags()
{
  for (tagtable::iterator i = getTags().begin(); i != getTags().end(); ++i)
    cout << i->second->getName() << "   " << i->second->dw << endl;
}


DECLARE_EXPORT void XMLInput::executeCommands()
{
  try { cmds.execute(); }
  catch (...)
  {
    try { throw; }
    catch (exception& e)
    {cout << "Error executing commands: " << e.what() << endl;}
    catch (...)
    {cout << "Error executing commands: Unknown exception type" << endl;}
    throw;
  }
}

}
