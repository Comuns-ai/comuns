# Phase 1 pins: verification spikes (2026-10-16)

## Purpose

These throwaway spikes checked the Phase 1 toolchain, cryptography and library pins before they were recorded in CIP-0005. Each spike installs or builds the exact versions in question, runs a small program, and keeps the log. The results are project measurements, not upstream claims. In the evidence register they carry these marks: [V] observed in the recorded log here, for the exact versions recorded; [L] inferred from such a log; [U] not run.

Date: 2026-10-16.

## Environment

- macOS, arm64.
- Rust 1.99.1 (`cargo +1.99.1 ...`).
- Node 24.22.0, checked against the published SHASUMS256.
- Foundry 1.8.5, sha256 verified.
- Other versions are recorded in each spike's `result.md` and `log.txt`.

Paths in the scripts and logs were rewritten: `$SPIKE` stands for the scratch directory the spikes ran in, and `$HOME` for the home directory. The scripts expect tool installs under `$SPIKE/tools/` (Node, Foundry) and `$SPIKE/<id>/deps/` (pnpm, wasm-bindgen-cli); adjust the paths to your own layout.

## Layout and how to reproduce

Each directory has a `result.md` (the findings, with log line references), a `log.txt` (every command and its full output), and the sources and lockfiles the spike used. Run the commands from the log (`grep '^\$ ' <id>/log.txt`). The `step*.sh` and `run.sh` files are the wrappers that produced the logs.

| Spike | What it checks | Reproduce |
|---|---|---|
| S1 | wasm32 crypto core: HPKE and OHTTP round trips natively, in WASM under Node and in a browser; feature graph; chunked-revision comparison; interop with ohttp-ts 0.6.1 | In `S1/crate`: `cargo +1.99.1 build`, `cargo +1.99.1 test -- --nocapture --test-threads=1`, `cargo +1.99.1 build --target wasm32-unknown-unknown --release`. Then, from `S1`: `wasm-bindgen --target nodejs --out-dir pkg-node crate/target/wasm32-unknown-unknown/release/comuns_crypto_spike.wasm` (wasm-bindgen 0.2.129) and `node node-run.cjs raw`. Interop: `npm install --ignore-scripts` in `S1/interop`, `cargo build --bin interop`, then `node interop.mjs ../crate/target/debug/interop plain dir1` (also `plain dir2`, `chunked dir1`, `chunked dir2`). Feature graph: `cargo tree -e features --target all`. Browser leg: serve `S1/web/` over http on 127.0.0.1 (the generated `.wasm` is not kept; rebuild from `S1` with `wasm-bindgen --target web --out-dir web crate/target/wasm32-unknown-unknown/release/comuns_crypto_spike.wasm`); the transcript is `S1/browser-leg.txt`. |
| S4 | TypeScript 7.0.2 with pnpm 12.14.0, ESLint, typescript-eslint and prettier; the lint project that aliases `typescript` to `@typescript/typescript6` | Run `step1.sh` to `step4.sh` in order. They install pnpm 12.14.0 and the dependencies, then run `tsc --strict --noEmit`, `eslint`, and `prettier --check`; the lint project is `S4/lint6`. |
| S5 | Foundry 1.8.5, solc 0.8.37, `cancun` against `osaka`, contract sizes; Semaphore 4.14.3 artifacts and a local proof | `S5/step1.sh` to `step11.sh` through `run.sh`. Contracts: `forge build --sizes` and `FOUNDRY_PROFILE=osaka forge build --sizes`, compared from `S5` with `node cmp.js .`. Proof: `node proof/prove.js 1` and `node proof/prove.js 32`. The artifacts tarball is `npm pack @zk-kit/semaphore-artifacts@4.13.0`; its 100 file hashes are in `artifacts-sha256.txt`. |
| S7 | EIP-712 hashes and signatures: viem 2.57.7 against alloy 2.5.0 (`sol!` and dynamic `TypedData`) | `S7/step1.sh` to `step6.sh`: `node run.mjs` in `viem`, `cargo +1.99.1 build --release` in `alloy` and `alloy-min`, then run the binaries and compare with `viem-out.json`. |
| S7b | solc 0.8.37 on a struct field named `final` | `forge build` in `S7b` (the log shows Error 2314, reserved keyword). `doc-final-count.txt` is the count of affected documents. |
| S8 | Read-only lookups: the llama.cpp commit vendored by llama-cpp-sys-2, name availability, checksums | `bash S8/lookups.sh >> S8/log.txt 2>&1` (needs network). |
| S9 | The ohttp 0.8.0 patch and its proof | Unpack the ohttp 0.8.0 crate, apply `S9/ohttp-0.8.0-chunked-fixes.patch` (for example `patch -p1` from the unpacked directory, after checking the path prefixes in the patch header), and point `[patch.crates-io]` at it, as `S9/crate/Cargo.toml` does. Then `cargo +1.99.1 test --lib -- --nocapture --test-threads=1`, the wasm build, and the interop commands as in S1. See `step2.sh` and `step3.sh`. |

Test vectors under `S1/interop` and `S9/interop` (the `data-*` directories) are written by `interop.mjs` and are not kept.

## Results

| Spike | Result | Summary |
|---|---|---|
| S1 | Partial | RFC 9458 round trip with the fixed suite passes natively, in WASM under Node 24.22.0, and in a browser. Chunked with ChaCha20-Poly1305 fails in ohttp 0.8.0 (`range end index 32 out of range for slice of length 16`). The WASM build needs only `getrandom =0.4.3` with `wasm_js`. Size after wasm-bindgen: 512,196 B raw, 145,295 B gzip -9, with no wasm-opt. Interop with ohttp-ts 0.6.1: non-chunked passes both ways; chunked passes only from the Rust server. |
| S1 (feature graph) | Measured | hpke 0.14.1 ends up with aes, alloc, chacha, getrandom, hkdfsha2, mlkem, nistp, shake and x25519, because ohttp's `rust-hpke` feature enables them; nss, gecko, unsafe-print-secrets and app-svc are not in the graph. 114 crates. |
| S1 (chunked revision) | Partial | Three deviations from draft-08 were found: an undersized client response-nonce buffer (16 bytes where the fixed suite needs 32), treating a zero-length non-final chunk as end of stream, and letting the sender emit such a chunk. The comparison used draft-08; newer revisions were not checked. |
| S4 | Partial | `tsc` 7.0.2 strict type-checking works. typescript-eslint 8.71.2 refuses TypeScript 7.0, so the lint project aliases `typescript` to `@typescript/typescript6` 6.0.2 (resolving to TS 6.0.3); prettier passes. pnpm 12.14.0 added `eslint@10.13.0` to `minimumReleaseAgeExclude` on its own. |
| S5 | Pass | Foundry 1.8.5 defaults to `evm_version = "osaka"`. With solc 0.8.37, `cancun` and the optimizer at 200 runs, Semaphore 4.14.3 compiles; runtime sizes are under 24,576 B. `cancun` and `osaka` give identical code apart from the metadata hash. |
| S6 (in S5) | Pass | The @zk-kit/semaphore-artifacts 4.13.0 tarball sha1 is `efe54e9ae463f748198f3d769f846224310caad9` and it holds 100 files. A proof from local artifacts passes at depth 1 (217 ms) and depth 32 (458 ms), and a tampered message verifies false. |
| S7 | Pass for viem and alloy dynamic `TypedData`; fail for `sol!` | viem 2.57.7 and alloy 2.5.0 agree on the type hash, domain separator, struct and signing hashes and signatures for 3 vouchers. alloy's `sol!` rejects a field named `final`. |
| S7b | Fail (as measured) | solc 0.8.37 rejects `bool final` with Error 2314. |
| S8 | Pass | llama-cpp-sys-2 0.1.160 vendors llama.cpp `d81235049384534c167caea52b85a694f6103d14`; names and checksums are recorded in `S8/result.md`. |
| S9 | Pass | With the patch, the chunked fixed-suite round trip passes natively and in WASM under Node, the zero-length-chunk checks pass, and chunked interop with ohttp-ts passes in both directions. The patch is 1 file, 17 insertions, 7 deletions. |

## Residuals

- Chunked interop was tested with whole buffered messages, not real incremental HTTP streaming.
- EIP-712 was compared between viem and alloy only. Solidity hash and signature conformance, and negative tests with a wrong domain or a tampered field, were not run.
- On-chain proof verification and Arbitrum limits were not run: proofs were verified in JavaScript only.
- WASM size was not optimized. The hpke code that cannot be removed adds P-256, P-384, P-521, ML-KEM and X-Wing.
- llama.cpp was not built (cmake was not installed). Native proving was not tried.
- The patched ohttp crate's own `stream` tests could not be compiled from the published package (an unpublished path dev-dependency is missing); the 6 stream-module tests were not run there.
- Names can change at any moment, and the npm scope endpoints do not prove a scope can be claimed.
- Tool side effect: rustup updated itself from 1.28.2 to 1.29.1 while installing toolchain 1.99.1.

## The ohttp patch

ohttp 0.8.0 is carried with a small patch (`S9/ohttp-0.8.0-chunked-fixes.patch`, `src/stream.rs` only), applied through `[patch.crates-io]` until an upstream release fixes it. The patch sizes the client response-nonce buffer to max(Nn, Nk) and enforces the draft-08 rule on zero-length chunks. ohttp is published under "MIT OR Apache-2.0" (github.com/martinthomson/ohttp); the patch modifies its `src/stream.rs`, quotes a few lines of it as context, and is offered under the same licences.

Upstream report: <link to be added>

## Large artifacts are not committed

Build outputs (`target/`, `node_modules/`, `deps/`, `pkg-node/`), `.wasm` files, downloaded tarballs, test-vector binaries and the unpacked ohttp trees are not committed. `S5/artifacts-sha256.txt` holds the SHA-256 of all 100 files in the Semaphore artifacts package, so a fresh download can be checked. `S5/semaphore-*.hex` and `S5/verifier-*.hex` are the compiled runtime bytecodes used for the `cancun` and `osaka` comparison.

## Test key

Source files in `S7` use the publicly known Foundry/anvil test key #0 to produce signatures. It is a public test key; never use it for value.
