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

#include "module.h"

namespace module_webservice
{


int frepple__demand(struct soap *soap, xsd__string name, struct frepple__DemandInfoResponse &result)
{
  // Search for the demand
  if (!name)
    return soap_sender_fault(soap, "Missing demand name", "NULL demand name passed");
  Demand* i = Demand::find(name);
  if (!i)
  {
    ostringstream msg;
    msg << "The demand with name '" << name << "' couldn't be found";
    return soap_sender_fault(soap, "Demand not found", msg.str().c_str());
  }

  // Retrieve demand data
  result._return.name = const_cast<char*>(i->getName().c_str());
  if (i->getItem())
    result._return.item = const_cast<char*>(i->getItem()->getName().c_str());
  result._return.priority = i->getPriority();
  result._return.due = i->getDue().getTicks();
  return SOAP_OK;
}


}
