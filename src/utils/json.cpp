/***************************************************************************
 *                                                                         *
 * Copyright (C) 2014 by frePPLe bv                                        *
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

#include "frepple/json.h"

#include <filesystem>
#include <iomanip>

/* Uncomment the next line to create a lot of debugging messages during
 * the parsing of the data. */
// #define PARSE_DEBUG

namespace frepple {
namespace utils {

// This is used as a dummy field to indicate situations where we need to
// set a property field on an object.
MetaFieldBool<Demand> JSONInput::useProperty(Tags::booleanproperty,
                                             &Demand::getHidden,
                                             &Demand::setHidden);

PyObject* saveJSONfile(PyObject* self, PyObject* args) {
  // Pick up arguments
  char* filename;
  char* content = nullptr;
  int formatted = 0;
  if (!PyArg_ParseTuple(args, "s|sp:saveJSONfile", &filename, &content,
                        &formatted))
    return nullptr;

  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;

  // Execute and catch exceptions
  try {
    JSONSerializerFile o(filename);
    if (content) {
      if (!strcmp(content, "BASE"))
        o.setContentType(BASE);
      else if (!strcmp(content, "PLAN"))
        o.setContentType(PLAN);
      else if (!strcmp(content, "DETAIL"))
        o.setContentType(DETAIL);
      else
        throw DataException("Invalid content type '" + string(content) + "'");
    }
    if (formatted) o.setFormatted(true);
    o.setMode(true);
    o.pushCurrentObject(&Plan::instance());
    o.setSaveReferences(true);
    Plan::instance().writeElement(&o, Tags::plan);
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }

  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void JSONSerializer::escape(const string& x) {
  *m_fp << "\"";
  for (const char* p = x.c_str(); *p; ++p) {
    switch (*p) {
      case '"':
        *m_fp << "\\\"";
        break;
      case '/':
        *m_fp << "\\/";
        break;
      case '\\':
        *m_fp << "\\\\";
        break;
      case '\b':
        *m_fp << "\\b";
        break;
      case '\t':
        *m_fp << "\\t";
        break;
      case '\n':
        *m_fp << "\\n";
        break;
      case '\f':
        *m_fp << "\\f";
        break;
      case '\r':
        *m_fp << "\\r";
        break;
      case '\v':
        *m_fp << "\\v";
        break;
      default:
        if (static_cast<short>(*p) > 0 && static_cast<short>(*p) < 32)
          // Control characters
          *m_fp << "\\u" << setw(4) << static_cast<int>(*p);
        else
          *m_fp << *p;
    }
  }
  *m_fp << "\"";
}

void JSONInputFile::parse(Object* pRoot) {
  // Check if string has been set
  if (filename.empty()) throw DataException("Missing input file or directory");

  // Check if the parameter is the name of a directory
  filesystem::path p(filename);
  if (!filesystem::exists(p))
    // Can't verify the status
    throw RuntimeException("Couldn't open input file '" + filename + "'");
  else if (filesystem::is_directory(p)) {
    // Data is a directory: loop through all *.json files now. No recursion in
    // subdirectories is done.
    // The code is unfortunately different for Windows & Linux. Sigh...
    for (const auto& entry : filesystem::directory_iterator(p)) {
      if (entry.is_regular_file() && entry.path().extension() == ".json")
        JSONInputFile(entry.path().string().c_str()).parse(pRoot);
    }
  } else {
    // Normal file
    // Read the complete file in a memory buffer
    ifstream t;
    t.open(filename.c_str());
    t.seekg(0, ios::end);
    ifstream::pos_type length = t.tellg();
    if (length > 300000000) {
      t.close();
      throw DataException("Maximum JSON file size is 300MB");
    }
    t.seekg(0, std::ios::beg);
    char* buffer = new char[length];
    t.read(buffer, length);
    t.close();

    // Parse the data
    JSONInput::parse(pRoot, buffer);
  }
}

PyObject* readJSONfile(PyObject* self, PyObject* args) {
  // Pick up arguments
  char* filename = nullptr;
  if (!PyArg_ParseTuple(args, "s:readJSONfile", &filename)) return nullptr;

  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;

  // Execute and catch exceptions
  try {
    if (!filename) throw DataException("Missing filename");
    JSONInputFile(filename).parse(&Plan::instance());
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }

  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

PyObject* readJSONdata(PyObject* self, PyObject* args) {
  // Pick up arguments
  char* data;
  if (!PyArg_ParseTuple(args, "s:readJSONdata", &data)) return nullptr;

  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS;

  // Execute and catch exceptions
  try {
    if (!data) throw DataException("No input data");
    JSONInputString(data).parse(&Plan::instance());
  } catch (...) {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }

  // Reclaim Python interpreter
  Py_END_ALLOW_THREADS;
  return Py_BuildValue("");
}

void JSONInput::parse(Object* pRoot, char* buffer) {
  if (!pRoot)
    throw DataException("Can't parse JSON data into nullptr root object");

  // Initialize the parser to read data into the object pRoot.
  objectindex = -1;
  dataindex = -1;
  objects[0].start = 0;
  objects[0].object = pRoot;
  objects[0].cls = &pRoot->getType();
  objects[0].hash = pRoot->getType().typetag->getHash();

  // Call the rapidjson in-site parser.
  // The parser will modify the string buffer during the parsing!
  rapidjson::InsituStringStream buf(buffer);
  rapidjson::Reader reader;
  try {
    rapidjson::ParseResult ok =
        reader.Parse<rapidjson::kParseCommentsFlag |
                     rapidjson::kParseTrailingCommasFlag |
                     rapidjson::kParseStopWhenDoneFlag>(buf, *this);
    if (!ok) {
      ostringstream o;
      o << "Error position " << ok.Offset()
        << " during JSON parsing: " << rapidjson::GetParseError_En(ok.Code());
      throw DataException(o.str());
    }
  } catch (const exception& e) {
    logger << "Parsing error near position " << buf.Tell() << endl;
    throw;
  }
}

bool JSONInput::Null() {
  if (dataindex < 0) return true;

  data[dataindex].value.setNull();

  if (objectindex == 0 && objects[objectindex].object &&
      data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 4, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::Bool(bool b) {
  if (dataindex < 0) return true;

  data[dataindex].value.setBool(b);

  if (objectindex == 0 && objects[objectindex].object &&
      data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 1, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::Int(int i) {
  if (dataindex < 0) return true;

  data[dataindex].value.setInt(i);

  if (objectindex == 0 && objects[objectindex].object &&
      data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 3, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::Uint(unsigned u) {
  if (dataindex < 0) return true;

  data[dataindex].value.setLong(u);

  if (objectindex == 0 && objects[objectindex].object &&
      data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 3, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::Int64(int64_t i) {
  if (dataindex < 0) return true;

  if (i < LONG_MAX && i > LONG_MIN)
    data[dataindex].value.setLong(static_cast<long>(i));
  else
    data[dataindex].value.setDouble(static_cast<double>(i));

  if (objectindex == 0 && objects[objectindex].object &&
      data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 3, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::Uint64(uint64_t u) {
  if (dataindex < 0) return true;

  if (u < ULONG_MAX)
    data[dataindex].value.setUnsignedLong(static_cast<unsigned long>(u));
  else
    data[dataindex].value.setDouble(static_cast<double>(u));

  if (objectindex == 0 && objects[objectindex].object &&
      data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 3, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::Double(double d) {
  if (dataindex < 0) return true;

  data[dataindex].value.setDouble(d);

  if (objectindex == 0 && objects[objectindex].object &&
      data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 3, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::String(const char* str, rapidjson::SizeType length, bool copy) {
  if (dataindex < 0) return true;

  // Note: JSON allows NULLs in the string values. FrePPLe doesn't, and the
  // next line will only copy the part before the null characters.
  // In XML, null characters are officially forbidden.
  data[dataindex].value.setString(str);

  if (data[dataindex].hash == Tags::type.getHash()) {
    // Immediate processing of the type field
    objects[objectindex].cls = MetaClass::findClass(str);
    if (!objects[objectindex].cls)
      throw DataException("Unknown type " + string(str));
  } else if (objectindex == 0 && objects[objectindex].object &&
             data[dataindex].field && !data[dataindex].field->isGroup()) {
    // Immediately process updates to the root object
    if (data[dataindex].field == &useProperty)
      // Property stored as a string
      objects[objectindex].object->setProperty(
          data[dataindex].name, data[dataindex].value, 4, getCommandManager());
    else
      data[dataindex].field->setField(objects[objectindex].object,
                                      data[dataindex].value);
    --dataindex;
  }
  return true;
}

bool JSONInput::StartObject() {
  if (++objectindex >= maxobjects)
    // You're joking?
    throw DataException("JSON-document nested excessively deep");

  // Reset the pointer to the object class being read
  if (objectindex && dataindex >= 0 && data[dataindex].field) {
    objects[objectindex].cls = data[dataindex].field->getClass();
    objects[objectindex].object = nullptr;
    objects[objectindex].start = dataindex + 1;
  } else if (objectindex)
    objects[objectindex].cls = nullptr;

// Debugging message
#ifdef PARSE_DEBUG
  logger << "Starting object #" << objectindex << " (type "
         << (objects[objectindex].cls ? objects[objectindex].cls->type
                                      : "nullptr")
         << ")" << endl;
#endif
  return true;
}

bool JSONInput::Key(const char* str, rapidjson::SizeType length, bool copy) {
  if (++dataindex >= maxdata)
    // You're joking?
    throw DataException("JSON-document nested excessively deep");

  // Look up the field
  data[dataindex].value.setNull();
  data[dataindex].hash = Keyword::hash(str);
  data[dataindex].name = str;

  if (objects[objectindex].cls) {
    data[dataindex].field =
        objects[objectindex].cls->findField(data[dataindex].hash);
    if (!data[dataindex].field && objects[objectindex].cls->category)
      data[dataindex].field =
          objects[objectindex].cls->category->findField(data[dataindex].hash);
    if (!data[dataindex].field) data[dataindex].field = &useProperty;
  } else
    data[dataindex].field = nullptr;

// Debugging message
#ifdef PARSE_DEBUG
  logger << "Reading field #" << dataindex << " '" << str << "' for object #"
         << objectindex << " ("
         << ((objectindex >= 0 && objects[objectindex].cls)
                 ? objects[objectindex].cls->type
                 : "none")
         << ")" << endl;
#endif

  return true;
}

bool JSONInput::EndObject(rapidjson::SizeType memberCount) {
  // Build a dictionary with all fields of this model
  JSONDataValueDict dict(data, objects[objectindex].start, dataindex);

  // Check if we need to add a parent object to the dict
  bool found_parent = false;
  if (objectindex > 0 && objects[objectindex].cls &&
      objects[objectindex].cls->parent) {
    assert(objects[objectindex - 1].cls);
    const MetaClass* cl = objects[objectindex - 1].cls;
    for (auto i = objects[objectindex].cls->getFields().begin();
         i != objects[objectindex].cls->getFields().end(); ++i)
      if ((*i)->getFlag(PARENT) && objectindex >= 1) {
        const MetaFieldBase* fld = data[objects[objectindex].start - 1].field;
        if (fld && !fld->isGroup())
          // Only under a group field can we inherit from a parent object
          continue;
        if (*((*i)->getClass()) == *cl ||
            (cl->category && *((*i)->getClass()) == *(cl->category))) {
          // Parent object matches expected type as parent field
          // First, create the parent object. It is normally created only
          // AFTER all its fields are read in, and that's too late for us.
          if (!objects[objectindex - 1].object) {
            JSONDataValueDict dict_parent(data, objects[objectindex - 1].start,
                                          objects[objectindex].start - 1);
            if (objects[objectindex - 1].cls->category) {
              assert(objects[objectindex - 1].cls->category->readFunction);
              objects[objectindex - 1].object =
                  objects[objectindex - 1].cls->category->readFunction(
                      objects[objectindex - 1].cls, dict_parent,
                      getCommandManager());
            } else {
              assert(
                  static_cast<const MetaCategory*>(objects[objectindex - 1].cls)
                      ->readFunction);
              objects[objectindex - 1].object =
                  static_cast<const MetaCategory*>(objects[objectindex - 1].cls)
                      ->readFunction(objects[objectindex - 1].cls, dict_parent,
                                     getCommandManager());
            }
            // Set fields already available now on the parent object
            for (auto idx = objects[objectindex - 1].start;
                 idx < objects[objectindex].start; ++idx) {
              if (data[idx].hash == Tags::type.getHash() ||
                  data[idx].hash == Tags::action.getHash())
                continue;
              if (data[idx].field == &useProperty &&
                  objects[objectindex - 1].object) {
                // Check again. If a field is defined on a subclass it is
                // possible that we didn't see it before the object got created.
                auto tmp = objects[objectindex - 1].object->getType().findField(
                    data[idx].hash);
                if (tmp) data[idx].field = tmp;
              }
              if (data[idx].field == &useProperty) {
                switch (data[idx].value.getDataType()) {
                  case JSONData::JSON_BOOL:
                    // Property stored as a boolean
                    objects[objectindex - 1].object->setProperty(
                        data[idx].name, data[idx].value, 1,
                        getCommandManager());
                    break;
                  case JSONData::JSON_INT:
                  case JSONData::JSON_LONG:
                  case JSONData::JSON_UNSIGNEDLONG:
                  case JSONData::JSON_DOUBLE:
                    // Property stored as a double value
                    objects[objectindex - 1].object->setProperty(
                        data[idx].name, data[idx].value, 3,
                        getCommandManager());
                    break;
                  default:
                    // Property stored as a string
                    objects[objectindex - 1].object->setProperty(
                        data[idx].name, data[idx].value, 4,
                        getCommandManager());
                }
              } else if (data[idx].field && !data[idx].field->isGroup()) {
                data[idx].field->setField(objects[objectindex - 1].object,
                                          data[idx].value, getCommandManager());
                data[idx].field = nullptr;  // Mark as already applied
              }
            }
          }
          // Add reference to parent to the current dict
          if (++dataindex >= maxdata)
            // You're joking?
            throw DataException("JSON-document nested excessively deep");
          data[dataindex].field = *i;
          data[dataindex].hash = (*i)->getHash();
          data[dataindex].value.setObject(objects[objectindex - 1].object);
          dict.enlarge();
          found_parent = true;
          break;
        }
      }
  }
  if (!found_parent && objectindex > 0 && objects[objectindex].cls &&
      objects[objectindex].cls->category &&
      objects[objectindex].cls->category->parent) {
    assert(objects[objectindex - 1].cls);
    const MetaClass* cl = objects[objectindex - 1].cls;
    for (auto i = objects[objectindex].cls->category->getFields().begin();
         i != objects[objectindex].cls->category->getFields().end(); ++i)
      if ((*i)->getFlag(PARENT) && objectindex >= 1) {
        const MetaFieldBase* fld = data[objects[objectindex].start - 1].field;
        if (fld && !fld->isGroup())
          // Only under a group field can we inherit from a parent object
          continue;
        if (*((*i)->getClass()) == *cl ||
            (cl->category && *((*i)->getClass()) == *(cl->category))) {
          // Parent object matches expected type as parent field
          // First, create the parent object. It is normally created only
          // AFTER all its fields are read in, and that's too late for us.
          if (!objects[objectindex - 1].object) {
            JSONDataValueDict dict_parent(data, objects[objectindex - 1].start,
                                          objects[objectindex].start - 1);
            if (objects[objectindex - 1].cls->category) {
              assert(objects[objectindex - 1].cls->category->readFunction);
              objects[objectindex - 1].object =
                  objects[objectindex - 1].cls->category->readFunction(
                      objects[objectindex - 1].cls, dict_parent,
                      getCommandManager());
            } else {
              assert(
                  static_cast<const MetaCategory*>(objects[objectindex - 1].cls)
                      ->readFunction);
              objects[objectindex - 1].object =
                  static_cast<const MetaCategory*>(objects[objectindex - 1].cls)
                      ->readFunction(objects[objectindex - 1].cls, dict_parent,
                                     getCommandManager());
            }
            // Set fields already available now on the parent object
            for (auto idx = objects[objectindex - 1].start;
                 idx < objects[objectindex].start; ++idx) {
              if (data[idx].hash == Tags::type.getHash() ||
                  data[idx].hash == Tags::action.getHash())
                continue;
              if (data[idx].field == &useProperty &&
                  objects[objectindex - 1].object) {
                // Check again. If a field is defined on a subclass it is
                // possible that we didn't see it before the object got created.
                auto tmp = objects[objectindex - 1].object->getType().findField(
                    data[idx].hash);
                if (tmp) data[idx].field = tmp;
              }
              if (data[idx].field == &useProperty) {
                switch (data[idx].value.getDataType()) {
                  case JSONData::JSON_BOOL:
                    // Property stored as a boolean
                    objects[objectindex - 1].object->setProperty(
                        data[idx].name, data[idx].value, 1,
                        getCommandManager());
                    break;
                  case JSONData::JSON_INT:
                  case JSONData::JSON_LONG:
                  case JSONData::JSON_UNSIGNEDLONG:
                  case JSONData::JSON_DOUBLE:
                    // Property stored as a double value
                    objects[objectindex - 1].object->setProperty(
                        data[idx].name, data[idx].value, 3,
                        getCommandManager());
                    break;
                  default:
                    // Property stored as a string
                    objects[objectindex - 1].object->setProperty(
                        data[idx].name, data[idx].value, 4,
                        getCommandManager());
                }
              } else if (data[idx].field && !data[idx].field->isGroup()) {
                data[idx].field->setField(objects[objectindex - 1].object,
                                          data[idx].value, getCommandManager());
                data[idx].field = nullptr;  // Mark as already applied
              }
            }
          }
          // Add reference to parent to the current dict
          if (++dataindex >= maxdata)
            // You're joking?
            throw DataException("JSON-document nested excessively deep");
          data[dataindex].field = *i;
          data[dataindex].hash = (*i)->getHash();
          data[dataindex].value.setObject(objects[objectindex - 1].object);
          dict.enlarge();
          break;
        }
      }
  }

// Debugging
#ifdef PARSE_DEBUG
  logger << "Ending Object #" << objectindex << " ("
         << ((objectindex >= 0 && objects[objectindex].cls)
                 ? objects[objectindex].cls->type
                 : "none")
         << "):" << endl;
  dict.print();
#endif

  // Root object never gets created
  if (objectindex) {
    // Call the object factory for the category and pass all field values
    // in a dictionary.
    // In some cases, the reading of the child fields already triggered the
    // creation of the parent. In such cases we can skip the creation step
    // here.
    if (!objects[objectindex].object) {
      if (!objects[objectindex].cls) {
        auto f = data[objects[objectindex - 1].start].field->getFunction();
        if (f)
          f(objects[objectindex - 1].object, dict, getCommandManager());
        else
          objects[objectindex].object = nullptr;
      } else if (objects[objectindex].cls->category) {
        assert(objects[objectindex].cls->category->readFunction);
        objects[objectindex].object =
            objects[objectindex].cls->category->readFunction(
                objects[objectindex].cls, dict, getCommandManager());
      } else if (static_cast<const MetaCategory*>(objects[objectindex].cls)
                     ->readFunction)
        objects[objectindex].object =
            static_cast<const MetaCategory*>(objects[objectindex].cls)
                ->readFunction(objects[objectindex].cls, dict,
                               getCommandManager());
      else
        objects[objectindex].object = nullptr;
    }
  }

  // Update all fields on the new object
  if (objects[objectindex].object) {
    for (auto idx = dict.getStart(); idx <= dict.getEnd(); ++idx) {
      if (data[idx].hash == Tags::type.getHash() ||
          data[idx].hash == Tags::action.getHash())
        continue;
      if (data[idx].field == &useProperty && objects[objectindex].object) {
        // Check again. If a field is defined on a subclass it is possible that
        // we didn't see it before the object got created.
        auto tmp =
            objects[objectindex].object->getType().findField(data[idx].hash);
        if (tmp) data[idx].field = tmp;
      }
      if (data[idx].field == &useProperty) {
        switch (data[idx].value.getDataType()) {
          case JSONData::JSON_BOOL:
            // Property stored as a boolean
            objects[objectindex].object->setProperty(
                data[idx].name, data[idx].value, 1, getCommandManager());
            break;
          case JSONData::JSON_INT:
          case JSONData::JSON_LONG:
          case JSONData::JSON_UNSIGNEDLONG:
          case JSONData::JSON_DOUBLE:
            // Property stored as a double value
            objects[objectindex].object->setProperty(
                data[idx].name, data[idx].value, 3, getCommandManager());
            break;
          default:
            // Property stored as a string
            objects[objectindex].object->setProperty(
                data[idx].name, data[idx].value, 4, getCommandManager());
        }
      } else if (data[idx].field && !data[idx].field->isGroup())
        data[idx].field->setField(objects[objectindex].object, data[idx].value,
                                  getCommandManager());
    }
  }

  if (objectindex && dataindex && data[dict.getStart() - 1].field &&
      data[dict.getStart() - 1].field->isPointer())
    // Update parent object
    data[dict.getStart() - 1].value.setObject(objects[objectindex].object);

  // Call the user exits
  if (getUserExit()) getUserExit().call(objects[objectindex].object);
  callUserExitCpp(objects[objectindex].object);

  // Update stack
  dataindex = objects[objectindex--].start - 1;
  return true;
}

bool JSONInput::StartArray() {
#ifdef PARSE_DEBUG
  logger << "Starting array" << endl;
#endif
  return true;
}

bool JSONInput::EndArray(rapidjson::SizeType elementCount) {
#ifdef PARSE_DEBUG
  logger << "Ending array" << endl;
#endif
  return true;
}

long JSONData::getLong() const {
  switch (data_type) {
    case JSON_NULL:
      return 0;
    case JSON_BOOL:
      return data_bool ? 1 : 0;
    case JSON_INT:
      return data_int;
    case JSON_LONG:
      return data_long;
    case JSON_UNSIGNEDLONG:
      return data_unsignedlong;
    case JSON_DOUBLE:
      if (data_double > LONG_MAX)
        return LONG_MAX;
      else if (data_double > LONG_MIN)
        return LONG_MIN;
      else
        return static_cast<long>(data_double);
    case JSON_STRING:
      return atol(data_string.c_str());
    case JSON_OBJECT:
      throw DataException("Invalid JSON data: no cast from object to long");
  }
  throw DataException("Unknown JSON type");
}

unsigned long JSONData::getUnsignedLong() const {
  switch (data_type) {
    case JSON_NULL:
      return 0;
    case JSON_BOOL:
      return data_bool ? 1 : 0;
    case JSON_INT:
      return data_int;
    case JSON_LONG:
      return data_long;
    case JSON_UNSIGNEDLONG:
      return data_unsignedlong;
    case JSON_DOUBLE:
      if (data_double > ULONG_MAX)
        return ULONG_MAX;
      else
        return static_cast<long>(data_double);
    case JSON_STRING:
      return atol(data_string.c_str());
    case JSON_OBJECT:
      throw DataException(
          "Invalid JSON data: no cast from object to unsigned long");
  }
  throw DataException("Unknown JSON type");
}

Duration JSONData::getDuration() const {
  switch (data_type) {
    case JSON_NULL:
      return Duration(0L);
    case JSON_BOOL:
      return Duration(data_bool ? 1L : 0L);
    case JSON_INT:
      return static_cast<long>(data_int);
    case JSON_LONG:
      return data_long;
    case JSON_UNSIGNEDLONG:
      return static_cast<double>(data_unsignedlong);
    case JSON_DOUBLE:
      return data_double;
    case JSON_STRING:
      return atol(data_string.c_str());
    case JSON_OBJECT:
      throw DataException("Invalid JSON data: no cast from object to duration");
  }
  throw DataException("Unknown JSON type");
}

int JSONData::getInt() const {
  switch (data_type) {
    case JSON_NULL:
      return 0;
    case JSON_BOOL:
      return data_bool ? 1 : 0;
    case JSON_INT:
      return data_int;
    case JSON_LONG:
      return data_long;
    case JSON_UNSIGNEDLONG:
      return data_unsignedlong;
    case JSON_DOUBLE:
      if (data_double > INT_MAX)
        return INT_MAX;
      else if (data_double > INT_MIN)
        return INT_MIN;
      else
        return static_cast<int>(data_double);
    case JSON_STRING:
      return atol(data_string.c_str());
    case JSON_OBJECT:
      throw DataException("Invalid JSON data: no cast from object to integer");
  }
  throw DataException("Unknown JSON type");
}

double JSONData::getDouble() const {
  switch (data_type) {
    case JSON_NULL:
      return 0;
    case JSON_BOOL:
      return data_bool ? 1 : 0;
    case JSON_INT:
      return data_int;
    case JSON_LONG:
      return data_long;
    case JSON_UNSIGNEDLONG:
      return data_unsignedlong;
    case JSON_DOUBLE:
      return data_double;
    case JSON_STRING:
      return atol(data_string.c_str());
    case JSON_OBJECT:
      throw DataException("Invalid JSON data: no cast from object to double");
  }
  throw DataException("Unknown JSON type");
}

Date JSONData::getDate() const {
  switch (data_type) {
    case JSON_NULL:
      return Date();
    case JSON_BOOL:
      return data_bool ? Date::infinitePast : Date::infiniteFuture;
    case JSON_INT:
      return Date(data_int);
    case JSON_LONG:
      return Date(data_long);
    case JSON_UNSIGNEDLONG:
      return Date(data_unsignedlong);
    case JSON_DOUBLE:
      return Date(static_cast<time_t>(data_double));
    case JSON_STRING:
      return Date(data_string.c_str());
    case JSON_OBJECT:
      throw DataException("Invalid JSON data: no cast from object to date");
  }
  throw DataException("Unknown JSON type");
}

const string& JSONData::getString() const {
  switch (data_type) {
    case JSON_NULL:
      const_cast<JSONData*>(this)->data_string = "";
      return data_string;
    case JSON_BOOL: {
      ostringstream convert;
      convert << data_bool;
      const_cast<JSONData*>(this)->data_string = convert.str();
      return data_string;
    }
    case JSON_INT: {
      ostringstream convert;
      convert << data_int;
      const_cast<JSONData*>(this)->data_string = convert.str();
      return data_string;
    }
    case JSON_LONG: {
      ostringstream convert;
      convert << data_long;
      const_cast<JSONData*>(this)->data_string = convert.str();
      return data_string;
    }
    case JSON_UNSIGNEDLONG: {
      ostringstream convert;
      convert << data_unsignedlong;
      const_cast<JSONData*>(this)->data_string = convert.str();
      return data_string;
    }
    case JSON_DOUBLE: {
      ostringstream convert;
      convert << data_double;
      const_cast<JSONData*>(this)->data_string = convert.str();
      return data_string;
    }
    case JSON_STRING:
      return data_string;
    case JSON_OBJECT:
      throw DataException("Invalid JSON data: no cast from object to string");
  }
  throw DataException("Unknown JSON type");
}

bool JSONData::getBool() const {
  switch (data_type) {
    case JSON_NULL:
      return false;
    case JSON_BOOL:
      return data_bool;
    case JSON_INT:
      return data_int != 0;
    case JSON_LONG:
      return data_long != 0;
    case JSON_UNSIGNEDLONG:
      return data_unsignedlong != 0;
    case JSON_DOUBLE:
      return data_double != 0;
    case JSON_STRING:
      return !data_string.empty();
    case JSON_OBJECT:
      return data_object != nullptr;
  }
  throw DataException("Unknown JSON type");
}

Object* JSONData::getObject() const {
  switch (data_type) {
    case JSON_NULL:
    case JSON_BOOL:
    case JSON_INT:
    case JSON_LONG:
    case JSON_UNSIGNEDLONG:
    case JSON_DOUBLE:
    case JSON_STRING:
      return nullptr;
    case JSON_OBJECT:
      return data_object;
  }
  throw DataException("Unknown JSON type");
}

void JSONDataValueDict::print() {
  for (auto i = strt; i <= nd; ++i) {
    if (fields[i].field)
      logger << "  " << i << "   " << fields[i].field->getName().getName()
             << ": ";
    else
      logger << "  " << i << "   null: ";
    Object* obj = static_cast<Object*>(fields[i].value.getObject());
    if (obj)
      logger << "pointer to " << obj->getType().type << endl;
    else
      logger << fields[i].value.getString() << endl;
  }
}

const JSONData* JSONDataValueDict::get(const Keyword& key) const {
  for (auto i = strt; i <= nd; ++i)
    if (fields[i].hash == key.getHash()) return &fields[i].value;
  return nullptr;
}

}  // namespace utils
}  // namespace frepple
