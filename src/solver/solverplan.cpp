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

#define FREPPLE_CORE
#include "frepple/solver.h"
namespace frepple
{

DECLARE_EXPORT const MetaClass MRPSolver::metadata;

const short MRPSolver::LEADTIME = 1;
const short MRPSolver::MATERIAL = 2;
const short MRPSolver::CAPACITY = 4;
const short MRPSolver::FENCE = 8;


void LibrarySolver::initialize()
{
  // Initialize only once
  static bool init = false;
  if (init)
  {
    logger << "Warning: Calling Frepple::LibrarySolver::initialize() more "
    << "than once." << endl;
    return;
  }

  // Register all classes.
  MRPSolver::metadata.registerClass(
    "SOLVER",
    "SOLVER_MRP",
    Object::createString<MRPSolver>,
    true);

  // Close the library at the end
#ifdef HAVE_ATEXIT
  atexit(finalize);
#endif
  init = true;
}


DECLARE_EXPORT bool MRPSolver::demand_comparison(const Demand* l1, const Demand* l2)
{
  if (l1->getPriority() != l2->getPriority())
    return l1->getPriority() < l2->getPriority();
  else if (l1->getDue() != l2->getDue())
    return l1->getDue() < l2->getDue();
  else
    return l1->getQuantity() < l2->getQuantity();
}


DECLARE_EXPORT void MRPSolver::MRPSolverdata::execute()
{
  // Message
  MRPSolver* Solver = getSolver();
  if (Solver->getVerbose())
    logger << "Start solving cluster " << cluster << " at " << Date::now() << endl;

  // Solve the planning problem
  try
  {
    // Sort the demands of this problem.
    // We use a stable sort to get reproducible results between platforms
    // and STL implementations.
    stable_sort(demands.begin(), demands.end(), demand_comparison);

    // Loop through the list of all demands in this planning problem
    for (deque<Demand*>::const_iterator i = demands.begin();
        i != demands.end(); ++i)
      // Plan the demand
      try { (*i)->solve(*Solver,this); }
      catch (...)
      {
        // Error message
        logger << "Error: Caught an exception while solving demand '"
          << (*i)->getName() << "':" << endl;
        try { throw; }
        catch (bad_exception&) {logger << "  bad exception" << endl;}
        catch (exception& e) {logger << "  " << e.what() << endl;}
        catch (...) {logger << "  Unknown type" << endl;}

        // Cleaning up
        undo();
      }

    // Clean the list of demands of this problem
    demands.clear();
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
    try { throw; }
    catch (bad_exception&){logger << "  bad exception" << endl;}
    catch (exception& e) {logger << "  " << e.what() << endl;}
    catch (...) {logger << "  Unknown type" << endl;}

    // Clean up the operationplans of this cluster
    for (Operation::iterator f=Operation::begin(); f!=Operation::end(); ++f)
      if (f->getCluster() == cluster)
        f->deleteOperationPlans();
  }

  // Message
  if (Solver->getVerbose())
    logger << "End solving cluster " << cluster << " at " << Date::now() << endl;
}


DECLARE_EXPORT void MRPSolver::solve(void *v)
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
  for (Operation::iterator e=Operation::begin(); e!=Operation::end(); ++e)
    // The next if-condition is actually redundant if we plan everything
    if (demands_per_cluster.find(e->getCluster())!=demands_per_cluster.end())
      e->deleteOperationPlans();

  // Create the command list to control the execution
  CommandList threads;
  // Solve in parallel threads
  int cl = demands_per_cluster.size();
  threads.setMaxParallel( cl > getMaxParallel() ? getMaxParallel() : cl);
  // Otherwise a problem in a single cluster could spoil it all
  threads.setAbortOnError(false);
  for (classified_demand::iterator j = demands_per_cluster.begin();
      j != demands_per_cluster.end(); ++j)
    threads.add(new MRPSolverdata(this, j->first, j->second));

  // Run the planning command threads and wait for them to exit
  threads.execute();
}


DECLARE_EXPORT void MRPSolver::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
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
  if (maxparallel) o->writeElement(Tags::tag_maxparallel, maxparallel);

  // Write the parent class
  Solver::writeElement(o, tag, NOHEADER);
}


DECLARE_EXPORT void MRPSolver::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_constraints))
    setConstraints(pElement.getInt());
  else if (pElement.isA(Tags::tag_maxparallel))
    setMaxParallel(pElement.getInt());
  else
    Solver::endElement(pIn, pElement);
}


} // end namespace
