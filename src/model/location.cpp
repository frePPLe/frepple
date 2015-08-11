/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bvba                                 *
 *                                                                         *
 * This library is free software; you can redistribute it and/or modify it *
 * under the terms of the GNU Affero General Public License as published   *
 * by the Free Software Foundation; either version 3 of the License, or    *
 * (at your option) any later version.                                     *
 *                                                                         *
 * This library is distributed in the hope that it will be useful,         *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 * GNU Affero General Public License for more details.                     *
 *                                                                         *
 * You should have received a copy of the GNU Affero General Public        *
 * License along with this program.                                        *
 * If not, see <http://www.gnu.org/licenses/>.                             *
 *                                                                         *
 ***************************************************************************/

#define FREPPLE_CORE
#include "frepple/model.h"

namespace frepple
{

template<class Location> DECLARE_EXPORT Tree utils::HasName<Location>::st;
DECLARE_EXPORT const MetaCategory* Location::metadata;
DECLARE_EXPORT const MetaClass* LocationDefault::metadata;


int Location::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Location>("location", "locations", reader, finder);
  registerFields<Location>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Location>::initialize();
}


int LocationDefault::initialize()
{
  // Initialize the metadata
  LocationDefault::metadata = MetaClass::registerClass<LocationDefault>("location", "location_default",
      Object::create<LocationDefault>, true);

  // Initialize the Python class
  return FreppleClass<LocationDefault,Location>::initialize();
}


DECLARE_EXPORT Location::~Location()
{
  // Remove all references from buffers to this location
  for (Buffer::iterator buf = Buffer::begin();
      buf != Buffer::end(); ++buf)
    if (buf->getLocation() == this)
      buf->setLocation(NULL);

  // Remove all references from resources to this location
  for (Resource::iterator res = Resource::begin();
      res != Resource::end(); ++res)
    if (res->getLocation() == this)
      res->setLocation(NULL);

  // Remove all references from operations to this location
  for (Operation::iterator oper = Operation::begin();
      oper != Operation::end(); ++oper)
    if (oper->getLocation() == this)
      oper->setLocation(NULL);

  // Remove all references from demands to this location
  for (Demand::iterator dmd = Demand::begin();
      dmd != Demand::end(); ++dmd)
    if (dmd->getLocation() == this)
      dmd->setLocation(NULL);

  // Remove all item suppliers referencing this location
  for (Supplier::iterator sup = Supplier::begin();
    sup != Supplier::end(); ++sup)
  {
    for (Supplier::itemlist::const_iterator it = sup->getItems().begin();
      it != sup->getItems().end(); )
    {
      if (it->getLocation() == this)
      {
        const ItemSupplier *itemsup = &*it;
        ++it;   // Advance iterator before the delete
        delete itemsup;
      }
      else
        ++it;
    }
  }

  // The ItemDistribution objects are automatically deleted by the
  // destructor of the Association list class.
}

} // end namespace
