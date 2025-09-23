/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

const REQUIRED_PROPERTIES = {
  name: "",
  description: "",
  category: "",
  subcategory: ""
};

export class Location {
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

  // Create an Location instance from API data
  static fromJSON(data) {
    return new Location(data);
  }

  // Clone the item with all its properties
  clone() {
    return new Location({ ...this });
  }

  // Check if all required properties are present and valid
  isValid() {
    return Object.keys(REQUIRED_PROPERTIES).every(key =>
      this[key] !== undefined && this[key] !== null
    );
  }

  // Update properties while preserving existing ones
  update(data = {}) {
    Object.assign(this, data);
    return this;
  }
}
