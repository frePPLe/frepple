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
      'Authorization': 'Bearer ' + window.service_token
    };

    const { loading, backendError, responseData } = await usePostBackendData(
      window.service_url + endpoint,
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
      'Authorization': 'Bearer ' + window.service_token
    };

    const { loading, backendError, responseData } = await useGetBackendData(
      window.service_url + endpoint,
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
      window.location.protocol + '//' + window.location.host + window.url_prefix + '/' + endpoint,
      data,
      { ...defaultHeaders, ...options }
    );

    if (backendError.value) {
      throw new Error(backendError.value);
    }

    return { loading, responseData };
  },

  async get(endpoint, options = {}) {
    console.log('71 options: ', options);
    const defaultHeaders = {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': getCsrfToken(),
      'Content-Type': 'application/json;charset=utf-8'
    };

    const { loading, backendError, responseData } = await useGetBackendData(
      window.location.protocol + '//' + window.location.host + window.url_prefix + '/' + endpoint,
      { ...defaultHeaders, ...options }
    );

    if (backendError.value) {
      throw new Error(backendError.value);
    }

    return { loading, responseData };
  }
};
