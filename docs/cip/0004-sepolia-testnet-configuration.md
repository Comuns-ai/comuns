# CIP 0004: Arbitrum Sepolia testnet configuration (testnet-only, non-normative)

Status: Draft
Type: economics
Created: 2026-10-15
Requires: 0002, 0003, 0005

This CIP is Draft. It is not in Last Call and it is not Final, and it adopts nothing. **Every value in this CIP is testnet-only and non-normative: it sets no mainnet value, and it must never be copied as a default into a mainnet deployment, a later CIP, a client or a node.** Sentences elsewhere in the documentation that say no value is set refer to normative (mainnet) values, and they stay true while this CIP exists and after it becomes Final. The Type is economics because the binding content is the table of price bands, denominations, relay fee, bonds and deadlines in the Specification. Because its subject is the deployment and configuration of the contracts, it takes two reviews under CONTRIBUTING.md section 4. It cannot become Final before [CIP-0002](0002-anonymous-credits-relays-and-ownerless-contexts.md), [CIP-0003](0003-bootstrap-first-maintainer-and-channels.md) and [CIP-0005](0005-phase-one-implementation.md) are Final, and it cannot enter Last Call while the item "Model to register" below is open.

## Abstract

If this CIP becomes Final, the seated maintainer deploys the four Comuns contracts and the stateless Semaphore verifier to Arbitrum Sepolia, without a proxy and without an upgrade path, and immediately executes, from one disposable testnet key, the testnet-only configuration written here: one band table for tier T0, a three-rung denomination ladder of 1,000,000,000,000, 2,000,000,000,000 and 4,000,000,000,000 wei with `MAX_CHANGE_NOTES = 2`, a relay fee of 100,000,000,000 wei, equal node and relay bonds, the deployment constants, and one Apache-2.0 or MIT model of tier T0. That is the configuration the Phase 1 slice of docs/project-plan.md needs before `openSessionFromCredit` can be tested. The testnet timelock is 0 under GOVERNANCE.md section 7.1; mainnet rules do not change. Deployed addresses, transaction hashes and operator settings are recorded afterwards in [docs/deployments/arbitrum-sepolia.md](../deployments/arbitrum-sepolia.md), never in this file.

## Motivation

Phase 1 of docs/project-plan.md (section 6) requires a Sepolia CIP that "defines the disposable testnet configuration, governance-only model registration and testnet-only bands and a testnet-only ladder of at least two denominations, all explicitly non-normative". The ladder must pass the `MAX_CHANGE_NOTES` compatibility check, and the relevant bands and credit parameters must be initialized before `openSessionFromCredit` is tested. The contracts document (docs/protocol/contracts-and-settlement.md, section 13, item 7) asks for that Sepolia exercise. RR-28 asks for a testnet CIP that initializes the Sepolia bands; it does not specify the ladder or the credit-path exit. RR-10 asks for a Sepolia-only CIP for the small Apache-2.0 or MIT model.

Without this CIP, nothing in the Phase 1 exit can be exercised: `setBands` and `setCreditParameters` have never been called, so every band is uninitialized and the denomination list is empty, and `openSessionFromCredit` fails closed. Several named values have no setter at all in the 23-function list, so they must be compiled into the deployment and need a written source. A written proposal is the right tool because every setter in the contracts document is governance-only, acting on a CIP, and because the first values anyone writes down are the ones most likely to be copied; writing them in a labelled, testnet-only CIP keeps them out of the normative record. The proposal does not rely on a token, a coin vote or an ARB balance.

## Specification

### Scope of every value

Every number in this section is **testnet-only, non-normative**. It applies to one disposable deployment on Arbitrum Sepolia. It is not a mainnet value, a recommended value, a default or evidence about mainnet economics. Mainnet still needs a separate parameter CIP for every value below, including forty directional band entries (docs/protocol/contracts-and-settlement.md, section 9). This CIP changes no protocol fee: the protocol fee stays 0.

### Parameter table

All wei amounts are integers. Band values are in wei per 1,000,000 tokens, the unit of `priceInPerMillion` and `priceOutPerMillion`. Durations are in seconds.

| Parameter | Value | Scope | Reason |
|---|---|---|---|
| Network | Arbitrum Sepolia | testnet-only, non-normative | The Phase 1 slice is a disposable testnet deployment; nothing of value is at stake |
| Chain id | UNVERIFIED: not in the evidence register; the deployer reads it from the connected network at deployment and records it in docs/deployments/arbitrum-sepolia.md | testnet-only, non-normative | No chain id is written here, because none is sourced; reading it from the network avoids copying an unchecked number |
| EIP-712 domain of `SessionEscrow` | name `Comuns SessionEscrow`, version `1`; `chainId` and `verifyingContract` are filled only in the deployment record | testnet-only, non-normative | Same name and version as the contracts document; chainId and verifyingContract come only from this deployment, so a testnet signature does not verify on mainnet or on a redeployed escrow |
| `MIN_DEPOSIT_WEI` | 1000000000000 | testnet-only, non-normative | Equals the smallest denomination, so every listed denomination meets the floor by construction |
| `MAX_CHANGE_NOTES` | 2 | testnet-only, non-normative | The smallest bound the ladder below satisfies (proof below) |
| `MIN_BOND_WEI` | 1000000000000000 | testnet-only, non-normative | A non-zero bond so the bond, unlock and `withdrawBond` paths are exercised; no economic threshold is asserted |
| `MIN_RELAY_BOND_WEI` | 1000000000000000 | testnet-only, non-normative | Equal to `MIN_BOND_WEI` for testnet simplicity; whether they should differ is contracts question 21, open for mainnet, as question 3 is for the node bond |
| `MERKLE_TREE_DURATION` | 3600 | testnet-only, non-normative | Semaphore's own default of one hour (evidence register §15, [V]), used only as this testnet constant; contracts question 23 stays open for mainnet |
| `CLOSE_WINDOW` | 259200 | testnet-only, non-normative | About one day of L1 force inclusion (evidence register §1, [V]), plus a one-day outage budget, plus one day of margin; this sizing is not a guarantee when an outage starts near the deadline |
| `BOND_UNLOCK_DELAY` | 345600 | testnet-only, non-normative | Exceeds `CLOSE_WINDOW` by one day (86400), so a deregistering node's open sessions can settle while it is still bonded; this is the testnet answer to contracts question 4 only |
| `CHUNK_TOKENS` | 32, one protocol-wide testnet constant | testnet-only, non-normative | Gives several chunks, receipts and vouchers per short completion; contracts question 1 (per node or protocol-wide) stays open for mainnet |
| `UPGRADE_TIMELOCK` | Not applicable: no contract on this deployment has an upgrade path (see "Upgrades") | testnet-only, non-normative | Nothing can be upgraded, so there is nothing for the constant to delay |
| T0 band, class S | input [1000000000000000, 2000000000000000]; output [2000000000000000, 4000000000000000] | testnet-only, non-normative | Synthetic, strictly separated intervals that satisfy the `setBands` precondition; not measured costs |
| T0 band, class M | input [3000000000000000, 4000000000000000]; output [5000000000000000, 6000000000000000] | testnet-only, non-normative | As for class S |
| T0 band, class L | input [5000000000000000, 6000000000000000]; output [7000000000000000, 8000000000000000] | testnet-only, non-normative | As for class S |
| T0 band, class X | input [7000000000000000, 8000000000000000]; output [9000000000000000, 10000000000000000] | testnet-only, non-normative | As for class S |
| Denomination index 0 | 1000000000000 | testnet-only, non-normative | The smallest rung, u; dust is always below it |
| Denomination index 1 | 2000000000000 | testnet-only, non-normative | 2u: with u, decomposes every remainder below 4u into at most two notes |
| Denomination index 2 | 4000000000000 | testnet-only, non-normative | 4u: large enough for the worked example's session, and makes the two-note `claimChange` path reachable |
| `RELAY_FEE_WEI` | 100000000000, passed on each of the three `setCreditParameters` calls | testnet-only, non-normative | Non-zero so the relay split is exercised; it is taken from settled value and never added to what the user pays |
| Offer used by the Phase 1 node | input 1000000000000000, output 2000000000000000 (the class S floors) | testnet-only, non-normative | Inside the T0 class S band, so the band check passes at open; a node operator's choice, recorded here only to make the worked example concrete |
| Testnet timelock | 0 | testnet-only, non-normative | GOVERNANCE.md section 7.1 applies on Arbitrum Sepolia; mainnet keeps a timelock of at least 7 days |

Constants with no setter. The 23-function list has no setter for `MIN_DEPOSIT_WEI`, `MAX_CHANGE_NOTES`, `MIN_BOND_WEI`, `MIN_RELAY_BOND_WEI`, `MERKLE_TREE_DURATION`, `CLOSE_WINDOW`, `BOND_UNLOCK_DELAY` or `CHUNK_TOKENS`. On this deployment they are compiled in, and changing one means a new deployment under a new Final CIP.

### Bands

The bands are written by one call, `setBands(T0, [S, M, L, X])`, with the values in the table. The caller sets `initialized` to true in all four `Band` entries (contracts question 19 stays open for the implementation; this call is valid whichever way it is answered). The precondition holds in both directions:

- floor is at most ceiling in every class and direction;
- input: S ceiling 2000000000000000 < M floor 3000000000000000; M ceiling 4000000000000000 < L floor 5000000000000000; L ceiling 6000000000000000 < X floor 7000000000000000;
- output: S ceiling 4000000000000000 < M floor 5000000000000000; M ceiling 6000000000000000 < L floor 7000000000000000; L ceiling 8000000000000000 < X floor 9000000000000000.

Tiers T1, T2, T3 and T4 stay uninitialized, so any session for a model of those tiers fails closed. The single Phase 1 offer uses the class S floors.

### Denomination ladder and the greedy proof

The ladder is appended in this order by three calls, `setCreditParameters(1000000000000, 100000000000)`, `setCreditParameters(2000000000000, 100000000000)` and `setCreditParameters(4000000000000, 100000000000)`, giving denomination indexes 0, 1 and 2. Every denomination is at least `MIN_DEPOSIT_WEI`. The check in `setCreditParameters` runs on every append, so every prefix of the ladder must pass it as well as the full ladder.

Write u = 1000000000000, so the ladder is [u, 2u, 4u] and `MAX_CHANGE_NOTES` = 2.

- **Full ladder [u, 2u, 4u].** Every remainder r below the largest denomination 4u can be written r = k·u + d with 0 ≤ d < u and k in {0, 1, 2, 3}. Greedy decomposition from the largest denomination gives: k = 0, no note; k = 1, one note u; k = 2, one note 2u; k = 3, two notes 2u + u. In every case at most 2 notes are minted and the dust is d < u, below the smallest denomination. So the full ladder passes with `MAX_CHANGE_NOTES` = 2, and no smaller bound passes, because k = 3 needs two notes.
- **Prefix [u].** Every remainder below u decomposes into 0 notes with dust r < u.
- **Prefix [u, 2u].** Every remainder below 2u is r = k·u + d with k in {0, 1}; greedy uses 0 notes or one note u, so at most 1 note, with dust d < u.
- **A remainder equal to the largest denomination.** A zero-use session on a 4u note leaves exactly 4u, which greedy turns into one 4u note with dust 0.

This ladder is not the fixture ladder in docs/economics/pricing-examples.json, whose values are fixtures that must not be copied as defaults; it is a separate synthetic ladder chosen for the proof above.

### Worked example (testnet-only, non-normative)

A client deposits one 4u note (4000000000000 wei, index 2) with `depositNote`. Later it spends the note in `openSessionFromCredit` with the Phase 1 node, through the registered relay, at the class S floors. The job has 128 input tokens and 128 output tokens, streamed in four chunks of `CHUNK_TOKENS` = 32. The payment rule of the contracts document is `paymentWei = (priceInPerMillion * inputTokens + priceOutPerMillion * outputTokens) / 1000000`:

| Voucher | inputTokens | outputTokens | cumulativeWei |
|---|---|---|---|
| Input voucher | 128 | 0 | 128000000000 |
| After chunk 1 | 128 | 32 | 192000000000 |
| After chunk 2 | 128 | 64 | 256000000000 |
| After chunk 3 | 128 | 96 | 320000000000 |
| After chunk 4, final | 128 | 128 | 384000000000 |

So the session settles 128 × 1000000000000000 / 1000000 + 128 × 2000000000000000 / 1000000 = 128000000000 + 256000000000 = 384000000000 wei. The relay receives the first `relayFeeWei` of settled value, 100000000000 wei, and the node receives 284000000000 wei. The remainder is recorded as `pendingWei` = 4000000000000 − 384000000000 = 3616000000000 wei. `claimChange` decomposes it greedily into two fresh notes, 2000000000000 (index 1) and 1000000000000 (index 0), and the dust 616000000000 wei, below u, goes to the node. Value is conserved: 100000000000 + 284000000000 + 3616000000000 = 4000000000000, and 2000000000000 + 1000000000000 + 616000000000 = 3616000000000.

**Zero-use session.** A session opened from a 4u note and closed with no voucher (`closeSession` with the `sessionSigner` authorisation, then `finalize` after `CLOSE_WINDOW`) settles 0 wei. The relay fee is 0, because the relay is paid only out of settled value; `pendingWei` is 4000000000000, and `claimChange` mints one fresh 4u note with dust 0.

**Ragequit.** A depositor that has deposited a 1u note from an address and never spent it calls `ragequit(0, …)` from the same address with a proof under the group scope and the message `keccak256("ragequit", msg.sender)`. The net-deposit bound holds (1u deposited, 0 ragequit before), the nullifier is stored, `balances` of that address is credited 1000000000000 wei, and the address collects it with `withdraw()`. The exit is public and linkable by design.

**Simulated delayed-inbox submission.** The walkthrough submits one session transaction, for example a `redeemVoucher` or a `closeSession`, through Arbitrum Sepolia's delayed inbox instead of the sequencer, to rehearse the force-inclusion path that `CLOSE_WINDOW` is sized against. Whether Arbitrum Sepolia's force-inclusion delay and tooling match Arbitrum One's is UNVERIFIED and is checked when the walkthrough is run. No example in this CIP carries prompt text.

### Upgrades

`NodeRegistry`, `ModelRegistry`, `ContextRegistry` (deployed but unused in Phase 1) and `SessionEscrow` are all non-upgradeable on Arbitrum Sepolia: no proxy, no upgrade path and no upgrade owner. The stateless verifier is likewise immutable. The fix for a defect on testnet is a new deployment, which the docs/architecture/deployment-and-decentralization.md row on contract code authority already allows for the testnet deployer. `UPGRADE_TIMELOCK` is not applicable because no upgrade path exists; that is a different thing from the governance execution delay of 0 below. The choice for the three registries on mainnet (deployment open question 5) stays open.

### Verifier

The verifier is the Semaphore v4 Groth16 verifier bytecode from the Semaphore packages, immutable and owned by nobody, as ADR 0011 describes; `SessionEscrow` calls it and never a shared `validateProof`. Before deployment the deployer verifies the ceremony artifacts and the circuit, proving-key and verifying-key match (docs/project-plan.md section 11) and records the artifact hashes in the deployment record. This CIP pins no Semaphore version. It asserts nothing about the second Phase-2 ceremony's date or participant count; evidence register §15 marks those unconfirmed [L].

### Model selection predicate

Exactly one model is registered with `registerModel`. It must satisfy all of:

- its license file carries the SPDX identifier Apache-2.0 or MIT;
- `commercialHosting` is true;
- the parameter count in its manifest falls in tier T0 (at most 4B parameters, docs/node/model-registry-and-licenses.md section 3), and it fits class S;
- the registrant states, in this CIP, what they read in the license file shipped with the exact weight file (docs/node/model-registry-and-licenses.md section 5; RR-10);
- its manifest includes the tokenizer test vector (docs/protocol/off-chain-api.md section 13, R2).

Families the registrant may consider, all from evidence register §7: Gemma 4 (Apache-2.0, [V]), Phi-4 (MIT, [V]), and Qwen3 or Qwen3.5 (reported Apache-2.0, [L/V], so the sentence read is mandatory). Whether any of them has a T0 member at a quantization that fits class S is not recorded and is UNVERIFIED.

### Model to register

Status: **Open; blocks Last Call.** This item must be completed in this CIP, by an edit made before Last Call, with:

- the exact weight file, its revision and its quantization: open;
- the tokenizer and its test vector: open;
- the parameter count from the manifest: open;
- the canonical manifest and its `manifestHash`: open;
- the SPDX identifier of the license file shipped with the weight file: open;
- the sentence the registrant read in that license file: open;
- the `metadataUri` passed to `registerModel`: open.

The call is then `registerModel(manifestHash, T0, licenseSpdx, true, metadataUri)`. The resulting `modelId` and the transaction hash are on-chain observations and go only into the deployment record.

### Governance on testnet

GOVERNANCE.md section 7.1 applies on Arbitrum Sepolia; mainnet is unchanged.

- The governance address of the contracts is one disposable testnet key held by the maintainer seated by CIP-0003. There is no timelock contract on Arbitrum Sepolia, and this CIP's testnet timelock is 0.
- The deployer is the same disposable key, not a multi-party key: this is the testnet side of deployment open question 4 only. The key is never written into the repository and never reused on mainnet.
- Right after this CIP is Final (which requires CIP-0002, CIP-0003 and CIP-0005 Final), the seated maintainer, in this order: deploys the verifier and the four contracts; calls `setBands(T0, [S, M, L, X])`; makes the three `setCreditParameters` calls; calls `registerModel`.
- The Phase 1 node then registers itself with `registerNode`: `hardwareClass` S, declared (no class benchmark exists yet); `modes` with the standard-mode bit only; `maxTier` T0; a bond of at least `MIN_BOND_WEI`; one offer at the class S floors; `benchmarkHash` and `modelBenchmarkHash` set to keccak256 of its published self-benchmark artifacts. Both hashes are the operator's claims, not a class certification.
- A relay with an operator address distinct from the node's registers itself with `registerRelay` and a bond of at least `MIN_RELAY_BOND_WEI`.
- Mainnet rules (GOVERNANCE.md section 7; the governance paragraph of docs/protocol/contracts-and-settlement.md) are unchanged. This exception is not a precedent for mainnet.

### Explicitly unset by this CIP

This CIP sets no value for `paddingBuckets[]`, `tokenBatch`, the anonymity-set warning threshold, the deposit-to-spend and change-to-spend delays, or the `sessionId` derivation. The Phase 1 node advertises whatever its operator configuration sets for `paddingBuckets` and `tokenBatch`; those are operator settings recorded in the deployment record, not CIP values. In Phase 1 the client's anonymity-set warning is the observed denomination-group size together with the sentence that no minimum is adopted; `belowThreshold` stays false until a CIP adopts a threshold, and RR-39 stays in force.

### Addresses and the deployment record

This CIP contains no address. Adding one during Last Call would be a substantive edit (GOVERNANCE.md section 4.3). After this CIP is Final, the seated maintainer fills [docs/deployments/arbitrum-sepolia.md](../deployments/arbitrum-sepolia.md) by an ordinary pull request. That record is an observation of what was deployed, not a revision of this Final text. A redeployment appends new entries and never overwrites earlier ones.

## Rationale

The values are chosen to exercise every path of the Phase 1 exit, not to model costs. Alternatives considered:

- **Copying the fixture ladder or bands from docs/economics/pricing-examples.json.** Rejected: those values are labelled fixtures, docs/economics/cost-and-pricing.md says fixture values must never be copied into production as defaults, and copying them into a CIP would be the first step of exactly that.
- **A two-rung ladder.** Rejected: [u, 2u] passes with one change note, so the two-note `claimChange` path would never run on testnet, and the largest note would be smaller than the worked example needs.
- **Upgradeable registries behind a proxy.** Rejected: it would leave an upgrade key on a disposable deployer for no benefit, since a testnet redeploy costs nothing of value.
- **A testnet timelock.** Rejected by the owner's decision: nothing of value is at stake on Arbitrum Sepolia, and a delay would only slow the walkthrough. GOVERNANCE.md section 7.1 scopes the exception to this network and these setters.
- **A multi-party testnet deployer key** (deployment open question 4). Not adopted for Phase 1: with one seated maintainer there is no second party to hold a share; the question stays open for later stages.

The external facts relied on are Arbitrum's roughly one-day L1 force inclusion (evidence register §1, [V]), Semaphore's one-hour default root duration and its ceremony record (evidence register §15, [V] and [L]), and the model licenses (evidence register §7, [V] and [L/V]). The Arbitrum Sepolia chain id is not in the register and is UNVERIFIED.

## Backwards compatibility

Nothing is deployed. This CIP changes no function name, signature or event layout.

This PR scopes the sentences that say no value is set, so that they refer to normative (mainnet) values and point at this CIP, in: docs/adr/0011-anonymous-credits.md, docs/protocol/contracts-and-settlement.md, docs/security/privacy-and-contexts.md and docs/product/dapp-and-sdk.md. Read that way, none of them is contradicted: no normative value is set anywhere.

## Security considerations

The governance and deployer key is a disposable testnet key held by one person. If it is lost or compromised, the fix is a fresh deployment of this CIP's values from a new disposable key, appended to the deployment record; nothing is migrated. A compromised key could change testnet bands, append denominations, change the relay fee or register a model, but it cannot seize escrow: no function sends ETH other than `withdraw()` to the credited address, and `SessionEscrow` has no upgrade path. Nothing in this CIP affects prompts, keys, seed phrases or the confidentiality of any session.

Once code exists, a vulnerability in the deployed contracts, the node or the relay is reported privately as SECURITY.md describes, not in a public issue. The relevant threats are in docs/security/threat-model.md. The verifier artifacts are checked before deployment and their hashes recorded, as the Verifier item requires.

## Economic considerations

The protocol fee is 0 and no treasury exists; this CIP does not change either. Payment stays ETH in the project's own contracts on Arbitrum.

The testnet parameters this CIP sets are: the T0 bands for classes S, M, L and X; the three denominations; `RELAY_FEE_WEI`; `MIN_DEPOSIT_WEI`; `MAX_CHANGE_NOTES`; `MIN_BOND_WEI`; `MIN_RELAY_BOND_WEI`; `MERKLE_TREE_DURATION`; `CLOSE_WINDOW`; `BOND_UNLOCK_DELAY`; and `CHUNK_TOKENS`. All are testnet-only and non-normative. This CIP's timelock is 0, under GOVERNANCE.md section 7.1, which applies only on Arbitrum Sepolia; on mainnet the longer of 7 days and a CIP's stated timelock still applies. No value here is evidence about mainnet economics, and none may be read as a price, a cost or a recommendation. There is no protocol token and no coin vote, and ARB balances are not this project's votes.

## Reference implementation

None.

## Change log

None.

## Copyright

Copyright 2026 Comuns contributors

Licensed under the Apache License, Version 2.0 (see LICENSE)
