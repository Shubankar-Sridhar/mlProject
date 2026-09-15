import axios from 'axios';

const API_BASE = import.meta.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

// Add request interceptor for auth
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      if (status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
      throw new Error(data.detail || 'API request failed');
    }
    throw new Error('Network error');
  }
);

export const api = {
  query: async (query, options = {}) => {
    const response = await apiClient.post('/query', {
      query,
      include_viz: true,
      ...options
    });
    return response.data;
  },

  train: async (databaseUrl, businessDocs, config = {}) => {
    const response = await apiClient.post('/train', {
      database_url: databaseUrl,
      business_docs: businessDocs,
      config
    });
    return response.data;
  },

  listModels: async () => {
    const response = await apiClient.get('/models');
    return response.data;
  },

  loadModel: async (modelId) => {
    const response = await apiClient.post(`/models/${modelId}/load`);
    return response.data;
  },

  health: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  }
};

export default api;