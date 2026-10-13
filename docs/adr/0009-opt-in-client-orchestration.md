# ADR 0009: Opt-in client orchestration, collective answers and experimental parallelism

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

Two requests sit beside single-node inference. One asks for a consensus mechanism over several models. The other asks for parallel execution, with an orchestrator that assesses task size and plans with parallelization in mind. The evidence is mixed, and it is task-dependent.

Collective answers help on some tasks and can lower quality. Debate with three agents raised arithmetic from 67.0 to 81.8 and MMLU from 63.9 to 71.1, and the authors note the cost (evidence register §11, [V]). One strong model sampled many times (Self-MoA) beat a mixture of models by 6.6% on one benchmark (evidence register §11, [V]). With homogeneous small agents, debate cost 2.1–3.4× the tokens of self-correction for equal or lower accuracy, and correct answers were discarded by plurality vote (evidence register §11, [V]).

DAG planning has reported up to 3.7× lower latency than a sequential tool loop, with the planner and the join left on the critical path, the slowest task setting the pace, and planner overhead making one benchmark slower (evidence register §12, [V]). Skeleton-style expansion is a poor fit for math, coding, Fermi estimates and writing (evidence register §12, [V]). Routing by difficulty is motivation only: the cited routers are trained, and v1 has no trained router (evidence register §13, [V]).

For splitting one model, the register does not support a promise of wide-area speed. At WAN round-trip times, one preprint says the cloud round trip remains too large for pipelined distributed speculative decoding to beat co-located speculative decoding. The quote is what the preprint says (evidence register §9, [V]). The result is not independently replicated (evidence register §9, [U]). Documents say "no WAN speed-up is promised". Larger draft models raise the acceptance rate α but cost more (higher c) (evidence register §9, [V]). Sharding is slow over the internet in the cited settings, and every shard holder can invert the prompt: 88.4% token accuracy on a 65B model, 92% exact recovery of 32-token inputs from embeddings, and 86.88 token F1 on a 4,112-token prompt from a middle layer (evidence register §10, [V]). The llama.cpp RPC facts — proof of concept, fragile and insecure, never on an open network — are evidence register §10, [V].

Default execution has to stay one node. Extra readers and extra sessions are a choice the user sees before signing.

## Decision

**(1) Single-node is the default.** One node, one session and one model. The per-request client-side `executionFeatures` set is never stored on-chain. Its names are `collective_answer`, `parallel_planning`, `task_decomposition`, `model_sharding` and `cross_node_speculation`. The empty set is single-node. Verifiable mode is a privacy mode of a session, not a member of this set. It adds one user-chosen verifier when the user opts in ([ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)).

**(2) The orchestrator is open-source code in the client SDK.** It assesses locally first and never contacts a node on its own. It may ask a planner node only after a disclosure sheet that says that node will see the full prompt. It may run parallel planning. It then shows the user a DAG of waves with disjoint outputs, review by a different model family, and a final check. The user confirms the plan. Planner output is data. It never authorizes a recipient, a payment, a tool or an external action. `planId`, `taskId` and `role` are bound into the job AAD. `wave` is advisory metadata, is not bound, and nodes must not rely on it. The wire role tokens are exactly: `executor`, `planner`, `answerer`, `reviewer`, `synthesizer`, `merge`, `orchestrator`, `shard holder`, `draft`, `target`, `verifier`.

**(3) A collective answer is a quality mechanism.** k ≥ 2 nodes answer independently. Reviewers cross-check blind, with positions swapped, under stable anonymous IDs `A1…Ak` assigned once per request. A synthesis lists disagreements. The client shows a session multiplier computed from the confirmed prices. It is not a protocol constant. Collective answers are not verification, not mode 2, not slashing and never a payment consequence. Differing answers are not evidence of fraud. A discarded answer does not reverse a voucher. Parallel planning reuses the same mechanism, adds an objection round that is not blind, and never auto-executes a judge's rank.

When one strong model is in a pool, the client suggests self-consistency or Self-MoA first. The user may still opt into `collective_answer`. Self-consistency is k samples of one strong model and a majority vote over a short extracted answer, only for a number, a choice or a label. Self-MoA is k samples of one strong model combined by a synthesizer, for free text. A plurality vote is never applied to free text. Disagreement between the two position-swapped review passes is expected and does not mark a synthesis incomplete. An empty splits list is valid. A synthesis is incomplete only when required fields are missing or malformed.

**(4) Every non-empty feature set is opt-in per request.** The disclosure sheet lists role, what each node receives, mode, prices, cap and reader counts before the user signs. It is shown again when the plan changes. Any change of node, model, data scope, price, cap or reader set creates a new sheet version that must be confirmed before any `openSession` or job under it. The order is: pick models, see the sheet, confirm, sign. A new session is a new sheet version, because it is a new deposit and cap. The request fails closed. There is no silent downgrade and no fallback that was not on the confirmed sheet. If verifiable mode is wanted for an orchestrated result, that verifier is on the sheet before signing. Adding one later requires a new sheet version. The sheet's `readersOfFullPrompt` follows the floor in [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md), which is a minimum, never a ceiling. `counts.fullPrompt` counts nodes literally sent the full prompt. `readersOfFullPrompt` is at least that number. The sheet JSON is normative. Tables are generated from it and must match it.

**(5) Payment does not grow a new contract.** One `SessionEscrow` session per distinct `(node, modelId)`. A node that serves a different model in another role gets a separate session. Jobs that share a session run one at a time (`maxConcurrentJobsPerSession = 1`). A wave runs concurrently only across different sessions. A second session for the same pair, when two tasks must run in parallel, is on the sheet. Pools are not payees. No payment moves between nodes. No new v1 contract and no new function. N sessions need N happy-path pairs (`openSession` and `closeWithVoucher`), plus L2 gas, at protocol fee 0. The combined cap is the sum of the session caps and is shown before the user signs, with the L2 gas estimate separate. User-facing copy shows ETH as a decimal with the unit.

**(6) Optional orchestrator nodes are ordinary sessions.** They see the prompt only when the user delegates planning, merging or synthesis. They hold no `sessionSigner` in v1, take no cut and are never mandatory. `sessionSigner` is not delegated in v1. No protocol component depends on one. A client that runs the SDK needs no orchestrator node. Delegation of `sessionSigner` to an orchestrator node is deferred to a later CIP.

**(7) `model_sharding` and `cross_node_speculation` are experimental Phase 3 spikes.** They may end in a published negative result. That outcome is acceptable and is published. A negative result for either spike does not withdraw collective answers or task decomposition.

Sharding treats every shard holder as able to read the prompt (evidence register §10, [V]). The reference client never uses llama.cpp RPC on an open network (evidence register §10, [V]). Shard holders, including the first and the last, hold no session and are never paid, in v1 or in the spike. The reference client never opens a session or signs a voucher for a shard holder. In the spike the client mediates every stage boundary: it holds the embeddings, sends each holder exactly its inputs, receives activations and forwards them, feeds sampled tokens back, and produces output itself from the last stage's logits. Holders authenticate with mutual TLS bound to their registered operator keys. Activations go only to holders on the sheet. A lost holder restarts the generation from the beginning on a new chain from the sheet. Replaying cached stage inputs to a sheet-listed replacement is the spike's measured option. It has a latency and privacy cost. The spike promises neither a time nor a success rate. No WAN speed-up is promised. Under mainnet parameters the reference client refuses `model_sharding`, because there is no activation meter. The spike runs only with testnet-only, non-normative prices.

Cross-node speculative decoding is one job per session on each of the draft node and the target node. Rounds are frames inside that job. The prompt is input-billed once per job, never per round. Both nodes are full-prompt readers. Drafts carry the draft model's per-token probability distributions as sealed metadata, which are not billable output tokens, or the spike is limited to greedy decoding at temperature 0, where tokens suffice. Tokens alone cannot preserve the target distribution. The greedy exact-match test is valid only against the spike's own measured determinism (evidence register §5, [V]: 80 unique outputs in 1,000 temperature-0 runs without batch-invariant kernels). The target's per-round work is bounded by a named `MAX_DRAFT_TOKENS` parameter, value unset. The target session is billed for drafted tokens it scores. The draft session is billed for drafted tokens it delivers, including drafts the target rejects. The feature is incompatible with verifiable mode: the deterministic profile needs byte-identical output, mistral.rs states that token-for-token equivalence is not guaranteed (evidence register §9, [V]), and TOPLOC cannot detect speculative decoding (evidence register §5, [V]). No WAN speed-up is promised (evidence register §9, [V] for the preprint's words, [U] because the result is not independently replicated). Under mainnet parameters the reference client refuses `cross_node_speculation`. Testnet-only prices are non-normative. The spike must not promise a WAN speed-up.

`task_decomposition` is the opt-in DAG of waves above. It is not experimental in the sense the two spikes are, and it is still off unless the user opts in. Easy and hard sub-tasks may use different confirmed models. That split is the user's choice. It is not a trained router.

## Alternatives considered

### A protocol-mandatory orchestrator or matcher

Rejected. It would be a new trusted party that sees every prompt, and a component every client would depend on. Assessment stays on the user's device until the user opts in. Node choice stays off-chain, from the model pool ([ADR 0008](0008-model-first-pools.md)).

### An on-chain plan contract in v1

Rejected. A plan registry would cost gas to store work the chain does not run, and the chain never routes inference. Plans are client-side JSON. The fifteen settlement functions stay closed ([ADR 0004](0004-sessions-vouchers-and-no-slashing.md)).

### Consensus as same-model integrity replication

Deferred. Re-executing one model under a demonstrated deterministic profile is verifiable mode's domain ([ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md), inference-verification document). It needs a profile v1 has not demonstrated. A collective answer compares models that may legitimately disagree, so it cannot be that check. Calling it consensus would blur a quality aid with chain consensus and with verification.

### Plan-only consensus

Deferred. Ranking plans and executing the winner without the user would auto-execute a judge's order. Position bias is enough to refuse that (evidence register §11, [V]). The user confirms a plan, or stops. A later CIP can propose a narrower aid. v1 does not execute a rank by itself.

### Multi-party escrow sessions

Deferred. One session already binds one user, one node and one model. A multi-party session would add contract surface for no v1 benefit: the client can open N ordinary sessions. Pools stay off the payee list.

### Making collective the default

Rejected. It would send the prompt to k readers and charge a multiple of the tokens without consent. The cost evidence is 2.1–3.4× tokens in one study, with quality that can fall (evidence register §11, [V]). The default remains single-node. The user opts in per request.

### sessionSigner delegation to orchestrator nodes

Deferred to a CIP. In v1 the `sessionSigner` stays on the user's client. An orchestrator node holds no `sessionSigner`, custodies no session and takes no cut. Delegation would let another party sign vouchers up to the cap.

### Silent downgrade

Rejected. Dropping a feature, swapping a node, narrowing a reader set or skipping a confirmation when the pool is short would bill the user for a different request from the one they signed. The client fails closed and says why.

## Consequences

- More parties can read a prompt only when the user opts in and the sheet lists them. The floor in [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) is the minimum count.
- Cost multipliers must be shown before signing, as a sum of sessions and as a multiplier against one session for a collective answer. The figure is computed for that request. It is not a constant of the protocol.
- N sessions cost N deposits and N happy-path transaction pairs. Fan-out is more expensive on L2 gas than single-node, by construction.
- Collective answers can make an answer worse. The client shows splits and the raw answers. It does not present a synthesis as verified.
- Experimental sharding and cross-node speculative decoding are labelled experimental. The reference client refuses both under mainnet parameters. Neither is paid as an activation stream. No WAN speed-up is promised.
- [docs/protocol/orchestration.md](../protocol/orchestration.md), [docs/protocol/collective-answers.md](../protocol/collective-answers.md) and [docs/node/distributed-execution.md](../node/distributed-execution.md) own the details. This ADR does not replace them.
- A CIP that wants `sessionSigner` delegation, an activation meter, or a default other than single-node has to say which sentence of this record it supersedes.

## Links

- [docs/evidence-register.md](../evidence-register.md) §5, §9, §10, §11, §12, §13
- [docs/protocol/orchestration.md](../protocol/orchestration.md)
- [docs/protocol/collective-answers.md](../protocol/collective-answers.md)
- [docs/node/distributed-execution.md](../node/distributed-execution.md)
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md)
- [docs/security/inference-verification.md](../security/inference-verification.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md)
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0008](0008-model-first-pools.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
