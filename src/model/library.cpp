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
// Solver metadata
DECLARE_EXPORT const MetaCategory* Solver::metadata;

// Load metadata
DECLARE_EXPORT const MetaCategory* Load::metadata;

// Location metadata
DECLARE_EXPORT const MetaCategory* Location::metadata;
DECLARE_EXPORT const MetaClass* LocationDefault::metadata;

// Buffer metadata
DECLARE_EXPORT const MetaCategory* Buffer::metadata;
DECLARE_EXPORT const MetaClass* BufferDefault::metadata,
  *BufferInfinite::metadata,
  *BufferProcure::metadata;

// Calendar metadata
DECLARE_EXPORT const MetaCategory* Calendar::metadata;
DECLARE_EXPORT const MetaCategory* Calendar::Bucket::metadata;
DECLARE_EXPORT const MetaClass *CalendarVoid::metadata,
  *CalendarDouble::metadata,
  *CalendarInt::metadata,
  *CalendarBool::metadata,
  *CalendarString::metadata,
  *CalendarOperation::metadata;

// Flow metadata
DECLARE_EXPORT const MetaCategory* Flow::metadata;
DECLARE_EXPORT const MetaClass* FlowStart::metadata,
  *FlowEnd::metadata;

// Operation metadata
DECLARE_EXPORT const MetaCategory* Operation::metadata;
DECLARE_EXPORT const MetaClass* OperationFixedTime::metadata,
  *OperationTimePer::metadata,
  *OperationRouting::metadata,
  *OperationAlternate::metadata;

// OperationPlan metadata
DECLARE_EXPORT const MetaClass* OperationPlan::metadata;
DECLARE_EXPORT const MetaCategory* OperationPlan::metacategory;

// Resource metadats
DECLARE_EXPORT const MetaCategory* Resource::metadata;
DECLARE_EXPORT const MetaClass* ResourceDefault::metadata;
DECLARE_EXPORT const MetaClass* ResourceInfinite::metadata;

// Item metadata
DECLARE_EXPORT const MetaCategory* Item::metadata;
DECLARE_EXPORT const MetaClass* ItemDefault::metadata;

// Customer metadata
DECLARE_EXPORT const MetaCategory* Customer::metadata;
DECLARE_EXPORT const MetaClass* CustomerDefault::metadata;

// Demand metadata
DECLARE_EXPORT const MetaCategory* Demand::metadata;
DECLARE_EXPORT const MetaClass* DemandDefault::metadata;

// Plan metadata
DECLARE_EXPORT const MetaCategory* Plan::metadata;

// Problem metadata
DECLARE_EXPORT const MetaCategory* Problem::metadata;
DECLARE_EXPORT const MetaClass* ProblemMaterialExcess::metadata,
  *ProblemMaterialShortage::metadata,
  *ProblemExcess::metadata,
  *ProblemShort::metadata,
  *ProblemEarly::metadata,
  *ProblemLate::metadata,
  *ProblemDemandNotPlanned::metadata,
  *ProblemPlannedEarly::metadata,
  *ProblemPlannedLate::metadata,
  *ProblemPrecedence::metadata,
  *ProblemBeforeFence::metadata,
  *ProblemBeforeCurrent::metadata,
  *ProblemCapacityUnderload::metadata,
  *ProblemCapacityOverload::metadata;


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

  // Create a singleton plan object
  // Since we can count on the initialization being executed only once, also
  // in a multi-threaded configuration, we don't need a more advanced mechanism
  // to protect the singleton plan.
  Plan::thePlan = new Plan();

  // Initialize the plan metadata.
  Plan::metadata = new MetaCategory("plan","");

  // Initialize the solver metadata.
  Solver::metadata = new MetaCategory
    ("solver", "solvers", Solver::reader, Solver::writer);

  // Initialize the location metadata.
  Location::metadata = new MetaCategory
    ("location", "locations", Location::reader, Location::writer);
  LocationDefault::metadata = new MetaClass("location", "location_default",
    Object::createString<LocationDefault>, true);

  // Initialize the customer metadata.
  Customer::metadata = new MetaCategory
    ("customer", "customers", Customer::reader, Customer::writer);
  CustomerDefault::metadata = new MetaClass(
    "customer",
    "customer_default",
    Object::createString<CustomerDefault>, true);

  // Initialize the calendar metadata.
  Calendar::Bucket::metadata = new MetaCategory("bucket", "buckets");
  Calendar::metadata = new MetaCategory
    ("calendar", "calendars", Calendar::reader, Calendar::writer);
  CalendarVoid::metadata = new MetaClass(
    "calendar",
    "calendar_void",
    Object::createString<CalendarVoid>);
  CalendarDouble::metadata = new MetaClass(
    "calendar",
    "calendar_double",
    Object::createString<CalendarDouble>, true);
  CalendarInt::metadata = new MetaClass(
    "calendar",
    "calendar_integer",
    Object::createString<CalendarInt>);
  CalendarBool::metadata = new MetaClass(
    "calendar",
    "calendar_boolean",
    Object::createString<CalendarBool>);
  CalendarString::metadata = new MetaClass(
    "calendar",
    "calendar_string",
    Object::createString<CalendarString>);
  CalendarOperation::metadata = new MetaClass(
    "calendar",
    "calendar_operation",
    Object::createString<CalendarOperation>);

  // Initialize the operation metadata.
  Operation::metadata = new MetaCategory
    ("operation", "operations", Operation::reader, Operation::writer);
  OperationFixedTime::metadata = new MetaClass(
    "operation",
    "operation_fixed_time",
    Object::createString<OperationFixedTime>, true);
  OperationTimePer::metadata = new MetaClass(
    "operation",
    "operation_time_per",
    Object::createString<OperationTimePer>);
  OperationRouting::metadata = new MetaClass(
    "operation",
    "operation_routing",
    Object::createString<OperationRouting>);
  OperationAlternate::metadata = new MetaClass(
    "operation",
    "operation_alternate",
    Object::createString<OperationAlternate>);

  // Initialize the item metadata.
  Item::metadata = new MetaCategory
    ("item", "items", Item::reader, Item::writer);
  ItemDefault::metadata = new MetaClass("item", "item_default",
    Object::createString<ItemDefault>, true);

  // Initialize the buffer metadata.
  Buffer::metadata = new MetaCategory
    ("buffer", "buffers", Buffer::reader, Buffer::writer);
  BufferDefault::metadata = new MetaClass(
    "buffer",
    "buffer_default",
    Object::createString<BufferDefault>, true);
  BufferInfinite::metadata = new MetaClass(
    "buffer",
    "buffer_infinite",
    Object::createString<BufferInfinite>);
  BufferProcure::metadata = new MetaClass(
    "buffer",
    "buffer_procure",
    Object::createString<BufferProcure>);

  // Initialize the demand metadata.
  Demand::metadata = new MetaCategory
    ("demand", "demands", Demand::reader, Demand::writer);
  DemandDefault::metadata = new MetaClass(
    "demand",
    "demand_default",
    Object::createString<DemandDefault>, true);

  // Initialize the resource metadata.
  Resource::metadata = new MetaCategory
    ("resource", "resources", Resource::reader, Resource::writer);
  ResourceDefault::metadata = new MetaClass(
    "resource",
    "resource_default",
    Object::createString<ResourceDefault>,
    true);
  ResourceInfinite::metadata = new MetaClass(
    "resource",
    "resource_infinite",
    Object::createString<ResourceInfinite>);

  // Initialize the load metadata.
  Load::metadata = new MetaCategory
    ("load", "loads", MetaCategory::ControllerDefault, NULL);
  const_cast<MetaCategory*>(Load::metadata)->registerClass(
    "load","load",true,Object::createDefault<Load>
    );

  // Initialize the flow metadata.
  Flow::metadata = new MetaCategory
    ("flow", "flows", MetaCategory::ControllerDefault);
  FlowStart::metadata = new MetaClass(
    "flow",
    "flow_start",
    Object::createDefault<FlowStart>, true);
  FlowEnd::metadata = new MetaClass(
    "flow",
    "flow_end",
    Object::createDefault<FlowEnd>);

  // Initialize the operationplan metadata.
  OperationPlan::metacategory = new MetaCategory("operationplan", "operationplans",
    OperationPlan::createOperationPlan, OperationPlan::writer);
  OperationPlan::metadata = new MetaClass("operationplan", "operationplan");

  // Initialize the problem metadata.
  Problem::metadata = new MetaCategory
    ("problem", "problems", NULL, Problem::writer);
  ProblemMaterialExcess::metadata = new MetaClass
    ("problem","material excess");
  ProblemMaterialShortage::metadata = new MetaClass
    ("problem","material shortage");
  ProblemExcess::metadata = new MetaClass
    ("problem","excess");
  ProblemShort::metadata = new MetaClass
    ("problem","short");
  ProblemEarly::metadata = new MetaClass
    ("problem","early");
  ProblemLate::metadata = new MetaClass
    ("problem","late");
  ProblemDemandNotPlanned::metadata = new MetaClass
    ("problem","unplanned");
  ProblemPlannedEarly::metadata = new MetaClass
    ("problem","planned early");
  ProblemPlannedLate::metadata = new MetaClass
    ("problem","planned late");
  ProblemPrecedence::metadata = new MetaClass
    ("problem","precedence");
  ProblemBeforeFence::metadata = new MetaClass
    ("problem","before fence");
  ProblemBeforeCurrent::metadata = new MetaClass
    ("problem","before current");
  ProblemCapacityUnderload::metadata = new MetaClass
    ("problem","underload");
  ProblemCapacityOverload::metadata = new MetaClass
    ("problem","overload");

  // Register new types in Python
  int nok = 0;
  nok += PythonPlan::initialize(PythonInterpreter::getModule());
  nok += PythonBuffer::initialize(PythonInterpreter::getModule());
  nok += PythonBufferDefault::initialize(PythonInterpreter::getModule());
  nok += PythonBufferInfinite::initialize(PythonInterpreter::getModule());
  nok += PythonBufferProcure::initialize(PythonInterpreter::getModule());
  nok += PythonBufferIterator::initialize(PythonInterpreter::getModule());
  nok += PythonCalendar::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarIterator::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarBucket::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarBucketIterator::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarBool::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarVoid::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarDouble::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarString::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarInt::initialize(PythonInterpreter::getModule());
  nok += PythonCalendarOperation::initialize(PythonInterpreter::getModule());
  nok += PythonCustomer::initialize(PythonInterpreter::getModule());
  nok += PythonCustomerDefault::initialize(PythonInterpreter::getModule());
  nok += PythonCustomerIterator::initialize(PythonInterpreter::getModule());
  nok += PythonDemand::initialize(PythonInterpreter::getModule());
  nok += PythonDemandIterator::initialize(PythonInterpreter::getModule());
  nok += PythonDemandDefault::initialize(PythonInterpreter::getModule());
  nok += PythonDemandPlanIterator::initialize(PythonInterpreter::getModule());
  nok += PythonPeggingIterator::initialize(PythonInterpreter::getModule());
  nok += PythonFlow::initialize(PythonInterpreter::getModule());
  nok += PythonFlowIterator::initialize(PythonInterpreter::getModule());
  nok += PythonFlowPlan::initialize(PythonInterpreter::getModule());
  nok += PythonFlowPlanIterator::initialize(PythonInterpreter::getModule());
  nok += PythonItem::initialize(PythonInterpreter::getModule());
  nok += PythonItemDefault::initialize(PythonInterpreter::getModule());
  nok += PythonItemIterator::initialize(PythonInterpreter::getModule());
  nok += PythonLoad::initialize(PythonInterpreter::getModule());
  nok += PythonLoadIterator::initialize(PythonInterpreter::getModule());
  nok += PythonLoadPlan::initialize(PythonInterpreter::getModule());
  nok += PythonLoadPlanIterator::initialize(PythonInterpreter::getModule());
  nok += PythonLocation::initialize(PythonInterpreter::getModule());
  nok += PythonLocationDefault::initialize(PythonInterpreter::getModule());
  nok += PythonLocationIterator::initialize(PythonInterpreter::getModule());
  nok += PythonOperation::initialize(PythonInterpreter::getModule());
  nok += PythonOperationAlternate::initialize(PythonInterpreter::getModule());
  nok += PythonOperationFixedTime::initialize(PythonInterpreter::getModule());
  nok += PythonOperationTimePer::initialize(PythonInterpreter::getModule());
  nok += PythonOperationRouting::initialize(PythonInterpreter::getModule());
  nok += PythonOperationIterator::initialize(PythonInterpreter::getModule());
  nok += PythonOperationPlan::initialize(PythonInterpreter::getModule());
  nok += PythonOperationPlanIterator::initialize(PythonInterpreter::getModule());
  nok += PythonProblem::initialize(PythonInterpreter::getModule());
  nok += PythonProblemIterator::initialize(PythonInterpreter::getModule());
  nok += PythonResource::initialize(PythonInterpreter::getModule());
  nok += PythonResourceDefault::initialize(PythonInterpreter::getModule());
  nok += PythonResourceInfinite::initialize(PythonInterpreter::getModule());
  nok += PythonResourceIterator::initialize(PythonInterpreter::getModule());
  nok += PythonSolver::initialize(PythonInterpreter::getModule());
  nok += PythonSolverIterator::initialize(PythonInterpreter::getModule());
  if (nok)
    throw RuntimeException("Error registering new Python types");

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
    "buffers", PythonBufferIterator::create, METH_NOARGS,
    "Returns an iterator over the buffers.");
  PythonInterpreter::registerGlobalMethod(
    "locations", PythonLocationIterator::create, METH_NOARGS,
    "Returns an iterator over the locations.");
  PythonInterpreter::registerGlobalMethod(
    "customers", PythonCustomerIterator::create, METH_NOARGS,
    "Returns an iterator over the customer.");
  PythonInterpreter::registerGlobalMethod(
    "items", PythonItemIterator::create, METH_NOARGS,
    "Returns an iterator over the items.");
  PythonInterpreter::registerGlobalMethod(
    "calendars", PythonCalendarIterator::create, METH_NOARGS,
    "Returns an iterator over the calendars.");
  PythonInterpreter::registerGlobalMethod(
    "demands", PythonDemandIterator::create, METH_NOARGS,
    "Returns an iterator over the demands.");
  PythonInterpreter::registerGlobalMethod(
    "resources", PythonResourceIterator::create, METH_NOARGS,
    "Returns an iterator over the resources.");
  PythonInterpreter::registerGlobalMethod(
    "operations", PythonOperationIterator::create, METH_NOARGS,
    "Returns an iterator over the operations.");
  PythonInterpreter::registerGlobalMethod(
    "operationplans", PythonOperationPlanIterator::create, METH_NOARGS,
    "Returns an iterator over the operationplans.");
  PythonInterpreter::registerGlobalMethod(
    "problems", PythonProblemIterator::create, METH_NOARGS,
    "Returns an iterator over the problems.");
  PythonInterpreter::registerGlobalMethod(
    "solvers", PythonSolverIterator::create, METH_NOARGS,
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
