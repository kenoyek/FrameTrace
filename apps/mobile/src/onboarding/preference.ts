import * as SecureStore from 'expo-secure-store';

// A local UX preference, not legal consent or permission to process media.
const key = 'frametrace.introduction';
const version = '1';
export async function introductionSeen(): Promise<boolean> {
  return await SecureStore.getItemAsync(key) === version;
}
export async function rememberIntroduction(): Promise<void> {
  await SecureStore.setItemAsync(key, version);
}
