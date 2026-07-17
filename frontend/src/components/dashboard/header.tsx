'use client';

import { usePathname } from 'next/navigation';
import { RefreshCw } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { ThemeToggle } from '../ui/theme-toggle';
import { HealthIndicator } from './health-indicator';
import { MobileNav } from './mobile-nav';
import { navigationItems } from './sidebar';
import { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';

export function Header() {
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const currentPage = navigationItems.find(
    (item) =>
      pathname === item.href || pathname.startsWith(item.href + '/'),
  );

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries();
    // Brief visual feedback
    setTimeout(() => setIsRefreshing(false), 600);
  }, [queryClient]);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-4 border-b border-border glass px-4">
      {/* Mobile menu trigger */}
      <MobileNav open={mobileOpen} onOpenChange={setMobileOpen} />

      {/* Page title / breadcrumb */}
      <div className="flex-1 min-w-0">
        <h1 className="text-sm font-semibold truncate">
          {currentPage?.name ?? 'Dashboard'}
        </h1>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <HealthIndicator />

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
          aria-label="Refresh all data"
        >
          <RefreshCw
            className={cn('h-4 w-4', isRefreshing && 'animate-spin')}
          />
        </button>

        <ThemeToggle />
      </div>
    </header>
  );
}
