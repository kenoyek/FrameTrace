import * as SecureStore from 'expo-secure-store';

const base = process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '');
export type Credential = { id: string; access_token: string };
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
export function upload(uri: string, name: string, mime: string, progress: (value: number | null) => void): Promise<Credential> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', endpoint('/v1/recognitions'));
    xhr.timeout = 120000;
    xhr.upload.onprogress = e => progress(e.lengthComputable ? e.loaded / e.total : null);
    xhr.onerror = () => reject(new Error('Upload could not connect. Check your connection and retry.'));
    xhr.ontimeout = () => reject(new Error('Upload timed out. Please retry.'));
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText);
        if (xhr.status !== 202) throw new Error(typeof body.detail === 'string' ? body.detail : 'Upload was rejected.');
        if (typeof body.id !== 'string' || typeof body.access_token !== 'string') throw new Error('Invalid API response.');
        resolve(body);
      } catch (error) { reject(error); }
    };
    const data = new FormData();
    data.append('file', { uri, name, type: mime } as unknown as Blob);
    xhr.send(data);
  });
}
export async function fetchJob(credential: Credential): Promise<Job> {
  const response = await fetch(endpoint(`/v1/recognitions/${credential.id}`), {
    headers: { Authorization: `Bearer ${credential.access_token}` },
  });
  if (!response.ok) throw new Error(response.status === 404 ? 'This recognition is no longer available.' : 'Cannot retrieve the result. Please retry.');
  return response.json();
}
export async function deleteJob(credential: Credential): Promise<void> {
  const response = await fetch(endpoint(`/v1/recognitions/${credential.id}`), {
    method: 'DELETE', headers: { Authorization: `Bearer ${credential.access_token}` },
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
    return typeof value.id === 'string' && typeof value.access_token === 'string' ? value : null;
  } catch { return null; }
}
