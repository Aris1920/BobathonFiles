import type { DebtProjection } from '../types';

interface LoanProjectionComparisonProps {
  high: DebtProjection;
  mid: DebtProjection;
  low: DebtProjection;
}

const fmt = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

function formatMonths(months: number): string {
  if (months < 12) return `${months} mo`;
  const years = Math.floor(months / 12);
  const remaining = months % 12;
  return remaining === 0 ? `${years} yr` : `${years} yr ${remaining} mo`;
}

interface TierCardProps {
  label: string;
  projection: DebtProjection;
  speedRank: 'fastest' | 'middle' | 'slowest';
}

function TierCard({ label, projection, speedRank }: TierCardProps) {
  const bgClass =
    speedRank === 'fastest'
      ? 'bg-green-50 border-green-200'
      : speedRank === 'slowest'
      ? 'bg-red-50 border-red-200'
      : 'bg-amber-50 border-amber-200';

  const headingClass =
    speedRank === 'fastest'
      ? 'text-green-700'
      : speedRank === 'slowest'
      ? 'text-red-700'
      : 'text-amber-700';

  const monthsClass =
    speedRank === 'fastest'
      ? 'text-green-800'
      : speedRank === 'slowest'
      ? 'text-red-800'
      : 'text-amber-800';

  return (
    <div className={`flex-1 rounded-xl border p-5 flex flex-col gap-3 ${bgClass}`}>
      <h3 className={`font-bold text-sm ${headingClass}`}>{label}</h3>

      <div className="space-y-1 text-xs text-gray-600">
        <p>
          Salary used:{' '}
          <span className="font-medium text-gray-800">
            {fmt.format(projection.median_salary_used)}/yr
          </span>
        </p>
        <p>
          Savings rate:{' '}
          <span className="font-medium text-gray-800">{projection.savings_rate_pct}%</span>
        </p>
      </div>

      <div className="mt-1">
        <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Months to pay off</p>
        <p className={`text-3xl font-extrabold leading-tight mt-0.5 ${monthsClass}`}>
          {formatMonths(projection.months_to_payoff)}
        </p>
      </div>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Total interest</p>
        <p className="text-lg font-bold text-gray-800 mt-0.5">
          {fmt.format(projection.total_interest_paid)}
        </p>
      </div>
    </div>
  );
}

export default function LoanProjectionComparison({ high, mid, low }: LoanProjectionComparisonProps) {
  const tiers = [
    { label: 'High Fit', projection: high },
    { label: 'Mid Fit', projection: mid },
    { label: 'Low Fit', projection: low },
  ];

  const months = [high.months_to_payoff, mid.months_to_payoff, low.months_to_payoff];
  const minMonths = Math.min(...months);
  const maxMonths = Math.max(...months);

  function speedRank(p: DebtProjection): 'fastest' | 'middle' | 'slowest' {
    if (p.months_to_payoff === minMonths) return 'fastest';
    if (p.months_to_payoff === maxMonths) return 'slowest';
    return 'middle';
  }

  return (
    <div className="flex flex-col sm:flex-row gap-4">
      {tiers.map(({ label, projection }) => (
        <TierCard
          key={label}
          label={label}
          projection={projection}
          speedRank={speedRank(projection)}
        />
      ))}
    </div>
  );
}
