import { apiClient, unwrap } from './client';
import type { HealthData, StandardResponse } from '../types/api';

export async function getHealth(): Promise<HealthData> {
  return unwrap<HealthData>(
    apiClient.get<StandardResponse<HealthData>>('/api/health'),
  );
}
