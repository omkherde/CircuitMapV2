import axios from 'axios';
import type { ValidateRequest, ValidateResponse, DemoResponse, DemoScenario, AppConfig } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Start a validation session
export async function startValidation(request: ValidateRequest): Promise<ValidateResponse> {
  const response = await api.post<ValidateResponse>('/api/validate', request);
  return response.data;
}

// Load demo data
export async function loadDemoData(scenario: DemoScenario): Promise<DemoResponse> {
  const response = await api.get<DemoResponse>(`/api/demo/${scenario}`);
  return response.data;
}

// Load live UI config
export async function loadAppConfig(): Promise<AppConfig> {
  const response = await api.get<AppConfig>('/api/config');
  return response.data;
}

// Get stream URL for a session
export function getStreamUrl(sessionId: string): string {
  return `${API_BASE_URL}/api/stream/${sessionId}`;
}

// Get brain map image URL
export function getBrainMapUrl(sessionId: string, mapType: 'expression' | 'disease'): string {
  return `${API_BASE_URL}/api/maps/${sessionId}/${mapType}.png`;
}

// Get PDF download URL
export function getPdfDownloadUrl(sessionId: string): string {
  return `${API_BASE_URL}/api/report/${sessionId}/download`;
}

// Health check
export async function healthCheck(): Promise<boolean> {
  try {
    await api.get('/api/health');
    return true;
  } catch {
    return false;
  }
}
