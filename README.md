# Comuns

This repository is a draft proposal for a community to build an open-source, decentralized LLM-inference network; nothing here runs yet.

The proposal works like this: Arbitrum One settles sessions in ETH. Rust nodes run models off-chain; llama.cpp kernels are C/C++. A wallet keeps many encrypted contexts and hands one to another node only by re-wrapping the keys of the granted versions, each of which has its own key. The node that runs a prompt can read it; other nodes and the chain see only ciphertext and metadata unless you explicitly grant another node access. The user picks a model and then a node from the pool of nodes currently offering it. Any node that can load a registered model may offer it, subject to its hosting permission and price band; higher hardware classes charge more for the same model so small tasks stay on small hardware. By default one node runs a request. Optional multi-node features — several nodes answering and cross-checking (a collective answer, which shows its disagreements and is not verification), a plan split into parallel sub-tasks on different pools, parallel planning, and experimental sharding and cross-node speculative decoding — are opt-in per request. Before you sign, the client shows which nodes will read which part, including nodes that can reconstruct prompt text from their inputs, and counts distinct nodes and operators. The two experimental features are Phase 3 testnet-only work; the reference client refuses them under mainnet parameters, shard holders receive no sessions or payments, and no WAN speed-up is promised. The orchestrator is open-source code in your app; an optional orchestrator node is paid as an ordinary session and is never required. Development is by CIP, Apache-2.0 and the DCO, with no protocol token and no slashing in v1. The scope is inference only.

comuns.ai

Draft · ADRs proposed · maintainers not seated

## Why

- Privacy from third parties through encrypted requests and contexts, with the chosen prompt readers disclosed. An executing operator can retain plaintext; encryption does not prevent that.
- Censorship resistance through independently operated nodes and a client that chooses its provider. This is a design goal, not a guarantee of availability.
- Participation from CPU-only class S to multi-GPU class X, subject to measured capability and model fit. Classes select price bands; model tiers are separate labels.

Comuns makes no claim of a lower price than hosted APIs.

## How to take part

Read [GOVERNANCE.md](GOVERNANCE.md) for the CIP process and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution and DCO rules. Review [the baseline adoption CIP](docs/cip/0001-adopt-baseline-adrs.md), which remains Draft. [MAINTAINERS.md](MAINTAINERS.md) records the unseated roles; seating and removal require a Final CIP. [SECURITY.md](SECURITY.md) explains reporting boundaries. Contribute documentation comments, requirement reviews or working-group proposals through issues and CIP comments on the future public repository.

Never paste prompts, keys or seed phrases into issues.

## Start here

1. [Pitch deck source](pitch/pitch-deck.md) — the short introduction.
2. [Printable pitch deck](pitch/pitch-deck.html) — the presentation form.
3. [Project charter](docs/project-charter.md) — scope, positions and document ownership.
4. [System architecture](docs/architecture/system-architecture.md) — components and flows.
5. [Project plan](docs/project-plan.md) — phases and evidence gates.

## Document map


### Repository root

- [README.md](README.md) — Entry point for the repository.
- [LICENSE](LICENSE) — Apache-2.0 license text.
- [GOVERNANCE.md](GOVERNANCE.md) — CIP process, working groups, decision rules.
- [CONTRIBUTING.md](CONTRIBUTING.md) — How to contribute; DCO sign-off.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Community conduct rules.
- [SECURITY.md](SECURITY.md) — How to report vulnerabilities.
- [MAINTAINERS.md](MAINTAINERS.md) — Maintainer roles (none seated).

### docs

- [docs/README.md](docs/README.md) — Index of the documentation.
- [docs/project-charter.md](docs/project-charter.md) — Project charter: scope, goals, non-goals, phases and risks.
- [docs/evidence-register.md](docs/evidence-register.md) — External facts with marks [V]/[L]/[U].
- [docs/requirements.md](docs/requirements.md) — Requirements traceability.
- [docs/project-plan.md](docs/project-plan.md) — Phases 0–4 and their exit criteria.
- [docs/risk-register.md](docs/risk-register.md) — Consolidated risks.
- [docs/glossary.md](docs/glossary.md) — Terms.
- [docs/faq.md](docs/faq.md) — Frequently asked questions.
- [docs/landscape.md](docs/landscape.md) — Comparison with other networks.
- [docs/review-report.md](docs/review-report.md) — Review report of the consistency pass over the document set.

### docs/architecture

- [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md) — Components and flows.
- [docs/architecture/deployment-and-decentralization.md](docs/architecture/deployment-and-decentralization.md) — Deployment and decentralization limits.

### docs/protocol

- [docs/protocol/contracts-and-settlement.md](docs/protocol/contracts-and-settlement.md) — Registries, cumulative vouchers and ETH credits claimed through withdraw().
- [docs/protocol/off-chain-api.md](docs/protocol/off-chain-api.md) — Client–node API.
- [docs/protocol/orchestration.md](docs/protocol/orchestration.md) — Opt-in client planning, parallel sub-tasks across model pools, waves and confirmed reader disclosure.
- [docs/protocol/collective-answers.md](docs/protocol/collective-answers.md) — Opt-in answers and cross-checks with visible disagreements, plus parallel planning; neither is verification.

### docs/security

- [docs/security/privacy-and-contexts.md](docs/security/privacy-and-contexts.md) — Prompt readers, signed job envelopes, per-version context keys, grants and backup limits.
- [docs/security/threat-model.md](docs/security/threat-model.md) — Threats and mitigations.
- [docs/security/inference-verification.md](docs/security/inference-verification.md) — Opt-in re-execution by a user-chosen second node under a demonstrated deterministic profile.

### docs/economics

- [docs/economics/cost-and-pricing.md](docs/economics/cost-and-pricing.md) — Separate hardware classes and model tiers, ordered price bands and session costs.
- [docs/economics/pricing-examples.json](docs/economics/pricing-examples.json) — Non-normative pricing fixtures.

### docs/node

- [docs/node/node-design.md](docs/node/node-design.md) — Rust node design.
- [docs/node/hardware-classes-and-benchmarks.md](docs/node/hardware-classes-and-benchmarks.md) — Classes and self-benchmarks.
- [docs/node/model-registry-and-licenses.md](docs/node/model-registry-and-licenses.md) — ModelRegistry and model licenses.
- [docs/node/distributed-execution.md](docs/node/distributed-execution.md) — Experimental Phase 3 testnet-only sharding and cross-node speculation; no WAN speed-up is promised.

### docs/product

- [docs/product/dapp-and-sdk.md](docs/product/dapp-and-sdk.md) — Reference dapp and client SDK.

### docs/adr

- [docs/adr/README.md](docs/adr/README.md) — ADR index.
- [docs/adr/0001-settle-on-arbitrum-one-evm-not-stylus.md](docs/adr/0001-settle-on-arbitrum-one-evm-not-stylus.md) — Proposed Arbitrum One settlement with EVM contracts.
- [docs/adr/0002-off-chain-rust-inference.md](docs/adr/0002-off-chain-rust-inference.md) — Proposed off-chain Rust nodes with pluggable inference backends.
- [docs/adr/0003-hpke-and-the-executor-plaintext-limit.md](docs/adr/0003-hpke-and-the-executor-plaintext-limit.md) — Proposed two-way HPKE with explicit disclosure of prompt readers.
- [docs/adr/0004-sessions-vouchers-and-no-slashing.md](docs/adr/0004-sessions-vouchers-and-no-slashing.md) — Proposed ETH escrow, cumulative vouchers, pull payments and no v1 slashing.
- [docs/adr/0005-hardware-classes-and-price-bands.md](docs/adr/0005-hardware-classes-and-price-bands.md) — Proposed ordered price bands across hardware classes.
- [docs/adr/0006-apache-2-0-and-dco.md](docs/adr/0006-apache-2-0-and-dco.md) — Proposed Apache-2.0 licensing and DCO contribution certification.
- [docs/adr/0007-no-protocol-token-in-v1.md](docs/adr/0007-no-protocol-token-in-v1.md) — Proposed ETH payments and no protocol token in v1.
- [docs/adr/0008-model-first-pools.md](docs/adr/0008-model-first-pools.md) — Proposed model-first pools: any node may offer a registered model it can load; classes select price bands.
- [docs/adr/0009-opt-in-client-orchestration.md](docs/adr/0009-opt-in-client-orchestration.md) — Proposed single-node default, opt-in client orchestration and optional ordinary-session orchestrator nodes.

### docs/cip

- [docs/cip/README.md](docs/cip/README.md) — CIP process.
- [docs/cip/0000-template.md](docs/cip/0000-template.md) — CIP template.
- [docs/cip/0001-adopt-baseline-adrs.md](docs/cip/0001-adopt-baseline-adrs.md) — CIP adopting the baseline ADRs.

### pitch

- [pitch/pitch-deck.md](pitch/pitch-deck.md) — Pitch deck source.
- [pitch/pitch-deck.html](pitch/pitch-deck.html) — Rendered pitch deck.

### scripts

- [scripts/check-pricing.py](scripts/check-pricing.py) — Checks the pricing fixtures.
- [scripts/check-docs.py](scripts/check-docs.py) — Checks document conventions.
- [scripts/check-deck.py](scripts/check-deck.py) — Checks the pitch deck.

## Checks you can run

```sh
python3 scripts/check-pricing.py
python3 scripts/check-docs.py
python3 scripts/check-deck.py --html pitch/pitch-deck.html --markdown pitch/pitch-deck.md --expected-slides 14
```

For the presentation, print to PDF with Chrome headless (1333 by 750 page), keeping the PDF outside this repository.

The documentation checker, scripts/check-docs.py, checks links, headers, section numbering and structure across the document set. Its Mermaid check is structural, not a render. The checker reads files and writes nothing.

## Roadmap

1. Phase 0 Documentation baseline
2. Phase 1 Sepolia slice
3. Phase 2 Contexts and classes
4. Phase 3 Verification spike
5. Phase 4 External review

See the project plan for exit criteria; these phases are proposed work.

## License

Code and documentation use [Apache-2.0](LICENSE), and contributions use the [DCO](CONTRIBUTING.md). LICENSE is GitHub's canonical Apache-2.0 license text. Model weights retain their own licenses.
