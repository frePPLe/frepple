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

export const forecastService = {
  async getItemtree(measure, item =null, location =null, customer=null) {
    let additional = "";
    if (item) additional += "&item=" + item;
    if (location) additional += "&location=" + location;
    if (customer) additional += "&customer=" + customer;
    return api.get('forecast/itemtree/?measure=' + measure + additional);
  },

  async getLocationtree(measure, item =null, location =null, customer=null) {
    let additional = "";
    if (item) additional += "&item=" + item;
    if (location) additional += "&location=" + location;
    if (customer) additional += "&customer=" + customer;
    return api.get('forecast/locationtree/?measure=' + measure + additional);
  },

  async getCustomertree(measure, item =null, location =null, customer=null) {
    let additional = "";
    if (item) additional += "&item=" + item;
    if (location) additional += "&location=" + location;
    if (customer) additional += "&customer=" + customer;
    return api.get('forecast/customertree/?measure=' + measure + additional);
  },

  async savePreferences(preferencesData) {
    return api.post('settings/', preferencesData );
  },
  //
  // async infoQuote(quoteName) {
  //   console.log("Calling info quote service", quoteName);
  //   return api.post('quote/info/', [quoteName] );
  // },
  //
  // async fetchQuoteData(endpoint) {
  //   return api.get(endpoint);
  // }
};
