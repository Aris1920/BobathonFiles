import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, updateProfile } from '../api/profile';
import { getLoans, createLoan, updateLoan, deleteLoan } from '../api/loans';
import { generateResults } from '../api/results';
import type { Profile, Loan, LoanCreate } from '../types';
import Navbar from '../components/Navbar';
import TagInput from '../components/TagInput';
import LoanList from '../components/LoanList';
import ResumeUpload from '../components/ResumeUpload';

export default function ProfilePage() {
  const navigate = useNavigate();

  // Profile state
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [resumeText, setResumeText] = useState('');
  const [loadError, setLoadError] = useState<string | null>(null);

  // Generate state
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Debounce timer for auto-save
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load profile and loans on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [p, l] = await Promise.all([getProfile(), getLoans()]);
        if (!cancelled) {
          setProfile(p);
          setLoans(l);
        }
      } catch {
        if (!cancelled) setLoadError('Failed to load your profile. Please refresh.');
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Auto-save profile with 800ms debounce after each change
  const scheduleAutoSave = useCallback((patch: Partial<Profile>) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try {
        const updated = await updateProfile(patch);
        setProfile(updated);
      } catch {
        // Silent auto-save failure; user will retry via Find My Jobs
      }
    }, 800);
  }, []);

  function updateField<K extends keyof Profile>(key: K, value: Profile[K]) {
    if (!profile) return;
    const patch = { ...profile, [key]: value };
    setProfile(patch);
    scheduleAutoSave({ [key]: value } as Partial<Profile>);
  }

  // Loan CRUD
  async function handleAddLoan(data: LoanCreate) {
    const loan = await createLoan(data);
    setLoans((prev) => [...prev, loan]);
  }

  async function handleUpdateLoan(id: string, data: Partial<LoanCreate>) {
    const loan = await updateLoan(id, data);
    setLoans((prev) => prev.map((l) => (l.id === id ? loan : l)));
  }

  async function handleDeleteLoan(id: string) {
    await deleteLoan(id);
    setLoans((prev) => prev.filter((l) => l.id !== id));
  }

  // Generate results
  async function handleGenerate() {
    setGenerating(true);
    setGenError(null);
    try {
      // Flush any pending debounced save first
      if (saveTimer.current) {
        clearTimeout(saveTimer.current);
        saveTimer.current = null;
        if (profile) await updateProfile(profile);
      }
      await generateResults(20, resumeText || undefined);
      navigate('/results');
    } catch {
      setGenError('Failed to generate results. Please try again.');
    } finally {
      setGenerating(false);
    }
  }

  if (loadError) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-2xl mx-auto px-6 py-20 text-center">
          <p className="text-red-600">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-2xl mx-auto px-6 py-20 text-center text-gray-400 text-sm">
          Loading…
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-6 py-10 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Your Profile</h1>
          <p className="text-sm text-gray-500 mt-1">
            Fill in your details and loans, then click "Find My Jobs" to see results.
          </p>
        </div>

        {/* Section 1 — About You */}
        <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
          <h2 className="text-base font-semibold text-gray-800">About You</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Major</label>
            <input
              type="text"
              value={profile.major}
              onChange={(e) => updateField('major', e.target.value)}
              placeholder="e.g. Computer Science"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Interests</label>
            <TagInput
              tags={profile.interests}
              onChange={(tags) => updateField('interests', tags)}
              placeholder="Add interest and press Enter…"
            />
            <p className="text-xs text-gray-400 mt-1">Press Enter or comma to add each interest.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Skills</label>
            <TagInput
              tags={profile.skills}
              onChange={(tags) => updateField('skills', tags)}
              placeholder="Add skill and press Enter…"
            />
            <p className="text-xs text-gray-400 mt-1">Press Enter or comma to add each skill.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Experience Level</label>
            <select
              value={profile.experience_level}
              onChange={(e) => updateField('experience_level', e.target.value as Profile['experience_level'])}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="entry">Entry Level</option>
              <option value="mid">Mid Level</option>
              <option value="senior">Senior Level</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Savings</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
              <input
                type="number"
                min="0"
                step="100"
                value={profile.savings}
                onChange={(e) => updateField('savings', parseFloat(e.target.value) || 0)}
                className="w-full border border-gray-300 rounded-md pl-7 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </section>

        {/* Section 2 — Resume */}
        <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-3">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Your Resume</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Optional — uploading your resume improves job match quality.
            </p>
          </div>
          <ResumeUpload onExtracted={setResumeText} />
        </section>

        {/* Section 3 — Student Loans */}
        <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Your Student Loans</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Add each loan to calculate your payoff timeline across salary tiers.
            </p>
          </div>
          <LoanList
            loans={loans}
            onAdd={handleAddLoan}
            onUpdate={handleUpdateLoan}
            onDelete={handleDeleteLoan}
          />
        </section>

        {/* Generate button */}
        {genError && (
          <p className="text-sm text-red-600 text-center">{genError}</p>
        )}
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
        >
          {generating ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Finding jobs…
            </span>
          ) : (
            'Find My Jobs →'
          )}
        </button>
      </main>
    </div>
  );
}
