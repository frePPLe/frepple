/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
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
  return moment(date).format(window.datetimeformat);
  // TODO Use Intl.DateTimeFormat for modern date formatting
  /*
  const formatter = new Intl.DateTimeFormat('default', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  return fmt ? date.toLocaleString() : formatter.format(date);
  */
};

function getDjangoTemplateVariable(key, options = { reactive: false }) {
  return ref(window[key]);
}

const dateFormat = (input, fmt) => {
  if (!input) return '';
  const date = new Date(input);
  return moment(date).format(window.dateformat);
  // TODO Use Intl.DateTimeFormat for modern date formatting
  /*
  // Using Intl.DateTimeFormat for date-only formatting
  const formatter = new Intl.DateTimeFormat('default', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return fmt ? date.toLocaleString() : formatter.format(date);
  */
};

const timeFormat = (input) => {
  if (!input) return '';
  const date = new Date(input);
  return moment(date).format("HH:mm:ss");
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

  const isNumber = isNumeric(nData);

  if (isNumber) {
    nData *= 1;
    const bNegative = (nData < 0);
    const absData = Math.abs(nData);
    let nOutput = 0.0;

    if (absData > 100000 || maxdecimals <= 0)
      nOutput = String(parseFloat(nData.toFixed()));
    else if (absData > 10000 || maxdecimals <= 1)
      nOutput = String(parseFloat(nData.toFixed(1)));
    else if (absData > 1000 || maxdecimals <= 2)
      nOutput = String(parseFloat(nData.toFixed(2)));
    else if (absData > 100 || maxdecimals <= 3)
      nOutput = String(parseFloat(nData.toFixed(3)));
    else if (absData > 10 || maxdecimals <= 4)
      nOutput = String(parseFloat(nData.toFixed(4)));
    else if (absData > 1 || maxdecimals <= 5)
      nOutput = String(parseFloat(nData.toFixed(5)));
    else
      nOutput = String(parseFloat(nData.toFixed(maxdecimals)));

    let sOutput = (bNegative ? "-" : "") + nOutput;

    const sDecimalSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    if (sDecimalSeparator !== ".")
      // Replace the "."
      sOutput = sOutput.replace(".", sDecimalSeparator);
    const sThousandsSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    if (sThousandsSeparator) {
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
  return nData?.toLocaleString() || '0';
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
  numberFormat,
  getDjangoTemplateVariable,
  debouncedInputHandler,
};
