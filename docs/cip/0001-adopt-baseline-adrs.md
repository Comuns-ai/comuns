# CIP 0001: Adopt the baseline ADRs

Status: Draft
Type: process
Created: 2026-10-12
Requires: None

This CIP is Draft. It is not in Last Call and it is not Final. It proposes that the community adopt the nine baseline ADRs. It does not mark the ADRs accepted. Each record stays proposed for as long as this file stays short of Final under GOVERNANCE.md.

## Abstract

If this CIP becomes Final, Comuns treats ADRs 0001 through 0009 as the adopted baseline for settlement, the node, privacy, sessions, price bands, licensing, the absence of a protocol token, model-first pools, and opt-in orchestration. A later change that contradicts one of them needs a superseding ADR. Until that happens, the nine files remain proposed, and this Draft does not adopt them. No parameter, contract or deployment changes in this text.

## Motivation

The design documents already take these decisions. They are spread across the contracts, the node, the privacy write-up, the economics note, the governance file and the orchestration notes. A reviewer cannot object to a scattered assumption as one proposal. A CIP is the written record Comuns uses for a decision. This one asks the community to adopt the nine records together, on the future public repository, with objections written against this file.

The proposal does not rely on a token, a coin vote or an ARB balance. ARB balances are not this project's votes. Anyone may object, including a class S operator. Nobody is seated, so nobody can merge this file on private authority.

## Specification

This CIP changes no price band, no deadline, no bond and no protocol fee. The protocol fee is 0. No timelock is stated, because no parameter changes. Nothing in this file sets a wei value.

The proposal is that, if this CIP becomes Final after the lifecycle in GOVERNANCE.md and docs/cip/README.md, the following nine records are the baseline. This Draft does not perform that step. Reviewers who object do so in writing on the future public repository, naming a specific defect and the change they want. Silence is not approval.

Moving this file from Draft follows the CIP lifecycle. A CIP in Last Call cannot become Stagnant. A substantive edit during Last Call returns the CIP to Review and starts a new, full 14-day Last Call. Seating and removal of maintainers happen only through a Final CIP. A status line that says Final without a completed Last Call is void. This file's status is Draft.

Each summary below is one sentence. The ADR text wins if a summary is read more loosely than the ADR.

1. [ADR 0001](../adr/0001-settle-on-arbitrum-one-evm-not-stylus.md) settles v1 on Arbitrum One with EVM contracts, leaves Stylus unused while new activations remain paused, and does not treat ARB balances as this project's votes.
2. [ADR 0002](../adr/0002-off-chain-rust-inference.md) runs inference off-chain in a Rust node, with llama.cpp through Rust bindings as the first adapter and mistral.rs as the second, selected per model by a published benchmark.
3. [ADR 0003](../adr/0003-hpke-and-the-executor-plaintext-limit.md) encrypts both directions with RFC 9180 HPKE in base mode, and in standard mode the executing node still reads the prompt in plaintext.
4. [ADR 0004](../adr/0004-sessions-vouchers-and-no-slashing.md) pays a session from an ETH deposit and cumulative `sessionSigner` vouchers stepped by `CHUNK_TOKENS`, credits balances for the holder to withdraw, and does not slash in v1.
5. [ADR 0005](../adr/0005-hardware-classes-and-price-bands.md) orders bands over S, M, L and X so that `floor(class c+1) > ceiling(class c)` for input and for output, leaves asks free inside the band, prices in wei per 1,000,000 tokens, keeps the protocol fee at 0, and sets no wei value.
6. [ADR 0006](../adr/0006-apache-2-0-and-dco.md) licenses code and documentation Apache-2.0, uses the DCO `Signed-off-by` line, takes no CLA, and leaves each model's weights under that model's own license.
7. [ADR 0007](../adr/0007-no-protocol-token-in-v1.md) does not issue a protocol token in v1, pays in ETH, governs by CIP, emits nothing, holds no coin vote, and does not use ARB balances as this project's votes.
8. [ADR 0008](../adr/0008-model-first-pools.md) lets a node offer any registered model it can load, forming an off-chain pool per `modelId`, and withdraws the class-to-tier serving gate without withdrawing ordered bands, protocol fee 0 or the no-slashing rule.
9. [ADR 0009](../adr/0009-opt-in-client-orchestration.md) keeps single-node execution as the default, allows `collective_answer`, `parallel_planning` and `task_decomposition` only as opt-in features on a disclosure sheet, treats `model_sharding` and `cross_node_speculation` as experimental Phase 3 spikes, states that a collective answer is not verification, and does not delegate `sessionSigner` in v1.

Adopting the nine records does not make multi-node execution the default and does not restore a class-to-tier serving gate. The plaintext limit, the no-slashing rule, the band ordering, the Apache-2.0 license and the no-token rule stay as those ADRs state them.

Later records. [ADR 0010](../adr/0010-anonymous-by-default.md), [ADR 0011](../adr/0011-anonymous-credits.md), [ADR 0012](../adr/0012-contexts-without-a-wallet-link.md) and [CIP-0002](0002-anonymous-credits-relays-and-ownerless-contexts.md) are separate proposals. This CIP does not adopt them. If this CIP and CIP-0002 both become Final, ADRs 0010–0012 supersede the conflicting sentences on identity, contexts, local execution and the fifteen-function list in the nine records above, rather than this file being rewritten.

## Rationale

One process CIP is the smallest proposal that lets a reviewer accept or object to the baseline as a set. Splitting adoption across nine CIPs would let the set pass in a combination the documents do not support, for example bands without the model-first pool rule, or orchestration without the plaintext limit.

The records were written to match decisions already in the design documents, including the review decisions those documents carry: pull payments through `withdraw()`, the cumulative voucher, the executor's plaintext in standard mode, per-version context keys, and verifiable mode as re-execution by a user-chosen second node. This CIP adds no mechanism of its own.

Alternatives considered:

- Edit the design documents in place and skip a CIP. Rejected. GOVERNANCE.md says a decision is a CIP, and an ADR stays proposed until this CIP has finished the lifecycle.
- Adopt only ADRs 0001–0007 and leave pools and orchestration out. Rejected. The contracts, node, privacy, orchestration, collective-answer and distributed-execution documents already record model-first pools and opt-in orchestration. Leaving them out of the baseline would hide decisions the other documents rely on. Including them does not make multi-node execution the default and does not restore a class-to-tier serving gate.
- Decide by coin vote or by ARB balance. Rejected. There is no protocol token and no coin vote (evidence register §8, [V], for the EIP comparison). ARB balances are not this project's votes.

## Backwards compatibility

Nothing is deployed. No contract, client or node exists to migrate. This CIP does not contradict the nine ADRs. It proposes to adopt them. ADR 0008 withdraws an earlier assumption that a hardware class may serve only up to a fixed tier. Adopting ADR 0008 adopts that withdrawal. This CIP does not restore that gate, and it does not make multi-node execution the default.

If a later CIP contradicts an ADR after this CIP has become Final, that later CIP names the superseding ADR. This sentence describes the rule in GOVERNANCE.md. It does not say that this CIP, or any ADR, has finished the lifecycle.

## Security considerations

Adopting these records does not seize escrow and does not expose prompts. An emergency action cannot seize escrow or expose prompts. No code exists, so no private vulnerability report is required for this CIP. This file contains no prompt, no key and no seed phrase.

The plaintext limit stays: in standard mode the executing node reads the prompt. Extra readers exist only when the user opts in and the disclosure sheet lists them. There is no slashing in v1. A signed voucher is not reversed. `sessionSigner` is not delegated to an orchestrator node in v1. Experimental sharding treats every shard holder as able to read the prompt, and the reference client refuses sharding and cross-node speculative decoding under mainnet parameters.

Security reporting, once a channel exists, is described in [SECURITY.md](../../SECURITY.md). The threat catalogue is [docs/security/threat-model.md](../security/threat-model.md). Neither file is amended here.

## Economic considerations

The protocol fee is 0, and no treasury exists. This CIP does not change that fact. There is no protocol token and no coin vote. ARB balances are not this project's votes. This CIP does not ask for funds, does not create a bounty and does not record a grant. Bands stay unset. Forty directional entries still have to be set by a later parameter CIP before a paid mainnet session can open. This file sets no wei value.

## Reference implementation

None.

## Change log

None.

## Copyright

This CIP assigns no copyright and uses no CLA.

Copyright 2026 Comuns contributors

Licensed under the Apache License, Version 2.0 (see LICENSE)
