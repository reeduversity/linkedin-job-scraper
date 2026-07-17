'use client';

import { useState, useEffect } from 'react';
import { useJobs } from '@/lib/hooks/queries';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonTable } from '@/components/ui/skeleton-table';
import { JobDetailsDialog } from '@/components/jobs/job-details-dialog';
import { Briefcase, Search, X, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import type { GetJobsParams } from '@/lib/api/jobs';
import type { LinkedInJob } from '@/lib/types/api';

function WorkplaceBadge({ type }: { type?: string | null }) {
  if (!type) return <span className="text-xs text-muted-foreground">—</span>;
  const colours: Record<string, string> = {
    REMOTE: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    HYBRID: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
    ONSITE: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  };
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', colours[type.toUpperCase()] ?? 'bg-muted text-muted-foreground')}>
      {type}
    </span>
  );
}

export default function JobsPage() {
  const [params, setParams] = useState<GetJobsParams>({ page: 1, limit: 15, sort: 'id', order: 'DESC' });
  const [searchTerm, setSearchTerm] = useState('');
  // Debounce search
  
  // Modal state
  const [selectedJob, setSelectedJob] = useState<LinkedInJob | null>(null);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    location: '',
    company: '',
    country: '',
    experience: '',
    remote: false,
    hybrid: false,
    onsite: false,
  });

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setParams(p => ({ ...p, page: 1, keyword: searchTerm || undefined }));
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const { data, isLoading, isError, refetch, isFetching } = useJobs(params);

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    const checked = (e.target as HTMLInputElement).checked;
    
    const newFilters = { ...filters, [name]: type === 'checkbox' ? checked : value };
    setFilters(newFilters);
    
    setParams(p => ({
      ...p,
      page: 1,
      location: newFilters.location || undefined,
      company: newFilters.company || undefined,
      country: newFilters.country || undefined,
      experience: newFilters.experience || undefined,
      remote: newFilters.remote || undefined,
      hybrid: newFilters.hybrid || undefined,
      onsite: newFilters.onsite || undefined,
    }));
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilters({
      location: '', company: '', country: '', experience: '',
      remote: false, hybrid: false, onsite: false
    });
    setParams({ page: 1, limit: 15, sort: 'id', order: 'DESC' });
  };

  const handlePrevPage = () => {
    if (params.page && params.page > 1) {
      setParams(p => ({ ...p, page: (p.page || 1) - 1 }));
    }
  };

  const handleNextPage = () => {
    if (data && params.page && params.page * (params.limit || 15) < data.total) {
      setParams(p => ({ ...p, page: (p.page || 1) + 1 }));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Jobs</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Browse, search, and filter all scraped LinkedIn jobs.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {/* Search & Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by keyword..."
              className="w-full h-10 pl-9 pr-4 rounded-md border border-input bg-background text-sm focus-ring"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button onClick={() => setSearchTerm('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn("focus-ring flex h-10 items-center gap-2 rounded-md border border-input px-4 text-sm font-medium transition-colors", showFilters ? "bg-accent" : "bg-background hover:bg-accent")}
          >
            <Filter className="h-4 w-4" /> Filters
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="p-4 rounded-lg border border-border bg-card shadow-sm grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium">Company</label>
              <input type="text" name="company" value={filters.company} onChange={handleFilterChange} className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm focus-ring" placeholder="e.g. Google" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium">Location</label>
              <input type="text" name="location" value={filters.location} onChange={handleFilterChange} className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm focus-ring" placeholder="e.g. London" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium">Country</label>
              <input type="text" name="country" value={filters.country} onChange={handleFilterChange} className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm focus-ring" placeholder="e.g. UK" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium">Experience Level</label>
              <select name="experience" value={filters.experience} onChange={handleFilterChange} className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm focus-ring">
                <option value="">Any</option>
                <option value="Internship">Internship</option>
                <option value="Entry level">Entry level</option>
                <option value="Associate">Associate</option>
                <option value="Mid-Senior level">Mid-Senior level</option>
                <option value="Director">Director</option>
                <option value="Executive">Executive</option>
              </select>
            </div>
            <div className="col-span-1 md:col-span-4 flex items-center justify-between border-t border-border mt-2 pt-4">
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" name="remote" checked={filters.remote} onChange={handleFilterChange} className="rounded border-input text-primary focus-ring" />
                  Remote
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" name="hybrid" checked={filters.hybrid} onChange={handleFilterChange} className="rounded border-input text-primary focus-ring" />
                  Hybrid
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" name="onsite" checked={filters.onsite} onChange={handleFilterChange} className="rounded border-input text-primary focus-ring" />
                  Onsite
                </label>
              </div>
              <button onClick={clearFilters} className="text-sm font-medium text-muted-foreground hover:text-foreground">
                Clear Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="relative">
        {isLoading ? (
          <SkeletonTable rows={15} columns={6} />
        ) : isError ? (
          <ErrorState title="Jobs unavailable" message="Failed to load job listings." onRetry={() => refetch()} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState icon={Briefcase} title="No jobs found" description="Try adjusting your search filters or run the scraper." />
        ) : (
          <div className={cn("transition-opacity", isFetching ? "opacity-50 pointer-events-none" : "opacity-100")}>
            <div className="rounded-lg border border-border bg-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Title</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Company</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Location</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Type</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Posted</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {data.items.map((job: LinkedInJob, idx: number) => (
                      <tr key={job.job_id ?? idx} className="hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-3 font-medium max-w-[200px] truncate">{job.job_title ?? '—'}</td>
                        <td className="px-4 py-3 text-muted-foreground max-w-[150px] truncate">{job.company_name ?? '—'}</td>
                        <td className="px-4 py-3 text-muted-foreground max-w-[150px] truncate">{job.location ?? '—'}</td>
                        <td className="px-4 py-3"><WorkplaceBadge type={job.workplace_type} /></td>
                        <td className="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap">
                          {job.posted_date ? formatDistanceToNow(new Date(job.posted_date), { addSuffix: true }) : '—'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => setSelectedJob(job)}
                            className="focus-ring inline-flex items-center justify-center rounded bg-secondary px-2.5 py-1 text-xs font-medium hover:bg-secondary/80"
                          >
                            Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/20">
                <p className="text-sm text-muted-foreground">
                  Showing <span className="font-medium">{(data.page - 1) * data.limit + 1}</span> to{' '}
                  <span className="font-medium">{Math.min(data.page * data.limit, data.total)}</span> of{' '}
                  <span className="font-medium">{data.total}</span> jobs
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrevPage}
                    disabled={data.page <= 1}
                    className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded border border-border bg-background disabled:opacity-50"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleNextPage}
                    disabled={data.page * data.limit >= data.total}
                    className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded border border-border bg-background disabled:opacity-50"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <JobDetailsDialog job={selectedJob} open={!!selectedJob} onOpenChange={(open) => !open && setSelectedJob(null)} />
    </div>
  );
}
