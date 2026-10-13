# Collective answers — several nodes answer, cross-check blind, one synthesis

Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12
**Reference:** docs/evidence-register.md, docs/protocol/orchestration.md, docs/protocol/off-chain-api.md, docs/protocol/contracts-and-settlement.md, docs/security/privacy-and-contexts.md, docs/security/inference-verification.md, docs/economics/cost-and-pricing.md, docs/adr/0009-opt-in-client-orchestration.md

---

## 1. Summary

Comuns is a community proposal for open-source decentralized LLM inference settled on Arbitrum One; nothing described here runs yet. This document specifies `collective_answer`, the proposal's answer to the request for a "consensus mechanism". It is named *collective answer* to avoid confusion with chain consensus, because it is a different thing: **a quality mechanism**, in which k ≥ 2 nodes answer the same prompt independently, reviewers cross-check the answers blind, and one synthesizer merges them into one answer that carries its disagreements openly. It is **not verification**, not same-model integrity replication (that is verifiable mode, docs/security/inference-verification.md), not plan-only consensus, and **never a payment consequence**: every node is paid for the tokens it delivered, whether or not the synthesis kept its text.

The evidence says the mechanism helps on some tasks and hurts on others. Three agents over two rounds of debate raised arithmetic from 67.0 to 81.8 and MMLU from 63.9 to 71.1 (evidence register §11 [V]); a mixture of six open-weight models reached a higher AlpacaEval 2.0 win rate than the strongest proprietary single model then tested (§11 [V]). But one strong model sampled many times beats a mixture of models by 6.6 % (Self-MoA, §11 [V]), debate does not reliably beat self-consistency (§11 [V]), agents flip correct answers to incorrect ones over rounds (§11 [V]), and with ten homogeneous small agents up to 70.0 % of correct answers were destabilized at 2.1–3.4× the token cost (§11 [V]). The design therefore defaults to showing disagreement rather than resolving it, defaults to different models for diversity while telling the user that one strong model sampled k times is often better and cheaper, and lists plainly when not to use the feature at all.

Every run is opt-in per request, starts only after the user has seen the disclosure sheet, signed, and funded a cap that covers every session, and discloses that at least k nodes read the full prompt.

## 2. Scope

In scope: the execution feature `collective_answer` — its roles, its three rounds, the blind cross-check, the synthesis output and its splits list, how the client surfaces disagreement, cost and latency, when not to use it, the reuse of the same mechanism for `parallel_planning` and for reviewing sub-task outputs, payment through ordinary sessions, privacy, what the feature is not, risks and open questions.

Out of scope and owned elsewhere: the assessment step that decides whether to suggest the feature and the plan schema (docs/protocol/orchestration.md); the job envelope, receipts and frames (docs/protocol/off-chain-api.md); sessions, vouchers and settlement (docs/protocol/contracts-and-settlement.md); the disclosure sheet, HPKE and the reader list (docs/security/privacy-and-contexts.md); verification of what a node ran (docs/security/inference-verification.md); prices (docs/economics/cost-and-pricing.md). All feature and role names here are normative and shared with docs/protocol/orchestration.md and docs/security/privacy-and-contexts.md: `collective_answer`, `parallel_planning`, and the roles `answerer`, `reviewer`, `synthesizer`.

Evidence marks follow the register: **[V]** verified, **[L]** likely, **[U]** unsure; a claim not in the register is labeled UNVERIFIED. All design statements are PROPOSED.

## 3. Why several answers

**What the evidence supports.**

- Multiagent debate, 3 agents × 2 rounds of a 2023 proprietary chat model: arithmetic 67.0 → 81.8, GSM8K 77.0 → 85.0 (majority vote alone: 81.0), MMLU 63.9 → 71.1; the authors note it is more expensive (evidence register §11 [V]).
- Mixture-of-Agents, 3 layers × 6 open-weight models with an open-weight aggregator: AlpacaEval 2.0 length-controlled win rate 65.1 % using only open-weight models, against 57.5 % for the strongest proprietary single model then tested; stated limitation: high time-to-first-token (§11 [V]).
- Self-consistency — sample many reasoning paths, take the majority answer: GSM8K +17.9 % over chain-of-thought (§11 [V]).
- LLM-as-a-judge: the strongest judge tested agreed with humans on 85 % of non-tie votes versus 81 % human–human agreement, so a model reviewer can be as consistent with people as people are with each other (§11 [V]).
- Fortytwo ranks peer answers pairwise and aggregates with reputation-weighted Bradley-Terry scores; reported GPQA Diamond 85.90 % versus 68.69 % for majority vote (§13 [V]); roughly 10–15 s added latency per the company [L]; company executives said node operators could potentially see prompts [L].

**What the same evidence says against it.**

- Self-MoA — one strong model sampled many times — beats a mixed mixture of models by 6.6 % on AlpacaEval 2.0, and mixing models often lowers average quality (§11 [V]). Diversity of models is not free quality.
- Debate does not reliably outperform self-consistency and is hyperparameter-sensitive (§11 [V]).
- Accuracy can fall over rounds: agents flip correct → incorrect under sycophancy and conformity (§11 [V]).
- With 10 homogeneous 7–8B agents, up to 70.0 % of previously correct answers were destabilized by peers; correct answers were present but discarded by plurality vote, with an oracle gap of up to 32.3 percentage points; debate cost 2.1–3.4× the tokens of self-correction for equal or lower accuracy (§11 [V]).
- Judges have position bias — the strongest judge was consistent on only 65.0 % of swapped orders, weaker judges 23.8 %–46.2 % — verbosity bias, and possible self-preference; the cited mitigations are judging twice with positions swapped and reference-guided judging (§11 [V]).
- Existing networks do not merge free text: Bittensor's validators score miners for emissions and the protocol does not merge outputs into one answer (§13 [V]); Allora averages numeric inferences only, by a loss-weighted average, and is designed for numeric targets (§13 [V]).

**Design consequences.** The mechanism (a) keeps answers independent in the first round so that no answerer is swayed before it has answered; (b) reviews blind, in randomized order and twice with positions swapped, because that is the mitigation the evidence names; (c) never takes a plurality vote over free text, because correct answers get discarded by plurality (§11 [V]); (d) synthesizes once and stops, rather than running rounds of debate that can flip correct answers; (e) returns disagreement to the user as a splits list rather than manufacturing agreement; and (f) tells the user, whenever a strong model is in a pool, that sampling that one model k times is often better and cheaper. The register's numbers come from benchmarks and specific models; none of them is a prediction of how this network's pools will behave, and the mechanism can make an answer worse.

## 4. Roles and rounds

Three roles, all normative. A session is opened per **(node, `modelId`)** pair, never "per node": a node that holds a second role with the same model runs the second role as another job on the same session, and a node that holds a second role with a *different* model it offers gets a separate session for it (the session's `modelId` is immutable). The disclosure sheet lists `roles[]` per session, and no node holds a role the sheet did not disclose. Jobs on one session run one at a time (`maxConcurrentJobsPerSession = 1`), because receipts and vouchers form one chain per session; a node's second role therefore waits for its first job to end, and the client runs a round concurrently only across different sessions.

| Role | Receives | Produces |
|---|---|---|
| `answerer` | The full prompt and any granted context, sealed separately | One independent answer |
| `reviewer` | The full prompt plus all k answers, anonymized under stable IDs `A1…Ak` and presented in randomized order, twice with positions swapped | One structured critique per answer ID per pass |
| `synthesizer` | The full prompt, all answers and all critiques | The merged answer, the splits list, the agreement level |

**k and the pools.** k ≥ 2 answerers are chosen by the user or by the client-side orchestrator from the pools of the models the user picked. Different models are allowed and are the default suggestion for diversity; the *several-models* preset fails closed and asks the user when fewer than two confirmed `modelId`s are available in the confirmed pools. Several samples from one model must **never** be described as diverse models: the client labels that case as one model sampled k times. The illustrated k = 3 below is non-normative; the default k is an open question.

**Reviewers.** Each reviewer runs **two review jobs**, one per position-swapped pass (section 5), each with its own `jobId`, sequential on that reviewer's session (`maxConcurrentJobsPerSession = 1`). The reviewers are either the answerers themselves — each reviewing the others' answers in those two further jobs on its own session, after its answer job has ended, if it reviews with the same model, or on a separate session if it reviews with another model it offers — or a separate reviewer set. By default a reviewer runs a different model than the producer it reviews, so that self-preference (§11 [V]) has less to work with; this is a default, not a guarantee of independence. The blind cross-check is on by default for k ≥ 3 and optional for k = 2.

**Synthesizer.** User-chosen. It may be the user's local model, in which case it adds no reader; a remote synthesizer is a full-prompt reader and the sheet says so.

**Rounds.**

- **Round 1 — independent answers.** The same prompt is sealed separately to each answerer: each (answerer, `modelId`) pair has its own session, its own HPKE envelope, its own `clientJobPublicKey`, its own `commitKey` and its own privacy mode. The k answer jobs run concurrently because they are on different sessions. No answerer learns who else answers or sees another answer while generating.
- **Round 2 — blind cross-check** (default on for k ≥ 3, section 5). The client assigns each answer a stable anonymous ID `A1…Ak` once per request, by a random permutation. Each reviewer receives the prompt plus all answers under those IDs, in randomized order, and is asked twice with positions swapped; its output is a structured critique per answer ID per pass.
- **Round 3 — synthesis** (section 6). The synthesizer receives the prompt, the answers and the critiques, and returns the merged answer, the splits list and an agreement level. It stops at the approved round, cost or latency limit rather than manufacture agreement; there is no fourth round by default.

Every intermediate result returns sealed to the client, which decrypts it and re-seals only what the next disclosed recipient is entitled to receive. Nodes never receive one another's envelopes or keys, and intermediate text is data: it never changes who the recipients are or what they are paid.

```mermaid
sequenceDiagram
    participant U as Client
    participant A as Answerer A
    participant B as Answerer B
    participant C as Answerer C
    participant R as Reviewer (different model than the producer it reviews)
    participant S as Synthesizer (user-chosen; may be local)
    U->>U: disclosure sheet: k = 3 answerers, reviewers, synthesizer; caps summed; user signs
    par Round 1 — independent, sealed separately
        U->>A: prompt (own session, own envelope)
        U->>B: prompt (own session, own envelope)
        U->>C: prompt (own session, own envelope)
        A-->>U: answer a (sealed to client)
        B-->>U: answer b (sealed to client)
        C-->>U: answer c (sealed to client)
    end
    U->>U: assign stable IDs A1, A2, A3 by one random permutation; randomize presentation order
    U->>R: Round 2 — prompt + answers A1, A2, A3 presented in order X
    R-->>U: critique per answer ID, pass 1
    U->>R: prompt + the same answers, same IDs, presented in order Y (positions swapped)
    R-->>U: critique per answer ID, pass 2
    U->>S: Round 3 — prompt + answers + critiques
    S-->>U: merged answer, splits list, agreement level
    U->>U: label "contested" if splits non-empty or agreement low; offer raw answers and critiques
    Note over U,S: every node is paid by its own vouchers; disagreement changes nothing about payment
```

## 5. Blind cross-check

The cross-check exists to counter the biases the evidence names, not to establish truth.

**Anonymization.** Before any reviewer sees an answer, the client strips everything that identifies its producer: node, model, session, and any self-identifying preamble the client can detect. Each answer then gets a **stable anonymous ID** `A1…Ak`, assigned **once per request** by a random permutation of the answers; the ID never changes between passes or between reviewers. Answers are never identified by position: a position changes between passes, so "answer 1" would name different answers in the critiques being combined, and scores and disputed claims would be attributed to the wrong answer. Every critique, every score and every split refers to the stable ID, and the client normalizes nothing before synthesis because there is nothing to normalize.

**Randomized order.** The presentation order of the answers is drawn at random per reviewer and per pass, so that no systematic position maps to a particular producer across reviewers; the IDs travel with the answers, so the order changes and the IDs do not.

**Swapped positions.** Each reviewer is asked twice — each pass is its own job, with its own `jobId`, run after the previous one on the reviewer's session: once in a random order and once with positions swapped (for k = 2 the two orders; for k ≥ 3 a second random permutation that moves every answer), with the same IDs in both passes. The strongest judge in the register was consistent on only 65.0 % of swapped orders (§11 [V]); two passes let the client see whether a score depends on position, by comparing the two scores given to the same ID. Scores that disagree between the two passes are reported as inconsistent rather than averaged silently; such disagreement is **expected** — it is what position bias looks like — and it never by itself marks a synthesis incomplete (section 7).

**Structured critique.** A reviewer returns, per answer ID and per pass: the claims it disputes, the errors it found, and a score from 1 to 5. Free-form prose is allowed in addition but is not what the synthesizer or the client acts on. The score scale is an open question.

**No majority vote over free text.** The default never selects an answer by plurality. The register shows correct answers present but discarded by plurality vote, with an oracle gap of up to 32.3 percentage points (§11 [V]). Where the user wants a vote, the self-consistency variant over a short extracted answer is the right tool (section 9), and only for tasks whose answer is a number, a choice or a label.

**Limits of blindness.** Blindness is a bias mitigation, not a guarantee of anonymity or of independence. An operator who runs two nodes recognizes its own style; a reviewer that is also an answerer knows which answer is its own; reviewers of the same family as a producer may still prefer it; and operators can collude outside the protocol. The client shows the operator count on the sheet, defaults the reviewer to a different model than the producer, and shows every raw score, so that a user can discount a review — it does not claim to have made collusion impossible.

## 6. Synthesis and the splits list

The synthesizer must return three things, and the client parses them before showing anything: the merged answer, the **splits** list, and the agreement level. A synthesis that omits any of the three, or returns one malformed, is treated as incomplete (section 7); an **empty splits list is valid** and means the synthesizer found no claim the answers disagree on.

- **`merged`** — the merged answer, in the form the user asked for.
- **`splits[]`** — one entry per claim the answers disagree on, with the claim stated neutrally and, for each position, which answers hold it (by stable anonymous ID) and which critiques support or dispute it (each critique named by reviewer, answer ID and pass). The synthesizer must list a split rather than silently choose a side; it may state which position it adopted in `merged` and why, but the split stays in the list.
- **`agreement`** — one of `high`, `medium`, `low`, with a one-line reason. It is a label, not a probability; nothing in the register calibrates it.
- **`stoppedAt`** — the round at which the synthesizer stopped and why (the approved round limit, the cost cap or the latency limit); the synthesizer never adds a round to reach agreement.

A synthesis output that parses:

```json
{
  "requestId": "req-7f3a",
  "sheetVersion": 2,
  "k": 3,
  "answerIds": ["A1", "A2", "A3"],
  "merged": "Both an index on (customer_id, created_at) and partitioning by month would reduce the query's scan; start with the composite index because it needs no migration, then measure before partitioning.",
  "splits": [
    {
      "claim": "Whether monthly partitioning is needed at this table size",
      "positions": [
        { "position": "Partition now; the table will pass 500M rows within a year", "answers": ["A1"], "supportingCritiques": [] },
        {
          "position": "Index first; partition only if measured scans stay slow",
          "answers": ["A2", "A3"],
          "supportingCritiques": [
            { "reviewer": 1, "answerId": "A1", "pass": 1 },
            { "reviewer": 1, "answerId": "A1", "pass": 2 }
          ]
        }
      ],
      "adoptedInMerged": "Index first",
      "reason": "Two answers and both passes of reviewer 1's critique of A1 favour measuring before partitioning; A1 gives no measurement."
    }
  ],
  "agreement": "medium",
  "agreementReason": "All answers agree on the composite index; they disagree on partitioning.",
  "stoppedAt": { "round": 3, "limit": "approved round limit" },
  "scores": [
    { "answerId": "A1", "reviewer": 1, "pass1": 3, "pass2": 3 },
    { "answerId": "A2", "reviewer": 1, "pass1": 5, "pass2": 4 },
    { "answerId": "A3", "reviewer": 1, "pass1": 4, "pass2": 4 }
  ]
}
```

The `scores` block is the client's own summary of the reviewers' critiques, attached for the user; the synthesizer does not produce it. `A1…Ak` are the stable anonymous IDs assigned once per request in round 2 (section 5); presentation positions are not recorded anywhere in the output, because they differ between passes and reviewers and would make a reference ambiguous. The client maps an ID back to its session only when the user asks for the original answers.

## 7. Surfacing disagreement in the client

The client is the only party that sees everything, and it shows disagreement rather than hiding it:

1. **The merged answer** is shown first, with the agreement level beside it.
2. **The `contested` label** is applied whenever the splits list is non-empty or the agreement level is `low`. A contested response is still shown; the label tells the user that the answers did not converge and that the merged text takes a side on something.
3. **Incomplete synthesis.** A synthesis is **incomplete** only when its output does not parse, or lacks `merged`, `splits` or `agreement`, or has one of them malformed. Then the client says so and shows the raw answers and critiques instead of a merged answer. Nothing about the *content* of the critiques makes a synthesis incomplete: a difference between the two position-swapped passes is expected (position bias, section 5), and an empty splits list is valid.
4. **Reviewer conflict shown, not relabeled.** When the critiques conflict — disputed claims in one critique that another critique affirms, or scores that diverge across reviewers — and the splits list is empty, the client shows the merged answer as returned and surfaces the conflict beside it: the disputed claims and both passes of scores, with a note that the reviewers disagreed on something the synthesis does not list. The user can then read the raw answers and critiques (next item) and decide; the synthesis stays complete and its label follows item 2.
5. **Original answers and critiques on request.** Every answer, every critique and both passes of scores are available to the user under their stable IDs, mapped back to the node and model that produced them; the mapping is shown only on request so that the user reads the synthesis blind first if they choose.
6. **Reader count.** The client shows, from the confirmed sheet, how many nodes and operators can read the prompt for this response: the banner "N nodes can read your prompt" takes N from the sheet's `readersOfFullPrompt` (the floor count of nodes that can read the prompt, by distinct node and by distinct operator), and the payload kinds (full prompt; all answers and critiques) are listed separately without counting any node twice. The sheet's `counts.fullPrompt` is the number of distinct nodes literally sent the full prompt; `readersOfFullPrompt` is never below it, and in a collective answer the two are equal, because every reader here receives the prompt as text. Amounts in this copy are shown in ETH as a decimal with the unit, never as raw wei.

A client that shows a merged answer without the label, the agreement level and access to the originals does not implement this feature.

## 8. Cost and latency

A collective answer costs at least k times the single-node tokens, plus the cross-check, plus the synthesis. The disclosure sheet shows the total as a **multiplier against one session** for this request; the multiplier is computed by the client from the actual k, the reviewer count and the confirmed prices, and is **not a protocol constant**.

**Symbolic cost.** Let P be the prompt tokens (prompt plus granted context), A the output tokens of one answer, k the number of answerers, r the number of reviewers (r = k when the answerers review), c the critique tokens a reviewer writes per answer per pass, and M the output tokens of the synthesis. Each reviewer reads all k answers twice (swapped positions). Then:

- Round 1: input k · P, output k · A.
- Round 2: input r · 2 · (P + k · A), output r · 2 · k · c.
- Round 3: input P + k · A + r · 2 · k · c, output M.
- **Total input ≈ k · P + 2r · (P + k · A) + (P + k · A + 2r · k · c); total output ≈ k · A + 2r · k · c + M.**

The total is at least k · (P + A) before any review — the floor the user pays even when the cross-check is off — and grows with r and with the two passes. Each session's cost is its tokens at its own confirmed prices, so the sheet sums per session and shows the sum as the multiplier.

**Worked example, token counts only (no wei; illustrative, non-normative).** P = 1,000, A = 500, k = 3, r = 3 (the answerers review), c = 100, M = 700:

| Round | Input tokens | Output tokens |
|---|---|---|
| 1 — three answers | 3 · 1,000 = 3,000 | 3 · 500 = 1,500 |
| 2 — three reviewers, two passes each | 3 · 2 · (1,000 + 1,500) = 15,000 | 3 · 2 · 3 · 100 = 1,800 |
| 3 — synthesis | 1,000 + 1,500 + 1,800 = 4,300 | 700 |
| **Total** | **22,300** | **4,000** |
| Single node, same prompt | 1,000 | 500 |

In this example the request reads about 22× the input tokens and about 8× the output tokens of a single session; with equal input and output prices it is roughly 17.5× the tokens of one session. The sheet shows that multiplier against one session for the user's actual prices, and the user funds a cap on every session before anything starts. A remote synthesizer is one more session; a local synthesizer costs no session.

**Latency.** The three rounds are sequential, and each round waits for its slowest participant: time ≈ max over answerers (round 1) + max over reviewers of two passes (round 2) + synthesis (round 3). Within a round, jobs run concurrently only across different sessions; jobs on one session (an answerer that also reviews with the same model, or a reviewer's two passes, each its own job) run one after the other, which the latency estimate must include. Time-to-first-token is the sum of three generations, which the register records as the stated limitation of mixture-of-agents designs (§11 [V]). A collective answer is never the right choice for latency-sensitive chat.

## 9. When not to use it

**Collective answer is always the user's choice.** The list below has two kinds of entry. Items 1–4 are **hard stops**: the client cannot start `collective_answer` because a precondition is missing, and the request fails closed. Items 5–11 are **cases the client advises against**: it says why, suggests the better tool, and the assessment step of docs/protocol/orchestration.md does not recommend the feature there — but the user who has read the advice may still opt in, and the client then runs the feature exactly as specified.

1. **No opt-in** for this request. Consent for an earlier request, or a funded session, is not consent.
2. **k under 2.**
3. **The cap is too small** to cover every session the sheet lists; the request fails closed rather than starting with fewer nodes.
4. **The pool cannot fill the confirmed set** — including the several-models preset with fewer than two confirmed `modelId`s — the request fails closed and asks.
5. **Short factual lookups**, where one answer is as good as three and the review adds nothing.
6. **Latency-sensitive chat**: three sequential rounds.
7. **One strong model is in a pool.** The client **suggests first** sampling that one model: self-consistency for a short checkable answer, Self-MoA for free text (below), because one strong model sampled many times beat a mixed mixture by 6.6 % (§11 [V]). The user may still opt into `collective_answer` after seeing the suggestion; the suggestion never blocks the feature.
8. **Math and code with checkable answers.** Prefer self-consistency, or a single strong model plus a test; a vote over a short extracted answer is where the register shows gains (GSM8K +17.9 %, §11 [V]), and free-text debate costs 2.1–3.4× for equal or lower accuracy (§11 [V]).
9. **Privacy-sensitive prompts.** Every answerer, every separate reviewer and a remote synthesizer read the full prompt; the sheet shows the exact count, which is at least k.
10. **The user asked for the cheapest single node.**
11. **Any case where the user would not pay k×** — the floor cost, before review and synthesis.

The assessment step recommends the feature only for tasks it classifies as large and open-ended; everything else is single-node by default. A recommendation is advice: the user opts in or out per request, and the client starts the feature whenever the user opts in and items 1–4 do not apply.

**The two cheaper variants** are different methods and the client names them separately:

- **Self-consistency** — k samples of one strong model and a majority vote over a short extracted answer. Only for tasks with a short checkable answer (a number, a choice, a label), because that is where a vote is meaningful (§11 [V]). One node, k jobs; readers: that node, plus the synthesizer if any and remote.
- **Self-MoA** — k samples of one strong model combined by a synthesizer, for free text (§11 [V]). One node, k jobs, plus synthesis. A plurality vote is never applied to free text.

Neither variant is a collective answer in the sense of this document, and neither may be described as several models.

## 10. Parallel planning with the same mechanism

`parallel_planning` reuses the exact mechanism with plans as answers. Its schema for a plan is owned by docs/protocol/orchestration.md.

- **Round 1.** k planner nodes each receive the full prompt and produce a plan independently; every planner is a full-prompt reader.
- **Round 2.** Plan reviewers cross-examine the anonymized plans blind, under stable anonymous IDs assigned once per request (section 5), in randomized order, twice with positions swapped, and return a structured critique per plan ID (claims disputed, missing steps, dependency errors, a 1–5 score). Every plan reviewer is a full-prompt reader.
- **Round 3.** The plan synthesizer merges the converged and evidence-backed parts into one plan and keeps the open splits **as questions for the user**; the plan synthesizer is a full-prompt reader when remote.
- **Objection round.** The merged plan is shown to the planners, which may object. **This round is not blind** — each planner sees the merged plan and may recognize its own and others' contributions — and the disclosure sheet says so before the user signs.
- **Client.** The client shows the merged plan, the splits and any rank the reviewers produced. **A rank is never executed automatically**: position bias alone (§11 [V]) is reason enough not to let a judge's ordering open sessions. The user confirms the splits, or stops; only then may execution sessions open, under a new sheet version that lists the execution nodes and is confirmed before any `openSession` — a change of node, model, data scope, price, cap or reader set always creates a new sheet version (docs/security/privacy-and-contexts.md).

The cost formula of section 8 applies with plans in place of answers; a plan is usually shorter than an answer, and the objection round adds one more job per planner.

## 11. Reviewing sub-task outputs

An orchestrated plan (docs/protocol/orchestration.md) may route each sub-task result to a **single reviewer from a different model family than the producer**, judged twice with positions swapped where there is more than one candidate output, under the same roles and the same payment rules as here. The reviewer receives the sub-task and its output; it is a full-prompt reader unless the client has verified that its payload contains no prompt text, and the sheet counts it accordingly.

If the plan requires a different-family reviewer and none is available in the confirmed pools, the affected plan **fails closed** until the user approves an explicitly weaker revision (same-family review, or no review); the client never substitutes silently.

A sub-task review, like a collective answer, is a quality aid: a low score is information for the merge step and for the user, never a payment event.

## 12. Payment and sessions

- **One session per (node, `modelId`).** Each answerer, each separate reviewer and a remote synthesizer is paid through an ordinary session opened by `openSession` for that node **and that model**. A node that both answers and reviews with the same model runs its answer job and then its two review jobs (one per pass), one after the other, on one session; a node selected to review or synthesize with a *different* model it offers gets a separate session for that model, because a session's `modelId` is immutable and the later job would otherwise fail or run the wrong model. Every such session is on the sheet. There is no multi-party session and no new contract function.
- **One job at a time per session.** `maxConcurrentJobsPerSession = 1`: receipts and vouchers form one chain per session. A round runs concurrently only across different sessions; if the user wants a node's second role to run in parallel on the same (node, `modelId`), the client opens a separate session for it, listed on the sheet.
- **Caps summed on the sheet.** Every session has its own cap `min(depositWei, maxSpendWei)`; the sheet lists each one and carries `totalCapWei` as their sum, with the L2 gas estimate carried separately. User-facing copy shows both in ETH as a decimal with the unit (wei ÷ 10^18), never as raw wei. The run does not start until every session is funded.
- **Receipts and vouchers as usual.** Each node sends its input receipt `(sessionId, jobId, jobInputTokens, cumulativeInputTokensAfter)` before prefill and a chunk receipt per output chunk; the client checks counts and signs cumulative vouchers of the one canonical `Voucher` type on each session separately. Each session has its own `commitKey` and `outputCommitment` chain. Cumulative counts are the totals covered by the last voucher the client signed: a job whose input voucher the client did not sign never enters the session's counts, and a voucher covers only the prefix the client acknowledged — an unacknowledged chunk is unpaid.
- **No payment consequence of disagreement.** A discarded answer, a low score, a split, a contested label or an incomplete synthesis never reverses a signed voucher and never triggers a refund, penalty or slash; there is no slashing in v1. Nodes are paid for delivered tokens even if the synthesis discards their text.
- **Signed vouchers stand.** The user's remedy against a node whose contributions are consistently poor is to stop signing further vouchers on that session, close it, and choose other nodes next time.
- **Reputation.** Reputation events may record consistently low cross-check scores for a node **only with the user's consent**; the scores come from reviewers whose biases the register documents, and a user may decline to publish them.
- **Abandoned nodes.** If an answerer disappears mid-run, that session follows the ordinary procedure (the node redeems its highest non-final voucher while legal; `closeSession`; `finalize` after `closeDeadline`), and the run continues with the remaining answers only if the result still meets the confirmed k; otherwise it fails closed and the user decides.

## 13. Privacy

- **k readers at least.** Every answerer receives the full prompt; every reviewer receives the prompt plus all answers; a remote synthesizer receives the prompt, all answers and all critiques. Each is a full-prompt reader on the disclosure sheet, counted by distinct node and by distinct operator; the reader list in docs/security/privacy-and-contexts.md is a floor, and the client derives the count from the actual payloads it seals.
- **The sheet.** Before any session is opened or reused, the sheet lists every recipient with role, model, mode, what it receives (full prompt; all answers and critiques), prices and cap, and `readersOfFullPrompt`. The run never starts without the user's signature on it. The flow is: pick models → see the sheet → confirm → sign the `openSession` transactions; the client never lets the user confirm a sheet and then change models. Any change of node, model, data scope, price, cap or reader set — adding a reviewer, swapping a synthesizer, raising a cap — creates a **new sheet version** that must be confirmed before any `openSession` or job under it. A new session is always a new sheet version, because it is a new deposit and cap; a session reused from an earlier request needs the new request's sheet confirmed first and carries forward only the totals covered by vouchers the client signed. After each `openSession` is included, the client compares the prices copied into the session on-chain with the confirmed sheet and, if they differ, signs nothing and calls `closeSession`; prices a node reports off-chain are informational.
- **Modes per session.** Each session keeps its own privacy mode — `standard`, `attested` or, for an answerer, `verifiable` — fixed at `openSession` and public on-chain. A collective answer does not change any session's mode and does not require all sessions to share one. If the user wants an answerer's output verified (mode 2), the verifier is on the sheet before signing; wanting it later means a new sheet version and a new confirmation, never a reader added to a confirmed sheet.
- **Client-mediated re-sealing.** Every answer and critique returns sealed to the client under that job's `clientJobPublicKey`; the client decrypts, anonymizes, and re-seals only the approved material to the next disclosed recipient under a new envelope signed by that session's `sessionSigner`. Nodes never receive each other's envelope keys, and no answer travels node to node.
- **No activations move.** A collective answer exchanges only text, through the client. It never moves activations at all, unlike the experimental `model_sharding` spike, where the client forwards activations to each sheet-listed shard holder (never holder to holder) and those activations can reveal the prompt: inversion recovers 88.4 % of tokens on a 65B model and 86.88 token F1 on a 4,112-token prompt (evidence register §10 [V]), which is why every shard holder is counted as a full-prompt reader there. The readers of a collective answer are exactly the nodes that receive the prompt as text, and the sheet names each of them.
- **Metadata.** Several sessions opened by one payer at about the same time reveal on-chain that a multi-node feature was used and its approximate shape; no v1 mitigation exists (docs/security/privacy-and-contexts.md section 9).

## 14. What it is not

- **Not verification.** A collective answer compares different models, so it cannot prove that any node ran the declared model; that is verifiable mode's job, and only verifiable mode's. Identical answers from k nodes prove nothing about weights or correctness, and differing answers are not evidence of fraud, because different models may legitimately disagree.
- **Not mode 2.** Verifiable mode is opt-in re-execution by a user-chosen second node under a demonstrated deterministic profile, with the prompt disclosed to that verifier; it is a privacy mode of a session, and this feature neither sets it nor substitutes for it. Its checks — the client-side output comparison and, where a backend supports it, a TOPLOC-style activation commitment, which is not claimed on llama.cpp or mistral.rs and cannot detect speculative decoding (evidence register §5 [V]) — belong to docs/security/inference-verification.md and are never applied to the answers of a collective run, since those come from different models and are expected to differ.
- **Not the consensus of a chain.** Nothing here orders transactions, finalizes state or secures funds. The name "collective answer" is chosen so that nobody reads chain consensus into it.
- **Not a vote.** No plurality is taken over free text; the splits list exists precisely so that minority positions are not discarded.
- **Not an emission or stake-weighted score.** No token is emitted, no stake weights an answer and no reputation weight enters the synthesis; the register's examples of such designs (§13 [V]) are not what this document specifies.

## 15. Risks

### R1 — Quality degradation **[RISK] · High**

Mixing models often lowers average quality, and one strong model sampled many times beat a mixed mixture by 6.6 % (evidence register §11 [V]). A user who chooses the several-models preset for diversity may get a worse answer than the single strongest node would have given, at several times the cost. Mitigation: the client names the cheaper variants whenever a strong model is in a pool, and the assessment step recommends the feature only for large, open-ended tasks.

### R2 — Sycophancy and conformity **[RISK] · High**

Agents flip correct answers to incorrect ones over rounds, and up to 70.0 % of correct answers were destabilized by peers among homogeneous small agents (§11 [V]). Mitigation: round 1 is independent, there is one review round and one synthesis, no debate rounds by default, and disagreement is surfaced rather than resolved.

### R3 — Position bias **[RISK] · Medium**

The strongest judge in the register was consistent on only 65.0 % of swapped orders, weaker judges 23.8 %–46.2 % (§11 [V]). Mitigation: randomized order and two passes with positions swapped; inconsistent scores are reported as inconsistent, and a rank is never executed automatically. Verbosity bias and self-preference have only the different-model default as mitigation.

### R4 — Cost **[RISK] · High**

At least k× the single-node tokens before review and synthesis, and roughly 17× in the worked example of section 8; debate cost 2.1–3.4× the tokens of self-correction for equal or lower accuracy in the register's setting (§11 [V]). Mitigation: the multiplier on the sheet, caps funded before the start, and the when-not-to-use list.

### R5 — Collusion **[RISK] · Medium**

Operators who run several nodes, or who coordinate, can bias answers, reviews and the synthesis; blindness reduces but does not remove this. Mitigation: operator counts on the sheet, a different-model default for reviewers, every raw answer and critique shown on request, and a local synthesizer as the user's option. Operator diversity as a hard requirement is an open question in the threat model.

### R6 — k readers **[RISK] · High**

At least k nodes read the full prompt, plus separate reviewers and a remote synthesizer. Mitigation: opt-in per request, the sheet's `readersOfFullPrompt` count by node and operator, fail-closed rules, and the explicit entry in the when-not-to-use list for privacy-sensitive prompts.

### R7 — Hidden disagreement **[RISK] · Medium**

A synthesizer may return a confident merged answer with an empty splits list although the answers conflicted. Mitigation: the client cross-checks the critiques against the splits list and, when the reviewers' disputed claims or scores conflict with an empty list, shows that conflict and the raw answers and critiques beside the merged answer (section 7); the synthesis is not relabeled incomplete for it, since an empty splits list is valid and two-pass score differences are expected. A disagreement the reviewers also missed remains hidden, and the document says so.

## 16. Open questions

1. **Default k.** Whether the default should be 2 or 3, given that the blind cross-check is optional at k = 2 and on by default at k ≥ 3, and what the cost difference means at the price bands in force.
2. **Reviewer selection.** Whether reviewers should by default be the answerers themselves (cheaper, but each knows its own answer) or a separate set (more readers), and whether a different operator, not only a different model, should be required rather than displayed.
3. **Score scale.** Whether the 1–5 score is the right granularity, whether pairwise comparisons (as in the ranking design the register records, §13 [V]) are better for k ≥ 3, and how two-pass inconsistency should be shown.
4. **Reputation use.** Whether consistently low cross-check scores, published with user consent, should enter public reputation at all, given the documented biases of model judges, and in what format.
5. **Agreement level.** Whether `agreement` should stay a three-value label or be derived from the scores by a published rule.
6. **Objection round.** Whether the non-blind objection round of `parallel_planning` adds enough to justify one more job per planner and the loss of blindness, or should be off by default.
7. **Abandoned answerer.** Whether a run should ever continue below the confirmed k, or always fail closed and ask.
