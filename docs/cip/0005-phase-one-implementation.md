# CIP 0005: Phase 1 implementation

Status: Draft
Type: protocol
Created: 2026-10-15
Requires: 0002, 0003

This CIP is Draft. It is not in Last Call and is not Final. It adopts nothing today, seats nobody and authorizes no implementation or deployment while its pre-code gates remain open. Adoption requires the public lifecycle in [GOVERNANCE.md](../../GOVERNANCE.md), with two reviews by two people other than the author covering the cryptography and contracts subjects under [CONTRIBUTING.md](../../CONTRIBUTING.md). Reviewers need not be maintainers.

## Abstract

This proposal defines the implementation work for the Phase 1 Arbitrum Sepolia slice. If Final, it adopts only [ADR 0013](../adr/0013-repositories-toolchains-ci-and-releases.md), [ADR 0014](../adr/0014-relay-authentication-to-gateways.md) and [ADR 0015](../adr/0015-node-key-possession.md): engineering and release rules, relay authentication, and client-checked node-key possession. It also resolves the contracts document's Q19 without changing the ABI. The completion matrix below carries the remaining decisions and evidence gates.

## Motivation

The [project plan](../project-plan.md) requires an implementation decision before Phase 1. The [node design](../node/node-design.md), [off-chain API](../protocol/off-chain-api.md), [contracts document](../protocol/contracts-and-settlement.md) and [SDK proposal](../product/dapp-and-sdk.md) defer concrete choices to that decision. The key-possession gap KI-3 is an implementation blocker, and a registered relay address alone does not authenticate a connection. A single implementation CIP makes those obligations reviewable before code and keeps deployment economics in a separate proposal.

## Specification

### Adoption and scope

If this CIP becomes Final, it adopts ADRs 0013, 0014 and 0015 only. It does **not** adopt ADRs 0001–0012, and it does not mark CIP-0001 or CIP-0002 Final. [CIP-0002](0002-anonymous-credits-relays-and-ownerless-contexts.md) and [CIP-0003](0003-bootstrap-first-maintainer-and-channels.md) must become Final independently before this CIP can become Final.

Phase 1 is the single-node, anonymous standard-mode credit path in project-plan: one Rust node, a relay with a distinct operator, the four contracts, and a minimal TypeScript reference client and SDK. It excludes context use, attested mode, verifiable mode, multi-node features and a wallet-funded session demo. The `context` crate is unused in this slice; required contract tests still cover the context ABI.

[CIP-0004](0004-sepolia-testnet-configuration.md) owns the testnet configuration and exact model registration item. Read every testnet number there; every such value is **testnet-only, non-normative**. This CIP restates no numeric configuration table and sets no economic parameter of its own. CIP-0004 is a reference, not a dependency of this CIP: it requires this CIP to be Final. ADR 0013 orders CIP-0005 Final, then code built and tested, then CIP-0004 Final, then deployment and setters immediately, followed by the deployment record, source pre-release and independent walkthrough. On Arbitrum Sepolia, GOVERNANCE.md section 7.1 applies; mainnet is unchanged.

### Code style

The following is the ADR 0013 style rule, stated here to satisfy CONTRIBUTING.md section 6. Solidity uses `forge fmt`, NatSpec on external functions, and `// SPDX-License-Identifier: Apache-2.0` as the first line. Rust uses rustfmt defaults, checked with `cargo fmt`, and clippy with warnings denied. TypeScript uses prettier defaults, eslint and strict `tsc`. No other per-file header is required. The code repository carries the Apache-2.0 `LICENSE` and the GOVERNANCE.md notice lines in its README: "Copyright 2026 Comuns contributors" and "Licensed under the Apache License, Version 2.0 (see LICENSE)". Vendored code retains upstream notices and terms, as [ADR 0006](../adr/0006-apache-2-0-and-dco.md) requires.

### Decisions without new contract identifiers

**Contracts Q19:** `setBands` overwrites each caller-supplied `initialized` bit with `true` before storage and before emitting `BandsSet`. Storage and the event therefore agree even when the caller supplied `false`. The function signature and event layout are unchanged. Tests must cover caller-supplied false bits as well as true bits and assert both stored and emitted values.

**Relay authentication:** ADR 0014 specifies the off-chain operator delegation and connection credential, the gateway's registry checks, the relay's validation of the gateway challenge, and a nonce bound to one TLS connection and consumed once. The relay resolves the gateway from its own registry view using the selected node operator; it does not accept a client-supplied destination URL. Authentication is per connection; client relay choice is per OHTTP exchange, while the spend fixes the fee relay. An unauthenticated connection receives nothing but the authentication challenge; the capability document, the key probe and job traffic are served only after the gateway has authenticated the relay. Phase 1 supports EOA relay operators; ERC-1271 and channel binding remain deferred and UNVERIFIED. No credential field is added to a contract.

**Key possession:** ADR 0015 specifies the anonymous `key_probe` before spending, through an authenticated relay. The capability document and `key_probe` carry no `sessionSigner`; session messages retain that signature requirement. The probe uses its own HPKE info and AAD, separate from job opens. The node reconstructs the tuple from its own identity and keys, and answers only after a successful open yielding exactly 32 bytes. The response carries the challenge, receipt public key, receipt-key signature and an HMAC-SHA256 under a secret exported from the probe's own HPKE context. The client verifies the MAC and signature before pinning a key or spending. This authenticates the response to the HPKE key holder even if an OHTTP key holder rewraps the probe. A valid OHTTP response supplies the separate OHTTP possession check, subject to the standards recheck below.

The client re-probes when keys in the latest `NodeRegistered` or `NodeUpdated` differ from its pinned keys; `keyringHashes` is not that trigger. Neither session-open event carries those keys. The probe mitigates key misattribution; T7's hostile-RPC mitigation is the client's own relay-tunnelled chain view, independent reads compared, and pinning. The in-flight key-swap question stays open. An attested quote must separately bind the same keys before that later mode is enabled. No X25519 or HPKE verification is added to the EVM, and an operator signature over public key bytes is not a possession proof.

### Completion matrix

Every open pre-code item below blocks this CIP's Final and the start of protocol code. The named working groups coordinate decisions and evidence, not private authority. Decisions and primary-source rechecks must be written into this CIP before Final; none is completed by this Draft. Where measurements require the implementation, the pre-code decision specifies the method and acceptance condition, and measured results remain release gates. Conformance tests cannot be waived by marking a decision complete. A substantive completion during Last Call returns the CIP to Review under GOVERNANCE.md.

| Item | Owner working group | Decision or evidence required | Blocks |
|---|---|---|---|
| Trait names | Node | Open: replace the node-design section 4 sketch with the selected backend trait names and boundary, retaining the first llama.cpp adapter. | Final and code until the interface decision is recorded; adapter conformance before release. |
| Memory-fit coefficients | Node | Open: state the measurement method, backend/build coverage, admission rule and acceptance condition replacing node-design section 5's illustrative coefficients; record measured coefficients and memory-fit evidence before advertising the model. | Method and admission decision before Final/code; measurements before release. |
| Receipt-key wire details | Cryptography, Protocol | ADR 0015 decides a separate secp256k1 receipt key, not derived from the HPKE key and bound by the response MAC. Open: the canonical encodings of (tuple, challenge) and of (tuple, challenge, receiptPublicKey, receiptSignature) under exporter context `comuns/key-probe/v1/response`, and the remaining wire details; publish shared node/client vectors. | Wire decisions before Final/code; vectors and negative cases before release. |
| Chain-client library | Node, Contracts | Open: choose a library and document EIP-712 hashing, secp256k1 signing/verification, Semaphore Groth16 preverification, event following with reorg handling, and delayed-inbox submission. Check the independent EIP-712 conformance path. | Selection and capability evidence before Final/code; conformance and simulated fallback before release. |
| Accepted `merkleTreeDepth` range | Contracts, Cryptography | Open: state the supported range against the actual circuit and verifier artifacts, consistent with the existing contracts specification, and require rejection of unsupported depths. Do not infer support from an unverified package. | Range and artifact decision before Final/code; boundary tests before release. |
| Operations runbook and gas limits | Node, Documentation | Open: specify ports, storage, driver/build recording, monitoring, upgrades, key compromise handling, spend admission and the method for selecting operator gas limits; measure submission and recovery costs and record deployment settings without secrets. | Runbook and policy before Final/code; measured limits and operational rehearsal before release. |
| Session-store settlement-finality policy | Node, Contracts | Open: choose and justify the confirmation/finality policy before deleting encrypted session state, including `commitKey`, the transcript chain and highest voucher. L2 settlement inclusion alone must not silently erase reorg recovery. | Policy before Final/code; restart and reorg tests before release. |
| SDK wallet, WASM HPKE and prover distribution | Applications, Cryptography | Open: select the wallet library and local proving/distribution approach; specify the WASM build of the node's HPKE implementation and reproducible distribution without a project-run server. Package name remains undecided under dapp-and-sdk OQ4. | Implementation/distribution decisions and package name before Final/code; shared vectors and client checks before release. |
| Padding buckets and token batching | Protocol, Cryptography, Applications | Unset: `paddingBuckets[]` and `tokenBatch` need measurements of byte and latency cost and residual traffic analysis under privacy section 12. This Draft chooses no sizes or defaults. | Measurement plan before Final/code; measured configuration and conformance before release. |
| `sessionId` derivation | Contracts, Protocol | Open: resolve contracts Q14 in this CIP without changing the function list, signatures or event layouts; no final derivation choice is set here. | Decision before Final/code; shared derivation vectors before release. |
| ERC-1271 relay operators and channel binding | Protocol, Cryptography | Deferred/UNVERIFIED: Phase 1 is EOA-only under ADR 0014. Record explicit rejection of unsupported operator credentials and leave extension design to a later CIP. | Rejection tests before Phase 1 release; later support blocked pending a separate reviewed decision. |
| Exact toolchain and dependency pins | Node, Contracts, Applications | Open: record exact Foundry/compiler, Rust, Node LTS, pnpm, TypeScript/tooling, HPKE, binding/backend, chain-client, OHTTP and prover/verifier dependencies here after rechecks. Require lockfiles and reproducible inputs; no `latest`. Evidence-register version snapshots are recheck inputs, not pins. | All exact pins before Final/code; lockfile and reproducible build checks before release. |
| Pre-code recheck: Stylus pause and EVM target | Contracts, Protocol | Open: recheck primary-source pause status and confirm the EVM target for RR-16, using evidence register §1 [V] as the dated starting point. Reopening would not itself change the proposed EVM target. | Final and any protocol code. |
| Pre-code recheck: chunked OHTTP | Protocol, Cryptography | Open: recheck primary-source publication status, chunked request support and interoperability for off-chain-api OQ3; record the supported exchange shape or the specified per-message fallback. Evidence register §15 [V] is a snapshot, not current confirmation. | Final and any protocol code; independent interop remains a release gate. |
| Pre-code recheck: Semaphore artifacts and licenses | Cryptography, Contracts | Open: verify primary-source ceremony provenance, circuit, proving/verifying-key match, verifier artifact hashes and their licenses. Evidence register §15 [L] leaves second-ceremony details unconfirmed; package and audit facts there [V] do not audit this wrapper. | Final and any protocol code; integration/conformance results before release. |
| Pre-code recheck: model and dependency licenses | Node, Documentation | Open: read primary-source license files for candidate model artifacts and selected dependencies, including paid-hosting conditions, upstream notices and the canonical project license. Evidence register §3 [V], §7 with each entry's own mark, and §8 [V/L] are starting points. No model is researched or selected by this Draft; CIP-0004 must complete its exact registration item before Last Call. | License evidence before Final and any protocol code; CIP-0004 model item before its Last Call. |
| Pre-code recheck: RFC 7748, RFC 9180 and RFC 9458 | Cryptography | Open: confirm from the primary standards the readings below used by ADRs 0014 and 0015, and record their effect on the probe and response authentication. Do not treat the hpke crate entry in evidence register §4 [V] as verification of these standards facts. | Final and any protocol code; probe/OHTTP conformance before release. |
| Q19 storage/event agreement | Contracts | Proposed resolution above: overwrite `initialized` with true before storage and emission, preserving the ABI. | Adoption through this CIP; storage/event regression tests before release. |
| Relay authentication and key possession | Protocol, Cryptography, Node | Proposed resolutions are ADRs 0014 and 0015. Implement their fail-closed checks and the negative cases below, with RR-48 and RR-49 evidence. | Adoption through this CIP and completion of pre-code wire/standards items; negative tests before release. |

### Standards readings to confirm

The following labels describe required confirmation in the fifth recheck, **not work already done**. Each reading is pending, and no RFC section number or current verification is claimed:

- Reading of RFC 7748: X25519 is a Diffie–Hellman function, with no signature scheme in the HPKE suite — **UNVERIFIED in the evidence register; confirmed in the CIP-0005 recheck** is required before Final.
- Reading of RFC 9458: it derives the response key from the request's HPKE context, so a valid OHTTP response shows that the responder decapsulated the request — **UNVERIFIED in the evidence register; confirmed in the CIP-0005 recheck** is required before Final.
- Reading of RFC 9180: it provides secret export, used by ADR 0015 for the probe-response MAC — **UNVERIFIED in the evidence register; confirmed in the CIP-0005 recheck** is required before Final.

### Release evidence

The code repository must pass ADR 0013's CI gates against the contracts document, including its 23-function list, signatures, event layouts and voucher type string. Cryptographic vectors and independent OHTTP interoperability follow [privacy and contexts](../security/privacy-and-contexts.md) section 12. These are implementation release gates, not claims that tests or code exist today.

The Phase 1 walkthrough and [risk register](../risk-register.md) gates remain required. The client shows the observed denomination-group size without adopting a minimum anonymity set or warning threshold (RR-39; evidence register §15 [U]). Deposit-to-spend and change-to-spend delays remain unset. Pre-release publication and the independent walkthrough follow the ordered ADR 0013 process; neither permits mainnet use.

## Rationale

One implementation CIP keeps the engineering decision and security prerequisites together while CIP-0004 owns deployment economics. ADR 0013's single proposed code repository supports shared conformance tests with the proposed one-maintainer bootstrap. The documentation repository remains the adoption record. Separate code repositories and alternative toolchains can be considered by a later CIP.

Overwriting `initialized` removes Q19's storage/event ambiguity without removing a field or changing a signature. Off-chain relay credentials and the pre-spend key probe preserve the contract ABI and address distinct checks: relay eligibility, possession of the node keys, and the client's independent chain view. Operator signatures over key bytes alone do not replace those checks. The standards readings remain subject to primary-source confirmation before code.

## Backwards compatibility

Nothing is deployed and there is no protocol implementation to migrate. The 23-function list, every function signature and every event layout in [ADR 0011](../adr/0011-anonymous-credits.md) and the contracts document are unchanged. Q19 changes the proposed handling of an existing bit only. ADRs 0014 and 0015 resolve the proposed relay-authentication and registration-PoP gaps with off-chain mechanisms; this CIP adopts no earlier ADR and cannot silently close their other open questions. Mainnet parameters and governance rules are unchanged.

## Security considerations

The design is unaudited and no reference implementation exists. [SECURITY.md](../../SECURITY.md), the [threat model](../security/threat-model.md) and the risk register govern reporting and release evidence. Private vulnerability reporting must be enabled and that action recorded by the seated maintainer before release; this Draft does not claim it is enabled. No report, test evidence or walkthrough may include real prompts, keys or seed phrases. An emergency action cannot seize escrow or expose prompts.

Relay-authentication negative tests must reject an unregistered or deregistering relay, the node's own operator, invalid or expired delegation/connection credentials, nonce replay and use on another TLS connection. The relay must reject a TLS origin, node operator or endpoint hash that differs from its own resolved registry record, a relayed challenge issued by another gateway, an expiry outside ADR 0014's bound, a wrong chainId or a wrong NodeRegistry address, closing with `gateway_challenge_mismatch`. The gateway binds the nonce to its issuing TLS connection and consumes it once; credential expiry is the delegation's `notAfter`. Capability and probe access must fail on an unauthenticated connection. ERC-1271 support is not inferred from an address.

Key-probe negative tests must cover wrong HPKE or OHTTP keys, altered tuples, failed opens, challenge lengths other than 32 bytes, replayed or mismatched challenges, invalid receipt signatures or response MACs, a probe rewrapped into another OHTTP request, and a substituted receipt key. They must show that no key is pinned and no note is spent on failure, and that a change in the latest registered keys triggers a new probe. The MAC check is essential: possession of an OHTTP key can permit rewrapping and is not possession of the inner HPKE key.

These cases are required by the RR-48 and RR-49 release gates. They do not close the in-flight key-swap question or eliminate collusion, timing correlation or operator access to standard-mode plaintext. The client's relay-tunnelled independent chain reads and pinning address hostile RPC state separately from possession.

## Economic considerations

The protocol fee is 0 and no treasury exists. There is no protocol token or coin vote; ARB balances confer no proposal or review rights. This CIP sets no economic parameter, price, bond, deadline, relay fee or execution timelock of its own. CIP-0004 owns the testnet-only, non-normative configuration and its governance exception; mainnet rules remain unchanged. No funding, bounty, grant or audit award is claimed.

## Reference implementation

None.

## Change log

None.

## Copyright

Copyright 2026 Comuns contributors

Licensed under the Apache License, Version 2.0 (see LICENSE)
