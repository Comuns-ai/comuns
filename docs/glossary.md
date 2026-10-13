# Glossary

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** [project-charter.md](project-charter.md), [protocol/contracts-and-settlement.md](protocol/contracts-and-settlement.md), [security/privacy-and-contexts.md](security/privacy-and-contexts.md), [protocol/orchestration.md](protocol/orchestration.md), [../GOVERNANCE.md](../GOVERNANCE.md)

---

Comuns is a community proposal for open-source decentralized LLM inference. Nothing runs yet. Entries are alphabetical. Settlement identifiers are defined in [protocol/contracts-and-settlement.md](protocol/contracts-and-settlement.md); if a wording here and that document disagree on a field, that document wins. v1 has no slashing and no token.

### ADR

An ADR is an architecture decision record under `docs/adr/`. The records ADR 0001 through ADR 0009 are proposed, and none is adopted, because adoption requires a Final CIP and [cip/0001-adopt-baseline-adrs.md](cip/0001-adopt-baseline-adrs.md) is not Final. With nobody seated, nobody has authority to mark a record adopted.

### answerer

An answerer is a node that, in an opt-in collective answer, receives the full prompt sealed to it alone and returns one independent answer. It does not see another answer while it is generating. It is a full-prompt reader, it is paid through an ordinary session for the model it runs, and a discarded answer does not reverse its signed voucher.

### attested mode

Attested mode (mode 1) means the client checks a TEE quote, bound to the node's HPKE key and a client nonce, before it seals anything, and the request fails closed when no eligible node exists. It is not a physical-attack defense: a physical extraction of attestation keys is recorded, and vendors treat physical attacks as out of scope (evidence register §4, [L]). The node still sees the prompt in plaintext inside the TEE.

### band

A band is the governance-set floor and ceiling, for input and for output, on the price a hardware class may ask for one model tier. For each tier the floor of the next stronger class is strictly above the previous class's ceiling, so stronger hardware charges more for the same model, and the operator may set any price inside that band. No wei value is adopted; an unset band blocks new paid sessions for that pair, and it does not make the class ineligible to offer the model.

### bond

A bond is the ETH an operator locks when registering a node. After the unlock delay, `withdrawBond` credits that operator's internal balance, and only `withdraw()` sends ETH. v1 has no slashing and no token, so the bond is never seized.

### chunk (CHUNK_TOKENS)

A chunk is one piece of output of at most `CHUNK_TOKENS` tokens, and each chunk the client acknowledges is one step of the session's cumulative voucher. `CHUNK_TOKENS` is a named parameter with no value set in v1. The node's unpaid exposure is the one chunk it may already have sent past the prefix the client signed for, and that unacknowledged chunk is not paid.

### CIP

A CIP is a Comuns Improvement Proposal, the written record of a change, and it moves Draft, then Review, then a 14-day Last Call, then Final. A CIP in Last Call cannot become Stagnant; a substantive edit during Last Call returns it to Review, and the single 6-month inactivity clock applies only to Draft and Review. Anyone may file a CIP, there is no token gate, and a maintainer is seated or removed only by a Final CIP.

### class (S/M/L/X)

A hardware class is S, M, L or X, encoded 0–3 and ordered S < M < L < X, and it is decided by passing per-class benchmark bars on the public class benchmark. A class is not a tier, and it is never defined as the highest tier passed; `maxTier` is a separate informational field. A class selects the price band only: classes price work, and they do not gate which registered model a node may offer.

### collective answer

A collective answer is an opt-in quality mechanism: at least two nodes answer the same prompt independently, reviewers cross-check those answers blind and twice with positions swapped, under stable ids `A1…Ak`, and a synthesizer returns a merged text plus a splits list. It is not verification, not mode 2, not chain consensus, and it never affects payment, so a disagreement does not reverse a signed voucher. When one strong model is in a pool the client suggests self-consistency or Self-MoA first, the user may still opt in, and a plurality vote is never applied to free text.

### content hash

The content hash is keccak256 of the complete stored blob, which is the header, the ciphertext and the tag, and that is the one canonical definition. It is not a hash of the plaintext. ContextRegistry stores the latest version and content hash for each context, and a node checks an older version against the `ContextSet` event history.

### context

A context is a versioned blob a wallet owns — a transcript, a document or a system prompt — and each version `v` has its own random 256-bit key `K_v`. The chain stores the content hash, not the ciphertext. The backup export contains the identity key and every key-wrap record, and ciphertext that existed only on a lost device is gone even with the backup.

### context grant

A context grant is EIP-712 typed data signed by the wallet that owns the context, not by the session signer, and it wraps exactly the keys of the granted versions to one node's HPKE key. Expiry is `expiresAt`, a unix time in seconds (`uint64`), never a block number. A narrow grant restricts decryption to those versions, and the grant's idempotency key includes the job id.

### DCO

The DCO, the Developer Certificate of Origin, is the per-commit certification this proposal uses, recorded as a Signed-off-by line. It grants no license (evidence register §8, [V/L]). This proposal uses no CLA and no copyright assignment, and code and documents are Apache-2.0.

### disclosure sheet

The disclosure sheet is the record the client shows before the user signs any session for a request: each node's role, what it receives, its privacy mode, its two prices and its cap, plus how many distinct nodes and distinct operators can read the prompt. `readersOfFullPrompt` is a floor taken from the actual payloads and is at least `counts.fullPrompt`, which counts nodes literally sent the full prompt; the sheet JSON is normative. Any change of node, model, data scope, price, cap or reader set creates a new sheet version that the user confirms before any `openSession` or job under it, and amounts are shown in ETH with the unit.

### draft node

A draft node is the node, in the experimental cross-node speculation spike, that proposes draft tokens for a target node to score. It receives the full prompt, so it is a full-prompt reader, and its ordinary session on the draft model is billed for the acknowledged draft tokens it delivers, including drafts the target rejects. The reference client refuses the spike under mainnet parameters; it runs only with testnet-only, non-normative prices, and no WAN speed-up is promised.

### escrow

Escrow is the `SessionEscrow` contract: the user deposits ETH for one node and one model, and the effective cap is the minimum of `depositWei` and `maxSpendWei`. No contract pushes ETH during settlement, refund or bond release; credits land in an internal balance, and the only function that sends ETH is `withdraw()`, which pays the caller its whole balance. For every settled session the credits to the node and to the user add up to `depositWei` exactly.

### execution feature

An execution feature is one of `collective_answer`, `parallel_planning`, `task_decomposition`, `model_sharding` and `cross_node_speculation`, chosen on the client per request and never stored on-chain. The empty set is single-node execution, which is the default. Every non-empty set is opt-in per request and is listed on the disclosure sheet, and these features are orthogonal to the privacy modes of each session.

### HPKE

HPKE in this proposal is RFC 9180 base mode with X25519, HKDF-SHA256 and ChaCha20-Poly1305, used in both directions: the client seals the job to the node's registered key, and the node seals each output chunk to that job's client key. Base mode does not authenticate the sender, so every job envelope also carries a signature by the session signer over the ciphertext. Client encryption keys come from the operating-system random source and are never derived from the wallet key.

### inference payment

The inference payment is the ETH that `SessionEscrow` credits to a node for cumulative tokens, by the formula `paymentWei = (priceInPerMillion * inputTokens + priceOutPerMillion * outputTokens) / 1000000` with integer floor division and the session's prices. It is not L2 gas, which the user pays separately to the chain, and the protocol fee is 0. v1 has no token; a signed voucher is not reversed; `redeemVoucher` credits the node and never credits a refund.

### L2 gas

L2 gas is the Arbitrum One fee for a transaction, including opening a session, topping up, redeeming a voucher, closing, finalizing and withdrawing. It does not pay for model tokens, and it is not the inference payment. The disclosure sheet shows a gas estimate in ETH with the unit, separate from the inference cap.

### maintainer

A maintainer is a person with merge authority, and none is seated. A maintainer is seated, and a maintainer is removed, only by a CIP that becomes Final. Until that CIP is Final, nobody may merge, execute a timelock or take an emergency action, and names written in a Draft do not seat anyone.

### manifest hash

The manifest hash is the SHA-256 of the canonical JSON manifest, which names the weight files and their hashes, the pinned tokenizer, the quantization, the context limit and the license file. The model id is keccak256 of that manifest hash, so a different manifest is a different model. In v1 only the governance timelock may register or update a model, and with nobody seated there is no mainnet registration.

### model sharding

Model sharding (`model_sharding`) is the experimental Phase 3 spike in which shard holders keep contiguous layer ranges of one model and the client mediates every stage boundary. Every shard holder is treated as able to read the prompt; none holds a session and none is paid, in v1 or in the spike, including the first and the last. The reference client refuses the feature under mainnet parameters, a lost holder causes a restart from the beginning on a new chain from the sheet, and no performance is promised.

### model tier (T0–T4)

A model tier partitions the manifest's parameter count: T0 is at most 4B; T1 is more than 4B and at most 8B; T2 is more than 8B and at most 32B; T3 is more than 32B and at most 70B; T4 is more than 70B. An 8,000,000,000-parameter model is T1. A tier labels the price band, it is not a hardware class, and it does not decide which node may serve the model.

### node

A node is the open-source Rust process an operator runs to load models and serve inference, with pluggable backends. In v1 the node's identity is the operator's address, one node per address. In standard mode that node sees the prompt in plaintext; it signs receipts, checks vouchers, and keeps every HPKE key used by a session that is not yet settled.

### offer

An offer is the registry entry `prices[modelId] = (priceInPerMillion, priceOutPerMillion, modelBenchmarkHash)` with a non-zero `modelBenchmarkHash`. `updateNode` replaces the whole list: it emits `OfferSet` for every model added or changed, and a cleared `OfferSet` with zero prices and a zero `modelBenchmarkHash` for every model removed, and clearing is always allowed. A hardware-class change revalidates every listed offer against the new class's bands and reverts if any price sits outside its band.

### operator

An operator is the person who runs a node and the Ethereum address that registers it, posts the bond and is paid for its sessions; the operator is the payee, and a pool is not. In standard mode the operator of the chosen node can read the prompt, because the node decrypts it.

### orchestrator

The orchestrator is open-source logic in the client SDK. It assesses the task on the user's device first, and it plans, decomposes work into waves, or runs a collective answer or parallel planning only after the user opts in and confirms the disclosure sheet. Planner output is untrusted data: it never authorizes a new recipient, a payment, a tool or an external action.

### orchestrator node

An orchestrator node is an optional node that runs the same orchestrator logic for a thin client, and it is paid as an ordinary session for the tokens it generates. It holds no session signer in v1, takes no cut and custodies no other session; the user's client still opens every session and signs every voucher. It is never mandatory, and it is a full-prompt reader whenever it plans, merges or synthesizes.

### plan

A plan is an off-chain DAG of waves, held as client-side JSON. It is not a contract, and no registry stores it. The work pays one ordinary session per distinct pair of node and model id, the user confirms every model before a session opens, and a judge's rank is never executed on its own.

### pool

A pool is the set of nodes with a current offer `prices[modelId]` carrying a non-zero `modelBenchmarkHash`, enumerated off-chain from `OfferSet` events. It is not a contract and not a payee; the chain stores offers and sessions, and it never stores a pool list. Any node may offer any registered model it can load, and `maxTier` is informational and is never read as a gate by `openSession`.

### re-wrap

Shared contexts are re-wrapped ciphertext: the client unwraps the granted version keys with the identity key and seals those same keys to the next node's HPKE key, and the stored blob stays ciphertext. Nodes never exchange plaintext or keys. Moving a context to another node is a new session, a new wallet-signed grant and a new reader, disclosed on a new sheet version.

### reputation event

A reputation event is an off-chain note, or a reading of public chain events, that records how a session ended or that a user disputes a node's behaviour. It is not a slash, not a refund and not a reversal of a signed voucher. In v1 the user's remedy is to stop signing further vouchers and to close the session.

### reviewer

A reviewer receives the prompt together with the material it critiques: anonymized answers in a collective answer, or a sub-task output that the client treats as containing prompt text unless the client has checked that it does not. In a collective answer the review is blind and is repeated with positions swapped, and disagreement between those two passes is expected and does not by itself make the synthesis incomplete. The reviewer is paid through an ordinary session, and a low score does not change that payment.

### session

A session is one ETH escrow binding one user, one node, one model and one privacy mode, and it may contain many jobs run one at a time. The usual path is two transactions, `openSession` and `closeWithVoucher`; either the user or the node may call `closeSession` at any time, and nothing closes a session by itself. A request that uses several node-and-model pairs opens one session for each distinct pair.

### session signer

The session signer is an application key the client generates for one session, registered at `openSession`. It signs every job envelope and every voucher for that session, so the wallet is not prompted once per chunk, and an orchestrator node never holds this key in v1. A stolen session signer can keep signing vouchers up to the effective cap until the session is settled, and `closeSession` does not stop those vouchers before the close deadline.

### settlement layer

The settlement layer is Arbitrum One, and the v1 contracts are Solidity on the EVM: `NodeRegistry`, `ModelRegistry`, `ContextRegistry` and `SessionEscrow`. Stylus is not the v1 path, because new Stylus activations are paused and no reopening date is recorded (evidence register §1, [V]). Inference runs off-chain; the chain records offers, content hashes and sessions, and it does not run the model.

### shard holder

A shard holder keeps one contiguous layer range in the experimental model-sharding spike and is treated as able to read the prompt. It holds no session and is never paid, in v1 or in the spike, and the reference client never opens a session or signs a voucher for it. Holders authenticate with mutual TLS bound to their registered operator keys, and the client sends activations only to holders named on the disclosure sheet.

### speculative decoding

Local speculative decoding inside one node is an engine detail: it adds no reader, and it stays off in verifiable mode. Cross-node speculative decoding is an experimental Phase 3 spike with one job per session on a draft node and one on a target node, both of which can read the prompt; rounds are frames inside that job, the prompt is input-billed once per job, and draft probability distributions travel as sealed metadata that are not billable tokens. The reference client refuses the spike under mainnet parameters, no WAN speed-up is promised, and the spike is incompatible with verifiable mode because a speculative engine does not guarantee byte-identical output.

### splits list

The splits list is the set of claims a synthesizer reports that the answers disagree on, each claim tied to the stable answer ids that hold each side. An empty splits list is valid and means the synthesizer found no such claim. The client marks the result contested when the splits list is non-empty or the agreement level is low, and that label does not change payment.

### standard mode

Standard mode (mode 0) means the chosen node sees the prompt, the granted context and the completion in plaintext. The client says this on the disclosure sheet before the user signs. Parties that were not selected see ciphertext and the public session metadata, not the prompt text.

### synthesizer

A synthesizer takes the prompt, the answers and the critiques and returns a merged answer, a splits list and an agreement level. A remote synthesizer can read the full prompt; a synthesizer that is the user's own local model does not add a remote reader. The synthesis is incomplete only when a required field is missing or malformed.

### verifiable mode

Verifiable mode (mode 2) is opt-in re-execution by a user-chosen second node under a demonstrated deterministic profile, after which the client compares the two outputs. The verifier is a disclosed full-prompt reader, the session mode is public on-chain, a mismatch does not change payment in v1, and an activation commitment may be given to that disclosed verifier only. It is not a collective answer, and cross-node speculation is incompatible with it.

### voucher

A voucher is the EIP-712 typed data `Voucher(bytes32 sessionId,uint64 seq,uint256 cumulativeWei,uint64 inputTokens,uint64 outputTokens,bytes32 outputCommitment,bool final)`, signed by the session signer, with cumulative token counts and a `seq` that starts at 1 and strictly increases. `final` means only that the client closes the session; `redeemVoucher` rejects a final voucher, and only `closeWithVoucher` and `finalize` credit a refund. A signed voucher is not reversed; `outputCommitment` is keccak256 of the session's random 32-byte commit key, the session id, that voucher's seq and the transcript hash, it is not checked on-chain, and opening the commit key discloses that session's output.

### wallet owner

The wallet owner is the Ethereum account that owns the user's contexts and that funds sessions. That wallet signs `openSession`, `topUp`, `closeSession`, `withdraw` and every context grant. It does not sign each chunk's voucher, and encryption keys are never derived from it.

### wave

A wave is one topological level of a plan: tasks in the same wave have disjoint outputs and do not depend on one another, so they can run at the same time on different sessions. The `wave` field is advisory metadata, it is not bound into the job's associated data, and a node must not rely on it. One session still runs only one job at a time, so two tasks that share a session run one after the other unless the sheet lists a second session.

### working group

A working group reviews documents in public and recommends changes. The groups named in this proposal are Protocol, Node, Cryptography, Contracts, Applications and Documentation. A working group does not decide, seats no chair and carries no token weight; a CIP decides.
