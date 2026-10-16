// S6 spike: generate + verify a Semaphore proof with LOCAL artifacts only (no network).
const path = require('path');
const http = require('http');
const https = require('https');
const net = require('net');

// Network tripwire: any fetch/http/https/net connection attempt is logged and aborted.
let netAttempts = 0;
function trip(what, arg) {
  netAttempts++;
  console.log('NETWORK ATTEMPT BLOCKED:', what, String(arg && (arg.href || arg.host || arg.hostname || arg)).slice(0, 120));
  throw new Error('network blocked by spike tripwire: ' + what);
}
globalThis.fetch = (u) => trip('fetch', u);
http.request = (o) => trip('http.request', o);
http.get = (o) => trip('http.get', o);
https.request = (o) => trip('https.request', o);
https.get = (o) => trip('https.get', o);
net.connect = (o) => trip('net.connect', o);
net.Socket.prototype.connect = function (o) { return trip('net.Socket.connect', o); };

const { Identity, Group, generateProof, verifyProof } = require('@semaphore-protocol/core');
const snarkjs = JSON.parse(require('fs').readFileSync(path.resolve(__dirname, 'node_modules/snarkjs/package.json')));

const depth = Number(process.argv[2]);
const dir = path.resolve(__dirname, '../deps/artifacts/unpacked/package');
const artifacts = {
  wasm: path.join(dir, `semaphore-${depth}.wasm`),
  zkey: path.join(dir, `semaphore-${depth}.zkey`),
};

(async () => {
  console.log('snarkjs', snarkjs.version, '| depth', depth);
  console.log('wasm', artifacts.wasm);
  console.log('zkey', artifacts.zkey);
  const id = new Identity('spike-secret-S6-test-identity-1'); // TEST identity
  const other = new Identity('spike-secret-S6-test-identity-2');
  const group = new Group([id.commitment, other.commitment]);
  const message = 'hello-S6';
  const scope = 'scope-S6';

  const t0 = performance.now();
  const proof = await generateProof(id, group, message, scope, depth, artifacts);
  const t1 = performance.now();
  const ok = await verifyProof(proof);
  const t2 = performance.now();
  // negative control: tampered message must fail
  let bad;
  try { bad = await verifyProof({ ...proof, message: '12345' }); } catch (e) { bad = 'threw: ' + e.message; }
  console.log('merkleTreeDepth', proof.merkleTreeDepth, 'root', proof.merkleTreeRoot.slice(0, 20) + '...');
  console.log('nullifier', proof.nullifier.slice(0, 20) + '...');
  console.log('generateProof_ms', (t1 - t0).toFixed(0));
  console.log('verifyProof_ms', (t2 - t1).toFixed(0));
  console.log('verify_result', ok);
  console.log('tampered_verify_result', bad);
  console.log('network_attempts', netAttempts);
  const rss = process.memoryUsage();
  console.log('rss_at_end_MB', (rss.rss / 1048576).toFixed(0));
  process.exit(ok === true && netAttempts === 0 ? 0 : 1);
})().catch((e) => { console.log('ERROR', e && e.stack || e); process.exit(2); });
