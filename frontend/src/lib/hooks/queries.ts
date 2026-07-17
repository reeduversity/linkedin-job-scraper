import { useQuery } from '@tanstack/react-query';
import { getHealth } from '../api/health';
import { getJobs, type GetJobsParams } from '../api/jobs';
import { getStatistics } from '../api/statistics';
import { getSchedulerStatus } from '../api/scheduler';

/** Query keys – centralised to avoid typos / stale cache bugs. */
export const queryKeys = {
  health: ['health'] as const,
  statistics: ['statistics'] as const,
  schedulerStatus: ['scheduler', 'status'] as const,
  jobs: (params?: GetJobsParams) => ['jobs', params ?? {}] as const,
  job: (id: string) => ['jobs', id] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    refetchInterval: 30_000, // poll health every 30s
  });
}

export function useStatistics() {
  return useQuery({
    queryKey: queryKeys.statistics,
    queryFn: getStatistics,
  });
}

export function useSchedulerStatus() {
  return useQuery({
    queryKey: queryKeys.schedulerStatus,
    queryFn: getSchedulerStatus,
  });
}

export function useJobs(params?: GetJobsParams) {
  return useQuery({
    queryKey: queryKeys.jobs(params),
    queryFn: () => getJobs(params),
  });
}
