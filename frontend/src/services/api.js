import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

export const checkHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const runPrediction = async (inputData) => {
  const res = await api.post('/predict', { ...inputData, source: 'react' });
  return res.data;
};

export const getPredictionHistory = async (limit = 50) => {
  const res = await api.get(`/predict_history?limit=${limit}`);
  return res.data;
};

export const getPredictionStats = async () => {
  const res = await api.get('/predict/stats');
  return res.data;
};

export const getModelInfo = async () => {
  const res = await api.get('/model/info');
  return res.data;
};

export const getFeatureImportance = async () => {
  const res = await api.get('/model/features');
  return res.data;
};

export default api;