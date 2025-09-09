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

  // async confirmQuote(quoteData) {
  //   return api.post('quote/confirm/', quoteData );
  // },
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
