export interface StandardResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface ErrorResponse {
  success: boolean;
  message: string;
  error: string;
  code: number;
}

export interface HealthData {
  status: string;
  database: string;
  scheduler: string;
  version: string;
  timestamp: string;
}

export interface LinkedInJob {
  job_id?: string | null;
  job_title?: string;
  company_name?: string;
  company_url?: string;
  company_logo?: string;
  company_size?: string;
  linkedin_job_url: string;
  application_url?: string;
  recruiter_url?: string;
  recruiter?: string;
  location?: string;
  country?: string;
  workplace_type?: string;
  employment_type?: string;
  experience_level?: string;
  easy_apply?: boolean | null;
  posted_date?: string | null;
  scraped_timestamp?: string | null;
  salary?: string;
  currency?: string;
  description?: string;
  job_summary?: string;
  skills?: string[] | null;
  industry?: string;
  benefits?: string;
  source_type?: 'LINKEDIN_JOB' | 'LINKEDIN_HIRING_POST';
  post_url?: string;
  post_author_name?: string;
  post_author_profile_url?: string;
  application_method?: string;
  application_email?: string;
  application_platform?: string;
  raw_json?: Record<string, unknown>;
}

export interface JobSearchRequest {
  keyword?: string | null;
  location?: string | null;
  country?: string | null;
  remote?: boolean | null;
  hybrid?: boolean | null;
  onsite?: boolean | null;
  employment_type?: string | null;
  experience_level?: string | null;
  company?: string | null;
  date_posted?: string | null;
  max_results?: number | null;
}

export interface JobsListData {
  items: LinkedInJob[];
  total: number;
  page: number;
  limit: number;
}

export interface ScrapeData {
  fetched: number;
  validated: number;
  duplicates_removed: number;
  saved: number;
  failed: number;
  execution_time: number;
}

export interface StatisticsData {
  total_jobs: number;
  total_companies: number;
  total_countries: number;
  remote_jobs: number;
  hybrid_jobs: number;
  onsite_jobs: number;
  easy_apply_jobs: number;
  hiring_posts?: number;
  latest_scrape_date?: string | null;
  oldest_scrape_date?: string | null;
  duplicate_count: number;
  top_companies: { name: string; count: number }[];
  top_locations: { name: string; count: number }[];
}

export interface SchedulerStatusData {
  running: boolean;
  interval: number | null;
  next_run: string | null;
  jobs_executed: number;
  last_run: string | null;
}
