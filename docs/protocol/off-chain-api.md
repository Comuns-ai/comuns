# Off-chain API — encrypted jobs, streaming frames and vouchers

Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12

**Reference:** docs/security/privacy-and-contexts.md, docs/protocol/contracts-and-settlement.md, docs/node/node-design.md, docs/product/dapp-and-sdk.md, docs/adr/0010-anonymous-by-default.md, docs/adr/0011-anonymous-credits.md, docs/adr/0012-contexts-without-a-wallet-link.md, docs/cip/0002-anonymous-credits-relays-and-ownerless-contexts.md, docs/adr/0014-relay-authentication-to-gateways.md, docs/adr/0015-node-key-possession.md, docs/cip/0005-phase-one-implementation.md

---

## 1. Summary

This document proposes the wire protocol between a Comuns client and a Comuns node: everything that happens off-chain between a credit spend and `closeWithVoucher`. Comuns is a community proposal for open-source decentralized LLM inference settled on Arbitrum One; nothing described here runs yet, no implementation exists and no audit has been performed. The protocol follows docs/adr/0010-anonymous-by-default.md (relays and the two content tiers), docs/adr/0011-anonymous-credits.md (credit-funded sessions) and docs/adr/0012-contexts-without-a-wallet-link.md (ownerless contexts); the CIP that proposes adopting them is [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md).

The protocol has five message families, all JSON, all carried as Oblivious HTTP exchanges through a relay (section 3):

1. a **capability document** a node publishes so clients can see what it serves, at what price, in which modes, with which OHTTP key and padding parameters, and with which optional roles, together with the **`key_probe` / `key_probe_response`** exchange of [ADR 0015](../adr/0015-node-key-possession.md) by which the client checks, before it spends, that the gateway holds the registered keys (section 5). These two are the only requests that carry no `sessionSigner`;
2. a **session handshake** in which the client spends one anonymous credit note through the node, the node opens the session on-chain, and the client proves it holds the session's `sessionSigner`;
3. **encrypted job envelopes** (client → node) and **streaming frames** (node → client), both HPKE-sealed, padded to size buckets, and bound by associated data to one place in one job, with every envelope signed by the session's `sessionSigner`;
4. **receipts and vouchers**: a node-signed input receipt before prefill, a node-signed chunk receipt sealed inside every output frame, and a client-signed cumulative EIP-712 voucher after each, so payment and delivery advance one chunk at a time;
5. **context grants** signed by a per-context key, cancellation and typed errors.

Identifiers are those of docs/protocol/contracts-and-settlement.md as amended by docs/adr/0011-anonymous-credits.md (`sessionId`, `jobId`, `sessionSigner`, `modelId`, `contextId`/`version`/`contentHash`, hardware classes S/M/L/X, tiers T0–T4, `priceInPerMillion`/`priceOutPerMillion`, `CHUNK_TOKENS`, the twenty-three contract functions, `pendingWei`, `RELAY_FEE_WEI`) and the cryptography is that of docs/security/privacy-and-contexts.md (HPKE base mode, the AAD tuple, per-version context keys, `commitKey`, `outputCommitment`). Where this document and either of those disagree, they win.

Three properties the protocol is designed around:

- **No transaction per message, and no wallet in the loop.** A session is opened by one credit spend that the node submits on-chain; every prompt and every chunk inside it is paid by an off-chain voucher signature; the node settles once. The user's wallet signs `depositNote` (and, if ever needed, `ragequit` and `withdraw`); only if the user opts in does it also sign account setup, bounded swaps or intents in its own account, and a deposit-key grant and its revocation ([ADR 0016](../adr/0016-funding-edge-and-deposit-key.md), proposed). The deposit key signs only `depositNote`. No account key, deposit key or login ever signs a voucher, envelope, spend, close or `claimChange`, and none is sent to a node or a relay. No wallet address, account, cookie or persistent client identifier appears in any message of this protocol. The inference payment is never hidden inside L2 gas and is shown to the user separately from it.
- **The node the user picked can read the prompt in standard mode, and should not learn who asked.** Every other party — the relay, other nodes, the sequencer, RPC providers, indexers — sees ciphertext and the public metadata of docs/security/privacy-and-contexts.md §9. The relay sees the client's network address and not the prompt; the node sees the prompt and not the client's network address. In attested mode, this node should not be able to read your prompt; a physical attack on the hardware can break that (evidence register §14).
- **Fail closed.** A required mode the node does not offer, no usable relay, a disclosure sheet version the client has not had confirmed, a price that differs from the confirmed one, a credit spend the node will not submit, or a pool that cannot fill a confirmed set ends the request with an error, never with a silent downgrade, a silent substitution or a direct connection.

## 2. Scope

In scope: transport, versioning, the capability document, the credit handshake, the job envelope, streaming frames, padding and batching, the receipt and voucher exchange, context grant messages, cancellation, the error catalogue, retry semantics and the settlement states a client shows.

Out of scope, owned elsewhere: contract semantics, the credit pool, the voucher's on-chain checks and every event (docs/protocol/contracts-and-settlement.md, transcribing docs/adr/0011-anonymous-credits.md); the cipher suite, the AAD tuple and the disclosure sheet's field list (docs/security/privacy-and-contexts.md); how a node schedules, batches and admits work (docs/node/node-design.md); how plans are built, routed and merged (docs/protocol/orchestration.md); the user interface (docs/product/dapp-and-sdk.md). This document carries the multi-node job metadata (`planId`, `taskId`, `role`, bound into the AAD, and `wave`, advisory only) only as fields a node may log; it says nothing about how a plan is formed.

Binding design decisions carried in, all PROPOSED:

| Decision | Value |
|---|---|
| Account | None presented to the network. The wallet signs `depositNote` (and, if ever needed, `ragequit` and `withdraw`); only if the user opts in does it also sign account setup, bounded swaps or intents in its own account, and a deposit-key grant and its revocation ([ADR 0016](../adr/0016-funding-edge-and-deposit-key.md), proposed). The deposit key signs only `depositNote`. No account key, deposit key or login ever signs a voucher, envelope, spend, close or `claimChange`, and none is sent to a node or a relay. `sessionSigner` is a fresh key per session, never reused. On the core path there is no email login, no password and no seed-phrase collection; an optional embedded wallet with email or social sign-in ([ADR 0017](../adr/0017-accounts-and-decentralized-access.md), proposed) is a funding-surface convenience whose identity is never sent to a node or a relay. |
| Transport | Oblivious HTTP (RFC 9458) through a relay chosen at random from `NodeRegistry`, with chunked OHTTP for streaming; the reference client has no direct client-to-node path (docs/adr/0010-anonymous-by-default.md) |
| Chain reads | The client reads `NodeRegistry` and `ModelRegistry` through a user-chosen RPC or any community indexer; every session-specific read (session lookup, settlement and change monitoring, Merkle witness and root queries) is an RPC or indexer query tunnelled through a relay; an indexer is a backend behind that transport, not an alternative to it |
| Encryption | HPKE in the client with an app-managed keypair, never the wallet key; `eth_getEncryptionPublicKey` and `eth_decrypt` are forbidden; the job HPKE envelope travels unchanged inside the OHTTP hop |
| Payment | ETH credit notes of fixed denominations spent by Semaphore proofs (docs/adr/0011-anonymous-credits.md), protocol fee 0, no token; vouchers per chunk, never a transaction per message; change returns as fresh notes through `claimChange`; pull payments on-chain (`withdraw()`) for nodes and relays |
| Contexts | Identified by a per-context key, `contextId = keccak256(contextPubKey)`; grants are signed by that key, never by a wallet (docs/adr/0012-contexts-without-a-wallet-link.md) |
| Multi-node | One ordinary session per `(node, modelId)`; no payment moves between nodes; `sessionSigner` is never delegated to a node in v1 |

Evidence tags: **[V]** verified in docs/evidence-register.md, **[L]** likely, **[U]** unsure or derived. Anything not tagged is this document's own proposal.

## 3. Transport and versioning

**Transport.** Every client–node message is encapsulated with Oblivious HTTP (RFC 9458) under the node's registered `ohttpKeyConfig` and sent to a relay, which forwards it to the node's gateway; the node process is the gateway. Both hops run over TLS 1.3. The client picks the relay at random for each OHTTP exchange (the proposed resolution of open question 2 in section 14, [ADR 0014](../adr/0014-relay-authentication-to-gateways.md); the relay paid the relay fee stays fixed by the credit spend), from the relay records of `NodeRegistry` (`registerRelay`, docs/adr/0011-anonymous-credits.md) whose `unlockAt` is zero and whose operator address differs from the node's operator; the contract refuses to register one address as both, and the client additionally refuses any relay record whose operator equals the node operator (`relay_is_node_operator`, section 10). When no such relay is available the request fails closed with `relay_unavailable`: **a direct connection to the node endpoint is not a reference path**. The client addresses the relay as `POST {relay endpoint}/comuns/v1/gateway/{nodeOperatorAddress}`, with the OHTTP-encapsulated request as the body; the relay resolves the gateway's endpoint from its own `NodeRegistry` view and never accepts a client-supplied URL, host or port, and it may refuse a gateway with `gateway_refused`, after which the client tries another relay for that exchange (ADR 0014). The relay authenticates to the gateway as a registered relay operator once per TLS connection (ADR 0014); the gateway serves nothing but the authentication challenge on a connection it has not authenticated, and that relay–gateway handshake carries no client identifier. The inner job HPKE envelope, its AAD and its `sessionSigner` signature (section 6) travel unchanged inside the OHTTP encapsulation, so a relay that terminates TLS still sees only an OHTTP ciphertext, and a node that terminates the OHTTP hop still sees only an HPKE ciphertext until it has checked the envelope. Streamed completions use chunked OHTTP (draft-ietf-ohai-chunked-ohttp-08, approved and in the RFC Editor queue, blocked on normative references, no RFC number on 2026-10-15; evidence register §15, recheck 2026-10-15, [V]); open question 3 records the residuals.

What RFC 9458 gives and does not give (evidence register §15 [V]): the relay sees the client's network address, request and response sizes, timing and the target gateway, never the OHTTP plaintext; the gateway sees the OHTTP plaintext, which is the HPKE job envelope, and the relay's address, never the client's address — and in standard mode the node can read the prompt once it opens that envelope; the two must be run by different entities, which is why the operator check above exists; traffic analysis is out of scope of the RFC; an OHTTP exchange costs at least two HTTP requests; and chunked OHTTP lets either the relay or the gateway measure round-trip time in an interactive exchange. The reference shape follows the draft's section 7.2 guidance: no request chunk depends on a response chunk within one exchange, which also avoids in-exchange replay of interactively generated request chunks (evidence register §15, recheck 2026-10-15, [V]). The gateway still links a session's exchanges through the session fields inside them and can time the gap between a response and the client's next exchange, which includes the client's round trip; that cross-exchange timing remains a residual (R8, T37, RR-40). One operator holding a relay and a node under two addresses is a stated residual, not a checked property (section 13). **Padding buckets and token batch sizes (sections 4, 6 and 7) are unset parameters**: they reduce what sizes and timing reveal and are not a claim that Whisper Leak or token-length inference is solved (evidence register §16 [V]).

No cookies, no persistent client identifiers and no wallet address appear in any message. Nothing in a request identifies the client beyond the `sessionSigner` of the session it belongs to, which is fresh per session.

- `GET /comuns/v1/capability`, carried as an OHTTP exchange through a relay on the path above, returns the capability document (section 4). The capability document and the `key_probe` exchange of ADR 0015 are the only requests that carry no sessionSigner. Both are served only on a relay connection the gateway has authenticated (ADR 0014), and neither carries a client identifier. Every session message keeps the sessionSigner rule.
- All other traffic of a session is OHTTP exchanges carrying the same JSON message types, with the same idempotency keys and the same two counters, that an earlier draft of this document carried over a per-session WebSocket. Every message is one JSON object with a `type` field. The reference exchange shape is one OHTTP exchange per message, and no exchange is interactive: the request body is complete before the node starts its response, and the client never sends a request chunk after it has received a response chunk of the same exchange. A job exchange carries the job envelope and its upload fragments as the request body (as chunked OHTTP request chunks or one known-length body; either way the content never depends on the response); its response carries the input receipt and then ends, because the reference node starts prefill only when it holds the input voucher (section 8). Each voucher is its own exchange, and its response streams the frames that voucher releases (section 8); each exchange uses a fresh OHTTP context. An earlier draft of this document carried one chunked exchange per job with the vouchers streamed inside the request body; that is the interactive case the draft's section 7.2 tells applications to avoid, because the gateway can then measure the client's round-trip time and a malicious relay can replay interactively generated request chunks (evidence register §15, recheck 2026-10-15, [V]); that shape is withdrawn. Chunked OHTTP requests and responses carry the HTTP header `Incremental: ?1`, which the draft says they SHOULD include so that relays do not buffer them (evidence register §15, recheck 2026-10-15, [V]); draft-ietf-httpbis-incremental is itself a normative reference the RFC Editor is waiting on (evidence register §15, recheck 2026-10-15, [V]). The draft's section 1.1 says chunked OHTTP is not intended for long-lived sessions that build up state (evidence register §15, recheck 2026-10-15, [V]); the session's state lives in the application above OHTTP, and session linkage remains. The node keeps the session's state (keyring, cumulative counts, pending receipt) across exchanges until the session is settled on-chain, so a lost exchange is resumed with a new `hello` (section 5).

**Exchange lifecycle.** In every exchange the request is complete before the response starts, no request chunk follows a response chunk, and each exchange uses a fresh OHTTP context. The messages, counters, fields and idempotency keys are unchanged by this shape; only the exchange boundaries are fixed here.

| Exchange | Request | Response |
|---|---|---|
| hello | `hello` | `welcome`; on a resume, `welcome` followed by pending receipts, retained terminal frames and replayed frames under their original `seq` |
| job | the job envelope and its upload fragments | the input receipt, then the response ends. Prefill starts only after the input voucher (section 8) |
| input voucher | the input voucher | the first output chunk (the one unpaid chunk) |
| chunk voucher | the voucher covering chunk n | chunk n+1, or the `endOfJob` frame |
| final voucher | the voucher covering the last chunk | an acknowledgment with no further output |
| cancel | `cancel` | the last frame with `finishReason = cancelled` and `endOfJob = true`; if it is not in this response, the node retains it for the client's next exchange for that job (section 10) |

`hello` is sent as its own exchange before the job exchange, and again on a resume (section 5). Timeout, cancellation and error frames are terminal frames: the node retains them and delivers them on the client's next exchange for that job, or after `welcome` on a resume `hello`, under their original frame `seq`. A response that ends at the input receipt, or after a released chunk, ends at a payment boundary; that is not truncation (section 7). The closing voucher with `final = true` (section 8) is likewise answered with an acknowledgment and no output.

**Version negotiation.** The capability document lists the protocol versions the node accepts as `protocolVersions`, newest first; the identifier format is `comuns/<major>.<minor>`. The client sends the version it wants in the credit spend and in the handshake. A node that does not accept it answers `unsupported_version`. There is no fallback to an older cipher suite: the cipher suite is fixed by docs/security/privacy-and-contexts.md §4 and is not part of version negotiation, and the OHTTP key configuration is fixed by the registry, not negotiated.

**Idempotency keys.** Two levels are kept apart. **Job-level billing** deduplicates by `jobId`, chosen by the client and unique within the session: a job's input is tokenized, receipted and counted once, however many times its envelopes arrive. **Frames and upload fragments** deduplicate by `(jobId, frameSeq)` in each direction: a multi-frame request (section 6) sends several envelopes under one `jobId` with `seq` 0, 1, 2 …, and each fragment is accepted once by its own `(jobId, seq)`; a repeated fragment is ignored, and a later fragment is never dropped because an earlier one shared its `jobId`. The idempotency key of a voucher is `(sessionId, seq)`. The idempotency key of a credit spend is its `nullifier`: nullifier deduplication prevents duplicate submissions and duplicate session creation. Validation failures are not cached permanently by nullifier: a replacement proof or a refreshed root for the same nullifier is revalidated against current chain state. Pending or successful submissions keep their existing result. The idempotency key of a grant is `(jobId, contextId, fromVersion, toVersion, nodeKeyHash)` — it includes `jobId`, so a later job on the same session that grants the same context range is a new grant, processed again, never answered with a stale reply. A node that receives a message with a key it has already processed replies with the same answer it gave the first time and performs no second effect; in particular it never counts a job's input twice, never submits a second spend for one nullifier, and never raises its cumulative counts for a repeated submission (section 11). Frames are idempotent too: a retransmitted frame identical to one the client already received is ignored, never a fatal error (section 7). A voucher whose `seq` equals the last accepted `seq` and whose content is identical is a no-op, never an error (section 11).

**One job at a time per session.** `limits.maxConcurrentJobsPerSession` is 1. Receipts and vouchers form one chain per session — every input receipt builds on the last signed voucher and every chunk receipt extends one `transcriptHash` — so two jobs cannot interleave on one session. Jobs that share a `(node, modelId)` session run sequentially; a client that needs two jobs in parallel on the same `(node, modelId)` opens a second session for it with a second note, listed on the disclosure sheet like any other session (docs/protocol/orchestration.md §8).

**Two counters that are never confused.** The frame `seq` is per job and per direction and starts at 0; the voucher `seq` is per session and starts at 1. The handshake reports both separately (`lastSeq` for vouchers, `lastFrameSeq` per open job for frames, section 5).

**Timeouts.** Each side advertises its limits; the node's are in `limits` of the capability document. Proposed defaults, all tunable by the operator and shown to the user by the client:

| Timer | Owner | Proposed default | On expiry |
|---|---|---|---|
| `spendSubmitTimeout` | client | 60 s after `credit_spend` was sent | no `session_opened` and no on-chain event: the client treats the note as in flight (section 13, R9) and may re-prove it to another node |
| `handshakeTimeout` | node | 30 s | exchange ends, nothing charged |
| `inputVoucherTimeout` | node | 60 s after the input receipt ended the job exchange | job cancelled, nothing charged (no prefill has started) |
| `chunkVoucherTimeout` | node | 30 s after a chunk receipt | node pauses after one unpaid chunk (section 8); after the timer it stops the job and may redeem its last signed voucher |
| `firstFrameTimeout` | client | operator-advertised `limits.maxTimeToFirstFrameMs`, counted from the moment the client sends the input-voucher exchange | client cancels the job; the input voucher stands (section 11) |
| `interFrameTimeout` | client | 2 × the node's advertised `limits.maxInterFrameMs`; the clock runs only while the client awaits a frame that a voucher it has sent should release, or a replayed frame after a resume. It starts when the client sends the voucher exchange whose response should carry that frame, or the resume `hello` whose `welcome` should carry the replayed frames; it does not run while the client prepares its next voucher | after that long without the awaited frame the client marks the answer truncated and stops waiting (section 7) |
| `reconnectWindow` | node | 10 min | after it the node runs the abandoned-client procedure of docs/protocol/contracts-and-settlement.md §12 |

## 4. Node capability document

A node publishes one capability document per endpoint. Clients use it to confirm what the registry says, to learn the node's HPKE public key hash, its OHTTP key configuration, its padding parameters and limits, and to see optional roles. The registry stays authoritative for prices, offers and keys: a capability document that disagrees with `NodeRegistry` is a reason to skip the node, not a reason to trust the document.

Fields:

| Field | Meaning |
|---|---|
| `protocolVersions` | Accepted protocol versions, newest first |
| `operator` | The node's operator address (its identity in `NodeRegistry`) |
| `endpoint` | The endpoint as registered |
| `hpkePublicKey` | The current registered HPKE public key (X25519, base64); clients must check it against the latest `NodeRegistered`/`NodeUpdated` event and seal only to the registered key |
| `ohttpKeyConfig` | The node's OHTTP key configuration (RFC 9458 format, base64). It **must equal** the `ohttpKeyConfig` registered in `NodeRegistry`; a client encapsulates only to the registered configuration. A node publishes one configuration for every user and **must not offer a per-user key**, which would single a user out (evidence register §15 [U]) |
| `keyringHashes` | Hashes of older keys still on the keyring for unsettled sessions (docs/security/privacy-and-contexts.md §5), so a client can tell that a session sealed to a rotated key is still served |
| `relayPolicy` | `{acceptsRelayed: true}`. Always true for a conforming node: the gateway accepts exchanges from any relay authenticated as a registered operator (ADR 0014) and the reference client sends through nothing else |
| `creditSubmission` | `{submitsSpends: true, denominationIndexes[]}`: the node submits `openSessionFromCredit` for the listed denomination indexes (indexes into the escrow's append-only list, never wei values). A node that lists none cannot be paid by the reference client |
| `paddingBuckets[]` | The envelope and frame size buckets, in bytes, ascending; the client pads every envelope and the node every frame to the smallest bucket that fits (sections 6 and 7). The values are **unset** (section 14) |
| `tokenBatch` | `{minTokens, maxDelayMs}`: a frame is emitted once it holds at least `minTokens` output tokens or `maxDelayMs` has elapsed since the previous frame, whichever comes first, and always at `endOfJob` (section 7). The values are **unset** |
| `class` | Hardware class, one of `S`, `M`, `L`, `X`, decided by passing the per-class bars of the public class benchmark; it selects the price band. A class is not a tier |
| `maxTier` | The largest tier the operator benchmarked, `T0`–`T4`, a separate field. **Informational only.** It is never a gate: any class may appear in any model's pool |
| `offers[]` | One entry per model offered: `modelId`, `manifestHash`, `priceInPerMillion`, `priceOutPerMillion`, `modelBenchmarkHash`, and a `readiness` object the node signs stating that the model is loaded now (`loaded`, `signedAt`, `signature`). A non-zero `modelBenchmarkHash` is what puts the node in that model's pool (`prices[modelId]` in `NodeRegistry`); `readiness` is a liveness hint, not a contract fact |
| `modes[]` | Advertised privacy modes drawn from `standard`, `attested`, `verifiable`; must equal the registry's `modes` bitmask |
| `limits` | `maxContextTokens`, `maxOutputTokens`, `chunkTokens` (the node's `CHUNK_TOKENS`), `maxConcurrentJobsPerSession` (1 in v1, section 3), `maxTimeToFirstFrameMs`, `maxInterFrameMs` (the longest gap the node promises between two consecutive frames of one job; the client stops waiting after twice this), `maxEnvelopeBytes` |
| `roles` | Optional. `orchestration: {plannerModelIds[]}` advertises that the node serves planning, assessment, merging or synthesis for thin clients through an ordinary session (docs/protocol/orchestration.md §11). `shard` and `draft` are **experimental flags only**, meaningful solely in the Phase 3 verification spike with testnet-only prices; under mainnet parameters the reference client refuses both `model_sharding` and `cross_node_speculation` and ignores these flags. A shard holder holds no session and is never paid, in v1 or in the spike |
| `attestation` | Present only when `attested` is advertised: the quote format and a URL (fetched through the relay) from which the client obtains a fresh quote bound to its own nonce before sealing anything. The client never accepts a quote whose report data does not commit to `hpkePublicKey`, `ohttpKeyConfig` and its nonce; in attested mode both keys are generated inside the TEE (docs/adr/0010-anonymous-by-default.md) |
| `deterministicProfiles[]` | Present only when `verifiable` is advertised: identifiers of engine configurations the node has demonstrated to be byte-deterministic (docs/security/inference-verification.md) |
| `signature` | Operator signature over the whole document minus this field |

```json
{
  "type": "capability",
  "protocolVersions": ["comuns/0.1"],
  "operator": "0x00000000000000000000000000000000000000a1",
  "endpoint": "node-a.example",
  "hpkePublicKey": "BASE64_X25519_PUBLIC_KEY_PLACEHOLDER_A",
  "ohttpKeyConfig": "BASE64_RFC9458_KEY_CONFIG_PLACEHOLDER_A_EQUALS_REGISTRY",
  "keyringHashes": [],
  "relayPolicy": {
    "acceptsRelayed": true
  },
  "creditSubmission": {
    "submitsSpends": true,
    "denominationIndexes": [0, 1]
  },
  "paddingBuckets": ["BUCKET_BYTES_PLACEHOLDER_UNSET_1", "BUCKET_BYTES_PLACEHOLDER_UNSET_2", "BUCKET_BYTES_PLACEHOLDER_UNSET_3"],
  "tokenBatch": {
    "minTokens": "UNSET_PLACEHOLDER",
    "maxDelayMs": "UNSET_PLACEHOLDER"
  },
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

All identifiers in this document are synthetic placeholders; the prices are illustrative numbers chosen so the voucher arithmetic of section 8 can be followed by hand, and they are not a band or a price proposal (docs/economics/cost-and-pricing.md owns prices). The padding buckets and token batch values are placeholders for parameters no document sets. No denomination value appears anywhere; `denominationIndexes` are list positions.

**Pool enumeration is model-first.** A client lets the user pick a model, then enumerates the model's pool: every node whose `NodeRegistry` entry has `prices[modelId]` with a non-zero `modelBenchmarkHash`, read through the user's RPC or a community indexer from `OfferSet` events (docs/protocol/contracts-and-settlement.md §9). The client then fetches each candidate's capability document through a relay and ranks by price, measured speed, reputation, privacy mode and class. Any class may appear in any pool; a stronger class costs more for the same model because the bands are ordered; `maxTier` is displayed, never used to filter. A node whose `creditSubmission.denominationIndexes` does not include a denomination the client holds is skipped.

## 5. Session handshake

The handshake has two halves. The **credit flow** funds the session on-chain without a user transaction: the client proves ownership of one note and the node submits the spend. The **hello** then binds the exchanges to that session and lets both sides check the other's facts before anything is sealed. No account key, deposit key or login is in this handshake; the wallet acted only earlier, at `depositNote` (and, on opt-in, the deposit-key grant of [ADR 0016](../adr/0016-funding-edge-and-deposit-key.md), proposed).

**Key probe (before the spend).** Before step 1 of the credit flow, the client runs the `key_probe` / `key_probe_response` exchange of [ADR 0015](../adr/0015-node-key-possession.md) with the node it has chosen, and runs it again on a resume whenever the keys in the latest `NodeRegistered` or `NodeUpdated` event differ from the keys it pinned (`keyringHashes` is not the trigger). It reads `hpkePublicKey` and `ohttpKeyConfig` only from that latest event in its own relay-tunnelled chain view, never from the capability document. It HPKE-seals a fresh 32-byte challenge to `hpkePublicKey` under the probe's own HPKE `info` and AAD, which are separate from the job AAD of section 6, and sends it as an OHTTP request encapsulated to `ohttpKeyConfig` through a relay connection the gateway has authenticated (ADR 0014). The probe carries no `sessionSigner`, no session or job identifier and no client identifier. `key_probe_response` returns the challenge, `receiptPublicKey`, a receipt-key signature and a response MAC under a key exported from the probe's own HPKE context; the field list is ADR 0015's, and the canonical encodings and vectors belong to [CIP-0005](../cip/0005-phase-one-implementation.md).

**Receipt-key pinning.** The client accepts the response only if the challenge equals the one it sent and both the response MAC and the receipt-key signature verify. It then pins `hpkePublicKey`, `ohttpKeyConfig` and `receiptPublicKey` for the session, and requires every input receipt, every chunk receipt, `session_opened` and `welcome` to verify under the pinned receipt key. Any failure fails closed before any note is spent and before any prompt is sealed, with no retry against a different key and no downgrade.

**Credit flow.**

1. The client generates a fresh `sessionSigner` key for this session and a Semaphore v4 proof for the note it will spend: group scope `keccak256(chainId, escrow, denominationIndex)` and message `keccak256(node, relay, modelId, mode, sessionSigner, expectedPriceInPerMillion, expectedPriceOutPerMillion)`, both of which the contract recomputes itself and hashes as Semaphore does (docs/adr/0011-anonymous-credits.md; evidence register §15 [V]). The Merkle witness and the current root are read through a relay-tunnelled RPC or indexer, never from the deposit wallet's connection. Phone proving for the deepest circuit, Semaphore-32, is 143–2,146 ms [V] (evidence register §15); the group depth is a proof parameter in 1–32 [V]. Before proving, the client shows the group size it can observe for that denomination and warns below the threshold the CIP sets (`anonymity_set_below_threshold`, a client-side warning, section 10).
2. The client sends `credit_spend` through the relay: the protocol version, `node`, `relay` (the relay record's operator address, which the proof message binds), `modelId`, `mode`, `sessionSigner`, the expected prices, `denominationIndex`, `merkleTreeDepth`, `merkleTreeRoot`, `nullifier`, `points[8]`, a client nonce, and a `sessionSigner` signature over all of them. There is no refund commitment and no user address in the message.
3. The node verifies the proof against the group's verifier, checks `merkleTreeRoot` is the current root or a replaced root still inside `MERKLE_TREE_DURATION`, checks the `nullifier` is unspent, checks the denomination index is one it lists and that `relay` is a registered, non-deregistering relay other than itself, all **against its own RPC view** of `SessionEscrow` and `NodeRegistry`. Any failure is `credit_spend_rejected` with a reason (`unknown_root`, `spent_nullifier`, `bad_proof`, `unknown_denomination`; section 10) and nothing is consumed: the nullifier is stored only by the contract. On success the node submits `openSessionFromCredit(node, relay, modelId, mode, sessionSigner, expectedPriceInPerMillion, expectedPriceOutPerMillion, denominationIndex, merkleTreeDepth, merkleTreeRoot, nullifier, points)` and pays its gas (about 230–270k L2 gas is an estimate for Semaphore's own `validateProof`, not a measurement of this contract; evidence register §15 [U]).
4. The node replies `session_opened` with `txHash` and `sessionId`, signed. The reply is information: the client **confirms the session on-chain itself**, through a relay-tunnelled RPC or indexer read. `openSessionFromCredit` emits two events in one call (docs/protocol/contracts-and-settlement.md §11): `SessionOpened(sessionId, user, node, modelId, mode, sessionSigner, depositWei, priceInPerMillion, priceOutPerMillion, maxSpendWei)` with `user = address(0)`, and then `CreditSessionOpened(sessionId, node, relay, modelId, mode, sessionSigner, denominationIndex, nullifier)`. The client joins the two by `sessionId`, checks that `CreditSessionOpened` carries its own `nullifier`, `node`, `relay`, `modelId`, `mode`, `sessionSigner` and `denominationIndex`, and reads the copied prices from `SessionOpened` or from the session record. A `session_opened` without a matching `CreditSessionOpened` for its nullifier within `spendSubmitTimeout` is treated as a node that did not submit (section 13, R9).
5. **On-chain prices win.** The client compares the prices copied into the session on-chain — `priceInPerMillion` and `priceOutPerMillion` in `SessionOpened` or in the session record, read through the relay — with the disclosure sheet the user confirmed (docs/security/privacy-and-contexts.md §8.3). The proof message binds the expected prices and `openSessionFromCredit` reverts if they differ from the offer, so a mismatch means a node submitted something other than the client's proof; the client sends nothing further and closes the session (unilateral close, below). The session's `depositWei` and `maxSpendWei` are the denomination, `relay` and `relayFeeWei` are copied from the registry and `RELAY_FEE_WEI` at that moment, and `user` is `address(0)`.

```json
{
  "type": "credit_spend",
  "protocolVersion": "comuns/0.1",
  "node": "0x00000000000000000000000000000000000000a1",
  "relay": "0x00000000000000000000000000000000000000e1",
  "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01",
  "mode": "standard",
  "sessionSigner": "0x0000000000000000000000000000000000005e01",
  "expectedPriceInPerMillion": "20000000000",
  "expectedPriceOutPerMillion": "40000000000",
  "denominationIndex": 0,
  "merkleTreeDepth": 16,
  "merkleTreeRoot": "0x0000000000000000000000000000000000000000000000000000000000007001",
  "nullifier": "0x000000000000000000000000000000000000000000000000000000000000f001",
  "points": [
    "0x0000000000000000000000000000000000000000000000000000000000000001",
    "0x0000000000000000000000000000000000000000000000000000000000000002",
    "0x0000000000000000000000000000000000000000000000000000000000000003",
    "0x0000000000000000000000000000000000000000000000000000000000000004",
    "0x0000000000000000000000000000000000000000000000000000000000000005",
    "0x0000000000000000000000000000000000000000000000000000000000000006",
    "0x0000000000000000000000000000000000000000000000000000000000000007",
    "0x0000000000000000000000000000000000000000000000000000000000000008"
  ],
  "clientNonce": "BASE64_NONCE_PLACEHOLDER",
  "signature": "SESSION_SIGNER_SIGNATURE_PLACEHOLDER"
}
```

```json
{
  "type": "session_opened",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "txHash": "0x00000000000000000000000000000000000000000000000000000000000000aa",
  "node": "0x00000000000000000000000000000000000000a1",
  "relay": "0x00000000000000000000000000000000000000e1",
  "denominationIndex": 0,
  "relayFeeWei": "ILLUSTRATIVE_NO_VALUE_SET",
  "clientNonce": "BASE64_NONCE_PLACEHOLDER",
  "signature": "NODE_SIGNATURE_PLACEHOLDER"
}
```

`merkleTreeDepth` 16 is a synthetic example inside Semaphore's range, not a chosen depth; `sessionSigner` is the address of a fresh per-session key, never a user wallet. The `nullifier` is public on-chain once spent; it links nothing but this session to this note's group.

**Hello.**

1. The client sends `hello` as its own exchange before the job exchange, and again on a resume (section 3): the protocol version, the `sessionId`, the `modelId` and `mode` it expects, the HPKE key hash it is about to seal to, a client nonce, on a resume `lastReceivedFrameSeq` for every job it considers open (the highest frame `seq` it received for that job, or −1 if none), and a `sessionSigner` signature over `(chainId, escrow, sessionId, nodeOperator, clientNonce)`. The signature proves the client holds the `sessionSigner` registered for that session; nothing else proves it, because `sessionId` is public in the open event.
2. The node reads the session from `SessionEscrow` through its own RPC: `status` must be `open` (or `closing` before `closeDeadline`, in which case the node may still serve but tells the client); `node` must be this operator; `sessionSigner` must recover from the signature; `modelId` and `mode` must match what the client expects; and the copied `priceInPerMillion`/`priceOutPerMillion` are echoed back.
3. The node answers `welcome`: the copied prices as it read them; the effective cap `min(depositWei, maxSpendWei)` (the denomination, for a credit session) and `settledWei` as it read them on-chain; the last voucher it holds (`lastSeq` — the **voucher** counter — with `lastInputTokens`, `lastOutputTokens`, `lastCumulativeWei`); for the job it considers open (at most one, section 3), `lastFrameSeq`, the highest **frame** `seq` it has sent in that job; a keyed transcript check value `keccak256(commitKey ‖ transcriptHash)` (zero for a new session; the plain `transcriptHash` never travels outside encryption); the node nonce; and a node signature over the whole message. If the session is new, the counts are zero and the node states that it expects `commitKey` in the first envelope. The welcome is information for the client's comparison: **node-signed totals are never trusted** (step 5), and **the prices in it are informational** (step 4).
4. **On-chain prices win**, again. The client compares the prices copied into the session **on-chain** — read from the session record or from `SessionOpened` through a relay-tunnelled RPC or indexer — with the confirmed sheet. If they differ, the client sends nothing further and submits `closeSession(sessionId, signature)` through a relay or broadcaster, with a `sessionSigner` EIP-712 signature over `(chainId, escrow, sessionId, "close")`; `pendingWei` is recorded by `finalize` after `closeDeadline` and reclaimed with `claimChange` (section 12). The prices a node reports in `welcome`, in its capability document or anywhere else are informational and **never trigger a close**: a `welcome` whose prices differ from the on-chain record is a node that is lying or stale, which the client records and treats as a reason to stop using the node, but the deposit is not locked up behind `closeDeadline` on a node's say-so.
5. The client resumes **only from its own voucher log**, never from the node's figures. It computes the remaining allowance itself as the effective cap minus the highest `cumulativeWei` it has ever signed on this session, redeemed or not. If the node's `lastSeq` is lower than the client's last signed voucher, the client re-sends that voucher (a resend with the same `seq` and identical content is a no-op on the node, section 11). If the node claims a higher `seq` than the client ever signed, the `sessionSigner` is compromised or the client's log is lost; in either case the client signs nothing more on this session, uses the **unilateral close** — `closeSession` with its `sessionSigner` signature, no voucher, then `finalize` after `closeDeadline` (docs/protocol/contracts-and-settlement.md R8), both submitted through a relay or broadcaster — and, if the user wants to continue, opens a new session with a new note under a new, confirmed disclosure sheet version, because a new session is a new note and a new cap. A lost voucher log is never repaired from a welcome: the client would be signing for tokens it cannot account for.

```json
{
  "type": "welcome",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "protocolVersion": "comuns/0.1",
  "status": "open",
  "funding": "credit",
  "priceInPerMillion": "20000000000",
  "priceOutPerMillion": "40000000000",
  "effectiveCapWei": "DENOMINATION_WEI_NO_VALUE_SET",
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

A resume after a lost exchange repeats the same `hello`, possibly through a different relay; the node's `welcome` then carries the state in the middle of which the exchange dropped. The node retransmits, under their original frame `seq`, every frame of each open job from the client's `lastReceivedFrameSeq + 1` onward, together with any input receipt the client has not yet answered and any retained terminal frame (timeout, cancellation or error, section 3); the client re-sends its latest voucher. The two sides reconcile on their own records: the client ignores any retransmitted frame identical to one it already holds and signs only for what its own log does not yet cover.

The whole flow, from deposit to change, in one picture. On the core path the wallet appears once, at `depositNote`; an opt-in deposit key adds a public grant and its revocation ([ADR 0016](../adr/0016-funding-edge-and-deposit-key.md), proposed):

```mermaid
sequenceDiagram
    participant W as Wallet (EIP-1193)
    participant C as Client (sessionSigner, HPKE keys, note secrets)
    participant R as Relay (OHTTP, random from NodeRegistry)
    participant E as SessionEscrow (Arbitrum One)
    participant N as Node (OHTTP gateway)
    W->>E: depositNote(identityCommitment, denominationIndex) + denomination (the only wallet step)
    C->>R: OHTTP GET /comuns/v1/capability
    R->>N: forward (relay sees client address, not content)
    N-->>C: capability (offers, modes, limits, hpkePublicKey, ohttpKeyConfig, paddingBuckets, tokenBatch)
    C->>R: key_probe (challenge sealed to the registered hpkePublicKey, OHTTP to the registered ohttpKeyConfig, no sessionSigner, no client identifier)
    R->>N: forward on the relay's authenticated connection
    N-->>C: key_probe_response (challenge, receiptPublicKey, receipt signature, response MAC), client verifies and pins the keys
    C->>C: show disclosure sheet; user confirms version v; fresh sessionSigner; Semaphore proof (witness read through the relay)
    C->>R: credit_spend (denominationIndex, root, nullifier, points, node, relay, modelId, mode, sessionSigner, expected prices)
    R->>N: forward
    N->>E: verify proof and nullifier against own RPC view; openSessionFromCredit (node pays gas)
    E-->>N: SessionOpened(sessionId, user = address(0), node, modelId, mode, sessionSigner, depositWei, copied prices, maxSpendWei) then CreditSessionOpened(sessionId, node, relay, modelId, mode, sessionSigner, denominationIndex, nullifier)
    N-->>C: session_opened (txHash, sessionId)
    C->>R: read SessionOpened and CreditSessionOpened, joined by sessionId, through the relay (RPC or indexer); copied prices from SessionOpened or the session record
    C->>C: on-chain copied prices == sheet v? else closeSession via relay and stop; allowance from own voucher log
    C->>R: hello (sessionId, version, expected model/mode, sessionSigner signature)
    R->>N: forward
    N->>E: read session: status, node, sessionSigner, prices
    N-->>C: welcome (copied prices, effective cap, settledWei, lastSeq, lastFrameSeq per open job)
    C->>N: job envelope via R (HPKE to node key; padded to a bucket; commitKey in first job sealed; AAD incl. requestId, sheetVersion; signed by sessionSigner)
    N-->>C: input receipt via R (sessionId, jobId, jobInputTokens, cumulativeInputTokensAfter)
    C->>N: voucher seq 1 via R (inputTokens = cumulativeInputTokensAfter) if the counts match
    N-->>C: frame seq 0 via R, chunked OHTTP (HPKE to clientJobPublicKey; padded; chunk receipt sealed inside)
    C->>N: voucher seq 2 via R (cumulative, outputCommitment)
    N-->>C: frame seq k, endOfJob = true (receipt sealed inside)
    C->>N: voucher seq k+2 via R
    Note over C,N: more jobs on the same session, one at a time; cumulative counts never fall below a signed voucher
    C->>N: voucher final = true via R (cooperative close)
    N->>E: closeWithVoucher — credits node and relay (relay fee first), records pendingWei; no user balance
    C->>R: claimChange(sessionId, changeCommitments, denominationIndexes, sessionSigner signature) via relay or broadcaster
    R->>E: forward; fresh change notes enter their groups, dust to the node
    Note over C,E: unilateral close instead: closeSession with a sessionSigner signature via relay or broadcaster, then finalize after closeDeadline; pendingWei is the full remainder
```

## 6. Encrypted job message

A job is one request on one session. Its envelope is HPKE-sealed (base mode, DHKEM(X25519, HKDF-SHA256), ChaCha20-Poly1305) to the node's registered public key and signed, outside the AEAD, by the session's `sessionSigner`. The AAD tuple is the one of docs/security/privacy-and-contexts.md §6, unchanged by the anonymity redesign (only the context content AAD of section 9 changes), reproduced here in the `aad` object so that the node can reconstruct it; any mismatch between `aad` and the envelope's own fields is a reason to reject.

**Nothing that changes the job travels in the clear.** The response key `clientJobPublicKey` and every job parameter (`maxOutputTokens`, sampling settings, `stop`) live inside the HPKE plaintext, and because the `sessionSigner` signature covers `keccak256(enc ‖ ciphertext)` they are inside the signed digest too. A relay, a TLS-terminating proxy or a misconfigured front-end can therefore neither redirect the completion to a key of its own nor raise `maxOutputTokens` or change sampling: any edit breaks the AEAD tag or the signature, and the node rejects the envelope. What is outside the ciphertext is either in the AAD, public already, or checked against an on-chain fact (`mode` against the session's mode; `grantRef` against the sealed grant, which is authoritative, and against the optional registry anchor).

**Padding rule.** Before sealing, the client appends a `padding` field of zero bytes to the plaintext body so that the sealed envelope's wire size equals the smallest entry of the node's `paddingBuckets[]` that fits; an envelope larger than the largest bucket is split into upload fragments (below), each padded to a bucket. Padding is inside the AEAD, so the relay and the path see only bucket sizes; the node discards it and never tokenizes it. This narrows what request sizes reveal and does not remove it (evidence register §16 [V]); bucket sizes are unset (section 14).

| Field | Meaning |
|---|---|
| `sessionId`, `jobId` | The session and the client-chosen job id (idempotency key) |
| `enc` | HPKE encapsulated key |
| `ciphertext` | AEAD output over the plaintext body (shown below): `clientJobPublicKey`, `commitKey` (first job of the session only), `prompt`, `contextGrant` (or absent), `params`, `modelId`, `padding` |
| `aad` | The AAD tuple: `chainId`, `escrow`, `sessionId`, `jobId`, `requestId`, `sheetVersion`, `planId`, `taskId`, `role`, `contextId`, `contextVersion`, `direction`, `seq`, `endOfJob`. `planId` and `taskId` are zero for single-node execution |
| `grantRef` | Reference to the context grant carried inside the ciphertext: `contextId`, `fromVersion`, `toVersion`, the `contentHash` of each version, and `anchored`, true only if the client points the node at the optional `ContextSet` anchor in `ContextRegistry`. The node rejects the job if `grantRef` and the sealed grant disagree |
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
  "modelId": "0x0000000000000000000000000000000000000000000000000000000000000a01",
  "padding": "BASE64_ZERO_BYTES_TO_THE_NEXT_BUCKET_PLACEHOLDER"
}
```

`clientJobPublicKey` is a fresh per-job X25519 public key the node seals frames to, discarded when the job ends. `params.maxOutputTokens` is what the client will sign vouchers up to for this job.

The node, in this order: checks the signature against the `sessionSigner` recorded on-chain for the session (reject with `invalid_envelope_signature` otherwise, before decrypting anything); checks the AAD tuple; checks `mode` against the session; if `grantRef.anchored`, checks every `grantRef` version's `contentHash` against `ContextRegistry` or its `ContextSet` history; decrypts; checks that the sealed grant matches `grantRef`, that `keccak256(contextPubKey) == contextId`, and verifies the grant's `contextSignature`, its head-record chain and `nodeKeyHash` (section 9); discards the padding; tokenizes the prompt and the granted context with the manifest's pinned tokenizer; sends the input receipt of section 8; and starts prefill only when it holds the input voucher.

```json
{
  "type": "job",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
  "enc": "BASE64_HPKE_ENCAPSULATED_KEY_PLACEHOLDER",
  "ciphertext": "BASE64_AEAD_CIPHERTEXT_PADDED_TO_A_BUCKET_PLACEHOLDER",
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
    },
    "anchored": false
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
  "ciphertext": "BASE64_AEAD_CIPHERTEXT_PADDED_TO_A_BUCKET_PLACEHOLDER",
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

A multi-frame request (for example a large granted context's ciphertext attached in several upload frames, the default delivery of section 9) sends several envelopes with the same `jobId`, `direction = client-to-node`, `seq` increasing from zero and `endOfJob = true` on the last; each is padded to a bucket and signed. The node applies the same AAD and `seq` rules it expects the client to apply to its frames, and deduplicates each fragment by `(jobId, seq)`, never by `jobId` alone: job-level deduplication by `jobId` applies to billing — one input receipt, one count — not to the fragments that make up the job (section 3). The job is tokenized and receipted only once its last fragment (`endOfJob = true`) has arrived.

### 6.1 The client-side objects the metadata points at

`planId`, `taskId`, `wave`, `role`, `requestId` and `sheetVersion` refer to two objects that exist only on the client and never travel to a node, a relay or the chain: the **plan** and the **disclosure sheet**. They are shown here so that implementers of the node side know what the metadata means and what they will never receive. The plan format is owned by docs/protocol/orchestration.md and the sheet's field list by docs/security/privacy-and-contexts.md §8.3.

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

The disclosure sheet is computed from the plan before any session opens; its `version` is what `sheetVersion` in every AAD refers to. `recipients[]` has one entry per session, that is per distinct `(node, modelId)`; `roles[]` and `receives[]` are arrays because one session may serve several tasks. Each recipient carries `operatorReadable`, false only for an attested recipient whose quote the client has verified. Three numbers are kept apart: `counts.fullPrompt` is the number of distinct nodes **literally sent** the full prompt (one below: the planner); `readersOfFullPrompt` is the floor count of nodes that **receive prompt text**, including attested recipients because the bytes reach them, derived from the actual payloads (docs/security/privacy-and-contexts.md §8.2) and always ≥ `counts.fullPrompt` — the two executors below receive sub-tasks that embed the brief and the reviewer receives sub-task outputs that may quote the prompt, so all four are readers; and `counts.operatorReadable` is the number of recipients whose operator can read what they receive, with `counts.attestedRecipients` the rest. The `anonymity` object is **per session and specific** (docs/security/privacy-and-contexts.md §8.3): `relay` names the relay chosen for each session and the size of the eligible relay set it was drawn from; `funding` names the denomination index each session spends from, that group's observed size and whether it is below the warning threshold (unset, section 10); `contextLinkage` states, per granted `contextId` and node, whether that context was granted to the same node before and whether it is anchored on-chain. Observed sizes below are explicitly synthetic placeholders.

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
      "operatorReadable": true,
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
      "operatorReadable": true,
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
      "operatorReadable": true,
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
      "operatorReadable": true,
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
    "draftTokens": 0,
    "operatorReadable": 4,
    "attestedRecipients": 0
  },
  "readersOfFullPrompt": {
    "nodes": 4,
    "operators": 4
  },
  "anonymity": {
    "transport": "every hop through an OHTTP relay; no direct client-to-node path",
    "relay": [
      {
        "node": "0x00000000000000000000000000000000000000c3",
        "relay": "0x00000000000000000000000000000000000000e1",
        "eligibleRelaySetSize": "OBSERVED_PLACEHOLDER"
      },
      {
        "node": "0x00000000000000000000000000000000000000a1",
        "relay": "0x00000000000000000000000000000000000000e2",
        "eligibleRelaySetSize": "OBSERVED_PLACEHOLDER"
      },
      {
        "node": "0x00000000000000000000000000000000000000b2",
        "relay": "0x00000000000000000000000000000000000000e1",
        "eligibleRelaySetSize": "OBSERVED_PLACEHOLDER"
      },
      {
        "node": "0x00000000000000000000000000000000000000d4",
        "relay": "0x00000000000000000000000000000000000000e3",
        "eligibleRelaySetSize": "OBSERVED_PLACEHOLDER"
      }
    ],
    "funding": [
      {
        "node": "0x00000000000000000000000000000000000000c3",
        "denominationIndex": 1,
        "observedGroupSize": "OBSERVED_PLACEHOLDER",
        "belowThreshold": "THRESHOLD_UNSET_PLACEHOLDER"
      },
      {
        "node": "0x00000000000000000000000000000000000000a1",
        "denominationIndex": 0,
        "observedGroupSize": "OBSERVED_PLACEHOLDER",
        "belowThreshold": "THRESHOLD_UNSET_PLACEHOLDER"
      },
      {
        "node": "0x00000000000000000000000000000000000000b2",
        "denominationIndex": 0,
        "observedGroupSize": "OBSERVED_PLACEHOLDER",
        "belowThreshold": "THRESHOLD_UNSET_PLACEHOLDER"
      },
      {
        "node": "0x00000000000000000000000000000000000000d4",
        "denominationIndex": 1,
        "observedGroupSize": "OBSERVED_PLACEHOLDER",
        "belowThreshold": "THRESHOLD_UNSET_PLACEHOLDER"
      }
    ],
    "contextLinkage": [
      {
        "contextId": "0x000000000000000000000000000000000000000000000000000000000000c001",
        "node": "0x00000000000000000000000000000000000000a1",
        "grantedToThisNodeBefore": true,
        "anchored": false
      },
      {
        "contextId": "0x000000000000000000000000000000000000000000000000000000000000c001",
        "node": "0x00000000000000000000000000000000000000b2",
        "grantedToThisNodeBefore": false,
        "anchored": false
      }
    ]
  },
  "totalCapWei": "ILLUSTRATIVE_NO_VALUE_SET",
  "l2GasEstimate": "SHOWN_SEPARATELY_NEVER_FOLDED_INTO_totalCapWei",
  "experimental": false
}
```

The sheet JSON is normative: every table or banner a client shows is generated from it and must match it exactly. `counts` matches `receives[]` node by node — one node is sent the full prompt, two a sub-task, one other nodes' outputs — and each node is counted under exactly one payload kind. `readersOfFullPrompt` is the separate floor: the sub-task executors and the reviewer-and-merge node are readers because their payloads were derived from the prompt and the client did not verify they contain none of it (docs/security/privacy-and-contexts.md §8.2). The headline banner is computed from `counts.operatorReadable` alone: "4 nodes can read your prompt". When `counts.attestedRecipients > 0` the headline adds "M more process it inside a TEE and should not be able to read it" with `M = counts.attestedRecipients`; `readersOfFullPrompt` is shown beside the headline as the floor and never shrinks because a recipient is attested. Each per-node line uses the verbatim banner sentence of docs/adr/0010-anonymous-by-default.md for its mode — standard: "This node can read your prompt and your answer. It should not learn who you are."; attested: "This node should not be able to read your prompt. A physical attack on the hardware can break that."; verifiable: "This node and the verifier you chose can read your prompt. They should not learn who you are." — and the relay sentence "The relay sees your network address and not your prompt. The node sees your prompt and not your network address." is shown with every sheet. The banner lists the payload kinds from `counts` without counting a node twice (docs/product/dapp-and-sdk.md §5). An attested request fails closed unless every plaintext recipient on the sheet is attested. Any change of node, model, data scope, price, cap, relay rule or reader set — including adding a verifier for verifiable mode on the result — creates a new sheet version that must be confirmed before any credit spend or job under it.

## 7. Streaming frames

The node streams the completion as HPKE frames sealed to `clientJobPublicKey`, one frame per chunk of at most `CHUNK_TOKENS` output tokens (the node's `limits.chunkTokens`), carried as chunks of the chunked OHTTP response of the voucher exchange that released them, or replayed after `welcome` on a resume (section 3). Each frame carries the AAD tuple with `direction = node-to-client`, a transport `seq` starting at zero, and `endOfJob = true` only on the last frame. Every frame carries the chunk receipt of section 8 **inside the sealed plaintext**: no hash of the chunk plaintext ever travels outside encryption, because a relay or a TLS-terminating proxy could otherwise hash candidate short answers, labels or numbers and identify the completion despite HPKE. Any hash that must appear outside encryption is keyed, `keccak256(commitKey ‖ chunk)`, and `commitKey` is known only to client and node.

**Padding and batching.** The node pads every frame plaintext with a `padding` field so that the sealed frame's wire size equals the smallest entry of its `paddingBuckets[]` that fits, and emits a frame only once it holds at least `tokenBatch.minTokens` output tokens or `tokenBatch.maxDelayMs` has elapsed since the previous frame, whichever comes first; the last frame of a job is emitted at once. A frame carries at most `chunkTokens` tokens; it may contain fewer than `minTokens` when `maxDelayMs` expires or the job ends. A capability document must advertise `minTokens ≤ chunkTokens`, and the client skips a node whose document does not. Both parameters are unset (section 14). They narrow what the relay and the path learn from sizes and inter-frame timing and do not close it: token-length and timing attacks on streamed LLM output remain partly effective after padding and batching (evidence register §16 [V]), and chunked OHTTP lets the relay and the gateway measure round-trip time in an interactive exchange (evidence register §15 [V]). The reference shape follows the draft's section 7.2 guidance: no request chunk depends on a response chunk within one exchange, which also avoids in-exchange replay of interactively generated request chunks (evidence register §15, recheck 2026-10-15, [V]). The gateway still links a session's exchanges through the session fields inside them and can time the gap between a response and the client's next exchange, which includes the client's round trip; that cross-exchange timing remains a residual (R8, T37, RR-40).

| Field | Meaning |
|---|---|
| `jobId`, `sessionId` | As in the job |
| `seq` | Transport sequence number of this frame, starting at 0 per job and per direction. This is never the voucher `seq`, a separate per-session counter starting at 1 |
| `enc` | HPKE encapsulated key for this frame's sender context (one per frame, or one per job with per-frame AEAD nonces — the reference choice is an open question, section 14) |
| `ciphertext` | AEAD output over the frame plaintext (shown below): the chunk `text`, `tokenCount`, for the last frame `finishReason` (`stop`, `length`, `cancelled`, `error`), the node-signed `receipt`, and `padding` |
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
  },
  "padding": "BASE64_ZERO_BYTES_TO_THE_NEXT_BUCKET_PLACEHOLDER"
}
```

`chunkHash` is the keccak256 of the chunk plaintext (docs/security/privacy-and-contexts.md §10); it is safe there only because the receipt is sealed. Receipts and vouchers count model tokens, never padding bytes. The frame on the wire:

```json
{
  "type": "frame",
  "sessionId": "0x0000000000000000000000000000000000000000000000000000000000005e01",
  "jobId": "0x0000000000000000000000000000000000000000000000000000000000000b01",
  "seq": 3,
  "enc": "BASE64_HPKE_ENCAPSULATED_KEY_PLACEHOLDER",
  "ciphertext": "BASE64_AEAD_CIPHERTEXT_PADDED_TO_A_BUCKET_PLACEHOLDER",
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

**Ordering and idempotency.** The client accepts a new frame only if its AAD matches the expected tuple and its `seq` is exactly the next expected value. A retransmitted frame whose `seq` the client has already received and whose bytes are identical to the frame it holds is **ignored, never a fatal error** — this is what makes resumption safe when the client received frame `n` but its voucher never reached the node. A frame with an already-received `seq` and different bytes, or a `seq` beyond the next expected value, is rejected and the client treats the stream as broken: it stops signing and sends `cancel` (section 10). The node never reorders and never retransmits a frame under a new `seq`; after a resume it resends, under their original `seq`, the frames of each open job from the client's `lastReceivedFrameSeq + 1` (section 5). The frame counter and the voucher counter are never confused: `welcome` reports `lastFrameSeq` per job for frames and `lastSeq` for vouchers.

**Finalization.** A job ends with exactly one frame carrying `endOfJob = true` and a `finishReason`. The client rejects anything that follows it for the same `jobId`. A `finishReason` of `length` means `maxOutputTokens` was reached; `cancelled` means the client's `cancel` was honoured; `error` means the node stopped and the body carries an error code from section 10. In every case the vouchers already signed stand; the client signs no voucher covering output it did not receive.

**Truncation detection.** A response that ends at the input-receipt boundary, or after a released chunk at a payment boundary (section 8: the node has sent the one chunk it may send unpaid and the next chunk is released by the client's next voucher exchange), is **not** truncation; the client sends the next voucher exchange, and `interFrameTimeout` (2 × the node's advertised `limits.maxInterFrameMs`) runs only while the client awaits a frame that a voucher it has sent should release, or a replayed frame after a resume; it starts when the client sends the voucher exchange whose response should carry that frame, or the resume `hello` whose `welcome` should carry the replayed frames, and it does not run while the client prepares its next voucher (section 3). A job is truncated when a frame that a sent voucher should release does not arrive within `interFrameTimeout`, when an exchange drops mid-frame, or when the node sends an error outside the stream. The client keeps the partial text, marks it truncated in the UI, and either resumes or cancels. A client that holds its voucher log resumes with a new `hello` and resends its latest voucher; the node resends from `lastReceivedFrameSeq + 1` under the original frame `seq`, identical duplicates are ignored, and normal signing continues for retransmitted chunks the log does not yet cover (section 11). The client signs nothing further for the session only when it has lost its voucher log (section 11, the unilateral close). A truncated job never silently becomes a complete answer.

## 8. Voucher exchange

Payment and delivery alternate in steps of one chunk. The node's unpaid exposure is one chunk; the user's exposure to a dishonest count is zero before prefill and one chunk during streaming; the loss that remains is stated at the end of this section. Nothing in this section changed with the anonymity redesign except who receives the settled value: on a credit session the first `relayFeeWei` of settled value goes to the relay and the rest to the node, and the unspent remainder becomes `pendingWei` rather than a user refund (docs/adr/0011-anonymous-credits.md).

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

**Step n — chunk receipt (node → client, sealed inside every frame).** Each frame's `receipt` is a usage claim: the session-cumulative input and output counts after this chunk and the hash of the chunk plaintext. The client checks the hash against the decrypted chunk, checks that `cumulativeOutputTokens` rose by exactly `tokenCount` and that `tokenCount` agrees with its own tokenizer tally of the chunk's **token text only** — receipts and vouchers count model tokens, never metadata bytes such as the receipt, the `finishReason`, the padding or any sealed side data — within a tolerance it sets (the reference client proposes zero tolerance for the pinned tokenizer and treats any disagreement as `output_count_mismatch`), extends `transcriptHash = keccak256(prev ‖ chunkHash)`, and signs the next cumulative voucher.

**Voucher (client → node).** The one canonical EIP-712 type of docs/protocol/contracts-and-settlement.md §8, signed by `sessionSigner` under the `SessionEscrow` domain:

`Voucher(bytes32 sessionId,uint64 seq,uint256 cumulativeWei,uint64 inputTokens,uint64 outputTokens,bytes32 outputCommitment,bool final)`

- `seq` starts at 1 and strictly increases per session.
- `inputTokens` and `outputTokens` are cumulative for the whole session, across all its jobs; they never fall.
- `cumulativeWei = (priceInPerMillion × inputTokens + priceOutPerMillion × outputTokens) / 1000000` with the session's copied prices, integer floor division, recomputed on-chain. With the illustrative prices of section 4 (20,000,000,000 and 40,000,000,000 wei per million), 1,200 input tokens and 236 output tokens give 24,000,000 + 9,440,000 = 33,440,000 wei.
- `outputCommitment = keccak256(commitKey ‖ sessionId ‖ seq ‖ transcriptHash)`, computed with this same voucher's `seq`, with `commitKey` the random 32-byte session key the client sent sealed in the session's first envelope; not checked on-chain; opening it to anyone discloses the session's output to them.
- `final` is true only on the closing voucher ("the client closes the session"). It is never the frame flag `endOfJob`. `redeemVoucher` rejects a `final` voucher; only `closeWithVoucher` accepts it.

**Two ways to close.** The **cooperative close** is the client signing a `final` voucher from its own log and the node calling `closeWithVoucher`, which credits the node (and the relay's share) and records `pendingWei = depositWei − settledWei` in one transaction. The **unilateral close** is `closeSession(sessionId, signature)` with a `sessionSigner` EIP-712 signature over `(chainId, escrow, sessionId, "close")`, submitted through a relay or broadcaster — no voucher, never a transaction from the deposit wallet — and `finalize` by anyone after `closeDeadline`; the node may still redeem its highest non-final voucher until then. Either way the client then reclaims `pendingWei` as change notes with `claimChange` (section 12). A client that has lost its voucher log uses only the unilateral close and signs nothing (section 11).

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

**Pause after one unpaid chunk.** The node sends chunk n+1 only after it holds the voucher covering chunk n. If the voucher does not arrive within `chunkVoucherTimeout` the node pauses the job; if it still does not arrive the node ends the job with `finishReason = error` and `unpaid_chunk_timeout`, keeps the highest voucher it holds and may redeem it at any time while that is legal. The node never streams ahead of payment by more than one chunk, and the reference node does not start prefill before the input voucher. Through a relay each voucher costs at least two HTTP requests (evidence register §15 [V]); under section 3 each voucher is one exchange whose response carries the chunk it releases, so the stream advances one exchange per chunk; whether the one-chunk exposure should widen to keep the stream smooth is an open question (section 14).

**Vouchers cover the acknowledged prefix.** A voucher — a chunk voucher, a closing voucher or a resend — may cover only the prefix of the transcript the client has acknowledged, and the node checks it against that prefix: it accepts a voucher whose counts and `outputCommitment` match the acknowledged prefix even when it has already sent one more chunk, and that unacknowledged chunk is simply unpaid — the node's one-chunk exposure, nothing more. A voucher whose `seq` equals the last accepted `seq` and whose content is identical is a no-op, never an error; a chunk in flight when such a resend arrives is covered by the next voucher. A voucher with an already-accepted `seq` and different content is rejected as not retryable, and the client treats the disagreement as it treats any unexplained mismatch (R4): it stops signing and closes.

**Cap and allowance; no top-up.** The effective cap is `min(depositWei, maxSpendWei)`, which on a credit session is the denomination. The client's **remaining allowance** is the effective cap minus the highest `cumulativeWei` it has signed in that session, redeemed or not — never the cap minus `settledWei`, which would count unredeemed vouchers as available. The client **never signs a voucher above the effective cap**: when the next chunk would take the running total past it, the client stops signing (`cap_exhausted`, section 10) and the node, which holds no voucher above the cap, pauses. `topUp` reverts on a credit session; the client closes with a `final` voucher and opens a new session with a new note (a new sheet version if anything else changed). The contract's rule that a voucher above the cap is paid only up to the cap, and the "re-sign the same cumulative totals under a new `seq`" recovery of docs/protocol/contracts-and-settlement.md §8, apply only if a voucher above the cap had been signed and was only partly paid — a situation the reference client never creates.

**What the client checks and does not check.** Automatic voucher signing verifies token counts against receipts and against what the client decrypted, and that the node declared the session's `modelId`. It does not judge answer quality. The chat view therefore has a Stop control (docs/product/dapp-and-sdk.md) that stops signing; the user then owes at most the chunks already received.

**Residual risk, stated plainly.** A node can redeem the input voucher and never run the prompt. The user's loss is bounded by that prompt's input fee; the remedy is to stop signing and record a reputation event; nothing in v1 refunds it.

## 9. Context grant message

A grant lets one node decrypt a range of versions of one context. A context is identified by a per-context signing key generated by the client from the operating-system CSPRNG, never the wallet key and never derived from it; `contextId = keccak256(contextPubKey)` (docs/adr/0012-contexts-without-a-wallet-link.md). The grant is carried inside the job envelope's ciphertext (section 6), and `grantRef` outside it tells the node which versions to expect and whether to consult the optional on-chain anchor. A grant belongs to the job that carries it: its idempotency key is `(jobId, contextId, fromVersion, toVersion, nodeKeyHash)` (section 3), so the second prompt of a chat that grants the same versions again is processed as a new grant for its new `jobId`. Its fields are those of docs/security/privacy-and-contexts.md §7 — `contextSignature` is EIP-712 typed data signed by the **context key**, never by a wallet and never by `sessionSigner`, over every grant field above it: `contextId`, `contextPubKey`, `fromVersion`, `toVersion`, the wrapped keys, `expiresAt` and `nodeKeyHash`. Each granted version also carries its signed head record `(contextId, version, contentHash, prevContentHash)` so the node can verify the hash chain without any registry; `headRecords[]` may additionally carry the signed head records of earlier versions, without their keys, so that a node seeing the context for the first time can verify the chain back to version 1. The message below adds only transport framing: per version, how the ciphertext reaches the node.

**Ciphertext delivery — inline by default, no SSRF.** The default, and the only delivery a node must support, is that the client uploads each granted version's ciphertext blob (`header ‖ ciphertext ‖ tag`) **inline in upload frames** of the same job: a multi-frame request (section 6) whose fragments are deduplicated by `(jobId, seq)`. An optional `blobUrl` lets the client point instead at a context host of its choosing, under rules the node applies before any connection is opened: the URL must be `https`; the host name must resolve to a public address — never a private, loopback, link-local, multicast or cloud-metadata range — and every redirect is re-checked against the same rule before it is followed; a size limit (at most `limits.maxEnvelopeBytes` per blob) and a time limit apply; the fetch happens **only after** the grant signature, `nodeKeyHash` and the session checks of section 6 have passed; and `contentHash` is verified before the blob is used. `blobUrl` is **never part of the signed grant fields**, so it carries no authority, and a node may refuse it altogether (answering `blob_url_refused`, after which the client re-sends the job with the blob inline). A node that implements `blobUrl` without these restrictions lets a correctly signed grant turn it into a proxy for requests to its own internal services, which no later hash check can undo. A node fetching a `blobUrl` connects to the host directly, so the host learns the node's address, never the client's.

```json
{
  "type": "context_grant",
  "contextId": "0x000000000000000000000000000000000000000000000000000000000000c001",
  "contextPubKey": "BASE64_CONTEXT_SIGNING_PUBLIC_KEY_PLACEHOLDER",
  "fromVersion": 5,
  "toVersion": 6,
  "anchored": false,
  "versions": [
    {
      "version": 5,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a5",
      "prevContentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a4",
      "headSignature": "CONTEXT_KEY_EIP712_HEAD_RECORD_SIGNATURE_PLACEHOLDER_V5",
      "delivery": "inline",
      "blobUrl": null,
      "wrappedKey": "BASE64_HPKE_WRAPPED_K5_TO_NODE_KEY_PLACEHOLDER"
    },
    {
      "version": 6,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a6",
      "prevContentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a5",
      "headSignature": "CONTEXT_KEY_EIP712_HEAD_RECORD_SIGNATURE_PLACEHOLDER_V6",
      "delivery": "url",
      "blobUrl": "https://host.example/blobs/0x000000000000000000000000000000000000000000000000000000000000c0a6",
      "wrappedKey": "BASE64_HPKE_WRAPPED_K6_TO_NODE_KEY_PLACEHOLDER"
    }
  ],
  "headRecords": [
    {
      "version": 1,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a1",
      "prevContentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
      "headSignature": "CONTEXT_KEY_EIP712_HEAD_RECORD_SIGNATURE_PLACEHOLDER_V1"
    },
    {
      "version": 2,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a2",
      "prevContentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a1",
      "headSignature": "CONTEXT_KEY_EIP712_HEAD_RECORD_SIGNATURE_PLACEHOLDER_V2"
    },
    {
      "version": 3,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a3",
      "prevContentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a2",
      "headSignature": "CONTEXT_KEY_EIP712_HEAD_RECORD_SIGNATURE_PLACEHOLDER_V3"
    },
    {
      "version": 4,
      "contentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a4",
      "prevContentHash": "0x000000000000000000000000000000000000000000000000000000000000c0a3",
      "headSignature": "CONTEXT_KEY_EIP712_HEAD_RECORD_SIGNATURE_PLACEHOLDER_V4"
    }
  ],
  "expiresAt": 1791986400,
  "nodeKeyHash": "0x000000000000000000000000000000000000000000000000000000000000d0a1",
  "contextSignature": "CONTEXT_KEY_EIP712_SIGNATURE_PLACEHOLDER"
}
```

`delivery`, `blobUrl` and `headRecords[]` are transport framing outside the signed grant fields (version 6 above shows the optional URL form; version 5 the default; `headRecords[]` carries ancestor head records without keys, each individually signed by the context key). Rules the node applies, in this order: check `keccak256(contextPubKey) == contextId` (`context_key_mismatch` otherwise, before anything else about the context is believed); verify `contextSignature` under `contextPubKey`; check that `nodeKeyHash` is the hash of a key on its keyring; verify the head-record chain **back to version 1**, whose `prevContentHash` is zero: for every version `v` from `toVersion` down to 1 the node needs a head record for exactly version `v` whose `headSignature` verifies under `contextPubKey`, taken from the grant's `versions[]`, from the grant's `headRecords[]`, or from records it verified in an earlier grant for this `contextId` and kept, and the record's `prevContentHash` must equal the `contentHash` of the record for exactly version `v − 1` (never of the version the node last held). A grant that omits earlier head records is accepted only if the node already holds verified records for them or, when `anchored`, the `ContextSet` history gives every missing `contentHash`; otherwise it fails with `context_hash_mismatch`. A repeated grant of a range the node already holds must still pass these checks, reusing the kept records; if `anchored`, check that each granted version's `contentHash` is what `ContextRegistry` or its `ContextSet` history records for that version; for each version take the blob from the job's upload frames or, only if it accepts `blobUrl` and the URL passes the rules above, fetch it; check that `keccak256(header ‖ ciphertext ‖ tag)` equals `contentHash`; check the content AAD `contextId ‖ v ‖ prevContentHash` version by version (the owner field of the earlier design is gone); unwrap exactly the keys given; use them only within the range and before `expiresAt` (`uint64` unix seconds, never a block number); discard them at `expiresAt` or at job end, whichever is earlier. Context tokens are input tokens and appear in the input receipt.

Without an anchor the node trusts the signed chain, and the client trusts the context host: with the chain no longer the default anchor, the context host is trusted for sequencing as well as for availability (docs/adr/0012-contexts-without-a-wallet-link.md). Clients persist every accepted head checkpoint in the vault and in the identity-key backup, and reject any head behind a checkpoint they hold. The limits of an unanchored context, stated plainly: a host can still equivocate between two devices that have never compared checkpoints, serving each a different fork; and a device restored from a stale backup accepts a head that a newer device would reject until the two devices sync. Whenever a globally consistent multi-device head is promised, an anonymous public anchor is required: `setContext` submitted by a broadcaster, never by the user's wallet. A node that receives grants for the same `contextId` across sessions can link those sessions; the disclosure sheet's `anonymity.contextLinkage` says so.

Errors: a key whose hash is not `contextId`, or a grant or head-record signature that does not verify under it, is `context_key_mismatch`; a hash that does not match, a broken chain, or a chain that cannot be verified back to version 1, is `context_hash_mismatch`; a version the anchor does not know, or a grant for a version behind a head the node was told to use, is `stale_version`; a grant past `expiresAt` is `grant_expired`; a `nodeKeyHash` not on the keyring is `grant_key_mismatch`; a `blobUrl` the node does not accept, or that fails the destination, size or time rules, is `blob_url_refused` (retryable with the blob inline).

## 10. Cancellation and errors

**Cancel (client → node).** The client may cancel a job at any time. The node stops generating, sends one last frame with `finishReason = cancelled` and `endOfJob = true` carrying the receipt for whatever it had already produced up to the previous chunk boundary (in the response of the `cancel` exchange, or retained for the client's next exchange for that job, section 3), and expects no voucher beyond the last chunk the client acknowledged (`lastAcknowledgedFrameSeq`): a chunk sent but not acknowledged is unpaid (section 8, acknowledged prefix). A cancel is idempotent by `jobId`.

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

**Error (either direction).** One shape for every error. `retryable` tells the receiver whether the identical message may be resent (section 11); `scope` says whether the job, the session or the request is affected. `credit_spend_rejected` carries its reason in `detail`.

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
| `attestation_failed` | client | Quote invalid, measurement not on the published list, report data not bound to `hpkePublicKey`, `ohttpKeyConfig` and the client nonce, or collateral expired | request | no envelope sealed; if a session was opened, `closeSession` |
| `relay_unavailable` | client | No registered relay with `unlockAt == 0` whose operator differs from the node's answered; the request fails closed and the client never connects to the node directly | request | no spend sent, no session opened |
| `relay_is_node_operator` | client or contract | The chosen relay record's operator equals the node's operator; the client skips it and `openSessionFromCredit` would revert | request | no spend sent |
| `anonymity_set_below_threshold` | client (warning) | The observable group size for the chosen denomination is below the threshold the CIP sets; the client shows the size and asks before proving; no authoritative minimum exists (evidence register §15 [U]) | request | nothing sent until the user decides |
| `credit_spend_rejected` | node | The node will not submit the spend: `unknown_root` (not the current root nor a replaced root inside `MERKLE_TREE_DURATION`), `spent_nullifier`, `bad_proof`, or `unknown_denomination` (an index the node does not list or the escrow does not know) | request | this rejection consumes nothing. For `spent_nullifier`, the client reconciles the existing spend through relay-tunnelled chain reads (`CreditSessionOpened` or `NoteRagequit` for that nullifier) and does not mark the note spendable. Other failures leave the note spendable only if its nullifier remains unused on-chain |
| `band_mismatch` | client | The node's current prices are outside the band for (model tier, node class), so `openSessionFromCredit` would revert; shown before any spend | request | no session opened |
| `price_mismatch` | client | Prices copied into the session **on-chain** (session record or the open event) differ from the confirmed sheet (handshake step 5); prices a node reports in `welcome` never raise it | session | `closeSession` with the `sessionSigner` signature; nothing signed |
| `no_offer_for_model` | client or node | The node has no offer (zero `modelBenchmarkHash`) for the model, so it is not in the pool | request | no session opened |
| `pool_cannot_fill_confirmed_set` | client | A node on the confirmed sheet is no longer in the pool, is deregistering, or refused admission, and no pre-confirmed fallback exists; the whole request fails closed | request | sessions already opened are closed with `closeSession` or a `final` voucher |
| `cap_exhausted` | client or node | The next chunk would take the signed total past `min(depositWei, maxSpendWei)`; the client signs nothing above the cap and the node pauses; `topUp` reverts on a credit session, so the client closes and opens a new session with a new note | session | every signed voucher stands |
| `model_not_loaded` | node | The node's offer exists but the process does not have the model loaded now (stale offer) | session | nothing charged if no input receipt was signed for; otherwise the input voucher stands |
| `context_key_mismatch` | node | `keccak256(contextPubKey) ≠ contextId`, or a grant or head-record signature does not verify under `contextPubKey` | job | no input receipt, nothing charged |
| `context_hash_mismatch` | node | A granted blob does not hash to its `contentHash`, the head-record chain is broken or cannot be verified back to version 1 (a missing ancestor record the node does not hold and no anchor supplies), or an anchored `contentHash` is not what the registry or its `ContextSet` history records | job | no input receipt, nothing charged |
| `stale_version` | node | The grant names a version the anchor does not know, or the client sent a version behind the head it asked the node to use; the client re-reads the head, rebases its edit and publishes the next version | job | nothing charged |
| `grant_expired` | node | `expiresAt` is in the past | job | nothing charged |
| `grant_key_mismatch` | node | `nodeKeyHash` is not on the node's keyring | job | nothing charged |
| `blob_url_refused` | node | The node does not accept `blobUrl`, or the URL fails the destination, redirect, size or time rules of section 9 | job | nothing charged; the client re-sends with the blob inline |
| `session_closed` | node | The session is `closing` past `closeDeadline`, or `settled`; nothing more can be served or redeemed | session | vouchers already redeemed stand; the remainder is `pendingWei`, reclaimed by `claimChange` |
| `stale_disclosure_sheet` | client | The plan changed (node added, scope widened, cap raised, price changed, relay rule changed) after the user confirmed, or an envelope would carry a `sheetVersion` with no recorded confirmation; the client sends nothing until the sheet is re-shown and signed for | request | signed vouchers stand; no new job |
| `unsupported_execution_feature` | client | A requested feature is not available: the pool has no node for a required role, or the feature is experimental and no testnet price exists | request | no session opened |
| `verifiable_with_cross_node_speculation` | client | Verifiable mode requires byte-identical re-execution; cross-node speculation does not guarantee it; the combination fails explicitly | request | no session opened |
| `invalid_envelope_signature` | node | The envelope's `sessionSigner` signature does not verify against the session's recorded signer; rejected before decryption | job | nothing charged |
| `input_count_mismatch` | client | `jobInputTokens` differs from the client's own tokenization, or `cumulativeInputTokensAfter ≠ lastInputTokens + jobInputTokens` | job | nothing signed for this job |
| `output_count_mismatch` | client | A chunk receipt's hash or counts disagree with the decrypted chunk | job | vouchers up to the previous chunk stand |
| `unpaid_chunk_timeout` | node | No voucher for the last chunk within `chunkVoucherTimeout` | job | the node keeps and may redeem its highest voucher |
| `unknown_session` | node | The session is not in `SessionEscrow`, or its `node` is another operator | session | nothing |

## 11. Retry semantics

**When an identical request may be resent.** A `credit_spend` may be resent byte for byte while no `session_opened` has arrived: its nullifier makes it idempotent, and a node that already submitted it answers with the same `session_opened`. A job envelope, or any fragment of a multi-frame one, whose `jobId` the node has not yet answered with an input receipt may be resent byte for byte: the node deduplicates each fragment by `(jobId, frameSeq)`, bills the job once by `jobId`, and answers once. A voucher may always be resent: `(sessionId, seq)` makes it idempotent — a voucher whose `seq` equals the last accepted `seq` and whose content is identical is a no-op, never an error, and the contract likewise ignores `seq ≤ lastSeq` (docs/protocol/contracts-and-settlement.md §8); the node checks every voucher against the prefix the client acknowledged (section 8). A `cancel` may be resent. A `hello` may be resent with a fresh nonce, through the same or a different relay.

**When a new `jobId` and a new envelope are required.** Once the node has sent an input receipt for a `jobId`, that job is defined, and the client has either signed for it or abandoned it. Any change to the prompt, the granted context, the parameters, the mode or the orchestration metadata is a new job: a new `jobId`, a fresh per-job keypair, a fresh HPKE context, a fresh AAD tuple and a fresh signature. Replaying an old envelope under a new `jobId` is impossible by construction because `jobId` is in the AAD and in the signed digest.

**How duplicate billing is prevented.** Vouchers are cumulative and the node is paid at most `min(cumulativeWei, cap)` for the whole session, so no repetition of any message can pay twice. A resent envelope receives the same input receipt with the same `cumulativeInputTokensAfter`; the node never raises its cumulative input for a `jobId` it already counted. A resent frame carries the same `seq` and the same receipt; the client never signs two vouchers for one chunk because the second has nothing new to add to the cumulative counts. A resent spend cannot open two sessions because the contract stores the nullifier. **An abandoned job leaves no trace in the counts** (section 8, unsigned receipts are void): if the client does not sign the input voucher for a job — Stop, `input_count_mismatch` or `inputVoucherTimeout` — that job's tokens never enter the cumulative counts; the node's next input receipt on the session is `lastSignedInputTokens + newJobInputTokens`, computed from the highest voucher it holds, so the client's check `lastInputTokens + jobInputTokens` passes for the next job and the session continues. Counts never fall below a signed voucher; they simply never rose for the unsigned job. A node that nevertheless carried the abandoned job's tokens forward would fail the client's check on every later job and earn nothing more on the session — the client signs nothing it cannot account for and closes.

**Retry after a client-side failure.** If the client lost its job exchange before receiving the input receipt, it starts a new exchange (through any eligible relay) and resends the envelope (idempotent). If a voucher exchange dropped mid-frame, or the frame a sent voucher should release did not arrive within `interFrameTimeout` (section 7), the client holding its voucher log resumes with a new `hello` carrying `lastReceivedFrameSeq` per open job and resends its latest voucher; the node resends from `lastReceivedFrameSeq + 1` under the original frame `seq` — retransmitted frames keep their `seq` — and the client ignores any retransmitted frame identical to one it already holds, then continues normal signing for the retransmitted chunks its log does not yet cover. If the client has signed a voucher the node never received, it resends its latest voucher; the counts are cumulative so order does not matter, and a resend the node already holds is a no-op. In every case the client resumes from **its own voucher log**: it never adopts the node's `lastInputTokens`, `lastOutputTokens` or `lastCumulativeWei`. "Signs nothing further" (section 7) applies only when that log is lost; the client then signs nothing more on that session: it uses the unilateral close — `closeSession` with its `sessionSigner` signature through a relay or broadcaster, no voucher — anyone calls `finalize` after `closeDeadline`, `pendingWei` is reclaimed with `claimChange`, and further work needs a new session, which is a new note and a new cap and therefore a new disclosure sheet version confirmed before the next credit spend.

**Retry after a node-side failure.** If the node answers with `retryable = true`, the identical message may be resent after a backoff the client chooses. If it answers `model_not_loaded`, `session_closed` or an `unknown_session`, the client stops using that session. If it answers `credit_spend_rejected` with `unknown_root`, the client re-reads the root through the relay and re-proves; with `spent_nullifier` the client checks on-chain whether a session already exists for that nullifier before treating the note as lost (section 13, R9).

**A retry on a different node needs a new session.** A session names one node and its HPKE key, and the credit proof's message binds the node; nothing sealed or proven for node A can be given to node B. To retry on node B the client must open a new session with B (a new proof over a note, submitted by B), seal a new envelope to B's key under a new `jobId`, and sign new vouchers for B. In a plan, B must already be on the confirmed disclosure sheet (as a pre-confirmed fallback); if it is not, the sheet is re-shown and the user signs again before anything is sent to B. The vouchers signed for node A stand: A is paid for what it delivered, and the remainder of A's session becomes `pendingWei` through `closeWithVoucher` or `finalize` and returns as change notes.

## 12. Settlement states visible to the client

The client shows the user where each job and each session stands. None of these states is a promise of L1 finality; "settled" means L2 inclusion under the single sequencer (docs/protocol/contracts-and-settlement.md §7). Every chain read behind these states is a relay-tunnelled RPC or indexer query; the client never polls the chain for its sessions from a connection that could be tied to the deposit wallet.

| State | Level | Meaning | What the user sees |
|---|---|---|---|
| `note_in_flight` | session | `credit_spend` was sent and no `CreditSessionOpened` with its nullifier is visible yet | the note is reserved for this node until the event appears or `spendSubmitTimeout` expires (section 13, R9) |
| `opened` | session | `CreditSessionOpened` with the client's nullifier is visible, and the `SessionOpened` with the same `sessionId` carries the confirmed prices | the session is funded by one note; the cap is the denomination; nothing is charged yet |
| `delivered` | job | The `endOfJob` frame arrived and every chunk receipt checked | the answer is complete; the running total shows what has been signed for |
| `voucher_accepted` | voucher | The node acknowledged the signed voucher in its exchange response | the amount is owed but nothing is on-chain yet; if the node vanished now it could still redeem up to this voucher |
| `redeemed` | voucher | A `VoucherRedeemed` event for a `seq` at or above this voucher is visible — that is, the transaction is **L2-included** under the sequencer | the amount is credited on-chain, the first `relayFeeWei` of it to the relay and the rest to the node; "L2-included" is distinct from L1 finality, which the client may optionally wait for |
| `settled` | session | A `SessionSettled` event is visible (`closeWithVoucher` or `finalize`) | the node's credit, the relay's fee and `pendingWei = depositWei − settledWei` are recorded; nothing further can be charged; `pendingWei` is the user's refund, waiting to be claimed as change |
| `change_claimable` | session | `pendingWei > 0` on a `settled` session | a Claim change control is offered: the client decomposes `pendingWei` greedily into at most `MAX_CHANGE_NOTES` fresh notes from the denomination list, generates a fresh identity per note, stores the secrets durably, and submits `claimChange(sessionId, changeCommitments, denominationIndexes, signature)` through a relay or broadcaster; the dust below the smallest denomination goes to the node and is shown as such |
| `change_claimed` | session | A `ChangeNoted(sessionId, changeCommitments, denominationIndexes, dustWei)` event is visible (docs/protocol/contracts-and-settlement.md §11) and `pendingWei` is zero | the new notes appear in the client's note list; the client delays spending them (delay unset) because a change note spent at once is linkable by timing (evidence register §15 [V]) |
| `closing` | session | `SessionClosing` is visible | until `closeDeadline` the node may still redeem; after it, `finalize` records the remainder as `pendingWei` |
| `truncated` | job | A frame that a sent voucher should release did not arrive within `interFrameTimeout`, an exchange dropped mid-frame, or the node sent an error outside the stream (section 7); a response that ends at the input-receipt boundary or at a payment boundary is not this state (section 3) | the partial answer is marked; the signed vouchers for received chunks stand; nothing is owed for the missing tail; a client holding its voucher log may resume with a new `hello` (section 11) |

There is no `withdrawable` state for the user: a credit session has no `user` balance, and the refund is change notes, not a withdrawal. `withdraw()` is for nodes and relays. A zero-use session (`settledWei == 0`) makes the whole denomination `pendingWei`, claimable in full as one note of the same denomination.

Application-level completion (`delivered`) and economic completion (`settled`) are different events and the client never conflates them; in particular a user who sees `delivered` has not yet been charged on-chain, and a user who sees `settled` cannot be charged more.

## 13. Risks

### R1 — Node redeems the input voucher and never runs the prompt **[RISK] · Low**

The input voucher is signed before prefill and is not reversible. Loss bounded by one prompt's input fee; mitigation is to stop signing and record a reputation event. Stated plainly, not solved; the credit redesign does not change it.

### R2 — Client and node tokenizers disagree **[RISK] · Medium**

If the manifest's pinned tokenizer is built differently on the two sides, every input receipt fails the client's check and no job can be paid for. Mitigation: a tokenizer test vector in the model manifest; the client refuses the session before the credit spend if its own tokenizer fails the vector (open question in docs/security/privacy-and-contexts.md §14).

### R3 — Stale capability document or stale offer **[RISK] · Medium**

A capability document can say `loaded: true` for a model the process has since unloaded, and an offer can outlive the model. `openSessionFromCredit` succeeds, the node answers `model_not_loaded`, and the note sits in the session until `closeSession`, `finalize` and `claimChange`. No money is lost; the node's gas, the client's time and a round trip through change are. Mitigation: the client requests admission in the handshake before sending any job and, where the user allows, before the spend; indexers downrank nodes whose sessions settle with zero `settledWei`.

### R4 — Session state loss on the node **[RISK] · Medium**

A node that loses its in-memory session state (pending receipt, `transcriptHash`, keyring) cannot continue a session correctly. Mitigation: the node keeps `commitKey`, the transcript chain and the highest voucher in persistent, encrypted local storage for the life of the session (until settled), so a restart can still redeem; per-job secrets are separate and discarded at job end; after a resume the `welcome` message is signed and the client compares it with its own voucher log, which alone decides what it signs next, and closes the session on any disagreement it cannot explain by a voucher the node has not yet received.

### R5 — Metadata in `orchestration` fields leaks the shape of a plan **[RISK] · Low**

`planId`, `taskId`, `role` (AAD-bound) and `wave` (advisory, unbound) tell a node that it is part of a larger request, how large, and in which position. They never carry another node's plaintext. Mitigation: none beyond saying so; the same shape is inferable on-chain from the timing of the sessions (docs/security/privacy-and-contexts.md §9).

### R6 — Protocol downgrade through version negotiation **[RISK] · Low**

Version negotiation could be abused to force an older message format. Mitigation: the cipher suite and the OHTTP key configuration are not negotiable; a major version change requires a CIP; the client refuses any version older than the one it was built against unless the user opts in.

### R7 — Unaudited implementation **[RISK] · High**

No implementation of this protocol exists and no audit of the design has been performed; the `hpke` crate the reference node intends to use reports no paid audit (evidence register §4 [V]). Mitigation: the review plan of docs/security/privacy-and-contexts.md §12, which is unfunded and unscheduled.

### R8 — Relay–node timing correlation **[RISK] · Medium**

A relay and a node that collude, or one operator holding both roles under two addresses (the contract refuses one address, not one person), can match the client address the relay sees with the session the node serves by timing and sizes. Chunked OHTTP lets either party measure round-trip time in an interactive exchange, and timing side channels have been found in a shipping IP-blinding relay (evidence register §15, §16 [V]). The reference shape follows the draft's section 7.2 guidance: no request chunk depends on a response chunk within one exchange, which also avoids in-exchange replay of interactively generated request chunks (evidence register §15, recheck 2026-10-15, [V]). The gateway still links a session's exchanges through the session fields inside them and can time the gap between a response and the client's next exchange, which includes the client's round trip; that cross-exchange timing remains a residual (R8, T37, RR-40). Padding buckets and token batching narrow the channel and do not close it; a client that keeps one relay per session gives the relay a whole-session view (section 14). Stated as a residual.

### R9 — A node that refuses, or silently delays, submitting the spend **[RISK] · Medium**

A node that answers `credit_spend_rejected` consumes nothing. A node that accepts the proof and never submits it costs the client `spendSubmitTimeout`; the client then re-proves the same note to another node, and because the nullifier is stored only on-chain the first node's late submission would revert. The gap is the window in between: the first node holds a valid proof bound to itself, the relay and this `sessionSigner`, and may submit it later, opening a session the client did not expect. The client therefore keeps the note marked in flight until either a session for its nullifier appears (which it then closes unilaterally and reclaims as change, paying nothing) or the note is respent elsewhere, and it never discards a `sessionSigner` key while a proof naming it is outstanding. Who bears gas for a spend the node declines is open (section 14).

## 14. Open questions

1. **HPKE context per frame or per job.** Whether each frame carries its own `enc` (simplest, larger) or one HPKE context per job is reused with per-frame AEAD nonces (smaller, needs careful nonce handling); the reference choice must be fixed before test vectors are published.
2. **Relay choice per request or per session.** A new random relay per exchange spreads one session's traffic across relays, so no single relay sees a whole session, at the cost of a fresh OHTTP context each time; one relay per session keeps the resume path simple and gives that relay the session's full timing profile (R8). The reference client's choice is open. Proposed resolution: [ADR 0014](../adr/0014-relay-authentication-to-gateways.md) (per exchange; fee relay fixed by the spend).
3. **Chunked OHTTP status.** Rechecked 2026-10-15 as a [CIP-0005](../cip/0005-phase-one-implementation.md) pre-code recheck (evidence register §15, recheck 2026-10-15): draft-ietf-ohai-chunked-ohttp-08 is approved and in the RFC Editor queue but blocked on two normative references and has no RFC number [V]; chunked request bodies are in the -08 text [V]; the Rust ohttp crate 0.8.0 implements chunked streaming by default [V] though the draft revision it targets is not stated in the sources examined on 2026-10-15 [U]; Google QUICHE has a chunked gateway [V]; chunked support in Cloudflare's published reference gateway was not found in the sources examined on 2026-10-15 [U]; the README of Microsoft's attested-ohttp-server links draft-ohai-chunked-ohttp-01 [V], and its compatibility with draft -08 is unverified [U]. Section 3 now fixes the per-message, non-interactive shape. Still open: the RFC number and date, and independent interoperability of the reference node and client with one other chunked implementation, a release gate (docs/security/privacy-and-contexts.md section 12).
4. **Gas when the node refuses.** The node pays the gas of `openSessionFromCredit`. Whether a node that declines a spend after verifying it should record a reason the client can show, and whether a client whose note was left in flight (R9) has any remedy beyond re-proving, is open; no fee or penalty is proposed.
5. **Padding sizes and batch sizes.** `paddingBuckets[]` and `tokenBatch` are unset. Choosing them needs measurements on the reference node, a stated cost in wasted bytes and added latency, and a stated residual against token-length and timing attacks (evidence register §16 [V]); none of these exists.
6. **Per-chunk exchanges through a relay.** The node streams at most one unpaid chunk (section 8) and under section 3 each voucher is one OHTTP exchange, so each chunk costs at least two HTTP requests through the relay (evidence register §15 [V]). Whether the exposure should widen to a small number of chunks, so that one voucher exchange releases several frames, or `CHUNK_TOKENS` should grow, is open and is a pricing question too; this PR changes neither. Putting later vouchers back into the same chunked request would restore the interactive case and is not a direction (open question 3).
7. **Naming the gateway at the relay.** RFC 9458 describes a relay bound to one gateway. A client that picks a random registered relay for any registered node needs the relay to accept the target gateway as a request parameter; the exact mechanism, and whether a relay may refuse some gateways, is open. Proposed resolution: [ADR 0014](../adr/0014-relay-authentication-to-gateways.md) (node operator address on the relay path; relay may refuse).
8. **`CHUNK_TOKENS` ownership.** Whether `limits.chunkTokens` is per node (advertised) or a protocol constant (docs/protocol/contracts-and-settlement.md §16).
9. **Capability document discovery.** Whether the document should also be published through an indexer so that clients can rank a pool without contacting every node, and how stale such a copy may be.
10. **Admission before the spend.** Whether the client should always obtain a signed admission promise from the node before proving and sending the credit spend, and whether a broken promise should be a reputation event indexers surface.
11. **Tokenizer tolerance.** Whether the client should accept small disagreements in `tokenCount` for the same pinned tokenizer, or whether any disagreement is a hard error as proposed here. Zero tolerance on re-tokenized decoded text can reject honest receipts, because different token sequences can decode to the same text; the candidate resolutions are that chunk tokens travel as token IDs inside the sealed frame so the client counts IDs rather than re-tokenizing text, or that a bounded tolerance applies.
12. **Reputation events.** The format of the client-side record of `model_not_loaded`, `unpaid_chunk_timeout`, a spend left in flight and the input-voucher-never-run case, so that community indexers can aggregate them without a central reporter and without a client identifier.
13. **`commitKey` loss.** How `commitKey` is re-sent if the session's first envelope is lost before the node acknowledges it, without opening a second session (docs/security/privacy-and-contexts.md §14).
14. **Thin clients.** Whether a device that cannot sign per chunk or cannot prove in time may delegate `sessionSigner`, which this document forbids in v1; an open question for a later CIP (docs/protocol/contracts-and-settlement.md §16).
15. **`blobUrl` policy.** Whether the reference node should accept `blobUrl` at all, and if so the exact size and time limits and the public-address check it applies after every redirect (section 9); the default remains inline upload.
16. **Resume after a transient disconnect.** An earlier draft of section 7 said the client "signs nothing further for the job" once a stream was truncated, yet a node that resumes after a new `hello` needs the voucher for the chunk it last sent before it streams the next one, so a transient drop would have stalled the job. Sections 7 and 11 now say that a client resuming from its own voucher log continues normal signing after the resume — re-sending its latest voucher, then signing for retransmitted chunks, which keep their original `seq`, that it had not yet covered — and that "signs nothing further" applies only when the voucher log is lost (section 11, the unilateral close). Recorded here so that the earlier reading is not reintroduced; the per-exchange timers of section 3 are the remaining implementation detail.
17. **Inline retry after `blob_url_refused`.** Section 9 has the client "re-send the job with the blob inline" after `blob_url_refused`, but a resend under the same `jobId` and fragment `seq` is returned by fragment dedupe (section 3) as already processed. The inline retry should use a new `jobId` (a new envelope, keypair, AAD tuple and signature, as section 11 requires for any changed job); nothing is charged for the refused job because no input receipt was signed for.
18. **Spike-only round frame and timer names.** The Phase 3 cross-node speculation spike needs a request frame kind inside an open job carrying the accepted tokens and a rollback point (docs/node/distributed-execution.md §8 and its open question 9); this document does not define it, its AAD fields, its ordering with `endOfJob` or its idempotency by `(jobId, frameSeq)`, and must before the spike runs. Separately, the client timer this document calls `interFrameTimeout` is defined only as 2 × the capability field `limits.maxInterFrameMs`; whether the timer should carry the capability field's name so the two cannot drift is open.
