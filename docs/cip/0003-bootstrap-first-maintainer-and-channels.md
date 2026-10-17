# CIP 0003: Bootstrap: first maintainer, enforcement contact and private security channel

Status: Review
Type: process
Created: 2026-10-15
Requires: None

This CIP is in Review. It is not in Last Call and it is not Final. It proposes the first maintainer, the enforcement contact and the private security channel that GOVERNANCE.md section 6 requires. A name written in a Draft or Review copy seats nobody, as [MAINTAINERS.md](../../MAINTAINERS.md) states. Seating and adoption take effect only when this CIP is Final; item 7 governs the review process before then, and item 9 requires sign-off from the commit that adds this file.

## Abstract

If this CIP becomes Final, exactly one maintainer is seated: the person with the GitHub handle @rodrigopavezi. That person holds merge authority, is the enforcement contact that CODE_OF_CONDUCT.md requires, and monitors GitHub private vulnerability reporting on the repositories of the Comuns-ai GitHub organization, the private channel that SECURITY.md makes a release gate. The CIP restates the review counts of CONTRIBUTING.md, adopts the four operating texts (GOVERNANCE.md, CONTRIBUTING.md, SECURITY.md and CODE_OF_CONDUCT.md) as they stand at a recorded commit, fixes where Last Call is dated, and records how the merges and unsigned commits made before any authority existed are treated. It changes no protocol parameter, adopts no ADR, and leaves CIP-0001 and CIP-0002 at Draft. The one-person bootstrap is a known limitation, stated in the Specification.

## Motivation

GOVERNANCE.md section 6 says nobody may merge, cut a software release, take an emergency action or act as a private enforcement contact until a Final CIP names the first people with merge authority. CODE_OF_CONDUCT.md section 4 keeps enforcement inactive until the bootstrap CIP names a contact. SECURITY.md section 3 keeps the first software release blocked until a monitored private channel exists. The Phase 0 exit in [docs/project-plan.md](../project-plan.md) requires this CIP to reach Final before any later phase can merge or release. Without it, the project can write documents but cannot accept one.

Several questions are open in the current texts and this CIP answers them: how many maintainers, the form of the private channel and its acknowledgement time, the wording of the enforcement contact, whether the review counts are restated or adopted, which record dates Last Call, whether the bootstrap CIP adopts GOVERNANCE.md and its companion files, and how the merged pull requests #1–#3 and the commits that lack a Signed-off-by trailer are treated.

The proposal does not rely on a token, a coin vote or an ARB balance. ARB balances are not this project's votes. Anyone may object, including a class S operator.

## Specification

1. **Parameters.** This CIP changes no price band, no deadline, no bond and no protocol fee. The protocol fee is 0. No timelock is stated, because no parameter changes. This file sets no wei value.

2. **Seating.** If this CIP becomes Final, exactly one maintainer is seated, on the day it becomes Final: GitHub handle @rodrigopavezi. The same person is the merge authority, the CODE_OF_CONDUCT.md enforcement contact (item 3) and the monitor of the private vulnerability channel (item 4). No email address is part of this seating. Known limitations of this one-person bootstrap:
   - **Bus factor.** If the seated person is unavailable, nobody can merge, publish a software release, act on a conduct report or read a private vulnerability report.
   - **No second reviewer among maintainers.** No other maintainer reviews the seated person's merges.
   - **Contact and maintainer are the same person.** The enforcement contact and the merge authority are not separated.
   - **No independent recipient.** A complaint about the maintainer's own conduct has no independent private recipient. It can be written in public under CODE_OF_CONDUCT.md section 4, without private information, or raised as a blocking objection or a removal CIP.
   - **No closer for a disputed blocking objection.** When the author and an objector disagree whether an objection still blocks, nobody can close the dispute; the objection stays open and the CIP stays in Review, as GOVERNANCE.md section 4.3 and risk R4 there describe.

   A later CIP may seat more people or split these roles. Removal stays the path in GOVERNANCE.md section 6.1: a CIP that anyone may file and that becomes Final as a state of the public record, which the sole maintainer's merge authority cannot block.

3. **Enforcement contact.** The enforcement contact is the seated maintainer, reached privately through GitHub only: the private vulnerability-report form of the Comuns-ai/comuns repository, with a report title beginning `Conduct:`. Such a report is handled privately and is never published as an advisory. GitHub's product behaviour is not in the evidence register, and how that form stores, notifies or restricts a report is UNVERIFIED. The enforcement ladder in CODE_OF_CONDUCT.md section 5 applies only after this CIP is Final. A conduct report must omit prompts, keys, seed phrases and other people's private information.

4. **Private security channel.** The private channel is GitHub private vulnerability reporting (security advisories) on every repository of the Comuns-ai GitHub organization, monitored by the seated maintainer. Naming the channel while this CIP is Draft, Review or Last Call is expected and does not breach SECURITY.md section 3. The channel exists for SECURITY.md only when both conditions hold: this CIP is Final, and the repository setting for private vulnerability reporting has been switched on. The repository owner switches it on in the repository settings. This file does not say the setting is on. After switching it on, the seated maintainer records the date in MAINTAINERS.md; until that record exists, the software-release gate in SECURITY.md section 3 stays unmet.
   - **Acknowledgement target.** The seated maintainer aims to acknowledge receipt of a report within 7 calendar days. This is best effort. There is no commitment to a fix time. A missed acknowledgement does not make the report public, and the reporter does not publish it on that ground.
   - A report omits prompts, keys and seed phrases, as SECURITY.md section 4 requires.

5. **Review counts.** This CIP adopts the review rule of CONTRIBUTING.md section 4 by reference and restates it:
   - two public reviews, by two people other than the author, for a document whose subject is the protocol, cryptography or contracts;
   - one public review, by a person other than the author, otherwise.

   The subject matter controls the count, not the Type field. A reviewer need not be a maintainer; with one person seated, this is how a second pair of eyes exists. This CIP takes one review. [CIP-0004](0004-sepolia-testnet-configuration.md) and [CIP-0005](0005-phase-one-implementation.md) take two. Changing the counts is a later CIP.

6. **Operating texts.** On the day this CIP becomes Final, it adopts by reference GOVERNANCE.md, CONTRIBUTING.md, SECURITY.md and CODE_OF_CONDUCT.md, as they stand at the commit whose hash is written on the line below the Last Call date (item 7). A substantive change to any of the four texts after that commit and before Final returns this CIP to Review. The four texts remain amendable by a later CIP. This CIP does not adopt CIP-0001, CIP-0002 or any ADR; CIP-0001 stays Draft. This answers the question in [docs/project-plan.md](../project-plan.md) section 13 on which CIPs establish executable authority while CIP-0001 stays Draft, and open question 8 of [docs/project-charter.md](../project-charter.md): participants follow GOVERNANCE.md section 4 for this CIP, and nobody is seated by a private act.

7. **Host of record and dating.** The public record of this CIP is this file on the default branch of Comuns-ai/comuns (the repository first named Comuns-ai/documentation; renaming it does not change the record, including pull requests #1–#7), together with the public pull request described here. Copies elsewhere do not start or stop any clock.
   - **The Draft.** This file reached the default branch through the pull request that added it (#4). The repository owner merged that pull request as a pre-authority act that grants no authority, like pull requests #1–#3. GitHub administrator rights on the repository are not merge authority under GOVERNANCE.md.
   - **Status changes.** Review, Last Call and Final are made in one public, unmerged pull request on Comuns-ai/comuns that edits this file's status line.
   - **Last Call date.** The commit in that pull request that sets `Status: Last Call` also adds, directly below the status line, a line `Last Call started: YYYY-MM-DD` and, on the next line, `Operating texts at: <full commit hash>`, naming the commit of the default branch at which item 6 reads the four operating texts. The date written in that line starts the 14 days, following the written-dates rule of GOVERNANCE.md section 4.3. GitHub's own timeline is corroboration only, and its behaviour is UNVERIFIED.
   - **Final.** Anyone may state in public, on that pull request, that 14 days have elapsed with no open blocking objection. The author then sets `Status: Final` in a commit to that pull request whose message lists the disposition of every review and every blocking objection. Final is a state of that public record, not a merge.
   - **Edits during Last Call.** A substantive edit during Last Call, including a change to the handle or to any role in item 2, returns this CIP to Review, and a new, full 14-day Last Call starts from the edited text. Typo, formatting and link fixes that change no meaning are listed in the Change log.
   - **First merge.** The seated person's first use of merge authority merges that pull request together with an update to MAINTAINERS.md. GitHub's merge mechanics are UNVERIFIED.

   The following is the intended future text of MAINTAINERS.md. It is text to apply only on the day this CIP becomes Final. It is not applied by the pull request that adds this file, and MAINTAINERS.md still records that nobody is seated.

   ```text
   # Maintainers

   Seated by CIP-0003 (docs/cip/0003-bootstrap-first-maintainer-and-channels.md), Final on YYYY-MM-DD.

   | GitHub handle | Seated on | Seated by | Roles |
   | --- | --- | --- | --- |
   | @rodrigopavezi | YYYY-MM-DD | CIP-0003 | merge authority; CODE_OF_CONDUCT.md enforcement contact; monitor of the private vulnerability channel |

   Private vulnerability reporting on the Comuns-ai repositories: date the setting was switched on, not yet recorded. The seated maintainer replaces this sentence with that date after switching it on. Until a date is recorded here, the release gate in SECURITY.md section 3 is unmet.

   Removal follows GOVERNANCE.md section 6.1. A later CIP may seat more people or split these roles.
   ```

8. **Prior acts.** Pull requests #1–#3, the pull request that added this file (#4), and every later pull request that the repository owner merges onto the author's own repository before this CIP is Final, which at the time this CIP entered Review were #5 and #6, are merges made by the author before any authority exists. This CIP does not authorize those merges retroactively; GOVERNANCE.md section 6 says authority does not reach backward. This CIP acknowledges the public record described in item 7 as the record whose process texts it adopts under item 6. It adopts no ADR, nor CIP-0001 or CIP-0002, and it grants no retroactive authority for the earlier merges.

9. **DCO.** The repository history before the pull request that adds this file holds seven commits without a Signed-off-by trailer, listed here by full hash as git prints them:
   - `95a91c8a22ebbdc25a557c50c1a37ce106ff7386`
   - `f20e1a5cfbd671abba321d0ef14d07c893580db9`
   - `1709e3a4c3fa52263ca2c2fe59a6fdecd6abb3a9`
   - `449436c5f90cdc669252b5254452b0753dd9f004`
   - `4adefc5991243f53db23f2555a96f15f4f8d2348`
   - `4ab8d48e0a6310eb15e47dc992a335716d3757c5`
   - `58e12a7f37674290985e6f32481d1409f79055b7`

   Three of them, `1709e3a4c3fa52263ca2c2fe59a6fdecd6abb3a9`, `4adefc5991243f53db23f2555a96f15f4f8d2348` and `58e12a7f37674290985e6f32481d1409f79055b7`, are the host-generated merge commits of pull requests #1–#3 and are listed for completeness. The four authored commits, `95a91c8a22ebbdc25a557c50c1a37ce106ff7386`, `f20e1a5cfbd671abba321d0ef14d07c893580db9`, `449436c5f90cdc669252b5254452b0753dd9f004` and `4ab8d48e0a6310eb15e47dc992a335716d3757c5`, are the owner's own work, and their author offers them under the Developer Certificate of Origin through this CIP. This is an enumerated historical exception for those commits only, not a blanket exception. History is not rewritten.

   From the commit that adds this file onward, every authored commit carries a Signed-off-by trailer, as CONTRIBUTING.md section 2 describes. The documentation check `scripts/check-dco.py` examines every commit in a pull request's range from its base to its head, merge commits included, so a merge commit inside a pull request's range must carry a trailer too. The merge commit the host creates when a pull request is merged lies outside every pull request's range and is not checked; such host-generated merge commits are not authored commits. Open question: whether the seated maintainer merges by squash or by rebase, so that every commit on the default branch carries a trailer. The host's behaviour for either method is UNVERIFIED.

10. **Testnet.** This CIP sets no testnet value. [CIP-0004](0004-sepolia-testnet-configuration.md) is the testnet configuration.

## Rationale

**One maintainer.** Nobody other than the author has taken part in the project so far. Naming a second person who has not taken part, or leaving a seat for an unnamed person, would seat nobody real or would seat someone without their public consent. One named person, with the limitations stated in item 2 and a removal path anyone can use, is the smallest seating that lets the project merge at all. A later CIP can widen it as contributors appear.

**GitHub-native channels.** The public record already lives on GitHub, so the private vulnerability-report form and repository security advisories add no new service, no new account and no email inbox. Keeping the conduct contact on the same form avoids publishing a personal address. Whether the form behaves as this CIP expects is UNVERIFIED, which is why the channel exists for SECURITY.md only after the setting is switched on and the date is recorded.

**Written dates on one host.** GOVERNANCE.md section 4.3 left open which record dates Last Call. A dated line in a public pull request on the one repository that holds the file gives every reader the same start date and the same text, and a status change can be read from the file without trusting a host timeline.

**Adopting the operating texts.** GOVERNANCE.md, CONTRIBUTING.md, SECURITY.md and CODE_OF_CONDUCT.md are Draft. Seating someone under rules nobody has adopted would leave the seated person's authority without a written procedure. Fixing the texts at a recorded commit lets reviewers object to the exact wording that will bind.

Alternatives considered:

- An email alias for the enforcement contact and for security reports. Rejected. It publishes an address, adds a service to run, and is not tied to the public record.
- An external bug-bounty platform. Rejected. No bounty exists, the protocol fee is 0 and no treasury exists, and a platform would add a third party to every report.
- A two-person seat with an unnamed second person. Rejected. A seat without a name seats nobody under GOVERNANCE.md section 6, and the review counts already let non-maintainers review.
- Treating pull requests #1–#3 as seating. Rejected. GOVERNANCE.md section 6 says authority does not reach backward, and a merge by the repository owner is not a Final CIP.
- Requiring CIP-0001 to be Final first. Rejected. CIP-0001 adopts design ADRs, not process. Making seating wait on the design baseline would block every merge, including fixes to the baseline itself.
- Deciding by coin vote or by ARB balance. Rejected. There is no protocol token and no coin vote; the Ethereum EIP lifecycle likewise uses no coin vote (evidence register §8 [V]). ARB balances are not this project's votes.

## Backwards compatibility

Nothing is deployed. No contract, client or node exists to migrate. This CIP does not contradict an ADR.

The pull request that adds this file also reconciles texts written before a host existed: the GOVERNANCE.md section 4.3 sentence on which hosted record dates Last Call; the sentences in SECURITY.md and CONTRIBUTING.md that send issues and objections to a public repository not yet named; and the Phase 0 content in [docs/project-charter.md](../project-charter.md), which listed only the documentation and is updated in the same pull request to name this bootstrap CIP. Those edits change no rule; they point at this CIP, which was then Draft.

## Security considerations

This CIP has no effect on prompts, keys, seed phrases or escrow. An emergency action cannot seize escrow or expose prompts. Reports through the channel in item 4, and conduct reports through the form in item 3, must omit prompts, keys and seed phrases. The release gate stays unmet until this CIP is Final and the maintainer has recorded in MAINTAINERS.md the date private vulnerability reporting was switched on. The one-person limitations in item 2 apply to security handling too: a report waits while the sole maintainer is unavailable.

Security reporting is described in [SECURITY.md](../../SECURITY.md). The threat catalogue is [docs/security/threat-model.md](../security/threat-model.md). Neither file is amended by this CIP. This file contains no prompt, no key and no seed phrase.

## Economic considerations

The protocol fee is 0, and no treasury exists. There is no protocol token and no coin vote. ARB balances are not this project's votes. This CIP does not ask for funds, does not create a bounty and does not record a grant. It sets no wei value.

## Reference implementation

None.

## Change log

None.

## Copyright

This CIP assigns no copyright and uses no CLA.

Copyright 2026 Comuns contributors

Licensed under the Apache License, Version 2.0 (see LICENSE)
