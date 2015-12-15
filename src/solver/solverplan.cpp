/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/solver.h"
namespace frepple
{

DECLARE_EXPORT const MetaClass* SolverMRP::metadata;
const Keyword SolverMRP::tag_iterationthreshold("iterationthreshold");
const Keyword SolverMRP::tag_iterationaccuracy("iterationaccuracy");
const Keyword SolverMRP::tag_lazydelay("lazydelay");
const Keyword SolverMRP::tag_allowsplits("allowsplits");
const Keyword SolverMRP::tag_rotateresources("rotateresources");
const Keyword SolverMRP::tag_planSafetyStockFirst("plansafetystockfirst");
const Keyword SolverMRP::tag_iterationmax("iterationmax");


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
  int nok = 0;
  nok += SolverMRP::initialize();
  nok += OperatorDelete::initialize();
  if (nok) throw RuntimeException("Error registering new Python types");
}


int SolverMRP::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<SolverMRP>(
    "solver", "solver_mrp", Object::create<SolverMRP>, true
    );
  registerFields<SolverMRP>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleClass<SolverMRP, Solver>::getPythonType();
  x.setName("solver_mrp");
  x.setDoc("frePPLe solver_mrp");
  x.supportgetattro();
  x.supportsetattro();
  x.supportcreate(create);
  x.addMethod("solve", solve, METH_NOARGS, "run the solver");
  x.addMethod("commit", commit, METH_NOARGS, "commit the plan changes");
  x.addMethod("rollback", rollback, METH_NOARGS, "rollback the plan changes");
  const_cast<MetaClass*>(metadata)->pythonClass = x.type_object();
  return x.typeReady();
}


PyObject* SolverMRP::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Create the solver
    SolverMRP *s = new SolverMRP();

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    while (PyDict_Next(kwds, &pos, &key, &value))
    {
      PythonData field(value);
      PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
      DataKeyword attr(PyBytes_AsString(key_utf8));
      Py_DECREF(key_utf8);
      const MetaFieldBase* fmeta = SolverMRP::metadata->findField(attr.getHash());
      if (!fmeta)
        fmeta = Solver::metadata->findField(attr.getHash());
      if (fmeta)
        // Update the attribute
        fmeta->setField(s, field);
      else
        s->setProperty(attr.getName(), value);
    };

    // Return the object. The reference count doesn't need to be increased
    // as we do with other objects, because we want this object to be available
    // for the garbage collector of Python.
    return static_cast<PyObject*>(s);
  }
  catch (...)
  {
    PythonType::evalException();
    return NULL;
  }
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


DECLARE_EXPORT void SolverMRP::SolverMRPdata::commit()
{
  // Check
  SolverMRP* solver = getSolver();
  if (!demands || !solver)
    throw LogicException("Missing demands or solver.");

  // Message
  if (solver->getLogLevel()>0)
    logger << "Start solving cluster " << cluster << " at " << Date::now() << endl;

  // Solve the planning problem
  try
  {
    // TODO Propagate & solve initial shortages and overloads

    // Sort the demands of this problem.
    // We use a stable sort to get reproducible results between platforms
    // and STL implementations.
    stable_sort(demands->begin(), demands->end(), demand_comparison);

    // Solve for safety stock in buffers.
    if (solver->getPlanSafetyStockFirst())
    {
      constrainedPlanning = (solver->getPlanType() == 1);
      solveSafetyStock(solver);
    }

    // Loop through the list of all demands in this planning problem
    safety_stock_planning = false;
    constrainedPlanning = (solver->getPlanType() == 1);
    for (deque<Demand*>::const_iterator i = demands->begin();
        i != demands->end(); ++i)
    {
      iteration_count = 0;
      try
      {
        // Plan the demand
        (*i)->solve(*solver, this);
      }
      catch (...)
      {
        // Error message
        logger << "Error: Caught an exception while solving demand '"
            << (*i)->getName() << "':" << endl;
        try {throw;}
        catch (const bad_exception&) {logger << "  bad exception" << endl;}
        catch (const exception& e) {logger << "  " << e.what() << endl;}
        catch (...) {logger << "  Unknown type" << endl;}
      }
    }

    // Clean the list of demands of this cluster
    demands->clear();

    // Solve for safety stock in buffers.
    if (!solver->getPlanSafetyStockFirst()) solveSafetyStock(solver);
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
    catch (const bad_exception&) {logger << "  bad exception" << endl;}
    catch (const exception& e) {logger << "  " << e.what() << endl;}
    catch (...) {logger << "  Unknown type" << endl;}

    // Clean up the operationplans of this cluster
    for (Operation::iterator f=Operation::begin(); f!=Operation::end(); ++f)
      if (f->getCluster() == cluster)
        f->deleteOperationPlans();

    // Clean the list of demands of this cluster
    demands->clear();
  }

  // Message
  if (solver->getLogLevel()>0)
    logger << "End solving cluster " << cluster << " at " << Date::now() << endl;
}


void SolverMRP::SolverMRPdata::solveSafetyStock(SolverMRP* solver)
{
  OperatorDelete cleanup(this);
  safety_stock_planning = true;
  if (getLogLevel()>0) logger << "Start safety stock replenishment pass   " << solver->getConstraints() << endl;
  vector< list<Buffer*> > bufs(HasLevel::getNumberOfLevels() + 1);
  for (Buffer::iterator buf = Buffer::begin(); buf != Buffer::end(); ++buf)
    if (buf->getCluster() == cluster
      && ( buf->getMinimum() || buf->getMinimumCalendar()
        || buf->getType() == *BufferProcure::metadata )
      )
      bufs[(buf->getLevel()>=0) ? buf->getLevel() : 0].push_back(&*buf);
  for (vector< list<Buffer*> >::iterator b_list = bufs.begin(); b_list != bufs.end(); ++b_list)
    for (list<Buffer*>::iterator b = b_list->begin(); b != b_list->end(); ++b)
      try
      {
        state->curBuffer = NULL;
        // A quantity of -1 is a flag for the buffer solver to solve safety stock.
        state->q_qty = -1.0;
        state->q_date = Date::infinitePast;
        state->a_cost = 0.0;
        state->a_penalty = 0.0;
        planningDemand = NULL;
        state->curDemand = NULL;
        state->curOwnerOpplan = NULL;
        // Call the buffer solver
        iteration_count = 0;
        (*b)->solve(*solver, this);
        // Check for excess
        if ((*b)->getType() != *BufferProcure::metadata)
          (*b)->solve(cleanup, this);
        CommandManager::commit();
      }
      catch(...)
      {
        CommandManager::rollback();
      }
  if (getLogLevel()>0) logger << "Finished safety stock replenishment pass" << endl;
  safety_stock_planning = false;
}


DECLARE_EXPORT void SolverMRP::update_user_exits()
{
  setUserExitBuffer(getPyObjectProperty(Tags::userexit_buffer.getName()));
  setUserExitDemand(getPyObjectProperty(Tags::userexit_demand.getName()));
  setUserExitFlow(getPyObjectProperty(Tags::userexit_flow.getName()));
  setUserExitOperation(getPyObjectProperty(Tags::userexit_operation.getName()));
  setUserExitResource(getPyObjectProperty(Tags::userexit_resource.getName()));
}


DECLARE_EXPORT void SolverMRP::solve(void *v)
{
  // Configure user exits
  update_user_exits();

  // Count how many clusters we have to plan
  int cl = HasLevel::getNumberOfClusters() + 1;

  // Categorize all demands in their cluster
  demands_per_cluster.resize(cl);
  for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
    demands_per_cluster[i->getCluster()].push_back(&*i);

  // Delete of operationplans of the affected clusters
  // This deletion is not multi-threaded... But on the other hand we need to
  // loop through the operations only once (rather than as many times as there
  // are clusters)
  if (getErasePreviousFirst())
  {
    if (getLogLevel()>0) logger << "Deleting previous plan" << endl;
    for (Operation::iterator e=Operation::begin(); e!=Operation::end(); ++e)
      e->deleteOperationPlans();
  }

  // Solve in parallel threads.
  // When not solving in silent and autocommit mode, we only use a single
  // solver thread.
  // Otherwise we use as many worker threads as processor cores.
  ThreadGroup threads;
  if (getLogLevel()>0 || !getAutocommit())
    threads.setMaxParallel(1);

  // Register all clusters to be solved
  for (int j = 0; j < cl; ++j)
    threads.add(
      SolverMRPdata::runme,
      new SolverMRPdata(this, j, &(demands_per_cluster[j]))
      );

  // Run the planning command threads and wait for them to exit
  threads.execute();

  // @todo Check the resource setups that were broken - needs to be removed
  for (Resource::iterator gres = Resource::begin(); gres != Resource::end(); ++gres)
    if (gres->getSetupMatrix()) gres->updateSetups();
}


DECLARE_EXPORT PyObject* SolverMRP::solve(PyObject *self, PyObject *args)
{
  // Parse the argument
  PyObject *dem = NULL;
  if (args && !PyArg_ParseTuple(args, "|O:solve", &dem)) return NULL;
  if (dem && !PyObject_TypeCheck(dem, Demand::metadata->pythonClass))
  {
    PyErr_SetString(PythonDataException, "solve(d) argument must be a demand");
    return NULL;
  }

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
      sol->update_user_exits();
      static_cast<Demand*>(dem)->solve(*sol, &(sol->getCommands()));
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
    SolverMRP * me = static_cast<SolverMRP*>(self);
    me->scanExcess(&(me->commands));
    me->commands.CommandManager::commit();
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


DECLARE_EXPORT PyObject* SolverMRP::rollback(PyObject *self, PyObject *args)
{
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    static_cast<SolverMRP*>(self)->commands.rollback();
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
