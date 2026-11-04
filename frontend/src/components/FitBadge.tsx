interface FitBadgeProps {
  score: number;
}

export default function FitBadge({ score }: FitBadgeProps) {
  let colorClass: string;
  let label: string;

  if (score >= 70) {
    colorClass = 'bg-green-100 text-green-800';
    label = 'High Fit';
  } else if (score >= 40) {
    colorClass = 'bg-amber-100 text-amber-800';
    label = 'Mid Fit';
  } else {
    colorClass = 'bg-red-100 text-red-800';
    label = 'Low Fit';
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {label} · {score}
    </span>
  );
}
