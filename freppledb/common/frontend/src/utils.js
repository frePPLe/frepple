/*
 * Copyright (C) 2025-2026 by frePPLe bv
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

import { ref } from 'vue';

const isEmpty = data => data === null || data === undefined;

const isObject = data => data && typeof data === 'object';

const isBlank = data => {
  return (
    isEmpty(data) ||
    (Array.isArray(data) && data.length === 0) ||
    (isObject(data) && Object.keys(data).length === 0) ||
    (typeof data === 'string' && data.trim().length === 0)
  );
};

const isNumeric = value => {
  if (value === '' || value === null || value === undefined) return false;
  return !isNaN(parseFloat(value)) && isFinite(value);
};

const getURLprefix = () => {
  const database = ref(window.database); // assuming database is defined globally
  return database.value === 'default' ? '' : `/${database.value}`;
};

// Date formatting filter, expecting a moment instance as input
const dateTimeFormat = (input, fmt) => {
  if (!input) return '';
  const date = new Date(input);
  return moment(date).format(fmt ? fmt : window.datetimeformat);
};

function getDjangoTemplateVariable(key, options = { reactive: false }) {
  return ref(window[key]);
}

const dateFormat = (input, fmt) => {
  if (!input) return '';
  const date = new Date(input);
  return moment(date).format(fmt ? fmt : window.dateformat);
};

const timeFormat = (input) => {
  if (!input) return '';
  const date = new Date(input);
  return moment(date).format("HH:mm:ss");
};

const dateToISO = (input) => {
  if (!input) return '';
  if (input instanceof Date) return moment(input).format('YYYY-MM-DDTHH:mm:ss');

  const dateTimeFmt = window.datetimeformat || 'YYYY-MM-DDTHH:mm:ss';
  const m = moment(input, dateTimeFmt, true);
  if (m.isValid()) return m.format('YYYY-MM-DDTHH:mm:ss');

  const dateFmt = window.dateformat || 'YYYY-MM-DD';
  const dm = moment(input, dateFmt, true);
  if (dm.isValid()) return dm.format('YYYY-MM-DDTHH:mm:ss');

  const fallback = moment(input);
  if (fallback.isValid()) return fallback.format('YYYY-MM-DDTHH:mm:ss');
  return input;
};

function debouncedInputHandler(func, delay = 300) {
  let timeoutId;

  return function executedFunction(...args) {
    const later = () => {
      timeoutId = null;
      func.apply(this, args);
    };

    clearTimeout(timeoutId);
    timeoutId = setTimeout(later, delay);

    if (!timeoutId) func.apply(this, args);
  };
}

const numberFormat = (nData, maxdecimals = 6) => {
  // Number formatting function copied from free-jqgrid.
  // Adapted to show a max number of decimal places.
  if (typeof (nData) === 'undefined' || nData === '')
    return '';

  const isNumber = nData !== '' && nData !== null && !isNaN(nData) && isFinite(nData);

  if (isNumber) {
    nData *= 1;
    const bNegative = (nData < 0);
    const absData = Math.abs(nData);
    let sOutput = 0.0;

    if (absData > 100000 || maxdecimals <= 0)
      sOutput = String(parseFloat(absData.toFixed()));
    else if (absData > 10000 || maxdecimals <= 1)
      sOutput = String(parseFloat(absData.toFixed(1)));
    else if (absData > 1000 || maxdecimals <= 2)
      sOutput = String(parseFloat(absData.toFixed(2)));
    else if (absData > 100 || maxdecimals <= 3)
      sOutput = String(parseFloat(absData.toFixed(3)));
    else if (absData > 10 || maxdecimals <= 4)
      sOutput = String(parseFloat(absData.toFixed(4)));
    else if (absData > 1 || maxdecimals <= 5)
      sOutput = String(parseFloat(absData.toFixed(5)));
    else
      sOutput = String(parseFloat(absData.toFixed(maxdecimals)));

    sOutput = (bNegative ? "-" : "") + sOutput;

    const sDecimalSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    if (sDecimalSeparator !== ".")
      // Replace the "."
      sOutput = sOutput.replace(".", sDecimalSeparator);
    const sThousandsSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    if (sThousandsSeparator && absData >= 1000) {
      let nDotIndex = sOutput.lastIndexOf(sDecimalSeparator);
      nDotIndex = (nDotIndex > -1) ? nDotIndex : sOutput.length;
      // we cut the part after the point for integer numbers
      // it will prevent storing/restoring of wrong numbers during inline editing
      let sNewOutput = sDecimalSeparator === undefined ? "" : sOutput.substring(nDotIndex);
      let nCount = -1, i;
      for (i = nDotIndex; i > 0; i--) {
        nCount++;
        if ((nCount % 3 === 0) && (i !== nDotIndex) && (!bNegative || (i > 1))) {
          sNewOutput = sThousandsSeparator + sNewOutput;
        }
        sNewOutput = sOutput.charAt(i - 1) + sNewOutput;
      }
      sOutput = sNewOutput;
    }
    return sOutput;
  }
  return (nData ? nData.toLocaleString() : null) || '0';
}

// Simple debounce function
function debounce(fn, delay = 150) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

// Admin escape function
function adminEscape(str) {
  if (typeof window.admin_escape === 'function') {
    return window.admin_escape(str);
  }
  return encodeURIComponent(str);
}

/**
 * Create a graph tooltip helper using a d3 instance
 * This allows Vue components to use d3 for tooltips without relying on the global window.graph object
 * which may not have access to the d3 module in ES module contexts
 *
 * @param {Object} d3Instance - The d3 library instance (imported from 'd3' package)
 * @returns {Object} Object with showTooltip, hideTooltip, and moveTooltip methods
 */
function createGraphTooltipHelper(d3Instance) {
  if (!d3Instance) {
    console.warn('Graph tooltip helper created without d3 instance');
    return {
      showTooltip: () => {},
      hideTooltip: () => {},
      moveTooltip: () => {}
    };
  }

  return {
    showTooltip: function (txt) {
      let tt = d3Instance.select('#tooltip');
      if (tt.empty()) {
        tt = d3Instance.select('body')
          .append('div')
          .attr('id', 'tooltip')
          .attr('role', 'tooltip')
          .attr('class', 'card p-2')
          .style('position', 'absolute');
      }
      tt.html('' + txt).style('display', 'block');
      this.moveTooltip();
    },

    hideTooltip: function () {
      d3Instance.select('#tooltip').style('display', 'none');
      d3Instance.event.stopPropagation();
    },

    moveTooltip: function () {
      const xpos = d3Instance.event.pageX + 5;
      let ypos = d3Instance.event.pageY - 28;
      const tooltipEl = d3Instance.select('#tooltip');
      const xlimit = window.innerWidth - tooltipEl.node().offsetWidth - 20;
      const ylimit = window.innerHeight - tooltipEl.node().offsetHeight - 20;

      if (xpos > xlimit) {
        ypos = d3Instance.event.pageY + 5;
      }
      if (ypos > ylimit) {
        ypos = d3Instance.event.pageY - tooltipEl.node().offsetHeight - 25;
      }
      tooltipEl.style({
        left: xpos + 'px',
        top: ypos + 'px'
      });
      d3Instance.event.stopPropagation();
    }
  };
}

export {
  isEmpty,
  isObject,
  isBlank,
  isNumeric,
  getURLprefix,
  dateTimeFormat,
  dateFormat,
  timeFormat,
  dateToISO,
  numberFormat,
  getDjangoTemplateVariable,
  debouncedInputHandler,
  debounce,
  adminEscape,
  createGraphTooltipHelper
};
