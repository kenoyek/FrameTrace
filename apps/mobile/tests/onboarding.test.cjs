const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function setup(initial = null, failure = null) {
  let saved = initial;
  const keys = [];
  const storage = {
    getItemAsync: async key => { keys.push(key); if (failure === 'read') throw new Error('unavailable'); return saved; },
    setItemAsync: async (key, value) => { keys.push(key); if (failure === 'write') throw new Error('unavailable'); saved = value; },
  };
  const context = { exports: {}, require: name => {
    assert.equal(name, 'expo-secure-store'); return storage;
  } };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/onboarding/preference.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return { ...context.exports, keys };
}
test('fresh, malformed and outdated preference values show the introduction', async () => {
  for (const value of [null, '', 'true', '0', '{broken']) assert.equal(await setup(value).introductionSeen(), false);
});
test('successful completion persists only its own versioned local preference', async () => {
  const api = setup();
  await api.rememberIntroduction();
  assert.equal(await api.introductionSeen(), true);
  assert.ok(api.keys.every(key => key === 'frametrace.introduction'));
});
test('read failure is surfaced for the explicit session-only fallback', async () => {
  await assert.rejects(setup(null, 'read').introductionSeen(), /unavailable/);
});
test('failed completion cannot mark the introduction as saved', async () => {
  const api = setup(null, 'write');
  await assert.rejects(api.rememberIntroduction(), /unavailable/);
  assert.equal(await api.introductionSeen(), false);
});
