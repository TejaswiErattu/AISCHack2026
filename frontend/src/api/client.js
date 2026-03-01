import axios from 'axios';
import {
  MOCK_REGIONS,
  MOCK_CLIMATE,
  MOCK_FINANCIAL,
  MOCK_NARRATIVES,
  MOCK_SIMULATION
} from '../data/mockData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

/**
 * Wrapper to handle demo fallbacks.
 * If API fails, it returns mock data and signals the context to show "Demo Mode".
 */
const handleRequest = async (requestPromise, mockData, setDemoMode) => {
  try {
    const response = await requestPromise;
    if (setDemoMode) setDemoMode(false);
    return response.data;
  } catch (error) {
    console.warn("API Error, falling back to mock data:", error.message);
    if (setDemoMode) setDemoMode(true);
    return mockData;
  }
};

export const api = {
  // Get all regions (with stress_score)
  getRegions: (setDemo) =>
    handleRequest(apiClient.get('/regions'), MOCK_REGIONS, setDemo),

  // Get climate indices for a region
  getClimate: (id, setDemo) =>
    handleRequest(apiClient.get(`/region/${id}/climate`), MOCK_CLIMATE, setDemo),

  // Get financial outputs for a region
  getFinancial: (id, setDemo) =>
    handleRequest(apiClient.get(`/region/${id}/financial`), MOCK_FINANCIAL, setDemo),

  // Get persona-specific narrative (Loan Officer, Farmer, Scientist)
  getNarrative: (id, panel, setDemo) =>
    handleRequest(apiClient.get(`/region/${id}/narrative?panel=${panel}`), MOCK_NARRATIVES[panel], setDemo),

  // Run a climate simulation (POST slider values)
  // Transform frontend field names → backend field names
  simulate: (payload, setDemo) => {
    const backendPayload = {
      region_id: payload.region_id,
      temperature_delta: payload.temperature,
      drought_index: payload.drought,
      rainfall_anomaly: payload.rainfall,
    };
    return handleRequest(apiClient.post('/simulate', backendPayload), MOCK_FINANCIAL, setDemo);
  },

  // Run Simulation Lab batch archetypes
  runBatchSimulation: (id, setDemo) =>
    handleRequest(apiClient.post('/simulate/batch', { region_id: id }), MOCK_SIMULATION, setDemo),

  // Download PDF/Text Risk Memo
  getMemoUrl: (id) => `${API_BASE_URL}/region/${id}/memo`
};
