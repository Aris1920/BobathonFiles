import client from './client';
import type { Loan, LoanCreate } from '../types';

export async function getLoans(): Promise<Loan[]> {
  const res = await client.get<Loan[]>('/loans');
  return res.data;
}

export async function createLoan(data: LoanCreate): Promise<Loan> {
  const res = await client.post<Loan>('/loans', data);
  return res.data;
}

export async function updateLoan(id: string, data: Partial<LoanCreate>): Promise<Loan> {
  const res = await client.put<Loan>(`/loans/${id}`, data);
  return res.data;
}

export async function deleteLoan(id: string): Promise<void> {
  await client.delete(`/loans/${id}`);
}
