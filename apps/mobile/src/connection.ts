export type ConnectionCheck = {
  state: 'responding' | 'not_configured' | 'invalid_configuration' | 'unreachable' | 'incompatible' | 'cancelled';
  message: string;
};

export async function checkConnection(signal?: AbortSignal, timeoutMs = 8000): Promise<ConnectionCheck> {
  const base = process.env.EXPO_PUBLIC_API_URL;
  if (!base) return { state: 'not_configured', message: 'This build has no recognition API address. Build again with EXPO_PUBLIC_API_URL set to a reachable test API. Local clip review is still available.' };
  let url: URL;
  try {
    url = new URL(base);
    if (!['http:', 'https:'].includes(url.protocol) || !url.hostname || url.username || url.password || url.search || url.hash) throw new Error();
  } catch { return { state: 'invalid_configuration', message: 'This build has an invalid API address. Use an HTTP or HTTPS base URL without credentials, query or fragment, then rebuild.' }; }
  if (signal?.aborted) return { state: 'cancelled', message: 'Connection check cancelled.' };
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal?.addEventListener('abort', cancel, { once: true });
  const timer = setTimeout(cancel, timeoutMs);
  try {
    // Public health probe only: never attach guest capabilities or account tokens.
    const response = await fetch(`${url.toString().replace(/\/$/, '')}/health`, {
      method: 'GET', signal: controller.signal, headers: { Accept: 'application/json' },
      credentials: 'omit', redirect: 'error', cache: 'no-store',
    });
    if (!response.ok) return { state: 'unreachable', message: 'The API did not report healthy status. Check the test server and try again.' };
    const health = await response.json();
    if (health?.status !== 'ok' || !['local', 'celery'].includes(health?.execution)) {
      return { state: 'incompatible', message: 'The address responded, but not with the expected FrameTrace health response. Check the API base URL.' };
    }
    return { state: 'responding', message: 'The API and its database responded. This does not test the recognition worker, catalog coverage, account service or video upload.' };
  } catch {
    return signal?.aborted ? { state: 'cancelled', message: 'Connection check cancelled.' }
      : { state: 'unreachable', message: 'Could not reach the API before the check finished. Check your connection, server address and HTTPS certificate. A phone cannot reach a server through the build machine’s localhost.' };
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }
}
