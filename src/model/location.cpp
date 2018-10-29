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

template<class Location> Tree<string> utils::HasName<Location>::st;
const MetaCategory* Location::metadata;
const MetaClass* LocationDefault::metadata;


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


Location::~Location()
{
  // Remove all references from buffers to this location
  for (auto buf = Buffer::begin(); buf != Buffer::end(); ++buf)
    if (buf->getLocation() == this)
      buf->setLocation(nullptr);

  // Remove all references from resources to this location
  for (auto res = Resource::begin(); res != Resource::end(); ++res)
    if (res->getLocation() == this)
      res->setLocation(nullptr);

  // Remove all references from operations to this location
  for (auto oper = Operation::begin(); oper != Operation::end(); ++oper)
    if (oper->getLocation() == this)
      oper->setLocation(nullptr);

  // Remove all references from demands to this location
  for (auto dmd = Demand::begin(); dmd != Demand::end(); ++dmd)
    if (dmd->getLocation() == this)
      dmd->setLocation(nullptr);

  // Remove all item suppliers referencing this location
  for (auto sup = Supplier::begin(); sup != Supplier::end(); ++sup)
  {
    for (auto it = sup->getItems().begin(); it != sup->getItems().end(); )
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

  // Remove all item distributions referencing this location
  for (auto it = Item::begin(); it != Item::end(); ++it)
  {
    for (auto dist = it->getDistributions().begin(); dist != it->getDistributions().end(); )
    {
      if (dist->getOrigin() == this)
      {
        const ItemDistribution *itemdist = &*dist;
        ++dist;   // Advance iterator before the delete
        delete itemdist;
      }
      else
        ++dist;
    }
  }

}

} // end namespace
