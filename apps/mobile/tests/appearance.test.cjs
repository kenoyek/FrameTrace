const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function setup(storage) {
  const context = { exports: {}, require: name => {
    assert.equal(name, 'expo-secure-store'); return storage;
  } };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/settings/appearance.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return context.exports;
}
test('missing or malformed preferences use system and valid choices round-trip', async () => {
  let saved = null;
  const api = setup({ getItemAsync: async () => saved, setItemAsync: async (key, value) => {
    assert.equal(key, 'frametrace.appearance'); saved = value;
  } });
  for (const value of [null, '', 'unexpected', '{broken']) { saved = value; assert.equal(await api.loadAppearance(), 'system'); }
  for (const value of ['light', 'dark', 'system']) { await api.saveAppearance(value); assert.equal(await api.loadAppearance(), value); }
});
test('system follows live device values and explicit modes override them', () => {
  const api = setup({});
  assert.equal(api.resolveAppearance('system', 'light'), 'light');
  assert.equal(api.resolveAppearance('system', 'dark'), 'dark');
  assert.equal(api.resolveAppearance('system', null), 'dark');
  assert.equal(api.resolveAppearance('dark', 'light'), 'dark');
  assert.equal(api.resolveAppearance('light', 'dark'), 'light');
});
test('rapid choices are serialized so earlier slow writes cannot win', async () => {
  const started = [];
  let release;
  const blocked = new Promise(resolve => { release = resolve; });
  let saved;
  const api = setup({ setItemAsync: async (_key, value) => {
    started.push(value); if (value === 'dark') await blocked; saved = value;
  } });
  const first = api.saveAppearance('dark');
  const last = api.saveAppearance('light');
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(started, ['dark']);
  release(); await Promise.all([first, last]);
  assert.deepEqual(started, ['dark', 'light']); assert.equal(saved, 'light');
});
test('failed writes are surfaced and do not poison later saves', async () => {
  let fail = true;
  let saved;
  const api = setup({ setItemAsync: async (_key, value) => {
    if (fail) throw new Error('storage unavailable'); saved = value;
  } });
  await assert.rejects(api.saveAppearance('dark'), /storage unavailable/);
  fail = false; await api.saveAppearance('light'); assert.equal(saved, 'light');
  await assert.rejects(api.saveAppearance('invalid'), /Invalid/);
  assert.equal(saved, 'light');
});
test('read failures are surfaced for session-only fallback', async () => {
  const api = setup({ getItemAsync: async () => { throw new Error('storage unavailable'); } });
  await assert.rejects(api.loadAppearance(), /storage unavailable/);
});
