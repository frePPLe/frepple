/***************************************************************************
  file : $URL: https://frepple.svn.sourceforge.net/svnroot/frepple/trunk/modules/lp_solver/lpsolver.h $
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
  * the Frepple log stream.
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
  * The following Frepple functions are available from within Python.<br>
  * All of these are in the module called frepple.
  *   - <b>version</b>:<br> 
  *     A string variable with the version of frepple.
  *   - <b>readXMLdata(string [,bool] [,bool])</b>:<br> 
  *     Processes an XML string passed as argument.
  *   - <b>log(string)</b>:<br>
  *     Prints a string to the frepple log file.<br>
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
  *   - class <b>frepple.iterator</b>:<br>
  *     Implements an iterator for problems.
  */

/* Python.h has to be included first. */
#include "Python.h"

#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;


namespace module_python
{


/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z);


/** This class embeds an interpreter for the Python language in Frepple.<br>
  * The interpreter can execute generic scripts, and it also has (currently 
  * quite limited) access to the frepple objects.<br>
  * The interpreter is multi-threaded. Multiple python scripts can run in
  * parallel. Internally Python allows only one thread at a time to
  * execute and the interpreter switches between the active threads, i.e.
  * a quite primitive threading model.<br>
  * Frepple uses a single global interpreter. A global Python variable or
  * function is thus visible across multiple invocations of the Python 
  * interpreter.
  */
class CommandPython : public Command, public XMLinstruction
{
  private:
    /** This is the thread state of the main execution thread. */
    static PyThreadState *mainThreadState;

    /** Command to be executed if the condition returns true. */
    string cmd;

    /** Command to be executed if the condition returns false. */
    string filename;

    /** A static array defining all methods that can be accessed from
      * within Python. */
    static PyMethodDef PythonAPI[];

  public:
    /** Executes either the if- or the else-clause, depending on the
      * condition. */
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
      * directly interacts with the frepple C++ API, without passing through
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

    /** Python exception class matching with Frepple::LogicException. */
    static PyObject* PythonLogicException;

    /** Python exception class matching with Frepple::DataException. */
    static PyObject* PythonDataException;

    /** Python exception class matching with Frepple::RuntimeException. */
    static PyObject* PythonRuntimeException;
};


extern "C"
{
/** This class is an interface between Python and the Frepple. */
struct PythonIterator
{
  private:
    PyObject_HEAD
    Problem::const_iterator iter;
  public:
    /** Python type definition structure. */
    static PyTypeObject InfoType;

    /** Returns a string representation of the iterator. */
    static PyObject* repr(PythonIterator* obj);

    /** Move to the next item. */
    static PyObject* next(PythonIterator* obj);

    /** Create a new iterator. */
    static PyObject* create(PyTypeObject* type, PyObject *args, PyObject *kwargs);
};
}

}

