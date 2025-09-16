const DEFAULT_CUSTOMER = {
  name:  	"Generic customer",
  description: "",
  category: "",
  subcategory: "",
};

export class Customer {
  constructor(data = {}) {
    // Initialize with default values merged with provided data
    Object.assign(this, DEFAULT_CUSTOMER, data);
  }

  // Convert to API format
  toJSON() {
    return {
      name: this.name,
      Description: this.description,
      Category: this.category,
      Subcategory: this.subcategory,
    };
  }

  // Create a Quote instance from API data
  static fromJSON(data) {
    return new Customer({
      ...data
    });
  }

  // Clone the quote
  clone() {
    return new Customer(this.toJSON());
  }
}
