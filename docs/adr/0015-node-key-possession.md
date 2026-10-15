# ADR 0015: Prove possession of node keys to the client, not to the contract

**Status:** proposed

**Date:** 2026-10-15

**Deciders:** none seated; adoption is proposed in [CIP-0005](../cip/0005-phase-one-implementation.md)

## Context

KI-3 is the review report's residual conflict 1 and its status row: [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md) section 5, [docs/security/threat-model.md](../security/threat-model.md) T7 and [docs/node/node-design.md](../node/node-design.md) section 7 describe node registration as carrying a proof of possession of the HPKE private key, while `registerNode` and `updateNode` take plain `hpkePublicKey` bytes. The contracts document records it as open question 18, the privacy document as open question 6, the node design as open question 2 (how the receipt-signing key is bound), and the system architecture's RPC-provider row relies on "proof of possession at registration and key pinning". The ownership is circular: the privacy document says the exact form is owned by the contracts document, and the contracts document points back at the privacy document's question 6. The risk register has no row for it, although the review report calls it a release blocker for any implementation.

The signatures are fixed. [ADR 0011](0011-anonymous-credits.md) and [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) carry `registerNode(bytes hpkePublicKey, bytes ohttpKeyConfig, string endpoint, HardwareClass hardwareClass, Tier maxTier, bytes32 benchmarkHash, uint8 modes, bytes32[] modelIds, Offer[] offers) payable` and the matching `updateNode`; neither has a proof field, and `NodeRegistered` and `NodeUpdated` carry the two keys as plain bytes. Adding a field would amend ADR 0011, the 23-function list and both event layouts.

The cipher suite is fixed by [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md): RFC 9180 HPKE in base mode, with X25519 and HKDF-SHA256 as the KEM, HKDF-SHA256 as the KDF and ChaCha20-Poly1305 as the AEAD. The reference implementation is the `hpke` crate 0.14.1 (evidence register §4, [V]). The outer hop is Oblivious HTTP to the node's registered `ohttpKeyConfig` (evidence register §15, [V]). What that suite does and does not offer to an on-chain check:

- An EVM contract cannot cheaply verify an X25519 operation or any HPKE operation. No precompile for X25519, HKDF or an HPKE open is in the evidence register; that is an absence in the register, not a verified fact about the EVM, and is marked UNVERIFIED. The register's only precompile mention is another network's TEE precompiles (evidence register §2, [V]), which is not a path for this protocol.
- X25519 is a Diffie–Hellman function (RFC 7748) and the HPKE suite gives it no signature scheme, so an X25519 key cannot sign a challenge the way a secp256k1 or Ed25519 key can. This is a reading of the standards, UNVERIFIED in the evidence register; confirmed in the CIP-0005 recheck.
- A secp256k1 signature by the operator's Ethereum account over the key bytes proves only that the operator chose those bytes. `msg.sender` on `registerNode` already proves that. It proves nothing about whether anyone holds the matching private key.
- A ciphertext produced by the registrant, for example an HPKE envelope sealed to `hpkePublicKey` and placed in the registration payload or the capability document, proves nothing either. Anyone can seal to a public key. Only decryption proves possession, and decryption is an act that the chain cannot witness.

So the question "signature or HPKE-sealed challenge, on-chain or by clients" has one answer that the suite permits: a challenge, decrypted by the node, verified by the party that is about to seal to that key.

## Decision

### (1) No registration-time proof and no on-chain check

`registerNode`, `updateNode`, `NodeRegistered` and `NodeUpdated` are unchanged from [ADR 0011](0011-anonymous-credits.md) and the contracts document. The contract binds public keys to an operator address and nothing more. Everywhere the documents say `proof of possession at registration`, the sentence is corrected to: `registration binds public keys to an operator; each client verifies live possession before sending anything confidential`.

### (2) The `key_probe` exchange

Possession is proven to each client, interactively and anonymously, by a `key_probe` exchange that the client performs through a relay the gateway has authenticated ([ADR 0014](0014-relay-authentication-to-gateways.md)). The probe runs before the credit spend that would bind the node to a session, and again on a resume whenever the keys in the latest `NodeRegistered` or `NodeUpdated` event differ from the keys the client pinned. (`keyringHashes` in the capability document is not the trigger: it lists older keys that the node still serves for unsettled sessions and says nothing about the current keys.)

**Key source.** The client reads `hpkePublicKey` and `ohttpKeyConfig` only from the latest `NodeRegistered` or `NodeUpdated` event for that operator in its own relay-tunnelled chain view, and may compare more than one RPC. It never takes a key from the capability document or from any message the node sends; the capability document's copy must equal the registered one, as the off-chain API already requires.

**Tuple.** The probe is domain-separated by the tuple

```
(`comuns/key-probe/v1`, chainId, NodeRegistry address, nodeOperator,
 keccak256(hpkePublicKey), keccak256(ohttpKeyConfig))
```

used, in that order, as the HPKE `info` and as the AAD of the probe envelope. Like the job AAD list of [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) it contains `chainId`, but it carries the probe-specific domain label, the NodeRegistry address, the node operator and the two key hashes where the job AAD carries the escrow address and the session and job identifiers, so the encoded tuples differ and a job envelope cannot open as a probe, nor a probe as a job envelope.

**Request.** The client generates a fresh 32-byte challenge from the operating-system CSPRNG, HPKE-seals it in base mode to `hpkePublicKey` under the tuple, and sends the sealed probe as an OHTTP request encapsulated to `ohttpKeyConfig`. The probe carries no `sessionSigner`, no session or job identifier and no client identifier. With the capability document it is one of the only two requests that carry no `sessionSigner`; both are served only on an authenticated relay connection.

**Node side.** The node reconstructs the tuple from its own identity and keys: its own operator address, the chain id and NodeRegistry address of its deployment, and the hashes of the keys it currently holds. It never takes any element of the tuple from the request. It opens the probe only under that tuple, and answers only if the open succeeds and yields exactly 32 bytes. A job envelope therefore cannot be replayed as a probe, a probe cannot be replayed as a job, and the probe is not a general decryption oracle: the only thing the node will ever decrypt under the probe tuple is an exactly 32-byte probe plaintext, opened under the tuple the node reconstructs itself; it is evidence of possession only when the response MAC verifies. The node rate-limits probes per relay connection.

**Response.** The node derives a response key through the RFC 9180 secret-export interface of the probe's own HPKE recipient context, with exporter context `comuns/key-probe/v1/response` and a 32-byte output. That RFC 9180 provides secret export is a reading of the standard, UNVERIFIED in the evidence register; confirmed in the CIP-0005 recheck. It answers `key_probe_response` inside the OHTTP response with:

1. the challenge bytes;
2. `receiptPublicKey`, its receipt-signing public key (a separate secp256k1 key, see (3));
3. `receiptSignature`, the receipt key's signature over the canonical encoding of (tuple, challenge);
4. `responseMac`, an HMAC-SHA256 under the exported response key over the canonical encoding of (tuple, challenge, `receiptPublicKey`, `receiptSignature`).

The canonical encoding is fixed by the conformance vectors of CIP-0005; this record fixes only the field list and order.

**Client side.** The client accepts the response only if the challenge equals the one it sent, `responseMac` verifies under the response key exported from its own sender context, and `receiptSignature` verifies under `receiptPublicKey` over the same tuple and challenge. It then pins `hpkePublicKey`, `ohttpKeyConfig` and `receiptPublicKey` for the session, and requires every input receipt, every chunk receipt, `session_opened` and `welcome` to verify under the pinned receipt key. Any failure, a wrong challenge, a bad MAC, a bad signature, a malformed response, a timeout or a refused exchange, fails closed before any note is spent and before any prompt is sealed. There is no retry against a different key and no downgrade.

### (3) What one probe covers

- **The HPKE private key.** A matching challenge shows freshness only: a party holding the OHTTP private key can rewrap the probe into its own OHTTP request to the honest node and return the challenge without opening it. What shows that the holder of the private key matching `hpkePublicKey` opened this probe is the verified response MAC, under the key exported from the probe's HPKE context with exporter context `comuns/key-probe/v1/response`.
- **The OHTTP private key.** RFC 9458 derives the response encryption key from the request's HPKE context, so a valid OHTTP response shows that the responder decapsulated the request with the private key of `ohttpKeyConfig`. This is a reading of the standard, UNVERIFIED in the evidence register; confirmed in the CIP-0005 recheck. Possession of `ohttpKeyConfig` is therefore covered by the same round trip; privacy open question 6 is answered yes.
- **The receipt-signing key.** The receipt key is a separate secp256k1 key held by the node, not a contract field and not derived from the HPKE key; node-design open question 2 is answered that way. It is bound by the MAC, not by the signature alone. A party that holds only the OHTTP private key can decapsulate the outer request and rewrap the sealed probe into another OHTTP request to whoever holds the HPKE key; if that holder returns the challenge, the rewrapping party could attach any receipt key and sign the challenge with it. The response key defeats that: it is a secret that the encapsulating client and the decapsulating HPKE private-key holder both hold, and that a party who only rewraps the OHTTP request does not, and the MAC under it covers `receiptPublicKey` and `receiptSignature`, so the receipt key named in the response is the one the HPKE holder vouched for. A substituted receipt key fails the MAC. The client checks the MAC and the signature before it pins any key or spends a note.

The three proofs are joint: a response that passes shows that one party, reachable through the registered `ohttpKeyConfig`, holds the HPKE private key and vouches for the receipt key, at the cost of one content-free round trip.

### (4) Attested mode

Attested mode is not in Phase 1. When it exists, the quote binds `hpkePublicKey` and `ohttpKeyConfig` as report data together with the client nonce (node-design attested paragraph, RR-02, RR-47); those sources do not bind the receipt key. This record proposes adding `receiptPublicKey` to the quote's report data before attested mode is enabled, so that the quote binds all three keys. The probe still runs. The quote shows where the keys live; the probe shows that they are live and reachable; neither replaces the other. A quote is never accepted as a substitute for the probe, and a passed probe is never accepted as a substitute for the quote.

### (5) The threat this mitigates

The probe mitigates **key misattribution**: a registry record whose keys the live gateway does not hold. That covers a public key copied from another node's record, a misconfigured node whose gateway and registry disagree, and a stale rotation where `updateNode` published a key the node has not yet loaded or has already dropped. Each is detected at the cost of one content-free round trip before any note is spent.

It does not mitigate **T7, the hostile RPC**. A hostile RPC can present an attacker-registered record whose keys the attacker genuinely holds; that record passes the probe, because the attacker does possess those keys. T7 is mitigated by the client reading and pinning keys from its own relay-tunnelled chain view, by comparing independent reads, and by key pinning across sessions. The threat model's T7 sentence, which currently credits the proof of possession, is reworded accordingly by the security reconciliation task.

### (6) Residuals

- A private key the operator has shared with a third party is undetectable. The probe shows that someone reachable through the registered gateway holds the key; it cannot show that nobody else does.
- Chain data alone never shows possession. A client, an indexer or a pool view that has not probed knows only that keys are bound to an operator.
- The in-flight key swap, contracts open question 17 and privacy open question 11, stays open: a same-price `updateNode` ordered just ahead of the spend can still change the keys, because the spend message binds no key hash. The client's defence is to probe immediately before the spend and to abandon the spend if the latest event changes between the probe and the submission; closing the window needs a change to the spend message, which this record does not make.
- The node rate-limits probes; an operator may throttle a relay connection that probes without opening sessions.
- Planned operator key rotation while sessions are active is discouraged on testnet. When it happens, a resume that finds different keys in the latest event re-probes, and a failed re-probe is fail-closed recovery: the client settles what it can and does not seal anything further to that node.

## Alternatives considered

### On-chain X25519 or HPKE verification

Rejected. No precompile or cheap path for X25519, HKDF-SHA256 or an HPKE open is in the evidence register (UNVERIFIED as an absence), so the check would be a large custom-arithmetic contract with its own audit burden, and any proof field would amend `registerNode`, `updateNode` and both events, which [ADR 0011](0011-anonymous-credits.md) and the 23-function list carry. The chain would also only ever see a proof made at registration time, which says nothing about whether the key is live when a client seals to it months later.

### An operator secp256k1 signature over the key bytes

Rejected. It proves authorization, that the operator chose these bytes, and `msg.sender` already proves that. It cannot prove possession of the X25519 private key, because the signing key and the encryption key are unrelated. A registration with a copied `hpkePublicKey` and a perfectly valid operator signature is exactly the misattribution case this record must detect.

### A registrant-produced HPKE ciphertext in the capability document

Rejected. Sealing to a public key needs no secret: anyone can produce a ciphertext to any registered key, so a sealed value in the capability document or the registration payload demonstrates nothing. Only decryption proves possession, and decryption of a value the client chose is what the probe does.

### Using the attested quote as the Phase 1 proof

Rejected. Standard mode has no quote, and Phase 1 runs standard mode only. A quote also binds keys to a measured environment at quote time; it does not show that the gateway that answers a particular client today holds them. The quote is kept as a separate, later check that binds the same three keys (4).

### Deriving a signing key from the X25519 seed

Rejected. Using the X25519 secret, or a seed shared with it, as a signing key is non-standard, is not something the HPKE suite or the `hpke` crate offers, and the safety of reusing one secret across a Diffie–Hellman function and a signature scheme is UNVERIFIED. ADR 0003 permits no homegrown cipher, KDF, MAC or mode. A separate receipt key, bound by the probe, costs one more key on the node and no new cryptography.

## Consequences

- The contracts document's open question 18 gets a proposed-resolution pointer to this record, and its node table keeps plain `hpkePublicKey` and `ohttpKeyConfig` bytes. No function, signature or event changes.
- The privacy document's section 5 sentence on proof of possession is corrected to the wording in (1), and open question 6 gets a proposed-resolution pointer: yes to `ohttpKeyConfig`, and the quote is a separate check.
- The threat model's T7 is reworded: the proof of possession is not its mitigation; the client's own chain view, independent reads and pinning are.
- The node design's key table names a separate secp256k1 receipt-signing key bound by the probe, its HPKE-boundary row lists `key_probe` as the only HPKE open outside job envelopes, under its own `info` and AAD, its attested paragraph is amended to add `receiptPublicKey` to the quote's report data before attested mode is enabled, and its open question 2 gets a proposed-resolution pointer.
- The off-chain API names `key_probe` and `key_probe_response` in its message-family table as the second request family without a `sessionSigner`, served only on an authenticated relay connection.
- The system architecture's RPC-provider row replaces "proof of possession at registration" with the client-side probe and pinning.
- The review report's KI-3 rows are annotated with a pointer to this record, not erased.
- The risk register gains RR-49 for KI-3, with a release gate that requires negative tests: a wrong challenge, a probe sealed under a job AAD, a job envelope presented as a probe, a response with a bad MAC, a probe rewrapped into another OHTTP request, a substituted receipt key, a key changed between the probe and the spend, and a direct (non-relayed) probe, each failing closed before any spend.
- CIP-0005 adds the RFC 7748, RFC 9180 and RFC 9458 readings above to its pre-code rechecks and fixes the canonical encodings and conformance vectors of the probe.
- The probe is one extra OHTTP round trip per node per session open and per key change, with no content and no identifier in it.
- KI-3 stays a release blocker until CIP-0005 is Final and the conformance tests, positive and negative, exist and pass in CI.

## Links

- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0011](0011-anonymous-credits.md)
- [ADR 0014](0014-relay-authentication-to-gateways.md)
- [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)
- [CIP-0005](../cip/0005-phase-one-implementation.md)
- [docs/evidence-register.md](../evidence-register.md) §2, §4, §15
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md) (node record, `registerNode`, `updateNode`, events, open questions 17 and 18)
- [docs/protocol/off-chain-api.md](../protocol/off-chain-api.md)
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md) (section 5, open questions 6 and 11)
- [docs/security/threat-model.md](../security/threat-model.md) (T7)
- [docs/node/node-design.md](../node/node-design.md) (key table, attested paragraph, open question 2)
- [docs/architecture/system-architecture.md](../architecture/system-architecture.md)
- [docs/risk-register.md](../risk-register.md) (RR-02, RR-47, RR-49)
- [docs/review-report.md](../review-report.md) (KI-3)
