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

#define FREPPLE_CORE
#include "frepple/solver.h"
namespace frepple
{

DECLARE_EXPORT const MetaClass* SolverMRP::metadata;


void LibrarySolver::initialize()
{
  // Initialize only once
  static bool init = false;
  if (init)
  {
    logger << "Warning: Calling frepple::LibrarySolver::initialize() more "
    << "than once." << endl;
    return;
  }
  init = true;

  // Register all classes.
  if (SolverMRP::initialize())
    throw RuntimeException("Error registering solver_mrp Python type");
}


int SolverMRP::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass
    ("solver","solver_mrp",Object::createString<SolverMRP>,true);

  // Initialize the Python class
  FreppleClass<SolverMRP,Solver>::getType().addMethod("solve", solve, METH_VARARGS, "run the solver");
  FreppleClass<SolverMRP,Solver>::getType().addMethod("commit", commit, METH_NOARGS, "commit the plan changes");
  FreppleClass<SolverMRP,Solver>::getType().addMethod("undo", undo, METH_NOARGS, "undo the plan changes");
  return FreppleClass<SolverMRP,Solver>::initialize();
}


DECLARE_EXPORT bool SolverMRP::demand_comparison(const Demand* l1, const Demand* l2)
{
  if (l1->getPriority() != l2->getPriority())
    return l1->getPriority() < l2->getPriority();
  else if (l1->getDue() != l2->getDue())
    return l1->getDue() < l2->getDue();
  else
    return l1->getQuantity() < l2->getQuantity();
}


DECLARE_EXPORT void SolverMRP::SolverMRPdata::execute()
{
  // Check
  if (!demands || !getSolver())
    throw LogicException("Missing demands or solver.");

  // Message
  SolverMRP* Solver = getSolver();
  if (Solver->getLogLevel()>0)
    logger << "Start solving cluster " << cluster << " at " << Date::now() << endl;

  // Solve the planning problem
  short oldConstraints = Solver->getConstraints();
  try
  {
    // Sort the demands of this problem.
    // We use a stable sort to get reproducible results between platforms
    // and STL implementations.
    stable_sort(demands->begin(), demands->end(), demand_comparison);

    if (Solver->getPlanType() == 3) Solver->setConstraints(0);

    // Loop through the list of all demands in this planning problem
    pass = 1; // First pass
    for (deque<Demand*>::const_iterator i = demands->begin();
        i != demands->end(); ++i)
    {
      Command* topcommand = getLastCommand();
      // Plan the demand
      try
      {
        State* mystate = state;
        push();
        try {(*i)->solve(*Solver,this);}
        catch (...)
        {
          while (state > mystate) pop();
          throw;
        }
        while (state > mystate) pop();
      }
      catch (...)
      {
        // Error message
        logger << "Error: Caught an exception while solving demand '"
          << (*i)->getName() << "':" << endl;
        try {throw;}
        catch (bad_exception&) {logger << "  bad exception" << endl;}
        catch (exception& e) {logger << "  " << e.what() << endl;}
        catch (...) {logger << "  Unknown type" << endl;}

        // Cleaning up
        undo(topcommand);
      }
    }

    // Second plan round for the unconstrained plan that searches alternates: 
    // plan the demand that can't be met on time in an incremental layer.
    if (Solver->getPlanType() == 2 && Solver->getConstraints())
    {
      // Switch off all constraints
      pass = 2; // Second pass
      Solver->setConstraints(0);

      // Loop over all demands
      for (deque<Demand*>::const_iterator i = demands->begin();
          i != demands->end(); ++i)
      {
        // Check whether the demand is already planned in full
        if ((*i)->getPlannedQuantity() > (*i)->getQuantity() - ROUNDING_ERROR) 
          continue;
        Command* topcommand = getLastCommand();
        // Plan the demand
        try
        {
          State* mystate = state;
          push();
          try {(*i)->solve(*Solver,this);}
          catch (...)
          {
            while (state > mystate) pop();
            throw;
          }
          while (state > mystate) pop();
        }
        catch (...)
        {
          // Error message
          logger << "Error: Caught an exception while solving demand '"
            << (*i)->getName() << "':" << endl;
          try {throw;}
          catch (bad_exception&) {logger << "  bad exception" << endl;}
          catch (exception& e) {logger << "  " << e.what() << endl;}
          catch (...) {logger << "  Unknown type" << endl;}

          // Cleaning up
          undo(topcommand);
        }
      }
    }

    // Clean the list of demands of this cluster
    demands->clear();
  }
  catch (...)
  {
    // We come in this exception handling code only if there is a problem with
    // with this cluster that goes beyond problems with single orders.
    // If the problem is with single orders, the exception handling code above
    // will do a proper rollback.

    // Error message
    logger << "Error: Caught an exception while solving cluster "
    << cluster << ":" << endl;
    try {throw;}
    catch (bad_exception&){logger << "  bad exception" << endl;}
    catch (exception& e) {logger << "  " << e.what() << endl;}
    catch (...) {logger << "  Unknown type" << endl;}

    // Clean up the operationplans of this cluster
    for (Operation::iterator f=Operation::begin(); f!=Operation::end(); ++f)
      if (f->getCluster() == cluster)
        f->deleteOperationPlans();

    // Clean the list of demands of this cluster
    demands->clear();
  }
      
  // Restore the old constraints
  Solver->setConstraints(oldConstraints);

  // Message
  if (Solver->getLogLevel()>0)
    logger << "End solving cluster " << cluster << " at " << Date::now() << endl;
}


DECLARE_EXPORT void SolverMRP::solve(void *v)
{
  // Categorize all demands in their cluster
  for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
    demands_per_cluster[i->getCluster()].push_back(&*i);

  // Delete of operationplans of the affected clusters
  // This deletion is not multi-threaded... But on the other hand we need to
  // loop through the operations only once (rather than as many times as there
  // are clusters)
  // A multi-threaded alternative would be to hash the operations here, and
  // then delete in each thread.
  if (getLogLevel()>0) logger << "Deleting previous plan" << endl;
  for (Operation::iterator e=Operation::begin(); e!=Operation::end(); ++e)
    // The next if-condition is actually redundant if we plan everything
    if (demands_per_cluster.find(e->getCluster())!=demands_per_cluster.end())
      e->deleteOperationPlans();

  // Count how many clusters we have to plan
  int cl = demands_per_cluster.size();
  if (cl<1) return;

  // Create the command list to control the execution
  CommandList threads;

  // Solve in parallel threads.
  // When not solving in silent and autocommit mode, we only use a single
  // solver thread.
  if (getLogLevel()>0 || !getAutocommit())
    threads.setMaxParallel(1);
  else
    threads.setMaxParallel( cl > getMaxParallel() ? getMaxParallel() : cl);

  // Make sure a problem in a single cluster doesn't spoil it all
  threads.setAbortOnError(false);
  for (classified_demand::iterator j = demands_per_cluster.begin();
      j != demands_per_cluster.end(); ++j)
    threads.add(new SolverMRPdata(this, j->first, &(j->second)));

  // Run the planning command threads and wait for them to exit
  threads.execute();

  // Check the resource setups that were broken yyy xxx todo needs to be removed
  for (Resource::iterator gres = Resource::begin(); gres != Resource::end(); ++gres)
  {
    if (gres->getSetupMatrix()) gres->updateSetups();
  }
}


DECLARE_EXPORT void SolverMRP::writeElement(XMLOutput *o, const Keyword& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);
    return;
  }

  // Write the complete object
  if (m != NOHEADER) o->BeginObject
    (tag, Tags::tag_name, getName(), Tags::tag_type, getType().type);

  // Write the fields
  if (constrts) o->writeElement(Tags::tag_constraints, constrts);
  if (plantype != 1) o->writeElement(Tags::tag_plantype, plantype);
  if (maxparallel) o->writeElement(Tags::tag_maxparallel, maxparallel);
  if (!autocommit) o->writeElement(Tags::tag_autocommit, autocommit);
  if (userexit_flow) 
    o->writeElement(Tags::tag_userexit_flow, static_cast<string>(userexit_flow));
  if (userexit_demand) 
    o->writeElement(Tags::tag_userexit_demand, static_cast<string>(userexit_demand));
  if (userexit_buffer) 
    o->writeElement(Tags::tag_userexit_buffer, static_cast<string>(userexit_buffer));
  if (userexit_resource) 
    o->writeElement(Tags::tag_userexit_resource, static_cast<string>(userexit_resource));
  if (userexit_operation) 
    o->writeElement(Tags::tag_userexit_operation, static_cast<string>(userexit_operation));

  // Write the parent class
  Solver::writeElement(o, tag, NOHEADER);
}


DECLARE_EXPORT void SolverMRP::endElement(XMLInput& pIn, const Attribute& pAttr, const DataElement& pElement)
{
  if (pAttr.isA(Tags::tag_constraints))
    setConstraints(pElement.getInt());
  else if (pAttr.isA(Tags::tag_maxparallel))
    setMaxParallel(pElement.getInt());
  else if (pAttr.isA(Tags::tag_autocommit))
    setAutocommit(pElement.getBool());
  else if (pAttr.isA(Tags::tag_userexit_flow))
    setUserExitFlow(pElement.getString());
  else if (pAttr.isA(Tags::tag_userexit_demand))
    setUserExitDemand(pElement.getString());
  else if (pAttr.isA(Tags::tag_userexit_buffer))
    setUserExitBuffer(pElement.getString());
  else if (pAttr.isA(Tags::tag_userexit_resource))
    setUserExitResource(pElement.getString());
  else if (pAttr.isA(Tags::tag_userexit_operation))
    setUserExitOperation(pElement.getString());
  else if (pAttr.isA(Tags::tag_plantype))
    setPlanType(pElement.getInt());
  else
    Solver::endElement(pIn, pAttr, pElement);
}


DECLARE_EXPORT PyObject* SolverMRP::getattro(const Attribute& attr)
{
  if (attr.isA(Tags::tag_constraints))
    return PythonObject(getConstraints());
  if (attr.isA(Tags::tag_maxparallel))
    return PythonObject(getMaxParallel());
  if (attr.isA(Tags::tag_autocommit))
    return PythonObject(getAutocommit());
  if (attr.isA(Tags::tag_userexit_flow))
    return getUserExitFlow();
  if (attr.isA(Tags::tag_userexit_demand))
    return getUserExitDemand();
  if (attr.isA(Tags::tag_userexit_buffer))
    return getUserExitBuffer();
  if (attr.isA(Tags::tag_userexit_resource))
    return getUserExitResource();
  if (attr.isA(Tags::tag_userexit_operation))
    return getUserExitOperation();
  if (attr.isA(Tags::tag_plantype))
    return PythonObject(getPlanType());
  return Solver::getattro(attr);
}


DECLARE_EXPORT int SolverMRP::setattro(const Attribute& attr, const PythonObject& field)
{
  if (attr.isA(Tags::tag_constraints))
    setConstraints(field.getInt());
  else if (attr.isA(Tags::tag_maxparallel))
    setMaxParallel(field.getInt());
  else if (attr.isA(Tags::tag_autocommit))
    setAutocommit(field.getBool());
  else if (attr.isA(Tags::tag_userexit_flow))
    setUserExitFlow(field);
  else if (attr.isA(Tags::tag_userexit_demand))
    setUserExitDemand(field);
  else if (attr.isA(Tags::tag_userexit_buffer))
    setUserExitBuffer(field);
  else if (attr.isA(Tags::tag_userexit_resource))
    setUserExitResource(field);
  else if (attr.isA(Tags::tag_userexit_operation))
    setUserExitOperation(field);
  else if (attr.isA(Tags::tag_plantype))
    setPlanType(field.getInt());
  else
    return Solver::setattro(attr, field);
  return 0;
}


DECLARE_EXPORT PyObject* SolverMRP::solve(PyObject *self, PyObject *args)
{
  // Parse the argument
  PyObject *dem = NULL;
  if (args && !PyArg_ParseTuple(args, "|O:solve", &dem)) return NULL;
  if (dem && !PyObject_TypeCheck(dem, Demand::metadata->pythonClass))
    throw DataException("solver argument must be a demand");

  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    SolverMRP* sol = static_cast<SolverMRP*>(self);
    if (!dem)
    {
      // Complete replan
      sol->setAutocommit(true);
      sol->solve();
    }
    else
    {
      // Incrementally plan a single demand
      sol->setAutocommit(false);
      sol->commands.sol = sol;
      static_cast<Demand*>(dem)->solve(*sol, &(sol->commands));
    }
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* SolverMRP::commit(PyObject *self, PyObject *args)
{
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    static_cast<SolverMRP*>(self)->commands.CommandList::execute();
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


DECLARE_EXPORT PyObject* SolverMRP::undo(PyObject *self, PyObject *args)
{
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    static_cast<SolverMRP*>(self)->commands.undo();
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}

} // end namespace
