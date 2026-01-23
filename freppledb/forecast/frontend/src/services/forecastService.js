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

export const forecastService = {
  async getItemtree(measure, item =null, location =null, customer=null) {
    let additional = "";
    if (item) additional += "&item=" + window.admin_escape(item);
    if (location) additional += "&location=" + window.admin_escape(location);
    if (customer) additional += "&customer=" + window.admin_escape(customer);
    return api.get('forecast/itemtree/?measure=' + measure + additional);
  },

  async getLocationtree(measure, item =null, location =null, customer=null) {
    let additional = "";
    if (item) additional += "&item=" + window.admin_escape(item);
    if (location) additional += "&location=" + window.admin_escape(location);
    if (customer) additional += "&customer=" + window.admin_escape(customer);
    return api.get('forecast/locationtree/?measure=' + measure + additional);
  },

  async getCustomertree(measure, item =null, location =null, customer=null) {
    let additional = "";
    if (item) additional += "&item=" + window.admin_escape(item);
    if (location) additional += "&location=" + window.admin_escape(location);
    if (customer) additional += "&customer=" + window.admin_escape(customer);
    return api.get('forecast/customertree/?measure=' + measure + additional);
  },

  async getForecastDetails(measure, item =null, location =null, customer=null) {
    let additional = "";
    if (item) additional += "&item=" + window.admin_escape(item);
    if (location) additional += "&location=" + window.admin_escape(location);
    if (customer) additional += "&customer=" + window.admin_escape(customer);
    return api.get('forecast/detail/?measure=' + measure + additional);
  },

  async postForecastDetails(postData) {
    return api.wspost('forecast/detail/', postData );
  },

  async savePreferences(preferencesData) {
    return api.post('settings/', preferencesData );
  }
};
