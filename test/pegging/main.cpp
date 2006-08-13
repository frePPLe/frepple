/***************************************************************************
  file : $HeadURL: file:///develop/SVNrepository/frepple/trunk/test/problems/main.cpp $
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


int main (int argc, char *argv[])
{
  try
  {
    // 0: Initialize
    FreppleInitialize(NULL);

    // 1: Read the model
    FreppleReadXMLFile("pegging.xml",true,false);

    // 2: Report the downstream pegging of all flowplans
    for (Buffer::iterator i = Buffer::begin(); i != Buffer::end(); ++i)
    {
      clog << "\nDownstream pegging for buffer '" << *i << "' :" << endl;
      for(Buffer::flowplanlist::const_iterator oo=(*i)->getFlowPlans().begin();
          oo!=(*i)->getFlowPlans().end(); ++oo)
      {
        clog << endl;
        for (PeggingIterator k(dynamic_cast<const FlowPlan*>(&(*oo))); k; ++k)  // @todo get rid of the ugly cast
        {
          if (k.getLevel() < 0)  // @todo find better convention for recognizing unpegged material
            clog << "\t" << k.getLevel() 
              << "  " << k->getQuantity() 
              << "  unpegged material"
              << "  " << k.getQuantity() 
              << endl;
          else
            clog << "\t" << k.getLevel() 
              << "  " << k->getQuantity() 
              << "  " << k->getDate() << "  " << k->getFlow()->getBuffer() 
              << "  " << k->getFlow()->getOperation() 
              << "  " << k.getQuantity() 
              << endl;
        }
      }
    }

    // 3: Report the upstream pegging of all demands
    for (Demand::iterator j = Demand::begin(); j != Demand::end(); ++j)
    {
      clog << "\nUpstream pegging for demand '" << *j << "' :" << endl;
      for(Demand::OperationPlan_list::const_iterator pp=(*j)->getDelivery().begin();
          pp!=(*j)->getDelivery().end(); ++pp)
      {
        // Assumption!!! The next line assumes that a delivery operation has 
        // only a single flow.
        FlowPlan * qq = (*pp)->getFlowPlans().front();
        clog << endl;
        for (PeggingIterator k(qq); k; --k)
        {
          if (k.getLevel() < 0)
            clog << "\t" << k.getLevel() 
              << "  " << k->getQuantity() 
              << "  unpegged material "
              << endl;
          else
            clog << "\t" << k.getLevel() 
              << "  " << k->getQuantity() 
              << "  " << k->getDate() << "  " << k->getFlow()->getBuffer() 
              << "  " << k->getFlow()->getOperation() 
              << "  " << k.getQuantity() 
              << endl;
        }
      }
    }
    
    // 4: Finalize
    FreppleExit();
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
  return EXIT_SUCCESS;
}
