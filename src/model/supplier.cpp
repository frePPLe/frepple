/***************************************************************************
 *                                                                         *
 * Copyright (C) 2014 by frePPLe bv                                        *
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

template <class Supplier>
Tree utils::HasName<Supplier>::st;
const MetaCategory* Supplier::metadata;
const MetaClass* SupplierDefault::metadata;

int Supplier::initialize() {
  // Initialize the metadata
  metadata = MetaCategory::registerCategory<Supplier>("supplier", "suppliers",
                                                      reader, finder);
  registerFields<Supplier>(const_cast<MetaCategory*>(metadata));

  // Initialize the Python class
  return FreppleCategory<Supplier>::initialize();
}

int SupplierDefault::initialize() {
  // Initialize the metadata
  SupplierDefault::metadata = MetaClass::registerClass<SupplierDefault>(
      "supplier", "supplier_default", Object::create<SupplierDefault>, true);

  // Initialize the Python class
  return FreppleClass<SupplierDefault, Supplier>::initialize();
}

Supplier::~Supplier() {}

}  // namespace frepple
