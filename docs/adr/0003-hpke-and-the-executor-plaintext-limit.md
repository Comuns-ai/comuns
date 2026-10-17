# ADR 0003: Encrypt both ways with HPKE and state who can still read

**Status:** proposed — proposed to be superseded in part by ADR 0010 and ADR 0012; the cipher suite, AAD list, envelope signature, commitKey and keyring rules carry forward

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

2026-10-14: [ADR 0010](0010-anonymous-by-default.md) and [ADR 0012](0012-contexts-without-a-wallet-link.md) withdraw four parts of this record: the sender-identity story (a session now presents no wallet or persistent identifier to a node), the sentence naming the payer in the public metadata (a credit session has no payer address), the wallet-signed grant (grants are signed by a per-context key) and the local-execution consequence (local execution is no longer a product option). Three further statements below are superseded and stay only as dated history: the MPC and FHE figures in this Context and under "FHE chat" are the evidence register §4 snapshot of 2026-10-12, replaced by the figures in evidence register §14; the sentence "Strict owner-only confidentiality against the chosen remote operator is an unmet requirement" is superseded in part by ADR 0010, which makes attested mode the opt-in answer to it, bounded by physical attacks; and the sharding-spike transport sentence in the Decision's transport paragraph ("activations move under mutual TLS") is replaced, since activations now travel through a relay, OHTTP-encapsulated to the holder's registered `ohttpKeyConfig` (docs/security/privacy-and-contexts.md §6, docs/node/distributed-execution.md). The plaintext limit remains: in standard mode the executing node reads the prompt. Everything else below stands.

In standard mode the node that executes a request sees the prompt, the granted context and the completion in plaintext. An executor must see plaintext unless fully homomorphic encryption, multi-party computation or a trusted execution environment is used (evidence register §4, [L]). The register's figures for the first two are far from interactive chat:

- A hybrid FHE scheme is about 2.2 MB of ciphertext per token, and a partly encrypted 8B model runs at about 18 seconds per token on 8 GPUs (evidence register §4, [L]).
- MPC for a 7B model is about 5 minutes per token (evidence register §4, [L]).

TEE overhead on the measured stacks is modest: for an 8B model, throughput about −6.85% and −8.84% and time-to-first-token about +19–21%; for a 70B model, about 0–2.3% (evidence register §4, [V]). TEE.fail (October 2025) extracted TDX and SEV-SNP keys, including attestation keys, with a DDR5 interposer, in a way that can also undermine GPU confidential-computing attestation. Vendors treat physical attacks as out of scope (evidence register §4, [L]).

Strict owner-only confidentiality against the chosen remote operator is an unmet requirement. The protocol's job is to name the readers, encrypt everyone else out, and refuse a silent widening of that set. Nothing here has been audited. The `hpke` crate 0.14.1 implements RFC 9180 and reports no paid audit (evidence register §4, [V]). Comuns has not audited it either.

## Decision

v1 encrypts the hop, not the computation. The cipher suite is fixed and is not negotiated.

| Component | Choice |
|---|---|
| Public-key encryption | RFC 9180 HPKE, base mode |
| KEM | X25519 with HKDF-SHA256 |
| KDF | HKDF-SHA256 |
| AEAD | ChaCha20-Poly1305 |
| Context content | ChaCha20-Poly1305 under a fresh key per version |
| Hash | keccak256 |
| Transport | TLS 1.3 on every client–node hop, and HPKE on v1 job envelopes |

TLS hides content from a passive observer of the hop. It does not hide sizes or timing. Padding is an open question. HPKE protects v1 job content so that a terminating proxy cannot read it. Neither replaces the other for those envelopes. The experimental sharding spike is the disclosed exception: activations move under mutual TLS without an HPKE envelope ([ADR 0009](0009-opt-in-client-orchestration.md)). No homegrown cipher, KDF, MAC or mode is permitted.

**Associated data**, in order, binds every envelope and frame to one place: `chainId`, escrow address, `sessionId`, `jobId`, `requestId`, `sheetVersion`, `planId`, `taskId`, `role`, `contextId`, `contextVersion`, direction, frame `seq` (per job, per direction, from 0), and `endOfJob`. `planId`, `taskId` and `role` are bound. `wave` is advisory metadata, is not bound, and a node must not rely on it. The wire `role` is one of: `executor`, `planner`, `answerer`, `reviewer`, `synthesizer`, `merge`, `orchestrator`, `shard holder`, `draft`, `target`, `verifier`. Frame `seq` is not the voucher `seq`. `endOfJob` marks a job's last frame and is never copied into a voucher's `isFinal`.

**Job authentication.** HPKE base mode does not authenticate the sender. Every job envelope carries a signature by the session's `sessionSigner` over `(chainId, escrow address, sessionId, jobId, requestId, sheetVersion, keccak256(enc ‖ ciphertext))`. The node rejects any envelope whose signature does not verify against the `sessionSigner` recorded for that session, before decrypting or scheduling. `clientJobPublicKey` and every job parameter (`maxOutputTokens`, sampling settings) live inside the HPKE plaintext and therefore inside that digest. Nothing that changes the job travels in the clear.

**Keys.** Client HPKE keys are application-managed, generated from the operating-system CSPRNG, stored encrypted at rest, and are never the wallet key and never derived from it. The long-lived identity key is mandatory. Each job also has a fresh keypair; completions are sealed to `clientJobPublicKey`, and that keypair is discarded when the job ends. The session `commitKey` is a separate random 32-byte value from the client CSPRNG, sealed inside the session's first job envelope. It is not derived from an HPKE exporter secret or from a per-job key. Client and node keep it until the session is settled. `outputCommitment = keccak256(commitKey ‖ sessionId ‖ seq ‖ transcriptHash)`, using that voucher's `seq`. `transcriptHash` chains from zero over every output chunk of every job. The commitment is not checked on-chain. Opening `commitKey` discloses the session's output to whoever receives it. It is not a proof without disclosure.

The deprecated wallet RPCs `eth_getEncryptionPublicKey` and `eth_decrypt` are not used (evidence register §4, [V]). Draft ERC-5630 is not used (evidence register §4, [V]).

**Who can still read.** In standard mode the executing node reads the prompt in plaintext. Other operators, the sequencer, RPC providers, indexers and network observers see ciphertext and the public metadata (node, model, token counts, prices, caps, timing, context hashes; credit sessions have no payer address, see [ADR 0010](0010-anonymous-by-default.md)). Single-node execution is the default: one remote party reads the prompt, unless the user also opts into verifiable mode, which adds one user-chosen verifier.

Any non-empty execution-feature set is opt-in per request and is listed on the disclosure sheet before the user signs ([ADR 0009](0009-opt-in-client-orchestration.md)). The sheet's `readersOfFullPrompt` is a floor, never a ceiling, counted by distinct node and by distinct operator. The floor is: the executor; in verifiable mode the verifier; in `collective_answer` every answerer, every reviewer (reviewers receive the prompt) and a remote synthesizer; in `parallel_planning` every planner, every plan reviewer and the plan synthesizer; in `cross_node_speculation` both the draft node and the target node; every shard holder; an orchestrator node whenever it plans, merges or synthesizes; a merge node, whose inputs are assumed to quote the prompt; any remote assessor or planner, including under `task_decomposition`; and any sub-task executor or reviewer whose payload contains prompt text. A sub-task payload is assumed to contain prompt text unless the client has verified that it contains none. The client derives the count from the actual payloads. `counts.fullPrompt` is how many distinct nodes are literally sent the full prompt. `readersOfFullPrompt` is at least that number. The banner is "N nodes can read your prompt", from `readersOfFullPrompt`.

**Attested mode** is optional. The client checks the quote before sealing: freshness via a client nonce, the quote bound to the node's HPKE key, a published measurement list bound to the build and the manifest, and vendor revocation collateral. Quote verification is client-side in v1. On-chain verification is about 3M gas directly, or about 350k gas via a ZK wrapper (evidence register §4, [V/L]), and is not v1. Intel EPID and IAS were discontinued in April 2025; DCAP or Intel Trust Authority are the remaining CPU paths (evidence register §4, [L]). If no eligible attested node exists, the request fails closed. The client never silently downgrades to standard mode. Attested mode is not a defense against physical attack (TEE.fail, evidence register §4, [L]).

**Verifiable mode** is opt-in re-execution by a user-chosen second node under a demonstrated deterministic profile. The verifier is a disclosed full-prompt reader. A session's mode is public on-chain, so mode-2 checks cover only mode-2 sessions. An activation commitment may be sent, through the client, only to that disclosed verifier. No other party receives one. `cross_node_speculation` is incompatible with this mode.

**Contexts move by owner re-wrap.** Each context version `v` has its own random 256-bit key `K_v` from the client CSPRNG. The blob is `header ‖ ciphertext ‖ tag`, with `ciphertext ‖ tag = ChaCha20-Poly1305(K_v, nonce, AAD, plaintext)`. The nonce is 12 random bytes stored in the header. The content AAD is `owner ‖ contextId ‖ v ‖ prevContentHash`. `contentHash` is keccak256 of the complete stored blob (`header ‖ ciphertext ‖ tag`). That is the one canonical definition.

A grant wraps exactly the `K_v` of the granted versions to that node's HPKE key, so a narrow grant restricts decryption. Grant expiry is `expiresAt`, a `uint64` unix time in seconds, never a block number. The grant is EIP-712 typed data signed by the wallet that owns the context, not by `sessionSigner`. Nodes never exchange plaintext or keys. Every `K_v` is also wrapped to the client's identity key. That wrap is mandatory. The backup export contains the identity key and every key-wrap record. It contains no ciphertext. Restoring the backup restores the ability to decrypt a version whose ciphertext can still be fetched from a context host or a second device. Ciphertext that existed only on a lost device is gone even with the backup. The backup alone does not restore every context. Users should keep at least one context host or a second device that holds the ciphertext.

`ContextRegistry` stores the latest `(version, contentHash)` per context and emits `ContextSet` for every version. A node verifies an older version from that event history. If two `setContext` transactions race, the loser reverts. The losing client keeps its local edit, rebases on the new head and publishes the next version. There is no silent merge.

The node keeps a keyring of every HPKE key used by a session that is not yet settled. `updateNode` publishes the new key. An old key is deleted only after every session that used it is settled.

An optional orchestrator node is a disclosed user choice. It is never a protocol dependency, and v1 has no mandatory proxy that sees every prompt ([ADR 0009](0009-opt-in-client-orchestration.md)).

## Alternatives considered

### Plaintext jobs

Rejected. The sequencer, RPC providers and every observer on the path would read the prompt. HPKE is what keeps those parties on ciphertext. It does not hide the prompt from the node the user selected, and the disclosure sheet says so.

### Sign-to-derive keys as the default

Rejected. Deriving an encryption key from a fixed wallet signature needs deterministic signatures (evidence register §4, [L]). Contract wallets and some hardware wallets may not sign deterministically, so the key would not reproduce and the contexts would become unreadable. One phished signature would also expose every context ever derived from it. A labelled opt-in may be proposed later. The client must not fall back to it silently. Proposed [ADR 0017](0017-accounts-and-decentralized-access.md) removes that later opt-in: no vault key is ever derived from a wallet signature.

### TEE-only membership

Rejected. Requiring a TEE for every node would drop operators who cannot produce a quote, and it would still fail against an operator with physical access (evidence register §4, [L]). Attested mode stays optional and client-checked. Standard mode stays the default and states the plaintext limit in the open.

### FHE chat

Rejected for v1. The register's figures, about 2.2 MB per token and about 18 seconds per token on an 8B model, and about 5 minutes per token for MPC on a 7B model (evidence register §4, [L]), are not interactive inference. The marks are [L]. They are not treated as a promise that the costs will stay there, and they are not treated as a reason to claim FHE works for this protocol.

### A mandatory proxy that sees prompts

Rejected. A protocol-mandatory relay, matcher or orchestrator would be a new party that sees every prompt. The orchestrator in [ADR 0009](0009-opt-in-client-orchestration.md) is open-source code in the client. An optional orchestrator node is an ordinary session the user opens on purpose. It is never mandatory and it takes no cut.

## Consequences

- Content privacy against the operator is the attested tier ([ADR 0010](0010-anonymous-by-default.md)); every remote mode has a reader and anonymity does not change that.
- More parties read a prompt only when the user opts in and the sheet lists them. A silent downgrade is a broken client.
- The `hpke` crate has no paid audit (evidence register §4, [V]). An external review is required before mainnet handles real prompts. No audit has been performed.
- Losing the identity key and its backup loses every context the wrap records covered. Losing the only device that held ciphertext loses those blobs even when the backup survives.
- A node that already decrypted a granted version cannot be forced to forget it. Revocation stops later versions.
- `commitKey` and the transcript chain are session state. The node keeps them in persistent encrypted local storage until the session is settled, so a restart can still redeem. Per-job secrets are discarded at job end.
- Wallet RPCs that decrypt in the page, and Draft ERC-5630, are not dependencies.

## Links

- [docs/evidence-register.md](../evidence-register.md) §4, §5, §9
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md)
- [docs/security/inference-verification.md](../security/inference-verification.md)
- [docs/security/threat-model.md](../security/threat-model.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0009](0009-opt-in-client-orchestration.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
