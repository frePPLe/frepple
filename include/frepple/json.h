/***************************************************************************
 *                                                                         *
 * Copyright (C) 2014-2015 by frePPLe bv                                   *
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
#ifndef FREPPLE_JSON_H
#define FREPPLE_JSON_H

#include "frepple.h"
using namespace frepple;

#if defined(HAVE_STDINT_H)
#include <stdint.h>
#else
#error "This compiler isn't supported"
#endif

// Parser flag to stop parsing at the end of root document
#define RAPIDJSON_PARSE_DEFAULT_FLAGS 8
#include "rapidjson/error/en.h"
#include "rapidjson/reader.h"

namespace frepple {
namespace utils {

/* Base class for writing JSON formatted data to an output stream.
 *
 * Subclasses implement writing to specific stream types, such as files
 * and strings.
 */
class JSONSerializer : public Serializer {
 public:
  /* Constructor with a given stream. */
  JSONSerializer(ostream& os) : Serializer(os) {
    flatten_properties = true;
    indentstring[0] = '\0';
  }

  /* Default constructor. */
  JSONSerializer() {
    flatten_properties = true;
    indentstring[0] = '\0';
  }

  /* Tweak to toggle between the dictionary and array modes. */
  void setMode(bool f) {
    if (mode.empty())
      mode.push(f);
    else
      mode.top() = f;
  }

  void setFormatted(bool b) { formatted = b; }

  bool getFormatted() const { return formatted; }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG" : [
   */
  void BeginList(const Keyword& t) {
    if (formatted) {
      if (!first) *m_fp << ",\n" << indentstring;
      incIndent();
    } else if (!first)
      *m_fp << ",";
    *m_fp << "\"" << t << "\":[";
    first = true;
    mode.push(true);
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG" : {
   */
  void BeginObject(const Keyword& t) {
    if (formatted) {
      if (!first) *m_fp << ",\n" << indentstring;
      incIndent();
    } else if (!first)
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << t << "\":";
    if (formatted)
      *m_fp << "{\n" << indentstring;
    else
      *m_fp << "{";
    first = true;
    mode.push(false);
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG" : {
   */
  void BeginObject(const Keyword& t, const string& atts) {
    if (formatted) {
      incIndent();
      if (first)
        *m_fp << "\n" << indentstring;
      else
        *m_fp << ",\n" << indentstring;
    } else if (!first)
      *m_fp << ",";
    *m_fp << "\"" << t << "\":{";
    first = true;
    mode.push(false);
    logger << "IMPLEMENTATION INCOMPLETE" << endl;  // TODO not using atts
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG" : {"TAG1": VAL1    (dictionary mode)
   *         {"TAG1": VAL1            (array mode)
   */
  void BeginObject(const Keyword& t, const Keyword& attr1, const string& val1) {
    if (formatted) {
      incIndent();
      if (first)
        *m_fp << "\n" << indentstring;
      else
        *m_fp << ",\n" << indentstring;
    } else if (!first)
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << t << "\":";
    *m_fp << "{\"" << attr1 << "\":";
    escape(val1);
    first = false;
    mode.push(false);
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG" : {"TAG1": VAL1    (dictionary mode)
   *         {"TAG1": VAL1            (array mode)
   */
  void BeginObject(const Keyword& t, const Keyword& attr1, const int val1) {
    if (formatted) {
      incIndent();
      if (first)
        *m_fp << "\n" << indentstring;
      else
        *m_fp << ",\n" << indentstring;
    } else if (!first)
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << t << "\":";
    *m_fp << "{\"" << attr1 << "\":" << val1;
    first = false;
    mode.push(false);
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG" : {"TAG1": VAL1    (dictionary mode)
   *         {"TAG1": VAL1            (array mode)
   */
  void BeginObject(const Keyword& t, const Keyword& attr1, const Date val1) {
    if (formatted) {
      incIndent();
      if (first)
        *m_fp << "\n" << indentstring;
      else
        *m_fp << ",\n" << indentstring;
    } else if (!first)
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << t << "\":";
    *m_fp << "{\"" << attr1 << "\":" << val1;
    first = false;
    mode.push(false);
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG":{"TAG1":"VAL1","TAG2":"VAL2" (dictionary mode)
   *         {"TAG1":"VAL1","TAG2":"VAL2"         (array mode)
   */
  void BeginObject(const Keyword& t, const Keyword& attr1, const string& val1,
                   const Keyword& attr2, const string& val2) {
    if (formatted) {
      incIndent();
      if (first)
        *m_fp << "\n" << indentstring;
      else
        *m_fp << ",\n" << indentstring;
    } else if (!first)
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << t << "\":";
    *m_fp << "{\"" << attr1 << "\":";
    escape(val1);
    *m_fp << ",\"" << attr2 << "\":";
    escape(val2);
    first = false;
    mode.push(false);
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG":{"TAG1":"VAL1","TAG2":"VAL2" (dictionary mode)
   *         {"TAG1":"VAL1","TAG2":"VAL2"         (array mode)
   */
  void BeginObject(const Keyword& t, const Keyword& attr1,
                   const unsigned long& val1, const Keyword& attr2,
                   const string& val2) {
    if (formatted) {
      incIndent();
      if (first)
        *m_fp << "\n" << indentstring;
      else
        *m_fp << ",\n" << indentstring;
    } else if (!first)
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << t << "\":";
    *m_fp << "{\"" << attr1 << "\":" << val1 << ",\"" << attr2 << "\":";
    escape(val2);
    first = false;
    mode.push(false);
  }

  /* Start writing a new object. This method will open a new tag.
   * Output: "TAG":{"TAG1":"VAL1","TAG2":"VAL2" (dictionary mode)
   *         {"TAG1":"VAL1","TAG2":"VAL2"         (array mode)
   */
  void BeginObject(const Keyword& t, const Keyword& attr1, const int& val1,
                   const Keyword& attr2, const Date val2, const Keyword& attr3,
                   const Date val3) {
    if (formatted) {
      incIndent();
      if (first)
        *m_fp << "\n" << indentstring;
      else
        *m_fp << ",\n" << indentstring;
    } else if (!first)
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << t << "\":";
    *m_fp << "{\"" << attr1 << "\":" << val1 << ",\"" << attr2 << "\":"
          << "\"" << val2 << "\",\"" << attr3 << "\":"
          << "\"" << val3 << "\"";
    first = false;
    mode.push(false);
  }

  /* Write the closing tag of this object
   * Output: }
   */
  void EndObject(const Keyword& t) {
    if (formatted) {
      decIndent();
      *m_fp << "\n" << indentstring << "}";
    } else
      *m_fp << "}";
    first = false;
    mode.pop();
  }

  /* Write the closing tag of this object
   * Output: ]
   */
  void EndList(const Keyword& t) {
    if (formatted) decIndent();
    *m_fp << "]";
    first = false;
    mode.pop();
  }

  /* Write the string to the output. This method is used for passing text
   * straight into the output file.
   */
  void writeString(const string& c) { *m_fp << c; }

  void resetFirst(bool t) { first = t; }

  void writeElementNull(const Keyword& t) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":null";
  }

  /* Write an unsigned long value enclosed opening and closing tags.
   * Output: , "TAG": uint
   */
  void writeElement(const Keyword& t, const long unsigned int val) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":" << val;
  }

  /* Write an integer value enclosed opening and closing tags.
   * Output: ,"TAG": int
   */
  void writeElement(const Keyword& t, const int val) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":" << val;
  }

  /* Write a double value enclosed opening and closing tags.
   * Output: ,"TAG": double
   */
  void writeElement(const Keyword& t, const double val) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":" << val;
  }

  void writeElement(const Keyword& t, const PooledString& u, const double val) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":"
          << "{\"" << u << "\": " << val << "}";
  }

  /* Write a boolean value enclosed opening and closing tags. The boolean
   * is written out as the string 'true' or 'false'.
   * Output: "TAG": true/false
   */
  void writeElement(const Keyword& t, const bool val) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << (val ? "\":true" : "\":false");
  }

  /* Write a string value enclosed opening and closing tags.
   * Output: "TAG": "val"
   */
  void writeElement(const Keyword& t, const string& val) {
    if (val.empty()) return;
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":";
    escape(val);
  }

  void writeElement(const string& key, const string& val) {
    if (val.empty()) return;
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    escape(key);
    *m_fp << ":";
    escape(val);
  }

  /* Writes an element with a string attribute.
   * Output:
   *   "TAG_U": {"TAG_T": "string"}    (dictionary mode)
   *   {"TAG_T": "string"}             (array mode)
   */
  void writeElement(const Keyword& u, const Keyword& t, const string& val) {
    if (val.empty()) {
      if (!mode.empty() && !mode.top()) {
        if (first)
          first = false;
        else if (formatted)
          *m_fp << ",\n" << indentstring;
        else
          *m_fp << ",";
        *m_fp << "\"" << u << "\":"
              << "{}";
      }
    } else {
      if (first)
        first = false;
      else if (formatted)
        *m_fp << ",\n" << indentstring;
      else
        *m_fp << ",";
      if (!mode.empty() && !mode.top()) *m_fp << "\"" << u << "\":";
      *m_fp << "{\"" << t << "\":";
      escape(val);
      *m_fp << "}";
    }
  }

  /* Writes an element with a long attribute.
   * Output: "TAG_U": {"TAG_T": long}
   */
  void writeElement(const Keyword& u, const Keyword& t, const long val) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << u << "\":";
    *m_fp << "{\"" << t << "\":" << val << "}";
  }

  /* Writes an element with a date attribute.
   * Output: "TAG_U": {"TAG_T": date}
   */
  void writeElement(const Keyword& u, const Keyword& t, const Date& val) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << u << "\":";
    *m_fp << "{\"" << t << "\":" << val << "}";
  }

  /* Writes an element with 2 string attributes.
   * Output: "TAG_U":{"TAG_T1":"val1","TAGT2":"val2"}
   */
  void writeElement(const Keyword& u, const Keyword& t1, const string& val1,
                    const Keyword& t2, const string& val2) {
    if (val1.empty()) {
      if (!mode.empty() && !mode.top()) {
        if (first)
          first = false;
        else if (formatted)
          *m_fp << ",\n" << indentstring;
        else
          *m_fp << ",";
        *m_fp << "\"" << u << "\":"
              << "{}";
      }
    } else {
      if (first)
        first = false;
      else if (formatted)
        *m_fp << ",\n" << indentstring;
      else
        *m_fp << ",";
      if (!mode.empty() && !mode.top()) *m_fp << "\"" << u << "\":";
      *m_fp << "{\"" << t1 << "\":";
      escape(val1);
      *m_fp << ",\"" << t2 << "\":";
      escape(val2);
      *m_fp << "}";
    }
  }

  /* Writes an element with a string and an unsigned long attribute.
   * Output: "TAG_U": {"TAG_T1": "val1","TAGT2": "val2"}
   */
  void writeElement(const Keyword& u, const Keyword& t1, unsigned long val1,
                    const Keyword& t2, const string& val2) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << u << "\":";
    *m_fp << "{\"" << t1 << "\":" << val1 << ",\"" << t2 << "\":";
    escape(val2);
    *m_fp << "}";
  }

  /* Writes an element with a short, an unsigned long and a double
   * attribute. Output: "TAG_U": {"TAG_T1":val1,"TAGT2":val2,"TAGT3":val3}
   */
  void writeElement(const Keyword& u, const Keyword& t1, short val1,
                    const Keyword& t2, unsigned long val2, const Keyword& t3,
                    double val3) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    if (!mode.empty() && !mode.top()) *m_fp << "\"" << u << "\":";
    *m_fp << "{\"" << t1 << "\":" << val1 << ",\"" << t2 << "\":" << val2
          << ",\"" << t3 << "\":" << val3 << "}";
  }

  /* Writes a C-type character string.
   * Output: "TAG_T": "val"
   */
  void writeElement(const Keyword& t, const char* val) {
    if (!val) return;
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":";
    escape(val);
  }

  /* Writes an timeperiod element.
   * Output: "TAG_T": "val"
   */
  void writeElement(const Keyword& t, const Duration d) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":" << static_cast<long>(d);
  }

  /* Writes an date element.
   * Output: \<TAG_T\>d\</TAG_T\> /> */
  void writeElement(const Keyword& t, const Date d) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":\"" << d << "\"";
  }

  /* Writes an daterange element.
   * Output: \<TAG_T\>d\</TAG_T\> */
  void writeElement(const Keyword& t, const DateRange& d) {
    if (first)
      first = false;
    else if (formatted)
      *m_fp << ",\n" << indentstring;
    else
      *m_fp << ",";
    *m_fp << "\"" << t << "\":\"" << d << "\"";
  }

  /* Write the argument to the output stream, while escaping any
   * special characters.
   * From the JSON specification http://www.ietf.org/rfc/rfc4627.txt:
   *   All Unicode characters may be placed within the quotation marks
   *   except for the characters that must be escaped: quotation mark,
   *   reverse solidus, and the control characters (U+0000 through
   *   U+001F).
   * For convenience we also escape the forward slash.
   *
   * This method works fine with UTF-8 and single-byte encodings, but will
   * NOT work with other multibyte encodings (such as UTF-116 or UTF-32).
   * FrePPLe consistently uses UTF-8 in its internal representation.
   */
  void escape(const string&);

 private:
  /* Generated nicely formatted text.
   * This is false by default, because it generates a smaller file
   * without the extra whitespace.
   */
  bool formatted = false;

  /* Flag to mark if an object has already one or more fields saved. */
  bool first = true;

  /* Stack to keep track of the current output mode: dictionary (true)
   * or array (true).
   */
  stack<bool> mode;

  /* This string is a null terminated string containing as many spaces as
   * indicated by the m_nIndent.
   */
  char indentstring[41];

  /* This variable keeps track of the indentation level. */
  short int m_nIndent = 0;

  /* Increment indentation level in the formatted output. */
  inline void incIndent() {
    indentstring[m_nIndent++] = '\t';
    if (m_nIndent > 40) m_nIndent = 40;
    indentstring[m_nIndent] = '\0';
  }

  /* Decrement indentation level in the formatted output. */
  inline void decIndent() {
    if (--m_nIndent < 0) m_nIndent = 0;
    indentstring[m_nIndent] = '\0';
  }

  /* Stack of objects and their data fields. */
  struct obj {
    const MetaClass* cls;
    Object* object;
    int start;
    size_t hash;
  };
  vector<obj> objects;
};

/* This class writes JSON data to a flat file.
 *
 * Note that an object of this class can write only to a single file. If
 * you need to write multiple files then multiple JSONSerializerFile objects
 * will be required.
 */
class JSONSerializerFile : public JSONSerializer {
 public:
  /* Constructor with a filename as argument. An exception will be
   * thrown if the output file can't be properly initialized. */
  JSONSerializerFile(const string& chFilename) {
    of.open(chFilename.c_str(), ios::out);
    if (!of) throw RuntimeException("Could not open output file");
    setOutput(of);
  }

  /* Destructor. */
  ~JSONSerializerFile() { of.close(); }

 private:
  ofstream of;
};

/* This class writes JSON data to a string.
 *
 * The generated output is stored internally in the class, and can be
 * accessed by converting the JSONOutputString object to a string object.
 * This class can consume a lot of memory if large sets of objects are
 * being saved in this way.
 */
class JSONSerializerString : public JSONSerializer {
 public:
  /* Default constructor. */
  JSONSerializerString() { setOutput(os); }

  /* Return the output string. */
  const string getData() const { return os.str(); }

 private:
  ostringstream os;
};

/* This python function writes the complete model to a JSON-file.
 *
 * Both the static model (i.e. items, locations, buffers, resources,
 * calendars, etc...) and the dynamic data (i.e. the actual plan including
 * the operationplans, demand, problems, etc...).
 * The format is such that the output file can be re-read to restore the
 * very same model.
 * The function takes the following arguments:
 *   - Name of the output file
 *   - Type of output desired: BASE, PLAN or DETAIL.
 *     The default value is BASE.
 */
PyObject* saveJSONfile(PyObject* self, PyObject* args);

class JSONData : public DataValue {
 public:
  /* Field types recognized by the parser. */
  enum JsonType {
    JSON_NULL,
    JSON_BOOL,
    JSON_INT,
    JSON_LONG,
    JSON_UNSIGNEDLONG,
    JSON_DOUBLE,
    JSON_STRING,
    JSON_OBJECT
  };

  /* Constructor. */
  JSONData() : data_type(JSON_NULL) {}

  /* Destructor. */
  virtual ~JSONData() {}

  virtual operator bool() const { return getBool(); }

  virtual long getLong() const;

  virtual unsigned long getUnsignedLong() const;

  virtual Duration getDuration() const;

  virtual int getInt() const;

  virtual double getDouble() const;

  virtual Date getDate() const;

  virtual const string& getString() const;

  virtual bool getBool() const;

  virtual Object* getObject() const;

  void setNull() { data_type = JSON_NULL; }

  virtual void setLong(const long l) {
    data_type = JSON_LONG;
    data_long = l;
  }

  virtual void setUnsignedLong(const unsigned long ul) {
    data_type = JSON_UNSIGNEDLONG;
    data_long = ul;
  }

  virtual void setDuration(const Duration d) {
    data_type = JSON_LONG;
    data_long = static_cast<long>(d);
  }

  virtual void setInt(const int i) {
    data_type = JSON_INT;
    data_int = i;
  }

  virtual void setDouble(const double d) {
    data_type = JSON_DOUBLE;
    data_double = d;
  }

  virtual void setDate(const Date d) {
    data_type = JSON_LONG;
    data_long = static_cast<long>(d.getTicks());
  }

  virtual void setString(const string& s) {
    data_type = JSON_STRING;
    data_string = s;
  }

  virtual void setBool(const bool b) {
    data_type = JSON_BOOL;
    data_bool = b;
  }

  virtual void setObject(Object* o) {
    data_type = JSON_OBJECT;
    data_object = o;
  }

  JsonType getDataType() const { return data_type; }

 private:
  /* Stores the type of data we're storing. */
  JsonType data_type;

  /* Data content. */
  union {
    bool data_bool;
    int data_int;
    long data_long;
    unsigned long data_unsignedlong;
    double data_double;
    Object* data_object;
  };
  string data_string;
};

/* A JSON parser, using the rapidjson library.
 *
 * Some specific limitations of the implementation:
 *   - JSON allows NULLs in the string values.
 *     FrePPLe doesn't, and we will only consider the part before the
 *     null characters.
 *   - The parser only supports UTF-8 encodings.
 *     RapidJSON also supports UTF-16 and UTF-32 (LE & BE), but a) FrePPLe
 *     internally represents all string data as UTF-8 and b) the in-situ
 *     parser requires input and destination encoding to be the same.
 *
 * See https://github.com/miloyip/rapidjson for information on rapidjson,
 * which is released under the MIT license.
 */
class JSONInput : public NonCopyable, public DataInput {
  friend rapidjson::Reader;

 private:
  /* This variable defines the maximum depth of the object creation stack.
   * This maximum is intended to protect us from malicious malformed
   * documents, and also for allocating efficient data structures for
   * the parser.
   */
  static const int maxobjects = 30;
  static const int maxdata = 200;

  static MetaFieldBool<Demand> useProperty;

 public:
  struct fld {
    const MetaFieldBase* field;
    size_t hash;
    JSONData value;
    string name;
  };

 private:
  /* Stack of fields already read. */
  vector<fld> data;

  /* Stack of objects and their data fields. */
  struct obj {
    const MetaClass* cls;
    Object* object;
    int start;
    size_t hash;
  };
  vector<obj> objects;

  /* Index into the objects stack. */
  int objectindex;

  /* Index into the data field stack. */
  int dataindex;

  // Handler callback functions for rapidjson
  bool Null();
  bool Bool(bool b);
  bool Int(int i);
  bool Uint(unsigned u);
  bool Int64(int64_t i);
  bool Uint64(uint64_t u);
  bool Double(double d);
  bool String(const char* str, rapidjson::SizeType length, bool copy);
  bool StartObject();
  bool Key(const char* str, rapidjson::SizeType length, bool copy);
  bool EndObject(rapidjson::SizeType memberCount);
  bool StartArray();
  bool EndArray(rapidjson::SizeType elementCount);
  bool RawNumber(const char* str, rapidjson::SizeType length, bool copy) {
    throw LogicException("Shouldn't be called");
  }

 protected:
  /* Constructor. */
  JSONInput() : data(maxdata), objects(maxobjects) {}

  /* Main parser function. */
  void parse(Object* pRoot, char* buffer);
};

/* This class reads JSON data from a string. */
class JSONInputString : public JSONInput {
 public:
  /* Default constructor. */
  JSONInputString(char* s) : data(s) {};

  /* Parse the specified string. */
  void parse(Object* pRoot) { JSONInput::parse(pRoot, data); }

 private:
  /* String containing the data to be parsed. Note that NO local copy of the
   * data is made, only a reference is stored. The class relies on the code
   * calling the command to correctly create and destroy the string being
   * used.
   */
  char* data;
};

/* This class reads JSON data from a file system.
 *
 * The filename argument can be the name of a file or a directory.
 * If a directory is passed, all files with the extension ".json"
 * will be read from it. Subdirectories are not recursed.
 */
class JSONInputFile : public JSONInput {
 public:
  /* Constructor. The argument passed is the name of a
   * file or a directory. */
  JSONInputFile(const string& s) : filename(s) {};

  /* Default constructor. */
  JSONInputFile() {};

  /* Update the name of the file to be processed. */
  void setFileName(const string& s) { filename = s; }

  /* Returns the name of the file or directory to process. */
  string getFileName() { return filename; }

  /* Parse the specified file.
   * When a directory was passed as the argument a failure is
   * flagged as soon as a single file returned a failure. All
   * files in an directory are processed however, regardless of
   * failure with one of the files.
   * RuntimeException is generated in the following conditions:
   *    - no input file or directory has been specified.
   *    - read access to the input file is not available
   *    - the program doesn't support reading directories on your platform
   */
  void parse(Object*);

 private:
  /* Name of the file or directory to be opened. */
  string filename;
};

/* This class represents a list of JSON key+value pairs.
 *
 * The method is a thin wrapper around one of the internal data
 * structures of the parser implemented in the class JSONInput.
 */
class JSONDataValueDict : public DataValueDict {
 public:
  typedef vector<pair<DataKeyword, XMLData> > dict;

  /* Constructor. */
  JSONDataValueDict(vector<JSONInput::fld>& f, int st, int nd)
      : fields(f), strt(st), nd(nd) {
    if (strt < 0) strt = 0;
  }

  /* Look up a certain keyword. */
  const JSONData* get(const Keyword& key) const;

  /* Enlarge the dictiorary. */
  void enlarge() { ++nd; }

  /* Auxilary debugging method. */
  void print();

  /* Return the start index in the array. */
  inline int getStart() const { return strt; }

  /* Return the end index in the array. */
  inline int getEnd() const { return nd; }

 public:  // TODO Should be kept private
  vector<JSONInput::fld>& fields;
  int strt;
  int nd;
};

/* Method exposed in Python to process JSON data from a string. */
PyObject* readJSONdata(PyObject*, PyObject*);

/* Method exposed in Python to process JSON data from a file. */
PyObject* readJSONfile(PyObject*, PyObject*);

}  // namespace utils
}  // namespace frepple

#endif
