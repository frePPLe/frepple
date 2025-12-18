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

template <class Customer>
Tree utils::HasName<Customer>::st;
const MetaCategory* Customer::metadata;
const MetaClass* CustomerDefault::metadata;

int Customer::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Customer>("customer", "customers",
                                                      reader, finder);
  registerFields<Customer>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Customer>::initialize();
}

int CustomerDefault::initialize() {
  // Initialize the metadata
  CustomerDefault::metadata = MetaClass::registerClass<CustomerDefault>(
      "customer", "customer_default", Object::create<CustomerDefault>, true);

  // Initialize the Python class
  return FreppleClass<CustomerDefault, Customer>::initialize();
}

Customer::~Customer() {
  // Remove all references from demands to this customer
  for (auto& i : Demand::all())
    if (i.getCustomer() == this) i.setCustomer(nullptr);
}

}  // namespace frepple
