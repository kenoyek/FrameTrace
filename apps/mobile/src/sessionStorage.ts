import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';
let chain: Promise<unknown> = Promise.resolve();
function serial<T>(action: () => Promise<T>): Promise<T> {
  const operation = chain.then(action, action);
  chain = operation.catch(() => {});
  return operation;
}
type Index = { id: string; count: number };
async function index(key: string): Promise<Index | null> {
  const value = await SecureStore.getItemAsync(key + '.index');
  if (!value) return null;
  const parsed = JSON.parse(value);
  if (!/^[a-f0-9]{24}$/.test(parsed.id) || !Number.isInteger(parsed.count) || parsed.count < 1 || parsed.count > 128) throw new Error('Invalid secure session index.');
  return parsed;
}
async function erase(key: string, value: Index | null) {
  if (value) await Promise.allSettled(Array.from({ length: value.count }, (_, i) => SecureStore.deleteItemAsync(`${key}.${value.id}.${i}`)));
}
// Separate generations keep old sessions intact if writing a new chunk fails.
export const secureSessionStorage = {
  getItem: (key: string) => serial(async () => {
    const value = await index(key);
    if (!value) return null;
    const chunks = await Promise.all(Array.from({ length: value.count }, (_, i) => SecureStore.getItemAsync(`${key}.${value.id}.${i}`)));
    if (chunks.some(chunk => chunk === null)) throw new Error('Secure session is incomplete. Sign in again.');
    return chunks.join('');
  }),
  setItem: (key: string, value: string) => serial(async () => {
    const previous = await index(key);
    const characters = Array.from(value);
    const next: Index = { id: Array.from(Crypto.getRandomBytes(12), b => b.toString(16).padStart(2, '0')).join(''), count: Math.max(1, Math.ceil(characters.length / 500)) };
    if (next.count > 128) throw new Error('Session exceeds secure storage capacity.');
    try {
      for (let i = 0; i < next.count; i++) await SecureStore.setItemAsync(`${key}.${next.id}.${i}`, characters.slice(i * 500, (i + 1) * 500).join(''));
      await SecureStore.setItemAsync(key + '.index', JSON.stringify(next));
    } catch (error) { await erase(key, next); throw error; }
    await erase(key, previous);
  }),
  removeItem: (key: string) => serial(async () => {
    const previous = await index(key);
    await SecureStore.deleteItemAsync(key + '.index');
    await erase(key, previous);
  }),
};
