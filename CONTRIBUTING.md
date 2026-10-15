# Contributing
Author: Comuns contributors
Status: Draft
Category: Process
Created: 2026-10-12
**Reference:** GOVERNANCE.md, CODE_OF_CONDUCT.md, MAINTAINERS.md, SECURITY.md, docs/cip/README.md, docs/cip/0000-template.md
---

## 1 How to take part today

Comuns is a document-phase proposal. Nothing runs yet, and no protocol implementation exists. `scripts/` holds documentation checkers, which are not a node, relay, client or contract. You can take part now in four ways.

1. Read GOVERNANCE.md, this file, MAINTAINERS.md, SECURITY.md, and docs/cip/README.md.
2. Open issues on the Comuns-ai/documentation repository. Use issues for document comments and for documentation flaws. SECURITY.md says what a public issue may contain once the subject is a vulnerability in code.
3. Comment on CIPs. None are Final. The template is docs/cip/0000-template.md.
4. Join a working group: Protocol, Node, Cryptography, Contracts, Applications, or Documentation. Write in a public issue, or on a relevant CIP, which group you are joining, and review that group's documents in public.

This draft sets no meeting schedule and names no discussion channel beyond issues and CIP comments on the Comuns-ai/documentation repository. MAINTAINERS.md records that no maintainers are seated. You do not need a hardware class, a stake, or a holding to do any of the four steps above. A class S operator has the same rights.

## 2 Developer Certificate of Origin

Contributions use the Developer Certificate of Origin. Comuns uses no CLA and no copyright assignment. The Signed-off-by line is not a CLA.

When you contribute a commit, including a documentation-only commit, add this trailer as the last line of the commit message:

```
Signed-off-by: Name <email>
```

Add the trailer with `git commit -s`. Use your own name and your own email in place of the placeholders. Do not add a Signed-off-by line for another person.

The trailer records the Developer Certificate of Origin, version 1.1. By adding it you certify that at least one of the first three statements below is true of the contribution, and that the fourth is true. In plain language, those statements are:

- You created the contribution in whole or in part, and you have the right to submit it under the open source license indicated in the file, which for Comuns is Apache-2.0 in LICENSE.
- The contribution is based on earlier work covered by an appropriate open source license, and under that license you have the right to submit that work with your modifications, under the same license unless you are permitted to submit under a different license, as indicated in the file. Porting or vendoring third-party open source code, such as MIT-licensed code, is this case; the upstream author does not need to sign off on this project.
- The contribution was provided to you by someone else who certified one of the three statements, and you have not modified it.
- You understand that the contribution and your sign-off are public, and that a record of them, including all personal information you submit with them, is kept indefinitely and may be redistributed with the project or the license involved.

That is a description of DCO 1.1, not a replacement for it; this project adds no further requirement to the sign-off. The DCO grants no license. A CLA may enable relicensing (evidence register §8 [V/L]). Comuns takes no CLA, so this project has no CLA path for relicensing. You keep your copyright. The license that applies to the contribution is Apache-2.0 in LICENSE, as GOVERNANCE.md states. This section is not legal advice.

A commit that lacks the trailer is not offered under this policy. There is no one to enforce that on a merge until maintainers are seated.

The seven commits listed in [docs/cip/0003-bootstrap-first-maintainer-and-channels.md](docs/cip/0003-bootstrap-first-maintainer-and-channels.md) are earlier history. Three of them are the host-generated merge commits of pull requests #1–#3, listed there for completeness. The four authored commits among them are the author's earlier work, offered under the Developer Certificate of Origin through that CIP. That offer is not a blanket exception. Every later authored commit carries the Signed-off-by trailer. `scripts/check-dco.py` checks every commit in a pull request's `base..head` range, merge commits included, and it does not exclude merges. A merge commit inside that range must carry a trailer. The merge commit the host creates when a pull request is merged lies outside every pull request range, so it is not checked, and such host-generated merge commits are not authored commits. Whether the seated maintainer merges by squash or by rebase, so that every commit on the default branch carries a trailer, is an open question in section 8. Host behaviour is UNVERIFIED.

## 3 Documentation conventions

Substantive documents use this header, then a horizontal rule:

```
# Document title
Author: Comuns contributors
Status: Draft
Category: Decision
Created: YYYY-MM-DD
**Reference:** GOVERNANCE.md
---
```

Use a real category and a real created date when you write a document. Then:

- Number the major sections as `## 1`, `## 2`, and so on.
- Put a Risks section after the body, and put Open questions after Risks.
- In a Risks section, give each item a heading of the form `### Rn — title **[RISK] · High|Medium|Low**`.
- Put diagrams in a fenced block tagged mermaid, using `flowchart TD` when the diagram is a flowchart.
- Name new files in kebab-case.
- Put an architecture decision record at docs/adr/NNNN-kebab-title.md.
- Put a CIP at docs/cip/NNNN-kebab-title.md.

ADRs under docs/adr/ are proposed until docs/cip/0001-adopt-baseline-adrs.md is accepted. After acceptance, a change that contradicts an ADR needs a superseding ADR. GOVERNANCE.md states that rule in full.

Cite an external fact as the evidence register section that actually contains it (docs/evidence-register.md, §1–§16, with How to cite at §17), with its mark, and mark a fact that is not in the register UNVERIFIED. The project domain is comuns.ai, written as plain text. Do not publish it as a link, and do not describe a service as running there.

## 4 Review rule

This review rule is proposed policy until maintainers are seated. It is the review practice for documents now. It is not a merge gate while nobody has merge authority.

- Two reviews are required for protocol, cryptography and contracts documents.
- One review is required otherwise.

A review is a public comment by a person other than the author. The comment names the document and states approval or names a blocking objection. The author's own revision does not count as a review. Two reviews means two people. One review means one person. Reviews do not weight stake, holdings, hardware class, or ARB balances.

When maintainers are seated, this policy stands until a CIP changes it. GOVERNANCE.md is the decision procedure for that CIP.

## 5 Secrets stay out of issues

never paste prompts, keys or seed phrases into issues.

The same ban covers CIP text, commit messages, and code comments. A report of a documentation flaw follows SECURITY.md and obeys the same ban. If a draft would be unclear without a prompt, describe the shape of the input in abstract terms and keep the prompt itself out of the repository.

## 6 Code style

Code style for a protocol implementation is deferred until a CIP adds that code. No protocol implementation exists. `scripts/` holds documentation checkers, which are not a node, relay, client or contract. This file sets no formatter, no language choice, and no layout. [docs/adr/0013-repositories-toolchains-ci-and-releases.md](docs/adr/0013-repositories-toolchains-ci-and-releases.md) proposes the style, and [docs/cip/0005-phase-one-implementation.md](docs/cip/0005-phase-one-implementation.md) (Draft) is the CIP that states it, under the same license and DCO rules as every other contribution.

## 7 Risks

### R1 — A future commit omits the DCO trailer **[RISK] · Medium**

A commit without `Signed-off-by: Name <email>` is not offered under this policy. Until maintainers are seated, nobody can refuse the merge on that ground, because nobody can merge. The rule is still the contribution rule.

### R2 — Secrets land in a public issue **[RISK] · High**

Issues on the Comuns-ai/documentation repository are public. Prompts, keys, and seed phrases in an issue would be exposed. Section 5 forbids that content. There is no private issue channel in this draft.

### R3 — Review counts are treated as optional **[RISK] · Medium**

The two-review rule for protocol, cryptography and contracts documents, and the one-review rule otherwise, are policy until maintainers are seated. Participants can ignore them and still have no merge to block the file. This draft asks the bootstrap CIP to keep the counts.

### R4 — Document form drifts before anyone can merge a fix **[RISK] · Low**

The header, the kebab-case paths, and the Risks-then-Open-questions order are easy to miss. With none seated, a correcting edit waits on the same public CIP path as every other change.

## 8 Open questions

- Must a review come from someone who has joined the relevant working group, or may any person review? This draft allows any person other than the author.
- Should the bootstrap CIP restate the review counts, or adopt this file by reference? [docs/cip/0003-bootstrap-first-maintainer-and-channels.md](docs/cip/0003-bootstrap-first-maintainer-and-channels.md) (Draft) proposes an answer: it restates the counts and adopts this file by reference. The question stays open until that CIP is Final.
- Which CIP will add the first code and the code style that comes with it? [docs/cip/0005-phase-one-implementation.md](docs/cip/0005-phase-one-implementation.md) (Draft) proposes to add the first code and states its style. The question stays open until that CIP is Final.
- Whether the seated maintainer merges by squash or by rebase, so that every commit on the default branch carries a Signed-off-by trailer, is open. Host behaviour is UNVERIFIED.
