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
#include "frepple/model.h"
#include <sys/stat.h>

namespace frepple
{

void LibraryModel::initialize()
{
  // Initialize only once
  static bool init = false;
  if (init)
  {
    logger << "Warning: Calling frepple::LibraryModel::initialize() more "
    << "than once." << endl;
    return;
  }
  init = true;

  // Initialize the utilities library
  LibraryUtils::initialize();

  // Register new types in Python
  int nok = 0;
  PyObject* module = PythonInterpreter::getModule();
  nok += Plan::initialize(module);

  // Initialize the solver metadata.
  nok += Solver::initialize(module);
  nok += SolverIterator::initialize(module);

  // Initialize the location metadata.
  nok += Location::initialize(module);
  nok += LocationDefault::initialize(module);
  nok += LocationIterator::initialize(module);

  // Initialize the customer metadata.
  nok += Customer::initialize(module);
  nok += CustomerDefault::initialize(module);
  nok += CustomerIterator::initialize(module);

  // Initialize the calendar metadata.
  nok += Calendar::initialize(module);
  nok += CalendarBucketIterator::initialize(module);  // xxx remove
  nok += CalendarEventIterator::initialize(module);   // xxx remove
  nok += CalendarBool::initialize(module);
  nok += CalendarVoid::initialize(module);
  nok += CalendarDouble::initialize(module);
  nok += CalendarString::initialize(module);
  nok += CalendarInt::initialize(module);
  nok += CalendarOperation::initialize(module);
  nok += CalendarIterator::initialize(module);

  // Initialize the operation metadata.
  nok += Operation::initialize(module);
  nok += OperationAlternate::initialize(module);
  nok += OperationFixedTime::initialize(module);
  nok += OperationTimePer::initialize(module);
  nok += OperationRouting::initialize(module);
  nok += OperationIterator::initialize(module);

  // Initialize the item metadata.
  nok += Item::initialize(module);
  nok += ItemDefault::initialize(module);
  nok += ItemIterator::initialize(module);

  // Initialize the buffer metadata.
  nok += Buffer::initialize(module);
  nok += BufferDefault::initialize(module);
  nok += BufferInfinite::initialize(module);
  nok += BufferProcure::initialize(module);
  nok += BufferIterator::initialize(module);

  // Initialize the demand metadata.
  nok += Demand::initialize(module);
  nok += DemandIterator::initialize(module);
  nok += DemandDefault::initialize(module);
  nok += DemandPlanIterator::initialize(module);

  // Initialize the resource metadata.
  nok += Resource::initialize(module);
  nok += ResourceDefault::initialize(module);
  nok += ResourceInfinite::initialize(module);
  nok += ResourceIterator::initialize(module);

  // Initialize the load metadata.
  nok += Load::initialize(module);  

  // Initialize the flow metadata.
  nok += Flow::initialize(module);

  // Initialize the operationplan metadata.
  nok += OperationPlan::initialize(module);
  nok += OperationPlanIterator::initialize(module);

  // Initialize the problem metadata.
  nok += Problem::initialize(module);
  nok += ProblemIterator::initialize(module);

  // Initialize the pegging metadata.
  nok += PeggingIterator::initialize(module);

  nok += PythonFlowIterator::initialize(module); // xxx
  nok += PythonFlowPlan::initialize(module);  // xxx
  nok += PythonFlowPlanIterator::initialize(module);  // xxx
  nok += PythonLoadIterator::initialize(module);  // xxx
  nok += PythonLoadPlan::initialize(module);  // xxx
  nok += PythonLoadPlanIterator::initialize(module);  // xxx

  // Exit if errors were found
  if (nok) throw RuntimeException("Error registering new Python types");

  // Register new methods in Python
  PythonInterpreter::registerGlobalMethod(
    "loadmodule", CommandLoadLibrary::executePython, METH_VARARGS,
    "Dynamically load a module in memory.");
  PythonInterpreter::registerGlobalMethod(
    "printsize", CommandPlanSize::executePython, METH_NOARGS,
    "Print information about the memory consumption.");
  PythonInterpreter::registerGlobalMethod(
    "erase", CommandErase::executePython, METH_VARARGS,
    "Removes the plan data from memory, and optionally the static info too.");
  PythonInterpreter::registerGlobalMethod(
    "readXMLdata", CommandReadXMLString::executePython, METH_VARARGS,
    "Processes an XML string passed as argument.");
  PythonInterpreter::registerGlobalMethod(
    "readXMLfile", CommandReadXMLFile::executePython, METH_VARARGS,
    "Read an XML-file.");
  PythonInterpreter::registerGlobalMethod(
    "saveXMLfile", CommandSave::executePython, METH_VARARGS,
    "Save the model to an XML-file.");
  PythonInterpreter::registerGlobalMethod(
    "saveplan", CommandSavePlan::executePython, METH_VARARGS,
    "Save the main plan information to a file.");
  PythonInterpreter::registerGlobalMethod(
    "buffers", BufferIterator::create, METH_NOARGS,
    "Returns an iterator over the buffers.");
  PythonInterpreter::registerGlobalMethod(
    "locations", LocationIterator::create, METH_NOARGS,
    "Returns an iterator over the locations.");
  PythonInterpreter::registerGlobalMethod(
    "customers", CustomerIterator::create, METH_NOARGS,
    "Returns an iterator over the customer.");
  PythonInterpreter::registerGlobalMethod(
    "items", ItemIterator::create, METH_NOARGS,
    "Returns an iterator over the items.");
  PythonInterpreter::registerGlobalMethod(
    "calendars", CalendarIterator::create, METH_NOARGS,
    "Returns an iterator over the calendars.");
  PythonInterpreter::registerGlobalMethod(
    "demands", DemandIterator::create, METH_NOARGS,
    "Returns an iterator over the demands.");
  PythonInterpreter::registerGlobalMethod(
    "resources", ResourceIterator::create, METH_NOARGS,
    "Returns an iterator over the resources.");
  PythonInterpreter::registerGlobalMethod(
    "operations", OperationIterator::create, METH_NOARGS,
    "Returns an iterator over the operations.");
  PythonInterpreter::registerGlobalMethod(
    "operationplans", OperationPlanIterator::create, METH_NOARGS,
    "Returns an iterator over the operationplans.");
  PythonInterpreter::registerGlobalMethod(
    "problems", ProblemIterator::create, METH_NOARGS,
    "Returns an iterator over the problems.");
  PythonInterpreter::registerGlobalMethod(
    "solvers", SolverIterator::create, METH_NOARGS,
    "Returns an iterator over the solvers.");
}


DECLARE_EXPORT void CommandPlanSize::execute()
{
  size_t count, memsize;

  // Log
  if (getVerbose())
    logger << "Start size report at " << Date::now() << endl;
  Timer t;

  // Intro
  logger << endl << "Size information of frePPLe " << PACKAGE_VERSION
  << " (" << __DATE__ << ")" << endl << endl;

  // Print current locale
  #if defined(HAVE_SETLOCALE) || defined(_MSC_VER)
  logger << "Locale: " << setlocale(LC_ALL,NULL) << endl << endl;
  #else
  logger << endl;
  #endif

  // Print loaded modules
  CommandLoadLibrary::printModules();

  // Print the number of clusters
  logger << "Clusters: " << HasLevel::getNumberOfClusters() 
    << " (hanging: " << HasLevel::getNumberOfHangingClusters() << ")" 
    << endl << endl;

  // Header for memory size
  logger << "Memory usage:" << endl;
  logger << "Model        \tNumber\tMemory" << endl;
  logger << "-----        \t------\t------" << endl;

  // Plan
  size_t total = Plan::instance().getSize();
  logger << "Plan         \t1\t"<< Plan::instance().getSize() << endl;

  // Locations
  memsize = 0;
  for (Location::iterator l = Location::begin(); l != Location::end(); ++l)
    memsize += l->getSize();
  logger << "Location     \t" << Location::size() << "\t" << memsize << endl;
  total += memsize;

  // Customers
  memsize = 0;
  for (Customer::iterator c = Customer::begin(); c != Customer::end(); ++c)
    memsize += c->getSize();
  logger << "Customer     \t" << Customer::size() << "\t" << memsize << endl;
  total += memsize;

  // Buffers
  memsize = 0;
  for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
    memsize += b->getSize();
  logger << "Buffer       \t" << Buffer::size() << "\t" << memsize << endl;
  total += memsize;

  // Resources
  memsize = 0;
  for (Resource::iterator r = Resource::begin(); r != Resource::end(); ++r)
    memsize += r->getSize();
  logger << "Resource     \t" << Resource::size() << "\t" << memsize << endl;
  total += memsize;

  // Operations, flows and loads
  size_t countFlows(0), memFlows(0), countLoads(0), memLoads(0);
  memsize = 0;
  for (Operation::iterator o = Operation::begin(); o != Operation::end(); ++o)
  {
    memsize += o->getSize();
    for (Operation::flowlist::const_iterator fl = o->getFlows().begin();
        fl != o->getFlows().end(); ++ fl)
    {
      ++countFlows;
      memFlows += fl->getSize();
    }
    for (Operation::loadlist::const_iterator ld = o->getLoads().begin();
        ld != o->getLoads().end(); ++ ld)
    {
      ++countLoads;
      memLoads += ld->getSize();
    }
  }
  logger << "Operation    \t" << Operation::size() << "\t" << memsize << endl;
  logger << "Flow         \t" << countFlows << "\t" << memFlows  << endl;
  logger << "Load         \t" << countLoads << "\t" << memLoads  << endl;
  total += memsize + memFlows + memLoads;

  // Calendars (which includes the buckets)
  memsize = 0;
  for (Calendar::iterator cl = Calendar::begin(); cl != Calendar::end(); ++cl)
    memsize += cl->getSize();
  logger << "Calendar     \t" << Calendar::size() << "\t" << memsize  << endl;
  total += memsize;

  // Items
  memsize = 0;
  for (Item::iterator i = Item::begin(); i != Item::end(); ++i)
    memsize += i->getSize();
  logger << "Item         \t" << Item::size() << "\t" << memsize  << endl;
  total += memsize;

  // Demands
  memsize = 0;
  for (Demand::iterator dm = Demand::begin(); dm != Demand::end(); ++dm)
    memsize += dm->getSize();
  logger << "Demand       \t" << Demand::size() << "\t" << memsize  << endl;
  total += memsize;

  // Operationplans
  size_t countloadplans(0), countflowplans(0);
  memsize = count = 0;
  for (OperationPlan::iterator j = OperationPlan::begin();
      j!=OperationPlan::end(); ++j)
  {
    ++count;
    memsize += sizeof(*j);
    countloadplans += j->sizeLoadPlans();
    countflowplans += j->sizeFlowPlans();
  }
  total += memsize;
  logger << "OperationPlan\t" << count << "\t" << memsize << endl;

  // Flowplans
  memsize = countflowplans * sizeof(FlowPlan);
  total +=  memsize;
  logger << "FlowPlan     \t" << countflowplans << "\t" << memsize << endl;

  // Loadplans
  memsize = countloadplans * sizeof(LoadPlan);
  total +=  memsize;
  logger << "LoadPlan     \t" << countloadplans << "\t" << memsize << endl;

  // Problems
  memsize = count = 0;
  for (Problem::const_iterator pr = Problem::begin(); pr!=Problem::end(); ++pr)
  {
    ++count;
    memsize += pr->getSize();
  }
  total += memsize;
  logger << "Problem      \t" << count << "\t" << memsize << endl;

  // TOTAL
  logger << "Total        \t\t" << total << endl << endl;

  // Log
  if (getVerbose())
    logger << "Finished size report at " << Date::now() << " : " << t << endl;
}


}
