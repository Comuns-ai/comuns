# ADR 0001: Settle on Arbitrum One with EVM contracts, not Stylus

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

Comuns is a community proposal for open-source decentralized LLM inference. Nothing runs yet. There is no deployment, no treasury and no seated maintainer. The chain's job in v1 is to record offers, model registrations, context hashes and ETH session escrow. Inference does not run inside a contract.

Arbitrum One is the chain the design work assumes ([docs/project-charter.md](../project-charter.md)). It has one sequencer. A transaction the sequencer ignores can be force-included from L1 after about one day (evidence register §1, [V]). There is no published sequencer-decentralization date (evidence register §1, [U]).

Stylus has been live since about September 2024 (evidence register §1, [L]). Its programs are limited to 24 KB compressed and 128 KB uncompressed, with a 365-day expiry (evidence register §1, [V]). New Stylus activations on Arbitrum One and Nova have been paused since 2026-10-02, with no reopening date, after AI-assisted hand-crafted WASM caused a chain-liveness denial of service. No user funds were at risk. Active programs keep running until expiry, and keepalive still works (evidence register §1, [V]).

A model cannot run inside a contract under those size limits. The performance the proposal wants from Rust lives in the off-chain node ([ADR 0002](0002-off-chain-rust-inference.md)).

Comuns governance and Arbitrum DAO governance are separate. A balance of ARB is not a vote on a Comuns CIP ([ADR 0007](0007-no-protocol-token-in-v1.md)).

## Decision

v1 settlement is Solidity on the EVM, on Arbitrum One. The four contracts are `NodeRegistry`, `ModelRegistry`, `ContextRegistry` and `SessionEscrow`. They are specified in [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md). Stylus is not a v1 execution environment.

Payment is in ETH. The protocol fee is 0. There is no protocol token. Inference payment is not L2 gas. L2 gas is an extra cost of the transactions that open, top up, redeem, close and withdraw.

The closed list of state-changing functions has fifteen names, including `withdraw()`. No contract pushes ETH during settlement, bond release or refund. Credits land in an internal `balances[address]` mapping. `withdraw()` is the only function that sends ETH: it zeroes `msg.sender`'s balance and then sends that amount, under checks-effects-interactions and a reentrancy guard. Every state-changing function follows the same two rules. A contract wallet that cannot receive ETH therefore cannot lock a refund, a payment or a bond.

`registerModel` and `updateModel` are callable only by the governance timelock, acting through a CIP. With nobody seated there is no mainnet registration. Models on Arbitrum Sepolia come from a testnet-only CIP. This blocks manifest squatting and a false `commercialHosting` flag.

Contracts are non-upgradeable in v1, or they sit behind a timelock of at least 7 days controlled by seated maintainers. An upgrade must not redirect escrow or change the terms of a funded session. A timelock delays an upgrade. It does not review the upgrade's content. No maintainer is seated, so no timelock can be executed.

`CLOSE_WINDOW` must exceed an expected sequencer outage plus about one day of force inclusion (evidence register §1, [V]). That sizing is not a guarantee. An outage that starts shortly before `closeDeadline` can still cost a node its unredeemed vouchers. Nodes redeem while redemption is legal. [ADR 0004](0004-sessions-vouchers-and-no-slashing.md) states the session rules.

Revisit Stylus only after a public reopening and a new ADR. Until that ADR is adopted through a CIP, no Comuns contract is a Stylus program.

ARB balances are not this project's votes.

## Alternatives considered

### Use Stylus anyway

Rejected. New activations have been paused since 2026-10-02 with no reopening date (evidence register §1, [V]). The 24 KB / 128 KB limits (evidence register §1, [V]) do not fit a model, so Stylus would not run inference. Keeping a paused toolchain on the settlement path adds a liveness dependency the EVM path does not have. Ink pricing that makes Stylus compute cheaper than the EVM (evidence register §1, [V]) does not change that, because v1 compute is off-chain.

### A dedicated Arbitrum chain

Deferred. An Arbitrum chain can use a custom ERC-20 gas token and 250 ms blocks (evidence register §1, [V]). Both are attractive for a busy inference market. Operating a chain is a separate operator burden, a separate bridge and a separate validation set. v1 settles on Arbitrum One. Whether a dedicated chain is ever worth that burden is an open question in the project charter, not a v1 decision.

### A new L1

Rejected. Comuns needs a place to escrow ETH and record offers. It does not need its own consensus, its own bridge or its own validator set. A new L1 would also be a new token surface, which [ADR 0007](0007-no-protocol-token-in-v1.md) refuses for v1. Nothing runs yet, so there is no load that would justify that cost.

### Another L2

Rejected. The project's founding requirements name Arbitrum One as the example chain (docs/requirements.md REQ-01), and every design document assumes that chain: session identifiers, force-inclusion timing, the fee snapshot used to justify sessions, and the governance split from the Arbitrum DAO. Moving the assumption to another L2 would rewrite those documents for no capability v1 uses.

## Consequences

- Rust performance lives in the off-chain node. The chain stores offers, sessions, hashes and credits.
- A Stylus return requires a public reopening and a superseding ADR. This record does not pre-approve that return.
- Session liveness follows a single sequencer. Force inclusion takes about one day (evidence register §1, [V]). `CLOSE_WINDOW` is sized against that fact and still leaves a residual risk, stated in [ADR 0004](0004-sessions-vouchers-and-no-slashing.md). "Settled" means L2 inclusion under that sequencer, not L1 finality.
- With nobody seated, bands cannot be set and models cannot be registered on mainnet, so a paid mainnet session cannot open. That is intentional.
- ARB balances, Arbitrum DAO votes and any Arbitrum grant program are outside Comuns governance. No grant is claimed.
- The chain id commonly published for Arbitrum One is recorded as UNVERIFIED in the contracts document and is confirmed at implementation. This ADR does not adopt a number for it.

## Links

- [docs/evidence-register.md](../evidence-register.md) §1
- [docs/project-charter.md](../project-charter.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [GOVERNANCE.md](../../GOVERNANCE.md)
- [ADR 0002](0002-off-chain-rust-inference.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0007](0007-no-protocol-token-in-v1.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
