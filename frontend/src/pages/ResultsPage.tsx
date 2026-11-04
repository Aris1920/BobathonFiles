import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateResults, getLatestResults } from '../api/results';
import type { ResultsResponse } from '../types';
import Navbar from '../components/Navbar';
import TierColumn from '../components/TierColumn';
import LoanProjectionComparison from '../components/LoanProjectionComparison';
import PayoffChart from '../components/PayoffChart';
import SavingsRateSlider from '../components/SavingsRateSlider';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export default function ResultsPage() {
  const navigate = useNavigate();

  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingsRate, setSavingsRate] = useState(20);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load on mount
  useEffect(() => {
    getLatestResults()
      .then((data) => {
        setResults(data);
      })
      .catch((err) => {
        if (err?.response?.status === 404) {
          navigate('/profile', {
            state: { message: 'Generate your first results from your profile page.' },
          });
        } else {
          setError('Failed to load results. Please try again.');
        }
      })
      .finally(() => setIsLoading(false));
  }, [navigate]);

  // Debounced regeneration when savings rate changes (skip on initial mount)
  const isFirstRender = useRef(true);
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      handleRegenerate(savingsRate);
    }, 1000);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savingsRate]);

  async function handleRegenerate(rate: number = savingsRate) {
    setIsRegenerating(true);
    setError(null);
    try {
      const data = await generateResults(rate);
      setResults(data);
    } catch {
      setError('Failed to regenerate results. Your previous results are still shown below.');
    } finally {
      setIsRegenerating(false);
    }
  }

  // Compute a rough monthly take-home for the slider display.
  // Use the high-tier median salary if available, otherwise fall back to a default.
  const roughMonthlyTakeHome = results
    ? (results.high_tier.debt_projection.median_salary_used / 12) * 0.75
    : 4000;

  // ------------------------------------------------------------------
  // Loading state
  // ------------------------------------------------------------------
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center py-32">
          <div className="flex items-center gap-3 text-gray-500">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Loading your results…
          </div>
        </div>
      </div>
    );
  }

  // ------------------------------------------------------------------
  // Error state (no results at all)
  // ------------------------------------------------------------------
  if (error && !results) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-lg mx-auto px-6 py-20 text-center">
          <p className="text-red-600 font-medium">{error}</p>
          <button
            onClick={() => handleRegenerate()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // ------------------------------------------------------------------
  // Main dashboard
  // ------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* ── Page header ── */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Your Career Matches</h1>
            {results && (
              <p className="text-sm text-gray-500 mt-0.5">
                Generated {formatDate(results.created_at)}
              </p>
            )}
          </div>
          <button
            onClick={() => handleRegenerate()}
            disabled={isRegenerating}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isRegenerating && (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            )}
            Regenerate →
          </button>
        </div>

        {/* ── Regeneration banner ── */}
        {isRegenerating && (
          <div className="w-full flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-xl px-5 py-3 text-blue-700 text-sm font-medium">
            <svg className="animate-spin h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Searching for jobs…
          </div>
        )}

        {/* ── Non-fatal error banner ── */}
        {error && results && (
          <div className="w-full bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {results && (
          <>
            {/* ── Savings Rate Slider ── */}
            <SavingsRateSlider
              value={savingsRate}
              onChange={setSavingsRate}
              monthlyTakeHome={roughMonthlyTakeHome}
            />

            {/* ── Three-column job tiers ── */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <TierColumn tier={results.high_tier} color="green" label="High Fit" />
              <TierColumn tier={results.mid_tier} color="amber" label="Mid Fit" />
              <TierColumn tier={results.low_tier} color="red" label="Low Fit" />
            </div>

            {/* ── Loan Payoff Projection ── */}
            <section className="space-y-4">
              <h2 className="text-lg font-bold text-gray-900">Student Loan Payoff Projection</h2>
              <LoanProjectionComparison
                high={results.high_tier.debt_projection}
                mid={results.mid_tier.debt_projection}
                low={results.low_tier.debt_projection}
              />
              <PayoffChart
                high={results.high_tier.debt_projection}
                mid={results.mid_tier.debt_projection}
                low={results.low_tier.debt_projection}
              />
            </section>

            {/* ── Saved Results History ── */}
            <section>
              <details className="bg-white rounded-xl border border-gray-200">
                <summary className="px-5 py-3 text-sm font-semibold text-gray-700 cursor-pointer select-none list-none flex items-center justify-between">
                  Saved Results History
                  <span className="text-gray-400 text-xs">▾</span>
                </summary>
                <div className="px-5 pb-4 pt-2 border-t border-gray-100">
                  <p className="text-xs text-gray-500">
                    Latest snapshot generated on{' '}
                    <span className="font-medium text-gray-700">{formatDate(results.created_at)}</span>.
                  </p>
                </div>
              </details>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
