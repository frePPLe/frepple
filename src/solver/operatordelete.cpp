/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba                 *
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


DECLARE_EXPORT const MetaClass* OperatorDelete::metadata;


int OperatorDelete::initialize()
{
  // Initialize the metadata
  metadata = new MetaClass(
    "solver", "solver_delete", Object::createString<OperatorDelete>
    );

  // Initialize the Python class
  FreppleClass<OperatorDelete, Solver>::getType().addMethod(
    "solve", solve, METH_VARARGS, "run the solver"
    );
  return FreppleClass<OperatorDelete, Solver>::initialize();
}


DECLARE_EXPORT void OperatorDelete::solve(void *v)
{
   // Loop over all buffers Push to stack, in order of level TODO

  // Clean up all buffers in the list
  while(!buffersToScan.empty())
  {
    Buffer* curbuf = buffersToScan.back();
    buffersToScan.pop_back();
    solve(curbuf);
  }
}


DECLARE_EXPORT void OperatorDelete::solve(OperationPlan* o, void* v)
{
  if (!o) return; // Null argument passed

  // Mark all buffers we consume from
  pushBuffers(o, true);

  // Delete the operationplan
  if (cmds)
    cmds->add(new CommandDeleteOperationPlan(o));
  else
    delete o;

  // Propagate to all upstream buffers
  while(!buffersToScan.empty())
  {
    Buffer* curbuf = buffersToScan.back();
    buffersToScan.pop_back();
    solve(curbuf);
  }
}


DECLARE_EXPORT void OperatorDelete::solve(const Resource* r, void* v)
{
  if (getLogLevel()>0)
    logger << "Scanning " << r << " for excess" << endl;

  // Loop over all operationplans on the resource
  for (Resource::loadplanlist::const_iterator i = r->getLoadPlans().begin();
    i != r->getLoadPlans().end(); ++i)
  {
    if (i->getType() == 1)
      // Add all buffers into which material is produced to the stack
      pushBuffers(static_cast<const LoadPlan*>(&*i)->getOperationPlan(), false);
  }

  // Process all buffers found, and their upstream colleagues
  while(!buffersToScan.empty())
  {
    Buffer* curbuf = buffersToScan.back();
    buffersToScan.pop_back();
    solve(curbuf);
  }
}


DECLARE_EXPORT void OperatorDelete::solve(const Demand* d, void* v)
{
  if (getLogLevel()>1)
    logger << "Scanning " << d << " for excess" << endl;

  // Delete all delivery operationplans.
  // Note that an extra loop is used to assure that our iterator doesn't get
  // invalidated during the deletion.
  while (true)
  {
    // Find a candidate operationplan to delete
    OperationPlan *candidate = NULL;
    const Demand::OperationPlan_list& deli = d->getDelivery();
    for (Demand::OperationPlan_list::const_iterator i = deli.begin(); i != deli.end(); ++i)
      if (!(*i)->getLocked())
      {
        candidate = *i;
        break;
      }
      if (!candidate) break;

      // Push the buffer on the stack in which the deletion creates excess inventory
      pushBuffers(candidate, true);

      // Delete only the delivery, immediately or through a delete command
      if (cmds)
        cmds->add(new CommandDeleteOperationPlan(candidate));
      else
        delete candidate;
  }

  // Propagate to all upstream buffers
  while(!buffersToScan.empty())
  {
    Buffer* curbuf = buffersToScan.back();
    buffersToScan.pop_back();
    solve(curbuf);
  }
}


void OperatorDelete::pushBuffers(OperationPlan* o, bool consuming)
{
  // Loop over all flowplans
  for (OperationPlan::FlowPlanIterator i = o->beginFlowPlans(); i != o->endFlowPlans(); ++i)
  {
    // Skip flowplans we're not interested in
    if ((consuming && i->getQuantity() >= 0)
      || (!consuming && i->getQuantity() <= 0))
      continue;

    // Check if the buffer is already found on the stack
    bool found = false;
    for (int j = buffersToScan.size()-1; j>=0 && !found; --j)
      if (buffersToScan[j] == i->getBuffer())
        found = true;

    // Add the buffer to the stack
    if (!found) buffersToScan.push_back(const_cast<Buffer*>(i->getBuffer()));
  }

  // Recursive call for all suboperationplans
  for (OperationPlan::iterator subopplan(o); subopplan != OperationPlan::end(); ++subopplan)
    pushBuffers(&*subopplan, consuming);
}


void OperatorDelete::solve(const Buffer* b, void* v)
{
  if (getLogLevel()>1)
    logger << "Scanning " << b << " for excess" << endl;

  Buffer::flowplanlist::const_iterator fiter = b->getFlowPlans().rbegin();
  Buffer::flowplanlist::const_iterator fend = b->getFlowPlans().end();
  if (fiter == fend)
    return; // There isn't a single flowplan in the buffer
  double excess = fiter->getOnhand() - fiter->getMin();

  // Find the earliest occurence of the excess
  fiter = b->getFlowPlans().begin();
  while (excess > ROUNDING_ERROR && fiter != fend)
  {
    if (fiter->getQuantity() <= 0)
    {
      // Not a producer
      ++fiter;
      continue;
    }
    FlowPlan* fp = NULL;
    if (fiter->getType() == 1)
      fp = const_cast<FlowPlan*>(static_cast<const FlowPlan*>(&*fiter));
    double cur_excess = b->getFlowPlans().getExcess(&*fiter);
    if (!fp || fp->getOperationPlan()->getLocked() || cur_excess < ROUNDING_ERROR)
    {
      // No excess producer, or it's locked
      ++fiter;
      continue;
    }
    assert(fp);

    // Increment the iterator here, because it can get invalidated later on
    while (
      fiter != fend
      && fiter->getType() == 1
      && static_cast<const FlowPlan*>(&*fiter)->getOperationPlan()->getTopOwner()==fp->getOperationPlan()->getTopOwner()
      )
        ++fiter;
    if (cur_excess >= fp->getQuantity() - ROUNDING_ERROR)
    {
      // The complete operationplan is excess.
      // Reduce the excess
      excess -= fp->getQuantity();
      // Add upstream buffers to the stack
      pushBuffers(fp->getOperationPlan(), true);
      // Log message
      if (getLogLevel()>0)
        logger << "Removing excess operationplan: '"
          << fp->getOperationPlan()->getOperation()
          << "'  " << fp->getOperationPlan()->getDates()
          << "  " << fp->getOperationPlan()->getQuantity()
          << endl;
      // Delete operationplan
      if (cmds)
        cmds->add(new CommandDeleteOperationPlan(fp->getOperationPlan()));
      else
        delete fp->getOperationPlan();
    }
    else
    {
      // Reduce the operationplan
      double newsize = fp->setQuantity(fp->getQuantity() - cur_excess, false, false);
      if (newsize == fp->getQuantity())
        // No resizing is feasible
        continue;
      // Add upstream buffers to the stack
      pushBuffers(fp->getOperationPlan(), true);
      // Reduce the excess
      excess -= fp->getQuantity() - newsize;
      if (getLogLevel()>0)
        logger << "Resizing excess operationplan to " << newsize << ": '"
          << fp->getOperationPlan()->getOperation()
          << "'  " << fp->getOperationPlan()->getDates()
          << "  " << fp->getOperationPlan()->getQuantity()
          << endl;
      // Resize operationplan
      if (cmds)
        cmds->add(new CommandMoveOperationPlan(
          fp->getOperationPlan(), Date::infinitePast,
          fp->getOperationPlan()->getDates().getEnd(), newsize)
          );
      else
        fp->getOperationPlan()->setQuantity(newsize);
    }
  }
}


PyObject* OperatorDelete::solve(PyObject *self, PyObject *args)
{
  // Parse the argument
  PyObject *obj = NULL;
  short objtype = 0;
  if (args && !PyArg_ParseTuple(args, "|O:solve", &obj)) return NULL;
  if (obj)
  {
    if (PyObject_TypeCheck(obj, Demand::metadata->pythonClass))
      objtype = 1;
    else if (PyObject_TypeCheck(obj, Buffer::metadata->pythonClass))
      objtype = 2;
    else if (PyObject_TypeCheck(obj, Resource::metadata->pythonClass))
      objtype = 3;
    else if (PyObject_TypeCheck(obj, OperationPlan::metadata->pythonClass))
      objtype = 4;
    else
    {
      PyErr_SetString(
        PythonDataException,
        "solve(d) argument must be a demand, buffer, resource or operationplan"
        );
      return NULL;
    }
  }

  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    OperatorDelete* sol = static_cast<OperatorDelete*>(self);
    switch (objtype)
    {
      case 0:
        // Delete all excess
        sol->solve();
        break;
      case 1:
        // Delete upstream of a single demand
        sol->solve(static_cast<Demand*>(obj));
        break;
      case 2:
        // Delete upstream of a single buffer
        sol->solve(static_cast<Buffer*>(obj));
        break;
      case 3:
        // Delete upstream of a single resource
        sol->solve(static_cast<Resource*>(obj));
      case 4:
        // Delete an operationplan
        sol->solve(static_cast<OperationPlan*>(obj));
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

}
