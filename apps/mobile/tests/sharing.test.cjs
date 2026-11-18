const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const context = { exports: {}, URL, Set, Date };
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/sharing/policy.ts', 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, context);
const { validatePending, validateConsumed, sharedLinkExplanation } = context.exports;
const valid = () => ({ id: '12345678-1234-1234-1234-123456789abc', createdAt: Date.now(), kind: 'video', fileSize: 1024, durationMs: 6000, width: 320, height: 240, mimeType: 'video/mp4', uri: 'file:///private/cache/FrameTraceShares/12345678-1234-1234-1234-123456789abc/clip.mp4' });

test('accepts a bounded private native copy for preview', () => {
  const item = validateConsumed(valid());
  assert.equal(item.durationMs, 6000);
  assert.equal(item.kind, 'video');
});
test('rejects oversized, overlong, invalid resolution and stale media', () => {
  for (const change of [{ fileSize: 51*1024*1024 }, { durationMs: 31000 }, { width: 10000, height: 10000 }, { durationMs: NaN }, { createdAt: Date.now()-25*3600*1000 }]) {
    assert.throws(() => validateConsumed({ ...valid(), ...change }));
  }
});
test('does not accept external URLs, content URIs or arbitrary local files as native copies', () => {
  for (const uri of ['https://example.com/video.mp4', 'content://provider/video', 'file://remote/cache/clip.mp4', 'file:///etc/passwd']) assert.throws(() => validateConsumed({ ...valid(), uri }));
  assert.throws(() => validateConsumed({ ...valid(), id: '../../private' }));
});
test('shared links remain unsupported and contain no downloadable query/path', () => {
  const link = validatePending({ id: valid().id, createdAt: Date.now(), kind: 'link', sourceHost: 'example.com', url: 'https://example.com/private?secret=never-keep' });
  assert.equal(link.sourceHost, 'example.com');
  assert.equal(link.url, undefined);
  assert.match(sharedLinkExplanation(), /cannot be downloaded/);
  assert.throws(() => validateConsumed(link));
});
test('provider errors do not expose borrowed URI/token details', () => {
  const error = validatePending({ id: valid().id, createdAt: Date.now(), kind: 'error', message: 'content://private?token=secret' });
  assert.ok(!error.message.includes('secret'));
});
