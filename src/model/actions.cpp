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
    cout << "Started running the solver '" << sol->getName()
      << "' at " << Date::now() << endl;
  Timer t;

  // Running the solver now
  sol->solve();

  // Ending message
  if (getVerbose())
    cout << "Finished running the solver '" << sol->getName()
    << "' at " << Date::now()  << " : " << t << endl;
}


DECLARE_EXPORT void Solver::writeElement
(XMLOutput *o, const XMLtag &tag, mode m) const
{
  // The subclass should have written its own header
  assert(m == NOHEADER);

  // Fields
  if (verbose) o->writeElement(Tags::tag_verbose, verbose);

  // End object
  o->EndObject(tag);
}


DECLARE_EXPORT void Solver::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_verbose))
    setVerbose(pElement.getBool());
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
    cout << "Started reading model from file '" << filename
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
    {
      LockManager::getManager().obtainWriteLock(&Plan::instance());
      XMLInput().parse(in, &Plan::instance(), validate);
    }
  }
  else if (validate_only)
    // Read and validate a file
    XMLInputFile(filename).parse(NULL, true);
  else
  {
    // Read, execute and optionally validate a file
    LockManager::getManager().obtainWriteLock(&Plan::instance());
    XMLInputFile(filename).parse(&Plan::instance(),validate);
  }

  // Message
  if (getVerbose())
    cout << "Finished reading model at " << Date::now()  << " : " << t << endl;
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
    cout << "Started reading model from string at " << Date::now() << endl;
  Timer t;

  // Note: Reading the data can throw exceptions...
  if (validate_only)
    XMLInputString(data).parse(NULL, true);
  else
  {
    LockManager::getManager().obtainWriteLock(&Plan::instance());
    XMLInputString(data).parse(&Plan::instance(), validate);
  }

  // Message
  if (getVerbose())
    cout << "Finished reading model at " << Date::now()  << " : " << t << endl;
}


//
// READ XML INPUT URL
//

DECLARE_EXPORT void CommandReadXMLURL::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA(Tags::tag_url))
    pElement >> url;
  else if (pElement.isA(Tags::tag_validate))
    pElement >> validate;
  else
    Command::endElement(pIn, pElement);
}


DECLARE_EXPORT void CommandReadXMLURL::execute()
{
  // Message
  if (getVerbose())
    cout << "Started reading model from url '" << url 
    << "' at " << Date::now() << endl;
  Timer t;

  // Replace environment variables in the url.
  Environment::resolveEnvironment(url);

  // Note: Reading the data can throw exceptions...
  if (validate_only)
    XMLInputURL(url).parse(NULL, true);
  else
  {
    LockManager::getManager().obtainWriteLock(&Plan::instance());
    XMLInputURL(url).parse(&Plan::instance(), validate);
  }

  // Message
  if (getVerbose())
    cout << "Finished reading model at " << Date::now()  << " : " << t << endl;
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
    cout << "Start saving model to file '" << filename
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
    cout << "Finished saving " << o.countObjects()
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
    cout << "Start saving plan to file '" << getFileName()
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
        for(Buffer::flowplanlist::const_iterator 
          oo=gbuf->getFlowPlans().begin();
          oo!=gbuf->getFlowPlans().end(); 
          ++oo)
          if (oo->getType() == 1)
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
        for(Demand::OperationPlan_list::const_iterator 
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
        for(Resource::loadplanlist::const_iterator 
          qq=gres->getLoadPlans().begin();
          qq!=gres->getLoadPlans().end(); 
          ++qq)
          if (qq->getType() == 1)
          {
            textoutput << "RESOURCE\t" << *gres << '\t'
              << qq->getDate() << '\t'
              << qq->getQuantity() << '\t'
              << qq->getOnhand() << endl;
          }
    }

    // Write the operationplan summary.
    for(OperationPlan::iterator rr = OperationPlan::begin();
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
      textoutput << "PROBLEM\t" << (*gprob)->getType().type << '\t'
        << (*gprob)->getDescription() << '\t'
        << (*gprob)->getDateRange() << endl;
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
    cout << "Finished saving plan at " << Date::now() << " : " << t << endl;
}


//
// MOVE OPERATIONPLAN
//

DECLARE_EXPORT CommandMoveOperationPlan::CommandMoveOperationPlan
  (OperationPlan* o, Date newdate, bool use_end_date)
  : opplan(o), use_end(use_end_date)
{
  if(!opplan) return;
  if (use_end)
  {
    originaldate = opplan->getDates().getEnd();
    opplan->setEnd(newdate);
  }
  else
  {
    originaldate = opplan->getDates().getStart();
    opplan->setStart(newdate);
  }
}


DECLARE_EXPORT void CommandMoveOperationPlan::undo()
{
  if (!opplan) return;
  if (use_end) opplan->setEnd(originaldate);
  else opplan->setStart(originaldate);
  opplan = NULL;
}


DECLARE_EXPORT void CommandMoveOperationPlan::setDate(Date newdate)
{
  if(!opplan) return;
  if (use_end) opplan->setEnd(newdate);
  else opplan->setStart(newdate);
}


DECLARE_EXPORT string CommandMoveOperationPlan::getDescription() const
{
  ostringstream ch;
  ch << "moving operationplan ";
  if (opplan)
    ch << "of operation '" << opplan->getOperation()
    << "' with identifier " << opplan->getIdentifier();
  else
    ch << "NULL";
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
      cout << "Start model erase command at " << Date::now() << endl;
    else
      cout << "Start plan erase command at " << Date::now() << endl;
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
    cout << "Finished erase command at " << Date::now() 
      << " : " << t << endl;
}

}
