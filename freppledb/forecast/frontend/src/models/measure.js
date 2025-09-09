const DEFAULT_MEASURE = {
  "$$hashKey": "",
  computed: "",
  defaultvalue: 0,
  discrete: false,
  editable: false,
  formatter: "number",
  initially_hidden: true,
  label: "",
  mode_future: "view",
  mode_past: "view",
  name: ""
};

export class Measure {
  constructor(data = {}) {
    // Initialize with default values merged with provided data
    Object.assign(this, DEFAULT_MEASURE, data);
  }

  // Convert to API format
  toJSON() {
    return {
      $$hashKey: this.$$hashKey,
      computed: this.computed,
      defaultvalue: this.defaultvalue,
      discrete: this.discrete,
      editable: this.editable,
      formatter: this.formatter,
      initially_hidden: this.initially_hidden,
      label: this.label,
      mode_future: this.mode_future,
      mode_past: this.mode_past,
      name: this.name,
    };
  }

  // Create a Quote instance from API data
  static fromJSON(data) {
    return new Measure({
      ...data
    });
  }

  // Clone the quote
  clone() {
    return new Measure(this.toJSON());
  }
}
