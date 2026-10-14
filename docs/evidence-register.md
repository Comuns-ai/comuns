# Comuns — Evidence register

Author: Comuns contributors
Status: Draft
Category: Analysis
Created: 2026-10-12
**Reference:** [project-charter.md](project-charter.md), [requirements.md](requirements.md)

---

This register is the single list of external facts the Comuns documents may rely on. Each fact carries a mark: **[V]** verified at source, **[L]** likely, **[U]** unsure. Sections §1–§8 are a snapshot taken 2026-10-12; sections §9–§13 were retrieved 2026-10-13; sections §14–§16 were compiled 2026-10-13 from two screened research annexes (annex A: private inference; annex B: anonymous payments and relays), and each of their facts names the annex and the source the annex gives. A URL is given where one was recorded. Nothing outside this register may be cited as evidence; see section 17.

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

## 14. Private inference: MPC, FHE and TEE (§14)

Compiled 2026-10-13 from annex A (private-inference research, screened). Marks follow the annex: [V] checked in the source, [L] likely (abstract, secondary source or vendor), [U] unsure; "(calc)" is the researcher's own arithmetic and keeps the annex's mark, or [U] where the annex gives none. This section supersedes nothing in §4: the §4 FHE/MPC/TEE bullets stay a dated 2026-10-12 snapshot with different figures.

MPC (secure multi-party computation)

- PUMA: 3PC replicated secret sharing, semi-honest, secure only if at most 1 of 3 parties is corrupt; LLaMA-7B with an 8-token prompt, first token 200 s and 1.79 GB on a LAN (0.1 ms RTT, three 128-thread servers) [V] — annex A R1, PUMA arXiv 2307.12533; second token about 164 s and 2.06 GB (calc) [V] — annex A R1
- Ditto (ICML 2024): 3PC, semi-honest, honest majority; GPT2-base 233 s on a WAN of 400 Mbps / 40 ms; BERT-base 30.6 s on LAN, 303.5 s on WAN; code not released [V] — annex A R4
- SIGMA (PoPETs 2024): 2PC function secret sharing with a dealer doing preprocessing, semi-honest; per 128-token pass with preprocessing excluded, Llama2-7B 23.1 s / 12.1 GB and Llama2-13B 37.6 s / 18.9 GB on a 9.4 Gbps / 0.05 ms LAN with A6000 GPUs; needs an honest dealer [V] — annex A R3
- BumbleBee (NDSS 2025): 2PC between client and server, HE + oblivious transfer, no third party; LLaMA-7B at 7.96 min and 6.27 GB per token on a 1 Gbps / 0.5 ms LAN [V]; GPT2-base (64-token prompt, 1 token out) 1.48 min on LAN and about 2.05 min on a 400 Mbps / 4 ms WAN [V]; the client is one of the two compute parties — annex A R2
- Permutation-based schemes (PermLLM, STIP, Centaur) are broken: an ICML 2025 attack recovers prompts exactly 97.6–100% of the time [V] — annex A R10, R11, PermLLM arXiv 2405.18744, permutation attack arXiv 2505.18332
- CrypTen was archived in May 2025 [V] — annex A §1
- No maliciously secure MPC result at 1B parameters or more was found; Mosformer, the first maliciously secure 3PC for transformers, covers BERT and GPT-2 only [L] — annex A §1, R13. The "not found" is a search result, not a proof of absence [U]
- 3PC schemes are secure only if at most 1 of 3 parties is corrupt [V] — annex A R1, R4; a Sybil operator controlling 2 of 3 nodes breaks privacy completely [U] — annex A §7 (researcher's reasoning)

FHE (fully homomorphic encryption)

- NEXUS (NDSS 2025): Llama-3-8B, 1 token out, 51.8 s on GPU batch-averaged (1,088 s on CPU) [V] — annex A R15
- ROSETTA (CCS 2026), per token on an A100: GPT-2 1.31 min, TinyLlama-1.1B 2.71 min, Llama-3-8B 5.18–6.79 min [V] — annex A R20, ROSETTA arXiv 2609.16915
- Cachemir: Llama-3-8B at 1.61 min/token on an A100, perplexity unchanged [V]; ROSETTA reports a conflicting figure for it — annex A R19, Cachemir arXiv 2602.11470
- Zama Concrete ML hybrid: the server runs only the linear layers and the client runs attention in the clear; GPT-2 about 11 s/token on a GPU server; the license grants no patent rights [V] — annex A R21, Zama Concrete ML LLM docs
- No FHE accelerator shipping for LLMs was found: Intel Heracles is a prototype with no commercial plan, Niobium has no ship date [V] — annex A R23, IEEE Spectrum Heracles March 2026

TEE (confidential-computing CPUs and GPUs)

- Google Cloud H100 + Intel TDX is generally available [V] — annex A R30, Google Cloud blog August 2025
- Azure offers H100 + AMD SEV-SNP [V] — annex A R31, Azure docs
- Blackwell B200/B300 and the RTX PRO 6000 support confidential computing [V, vendor] — annex A R29, NVIDIA
- NVIDIA reports a confidential-computing overhead of 1–8% [V, vendor] — annex A §5, NVIDIA
- An independent H100 + TDX study measured time-to-first-token up 21.8–27.8% and throughput down 11.5–21.1% [V] — annex A R28
- NVIDIA's attestation service (NRAS) checks the GPU report together with the CPU TEE measurements; keys are released only after that [V] — annex A R29
- TEE.fail (S&P 2026): a DDR5 interposer costing under $1,000 extracts TDX and SEV-SNP keys; NVIDIA attestation reports are not VM-bound, so a report can be relayed; Intel and AMD consider physical attacks out of scope [V] — annex A R32, tee.fail
- TDXRay (S&P 2026) recovers prompts from tokenizer memory-access patterns with 91.5–94.2% similarity [L] — annex A R34, tdxray.cpusec.org
- Battering RAM / WireTap (2025) are further physical attacks [L] — annex A §5
- Every network shipping private LLM inference today uses TEEs: NEAR AI Cloud (TDX + NVIDIA CC on H200, attested TLS) [V], Nillion nilAI (NVIDIA CC TEE, no MPC for LLMs) [V], Phala (H100/H200 TEEs) [V], Chutes [L] — annex A §6, NEAR AI, Nillion and Phala docs

What leaks in every approach, and the scale gap

- Output length alone reveals the language with more than 75% precision [V] — annex A R42
- Timing and packet sizes reveal the topic (Whisper Leak) [L] — annex A R43, Whisper Leak, The Hacker News, November 2025; annex B §5 marks the Whisper Leak paper itself [V] (see §16)
- The model and architecture are visible to the compute parties [U] — annex A §7 (researcher's reasoning)
- GPU TEEs cost 1–28% and are the only option shown at 70B scale and beyond [U] — annex A §7, combining R28 and the NVIDIA figure above
- A 200-token answer at 7–13B with the best cryptographic results (SIGMA, NEXUS, Cachemir) takes hours; no MPC or FHE result at 70B was found [U] (calc) — annex A §7

## 15. Anonymous credits, relays and precedents (§15)

Compiled 2026-10-13 from annex B §1, §2, §4, §6 and §7 (anonymous payments and relays research, screened). Marks follow the annex: [V] verified in the source, [L] likely (abstract, secondary, vendor or snippet), [U] unsure or the researcher's own estimate.

Semaphore v4

- An identity commitment goes into an on-chain LeanIMT/Poseidon group; a spend is a membership proof plus a per-scope nullifier; `validateProof` rejects reused nullifiers, verifies the proof and stores the nullifier [V] — annex B §1, Semaphore docs and repo
- Semaphore has no deposit or withdraw logic, so a payment pool must be built on top [U] — annex B §1
- Anonymity set: the group, with tree depth 1–32 [V] — annex B §1, Semaphore docs and repo
- Proof system: Groth16 with a snarkjs verifier [V] — annex B §1, Semaphore docs and repo
- Trusted setup: more than 400 participants, finished 13 July 2024 [V]; a second Phase-2 ceremony followed a ZK-Kit circuit fix, its date and participant count unconfirmed [L] — annex B §1, Semaphore docs and repo
- Live on Arbitrum One: Semaphore `0x8A1f…693D`, verifier `0x4DeC…31f8` [V] — annex B §1, Semaphore docs and repo
- No published v4 gas figure; a generic Groth16/BN254 check is about 181k gas plus about 6.15k per public input [V]; Arbitrum charges EVM instructions at Ethereum gas plus a parent-chain data fee (Brotli-compressed size × 16) [V] — annex B §1
- Estimate for Semaphore's own `validateProof`: about 230–270k L2 gas [U] — annex B §1 (researcher's estimate)
- The Arbitrum gas-price floor is unclear: sources give 0.1, 0.02 or 0.01 gwei [L] — annex B §1
- Proving time for the Semaphore-32 circuit: iPhone 16 Pro native rapidsnark 143 ms, ark-works 151 ms, snarkjs 1,002 ms; iPhone browser 652 ms (ark-works) and 920 ms (snarkjs); Samsung S23 Ultra rapidsnark 166 ms, snarkjs 2,146 ms [V] — annex B §1, Semaphore docs and repo
- Audits and license: v4.0.0 audited by PSE; v3 audited by Veridise; MIT license [V] — annex B §1, Semaphore docs and repo
- Contract source, read 2026-10-13 (semaphore-protocol/semaphore, `packages/contracts/contracts/Semaphore.sol` and `interfaces/ISemaphore.sol`):
  - `SemaphoreProof` has the fields `merkleTreeDepth`, `merkleTreeRoot`, `nullifier`, `message`, `scope` and `points[8]` [V].
  - `validateProof(groupId, proof)` has no access modifier: any caller holding a proof can submit it, which verifies the proof and stores the group's nullifier [V].
  - `verifyProof` accepts the current root, or a replaced root until the group's `merkleTreeDuration` has passed since the replacement; `createGroup()` sets 1 hour by default, and the duration is settable by the group admin [V].
  - `message` and `scope` enter the verifier as public inputs hashed as `uint256(keccak256(abi.encodePacked(x))) >> 8` [V].
  - Proof depth is bounded by `MIN_DEPTH`..`MAX_DEPTH` and is a proof parameter [V].
  - LeanIMT insertion gas and `addMember` duplicate-leaf behaviour were not checked [U].
  - Source: Semaphore repository contract source, read by the project on 2026-10-13.

Other credit and pool designs

- Privacy Pools (0xbow): deposits are public; a full or partial withdrawal is a Groth16 proof of inclusion in the state tree and in the ASP-approved label set; a partial withdrawal re-commits the remainder (the change pattern); withdrawals can go through a relayer charging a basis-point fee; each proof is bound to its parameters by a context hash; ragequit lets the depositor always withdraw publicly without ASP approval [V] — annex B §1, Privacy Pools docs and repo (0xbow-io/privacy-pools-core)
- Privacy Pools anonymity set is the ASP-approved subset [L] — annex B §1
- Privacy Pools trusted setup: Groth16/Circom on BN254, Phase 2 in March 2025 with 514 and 513 contributions; only an Ethereum mainnet ETH pool is listed, no Arbitrum deployment found; Apache-2.0 with an audit directory in the repo; gas and proving time not found [V] — annex B §1, Privacy Pools docs and repo, L2BEAT
- Railgun: live on Arbitrum, contract `0xFA70…A4b9`; UTXO notes with arbitrary amounts, each token with its own anonymity set; Groth16/BN254, 54 circuits, Phase 2 with 304 contributions ending December 2022; 0.25% fee on each shield and unshield, broadcasters about 10% over gas; PPOI list providers flag illicit funds and new shields wait 1 hour; L2BEAT reports a 7-day exit window but flags contract permissions that contradict it [V] — annex B §1, Railgun docs, L2BEAT
- Tornado-style pools: fixed 0.1 / 1 / 10 / 100 ETH denominations, Groth16 with a MiMC tree, setup of 1,114 contributions; a malicious governance proposal (May 2023) and an app build that leaked deposit notes (January 2024) [V] — annex B §1, L2BEAT; an Arbitrum deployment was announced in November 2021 [L] — annex B §1
- RLN: each message reveals a share y = k + a·x; reusing a ticket index reveals the secret key k, which allows slashing [V] — annex B §1
- "ZK API Usage Credits" (Crapis, credited with Buterin; ethresear.ch, 11 Feb 2026): a maximum cost per request plus refunds [V] — annex B §1, ethresear.ch/t/24104
- zkAPI (Ethereum Foundation): mainnet since 1 Oct 2026, Groth16/BN254 with a 32-level tree, single-party trusted setup, labelled experimental, mainnet and Sepolia only [V]; spend proofs are verified off-chain [L] — annex B §1, github.com/ethereum/zkapi
- IETF Anonymous Credit Tokens: an expired individual draft; BBS-style keyed-verification credentials with partial spends and anonymous change [V] — annex B §1, draft-schlesinger-cfrg-act

Blind-signature tokens and issuers

- RFC 9576 defines the roles Client, Attester, Issuer and Origin [V]; RFC 9578 token types are VOPRF(P-384), privately verifiable, and Blind RSA-2048, publicly verifiable, and neither carries an amount or metadata [V] — annex B §1, RFC 9576, RFC 9578
- Issuers hold secret keys, so issuance happens off-chain [U] — annex B §1
- Issuer options: (a) each node as its own issuer fragments the anonymity sets, and RFC 9576 says to limit active configurations [V] — RFC 9576; (b) threshold issuance with Coconut (NDSS 2019) [L] or Nym zk-nyms with a t-of-n quorum of signers [V] — Coconut NDSS 2019, Nym zk-nym docs; (c) a central token service, as Apple PCC uses rate-limited RSA blind signatures [V] — Apple PCC documentation; all via annex B §1
- If issuer and origin collude, a distinctive gap between challenge and issuance can link them [V] — annex B §1, RFC 9576

Metered sessions

- Existing patterns: Privacy Pools partial withdrawal with change re-committed; a maximum cost up front then refunds by signed tickets or a homomorphic running total; zkAPI's capped lease with actual usage deducted afterwards; ACT anonymous change on partial spends [V] — annex B §2
- Refund amounts and the server-visible settlement log let a server re-link requests; a forum simulation recovered per-user chains; the proposed fix is fixed budget classes of 256/512/1024/2048 tokens at an estimated 20–40% cost overhead [V] — annex B §2, zkAPI (ethresear.ch/t/24104)
- Tornado Cash: address reuse and fund-flow links trace 5.1–12.6% of withdrawals, FIFO timing adds 15–22 percentage points, and over $2.3B was linked; v3 of that paper was withdrawn over reference errors [V] — annex B §2
- Mixer anonymity sets shrink 27.34% on average (Ethereum) and 46.02% (BSC); advertised sizes are mostly inaccurate [V] — annex B §2
- Zcash heuristics shrink the anonymity set "considerably" [V] — annex B §2
- Mitigations: common amounts, a delay before exiting, fresh addresses, client-side delays before redeeming tokens [V] — annex B §2
- No authoritative minimum anonymity-set size was found [U] — annex B §2 (a search result, not a proof of absence)

Network-level anonymity

- Oblivious HTTP (RFC 9458): the relay sees the client's IP but not the content, the gateway sees the content but not the IP, and relay and gateway must be run by different entities; a fresh HPKE context per request; no streaming; no forward secrecy within a key configuration; traffic analysis is out of scope [V] — annex B §4, RFC 9458
- Each OHTTP request costs at least two HTTP requests; no published millisecond figures; ODoH, a similar design, is "comparable" to DoH [V] — annex B §4, RFC 9458, ODoH (PoPETs 2021)
- Chunked OHTTP (draft -08, February 2026, at the IESG) enables streaming; interactive exchanges let the relay or gateway measure round-trip time [V] — annex B §4, draft-ietf-ohai-chunked-ohttp
- Tor median round-trip to the response header (20 Sep 2026): 100–540 ms to public servers, 250–680 ms to onion services [V] — annex B §4, Tor Metrics; DeepCorr reports 96% flow-correlation accuracy from about 900 packets [L] — annex B §4, DeepCorr
- Nym: 5 hops with about 15 ms average mixing delay per hop; Nym publishes no measured latency [V] — annex B §4, Nym limitations

Precedents: relays combined with TEE inference

- Apple Private Cloud Compute: one-time RSA blind-signature tokens (RFC 9578 style) unlinkable to the request; the client chooses randomly among relays run by distinct third parties (Cloudflare, Fastly); relays route to attested nodes; the client encrypts only to a subset of nodes; node keys are checked against a transparency log; goal: a limited compromise must not let an attacker steer requests from specific users [V] — annex B §4, §6, Apple PCC documentation
- Apple PCC published limits: the relay exposes the client's rough region and headers can help target a user; target diffusion is bounded by the number of node ensembles (k) that can decrypt a request; a software attack could work fleet-wide; metering could re-link usage, mitigated by a Cost Aggregation Service; the multi-turn KV cache is encrypted with keys the device supplies each turn and PCC keeps no keys between turns [V] — annex B §6, Apple PCC documentation
- Cloudflare runs an OHTTP Relay and launched an OHTTP Gateway in October 2026 [V] — annex B §4
- Meta WhatsApp Private Processing (April 2025): anonymous credentials, a third-party OHTTP relay, RA-TLS to confidential VMs and confidential-compute GPUs; Trail of Bits found 28 issues, 8 of them High [V] — annex B §4, §6, Meta Engineering (29 Apr 2025), Trail of Bits WhatsApp Private Processing review (Aug 2025)
- Google Private AI Compute (November 2025) uses IP-blinding relays [V] — annex B §4, §6, NCC Group Google report v1.4 (8 Nov 2025)
- NEAR AI: Intel TDX plus NVIDIA confidential computing on H200s, API keys, gateway metadata undocumented [V] — annex B §6
- OpenGradient: OHTTP to AWS Nitro enclaves, an on-chain enclave registry, and relay-to-gateway payment via x402 on Base [V] — annex B §6
- TEE.fail: a DDR5 interposer under $1,000 forges TDX attestation that passes Intel's checks and reuses NVIDIA attestations; Intel and AMD treat it as out of scope [V] — annex B §6, TEE.fail (see also §14)

Researcher's takeaways (annex B §7, [U] unless cited)

- A zkAPI-style vault on Arbitrum with fixed-denomination deposits into a Groth16/BN254 note tree, per-request RLN spends verified off-chain by nodes, and the chain touched only for deposit, batched settlement and escape at about 200–270k L2 gas per on-chain proof [U] — annex B §7
- Fixed budget classes to avoid refund linkage, re-randomized change, delayed and batched settlement [U] — annex B §7
- An OHTTP relay run independently of node operators, chunked OHTTP for streaming, a fresh HPKE context per request, size-bucket padding and token batching, and gateway keys published in one on-chain registry so no user can be given unique keys [U] — annex B §7
- Give each conversation a random ID and a client-held key; store the encrypted blobs off-chain; deliver keys per turn inside the attested channel (the PCC pattern); never reference the wallet on-chain; turns within one conversation are linkable [U] — annex B §7 (researcher's reasoning)
- Residual risks: prompt content and stylometry, relay–node timing correlation, small anonymity sets at launch, physical attacks on TEEs, trust in the trusted setup, and legal exposure (§16) [U] — annex B §7

## 16. Deanonymization and legal facts (§16)

Compiled 2026-10-13 from annex B §3 and §5. Marks follow the annex. The legal items are facts as the annex reports them, not legal advice.

What the prompt text reveals

- LLMs infer personal attributes from text at up to 85% top-1 accuracy [L] — annex B §5, deanonymization research list
- An LLM pipeline linked pseudonymous profiles at up to 68% recall at 90% precision [V] — annex B §5, deanonymization research list
- Query-log precedent: AOL user 4417749 [L] — annex B §5

Traffic and node-side side channels

- Token lengths alone let attackers reconstruct 29% of responses and infer the topic of 55% [V] — annex B §5, deanonymization research list
- Whisper Leak (28 LLMs): often more than 98% AUPRC; padding, batching and packet injection reduce it, but none fully protects [V] — annex B §5, Whisper Leak (annex A marks the secondary report [L], see §14)
- Unpadded ciphertext length leaks request and response size [V] — annex B §5
- vLLM's prefix cache leaked through time-to-first-token (AUC 0.99), fixed in 0.9.0 [L] — annex B §5, CVE-2025-46570
- Trail of Bits flagged unmasked output size and possible tokenization-cache leaks [V] — annex B §5, Trail of Bits WhatsApp Private Processing review (Aug 2025)

Relay–node correlation and multi-turn linkability

- NCC Group found timing side channels in Google's IP-blinding relay that "may be able to unmask" users, exploitability Low [V] — annex B §5, NCC Group Google report v1.4 (8 Nov 2025)
- Trail of Bits: rotating OHTTP or credential keys could deanonymize users, severity Medium [V] — annex B §5, Trail of Bits WhatsApp Private Processing review (Aug 2025)
- OpenGradient states that timing and volume metadata are not protected [V] — annex B §5
- Apple PCC deliberately links the turns of one conversation [V] — annex B §5, Apple PCC documentation
- Mitigations: fresh keys per request; padding, batching and packet injection; consistent issuer keys for all users [V] — annex B §5
- No study of conversation splitting was found [U] — annex B §5 (a search result, not a proof of absence)

Legal and regulatory facts (not legal advice)

- OFAC sanctioned Tornado Cash in August 2022 [V] — annex B §3, OFAC
- *Van Loon v. Treasury* (5th Cir., 26 Nov 2024): immutable smart contracts are not "property" under IEEPA [V] — annex B §3, Van Loon v. Treasury (5th Cir.)
- OFAC delisted Tornado Cash on 21 March 2025 [V] — annex B §3, OFAC recent action 20250321
- Roman Storm was convicted on 6 August 2025 of conspiracy to operate an unlicensed money-transmitting business (§1960), maximum 5 years [V] — annex B §3, USAO-SDNY; the other counts were a hung jury per DOJ and Decrypt [L], and one outlet called the sanctions count an acquittal [U] — annex B §3
- Storm's acquittal motion was argued on 9 April 2026 and is undecided; retrial is set for 26 April 2027 [V] — annex B §3, USAO-SDNY
- DOJ policy (21 Aug 2025): no new §1960(b)(1)(C) charges against a third party where the software is "truly decentralized", only automates peer-to-peer transactions, and nobody has custody of user funds [V] — annex B §3, DOJ
- Samourai Wallet founders were sentenced to 5 and 4 years in November 2025 [L] — annex B §3, USAO-SDNY
- EU AMLR (Regulation 2024/1624) Article 79(1): credit institutions, financial institutions and crypto-asset service providers may not keep anonymous crypto-asset accounts, or accounts allowing anonymisation or increased obfuscation, including through anonymity-enhancing coins [V] — annex B §3, AMLR Art. 79; it applies from 10 July 2027 [L] — annex B §3
- Compliance designs: association sets let a user prove membership in a "good" set without revealing which deposit is theirs [L]; the ASP publishes roots plus an IPFS hash on-chain, and ragequit remains as a public exit [V] — annex B §3, Privacy Pools docs

## 17. How to cite

- Sibling documents cite a fact as 'evidence register §N' together with its mark ([V], [L] or [U]), for example: "new Stylus activations are paused (evidence register §1, [V])".
- Any claim that is not in this register is labeled UNVERIFIED where it appears.
- A [U] or [L] fact must not be presented as settled; a [L/V] or [V/L] fact keeps its compound mark.
- §1–§8 are a snapshot of 2026-10-12. The §1 fee snapshot (Arbiscan) is dated 2026-10-13 although retrieval was recorded as 2026-10-12, so it may be used only when labeled as a dated snapshot ("Arbiscan, 2026-10-13").
- §9–§13 were retrieved 2026-10-13. They are cited as 'evidence register §N' with their marks like every other section.
- The 2025–26 networked-speculative-decoding preprints in §9 carry both marks inline: [V] for what the preprint says, [U] because the result is not independently replicated. A document citing them carries both marks and the [U] stays; no document may cite them as [V] alone or upgrade them. The cited claim is "no WAN speed-up is promised", never "no speed-up exists".
- The llama.cpp RPC backend facts ('proof-of-concept', 'fragile and insecure', never on an open network) are §10, not §9; a citation to them must say §10.
- §14–§16 were added 2026-10-13, compiled from two screened research annexes (annex A: private inference; annex B: anonymous payments and relays). They are cited as 'evidence register §N' with the mark the annex gives. The older §4 FHE/MPC/TEE bullets remain a dated 2026-10-12 snapshot with different figures; a document citing current figures cites §14.
- A [U] figure in §14–§16 (including "(calc)" arithmetic and the researchers' own estimates and takeaways) must not be upgraded to [L] or [V] by any document; a fact that annex A and annex B mark differently (Whisper Leak) is cited with the mark of the entry actually used.
- The Semaphore-32 proving times (143–2,146 ms [V]) and the about 230–270k L2 gas estimate for `validateProof` [U] describe Semaphore's own circuit and contract function, not any Comuns circuit or contract. A Comuns figure built on them is UNVERIFIED until measured. Semaphore audits ("v4.0.0 audited by PSE; v3 audited by Veridise") do not transfer to any Comuns contract.
- The legal and regulatory items in §16 are facts as reported, not legal advice; no document may present them as legal advice or as a legal conclusion about Comuns.
- Adding or changing a fact requires a pull request to this file that states the source and the mark; reviewers check the source before merge.
