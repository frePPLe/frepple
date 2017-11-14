/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2013 by frePPLe bvba                                 *
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


#include "frepple.h"
#include "freppleinterface.h"
using namespace frepple;


class SignalSniffer
{
  public:
    static bool callback(Buffer* l, const Signal a)
    {
      logger << "  Buffer '" << l << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(BufferInfinite* l, const Signal a)
    {
      logger << "  BufferInfinite '" << l << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(BufferDefault* l, const Signal a)
    {
      logger << "  BufferDefault '" << l << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(Operation* l, const Signal a)
    {
      logger << "  Operation '" << l << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(OperationFixedTime* l, const Signal a)
    {
      logger << "  OperationFixedTime '" << l << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(Item* l, const Signal a)
    {
      logger << "  Item '" << l << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(Flow* l, const Signal a)
    {
      logger << "  Flow between '" << l->getBuffer() << "' and '"
          << l->getOperation() << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(Demand* l, const Signal a)
    {
      logger << "  Demand '" << l << "' receives signal " << a << endl;
      return true;
    }
    static bool callback(Calendar* l, const Signal a)
    {
      logger << "  Calendar '" << l << "' receives signal " << a << endl;
      return true;
    }
};


int main (int argc, char *argv[])
{
  try
  {
    // 0: Initialize
    FreppleInitialize();

    // 1: Create subscriptions
    // a) buffers
    FunctorStatic<Buffer,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Buffer,SignalSniffer>::connect(SIG_REMOVE);
    FunctorStatic<BufferDefault,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<BufferDefault,SignalSniffer>::connect(SIG_REMOVE);
    FunctorStatic<BufferInfinite,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<BufferInfinite,SignalSniffer>::connect(SIG_REMOVE);

    // b) operations
    FunctorStatic<Operation,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Operation,SignalSniffer>::connect(SIG_REMOVE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<OperationFixedTime,SignalSniffer>::connect(SIG_REMOVE);

    // c) items
    FunctorStatic<Item,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Item,SignalSniffer>::connect(SIG_REMOVE);

    // d) flows
    /*
    FunctorStatic<Flow,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Flow,SignalSniffer>::connect(SIG_REMOVE);
    */

    // e) demands
    FunctorStatic<Demand,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Demand,SignalSniffer>::connect(SIG_REMOVE);

    // f) calendars
    FunctorStatic<Calendar,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Calendar,SignalSniffer>::connect(SIG_REMOVE);

    // 2: Read and the model
    logger << "Create the model with callbacks:" << endl;
    FreppleReadXMLFile("callback.xml", true, false);

    // 3: Plan erase the model
    logger << "Plan the model:" << endl;
    utils::PythonInterpreter::execute("frepple.solver_mrp(constraints=0).solve()");

    // 4: Plan erase the model
    logger << "Erase the model:" << endl;
    utils::PythonInterpreter::execute("frepple.erase(True)");

    // 5: Remove the subscriptions
    // a) buffers
    FunctorStatic<Buffer,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Buffer,SignalSniffer>::disconnect(SIG_REMOVE);
    FunctorStatic<BufferDefault,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<BufferDefault,SignalSniffer>::disconnect(SIG_REMOVE);
    FunctorStatic<BufferInfinite,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<BufferInfinite,SignalSniffer>::disconnect(SIG_REMOVE);

    // b) operations
    FunctorStatic<Operation,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Operation,SignalSniffer>::disconnect(SIG_REMOVE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<OperationFixedTime,SignalSniffer>::disconnect(SIG_REMOVE);

    // c) items
    FunctorStatic<Item,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Item,SignalSniffer>::disconnect(SIG_REMOVE);

    // d) flows
    /*
    FunctorStatic<Flow,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Flow,SignalSniffer>::disconnect(SIG_REMOVE);
    */

    // e) demands
    FunctorStatic<Demand,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Demand,SignalSniffer>::disconnect(SIG_REMOVE);

    // f) calendars
    FunctorStatic<Calendar,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Calendar,SignalSniffer>::disconnect(SIG_REMOVE);

    // 6: Reread the model
    logger << "Recreate the model without callbacks:" << endl;
    FreppleReadXMLFile("callback.xml",true,false);
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
