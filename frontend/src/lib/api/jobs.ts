import { apiClient, unwrap } from './client';
import type {
  JobsListData,
  LinkedInJob,
  JobSearchRequest,
  ScrapeData,
  StandardResponse,
} from '../types/api';

export interface GetJobsParams {
  page?: number;
  limit?: number;
  keyword?: string;
  company?: string;
  location?: string;
  remote?: boolean;
  hybrid?: boolean;
  onsite?: boolean;
  experience?: string;
  country?: string;
  sort?: string;
  order?: string;
  source_type?: string;
}

export async function getJobs(
  params: GetJobsParams = {},
): Promise<JobsListData> {
  return unwrap<JobsListData>(
    apiClient.get<StandardResponse<JobsListData>>('/api/jobs', { params }),
  );
}

export async function getJob(jobId: string): Promise<LinkedInJob> {
  return unwrap<LinkedInJob>(
    apiClient.get<StandardResponse<LinkedInJob>>(`/api/jobs/${jobId}`),
  );
}

export async function scrapeJobs(
  payload: JobSearchRequest,
): Promise<ScrapeData> {
  return unwrap<ScrapeData>(
    apiClient.post<StandardResponse<ScrapeData>>('/api/jobs/scrape', payload),
  );
}
