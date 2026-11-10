import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, Linking, Pressable, ScrollView, StyleSheet, Text, useColorScheme, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import * as ImagePicker from 'expo-image-picker';
import * as Haptics from 'expo-haptics';
import { useVideoPlayer, VideoView } from 'expo-video';
import { useQuery } from '@tanstack/react-query';
import { Credential, deleteJob, fetchJob, restore, restorePending, stages, upload } from '../src/api';
import { palette, tokens } from '../src/theme';

function Preview({ uri }: { uri: string }) {
  const player = useVideoPlayer(uri, player => { player.loop = false; });
  return <VideoView player={player} style={styles.video} nativeControls contentFit="contain" accessibilityLabel="Selected clip preview" />;
}
const timestamp = (value: number) => `${Math.floor(value / 60)}:${Math.floor(value % 60).toString().padStart(2, '0')}`;
export default function Home() {
  const system = useColorScheme();
  const [appearance, setAppearance] = useState<'system' | 'dark' | 'light'>('system');
  const color = palette[(appearance === 'system' ? system : appearance) === 'light' ? 'light' : 'dark'];
  const [selected, setSelected] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [credential, setCredential] = useState<Credential | null>(null);
  const [restoring, setRestoring] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  useFocusEffect(useCallback(() => {
    let active = true;
    Promise.all([restore(), restorePending()]).then(([access, pending]) => {
      if (!active) return;
      setCredential(access);
      if (pending) {
        setSelected({ uri: pending.uri, width: 0, height: 0, type: 'video', fileName: pending.name, mimeType: pending.mime });
        setError('An upload was interrupted. Tap Identify to retry with the same submission. If the cached video is unavailable, choose it again.');
      }
    }).catch(() => { if (active) setError('Could not restore the last recognition.'); }).finally(() => { if (active) setRestoring(false); });
    return () => { active = false; };
  }, []));
  const job = useQuery({
    queryKey: ['recognition', credential?.id], queryFn: () => fetchJob(credential!),
    enabled: !!credential,
    refetchInterval: query => ['completed', 'failed'].includes(query.state.data?.status ?? '') ? false : 1500,
  });
  const result = job.data?.result;
  const working = !!credential && !['completed', 'failed'].includes(job.data?.status ?? '');
  const textStyle = { color: color.text };
  function Button({ title, onPress, secondary = false, disabled = false }: { title: string; onPress: () => void; secondary?: boolean; disabled?: boolean }) {
    return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} onPress={onPress} disabled={disabled}
      style={({ pressed }) => [styles.button, { backgroundColor: secondary ? color.surface : color.button, borderColor: color.border, opacity: disabled ? .45 : pressed ? .8 : 1 }]}>
      <Text style={[styles.buttonText, { color: secondary ? color.text : '#FFFFFF' }]}>{title}</Text>
    </Pressable>;
  }
  async function choose() {
    setError(null);
    try {
      const selection = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['videos'], allowsEditing: false, quality: 1 });
      if (selection.canceled) return;
      const video = selection.assets[0];
      if (video.duration && (video.duration > 30000 || video.duration < 1000)) throw new Error('Choose a clip between 1 and 30 seconds. Trimming is not available in this build yet.');
      if (video.fileSize && video.fileSize > 50 * 1024 * 1024) throw new Error('Choose a video smaller than 50 MB.');
      setSelected(video);
      void Haptics.selectionAsync().catch(() => {});
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not open the video picker.'); }
  }
  async function identify() {
    if (!selected) return;
    setUploading(true); setProgress(null); setError(null);
    try {
      const access = await upload(selected.uri, selected.fileName ?? 'clip.mp4', selected.mimeType ?? 'video/mp4', setProgress);
      setCredential(access); setSelected(null);
    } catch (error) { setError(error instanceof Error ? error.message : 'Upload failed. Please retry.'); }
    finally { setUploading(false); }
  }
  async function forget() {
    if (!credential) return;
    try { await deleteJob(credential); setCredential(null); setError(null); }
    catch (error) { setError(error instanceof Error ? error.message : 'Could not delete recognition.'); }
  }
  return <SafeAreaView style={{ flex: 1, backgroundColor: color.background }}>
    <StatusBar style={color === palette.dark ? 'light' : 'dark'} />
    <ScrollView contentContainerStyle={styles.scroll}>
      <View style={styles.header}><View style={[styles.mark, { borderColor: color.accent }]}><Text style={{ color: color.accent, fontSize: 24 }}>⌕</Text></View>
        <Text style={[styles.brand, textStyle]}>FrameTrace</Text><View style={{ flex: 1 }} /><Pressable accessibilityRole="button" onPress={() => router.push('/account')} style={{ minHeight: 44, justifyContent: 'center' }}><Text style={{ color: color.accent }}>Account & history</Text></Pressable></View>
      <Text style={[styles.eyebrow, { color: color.accent }]}>EVERY CLIP HAS A STORY</Text>
      <Text accessibilityRole="header" style={[styles.headline, textStyle]}>What video is{ '\n' }this from?</Text>
      <Text style={[styles.subtitle, { color: color.muted }]}>Upload a clip and discover its source.</Text>
      <View style={[styles.panel, { backgroundColor: color.surface, borderColor: color.border }]}>
        <Text style={[styles.section, textStyle]}>{selected ? 'Your clip, ready to trace' : 'See a clip. Find the original.'}</Text>
        {selected ? <><Preview uri={selected.uri} /><Text style={{ color: color.muted }}>{selected.fileName ?? 'Selected video'} · {selected.duration == null ? 'Duration checked on upload' : `${(selected.duration / 1000).toFixed(1)} seconds`}</Text>
          <Button title={uploading ? progress === null ? 'Uploading…' : `Uploading ${Math.round(progress * 100)}%` : 'Identify this Video'} onPress={identify} disabled={uploading || working} />
          <Button title="Choose a different clip" secondary onPress={choose} disabled={uploading} /></>
          : <><Text style={[styles.body, { color: color.muted }]}>Choose a short video from your gallery. We’ll look for matching moments in our reference catalog.</Text>
            <Button title="Identify a Video  ↗" onPress={choose} disabled={uploading || restoring} />
            <Text style={[styles.caption, { color: color.muted }]}>MP4 or MOV · Up to 30 seconds · Max 50 MB</Text></>}
      </View>
      {(error || job.error) && <View accessibilityRole="alert" style={[styles.panel, { borderColor: color.border }]}><Text style={{ color: color.text }}>{error ?? job.error?.message}</Text>
        {job.error && <Button title="Retry connection" secondary onPress={() => { void job.refetch(); }} />}</View>}
      {restoring && <ActivityIndicator accessibilityLabel="Restoring last recognition" color={color.accent} />}
      {credential && <View style={[styles.panel, { backgroundColor: color.surface, borderColor: color.border }]}>
        <Text accessibilityRole="header" style={[styles.section, textStyle]}>Latest discovery</Text>
        {working && <><ActivityIndicator color={color.accent} /><Text accessibilityLiveRegion="polite" style={{ color: color.muted }}>{stages[job.data?.status ?? 'queued'] ?? 'Retrieving recognition'}</Text>
          <Text style={[styles.caption, { color: color.muted }]}>Your search continues on the server. You can return to this result later.</Text></>}
        {job.data?.status === 'failed' && <Text style={textStyle}>{job.data.error ?? 'Recognition failed. Try another clip.'}</Text>}
        {result && <><Text style={[styles.section, textStyle]}>{result.classification === 'no_match' ? "We couldn’t identify this clip yet." : result.classification === 'possible_match' ? 'Possible matches' : 'Matching segment found'}</Text>
          <Text style={[styles.body, { color: color.muted }]}>{result.reason}</Text>
          {result.candidates.map(candidate => <View key={`${candidate.reference_id}-${candidate.start_seconds}`} style={[styles.candidate, { borderColor: color.border }]}>
            <Text style={[styles.section, textStyle]}>{candidate.title}</Text>
            <Text style={{ color: color.muted }}>{candidate.publisher}</Text>
            <Text style={{ color: color.accent }}>At {timestamp(candidate.start_seconds)} · ±{candidate.timestamp_uncertainty_seconds}s</Text>
            <Text style={[styles.caption, { color: color.muted }]}>{candidate.evidence.aligned_frames} of {candidate.evidence.query_frames} sampled frames align. This identifies an indexed recording, not its original creator.</Text>
            {candidate.source_url?.startsWith('https://') && <Button title="Open indexed source" secondary onPress={() => { void Linking.openURL(candidate.source_url!).catch(() => Alert.alert('Unable to open source')); }} />}
          </View>)}
          {result.classification === 'no_match' && <Text style={{ color: color.muted }}>Try a clearer or longer excerpt. The source may not be in our catalog yet.</Text>}</>}
        {!working && <Button title="Delete this recognition" secondary onPress={() => Alert.alert('Delete recognition?', 'This removes the server result and the saved access on this device.', [{ text: 'Cancel', style: 'cancel' }, { text: 'Delete', style: 'destructive', onPress: () => { void forget(); } }])} />}
      </View>}
      <View style={styles.footer}><Text style={[styles.section, textStyle]}>A match you can trust.</Text><Text style={[styles.body, { color: color.muted }]}>Searches use an authorized reference catalog. If there isn’t enough evidence, we’ll say so. Clips are deleted after processing.</Text>
        <Text style={[styles.caption, { color: color.muted }]}>Development build · Visual matching only · Native sharing coming later</Text>
        <View style={styles.appearance}>{(['system', 'dark', 'light'] as const).map(mode => <Pressable key={mode} accessibilityRole="button" accessibilityState={{ selected: appearance === mode }} onPress={() => setAppearance(mode)} style={[styles.mode, { borderColor: appearance === mode ? color.accent : color.border }]}><Text style={{ color: color.text }}>{mode[0].toUpperCase() + mode.slice(1)}</Text></Pressable>)}</View>
      </View>
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  scroll: { padding: 24, paddingBottom: 48, gap: tokens.gap, width: '100%', maxWidth: tokens.maxWidth, alignSelf: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 36, flexWrap: 'wrap' },
  mark: { width: 38, height: 38, borderWidth: 2, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  brand: { fontSize: 23, fontWeight: '700', letterSpacing: -.8 },
  eyebrow: { fontSize: 11, fontWeight: '700', letterSpacing: 2 },
  headline: { fontSize: 46, lineHeight: 51, fontWeight: '800', letterSpacing: -2 },
  subtitle: { fontSize: 17, lineHeight: 26, marginBottom: 14 },
  panel: { padding: 22, borderWidth: 1, borderRadius: tokens.radius, gap: 16 },
  section: { fontSize: 19, fontWeight: '700', lineHeight: 27 },
  body: { fontSize: 15, lineHeight: 24 },
  caption: { fontSize: 12, lineHeight: 19 },
  button: { minHeight: 54, borderRadius: 14, borderWidth: 1, padding: 16, alignItems: 'center', justifyContent: 'center' },
  buttonText: { fontSize: 16, fontWeight: '700', textAlign: 'center' },
  video: { width: '100%', aspectRatio: 16 / 10, borderRadius: 12 },
  candidate: { borderTopWidth: 1, paddingTop: 18, gap: 10 },
  footer: { paddingTop: 12, gap: 14 },
  appearance: { flexDirection: 'row', gap: 10, flexWrap: 'wrap' },
  mode: { borderWidth: 1, borderRadius: 12, minHeight: 44, paddingHorizontal: 16, justifyContent: 'center' },
});
