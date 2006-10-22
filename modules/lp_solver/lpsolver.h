/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/include/frepple/erp.h $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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
  * @brief A solver module based on linear programming algorithm.
  *
  * @todo missing doc of the LP solver
  *
  */
  
#include "frepple.h"
using namespace frepple;

extern "C" {
#include "glpk.h"
}

namespace module_lp_solver
{

/** This class is a prototype of an Linear Programming (LP) Solver for the
  * planning problem or a subset of it. It is based on the GLPK (Gnu
  * Linear Programming Kit) library.
  * The class provides only a prototype framework, and it is definately not
  * ready for full use in a production environment. It misses too much
  * functionality for this purpose (e.g. no on-hand netting, doesn't plan
  * demand late, single level supply chain, no lead times, etc).
  * Nevertheless, the current code is currently geared towards simple
  * alLocation Problems but could be extended relatively easy to solve
  * other subProblems. See the documentation for further details on the LP
  * formulation, potential uses, limitations, etc...
  */
class LPSolver : public Solver
{
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

    virtual const MetaData& getType() const {return metadata;}
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
