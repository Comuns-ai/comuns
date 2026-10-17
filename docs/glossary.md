# Glossary

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** [project-charter.md](project-charter.md), [protocol/contracts-and-settlement.md](protocol/contracts-and-settlement.md), [security/privacy-and-contexts.md](security/privacy-and-contexts.md), [protocol/orchestration.md](protocol/orchestration.md), [../GOVERNANCE.md](../GOVERNANCE.md)

---

Comuns is a community proposal for open-source decentralized LLM inference. Nothing runs yet. Entries are alphabetical. Settlement identifiers are defined in [protocol/contracts-and-settlement.md](protocol/contracts-and-settlement.md); ADR [0011](adr/0011-anonymous-credits.md) is the source of truth for signatures, parameters and session fields; ADRs [0010](adr/0010-anonymous-by-default.md) and [0012](adr/0012-contexts-without-a-wallet-link.md) govern anonymity and contexts. v1 has no slashing and no token.


### ADR

An ADR is an architecture decision record under `docs/adr/`. The records ADR 0001 through ADR 0018 are proposed, and none is adopted, because adoption requires a Final CIP; [CIP-0001](cip/0001-adopt-baseline-adrs.md) and [CIP-0002](cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) remain Draft, and [CIP-0005](cip/0005-phase-one-implementation.md) (Draft) names ADR 0013–0015. ADR 0016–0018 have no adopting CIP yet. ADR 0003 is superseded in part by ADR 0010–0012. With nobody seated, nobody has authority to mark a record adopted.

### anonymous by default

Anonymous by default is the proposed separation of a request from the user’s identity: relay transport, credit-funded sessions with fresh session signers, and contexts without a wallet link. Nodes and chain observers should not learn who asked. It does not hide content in standard mode. Identifying text and timing remain risks (evidence register §16, [V]/[L]); anonymity sets are small at launch (evidence register §15, [U]); relay–node collusion remains a risk (evidence register §15, [V], and §16, [V]). All session-specific chain reads, including RPC or indexer queries for sessions, settlement, change, witnesses and roots, tunnel through a relay.

### answerer

An answerer is a node that, in an opt-in collective answer, receives the full prompt sealed to it alone and returns one independent answer. It does not see another answer while it is generating. It is a full-prompt reader, it is paid through a credit-funded session for the model it runs, and a discarded answer does not reverse its signed voucher.

### attested mode

Attested mode (mode 1) adds content privacy to anonymous transport and credits. The normative banner is: “This node should not be able to read your prompt. A physical attack on the hardware can break that.” Before sealing, the client checks a quote binding the TEE-generated job HPKE key, gateway key configuration and client nonce against the published measurement list for the node build and model manifest. Every plaintext recipient must be attested; no eligible node means failure, never a silent downgrade. Hardware limits are recorded in evidence register §14, [V]/[L].

### band

A band is the governance-set floor and ceiling, for input and for output, on the price a hardware class may ask for one model tier. For each tier the floor of the next stronger class is strictly above the previous class's ceiling, so stronger hardware charges more for the same model, and the operator may set any price inside that band. No wei value is adopted; an unset band blocks new paid sessions for that pair, and it does not make the class ineligible to offer the model.

### bond

A bond is the ETH an operator locks when registering a node or relay. After deregistration and the unlock delay, `withdrawBond` credits that operator’s internal balance and deletes the corresponding record; the relay branch requires no Node record. Only `withdraw()` sends ETH. v1 has no slashing and no token.

### change note

A change note is a fresh fixed-denomination note minted by `claimChange` after settlement, authorised by the session signer. The client greedily decomposes `pendingWei` into at most `MAX_CHANGE_NOTES` notes and durably stores a new Semaphore identity for each before publication. A zero-use session can return its full denomination this way. No note is inserted at close or finalize; there is no separate refund note.

### chunk (CHUNK_TOKENS)

A chunk is one piece of output of at most `CHUNK_TOKENS` tokens, and each chunk the client acknowledges is one step of the session's cumulative voucher. `CHUNK_TOKENS` is a named parameter with no value set in v1. The node's unpaid exposure is the one chunk it may already have sent past the prefix the client signed for, and that unacknowledged chunk is not paid.

### CIP

A CIP is a Comuns Improvement Proposal, the written record of a change, and it moves Draft, then Review, then a 14-day Last Call, then Final. A CIP in Last Call cannot become Stagnant; a substantive edit during Last Call returns it to Review, and the single 6-month inactivity clock applies only to Draft and Review. Anyone may file a CIP, there is no token gate, and a maintainer is seated or removed only by a Final CIP.

### class (S/M/L/X)

A hardware class is S, M, L or X, encoded 0–3 and ordered S < M < L < X, and it is decided by passing per-class benchmark bars on the public class benchmark. A class is not a tier, and it is never defined as the highest tier passed; `maxTier` is a separate informational field. A class selects the price band only: classes price work, and they do not gate which registered model a node may offer.

### collective answer

A collective answer is an opt-in quality mechanism: at least two nodes answer the same prompt independently, reviewers cross-check those answers blind and twice with positions swapped, under stable ids `A1…Ak`, and a synthesizer returns a merged text plus a splits list. It is not verification, not mode 2, not chain consensus, and it never affects payment, so a disagreement does not reverse a signed voucher. When one strong model is in a pool the client suggests self-consistency or Self-MoA first, the user may still opt in, and a plurality vote is never applied to free text.

### content hash

The content hash is keccak256 of the complete stored blob: header, ciphertext and tag, never plaintext. A context-key-signed head record binds it to the context id, version and previous content hash. The default integrity path is the host’s signed hash chain plus client checkpoints; an anchored context also records its latest version and hash in ContextRegistry, with older versions checked against event history.

### context

A context is a versioned encrypted blob, such as a transcript, document or system prompt. One wallet owns many contexts only through the key list in its local vault and identity-key backup; no wallet label is sent to nodes or written on-chain. `contextId = keccak256(contextPubKey)` and each version has a fresh encryption key `K_v`. A context host stores signed heads and ciphertext and is trusted for sequencing and availability. Clients persist accepted head checkpoints in the vault and backups and reject rollback behind them. Unanchored hosts can equivocate between devices that have not compared checkpoints; a stale backup cannot detect a head newer checkpoints would reject. A globally consistent multi-device head requires a public `setContext` anchor submitted by a broadcaster. Reusing a context id links sessions; key backups do not restore lost ciphertext.

### context grant

A context grant is EIP-712 typed data signed by the independent context key, carrying `contextPubKey` and `contextSignature`. It travels inside the encrypted job and wraps exactly the granted versions’ `K_v` keys to the recipient node’s job HPKE key. Neither the wallet nor the session signer signs the grant. Expiry is `expiresAt`, a unix time in seconds (`uint64`); the grant’s idempotency key includes the job id.

### context key

A context key is a random per-context signing key from the operating-system CSPRNG, never the wallet key or derived from it. It signs grants, head records and optional public anchors. The client checks `keccak256(contextPubKey) == contextId`. It is distinct from the per-version content encryption keys `K_v`; its wallet association stays in the vault and backup.

### core path

The core path is the proposed way of using the client that needs nothing hosted beyond a user-chosen Arbitrum RPC and the permissionless relays and nodes: a content-hash-pinned static build reached by a verifying fetch, a locally run gateway or a local run, and the user's own ETH account. Hosted conveniences (social login, embedded wallet, on-ramp, intent orchestrator, gas sponsor, bundler, indexer, public gateway) are optional, disclosed, replaceable and never in the spend path. It is proposed in [ADR 0017](adr/0017-accounts-and-decentralized-access.md) and [ADR 0018](adr/0018-one-client-stack.md), and it is not adopted; there is no adopting CIP yet.

### credit

A credit is ETH held as an unspent fixed-denomination note in the non-upgradeable SessionEscrow. A public `depositNote` creates it; a membership proof and nullifier fund `openSessionFromCredit` without naming the deposit wallet. It is not a protocol token or a withdrawable `balances[address]` entry. Change creates fresh notes, and ragequit is a public exit bounded by the caller’s deposits in that denomination group.

### DCO

The DCO, the Developer Certificate of Origin, is the per-commit certification this proposal uses, recorded as a Signed-off-by line. It grants no license (evidence register §8, [V/L]). This proposal uses no CLA and no copyright assignment, and code and documents are Apache-2.0.

### denomination

A denomination is the fixed ETH face value of a note and its Semaphore group, selected by denomination index. Governance appends values through `setCreditParameters`; existing values never change. Each value satisfies `MIN_DEPOSIT_WEI`, and an append must preserve greedy decomposition of every remainder below the largest denomination into at most `MAX_CHANGE_NOTES` notes with dust below the smallest denomination. Values remain unset.

### deposit key

The deposit key is a client-managed key (`depositKey`), proposed and not adopted. It exists only on an EIP-7702 EOA or a smart account, because a plain EOA "does not support ERC-7579 modules, session keys, multisig, account deployment, or ERC-4337 user operations" (evidence register §1, client UX research 2026-10-15, [V]). Its on-chain permission names exactly SessionEscrow's `depositNote`, with a per-call native ceiling set equal to one denomination, a use limit and a validity window. Each permission is bound to one contract and its listed selectors, and the native limit is a per-call ceiling (evidence register §4, client UX research 2026-10-15, [V]). Whether that permission can require exact equality, rather than a ceiling, is not documented (evidence register §4, client UX research 2026-10-15, [U]), so SessionEscrow's own value check is the equality rule. The documented spending-limit policy covers ERC-20 tokens and does not mention native ETH (evidence register §4, client UX research 2026-10-15, [V]), so no cumulative native limit is claimed. It never names a node, relay or other contract, never signs a voucher, envelope, spend, close, `claimChange`, `ragequit`, `withdraw` or grant, never pays a node or relay, is never in the spend path, and is never sent to a node or a relay. Refills follow a threshold or schedule with jitter, and no threshold, schedule or jitter is set; a refill never fires at cap exhaustion, on send or resume, or immediately before a spend. Automatic refills remain unavailable until a reviewed timing policy is adopted and its eligibility and trigger rules are demonstrated, and a fee-policy review is also required before the convenience is enabled. It is not a session key, not the session signer and not `commitKey`. The ragequit allowance (`depositedWei`) accrues to the account that is `msg.sender` of `depositNote`, which under the caller invariant is the user's own account; a deposit key never calls `ragequit`. If enforcement is correct, a stolen deposit key can move at most cap × uses of principal per grant and per chain, and only into `depositNote`. Gas and fees are separate and not bounded here. A validator or account defect is not bounded. A stolen key can create notes whose secrets the attacker holds, and the user cannot recover them. [ADR 0016](adr/0016-funding-edge-and-deposit-key.md) proposes it, and there is no adopting CIP yet.

### disclosure sheet

The disclosure sheet is the record the user confirms before a credit spend or job: recipient roles, payloads, modes, prices and caps, plus `anonymity.transport`, `relay`, `funding` and `contextLinkage`. `readersOfFullPrompt` remains a floor on distinct recipients and operators across all modes. `recipients[].operatorReadable` is false only for attested recipients; `counts.operatorReadable` drives the banner, alongside `counts.attestedRecipients`. An attested request fails closed unless every plaintext recipient is attested. A change to the node, model, scope, price, cap or reader set requires a new confirmed sheet.

### draft node

A draft node is the node, in the experimental cross-node speculation spike, that proposes draft tokens for a target node to score. It receives the full prompt, so it is a full-prompt reader, and its credit-funded session on the draft model is billed for the acknowledged draft tokens it delivers, including drafts the target rejects. The reference client refuses the spike under mainnet parameters; it runs only with testnet-only, non-normative prices, and no WAN speed-up is promised.

### dust

Dust is `pendingWei` minus the value of the notes minted by `claimChange`. It is credited once to `balances[node]`, then `pendingWei` becomes zero. The reference client decomposes change greedily, leaving dust below the smallest denomination. An empty change list is the dust-only branch.

### embedded wallet

An embedded wallet is a provider-hosted account opened with an email, social or passkey identity. In this proposal it is an optional funding-surface convenience, proposed and not adopted, that signs `depositNote`, `ragequit` and `withdraw`; only if the user opts in does it also sign account setup, bounded swaps or intents in its own account, and a deposit-key grant and its revocation ([ADR 0016](adr/0016-funding-edge-and-deposit-key.md), proposed). The deposit key signs only `depositNote`. No account key, deposit key or login ever signs a voucher, envelope, spend, close or `claimChange`, and none is sent to a node or a relay. It never pays a node or relay and is never in the spend path. A researcher analysis, not upgraded here, holds that the provider can map the login identity to the deposit address (evidence register §4, client UX research 2026-10-15, [U]). The note vault is never derived from, wrapped by, stored with or recoverable through it. Candidates are recorded, none selected ([ADR 0017](adr/0017-accounts-and-decentralized-access.md), proposed; no adopting CIP yet).

### escrow

Escrow is the non-upgradeable `SessionEscrow` contract holding notes and sessions. For a credit session, `nodeCredited + relayCredited + remainingLockedWei + pendingWei + mintedChangeValue = depositWei`; remaining locked value is `depositWei − settledWei` while open or closing and zero after settlement, and node credit includes dust exactly once. Settlement leaves unused value in `pendingWei` for `claimChange`, without a wallet refund. Only `withdraw()` sends internal balances as ETH. The legacy wallet path remains specified for direct callers and is absent from the reference client.

### execution feature

An execution feature is one of `collective_answer`, `parallel_planning`, `task_decomposition`, `model_sharding` and `cross_node_speculation`, chosen on the client per request and never stored on-chain. The empty set is single-node execution, which is the default. Every non-empty set is opt-in per request and is listed on the disclosure sheet, and these features are orthogonal to the privacy modes of each session.

### gateway key configuration

The gateway key configuration is a node’s registered `ohttpKeyConfig`, used for the outer OHTTP hop. Every user checks the same published configuration to avoid individual key tagging. Relays hold no OHTTP gateway key. In attested mode the gateway and job HPKE keys are generated inside the TEE and both are bound into its quote.

### HPKE

HPKE in this proposal is RFC 9180 base mode with X25519, HKDF-SHA256 and ChaCha20-Poly1305, used in both directions: the client seals the job to the node's registered key, and the node seals each output chunk to that job's client key. Base mode does not authenticate the sender, so every job envelope also carries a signature by the session signer over the ciphertext. Client encryption keys come from the operating-system random source and are never derived from the wallet key.

### inference payment

The inference payment is cumulative ETH for tokens: `paymentWei = (priceInPerMillion * inputTokens + priceOutPerMillion * outputTokens) / 1000000`, with integer floor division and the session’s copied prices. Credit-session payouts split between relay and node: the first `relayFeeWei` of settled value goes to the relay, the rest to the node. This is distinct from L2 gas; the node bears spend gas and reflects it in its offer. The protocol fee is 0, and a signed voucher is not reversed.

### L2 gas

L2 gas is the Arbitrum One fee for chain transactions such as depositing a note, spending it, settling, claiming change and withdrawing a balance. It does not buy model tokens. The node bears credit-spend gas and reflects it in its offer; the client shows applicable gas estimates separately from the inference cap. Credit sessions cannot be topped up.

### maintainer

A maintainer is a person with merge authority, and none is seated. A maintainer is seated, and a maintainer is removed, only by a CIP that becomes Final. Until that CIP is Final, nobody may merge, execute a timelock or take an emergency action, and names written in a Draft do not seat anyone.

### manifest hash

The manifest hash is the SHA-256 of the canonical JSON manifest, which names the weight files and their hashes, the pinned tokenizer, the quantization, the context limit and the license file. The model id is keccak256 of that manifest hash, so a different manifest is a different model. In v1 only the governance timelock may register or update a model, and with nobody seated there is no mainnet registration.

### model sharding

Model sharding (`model_sharding`) is the experimental Phase 3 spike in which disclosed network nodes perform all model computation, including embeddings and the output layer. Every holder is an unpaid volunteer reader without a session. The client mediates stage boundaries, transport and sampling decisions, but runs no model computation. Activations travel through a relay, OHTTP-encapsulated to each holder’s registered `ohttpKeyConfig`, without an inner job HPKE envelope. The reference client refuses this spike under mainnet parameters; loss of a holder restarts generation on a new chain from the sheet, and no performance is promised.

### model tier (T0–T4)

A model tier partitions the manifest's parameter count: T0 is at most 4B; T1 is more than 4B and at most 8B; T2 is more than 8B and at most 32B; T3 is more than 32B and at most 70B; T4 is more than 70B. An 8,000,000,000-parameter model is T1. A tier labels the price band, it is not a hardware class, and it does not decide which node may serve the model.

### node

A node is the open-source Rust process an operator runs to load models and serve inference, with pluggable backends. In v1 the node's identity is the operator's address, one node per address. In standard mode that node sees the prompt in plaintext; it signs receipts, checks vouchers, and keeps every HPKE key used by a session that is not yet settled.

### note

A note is a fixed-denomination credit represented by a commitment in SessionEscrow’s denomination group and a client-held secret. Every deposit and change note uses a fresh Semaphore identity, stored durably before its `uint256` commitment is published. The escrow’s `noteSeen` rejects commitments previously used in any group. Identity reuse can make another note unspendable or link groups; losing the secret loses the note.

### nullifier

A nullifier is the public single-use identifier proved for a note under the fixed scope `keccak256(chainId, escrow, denominationIndex)`. SessionEscrow maintains its own nullifier set, trees and root window and calls only the stateless Semaphore v4 verifier. A consumed nullifier cannot fund another session or ragequit. The contract computes the scope and message itself as specified in ADR 0011.

### offer

An offer is the registry entry `prices[modelId] = (priceInPerMillion, priceOutPerMillion, modelBenchmarkHash)` with a non-zero `modelBenchmarkHash`. `updateNode` replaces the whole list: it emits `OfferSet` for every model added or changed, and a cleared `OfferSet` with zero prices and a zero `modelBenchmarkHash` for every model removed, and clearing is always allowed. A hardware-class change revalidates every listed offer against the new class's bands and reverts if any price sits outside its band.

### on-ramp

An on-ramp is a hosted service, proposed and not adopted, that sells ETH on Arbitrum One for fiat and delivers it to an address the buyer controls after the provider's KYC or identity step. It never delivers to the escrow and never calls `depositNote`. `depositNote` credits the public-exit allowance (`depositedWei`) of its caller, and `ragequit` lets an address exit only up to its own allowance and only with a valid note proof bound to that address; it does not bind a note to its original depositor. A deposit made by anything other than the user's own account would credit that address's allowance instead, and the user could not ragequit that value. It never pays a node or relay and is never in the spend path. A stablecoin bought this way is converted to ETH in the user's own account before `depositNote`. Settlement stays ETH. Coinbase's Layer 2 table lists ETH on Arbitrum, and the MoonPay and Transak currency listings include ETH on Arbitrum (evidence register §15, client UX research 2026-10-15, [V]; the Transak currencies API was not independently re-fetched). The Coinbase Guest Checkout, MoonPay and Transak terms each state that the buyer owns or controls the destination wallet (evidence register §16, client UX research 2026-10-15, [V]; the Coinbase Guest Checkout terms were not independently re-fetched). Each researched provider documents a KYC or identity step (evidence register §16, client UX research 2026-10-15, [V] per provider). These are provider statements, not a legal conclusion, and whether they apply is an open review item. Candidates are recorded, none selected. [ADR 0016](adr/0016-funding-edge-and-deposit-key.md) proposes this, and there is no adopting CIP yet.

### operator

An operator is the person who runs a node and the Ethereum address that registers it, posts the bond and is paid for its sessions; the operator is the payee, and a pool is not. In standard mode the operator of the chosen node can read the prompt, because the node decrypts it.

### orchestrator

The orchestrator is open-source control logic in the client SDK. On-device assessment uses rules and user choices, with no model computation. Model-based planning, review, merging and synthesis run on disclosed network nodes after user confirmation. Planner output is untrusted data and never authorizes a recipient, payment, tool or external action.

### orchestrator node

An orchestrator node is an optional network node for model-based planning, merging or synthesis, paid through its own credit-funded session. It receives requests through a relay and holds no session signer, takes no cut and custodies no other session. It is a disclosed full-prompt recipient; operator readability depends on its mode. It is never mandatory.

### plan

A plan is an off-chain DAG of waves held as client-side JSON, not a contract or registry entry. Every paid node-and-model pair has a credit-funded session. The user confirms the model and disclosure sheet before the spend; a judge’s rank cannot authorize execution. Unpaid volunteer holders in the sharding spike are the stated exception to paid sessions.

### pool

A pool is the set of nodes with a current offer `prices[modelId]` carrying a non-zero `modelBenchmarkHash`, enumerated off-chain from `OfferSet` events. It is not a contract and not a payee; the chain stores offers and sessions, and it never stores a pool list. Any node may offer any registered model it can load, and `maxTier` is informational and is never read as a gate by `openSession` or `openSessionFromCredit`.

### ragequit

Ragequit is a public, linkable exit for a note proved in a denomination group. It credits `balances[msg.sender]` only while `depositedWei[msg.sender][denominationIndex] − ragequitWei[msg.sender][denominationIndex]` covers that denomination, consumes the nullifier and increases the caller’s ragequit total. It cannot distinguish deposit notes from change notes or identify a note’s original depositor. The caller withdraws the balance through `withdraw()`.

### re-wrap

Sharing a context re-wraps exactly the granted versions’ keys from the identity-key vault to the recipient node’s job HPKE key; stored blobs remain ciphertext. Nodes never exchange plaintext or keys. Moving a context requires a context-key-signed grant and a newly confirmed disclosure sheet for the recipient; the wallet does not sign the grant.

### relay

A relay is a registered, bonded transport operator distinct from the chosen node operator. The relay banner, normative and copied verbatim from ADR 0010, is: “The relay sees your network address and not your prompt. The node sees your prompt and not your network address.” The node is the OHTTP gateway; the relay has no gateway key. The client selects a relay at random and fails closed if none exists. Registration prevents one address holding both roles, but cannot detect one person using two addresses. A relay’s copied fee comes from the session’s settled value; collusion and timing remain risks (evidence register §15–§16, [V]/[U]).

### reputation event

A reputation event is an off-chain note, or a reading of public chain events, that records how a session ended or that a user disputes a node's behaviour. It is not a slash, not a refund and not a reversal of a signed voucher. In v1 the user's remedy is to stop signing further vouchers and to close the session.

### reviewer

A reviewer receives the prompt together with the material it critiques: anonymized answers in a collective answer, or a sub-task output that the client treats as containing prompt text unless the client has checked that it does not. In a collective answer the review is blind and is repeated with positions swapped, and disagreement between those two passes is expected and does not by itself make the synthesis incomplete. The reviewer is paid through a credit-funded session, and a low score does not change that payment.

### session

A session binds one node, model, privacy mode and fresh session signer, and may run many jobs one at a time. The reference client spends a note through `openSessionFromCredit`, submitted by the node or a broadcaster: `user = address(0)`, `funding = credit`, and `depositWei = maxSpendWei` equals the denomination. It records the relay and copied relay fee, and cannot be topped up. The node can close it, or any broadcaster can submit `closeSession` with a session-signer signature; anyone can finalize after the deadline. Settlement records unused value as `pendingWei` for `claimChange`, even in settled status. If both node and signer are gone it stays open. The legacy wallet session is specified only for direct callers.

### session signer

The session signer is a fresh application key per session, never reused or derived from the wallet, recorded by `openSessionFromCredit`. It signs job envelopes, vouchers, credit-session close authorizations and `claimChange` authorizations. It signs no context grants and is never delegated to an orchestrator node. A stolen signer can authorize vouchers up to the cap or redirect change; closing does not stop vouchers before the close deadline. The wallet is not prompted for each session or chunk. It is not the deposit key of ADR 0016, which signs only depositNote.

### settlement layer

The settlement layer is Arbitrum One, and the v1 contracts are Solidity on the EVM: `NodeRegistry`, `ModelRegistry`, `ContextRegistry` and `SessionEscrow`. Stylus is not the v1 path, because new Stylus activations are paused and no reopening date is recorded (evidence register §1, [V]). Inference runs off-chain; the chain records offers, optional context anchors, notes and sessions, and it does not run the model.

### shard holder

A shard holder is a disclosed unpaid volunteer reader in the experimental sharding spike, including nodes computing embeddings and the output layer. It holds no session and receives no voucher. The client sends activations only to holders on the sheet, through a relay and OHTTP to each holder’s registered `ohttpKeyConfig`, with no inner job HPKE envelope and no direct client-to-holder path.

### speculative decoding

Local speculative decoding inside one node is an engine detail: it adds no reader, and it stays off in verifiable mode. Cross-node speculative decoding is an experimental Phase 3 spike with one job per session on a draft node and one on a target node, both of which can read the prompt; rounds are frames inside that job, the prompt is input-billed once per job, and draft probability distributions travel as sealed metadata that are not billable tokens. The reference client refuses the spike under mainnet parameters, no WAN speed-up is promised, and the spike is incompatible with verifiable mode because a speculative engine does not guarantee byte-identical output.

### splits list

The splits list is the set of claims a synthesizer reports that the answers disagree on, each claim tied to the stable answer ids that hold each side. An empty splits list is valid and means the synthesizer found no such claim. The client marks the result contested when the splits list is non-empty or the agreement level is low, and that label does not change payment.

### standard mode

Standard mode (mode 0) is the anonymous default. The normative banner is: “This node can read your prompt and your answer. It should not learn who you are.” The chosen node also reads granted context and can retain content. Relays hide the client’s network address from it, credits remove the payer from the session, and context keys avoid wallet-labelled grants. Identifying content and traffic correlation remain risks (evidence register §16, [V]/[L]).

### synthesizer

A synthesizer is a disclosed network node that receives the prompt, answers and critiques and returns a merged answer, splits list and agreement level. It is a full-prompt recipient paid through a credit session; operator readability depends on its mode. The client performs no model synthesis. Synthesis is incomplete when a required field is missing or malformed.

### verifiable mode

Verifiable mode (mode 2) is opt-in re-execution by a user-chosen second node under a demonstrated deterministic profile. The normative banner is: “This node and the verifier you chose can read your prompt. They should not learn who you are.” The verifier uses a relay and its own credit session and adds a disclosed reader. Mode is public; mismatch does not change payment. It is no content-privacy upgrade, is not combined with attested mode in v1, and is incompatible with cross-node speculation.

### voucher

A voucher is the EIP-712 typed data `Voucher(bytes32 sessionId,uint64 seq,uint256 cumulativeWei,uint64 inputTokens,uint64 outputTokens,bytes32 outputCommitment,bool isFinal)`, signed by the session signer, with cumulative token counts and a `seq` that starts at 1 and strictly increases. `isFinal` means only that the client closes the session; `redeemVoucher` rejects a final voucher, and `closeWithVoucher` or `finalize` record unused credit-session value in `pendingWei` for a later `claimChange`; only legacy wallet sessions credit a user refund. A signed voucher is not reversed; `outputCommitment` is keccak256 of the session's random 32-byte commit key, the session id, that voucher's seq and the transcript hash, it is not checked on-chain, and opening the commit key discloses that session's output.

### wallet owner

The wallet owner is the account that publicly deposits ETH through `depositNote` and may use the public, deposit-bounded `ragequit` exit followed by `withdraw()`. Its association with context keys stays only in the vault and backup. The reference client does not ask it to sign per-session prompts, vouchers or context grants; fresh session signers and independent context keys handle those. Wallet-funded `openSession` and `topUp` remain legacy direct-caller interfaces, absent from the reference client.

### wave

A wave is one topological level of a plan: tasks in the same wave have disjoint outputs and do not depend on one another, so they can run at the same time on different sessions. The `wave` field is advisory metadata, it is not bound into the job's associated data, and a node must not rely on it. One session still runs only one job at a time, so two tasks that share a session run one after the other unless the sheet lists a second session.

### working group

A working group reviews documents in public and recommends changes. The groups named in this proposal are Protocol, Node, Cryptography, Contracts, Applications and Documentation. A working group does not decide, seats no chair and carries no token weight; a CIP decides.
