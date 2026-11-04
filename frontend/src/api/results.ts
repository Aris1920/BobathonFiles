import client from './client';
import type { ResultsResponse } from '../types';

export async function generateResults(
  savings_rate_pct: number,
  resume_text?: string
): Promise<ResultsResponse> {
  const res = await client.post<ResultsResponse>('/results/generate', {
    savings_rate_pct,
    resume_text,
  });
  return res.data;
}

export async function getLatestResults(): Promise<ResultsResponse> {
  const res = await client.get<ResultsResponse>('/results/latest');
  return res.data;
}
