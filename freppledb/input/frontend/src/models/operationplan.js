/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
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
  id: -1
};

export class Operationplan {
  constructor(data = {}) {
    Object.assign(this, REQUIRED_PROPERTIES);

    Object.assign(this, data);
  }

  // Convert to API format - includes all properties
  toJSON() {
    // Return all properties as-is
    return { ...this };
  }

  // Create an Item instance from API data
  static fromJSON(data) {
    return new Operationplan(data);
  }

  // Clone the item with all its properties
  clone() {
    return new Operationplan({ ...this });
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
