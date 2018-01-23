/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
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

/** @file xml.h
  * @brief Header file for XML processing.
  */
#pragma once
#ifndef FREPPLE_XML_H
#define FREPPLE_XML_H

// Header files for the Xerces-c XML parser.
#ifndef DOXYGEN
#include <xercesc/util/XercesVersion.hpp>
#if _XERCES_VERSION < 30200
#define XERCES_STATIC_LIBRARY
#endif
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

namespace frepple
{

namespace utils
{

// Forward declarations
class XMLInput;


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
class XMLInput : public DataInput, public NonCopyable,  private xercesc::DefaultHandler
{
  private:
    /** This variable defines the maximum depth of the object creation stack.
      * This maximum is intended to protect us from malicious malformed
      * xml-documents, and also for allocating efficient data structures for
      * the parser.
      */
    static const int maxobjects = 30;
    static const int maxdata = 200;

  public:
    struct fld
    {
      const MetaFieldBase* field;
      XMLData value;
      string name;
      hashtype hash;
    };

  private:
    /** A transcoder to encoding to UTF-8. */
    static xercesc::XMLTranscoder* utf8_encoder;

    /** A pointer to an XML parser for processing the input. */
    xercesc::SAX2XMLReader* parser = nullptr;

    /** Stack of objects and their data fields. */
    struct obj
    {
      const MetaClass* cls;
      Object* object;
      int start;
      hashtype hash;
    };
    vector<obj> objects;

    /** Stack of fields already read. */
    vector<fld> data;

    /** Index into the objects stack. */
    int objectindex = -1;

    /** Index into the data field stack. */
    int dataindex = -1;

    /** A variable to keep track of the size of the element stack. It is used
      * together with the variable m_EStack.
      */
    short numElements = -1;

    /** Controls wether or not we need to process character data. */
    bool reading = false;

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
    bool abortOnDataException = true;

    /** This field counts how deep we are in a nested series of ignored input.
      * It is represented as a counter since the ignored element could contain
      * itself.
      */
    unsigned short ignore = 0;

    /** A buffer used for transcoding XML data. */
    char encodingbuffer[4*1024];

    /** Handler called when a new element tag is encountered.
      * It pushes a new element on the stack and calls the current handler.
      */
    void startElement (const XMLCh* const, const XMLCh* const,
        const XMLCh* const, const xercesc::Attributes&);

    /** Handler called when closing element tag is encountered.
      * If this is the closing tag for the current event handler, pop it
      * off the handler stack. If this empties the stack, shut down parser.
      * Otherwise, just feed the element with the already completed
      * data section to the current handler, then pop it off the element
      * stack.
      */
    void endElement
    (const XMLCh* const, const XMLCh* const, const XMLCh* const);

    /** Handler called when character data are read in.
      * The data string is add it to the current element data.
      */
    void characters(const XMLCh *const, const XMLSize_t);

    /** Handler called by Xerces in fatal error conditions. It throws an
      * exception to abort the parsing procedure. */
    void fatalError (const xercesc::SAXParseException&);

    /** Handler called by Xercess when reading a processing instruction. The
      * handler looks up the target in the repository and will call the
      * registered XMLinstruction.
      * @see XMLinstruction
      */
    void processingInstruction (const XMLCh *const, const XMLCh *const);

    /** Handler called by Xerces in error conditions. It throws an exception
      * to abort the parsing procedure. */
    void error (const xercesc::SAXParseException&);

    /** Handler called by Xerces for warnings. */
    void warning (const xercesc::SAXParseException&);

  public:
    /** Constructor. */
    XMLInput();

    /** Destructor. */
    virtual ~XMLInput();

    /** This is the core parsing function, which triggers the XML parser to
      * start processing the input. It is normally called from the method
      * parse(Object*) once a proper stream has been created.
      * @see parse(Object*)
      */
    void parse(xercesc::InputSource&, Object*, bool=false);

    /** Updates whether we ignore data exceptions or whether we abort the
      * processing of the XML data stream. */
    void setAbortOnDataError(bool i)
    {
      abortOnDataException = i;
    }

    /** Returns the behavior of the parser in case of data errors.<br>
      * When true is returned, the processing of the XML stream continues
      * after a DataException. Other, more critical, exceptions types will
      * still abort the parsing process.<br>
      * False indicates that the processing of the XML stream is aborted.
      */
    bool getAbortOnDataError() const
    {
      return abortOnDataException;
    }

    /** Transcode the Xerces XML characters to our UTF8 encoded buffer. */
    char* transcodeUTF8(const XMLCh*);

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
    void setFileName(const string& s)
    {
      filename = s;
    }

    /** Returns the name of the file or directory to process. */
    string getFileName()
    {
      return filename;
    }

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
    void parse(Object*, bool=false);

  private:
    /** Name of the file to be opened. */
    string filename;
};


/** @brief This class represents a list of XML key+value pairs.
  *
  * The method is a thin wrapper around one of the internal data
  * structures of the XMLInput class.
  */
class XMLDataValueDict : public DataValueDict
{
  public:
    typedef vector< pair<DataKeyword, XMLData> > dict;

    /** Constructor. */
    XMLDataValueDict(
      vector<XMLInput::fld>& f,
      int st,
      int nd
      ) : fields(f), strt(st), nd(nd) {}

    /** Look up a certain keyword. */
    const XMLData* get(const Keyword& key) const;

    /** Enlarge the dictiorary. */
    void enlarge()
    {
      ++nd;
    }

    /** Auxilary debugging method. */
    void print();

  private:
    vector<XMLInput::fld>& fields;
    int strt;
    int nd;
};


/** @brief Base class for writing XML formatted data to an output stream.
  *
  * Subclasses implement writing to specific stream types, such as files
  * and strings.
  */
class XMLSerializer : public Serializer
{
  public:
    /** Updates the string that is printed as the first line of each XML
      * document.<br>
      * The default value is:
      *   <?xml version="1.0" encoding="UTF-8"?>
      */
    void setHeaderStart(const string& s)
    {
      headerStart = s;
    }

    /** Returns the string that is printed as the first line of each XML
      * document. */
    string getHeaderStart() const
    {
      return headerStart;
    }

    /** Updates the attributes that are written for the root element of each
      * XML document.<br>
      * The default value is an empty string.
      */
    void setHeaderAtts(const string& s)
    {
      headerAtts = s;
    }

    /** Returns the attributes that are written for the root element of each
      * XML document. */
    string getHeaderAtts() const
    {
      return headerAtts;
    }

    /** Constructor with a given stream. */
    XMLSerializer(ostream& os) : Serializer(os)
    {
      indentstring[0] = '\0';
    }

    /** Default constructor. */
    XMLSerializer()
    {
      indentstring[0] = '\0';
    }

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * Output: \<TAG\>
      */
    void BeginList(const Keyword& t)
    {
      *m_fp << indentstring << t.stringElement() << "\n";
      incIndent();
    }

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
      * Output: \<TAG TAG1="val1"\>
      */
    void BeginObject(const Keyword& t, const Keyword& attr1, const string& val1)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute();
      escape(val1);
      *m_fp << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * Output: \<TAG TAG1="val1"\>
      */
    void BeginObject(const Keyword& t, const Keyword& attr1, const Date val1)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute() << val1 << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * Output: \<TAG TAG1="val1"\>
      */
    void BeginObject(const Keyword& t, const Keyword& attr1, const int val1)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute() << val1 << "\">\n";
      incIndent();
    }

    /** Start writing a new object. This method will open a new XML-tag.<br>
      * Output: \<TAG TAG1="val1" TAG2="val2"\>
      */
    void BeginObject(const Keyword& t, const Keyword& attr1, const string& val1,
      const Keyword& attr2, const string& val2)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute();
      escape(val1);
      *m_fp << "\"" << attr2.stringAttribute();
      escape(val2);
      *m_fp << "\">\n";
      incIndent();
    }

    void BeginObject(const Keyword& t, const Keyword& attr1, const unsigned long& val1,
      const Keyword& attr2, const string& val2)
    {
      *m_fp << indentstring << t.stringStartElement()
          << attr1.stringAttribute() << val1 << "\""
          << attr2.stringAttribute();
      escape(val2);
      *m_fp << "\">\n";
      incIndent();
    }

    void BeginObject(const Keyword& t, const Keyword& attr1, const int& val1,
      const Keyword& attr2, const Date val2,
      const Keyword& attr3, const Date val3)
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

    /** Write the closing tag of this object and decrease the indentation
      * level.<br>
      * Output: \</TAG_T\>
      */
    void EndList(const Keyword& t)
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
      {
        *m_fp << indentstring << t.stringElement();
        escape(val);
        *m_fp << t.stringEndElement();
      }
    }

    /** Writes an element with a string attribute.<br>
      * Output: \<TAG_U TAG_T="string"/\> */
    void writeElement(const Keyword& u, const Keyword& t, const string& val)
    {
      if (val.empty())
        *m_fp << indentstring << u.stringStartElement() << "/>\n";
      else
      {
        *m_fp << indentstring << u.stringStartElement() << t.stringAttribute();
        escape(val);
        *m_fp << "\"/>\n";
      }
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
      {
        *m_fp << indentstring << u.stringStartElement() << t1.stringAttribute();
        escape(val1);
        *m_fp << "\"" << t2.stringAttribute();
        escape(val2);
        *m_fp << "\"/>\n";
      }
    }

    /** Writes an element with a string and an unsigned long attribute.<br>
      * Output: \<TAG_U TAG_T1="val1" TAG_T2="val2"/\> */
    void writeElement(const Keyword& u, const Keyword& t1, unsigned long val1,
        const Keyword& t2, const string& val2)
    {
      *m_fp << indentstring << u.stringStartElement()
          << t1.stringAttribute() << val1 << "\""
          << t2.stringAttribute();
      escape(val2);
      *m_fp << "\"/>\n";
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
      if (!val) return;
      *m_fp << indentstring << t.stringElement();
      escape(val);
      *m_fp << t.stringEndElement();
    }

    /** Writes an Duration element.<br>
      * Output: \<TAG_T\>d\</TAG_T\> /> */
    void writeElement(const Keyword& t, const Duration d)
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

    /** This method writes a serializable object with a complete XML compliant
      * header.<br>
      * You should call this method for the root object of your xml document,
      * and writeElement for all objects nested in it.
      * @see writeElement(const Keyword&, Object*)
      */
    void writeElementWithHeader(const Keyword& tag, const Object* object);

    /** Returns a pointer to the object that is currently being saved. */
    Object* getCurrentObject() const
    {
      return const_cast<Object*>(currentObject);
    }

    /** Returns a pointer to the parent of the object that is being saved. */
    Object* getPreviousObject() const
    {
      return const_cast<Object*>(parentObject);
    }

    /** Returns the number of objects that have been serialized. */
    unsigned long countObjects() const
    {
      return numObjects;
    }

    /** Get a string suitable for correctly indenting the output. */
    const char* getIndent()
    {
      return indentstring;
    }

  private:
    /** Write the argument to the output stream, while escaping any
      * special characters.
      * The following characters are replaced:
      *    - &: replaced with &amp;
      *    - <: replaced with &lt;
      *    - >: replaced with &gt;
      *    - ": replaced with &quot;
      *    - ': replaced with &apos;
      *    - all other characters are left unchanged
      * The reverse process of un-escaping the special character sequences is
      * taken care of by the Xerces library.
      *
      * This method works fine with UTF-8 and single-byte encodings, but will
      * NOT work with other multibyte encodings (such as UTF-116 or UTF-32).
      * FrePPLe consistently uses UTF-8 in its internal representation.
      */
    void escape(const string&);

    /** Increase the indentation level. The indentation level is between
      * 0 and 40. */
    void incIndent();

    /** Decrease the indentation level. */
    void decIndent();

    /** This string defines what will be printed at the start of each XML
      * document. The default value is:
      *   \<?xml version="1.0" encoding="UTF-8"?\>
      */
    string headerStart = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>";

    /** This string defines what will be attributes are printed for the root
      * element of each XML document.
      * The default value is:
      *    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      */
    string headerAtts = "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"";

    /** This string is a null terminated string containing as many spaces as
      * indicated by the m_indent.
      * @see incIndent, decIndent
      */
    char indentstring[41];

    /** This variable keeps track of the indentation level.
      * @see incIndent, decIndent
      */
    short int m_nIndent = 0;
};


/** @brief This class writes XML data to a flat file.
  *
  * Note that an object of this class can write only to a single file. If
  * multiple files are required multiple XMLOutputFile objects will be
  * required too.
  * @see XMLOutput
  */
class XMLSerializerFile : public XMLSerializer
{
  public:
    /** Constructor with a filename as argument. An exception will be
      * thrown if the output file can't be properly initialized. */
    XMLSerializerFile(const string& chFilename)
    {
      of.open(chFilename.c_str(), ios::out);
      if(!of) throw RuntimeException("Could not open output file");
      setOutput(of);
    }

    /** Destructor. */
    ~XMLSerializerFile()
    {
      of.close();
    }

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
class XMLSerializerString : public XMLSerializer
{
  public:
    /** Constructor with a starting string as argument. */
    XMLSerializerString(const string& str) : os(str)
    {
      setOutput(os);
    }

    /** Default constructor. */
    XMLSerializerString()
    {
      setOutput(os);
    }

    /** Return the output string. */
    const string getData() const
    {
      return os.str();
    }

  private:
    ostringstream os;
};

} // end namespace
} // end namespace

#endif  // End of FREPPLE_XML_H
