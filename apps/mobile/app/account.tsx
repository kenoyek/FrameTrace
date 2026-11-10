import { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, useColorScheme, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import type { Session } from '@supabase/supabase-js';
import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { authSession, supabase } from '../src/auth';
import { claimLatest, clearHistory, deleteHistoryItem, history, saveResult, reopenAccountResult } from '../src/api';
import { palette } from '../src/theme';
export default function Account() {
  const c = palette[useColorScheme() === 'light' ? 'light' : 'dark'];
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const cache = useQueryClient();
  useEffect(() => {
    authSession().then(setSession).catch(() => setMessage('Please sign in again.'));
    const listener = supabase?.auth.onAuthStateChange((_event, value) => setSession(value));
    return () => listener?.data.subscription.unsubscribe();
  }, []);
  const searches = useInfiniteQuery({ queryKey: ['history', session?.user.id, saved], initialPageParam: 0,
    queryFn: ({ pageParam }) => history(saved, pageParam), getNextPageParam: page => page.next_offset ?? undefined, enabled: !!session,
    refetchInterval: query => query.state.data?.pages.some(page => page.items.some(item => !['completed', 'failed'].includes(item.status))) ? 2000 : false,
  });
  async function perform(action: () => Promise<unknown>) {
    setBusy(true); setMessage(null);
    try { await action(); await cache.invalidateQueries({ queryKey: ['history'] }); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Request failed. Please retry.'); }
    finally { setBusy(false); }
  }
  async function authenticate(signup: boolean) {
    if (!supabase) return;
    if (!email.trim() || password.length < 8) throw new Error('Enter your email and a password of at least 8 characters.');
    const result = signup ? await supabase.auth.signUp({ email: email.trim(), password }) : await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (result.error) throw result.error;
    setPassword('');
    if (signup && !result.data.session) setMessage('Check your email to confirm your account, then sign in.');
  }
  function Button({ label, action }: { label: string; action: () => void }) {
    return <Pressable accessibilityRole="button" disabled={busy} onPress={action} style={[styles.button, { borderColor: c.border, opacity: busy ? .5 : 1 }]}><Text style={{ color: c.accent, fontWeight: '700' }}>{label}</Text></Pressable>;
  }
  return <SafeAreaView style={{ flex: 1, backgroundColor: c.background }}><KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}><ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.page}>
    <Button label="← Back to FrameTrace" action={() => router.back()} />
    <Text accessibilityRole="header" style={[styles.title, { color: c.text }]}>Your discoveries</Text>
    <Text style={[styles.body, { color: c.muted }]}>Keep your searches private, save useful matches, and return to their stories.</Text>
    {!supabase ? <Text style={[styles.body, { color: c.muted }]}>Accounts are not available in this development build yet. You can continue identifying clips as a guest.</Text> : !session ? <View style={[styles.card, { borderColor: c.border }]}>
      <Text style={[styles.heading, { color: c.text }]}>Sign in or create an account</Text>
      <TextInput accessibilityLabel="Email" placeholder="Email" placeholderTextColor={c.muted} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" value={email} onChangeText={setEmail} style={[styles.input, { color: c.text, borderColor: c.border }]} />
      <TextInput accessibilityLabel="Password" placeholder="Password" placeholderTextColor={c.muted} secureTextEntry autoComplete="password" value={password} onChangeText={setPassword} style={[styles.input, { color: c.text, borderColor: c.border }]} />
      <Button label={busy ? 'Please wait…' : 'Sign in'} action={() => { void perform(() => authenticate(false)); }} />
      <Button label="Create account" action={() => { void perform(() => authenticate(true)); }} />
    </View> : <>
      <Text style={{ color: c.muted }}>{session.user.email}</Text>
      <Button label="Add latest guest discovery to my history" action={() => { void perform(claimLatest); }} />
      <Button label={saved ? 'Show all searches' : 'Show saved results'} action={() => setSaved(!saved)} />
      {searches.isPending && <Text style={{ color: c.muted }}>Loading your history…</Text>}
      {searches.error && <><Text accessibilityRole="alert" style={{ color: c.text }}>{searches.error.message}</Text><Button label="Retry history" action={() => { void searches.refetch(); }} /></>}
      {searches.data?.pages[0].items.length === 0 && <Text style={{ color: c.muted }}>No discoveries here yet. Identify a clip to start your history.</Text>}
      {searches.data?.pages.flatMap(page => page.items).map(item => <View key={item.id} style={[styles.card, { borderColor: c.border }]}>
        <Text style={[styles.heading, { color: c.text }]}>{(item.result?.classification === 'possible_match' ? 'Possible match · ' : '') + (item.result?.candidates[0]?.title ?? (item.status === 'failed' ? 'Search could not finish' : item.result?.classification === 'no_match' ? 'No reliable match' : 'Search in progress'))}</Text>
        <Text style={{ color: c.muted }}>{new Date(item.created_at).toLocaleDateString()} · {item.status}</Text>
        <Text style={[styles.body, { color: c.muted }]}>{item.result?.reason ?? item.error ?? 'Return after processing completes.'}</Text>
        {item.result?.candidates[0] && <Text style={{ color: c.accent }}>{item.result.classification === 'possible_match' ? 'Candidate at' : 'Matched at'} {item.result.candidates[0].start_seconds.toFixed(1)} seconds</Text>}
        <Button label="Open discovery" action={() => { void perform(async () => { await reopenAccountResult(item.id); router.back(); }); }} />
        <Button label={item.saved ? 'Remove from saved' : 'Save result'} action={() => { void perform(() => saveResult(item.id, !item.saved)); }} />
        <Button label="Delete search" action={() => Alert.alert('Delete search?', 'This removes this private history record.', [{ text: 'Cancel', style: 'cancel' }, { text: 'Delete', style: 'destructive', onPress: () => { void perform(() => deleteHistoryItem(item.id)); } }])} />
      </View>)}
      {searches.hasNextPage && <Button label={searches.isFetchingNextPage ? 'Loading…' : 'Load more discoveries'} action={() => { void searches.fetchNextPage(); }} />}
      <Button label="Clear my search history" action={() => Alert.alert('Clear history?', 'Saved and recent searches will be removed. Active searches must finish first.', [{ text: 'Cancel', style: 'cancel' }, { text: 'Clear', style: 'destructive', onPress: () => { void perform(clearHistory); } }])} />
      <Button label="Sign out" action={() => { void perform(async () => { const result = await supabase!.auth.signOut(); if (result.error) throw result.error; }); }} />
    </>}
    {message && <Text accessibilityRole="alert" style={[styles.body, { color: c.text }]}>{message}</Text>}
  </ScrollView></KeyboardAvoidingView></SafeAreaView>;
}
const styles = StyleSheet.create({ page: { padding: 24, gap: 18, paddingBottom: 48, maxWidth: 640, width: '100%', alignSelf: 'center' }, title: { fontSize: 34, fontWeight: '800' }, heading: { fontSize: 18, fontWeight: '700' }, body: { fontSize: 15, lineHeight: 24 }, card: { borderWidth: 1, borderRadius: 18, padding: 20, gap: 14 }, input: { borderWidth: 1, borderRadius: 12, padding: 14, minHeight: 50 }, button: { borderWidth: 1, borderRadius: 12, minHeight: 48, padding: 14, justifyContent: 'center' } });
