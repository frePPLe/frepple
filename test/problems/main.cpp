/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba                 *
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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,*
 * USA                                                                     *
 *                                                                         *
 ***************************************************************************/


#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;


void reportProblems(string when)
{
  logger << "Problems after " << when << ":" << endl;
  for (Problem::const_iterator i = Problem::begin(); i != Problem::end(); ++i)
    logger << "   " << i->getDates() << " - " << i->getDescription() << endl;
  logger << endl;
}


int main (int argc, char *argv[])
{
  try
  {
    // 0: Initialize
    FreppleInitialize(0,NULL);

    // 1: Read the model
    FreppleReadXMLFile("problems.xml",true,false);
    reportProblems("reading input");

    // 2: Plan the model
    FreppleReadXMLData(
      "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n" \
      "<plan xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" \
      "<?python\n" \
      "frepple.solver_mrp(name=\"MRP\", constraints=0).solve()\n"  \
      "?>\n" \
      "</plan>", true, false
    );
    reportProblems("planning");

    // Define variables for each of the 2 operation_plans
    Operation *buildoper = Operation::find("make end item");
    OperationPlan *build = &*OperationPlan::iterator(buildoper);
    Operation *deliveroper = Operation::find("delivery end item");
    OperationPlan *deliver = &*OperationPlan::iterator(deliveroper);
    if (!deliver || !build) throw DataException("Can't find operationplans");

    // 3: Increase quantity of the delivery & report
    float oldqty = deliver->getQuantity();
    deliver->setQuantity(100);
    reportProblems("increasing delivery quantity");

    // 4: Reduce the quantity of the delivey & report
    deliver->setQuantity(1);
    reportProblems("decreasing delivery quantity");

    // 5: Move the delivery early & report
    Date oldstart = deliver->getDates().getStart();
    deliver->setStart(oldstart - TimePeriod(86400));
    reportProblems("moving delivery early");

    // 6: Move the delivery late & report
    deliver->setStart(oldstart + TimePeriod(86400));
    reportProblems("moving delivery late");

    // 7: Restoring original delivery plan & report
    deliver->setQuantity(oldqty);
    deliver->setStart(oldstart);
    reportProblems("restoring original delivery plan");

    // 8: Deleting delivery
    delete deliver;
    reportProblems("deleting delivery plan");

    // 9: Move the make operation before current & report
    oldstart = build->getDates().getStart();
    build->setStart(Plan::instance().getCurrent() - TimePeriod(1));
    reportProblems("moving build early");

    // 10: Restoring the original build plan & report
    build->setStart(oldstart);
    reportProblems("restoring original build plan");
  }
  catch (...)
  {
    logger << "Error: Caught an exception in main routine:" <<  endl;
    try { throw; }
    catch (const exception& e) {logger << "  " << e.what() << endl;}
    catch (...) {logger << "  Unknown type" << endl;}
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
