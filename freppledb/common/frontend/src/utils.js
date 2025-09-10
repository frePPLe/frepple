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

const getURLprefix = () => {
  const database = ref(window.database); // assuming database is defined globally
  return database.value === 'default' ? '' : `/${database.value}`;
};

// Date formatting filter, expecting a moment instance as input
const dateTimeFormat = (input, fmt) => {
  if (!input) return '';
  const date = new Date(input);
  // Using Intl.DateTimeFormat for modern date formatting
  const formatter = new Intl.DateTimeFormat('default', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  return fmt ? date.toLocaleString() : formatter.format(date);
};

function getDjangoTemplateVariable(key, options = { reactive: false }) {
  return ref(window[key]);
}

const dateFormat = (input, fmt) => {
  if (!input) return '';
  const date = new Date(input);
  // Using Intl.DateTimeFormat for date-only formatting
  const formatter = new Intl.DateTimeFormat('default', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return fmt ? date.toLocaleString() : formatter.format(date);
};

export {
  isEmpty,
  isObject,
  isBlank,
  getURLprefix,
  dateTimeFormat,
  dateFormat,
  getDjangoTemplateVariable,
};
