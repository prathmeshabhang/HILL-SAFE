import axios from 'axios';

// Default to relative URL so Vite proxy directs requests to http://127.0.0.1:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Attach Authorization header if token exists
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('floody_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for unified error parsing
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // If connection refused, fall back gracefully
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Backend communication error';
    console.warn(`[API] ${error.config?.url} error:`, message);
    return Promise.reject(error);
  }
);
