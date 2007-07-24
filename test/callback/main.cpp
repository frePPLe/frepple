/***************************************************************************
  file : $HeadURL$
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


#include "freppleinterface.h"
#include "frepple.h"
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
    FreppleInitialize(NULL);

    // 1: Create subscriptions
    // a) buffers
    FunctorStatic<Buffer,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Buffer,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<Buffer,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<Buffer,SignalSniffer>::connect(SIG_REMOVE);
    FunctorStatic<BufferDefault,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<BufferDefault,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<BufferDefault,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<BufferDefault,SignalSniffer>::connect(SIG_REMOVE);
    FunctorStatic<BufferInfinite,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<BufferInfinite,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<BufferInfinite,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<BufferInfinite,SignalSniffer>::connect(SIG_REMOVE);

    // b) operations
    FunctorStatic<Operation,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Operation,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<Operation,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<Operation,SignalSniffer>::connect(SIG_REMOVE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<OperationFixedTime,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::connect(SIG_REMOVE);

    // c) items
    FunctorStatic<Item,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Item,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<Item,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<Item,SignalSniffer>::connect(SIG_REMOVE);

    // d) flows
    FunctorStatic<Flow,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Flow,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<Flow,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<Flow,SignalSniffer>::connect(SIG_REMOVE);

    // e) demands
    FunctorStatic<Demand,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Demand,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<Demand,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<Demand,SignalSniffer>::connect(SIG_REMOVE);

    // f) calendars
    FunctorStatic<Calendar,SignalSniffer>::connect(SIG_ADD);
    FunctorStatic<Calendar,SignalSniffer>::connect(SIG_BEFORE_CHANGE);
    FunctorStatic<Calendar,SignalSniffer>::connect(SIG_AFTER_CHANGE);
    FunctorStatic<Calendar,SignalSniffer>::connect(SIG_REMOVE);

    // 2: Read and the model
    logger << "Create the model with callbacks:" << endl;
    FreppleReadXMLFile("callback.xml",true,false);

    // 3: Plan erase the model
    logger << "Plan the model:" << endl;
    FreppleReadXMLData(
      "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" \
      "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" \
      "<COMMANDS>" \
      "<COMMAND xsi:type=\"COMMAND_SOLVE\">" \
      "<SOLVER NAME=\"MRP\" xsi:type=\"SOLVER_MRP\" CONSTRAINTS=\"0\"/>" \
      "</COMMAND>" \
      "</COMMANDS>" \
      "</PLAN>", true, false
    );

    // 4: Plan erase the model
    logger << "Erase the model:" << endl;
    FreppleReadXMLData(
      "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" \
      "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" \
      "<COMMANDS>" \
      "<COMMAND xsi:type=\"COMMAND_ERASE\" MODE=\"model\" />" \
      "</COMMANDS>" \
      "</PLAN>", true, false
    );

    // 5: Remove the subscriptions
    // a) buffers
    FunctorStatic<Buffer,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Buffer,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<Buffer,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<Buffer,SignalSniffer>::disconnect(SIG_REMOVE);
    FunctorStatic<BufferDefault,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<BufferDefault,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<BufferDefault,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<BufferDefault,SignalSniffer>::disconnect(SIG_REMOVE);
    FunctorStatic<BufferInfinite,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<BufferInfinite,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<BufferInfinite,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<BufferInfinite,SignalSniffer>::disconnect(SIG_REMOVE);

    // b) operations
    FunctorStatic<Operation,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Operation,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<Operation,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<Operation,SignalSniffer>::disconnect(SIG_REMOVE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<OperationFixedTime,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<OperationFixedTime,SignalSniffer>::disconnect(SIG_REMOVE);

    // c) items
    FunctorStatic<Item,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Item,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<Item,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<Item,SignalSniffer>::disconnect(SIG_REMOVE);

    // d) flows
    FunctorStatic<Flow,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Flow,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<Flow,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<Flow,SignalSniffer>::disconnect(SIG_REMOVE);

    // e) demands
    FunctorStatic<Demand,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Demand,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<Demand,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<Demand,SignalSniffer>::disconnect(SIG_REMOVE);

    // f) calendars
    FunctorStatic<Calendar,SignalSniffer>::disconnect(SIG_ADD);
    FunctorStatic<Calendar,SignalSniffer>::disconnect(SIG_BEFORE_CHANGE);
    FunctorStatic<Calendar,SignalSniffer>::disconnect(SIG_AFTER_CHANGE);
    FunctorStatic<Calendar,SignalSniffer>::disconnect(SIG_REMOVE);

    // 6: Reread the model
    logger << "Recreate the model without callbacks:" << endl;
    FreppleReadXMLFile("callback.xml",true,false);
  }
  catch (...)
  {
    logger << "Error: Caught an exception in main routine:" <<  endl;
    try { throw; }
    catch (exception& e) {logger << "  " << e.what() << endl;}
    catch (...) {logger << "  Unknown type" << endl;}
    FreppleExit();
    return EXIT_FAILURE;
  }
  FreppleExit();
  return EXIT_SUCCESS;
}
