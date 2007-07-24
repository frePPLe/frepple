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

#include "lpsolver.h"

namespace module_lp_solver
{

const MetaClass LPSolver::metadata;


MODULE_EXPORT const char* initialize(const CommandLoadLibrary::ParameterList& z)
{
  // Initialize only once
  static bool init = false;
  static const char* name = "lpsolver";
  if (init)
  {
    logger << "Warning: Initializing module lpsolver more than once." << endl;
    return name;
  }
  init = true;

  // Print the parameters
  /*
  for (CommandLoadLibrary::ParameterList::const_iterator
    j = z.begin(); j!= z.end(); ++j)
    logger << "Parameter " << j->first << " = " << j->second << endl;
  */

  // Initialize the metadata.
  LPSolver::metadata.registerClass(
    "SOLVER",
    "SOLVER_LP",
    Object::createString<LPSolver>);

  // Return the name of the module
  return name;
}


void LPSolver::solve(void *v)
{

  //
  // PART I: Problem initialisation
  //
  if (getVerbose())
    logger << "Start Solver initialisation at " << Date::now() << endl;

  // We really need a calendar the lp buckets!
  if (!cal) throw DataException("No calendar specified for LP Solver");

  // Initialisation
  lp = lpx_create_prob();
  string x = replaceSpaces(Plan::instance().getName());
  lpx_set_prob_name(lp, (char*) x.c_str());

  // Count the number of buckets
  unsigned int buckets = 0;
  for (Calendar::BucketIterator c=cal->beginBuckets(); c!=cal->endBuckets(); ++c)
    ++buckets;

  // Determine Problem SIZE!
  lpx_add_cols(lp, Demand::size()         // Col 1 ... Demands
      + buckets                  // Col Demands+1 ... Demands+Buckets
              );
  lpx_add_rows(lp, 1 +                    // Row 1: total inventory
      1 +                        // Row 2: total planned qty
      2 +                        // For each demand prio
      buckets
              );

  // Build predefined rows
  lpx_set_row_name(lp, ++rows, "Inventory");
  lpx_set_row_name(lp, ++rows, "Planned_Qty");

  // Build problem for the Buffers
  Buffer::find("RM3")->solve(*this,this);

  // Build problem for the demands
  for (Demand::iterator j = Demand::begin(); j != Demand::end(); ++j)
    j->solve(*this,this);

  if (getVerbose())
    logger << "Finished Solver initialisation at " << Date::now() << endl;

  //
  // PART II: solving...
  //

  // Initial message
  if (getVerbose()) logger << "Start solving at " << Date::now() << endl;

  // Objective: maximize the planned demand of each priority
  for (priolist::iterator i = demandprio2row.begin();
      i != demandprio2row.end(); ++i)
  {
    if (getVerbose())
      logger << "Start maximizing supply for demand priority " << i->first
      << " at " << Date::now() << endl;
    // Set the right row as the objective
    lpx_set_obj_coef(lp, i->second, 1.0);
    lpx_set_obj_dir(lp, LPX_MAX);
    // Solve
    lpx_simplex(lp);
    // Results...
    if (getVerbose())
      logger << " Satisfied " << lpx_get_obj_val(lp) << " units" << endl;
    // Fix the optimal solution for the next objective layers
    lpx_set_row_bnds(lp, i->second, LPX_LO, lpx_get_obj_val(lp), 0.0);
    // Remove from the objective
    lpx_set_obj_coef(lp, i->second, 0.0);
  }

  // Additional objective: minimize the inventory
  lpx_set_obj_coef(lp, 1, 1.0);
  lpx_set_obj_dir(lp, LPX_MIN);
  lpx_simplex(lp);
  lpx_write_mps(lp,"lp_solver.mps");
  lpx_print_sol(lp,"lp_solver.sol");

  // Final message
  if (getVerbose()) logger << "Finished solving at " << Date::now() << endl;

  //
  // PART III: cleanup the solver
  //

  if (getVerbose())
    logger << "Start solver finalisation at " << Date::now() << endl;
  lpx_delete_prob(lp);
  if (getVerbose())
    logger << "Finished solver finalisation at " << Date::now() << endl;

}


void LPSolver::solve(const Demand* l, void* v)
{
  LPSolver* Sol = (LPSolver*)v;

  // Set the name of the column equal to the demand name
  string x = replaceSpaces(l->getName());
  lpx_set_col_name(Sol->lp, ++(Sol->columns), const_cast<char*>(x.c_str()));

  // The planned quantity lies between 0 and the demand's requested quantity
  lpx_set_col_bnds(Sol->lp, Sol->columns, LPX_DB, 0.0, l->getQuantity());

  // Create a row for each priority level of demands
  if ( Sol->demandprio2row.find(l->getPriority())
      == Sol->demandprio2row.end())
  {
    ostringstream x;
    x << "Planned_Qty_" << l->getPriority();
    Sol->demandprio2row[l->getPriority()] = ++(Sol->rows);
    lpx_set_row_name(Sol->lp, Sol->rows, const_cast<char*>(x.str().c_str()));
  }

  // Insert in the constraint column
  int ndx[4];
  double val[4];
  ndx[1] = 2;
  val[1] = 1.0;
  ndx[2] = Sol->demandprio2row[l->getPriority()];
  val[2] = 1.0;
  ndx[3] = Sol->Buffer2row[Buffer::find("RM3")]
      + Sol->cal->findBucketIndex(l->getDue());
  val[3] = 1.0;
  lpx_set_mat_col(Sol->lp, Sol->columns, 3, ndx, val);

}


void LPSolver::solve(const Buffer* buf, void* v)
{
  LPSolver* Sol = (LPSolver*)v;
  bool first = true;

  // Insert the Buffer in a list for references
  Sol->Buffer2row[buf] = Sol->rows;

  Buffer::flowplanlist::const_iterator f = buf->getFlowPlans().begin();
  for (Calendar::BucketIterator b = Sol->cal->beginBuckets();
      b != Sol->cal->endBuckets(); ++b)
  {

    // Find the supply in this Bucket
    double supply(0.0);
    for (; f!=buf->getFlowPlans().end() && f->getDate()<b->getEnd(); ++f)
      if (f->getQuantity() > 0.0f) supply += f->getQuantity();

    // Set the name of the column equal to the Buffer & Bucket
    string x = replaceSpaces(string(buf->getName()) + "_" + b->getName());
    lpx_set_col_name(Sol->lp, ++(Sol->columns), const_cast<char*>(x.c_str()));
    lpx_set_row_name(Sol->lp, ++(Sol->rows), const_cast<char*>(x.c_str()));

    // Set the lower bound for the inventory level column
    lpx_set_col_bnds(Sol->lp, Sol->columns, LPX_LO, 0.0, 0.0);

    // Fix the supply row
    lpx_set_row_bnds(Sol->lp, Sol->rows, LPX_FX, supply, supply);

    // Insert in the constraint row
    int ndx[3];
    double val[3];
    if (!first)
    {
      ndx[1] = Sol->columns -1;
      val[1] = -1.0;
      lpx_set_mat_row(Sol->lp, Sol->rows, 1, ndx, val);
    }
    ndx[1] = Sol->rows;
    val[1] = 1.0;
    ndx[2] = 1;
    val[2] = 1.0;
    lpx_set_mat_col(Sol->lp, Sol->columns, 2, ndx, val);
    first = false;

  }
}


string LPSolver::replaceSpaces(string input)
{
  string x = input;
  for (string::iterator i = x.begin(); i != x.end(); ++i)
    if (*i == ' ') *i = '_';
  return x;
}


void LPSolver::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Fields
  o->writeElement(Tags::tag_calendar, cal);
  Solver::writeElement(o, tag, NOHEADER);
}


void LPSolver::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_calendar))
    pIn.readto(Calendar::reader(Calendar::metadata,pIn));
}


void LPSolver::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_calendar))
  {
    Calendar * c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
    if (c) setCalendar(c);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
    // The standard fields of a solver...
    Solver::endElement(pIn, pElement);
}

}  // End namespace
