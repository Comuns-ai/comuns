# ADR 0008: Model-first pools, not a class-tier serving gate

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

The user chooses a model. The nodes that currently offer that model are the set the client picks from. A request that a node may run any model it can load follows from that choice: the limit is whether the weights fit, not a table that assigns tiers to classes.

Memory, not class, decides fit. A 70B model at Q4 does not fit a 32 GB card (evidence register §6, [V]). A class label does not measure that card, and the chain has no proof of memory. `maxTier` records the largest tier an operator benchmarked. It is information. Treating it as "the highest tier this class may serve" would forbid a willing node from serving a model it can load.

An earlier assumption said that class S serves only T0, class M only through T1, class L only through T2, and class X only through `maxTier`. That assumption is a serving gate. It contradicts the user's choice of model. This record withdraws it.

Ordered bands stay. For the same model, a stronger class charges more and a weaker class charges less ([ADR 0005](0005-hardware-classes-and-price-bands.md)). The protocol fee stays 0. There is no slashing in v1 ([ADR 0004](0004-sessions-vouchers-and-no-slashing.md)). Withdrawing the gate does not withdraw those three rules.

Tiers remain a partition by parameter count: T0 at most 4B; T1 more than 4B and at most 8B; T2 more than 8B and at most 32B; T3 more than 32B and at most 70B; T4 more than 70B. Hardware class is not a tier.

## Decision

A node may offer any registered model it can load. An offer is

`prices[modelId] = (priceInPerMillion, priceOutPerMillion, modelBenchmarkHash)`

with a non-zero `modelBenchmarkHash`. The node writes offers through `registerNode` or `updateNode`. `updateNode` takes the complete offer list and replaces the stored list. It emits `OfferSet` for every model added or changed, and an `OfferSet` with zero prices and a zero `modelBenchmarkHash` (cleared) for every model removed. Clearing is always allowed, whatever the band or `commercialHosting` state. `deregisterNode` emits a cleared `OfferSet` for every offer it removes. A hardware-class change revalidates every listed offer against the new bands and reverts if any is outside its band.

The pool of a `modelId` is the set of nodes with such an offer. Clients and indexers enumerate it off-chain from `OfferSet` events: keep each operator's latest offer, drop a zero hash, drop a deregistered node, and read the current prices. The pool is never a registry record, never a payee and never a session party. The chain stores offers and sessions. It does not store a pool list, a plan or a sub-task assignment. No function pays a pool.

`maxTier` is informational and does not limit offers. `openSession` checks the offer, the band for `(the model's tier, the node's class)`, and `commercialHosting`. It never checks a class-tier matrix, and it never reads `maxTier`.

Bands exist for every `(tier, class)` pair, over all four classes S < M < L < X, with `floor(class c+1) > ceiling(class c)` for input and for output separately. Stronger hardware charges more for the same model. Forty directional entries must be set before mainnet. An unset band blocks that pair until a CIP. It does not make the class ineligible.

Memory fit and the per-model benchmark are off-chain admission. The node offers a model only when it can load it at the concurrency it advertises, and only after it has published a self-benchmark whose hash is `modelBenchmarkHash`. The chain gains no proof of memory. A stale offer — the model is no longer loaded — can still pass `openSession`. The node then refuses. The user loses gas and time, not the deposit, once the session is closed. Stale offers are a reputation risk. They are not slashing.

`registerModel` and `updateModel` are governance-only in v1, so the manifest, the tier and `commercialHosting` come from a CIP. With nobody seated there is no mainnet registration. Sepolia models come from a testnet-only CIP. A model with `commercialHosting` false can be registered and cannot be offered.

This record withdraws the class-tier serving gate: the earlier assumption that S serves only T0, M only through T1, L only through T2, and X only through `maxTier`. It withdraws that gate without withdrawing band ordering, protocol fee 0, or the no-slashing rule.

## Alternatives considered

### Keep the class-tier serving gate

Rejected. A gate that lets S serve only T0, M only through T1, L only through T2, and X only through `maxTier` forbids a willing node from serving a model it can load. It also contradicts the user's choice of model: the client would have to hide legal offers because of a class label. A 32 GB card that cannot hold a 70B Q4 model (evidence register §6, [V]) is already excluded by memory fit, without a protocol ban on the class.

### One pool that ignores modelId

Rejected. A single pool of "nodes" would make the user pick hardware first and discover the model second. Sessions, prices and manifests are per `modelId`. Mixing them would let a session pay a node for a model it did not offer. The pool is a filtered view of offers for one `modelId`.

### Class-restricted pools

Rejected. A pool per `(modelId, class)` would split liquidity and would reintroduce the gate by another route: the client would treat class as eligibility. Any class may stand in a model's pool. The class selects the band, so the same model costs more from stronger hardware. The client may prefer a class when it sorts by price or measured speed. The protocol does not require that preference.

### An on-chain proof of VRAM

Rejected. No such proof is available to these contracts. A self-benchmark is a signed claim, not an unfakeable measurement. Spot re-benchmarks use a private, rotating prompt set chosen at random times, and they remain claims. Inventing a proof the chain cannot check would be a false assurance. Admission stays off-chain.

### On-chain pool lists

Rejected. A list would copy the offers, drift from them, and cost gas to maintain. It would also invite a matcher. The chain never routes inference. Clients choose a node off-chain. An on-chain matcher would be a gas sink and a point of capture.

## Consequences

- A thin pool may hold no quote inside a band, or no offer at all. The client says so. It does not silently switch models. A substitution is a new disclosure sheet and a new confirmation.
- Forty band entries must be set before mainnet. Until then, model-first pools cannot take a paid mainnet session. That block is the unset-band rule, not a return of the serving gate.
- Stale offers are a reputation risk. The reference client asks the node for admission before `openSession`. Indexers can downrank sessions that settle with nothing paid. No slash follows.
- A class S node that loads a T4 model may offer it inside the (T4, S) band, once that band exists. A class X node offering the same model prices inside the (T4, X) band, which the ordering rule places strictly above S.
- Governance-only registration slows the listing of models and blocks squatters. Both effects stand until a later CIP reopens registration.
- Pools are not parties to a session. Multi-node work opens one session per `(node, modelId)` and pays those nodes, never the pool ([ADR 0009](0009-opt-in-client-orchestration.md)).
- Ordered bands, protocol fee 0 and no slashing remain in force. A CIP that wants a serving gate again has to supersede this ADR and say so.

## Links

- [docs/evidence-register.md](../evidence-register.md) §6
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/node/model-registry-and-licenses.md](../node/model-registry-and-licenses.md)
- [docs/node/node-design.md](../node/node-design.md)
- [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0005](0005-hardware-classes-and-price-bands.md)
- [ADR 0006](0006-apache-2-0-and-dco.md)
- [ADR 0009](0009-opt-in-client-orchestration.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
