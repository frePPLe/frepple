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

import { api } from './api.js';

export const operationplanService = {
  async getOperationplanDetails(params) {
    return api.get('operationplan/?reference=' + encodeURIComponent(params.reference), {});
  },

  async postOperationplanDetails(postData) {
    return api.wspost('operationplan/', postData );
  },

  async savePreferences(preferencesData) {
    return api.post('settings/', preferencesData );
  },

  async getKanbanData(params) {
    const searchParams = new URLSearchParams(params).toString();
    const endpoint = (location.pathname.startsWith(window.url_prefix)
      ? location.pathname.substring(window.url_prefix.length)
      : location.pathname) + '?' + searchParams;
    return api.get(endpoint.startsWith('/') ? endpoint.substring(1) : endpoint, {});
  }
};
