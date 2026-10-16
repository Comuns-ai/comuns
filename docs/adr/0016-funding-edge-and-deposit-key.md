# ADR 0016: Fund notes at the edge and keep the escrow in ETH

**Status:** proposed

**Date:** 2026-10-15

**Deciders:** none seated; no adopting CIP yet

## Context

This record answers the owner's requests 1 to 3: easier payment through a key the user approves once, a fiat on-ramp so a user can buy credits with a card, and paying in a stablecoin to avoid conversion problems, with the freeze risk that a stablecoin carries. It changes no contract, proof, voucher or wire format, so no adopting CIP is proposed; adoption would require a later Final CIP.

The escrow fixes who may fund and who may exit. In [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md), the `depositNote(identityCommitment, denominationIndex)` row (:280) requires `msg.value ==` the listed denomination exactly, and the contract credits `depositedWei[msg.sender][denominationIndex]`. The `ragequit` row (:283) requires `depositedWei[msg.sender][denominationIndex] − ragequitWei[msg.sender][denominationIndex] ≥ denomination` and verifies the proof under `message = keccak256("ragequit", msg.sender)`. `depositNote` credits the public-exit allowance (`depositedWei`) of its caller, and `ragequit` lets an address exit only up to its own allowance and only with a valid note proof bound to that address; it does not bind a note to its original depositor (contracts :280, :283). A deposit made by anything other than the user's own account would credit that address's allowance instead, and the user could not ragequit that value. The rule that only the user's own account calls `depositNote` is the caller/exit invariant that every decision below rests on.

Before this record, the client document limited what the wallet signs. [docs/product/dapp-and-sdk.md](../product/dapp-and-sdk.md) said the wallet signs only `depositNote`, `ragequit` and `withdraw` and is never prompted per session, per chunk or per context grant, and that at cap exhaustion the client stops signing and offers to continue in a new credit session; this record and the edits that accompany it replace that signing sentence and keep the cap-exhaustion rule; open question 1 asks how to support contract wallets whose `depositNote` is a batched user operation, and open question 2 asks whether a later CIP could let a smart account authorize `sessionSigner` as a session key.

Timing linkage between a public deposit and a later spend is already recorded, with every delay unset: [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md) §9 and R13 and its open question on delays, [docs/security/threat-model.md](../security/threat-model.md) T33 and R18, [docs/risk-register.md](../risk-register.md) RR-39, [ADR 0011](0011-anonymous-credits.md), [CIP-0004](../cip/0004-sepolia-testnet-configuration.md), dapp R8 and the contracts document's R12. Nothing here sets a delay.

The phrase "session key" is taken. The dapp document's open question 2 uses it for a hypothetical `sessionSigner` delegation, and [docs/project-plan.md](../project-plan.md) :67 calls `commitKey` "a random session key". A deposit-only key needs a name that cannot be confused with either.

The external facts this record relies on are the "Client UX research 2026-10-15" blocks of [docs/evidence-register.md](../evidence-register.md); each is cited below with the mark of the clause used, and no [L] or [U] is upgraded.

## Decision

### (1) The escrow holds only ETH

`SessionEscrow` holds ETH and nothing else. Settlement stays ETH on Arbitrum One in the project's own contracts, and bands stay in wei.

A USDC or USDT escrow is rejected because one issuer action against the escrow address would stop every note and every pending earning from moving:

- a blacklisted USDC address "will be unable to call `transfer` or `transferFrom`, and will be unable to receive tokens", and a separate pauser role halts all transfers, minting and burning of the whole contract (evidence register §15, client UX research 2026-10-15, [V]);
- the USDT0 token on Arbitrum One has an owner-only block list with `addToBlockedList`, `removeFromBlockedList` and `destroyBlockedFunds`, which burns a blocked holder's balance (evidence register §15, client UX research 2026-10-15, [V]); a blocked USDT0 address cannot send unless the caller is the owner, but can still receive (evidence register §15, client UX research 2026-10-15, [V per the fact-check]);
- Circle's USDC terms reserve the right to block transfers to and from an address, and Tether's terms reserve the right to freeze tokens and blacklist addresses (evidence register §16, client UX research 2026-10-15, [V]);
- the precedent is on chain: Circle blacklisted the OFAC-listed Tornado Cash USDC addresses on 2022-08-08 and un-blacklisted the checked address on 2025-03-22 (evidence register §15, client UX research 2026-10-15, [V]);
- Circle's Bridged USDC terms say Circle "lacks the ability to block certain addresses or freeze Bridged USDC", but the same terms also say Circle "may also be required to freeze Bridged USDC", so "cannot freeze" is not absolute (evidence register §16, client UX research 2026-10-15, [V]), and whether those terms cover Arbitrum's bridged USDC is unverified (evidence register §16, client UX research 2026-10-15, [U]).

These are facts as the sources state them and not a legal reading of any issuer's terms. The decision is operational: a contract that holds other people's notes must not have an address that a third party can disable.

This declines the escrow change that four documents left open: the later-stablecoin sentence of [ADR 0007](0007-no-protocol-token-in-v1.md), the contracts document's open question 5, the stablecoin question in [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md) and open question 8 of [docs/architecture/deployment-and-decentralization.md](../architecture/deployment-and-decentralization.md). A second settlement asset would still be a CIP; none is proposed.

### (2) The funding-edge rule

Funding happens at the edge, in the user's own account, before the deposit. A user may:

- deposit ETH the account already holds;
- buy ETH on Arbitrum One delivered to an address the user controls. Coinbase's Layer 2 table lists ETH on Arbitrum, and the MoonPay and Transak currency listings include ETH on Arbitrum (evidence register §15, client UX research 2026-10-15, [V]; the Transak currencies API was not independently re-fetched). The Coinbase Guest Checkout, MoonPay and Transak terms each state that the buyer owns or controls the destination wallet (evidence register §16, client UX research 2026-10-15, [V]; the Coinbase Guest Checkout terms were not independently re-fetched). These are recorded as provider statements; whether they apply to any particular delivery is an open review item and no legal conclusion is drawn. Each researched provider documents a KYC or identity step (evidence register §16, client UX research 2026-10-15, [V] per provider); that every on-ramp ties the receiving address to an identity is a researcher inference (evidence register §15, client UX research 2026-10-15, [L]);
- convert a stablecoin to native ETH inside the user's own account by an exact-output swap, so the account ends with exactly one denomination's worth of ETH plus gas. SwapRouter02 has `exactOutputSingle` and `exactOutput` and can unwrap WETH to ETH in the same multicall, and the Universal Router has exact-output and unwrap commands (evidence register §15, client UX research 2026-10-15, [V]); Uniswap v4 treats `address(0)` as native currency (evidence register §15, client UX research 2026-10-15, [V]), and whether a native pool on Arbitrum has enough liquidity is unknown (evidence register §15, client UX research 2026-10-15, [U]);
- or convert by an intent whose output recipient is the user's own account: ordinary swap intents support exact output (evidence register §15, client UX research 2026-10-15, [V]), and a multi-chain intent is not atomic, since "funds can arrive before a later destination action fails" (evidence register §4, client UX research 2026-10-15, [V]).

Candidates recorded, none selected: Coinbase Onramp, MoonPay, Transak, Stripe (whose Arbitrum support is contradictory across its own pages, evidence register §15, client UX research 2026-10-15, [V]/[U]), Rhinestone intents and its Swapped on-ramp widget (whose "service-managed deposit account" has unknown custody, evidence register §15, client UX research 2026-10-15, [U]), Uniswap v3 SwapRouter02, the Universal Router (which version is open, evidence register §15, client UX research 2026-10-15, [U]) and Uniswap v4. Recording a provider does not select it. Every price, fee and limit in those blocks is an observation dated 2026-10-15, not a value this record sets.

### (3) The caller invariant

The caller invariant: msg.sender of every depositNote is the user's own address. That address is one of:

- a plain EOA;
- that EOA delegated under EIP-7702, which ArbOS 40 includes (evidence register §1, recheck 2026-10-15, [V]); delegation leaves the address and its assets where they are (evidence register §1, client UX research 2026-10-15, [V]), and the EOA stays the root authority and cannot rotate its key (evidence register §1, client UX research 2026-10-15, [V]);
- or the user's smart account executing the call itself. Rhinestone's Intent Executor "runs destination calls through the account" (evidence register §4, client UX research 2026-10-15, [V]); that the target contract therefore sees the account as `msg.sender` is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]) and needs call traces before any integration is attempted.

No on-ramp, router, solver, bundler, sponsor, orchestrator or helper contract ever calls `depositNote`. The reason is the caller/exit invariant of the Context, not any provider's terms: a deposit made by anything other than the user's own account would credit that address's public-exit allowance (`depositedWei`) instead, and the user could not ragequit that value.

A swap-session scope alone cannot call `depositNote`, because its only operations are approving the sell token and calling the venue's swap entrypoint and "Every other operation reverts on-chain" (evidence register §15, client UX research 2026-10-15, [V]); that this excludes `depositNote` is a researcher inference (evidence register §15, client UX research 2026-10-15, [L]). One session that swaps a stablecoin to native ETH and then calls `depositNote` with an exact nonzero `msg.value` is not documented (evidence register §15, client UX research 2026-10-15, [U]). Until it is shown, conversion and deposit are two separately authorized calls from the user's account.

### (4) The deposit key

The signing matrix of the whole client, which the sibling documents carry, is:

- the account signs `depositNote`, `ragequit` and `withdraw`;
- only on opt-in, it also signs account setup, bounded swaps or intents in its own account, and the deposit-key grant and its revocation;
- `depositKey` signs `depositNote` only;
- `sessionSigner`, context keys and `commitKey` are unchanged.

The sentence the sibling documents use for signing is: "…only if the user opts in does it also sign … a deposit-key grant and its revocation (ADR 0016, proposed). The deposit key signs only `depositNote`. No account key, deposit key or login ever signs a voucher, envelope, spend, close or `claimChange`, and none is sent to a node or a relay." The sentence they use for the public step is: "the one public, wallet-linked step of the payment path (an opt-in deposit key adds a public grant and its revocation, ADR 0016)".

**Name.** SDK name `depositKey`, user-facing "deposit key". It is never called a session key, `sessionSigner` or `commitKey`.

**Where it exists.** Only on an EIP-7702 EOA or a smart account: "A plain EOA does not support ERC-7579 modules, session keys, multisig, account deployment, or ERC-4337 user operations." (evidence register §1, client UX research 2026-10-15, [V]). The core path does not need it; a user with a plain EOA deposits by hand and loses nothing.

**Permission shape.** The on-chain permission names exactly one contract, `SessionEscrow` on the chain in use, and exactly one selector, `depositNote`. Each permission is bound to one contract address and its listed selectors, so listing one function does not authorize another (evidence register §4, client UX research 2026-10-15, [V]). `valueLimitPerUse` is set to the granted denomination; it is a per-call ceiling (evidence register §4, client UX research 2026-10-15, [V]), and whether the permission can require exact equality is not documented (evidence register §4, client UX research 2026-10-15, [U]), so the contract's own `msg.value ==` check is the equality rule. `maxUses` counts per function and per chain, and `validAfter` and `validUntil` bound the window (evidence register §4, client UX research 2026-10-15, [V]); a chain that refuses the timeframe policy fails closed and the grant is not made there. The documented spending-limit policy covers ERC-20 tokens and does not mention native ETH (evidence register §4, client UX research 2026-10-15, [V]), so no cumulative ETH limit is claimed.

**Exposure.** If enforcement is correct, a stolen deposit key can move at most cap × uses of principal per grant and per chain, and only into `depositNote`. Gas and fees are separate and not bounded here. A validator or account defect is not bounded. A stolen key can create notes whose secrets the attacker holds, and the user cannot recover them. Because a stolen key chooses the `identityCommitment`, whether calldata rules can bind the grant to a prepared commitment set is a review item (UNVERIFIED; no source examined states it).

**What it never names or signs.** The grant names no node, relay, NodeRegistry, ModelRegistry, ContextRegistry, router, venue, token approval or module install. The deposit key never signs a voucher, envelope, `closeSession`, `claimChange`, `ragequit`, `withdraw` or context grant. It never pays a node or relay and is never in the spend path.

**Visibility.** The Smart Sessions v1 interface emits `SessionCreated` and `PolicyEnabled` events naming the account (evidence register §4, client UX research 2026-10-15, [V]); that grants are therefore public is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]); which validator version is deployed is unknown (evidence register §4, client UX research 2026-10-15, [U]). The client says so before the grant, with the funding-surface copy: "Your deposits are public, and the provider can link them to your identity. Sessions do not include your wallet address or login identity. Timing, small groups, identifying content and collusion can still link activity."

**Revocation.** Revocation is on-chain and chain by chain; "Deleting a local key does not revoke its onchain authority" (evidence register §4, client UX research 2026-10-15, [V]). Deleting the local key is not revocation and the client never describes it as such.

**Note secrets.** The dapp document's note-secret rule is unchanged: the note secret is generated locally from the OS CSPRNG and stored in the vault before any commitment is submitted, whether the account or the deposit key submits it.

### (5) Refill timing

A refill made with the deposit key fires on an unspent-note threshold or on a schedule with random jitter, into a buffer of notes that honour `spendableAfter`. A refill never fires at cap exhaustion, on a send or resume event, or immediately before a spend. Cap exhaustion continues only on an already-buffered eligible note; otherwise the client pauses and says why. The refill job runs inside the funding module only.

Threshold, schedule, jitter, buffer size and both delays stay unset. Buffering and scheduling are mitigations against the timing linkage of privacy R13 and threat-model T33 and R18, not guarantees. The RR-52 gate reads: "This PR sets no timing values. Automatic refills remain unavailable until a reviewed timing policy is adopted and its eligibility and trigger rules are demonstrated." A fee-policy review is also required before the convenience is enabled.

### (6) Conveniences are optional and never in the spend path

Gas sponsorship, intent orchestrators and on-ramps are optional, disclosed, replaceable conveniences. None is in the spend path: no sponsor, orchestrator or on-ramp sees a session, a voucher, a relay choice or a note secret. Sponsorship prices such as "Sponsored amount plus 10%" (evidence register §15, client UX research 2026-10-15, [V]) are observations, not adopted values. A sponsored deposit still comes from the user's account under (3). The inference cap stays the denomination; any funding fee is a separate line on the funding surface and never changes what a note is worth inside a session.

### (7) Licence facts are review items

Smart Sessions v1 declares its licence in several places: the README says AGPL-3.0, `SmartSession.sol` declares AGPL-3.0-only, `ISmartSession.sol` declares UNLICENSED, and the repository has no LICENSE file (evidence register §8, client UX research 2026-10-15, [V]). Smart Sessions v2 declares BUSL-1.1 (evidence register §8, client UX research 2026-10-15, [V]). Which version is deployed is unknown (evidence register §4, client UX research 2026-10-15, [U]). These are facts, not conclusions, and are RR-58 items.

## Alternatives considered

### A stablecoin escrow

Rejected. The freeze mechanics in (1) apply to the escrow address itself: one blacklist or block-list entry, or one pause, stops every note and every unsettled earning at once, and a `destroyBlockedFunds` call can burn them (evidence register §15, client UX research 2026-10-15, [V]). An ETH escrow has no such party. Conversion stays at the edge where only the converting user is exposed.

### A router, solver or helper contract as the `depositNote` caller

Rejected on the caller/exit invariant. `depositNote` credits the public-exit allowance of its caller and `ragequit` lets an address exit only up to its own allowance with a note proof bound to that address (contracts :280 and :283), so a deposit made by a router would credit the router's allowance, and the user could not ragequit that value. Whether a call made through the account yields the account as `msg.sender` is itself an inference (evidence register §4, client UX research 2026-10-15, [L]) that needs call traces.

### On-ramp delivery straight to the escrow

Rejected on the same invariant: the on-ramp's calling address would be the depositor, so the public-exit allowance would be credited to that address and the user could not ragequit that value. The provider statements that the buyer controls the destination wallet are recorded in §16 as statements; they are not the reason for the rejection, and whether they apply is an open review item.

### `sessionSigner` as a session key, or a wallet-funded session

Deferred. The dapp document's open question 2 stays open. Letting a smart account authorize `sessionSigner` would put an account key in the spend path and would need a CIP; none is proposed, and this record does not authorize it. The deposit key is deliberately the opposite: it funds and never spends.

### Bundler plus paymaster as the only deposit path

Rejected as a requirement. Whether a shared ERC-4337 mempool is live on Arbitrum is recorded with a conflict between sources (evidence register §1, client UX research 2026-10-15, [V] for each statement, [U] for the resolution), and the EntryPoint code identity on Arbitrum One is unverified (evidence register §1, client UX research 2026-10-15, [U]). The user's EOA or EIP-7702 EOA submits `depositNote` itself; a bundler is at most a convenience.

### Refill at cap exhaustion

Rejected. A deposit fired at the moment a session runs dry is a timing beacon that privacy R13 and threat-model T33 and R18 already describe. The client continues only on a buffered eligible note, or pauses.

### Selecting one on-ramp, DEX or orchestrator now

Deferred. The register records candidates and their observed prices; selecting one would seat a provider in a client that has not been built, and no fact in the register decides between them.

### Setting numeric delays, thresholds or jitter

Deferred, as every earlier document does. No value is adopted here; the RR-52 gate in (5) governs.

## Consequences

- No ABI, proof, voucher or wire change, so no CIP. Spends are unchanged: `sessionSigner`, vouchers, envelopes, `closeSession` and `claimChange` are exactly as ADR 0011 and the contracts document define them.
- Nothing is selected: no on-ramp, DEX, router version, orchestrator, validator, bundler or sponsor.
- Public deposits still name the account, and an opt-in deposit key adds a public grant and its revocation; the funding-surface copy in (4) replaces every absolute assurance.
- The risk register gains RR-51 (wrong `depositNote` caller), RR-52 (deposit-key scope, stolen key, validator defect and refill timing, with the gate in (5)), RR-54 (funding-edge losses with the escrow excluded) and RR-55 (a hosted convenience treated as required); ids reserved by this plan.
- The dapp document gains R10 (funding-side identity linkage) and R11 (wrong caller or deposit-key misuse), and its §11 refusals and screen 3 say "never pays a node or relay".
- The Smart Sessions licence facts become RR-58 items.
- [ADR 0017](0017-accounts-and-decentralized-access.md) carries the account tiers and the isolation of the funding surface on which the deposit key lives; [ADR 0018](0018-one-client-stack.md) carries the client stack.

## Links

- [docs/evidence-register.md](../evidence-register.md) §1, §4, §8, §15, §16 (client UX research 2026-10-15), §1 (recheck 2026-10-15), §17
- [docs/product/dapp-and-sdk.md](../product/dapp-and-sdk.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [ADR 0007](0007-no-protocol-token-in-v1.md)
- [ADR 0010](0010-anonymous-by-default.md)
- [ADR 0011](0011-anonymous-credits.md)
- [ADR 0017](0017-accounts-and-decentralized-access.md)
- [ADR 0018](0018-one-client-stack.md)
- [docs/risk-register.md](../risk-register.md)
- [CIP-0004](../cip/0004-sepolia-testnet-configuration.md)
- [CIP-0005](../cip/0005-phase-one-implementation.md)
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md)
- [docs/security/threat-model.md](../security/threat-model.md)
- [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md)
- [docs/architecture/deployment-and-decentralization.md](../architecture/deployment-and-decentralization.md)
- [docs/project-plan.md](../project-plan.md)
