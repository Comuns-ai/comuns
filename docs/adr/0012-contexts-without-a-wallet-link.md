# ADR 0012: Contexts without a wallet link

**Status:** proposed

**Date:** 2026-10-14

**Deciders:** none seated; adoption is proposed in [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)

## Context

[ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) keys a context by `(owner, contextId)` in `ContextRegistry`, binds `owner` into the content AAD, and has the owning wallet sign every grant as EIP-712 typed data. Each of those three choices links the context to a wallet: on-chain for every observer through `setContext` and the `ContextSet` event, and at the node through the grant's `owner` and `ownerSignature`. Under [ADR 0010](0010-anonymous-by-default.md) a node must not learn who asked, and a chain observer must not learn which wallet holds which context. The owner's original requirement stays: one wallet owns one-to-many contexts, and a context is shared with more than one node.

The research precedent is a random identifier and a client-held key per conversation, encrypted blobs stored off-chain, and no on-chain wallet reference, with the stated limit that turns within one conversation are linkable (evidence register §16, [V] for the PCC precedent; evidence register §15, [U] for the design recommendation).

## Decision

**(1) The context identity is a key.** The client generates a random per-context signing key from the operating-system CSPRNG. It is never the wallet key and never derived from it. `contextId = keccak256(contextPubKey)`. A node verifies `keccak256(contextPubKey) == contextId` before it accepts anything about that context.

**(2) The head record and the hash chain.** Each version has a head record `(contextId, version, contentHash, prevContentHash)` signed as EIP-712 typed data by the context key. `contentHash` keeps ADR 0003's definition, keccak256 of the complete stored blob. The node verifies the signature and the chain: the record's `prevContentHash` equals the previous version's `contentHash`, back to version 1 whose `prevContentHash` is zero. The content AAD becomes `contextId ‖ v ‖ prevContentHash`; the owner field is removed. The cipher, the per-version key `K_v`, the nonce and the blob layout stay with ADR 0003.

**(3) Grants.** A grant carries `contextPubKey` and `contextSignature` instead of `owner` and `ownerSignature`. It travels inside the job plaintext, under the job's HPKE envelope, and wraps exactly the granted `K_v` to the node's HPKE key, as before. Grant expiry stays `expiresAt`, a `uint64` unix time. Sharing between nodes is unchanged: `K_v` is re-wrapped per node by the client, and nodes never exchange plaintext or keys.

**(4) The registry drops the owner.** `ContextRegistry` keys a context by `contextId` alone. `setContext(contextId, version, contentHash, contextPubKey, signature)` is callable by any address. The contract checks `keccak256(contextPubKey) == contextId`, `version == previous + 1`, `contentHash ≠ 0`, and that `signature` is the context key's EIP-712 signature over `(chainId, registry, contextId, version, contentHash)`. In the reference client the transaction is submitted by a broadcaster or a node, never by the user's wallet. The registry is an optional public anchor that the default client does not need.

**(5) The default integrity path is off-chain.** A context host stores the blobs and the signed head records. It accepts a new version only by compare-and-swap on `version == head + 1`; a client that loses the race keeps its local edit, rebases on the new head and publishes the next version. There is no silent merge. With the chain no longer the default anchor, the context host is trusted for sequencing as well as for availability. Clients persist every accepted head checkpoint in the vault and in the identity-key backup, and reject any head behind a checkpoint they hold. A host can still equivocate between two devices that have never compared checkpoints, and a device restored from a stale backup accepts a head that a newer device would reject until the two devices sync. Whenever a globally consistent multi-device head is promised, an anonymous public anchor is required: `setContext` submitted by a broadcaster.

**(6) Ownership stays local.** One wallet owns one-to-many contexts. The list of a wallet's context keys lives only in the local vault, encrypted under the identity key, and in the identity-key backup. It is never sent to a node and never written on-chain. The backup rules of ADR 0003 apply: the backup holds keys and key-wrap records, not ciphertext.

**(7) Residuals.** A `contextId` is a pseudonym. Nodes receiving grants can link sessions that reuse the same `contextId`. A public anchor links that context's versions on-chain; it does not itself publish which sessions grant the context. A client may fork a context under a new key to break that chain, at the cost of a new pseudonym with no history. Turns within one conversation are inherently linkable; the shipping precedent accepts the same (evidence register §16, [V]). The disclosure sheet's `anonymity.contextLinkage` field states which of these apply to a request.

## Alternatives considered

### A registry written from the wallet

Rejected. It is the design this record replaces. `setContext` from the wallet, and `owner` in the record and the AAD, publish which wallet holds which context to every observer and to every node that receives a grant.

### A registry written from a fresh wallet address per context

Rejected. The fresh address needs gas, and the transaction that funds it links it to the wallet that paid. Anonymous funding of a throwaway address is exactly the problem [ADR 0011](0011-anonymous-credits.md) solves for sessions; solving it again for a registry write buys nothing that a broadcaster-submitted, context-key-signed `setContext` does not.

### No integrity anchor at all

Rejected. Without a signed hash chain and a compare-and-swap host, a context host or a node could serve a forked or rolled-back version and the client could not detect it. The chain plus checkpoints is the minimum; the optional on-chain anchor is for the multi-device case.

### Per-node derived context keys

Rejected. Deriving a different context key per node would stop one node from linking the context across nodes, but every grant would need its own key, chain and head record, and the hash chain would no longer be one chain. The complexity is not justified while the node already receives the plaintext it is granted.

## Consequences

- `ContextRegistry` changes shape: the `Context` record loses `owner`, the `ContextSet` event loses `owner`, and `setContext` gains two parameters. The contracts document transcribes the signature from [ADR 0011](0011-anonymous-credits.md).
- The owner is removed from the content AAD. The AAD list in ADR 0003 is amended by this record and otherwise stands.
- Grants that reach a node identify a context key, not a wallet. A node can still group every session that grants the same context.
- The context host becomes a trusted party for sequencing. Equivocation against devices that have not synced, and acceptance of a stale head after a backup restore, are the documented limits of an unanchored context.
- Losing the context key means no further version can be signed; the content remains readable through the identity-key wraps. Losing the identity key and its backup loses the list of contexts and every wrap record, as in ADR 0003.
- A fork uses a new `contextId` and need not publish a parent pointer. Shared plaintext and timing can still link it to its parent.
- The privacy document, the threat model, the off-chain API and the node design must be rewritten to this record. [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) proposes adopting it.

## Links

- [docs/evidence-register.md](../evidence-register.md) §15 and §16
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0010](0010-anonymous-by-default.md)
- [ADR 0011](0011-anonymous-credits.md)
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/protocol/off-chain-api.md](../protocol/off-chain-api.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
- [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)
