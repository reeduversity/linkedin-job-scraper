'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { scrapeJobs } from '@/lib/api/jobs';
import { queryKeys } from '@/lib/hooks/queries';
import { useToast } from '@/components/ui/toast';
import { Database, Play, CheckCircle2, Loader2 } from 'lucide-react';
import type { JobSearchRequest, ScrapeData } from '@/lib/types/api';

const scrapeSchema = z.object({
  keyword: z.string().optional(),
  location: z.string().optional(),
  country: z.string().optional(),
  company: z.string().optional(),
  remote: z.boolean().optional(),
  hybrid: z.boolean().optional(),
  onsite: z.boolean().optional(),
  employment_type: z.string().optional(),
  experience_level: z.string().optional(),
  date_posted: z.string().optional(),
  max_results: z.number().min(1).max(1000).optional().or(z.literal('')),
});

export default function ScraperPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [result, setResult] = useState<ScrapeData | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    keyword: '',
    location: '',
    country: '',
    company: '',
    remote: false,
    hybrid: false,
    onsite: false,
    employment_type: '',
    experience_level: '',
    date_posted: '',
    max_results: 50,
  });

  const mutation = useMutation({
    mutationFn: async (payload: JobSearchRequest) => scrapeJobs(payload),
    onSuccess: (data) => {
      setResult(data);
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs() });
      queryClient.invalidateQueries({ queryKey: queryKeys.statistics });
      toast({
        variant: 'success',
        title: 'Scrape completed',
        description: `Successfully saved ${data.saved} new jobs.`,
      });
    },
    onError: (error: unknown) => {
      const msg =
        (error as { message?: string })?.message ||
        'An unexpected error occurred during scraping.';
      setErrorMessage(msg);
      setResult(null);
      toast({
        variant: 'error',
        title: 'Scrape failed',
        description: msg,
      });
    },
    onSettled: () => {
      // no-op: react-query will flip isPending automatically.
      // keeping hook for future extension and to ensure we never "forget" to stop.
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);
    setErrorMessage(null);

    try {
      const parsed = scrapeSchema.parse({
        ...formData,
        max_results: formData.max_results ? Number(formData.max_results) : undefined,
      });

      const payload: JobSearchRequest = {
        keyword: parsed.keyword || undefined,
        location: parsed.location || undefined,
        country: parsed.country || undefined,
        company: parsed.company || undefined,
        remote: parsed.remote || undefined,
        hybrid: parsed.hybrid || undefined,
        onsite: parsed.onsite || undefined,
        employment_type: parsed.employment_type || undefined,
        experience_level: parsed.experience_level || undefined,
        date_posted: parsed.date_posted || undefined,
        max_results: parsed.max_results !== '' ? Number(parsed.max_results) : undefined,
      };

      mutation.mutate(payload);
    } catch (err) {
      if (err instanceof z.ZodError) {
        const anyErr = err as unknown as { errors: { message: string }[] };
        const msg =
          anyErr.errors?.[0]?.message || 'Validation failed';
        setErrorMessage(msg);
        toast({ variant: 'error', title: 'Invalid inputs', description: msg });
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    const checked = (e.target as HTMLInputElement).checked;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Scraper Control</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Configure and run LinkedIn job scraping operations. Uses your Apify integration.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Form */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Keywords</label>
                <input
                  type="text"
                  name="keyword"
                  value={formData.keyword}
                  onChange={handleChange}
                  className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                  placeholder="e.g. Software Engineer"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Location</label>
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                    placeholder="e.g. London"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Country</label>
                  <input
                    type="text"
                    name="country"
                    value={formData.country}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                    placeholder="e.g. gb"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium">Company</label>
                <input
                  type="text"
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                  className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                  placeholder="e.g. Google"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Experience</label>
                  <select
                    name="experience_level"
                    value={formData.experience_level}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                  >
                    <option value="">Any</option>
                    <option value="Internship">Internship</option>
                    <option value="Entry level">Entry level</option>
                    <option value="Associate">Associate</option>
                    <option value="Mid-Senior level">Mid-Senior level</option>
                    <option value="Director">Director</option>
                    <option value="Executive">Executive</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Date Posted</label>
                  <select
                    name="date_posted"
                    value={formData.date_posted}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                  >
                    <option value="">Any Time</option>
                    <option value="past-24h">Past 24 hours</option>
                    <option value="past-week">Past week</option>
                    <option value="past-month">Past month</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Max Results</label>
                  <input
                    type="number"
                    name="max_results"
                    value={formData.max_results}
                    onChange={handleChange}
                    min={1}
                    max={1000}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Employment Type</label>
                  <select
                    name="employment_type"
                    value={formData.employment_type}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background focus-ring text-sm"
                  >
                    <option value="">Any</option>
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Contract">Contract</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2 pt-2">
                <label className="text-sm font-medium">Workplace Type</label>
                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      name="remote"
                      checked={formData.remote}
                      onChange={handleChange}
                      className="rounded border-input text-primary focus-ring"
                    />
                    Remote
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      name="hybrid"
                      checked={formData.hybrid}
                      onChange={handleChange}
                      className="rounded border-input text-primary focus-ring"
                    />
                    Hybrid
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      name="onsite"
                      checked={formData.onsite}
                      onChange={handleChange}
                      className="rounded border-input text-primary focus-ring"
                    />
                    Onsite
                  </label>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border mt-4">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 disabled:opacity-50"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Scraping...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" /> Run Scraper
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        <div>
          {mutation.isPending && (
            <div className="h-full rounded-xl border border-border bg-card p-6 flex flex-col items-center justify-center text-center space-y-4">
              <Loader2 className="h-10 w-10 text-primary animate-spin" />
              <div>
                <h3 className="font-semibold text-lg">Scraping in progress</h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-[250px]">
                  This may take several minutes depending on the max results and Apify queue.
                </p>
              </div>
            </div>
          )}

          {!mutation.isPending && result && (
            <div className="rounded-xl border border-success/30 bg-success/5 p-6 space-y-6">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-8 w-8 text-success" />
                <div>
                  <h3 className="font-semibold text-lg">Scrape Completed</h3>
                  <p className="text-sm text-muted-foreground">
                    Executed in {result.execution_time} seconds
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <ResultStat label="Fetched" value={result.fetched} />
                <ResultStat label="Validated" value={result.validated} />
                <ResultStat label="Duplicates Removed" value={result.duplicates_removed} />
                <ResultStat label="Failed" value={result.failed} />
              </div>

              <div className="rounded-lg bg-background border border-border p-4 text-center">
                <p className="text-sm font-medium text-muted-foreground">
                  Successfully Saved to Database
                </p>
                <p className="text-3xl font-bold text-success mt-1">{result.saved}</p>
              </div>
            </div>
          )}

          {!mutation.isPending && !result && errorMessage && (
            <div className="h-full rounded-xl border border-destructive/30 bg-destructive/5 p-6 flex flex-col items-center justify-center text-center space-y-3 min-h-[300px]">
              <CheckCircle2 className="h-10 w-10 text-destructive" />
              <div>
                <h3 className="font-medium text-destructive">Scrape failed</h3>
                <p className="text-sm text-destructive/80 mt-1 max-w-[400px] break-words">
                  {errorMessage}
                </p>
              </div>
            </div>
          )}

          {!mutation.isPending && !result && !errorMessage && (
            <div className="h-full rounded-xl border border-border border-dashed bg-card/50 p-6 flex flex-col items-center justify-center text-center space-y-3 min-h-[300px]">
              <Database className="h-10 w-10 text-muted-foreground" />
              <div>
                <h3 className="font-medium text-muted-foreground">Ready to Scrape</h3>
                <p className="text-sm text-muted-foreground/70 mt-1 max-w-[250px]">
                  Configure your search parameters and click "Run Scraper" to start fetching data.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-background border border-border p-3 text-center shadow-sm">
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground mt-1 font-medium uppercase tracking-wider">{label}</p>
    </div>
  );
}
