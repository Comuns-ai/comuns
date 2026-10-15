# ADR 0011: Anonymous credits: Semaphore groups inside SessionEscrow

**Status:** proposed

**Date:** 2026-10-14

**Deciders:** none seated; adoption is proposed in [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)

## Context

[ADR 0010](0010-anonymous-by-default.md) makes the absence of a sender identity the default property of every session. `openSession` as specified in [ADR 0004](0004-sessions-vouchers-and-no-slashing.md) and `docs/protocol/contracts-and-settlement.md` contradicts that: the user's wallet signs the transaction, deposits ETH and is recorded as `user`, so the node, the sequencer and every chain observer learn which address paid for which node, model and mode. A session funded that way is linkable no matter what the transport hides.

The owner asked for anonymous credits: a user deposits once into a pool contract and later spends unlinkable credits with any node. Evidence register §15 (annex B) compares the available constructions. Semaphore v4 is a membership-and-nullifier primitive with a LeanIMT Poseidon tree, Groth16 proofs, a trusted setup with more than 400 participants finished 13 July 2024, and a live deployment on Arbitrum One; v4.0.0 was audited by PSE and v3 by Veridise (evidence register §15, [V]). It has no deposit or withdrawal logic of its own (evidence register §15, [U]). Privacy Pools is listed only on Ethereum mainnet; Railgun charges 0.25% per shield and unshield and is governed by a DAO (evidence register §15, [V]). Tornado-style pools carry a sanctions history (evidence register §16, [V]). Blind-signature tokens need an issuer that holds a secret key (evidence register §15, [U]). No authoritative minimum anonymity-set size was found (evidence register §15, [U]). Refund amounts are a known re-linking channel (evidence register §15, [V]).

The closed list in `docs/protocol/contracts-and-settlement.md` has fifteen state-changing functions and may only grow by a CIP that amends that document. This record defines the amended list in full. [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md), the contracts document and the off-chain API transcribe from here.

Nothing here is implemented, audited or deployed. No normative value is set in any document: no denomination, relay fee or other wei value, like the price bands. Where this record says a value is unset, it means that no normative value is set. [CIP-0004](../cip/0004-sepolia-testnet-configuration.md) may set testnet-only, non-normative values for Arbitrum Sepolia; they are not defaults and not a Tornado-style ladder.

## Decision

**(1) Groups live inside `SessionEscrow`.** `SessionEscrow` holds one Semaphore v4 group per denomination index. It maintains its own LeanIMT trees (the zk-kit LeanIMT that Semaphore uses), its own nullifier set, and its own root window: a proof is accepted against the current root of its group, or against a replaced root until `MERKLE_TREE_DURATION` has passed since it was replaced. `MERKLE_TREE_DURATION` is a named deployment constant, unset; Semaphore's own default is 1 hour (evidence register §15, [V]). No function changes it. `SessionEscrow` calls only the stateless Semaphore v4 Groth16 verifier, deployed from the Semaphore packages as immutable bytecode owned by nobody. It does not call a shared Semaphore deployment's `validateProof`: that function has no access modifier, so anyone holding a user's proof could consume the nullifier outside the escrow and destroy the note (evidence register §15, [V]). The existing Arbitrum One Semaphore deployment is evidence of maturity, not our pool. Proof arguments use Semaphore's types: `uint256 merkleTreeDepth`, `uint256 merkleTreeRoot`, `uint256 nullifier`, `uint256[8] points`. `merkleTreeDepth` must lie in Semaphore's range of 1 to 32 (evidence register §15, [V]). The phone proving times cited below are for the deepest circuit, Semaphore-32, and depth is not a claim about the anonymity set.

**(2) Denominations and the relay fee.** `setCreditParameters(denominationWei, relayFeeWei)` is governance only, through the same timelock as `setBands`. A non-zero `denominationWei` appends one denomination index; the list is append-only and an index's value never changes. `denominationWei == 0` appends nothing and only sets the fee. Every call sets `RELAY_FEE_WEI`, which may be 0. A denomination must be at least `MIN_DEPOSIT_WEI`, so a credit session satisfies the deposit floor by construction. An append is rejected unless, with the new denomination included, every remainder below the largest listed denomination can be greedily decomposed into at most `MAX_CHANGE_NOTES` notes with dust below the smallest denomination; that compatibility check is what makes the dust guarantee in (7) hold. No normative value is set here, no Tornado-style ladder is proposed, and no minimum anonymity set is claimed. On Arbitrum Sepolia, [GOVERNANCE.md](../../GOVERNANCE.md) section 7.1 applies; mainnet unchanged.

**(3) Deposit.** `depositNote(identityCommitment, denominationIndex)` is payable with `msg.value` equal to that denomination. It inserts the commitment into that index's group and records `depositedWei[msg.sender][denominationIndex] += msg.value`. The deposit is the one public, wallet-linked step. Every note, whether from a deposit or from change, carries a fresh Semaphore identity generated by the client, which stores the note secret durably before the commitment is published. With a fixed scope per group an identity has exactly one nullifier per group, so a reused identity makes a second note unspendable, and the same commitment in two groups links them publicly. `SessionEscrow` keeps `noteSeen[commitment]`; `depositNote` and `claimChange` revert on any commitment already seen in any group. That check does not depend on LeanIMT's duplicate-leaf behaviour, which stays UNVERIFIED.

**(4) Spend.** `openSessionFromCredit` is called by the node or by any broadcaster, never required from the user's wallet. The proof is a Semaphore v4 proof for the denomination's group. The contract computes scope and message itself and never trusts caller-supplied values: scope is `keccak256(chainId, escrow, denominationIndex)`, fixed per group, so each note has exactly one nullifier and can be spent once; message is `keccak256(node, relay, modelId, mode, sessionSigner, expectedPriceInPerMillion, expectedPriceOutPerMillion)`, so a submitter cannot redirect the spend. Both are passed to the verifier hashed as Semaphore does, `uint256(keccak256(abi.encodePacked(x))) >> 8` (evidence register §15, [V]). On success the contract stores the nullifier and opens a session with `user = address(0)`, `funding = credit`, `depositWei = maxSpendWei =` the denomination, `relay` and `relayFeeWei` copied from the registry and `RELAY_FEE_WEI` at that moment, and `pendingWei = 0`. Every `openSession` check except `msg.value` applies: price binding against the offer, `commercialHosting`, the mode bit, the band, `sessionSigner ≠ 0`, and `maxTier` is never read. In addition `relay` must be a registered relay that is not deregistering and `relay ≠ node`.

**(5) Vouchers and the relay split.** The `Voucher` type string, `redeemVoucher` and the exact floor payment rule are unchanged. For a credit session each incremental payout splits as `relayDelta = min(relayFeeWei, newSettled) − min(relayFeeWei, oldSettled)` to `balances[relay]` and `nodeDelta = payout − relayDelta` to `balances[node]`, so the first `relayFeeWei` of settled value goes to the relay and the rest to the node. `topUp` reverts on a credit session. When the cap is exhausted the client opens a new credit session with a new note.

**(6) Settlement.** `closeWithVoucher` and `finalize` on a credit session credit nothing to `balances[user]`. They record `pendingWei = depositWei − settledWei`, which is the full denomination when `settledWei == 0`. No leaf is inserted at close or finalize, so settlement can never be blocked by a commitment check. There is no refund commitment in the message, the record, the events or the close path.

**(7) Change.** `claimChange(sessionId, changeCommitments[], denominationIndexes[], signature)` is callable by anyone, with no deadline, while `pendingWei > 0`. It is allowed in status `settled`, the one exception to the rule that a settled session accepts no call. It is authorised by a `sessionSigner` EIP-712 signature over `(chainId, escrow, sessionId, keccak256(changeCommitments), keccak256(denominationIndexes))`. At most `MAX_CHANGE_NOTES` entries, a named constant, unset and small. The listed denominations must sum to at most `pendingWei`; each commitment must be fresh under `noteSeen`; each is inserted into its group. Dust is `pendingWei − sum` and goes to `balances[node]`; `pendingWei` is then zeroed. An empty array is the dust-only branch. The client decomposes greedily from the largest listed denomination, so dust stays below the smallest denomination.

**(8) Ragequit.** `ragequit(denominationIndex, merkleTreeDepth, merkleTreeRoot, nullifier, points)` pays `balances[msg.sender]` one denomination for one note of that group that the caller proves, under the group scope with message `keccak256("ragequit", msg.sender)`. It stores the nullifier. It is allowed only while `depositedWei[msg.sender][denominationIndex] − ragequitWei[msg.sender][denominationIndex] ≥ denomination`, and it increments `ragequitWei` by the denomination, so an address never exits more than it deposited into that group. It is public and linkable by design. Because a Semaphore proof hides which leaf is spent, it cannot tell deposit notes from change notes, and no document claims otherwise. The credited balance leaves through the ordinary `withdraw()`. There is no dedicated anonymous withdrawal entry point, no association-set gate, no admin key over notes, no token, no treasury, and the protocol fee is 0.

**(9) Invariants.** Per credit session, at all times: `nodeCredited + relayCredited + remainingLockedWei + pendingWei + mintedChangeValue = depositWei`, where `remainingLockedWei = depositWei − settledWei` while the session is open or closing and 0 after settlement, and `nodeCredited` includes the dust exactly once, after `claimChange`. Pool-wide: `address(this).balance == Σ balances + Σ open or closing (depositWei − settledWei) + Σ pendingWei + Σ unspent note face value`. Pricing fixtures use the same equations.

**(10) Gas and proving.** A spend costs about 230–270k L2 gas (evidence register §15, [U]: an estimate for Semaphore's `validateProof`, not a measurement of this contract). LeanIMT insertion gas is UNVERIFIED. Phone proving is 143–2,146 ms [V] (Semaphore-32) (evidence register §15). Nodes bear the spend gas and price it into their offers; a broadcaster that submits for a node is the node's own arrangement.

**(11) Anonymity set.** The set is the group of one denomination. No authoritative minimum anonymity-set size was found (evidence register §15, [U]). The client shows the group size and warns below a threshold the CIP sets. Refund linkage is mitigated by fixed-denomination change, by a client-side delay before spending change (unset) and by a deposit-to-spend delay (unset) (evidence register §15, [V]).

**(12) Compliance, stated as facts** (evidence register §16): the contract is immutable and no key can move a note; deposits are public; ragequit is public and pays only the caller, bounded by the caller's own deposits. There is no dedicated anonymous withdrawal entry point. A credit holder who operates a node can open a session to it, sign vouchers and withdraw that node's balance, because the contract does not verify that inference happened. Regulatory classification is UNVERIFIED and is a Phase 4 review item (facts in evidence register §16, not legal advice). AMLR Article 79(1) binds credit institutions, financial institutions and crypto-asset service providers and applies from 10 July 2027 (evidence register §16, [V] for the text, [L] for the date). The DOJ policy of 21 August 2025 on truly decentralized software, the open Storm case with its retrial date, the Van Loon ruling and the Tornado Cash delisting are recorded in evidence register §16. Association sets are a later CIP. This record does not decide whether anyone is a money transmitter or a CASP.

**(13) Wallet path.** `openSession`, `topUp` and user refunds remain specified for a direct caller. The reference client has no call site for them, and no document offers that path as a privacy mode.

**(14) Non-upgradeable.** The credit-holding `SessionEscrow` is deployed without a proxy and without an upgrade path. Governance parameters (`setBands`, `setCreditParameters`) stay timelocked. On Arbitrum Sepolia, GOVERNANCE.md section 7.1 applies; mainnet unchanged. The other three contracts keep their current upgrade wording.

**(15) The amended closed list.** Twenty-three state-changing functions: the original fifteen plus eight new names. New names, and no others: `depositNote`, `openSessionFromCredit`, `claimChange`, `ragequit`, `setCreditParameters`, `registerRelay`, `updateRelay`, `deregisterRelay`. `setContext` keeps its name with changed parameters ([ADR 0012](0012-contexts-without-a-wallet-link.md)). `registerNode` and `updateNode` gain `ohttpKeyConfig`. `withdrawBond` and `closeSession` keep their names and are extended. `redeemVoucher`, `closeWithVoucher` and `finalize` keep their signatures and gain the credit-session rules above.

| # | Function | Contract | Status | Signature and rule |
|---|---|---|---|---|
| 1 | `registerNode` | NodeRegistry | amended | `registerNode(bytes hpkePublicKey, bytes ohttpKeyConfig, string endpoint, HardwareClass hardwareClass, Tier maxTier, bytes32 benchmarkHash, uint8 modes, bytes32[] modelIds, Offer[] offers) payable`. Reverts if the caller is a registered relay. |
| 2 | `updateNode` | NodeRegistry | amended | `updateNode(bytes hpkePublicKey, bytes ohttpKeyConfig, string endpoint, HardwareClass hardwareClass, Tier maxTier, bytes32 benchmarkHash, uint8 modes, bytes32[] modelIds, Offer[] offers)`. Replace-all semantics unchanged. |
| 3 | `deregisterNode` | NodeRegistry | unchanged | `deregisterNode()` |
| 4 | `withdrawBond` | NodeRegistry | extended | `withdrawBond()`. For a node as today. For a relay: after `deregisterRelay` set `unlockAt`, and `block.timestamp ≥ unlockAt`, credits the relay's `bondWei` to `balances[operator]` and deletes the Relay record. Requires and deletes no Node record in that branch. |
| 5 | `withdraw` | NodeRegistry and SessionEscrow | unchanged | `withdraw()` |
| 6 | `registerModel` | ModelRegistry | unchanged | `registerModel(bytes32 manifestHash, Tier tier, string licenseSpdx, bool commercialHosting, string metadataUri)` |
| 7 | `updateModel` | ModelRegistry | unchanged | `updateModel(bytes32 modelId, string licenseSpdx, bool commercialHosting, string metadataUri)` |
| 8 | `setContext` | ContextRegistry | amended | `setContext(bytes32 contextId, uint64 version, bytes32 contentHash, bytes contextPubKey, bytes signature)`. Any caller; rules in ADR 0012. |
| 9 | `openSession` | SessionEscrow | unchanged | `openSession(address node, bytes32 modelId, Mode mode, address sessionSigner, uint256 maxSpendWei, uint256 expectedPriceInPerMillion, uint256 expectedPriceOutPerMillion) payable returns (bytes32 sessionId)`. Records `funding = wallet`, `relay = address(0)`, `relayFeeWei = 0`. |
| 10 | `topUp` | SessionEscrow | unchanged | `topUp(bytes32 sessionId, uint256 newMaxSpendWei) payable`. Reverts when `funding == credit`. |
| 11 | `redeemVoucher` | SessionEscrow | amended | `redeemVoucher(bytes32 sessionId, Voucher voucher, bytes signature)`. Credit sessions apply the relay split of (5). |
| 12 | `closeWithVoucher` | SessionEscrow | amended | `closeWithVoucher(bytes32 sessionId, Voucher voucher, bytes signature)`. Credit sessions apply the relay split and record `pendingWei` instead of crediting `balances[user]`. |
| 13 | `closeSession` | SessionEscrow | extended | `closeSession(bytes32 sessionId, bytes signature)`. Wallet session: the user or the node, `signature` ignored. Credit session: the node, or any caller whose `signature` is a `sessionSigner` EIP-712 signature over `(chainId, escrow, sessionId, "close")`. Not permissionless. The reference client submits it through a relay or broadcaster, never from the deposit wallet. If both the node and the sessionSigner key are gone, the session stays open. |
| 14 | `finalize` | SessionEscrow | amended | `finalize(bytes32 sessionId)`. Anyone. Credit sessions record `pendingWei = depositWei − settledWei` and credit nothing to a user. |
| 15 | `setBands` | NodeRegistry | unchanged | `setBands(Tier tier, Band[4] bands)` |
| 16 | `setCreditParameters` | SessionEscrow | new | `setCreditParameters(uint256 denominationWei, uint256 relayFeeWei)`. Governance only; rules in (2), including the `MAX_CHANGE_NOTES` compatibility check on every append. |
| 17 | `depositNote` | SessionEscrow | new | `depositNote(uint256 identityCommitment, uint8 denominationIndex) payable`. `msg.value` equals the denomination; rules in (3). |
| 18 | `openSessionFromCredit` | SessionEscrow | new | `openSessionFromCredit(address node, address relay, bytes32 modelId, Mode mode, address sessionSigner, uint256 expectedPriceInPerMillion, uint256 expectedPriceOutPerMillion, uint8 denominationIndex, uint256 merkleTreeDepth, uint256 merkleTreeRoot, uint256 nullifier, uint256[8] points) returns (bytes32 sessionId)`. Rules in (4). |
| 19 | `claimChange` | SessionEscrow | new | `claimChange(bytes32 sessionId, uint256[] changeCommitments, uint8[] denominationIndexes, bytes signature)`. Rules in (7). |
| 20 | `ragequit` | SessionEscrow | new | `ragequit(uint8 denominationIndex, uint256 merkleTreeDepth, uint256 merkleTreeRoot, uint256 nullifier, uint256[8] points)`. Rules in (8). |
| 21 | `registerRelay` | NodeRegistry | new | `registerRelay(string endpoint) payable`. `msg.value ≥ MIN_RELAY_BOND_WEI` (named, unset). Reverts if the caller is a registered node or relay. Creates a Relay record `(operator, endpoint, bondWei, unlockAt = 0)`. |
| 22 | `updateRelay` | NodeRegistry | new | `updateRelay(string endpoint)`. The relay's operator, while `unlockAt == 0`. |
| 23 | `deregisterRelay` | NodeRegistry | new | `deregisterRelay()`. The relay's operator; sets `unlockAt = block.timestamp + BOND_UNLOCK_DELAY`. Open sessions that name the relay continue and still pay it. |

New session fields: `funding` (`uint8`: 0 wallet, 1 credit), `relay` (`address`), `relayFeeWei` (`uint256`), `pendingWei` (`uint256`). New escrow state: one LeanIMT per denomination index, the root window, the nullifier set, `noteSeen`, `depositedWei[address][index]`, `ragequitWei[address][index]`, the denomination list and `RELAY_FEE_WEI`. New registry state: Relay records and the relay bond. New named parameters, all unset: `MERKLE_TREE_DURATION`, `MAX_CHANGE_NOTES`, `MIN_RELAY_BOND_WEI`, `RELAY_FEE_WEI`. Each new function emits at least one event; the exact event fields are defined once in the contracts document, as today.

## Alternatives considered

### A custom join-split circuit with its own ceremony

Deferred. Arbitrary-amount notes would remove dust and the fixed-denomination change rule, but there is no audited circuit and no trusted setup for it, and a Comuns-run ceremony would be a new trust assumption with nobody seated to run it. Semaphore's circuit, setup and audits exist today (evidence register §15, [V]). No audit claim transfers to the Comuns wrapper around it.

### Reusing Privacy Pools

Rejected. Only an Ethereum mainnet ETH pool is listed; no Arbitrum deployment was found, and its anonymity set is the ASP-approved subset (evidence register §15, [V]/[L]). Its change pattern and public ragequit are borrowed as ideas, not as a dependency. An association set may be a later CIP.

### Railgun

Rejected. It charges 0.25% on each shield and unshield, broadcasters add about 10% over gas, lists gate new shields, and a DAO governs it with contract permissions that L2BEAT flags (evidence register §15, [V]). Protocol fee 0 and no token (ADR 0007) rule it out.

### Tornado-style anonymous withdrawal

Rejected. A fixed-denomination pool with anonymous withdrawal to any address is a mixer by construction, carries the 2022–2025 sanctions history and the open criminal case (evidence register §16, [V]), and would need a governance it has already been attacked through (evidence register §15, [V]). This record has no dedicated anonymous withdrawal entry point; the exits are a session, including one to a node the credit holder operates, or a public ragequit to the caller.

### Blind-signature tokens

Rejected. Privacy Pass tokens carry no amount (evidence register §15, [V]), and an issuer holds a secret key so issuance is off-chain (evidence register §15, [U]). Nym already runs a t-of-n quorum (evidence register §15, [V]); this record does not use one. Per-node issuers fragment the anonymity set (evidence register §15, [V]).

### Off-chain-only RLN spends

Rejected. Verifying spends off-chain at the node, as zkAPI does (evidence register §15, [V]/[L]), would make settlement depend on the node's honesty and give the voucher flow nothing to settle against. The spend is on-chain so the session is funded on-chain.

### Variable-amount refunds to `balances[user]`

Rejected. A refund amount is a re-linking channel, and a forum simulation recovered per-user chains from exactly that (evidence register §15, [V]). Credit sessions have no `user`, and change is fixed-denomination notes plus dust to the node.

### A shared Semaphore deployment's `validateProof`

Rejected. It has no access modifier and would let any holder of a proof consume the nullifier outside the escrow (evidence register §15, [V]). The escrow keeps its own trees, nullifiers and root window and calls only the verifier.

### An upgradeable `SessionEscrow` behind a timelock

Rejected. An upgrade key over the contract that holds the notes is an admin key over every note. The escrow is immutable; a defect is fixed by a new deployment that users migrate to by ragequit or by spending down.

## Consequences

- Eight new functions and four amended signatures need a CIP that amends the contracts document; the count becomes 23. [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) proposes it.
- The Phase 1 Sepolia slice needs at least two testnet-only denominations (no normative value is set; testnet-only, non-normative values are proposed in [CIP-0004](../cip/0004-sepolia-testnet-configuration.md)) so that its exit can demonstrate a partial spend with `claimChange` into at least one smaller note plus dust, a zero-use session claimed back in full, and a `ragequit`.
- The anonymity set per denomination is small at launch and the client must say so. One study reported that address reuse and fund-flow links traced 5.1–12.6% of withdrawals, with FIFO timing adding 15–22 percentage points; v3 of that paper was withdrawn over reference errors (evidence register §15, [V]).
- Every spend is a Groth16 verification paid by the node. Node offers will reflect it.
- A note whose secret is lost is gone. There is no recovery and no admin.
- Dust accrues to nodes. With greedy change it stays below the smallest denomination per session; the CIP's ladder decides how much that is.
- Change notes re-enter the same groups. A change note spent too soon after its session settles is linkable by timing; the client delays, and the delay is unset.
- `claimChange` in status `settled` is the one exception to "settled accepts no call" and the state machine must say so.
- A credit holder who runs a node can pay itself; the contract does not know whether inference happened. The compliance paragraph above records the consequence.
- The pricing fixtures gain credit-session cases that satisfy the invariants in (9).
- Accounting bugs in the split, the dust branch and the root window are the highest-severity risk of this record. An external review is required before mainnet holds notes; none has been performed.

## Links

- [docs/evidence-register.md](../evidence-register.md) §15, §16
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0007](0007-no-protocol-token-in-v1.md)
- [ADR 0010](0010-anonymous-by-default.md)
- [ADR 0012](0012-contexts-without-a-wallet-link.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md)
- [docs/economics/pricing-examples.json](../economics/pricing-examples.json)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
- [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)
- [CIP-0004](../cip/0004-sepolia-testnet-configuration.md) (testnet-only, non-normative values)
