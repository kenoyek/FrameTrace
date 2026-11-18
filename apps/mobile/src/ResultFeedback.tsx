import { useEffect, useRef, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { sendFeedback, type Credential, type FeedbackRating } from './api';
import { useAppearance } from './settings/AppearanceProvider';

export function ResultFeedback({ credential, initial }: { credential: Credential; initial: FeedbackRating | null }) {
  const { color } = useAppearance();
  const [rating, setRating] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const lock = useRef(false);
  const mounted = useRef(true);
  // Background refetches can finish before a newer save. Keep acknowledged local feedback.
  const savedLocally = useRef(false);
  useEffect(() => { if (!savedLocally.current) setRating(initial); }, [initial]);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  async function submit(value: FeedbackRating) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setMessage(null);
    try {
      const saved = await sendFeedback(credential, value);
      if (mounted.current) { savedLocally.current = true; setRating(saved); setMessage('Feedback saved. Thank you.'); }
    } catch (error) { if (mounted.current) setMessage(error instanceof Error ? error.message : 'Feedback could not be saved. Please retry.'); }
    finally { lock.current = false; if (mounted.current) setBusy(false); }
  }
  return <View style={{ gap: 12 }}>
    <Text accessibilityRole="header" style={{ color: color.text, fontSize: 17, fontWeight: '700' }}>Was this result helpful?</Text>
    <Text style={{ color: color.muted, lineHeight: 22 }}>Optional. Your response stays with this recognition and does not change the match or train a model automatically.</Text>
    {([['helpful', 'Helpful'], ['not_helpful', 'Not helpful'], ['unsure', 'Not sure']] as const).map(([value, label]) => <Pressable key={value}
      accessibilityRole="radio" accessibilityState={{ checked: rating === value, disabled: busy }} disabled={busy}
      onPress={() => { void submit(value); }} style={{ minHeight: 48, borderWidth: 1, borderColor: rating === value ? color.accent : color.border, borderRadius: 12, padding: 14, justifyContent: 'center', opacity: busy ? .5 : 1 }}>
      <Text style={{ color: color.text }}>{label}{rating === value ? ' · Selected' : ''}</Text>
    </Pressable>)}
    {(message || busy) && <Text accessibilityLiveRegion="polite" style={{ color: color.text }}>{busy ? 'Saving feedback…' : message}</Text>}
  </View>;
}
