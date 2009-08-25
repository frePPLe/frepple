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

#include "lpsolver.h"

namespace module_lp_solver
{

const MetaClass *LPSolver::metadata;

const Keyword tag_datafile("datafile");
const Keyword tag_modelfile("modelfile");
const Keyword tag_solutionfile("solutionfile");
const Keyword tag_objective("objective");


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

  try 
  {
    // Register the Python extension
    PyThreadState *myThreadState = PyGILState_GetThisThreadState();
    if (!Py_IsInitialized() || !myThreadState)
      throw RuntimeException("Python isn't initialized correctly");
    try
    {
      // Get the global lock.
      PyEval_RestoreThread(myThreadState);
      // Register new Python data types
      if (LPSolver::initialize())
        throw RuntimeException("Error registering Python solver_lp extension");
    }
    // Release the global lock when leaving the function
    catch (...)
    {
      PyEval_ReleaseLock();
      throw;  // Rethrow the exception
    }
    PyEval_ReleaseLock();
  }
  catch (exception &e) 
  {
    // Avoid throwing errors during the initialization!
    logger << "Error: " << e.what() << endl;
  }
  catch (...)
  {
    logger << "Error: unknown exception" << endl;
  }

  // Return the name of the module
  return name;
}


int LPSolver::initialize()
{
  // Initialize the metadata.
  metadata = new MetaClass("solver", "solver_lp",
    Object::createString<LPSolver>);

  // Initialize the Python class
  return FreppleClass<LPSolver,Solver>::initialize();
}


void LPSolver::solveObjective(const string& colname)
{
  // Set the objective coefficient
  if (colname.empty()) throw DataException("Empty objective name");
  int col = glp_find_col(lp, colname.c_str());
  if (!col) 
    throw DataException("Unknown objective name '" + string(colname) + "'");
  lpx_set_obj_coef(lp, col, 1.0);

  // Message
  if (getLogLevel()>0) 
    logger << "Solving for " << colname << "..." << endl;

  // Solve
  int result = glp_simplex(lp, &parameters);

  // Echo the result
  double val = lpx_get_obj_val(lp);
  if (getLogLevel()>0) 
  {
    if (result)
      logger << "  Error " << result << endl;
    else
      logger << "  Optimum " << val <<  " found at " << Date::now() << endl;
  }

  // Freeze the column bounds
  lpx_set_col_bnds(lp, col, LPX_DB, 
    val>=ROUNDING_ERROR ? val-ROUNDING_ERROR : 0.0, 
    val>=-ROUNDING_ERROR ? val+ROUNDING_ERROR : 0.0);

  // Remove from the objective 
  lpx_set_obj_coef(lp, col, 0.0);

  // No more presolving required after 1 objective
  if (parameters.presolve) parameters.presolve = 0; 
}


void LPSolver::solve(void *v)
{
  if (getLogLevel()>0)
    logger << "Start running the solver at " << Date::now() << endl;

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
  if (modelfilename.empty())
    throw DataException("No model file specified");
  if (datafilename.empty())
    lp = lpx_read_model(modelfilename.c_str(), NULL, NULL);
  else
    lp = lpx_read_model(modelfilename.c_str(), datafilename.c_str(), NULL);
  if (lp == NULL) 
    throw RuntimeException("Cannot read model file '" + modelfilename + "'");

  // Optinally, write the model in MPS format. This format can be read 
  // directly by other Linear Programming packages.
  if (getLogLevel()>2)
  { 
    string c = modelfilename + ".mps";
    lpx_write_mps(lp,c.c_str());
  }

  // Scale the problem data
  lpx_scale_prob(lp);

  // Enable pre-solving
  // After the first objective, the presolving is switched off.
  parameters.presolve = 1;

  // Minimize the goal
  glp_set_obj_dir(lp, minimum ? GLP_MIN : GLP_MAX);

  // Create an index for quick searching on names
  glp_create_index(lp);

  if (getLogLevel()>0)
    logger << "Finished solver initialisation at " << Date::now() << endl;

  // Solving...
  if (objectives.empty())
    throw DataException("No solver objectives are specified");
  for (list<string>::const_iterator i = objectives.begin(); 
    i != objectives.end(); ++i)
      solveObjective(*i);

  // Write solution 
  if (!solutionfilename.empty())
    lpx_print_sol(lp,solutionfilename.c_str());
  
  // Cleanup
  lpx_delete_prob(lp);
  glp_term_hook(NULL,NULL);

  if (getLogLevel()>0)
    logger << "Finished running the solver at " << Date::now() << endl;
}


string LPSolver::replaceSpaces(const string& input)
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
  if (getMinimum())
    o->writeElement(Tags::tag_minimum, true);
  else
    o->writeElement(Tags::tag_maximum, true);
  o->writeElement(tag_modelfile, getModelFile());
  o->writeElement(tag_datafile, getDataFile());
  o->writeElement(tag_solutionfile, getSolutionFile());
  for (list<string>::const_iterator i = objectives.begin(); 
    i != objectives.end(); ++i)
      o->writeElement(tag_objective, *i);
  Solver::writeElement(o, tag, NOHEADER);
}


void LPSolver::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_minimum))
    setMinimum(pElement.getBool());
  else if (pAttr.isA(Tags::tag_maximum))
    setMinimum(!pElement.getBool());
  else if (pAttr.isA(tag_datafile))
    setDataFile(pElement.getString());
  else if (pAttr.isA(tag_modelfile))
    setModelFile(pElement.getString());
  else if (pAttr.isA(tag_solutionfile))
    setSolutionFile(pElement.getString());
  else if (pAttr.isA(tag_objective))
    addObjective(pElement.getString());
  else
    // The standard fields of a solver...
    Solver::endElement(pIn, pAttr, pElement);
}


PyObject* LPSolver::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_minimum))
    return PythonObject(getMinimum());
  else if (attr.isA(Tags::tag_maximum))
    return PythonObject(!(getMinimum()));
  else if (attr.isA(tag_datafile))
    return PythonObject(getDataFile());
  else if (attr.isA(tag_modelfile))
    return PythonObject(getModelFile());
  else if (attr.isA(tag_solutionfile))
    return PythonObject(getSolutionFile());
  else if (attr.isA(tag_objective))
  {
	  // The list of objectives is returned as a list of strings
    PyObject* result = PyList_New(getObjectives().size());
    int count = 0;
    for (list<string>::const_iterator i = getObjectives().begin(); 
        i != getObjectives().end(); ++i)
      PyList_SetItem(result, count++, PythonObject(*i));
    return result;
  }
  return Solver::getattro(attr); 
}


int LPSolver::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_minimum))
    setMinimum(field.getBool());
  else if (attr.isA(Tags::tag_maximum))
	  setMinimum(!field.getBool());
  else if (attr.isA(tag_datafile))
	  setDataFile(field.getString());
  else if (attr.isA(tag_modelfile))
	  setModelFile(field.getString());
  else if (attr.isA(tag_solutionfile))
	  setSolutionFile(field.getString());
  else if (attr.isA(tag_objective))
  {
	  // The objective argument is a list of strings
    PyObject* seq = PySequence_Fast(static_cast<PyObject*>(field), "expected a list");
    if (!PyList_Check(seq))
    {
      PyErr_SetString(PythonDataException, "expected a list");
	    return -1; // Error
	  }
	  int len = PySequence_Size(static_cast<PyObject*>(field));
	  PythonObject item;
    for (int i = 0; i < len; i++) 
    {
	    item = PyList_GET_ITEM(seq, i);
	    addObjective(item.getString());
    }
  }
  else
    return Solver::setattro(attr, field);
  return 0; // OK
}

}  // End namespace
