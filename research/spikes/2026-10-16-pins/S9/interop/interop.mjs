// S3 interop: ohttp-ts 0.6.1 + panva hpke 1.1.7 <-> Rust ohttp 0.8.0 (via files).
// usage: node interop.mjs <rust-interop-binary> <plain|chunked> <dir1|dir2>
import { spawn, execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import {
  CipherSuite,
  KEM_DHKEM_X25519_HKDF_SHA256,
  KDF_HKDF_SHA256,
  AEAD_ChaCha20Poly1305,
} from "hpke";
import {
  KeyConfig,
  OHTTPClient,
  OHTTPServer,
  ChunkedOHTTPClient,
  ChunkedOHTTPServer,
  MediaType,
} from "ohttp-ts";

const [bin, mode, dir] = process.argv.slice(2);
const chunked = mode === "chunked";
const work = new URL(`./data-${mode}-${dir}/`, import.meta.url).pathname;
rmSync(work, { recursive: true, force: true });
mkdirSync(work, { recursive: true });
const hex = (b) => Buffer.from(b).toString("hex");
const suite = new CipherSuite(KEM_DHKEM_X25519_HKDF_SHA256, KDF_HKDF_SHA256, AEAD_ChaCha20Poly1305);
console.log(`node ${process.version} mode=${mode} dir=${dir} suite AEAD=${suite.AEAD.name} id=0x${suite.AEAD.id.toString(16)} (from panva hpke)`);

async function bodyBytes(init) {
  return new Uint8Array(await new Response(init.body).arrayBuffer());
}

if (dir === "dir1") {
  // Rust server KeyConfig -> ohttp-ts client -> Rust server -> ohttp-ts client.
  const cfgPath = work + "config.bin";
  console.log(execFileSync(bin, ["server-config", cfgPath]).toString().trim());
  const keyConfig = KeyConfig.parse(new Uint8Array(readFileSync(cfgPath)));
  const client = chunked ? new ChunkedOHTTPClient(suite, keyConfig) : new OHTTPClient(suite, keyConfig);
  const inner = new Request("https://gateway.example/v1/infer", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ prompt: "hello from ohttp-ts" }),
  });
  const { init, context } = await client.encapsulateRequest(inner);
  const reqBytes = await bodyBytes(init);
  writeFileSync(work + "req.bin", reqBytes);
  console.log(`ohttp-ts client wrote ${reqBytes.length}B request, header=${hex(reqBytes.subarray(0, 7))}`);
  console.log(execFileSync(bin, ["server", mode, work + "req.bin", work + "resp.bin"]).toString().trim());
  const respBytes = new Uint8Array(readFileSync(work + "resp.bin"));
  const outer = new Response(respBytes, {
    headers: { "content-type": chunked ? MediaType.CHUNKED_RESPONSE : MediaType.RESPONSE },
  });
  const res = await context.decapsulateResponse(outer);
  const text = await res.text();
  console.log(`ohttp-ts client decapsulated: status=${res.status} body=${JSON.stringify(text)}`);
  if (res.status !== 200 || text !== "hello from rust gateway") throw new Error("mismatch");
  console.log(`INTEROP ${mode} dir1 PASS`);
} else {
  // ohttp-ts server KeyConfig -> Rust client -> ohttp-ts server -> Rust client.
  const keyConfig = await KeyConfig.generate(suite, 0x01);
  const cfgBytes = KeyConfig.serialize(keyConfig);
  writeFileSync(work + "config.bin", cfgBytes);
  console.log(`ohttp-ts server-config ${cfgBytes.length}B ${hex(cfgBytes)}`);
  const server = chunked ? new ChunkedOHTTPServer([keyConfig]) : new OHTTPServer([keyConfig]);
  const child = spawn(bin, ["client", mode, work + "config.bin", work + "req.bin", work + "resp.bin"]);
  let out = "";
  child.stdout.on("data", (d) => (out += d));
  child.stderr.on("data", (d) => (out += d));
  const exited = new Promise((r) => child.on("exit", (code, sig) => r({ code, sig })));
  for (let i = 0; i < 300 && !existsSync(work + "req.bin"); i++) await new Promise((r) => setTimeout(r, 100));
  await new Promise((r) => setTimeout(r, 200));
  const reqBytes = new Uint8Array(readFileSync(work + "req.bin"));
  const outerReq = new Request("https://gateway.example/ohttp", {
    method: "POST",
    headers: { "content-type": chunked ? MediaType.CHUNKED_REQUEST : MediaType.REQUEST },
    body: reqBytes,
  });
  const { request, context } = await server.decapsulateRequest(outerReq);
  const reqText = await request.text();
  console.log(`ohttp-ts server decapsulated: ${request.method} ${request.url} body=${JSON.stringify(reqText)}`);
  const resp = await context.encapsulateResponse(
    new Response("hello from ohttp-ts gateway", { status: 200, headers: { "content-type": "text/plain" } }),
  );
  const respBytes = new Uint8Array(await resp.arrayBuffer());
  writeFileSync(work + "resp.bin", respBytes);
  console.log(`ohttp-ts server wrote ${respBytes.length}B response`);
  const { code, sig } = await exited;
  console.log(out.trim());
  console.log(`rust client exit code=${code} signal=${sig}`);
  if (code !== 0 || !out.includes("hello from ohttp-ts gateway")) throw new Error("rust client failed");
  console.log(`INTEROP ${mode} dir2 PASS`);
}
