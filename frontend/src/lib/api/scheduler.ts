import { apiClient, unwrap } from './client';
import type { SchedulerStatusData, StandardResponse } from '../types/api';

export async function getSchedulerStatus(): Promise<SchedulerStatusData> {
  return unwrap<SchedulerStatusData>(
    apiClient.get<StandardResponse<SchedulerStatusData>>(
      '/api/scheduler/status',
    ),
  );
}

export async function startScheduler(): Promise<Record<string, never>> {
  return unwrap<Record<string, never>>(
    apiClient.post<StandardResponse<Record<string, never>>>(
      '/api/scheduler/start',
    ),
  );
}

export async function stopScheduler(): Promise<Record<string, never>> {
  return unwrap<Record<string, never>>(
    apiClient.post<StandardResponse<Record<string, never>>>(
      '/api/scheduler/stop',
    ),
  );
}

export async function runSchedulerOnce(): Promise<Record<string, never>> {
  return unwrap<Record<string, never>>(
    apiClient.post<StandardResponse<Record<string, never>>>(
      '/api/scheduler/run-once',
    ),
  );
}

export async function runOnce(): Promise<Record<string, never>> {
  return unwrap<Record<string, never>>(
    apiClient.post<StandardResponse<Record<string, never>>>(
      '/api/scheduler/run-once',
    ),
  );
}
