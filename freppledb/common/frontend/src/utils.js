/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

import { onMounted, onUnmounted, ref } from 'vue';

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

export {
  isEmpty,
  isObject,
  isBlank,
  isNumeric,
  getURLprefix,
  dateTimeFormat,
  dateFormat,
  timeFormat,
  debouncedInputHandler,
};
