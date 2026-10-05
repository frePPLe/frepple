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
 * Persists the preferences of the current report.
 *
 * The object `window.preferences`, the object Django published in the
 * report template (admin/base_site_grid.html). This service owns it, persists it
 * and exposes no API of its own: callers talk to it with CustomEvents
 *
 *   preferences:get     in    detail: {key, fallback}   answer: detail.value
 *   preferences:set     in    detail: {patch}
 *
 * The preferences are read fresh on every call rather than cached.
 */
window.PreferencesService = (function (w) {
  'use strict';

  /* Coalesces bursts of writes into a single POST. */
  var PERSIST_DELAY = 150;
  var timer = null;

  function prefData() {
    if (!w.preferences || typeof w.preferences !== 'object') w.preferences = {};
    return w.preferences;
  }

  function persist() {
    if (timer || !w.reportkey) return;
    timer = setTimeout(function () {
      timer = null;
      var payload = {};
      payload[w.reportkey] = prefData();
      $.ajax({
        url: (w.url_prefix || '') + '/settings/',
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify(payload),
        /* X-CSRFToken is attached to every same-origin POST by the global
         * ajaxSend handler in frepple.js. */
        error: w.ajaxerror,
      });
    }, PERSIST_DELAY);
  }

  document.addEventListener('preferences:get', function (e) {
    if (!e.detail) return;
    var value = prefData()[e.detail.key];
    e.detail.value = value === undefined ? e.detail.fallback : value;
  });

  document.addEventListener('preferences:set', function (e) {
    if (!e.detail || !e.detail.patch) return;
    var d = prefData();
    var patch = e.detail.patch;
    Object.keys(patch).forEach(function (key) {
      d[key] = patch[key];
    });
    persist();
  });

  return {};
})(window);
