/***************************************************************************
  file : $URL: file:///C:/develop/SVNrepository/frepple/trunk/contrib/scripting/frepple.i $
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


#include "mod_frepple.h"


int getInventoryFilter(request_rec *r)
{
  try
  {

  // Set the response headers: xml data that can be cached by your browser
  ap_set_content_type(r, "application/xml");
  //xxxapr_table_setn(r->headers_out, "Cache-Control", "max-age=10800");
  apr_table_setn(r->headers_out, "Cache-Control", "no-cache");
  if (r->header_only) return OK;
  
  // Generating the list of locations
  ap_rputs( 
   "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>"
   "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
   "<LOCATIONS>\n", r);
  for (Location::iterator gloc = Location::begin();
    gloc != Location::end(); ++gloc)
    if (!(*gloc)->getHidden())
      ap_rprintf(r, "<LOCATION NAME=\"%s\"/>\n", (*gloc)->getName().c_str());

  // Generating the list of items
  ap_rputs(
   "</LOCATIONS><ITEMS>\n", r);
  for (Item::iterator gitem = Item::begin();
    gitem != Item::end(); ++gitem)
    if (!(*gitem)->getHidden())
     ap_rprintf(r, "<ITEM NAME=\"%s\"/>\n", (*gitem)->getName().c_str());

  // Generating the list of buffers
  ap_rputs(
   "  </ITEMS><BUFFERS>\n", r);
  for (Buffer::iterator gbuf = Buffer::begin();
      gbuf != Buffer::end(); ++gbuf)
    if (!(*gbuf)->getHidden())
    ap_rprintf(r,
      "<BUFFER NAME=\"%s\" LOCATION=\"%s\" ITEM=\"%s\"/>\n",
      (*gbuf)->getName().c_str(),
      (*gbuf)->getLocation() ? (*gbuf)->getLocation()->getName().c_str() : "",
      (*gbuf)->getItem() ? (*gbuf)->getItem()->getName().c_str() : "");
  ap_rputs("</BUFFERS></PLAN>\n", r);

  return OK;
  }
  catch (...) {return HTTP_NOT_FOUND;}
};
