import axios from 'axios';
import type { ReleaseRequest, RiskReport } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const analyzeRelease = async (request: ReleaseRequest): Promise<RiskReport> => {
  const response = await axios.post(`${API_BASE_URL}/releases/analyze`, request);
  return response.data;
};
