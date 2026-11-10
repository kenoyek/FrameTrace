import { authSession } from './auth';
import * as Crypto from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';

const base = process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '');
export type Credential = { id: string; access_token?: string; user_id?: string };
export type Candidate = {
  reference_id: string; title: string; publisher: string; source_url: string | null;
  start_seconds: number; timestamp_uncertainty_seconds: number;
  evidence: { aligned_frames: number; query_frames: number; coverage: number; mean_hash_distance: number };
};
export type Job = {
  id: string; status: string; error: string | null;
  result: null | { classification: 'matching_segment' | 'possible_match' | 'no_match'; reason: string; candidates: Candidate[] };
};
export const stages: Record<string, string> = {
  queued: 'Waiting for a recognition worker', extracting_features: 'Extracting visual features',
  searching_catalog: 'Searching the reference catalog', verifying_candidates: 'Verifying temporal alignment',
  completed: 'Analysis complete', failed: 'Analysis stopped',
};
function endpoint(path: string): string {
  if (!base) throw new Error('Set EXPO_PUBLIC_API_URL to your development API address, then restart Expo.');
  if (!/^https?:\/\//.test(base)) throw new Error('API address must use HTTP or HTTPS.');
  return `${base}${path}`;
}
export type PendingSubmission = { uri: string; name: string; mime: string; token: string; principal?: string | null };
export async function restorePending(): Promise<PendingSubmission | null> {
  const saved = await SecureStore.getItemAsync('frametrace.pendingSubmission');
  if (!saved) return null;
  try {
    const value = JSON.parse(saved);
    return typeof value.uri === 'string' && typeof value.name === 'string' &&
      typeof value.mime === 'string' && typeof value.token === 'string' &&
      /^[a-f0-9]{64}$/.test(value.token) ? value : null;
  } catch { return null; }
}
export async function upload(uri: string, name: string, mime: string, progress: (value: number | null) => void): Promise<Credential> {
  // Persist the capability before sending. Response loss must not create a second job.
  const session = await authSession();
  const principal = session?.user.id ?? null;
  const pending = await restorePending();
  const token = pending?.uri === uri && pending.name === name && pending.mime === mime && (pending.principal ?? null) === principal
    ? pending.token : Array.from(Crypto.getRandomBytes(32), byte => byte.toString(16).padStart(2, '0')).join('');
  await SecureStore.setItemAsync('frametrace.pendingSubmission', JSON.stringify({ uri, name, mime, token, principal }));
  const credential = await new Promise<Credential>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', endpoint('/v1/recognitions'));
    xhr.setRequestHeader('X-Submission-Token', token);
    if (session) xhr.setRequestHeader('Authorization', `Bearer ${session.access_token}`);
    xhr.timeout = 120000;
    xhr.upload.onprogress = e => progress(e.lengthComputable ? e.loaded / e.total : null);
    xhr.onerror = () => reject(new Error('Upload could not connect. Check your connection and retry.'));
    xhr.ontimeout = () => reject(new Error('Upload timed out. Please retry.'));
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText);
        if (xhr.status !== 202) throw new Error(typeof body.detail === 'string' ? body.detail : 'Upload was rejected.');
        if (typeof body.id !== 'string' || typeof body.access_token !== 'string') throw new Error('Invalid API response.');
        resolve({ ...body, ...(principal ? { user_id: principal } : {}) });
      } catch (error) { reject(error); }
    };
    const data = new FormData();
    data.append('file', { uri, name, type: mime } as unknown as Blob);
    xhr.send(data);
  });
  await remember(credential);
  await SecureStore.deleteItemAsync('frametrace.pendingSubmission');
  return credential;
}
export async function fetchJob(credential: Credential): Promise<Job> {
  const response = await fetch(endpoint(`/v1/recognitions/${credential.id}`), {
    headers: { Authorization: await jobAuthorization(credential) },
  });
  if (!response.ok) throw new Error(response.status === 404 ? 'This recognition is no longer available.' : 'Cannot retrieve the result. Please retry.');
  return response.json();
}
export async function deleteJob(credential: Credential): Promise<void> {
  const response = await fetch(endpoint(`/v1/recognitions/${credential.id}`), {
    method: 'DELETE', headers: { Authorization: await jobAuthorization(credential) },
  });
  if (!response.ok && response.status !== 404) throw new Error('Cannot delete while processing is active. Try again after completion.');
  await SecureStore.deleteItemAsync('frametrace.activeJob');
}
export async function remember(credential: Credential) {
  await SecureStore.setItemAsync('frametrace.activeJob', JSON.stringify(credential));
}
export async function restore(): Promise<Credential | null> {
  const saved = await SecureStore.getItemAsync('frametrace.activeJob');
  if (!saved) return null;
  try {
    const value = JSON.parse(saved);
    return typeof value.id === 'string' && (typeof value.access_token === 'string' || typeof value.user_id === 'string') ? value : null;
  } catch { return null; }
}

async function jobAuthorization(credential: Credential): Promise<string> {
  if (!credential.user_id) {
    if (!credential.access_token) throw new Error('This guest discovery is no longer available.');
    return `Bearer ${credential.access_token}`;
  }
  const session = await authSession();
  if (!session || session.user.id !== credential.user_id) throw new Error('Sign in to the account that owns this recognition.');
  return `Bearer ${session.access_token}`;
}
async function accountRequest(path: string, init: RequestInit = {}) {
  const session = await authSession();
  if (!session) throw new Error('Sign in to continue.');
  const response = await fetch(endpoint(path), { ...init, headers: {
    'Content-Type': 'application/json', ...init.headers, Authorization: `Bearer ${session.access_token}`,
  } });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Account request failed.');
  }
  return response;
}
export type HistoryItem = Job & { saved: boolean; created_at: string };
export async function history(saved = false, offset = 0): Promise<{ items: HistoryItem[]; next_offset: number | null }> {
  return (await accountRequest(`/v1/history?saved_only=${saved}&offset=${offset}`)).json();
}
export async function saveResult(id: string, saved: boolean) {
  await accountRequest(`/v1/history/${id}`, { method: 'PATCH', body: JSON.stringify({ saved }) });
}
export async function deleteHistoryItem(id: string) {
  await accountRequest(`/v1/recognitions/${id}`, { method: 'DELETE' });
}
export async function clearHistory() {
  let more = true;
  while (more) {
    const body = await (await accountRequest('/v1/history', { method: 'DELETE' })).json();
    more = body.may_have_more;
  }
}
export async function claimLatest() {
  const current = await restore();
  const session = await authSession();
  if (!current || !session) throw new Error('Select a discovery and sign in first.');
  if (current.user_id) {
    if (current.user_id !== session.user.id) throw new Error('This discovery belongs to another account.');
    return;
  }
  if (!current.access_token) throw new Error('Guest discovery access is unavailable.');
  await accountRequest(`/v1/recognitions/${current.id}/claim`, { method: 'POST', headers: { 'X-Job-Token': current.access_token } });
  await remember({ ...current, user_id: session.user.id });
}

export async function reopenAccountResult(id: string) {
  const session = await authSession();
  if (!session) throw new Error('Sign in to continue.');
  await remember({ id, user_id: session.user.id });
}
