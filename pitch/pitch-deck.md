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

By default **one node** runs a request: pick a model, then a node from its pool. Collective answers and decomposed plans are **opt-in**.

1. Deposit once into the credit pool.
2. Encrypt the prompt locally; send it through a relay run by someone else.
3. The node opens the session with your unlinkable credit and runs the model off-chain; chunks return sealed.
4. The client signs a voucher per chunk.

A paid orchestrator is disclosed, never mandatory.

> Speaker notes: Walk the four steps slowly; single-node execution is the default. You pick a model and a node before step 2. Parallel planning is also opt-in; every planner reads the prompt, and the client shows which nodes read what before signing. The chain never runs a model. The open-source orchestrator in the user's app can assess, plan a DAG, run waves in parallel, review and merge; it is designed client-side code, not something implemented today.

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

- Anonymous by default: the node you pick can read your prompt, but neither it nor the chain should learn who sent it.
- Attested (TEE) nodes should not be able to read it either; a physical attack can break that (evidence register §14, [V]).
- Standard mode has one content reader; multi-node features add more, counted on the disclosure sheet before you confirm.
- Relays hide your network address; unlinkable credits hide your wallet, though the deposit itself is public.
- Not hidden: what your words reveal about you, or traffic timing (evidence register §16, [L]/[V]).

> Speaker notes: Keep the two promises apart. The disclosure sheet is shown before you confirm. Anonymity: the node you pick can read your prompt but should not learn who sent it. Confidentiality: only an attested node should be unable to read it, barring a physical attack. The disclosure sheet counts every reader before the user signs anything.

---

## Your contexts, your wallet

- Many encrypted, versioned contexts live in your local vault; the chain stores no wallet.
- Each version has its own key; ciphertext stays off-chain.
- Sharing with a node means re-wrapping that version's key to the node's key, signed by a per-context key, not your wallet. Nodes never exchange plaintext.
- Revocation works going forward: later versions stay unreadable, but a node cannot forget plaintext it already saw.
- Back up the identity key, and keep ciphertext on a second device or host.

> Speaker notes: Contexts are portable memory the user owns, with no wallet link on-chain. Revocation limits the future, not the past, and the deck should say so.

---

## Sessions on Arbitrum One

- Solidity contracts on the EVM of Arbitrum One settle sessions.
- Sessions are funded by unlinkable credits from Semaphore groups inside the escrow and opened by the node: the chain sees a session, never a payer.
- Stylus is not the v1 plan: new activations are paused since 2026-10-02 (evidence register §1, [V]).
- Close still settles; claiming unspent credit takes another transaction. Gas is paid separately.
- Protocol fee: zero. Payees withdraw their credited balances.

> Speaker notes: Many prompts share one session, so the chain sees an open and a close but no payer. Multi-node plans multiply sessions, and we say so up front.

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
- MPC or FHE private inference: minutes per token today (evidence register §14, [V]).
- Running the model on your own machine as a product option.

A narrow scope keeps the design small enough for a volunteer community to review line by line.

> Speaker notes: Every non-goal removes a reason for someone to capture the project. If the community wants one of these later, it writes a CIP.

---

## From proposal to running code

| Phase | Name | Content |
|---|---|---|
| 0 | Documentation baseline | This documentation |
| 1 | Sepolia slice | Relay plus credit session |
| 2 | Contexts and classes | Ownerless contexts, pools, sheet, orchestrator |
| 3 | Verification spike | Attested nodes plus the spikes |
| 4 | External review | Reviews, then go/no-go |

There are no dates. Phase 3 may end with a negative result. Sharding and cross-node speculation are experimental Phase 3 work, with testnet-only prices, refused under mainnet parameters; shard holders hold no session and are never paid. No internet speed-up is promised (evidence register §9, quote [V], result not replicated [U]).

> Speaker notes: Phases are ordered, not scheduled. A published negative result counts as a finished phase.

---

## Risks we state openly

- Anonymity is not confidentiality: the chosen node reads standard-mode content; your words can identify you; anonymity sets are small at launch; relay and node timing can correlate (evidence register §15 [U], §16 [V]/[L]).
- Arbitrum One has a single sequencer (evidence register §1, [V]).
- Price bands are unset: no mainnet.
- Class claims are self-benchmarks, fakeable.
- Nobody is seated; nobody may come.
- Activations can reveal a prompt (evidence register §10, [V]); parallel plans cost several sessions and can be worse than one model (evidence register §11, [V]).

> Speaker notes: Read the risks aloud rather than skipping them. Anonymity sets are small at launch. Relay and node timing can both correlate; contributors may not arrive. Without price bands mainnet is not deployable; hardware class claims are self-benchmarks. A collective answer likewise costs several sessions and can be worse than one strong model. Each one has a mitigation and an owner document in the repository.

---

## Build it with us

- Read the documents and comment on CIP-0001, which proposes adopting the baseline decisions.
- Join a working group: Protocol, Node, Cryptography, Contracts, Applications or Documentation.
- Later, run a node on any hardware class.
- Never paste prompts, keys or seed phrases into issues.
- comuns.ai

Figures and design notes live in the referenced documents and are a 2026-10-12 proposal snapshot.

> Speaker notes: Close with the ask: read, comment, join a group. Nothing needs a token or a powerful machine to take part.
