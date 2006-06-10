/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/solver/solverplan.cpp $
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

#define FREPPLE_CORE 
#include "frepple/solver.h"
namespace frepple
{

const MetaClass MRPSolver::metadata;
#ifdef HAVE_LIBGLPK
const MetaClass LPSolver::metadata;
#endif


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
    clog << "Warning: Calling Frepple::LibrarySolver::initialize() more " 
      << "than once." << endl;
    return;
  }

  // Register all classes.
  MRPSolver::metadata.registerClass(
    "SOLVER", 
    "SOLVER_MRP", 
    Object::createString<MRPSolver>, 
    true);
#ifdef HAVE_LIBGLPK
  LPSolver::metadata.registerClass(
    "SOLVER", 
    "SOLVER_LP", 
    Object::createString<LPSolver>);
#endif

  // Close the library at the end
#ifdef HAVE_ATEXIT
  atexit(finalize);
#endif
  init = true;
}


bool MRPSolver::demand_comparison(Demand* l1, Demand* l2)
{
  if (l1->getPriority() != l2->getPriority())
    return l1->getPriority() < l2->getPriority();
  else
    return l1->getDue() < l2->getDue();
}


void* MRPSolver::SolverThread(void *arg)
{
  // Message
  MRPSolverdata* Solverthread = static_cast<MRPSolverdata*>(arg);
  MRPSolver* Solver = Solverthread->getSolver();
  unsigned int myid = Solverthread->threadid;

  if (Solver->getVerbose()) clog << "Start planning thread " << myid << endl;

  // Find the next planning problem
  cluster_iterator mycluster;
  while ((mycluster=next_cluster(Solver)) != Solver->demands_per_cluster.end())
  {
    try
    {
      // Message
      if (Solver->getVerbose())
        clog << "Thread " << myid << " starts solving cluster "
        << mycluster->first << " at " << Date::now() << endl;

      // Sort the demands of this problem.
      // We use a stable sort to get reproducible results between platforms
      // and STL implementations.
      stable_sort(mycluster->second.begin(), mycluster->second.end(),
        demand_comparison);

      // Loop through the list of all demands in this planning problem
      for (deque<Demand*>::const_iterator i = mycluster->second.begin();
           i != mycluster->second.end(); ++i)
        // Plan the demand
        try { (*i)->solve(*Solver,Solverthread); }
        catch (...)
        {
          // Error message
          clog << "Error: Caught an exception in thread " << myid
          << " while solving demand '" << (*i)->getName() << "':" << endl;
          try { throw; }
          catch (bad_exception&) {clog << "  bad exception" << endl;}
          catch (exception& e) {clog << "  " << e.what() << endl;}
          catch (...) {clog << "  Unknown type" << endl;}

          // Cleaning up
          Solverthread->actions.undo();
        }

      // Clean the list of demands of this problem
      mycluster->second.clear();
    }
    catch (...)
    {
      // We come in this exception handling code only if there is a problem with
      // with this cluster that goes beyond problems with single orders.
      // If the problem is with single orders, the exception handling code above
      // will do a proper rollback.

      // Error message
      clog << "Error: Caught an exception in thread " << myid
      << " while solving cluster " << mycluster->first << ":" << endl;
      try { throw; }
      catch (bad_exception&){clog << "  bad exception" << endl;}
      catch (exception& e) {clog << "  " << e.what() << endl;}
      catch (...) {clog << "  Unknown type" << endl;}

      // Clean up the operationplans of this cluster
      for (Operation::iterator f=Operation::begin(); f!=Operation::end(); ++f)
        if ((*f)->getCluster() == mycluster->first)
        	(*f)->deleteOperationPlans();
    }
  }

  // Message
  if (Solver->getVerbose()) clog << "End planning thread " << myid << endl;

  // Return value doesn't matter. The POSIX pthread interface wants a void
  // pointer as return value, so we just pass NULL...
  return NULL;
}


MRPSolver::cluster_iterator MRPSolver::next_cluster(MRPSolver* Solver)
{
  cluster_iterator nxt;
#ifdef MT
  static pthread_mutex_t dd;
  pthread_mutex_lock(&dd);
#endif
  nxt = Solver->cur_cluster;
  if (Solver->cur_cluster != Solver->demands_per_cluster.end())
    ++Solver->cur_cluster;
#ifdef MT
  pthread_mutex_unlock(&dd);
#endif
  return nxt;
}


/** @todo enhance to allow cluster level planning */
void MRPSolver::solve(void *v)
{
  // Categorize all demands in their cluster
  for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
    demands_per_cluster[(*i)->getCluster()].push_back(*i);
  cur_cluster = demands_per_cluster.begin();

  // Delete of operationplans of the affected clusters
  // This deletion is not multi-threaded... But on the other hand we need to
  // loop through the operations only once (rather than as many times as there
  // are clusters)
  // A multi-threaded alternative would be to hash the operations here, and
  // then delete in each thread.
  for (Operation::iterator e=Operation::begin(); e!=Operation::end(); ++e)
    // The next if-condition is actually redundant if we want to plan everything
    if (demands_per_cluster.find((*e)->getCluster())!=demands_per_cluster.end())
      (*e)->deleteOperationPlans();

  // Compute how many threads to use...
#ifdef MT
  int numthreads = demands_per_cluster.size();
  if(numthreads == 0) return;
  if(numthreads > MAXTHREADS) numthreads = MAXTHREADS;

  // Do we need to spawn new threads at all?
  if (numthreads==1)
  {
#endif
    // This block of code is executed in a single-threaded executable or
    // in a multi-threaded executable with a single planning problem.
    MRPSolverdata f;
    f.threadid = 1;
    f.sol = this;
    SolverThread(&f);
    return;
#ifdef MT
  }

  pthread_t threads[numthreads];         // holds thread info
  int errcode;                           // holds pthread error code
  int status;                            // holds return value
  MRPSolverdata data[numthreads];        // data structure per thread

  // Create the planning threads
  for (int worker=0; worker<numthreads; ++worker)
  {
    data[worker].threadid = worker;
    data[worker].sol = this;
    if ((errcode=pthread_create(&threads[worker],  // thread struct
                                NULL,              // default thread attributes
                                SolverThread,      // start routine
                                &data[worker])))   // arg to routine
      {
        // @todo Not exception safe: some threads may already be launched!
        ostringstream ch;
        ch << "Couldn't create thread " << worker << ", error " << errcode;
        throw RuntimeException(ch.str());
      }
  }

  // Wait for the planning threads as they exit
  for (int worker=0; worker<numthreads; ++worker)
    // Wait for thread to terminate
    if ((errcode=pthread_join(threads[worker],(void**) &status)))
    {
      // @todo thread joining is not exception safe
      ostringstream ch;
      ch << "Couldn't join with thread " << worker << ", error " << errcode;
      throw RuntimeException(ch.str());
    }
#endif
}


void MRPSolver::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
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

  // Write the parent class
  Solver::writeElement(o, tag, NOHEADER);
}


void MRPSolver::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_constraints))
    setConstraints(pElement.getInt());
  else 
    Solver::endElement(pIn, pElement);
}


} // end namespace
