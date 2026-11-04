import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import type { DebtProjection } from '../types';

interface PayoffChartProps {
  high: DebtProjection;
  mid: DebtProjection;
  low: DebtProjection;
}

const TIER_COLORS = ['#22c55e', '#f59e0b', '#ef4444'];

export default function PayoffChart({ high, mid, low }: PayoffChartProps) {
  const data = [
    { tier: 'High Fit', months: high.months_to_payoff },
    { tier: 'Mid Fit', months: mid.months_to_payoff },
    { tier: 'Low Fit', months: low.months_to_payoff },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-sm font-semibold text-gray-700 mb-4">
        Months to Pay Off Student Loans by Job Tier
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis
            dataKey="tier"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
            label={{ value: 'Months', angle: -90, position: 'insideLeft', offset: 10, style: { fontSize: 11, fill: '#9ca3af' } }}
          />
          <Tooltip
            formatter={(value: number) => [`${value} months`, 'Payoff time']}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
          />
          <Bar dataKey="months" radius={[6, 6, 0, 0]}>
            {data.map((_entry, index) => (
              <Cell key={`cell-${index}`} fill={TIER_COLORS[index]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
