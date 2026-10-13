# ADR index

The nine architecture decision records in this directory are proposed. None is adopted. Adoption is the subject of [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md). That CIP is Draft. It is not in Last Call and it is not Final. This index does not mark any ADR accepted. With nobody seated, nobody has authority to mark one adopted. After that CIP is Final, a change that contradicts an ADR needs a superseding ADR. A silent edit does not overturn an adopted ADR.

The system shape these records assume is described in [docs/architecture/system-architecture.md](../architecture/system-architecture.md).

## How to add an ADR

Take the next free four-digit number. The next number after 0009 is 0010. Name the file `docs/adr/NNNN-kebab-case-title.md`: lowercase words separated by hyphens. Start the file with `# ADR NNNN: Title`. Set `**Status:** proposed`. Set `**Date:**` to the day the file is opened, as YYYY-MM-DD. Keep the Deciders line used by the records below until a CIP adopts the record. Include the sections Context, Decision, Alternatives considered (at least three, each with the reason it was rejected or deferred), Consequences and Links. Cite an external fact as the evidence-register section that contains it. A new ADR does not adopt itself, and adding it to this index does not adopt it.

## The records

- [ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md) — Settle on Arbitrum One with EVM contracts, and leave Stylus unused while new activations are paused.
- [ADR 0002](0002-off-chain-rust-inference.md) — Run inference off-chain in a Rust node, with llama.cpp through Rust bindings as the first adapter and mistral.rs as the second, chosen per model by benchmark.
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) — Encrypt both directions with RFC 9180 HPKE, and state that in standard mode the executing node still reads plaintext.
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md) — Settle a session with a deposit and cumulative `sessionSigner` vouchers stepped by `CHUNK_TOKENS`, and do not slash in v1.
- [ADR 0005](0005-hardware-classes-and-price-bands.md) — Order price bands so each stronger hardware class charges more for the same model, with asks free inside the band and no wei value set here.
- [ADR 0006](0006-apache-2-0-and-dco.md) — License code and documentation Apache-2.0, certify contributions with the DCO, and leave model-weight licenses with the weights.
- [ADR 0007](0007-no-protocol-token-in-v1.md) — Do not issue a protocol token in v1; pay in ETH and decide by CIP.
- [ADR 0008](0008-model-first-pools.md) — Let any node offer any registered model it can load, as an off-chain pool per model, and withdraw the class-tier serving gate without withdrawing ordered bands.
- [ADR 0009](0009-opt-in-client-orchestration.md) — Keep single-node execution as the default, and allow collective answers, planning and experimental parallelism only as disclosed opt-in features.

[docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md) proposes that the community adopt these nine records. It does not mark them accepted.

[docs/architecture/system-architecture.md](../architecture/system-architecture.md) is the architecture overview that sits beside this set.
