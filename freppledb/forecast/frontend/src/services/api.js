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
