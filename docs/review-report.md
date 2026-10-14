# Review report — consistency pass

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** docs/README.md, docs/adr/README.md

---

**Note (2026-10-14).** This report reviewed the baseline documents. ADR 0010, ADR 0011, ADR 0012 and CIP-0002 propose a later model in which the default is anonymous standard mode over relays with anonymous credits, local execution is not an option, attested mode is the content-privacy tier, and contexts carry no wallet link. In that later model, standard mode lets the node read the content and the node should not learn who asked; attested mode means the node should not be able to read the prompt, barring a physical attack (evidence register §14). The evidence register's How to cite section is now §17. Section and question numbers in this report refer to the baseline versions of the documents. The lines below are not a review of that later model.

## 1. Method

Every file in the repository's document map was read in full — the seven root files, every file under docs/ (including the nine ADRs, the three CIP files and the pricing fixture), the two pitch files (read, never edited; they belong to the pitch deck update) and the three scripts. The two checkers were run before any edit and again after the last one. The 22 invariants of the review scope were checked by reading the owning documents and by a read-only text sweep over every non-hidden file for the phrases each invariant forbids or requires (AI-tool credits, class-serving restrictions, "highest tier passed", loose tier predicates, "node to node" activation traffic, role-token variants, the EIP-712 type string, the chain id without its mark, domains, e-mail addresses, calendar dates, feature and mode names, phase names). Precedence when files disagreed: ADR, then docs/protocol/contracts-and-settlement.md, then docs/security/privacy-and-contexts.md, then docs/security/threat-model.md, then docs/protocol/orchestration.md, then docs/protocol/collective-answers.md, then docs/node/distributed-execution.md, then docs/economics/cost-and-pricing.md, then docs/architecture/system-architecture.md, then the rest; the review decisions D1–D20 and E1–E50 won over any sentence. Edits were limited to repairing contradictions against the invariants, fixing links, headers and numbering, making the checks pass, and recording the known issues carried forward; no caveat, risk, UNVERIFIED mark or non-goal was removed, and no feature, number, token, slashing rule, date, audit, grant, contact or document other than this report was added.

## 2. Invariant results

### 2.1 Invariant 1 — Arbitrum One EVM, Stylus not v1 — Pass

Checked: docs/adr/0001-settle-on-arbitrum-one-evm-not-stylus.md; docs/protocol/contracts-and-settlement.md §2, §14; docs/project-charter.md 4.2, R2; docs/architecture/system-architecture.md §1, R1; docs/architecture/deployment-and-decentralization.md §5; docs/faq.md; docs/glossary.md; docs/risk-register.md §1; pitch/pitch-deck.md slide 9. Every statement names Solidity/EVM on Arbitrum One and cites the pause since 2026-10-02 (evidence register §1).

### 2.2 Invariant 2 — Off-chain Rust node; llama.cpp kernels are C/C++ — Pass

Checked: docs/adr/0002-off-chain-rust-inference.md; docs/node/node-design.md §1, §4; docs/project-charter.md 4.3; docs/architecture/system-architecture.md §1, §5; README.md; docs/faq.md; docs/project-plan.md §4; docs/risk-register.md §1; docs/evidence-register.md §3. Wherever the backend's language is characterized, the kernels are called C/C++ and Rust is not claimed to make inference faster.

### 2.3 Invariant 3 — Executing node sees plaintext in standard mode — Pass

Checked: docs/architecture/system-architecture.md §1 (summary bullet); docs/security/privacy-and-contexts.md §1 (first sentence); docs/security/threat-model.md §1; docs/faq.md (first answer); README.md (introduction and "Why"). All five state it.

### 2.4 Invariant 4 — Training, fine-tuning and federated learning only as non-goals — Pass

Checked by sweep over every file: every occurrence of "federated" or "fine-tun" is inside a non-goal statement, an out-of-scope note, or an evidence-register entry describing a third-party training project or a fine-tuned model in a cited paper (§2, §12).

### 2.5 Invariant 5 — Strict band ordering per tier, input and output separately; no wei floor adopted — Pass

Checked: docs/protocol/contracts-and-settlement.md §6 (`setBands`), §9; docs/economics/cost-and-pricing.md §6, §1; docs/adr/0005-hardware-classes-and-price-bands.md; docs/node/hardware-classes-and-benchmarks.md §3; docs/economics/pricing-examples.json (`bands-T1-illegal-M-quote`, `class-S-on-T4-band`, checked by scripts/check-pricing.py). Every wei figure is labeled FIXTURE / illustrative / derived-UNVERIFIED.

### 2.6 Invariant 6 — No slashing; disputes are reputation events; remedy is to stop signing; a signed voucher is not reversed — Pass

Checked: docs/adr/0004-sessions-vouchers-and-no-slashing.md; docs/protocol/contracts-and-settlement.md §8, §14; docs/security/inference-verification.md §4, §9, §10; docs/protocol/collective-answers.md §12; docs/glossary.md; docs/faq.md; pitch slide 10. The sweep found no sentence in which Comuns slashes anyone; the only "slashed" occurrences describe third-party networks in the evidence register and landscape.

### 2.7 Invariant 7 — No protocol token; protocol fee 0 — Pass

Checked: docs/adr/0007-no-protocol-token-in-v1.md; GOVERNANCE.md §1, §7; docs/protocol/contracts-and-settlement.md §2; docs/economics/cost-and-pricing.md §11; docs/project-charter.md 4.8; pitch slides 9 and 11. Every "protocol fee" occurrence says 0.

### 2.8 Invariant 8 — Apache-2.0 and DCO, no CLA — Pass

Checked: LICENSE (Apache-2.0 text, unchanged); docs/adr/0006-apache-2-0-and-dco.md; GOVERNANCE.md §1, §2.1; CONTRIBUTING.md §2; README.md; docs/project-plan.md §3, §7.

### 2.9 Invariant 9 — ETH formula with one floor division by 1000000, not L2 gas; sessions with chunked vouchers; two happy-path transactions; no finalize-at-posted-usage — Pass

Checked: docs/protocol/contracts-and-settlement.md §3, §8, §12, §14; docs/economics/cost-and-pricing.md §3, §4, §9; docs/project-charter.md 4.8; docs/glossary.md ("inference payment", "voucher"); docs/faq.md; scripts/check-pricing.py (`formula-*` and `session-*` fixtures). The formula appears identically everywhere; "finalize at posted usage" occurs only as the thing that is absent.

### 2.10 Invariant 10 — TOPLOC not claimed on llama.cpp or mistral.rs; verifiable mode opt-in and disclosed — Pass

Checked: docs/security/inference-verification.md §3, §5, §7; docs/node/node-design.md §4; docs/adr/0002; docs/adr/0003; docs/project-charter.md 4.7; docs/protocol/collective-answers.md §14; docs/faq.md. Every TOPLOC mention is a candidate on other engines or an explicit non-claim; every verifiable-mode statement says opt-in, user-chosen verifier, listed on the sheet.

### 2.11 Invariant 11 — Normative names — Pass (after edits)

Checked by sweep and reading: modes `standard`/`attested`/`verifiable`; `executionFeatures` with the five feature names and the empty set called single-node; "disclosure sheet" everywhere (one "disclosure table" in docs/project-plan.md §6 reworded to "the table generated from the disclosure sheet"); classes S/M/L/X; tiers T0–T4; the offer tuple `prices[modelId] = (priceInPerMillion, priceOutPerMillion, modelBenchmarkHash)`; `sessionSigner`, `CHUNK_TOKENS`, `closeWithVoucher`, `finalize`, the input voucher and the `final` flag in docs/glossary.md and docs/faq.md match docs/protocol/contracts-and-settlement.md. The EIP-712 type string occurs eleven times, all byte-identical. Role tokens: the two `"merge node"` values in the sheet JSON of docs/protocol/orchestration.md §13 and docs/protocol/off-chain-api.md §6.1 were changed to the canonical token `merge` (KI-5); docs/security/privacy-and-contexts.md §6 now names its list as the canonical tokens and §8.3 draws `roles[]` from it.

### 2.12 Invariant 12 — App-managed client keys; sign-to-derive only as a rejected default; deprecated wallet RPCs only in prohibitions; chain id UNVERIFIED — Pass

Checked: docs/security/privacy-and-contexts.md §5, §6, §11; docs/adr/0003; docs/product/dapp-and-sdk.md §2, §11; docs/protocol/off-chain-api.md §6 (the `42161` JSON values are followed by the UNVERIFIED note); docs/protocol/contracts-and-settlement.md §6.1, §8; docs/architecture/system-architecture.md §18. The sweep found no sign-to-derive or `eth_decrypt` mention outside a rejection or prohibition.

### 2.13 Invariant 13 — Links, headers, numbering; ADRs proposed; CIP-0001 Draft; MAINTAINERS seats nobody — Pass (after edits)

Checked: scripts/check-docs.py (links, header block, consecutive H2 numbering, Risks then Open questions, [RISK] marker, ADR structure, deck-14) passes on every file after this report was added and linked from README.md and docs/README.md; docs/protocol/off-chain-api.md §14 had its open questions numbered 1–6, 11, 7–10 and was renumbered 1–14 (with four new items). All nine ADRs carry `**Status:** proposed`; docs/cip/0001-adopt-baseline-adrs.md says `Status: Draft` and links ADRs 0001–0009; MAINTAINERS.md says "None seated."

### 2.14 Invariant 14 — Phase names identical in charter, plan, README and pitch — Pass (after edit)

Checked: README.md "Roadmap"; docs/project-plan.md §6 headings and §8 diagram; pitch/pitch-deck.md slide 12; docs/project-charter.md 4.11. The charter's Phase 4 name was "External review and a go/no-go CIP" while the other three say "External review"; the charter's name column now reads "External review" and the go/no-go CIP moved into its content column (4.18 "Phase names are unchanged" holds).

### 2.15 Invariant 15 — No automated-tool credit; no invented domain, subdomain, e-mail, grant, audit, partnership or calendar date — Pass

Checked by sweep: no file credits an automated writing or coding tool or its company as author or tool (the only matches are "OpenAI-compatible API", the open-weight model gpt-oss, and the evidence register's "AI-assisted hand-crafted WASM" in the Arbitrum pause notice, all allowed). Domains found: comuns.ai (the project domain), the sourced URLs of docs/evidence-register.md, RFC-reserved example hosts (`node.example.org`, `node-a.example`, `host.example`), and third-party project names recorded in the register (io.net, Vast.ai). No e-mail address anywhere. Dates: 2026-10-12 (document creation and snapshot), 2026-10-13 (fee snapshot and §9–§13 retrieval), 2026-10-02 (Stylus pause), 2026-09-23 and 2024-07-01 (evidence-register entries only). GOVERNANCE.md §10 and SECURITY.md §2 say no grant and no audit exist.

### 2.16 Invariant 16 — Numeric claims cite the register or are marked; 2026-10-13 fee figures are a snapshot; §9–§13 present and labeled retrieved 2026-10-13 — Pass

Checked: docs/evidence-register.md has H2 headings §1–§13 and "How to cite" (check-docs `evidence-sections`); its preamble and §14 state that §9–§13 were retrieved 2026-10-13; every 2026-10-13 occurrence in the sweep is labeled snapshot, dated or retrieved; docs/economics/cost-and-pricing.md labels every computed figure derived/UNVERIFIED; docs/protocol/contracts-and-settlement.md §3 tags each number [V] or [U].

### 2.17 Invariant 17 — Model-first pools — Pass (after edits)

Checked: docs/adr/0008-model-first-pools.md; docs/protocol/contracts-and-settlement.md §4, §5, §6 (`openSession` never compares class to tier, never reads `maxTier`), §9, §14; docs/node/model-registry-and-licenses.md §7; docs/node/hardware-classes-and-benchmarks.md §1, §3; docs/economics/cost-and-pricing.md §5; docs/product/dapp-and-sdk.md §2; docs/faq.md; docs/glossary.md ("pool"). No document states that a class may serve only certain tiers (the withdrawn rule is named only as withdrawn in the charter, ADR 0008 and CIP-0001); the phrase "cannot serve the tier" does not occur. Bands are stated for every (tier, class) pair over all four classes; no wei floor is adopted. Two definitions of `maxTier` as "the highest tier passed on the class benchmark" (contracts §5 Node record; charter 4.9) contradicted E1 and were replaced by "the largest tier the operator benchmarked, informational" (KI-10).

### 2.18 Invariant 18 — Single-node default; every multi-node feature and the orchestrator node opt-in and disclosed with reader counts; every participant reads what it receives; fail closed, no silent downgrade or unlisted fallback — Pass (after edits)

Checked: docs/security/privacy-and-contexts.md §1, §8.2, §8.3 (counts over full prompt, sub-task, other answers, activations, draft tokens; readers list as a floor; re-show, fail-closed and reuse rules; verifier on the sheet; entries per (node, modelId) session); docs/protocol/orchestration.md §1, §8, §13, §14; docs/protocol/collective-answers.md §13; docs/node/distributed-execution.md §5, §6, §8; docs/architecture/system-architecture.md §9, §15; docs/product/dapp-and-sdk.md §5, §8, §11; docs/adr/0009 (1), (4), (6); docs/project-charter.md 4.16; docs/security/threat-model.md T14, T19; docs/protocol/off-chain-api.md §10 (`unsupported_mode`, `pool_cannot_fill_confirmed_set`, `stale_disclosure_sheet`). The attested-mode quote binds the HPKE key hash plus a client nonce (privacy §8.1, inference-verification §6); `finalize` is refused before `closeDeadline` (contracts §6); shard holders are never paid through `SessionEscrow` (contracts §9 strengthened per KI-6, distributed-execution §5). The privacy document's two sentences that activations move "node to node" were aligned with the client-mediated spike data path (KI-8); the threat model's visibility row and T20 were aligned the same way.

### 2.19 Invariant 19 — Collective answers are a quality mechanism, never verification, mode 2, chain consensus or a payment consequence; parallel planning reuses it with an objection round and never auto-executes a rank — Pass (after edits)

Checked: docs/protocol/collective-answers.md §1, §4–§7, §10, §12, §14; docs/adr/0009 (3); docs/security/inference-verification.md §3, §7; docs/protocol/orchestration.md §10; docs/landscape.md §4; docs/glossary.md; docs/faq.md; pitch slide 10. The inconsistent scheduling of the two review passes (one job in §4 versus two in §5/§8) was repaired to two review jobs per reviewer, one per pass, sequential on that session (KI-16), and the matching sentence in docs/economics/cost-and-pricing.md §9 was aligned (the fixture arithmetic is unchanged).

### 2.20 Invariant 20 — Orchestrator in the client SDK by default; orchestrator nodes ordinary sessions, see the prompt only when planning is delegated, hold no `sessionSigner`, take no cut, never mandatory; the chain stores no plans, pool lists or sub-task assignments; one session per distinct (node, modelId); N sessions need N happy-path pairs; disagreement never reverses a voucher — Pass

Checked: docs/adr/0009 (2), (5), (6); docs/protocol/orchestration.md §1, §4, §8, §11, §12; docs/protocol/contracts-and-settlement.md §2, §9, §14; docs/economics/cost-and-pricing.md §9; docs/architecture/system-architecture.md §1, §4, §13; docs/project-charter.md 4.15, 4.17; docs/product/dapp-and-sdk.md §2, §3; docs/glossary.md ("orchestrator", "orchestrator node", "plan"). A request that reuses open sessions shows its own sheet and needs explicit confirmation (orchestration §8, privacy §8.3, charter 4.16); sheet entries are per (node, modelId) session (privacy §8.3, collective §12).

### 2.21 Invariant 21 — Sharding and cross-node speculation are experimental Phase 3 spikes, may end in a negative result, are not paid under mainnet parameters, never use llama.cpp RPC on an open network, treat activations as revealing the prompt (§10), promise no WAN speed-up (§9), and speculation is incompatible with verifiable mode and undetectable by TOPLOC — Pass (after edits)

Checked: docs/node/distributed-execution.md throughout; docs/adr/0009 (7); docs/protocol/contracts-and-settlement.md §9, §14; docs/security/privacy-and-contexts.md §8.1, §8.2, §11; docs/security/threat-model.md T20, T21; docs/security/inference-verification.md §3, §5, §9; docs/economics/cost-and-pricing.md §9; docs/node/node-design.md §3, §6; docs/project-charter.md 4.14, 4.18; docs/project-plan.md §6 Phase 3; docs/risk-register.md RR-21, RR-22, RR-36; README.md; pitch slide 12. One contradiction was repaired: contracts §9 and cost-and-pricing §9 said the target node's session bills "the accepted output the user receives", while E46 and distributed-execution §8 bill the target for the drafted tokens it scores (at most `MAX_DRAFT_TOKENS` per round); both now say the latter. The status line and the defect list required by KI-15 were added to distributed-execution.

### 2.22 Invariant 22 — ADR 0008 and 0009 proposed; CIP 0001 Draft and links all nine ADRs; charter map, README map and docs index list the five new paths; phase names unchanged; deck has exactly 14 slides — Pass

Checked: docs/adr/0008-model-first-pools.md and docs/adr/0009-opt-in-client-orchestration.md (`**Status:** proposed`); docs/cip/0001-adopt-baseline-adrs.md (`Status: Draft`, nine ADR links in Specification); docs/project-charter.md §5, README.md document map and docs/README.md §2 list docs/protocol/orchestration.md, docs/protocol/collective-answers.md, docs/node/distributed-execution.md, docs/adr/0008-model-first-pools.md and docs/adr/0009-opt-in-client-orchestration.md; pitch/pitch-deck.md has 14 `## ` headings and pitch/pitch-deck.html 14 `<section class="slide"` elements (check-docs `deck-14` passes; scripts/check-deck.py counts the same).

## 3. Scenario traces

Each row names where the scenario is specified, then the consent and cap checks that were traced through those sections rather than keyword-matched.

| Scenario | Documents and sections | Consent and cap conservation as traced |
|---|---|---|
| Happy session | contracts §8 (signing cadence), §12 (happy path), §7 (invariants); off-chain-api §5 (handshake, on-chain prices win), §8 (input receipt, input voucher, chunk receipts, cumulative vouchers); privacy §3 (diagram), §6, §10; node-design §6; system-architecture §7; dapp-and-sdk §4 (screens 7–10, 13); cost-and-pricing §9 (`session-two-prompts-partial-chunks`) | Sheet v1 shown and confirmed before `openSession`; `requestId` and `sheetVersion` bound into every AAD (privacy §8.3, off-chain §6). Effective cap = min(depositWei, maxSpendWei); the client never signs above it (off-chain §8); `closeWithVoucher` computes payout = min(cumulativeWei, cap) − settledWei, raises settledWei by that payout and credits it to the node, and only then credits refund = depositWei − settledWei (the updated value) to the user, so node credits + refund = depositWei (contracts §6, §7; check-pricing `session-*` fixtures apply the same order and assert the sum). |
| User abandons mid-stream | contracts §6 notes (abandoned-client procedure), §12; threat-model T4, T30; privacy §10; off-chain-api §3 (`reconnectWindow`), §11; node-design §6; FAQ ("close my laptop"); ADR 0004 | No new consent needed; the node redeems its highest non-`final` voucher while legal, then `closeSession`, then `finalize` after `closeDeadline`. Node credit ≤ the last signed voucher ≤ cap; `finalize` credits depositWei − settledWei to the user; the unacknowledged chunk is unpaid (one-chunk exposure). |
| Node offline mid-stream | contracts §12 ("Node goes offline"); off-chain-api §7 (truncation), §11 (retry on a different node needs a new session); system-architecture §15; dapp-and-sdk §8; threat-model T4, T12; node-design §6 | The client marks the answer truncated after 2 × `maxInterFrameMs`, reconnects for `reconnectWindow`, then closes cooperatively if the node returns or unilaterally (`closeSession`, `finalize`). The node may still `redeemVoucher` while legal; the user never owes more than the signed total; a retry elsewhere is a new session under a sheet that already lists that node or a new sheet version. |
| Sequencer down for a day | contracts §7 (timing), §12 ("Sequencer down for a day"), R2, §16 q2; threat-model T5, R8; system-architecture §15; deployment §5; cost-and-pricing R9; ADR 0001, ADR 0004; FAQ | Vouchers continue off-chain; the node submits through the delayed inbox (force inclusion after about one day, evidence register §1 [V]). `CLOSE_WINDOW` must exceed an outage plus about one day; an outage shortly before `closeDeadline` can still cost the node its unredeemed vouchers — stated as a residual risk, never a guarantee. The user loses nothing: `finalize` credits whatever was not redeemed. |
| Required attested mode, no eligible node | privacy §8.1 (fail-closed bullet), §8.3 (fail-closed rule); inference-verification §6 item 5; off-chain-api §10 (`unsupported_mode`, `attestation_failed`); system-architecture §9, §15; dapp-and-sdk §8; orchestration §13, §15; ADR 0003 | The request fails closed before any envelope is sealed; the client never downgrades to standard mode silently. Funds: none if no session was opened; otherwise the client calls `closeSession`, the deposit stays escrowed for the close window, and `finalize` — callable only once `closeDeadline` has passed (contracts §6) — credits it to `balances[user]`; no job was sent, so only L2 gas is spent and the user then calls `withdraw()`. |
| Collective answer, one of three answerers disagrees | collective-answers §4 (roles, rounds), §5 (stable IDs A1…Ak, two review jobs per reviewer), §6 (synthesis with a non-empty `splits[]`), §7 ("contested" label), §12 (vouchers stand, no payment consequence), §13 (sheet before any session); privacy §8.2, §8.3; cost-and-pricing §9 (`collective-answer-three-answerers`: seven sessions, caps summing to 5,200 wei within the combined cap); system-architecture §15 (contested row); dapp-and-sdk screen 11; inference-verification §9 | Sheet lists every (node, modelId) session — three answerers, the reviewers, the synthesizer — with roles, receives, prices and caps; confirmed before the `openSession` calls, then re-read prices on-chain. Three answer sessions plus review and synthesis sessions each run their own receipts and vouchers; the synthesis returns `merged`, a non-empty `splits` list and an agreement level; the client labels the result contested and offers the originals; every signed voucher stands, and `totalCapWei` is the sum of the per-session caps, each session paid at most its own cap. |
| Decomposed plan, one sub-task node offline mid-wave | orchestration §8 (failures), §12 (a retried task pays both), §14 (node offline, lost voucher log rows); off-chain-api §11 (retry on a different node needs a new session, pre-confirmed fallback); system-architecture §15 (sub-task node offline row); dapp-and-sdk §8; cost-and-pricing §9 (combined-cap partition: settled + outstanding signed liabilities + unspent reservations ≤ B; an abandoned session keeps its reservation until settlement is known); privacy §8.3 (fail-closed rule) | Retry only on a node that was on the confirmed sheet, with a new session; a node not on the sheet means a new sheet version and a new confirmation. Signed vouchers on the failed session stand and stay counted as liabilities; the failed session is closed unilaterally (`closeSession`, `finalize`); the fallback session's cap is reserved inside the combined cap, and a retry that would breach the bound needs a new sheet and signature. |
| Confirmed pool cannot be filled | privacy §8.3 (fail-closed rule); orchestration §14 (pool cannot fill the confirmed set), R7; off-chain-api §10 (`pool_cannot_fill_confirmed_set`); collective-answers §9 item 4, §12 (abandoned answerer); system-architecture §15; dapp-and-sdk §8; threat-model T14; charter 4.16; ADR 0009 (4) | The whole request fails closed; no job is sent and no node outside the confirmed sheet is substituted. Because no job is sent, no node has delivered paid work for this request: each session already opened is closed with `closeSession`, its deposit stays escrowed for the close window, and `finalize` after `closeDeadline` credits the whole deposit to `balances[user]`; only L2 gas is spent. (A session reused from an earlier request keeps that request's signed vouchers, which pay the node only if redeemed before `closeDeadline`; contracts §6–§8.) |

Consent validity, end to end: the sheet's `version` is confirmed by the user (privacy §8.3), bound into every envelope's AAD as `sheetVersion` with `requestId` (privacy §6, off-chain §6), checked by the client before any dispatch (`stale_disclosure_sheet`, off-chain §10; dapp `run` refuses without a recorded confirmation), re-versioned on any change of node, model, data scope, price, cap or reader set and for every new session (orchestration §13, §14; collective §13; ADR 0009 (4)), and never carried over from an earlier request or a funded session (charter 4.16). Cap conservation, end to end: per session the contract credits node + user = depositWei exactly (contracts §7, tested in check-pricing); across a request the client keeps settled spend + outstanding signed liabilities + unspent reservations within the confirmed combined cap and shows L2 gas separately (cost-and-pricing §9, orchestration §12, dapp §6).

## 4. Edits made

Pitch files were not edited. Every edit below repairs a contradiction against the invariants or a decision, fixes a link, header or numbering, records a known issue carried forward, or makes a check pass.

- docs/protocol/contracts-and-settlement.md — §4 tier table rewritten as the E2 partition ("> 4B and ≤ 8B" etc.); §5 `maxTier` redefined per E1 (largest tier benchmarked, informational); §9 Phase 3 paragraph: shard holders hold no session and the reference client never opens one or signs a voucher for one (KI-6), target node billed for drafted tokens it scores (E46); §16 open questions 17–19 added (key swap in flight KI-2, proof of possession KI-3, `BandsSet` `initialized` bit KI-4).
- docs/project-charter.md — 4.9 tier predicates as the E2 partition and `maxTier` per E1 (KI-10); 4.11 Phase 4 name "External review" (invariant 14); 4.16 role list uses the canonical tokens (KI-5).
- docs/security/privacy-and-contexts.md — §5 node-key sentence aligned with contracts §9 and the in-flight key swap named (KI-2); §6 AAD `role` row names the canonical token list (KI-5); §6 response frames state E16 (receipts inside the sealed frame, keyed hashes outside) (KI-7); §6 and §8.2 sharding sentences aligned with the client-mediated data path (KI-8, KI-18); §8.3 `roles[]` drawn from the canonical tokens (KI-5); §11 forbidden list reworded for the client-mediated path; §14 open questions 11 (key swap) and 12 (non-session readers, KI-19) added.
- docs/security/threat-model.md — §5 activations row and T20 response aligned with the client-mediated spike data path.
- docs/protocol/orchestration.md — §4 sheet `roles[]` vocabulary statement; §13 table and JSON `"merge node"` → `merge` (KI-5).
- docs/protocol/off-chain-api.md — §6.1 sheet JSON `"merge node"` → `merge` (KI-5); §14 open questions renumbered 1–14 (item 11 was out of order), question 5 extended (KI-11), questions 12 (KI-12), 13 (KI-13) and 14 (round frame and timer name, KI-9) added.
- docs/protocol/collective-answers.md — §4, §5, §8, §12: two review jobs per reviewer, one per pass, sequential on the session (KI-16); §13: no activations move, and the spike's activations go from the client to each holder (KI-18).
- docs/economics/cost-and-pricing.md — §9: reviewer sessions run two cross-check jobs (KI-16, arithmetic unchanged); target node billed for drafted tokens scored (E46).
- docs/node/distributed-execution.md — status line "Phase 3 spike sketch with known defects — not a specification" after the header; open question 1 no longer refers to the (now repaired) privacy sentence; open question 11 lists defects (a)–(g) (KI-15).
- docs/architecture/deployment-and-decentralization.md — §3 Phase 0 exit includes the Final bootstrap seating CIP; Phase 4 row no longer seats maintainers; §4 bootstrap-maintainers row aligned with GOVERNANCE.md §6 and SECURITY.md §3 (KI-20).
- docs/project-plan.md — §6 Phase 0 exit includes the Final bootstrap seating CIP (KI-20); §6 Phase 2 "disclosure table" → table generated from the disclosure sheet (invariant 11); §9 Documentation-baseline milestone row aligned.
- docs/cip/README.md — §5 merge rule refers to the currently seated maintainers per MAINTAINERS.md and GOVERNANCE.md §6.1 (KI-1).
- docs/node/node-design.md — §13 open question 11 (session store kept until settlement is final under a confirmation policy, KI-17).
- docs/product/dapp-and-sdk.md — §13 open question 8 (`SessionMap` maps a pair to a list of session ids, KI-14).
- README.md — document map links docs/review-report.md.
- docs/README.md — reading order and complete map link docs/review-report.md with its title.
- docs/review-report.md — this report (new file).

Not edited, by rule: LICENSE, MAINTAINERS.md, GOVERNANCE.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, docs/evidence-register.md, docs/requirements.md, docs/risk-register.md, docs/glossary.md, docs/faq.md, docs/landscape.md, docs/architecture/system-architecture.md, docs/security/inference-verification.md, docs/node/hardware-classes-and-benchmarks.md, docs/node/model-registry-and-licenses.md, docs/economics/pricing-examples.json, all nine ADRs, docs/adr/README.md, docs/cip/0000-template.md, docs/cip/0001-adopt-baseline-adrs.md, the three scripts, pitch/pitch-deck.md, pitch/pitch-deck.html.

## 5. Residual conflicts

Each of these was left as found because repairing it would have meant choosing a design the decisions do not state, or because the review scope says to record rather than repair.

1. docs/security/privacy-and-contexts.md §5, docs/security/threat-model.md T7 and docs/node/node-design.md §7 describe node registration as carrying a proof of possession of the HPKE private key, while `registerNode` and `updateNode` in docs/protocol/contracts-and-settlement.md §6 take plain `hpkePublicKey` bytes. Recorded as contracts open question 18 (KI-3); the sentences were not changed because the proof's form and location are undecided. This is a release blocker for any implementation.
2. docs/protocol/off-chain-api.md §7 still says a client "signs nothing further for the job" after a truncation, which read literally stalls a resumed job; recorded as its open question 12 (KI-12) rather than rewritten, because the review scope asked for a record.
3. docs/protocol/off-chain-api.md §9 still has the inline retry after `blob_url_refused` reuse the job; recorded as its open question 13 (KI-13).
4. docs/architecture/deployment-and-decentralization.md §1 and §3 label the last stage "Phase 4 — External review and a go/no-go CIP"; the four files named by invariant 14 (charter, plan, README, pitch) now agree on "External review", and the deployment label was left as a description of the stage. Repaired after the review: the deployment document and docs/requirements.md now use "External review" as the name.
5. docs/cip/README.md §1 and GOVERNANCE.md §4.5 still describe docs/cip/0001-adopt-baseline-adrs.md as possibly missing; the file exists, the wording is hedged, and GOVERNANCE.md is outside the repair scope of this review. Repaired after the review: docs/cip/README.md now says CIP-0001 is a Draft and is not Final, and GOVERNANCE.md §1 states plainly that the license text is in LICENSE.
6. Descriptive role names ("merge node", "orchestrator node", "draft node") remain in prose tables (threat-model §5 column heading, system-architecture §4, charter 4.16's surrounding text); only JSON `roles[]` values and the AAD token list were normalized to the canonical tokens, which is what E26 and KI-5 require.
7. docs/security/privacy-and-contexts.md §8.3 still has one `recipients[]` entry per session, so the sharding spike cannot list shard holders on the sheet; recorded as its open question 12, RR-38 and the project plan already block the spike on a CIP (KI-19).

## 6. Handoff to the pitch deck

No sentence of pitch/pitch-deck.md or pitch/pitch-deck.html contradicts the invariants. The following omissions are recorded for the pitch deck update to weigh; none was edited here.

1. Slide 10 describes verifiable mode as opt-in re-execution by a second user-chosen node but omits that it runs under a demonstrated deterministic profile, that the session mode is public on-chain, and that a mismatch has no payment consequence.
2. Slide 7 says the client states "how many nodes see the full prompt, a sub-task, activations or draft tokens" but does not say the count is by distinct node and distinct operator, or that the reader list is a floor derived from the actual payloads.
3. Slide 12 names the two Phase 3 spikes as experiments and says no speed-up over the internet is promised, but does not say they run only with testnet-only, non-normative prices, that the reference client refuses both under mainnet parameters, or that shard holders hold no session and are not paid.
4. Slide 10 says a collective answer "is not verification" but not that it never has a payment consequence; parallel planning is not named anywhere in the deck (slide 4 mentions planning a DAG only).
5. Slide 5 says "Memory decides, not class"; the documents say memory fit plus the per-model self-benchmark are the node's own admission decision, and that a self-benchmark is a signed claim, not an unfakeable proof (slide 13 says the latter).
6. The term "disclosure sheet" appears only in speaker notes (slide 7), never in a slide body.
7. Slide 12 lists Phase 4 as "External review", which now matches the charter, plan and README.

## 7. Check output

Commands run from the worktree root after the last edit.

`python3 scripts/check-pricing.py` — exit code 0:

```text
PASS formula-exact
PASS formula-zero-output
PASS formula-floor-remainder
PASS session-two-prompts-partial-chunks
PASS session-over-cap
PASS bands-T1-illegal-M-quote
PASS class-S-on-T4-band
PASS operator-4090-owned-electricity-only
PASS operator-H100-rented-single-stream
PASS operator-H100-rented-batched
PASS operator-H100-rented-half-utilization
PASS collective-answer-three-answerers
PASS session-L2-amortization-illustration
```

`python3 scripts/check-docs.py` — exit code 0; one PASS line per file, ending:

```text
PASS .:1 summary: 319 checks, 0 failures
```

Before this review the same command exited 1 with one failure: `FAIL docs/project-plan.md:97 links: missing file: review-report.md`, which this report resolves.

## 8. Verification limits

- The Mermaid check in scripts/check-docs.py is structural only (fence tag and first declaration); no diagram was rendered, and this review checked diagrams by reading them.
- scripts/check-pricing.py is a documentation calculator over the non-normative fixtures in docs/economics/pricing-examples.json; it is not an audit, not an implementation of the contracts, and it adopts no price.
- LICENSE is GitHub's canonical Apache-2.0 text as carried on the main branch; it was read (header, definitions and the closing appendix match the Apache-2.0 text) and not edited. A byte-for-byte comparison against an external canonical copy was not performed, because no network access was used.
- No contract, node or client code exists; every statement about behaviour is a reading of the documents, and nothing here claims that any check would pass against an implementation.
- The text sweep looked for forbidden and required phrases; it cannot detect a contradiction expressed in different words, so the invariant results rest on the reading recorded in section 2 as much as on the sweep.
- The pitch files were read in Markdown and as extracted HTML text; the HTML was not rendered and scripts/check-deck.py's Chrome-dependent checks were not run.

## 9. Open questions

1. Whether `openSession` should bind the expected `hpkePublicKey` hash (or a whole-offer hash) so that a same-price key or endpoint swap in flight reverts the open (contracts §16 questions 8 and 17; privacy §14 question 11).
2. The form and location of the proof of possession for `hpkePublicKey` at registration (contracts §16 question 18; privacy §14 question 6).
3. Whether `BandsSet` should omit the `initialized` bit or the contract should force it true before emitting (contracts §16 question 19).
4. The disclosure-sheet extension for non-session readers that the sharding spike needs (privacy §14 question 12; RR-38).
5. Whether chunk tokens should travel as token IDs inside the sealed frame, or a bounded tokenizer tolerance should apply (off-chain-api §14 question 5).
6. The spike-only round frame kind, and whether the client's inter-frame timer should carry the capability field's name (off-chain-api §14 question 14).
7. Whether the deployment document's stage label "External review and a go/no-go CIP" should be shortened to the charter's phase name. Repaired after the review: docs/architecture/deployment-and-decentralization.md and docs/requirements.md now use "External review" as the phase name.
8. Whether docs/cip/README.md §1 and GOVERNANCE.md §4.5 should drop the "possibly missing" wording now that docs/cip/0001-adopt-baseline-adrs.md exists. Repaired after the review: docs/cip/README.md no longer carries it.
9. Whether descriptive role names in prose tables should also be replaced by the canonical tokens, beyond the JSON values and the AAD list normalized here.
10. Whether a byte-for-byte comparison of LICENSE against an external canonical Apache-2.0 copy should be added to a later check.

## 10. Known issues carried forward

Status of every item from the cross-vendor reviews, as the review scope requires.

| Item | Status |
|---|---|
| KI-1 | Repaired in docs/cip/README.md §5 (merge authority follows the currently seated maintainers per MAINTAINERS.md and GOVERNANCE.md §6.1). |
| KI-2 | Repaired in docs/security/privacy-and-contexts.md §5 (key read from the latest `NodeRegistered` / `NodeUpdated` event, as contracts §9); the openSession key binding is recorded as an open question in docs/protocol/contracts-and-settlement.md §16 (question 17) and docs/security/privacy-and-contexts.md §14 (question 11). |
| KI-3 | Recorded as an open question in docs/protocol/contracts-and-settlement.md §16 (question 18); release blocker for any implementation. |
| KI-4 | Recorded as an open question in docs/protocol/contracts-and-settlement.md §16 (question 19). |
| KI-5 | Repaired: canonical token list named in docs/security/privacy-and-contexts.md §6 and reused in §8.3, docs/protocol/orchestration.md §4 and §13, docs/protocol/off-chain-api.md §6.1 and docs/project-charter.md 4.16. |
| KI-6 | Repaired in docs/protocol/contracts-and-settlement.md §9 (shard holders hold no session; the reference client never opens a session or signs a voucher for one); docs/node/distributed-execution.md §5 already states it. |
| KI-7 | Repaired in docs/security/privacy-and-contexts.md §6 (E16 stated; §10 refers to §6). |
| KI-8 | Repaired in docs/security/privacy-and-contexts.md §6 and §8.2 (client-mediated data path, mutual TLS bound to operator keys). |
| KI-9 | Recorded as an open question in docs/protocol/off-chain-api.md §14 (question 14): the round frame is undefined and the timer name is checked against `maxInterFrameMs`. |
| KI-10 | Repaired in docs/project-charter.md 4.9 (and the same definition in docs/protocol/contracts-and-settlement.md §5). |
| KI-11 | Recorded as an open question in docs/protocol/off-chain-api.md §14 (question 5, extended). |
| KI-12 | Recorded as an open question in docs/protocol/off-chain-api.md §14 (question 12). |
| KI-13 | Recorded as an open question in docs/protocol/off-chain-api.md §14 (question 13). |
| KI-14 | Recorded as an open question in docs/product/dapp-and-sdk.md §13 (question 8). |
| KI-15 | Repaired in docs/node/distributed-execution.md (status line after the header; defects (a)–(g) in §13 question 11; no redesign). |
| KI-16 | Repaired in docs/protocol/collective-answers.md §4, §5, §8 and §12 (two review jobs per reviewer, sequential on the session), with docs/economics/cost-and-pricing.md §9 aligned. |
| KI-17 | Recorded as an open question in docs/node/node-design.md §13 (question 11). |
| KI-18 | Repaired in docs/security/privacy-and-contexts.md §6 and §8.2 and docs/protocol/collective-answers.md §13 (and the threat model's §5 row and T20). |
| KI-19 | Recorded as an open question in docs/security/privacy-and-contexts.md §14 (question 12); the project plan and RR-38 already block the spike on it. |
| KI-20 | Repaired in docs/architecture/deployment-and-decentralization.md §3 and §4 and docs/project-plan.md §6 and §9 (the bootstrap seating CIP is a Phase 0 exit item, before any merge or release, per GOVERNANCE.md §6 and SECURITY.md §3). |
