# Comuns — Evidence register

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** [project-charter.md](project-charter.md), [requirements.md](requirements.md)

---

This register is the single list of external facts the Comuns documents may rely on. Each fact carries a mark: **[V]** verified at source, **[L]** likely, **[U]** unsure. Sections §1–§8 are a snapshot taken 2026-10-12; sections §9–§13 were retrieved 2026-10-13. A URL is given where one was recorded. Nothing outside this register may be cited as evidence; see section 14.

## 1. Arbitrum (§1)

- Stylus live since ~Sep 2024 via ArbOS 31 [L]; Rust first-class SDK, C/C++ supported [V] — docs.arbitrum.io/stylus/gentle-introduction
- New Stylus activations paused on One and Nova since 2026-10-02 by the Security Council after AI-assisted hand-crafted WASM caused chain-liveness DoS; no user funds at risk; active programs keep running until expiry; keepalive works; no reopening date [V] — docs.arbitrum.io/notices/stylus-activation-pause-notice
- ArbOS 61 renewal to Aug 2027 [U]
- Ink: 1 gas = 10,000 ink; compute 10–100x cheaper than EVM; memory 100–500x cheaper; SLOAD/SSTORE same; call overhead 8,832/352 gas [V]
- Limits: 24 KB compressed / 128 KB uncompressed; activation 1,659,168 gas + size fee; expiry 365 days; keepalive ≥31 days [V]
- stylus-sdk 0.10.10, MIT OR Apache-2.0; cargo-stylus [V]
- Arbitrum chains: Nitro; Rollup/AnyTrust/Alt-DA; custom ERC-20 gas token; Stylus included; 250 ms blocks; 6.4-day withdrawals; L3s on One/Nova owe no revenue share, others 10% [V]
- Fees (Arbiscan, 2026-10-13): gas 0.02 gwei, ERC-20 transfer ~$0.003, swap ~$0.01 [V]; ETH transfer ~$0.001 derived [U]
- BoLD permissionless validation Feb 2025 on One; L2BEAT Stage 1; ~6d 8h challenge; 3,600 ETH stake [V]
- Single sequencer; L1 force inclusion after ~1 day [V]
- Ordering moved to Priority Gas Auctions ~2026-09-23 [L/V]
- No sequencer-decentralization date [U]
- DAO: 10B ARB; treasury ~3.528B; constitutional quorum 50%, non-constitutional 40%; 14-day vote; 1M ARB to submit; timelocks 3 or 8 days + 3 days L1; Security Council 12 members, 9-of-12 [V]

## 2. Decentralized compute and inference networks (§2)

- Bittensor: own Substrate L1 (Rust), Python SDK, Yuma consensus, miners paid by emissions not per request, ~18/41/41 split [L]; Chutes subnet 64 claims Intel TDX + NVIDIA TEEs [L]
- Akash: reverse auction ~5 min, no protocol-level result verification, per-block escrow in ACT, experimental TEE, Cosmos SDK/Go [V]
- Ritual: EVM L1, TEE LLM precompiles, staked executors slashed, secrets ECIES to TEE key, private testnet since Dec 2024, no mainnet found [V]
- Gensyn: OP Stack rollup, mainnet Apr 2026 [L]; Verde + RepOps [V] arxiv 2502.19405; training-first [L]
- io.net: central matching, hardware checks after 2024 fake-GPU incident, Solana token, no privacy mechanism found [L]
- Hyperbolic: centralized market + PoSP/spML research [V] arxiv 2405.00295
- Nillion: nilCC TEE [V]
- Phala: TDX + NVIDIA TEEs [L]; dstack Rust, dcap-qvl Rust DCAP verifier MIT [V]
- Oasis: ROFL TEE apps, Rust SDK [L]
- Lilypad: Go, Apache-2.0, solver [V]; deterministic modules [L]
- Morpheus: on-chain bids, MOR stake, proxy-router carries prompts, 'tee' tags attested, settles on Base, MIT, Go + TypeScript [V]
- ORA: opML bisection to one-step MIPS VM, 7B on CPU-only PC [V] arxiv 2401.17555; <10 min window [L]
- EZKL: Rust zkML, audited 2025 [V]
- Prime Intellect: protocol repo (Rust, Apache-2.0) archived Jan 2026, TOPLOC [V]
- Nous Psyche: training only, Rust, Apache-2.0 [V]
- Nosana: Solana marketplace [L]; verification [U]
- Golem: yagna Rust, Polygon/Ethereum payments [V]; verification [U]
- Fluence: Arbitrum Orbit appchain, USDC [L]
- Exo: own devices, OpenAI-compatible API, Python + Rust, Apache-2.0, no payments or verification [V]
- Petals: block-sharded swarm, ~6 tok/s Llama 2 70B, README warns data processed by others, MIT, last release Sep 2023 [V]

## 3. Inference engines (§3)

All entries in this section are [V].

- candle: CPU/CUDA/Metal/WASM, no Vulkan/ROCm, GGUF, no built-in OpenAI-compatible server (third-party candle-vllm adds one), MIT/Apache-2.0, 0.11.0 [V]
- mistral.rs: CUDA (FlashAttention)/Metal/CPU; ISQ/GGUF/GPTQ/AWQ/HQQ/FP8; 'mistralrs serve' OpenAI-compatible with PagedAttention and continuous batching; MIT; v0.9.4 [V]
- llama.cpp: C/C++, MIT, ~131k stars; CUDA/HIP/Metal/Vulkan/SYCL/WebGPU; 1.5–8-bit quant; llama-server OpenAI-compatible; Rust bindings llama-cpp-2 (cuda/metal/vulkan/rocm) and llama_cpp [V]
- burn: CUDA/ROCm/Metal/Vulkan/WebGPU, no LLM server [V]
- ratchet: WebGPU, small [V]
- SGLang gateway and vLLM router are Rust [V]
- HF TGI: maintenance [V]
- Ollama is Go [V]

## 4. Privacy and encryption (§4)

- hpke crate 0.14.1, RFC 9180 (X25519, P-256/384/521, ML-KEM, X-Wing; AES-GCM, ChaCha20-Poly1305), no paid audit [V]
- ecies crate 0.2.11: secp256k1 + AES-256-GCM/XChaCha20 + HKDF-SHA256, interoperates with eciesjs [V]
- The executor must see plaintext unless FHE, MPC or TEE [L]
- TEE overhead (H100 + SEV-SNP, H200 + TDX): Llama-3.1-8B throughput −6.85%/−8.84%, TTFT +19–21%, 70B ~0–2.3% [V] arxiv 2409.03992
- EPID/IAS discontinued Apr 2025; DCAP or Intel Trust Authority [L]
- Automata on-chain quote verification ~3M gas, or ~350k via ZK (RISC Zero) [V/L]
- TEE.fail (Oct 2025): DDR5 interposer extracted TDX and SEV-SNP keys incl. attestation keys; can undermine NVIDIA GPU CC attestation; vendors treat physical attacks as out of scope [L]
- FHE hybrid ~2.2 MB/token on GPT-2; LLaMA-3-8B partially encrypted ~18 s/token on 8 GPUs [L]
- MPC: PUMA LLaMA-7B ~5 min/token [L]
- MetaMask eth_getEncryptionPublicKey/eth_decrypt deprecated since 2022 [V]
- ERC-5630 Draft [V]
- Sign-to-derive (e.g. Umbra) needs RFC 6979 deterministic signatures [L]
- Lit Protocol: BLS + TEE [L]

## 5. Inference verification (§5)

- zkLLM 13B <15 min [L]; DeepProve GPT-2 ~174 tok/min [L]; zkPyTorch Llama-3-8B ~150 s/token [L]
- TOPLOC: top-k activations every 32 tokens, 258 B per 32 tokens, validation up to 100x faster, detected 100% of model/prompt/precision changes in the authors' tests, GPU tolerance via thresholds, cannot detect speculative decoding, integrated with vLLM/SGLang [V] arxiv 2501.16007
- PoSP/spML: challenge with probability p; honest play is the unique equilibrium when p > C/((1−r)(R+S)); assumes deterministic execution [V]
- SVIP [L]
- 1,000 temperature-0 runs of Qwen3-235B gave 80 unique outputs; batch-invariant kernels made them identical at ~1.6x runtime on Qwen3-8B [V] thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference
- EigenLayer slashing live Apr 2025 [L]

## 6. Hardware, throughput and prices (§6)

- Single-stream llama.cpp Q4_K_M (2024), 8B: RTX 3090 ~112, 4090 ~128, A100 ~133–138, H100 PCIe ~144, M3 Max ~51, M2 Ultra ~76 tok/s; 70B: 2x3090 ~16, 2x4090 ~19, A100 ~22–24, H100 ~25, M2 Ultra ~12 tok/s [V]
- RTX 5090 32 GB, 575 W: Qwen3-8B ~186, 14B ~124, 32B ~61 tok/s; 70B Q4 does not fit [V]
- M4 Max 7B Q4_0 ~83 tok/s [V]
- Mac Studio M5 Ultra up to 512 GB [V]
- Batched TensorRT-LLM FP8: 8B ~27,569 tok/s on 1xH100; 70B ~3,191 tok/s [V]
- 4090 450 W; H100 SXM up to 700 W [V]
- US residential electricity ~18.8¢/kWh [L]
- 4090 ≈ $0.08/h ≈ ~$0.18 per 1M tokens, derived [U]
- Rentals, Oct 2026: RunPod 4090 $0.34 community / $0.74 secure, H100 SXM $2.69 / $3.49 [V]; Vast.ai medians 4090 ~$0.40, H100 ~$1.67 [L]; Akash H100 ~$2.71 [V]
- APIs per 1M tokens in/out: OpenRouter Llama-3.1-8B from $0.02/$0.04, Llama-3.3-70B from $0.10/$0.32, gpt-oss-120b from $0.03/$0.15 [V]; Groq gpt-oss-120b $0.15/$0.60 [V]; Together Llama-3.3-70B $1.04/$1.04 [V]

## 7. Model licenses (§7)

- Llama 3.3/4: commercial use + redistribution; >700M MAU needs a license; 'Built with Llama'; derived names start with Llama; Notice file; multimodal rights withheld from EU entities in 3.2/4 [V]
- Mistral Large 3 Apache-2.0 [V]; Mistral Research and Non-Production licenses forbid commercial hosting [V]
- Qwen2.5-72B: Qwen License, >100M MAU [V]; Qwen3/3.5 Apache-2.0 [L/V]
- DeepSeek R1/V3.1 MIT [V]
- Gemma 4 Apache-2.0; Gemma 3 own terms [V]
- Phi-4 MIT [V]
- gpt-oss Apache-2.0 + usage policy [V]

## 8. Governance and licensing practice (§8)

- Ethereum: off-chain governance, no coin vote; EIP Draft → Review → Last Call ~14 days → Final; Stagnant after 6 months [V]
- Rust RFC 10-day FCP [V]
- Bittensor BITs, Cosmos ADRs [L]
- Optimism Token House + Citizens' House [L]; 7-day veto after Developer Advisory Board [V]
- Arbitrum DAO Audit Program $10M ARB / 12 months; Stylus Sprint finished; new Foundation grants 'coming soon' [V]
- DCO = per-commit certification, grants no license; a CLA may enable relicensing [V/L]
- Apache-2.0 patent grant, MIT none [L]
- AGPL §13 network clause [L]
- BSL 1.1 not open source [V]
- Gitcoin GG24 ~$1.8M [L]

## 9. Speculative decoding (§9)

- Leviathan, Kalman, Matias, 'Fast Inference from Transformers via Speculative Decoding' (ICML 2023): accelerates sampling without changing the output distribution, no retraining; 2–3× on an 11B T5, per-setting ~1.4×–3.4×; acceptance rate α, speedup = (1−α^(γ+1))/((1−α)(γc+1)) with γ draft length and c draft/target cost ratio; larger draft models raise α but cost more (higher c), while a longer draft length γ leaves per-token α unchanged and raises the cost term γc+1; temperature 1 lowers α vs temperature 0 [V] arxiv 2211.17192
- Chen et al., 'Accelerating Large Language Model Decoding with Speculative Sampling': modified rejection sampling preserves the target distribution 'within hardware numerics'; a 70B target with a 4B draft on one TPU pod 1.92×–2.46× (code highest) [V] arxiv 2302.01318
- 'Speculation at a Distance' (arxiv 2606.25091, Jun 2026): pipelined distributed speculative decoding matches co-located only when round-trip time is below the edge drafting window; 'at WAN RTTs, the cloud round trip remains too large for pipelined DSD to beat co-located SD'; main benefit multi-tenant capacity — the quote is what the preprint says [V]; the result is not independently replicated [U]. Its baseline is co-located speculative decoding, not a single node doing ordinary decoding; documents say "no WAN speed-up is promised", never "no speed-up exists"
- Delay-adaptive speculation (arxiv 2606.20591): optimal draft length grows only logarithmically with delay; phase transitions at ~83 ms and ~111 ms in one edge+GPU setup — the quote is what the preprint says [V]; the result is not independently replicated [U]
- Edge-cloud early-exit (arxiv 2505.21594): up to 35% lower latency vs cloud-only decoding; network setup not described in the abstract — the quote is what the preprint says [V]; the result is not independently replicated [U]
- These 2025–26 preprints are not independently replicated [U]; the three entries above carry both marks inline for that reason
- llama.cpp llama-server supports a separate draft model (--model-draft, --spec-draft-n-max, default 3) plus n-gram and other modes; the docs give no measured speedups [V] github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
- Draft and target must share a vocabulary [L]
- mistral.rs exposes speculative decoding as 'MTP' with specific drafter checkpoints only, configured at launch, and states 'token-for-token equivalence is not guaranteed' [V]
- TOPLOC cannot detect speculative decoding (§5)

## 10. Sharding one model across machines (§10)

- Petals (NeurIPS 2023): each server holds a contiguous block segment; clients hold embeddings and choose a server chain by compute plus network latency; servers keep the KV cache; clients replay to a replacement on failure [V] arxiv 2312.08361
- Petals sequential steps/s at batch 1: Llama 2 70B on 3×T4 2.29 at <5 ms RTT, 1.57 at 100 ms RTT, vs 0.139 with offloading; BLOOM-176B on 10×RTX 3090 1.05 at 100 Mbit/s low latency, 0.34 at 100 ms RTT [V]
- Petals README: up to 6 tok/s Llama 2 70B, and 'Your data will be processed with the help of other people in the public swarm' [V]
- Exo: topology-aware auto-parallel (pipeline or tensor); claims 1.8× on 2 devices and 3.2× on 4 for tensor parallel, no methodology given; the legacy partitioner gives each device a contiguous slice proportional to its memory [V] github.com/exo-explore/exo
- llama.cpp RPC backend splits weights and KV cache across local and remote devices by memory; docs: 'proof-of-concept development stage', 'fragile and insecure', 'Never run the RPC server on an open network or in a sensitive environment!' [V] github.com/ggml-org/llama.cpp/blob/master/tools/rpc/README.md
- mistral.rs supports NCCL tensor parallelism, layer mapping and multi-node NCCL [V]
- prima.cpp (ICLR 2026): pipelined-ring parallelism; a 70B model at ~674 ms/token (~1.5 tok/s) on 4 home devices over Wi-Fi; 32B with speculative decoding 26 tok/s [V] arxiv 2504.08791
- SWARM parallelism (ICML 2023) is about TRAINING, not inference [V]
- Activations leak prompts: vec2text (EMNLP 2023) recovers 92% of 32-token inputs exactly from text embeddings [V] arxiv 2310.06816
- 'Prompt Inversion Attack against Collaborative Inference of LLMs' (IEEE S&P 2025): a malicious participant in split inference recovers the prompt from received activations at 88.4% token accuracy on a 65B model [V] arxiv 2503.09022
- 'Depth Gives a False Sense of Privacy' (USENIX Security 2025): a 4,112-token medical prompt nearly fully inverted (86.88 token F1) from a middle layer; four practical defenses failed to fully prevent inversion [V] arxiv 2507.16372
- Consequence: every shard holder must be treated as able to read the prompt.

## 11. Collective answers from multiple models (§11)

- Multiagent debate (Du et al., arxiv 2305.14325): 3 agents × 2 rounds of a 2023 proprietary chat model; single agent → debate: arithmetic 67.0 → 81.8, GSM8K 77.0 → 85.0 (majority vote 81.0), biographies 66.0 → 73.8, MMLU 63.9 → 71.1; the authors note debate is more expensive [V]
- Mixture-of-Agents (Wang et al., arxiv 2406.04692): proposers generate reference answers, aggregators synthesize, in layers; default 3 layers × 6 open-weight models (Qwen1.5-110B/72B, WizardLM-8x22B, Llama-3-70B, Mixtral-8x22B, dbrx) with an open-weight aggregator; AlpacaEval 2.0 LC win rate 65.1% using only open-weight models vs 57.5% for the strongest proprietary single model then tested; stated limitation high time-to-first-token [V]
- 'Rethinking Mixture-of-Agents' (arxiv 2502.00674): one strong model sampled many times (Self-MoA) beats mixed MoA by 6.6% on AlpacaEval 2.0; mixing models often lowers average quality [V]
- Self-consistency (ICLR 2023): sample many reasoning paths, take the majority answer; GSM8K +17.9%, SVAMP +11.0%, AQuA +12.2% over chain-of-thought [V] arxiv 2203.11171
- LLM-as-a-judge (Zheng et al., NeurIPS 2023): the strongest judge tested agreed with humans on 85% of non-tie votes vs 81% human–human; position bias (the strongest judge consistent on only 65.0% of swapped orders, weaker judges 23.8%–46.2%), verbosity bias and possible self-preference (+10% to +25%, evidence inconclusive); mitigations: judge twice with positions swapped, reference-guided judging [V] arxiv 2306.05685
- Debate does not reliably outperform self-consistency and is hyperparameter-sensitive [V] arxiv 2311.17371
- Accuracy can fall over rounds — agents flip correct → incorrect (sycophancy, conformity) [V] arxiv 2509.05396
- With 10 homogeneous 7–8B agents, up to 70.0% of previously correct answers destabilized by peers; correct answers present but discarded by plurality vote (oracle gap up to 32.3 pp); debate costs 2.1–3.4× the tokens of self-correction for equal or lower accuracy [V] arxiv 2605.00914

## 12. Parallel task decomposition (§12)

- Skeleton-of-Thought (ICLR 2024): the model writes a 3–10 point skeleton, then expands points in parallel and concatenates; up to 2.39× speedup across 12 models; quality at least as good in ~60% of cases; good for generic/knowledge/roleplay, poor for math, coding, Fermi and writing; ignores dependencies between points; a small router (~0.04 s) decides when to use it [V] arxiv 2307.15337
- LLMCompiler (ICML 2024): a planner builds a DAG of tasks with placeholders; a task-fetching unit dispatches ready tasks; an executor runs them in parallel; replanning when needed; up to 3.7× lower latency and 6.7× lower cost vs sequential ReAct, ~9% accuracy gain; the planner and the final join cannot be parallelized, the slowest parallel task sets the pace, and planner overhead made it slower on one benchmark [V] arxiv 2312.04511
- ReWOO: decoupling reasoning from tool observations; ~5× token efficiency, +4% accuracy on HotpotQA [V] arxiv 2305.18323
- APAR: models fine-tuned to fork output into a paragraph tree; up to 2× (4× with speculative decoding) [V] arxiv 2401.06761

## 13. Routing by task complexity, and existing answer aggregation (§13)

- RouteLLM (LMSYS 2024): learned routers between a strong and a weak model cut cost 'over 2 times in certain cases' without quality loss [V] arxiv 2406.18665
- RouteLLM blog: at 95% of the strong model's quality, cost cut >85% on MT-Bench, 45% on MMLU, 35% on GSM8K (weak model Mixtral 8x7B); only 14% of MT-Bench calls went to the strong model [V] lmsys.org/blog/2024-07-01-routellm
- FrugalGPT: a learned cascade matches the strongest model at up to 98% lower cost [V] arxiv 2305.05176
- Hybrid LLM (ICLR 2024): routing by predicted difficulty; up to 40% fewer large-model calls with no quality drop [V] arxiv 2404.14618
- AutoMix (NeurIPS 2024): the small model answers and self-verifies, a router escalates; >50% lower cost at comparable performance [V] arxiv 2310.12963
- Bittensor validators score miners for emissions; the protocol does not merge outputs into one answer [V]
- Allora combines numeric inferences as a loss-weighted average; designed for numeric targets, not free text [V] docs.allora.network/learn/inference-synthesis
- Fortytwo: nodes answer, then rank each other's answers pairwise; Bradley-Terry-style aggregation weighted by on-chain reputation; reported GPQA Diamond 85.90% vs 68.69% for majority vote [V] arxiv 2510.24801; ~10–15 s added latency per the company [L]; company executives said node operators could potentially see prompts [L]

## 14. How to cite

- Sibling documents cite a fact as 'evidence register §N' together with its mark ([V], [L] or [U]), for example: "new Stylus activations are paused (evidence register §1, [V])".
- Any claim that is not in this register is labeled UNVERIFIED where it appears.
- A [U] or [L] fact must not be presented as settled; a [L/V] or [V/L] fact keeps its compound mark.
- §1–§8 are a snapshot of 2026-10-12. The §1 fee snapshot (Arbiscan) is dated 2026-10-13 although retrieval was recorded as 2026-10-12, so it may be used only when labeled as a dated snapshot ("Arbiscan, 2026-10-13").
- §9–§13 were retrieved 2026-10-13. They are cited as 'evidence register §N' with their marks like every other section.
- The 2025–26 networked-speculative-decoding preprints in §9 carry both marks inline: [V] for what the preprint says, [U] because the result is not independently replicated. A document citing them carries both marks and the [U] stays; no document may cite them as [V] alone or upgrade them. The cited claim is "no WAN speed-up is promised", never "no speed-up exists".
- The llama.cpp RPC backend facts ('proof-of-concept', 'fragile and insecure', never on an open network) are §10, not §9; a citation to them must say §10.
- Adding or changing a fact requires a pull request to this file that states the source and the mark; reviewers check the source before merge.
