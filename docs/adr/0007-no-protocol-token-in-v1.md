# ADR 0007: Do not issue a protocol token in v1

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

Comuns needs a way to pay a node and a way to change the protocol. Both already have forms that do not require a new asset. Payment is ETH in `SessionEscrow` ([ADR 0004](0004-sessions-vouchers-and-no-slashing.md)). Change is a written CIP under GOVERNANCE.md: Draft, Review, Last Call of 14 days, then Final, with no coin vote. The Ethereum EIP lifecycle likewise uses no coin vote (evidence register §8, [V]).

The chain is Arbitrum One ([ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md)). That chain has its own DAO and its own asset, ARB. A reader can mistake an ARB balance, an Arbitrum vote or a grant program for a Comuns vote. The evidence register records that DAO's parameters (evidence register §1, [V]) and an audit program denominated in ARB (evidence register §8, [V]). None of that is this project's governance, and no grant has been awarded to Comuns.

The protocol fee is 0, so no treasury exists. Emissions would need a treasury, a schedule and a reason to pay operators in a new asset rather than in the ETH the user already deposited. v1 has no such reason.

Nothing runs yet. Issuing an asset before a network exists would create a voting and regulatory surface for a repository of documents.

## Decision

v1 does not issue a protocol token.

- Users pay nodes in ETH. Inference payment is not L2 gas and is not a project token.
- Governance is by CIP. Rough consensus is written objections addressed in the text, then a 14-day Last Call. There is no numerical vote.
- There are no emissions. Operators are paid by the vouchers their users sign, inside the price bands of [ADR 0005](0005-hardware-classes-and-price-bands.md), or they are not paid.
- There is no coin vote. A balance of any asset does not file, pass, block or weight a CIP. Anyone may file, including a class S operator.
- ARB balances are not this project's votes. A decision of the Arbitrum DAO does not change a Comuns CIP, an ADR or a protocol parameter. A Comuns CIP does not change Arbitrum DAO governance.
- The protocol fee stays 0. No treasury is created. This record creates no bounty and names no recipient.

A later proposal to issue a token must show what ETH and CIPs cannot do. The proposal has to name the action that a session deposit, a voucher, a price band and a CIP cannot perform, and why a new asset is the remedy. A CIP that only wants a vote, a status badge or an emission to attract operators does not meet that test. Until such a CIP is Final, no document may describe a Comuns token, a Comuns emission or a Comuns coin vote as part of v1.

Seating and removal of maintainers happen only through a Final CIP. A token balance does not seat anyone. Nobody is seated.

## Alternatives considered

### Emission-paid operators

Rejected. Paying operators from emissions, rather than from the user's ETH deposit, disconnects reward from delivered tokens. The register records networks that pay miners by emissions (evidence register §2, [L]). Comuns pays the node that the user's voucher names, up to the cap, and pays nothing else. An emission also needs a treasury. The protocol fee is 0, so no treasury exists.

### Staking a new token to speak

Rejected. The right to file a CIP does not depend on hardware class, stake or holdings. A staking gate would make speech proportional to a balance. That is a coin vote under another name. GOVERNANCE.md forbids it. A registration bond in ETH, withdrawable and never slashed ([ADR 0004](0004-sessions-vouchers-and-no-slashing.md)), is an anti-sybil deposit for node identity. It is not a speech token, and its size is unset.

### Burn-and-mint credits

Rejected. A credit that is burned to buy inference and minted to pay nodes is a second currency beside ETH. Bands, vouchers and `cumulativeWei` are already defined in wei. A credit would need an issuer, a mint rule and a redemption rule, which is a token system. v1 does not add one. A later stablecoin settlement asset, if any, is a CIP about the escrow's asset, and it still has to pass the test in this decision: what ETH cannot do.

### Using ARB votes

Rejected. ARB balances are not this project's votes. The Arbitrum DAO has its own quorum, timelock and council (evidence register §1, [V]). Importing that machinery would let an unrelated holding decide Comuns parameters, including bands and the license. Comuns governance stays in CIPs on the future public repository. Holding ARB confers no extra right to file, to block or to merge.

## Consequences

- Documents, clients and talks about v1 do not promise a token, an airdrop, an emission or a points program. There is no program to join.
- Grant programs that exist beside this project, including those recorded in evidence register §8, are not Comuns funds. No application is recorded here. Whether any application is pending is UNVERIFIED.
- A CIP that sets the protocol fee above 0 would also have to create a treasury this project does not have. No such CIP is Final. The fee remains 0.
- Price bands stay in wei ([ADR 0005](0005-hardware-classes-and-price-bands.md)). There is no token unit to denominate them in.
- The absence of a token does not by itself decide regulation of operating a node or of hosting a model. This record is not legal advice ([ADR 0006](0006-apache-2-0-and-dco.md)).
- Reviewers of a future token CIP start from the test above. The test is the bar. It is not a roadmap item.

## Links

- [docs/evidence-register.md](../evidence-register.md) §1, §2, §8
- [GOVERNANCE.md](../../GOVERNANCE.md)
- [docs/cip/README.md](../cip/README.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md)
- [ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0005](0005-hardware-classes-and-price-bands.md)
- [ADR 0006](0006-apache-2-0-and-dco.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
