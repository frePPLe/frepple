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

#define FREPPLE_CORE
#include "frepple/model.h"
#include <sys/stat.h>

namespace frepple
{

// Command metadata
DECLARE_EXPORT const MetaClass CommandPlanSize::metadata,
  CommandCreateOperationPlan::metadata,
  CommandDeleteOperationPlan::metadata,
  CommandMoveOperationPlan::metadata,
  CommandSolve::metadata,
  CommandReadXMLFile::metadata,
  CommandReadXMLString::metadata,
  CommandSave::metadata,
  CommandSavePlan::metadata,
  CommandErase::metadata;

// Solver metadata
DECLARE_EXPORT const MetaCategory Solver::metadata;

// Load metadata
DECLARE_EXPORT const MetaCategory Load::metadata;

// Location metadata
DECLARE_EXPORT const MetaCategory Location::metadata;
DECLARE_EXPORT const MetaClass LocationDefault::metadata;

// Buffer metadata
DECLARE_EXPORT const MetaCategory Buffer::metadata;
DECLARE_EXPORT const MetaClass BufferDefault::metadata,
  BufferInfinite::metadata,
  BufferProcure::metadata;

// Calendar metadata
DECLARE_EXPORT const MetaCategory Calendar::metadata;
DECLARE_EXPORT const MetaCategory Calendar::Bucket::metadata;
DECLARE_EXPORT const MetaClass CalendarVoid::metadata,
  CalendarFloat::metadata,
  CalendarInt::metadata,
  CalendarBool::metadata,
  CalendarString::metadata,
  CalendarOperation::metadata;

// Flow metadata
DECLARE_EXPORT const MetaCategory Flow::metadata;
DECLARE_EXPORT const MetaClass FlowStart::metadata,
  FlowEnd::metadata;

// Operation metadata
DECLARE_EXPORT const MetaCategory Operation::metadata;
DECLARE_EXPORT const MetaClass OperationFixedTime::metadata,
  OperationTimePer::metadata,
  OperationRouting::metadata,
  OperationAlternate::metadata,
  OperationEffective::metadata;

// OperationPlan metadata
DECLARE_EXPORT const MetaCategory OperationPlan::metadata;

// Resource metadats
DECLARE_EXPORT const MetaCategory Resource::metadata;
DECLARE_EXPORT const MetaClass ResourceDefault::metadata;
DECLARE_EXPORT const MetaClass ResourceInfinite::metadata;

// Item metadata
DECLARE_EXPORT const MetaCategory Item::metadata;
DECLARE_EXPORT const MetaClass ItemDefault::metadata;

// Customer metadata
DECLARE_EXPORT const MetaCategory Customer::metadata;
DECLARE_EXPORT const MetaClass CustomerDefault::metadata;

// Demand metadata
DECLARE_EXPORT const MetaCategory Demand::metadata;
DECLARE_EXPORT const MetaClass DemandDefault::metadata;

// Plan metadata
DECLARE_EXPORT const MetaCategory Plan::metadata;

// Problem metadata
DECLARE_EXPORT const MetaCategory Problem::metadata;
DECLARE_EXPORT const MetaClass ProblemMaterialExcess::metadata,
  ProblemMaterialShortage::metadata,
  ProblemExcess::metadata,
  ProblemShort::metadata,
  ProblemEarly::metadata,
  ProblemLate::metadata,
  ProblemDemandNotPlanned::metadata,
  ProblemPlannedEarly::metadata,
  ProblemPlannedLate::metadata,
  ProblemPrecedence::metadata,
  ProblemBeforeFence::metadata,
  ProblemBeforeCurrent::metadata,
  ProblemCapacityUnderload::metadata,
  ProblemCapacityOverload::metadata;


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

  // Initialize the command metadata.
  CommandPlanSize::metadata.registerClass(
    "COMMAND",
    "COMMAND_SIZE",
    Object::createDefault<CommandPlanSize>);
  CommandCreateOperationPlan::metadata.registerClass(
    "COMMAND",
    "COMMAND_CREATE_OPPLAN"); // No factory method: cmd not created with xml
  CommandDeleteOperationPlan::metadata.registerClass(
    "COMMAND",
    "COMMAND_DELETE_OPPLAN"); // No factory method: cmd not created with xml
  CommandMoveOperationPlan::metadata.registerClass(
    "COMMAND",
    "COMMAND_MOVE_OPPLAN"); // No factory method: cmd not created with xml
  CommandSolve::metadata.registerClass(
    "COMMAND",
    "COMMAND_SOLVE",
    Object::createDefault<CommandSolve>);
  CommandReadXMLFile::metadata.registerClass(
    "COMMAND",
    "COMMAND_READXML",
    Object::createDefault<CommandReadXMLFile>);
  CommandReadXMLString::metadata.registerClass(
    "COMMAND",
    "COMMAND_READXMLSTRING",
    Object::createDefault<CommandReadXMLString>);
  CommandSave::metadata.registerClass(
    "COMMAND",
    "COMMAND_SAVE",
    Object::createDefault<CommandSave>);
  CommandSavePlan::metadata.registerClass(
    "COMMAND",
    "COMMAND_SAVEPLAN",
    Object::createDefault<CommandSavePlan>);
  CommandErase::metadata.registerClass(
    "COMMAND",
    "COMMAND_ERASE",
    Object::createDefault<CommandErase>);

  // Initialize the plan metadata.
  Plan::metadata.registerCategory("PLAN");

  // Initialize the solver metadata.
  Solver::metadata.registerCategory
    ("SOLVER", "SOLVERS", Solver::reader, Solver::writer);

  // Initialize the location metadata.
  Location::metadata.registerCategory
    ("LOCATION", "LOCATIONS", Location::reader, Location::writer);
  LocationDefault::metadata.registerClass("LOCATION", "LOCATION",
    Object::createString<LocationDefault>, true);

  // Initialize the customer metadata.
  Customer::metadata.registerCategory
    ("CUSTOMER", "CUSTOMERS", Customer::reader, Customer::writer);
  CustomerDefault::metadata.registerClass(
    "CUSTOMER",
    "CUSTOMER",
    Object::createString<CustomerDefault>, true);

  // Initialize the calendar metadata.
  Calendar::Bucket::metadata.registerCategory("BUCKET", "BUCKETS");
  Calendar::metadata.registerCategory
    ("CALENDAR", "CALENDARS", Calendar::reader, Calendar::writer);
  CalendarVoid::metadata.registerClass(
    "CALENDAR",
    "CALENDAR_VOID",
    Object::createString<CalendarVoid>);
  CalendarFloat::metadata.registerClass(
    "CALENDAR",
    "CALENDAR_FLOAT",
    Object::createString<CalendarFloat>, true);
  CalendarInt::metadata.registerClass(
    "CALENDAR",
    "CALENDAR_INTEGER",
    Object::createString<CalendarInt>);
  CalendarBool::metadata.registerClass(
    "CALENDAR",
    "CALENDAR_BOOLEAN",
    Object::createString<CalendarBool>);
  CalendarString::metadata.registerClass(
    "CALENDAR",
    "CALENDAR_STRING",
    Object::createString<CalendarString>);
  CalendarOperation::metadata.registerClass(
    "CALENDAR",
    "CALENDAR_OPERATION",
    Object::createString<CalendarOperation>);

  // Initialize the operation metadata.
  Operation::metadata.registerCategory
    ("OPERATION", "OPERATIONS", Operation::reader, Operation::writer);
  OperationFixedTime::metadata.registerClass(
    "OPERATION",
    "OPERATION_FIXED_TIME",
    Object::createString<OperationFixedTime>, true);
  OperationTimePer::metadata.registerClass(
    "OPERATION",
    "OPERATION_TIME_PER",
    Object::createString<OperationTimePer>);
  OperationRouting::metadata.registerClass(
    "OPERATION",
    "OPERATION_ROUTING",
    Object::createString<OperationRouting>);
  OperationAlternate::metadata.registerClass(
    "OPERATION",
    "OPERATION_ALTERNATE",
    Object::createString<OperationAlternate>);
  OperationEffective::metadata.registerClass(
    "OPERATION",
    "OPERATION_EFFECTIVE",
    Object::createString<OperationEffective>);

  // Initialize the item metadata.
  Item::metadata.registerCategory
    ("ITEM", "ITEMS", Item::reader, Item::writer);
  ItemDefault::metadata.registerClass("ITEM", "ITEM",
    Object::createString<ItemDefault>, true);

  // Initialize the buffer metadata.
  Buffer::metadata.registerCategory
    ("BUFFER", "BUFFERS", Buffer::reader, Buffer::writer);
  BufferDefault::metadata.registerClass(
    "BUFFER",
    "BUFFER",
    Object::createString<BufferDefault>, true);
  BufferInfinite::metadata.registerClass(
    "BUFFER",
    "BUFFER_INFINITE",
    Object::createString<BufferInfinite>);
  BufferProcure::metadata.registerClass(
    "BUFFER",
    "BUFFER_PROCURE",
    Object::createString<BufferProcure>);

  // Initialize the demand metadata.
  Demand::metadata.registerCategory
    ("DEMAND", "DEMANDS", Demand::reader, Demand::writer);
  DemandDefault::metadata.registerClass(
    "DEMAND",
    "DEMAND",
    Object::createString<DemandDefault>, true);

  // Initialize the resource metadata.
  Resource::metadata.registerCategory
    ("RESOURCE", "RESOURCES", Resource::reader, Resource::writer);
  ResourceDefault::metadata.registerClass(
    "RESOURCE",
    "RESOURCE",
    Object::createString<ResourceDefault>,
    true);
  ResourceInfinite::metadata.registerClass(
    "RESOURCE",
    "RESOURCE_INFINITE",
    Object::createString<ResourceInfinite>);

  // Initialize the load metadata.
  Load::metadata.registerCategory
    ("LOAD", "LOADS", MetaCategory::ControllerDefault, NULL);
  Load::metadata.registerClass
    ("LOAD", "LOAD", Object::createDefault<Load>, true);

  // Initialize the flow metadata.
  Flow::metadata.registerCategory
    ("FLOW", "FLOWS", MetaCategory::ControllerDefault);
  FlowStart::metadata.registerClass(
    "FLOW",
    "FLOW_START",
    Object::createDefault<FlowStart>, true);
  FlowEnd::metadata.registerClass(
    "FLOW",
    "FLOW_END",
    Object::createDefault<FlowEnd>);

  // Initialize the operationplan metadata.
  OperationPlan::metadata.registerCategory("OPERATION_PLAN", "OPERATION_PLANS",
    OperationPlan::createOperationPlan, OperationPlan::writer);

  // Initialize the problem metadata.
  Problem::metadata.registerCategory
    ("PROBLEM", "PROBLEMS", NULL, Problem::writer);
  ProblemMaterialExcess::metadata.registerClass
    ("PROBLEM","material excess");
  ProblemMaterialShortage::metadata.registerClass
    ("PROBLEM","material shortage");
  ProblemExcess::metadata.registerClass
    ("PROBLEM","excess");
  ProblemShort::metadata.registerClass
    ("PROBLEM","short");
  ProblemEarly::metadata.registerClass
    ("PROBLEM","early");
  ProblemLate::metadata.registerClass
    ("PROBLEM","late");
  ProblemDemandNotPlanned::metadata.registerClass
    ("PROBLEM","unplanned");
  ProblemPlannedEarly::metadata.registerClass
    ("PROBLEM","planned early");
  ProblemPlannedLate::metadata.registerClass
    ("PROBLEM","planned late");
  ProblemPrecedence::metadata.registerClass
    ("PROBLEM","precedence");
  ProblemBeforeFence::metadata.registerClass
    ("PROBLEM","before fence");
  ProblemBeforeCurrent::metadata.registerClass
    ("PROBLEM","before current");
  ProblemCapacityUnderload::metadata.registerClass
    ("PROBLEM","underload");
  ProblemCapacityOverload::metadata.registerClass
    ("PROBLEM","overload");

  // Verify the existence of the schema file
  string env = Environment::getHomeDirectory();
  env += "frepple.xsd";
  struct stat stat_p;
  if (stat(env.c_str(), &stat_p))
    // Can't locate
    throw RuntimeException("Can't find schema file 'frepple.xsd'");
  else if (!(stat_p.st_mode & S_IREAD))
    // Can't read
    throw RuntimeException("Can't read schema file 'frepple.xsd'");

  // Make sure the exit function is called
#ifdef HAVE_ATEXIT
  atexit(finalize);
#endif
}


DECLARE_EXPORT void CommandPlanSize::execute()
{
  size_t count, memsize;

  // Log
  if (getVerbose())
    logger << "Start size report at " << Date::now() << endl;
  Timer t;

  // Intro
  logger << endl << "Size information of Frepple " << PACKAGE_VERSION
  << " (" << __DATE__ << ")" << endl << endl;

  // Print current locale
  logger << "Locale: " << setlocale(LC_ALL,NULL) << endl << endl;

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

  // Operation_plans
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
    memsize += sizeof(**pr);
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
