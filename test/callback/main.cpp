/***************************************************************************
  file : $HeadURL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2006 by Johan De Taeye                                    *
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
    static bool callback(Buffer* l, Signal a)
    { 
      clog << "  Buffer '" << l << "' receives signal " << a << endl; 
      return true;
    }
    static bool callback(BufferInfinite* l, Signal a)
    { 
      clog << "  BufferInfinite '" << l << "' receives signal " << a << endl; 
      return true;
    }
    static bool callback(BufferDefault* l, Signal a)
    { 
      clog << "  BufferDefault '" << l << "' receives signal " << a << endl; 
      return true;
    }
    static bool callback(Operation* l, Signal a)
    { 
      clog << "  Operation '" << l << "' receives signal " << a << endl; 
      return true;
    }
    static bool callback(OperationFixedTime* l, Signal a)
    { 
      clog << "  OperationFixedTime '" << l << "' receives signal " << a << endl; 
      return true;
    }
    static bool callback(Item* l, Signal a)
    { 
      clog << "  Item '" << l << "' receives signal " << a << endl; 
      return true;
    }
    static bool callback(Flow* l, Signal a)
    { 
      clog << "  Flow between '" << l->getBuffer() << "' and '" <<
        l->getOperation() << "' receives signal " << a << endl; 
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

    // 2: Read and the model
    clog << "Create the model with callbacks:" << endl;
    FreppleReadXMLFile("callback.xml",true,false);

    // 3: Erase the model
    FreppleReadXMLData(
	    "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" \
			"<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" \
	    	"<COMMANDS>" \
		       "<COMMAND xsi:type=\"COMMAND_ERASE\" MODE=\"model\" />" \
		  	"</COMMANDS>" \
		  "</PLAN>", true, false
		);
		    
    // 4: Remove the subscriptions
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

    // 5: Reread and replan the model
    clog << "Recreate the model without callbacks:" << endl;
    FreppleReadXMLFile("callback.xml",true,false);
  }
  catch (...)
  {
    clog << "Error: Caught an exception in main routine:" <<  endl;
    try { throw; }
    catch (exception& e) {clog << "  " << e.what() << endl;}
    catch (...) {clog << "  Unknown type" << endl;}
    FreppleExit();
    return EXIT_FAILURE;
  }
  FreppleExit();
  return EXIT_SUCCESS;
}
