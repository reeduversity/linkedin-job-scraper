'use client';

import { useHealth } from '@/lib/hooks/queries';
import { cn } from '@/lib/utils';

export function HealthIndicator({ className }: { className?: string }) {
  const { data, isLoading, isError } = useHealth();

  const status = isError
    ? 'offline'
    : isLoading
      ? 'checking'
      : data?.status === 'healthy'
        ? 'healthy'
        : 'degraded';

  const colors: Record<string, string> = {
    healthy: 'bg-emerald-500',
    degraded: 'bg-amber-500',
    offline: 'bg-red-500',
    checking: 'bg-muted-foreground',
  };

  const labels: Record<string, string> = {
    healthy: 'API Healthy',
    degraded: 'API Degraded',
    offline: 'API Offline',
    checking: 'Checking…',
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span
        className={cn('h-2 w-2 rounded-full', colors[status], {
          'animate-pulse': status === 'checking',
        })}
      />
      <span className="text-xs font-medium text-muted-foreground">
        {labels[status]}
      </span>
    </div>
  );
}
