# CIP 0002: Anonymous credits, relays and ownerless contexts

Status: Draft
Type: protocol
Created: 2026-10-14
Requires: 0001

This CIP is Draft. It is not in Last Call and it is not Final. This Draft does not adopt itself, and it does not mark ADR 0010, ADR 0011 or ADR 0012 accepted: each of those records stays proposed for as long as this file stays short of Final under GOVERNANCE.md. It does not require [CIP-0001](0001-adopt-baseline-adrs.md) to be Final in order to exist; it requires CIP-0001 only in the sense that it amends records CIP-0001 proposes to adopt.

## Abstract

If this CIP becomes Final, Comuns adopts [ADR 0010](../adr/0010-anonymous-by-default.md) (anonymous by default: relays, unlinkable sessions and two content tiers), [ADR 0011](../adr/0011-anonymous-credits.md) (anonymous credits: Semaphore groups inside `SessionEscrow`) and [ADR 0012](../adr/0012-contexts-without-a-wallet-link.md) (contexts without a wallet link). [ADR 0003](../adr/0003-hpke-and-the-executor-plaintext-limit.md) is superseded in part, on sender identity, relays, local execution, the default story and the owner field of the context AAD; its cipher suite, envelope signature, `commitKey` and keyring rules stand. The closed list of state-changing functions in [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md) grows from fifteen to 23. There are still four contracts. No band, bond, deadline or protocol fee changes, and no wei value is set.

In standard mode the node can read the prompt, the granted context and the answer, but should not learn who asked. In attested mode the node should not be able to read the prompt either, barring a physical attack (evidence register §14). Standard mode does not hide content.

## Motivation

The owner's first requirement was that prompts run privately. The research in evidence register §14 does not support that requirement for a remote network today: cryptographic private inference runs at minutes per token for GPT-2-class models over the internet, and every network that ships private LLM inference uses trusted execution environments (evidence register §14, [V]/[L]). What a remote node can be denied in practice is the identity of the person asking.

The current design gives that identity away three times. `openSession` records the paying wallet as `user` on-chain. `ContextRegistry` keys every context by its owning wallet and publishes it in `ContextSet`. Clients connect to nodes directly, so the node sees the client's network address. ADR 0010, ADR 0011 and ADR 0012 replace those three links with a relay, an anonymous credit and a context key. They change the closed function list, so a CIP that amends the contracts document is the required tool. The proposal does not rely on a token, a coin vote or an ARB balance.

## Specification

This CIP changes no price band, no deadline, no node bond and no protocol fee. The protocol fee stays 0. No timelock is stated for a parameter change, because this CIP changes no existing parameter: the denominations, `RELAY_FEE_WEI`, `MIN_RELAY_BOND_WEI`, `MERKLE_TREE_DURATION` and `MAX_CHANGE_NOTES` are named here and left unset, like the price bands. Setting any of them is a later parameter CIP. Nothing in this file sets a wei value.

The normative text is ADR 0010, ADR 0011 and ADR 0012. This section transcribes the parts that amend the contracts document, without renaming anything. Where a summary here is read more loosely than ADR 0011, ADR 0011 wins.

### Contracts

Still four contracts: `NodeRegistry`, `ModelRegistry`, `ContextRegistry` and `SessionEscrow`. Relays and their bonds live inside `NodeRegistry`. The Semaphore groups, nullifiers and root window live inside `SessionEscrow`. The credit-holding `SessionEscrow` is non-upgradeable: it is deployed without a proxy and without an upgrade path. Governance parameters (`setBands`, `setCreditParameters`) stay timelocked. The other three contracts keep their current upgrade wording.

`SessionEscrow` keeps its own state and calls only the stateless Semaphore v4 Groth16 verifier from the Semaphore packages:

- one LeanIMT group per denomination index (the zk-kit LeanIMT that Semaphore uses);
- its own nullifier set;
- its own root window: a proof is accepted against the current root of its group, or against a replaced root until `MERKLE_TREE_DURATION` has passed since it was replaced; `MERKLE_TREE_DURATION` is a named deployment constant, unset, and no function changes it;
- `noteSeen[commitment]`, so that `depositNote` and `claimChange` revert on any commitment already seen in any group;
- `depositedWei[address][index]` and `ragequitWei[address][index]`;
- the append-only denomination list and `RELAY_FEE_WEI`.

It does not call a shared Semaphore deployment's `validateProof`. Proof arguments use Semaphore's types, `uint256 merkleTreeDepth`, `uint256 merkleTreeRoot`, `uint256 nullifier` and `uint256[8] points`, and `merkleTreeDepth` must lie in 1 to 32. Every commitment is a `uint256`, and every note carries a fresh Semaphore identity generated by the client, which stores the note secret durably before the commitment is published.

### The amended closed list

Twenty-three state-changing functions: the original fifteen in the order of the ADR 0011 table, then eight new names and no others: `depositNote`, `openSessionFromCredit`, `claimChange`, `ragequit`, `setCreditParameters`, `registerRelay`, `updateRelay`, `deregisterRelay`. The table numbers rows as ADR 0011 does; the order of the closed list is the order of the sentence above. Each signature is quoted once.

| # | Function | Contract | Status | Signature |
|---|---|---|---|---|
| 1 | `registerNode` | NodeRegistry | amended | `registerNode(bytes hpkePublicKey, bytes ohttpKeyConfig, string endpoint, HardwareClass hardwareClass, Tier maxTier, bytes32 benchmarkHash, uint8 modes, bytes32[] modelIds, Offer[] offers) payable`; reverts if the caller is a registered relay |
| 2 | `updateNode` | NodeRegistry | amended | `updateNode(bytes hpkePublicKey, bytes ohttpKeyConfig, string endpoint, HardwareClass hardwareClass, Tier maxTier, bytes32 benchmarkHash, uint8 modes, bytes32[] modelIds, Offer[] offers)` |
| 3 | `deregisterNode` | NodeRegistry | unchanged | `deregisterNode()` |
| 4 | `withdrawBond` | NodeRegistry | extended | `withdrawBond()`; for a relay, after `deregisterRelay` and `block.timestamp ≥ unlockAt`, credits the relay's `bondWei` to `balances[operator]` and deletes the Relay record, requiring and deleting no Node record |
| 5 | `withdraw` | NodeRegistry and SessionEscrow | unchanged | `withdraw()` |
| 6 | `registerModel` | ModelRegistry | unchanged | `registerModel(bytes32 manifestHash, Tier tier, string licenseSpdx, bool commercialHosting, string metadataUri)` |
| 7 | `updateModel` | ModelRegistry | unchanged | `updateModel(bytes32 modelId, string licenseSpdx, bool commercialHosting, string metadataUri)` |
| 8 | `setContext` | ContextRegistry | amended | `setContext(bytes32 contextId, uint64 version, bytes32 contentHash, bytes contextPubKey, bytes signature)`; any caller; rules in ADR 0012 |
| 9 | `openSession` | SessionEscrow | unchanged | `openSession(address node, bytes32 modelId, Mode mode, address sessionSigner, uint256 maxSpendWei, uint256 expectedPriceInPerMillion, uint256 expectedPriceOutPerMillion) payable returns (bytes32 sessionId)`; records `funding = wallet`, `relay = address(0)`, `relayFeeWei = 0` |
| 10 | `topUp` | SessionEscrow | unchanged | `topUp(bytes32 sessionId, uint256 newMaxSpendWei) payable`; reverts when `funding == credit` |
| 11 | `redeemVoucher` | SessionEscrow | amended | `redeemVoucher(bytes32 sessionId, Voucher voucher, bytes signature)`; credit sessions apply the relay split |
| 12 | `closeWithVoucher` | SessionEscrow | amended | `closeWithVoucher(bytes32 sessionId, Voucher voucher, bytes signature)`; credit sessions apply the relay split and record `pendingWei` |
| 13 | `closeSession` | SessionEscrow | extended | `closeSession(bytes32 sessionId, bytes signature)` |
| 14 | `finalize` | SessionEscrow | amended | `finalize(bytes32 sessionId)`; anyone; credit sessions record `pendingWei` |
| 15 | `setBands` | NodeRegistry | unchanged | `setBands(Tier tier, Band[4] bands)` |
| 16 | `setCreditParameters` | SessionEscrow | new | `setCreditParameters(uint256 denominationWei, uint256 relayFeeWei)` |
| 17 | `depositNote` | SessionEscrow | new | `depositNote(uint256 identityCommitment, uint8 denominationIndex) payable` |
| 18 | `openSessionFromCredit` | SessionEscrow | new | `openSessionFromCredit(address node, address relay, bytes32 modelId, Mode mode, address sessionSigner, uint256 expectedPriceInPerMillion, uint256 expectedPriceOutPerMillion, uint8 denominationIndex, uint256 merkleTreeDepth, uint256 merkleTreeRoot, uint256 nullifier, uint256[8] points) returns (bytes32 sessionId)` |
| 19 | `claimChange` | SessionEscrow | new | `claimChange(bytes32 sessionId, uint256[] changeCommitments, uint8[] denominationIndexes, bytes signature)` |
| 20 | `ragequit` | SessionEscrow | new | `ragequit(uint8 denominationIndex, uint256 merkleTreeDepth, uint256 merkleTreeRoot, uint256 nullifier, uint256[8] points)` |
| 21 | `registerRelay` | NodeRegistry | new | `registerRelay(string endpoint) payable` |
| 22 | `updateRelay` | NodeRegistry | new | `updateRelay(string endpoint)` |
| 23 | `deregisterRelay` | NodeRegistry | new | `deregisterRelay()` |

Relays hold no OHTTP key configuration; only nodes register `ohttpKeyConfig`, because the node process is the OHTTP gateway.

### Rules

- **Credit parameters.** `setCreditParameters` is governance only, through the same timelock as `setBands`. On Arbitrum Sepolia, [GOVERNANCE.md](../../GOVERNANCE.md) §7.1 applies; mainnet unchanged. A non-zero `denominationWei` appends one denomination index; the list is append-only and an index's value never changes. `denominationWei == 0` appends nothing. Every call sets `RELAY_FEE_WEI`, which may be 0. A denomination must be at least `MIN_DEPOSIT_WEI`. An append is rejected unless every remainder below the largest listed denomination decomposes greedily into at most `MAX_CHANGE_NOTES` notes with dust below the smallest denomination.
- **Deposit.** `depositNote` takes `msg.value` equal to the denomination, inserts the commitment into that group, and records `depositedWei[msg.sender][denominationIndex] += msg.value`. It is the one public, wallet-linked step.
- **Semaphore scope and message.** The contract computes both itself and never trusts caller-supplied values. Scope is `keccak256(chainId, escrow, denominationIndex)`, fixed per group, so each note has exactly one nullifier and can be spent once. For a spend, message is `keccak256(node, relay, modelId, mode, sessionSigner, expectedPriceInPerMillion, expectedPriceOutPerMillion)`, so a submitter cannot redirect it. For a ragequit, message is `keccak256("ragequit", msg.sender)`. Both scope and message are passed to the verifier hashed as Semaphore does, `uint256(keccak256(abi.encodePacked(x))) >> 8`.
- **Spend.** `openSessionFromCredit` is called by the node or by any broadcaster, never required from the user's wallet. On success it stores the nullifier and opens a session with `user = address(0)`, `funding = credit`, `depositWei = maxSpendWei =` the denomination, `relay`, `relayFeeWei` copied from `RELAY_FEE_WEI` at that moment, and `pendingWei = 0`. Every `openSession` check except `msg.value` applies, `maxTier` is never read, `relay` must be a registered relay that is not deregistering, and `relay ≠ node`.
- **Relay fee from the first settled wei.** For a credit session each incremental payout in `redeemVoucher` and `closeWithVoucher` splits as `relayDelta = min(relayFeeWei, newSettled) − min(relayFeeWei, oldSettled)` to `balances[relay]` and `nodeDelta = payout − relayDelta` to `balances[node]`. The `Voucher` type string and the payment rule are unchanged. No user transaction pays the relay.
- **`topUp`** reverts on a credit session. When the cap is exhausted the client opens a new credit session with a new note.
- **Close.** For a credit session `closeSession` is callable by the node, or by any caller whose `signature` is a `sessionSigner` EIP-712 signature over `(chainId, escrow, sessionId, "close")`. It is not permissionless. The reference client submits it through a relay or broadcaster, never from the deposit wallet. If both the node and the `sessionSigner` key are gone, the session stays open.
- **Settlement.** `closeWithVoucher` and `finalize` on a credit session never credit `balances[user]`. They record `pendingWei = depositWei − settledWei`, which is the full denomination when `settledWei == 0`. No leaf is inserted at close or finalize. There is no refund commitment.
- **Change.** `claimChange` is callable by anyone, with no deadline, while `pendingWei > 0`, including in status `settled`, the one exception to the rule that a settled session accepts no call. It is authorised by a `sessionSigner` EIP-712 signature over `(chainId, escrow, sessionId, keccak256(changeCommitments), keccak256(denominationIndexes))`. It takes at most `MAX_CHANGE_NOTES` entries; the listed denominations sum to at most `pendingWei`; each commitment is fresh under `noteSeen` and is inserted into its group. Dust, `pendingWei` minus that sum, goes to `balances[node]`, and `pendingWei` is zeroed. An empty array is the dust-only branch. The client decomposes greedily, so dust stays below the smallest denomination.
- **Ragequit.** `ragequit` pays `balances[msg.sender]` one denomination for one note of that group that the caller proves, stores the nullifier, and is allowed only while `depositedWei[msg.sender][denominationIndex] − ragequitWei[msg.sender][denominationIndex] ≥ denomination`; it then increments `ragequitWei`. It is public and linkable by design, and it cannot tell deposit notes from change notes. The credited balance leaves through `withdraw()`.
- **Relays.** `registerRelay` requires `msg.value ≥ MIN_RELAY_BOND_WEI` (named, unset), reverts if the caller is a registered node or relay, and creates a Relay record `(operator, endpoint, bondWei, unlockAt = 0)`. `updateRelay` is the operator's, while `unlockAt == 0`. `deregisterRelay` sets `unlockAt = block.timestamp + BOND_UNLOCK_DELAY`; open sessions that name the relay continue and still pay it. Relays are never slashed.
- **Contexts.** `ContextRegistry` keys a context by `contextId` alone, with `contextId = keccak256(contextPubKey)`. `setContext` checks that hash, `version == previous + 1`, `contentHash ≠ 0`, and that `signature` is the context key's EIP-712 signature over `(chainId, registry, contextId, version, contentHash)`. In the reference client a broadcaster or a node submits it, never the user's wallet. The registry is an optional public anchor; the default integrity path is the context host's compare-and-swap and the signed hash chain of ADR 0012. Whenever a globally consistent multi-device head is promised, an anonymous public anchor is required: `setContext` submitted by a broadcaster.

New session fields: `funding` (`uint8`: 0 wallet, 1 credit), `relay` (`address`), `relayFeeWei` (`uint256`), `pendingWei` (`uint256`). `user` is `address(0)` when `funding` is credit.

Events: each new function emits at least one event. The exact event names and field orders are defined once, in [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md) §11, which transcribes from ADR 0011 and is the normative name source; every other document uses those names and fields. The new event names are, copied from §11: `CreditParametersSet` (`setCreditParameters`), `NoteDeposited` (`depositNote`), `CreditSessionOpened` (`openSessionFromCredit`, emitted after `SessionOpened` with `user = address(0)` in the same call), `ChangeNoted` (`claimChange`), `NoteRagequit` (`ragequit`), `RelayRegistered` (`registerRelay`), `RelayUpdated` (`updateRelay`) and `RelayDeregistered` (`deregisterRelay`). `BondWithdrawn` is reused for a relay bond; `NodeRegistered` and `NodeUpdated` gain `ohttpKeyConfig` as their last field; `ContextSet` loses its `owner` field and becomes `(contextId*, version, contentHash)`.

### The credit invariant

Per credit session, at all times: `nodeCredited + relayCredited + remainingLockedWei + pendingWei + mintedChangeValue = depositWei`, where `remainingLockedWei = depositWei − settledWei` while the session is open or closing and 0 after settlement, and `nodeCredited` includes the dust exactly once, after `claimChange`. Pool-wide: `address(this).balance == Σ balances + Σ open or closing (depositWei − settledWei) + Σ pendingWei + Σ unspent note face value`. The pricing fixtures use the same equations.

### Client and transport

- The reference client has no call site for `openSession`, `topUp` or user refunds. Those remain specified for a direct caller, and no document offers that path as a privacy mode.
- Client-to-node traffic uses RFC 9458 Oblivious HTTP through a registered relay, with chunked OHTTP for streaming. When no relay is available the request fails closed; there is no direct-connection fallback.
- Every session-specific chain read the reference client makes goes through a relay, including session lookup, settlement and change monitoring, and witness and root queries. An indexer is a backend behind that transport, not an alternative to it.
- Local execution is withdrawn. Inference runs only on network nodes, and the client performs no model computation.
- The Phase 1 Sepolia slice needs a testnet-only ladder of at least two denominations, values unset here. Its exit demonstrates a partial spend with `claimChange` into at least one smaller note plus dust, a zero-use session claimed back in full, and a `ragequit`.

## Rationale

The facts this design rests on are in [docs/evidence-register.md](../evidence-register.md) §14–§16.

- Cryptographic private inference is not interactive: about 2 minutes per token on GPT2-base for the best client-plus-server scheme, about 233 s for GPT2-base in the best three-party scheme over a WAN, and 1.31 to 6.79 minutes per token for FHE on an A100 (evidence register §14, [V]). Every network shipping private LLM inference uses TEEs (evidence register §14, [V]/[L]). MPC and FHE are future work only: they are not part of this proposal and no work on them is planned.
- TEEs do not resist physical attacks: TEE.fail extracts TDX and SEV-SNP keys with a DDR5 interposer under $1,000 (evidence register §14, [V]), and TDXRay recovers prompts from tokenizer memory-access patterns (evidence register §14, [L]). Attested mode is therefore stated as "should not be able to read", never as a guarantee.
- Semaphore v4 gives membership and a per-scope nullifier on a LeanIMT Poseidon tree with Groth16 proofs, a trusted setup with more than 400 participants finished 13 July 2024, a depth of 1 to 32, and a live deployment on Arbitrum One (evidence register §15, [V]). v4.0.0 was audited by PSE; v3 was audited by Veridise (evidence register §15, [V]). No audit claim transfers to the Comuns wrapper around it.
- Semaphore's `validateProof` has no access modifier, its root window is the current root or a replaced root within `merkleTreeDuration`, and scope and message enter the verifier hashed as `uint256(keccak256(abi.encodePacked(x))) >> 8` (evidence register §15, [V]). That is why the escrow keeps its own trees, nullifiers and root window and calls only the verifier.
- Phone proving is 143–2,146 ms [V] (Semaphore-32) (evidence register §15). Semaphore's own `validateProof` is estimated at about 230–270k L2 gas (evidence register §15, [U]); Comuns spend gas is UNVERIFIED until measured. LeanIMT insertion gas and duplicate-leaf behaviour are UNVERIFIED.
- Refund amounts re-link requests, and fixed budget classes are the proposed fix (evidence register §15, [V]); hence fixed-denomination change notes and dust to the node instead of a variable refund to a user.
- RFC 9458 separates who sees the network address from who sees the content, provided relay and gateway are run by different entities, and chunked OHTTP enables streaming (evidence register §15, [V]). Tor and Nym were rejected as the default: Tor's median round trip to the response header is 100–540 ms to public servers and flow correlation reaches 96% from about 900 packets (evidence register §15, [V]/[L]), and Nym publishes no measured latency (evidence register §15, [V]).
- No authoritative minimum anonymity-set size was found (evidence register §15, [U]).
- Prompt text, sizes and timing still leak: attribute inference reaches up to 85% top-1 accuracy (evidence register §16, [L]), token lengths reconstruct 29% of responses (evidence register §16, [V]), and Whisper Leak often exceeds 98% AUPRC with no mitigation fully protecting (evidence register §16, [V]).
- Turns within one conversation are linkable in the shipping precedent too (evidence register §16, [V]), which is why a `contextId` is stated as a pseudonym.

Alternatives considered, each recorded in the ADRs: a custom join-split circuit (deferred), Privacy Pools (only an Ethereum mainnet pool is listed, evidence register §15, [V]), Railgun (fees and DAO governance, evidence register §15, [V]), a Tornado-style anonymous withdrawal (rejected, evidence register §16, [V]), blind-signature tokens (an issuer holds a secret key, evidence register §15, [U]), off-chain-only RLN spends, an upgradeable escrow, a wallet-written context registry, and local execution as the privacy fix. Anything stated in this CIP that is not traceable to evidence register §14–§16 or to the ADRs is UNVERIFIED, including the claim that the relay and node operators of a deployed network will in fact be distinct entities.

## Backwards compatibility

Nothing is deployed. No contract, client or node exists to migrate.

This CIP contradicted the following documents as they stood when it was drafted; each has been updated to follow it, and the list records what changed:

- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md) §2 (four contracts and fifteen functions; the upgrade wording for `SessionEscrow`) and §6 (the function table);
- [docs/project-charter.md](../project-charter.md) 4.8 (ETH session escrow from the user's wallet) and 4.17 (no function beyond the fifteen);
- [ADR 0001](../adr/0001-settle-on-arbitrum-one-evm-not-stylus.md), on the upgrade path for `SessionEscrow`;
- [ADR 0003](../adr/0003-hpke-and-the-executor-plaintext-limit.md), superseded in part by ADR 0010 and ADR 0012 as stated in the Abstract;
- [ADR 0004](../adr/0004-sessions-vouchers-and-no-slashing.md), on refunds credited to `balances[user]`;
- [ADR 0009](../adr/0009-opt-in-client-orchestration.md), on client-side model computation in the sharding spike;
- [docs/architecture/deployment-and-decentralization.md](../architecture/deployment-and-decentralization.md), the Phase 1 row (fifteen functions and an `openSession` happy path).

Wallet-funded `openSession` remains defined. It is retained for a direct caller; the reference client does not call it.

ADRs 0010–0012 are proposed and supersede nothing until this CIP is Final. If CIP-0001 and this CIP both become Final, ADRs 0010–0012 supersede the conflicting sentences of the baseline ADRs; CIP-0001 is not rewritten.

## Security considerations

Security reporting, once a channel exists, is described in [SECURITY.md](../../SECURITY.md). The threat catalogue is [docs/security/threat-model.md](../security/threat-model.md). No protocol implementation exists, so no private vulnerability report is required for this CIP. This file contains no prompt, no key and no seed phrase.

- Standard mode does not hide content: the node reads the prompt, the granted context and the answer. What changes is that it should not learn who asked. Identifying text in the prompt can still deanonymize the author.
- Attested mode: the node should not be able to read the prompt, barring a physical attack on the hardware (evidence register §14).
- A stolen `sessionSigner` key can sign vouchers up to the denomination of that session, close the session, and redirect its pending change into notes the thief controls. Exposure is one denomination per session.
- A lost note secret loses the note. There is no recovery and no admin key over notes.
- Identity reuse across notes is forbidden: a reused identity makes a second note unspendable, and the same commitment in two groups links them publicly. `noteSeen` enforces freshness on-chain.
- `ragequit` is public and linkable by design, pays only the caller, and is bounded by the caller's own net deposits into that group.
- A relay and a node that collude, or one operator holding both roles under two addresses, can correlate timing and sizes. The contract refuses one address in both roles; it cannot detect two addresses.
- An unanchored context trusts its host for sequencing as well as availability. Clients persist accepted head checkpoints in the vault and the identity-key backup and reject rollback behind them; equivocation between unsynced devices and stale-backup acceptance remain documented limits.
- Accounting bugs in the relay split, the dust branch and the root window are the highest-severity risk. An external review is required before mainnet holds notes; none has been performed.
- No emergency action seizes escrow, moves a note or reads a prompt. The escrow is non-upgradeable, so no key can do any of those through an upgrade either.

There is no dedicated anonymous withdrawal entry point. A credit holder who operates a node can open a session to it, sign vouchers and withdraw that node's balance, because the contract does not verify that inference happened. Regulatory classification is UNVERIFIED and is a Phase 4 review item (facts in evidence register §16, not legal advice).

## Economic considerations

The protocol fee is 0, and no treasury exists. This CIP does not change that fact. There is no protocol token and no coin vote. ARB balances are not this project's votes.

- Dust from `claimChange` is node income, not a fee: it goes to `balances[node]` and to nobody else.
- The relay fee is paid from the node's settled value, not by the user and not to the protocol. Its value is unset and may be 0.
- Unset denominations are not prices. A denomination is the size of a note; the price of inference stays the node's offer inside its band. Until a parameter CIP sets the denominations and `RELAY_FEE_WEI`, no credit session can open on mainnet, as with the unset bands.
- Nodes bear the spend gas of `openSessionFromCredit` and price it into their offers; a broadcaster that submits for a node is the node's own arrangement.
- The relay bond `MIN_RELAY_BOND_WEI` is a new named parameter, unset. The node bond is unchanged.

This CIP does not ask for funds, does not create a bounty and does not record a grant.

## Reference implementation

None.

## Change log

None.

## Copyright

This CIP assigns no copyright and uses no CLA.

Copyright 2026 Comuns contributors

Licensed under the Apache License, Version 2.0 (see LICENSE)
