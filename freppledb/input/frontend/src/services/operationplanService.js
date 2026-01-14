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
  async getOperationplanDetails(params) {
    return api.get('operationplan/?reference=' + params.reference, {});
  },

  async postOperationplanDetails(postData) {
    return api.wspost('operationplan/', postData );
  },

  async savePreferences(preferencesData) {
    return api.post('settings/', preferencesData );
  }
};
