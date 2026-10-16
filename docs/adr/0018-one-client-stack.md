# ADR 0018: One client stack for web, desktop and mobile

**Status:** proposed

**Date:** 2026-10-15

**Deciders:** none seated; no adopting CIP yet

## Context

This record answers the owner's request 6: desktop and mobile apps on the same stack as the web client. It changes no contract, proof, voucher or wire format, so no adopting CIP is proposed; adoption would require a later Final CIP.

[ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) fixes the HPKE suite the client must speak, and [ADR 0013](0013-repositories-toolchains-ci-and-releases.md) places the client in `client/` of one code repository. The "SDK wallet, WASM HPKE and prover distribution" row of [CIP-0005](../cip/0005-phase-one-implementation.md) is Open: it asks for the wallet library and the local proving and distribution approach, and it pins artifacts by SHA-256. [docs/risk-register.md](../risk-register.md) RR-50 records the GPL-3.0 and LGPL-3.0 questions on the prover, verifier-generation and compiler path. The dapp document's open question 4 ([docs/product/dapp-and-sdk.md](../product/dapp-and-sdk.md)) asks whether the SDK ships a WASM HPKE build and a native or WASM Groth16 prover, and how the reference client is distributed without a project-run server.

The external facts this record relies on are the "Client UX research 2026-10-15" blocks of [docs/evidence-register.md](../evidence-register.md) and the §8 recheck of 2026-10-15, cited with the mark of the clause used; no [L] or [U] is upgraded, and no licence or store fact is read as a legal conclusion.

## Decision

### (1) One stack

The client is a TypeScript UI over a Rust core, and the Rust core reuses the node's `hpke`, `ohttp` and `bhttp` crates so that the client and the node share one implementation of [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md). The web build compiles the core to WASM. Desktop and mobile wrap the same UI and the same core in a native shell.

**Native-shell candidate, not selected: Tauri 2.** Its README lists iOS and Android beside Windows, macOS and Linux (evidence register §4, client UX research 2026-10-15, [V]); it uses WebView2 on Windows, WKWebView on macOS and, in its webview layer, on iOS, and the device's system WebView on Android, shipping none of its own (evidence register §4, client UX research 2026-10-15, [V]); webview code reaches the system only through the IPC layer, capabilities grant permissions per window or webview with a `platforms` array, and on Linux and Android Tauri cannot distinguish an embedded iframe from the window itself (evidence register §4, client UX research 2026-10-15, [V]); Rust is called through typed commands (evidence register §4, client UX research 2026-10-15, [V]), and that this is how the HPKE and OHTTP crates would be reused is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]). The code is MIT, or MIT/Apache-2.0 where the README says so, with LICENSE-MIT and LICENSE_APACHE-2.0 in the repository, and wry is Apache-2.0/MIT (evidence register §8, client UX research 2026-10-15, [V]). If Tauri is chosen, 2.11.1 is the observed patched floor: its release notes fix the local-origin check on Windows and Android, and GHSA-7gmj-67g7-phm9 lists 2.11.1 as patched, while the CVE-2026-42184 record contradicts itself on the fixed version (evidence register §4, client UX research 2026-10-15, [V]). That floor is an observation dated 2026-10-15, not a CIP-0005 pin. The October 2024 statement that "We are not completely happy about the developer experience at the moment" on mobile has no later official statement (evidence register §4, client UX research 2026-10-15, [V] for the statement, [U] for the absence), and no Tauri web target was found (evidence register §4, client UX research 2026-10-15, [U]). Tauri's security documentation says plugin and core code "has full system access and is not constrained" (evidence register §4, client UX research 2026-10-15, [V]); the shell is therefore trusted code under the same review as the core.

**Recorded alternative: React Native or Expo with UniFFI.** React Native and Expo are MIT and UniFFI and uniffi-bindgen-react-native are MPL-2.0 (evidence register §8, client UX research 2026-10-15, [V]); uniffi-bindgen-react-native's own documentation says it "should not yet be used in production" (evidence register §4, client UX research 2026-10-15, [V]), and no Expo-specific UniFFI guide was found (evidence register §4, client UX research 2026-10-15, [U]).

**Structure.** Portable logic is separated from the wallet, secure-storage, passkey and lifecycle adapters, so a shell change touches adapters only. Remote provider content gets no vault or prover capability, which is the isolation rule of [ADR 0017](0017-accounts-and-decentralized-access.md) applied to the native capability sets. The shell, a provider webview and a store listing are never in the spend path; signing and proving remain in the client core, and the existing node and relay protocol roles remain unchanged.

### (2) The passkey-in-app gap

Native passkeys stay gated by per-platform demonstration; the core path uses an external wallet. The recorded facts:

- Apple requires an associated domain with the `webcredentials` service type and documents passkeys in WKWebView for a relying party that is an associated domain of the app (evidence register §4, client UX research 2026-10-15, [V]); Tauri documentation on adding that entitlement was not found (evidence register §4, client UX research 2026-10-15, [U]);
- Android WebView supports passkeys through Credential Manager only when the app opts in with `setWebAuthenticationSupport()` and sets up Digital Asset Links, the sample adds `credentials-play-services-auth`, and conditional mediation is unsupported (evidence register §4, client UX research 2026-10-15, [V]);
- Tauri's biometric plugin prompts for biometrics and is not WebAuthn, a maintainer calls the authenticator plugin "basically broken", issue 7926 is open with a later Android 16 success report whose accuracy is unresolved (evidence register §4, client UX research 2026-10-15, [V] for what the pages say, [L] for the reports), and the community plugin marks macOS and iOS unsupported (evidence register §4, client UX research 2026-10-15, [V]);
- whether a frontend served from a bundled custom scheme can run WebAuthn for an associated-domain relying party was not found (evidence register §4, client UX research 2026-10-15, [U]).

### (3) Prover candidates, none selected

- The current path: `@semaphore-protocol/proof` on snarkjs, whose npm license field is GPL-3.0 (evidence register §8, recheck 2026-10-15, [V]).
- `semaphore-protocol/semaphore-rs`, MIT, which depends on mopro's `circom-prover` (evidence register §8 and §15, client UX research 2026-10-15, [V]); `circom-prover` is "MIT OR Apache-2.0" with `arkworks` and `rustwitness` as default features (evidence register §8 and §15, client UX research 2026-10-15, [V]); that Semaphore v4 is therefore provable through arkworks is a researcher inference (evidence register §15, client UX research 2026-10-15, [L]); ark-groth16 is Apache-2.0 or MIT and its README says "NOT ready for production use" (evidence register §8, client UX research 2026-10-15, [V]), a warning that attaches to ark-groth16 only.
- `worldcoin/semaphore-rs`, MIT (evidence register §8, client UX research 2026-10-15, [V]); it names no Semaphore version, so v4 compatibility is unknown (evidence register §15, client UX research 2026-10-15, [U]).
- rapidsnark, whose COPYING is LGPL-3.0 (evidence register §8, client UX research 2026-10-15, [V]); that linking it has licence consequences is a researcher inference (evidence register §8, client UX research 2026-10-15, [L]).
- mopro, "Apache-2.0 or MIT" (evidence register §8, client UX research 2026-10-15, [V]); licences for zkmopro/rust-rapidsnark, SemaphoreReactNative and semaphore-bindings were not shown (evidence register §8, client UX research 2026-10-15, [U]); audits of semaphore-rs, circom-prover and mopro were not found (evidence register §8, client UX research 2026-10-15, [U]).

Before any choice, a candidate must show: an identical accepted circuit, identical artifacts, identical public-input and proof encoding, browser and native interoperability on the same proof, local-only proving, and measured memory and latency. A permissive native candidate does not close RR-50, which covers the whole path. Changing circuits or verifier semantics would need a CIP; SHA-256 artifact pinning stays exactly as CIP-0005 states.

### (4) App stores: facts and open questions, no legal conclusion

Recorded from the register's §16 block as facts, not as advice and not as a classification of Comuns:

- Apple 3.1.5 allows wallets only from developers enrolled as an organization, bans on-device mining and allows cryptocurrency transactions only on an approved exchange where licensed (evidence register §16, client UX research 2026-10-15, [V]);
- Apple 3.1.1 bans unlocking content or functionality with cryptocurrencies and cryptocurrency wallets (evidence register §16, client UX research 2026-10-15, [V]); whether that reaches paying for inference with notes inside an iOS app is an open reading (evidence register §16, client UX research 2026-10-15, [U]);
- Apple 2.5.2 bans downloading code that introduces or changes features (evidence register §16, client UX research 2026-10-15, [V]); whether that covers downloaded zkey or witness artifacts is an open reading (evidence register §16, client UX research 2026-10-15, [U]);
- Apple 5.1.1(ix) requires a legal entity for regulated services including crypto exchanges (evidence register §16, client UX research 2026-10-15, [V]);
- in the EU, notarization is a baseline review on every channel, including alternative marketplaces and web distribution, with eligibility bars and a commission on paid digital sales (evidence register §16, client UX research 2026-10-15, [V]); whether 3.1.5 applies to notarized apps rests on a missing marker and is a researcher inference (evidence register §16, client UX research 2026-10-15, [L]);
- Google Play's payments policy requires Play Billing for in-app digital transactions and no crypto exception was found (evidence register §16, client UX research 2026-10-15, [V] and [U]); non-custodial wallets are out of scope of its exchange-and-wallet policy (evidence register §16, client UX research 2026-10-15, [V]); whether the organization-account rule covers a non-custodial wallet is an open reading (evidence register §16, client UX research 2026-10-15, [U]);
- F-Droid rebuilds FLOSS apps from source and rejects apps that need Play Services (evidence register §16, client UX research 2026-10-15, [V]); that the Android WebView passkey sample's Play Services dependency conflicts with that is a researcher inference (evidence register §16, client UX research 2026-10-15, [L]).

Store distribution is a convenience. The verified web client and the local run of [ADR 0017](0017-accounts-and-decentralized-access.md) survive a rejected or removed listing, and a store listing is never in the spend path.

**Answer to the dapp document's open question 4.** The SDK ships the Rust core as WASM for the web and as a native library for the shells; the prover is a candidate list under (3); and distribution without a project-run server is ADR 0017 (5).

## Alternatives considered

### A web-only client

Rejected. The owner asked for desktop and mobile, and a web-only client leaves every native secure-storage and lifecycle adapter unbuilt. The web build remains the core path and the survival channel of (4).

### Separate native codebases per platform

Rejected. Three implementations of the HPKE, OHTTP and proof path would triple the surface that [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) and CIP-0005 must review, and would drift from the node's crates.

### A project-hosted web app, RPC or bundler

Rejected. It would seat a required hosted service, which [ADR 0017](0017-accounts-and-decentralized-access.md) (1) forbids on the core path.

### Electron or a bundled Chromium

Deferred. The evidence register does not establish this alternative's platform coverage or security floor, so it cannot yet be evaluated against the one-stack requirement.

### React Native as the single stack

Deferred, not rejected. It is the recorded alternative in (1); its Rust bridge "should not yet be used in production" by its own documentation (evidence register §4, client UX research 2026-10-15, [V]), and a web build would need a separate path.

### Selecting a prover now

Deferred. The interoperability and measurement conditions in (3) have not been met for any candidate, and the licence questions are RR-50 items.

### Requiring a store install

Rejected. The store rules in (4) are open readings, a listing can be removed, and the verified web client must remain sufficient.

## Consequences

- No CIP: no circuit, verifier, contract or wire change is proposed.
- The risk register gains RR-58 (dependency licences across the shell, wallet, validator and prover candidates) and RR-59 (app-store removal), with surface-scoped gates so that a store or vendoring gate never blocks the core path or protocol code; RR-50 stays open and gains the prover facts.
- The dapp document gains R13 (a hosted convenience or store listing treated as required) and its open question 4 takes the answer in (4).
- The CIP-0005 distribution row references this record and selects nothing; its pinning sentences are unchanged.
- No shell, prover, store or version is selected or adopted; 2.11.1 is an observed floor, not a pin.

## Links

- [docs/evidence-register.md](../evidence-register.md) §4, §8, §15, §16 (client UX research 2026-10-15), §8 (recheck 2026-10-15), §17
- [docs/product/dapp-and-sdk.md](../product/dapp-and-sdk.md)
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0013](0013-repositories-toolchains-ci-and-releases.md)
- [ADR 0016](0016-funding-edge-and-deposit-key.md)
- [ADR 0017](0017-accounts-and-decentralized-access.md)
- [CIP-0005](../cip/0005-phase-one-implementation.md)
- [docs/risk-register.md](../risk-register.md)
- [docs/architecture/system-architecture.md](../architecture/system-architecture.md)
