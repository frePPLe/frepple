/***************************************************************************
 *                                                                         *
 * Copyright (C) 2014 by frePPLe bvba                                      *
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

template<class Supplier> Tree<string> utils::HasName<Supplier>::st;
const MetaCategory* Supplier::metadata;
const MetaClass* SupplierDefault::metadata;


int Supplier::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Supplier>("supplier", "suppliers", reader, finder);
  registerFields<Supplier>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Supplier>::initialize();
}


int SupplierDefault::initialize()
{
  // Initialize the metadata
  SupplierDefault::metadata = MetaClass::registerClass<SupplierDefault>(
    "supplier", "supplier_default",
    Object::create<SupplierDefault>, true
    );

  // Initialize the Python class
  return FreppleClass<SupplierDefault,Supplier>::initialize();
}


Supplier::~Supplier()
{
}

} // end namespace
