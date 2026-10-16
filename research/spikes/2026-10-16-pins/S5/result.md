# S5 + S6: Foundry/solc/cancun with Semaphore contracts, and Semaphore artifacts and proof
All work is in `$SR/S5/`. Every command and its output is in `$SR/S5/log.txt` (command lines start with `$ (cd ...)`). The one exception is the `forge build --sizes` and `forge inspect` runs of step 6, whose first attempt failed on a remapping error. That failure is also in the log, followed by the successful reruns.

## Results

| Check | Result | Measured value | Evidence (log.txt grep string) |
|---|---|---|---|
| S5.1 forge init (`--no-git --offline`) | PASS | `forge Version: 1.8.5`, commit `51a52c59cffd940f76eddd0b4bb1791aa4b5ac7f`, build 2026-10-05, profile dist | `Initialized forge project`, `Commit SHA: 51a52c59` |
| S5.2 default `evm_version` with no `evm_version` and no `solc_version` | PASS (answer: **osaka**) | `forge config` printed `evm_version = "osaka"` and `"solc": null`, `"auto_detect_solc": true`. Defaults also showed `optimizer = false` and `optimizer_runs = 200`. This settles the conflict in favour of source-says-Osaka: forge 1.8.5 defaults to osaka, not prague. | `21:evm_version = "osaka"`, `"evm_version": "osaka"` |
| S5.3a explicit settings: solc 0.8.37, cancun, optimizer on | PASS | `forge config` reported `evm_version = "cancun"`, `solc = "0.8.37"`, `optimizer = true`, **`optimizer_runs = 200`** (forge default, not set by me). | `21:evm_version = "cancun"`, `25:solc = "0.8.37"`, `29:optimizer_runs = 200` |
| S5.3b minimal contract using `block.timestamp` and `block.chainid` | PASS | `Compiling 1 files with Solc 0.8.37`, `Compiler run successful!`. Mini runtime is 121 B and initcode 147 B. | `Solc 0.8.37 finished`, `\| Mini ` |
| S5.3c add `@semaphore-protocol/contracts@4.14.3` and compile Semaphore.sol and SemaphoreVerifier.sol, cancun | PASS | `Compiling 13 files with Solc 0.8.37`, `Compiler run successful!`. Installed with `npm install --ignore-scripts --save-exact` into `deps/sem`. It pulled in `@zk-kit/lean-imt.sol@2.0.1` and `poseidon-solidity`. Upstream pragma is `>=0.8.23 <0.9.0`. The CBOR metadata in both runtime bytecodes ends `...64736f6c63430008250033`, so solc 0.8.37 was used. | `Compiling 13 files with Solc 0.8.37`, `Compiler run successful!`, and the `706673582212...64736f6c63430008250033` metadata tails printed by `cmp.js` |
| S5.3d sizes, any contract over 24576 B | PASS (none over) | Runtime: Semaphore **7,934 B**, SemaphoreVerifier **15,856 B**, PoseidonT3 16,466 B, Mini 121 B. Initcode: Semaphore 8,069 B, SemaphoreVerifier 30,413 B, PoseidonT3 16,518 B. Smallest runtime margin is the verifier's 8,720 B. SemaphoreVerifier's initcode (30,413 B) exceeds 24,576 B but is under the 49,152 B initcode limit (EIP-3860) and the table shows margin 18,739 B. | `\| SemaphoreVerifier \| 15,856 \| 30,413 \| 8,720 \| 18,739` |
| S5.3e cancun vs osaka, Semaphore verifier runtime bytecode | PASS (behaviourally identical) | Raw bytecode is **not byte-identical**. The `cmp` of the `forge inspect` hex outputs and the raw-bytecode comparison in `cmp.js` both report `full identical false`. The only difference is the trailing CBOR metadata hash, which covers the settings including evm_version. With the 53-byte metadata stripped the code is **identical: 0 differing bytes of 15,803** (verifier) and of 7,881 (Semaphore). Size difference is **0 B** (15,856 vs 15,856 and 7,934 vs 7,934). The `forge build --sizes` tables are identical for the two profiles. | `full identical false \| metadata-stripped cancun 15803 osaka 15803 stripped identical true differing bytes 0`, `metadata cancun ...1d855b...`, `metadata osaka  ...ad2fa6...` |
| S5.4 upstream v4.14.3 compiler settings | PASS | `packages/contracts/hardhat.config.ts`: `solidity: { version: "0.8.23", settings: { optimizer: { enabled: true, runs: 200 } } }`. **No `evmVersion` is set** and no metadata, viaIR or bytecodeHash settings. The hardhat network sets `chainId: 1337` and `allowUnlimitedContractSize: true`. `foundry.toml` returned HTTP 404 both at `packages/contracts/` and at the repo root. | `version: "0.8.23"`, `runs: 200`, `foundry.toml http=404`, `root foundry.toml http=404` |
| S6.1 tarball `npm pack @zk-kit/semaphore-artifacts@4.13.0`, sha1 | PASS | sha1 `efe54e9ae463f748198f3d769f846224310caad9`, equal to the expected value and to `npm view dist.shasum`. Tarball is 109,100,273 B. | `efe54e9ae463f748198f3d769f846224310caad9  zk-kit-semaphore-artifacts-4.13.0.tgz`, `dist.shasum = 'efe54e9ae` |
| S6.1 sha512 integrity | PASS | `sha512-UgFQkcwI63XT1Xk8fkUYMNfcuR85LiSL3Of9XLsyMLflHkiwXP9D1WC8hnpD8Tp2HoAMJ/mCv7ZMlU7TC0mvdQ==`. It matches `npm view dist.integrity`. | `sha512-UgFQkcwI63` |
| S6.2 file count, sizes, SHA-256 | PASS | **100 files**: 96 artifact files (3 per depth, depths 1 to 32) plus CHANGELOG.md, LICENSE, README.md, package.json. Unpacked total **170,928,598 B** (about 163 MiB; `du` 167,084 KiB). SHA-256 of all 100 files is in `$SR/S5/artifacts-sha256.txt` (100 lines). Per-depth sizes are in the table below. | `entryCount": 100`, `total_bytes=170928598`, `wc -l artifacts-sha256.txt` shows 100 |
| S6.3 proof at depth 1 with local wasm and zkey, then verifyProof | PASS | `verifyProof` returned `true`. `generateProof` took **217 ms**, `verifyProof` 7 ms. Peak RSS **353,026,048 B (about 337 MiB)** from `/usr/bin/time -l`. A tampered message verified `false` (negative control). 0 network attempts. | `depth 1`, `generateProof_ms 217`, `verify_result true`, `353026048  maximum resident set size` |
| S6.3 proof at depth 32 | PASS | `verifyProof` returned `true`. `generateProof` took **458 ms**, `verifyProof` 8 ms. Peak RSS **661,635,072 B (about 631 MiB)**. Tampered message verified `false`. 0 network attempts. | `depth 32`, `generateProof_ms 458`, `verify_result true`, `661635072  maximum resident set size` |
| S6.3 no network download | PASS, with a caveat | Local `{wasm, zkey}` paths were passed, so the library's default download branch (`snarkArtifacts ?? maybeGetSnarkArtifacts`) was never entered. As a tripwire, `prove.js` replaced `fetch`, `http.request/get`, `https.request/get` and `net.connect` with blockers. `network_attempts 0` was printed in both runs. The tripwire itself was not tested with a deliberately network-using call. | `network_attempts 0` (two occurrences) |

### Per-depth artifact sizes (bytes, from the unpacked tarball)

| Depth | wasm | zkey | json (verification key) |
|---|---|---|---|
| 1 | 1,798,638 | 1,552,601 | 3,746 |
| 8 | 1,811,974 | 2,231,251 | 3,741 |
| 16 | 1,843,806 | 3,408,199 | 3,744 |
| 32 | 1,859,813 | 5,850,470 | 3,746 |
| Package total, depths 1 to 32 plus 4 meta files (100 files) | | | 170,928,598 |

## Exact versions resolved
- forge 1.8.5 (commit 51a52c59cffd940f76eddd0b4bb1791aa4b5ac7f). Solc used: 0.8.37, via forge's `solc_version`. The solc binary was fetched automatically by forge.
- Node v24.22.0.
- `@semaphore-protocol/contracts` 4.14.3, `@zk-kit/lean-imt.sol` 2.0.1, `poseidon-solidity` (version not read; installed as a transitive dependency).
- `@semaphore-protocol/core` 4.14.3, `@semaphore-protocol/proof` 4.14.3, `@semaphore-protocol/group` and `identity` 4.14.3, `@semaphore-protocol/utils` 4.14.3.
- **snarkjs 0.7.5** (the one used by `@semaphore-protocol/proof`). `@types/snarkjs` pulls an extra `snarkjs@0.5.0` as a type-only dependency.
- `@zk-kit/artifacts@2.0.1`, `@zk-kit/lean-imt@2.2.5`, `@zk-kit/utils` 1.2.1, 1.3.0 and 1.4.1.
- `@zk-kit/semaphore-artifacts@4.13.0` (tarball verified).
- `npm ls` shows 173 packages added for the proof project, and `npm install` reported 14 vulnerabilities (5 moderate, 9 high). I did not investigate them.

## Findings that affect a pin
1. **Foundry's default `evm_version` is `osaka` in 1.8.5**, so the pins must set `evm_version = "cancun"` explicitly. `forge config` showed that no setting means osaka.
2. **The default `optimizer` is false.** Pinning `optimizer = true` leaves `optimizer_runs` at 200, which equals upstream's 200. The runs value is therefore not a deviation, but it is implicit unless pinned.
3. **Upstream compiles with solc 0.8.23 and no `evmVersion`**, while this spike uses 0.8.37 with cancun. The 0.8.37 plus cancun build still compiles `Semaphore.sol` and `SemaphoreVerifier.sol`. It is a different compiler from the one upstream's config uses, so its bytecode is presumably not the upstream release bytecode. I did not compile with 0.8.23 or compare, and I did not check which compiler any audit covered.
4. **cancun vs osaka makes no code difference for these contracts** (0 differing bytes, 0 B size difference), only the metadata hash differs. If the evidence register compares deployed bytecode hashes, it must strip the CBOR metadata or pin the settings exactly.
5. Semaphore.sol (7,934 B) and SemaphoreVerifier.sol (15,856 B) are within the 24,576 B runtime limit. The verifier's initcode is 30,413 B, which is under the 49,152 B initcode limit but needs a chain that does not cap initcode below that. I did not test Arbitrum limits.
6. **Foundry remapping gotcha:** a remapping `@zk-kit/lean-imt.sol/=...` mangled the path to `lean-imt.solInternalLeanIMT.sol` and the compile failed. Remapping `@zk-kit/=.../@zk-kit/` works. This needs `allow_paths` when the dependencies sit outside the project.
7. **The proof library's default artifact version is `4.13.0`** (hard-coded in `generateProof`), the same version as the pinned tarball. The `verifyProof` verification keys are embedded in the library for depths 1 to 32, so verification needs no download. The default path downloads from the network only when no `snarkArtifacts` are passed.
8. The artifact tarball is 109 MB packed and 171 MB unpacked, because it ships all 32 depths. A deployment that needs only one depth would have to extract the files it uses.
9. Proof timings are small on this machine (217 ms and 458 ms), but depth 32 peaked at about 631 MiB RSS. That figure matters for a memory-limited client.

## Residuals / not verified
- Proof on-chain verification (calling `SemaphoreVerifier` with this proof) was not done; only the JS `verifyProof` was run.
- I did not compile with solc 0.8.23 to compare with upstream bytecode.
- Depths other than 1 and 32 (for example 8 and 16) were not proved; only their file sizes were recorded.
- The network tripwire was not positively tested, and the log contains no OS-level network trace. "No network" rests on the local paths being passed and `network_attempts 0`.
- The `poseidon-solidity` version was not recorded. Timings are from one run each, on one machine, with no warm-up statistics.
- The README of the artifacts package (341 B) contained only links to circuits and the proof library, with no text addressed to an AI. Nothing addressed to an AI was seen in the other fetched content (the upstream hardhat config, npm output).
- Scratch files: `foundry.toml` has an extra `[profile.osaka]` for the comparison. `target`-like directories `contracts/out`, `contracts/out-osaka`, `contracts/cache*`, `deps/` (about 280 MB), and `proof/node_modules` are in `$SR/S5/` for the orchestrator to delete. I also left small helper files (`run.sh`, `step*.sh`, `cmp.js`, `*.hex`).
