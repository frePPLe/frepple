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
#include <sys/stat.h>

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
    if(h == INVALID_HANDLE_VALUE)
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
    XMLCh *f = XMLString::transcode(filename.c_str());
    LocalFileInputSource in(f);
    XMLString::release(&f);
    XMLInput::parse(in, pRoot, validate);
  }
}


void CSVInput::processInstruction(XMLInput &i, const char *d)
{

  clog << "processing instruction " << d << endl;

  Object* pRoot = i.getCurrentObject();

  XMLElement fields[10];   // xxx use Attributes instead
  fields[0].initialize("NAME");
  fields[1].initialize("DESCRIPTION");
  fields[2].initialize("CATEGORY");

  ifstream in("test.csv");
  unsigned int linecount = 0;
  if (!in) throw DataException("Can't open data file");
  char buffer[1000];
  while (!in.eof())
  {
    // Read the next line
    in.getline(buffer,1000);
    ++linecount;

    // Skip comment lines and empty lines
    if (*buffer == comment || !*buffer) continue;

    // Split the line in different fields
    char *datafields[100];
    buffer[999] = '\0';
    unsigned int fieldcount = 0;
    datafields[0] = buffer;
    for (char *c = buffer; *c; ++c)
      if (*c == fieldseparator)
      {
        *c = '\0';
        datafields[++fieldcount] = c + 1;
      }
    if (fieldcount > 10) 
      clog << "Ignoring excess data fields on line " << linecount << endl;

    //  xxx  create master object
    // xxx parent element also needs to be set correct
    // ABSOLUTELY NEED TO USE ATTS... Can't simulate it...
    // i.startElement("ITEM", "ITEM", "NAME", NULL);  

    // Process the fields
    for (unsigned int j=0; j<=fieldcount; ++j)
      try
      {
        clog << "puree " << linecount << ", field " 
          << fields[j].getName() << " -" << datafields[j] << "-" << endl;
        //pRoot->beginElement(*this, fields[j]);
        fields[j].setData(datafields[j]);
        //pRoot->endElement(*this, fields[j]);
      }
      catch (const DataException& toCatch)
      {
        ostringstream msg;
        msg << "Data error during CSV reading on line " << linecount 
          << ": " << toCatch.what();
      }
      catch (...)
      {
        in.close();
        throw;
      }
  }
  in.close();

  // xxx: maintain getParentElement, PrevObject, prevElement, isObjectEnd, 
  // getAttributes, readto, shutdown, topObject, setUserArea, getUserArea,
  // ...

  // xxx: Build more abstract input processor, common for xml and csv input

  // xxx: Use a template xml file to define the fields

  // xxx: could we create a new type of xerces parser instead???
}


void CSVInput::startElement (const XMLCh* const a, const XMLCh* const b,
      const XMLCh* const c, const Attributes& d)
{
  char* name = XMLString::transcode(b);
  clog << "start " << name << endl;
  XMLString::release(&name);
}

void CSVInput::endElement
      (const XMLCh* const a, const XMLCh* const b, const XMLCh* const qname)
{
  char* name = XMLString::transcode(b);
  clog << "end " << name << endl;
  XMLString::release(&name);
}

void CSVInput::characters(const XMLCh *const a, const unsigned int b)
{
  char* name = XMLString::transcode(a);
  clog << "char " << name << endl;
  XMLString::release(&name);
}

void CSVInput::warning (const SAXParseException&)
{
  clog << "warn" << endl;
}

void CSVInput::readTemplate
  (string &header, string &rep, string &footer, Object *pRoot)
{
  string in = header + rep + footer;
  SAX2XMLReader* parser;
   try {
    // Create a Xerces parser
    parser = XMLReaderFactory::createXMLReader();

    // Set the features of the parser. A bunch of the options are dependent
    // on whether we want to validate the input or not.
    parser->setProperty(XMLUni::fgXercesScannerName, 
      const_cast<XMLCh*>(XMLUni::fgSGXMLScanner));
    parser->setFeature(XMLUni::fgSAX2CoreNameSpaces, true);
    parser->setFeature(XMLUni::fgSAX2CoreValidation, true);
    parser->setFeature(XMLUni::fgSAX2CoreNameSpacePrefixes, false);
    parser->setFeature(XMLUni::fgXercesIdentityConstraintChecking, false);   
    parser->setFeature(XMLUni::fgXercesDynamic, false);
    parser->setFeature(XMLUni::fgXercesSchema, true);
    parser->setFeature(XMLUni::fgXercesSchemaFullChecking, false);
    parser->setFeature(XMLUni::fgXercesValidationErrorAsFatal,true);

    string schema = Environment::getHomeDirectory();
    schema += "frepple.xsd";
    XMLCh *c = XMLString::transcode(schema.c_str());
    parser->setProperty(
      XMLUni::fgXercesSchemaExternalNoNameSpaceSchemaLocation, c
      );
    XMLString::release(&c);

    // Set the event handler. 
    parser->setContentHandler(this);

    // Set the error handler
    parser->setErrorHandler(this);

    // Parse the input
    MemBufInputSource a(
        reinterpret_cast<const XMLByte*>(in.c_str()),
        static_cast<const unsigned int>(in.size()),
        "xml memory template",
        false);
    parser->parse(a);
  }
  // Note: the reset() method needs to be called in all circumstances. The
  // reset method allows all objects to finish in a valid state and clean up
  // any memory they may have allocated.
  catch (const XMLException& toCatch)
  {
    char* message = XMLString::transcode(toCatch.getMessage());
    string msg(message);
    XMLString::release(&message);
    throw RuntimeException("Parsing error: " + msg);
  }
  catch (const SAXParseException& toCatch)
  {
    char* message = XMLString::transcode(toCatch.getMessage());
    ostringstream msg(message);
    if (toCatch.getLineNumber() > 0) 
      msg << " at line " << toCatch.getLineNumber();
    XMLString::release(&message);
    throw RuntimeException("Parsing error: " + msg.str());
  }
  catch (const exception& toCatch)
  {
    ostringstream msg;
    msg << "Error during XML parsing: " << toCatch.what();
    throw RuntimeException(msg.str());
  }
  catch (...)
  {
    throw RuntimeException(
      "Parsing error: Unexpected exception during XML parsing");
  }
}


} // end namespace
