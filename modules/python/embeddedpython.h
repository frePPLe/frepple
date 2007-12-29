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
  * limitations of the Python threading model, of course).<br>
  * After loading, the module will check whether a file
  * '$FREPPLE_HOME/init.py' exists and, if it does, will execute the
  * statements in the file. In this way a library of globally available
  * functions can easily be initialized.<br>
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
  *   - <b>version</b>:<br>
  *     A string variable with the version number.
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
  *     Returns the complete model as an XML-formatted string.
  *   - <b>createItem(string, string)</b>:<br>
  *     Uses the C++ API to create an item and its delivery operation.<br>
  *     For experimental purposes...
  *   - class <b>frepple.problem</b>:<br>
  *     Implements an iterator for problems.
  *   - class <b>frepple.operationplan</b>:<br>
  *     Implements an iterator for operationplans.
  *   - class <b>frepple.demand</b>:<br>
  *     Implements an iterator for demand, its delivery operationplans
  *     and its pegging.
  *   - class <b>frepple.buffer</b>:<br>
  *     Implements an iterator for buffer and its flowplans.
  *   - class <b>frepple.resource</b>:<br>
  *     Implements an iterator for resource and its loadplans.
  *
  * Note that the interface between frePPLe and Python is an iterator,
  * and we stay away from the 'twin-object' approach. This is because
  * we want frePPLe to remain the owner of all data.
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


/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z);


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

    /** This static variable is a template for defining our Python
      * objects.<br>
      * It is copied for each interface object we define.
      */
    static const PyTypeObject TemplateInfoType;

  public:
    /** This template function initializes a structure as a Python class.<br>
      * The class passed as template argument must have a verify specific
      * structure: see the examples.
      */
    template<class X> static void define_type(PyObject* m, const string& a, const string& b)
    {
      // Copy the default type information, and overwrite some fields
      memcpy(&X::InfoType, &TemplateInfoType, sizeof(PyTypeObject));
      X::InfoType.tp_basicsize =	sizeof(X);
      X::InfoType.tp_iternext = reinterpret_cast<iternextfunc>(X::next);
      X::InfoType.tp_new = X::create;
      X::InfoType.tp_dealloc = reinterpret_cast<destructor>(X::destroy);
      // Note: We need to 'leak' the strings allocated on the next two lines!
      string *aa = new string(string("frepple.") + a);
      string *bb = new string(b);
      X::InfoType.tp_name = const_cast<char*>(aa->c_str());
      X::InfoType.tp_doc = const_cast<char*>(bb->c_str());

      // Allow for type-specific registration code;
      X::define_type();

      // Register the new type in the module
      if (PyType_Ready(&X::InfoType) < 0)
      {
        PyEval_ReleaseLock();
        throw frepple::RuntimeException("Can't register python type " + a);
      }
      Py_INCREF(&X::InfoType);
      PyModule_AddObject(m, const_cast<char*>(a.c_str()), reinterpret_cast<PyObject*>(&X::InfoType));
    }

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
    string getCommandLine() {return cmd;}

    /** Return the filename. */
    string getFileName() {return filename;}

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

    /** Python API: Create an item and a delivery operation. This function
      * directly interacts with the frePPLe C++ API, without passing through
      * XML.<br>
      * This function is intended for experimental and demonstration purposes
      * only.<br>
      * Arguments: item name (string), operation name (string)
      */
    static PyObject *python_createItem(PyObject*, PyObject*);

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

    /** Python exception class matching with frepple::LogicException. */
    static PyObject* PythonLogicException;

    /** Python exception class matching with frepple::DataException. */
    static PyObject* PythonDataException;

    /** Python exception class matching with frepple::RuntimeException. */
    static PyObject* PythonRuntimeException;
};


/** Conversion between the frePPLe date class and the Python datetime class. */
PyObject* PythonDateTime(const Date& d);


extern "C"
{


  /** @brief This class exports Problem information to Python. */
  struct PythonProblem
  {
    private:
      PyObject_HEAD
      Problem::const_iterator *iter;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonProblem*);
      static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
      static void destroy(PythonProblem* obj)
      {delete obj->iter; PyObject_Del(obj);}
      static void define_type() {}
  };


  /** @brief This class exports FlowPlan information to Python. */
  struct PythonFlowPlan
  {
    private:
      PyObject_HEAD
      Buffer::flowplanlist::const_iterator iter;
      Buffer* buf;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonFlowPlan*);
      static PyObject* create(PyTypeObject* type, PyObject *args, PyObject *kwargs) {return NULL;}
      static void destroy(PythonFlowPlan* obj) {PyObject_Del(obj);}
      static void define_type() { InfoType.tp_new = 0; }
      static PyObject* createFromBuffer(Buffer*);
  };


  /** @brief This class exports LoadPlan information to Python. */
  struct PythonLoadPlan
  {
    private:
      PyObject_HEAD
      Resource::loadplanlist::const_iterator iter;
      Resource* res;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonLoadPlan*);
      static PyObject* create(PyTypeObject* type, PyObject *args, PyObject *kwargs) {return NULL;}
      static void destroy(PythonLoadPlan* obj) {PyObject_Del(obj);}
      static void define_type() { InfoType.tp_new = 0; }
      static PyObject* createFromResource(Resource*);
  };


  /** @brief This class exports demand pegging information to Python. */
  struct PythonDemandPegging
  {
    private:
      PyObject_HEAD
      PeggingIterator* iter;
      Demand* dem;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonDemandPegging*);
      static PyObject* create(PyTypeObject* , PyObject *args, PyObject *kwargs) {return NULL;}
      static void destroy(PythonDemandPegging* obj)
      {delete obj->iter; PyObject_Del(obj);}
      static void define_type() { InfoType.tp_new = 0; }
      static PyObject* createFromDemand(Demand*);
  };


  /** @brief This class exports OperationPlan information to Python. */
  struct PythonOperationPlan
  {
    private:
      PyObject_HEAD
      OperationPlan::iterator iter;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonOperationPlan*);
      static PyObject* create(PyTypeObject* , PyObject *, PyObject *);
      static void destroy(PythonOperationPlan* obj) {PyObject_Del(obj);}
      static void define_type() {}
  };


  /** @brief This class exports Demand information to Python. */
  struct PythonDemand
  {
    private:
      PyObject_HEAD
      Demand::iterator iter;
      PyObject* peggingiterator;
      PyObject* deliveryiterator;      
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonDemand*);
      static PyObject* create(PyTypeObject*, PyObject *, PyObject *);
      static void destroy(PythonDemand* obj) 
      {
        if (obj->peggingiterator) Py_DECREF(obj->peggingiterator);
        if (obj->deliveryiterator) Py_DECREF(obj->deliveryiterator);
        PyObject_Del(obj);
      }
      static void define_type() {}
  };


  /** @brief This class exports a delivery operationplan iterator to Python. */
  struct PythonDemandDelivery
  {
    private:
      PyObject_HEAD
      Demand::OperationPlan_list::const_iterator iter;
      const Demand* dem;
      const Demand* dem_owner;
      double cumPlanned;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonDemandDelivery*);
      static PyObject* create(PyTypeObject* type, PyObject *args, PyObject *kwargs) {return NULL;}
      static void destroy(PythonDemandDelivery* obj) {PyObject_Del(obj);}
      static void define_type() {}
      static PyObject* createFromDemand(Demand*);
  };


  /** @brief This class exports Buffer information to Python. */
  struct PythonBuffer
  {
    private:
      PyObject_HEAD
      Buffer::iterator iter;
      PyObject* flowplaniterator;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonBuffer*);
      static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
      static void destroy(PythonBuffer* obj) 
      {
        if (obj->flowplaniterator) Py_DECREF(obj->flowplaniterator);
        PyObject_Del(obj);
      }
      static void define_type() {}
  };


  /** @brief This class exports Resource information to Python. */
  struct PythonResource
  {
    private:
      PyObject_HEAD
      Resource::iterator iter;
      PyObject* loadplaniterator;
    public:
      static PyTypeObject InfoType;
      static PyObject* next(PythonResource*);
      static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
      static void destroy(PythonResource* obj) 
      {
        if (obj->loadplaniterator) Py_DECREF(obj->loadplaniterator);
        PyObject_Del(obj);
      }
      static void define_type() {}
  };


}  // End extern "C"


}

#endif
