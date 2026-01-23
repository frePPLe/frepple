/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

import {isBlank} from "@common/utils.js";

const REQUIRED_PROPERTIES = {
  Name: ""
};

export class Customer {
  constructor(data = {}) {
    Object.assign(this, REQUIRED_PROPERTIES);

    if (!isBlank(data)) {
      Object.assign(this, data);
    }
  }

  // Convert to API format - includes all properties
  toJSON() {
    // Return all properties as-is
    return { ...this };
  }

  // Create an Customer instance from API data
  static fromJSON(data) {
    return new Customer(data);
  }

  // Clone the item with all its properties
  clone() {
    return new Customer({ ...this });
  }

  // Update properties while preserving existing ones
  update(attributeData = []) {
    Object.assign(this, Object.fromEntries(attributeData));
    return this;
  }
}
