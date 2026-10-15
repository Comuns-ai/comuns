# Dapps and SDK — chat on top of the session protocol

Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12

**Reference:** docs/protocol/off-chain-api.md, docs/protocol/contracts-and-settlement.md, docs/security/privacy-and-contexts.md, docs/economics/cost-and-pricing.md, docs/node/node-design.md, docs/adr/0010-anonymous-by-default.md, docs/adr/0011-anonymous-credits.md, docs/adr/0012-contexts-without-a-wallet-link.md

---

## 1. Summary

This document proposes a reference chat client and a TypeScript SDK for Comuns, the community proposal for open-source decentralized LLM inference settled on Arbitrum One. Nothing described here exists yet; no package is published and the package name is undecided.

The client is deliberately thin, and it is anonymous by default (docs/adr/0010-anonymous-by-default.md). It owns five things and nothing else: the user's wallet connection (EIP-1193), used only to deposit credit notes and, if the user chooses, to ragequit and withdraw; an app-managed HPKE keypair that is never the wallet key; a local, encrypted vault holding the note secrets, the context keys, the key-wrap records and the accepted context head checkpoints; a fresh `sessionSigner` per session; and the relay transport through which every job and every session-specific chain read travels. Everything else is the protocol: credit notes, sessions and vouchers from docs/protocol/contracts-and-settlement.md and docs/adr/0011-anonymous-credits.md, envelopes, the credit flow and frames from docs/protocol/off-chain-api.md, modes, features and the disclosure sheet from docs/security/privacy-and-contexts.md, and ownerless contexts from docs/adr/0012-contexts-without-a-wallet-link.md.

What the user does, in order: connect a wallet on Arbitrum One and choose an RPC endpoint; **deposit** ETH once into a fixed-denomination credit note (`depositNote`, the one public, wallet-linked step); later, **pick a model first**, then one node from that model's pool (or confirm a ranked set from it), and a relay drawn at random from the registry; choose the execution features (none by default, which means single-node); read the disclosure sheet and the banner; and **spend a credit**: the client proves on the device that it holds one note, hands the proof to the node through the relay, and the node submits `openSessionFromCredit`. The wallet is not asked to sign anything for a session. Every chunk is paid by an automatic voucher signature from `sessionSigner` within the cap, which is the note's denomination; no transaction is sent per message; the service cost is shown in ETH as a cap and a running total, separate from the L2 fee; the protocol fee is 0 and there is no token. Granting a context to a node is a local re-wrap signed by that context's own key, with no wallet prompt. Ending the session cooperatively signs one final voucher so the node settles; the unused remainder is recorded as `pendingWei` and returns as fresh change notes through `claimChange`. Multi-node features never start without the user confirming the disclosure sheet for that request.

The standard tier promises that the node can read the prompt but should not learn who sent it. The attested tier adds that the node should not be able to read the prompt either, barring a physical attack (evidence register §14). Inference runs only on network nodes; the client performs no model computation.

## 2. Scope

This is one reference client. **The client is not the protocol.** Anyone may write another dapp against the same contracts and the same off-chain API; the community categories in section 10 are examples. What this document fixes is what any honest client must show and must refuse (sections 5, 8 and 11), because the protocol's privacy promises depend on the client doing so (docs/security/privacy-and-contexts.md R5).

Binding decisions carried in, all PROPOSED:

| Decision | Value |
|---|---|
| Account | The wallet funds deposits and is the only account: no email login, no password, no seed-phrase collection, ever. The wallet address is never sent to a node or a relay |
| Funding | Anonymous credits (docs/adr/0011-anonymous-credits.md): `depositNote` from the wallet, then one note per session spent by `openSessionFromCredit`, submitted by the node. The wallet-funded `openSession` has no call site in this client and is not offered as a mode |
| Transport | Every job, frame, voucher, `closeSession`, `claimChange` and session-specific chain read goes through a relay (Oblivious HTTP); there is no direct client-to-node path and no fallback to one |
| RPC | User-chosen; registry-wide reads (models, pools, relays) may use it directly; every session-specific read (session lookup, settlement and change monitoring, Merkle witness and root) is tunnelled through a relay. An indexer is a backend behind that transport, not an alternative to it. No project-operated endpoint or matcher |
| Selection | Model-first; the pool of a model is every node whose `prices[modelId]` has a non-zero `modelBenchmarkHash`; the user picks a node or confirms a ranked set; any class may appear in any pool; `maxTier` is informational. The relay is drawn at random per session |
| Encryption | HPKE in the client with an app-managed keypair; `eth_getEncryptionPublicKey` and `eth_decrypt` are forbidden |
| Signing | The wallet signs only `depositNote`, `ragequit` and `withdraw`. Vouchers, envelopes, `closeSession` and `claimChange` are signed by the session's fresh `sessionSigner`; head records, grants and any `setContext` anchor are signed by the context key. The wallet is never prompted per session, per chunk or per grant |
| Payment | ETH, protocol fee 0, no token; never hidden inside L2 gas; the relay fee is paid from the first wei of the node's settled value, never by a user transaction; the unused remainder of a note returns as change notes |
| Orchestration | Default is the client's own SDK code; an optional orchestrator node is reached through an ordinary credit session after its own disclosure; `sessionSigner` is never delegated in v1 |
| Contexts | Local-first, many per wallet, each with its own context key; encrypted per version; switched between nodes by re-wrapping keys; never uploaded in plaintext; the list of a wallet's contexts lives only in the local vault |
| Execution | Inference runs only on network nodes; the client keeps transport, orchestration and sampling decisions and performs no model computation |

Out of scope: the node software (docs/node/node-design.md), prices and bands (docs/economics/cost-and-pricing.md), the orchestration pattern itself (docs/protocol/orchestration.md), verification (docs/security/inference-verification.md).

## 3. SDK surface

A sketch of the call shapes, not an API freeze. The package name is undecided; wallet access is EIP-1193; HPKE uses WebCrypto X25519 where the platform exposes it and otherwise a WASM build of the same RFC 9180 implementation the reference node uses, so that client and node share one cipher suite (docs/security/privacy-and-contexts.md §4). The OHTTP encapsulation to a node's registered `ohttpKeyConfig` uses the same suite.

Proof generation is local: the Semaphore v4 proof for a spend or a ragequit is computed on the user's device and never delegated to a node, a relay or a proving service. Phone proving for the deepest circuit is 143–2,146 ms [V] (Semaphore-32) (evidence register §15); the group depth is a proof parameter in Semaphore's range of 1 to 32 [V] and says nothing about the size of the anonymity set. The prover artifacts (wasm, zkey and verification key for the depths the escrow accepts) ship pinned by SHA-256 in the code repository or a project-hosted copy and are checked before use; the client never downloads them unverified at runtime, because per-file hashes were not found in the sources examined on 2026-10-15 [U] and the artifact repository was archived on 2026-08-19 [V] (evidence register §15, recheck 2026-10-15).

```typescript
// Package name undecided. Everything below is a call-shape sketch.
import type { EIP1193Provider } from "eip1193-types-placeholder";

type Hex = `0x${string}`;
type Mode = "standard" | "attested" | "verifiable";
type Funding = "credit";                 // the wallet-funded openSession has no SDK call
type Transport = "relay";                // OHTTP through a registered relay; there is no "direct"
type ExecutionFeature =
  | "collective_answer"
  | "parallel_planning"
  | "task_decomposition"
  | "model_sharding"        // experimental, Phase 3 spike
  | "cross_node_speculation"; // experimental, Phase 3 spike
type HardwareClass = "S" | "M" | "L" | "X";

interface ConnectOptions {
  provider: EIP1193Provider;          // the wallet: used only for depositNote, ragequit and withdraw
  rpcUrl: string;                     // user-chosen Arbitrum One RPC; session-specific reads are tunnelled through a relay
  indexerUrl?: string;                // optional community indexer, a backend behind the relay transport, never required
  orchestratorNode?: Hex;             // optional: send plan requests to a node advertising roles.orchestration
}

interface Denomination { index: number; wei: bigint; observedGroupSize: number }   // values come from setCreditParameters; none is set in any document

interface Note {                      // one entry of the local note store; the secret never leaves the vault
  commitment: bigint; denominationIndex: number;
  origin: "deposit" | "change";
  state: "unspent" | "in_flight" | "spent" | "ragequit";
  insertedAt: number;                 // unix seconds the commitment was seen in its group
  spendableAfter: number;             // insertedAt + the client delay (unset); the client recommends waiting until then
}

interface RelayEntry { operator: Hex; endpoint: string }     // a Relay record; the relay's address is its operator

interface PoolEntry {
  node: Hex;                          // operator address
  endpoint: string;
  class: HardwareClass;               // shown as "S Small" | "M Mid-size" | "L Large" | "X Largest"
  maxTier: "T0" | "T1" | "T2" | "T3" | "T4"; // informational only
  modes: Mode[];
  priceInPerMillion: bigint;
  priceOutPerMillion: bigint;
  modelBenchmarkHash: Hex;            // non-zero: in the pool
  measuredTokensPerSecond?: number;   // client-measured through a relay, optional
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

interface HeadRecord { contextId: Hex; version: number; contentHash: Hex; prevContentHash: Hex; signature: Hex }  // signed by the context key

interface ContextGrant {
  contextId: Hex; contextPubKey: Hex;   // the node checks keccak256(contextPubKey) == contextId
  fromVersion: number; toVersion: number; expiresAt: number; nodeKeyHash: Hex;
  wrappedKeys: string[];              // K_fromVersion … K_toVersion, each HPKE-sealed to the node's registered key
  contextSignature: Hex;              // EIP-712 by the context key over every field above; never a wallet signature
  headRecords: HeadRecord[];          // sent beside the grant, outside its signed fields: version 1 up to toVersion
}

interface DisclosureSheet {
  requestId: Hex; planId: Hex; version: number;
  recipients: Array<{ node: Hex; operator: Hex; roles: string[]; modelId: Hex; mode: Mode; receives: string[];
                      operatorReadable: boolean;          // false only for an attested recipient whose quote verified
                      priceInPerMillion: bigint; priceOutPerMillion: bigint; capWei: bigint }>;
  counts: { fullPrompt: number; subTask: number; otherAnswers: number; activations: number; draftTokens: number;
            operatorReadable: number; attestedRecipients: number };
  readersOfFullPrompt: { nodes: number; operators: number };   // the floor; unchanged by mode
  anonymity: {
    transport: Transport;             // serialised in the sheet JSON as the sentence of docs/protocol/off-chain-api.md §6.1
    relay: Array<{ node: Hex; relay: Hex /* the relay operator's address */; eligibleRelaySetSize: number }>;
    funding: Array<{ node: Hex; denominationIndex: number; observedGroupSize: number; belowThreshold: boolean }>;  // every session is Funding "credit"
    contextLinkage: Array<{ contextId: Hex; node: Hex; grantedToThisNodeBefore: boolean; anchored: boolean }>;
    // linkage is by context key alone when anchored is false, and also on-chain when it is true
  };
  totalCapWei: bigint;
  l2GasEstimate: bigint;              // the user's own wallet transactions only; shown separately, never folded into totalCapWei
  experimental: boolean;
}

interface ComunsClient {
  connect(opts: ConnectOptions): Promise<{ chainId: number }>;   // the account is never returned to session code
  listModels(): Promise<Array<{ modelId: Hex; tier: string; licenseSpdx: string; commercialHosting: boolean }>>;
  listPool(modelId: Hex): Promise<PoolEntry[]>;           // model-first: every node with a non-zero modelBenchmarkHash for modelId
  listNodes(): Promise<PoolEntry[]>;                       // all registered nodes, for the operator directory view
  relays(): Promise<RelayEntry[]>;                         // registered relays with unlockAt == 0; the client draws one at random per session

  listDenominations(): Promise<Denomination[]>;            // the append-only list and each group's observed size
  deposit(denominationIndex: number): Promise<{ commitment: bigint; txHash: Hex }>;
  // Generates a fresh Semaphore identity, stores its secret durably in the vault, THEN asks the wallet to send
  // depositNote(identityCommitment, denominationIndex) with msg.value equal to the denomination. Public and wallet-linked.
  creditBalance(): Promise<{ notes: Note[]; unspentWei: bigint; pendingChangeWei: bigint }>;
  // Read from the local note store only; never asks a node, a relay or an indexer which notes are the user's.
  ragequit(commitment: bigint): Promise<Hex>;
  // Proves one note of that group locally and asks the wallet to send ragequit(denominationIndex, merkleTreeDepth,
  // merkleTreeRoot, nullifier, points). Public and linkable; bounded by the wallet's own deposits into that group.

  openCreditSession(args: {
    node: Hex; modelId: Hex; mode: Mode;
    relay?: RelayEntry;                                    // omitted: drawn at random; never one whose operator is the node
    denominationIndex: number;                             // the client picks an unspent note of this group
    expectedPriceInPerMillion: bigint; expectedPriceOutPerMillion: bigint;   // from the confirmed sheet
  }): Promise<{ sessionId: Hex; sessionSigner: Hex; relay: RelayEntry }>;
  // Before the proof and credit_spend are sent, runs the ADR 0015 key_probe through an authenticated relay and spends
  // nothing unless the challenge, the response MAC and the receipt signature verify; then pins the receipt key for the session.
  // Fresh sessionSigner; local Semaphore proof (witness and root read through the relay); credit_spend through the relay;
  // the node submits openSessionFromCredit. No wallet prompt. Resolves only after the client sees SessionOpened and
  // CreditSessionOpened with its own nullifier through the relay and the copied prices match the sheet.

  chat(args: {
    sessionId: Hex; prompt: string; contextGrants?: ContextGrant[];
    params?: { maxOutputTokens?: number; temperature?: number };
    signal?: AbortSignal;                                   // the Stop control: aborting stops voucher signing
  }): AsyncIterable<{ text: string; cumulativeOutputTokens: number; runningTotalWei: bigint }>;

  assess(args: { prompt: string; contextTokens: number; userChoice?: ExecutionFeature[] }): Promise<Assessment>;
  // Local heuristics only: never contacts a node. Returns a size class, risk flags and a recommended feature set.

  plan(args: { requestId: Hex; prompt: string; assessment: Assessment; plannerSessionId?: Hex }): Promise<Plan>;
  // Returns a plan DAG. May call a planner session the user approved after a first disclosure sheet.

  disclosureSheet(args: { requestId: Hex; plan?: Plan; mode: Mode; features: ExecutionFeature[] }): Promise<DisclosureSheet>;
  // Returns the table the UI must show before any proof is handed to a node for this request.

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
    list(): Promise<Array<{ contextId: Hex; name: string; headVersion: number; anchored: boolean }>>;
    // From the local vault only; the list of a wallet's contexts is never sent anywhere.
    create(args: { name: string; plaintext: Uint8Array }): Promise<{ contextId: Hex; version: number; contentHash: Hex }>;
    // Fresh context key from the OS CSPRNG; contextId = keccak256(contextPubKey); head record signed by the context key.
    update(args: { contextId: Hex; plaintext: Uint8Array }): Promise<{ version: number; contentHash: Hex }>;
    // New K_v, new head record; published to the context host by compare-and-swap through a relay; checkpoint kept.
    anchor(args: { contextId: Hex; version: number }): Promise<Hex>;
    // Optional: setContext(contextId, version, contentHash, contextPubKey, signature) submitted by a broadcaster through a relay.
    grant(args: Array<{ contextId: Hex; fromVersion: number; toVersion: number; node: Hex; expiresAt: number }>): Promise<ContextGrant[]>;
    // Re-wraps the granted versions' keys to each node's registered key and signs each grant with that context's key.
    // Entirely local; no wallet prompt; sessionSigner never signs a grant.
    revoke(args: { contextId: Hex; node: Hex }): Promise<void>;   // stops future grants; cannot un-read the past
    exportBackup(passphrase: string): Promise<Uint8Array>;
    // Identity key, every key-wrap record, the context keys, the note secrets and the accepted head checkpoints; no ciphertext.
    importBackup(file: Uint8Array, passphrase: string): Promise<void>;
  };

  closeSession(args: { sessionId: Hex }): Promise<{ finalVoucherSeq: number }>;
  // Cooperative close: signs the final voucher from the SDK's own voucher log; the node calls closeWithVoucher, which
  // credits node and relay and records pendingWei. Refuses to run when the log for the session is missing.
  closeSessionUnilateral(args: { sessionId: Hex }): Promise<Hex>;
  // closeSession(sessionId, signature) with a sessionSigner EIP-712 signature over (chainId, escrow, sessionId, "close"),
  // submitted through a relay or broadcaster, never from the deposit wallet; no voucher signed. Used after a lost voucher
  // log, a vanished node, or a price mismatch. The node may still redeem its highest voucher until closeDeadline.
  finalize(args: { sessionId: Hex }): Promise<Hex>;        // after closeDeadline, through a relay or broadcaster; records pendingWei
  claimChange(args: { sessionId: Hex }): Promise<{ commitments: bigint[]; denominationIndexes: number[]; dustWei: bigint }>;
  // Greedy decomposition of pendingWei into at most MAX_CHANGE_NOTES fresh notes, each with a fresh identity stored
  // durably first; sessionSigner signs; submitted through a relay or broadcaster. Dust below the smallest denomination
  // goes to the node.
  withdraw(): Promise<Hex>;                                 // pulls balances[wallet], which only a ragequit credits for a user
}
```

Notes on the sketch:

- `assess` runs on the user's device and never contacts a node. `plan` contacts a node only when the user has opted into orchestration and approved a planner session after its own disclosure sheet (docs/protocol/orchestration.md §5).
- `run` refuses to dispatch any job for a `requestId` without a recorded confirmation of the current sheet version, and refuses to dispatch any job without a relay: when no eligible relay exists the request fails closed with `relay_unavailable`, and the SDK has no code path that connects to a node directly. It binds `requestId` and `sheetVersion` into every envelope's AAD (docs/security/privacy-and-contexts.md §8.3). The order is fixed: pick models → see the sheet → confirm → spend a credit per session. Any change of node, relay, model, data scope, price, cap or reader set after a confirmation creates a new sheet version that must be confirmed again; a client never confirms a sheet and then changes models under it. If verifiable mode (or any other extra reader) is wanted on the result, that verifier is on the sheet, with its own credit session, before any spend; adding one later is a new sheet version and a new confirmation.
- `deposit` writes the note secret to the vault before the wallet sends the transaction, so a crash between the two leaves a stored secret for a commitment that may never be published, never a published commitment with no secret. Every note, deposit and change alike, gets a fresh Semaphore identity; a reused identity would make a second note unspendable and link two groups publicly (docs/adr/0011-anonymous-credits.md).
- `creditBalance` is a local read. Asking an indexer "which of these commitments are mine" would link the notes to the asker; the client instead reads group roots and witnesses through a relay and computes everything else itself.
- The SDK signs vouchers only from its own voucher log and never above the effective cap `min(depositWei, maxSpendWei)`, which on a credit session is the note's denomination; the remaining allowance it shows is that cap minus the highest `cumulativeWei` it has signed, redeemed or not. It never adopts a node's reported totals. There are two ways to close: the cooperative `closeSession` (a final voucher, then the node's `closeWithVoucher`) and the unilateral `closeSessionUnilateral` (the contract's `closeSession` with a `sessionSigner` signature, no voucher, then `finalize` after `closeDeadline`). Either way `pendingWei` is then claimed with `claimChange`. If the log for a session is lost the SDK signs nothing more there — it cannot build a final voucher without its own counts and must not build one from the node's — so it uses only the unilateral close; further work needs a new session, and because a new session is a new note and a new cap, a new disclosure sheet version is shown and confirmed before that spend.
- `topUp` reverts on a credit session and the SDK has no call for it. When the cap is exhausted the client opens a new credit session with a new note (section 6).
- Sessions are keyed by the pair `(node, modelId)` (`SessionMap`): one node may serve two models of a plan, and two nodes may serve the same model, so a single `Hex` key would collide and route a job onto the wrong session. A session runs one job at a time (`maxConcurrentJobsPerSession = 1`, docs/protocol/off-chain-api.md §3); `run` dispatches a wave's tasks concurrently only across different sessions and runs two tasks that share a session one after the other, unless the sheet lists a second session for that pair.
- Price checks read the chain, not the node: after `SessionOpened` and `CreditSessionOpened` are visible through the relay, the SDK compares the prices copied into the session on-chain with the confirmed sheet; prices a node reports in `welcome` are informational and never trigger a close. The spend message binds the expected prices, so a changed offer makes the spend revert and consumes no nullifier.
- `orchestratorNode`, if set, sends the plan request to a node that advertises `roles.orchestration` through an ordinary credit session, after a disclosure sheet saying that node will see the full prompt and the plan. The orchestrator node holds no `sessionSigner`; the user's client still opens every downstream session and signs every voucher.
- The compatibility adapter (section 10) that exposes the widely used chat-completions request shape of hosted inference APIs is a wrapper over `chat`; it encrypts on the client side and sends through a relay before any untrusted hop, and never forwards plaintext to a gateway.

## 4. Screens and flow

Nineteen named screens. Every screen is reachable by keyboard (section 9). The wallet appears on three of them only: Deposit and notes (screen 3), for `depositNote` and `ragequit`, and Withdraw balance (screen 19). No screen asks the wallet to sign a session, a voucher or a context grant.

| # | Screen | What it does | What it must show |
|---|---|---|---|
| 1 | **Connect wallet** | EIP-1193 connect; checks the chain is Arbitrum One (or Arbitrum Sepolia in developer mode) | no email, no password; "your wallet funds your deposits; it is never shown to a node" |
| 2 | **Network and RPC** | The user enters or picks an RPC endpoint and optionally an indexer; the client never defaults to a project-run endpoint | which endpoint sees registry-wide reads; that every session-specific read goes through a relay |
| 3 | **Deposit and notes** | Lists the denominations and each group's observed size; `deposit` sends `depositNote` from the wallet after the note secret is stored; lists the notes in the local store with their state; offers `ragequit` per note | that the deposit is **public** and names the wallet; the group size of the chosen denomination; a recommendation to wait before spending a new note (the deposit-to-spend delay is unset and no minimum is adopted; evidence register §15 [V] for timing linkage); that `ragequit` is public, linkable to the wallet and bounded by the wallet's own deposits into that group |
| 4 | **Model picker** | Lists registered models with tier label, license and `commercialHosting`; the user picks a model first | models with `commercialHosting = false` are shown as not available for paid sessions |
| 5 | **Model pool** | The nodes in the chosen model's pool, each with plain class label **S Small**, **M Mid-size**, **L Large**, **X Largest**, prices, modes, measured speed and reputation; the user picks one node or confirms a ranked set | "a stronger class costs more for the same model"; `maxTier` as information; the attested filter copy of section 5 |
| 6 | **Relay choice** | Draws a relay at random from the registered relays with `unlockAt == 0`, skipping any whose operator is a chosen node's operator; the user may redraw | the relay banner sentence (section 5); the size of the eligible relay set; that one person running a relay and a node under two addresses is not detected |
| 7 | **Execution features** | Single-node is selected by default; the user may add collective answer, task decomposition or parallel planning; sharding and cross-node speculative decoding are labelled experimental and hidden when no testnet price exists | the reader count that each feature adds, and that each paid recipient spends its own note, before anything is chosen |
| 8 | **Plan review** | For task decomposition: the DAG, each task's model and node, the waves; the user confirms every `modelId` and node, or forces single-node. This comes **before** the sheet: models and nodes are fixed here, then disclosed | every `modelId`; the planner's output is data, never authority |
| 9 | **Disclosure sheet** | The table of docs/security/privacy-and-contexts.md §8.3, generated from the sheet JSON for the models, nodes and relays confirmed so far: which nodes see the full prompt, a sub-task, other answers, activations or draft tokens; `operatorReadable` per recipient; the `anonymity` object (relay per session, denomination group and its size, context linkage); counts, prices and caps; a verifier, if verifiable mode is wanted on the result, is already listed | nothing proceeds until the user confirms this sheet; any later change of node, relay, model, scope, price, cap or reader set returns the user to this screen with a new version |
| 10 | **Banner and cap** | The banner of section 5, the cap in ETH (the denomination of the note each session spends), the L2 fee estimate shown separately | the headline, the per-node banner sentences and the relay sentence; "cap" and "running total" are service cost, not gas |
| 11 | **Spend a credit** | Per session: first the ADR 0015 `key_probe` through an authenticated relay (no spend unless the challenge, the response MAC and the receipt signature verify; the receipt key is then pinned for the session), then a fresh `sessionSigner`, a Semaphore proof generated on the device (phone proving 143–2,146 ms [V] (Semaphore-32), evidence register §15), `credit_spend` through the relay; the node submits `openSessionFromCredit` and pays its gas. No wallet prompt | `note_in_flight` until `CreditSessionOpened` with the client's nullifier is visible through the relay, then `opened`; the on-chain copied prices checked against the sheet; the group size and the below-threshold warning if it applies |
| 12 | **Chat** | Streaming answer through the relay, running spend, a **Stop** control that stops voucher signing | running total vs cap; truncated answers marked |
| 13 | **Disagreement view** | For collective answers: each answer under its stable anonymous ID (A1…Ak, assigned once per request), each critique, the synthesis, and any objection; never a ranked list the client auto-executes | the disagreement is visible, never hidden inside the synthesis; every critique and split names the stable ID |
| 14 | **Switch node** | Closes the current session (final voucher) and spends a new note on another pool node, through a newly drawn relay; re-wraps context keys to the new node locally, signed by the context key | that this is a new session with a new reader and a new note; the sheet is shown again |
| 15 | **Close and change** | Cooperative close signs the final voucher; a unilateral close (`closeSession` with a `sessionSigner` signature through a relay or broadcaster, then `finalize` after `closeDeadline`) is offered when the node is gone or the voucher log is lost; once `settled`, a **Claim change** control decomposes `pendingWei` greedily into fresh notes and submits `claimChange` through a relay or broadcaster | `settled`, then `change_claimable` and `change_claimed` (docs/protocol/off-chain-api.md §12); the dust that goes to the node; that a change note spent at once is linkable by timing and the client delays it (delay unset) |
| 16 | **Context sidebar** | Create, edit (new version), grant, revoke, optionally anchor; see which node holds which versions | local-first; a grant is per node and per version range, signed by the context key, with no wallet prompt; whether the context is anchored and what that links |
| 17 | **Spend history** | Per session: relay, denomination, signed total, redeemed total, relay share, `pendingWei`, change and dust, state from docs/protocol/off-chain-api.md §12; per deposit: the L2 fee paid | service cost and gas as separate columns |
| 18 | **Backup and restore** | Export the encrypted backup (identity key, every key-wrap record, the context keys, the note secrets and the accepted head checkpoints); import on a new device | the backup holds no ciphertext; a note whose secret is in no backup is lost with the device; keep a context host or a second device for ciphertext |
| 19 | **Withdraw balance** | Pulls `balances[wallet]` from `SessionEscrow` (a user has one only after a ragequit) and, for operators using the same client, from `NodeRegistry` | that `withdraw()` is a public wallet transaction |

The single-node flow from deposit to change:

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dapp (SDK, vault, sessionSigner, HPKE keys)
    participant W as Wallet (EIP-1193)
    participant R as Relay (OHTTP, random from NodeRegistry)
    participant E as SessionEscrow
    participant N as Node (from the model's pool, OHTTP gateway)
    U->>D: Connect wallet, set RPC
    D->>W: eth_requestAccounts, chainId check
    U->>D: Deposit into one denomination
    D->>D: fresh Semaphore identity; note secret stored in the vault first
    D->>W: depositNote(identityCommitment, denominationIndex) + denomination
    W->>E: one public transaction (the only wallet step for sessions)
    Note over U,D: later, after the recommended delay (unset)
    U->>D: Pick model, then node; execution features = none (single-node)
    D->>D: draw a relay at random (operator differs from the node's)
    D-->>U: Disclosure sheet v1 + headline + banner sentences + relay sentence + cap
    U->>D: Confirm (sheet v1 recorded)
    D->>R: witness and root read (RPC or indexer through the relay)
    D->>D: fresh sessionSigner; Semaphore proof on the device
    D->>R: credit_spend (proof, node, relay, modelId, mode, sessionSigner, expected prices)
    R->>N: forward
    N->>E: openSessionFromCredit (node pays the gas)
    N-->>D: session_opened via R
    D->>R: read SessionOpened + CreditSessionOpened through the relay; copied prices == sheet v1?
    D->>N: hello via R (sessionSigner signature); welcome (its prices are informational)
    U->>D: Type prompt
    D->>N: job envelope via R (HPKE, padded, commitKey, AAD with requestId and sheetVersion 1, signed)
    N-->>D: input receipt via R
    D->>N: input voucher via R (automatic, counts match)
    loop per chunk
        N-->>D: frame + chunk receipt via R (chunked OHTTP)
        D-->>U: streamed text, running total
        D->>N: cumulative voucher via R (automatic, within cap)
    end
    U->>D: Close session
    D->>N: final voucher via R (cooperative close)
    N->>E: closeWithVoucher → relay fee first, node credit, pendingWei recorded
    D->>R: claimChange(sessionId, changeCommitments, denominationIndexes, sessionSigner signature)
    R->>E: forward; fresh change notes enter their groups, dust to the node
    D-->>U: Change notes in the local store; spend delay recommended
    Note over D,E: unilateral close instead: closeSession with a sessionSigner signature via R, then finalize after closeDeadline, then claimChange
```

## 5. The plaintext banner

The banner is shown on screen 10 and again at the top of the chat view. It is not dismissible until read (keyboard: focus lands on it; screen readers announce it). In standard mode it is **informational**: it states what the default is, it is not a warning the user must opt into, and it offers no switch. There is no mode, setting or toggle that reveals the wallet to a node, funds a session from the wallet, or connects without a relay. A client may add sentences but may not remove or reword the normative ones.

**The normative sentences.** Copied verbatim from docs/adr/0010-anonymous-by-default.md and docs/security/privacy-and-contexts.md §8.1; each is shown for the mode it names:

- standard: This node can read your prompt and your answer. It should not learn who you are.
- attested: This node should not be able to read your prompt. A physical attack on the hardware can break that.
- verifiable: This node and the verifier you chose can read your prompt. They should not learn who you are.
- relay: The relay sees your network address and not your prompt. The node sees your prompt and not your network address.

**The headline.** Computed from the sheet, never hand-written (docs/security/privacy-and-contexts.md §8.3):

> **{counts.operatorReadable} nodes can read your prompt.**
> {if counts.attestedRecipients > 0:} **{counts.attestedRecipients} more process it inside a TEE and should not be able to read it.**

The client substitutes the numbers and makes the noun and verb agree with them ("1 node can read your prompt"); it changes no other word. `readersOfFullPrompt` is shown beside the headline as the floor of nodes that receive prompt text: it never shrinks because a recipient is attested.

**Single-node default (standard mode).** Generated for one recipient with `operatorReadable = true`:

> **1 node can read your prompt.**
> Floor of readers: 1 node run by 1 operator receives prompt text.
> *{node name}* run by operator *{operator address}*: This node can read your prompt and your answer. It should not learn who you are.
> Relay *{relay endpoint}*: The relay sees your network address and not your prompt. The node sees your prompt and not your network address.
> What is public on-chain: the node, the relay, the model, the mode, the denomination your note came from, the sizes of your messages, the prices and the timing. Your deposit is public and names your wallet; the session does not. Names, addresses and other identifying details you type can still reveal who you are to the node (evidence register §16, [L]/[V]). Nobody can give you a refund for a bad answer; you pay for the chunks you receive until you press Stop.

**Single-node attested.** Generated for one recipient with `operatorReadable = false`:

> **0 nodes can read your prompt.**
> **1 more processes it inside a TEE and should not be able to read it.**
> Floor of readers: 1 node run by 1 operator receives prompt text.
> *{node name}* run by operator *{operator address}*: This node should not be able to read your prompt. A physical attack on the hardware can break that.
> Relay *{relay endpoint}*: The relay sees your network address and not your prompt. The node sees your prompt and not your network address.

The two banners differ in their headline and in their per-node sentence, and the client never shows one in place of the other.

**Attested filter copy (screen 5 and the banner).**

> Attested nodes run inside a trusted execution environment and prove which software they run before you send anything. This node should not be able to read your prompt. A physical attack on the hardware can break that.

When the user requires attested mode and no node in the pool is eligible, the request fails closed with the copy of section 8 ("No node in this model's pool offers attested." / "This node could not prove its software. Nothing was sent."). There is no fallback to standard mode and no offer of one.

**Verifiable mode.** The per-node sentence for both nodes is the verifiable sentence above, and the client adds:

> That is two readers, not one. Both nodes can see on-chain that this session is checked; a node can behave honestly only here and differently elsewhere.

Because a session's mode is public on-chain, verifiable mode checks only verifiable-mode sessions. The client therefore offers, as a separate opt-in, **unannounced spot checks** of standard-mode sessions: the user re-runs a sampled prompt on another node, through a relay and on its own credit session, which then reads it and is disclosed as a reader for that check. This is not a proof either; it is a sample.

**Multi-node variant.** Generated from the disclosure sheet, never hand-written:

> **{counts.operatorReadable} nodes can read your prompt.** {if counts.attestedRecipients > 0:} **{counts.attestedRecipients} more process it inside a TEE and should not be able to read it.**
> Floor of readers: {readersOfFullPrompt.nodes} nodes run by {readersOfFullPrompt.operators} operators receive prompt text.
> {for each recipient:} *{node name}* ({roles}) receives {receives list}. {the normative sentence for its mode}
> {for each session:} relay *{relay endpoint}*, drawn from {eligibleRelaySetSize} relays; note from a group of {observedGroupSize}{if belowThreshold: — this group is small}.
> The relay sees your network address and not your prompt. The node sees your prompt and not your network address.
> What each is sent, counting every node once: {counts.fullPrompt} sent your full prompt; {counts.subTask} sent a sub-task that may quote it; {counts.otherAnswers} sent other nodes' answers or outputs. {if activations > 0:} {counts.activations} sent model activations, from which the prompt can be recovered — this is experimental. {if draftTokens > 0:} {counts.draftTokens} sent your prompt plus draft tokens — this is experimental.
> Total cap across all sessions: {totalCapEth} ETH, one note per session. L2 fees, shown separately: about {l2GasEstimateEth} ETH.
> Nothing is sent to any of these nodes until you confirm below.

The headline counts recipients by `operatorReadable`; the floor line is `readersOfFullPrompt`; the payload line lists kinds from `counts`, where each node appears under exactly one kind and `counts.fullPrompt` is only the nodes literally sent the full prompt (docs/security/privacy-and-contexts.md §8.3). These numbers never add up to each other and the banner never implies they do. `{totalCapEth}` is `totalCapWei ÷ 10^18` and `{l2GasEstimateEth}` is the gas estimate in ETH, both printed as decimals with the unit; raw wei never appears in user-facing copy (section 6). An attested request fails closed unless every recipient whose `receives[]` is non-empty is attested; the client never mixes an attested executor with an operator-readable synthesizer, reviewer or verifier.

**No multi-node feature starts without the user confirming that sheet.** The client records the confirmation of the sheet's `version`, binds `requestId` and `sheetVersion` into every envelope's AAD, and refuses to hand a spend proof to any node, or dispatch any job, for a request whose current sheet version has no confirmation. If anything changes — a node added or swapped, a relay changed, a model changed, what any node receives widened, a cap raised, a price changed, a reader (such as a verifier) added — the sheet's version increments and the banner is regenerated and shown again before any spend or job under it. The order is always pick models → see the sheet → confirm → spend; the client never confirms a sheet and then changes models. The banner and every table are generated from the sheet JSON and must match it exactly.

## 6. Price and cap display

Two numbers are always separate: **service cost** (ETH paid to nodes, and through them to relays, by vouchers) and **L2 fee** (gas for the user's own wallet transactions: `depositNote`, `ragequit`, `withdraw`). The node bears the gas of `openSessionFromCredit` — about 230–270k L2 gas, an estimate for Semaphore's own `validateProof` and not a measurement of this contract (evidence register §15 [U]) — and prices it into its offer; it is part of the service cost and is never shown as the user's gas. `closeSession`, `finalize`, `claimChange` and any `setContext` anchor are submitted through a relay or broadcaster, never from the deposit wallet; no document sets a fee for that, and if a broadcaster asks one the client shows it separately in ETH. The client never folds service cost and gas into one number and never hides the inference payment inside gas.

**Units.** Every amount in user copy is shown in ETH as a decimal with the unit: a wei amount is divided by 10^18 (as a formatting example only, not a denomination, 50,000,000,000,000,000 wei is shown as "0.05 ETH", never as "50000000000000000 ETH"), and an L2 gas estimate is shown in ETH with the unit too. Raw wei never appears in user-facing copy; the exact wei is available on request (section 9). No denomination, relay fee or bond value is set in any document; the client reads them from the chain.

| Shown | Meaning |
|---|---|
| Cap | `min(depositWei, maxSpendWei)` for this session, which on a credit session is the denomination of the spent note; the most this session can ever pay |
| Running total | `cumulativeWei` of the last voucher the client signed; rises chunk by chunk |
| Remaining allowance | the cap minus the highest `cumulativeWei` the client has signed in this session, redeemed or not; never the cap minus `settledWei` |
| Signed but not yet on-chain | the running total minus what `VoucherRedeemed` events show; owed, not yet redeemed |
| Relay share | the first `relayFeeWei` of the settled value, paid to the relay out of the service cost, never on top of it; `relayFeeWei` is copied onto the session at open and may be 0 |
| Change | `pendingWei = depositWei − settledWei`, recorded at `closeWithVoucher` or `finalize` and returned by `claimChange` as fresh notes plus dust; the full denomination when nothing was settled |
| Dust | `pendingWei` minus the sum of the change notes, below the smallest denomination, credited to the node |
| L2 fee | the user's own wallet transactions: estimate before signing, actual after inclusion; never part of the cap |

**Cap exhaustion.** The client never signs a voucher above the cap: when the next chunk would take the running total past it, the client stops signing and the node pauses; the chat view shows "cap reached" with two choices: **continue in a new credit session** or close. `topUp` reverts on a credit session, so continuing means closing this session and spending a new note on the same node through a newly drawn relay; because a new session is a new note and a new cap, a new disclosure sheet version is shown and confirmed before that spend. The unused remainder of the exhausted session, if any, returns as change. The "re-sign the same totals under a new `seq`" recovery of docs/protocol/contracts-and-settlement.md §8 applies only if a voucher above the old cap had been signed and only partly paid, which this client never does. The answer that was cut off is marked truncated.

**An unfinished, unsigned tail is not a charge for the whole cap.** If the user presses Stop, the connection drops, or the node stops, the user owes exactly what the signed vouchers say — at most the chunks received — and the rest of the note returns as change after settlement. The cap bounds the loss; it is not the price.

**What is never shown as free.** The input voucher is signed before prefill; a prompt that is never answered still cost its input fee. The spend history records it as such. The converse also holds: a prompt the user stops before signing its input voucher costs nothing and its tokens never enter the session's counts — the counts are the totals of the last voucher signed, and an unsigned receipt binds nobody (docs/protocol/off-chain-api.md §8).

## 7. Contexts

Contexts are local-first: transcripts, documents and system prompts live on the user's device, encrypted under a random key per version (docs/security/privacy-and-contexts.md §7), many per wallet. Each context has its own **context key**, generated from the OS CSPRNG, never the wallet key and never derived from it; `contextId = keccak256(contextPubKey)`. Nothing ties a context to the wallet: not on-chain, not in the AAD, not in the grant (docs/adr/0012-contexts-without-a-wallet-link.md). The list of the wallet's contexts lives only in the local vault, encrypted under the identity key, and in the backup; the client never sends it to a node, a relay or a context host.

**A grant is a local re-wrap signed by the context key.** A context is shared with a node by a grant that wraps exactly the granted versions' keys to that node's registered HPKE key and carries `contextPubKey` and a `contextSignature` by the context key over every grant field. The SDK's `grant()` builds and signs grants entirely on the device: there is no wallet prompt, and `sessionSigner` never signs a grant. Switching node means issuing a new grant to the new node (re-wrapping), never sending plaintext anywhere. The grant travels inside the job plaintext, under the job's HPKE envelope, through the relay, with the signed head records from version 1 beside it so the node can verify the hash chain (docs/protocol/off-chain-api.md §9).

**Ciphertext reaches the node inline.** By default the client uploads the granted versions' ciphertext in the job's own upload frames; an optional `blobUrl` to a public `https` host is allowed only under the restrictions of docs/protocol/off-chain-api.md §9, and a node may refuse it, after which the client re-sends inline.

The client:

- shows, per context, every version, its `contentHash`, which nodes currently hold a grant and until when (`expiresAt`, unix seconds), and whether the context is anchored;
- publishes a new version as a head record `(contextId, version, contentHash, prevContentHash)` signed by the context key, to the context host by compare-and-swap on `version == head + 1`, through a relay; on a race with another device it keeps the local edit, rebases on the new head and publishes the next version, telling the user where the edits overlap;
- persists every accepted head checkpoint in the vault and the backup and rejects any head behind one; it says plainly that the context host is trusted for sequencing as well as availability, that a host can equivocate between two devices that have never compared checkpoints, and that a device restored from a stale backup accepts a head a newer device would reject until the two sync;
- offers an optional public anchor, `setContext(contextId, version, contentHash, contextPubKey, signature)` submitted by a broadcaster through a relay, never by the wallet; it is required whenever the user is promised one consistent head across devices, and the client says that an anchor links that context's versions on-chain;
- optionally stores ciphertext, key-wrap records and head records at an owner-chosen host; the registry never holds content;
- exports a backup that contains the identity key, every key-wrap record, the context keys, the note secrets and the head checkpoints, but no ciphertext. A context whose ciphertext existed only on a lost device is gone even with the backup; the client says so on screen 18 and recommends at least one host or a second device;
- shows the `anonymity.contextLinkage` line of the sheet: a node that receives grants for the same `contextId` across sessions can link those sessions, and forking the context under a new key starts a new pseudonym with no history;
- marks revocation honestly: revoking a node stops future grants and makes every later version unreadable to it; it cannot make the node forget versions it already decrypted.

Context tokens are input tokens: granting a 20,000-token context to a job adds 20,000 tokens to the input receipt and the input voucher, and the chat view shows that before the prompt is sent.

## 8. Failure states

What the user sees and what funds are at risk. In every case a signed voucher stands; the user never loses more than the signed total of each session, and never the whole cap for an unsigned tail.

| Failure | What the user sees | Funds at risk |
|---|---|---|
| Relay unavailable | `relay_unavailable`: "No relay is available. Nothing was sent." The request fails closed; the client never connects to the node directly and offers no option to connect directly. | none; no spend sent, no session opened |
| Spend rejected by the node | `credit_spend_rejected` with its reason. `unknown_root`: the client re-reads the root through the relay and re-proves. `unknown_denomination`: the client picks another node or group. `bad_proof`: the client re-proves once and otherwise stops. `spent_nullifier`: the client checks through the relay for a `CreditSessionOpened` or `NoteRagequit` with that nullifier before marking the note spent, and never marks it spendable again | none from the rejection itself; a note is lost only if its nullifier is already used on-chain |
| Group below the warning threshold | `anonymity_set_below_threshold`: "Only {n} notes are in this group. Others may be able to link this session to your deposit." Shown before proving; the user decides. The threshold is unset and no authoritative minimum exists (evidence register §15 [U]) | none; nothing sent until the user decides |
| Node withholds the spend | `note_in_flight` past `spendSubmitTimeout`: "The node has not opened your session." The client may spend the same note with another node through a new proof; the withheld proof then reverts on the stored nullifier | none; a late submission opens a session the client closes unilaterally and claims back as change |
| Node offline mid-stream | the answer stops, is marked truncated only when a frame that a sent voucher should release, or a frame replayed after a resume, has not arrived within `interFrameTimeout` (2 × the node's advertised `maxInterFrameMs`); the timer does not run while the client prepares its next voucher, and a response that ends at the input-receipt or a payment boundary is not truncation (docs/protocol/off-chain-api.md section 3); the client reconnects through the same or another relay for `reconnectWindow` (the node resends from the last frame the client received; identical duplicates are ignored; the client re-sends its latest voucher, a no-op if the node already holds it, and resumes from its own log), then offers Close (cooperative: a final voucher if the node returns; otherwise unilateral: `closeSessionUnilateral`, `finalize` after `closeDeadline`, then `claimChange`) | chunks already signed for; the remainder returns as change after the close window |
| Lost voucher log (device reset mid-session) | "This session's records are gone; nothing more will be signed on it." The client uses only the unilateral close, offers `finalize` after `closeDeadline` and then `claimChange` if the `sessionSigner` key survived, and never resumes from the node's figures. Further work needs a new session, which is a new note and cap: a new disclosure sheet version is shown and confirmed before that spend | vouchers the node already holds stand; the remainder returns as change only while the `sessionSigner` key exists |
| Lost `sessionSigner` | "This session's signing key is gone." The client cannot sign a voucher, a broadcast `closeSession` or `claimChange`. The node can still redeem and close, and `finalize` records `pendingWei`, but **nobody can claim that change**: `claimChange` needs a `sessionSigner` signature. If the node is gone too, the session stays open | the unspent remainder of that note |
| Lost note store | "Your unspent notes are gone from this device." Restore from the backup on screen 18; a note whose secret is in no backup cannot be spent, ragequit or recovered: there is no admin and no recovery | the face value of every unspent note not in a backup |
| Lost wallet | stated honestly on screen 3: notes in the vault can still be spent in sessions, because spending needs the note secret, not the wallet; a credit session has no user address, so no refund is trapped behind a lost wallet. What is lost is the ability to `ragequit`, which only the depositing address may call, and any balance a past ragequit credited to the wallet but that was not withdrawn. If the note secrets lived only on the same lost device, the notes are lost too (lost note store) | the ragequit exit and any unwithdrawn balance |
| Attestation failed | "This node could not prove its software. Nothing was sent." The request fails closed; no fallback to standard mode | none; if a session was already opened, `closeSession` with the `sessionSigner` signature, `finalize` and `claimChange` return the full denomination as change |
| No eligible node for the required mode | "No node in this model's pool offers {mode}." The request fails closed | none |
| Empty or thin pool | "No node offers this model" or "Only {n} nodes offer this model; prices may be uncompetitive" | none |
| Stale context | `stale_version` or `context_hash_mismatch`: "Your context changed since this grant was made" with a rebase-and-republish action | nothing charged for that job |
| Cap exhausted on one session | "Cap reached on {node}" with continue-in-a-new-session or close; in a plan, only that task pauses | signed total of that session |
| Sequencer delay | "Arbitrum's sequencer is slow or down; a transaction can be force-included from L1 after about a day" (evidence register §1 [V]); vouchers continue off-chain | a node that redeems late may lose vouchers to the close deadline (docs/protocol/contracts-and-settlement.md R2); the user loses nothing |
| One sub-task node of a plan offline mid-wave | that task is marked failed; the client retries only on a node that was on the confirmed sheet, with a new credit session; the vouchers signed for the failed node stand | the failed node's signed total; one more note is spent |
| Contested or incomplete collective answer | the disagreement view shows every answer and critique and the synthesizer's objection if any; the client never presents the result as verified. "Incomplete" means only that required fields are missing or malformed; disagreement between the two position-swapped review passes is expected (position bias) and an empty splits list is valid | every session's signed total |
| Pool cannot fill the confirmed set | "A node on your confirmed sheet is no longer available." The request fails closed; sessions already opened are closed | nothing beyond the signed totals; the remainders return as change |
| Stale disclosure sheet | "The plan changed since you confirmed." The new sheet is shown; nothing is sent until it is confirmed | none for the unsent part |
| Prices copied into the session on-chain differ from the sheet | "The node changed its price; nothing was sent." The unilateral close is submitted through the relay; the full denomination returns as change after `finalize`. Only the on-chain copied prices can raise this; a different price in the node's `welcome` is logged and the node is dropped, but never locks the note behind a close | none beyond the delay; the spend message binds the prices, so a changed offer normally makes the spend revert |
| Only some of N spends opened | "{k} of {N} sessions opened. Nothing was sent." Close is offered on the opened ones (final voucher with zero output, or the unilateral close), then change | none beyond the delay; zero-use sessions return the full denomination as change |

## 9. Accessibility

- Every control is reachable and operable by keyboard; focus order follows reading order; the banner receives focus when shown and is announced.
- Nothing is conveyed by color alone: class labels carry their words (S Small, M Mid-size, L Large, X Largest); modes carry text; experimental features carry the word "experimental"; a truncated answer carries a text marker, not only a tint; a small-group warning carries words, not only a color.
- The chat stream uses a live region with polite announcements per chunk boundary, not per token.
- Layouts work from narrow phone viewports (one column, the running total pinned) to wide desktops (chat, context sidebar and spend side by side); no horizontal scrolling at 320 px width.
- Numbers are shown with units (ETH, tokens) and never abbreviated in a way a screen reader mispronounces; wei values are converted to ETH decimals for display (section 6) and the exact wei is available on request.
- Proof generation on screen 11 shows progress and announces completion; it never blocks keyboard focus.
- Timeouts that end a session (section 8) are announced before they expire and can be extended where the protocol allows.

## 10. Dapp categories the community can build

The SDK is general; the chat client is one use. Categories the community can build on the same contracts and API:

| Category | What it needs from the protocol |
|---|---|
| Chat | credit sessions, the relay transport, streaming, contexts for transcripts |
| Document Q&A over private contexts | context grants per version signed by the context key; local-first storage; a node that supports large `maxContextTokens` |
| Coding assistants | task decomposition with a reviewer of a different model family; a test harness on the user's side, because the protocol cannot judge code quality |
| Agents | **inference only**: the protocol provides answers, never permission to act; any tool or external action is the dapp's own responsibility and must be gated by the user, not by model output |
| On-chain apps calling inference | an app contract cannot call a node; a user or a relayer the app trusts spends a credit for the session, and the result is brought on-chain by whoever the app trusts; verifiable mode gives a second opinion, not a proof |
| Compatibility adapter | a wrapper exposing the widely used chat-completions request shape so existing tools work; it **must encrypt on the client side and send through a relay before any untrusted hop** — an adapter that forwards plaintext to a gateway that then encrypts is not a Comuns client |

**Developer onboarding on Arbitrum Sepolia.** No deployment is claimed. Phase 1 exercises the credit path. When the testnet-only CIP registers Sepolia models and bands and sets a testnet-only ladder of at least two denominations (values unset for mainnet; CIP-0004 proposes a testnet-only, non-normative table; docs/protocol/contracts-and-settlement.md §15 R14 and §16 Q20), a developer would: connect a wallet on Arbitrum Sepolia; point the SDK at the testnet escrow and registries; list the testnet relays and pool; `deposit` testnet ETH into a note; spend that note on a session through a relay; run a partial spend and claim its change into at least one smaller note plus dust; open a zero-use session and claim the full denomination back as change; `ragequit` one note and `withdraw` the balance; run every walkthrough of the contracts document; and run the disclosure-sheet conformance test (docs/security/privacy-and-contexts.md §12) against their own client. Experimental features appear only when a testnet price exists.

## 11. What this client will not do

- Host prompts, contexts or answers on any project-run server.
- Offer a second account system: no email, no password, no social login.
- Send the wallet address, an account, an API key or any persistent identifier to a node or a relay.
- Open a direct job connection to a node, for any message or any session-specific chain read, or fall back to one when no relay is available.
- Fund a session from the wallet (`openSession`), offer that as a mode, or offer any toggle that reveals the wallet to a node.
- Reuse a `sessionSigner` across sessions or a Semaphore identity across notes, or publish a commitment before its secret is stored.
- Generate a spend or ragequit proof anywhere but on the user's device.
- Offer local execution: inference runs only on network nodes, and the client performs no model computation.
- Hide the inference payment inside L2 gas, or show one number for service cost and gas.
- Auto-route to the cheapest node. The user picks the node, or confirms a ranked set; ranking is advisory.
- Silently add a node to a request, switch a request to a multi-node feature, change a relay, widen what any node receives or raise a cap without re-showing the disclosure sheet and obtaining a confirmation.
- Fall back to a node that was not on the confirmed sheet, or downgrade an attested request to standard mode.
- Confirm a sheet and then change the models, nodes or readers under it; the order is pick models, see the sheet, confirm, spend.
- Sign a voucher above the effective cap, or resume a session from a node's reported totals instead of its own voucher log; after a lost log it closes unilaterally and signs nothing.
- Close a session because of a price a node merely reported; only the prices copied on-chain are compared with the sheet.
- Show raw wei in user copy.
- Sign a context grant, head record or `setContext` with the wallet; the context key signs all three.
- Run `model_sharding` or `cross_node_speculation` under mainnet parameters; both exist only with testnet-only prices.
- Present a collective answer as verified, or hide a disagreement inside a collective answer.
- Delegate `sessionSigner` to an orchestrator node in v1; the orchestrator node holds no session key, custodies no funds and signs no voucher on the user's behalf.
- Collect seed phrases, private keys or wallet passwords under any pretext.
- Hide the fact that a quality refund is impossible: a signed voucher is not reversed by anyone.
- Call `eth_getEncryptionPublicKey` or `eth_decrypt`, or derive an encryption key from a wallet signature by default.
- Send a transaction per message.

## 12. Risks

### R1 — Compromised or dishonest client **[RISK] · High**

A client that skips the sheet, miscounts readers, seals to the wrong key, connects directly or sends the wallet address defeats every guarantee. Mitigation: open-source reference client; the disclosure-sheet and relay conformance tests (docs/security/privacy-and-contexts.md §12); `sheetVersion` bound into the AAD so a log audit can find divergence.

### R2 — Wallet, note and key UX **[RISK] · High**

Users may lose the backup, the device holding note secrets or ciphertext, a `sessionSigner` with unclaimed change, or the wallet. Each loss is permanent in a different way (sections 7 and 8), and a lost note has no admin and no recovery. Mitigation: the vault writes every secret before its commitment is published; screen 18 says exactly what each loss means; the backup format is an open question.

### R3 — Price and pool volatility **[RISK] · Medium**

Prices change between pool listing and the spend. `openSessionFromCredit` reverts on a changed price and consumes no nullifier, so no note is lost, but the user must re-confirm. Mitigation: refresh the pool just before the sheet; show a one-wei change as a change.

### R4 — Automatic signing pays for bad answers **[RISK] · Medium**

Voucher signing checks counts, not quality. Mitigation: the Stop control; small denominations; spend history; reputation.

### R5 — Orchestrator-node dependency for thin clients **[RISK] · Medium**

A thin client that relies on an orchestrator node to plan gives that node the full prompt and the plan. Mitigation: the node is optional, reached through an ordinary credit session after its own sheet, and never holds `sessionSigner`.

### R6 — Experimental features reach users **[RISK] · Medium**

Sharding and cross-node speculation, if exposed, widen the reader set in ways users do not expect (activations recover prompts, evidence register §10 [V]). Mitigation: hidden unless a testnet price exists; labelled experimental; the sheet counts activations and draft tokens.

### R7 — Stolen `sessionSigner` on the device **[RISK] · Medium**

The app-local key signs vouchers and envelopes up to the cap until settlement, and it also authorises `closeSession` and `claimChange`, so a thief can redirect the change of that session to notes it controls. Mitigation: one note per session caps the loss at one denomination; keys encrypted at rest; deleted once the change is claimed; rotation is an open question for a later CIP.

### R8 — Deposit-to-spend and change timing link sessions to a wallet **[RISK] · High**

The deposit is public and names the wallet. A spend soon after a deposit into a small group, or a change note spent soon after its session settles, is linkable by timing (evidence register §15 [V]). Mitigation: the client shows the group size, warns below the threshold and recommends a delay before spending; both delays and the threshold are unset, and no authoritative minimum anonymity set exists (evidence register §15 [U]).

### R9 — The prompt identifies its author **[RISK] · High**

In standard mode the node reads the prompt, and names, addresses and writing style can deanonymize the author whatever the transport hides: attribute inference from text reaches up to 85% top-1 accuracy and pseudonymous-profile linking up to 68% recall at 90% precision (evidence register §16, [L]/[V]). Mitigation: the banner says so; the client cannot prevent it.

## 13. Open questions

1. **Wallet library.** Which EIP-1193 wrapper to use, and how to support contract wallets whose `depositNote` or `ragequit` is a batched user operation.
2. **Session keys and account abstraction.** Whether a later CIP lets a smart account authorize `sessionSigner` as a session key with a spending limit, and whether that could be done without linking the session to the account — future work, not v1.
3. **Backup format.** The password-based KDF, versioning and update cadence of the encrypted export of the identity key, key-wrap records, context keys, note secrets and head checkpoints; whether an optional ciphertext bundle is offered (docs/security/privacy-and-contexts.md §14).
4. **Package name and distribution.** The SDK's name, whether it ships a WASM HPKE build and a native or WASM Groth16 prover by default, and how the reference client is distributed without a project-run server. ADR 0013 proposes one code repository with the client in a `client/` directory; the package name stays undecided. The prover choice is also a license question: @semaphore-protocol/proof 4.14.3 depends on snarkjs 0.7.5, whose npm license field is GPL-3.0, and core pulls proof in (evidence register §8, recheck 2026-10-15, [V]); the licenses of other provers are not in the register (UNVERIFIED); RR-50 is the review item and no legal conclusion is drawn here. The package name and the native-versus-WASM choice stay open.
5. **Batching spends.** Whether the N spends of a plan should be submitted together, staggered or through distinct relays, given that sessions opened in one window are correlatable (docs/security/privacy-and-contexts.md §9).
6. **Reputation source.** Which community indexers the client lists by default, if any, how a user adds their own, and how reputation queries avoid revealing which node the user is about to pick.
7. **Note-store backup.** How often the client refreshes the backup as deposits and change create new note secrets, whether a note created after the last backup should block further spending until the backup is refreshed, and how a restored device reconciles notes already spent elsewhere (by nullifier, read through a relay).
8. **`SessionMap` with a second session per pair.** Section 3 keys `SessionMap` to one `sessionId` per `(node, modelId)`, while docs/protocol/orchestration.md §6 allows a second, separately disclosed session for the same pair when two tasks of a wave must run in parallel. `SessionMap` should map a pair to a list of `sessionId`s (or to the sheet's session index), with the dispatcher choosing among them; the shape is open for the SDK.
9. **Relay-selection UX.** Whether the user should see and redraw the random relay at all or only on request, whether to prefer distinct relays per session of one plan, how to present the eligible relay set when it is small, and whether a user-chosen relay (for example one placed behind Tor) is offered and how it is disclosed on the sheet.
