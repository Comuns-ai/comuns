# ADR 0017: Accounts, an independent note vault and decentralized access

**Status:** proposed

**Date:** 2026-10-15

**Deciders:** none seated; no adopting CIP yet

## Context

This record answers the owner's requests 4 and 5: an embedded wallet with social login through Google/Gmail or X, and a truly decentralized dapp with no required hosted backend. It changes no contract, proof, voucher or wire format, so no adopting CIP is proposed; adoption would require a later Final CIP.

Before this record, the documents drew a hard line. [docs/product/dapp-and-sdk.md](../product/dapp-and-sdk.md) said the wallet is the only account, with no email login, no password and no seed-phrase collection, and listed "no social login" among the things the client will not do. [docs/architecture/system-architecture.md](../architecture/system-architecture.md) says no part of the protocol requires a project-run service, and it said a wallet is the only on-chain account a user needs and appears in exactly one public step. The dapp document has the client never default to a project-run RPC endpoint, and forbids hosting prompts, contexts or answers on any project-run server. [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md) §5 makes the app-generated identity key the root of the vault, and it used the wallet key only for `depositNote`, `ragequit` and `withdraw`. This record and the edits that accompany it replace the account, login and signing sentences and keep the no-project-service rules. The dapp document's open question 1 asks how contract wallets are supported, and open question 4 asks how the reference client is distributed without a project-run server.

An embedded wallet with social login is a funding convenience that the line above did not anticipate. The question is not whether to replace the wallet-only rule but whether a convenience can sit beside it without reaching the vault, the session or the spend path. The external facts this record relies on are the "Client UX research 2026-10-15" blocks of [docs/evidence-register.md](../evidence-register.md), cited with the mark of the clause used; no [L] or [U] is upgraded.

## Decision

### (1) Two tiers

**The core path** always works with: a static client build reached by a verifying fetch or run locally (5); an RPC endpoint the user chooses (6); the user's own account holding ETH on Arbitrum One; and the permissionless relays and nodes. No project-run or hosted service is required, and the client never defaults to one.

**Conveniences** are optional, disclosed and replaceable, and are used only on the funding surface: social login (Google/Gmail, Apple, and X where a provider offers it), embedded wallets, on-ramps, intent orchestrators, gas sponsorship, indexers and public gateways. Each is never in the spend path. A session never has an account: `sessionSigner`, the relay choice, the node choice and the voucher log are created and held by the chat client alone.

The sentence the sibling documents use is: "On the core path there is no email login, no password and no seed-phrase collection; an optional embedded wallet with email or social sign-in (ADR 0017, proposed) is a funding-surface convenience whose identity is never sent to a node or a relay."

### (2) Embedded-wallet candidates, none selected

Recorded as facts from the register; recording a provider does not select it.

- **Rhinestone embedded wallet.** The passkey private key stays on the user's authenticator (evidence register §4, client UX research 2026-10-15, [V]); the managed path adds a Rhinestone co-signature to every transaction (evidence register §4, client UX research 2026-10-15, [V]); in the released verified-identity recovery flow Rhinestone operates the guardian, applies the email or OAuth policy off-chain and signs with AWS KMS, with no enclave enforcing the policy and a TEE signer still under development (evidence register §4, client UX research 2026-10-15, [V]); whoever controls the guardian can authorize a replacement passkey (evidence register §4, client UX research 2026-10-15, [V]); the SDK README names only Google and Apple sign-in and X was not found (evidence register §4, client UX research 2026-10-15, [V] and [U]); passkey-only sign-up without an email or social identity was not found (evidence register §4, client UX research 2026-10-15, [U]); passkeys and accounts are scoped per hostname (evidence register §4, client UX research 2026-10-15, [V]); no privacy policy was found (evidence register §16, client UX research 2026-10-15, [U]); the SDK's telemetry option bridges events into the integrator's own observability (evidence register §4, client UX research 2026-10-15, [V]) and whether anything reaches Rhinestone is unknown (evidence register §4, client UX research 2026-10-15, [U]).
- **Privy.** Keys exist as a 2-of-2 share set reconstituted briefly inside AWS Nitro Enclaves (evidence register §4, client UX research 2026-10-15, [V]); in TEE mode a login unlocks the wallet on a new device (evidence register §4, client UX research 2026-10-15, [V]); Google and Twitter are supported logins (evidence register §4, client UX research 2026-10-15, [V]); passkey sign-up exists (evidence register §4, client UX research 2026-10-15, [V]) and passkey-only sign-up without an email is a researcher reading (evidence register §4, client UX research 2026-10-15, [L]); the SDK "sends anonymous usage analytics in the background" (evidence register §4, client UX research 2026-10-15, [V]) and no off switch was found (evidence register §4, client UX research 2026-10-15, [U]); the privacy policy lists email, phone, wallet address, social identity, IP address and device data, disclosed to developers, service providers and analytics providers (evidence register §16, client UX research 2026-10-15, [V]).
- **Turnkey.** Key material is decrypted only inside an enclave and attestation is supported (evidence register §4, client UX research 2026-10-15, [V]); "All OIDC tokens are verified inside of Turnkey's secure enclaves" (evidence register §4, client UX research 2026-10-15, [V]), and that the token's nonce is bound to the client's key is the researcher's wording (evidence register §4, client UX research 2026-10-15, [L]); Google, Twitter and passkeys are supported, with X/Twitter listed as OAuth 2.0-only rather than OIDC (evidence register §4, client UX research 2026-10-15, [V]); the parent organization has read-only visibility into every sub-organization (evidence register §4, client UX research 2026-10-15, [V]); the privacy policy lists the wallet address and transaction history (evidence register §16, client UX research 2026-10-15, [V]).

A researcher analysis, marked [U] and not upgraded here, holds that each provider can map the login identity to the wallet address, that every deposit sent from that address is therefore linkable at the provider to the login identity, and that the zero-knowledge spends carry no such identity (evidence register §4, client UX research 2026-10-15, [U]). The per-provider collection statements above are [V]; the linkage conclusion stays [U] and is cited as nothing stronger. Privy and Turnkey wallets are EOAs that can be upgraded under EIP-7702 (evidence register §4, client UX research 2026-10-15, [V]), which keeps them inside the caller invariant of [ADR 0016](0016-funding-edge-and-deposit-key.md).

### (3) The note-vault rule

The existing app-generated identity key of privacy §5 stays the root of the vault. It, every note secret, every context key, `sessionSigner` and `commitKey` come from the operating-system CSPRNG on the device, and none of them is ever derived from, wrapped by, stored with, or recoverable through a wallet key, an embedded-wallet or passkey provider, a recovery guardian, cloud sync or a login identity. The encrypted backup export is the only recovery of the vault. A provider's wallet export (documented for Privy and Turnkey, evidence register §4, client UX research 2026-10-15, [V]; not found for Rhinestone, evidence register §4, client UX research 2026-10-15, [U]) is not the note backup. A provider's recovery may move the funding account and must not reach the vault. Losing the login must never be the only way to lose, or the only way to spend, the notes. The rule is unconditional: there is no opt-in that derives a vault key from a wallet signature.

### (4) The isolation rule

The chat/inference client and the wallet/funding surface are separate modules.

**Boundaries.** They run in distinct origins with separate storage: on the web as two origins, and in native builds as separate webviews with distinct origins and capability sets. A same-origin window, a worker or an iframe is not the boundary; this is a design rule, not a cited fact. No provider iframe or script runs inside a privileged webview.

**Native permissions.** The funding capability set denies every vault, note-secret, prover, `sessionSigner`, `commitKey`, context-key and relay command. There are no wildcard grants. A narrow bridge between the two modules validates both the sender and the payload.

**Loading.** A provider SDK loads only after the user chooses that convenience, and only on funding screens.

**Public funding allowlist** (may reach the provider): the chain id, the account address and the denomination; the `depositNote` calldata the funding surface builds, which carries the public `identityCommitment`; grant and revocation metadata; user-authorized `ragequit` calldata; and transaction results.

**Session denylist** (never crosses): note secrets, trapdoors, nullifiers and preimages; spend and change requests; session ids, `sessionSigner`, `commitKey` and context keys; vouchers; relay and node choice; prompts, answers and contexts.

**Placement.** The refill job of ADR 0016 runs inside the funding module only.

**Disclosure.** What the provider may observe is stated verbatim on the funding surface: the login identity, the wallet address, IP and device data, the public deposit and grant transactions, and its own analytics, which are disclosed and never assumed disabled. The copy is: "Your deposits are public, and the provider can link them to your identity. Sessions do not include your wallet address or login identity. Timing, small groups, identifying content and collusion can still link activity."

**Open question.** How a static build obtains two origins: two pinned builds, ENS subnames or a native split. A path gateway that collapses origins fails the rule. The RR-56 gate requires per-platform storage, IPC and network-egress tests.

### (5) Static distribution

The client is a reproducible build pinned by its content hash, published through an ENS `contenthash` and reached in one of three ways:

- a verifying fetch: a client that asks a gateway for verifiable response types can check the bytes itself, and "CAR verification does not require running IPFS node" (evidence register §4, client UX research 2026-10-15, [V]); `@helia/verified-fetch` is a recorded candidate (evidence register §4, client UX research 2026-10-15, [V]), and so is the Service Worker Gateway, licensed "Apache-2.0 OR MIT" (evidence register §4 and §8, client UX research 2026-10-15, [V]);
- a locally run gateway, which eth.limo documents with a replaceable Ethereum RPC and end-to-end verification (evidence register §4, client UX research 2026-10-15, [V]);
- or a local run from the pinned build or a direct CID.

ENSIP-7 protocol code 0xe3 denotes IPFS content; only the name's Manager can set the content hash, in one Ethereum mainnet transaction that needs ETH there (evidence register §4, client UX research 2026-10-15, [V]). Public gateways are best-effort and "not intended to be part of your critical path" (evidence register §4, client UX research 2026-10-15, [V]). Brave deprecated its built-in IPFS node in August 2024 (evidence register §4, client UX research 2026-10-15, [V]) and whether it still loads ENS-linked sites without a gateway is unresolved (evidence register §4, client UX research 2026-10-15, [U]). IPFS traffic is observable, since third parties can see which CIDs are requested (evidence register §4, client UX research 2026-10-15, [V]), and that an HTTP gateway sees the client's IP and CID is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]). ENS resolution may need a user-chosen Ethereum RPC; direct CID and local access always remain.

### (6) RPC

There is no default endpoint; the user chooses. A full Arbitrum node needs 64 GB RAM, 8 cores and NVMe storage of "ideally several terabytes", a parent-chain RPC, and about a 2.3 TB pruned snapshot (evidence register §1, client UX research 2026-10-15, [V]), which is infeasible for most users, and no browser light client for Arbitrum One was found (evidence register §1, client UX research 2026-10-15, [U]). Chain reads therefore trust the chosen RPC, and the client says so. Session-specific reads stay relay-tunnelled as the dapp document's :33 requires.

### (7) Passkey validators for a self-managed account

Candidates, none selected and none required: OpenZeppelin `WebAuthn.sol` and `P256.sol` (MIT) and base/webauthn-sol (MIT), both using the RIP-7212 precompile with a Solidity fallback (evidence register §4 and §8, client UX research 2026-10-15, [V]); Rhinestone's `WebAuthnValidator`, whose source says AGPL-3.0-only while its package.json says GPL-3.0; the Safe passkey module (LGPL-3.0); and ZeroDev's (MIT) (evidence register §8, client UX research 2026-10-15, [V]). EIP-7951 has been active on Arbitrum One since 2026-01-08 (evidence register §1, client UX research 2026-10-15, [V]); the Arbitrum precompile reference lists no P256VERIFY address (evidence register §1, client UX research 2026-10-15, [V]); whether RIP-7212 arrived in ArbOS 31 or 32 is unresolved, and the P256VERIFY address itself was not found (evidence register §1, client UX research 2026-10-15, [U]). No hosted passkey service is in the core path.

### (8) Bundlers

The core path needs none: the user's EOA, EIP-7702 EOA or smart account submits `depositNote` itself. The record on a shared ERC-4337 mempool on Arbitrum conflicts between sources (evidence register §1, client UX research 2026-10-15, [V] for each statement, [U] for the resolution), and the EntryPoint code identity on Arbitrum One is unverified (evidence register §1, client UX research 2026-10-15, [U]). A smart-account convenience needs demonstrated independent submission before it is offered.

**Answer to the dapp document's open question 1.** Contract wallets are supported when the account is `msg.sender` of `depositNote`, including a batched user operation from that account.

**Answer to open question 2.** This record does not authorize `sessionSigner` as a session key; that stays future work with no CIP proposed.

## Alternatives considered

### Mandatory social login or a backend account

Rejected. It would seat a hosted service in the core path and contradict dapp :30 and :480 and system-architecture :44 and :210. Privy and Turnkey document identity and device-data collection (evidence register §16, client UX research 2026-10-15, [V]); Rhinestone's privacy policy was not found (evidence register §16, client UX research 2026-10-15, [U]), and whether its SDK sends analytics to Rhinestone remains unknown (evidence register §4, client UX research 2026-10-15, [U]). Every such login stays confined to the funding surface.

### A provider-held or provider-synced vault

Rejected. A login unlocks a Privy wallet on a new device (evidence register §4, client UX research 2026-10-15, [V]) and a Rhinestone guardian can authorize a replacement passkey (evidence register §4, client UX research 2026-10-15, [V]); a vault reachable that way would be reachable by whoever controls the login or the guardian. The vault rule in (3) is unconditional.

### One bundle with the wallet SDK in the chat view

Rejected. The Privy SDK sends analytics by default with no documented off switch (evidence register §4, client UX research 2026-10-15, [V] and [U]), and any SDK in the chat origin could read what the session denylist forbids. The isolation rule in (4) is the boundary.

### A hosted passkey service, or a project RPC, gateway or bundler in the core path

Rejected. The Rhinestone wallet SDK defaults to a hosted passkey service (evidence register §4, client UX research 2026-10-15, [V]); a project endpoint of any kind would make the project a required party, which (1) forbids. Each may be a disclosed convenience.

### A CIP letting a smart account authorize `sessionSigner`

Deferred. It would put an account in the spend path and link a session to that account; it needs its own CIP and none is proposed.

### X login as a requirement

Rejected. X was not found for Rhinestone (evidence register §4, client UX research 2026-10-15, [U]) and is OAuth 2.0-only at Turnkey (evidence register §4, client UX research 2026-10-15, [V]); no login of any kind is required on the core path.

## Consequences

- No CIP: nothing on chain or on the wire changes.
- The risk register gains RR-53 (funding-side identity linkage), RR-55 (a hosted convenience treated as required), RR-56 (a funding SDK observes chat, with its per-platform gate), RR-57 (the vault reachable through provider recovery) and RR-60 (RPC and gateway trust); ids reserved by this plan.
- The dapp document gains R10 (funding-side identity linkage), R12 (an SDK observes session data) and R13 (a hosted convenience or store listing treated as required), and its open questions 1 and 2 take the answers in (8).
- The wallet-derived-key opt-in of the privacy document and the dapp document is removed, and [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) records that this ADR removes it.
- Every provider, validator, gateway and light client named here remains a candidate; none is selected or adopted.
- [ADR 0016](0016-funding-edge-and-deposit-key.md) defines what the funding surface may sign; [ADR 0018](0018-one-client-stack.md) defines the stack on which the two modules are built.

## Links

- [docs/evidence-register.md](../evidence-register.md) §1, §4, §8, §15, §16 (client UX research 2026-10-15), §17
- [docs/product/dapp-and-sdk.md](../product/dapp-and-sdk.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/architecture/system-architecture.md](../architecture/system-architecture.md)
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md) (§5)
- [docs/security/threat-model.md](../security/threat-model.md)
- [docs/risk-register.md](../risk-register.md)
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0007](0007-no-protocol-token-in-v1.md)
- [ADR 0010](0010-anonymous-by-default.md)
- [ADR 0011](0011-anonymous-credits.md)
- [ADR 0012](0012-contexts-without-a-wallet-link.md)
- [ADR 0013](0013-repositories-toolchains-ci-and-releases.md)
- [ADR 0016](0016-funding-edge-and-deposit-key.md)
- [ADR 0018](0018-one-client-stack.md)
- [CIP-0005](../cip/0005-phase-one-implementation.md)
