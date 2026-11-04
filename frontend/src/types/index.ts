export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Profile {
  id: string;
  user_id: string;
  major: string;
  interests: string[];
  skills: string[];
  experience_level: 'entry' | 'mid' | 'senior';
  savings: number;
  updated_at: string;
}

export interface Loan {
  id: string;
  user_id: string;
  label: string;
  loan_type: 'federal_subsidized' | 'federal_unsubsidized' | 'federal_grad_plus' | 'private';
  balance: number;
  annual_interest_rate: number;
  minimum_monthly_payment: number;
  created_at: string;
}

export interface LoanCreate {
  label: string;
  loan_type: Loan['loan_type'];
  balance: number;
  annual_interest_rate: number;
  minimum_monthly_payment: number;
}

export interface SalaryStats {
  min: number;
  max: number;
  median: number;
}

export interface JobResult {
  id: string;
  job_title: string;
  company: string;
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_median_est: number | null;
  source: 'linkedin' | 'handshake' | 'indeed' | 'usajobs';
  job_url: string;
  fit_score: number;
  tier: 'high' | 'mid' | 'low';
}

export interface DebtProjection {
  months_to_payoff: number;
  total_interest_paid: number;
  median_salary_used: number;
  savings_rate_pct: number;
}

export interface TierResult {
  jobs: JobResult[];
  salary_stats: SalaryStats;
  debt_projection: DebtProjection;
}

export interface ResultsResponse {
  high_tier: TierResult;
  mid_tier: TierResult;
  low_tier: TierResult;
  created_at: string;
}
