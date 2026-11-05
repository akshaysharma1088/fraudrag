// Builds an external payee-matching set from an independent descriptor generator:
// wnstnb/foliome scripts/generate-training-data.js (Apache-2.0), pinned commit below.
// We load that file's merchant pools and format functions (everything above its
// "const generators" block), seed Math.random, and pair each merchant's display name
// with descriptors produced by the generator's own formats. Nothing from that repository
// is vendored here; CI clones it at the pinned commit.
//
//   node external/foliome_pairs.js <path-to-generate-training-data.js> <out.jsonl>
const fs = require('fs');
const vm = require('vm');
const PINNED = 'a9a6d99e4cba4ac054e4ccbd7d3be7904ff053de';

function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

const [src, out] = process.argv.slice(2);
let code = fs.readFileSync(src, 'utf8');
code = code.slice(0, code.indexOf('const generators = {'));
const rnd = mulberry32(20261104);
const sandboxMath = Object.create(Math); sandboxMath.random = rnd;
const ctx = { require, process: { argv: [] }, __dirname: '.', console, Math: sandboxMath };
vm.createContext(ctx);
vm.runInContext(code + '\nthis.__x = { merchants, randomFormat, randInt, randDigits, fmt };', ctx);
const { merchants, randomFormat, randInt, randDigits, fmt } = ctx.__x;
const rand = arr => arr[Math.floor(rnd() * arr.length)];

// flatten pools: [{pool, name}]
const items = [];
for (const [cat, sub] of Object.entries(merchants)) {
  if (Array.isArray(sub)) { sub.forEach(n => items.push({ pool: cat, name: n })); continue; }
  for (const [k, arr] of Object.entries(sub)) if (Array.isArray(arr)) arr.forEach(n => items.push({ pool: `${cat}.${k}`, name: n }));
}
const seen = new Set(); const uniq = items.filter(x => typeof x.name === 'string' && !seen.has(x.name) && seen.add(x.name));
const title = s => s.toLowerCase().replace(/(^|[\s\-.&/])([a-z])/g, (m, p, c) => p + c.toUpperCase()).replace(/'S\b/g, "'s");
// the generator's own abbreviation rule (used for grocery chains): drop spaces/apostrophes, keep 7-10 chars, add a store number
const abbrev = m => fmt(`${m.replace(/[' ]/g, '').substring(0, randInt(7, 10)).toUpperCase()} #${randDigits(randInt(3, 5))}`);
const descriptor = m => (rnd() < 0.25 ? abbrev(m) : randomFormat(m, { isDebit: true }));

const rows = [];
for (const it of uniq) {
  const samePool = uniq.filter(x => x.pool === it.pool && x.name !== it.name);
  for (let k = 0; k < 2; k++) rows.push({ name: title(it.name), descriptor: descriptor(it.name), label: 1, pool: it.pool, kind: 'positive' });
  if (samePool.length) rows.push({ name: title(it.name), descriptor: descriptor(rand(samePool).name), label: 0, pool: it.pool, kind: 'same_pool' });
  rows.push({ name: title(it.name), descriptor: descriptor(rand(uniq.filter(x => x.pool !== it.pool)).name), label: 0, pool: it.pool, kind: 'random' });
}
fs.writeFileSync(out, rows.map(r => JSON.stringify({ ...r, source: `foliome@${PINNED.slice(0, 12)}` })).join('\n') + '\n');
console.log(`merchants ${uniq.length}, pairs ${rows.length}`);
