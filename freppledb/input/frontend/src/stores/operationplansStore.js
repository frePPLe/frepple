/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

import {toRaw} from "vue";
import {operationplanService} from "@/services/operationplanService.js";7

/**
 * @typedef {Object} OperationplansState
 * @property {string} mode - Display mode: 'table', 'kanban', 'gantt', or 'calendar*'
 * @property {string} calendarmode - Calendar mode: 'day', 'week', or 'month'
 * @property {string} grouping - Grouping configuration
 * @property {string} groupingdir - Grouping direction: 'asc' or 'desc'
 * @property {boolean} showTop - Show top level operations
 * @property {boolean} showChildren - Show child level operations
 * @property {Array} operationplan - single operationplans
 // * @property {Array} operationplans - object with operationplans with id as key // {id: operationplan}
 * @property {Array} selectedOperationplans - Multiple selected operationplans   // list of ids
 * @property {boolean} loading - Loading state
 * @property {Object} error - Error state
 * @property {number} dataRowHeight - Row height for table
 * @property {Object} preferences - User preferences
 * @property {Date} horizonstart - Start date of planning horizon
 * @property {Date} horizonend - End date of planning horizon
 * @property {Date} viewstart - Start date of current view
 * @property {Date} viewend - End date of current view
 * @property {Date} currentdate - Current date
 * @property {string} currentFilter - Current search/filter
 * @property {string} sidx
 * @property {string} sord
 * @property {string} width
 * @property {string} detailWidth
 */

import { defineStore } from 'pinia';
import {Operationplan} from "@/models/operationplan.js";

const moment = window.moment;
const datetimeformat = window.datetimeformat;

export const useOperationplansStore = defineStore('operationplans', {
  state: () => ({
    // Data
    operationplan: new Operationplan(),
    operationplans: {},
    selectedOperationplans: [],

    // Preferences
    preferences: {},

    mode: 'table',
    calendarmode: 'month',
    grouping: null,
    groupingdir: 'asc',
    showTop: true,
    showChildren: true,
    page: 1,
    rows: [],    // table columns to be (de)selected
    frozen: 0,
    currentFilter: '', // preferences.favorites
    widgets: [],
    sidx: 'batch',
    sord: 'asc',
    favorites: [],  // for filters
    segment: "",
    columns: [], // ['proposed', 'approved', 'confirmed', 'completed', 'closed']

    // UI state
    loading: false,
    error: { title: "", showError: false, message: "", details: "", type: "error" },
    dataRowHeight: null,
    width: 300,
    detailwidth: 300,
    height: 300,

    // Calendar
    horizonstart: new Date(),
    horizonend: new Date(),
    viewstart: new Date(),
    viewend: new Date(),
    currentdate: new Date(),

    // Kanban
    kanbanoperationplans: [],
    kanbancolumns: [],
    ganttoperationplans: [],
    calendarevents: [],
  }),

  getters: {
    isTableMode: () => this.mode === 'table',
    isKanbanMode: () => this.mode === 'kanban',
    isGanttMode: () => this.mode === 'gantt',
    isCalendarMode: () => this.mode.startsWith('calendar'),

    hasSelected: () => this.selectedOperationplans.length > 0,

    getPreferences(state) {
      state.preferences = window.preferences;
    },
  },

  actions: {
    // Display mode actions
    setMode(newMode) {
      this.mode = newMode;
      this.preferences.mode = newMode;
    },

    setCalendarMode(newCalendarMode) {
      this.calendarmode = newCalendarMode;
      this.preferences.calendarmode = newCalendarMode;
    },

    async loadOperationplans(references = [], selectedFlag, selectedRows) {
      if (references.length === 0) return;
      console.log(120, toRaw(references), selectedFlag, toRaw(selectedRows));
      this.selectedOperationplans.length = 0
      this.selectedOperationplans.push(...selectedRows);
      if (selectedFlag === false) {
        if (this.selectedOperationplans.length === 1) {
          console.log(126, this.selectedOperationplans[0]);
          await this.loadOperationplans(selectedRows, true, selectedRows);
          // const parsedId = parseInt(selectedRows[0]);
          // this.operationplan.id = isNaN(parsedId) ? -1 : parsedId;
        }
      } else {
        console.log(134, 'loadOperationplans: ', references, toRaw(this.selectedOperationplans));
        this.operationplan = new Operationplan();
        this.loading = true;
        this.error.showError = false;
        const operationplanReference = references[0];

        try {
          const response = await operationplanService.getOperationplanDetails({
            reference: operationplanReference
          });

          // Update the store with the fetched data
          const operationplan = toRaw(response.responseData.value)[0];
          if (this.selectedOperationplans.length === 1) {
            console.log(135, operationplan, parseInt(operationplanReference));

            this.operationplan = new Operationplan(operationplan);
            // const parsedId = parseInt(operationplanReference);
            // this.operationplan.id = isNaN(parsedId) ? -1 : parsedId;
          } else {
            console.log("152 aggregated info: ");
          // this.operationplan = new Operationplan({id: -1});
          this.operationplan = new Operationplan();
          }
        } catch (error) {
          this.error = {
            title: 'Failed to load operation plans',
            showError: true,
            message: error.response?.data?.message || 'An error occurred while loading operation plans',
            details: error.message,
            type: 'error'
          };
        } finally {
          this.loading = false;
        }
        // } else { //  calculate aggregated info
        //   this.operationplan = new Operationplan({id: -1});
        // }
      }
    },

    // Filter and search actions
    setCurrentFilter(filter) {
      this.currentFilter = filter;
      this.page = 1; // Reset to first page when filter changes
    },

    resetFilter() {
      this.currentFilter = '';
      this.page = 1;
      this.sidx = 'batch';
      this.sord = 'asc';
      this.preferences.sidx = 'batch';
      this.preferences.sord = 'asc';
    },

    // Preferences actions
    setPreference(key, value) {
      this.preferences[key] = value;
    },

    // Column management actions
    setColumns(columns) {
      this.columns = columns;
    },

    setFrozenColumns(frozen) {
      this.frozen = frozen;
    },

    // Calendar and view actions
    setViewRange(start, end) {
      this.viewstart = start;
      this.viewend = end;
    },

    setHorizonRange(start, end) {
      this.horizonstart = start;
      this.horizonend = end;
    },

    setCurrentDate(date) {
      this.currentdate = date;
    },

    // Initialize store with preferences
    async initialize() {
      // Load preferences from localStorage if available
      const savedPreferences = localStorage.getItem('operationplansPreferences');
      if (savedPreferences) {
        try {
          const parsedPrefs = JSON.parse(savedPreferences);
          this.preferences = { ...this.preferences, ...parsedPrefs };
        } catch (e) {
          console.warn('Failed to parse saved preferences:', e);
        }
      }

      // Apply saved preferences to UI state
      if (this.preferences.mode) this.mode = this.preferences.mode;
      if (this.preferences.calendarmode) this.calendarmode = this.preferences.calendarmode;
      if (this.preferences.grouping) this.grouping = this.preferences.grouping;
      if (this.preferences.groupingdir) this.groupingdir = this.preferences.groupingdir;
      if (this.preferences.sidx) this.sidx = this.preferences.sidx;
      if (this.preferences.sord) this.sord = this.preferences.sord;

      // Load initial data
      await this.loadOperationplans();
    },

    setShowTop(value) {
      this.showTop = value;
      if (!this.preferences) this.preferences = {};
      this.preferences.showTop = value;
    },

    setShowChildren(value) {
      this.showChildren = value;
      if (!this.preferences) this.preferences = {};
      this.preferences.showChildren = value;
    },

    setDataRowHeight(height) {
      this.dataRowHeight = height;
      if (!this.preferences) this.preferences = {};
      this.preferences.height = height;
    },

    setViewDates(startDate, endDate) {
      this.viewstart = new Date(startDate);
      this.viewend = new Date(endDate);
    },

    // Selection actions
    selectMultipleOperationplans(operationplans) {
      console.log(240, 'selectMultipleOperationplans: ', operationplans);
      // this.selectedOperationplans = operationplans;
    },

    clearSelection() {
      this.selectedOperationplan = null;
      this.selectedOperationplans = [];
    },

    setCalendarEvents(events) {
      this.calendarevents = events;
    },

    // Preferences
    setPreferences(preferences) {
      this.preferences = preferences;
    },

    async savePreferences() {
      this.loading = true;
      this.clearError();
      try {
        // Update preferences with current mode settings
        this.preferences.mode = this.mode;
        this.preferences.calendarmode = this.calendarmode;
        this.preferences.grouping = this.grouping;
        this.preferences.groupingdir = this.groupingdir;
        this.preferences.showTop = this.showTop;
        this.preferences.showChildren = this.showChildren;
        if (this.dataRowHeight !== null) {
          this.preferences.height = this.dataRowHeight;
        }

        // Call your backend service here if needed
        // const result = await operationplanService.savePreferences(this.preferences);
        await operationplanService.savePreferences({ "freppledb.input.views.manufacturing.ManufacturingOrderList": this.preferences });

        console.log('Preferences saved:', this.preferences);
      } catch (error) {
        this.setError({
          title: 'Error',
          message: 'Unable to save preferences',
          details: error.message || '',
          type: 'error',
        });
      } finally {
        this.loading = false;
      }
    },

    // Error handling
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
    },

    // Display info for selected operationplans
    displayInfo(operationplan) {
      this.selectedOperationplan = operationplan;
    },

    // Process aggregated info for multiple selections
    processAggregatedInfo(operationplans, colModel) {
      this.selectedOperationplans = operationplans;
      console.log(260, 'processAggregatedInfo: ', operationplans, colModel);

      const aggColModel = [];
      const aggregatedopplan = {colmodel: {}};
      let temp;

      colModel.forEach((modelValue, key) => {
        if (Object.prototype.hasOwnProperty.call(modelValue, 'summaryType')) {
          aggColModel.push([key, modelValue.name, modelValue.summaryType, modelValue.formatter]);
          aggregatedopplan[modelValue.name] = null;
          aggregatedopplan.colmodel[modelValue.name] = {
            'type': modelValue.summaryType,
            'label': modelValue.label,
            'formatter': modelValue.formatter
          };
        }
      });

      const dateKeys  = new Set(["enddate", "startdate"]);

      operationplans.forEach((opplan) => {
        aggColModel.forEach((field) => {
          if (field[2] === 'sum') {
            if (field[3] === 'duration') {
              temp = new moment.duration(opplan[field[1]]).asSeconds();
              if (temp._d !== 'Invalid Date') {
                if (aggregatedopplan[field[1]] === null)
                  aggregatedopplan[field[1]] = temp;
                else
                  aggregatedopplan[field[1]] += temp;
              }
            }
            else if (!isNaN(parseFloat(opplan[field[1]]))) {
              if (aggregatedopplan[field[1]] === null) {
                aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
              } else {
                aggregatedopplan[field[1]] += parseFloat(opplan[field[1]]);
              }
            }
          } else if (field[2] === 'max') {

            if (['color', 'number', 'currency'].indexOf(field[3]) !== -1 && opplan[field[1]] !== "") {
              if (parseFloat(opplan[field[1]])) {
                if (aggregatedopplan[field[1]] === null) {
                  aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
                } else {
                  aggregatedopplan[field[1]] = Math.max(aggregatedopplan[field[1]], parseFloat(opplan[field[1]]));
                }
              }
            } else if (field[3] === 'duration') {
              temp = new moment.duration(opplan[field[1]]).asSeconds();
              if (temp._d !== 'Invalid Date') {
                if (aggregatedopplan[field[1]] === null) {
                  aggregatedopplan[field[1]] = temp;
                } else {
                  aggregatedopplan[field[1]] = Math.max(aggregatedopplan[field[1]], temp);
                }
              }
            } else if (field[3] === 'date') {
              temp = new moment(opplan[field[1]], datetimeformat);
              if (temp._d !== 'Invalid Date') {
                console.log(415, temp, aggregatedopplan[field[1]]);
                if (aggregatedopplan[field[1]] === null || temp.isAfter(aggregatedopplan[field[1]]))
                  aggregatedopplan[field[1]] = temp;
              }
            }

          } else if (field[2] === 'min') {

            if (['color', 'number'].indexOf(field[3]) !== -1 && opplan[field[1]] !== "") {
              temp = parseFloat(opplan[field[1]]);
              if (!isNaN(temp)) {
                if (aggregatedopplan[field[1]] === null) {
                  aggregatedopplan[field[1]] = temp;
                } else {
                  aggregatedopplan[field[1]] = Math.min(aggregatedopplan[field[1]], temp);
                }
              }
            } else if (field[3] === 'duration') {
              temp = new moment.duration(opplan[field[1]]).asSeconds();
              if (temp._d !== 'Invalid Date') {
                if (aggregatedopplan[field[1]] === null) {
                  aggregatedopplan[field[1]] = temp;
                } else {
                  aggregatedopplan[field[1]] = Math.min(aggregatedopplan[field[1]], temp);
                }
              }
            } else if (field[3] === 'date') {
              dateKeys.add(field[1]);
              temp = new moment(opplan[field[1]], datetimeformat);
              console.log(442, temp);
              if (temp._d !== 'Invalid Date') {
                if (aggregatedopplan[field[1]] === null) {
                  aggregatedopplan[field[1]] = temp;
                } else {
                  aggregatedopplan[field[1]] = moment.min(aggregatedopplan[field[1]], temp);
                }
              }
            }

          }

        });
      });
      console.log(460, 'dateKeys: ', dateKeys);
      dateKeys.forEach((key) => {
        aggregatedopplan[key] = aggregatedopplan[key].format('YYYY-MM-DD[T]HH:mm:ss');
      })

      // aggregatedopplan.start = aggregatedopplan.startdate.format('YYYY-MM-DD[T]HH:mm:ss');
      // aggregatedopplan.end = aggregatedopplan.enddate.format('YYYY-MM-DD[T]HH:mm:ss');

      console.log(262, 'aggColModel: ', aggregatedopplan);
      // this.operationplan = new Operationplan(aggregatedopplan, aggColModel)
      this.operationplan = new Operationplan(aggregatedopplan);
    },

    setEditFormValues(field, value) {
      console.log(491, 'setEditFormValues: ', field, value);
    },

    applyOperationplanChanges() {
      console.log(465, 'applyOperationplanChanges');
    }
  }
})
