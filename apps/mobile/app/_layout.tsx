import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
const client = new QueryClient({ defaultOptions: { queries: { retry: 1 } } });
export default function Layout() {
  return <GestureHandlerRootView style={{ flex: 1 }}><SafeAreaProvider>
    <QueryClientProvider client={client}><Stack screenOptions={{ headerShown: false }} /></QueryClientProvider>
  </SafeAreaProvider></GestureHandlerRootView>;
}
