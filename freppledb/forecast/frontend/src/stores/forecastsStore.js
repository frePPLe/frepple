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
 */

import { defineStore } from 'pinia';
import { Item } from '../models/item.js';
import { Location } from '../models/location.js';
import { Customer } from '../models/customer.js';
import { Measure } from '../models/measure.js';
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
    currentSequence: null,
    currentMeasure: null,
    loading: false,
    error: null,
    dataRowHeight: null
  }),

  getters: {
    measures: () => window.measures,
    preferences: () => window.preferences,
    // computedItemTree: state => state.itemTree,
    // computedLocationTree: state => state.locationTree,
    // computedCustomerTree: state => state.customerTree,
  },

  actions: {
    setCurrentMeasure(measure, save = true) {
      console.log('setCurrentSequence', this.currentSequence,'setCurrentMeasure', measure, save);
      if (this.currentMeasure === measure) return;
      this.currentMeasure = measure;
      if (this.currentSequence === null) return;
      this.getItemtree();
      this.getLocationtree();
      this.getCustomertree();
      if (save) this.savePreferences();
    },

    setCurrentSequence(sequence, save = true) {
      console.log('setCurrentSequence', sequence, 'setCurrentMeasure', this.currentMeasure, save);
      if (this.currentSequence === sequence) return;
      this.currentSequence = sequence;
      if (this.currentMeasure === null) return;
      this.getItemtree();
      this.getLocationtree();
      this.getCustomertree();
      if (save) this.savePreferences();
    },

    setCurrentHeight(height) {
      this.dataRowHeight = height;
      console.log('setDataRowHeight', height);
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

    async getItemtree() {
      this.loading = true;
      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure);

        // Use the promise-like behavior of the composable
        const result = await forecastService.getItemtree(this.currentMeasure);

        // The result now contains the resolved refs with data
        const {loading, backendError, responseData} = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          const result = toRaw(responseData.value);
          this.treeBuckets = result[0].values.map(x => x['bucketname']);
          this.itemTree = result;
          console.log('Data successfully loaded:', this.itemTree, result);
        } else {
          console.warn('⚠️ No data received from API');
          this.itemTree = {};
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getLocationtree() {
      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure);

        // Use the promise-like behavior of the composable
        const result = await forecastService.getLocationtree(this.currentMeasure);

        // The result now contains the resolved refs with data
        const {loading, backendError, responseData} = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          this.locationTree = toRaw(responseData.value);
          console.log('Data successfully loaded:', this.locationTree);
        } else {
          console.warn('⚠️ No data received from API');
          this.locationTree = {};
        }

      } catch (error) {
        console.error('API Error:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getCustomertree() {

      this.error = null;

      try {
        console.log('Calling API with measure:', this.currentMeasure);

        const result = await forecastService.getCustomertree(this.currentMeasure);

        const {loading, backendError, responseData} = result;
        this.loading = loading;

        if (backendError) {
          throw new Error(backendError.value.message || 'API Error');
        }

        if (responseData.value) {
          this.customerTree = toRaw(responseData.value);
          console.log('Data successfully loaded:', this.customerTree);
        } else {
          console.warn('⚠️ No data received from API');
          this.customerTree = {};
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
