import type { JobResult } from '../types';

type Source = JobResult['source'];

interface SourceBadgeProps {
  source: Source;
}

const SOURCE_CONFIG: Record<Source, { label: string; style: React.CSSProperties }> = {
  linkedin: {
    label: 'LinkedIn',
    style: { backgroundColor: '#0077b5', color: '#ffffff' },
  },
  handshake: {
    label: 'Handshake',
    style: { backgroundColor: '#E05C82', color: '#ffffff' },
  },
  indeed: {
    label: 'Indeed',
    style: { backgroundColor: '#4338ca', color: '#ffffff' },
  },
  usajobs: {
    label: 'USAJobs',
    style: { backgroundColor: '#1e3a5f', color: '#ffffff' },
  },
};

export default function SourceBadge({ source }: SourceBadgeProps) {
  const { label, style } = SOURCE_CONFIG[source];

  return (
    <span
      className="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
      style={style}
    >
      {label}
    </span>
  );
}
