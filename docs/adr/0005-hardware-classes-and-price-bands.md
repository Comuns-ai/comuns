# ADR 0005: Charge more for higher hardware classes through ordered bands

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

Operators bring different machines. A public class benchmark will sort a node into a hardware class. The class is a price label. It is not a permission to serve a model, and it is not "the highest tier the machine passed."

`hardwareClass` is one of S, M, L, X, encoded 0–3, ordered S < M < L < X. The class is self-declared and backed by a public self-benchmark. The acceptance bars are for a later CIP. `maxTier` is a separate, informational field: the largest tier the operator benchmarked. `openSession` never reads `maxTier` ([ADR 0008](0008-model-first-pools.md)).

Model tiers are a partition by the parameter count in the manifest, not a hardware ladder:

- T0: at most 4B parameters
- T1: more than 4B and at most 8B
- T2: more than 8B and at most 32B
- T3: more than 32B and at most 70B
- T4: more than 70B

An 8,000,000,000-parameter model is T1. There is no cross-tier ordering rule. The same model has one tier, and every class that can load it may offer it.

Batches on strong hardware can produce a token for less than a single stream on a small machine (evidence register §6, [V], records both single-stream and batched snapshots). If price followed that cost, a large operator would undercut every smaller one on the same model. The proposal refuses that outcome. Weaker honest operators keep a ceiling below the next class's floor for the same model. That is a democratic-access rule. It is not cost-plus pricing, and it is not a claim of lower prices than hosted APIs.

This record sets no wei value. Worksheets and fixture files elsewhere are illustrations. They are not adopted prices.

## Decision

Governance sets a price band for every pair `(tier, class)` by CIP, through `setBands(tier, bands[4])`, one call per tier covering S, M, L and X. Each band has an inclusive floor and ceiling for input and an inclusive floor and ceiling for output. Prices are wei per 1,000,000 tokens. Asks are free within the band. The protocol fee is 0.

The ordering rule, enforced by `setBands` for every tier and for input and output separately, is:

`floor(class c+1) > ceiling(class c)`

over all four classes, S < M < L < X. Adjacent corridors do not overlap. The stronger class charges more for the same model. The weaker class charges less. A quote that sits in class S's interval is outside class M's interval.

Bands exist for every `(tier, class)` pair because class does not gate which model may be offered. That serving rule is [ADR 0008](0008-model-first-pools.md). An uninitialized band means the pair is waiting for governance. It does not mean the class is forbidden to serve the tier. Five tiers and four classes make twenty pairs and forty directional entries (input and output). All forty must be set before a mainnet session can open. With nobody seated, none are set.

`registerNode`, `updateNode` and `openSession` accept a price only when it lies inside the band for `(the model's tier, the node's class)`. A hardware-class change revalidates every listed offer against the new bands and reverts if any listed offer is outside its band. Clearing an offer is always allowed. Existing sessions keep the prices copied at `openSession`.

Operators may skip a tier by not offering it. The protocol does not require a class X node to serve T0. Specialization is an economic possibility. It is not an eligibility rule, and whether it happens is UNVERIFIED.

No wei value is adopted here. A later CIP states the floors and ceilings in numbers, with the timelock GOVERNANCE.md requires. Until that CIP is Final, draft figures are not parameters.

## Alternatives considered

### Auction to the cheapest

Rejected. A reverse auction would hand the same model to whoever bids lowest. Strong hardware with batching would win on production cost and would erase the lower ceiling reserved for weaker operators. The evidence register records auction-style markets elsewhere (evidence register §2). Comuns does not copy them. The user still chooses a node inside the band by price, measured speed, reputation and mode. The band is the corridor. The ask inside it is the operator's.

### Cost-plus

Rejected. An operator's worksheet may inform the ask. It does not override the floor. A batched datacenter token can be cheaper to produce than a single-stream token, and the floor still forbids undercutting the weaker class. Publishing electricity or rental snapshots (evidence register §6) as if they were Comuns prices would launder illustrations into parameters. This record does not do that.

### One price for all classes

Rejected. A single price hides the hardware the user is paying for and removes the reason to publish a class. Stronger and weaker operators would be forced through one number, so the democratic-access gap would not exist. Class would become a badge with no economic effect.

### A new gas token

Rejected. Inference payment is ETH, and L2 gas is a separate fee the user already pays to Arbitrum. A new gas token would be a protocol token. [ADR 0007](0007-no-protocol-token-in-v1.md) forbids a protocol token in v1. Bands are denominated in wei per 1,000,000 tokens so that `SessionEscrow` can recompute `cumulativeWei` without an oracle. A stablecoin as a second settlement asset is an open question for a later CIP, not a v1 band.

## Consequences

- The accepted batching margin is intentional. Strong hardware may produce tokens more cheaply and still must price above the weaker class's ceiling for the same model. There is no promise of profit, demand or equal latency.
- Strong hardware may skip small tiers. A band can contain no willing supplier. The client says when a pool has no acceptable quote. It does not substitute a model or cross a band in silence ([ADR 0008](0008-model-first-pools.md)).
- Forty directional entries must be set by seated maintainers before mainnet. A partial table blocks pairs. Indexers show an unset pair as pending a CIP, not as a class ban.
- Fake class claims move an operator into a dearer or cheaper corridor. v1 has no slashing for that ([ADR 0004](0004-sessions-vouchers-and-no-slashing.md)). The benchmark is a public claim, not an unfakeable proof. Spot re-benchmarks use a private, rotating prompt set, and they are still not an unfakeable proof.
- ETH volatility changes the real cost of a wei band. This record states no exchange rate.
- Changing a floor, a ceiling, the protocol fee or a deadline takes a CIP that becomes Final, then the longer of 7 days and that CIP's timelock, executed by seated maintainers. Nobody is seated.

## Links

- [docs/evidence-register.md](../evidence-register.md) §2, §6
- [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/node/hardware-classes-and-benchmarks.md](../node/hardware-classes-and-benchmarks.md)
- [GOVERNANCE.md](../../GOVERNANCE.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0007](0007-no-protocol-token-in-v1.md)
- [ADR 0008](0008-model-first-pools.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
