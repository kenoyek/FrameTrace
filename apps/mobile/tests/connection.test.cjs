const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function setup(base, fetch) {
  const context = { exports: {}, URL, AbortController, setTimeout, clearTimeout,
    process: { env: { EXPO_PUBLIC_API_URL: base } }, fetch };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/connection.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return context.exports.checkConnection;
}
test('missing or invalid API config makes no request', async () => {
  const fetch = () => { throw Error('must not call'); };
  assert.equal((await setup(undefined, fetch)()).state, 'not_configured');
  for (const base of ['invalid', 'ftp://example.test', 'https://user:secret@example.test', 'https://example.test?token=private', 'https://example.test/#fragment']) {
    assert.equal((await setup(base, fetch)()).state, 'invalid_configuration');
  }
});
test('valid health probe preserves API prefix and sends no credentials', async () => {
  const check = setup('https://example.test/api/', async (url, options) => {
    assert.equal(url, 'https://example.test/api/health');
    assert.equal(options.method, 'GET');
    assert.equal(options.credentials, 'omit');
    assert.equal(options.headers.Authorization, undefined);
    assert.equal(options.body, undefined);
    return { ok: true, json: async () => ({ status: 'ok', execution: 'celery' }) };
  });
  const result = await check();
  assert.equal(result.state, 'responding');
  assert.match(result.message, /does not test/);
});
test('nonhealthy and unrelated services do not pass the connection check', async () => {
  assert.equal((await setup('https://example.test', async () => ({ ok: false }))()).state, 'unreachable');
  for (const health of [{ status: 'ok' }, { status: 'failed', execution: 'local' }, null]) {
    assert.equal((await setup('https://example.test', async () => ({ ok: true, json: async () => health }))()).state, 'incompatible');
  }
});
test('transport or malformed JSON errors expose no server details', async () => {
  for (const fetch of [async () => { throw Error('private server token'); }, async () => ({ ok: true, json: async () => { throw Error('private payload'); } })]) {
    const result = await setup('https://example.test', fetch)();
    assert.equal(result.state, 'unreachable');
    assert.ok(!result.message.includes('private'));
  }
});
test('timeout aborts an outstanding request', async () => {
  const check = setup('https://example.test', (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(Error('aborted')));
  }));
  assert.equal((await check(undefined, 5)).state, 'unreachable');
});
test('caller cancellation stops the probe and pre-cancellation sends no request', async () => {
  const controller = new AbortController();
  controller.abort();
  assert.equal((await setup('https://example.test', () => { throw Error('must not call'); })(controller.signal)).state, 'cancelled');
  const next = new AbortController();
  const check = setup('https://example.test', (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(Error('aborted')));
  }));
  const pending = check(next.signal); next.abort();
  assert.equal((await pending).state, 'cancelled');
});
