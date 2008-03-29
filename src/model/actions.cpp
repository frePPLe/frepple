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

namespace frepple
{

template<class Solver> DECLARE_EXPORT Tree HasName<Solver>::st;

//
// SOLVE
//

DECLARE_EXPORT void CommandSolve::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_solver))
    pIn.readto( Solver::reader(Solver::metadata,pIn) );
}


DECLARE_EXPORT void CommandSolve::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_solver))
  {
    Solver *s = dynamic_cast<Solver*>(pIn.getPreviousObject());
    if (s) setSolver(s);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
    Command::endElement(pIn, pElement);
}


DECLARE_EXPORT void CommandSolve::execute()
{
  // Make sure the solver field is specified
  if (!sol) throw RuntimeException("Solve command with unspecified solver");

  // Start message
  if (getVerbose())
    logger << "Started running the solver '" << sol->getName()
    << "' at " << Date::now() << endl;
  Timer t;

  // Running the solver now
  sol->solve();

  // Ending message
  if (getVerbose())
    logger << "Finished running the solver '" << sol->getName()
    << "' at " << Date::now()  << " : " << t << endl;
}


DECLARE_EXPORT void Solver::writeElement
(XMLOutput *o, const XMLtag &tag, mode m) const
{
  // The subclass should have written its own header
  assert(m == NOHEADER);

  // Fields
  if (loglevel) o->writeElement(Tags::tag_loglevel, loglevel);

  // End object
  o->EndObject(tag);
}


DECLARE_EXPORT void Solver::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_loglevel))
  {
    int i = pElement.getInt();
    if (i<0 || i>USHRT_MAX)
      throw DataException("Invalid log level" + pElement.getString());
    setLogLevel(i);
  }
}


//
// READ XML INPUT FILE
//

DECLARE_EXPORT void CommandReadXMLFile::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_filename))
    pElement >> filename;
  else if (pElement.isA(Tags::tag_validate))
    pElement >> validate;
  else
    Command::endElement(pIn, pElement);
}


DECLARE_EXPORT void CommandReadXMLFile::execute()
{
  // Message
  if (getVerbose())
    logger << "Started reading model from file '" << filename
    << "' at " << Date::now() << endl;
  Timer t;

  // Replace environment variables in the filename.
  Environment::resolveEnvironment(filename);

  // Note: Reading the data files can throw exceptions...
  if (filename.empty())
  {
    // Read from standard input
    StdInInputSource in;
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


//
// READ XML INPUT STRING
//

DECLARE_EXPORT void CommandReadXMLString::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_data))
    pElement >> data;
  else if (pElement.isA(Tags::tag_validate))
    pElement >> validate;
  else
    Command::endElement(pIn, pElement);
}


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


//
// SAVE MODEL TO XML
//

DECLARE_EXPORT void CommandSave::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_filename))
    pElement >> filename;
  else if (pElement.isA(Tags::tag_headerstart))
    pElement >> headerstart;
  else if (pElement.isA(Tags::tag_headeratts))
    pElement >> headeratts;
  else if (pElement.isA(Tags::tag_content))
  {
    string tmp;
    pElement >> tmp;
    if (tmp == "STANDARD") content = XMLOutput::STANDARD;
    else if (tmp == "PLAN") content = XMLOutput::PLAN;
    else if (tmp == "PLANDETAIL") content = XMLOutput::PLANDETAIL;
    else throw DataException("Invalid content type '" + tmp + "'");
  }
  else
    Command::endElement(pIn, pElement);
}


DECLARE_EXPORT void CommandSave::execute()
{
  // Message
  if (getVerbose())
    logger << "Start saving model to file '" << filename
    << "' at " << Date::now() << endl;
  Timer t;

  // Replace environment variables in the filename.
  Environment::resolveEnvironment(filename);

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


//
// SAVE PLAN SUMMARY TO TEXT FILE
//


DECLARE_EXPORT void CommandSavePlan::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_filename))
    pElement >> filename;
  else
    Command::endElement(pIn, pElement);
}


DECLARE_EXPORT void CommandSavePlan::execute()
{
  // Message
  if (getVerbose())
    logger << "Start saving plan to file '" << getFileName()
    << "' at " << Date::now() << endl;
  Timer t;

  // Replace environment variables in the filename.
  Environment::resolveEnvironment(filename);

  // Output steam
  if (getFileName().empty())
    throw RuntimeException("No file specified for export.");
  ofstream textoutput;

  // Open the file, write to it and close it. Catch exceptions all along...
  try
  {
    // Open the log file
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
        for (Demand::OperationPlan_list::const_iterator
            pp=gdem->getDelivery().begin();
            pp!=gdem->getDelivery().end();
            ++pp)
        {
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
      << gprob->getDateRange() << endl;
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


//
// MOVE OPERATIONPLAN
//

DECLARE_EXPORT CommandMoveOperationPlan::CommandMoveOperationPlan
(OperationPlan* o, Date newdate, bool pref_end, double newQty)
    : opplan(o), prefer_end(pref_end)
{
  if (!opplan) return;
  originalqty = opplan->getQuantity();
  if (newQty == -1.0) newQty = originalqty;
  originaldates = opplan->getDates();
  if (prefer_end)
    opplan->getOperation()->setOperationPlanParameters(
      opplan, newQty, Date::infinitePast, newdate, prefer_end
    );
  else
    opplan->getOperation()->setOperationPlanParameters(
      opplan, newQty, newdate, Date::infiniteFuture, prefer_end
    );
}


DECLARE_EXPORT void CommandMoveOperationPlan::undo()
{
  if (!opplan) return;
  opplan->getOperation()->setOperationPlanParameters(
    opplan, originalqty, originaldates.getStart(), originaldates.getEnd(), prefer_end
  );
  opplan = NULL;
}


DECLARE_EXPORT void CommandMoveOperationPlan::setDate(Date newdate)
{
  if (!opplan) return;
  if (prefer_end)
    opplan->getOperation()->setOperationPlanParameters(
      opplan, opplan->getQuantity(), Date::infinitePast, newdate, prefer_end
    );
  else
    opplan->getOperation()->setOperationPlanParameters(
      opplan, opplan->getQuantity(), newdate, Date::infiniteFuture, prefer_end
    );
}


DECLARE_EXPORT void CommandMoveOperationPlan::setQuantity(double newqty)
{
  if (!opplan) return;
  if (prefer_end)
    opplan->getOperation()->setOperationPlanParameters(
      opplan, newqty, opplan->getDates().getStart(), opplan->getDates().getEnd(), prefer_end
    );
  else
    opplan->getOperation()->setOperationPlanParameters(
      opplan, newqty, opplan->getDates().getStart(), opplan->getDates().getEnd(), prefer_end
    );
}


DECLARE_EXPORT string CommandMoveOperationPlan::getDescription() const
{
  ostringstream ch;
  ch << "updating operationplan ";
  if (opplan)
    ch << "of operation '" << opplan->getOperation()
    << "' with identifier " << opplan->getIdentifier();
  else
    ch << "NULL";
  return ch.str();
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
    throw DataException("Can't delete a locked operationplan.");

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
  if (opplan) opplan->initialize();

  // Avoid undoing multiple times!
  oper = NULL;
}


DECLARE_EXPORT string CommandDeleteOperationPlan::getDescription() const
{
  ostringstream ch;
  ch << "deleting operationplan";
  if (oper) ch << " for operation '" << oper->getName() << "'";
  if (id) ch << " with identifier " << id;
  return ch.str();
}


//
// DELETE MODEL
//

DECLARE_EXPORT void CommandErase::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_mode))
  {
    string m = pElement.getString();
    if (m == "plan") deleteStaticModel = false;
    else if (m == "model") deleteStaticModel = true;
    else throw DataException("Unknown mode '" + m + "' for erase command");
  }
  else
    Command::endElement(pIn, pElement);
}


DECLARE_EXPORT void CommandErase::execute()
{
  // Starting message
  if (getVerbose())
    if (deleteStaticModel)
      logger << "Start model erase command at " << Date::now() << endl;
    else
      logger << "Start plan erase command at " << Date::now() << endl;
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
    Location::clear();
    Customer::clear();
    Calendar::clear();
    Solver::clear();
    Item::clear();
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

}
