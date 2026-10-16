const fs = require('fs');
const base = process.argv[2];
function load(dir, name, file) {
  const j = JSON.parse(fs.readFileSync(`${base}/contracts/${dir}/${file}/${name}.json`));
  return j.deployedBytecode.object.replace(/^0x/, '');
}
function strip(h) { // remove CBOR metadata: last 2 bytes give its length
  const n = parseInt(h.slice(-4), 16);
  return h.slice(0, h.length - (n + 2) * 2);
}
for (const [name, file] of [['SemaphoreVerifier', 'SemaphoreVerifier.sol'], ['Semaphore', 'Semaphore.sol']]) {
  const a = load('out', name, file), b = load('out-osaka', name, file);
  const sa = strip(a), sb = strip(b);
  let diffs = 0, first = -1;
  for (let i = 0; i < sa.length; i += 2) if (sa.slice(i, i + 2) !== sb.slice(i, i + 2)) { diffs++; if (first < 0) first = i / 2; }
  console.log(name, 'cancun bytes', a.length / 2, 'osaka bytes', b.length / 2,
    'full identical', a === b, '| metadata-stripped cancun', sa.length / 2, 'osaka', sb.length / 2,
    'stripped identical', sa === sb, 'differing bytes', diffs, 'first diff offset', first);
  console.log(' metadata cancun', a.slice(-100), '\n metadata osaka ', b.slice(-100));
}
