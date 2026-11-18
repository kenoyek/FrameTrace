import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useColorScheme } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { palette } from '../theme';
import { loadAppearance, resolveAppearance, saveAppearance, type Appearance } from './appearance';

type AppearanceContext = {
  appearance: Appearance; color: typeof palette.dark; ready: boolean; saving: boolean;
  error: string | null; setAppearance: (value: Appearance) => Promise<void>;
};
const Context = createContext<AppearanceContext | null>(null);
export function AppearanceProvider({ children }: { children: ReactNode }) {
  const system = useColorScheme();
  const [appearance, setValue] = useState<Appearance>('system');
  const [ready, setReady] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const writeCount = useRef(0);
  const revision = useRef(0);
  useEffect(() => {
    let active = true;
    loadAppearance().then(value => { if (active) setValue(value); })
      .catch(() => { if (active) setError('Could not read your appearance preference. Using the device setting until you choose a mode.'); })
      .finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);
  async function setAppearance(value: Appearance) {
    if (!ready) return;
    const current = ++revision.current;
    setValue(value); setError(null); setSaving(true); writeCount.current++;
    try { await saveAppearance(value); }
    catch { if (revision.current === current) setError('This appearance is active for this session, but could not be saved. Tap the mode again to retry.'); }
    finally { if (--writeCount.current === 0) setSaving(false); }
  }
  const resolved = resolveAppearance(appearance, system);
  return <Context.Provider value={{ appearance, color: palette[resolved], ready, saving, error, setAppearance }}>
    <StatusBar style={resolved === 'dark' ? 'light' : 'dark'} />{children}
  </Context.Provider>;
}
export function useAppearance() {
  const value = useContext(Context);
  if (!value) throw new Error('AppearanceProvider is required.');
  return value;
}
