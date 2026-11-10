import { useEffect } from 'react';
import { manageSessionRefresh, supabase } from '../src/auth';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
const client = new QueryClient({ defaultOptions: { queries: { retry: 1 } } });
export default function Layout() {
  useEffect(() => {
    const stop = manageSessionRefresh();
    let prior: string | null | undefined;
    const listener = supabase?.auth.onAuthStateChange((_event, session) => {
      const user = session?.user.id ?? null;
      if (user !== prior) client.clear();
      prior = user;
    });
    return () => { stop(); listener?.data.subscription.unsubscribe(); };
  }, []);
  return <GestureHandlerRootView style={{ flex: 1 }}><SafeAreaProvider>
    <QueryClientProvider client={client}><Stack screenOptions={{ headerShown: false }} /></QueryClientProvider>
  </SafeAreaProvider></GestureHandlerRootView>;
}
