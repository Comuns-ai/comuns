# Comuns — pitch deck

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** docs/project-charter.md, docs/architecture/system-architecture.md, docs/project-plan.md, docs/economics/cost-and-pricing.md, docs/security/privacy-and-contexts.md, GOVERNANCE.md

pitch/pitch-deck.html is the self-contained rendering of this file and must be kept in sync


---

## Comuns

**Open, community-built AI inference for everyone**

- A community proposal for open-source, decentralized LLM inference, settled on Arbitrum One.
- Not a running product: nothing runs yet. Every document is a draft the community may adopt, change or reject through Comuns Improvement Proposals (CIPs).
- *Comuns* is Portuguese for "commons".
- comuns.ai

> Speaker notes: Open by saying what this is and what it is not: a proposal written in the open, not a launched network. Everything that follows is a draft the audience can change.

---

## The closed door

- Hosted models concentrate capability in a few providers.
- A cheap API still lets the provider read every prompt and refuse service.
- Hosted open-weight inference is already offered from $0.02 per 1M input tokens in a public snapshot (evidence register §6, [V]).
- Comuns does not claim a lower price than hosted APIs.
- The case is control: code, specifications and economics that anyone can inspect, run and fork.

> Speaker notes: Do not argue on price; the snapshot shows hosted inference is already cheap. Argue on who holds the door: who reads prompts and who can refuse service.

---

## Built by a community, in the open

- Apache-2.0 for code and documents; DCO sign-off, no CLA.
- Decisions are CIPs: Draft, Review, Last Call, Final. Working groups review; a CIP decides.
- No token gate and no coin vote: a class S operator has an equal voice.
- No maintainers are seated yet; the first are named only by a public CIP.
- **The repository is the proposal.** Every claim in this deck lives in a document anyone can challenge.

> Speaker notes: This is the central message. Comuns is built by whoever shows up and writes in public, not by a company that owns the roadmap.

---

## One prompt, end to end

By default **one node** runs a request: pick a model, then a node from its pool. Collective answers, decomposed plans and parallel planning are **opt-in**; every planner reads the prompt, and the client shows which nodes read what before signing.

1. Pick a node; encrypt the prompt locally.
2. Open a session with a deposit.
3. The node runs the model off-chain; chunks return sealed.
4. The client signs a voucher per chunk.

A paid orchestrator node is disclosed, never mandatory. The chain never runs a model.

> Speaker notes: Walk the four steps slowly; single-node execution is the default. The open-source orchestrator in the user's app can assess, plan a DAG, run waves in parallel, review and merge; it is designed client-side code, not something implemented today.

---

## Small hardware, large hardware

- Model-first pools: the user picks a model; its **pool** is the nodes offering it.
- Any node may serve any registered model it can load. Memory fit and its per-model self-benchmark decide, not class; the benchmark is a signed claim, not proof.
- The same model is cheaper from small hardware and dearer from strong hardware.
- Classes and tiers are labels, never a serving-permission matrix.
- Illustration: a 70B Q4 model does not fit a 32 GB card (evidence register §6, [V]).

> Speaker notes: Memory fit is the only real limit on what a node offers. CPU-only machines target tier T0, a target still to be validated, with no published benchmark yet.

---

## Better hardware charges more

- Governance sets a price band for every tier and class, input and output separately.
- The floor of a higher class sits strictly above the ceiling of the class below.
- So every class may offer the same model: a weaker class charges less for it, and a stronger class is paid more.
- There is no class-to-tier eligibility restriction.
- Not an auction to the cheapest: users choose by price, speed, reputation and privacy mode.
- No band value is adopted; a later CIP sets them.

> Speaker notes: Bands reward stronger hardware without excluding small machines. No numbers are shown because none are adopted.

---

## Who can read a prompt

- In standard mode the chosen node can read the prompt.
- Other nodes and the chain cannot read it.
- With more than one node, the disclosure sheet states before signing how many readers, counted by distinct node and operator, see the prompt, a sub-task, activations or draft tokens: a floor from the actual payloads.
- Public: who paid whom, for which model, and token counts.
- Attested mode does not stop a physical attacker (evidence register §4, [L]).
- Local execution is the only owner-only option.

> Speaker notes: Say plainly that the executor sees plaintext. The disclosure sheet counts every reader before the user signs anything.

---

## Your contexts, your wallet

- One wallet keeps many encrypted, versioned contexts.
- Each version has its own key; ciphertext stays off-chain and the chain records the latest version hash.
- Sharing with a node means re-wrapping that version's key to the node's key, signed by the owning wallet. Nodes never exchange plaintext.
- Revocation works going forward: later versions stay unreadable, but a node cannot forget what it already decrypted.
- Back up the identity key, and keep ciphertext on a second device or host.

> Speaker notes: Contexts are portable memory the user owns. Revocation limits the future, not the past, and the deck should say so.

---

## Sessions on Arbitrum One

- Solidity contracts on the EVM of Arbitrum One settle sessions.
- Stylus is not the v1 plan: new activations are paused since 2026-10-02 (evidence register §1, [V]), and a model cannot fit in a contract.
- Two transactions per session on the happy path, not one per message; a plan using several nodes pays several sessions.
- The ETH paid to the node is not the L2 fee; gas is paid separately.
- Protocol fee: zero. Payees withdraw their credited balances.

> Speaker notes: Many prompts share one session, so the chain sees an open and a close. Multi-node plans multiply sessions, and we say so up front.

---

## Trust, then verify when you ask

- v1 does not slash; nodes post only a withdrawable bond.
- The user's remedy: stop signing vouchers and leave a reputation event.
- A **collective answer** is opt-in: several nodes answer independently, cross-check blind, and one synthesis lists disagreements. It costs more, is not verification and never changes payment.
- Verifiable mode is opt-in re-execution by a second node the user chooses, who reads the prompt, under a demonstrated deterministic profile. The mode is public on-chain; a mismatch has no payment consequence.
- zk proofs are not the product.

> Speaker notes: Quality and verification are separate tools. A collective answer can surface disagreement; only re-execution checks a result, and it adds a reader.

---

## Inference only, no token

Comuns does LLM inference and nothing else. Its non-goals:

- Training, fine-tuning and federated learning.
- A protocol token, staking rewards or emissions.
- Stylus in v1, and inference inside a contract.
- A mandatory central proxy or orchestrator.
- Slashing in v1.

A narrow scope keeps the design small enough for a volunteer community to review line by line.

> Speaker notes: Every non-goal removes a reason for someone to capture the project. If the community wants one of these later, it writes a CIP.

---

## From proposal to running code

| Phase | Name |
|---|---|
| 0 | Documentation baseline |
| 1 | Sepolia slice |
| 2 | Contexts and classes |
| 3 | Verification spike |
| 4 | External review |

There are no dates. Phase 3 may end with a negative result. Sharding and cross-node speculation are experimental Phase 3 work, with testnet-only prices, refused under mainnet parameters; shard holders hold no session and are never paid. No internet speed-up is promised (evidence register §9, quote [V], result not replicated [U]). Phase 4 closes with a go/no-go CIP.

> Speaker notes: Phases are ordered, not scheduled. A published negative result counts as a finished phase.

---

## Risks we state openly

- Executor plaintext: the chosen node reads the prompt in standard mode.
- Arbitrum One has a single sequencer (evidence register §1, [V]).
- Price bands are unset, so mainnet is not deployable.
- Hardware class claims are self-benchmarks and can be faked.
- Nobody is seated, and nobody may come to contribute.
- Activations can reveal a prompt (evidence register §10, [V]); a parallel plan or collective answer costs several sessions and can be worse than one strong model (evidence register §11, [V]).

> Speaker notes: Read the risks aloud rather than skipping them. Each one has a mitigation and an owner document in the repository.

---

## Build it with us

- Read the documents and comment on CIP-0001, which proposes adopting the baseline decisions.
- Join a working group: Protocol, Node, Cryptography, Contracts, Applications or Documentation.
- Later, run a node on any hardware class.
- Never paste prompts, keys or seed phrases into issues.
- comuns.ai

Figures and design notes live in the referenced documents and are a 2026-10-12 proposal snapshot.

> Speaker notes: Close with the ask: read, comment, join a group. Nothing needs a token or a powerful machine to take part.
