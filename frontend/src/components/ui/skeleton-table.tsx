import { cn } from '@/lib/utils';

interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export function SkeletonTable({
  rows = 5,
  columns = 4,
  className,
}: SkeletonTableProps) {
  return (
    <div className={cn('w-full overflow-hidden rounded-lg border border-border', className)}>
      {/* Header */}
      <div className="flex gap-4 border-b border-border bg-muted/40 px-4 py-3">
        {Array.from({ length: columns }).map((_, i) => (
          <div
            key={`h-${i}`}
            className="h-4 flex-1 animate-pulse rounded bg-muted"
          />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, ri) => (
        <div
          key={`r-${ri}`}
          className="flex gap-4 border-b border-border px-4 py-3 last:border-b-0"
        >
          {Array.from({ length: columns }).map((_, ci) => (
            <div
              key={`c-${ri}-${ci}`}
              className="h-4 flex-1 animate-pulse rounded bg-muted"
              style={{ animationDelay: `${(ri * columns + ci) * 50}ms` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
