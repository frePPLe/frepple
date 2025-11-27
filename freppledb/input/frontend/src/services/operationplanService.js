/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */


import { api } from './api.js';

export const operationplanService = {
  // async getItemtree(measure, item =null, location =null, customer=null) {
  //   let additional = "";
  //   if (item) additional += "&item=" + window.admin_escape(item);
  //   if (location) additional += "&location=" + window.admin_escape(location);
  //   if (customer) additional += "&customer=" + window.admin_escape(customer);
  //   return api.get('forecast/itemtree/?measure=' + measure + additional);
  // },
  //
  // async getLocationtree(measure, item =null, location =null, customer=null) {
  //   let additional = "";
  //   if (item) additional += "&item=" + window.admin_escape(item);
  //   if (location) additional += "&location=" + window.admin_escape(location);
  //   if (customer) additional += "&customer=" + window.admin_escape(customer);
  //   return api.get('forecast/locationtree/?measure=' + measure + additional);
  // },
  //
  // async getCustomertree(measure, item =null, location =null, customer=null) {
  //   let additional = "";
  //   if (item) additional += "&item=" + window.admin_escape(item);
  //   if (location) additional += "&location=" + window.admin_escape(location);
  //   if (customer) additional += "&customer=" + window.admin_escape(customer);
  //   return api.get('forecast/customertree/?measure=' + measure + additional);
  // },
  //
  // async getForecastDetails(measure, item =null, location =null, customer=null) {
  //   let additional = "";
  //   if (item) additional += "&item=" + window.admin_escape(item);
  //   if (location) additional += "&location=" + window.admin_escape(location);
  //   if (customer) additional += "&customer=" + window.admin_escape(customer);
  //   return api.get('forecast/detail/?measure=' + measure + additional);
  // },
  //
  // async postForecastDetails(postData) {
  //   return api.wspost('forecast/detail/', postData );
  // },

  async savePreferences(preferencesData) {
    return api.post('settings/', preferencesData );
  }
};
