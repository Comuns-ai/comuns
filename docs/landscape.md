# Landscape — other networks and the gap this proposal fills

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** [evidence-register.md](evidence-register.md) §2, [project-charter.md](project-charter.md), [adr/0008-model-first-pools.md](adr/0008-model-first-pools.md), [adr/0009-opt-in-client-orchestration.md](adr/0009-opt-in-client-orchestration.md)

---

## 1. Summary

Comuns is a community proposal for open-source, decentralized LLM inference settled in ETH on Arbitrum One. Nothing runs yet: there is no network, no deployment and no seated maintainer. This file reads other compute and inference networks only from evidence register §2, which is a snapshot, and then states the design this proposal writes for itself.

The table is not a ranking. This proposal does not claim to be faster, cheaper or more proven than any project named below. A cell that compares designs states what this proposal does. It does not score the other project.

Gensyn and Nous Psyche are marked out of scope because §2 records them as training efforts. This proposal is inference only.

Model-first pools, the open-source client-side orchestrator and collective answers appear in this file only as this proposal's own design. They are not attributes of the projects in the table.

## 2. How to read this (confidence marks)

Every external fact in this file is copied from evidence register §2, and it keeps the mark §2 gives it. The register's marks mean:

- **[V]** verified at the source the register names.
- **[L]** likely. A likely mark is not a settled fact.
- **[U]** unsure. An unsure mark is not a settled fact.

A mark sits on the clause it belongs to. This file does not upgrade [L] or [U] to [V], and it does not drop a mark when it repeats a fact. Where §2 is silent, the cell says "not stated in evidence register §2". Silence is not filled from memory.

Sections §1–§8 of the evidence register, including §2, are a snapshot taken 2026-10-12. A later change to a named project is absent from this table until the register itself changes. Header dates and statements about this proposal are not §2 facts; they are this document's own.

Names, numbers and dates of third-party projects that do not appear in §2 are not used here. Mechanisms recorded only in later sections of the register are not imported to decorate a row.

## 3. Comparison table

Columns are the project, where it settles or how it coordinates, how operators are paid, what §2 says about prompt privacy, what §2 says about checking a result, and a note that states this proposal's own design. The note is not a score.

| Project | Settlement or coordination | How operators are paid | Prompt privacy | Result check | Note for this proposal |
| --- | --- | --- | --- | --- | --- |
| Bittensor | Own Substrate L1 (Rust); Python SDK; Yuma consensus [L] | Miners paid by emissions, not per request; ~18/41/41 split [L] | Chutes subnet 64 claims Intel TDX and NVIDIA TEEs [L]. No other prompt-privacy fact is in §2 | Not stated in evidence register §2 | This proposal pays ETH for a session the user opened, by chunked cumulative vouchers, and it issues no emission. It does not rank that payment against an emission split. |
| Akash | Cosmos SDK / Go; reverse auction ~5 min [V] | Per-block escrow in ACT [V] | Experimental TEE [V] | No protocol-level result verification [V] | This proposal does not run a reverse auction and does not escrow in ACT. A session deposit is ETH on Arbitrum One. |
| Ritual | EVM L1; private testnet since Dec 2024; no mainnet found [V] | Staked executors slashed [V]. A per-request payment asset is not stated in §2 | TEE LLM precompiles; secrets ECIES to a TEE key [V] | Staked executors slashed [V]. §2 does not say which output the slash measures | This proposal has no slashing in v1 and does not run the model as an L1 precompile. Nothing in this proposal runs yet. This document does not rank the two designs. |
| Gensyn | OP Stack rollup; mainnet Apr 2026 [L] | Not stated in evidence register §2 | Not stated in evidence register §2 | Verde + RepOps [V] | Out of scope. Training-first [L]. This proposal is inference only. |
| io.net | Central matching [L] | Solana token [L]. A per-request formula is not stated in §2 | No privacy mechanism found [L] | Hardware checks after a 2024 fake-GPU incident [L]. A protocol-level result check is not stated in §2 | This proposal has no central matcher and no token. It does not treat a hardware check as an unfakeable proof. |
| Hyperbolic | Centralized market [V] | Not stated in evidence register §2 | Not stated in evidence register §2 | PoSP/spML research [V] | This proposal's client reads offers. It does not adopt that research as a payment rule, and it does not rank the two checks. |
| Morpheus | On-chain bids; settles on Base; MIT; Go + TypeScript [V] | MOR stake [V]. A per-token ETH formula is not stated in §2 | Proxy-router carries prompts [V] | 'tee' tags attested [V]. Nothing further on result checking is in §2 | This proposal does not place a proxy on the path of the prompt. The client seals the prompt to the node the user chose. |
| ORA (opML) | Not stated in evidence register §2 | Not stated in evidence register §2 | Not stated in evidence register §2 | opML bisection to a one-step MIPS VM; 7B on a CPU-only PC [V]; window under 10 min [L] | This proposal does not use that bisection as its result check. Opt-in verifiable mode is re-execution by a second node the user chooses. This document does not rank the two checks. |
| Petals | Block-sharded swarm; MIT; last release Sep 2023 [V] | Not stated in evidence register §2 | README warns that data is processed by other people [V] | No result check is stated in §2. §2 records ~6 tok/s for Llama 2 70B [V], which is a throughput figure | Single-node execution is this proposal's default. This document records that throughput figure and does not rank this proposal's speed against it. |
| Exo | Own devices; Python + Rust; Apache-2.0 [V] | No payments [V] | Not stated in evidence register §2 | No verification [V] | This proposal specifies an ETH session payment. It does not claim that a payment makes a result more correct. |
| Prime Intellect | Protocol repo (Rust, Apache-2.0) archived Jan 2026 [V] | Not stated in evidence register §2 | Not stated in evidence register §2 | TOPLOC [V]. §2 names it and does not describe the method | This proposal does not depend on that archived repository and does not adopt the named check as its v1 result check. This document does not rank the checks. |
| Nous Psyche | Rust, Apache-2.0 [V] | Not stated in evidence register §2 | Not stated in evidence register §2 | Not stated in evidence register §2 | Out of scope. Training only [V]. This proposal is inference only. |

### Further networks, one clause each

These clauses are the whole of what §2 records for each name. They are not extra rows and they are not rankings.

- Phala is recorded as TDX and NVIDIA TEEs [L], with dstack in Rust and dcap-qvl, a Rust DCAP verifier under MIT [V].
- Oasis ROFL is recorded as TEE apps with a Rust SDK [L].
- Nillion is recorded as nilCC, a TEE [V].
- Lilypad is recorded as Go, Apache-2.0 and a solver [V], with deterministic modules marked [L].
- Fluence is recorded as an Arbitrum Orbit appchain using USDC [L].
- Nosana is recorded as a Solana marketplace [L], with verification marked [U].
- Golem is recorded as yagna in Rust with Polygon and Ethereum payments [V], with verification marked [U].

## 4. The gap

This section states this proposal's own design. It adds no third-party name, number or date.

**Per-session ETH payment, with chunked vouchers, rather than emissions.** The user deposits ETH for a session with one node and one model. The client signs a cumulative voucher for each chunk of output the client has acknowledged. Input and output token counts on a voucher are cumulative for the session, and a later voucher cannot lower what is owed. The contract credits an internal balance. No contract pushes ETH during settlement, bond release or refund. The only function that sends ETH is `withdraw()`, which pays the caller that caller's whole balance. A signed voucher is not reversed. v1 has no slashing and no token. The protocol fee is 0. The inference payment is the ETH owed for tokens. It is not the chain's transaction fee.

**Wallet-owned encrypted contexts.** Each wallet owns many versioned contexts, encrypted under a fresh key for each version. Sharing a context with a node re-wraps that version's key to the node's key. The ciphertext blob is what moves. Nodes do not exchange plaintext. The chain stores the content hash, not the text. The backup holds keys and key-wrap records. Ciphertext that existed only on a lost device is gone even with that backup.

**An open Rust node.** Inference runs off-chain in an open-source Rust node with pluggable backends. This proposal does not claim that the language alone makes inference faster.

**Ordered hardware-class bands.** Hardware classes are S, M, L and X. A class is decided by passing per-class benchmark bars on the public class benchmark, and it selects the price band. A class is not a tier, and it is not "the highest tier passed". For the same model, the next stronger class has a floor strictly above the previous class's ceiling, so stronger hardware charges more and weaker hardware charges less. Classes price work. They do not gate which model a node may offer. No wei value is adopted, so mainnet is not deployable until a CIP sets the bands. A self-benchmark is a signed claim, not an unfakeable proof.

**Community CIPs, with no token.** A change is a written CIP under rough consensus. There is no coin vote. No maintainer is seated, and seating happens only through a Final CIP. A CIP in Last Call cannot become Stagnant. A substantive edit during Last Call returns the CIP to Review.

**Arbitrum One settlement.** Settlement is Arbitrum One, with EVM contracts for nodes, models, context hashes and session escrow. The chain records offers and sessions. It does not run the model, and it does not store a pool list or a plan.

**Inference only.** Training, fine-tuning and federated learning are non-goals.

**The executing node sees plaintext.** In standard mode the chosen node can read the prompt, the granted context and the completion. The client says so before the user signs. This proposal does not claim confidentiality against that node. Attested mode checks a TEE quote and is not a physical-attack defense. Verifiable mode, when the user opts in, is re-execution by a second node the user chooses, under a demonstrated deterministic profile, and that verifier can read the prompt too.

**Model-first pools, with per-model offers and no class-to-tier gate.** A pool is the set of nodes with a current offer for one model id. The offer is `prices[modelId]` carrying input and output prices and a non-zero per-model benchmark hash. Clients enumerate pools off-chain. A pool is not a contract and not a payee. Any node may offer any registered model it can load. `maxTier` is informational. Model registration in v1 is governance-only, through a CIP. With nobody seated, there is no mainnet registration.

**An open-source client-side orchestrator, with opt-in collective answers.** Single-node execution is the default: one node, one session, one reader of the prompt in standard mode. Collective answers, decomposed plans and parallel planning are opt-in per request. The orchestrator is open-source logic in the client SDK. Before the user signs, the client shows a disclosure sheet that lists each node's role, what that node receives, its prices and its cap, and counts which nodes can read the prompt. An optional orchestrator node is never mandatory. It is paid as an ordinary session and holds no session signer in v1.

Collective answers are this proposal's quality mechanism: independent answers, a blind cross-check, and a synthesis that lists disagreements. They are not verification, not a privacy mode and not chain consensus, and they never change what a signed voucher pays.

Two further features, model sharding and cross-node speculation, are experimental spikes in this proposal. The reference client refuses both under mainnet parameters. They run only with testnet-only, non-normative prices. Shard holders hold no session and are not paid. For cross-node speculation, no WAN speed-up is promised. Both are opt-in and appear on the disclosure sheet. Single-node execution remains the default.

## 5. What this proposal refuses to copy

Each item is a pattern this proposal refuses. Where a named project illustrates the pattern, the only fact used is one that evidence register §2 states, with its mark. The refusal itself is this proposal's design.

1. **A proxy that sees prompts.** §2 records that the Morpheus proxy-router carries prompts [V]. This proposal seals the prompt to the node the user chose. No proxy sits on that path.
2. **A public swarm.** §2 records Petals as a block-sharded swarm whose README warns that data is processed by other people [V]. This proposal's default is one node chosen by the user.
3. **An emission token.** §2 records that Bittensor miners are paid by emissions, not per request [L]. This proposal has no token. An operator is paid from the ETH session the user opened.
4. **A central matcher.** §2 records that io.net uses central matching [L]. This proposal's client chooses a node by reading offers. A matcher is not a protocol role.
5. **A claim of unfakeable hardware.** §2 records that io.net added hardware checks after a 2024 fake-GPU incident [L]. This proposal's class benchmark and per-model self-benchmark are signed claims. They are not an unfakeable proof, and v1 does not slash because a benchmark looks wrong.
6. **Slashing on nondeterministic output.** §2 records that Ritual's staked executors are slashed [V]. §2 does not say that the slash is for two outputs that differ. This proposal's own rule is that v1 has no slashing. Differing outputs are not a payment event, and a signed voucher is not reversed.
7. **A public swarm that shards prompts across strangers by default.** The Petals fact in item 2 is the §2 record of a public swarm that processes other people's data [V]. This proposal does not shard a prompt across strangers by default. Its experimental sharding spike is opt-in, treats every shard holder as able to read the prompt, pays no shard holder, and is refused by the reference client under mainnet parameters.
8. **A mandatory orchestrator or proxy that sees every prompt.** The Morpheus proxy-router fact in item 1 is the §2 record of a component that carries prompts [V]. §2 does not describe a mandatory orchestrator, and this file does not invent one. This proposal keeps orchestration as open-source logic in the client. Single-node is the default. An orchestrator node is optional, is paid as an ordinary session, and holds no session signer.
9. **An emission or stake-weighted score presented as a collective answer.** §2 records Bittensor emissions [L] and a Morpheus MOR stake [V]. This proposal does not present an emission share or a stake weight as a collective answer. When the user opts in, a collective answer is a quality mechanism on ordinary ETH sessions, and disagreement does not change payment.

## 6. Risks

### R1 — The comparison table goes stale **[RISK] · High**

Evidence register §2 is a snapshot taken 2026-10-12. A project can change its settlement, its payment, its privacy claim or its result check after that date. A reader who treats this table as a live survey will be wrong, and a later document that copies a cell without re-checking the register will spread the stale cell. Mitigation: this file cites §2 and does not add third-party facts; a changed fact is a change to the register first, with its source and its mark.

### R2 — A likely mark is read as certain **[RISK] · Medium**

Several load-bearing cells are [L] or [U]: Bittensor's consensus, emission split and TEE claim; Gensyn's mainnet date and training-first label; io.net's matching, token, privacy note and hardware checks; the ORA window; Phala's TEEs; Oasis ROFL; Fluence; Nosana's marketplace; Lilypad's deterministic modules; and the verification notes for Nosana and Golem, which are [U]. A summary that drops the mark turns a likely or unsure statement into a settled one. Mitigation: every borrowed fact in this file keeps the mark §2 gave it, and section 2 says a likely mark is not certainty.

### R3 — A design note is read as a ranking **[RISK] · Medium**

The last column states this proposal's design beside another project's §2 facts. A reader can turn "this proposal has no token" or "this proposal does not slash" into a claim of a lower price or a stronger proof. This proposal does not make that claim. Nothing here runs yet, so there is no measurement to rank. Mitigation: section 1 states the limit; notes that mention another project's figure say they do not rank this proposal against it.

## 7. Open questions

These are interop CIP candidates. None is a decision. A CIP would have to be filed, reviewed and taken through Last Call. Each question uses only names and facts that §2 already records, plus this proposal's own design.

1. Should a later CIP define a read-only way for a client to notice an operator who also sells capacity through a coordination method §2 names — Akash's reverse auction [V], io.net's central matching [L], Nosana's Solana marketplace [L], Hyperbolic's centralized market [V], or Golem's Polygon and Ethereum payments [V] — while this proposal keeps ETH session escrow and does not adopt that network's token, matcher or escrow?
2. Should a later CIP name which TEE quote a client may check in attested mode, limited to mechanisms §2 already records (Ritual's TEE precompiles and ECIES-to-TEE-key [V], Phala's TDX and NVIDIA TEEs [L], Nillion's nilCC [V], Oasis ROFL [L], Morpheus 'tee' tags [V], Akash's experimental TEE [V], Bittensor Chutes subnet 64's claimed Intel TDX and NVIDIA TEEs [L])? Attested mode in this proposal remains not a physical-attack defense.
3. Should a later CIP study ORA's opML bisection to a one-step MIPS VM [V], or the TOPLOC name §2 records for Prime Intellect [V], as an optional result check beside this proposal's opt-in re-execution? §2 does not describe the TOPLOC method, and this file does not import a description. The CIP would have to bring its own evidence, and it would not rank one check as a stronger proof.
4. Should a later CIP define a boundary with a block-sharded swarm of the kind §2 records for Petals [V], given that this proposal's default is one node and that a public swarm which processes other people's data is a pattern this proposal refuses as the default?
5. Fluence is recorded as an Arbitrum Orbit appchain using USDC [L]. Should a later CIP study settlement on an Orbit chain, or in a token other than ETH, knowing that v1 settles ETH on Arbitrum One and has no token? This document does not propose that change.
6. Training interop with Gensyn (training-first [L]) or Nous Psyche (training only [V]) is out of scope while this proposal remains inference only. A CIP that widened scope to training would have to say so as a change of scope. This document does not propose that CIP.
