# ADR 0004: Settle with session escrow and chunked vouchers, with no slashing in v1

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

Hosted prices for a small model start near $0.02 per million input tokens and $0.04 per million output tokens (evidence register §6, [V]). The Arbitrum One fee snapshot dated 2026-10-13 records gas at 0.02 gwei and an ERC-20 transfer near $0.003 (evidence register §1, [V]). An ETH transfer is derived near $0.001 (evidence register §1, [U]). A short prompt's inference is worth far less than two contract calls. Paying one on-chain job per prompt would spend more on L2 fees than on inference for small models, and it would ask the wallet to sign every message.

The same evidence blocks a penalty on output mismatch. One thousand temperature-0 runs of one model produced 80 unique outputs. Batch-invariant kernels made a smaller model identical at about 1.6× runtime (evidence register §5, [V]). An honest node can disagree with another honest node. A slash on that disagreement would punish honesty.

PoSP/spML says honest play is the unique equilibrium when p > C/((1−r)(R+S)), and it assumes deterministic execution (evidence register §5, [V]). v1 has no demonstrated profile to plug into that inequality, and it assigns no values to the symbols.

Nothing runs yet. No code and no audit exist.

## Decision

The reference client funds a session through [ADR 0011](0011-anonymous-credits.md) and [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md): a note is spent by `openSessionFromCredit`, submitted by the node or a broadcaster, and the session records `user = address(0)`. Wallet `openSession` remains specified for a direct caller and is not the reference client's path. This record does not offer that wallet path as a privacy mode. On the wallet path a user pays one node for one model by depositing ETH in `SessionEscrow`, and the wallet signs `openSession`, and `topUp`, `closeSession` or `withdraw()` when those are used. Inference runs off-chain ([ADR 0002](0002-off-chain-rust-inference.md)). The client signs cumulative EIP-712 vouchers with an app-generated `sessionSigner` on either path. The wallet is not prompted per chunk. On the credit path the wallet signs nothing for the session.

`openSession` takes `expectedPriceInPerMillion` and `expectedPriceOutPerMillion` and reverts if the node's current offer differs, so an offer change cannot lock a deposit. `openSessionFromCredit` applies the same price binding. After inclusion the client reads the prices copied into the session. If they differ from the confirmed disclosure sheet, the client signs nothing and closes. On a credit session that close is submitted through a relay or broadcaster, never from the deposit wallet. Prices a node reports in a welcome message are informational and never trigger that close.

The effective cap is `min(depositWei, maxSpendWei)`. `topUp(newMaxSpendWei)` is payable and may raise `maxSpendWei` together with the deposit. It never lowers the cap. `topUp` reverts on a credit session. When a credit session's cap is exhausted the client opens a new credit session with a new note ([ADR 0011](0011-anonymous-credits.md)). The client never signs a voucher above the effective cap. The path that re-signs the same cumulative totals under a new `seq` applies only when a voucher above the old cap was signed and only partly paid. A voucher above the cap is paid only up to the cap.

**The one canonical voucher type**, defined only in the contracts document, with no spaces after the commas:

`Voucher(bytes32 sessionId,uint64 seq,uint256 cumulativeWei,uint64 inputTokens,uint64 outputTokens,bytes32 outputCommitment,bool final)`

`inputTokens` and `outputTokens` are cumulative for the session. `cumulativeWei = (priceInPerMillion * inputTokens + priceOutPerMillion * outputTokens) / 1000000`, recomputed on-chain from the session's copied prices. `seq` starts at 1 and strictly increases. The contract also requires `inputTokens`, `outputTokens` and `cumulativeWei` to be at least the last accepted voucher, so a later voucher cannot lower what is owed. `outputCommitment = keccak256(commitKey ‖ sessionId ‖ seq ‖ transcriptHash)` uses that voucher's `seq`. `commitKey` is a random 32-byte key the client seals in the first job envelope ([ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)). The field is not checked on-chain. Opening it discloses the session's output.

`final` means only that the client closes the session. The per-job last frame uses a different flag, `endOfJob`, which is never copied into `final`.

**CHUNK_TOKENS** is the maximum output tokens in one voucher step. Its value is unset. The node streams at most one chunk of `CHUNK_TOKENS` ahead of the highest voucher it holds. That chunk is the node's unpaid exposure.

**Signing cadence.** The node tokenizes the prompt and granted context with the manifest's pinned tokenizer and, before prefill, sends a node-signed input receipt `(sessionId, jobId, jobInputTokens, cumulativeInputTokensAfter)`. The client checks `jobInputTokens` against its own tokenization and checks `cumulativeInputTokensAfter = lastInputTokens + jobInputTokens`. It signs the input voucher only if both match. The node starts prefill when it holds that voucher. Each output chunk then arrives with a node-signed receipt of the cumulative counts and the chunk hash, inside the sealed frame. The client signs the next voucher for the prefix it acknowledged. Receipts count model tokens only. Unsigned receipts bind nobody. A job whose input voucher was never signed never enters the cumulative counts.

**Redemption.** `redeemVoucher` rejects any voucher with `final == true`. A closing voucher goes only through `closeWithVoucher`. On a wallet-funded session, `closeWithVoucher` credits the node and credits the refund `depositWei − settledWei` to `balances[user]` in the same call. `redeemVoucher` credits the node and credits no refund. `finalize` on a wallet-funded session credits only that refund and credits nothing to the node. For every settled wallet-funded session, node credits plus the user refund equal `depositWei`. The shared escrow balance, across both funding paths, satisfies `address(this).balance == Σ balances + Σ open/closing (depositWei − settledWei) + Σ pendingWei + Σ unspent note face value`.

A credit session does not refund `balances[user]`. On a credit session each incremental payout, from `redeemVoucher` or `closeWithVoucher`, splits as `relayDelta = min(relayFeeWei, newSettled) − min(relayFeeWei, oldSettled)` to `balances[relay]` and `nodeDelta = payout − relayDelta` to `balances[node]`. `closeWithVoucher` and `finalize` record `pendingWei = depositWei − settledWei`, which is the full denomination when `settledWei == 0`. The cumulative voucher, the no-slashing rule, pull payments and protocol fee 0 stay. The credit-session invariant and the pool-wide balance equation are the ones in [ADR 0011](0011-anonymous-credits.md).

No contract pushes ETH. Credits go to `balances[address]`. The only ETH-sending function is `withdraw()`, which pays `msg.sender` its whole balance after zeroing it. Every state-changing function uses checks-effects-interactions and a reentrancy guard. The closed list has 23 names via [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md), as [ADR 0011](0011-anonymous-credits.md) defines.

**State.** Legality follows `status`, never `closeDeadline == 0`. `redeemVoucher` and `closeWithVoucher` are allowed when `status` is open, or when `status` is closing and `block.timestamp < closeDeadline`. No voucher is redeemable after `closeDeadline`. `finalize` requires closing and `block.timestamp ≥ closeDeadline`. A settled wallet-funded session accepts no call. A settled credit session accepts `claimChange` while `pendingWei > 0`, and no other call. `closeDeadline` is set only by `closeSession`. On a wallet-funded session either the user or the node may call `closeSession` while the session is open. On a credit session the node may call `closeSession`, or any broadcaster presenting a `sessionSigner` EIP-712 signature over `(chainId, escrow, sessionId, "close")`. The reference client submits that credit close through a relay or broadcaster, never from the deposit wallet. Nothing closes a session automatically.

**Two closes.** Cooperative close: the client signs a final voucher and the node calls `closeWithVoucher`. Unilateral close on a wallet-funded session: the client calls `closeSession` with no voucher, and anyone calls `finalize` after `closeDeadline`. Unilateral close on a credit session uses the broadcaster signature above, and `finalize` stays anyone. A client that has lost its voucher log signs nothing more and uses only the unilateral close.

**Abandoned client.** A node never relies on `closeWithVoucher` without a final voucher. When the client disappears, or a key is lost, the node redeems its highest non-final voucher with `redeemVoucher` while that is legal, then calls `closeSession`. `finalize` after `closeDeadline` credits the remainder to `balances[user]` on a wallet-funded session, and records `pendingWei` on a credit session. A user who disappears pays only what they signed. A signed voucher is not reversed. There is no finalize-at-posted-usage: `finalize` never pays the node from a figure the node posts.

**Lost node key.** Nothing refunds automatically. On a wallet-funded session the user calls `closeSession` and then `finalize` after `closeDeadline`. On a credit session the same `closeSession` signature in the state rules above authorises a broadcaster, and `finalize` stays anyone. If both the node and the `sessionSigner` key are gone, the session stays open.

**Lost user wallet.** On a wallet-funded session the refund is credited to the depositing address. `withdraw()` pays only `msg.sender`. If that wallet is lost, the credit is unrecoverable. An anyone-can-close idle timeout is an open question, not v1. A credit session's remainder stays `pendingWei` until `claimChange`, and that remainder is not a balance of the deposit wallet.

**Stolen `sessionSigner`.** It can sign vouchers up to the effective cap until the session is settled. `closeSession` does not stop it. Vouchers stay redeemable until `closeDeadline`. v1 mitigation is a small per-session cap. Signer rotation or revocation is an open question for a later CIP. `sessionSigner` is not delegated to an orchestrator node in v1.

**No slashing in v1.** There is no slashing function, no dispute contract and no forced refund. The registration bond is withdrawable after `BOND_UNLOCK_DELAY` and is never seized. A dispute is a reputation event. The user's remedy is to stop signing, close, and record that event. Verifiable mode is opt-in and disclosed: re-execution by a user-chosen second node under a demonstrated deterministic profile, with no payment consequence when the outputs differ. The mode is public on-chain, so those checks cover only mode-2 sessions. They do not catch substitution on sessions the executor can see are not mode 2. The mitigation for standard-mode sessions is an opt-in, unannounced client-side spot check, which discloses the second reader.

A future penalty — a hash-mismatch slash, a forfeited bond, a forced refund — may be proposed only by CIP, only after a published positive result, and only when the CIP states a demonstrated deterministic profile, an evidence format, an adjudicator, an appeal, and the PoSP condition p > C/((1−r)(R+S)) with the values of p, C, r, R and S set in that CIP. This record leaves every value unset. Until that CIP exists, a mismatch is a reputation event.

`CLOSE_WINDOW` must exceed an expected sequencer outage plus about one day of force inclusion (evidence register §1, [V]). Nodes should redeem promptly. An outage that starts shortly before `closeDeadline` can still cost the node its unredeemed vouchers. That residual risk is stated plainly. It is not a guarantee.

**Residual risk of the input voucher.** A node can redeem the input voucher and never run the prompt. The user's loss is bounded by that prompt's input fee. The remedy is to stop signing and record a reputation event. No contract refunds it.

The protocol fee is 0. Multi-node work does not add a contract: N distinct `(node, modelId)` pairs are N sessions and N happy-path pairs ([ADR 0009](0009-opt-in-client-orchestration.md)).

## Alternatives considered

### One on-chain job per prompt

Rejected. For small models the L2 fee of a deposit and a payout exceeds the inference fee, on the order of the comparison in the contracts document (evidence register §1 and §6). It would also be a wallet action per message. A session amortizes two happy-path transactions across many chunks. On the reference client those are `openSessionFromCredit` and `closeWithVoucher`. Wallet `openSession` remains specified and is not that path. `withdraw()` is a later pull, once for many sessions.

### Dispute equals a full refund

Rejected. A user who could dispute and receive the whole deposit back would get free inference by disputing. A signed voucher stands. Quality disagreements are reputation events. Verifiable mode shows both outputs and reverses nothing.

### The node finalizes at claimed usage

Rejected. `finalize` pays the node nothing. If the node could settle at a usage figure it posted, an absent user could not police the counts. The node is paid only by vouchers the `sessionSigner` signed, up to the effective cap. The abandoned-client procedure redeems the highest non-final voucher first.

### Slash on hash mismatch

Rejected. Eighty unique outputs in 1,000 temperature-0 runs (evidence register §5, [V]) mean an honest pair of nodes can disagree. A slash needs a demonstrated deterministic profile, an evidence format, an adjudicator and an appeal, and it must meet the PoSP condition with values this record does not set. v1 has none of those. The bond is not a slash pool.

### Push ETH to the user or the node during settlement

Rejected. A recipient that reenters, or a contract wallet that cannot receive ETH, would lock a refund, a payment or a bond for everyone sharing the contract balance. Pull payments credit `balances[address]`. Only `withdraw()` sends ETH.

## Consequences

- A credit session opens with `openSessionFromCredit` and settles with `closeWithVoucher`; unused value stays `pendingWei` until a separate `claimChange` creates change notes and credits dust to the node. Deposits, change claims and withdrawals add transactions. A wallet-funded session settles to internal balances in two happy-path transactions, and `withdraw()` moves ETH out and can batch many sessions.
- Nodes bear the L2 gas of a credit spend. A spend costs about 230–270k L2 gas (evidence register §15, [U]: an estimate for Semaphore's `validateProof`, not a measurement of this contract). LeanIMT insertion gas is UNVERIFIED. Nodes price that gas into their offers ([ADR 0011](0011-anonymous-credits.md)).
- The node's loss on an abandoned client is at most one unpaid chunk of `CHUNK_TOKENS`, plus any input fee the client already signed. The user's loss on a node that takes the input fee and does not run is that input fee.
- A stolen `sessionSigner` is bounded by the cap the user already chose. Closing the session does not revoke the key before `closeDeadline`.
- Sequencer censorship longer than the remaining window costs the node unredeemed vouchers. Prompt redemption is the mitigation. There is no deadline extension in v1.
- On a wallet-funded session, a lost depositing wallet cannot recover its credited refund. Deposits should be sized to the task. A credit session's remainder is `pendingWei`, not `balances[user]`.
- No slashing means model substitution in standard mode is invisible to the contract. Reputation, opt-in verifiable mode and opt-in attested mode are the v1 responses. Each costs the user something, as the verification document states.
- Adding a penalty, a fee, a treasury or a dispute contract takes a CIP that amends the closed function list and, for a slash, supersedes this ADR after a published positive result.
- `CHUNK_TOKENS`, `CLOSE_WINDOW`, `MIN_BOND_WEI`, `MIN_DEPOSIT_WEI` and `BOND_UNLOCK_DELAY` have no values in this record.

## Links

- [docs/evidence-register.md](../evidence-register.md) §1, §5, §6, §15
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md)
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md)
- [docs/security/inference-verification.md](../security/inference-verification.md)
- [docs/economics/cost-and-pricing.md](../economics/cost-and-pricing.md)
- [ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md)
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0005](0005-hardware-classes-and-price-bands.md)
- [ADR 0008](0008-model-first-pools.md)
- [ADR 0009](0009-opt-in-client-orchestration.md)
- [ADR 0011](0011-anonymous-credits.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
- [docs/cip/0002-anonymous-credits-relays-and-ownerless-contexts.md](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md)
