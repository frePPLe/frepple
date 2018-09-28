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
#include "frepple/model.h"

namespace frepple
{

//
// READ XML INPUT FILE
//


PyObject* readXMLfile(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *filename = nullptr;
  int validate(1), validate_only(0);
  PyObject *userexit = nullptr;
  int ok = PyArg_ParseTuple(args, "|siiO:readXMLfile",
    &filename, &validate, &validate_only, &userexit);
  if (!ok) return nullptr;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    if (!filename)
    {
      // Read from standard input
      xercesc::StdInInputSource in;
      XMLInput p;
      if (userexit) p.setUserExit(userexit);
      if (validate_only!=0)
        // When no root object is passed, only the input validation happens
        p.parse(in, nullptr, true);
      else
        p.parse(in, &Plan::instance(), validate!=0);
    }
    else
    {
      XMLInputFile p(filename);
      if (userexit) p.setUserExit(userexit);
      if (validate_only!=0)
        // Read and validate a file
        p.parse(nullptr, true);
      else
        // Read, execute and optionally validate a file
        p.parse(&Plan::instance(),validate!=0);
    }
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


//
// READ XML INPUT STRING
//


PyObject* readXMLdata(PyObject *self, PyObject *args)
{
  // Pick up arguments
  char *data;
  int validate(1), validate_only(0);
  PyObject *userexit = nullptr;
  int ok = PyArg_ParseTuple(args, "s|iiO:readXMLdata",
    &data, &validate, &validate_only, &userexit);
  if (!ok) return nullptr;

  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS

  // Execute and catch exceptions
  try
  {
    if (!data) throw DataException("No input data");
    XMLInputString p(data);
    if (userexit) p.setUserExit(userexit);
    if (validate_only!=0)
      p.parse(nullptr, true);
    else
      p.parse(&Plan::instance(), validate!=0);
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");  // Safer than using Py_None, which is not portable across compilers
}


//
// SAVE MODEL TO XML
//


PyObject* saveXMLfile(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *filename;
  char *content = nullptr;
  int ok = PyArg_ParseTuple(args, "s|s:saveXMLfile", &filename, &content);
  if (!ok) return nullptr;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    XMLSerializerFile o(filename);
    if (content)
    {
      if (!strcmp(content, "BASE"))
        o.setContentType(BASE);
      else if (!strcmp(content, "PLAN"))
        o.setContentType(PLAN);
      else if (!strcmp(content, "DETAIL"))
        o.setContentType(DETAIL);
      else
        throw DataException("Invalid content type '" + string(content) + "'");
    }
    o.writeElementWithHeader(Tags::plan, &Plan::instance());
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


//
// SAVE PLAN SUMMARY TO TEXT FILE
//


PyObject* savePlan(PyObject* self, PyObject* args)
{
  // Pick up arguments
  const char *filename = "plan.out";
  int ok = PyArg_ParseTuple(args, "s:saveplan", &filename);
  if (!ok) return nullptr;

  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS

  // Execute and catch exceptions
  ofstream textoutput;
  try
  {
    // Open the output file
    textoutput.open(filename, ios::out);

    // Write the buffer summary
    for (Buffer::iterator gbuf = Buffer::begin();
        gbuf != Buffer::end(); ++gbuf)
    {
      if (gbuf->getHidden())
        continue;
      for (auto oo=gbuf->getFlowPlans().begin(); oo!=gbuf->getFlowPlans().end(); ++oo)
        if (oo->getEventType() == 1 && oo->getQuantity() != 0.0)
        {
          textoutput << "BUFFER\t" << *gbuf << '\t'
              << oo->getDate() << '\t'
              << oo->getQuantity() << '\t'
              << (round(oo->getOnhand() * 1000) / 1000) << endl;
        }
    }

    // Write the demand summary
    for (Demand::iterator gdem = Demand::begin();
        gdem != Demand::end(); ++gdem)
    {
      const Demand::OperationPlanList &deli = gdem->getDelivery();
      for (auto pp = deli.begin(); pp != deli.end(); ++pp)
        textoutput << "DEMAND\t" << (*gdem) << '\t'
            << (*pp)->getEnd() << '\t'
            << (*pp)->getQuantity() << endl;
    }

    // Write the resource summary
    for (Resource::iterator gres = Resource::begin();
        gres != Resource::end(); ++gres)
    {
      if (gres->getHidden())
        continue;
      for (auto qq=gres->getLoadPlans().begin(); qq!=gres->getLoadPlans().end(); ++qq)
        if (qq->getEventType() == 1 && qq->getQuantity() != 0.0)
        {
          textoutput << "RESOURCE\t" << *gres << '\t'
              << qq->getDate() << '\t'
              << qq->getQuantity() << '\t'
              << (round(qq->getOnhand() * 1000) / 1000) << endl;
        }
    }

    // Write the operationplan summary.
    for (OperationPlan::iterator rr = OperationPlan::begin();
        rr != OperationPlan::end(); ++rr)
    {
      // TODO if-condition here isn't very clean and generic
      if (rr->getOperation()->getHidden()
        && rr->getOperation()->getType() != *OperationItemSupplier::metadata
        && rr->getOperation()->getType() != *OperationItemDistribution::metadata)
          continue;
      textoutput << "OPERATION\t" << rr->getOperation() << '\t'
        << rr->getStart() << '\t'
        << rr->getEnd() << '\t'
        << rr->getQuantity();
      if (rr->getProposed())
        textoutput << endl;
      else if (rr->getConfirmed())
        textoutput << "\tconfirmed" << endl;
      else if (rr->getApproved())
        textoutput << "\tapproved" << endl;
      else
        throw LogicException("Unknown operationplan status");
    }

    // Write the problem summary.
    Problem::iterator gprob;
    while (Problem *p = gprob.next())
    {
      textoutput << "PROBLEM\t" << p->getType().type << '\t'
          << p->getDescription() << '\t'
          << p->getDates() << endl;
    }

    // Write the constraint summary
    for (auto gdem = Demand::begin(); gdem != Demand::end(); ++gdem)
    {
      Problem::iterator i = gdem->getConstraints().begin();
      while (Problem *prob = i.next())
      {
        textoutput << "DEMAND CONSTRAINT\t" << (*gdem) << '\t'
            << prob->getDescription() << '\t'
            << prob->getDates() << '\t' << endl;
      }
    }

    // Close the output file
    textoutput.close();
  }
  catch (...)
  {
    if (textoutput.is_open())
      textoutput.close();
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


//
// MOVE OPERATIONPLAN
//

CommandMoveOperationPlan::CommandMoveOperationPlan(OperationPlan* o) : opplan(o), state(o)
{
  if (!o)
    return;

  // Construct a subcommand for all suboperationplans
  for (OperationPlan::iterator x(o); x != o->end(); ++x)
  {
    CommandMoveOperationPlan *n = new CommandMoveOperationPlan(&*x);
    n->owner = this;
    if (firstCommand)
    {
      n->next = firstCommand;
      firstCommand->prev = n;
    }
    firstCommand = n;
  }
}


CommandMoveOperationPlan::CommandMoveOperationPlan
(OperationPlan* o, Date newstart, Date newend, double newQty)
  : opplan(o), state(o), firstCommand(nullptr)
{
  if (!opplan)
    return;

  // Update the settings
  assert(opplan->getOperation());
  opplan->getOperation()->setOperationPlanParameters(
    opplan, newQty == -1.0 ? opplan->getQuantity() : newQty, 
    newstart, newend, true, true, false
  );

  // Construct a subcommand for all suboperationplans
  for (OperationPlan::iterator x(o); x != o->end(); ++x)
  {
    CommandMoveOperationPlan *n = new CommandMoveOperationPlan(&*x);
    n->owner = this;
    if (firstCommand)
    {
      n->next = firstCommand;
      firstCommand->prev = n;
    }
    firstCommand = n;
  }
}


void CommandMoveOperationPlan::restore(bool del)
{
  // Restore all suboperationplans and (optionally) delete the subcommands
  for (Command *c = firstCommand; c; )
  {
    CommandMoveOperationPlan *tmp = static_cast<CommandMoveOperationPlan*>(c);
    tmp->restore(del);
    c = c->next;
    if (del)
      delete tmp;
  }

  // Restore the original dates
  if (!opplan)
    return;
  opplan->restore(state);
}


//
// DELETE OPERATIONPLAN
//

CommandDeleteOperationPlan::CommandDeleteOperationPlan(OperationPlan* o) : opplan(o)
{
  // Validate input
  if (!o)
    return;

  // Avoid deleting locked operationplans
  if (!o->getProposed())
  {
    opplan = nullptr;
    throw DataException("Can't delete a locked operationplan");
  }

  // Deletion of all suboperationplans in this 
  stack<OperationPlan*> to_delete;
  to_delete.push(opplan->getTopOwner());
  while (!to_delete.empty())
  {
    // Pick up the top of the stack
    auto tmp = to_delete.top();
    to_delete.pop();

    // Delete all flowplans and loadplans, and unregister from operationplan list
    tmp->deleteFlowLoads();
    tmp->removeFromOperationplanList();
    if (tmp->getDemand())
      tmp->getDemand()->removeDelivery(opplan);

    // Push child operationplans on the stack
    OperationPlan::iterator x(tmp);
    while (OperationPlan* i = x.next())
      to_delete.push(i);
  }
}


//
// DELETE MODEL
//


PyObject* eraseModel(PyObject* self, PyObject* args)
{
  // Pick up arguments
  PyObject *obj = nullptr;
  int ok = PyArg_ParseTuple(args, "|O:erase", &obj);
  if (!ok) return nullptr;

  // Validate the argument
  bool deleteStaticModel = false;
  if (obj) deleteStaticModel = PythonData(obj).getBool();

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try
  {
    if (deleteStaticModel)
    {
      // Delete all entities.
      // The order is chosen to minimize the work of the individual destructors.
      // E.g. the destructor of the item class recurses over all demands and
      // all buffers. It is much faster if there are none already.
      Operation::clear();
      Demand::clear();
      Buffer::clear();
      Resource::clear();
      SetupMatrix::clear();
      Location::clear();
      Customer::clear();
      Calendar::clear();
      Supplier::clear();
      Item::clear();
      Plan::instance().setName("");
      Plan::instance().setDescription("");
    }
    else
    {
      // Delete the operationplans only
      for (Operation::iterator gop = Operation::begin();
          gop != Operation::end(); ++gop)
        gop->deleteOperationPlans();
    }
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


//
// PRINT MODEL SIZE
//


PyObject* printModelSize(PyObject* self, PyObject* args)
{
  // Free Python interpreter for other threads
  Py_BEGIN_ALLOW_THREADS

  // Execute and catch exceptions
  try
  {
    size_t count, memsize;

    // Intro
    logger << endl << "Size information of frePPLe " << PACKAGE_VERSION
      << " (" << __DATE__ << ")" << endl << endl;

    // Print loaded modules
    Environment::printModules();

    // Print the number of clusters
    logger << "Clusters: " << HasLevel::getNumberOfClusters() << endl << endl;

    // Header for memory size
    logger << "Memory usage:" << endl;
    logger << "Model                 \tCount\tMemory" << endl;
    logger << "-----                 \t-----\t------" << endl;

    // Plan
    size_t total = Plan::instance().getSize();
    logger << "Plan                  \t1\t"<< Plan::instance().getSize() << endl;

    // Locations
    memsize = 0;
    size_t countItemDistributions(0), memItemDistributions(0);
    for (Location::iterator l = Location::begin(); l != Location::end(); ++l)
    {
      memsize += l->getSize();
      for (Location::distributionlist::const_iterator rs = l->getDistributions().begin();
        rs != l->getDistributions().end(); ++rs)
      {
        ++countItemDistributions;
        memItemDistributions += rs->getSize();
      }
    }
    logger << "Location              \t" << Location::size() << "\t" << memsize << endl;
    total += memsize;

    // Customers
    memsize = 0;
    for (Customer::iterator c = Customer::begin(); c != Customer::end(); ++c)
      memsize += c->getSize();
    logger << "Customer              \t" << Customer::size() << "\t" << memsize << endl;
    total += memsize;

    // Suppliers
    memsize = 0;
    for (Supplier::iterator c = Supplier::begin(); c != Supplier::end(); ++c)
      memsize += c->getSize();
    logger << "Supplier              \t" << Supplier::size() << "\t" << memsize << endl;
    total += memsize;

    // Buffers
    memsize = 0;
    for (Buffer::iterator b = Buffer::begin(); b != Buffer::end(); ++b)
      memsize += b->getSize();
    logger << "Buffer                \t" << Buffer::size() << "\t" << memsize << endl;
    total += memsize;

    // Setup matrices
    memsize = 0;
    size_t countSetupRules(0), memSetupRules(0);
    for (SetupMatrix::iterator s = SetupMatrix::begin(); s != SetupMatrix::end(); ++s)
    {
      memsize += s->getSize();
      SetupMatrixRule::iterator iter = s->getRules();
      while (SetupMatrixRule *sr = iter.next())
      {
        ++countSetupRules;
        memSetupRules += sr->getSize();
      }
    }
    logger << "Setup matrix          \t" << SetupMatrix::size() << "\t" << memsize << endl;
    logger << "Setup matrix rules    \t" << countSetupRules << "\t" << memSetupRules << endl;
    total += memsize;
    total += memSetupRules;

    // Resources
    memsize = 0;
    for (Resource::iterator r = Resource::begin(); r != Resource::end(); ++r)
      memsize += r->getSize();
    logger << "Resource              \t" << Resource::size() << "\t" << memsize << endl;
    total += memsize;

    // Skills and resourceskills
    size_t countResourceSkills(0), memResourceSkills(0);
    memsize = 0;
    for (Skill::iterator sk = Skill::begin(); sk != Skill::end(); ++sk)
    {
      memsize += sk->getSize();
      Skill::resourcelist::const_iterator iter = sk->getResources();
      while(ResourceSkill *r = iter.next())
      {
        ++countResourceSkills;
        memResourceSkills += r->getSize();
      }
    }
    logger << "Skill                 \t" << Skill::size() << "\t" << memsize << endl;
    logger << "Resource skill        \t" << countResourceSkills << "\t" << memResourceSkills << endl;
    total += memsize;
    total += memResourceSkills;

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
    logger << "Operation             \t" << Operation::size() << "\t" << memsize << endl;
    logger << "Operation material    \t" << countFlows << "\t" << memFlows  << endl;
    logger << "operation resource    \t" << countLoads << "\t" << memLoads  << endl;
    total += memsize + memFlows + memLoads;

    // Calendars and calendar buckets
    memsize = 0;
    size_t countBuckets(0), memBuckets(0);
    for (Calendar::iterator cl = Calendar::begin(); cl != Calendar::end(); ++cl)
    {
      memsize += cl->getSize();
      for (auto bckt = cl->getBuckets(); bckt != CalendarBucket::iterator::end(); ++bckt)
      {
        ++countBuckets;
        memBuckets += bckt->getSize();
      }
    }
    logger << "Calendar              \t" << Calendar::size() << "\t" << memsize << endl;
    total += memsize;
    logger << "Calendar buckets      \t" << countBuckets << "\t" << memBuckets << endl;
    total += memBuckets;

    // Items
    memsize = 0;
    size_t countItemSuppliers(0), memItemSuppliers(0);
    for (Item::iterator i = Item::begin(); i != Item::end(); ++i)
    {
      memsize += i->getSize();
      for (Item::supplierlist::const_iterator rs = i->getSuppliers().begin();
        rs != i->getSuppliers().end(); ++rs)
      {
        ++countItemSuppliers;
        memItemSuppliers += rs->getSize();
      }
    }
    logger << "Item                  \t" << Item::size() << "\t" << memsize  << endl;
    logger << "Item suppliers        \t" << countItemSuppliers << "\t" << memItemSuppliers << endl;
    logger << "Item distributions    \t" << countItemDistributions << "\t" << memItemDistributions << endl;
    total += memsize + memItemSuppliers + memItemDistributions;

    // Demands
    memsize = 0;
    size_t c_count = 0, c_memsize = 0;
    for (Demand::iterator dm = Demand::begin(); dm != Demand::end(); ++dm)
    {
      memsize += dm->getSize();
      Problem::iterator cstrnt_iter(dm->getConstraints().begin());
      while (Problem *cstrnt = cstrnt_iter.next())
      {
        ++c_count;
        c_memsize += cstrnt->getSize();
      }
    }
    logger << "Demand                \t" << Demand::size() << "\t" << memsize  << endl;
    logger << "Constraints           \t" << c_count << "\t" << c_memsize  << endl;
    total += memsize + c_memsize;

    // Operationplans
    size_t countloadplans(0), countflowplans(0);
    memsize = count = 0;
    for (OperationPlan::iterator j = OperationPlan::begin();
        j!=OperationPlan::end(); ++j)
    {
      ++count;
      memsize += j->getSize();
      countloadplans += j->sizeLoadPlans();
      countflowplans += j->sizeFlowPlans();
    }
    total += memsize;
    logger << "OperationPlan         \t" << count << "\t" << memsize << endl;

    // Flowplans
    memsize = countflowplans * sizeof(FlowPlan);
    total +=  memsize;
    logger << "OperationPlan material\t" << countflowplans << "\t" << memsize << endl;

    // Loadplans
    memsize = countloadplans * sizeof(LoadPlan);
    total +=  memsize;
    logger << "OperationPlan resource\t" << countloadplans << "\t" << memsize << endl;

    // Problems
    memsize = count = 0;
    Problem::iterator piter;
    while (Problem *pr = piter.next())
    {
      ++count;
      memsize += pr->getSize();
    }
    total += memsize;
    logger << "Problem               \t" << count << "\t" << memsize << endl;

    // Shared string pool
    auto tmp = PooledString::getSize();
    logger << "String pool           \t" << tmp.first << "\t" << tmp.second << endl;

    // TOTAL
    logger << "Total                 \t\t" << total << endl << endl;
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return nullptr;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}

} // end namespace
