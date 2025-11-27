/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
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
