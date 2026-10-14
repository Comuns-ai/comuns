# ADR 0010: Anonymous by default: relays, unlinkable sessions and two content tiers

**Status:** proposed

**Date:** 2026-10-14

**Deciders:** none seated; adoption is proposed in [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)

## Context

The owner's first requirement was that prompts run privately: only the client should be able to read the question and the answer. The research compiled in evidence register §14 (annex A) does not support that requirement for a remote network in 2026. Cryptographic private inference runs at minutes per token even for GPT-2-class models over the internet: the best measured client-plus-server scheme takes about 2 minutes per token on GPT2-base over a 400 Mbps WAN, the best three-party scheme about 233 seconds for GPT2-base over a 40 ms WAN, and FHE generation between 1.3 and 6.8 minutes per token on an A100 (evidence register §14, [V]). No maliciously secure MPC result at 1B parameters or more was found (evidence register §14, [U]). No FHE accelerator shipping for LLMs was found, and the permutation-based shortcuts are broken (evidence register §14, [V]). Every network that ships private LLM inference today uses trusted execution environments (evidence register §14, [V]/[L]).

The requirement is therefore reframed. What a remote node can be denied in practice is not the content but the identity of the person asking. What can additionally be denied, on hardware that supports it and subject to physical attacks (TEE.fail, TDXRay; evidence register §14, [V]/[L]), is the operator's view of the content. Those are two different properties and this record keeps them apart.

Three earlier positions change as a result. ADR 0003 described single-node standard mode as a warned default in which the executing node reads the prompt and public metadata names the payer; the payer disappears. ADR 0003's local-execution consequence is withdrawn; local execution is no longer a product option. Contexts, which ADR 0003 bound to the owning wallet on-chain, are redesigned in ADR 0012. Payments, which `openSession` bound to a user wallet, are redesigned in ADR 0011. ADR 0003's cipher suite, associated-data list except the owner field, which ADR 0012 removes, envelope signature, `commitKey` and keyring rules are unchanged and carry forward.

Nothing in this record has been implemented, audited or deployed. The protocol is documentation only.

## Decision

**(1) The default property of every session is that the executing node and chain observers do not learn who asked.** The client never presents a wallet address, an account, an API key or any persistent identifier to a node. `sessionSigner` is a fresh key per session and is never reused across sessions. Per-job HPKE keys are generated and discarded as in [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md). Every session-specific chain read the reference client makes (session lookup, settlement and change monitoring, Merkle witness and root queries) goes through the same anonymity-preserving transport as the jobs: RPC or indexer queries tunnelled through a relay. An indexer is a backend behind that transport, not an alternative to it.

**(2) Transport is Oblivious HTTP.** Client-to-node traffic uses RFC 9458 Oblivious HTTP, with chunked OHTTP (draft-ietf-ohai-chunked-ohttp, draft -08) for streamed completions (evidence register §15, [V]). The node process is the OHTTP gateway. Its gateway key configuration, `ohttpKeyConfig`, is registered in `NodeRegistry`: `registerNode` and `updateNode` gain that parameter (signatures in [ADR 0011](0011-anonymous-credits.md)). A node publishes one configuration for every user, so no user can be handed a unique key that would single them out (evidence register §15, [U]). The inner Comuns HPKE job envelope, its associated data and its `sessionSigner` signature from ADR 0003 travel unchanged inside the OHTTP hop. The relay sees the client's network address, request and response sizes, timing and the target gateway, never the envelope. The gateway sees the envelope and the relay's address, never the client's network address. Relay and gateway must be run by different entities for this to hold (evidence register §15, [V]).

**(3) Relays are a registered role.** `NodeRegistry` gains `registerRelay`, `updateRelay` and `deregisterRelay`. A relay posts a bond and withdraws it with `withdrawBond` after the same `BOND_UNLOCK_DELAY` as a node; relays are never slashed. The contract refuses to register an address as both a relay and a node. The client picks a relay at random from the registry, and `openSessionFromCredit` reverts when `relay == node`. One person operating a relay and a node from two addresses is a stated residual risk, not a checked property. Relays are paid a global `RELAY_FEE_WEI`, a governance parameter with no value set in any document and allowed to be 0. It is copied onto the session at open and paid from the first wei of the node's settled value, never by a user transaction ([ADR 0011](0011-anonymous-credits.md)). The reference client has no direct client-to-node job path. When no relay is available the request fails closed; the client does not fall back to a direct connection.

**(4) Payments are anonymous credits** per [ADR 0011](0011-anonymous-credits.md). A session funded by a credit has no `user` address: the contract records `user = address(0)`. **Contexts carry no wallet link** per [ADR 0012](0012-contexts-without-a-wallet-link.md).

**(5) Modes keep their names and numbers.**

- `standard` (0) is the default. The node can read the prompt, the granted context and the answer. It should not learn who sent them.
- `attested` (1) is opt-in. The session is anonymous and, in addition, the operator should not be able to read the content, subject to the hardware attacks in evidence register §14 (TEE.fail and TDXRay). The client verifies the quote before sealing, as in ADR 0003. In attested mode both the OHTTP gateway key and the job HPKE key are generated inside the TEE and the quote binds both. If no eligible attested node exists the request fails closed; there is no silent downgrade to standard mode.
- `verifiable` (2) stays opt-in re-execution by a user-chosen second node under a demonstrated deterministic profile. The verifier is also reached through a relay and funded by its own credit. It adds a second content reader. It is not a privacy upgrade, and it is not combined with attested mode in v1.

**(6) The disclosure sheet** keeps `readersOfFullPrompt`, the floor of distinct nodes and operators that receive the full prompt in every mode ([ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md), [ADR 0009](0009-opt-in-client-orchestration.md)). It gains `recipients[].operatorReadable` (false only for an attested recipient), `counts.operatorReadable`, `counts.attestedRecipients` and an `anonymity` object with the fields `transport`, `relay`, `funding` and `contextLinkage`. The headline banner is computed from `counts.operatorReadable`. An attested request fails closed unless every plaintext recipient on the sheet is attested.

The banner sentences below are normative. Later documents copy them verbatim.

- standard: This node can read your prompt and your answer. It should not learn who you are.
- attested: This node should not be able to read your prompt. A physical attack on the hardware can break that.
- verifiable: This node and the verifier you chose can read your prompt. They should not learn who you are.
- relay: The relay sees your network address and not your prompt. The node sees your prompt and not your network address.

**(7) Local execution is withdrawn** as a product option, as a fallback and as the owner-only option. Inference runs only on network nodes. The client keeps transport, orchestration and sampling decisions; it performs no model computation.

**(8) Padding and batching.** Job envelopes and streamed frames are padded to size buckets, and output tokens are batched per frame. The bucket sizes and batch sizes are unset. This reduces, and does not remove, what sizes and timing reveal; no claim is made that it defeats Whisper Leak or token-length inference (evidence register §16, [V]).

**(9) Future work.** Cryptographic private inference (MPC or FHE) is not part of this proposal and no work on it is planned.

Where this record and ADR 0003 disagree on sender identity, relays, local execution or the default story, this record wins. The cipher suite, the associated-data list (with the owner removal of ADR 0012), the envelope signature, `commitKey` and the keyring rules stay with ADR 0003.

## Alternatives considered

### MPC or FHE now

Rejected. The measured figures are minutes per token for GPT-2-class models over the internet (evidence register §14, [V]). A 200-token answer at 7–13B with the best cryptographic results takes hours (evidence register §14, [U] (calc)). None is interactive. One future-work sentence is all this proposal says about them.

### Tor or Nym as the default path

Rejected. Tor's median round trip to the response header is 100–540 ms to public servers and 250–680 ms to onion services, and flow correlation reaches 96% accuracy from about 900 packets (evidence register §15, [V]/[L]). Nym adds five hops with about 15 ms of mixing delay per hop and publishes no measured latency (evidence register §15, [V]). Neither offers a streaming guarantee for token-by-token completions. Shipping private-inference deployments use anonymity relays, including OHTTP; chunked OHTTP enables streaming (evidence register §15, [V]). A user may still place a relay behind Tor; that is a client choice, not the protocol default.

### Wallet-funded `openSession` as a warned privacy mode

Rejected. A wallet-signed `openSession` publishes the payer on-chain and defeats the default property for every observer. The function stays specified for a direct caller ([ADR 0011](0011-anonymous-credits.md)), but the reference client has no call site for it and no document offers it as a privacy mode.

### Local execution as the privacy fix

Rejected and withdrawn. It answers the content question for one person with a capable machine and answers nothing for the network. Keeping it as "the only owner-only option" would describe a product this proposal does not offer.

### TEE-only membership

Rejected, as in ADR 0003. Requiring a TEE for every node would drop operators who cannot produce a quote, would still not resist an operator with physical access (evidence register §14, [V]), and would make the whole network depend on vendor attestation services. Attested mode stays optional and client-checked.

### A direct-connection opt-out in the reference client

Rejected. An opt-out would make the default property a setting, and a setting that saves a round trip gets switched off. Relay unavailability fails closed. A third-party client may do otherwise; the reference client does not.

### Each node as its own Privacy Pass issuer

Rejected. Blind-signature tokens issued per node would fragment the anonymity set per issuer key, and RFC 9576 advises limiting active issuer configurations (evidence register §15, [V]). Credits are instead a per-denomination group inside the escrow ([ADR 0011](0011-anonymous-credits.md)).

## Consequences

- The node still reads the prompt in standard mode. Identifying text, names, addresses and writing style can deanonymize the author regardless of transport: attribute inference from text reaches up to 85% top-1 accuracy and pseudonymous-profile linking up to 68% recall at 90% precision in the cited studies (evidence register §16, [L]/[V]). The client warns; it cannot prevent this.
- A relay and a node that collude, or one operator holding both roles under two addresses, can correlate timing and sizes. Chunked OHTTP lets either party measure round-trip time (evidence register §15, [V]), and timing side channels have been found in a shipping IP-blinding relay (evidence register §16, [V]). Padding and batching narrow this; they do not close it.
- Anonymity sets are small at launch: few relays, few nodes and few credit holders per denomination. The disclosure sheet shows the sizes it can observe and does not claim a minimum.
- Sybil operators are not detected on-chain. Two addresses are two registrations.
- Attested mode is bounded by the hardware: a DDR5 interposer under $1,000 extracts TDX and SEV-SNP keys and the vendors treat physical attacks as out of scope; tokenizer memory-access patterns recover prompts with 91.5–94.2% similarity in TDXRay (evidence register §14, [V]/[L]).
- Output length alone reveals the language with more than 75% precision (evidence register §14, [V]). Token lengths reconstruct 29% of responses and infer the topic of 55%, and Whisper Leak reaches often more than 98% AUPRC (evidence register §16, [V]). Buckets and batching are mitigations, not fixes.
- Every session costs the relay's share of latency: at least two HTTP requests per OHTTP exchange (evidence register §15, [V]). No millisecond figure is published and none is claimed here.
- The off-chain API, the privacy document, the threat model, the node design and the dApp copy must be rewritten to this record. [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) proposes adopting it.
- Where this record and ADR 0003 disagree on identity, relays, local execution or the default story, this record wins; everything else in ADR 0003 stands.

## Links

- [docs/evidence-register.md](../evidence-register.md) §4, §14, §15, §16
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0009](0009-opt-in-client-orchestration.md)
- [ADR 0011](0011-anonymous-credits.md)
- [ADR 0012](0012-contexts-without-a-wallet-link.md)
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md)
- [docs/security/threat-model.md](../security/threat-model.md)
- [docs/protocol/off-chain-api.md](../protocol/off-chain-api.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
- [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)
