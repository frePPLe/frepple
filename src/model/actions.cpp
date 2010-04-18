/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2010 by Johan De Taeye                                    *
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

namespace frepple
{

//
// READ XML INPUT FILE
//

DECLARE_EXPORT void CommandReadXMLFile::execute()
{
  // Message
  if (getVerbose())
    logger << "Started reading model from file '" << filename
    << "' at " << Date::now() << endl;
  Timer t;

  // Note: Reading the data files can throw exceptions...
  if (filename.empty())
  {
    // Read from standard input
    xercesc::StdInInputSource in;
    if (validate_only)
      // When no root object is passed, only the input validation happens
      XMLInput().parse(in, NULL, true);
    else
      XMLInput().parse(in, &Plan::instance(), validate);
  }
  else if (validate_only)
    // Read and validate a file
    XMLInputFile(filename).parse(NULL, true);
  else
    // Read, execute and optionally validate a file
    XMLInputFile(filename).parse(&Plan::instance(),validate);

  // Message
  if (getVerbose())
    logger << "Finished reading model at " << Date::now()  << " : " << t << endl;
}


DECLARE_EXPORT PyObject* CommandReadXMLFile::executePython(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *data;
  int i1(1), i2(0);
  int ok = PyArg_ParseTuple(args, "s|ii:readXMLfile", &data, &i1, &i2);
  if (!ok) return NULL;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try {
    CommandReadXMLFile(data, i1!=0, i2!=0).execute();
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


//
// READ XML INPUT STRING
//

DECLARE_EXPORT void CommandReadXMLString::execute()
{
  // Message
  if (getVerbose())
    logger << "Started reading model from string at " << Date::now() << endl;
  Timer t;

  // Note: Reading the data can throw exceptions...
  if (validate_only)
    XMLInputString(data).parse(NULL, true);
  else
    // Locking the plan assures a single read command is running at any time.
    XMLInputString(data).parse(&Plan::instance(), validate);

  // Message
  if (getVerbose())
    logger << "Finished reading model at " << Date::now()  << " : " << t << endl;
}


PyObject* CommandReadXMLString::executePython(PyObject *self, PyObject *args)
{
  // Pick up arguments
  char *data;
  int i1(1), i2(0);
  int ok = PyArg_ParseTuple(args, "s|ii:readXMLdata", &data, &i1, &i2);
  if (!ok) return NULL;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try {
    if (data) CommandReadXMLString(string(data), i1!=0, i2!=0).execute();
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");  // Safer than using Py_None, which is not
                             // portable across compilers
}


//
// SAVE MODEL TO XML
//

DECLARE_EXPORT void CommandSave::execute()
{
  // Message
  if (getVerbose())
    logger << "Start saving model to file '" << filename
    << "' at " << Date::now() << endl;
  Timer t;

  // Save the plan
  XMLOutputFile o(filename);
  if (!headerstart.empty()) o.setHeaderStart(headerstart);
  if (!headeratts.empty()) o.setHeaderAtts(headeratts);
  o.setContentType(content);
  o.writeElementWithHeader(Tags::tag_plan, &Plan::instance());

  // Message
  if (getVerbose())
    logger << "Finished saving " << o.countObjects()
    << " objects at " << Date::now() << " : " << t << endl;
}


PyObject* CommandSave::executePython(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *data;
  char *content = NULL;
  int ok = PyArg_ParseTuple(args, "s|s:save", &data, &content);
  if (!ok) return NULL;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try {
    CommandSave cmd(data);
    if (content)
    {
      if (!strcmp(content,"STANDARD"))
        cmd.setContent(XMLOutput::STANDARD);
      else if (!strcmp(content,"PLAN"))
        cmd.setContent(XMLOutput::PLAN);
      else if (!strcmp(content,"PLANDETAIL"))
        cmd.setContent(XMLOutput::PLANDETAIL);
      else
        throw DataException("Invalid content type '" + string(content) + "'");
    }
    cmd.execute();
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


//
// SAVE PLAN SUMMARY TO TEXT FILE
//

DECLARE_EXPORT void CommandSavePlan::execute()
{
  // Message
  if (getVerbose())
    logger << "Start saving plan to file '" << getFileName()
    << "' at " << Date::now() << endl;
  Timer t;

  // Output steam
  if (getFileName().empty())
    throw RuntimeException("No file specified for export");
  ofstream textoutput;

  // Open the file, write to it and close it. Catch exceptions all along...
  try
  {
    // Open the output file
    textoutput.open(getFileName().c_str(), ios::out);

    // Write the buffer summary
    for (Buffer::iterator gbuf = Buffer::begin();
        gbuf != Buffer::end(); ++gbuf)
    {
      if (!gbuf->getHidden())
        for (Buffer::flowplanlist::const_iterator
            oo=gbuf->getFlowPlans().begin();
            oo!=gbuf->getFlowPlans().end();
            ++oo)
          if (oo->getType() == 1 && oo->getQuantity() != 0.0)
          {
            textoutput << "BUFFER\t" << *gbuf << '\t'
            << oo->getDate() << '\t'
            << oo->getQuantity() << '\t'
            << oo->getOnhand() << endl;
          }
    }

    // Write the demand summary
    for (Demand::iterator gdem = Demand::begin();
        gdem != Demand::end(); ++gdem)
    {
      if (!gdem->getHidden())
      {
        for (Demand::OperationPlan_list::const_iterator
            pp = gdem->getDelivery().begin();
            pp != gdem->getDelivery().end();
            ++pp)
          textoutput << "DEMAND\t" << (*gdem) << '\t'
            << (*pp)->getDates().getEnd() << '\t'
            << (*pp)->getQuantity() << endl;
      }
    }

    // Write the resource summary
    for (Resource::iterator gres = Resource::begin();
        gres != Resource::end(); ++gres)
    {
      if (!gres->getHidden())
        for (Resource::loadplanlist::const_iterator
            qq=gres->getLoadPlans().begin();
            qq!=gres->getLoadPlans().end();
            ++qq)
          if (qq->getType() == 1 && qq->getQuantity() != 0.0)
          {
            textoutput << "RESOURCE\t" << *gres << '\t'
            << qq->getDate() << '\t'
            << qq->getQuantity() << '\t'
            << qq->getOnhand() << endl;
          }
    }

    // Write the operationplan summary.
    for (OperationPlan::iterator rr = OperationPlan::begin();
        rr != OperationPlan::end(); ++rr)
    {
      if (rr->getOperation()->getHidden()) continue;
      textoutput << "OPERATION\t" << rr->getOperation() << '\t'
      << rr->getDates().getStart() << '\t'
      << rr->getDates().getEnd() << '\t'
      << rr->getQuantity() << endl;
    }

    // Write the problem summary.
    for (Problem::const_iterator gprob = Problem::begin();
        gprob != Problem::end(); ++gprob)
    {
      textoutput << "PROBLEM\t" << gprob->getType().type << '\t'
      << gprob->getDescription() << '\t'
      << gprob->getDates() << endl;
    }

    // Write the constraint summary
    for (Demand::iterator gdem = Demand::begin();
        gdem != Demand::end(); ++gdem)
    {
      if (!gdem->getHidden())
      {
        for (Problem::const_iterator i = gdem->getConstraints().begin();
            i != gdem->getConstraints().end();
            ++i)
          textoutput << "DEMAND CONSTRAINT\t" << (*gdem) << '\t'
            << i->getDescription() << '\t'
            << i->getDates() << '\t' << endl;
      }
    }

    // Close the output file
    textoutput.close();
  }
  catch (exception& e)
  {
    textoutput.close();
    throw RuntimeException("Error writing to file '"
        + getFileName() + "':\n" + e.what());
  }
  catch (...)
  {
    textoutput.close();
    throw RuntimeException("Error writing to file '"
        + getFileName() + "'");
  }

  // Message
  if (getVerbose())
    logger << "Finished saving plan at " << Date::now() << " : " << t << endl;
}


PyObject* CommandSavePlan::executePython(PyObject* self, PyObject* args)
{
  // Pick up arguments
  char *data;
  int ok = PyArg_ParseTuple(args, "s:saveplan", &data);
  if (!ok) return NULL;

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try {
    CommandSavePlan(data).execute();
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}


//
// MOVE OPERATIONPLAN
//
               
DECLARE_EXPORT CommandMoveOperationPlan::CommandMoveOperationPlan
  (OperationPlan* o) : opplan(o), firstCommand(NULL)
{
  if (!o) 
  {
    originalqty = 0;
    return;
  }
  originalqty = opplan->getQuantity();
  originaldates = opplan->getDates();

  // Construct a subcommand for all suboperationplans
  for (OperationPlan::iterator x(o); x != o->end(); ++x)
    if (x->getOperation() != OperationSetup::setupoperation)
    {
      CommandMoveOperationPlan *n = new CommandMoveOperationPlan(o);
      n->owner = this;
      if (firstCommand)
      {
        n->next = firstCommand;
        firstCommand->prev = n;
      }
      firstCommand = n;
    }
}


DECLARE_EXPORT CommandMoveOperationPlan::CommandMoveOperationPlan
(OperationPlan* o, Date newstart, Date newend, double newQty) 
  : opplan(o), firstCommand(NULL)
{
  if (!opplan) return;

  // Store current settings
  originalqty = opplan->getQuantity();
  if (newQty == -1.0) newQty = originalqty;
  originaldates = opplan->getDates();

  // Update the settings
  assert(opplan->getOperation());
  opplan->getOperation()->setOperationPlanParameters(
    opplan, newQty, newstart, newend
  );

  // Construct a subcommand for all suboperationplans
  for (OperationPlan::iterator x(o); x != o->end(); ++x)
    if (x->getOperation() != OperationSetup::setupoperation)
    {
      CommandMoveOperationPlan *n = new CommandMoveOperationPlan(o);
      n->owner = this;
      if (firstCommand)
      {
        n->next = firstCommand;
        firstCommand->prev = n;
      }
      firstCommand = n;
    }
}


DECLARE_EXPORT void CommandMoveOperationPlan::restore(bool del)
{
  // Restore all suboperationplans and (optionally) delete the subcommands
  for (Command *c = firstCommand; c; )
  {
    CommandMoveOperationPlan *tmp = static_cast<CommandMoveOperationPlan*>(c);
    tmp->restore(del);
    c = c->next;
    if (del) delete tmp;
  }

  // Restore the original dates
  if (!opplan) return;
  opplan->getOperation()->setOperationPlanParameters(
    opplan, originalqty, originaldates.getStart(), originaldates.getEnd()
  );
}


//
// DELETE OPERATIONPLAN
//

DECLARE_EXPORT CommandDeleteOperationPlan::CommandDeleteOperationPlan
  (OperationPlan* o)
{
  // Validate input
  if (!o)
  {
    oper = NULL;
    return;
  }

  // Avoid deleting locked operationplans
  if (o->getLocked())
    throw DataException("Can't delete a locked operationplan");

  // Register the fields of the operationplan before deletion
  oper = o->getOperation();
  qty = o->getQuantity();
  dates = o->getDates();
  id = o->getIdentifier();
  dmd = o->getDemand();
  ow = &*(o->getOwner());

  // Delete the operationplan
  delete o;
}


DECLARE_EXPORT void CommandDeleteOperationPlan::undo()
{
  // Already executed, or never initialized completely
  if (!oper) return;

  // Recreate and register the operationplan.
  // Note that the recreated operationplan has the same field values as the
  // original one, but has a different memory address. Any pointers to the
  // original operationplan are now dangling.
  OperationPlan* opplan = oper->createOperationPlan(qty, dates.getStart(),
    dates.getEnd(), dmd, const_cast<OperationPlan*>(ow), id);
  if (opplan) opplan->instantiate();

  // Avoid undoing multiple times!
  oper = NULL;
}


//
// DELETE MODEL
//


DECLARE_EXPORT void CommandErase::execute()
{
  // Starting message
  if (getVerbose())
  {
    if (deleteStaticModel)
      logger << "Start model erase command at " << Date::now() << endl;
    else
      logger << "Start plan erase command at " << Date::now() << endl;
  }
  Timer t;

  if (deleteStaticModel)
  {
    // Delete all entities.
    // The order is chosen to minimize the work of the individual destructors.
    // E.g. the destructor of the item class recurses over all demands and
    // all buffers. It is much faster if there are none already.
    Demand::clear();
    Operation::clear();  
    Buffer::clear();     
    Resource::clear();
    SetupMatrix::clear();
    Location::clear();
    Customer::clear();
    Calendar::clear();
    Solver::clear();
    Item::clear();
    // The setup operation is a static singleton and should always be around
    OperationSetup::setupoperation = Operation::add(new OperationSetup("setup operation"));
  }
  else
    // Delete the operationplans only
    for (Operation::iterator gop = Operation::begin();
        gop != Operation::end(); ++gop)
      gop->deleteOperationPlans();

  // Ending message
  if (getVerbose())
    logger << "Finished erase command at " << Date::now()
    << " : " << t << endl;
}


PyObject* CommandErase::executePython(PyObject* self, PyObject* args)
{
  // Pick up arguments
  PyObject *obj = NULL;
  int ok = PyArg_ParseTuple(args, "|O:erase", &obj);
  if (!ok) return NULL;

  // Validate the argument
  bool staticalso = false;
  if (obj) staticalso = PythonObject(obj).getBool();

  // Execute and catch exceptions
  Py_BEGIN_ALLOW_THREADS   // Free Python interpreter for other threads
  try {
    CommandErase(staticalso).execute();
  }
  catch (...)
  {
    Py_BLOCK_THREADS;
    PythonType::evalException();
    return NULL;
  }
  Py_END_ALLOW_THREADS   // Reclaim Python interpreter
  return Py_BuildValue("");
}

} // end namespace
