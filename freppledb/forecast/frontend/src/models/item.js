const DEFAULT_ITEM = {
  name:  	"All items",
  description: "",
  category: "",
  subcategory: "",
  cost:  	0.0,
  "count of late demands": 0,
  "Quantity of late demands": 0,
  "value of late demand": 0,
  "count of unplanned demands": 0,
  "Quantity of unplanned demands": 0,
  "Value of unplanned demands": 0,
  "Demand_pattern": "",
  Adi: 0,
  Cv2: 0,
  "Outliers last bucket": 0,
  "Outliers last 6 buckets": 0,
  "Outliers last 12 buckets": 0
};

export class Item {
  constructor(data = {}) {
    // Initialize with default values merged with provided data
    Object.assign(this, DEFAULT_ITEM, data);
  }

  // Convert to API format
  toJSON() {
    return {
      name: this.name,
      Description: this.description,
      Category: this.category,
      Subcategory: this.subcategory,
      Cost: this.cost,
      "count of late demands": this["count of late demands"],
      "Quantity of late demands": this["Quantity of late demands"],
      "value of late demand": this["value of late demand"],
      "count of unplanned demands": this["count of unplanned demands"],
      "Quantity of unplanned demands": this["Quantity of unplanned demands"],
      "Value of unplanned demands": this["Value of unplanned demands"],
      "Demand_pattern": this["Demand_pattern"],
      Adi: this.Adi,
      Cv2: this.Cv2,
      "Outliers last bucket": this["Outliers last bucket"],
      "Outliers last 6 buckets": this["Outliers last 6 buckets"],
      "Outliers last 12 buckets": this["Outliers last 12 buckets"],
    };
  }

  // Create a Quote instance from API data
  static fromJSON(data) {
    return new Item({
      ...data
    });
  }

  // Clone the quote
  clone() {
    return new Item(this.toJSON());
  }
}
