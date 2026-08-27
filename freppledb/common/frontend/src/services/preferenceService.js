/*
 * Copyright (C) 2026 by frePPLe bv
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

const debounceTimers = new Map();

function debounce(key, fn, delay) {
  return function (...args) {
    if (debounceTimers.has(key)) {
      clearTimeout(debounceTimers.get(key));
    }
    debounceTimers.set(
      key,
      setTimeout(() => {
        debounceTimers.delete(key);
        fn(...args);
      }, delay),
    );
  };
}

export function getPreference(key, defaultValue) {
  if (window.preferences && window.preferences[key] !== undefined) {
    return window.preferences[key];
  }
  return defaultValue;
}

export function savePreference(preferenceKey, value) {
  const existing = window.preferences || {};
  const merged = { ...existing, [preferenceKey]: value };
  const data = {
    [window.reportkey]: merged,
  };

  if (window.debug) console.log('Saving preference:', preferenceKey, value, data);

  const prefix = window.url_prefix || '';
  return fetch(prefix + '/settings/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify(data),
  }).then(response => {
    if (!response.ok) {
      console.error('Failed to save preference:', preferenceKey, response.status);
    } else if (window.debug) {
      console.log('Preference saved:', preferenceKey, value);
    }
    return response;
  }).catch(error => {
    console.error('Error saving preference:', preferenceKey, error);
  });
}

export function savePreferenceDebounced(key, value, delay = 400) {
  const debouncedSave = debounce(
    `pref_${key}`,
    () => savePreference(key, value),
    delay,
  );
  debouncedSave();
}

export function flushPreferenceDebounce(key) {
  const timerKey = `pref_${key}`;
  if (debounceTimers.has(timerKey)) {
    clearTimeout(debounceTimers.get(timerKey));
    debounceTimers.delete(timerKey);
    savePreference(key, window.preferences?.[key]);
  }
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
