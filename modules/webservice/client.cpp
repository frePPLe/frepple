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

#include "soapfreppleProxy.h"
#include "frepple.nsmap"


int main(int argc, char *argv[])
{
   if  (argc <= 2 || (strcmp(argv[1],"get") && strcmp(argv[1],"post")))
   {
     std::cout << "Usage:" << std::endl;
     std::cout << "  " << argv[0] << " get <demand name>" << std::endl << std::endl;
     std::cout << "  " << argv[0] << " post <data>" << std::endl << std::endl;
     return 1;
   }

   frepple svc;

   // Return demand information
   if (!strcmp(argv[1],"get"))
   {
     struct frepple__DemandInfoResponse result;
     if (svc.frepple__demand(argv[2], result) == SOAP_OK)
     {
       std::cout << "Name: " << result._return.name << std::endl
         << "Item: " << result._return.item << std::endl
         << "Quantity: " << result._return.quantity << std::endl
         << "Due date: " << asctime(gmtime(&result._return.due))
         << "Priority: " << result._return.priority << std::endl;
     }
     else
        soap_print_fault(svc.soap, stderr);
   }

   // Post new XML data
   if (!strcmp(argv[1],"post"))
   {
     struct frepple__PostResponse result;
     if (svc.frepple__post(argv[2], result) == SOAP_OK)
     {
       std::cout << "answer: " << result._return << std::endl;
     }
     else
        soap_print_fault(svc.soap, stderr);
   }

   return 0;
}

