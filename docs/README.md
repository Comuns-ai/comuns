# Documentation index

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** README.md

---

## 1. Reading order

This is a draft community proposal; no protocol implementation runs yet; documentation checker scripts are included. Paths in the table are relative to the repository root, while link destinations are relative to this index. Read in this order, then use the table for the complete document map.

1. [Repository introduction](../README.md), [Markdown pitch](../pitch/pitch-deck.md) and [printable pitch](../pitch/pitch-deck.html) — purpose and status.
2. [Charter](project-charter.md), [evidence register](evidence-register.md) and [requirements](requirements.md) — proposed scope, evidence and traceability.
3. [Governance](../GOVERNANCE.md), [contributing](../CONTRIBUTING.md), [CIP process](cip/README.md), [baseline adoption CIP](cip/0001-adopt-baseline-adrs.md) (CIP-0001, Draft) and [bootstrap CIP](cip/0003-bootstrap-first-maintainer-and-channels.md) (CIP-0003, Draft; seats nobody today) — how the community changes the proposal.
4. [System architecture](architecture/system-architecture.md), [deployment](architecture/deployment-and-decentralization.md) and [project plan](project-plan.md) — boundaries and phase gates.
5. [Contracts and settlement](protocol/contracts-and-settlement.md), [off-chain API](protocol/off-chain-api.md) and [privacy and contexts](security/privacy-and-contexts.md) — credit-funded settlement, anonymous transport, authenticated jobs and readers. See proposed [ADR 0010](adr/0010-anonymous-by-default.md), [ADR 0011](adr/0011-anonymous-credits.md) and [ADR 0012](adr/0012-contexts-without-a-wallet-link.md).
6. [Node design](node/node-design.md), [benchmarks](node/hardware-classes-and-benchmarks.md), [model registry](node/model-registry-and-licenses.md), [pricing](economics/cost-and-pricing.md) and [model-first pools ADR](adr/0008-model-first-pools.md) — model offers, hardware and costs.
7. [Orchestration](protocol/orchestration.md), [collective answers](protocol/collective-answers.md), [distributed execution](node/distributed-execution.md) and [opt-in orchestration ADR](adr/0009-opt-in-client-orchestration.md) — client plans and parallel sub-tasks, answers with disagreements, and experimental testnet-only sharding and speculation.
8. [Dapp and SDK](product/dapp-and-sdk.md), [threat model](security/threat-model.md), [inference verification](security/inference-verification.md), [risk register](risk-register.md) and [ADR index](adr/README.md) — user flow, limits and decision rationale.
9. [Glossary](glossary.md), [FAQ](faq.md), [landscape](landscape.md) and the [review report](review-report.md) — companion references and the consistency pass over the set.

pitch/pitch-deck.html is the printable form of the Markdown deck.

## 2. Complete map

Categories below describe the document or artifact. Companion titles and categories are descriptive index labels, pending those documents' review.

| Path | Title | Category | One-line summary |
|---|---|---|---|
| [README.md](../README.md) | Comuns | Index | Entry point for the repository. |
| [LICENSE](../LICENSE) | Apache-2.0 license | License | Apache-2.0 license text. |
| [GOVERNANCE.md](../GOVERNANCE.md) | Governance — how Comuns changes | Decision | CIP process, working groups, decision rules. |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contributing | Process | How to contribute; DCO sign-off. |
| [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Code of conduct | Decision | Community conduct rules. |
| [SECURITY.md](../SECURITY.md) | Security policy | Decision | How to report vulnerabilities. |
| [MAINTAINERS.md](../MAINTAINERS.md) | Maintainers | Index | Maintainer roles (none seated). |
| [docs/README.md](README.md) | Documentation index | Analysis | Index of the documentation. |
| [docs/project-charter.md](project-charter.md) | Comuns — Project charter | Technical Proposal | This charter. |
| [docs/evidence-register.md](evidence-register.md) | Comuns — Evidence register | Analysis | External facts with marks [V]/[L]/[U]. |
| [docs/requirements.md](requirements.md) | Comuns — Requirements traceability | Technical Proposal | Requirements traceability. |
| [docs/project-plan.md](project-plan.md) | Project plan — build Comuns in the open | Technical Proposal | Phases 0–4 and their exit criteria. |
| [docs/risk-register.md](risk-register.md) | Risk register — consolidated | Analysis | Consolidated risks. |
| [docs/glossary.md](glossary.md) | Glossary | Analysis | Terms. |
| [docs/faq.md](faq.md) | Frequently asked questions | Analysis | Frequently asked questions. |
| [docs/landscape.md](landscape.md) | Landscape | Analysis | Comparison with other networks. |
| [docs/review-report.md](review-report.md) | Review report — consistency pass | Analysis | Review of the document set: invariants, scenario traces, edits and handoffs. |
| [docs/architecture/system-architecture.md](architecture/system-architecture.md) | System architecture — decentralized LLM inference on Arbitrum One | Technical Proposal | Components and flows. |
| [docs/architecture/deployment-and-decentralization.md](architecture/deployment-and-decentralization.md) | Deployment and decentralization — stages, dependencies and what stays central | Technical Proposal | Deployment and decentralization limits. |
| [docs/deployments/arbitrum-sepolia.md](deployments/arbitrum-sepolia.md) | Arbitrum Sepolia deployment record (testnet-only, non-normative) | Record | Unfilled record for deployment observations after CIP-0004 is Final; no deployment claimed. |
| [docs/protocol/contracts-and-settlement.md](protocol/contracts-and-settlement.md) | Contracts and settlement — sessions, vouchers and registries on Arbitrum One | Technical Proposal | Registries, cumulative vouchers and ETH credits claimed through withdraw(). |
| [docs/protocol/off-chain-api.md](protocol/off-chain-api.md) | Off-chain API — encrypted jobs, streaming frames and vouchers | Technical Proposal | Client–node API. |
| [docs/protocol/orchestration.md](protocol/orchestration.md) | Orchestration — assess, plan with parallelism in mind, execute in waves, merge | Technical Proposal | Opt-in client planning, parallel sub-tasks across model pools, waves and confirmed reader disclosure. |
| [docs/protocol/collective-answers.md](protocol/collective-answers.md) | Collective answers — several nodes answer, cross-check blind, one synthesis | Technical Proposal | Opt-in answers and cross-checks with visible disagreements, plus parallel planning; neither is verification. |
| [docs/security/privacy-and-contexts.md](security/privacy-and-contexts.md) | Privacy and contexts — anonymous by default, two content tiers | Technical Proposal | Anonymous relay transport, two content tiers, context-key grants and backup limits. |
| [docs/security/threat-model.md](security/threat-model.md) | Threat model — prompts, contexts and escrow | Analysis | Threats and mitigations. |
| [docs/security/inference-verification.md](security/inference-verification.md) | Inference verification — what can be checked, at what privacy cost | Technical Proposal | Opt-in re-execution by a user-chosen second node under a demonstrated deterministic profile. |
| [docs/economics/cost-and-pricing.md](economics/cost-and-pricing.md) | Cost and pricing — hardware classes, bands and the session economy | Technical Proposal | Separate hardware classes and model tiers, ordered price bands and session costs. |
| [docs/economics/pricing-examples.json](economics/pricing-examples.json) | Pricing examples | Fixture | Non-normative pricing fixtures. |
| [docs/node/node-design.md](node/node-design.md) | Node — a Rust inference server | Technical Proposal | Rust node design. |
| [docs/node/hardware-classes-and-benchmarks.md](node/hardware-classes-and-benchmarks.md) | Hardware classes and benchmarks — who can run what | Technical Proposal | Classes and self-benchmarks. |
| [docs/node/model-registry-and-licenses.md](node/model-registry-and-licenses.md) | Model registry — manifests, tiers and licenses | Technical Proposal | ModelRegistry and model licenses. |
| [docs/node/distributed-execution.md](node/distributed-execution.md) | Distributed execution — sharding one model and speculative decoding across tiers | Technical Proposal | Experimental Phase 3 testnet-only sharding and cross-node speculation; no WAN speed-up is promised. |
| [docs/product/dapp-and-sdk.md](product/dapp-and-sdk.md) | Dapps and SDK — chat on top of the session protocol | Technical Proposal | Reference dapp and client SDK. |
| [docs/adr/README.md](adr/README.md) | ADR index | Index | ADR index. |
| [docs/adr/0001-settle-on-arbitrum-one-evm-not-stylus.md](adr/0001-settle-on-arbitrum-one-evm-not-stylus.md) | ADR 0001: Settle on Arbitrum One with EVM contracts, not Stylus | Decision | Proposed Arbitrum One settlement with EVM contracts. |
| [docs/adr/0002-off-chain-rust-inference.md](adr/0002-off-chain-rust-inference.md) | ADR 0002: Run inference off-chain in a Rust node with pluggable backends | Decision | Proposed off-chain Rust nodes with pluggable inference backends. |
| [docs/adr/0003-hpke-and-the-executor-plaintext-limit.md](adr/0003-hpke-and-the-executor-plaintext-limit.md) | ADR 0003: Encrypt both ways with HPKE and state who can still read | Decision | Proposed two-way HPKE; superseded in part by ADR 0010–0012 on anonymity, execution and context identity. |
| [docs/adr/0004-sessions-vouchers-and-no-slashing.md](adr/0004-sessions-vouchers-and-no-slashing.md) | ADR 0004: Settle with session escrow and chunked vouchers, with no slashing in v1 | Decision | Proposed ETH escrow, cumulative vouchers, pull payments and no v1 slashing. |
| [docs/adr/0005-hardware-classes-and-price-bands.md](adr/0005-hardware-classes-and-price-bands.md) | ADR 0005: Charge more for higher hardware classes through ordered bands | Decision | Proposed ordered price bands across hardware classes. |
| [docs/adr/0006-apache-2-0-and-dco.md](adr/0006-apache-2-0-and-dco.md) | ADR 0006: License the work Apache-2.0 and use the DCO | Decision | Proposed Apache-2.0 licensing and DCO contribution certification. |
| [docs/adr/0007-no-protocol-token-in-v1.md](adr/0007-no-protocol-token-in-v1.md) | ADR 0007: Do not issue a protocol token in v1 | Decision | Proposed ETH payments and no protocol token in v1. |
| [docs/adr/0008-model-first-pools.md](adr/0008-model-first-pools.md) | ADR 0008: Model-first pools, not a class-tier serving gate | Decision | Proposed model-first pools: any node may offer a registered model it can load; classes select price bands. |
| [docs/adr/0009-opt-in-client-orchestration.md](adr/0009-opt-in-client-orchestration.md) | ADR 0009: Opt-in client orchestration, collective answers and experimental parallelism | Decision | Proposed single-node default, opt-in client orchestration and optional credit-session orchestrator nodes. |
| [docs/adr/0010-anonymous-by-default.md](adr/0010-anonymous-by-default.md) | ADR 0010: Anonymous by default: relays, unlinkable sessions and two content tiers | Decision | Proposed anonymous default and relay transport. |
| [docs/adr/0011-anonymous-credits.md](adr/0011-anonymous-credits.md) | ADR 0011: Anonymous credits: Semaphore groups inside SessionEscrow | Decision | Proposed anonymous credits and the amended 23-function list. |
| [docs/adr/0012-contexts-without-a-wallet-link.md](adr/0012-contexts-without-a-wallet-link.md) | ADR 0012: Contexts without a wallet link | Decision | Proposed context-key identity and optional public anchors. |
| [docs/adr/0013-repositories-toolchains-ci-and-releases.md](adr/0013-repositories-toolchains-ci-and-releases.md) | ADR 0013: Repositories, toolchains, CI, DCO enforcement, code style and releases up to testnet | Decision | Proposed repository layout, toolchains, CI, DCO, style and testnet release gates; adoption proposed in CIP-0005. |
| [docs/adr/0014-relay-authentication-to-gateways.md](adr/0014-relay-authentication-to-gateways.md) | ADR 0014: Relay authentication to gateways | Decision | Proposed relay authentication per connection without a contract change; adoption proposed in CIP-0005. |
| [docs/adr/0015-node-key-possession.md](adr/0015-node-key-possession.md) | ADR 0015: Prove possession of node keys to the client, not to the contract | Decision | Proposed client key-possession probe before spending, without a contract change; adoption proposed in CIP-0005. |
| [docs/adr/0016-funding-edge-and-deposit-key.md](adr/0016-funding-edge-and-deposit-key.md) | ADR 0016: Fund notes at the edge and keep the escrow in ETH | Decision | Proposed ETH-only escrow with funding at the edge from the user's own account and a deposit key that can only call depositNote; no adopting CIP yet. |
| [docs/adr/0017-accounts-and-decentralized-access.md](adr/0017-accounts-and-decentralized-access.md) | ADR 0017: Accounts, an independent note vault and decentralized access | Decision | Proposed core path with no hosted service, optional embedded wallets and social login, an independent note vault and an isolated funding surface; no adopting CIP yet. |
| [docs/adr/0018-one-client-stack.md](adr/0018-one-client-stack.md) | ADR 0018: One client stack for web, desktop and mobile | Decision | Proposed one TypeScript-over-Rust client stack for web, desktop and mobile; prover and store facts recorded, nothing selected; no adopting CIP yet. |
| [docs/cip/README.md](cip/README.md) | CIPs — Comuns Improvement Proposals | Process | CIP process. |
| [docs/cip/0000-template.md](cip/0000-template.md) | CIP NNNN: Title | Process | CIP template. |
| [docs/cip/0001-adopt-baseline-adrs.md](cip/0001-adopt-baseline-adrs.md) | CIP 0001: Adopt the baseline ADRs | Process | Draft CIP proposing adoption of the baseline ADRs. |
| [docs/cip/0002-anonymous-credits-relays-and-ownerless-contexts.md](cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) | CIP 0002: Anonymous credits, relays and ownerless contexts | Process | Draft amendment for anonymous credits, relays and contexts; no adoption yet. |
| [docs/cip/0003-bootstrap-first-maintainer-and-channels.md](cip/0003-bootstrap-first-maintainer-and-channels.md) | CIP 0003: Bootstrap: first maintainer, enforcement contact and private security channel | Process | Draft bootstrap CIP; proposes seating the first maintainer and naming the private channels; seats nobody today. |
| [docs/cip/0004-sepolia-testnet-configuration.md](cip/0004-sepolia-testnet-configuration.md) | CIP 0004: Arbitrum Sepolia testnet configuration (testnet-only, non-normative) | Process | Draft CIP proposing testnet-only, non-normative configuration and model registration; mainnet unchanged. |
| [docs/cip/0005-phase-one-implementation.md](cip/0005-phase-one-implementation.md) | CIP 0005: Phase 1 implementation | Process | Draft implementation CIP proposing ADRs 0013–0015, completion gates and pre-code rechecks. |
| [pitch/pitch-deck.md](../pitch/pitch-deck.md) | Comuns — pitch deck | Analysis | Pitch deck source. |
| [pitch/pitch-deck.html](../pitch/pitch-deck.html) | Comuns — printable pitch deck | Presentation | Rendered pitch deck. |
| [scripts/check-pricing.py](../scripts/check-pricing.py) | Pricing checker | Tooling | Checks the pricing fixtures. |
| [scripts/check-docs.py](../scripts/check-docs.py) | Documentation checker | Tooling | Checks document conventions. |
| [scripts/check-deck.py](../scripts/check-deck.py) | Pitch deck checker | Tooling | Checks the pitch deck. |
| [scripts/check-dco.py](../scripts/check-dco.py) | DCO checker | Tooling | Checks DCO trailers on every commit in a pull-request range, including merges. |

## 3. Documentation conventions

Substantive documents begin with a title and this header block, using their actual category and appropriate references:

```text
# Document title
Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12
**Reference:** README.md
---
```

Number H2 sections consecutively from 1. End with Risks, then Open questions. Identify each risk with a `[RISK]` marker and a severity. Technical Proposals under docs/ are checked for that structure. The evidence register additionally needs H2 headings containing the literal labels §1 through §16 and a How to cite section. Cite the section that actually contains a fact and its evidence mark; use UNVERIFIED for facts absent from the register.

Put diagrams in fences tagged `mermaid`. The checker accepts declarations beginning with `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `graph` or `classDiagram`; it checks structure, not rendering. Fences must balance, and every `json` fence must contain valid JSON. Use document-relative Markdown links. On a **Reference:** line, bare paths beginning with docs/, pitch/ or scripts/ and root filenames are repository-relative; other bare paths are relative to the document.

ADRs follow the [ADR index](adr/README.md): a four-digit numbered filename, a title beginning `# ADR NNNN:`, the fields `**Status:**`, `**Date:**`, `**Deciders:**`, and the H2 sections Context, Decision, Alternatives considered, Consequences and Links. Include at least three alternatives with rejection or deferral reasons. ADRs remain proposed until their adopting CIP is Final: CIP-0001 for ADRs 0001–0009, CIP-0002 for ADRs 0010–0012 and CIP-0005 for ADRs 0013–0015; later contradictions require a superseding ADR. ADRs 0016–0018 are proposed with no adopting CIP yet.

CIPs follow the [CIP process](cip/README.md) and [template](cip/0000-template.md): a four-digit filename, a `# CIP NNNN:` title, Status, Type, Created and Requires fields, and Abstract, Motivation, Specification, Rationale, Backwards compatibility, Security considerations, Economic considerations, Reference implementation, Change log and Copyright sections. These ADR and CIP formats use their own unnumbered section headings. A CIP proceeds through Draft, Review, Last Call and Final under GOVERNANCE.md. A substantive Last Call edit returns it to Review; a Last Call CIP cannot become Stagnant. Seating and removal require a Final CIP.

## 4. Risks

### R1 — Drafts mistaken for implemented behavior **[RISK] · High**

Every architecture and protocol statement remains a proposal. Passing structural checks does not establish protocol correctness, security, performance or a rendered diagram's validity.

### R2 — Companion documents or review report are pending **[RISK] · Medium**

The review report, docs/review-report.md, records the consistency review of the set.

## 5. Open questions

- Which proposals will the community adopt through a Final CIP?
- Which residual conflicts recorded in the review report should be settled by a CIP first?
