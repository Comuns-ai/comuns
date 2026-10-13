# ADR 0002: Run inference off-chain in a Rust node with pluggable backends

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

The chain chosen in [ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md) records offers and escrow. It does not run a model. The program an operator runs is a node on the operator's own machine. Nothing described here exists yet: there is no Rust project, no crate, no build and no deployment.

Operators will bring different devices. The evidence register lists engines that already cover those devices, and it lists their languages (evidence register §3, [V]). The node has to speak one protocol — HPKE, receipts, vouchers, the pinned tokenizer — while the kernels underneath may be C, C++ or Rust.

A claim that "Rust is faster" would be false. Throughput and latency come from kernels, memory bandwidth, batching and which models a backend can load. The language of the host process decides safety, packaging and the foreign-function surface. Measured differences between backends are why a model is offered on an adapter only after a published benchmark, not because of the host language.

## Decision

The Comuns node is one Rust binary that runs off-chain. It watches the registries and its own sessions on Arbitrum One, accepts encrypted jobs over TLS 1.3 and HPKE, runs them through a pluggable backend, meters tokens with the tokenizer pinned in the model manifest, exchanges node-signed receipts for client-signed vouchers, and redeems on-chain. Prompt, context and completion plaintext exist only in process memory, are zeroized after use and are never logged. Logging policy does not stop a modified node. It is the reference node's rule.

Backends sit behind one trait. Per-model choice of adapter is gated by the benchmark protocol: the node offers a model on an adapter only after the operator has published a self-benchmark of that model on that adapter and build, and `modelBenchmarkHash` names that result ([ADR 0008](0008-model-first-pools.md)).

Two adapters are in the proposal.

- **llama.cpp through Rust bindings is the first adapter.** The bindings named in the evidence register are `llama-cpp-2` (cuda, metal, vulkan, rocm) and `llama_cpp` (evidence register §3, [V]). The kernels are C/C++ (evidence register §3, [V]). The Rust side is a foreign-function wrapper. Devices: CPU, CUDA, Metal, Vulkan and ROCm (HIP) (evidence register §3, [V]). Quantizations from 1.5-bit to 8-bit are in scope (evidence register §3, [V]). This is the widest hardware coverage and the small-hardware path.
- **mistral.rs is the second adapter.** It is Rust, with CUDA (FlashAttention), Metal and CPU (evidence register §3, [V]). It provides paged attention and continuous batching (evidence register §3, [V]). Its HTTP server may run only on the loopback interface, after the HPKE boundary has decrypted the job. It is never a public, unauthenticated route for prompts.

The node uses continuous batching where the selected backend supports it. Scheduling concurrency is per class and is configuration. Inside one session, jobs run one at a time (`maxConcurrentJobsPerSession = 1`), because receipts and vouchers are one chain per session ([ADR 0004](0004-sessions-vouchers-and-no-slashing.md)).

Verifiable mode is advertised only after a deterministic profile has been demonstrated for that model and backend: repeated runs of a published test set produce byte-identical output. Temperature 0 and a pinned build are necessary and not sufficient. One thousand temperature-0 runs of one model produced 80 unique outputs without batch-invariant kernels (evidence register §5, [V]). Otherwise the node refuses mode 2. Support for TOPLOC on llama.cpp or mistral.rs is not claimed. TOPLOC is integrated with other engines and cannot detect speculative decoding (evidence register §5, [V]).

A LAN cluster behind one endpoint, using llama.cpp RPC on a private network or mistral.rs NCCL on a private fabric, is one node with one ordinary offer. The llama.cpp RPC backend is a proof of concept, fragile and insecure, and its documentation says never to run the RPC server on an open network (evidence register §10, [V]). This node must not run that RPC server on an open network. Cross-operator sharding is not a v1 node process ([ADR 0009](0009-opt-in-client-orchestration.md)).

No document may claim that Rust makes inference faster.

## Alternatives considered

### In-contract inference

Rejected. A model does not fit a contract. Stylus programs are limited to 24 KB compressed and 128 KB uncompressed (evidence register §1, [V]), and new Stylus activations are paused with no reopening date (evidence register §1, [V]; [ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md)). The chain would also see the prompt.

### A Python node

Rejected. The proposal is one Rust binary so that HPKE, metering, voucher checks and the chain client share one process and one packaging story. A Python node would be a second language on the path that holds plaintext. The devices the evidence lists are already covered by the two adapters (evidence register §3, [V]).

### A Go server (Ollama)

Rejected. Ollama is Go (evidence register §3, [V]). Putting it behind the node would add a process boundary and a second language, and it would not add a device or a quantization the two adapters lack. The reference node does not terminate prompts on a public Go HTTP API.

### zkML as the engine

Rejected for v1. The register's rates are not interactive: a 13B proof under 15 minutes, a small model at roughly 174 tokens per minute, and an 8B model at roughly 150 seconds per token (evidence register §5, [L]). zkML remains the candidate that could prove execution without a second prompt reader. It is not the engine that serves a session. [ADR 0004](0004-sessions-vouchers-and-no-slashing.md) leaves it as a later candidate, not a v1 penalty or a v1 backend.

### A from-scratch Rust kernel claimed to be faster

Rejected. No measurement in the register supports a claim that a new Rust kernel beats the C/C++ kernels in llama.cpp or the CUDA and Metal paths in mistral.rs. The host language does not set tokens per second. Shipping an unmeasured kernel would also drop the quantizations and devices the first adapter already has (evidence register §3, [V]). Per-model selection stays gated by a published benchmark. candle, burn and ratchet are not v1 adapters: candle has no Vulkan or ROCm and no built-in server, and burn has no LLM server (evidence register §3, [V]). They can be proposed later by CIP.

## Consequences

- Operators build and run a Rust program. This repository still contains no code.
- The llama.cpp adapter has a C/C++ foreign-function boundary. Memory safety at that boundary is a high risk owned by the node design, not removed by writing the host in Rust.
- Malicious weight files are refused when their hashes do not match the manifest. The chain does not check that the process loaded those bytes.
- Backend choice is an operator benchmark, published as `modelBenchmarkHash`, not a protocol default and not a language ranking.
- Local speculative decoding inside one node is an engine detail. It adds no reader. It stays off in verifiable mode, because mistral.rs states that token-for-token equivalence is not guaranteed (evidence register §9, [V]).
- Open-internet model sharding and cross-node speculative decoding are not v1 node processes. They are experimental Phase 3 spikes ([ADR 0009](0009-opt-in-client-orchestration.md)).

## Links

- [docs/evidence-register.md](../evidence-register.md) §1, §3, §5, §9, §10
- [docs/node/node-design.md](../node/node-design.md)
- [docs/node/hardware-classes-and-benchmarks.md](../node/hardware-classes-and-benchmarks.md)
- [docs/security/inference-verification.md](../security/inference-verification.md)
- [ADR 0001](0001-settle-on-arbitrum-one-evm-not-stylus.md)
- [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md)
- [ADR 0004](0004-sessions-vouchers-and-no-slashing.md)
- [ADR 0008](0008-model-first-pools.md)
- [ADR 0009](0009-opt-in-client-orchestration.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
