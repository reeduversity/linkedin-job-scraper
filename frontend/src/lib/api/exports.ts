import { apiClient } from './client';

const EXPORT_BASE = '/api/export';

async function downloadBlob(path: string, filename: string): Promise<void> {
  const response = await apiClient.get(path, { responseType: 'blob' });
  const blob = new Blob([response.data as BlobPart]);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function downloadCsv(): Promise<void> {
  return downloadBlob(`${EXPORT_BASE}/csv`, 'linkedin_jobs.csv');
}

export function downloadExcel(): Promise<void> {
  return downloadBlob(`${EXPORT_BASE}/excel`, 'linkedin_jobs.xlsx');
}

export function downloadJson(): Promise<void> {
  return downloadBlob(`${EXPORT_BASE}/json`, 'linkedin_jobs.json');
}
