import client from './client';
import type { Profile } from '../types';

export async function getProfile(): Promise<Profile> {
  const res = await client.get<Profile>('/profile');
  return res.data;
}

export async function updateProfile(data: Partial<Profile>): Promise<Profile> {
  const res = await client.put<Profile>('/profile', data);
  return res.data;
}
