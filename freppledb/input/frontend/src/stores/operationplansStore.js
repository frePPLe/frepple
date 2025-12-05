/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

import {operationplanService} from "@/services/operationplanService.js";

/**
 * @typedef {Object} OperationplansState
 * @property {string} mode - Display mode: 'table', 'kanban', 'gantt', or 'calendar*'
 * @property {string} calendarmode - Calendar mode: 'day', 'week', or 'month'
 * @property {string} grouping - Grouping configuration
 * @property {string} groupingdir - Grouping direction: 'asc' or 'desc'
 * @property {boolean} showTop - Show top level operations
 * @property {boolean} showChildren - Show child level operations
 * @property {Array} operationplans - List of operation plans
 * @property {Object} selectedOperationplan - Currently selected operationplan
 * @property {Array} selectedOperationplans - Multiple selected operationplans
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
 */

let aaa = [
  'sidx', 'sord',
  'width']

import { defineStore } from 'pinia';


export const useOperationplansStore = defineStore('operationplans', {
  state: () => ({
    // Data
    operationplans: [],
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

    hasSelected: () => !!this.selectedOperationplan || this.selectedOperationplans.length > 0,

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

    // Data management actions
    async loadOperationplans(reference) {
      this.loading = true;
      this.error.showError = false;

      try { // reference value should be the selected table record reference
        const response = await operationplanService.getOperationplanDetails({
          reference: reference
        });

        // Update the store with the fetched data
        this.operationplans = response.data.results;
        print(128,  response.data.results, roRaw( response.data.results));
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
    },

    // Selection actions
    selectOperationplan(operationplan) {
      this.selectedOperationplan = operationplan;
      this.selectedOperationplans = operationplan ? [operationplan] : [];
    },

    toggleSelectOperationplan(operationplan) {
      const index = this.selectedOperationplans.findIndex(op => op.id === operationplan.id);

      if (index === -1) {
        this.selectedOperationplans.push(operationplan);
      } else {
        this.selectedOperationplans.splice(index, 1);
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

    updatePreferences() {
      // Save preferences to localStorage or backend
      localStorage.setItem('operationplansPreferences', JSON.stringify(this.preferences));
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

    // Utility actions
    resetState() {
      // Reset all state properties to their initial values
      Object.assign(this.$state, {
        operationplans: [],
        selectedOperationplans: [],
        preferences: {},
        mode: 'table',
        calendarmode: 'month',
        grouping: null,
        groupingdir: 'asc',
        showTop: true,
        showChildren: true,
        page: 1,
        rows: [],
        frozen: 0,
        currentFilter: '',
        widgets: [],
        sidx: 'batch',
        sord: 'asc',
        favorites: [],
        segment: "",
        columns: [],
        loading: false,
        error: { title: "", showError: false, message: "", details: "", type: "error" },
        dataRowHeight: null,
        width: 300,
        detailwidth: 300,
        height: 300,
        horizonstart: new Date(),
        horizonend: new Date(),
        viewstart: new Date(),
        viewend: new Date(),
        currentdate: new Date(),
        kanbanoperationplans: [],
        kanbancolumns: [],
        ganttoperationplans: [],
        calendarevents: []
      });
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
      this.selectedOperationplans = operationplans;
    },

    clearSelection() {
      this.selectedOperationplan = null;
      this.selectedOperationplans = [];
    },

    // Data loading actions
    setOperationplans(operationplans) {
      this.operationplans = operationplans;
    },

    setKanbanOperationplans(operationplans) {
      this.kanbanoperationplans = operationplans;
    },

    setKanbanColumns(columns) {
      this.kanbancolumns = columns;
    },

    setGanttOperationplans(operationplans) {
      this.ganttoperationplans = operationplans;
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
        const result = await operationplanService.savePreferences({ "freppledb.input.views.manufacturing.ManufacturingOrderList": this.preferences });

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
    },
  }
})
