# Arbitrum Sepolia deployment record (testnet-only, non-normative)

Author: Comuns contributors
Status: Draft
Category: Record
Created: 2026-10-15
**Reference:** [docs/cip/0004-sepolia-testnet-configuration.md](../cip/0004-sepolia-testnet-configuration.md)

---

Nothing is deployed: every row below reads `not yet deployed`, and every value later written here is testnet-only and non-normative. This record holds observations of the Arbitrum Sepolia deployment made under [CIP-0004](../cip/0004-sepolia-testnet-configuration.md) after that CIP is Final. It sets no value, it is not a revision of CIP-0004, and nothing in it may be copied as a mainnet value or default. The seated maintainer fills it by an ordinary pull request.

The record is append-only. A redeployment adds new rows with their own date and never overwrites or deletes an earlier row. The model's manifest, `manifestHash`, license identifier and the sentence the registrant read are filled in CIP-0004's Model to register item before Last Call; that item is open in this draft, so they are not here. This record holds on-chain observations, operator settings, the contracts commit and the Semaphore artifact hashes the deployer computed before deployment, because per-file hashes were not found in the sources examined on 2026-10-15 [U] and the artifact repository is archived [V] (evidence register §15, recheck 2026-10-15; CIP-0004 Verifier item). The deployer pins the Semaphore release only after CIP-0005's pins row records one. The first three Semaphore rows hold pre-deployment results and the fourth the post-deployment check made before use. Locally computed hashes identify bytes and do not establish ceremony soundness (RR-41).

| Item | Value | Recorded on |
|---|---|---|
| Chain id (UNVERIFIED until read from the connected network) | not yet deployed | not yet deployed |
| Deployer address | not yet deployed | not yet deployed |
| Governance key address | not yet deployed | not yet deployed |
| Contracts commit | not yet deployed | not yet deployed |
| `SessionEscrow` address | not yet deployed | not yet deployed |
| `NodeRegistry` address | not yet deployed | not yet deployed |
| `ModelRegistry` address | not yet deployed | not yet deployed |
| `ContextRegistry` address | not yet deployed | not yet deployed |
| Semaphore verifier address | not yet deployed | not yet deployed |
| Pre-deployment: Semaphore release tag, @zk-kit/semaphore-artifacts version with its verified npm tarball shasum, and the pinned circuit and compiler inputs | not yet deployed | not yet deployed |
| Pre-deployment: SHA-256 of SemaphoreVerifier.sol and SemaphoreVerifierKeyPts.sol at the pinned tag, and of each vendored artifact file (semaphore-{depth}.wasm, .zkey, .json) for every accepted depth, with where the pinned copy is hosted | not yet deployed | not yet deployed |
| Pre-deployment: result of comparing each exported zkey verification key with the artifact JSON, the proof package's verification keys and the verifier's packed key points, and of the circuit/zkey check against the ptau (a missing input or a check that cannot run blocks deployment) | not yet deployed | not yet deployed |
| Post-deployment, before use: result of comparing the deployed verifier bytecode with the pinned build | not yet deployed | not yet deployed |
| `modelId` | not yet deployed | not yet deployed |
| Node operator address | not yet deployed | not yet deployed |
| Relay operator address | not yet deployed | not yet deployed |
| `benchmarkHash` | not yet deployed | not yet deployed |
| `modelBenchmarkHash` | not yet deployed | not yet deployed |
| `paddingBuckets` as configured by the node operator | not yet deployed | not yet deployed |
| `tokenBatch` as configured by the node operator | not yet deployed | not yet deployed |
| Transaction hash of `setBands(T0, …)` | not yet deployed | not yet deployed |
| Transaction hash of `setCreditParameters` (index 0) | not yet deployed | not yet deployed |
| Transaction hash of `setCreditParameters` (index 1) | not yet deployed | not yet deployed |
| Transaction hash of `setCreditParameters` (index 2) | not yet deployed | not yet deployed |
| Transaction hash of `registerModel` | not yet deployed | not yet deployed |
