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

/** @file lpsolver.h
  * @brief Header file for the module lp_solver.
  *
  * @namespace module_lp_solver
  * @brief A solver module based on a linear programming algorithm.
  *
  * The module is currently in beta-mode: it is usable as a proof of concept, 
  * but isn't finished yet as an out-of-the-box integrated solver. 
  *
  * The linear programming problem definition is very flexible.<br>
  * As a prototyping example, a capacity allocation problem is used. 
  * Different business problems will obviously require a different formulation. 
  *
  * The module uses the "Gnu Linear Programming Kit" library (aka GLPK) to
  * solve the LP model.
  *
  * The XML schema extension enabled by this module is (see mod_lpsolver.xsd):
  * <PRE>
  * <xsd:complexType name="solver_lp">
  *   <xsd:complexContent>
  *     <xsd:extension base="solver">
  *       <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *         <xsd:element name="verbose" xsi:type="xsd:boolean" />
  *         <xsd:element name="calendar" xsi:type="calendar" />
  *       </xsd:choice>
  *     </xsd:extension>
  *   </xsd:complexContent>
  * </xsd:complexType>
  * </PRE>
  */

#include "frepple.h"
using namespace frepple;

extern "C"
{
#include "glpk.h"
}

namespace module_lp_solver
{

/** Initialization routine for the library. */
MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z);

/** @brief This class is a prototype of an Linear Programming (LP) Solver for
  * the planning problem or a subset of it.
  *
  * The class provides only a concept / prototype, and it is definately not
  * ready for full use in a production environment. It misses too much
  * functionality for this purpose.
  */
class LPSolver : public Solver
{
  public:
    /** This method creates a new column in the model for every demand. It's
      * value represents the planned quantity of that demand.
      * @exception DataException Generated when no calendar has been specified.
      */
    void solve(void* = NULL);

    Calendar* getCalendar() const {return cal;}
    void setCalendar(Calendar* c) {cal = c;}

    void beginElement(XMLInput& pIn, const Attribute& pAttr);
    virtual void writeElement(XMLOutput*, const Keyword&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement);

    LPSolver(const string n) : Solver(n), cal(NULL) {};
    ~LPSolver() {};

    virtual const MetaClass& getType() const {return metadata;}
    static const MetaClass metadata;
    virtual size_t getSize() const {return sizeof(LPSolver);}

  private:
    /** This is an auxilary function. GLPK requires names to contain only
      * "graphic" characters. A space isn't one of those. Since our model
      * can contain HasHierarchy names with a space, we call this function to
      * replace the spaces with underscores.
     * Note however that we can't garantuee that the updated strings are
     * all unique after the replacement!
      */
    static string replaceSpaces(string);

    /** This object is the interface with the GLPK structures. */
    LPX* lp;

    /** Storing simplex configuration paramters. */
    glp_smcp parameters;

    /** Which buckets to use for the linearization of the problem. */
    Calendar *cal;

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
    void solveObjective(const char*);

};

}  // End namespace
