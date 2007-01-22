/***************************************************************************
  file : $URL$
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

/** @file lpsolver.h
  * @brief Header file for the module lp_solver.
  *
  * @namespace module_lp_solver
  * @brief A solver module based on a linear programming algorithm.
  *
  * This module uses a linear programming representation to solve simple 
  * material allocation problems: Given a limited supply of components
  * it establishes the most profitable mix of end items that can be 
  * assembled from the components.
  *
  * The representation doesn't account for a lot of the details. In its 
  * current form the solver accounts only for the simplest of cases. 
  * Additional development work can enhance the solver.
  * A short list of the restrictions:
  *  - no intermediate materials and their WIP or inventory
  *  - no leadtimes taken into account
  *  - no support for alternate and routing operations
  *  - no capacity constraints
  *  - demand can only be planned short, not late
  *
  * The module uses the "Gnu Linear Programming Kit" library (aka GLPK) to
  * solve the LP model.
  *
  * The XML schema extension enabled by this module is (see mod_lpsolver.xsd):
  * <PRE>
  * <xsd:complexType name="SOLVER_LP">
  *   <xsd:complexContent>
  *     <xsd:extension base="SOLVER">
  *       <xsd:choice minOccurs="0" maxOccurs="unbounded">
  *         <xsd:element name="VERBOSE" type="xsd:boolean" />
  *         <xsd:element name="CALENDAR" type="CALENDAR" />
  *       </xsd:choice>
  *     </xsd:extension>
  *   </xsd:complexContent>
  * </xsd:complexType>
  * </PRE>
  */
  
#include "frepple.h"
using namespace frepple;

extern "C" {
#include "glpk.h"
}

namespace module_lp_solver
{

/** This class is a prototype of an Linear Programming (LP) Solver for the
  * planning problem or a subset of it.<br>
  * The class provides only a concept / prototype, and it is definately not
  * ready for full use in a production environment. It misses too much
  * functionality for this purpose.
  */
class LPSolver : public Solver
{
  TYPEDEF(LPSolver);
  public:
    /** This method creates a new column in the model for every demand. It's
      * value represents the planned quantity of that demand.
      * @exception DataException Generated when no calendar has been specified.
      */
    void solve(void* = NULL);
    void solve(Demand*, void* = NULL);
    void solve(Buffer*, void* = NULL);

    Calendar * getCalendar() const {return cal;}
    void setCalendar(Calendar* c) {cal = c;}

    void beginElement(XMLInput& pIn, XMLElement& pElement);
    virtual void writeElement(XMLOutput*, const XMLtag&, mode=DEFAULT) const;
    void endElement(XMLInput& pIn, XMLElement& pElement);

    LPSolver(const string n) : Solver(n), cal(NULL), rows(0), columns(0) {};
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

    /** Which buckets to use for the linearization of the Problem. */
    Calendar *cal;

    /** A counter for the number of rows in our LP matrix. */
    int rows;

    /** A counter for the number of columns in our LP matrix. */
    int columns;

    typedef map< int, int, less<int> > priolist;
    /** Here we store a conversion table between a certain value of the demand
      * priority and a row in the LP matrix. The row represents the satisfied
      * demand of this demand priority.
      */
    priolist demandprio2row;

    typedef map<const Buffer*, int, less<const Buffer*> > Bufferlist;
    /** Here we store a conversion table between a Buffer pointer and a row
      * index in the LP constraint matrix. Each Buffer has N rows in the matrix,
      * where N is the number of buckets in the Calendar.
      * The index stored in this table is the lowest row number -1.
      */
    Bufferlist Buffer2row;
};

}  // End namespace
