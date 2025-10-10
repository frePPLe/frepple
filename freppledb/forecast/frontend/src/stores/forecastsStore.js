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
 * @property {string|null} error
 * @property {number} dataRowHeight
 * @property {Object} bucketChanges
 * @property {Array} history
 * @property {Array} comments
 * @property {string} commentType
 * @property {string} newComment
 * @property {string} originalComment
 * @property {boolean} hasChanges
 * @property {boolean} forecastAttributes
 * @property {boolean} currency
 * @property {Object} editForm
 */

import {defineStore} from 'pinia';
import {Item} from '../models/item.js';
import {Location} from '../models/location.js';
import {Customer} from '../models/customer.js';
import {forecastService} from '../services/forecastService.js';
import {toRaw} from "vue";

export const useForecastsStore = defineStore('forecasts', {
    state: () => ({
      item: new Item(),
      location: new Location(),
      customer: new Customer(),
      itemTree: {},
      locationTree: {},
      customerTree: {},
      treeBuckets: [], // bucket labels for selection cards
      treeExpansion: {item: {0: new Set()}, location: {0: new Set()}, customer: {0: new Set()}},
      currentSequence: null,
      currentMeasure: null,
      currentBucket: null,
      preselectedBucketIndexes: [],
      loading: false,
      error: null,
      dataRowHeight: null,
      showTab: 'attributes',
      bucketChanges: {}, // buckets changed in the UI
      history: [],
      comments: [],
      commentType: '',
      newComment: '',
      originalComment: '',
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
    }),

    getters: {
      measures: () => window.measures,
      preferences: () => window.preferences,
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
          const {loading, backendError, responseData} = result;
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
          const {loading, backendError, responseData} = result;
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

          const {loading, backendError, responseData} = result;
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

          const {loading, backendError, responseData} = result;
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
        this.newComment = '';
        this.originalComment = '';
        this.hasChanges = false;
      },

      updateCommentContent(content) {
        this.newComment = content;
        this.hasChanges = content !== this.originalComment;
      },

      async saveComment() {
        console.log('Saving comment:', this.newComment, 'for type:', this.commentType);
        this.originalComment = this.newComment;

        await this.saveForecastChanges(false);
        this.hasChanges = false;
      },

      async undo() {
        this.newComment = "";
        this.commentType = "";
        this.forecastAttributes.forecastmethod = this.forecastAttributes.oldForecastmethod;
        this.hasChanges = false;
      },

      getBucketIndexesFromFormDates() {
        let bucketIndexes = [];

        for (const bckt in this.buckets) {
          const bucketStartDate = new Date(this.buckets[bckt]["startdate"]);
          const bucketEndDate = new Date(this.buckets[bckt]["enddate"]);
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

      setEditFormValues( field, value) {
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

      applyForecastChanges: function () {
        // Make custom changest to forecast
        const factor = 1 + this.editForm.increaseByPercent / 100.0;
        const msr = this.editForm.selectedMeasure.name;

        for (const bckt of this.getBucketIndexesFromFormDates()) {
          // console.log('448 bucket.startdate: ', this.buckets[bckt]["startdate"], ' UTC: ', bucketStartDate.getTime(), 'editForm.startDate: ', this.editForm.startDate, ' UTC: ', editFormStartDate.getTime());

          console.log('450 bucket.startdate: ', this.buckets[bckt]["startdate"], 'editForm.startDate: ', this.editForm.startDate);

          switch (this.editForm.mode) {
            case "set":
              this.buckets[bckt][msr] = msr.discrete ? Math.round(this.editForm.setTo) : this.editForm.setTo;
              break;
            case "increase":
              if (msr.name === "forecastoverride") {
                this.buckets[bckt][msr] =
                  msr.discrete ? Math.round(this.buckets[bckt]["forecasttotal"] + this.editForm.increaseBy) : this.buckets[bckt]["forecasttotal"] + this.editForm.increaseBy;
              } else {
                this.buckets[bckt][msr] =
                  msr.discrete ? Math.round(this.buckets[bckt][msr] + this.editForm.increaseBy) : this.buckets[bckt][msr] + this.editForm.increaseBy;
              }
              break;
            case "increasePercent":
              if (msr.name === "forecastoverride") {
                this.buckets[bckt][msr] =
                  msr.discrete ? Math.round(this.buckets[bckt]["forecasttotal"] * factor) : this.buckets[bckt]["forecasttotal"] * factor;
              } else {
                this.buckets[bckt][msr] =
                  msr.discrete ? Math.round(this.buckets[bckt][msr] * factor) : this.buckets[bckt][msr] * factor;
              }
              break;
            default:
              break;
          }

          if (msr === "forecastoverride") {
            this.buckets[bckt]["forecasttotal"] =
              (this.buckets[bckt]["forecastoverride"] !== -1
                && this.buckets[bckt]["forecastoverride"] != null) ?
                this.buckets[bckt]["forecastoverride"] :
                this.buckets[bckt]["forecastbaseline"];
          }

          console.log(486, bckt);
          this.bucketChanges[bckt] = this.buckets[bckt];
          this.hasChanges = true;
          console.log(489, toRaw(this.bucketChanges[bckt]));

        }
      },

      async saveForecastChanges(recalculate = false) {
        console.log('Saving forecast changes');
        this.loading = true;
        this.error = null;
        const newData = {
          item: this.item.Name,
          location: this.location.Name,
          customer: this.customer.Name,
          comment: this.newComment,
          commentType: this.commentType,
          units: this.currentMeasure,
          horizon: this.horizon,
          buckets: Object.values(toRaw(this.bucketChanges)), //list of buckets not a dictionary
          horizonbuckets: this.horizonbuckets,
          forecastmethod: this.forecastAttributes.forecastmethod,
          recalculate: recalculate,
        };
        console.log(509, newData);
        try {
          const result = await forecastService.postForecastDetails(newData);

          const {loading, backendError, responseData} = result;

          this.loading = loading;

          if (backendError) {
            throw new Error(backendError.value.message || 'API Error in forecast changes');
          }

          if (responseData.value) {
            console.log('Forecast Changes saved', newData);
            this.hasChanges = false;
          } else {
            console.warn('Forecast changes not saved');
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
        // console.log('76 savePreferences ', this.currentSequence, this.currentMeasure, this.dataRowHeight);
        this.preferences.sequence = this.currentSequence;
        this.preferences.measure = this.currentMeasure;
        // Include height in preferences if it exists
        if (this.dataRowHeight !== null) {
          this.preferences.height = this.dataRowHeight;
        }

        try {
          const result = await forecastService.savePreferences({"freppledb.forecast.planning": this.preferences});

          const {loading, backendError, responseData} = result;
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
          console.error('API Error:', error);
          this.error = error.message;
          throw error;
        } finally {
          this.loading = false;
        }
      },

      setShowTab(tab) {
        this.showTab = tab;
      },
    },
  })
