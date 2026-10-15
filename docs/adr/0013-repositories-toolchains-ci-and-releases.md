# ADR 0013: Repositories, toolchains, CI, DCO enforcement, code style and releases up to testnet

**Status:** proposed

**Date:** 2026-10-15

**Deciders:** none seated; adoption is proposed in [CIP-0005](../cip/0005-phase-one-implementation.md)

## Context

No protocol code exists. The Comuns-ai/documentation repository contains documents, documentation checkers in `scripts/` and a GitHub Actions workflow that currently runs only `check-deck.py`. Neither the other documentation checks nor DCO trailers are checked in CI. [CONTRIBUTING.md](../../CONTRIBUTING.md) section 6 requires the CIP that adds code to state its style.

[Node design](../node/node-design.md) section 11 suggests crates in prose, without creating a workspace. The [dapp and SDK proposal](../product/dapp-and-sdk.md) leaves its package name undecided. [Project plan](../project-plan.md) section 11 requires versions to be pinned only in the implementation proposal. A repository boundary, toolchain policy and ordered release gates are needed before the Phase 1 implementation begins. This record proposes those decisions; it does not adopt itself or create protocol code.

## Decision

### 1. Repositories

The documentation repository remains the home of documents, checkers and documentation workflows. One code repository is proposed under the Comuns-ai organization, named `comuns`: `Comuns-ai/comuns`. Name availability is **UNVERIFIED**. This PR does not create it.

Its proposed top-level layout is:

| Directory | Responsibility |
|---|---|
| `contracts/` | Foundry project with `src/`, `test/` and `script/` for the contracts, tests and deployment scripts. |
| `node/` | One Cargo workspace with the `binary`, `chain`, `crypto`, `runtime`, `http`, `meter` and `context` crates of node-design section 11, plus `relay`. It builds two executables: the node and the relay. The node remains one process hosting the gateway; the relay is a separate process. The `context` crate is unused in Phase 1. |
| `client/` | TypeScript SDK and reference client. The package name remains undecided under dapp-and-sdk OQ4. |
| `conformance/` | Shared test vectors and the identifier list consumed by contracts, Rust and TypeScript tests. The contracts document remains the source against which that list is checked. |
| `deployments/` | Mirrors `docs/deployments/` in the documentation repository, with references to the corresponding deployment records. |

### 2. Toolchains

Use Foundry (`forge`, `cast`, `anvil`) for contracts. Use Rust stable with `cargo fmt` and clippy with warnings denied (`cargo clippy -- -D warnings`). The first inference adapter is llama.cpp through Rust bindings, as proposed in [ADR 0002](0002-off-chain-rust-inference.md). Use TypeScript with strict `tsc`, eslint and prettier, a supported Node LTS and pnpm. Use the `hpke` crate for HPKE in the node and a WASM build of the same implementation for the SDK.

This ADR pins no version. Exact toolchain and dependency versions are recorded only in CIP-0005 after its rechecks; lockfiles are required in the code repository and floating `latest` selections are forbidden. The evidence-register snapshots `hpke` 0.14.1 (evidence register §4 [V]) and mistral.rs 0.9.4 (evidence register §3 [V]) are recheck inputs, **not pins** or claims of current suitability.

### 3. Continuous integration

Use GitHub Actions. The documentation CI addition in this PR is `.github/workflows/docs-checks.yml`, running `scripts/check-docs.py`, `scripts/check-pricing.py`, `scripts/check-deck.py` and `scripts/check-dco.py`. The DCO check uses the pull request's base-to-head commit range. This workflow is documentation infrastructure, not a protocol implementation.

The code repository's CI is specified here, not created by this PR. It must run:

- Lint and build checks for every component, including the formatters and warnings policy below, `cargo test`, and TypeScript type, lint and test checks.
- Foundry tests covering the [contracts document](../protocol/contracts-and-settlement.md) section 13: unit tests for preconditions, effects and events; reentrancy and pull payments; randomized conservation and settlement invariants; input and output band boundaries; EIP-712 conformance using an independent off-chain library; and the credit, relay and context test list. The absence of a Phase 1 context UI does not waive the contract tests.
- A conformance job that fails if any of the 23 function names, their signatures, event names or field layouts, or the canonical voucher type string drifts from the contracts document and [ADR 0011](0011-anonymous-credits.md). The shared identifier list must not become an unchecked second authority. Enum values and the payment rule are also checked against the document.
- Cryptographic vectors shared by the reference client and node, independent OHTTP interoperability, negative cases, parser/state-machine fuzzing and disclosure-sheet conformance under [privacy and contexts](../security/privacy-and-contexts.md) section 12. Later-mode tests remain gates on their respective modes.
- Relay-authentication and key-probe negative cases under [ADR 0014](0014-relay-authentication-to-gateways.md), [ADR 0015](0015-node-key-possession.md) and CIP-0005, including a challenge relayed from another gateway, a wrong domain deployment, a probe rewrapped into another OHTTP request and a substituted receipt key.

Pin workflow actions by commit SHA and grant minimum permissions. The documentation checks use read-only permissions. Untrusted pull requests receive no deployment secrets. These conformance checks are release gates; a passing document checker is not evidence that the protocol passes them.

### 4. DCO enforcement

`scripts/check-dco.py` fails a pull request when **any commit in `base..head`, including a merge commit**, lacks a `Signed-off-by` trailer. It must not exclude merges. An unsigned merge within the range is a required failing test. The merge commit the host creates when the pull request is merged lies outside that pull request's range and is not checked by it.

The seven earlier commits are outside the new PR range by construction. [CIP-0003](../cip/0003-bootstrap-first-maintainer-and-channels.md) lists all seven, including the three host-generated merges for completeness, and records the author's DCO certification of the four authored commits. It is not a blanket exemption for later merges or authored commits. Every authored commit from this PR onward requires its own trailer.

After CIP-0003 is Final, the seated maintainer configures branch protection to require the checks. No branch protection is claimed configured. Whether squash or rebase merging will ensure every default-branch commit carries a trailer remains open; host behaviour is **UNVERIFIED**.

### 5. Code style and notices

Solidity uses `forge fmt`, NatSpec on external functions, and `// SPDX-License-Identifier: Apache-2.0` as the first line. Rust uses rustfmt defaults, checked with `cargo fmt`, and clippy with warnings denied. TypeScript uses prettier defaults, eslint and strict `tsc`. No other per-file header is required. The code repository carries the Apache-2.0 `LICENSE` and the [GOVERNANCE.md](../../GOVERNANCE.md) notice lines in its README: "Copyright 2026 Comuns contributors" and "Licensed under the Apache License, Version 2.0 (see LICENSE)". Vendored code retains upstream notices and terms, as [ADR 0006](0006-apache-2-0-and-dco.md) requires.

### 6. Release process up to testnet

Proceed in this order; each gate needs a public record before the next step:

1. CIP-0003 becomes Final and `MAINTAINERS.md` is updated.
2. The seated maintainer enables GitHub private vulnerability reporting on the relevant Comuns-ai repositories and records that action and monitoring responsibility. This is an unmet gate; this document does not claim the setting is enabled.
3. [CIP-0002](../cip/0002-anonymous-credits-relays-and-ownerless-contexts.md) becomes Final through its own process.
4. CIP-0005 becomes Final with every pre-code decision complete and its five pre-code rechecks written up as evidence.
5. The code is built and tested, including the conformance and negative-test gates.
6. [CIP-0004](../cip/0004-sepolia-testnet-configuration.md) becomes Final. It requires CIP-0002, CIP-0003 and CIP-0005; CIP-0005 does not require CIP-0004. The exact model registration item must already have been completed in CIP-0004 before its Last Call.
7. The seated maintainer deploys from the disposable testnet key and runs the setters immediately after CIP-0004 is Final. All testnet values come from CIP-0004 and are testnet-only, non-normative. On Arbitrum Sepolia, GOVERNANCE.md section 7.1 applies; mainnet is unchanged.
8. Fill `docs/deployments/arbitrum-sepolia.md` with the deployment observations and evidence, and mirror the record in the code repository.
9. Tag a `v0.y.z` testnet pre-release in the code repository, identifying the source commit and supplying lockfiles and checksums. Phase 1 releases contain source, not binaries.
10. A person other than the implementation author completes and records the Phase 1 exit walkthrough from project-plan: the distinct-operator relay session, deposit, node-submitted credit open, checked receipts and vouchers, cooperative close, node withdrawal, smaller change note plus dust, zero-use full return, ragequit, recovery and a simulated delayed-inbox submission.

[GOVERNANCE.md](../../GOVERNANCE.md) section 8 may hold publication of a release. Completing these testnet steps supplies no mainnet authorization; mainnet requires its own later gates and unchanged governance rules.

### 7. The implementation CIP

CIP-0005 carries all deferred implementation decisions in its completion matrix: trait names, memory-fit coefficients, receipt-key wire details, chain-client library, accepted `merkleTreeDepth` range, operations and gas limits, session-store settlement finality, SDK wallet and WASM HPKE/prover distribution, padding buckets, token batching, `sessionId` derivation, ERC-1271 relay operators, and exact toolchain and dependency pins. It proposes the Q19 initialized-bit resolution without an ABI change and adopts the relay-authentication and key-possession records only upon becoming Final.

Its pre-code rechecks cover the Stylus pause and EVM target, chunked OHTTP, Semaphore ceremony/circuit/verifier artifacts and licenses, model and dependency licenses, and the RFC 7748, RFC 9180 and RFC 9458 readings used by ADRs 0014 and 0015. Each requires primary-source evidence. No unresolved pre-code item may be treated as permission to start implementation; conformance results remain later release gates.

## Alternatives considered

- **Protocol code in the documentation repository:** rejected because it mixes the specification and adoption record with implementation tooling and releases.
- **Three or four code repositories before the first slice:** deferred. The proposed bootstrap has one maintainer, and shared identifier tests favour one code repository. A later CIP may split it when there is a concrete need.
- **Hardhat:** rejected for this slice because the contracts document already specifies Foundry tests; introducing another contract toolchain adds no required capability here.
- **A third-party DCO application:** rejected because an in-repository range checker has no external service dependency and makes its policy reviewable with the documents.
- **Version pins in this ADR:** rejected because project-plan section 11 puts them in the implementation proposal after rechecking the evidence snapshots.

## Consequences

The only executable scope of this documentation PR is the documentation CI workflow and its DCO checker; it adds no protocol implementation. The proposed code repository, node and relay binaries, and required branch protection do not exist yet. This ADR creates none of them.

One code repository permits coordinated changes and shared conformance vectors while keeping adoption in the documentation repository. Its shared identifier list and mirrored deployment records require drift checks. CI gates and a one-person bootstrap do not substitute for independent review. Unfilled CIP-0005 decisions block Final, and failed implementation gates block release.

## Links

- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [GOVERNANCE.md](../../GOVERNANCE.md)
- [SECURITY.md](../../SECURITY.md)
- [Node design](../node/node-design.md)
- [Dapp and SDK](../product/dapp-and-sdk.md)
- [Contracts and settlement](../protocol/contracts-and-settlement.md)
- [Project plan](../project-plan.md)
- [Risk register](../risk-register.md)
- [ADR 0002](0002-off-chain-rust-inference.md)
- [ADR 0006](0006-apache-2-0-and-dco.md)
- [CIP-0005](../cip/0005-phase-one-implementation.md)
- Documentation CI workflow: `.github/workflows/docs-checks.yml`
