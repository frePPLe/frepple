/***************************************************************************
 *                                                                         *
 * Copyright (C) 2007-2015 by frePPLe bv                                   *
 *                                                                         *
 * Permission is hereby granted, free of charge, to any person obtaining   *
 * a copy of this software and associated documentation files (the         *
 * "Software"), to deal in the Software without restriction, including     *
 * without limitation the rights to use, copy, modify, merge, publish,     *
 * distribute, sublicense, and/or sell copies of the Software, and to      *
 * permit persons to whom the Software is furnished to do so, subject to   *
 * the following conditions:                                               *
 *                                                                         *
 * The above copyright notice and this permission notice shall be          *
 * included in all copies or substantial portions of the Software.         *
 *                                                                         *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,         *
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF      *
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                   *
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE  *
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION  *
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION   *
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.         *
 *                                                                         *
 ***************************************************************************/

#include "frepple/model.h"

namespace frepple {

template <class Location>
Tree utils::HasName<Location>::st;
const MetaCategory* Location::metadata;
const MetaClass* LocationDefault::metadata;

int Location::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Location>("location", "locations",
                                                      reader, finder);
  registerFields<Location>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Location>::initialize();
}

int LocationDefault::initialize() {
  // Initialize the metadata
  LocationDefault::metadata = MetaClass::registerClass<LocationDefault>(
      "location", "location_default", Object::create<LocationDefault>, true);

  // Initialize the Python class
  return FreppleClass<LocationDefault, Location>::initialize();
}

Location::~Location() {
  // Remove all references from buffers to this location
  for (auto buf = Buffer::begin(); buf != Buffer::end();) {
    if (buf->getLocation() == this) {
      auto tmp = &*buf;
      ++buf;
      delete tmp;
    } else
      ++buf;
  }

  // Remove all references from resources to this location
  for (auto res = Resource::begin(); res != Resource::end();) {
    if (res->getLocation() == this) {
      auto tmp = &*res;
      ++res;
      delete tmp;
    } else
      ++res;
  }

  // Remove all references from operations to this location
  for (auto oper = Operation::begin(); oper != Operation::end();) {
    if (oper->getLocation() == this) {
      auto tmp = &*oper;
      ++oper;
      delete tmp;
    } else
      ++oper;
  }

  // Remove all references from demands to this location
  for (auto& dmd : Demand::all())
    if (dmd.getLocation() == this) dmd.setLocation(nullptr);

  // Remove all item suppliers referencing this location
  for (auto& sup : Supplier::all()) {
    for (auto it = sup.getItems().begin(); it != sup.getItems().end();) {
      if (it->getLocation() == this) {
        const ItemSupplier* itemsup = &*it;
        ++it;  // Advance iterator before the delete
        delete itemsup;
      } else
        ++it;
    }
  }

  // Remove all item distributions referencing this location
  for (auto& it : Item::all()) {
    for (auto dist = it.getDistributions().begin();
         dist != it.getDistributions().end();) {
      if (dist->getOrigin() == this) {
        const ItemDistribution* itemdist = &*dist;
        ++dist;  // Advance iterator before the delete
        delete itemdist;
      } else
        ++dist;
    }
  }
}

}  // namespace frepple
