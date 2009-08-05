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
 * Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA *
 *                                                                         *
 ***************************************************************************/

#include "module.h"
#include "frepple.nsmap" 


/** Implementation of the webservice method to return demand information. */
SOAP_FMAC5 int SOAP_FMAC6 frepple__demand(struct soap* soap, char *name, struct frepple__DemandInfoResponse &result)
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
  result._return.quantity = i->getQuantity();
  result._return.due = i->getDue().getTicks();
  return SOAP_OK;
}


/** Implementation of the webservice method to post XML data. */
SOAP_FMAC5 int SOAP_FMAC6 frepple__post(struct soap* soap, char *data, struct frepple__PostResponse &result)
{
  try { 
    CommandReadXMLString(data, true, false).execute(); 
  }
  catch (DataException e)
    { return soap_sender_fault(soap, "Data Exception", e.what()); }
  catch (LogicException e)
    { return soap_sender_fault(soap, "Logic Exception", e.what()); }
  catch (RuntimeException e)
    { return soap_sender_fault(soap, "Runtime Exception", e.what()); }
  catch (...)
    { return soap_sender_fault(soap, "Exception", "Unidentified"); }
  result._return = 11;
  return SOAP_OK;
}


