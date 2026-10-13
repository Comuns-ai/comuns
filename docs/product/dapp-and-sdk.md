# Dapps and SDK — chat on top of the session protocol

Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12

**Reference:** docs/protocol/off-chain-api.md, docs/protocol/contracts-and-settlement.md, docs/security/privacy-and-contexts.md, docs/economics/cost-and-pricing.md, docs/node/node-design.md

---

## 1. Summary

This document proposes a reference chat client and a TypeScript SDK for Comuns, the community proposal for open-source decentralized LLM inference settled on Arbitrum One. Nothing described here exists yet; no package is published and the package name is undecided.

The client is deliberately thin. It owns three things and nothing else: the user's wallet connection (EIP-1193, the only account there is), an app-managed HPKE keypair that is never the wallet key, and a local store of encrypted contexts. Everything else is the protocol: sessions and vouchers from docs/protocol/contracts-and-settlement.md, envelopes and frames from docs/protocol/off-chain-api.md, modes, features and the disclosure sheet from docs/security/privacy-and-contexts.md.

What the user does, in order: connect a wallet on Arbitrum One, choose an RPC endpoint, **pick a model first**, then pick one node from that model's pool (or confirm a ranked set from it), choose the execution features (none by default, which means single-node), read the disclosure sheet and the plaintext banner, set a cap, sign `openSession` once, and chat. Every chunk is paid by an automatic voucher signature within the cap; no transaction is sent per message; the service cost is shown in ETH as a cap and a running total, separate from the L2 fee; the protocol fee is 0 and there is no token. Granting a context to a node asks the wallet for one typed-data signature (batched per request), because a grant is signed by the wallet that owns the context. Ending the session cooperatively signs one final voucher so the node settles and the refund is credited in one transaction; the user can also close unilaterally through the contract without a voucher. Multi-node features never start without the user signing after the disclosure sheet for that request.

## 2. Scope

This is one reference client. **The client is not the protocol.** Anyone may write another dapp against the same contracts and the same off-chain API; the community categories in section 10 are examples. What this document fixes is what any honest client must show and must refuse (sections 5, 8 and 11), because the protocol's privacy promises depend on the client doing so (docs/security/privacy-and-contexts.md R5).

Binding decisions carried in, all PROPOSED:

| Decision | Value |
|---|---|
| Account | The wallet is the only account: no email login, no password, no seed-phrase collection, ever |
| RPC | User-chosen; the client reads `NodeRegistry` and `ModelRegistry` through it or any community indexer; no project-operated relay or matcher |
| Selection | Model-first; the pool of a model is every node whose `prices[modelId]` has a non-zero `modelBenchmarkHash`; the user picks a node or confirms a ranked set; any class may appear in any pool; `maxTier` is informational |
| Encryption | HPKE in the client with an app-managed keypair; `eth_getEncryptionPublicKey` and `eth_decrypt` are forbidden |
| Signing | One wallet signature per session (`openSession`); vouchers are EIP-712 signatures by the app-generated `sessionSigner`, automatic within the cap; the wallet is never prompted per chunk. A context grant is EIP-712 typed data signed by the wallet that owns the context, never by `sessionSigner` — one wallet prompt per request where the grants can be batched, and the UI says so |
| Payment | ETH, protocol fee 0, no token; never hidden inside L2 gas; pull payments — refunds and payouts are balances the user withdraws |
| Orchestration | Default is the client's own SDK code; an optional orchestrator node is reached through an ordinary session after its own disclosure; `sessionSigner` is never delegated in v1 |
| Contexts | Local-first, many per wallet, encrypted per version, switched between nodes by re-wrapping keys, never uploaded in plaintext |

Out of scope: the node software (docs/node/node-design.md), prices and bands (docs/economics/cost-and-pricing.md), the orchestration pattern itself (docs/protocol/orchestration.md), verification (docs/security/inference-verification.md).

## 3. SDK surface

A sketch of the call shapes, not an API freeze. The package name is undecided; wallet access is EIP-1193; HPKE uses WebCrypto X25519 where the platform exposes it and otherwise a WASM build of the same RFC 9180 implementation the reference node uses, so that client and node share one cipher suite (docs/security/privacy-and-contexts.md §4).

```typescript
// Package name undecided. Everything below is a call-shape sketch.
import type { EIP1193Provider } from "eip1193-types-placeholder";

type Hex = `0x${string}`;
type Mode = "standard" | "attested" | "verifiable";
type ExecutionFeature =
  | "collective_answer"
  | "parallel_planning"
  | "task_decomposition"
  | "model_sharding"        // experimental, Phase 3 spike
  | "cross_node_speculation"; // experimental, Phase 3 spike
type HardwareClass = "S" | "M" | "L" | "X";

interface ConnectOptions {
  provider: EIP1193Provider;          // the wallet; the only account
  rpcUrl: string;                     // user-chosen Arbitrum One RPC
  indexerUrl?: string;                // optional community indexer, never required
  orchestratorNode?: Hex;             // optional: send plan requests to a node advertising roles.orchestration
}

interface PoolEntry {
  node: Hex;                          // operator address
  endpoint: string;
  class: HardwareClass;               // shown as "S Small" | "M Mid-size" | "L Large" | "X Largest"
  maxTier: "T0" | "T1" | "T2" | "T3" | "T4"; // informational only
  modes: Mode[];
  priceInPerMillion: bigint;
  priceOutPerMillion: bigint;
  modelBenchmarkHash: Hex;            // non-zero: in the pool
  measuredTokensPerSecond?: number;   // client-measured, optional
  reputation?: number;                // from an indexer the user chose, optional
}

interface Assessment {
  sizeClass: "small" | "medium" | "large";
  riskFlags: Array<"privacy-sensitive" | "needs-exact-math-or-code" | "time-critical" | "decomposition-poor-fit">;
  recommendedExecutionFeatures: ExecutionFeature[];   // [] means single-node
  subTaskModelSuggestions?: Array<{ taskHint: string; modelId: Hex }>;
  source: "local-heuristics" | "planner-session";
}

interface Plan { /* the DAG of docs/protocol/orchestration.md §6 */ planId: Hex; version: number; tasks: unknown[] }

// Sessions are keyed by the pair: a node may serve two models, and two nodes may serve one model.
type SessionMap = Record<Hex /* node */, Record<Hex /* modelId */, Hex /* sessionId */>>;
// Equivalent single-key form, if a flat map is preferred: Record<`${Hex}:${Hex}` /* `${node}:${modelId}` */, Hex>.

interface ContextGrant {
  contextId: Hex; fromVersion: number; toVersion: number; expiresAt: number; nodeKeyHash: Hex;
  wrappedKeys: string[];              // K_fromVersion … K_toVersion, each HPKE-sealed to the node's registered key
  ownerSignature: Hex;                // EIP-712 typed data signed by the wallet that owns the context, never by sessionSigner
}

interface DisclosureSheet {
  requestId: Hex; planId: Hex; version: number;
  recipients: Array<{ node: Hex; operator: Hex; roles: string[]; modelId: Hex; mode: Mode; receives: string[];
                      priceInPerMillion: bigint; priceOutPerMillion: bigint; capWei: bigint }>;
  counts: { fullPrompt: number; subTask: number; otherAnswers: number; activations: number; draftTokens: number };
  readersOfFullPrompt: { nodes: number; operators: number };
  totalCapWei: bigint;
  l2GasEstimate: bigint;              // shown separately, never folded into totalCapWei
  experimental: boolean;
}

interface ComunsClient {
  connect(opts: ConnectOptions): Promise<{ account: Hex; chainId: number }>;
  listModels(): Promise<Array<{ modelId: Hex; tier: string; licenseSpdx: string; commercialHosting: boolean }>>;
  listPool(modelId: Hex): Promise<PoolEntry[]>;           // model-first: every node with a non-zero modelBenchmarkHash for modelId
  listNodes(): Promise<PoolEntry[]>;                       // all registered nodes, for the operator directory view

  openSession(args: {
    node: Hex; modelId: Hex; mode: Mode;
    depositWei: bigint; maxSpendWei: bigint;
    expectedPriceInPerMillion: bigint; expectedPriceOutPerMillion: bigint;   // from the confirmed sheet
  }): Promise<{ sessionId: Hex; sessionSigner: Hex }>;     // one wallet signature; sessionSigner is app-generated

  chat(args: {
    sessionId: Hex; prompt: string; contextGrant?: ContextGrant;
    params?: { maxOutputTokens?: number; temperature?: number };
    signal?: AbortSignal;                                   // the Stop control: aborting stops voucher signing
  }): AsyncIterable<{ text: string; cumulativeOutputTokens: number; runningTotalWei: bigint }>;

  assess(args: { prompt: string; contextTokens: number; userChoice?: ExecutionFeature[] }): Promise<Assessment>;
  // Local heuristics only: never contacts a node. Returns a size class, risk flags and a recommended feature set.

  plan(args: { requestId: Hex; prompt: string; assessment: Assessment; plannerSessionId?: Hex }): Promise<Plan>;
  // Returns a plan DAG. May call a planner session the user approved after a first disclosure sheet.

  disclosureSheet(args: { requestId: Hex; plan?: Plan; mode: Mode; features: ExecutionFeature[] }): Promise<DisclosureSheet>;
  // Returns the table the UI must show before the user signs anything for this request.

  run(args: {
    requestId: Hex; sheet: DisclosureSheet; confirmation: { version: number; signedAt: number };
    sessions: SessionMap;                                   // keyed by the pair (node, modelId), never by a single Hex
    signal?: AbortSignal;
  }): Promise<{ merged: string; splits: Array<{ taskId: Hex; node: Hex; modelId: Hex; answerId?: string; text: string; disagreement?: string }> }>;
  // Executes a confirmed plan or collective request across the sessions it names; returns the merged result with the splits.
  // answerId is the stable anonymous ID (A1…Ak) of a collective answer, assigned once per request; every critique and split refers to it.

  onSignVoucher(hook: (v: { sessionId: Hex; seq: number; cumulativeWei: bigint; inputTokens: number; outputTokens: number }) => boolean): void;
  // Called before every automatic signature; returning false stops signing (used by the Stop control and the cap check).

  contexts: {
    create(args: { name: string; plaintext: Uint8Array }): Promise<{ contextId: Hex; version: number; contentHash: Hex }>;
    update(args: { contextId: Hex; plaintext: Uint8Array }): Promise<{ version: number; contentHash: Hex }>;
    grant(args: Array<{ contextId: Hex; fromVersion: number; toVersion: number; node: Hex; expiresAt: number }>): Promise<ContextGrant[]>;
    // Wraps the granted versions' keys to each node's registered key and asks the WALLET to sign the grants as EIP-712
    // typed data (docs/security/privacy-and-contexts.md §7) — one wallet prompt for the whole array where the wallet
    // supports it; sessionSigner never signs a grant. The UI says a wallet signature is coming before it is requested.
    revoke(args: { contextId: Hex; node: Hex }): Promise<void>;   // stops future grants; cannot un-read the past
    exportBackup(passphrase: string): Promise<Uint8Array>;         // identity key + every key-wrap record; no ciphertext
    importBackup(file: Uint8Array, passphrase: string): Promise<void>;
  };

  closeSession(args: { sessionId: Hex }): Promise<{ finalVoucherSeq: number }>;
  // Cooperative close: signs the final voucher from the SDK's own voucher log; the node calls closeWithVoucher and the
  // refund is credited in that transaction. Refuses to run when the log for the session is missing.
  closeSessionUnilateral(args: { sessionId: Hex }): Promise<Hex>;
  // Unilateral close: the contract's closeSession directly, one wallet transaction, no voucher signed; used after a lost
  // voucher log, a vanished node, or a price mismatch. The node may still redeem its highest voucher until closeDeadline.
  finalize(args: { sessionId: Hex }): Promise<Hex>;        // after closeDeadline; credits the remainder to the user
  withdraw(): Promise<Hex>;                                 // pulls balances[user] in one transaction
}
```

Notes on the sketch:

- `assess` runs on the user's device and never contacts a node. `plan` contacts a node only when the user has opted into orchestration and approved a planner session after its own disclosure sheet (docs/protocol/orchestration.md §5).
- `run` refuses to dispatch any job for a `requestId` without a recorded confirmation of the current sheet version; it binds `requestId` and `sheetVersion` into every envelope's AAD (docs/security/privacy-and-contexts.md §8.3). The order is fixed: pick models → see the sheet → confirm → sign `openSession`(s). Any change of node, model, data scope, price, cap or reader set after a confirmation creates a new sheet version that must be confirmed again; a client never confirms a sheet and then changes models under it. If verifiable mode (or any other extra reader) is wanted on the result, that verifier is on the sheet before signing; adding one later is a new sheet version and a new confirmation.
- The SDK signs vouchers only from its own voucher log and never above the effective cap `min(depositWei, maxSpendWei)`; the remaining allowance it shows is that cap minus the highest `cumulativeWei` it has signed, redeemed or not. It never adopts a node's reported totals. There are two ways to close: the cooperative `closeSession` (a final voucher, then the node's `closeWithVoucher`) and the unilateral `closeSessionUnilateral` (the contract's `closeSession`, no voucher, then `finalize` after `closeDeadline`). If the log for a session is lost the SDK signs nothing more there — it cannot build a final voucher without its own counts and must not build one from the node's — so it uses only the unilateral close; further work needs a new session, and because a new session is a new deposit and cap, a new disclosure sheet version is shown and confirmed before that `openSession`.
- Sessions are keyed by the pair `(node, modelId)` (`SessionMap`): one node may serve two models of a plan, and two nodes may serve the same model, so a single `Hex` key would collide and route a job onto the wrong session. A session runs one job at a time (`maxConcurrentJobsPerSession = 1`, docs/protocol/off-chain-api.md §3); `run` dispatches a wave's tasks concurrently only across different sessions and runs two tasks that share a session one after the other, unless the sheet lists a second session for that pair.
- Price checks read the chain, not the node: after `SessionOpened` the SDK compares the prices copied into the session on-chain with the confirmed sheet; prices a node reports in `welcome` are informational and never trigger a close.
- `orchestratorNode`, if set, sends the plan request to a node that advertises `roles.orchestration` through an ordinary session, after a disclosure sheet saying that node will see the full prompt and the plan. The orchestrator node holds no `sessionSigner`; the user's client still opens every downstream session and signs every voucher.
- The compatibility adapter (section 10) that exposes the widely used chat-completions request shape of hosted inference APIs is a wrapper over `chat`; it encrypts on the client side before any untrusted hop and never forwards plaintext to a gateway.

## 4. Screens and flow

Sixteen named screens. Every screen is reachable by keyboard (section 9).

| # | Screen | What it does | What it must show |
|---|---|---|---|
| 1 | **Connect wallet** | EIP-1193 connect; checks the chain is Arbitrum One (or Arbitrum Sepolia in developer mode) | no email, no password; "your wallet is your account" |
| 2 | **Network and RPC** | The user enters or picks an RPC endpoint and optionally an indexer; the client never defaults to a project-run endpoint | which endpoint will see the user's reads |
| 3 | **Model picker** | Lists registered models with tier label, license and `commercialHosting`; the user picks a model first | models with `commercialHosting = false` are shown as not available for paid sessions |
| 4 | **Model pool** | The nodes in the chosen model's pool, each with plain class label **S Small**, **M Mid-size**, **L Large**, **X Largest**, prices, modes, measured speed and reputation; the user picks one node or confirms a ranked set | "a stronger class costs more for the same model"; `maxTier` as information; attested filter copy from section 5 |
| 5 | **Execution features** | Single-node is selected by default; the user may add collective answer, task decomposition or parallel planning; sharding and cross-node speculative decoding are labelled experimental and hidden when no testnet price exists | the reader count that each feature adds, before anything is chosen |
| 6 | **Plan review** | For task decomposition: the DAG, each task's model and node, the waves; the user confirms every `modelId` and node, or forces single-node. This comes **before** the sheet: models and nodes are fixed here, then disclosed | every `modelId`; the planner's output is data, never authority |
| 7 | **Disclosure sheet** | The table of docs/security/privacy-and-contexts.md §8.3, generated from the sheet JSON for the models and nodes confirmed on screen 6: which nodes see the full prompt, a sub-task, other answers, activations or draft tokens, with the counts, prices and caps; a verifier, if verifiable mode is wanted on the result, is already listed | nothing proceeds until the user signs after this sheet; any later change of node, model, scope, price, cap or reader set returns the user to this screen with a new version |
| 8 | **Plaintext banner and cap** | The banner of section 5, the cap in ETH, the deposit, the L2 fee estimate shown separately | the single-node or multi-node banner; "cap" and "running total" are service cost, not gas |
| 9 | **Confirm deposit** | The one wallet signature: `openSession` (one per session in a plan), under the sheet version confirmed on screen 7 | what is being signed: node, model, mode, cap, prices |
| 10 | **Chat** | Streaming answer, running spend, a **Stop** control that stops voucher signing | running total vs cap; truncated answers marked |
| 11 | **Disagreement view** | For collective answers: each answer under its stable anonymous ID (A1…Ak, assigned once per request), each critique, the synthesis, and any objection; never a ranked list the client auto-executes | the disagreement is visible, never hidden inside the synthesis; every critique and split names the stable ID |
| 12 | **Switch node** | Closes the current session (final voucher) and opens a new one on another pool node; re-wraps context keys to the new node (a wallet signature for the new grant) | that this is a new session with a new reader; the sheet is shown again |
| 13 | **Close and refund** | Cooperative close signs the final voucher; a unilateral close (no voucher: the contract's `closeSession`, then `finalize` after `closeDeadline`) is offered when the node is gone or the voucher log is lost; shows `settled` when `SessionSettled` is seen and the refund as a withdrawable balance | refund is a balance to pull with `withdraw()`, not an automatic transfer; which of the two closes is being done |
| 14 | **Context sidebar** | Create, edit (new version), grant, revoke, see which node holds which versions | local-first; a grant is per node and per version range and is signed by the wallet (one typed-data prompt per request, batched where the wallet allows) — the screen says so before the prompt appears |
| 15 | **Spend history** | Per session: signed total, redeemed total, refund, L2 fees paid, state from docs/protocol/off-chain-api.md §12 | service cost and gas as separate columns |
| 16 | **Key backup and restore** | Export the encrypted backup (identity key and every key-wrap record); import on a new device | the backup holds no ciphertext; keep a context host or a second device |

A seventeenth, **Withdraw balance**, is a one-button screen that pulls `balances[user]` from `SessionEscrow` (and, for operators using the same client, from `NodeRegistry`).

The single-node flow from connect to streamed answer:

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dapp (SDK, sessionSigner, HPKE keys)
    participant W as Wallet (EIP-1193)
    participant R as RPC / indexer (user-chosen)
    participant E as SessionEscrow
    participant N as Node (from the model's pool)
    U->>D: Connect wallet, set RPC
    D->>W: eth_requestAccounts, chainId check
    U->>D: Pick model
    D->>R: ModelRegistry, OfferSet events → pool of modelId
    D-->>U: Model pool: nodes with class S/M/L/X, prices, modes, speed, reputation
    U->>D: Pick node; execution features = none (single-node)
    D-->>U: Disclosure sheet v1 + plaintext banner + cap
    U->>D: Confirm (sheet v1 recorded)
    D->>W: openSession(node, modelId, mode, sessionSigner, maxSpendWei, expectedPriceIn, expectedPriceOut) + deposit
    W->>E: one transaction
    E-->>D: SessionOpened; D compares the on-chain copied prices with sheet v1
    D->>N: hello (sessionSigner signature); welcome (its prices are informational)
    U->>D: Type prompt
    D->>N: job envelope (HPKE, commitKey, AAD with requestId and sheetVersion 1, signed)
    N-->>D: input receipt
    D->>N: input voucher (automatic, counts match)
    loop per chunk
        N-->>D: frame + chunk receipt
        D-->>U: streamed text, running total
        D->>N: cumulative voucher (automatic, within cap)
    end
    U->>D: Close session
    D->>N: final voucher (cooperative close)
    N->>E: closeWithVoucher → node credit + user refund credited
    D-->>U: Settled; refund withdrawable
    Note over D,E: unilateral close instead: D sends closeSession (no voucher), then finalize after closeDeadline
```

## 5. The plaintext banner

The banner is shown on screen 8 and again at the top of the chat view. It is not dismissible until read (keyboard: focus lands on it; screen readers announce it). The proposed copy is exact; a client may add but not remove sentences.

**Single-node default (standard mode):**

> **Standard mode: the node you pick can read this prompt.**
> The node *{node name}* run by operator *{operator address}* will read your prompt, the context versions you grant it and the answer in plaintext. Other nodes, the Arbitrum chain, your RPC provider and anyone watching the network cannot: they see only encrypted data. What is public on-chain: your address, the node, the model, the sizes of your messages and the prices. Nobody can give you a refund for a bad answer; you pay for the chunks you receive until you press Stop.

**Attested mode filter copy (screen 4 and the banner):**

> Attested nodes run inside a trusted execution environment and prove which software they run before you send anything. **A TEE does not stop an operator with physical access to the machine.** If you need protection against the operator itself, run the model locally.

**Verifiable mode:**

> A second node you choose will also read this prompt and re-run it to check the answer. That is two readers, not one. Both nodes can see on-chain that this session is checked; a node can behave honestly only here and differently elsewhere.

Because a session's mode is public on-chain, verifiable mode checks only verifiable-mode sessions. The client therefore offers, as a separate opt-in, **unannounced spot checks** of standard-mode sessions: the user re-runs a sampled prompt on another node, which then reads it and is disclosed as a reader for that check. This is not a proof either; it is a sample.

**Multi-node variant.** Generated from the disclosure sheet, never hand-written:

> **{readersOfFullPrompt.nodes} nodes run by {readersOfFullPrompt.operators} operators can read this prompt.**
> {for each recipient:} *{node name}* ({roles}) receives {receives list}.
> What each is sent, counting every node once: {counts.fullPrompt} sent your full prompt; {counts.subTask} sent a sub-task that may quote it; {counts.otherAnswers} sent other nodes' answers or outputs. {if activations > 0:} {counts.activations} sent model activations, from which the prompt can be recovered — this is experimental. {if draftTokens > 0:} {counts.draftTokens} sent your prompt plus draft tokens — this is experimental.
> Total cap across all sessions: {totalCapEth} ETH. L2 fees, shown separately: about {l2GasEstimateEth} ETH.
> Nothing is sent to any of these nodes until you sign below.

The headline count is `readersOfFullPrompt`, the floor of nodes that **can read** the prompt; the second line lists payload kinds from `counts`, where each node appears under exactly one kind and `counts.fullPrompt` is only the nodes literally sent the full prompt (docs/security/privacy-and-contexts.md §8.3). The two never add up to each other and the banner never implies they do. `{totalCapEth}` is `totalCapWei ÷ 10^18` and `{l2GasEstimateEth}` is the gas estimate in ETH, both printed as decimals with the unit; raw wei never appears in user-facing copy (section 6).

**No multi-node feature starts without the user signing after that sheet.** The client records the confirmation of the sheet's `version`, binds `requestId` and `sheetVersion` into every envelope's AAD, and refuses to dispatch any job for a request whose current sheet version has no confirmation. If anything changes — a node added or swapped, a model changed, what any node receives widened, a cap raised, a price changed, a reader (such as a verifier) added — the sheet's version increments and the banner is regenerated and shown again before any `openSession` or job under it. The order is always pick models → see the sheet → confirm → sign; the client never confirms a sheet and then changes models. The banner and every table are generated from the sheet JSON and must match it exactly.

## 6. Price and cap display

Two numbers are always separate: **service cost** (ETH paid to nodes through vouchers) and **L2 fee** (gas for `openSession`, `topUp`, `closeSession`, `finalize`, `withdraw`). The client never folds one into the other and never hides the inference payment inside gas.

**Units.** Every amount in user copy is shown in ETH as a decimal with the unit: a wei amount is divided by 10^18 (a cap of 50,000,000,000,000,000 wei is shown as "0.05 ETH", never as "50000000000000000 ETH"), and an L2 gas estimate is shown in ETH with the unit too. Raw wei never appears in user-facing copy; the exact wei is available on request (section 9).

| Shown | Meaning |
|---|---|
| Cap | `min(depositWei, maxSpendWei)` for this session; the most this session can ever pay the node |
| Running total | `cumulativeWei` of the last voucher the client signed; rises chunk by chunk |
| Remaining allowance | the cap minus the highest `cumulativeWei` the client has signed in this session, redeemed or not; never the cap minus `settledWei` |
| Signed but not yet on-chain | the running total minus what `VoucherRedeemed` events show; owed, not yet redeemed |
| Refund | `depositWei − settledWei`, credited at `closeWithVoucher` or `finalize`; withdrawable |
| L2 fee | estimate before signing; actual after inclusion; never part of the cap |

**Cap exhaustion.** The client never signs a voucher above the cap: when the next chunk would take the running total past it, the client stops signing and the node pauses; the chat view shows "cap reached" with two choices: top up (`topUp`, one wallet transaction, raises the cap and the deposit; afterwards the client simply continues with the next chunk voucher) or close. The "re-sign the same totals under a new `seq`" recovery of docs/protocol/contracts-and-settlement.md §8 applies only if a voucher above the old cap had been signed and only partly paid, which this client never does. The answer that was cut off is marked truncated.

**An unfinished, unsigned tail is not a charge for the whole cap.** If the user presses Stop, the connection drops, or the node stops, the user owes exactly what the signed vouchers say — at most the chunks received — and the rest of the deposit returns at settlement. The cap bounds the loss; it is not the price.

**What is never shown as free.** The input voucher is signed before prefill; a prompt that is never answered still cost its input fee. The spend history records it as such. The converse also holds: a prompt the user stops before signing its input voucher costs nothing and its tokens never enter the session's counts — the counts are the totals of the last voucher signed, and an unsigned receipt binds nobody (docs/protocol/off-chain-api.md §8).

## 7. Contexts

Contexts are local-first: transcripts, documents and system prompts live on the user's device, encrypted under a random key per version (docs/security/privacy-and-contexts.md §7), many per wallet. A context is shared with a node by a grant that wraps exactly the granted versions' keys to that node's registered HPKE key; switching node means issuing a new grant to the new node (re-wrapping), never sending plaintext anywhere.

**A grant needs a wallet signature.** The node accepts a grant only if its `ownerSignature` recovers to the on-chain owner of the context — the wallet, not `sessionSigner` (docs/protocol/off-chain-api.md §9). The SDK's `grant()` therefore builds the grants as EIP-712 typed data and asks the wallet to sign them: one prompt per request where the wallet can sign a batch, otherwise one per grant. The UI says so before the prompt appears ("your wallet will ask you to sign the context grant") so the extra signature is never a surprise, and it is the only wallet interaction a chat needs besides `openSession`.

**Ciphertext reaches the node inline.** By default the client uploads the granted versions' ciphertext in the job's own upload frames; an optional `blobUrl` to a public `https` host is allowed only under the restrictions of docs/protocol/off-chain-api.md §9, and a node may refuse it, after which the client re-sends inline.

The client:

- shows, per context, every version, its `contentHash`, which nodes currently hold a grant and until when (`expiresAt`, unix seconds);
- publishes a new version with `setContext(contextId, version, contentHash)` when the user chooses to; on a race with another device it keeps the local edit, rebases on the new head and publishes the next version, telling the user where the edits overlap;
- optionally stores ciphertext and key-wrap records at an owner-chosen host; the registry never holds content;
- exports a backup that contains the identity key and every key-wrap record but no ciphertext. A context whose ciphertext existed only on a lost device is gone even with the backup; the client says so on screen 16 and recommends at least one host or a second device;
- marks revocation honestly: revoking a node stops future grants and makes every later version unreadable to it; it cannot make the node forget versions it already decrypted.

Context tokens are input tokens: granting a 20,000-token context to a job adds 20,000 tokens to the input receipt and the input voucher, and the chat view shows that before the prompt is sent.

## 8. Failure states

What the user sees and what funds are at risk. In every case a signed voucher stands; the user never loses more than the signed total of each session, and never the whole cap for an unsigned tail.

| Failure | What the user sees | Funds at risk |
|---|---|---|
| Node offline mid-stream | the answer stops, is marked truncated after 2 × the node's advertised `maxInterFrameMs` without a frame; the client reconnects for `reconnectWindow` (the node resends from the last frame the client received; identical duplicates are ignored; the client re-sends its latest voucher, a no-op if the node already holds it, and resumes from its own log), then offers Close (cooperative: a final voucher if the node returns; otherwise unilateral: `closeSessionUnilateral` and `finalize` after `closeDeadline`) | chunks already signed for; the deposit remainder returns after the close window |
| Lost voucher log (device reset mid-session) | "This session's records are gone; nothing more will be signed on it." The client uses only the unilateral close (`closeSessionUnilateral`, no voucher), offers `finalize` after `closeDeadline`, and never resumes from the node's figures. Further work needs a new session, which is a new deposit and cap: a new disclosure sheet version is shown and confirmed before that `openSession` | vouchers the node already holds stand; the remainder returns at `finalize` |
| Attestation failed | "This node could not prove its software. Nothing was sent." The request fails closed; no fallback to standard mode | none; if `openSession` was already sent, the deposit returns via `closeSession` and `finalize` |
| No eligible node for the required mode | "No node in this model's pool offers {mode}." The request fails closed | none |
| Empty or thin pool | "No node offers this model" or "Only {n} nodes offer this model; prices may be uncompetitive" | none |
| Stale context | `stale_version` or `context_hash_mismatch`: "Your context changed since this grant was made" with a rebase-and-republish action | nothing charged for that job |
| Cap exhausted on one session | "Cap reached on {node}" with top-up or close; in a plan, only that task pauses | signed total of that session |
| Sequencer delay | "Arbitrum's sequencer is slow or down; your transaction can be force-included from L1 after about a day" (evidence register §1 [V]); vouchers continue off-chain | a node that redeems late may lose vouchers to the close deadline (docs/protocol/contracts-and-settlement.md R2); the user loses nothing |
| One sub-task node of a plan offline mid-wave | that task is marked failed; the client retries only on a node that was on the confirmed sheet, with a new session; the vouchers signed for the failed node stand | the failed node's signed total plus one more session's L2 gas |
| Contested or incomplete collective answer | the disagreement view shows every answer and critique and the synthesizer's objection if any; the client never presents the result as verified. "Incomplete" means only that required fields are missing or malformed; disagreement between the two position-swapped review passes is expected (position bias) and an empty splits list is valid | every session's signed total |
| Pool cannot fill the confirmed set | "A node on your confirmed sheet is no longer available." The request fails closed; sessions already opened are closed | L2 gas of the opened sessions; deposits return at settlement |
| Stale disclosure sheet | "The plan changed since you confirmed." The new sheet is shown; nothing is sent until it is signed for | none for the unsent part |
| Prices copied into the session on-chain differ from the sheet | "The node changed its price; nothing was sent." The unilateral close is called; deposit returns via `finalize`. Only the on-chain copied prices can raise this; a different price in the node's `welcome` is logged and the node is dropped, but never locks the deposit behind a close | L2 gas only |
| Only some of N `openSession` calls signed | "You opened {k} of {N} sessions. Nothing was sent." Close is offered on the opened ones (final voucher with zero output, or the unilateral close then `finalize`) | L2 gas of the opened sessions |
| Wallet declines the grant signature | "The context was not shared; the prompt was not sent." Nothing is sealed; the user may retry or send without the context | none |
| Lost wallet | stated honestly on screen 16: refunds are credited to the depositing address and pulled with `withdraw()`; a lost wallet loses them | the credited balance |

## 9. Accessibility

- Every control is reachable and operable by keyboard; focus order follows reading order; the plaintext banner receives focus when shown and is announced.
- Nothing is conveyed by color alone: class labels carry their words (S Small, M Mid-size, L Large, X Largest); modes carry text; experimental features carry the word "experimental"; a truncated answer carries a text marker, not only a tint.
- The chat stream uses a live region with polite announcements per chunk boundary, not per token.
- Layouts work from narrow phone viewports (one column, the running total pinned) to wide desktops (chat, context sidebar and spend side by side); no horizontal scrolling at 320 px width.
- Numbers are shown with units (ETH, tokens) and never abbreviated in a way a screen reader mispronounces; wei values are converted to ETH decimals for display (section 6) and the exact wei is available on request.
- Timeouts that end a session (section 8) are announced before they expire and can be extended where the protocol allows.

## 10. Dapp categories the community can build

The SDK is general; the chat client is one use. Categories the community can build on the same contracts and API:

| Category | What it needs from the protocol |
|---|---|
| Chat | sessions, streaming, contexts for transcripts |
| Document Q&A over private contexts | context grants per version; local-first storage; a node that supports large `maxContextTokens` |
| Coding assistants | task decomposition with a reviewer of a different model family; a local test harness, because the protocol cannot judge code quality |
| Agents | **inference only**: the protocol provides answers, never permission to act; any tool or external action is the dapp's own responsibility and must be gated by the user, not by model output |
| On-chain apps calling inference | an app contract cannot call a node; a user or a relayer the app trusts opens the session, and the result is brought on-chain by whoever the app trusts; verifiable mode gives a second opinion, not a proof |
| Compatibility adapter | a wrapper exposing the widely used chat-completions request shape so existing tools work; it **must encrypt on the client side before any untrusted hop** — an adapter that forwards plaintext to a gateway that then encrypts is not a Comuns client |

**Developer onboarding on Arbitrum Sepolia.** No deployment is claimed. When the testnet-only CIP registers Sepolia models and bands (docs/protocol/contracts-and-settlement.md §13), a developer would: connect a wallet on Arbitrum Sepolia; point the SDK at the testnet escrow and registries; list the testnet pool; open a session with testnet ETH; run every walkthrough of the contracts document; and run the disclosure-sheet conformance test (docs/security/privacy-and-contexts.md §12) against their own client. Experimental features appear only when a testnet price exists.

## 11. What this client will not do

- Host prompts, contexts or answers on any project-run server.
- Offer a second account system: no email, no password, no social login; the wallet is the account.
- Hide the inference payment inside L2 gas, or show one number for service cost and gas.
- Auto-route to the cheapest node. The user picks the node, or confirms a ranked set; ranking is advisory.
- Silently add a node to a request, switch a request to a multi-node feature, widen what any node receives or raise a cap without re-showing the disclosure sheet and obtaining a signature.
- Fall back to a node that was not on the confirmed sheet.
- Confirm a sheet and then change the models, nodes or readers under it; the order is pick models, see the sheet, confirm, sign.
- Sign a voucher above the effective cap, or resume a session from a node's reported totals instead of its own voucher log; after a lost log it closes unilaterally and signs nothing.
- Close a session because of a price a node merely reported; only the prices copied on-chain are compared with the sheet.
- Show raw wei in user copy, or sign a context grant with anything but the owning wallet.
- Run `model_sharding` or `cross_node_speculation` under mainnet parameters; both exist only with testnet-only prices.
- Present a collective answer as verified, or hide a disagreement inside a collective answer.
- Delegate `sessionSigner` to an orchestrator node in v1; the orchestrator node holds no session, custodies no funds and signs no voucher on the user's behalf.
- Collect seed phrases, private keys or wallet passwords under any pretext.
- Hide the fact that a quality refund is impossible: a signed voucher is not reversed by anyone.
- Call `eth_getEncryptionPublicKey` or `eth_decrypt`, or derive an encryption key from a wallet signature by default.
- Send a transaction per message.

## 12. Risks

### R1 — Compromised or dishonest client **[RISK] · High**

A client that skips the sheet, miscounts readers or seals to the wrong key defeats every guarantee. Mitigation: open-source reference client; the disclosure-sheet conformance test; `sheetVersion` bound into the AAD so a log audit can find divergence.

### R2 — Wallet and key UX **[RISK] · Medium**

Users may lose the identity key backup, lose the device holding ciphertext, or lose the wallet. Each loss is permanent in a different way (section 7, section 8). Mitigation: screen 16 says exactly what each loss means; the backup format is an open question.

### R3 — Price and pool volatility **[RISK] · Medium**

Prices change between pool listing and `openSession`. `openSession` reverts on a changed price, so no deposit is locked, but the user must re-confirm. Mitigation: refresh the pool just before the sheet; show a one-wei change as a change.

### R4 — Automatic signing pays for bad answers **[RISK] · Medium**

Voucher signing checks counts, not quality. Mitigation: the Stop control; small caps; spend history; reputation.

### R5 — Orchestrator-node dependency for thin clients **[RISK] · Medium**

A thin client that relies on an orchestrator node to plan gives that node the full prompt and the plan. Mitigation: the node is optional, reached through an ordinary session after its own sheet, and never holds `sessionSigner`.

### R6 — Experimental features reach users **[RISK] · Medium**

Sharding and cross-node speculation, if exposed, widen the reader set in ways users do not expect (activations recover prompts, evidence register §10 [V]). Mitigation: hidden unless a testnet price exists; labelled experimental; the sheet counts activations and draft tokens.

### R7 — Stolen `sessionSigner` on the device **[RISK] · Medium**

The app-local key signs vouchers and envelopes up to the cap until settlement; `closeSession` does not revoke it. Mitigation: small per-session caps; encrypted at rest; discarded at session end; rotation is an open question for a later CIP.

### R8 — Lost wallet loses credited refunds **[RISK] · Medium**

Refunds are credited to the depositing address and pulled with `withdraw()`; a lost wallet cannot pull them. Stated on screen 16; no v1 mitigation beyond small deposits.

## 13. Open questions

1. **Wallet library.** Which EIP-1193 wrapper to use, and how to support contract wallets whose `openSession` is a batched user operation.
2. **Session keys and account abstraction.** Whether a later CIP lets a smart account authorize `sessionSigner` as a session key with a spending limit, so that thin clients that cannot sign per chunk can still use the protocol — future work, not v1.
3. **Backup format.** The password-based KDF, versioning and update cadence of the encrypted export of the identity key and key-wrap records; whether an optional ciphertext bundle is offered (docs/security/privacy-and-contexts.md §14).
4. **Package name and distribution.** The SDK's name, whether it ships a WASM HPKE build by default, and how the reference client is distributed without a project-run server.
5. **Batching `openSession`.** Whether a multicall from the client, or a new batch entry point by CIP, can open the N sessions of a plan in one wallet action (docs/protocol/contracts-and-settlement.md §16).
6. **Reputation source.** Which community indexers the client lists by default, if any, and how a user adds their own.
7. **Local execution mode.** Whether the same client should offer a local-model mode as the owner-only option the privacy document describes, and how it is kept clearly apart from paid sessions.
8. **`SessionMap` with a second session per pair.** Section 3 keys `SessionMap` to one `sessionId` per `(node, modelId)`, while docs/protocol/orchestration.md §6 allows a second, separately disclosed session for the same pair when two tasks of a wave must run in parallel. `SessionMap` should map a pair to a list of `sessionId`s (or to the sheet's session index), with the dispatcher choosing among them; the shape is open for the SDK.
