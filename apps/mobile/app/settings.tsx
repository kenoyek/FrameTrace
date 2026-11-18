import { useEffect, useRef, useState } from 'react';
import { checkConnection, type ConnectionCheck } from '../src/connection';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAppearance } from '../src/settings/AppearanceProvider';
import { tokens } from '../src/theme';

export default function Settings() {
  const { appearance, color, ready, saving, error, setAppearance } = useAppearance();
  const [checking, setChecking] = useState(false);
  const [connection, setConnection] = useState<ConnectionCheck | null>(null);
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => { request.current?.abort(); request.current = null; }, []);
  async function testConnection() {
    if (request.current) return;
    const controller = new AbortController(); request.current = controller;
    setChecking(true); setConnection(null);
    try {
      const result = await checkConnection(controller.signal);
      if (!controller.signal.aborted) setConnection(result);
    } finally {
      if (request.current === controller) { request.current = null; setChecking(false); }
    }
  }
  function Link({ title, action }: { title: string; action: () => void }) {
    return <Pressable accessibilityRole="button" onPress={action} style={[styles.link, { borderColor: color.border }]}><Text style={{ color: color.accent, fontSize: 16 }}>{title}</Text></Pressable>;
  }
  return <SafeAreaView style={{ flex: 1, backgroundColor: color.background }}><ScrollView contentContainerStyle={styles.page}>
    <Link title="← Back to FrameTrace" action={() => { if (router.canGoBack()) router.back(); else router.replace('/'); }} />
    <Text accessibilityRole="header" style={[styles.title, { color: color.text }]}>Settings</Text>
    <View style={[styles.card, { borderColor: color.border }]}>
      <Text accessibilityRole="header" style={[styles.heading, { color: color.text }]}>Appearance</Text>
      <Text style={[styles.body, { color: color.muted }]}>Use your device’s setting, or choose a look for every FrameTrace screen. Your choice stays on this device.</Text>
      {(['system', 'light', 'dark'] as const).map(mode => <Pressable key={mode} accessibilityRole="radio" accessibilityState={{ checked: appearance === mode, disabled: !ready }} disabled={!ready}
        onPress={() => { void setAppearance(mode); }} style={[styles.link, { borderColor: appearance === mode ? color.accent : color.border }]}>
        <Text style={{ color: color.text, fontSize: 16 }}>{mode[0].toUpperCase() + mode.slice(1)}{appearance === mode ? ' · Selected' : ''}</Text>
      </Pressable>)}
      {(!ready || saving) && <Text accessibilityLiveRegion="polite" style={{ color: color.muted }}>{ready ? 'Saving preference…' : 'Loading preference…'}</Text>}
      {error && <Text accessibilityRole="alert" style={[styles.body, { color: color.text }]}>{error}</Text>}
    </View>
    <View style={[styles.card, { borderColor: color.border }]}>
      <Text accessibilityRole="header" style={[styles.heading, { color: color.text }]}>Test API connection</Text>
      <Text style={[styles.body, { color: color.muted }]}>Check whether this build can reach its recognition API. This sends no clip or account token. The result is a snapshot; upload and worker testing are separate.</Text>
      <Pressable accessibilityRole="button" accessibilityState={{ disabled: checking }} disabled={checking} onPress={() => { void testConnection(); }} style={[styles.link, { borderColor: color.border }]}>
        <Text style={{ color: color.accent }}>{checking ? 'Checking…' : 'Check connection'}</Text>
      </Pressable>
      {connection && <Text accessibilityLiveRegion="polite" style={[styles.body, { color: color.text }]}>{connection.message}</Text>}
    </View>
    <Text accessibilityRole="header" style={[styles.heading, { color: color.text }]}>Your clips and discoveries</Text>
    <Link title="How FrameTrace works & clip privacy" action={() => router.push('/guide')} />
    <Link title="Account & history" action={() => router.push('/account')} />
    <Text style={[styles.body, { color: color.muted }]}>Development build · Visual matching against an authorized reference catalog. A match identifies an indexed recording; it does not verify its original creator.</Text>
  </ScrollView></SafeAreaView>;
}
const styles = StyleSheet.create({
  page: { padding: 24, gap: 20, paddingBottom: 48, width: '100%', maxWidth: tokens.maxWidth, alignSelf: 'center' },
  title: { fontSize: 34, lineHeight: 42, fontWeight: '800' },
  heading: { fontSize: 19, lineHeight: 27, fontWeight: '700' },
  body: { fontSize: 15, lineHeight: 24 },
  card: { borderWidth: 1, borderRadius: tokens.radius, padding: 20, gap: 16 },
  link: { minHeight: 48, padding: 14, borderWidth: 1, borderRadius: 12, justifyContent: 'center' },
});
