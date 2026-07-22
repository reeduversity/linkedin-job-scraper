import axios, { AxiosError, AxiosResponse } from 'axios';
import type { StandardResponse, ErrorResponse } from '../types/api';

const API_BASE_URL = 'https://campusdice-lab--linkedin-job-scraper-fastapi-app.modal.run';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120_000,
});

/** Normalised error shape thrown by the interceptor. */
export interface ApiError {
  success: false;
  message: string;
  code: number;
}

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ErrorResponse | { detail: string | unknown }>) => {
    let message = 'An unexpected error occurred';
    const code = error.response?.status ?? 500;

    if (error.response?.data) {
      const body = error.response.data;
      if ('message' in body && typeof body.message === 'string' && body.message) {
        message = body.message;
      } else if ('detail' in body) {
        message =
          typeof body.detail === 'string'
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } else if (error.code === 'ECONNABORTED') {
      message = 'Request timed out — is the backend running?';
    } else if (!error.response) {
      message = 'Network error — cannot reach the backend';
    }

    const normalised: ApiError = { success: false, message, code };
    return Promise.reject(normalised);
  },
);

/**
 * Unwrap a StandardResponse and return only the `data` payload.
 * Throws an ApiError when the backend reports `success: false`.
 */
export async function unwrap<T>(
  promise: Promise<AxiosResponse<StandardResponse<T>>>,
): Promise<T> {
  const { data: envelope } = await promise;
  if (!envelope.success) {
    throw { success: false, message: envelope.message, code: 400 } satisfies ApiError;
  }
  return envelope.data;
}
