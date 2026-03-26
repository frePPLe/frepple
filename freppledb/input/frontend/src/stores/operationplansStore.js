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

import { toRaw } from 'vue';
import { defineStore } from 'pinia';
import { operationplanService } from '@/services/operationplanService.js';
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
    editForm: { quantity: null, startdate: '', enddate: '', remark: '' },

    mode: window.preferences?.mode || window.mode || 'table',
    calendarmode: 'month',
    grouping: null,
    groupingdir: 'asc',
    showTop: true,
    showChildren: true,
    page: 1,
    rows: [], // table columns to be (de)selected
    frozen: 0,
    currentFilter: '', // preferences.favorites
    widgets: {},
    sidx: 'batch',
    sord: 'asc',
    favorites: [], // for filters
    segment: '',
    columns: [], // ['proposed', 'approved', 'confirmed', 'completed', 'closed']

    // UI state
    loading: false,
    exporting: false,
    exportError: null,
    exportSuccess: null,
    error: { title: '', showError: false, message: '', details: '', type: 'error' },
    dataRowHeight: window.preferences?.height || null,
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
    kanbancolumns: window.preferences?.columns || [
      'proposed',
      'approved',
      'confirmed',
      'completed',
      'closed',
    ],
    groupBy: window.groupBy || 'status',
    groupOperator: window.groupOperator || 'eq',
    ganttoperationplans: [],
    calendarevents: [],
  }),

  getters: {
    isTableMode: (state) => state.mode === 'table',
    isKanbanMode: (state) => state.mode === 'kanban',
    isGanttMode: (state) => state.mode === 'gantt',
    isCalendarMode: (state) => state.mode.startsWith('calendar'),
    hasSelected: (state) => state.selectedOperationplans?.length > 0,
    hasChanges(state) {
      return Object.keys(state.operationplanChanges).length > 0;
    },
    getMode(state) {
      state.mode = window.mode;
    },
    getPreferences(state) {
      state.preferences = window.preferences;
    },
  },

  actions: {
    setMode(newMode) {
      this.mode = newMode;
      window.mode = newMode;
      if (window.preferences) {
        window.preferences.mode = newMode;
      }
      this.undo();
    },

    setCalendarMode(newCalendarMode) {
      this.calendarmode = newCalendarMode;
      this.preferences.calendarmode = newCalendarMode;
    },

    setGrouping(newGrouping) {
      this.grouping = newGrouping;
      this.preferences.grouping = newGrouping;
    },

    isChanged(reference, field = null) {
      if (!reference) return false;
      if (!field) return Object.keys(this.operationplanChanges).includes(reference);
      else
        return (
          Object.prototype.hasOwnProperty.call(this.operationplanChanges, reference) &&
          Object.prototype.hasOwnProperty.call(this.operationplanChanges[reference], field)
        );
    },

    async loadOperationplans(references = [], selectedFlag, selectedRows, isDataSaved = false) {
      this.selectedOperationplans.length = 0;
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
            reference: operationplanReference,
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
            message:
              error.response?.data?.message || 'An error occurred while loading operation plans',
            details: error.message,
            type: 'error',
          };
        } finally {
          this.loading = false;
        }
      }
      if (
        this.operationplanChanges[this.operationplan.reference] !== undefined &&
        !window.isDataSaved
      ) {
        for (const field in this.operationplanChanges[this.operationplan.reference]) {
          this.operationplan[field] =
            this.operationplanChanges[this.operationplan.reference][field];
        }
      }
    },

    async loadKanbanData(thefilter) {
      if (this.mode !== 'kanban') return;
      if (!thefilter) {
        thefilter = this.currentFilter || window.initialfilter;
      }

      const params = {
        format: 'kanban',
        sidx: this.sidx,
        sord: this.sord,
      };

      const promises = this.kanbancolumns.map(async (key) => {
        let colfilter = thefilter ? JSON.parse(JSON.stringify(thefilter)) : undefined;
        const extrafilter = {
          field: this.groupBy,
          op: this.groupOperator,
          data: key,
        };
        if (colfilter === undefined || colfilter === null) {
          colfilter = {
            groupOp: 'AND',
            rules: [extrafilter],
            groups: [],
          };
        } else {
          if (colfilter['groupOp'] === 'AND') colfilter['rules'].push(extrafilter);
          else
            colfilter = {
              groupOp: 'AND',
              rules: [extrafilter],
              groups: [colfilter],
            };
        }
        try {
          const { responseData } = await operationplanService.getKanbanData({
            ...params,
            filters: JSON.stringify(colfilter),
          });
          this.kanbanoperationplans[key] = responseData.value;
        } catch (err) {
          if (err.response && err.response.status === 401) location.reload();
          throw err;
        }
        if (
          this.operationplanChanges[this.operationplan.reference] !== undefined &&
          !window.isDataSaved
        ) {
          for (const field in this.operationplanChanges[this.operationplan.reference]) {
            this.kanbanoperationplans[key][this.operationplan.reference][field] =
              this.operationplanChanges[this.operationplan.reference][field];
          }
          for (const field in this.operationplanChanges[this.operationplan.reference]) {
            this.kanbanoperationplans[key][this.operationplan.reference][field] =
              this.operationplanChanges[this.operationplan.reference][field];
          }
        }
      });
      await Promise.all(promises);
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
        this.selectedOperationplans.forEach((op) => {
          this.setEditFormValues('status', value);
          this.trackOperationplanChanges(op.reference, 'status', value);
        });
      }
    },

    setKanbanStatus(oldStatus, oldIndex, newStatus, newIndex, reference) {
      if (!this.kanbancolumns.includes(newStatus)) return;

      const currentRef =
        this.operationplan?.reference || this.operationplan?.operationplan__reference;
      if (currentRef === reference) {
        this.operationplan.status = newStatus;
      }

      this.trackOperationplanChanges(reference, 'status', newStatus);
    },

    // Move a card between Kanban columns when status changes
    moveKanbanCard(reference, oldStatus, newStatus) {
      if (!this.kanbancolumns.includes(newStatus)) return;
      if (oldStatus === newStatus) return;

      // We need to check all columns because multiple cards with same reference
      // might exist in different status columns
      // or at least ensure we move ALL matching cards from the oldStatus column.

      const oldColumn = this.kanbanoperationplans[oldStatus];
      if (!oldColumn || !oldColumn.rows) return;

      // Find all matching cards
      let cardIndex;
      while ((cardIndex = oldColumn.rows.findIndex((row) => row.reference == reference)) !== -1) {
        // Remove from old column
        const cardData = oldColumn.rows.splice(cardIndex, 1)[0];

        // Update status fields
        cardData.status = newStatus;
        if (Object.prototype.hasOwnProperty.call(cardData, 'operationplan__status')) {
          cardData.operationplan__status = newStatus;
        }
        cardData.dirty = true;

        // Ensure new column exists
        if (!this.kanbanoperationplans[newStatus]) {
          this.kanbanoperationplans[newStatus] = { rows: [], records: 0 };
        }

        // Add to new column
        this.kanbanoperationplans[newStatus].rows.unshift(cardData);

        // Update counters
        oldColumn.records--;
        this.kanbanoperationplans[newStatus].records++;
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
    setPreferences(reportKey, preferences) {
      this.preferences = preferences;
      window.preferences = preferences;
      const data = {};
      if (reportKey) {
        data[reportKey] = preferences;
        operationplanService.savePreferences(data);
      }
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
        // if (this.dataRowHeight !== null) {
        //   this.preferences.height = this.dataRowHeight;
        // }
        await operationplanService.savePreferences({
          'freppledb.input.views.manufacturing.ManufacturingOrderList': this.preferences,
        });
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

    setExporting(status) {
      this.exporting = status;
    },

    undo() {
      this.operationplan = new Operationplan();
      this.editForm = { setQuantity: null, setStart: '', setEnd: '', setRemark: '' };
      this.selectedOperationplans = [];
      this.operationplanChanges = {};
      window.operationplanChanges = toRaw(this.operationplanChanges);
      if (this.mode === 'kanban') {
        this.loadKanbanData();
      }
    },

    async saveOperationplanChanges() {
      const changes = [];
      for (const [key, value] of Object.entries(this.operationplanChanges)) {
        value.id = key;
        changes.push(toRaw({ ...value, id: key }));
      }
      if (!changes || Object.keys(changes).length === 0) return;

      changes.map((x) => {
        delete x.end;
        delete x.start;
        // delete x.id;
        if (x.startdate) {
          x.startdate = x.startdate.replace('T', ' ');
        }
        if (x.enddate) {
          x.enddate = x.enddate.replace('T', ' ');
        }
        if (x.operationplan__startdate) {
          x.operationplan__startdate = x.startdate.replace('T', ' ');
        }
        if (x.operationplan__enddate) {
          x.operationplan__enddate = x.operationplan__enddate.replace('T', ' ');
        }
        return x;
      });

      try {
        await operationplanService.postOperationplanDetails(changes);
        this.undo();
      } catch (e) {
        this.setError({
          title: 'Save failed',
          message: e.message || 'Unknown error',
          type: 'error',
        });
      }
    },

    async erpExport() {
      try {
        // Send the FULL operationplan object (matching table mode behavior)
        // This ensures consistency with what frepple.js sends in table mode
        const exportData = {
          // The backend only needs these fields in the python tests
          "reference": this.operationplan.reference,
          "type": this.operationplan.type,
          "quantity": this.operationplan.quantity,
          "enddate": this.operationplan.end

          // ...this.operationplan,
        };

        // Use the Vue service instead of direct AJAX
        const response = await operationplanService.exportToERP([exportData]);

        // Handle successful response
        if (
          response &&
          response.responseData &&
          response.responseData.value &&
          response.responseData.value[0] &&
          response.responseData.value[0].status === 'ok'
        ) {
          this.exportError = null;
          // store.undo();
        } else if (
          response &&
          response.responseData &&
          response.responseData.value &&
          response.responseData.value[0] &&
          response.responseData.value[0].messages
        ) {
          this.exportError = response.responseData.value[0].messages.join('\n');
        } else {
          this.exportError = 'Export failed: Unexpected response format from server';
        }
      } catch (err) {
        console.error('Export error:', err);

        // Handle different error types
        if (err.response) {
          // Server responded with error status
          if (err.response.data && err.response.data.detail) {
            this.exportError = err.response.data.detail;
          } else if (err.response.data && err.response.data.message) {
            this.exportError = err.response.data.message;
          } else {
            this.exportError = 'Server error: ' + (err.response.status || 'Unknown');
          }
        } else if (err.request) {
          // Request made but no response received
          this.exportError = 'No response from server';
        } else {
          // Something else happened in setting up the request
          this.exportError = err.message || 'Export failed: Unknown error';
        }
      } finally {
        this.setExporting(false);
      }
    },

    // Error handling
    setError(errorData) {
      this.error = {
        showError: true,
        title: errorData.title || 'Error',
        message: errorData.message || 'An error occurred',
        details: errorData.details || '',
        type: errorData.type || 'error',
      };
    },

    clearError() {
      this.error = {
        showError: false,
        message: '',
        details: '',
        type: 'error',
        title: '',
      };
    },

    // Process aggregated info for multiple selections
    processAggregatedInfo(operationplans, colModel) {
      this.selectedOperationplans = operationplans;

      const aggColModel = [];
      const aggregatedopplan = { colmodel: {} };
      let temp;

      colModel.forEach((modelValue, key) => {
        if (Object.prototype.hasOwnProperty.call(modelValue, 'summaryType')) {
          aggColModel.push([key, modelValue.name, modelValue.summaryType, modelValue.formatter]);
          aggregatedopplan[modelValue.name] = null;
          aggregatedopplan.colmodel[modelValue.name] = {
            type: modelValue.summaryType,
            label: modelValue.label,
            formatter: modelValue.formatter,
          };
        }
      });

      const dateKeys = new Set(['end', 'start']);
      operationplans.forEach((opplan) => {
        aggColModel.forEach((field) => {
          if (field[2] === 'sum') {
            if (field[3] === 'duration') {
              temp = new moment.duration(opplan[field[1]]).asSeconds();
              if (temp._d !== 'Invalid Date') {
                if (aggregatedopplan[field[1]] === null) aggregatedopplan[field[1]] = temp;
                else aggregatedopplan[field[1]] += temp;
              }
            } else if (!isNaN(parseFloat(opplan[field[1]]))) {
              if (aggregatedopplan[field[1]] === null) {
                aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
              } else {
                aggregatedopplan[field[1]] += parseFloat(opplan[field[1]]);
              }
            }
          } else if (field[2] === 'max') {
            if (
              ['color', 'number', 'currency'].indexOf(field[3]) !== -1 &&
              opplan[field[1]] !== ''
            ) {
              if (parseFloat(opplan[field[1]])) {
                if (aggregatedopplan[field[1]] === null) {
                  aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
                } else {
                  aggregatedopplan[field[1]] = Math.max(
                    aggregatedopplan[field[1]],
                    parseFloat(opplan[field[1]])
                  );
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
            if (['color', 'number'].indexOf(field[3]) !== -1 && opplan[field[1]] !== '') {
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

      aggregatedopplan.start =
        aggregatedopplan.startdate || aggregatedopplan.operationplan__startdate;
      aggregatedopplan.end = aggregatedopplan.enddate || aggregatedopplan.operationplan__enddate;
      dateKeys.forEach((key) => {
        aggregatedopplan[key] = aggregatedopplan[key].format('YYYY-MM-DD[T]HH:mm:ss');
      });

      this.operationplan = new Operationplan(aggregatedopplan);
    },

    expandOrCollapse(i, type) {
      // 0: collapsed, 1: expanded, 2: hidden, 3: leaf node
      const data =
        type === 'downstream'
          ? this.operationplan.downstreamoperationplans
          : type === 'upstream'
            ? this.operationplan.upstreamoperationplans
            : [];
      let j = i + 1;
      const myLevel = data[i][0];
      if (data[i][11] === 0) data[i][11] = 1;
      else data[i][11] = 0;
      while (j < data.length) {
        if (data[j][0] <= myLevel) break;
        else if (data[j][0] > myLevel + 1 || data[i][11] === 0) data[j][11] = 2;
        else if (j === data.length - 1 || data[j][0] >= data[j + 1][0]) {
          if (data[j][12] != null && data[j][12] === data[j + 1][12]) data[j][11] = 1;
          else data[j][11] = 3;
        } else if (data[j][0] === myLevel + 1 && data[i][11] === 1) data[j][11] = 0;
        ++j;
      }
    },

    setKanbanCardValue(id, field, statusKey, value) {
      // Iterate through all columns to find all cards with the same reference
      for (const columnKey in this.kanbanoperationplans) {
        const column = this.kanbanoperationplans[columnKey];
        if (!column || !column.rows) continue;

        const targets = column.rows.filter((x) => x.reference === id);

        targets.forEach((target) => {
          const targetKeys = Object.keys(target);

          // Determine the correct field name (handling operationplan__ prefix)
          let newField = targetKeys.includes(field)
            ? field
            : field.includes('operationplan__')
              ? field.replace('operationplan__', '')
              : 'operationplan__' + field;

          // Special handling for quantity fields based on record type
          if (['DO', 'MO', 'WO'].includes(target.type)) {
            if (newField === 'quantity' || newField === 'quantity_completed') {
              if (
                ['ResourceDetail', 'InventoryDetail'].includes(window.reportkey.split('.').pop()) ||
                target.type === 'DO'
              ) {
                newField = 'operationplan__' + newField.replace('operationplan__', '');
              }
            }
          }

          // Update the value on the card
          target[newField] = value;
        });
      }
    },

    setEditFormValues(field, value) {
      switch (this.mode) {
        case 'table':
          window.displayongrid(this.operationplan.reference, field, value);
          break;
        case 'kanban':
          this.setKanbanCardValue(
            this.operationplan.reference,
            field,
            this.operationplan.status,
            value
          );
          break;
        case 'default':
          break;
      }

      this.editForm[field] = value;

      // Capture old status before updating
      const oldStatus = this.operationplan.status;

      // Map kanban field names to operationplan fields and update
      if (['status', 'operationplan__status'].includes(field)) {
        this.operationplan.status = value;

        // Move the Kanban card to the new column
        if (this.mode === 'kanban')
          this.moveKanbanCard(this.operationplan.reference, oldStatus, value);
      } else if (field === 'startdate' || field === 'operationplan__startdate') {
        this.operationplan.start = value;
        this.operationplan[field] = value;
      } else if (field === 'enddate' || field === 'operationplan__enddate') {
        this.operationplan.end = value;
        this.operationplan[field] = value;
      } else if (field === 'quantity' || field === 'operationplan__quantity') {
        this.operationplan.quantity = parseFloat(value);
        this.operationplan[field] = parseFloat(value);
      } else if (field === 'quantity_completed' || field === 'operationplan__quantity_completed') {
        this.operationplan.quantity_completed = parseFloat(value);
        this.operationplan[field] = parseFloat(value);
      } else if (field === 'remark' || field === 'operationplan__remark') {
        this.operationplan.remark = value;
        this.operationplan[field] = value;
      } else {
        // For any other fields
        this.operationplan[field] = value;
      }

      this.trackOperationplanChanges(this.operationplan.reference, field, value);
    },

    applyGridCellEdit({ reference, field, value }) {
      const currentRef =
        this.operationplan?.reference || this.operationplan?.operationplan__reference;

      if (currentRef && reference && String(currentRef) !== String(reference)) {
        return;
      }

      this.trackOperationplanChanges(reference, field, value);

      switch (field) {
        case 'quantity':
          this.operationplan.quantity = parseFloat(value);
          break;
        case 'remark':
          this.operationplan.remark = value;
          break;
        case 'startdate':
          this.operationplan.start = value;
          break;
        case 'enddate':
          this.operationplan.end = value;
          break;
        case 'status':
          this.operationplan.status = value;
          break;
        default:
          this.operationplan[field] = value;
          break;
      }
    },

    trackOperationplanChanges(reference, field, value) {
      this.operationplanChanges[reference] = this.operationplanChanges[reference] || {};

      if (field === 'quantity' || field === 'operationplan__quantity') {
        const n = parseFloat(value);
        const v = isNaN(n) ? value : n;
        this.operationplanChanges[reference]['operationplan__quantity'] = v;
        this.operationplanChanges[reference]['quantity'] = v;
      } else if (
        field === 'startdate' ||
        field === 'operationplan__startdate' ||
        field === 'start'
      ) {
        this.operationplanChanges[reference]['operationplan__startdate'] = value;
        this.operationplanChanges[reference]['start'] = value;
        this.operationplanChanges[reference]['startdate'] = value;
      } else if (field === 'enddate' || field === 'operationplan__enddate' || field === 'end') {
        this.operationplanChanges[reference]['operationplan__enddate'] = value;
        this.operationplanChanges[reference]['end'] = value;
        this.operationplanChanges[reference]['enddate'] = value;
      } else {
        this.operationplanChanges[reference][field] = value;
      }
      window.operationplanChanges = toRaw(this.operationplanChanges);
    },
  },
});
