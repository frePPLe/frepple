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

/** @file pythonutils.h
  * @brief Reusable functions for python functionality.
  *
  * @namespace frepple::python
  * @brief Utility classes for interfacing to and from the Python language.
  */

#ifndef PYTHONUTILS_H
#define PYTHONUTILS_H

/* Python.h has to be included first. 
   For a debugging build on windows we avoid using the debug version of Python
   since that also requires Python and all its modules to be compiled in debug
   mode.
*/
#if defined(_DEBUG) && defined(_MSC_VER)
#undef _DEBUG
#include "Python.h"
#define _DEBUG
#else
#include "Python.h"
#endif
#include "datetime.h"

#include "frepple/utils.h"
using namespace frepple::utils;

namespace frepple
{
namespace python
{


// For compatibility with earlier Python releases
#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
#endif


/** An initialization routine for the library. */
void initialize();


/** @brief This class is used to maintain the Python interpreter.
  *
  * A single interpreter is used throughout the lifetime of the
  * application.<br>
  * The implementation is implemented in a thread-safe way (within the
  * limitations of the Python threading model, of course).
  *
  * During the initialization the code checks for a file 'init.py' in its 
  * search path and, if it does exist, the statements in the file will be
  * executed. In this way a library of globally available functions
  * can easily be initialized.
  *
  * The stderr and stdout streams of Python are redirected by default to
  * the frePPLe log stream.
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
  *   - <b>erase(boolean)</b>:<br>
  *     Erase the model (arg true) or only the plan (arg false, default).
  *   - <b>version</b>:<br>
  *     A string variable with the version number.
  */
class PythonInterpreter
{
  public:
    /** Initializes the interpreter. */
    static void initialize();

    /** Execute some python code. */
    static DECLARE_EXPORT void execute(const char*);

    /** Register a new method to Python.<br>
      * Arguments:
      * - The name of the built-in function/method
      * - The function that implements it.
      * - Combination of METH_* flags, which mostly describe the args 
      *   expected by the C func.
      * - The __doc__ attribute, or NULL.
      */
    static DECLARE_EXPORT void registerGlobalMethod(
      const char*, PyCFunction, int, const char*, bool = true	
     );

    /** Return a pointer to the main extension module. */
    static DECLARE_EXPORT PyObject* getModule() { return module; }

    /** Return the preferred encoding of the Python interpreter. */
    static const char* getPythonEncoding() { return encoding.c_str(); }

  private:
    /** A pointer to the frePPLe extension module. */  
    static PyObject *module;

    /** This is the thread state of the main execution thread. */
    static PyThreadState *mainThreadState;

    /** Python API: Used for redirecting the Python output to the same file
      * as the applciation. <br>
      * Arguments: data (string)
      */
    static DECLARE_EXPORT PyObject *python_log(PyObject*, PyObject*);

    /** Python unicode strings are encoded to this locale when bringing them into
      * frePPLe.<br>
      */
    static DECLARE_EXPORT string encoding;
};


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
    /** Python commands to be executed. */
    string cmd;

    /** Python source file to be executed. */
    string filename;

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

    void DECLARE_EXPORT endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement);

    /** This method is called when a processing instruction is read. */
    void processInstruction(XMLInput &i, const char *d) 
      {PythonInterpreter::execute(d);}
};


/** @brief Python exception class matching with frepple::LogicException. */
extern DECLARE_EXPORT PyObject* PythonLogicException;

/** @brief Python exception class matching with frepple::DataException. */
extern DECLARE_EXPORT PyObject* PythonDataException;

/** @brief Python exception class matching with frepple::RuntimeException. */
extern DECLARE_EXPORT PyObject* PythonRuntimeException;


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
   /** A static function that evaluates an exception and sets the Python
      * error string properly.<br>
      * This function should only be called from within a catch-block, since
      * internally it rethrows the exception!
      */
    static DECLARE_EXPORT void evalException();

    /** Constructor, sets the tp_base_size member. */
    DECLARE_EXPORT PythonType(size_t base_size);

    /** Return a pointer to the actual Python PyTypeObject. */
    PyTypeObject* type_object() const {return const_cast<PyTypeObject*>(&table);}

    /** Add a new method. */
    DECLARE_EXPORT void addMethod(char*, PyCFunction, int, char*);

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
    DECLARE_EXPORT void supportgetattro() 
      {table.tp_getattro = getattro_handler;}

    /** Updates tp_setattro.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   int setattro(const Attribute& attr, const PythonObject& field)
      */
    DECLARE_EXPORT void supportsetattro() 
      {table.tp_setattro = setattro_handler;}

    /** Updates tp_compare.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   int compare(const PythonObject& other)
      */
    DECLARE_EXPORT void supportcompare() 
      {table.tp_compare = compare_handler;}

    /** Updates tp_iter and tp_iternext.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* iternext()
      */
    DECLARE_EXPORT void supportiter()
    {
      table.tp_iter = PyObject_SelfIter;
      table.tp_iternext = iternext_handler;
    }

    /** Updates tp_call.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* call(const PythonObject& args, const PythonObject& kwds)
      */
    DECLARE_EXPORT void supportcall() 
      {table.tp_call = call_handler;}

    /** Updates tp_str.<br>
      * The extension class will need to define a member function with this
      * prototype:<br>
      *   PyObject* str()
      */
    DECLARE_EXPORT void supportstr() 
      {table.tp_str = str_handler;}

    /** Type definition for create functions. */
    typedef PyObject* (*createfunc)(PyTypeObject*, PyObject*, PyObject*);

    /** Updates tp_new with the function passed as argument. */
    void supportcreate(createfunc c) {table.tp_new = c;}

    /** This method needs to be called after the type information has all
      * been updated. It adds the type to the module that is passed as
      * argument. */
    DECLARE_EXPORT int typeReady(PyObject* m);

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
  * @todo endelement function should be shared with setattro function.
  * Unifies the python and xml worlds: shared code base to update objects!
  * (Code for extracting info is still python specific, and writeElement
  * is also xml-specific)
  * xml->prevObject = python->cast value to a different type
  *
  * @todo object creator should be common with the XML reader, which uses
  * the registered factory method.
  * Also supports add/add_change/remove.
  * Tricky: flow/load which use an additional validate() method
  *
  * @todo improper use of the python proxy objects can crash the application.
  * It is possible to keep the Python proxy around longer than the C++
  * object. Re-accessing the proxy will crash frePPLe.
  * We need a handler to subscribe to the C++ delete, which can then invalidate the
  * Python object. Alternative solution is to move to a twin object approach:
  * a C++ object and a python object always coexist as a twin pair.
  */
class PythonObject : public DataElement
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

    /** Assignment operator. */
    PythonObject& operator = (const PythonObject& o) { obj = o.obj; return *this; }

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
          PyUnicode_AsEncodedString(obj, PythonInterpreter::getPythonEncoding(), "ignore");
      }
      return PyString_AsString(PyObject_Str(obj));
    }

    /** Extract an unsigned long from the Python object. */
    unsigned long getUnsignedLong() const
    {
      return PyLong_AsUnsignedLong(obj);
    }

    /** Convert a Python datetime.date or datetime.datetime object into a
      * frePPLe date. */
    DECLARE_EXPORT Date getDate() const;

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
    TimePeriod getTimeperiod() const
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
    DECLARE_EXPORT PythonObject(Object* p);

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
    DECLARE_EXPORT PythonObject(const Date& val);
};


/** @brief This class is a wrapper around a Python dictionary. */
class PythonAttributeList : public AttributeList
{
  private:
    PyObject* kwds;
    PythonObject result;   // @todo we don't want such an element as member...

  public:
    PythonAttributeList(PyObject* a) : kwds(a) {}

    virtual const DataElement* get(const Keyword& k) const
    {
      if (!kwds)
      {
        const_cast<PythonAttributeList*>(this)->result = PythonObject();
        return &result;
      }
      PyObject* val = PyDict_GetItemString(kwds,k.getName().c_str());
      const_cast<PythonAttributeList*>(this)->result = PythonObject(val);
      return &result;
    }
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
    virtual PyObject* getattro(const Attribute& attr)
    {
      PyErr_SetString(PythonLogicException, "Missing method 'getattro'");
      return NULL;
    }

    /** Default setattro method. <br>
      * Subclasses are expected to implement an override if the type supports
      * settattro.
      */
    virtual int setattro(const Attribute& attr, const PythonObject& field)
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
    virtual PyObject* getattro(const Attribute&) = 0;

    virtual int setattro(const Attribute&, const PythonObject&) = 0;

    /** Return the name as the string representation in Python. */
    PyObject* str()
    {
      return PythonObject(obj ? obj->getName() : "None");
    }

    /** Comparison operator. */
    int compare(const PythonObject& other)
    {
      if (!obj || !other.check(ME::getType()))
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
      try
      {
        // Find or create the C++ object
        PythonAttributeList atts(kwds);
        Object* x = PROXY::reader(PROXY::metadata,atts);

        // Create a python proxy
        PythonExtensionBase* pr = static_cast<PythonExtensionBase*>(static_cast<PyObject*>(*(new PythonObject(x))));

        // Iterate over extra keywords, and set attributes. @todo move this responsability to the readers...
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(kwds, &pos, &key, &value))
        {
          PythonObject field(value);
          Attribute attr(PyString_AsString(key));
          if (!attr.isA(Tags::tag_name) && !attr.isA(Tags::tag_type) && !attr.isA(Tags::tag_action))
          {
            int result = pr->setattro(attr, field);
            if (result)
              PyErr_Format(PyExc_AttributeError,
                "attribute '%s' on '%s' can't be updated",
                PyString_AsString(key), pr->ob_type->tp_name);
          }
        };
        return pr;

      }
      catch (...)
      {
        PythonType::evalException();
        return NULL;
      }
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

    /** Comparison operator. */
    int compare(const PythonObject& other)
    {
      if (!obj || !other.check(BASE::getType()))
      {
        // Different type
        PyErr_SetString(PythonDataException, "Wrong type in comparison");
        return -1;
      }
      BASE* y = static_cast<BASE*>(static_cast<PyObject*>(other));
      return obj->getName().compare(y->obj->getName());
    }

    /** Return the name as the string representation in Python. */
    PyObject* str()
    {
      return PythonObject(obj ? obj->getName() : "None");
    }

    static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
    {
      try
      {
        // Find or create the C++ object
        PythonAttributeList atts(kwds);
        Object* x = PROXY::reader(PROXY::metadata,atts);

        // Create a python proxy
        PythonExtensionBase* pr = static_cast<PythonExtensionBase*>(static_cast<PyObject*>(*(new PythonObject(x))));

        // Iterate over extra keywords, and set attributes.   @todo move this responsability to the readers...
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(kwds, &pos, &key, &value))
        {
          PythonObject field(value);
          Attribute attr(PyString_AsString(key));
          if (!attr.isA(Tags::tag_name) && !attr.isA(Tags::tag_type) && !attr.isA(Tags::tag_action))
          {
            int result = pr->setattro(attr, field);
            if (result)
              PyErr_Format(PyExc_AttributeError,
                "attribute '%s' on '%s' can't be updated",
                PyString_AsString(key), pr->ob_type->tp_name);
          }
        };
        return pr;

      }
      catch (...)
      {
        PythonType::evalException();
        return NULL;
      }
    }

  public: // @todo should not be public
    PROXY* obj;

  private:
    virtual PyObject* getattro(const Attribute&) = 0;

    virtual int setattro(const Attribute&, const PythonObject&) = 0;

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

    template <class OTHER> FreppleIterator(const OTHER *o) : i(o) {}

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

} // end namespace
} // end namespace
#endif  // End of PYTHONUTILS_H
