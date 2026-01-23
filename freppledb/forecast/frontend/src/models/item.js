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

// const DEFAULT_ITEM = {
//   name:  	"",
//   description: "",
//   category: "",
//   subcategory: "",
//   cost:  	0.0,
  // "count of late demands": 0,
  // "Quantity of late demands": 0,
  // "value of late demand": 0,
  // "count of unplanned demands": 0,
  // "Quantity of unplanned demands": 0,
  // "Value of unplanned demands": 0,
  // "Demand_pattern": "",
  // Adi: 0,
  // Cv2: 0,
  // "Outliers last bucket": 0,
  // "Outliers last 6 buckets": 0,
  // "Outliers last 12 buckets": 0
// };

const REQUIRED_PROPERTIES = {
  Name: ""
};

export class Item {
  constructor(data = {}) {
    Object.assign(this, REQUIRED_PROPERTIES);

    Object.assign(this, data);
  }

  // Get only the required properties
  getRequiredProperties() {
    const { name, description, category, subcategory } = this;
    return { name, description, category, subcategory };
  }

  // Get all custom/optional properties (everything except the required ones)
  getCustomProperties() {
    const result = {};
    const requiredKeys = Object.keys(REQUIRED_PROPERTIES);

    for (const [key, value] of Object.entries(this)) {
      if (!requiredKeys.includes(key)) {
        result[key] = value;
      }
    }

    return result;
  }

  // Convert to API format - includes all properties
  toJSON() {
    // Return all properties as-is
    return { ...this };
  }

  // Create an Item instance from API data
  static fromJSON(data) {
    return new Item(data);
  }

  // Clone the item with all its properties
  clone() {
    return new Item({ ...this });
  }

  // Check if all required properties are present and valid
  isValid() {
    return Object.keys(REQUIRED_PROPERTIES).every(key =>
      this[key] !== undefined && this[key] !== null
    );
  }

  // Update properties while preserving existing ones
  update(attributeData = []) {
    Object.assign(this, Object.fromEntries(attributeData));
    return this;
  }
}
