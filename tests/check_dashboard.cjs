// Dependency-free script interaction smoke test. This is not a layout renderer.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2], 'utf8');
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.handlers = {}; this.clientWidth = 1000; this._value = null; this._text = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; this._value = null; }
  setAttribute(name, value) { this[name] = value; }
  addEventListener(name, handler) { this.handlers[name] = handler; }
  get options() { return this.children; }
  get value() { return this._value ?? (this.tag === 'select' ? this.children[0]?.value ?? '' : ''); }
  set value(value) { this._value = value; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(' '); }
  set textContent(value) { this._text = value; this.children = []; }
}
const elements = {};
for (const match of html.matchAll(/<([a-z]+)[^>]*\bid="([^"]+)"/g)) elements[match[2]] = new Element(match[1]);
elements['benchmark-data'].textContent = html.match(/<script id="benchmark-data"[^>]*>([\s\S]*?)<\/script>/)[1];
const originalReports = JSON.parse(elements['benchmark-data'].textContent);
const mismatch = structuredClone(originalReports[0]);
mismatch.run_id = 'incompatible-test'; mismatch.created_at = '2000-01-01';
mismatch.puzzles[0].fingerprint = 'changed-puzzle';
const budgetMismatch = structuredClone(originalReports[0]);
budgetMismatch.run_id = 'budget-test'; budgetMismatch.created_at = '2000-01-01';
budgetMismatch.budget.max_candidates += 1;
elements['benchmark-data'].textContent = JSON.stringify([...originalReports, mismatch, budgetMismatch]);
elements.filter.value = 'all'; elements.sort.value = 'saved';
const document = { getElementById: id => { assert.ok(elements[id], 'Missing element ' + id); return elements[id]; }, createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag) };
const source = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const context = vm.createContext({ document, window: { addEventListener() {} }, console });
vm.runInContext(source, context);
const reports = JSON.parse(elements['benchmark-data'].textContent);
assert.ok(reports.length >= 2, 'Need two runs to exercise run switching');
assert.equal(elements['stats'].children.length, 4);
assert.ok(elements['method-table'].children.length > 0);
assert.ok(elements['seed-table'].children.length > 0);
assert.ok(elements['method-chart'].children.length > 0);
const latest = [...reports].sort((a,b) => b.created_at.localeCompare(a.created_at))[0];
assert.equal(elements['puzzle-table'].children.length, latest.puzzles.length);
const candidate = latest.summaries.find(s => s.method === 'greedy' && s.seed === 2026) || latest.summaries[0];
assert.ok(elements['stats'].textContent.includes(Number(candidate.total_steps).toLocaleString('en-US')),
  `Selected ${elements['candidate-method'].value}; stats: ${elements['stats'].textContent}`);
elements.search.value = latest.puzzles[0].id;
elements.search.handlers.input();
assert.equal(elements['puzzle-table'].children.length, 1);
elements.search.value = ''; elements.filter.value = 'win'; elements.filter.handlers.input();
assert.ok(elements['puzzle-table'].children.every(row => Number(row.children[3].textContent.replaceAll(',', '')) > 0));
elements['reference-run'].value = elements['reference-run'].options[1].value;
elements['reference-run'].handlers.change();
assert.ok(!elements['comparison-status'].textContent.includes('Direct comparison is disabled'));
elements['reference-run'].value = 'budget-test'; elements['reference-run'].handlers.change();
assert.ok(elements['comparison-status'].textContent.includes('Search budgets'));
const alternate = elements['candidate-method'].options.find(option => option.value !== elements['candidate-method'].value);
assert.ok(alternate, 'Need multiple methods or seeds to exercise method switching');
elements['candidate-method'].value = alternate.value; elements['candidate-method'].handlers.change();
assert.ok(elements['method-table'].children.length > 0);
elements['reference-run'].value = 'incompatible-test'; elements['reference-run'].handlers.change();
assert.ok(elements['comparison-status'].textContent.includes('Direct comparison is disabled'));
assert.equal(elements['puzzle-table'].children.length, 0);
console.log('Dashboard scripts passed: initial render, scores, search, wins filter, cross-run comparison, method switching, and dataset mismatch protection.');
