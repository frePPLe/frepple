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
 * Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
 *                                                                         *
 ***************************************************************************/

/** @file embeddedpython.h
  * @brief Header file for the module python.
  *
  * @namespace module_python
  * @brief An embedded interpreter for the Python language.
  *
  * A single interpreter is used throughout the lifetime of the
  * application.<br>
  * The implementation is implemented in a thread-safe way (within the
  * limitations of the Python threading model, of course).
  *
  * After loading, the module will check whether a file
  * '$FREPPLE_HOME/init.py' exists and, if it does, will execute the
  * statements in the file. In this way a library of globally available
  * functions can easily be initialized.
  *
  * The stderr and stdout streams of Python are redirected by default to
  * the frePPLe log stream.
  *
  * The XML schema extension enabled by this module is (see mod_python.xsd):
  * <PRE>
  *   <xsd:complexType name="COMMAND_PYTHON">
  *     <xsd:complexContent>
  *       <xsd:extension base="COMMAND">
  *         <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *           <xsd:element name="VERBOSE" type="xsd:boolean" />
  *           <xsd:element name="CMDLINE" type="xsd:string" />
  *           <xsd:element name="FILENAME" type="xsd:string" />
  *         </xsd:choice>
  *         <xsd:attribute name="CMDLINE" type="xsd:string" />
  *         <xsd:attribute name="FILENAME" type="xsd:string" />
  *       </xsd:extension>
  *     </xsd:complexContent>
  *   </xsd:complexType>
  * </PRE> The XML code can also include python code as a processing instruction:
  * <PRE>
  *   <?PYTHON your Python code comes here ?>
  * </PRE>
  *
  * The following frePPLe functions are available from within Python.<br>
  * All of these are in the module called frePPLe.
  *   - The following <b>classes</b> and their attributes are accessible for reading
  *     and writing.
  *       - buffer
  *       - buffer_default
  *       - buffer_infinite
  *       - buffer_procure
  *       - calendar
  *       - calendarBucket
  *       - calendar_boolean
  *       - calendar_double
  *       - calendar_void
  *       - customer
  *       - customer_default
  *       - demand
  *       - demand_default
  *       - flow
  *       - flowplan
  *       - item
  *       - item_default
  *       - load
  *       - loadplan
  *       - location
  *       - location_default
  *       - operation
  *       - operation_alternate
  *       - operation_fixed_time
  *       - operation_routing
  *       - operation_time_per
  *       - operationplan
  *       - parameters
  *       - problem  (read-only)
  *       - resource
  *       - resource_default
  *       - resource_infinite
  *       - solver
  *       - solver_mrp
  *   - The following functions or attributes return <b>iterators</b> over the
  *     frePPLe objects:<br>
  *       - buffers()
  *       - buffer.flows
  *       - buffer.flowplans
  *       - calendar.buckets
  *       - calendars()
  *       - customers()
  *       - demands()
  *       - demand.operationplans
  *       - demand.pegging
  *       - operation.flows
  *       - operation.loads
  *       - items()
  *       - locations()
  *       - operations()
  *       - operation.operationplans
  *       - problems()
  *       - resources()
  *       - resource.loads
  *       - resource.loadplans
  *       - solvers()
  *   - <b>readXMLdata(string [,bool] [,bool])</b>:<br>
  *     Processes an XML string passed as argument.
  *   - <b>log(string)</b>:<br>
  *     Prints a string to the frePPLe log file.<br>
  *     This is used for redirecting the stdout and stderr of Python.
  *   - <b>readXMLfile(string [,bool] [,bool])</b>:<br>
  *     Read an XML-file.
  *   - <b>saveXMLfile(string)</b>:<br>
  *     Save the model to an XML-file.
  *   - <b>saveXMLstring()</b>:<br>
  *     Returns the complete model as an XML-formatted string.<br>
  *   - <b>version</b>:<br>
  *     A string variable with the version number.
  *
  * Note that the interface between frePPLe and Python follows a 'proxy'
  * pattern. The Python objects are a temporary poxy only to the C++
  * objects. We stay away from a 'twin-object' approach.
  */

#ifndef PYTHON_H
#define PYTHON_H

/* Python.h has to be included first. */
#include "Python.h"
#include "datetime.h"

#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;


namespace module_python
{

// Include definitions of commonly used python utility functions
#include "pythonutils.h"

/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z);


/** @brief Python exception class matching with frepple::LogicException. */
extern PyObject* PythonLogicException;

/** @brief Python exception class matching with frepple::DataException. */
extern PyObject* PythonDataException;

/** @brief Python exception class matching with frepple::RuntimeException. */
extern PyObject* PythonRuntimeException;


/** @brief This command executes Python code in the embedded interpreter.
  *
  * The interpreter can execute generic scripts, and it also has access
  * to the frePPLe objects.<br>
  * The interpreter is multi-threaded. Multiple python scripts can run in
  * parallel. Internally Python allows only one thread at a time to
  * execute and the interpreter switches between the active threads, i.e.
  * a quite primitive threading model.<br>
  * FrePPLe uses a single global interpreter. A global Python variable or
  * function is thus visible across multiple invocations of the Python
  * interpreter.
  */
class CommandPython : public Command, public XMLinstruction
{
  private:
    /** This is the thread state of the main execution thread. */
    static PyThreadState *mainThreadState;

    /** Python commands to be executed. */
    string cmd;

    /** Python source file to be executed. */
    string filename;

    /** A static array defining all methods that can be accessed from
      * within Python. */
    static PyMethodDef PythonAPI[];

  public:
    /** Executes the python command or source file. */
    void execute();

    /** Returns a descriptive string. */
    string getDescription() const {return "Python interpreter";}

    /** Default constructor. */
    explicit CommandPython() {}

    /** Destructor. */
    virtual ~CommandPython() {}

    /** Update the commandline field and clears the filename field. */
    void setCommandLine(string s) {cmd = s; filename.clear();}

    /** Return the command line. */
    string getCommandLine() const {return cmd;}

    /** Return the filename. */
    string getFileName() const {return filename;}

    /** Update the filename field and clear the filename field. */
    void setFileName(string s) {filename = s; cmd.clear();}

    virtual const MetaClass& getType() const {return metadata;}
    /** Metadata for registration as a command. */
    static const MetaClass metadata;
    /** Metadata for registration as an XML instruction. */
    static const MetaClass metadata2;
    virtual size_t getSize() const
      {return sizeof(CommandPython) + cmd.size() + filename.size();}

    void endElement(XMLInput& pIn, XMLElement& pElement);

    /** This method is called when a processing instruction is read. */
    void processInstruction(XMLInput &i, const char *d) {executePython(d);}

    /** This is the workhorse that actually executes the argument string in
      * the Python interpreter. */
    void executePython(const char*);

    /** Initializes the python interpreter. */
    static void initialize();

  private:
    /** Python API: Used for redirecting the Python output to the same file
      * as the applciation. <br>
      * Arguments: data (string)
      */
    static PyObject *python_log(PyObject*, PyObject*);

    /** Python API: process an XML-formatted string.<br>
      * Arguments: data (string), validate (bool), checkOnly (bool)
      */
    static PyObject *python_readXMLdata(PyObject*, PyObject*);

    /** Python API: read an xml file.<br>
      * Arguments: data (string), validate (bool), checkOnly (bool)
      */
    static PyObject *python_readXMLfile(PyObject*, PyObject*);

    /** Python API: save the model to a XML-file.<br>
      * Arguments: filename (string)
      */
    static PyObject *python_saveXMLfile(PyObject*, PyObject*);

    /** Python API: return the model as an XML-formatted string.<br>
      * Arguments: none
      * Return: string
      */
    static PyObject *python_saveXMLstring(PyObject*, PyObject*);
};


// The following handler functions redirect the call from Python onto a
// matching virtual function in a PythonExtensionBase subclass.
extern "C"
{
  /** Handler function called from Python. Internal use only. */
  PyObject* getattro_handler (PyObject*, PyObject*);
  /** Handler function called from Python. Internal use only. */
  int setattro_handler (PyObject*, PyObject*, PyObject*);
  /** Handler function called from Python. Internal use only. */
  int compare_handler (PyObject*, PyObject*);
  /** Handler function called from Python. Internal use only. */
  PyObject* iternext_handler (PyObject*);
  /** Handler function called from Python. Internal use only. */
  PyObject* call_handler(PyObject*, PyObject*, PyObject*);
  /** Handler function called from Python. Internal use only. */
  PyObject* str_handler(PyObject*);
}


/** @brief This class is a wrapper around the type information in Python.
  *
  * In the Python C API this is represented by the PyTypeObject structure.
  * This class defines a number of convenience functions to update and maintain
  * the type information.
  */
class PythonType : public NonCopyable
{
  private:
    /** This static variable is a template for cloning type definitions.<br>
      * It is copied for each type object we create.
      */
    static const PyTypeObject PyTypeObjectTemplate;

    /** Accumulator of method definitions. */
    vector<PyMethodDef> methodvector;    

    /** Real method table created after initialization. */
    PyMethodDef *methods;        

  public:
    /** A static functin that evaluates an exception and sets the Python 
      * error string properly.<br>
      * This function should only be called from within a catch-block, since 
      * it rethrows the exception!
      */
    static void evalException();

    /** Constructor, sets the tp_base_size member. */
    PythonType (size_t base_size);

    /** Return a pointer to the actual Python PyTypeObject. */
    PyTypeObject* type_object() const {return const_cast<PyTypeObject*>(&table);}

    /** Add a new method. */
    void addMethod(const char*, PyCFunction, int, const char*);

    /** Updates tp_name. */
    void setName (const string n)
    {
      name = "frepple." + n;
      table.tp_name = const_cast<char*>(name.c_str());
    }

    /** Updates tp_doc. */
    void setDoc (const string n)
    {
      doc = n;
      table.tp_doc = const_cast<char*>(doc.c_str());
    }

    /** Updates tp_base. */
    void setBase(PythonType& b)
    {
      table.tp_base = &b.table;
    }

    /** Updates the deallocator. */
    void dealloc(void (*f)(PyObject*))
    {
      table.tp_dealloc = f;
    }

    /** Updates tp_getattro.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PythonObject getattro(const XMLElement& name)
      */
    void supportgetattro() {table.tp_getattro = getattro_handler;}

    /** Updates tp_setattro.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   int setattro(const XMLElement& name, const PythonObject& value)
      */
    void supportsetattro() {table.tp_setattro = setattro_handler;}

    /** Updates tp_compare.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   int compare(const PythonObject& other)
      */
    void supportcompare() {table.tp_compare = compare_handler;}

    /** Updates tp_iter and tp_iternext.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* iternext()
      */
    void supportiter()
    {
      table.tp_iter = PyObject_SelfIter;
      table.tp_iternext = iternext_handler;
    }

    /** Updates tp_call.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* call(const PythonObject& args, const PythonObject& kwds)
      */
    void supportcall() {table.tp_call = call_handler;}

    /** Updates tp_str.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* str()
      */
    void supportstr() {table.tp_str = str_handler;}

    /** Type definition for create functions. */
    typedef PyObject* (*createfunc)(PyTypeObject*, PyObject*, PyObject*);

    /** Updates tp_new with the function passed as argument. */
    void supportcreate(createfunc c) {table.tp_new = c;}

    /** This method needs to be called after the type information has all
      * been updated. It adds the type to the module that is passed as
      * argument. */
    int typeReady(PyObject* m);

  private:
    /** The type object, as it is used by Python. */
    PyTypeObject table;

    /** Class name. */
    string name;

    /** Documentation string. */
    string doc;
};


/** @brief This class handles two-way translation between the data types
  * in C++ and Python.
  *
  * This class is basically a wrapper around a PyObject pointer.
  *
  * When creating a PythonObject from a C++ object, make sure to increment
  * the reference count of the object.<br>
  * When constructing a PythonObject from an existing Python object, the
  * code that provided us the PyObject pointer should have incremented the
  * reference count already.
  *
  *@todo endelement function should be shared with setattro function.
  *Unifies the python and xml worlds: shared code base to update objects!
  *(Code for extracting info is still python specific, and writeElement
  *is also xml-specific)
  *  xml->prevObject = python->cast value to a different type
  *
  * @todo improper use of the python proxy objects can crash the application.
  * It is possible to keep the Python proxy around longer than the C++
  * object. Re-accessing the proxy will crash frePPLe.
  * We need a handler to subscribe to the C++ delete, which can then invalidate the
  * Python object.
  */
class PythonObject : public NonCopyable
{
  private:
    PyObject* obj;

  public:
    /** Default constructor. The default value is equal to Py_None. */
    explicit PythonObject() : obj(Py_None) {Py_INCREF(obj);}

    /** Constructor from an existing Python object.<br>
      * The reference count isn't increased.
      */
    PythonObject(PyObject* o) : obj(o) {}

    /** This conversion operator casts the object back to a PyObject pointer. */
    operator PyObject*() const {return obj;}

    /** Check for null value. */
    operator bool() const {return obj != NULL;}

    /** Check whether the Python object is of a certain type.<br>
      * Subclasses of the argument type will also give a true return value.
      */
    bool check(const PythonType& c) const
    {
      return obj ?
        PyObject_TypeCheck(obj, c.type_object()) :
        false;
    }

    /** Convert a Python string into a C++ string. */
    inline string getString() const
    {
      if (obj == Py_None) return string();
      if (PyUnicode_Check(obj))
      {
        // Replace the unicode object with a string encoded in the correct locale
        const_cast<PyObject*&>(obj) =
          PyUnicode_AsEncodedString(obj, NULL, "ignore");   // xxx test@todo need generic encoding of unicode objects to the locale understood by frepple
      }
      return PyString_AsString(PyObject_Str(obj));
    }

    /** Convert a Python datetime.date or datetime.datetime object into a
      * frePPLe date. */
    Date getDate() const;

    /** Convert a Python number into a C++ double. */
    inline double getDouble() const
    {
      if (obj == Py_None) return 0;
      return PyFloat_AsDouble(obj);
    }

    /** Convert a Python number into a C++ integer. */
    inline int getInt() const
    {
      int result = PyInt_AsLong(obj);
	  if (result == -1 && PyErr_Occurred())
		  throw DataException("Invalid number");
	  return result;
    }

    /** Convert a Python number into a C++ long. */
    inline long getLong() const
    {
      int result = PyInt_AsLong(obj);
	  if (result == -1 && PyErr_Occurred())
		  throw DataException("Invalid number");
	  return result;
	}

    /** Convert a Python number into a C++ bool. */
    inline bool getBool() const
    {
      return PyObject_IsTrue(obj) ? true : false;
    }

    /** Convert a Python number as a number of seconds into a frePPLe
      * TimePeriod.<br>
	  * A TimePeriod is represented as a number of seconds in Python.
	  */
    TimePeriod getTimePeriod() const
    {
      int result = PyInt_AsLong(obj);
	  if (result == -1 && PyErr_Occurred())
		  throw DataException("Invalid number");
	  return result;
  	}

    /** Constructor from a pointer to an Object.<br>
      * The metadata of the Object instances allow us to create a Python
      * object that works as a proxy for the C++ object.
      */
    PythonObject(Object* p);

    /** Convert a C++ string into a (raw) Python string. */
    inline PythonObject(const string& val)
    {
      if (val.empty())
      {
        obj = Py_None;
        Py_INCREF(obj);
      }
      else
        obj = PyString_FromString(val.c_str());
    }

    /** Convert a C++ double into a Python number. */
    inline PythonObject(const double val)
    {
      obj = PyFloat_FromDouble(val);
    }

    /** Convert a C++ integer into a Python integer. */
    inline PythonObject(const int val)
    {
      obj = PyInt_FromLong(val);
    }

    /** Convert a C++ long into a Python long. */
    inline PythonObject(const long val)
    {
      obj = PyLong_FromLong(val);
    }

    /** Convert a C++ unsigned long into a Python long. */
    inline PythonObject(const unsigned long val)
    {
      obj = PyLong_FromUnsignedLong(val);
    }

    /** Convert a C++ boolean into a Python boolean. */
    inline PythonObject(const bool val)
    {
      obj = val ? Py_True : Py_False;
      Py_INCREF(obj);
    }

    /** Convert a frePPLe TimePeriod into a Python number representing
      * the number of seconds. */
    inline PythonObject(const TimePeriod val)
    {
      // A TimePeriod is represented as a number of seconds in Python
      obj = PyLong_FromLong(val);
    }

    /** Convert a frePPLe date into a Python datetime.datetime object. */
    PythonObject(const Date& val);
};


/** @brief This is a base class for all Python extension types.
  *
  * When creating you own extensions, inherit from the PythonExtension
  * template class instead of this one.
  *
  * It inherits from the PyObject C struct, defined in the Python C API.<br>
  * These functions aren't called directly from Python. Python first calls a
  * handler C-function and the handler function will use a virtual call to
  * run the correct C++-method.
  *
  * Our extensions don't use the usual Python heap allocator. They are
  * created and initialized with the regular C++ new and delete. A special
  * deallocator is called from Python to delete objects when their reference
  * count reaches zero.
  */
class PythonExtensionBase : public PyObject
{
  public:
    /** Constructor */
    PythonExtensionBase() {}

    /** Destructor. */
    virtual ~PythonExtensionBase() {}

    /** Default getattro method. <br>
      * Subclasses are expected to implement an override if the type supports
      * gettattro.
      */
    virtual PyObject* getattro(const XMLElement& name)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'getattro'");
      return NULL;
    }

    /** Default setattro method. <br>
      * Subclasses are expected to implement an override if the type supports
      * settattro.
      */
    virtual int setattro(const XMLElement& name, const PythonObject& value)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'setattro'");
      return -1;
    }

    /** Default compare method. <br>
      * Subclasses are expected to implement an override if the type supports
      * compare.
      */
    virtual int compare(const PythonObject& other)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'compare'");
      return -1;
    }

    /** Default iternext method. <br>
      * Subclasses are expected to implement an override if the type supports
      * iteration.
      */
    virtual PyObject* iternext()
    {
      PyErr_SetString(PythonLogicException, "Missing method 'iternext'");
      return NULL;
    }

    /** Default call method. <br>
      * Subclasses are expected to implement an override if the type supports
      * calls.
      */
    virtual PyObject* call(const PythonObject& args, const PythonObject& kwds)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'call'");
      return NULL;
    }

    /** Default str method. <br>
      * Subclasses are expected to implement an override if the type supports
      * conversion to a string.
      */
    virtual PyObject* str()
    {
      PyErr_SetString(PythonLogicException, "Missing method 'str'");
      return NULL;
    }
};


/** @brief Template class to define Python extensions.
  *
  * The template argument should be your extension class, inheriting from
  * this template class:
  *   class MyClass : PythonExtension<MyClass>
  */
template<class T>
class PythonExtension: public PythonExtensionBase, public NonCopyable
{
  public:
    /** Constructor. */
    explicit PythonExtension()
    {
      PyObject_INIT(this, getType().type_object());
    }

    /** Destructor. */
    virtual ~PythonExtension() {}

    /** This method keeps the type information object for your extension. */
    static PythonType& getType()
    {
      static PythonType* table = NULL;
      if (!table)
      {
        table = new PythonType(sizeof(T));
        table->dealloc( deallocator );
      }
      return *table;
    }

    /** Free the memory.<br>
      * See the note on the memory management in the class documentation
      * for PythonExtensionBase.
      */
    static void deallocator(PyObject* o) {delete static_cast<T*>(o);}
};


/** @brief A template class to expose category classes which use a string
  * as the key to Python . */
template <class ME, class PROXY>
class FreppleCategory : public PythonExtension< FreppleCategory<ME,PROXY> >
{
  public:
    /** Initialization method. */
    static int initialize(PyObject* m)
    {
      // Initialize the type
      PythonType& x = PythonExtension< FreppleCategory<ME,PROXY> >::getType();
      x.setName(PROXY::metadata.type);
      x.setDoc("frePPLe " + PROXY::metadata.type);
      x.supportgetattro();
      x.supportsetattro();
      x.supportstr();
      x.supportcompare();
      x.supportcreate(create);
      const_cast<MetaCategory&>(PROXY::metadata).factoryPythonProxy = proxy;
      return x.typeReady(m);
    }

    static void* proxy(Object* p) {return static_cast<PyObject*>(new ME(static_cast<PROXY*>(p)));}

    /** Constructor. */
    FreppleCategory(PROXY* x = NULL) : obj(x) {}

  public: // @todo should not be public
    PROXY* obj;

  private:
    virtual PyObject* getattro(const XMLElement&) = 0;

    virtual int setattro(const XMLElement&, const PythonObject&) = 0;

    /** Return the name as the string representation in Python. */
    PyObject* str()
    {
      return PythonObject(obj ? obj->getName() : "None");
    }

    /** Comparison operator. */
    int compare(const PythonObject& other)
    {
      if (!other.check(ME::getType()))
      {
        // Different type
        PyErr_SetString(PythonDataException, "Wrong type in comparison");
        return -1;
      }
      PROXY* y = static_cast<ME*>(static_cast<PyObject*>(other))->obj;
      return obj->getName().compare(y->getName());     
    }

    static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    {
      // Check presence of keyword arguments
      if (!kwds)
      {
        PyErr_SetString(PythonDataException, "Missing keyword arguments");
        return NULL;
      }

      // Pick up the name attribute.
      PyObject* name = PyDict_GetItemString(kwds,"name");
      if (!name)
      {
        PyErr_SetString(PythonDataException, "No name argument specified");
        return NULL;
      }

      // Pick up the type attribute.
      string type = "default";
      PyObject* typekwd = PyDict_GetItemString(kwds,"type");
      if (typekwd)
        type = string(PyString_AsString(PyObject_Str(typekwd)));

      // Create the C++ object
      const MetaClass* j = PROXY::metadata.findClass(type.c_str());
      if (!j)
      {
        PyErr_Format(PythonDataException, 
          "No type %s registered for category %s",
          type, PROXY::metadata.type.c_str());
        return NULL;
      }
      PROXY* x = PROXY::add(string(PyString_AsString(PyObject_Str(name))), *j);

      // Create a python proxy
      PythonExtensionBase* pr = static_cast<PythonExtensionBase*>(static_cast<PyObject*>(*(new PythonObject(x))));

      // Iterate over extra keywords, and set attributes.
      if (pr)
      {
        try
        {
          PyObject *key, *value;
          Py_ssize_t pos = 0;
          while (PyDict_Next(kwds, &pos, &key, &value))
          {
            XMLElement field(PyString_AsString(key));
            if (!field.isA(Tags::tag_name) && !field.isA(Tags::tag_type))
            {
              int result = pr->setattro(field, value);
              if (result)
                PyErr_Format(PyExc_AttributeError,
                  "attribute '%s' on '%s' can't be updated",
                  PyString_AsString(key), pr->ob_type->tp_name);
            }
          };
        }
        catch (...)
        {
          PythonType::evalException();
          delete pr;
          return NULL;
        }
      }
      return pr;
    }
};


/** @brief A template class to expose classes to Python. */
template <class ME, class BASE, class PROXY>
class FreppleClass  : public PythonExtension< FreppleClass<ME,BASE,PROXY> >
{
  public:
    static int initialize(PyObject* m)
    {
      // Initialize the type
      PythonType& x = PythonExtension< FreppleClass<ME,BASE,PROXY> >::getType();
      x.setName(PROXY::metadata.type);
      x.setDoc("frePPLe " + PROXY::metadata.type);
      x.supportgetattro();
      x.supportsetattro();
      x.supportstr();
      x.supportcompare();
      x.supportcreate(create);
      x.setBase(BASE::getType());
      const_cast<MetaClass&>(PROXY::metadata).factoryPythonProxy = proxy;
      return x.typeReady(m);
    }

    static void* proxy(Object* p) {return static_cast<PyObject*>(new ME(static_cast<PROXY*>(p)));}

    FreppleClass(PROXY* p= NULL) : obj(p) {}

  public: // @todo should not be public
    PROXY* obj;

  private:
    virtual PyObject* getattro(const XMLElement&) = 0;

    /** Comparison operator. */
    int compare(const PythonObject& other)
    {
      if (!other.check(BASE::getType()))
      {
        // Different type
        PyErr_SetString(PythonDataException, "Wrong type in comparison");
        return -1;
      }
      BASE* y = static_cast<BASE*>(static_cast<PyObject*>(other));
      return obj->getName().compare(y->obj->getName());
    }

    virtual int setattro(const XMLElement&, const PythonObject&) = 0;

    /** Return the name as the string representation in Python. */
    PyObject* str()
    {
      return PythonObject(obj ? obj->getName() : "None");
    }

    static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    {
      // Check presence of keyword arguments
      if (!kwds)
      {
        PyErr_SetString(PythonDataException, "Missing keyword arguments");
        return NULL;
      }

      // Pick up the name attribute.
      PyObject* name = PyDict_GetItemString(kwds,"name");
      if (!name)
      {
        PyErr_SetString(PythonDataException, "No name argument specified");
        return NULL;
      }

      // Create the C++ object
      PROXY* x = reinterpret_cast<PROXY*>(PROXY::add(string(PyString_AsString(PyObject_Str(name))), PROXY::metadata));

      // Create a python proxy
      ME* pr = new ME(x);

      // Iterate over extra keywords, and set attributes.
      if (pr)
      {
        try
        {
          PyObject *key, *value;
          Py_ssize_t pos = 0;
          bool  nok =false;
          while (PyDict_Next(kwds, &pos, &key, &value))
          {
            XMLElement field(PyString_AsString(key));
            if (!field.isA(Tags::tag_name))
            {
              int result = pr->setattro(field, value);
              if (result)
                PyErr_Format(PyExc_AttributeError,
                  "attribute '%s' on '%s' can't be updated",
                  PyString_AsString(key), pr->ob_type->tp_name);
            }
          };
        }
        catch (...)
        {
          PythonType::evalException();
          delete pr;
          return NULL;
        }
      }

      return static_cast<PyObject*>(pr);
    }
};


/** @brief A template class to expose iterators to Python. */
template <class ME, class ITERCLASS, class DATACLASS, class PROXYCLASS>
class FreppleIterator : public PythonExtension<ME>
{
  public:
    static int initialize(PyObject* m)
    {
      // Initialize the type
      PythonType& x = PythonExtension<ME>::getType();
      x.setName(DATACLASS::metadata.type + "Iterator");
      x.setDoc("frePPLe iterator for " + DATACLASS::metadata.type);
      x.supportiter();
      return x.typeReady(m);
    }

    FreppleIterator() : i(DATACLASS::begin()) {}

    static PyObject* create(PyObject* self, PyObject* args)
      {return new ME();}

  private:
    ITERCLASS i;
    virtual PyObject* iternext()
    {
      if (i == DATACLASS::end()) return NULL;
      PyObject* result = PythonObject(&*i);
      ++i;
      return result;
    }
};


//
// SETTINGS
//


/** @brief This class exposes global plan information to Python. */
class PythonPlan : public PythonExtension<PythonPlan>
{
  public:
    static int initialize(PyObject* m);
  private:
    PyObject* getattro(const XMLElement&);
    int setattro(const XMLElement&, const PythonObject&);
};


//
// PROBLEMS
//


class PythonProblem : public PythonExtension<PythonProblem>
{
  public:
    static int initialize(PyObject* m);
    PythonProblem(Problem* p) : prob(p) {}
    static void* proxy(Object* p)
      {return static_cast<PyObject*>(new PythonProblem(static_cast<Problem*>(p)));}
  private:
    PyObject* getattro(const XMLElement&);
    Problem* prob;
};


class PythonProblemIterator
  : public FreppleIterator<PythonProblemIterator,Problem::const_iterator,Problem,PythonProblem>
{
};


//
// BUFFERS
//


class PythonBuffer : public FreppleCategory<PythonBuffer,Buffer>
{
  public:
    PythonBuffer(Buffer* p) : FreppleCategory<PythonBuffer,Buffer>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonBufferIterator
  : public FreppleIterator<PythonBufferIterator,Buffer::iterator,Buffer,PythonBuffer>
{
};


class PythonBufferDefault : public FreppleClass<PythonBufferDefault,PythonBuffer,BufferDefault>
{
  public:
    PythonBufferDefault(BufferDefault* p)
      : FreppleClass<PythonBufferDefault,PythonBuffer,BufferDefault>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonBufferInfinite : public FreppleClass<PythonBufferInfinite,PythonBuffer,BufferInfinite>
{
  public:
    PythonBufferInfinite(BufferInfinite* p)
      : FreppleClass<PythonBufferInfinite,PythonBuffer,BufferInfinite>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonBufferProcure : public FreppleClass<PythonBufferProcure,PythonBuffer,BufferProcure>
{
  public:
    PythonBufferProcure(BufferProcure* p)
      : FreppleClass<PythonBufferProcure,PythonBuffer,BufferProcure>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// LOCATIONS
//


class PythonLocation : public FreppleCategory<PythonLocation,Location>
{
  public:
    PythonLocation(Location* p) : FreppleCategory<PythonLocation,Location>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonLocationIterator
  : public FreppleIterator<PythonLocationIterator,Location::iterator,Location,PythonLocation>
{
};


class PythonLocationDefault : public FreppleClass<PythonLocationDefault,PythonLocation,LocationDefault>
{
  public:
    PythonLocationDefault(LocationDefault* p)
      : FreppleClass<PythonLocationDefault,PythonLocation,LocationDefault>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// CUSTOMERS
//


class PythonCustomer : public FreppleCategory<PythonCustomer,Customer>
{
  public:
    PythonCustomer(Customer* p) : FreppleCategory<PythonCustomer,Customer>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonCustomerIterator
  : public FreppleIterator<PythonCustomerIterator,Customer::iterator,Customer,PythonCustomer>
{
};


class PythonCustomerDefault : public FreppleClass<PythonCustomerDefault,PythonCustomer,CustomerDefault>
{
  public:
    PythonCustomerDefault(CustomerDefault* p)
      : FreppleClass<PythonCustomerDefault,PythonCustomer,CustomerDefault>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// ITEMS
//


class PythonItem : public FreppleCategory<PythonItem,Item>
{
  public:
    PythonItem(Item* p) : FreppleCategory<PythonItem,Item>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonItemIterator
  : public FreppleIterator<PythonItemIterator,Item::iterator,Item,PythonItem>
{
};


class PythonItemDefault : public FreppleClass<PythonItemDefault,PythonItem,ItemDefault>
{
  public:
    PythonItemDefault(ItemDefault* p)
      : FreppleClass<PythonItemDefault,PythonItem,ItemDefault>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// CALENDARS
//


class PythonCalendar : public FreppleCategory<PythonCalendar,Calendar>
{
  public:
    PythonCalendar(Calendar* p) : FreppleCategory<PythonCalendar,Calendar>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonCalendarIterator
  : public FreppleIterator<PythonCalendarIterator,Calendar::iterator,Calendar,PythonCalendar>
{
};


class PythonCalendarBucketIterator
  : public PythonExtension<PythonCalendarBucketIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonCalendarBucketIterator(Calendar* c) : cal(c)
    {
      if (!c)
        throw LogicException("Creating bucket iterator for NULL calendar");
      i = c->beginBuckets();
    }

  private:
    Calendar* cal;
    Calendar::BucketIterator i;
    PyObject *iternext();
};


class PythonCalendarBucket
  : public PythonExtension<PythonCalendarBucket>
{
  public:
    static int initialize(PyObject* m);
    PythonCalendarBucket(Calendar* c, Calendar::Bucket* b) : cal(c), obj(b) {}
  private:
    Calendar::Bucket* obj;
    Calendar* cal;
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
    // @todo static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
};


class PythonCalendarVoid : public FreppleClass<PythonCalendarVoid,PythonCalendar,CalendarVoid>
{
  public:
    PythonCalendarVoid(CalendarVoid* p)
      : FreppleClass<PythonCalendarVoid,PythonCalendar,CalendarVoid>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonCalendarBool : public FreppleClass<PythonCalendarBool,PythonCalendar,CalendarBool>
{
  public:
    PythonCalendarBool(CalendarBool* p)
      : FreppleClass<PythonCalendarBool,PythonCalendar,CalendarBool>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonCalendarDouble : public FreppleClass<PythonCalendarDouble,PythonCalendar,CalendarDouble>
{
  public:
    PythonCalendarDouble(CalendarDouble* p)
      : FreppleClass<PythonCalendarDouble,PythonCalendar,CalendarDouble>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// DEMANDS
//


class PythonDemand : public FreppleCategory<PythonDemand,Demand>
{
  public:
    PythonDemand(Demand* p) : FreppleCategory<PythonDemand,Demand>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonDemandIterator
  : public FreppleIterator<PythonDemandIterator,Demand::iterator,Demand,PythonDemand>
{
};


class PythonDemandDefault : public FreppleClass<PythonDemandDefault,PythonDemand,DemandDefault>
{
  public:
    PythonDemandDefault(DemandDefault* p)
      : FreppleClass<PythonDemandDefault,PythonDemand,DemandDefault>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// RESOURCES
//


class PythonResource : public FreppleCategory<PythonResource,Resource>
{
  public:
    PythonResource(Resource* p) : FreppleCategory<PythonResource,Resource>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonResourceIterator
  : public FreppleIterator<PythonResourceIterator,Resource::iterator,Resource,PythonResource>
{
};


class PythonResourceDefault : public FreppleClass<PythonResourceDefault,PythonResource,ResourceDefault>
{
  public:
    PythonResourceDefault(ResourceDefault* p)
      : FreppleClass<PythonResourceDefault,PythonResource,ResourceDefault>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonResourceInfinite : public FreppleClass<PythonResourceInfinite,PythonResource,ResourceInfinite>
{
  public:
    PythonResourceInfinite(ResourceInfinite* p)
      : FreppleClass<PythonResourceInfinite,PythonResource,ResourceInfinite>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// OPERATIONS
//


class PythonOperation : public FreppleCategory<PythonOperation,Operation>
{
  public:
    PythonOperation(Operation* p) : FreppleCategory<PythonOperation,Operation>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonOperationIterator
  : public FreppleIterator<PythonOperationIterator,Operation::iterator,Operation,PythonOperation>
{
};


class PythonOperationAlternate : public FreppleClass<PythonOperationAlternate,PythonOperation,OperationAlternate>
{
  public:
    PythonOperationAlternate(OperationAlternate* p)
      : FreppleClass<PythonOperationAlternate,PythonOperation,OperationAlternate>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonOperationFixedTime : public FreppleClass<PythonOperationFixedTime,PythonOperation,OperationFixedTime>
{
  public:
    PythonOperationFixedTime(OperationFixedTime* p)
      : FreppleClass<PythonOperationFixedTime,PythonOperation,OperationFixedTime>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonOperationTimePer : public FreppleClass<PythonOperationTimePer,PythonOperation,OperationTimePer>
{
  public:
    PythonOperationTimePer(OperationTimePer* p)
      : FreppleClass<PythonOperationTimePer,PythonOperation,OperationTimePer>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonOperationRouting : public FreppleClass<PythonOperationRouting,PythonOperation,OperationRouting>
{
  public:
    PythonOperationRouting(OperationRouting* p)
      : FreppleClass<PythonOperationRouting,PythonOperation,OperationRouting>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


//
// OPERATIONPLANS
//


class PythonOperationPlan : public PythonExtension<PythonOperationPlan>
{
  public:
    static int initialize(PyObject* m);
    PythonOperationPlan(OperationPlan* p) : obj(p) {}
    static void* proxy(Object* p)
      {return static_cast<PyObject*>(new PythonOperationPlan(static_cast<OperationPlan*>(p)));}
  private:
    OperationPlan* obj;
    // @todo static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds);    "id"+"operation" keywords used
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};


class PythonOperationPlanIterator
  : public FreppleIterator<PythonOperationPlanIterator,OperationPlan::iterator,OperationPlan,PythonOperationPlan>
{
};


//
// FLOWPLANS
//


class PythonFlowPlan : public PythonExtension<PythonFlowPlan>
{
  public:
    static int initialize(PyObject* m);
    PythonFlowPlan(FlowPlan* p) : fl(p) {}
  private:
    PyObject* getattro(const XMLElement&);
    FlowPlan* fl;
};


class PythonFlowPlanIterator : public PythonExtension<PythonFlowPlanIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonFlowPlanIterator(Buffer* b) : buf(b)
    {
      if (!b)
        throw LogicException("Creating flowplan iterator for NULL buffer");
      i = b->getFlowPlans().begin();
    }

  private:
    Buffer* buf;
    Buffer::flowplanlist::const_iterator i;
    PyObject *iternext();
};


//
// LOADPLANS
//


class PythonLoadPlan : public PythonExtension<PythonLoadPlan>
{
  public:
    static int initialize(PyObject* m);
    PythonLoadPlan(LoadPlan* p) : fl(p) {}
  private:
    PyObject* getattro(const XMLElement&);
    LoadPlan* fl;
};


class PythonLoadPlanIterator : public PythonExtension<PythonLoadPlanIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonLoadPlanIterator(Resource* r) : res(r)
    {
      if (!r)
        throw LogicException("Creating loadplan iterator for NULL resource");
      i = r->getLoadPlans().begin();
    }

  private:
    Resource* res;
    Resource::loadplanlist::const_iterator i;
    PyObject *iternext();
};


//
// DEMAND DELIVERY OPERATIONPLANS
//


class PythonDemandPlanIterator : public PythonExtension<PythonDemandPlanIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonDemandPlanIterator(Demand* r) : dem(r)
    {
      if (!r)
        throw LogicException("Creating demandplan iterator for NULL demand");
      i = r->getDelivery().begin();
    }

  private:
    Demand* dem;
    Demand::OperationPlan_list::const_iterator i;
    PyObject *iternext();
};


//
// DEMAND PEGGING
//


class PythonPeggingIterator : public PythonExtension<PythonPeggingIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonPeggingIterator(Demand* r) : dem(r), i(r)
    {
      if (!r)
        throw LogicException("Creating pegging iterator for NULL demand");
    }

  private:
    Demand* dem;
    PeggingIterator i;
    PyObject *iternext();
};


//
// LOADS
//


class PythonLoad : public PythonExtension<PythonLoad>
{
  public:
    static int initialize(PyObject* m);
    PythonLoad(Load* p) : ld(p) {}
  private:
    PyObject* getattro(const XMLElement&);
    int setattro(const XMLElement&, const PythonObject&);
    // @todo static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    static void* proxy(Object* p) {return static_cast<PyObject*>(new PythonLoad(static_cast<Load*>(p)));}
    Load* ld;
};


class PythonLoadIterator : public PythonExtension<PythonLoadIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonLoadIterator(Resource* r)
      : res(r), ir(r ? r->getLoads().begin() : NULL), oper(NULL), io(NULL)
    {
      if (!r)
        throw LogicException("Creating loadplan iterator for NULL resource");
    }

    PythonLoadIterator(Operation* o)
      : res(NULL), ir(NULL), oper(o), io(o ? o->getLoads().begin() : NULL)
    {
      if (!o)
        throw LogicException("Creating loadplan iterator for NULL operation");
    }

  private:
    Resource* res;
    Resource::loadlist::const_iterator ir;
    Operation* oper;
    Operation::loadlist::const_iterator io;
    PyObject *iternext();
};


//
// FLOW
//


class PythonFlow : public PythonExtension<PythonFlow>
{
  public:
    static int initialize(PyObject* m);
    PythonFlow(Flow* p) : fl(p) {}
  private:
    PyObject* getattro(const XMLElement&);
    // @todo static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    int setattro(const XMLElement&, const PythonObject&);
    static void* proxy(Object* p) {return static_cast<PyObject*>(new PythonFlow(static_cast<Flow*>(p)));}
    Flow* fl;
};


class PythonFlowIterator : public PythonExtension<PythonFlowIterator>
{
  public:
    static int initialize(PyObject* m);

    PythonFlowIterator(Buffer* b)
      : buf(b), ib(b ? b->getFlows().begin() : NULL), oper(NULL), io(NULL)
    {
      if (!b)
        throw LogicException("Creating flowplan iterator for NULL buffer");
    }

    PythonFlowIterator(Operation* o)
      : buf(NULL), ib(NULL), oper(o), io(o ? o->getFlows().begin() : NULL)
    {
      if (!o)
        throw LogicException("Creating flowplan iterator for NULL operation");
    }

  private:
    Buffer* buf;
    Buffer::flowlist::const_iterator ib;
    Operation* oper;
    Operation::flowlist::const_iterator io;
    PyObject *iternext();
};


//
// SOLVERS
//


class PythonSolver : public FreppleCategory<PythonSolver,Solver>
{
  public:
    static int initialize(PyObject* m)
    {
      getType().addMethod("solve", solve, METH_NOARGS, "run the solver");
      return FreppleCategory<PythonSolver,Solver>::initialize(m);
    }
    PythonSolver(Solver* p) : FreppleCategory<PythonSolver,Solver>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
    static PyObject* solve(PyObject*, PyObject*);
};


class PythonSolverIterator
  : public FreppleIterator<PythonSolverIterator,Solver::iterator,Solver,PythonSolver>
{
};


class PythonSolverMRP : public FreppleClass<PythonSolverMRP,PythonSolver,SolverMRP>
{
  public:
    PythonSolverMRP(SolverMRP* p)
      : FreppleClass<PythonSolverMRP,PythonSolver,SolverMRP>(p) {}
    virtual PyObject* getattro(const XMLElement&);
    virtual int setattro(const XMLElement&, const PythonObject&);
};

}

#endif
