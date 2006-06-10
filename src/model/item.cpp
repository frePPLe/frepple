/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/src/model/item.cpp $
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

#define FREPPLE_CORE 
#include "frepple/model.h"

namespace frepple
{

template<class Item> DECLARE_EXPORT Tree HasName<Item>::st;


Item::~Item()
{
  // Remove references from the buffers
  for (Buffer::iterator buf = Buffer::begin();
       buf != Buffer::end(); ++buf)
    if ((*buf)->getItem() == this) (*buf)->setItem(NULL);

  // Remove references from the demands
  for (Demand::iterator l = Demand::begin();
       l != Demand::end(); ++l)
    if ((*l)->getItem() == this) (*l)->setItem(NULL);
}


void Item::writeElement(XMLOutput *o, const XMLtag& tag, mode m) const
{
  // Writing a reference
  if (m == REFERENCE)
  {
    o->writeElement(tag, Tags::tag_name, getName());
    return;
  }
    
  // Write the complete item
  if (m != NOHEADER) o->BeginObject(tag, Tags::tag_name, getName());

  // Write the fields
  HasDescription::writeElement(o, tag);
  HasHierarchy<Item>::writeElement(o, tag);
  o->writeElement(Tags::tag_operation, deliveryOperation);
  o->EndObject(tag);
}


void Item::beginElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_operation))
    pIn.readto( MetaCategory::ControllerString<Operation>(Operation::metadata,pIn.getAttributes()) );
  else
    HasHierarchy<Item>::beginElement(pIn, pElement);
}


void Item::endElement(XMLInput& pIn, XMLElement& pElement)
{
  if (pElement.isA (Tags::tag_operation))
  {
    Operation *o = dynamic_cast<Operation*>(pIn.getPreviousObject());
    if (o) setDelivery(o);
    else throw LogicException("Incorrect object type during read operation");
  }
  else
  {
    HasDescription::endElement(pIn, pElement);
    HasHierarchy<Item>::endElement(pIn, pElement);
  }
}


}
