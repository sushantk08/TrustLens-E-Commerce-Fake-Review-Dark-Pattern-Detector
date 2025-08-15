import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const triggerAnalysis = async (url) => {
  const response = await apiClient.post('/api/products/analyze/', { url });
  return response.data;
};

export const fetchProductReport = async (productId) => {
  const response = await apiClient.get(`/api/products/${productId}/`);
  return response.data;
};