# ADR 0006: License the work Apache-2.0 and use the DCO

**Status:** proposed

**Date:** 2026-10-12

**Deciders:** none seated; adoption is the subject of docs/cip/0001-adopt-baseline-adrs.md

## Context

Comuns publishes design documents now and intends to publish code later. Contributors need one license for that work, and a way to certify that they have the right to submit it. The project has no seated maintainers and no legal department. This record is not legal advice.

Model weights are not this repository. Families in the evidence register ship under Apache-2.0, MIT, and bespoke terms that sometimes forbid commercial hosting or that set user-count thresholds (evidence register §7). The software license must not be read as a license to those weights.

The Ethereum process this project's CIP lifecycle follows is off-chain and uses no coin vote (evidence register §8, [V]). Licensing is the same kind of written decision. It is not a holding.

## Decision

Code and documentation in Comuns are licensed under the Apache License, Version 2.0. The license text belongs at `LICENSE`. Contributors keep their copyright. Comuns takes no copyright assignment.

Contributions are certified with the Developer Certificate of Origin, version 1.1, recorded as a `Signed-off-by` trailer on the commit, as CONTRIBUTING.md specifies. The contributor signs for their own work. The DCO grants no license (evidence register §8, [V/L]). There is no CLA.

Model weights keep their own licenses. Registering a model records `licenseSpdx` and a `commercialHosting` flag that the registrant read from the file shipped with the weights. The registry grants no license. An operator who loads a file is responsible for the right to run it and to charge for it. Apache-2.0 on the Comuns node does not change a model's terms, and a model's terms do not relicense the node.

Apache-2.0 likely includes a patent grant. That statement is a characterization in the evidence register (evidence register §8, [L]), not legal advice.

This decision covers the Comuns repositories of code and documentation. It does not cover third-party engines the node links, such as llama.cpp (MIT in the register, evidence register §3, [V]) or mistral.rs (MIT, evidence register §3, [V]). Those components stay under their own licenses. Vendoring them is allowed only on their terms, with the DCO covering the act of submitting the vendor commit, as CONTRIBUTING.md describes.

## Alternatives considered

### MIT

Rejected for the project license. MIT likely includes no patent grant (evidence register §8, [L]). Apache-2.0 likely does. The comparison is not legal advice. MIT remains a common license for model weights and for engines the node may link. Those upstream licenses are unchanged by this ADR. Choosing MIT for Comuns itself would drop the patent grant the register associates with Apache-2.0, which is the reason it was not selected.

### AGPL

Deferred. AGPL section 13's network clause requires offering source to network users of a modified version (evidence register §8, [L]). Whether operators of a Comuns node should carry that obligation is a later CIP. Until such a CIP is Final, code and documentation stay under Apache-2.0. This deferral is not legal advice.

### BSL

Rejected. BSL 1.1 is not open source (evidence register §8, [V]). Comuns does not use it for code or documentation.

### A CLA

Rejected. A CLA may enable relicensing (evidence register §8, [V/L]). Comuns does not want a private path to relicense contributions. The DCO certifies the right to submit under Apache-2.0 and grants no license of its own. There is no copyright assignment. A later relicensing would need a CIP and the rights the existing license already gives, not a CLA stockpile.

## Consequences

- Every commit, including a documentation commit, carries `Signed-off-by` under the policy in CONTRIBUTING.md. A commit without the trailer is not offered under that policy. Until maintainers are seated, nobody can enforce the trailer by refusing a merge, because nobody can merge.
- GOVERNANCE.md, the CIP template and this ADR are not a substitute for the text of `LICENSE`.
- Operators still have to read the license file shipped with each weight file before a registration CIP sets `commercialHosting`. The snapshot in the model-registry document is a reading aid dated 2026-10-12, not a grant.
- Documents that quote third-party material stay within what this project may redistribute. This ADR does not relicense that material.
- Moving the project license to AGPL, MIT, or anything else takes a CIP. An emergency action cannot change the license.
- This record is not legal advice. Neither is the patent-grant comparison (evidence register §8, [L]).

## Links

- [docs/evidence-register.md](../evidence-register.md) §3, §7, §8
- [GOVERNANCE.md](../../GOVERNANCE.md)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [docs/node/model-registry-and-licenses.md](../node/model-registry-and-licenses.md)
- [docs/cip/README.md](../cip/README.md)
- [docs/cip/0000-template.md](../cip/0000-template.md)
- [ADR 0007](0007-no-protocol-token-in-v1.md)
- [ADR 0008](0008-model-first-pools.md)
- [docs/cip/0001-adopt-baseline-adrs.md](../cip/0001-adopt-baseline-adrs.md)
