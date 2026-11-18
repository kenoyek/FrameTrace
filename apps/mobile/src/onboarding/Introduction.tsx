import { useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, useColorScheme, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { palette, tokens } from '../theme';

export function Introduction({ onContinue, onContinueWithoutSaving, storageError = false, review = false }: {
  onContinue: () => Promise<void>;
  onContinueWithoutSaving?: () => void;
  storageError?: boolean;
  review?: boolean;
}) {
  const color = palette[useColorScheme() === 'light' ? 'light' : 'dark'];
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  async function proceed() {
    if (lock.current) return;
    lock.current = true; setBusy(true); setFailed(false);
    try { await onContinue(); }
    catch { setFailed(true); }
    finally { lock.current = false; setBusy(false); }
  }
  return <SafeAreaView style={{ flex: 1, backgroundColor: color.background }}>
    <ScrollView contentContainerStyle={styles.page}>
      <Text style={{ color: color.accent, fontWeight: '700' }}>FRAMETRACE</Text>
      <Text accessibilityRole="header" style={[styles.title, { color: color.text }]}>{review ? 'How FrameTrace works' : 'Find the story behind a clip.'}</Text>
      {[
        ['Start with a clip you may use', 'Choose a local video, record with permission, or share a video from another app. Use a 1–30 second MP4 or MOV, up to 50 MB. Trimming is not available yet.'],
        ['Review, then identify', 'Selecting, recording or sharing a clip does not upload it. Review the preview, then tap Identify to send it to the configured recognition service. Camera and microphone access are requested only when you choose Record.'],
        ['A match needs evidence', 'FrameTrace searches a limited, authorized reference catalog. It may find a matching segment, suggest a possible match or return no match. It does not search every video online or verify the original creator. Shared links cannot be downloaded.'],
        ['Understand what stays', 'The service normally removes query clips after completion or permanent failure. Temporary failures can retain clips for retry; abandoned jobs follow the configured retention policy, normally 24 hours. Device share caches are pruned on later app activity and may remain while the app is closed.'],
        ['You control your discoveries', 'You can use guest searches without an account. Guest access is saved on this device. Accounts, when configured, offer private history and saved results. Delete a finished recognition from its result, or manage account history from Account & history.'],
      ].map(([title, body]) => <View key={title} style={[styles.card, { borderColor: color.border }]}>
        <Text accessibilityRole="header" style={[styles.heading, { color: color.text }]}>{title}</Text>
        <Text style={[styles.body, { color: color.muted }]}>{body}</Text>
      </View>)}
      <Text style={[styles.body, { color: color.muted }]}>Development build. Recognition quality, device testing and security review remain incomplete. This guide is an explanation of current behavior, not a legal privacy policy.</Text>
      {(failed || storageError) && <Text accessibilityRole="alert" style={[styles.body, { color: color.text }]}>Your introduction preference could not be saved or read. Retry, or continue for this session; you may see this guide again next time.</Text>}
      <Pressable accessibilityRole="button" accessibilityState={{ disabled: busy }} disabled={busy} onPress={() => { void proceed(); }} style={[styles.button, { backgroundColor: color.button, opacity: busy ? .5 : 1 }]}>
        <Text style={styles.buttonText}>{busy ? 'Please wait…' : review ? 'Back to FrameTrace' : 'Start exploring'}</Text>
      </Pressable>
      {(failed || storageError) && onContinueWithoutSaving && <Pressable accessibilityRole="button" disabled={busy} onPress={onContinueWithoutSaving} style={styles.button}>
        <Text style={{ color: color.accent }}>Continue without saving</Text>
      </Pressable>}
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  page: { padding: 24, gap: 20, paddingBottom: 48, width: '100%', maxWidth: tokens.maxWidth, alignSelf: 'center' },
  title: { fontSize: 34, lineHeight: 42, fontWeight: '800' },
  card: { padding: 20, gap: 10, borderWidth: 1, borderRadius: tokens.radius },
  heading: { fontSize: 19, lineHeight: 27, fontWeight: '700' },
  body: { fontSize: 15, lineHeight: 24 },
  button: { minHeight: 54, padding: 16, alignItems: 'center', justifyContent: 'center', borderRadius: 14 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});
