'use client';

import { useStatistics } from '@/lib/hooks/queries';
import { StatCard } from '@/components/ui/stat-card';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';
import { Briefcase, Building2, Globe, Wifi, Blend, MapPin, Copy, Calendar, BarChart3, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

export default function AnalyticsPage() {
  const { data, isLoading, isError, refetch } = useStatistics();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Analytics</h2>
          <p className="text-sm text-muted-foreground mt-1">Loading dashboard data...</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-muted/50 animate-pulse border border-border" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return <ErrorState title="Analytics unavailable" message="Failed to load statistics from the server." onRetry={() => refetch()} />;
  }

  if (!data || data.total_jobs === 0) {
    return (
      <div className="space-y-6">
         <div>
          <h2 className="text-2xl font-bold tracking-tight">Analytics</h2>
          <p className="text-sm text-muted-foreground mt-1">Visualise trends and insights.</p>
        </div>
        <EmptyState icon={BarChart3} title="Not enough data" description="Run the scraper to collect job data before viewing analytics." />
      </div>
    );
  }

  const chartData = [
    { name: 'Remote', value: data.remote_jobs, color: '#10b981' },
    { name: 'Hybrid', value: data.hybrid_jobs, color: '#3b82f6' },
    { name: 'Onsite', value: data.onsite_jobs, color: '#f59e0b' },
  ].filter(d => d.value > 0);

  const formatDate = (val?: string | null) => {
    if (!val) return '—';
    try {
      return formatDistanceToNow(new Date(val), { addSuffix: true });
    } catch {
      return '—';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Analytics</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Visualise trends and insights from your scraped database.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Jobs" value={data.total_jobs} icon={Briefcase} />
        <StatCard title="Total Companies" value={data.total_companies} icon={Building2} />
        <StatCard title="Total Countries" value={data.total_countries} icon={Globe} />
        <StatCard title="Easy Apply Jobs" value={data.easy_apply_jobs} icon={Briefcase} />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="md:col-span-2 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
           <StatCard title="Remote" value={data.remote_jobs} icon={Wifi} className="border-emerald-500/20 bg-emerald-500/5" />
           <StatCard title="Hybrid" value={data.hybrid_jobs} icon={Blend} className="border-blue-500/20 bg-blue-500/5" />
           <StatCard title="Onsite" value={data.onsite_jobs} icon={MapPin} className="border-amber-500/20 bg-amber-500/5" />
           
           <StatCard title="Duplicates Prevented" value={data.duplicate_count} icon={Copy} className="sm:col-span-2 lg:col-span-3" />
        </div>

        <div className="rounded-xl border border-border bg-card p-6 flex flex-col items-center justify-center">
           <h3 className="text-sm font-semibold mb-4 w-full text-left">Workplace Distribution</h3>
           <div className="h-48 w-full">
             <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartData} innerRadius={50} outerRadius={75} paddingAngle={2} dataKey="value">
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: unknown) => [`${value} jobs`, undefined]} />
                  <Legend />
                </PieChart>
             </ResponsiveContainer>
           </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-6 flex flex-col items-center justify-center overflow-hidden">
           <h3 className="text-sm font-semibold mb-4 w-full text-left">Top Companies</h3>
           <div className="h-64 w-full -ml-8">
             {data.top_companies && data.top_companies.length > 0 ? (
               <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.top_companies} layout="vertical" margin={{ left: 80, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }} />
                    <Tooltip cursor={{ fill: 'hsl(var(--muted))' }} contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))', borderRadius: '0.5rem' }} />
                    <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
               </ResponsiveContainer>
             ) : (
               <div className="flex h-full items-center justify-center text-sm text-muted-foreground ml-8">No data available</div>
             )}
           </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 flex flex-col items-center justify-center overflow-hidden">
           <h3 className="text-sm font-semibold mb-4 w-full text-left">Top Locations</h3>
           <div className="h-64 w-full -ml-8">
             {data.top_locations && data.top_locations.length > 0 ? (
               <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.top_locations} layout="vertical" margin={{ left: 80, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }} />
                    <Tooltip cursor={{ fill: 'hsl(var(--muted))' }} contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))', borderRadius: '0.5rem' }} />
                    <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
               </ResponsiveContainer>
             ) : (
               <div className="flex h-full items-center justify-center text-sm text-muted-foreground ml-8">No data available</div>
             )}
           </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
         <div className="rounded-xl border border-border bg-card p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-muted"><Calendar className="h-4 w-4 text-muted-foreground" /></div>
              <div>
                <p className="text-sm font-medium">First Scrape</p>
                <p className="text-xs text-muted-foreground">Oldest record in DB</p>
              </div>
            </div>
            <span className="font-semibold">{formatDate(data.oldest_scrape_date)}</span>
         </div>
         <div className="rounded-xl border border-border bg-card p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-muted"><Clock className="h-4 w-4 text-muted-foreground" /></div>
              <div>
                <p className="text-sm font-medium">Last Scrape</p>
                <p className="text-xs text-muted-foreground">Most recent record in DB</p>
              </div>
            </div>
            <span className="font-semibold">{formatDate(data.latest_scrape_date)}</span>
         </div>
      </div>
    </div>
  );
}
