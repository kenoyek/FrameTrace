const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function storage() {
  const values = new Map();
  let failAfter = Infinity;
  const native = {
    async getItemAsync(key) { return values.get(key) ?? null; },
    async setItemAsync(key, value) {
      if (--failAfter < 0) throw Error('native write interrupted');
      assert.ok(Buffer.byteLength(value, 'utf8') < 2048);
      values.set(key, value);
    },
    async deleteItemAsync(key) { values.delete(key); },
  };
  const context = { exports: {}, require(name) {
    if (name === 'expo-secure-store') return native;
    if (name === 'expo-crypto') return { getRandomBytes: n => require('node:crypto').randomBytes(n) };
    throw Error(name);
  } };
  const output = ts.transpileModule(fs.readFileSync('src/sessionStorage.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  vm.runInNewContext(output, context);
  return { api: context.exports.secureSessionStorage, values, failAfter(n) { failAfter = n; } };
}
test('large Unicode sessions round-trip through bounded secure entries', async () => {
  const s = storage();
  const value = '🔎'.repeat(1700)+'session data';
  await s.api.setItem('session', value);
  assert.equal(await s.api.getItem('session'), value);
  assert.ok(s.values.size > 2);
});
test('interrupted replacement preserves previous committed session', async () => {
  const s = storage();
  await s.api.setItem('session', 'previous-valid-session');
  s.failAfter(1);
  await assert.rejects(s.api.setItem('session', 'replacement'.repeat(500)), /interrupted/);
  assert.equal(await s.api.getItem('session'), 'previous-valid-session');
});
test('serialized updates and sign-out remove the accessible session', async () => {
  const s = storage();
  await Promise.all([s.api.setItem('session', 'first'), s.api.setItem('session', 'second')]);
  assert.equal(await s.api.getItem('session'), 'second');
  await s.api.removeItem('session');
  assert.equal(await s.api.getItem('session'), null);
  assert.equal(s.values.size, 0);
});
test('missing secure chunks fail closed instead of returning a partial token', async () => {
  const s = storage();
  await s.api.setItem('session', 'some token');
  const index = JSON.parse(s.values.get('session.index'));
  s.values.delete(`session.${index.id}.0`);
  await assert.rejects(s.api.getItem('session'), /incomplete/);
});
