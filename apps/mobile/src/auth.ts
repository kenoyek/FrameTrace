import 'react-native-url-polyfill/auto';
import { createClient, processLock } from '@supabase/supabase-js';
import { AppState } from 'react-native';
import { secureSessionStorage } from './sessionStorage';
const url = process.env.EXPO_PUBLIC_SUPABASE_URL;
const key = process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
if (key && !key.startsWith('sb_publishable_')) throw new Error('Use a Supabase publishable key in the mobile app.');
export const supabase = url && key ? createClient(url, key, { auth: {
  storage: secureSessionStorage, lock: processLock, persistSession: true, autoRefreshToken: true, detectSessionInUrl: false,
} }) : null;
export async function authSession() {
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) throw new Error('Your session could not be restored. Please sign in again.');
  return data.session;
}
export function manageSessionRefresh() {
  const refresh = (state: string) => {
    if (state === 'active') supabase?.auth.startAutoRefresh();
    else supabase?.auth.stopAutoRefresh();
  };
  refresh(AppState.currentState ?? 'unknown');
  const subscription = AppState.addEventListener('change', refresh);
  return () => { subscription.remove(); supabase?.auth.stopAutoRefresh(); };
}
