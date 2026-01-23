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

import { ref, toValue } from 'vue';
import axios from 'axios';

// reference info about Axios, to be deleted in final version
//-------------------------------------------------------
// interface AxiosStatic extends AxiosInstance {
//   create(config?: CreateAxiosDefaults): AxiosInstance;
//   Cancel: CancelStatic;
//   CancelToken: CancelTokenStatic;
//   Axios: typeof Axios;
//   AxiosError: typeof AxiosError;
//   CanceledError: typeof CanceledError;
//   HttpStatusCode: typeof HttpStatusCode;
//   readonly VERSION: string;
//   isCancel(value: any): value is Cancel;
//   all<T>(values: Array<T | Promise<T>>): Promise<T[]>;
//   spread<T, R>(callback: (...args: T[]) => R): (array: T[]) => R;
//   isAxiosError<T = any, D = any>(payload: any): payload is AxiosError<T, D>;
//   toFormData(sourceObj: object, targetFormData?: GenericFormData, options?: FormSerializerOptions): GenericFormData;
//   formToJSON(form: GenericFormData|GenericHTMLFormElement): object;
//   getAdapter(adapters: AxiosAdapterConfig | AxiosAdapterConfig[] | undefined): AxiosAdapter;
//   AxiosHeaders: typeof AxiosHeaders;
// }
//-------------------------------------------------------

// Create an Axios instance

const axiosInstance = axios.create({
  withCredentials: true,
  timeout: 180000, // Add a timeout of 3 minutes
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to get CSRF token from cookies
export function getCsrfToken() {
  const name = 'csrftoken=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const cookieArray = decodedCookie.split(';');

  for (let cookie of cookieArray) {
    cookie = cookie.trim();
    if (cookie.indexOf(name) === 0) {
      return cookie.substring(name.length);
    }
  }
  return '';
}

// Add axios interceptor to add CSRF token to each request
axiosInstance.interceptors.request.use(
  config => {
    // // Add CSRF token to headers
    // config.headers['X-CSRFToken'] = getCsrfToken();
    return config;
  },
  error => {
    return Promise.reject(error);
  },
);

// Add response interceptor to capture errors and handle them globally
axiosInstance.interceptors.response.use(
  response => {
    // Any status code within the range of 2xx causes this function to trigger
    return response;
  },
  error => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          console.error('Unauthorized: Please log in', error.response.data);
          break;
        case 403:
          console.error(
            "Forbidden: You don't have permission",
            error.response.data,
          );
          break;
        case 404:
          console.error(
            "Not Found: The requested resource doesn't exist",
            error.response.data,
          );
          break;
        case 422:
          console.error('Validation Error:', error.response.data);
          break;
        case 500:
          console.error(
            'Server Error: Please try again later',
            error.response.data,
          );
          break;
        default:
          console.error(
            `Error ${error.response.status}: ${error.response.data}`,
          );
      }

      // Missing dialog/toast notification here
      // Common component for error display?
    } else if (error.request) {
      console.error('Network Error: No response received');
    } else {
      console.error('Request Error:', error.message);
    }

    // Return the rejected promise so components can handle the error,
    // and launch the dialog included in the django template?
    return Promise.reject(error);
  },
);

export function useGetBackendData(inputValue, headers={}) {
  const url = toValue(inputValue);
  const backendError = ref(null);
  const responseData = ref(null);
  const loading = ref(true);

  // Return a promise that resolves with the refs
  const promise = axiosInstance
    .get(url, {
      headers: headers
    })
    .then(response => {
      responseData.value = response.data;
      loading.value = false;
      return { loading, backendError, responseData };
    })
    .catch(error => {
      backendError.value = error;
      loading.value = false;
      return { loading, backendError, responseData };
    });

  // Return an object with both the refs and the promise
  return {
    loading,
    backendError,
    responseData,
    then: (onFulfilled, onRejected) => promise.then(onFulfilled, onRejected)
  };
}

export function usePostBackendData(inputValue, inputData, headers={}) {
  const url = toValue(inputValue);
  const backendError = ref(null);
  const responseData = ref(null);
  const loading = ref(true);

  // Return a promise that resolves with the refs
  const promise = axiosInstance
    .post(url, toValue(inputData), {
      headers: headers
    })
    .then(response => {
      responseData.value = response.data;
      loading.value = false;
      return { loading, backendError, responseData };
    })
    .catch(error => {
      backendError.value = error;
      loading.value = false;
      return { loading, backendError, responseData };
    });

  // Return an object with both the refs and the promise
  return {
    loading,
    backendError,
    responseData,
    then: (onFulfilled, onRejected) => promise.then(onFulfilled, onRejected)
  };
}

export function usePutBackendData(inputValue, inputData, headers={}) {
  const url = toValue(inputValue);
  const backendError = ref(null);
  const backendData = toValue(inputData);
  const loading = ref(true);

  const promise = axiosInstance
    .put(url, backendData, {
      headers: headers
    })
    .then(response => {
      console.log(response.statusText);
      loading.value = false;
      return { loading, backendError };
    })
    .catch(error => {
      console.log(error);
      backendError.value = error;
      loading.value = false;
      return { loading, backendError };
    });

  return {
    loading,
    backendError,
    then: (onFulfilled, onRejected) => promise.then(onFulfilled, onRejected)
  };
}

export function usePatchBackendData(inputValue, inputData, headers={}) {
  const url = toValue(inputValue);
  const backendError = ref(null);
  const backendData = toValue(inputData);
  const loading = ref(true);

  const promise = axiosInstance
    .patch(url, backendData, {
      headers: headers
    })
    .then(response => {
      loading.value = false;
      return { loading, backendError };
    })
    .catch(error => {
      console.log(error);
      backendError.value = error;
      loading.value = false;
      return { loading, backendError };
    });

  return {
    loading,
    backendError,
    then: (onFulfilled, onRejected) => promise.then(onFulfilled, onRejected)
  };
}

export function useDeleteBackendData(inputValue, headers={}) {
  const url = toValue(inputValue);
  const backendError = ref(null);
  const loading = ref(true);

  const promise = axiosInstance
    .delete(url, {
      headers: headers
    })
    .then(response => {
      loading.value = false;
      return { loading, backendError };
    })
    .catch(error => {
      console.log(error);
      backendError.value = error;
      loading.value = false;
      return { loading, backendError };
    });

  return {
    loading,
    backendError,
    then: (onFulfilled, onRejected) => promise.then(onFulfilled, onRejected)
  };
}
