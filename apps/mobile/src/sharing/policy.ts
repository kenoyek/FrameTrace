export const SHARE_LIMITS = { bytes: 50 * 1024 * 1024, durationMs: 30000, ttlMs: 24 * 3600 * 1000 };
export type SharedItem = { id: string; createdAt: number } & (
  { kind: 'video'; fileSize: number; durationMs: number; width: number; height: number; mimeType: 'video/mp4' } |
  { kind: 'link'; sourceHost: string } | { kind: 'error'; message: string }
);
export type SharedVideo = Extract<SharedItem, { kind: 'video' }> & { uri: string };
const idPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const friendlyErrors = new Set([
  'Share one video at a time.', 'Share an MP4 or MOV video file.',
  'Choose a valid MP4 or MOV video.', 'Share a clip between 1 and 30 seconds.',
  'This video resolution is unsupported.', 'Choose a video smaller than 50 MB.',
  'Import took too long. Try another video.', 'The shared video permission expired. Share it again.',
  'Choose this video from your gallery instead.',
]);
export function validatePending(value: unknown, now = Date.now()): SharedItem | null {
  if (value === null) return null;
  if (!value || typeof value !== 'object') throw new Error('The shared item could not be read.');
  const raw = value as Record<string, unknown>;
  if (typeof raw.id !== 'string' || !idPattern.test(raw.id) || typeof raw.createdAt !== 'number' ||
      !Number.isFinite(raw.createdAt) || raw.createdAt > now + 300000) throw new Error('The shared item could not be read.');
  if (now - raw.createdAt > SHARE_LIMITS.ttlMs) throw new Error('This shared item expired. Share it again.');
  const common = { id: raw.id, createdAt: raw.createdAt };
  if (raw.kind === 'link') {
    return { ...common, kind: 'link', sourceHost: typeof raw.sourceHost === 'string' && /^[a-z0-9.-]{1,253}$/i.test(raw.sourceHost) ? raw.sourceHost : 'this source' };
  }
  if (raw.kind === 'error') return { ...common, kind: 'error', message: typeof raw.message === 'string' && friendlyErrors.has(raw.message) ? raw.message : 'This item could not be imported. Share another MP4 or MOV video.' };
  const numeric = ['fileSize', 'durationMs', 'width', 'height'] as const;
  if (raw.kind !== 'video' || numeric.some(key => typeof raw[key] !== 'number' || !Number.isFinite(raw[key]))) throw new Error('The shared item is not a supported video.');
  const { fileSize, durationMs, width, height } = raw as Record<typeof numeric[number], number>;
  if (fileSize < 12 || fileSize > SHARE_LIMITS.bytes) throw new Error('Choose a video smaller than 50 MB.');
  if (durationMs < 1000 || durationMs > SHARE_LIMITS.durationMs) throw new Error('Share a clip between 1 and 30 seconds.');
  if (width <= 0 || height <= 0 || width * height > 3840 * 2160) throw new Error('This video resolution is unsupported.');
  return { ...common, kind: 'video', fileSize, durationMs, width, height, mimeType: 'video/mp4' };
}
export function validateConsumed(value: unknown): SharedVideo {
  const item = validatePending(value);
  if (!item || item.kind !== 'video') throw new Error('Choose a shared video file to identify.');
  const uri = (value as Record<string, unknown>).uri;
  if (typeof uri !== 'string') throw new Error('Shared video access expired. Share it again.');
  const parsed = new URL(uri);
  if (parsed.protocol !== 'file:' || parsed.hostname || !decodeURIComponent(parsed.pathname).endsWith(`/FrameTraceShares/${item.id}/clip.mp4`)) throw new Error('Shared video access could not be verified.');
  return { ...item, uri };
}
export function sharedLinkExplanation(): string {
  return 'Shared links cannot be downloaded from this source. Choose a permitted video file from your gallery instead.';
}
