import axios from 'axios';
import type {
  ReleaseAnalysisRequest,
  UnifiedRiskReport,
  ScenarioPreset,
  ApprovalSubmissionRequest,
  HumanApprovalDetails,
  ActionToggleRequest
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const analyzeRelease = async (request: ReleaseAnalysisRequest): Promise<UnifiedRiskReport> => {
  const response = await axios.post(`${API_BASE_URL}/releases/analyze`, request);
  return response.data;
};

export const getScenarios = async (): Promise<ScenarioPreset[]> => {
  const response = await axios.get(`${API_BASE_URL}/releases/scenarios`);
  return response.data;
};

export const submitApproval = async (request: ApprovalSubmissionRequest): Promise<HumanApprovalDetails> => {
  const response = await axios.post(`${API_BASE_URL}/releases/approval`, request);
  return response.data;
};

export const getApproval = async (repository: string, release: string): Promise<HumanApprovalDetails> => {
  const response = await axios.get(`${API_BASE_URL}/releases/approval`, {
    params: { repository, release }
  });
  return response.data;
};

export const toggleAction = async (request: ActionToggleRequest): Promise<any> => {
  const response = await axios.post(`${API_BASE_URL}/releases/actions/toggle`, request);
  return response.data;
};
