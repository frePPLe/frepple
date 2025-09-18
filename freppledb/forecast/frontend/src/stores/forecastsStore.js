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
 * @property {boolean} loading
 * @property {string|null} error
 * @property {Object} treeExpansion
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
    treeBuckets: [],
    treeExpansion: {item: {0: new Set()}, location: {0: new Set()}, customer: {0: new Set()}},
    currentSequence: null,
    currentMeasure: null,
    loading: false,
    error: null,
    dataRowHeight: null
  }),

  getters: {
    measures: () => window.measures,
    preferences: () => window.preferences
  },

  actions: {
    async setCurrentMeasure(measure, save = true) {
      console.log('setCurrentSequence', this.currentSequence,'setCurrentMeasure', measure, save);
      if (this.currentMeasure === measure) return;
      this.currentMeasure = measure;
      if (this.currentSequence === null) return;
      this.itemTree = await this.getItemtree();
      this.itemTree[0].expanded = 1;
      this.locationTree = await this.getLocationtree();
      this.locationTree[0].expanded = 1;
      this.customerTree = await this.getCustomertree();
      this.customerTree[0].expanded = 1;
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
      if (save) await this.savePreferences();
    },

    setCurrentHeight(height) {
      this.dataRowHeight = height;
      console.log('setDataRowHeight', height);
    },

    async setItemLocationCustomer(model, objectName, hasChildren, lvl, isExpanded = false) {
      // This function will get the tree values according to the panel ordering
      // and also add get from the backend the leafs/children of the tree.
      let newData = [];
      // console.log('86 setItemLocationCustomer', model, objectName, asChildren, isExpanded);
      this[model].name = objectName;
      const modelSequence = this.currentSequence.split("").map(x => (x === 'I' ? 'item' : (x === 'L' ? 'location' : 'customer')));

      let getTree = false;
      const rootParameters = {item: null, location: null, customer: null};
      const childrenParameters = {item: null, location: null, customer: null};
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
        rootParameters[m] = this[m].name;
        if (m === model) {
          getTree = true;
          childrenParameters[m] = objectName;
        } else {
          childrenParameters[m] = this[m].name;
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
            this.customer.splice(insertIndex, 0, ...newData);

            if (!Object.prototype.hasOwnProperty.call(this.treeExpansion.customer, lvl)) {
              this.treeExpansion.customer[lvl] = new Set();
            }
            this.treeExpansion.customer[lvl].add(objectName);
            break;
          default:
            break;
        }
      }

      await this.savePreferences();
    },

    async getItemtree(itemName = null, locationName = null, customerName= null) {
      this.loading = true;
      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure, itemName, locationName, customerName );

        // Use the promise-like behavior of the composable
        const result = await forecastService.getItemtree(this.currentMeasure, itemName, locationName, customerName);

        // The result now contains the resolved refs with data
        const {loading, backendError, responseData} = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          this.treeBuckets = result[0].values.map(x => x['bucketname']);

          if (result[0]['lvl'] === 0) {
            this.item.name = result[0].item;
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

    async getLocationtree(itemName = null, locationName = null, customerName= null) {
      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure, itemName, locationName, customerName);

        // Use the promise-like behavior of the composable
        const result = await forecastService.getLocationtree(this.currentMeasure, itemName, locationName, customerName);

        // The result now contains the resolved refs with data
        const {loading, backendError, responseData} = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          console.log('Data successfully loaded:', this.locationTree);

          if (result[0]['lvl'] === 0) {
            this.location.name = result[0].location;
            if (result[0]['children']) {
              this.treeExpansion.location[0].add(result[0].location);
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

    async getCustomertree(itemName = null, locationName = null, customerName= null) {

      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure, itemName, locationName, customerName);

        const result = await forecastService.getCustomertree(this.currentMeasure, itemName, locationName, customerName);

        const {loading, backendError, responseData} = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          console.log('Data successfully loaded:', this.customerTree);

          if (result[0]['lvl'] === 0) {
            this.customer.name = result[0].customer;
            if (result[0]['children']) {
              this.treeExpansion.customer[0].add(result[0].customer);
              result[0]['expanded'] = 1;
            }
          }

          return result;
        } else {
          console.warn('⚠️ No data received from API');
          return  {};
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async savePreferences() {
      this.loading = true;
      this.error = null;
      console.log('76', this.currentSequence, this.currentMeasure);
      this.preferences.sequence = this.currentSequence;
      this.preferences.measure = this.currentMeasure;

      try {
        const result = await forecastService.savePreferences({"freppledb.forecast.planning": this.preferences});

        const {loading, backendError, responseData} = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          console.log('Preferences saved', this.itemTree);
        } else {
          console.warn('Preferences not saved');
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
  },
})
