import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';
import test from 'node:test';

const source = readFileSync(new URL('../worker.js', import.meta.url), 'utf8');
const workerContext = vm.createContext({});
vm.runInContext(source.replace('export default {', 'const worker = {') + '\nthis.html=indexHtml();', workerContext);
const html = workerContext.html;
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];

function storage() {
  const data = new Map();
  return { data, getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, value) };
}

// Run the actual page script with DOM controls that coerce values as browser inputs do.
function page(localStorage, confirm = () => true) {
  function control(name, initial = '') {
    let value = initial;
    const handlers = {};
    return {
      name, hidden: true, textContent: '',
      get value() { return value; }, set value(next) { value = String(next); },
      addEventListener: (type, handler) => (handlers[type] ??= []).push(handler),
      fire(type) { for (const handler of handlers[type] ?? []) handler(); },
      checkValidity() { return this.value !== '' && Number.isInteger(Number(this.value)); },
      reportValidity() {}, focus() {},
    };
  }
  const numbers = [...html.matchAll(/<input type="number" name="([^"]+)" value="([^"]+)"/g)]
    .map(match => control(match[1], match[2]));
  const preset = control('preset', 'custom');
  preset.options = [...html.matchAll(/<option value="([^"]+)"/g)].map(match => ({ value: match[1] }));
  preset.appendChild = option => {
    option.remove = () => preset.options.splice(preset.options.indexOf(option), 1);
    preset.options.push(option);
  };
  const name = control('custom_preset_name');
  const save = control('save-custom-preset');
  const remove = control('delete-custom-preset');
  const message = control('preset-message');
  const form = {
    ...Object.fromEntries(numbers.map(field => [field.name, field])),
    querySelector: selector => selector.includes('custom_preset_name') ? name : preset,
    querySelectorAll: () => numbers, addEventListener() {},
  };
  const elements = { 'analyze-form': form, 'save-custom-preset': save,
    'delete-custom-preset': remove, 'preset-message': message };
  vm.runInNewContext(script, {
    document: { getElementById: id => elements[id], createElement: () => ({}) },
    localStorage, crypto: webcrypto, confirm,
  });
  return { form, numbers, preset, name, save, remove, message };
}

test('save all numeric settings, select, and restore across page loads without files', () => {
  const store = storage();
  const p = page(store);
  p.numbers.forEach((field, index) => { field.value = index + 100; });
  p.name.value = 'My preset';
  p.save.fire('click');
  const id = p.preset.value;
  assert.match(id, /^user:/);
  assert.equal(p.remove.hidden, false);
  const saved = JSON.parse(store.getItem('jan-web.custom-presets.v1'));
  assert.equal(saved[0].name, 'My preset');
  assert.equal(Object.keys(saved[0].settings).length, 9);
  assert.equal('paifu_files' in saved[0].settings, false);
  const restored = page(store);
  assert.equal(restored.preset.value, id);
  assert.equal(restored.remove.hidden, false);
  restored.numbers.forEach((field, index) => assert.equal(field.value, String(index + 100)));
  restored.form.rate.value = '999';
  restored.form.rate.fire('input');
  assert.equal(restored.preset.value, 'custom');
  assert.equal(restored.remove.hidden, true);
  restored.preset.value = id;
  restored.preset.fire('change');
  assert.equal(restored.form.rate.value, '100');
  assert.equal(restored.name.value, 'My preset');
});

test('overwriting uses the same ID and deletion persists without changing numeric fields', () => {
  const store = storage();
  const p = page(store);
  p.name.value = 'Home'; p.save.fire('click');
  const id = p.preset.value;
  p.form.rate.value = '77'; p.form.rate.fire('change'); p.save.fire('click');
  assert.equal(p.preset.value, id);
  assert.equal(JSON.parse(store.getItem('jan-web.custom-presets.v1')).length, 1);
  p.remove.fire('click');
  assert.equal(p.preset.value, 'custom');
  assert.equal(p.form.rate.value, '77');
  assert.equal(p.remove.hidden, true);
  assert.equal(p.preset.options.some(option => option.value === id), false);
  assert.equal(page(store).preset.options.some(option => option.value === id), false);
});

test('built-in presets cannot be deleted or overwritten by a matching display name', () => {
  const p = page(storage());
  p.name.value = 'テンピン'; p.save.fire('click');
  assert.match(p.preset.value, /^user:/);
  p.preset.value = 'tenpin'; p.preset.fire('change');
  assert.equal(p.form.rate.value, '100');
  assert.equal(p.remove.hidden, true);
  const count = p.preset.options.length;
  p.remove.fire('click');
  assert.equal(p.preset.options.length, count);
  assert.equal(p.preset.value, 'tenpin');
  p.form.oka_1.fire('change');
  assert.equal(p.preset.value, 'custom');
});

test('empty names, invalid values and cancelled overwrite preserve saved presets', () => {
  const store = storage(); const p = page(store, () => false);
  p.save.fire('click');
  assert.equal(store.getItem('jan-web.custom-presets.v1'), null);
  p.name.value = 'Home'; p.form.rate.value = ''; p.save.fire('click');
  assert.equal(store.getItem('jan-web.custom-presets.v1'), null);
  p.form.rate.value = '50'; p.save.fire('click');
  p.form.rate.value = '90'; p.save.fire('click');
  assert.equal(JSON.parse(store.getItem('jan-web.custom-presets.v1'))[0].settings.rate, '50');
});

test('unavailable or corrupt storage fails gracefully and names are rendered as text', () => {
  const blocked = page({ getItem() { throw Error('blocked'); }, setItem() { throw Error('blocked'); } });
  blocked.name.value = 'Home'; blocked.save.fire('click');
  assert.equal(blocked.preset.value, 'custom');
  assert.match(blocked.message.textContent, /保存できません/);
  assert.equal(blocked.remove.hidden, true);
  const store = storage();
  store.setItem('jan-web.custom-presets.v1', '{invalid');
  const p = page(store);
  p.name.value = '<img src=x onerror=alert(1)>';
  p.save.fire('click');
  assert.equal(p.preset.options.at(-1).textContent, '<img src=x onerror=alert(1)>（保存済み）');
});
