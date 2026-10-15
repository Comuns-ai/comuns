# Code of conduct
Author: Comuns contributors
Status: Draft
Category: Decision
Created: 2026-10-12
**Reference:** GOVERNANCE.md, MAINTAINERS.md, CONTRIBUTING.md
---

## 1 Pledge

People who write, review, or discuss Comuns pledge to treat one another as equals in that work. We pledge to judge a CIP by its written content. Hardware class, stake, and holdings do not change anyone's right to file one. A class S operator has the same rights. We pledge to keep the work on LLM inference and its governance, to leave other people's private information out of the repository, and to remember that no maintainers are seated and that nobody has private authority.

## 2 Expected behavior

- Read the CIP or the document before you object to it.
- Make each objection specific, and say what change would answer it.
- Talk about the text, and keep personal characterization out of the review.
- Cite an external fact as the evidence register section that contains it (docs/evidence-register.md, §1–§16, with How to cite at §17), and mark a claim that is not in the register UNVERIFIED.
- Leave prompts, keys, and seed phrases out of issues, CIPs, and comments.
- Add the Developer Certificate of Origin trailer when you offer a commit, as CONTRIBUTING.md describes.
- Assume the lifecycle in GOVERNANCE.md is the way a disagreement gets a decision.

## 3 Unacceptable behavior

- Insults, slurs, and threats directed at a person.
- Sexual comments, or sexual attention, that the other person has not invited.
- Publishing another person's private information.
- Putting prompts, keys, or seed phrases into an issue, a CIP, or a commit.
- Trying to block a filing because of the author's hardware class, stake, holdings, or ARB balance.
- Announcing merge authority, a private sanction, or an emergency action while no maintainers are seated.
- Flooding Last Call with comments that raise no specific objection.

## 4 Reporting

Until maintainers are seated, see MAINTAINERS.md; this repository has no private enforcement contact. [docs/cip/0003-bootstrap-first-maintainer-and-channels.md](docs/cip/0003-bootstrap-first-maintainer-and-channels.md) (Draft) proposes the contact. Enforcement is inactive until that CIP is Final. The contact and the maintainer are the same person, a known limitation.

Enforcement is inactive until that CIP is Final. Before then, a person may describe conduct in a public issue on the Comuns-ai/documentation repository only when the issue contains no prompts, no keys, no seed phrases, and no other person's private information. The issue records what happened. It does not start a sanction, and it does not seat a maintainer.

## 5 Enforcement ladder

The enforcement ladder has three levels. It applies only after the bootstrap CIP is Final, maintainers are seated, and that CIP has named the enforcement contact. Until then, nobody applies these steps. Nobody has private authority to improvise a sanction.

Each case starts at the least serious level that addresses the behavior. A severe case may start at temporary exclusion from discussion, or at removal from a future maintainer role.

Filing a CIP, and filing a blocking objection on a CIP, are proposal rights under GOVERNANCE.md. Correction and temporary exclusion from discussion do not remove either right. They pause discussion, as the level describes. They do not create a holding requirement, a hardware-class requirement, or a vote.

### 5.1 Correction

A seated maintainer writes, in public, which behavior broke this policy and what change they expect. The person continues to file issues, to comment on CIPs, and to file CIPs. The note stays factual, and it omits private information, prompts, keys, and seed phrases.

### 5.2 Temporary exclusion from discussion

A seated maintainer sets a stated period of temporary exclusion from discussion. During that period the person does not file issues and does not take part in CIP discussion. They may still file a CIP, and they may still file a blocking objection on any CIP, including one in Last Call, because neither is a discussion right. An excluded person files the objection through the public record of the CIP, in the form GOVERNANCE.md section 4.3 requires, and it has the same effect as any other blocking objection. The period and the reason are written in public, without private information, prompts, keys, or seed phrases. When the period ends, the person returns to discussion with the same proposal rights as anyone else.

The period is at most 90 days. That maximum is a proposal of this draft, recorded in GOVERNANCE.md's open questions. The maintainer writes the length, within that maximum, in the public note. This draft sets no default length.

### 5.3 Removal from a future maintainer role

Removal from a future maintainer role applies when the person is a seated maintainer, or when a CIP proposes to seat them. If they are seated, removal takes effect only through a CIP that becomes Final, as GOVERNANCE.md section 6.1 states; no group of seated maintainers removes anyone outside a CIP, and when only one maintainer is seated the path is still a CIP, which anyone may file. The seated person keeps merge authority until that CIP is Final. If a CIP proposes to seat a person with a pending conduct matter, anyone may file a blocking objection on that CIP naming the matter; the objection returns the CIP to Review, where the author may change the names and start a new Last Call. Removal from a future maintainer role does not remove the right to file a CIP or a blocking objection.

## 6 Risks

### R1 — The ladder has no operator **[RISK] · High**

No maintainers are seated, and enforcement is inactive until the bootstrap CIP names a contact. A public issue can record conduct and still produce no correction, no temporary exclusion from discussion, and no removal from a future maintainer role.

### R2 — A public report can expose private information **[RISK] · High**

Before a contact exists, the record of conduct is a public issue. A report that includes private information, a prompt, a key, or a seed phrase would publish it. Section 4 forbids that content. There is no private channel in this file.

### R3 — Exclusion could be widened into a proposal ban **[RISK] · Medium**

Temporary exclusion from discussion is limited to discussion so that equal proposal rights stay intact. A later custom could try to turn it into a ban on filing CIPs. That widening would need a CIP, and it would conflict with GOVERNANCE.md as this draft stands.

## 7 Open questions

- The bootstrap CIP must name the enforcement contact. This draft leaves the role's wording to that CIP. [docs/cip/0003-bootstrap-first-maintainer-and-channels.md](docs/cip/0003-bootstrap-first-maintainer-and-channels.md) (Draft) proposes the contact. Enforcement is inactive until that CIP is Final. The contact and the maintainer are the same person, a known limitation.
- What period should be the usual length of temporary exclusion from discussion? This draft sets no default and proposes a 90-day maximum.
- May a person removed from a maintainer role be named again in a later CIP? This draft allows a later CIP to propose it, with Last Call as the check.
- Should temporary exclusion from discussion ever pause new CIP filings, or must proposal rights stay intact in every case? This draft keeps them intact.
