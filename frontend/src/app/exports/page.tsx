'use client';

import { useState } from 'react';
import { useToast } from '@/components/ui/toast';
import { downloadCsv, downloadExcel, downloadJson } from '@/lib/api/exports';
import { Download, FileText, FileSpreadsheet, FileJson, Loader2 } from 'lucide-react';

export default function ExportsPage() {
  const { toast } = useToast();
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleDownload = async (type: 'csv' | 'excel' | 'json') => {
    setDownloading(type);
    try {
      if (type === 'csv') await downloadCsv();
      if (type === 'excel') await downloadExcel();
      if (type === 'json') await downloadJson();

      toast({
        variant: 'success',
        title: 'Export successful',
        description: `Your ${type.toUpperCase()} file has been downloaded.`,
      });
    } catch (err: unknown) {
      toast({
        variant: 'error',
        title: 'Export failed',
        description: (err as Error)?.message || 'Could not download the file. Make sure the backend is reachable.',
      });
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Data Exports</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Download your scraped job database in various formats for offline analysis.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-3">
        {/* CSV */}
        <div className="flex flex-col items-center text-center p-8 rounded-xl border border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="rounded-full bg-blue-500/10 p-4 mb-4">
            <FileText className="h-8 w-8 text-blue-500" />
          </div>
          <h3 className="font-semibold text-lg">CSV Export</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6 flex-1">
            Standard Comma-Separated Values format. Best for importing into generic tools or data pipelines.
          </p>
          <button
            onClick={() => handleDownload('csv')}
            disabled={downloading !== null}
            className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-secondary px-4 py-2.5 text-sm font-medium hover:bg-secondary/80 disabled:opacity-50"
          >
            {downloading === 'csv' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {downloading === 'csv' ? 'Downloading...' : 'Download CSV'}
          </button>
        </div>

        {/* Excel */}
        <div className="flex flex-col items-center text-center p-8 rounded-xl border border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="rounded-full bg-emerald-500/10 p-4 mb-4">
            <FileSpreadsheet className="h-8 w-8 text-emerald-500" />
          </div>
          <h3 className="font-semibold text-lg">Excel Export</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6 flex-1">
            Native .xlsx file format. Best for analysis in Microsoft Excel or Google Sheets.
          </p>
          <button
            onClick={() => handleDownload('excel')}
            disabled={downloading !== null}
            className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600/90 disabled:opacity-50"
          >
            {downloading === 'excel' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {downloading === 'excel' ? 'Downloading...' : 'Download Excel'}
          </button>
        </div>

        {/* JSON */}
        <div className="flex flex-col items-center text-center p-8 rounded-xl border border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="rounded-full bg-amber-500/10 p-4 mb-4">
            <FileJson className="h-8 w-8 text-amber-500" />
          </div>
          <h3 className="font-semibold text-lg">JSON Export</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6 flex-1">
            Raw JavaScript Object Notation. Best for developers and system integrations.
          </p>
          <button
            onClick={() => handleDownload('json')}
            disabled={downloading !== null}
            className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-secondary px-4 py-2.5 text-sm font-medium hover:bg-secondary/80 disabled:opacity-50"
          >
            {downloading === 'json' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {downloading === 'json' ? 'Downloading...' : 'Download JSON'}
          </button>
        </div>
      </div>
    </div>
  );
}
