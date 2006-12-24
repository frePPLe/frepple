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

#define FREPPLE_CORE 
#include "frepple/model.h"

namespace frepple
{

template<class Location> DECLARE_EXPORT Tree HasName<Location>::st;


DECLARE_EXPORT void Location::writeElement(XMLOutput* o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }
    
  // Write the complete object
  if (m != NOHEADER) o->BeginObject(tag, Tags::tag_name, getName());

  // Write the fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Location>::writeElement(o, tag);
  o->EndObject(tag);
}


DECLARE_EXPORT void Location::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  HasHierarchy<Location>::beginElement(pIn, pElement);
}


DECLARE_EXPORT void Location::endElement(XMLInput& pIn, XMLElement& pElement)
{
  HasDescription::endElement(pIn, pElement);
  HasHierarchy<Location>::endElement(pIn, pElement);
}


DECLARE_EXPORT Location::~Location()
{
  // Remove all references from buffers to this location
  for (Buffer::iterator buf = Buffer::begin();
       buf != Buffer::end(); ++buf)
    if (buf->getLocation() == this) buf->setLocation(NULL);

  // Remove all references from resources to this location
  for (Resource::iterator res = Resource::begin();
       res != Resource::end(); ++res)
    if (res->getLocation() == this) res->setLocation(NULL);
}

}
