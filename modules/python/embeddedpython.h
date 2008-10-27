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
  *   <xsd:complexType name="command_python">
  *     <xsd:complexContent>
  *       <xsd:extension base="command">
  *         <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *           <xsd:element name="verbose" type="xsd:boolean" />
  *           <xsd:element name="cmdline" type="xsd:string" />
  *           <xsd:element name="filename" type="xsd:string" />
  *         </xsd:choice>
  *         <xsd:attribute name="cmdline" type="xsd:string" />
  *         <xsd:attribute name="filename" type="xsd:string" />
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

/* PythonUtils.h has to be included first.*/
#include "../python/pythonutils.h"

#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;


namespace module_python
{


// For compatibility with earlier Python releases
#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
#endif

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

    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement);

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


//
// SETTINGS
//


/** @brief This class exposes global plan information to Python. */
class PythonPlan : public PythonExtension<PythonPlan>
{
  public:
    static int initialize(PyObject* m);
  private:
    PyObject* getattro(const Attribute&);
    int setattro(const Attribute&, const PythonObject&);
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
    PyObject* getattro(const Attribute&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonBufferInfinite : public FreppleClass<PythonBufferInfinite,PythonBuffer,BufferInfinite>
{
  public:
    PythonBufferInfinite(BufferInfinite* p)
      : FreppleClass<PythonBufferInfinite,PythonBuffer,BufferInfinite>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonBufferProcure : public FreppleClass<PythonBufferProcure,PythonBuffer,BufferProcure>
{
  public:
    PythonBufferProcure(BufferProcure* p)
      : FreppleClass<PythonBufferProcure,PythonBuffer,BufferProcure>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


//
// LOCATIONS
//


class PythonLocation : public FreppleCategory<PythonLocation,Location>
{
  public:
    PythonLocation(Location* p) : FreppleCategory<PythonLocation,Location>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


//
// CUSTOMERS
//


class PythonCustomer : public FreppleCategory<PythonCustomer,Customer>
{
  public:
    PythonCustomer(Customer* p) : FreppleCategory<PythonCustomer,Customer>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


//
// ITEMS
//


class PythonItem : public FreppleCategory<PythonItem,Item>
{
  public:
    PythonItem(Item* p) : FreppleCategory<PythonItem,Item>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


//
// CALENDARS
//


class PythonCalendar : public FreppleCategory<PythonCalendar,Calendar>
{
  public:
    PythonCalendar(Calendar* p) : FreppleCategory<PythonCalendar,Calendar>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
    // @todo static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
};


class PythonCalendarVoid : public FreppleClass<PythonCalendarVoid,PythonCalendar,CalendarVoid>
{
  public:
    PythonCalendarVoid(CalendarVoid* p)
      : FreppleClass<PythonCalendarVoid,PythonCalendar,CalendarVoid>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonCalendarBool : public FreppleClass<PythonCalendarBool,PythonCalendar,CalendarBool>
{
  public:
    PythonCalendarBool(CalendarBool* p)
      : FreppleClass<PythonCalendarBool,PythonCalendar,CalendarBool>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonCalendarDouble : public FreppleClass<PythonCalendarDouble,PythonCalendar,CalendarDouble>
{
  public:
    PythonCalendarDouble(CalendarDouble* p)
      : FreppleClass<PythonCalendarDouble,PythonCalendar,CalendarDouble>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


//
// DEMANDS
//


class PythonDemand : public FreppleCategory<PythonDemand,Demand>
{
  public:
    PythonDemand(Demand* p) : FreppleCategory<PythonDemand,Demand>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


//
// RESOURCES
//


class PythonResource : public FreppleCategory<PythonResource,Resource>
{
  public:
    PythonResource(Resource* p) : FreppleCategory<PythonResource,Resource>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonResourceInfinite : public FreppleClass<PythonResourceInfinite,PythonResource,ResourceInfinite>
{
  public:
    PythonResourceInfinite(ResourceInfinite* p)
      : FreppleClass<PythonResourceInfinite,PythonResource,ResourceInfinite>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


//
// OPERATIONS
//


class PythonOperation : public FreppleCategory<PythonOperation,Operation>
{
  public:
    PythonOperation(Operation* p) : FreppleCategory<PythonOperation,Operation>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationFixedTime : public FreppleClass<PythonOperationFixedTime,PythonOperation,OperationFixedTime>
{
  public:
    PythonOperationFixedTime(OperationFixedTime* p)
      : FreppleClass<PythonOperationFixedTime,PythonOperation,OperationFixedTime>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationTimePer : public FreppleClass<PythonOperationTimePer,PythonOperation,OperationTimePer>
{
  public:
    PythonOperationTimePer(OperationTimePer* p)
      : FreppleClass<PythonOperationTimePer,PythonOperation,OperationTimePer>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationRouting : public FreppleClass<PythonOperationRouting,PythonOperation,OperationRouting>
{
  public:
    PythonOperationRouting(OperationRouting* p)
      : FreppleClass<PythonOperationRouting,PythonOperation,OperationRouting>(p) {}
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    static PyObject* create(PyTypeObject*, PyObject*, PyObject*);
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};


class PythonOperationPlanIterator
  : public FreppleIterator<PythonOperationPlanIterator,OperationPlan::iterator,OperationPlan,PythonOperationPlan>
{
  public:
    /** Constructor to iterate over all operationplans. */
    PythonOperationPlanIterator() {}

    /** Constructor to iterate over the operationplans of a single operation. */
    PythonOperationPlanIterator(Operation* o)
      : FreppleIterator<PythonOperationPlanIterator,OperationPlan::iterator,OperationPlan,PythonOperationPlan>(o)
    {}
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
    PyObject* getattro(const Attribute&);
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
    PyObject* getattro(const Attribute&);
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
    PyObject* getattro(const Attribute&);
    int setattro(const Attribute&, const PythonObject&);
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
    PyObject* getattro(const Attribute&);
    // @todo static PyObject* create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)  issue: construction & validation of floaws is a bit different....   
    int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
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
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
};

}

#endif
