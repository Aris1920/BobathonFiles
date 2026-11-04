import type { JobResult } from '../types';
import FitBadge from './FitBadge';
import SourceBadge from './SourceBadge';

interface JobCardProps {
  job: JobResult;
}

const fmt = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

export default function JobCard({ job }: JobCardProps) {
  const hasSalary = job.salary_min !== null || job.salary_max !== null;

  let salaryText: string;
  if (!hasSalary) {
    salaryText = 'Salary not listed';
  } else if (job.salary_min !== null && job.salary_max !== null) {
    salaryText = `${fmt.format(job.salary_min)} – ${fmt.format(job.salary_max)}`;
  } else if (job.salary_min !== null) {
    salaryText = `From ${fmt.format(job.salary_min)}`;
  } else {
    salaryText = `Up to ${fmt.format(job.salary_max!)}`;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <FitBadge score={job.fit_score} />
        <SourceBadge source={job.source} />
      </div>

      <div>
        <p className="font-semibold text-gray-900 text-sm leading-snug">{job.job_title}</p>
        <p className="text-gray-500 text-xs mt-0.5">
          {job.company} · {job.location}
        </p>
      </div>

      <p className="text-gray-700 text-xs font-medium">{salaryText}</p>

      {job.job_url && (
        <a
          href={job.job_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-700 text-xs font-medium inline-flex items-center gap-0.5 w-fit"
        >
          View Listing ↗
        </a>
      )}
    </div>
  );
}
