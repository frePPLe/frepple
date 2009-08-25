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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 *
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/

/** @file lpsolver.h
  * @brief Header file for the module lp_solver.
  *
  * @namespace module_lp_solver
  * @brief A solver module based on a linear programming algorithm.
  *
  * The solver is intended primarly for prototyping purposes. Cleaner and
  * more performant alternatives are recommended for real production use.
  *
  * The module uses the "Gnu Linear Programming Kit" library (aka GLPK) to
  * solve the LP model.<br>
  * The solver works as follows:
  * - The solver expects a <b>model file</b> and a <b>data file</b> as input.<br>
  *   The model file represents the mathematical representation of the 
  *   problem to solve.<br>
  *   The data file holds the data to be loaded into the problem. If no
  *   data file is specified, the data section in the model file is used 
  *   instead.<br>
  *   The user is responsible for creating these files. See the unit test
  *   lp_solver1 for an example.
  * - The solver solves for a number of objectives in sequence.<br>
  *   After solving an objective's optimal value, the solver freezes the 
  *   value as a constraint and start for the next objective. Subsequent 
  *   objectives can thus never yield a solution that is suboptimal for the
  *   previous objectives.
  * - After solving for all objectives the solution is written to a solution
  *   file.<br>
  *   The user is responsible for all processing of this solution file.
  *
  * The XML schema extension enabled by this module is (see mod_lpsolver.xsd):
  * <PRE>
  * <xsd:complexType name="solver_lp">
  *   <xsd:complexContent>
  *     <xsd:extension base="solver">
  *       <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *         <xsd:element name="loglevel" type="loglevel" />
  *         <xsd:element name="minimum" type="xsd:boolean" />
  *         <xsd:element name="modelfile" type="xsd:normalizedString" />
  *         <xsd:element name="datafile" type="xsd:normalizedString" />
  *         <xsd:element name="solutionfile" type="xsd:normalizedString" />
  *         <xsd:element name="objective" type="xsd:normalizedString" />
  *       </xsd:choice>
  *       <xsd:attribute name="loglevel" type="loglevel" />
  *       <xsd:attribute name="minimum" type="xsd:boolean" />
  *       <xsd:attribute name="modelfile" type="xsd:normalizedString" />
  *       <xsd:attribute name="datafile" type="xsd:normalizedString" />
  *       <xsd:attribute name="solutionfile" type="xsd:normalizedString" />
  *       <xsd:attribute name="objective" type="xsd:normalizedString" />
  *     </xsd:extension>
  *   </xsd:complexContent>
  * </xsd:complexType>
  * </PRE>
  */

#include "frepple.h"
using namespace frepple;

extern "C"
{
#if defined HAVE_GLPK_H || !defined HAVE_GLPK_GLPK_H
#include "glpk.h"
#else
#ifdef HAVE_GLPK_GLPK_H
#include "glpk/glpk.h"
#endif
#endif
}

namespace module_lp_solver
{

/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z);

/** @brief This class is a prototype of an Linear Programming (LP) Solver for
  * the planning problem or a subset of it.
  *
  * The solver is intended primarly for prototyping purposes. Cleaner and
  * more performant alternatives are recommended for real production use.
  */
class LPSolver : public Solver
{
  public:
    /** This method creates a new column in the model for every demand. It's
      * value represents the planned quantity of that demand.
      * @exception DataException Generated when no calendar has been specified.
      */
    void solve(void* = NULL);

    /** Return the name of the GNU MathProg model file. */
    string getModelFile() const {return modelfilename;}

    /** Update the name of the GNU MathProg model file. */
    void setModelFile(const string& c) {modelfilename = c;}

    /** Return the name of the GNU MathProg data file. */
    string getDataFile() const {return datafilename;}

    /** Update the name of the GNU MathProg data file. */
    void setDataFile(const string& c) {datafilename = c;}

    /** Return the name of the solution file. */
    string getSolutionFile() const {return solutionfilename;}

    /** Update the name of the solution file. <br>
      * After running the solver the solution is written to this flat file.
      */
    void setSolutionFile(const string& c) {solutionfilename = c;}

    /** Returns true when the solver needs to minimize the objective(s).<br>
      * Returns false when the solver needs to maximize the objective(s).
      */
    bool getMinimum() const {return minimum;}

    /** Update the solver direction: minimization or maximization. */
    void setMinimum(bool m) {minimum = m;}

    /** Append a new objective to the list. */
    void addObjective(const string& c) { objectives.push_back(c); }

	  /** Return a reference to the list of objectives. */
	  const list<string>& getObjectives() const {return objectives;}
	
    virtual void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement);
    virtual PyObject* getattro(const Attribute&);
    virtual int setattro(const Attribute&, const PythonObject&);
    static int initialize();

	  /** Constructor. */
    LPSolver(const string& n) : Solver(n), minimum(true) {initType(metadata);}
	
	  /** Destructor. */
    ~LPSolver() {};

    virtual const MetaClass& getType() const {return *metadata;}
    static const MetaClass *metadata;
    virtual size_t getSize() const {return sizeof(LPSolver);}

  private:
    /** This is an auxilary function. GLPK requires names to contain only
      * "graphic" characters. A space isn't one of those. Since our model
      * can contain HasHierarchy names with a space, we call this function to
      * replace the spaces with underscores.<br>
      * Note however that we can't garantuee that the updated strings are
      * all unique after the replacement!
      */
    static string replaceSpaces(const string&);

    /** This object is the interface with the GLPK structures. */
    LPX* lp;

    /** Storing simplex configuration paramters. */
    glp_smcp parameters;

    /** A list of model columns to use as objectives. */
    list<string> objectives;

    /** Direction of the solver: minimization or maximization. */
    bool minimum;

    /** Name of the model file.<br>
      * This field is required.*/
    string modelfilename;

    /** Name of the data file.<br>
      * If the field is left empty, the data section in the model file is
      * used instead.
      */
    string datafilename;

    /** Name of the solution file.<br>
      * If the field is left empty, the solution is not exported.
      */
    string solutionfilename;

    /** A hook to intercept the terminal output of the solver library, and
      * redirect it into the frePPLe log file. 
      */
    static int solveroutputredirect(void* info, const char* msg)
    {
      logger << msg;
      logger.flush();
      return 1;
    }

    /** Solve for a goal in a hierarchical sequence. */
    void solveObjective(const string&);
};

}  // End namespace
