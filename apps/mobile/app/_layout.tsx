import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Introduction } from '../src/onboarding/Introduction';
import { introductionSeen, rememberIntroduction } from '../src/onboarding/preference';
import { manageSessionRefresh, supabase } from '../src/auth';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
const client = new QueryClient({ defaultOptions: { queries: { retry: 1 } } });
export default function Layout() {
  const [introduced, setIntroduced] = useState<boolean | null>(null);
  const [preferenceError, setPreferenceError] = useState(false);
  useEffect(() => {
    let active = true;
    introductionSeen().then(seen => { if (active) setIntroduced(seen); }).catch(() => {
      if (active) { setPreferenceError(true); setIntroduced(false); }
    });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!introduced) return;
    const stop = manageSessionRefresh();
    let prior: string | null | undefined;
    const listener = supabase?.auth.onAuthStateChange((_event, session) => {
      const user = session?.user.id ?? null;
      if (user !== prior) client.clear();
      prior = user;
    });
    return () => { stop(); listener?.data.subscription.unsubscribe(); };
  }, [introduced]);
  return <GestureHandlerRootView style={{ flex: 1 }}><SafeAreaProvider>
    <QueryClientProvider client={client}>{introduced === null
      ? <View style={{ flex: 1, justifyContent: 'center' }}><ActivityIndicator accessibilityLabel="Loading introduction preference" /></View>
      : !introduced ? <Introduction storageError={preferenceError} onContinue={async () => {
        await rememberIntroduction(); setIntroduced(true);
      }} onContinueWithoutSaving={() => setIntroduced(true)} />
      : <Stack screenOptions={{ headerShown: false }} />}</QueryClientProvider>
  </SafeAreaProvider></GestureHandlerRootView>;
}
