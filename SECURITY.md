# Security policy
Author: Comuns contributors
Status: Draft
Category: Decision
Created: 2026-10-12
**Reference:** GOVERNANCE.md, MAINTAINERS.md, docs/security/threat-model.md
---

## 1 Summary

Comuns is a community proposal for a decentralized LLM-inference network. This file is the security policy for that proposal while it is documents, and the rule for reporting once code exists. Nothing runs yet. No protocol implementation exists. `scripts/` holds documentation checkers, which are not a node, relay, client or contract. No bounty exists. Decisions that change this policy are CIPs under GOVERNANCE.md. No maintainers are seated, so nobody operates a private reporting channel today.

External facts are cited as the evidence register section that contains them (docs/evidence-register.md, §1–§16, with How to cite at §17); the grant facts in this file live in §8. This file is not legal advice. An external factual claim that is not in the register is marked UNVERIFIED.

## 2 What exists today

What exists today is documents only. No service is running. This repository holds no keys and no seed phrases. No bounty exists.

The project domain is comuns.ai, written here as plain text. This repository does not present that domain as a running service, and it does not name that domain as a place to send reports.

Arbitrum DAO grant programs exist, including an Audit Program (evidence register §8 [V]). None have been awarded to Comuns. This project does not claim an audit. Whether an application is pending is UNVERIFIED.

The protocol fee is 0, so no treasury exists. There is no treasury key to custody because there is no treasury.

## 3 Reporting once code exists

Once code exists, send a private report to seated maintainers. A monitored private channel is a release gate: seated maintainers do not publish a software release until that channel exists and someone seated is monitoring it. This file adopts no channel, names no inbox, and names no address. MAINTAINERS.md seats nobody, so the gate is unmet.

Until then, a public issue may describe a documentation flaw. A public issue is the wrong place for a vulnerability in code. If code appears in the repository before a monitored private channel exists, use this interim path: open a public issue that names only the affected document path or component and says that a vulnerability report is being held for the private channel, with no exploit detail, no reproduction, and no prompts, keys, or seed phrases; keep the detail yourself; and send it by private report to seated maintainers as soon as the channel the bootstrap CIP names exists. Document-only changes are not a software release and may proceed under GOVERNANCE.md while the gate is unmet.

The bootstrap CIP that seats maintainers names the channel and the people who monitor it as part of seating, as GOVERNANCE.md section 6 requires. Naming the channel in that CIP while it is Draft, Review, or Last Call is expected and does not breach this policy. The channel does not exist, and the setting is not claimed enabled, until that CIP is Final and the maintainer records enabling it.

## 4 Never include prompts, keys or seed phrases in a report

Never include prompts, keys or seed phrases in a report. That ban covers a public issue, a private report, a CIP comment, and a commit. Describe the flaw by document path, CIP number, component, and behavior. Say what an attacker could cause, and stop before the secret, the prompt text, or the raw key material.

If you have already put that material in a public issue, say so in a follow-up that does not repeat the secret, and treat the material as exposed. This draft has no seated maintainer who can purge history. Whether the host of the Comuns-ai/documentation repository can purge a commit is UNVERIFIED. Host product behaviour not in the evidence register is UNVERIFIED.

## 5 Scope

Project scope is LLM inference only. A report does not widen it.

In scope today:

- Errors and dangerous ambiguities in the documents of this repository, reported as documentation flaws in a public issue.
- A proposed design that would seize escrow, expose prompts, or skip the parameter timelock in GOVERNANCE.md.

In scope once code exists, by private report to seated maintainers:

- Defects in the LLM-inference protocol, node software, cryptography, and settlement contracts.
- Defects that could expose prompts, seize or divert escrow, or break a settlement rule a CIP has accepted.

Out of scope today:

- A running service, a production key, or a bounty payment. None of those exist.
- Arbitrum DAO systems, and any third-party application. Comuns governance is separate from Arbitrum DAO governance, as GOVERNANCE.md states.
- Support questions about a network that is not running.

Privacy limits for prompts are the subject of docs/security/privacy-and-contexts.md. The threat model is docs/security/threat-model.md. This policy points at those paths and does not restate them. If this file and those documents disagree after both are accepted, the conflict is an open question until a CIP resolves it.

## 6 Risks

### R1 — No private reporting channel **[RISK] · High**

No maintainers are seated, so no one monitors a private channel. A documentation flaw can be filed in public. A code vulnerability has nowhere to go that meets this policy until a monitored private channel is a release gate that has actually been met.

### R2 — A public issue can leak secrets **[RISK] · High**

A public issue is readable by anyone who can read the Comuns-ai/documentation repository. Prompts, keys, or seed phrases in that issue would be exposed. Section 4 forbids that content. Nothing in the current document set can claw a pasted secret back, because no maintainers are seated.

### R3 — No bounty and no awarded audit **[RISK] · Medium**

No bounty exists. Arbitrum DAO grant programs, including an Audit Program, exist (evidence register §8 [V]), and none have been awarded to Comuns. Reviewers have no payment from this project, and this project has no audit report to point to. Findings depend on volunteer reading of documents.

### R4 — The release gate can delay the first software release **[RISK] · Medium**

A monitored private channel is a release gate. That delay is intentional. It also means the first software release waits on seating and on the channel the bootstrap CIP names; this file deliberately does not name one. Document work is not blocked by that gate.

### R5 — Scope creep through the report inbox **[RISK] · Low**

A report could ask Comuns to secure training, generic compute, or another network. Scope is LLM inference only. Those subjects are out of scope, and a report does not create a treasury or a token with which to fund them.

## 7 Open questions

- What form should the monitored private channel take? The bootstrap CIP names it as part of seating; this draft does not choose the form. [docs/cip/0003-bootstrap-first-maintainer-and-channels.md](docs/cip/0003-bootstrap-first-maintainer-and-channels.md) (Draft) proposes GitHub private vulnerability reporting monitored by the seated maintainer. The channel does not exist, and the setting is not claimed enabled, until that CIP is Final and the maintainer records enabling it.
- What acknowledgement time, if any, that CIP should promise. This draft sets none. Copying an outside project's response window would be UNVERIFIED here. [docs/cip/0003-bootstrap-first-maintainer-and-channels.md](docs/cip/0003-bootstrap-first-maintainer-and-channels.md) (Draft) proposes a 7-day acknowledgement target. The channel does not exist, and the setting is not claimed enabled, until that CIP is Final and the maintainer records enabling it.
- After the private channel exists, do documentation flaws stay on public issues? This draft keeps them public while only documents exist.
- If SECURITY.md and docs/security/threat-model.md disagree after both are accepted, which one yields? This draft does not decide that conflict.
- Who may confirm, in public, that a reported documentation flaw is fixed, while no maintainers are seated? This draft leaves confirmation to the public CIP discussion.
