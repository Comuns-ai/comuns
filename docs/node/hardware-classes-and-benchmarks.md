# Hardware classes and benchmarks — who can run what

Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12
**Reference:** docs/economics/cost-and-pricing.md, docs/node/node-design.md, docs/protocol/contracts-and-settlement.md, docs/evidence-register.md, docs/security/privacy-and-contexts.md, docs/adr/0010-anonymous-by-default.md

---

## 1. Summary

Comuns sorts nodes into four **hardware classes**, S < M < L < X, and models into five **tiers**, T0–T4. The two scales do different jobs. A tier is a parameter-count label attached to a model at registration; the five tiers partition the parameter-count axis (section 4). A class is a **price-band label** a node earns by publishing a self-benchmark: `hardwareClass ∈ {S, M, L, X}` (encoded 0–3) is decided by **passing per-class benchmark bars** on the public class benchmark. **A class is not a tier**: `maxTier ∈ {T0..T4}` is a separate, informational field recording the largest tier the operator benchmarked, and nothing is ever defined as "the highest tier passed". Together tier and class select the governance-set price band for (tier, class), inside which the node's offer prices must lie; stronger hardware charges more for the same model and weaker hardware charges less.

What classes do **not** do: they never decide which model a node may offer. **Classes price work through the bands; they do not gate which model a node may offer.** A node may offer any registered model it can actually load, whatever its class; `maxTier` is informational and is never read by `openSessionFromCredit`, the reference client's only way to open a session, nor by the wallet-funded `openSession`. A class M node that can load a T3 model at low speed may offer it inside the (T3, M) band. The example machines in section 3 illustrate what is **likely to fit in memory**; they are **not a serving cap** and not an eligibility table.

Everything numeric in this document is either a cited figure from docs/evidence-register.md §6, §4 or §14, marked [V] unless noted, or an illustration marked as such. No measured minimum hardware requirement is claimed; the small-hardware path (section 8) is a target to validate, not an established floor. Nothing here runs yet, and no benchmark has been executed by this project.

## 2. Scope

In scope: the meaning of the four classes and five tiers; which hardware may advertise the attested mode; illustrative example machines; the reference throughput figures the proposal may cite; the public benchmark protocol that produces `benchmarkHash` (class) and `modelBenchmarkHash` (per model); what the benchmark can and cannot prove; the small-hardware path; risks and open questions.

Out of scope: the numeric values of bands and the cost model (docs/economics/cost-and-pricing.md); the node program (docs/node/node-design.md); the contract checks on offers and bands (docs/protocol/contracts-and-settlement.md); model manifests and licenses (docs/node/model-registry-and-licenses.md).

Evidence tags: **[V]**, **[L]**, **[U]** as in docs/evidence-register.md, cited by section. Anything not cited there is UNVERIFIED.

## 3. Classes

The four classes order strictly S < M < L < X and are encoded 0–3 on-chain (contracts doc, §4). A node declares its class in `registerNode` or `updateNode` and backs it with `benchmarkHash`, the signed hash of its public self-benchmark on the **class benchmark** (section 6). The class is decided by which **per-class bars** the node's result passes on that benchmark (TTFT, decode tok/s and batched throughput on the class benchmark model); a node that passes the X bars is class X, one that passes only the S bars is class S. The bars themselves are an open question (section 10). **A class is never "the highest tier passed"**: tiers label models, classes label nodes, and the two enumerations are different (`hardwareClass` has four values encoded 0–3, `tier` has five). Classes are **labels, not measured constants**: the proposal has measured nothing, and the bars will be set by a CIP.

Illustrative example machines, and the largest tier each is **likely to fit in memory** — an illustration of memory fit, not a serving cap, written as one sentence so that it cannot be read as a table of rights: S is a CPU-only machine or one with 8–16 GB of unified memory, typically T0; M is a consumer GPU with 12–24 GB or a 32 GB unified-memory machine, typically up to T1; L is 32–96 GB of device or unified memory, typically up to T2; and X is multi-GPU or 80 GB+ per GPU, T3–T4 — every figure in that sentence is illustrative until measured, and the sentence is explicitly **not an eligibility table**.

Four consequences, all binding:

- A node of any class may offer any registered model it can load (memory fit plus its own public self-benchmark of that model, docs/node/node-design.md §5). The class only decides which band its prices must fall in.
- The same model is cheaper from a small node and dearer from a strong one, because `floorIn(c+1) > ceilingIn(c)` and `floorOut(c+1) > ceilingOut(c)` for adjacent classes (contracts doc, §9). A user who wants a T3 model slowly and cheaply can buy it from a class M node that fits it; a user who wants it fast buys it from class X.
- `maxTier` stays **informational**: it is a separate field from the class, records the largest tier the operator benchmarked (the highest tier among the models it has published a per-model benchmark for), and nothing reads it as a gate.
- The bands and the never-read-`maxTier` rule apply to `openSessionFromCredit` exactly as to `openSession`: the spend is checked against the band for (the model's tier, the node's class) and both offer prices must lie inside it (docs/adr/0011-anonymous-credits.md). A credit session's cap is its note's denomination, whatever the class.

**Attested nodes are the content-private tier, and need confidential-computing hardware.** Every node is anonymous by default: in standard mode the node can read the prompt but should not learn who asked (docs/adr/0010-anonymous-by-default.md). The attested mode adds content privacy: this node should not be able to read your prompt; a physical attack on the hardware can break that (evidence register §14). A node of any class may set the attested bit in `modes` **only when it runs on confidential-computing hardware** whose quote the client can verify — a CPU TEE (Intel TDX or AMD SEV-SNP) together with GPU confidential computing, of the kinds evidence register §14 records as available: H100 with TDX, generally available on Google Cloud [V]; H100 with SEV-SNP on Azure [V]; and Blackwell B200/B300 and the RTX PRO 6000, which support confidential computing [V, vendor]. A machine without such hardware must not advertise attested mode; it may advertise standard mode and, with a demonstrated deterministic profile, verifiable mode, whatever its class. Attested mode is not a class and moves no node into another band; it is a mode the client selects and verifies per request, and the cost of the TEE (section 5) is the operator's to price inside its band. The example machines above are illustrations of memory fit and say nothing about whether a machine can attest.

## 4. Tiers

The tiers are a **partition** of the parameter-count axis: every parameter count falls in exactly one tier.

| Tier | Parameter count (manifest `parameters`) | Examples of the size class (names only; registration is by manifest) |
|---|---|---|
| T0 | ≤ 4B | small instruction-tuned models at 1–4B |
| T1 | > 4B and ≤ 8B | 7B–8B models |
| T2 | > 8B and ≤ 32B | 14B–32B models |
| T3 | > 32B and ≤ 70B | 70B models |
| T4 | > 70B | 100B+ and mixture-of-experts models above 70B total |

An 8,000,000,000-parameter model is T1, and only T1. A tier is set at `registerModel` from the parameter count in the manifest and is immutable; a different quantization of the same weights is a different manifest and therefore a different `modelId`, but the same tier. Tiers label price bands; they never gate who may serve.

## 5. Reference figures

The tables cite only figures from docs/evidence-register.md §6, §4 and §14. Single-stream and batched measurements are **separated** because they measure different things: single-stream is one user's decode speed; batched throughput is aggregate tokens per second across many concurrent requests, which an inference provider sees and a single user never does. The two must never be compared or averaged. All rows are [V] unless noted; the engine, quantization and date are part of the figure.

**Single-stream decode (llama.cpp, Q4_K_M, 2024 measurements)**

| Model | Hardware | Decode tok/s | Mark |
|---|---|---|---|
| 8B | RTX 3090 | ~112 | [V] |
| 8B | RTX 4090 | ~128 | [V] |
| 8B | A100 | ~133–138 | [V] |
| 8B | H100 PCIe | ~144 | [V] |
| 8B | M3 Max | ~51 | [V] |
| 8B | M2 Ultra | ~76 | [V] |
| 70B | 2× RTX 3090 | ~16 | [V] |
| 70B | 2× RTX 4090 | ~19 | [V] |
| 70B | A100 | ~22–24 | [V] |
| 70B | H100 | ~25 | [V] |
| 70B | M2 Ultra | ~12 | [V] |

**Single-stream decode (other reported setups)**

| Model | Hardware | Decode tok/s | Mark |
|---|---|---|---|
| Qwen3-8B | RTX 5090 32 GB | ~186 | [V] |
| Qwen3-14B | RTX 5090 32 GB | ~124 | [V] |
| Qwen3-32B | RTX 5090 32 GB | ~61 | [V] |
| 70B Q4 | RTX 5090 32 GB | does not fit | [V] |
| 7B Q4_0 | M4 Max | ~83 | [V] |

**Batched throughput (TensorRT-LLM, FP8, 1× H100) — aggregate, not per user**

| Model | Hardware | Throughput tok/s | Mark |
|---|---|---|---|
| 8B | 1× H100 | ~27,569 | [V] |
| 70B | 1× H100 | ~3,191 | [V] |

**Power and memory**

| Item | Figure | Mark |
|---|---|---|
| RTX 4090 board power | 450 W | [V] |
| H100 SXM board power | up to 700 W | [V] |
| Mac Studio M5 Ultra unified memory | up to 512 GB | [V] |

**TEE overhead (a note, not a planning assumption).** The cited figures are dated snapshots from different setups and are shown side by side, never averaged:

| Source | Setup | Figure | Mark |
|---|---|---|---|
| Independent study (evidence register §14, compiled 2026-10-13) | H100 + TDX | time-to-first-token up 21.8–27.8 %, throughput down 11.5–21.1 % | [V] |
| NVIDIA (evidence register §14) | Confidential computing, vendor figure | 1–8 % overhead | [V, vendor] |
| Older snapshot (evidence register §4, 2026-10-12) | 8B model on H100 + SEV-SNP and H200 + TDX | throughput −6.85 % / −8.84 %, TTFT +19–21 % | [V] |
| Older snapshot (evidence register §4, 2026-10-12) | 70B model, same setups | roughly 0–2.3 % | [V] |

Attested-mode nodes should expect a cost somewhere in that spread, and the independent measurement is the least favourable of them; no document plans on the exact numbers.

How to read the tables: a 70B model that does not fit a 32 GB card is the clearest statement of memory fit in the register; the KV cache on top of the weights depends on context length and on the backend's cache quantization, so a model that "fits" at one context may not at another (docs/node/node-design.md §5). The same 8B model runs at ~51 tok/s on one machine and ~186 tok/s on another; that spread is what the classes price.

## 6. Benchmark protocol

Every node publishes two kinds of self-benchmark and signs them. The **class benchmark** produces `benchmarkHash` and decides the class label. A **per-model benchmark** produces `modelBenchmarkHash` for each model the node offers and is pinned to that exact `modelId` and manifest. Both use the same method so that any operator can rerun either. The protocol below is PROPOSED; its constants are open questions (section 10).

| Element | Rule |
|---|---|
| Prompts | A public synthetic prompt set, published in the repository with its hash; no private or user data |
| Pinned inputs | Model manifest (hence weights and quantization), tokenizer digest, engine name and build, driver versions, all recorded in the result |
| Lengths | Fixed prompt length and fixed output length per run, stated in tokens of the pinned tokenizer |
| Cold and warm | One cold run (first load) and warm runs after it, reported separately |
| Batch size | Batch size 1 for the single-stream numbers, plus a batched run at a stated concurrency, reported **separately** and never merged |
| Concurrency | The concurrency the node intends to advertise for that model; the memory-fit check is at this concurrency |
| Repetitions | A fixed number of warm repetitions; median and spread reported |
| Reported | Time-to-first-token, decode tokens per second (single-stream), batched throughput (tokens per second at the stated concurrency), peak device and host memory, and the power-measurement method (board sensor, wall meter, or "not measured") |
| Result | A canonical JSON result; its hash is signed by the node's key and stored on-chain as `benchmarkHash` (class) or `modelBenchmarkHash` (per model, in the offer); the result file is served by the node and may be mirrored by indexers |
| Renewal | Results carry a date; a renewal period is set by CIP; a result older than the period is shown as stale by indexers (a reputation signal, not a contract rule) |

For the class benchmark the node runs the **class benchmark model** (section 8 of docs/node/model-registry-and-licenses.md: Apache-2.0 or MIT, small enough for class S; the concrete file is open) and reports its figures; the class is the highest class whose **per-class bars** those figures pass. For a per-model benchmark the node runs the same procedure on the offered model and manifest; `maxTier` is simply the largest tier among the models the operator has benchmarked this way, and the class benchmark does not set it. A node that changes its backend build, drivers or hardware re-runs both and republishes through `updateNode`.

## 7. Anti-spoofing limits

The benchmark is a **self-published claim backed by a signature; it is not an unfakeable hardware proof.** What it proves is that someone holding the node's key signed a result file of the right shape. What it does not prove:

- **Proxying.** An operator can forward the benchmark — and later verification requests — to a stronger machine or a hosted API, then serve real traffic from something cheaper (threat model T11). The result file cannot distinguish this.
- **Fabrication.** An operator can write any numbers into the result and sign them.
- **Reported incident.** A 2024 fake-GPU incident on a compute marketplace led that marketplace to add hardware checks (evidence register §2, [L]); the register records it as a reported incident, and this proposal treats it as evidence that self-reported hardware is gamed in practice.

What the proposal does about it, all off-chain and all reputation, **never slashing**:

- **Spot re-benchmarks.** Community verifiers, or the client itself, may run a **private, rotating prompt set** — never the public self-benchmark set — against a node's real endpoint through an ordinary credit session reached through a relay, so that the node is not told who is measuring, **at random times**, and publish the measured TTFT and tok/s beside the node's claim. The public set is useless for this: an operator who proxies it to a stronger machine and serves real traffic from a cheaper one shows no gap on that set. A private set chosen at random times is harder to anticipate, but it is **still not an unfakeable proof**: an operator can proxy every request, and a measurement over the internet includes the measurer's own network. A large gap is reputation evidence. It is not slashing, because the bond is never seized (contracts doc).
- **Verifiable mode on mode-2 sessions.** A user who chooses mode 2 gets a re-execution by a second node, and a substituted model shows up there — **but a session's mode is public on-chain** (`SessionOpened` carries it), so mode-2 checks cover only mode-2 sessions, and an operator can behave honestly on those alone while substituting on standard-mode traffic. It is an integrity check for the session it runs on, not for the node; it costs the user a second session.
- **Unannounced client-side spot checks of standard-mode sessions.** The mitigation for the gap above is opt-in and client-side: the user re-runs a sampled prompt from a standard-mode session on another node and compares. That second node reads the prompt and is disclosed on the sheet like any reader.
- **Pinned tokenizer.** A node that serves a different model than it claims tends to count tokens differently; the input receipt against the client's own tokenization surfaces that at the first job.
- **Indexers show staleness** and the spread between claimed and spot-measured figures; clients may sort by measured speed rather than claimed class.

The class therefore sets a price band, and the market — not the contract — punishes a node whose price does not match its delivery. A node that claims class X and delivers class M speed is overpriced inside its band and loses sessions to nodes whose measurements match their claims.

## 8. Small-hardware path

The proposal wants a CPU-only machine or a small unified-memory laptop to be able to join as class S and offer T0 models. The register contains **no** CPU-only throughput figure, so this is a **target requiring validation, not a measured minimum**: no document may state a minimum CPU, memory size or tokens-per-second figure as established until a benchmark result exists. What can be said:

- The llama.cpp adapter is the small-hardware path because its kernels run on CPU and on every listed GPU family (evidence register §3, [V]) and it supports 1.5–8-bit quantizations [V].
- A T0 model at a 4-bit quantization has weights in the low gigabytes by the memory-fit formula of docs/node/node-design.md §5, with illustrative coefficients; the KV cache at a short context and concurrency 1 adds less. Whether the resulting decode speed is useful to a user is exactly what the Phase 1 and Phase 2 measurements must show.
- A class S node is priced in the lowest band for every tier, so even a slow T0 node has a lawful price; whether users buy at that speed is a market question.
- The class benchmark model must itself be small enough to run on class S hardware, which is why its license and size are constrained (docs/node/model-registry-and-licenses.md §8).

Until a CPU-only result is published, the honest statement is: the proposal is designed so that small machines can participate, and has not yet shown that they can do so usefully.

## 9. Risks

### R1 — Bands misread as eligibility **[RISK] · High**

Users and operators will read "class M, typically up to T1" as "class M may not serve T2". It may; the sentence illustrates memory fit. Mitigation: every document says classes price and do not gate; indexers never hide a model from a class; `maxTier` is labelled informational everywhere it appears.

### R2 — Benchmark gaming **[RISK] · High**

Proxied or fabricated benchmarks put a slow node in a high band. Nothing on-chain can detect it, and verifiable mode catches substitution only on sessions opened in mode 2, which the node can see. Mitigation: section 7 — spot re-benchmarks on a private rotating prompt set at random times, opt-in unannounced client-side spot checks of standard-mode sessions, measured-speed sorting in clients; all reputation, none slashing, none an unfakeable proof.

### R3 — Figures cited as planning constants **[RISK] · Medium**

The 2024 single-stream numbers and the batched H100 numbers are from specific engines, quantizations and dates and will drift. Mitigation: every figure carries its engine and mark; the cost document uses them as illustrations only; the register is the only source and changes by pull request.

### R4 — Memory fit misjudged **[RISK] · Medium**

An operator offers a model that fits at concurrency 1 and fails at the advertised concurrency, or fits at a short context and not at the session's. Mitigation: the memory-fit check runs at the advertised concurrency and context; the node refuses rather than swaps into failure; stale or wrong offers are a reputation event, not a contract matter.

### R5 — Small-hardware path stated as established **[RISK] · Medium**

Marketing text turns "a target" into "runs on any laptop". Mitigation: this document states no minimum; the first published CPU-only result replaces the target with a figure, and until then every user-facing text says "to be validated".

### R6 — Batched and single-stream figures confused **[RISK] · Low**

A ~27,569 tok/s batched figure quoted next to a ~144 tok/s single-stream figure misleads a reader about what one user gets. Mitigation: separate tables, separate reporting in the benchmark result, and the rule that the two are never averaged.

### R7 — Attested mode advertised without confidential-computing hardware **[RISK] · Medium**

An operator sets the attested bit on a machine that cannot produce a valid quote, or users read "class X" as "content-private". Mitigation: the client verifies the quote and the binding of both node keys before sealing, and fails closed with no downgrade to standard mode (docs/security/privacy-and-contexts.md §8.1); every document keeps class and mode apart; the attested banner says what the hardware cannot stop: a physical attack can break it (evidence register §14). A failed quote is a reputation event, not slashing.

## 10. Open questions

1. **The class-S benchmark model.** Which Apache-2.0 or MIT model, at which quantization, is small enough to run on CPU-only hardware and still discriminates between classes; the constraint is in docs/node/model-registry-and-licenses.md §8 and the concrete file is open.
2. **Bars per class.** The TTFT, tok/s and batched-throughput thresholds on the class benchmark model that decide S, M, L and X, and whether they are single-stream only or also batched.
3. **Renewal.** Whether a per-model benchmark must be renewed together with the class benchmark, on the same period, or only when the manifest, build or hardware changes.
4. **Benchmark constants.** Prompt and output lengths, repetition count, the stated concurrency for the batched run, and the power-measurement method required for a result to count.
5. **Spot re-benchmark protocol.** Who curates and rotates the private prompt set, how a measurer publishes a spot result so that indexers can match it to a node's claim without revealing the set, and how the measurer's own network is reported.
6. **Unified-memory classes.** Whether machines with large unified memory but modest bandwidth (the 512 GB figure, evidence register §6, [V]) belong in the class their memory suggests or the class their decode speed suggests; the class benchmark answers this by measurement, but the bars must be chosen with it in mind.
7. **Attestation bars per hardware family.** Which CPU TEE and GPU confidential-computing combinations, firmware versions and measurement lists a client accepts for the attested bit, and how that list is published and revised; owned with docs/security/privacy-and-contexts.md.
