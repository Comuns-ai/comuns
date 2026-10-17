# S9: patch ohttp 0.8.0 chunked bugs and prove the fix

Directory: `$SR/S9/`. Log: `$SR/S9/log.txt` (L = line number, 378 lines). The suite in every test is X25519 / HKDF-SHA256 / ChaCha20-Poly1305 unless stated otherwise.

**Bookkeeping note.** In `run.sh`, `exit=` is the exit code of the last command in the pipeline.
- In step 2 (L62-238) that was a `grep` or `tail`, not cargo. Use the `test result:` lines as the evidence there.
- Step 3 (L239 on) used `set -o pipefail`.
- L245 `exit=1` comes from `ls .cargo` on the absent directory. It shows no `.cargo/config` exists. The wasm build itself finished (L240).

## Results
| Check | Result | Measured value | Evidence (log.txt) |
|---|---|---|---|
| Patched build (native) | PASS | ohttp resolves to the path `S9/ohttp-0.8.0-patched` through `[patch.crates-io]` | L51 "Finished `dev`"; L53-61 `cargo tree -i ohttp` / `pkgid` = `path+file://…/S9/ohttp-0.8.0-patched#ohttp@0.8.0` |
| (a) RFC 9458 round trip | PASS | cfg 41 B, req 144 B, resp 83 B | L67 |
| (b) fixed-suite ChaCha20-Poly1305 chunked round trip | **PASS** (was FAIL/panic in S1) | req 164 B, resp 124 B, 3 frames + final; first frame decrypts incrementally; truncation rejected | L73 |
| (c) zero-length non-final chunk injected into a response | PASS | Rejected on both read paths with `Error::Format` ("an error was found in the format") after plaintext "one": 1024 B buffer (`read_into_output`) and 8 B buffer (buffered path). The 106 B response is hand-built from the HPKE exporter secret. The positive control (same construction, no empty chunk) decrypts | L62-82; full string in L262 (wasm) and in the `test_all_summary` line |
| (c) negative control (ohttp with only the nonce fix) | FAIL as expected | `c: zero-length non-final chunk ACCEPTED (buf 1024): read ended cleanly with plaintext "one"`. This shows (c) detects bug 2 | L125-148 (L132) |
| (d) empty `write(&[])` emits no bytes | PASS | 4 empty writes (client request and gateway response, each before and after the first data write) returned Ok(0) and emitted 0 B; the stream still decrypts (89 B resp) | L62-82 |
| (d) negative control | FAIL as expected | `d: request mismatch`. Unpatched, the empty write emits a chunk, and the unpatched reader then truncates the request at it. S3 under the negative control: "wrote 0 pt bytes as a 17-byte framed chunk; receiver result=Ok(3) plaintext="one"" | L137, L139 |
| Spike `cargo test` overall | PASS | 7 passed, 0 failed. S3 diagnostic now: "0-byte framed chunk; receiver … Ok(6) "onetwo"" | L79, L82 |
| Patched crate's own tests, `stream` on | FAIL (could not compile; not caused by the patch) | `error[E0432]: unresolved import sync_async` in the `stream` test module. `sync-async` is an unpublished path dev-dependency (`../sync-async` in Cargo.toml.orig) that is absent from the crates.io package | L152-193 (L169) |
| Patched crate's own tests, `client,server,rust-hpke` | PASS | 30 passed, 0 failed (config, rh::aead/hkdf/hpke, RFC 9458 request/response incl. truncation, P-256, X-Wing). The 6 `stream` module tests (request_response, dribble_out, dribble_in, split_in, long_request, StutterDribble harness) were **NOT RUN** | L194-230 |
| clippy `--all-targets -D warnings` | PASS | clean | L97-99 |
| wasm32 build | PASS | `cargo build --target wasm32-unknown-unknown --release`. getrandom 0.4.3 `wasm_js` config from S1 unchanged; `RUSTFLAGS=` empty, no `.cargo/` | L239-245 |
| Node wasm (a), (b) ChaCha20-Poly1305, (c) (and (d)) | PASS | Node v24.22.0: `roundtrip(): PASS a: … ; b[ChaCha20Poly1305]: chunked ok …; c: zero-length non-final chunk rejected …; d: … emitted 0 B …`. Wasm guard removed; `roundtrip_b_raw(): PASS b[ChaCha20Poly1305]…` (S1: trap) | L254, L262, L263 |
| Web bundle | PASS (generated, not browser-run) | `$SR/S9/web/`: index.html, comuns_crypto_spike.js, _bg.wasm, .d.ts. Serve the directory over http and open `index.html`. Expected text starts `PASS a: RFC9458 ok` | L265-277 |
| wasm sizes | measured | cargo release: 578,675 B raw / 171,045 B gzip -9. After wasm-bindgen `_bg.wasm`: 560,900 B / 156,385 B. S1 was 512,196 / 145,295 after bindgen; the growth is the spike's (c)/(d) code plus direct hkdf/sha2/chacha20poly1305 use in test (c) | L272-275 |
| Interop plain dir1 (Rust gateway ↔ ohttp-ts client) | PASS | `INTEROP plain dir1 PASS` | L306 |
| Interop plain dir2 (ohttp-ts gateway ↔ Rust client) | PASS | `INTEROP plain dir2 PASS` | L319 |
| Interop chunked dir1 | PASS | `INTEROP chunked dir1 PASS` (Rust server wrote 137 B) | L332 |
| Interop chunked dir2 (ohttp-ts server → Rust client) | **PASS** (was FAIL/panic in S1) | Rust client wrote a 164 B chunked request; the ohttp-ts gateway wrote 1073 B; `rust client decapsulated (chunked): status=200 body="hello from ohttp-ts gateway"`, exit 0 | L345-346 |
| Diff size | measured | `ohttp-0.8.0-chunked-fixes.patch`: 1 file (src/stream.rs), **17 insertions, 7 deletions** (74-line unified diff) | L1-8 (L7) |

## Exact versions resolved
- rustc/cargo 1.99.1 (L9-11).
- From `crate/Cargo.lock`:
  - **ohttp 0.8.0** (path, patched), hpke 0.14.1, bhttp 0.8.0;
  - chacha20poly1305 0.11.0, hkdf 0.13.0, sha2 0.11.1;
  - futures 0.3.34, getrandom 0.4.3;
  - wasm-bindgen 0.2.129, js-sys 0.3.106 (L348-378).
- Tools:
  - wasm-bindgen-cli 0.2.129, installed with `--locked --root $SR/S9/deps` (L251, L255);
  - Node v24.22.0, npm 11.19.1.
- npm (`npm ci --ignore-scripts` from S1's lockfile): ohttp-ts 0.6.1, hpke 1.1.7, bhttp-ts 0.6.1, quicvarint 0.2.1 (L281-295).
- The self-test copy used ohttp's own packaged `Cargo.lock`. Cargo downloaded several older versions into the normal cargo cache for it: hpke 0.14.0, aes-gcm 0.11.0, polyval 0.7.2, rand 0.10.2, x-wing 0.1.0, aes 0.9.1, futures-util 0.3.32 and others (L152-168). Those downloads affect only that self-test run.

## Patch details (what changed in `src/stream.rs`)
1. `const MAX_ENTROPY: usize = 32;` (with a comment: the largest `max(Nn, Nk)` over the supported AEADs; AES-256-GCM and ChaCha20-Poly1305 have Nk = 32). It is used in both nonce buffers (orig :244 and :743). There is no API change.
2. **Reader.** The empty-plaintext check runs after successful AEAD open, so a forged chunk still fails as an AEAD error.
   - In `read_into_output`, an empty decrypted chunk returns `Error::Format`.
   - In the buffered path, `!last && pt.is_empty()` returns `Error::Format`, replacing the old `continue`.
   - **Variant choice:** the existing `Error::Format`. No variant was added, because `Error` is public and not `#[non_exhaustive]`.
3. **Writer.** `ChunkWriter::poll_write` with empty input returns `Ok(0)` before flushing or sealing anything. `WriteAfterClose` is still checked first.

## Findings that affect a pin
1. **The patch fixes all three bugs** at a cost of 17 insertions and 7 deletions in one file. With it, the Rust and wasm chunked client works with the fixed suite (ChaCha20-Poly1305), natively, in Node wasm, and against an ohttp-ts gateway. Pinning plain ohttp 0.8.0 for the chunked client is still broken. A chunked pin needs this patch through `[patch.crates-io]` (a path or git fork) until upstream ships a fix.
2. **Test (c) needs its own response builder.** With the patch, the writer can no longer produce a zero-length non-final chunk, so (c) builds the response by hand.
   - It uses hpke `setup_receiver`, the exporter, HKDF and ChaCha20-Poly1305, with the same crate versions ohttp already resolves.
   - So the spike crate now depends directly on chacha20poly1305 =0.11.0, hkdf =0.13.0 and sha2 =0.11.1. This adds no new crates to the graph.
   - If the product keeps this test, these direct dependencies come with it.
3. **The crate's `stream` tests cannot run from the crates.io package**, because the `sync-async` dev-dependency is unpublished. Running them would need the upstream git repository, which was not fetched (not approved).

## Residuals / not verified
- **Not run against the patch:**
  - ohttp's own 6 `stream` module tests (sync-async missing).
  - The browser leg. The orchestrator serves `$SR/S9/web/` and opens `index.html`.
  - AES-256-GCM chunked was not exercised, though it shares the 32-byte path.
- **Draft text not re-read:**
  - The draft-08 text was not re-read in S9; S1's `deps/` copy had been deleted. The §6 references (txt ~L405-408) come from the packet and S1 (sha256 c7fa23ec… in S1 log L1302). The upstream issue paraphrases them without quoting.
  - Whether a newer draft or RFC changes §6 was not checked.
- **Upstream not checked:**
  - Upstream `main` was not re-fetched. The "main still has 16-byte buffers" claim rests on `$SR/S1/stream-main.rs` (lines 244, 743; also 545 `continue` and 160 unguarded `poll_write`). The commit of that copy is not recorded in S9.
  - No existing upstream issue or PR covering these bugs was searched for.
- **Reader state after the error:** after the new `Error::Format`, the reader stays in its mid-chunk state, just as it does after an AEAD failure. Callers must stop reading after an error.
- **Upstream issue:** the draft at `$SR/S9/upstream-issue.md` was NOT posted. Its reproduction snippet is a sketch that was not compiled as written.
- **Cleanup:** `crate/target`, `negctl/` (negative-control crate and nonce-only ohttp copy, with target), `selftest/` (with target), `interop/node_modules` and `deps/` are left for the orchestrator to delete. `ohttp-0.8.0-orig/` and `ohttp-0.8.0-patched/` have no target dirs; the self-test ran in the `selftest/` copy so cargo could not touch the diffed tree.
- **Text addressed to an AI:** none was seen in any fetched content.
