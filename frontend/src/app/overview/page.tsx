'use client';

import {
  useHealth,
  useStatistics,
  useSchedulerStatus,
  useJobs,
} from '@/lib/hooks/queries';
import { StatCard } from '@/components/ui/stat-card';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Briefcase,
  Building2,
  Globe,
  Wifi,
  Blend,
  MapPin,
  Server,
  Clock,
  Activity,
  ExternalLink,
  CalendarDays,
  Database,
  Download,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import type { LinkedInJob } from '@/lib/types/api';

/* ——— Skeleton helpers ——— */
function StatSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="h-4 w-20 animate-pulse rounded bg-muted" />
        <div className="h-4 w-4 animate-pulse rounded bg-muted" />
      </div>
      <div className="mt-3 h-7 w-16 animate-pulse rounded bg-muted" />
      <div className="mt-2 h-3 w-28 animate-pulse rounded bg-muted" />
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <div className="bg-muted/40 px-4 py-3 flex gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-4 flex-1 animate-pulse rounded bg-muted" />
        ))}
      </div>
      {Array.from({ length: 5 }).map((_, ri) => (
        <div key={ri} className="flex gap-4 border-t border-border px-4 py-3">
          {Array.from({ length: 5 }).map((_, ci) => (
            <div
              key={ci}
              className="h-4 flex-1 animate-pulse rounded bg-muted"
              style={{ animationDelay: `${ri * 80 + ci * 30}ms` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

function StatusSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-6 space-y-4">
      <div className="h-5 w-32 animate-pulse rounded bg-muted" />
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex justify-between">
          <div className="h-4 w-24 animate-pulse rounded bg-muted" />
          <div className="h-4 w-16 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

/* ——— Sub-components ——— */

function KpiGrid() {
  const { data, isLoading, isError, refetch } = useStatistics();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <StatSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return <ErrorState title="Statistics unavailable" message="Could not load statistics from the backend." onRetry={() => refetch()} />;
  }

  if (!data) return null;

  const cards = [
    { title: 'Total Jobs', value: data.total_jobs, icon: Briefcase, desc: 'Jobs in database' },
    { title: 'Hiring Posts', value: data.hiring_posts ?? 0, icon: Briefcase, desc: 'Direct employee posts' },
    { title: 'Companies', value: data.total_companies, icon: Building2, desc: 'Unique companies' },
    { title: 'Remote', value: data.remote_jobs, icon: Wifi, desc: 'Remote positions' },
    { title: 'Hybrid', value: data.hybrid_jobs, icon: Blend, desc: 'Hybrid positions' },
    { title: 'Onsite', value: data.onsite_jobs, icon: MapPin, desc: 'Onsite positions' },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {cards.map((c) => (
        <StatCard
          key={c.title}
          title={c.title}
          value={c.value}
          description={c.desc}
          icon={c.icon}
        />
      ))}
    </div>
  );
}

function RecentJobsTable() {
  const { data, isLoading, isError, refetch } = useJobs({
    page: 1,
    limit: 8,
    sort: 'id',
    order: 'DESC',
  });

  if (isLoading) return <TableSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Jobs unavailable"
        message="Could not load recent jobs."
        onRetry={() => refetch()}
      />
    );
  }

  const jobs = data?.items ?? [];

  if (jobs.length === 0) {
    return (
      <EmptyState
        icon={Briefcase}
        title="No jobs yet"
        description="No jobs have been scraped yet. Use the Scraper to fetch LinkedIn jobs."
      />
    );
  }

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Title</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Company</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Location</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Type</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Level</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Posted</th>
              <th className="px-4 py-3 text-right font-medium text-muted-foreground">Link</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job: LinkedInJob, idx: number) => (
              <tr
                key={job.job_id ?? job.linkedin_job_url ?? idx}
                className="border-b border-border last:border-b-0 transition-colors hover:bg-muted/30"
              >
                <td className="px-4 py-3 font-medium max-w-[200px] truncate">
                  <div className="flex flex-col gap-1">
                    <span className="truncate">{job.job_title ?? '—'}</span>
                    {job.source_type === 'LINKEDIN_HIRING_POST' && (
                      <span className="inline-flex items-center rounded-md bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 ring-1 ring-inset ring-emerald-500/20 w-fit">
                        Direct Hiring Post
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-muted-foreground max-w-[160px] truncate">
                  {job.company_name ?? '—'}
                </td>
                <td className="px-4 py-3 text-muted-foreground max-w-[140px] truncate">
                  {job.location ?? '—'}
                </td>
                <td className="px-4 py-3">
                  <WorkplaceBadge type={job.workplace_type} />
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs">
                  {job.experience_level ?? '—'}
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap">
                  {formatDate(job.posted_date)}
                </td>
                <td className="px-4 py-3 text-right">
                  {job.linkedin_job_url && (
                    <a
                      href={job.linkedin_job_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="focus-ring inline-flex items-center gap-1 text-xs text-info hover:underline"
                    >
                      View <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden divide-y divide-border">
        {jobs.map((job: LinkedInJob, idx: number) => (
          <div
            key={job.job_id ?? job.linkedin_job_url ?? idx}
            className="p-4 space-y-2"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex flex-col gap-1">
                <p className="font-medium truncate">{job.job_title ?? '—'}</p>
                {job.source_type === 'HIRING_POST' && (
                  <span className="inline-flex items-center rounded-md bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 ring-1 ring-inset ring-emerald-500/20 w-fit">
                    Direct Hiring Post
                  </span>
                )}
                <p className="text-sm text-muted-foreground truncate">{job.company_name ?? '—'}</p>
              </div>
              <WorkplaceBadge type={job.workplace_type} />
            </div>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="truncate">{job.location ?? '—'}</span>
              <span>{formatDate(job.posted_date)}</span>
            </div>
            {job.linkedin_job_url && (
              <a
                href={job.linkedin_job_url}
                target="_blank"
                rel="noopener noreferrer"
                className="focus-ring inline-flex items-center gap-1 text-xs text-info hover:underline"
              >
                View on LinkedIn <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SystemStatus() {
  const { data: health, isLoading: hLoading } = useHealth();
  const { data: scheduler, isLoading: sLoading } = useSchedulerStatus();

  if (hLoading || sLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <StatusSkeleton />
        <StatusSkeleton />
      </div>
    );
  }

  const rows = [
    {
      label: 'Backend',
      value: health?.status ?? 'unknown',
      ok: health?.status === 'healthy',
    },
    {
      label: 'Database',
      value: health?.database ?? 'unknown',
      ok: health?.database === 'healthy',
    },
    {
      label: 'Scheduler',
      value: health?.scheduler ?? 'unknown',
      ok: health?.scheduler === 'healthy',
    },
    {
      label: 'API Version',
      value: health?.version ?? '—',
      ok: true,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* System status */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Server className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">System Status</h3>
        </div>
        <div className="space-y-3">
          {rows.map((r) => (
            <div key={r.label} className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{r.label}</span>
              <span
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
                  r.ok
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                    : 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
                )}
              >
                <span
                  className={cn(
                    'h-1.5 w-1.5 rounded-full',
                    r.ok ? 'bg-emerald-500' : 'bg-amber-500',
                  )}
                />
                {r.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Scheduler summary */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Scheduler</h3>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Status</span>
            <span
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
                scheduler?.running
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                  : 'bg-muted text-muted-foreground',
              )}
            >
              <span
                className={cn(
                  'h-1.5 w-1.5 rounded-full',
                  scheduler?.running ? 'bg-emerald-500' : 'bg-muted-foreground',
                )}
              />
              {scheduler?.running ? 'Running' : 'Stopped'}
            </span>
          </div>
          <StatusRow label="Last Run" value={formatDate(scheduler?.last_run ?? null)} />
          <StatusRow label="Next Run" value={formatDate(scheduler?.next_run ?? null)} />
          <StatusRow label="Jobs Executed" value={String(scheduler?.jobs_executed ?? 0)} />
        </div>
      </div>
    </div>
  );
}

/* ——— Tiny helpers ——— */

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

function WorkplaceBadge({ type }: { type?: string | null }) {
  if (!type) return <span className="text-xs text-muted-foreground">—</span>;

  const colours: Record<string, string> = {
    REMOTE:
      'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    HYBRID:
      'bg-blue-500/10 text-blue-600 dark:text-blue-400',
    ONSITE:
      'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        colours[type.toUpperCase()] ?? 'bg-muted text-muted-foreground',
      )}
    >
      {type}
    </span>
  );
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  try {
    const date = new Date(value);
    if (isNaN(date.getTime())) return '—';
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return '—';
  }
}

/* ——— Page ——— */

import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/hooks/queries';
import { useToast } from '@/components/ui/toast';
// ... previous imports unchanged, just insert inside OverviewPage ...

export default function OverviewPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const handleRefreshAll = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.health }),
      queryClient.invalidateQueries({ queryKey: queryKeys.statistics }),
      queryClient.invalidateQueries({ queryKey: queryKeys.schedulerStatus }),
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs() })
    ]);
    toast({ variant: 'success', title: 'Dashboard Refreshed', description: 'All metrics have been updated.' });
  };

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Overview</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor scraping activity and system health at a glance.
          </p>
        </div>
        <div className="flex gap-2">
           <Link href="/scraper" className="focus-ring inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90">
             Run Scraper
           </Link>
           <button onClick={handleRefreshAll} className="focus-ring inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground">
             Refresh All
           </button>
        </div>
      </div>

      {/* KPI cards */}
      <KpiGrid />


      {/* Recent jobs */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Recent Jobs</h3>
          </div>
          <Link href="/jobs" className="text-sm font-medium text-primary hover:underline">View all</Link>
        </div>
        <RecentJobsTable />
      </section>

      {/* System status + Scheduler */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">System &amp; Scheduler</h3>
        </div>
        <SystemStatus />
      </section>
    </div>
  );
}
