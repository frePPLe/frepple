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
  async getItemtree(measure) {
    return api.get('forecast/itemtree/?measure=' + measure);
  },

  async getLocationtree(measure) {
    return api.get('forecast/locationtree/?measure=' + measure);
  },

  async getCustomertree(measure) {
    return api.get('forecast/customertree/?measure=' + measure);
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
