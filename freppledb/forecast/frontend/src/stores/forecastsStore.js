
import { defineStore } from 'pinia';
import { Item } from '../models/item.js';
import { Location } from '../models/location.js';
import { Customer } from '../models/customer.js';
import { Measure } from '../models/measure.js';
import { forecastService } from '../services/forecastService.js';

export const useForecastsStore = defineStore('forecasts', {
  state: () => ({
    item: new Item(),
    location: new Location(),
    customer: new Customer(),
    itemTree: [],
    locationTree: [],
    customerTree: [],
    currentSequence: 'ILC',
    currentMeasure: 'nodata',
    loading: false,
    error: null
  }),

  getters: {
    measures: () => window.measures,
    preferences: () => window.preferences,
    // hasProblems: (state) => state.quote.problems.length > 0,
    // hasOperations: (state) => state.quote.pegging.length > 0,
    // canIncreasePegLevel: (state) => state.quote.pegging && state.quote.pegging.length > 0,
    // canDecreasePegLevel: (state) => state.peglevel > 0 && state.quote.pegging
  },

  actions: {
    setCurrentMeasure(measure) {
      this.currentMeasure = measure;
    },

    async getItemtree() {
      this.loading = true;
      this.error = null;

      try {
        // const measure = {
        //   measure: this.state.currentMeasure
        // };

        const {responseData} = await forecastService.getItemtree(this.state.currentMeasure);
        console.log(41, responseData);
        // if (responseData.value?.demands?.[0]) {
        //   const demandData = responseData.value.demands[0];
        //
        //   // Extract string values for item, customer, location
        //   const item = typeof demandData.item === 'string'
        //     ? demandData.item
        //     : (demandData.item?.name || '');
        //
        //   const customer = typeof demandData.customer === 'string'
        //     ? demandData.customer
        //     : (demandData.customer?.name || '');
        //
        //   const location = typeof demandData.location === 'string'
        //     ? demandData.location
        //     : (demandData.location?.name || '');
        //
        //   this.updateQuote({
        //     name: demandData.name,
        //     description: demandData.description,
        //     status: demandData.status,
        //     item: item,
        //     customer: customer,
        //     location: location,
        //     quantity: demandData.quantity,
        //     minshipment: demandData.minshipment,
        //     due: demandData.due,
        //     maxlateness: demandData.maxlateness / 86400,
        //     problems: demandData.problems || [],
        //     constraints: demandData.constraints || [],
        //     pegging: demandData.pegging || [],
        //     pegging_first_level: demandData.pegging_first_level || [],
        //     delay: demandData.delay,
        //     planned_quantity: demandData.planned_quantity
        //   });
        // }
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
        // this.gridRefreshEvent();
      }
    },

    // async quoteQuote() {
    //   this.loading = true;
    //   this.error = null;
    //
    //   try {
    //     const quoteData = [{
    //       name: this.quote.name,
    //       quantity: this.quote.quantity,
    //       description: this.quote.description || '',
    //       due: new Date(this.quote.due).toISOString(),
    //       item: {name: this.quote.item.name},
    //       location: {name: this.quote.location.name},
    //       customer: {name: this.quote.customer.name},
    //       minshipment: this.quote.minshipment,
    //       maxlateness: this.quote.maxlateness * 86400,
    //       priority: 20
    //     }];
    //
    //     const response = await quoteService.quoteQuote(quoteData);
    //     const {responseData} = response;
    //
    //     if (responseData.value?.demands?.[0]) {
    //       const demandData = responseData.value.demands[0];
    //
    //       // Extract string values for item, customer, location
    //       const item = typeof demandData.item === 'string'
    //         ? demandData.item
    //         : (demandData.item?.name || '');
    //
    //       const customer = typeof demandData.customer === 'string'
    //         ? demandData.customer
    //         : (demandData.customer?.name || '');
    //
    //       const location = typeof demandData.location === 'string'
    //         ? demandData.location
    //         : (demandData.location?.name || '');
    //
    //       this.updateQuote({
    //         name: demandData.name,
    //         description: demandData.description,
    //         status: demandData.status,
    //         item: item,
    //         customer: customer,
    //         location: location,
    //         quantity: demandData.quantity,
    //         minshipment: demandData.minshipment,
    //         due: demandData.due,
    //         maxlateness: demandData.maxlateness / 86400,
    //         problems: demandData.problems || [],
    //         constraints: demandData.constraints || [],
    //         pegging: demandData.pegging || [],
    //         pegging_first_level: demandData.pegging_first_level || [],
    //         delay: demandData.delay,
    //         planned_quantity: demandData.planned_quantity
    //       });
    //     }
    //   } catch (error) {
    //     this.error = error.message;
    //     throw error;
    //   } finally {
    //     this.loading = false;
    //     this.gridRefreshEvent();
    //   }
    // },
    //
    // async cancelQuote() {
    //   this.loading = true;
    //   this.error = null;
    //
    //   try {
    //     await quoteService.cancelQuote(this.quote.name);
    //     this.resetQuote();
    //   } catch (error) {
    //     this.error = error.message;
    //     throw error;
    //   } finally {
    //     this.loading = false;
    //     this.gridRefreshEvent();
    //   }
    // },
    //
    // async confirmQuote() {
    //   this.loading = true;
    //   this.error = null;
    //
    //   try {
    //     const quoteData = [{
    //       name: this.quote.name,
    //       problems: this.quote.problems,
    //       operationplans: this.quote.operationplans
    //     }];
    //
    //     const response = await quoteService.confirmQuote(quoteData);
    //     const {responseData} = response;
    //
    //     if (responseData.value?.demands?.[0]) {
    //       const demandData = responseData.value.demands[0];
    //
    //       // Extract string values for item, customer, location
    //       const item = typeof demandData.item === 'string'
    //         ? demandData.item
    //         : (demandData.item?.name || '');
    //
    //       const customer = typeof demandData.customer === 'string'
    //         ? demandData.customer
    //         : (demandData.customer?.name || '');
    //
    //       const location = typeof demandData.location === 'string'
    //         ? demandData.location
    //         : (demandData.location?.name || '');
    //
    //       this.updateQuote({
    //         name: demandData.name,
    //         description: demandData.description,
    //         status: demandData.status,
    //         item: item,
    //         customer: customer,
    //         location: location,
    //         quantity: demandData.quantity,
    //         minshipment: demandData.minshipment,
    //         due: demandData.due,
    //         maxlateness: demandData.maxlateness / 86400,
    //         problems: demandData.problems || [],
    //         constraints: demandData.constraints || [],
    //         pegging: demandData.pegging || [],
    //         pegging_first_level: demandData.pegging_first_level || [],
    //         delay: demandData.delay,
    //         planned_quantity: demandData.planned_quantity
    //       });
    //     }
    //   } catch (error) {
    //     this.error = error.message;
    //     throw error;
    //   } finally {
    //     this.loading = false;
    //     this.gridRefreshEvent();
    //   }
    // },
    //
    // async infoQuote() {
    //   this.loading = true;
    //   this.error = null;
    //   console.log("Calling info quote", this.quote.name);
    //
    //   try {
    //     const response = await quoteService.infoQuote(this.quote.name);
    //     const {responseData} = response;
    //
    //     if (responseData.value?.demands?.[0]) {
    //       const demandData = responseData.value.demands[0];
    //
    //       // Extract string values for item, customer, location
    //       const item = typeof demandData.item === 'string'
    //         ? demandData.item
    //         : (demandData.item?.name || '');
    //
    //       const customer = typeof demandData.customer === 'string'
    //         ? demandData.customer
    //         : (demandData.customer?.name || '');
    //
    //       const location = typeof demandData.location === 'string'
    //         ? demandData.location
    //         : (demandData.location?.name || '');
    //
    //       // Update the quote with resolved string values
    //       this.updateQuote({
    //         name: demandData.name,
    //         description: demandData.description,
    //         status: demandData.status,
    //         item: item,
    //         customer: customer,
    //         location: location,
    //         quantity: demandData.quantity,
    //         minshipment: demandData.minshipment,
    //         due: demandData.due,
    //         maxlateness: demandData.maxlateness / 86400,
    //         problems: demandData.problems || [],
    //         constraints: demandData.constraints || [],
    //         pegging: demandData.pegging || [],
    //         pegging_first_level: demandData.pegging_first_level || [],
    //         delay: demandData.delay,
    //         planned_quantity: demandData.planned_quantity
    //       });
    //     } else {
    //       console.error("No demand data found in response:", responseData.value);
    //     }
    //   } catch (error) {
    //     console.error("Error in infoQuote:", error);
    //     this.error = error.message;
    //   } finally {
    //     this.loading = false;
    //     this.gridRefreshEvent();
    //   }
    // },
    //
    // async fetchQuoteData(endpoint) {
    //   this.loading = true;
    //   try {
    //     const {backendData} = await quoteService.fetchQuoteData(endpoint);
    //
    //     if (backendData.value?.rows?.length > 0) {
    //       const data = backendData.value.rows[0];
    //       this.updateQuote(data);
    //     }
    //   } catch (error) {
    //     this.error = error.message;
    //   } finally {
    //     this.loading = false;
    //     this.gridRefreshEvent();
    //   }
    // },
    //
    // updateQuote(data) {
    //   this.quote = {
    //     ...this.quote,
    //     name: data.name,
    //     description: data.description,
    //     item: {name: data.item},
    //     customer: {name: data.customer},
    //     location: {name: data.location},
    //     quantity: parseFloat(data.quantity),
    //     minshipment: parseFloat(data.minshipment),
    //     due: data.due,
    //     maxlateness: data.maxlateness,
    //     status: data.status,
    //     pegging: data.pegging || [],
    //     pegging_first_level: data.pegging_first_level || [],
    //     problems: data.problems || [],
    //     constraints: data.constraints || []
    //   };
    // },
    //
    // resetQuote() {
    //   this.quote = {
    //     name: '',
    //     description: '',
    //     item: {name: ''},
    //     customer: {name: ''},
    //     location: {name: ''},
    //     quantity: null,
    //     minshipment: null,
    //     due: null,
    //     maxlateness: null,
    //     status: '',
    //     pegging: [],
    //     pegging_first_level: [],
    //     problems: [],
    //     constraints: []
    //   };
    //   this.peglevel = 0;
    //   this.error = null;
    // },
    //
    // increasePegLevel() {
    //   if (this.canIncreasePegLevel) {
    //     this.peglevel++;
    //   }
    // },
    //
    // decreasePegLevel() {
    //   if (this.canDecreasePegLevel) {
    //     this.peglevel--;
    //   }
    // },
    //
    // setQuoteProperty(property, value) {
    //   console.log(96, property, value, this.quote[property]);
    //   if (property === 'item') {
    //     this.quote[property] = {name: value};
    //   } else if (property === 'customer') {
    //     this.quote[property] = {name: value};
    //   } else if (property === 'location') {
    //     this.quote[property] = {name: value};
    //   } else if (property === 'maxllateness') {
    //     this.quote[property] = {name: value};
    //   } else {
    //     this.quote[property] = value;
    //   }
    // },
    //
    // gridRefreshEvent() {
    //   const event = new CustomEvent('gridRefresh', {
    //     bubbles: true,
    //     cancelable: true
    //   });
    //
    //   window.dispatchEvent(event);
    // }
  },
})

