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

template<class Customer> Tree<string> utils::HasName<Customer>::st;
const MetaCategory* Customer::metadata;
const MetaClass* CustomerDefault::metadata;


int Customer::initialize()
{
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Customer>("customer", "customers", reader, finder);
  registerFields<Customer>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Customer>::initialize();
}


int CustomerDefault::initialize()
{
  // Initialize the metadata
  CustomerDefault::metadata = MetaClass::registerClass<CustomerDefault>(
    "customer", "customer_default",
    Object::create<CustomerDefault>, true
    );

  // Initialize the Python class
  return FreppleClass<CustomerDefault,Customer>::initialize();
}


Customer::~Customer()
{
  // Remove all references from demands to this customer
  for (Demand::iterator i = Demand::begin(); i != Demand::end(); ++i)
    if (i->getCustomer() == this) i->setCustomer(nullptr);
}

} // end namespace
