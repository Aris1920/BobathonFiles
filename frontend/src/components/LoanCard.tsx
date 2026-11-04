import { useState } from 'react';
import type { Loan, LoanCreate } from '../types';

const LOAN_TYPE_LABELS: Record<Loan['loan_type'], string> = {
  federal_subsidized: 'Federal Subsidized',
  federal_unsubsidized: 'Federal Unsubsidized',
  federal_grad_plus: 'Federal Grad PLUS',
  private: 'Private',
};

interface LoanCardProps {
  loan: Loan;
  onUpdate: (id: string, data: Partial<LoanCreate>) => void;
  onDelete: (id: string) => void;
}

export default function LoanCard({ loan, onUpdate, onDelete }: LoanCardProps) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Omit<LoanCreate, 'annual_interest_rate'> & { rate_pct: string }>({
    label: loan.label,
    loan_type: loan.loan_type,
    balance: loan.balance,
    rate_pct: String(+(loan.annual_interest_rate * 100).toFixed(4)),
    minimum_monthly_payment: loan.minimum_monthly_payment,
  });

  function handleSave() {
    onUpdate(loan.id, {
      label: form.label,
      loan_type: form.loan_type,
      balance: Number(form.balance),
      annual_interest_rate: parseFloat(form.rate_pct) / 100,
      minimum_monthly_payment: Number(form.minimum_monthly_payment),
    });
    setEditing(false);
  }

  function handleDelete() {
    if (window.confirm(`Delete loan "${loan.label}"?`)) {
      onDelete(loan.id);
    }
  }

  if (editing) {
    return (
      <div className="bg-white border border-blue-300 rounded-lg p-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
            <input
              type="text"
              value={form.label}
              onChange={(e) => setForm({ ...form, label: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Loan Type</label>
            <select
              value={form.loan_type}
              onChange={(e) => setForm({ ...form, loan_type: e.target.value as Loan['loan_type'] })}
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {(Object.entries(LOAN_TYPE_LABELS) as [Loan['loan_type'], string][]).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Balance ($)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.balance}
              onChange={(e) => setForm({ ...form, balance: +e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Annual Interest Rate (%)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.rate_pct}
              onChange={(e) => setForm({ ...form, rate_pct: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Min Monthly Payment ($)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.minimum_monthly_payment}
              onChange={(e) => setForm({ ...form, minimum_monthly_payment: +e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
          >
            Save
          </button>
          <button
            onClick={() => setEditing(false)}
            className="px-4 py-1.5 border border-gray-300 text-gray-600 text-sm rounded-md hover:border-gray-400 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-start justify-between gap-4">
      <div className="space-y-1 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-gray-900 text-sm">{loan.label}</span>
          <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full font-medium">
            {LOAN_TYPE_LABELS[loan.loan_type]}
          </span>
        </div>
        <div className="flex gap-4 text-sm text-gray-600 flex-wrap">
          <span>Balance: <span className="font-medium text-gray-900">${loan.balance.toLocaleString()}</span></span>
          <span>Rate: <span className="font-medium text-gray-900">{(loan.annual_interest_rate * 100).toFixed(2)}%</span></span>
          <span>Min payment: <span className="font-medium text-gray-900">${loan.minimum_monthly_payment.toLocaleString()}/mo</span></span>
        </div>
      </div>
      <div className="flex gap-2 shrink-0">
        <button
          onClick={() => setEditing(true)}
          className="px-3 py-1.5 border border-gray-300 text-gray-600 text-xs rounded-md hover:border-gray-400 transition-colors"
        >
          Edit
        </button>
        <button
          onClick={handleDelete}
          className="px-3 py-1.5 border border-red-200 text-red-600 text-xs rounded-md hover:bg-red-50 transition-colors"
          aria-label="Delete loan"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
