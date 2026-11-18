import * as SecureStore from 'expo-secure-store';
export type Appearance = 'system' | 'light' | 'dark';
const key = 'frametrace.appearance';
export function parseAppearance(value: unknown): Appearance {
  return value === 'light' || value === 'dark' ? value : 'system';
}
export function resolveAppearance(appearance: Appearance, system: string | null | undefined): 'light' | 'dark' {
  return (appearance === 'system' ? system : appearance) === 'light' ? 'light' : 'dark';
}
export async function loadAppearance(): Promise<Appearance> {
  return parseAppearance(await SecureStore.getItemAsync(key));
}
// Serialize writes so a slower earlier write cannot replace a later choice.
let writes: Promise<void> = Promise.resolve();
export function saveAppearance(appearance: Appearance): Promise<void> {
  if (!['system', 'light', 'dark'].includes(appearance)) return Promise.reject(new Error('Invalid appearance.'));
  const operation = writes.catch(() => {}).then(() => SecureStore.setItemAsync(key, appearance));
  writes = operation;
  return operation;
}
