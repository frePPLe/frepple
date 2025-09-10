/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */


import { usePostBackendData, useGetBackendData, getCsrfToken } from '@common/useBackend.js';

export const api = {
  async wspost(endpoint, data, options = {}) {
    const defaultHeaders = {
      'Authorization': 'Bearer ' + service_token
    };

    const { loading, backendError, responseData } = await usePostBackendData(
      service_url + endpoint,
      data,
      { ...defaultHeaders, ...options }
    );

    if (backendError.value) {
      throw new Error(backendError.value);
    }

    return { loading, responseData };
  },

  async wsget(endpoint, options = {}) {
    const defaultHeaders = {
      'Authorization': 'Bearer ' + service_token
    };

    const { loading, backendError, responseData } = await useGetBackendData(
      service_url + endpoint,
      { ...defaultHeaders, ...options }
    );

    if (backendError.value) {
      throw new Error(backendError.value);
    }

    return { loading, responseData };
  },

  async post(endpoint, data, options = {}) {
    const defaultHeaders = {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': getCsrfToken(),
      'Content-Type': 'application/json;charset=utf-8'
    };

    const { loading, backendError, responseData } = await usePostBackendData(
      'http://' + window.location.host + '/' + endpoint,
      data,
      { ...defaultHeaders, ...options }
    );

    if (backendError.value) {
      throw new Error(backendError.value);
    }

    return { loading, responseData };
  },

  async get(endpoint, options = {}) {
    const defaultHeaders = {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': getCsrfToken(),
      'Content-Type': 'application/json;charset=utf-8'
    };

    const { loading, backendError, responseData } = await useGetBackendData(
      'http://' + window.location.host + '/' + endpoint,
      { ...defaultHeaders, ...options }
    );

    if (backendError.value) {
      throw new Error(backendError.value);
    }

    return { loading, responseData };
  }
};
