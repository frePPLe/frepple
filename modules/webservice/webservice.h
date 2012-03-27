/***************************************************************************
  file : $URL$
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007 by Johan De Taeye, frePPLe bvba                                    *
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

/* The contents of this file is automatically processed into a WSDL
 * service definition file.
 * See the gsoap documentation for the right format and supported constructs.
 */

#ifndef DOXYGEN

/* Typedefs to help gsoap map the types to XML data types. */
typedef double xsd__double;
typedef long int xsd__int;
typedef bool xsd__boolean;
typedef char* xsd__string;
typedef time_t  xsd__dateTime;

//gsoap frepple service name: frepple
//gsoap frepple service namespace: urn:frepple
//gsoap frepple service style: rpc
//gsoap frepple service encoding: encoded
//gsoap frepple service namespace: http://192.168.0.137/static/frepple.wsdl
//gsoap frepple service location: http://192.168.0.137:6262
//gsoap frepple service documentation: frePPLe - a free Production Planning Library

class frepple__DemandInfo
{
  public:
    xsd__string name;
    xsd__string item;
    xsd__int priority;
    xsd__double quantity;
    xsd__dateTime due;
};
struct frepple__DemandInfoResponse {frepple__DemandInfo _return;};

//gsoap frepple service method-action: demand ""
int frepple__demand(xsd__string name, struct frepple__DemandInfoResponse &result);

struct frepple__PostResponse {xsd__int _return;};

//gsoap frepple service method-action: post ""
int frepple__post(xsd__string data, struct frepple__PostResponse &result);

#endif
