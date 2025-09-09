import { usePostBackendData, useGetBackendData } from '@common/useBackend.js';

export const api = {
  async post(endpoint, data, options = {}) {
    const defaultHeaders = {
      'Authorization': 'Bearer ' + service_token
    };

    const { loading, backendError, responseData } = usePostBackendData(
      service_url + endpoint,
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
      'Authorization': 'Bearer ' + service_token
    };

    const { loading, backendError, responseData } = useGetBackendData(
      service_url + endpoint,
      { ...defaultHeaders, ...options }
    );

    if (backendError.value) {
      throw new Error(backendError.value);
    }

    return { loading, responseData };
  }
};
