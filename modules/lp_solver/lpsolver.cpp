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

  // Initialize the metadata.
  LPSolver::metadata.registerClass(
    "solver",
    "solver_lp",
    Object::createString<LPSolver>);

  // Return the name of the module
  return name;
}


void LPSolver::solveObjective(const char* colname)
{
  // Set the objective coefficient
  int col = glp_find_col(lp, colname);
  if (!col) throw LogicException("Solving for unknown column '" + string(colname) + "'");
  lpx_set_obj_coef(lp, col, 1.0);

  // Solve
  int result = glp_simplex(lp, &parameters);

  // Echo the result
  double val = lpx_get_obj_val(lp);
  if (getLogLevel()>0) 
  {
    logger << " Objective " << colname << ": " << val;
    if (result)
      logger << "     Error " << result << endl;
    else
      logger << "     OK" << endl;
  }

  // Freeze the column bounds
  lpx_set_col_bnds(lp, col, LPX_DB, 
    val>=ROUNDING_ERROR ? val-ROUNDING_ERROR : 0.0, 
    val>=-ROUNDING_ERROR ? val+ROUNDING_ERROR : 0.0);

  // Remove from the objective 
  lpx_set_obj_coef(lp, col, 0.0);
}


void LPSolver::solve(void *v)
{
  //
  // PART I: Problem initialisation
  //
  if (getLogLevel()>0)
    logger << "Start solver initialisation at " << Date::now() << endl;

  // Capture all terminal output of the solver
  glp_term_hook(solveroutputredirect,NULL);

  // Configure verbosity of the output
  glp_init_smcp(&parameters);
  if (getLogLevel() == 0)
    parameters.msg_lev = GLP_MSG_OFF;
  else if (getLogLevel() == 1)
    parameters.msg_lev = GLP_MSG_ERR;
  else if (getLogLevel() == 2)
    parameters.msg_lev = GLP_MSG_ON;
  else
    parameters.msg_lev = GLP_MSG_ALL;

  // Read the problem from a file in the GNU MathProg language.
  // The first argument is a model file.
  // The second argument is a data file: it is exported earlier, typically using 
  // frePPLe's python API.
  lp = lpx_read_model("lpsolver.mod", "lpsolver.dat", NULL);
  if (lp == NULL)
    throw RuntimeException("Cannot read mps file `%s'\n");

  // Scale the problem data
  lpx_scale_prob(lp);

  // Enable pre-solving (for the first simplex run)
  parameters.presolve = 1;

  // Minimize the goal
  glp_set_obj_dir(lp, GLP_MIN);

  // Create an index for quick searching on names
  glp_create_index(lp);

  if (getLogLevel()>0)
    logger << "Finished solver initialisation at " << Date::now() << endl;

  //
  // PART II: solving...
  // We solve with a sequence of hierarchical goals: First the highest 
  // priority goal is solved for. After finding its optimal value, we set the 
  // value as a constraint and start for the next priority goal.
  //

  // Initial message
  if (getLogLevel()>0) logger << "Start solving at " << Date::now() << endl;

  // Solve for a number of objectives
  solveObjective("goalshortage[1]");
  parameters.presolve = 0; // No more presolving required after 1 objective
  solveObjective("goallate[1]");
  solveObjective("goalshortage[2]");
  solveObjective("goallate[2]");
  solveObjective("goalshortage[3]");
  solveObjective("goallate[3]");
  solveObjective("goalearly[1]");
  solveObjective("goalearly[2]");
  solveObjective("goalearly[3]");

  // Final message
  if (getLogLevel()>0) logger << "Finished solving at " << Date::now() << endl;

  //
  // PART III: cleanup the solver
  //
  if (getLogLevel()>0)
    logger << "Start solver finalisation at " << Date::now() << endl;
  lpx_write_mps(lp,"lpsolver.mps");
  lpx_print_sol(lp,"lpsolver.sol");
  lpx_delete_prob(lp);
  glp_term_hook(NULL,NULL);
  if (getLogLevel()>0)
    logger << "Finished solver finalisation at " << Date::now() << endl;
}


string LPSolver::replaceSpaces(string input)
{
  string x = input;
  for (string::iterator i = x.begin(); i != x.end(); ++i)
    if (*i == ' ') *i = '_';
  return x;
}


void LPSolver::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
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


void LPSolver::beginElement(XMLInput& pIn, const Attribute& pAttr)
{
  if (pAttr.isA (Tags::tag_calendar))
    pIn.readto(Calendar::reader(Calendar::metadata,pIn.getAttributes()));
}


void LPSolver::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_calendar))
  {
    Calendar * c = dynamic_cast<Calendar*>(pIn.getPreviousObject());
    if (c) setCalendar(c);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
    // The standard fields of a solver...
    Solver::endElement(pIn, pAttr, pElement);
}

}  // End namespace
