// API boundary tests with simulated transport/native modules. Real recognition is tested in Python.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function client() {
  const storage = new Map();
  const requests = [];
  const replies = [];
  let failStorage = false;
  let session = null;
  const fetches = [];
  const store = {
    async getItemAsync(key) { return storage.get(key) ?? null; },
    async setItemAsync(key, value) { if (failStorage) throw Error('storage unavailable'); storage.set(key, value); },
    async deleteItemAsync(key) { storage.delete(key); },
  };
  class XHR {
    upload = {};
    headers = {};
    open() {}
    setRequestHeader(key, value) { this.headers[key] = value; }
    send() {
      assert.ok(storage.has('frametrace.pendingSubmission'), 'persist before network');
      requests.push(this);
      const reply = replies.shift();
      if (reply === 'lost') return queueMicrotask(() => this.onerror());
      this.status = reply?.status ?? 202;
      this.responseText = JSON.stringify(reply?.body ?? { id: 'one-job', access_token: this.headers['X-Submission-Token'], status: 'queued' });
      queueMicrotask(() => this.onload());
    }
  }
  const output = ts.transpileModule(fs.readFileSync('src/api.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const context = { exports: {}, require(name) {
    if (name === './auth') return { authSession: async () => session };
    if (name === 'expo-secure-store') return store;
    if (name === 'expo-crypto') return { getRandomBytes: () => require('node:crypto').randomBytes(32) };
    throw Error(name);
  }, process: { env: { EXPO_PUBLIC_API_URL: 'https://example.test' } },
    fetch: async (url, options) => { fetches.push({ url, options }); return { ok: true, json: async () => ({ id: "one-job", status: "queued" }) }; }, XMLHttpRequest: XHR, FormData: class { append() {} }, queueMicrotask };
  vm.runInNewContext(output, context);
  return { api: context.exports, storage, requests, replies, fetches, setSession(value) { session = value; }, failStorage() { failStorage = true; } };
}

test('lost response retry reuses persisted capability and remembers result', async () => {
  const c = client();
  c.replies.push('lost');
  await assert.rejects(c.api.upload('file:///clip.mp4', 'clip.mp4', 'video/mp4', () => {}), /connect/);
  const pending = await c.api.restorePending();
  assert.match(pending.token, /^[a-f0-9]{64}$/);
  assert.equal(c.requests.length, 1);
  // Merely restoring the clip never uploads it automatically.
  assert.equal(c.requests.length, 1);
  const result = await c.api.upload('file:///clip.mp4', 'clip.mp4', 'video/mp4', () => {});
  assert.equal(c.requests[0].headers['X-Submission-Token'], c.requests[1].headers['X-Submission-Token']);
  assert.equal(result.access_token, pending.token);
  assert.equal((await c.api.restore()).id, 'one-job');
  assert.equal(await c.api.restorePending(), null);
});

test('a different selected clip receives a new capability', async () => {
  const c = client();
  c.replies.push('lost');
  await assert.rejects(c.api.upload('file:///first.mp4', 'clip.mp4', 'video/mp4', () => {}));
  const first = (await c.api.restorePending()).token;
  c.replies.push('lost');
  await assert.rejects(c.api.upload('file:///second.mp4', 'clip.mp4', 'video/mp4', () => {}));
  assert.notEqual((await c.api.restorePending()).token, first);
});

test('secure storage failure prevents upload', async () => {
  const c = client();
  c.failStorage();
  await assert.rejects(c.api.upload('file:///clip.mp4', 'clip.mp4', 'video/mp4', () => {}), /storage/);
  assert.equal(c.requests.length, 0);
});

test('server rejection retains retry capability and does not invent a result', async () => {
  const c = client();
  c.replies.push({ status: 429, body: { detail: 'Uploads are busy; please retry.' } });
  await assert.rejects(c.api.upload('file:///clip.mp4', 'clip.mp4', 'video/mp4', () => {}), /busy/);
  assert.ok(await c.api.restorePending());
  assert.equal(await c.api.restore(), null);
});


test('account uploads use a session JWT and cannot be fetched under another account', async () => {
  const c = client();
  c.setSession({ user: { id: 'user-a' }, access_token: 'signed-jwt-a' });
  const access = await c.api.upload('file:///clip.mp4', 'clip.mp4', 'video/mp4', () => {});
  assert.equal(access.user_id, 'user-a');
  assert.equal(c.requests[0].headers.Authorization, 'Bearer signed-jwt-a');
  await c.api.fetchJob(access);
  assert.equal(c.fetches[0].options.headers.Authorization, 'Bearer signed-jwt-a');
  c.setSession({ user: { id: 'user-b' }, access_token: 'signed-jwt-b' });
  await assert.rejects(c.api.fetchJob(access), /account that owns/);
  assert.equal(c.fetches.length, 1);
});

test('guest discovery keeps its capability until explicitly claimed', async () => {
  const c = client();
  const access = await c.api.upload('file:///clip.mp4', 'clip.mp4', 'video/mp4', () => {});
  c.setSession({ user: { id: 'user-a' }, access_token: 'signed-jwt-a' });
  await c.api.fetchJob(access);
  assert.equal(c.fetches[0].options.headers.Authorization, 'Bearer '+access.access_token);
});
