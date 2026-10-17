# S1: wasm32 crypto core, plus S2 (feature graph) and S3 (chunked revision and interop)

Crate: `$SR/S1/crate/` (`comuns-crypto-spike`, edition 2024, rust-version 1.99). Log: `$SR/S1/log.txt` (L = line number in it).
Fixed suite in every test: DHKEM(X25519, HKDF-SHA256) / HKDF-SHA256 / ChaCha20-Poly1305 (wire header `01 0020 0001 0003`).

## Results
| Check | Result | Measured value | Evidence (log.txt) |
|---|---|---|---|
| native build | PASS | `cargo +1.99.1 build` ok | L1-~70 "Finished `dev`"; later builds L1303, L1353 |
| native test (a) RFC 9458 round trip | PASS | cfg 41 B, enc req 144 B, enc resp 83 B; BHTTP request parsed by the server | L1310 `a: RFC9458 ok (cfg 41B, req 144B, resp 83B)` |
| native test (b) chunked round trip, fixed suite | **FAIL** | ohttp 0.8.0 panics in the stream **client** while reading the response nonce: `range end index 32 out of range for slice of length 16` at ohttp-0.8.0/src/stream.rs:775:31 | L291, L296, L1312, L1321; `test result: FAILED. 3 passed; 2 failed` L1333, exit=101 L1336 |
| (b) diagnostic with AES-128-GCM (not the fixed suite) | PASS | chunked req 164 B, resp 108 B, 3 frames + final; the first frame decrypts from a prefix (incremental); a missing final chunk is rejected | L1312 `diagnostic b[Aes128Gcm]: chunked ok` |
| clippy `-D warnings` | PASS | `clippy -- -D warnings` clean (L343-425). The final `--all-targets` run needed one fix to the spike's own interop bin (collapsible_if, L1415); clean after that | L1468-1471 exit=0 |
| wasm32 build | PASS (after config) | Without config: `getrandom 0.4.3` compile_error "wasm32/64-unknown-unknown are not supported by default; ... enable the "wasm_js" crate feature" (L702, exit=101 L716). Fix: `[target.'cfg(target_arch = "wasm32")'.dependencies] getrandom = { version = "=0.4.3", features = ["wasm_js"] }`. **No RUSTFLAGS and no `--cfg getrandom_backend` needed for 0.4.x** (README L731; `RUSTFLAGS=` empty, no .cargo/config.toml, L832-836; the exit=1 at L836 comes from `cat` of the absent config file, not from the build) | L832 "Finished `release`"; L1440 rebuild |
| Node wasm round trip (Node v24.22.0, `--target nodejs`) | PARTIAL | `roundtrip()` = `FAIL(b) a: RFC9458 ok ...; b[ChaCha20Poly1305]: not run under wasm guard ...; diagnostic b[Aes128Gcm]: chunked ok ...`. (a) PASS inside wasm. Fixed-suite (b) FAIL: `roundtrip_b_raw()` (unguarded) traps with `RuntimeError unreachable` | L1260, L1261 |
| web bundle generated | PASS (not browser-run) | `$SR/S1/web/` = index.html, comuns_crypto_spike.js, comuns_crypto_spike_bg.wasm, .d.ts files. **Serve the directory `$SR/S1/web/` over http and open `index.html`** (ES module, so `file://` will not work). Expected body/console: the same `FAIL(b) a: RFC9458 ok ...` string as in Node | L1263-1270 |
| wasm sizes | measured | cargo release output: raw 528,620 B / gzip -9 155,717 B. After wasm-bindgen (`_bg.wasm`): raw 512,196 B / gzip -9 145,295 B. Default release profile, no wasm-opt, no LTO or opt-level tuning | L1271-1272 |
| hpke features unified | measured | hpke 0.14.1 enabled: **aes, alloc, chacha, getrandom, hkdfsha2, mlkem, nistp, shake, x25519**. We ask only for alloc/x25519/chacha/getrandom. ohttp's `rust-hpke` dependency hard-codes `features = ["getrandom","x25519","nistp","mlkem","aes","chacha"]` (ohttp-0.8.0/Cargo.toml), which adds aes, nistp (P-256/384/521), mlkem (ml-kem, x-wing) and shake. Same on wasm32 | L1156-1206 (`hpke feature "..."` sort -u list); `cargo tree -e features -i hpke` ~L437-500 |
| nss / gecko / unsafe-print-secrets off | PASS | ohttp features in the graph: client, rust-hpke, server, stream only. A grep for `nss\|gecko\|unsafe-print-secrets\|app-svc\|bindgen v0.72\|mozbuild` over the full `--target all` feature tree (743 lines) found nothing | L1206 `grep-exit=1` |
| licence list | measured | 114 packages in resolve: MIT OR Apache-2.0 (66); Apache-2.0 OR MIT (32); MIT/Apache-2.0 (4: curve25519-dalek-derive, ff, group, hpke); **BSD-3-Clause (3: curve25519-dalek 5.0.0, subtle 2.6.1, x25519-dalek 3.0.0)**; MIT (3: slab, winnow 0.7.15, winnow 1.0.4); Unlicense OR MIT (2: byteorder, memchr); MIT OR Apache-2.0 OR BSD-1-Clause (fiat-crypto); MIT OR Apache-2.0 OR LGPL-2.1-or-later (r-efi); (MIT OR Apache-2.0) AND Unicode-3.0 (unicode-ident); NONE (the spike crate) | L1276-1296 |
| chunked revision matches -08 | PARTIAL | Labels, AAD, final-chunk indicator, KDF steps and nonce XOR all match. Three behaviour deviations, see below | source quotes below; L1324 |
| interop RFC 9458, both directions | PASS | Rust KeyConfig → ohttp-ts client → Rust decapsulate → Rust response → ohttp-ts decapsulate: `INTEROP plain dir1 PASS`. ohttp-ts KeyConfig → Rust client → ohttp-ts server → Rust client: `INTEROP plain dir2 PASS`. The BHTTP bodies also interoperate | L1364, L1376 |
| interop chunked | PARTIAL | dir1 (Rust **server** chunked → ohttp-ts chunked client) PASS (L1388). dir2 (ohttp-ts chunked server → Rust **client**) **FAIL**: Rust panics at stream.rs:775:31 `range end index 32 out of range for slice of length 16`, exit 101 (L1399, L1412). No fix is possible without patching ohttp, so it is recorded as FAIL | L1388, L1399, L1412 |

### S3 source vs draft-ietf-ohai-chunked-ohttp-08
Draft fetched from datatracker (html) and from the ietf.org archive (.txt, which is easier to cite by line), `deps/draft-08.*`. txt sha256 `c7fa23ec...c207`, L~1140.

| Item | ohttp 0.8.0 source | draft-08 (.txt line) | Match |
|---|---|---|---|
| request info label | stream.rs:24 `INFO_REQUEST: &[u8] = b"message/bhttp chunked request";` and lib.rs:76-86 `build_info` = label ‖ 0x00 ‖ key_id ‖ kem ‖ kdf ‖ aead | 420-422 `info = concat(encode_str("message/bhttp chunked request"), encode(1, 0), hdr)` | yes |
| response export label | stream.rs:26 `LABEL_RESPONSE: &[u8] = b"message/bhttp chunked response";` and lib.rs:232-233 export of `entropy` = max(Nn,Nk) bytes (lib.rs:228-229) | 466 `secret = context.Export("message/bhttp chunked response", entropy_len)` | yes |
| AAD | stream.rs:29 `CHUNK_AAD: &[u8] = b"";` stream.rs:30 `FINAL_CHUNK_AAD: &[u8] = b"final";` | 427, 433-436, 478, 486-490 (`Seal("final", chunk)`) | yes |
| final-chunk indicator | stream.rs:110-112 (`if last { (0, 0) }`, the length written is 0); QUIC varint stream.rs:50-61 | 437 `final_chunk = concat(varint_encode(0), sealed_final_chunk)`; 313-317 | yes |
| response key/nonce | lib.rs:236-248 `salt = enc ‖ nonce`, `hkdf.extract`, `expand_key(.. b"key" ..)`, `expand_data(.. b"nonce", n_n)` (INFO_KEY/INFO_NONCE lib.rs:64-65); server nonce `random(entropy)` stream.rs:606 | 460-470 | yes |
| per-chunk counter | rh/aead.rs:16 `COUNTER_LEN: usize = 8`, :105-110 XORs the u64 `seq` into the last 8 bytes of the 12-byte nonce; request side uses the HPKE context sequence | 472-484 `chunk_nonce = aead_nonce XOR encode(Nn, counter)` | equivalent for counter < 2^64 (the draft allows up to 256^Nn) |
| max chunk | stream.rs:28 `MAX_CHUNK_PLAINTEXT = 1 << 14`; the receiver rejects longer chunks with ChunkTooLarge (stream.rs:385-386) | 269-272 MUST support receiving 2^14; senders SHOULD limit | compatible (does not accept larger chunks) |
| **response nonce length (client)** | stream.rs:244 `nonce: [0; 16]`, :743 `nonce: [u8; 16]`, :775 `&mut nonce[..entropy(*this.config)]` | 345 `Response Nonce (8 * max(Nn, Nk))`; 457-460 | **DEVIATION (bug)**: the buffer is 16 bytes; ChaCha20-Poly1305 (and AES-256-GCM) need 32 → panic. Measured L1312, L1399 |
| **zero-length non-final chunk (receiver)** | stream.rs:409-425 `read_into_output` returns `Ok(pt.len())` = `Ok(0)` for an empty chunk, which callers treat as EOF (the `continue` guard at stream.rs:544-547 is only on the other path) | 405-408 receiver MUST treat it as equivalent to a decryption error | **DEVIATION**: measured `receiver result=Ok(3) plaintext="one"`. Data after the empty chunk ("two") and the final chunk are silently dropped with no error (L1324, AES diagnostic) |
| **zero-length non-final chunk (sender)** | `poll_write(&[])` → `write_chunk(.., &[], false)` stream.rs:160-161 | 405 MUST NOT send | **DEVIATION**: measured `sender wrote 0 pt bytes as a 17-byte framed chunk` (L1324). `write_all` never emits one, but a raw `write(&[])` does |

ohttp-ts 0.6.1 src/constants.ts uses the same labels ("message/bhttp chunked request"/"response"), `FINAL_CHUNK_AAD = "final"` and 16384-byte chunks, and cites draft-08.

## Exact versions resolved
From Cargo.lock / `--version`: rustc/cargo 1.99.1 (L1-3); hpke 0.14.1, ohttp 0.8.0, bhttp 0.8.0, chacha20poly1305 0.11.0, x25519-dalek 3.0.0, curve25519-dalek 5.0.0, futures 0.3.34, **getrandom 0.4.3** (the only getrandom in the crate graph; the getrandom 0.2.17 at L1040 belongs to the wasm-bindgen-cli build), wasm-bindgen 0.2.129, js-sys 0.3.106 (L1441-1466). wasm-bindgen-cli 0.2.129 (L1253 `wasm-bindgen 0.2.129`). Node v24.22.0, npm 11.19.1. npm: ohttp-ts 0.6.1, hpke 1.1.7, bhttp-ts 0.6.1, quicvarint 0.2.1 (`npm ls`, ~L1100).

Dependencies added beyond the packet:
- `futures =0.3.34` (default-features off, `std`), spike-only, to drive ohttp's AsyncRead/AsyncWrite stream API.
- `getrandom =0.4.3 [wasm_js]` for wasm32 only.

bhttp `stream` built with `default-features = false` and needed nothing extra. ohttp 0.8.0 does not depend on bhttp at all.

## Findings that affect a pin
1. **ohttp 0.8.0 chunked (stream) client cannot use the fixed suite.** It panics on every ChaCha20-Poly1305 (and AES-256-GCM) chunked response. Its 16-byte response-nonce buffer is too small for max(Nn,Nk)=32. The Rust gateway/server side of chunked works and interoperates with ohttp-ts. A Rust or wasm **client** of chunked responses on this pin is broken: natively it panics, in wasm it traps (`RuntimeError unreachable`). Non-chunked RFC 9458 is unaffected.
2. **ohttp 0.8.0 does not enforce draft-08 §6's zero-length-chunk rule.** Its reader returns a clean EOF at an empty non-final chunk, silently truncating the stream without verifying the "final" chunk. Its writer can emit such a chunk. Only a key holder (the gateway) can produce one, so this is a robustness/interop issue rather than an on-path forgery. Still, the truncation goes undetected.
3. **The hpke features cannot be narrowed through ohttp.** `rust-hpke` force-enables aes, nistp, mlkem (plus shake and hkdfsha2). P-256/384/521, ML-KEM and X-Wing code is therefore in the graph and in the wasm (~145 KB gzip after bindgen).
4. **getrandom resolved to 0.4.3, not 0.3.** The wasm32 opt-in is just the `wasm_js` feature, with no `getrandom_backend` rustflag.
5. **ohttp-ts gets ChaCha20-Poly1305 from panva `hpke` 1.1.7's `AEAD_ChaCha20Poly1305`, which uses WebCrypto.** Node 24.22.0 prints `ExperimentalWarning: The ChaCha20-Poly1305 Web Crypto API algorithm is an experimental feature` (L1357). Browsers generally do not ship WebCrypto ChaCha20-Poly1305. I'm not certain of current browser status; this was not verified here. ohttp-ts's own README points to `@panva/hpke-noble` for a non-WebCrypto ChaCha, which was not installed (not in the approved list).
6. The licence graph includes BSD-3-Clause (the dalek crates and subtle) and a few MIT-only crates. Facts only; no conclusion drawn.

## Residuals / not verified
- The browser leg was not run (orchestrator). Serve `$SR/S1/web/` and open `index.html`. The expected output string starts `FAIL(b) a: RFC9458 ok`.
- No patched or newer ohttp was tried. Whether a later ohttp release fixes the 16-byte nonce buffer was not checked.
- Draft -08 expired 22 Aug 2026 (txt L8). A newer revision or RFC may exist and was not checked.
- ohttp-ts adds BHTTP padding by default (requests ~1079 B). Rust bhttp accepted the padded messages; padding behaviour was not studied further.
- Chunked interop covered whole buffered messages through files, not real incremental streaming over HTTP.
- The wasm sizes are for the default release profile with no wasm-opt.
- The test packet's own `roundtrip()` output and the result of a `cargo test` that includes known-failing tests are documented above. `cargo test` exits 101 by design while (b) fails.
- One bookkeeping note: the log entry at L274 shows exit=0 for a test run whose output was piped through `tail`. The test run actually FAILED (L271).
