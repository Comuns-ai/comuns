# FAQ

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** [project-charter.md](project-charter.md), [glossary.md](glossary.md), [landscape.md](landscape.md)

---

Comuns is a community proposal for open-source, decentralized LLM inference settled in ETH on Arbitrum One. Nothing described here runs yet. No maintainer is seated, no price in wei is adopted, and mainnet is not deployable. Each answer points at the document that owns the detail. Amounts a person would see in the app are shown in ETH with the unit. This proposal does not claim a lower price or a stronger proof than a hosted API or than any other network.


### Can the node operator read my prompt?

In standard mode, yes: “This node can read your prompt and your answer. It should not learn who you are.” Granted context is readable too. In attested mode: “This node should not be able to read your prompt. A physical attack on the hardware can break that.” The client checks the quote and fails closed if no eligible node exists (hardware limits: evidence register §14, [V]/[L]). Verifiable mode adds a disclosed reader. See [privacy and contexts](security/privacy-and-contexts.md).

### How do I pay without being identified?

Your wallet makes a public deposit for a fixed-denomination note. Later, a membership proof spends the note without identifying its deposit, and a node or broadcaster opens the credit session. A fresh session signer signs usage vouchers; unused value becomes fresh change notes plus dust to the node. Jobs and session-specific chain reads go through a relay. Identifying text, timing and small groups can still link activity (evidence register §15–§16, [V]/[L]/[U]). See [ADR 0011](adr/0011-anonymous-credits.md).

### Who runs relays?

Registered operators post a bond and publish an endpoint. The client chooses a relay at random; its operator must be independent of the node’s operator. One address cannot register both roles, but two addresses may conceal common ownership. Relays receive a share of settled session value. No available relay means the request fails closed. See [ADR 0010](adr/0010-anonymous-by-default.md).

### Is this a mixer?

There is no dedicated anonymous withdrawal entry point. A credit holder who operates a node can open a session to it, sign vouchers and withdraw that node’s balance, because the contract does not verify that inference happened. Regulatory classification is UNVERIFIED and is a Phase 4 review item (facts in [evidence register §16](evidence-register.md), not legal advice). `ragequit` publicly credits the caller, bounded by that address’s net deposits in the group; it cannot distinguish deposit notes from change notes. See [ADR 0011](adr/0011-anonymous-credits.md).

### Can I run the model locally?

No. Local execution is not a product option or fallback. Inference runs only on network nodes; the client handles transport, orchestration and sampling decisions without model computation. Attested mode is the optional content-privacy tier. See [ADR 0010](adr/0010-anonymous-by-default.md).

### Do I need a GPU?

No GPU is needed to send a prompt; a network node runs the model. Operators must have enough memory to load the models they offer. Hardware classes select price bands and do not restrict model eligibility. No project benchmark has been run. See [hardware classes](node/hardware-classes-and-benchmarks.md).

### What does a request cost, and why does this proposal not claim to be cheaper than a hosted API?

No price is adopted. The disclosure sheet shows input and output rates, the cap and gas estimates in ETH before confirmation. Credit-session spend gas is borne by the node and reflected in its offer; the relay’s share comes from settled value. `openSessionFromCredit` rejects changed offer prices, and the client checks the copied prices through the relay before signing. There is no claim of a lower cost than hosted APIs. See [pricing](economics/cost-and-pricing.md).

### What is the difference between L2 gas and the inference payment?

Inference payment covers signed token usage; credit sessions split it between the relay and node. L2 gas pays for chain transactions and does not buy tokens. The node bears credit-spend gas and reflects it in its offer; deposit and public-exit transactions are wallet actions. Settlement leaves unused credit value for change rather than sending it to a wallet. See [pricing](economics/cost-and-pricing.md).

### Why does a session cover many messages instead of one transaction per message?

One credit spend funds a session that runs many jobs, one at a time. Usage vouchers are signed off-chain by a fresh session signer, so each message needs neither a chain transaction nor a wallet prompt. Signed vouchers are not reversed. Settlement records unused value for `claimChange`; the cap cannot be topped up, so further spending needs a new note and session. See [contracts and settlement](protocol/contracts-and-settlement.md).

### Why Arbitrum One, and why not Stylus for v1?

The proposal uses Arbitrum One and Solidity on the EVM for offers, anonymous credit sessions and optional context anchors. The chain runs no inference. The recorded activation pause is the reason Stylus was excluded from v1 (evidence register §1, [V]); this is a dated design rationale. See [ADR 0001](adr/0001-settle-on-arbitrum-one-evm-not-stylus.md).

### Why is there no token?

v1 has no protocol token, no emissions and no coin vote. Operators are paid in ETH from the session you opened. A decision is a CIP. A balance of any asset, including ARB, is not a vote on this project. The protocol fee is 0, so this proposal has no treasury. See [adr/0007-no-protocol-token-in-v1.md](adr/0007-no-protocol-token-in-v1.md) and [../GOVERNANCE.md](../GOVERNANCE.md).

### Why is the node written in Rust, and why are the kernels C and C++?

Inference runs off-chain in an open-source Rust node so the process, the meter and the voucher checks share one program. The first backend is llama.cpp through Rust bindings, and those kernels are C and C++ (evidence register §3, [V]). The second backend is mistral.rs (evidence register §3, [V]). The kernels do the math. This proposal does not claim that Rust alone makes inference faster. See [adr/0002-off-chain-rust-inference.md](adr/0002-off-chain-rust-inference.md) and [node/node-design.md](node/node-design.md).

### Why not zero-knowledge proofs for the result?

The proposal uses opt-in re-execution by a user-chosen verifier under a demonstrated deterministic profile. That verifier is another content reader, reached through a relay and funded by its own credit session. The evidence for result-proof costs is recorded separately (evidence register §5, [L]); the credit membership proof does not prove that inference happened. See [inference verification](security/inference-verification.md).

### How are nodes kept honest without slashing?

Clients check signed receipts, token counts and delivered chunks before signing vouchers. A node can still redeem a signed input voucher without running inference; signed vouchers are not reversed. The remedy is to stop signing, close the session through the relay or a broadcaster with a session-signer authorization, and record a reputation event. Disagreement is not a refund or slash. See [inference verification](security/inference-verification.md).

### What is a context, and how is it shared between nodes?

A context is a versioned encrypted blob. Your vault keeps the wallet’s context-key list private; an independent context key signs each grant, and the client wraps only the granted versions’ keys to the node. Hosts are trusted for sequencing and availability. Saved head checkpoints reject rollback, but unsynced devices and stale backups have limits; a globally consistent multi-device head needs a broadcaster-submitted public anchor. Backups hold keys and checkpoints, not ciphertext. See [ADR 0012](adr/0012-contexts-without-a-wallet-link.md).

### What happens if I close my laptop in the middle of an answer?

An unacknowledged output chunk is unpaid. With the voucher log you can resume or settle; without it, stop signing and use the session signer to authorize closure through a relay or broadcaster. The node can also close; anyone can finalize after the deadline. Unused value stays in `pendingWei` until a session-signer-authorized `claimChange` creates fresh notes. If both node and signer are gone, the session stays open. See [contracts and settlement](protocol/contracts-and-settlement.md).

### What happens if the sequencer is down?

The evidence register records a single sequencer and L1 force inclusion after about one day (evidence register §1, [V]). That does not guarantee timely voucher redemption near a close deadline. Credit-session closure needs the node or a session-signer authorization sent through a relay or broadcaster; nothing closes automatically. L2 settlement is distinct from L1 finality. See [contracts and settlement](protocol/contracts-and-settlement.md).

### Which model licenses can a node host for pay?

The registry records a license identifier and `commercialHosting`; it grants no license. Offers, `openSession` and `openSessionFromCredit` refuse models whose flag is false. Operators remain responsible for the exact weights’ license. Model registration requires a governance CIP, and nobody is seated to register mainnet models. See [model registry and licenses](node/model-registry-and-licenses.md).

### Is training supported?

No. Scope is LLM inference. Training, fine-tuning and federated learning are non-goals, and this proposal does not plan them. See [project-charter.md](project-charter.md).

### How do I propose a change?

Copy the CIP template and fill it in. Anyone may file a CIP, including an operator of a small machine. A CIP moves Draft, then Review, then Last Call for 14 days, then Final, if no blocking objection is open. A CIP in Last Call cannot become Stagnant. A substantive edit during Last Call returns it to Review and starts a new 14-day Last Call. One inactivity clock of 6 months applies to Draft and Review only. There is no token vote. While nobody is seated, filing a CIP does not merge it. See [../GOVERNANCE.md](../GOVERNANCE.md) and [cip/README.md](cip/README.md).

### Who controls the project today?

Nobody is seated. No maintainer has merge authority, no working group has a chair, and no ADR is adopted. The first people with merge authority have to be named by a public CIP that finishes Last Call and becomes Final. Until that day, nobody may merge, run a timelock, or take an emergency action. A name written in a draft seats nobody. ARB balances are not votes here. See [../GOVERNANCE.md](../GOVERNANCE.md) and [../MAINTAINERS.md](../MAINTAINERS.md).

### How could I run a node later?

Nothing runs yet. The proposed path is to run the Rust node, pass a class benchmark, post the bond and offer registered models the machine can load, with valid bands and per-model benchmark hashes. The node registers its job HPKE key and OHTTP gateway configuration and receives requests through relays. Mainnet still needs governance and parameters. See [node design](node/node-design.md).

### Can my node serve any model?

Any registered model it can load, subject to `commercialHosting`, a per-model benchmark and valid prices for its class and the model’s tier. `maxTier` is informational, not an eligibility gate. A model must first be registered through governance. See [model registry](node/model-registry-and-licenses.md).

### What is a model pool?

The set of nodes with current offers for one model, enumerated from registry state and events. It is neither a contract nor a payee: a credit session pays the selected node and relay. If no acceptable node is available, the client says so and does not silently change models. See [ADR 0008](adr/0008-model-first-pools.md).

### How do I choose between a cheap small node and an expensive strong node for the same model?

Pick the model first, then compare its nodes’ quotes, measured speed, reputation and privacy mode. Classes select ordered price bands; stronger hardware must charge more for the same model. Benchmarks are claims, not unfakeable proof. The sheet shows rates and caps before you confirm. See [pricing](economics/cost-and-pricing.md).

### Do several nodes see my prompt?

The default is one node, whose operator can read content in standard mode. Multi-node features require confirmation for each request. The disclosure sheet lists every recipient and distinguishes full-prompt recipients from operator-readable recipients. An attested request requires all plaintext recipients to be attested; an unavailable confirmed set fails closed. See [privacy and contexts](security/privacy-and-contexts.md).

### What is a collective answer, what does it cost, and when is it a bad idea?

Several network nodes answer independently, reviewers cross-check, and a synthesizer reports an answer plus disagreements. Each paid node-and-model pair uses a credit session. The sheet discloses recipients, operator readability and total cost. This opt-in quality mechanism is usually unsuitable for a short lookup or a request that must minimize readers and latency. It is not verification and changes no signed payment. See [collective answers](protocol/collective-answers.md).

### What happens when several nodes disagree?

The client labels the synthesis contested and shows its splits list and original answers. Missing or malformed required fields make synthesis incomplete, in which case the raw answers and critiques remain available. Disagreement reverses no voucher and triggers no slash. See [collective answers](protocol/collective-answers.md).

### Can a big task be split into parallel sub-tasks on different nodes, and who sees what?

Only with your opt-in. The client executes a plan in waves; every paid node-and-model pair has a credit session. Planners, reviewers and merge nodes are disclosed recipients, and sub-task payloads are treated as containing prompt text unless checked otherwise. Changes to recipients, scope or caps require a new confirmed sheet. See [orchestration](protocol/orchestration.md).

### Who assesses and plans, and who pays each planning, review and retry call?

On-device rules and user choices assess the request without model computation. Model-based planning, review, merging, synthesis and retries run on disclosed network nodes through credit sessions. You pay signed work, including a failed attempt followed by a confirmed retry. Planner output cannot authorize a new recipient or raise a cap. See [orchestration](protocol/orchestration.md) and [pricing](economics/cost-and-pricing.md).

### Can one big model be split over several small machines?

Only in the opt-in Phase 3 testnet spike. Disclosed unpaid volunteer nodes perform all model computation, including embeddings and the output layer; every holder is a reader. The client mediates stages through relays using OHTTP to each holder’s registered gateway key, without an inner job HPKE envelope. Holders have no sessions or payments, mainnet refuses the feature, and no speed-up is promised. See [distributed execution](node/distributed-execution.md).

### Can small nodes speed up a big node with speculative decoding?

That is an experimental Phase 3 testnet spike, with no promised WAN speed-up. The draft and target nodes are both disclosed readers, each funded through a credit session; acknowledged draft tokens are billable even when rejected. It is incompatible with verifiable mode. Speculation inside one serving node is an engine detail, not client-side model execution. See [distributed execution](node/distributed-execution.md).

### What is an orchestrator node, and must I use one?

It is an optional network node for model-based planning, merging or synthesis, paid through a credit session and listed on the disclosure sheet. It holds no session signer and cannot authorize your other sessions. The default orchestrator is control logic in the client SDK, with no model computation on your device. See [orchestration](protocol/orchestration.md).
