/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

/**
 * @typedef {Object} ForecastsState
 * @property {Item} item
 * @property {Location} location
 * @property {Customer} customer
 * @property {Array} itemTree
 * @property {Array} locationTree
 * @property {Array} customerTree
 * @property {string} currentSequence
 * @property {string} currentMeasure
 * @property {string} currentBucket
 * @property {Array} preselectedBucketIndexes
 * @property {boolean} loading
 * @property {Object} error
 * @property {number} dataRowHeight
 * @property {Object} bucketChanges
 * @property {Array} history
 * @property {Array} comments
 * @property {string} commentType
 * @property {string} newComment
 * @property {boolean} hasChanges
 * @property {boolean} forecastAttributes
 * @property {boolean} currency
 * @property {Object} editForm
 * @property {Array} tableRows
 * @property {Boolean} showDescription
 */

import { defineStore } from 'pinia';
import { Item } from '../models/item.js';
import { Location } from '../models/location.js';
import { Customer } from '../models/customer.js';
import { forecastService } from '../services/forecastService.js';
import { toRaw } from "vue";

export const useForecastsStore = defineStore('forecasts', {
  state: () => ({
    item: new Item(),
    location: new Location(),
    customer: new Customer(),
    itemTree: {},
    locationTree: {},
    customerTree: {},
    treeBuckets: [], // bucket labels for selection cards
    treeExpansion: { item: { 0: new Set() }, location: { 0: new Set() }, customer: { 0: new Set() } },
    currentSequence: null,
    currentMeasure: null,
    currentBucket: null,
    preselectedBucketIndexes: [],
    loading: false,
    error: { title: "", showError: false, message: "", details: "", type: "error" },
    dataRowHeight: null,
    showTab: 'forecast',
    bucketChanges: {}, // buckets changed in the UI
    history: [],
    comments: [],
    commentType: '',
    newComment: '',
    hasChanges: false,
    horizon: 'week',
    buckets: [], // buckets arriving from backend
    horizonbuckets: 'week',
    forecastAttributes: {
      "oldForecastmethod": "aggregated",
      "forecastmethod": "",
      "forecast_out_method": "",
      "forecast_out_smape": 0
    },
    currency: [],
    editForm: {
      selectedMeasure: null,
      startDate: new Date().toISOString().split('T')[0], // Format as YYYY-MM-DD for date input
      endDate: new Date().toISOString().split('T')[0],   // Format as YYYY-MM-DD for date input
      mode: 'set', // 'set', 'increase', or 'increasePercent'
      setTo: 0.0,
      increaseBy: 0.0,
      increaseByPercent: 0.0
    },
    tableRows: [],
    showDescription: false,
  }),

  getters: {
    measures: () => window.measures,
    preferences(state) {
      const defaultMeasures = [
        'orderstotal3ago',
        'orderstotal2ago',
        'orderstotal1ago',
        'ordersadjustment1ago',
        'orderstotal',
        'ordersadjustment',
        'forecastbaseline',
        'forecastoverride',
        'ordersplanned',
        'forecastplanned',
        'forecasttotal',
      ];
      state.tableRows = window.preferences['rows'] === undefined ? defaultMeasures : window.preferences['rows'];
      state.showDescription = window.preferences['showdescription'] === undefined ? false : window.preferences['showdescription'];

      return window.preferences;
    },
    currentBucketName: () => window.currentbucket,
  },

  actions: {
    async setCurrentMeasure(measure, save = true) {
      console.log('setCurrentMeasure', this.currentSequence, 'setCurrentMeasure', measure, save);
      if (this.currentMeasure === measure) return;
      this.currentMeasure = measure;
      if (this.currentSequence === null) return;
      this.itemTree = await this.getItemtree();
      this.itemTree[0].expanded = 1;
      this.locationTree = await this.getLocationtree();
      this.locationTree[0].expanded = 1;
      this.customerTree = await this.getCustomertree();
      this.customerTree[0].expanded = 1;
      await this.getForecastDetails();
      if (save) await this.savePreferences();
    },

    async setCurrentSequence(sequence, save = true) {
      console.log('setCurrentSequence', sequence, 'setCurrentMeasure', this.currentMeasure, save);
      if (this.currentSequence === sequence) return;
      this.currentSequence = sequence;
      if (this.currentMeasure === null) return;
      this.itemTree = await this.getItemtree();
      this.itemTree[0].expanded = 1;
      this.locationTree = await this.getLocationtree();
      this.locationTree[0].expanded = 1;
      this.customerTree = await this.getCustomertree();
      this.customerTree[0].expanded = 1;
      await this.getForecastDetails();
      if (save) await this.savePreferences();
    },

    setCurrentHeight(height) {
      this.dataRowHeight = height;
      // Update preferences to persist the height
      this.preferences.height = height;
      console.log('setDataRowHeight', height);
    },

    async setItemLocationCustomer(model, objectAttributes, hasChildren, lvl, isExpanded = false) {
      // This function will get the tree values according to the panel ordering
      // and also add get from the backend the leafs/children of the tree.
      let newData = [];
      const objectName = objectAttributes.Name;
      this[model].Name = objectName;
      this[model].Description = objectAttributes.Description;
      const modelSequence = this.currentSequence.split("").map(x => (x === 'I' ? 'item' : (x === 'L' ? 'location' : 'customer')));
      console.log('129 setItemLocationCustomer', model, objectName, hasChildren, isExpanded);

      let getTree = false;
      const rootParameters = { item: null, location: null, customer: null };
      const childrenParameters = { item: null, location: null, customer: null };
      for (let m of modelSequence) {
        console.log(88, model, m, this.currentSequence);

        if (getTree) {
          switch (m) {
            case 'item':
              this.itemTree = await this.getItemtree(rootParameters['item'], rootParameters['location'], rootParameters['customer']);
              break;
            case 'location':
              this.locationTree = await this.getLocationtree(rootParameters['item'], rootParameters['location'], rootParameters['customer']);
              break;
            case 'customer':
              this.customerTree = await this.getCustomertree(rootParameters['item'], rootParameters['location'], rootParameters['customer']);
              break;
            default:
              break;
          }
        }
        rootParameters[m] = this[m].Name;
        if (m === model) {
          getTree = true;
          childrenParameters[m] = objectName;
        } else {
          childrenParameters[m] = this[m].Name;
        }
      }

      if (!isExpanded) {
        this.treeExpansion[model][lvl].delete(objectName);
        return;
      }

      if (hasChildren) {
        console.log(95, hasChildren);
        let insertIndex = 0;
        switch (model) {
          case 'item': {
            insertIndex = this.itemTree.findIndex(x => x.item === objectName) + 1;
            newData = await this.getItemtree(childrenParameters['item'], childrenParameters['location'], childrenParameters['customer']);
            console.log(99, newData);
            this.itemTree.splice(insertIndex, 0, ...newData);

            if (!Object.prototype.hasOwnProperty.call(this.treeExpansion.item, lvl)) {
              this.treeExpansion.item[lvl] = new Set();
            }
            this.treeExpansion.item[lvl].add(objectName);
            console.log(117, toRaw(this.treeExpansion))
            break;
          }
          case 'location':
            insertIndex = this.locationTree.findIndex(x => x.location === objectName) + 1;
            newData = await this.getLocationtree(childrenParameters['item'], childrenParameters['location'], childrenParameters['customer']);
            this.locationTree.splice(insertIndex, 0, ...newData);

            if (!Object.prototype.hasOwnProperty.call(this.treeExpansion.location, lvl)) {
              this.treeExpansion.location[lvl] = new Set();
            }
            this.treeExpansion.location[lvl].add(objectName);
            break;
          case 'customer':
            console.log(157, 'case customer');
            insertIndex = this.customerTree.findIndex(x => x.customer === objectName) + 1;
            newData = await this.getCustomertree(childrenParameters['item'], childrenParameters['location'], childrenParameters['customer']);
            this.customerTree.splice(insertIndex, 0, ...newData);

            if (!Object.prototype.hasOwnProperty.call(this.treeExpansion.customer, lvl)) {
              this.treeExpansion.customer[lvl] = new Set();
            }
            this.treeExpansion.customer[lvl].add(objectName);
            break;
          default:
            break;
        }
      }
      await this.getForecastDetails(childrenParameters['item'], childrenParameters['location'], childrenParameters['customer']);

      await this.savePreferences();
    },

    async getItemtree(itemName = null, locationName = null, customerName = null) {
      this.loading = true;
      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure, itemName, locationName, customerName);

        // Use the promise-like behavior of the composable
        const result = await forecastService.getItemtree(this.currentMeasure, itemName, locationName, customerName);

        // The result now contains the resolved refs with data
        const { loading, backendError, responseData } = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          this.treeBuckets = result[0].values.map(x => x['bucketname']);

          if (result[0]['lvl'] === 0) {
            this.item.Name = result[0].item;
            if (result[0]['children']) {
              this.treeExpansion.item[0].add(result[0].item);
              result[0]['expanded'] = 1;
            }
          }

          return result;
        } else {
          console.warn('⚠️ No data received from API');
          return {};
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getLocationtree(itemName = null, locationName = null, customerName = null) {
      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure, itemName, locationName, customerName);

        // Use the promise-like behavior of the composable
        const result = await forecastService.getLocationtree(this.currentMeasure, itemName, locationName, customerName);

        // The result now contains the resolved refs with data
        const { loading, backendError, responseData } = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          console.log('Data successfully loaded:', this.locationTree);

          if (result[0]['lvl'] === 0) {
            this.location.Name = result[0].location;
            if (result[0]['children']) {
              this.treeExpansion.location[0].add(result[0].location);
              result[0]['expanded'] = 1;
            }
          }

          return result;
        } else {
          console.warn('⚠️ No data received from API');
          store.setError({ title: "warning", error: null, message: "'⚠️ No data received from API'", details: "", type: "error" })
          return {};
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getCustomertree(itemName = null, locationName = null, customerName = null) {

      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure, itemName, locationName, customerName);

        const result = await forecastService.getCustomertree(this.currentMeasure, itemName, locationName, customerName);

        const { loading, backendError, responseData } = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          console.log('Data successfully loaded:', this.customerTree);

          if (result[0]['lvl'] === 0) {
            this.customer.Name = result[0].customer;
            if (result[0]['children']) {
              this.treeExpansion.customer[0].add(result[0].customer);
              result[0]['expanded'] = 1;
            }
          }

          return result;
        } else {
          console.warn('⚠️ No data received from API');
          return {};
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getForecastDetails(itemName = null, locationName = null, customerName = null) {

      this.error = null;

      try {
        console.log('Calling Details measure:', this.currentMeasure, itemName, locationName, customerName);

        const result = await forecastService.getForecastDetails(this.currentMeasure, itemName, locationName, customerName);

        const { loading, backendError, responseData } = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          console.log('Details successfully loaded:', result);

          this.item.update(result['attributes']['item']);
          this.location.update(result['attributes']['location']);
          this.customer.update(result['attributes']['customer']);
          this.comments = result['comments'];
          this.buckets = result['forecast'];
          this.forecastAttributes.forecastmethod = result['attributes']['forecast']['forecastmethod'];
          this.forecastAttributes.oldForecastmethod = result['attributes']['forecast']['forecastmethod'];
          this.forecastAttributes.forecast_out_method = result['attributes']['forecast']['forecast_out_method'];
          this.forecastAttributes.forecast_out_smape = result['attributes']['forecast']['forecast_out_smape'];
          this.currency.length = 0;
          this.currency.push(...result['attributes']['currency']);

          return result;
        } else {
          console.warn('⚠️ No data received from API');
          return {};
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async setForecastMethod(forecastMethod) {
      if (forecastMethod === this.forecastAttributes.oldForecastmethod) return;

      this.hasChanges = true;
      this.forecastAttributes.forecastmethod = forecastMethod;
    },

    setCommentType(newCommentType) {
      this.commentType = newCommentType;
    },

    updateCommentContent(content) {
      this.newComment = content;
      this.hasChanges = true;
    },

    async undo() {
      this.newComment = "";
      this.commentType = "";
      this.forecastAttributes.forecastmethod = this.forecastAttributes.oldForecastmethod;
      this.hasChanges = false;
      this.bucketChanges = {};
      await this.getForecastDetails(this.item.Name, this.location.Name, this.customer.Name);
    },

    getBucketIndexesFromFormDates() {
      let bucketIndexes = [];

      for (const bckt in this.buckets) {
        const bucketStartDate = new Date(this.buckets[bckt]["startdate"].replace(" ", 'T') + 'Z');
        const bucketEndDate = new Date(this.buckets[bckt]["enddate"].replace(" ", 'T') + 'Z');
        const editFormStartDate = new Date(this.editForm.startDate);
        const editFormEndDate = new Date(this.editForm.endDate);

        if (bucketStartDate.getTime() < editFormEndDate.getTime() &&
          bucketEndDate.getTime() > editFormStartDate.getTime()) {
          bucketIndexes.push(parseInt(bckt));
        }
        if (bucketStartDate > editFormEndDate)
          break;
      }
      return bucketIndexes;
    },

    setPreselectedBucketIndexes() {
      this.preselectedBucketIndexes.length = 0;
      this.preselectedBucketIndexes.push(...this.getBucketIndexesFromFormDates());
    },

    getBucketIndexFromName(bucketName) {
      if (!bucketName) return 0;
      return this.buckets.findIndex(bucket => bucket.bucket === bucketName);
    },

    setEditFormValues(field, value) {
      switch (field) {
        case "selectedMeasure":
          this.editForm.selectedMeasure = value;
          break
        case "startDate":
          this.editForm.startDate = value;
          break;
        case "endDate":
          this.editForm.endDate = value;
          break;
        case "setTo":
          this.editForm.setTo = value;
          break;
        case "mode":
          this.editForm.mode = value;
          break;
        case "increaseBy":
          this.editForm.increaseBy = value;
          break;
        case "increaseByPercent":
          this.editForm.increaseByPercent = value;
          break;
        default:
          break;
      }
    },

    logChange: function (bckt, msr, val) {
      this.buckets[bckt][msr] = val;
      if (bckt in this.bucketChanges) {
        this.bucketChanges[bckt][msr] = val;
      }
      else {
        this.bucketChanges[bckt] = {
          'bucket': this.buckets[bckt].bucket, [msr]: val
        };
      }
    },

    applyForecastChanges: function () {
      // Make custom changes to forecast
      const msr = this.editForm.selectedMeasure.name;
      for (const bckt of this.getBucketIndexesFromFormDates()) {
        switch (this.editForm.mode) {
          case "set":
            this.logChange(bckt, msr,
              msr.discrete ?
                Math.round(this.editForm.setTo) :
                this.editForm.setTo
            );
            break;
          case "increase":
            this.logChange(bckt, msr,
              msr.discrete ?
                Math.round(this.buckets[bckt][msr.name === "forecastoverride" ? "forecasttotal" : msr] + this.editForm.increaseBy) :
                this.buckets[bckt][msr.name === "forecastoverride" ? "forecasttotal" : msr] + this.editForm.increaseBy
            );
            break;
          case "increasePercent":
            const factor = 1 + this.editForm.increaseByPercent / 100.0;
            this.logChange(bckt, msr,
              msr.discrete ?
                Math.round(this.buckets[bckt][msr.name === "forecastoverride" ? "forecasttotal" : msr] * factor) :
                this.buckets[bckt][msr.name === "forecastoverride" ? "forecasttotal" : msr] * factor
            );
            break;
          default:
            return;
        }

        if (msr === "forecastoverride") {
          this.buckets[bckt]["forecasttotal"] =
            (this.buckets[bckt]["forecastoverride"] !== -1
              && this.buckets[bckt]["forecastoverride"] != null) ?
              this.buckets[bckt]["forecastoverride"] :
              this.buckets[bckt]["forecastbaseline"];
        }
        this.hasChanges = true;
      }
    },

    async saveForecastChanges(recalculate = false) {
      console.log('Saving forecast changes');
      this.loading = true;
      this.clearError();
      let newData = {
        item: this.item.Name,
        location: this.location.Name,
        customer: this.customer.Name,
        units: this.currentMeasure,
        horizon: this.horizon,
        buckets: Object.values(toRaw(this.bucketChanges)), //list of buckets not a dictionary
        horizonbuckets: this.horizonbuckets,
        forecastmethod: this.forecastAttributes.forecastmethod,
        recalculate: recalculate,
      };
      if (this.newComment != '') {
        newData.comment = this.newComment;
        newData.commenttype = this.commentType;
      }
      try {
        const result = await forecastService.postForecastDetails(newData);

        const { loading, backendError, responseData } = result;

        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error in forecast changes');
        }

        if (responseData.value) {
          console.log('Forecast Changes saved', newData);
          this.hasChanges = false;
          await this.getForecastDetails(this.item.Name, this.location.Name, this.customer.Name);
        } else {
          console.warn('Forecast changes not saved');
        }

      } catch (error) {
        console.error('API Error:', error);
        /*
        // Create detailed error information uncomment to activate full details
        let details = '';

        // Add stack trace if available
        if (error.stack) {
          details += `Stack Trace:\n${error.stack}\n\n`;
        }

        // Add axios response details if available
        if (error.response) {
          details += `HTTP Status: ${error.response.status}\n`;
          details += `Status Text: ${error.response.statusText}\n`;
          details += `Response Data: ${JSON.stringify(error.response.data, null, 2)}\n`;
          details += `Response Headers: ${JSON.stringify(error.response.headers, null, 2)}\n\n`;
        }

        // Add request details if available
        if (error.config) {
          details += `Request URL: ${error.config.url}\n`;
          details += `Request Method: ${error.config.method?.toUpperCase()}\n`;
          if (error.config.data) {
            details += `Request Data: ${JSON.stringify(JSON.parse(error.config.data), null, 2)}\n`;
          }
        }

        // Add any additional error properties
        if (error.code) {
          details += `Error Code: ${error.code}\n`;
        }
        */
        this.setError({
          title: 'Forecast Update Failed',
          message: 'Unable to apply forecast changes',
          // details: details || error.message,    // to see full trace uncomment this line and comment the next line.
          details: error.response?.data?.message || error.message,
          type: 'error'
        });
      } finally {
        this.loading = false;
      }
    },


    async savePreferences() {
      this.loading = true;
      this.error = null;
      // console.log('76 savePreferences ', this.currentSequence, this.currentMeasure, this.dataRowHeight);
      this.preferences.sequence = this.currentSequence;
      this.preferences.measure = this.currentMeasure;
      this.preferences.showdescription = this.showDescription;
      this.preferences.rows = this.tableRows;
      // Include height in preferences if it exists
      if (this.dataRowHeight !== null) {
        this.preferences.height = this.dataRowHeight;
      }

      try {
        const result = await forecastService.savePreferences({ "freppledb.forecast.planning": this.preferences });

        const { loading, backendError, responseData } = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          console.log('Preferences saved', this.preferences);
        } else {
          console.warn('Preferences not saved');
        }

      } catch (error) {
        console.log('API Error:', error);
        this.setError({
          title: 'Forecast Update Failed',
          message: 'Unable to apply forecast changes',
          details: error.response?.data?.message || error.message,
          type: 'error',
        });
      } finally {
        this.loading = false;
      }
    },

    setShowTab(tab) {
      this.showTab = tab;
    },

    setError(errorData) {
      this.error = {
        showError: true,
        title: errorData.title || 'Error',
        message: errorData.message || 'An error occurred',
        details: errorData.details || '',
        type: errorData.type || 'error'
      };
    },

    clearError() {
      this.error = {
        showError: false,
        message: '',
        details: '',
        type: 'error',
        title: ''
      };
    }
  }
})
