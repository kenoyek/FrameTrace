import { useCallback, useEffect, useRef, useState } from 'react';
import { AppState } from 'react-native';
import { shareBridge } from '../../modules/frametrace-share';
import { SharedItem, validateConsumed, validatePending } from './policy';
export function useSharedInbox() {
  const [pending, setPending] = useState<SharedItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const [busy, setBusy] = useState(false);
  const mounted = useRef(false);
  const refreshing = useRef(false);
  const again = useRef(false);
  const refresh = useCallback(async () => {
    if (!shareBridge) return;
    if (refreshing.current) { again.current = true; return; }
    refreshing.current = true;
    if (mounted.current) setChecking(true);
    let latest: SharedItem | null = null;
    try {
      do {
        again.current = false;
        latest = validatePending(await shareBridge.peek());
        if (mounted.current) setPending(latest);
      } while (again.current && mounted.current);
      return latest;
    } catch { if (mounted.current) setError('Shared items could not be read. Try sharing the video again.'); }
    finally { refreshing.current = false; if (mounted.current) setChecking(false); }
  }, []);
  useEffect(() => {
    mounted.current = true;
    void refresh();
    const listener = shareBridge?.addListener('onShare', event => {
      if (typeof event?.error === 'string') setError('Finish or dismiss earlier shared videos first, then share again.');
      void refresh();
    });
    const activity = AppState.addEventListener('change', state => { if (state === 'active') void refresh(); });
    return () => { mounted.current = false; listener?.remove(); activity.remove(); };
  }, [refresh]);
  const consume = useCallback(async (id: string) => {
    if (!shareBridge) throw new Error('Sharing is not available in this build. Choose a video from your gallery.');
    setBusy(true); setError(null);
    try {
      let value: unknown;
      try { value = await shareBridge.consume(id); }
      catch { throw new Error('This shared video is no longer available. Dismiss it and share it again.'); }
      return validateConsumed(value);
    }
    finally { setBusy(false); }
  }, []);
  const discard = useCallback(async (id: string) => {
    if (!shareBridge) return;
    await shareBridge.discard(id);
    await refresh();
  }, [refresh]);
  return { available: !!shareBridge, pending, error, busy, checking, refresh, consume, discard };
}
