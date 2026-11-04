import type { TierResult } from '../types';
import JobCard from './JobCard';

interface TierColumnProps {
  tier: TierResult;
  color: 'green' | 'amber' | 'red';
  label: string;
}

const fmt = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

const COLOR_CLASSES: Record<TierColumnProps['color'], { dot: string; text: string; border: string }> = {
  green: { dot: 'bg-green-500', text: 'text-green-700', border: 'border-green-200' },
  amber: { dot: 'bg-amber-500', text: 'text-amber-700', border: 'border-amber-200' },
  red: { dot: 'bg-red-500', text: 'text-red-700', border: 'border-red-200' },
};

export default function TierColumn({ tier, color, label }: TierColumnProps) {
  const c = COLOR_CLASSES[color];
  const { jobs, salary_stats } = tier;

  // SalaryStats fields are always numbers; guard against 0/NaN from sparse data
  const hasSalaryStats =
    salary_stats.min > 0 &&
    salary_stats.max > 0 &&
    salary_stats.median > 0;

  return (
    <div className={`flex flex-col gap-3 rounded-xl border ${c.border} bg-gray-50 p-4`}>
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className={`w-3 h-3 rounded-full flex-shrink-0 ${c.dot}`} />
        <h2 className={`font-bold text-base ${c.text}`}>{label}</h2>
      </div>

      {/* Stats bar */}
      <div className="text-xs text-gray-600 space-y-0.5">
        <p>
          <span className="font-medium text-gray-800">{jobs.length}</span>{' '}
          {jobs.length === 1 ? 'job' : 'jobs'}
        </p>
        {hasSalaryStats && (
          <>
            <p>
              Range:{' '}
              <span className="font-medium text-gray-800">
                {fmt.format(salary_stats.min)} – {fmt.format(salary_stats.max)}
              </span>
            </p>
            <p>
              Median:{' '}
              <span className="font-medium text-gray-800">{fmt.format(salary_stats.median)}</span>
            </p>
          </>
        )}
      </div>

      {/* Job list */}
      <div
        className="flex flex-col gap-2 overflow-y-auto pr-0.5"
        style={{ maxHeight: '60vh' }}
      >
        {jobs.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-6">No jobs in this tier</p>
        ) : (
          jobs.map((job) => <JobCard key={job.id} job={job} />)
        )}
      </div>
    </div>
  );
}
