# S7: EIP-712 conformance (viem vs alloy)

TEST domain (labelled test values): name "SessionEscrow", version "1", chainId 421614, verifyingContract 0x000000000000000000000000000000000000dEaD. TEST key = publicly known anvil key #0 (signer 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266). Files: viem/run.mjs, alloy/src/main.rs (sol!), alloy/src/bin/dynabi.rs (dyn-abi), alloy-min/ (minimal-feature build). Raw outputs: viem-out.json, alloy-sol-out.txt, alloy-dyn-out.txt, alloy-min-out.txt. All commands in log.txt.

Vouchers: V1 = seq 1, cumulativeWei 1e15, in 128, out 256, commitment 0x00..00, final=false. V2 = seq 42, cumulativeWei 123456789012345678901234567890, in 4096, out 8192, commitment 0xcd*32, final=true. V3 = seq/in/out = max uint64, cumulativeWei = max uint256, commitment 0x01*32, final=true. sessionIds 0x11*32, 0xab*32, 0xff*32.

## Results
| Check | Result | Measured value | Evidence |
|---|---|---|---|
| viem hashTypedData + signTypedData + recoverTypedDataAddress (3 vouchers) | PASS | recovered == 0xf39F...2266 for all 3 | log.txt "recoveredMatches": true x3 |
| alloy `sol!` struct, as literally specified (field `bool final`) | FAIL | Rust rejects `final` (reserved keyword): "expected identifier, found reserved keyword `final`" | log.txt line ~100 |
| alloy `sol!` with `bool r#final` | FAIL (hash mismatch) | encodeType contains `bool r#final`; typeHash 0xcbfb75fc...02e0 != viem 0x8611af2f...dd96; structHash, signingHash, signature all differ for all 3 vouchers. Domain separator matches. | alloy-sol-out.txt; log.txt "r#final" |
| `#[sol(rename = "final")]` workaround | FAIL | rename is UNIMPLEMENTED in alloy-sol-macro-input 1.7.3 (attr.rs:100 doc comment); compile error on field attribute | log.txt "fix2" |
| alloy dyn-abi `TypedData` (JSON types, field named "final") vs viem | PASS | typeHash, domainSeparator, structHash, signingHash and signature all identical, V1-V3 (byte for byte) | alloy-dyn-out.txt vs viem-out.json |
| Domain separator viem vs alloy (sol! and dyn) | PASS | 0x0919c99458ded79404eb9b887a4971d2bf9e493dcdd1fd9ab26116e66f767ef1 | all outputs |
| Signatures deterministic, same across impls (dyn path) | PASS | see table below | |
| forge/Solidity third path | NOT RUN | forge would download solc (none cached in ~/.svm; not in approved downloads) | log.txt note |

### Values (viem == alloy dyn-abi; type hash and domain separator common)
- typeString: `Voucher(bytes32 sessionId,uint64 seq,uint256 cumulativeWei,uint64 inputTokens,uint64 outputTokens,bytes32 outputCommitment,bool final)`
- typeHash: 0x8611af2f59eba3c07185bdfaa04289f9baad0b61f4d8c96a950d393db45fdd96
- domainSeparator: 0x0919c99458ded79404eb9b887a4971d2bf9e493dcdd1fd9ab26116e66f767ef1

| V | structHash | signingHash | signature (r||s||v) |
|---|---|---|---|
| 1 | 0x018f50c547a39cb4f157bdc42a6a14b6d63445c559ea8bc37872b21f6549efe8 | 0xdd0bb382df4dcee52df022543b00ec9eac6e74c3052a961745e4355461e05afd | 0x67b882f22b2cc7a1b038e0e0f2f579e12ba75b0d5c1cbcdc3916cdc790f6383e13bd55f3f4d4dd883ccafd8ebd67eeaa64a082fd61d9fbb160a403a3327f66701c |
| 2 | 0x5e3bca8aea480632fbe318b75066e7e1d9394ece554ebb8f300a7aa4fc6e9236 | 0x924da95b5a7d7862f192f74cf3e256c935e875eb87c300dd989e1daf2b045d48 | 0x410765badd1a7aba7f21bb4bec4f5de28da61042e927ed6dabe03eb690bd29bc27af8b5c5ef32fd0d6e8d0528530494a0b4b9edcd879d8f8b03ebf4a1d0e46271b |
| 3 | 0xdba51416a9fce5ec21e45d07f6017288df1b80dccdf84a622f19451475a3ba96 | 0x5085ae3724a67215d2678081759223dc2949e48d3ade17cc1da90e2360045ba4 | 0xf9bd7c35a6c2c4d8098b737cc08434614b0d7e587caf7628e489daa1058093645d9165d9f9ac9b3da6ce49a298ce0701363e980646ac5d496284d6e1aa59a1da1b |

alloy `sol!` with `r#final` (non-matching, for the record): typeHash 0xcbfb75fc33241dbd4b765fd2b41a2cb3ab2aaa3ba7490323267038144eb302e0; V1 structHash 0x069a34a9...fe30, signingHash 0x55d3d16d...2530.

## Exact versions resolved
- Node v24.22.0; viem 2.57.7 (`npm ls viem`, installed with --ignore-scripts, 13 packages, 0 vulnerabilities).
- Rust toolchain 1.99.1. alloy 2.5.0, alloy-core 1.7.3, alloy-sol-types 1.7.3, alloy-primitives 1.7.3, alloy-signer 2.5.0, alloy-signer-local 2.5.0, alloy-dyn-abi 1.7.3 (dyn build only), serde_json 1.0.154 (dyn bin only). Full list in alloy-min/Cargo.lock and alloy/Cargo.lock.
- Minimal alloy features (default-features = false): for sol! hashing + local signing: `["sol-types", "signer-local"]` (verified building and producing the sol! output; alloy-min output identical to the full build). For the dyn-abi TypedData path add `"dyn-abi", "eip712", "serde"` (plus a serde_json dep). I did not individually prove each of those three is required; this is the set that built.
- Build time (release, registry sources already cached, Apple silicon): alloy-min (sol-types + signer-local) 15.4 s; first cold compile attempt of the same deps ~56 s (log.txt, failed at the last crate on the `final` error, so deps compiled); dyn build 42 s (some crate downloads included).

## Findings that affect a pin
1. **The field name `final` cannot be used in alloy's `sol!`** (Rust reserved keyword). The escape `r#final` is carried into the EIP-712 type string, producing a different typeHash and therefore different struct hashes and signatures from viem. `#[sol(rename)]` is unimplemented. So a Rust node cannot use `sol!` with the canonical type as written in contracts-and-settlement.md :249.
2. Working options for the Rust side: use alloy dyn-abi `TypedData` (matches viem exactly, as measured), or rename the field in the canonical type (for example `isFinal`) everywhere (document, viem, alloy, contract). The pin should choose one. I did not test other options (e.g. a manual `SolStruct` impl).
3. I believe `final` is also a reserved keyword in Solidity, which would break an on-chain `struct Voucher` with a field named `final`. NOT verified: the forge path was not run (needs a solc download). Recommend verifying with forge before the pin is frozen; if true, the field must be renamed regardless.
4. viem and alloy agree on domain separator; viem and alloy dyn-abi agree on all hashes and RFC 6979 signatures, with v encoded as 27/28 (0x1b/0x1c) in both.
5. viem API notes: `hashDomain`/`hashStruct` are exported from the `viem` root; `signTypedData` from `viem/accounts`.

## Residuals / not verified
- Solidity/forge third path not run (see above); the Solidity reserved-keyword claim is unverified.
- Only 3 vouchers tested; no negative tests (wrong domain, tampered field).
- Feature minimality for the dyn path not individually bisected.
- No text addressed to an AI was encountered in fetched content.
