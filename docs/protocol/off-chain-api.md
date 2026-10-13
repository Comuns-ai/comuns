# Off-chain API — encrypted jobs, streaming frames and vouchers

Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12

**Reference:** docs/security/privacy-and-contexts.md, docs/protocol/contracts-and-settlement.md, docs/node/node-design.md, docs/product/dapp-and-sdk.md

---

## 1. Summary

This document proposes the wire protocol between a Comuns client and a Comuns node: everything that happens off-chain between `openSession` and `closeWithVoucher`. Comuns is a community proposal for open-source decentralized LLM inference settled on Arbitrum One; nothing described here runs yet, no implementation exists and no audit has been performed.

The protocol has five message families, all JSON, all carried over TLS 1.3:

1. a **capability document** a node publishes so clients can see what it serves, at what price, in which modes, and with which optional roles;
2. a **session handshake** in which the client proves it owns an on-chain session and the node verifies that session's state on-chain;
3. **encrypted job envelopes** (client → node) and **streaming frames** (node → client), both HPKE-sealed and bound by associated data to one place in one job, with every envelope signed by the session's `sessionSigner`;
4. **receipts and vouchers**: a node-signed input receipt before prefill, a node-signed chunk receipt sealed inside every output frame, and a client-signed cumulative EIP-712 voucher after each, so payment and delivery advance one chunk at a time;
5. **context grants**, cancellation and typed errors.

Identifiers are those of docs/protocol/contracts-and-settlement.md (`sessionId`, `jobId`, `sessionSigner`, `modelId`, `contextId`/`version`/`contentHash`, hardware classes S/M/L/X, tiers T0–T4, `priceInPerMillion`/`priceOutPerMillion`, `CHUNK_TOKENS`, the fifteen contract functions) and the cryptography is that of docs/security/privacy-and-contexts.md (HPKE base mode, the AAD tuple, per-version context keys, `commitKey`, `outputCommitment`). Where this document and either of those disagree, they win.

Three properties the protocol is designed around:

- **No transaction per message.** A session is opened with one wallet signature; every prompt and every chunk inside it is paid by an off-chain voucher signature; the node settles once. The inference payment is never hidden inside L2 gas and is shown to the user separately from it.
- **The node the user picked can read the prompt in standard mode, and nobody else can.** Every other party — other nodes, the sequencer, RPC providers, indexers — sees ciphertext and the public metadata of docs/security/privacy-and-contexts.md §9.
- **Fail closed.** A required mode the node does not offer, a disclosure sheet version the client has not had confirmed, a price that differs from the confirmed one, or a pool that cannot fill a confirmed set ends the request with an error, never with a silent downgrade or a silent substitution.

## 2. Scope

In scope: transport, versioning, the capability document, the session handshake, the job envelope, streaming frames, the receipt and voucher exchange, context grant messages, cancellation, the error catalogue, retry semantics and the settlement states a client shows.

Out of scope, owned elsewhere: contract semantics and the voucher's on-chain checks (docs/protocol/contracts-and-settlement.md); the cipher suite, the AAD tuple and the disclosure sheet's field list (docs/security/privacy-and-contexts.md); how a node schedules, batches and admits work (docs/node/node-design.md); how plans are built, routed and merged (docs/protocol/orchestration.md); the user interface (docs/product/dapp-and-sdk.md). This document carries the multi-node job metadata (`planId`, `taskId`, `role`, bound into the AAD, and `wave`, advisory only) only as fields a node may log; it says nothing about how a plan is formed.

Binding design decisions carried in, all PROPOSED:

| Decision | Value |
|---|---|
| Account | The wallet is the only account; there is no email login and the client never collects a seed phrase |
| RPC endpoint | User-chosen; the client reads `NodeRegistry` and `ModelRegistry` through it or through any community indexer |
| Relay / matcher | None operated by the project and none mandatory; the client talks to the node endpoint from `NodeRegistry` directly |
| Encryption | HPKE in the client with an app-managed keypair, never the wallet key; `eth_getEncryptionPublicKey` and `eth_decrypt` are forbidden |
| Payment | ETH only, protocol fee 0, no token; vouchers per chunk, never a transaction per message; pull payments on-chain (`withdraw()`) |
| Multi-node | One ordinary session per `(node, modelId)`; no payment moves between nodes; `sessionSigner` is never delegated to a node in v1 |

Evidence tags: **[V]** verified in docs/evidence-register.md, **[L]** likely, **[U]** unsure or derived. Anything not tagged is this document's own proposal.

## 3. Transport and versioning

**Transport.** Every client–node hop is HTTPS over TLS 1.3, which authenticates the endpoint recorded in `NodeRegistry` and hides the content of the connection from passive observers on the path; HPKE protects the content end to end so that a terminating proxy or a misconfigured front-end still sees nothing (docs/security/privacy-and-contexts.md §4). Both are required. **TLS hides content, not sizes or timing**: a passive observer on the client–node path still sees the size of every envelope and frame and when each was sent, which reveals prompt and chunk sizes (docs/security/privacy-and-contexts.md §9); padding to fixed sizes is an open question (section 14), not a v1 property.

- `GET {endpoint}/comuns/v1/capability` returns the capability document (section 4). It is the only unauthenticated request.
- All other traffic of a session runs over one WebSocket per session, `wss://{endpoint}/comuns/v1/sessions/{sessionId}`, opened after the handshake of section 5. Every message on it is one JSON object with a `type` field. A client may open a second WebSocket for the same session after a disconnect; the node keeps the session's state (keyring, cumulative counts, pending receipt) across reconnects until the session is settled on-chain.

**Version negotiation.** The capability document lists the protocol versions the node accepts as `protocolVersions`, newest first; the identifier format is `comuns/<major>.<minor>`. The client sends the version it wants in the handshake. A node that does not accept it answers `unsupported_version` and closes. There is no fallback to an older cipher suite: the cipher suite is fixed by docs/security/privacy-and-contexts.md §4 and is not part of version negotiation.

**Idempotency keys.** Two levels are kept apart. **Job-level billing** deduplicates by `jobId`, chosen by the client and unique within the session: a job's input is tokenized, receipted and counted once, however many times its envelopes arrive. **Frames and upload fragments** deduplicate by `(jobId, frameSeq)` in each direction: a multi-frame request (section 6) sends several envelopes under one `jobId` with `seq` 0, 1, 2 …, and each fragment is accepted once by its own `(jobId, seq)`; a repeated fragment is ignored, and a later fragment is never dropped because an earlier one shared its `jobId`. The idempotency key of a voucher is `(sessionId, seq)`. The idempotency key of a grant is `(jobId, contextId, fromVersion, toVersion, nodeKeyHash)` — it includes `jobId`, so a later job on the same session that grants the same context range is a new grant, processed again, never answered with a stale reply. A node that receives a message with a key it has already processed replies with the same answer it gave the first time and performs no second effect; in particular it never counts a job's input twice and never raises its cumulative counts for a repeated submission (section 11). Frames are idempotent too: a retransmitted frame identical to one the client already received is ignored, never a fatal error (section 7). A voucher whose `seq` equals the last accepted `seq` and whose content is identical is a no-op, never an error (section 11).

**One job at a time per session.** `limits.maxConcurrentJobsPerSession` is 1. Receipts and vouchers form one chain per session — every input receipt builds on the last signed voucher and every chunk receipt extends one `transcriptHash` — so two jobs cannot interleave on one session. Jobs that share a `(node, modelId)` session run sequentially; a client that needs two jobs in parallel on the same `(node, modelId)` opens a second session for it, listed on the disclosure sheet like any other session (docs/protocol/orchestration.md §8).

**Two counters that are never confused.** The frame `seq` is per job and per direction and starts at 0; the voucher `seq` is per session and starts at 1. The handshake reports both separately (`lastSeq` for vouchers, `lastFrameSeq` per open job for frames, section 5).

**Timeouts.** Each side advertises its limits; the node's are in `limits` of the capability document. Proposed defaults, all tunable by the operator and shown to the user by the client:

| Timer | Owner | Proposed default | On expiry |
|---|---|---|---|
| `handshakeTimeout` | node | 30 s | WebSocket closed, nothing charged |
| `inputVoucherTimeout` | node | 60 s after the input receipt | job cancelled, nothing charged (no prefill has started) |
| `chunkVoucherTimeout` | node | 30 s after a chunk receipt | node pauses after one unpaid chunk (section 8); after the timer it stops the job and may redeem its last signed voucher |
| `firstFrameTimeout` | client | operator-advertised `limits.maxTimeToFirstFrameMs` | client cancels the job; the input voucher stands (section 11) |
| `interFrameTimeout` | client | 2 × the node's advertised `limits.maxInterFrameMs` | after that long without a frame the client marks the answer truncated and stops waiting (section 7) |
| `reconnectWindow` | node | 10 min | after it the node runs the abandoned-client procedure of docs/protocol/contracts-and-settlement.md §12 |

## 4. Node capability document

A node publishes one capability document per endpoint. Clients use it to confirm what the registry says, to learn the node's HPKE public key hash and limits, and to see optional roles. The registry stays authoritative for prices and offers: a capability document that disagrees with `NodeRegistry` is a reason to skip the node, not a reason to trust the document.

Fields:

| Field | Meaning |
|---|---|
| `protocolVersions` | Accepted protocol versions, newest first |
| `operator` | The node's operator address (its identity in `NodeRegistry`) |
| `endpoint` | The endpoint as registered |
| `hpkePublicKey` | The current registered HPKE public key (X25519, base64); clients must check it against the latest `NodeRegistered`/`NodeUpdated` event and seal only to the registered key |
| `keyringHashes` | Hashes of older keys still on the keyring for unsettled sessions (docs/security/privacy-and-contexts.md §5), so a client can tell that a session sealed to a rotated key is still served |
| `class` | Hardware class, one of `S`, `M`, `L`, `X`, decided by passing the per-class bars of the public class benchmark; it selects the price band. A class is not a tier |
| `maxTier` | The largest tier the operator benchmarked, `T0`–`T4`, a separate field. **Informational only.** It is never a gate: any class may appear in any model's pool |
| `offers[]` | One entry per model offered: `modelId`, `manifestHash`, `priceInPerMillion`, `priceOutPerMillion`, `modelBenchmarkHash`, and a `readiness` object the node signs stating that the model is loaded now (`loaded`, `signedAt`, `signature`). A non-zero `modelBenchmarkHash` is what puts the node in that model's pool (`prices[modelId]` in `NodeRegistry`); `readiness` is a liveness hint, not a contract fact |
| `modes[]` | Advertised privacy modes drawn from `standard`, `attested`, `verifiable`; must equal the registry's `modes` bitmask |
| `limits` | `maxContextTokens`, `maxOutputTokens`, `chunkTokens` (the node's `CHUNK_TOKENS`), `maxConcurrentJobsPerSession` (1 in v1, section 3), `maxTimeToFirstFrameMs`, `maxInterFrameMs` (the longest gap the node promises between two consecutive frames of one job; the client stops waiting after twice this), `maxEnvelopeBytes` |
| `roles` | Optional. `orchestration: {plannerModelIds[]}` advertises that the node serves planning, assessment, merging or synthesis for thin clients through an ordinary session (docs/protocol/orchestration.md §11). `shard` and `draft` are **experimental flags only**, meaningful solely in the Phase 3 verification spike with testnet-only prices; under mainnet parameters the reference client refuses both `model_sharding` and `cross_node_speculation` and ignores these flags. A shard holder holds no session and is never paid, in v1 or in the spike |
| `attestation` | Present only when `attested` is advertised: the quote format and a URL from which the client fetches a fresh quote bound to its own nonce before sealing anything. The client never accepts a quote whose report data does not commit to `hpkePublicKey` and its nonce |
| `deterministicProfiles[]` | Present only when `verifiable` is advertised: identifiers of engine configurations the node has demonstrated to be byte-deterministic (docs/security/inference-verification.md) |
| `signature` | Operator signature over the whole document minus this field |

```json
{
  "type": "capability",
  "protocolVersions": ["comuns/0.1"],
  "operator": "0x00000000000000000000000000000000000000a1",
  "endpoint": "node-a.example",
  "hpkePublicKey": "BASE64_X25519_PUBLIC_KEY_PLACEHOLDER_A",
  "keyringHashes": [],
  "class": "M",
  "maxTier": "T2",
  "offers": [
    {
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01",
      "manifestHash": "0x0000000000000000000000000000000000000000000000000000000000003a01",
      "priceInPerMillion": "20000000000",
      "priceOutPerMillion": "40000000000",
      "modelBenchmarkHash": "0x000000000000000000000000000000000000000000000000000000000000b301",
      "readiness": {
        "loaded": true,
        "signedAt": 1791900000,
        "signature": "OPERATOR_SIGNATURE_PLACEHOLDER"
      }
    },
    {
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a02",
      "manifestHash": "0x0000000000000000000000000000000000000000000000000000000000003a02",
      "priceInPerMillion": "100000000000",
      "priceOutPerMillion": "320000000000",
      "modelBenchmarkHash": "0x000000000000000000000000000000000000000000000000000000000000b302",
      "readiness": {
        "loaded": true,
        "signedAt": 1791900000,
        "signature": "OPERATOR_SIGNATURE_PLACEHOLDER"
      }
    }
  ],
  "modes": ["standard", "attested"],
  "limits": {
    "maxContextTokens": 32768,
    "maxOutputTokens": 4096,
    "chunkTokens": 64,
    "maxConcurrentJobsPerSession": 1,
    "maxTimeToFirstFrameMs": 15000,
    "maxInterFrameMs": 10000,
    "maxEnvelopeBytes": 4194304
  },
  "roles": {
    "orchestration": {
      "plannerModelIds": ["0x0000000000000000000000000000000000000000000000000000000000000a02"]
    },
    "shard": false,
    "draft": false
  },
  "attestation": {
    "format": "tdx-dcap-v4+gpu-cc",
    "quoteUrl": "https://node-a.example/comuns/v1/attestation/quote"
  },
  "signature": "OPERATOR_SIGNATURE_PLACEHOLDER"
}
```

All identifiers in this document are synthetic placeholders; the prices are illustrative numbers chosen so the voucher arithmetic of section 8 can be followed by hand, and they are not a band or a price proposal (docs/economics/cost-and-pricing.md owns prices).

**Pool enumeration is model-first.** A client lets the user pick a model, then enumerates the model's pool: every node whose `NodeRegistry` entry has `prices[modelId]` with a non-zero `modelBenchmarkHash`, read through the user's RPC or a community indexer from `OfferSet` events (docs/protocol/contracts-and-settlement.md §9). The client then fetches each candidate's capability document and ranks by price, measured speed, reputation, privacy mode and class. Any class may appear in any pool; a stronger class costs more for the same model because the bands are ordered; `maxTier` is displayed, never used to filter.

## 5. Session handshake

The handshake binds the WebSocket to one on-chain session and lets both sides check the other's facts before anything is sealed.

1. The client opens `wss://{endpoint}/comuns/v1/sessions/{sessionId}` and sends `hello`: the protocol version, the `sessionId`, the `modelId` and `mode` it expects, the HPKE key hash it is about to seal to, a client nonce, on a reconnect `lastReceivedFrameSeq` for every job it considers open (the highest frame `seq` it received for that job, or −1 if none), and a `sessionSigner` signature over `(chainId, escrow, sessionId, nodeOperator, clientNonce)`. The signature proves the client holds the `sessionSigner` registered for that session; nothing else proves it, because `sessionId` is public in `SessionOpened`.
2. The node reads the session from `SessionEscrow` through its own RPC: `status` must be `open` (or `closing` before `closeDeadline`, in which case the node may still serve but tells the client); `node` must be this operator; `sessionSigner` must recover from the signature; `modelId` and `mode` must match what the client expects; and the copied `priceInPerMillion`/`priceOutPerMillion` are echoed back.
3. The node answers `welcome`: the copied prices as it read them; the effective cap `min(depositWei, maxSpendWei)` and `settledWei` as it read them on-chain; the last voucher it holds (`lastSeq` — the **voucher** counter — with `lastInputTokens`, `lastOutputTokens`, `lastCumulativeWei`); for the job it considers open (at most one, section 3), `lastFrameSeq`, the highest **frame** `seq` it has sent in that job; a keyed transcript check value `keccak256(commitKey ‖ transcriptHash)` (zero for a new session; the plain `transcriptHash` never travels outside encryption); the node nonce; and a node signature over the whole message. If the session is new, the counts are zero and the node states that it expects `commitKey` in the first envelope. The welcome is information for the client's comparison: **node-signed totals are never trusted** (step 5), and **the prices in it are informational** (step 4).
4. **On-chain prices win.** The client compares the prices copied into the session **on-chain** — read from the session record through its own RPC, or from the `SessionOpened` event — with the disclosure sheet the user confirmed (docs/security/privacy-and-contexts.md §8.3, price confirmation). If the on-chain prices differ from the sheet, the client sends nothing further, closes the WebSocket and calls `closeSession`; the deposit returns through `finalize` after `closeDeadline`. This is defence in depth behind the on-chain price binding of `openSession`. The prices a node reports in `welcome`, in its capability document or anywhere else are informational and **never trigger a close**: a `welcome` whose prices differ from the on-chain record is a node that is lying or stale, which the client records and treats as a reason to stop using the node, but the deposit is not locked up behind `closeDeadline` on a node's say-so.
5. The client resumes **only from its own voucher log**, never from the node's figures. It computes the remaining allowance itself as the effective cap minus the highest `cumulativeWei` it has ever signed on this session, redeemed or not. If the node's `lastSeq` is lower than the client's last signed voucher, the client re-sends that voucher (a resend with the same `seq` and identical content is a no-op on the node, section 11). If the node claims a higher `seq` than the client ever signed, the `sessionSigner` is compromised or the client's log is lost; in either case the client signs nothing more on this session, uses the **unilateral close** — the contract's `closeSession` directly, no voucher, then `finalize` after `closeDeadline` (docs/protocol/contracts-and-settlement.md R8) — and, if the user wants to continue, opens a new session under a new, confirmed disclosure sheet version, because a new session is a new deposit and a new cap. A lost voucher log is never repaired from a welcome: the client would be signing for tokens it cannot account for.

```json
{
  "type": "welcome",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "protocolVersion": "comuns/0.1",
  "status": "open",
  "priceInPerMillion": "20000000000",
  "priceOutPerMillion": "40000000000",
  "effectiveCapWei": "100000000000",
  "settledWei": "0",
  "lastSeq": 4,
  "lastInputTokens": 1200,
  "lastOutputTokens": 192,
  "lastCumulativeWei": "31680000",
  "openJobs": [
    {
      "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
      "lastFrameSeq": 2,
      "pendingReceipt": "chunk"
    }
  ],
  "transcriptCheck": "0x0000000000000000000000000000000000000000000000000000000000007c02",
  "expectsCommitKey": false,
  "nodeNonce": "BASE64_NONCE_PLACEHOLDER",
  "signature": "NODE_SIGNATURE_PLACEHOLDER"
}
```

A reconnect repeats the same handshake; the node's `welcome` then carries the state in the middle of which the connection dropped. The node retransmits, under their original frame `seq`, every frame of each open job from the client's `lastReceivedFrameSeq + 1` onward, together with any input receipt the client has not yet answered; the client re-sends its latest voucher. The two sides reconcile on their own records: the client ignores any retransmitted frame identical to one it already holds and signs only for what its own log does not yet cover.

The whole flow, from handshake to settlement, in one picture:

```mermaid
sequenceDiagram
    participant W as Wallet (EIP-1193)
    participant C as Client (sessionSigner, HPKE keys)
    participant E as SessionEscrow (Arbitrum One)
    participant N as Node
    C->>N: GET /comuns/v1/capability
    N-->>C: capability (offers, modes, limits, hpkePublicKey, roles)
    C->>C: show disclosure sheet; user confirms version v
    W->>E: openSession(node, modelId, mode, sessionSigner, maxSpendWei, expectedPriceIn, expectedPriceOut) + deposit
    E-->>C: SessionOpened(sessionId, copied prices)
    C->>N: hello (sessionId, version, expected model/mode, sessionSigner signature)
    N->>E: read session: status, node, sessionSigner, prices
    N-->>C: welcome (copied prices, effective cap, settledWei, lastSeq, lastFrameSeq per open job)
    C->>C: on-chain copied prices == sheet v? else closeSession and stop; allowance from own voucher log
    C->>N: job envelope (HPKE to node key; clientJobPublicKey, params, commitKey in first job sealed; AAD incl. requestId, sheetVersion; signed by sessionSigner)
    N-->>C: input receipt (sessionId, jobId, jobInputTokens, cumulativeInputTokensAfter)
    C->>N: voucher seq 1 (inputTokens = cumulativeInputTokensAfter) if the counts match
    N-->>C: frame seq 0 (HPKE to clientJobPublicKey; chunk receipt sealed inside)
    C->>N: voucher seq 2 (cumulative, outputCommitment)
    N-->>C: frame seq k, endOfJob = true (receipt sealed inside)
    C->>N: voucher seq k+2
    Note over C,N: more jobs on the same session, one at a time; cumulative counts never fall below a signed voucher
    C->>N: voucher final = true (cooperative close: the client closes the session)
    N->>E: closeWithVoucher — credits node and user balances; withdraw() later
    Note over C,E: unilateral close instead: the client calls closeSession (no voucher), then finalize after closeDeadline
```

## 6. Encrypted job message

A job is one request on one session. Its envelope is HPKE-sealed (base mode, DHKEM(X25519, HKDF-SHA256), ChaCha20-Poly1305) to the node's registered public key and signed, outside the AEAD, by the session's `sessionSigner`. The AAD tuple is the one of docs/security/privacy-and-contexts.md §6, reproduced here in the `aad` object so that the node can reconstruct it; any mismatch between `aad` and the envelope's own fields is a reason to reject.

**Nothing that changes the job travels in the clear.** The response key `clientJobPublicKey` and every job parameter (`maxOutputTokens`, sampling settings, `stop`) live inside the HPKE plaintext, and because the `sessionSigner` signature covers `keccak256(enc ‖ ciphertext)` they are inside the signed digest too. A TLS-terminating proxy or a misconfigured front-end can therefore neither redirect the completion to a key of its own nor raise `maxOutputTokens` or change sampling: any edit breaks the AEAD tag or the signature, and the node rejects the envelope. What is outside the ciphertext is either in the AAD, public already, or checked against an on-chain fact (`mode` against the session's mode; `grantRef` against the registry and against the sealed grant, which is authoritative).

| Field | Meaning |
|---|---|
| `sessionId`, `jobId` | The session and the client-chosen job id (idempotency key) |
| `enc` | HPKE encapsulated key |
| `ciphertext` | AEAD output over the plaintext body (shown below): `clientJobPublicKey`, `commitKey` (first job of the session only), `prompt`, `contextGrant` (or absent), `params`, `modelId` |
| `aad` | The AAD tuple: `chainId`, `escrow`, `sessionId`, `jobId`, `requestId`, `sheetVersion`, `planId`, `taskId`, `role`, `contextId`, `contextVersion`, `direction`, `seq`, `endOfJob`. `planId` and `taskId` are zero for single-node execution |
| `grantRef` | Reference to the context grant carried inside the ciphertext: `contextId`, `fromVersion`, `toVersion`, and the `contentHash` of each version so the node can check the registry before decrypting the grant. The node rejects the job if `grantRef` and the sealed grant disagree |
| `mode` | `standard`, `attested` or `verifiable`; must equal the session's mode, which is public on-chain, so it cannot be used to change the job |
| `orchestration` | Optional metadata: `planId`, `taskId`, `role` — bound into the AAD, so they must equal the `aad` values — and `wave`, which is **advisory metadata only, not AAD-bound; a node must not rely on it**. `role` uses exactly the canonical tokens of the AAD field in docs/security/privacy-and-contexts.md §6: `executor`, `planner`, `answerer`, `reviewer`, `synthesizer`, `merge`, `orchestrator`, `shard holder`, `draft`, `target`, `verifier`. There is no separate assessor token: an assessment is the output of a planner session and carries `planner`. **These fields are metadata the node may log. They are never a way to learn another node's plaintext**: a node receives only what the client sealed to it, and the plan, every intermediate result and every other node's envelope stay with the client |
| `signature` | `sessionSigner` signature over `(chainId, escrow, sessionId, jobId, requestId, sheetVersion, keccak256(enc ‖ ciphertext))` |

The plaintext body the client seals, before encryption (it never appears on the wire in this form):

```json
{
  "type": "job_plaintext",
  "clientJobPublicKey": "BASE64_X25519_PER_JOB_PUBLIC_KEY_PLACEHOLDER",
  "commitKey": "BASE64_32_BYTE_SESSION_COMMIT_KEY_PLACEHOLDER_FIRST_JOB_ONLY",
  "prompt": "Summarize the attached brief.",
  "contextGrant": "SEE_SECTION_9_OR_ABSENT",
  "params": {
    "maxOutputTokens": 512,
    "temperature": 0.7,
    "topP": 0.95,
    "stop": []
  },
  "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01"
}
```

`clientJobPublicKey` is a fresh per-job X25519 public key the node seals frames to, discarded when the job ends. `params.maxOutputTokens` is what the client will sign vouchers up to for this job.

The node, in this order: checks the signature against the `sessionSigner` recorded on-chain for the session (reject with `invalid_envelope_signature` otherwise, before decrypting anything); checks the AAD tuple; checks `mode` against the session; checks every `grantRef` version's `contentHash` against `ContextRegistry` or its `ContextSet` history; decrypts; checks that the sealed grant matches `grantRef` and verifies the grant's `ownerSignature` and `nodeKeyHash`; tokenizes the prompt and the granted context with the manifest's pinned tokenizer; sends the input receipt of section 8; and starts prefill only when it holds the input voucher.

```json
{
  "type": "job",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
  "enc": "BASE64_HPKE_ENCAPSULATED_KEY_PLACEHOLDER",
  "ciphertext": "BASE64_AEAD_CIPHERTEXT_PLACEHOLDER",
  "aad": {
    "chainId": 42161,
    "escrow": "0x0000000000000000000000000000000000000e5c",
    "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
    "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
    "requestId": "0x0000000000000000000000000000000000000000000000000000000000004e01",
    "sheetVersion": 1,
    "planId": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "taskId": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "role": "executor",
    "contextId": "0x000000000000000000000000000000000000000000000000000000000000c001",
    "contextVersion": 6,
    "direction": "client-to-node",
    "seq": 0,
    "endOfJob": true
  },
  "grantRef": {
    "contextId": "0x000000000000000000000000000000000000000000000000000000000000c001",
    "fromVersion": 5,
    "toVersion": 6,
    "contentHashes": {
      "5": "0x000000000000000000000000000000000000000000000000000000000000c0a5",
      "6": "0x000000000000000000000000000000000000000000000000000000000000c0a6"
    }
  },
  "mode": "standard",
  "orchestration": null,
  "signature": "SESSION_SIGNER_SIGNATURE_PLACEHOLDER"
}
```

The `chainId` value 42161 is the commonly published chain id of Arbitrum One and is UNVERIFIED in this document, as in docs/security/privacy-and-contexts.md §6; confirm at implementation. A job that belongs to a plan carries `orchestration` instead of `null`; its `planId`, `taskId` and `role` are then the same values as in `aad`, and `wave` is advisory:

```json
{
  "type": "job",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e02",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b07",
  "enc": "BASE64_HPKE_ENCAPSULATED_KEY_PLACEHOLDER",
  "ciphertext": "BASE64_AEAD_CIPHERTEXT_PLACEHOLDER",
  "aad": {
    "chainId": 42161,
    "escrow": "0x0000000000000000000000000000000000000e5c",
    "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e02",
    "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b07",
    "requestId": "0x0000000000000000000000000000000000000000000000000000000000004e02",
    "sheetVersion": 2,
    "planId": "0x0000000000000000000000000000000000000000000000000000000000009101",
    "taskId": "0x0000000000000000000000000000000000000000000000000000000000000702",
    "role": "executor",
    "contextId": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "contextVersion": 0,
    "direction": "client-to-node",
    "seq": 0,
    "endOfJob": true
  },
  "grantRef": null,
  "mode": "standard",
  "orchestration": {
    "planId": "0x0000000000000000000000000000000000000000000000000000000000009101",
    "taskId": "0x0000000000000000000000000000000000000000000000000000000000000702",
    "wave": 1,
    "role": "executor"
  },
  "signature": "SESSION_SIGNER_SIGNATURE_PLACEHOLDER"
}
```

A multi-frame request (for example a large granted context's ciphertext attached in several upload frames, the default delivery of section 9) sends several envelopes with the same `jobId`, `direction = client-to-node`, `seq` increasing from zero and `endOfJob = true` on the last; each is signed. The node applies the same AAD and `seq` rules it expects the client to apply to its frames, and deduplicates each fragment by `(jobId, seq)`, never by `jobId` alone: job-level deduplication by `jobId` applies to billing — one input receipt, one count — not to the fragments that make up the job (section 3). The job is tokenized and receipted only once its last fragment (`endOfJob = true`) has arrived.

### 6.1 The client-side objects the metadata points at

`planId`, `taskId`, `wave`, `role`, `requestId` and `sheetVersion` refer to two objects that exist only on the client and never travel to a node or to the chain: the **plan** and the **disclosure sheet**. They are shown here so that implementers of the node side know what the metadata means and what they will never receive. The plan format is owned by docs/protocol/orchestration.md and the sheet's field list by docs/security/privacy-and-contexts.md §8.3.

A plan is a DAG of tasks; waves are its topological levels; the client dispatches one encrypted job per task into the session of the node it confirmed for that task's `modelId`. Each task has a unique `outputName`, which is the placeholder later templates use (`${outputName}`); `outputSchema` may repeat across tasks. Because a session runs one job at a time (section 3), a wave's tasks run concurrently only across different sessions; two tasks of one wave that share a session run one after the other. No node sees the plan unless the user delegated planning to an orchestrator node, in which case the plan is that node's output, sealed back to the client.

```json
{
  "type": "plan",
  "planId": "0x0000000000000000000000000000000000000000000000000000000000009101",
  "version": 1,
  "requestHash": "0x0000000000000000000000000000000000000000000000000000000000004e02",
  "createdBy": {
    "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a02",
    "node": "0x00000000000000000000000000000000000000c3"
  },
  "tasks": [
    {
      "taskId": "0x0000000000000000000000000000000000000000000000000000000000000701",
      "wave": 1,
      "dependsOn": [],
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01",
      "role": "executor",
      "promptTemplate": "Summarize the regulatory section of the attached brief in 200 words.",
      "visibility": "subTask",
      "outputName": "regulatorySummary",
      "outputSchema": "text",
      "maxOutputTokens": 400
    },
    {
      "taskId": "0x0000000000000000000000000000000000000000000000000000000000000702",
      "wave": 1,
      "dependsOn": [],
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01",
      "role": "executor",
      "promptTemplate": "List the open technical questions in the attached brief as bullet points.",
      "visibility": "subTask",
      "outputName": "openQuestions",
      "outputSchema": "text",
      "maxOutputTokens": 400
    },
    {
      "taskId": "0x0000000000000000000000000000000000000000000000000000000000000703",
      "wave": 2,
      "dependsOn": [
        "0x0000000000000000000000000000000000000000000000000000000000000701",
        "0x0000000000000000000000000000000000000000000000000000000000000702"
      ],
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a02",
      "role": "reviewer",
      "promptTemplate": "Review for contradictions: ${regulatorySummary} and ${openQuestions}",
      "visibility": "subTask",
      "outputName": "contradictionReview",
      "outputSchema": "text",
      "maxOutputTokens": 300
    }
  ],
  "merge": {
    "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a02",
    "strategy": "synthesize"
  },
  "collective": null,
  "estimatedTokens": 3200,
  "estimatedCapWei": "ILLUSTRATIVE_NO_VALUE_SET"
}
```

The disclosure sheet is computed from the plan before any session opens; its `version` is what `sheetVersion` in every AAD refers to. `recipients[]` has one entry per session, that is per distinct `(node, modelId)`; `roles[]` and `receives[]` are arrays because one session may serve several tasks. Two numbers are kept apart: `counts.fullPrompt` is the number of distinct nodes **literally sent** the full prompt (one below: the planner), while `readersOfFullPrompt` is the floor count of nodes that **can read** it, derived from the actual payloads (docs/security/privacy-and-contexts.md §8.2) and always ≥ `counts.fullPrompt`: the two executors below receive sub-tasks that embed the brief and the reviewer receives sub-task outputs that may quote the prompt, so all four are readers.

```json
{
  "type": "disclosure_sheet",
  "requestId": "0x0000000000000000000000000000000000000000000000000000000000004e02",
  "planId": "0x0000000000000000000000000000000000000000000000000000000000009101",
  "version": 2,
  "recipients": [
    {
      "node": "0x00000000000000000000000000000000000000c3",
      "operator": "0x00000000000000000000000000000000000000c3",
      "roles": ["planner"],
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a02",
      "mode": "standard",
      "receives": ["full prompt"],
      "priceInPerMillion": "100000000000",
      "priceOutPerMillion": "320000000000",
      "capWei": "ILLUSTRATIVE_NO_VALUE_SET"
    },
    {
      "node": "0x00000000000000000000000000000000000000a1",
      "operator": "0x00000000000000000000000000000000000000a1",
      "roles": ["executor"],
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01",
      "mode": "standard",
      "receives": ["sub-task", "context versions whose keys are granted"],
      "priceInPerMillion": "20000000000",
      "priceOutPerMillion": "40000000000",
      "capWei": "ILLUSTRATIVE_NO_VALUE_SET"
    },
    {
      "node": "0x00000000000000000000000000000000000000b2",
      "operator": "0x00000000000000000000000000000000000000b2",
      "roles": ["executor"],
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01",
      "mode": "standard",
      "receives": ["sub-task", "context versions whose keys are granted"],
      "priceInPerMillion": "21000000000",
      "priceOutPerMillion": "41000000000",
      "capWei": "ILLUSTRATIVE_NO_VALUE_SET"
    },
    {
      "node": "0x00000000000000000000000000000000000000d4",
      "operator": "0x00000000000000000000000000000000000000d4",
      "roles": ["reviewer", "merge"],
      "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a02",
      "mode": "standard",
      "receives": ["sub-task outputs, which may quote the prompt"],
      "priceInPerMillion": "100000000000",
      "priceOutPerMillion": "320000000000",
      "capWei": "ILLUSTRATIVE_NO_VALUE_SET"
    }
  ],
  "counts": {
    "fullPrompt": 1,
    "subTask": 2,
    "otherAnswers": 1,
    "activations": 0,
    "draftTokens": 0
  },
  "readersOfFullPrompt": {
    "nodes": 4,
    "operators": 4
  },
  "totalCapWei": "ILLUSTRATIVE_NO_VALUE_SET",
  "l2GasEstimate": "SHOWN_SEPARATELY_NEVER_FOLDED_INTO_totalCapWei",
  "experimental": false
}
```

The sheet JSON is normative: every table or banner a client shows is generated from it and must match it exactly. `counts` matches `receives[]` node by node — one node is sent the full prompt, two a sub-task, one other nodes' outputs — and each node is counted under exactly one payload kind. `readersOfFullPrompt` is the separate floor: the sub-task executors and the reviewer-and-merge node are readers because their payloads were derived from the prompt and the client did not verify they contain none of it (docs/security/privacy-and-contexts.md §8.2). A banner says "4 nodes can read your prompt" from `readersOfFullPrompt` and lists the payload kinds from `counts` without counting a node twice (docs/product/dapp-and-sdk.md §5). Any change of node, model, data scope, price, cap or reader set — including adding a verifier for verifiable mode on the result — creates a new sheet version that must be confirmed before any `openSession` or job under it.

## 7. Streaming frames

The node streams the completion as HPKE frames sealed to `clientJobPublicKey`, one frame per chunk of at most `CHUNK_TOKENS` output tokens (the node's `limits.chunkTokens`). Each frame carries the AAD tuple with `direction = node-to-client`, a transport `seq` starting at zero, and `endOfJob = true` only on the last frame. Every frame carries the chunk receipt of section 8 **inside the sealed plaintext**: no hash of the chunk plaintext ever travels outside encryption, because a TLS-terminating proxy could otherwise hash candidate short answers, labels or numbers and identify the completion despite HPKE. Any hash that must appear outside encryption is keyed, `keccak256(commitKey ‖ chunk)`, and `commitKey` is known only to client and node.

| Field | Meaning |
|---|---|
| `jobId`, `sessionId` | As in the job |
| `seq` | Transport sequence number of this frame, starting at 0 per job and per direction. This is never the voucher `seq`, a separate per-session counter starting at 1 |
| `enc` | HPKE encapsulated key for this frame's sender context (one per frame, or one per job with per-frame AEAD nonces — the reference choice is an open question, section 14) |
| `ciphertext` | AEAD output over the frame plaintext (shown below): the chunk `text`, `tokenCount`, for the last frame `finishReason` (`stop`, `length`, `cancelled`, `error`), and the node-signed `receipt` |
| `aad` | The AAD tuple |
| `endOfJob` | Last-frame flag, also in the AAD. Never copied into a voucher's `final` |

The frame plaintext, before sealing:

```json
{
  "type": "frame_plaintext",
  "text": "…the last 44 tokens of the answer…",
  "tokenCount": 44,
  "finishReason": "stop",
  "receipt": {
    "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
    "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
    "cumulativeInputTokens": 1200,
    "cumulativeOutputTokens": 236,
    "chunkHash": "0x00000000000000000000000000000000000000000000000000000000000c4a53",
    "signedAt": 1791900123,
    "signature": "NODE_SIGNATURE_PLACEHOLDER"
  }
}
```

`chunkHash` is the keccak256 of the chunk plaintext (docs/security/privacy-and-contexts.md §10); it is safe there only because the receipt is sealed. The frame on the wire:

```json
{
  "type": "frame",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
  "seq": 3,
  "enc": "BASE64_HPKE_ENCAPSULATED_KEY_PLACEHOLDER",
  "ciphertext": "BASE64_AEAD_CIPHERTEXT_PLACEHOLDER",
  "aad": {
    "chainId": 42161,
    "escrow": "0x0000000000000000000000000000000000000e5c",
    "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
    "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
    "requestId": "0x0000000000000000000000000000000000000000000000000000000000004e01",
    "sheetVersion": 1,
    "planId": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "taskId": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "role": "executor",
    "contextId": "0x000000000000000000000000000000000000000000000000000000000000c001",
    "contextVersion": 6,
    "direction": "node-to-client",
    "seq": 3,
    "endOfJob": true
  },
  "endOfJob": true
}
```

**Ordering and idempotency.** The client accepts a new frame only if its AAD matches the expected tuple and its `seq` is exactly the next expected value. A retransmitted frame whose `seq` the client has already received and whose bytes are identical to the frame it holds is **ignored, never a fatal error** — this is what makes reconnection safe when the client received frame `n` but its voucher never reached the node. A frame with an already-received `seq` and different bytes, or a `seq` beyond the next expected value, is rejected and the client treats the stream as broken: it stops signing and sends `cancel` (section 10). The node never reorders and never retransmits a frame under a new `seq`; after a reconnect it resends, under their original `seq`, the frames of each open job from the client's `lastReceivedFrameSeq + 1` (section 5). The frame counter and the voucher counter are never confused: `welcome` reports `lastFrameSeq` per job for frames and `lastSeq` for vouchers.

**Finalization.** A job ends with exactly one frame carrying `endOfJob = true` and a `finishReason`. The client rejects anything that follows it for the same `jobId`. A `finishReason` of `length` means `maxOutputTokens` was reached; `cancelled` means the client's `cancel` was honoured; `error` means the node stopped and the body carries an error code from section 10. In every case the vouchers already signed stand; the client signs no voucher covering output it did not receive.

**Truncation detection.** A stream that stops without an `endOfJob` frame — connection dropped, `interFrameTimeout` expired (2 × the node's advertised `limits.maxInterFrameMs` without a frame; the client marks the answer truncated and stops waiting), or the node sent an error outside the stream — is truncated. The client keeps the partial text, marks it truncated in the UI, signs nothing further for the job, and either reconnects (the node resends from `lastReceivedFrameSeq + 1`; identical duplicates are ignored) or cancels. A truncated job never silently becomes a complete answer.

## 8. Voucher exchange

Payment and delivery alternate in steps of one chunk. The node's unpaid exposure is one chunk; the user's exposure to a dishonest count is zero before prefill and one chunk during streaming; the loss that remains is stated at the end of this section.

**Step 0 — input receipt (node → client, before prefill).** After tokenizing the job's prompt and granted context with the manifest's pinned tokenizer, and before any prefill, the node sends a node-signed input receipt over `(sessionId, jobId, jobInputTokens, cumulativeInputTokensAfter)`. The client recomputes `jobInputTokens` with the same tokenizer and checks `cumulativeInputTokensAfter = lastInputTokens + jobInputTokens`, where `lastInputTokens` is the `inputTokens` of the last voucher it signed on this session (zero for the first job). If either check fails the client signs nothing and abandons the job (`input_count_mismatch`); if both hold it signs the **input voucher**, whose `inputTokens` is the cumulative total and whose `outputTokens` is unchanged from the previous voucher.

**Unsigned receipts are void.** "Cumulative" on both sides means *the totals covered by the last voucher the client signed*. If the client does not sign the input voucher for a job — it stops, the counts mismatch, or `inputVoucherTimeout` expires — that job's tokens never enter the cumulative counts: the node's next input receipt is `lastSignedInputTokens + newJobInputTokens`, where `lastSignedInputTokens` is the `inputTokens` of the highest voucher the node holds. Counts never fall below a signed voucher, and an unsigned receipt binds nobody; a receipt is a claim, a voucher is the agreement.

```json
{
  "type": "input_receipt",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
  "jobInputTokens": 1200,
  "cumulativeInputTokensAfter": 1200,
  "tokenizer": "manifest-pinned",
  "signedAt": 1791900100,
  "signature": "NODE_SIGNATURE_PLACEHOLDER"
}
```

**Step n — chunk receipt (node → client, sealed inside every frame).** Each frame's `receipt` is a usage claim: the session-cumulative input and output counts after this chunk and the hash of the chunk plaintext. The client checks the hash against the decrypted chunk, checks that `cumulativeOutputTokens` rose by exactly `tokenCount` and that `tokenCount` agrees with its own tokenizer tally of the chunk's **token text only** — receipts and vouchers count model tokens, never metadata bytes such as the receipt, the `finishReason` or any sealed side data — within a tolerance it sets (the reference client proposes zero tolerance for the pinned tokenizer and treats any disagreement as `output_count_mismatch`), extends `transcriptHash = keccak256(prev ‖ chunkHash)`, and signs the next cumulative voucher.

**Voucher (client → node).** The one canonical EIP-712 type of docs/protocol/contracts-and-settlement.md §8, signed by `sessionSigner` under the `SessionEscrow` domain:

`Voucher(bytes32 sessionId,uint64 seq,uint256 cumulativeWei,uint64 inputTokens,uint64 outputTokens,bytes32 outputCommitment,bool final)`

- `seq` starts at 1 and strictly increases per session.
- `inputTokens` and `outputTokens` are cumulative for the whole session, across all its jobs; they never fall.
- `cumulativeWei = (priceInPerMillion × inputTokens + priceOutPerMillion × outputTokens) / 1000000` with the session's copied prices, integer floor division, recomputed on-chain. With the illustrative prices of section 4 (20,000,000,000 and 40,000,000,000 wei per million), 1,200 input tokens and 236 output tokens give 24,000,000 + 9,440,000 = 33,440,000 wei.
- `outputCommitment = keccak256(commitKey ‖ sessionId ‖ seq ‖ transcriptHash)`, computed with this same voucher's `seq`, with `commitKey` the random 32-byte session key the client sent sealed in the session's first envelope; not checked on-chain; opening it to anyone discloses the session's output to them.
- `final` is true only on the closing voucher ("the client closes the session"). It is never the frame flag `endOfJob`. `redeemVoucher` rejects a `final` voucher; only `closeWithVoucher` accepts it.

**Two ways to close.** The **cooperative close** is the client signing a `final` voucher from its own log and the node calling `closeWithVoucher`, which credits the node and the user's refund in one transaction. The **unilateral close** is the client calling the contract's `closeSession` directly — no voucher, one wallet transaction — and `finalize` after `closeDeadline`; the node may still redeem its highest non-final voucher until then. A client that has lost its voucher log uses only the unilateral close and signs nothing (section 11).

```json
{
  "type": "voucher",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "seq": 5,
  "cumulativeWei": "33440000",
  "inputTokens": 1200,
  "outputTokens": 236,
  "outputCommitment": "0x0000000000000000000000000000000000000000000000000000000000000c05",
  "final": false,
  "signature": "SESSION_SIGNER_EIP712_SIGNATURE_PLACEHOLDER"
}
```

**Pause after one unpaid chunk.** The node sends chunk n+1 only after it holds the voucher covering chunk n. If the voucher does not arrive within `chunkVoucherTimeout` the node pauses the job; if it still does not arrive the node ends the job with `finishReason = error` and `unpaid_chunk_timeout`, keeps the highest voucher it holds and may redeem it at any time while that is legal. The node never streams ahead of payment by more than one chunk, and the reference node does not start prefill before the input voucher.

**Vouchers cover the acknowledged prefix.** A voucher — a chunk voucher, a closing voucher or a resend — may cover only the prefix of the transcript the client has acknowledged, and the node checks it against that prefix: it accepts a voucher whose counts and `outputCommitment` match the acknowledged prefix even when it has already sent one more chunk, and that unacknowledged chunk is simply unpaid — the node's one-chunk exposure, nothing more. A voucher whose `seq` equals the last accepted `seq` and whose content is identical is a no-op, never an error; a chunk in flight when such a resend arrives is covered by the next voucher. A voucher with an already-accepted `seq` and different content is rejected as not retryable, and the client treats the disagreement as it treats any unexplained mismatch (R4): it stops signing and closes.

**Cap, allowance and top-up.** The effective cap is `min(depositWei, maxSpendWei)`. The client's **remaining allowance** is the effective cap minus the highest `cumulativeWei` it has signed in that session, redeemed or not — never the cap minus `settledWei`, which would count unredeemed vouchers as available. The client **never signs a voucher above the effective cap**: when the next chunk would take the running total past it, the client stops signing (`cap_exhausted`, section 10) and the node, which holds no voucher above the cap, pauses. After a `topUp` (which raises `maxSpendWei` and the deposit) the client simply continues with the next chunk voucher under the next `seq`. The contract's rule that a voucher above the cap is paid only up to the cap, and the "re-sign the same cumulative totals under a new `seq`" recovery of docs/protocol/contracts-and-settlement.md §8, apply only if a voucher above the old cap had been signed and was only partly paid — a situation the reference client never creates.

**What the client checks and does not check.** Automatic voucher signing verifies token counts against receipts and against what the client decrypted, and that the node declared the session's `modelId`. It does not judge answer quality. The chat view therefore has a Stop control (docs/product/dapp-and-sdk.md) that stops signing; the user then owes at most the chunks already received.

**Residual risk, stated plainly.** A node can redeem the input voucher and never run the prompt. The user's loss is bounded by that prompt's input fee; the remedy is to stop signing and record a reputation event; nothing in v1 refunds it.

## 9. Context grant message

A grant lets one node decrypt a range of versions of one context the wallet owns. It is carried inside the job envelope's ciphertext (section 6), and `grantRef` outside it tells the node which registry entries to check first. A grant belongs to the job that carries it: its idempotency key is `(jobId, contextId, fromVersion, toVersion, nodeKeyHash)` (section 3), so the second prompt of a chat that grants the same versions again is processed as a new grant for its new `jobId`. Its fields are those of docs/security/privacy-and-contexts.md §7 — `ownerSignature` is EIP-712 typed data signed by the **wallet that owns the context**, never by `sessionSigner`, over `contextId`, `fromVersion`, `toVersion`, the wrapped keys, `expiresAt` and `nodeKeyHash` (the client batches the grants of one request into one wallet prompt where it can; docs/product/dapp-and-sdk.md §7). The message below adds only transport framing: per version, how the ciphertext reaches the node.

**Ciphertext delivery — inline by default, no SSRF.** The default, and the only delivery a node must support, is that the client uploads each granted version's ciphertext blob (`header ‖ ciphertext ‖ tag`) **inline in upload frames** of the same job: a multi-frame request (section 6) whose fragments are deduplicated by `(jobId, seq)`. An optional `blobUrl` lets the owner point instead at a host of its choosing, under rules the node applies before any connection is opened: the URL must be `https`; the host name must resolve to a public address — never a private, loopback, link-local, multicast or cloud-metadata range — and every redirect is re-checked against the same rule before it is followed; a size limit (at most `limits.maxEnvelopeBytes` per blob) and a time limit apply; the fetch happens **only after** the grant signature, `nodeKeyHash` and the session checks of section 6 have passed; and `contentHash` is verified before the blob is used. `blobUrl` is **never part of the signed grant fields**, so it carries no authority, and a node may refuse it altogether (answering `blob_url_refused`, after which the client re-sends the job with the blob inline). A node that implements `blobUrl` without these restrictions lets a correctly signed grant turn it into a proxy for requests to its own internal services, which no later hash check can undo.

```json
{
  "type": "context_grant",
  "contextId": "0x000000000000000000000000000000000000000000000000000000000000c001",
  "owner": "0x00000000000000000000000000000000000000ff",
  "fromVersion": 5,
  "toVersion": 6,
  "versions": [
    {
      "version": 5,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a5",
      "delivery": "inline",
      "blobUrl": null,
      "wrappedKey": "BASE64_HPKE_WRAPPED_K5_TO_NODE_KEY_PLACEHOLDER"
    },
    {
      "version": 6,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a6",
      "delivery": "url",
      "blobUrl": "https://host.example/blobs/0x000000000000000000000000000000000000000000000000000000000000c0a6",
      "wrappedKey": "BASE64_HPKE_WRAPPED_K6_TO_NODE_KEY_PLACEHOLDER"
    }
  ],
  "expiresAt": 1791986400,
  "nodeKeyHash": "0x000000000000000000000000000000000000000000000000000000000000d0a1",
  "ownerSignature": "WALLET_SIGNATURE_PLACEHOLDER"
}
```

`delivery` and `blobUrl` are transport framing outside the signed fields (version 6 above shows the optional URL form; version 5 the default). Rules the node applies, in this order: verify `ownerSignature` against the on-chain owner of `(owner, contextId)`; check that `nodeKeyHash` is the hash of a key on its keyring; for each version take the blob from the job's upload frames or, only if it accepts `blobUrl` and the URL passes the rules above, fetch it; check that `keccak256(header ‖ ciphertext ‖ tag)` equals `contentHash` and that `contentHash` is what `ContextRegistry` or its `ContextSet` history records for that version; check the AAD chain `owner ‖ contextId ‖ v ‖ prevContentHash` version by version; unwrap exactly the keys given; use them only within the range and before `expiresAt` (unix seconds, never a block number); discard them at `expiresAt` or at job end, whichever is earlier. Context tokens are input tokens and appear in the input receipt.

Errors: a hash that does not match is `context_hash_mismatch`; a version the registry does not know, or a grant for a version behind a head the node was told to use, is `stale_version`; a grant past `expiresAt` is `grant_expired`; a `nodeKeyHash` not on the keyring is `grant_key_mismatch`; a `blobUrl` the node does not accept, or that fails the destination, size or time rules, is `blob_url_refused` (retryable with the blob inline).

## 10. Cancellation and errors

**Cancel (client → node).** The client may cancel a job at any time. The node stops generating, sends one last frame with `finishReason = cancelled` and `endOfJob = true` carrying the receipt for whatever it had already produced up to the previous chunk boundary, and expects no voucher beyond the last chunk the client acknowledged (`lastAcknowledgedFrameSeq`): a chunk sent but not acknowledged is unpaid (section 8, acknowledged prefix). A cancel is idempotent by `jobId`.

```json
{
  "type": "cancel",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
  "reason": "user_stop",
  "lastAcknowledgedFrameSeq": 2,
  "signature": "SESSION_SIGNER_SIGNATURE_PLACEHOLDER"
}
```

**Error (either direction).** One shape for every error. `retryable` tells the receiver whether the identical message may be resent (section 11); `scope` says whether the job, the session or the request is affected.

```json
{
  "type": "error",
  "code": "stale_disclosure_sheet",
  "scope": "request",
  "retryable": false,
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e02",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b07",
  "detail": "sheetVersion 1 in AAD, but the client's recorded confirmation is for version 2",
  "at": 1791900200
}
```

Error catalogue. The sender column says who raises it in the normal case; a client raises most of them locally, before anything is sent, which is what fail-closed means in practice.

| Code | Raised by | Meaning | Scope | What stands |
|---|---|---|---|---|
| `unsupported_version` | node | No shared protocol version | session | nothing sent, nothing charged |
| `unsupported_mode` | client or node | The required privacy mode is not advertised by the node; the request fails closed, never downgrades | request | no session opened |
| `attestation_failed` | client | Quote invalid, measurement not on the published list, report data not bound to `hpkePublicKey` and the client nonce, or collateral expired | request | no envelope sealed; if a session was opened, `closeSession` |
| `band_mismatch` | client | The node's current prices are outside the band for (model tier, node class), so `openSession` would revert; shown before any transaction | request | no session opened |
| `price_mismatch` | client | Prices copied into the session **on-chain** (session record or `SessionOpened`) differ from the confirmed sheet (handshake step 4); prices a node reports in `welcome` never raise it | session | `closeSession`; nothing signed |
| `no_offer_for_model` | client or node | The node has no offer (zero `modelBenchmarkHash`) for the model, so it is not in the pool | request | no session opened |
| `pool_cannot_fill_confirmed_set` | client | A node on the confirmed sheet is no longer in the pool, is deregistering, or refused admission, and no pre-confirmed fallback exists; the whole request fails closed | request | sessions already opened are closed with `closeSession` or a `final` voucher |
| `cap_exhausted` | client or node | The next chunk would take the signed total past `min(depositWei, maxSpendWei)`; the client signs nothing above the cap and the node pauses until `topUp`, after which the client continues with the next chunk voucher | session | every signed voucher stands |
| `model_not_loaded` | node | The node's offer exists but the process does not have the model loaded now (stale offer) | session | nothing charged if no input receipt was signed for; otherwise the input voucher stands |
| `context_hash_mismatch` | node | A granted blob does not hash to the `contentHash` in the registry or its `ContextSet` history | job | no input receipt, nothing charged |
| `stale_version` | node | The grant names a version the registry does not know, or the client sent a version behind the head it asked the node to use; the client re-reads the head, rebases its edit and publishes the next version | job | nothing charged |
| `grant_expired` | node | `expiresAt` is in the past | job | nothing charged |
| `grant_key_mismatch` | node | `nodeKeyHash` is not on the node's keyring | job | nothing charged |
| `blob_url_refused` | node | The node does not accept `blobUrl`, or the URL fails the destination, redirect, size or time rules of section 9 | job | nothing charged; the client re-sends with the blob inline |
| `session_closed` | node | The session is `closing` past `closeDeadline`, or `settled`; nothing more can be served or redeemed | session | vouchers already redeemed stand; the remainder returns by `finalize` |
| `stale_disclosure_sheet` | client | The plan changed (node added, scope widened, cap raised, price changed) after the user confirmed, or an envelope would carry a `sheetVersion` with no recorded confirmation; the client sends nothing until the sheet is re-shown and signed for | request | signed vouchers stand; no new job |
| `unsupported_execution_feature` | client | A requested feature is not available: the pool has no node for a required role, or the feature is experimental and no testnet price exists | request | no session opened |
| `verifiable_with_cross_node_speculation` | client | Verifiable mode requires byte-identical re-execution; cross-node speculation does not guarantee it; the combination fails explicitly | request | no session opened |
| `invalid_envelope_signature` | node | The envelope's `sessionSigner` signature does not verify against the session's recorded signer; rejected before decryption | job | nothing charged |
| `input_count_mismatch` | client | `jobInputTokens` differs from the client's own tokenization, or `cumulativeInputTokensAfter ≠ lastInputTokens + jobInputTokens` | job | nothing signed for this job |
| `output_count_mismatch` | client | A chunk receipt's hash or counts disagree with the decrypted chunk | job | vouchers up to the previous chunk stand |
| `unpaid_chunk_timeout` | node | No voucher for the last chunk within `chunkVoucherTimeout` | job | the node keeps and may redeem its highest voucher |
| `unknown_session` | node | The session is not in `SessionEscrow`, or its `node` is another operator | session | nothing |

## 11. Retry semantics

**When an identical request may be resent.** A job envelope, or any fragment of a multi-frame one, whose `jobId` the node has not yet answered with an input receipt may be resent byte for byte: the node deduplicates each fragment by `(jobId, frameSeq)`, bills the job once by `jobId`, and answers once. A voucher may always be resent: `(sessionId, seq)` makes it idempotent — a voucher whose `seq` equals the last accepted `seq` and whose content is identical is a no-op, never an error, and the contract likewise ignores `seq ≤ lastSeq` (docs/protocol/contracts-and-settlement.md §8); the node checks every voucher against the prefix the client acknowledged (section 8). A `cancel` may be resent. A `hello` may be resent with a fresh nonce.

**When a new `jobId` and a new envelope are required.** Once the node has sent an input receipt for a `jobId`, that job is defined, and the client has either signed for it or abandoned it. Any change to the prompt, the granted context, the parameters, the mode or the orchestration metadata is a new job: a new `jobId`, a fresh per-job keypair, a fresh HPKE context, a fresh AAD tuple and a fresh signature. Replaying an old envelope under a new `jobId` is impossible by construction because `jobId` is in the AAD and in the signed digest.

**How duplicate billing is prevented.** Vouchers are cumulative and the node is paid at most `min(cumulativeWei, cap)` for the whole session, so no repetition of any message can pay twice. A resent envelope receives the same input receipt with the same `cumulativeInputTokensAfter`; the node never raises its cumulative input for a `jobId` it already counted. A resent frame carries the same `seq` and the same receipt; the client never signs two vouchers for one chunk because the second has nothing new to add to the cumulative counts. **An abandoned job leaves no trace in the counts** (section 8, unsigned receipts are void): if the client does not sign the input voucher for a job — Stop, `input_count_mismatch` or `inputVoucherTimeout` — that job's tokens never enter the cumulative counts; the node's next input receipt on the session is `lastSignedInputTokens + newJobInputTokens`, computed from the highest voucher it holds, so the client's check `lastInputTokens + jobInputTokens` passes for the next job and the session continues. Counts never fall below a signed voucher; they simply never rose for the unsigned job. A node that nevertheless carried the abandoned job's tokens forward would fail the client's check on every later job and earn nothing more on the session — the client signs nothing it cannot account for and closes.

**Retry after a client-side failure.** If the client lost its connection before receiving the input receipt, it reconnects and resends the envelope (idempotent). If it lost the connection mid-stream, it reconnects with `lastReceivedFrameSeq` per open job in `hello`; the node resends from `lastReceivedFrameSeq + 1` under the original frame `seq`, and the client ignores any retransmitted frame identical to one it already holds. If the client has signed a voucher the node never received, it resends its latest voucher; the counts are cumulative so order does not matter, and a resend the node already holds is a no-op. In every case the client resumes from **its own voucher log**: it never adopts the node's `lastInputTokens`, `lastOutputTokens` or `lastCumulativeWei`. If that log is lost, the client signs nothing more on that session: it uses the unilateral close — the contract's `closeSession` directly, no voucher — the user calls `finalize` after `closeDeadline`, and further work needs a new session, which is a new deposit and a new cap and therefore a new disclosure sheet version confirmed before `openSession`.

**Retry after a node-side failure.** If the node answers with `retryable = true`, the identical message may be resent after a backoff the client chooses. If it answers `model_not_loaded`, `session_closed` or an `unknown_session`, the client stops using that session.

**A retry on a different node needs a new session.** A session names one node and its HPKE key; nothing sealed to node A can be given to node B. To retry on node B the client must open a new `SessionEscrow` session with B (one wallet signature), seal a new envelope to B's key under a new `jobId`, and sign new vouchers for B. In a plan, B must already be on the confirmed disclosure sheet (as a pre-confirmed fallback); if it is not, the sheet is re-shown and the user signs again before anything is sent to B. The vouchers signed for node A stand: A is paid for what it delivered, and the user's refund from A's session returns through `closeWithVoucher` or `finalize`.

## 12. Settlement states visible to the client

The client shows the user where each job and each session stands. None of these states is a promise of L1 finality; "settled" means L2 inclusion under the single sequencer (docs/protocol/contracts-and-settlement.md §7).

| State | Level | Meaning | What the user sees |
|---|---|---|---|
| `delivered` | job | The `endOfJob` frame arrived and every chunk receipt checked | the answer is complete; the running total shows what has been signed for |
| `voucher_accepted` | voucher | The node acknowledged the signed voucher over the WebSocket | the amount is owed but nothing is on-chain yet; if the node vanished now it could still redeem up to this voucher |
| `redeemed` | voucher | A `VoucherRedeemed` event for a `seq` at or above this voucher is visible through the user's RPC — that is, the transaction is **L2-included** under the sequencer | the amount is credited to the node's balance on-chain; "L2-included" is distinct from L1 finality, which the client may optionally wait for |
| `settled` | session | A `SessionSettled` event is visible (`closeWithVoucher` or `finalize`) | the node's credit and the user's refund are both recorded; nothing further can be charged; the refund is a balance to be pulled with `withdraw()` |
| `withdrawable` | user | `balances[user]` in `SessionEscrow` is non-zero | a Withdraw control is offered; it is one transaction for every settled session at once |
| `closing` | session | `SessionClosing` is visible | until `closeDeadline` the node may still redeem; after it, `finalize` returns the remainder |
| `truncated` | job | The stream ended without `endOfJob` | the partial answer is marked; the signed vouchers for received chunks stand; nothing is owed for the missing tail |

Application-level completion (`delivered`) and economic completion (`settled`) are different events and the client never conflates them; in particular a user who sees `delivered` has not yet been charged on-chain, and a user who sees `settled` cannot be charged more.

## 13. Risks

### R1 — Node redeems the input voucher and never runs the prompt **[RISK] · Low**

The input voucher is signed before prefill and is not reversible. Loss bounded by one prompt's input fee; mitigation is to stop signing and record a reputation event. Stated plainly, not solved.

### R2 — Client and node tokenizers disagree **[RISK] · Medium**

If the manifest's pinned tokenizer is built differently on the two sides, every input receipt fails the client's check and no job can be paid for. Mitigation: a tokenizer test vector in the model manifest; the client refuses the session before `openSession` if its own tokenizer fails the vector (open question in docs/security/privacy-and-contexts.md §14).

### R3 — Stale capability document or stale offer **[RISK] · Medium**

A capability document can say `loaded: true` for a model the process has since unloaded, and an offer can outlive the model. `openSession` succeeds, the node answers `model_not_loaded`, and the deposit sits until `closeSession` and `finalize`. No money is lost; gas and time are. Mitigation: the client requests admission in the handshake before sending any job and, where the user allows, before `openSession`; indexers downrank nodes whose sessions settle with zero `settledWei`.

### R4 — WebSocket state loss on the node **[RISK] · Medium**

A node that loses its in-memory session state (pending receipt, `transcriptHash`, keyring) cannot continue a session correctly. Mitigation: the node keeps `commitKey`, the transcript chain and the highest voucher in persistent, encrypted local storage for the life of the session (until settled), so a restart can still redeem; per-job secrets are separate and discarded at job end; after a reconnect the `welcome` message is signed and the client compares it with its own voucher log, which alone decides what it signs next, and closes the session on any disagreement it cannot explain by a voucher the node has not yet received.

### R5 — Metadata in `orchestration` fields leaks the shape of a plan **[RISK] · Low**

`planId`, `taskId`, `role` (AAD-bound) and `wave` (advisory, unbound) tell a node that it is part of a larger request, how large, and in which position. They never carry another node's plaintext. Mitigation: none beyond saying so; the same shape is inferable on-chain from the timing of the sessions (docs/security/privacy-and-contexts.md §9).

### R6 — Protocol downgrade through version negotiation **[RISK] · Low**

Version negotiation could be abused to force an older message format. Mitigation: the cipher suite is not negotiable; a major version change requires a CIP; the client refuses any version older than the one it was built against unless the user opts in.

### R7 — Unaudited implementation **[RISK] · High**

No implementation of this protocol exists and no audit of the design has been performed; the `hpke` crate the reference node intends to use reports no paid audit (evidence register §4 [V]). Mitigation: the review plan of docs/security/privacy-and-contexts.md §12, which is unfunded and unscheduled.

## 14. Open questions

1. **HPKE context per frame or per job.** Whether each frame carries its own `enc` (simplest, larger) or one HPKE context per job is reused with per-frame AEAD nonces (smaller, needs careful nonce handling); the reference choice must be fixed before test vectors are published.
2. **`CHUNK_TOKENS` ownership.** Whether `limits.chunkTokens` is per node (advertised) or a protocol constant (docs/protocol/contracts-and-settlement.md §16).
3. **Capability document discovery.** Whether the document should also be published through an indexer so that clients can rank a pool without contacting every node, and how stale such a copy may be.
4. **Admission before `openSession`.** Whether the client should always obtain a signed admission promise from the node before the user signs `openSession`, and whether a broken promise should be a reputation event indexers surface.
5. **Tokenizer tolerance.** Whether the client should accept small disagreements in `tokenCount` for the same pinned tokenizer, or whether any disagreement is a hard error as proposed here. Zero tolerance on re-tokenized decoded text can reject honest receipts, because different token sequences can decode to the same text; the candidate resolutions are that chunk tokens travel as token IDs inside the sealed frame so the client counts IDs rather than re-tokenizing text, or that a bounded tolerance applies.
6. **Padding.** Whether envelopes and frames are padded to fixed sizes, since TLS hides content but not sizes or timing (section 3; docs/security/privacy-and-contexts.md §14).
7. **Transport alternatives.** Whether a plain HTTPS request/response pair with server-sent frames should be offered beside the WebSocket for clients that cannot keep a socket open, and what that does to reconnect semantics.
8. **Reputation events.** The format of the client-side record of `model_not_loaded`, `unpaid_chunk_timeout` and the input-voucher-never-run case, so that community indexers can aggregate them without a central reporter.
9. **`commitKey` loss.** How `commitKey` is re-sent if the session's first envelope is lost before the node acknowledges it, without opening a second session (docs/security/privacy-and-contexts.md §14).
10. **Thin clients.** Whether a device that cannot sign per chunk may delegate `sessionSigner`, which this document forbids in v1; an open question for a later CIP (docs/protocol/contracts-and-settlement.md §16).
11. **`blobUrl` policy.** Whether the reference node should accept `blobUrl` at all, and if so the exact size and time limits and the public-address check it applies after every redirect (section 9); the default remains inline upload.
12. **Resume after a transient disconnect.** Section 7 says the client "signs nothing further for the job" once a stream is truncated, yet a node that resumes after a reconnect needs the voucher for the chunk it last sent before it streams the next one, so a transient disconnect would stall the job. The intended reading is that a client resuming from its own voucher log continues normal signing after the reconnect — re-sending its latest voucher, then signing for retransmitted chunks it had not yet covered — and that "sign nothing further" applies only when the voucher log is lost (section 11, the unilateral close); the text of section 7 should be tightened to say so.
13. **Inline retry after `blob_url_refused`.** Section 9 has the client "re-send the job with the blob inline" after `blob_url_refused`, but a resend under the same `jobId` and fragment `seq` is returned by fragment dedupe (section 3) as already processed. The inline retry should use a new `jobId` (a new envelope, keypair, AAD tuple and signature, as section 11 requires for any changed job); nothing is charged for the refused job because no input receipt was signed for.
14. **Spike-only round frame and timer names.** The Phase 3 cross-node speculation spike needs a request frame kind inside an open job carrying the accepted tokens and a rollback point (docs/node/distributed-execution.md §8 and its open question 9); this document does not define it, its AAD fields, its ordering with `endOfJob` or its idempotency by `(jobId, frameSeq)`, and must before the spike runs. Separately, the client timer this document calls `interFrameTimeout` is defined only as 2 × the capability field `limits.maxInterFrameMs`; whether the timer should carry the capability field's name so the two cannot drift is open.
