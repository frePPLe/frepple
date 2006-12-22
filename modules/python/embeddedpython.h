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
  * The XML schema extension enabled by this module is:
  * <PRE>
  *   <xsd:complexType name="COMMAND_PYTHON">
  *     <xsd:complexContent>
  *       <xsd:extension base="COMMAND">
  *         <xsd:choice minOccurs="0" maxOccurs="unbounded">
  * 					<xsd:element name="VERBOSE" type="xsd:boolean" />
  *           <xsd:element name="CMDLINE" type="xsd:string" />
  *           <xsd:element name="FILENAME" type="xsd:string" />
  *         </xsd:choice>
  *   			<xsd:attribute name="CMDLINE" type="xsd:string" />
  *   			<xsd:attribute name="FILENAME" type="xsd:string" />
  *       </xsd:extension>
  *     </xsd:complexContent>
  *   </xsd:complexType>
  * </PRE>
  *
  * The following Frepple functions are available from within Python.
  * All of these are in the module frepple.
  *   - version(): returns the version number of frepple
  */

/* Python.h has to appear first */
#include "Python.h"

#include "frepple.h"
using namespace frepple;


namespace module_python
{


/** This class embeds an interpreter for the Python language in Frepple.<br>
  * The interpreter can execute generic script, and it also has (limited)
  * access to the frepple objects.<br>
  * A single, global interpreter is used and only a single python command is
  * allowed to run simultaneously.
  */
class CommandPython : public Command
{
  private:
    /** The interpreter is not thread-safe. We allow only a single python
      * command to execute at the same time. 
      */
    static Mutex interpreterbusy;

    /** Command to be executed if the condition returns true. */
    string cmd;

    /** Command to be executed if the condition returns false. */
    string filename;

  public:
    /** A static array defining all methods that can be accessed from 
      * within Python. */
    static PyMethodDef PythonAPI[];

    /** Executes either the if- or the else-clause, depending on the 
      * condition. */
    void execute();

    /** Returns a descriptive string. */
    string getDescription() const {return "Python interpreter";}

    /** Default constructor. */
    explicit CommandPython() {}

    /** Destructor. */
    virtual ~CommandPython() {}

    /** Update the command line. */
    void setCommandLine(string s) {cmd = s; filename.clear();}

    /** Return the command line. */
    string getCommandLine() {return cmd;}

    /** Return the filename. */
    string getFileName() {return filename;}

    /** Update the filename. */
    void setFileName(string s) {filename = s; cmd.clear();}

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const 
      {return sizeof(CommandPython) + cmd.size() + filename.size();}

    void endElement(XMLInput& pIn, XMLElement& pElement);

  private:
    /** Python API: return a version string. */
    static PyObject *python_version(PyObject*, PyObject*);
};

}

