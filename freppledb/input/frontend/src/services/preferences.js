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
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

/*
 * Reads and writes the report's preference document.
 *
 * The app never touches `window.preferences` itself: it asks the service, which
 * lives in common/static/common/src/preferencesService.js and is only loaded by
 * the reports that use it. Requests are done with CustomEvents, which
 * dispatch synchronously - so a read gets its answer back on the detail object
 * it passed in, with no promise and no callback.
 */

/* Read one preference, or `fallback` when the report has never stored it. */
export function getPreference(key, fallback) {
  const detail = { key, fallback };
  document.dispatchEvent(new CustomEvent('preferences:get', { detail }));
  return detail.value;
}

export function setPreferences(patch) {
  document.dispatchEvent(new CustomEvent('preferences:set', { detail: { patch } }));
}
