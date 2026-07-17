import { apiClient, unwrap } from './client';
import type { StatisticsData, StandardResponse } from '../types/api';

export async function getStatistics(): Promise<StatisticsData> {
  return unwrap<StatisticsData>(
    apiClient.get<StandardResponse<StatisticsData>>('/api/statistics'),
  );
}
