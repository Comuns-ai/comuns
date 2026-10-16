# Dapps and SDK — chat on top of the session protocol

Author: Comuns contributors
Status: Draft
Category: Technical Proposal
Created: 2026-10-12

**Reference:** docs/protocol/off-chain-api.md, docs/protocol/contracts-and-settlement.md, docs/security/privacy-and-contexts.md, docs/economics/cost-and-pricing.md, docs/node/node-design.md, docs/adr/0010-anonymous-by-default.md, docs/adr/0011-anonymous-credits.md, docs/adr/0012-contexts-without-a-wallet-link.md, docs/adr/0016-funding-edge-and-deposit-key.md, docs/adr/0017-accounts-and-decentralized-access.md, docs/adr/0018-one-client-stack.md

---

## 1. Summary

This document proposes a reference chat client and a TypeScript SDK for Comuns, the community proposal for open-source decentralized LLM inference settled on Arbitrum One. Nothing described here exists yet; no package is published and the package name is undecided.

The client is deliberately thin, and it is anonymous by default (docs/adr/0010-anonymous-by-default.md). It owns five things and nothing else: the user's wallet connection (EIP-1193), which signs `depositNote`, `ragequit` and `withdraw`, and only if the user opts in does it also sign account setup, a bounded swap or intent in its own account, and a deposit-key grant and its revocation (ADR 0016, proposed). The deposit key signs only `depositNote`. No account key, deposit key or login ever signs a voucher, envelope, spend, close or `claimChange`, and none is sent to a node or a relay; the wallet is never prompted per session, per chunk or per context grant; an app-managed HPKE keypair that is never the wallet key; a local, encrypted vault holding the note secrets, the context keys, the key-wrap records and the accepted context head checkpoints; a fresh `sessionSigner` per session; and the relay transport through which every job and every session-specific chain read travels. Everything else is the protocol: credit notes, sessions and vouchers from docs/protocol/contracts-and-settlement.md and docs/adr/0011-anonymous-credits.md, envelopes, the credit flow and frames from docs/protocol/off-chain-api.md, modes, features and the disclosure sheet from docs/security/privacy-and-contexts.md, and ownerless contexts from docs/adr/0012-contexts-without-a-wallet-link.md.

What the user does, in order: connect a wallet on Arbitrum One and choose an RPC endpoint; **deposit** ETH once into a fixed-denomination credit note (`depositNote`, the one public, wallet-linked step of the payment path; an opt-in deposit key adds a public grant and its revocation, ADR 0016). The deposit may be funded from ETH the account already holds, through an optional card purchase, or from a stablecoin converted to ETH in the user's own account first (ADR 0016, proposed), and it may optionally be refilled by a deposit key that can only call `depositNote`; the escrow holds only ETH. Later, **pick a model first**, then one node from that model's pool (or confirm a ranked set from it), and a relay drawn at random from the registry; choose the execution features (none by default, which means single-node); read the disclosure sheet and the banner; and **spend a credit**: the client proves on the device that it holds one note, hands the proof to the node through the relay, and the node submits `openSessionFromCredit`. The wallet is not asked to sign anything for a session. Every chunk is paid by an automatic voucher signature from `sessionSigner` within the cap, which is the note's denomination; no transaction is sent per message; the service cost is shown in ETH as a cap and a running total, separate from the L2 fee; the protocol fee is 0 and there is no token. Granting a context to a node is a local re-wrap signed by that context's own key, with no wallet prompt. Ending the session cooperatively signs one final voucher so the node settles; the unused remainder is recorded as `pendingWei` and returns as fresh change notes through `claimChange`. Multi-node features never start without the user confirming the disclosure sheet for that request.

The standard tier promises that the node can read the prompt but should not learn who sent it. The attested tier adds that the node should not be able to read the prompt either, barring a physical attack (evidence register §14). Inference runs only on network nodes; the client performs no model computation.

## 2. Scope

This is one reference client. **The client is not the protocol.** Anyone may write another dapp against the same contracts and the same off-chain API; the community categories in section 10 are examples. What this document fixes is what any honest client must show and must refuse (sections 5, 8 and 11), because the protocol's privacy promises depend on the client doing so (docs/security/privacy-and-contexts.md R5).

Binding decisions carried in, all PROPOSED:

| Decision | Value |
|---|---|
| Account | The funding account is the wallet (an injected wallet, an EIP-7702 EOA or a smart account) and it is the only required account; sessions have no account and no login is needed to spend. On the core path there is no email login, no password and no seed-phrase collection; an optional embedded wallet with email or social sign-in (ADR 0017, proposed) is a funding-surface convenience whose identity is never sent to a node or a relay. Where a provider offers Google, Apple or X sign-in it is an optional, disclosed, replaceable funding convenience; neither the login identity nor the wallet address is sent to a node or a relay, and the client never collects a seed phrase |
| Funding | Anonymous credits (docs/adr/0011-anonymous-credits.md): `depositNote` from the wallet, then one note per session spent by `openSessionFromCredit`, submitted by the node. The wallet-funded `openSession` has no call site in this client and is not offered as a mode. An on-ramp or swap output lands in the user's own account before `depositNote`; no helper contract, router, solver or on-ramp is ever the depositor (ADR 0016, proposed) |
| Transport | Every job, frame, voucher, `closeSession`, `claimChange` and session-specific chain read goes through a relay (Oblivious HTTP); there is no direct client-to-node path and no fallback to one |
| RPC | User-chosen; registry-wide reads (models, pools, relays) may use it directly; every session-specific read (session lookup, settlement and change monitoring, Merkle witness and root) is tunnelled through a relay. An indexer is a backend behind that transport, not an alternative to it. No project-operated endpoint or matcher |
| Selection | Model-first; the pool of a model is every node whose `prices[modelId]` has a non-zero `modelBenchmarkHash`; the user picks a node or confirms a ranked set; any class may appear in any pool; `maxTier` is informational. The relay is drawn at random per session |
| Encryption | HPKE in the client with an app-managed keypair; `eth_getEncryptionPublicKey` and `eth_decrypt` are forbidden |
| Signing | The root account signs `depositNote`, `ragequit` and `withdraw`; only if the user opts in does it also sign account setup, a bounded swap or intent in its own account, and a deposit-key grant and its revocation (ADR 0016, proposed). The deposit key signs only `depositNote`, within its grant, and is neither `sessionSigner` nor `commitKey`. No account key, deposit key or login ever signs a voucher, envelope, spend, close or `claimChange`, and none is sent to a node or a relay. Vouchers, envelopes, `closeSession` and `claimChange` are signed by the session's fresh `sessionSigner`; head records, grants and any `setContext` anchor are signed by the context key. The wallet is never prompted per session, per chunk or per context grant |
| Payment | ETH, protocol fee 0, no token; never hidden inside L2 gas; the relay fee is paid from the first wei of the node's settled value, never by a user transaction; the unused remainder of a note returns as change notes. A funding-provider fee, if a convenience is used, is shown separately on the funding surface; it is not the cap and not a protocol fee |
| Core path | A local run or a content-hash-pinned build reached through an ENS `contenthash` with a verifying fetch; a user-chosen RPC; the user's own account; the permissionless relays and nodes. Every hosted login, on-ramp, orchestrator, sponsor, bundler, indexer or gateway can be absent and the client still works (ADR 0017 and ADR 0018, proposed) |
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
type AccountKind = "injected" | "eip7702" | "smart-account";   // the funding account; msg.sender of every depositNote
type FundingConvenience = "onramp" | "swap" | "intent" | "gas-sponsor" | "embedded-wallet";
// hosted, optional, disclosed, never in the spend path; the SDK core imports no provider SDK

interface DepositKeyGrant {           // ADR 0016 (proposed): exists only on an EIP-7702 EOA or a smart account
  escrow: Hex;                        // SessionEscrow on the chain in use; the only contract the grant names
  selector: "depositNote";            // the only selector the grant names
  denominationIndex: number;
  valueLimitPerUseWei: bigint;        // ceiling equal to the denomination; the contract enforces exact msg.value
  maxUses: number;
  validAfter: number; validUntil: number;   // unix seconds
  revokedOnChain: boolean;            // revocation is on-chain, chain by chain; deleting the local key is not revocation
}                                     // no node, relay, token or venue field, by design

interface RefillPolicy { minUnspentNotes?: number; everySeconds?: number; jitterSeconds?: number }
// all unset; never triggered by cap exhaustion, a send, a resume or a spend

interface ConnectOptions {
  provider: EIP1193Provider;          // the wallet: used only for depositNote, ragequit, withdraw and the optional deposit-key grant and revocation
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
  l2GasEstimate: bigint;              // the user's own account transactions, including a deposit-key depositNote; a sponsor-paid fee is shown as sponsored, never folded into totalCapWei
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
  // Generates a fresh Semaphore identity, stores its secret durably in the vault, THEN sends
  // depositNote(identityCommitment, denominationIndex) with msg.value equal to the denomination. Public and wallet-linked.
  // Sent by the wallet or by the deposit key; msg.sender is always the user's own account so the ragequit allowance (depositedWei) stays with the user's account.
  grantDepositKey(grant: Omit<DepositKeyGrant, "revokedOnChain">): Promise<{ txHash: Hex }>;   // opt-in; signed once by the root account; public on-chain
  revokeDepositKey(grant: DepositKeyGrant): Promise<{ txHash: Hex }>;                           // on-chain, chain by chain
  setRefillPolicy(policy: RefillPolicy): Promise<void>;     // values unset; runs inside the funding module only
  refillNow(denominationIndex: number): Promise<{ commitment: bigint; txHash: Hex }>;   // manual; honours spendableAfter
  fundingOptions(): Promise<FundingConvenience[]>;         // what the user enabled; the SDK core imports no provider SDK
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
- `topUp` reverts on a credit session and the SDK has no call for it. When the cap is exhausted the client opens a new credit session with a note already in the vault that has passed the unset delay, and never deposits in that action (section 6).
- Sessions are keyed by the pair `(node, modelId)` (`SessionMap`): one node may serve two models of a plan, and two nodes may serve the same model, so a single `Hex` key would collide and route a job onto the wrong session. A session runs one job at a time (`maxConcurrentJobsPerSession = 1`, docs/protocol/off-chain-api.md §3); `run` dispatches a wave's tasks concurrently only across different sessions and runs two tasks that share a session one after the other, unless the sheet lists a second session for that pair.
- Price checks read the chain, not the node: after `SessionOpened` and `CreditSessionOpened` are visible through the relay, the SDK compares the prices copied into the session on-chain with the confirmed sheet; prices a node reports in `welcome` are informational and never trigger a close. The spend message binds the expected prices, so a changed offer makes the spend revert and consumes no nullifier.
- `orchestratorNode`, if set, sends the plan request to a node that advertises `roles.orchestration` through an ordinary credit session, after a disclosure sheet saying that node will see the full prompt and the plan. The orchestrator node holds no `sessionSigner`; the user's client still opens every downstream session and signs every voucher.
- The compatibility adapter (section 10) that exposes the widely used chat-completions request shape of hosted inference APIs is a wrapper over `chat`; it encrypts on the client side and sends through a relay before any untrusted hop, and never forwards plaintext to a gateway.
- **The isolation rule (ADR 0017, proposed).** Provider adapters for a `FundingConvenience` are separate packages loaded only by the funding surface, only after the user chooses that convenience and only on funding screens; the SDK core imports none of them. The chat client and the funding surface run in distinct origins with separate storage: on the web as two origins, and in native builds as separate webviews with distinct origins and capability sets. A same-origin window, a worker or an iframe is not the boundary; this is a design rule, not a cited fact. No provider iframe or script runs inside a privileged webview. The funding capability set denies every vault, note-secret, prover, `sessionSigner`, `commitKey`, context-key and relay command, there are no wildcard grants, and a narrow bridge validates both the sender and the payload. What may reach the provider (the public funding allowlist): the chain id, the account address and the denomination; the `depositNote` calldata the funding surface builds, which carries the public `identityCommitment`; grant and revocation metadata; user-authorized `ragequit` calldata; and transaction results. What never crosses (the session denylist): note secrets, trapdoors, nullifiers and preimages; spend and change requests; session ids, `sessionSigner`, `commitKey` and context keys; vouchers; relay and node choice; prompts, answers and contexts.
- **The refill rule (ADR 0016, proposed).** A refill made with the deposit key fires on an unspent-note threshold or on a schedule with random jitter, into a buffer of notes that honour `spendableAfter`; the refill job runs inside the funding module only. It never fires at cap exhaustion, on a send or resume event, or immediately before a spend. Threshold, schedule, jitter, buffer size and both delays are unset; `RefillPolicy` ships with every field unset and automatic refills stay unavailable until a reviewed timing policy is adopted (section 13).

## 4. Screens and flow

Twenty-two named screens. Every screen is reachable by keyboard (section 9). The protocol wallet is prompted on screens 3, 19 and 21 only: Deposit and notes (screen 3), for `depositNote` and `ragequit`, Withdraw balance (screen 19), and Automatic refills (screen 21), for the opt-in deposit-key grant and its revocation. Screen 20's provider widget is not the protocol wallet; it may prompt the funding account inside the isolated funding surface. No screen asks the wallet to sign a session, a voucher or a context grant.

| # | Screen | What it does | What it must show |
|---|---|---|---|
| 1 | **Connect or create a funding account** | EIP-1193 connect of an injected wallet, an EIP-7702 EOA or a smart account; checks the chain is Arbitrum One (or Arbitrum Sepolia in developer mode); an optional embedded wallet with social sign-in, where a provider offers it, is offered only inside the isolated funding surface (section 12) | "no login is needed to spend"; "an optional embedded wallet lets its provider link your sign-in to your deposits"; "your wallet funds your deposits; it is never shown to a node". On the core path there is no email login, no password and no seed-phrase collection; an optional embedded wallet with email or social sign-in (ADR 0017, proposed) is a funding-surface convenience whose identity is never sent to a node or a relay |
| 2 | **Network and RPC** | The user enters or picks an RPC endpoint and optionally an indexer; the client never defaults to a project-run endpoint | which endpoint sees registry-wide reads; that every session-specific read goes through a relay |
| 3 | **Deposit and notes** | Lists the denominations and each group's observed size; `deposit` sends `depositNote` from the wallet after the note secret is stored; lists the notes in the local store with their state; offers `ragequit` per note | that the deposit is **public** and names the wallet; the group size of the chosen denomination; a recommendation to wait before spending a new note (the deposit-to-spend delay is unset and no minimum is adopted; evidence register §15 [V] for timing linkage); that `ragequit` is public, linkable to the wallet and bounded by the wallet's own deposits into that group; that a deposit key, if one is granted on screen 21, can repeat only `depositNote`, never pays a node or relay, and cannot `ragequit` |
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
| 20 | **Fund with a card or a stablecoin** | Opens in the isolated funding surface (section 12), never in the chat view; loads the chosen provider adapter only after opt-in; an on-ramp delivers ETH to the user's own address, never to the escrow; a stablecoin is swapped to ETH by an exact-output swap or intent inside the user's own account; the user then deposits from screen 3 or by a deposit-key refill (ADR 0016, proposed) | KYC, the provider fee, the delivered ETH, the quote expiry and who pays gas, each disclosed before the purchase; the provider fee as a separate line that is neither the cap nor a protocol fee; "Your deposits are public, and the provider can link them to your identity. Sessions do not include your wallet address or login identity. Timing, small groups, identifying content and collusion can still link activity."; "A stablecoin issuer can freeze its token; notes already deposited are ETH." |
| 21 | **Automatic refills (deposit key)** | Opt-in; the root account signs one grant naming the escrow contract, the `depositNote` function, the per-call cap equal to the denomination, the number of uses and the validity window; a revoke control sends the on-chain revocation, chain by chain; the refill policy (threshold, schedule, jitter) is shown with every value unset and automatic refills stay unavailable until a reviewed timing policy exists | the contract, function, cap, uses and window; that the grant and its revocation are public on-chain; that deleting the local key is not revocation; "This approval can only add credits within the limits shown. It never pays an inference node or relay, and cannot ragequit."; "Refills happen on a schedule, not when you run out, so a deposit is not followed at once by a session." |
| 22 | **Get the app and choose an RPC** | Shows the pinned build hash of the running client and how it was reached (a verifying fetch of the ENS `contenthash`, a locally run gateway, or a local run); links the desktop and mobile builds of the same stack (section 14); the user enters an RPC endpoint, and there is no default | the build hash to compare against the published one; "chain reads trust the RPC you choose"; that session-specific reads still go through a relay; that a store listing or a hosted gateway is a convenience the client works without |

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
    Note over U,W: optional: on-ramp or swap into the user's own account; a deposit key may send depositNote within its grant
    D->>W: depositNote(identityCommitment, denominationIndex) + denomination
    W->>E: one public transaction (the only wallet step for sessions)
    Note over U,D: later, after the recommended delay (unset)
    Note over D,N: no refill sits on any spend arrow below; a refill never fires at cap exhaustion, on a send or resume, or just before a spend
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

Two numbers are always separate: **service cost** (ETH paid to nodes, and through them to relays, by vouchers) and **L2 fee** (gas for the user's own account transactions: `depositNote`, whether sent by the wallet or by the deposit key, `ragequit` and `withdraw`; a sponsor-paid fee is shown as sponsored and disclosed, never folded into either number). Every inference amount stays in ETH; a card, swap or sponsorship charge is a separate line on the funding surface and is never added to the cap (ADR 0016, proposed). The node bears the gas of `openSessionFromCredit` — about 230–270k L2 gas, an estimate for Semaphore's own `validateProof` and not a measurement of this contract (evidence register §15 [U]) — and prices it into its offer; it is part of the service cost and is never shown as the user's gas. `closeSession`, `finalize`, `claimChange` and any `setContext` anchor are submitted through a relay or broadcaster, never from the deposit wallet; no document sets a fee for that, and if a broadcaster asks one the client shows it separately in ETH. The client never folds service cost and gas into one number and never hides the inference payment inside gas.

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
| L2 fee | the user's own account transactions, including a deposit-key `depositNote`: estimate before signing, actual after inclusion; never part of the cap; a sponsor-paid fee is shown as sponsored |

**Cap exhaustion.** The client never signs a voucher above the cap: when the next chunk would take the running total past it, the client stops signing and the node pauses; the chat view shows "cap reached" with two choices: **continue in a new credit session** or close. `topUp` reverts on a credit session, so continuing means closing this session and spending a new note on the same node through a newly drawn relay; because a new session is a new note and a new cap, a new disclosure sheet version is shown and confirmed before that spend. The new session spends a note already in the vault that has passed the unset delay; the client never deposits in that action, and no deposit-key refill fires because of it. When no eligible note exists the chat pauses with "No ready credits. Chat is paused." and offers a manual deposit (screen 3) or the next scheduled refill, if a deposit key is granted (ADR 0016, proposed). The unused remainder of the exhausted session, if any, returns as change. The "re-sign the same totals under a new `seq`" recovery of docs/protocol/contracts-and-settlement.md §8 applies only if a voucher above the old cap had been signed and only partly paid, which this client never does. The answer that was cut off is marked truncated.

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
| Lost wallet | stated honestly on screen 3: notes in the vault can still be spent in sessions, because spending needs the note secret, not the wallet; a credit session has no user address, so no refund is trapped behind a lost wallet. What is lost is the ability to `ragequit` using the lost account's net-deposit allowance; another address needs its own sufficient allowance and a valid note proof bound to it. Also lost is any balance a past ragequit credited to the wallet but that was not withdrawn. If the note secrets lived only on the same lost device, the notes are lost too (lost note store) | the ragequit exit and any unwithdrawn balance |
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
| On-ramp declined or delayed | "Your purchase was declined or is still pending with the provider." Shown inside the funding surface; no note was created, no deposit was sent; the user may retry, use another convenience or deposit ETH already held | none in the protocol; whatever the provider's own terms say about the purchase, which the client cannot see |
| Atomic exact-output swap not met | "The swap could not deliver the exact amount; nothing was converted." Applies only to an atomic exact-output swap whose revert is confirmed on-chain: the Uniswap v4 router reverts when the input needed exceeds `amountInMaximum` (evidence register §15, client UX research 2026-10-15, [V]); no deposit follows | funding-edge losses are possible (gas for the reverted transaction, and whatever the venue's own behaviour is where the revert is not confirmed); no `depositNote` was sent |
| Intent failed after delivery | "Your intent did not complete. Check your balances before depositing." A multi-chain intent may leave funds delivered before a later destination action fails, because it is not atomic (evidence register §4, client UX research 2026-10-15, [V]); the client reconciles the actual balances and the provider status, and does not deposit automatically | funding-edge losses are possible: funds may sit on an unintended chain or in an unintended token, and fees already charged are not returned; nothing in the protocol is at risk because no `depositNote` was sent |
| Deposit key expired, exhausted or revoked | "Automatic refills have stopped: the deposit key has {expired / used all its uses / been revoked}." Refills stop; screen 21 offers a new grant; screen 3 offers a manual deposit; sessions on notes already in the vault continue | none; notes already deposited are unaffected |
| Funding convenience outage | "{provider} is unavailable." The core path continues: deposits from ETH already held, and every session, are unaffected because no convenience is in the spend path | none |
| Provider account lost | "Recovering your sign-in does not restore your credit notes. Keep your encrypted backup." The embedded funding account may be unrecoverable, depending on the provider's recovery (section 12); notes in the vault still spend, because spending needs the note secret, not the account; what is lost is `ragequit` using the lost account's net-deposit allowance; another address needs its own sufficient allowance and a valid note proof bound to it; any unwithdrawn balance there is lost too | the ragequit exit and any unwithdrawn balance of that account; the notes only if their secrets are in no backup |

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
- Require any login to spend: an optional embedded wallet with social login funds deposits only, on the isolated funding surface, and its identity never reaches a node or relay. On the core path there is no email login, no password and no seed-phrase collection; an optional embedded wallet with email or social sign-in (ADR 0017, proposed) is a funding-surface convenience whose identity is never sent to a node or a relay.
- Send the wallet address, an account, an API key or any persistent identifier to a node or a relay.
- Let a deposit key, on-ramp, router, solver, sponsor or orchestrator pay a node or relay or sit in the spend path: a deposit key never pays a node or relay and signs only `depositNote`.
- Call `depositNote` from any address other than the user's own account; no router, solver, helper contract or on-ramp is ever the depositor.
- Load a wallet or funding SDK in the chat view; provider adapters load only on the isolated funding surface after opt-in.
- Store a note secret, the identity key, a context key, `sessionSigner` or `commitKey` only with a login or wallet provider, or derive any of them from one; the encrypted backup is the only recovery.
- Default to a project RPC, gateway or bundler.
- Trigger a deposit at cap exhaustion or immediately before a spend; a refill fires only on a threshold or schedule, with every value unset.
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
- Call `eth_getEncryptionPublicKey` or `eth_decrypt`, or derive an encryption or vault key from a wallet signature; there is no opt-in for that (ADR 0017, proposed).
- Send a transaction per message.

## 12. Account and sign-in

This section carries ADR 0017 (proposed) into the client. Nothing here changes a contract, a proof, a voucher or a wire format; no provider, validator or library is selected.

**Two tiers.** The core path always works with an account the user already controls, a user-chosen RPC, the permissionless relays and nodes, and a client build reached by a verifying fetch or run locally (section 14). Conveniences — social login (Google/Gmail, Apple, and X where a provider offers it), embedded wallets, on-ramps, intent orchestrators, gas sponsorship, indexers and public gateways — are optional, disclosed and replaceable, live only on the funding surface, and are never in the spend path. A session never has an account: `sessionSigner`, the relay choice, the node choice and the voucher log are created and held by the chat client alone. On the core path there is no email login, no password and no seed-phrase collection; an optional embedded wallet with email or social sign-in (ADR 0017, proposed) is a funding-surface convenience whose identity is never sent to a node or a relay.

**Core-path sign-in.** Two forms, neither hosted:

- an injected wallet over EIP-1193 (`AccountKind = "injected"`), which is what screens 1 and 3 already assume; a plain EOA deposits by hand and needs no deposit key, because "A plain EOA does not support ERC-7579 modules, session keys, multisig, account deployment, or ERC-4337 user operations." (evidence register §1, client UX research 2026-10-15, [V]);
- a self-managed passkey account with an open validator (`"eip7702"` or `"smart-account"`), where the EOA delegated under EIP-7702 keeps its address and assets (evidence register §1, client UX research 2026-10-15, [V]) and stays the root authority that cannot rotate its key (evidence register §1, client UX research 2026-10-15, [V]). Validator candidates, none selected and none required: OpenZeppelin `WebAuthn.sol` and `P256.sol` (MIT) and base/webauthn-sol (MIT), both using the RIP-7212 precompile with a Solidity fallback (evidence register §4 and §8, client UX research 2026-10-15, [V]); Rhinestone's `WebAuthnValidator`, whose source says AGPL-3.0-only while its package.json says GPL-3.0, the Safe passkey module (LGPL-3.0) and ZeroDev's (MIT) are recorded with their licence facts (evidence register §8, client UX research 2026-10-15, [V]). EIP-7951 has been active on Arbitrum One since 2026-01-08 (evidence register §1, client UX research 2026-10-15, [V]); whether RIP-7212 arrived in ArbOS 31 or 32 is unresolved and the precompile reference lists no P256VERIFY address (evidence register §1, client UX research 2026-10-15, [U]). No hosted passkey service is in the core path.

**Optional embedded wallets, none selected.** Recorded from the register; recording a provider does not select it.

- *Rhinestone.* The passkey private key stays on the user's authenticator (evidence register §4, client UX research 2026-10-15, [V]); the managed path adds a Rhinestone co-signature to every transaction (evidence register §4, client UX research 2026-10-15, [V]); in the released verified-identity recovery flow Rhinestone operates the guardian, applies the email or OAuth policy off-chain and signs with AWS KMS, with no enclave enforcing the policy and a TEE signer still under development (evidence register §4, client UX research 2026-10-15, [V]); whoever controls the guardian can authorize a replacement passkey (evidence register §4, client UX research 2026-10-15, [V]); the SDK README names only Google and Apple sign-in and X was not found (evidence register §4, client UX research 2026-10-15, [V] and [U]); passkey-only sign-up without an email or social identity was not found (evidence register §4, client UX research 2026-10-15, [U]); passkeys and accounts are scoped per hostname (evidence register §4, client UX research 2026-10-15, [V]); the wallet SDK defaults to a hosted passkey service (evidence register §4, client UX research 2026-10-15, [V]); no privacy policy was found (evidence register §16, client UX research 2026-10-15, [U]); the SDK's telemetry option bridges events into the integrator's own observability (evidence register §4, client UX research 2026-10-15, [V]) and whether anything reaches Rhinestone is unknown (evidence register §4, client UX research 2026-10-15, [U]); key export was not found (evidence register §4, client UX research 2026-10-15, [U]).
- *Privy.* Keys exist as a 2-of-2 share set reconstituted briefly inside AWS Nitro Enclaves (evidence register §4, client UX research 2026-10-15, [V]); in TEE mode a login unlocks the wallet on a new device (evidence register §4, client UX research 2026-10-15, [V]); Google and Twitter are supported logins (evidence register §4, client UX research 2026-10-15, [V]); passkey sign-up exists (evidence register §4, client UX research 2026-10-15, [V]) and passkey-only sign-up without an email is a researcher reading (evidence register §4, client UX research 2026-10-15, [L]); the SDK "sends anonymous usage analytics in the background" (evidence register §4, client UX research 2026-10-15, [V]) and no off switch was found (evidence register §4, client UX research 2026-10-15, [U]); the user can export the full private key (evidence register §4, client UX research 2026-10-15, [V]); the privacy policy lists email, phone, wallet address, social identity, IP address and device data, disclosed to developers, service providers and analytics providers (evidence register §16, client UX research 2026-10-15, [V]).
- *Turnkey.* Key material is decrypted only inside an enclave and attestation is supported (evidence register §4, client UX research 2026-10-15, [V]); "All OIDC tokens are verified inside of Turnkey's secure enclaves" (evidence register §4, client UX research 2026-10-15, [V]), and that the token's nonce is bound to the client's key is the researcher's wording (evidence register §4, client UX research 2026-10-15, [L]); Google, Twitter and passkeys are supported, with X/Twitter listed as OAuth 2.0-only rather than OIDC (evidence register §4, client UX research 2026-10-15, [V]); the parent organization has read-only visibility into every sub-organization (evidence register §4, client UX research 2026-10-15, [V]); wallet export is encrypted to a transport encryption key, and only the holder of that key's private half can decrypt the bundle (evidence register §4, client UX research 2026-10-15, [V]); the privacy policy lists the wallet address and transaction history (evidence register §16, client UX research 2026-10-15, [V]).

Privy and Turnkey wallets are EOAs that can be upgraded under EIP-7702 (evidence register §4, client UX research 2026-10-15, [V]), which keeps them inside the caller invariant of section 13. A researcher analysis, marked [U] and not upgraded here, holds that each provider can map the login identity to the wallet address and that every deposit from that address is therefore linkable at the provider to the login identity while the zero-knowledge spends carry no such identity (evidence register §4, client UX research 2026-10-15, [U]); the per-provider collection statements above are [V], and the linkage conclusion is cited as nothing stronger. Privy and Turnkey document identity and device-data collection (evidence register §16, client UX research 2026-10-15, [V]); Rhinestone's identity retention and provider telemetry are unknown (evidence register §4, client UX research 2026-10-15, [U]), and its privacy policy was not found (evidence register §16, client UX research 2026-10-15, [U]). That is why every login stays on the funding surface.

**The vault rule (unconditional).** The app-generated identity key of docs/security/privacy-and-contexts.md §5 stays the root of the vault. It, every note secret, every context key, `sessionSigner` and `commitKey` come from the operating-system CSPRNG on the device, and none of them is ever derived from, wrapped by, stored with, or recoverable through a wallet key, an embedded-wallet or passkey provider, a recovery guardian, cloud sync or a login identity. The encrypted backup export (screen 18) is the only recovery of the vault. A provider's wallet export is not the note backup. A provider's recovery may move the funding account and must not reach the vault; losing the login must never be the only way to lose, or the only way to spend, the notes. There is no opt-in that derives a vault key from a wallet signature (section 11).

**The isolation rule.** As stated under the sketch in section 3: the chat client and the funding surface are separate modules in distinct origins with separate storage, the funding capability set denies every vault, note-secret, prover, `sessionSigner`, `commitKey`, context-key and relay command, a provider SDK loads only after the user chooses that convenience and only on funding screens, and the public funding allowlist and the session denylist fix what may and may never cross. The refill job of section 13 runs inside the funding module only. How a static build obtains two origins — two pinned builds, ENS subnames or a native split — is an open question recorded in ADR 0017; a path gateway that collapses origins fails the rule, and the RR-56 gate requires per-platform storage, IPC and network-egress tests.

**Disclosure.** What the provider may observe is stated verbatim on the funding surface: the login identity, the wallet address, IP and device data, the public deposit and grant transactions, and its own analytics, which are disclosed and never assumed disabled. The copy is: "Your deposits are public, and the provider can link them to your identity. Sessions do not include your wallet address or login identity. Timing, small groups, identifying content and collusion can still link activity." The client adds: "This client never sends your login or your address to a node or a relay." Buffering and scheduling (section 13) are mitigations, not guarantees.

## 13. Funding: on-ramp, stablecoin conversion and the deposit key

This section carries ADR 0016 (proposed) into the client. It changes no contract, proof, voucher or wire format; every price, fee and limit quoted is an observation dated 2026-10-15, not a value this document sets; no provider, DEX, router version or validator is selected.

**Why the escrow stays ETH.** `SessionEscrow` holds ETH and nothing else; bands stay in wei. A stablecoin escrow is declined because one issuer action against the escrow address would stop every note and every pending earning at once: a blacklisted USDC address "will be unable to call `transfer` or `transferFrom`, and will be unable to receive tokens", and a separate pauser role halts all transfers, minting and burning of the whole contract (evidence register §15, client UX research 2026-10-15, [V]); the USDT0 token on Arbitrum One has an owner-only block list with `addToBlockedList`, `removeFromBlockedList` and `destroyBlockedFunds`, which burns a blocked holder's balance (evidence register §15, client UX research 2026-10-15, [V]), and a blocked USDT0 address cannot send unless the caller is the owner, but can still receive (evidence register §15, client UX research 2026-10-15, [V per the fact-check]); Circle's USDC terms reserve the right to block transfers to and from an address, and Tether's terms reserve the right to freeze tokens and blacklist addresses (evidence register §16, client UX research 2026-10-15, [V]); the precedent is on chain: Circle blacklisted the OFAC-listed Tornado Cash USDC addresses on 2022-08-08 and un-blacklisted the checked address on 2025-03-22 (evidence register §15, client UX research 2026-10-15, [V]); Circle's Bridged USDC terms say Circle lacks the ability to block or freeze Bridged USDC but also that Circle "may also be required to freeze Bridged USDC" (evidence register §16, client UX research 2026-10-15, [V]), and whether those terms cover Arbitrum's bridged USDC is unverified (evidence register §16, client UX research 2026-10-15, [U]). These are facts as the sources state them, not a legal reading of any issuer's terms. Conversion therefore happens at the edge, in the user's own account, where only the converting user is exposed; a second settlement asset would still be a CIP and none is proposed.

**The caller invariant.** `msg.sender` of every `depositNote` is the user's own address: a plain EOA, that EOA delegated under EIP-7702, or the user's smart account executing the call itself. The reason is the contract, not any provider's terms: `depositNote` credits the public-exit allowance (`depositedWei`) of its caller, and `ragequit` lets an address exit only up to its own allowance and only with a valid note proof bound to that address; it does not bind a note to its original depositor (docs/protocol/contracts-and-settlement.md :280 and :283). A deposit made by anything other than the user's own account would credit that address's allowance instead, and the user could not ragequit that value. No on-ramp, router, solver, bundler, sponsor, orchestrator or helper contract ever calls it, and an on-ramp never delivers to the escrow. That a call routed through a smart account by an intent executor yields the account as `msg.sender` is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]) that needs call traces before any integration is attempted.

**On-ramp flow (optional).** The user buys ETH on Arbitrum One delivered to an address the user controls, then deposits from screen 3 or by a deposit-key refill. Candidates recorded, none selected:

- *Coinbase Onramp.* Its Layer 2 table lists ETH on Arbitrum (evidence register §15, client UX research 2026-10-15, [V]); the integrator passes the destination address (evidence register §15, client UX research 2026-10-15, [V]); fees are a spread, a variable fee shown at preview, a network fee, and "a 2.5% fee for credit card transactions, and 0.5% fee for ACH" (evidence register §15, client UX research 2026-10-15, [V]); Headless Onramp is US-only and collects phone, email, one-time passwords and identity information for limit upgrades (evidence register §16, client UX research 2026-10-15, [V]); Guest Checkout was US-only with a $500-a-week limit and was due to be deprecated on 2026-06-30 (evidence register §16, client UX research 2026-10-15, [V]).
- *MoonPay.* Its currencies API lists ETH on Arbitrum with no country blocks and blocked in New York and the US Virgin Islands (evidence register §15, client UX research 2026-10-15, [V]); the fee is "up to 4.5%", with a minimum "up to $3.99" for direct use (evidence register §15, client UX research 2026-10-15, [V]) and a partner-referral minimum up to $4.50 (evidence register §15, client UX research 2026-10-15, [V per the fact-check]), plus a network fee and a spread (evidence register §15, client UX research 2026-10-15, [V]); KYC is tiered, with the lowest US tier asking only basic information and New York requiring full KYC from the first transaction (evidence register §16, client UX research 2026-10-15, [V]); MoonPay says it provides no custodial wallet (evidence register §15, client UX research 2026-10-15, [V]).
- *Transak.* Its currencies API lists ETH on Arbitrum as allowed (evidence register §15, client UX research 2026-10-15, [V]; not independently re-fetched); published fees are card 3.99% + $1, Apple Pay 3.99% + $1, Google Pay 3.99%, wire 0.75% + $9 and bank transfer 2% + $1, plus a spread of 0% to 2.5%, with gas and third-party fees extra (evidence register §15, client UX research 2026-10-15, [V]); Light KYC asks for name, phone, date of birth, address, country and, in the US, SSN, with no photo ID (evidence register §16, client UX research 2026-10-15, [V]); the destination address can be pre-filled and locked (evidence register §15, client UX research 2026-10-15, [V]).
- *Stripe.* Its main supported-assets table and its Embedded Components page make conflicting statements about Arbitrum availability (evidence register §15, client UX research 2026-10-15, [V] for those statements). Resolved Arbitrum support, ETH-on-Arbitrum availability and a published fee rate were not found (evidence register §15, client UX research 2026-10-15, [U]). Stripe handles KYC and sanctions screening and access requires an approved application (evidence register §16, client UX research 2026-10-15, [V]).
- *Rhinestone's on-ramp widget* embeds Swapped's checkout and routes funds through a "service-managed deposit account" whose custody is unknown (evidence register §15, client UX research 2026-10-15, [V] for the description, [U] for custody).

Each researched provider documents a KYC or identity step (evidence register §16, client UX research 2026-10-15, [V] per provider); that every on-ramp ties the receiving address to an identity is a researcher inference (evidence register §15, client UX research 2026-10-15, [L]). The Coinbase Guest Checkout, MoonPay and Transak terms each state that the buyer owns or controls the destination wallet (evidence register §16, client UX research 2026-10-15, [V]; the Coinbase Guest Checkout terms were not independently re-fetched); these are recorded as provider statements, whether they apply to any particular delivery is an open review item, and the client rejects escrow delivery on the caller invariant above, not on those terms. Screen 20 discloses KYC, the fee, the delivered ETH, the quote expiry and who pays gas; the provider fee is a separate line and never changes what a note is worth inside a session.

**Swap flow (optional).** A stablecoin the user already holds is converted to native ETH inside the user's own account by an exact-output swap, so the account ends with exactly one denomination's worth of ETH plus gas, and the user then deposits. SwapRouter02 has `exactOutputSingle` and `exactOutput` and can unwrap WETH to ETH in the same multicall, and the Universal Router has exact-output and unwrap commands (evidence register §15, client UX research 2026-10-15, [V]); Uniswap names the Universal Router as the preferred entrypoint, and which version to use is open (evidence register §15, client UX research 2026-10-15, [V] and [U]); the v4 router reverts when the input needed exceeds `amountInMaximum` (evidence register §15, client UX research 2026-10-15, [V]); Uniswap v4 treats `address(0)` as native currency (evidence register §15, client UX research 2026-10-15, [V]), and whether a native pool on Arbitrum has enough liquidity is unknown (evidence register §15, client UX research 2026-10-15, [U]). An intent whose output recipient is the user's own account is the other route: ordinary swap intents support exact output (evidence register §15, client UX research 2026-10-15, [V]); a multi-chain intent is not atomic, since "funds can arrive before a later destination action fails" (evidence register §4, client UX research 2026-10-15, [V]). A swap-session scope alone cannot call `depositNote`: its only operations are approving the sell token and calling the venue's swap entrypoint and "Every other operation reverts on-chain." (evidence register §15, client UX research 2026-10-15, [V]); that this excludes `depositNote` is a researcher inference (evidence register §15, client UX research 2026-10-15, [L]). One session that swaps a stablecoin to native ETH and then calls `depositNote` with an exact nonzero `msg.value` is not documented (evidence register §15, client UX research 2026-10-15, [U]); until it is shown, conversion and deposit are two separately authorized calls from the user's account (open question 13). Uniswap's licence facts (v3-core BUSL 1.1, periphery and SwapRouter02 GPL-2.0-or-later, universal-router GPL-3.0-or-later, v4-core BUSL 1.1 and v4-periphery MIT; evidence register §8, client UX research 2026-10-15, [V]) are RR-58 items; whether any of it matters when the client only calls deployed contracts is unresolved (evidence register §8, client UX research 2026-10-15, [U]) and no legal conclusion is drawn.

**The deposit key.** SDK name `depositKey`, user-facing "deposit key"; it is never called a session key, `sessionSigner` or `commitKey`. It exists only on an EIP-7702 EOA or a smart account (the EOA quote above); the core path does not need it.

- *Grant shape* (`DepositKeyGrant`, section 3). The on-chain permission names exactly one contract, `SessionEscrow` on the chain in use, and exactly one selector, `depositNote`. Each permission is bound to one contract address and its listed selectors, so listing one function does not authorize another (evidence register §4, client UX research 2026-10-15, [V]). `valueLimitPerUse` is set to the granted denomination; it is a per-call ceiling (evidence register §4, client UX research 2026-10-15, [V]), and whether the permission can require exact equality is not documented (evidence register §4, client UX research 2026-10-15, [U]), so the contract's own `msg.value ==` check is the equality rule. `maxUses` counts per function and per chain, and `validAfter` and `validUntil` bound the window (evidence register §4, client UX research 2026-10-15, [V]); a chain that refuses the timeframe policy fails closed and the grant is not made there. The documented spending-limit policy covers ERC-20 tokens and does not mention native ETH (evidence register §4, client UX research 2026-10-15, [V]), so no cumulative ETH limit is claimed. The grant names no node, relay, NodeRegistry, ModelRegistry, ContextRegistry, router, venue, token approval or module install. The deposit key never signs a voucher, envelope, `closeSession`, `claimChange`, `ragequit`, `withdraw` or context grant; it never pays a node or relay and is never in the spend path. The note secret is generated locally and stored in the vault before any commitment is submitted, whether the account or the deposit key submits it (section 3).
- *Timing rules.* A refill fires on an unspent-note threshold or on a schedule with random jitter, into a buffer of notes that honour `spendableAfter`. It never fires at cap exhaustion, on a send or resume event, or immediately before a spend; cap exhaustion continues only on an already-buffered eligible note, otherwise the client pauses and says why (section 6). Threshold, schedule, jitter, buffer size and both delays stay unset; buffering and scheduling are mitigations against the timing linkage of R8, not guarantees. The RR-52 gate reads: "This PR sets no timing values. Automatic refills remain unavailable until a reviewed timing policy is adopted and its eligibility and trigger rules are demonstrated." A fee-policy review is also required before the convenience is enabled.
- *Public visibility.* The Smart Sessions v1 interface emits `SessionCreated` and `PolicyEnabled` events naming the account (evidence register §4, client UX research 2026-10-15, [V]); that grants are therefore public is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]); which validator version is deployed is unknown (evidence register §4, client UX research 2026-10-15, [U]). Screen 21 says so before the grant, with the funding-surface copy of section 12.
- *Revocation.* On-chain and chain by chain; "Deleting a local key does not revoke its onchain authority" (evidence register §4, client UX research 2026-10-15, [V]). Deleting the local key is not revocation and the client never describes it as such; `revokedOnChain` is set only from the chain.
- *Exposure.* If enforcement is correct, a stolen deposit key can move at most cap × uses of principal per grant and per chain, and only into `depositNote`. Gas and fees are separate and not bounded here. A validator or account defect is not bounded. A stolen key can create notes whose secrets the attacker holds, and the user cannot recover them. Whether calldata rules can bind the grant to a prepared commitment set is a review item (UNVERIFIED; no source examined states it).
- *Validator licences.* Smart Sessions v1 is AGPL-3.0 and v2 is BUSL-1.1 as their sources state (evidence register §8, client UX research 2026-10-15, [V]); which version is deployed is unknown (evidence register §4, client UX research 2026-10-15, [U]). These are RR-58 facts, not conclusions.

**Gas sponsorship and orchestrators (optional).** A sponsor pays the L2 fee of a transaction that still comes from the user's account under the caller invariant; the sponsored fee is shown as sponsored on the funding surface, never folded into the cap or the L2 fee line (section 6). Sponsorship prices such as "Sponsored amount plus 10%" (evidence register §15, client UX research 2026-10-15, [V]) are observations, not adopted values. No sponsor, orchestrator or on-ramp sees a session, a voucher, a relay choice or a note secret.

## 14. Distribution and platforms

This section carries ADR 0017 (5)–(6) and ADR 0018 (both proposed) into the client. No shell, prover, store or version is selected; licence and store facts are facts and review items, not legal conclusions. Local client execution is not local model inference: inference still runs only on network nodes, and the client performs no model computation (section 2).

**Core path.** The client is a reproducible build pinned by its content hash, published through an ENS `contenthash`, and reached in one of three ways: a verifying fetch, where a client that asks a gateway for verifiable response types can check the bytes itself and "CAR verification does not require running IPFS node" (evidence register §4, client UX research 2026-10-15, [V]), with `@helia/verified-fetch`, which fetches from trustless gateways and verifies the data (evidence register §4, client UX research 2026-10-15, [V]; its licence is UNVERIFIED here), and the Service Worker Gateway, whose README states Apache-2.0 OR MIT (evidence register §8, client UX research 2026-10-15, [V]), as recorded candidates; a locally run gateway, which eth.limo documents with a replaceable Ethereum RPC and end-to-end verification (evidence register §4, client UX research 2026-10-15, [V]); or a local run from the pinned build or a direct CID. ENSIP-7 protocol code 0xe3 denotes IPFS content; only the name's Manager can set the content hash, in one Ethereum mainnet transaction that needs ETH there (evidence register §4, client UX research 2026-10-15, [V]). Public gateways are best-effort and "not intended to be part of your critical path" (evidence register §4, client UX research 2026-10-15, [V]); Brave deprecated its built-in IPFS node in August 2024 (evidence register §4, client UX research 2026-10-15, [V]) and whether it still loads ENS-linked sites without a gateway is unresolved (evidence register §4, client UX research 2026-10-15, [U]). IPFS traffic is observable, since third parties can see which CIDs are requested (evidence register §4, client UX research 2026-10-15, [V]), and that an HTTP gateway sees the client's IP and CID is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]). ENS resolution may need a user-chosen Ethereum RPC; direct CID and local access always remain. Screen 22 shows the running build's hash so the user can compare it with the published one.

**The RPC rule.** There is no default endpoint; the user chooses (screen 2 and screen 22). A full Arbitrum node needs 64 GB RAM, 8 cores and NVMe storage of "ideally several terabytes", a parent-chain RPC, and about a 2.3 TB pruned snapshot (evidence register §1, client UX research 2026-10-15, [V]), which is infeasible for most users; the official public RPC comes with "No uptime, latency, or rate-limit guarantees." (evidence register §1, client UX research 2026-10-15, [V]); no browser light client for Arbitrum One was found (evidence register §1, client UX research 2026-10-15, [U]). Chain reads therefore trust the chosen RPC, and the client says so in those words. Session-specific reads stay relay-tunnelled (section 2). A bundler is not required: the user's EOA, EIP-7702 EOA or smart account submits `depositNote` itself; the record on a shared ERC-4337 mempool on Arbitrum conflicts between sources (evidence register §1, client UX research 2026-10-15, [V] for each statement, [U] for the resolution), and the EntryPoint code identity on Arbitrum One is unverified (evidence register §1, client UX research 2026-10-15, [U]).

**One stack.** The client is a TypeScript UI over a Rust core that reuses the node's `hpke`, `ohttp` and `bhttp` crates (ADR 0003); the web build compiles the core to WASM, and desktop and mobile wrap the same UI and core in a native shell. Portable logic is separated from the wallet, secure-storage, passkey and lifecycle adapters, so a shell change touches adapters only, and remote provider content gets no vault or prover capability. The shell, a provider webview and a store listing are never in the spend path.

- *Native-shell candidate, not selected: Tauri 2.* Its README lists iOS and Android beside Windows, macOS and Linux (evidence register §4, client UX research 2026-10-15, [V]); it uses WebView2 on Windows, WKWebView on macOS and, in its webview layer, on iOS, and the device's system WebView on Android, shipping none of its own (evidence register §4, client UX research 2026-10-15, [V]); webview code reaches the system only through the IPC layer, capabilities grant permissions per window or webview with a `platforms` array, and on Linux and Android Tauri cannot distinguish an embedded iframe from the window itself (evidence register §4, client UX research 2026-10-15, [V]), which is why the isolation rule uses separate webviews, not iframes; Rust is called through typed commands (evidence register §4, client UX research 2026-10-15, [V]), and that this is how the HPKE and OHTTP crates would be reused is a researcher inference (evidence register §4, client UX research 2026-10-15, [L]). The code is MIT, or MIT/Apache-2.0 where the README says so, and wry is Apache-2.0/MIT (evidence register §8, client UX research 2026-10-15, [V]). If Tauri is chosen, 2.11.1 is the observed patched floor: its release notes fix the local-origin check on Windows and Android, and GHSA-7gmj-67g7-phm9 lists 2.11.1 as patched, while the CVE-2026-42184 record contradicts itself on the fixed version (evidence register §4, client UX research 2026-10-15, [V]); that floor is an observation dated 2026-10-15, not a pin. The October 2024 statement that "We are not completely happy about the developer experience at the moment" on mobile has no later official statement (evidence register §4, client UX research 2026-10-15, [V] for the statement, [U] for the absence), and no Tauri web target was found (evidence register §4, client UX research 2026-10-15, [U]). Plugin and core code "has full system access and is not constrained" (evidence register §4, client UX research 2026-10-15, [V]), so the shell is trusted code under the same review as the core.
- *Recorded alternative: React Native or Expo with UniFFI.* React Native and Expo are MIT and UniFFI and uniffi-bindgen-react-native are MPL-2.0 (evidence register §8, client UX research 2026-10-15, [V]); uniffi-bindgen-react-native's own documentation says it "should not yet be used in production" (evidence register §4, client UX research 2026-10-15, [V]), and no Expo-specific UniFFI guide was found (evidence register §4, client UX research 2026-10-15, [U]).

**The passkey-in-app gap.** Native passkeys stay gated by per-platform demonstration; the core path uses an external wallet as the fallback on every platform. Apple requires an associated domain with the `webcredentials` service type and documents passkeys in WKWebView for a relying party that is an associated domain of the app (evidence register §4, client UX research 2026-10-15, [V]); Tauri documentation on adding that entitlement was not found (evidence register §4, client UX research 2026-10-15, [U]). Android WebView supports passkeys through Credential Manager only when the app opts in with `setWebAuthenticationSupport()` and sets up Digital Asset Links, the sample adds `credentials-play-services-auth`, and conditional mediation is unsupported (evidence register §4, client UX research 2026-10-15, [V]). Tauri's biometric plugin prompts for biometrics and is not WebAuthn, a maintainer calls the authenticator plugin "basically broken", issue 7926 is open with a later Android 16 success report whose accuracy is unresolved (evidence register §4, client UX research 2026-10-15, [V] for what the pages say, [L] for the reports), and the community plugin marks macOS and iOS unsupported (evidence register §4, client UX research 2026-10-15, [V]). Whether a frontend served from a bundled custom scheme can run WebAuthn for an associated-domain relying party was not found (evidence register §4, client UX research 2026-10-15, [U]); this is open question 11.

**Prover candidates, none selected.** The current path is `@semaphore-protocol/proof` on snarkjs, whose npm license field is GPL-3.0 (evidence register §8, recheck 2026-10-15, [V]). Native candidates: `semaphore-protocol/semaphore-rs`, MIT, which depends on mopro's `circom-prover` (evidence register §8 and §15, client UX research 2026-10-15, [V]); `circom-prover` is "MIT OR Apache-2.0" with `arkworks` and `rustwitness` as default features (evidence register §8 and §15, client UX research 2026-10-15, [V]), and that Semaphore v4 is therefore provable through arkworks is a researcher inference (evidence register §15, client UX research 2026-10-15, [L]); ark-groth16 is Apache-2.0 or MIT and its README says "NOT ready for production use" (evidence register §8, client UX research 2026-10-15, [V]), a warning that attaches to ark-groth16 only; `worldcoin/semaphore-rs`, MIT (evidence register §8, client UX research 2026-10-15, [V]), names no Semaphore version, so v4 compatibility is unknown (evidence register §15, client UX research 2026-10-15, [U]); rapidsnark, whose COPYING is LGPL-3.0 (evidence register §8, client UX research 2026-10-15, [V]), where linking consequences are a researcher inference (evidence register §8, client UX research 2026-10-15, [L]); mopro, "Apache-2.0 or MIT" (evidence register §8, client UX research 2026-10-15, [V]), while licences for zkmopro/rust-rapidsnark, SemaphoreReactNative and semaphore-bindings were not shown (evidence register §8, client UX research 2026-10-15, [U]) and audits of semaphore-rs, circom-prover and mopro were not found (evidence register §8, client UX research 2026-10-15, [U]). Before any choice, a candidate must show an identical accepted circuit, identical artifacts, identical public-input and proof encoding, browser and native interoperability on the same proof, local-only proving, and measured memory and latency. A permissive native candidate does not close RR-50, which covers the whole path; the licence facts are RR-50 and RR-58 items; changing circuits or verifier semantics would need a CIP; SHA-256 artifact pinning stays exactly as section 3 and CIP-0005 state.

**App stores: facts and open questions, no legal conclusion.** Recorded from the register as facts, not as advice and not as a classification of Comuns: Apple 3.1.5 allows wallets only from developers enrolled as an organization, bans on-device mining and allows cryptocurrency transactions only on an approved exchange where licensed (evidence register §16, client UX research 2026-10-15, [V]); Apple 3.1.1 bans unlocking content or functionality with cryptocurrencies and cryptocurrency wallets (evidence register §16, client UX research 2026-10-15, [V]), and whether that reaches paying for inference with notes inside an iOS app is an open reading (evidence register §16, client UX research 2026-10-15, [U]); Apple 2.5.2 bans downloading code that introduces or changes features (evidence register §16, client UX research 2026-10-15, [V]), and whether that covers downloaded zkey or witness artifacts is an open reading (evidence register §16, client UX research 2026-10-15, [U]); Apple 5.1.1(ix) requires a legal entity for regulated services including crypto exchanges (evidence register §16, client UX research 2026-10-15, [V]); in the EU, notarization is a baseline review on every channel, with eligibility bars and a commission on paid digital sales (evidence register §16, client UX research 2026-10-15, [V]), and whether 3.1.5 applies to notarized apps rests on a missing marker and is a researcher inference (evidence register §16, client UX research 2026-10-15, [L]); Google Play's payments policy says in-app digital transactions "must use Google Play's billing system for those transactions unless Section 3, 8, or 9 applies." (evidence register §16, client UX research 2026-10-15, [V]), and a crypto exception was not found (evidence register §16, client UX research 2026-10-15, [U]), non-custodial wallets are out of scope of its exchange-and-wallet policy (evidence register §16, client UX research 2026-10-15, [V]), and whether the organization-account rule covers a non-custodial wallet is an open reading (evidence register §16, client UX research 2026-10-15, [U]); F-Droid rebuilds FLOSS apps from source and rejects apps that need Play Services (evidence register §16, client UX research 2026-10-15, [V]), and that the Android WebView passkey sample's Play Services dependency conflicts with that is a researcher inference (evidence register §16, client UX research 2026-10-15, [L]). Store distribution is a convenience: the verified web client and the local run survive a rejected or removed listing (RR-59), and a store listing is never in the spend path.

## 15. Risks

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

The deposit is public and names the wallet. A spend soon after a deposit into a small group, or a change note spent soon after its session settles, is linkable by timing (evidence register §15 [V]). Mitigation: the client shows the group size, warns below the threshold and recommends a delay before spending; both delays and the threshold are unset, and no authoritative minimum anonymity set exists (evidence register §15 [U]). An automatic refill by a deposit key is not an exception to the unset delays: a refilled note waits for `spendableAfter` like any other, and a refill never fires at cap exhaustion or just before a spend (section 13).

### R9 — The prompt identifies its author **[RISK] · High**

In standard mode the node reads the prompt, and names, addresses and writing style can deanonymize the author whatever the transport hides: attribute inference from text reaches up to 85% top-1 accuracy and pseudonymous-profile linking up to 68% recall at 90% precision (evidence register §16, [L]/[V]). Mitigation: the banner says so; the client cannot prevent it.

### R10 — Funding-side identity linkage through social login, KYC and refills **[RISK] · High**

An embedded wallet's provider can map a login identity to the funding address, an on-ramp documents a KYC or identity step, and a deposit key adds public grants and refills, so every deposit from that address can be linked by those parties to a person (the per-provider collection statements are evidence register §4 and §16, client UX research 2026-10-15, [V]; the linkage analysis is [U] and not upgraded here). Sessions carry no address or login, but timing, small groups, identifying content and collusion can still link activity. Mitigation: the conveniences are optional and live only on the isolated funding surface (ADR 0016 and ADR 0017, proposed; section 12); the verbatim disclosure copy replaces every absolute assurance; refills are buffered and scheduled, never fired at a spend (section 13); RR-53 and RR-52 carry the gates, and RR-39 is amended, not closed.

### R11 — Wrong `depositNote` caller or deposit-key misuse **[RISK] · High**

A deposit sent by a router, solver, on-ramp, sponsor or helper contract would credit that address's public-exit allowance (`depositedWei`) instead of the user's, and the user could not ragequit that value; a deposit key granted too widely, a validator defect, or a stolen key widens what the key can do. If enforcement is correct, a stolen deposit key can move at most cap × uses of principal per grant and per chain, and only into `depositNote`. Gas and fees are separate and not bounded here. A validator or account defect is not bounded. A stolen key can create notes whose secrets the attacker holds, and the user cannot recover them (section 13). Mitigation: the caller invariant is a client refusal (section 11) and a test item (RR-51); the grant names one contract, one selector, a per-call cap equal to the denomination, uses and a window, and the contract's exact `msg.value` check is the equality rule (ADR 0016, proposed); revocation is on-chain; the exposure statement is shown on screen 21; whether calldata rules can bind a grant to a prepared commitment set is a review item (RR-52).

### R12 — A wallet or funding SDK observes session data **[RISK] · High**

A provider SDK loaded in the chat origin could read note secrets, session ids, `sessionSigner`, vouchers, relay and node choice, prompts or answers, and the Privy SDK sends analytics by default with no documented off switch (evidence register §4, client UX research 2026-10-15, [V] and [U]). Mitigation: the isolation rule (ADR 0017, proposed; section 12): distinct origins with separate storage, a funding capability set that denies every vault, prover, key and relay command, adapters loaded only on funding screens after opt-in, and the allowlist and denylist of section 3; the RR-56 gate requires per-platform storage, IPC and network-egress tests; RR-57 covers the vault reached through provider recovery, which the unconditional vault rule forbids.

### R13 — A hosted convenience or a store listing is treated as required **[RISK] · Medium**

If a login, on-ramp, orchestrator, sponsor, bundler, indexer, gateway or RPC became a required party, or a store listing became the only way to get the client, the project would be a required service and a removal, outage or policy change would stop users (the store facts are evidence register §16, client UX research 2026-10-15, [V]; the readings that matter are [U] or [L], and no legal conclusion is drawn). Mitigation: the core path of section 2 (local run or verified pinned build, user-chosen RPC, own account, permissionless relays and nodes) is the tested baseline and every convenience can be absent (ADR 0017 and ADR 0018, proposed; section 14); no default RPC, gateway or bundler (section 11); RR-55, RR-59 and RR-60 carry surface-scoped gates so a store, vendoring or convenience gate never blocks the core path or protocol code; RR-58 holds the dependency-licence facts.

## 16. Open questions

1. **Wallet library and contract wallets.** Contract wallets are supported because `msg.sender` of `depositNote` and `ragequit` is the account itself, including a batched user operation from that account (ADR 0017, proposed; section 13). Which EIP-1193 wrapper to use, and whether a bundler is offered as a convenience, stay open: the shared-mempool record conflicts and the EntryPoint code identity on Arbitrum One is unverified (section 14).
2. **`sessionSigner` delegation.** Letting a smart account authorize `sessionSigner` as a session key stays future work with no CIP proposed; it would put an account key in the spend path and link a session to that account. The deposit key of ADR 0016 (proposed) is not an authorization of `sessionSigner`: it funds and never spends.
3. **Backup format.** The password-based KDF, versioning and update cadence of the encrypted export of the identity key, key-wrap records, context keys, note secrets and head checkpoints; whether an optional ciphertext bundle is offered (docs/security/privacy-and-contexts.md §14).
4. **Package name and distribution.** Distribution is answered by ADR 0017 (5) and ADR 0018 (both proposed; section 14): the Rust core ships as WASM for the web and as a native library for the shells, and the client is a content-hash-pinned build reached by a verifying fetch, a local gateway or a local run, with no project-run server. ADR 0013 proposes one code repository with the client in a `client/` directory; the package name stays open. The prover choice is also a license question: @semaphore-protocol/proof 4.14.3 depends on snarkjs 0.7.5, whose npm license field is GPL-3.0, and core pulls proof in (evidence register §8, recheck 2026-10-15, [V]); native prover candidates are recorded in evidence register §8, client UX research 2026-10-15, none is selected; RR-50 is the review item and draws no legal conclusion.
5. **Batching spends.** Whether the N spends of a plan should be submitted together, staggered or through distinct relays, given that sessions opened in one window are correlatable (docs/security/privacy-and-contexts.md §9).
6. **Reputation source.** Which community indexers the client lists by default, if any, how a user adds their own, and how reputation queries avoid revealing which node the user is about to pick.
7. **Note-store backup.** How often the client refreshes the backup as deposits and change create new note secrets, whether a note created after the last backup should block further spending until the backup is refreshed, and how a restored device reconciles notes already spent elsewhere (by nullifier, read through a relay).
8. **`SessionMap` with a second session per pair.** Section 3 keys `SessionMap` to one `sessionId` per `(node, modelId)`, while docs/protocol/orchestration.md §6 allows a second, separately disclosed session for the same pair when two tasks of a wave must run in parallel. `SessionMap` should map a pair to a list of `sessionId`s (or to the sheet's session index), with the dispatcher choosing among them; the shape is open for the SDK.
9. **Relay-selection UX.** Whether the user should see and redraw the random relay at all or only on request, whether to prefer distinct relays per session of one plan, how to present the eligible relay set when it is small, and whether a user-chosen relay (for example one placed behind Tor) is offered and how it is disclosed on the sheet.
10. **Refill policy.** The unspent-note threshold, the schedule and the jitter of a deposit-key refill, and how they interact with the unset deposit-to-spend and change delays: a refilled note must wait for `spendableAfter`, and the buffer must be large enough that a refill is never the last event before a spend. No value is set; the RR-52 gate (section 13) keeps automatic refills unavailable until a reviewed timing policy exists.
11. **Passkeys inside the native shell.** Whether a passkey can be created and used from inside a Tauri webview on iOS and macOS (the entitlement documentation was not found) and from a custom-scheme origin for an associated-domain relying party (not found); until shown per platform, the external wallet is the fallback (section 14).
12. **Which on-ramps, and a KYC-light tier.** Which on-ramp candidates, if any, the funding surface offers, and whether a KYC-light tier such as MoonPay's basic-information tier or Transak's Light KYC (evidence register §16, client UX research 2026-10-15, [V]) is exposed; whether the buyer-controls-wallet statements of the providers' terms apply to any delivery is an open review item, not a legal conclusion.
13. **One session or intent for swap plus deposit.** Whether one session or intent can swap a stablecoin to native ETH and then call `depositNote` with an exact nonzero `msg.value` from the user's own account; this is not documented (evidence register §15, client UX research 2026-10-15, [U]), so conversion and deposit are two separately authorized calls until it is shown (section 13).
