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

const MetaClass* SolverCreate::metadata;
const Keyword SolverCreate::tag_iterationthreshold("iterationthreshold");
const Keyword SolverCreate::tag_iterationaccuracy("iterationaccuracy");
const Keyword SolverCreate::tag_lazydelay("lazydelay");
const Keyword SolverCreate::tag_administrativeleadtime("administrativeleadtime");
const Keyword SolverCreate::tag_minimumdelay("minimumdelay");
const Keyword SolverCreate::tag_allowsplits("allowsplits");
const Keyword SolverCreate::tag_autofence("autofence");
const Keyword SolverCreate::tag_rotateresources("rotateresources");
const Keyword SolverCreate::tag_planSafetyStockFirst("plansafetystockfirst");
const Keyword SolverCreate::tag_iterationmax("iterationmax");


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
  nok += SolverCreate::initialize();
  nok += OperatorDelete::initialize();
  if (nok) throw RuntimeException("Error registering new Python types");
}


int SolverCreate::initialize()
{
  // Initialize the metadata
  metadata = MetaClass::registerClass<SolverCreate>(
    "solver", "solver_mrp", Object::create<SolverCreate>, true
    );
  registerFields<SolverCreate>(const_cast<MetaClass*>(metadata));

  // Initialize the Python class
  PythonType& x = FreppleClass<SolverCreate, Solver>::getPythonType();
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


PyObject* SolverCreate::create(PyTypeObject* pytype, PyObject* args, PyObject* kwds)
{
  try
  {
    // Create the solver
    SolverCreate *s = new SolverCreate();

    // Iterate over extra keywords, and set attributes.   @todo move this responsibility to the readers...
    if (kwds)
    {
      PyObject *key, *value;
      Py_ssize_t pos = 0;
      while (PyDict_Next(kwds, &pos, &key, &value))
      {
        PythonData field(value);
        PyObject* key_utf8 = PyUnicode_AsUTF8String(key);
        DataKeyword attr(PyBytes_AsString(key_utf8));
        Py_DECREF(key_utf8);
        const MetaFieldBase* fmeta = SolverCreate::metadata->findField(attr.getHash());
        if (!fmeta)
          fmeta = Solver::metadata->findField(attr.getHash());
        if (fmeta)
          // Update the attribute
          fmeta->setField(s, field);
        else
          s->setProperty(attr.getName(), value);
      };
    }

    // Return the object. The reference count doesn't need to be increased
    // as we do with other objects, because we want this object to be available
    // for the garbage collector of Python.
    return static_cast<PyObject*>(s);
  }
  catch (...)
  {
    PythonType::evalException();
    return nullptr;
  }
}


SolverCreate::SolverData::SolverData(SolverCreate* s, int c, deque<Demand*>* d)
  : sol(s), cluster(c), demands(d), constrainedPlanning(true),
  logConstraints(true), state(statestack), prevstate(statestack - 1)
{
  operator_delete = new OperatorDelete();
}


void SolverCreate::SolverData::setCommandManager(CommandManager* a)
{
  if (mgr == a)
    return;
  mgr = a;
  if (operator_delete)
    operator_delete->setCommandManager(a);
}


SolverCreate::SolverData::~SolverData()
{
  delete operator_delete;
};


bool SolverCreate::demand_comparison(const Demand* l1, const Demand* l2)
{
  if (l1->getPriority() != l2->getPriority())
    return l1->getPriority() < l2->getPriority();
  else if (l1->getDue() != l2->getDue())
    return l1->getDue() < l2->getDue();
  else
    return l1->getQuantity() < l2->getQuantity();
}


void SolverCreate::SolverData::push(double q, Date d, bool full)
{
  if (state >= statestack + MAXSTATES)
    throw RuntimeException("Maximum recursion depth exceeded");
  ++state;
  ++prevstate;
  state->q_qty = q;
  state->q_date = d;
  state->q_date_max = d;
  if (full)
  {
    state->q_loadplan = prevstate->q_loadplan;
    state->q_flowplan = prevstate->q_flowplan;
    state->q_operationplan = prevstate->q_operationplan;
    state->curOwnerOpplan = prevstate->curOwnerOpplan;
    state->curDemand = prevstate->curDemand;
    state->curBuffer = prevstate->curBuffer;
    state->q_qty_min = prevstate->q_qty_min;
  }
  else
  {
    state->q_loadplan = nullptr;
    state->q_flowplan = nullptr;
    state->q_operationplan = nullptr;
    state->curOwnerOpplan = nullptr;
    state->curDemand = nullptr;
    state->curBuffer = nullptr;
    state->q_qty_min = 1.0;
  }
  state->forceLate = false;
  state->a_cost = 0.0;
  state->a_penalty = 0.0;
  state->a_date = Date::infiniteFuture;
  state->a_qty = 0.0;
}


void SolverCreate::SolverData::pop(bool copy_answer)
{
  if (state < statestack)
    throw LogicException("State stack empty");
  if (copy_answer)
  {
    prevstate->a_qty = state->a_qty;
    prevstate->a_date = state->a_date;
    prevstate->a_penalty = state->a_penalty;
    prevstate->a_cost = state->a_cost;
  }
  --state;
  --prevstate;
}


void SolverCreate::SolverData::commit()
{
  // Check
  SolverCreate* solver = getSolver();
  if (!demands || !solver)
    throw LogicException("Missing demands or solver.");

  // Message
  if (solver->getLogLevel()>0)
    logger << "Start solving cluster " << cluster << endl;

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
        // Log the exception as the only reason for the demand not being planned
        (*i)->getConstraints().clear();
        // Error message
        logger << "Error: Caught an exception while solving demand '"
            << (*i)->getName() << "':" << endl;
        try {throw;}
        catch (const bad_exception&) 
        {
          (*i)->getConstraints().push(new ProblemInvalidData(
            (*i), "Error: bad exception", "demand",           
            (*i)->getDue(), (*i)->getDue(), (*i)->getQuantity(), false
          ));
          logger << "  bad exception" << endl;
        }
        catch (const exception& e) 
        {
          (*i)->getConstraints().push(new ProblemInvalidData(
            (*i), "Error: " + string(e.what()), "demand",
            (*i)->getDue(), (*i)->getDue(), (*i)->getQuantity(), false
          ));
          logger << "  " << e.what() << endl;
        }
        catch (...)
        {
          (*i)->getConstraints().push(new ProblemInvalidData(
            (*i), "Error: unknown type", "demand",
            (*i)->getDue(), (*i)->getDue(), (*i)->getQuantity(), false
          ));
          logger << "  Unknown type" << endl;
        }
      }
    }

    // Clean the list of demands of this cluster
    demands->clear();

    // Completely recreate all purchasing operation plans
    for (set<const OperationItemSupplier*>::iterator o = purchase_operations.begin();
      o != purchase_operations.end(); ++o
      )
    {
      // TODO This code assumes the buffer is ONLY replenished through these purchases.
      // When it is replenished through an alternate, it will not give the results we expect.

      // Erase existing proposed purchases
      const_cast<OperationItemSupplier*>(*o)->deleteOperationPlans(false);
      // Create new proposed purchases
      try
      {
        safety_stock_planning = true;
        state->curBuffer = nullptr;
        state->q_qty = -1.0;
        state->q_date = Date::infinitePast;
        state->a_cost = 0.0;
        state->a_penalty = 0.0;
        state->curDemand = nullptr;
        state->curOwnerOpplan = nullptr;
        state->a_qty = 0;
        (*o)->getBuffer()->solve(*solver, this);
        getCommandManager()->commit();
      }
      catch(...)
      {
        getCommandManager()->rollback();
      }
    }
    purchase_operations.clear();

    // Solve for safety stock in buffers.
    if (!solver->getPlanSafetyStockFirst())
      solveSafetyStock(solver);
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
    logger << "End solving cluster " << cluster << endl;
}


void SolverCreate::SolverData::solveSafetyStock(SolverCreate* solver)
{
  OperatorDelete cleanup(getCommandManager());
  cleanup.setConstrained(solver->isMaterialConstrained());
  safety_stock_planning = true;
  if (getLogLevel() > 0)
    logger << "Start safety stock replenishment pass   " << solver->getConstraints() << endl;
  vector< list<Buffer*> > bufs(HasLevel::getNumberOfLevels() + 1);
  for (Buffer::iterator buf = Buffer::begin(); buf != Buffer::end(); ++buf)
    if (buf->getCluster() == cluster
      && buf->getType() != *BufferInfinite::metadata      
      && (buf->getProducingOperation() || !solver->isMaterialConstrained())
      && (
        buf->getMinimum() 
        || buf->getMinimumCalendar() 
        || buf->getFlowPlans().begin() != buf->getFlowPlans().end()
        )
      )
      bufs[(buf->getLevel()>=0) ? buf->getLevel() : 0].push_back(&*buf);
  for (vector< list<Buffer*> >::iterator b_list = bufs.begin(); b_list != bufs.end(); ++b_list)
    for (list<Buffer*>::iterator b = b_list->begin(); b != b_list->end(); ++b)
      try
      {
        state->curBuffer = nullptr;
        // A quantity of -1 is a flag for the buffer solver to solve safety stock.
        state->q_qty = -1.0;
        state->q_date = Date::infinitePast;
        state->a_cost = 0.0;
        state->a_penalty = 0.0;
        planningDemand = nullptr;
        state->curDemand = nullptr;
        state->curOwnerOpplan = nullptr;
        // Call the buffer solver
        iteration_count = 0;
        (*b)->solve(*solver, this);
        // Check for excess
        (*b)->solve(cleanup, this);
        getCommandManager()->commit();
      }
      catch(...)
      {
        getCommandManager()->rollback();
      }

  if (getLogLevel() > 0)
    logger << "Finished safety stock replenishment pass" << endl;
  safety_stock_planning = false;
}


void SolverCreate::update_user_exits()
{
  setUserExitBuffer(getPyObjectProperty(Tags::userexit_buffer.getName()));
  setUserExitDemand(getPyObjectProperty(Tags::userexit_demand.getName()));
  setUserExitFlow(getPyObjectProperty(Tags::userexit_flow.getName()));
  setUserExitOperation(getPyObjectProperty(Tags::userexit_operation.getName()));
  setUserExitResource(getPyObjectProperty(Tags::userexit_resource.getName()));
}


void SolverCreate::solve(void *v)
{
  // Configure user exits
  update_user_exits();

  // Count how many clusters we have to plan
  int cl = (cluster == -1 ? HasLevel::getNumberOfClusters() + 1 : 1);

  // Categorize all demands in their cluster
  demands_per_cluster.resize(cl);
  if (cluster == -1)
  {
    for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
      if (i->getQuantity() > 0
        && (i->getStatus() == Demand::OPEN || i->getStatus() == Demand::QUOTE))
          demands_per_cluster[i->getCluster()].push_back(&*i);
  }
  else
  {
    for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
      if (i->getCluster() == cluster
        && i->getQuantity() > 0
        && (i->getStatus() == Demand::OPEN || i->getStatus() == Demand::QUOTE))
          demands_per_cluster[0].push_back(&*i);
  }

  // Delete of operationplans
  // This deletion is not multi-threaded... But on the other hand we need to
  // loop through the operations only once
  if (getErasePreviousFirst())
  {
    if (getLogLevel()>0) logger << "Deleting previous plan" << endl;
    for (Operation::iterator e=Operation::begin(); e!=Operation::end(); ++e)
      if (cluster == -1 || e->getCluster() == cluster)
        e->deleteOperationPlans();
  }

  // Solve in parallel threads.
  // When not solving in silent and autocommit mode, we only use a single
  // solver thread.
  // Otherwise we use as many worker threads as processor cores.
  ThreadGroup threads;
  if (getLogLevel()>0 || !getAutocommit() || cluster != -1)
    threads.setMaxParallel(1);

  // Register all clusters to be solved
  for (int j = 0; j < cl; ++j)
    threads.add(
      SolverData::runme,
      new SolverData(this, (cluster == -1) ? j :  cluster, &(demands_per_cluster[j]))
      );

  // Run the planning command threads and wait for them to exit
  threads.execute();
}


PyObject* SolverCreate::solve(PyObject *self, PyObject *args)
{
  // Parse the argument
  PyObject *dem = nullptr;
  if (args && !PyArg_ParseTuple(args, "|O:solve", &dem)) return nullptr;
  if (dem && !PyObject_TypeCheck(dem, Demand::metadata->pythonClass))
  {
    PyErr_SetString(PythonDataException, "solve(d) argument must be a demand");
    return nullptr;
  }

  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    SolverCreate* sol = static_cast<SolverCreate*>(self);
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
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


PyObject* SolverCreate::commit(PyObject *self, PyObject *args)
{
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    SolverCreate * me = static_cast<SolverCreate*>(self);
    assert(me->commands.getCommandManager());
    me->scanExcess(me->commands.getCommandManager());
    me->commands.getCommandManager()->commit();
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


PyObject* SolverCreate::rollback(PyObject *self, PyObject *args)
{
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    SolverCreate * me = static_cast<SolverCreate*>(self);
    assert(me->commands.getCommandManager());
    me->commands.getCommandManager()->rollback();
  }
  catch(...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}

} // end namespace
