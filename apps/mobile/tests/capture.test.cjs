const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function setup({ platform = 'android', camera = true, microphone = true, canceled = false } = {}) {
  const calls = [];
  const video = { uri: 'file:///cache/recording.mp4', type: 'video', duration: 5000, fileSize: 1024, width: 640, height: 480 };
  const picker = {
    requestCameraPermissionsAsync: async () => { calls.push('camera permission'); return { granted: camera, canAskAgain: false }; },
    launchCameraAsync: async options => { calls.push(options); return { canceled, assets: [video] }; },
    UIImagePickerControllerQualityType: { Medium: 1 },
  };
  const native = { Platform: { OS: platform }, PermissionsAndroid: {
    PERMISSIONS: { RECORD_AUDIO: 'audio' }, RESULTS: { GRANTED: 'granted' },
    request: async () => { calls.push('microphone permission'); return microphone ? 'granted' : 'denied'; },
  } };
  const context = { exports: {}, require: name => name === 'expo-image-picker' ? picker : native };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/media/capture.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return { ...context.exports, calls, video };
}
test('recording asks for camera and Android microphone before opening bounded camera', async () => {
  const api = setup();
  assert.equal(await api.recordVideo(), api.video);
  assert.equal(api.calls[0], 'camera permission');
  assert.equal(api.calls[1], 'microphone permission');
  assert.equal(api.calls[2].videoMaxDuration, 30);
  assert.equal(api.calls[2].allowsEditing, false);
});
test('denied permissions never open camera', async () => {
  for (const options of [{ camera: false }, { microphone: false }]) {
    const api = setup(options);
    await assert.rejects(api.recordVideo(), /access/);
    assert.ok(api.calls.every(value => typeof value === 'string'));
  }
});
test('cancellation returns no clip and iOS delegates microphone prompting to system camera', async () => {
  const api = setup({ platform: 'ios', canceled: true });
  assert.equal(await api.recordVideo(), null);
  assert.equal(api.calls.length, 2);
});
test('web recording is rejected without a permission prompt', async () => {
  const api = setup({ platform: 'web' });
  await assert.rejects(api.recordVideo(), /Android or iOS/);
  assert.equal(api.calls.length, 0);
});
test('preflight rejects invalid durations, sizes, dimensions and remote assets', () => {
  const api = setup();
  api.validateVideo({ ...api.video, duration: 30000, fileSize: 50 * 1024 * 1024 });
  // Some system providers omit duration or size. Server validation remains required.
  api.validateVideo({ ...api.video, duration: undefined, fileSize: undefined });
  for (const change of [{ duration: 0 }, { duration: NaN }, { duration: 30001 }, { fileSize: 0 }, { fileSize: Infinity }, { width: 0 }, { width: 10000, height: 10000 }, { uri: 'https://example.com/clip.mp4' }, { type: 'image' }]) {
    assert.throws(() => api.validateVideo({ ...api.video, ...change }));
  }
});
