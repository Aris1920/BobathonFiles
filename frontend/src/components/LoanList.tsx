import { useState } from 'react';
import type { Loan, LoanCreate } from '../types';
import LoanCard from './LoanCard';

const LOAN_TYPE_LABELS: Record<Loan['loan_type'], string> = {
  federal_subsidized: 'Federal Subsidized',
  federal_unsubsidized: 'Federal Unsubsidized',
  federal_grad_plus: 'Federal Grad PLUS',
  private: 'Private',
};

const EMPTY_FORM: NewLoanForm = {
  label: '',
  loan_type: 'federal_subsidized',
  balance: '',
  rate_pct: '',
  minimum_monthly_payment: '',
};

interface NewLoanForm {
  label: string;
  loan_type: Loan['loan_type'];
  balance: string;
  rate_pct: string;
  minimum_monthly_payment: string;
}

interface LoanListProps {
  loans: Loan[];
  onAdd: (data: LoanCreate) => void;
  onUpdate: (id: string, data: Partial<LoanCreate>) => void;
  onDelete: (id: string) => void;
}

export default function LoanList({ loans, onAdd, onUpdate, onDelete }: LoanListProps) {
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState<NewLoanForm>(EMPTY_FORM);

  function handleAdd() {
    if (!form.label || !form.balance || !form.rate_pct || !form.minimum_monthly_payment) return;
    onAdd({
      label: form.label,
      loan_type: form.loan_type,
      balance: parseFloat(form.balance),
      annual_interest_rate: parseFloat(form.rate_pct) / 100,
      minimum_monthly_payment: parseFloat(form.minimum_monthly_payment),
    });
    setForm(EMPTY_FORM);
    setAdding(false);
  }

  return (
    <div className="space-y-3">
      {loans.map((loan) => (
        <LoanCard key={loan.id} loan={loan} onUpdate={onUpdate} onDelete={onDelete} />
      ))}

      {adding ? (
        <div className="bg-white border border-blue-300 rounded-lg p-4 space-y-3">
          <h4 className="text-sm font-semibold text-gray-800">New Student Loan</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
              <input
                type="text"
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
                placeholder="e.g. Federal Direct Subsidized"
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
                onChange={(e) => setForm({ ...form, balance: e.target.value })}
                placeholder="25000"
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
                placeholder="5.5"
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
                onChange={(e) => setForm({ ...form, minimum_monthly_payment: e.target.value })}
                placeholder="200"
                className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
            >
              Add
            </button>
            <button
              onClick={() => { setAdding(false); setForm(EMPTY_FORM); }}
              className="px-4 py-1.5 border border-gray-300 text-gray-600 text-sm rounded-md hover:border-gray-400 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="w-full py-2.5 border-2 border-dashed border-gray-300 text-gray-500 text-sm rounded-lg hover:border-blue-400 hover:text-blue-600 transition-colors"
        >
          + Add Student Loan
        </button>
      )}
    </div>
  );
}
