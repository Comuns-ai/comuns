# ADR index

The fifteen architecture decision records in this directory are proposed. None is adopted. Adoption of ADR 0001 to ADR 0009 is the subject of [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md). That CIP is Draft. It is not in Last Call and it is not Final. [docs/cip/0002-anonymous-credits-relays-and-ownerless-contexts.md](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) (Draft) proposes adopting ADR 0010 to ADR 0012 and amending the closed function list of the contracts document. [CIP-0005](../cip/0005-phase-one-implementation.md) (Draft) proposes adopting ADRs 0013–0015. This index does not mark any ADR accepted. With nobody seated, nobody has authority to mark one adopted. After a CIP is Final, a change that contradicts an ADR needs a superseding ADR. A silent edit does not overturn an adopted ADR.

The system shape these records assume is described in [docs/architecture/system-architecture.md](../architecture/system-architecture.md).

## How to add an ADR

Take the next free four-digit number. The next number after 0015 is 0016. Name the file `docs/adr/NNNN-kebab-case-title.md`: lowercase words separated by hyphens. Start the file with `# ADR NNNN: Title`. Set `**Status:** proposed`. Set `**Date:**` to the day the file is opened, as YYYY-MM-DD. Keep the Deciders line used by the records below until a CIP adopts the record. Include the sections Context, Decision, Alternatives considered (at least three, each with the reason it was rejected or deferred), Consequences and Links. Cite an external fact as the evidence-register section that contains it. A new ADR does not adopt itself, and adding it to this index does not adopt it.

## The records

- [ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md) — Settle on Arbitrum One with EVM contracts, and leave Stylus unused while new activations are paused.
- [ADR 0002](0002-off-chain-rust-inference.md) — Run inference off-chain in a Rust node, with llama.cpp through Rust bindings as the first adapter and mistral.rs as the second, chosen per model by benchmark.
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) — Encrypt both directions with RFC 9180 HPKE, and state that in standard mode the executing node still reads plaintext. Proposed to be superseded in part by ADR 0010 and ADR 0012; the cipher suite, AAD list, envelope signature, commitKey and keyring rules carry forward.
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md) — Settle a session with a deposit and cumulative `sessionSigner` vouchers stepped by `CHUNK_TOKENS`, and do not slash in v1.
- [ADR 0005](0005-hardware-classes-and-price-bands.md) — Order price bands so each stronger hardware class charges more for the same model, with asks free inside the band and no wei value set here.
- [ADR 0006](0006-apache-2-0-and-dco.md) — License code and documentation Apache-2.0, certify contributions with the DCO, and leave model-weight licenses with the weights.
- [ADR 0007](0007-no-protocol-token-in-v1.md) — Do not issue a protocol token in v1; pay in ETH and decide by CIP.
- [ADR 0008](0008-model-first-pools.md) — Let any node offer any registered model it can load, as an off-chain pool per model, and withdraw the class-tier serving gate without withdrawing ordered bands.
- [ADR 0009](0009-opt-in-client-orchestration.md) — Keep single-node execution as the default, and allow collective answers, planning and experimental parallelism only as disclosed opt-in features.
- [ADR 0010](0010-anonymous-by-default.md) — Make anonymity the default property of every session: Oblivious HTTP through registered relays, a fresh `sessionSigner` per session, no wallet shown to a node, standard mode as the default tier whose node can read content but should not learn who asked, attested mode as the opt-in content-private tier, and no local execution. Proposed, not adopted.
- [ADR 0011](0011-anonymous-credits.md) — Fund sessions with anonymous credits: fixed-denomination notes in Semaphore v4 groups inside `SessionEscrow`, spent by nullifier into credit sessions with fixed-denomination change, a public ragequit and no dedicated anonymous withdrawal entry point; amends the closed function list to 23 names. Proposed, not adopted.
- [ADR 0012](0012-contexts-without-a-wallet-link.md) — Identify a context by a random per-context signing key instead of a wallet, sign head records and grants with that key, and make the registry an optional anchor that any address may write. Proposed, not adopted.
- [ADR 0013](0013-repositories-toolchains-ci-and-releases.md) — Repository layout, toolchains, CI, DCO, style and testnet release gates. Proposed, not adopted; adoption is proposed in CIP-0005
- [ADR 0014](0014-relay-authentication-to-gateways.md) — Relay authentication per connection without a contract change. Proposed, not adopted; adoption is proposed in CIP-0005
- [ADR 0015](0015-node-key-possession.md) — Client key-possession probe before spending, without a contract change. Proposed, not adopted; adoption is proposed in CIP-0005

[docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md) proposes that the community adopt the first nine records. It does not mark them accepted. [docs/cip/0002-anonymous-credits-relays-and-ownerless-contexts.md](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) (Draft) proposes adopting ADR 0010, ADR 0011 and ADR 0012 and amending the function list; it is Draft and adopts nothing.

[docs/architecture/system-architecture.md](../architecture/system-architecture.md) is the architecture overview that sits beside this set.
