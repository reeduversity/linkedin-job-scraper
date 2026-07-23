'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { X, ExternalLink, CalendarDays, MapPin, Building2, Briefcase, Globe, Blend, Mail } from 'lucide-react';
import type { LinkedInJob } from '@/lib/types/api';
import { formatDistanceToNow } from 'date-fns';

interface JobDetailsDialogProps {
  job: LinkedInJob | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function JobDetailsDialog({ job, open, onOpenChange }: JobDetailsDialogProps) {
  if (!job) return null;

  const formatDate = (val?: string | null) => {
    if (!val) return '—';
    try {
      return formatDistanceToNow(new Date(val), { addSuffix: true });
    } catch {
      return '—';
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl max-h-[90vh] overflow-y-auto -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-0 shadow-2xl focus:outline-none data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95">
          <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card/95 backdrop-blur px-6 py-4">
            <div>
              <Dialog.Title className="text-lg font-semibold leading-none tracking-tight">
                {job.job_title ?? 'Job Details'}
              </Dialog.Title>
              <div className="flex items-center gap-2 mt-1.5">
                <Dialog.Description className="text-sm text-muted-foreground">
                  {job.company_name ?? 'Unknown Company'}
                </Dialog.Description>
                {job.source_type === 'LINKEDIN_HIRING_POST' && (
                  <span className="inline-flex items-center rounded-md bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 ring-1 ring-inset ring-emerald-500/20">
                    Direct Hiring Post
                  </span>
                )}
              </div>
            </div>
            <Dialog.Close asChild>
              <button className="focus-ring rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>
          
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
               <InfoItem icon={MapPin} label="Location" value={job.location} />
               <InfoItem icon={Globe} label="Country" value={job.country} />
               <InfoItem icon={Blend} label="Workplace" value={job.workplace_type} />
               <InfoItem icon={Briefcase} label="Type" value={job.employment_type} />
               <InfoItem icon={Building2} label="Level" value={job.experience_level} />
               <InfoItem icon={CalendarDays} label="Posted" value={formatDate(job.posted_date)} />
               {job.application_method && (
                 <InfoItem icon={Mail} label="Apply Via" value={job.application_method.replace('_', ' ')} />
               )}
               {job.application_email && (
                 <InfoItem icon={Mail} label="Email" value={job.application_email} />
               )}
               {job.application_platform && (
                 <InfoItem icon={Globe} label="Platform" value={job.application_platform} />
               )}
            </div>
            
            {(job.salary || job.easy_apply) && (
              <div className="flex flex-wrap gap-2">
                {job.salary && (
                  <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2.5 py-1 text-sm font-medium text-emerald-600 dark:text-emerald-400">
                    {job.currency} {job.salary}
                  </span>
                )}
                {job.easy_apply && (
                  <span className="inline-flex items-center rounded-md bg-blue-500/10 px-2.5 py-1 text-sm font-medium text-blue-600 dark:text-blue-400">
                    Easy Apply
                  </span>
                )}
              </div>
            )}

            {job.description && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium">Description</h3>
                <div className="text-sm text-muted-foreground whitespace-pre-wrap rounded-lg bg-muted/30 p-4 leading-relaxed">
                  {job.description}
                </div>
              </div>
            )}

            <div className="flex flex-col gap-3 pt-4 border-t border-border mt-4">
               {job.source_type === 'LINKEDIN_HIRING_POST' ? (
                 <div className="space-y-4">
                   <h3 className="text-sm font-semibold">Application Instructions</h3>
                   {(!job.application_methods || job.application_methods.length === 0) ? (
                     <p className="text-sm text-muted-foreground italic">Application instructions not provided.</p>
                   ) : (
                     <div className="flex flex-col gap-3">
                       {job.application_methods.includes('EMAIL') && job.application_email && (
                         <div className="flex flex-col gap-2 rounded-lg border border-border p-4 bg-muted/20">
                           <span className="text-sm font-medium">Application Email: <span className="text-muted-foreground font-normal">{job.application_email}</span></span>
                           <div className="flex gap-2">
                             <button
                               onClick={() => navigator.clipboard.writeText(job.application_email!)}
                               className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
                             >
                               Copy Email
                             </button>
                             <a
                               href={`mailto:${job.application_email}`}
                               className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
                             >
                               Email
                             </a>
                           </div>
                         </div>
                       )}
                       {job.application_methods.includes('FORM') && job.application_url && (
                         <a
                           href={job.application_url}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 w-fit"
                         >
                           Apply via {job.application_platform === 'GOOGLE_FORMS' ? 'Google Form' : 'Form'} <ExternalLink className="h-4 w-4" />
                         </a>
                       )}
                       {job.application_methods.includes('EXTERNAL_LINK') && job.application_url && (
                         <a
                           href={job.application_url}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 w-fit"
                         >
                           Apply Now <ExternalLink className="h-4 w-4" />
                         </a>
                       )}
                       {job.application_methods.includes('DIRECT_MESSAGE') && (job.post_author_profile_url || job.post_url) && (
                         <a
                           href={job.post_author_profile_url || job.post_url}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="inline-flex items-center justify-center gap-2 rounded-md bg-[#0a66c2] px-4 py-2.5 text-sm font-medium text-white shadow transition-colors hover:bg-[#004182] w-fit"
                         >
                           Contact Hiring Person on LinkedIn <ExternalLink className="h-4 w-4" />
                         </a>
                       )}
                       {job.application_methods.includes('COMMENT') && job.post_url && (
                         <a
                           href={job.post_url}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="inline-flex items-center justify-center gap-2 rounded-md bg-[#0a66c2] px-4 py-2.5 text-sm font-medium text-white shadow transition-colors hover:bg-[#004182] w-fit"
                         >
                           Apply by Commenting on Post <ExternalLink className="h-4 w-4" />
                         </a>
                       )}
                     </div>
                   )}
                   {job.post_url && (
                     <div className="pt-2">
                       <a
                         href={job.post_url}
                         target="_blank"
                         rel="noopener noreferrer"
                         className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground underline underline-offset-4"
                       >
                         View Original Post <ExternalLink className="h-3 w-3" />
                       </a>
                     </div>
                   )}
                 </div>
               ) : (
                 <div className="flex flex-wrap gap-3">
                   {job.linkedin_job_url && (
                     <a
                       href={job.linkedin_job_url}
                       target="_blank"
                       rel="noopener noreferrer"
                       className="focus-ring inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
                     >
                       View on LinkedIn <ExternalLink className="h-4 w-4" />
                     </a>
                   )}
                   {job.application_url && (
                     <a
                       href={job.application_url}
                       target="_blank"
                       rel="noopener noreferrer"
                       className="focus-ring inline-flex items-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
                     >
                       Company Website <ExternalLink className="h-4 w-4" />
                     </a>
                   )}
                 </div>
               )}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function InfoItem({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value?: string | null }) {
  return (
    <div className="space-y-1">
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </span>
      <p className="text-sm font-medium">{value ?? '—'}</p>
    </div>
  );
}
