'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useSchedulerStatus, queryKeys } from '@/lib/hooks/queries';
import { startScheduler, stopScheduler, runSchedulerOnce } from '@/lib/api/scheduler';
import { useToast } from '@/components/ui/toast';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { ErrorState } from '@/components/ui/error-state';
import { Clock, Play, Square, Zap, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

export default function SchedulerPage() {
  const { data, isLoading, isError, refetch } = useSchedulerStatus();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [confirmStopOpen, setConfirmStopOpen] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.schedulerStatus });
  };

  const startMutation = useMutation({
    mutationFn: startScheduler,
    onSuccess: () => {
      invalidate();
      toast({ variant: 'success', title: 'Scheduler started', description: 'The automated scraping schedule is now active.' });
    },
    onError: (err: unknown) => {
      toast({ variant: 'error', title: 'Failed to start', description: (err as Error)?.message || 'Could not start scheduler.' });
    }
  });

  const stopMutation = useMutation({
    mutationFn: stopScheduler,
    onSuccess: () => {
      invalidate();
      setConfirmStopOpen(false);
      toast({ variant: 'success', title: 'Scheduler stopped', description: 'The automated scraping schedule has been paused.' });
    },
    onError: (err: unknown) => {
      toast({ variant: 'error', title: 'Failed to stop', description: (err as Error)?.message || 'Could not stop scheduler.' });
    }
  });

  const runOnceMutation = useMutation({
    mutationFn: runSchedulerOnce,
    onSuccess: () => {
      invalidate();
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs() });
      queryClient.invalidateQueries({ queryKey: queryKeys.statistics });
      toast({ variant: 'success', title: 'Scrape started', description: 'A one-off scraping job has been dispatched.' });
    },
    onError: (err: unknown) => {
      toast({ variant: 'error', title: 'Failed to run', description: (err as Error)?.message || 'Could not dispatch one-off job.' });
    }
  });

  const isPending = startMutation.isPending || stopMutation.isPending || runOnceMutation.isPending;

  const formatDate = (val?: string | null) => {
    if (!val) return '—';
    try {
      return formatDistanceToNow(new Date(val), { addSuffix: true });
    } catch {
      return '—';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Scheduler</h2>
          <p className="text-sm text-muted-foreground mt-1">Manage automated scraping schedules.</p>
        </div>
        <div className="h-64 rounded-xl border border-border bg-card animate-pulse" />
      </div>
    );
  }

  if (isError) {
    return <ErrorState title="Scheduler unavailable" message="Failed to load scheduler status." onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Scheduler</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Automate your job scraping by running tasks on a defined interval.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Status Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col">
          <div className="flex items-center gap-3 mb-6">
            <div className={cn("p-3 rounded-full", data?.running ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground")}>
              <Clock className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold leading-none">Scheduler Status</h3>
              <p className={cn("text-sm mt-1 font-medium", data?.running ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground")}>
                {data?.running ? 'Running' : 'Stopped'}
              </p>
            </div>
          </div>

          <div className="space-y-4 flex-1">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="text-sm text-muted-foreground">Interval</span>
              <span className="text-sm font-medium">{data?.interval ? `${data.interval} minutes` : '—'}</span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="text-sm text-muted-foreground">Last Run</span>
              <span className="text-sm font-medium">{formatDate(data?.last_run)}</span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="text-sm text-muted-foreground">Next Run</span>
              <span className="text-sm font-medium">{data?.running ? formatDate(data?.next_run) : '—'}</span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="text-sm text-muted-foreground">Jobs Executed</span>
              <span className="text-sm font-medium">{data?.jobs_executed ?? 0}</span>
            </div>
          </div>
        </div>

        {/* Actions Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col">
          <div className="mb-6">
            <h3 className="text-lg font-semibold leading-none">Controls</h3>
            <p className="text-sm text-muted-foreground mt-1">Start, stop, or force execution.</p>
          </div>

          <div className="space-y-4 flex-1 flex flex-col justify-center">
            {data?.running ? (
              <button
                onClick={() => setConfirmStopOpen(true)}
                disabled={isPending}
                className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-destructive px-4 py-2.5 text-sm font-medium text-destructive-foreground shadow transition-colors hover:bg-destructive/90 disabled:opacity-50"
              >
                {stopMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4 fill-current" />}
                Stop Scheduler
              </button>
            ) : (
              <button
                onClick={() => startMutation.mutate()}
                disabled={isPending}
                className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow transition-colors hover:bg-emerald-600/90 disabled:opacity-50"
              >
                {startMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />}
                Start Scheduler
              </button>
            )}

            <div className="relative">
              <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border" /></div>
              <div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">or</span></div>
            </div>

            <button
              onClick={() => runOnceMutation.mutate()}
              disabled={isPending}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-md border border-input bg-background px-4 py-2.5 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
            >
              {runOnceMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4 fill-amber-500 text-amber-500" />}
              Run Once Now
            </button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={confirmStopOpen}
        onOpenChange={setConfirmStopOpen}
        title="Stop Scheduler?"
        description="This will pause automated background scraping. You will need to start it manually later."
        confirmLabel="Stop Scheduler"
        cancelLabel="Cancel"
        variant="destructive"
        onConfirm={() => stopMutation.mutate()}
      />
    </div>
  );
}
