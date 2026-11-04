import client from './client';
import type { TokenResponse } from '../types';

export async function register(email: string, password: string): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>('/auth/register', { email, password });
  return res.data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>('/auth/login', { email, password });
  return res.data;
}

export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>('/auth/refresh', { refresh_token });
  return res.data;
}
