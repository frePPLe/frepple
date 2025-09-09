const DEFAULT_LOCATION = {
  name:  	"All locations",
  description: "",
  category: "",
  subcategory: "",
};

export class Location {
  constructor(data = {}) {
    // Initialize with default values merged with provided data
    Object.assign(this, DEFAULT_LOCATION, data);
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
    return new Location({
      ...data
    });
  }

  // Clone the quote
  clone() {
    return new Location(this.toJSON());
  }
}
