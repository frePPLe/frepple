/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

import {toRaw} from "vue";
import { defineStore } from 'pinia';
import {operationplanService} from "@/services/operationplanService.js";
import { Operationplan } from '@/models/operationplan.js';

/**
 * @typedef {Object} OperationplansState
 * @property {string} mode - Display mode: 'table', 'kanban', 'gantt', or 'calendar*'
 * @property {string} calendarmode - Calendar mode: 'day', 'week', or 'month'
 * @property {string} grouping - Grouping configuration
 * @property {string} groupingdir - Grouping direction: 'asc' or 'desc'
 * @property {boolean} showTop - Show top level operations
 * @property {boolean} showChildren - Show child level operations
 * @property {Array} operationplan - single operationplans
 * @property {Array} selectedOperationplans - Multiple selected operationplans   // list of ids
 * @property {Object} operationplanChanges - Multiple selected operationplans   // {{reference: {fields: values}}]
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

const moment = window.moment;
const datetimeformat = window.datetimeformat;

export const useOperationplansStore = defineStore('operationplans', {
  state: () => ({
    // Data
    operationplan: new Operationplan(),
    operationplans: {},
    selectedOperationplans: [],
    operationplanChanges: {},

    preferences: {},
    editForm: {quantity: null, startdate: "", enddate: "", remark: ""},

    mode: window.preferences?.mode || window.mode || 'table',
    calendarmode: 'month',
    grouping: null,
    groupingdir: 'asc',
    showTop: true,
    showChildren: true,
    page: 1,
    rows: [],    // table columns to be (de)selected
    frozen: 0,
    currentFilter: '', // preferences.favorites
    widgets: {},
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
    kanbanoperationplans: {},
    kanbancolumns: window.preferences?.columns || ["proposed", "approved", "confirmed", "completed", "closed"],
    groupBy: window.groupBy || 'status',
    groupOperator: window.groupOperator || 'eq',
    ganttoperationplans: [],
    calendarevents: [],
  }),

  getters: {
    isTableMode: (window) => window.mode === 'table',
    isKanbanMode: (window) => window.mode === 'kanban',
    isGanttMode: (window) => window.mode === 'gantt',
    isCalendarMode: (window) => window.mode.startsWith('calendar'),

    hasSelected: () => this.selectedOperationplans.length > 0,
    getMode(state) {
      state.mode = window.mode;
    },
    getPreferences(state) {
      state.preferences = window.preferences;
    },
  },

  actions: {
    initializeMode() {
      // Sync with window preferences on init
      this.mode = window.preferences?.mode || window.mode || 'table';
      console.log('Mode initialized to:', this.mode);
    },

    setMode(newMode) {
      this.mode = newMode;
      window.mode = newMode;
      if (window.preferences) {
        window.preferences.mode = newMode;
      }
      console.log('Store mode updated to:', newMode);
    },

    syncModeFromWindow() {
      if (window.mode && window.mode !== this.mode) {
        this.mode = window.mode;
        console.log('Synced mode from window:', this.mode);
      }
    },

    setCalendarMode(newCalendarMode) {
      this.calendarmode = newCalendarMode;
      this.preferences.calendarmode = newCalendarMode;
    },

    async loadOperationplans(references = [], selectedFlag, selectedRows, isDataSaved = false) {
      this.selectedOperationplans.length = 0
      this.selectedOperationplans.push(...toRaw(selectedRows));
      if (references.length === 0) {
        this.operationplan = new Operationplan();
      } else if (selectedFlag === false) {
        if (this.selectedOperationplans.length === 1) {
          await this.loadOperationplans(selectedRows, true, selectedRows);
        }
      // } else if ( this.operationplan.reference !== undefined && (references[0] === this.operationplan.reference.toString())) {
        // do nothing
      } else {
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
            this.operationplan = new Operationplan(operationplan);
          } else {
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
      }
      if (this.operationplanChanges[this.operationplan.reference] !== undefined && !window.isDataSaved) {
        for (const field in this.operationplanChanges[this.operationplan.reference]) {
          this.operationplan[field] = this.operationplanChanges[this.operationplan.reference][field];
        }
      }
    },

    async loadKanbanData(thefilter) {
      if (!thefilter) {
        thefilter = this.currentFilter || window.initialfilter;
      }

      const params = {
        format: 'kanban',
        sidx: this.sidx,
        sord: this.sord
      };

      for (const key of this.kanbancolumns) {
        let colfilter = thefilter ? JSON.parse(JSON.stringify(thefilter)) : undefined;
        const extrafilter = {
          field: this.groupBy,
          op: this.groupOperator,
          data: key,
        };
        if (colfilter === undefined || colfilter === null) {
          // First filter
          colfilter = {
            groupOp: "AND",
            rules: [extrafilter],
            groups: [],
          };
        } else {
          if (colfilter["groupOp"] === "AND")
            // Add condition to existing and-filter
            colfilter["rules"].push(extrafilter);
          else
            // Wrap existing filter in a new and-filter
            colfilter = {
              groupOp: "AND",
              rules: [extrafilter],
              groups: [colfilter],
            };
        }
        try {
          const { responseData } = await operationplanService.getKanbanData({
            ...params,
            filters: JSON.stringify(colfilter)
          });
          const tmp = responseData.value;
          for (const x of tmp.rows) {
            x.type =
              x.operationplan__type || x.type || window.default_operationplan_type;
            if (Object.prototype.hasOwnProperty.call(x, "enddate"))
              x.enddate = new Date(x.enddate);
            if (Object.prototype.hasOwnProperty.call(x, "operationplan__enddate"))
              x.operationplan__enddate = new Date(x.operationplan__enddate);
            if (Object.prototype.hasOwnProperty.call(x, "startdate"))
              x.startdate = new Date(x.startdate);
            if (Object.prototype.hasOwnProperty.call(x, "operationplan__startdate"))
              x.operationplan__startdate = new Date(x.operationplan__startdate);
            if (Object.prototype.hasOwnProperty.call(x, "quantity"))
              x.quantity = parseFloat(x.quantity);
            if (Object.prototype.hasOwnProperty.call(x, "operationplan__quantity"))
              x.operationplan__quantity = parseFloat(x.operationplan__quantity);
            if (Object.prototype.hasOwnProperty.call(x, "quantity_completed"))
              x.quantity_completed = parseFloat(x.quantity_completed);
            if (
              Object.prototype.hasOwnProperty.call(
                x,
                "operationplan__quantity_completed"
              )
            )
              x.operationplan__quantity_completed = parseFloat(
                x.operationplan__quantity_completed
              );
            if (Object.prototype.hasOwnProperty.call(x, "operationplan__status"))
              x.status = x.operationplan__status;
            if (Object.prototype.hasOwnProperty.call(x, "operationplan__origin"))
              x.origin = x.operationplan__origin;
            // [x.color, x.inventory_status] = formatInventoryStatus(x);
          }
          this.kanbanoperationplans[key] = tmp;
        } catch (err) {
          if (err.response && err.response.status === 401) location.reload();
        }
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

    setStatus(value) {
      if (value !== 'no_action' && value !== 'erp_incr_export') {
        this.selectedOperationplans.forEach(
          (op) => {
            this.setEditFormValues('status', value);
            this.trackOperationplanChanges(op.reference, 'status', value);
          }
        );
      }
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
      window.preferences = preferences;
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
        await operationplanService.savePreferences({ "freppledb.input.views.manufacturing.ManufacturingOrderList": this.preferences });
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

    // async save(data) {
    //   console.log(314, 'save: ', data);
    // },

    undo() {
      this.operationplan = new Operationplan();
      this.editForm = {setQuantity: null, setStart: "", setEnd: "", setRemark: ""};
      this.selectedOperationplans = [];
      this.operationplanChanges = {};
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

    // Process aggregated info for multiple selections
    processAggregatedInfo(operationplans, colModel) {
      this.selectedOperationplans = operationplans;

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

      const dateKeys  = new Set(["end", "start"]);
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
              dateKeys.add(field[1]);
              temp = new moment(opplan[field[1]], datetimeformat);
              if (temp._d !== 'Invalid Date') {
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
              const temp = new moment(opplan[field[1]], datetimeformat);
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

      aggregatedopplan.start = aggregatedopplan.startdate || aggregatedopplan.operationplan__startdate;
      aggregatedopplan.end = aggregatedopplan.enddate || aggregatedopplan.operationplan__enddate;
      dateKeys.forEach((key) => {
        aggregatedopplan[key] = aggregatedopplan[key].format('YYYY-MM-DD[T]HH:mm:ss');
      })

      this.operationplan = new Operationplan(aggregatedopplan);
    },

    expandOrCollapse(i, type) {
      // 0: collapsed, 1: expanded, 2: hidden, 3: leaf node
      const data = (type === 'downstream') ? this.operationplan.downstreamoperationplans : (type === 'upstream') ? this.operationplan.upstreamoperationplans : [];
      let j = i + 1;
      const myLevel = data[i][0];
      if (data[i][11] === 0)
        data[i][11] = 1;
      else
        data[i][11] = 0;
      while (j < data.length) {
        if (data[j][0] <= myLevel)
          break;
        else if (data[j][0] > myLevel + 1
          || data[i][11] === 0)
          data[j][11] = 2;
        else if (j === data.length - 1 ||
          data[j][0] >= data[j + 1][0]) {
          if (data[j][12] != null
            && data[j][12] === data[j + 1][12])
            data[j][11] = 1;
          else
            data[j][11] = 3;
        }
        else if (data[j][0] === myLevel + 1
          && data[i][11] === 1)
          data[j][11] = 0;
        ++j;
      }
    },

    setEditFormValues(field, value) {
      window.displayongrid(this.operationplan.reference, field, value);
      this.editForm[field] = value;
      if (field === 'status') this.operationplan.status = value;
      this.trackOperationplanChanges(this.operationplan.reference, field, value);
    },

    applyGridCellEdit({ reference, field, value }) {
      const currentRef =
        this.operationplan?.reference ||
        this.operationplan?.operationplan__reference;

      if (currentRef && reference && String(currentRef) !== String(reference)) {
        return;
      }

      this.trackOperationplanChanges(reference, field, value);

      switch (field) {
        case 'quantity': this.operationplan.quantity = parseFloat(value); break;
        case 'remark': this.operationplan.remark = value; break;
        case 'startdate': this.operationplan.start = value; break;
        case 'enddate': this.operationplan.end = value; break;
        case 'status': this.operationplan.status = value; break;
        default: this.operationplan[field] = value; break;
      }
    },

    trackOperationplanChanges(reference, field, value) {
      this.operationplanChanges[reference] = this.operationplanChanges[reference] || {};

      if (field === 'quantity' || field === 'operationplan__quantity') {
        const n = parseFloat(value);
        const v = isNaN(n) ? value : n;
        this.operationplanChanges[reference]['operationplan__quantity'] = v;
        this.operationplanChanges[reference]['quantity'] = v;
      } else if (field === 'startdate' || field === 'operationplan__startdate' || field === 'start') {
        this.operationplanChanges[reference]['operationplan__startdate'] = value;
        this.operationplanChanges[reference]['start'] = value;
        this.operationplanChanges[reference]['startdate'] = value;
      } else if (field === 'enddate' || field === 'operationplan__enddate' || field === 'end') {
        this.operationplanChanges[reference]['operationplan__enddate'] = value;
        this.operationplanChanges[reference]['end'] =  value;
        this.operationplanChanges[reference]['enddate'] = value;
      } else {
        this.operationplanChanges[reference][field] = value;
      }
      window.operationplanChanges = toRaw(this.operationplanChanges);
    }
  }
})
