# S8: read-only lookups (no installs)

Run 2026-10-16, about 18:46-18:55 UTC. Every command and its full output is in `$SR/S8/log.txt`. Line numbers below refer to that file. Only curl GET and `gh api` GET were used, plus one `.crate` download into `$SR/S8/deps/`. Nothing was installed and no git state was changed.

## Results

| Check | Result | Measured value | Evidence |
|---|---|---|---|
| 1a. llama-cpp-2 0.1.159 dependency on llama-cpp-sys-2 | PASS | req `^0.1.159`, kind `normal`, optional false, target null (a second entry adds `metal` for `cfg(all(target_os="macos", any(target_arch="aarch64","arm64")))`) | `https://crates.io/api/v1/crates/llama-cpp-2/0.1.159/dependencies`, field `dependencies[].req`; log lines 4-5 |
| 1b. Versions of llama-cpp-sys-2 in the 0.1.159 window | PASS | 0.1.159 (created 2026-10-07T17:13:15Z, cksum 1a96d43d9370ff79293fe9777c9a4bda9d3bacb7100b61ed1e3690df39e9ad9e), 0.1.160 (created 2026-10-15T21:26:08Z, cksum 912d8a0522acec022ae07d099366234067c8af6a18570a603f0749b7bb927e9a), `max_stable_version` = 0.1.160 | `https://crates.io/api/v1/crates/llama-cpp-sys-2`, fields `versions[].num/created_at/checksum`, `crate.max_stable_version`; log lines 8-9 |
| 1c. VCS sha of llama-cpp-sys-2 0.1.159 | PASS | `3cfdd729d65e35da407e5f820edf73201bfa54f6` | `.cargo_vcs_info.json` inside `https://static.crates.io/crates/llama-cpp-sys-2/llama-cpp-sys-2-0.1.159.crate`, field `git.sha1`; log lines 82-85 |
| 1d. llama.cpp submodule at that sha | PASS | `26394b4e6749a41c3633db040e0987500a5f7013` (type `submodule`) | `gh api repos/utilityai/llama-cpp-rs/contents/llama-cpp-sys-2/llama.cpp?ref=3cfdd729d65e35da407e5f820edf73201bfa54f6`, field `sha`; log line 95 |
| 1e. Upstream of that submodule | PASS | `https://github.com/ggml-org/llama.cpp` | `gh api repos/utilityai/llama-cpp-rs/contents/.gitmodules?ref=3cfdd729...`, base64-decoded `url`; log lines 98-101 |
| 1f. Commit 26394b4e (upstream) | PASS | "json: Fixed json enum handling (#28518)", committer date 2026-09-21T08:32:07Z | `gh api repos/ggml-org/llama.cpp/commits/26394b4e6749a41c3633db040e0987500a5f7013`; log line 103 |
| 1g. Vendored commit of llama-cpp-sys-2 0.1.160 (for comparison) | PASS | VCS sha `0dd5814c9b061930965d144c1653cd4d05054873`, submodule `d81235049384534c167caea52b85a694f6103d14` ("llama.cpp : bump version to 0.6.0 (#29997)", 2026-10-05T15:13:51Z) | `.cargo_vcs_info.json` in llama-cpp-sys-2-0.1.160.crate (log lines 88-91); `gh api repos/utilityai/llama-cpp-rs/contents/llama-cpp-sys-2/llama.cpp?ref=0dd5814c...` (log line 97); `gh api repos/ggml-org/llama.cpp/commits/d812350...` (log line 105) |
| 1h. llama.cpp v0.7.0 tag | PASS | Annotated tag object `757cad021b357f417065ddbc41a6e8f87c1f8136`, dereferences to commit `620d2225cc436ab0b001e3200e590e3b286ef9ab` ("llama.cpp : bump version to 0.7.0 (#30603)", 2026-10-15T13:48:22Z) | `gh api repos/ggml-org/llama.cpp/git/refs/tags/v0.7.0` (`object.type` = tag); `gh api repos/ggml-org/llama.cpp/git/tags/757cad02...` (`object.sha`); log lines 106-111 |
| 1i. Vendored commit vs v0.7.0 | PASS | 26394b4e...620d2225: status `ahead`, ahead_by 595, behind_by 0 (26394b4e is an ancestor of v0.7.0, 595 commits behind). d812350...620d2225: ahead_by 240, behind_by 0 | `gh api repos/ggml-org/llama.cpp/compare/26394b4e...620d2225` (`status`, `ahead_by`, `behind_by`); log lines 112-115 |
| 2a. GitHub `Comuns-ai/comuns` | PASS (404) | `Not Found`, HTTP 404 | `gh api repos/Comuns-ai/comuns`; log lines 117-118 |
| 2b. GitHub org `Comuns-ai` repos | PASS | Org exists (id 341979546, `public_repos` 2). Repos: `Comuns-ai/documentation`, `Comuns-ai/.github`. Search total 2 | `gh api orgs/Comuns-ai/repos?per_page=100` (`.[].full_name`); `gh api orgs/Comuns-ai` (`id`, `public_repos`); `gh api search/repositories?q=org:Comuns-ai` (`total_count`); log lines 119-125 |
| 2c. npm scope `@comuns` | PASS (not found) | `{"error":"Scope not found"}`, HTTP 404 | `https://registry.npmjs.org/-/org/comuns/package`; log lines 126-128 |
| 2d. npm scope `@comuns-ai` | PASS (not found) | `{"error":"Scope not found"}`, HTTP 404 | `https://registry.npmjs.org/-/org/comuns-ai/package`; log lines 129-131 |
| 2e. npm `/-/user/org.<scope>/package` (comuns, comuns-ai) | PASS (not found) | `{"error":"Scope not found"}`, HTTP 404 for both | `https://registry.npmjs.org/-/user/org.comuns/package` and `.../org.comuns-ai/package`; log lines 132-137 |
| 2f. npm `@comuns/sdk` | PASS (404) | HTTP 404 | `https://registry.npmjs.org/@comuns%2fsdk`; log lines 138-139 |
| 2g. npm `@comuns-ai/sdk` | PASS (404) | HTTP 404 | `https://registry.npmjs.org/@comuns-ai%2fsdk`; log lines 140-141 |
| 2h. crates.io `comuns-node`, `comuns-relay`, `comuns` | PASS (404) | HTTP 404 for all three | `https://crates.io/api/v1/crates/<name>`; log lines 142-145 |
| 3a. Node 24.22.0 SHA-256 (darwin-arm64, linux-x64) | PASS | darwin-arm64 `6a9724d9b50a5f22b4816cded441b5a8d9ddae546191a5e5b7efa5a5e2ee26d5`; linux-x64 `28ea0a438de9a13bd7891fd758eee6c7819ee8af5442dfd8d45bd65e56d4228c` | `https://nodejs.org/dist/v24.22.0/SHASUMS256.txt` (matching lines); log lines 147-149 |
| 3b. pnpm 12.14.0 | PASS | integrity `sha512-wYum2HmT09Fky16JSPMrLAbuhUSH4GzY2GeBNC+z5btGNDZwNHEehoArqpw3vqkGzhkprQjXCITJfYAd8TOJpg==`; shasum (sha1) `b589f9374f009fa90d07b42e803ef0ac646dffb5` | `https://registry.npmjs.org/pnpm/12.14.0`, `dist.integrity`, `dist.shasum`; log lines 150-151 |
| 3c. viem 2.57.7 | PASS | integrity `sha512-x3UqqrcQuESaRVK6a0BvNmoNP0SVhu913uxEAxYLJx1lNYnj6ylTntfUdakCUKjk1+T+63gkdwFGJQ2O5C/nRw==`; shasum `31c62217c90b937f7f8aa39cc3459d21811e5d8f` | `https://registry.npmjs.org/viem/2.57.7`; log lines 152-153 |
| 3d. typescript 7.0.2 | PASS | integrity `sha512-8FYau96o3NKOhbjKi/qNvG/W5jhzxkbdm5sj9AbZ/5T5sWqn3hJgLfGx27sRKZWTvyzCP8dLRBTf5tBTSRVUNA==`; shasum `9ec773d7954a8c182c17cc5bbd575aa28bc51582` | `https://registry.npmjs.org/typescript/7.0.2`; log lines 154-155 |
| 3e. @semaphore-protocol/proof 4.14.3 | PASS | integrity `sha512-Zu7vIA161+jieo1DzhKoGB/UgTnG6cGMJtAN1/O6o4yKXKBkq7ly7JC3RZ0SbayfdN4TpTJyfO27i1USQ51eyw==`; shasum `b5d0d7faed4fe5cfa1d8009a0dc0d4453029afe2` | `https://registry.npmjs.org/@semaphore-protocol%2fproof/4.14.3`; log lines 156-157 |
| 3f. @semaphore-protocol/contracts 4.14.3 | PASS | integrity `sha512-N6UdFINfvDbpsIRSGuvOXZbKczDTrJATQQN5ToFI+oAVAO8s9TuBrFxDIsATnGnP8q/Dz/j7ZBEE6ypAU5Zebw==`; shasum `d1cd78d62f2050ff21c5237c1269f24c8c607663` | `https://registry.npmjs.org/@semaphore-protocol%2fcontracts/4.14.3`; log lines 158-159 |
| 3g. crates.io checksums (SHA-256) | PASS | hpke 0.14.1 `a5324110b02044183df000f0bd7d2d7e61f1000631508627e77f63983b6fdffb`; ohttp 0.8.0 `cc53603e4bf77342fe8409611972078761604e4370330c4ee5abac49f079b464`; bhttp 0.8.0 `b60d03ddf90ae9569b5f5397900b9838f92bd1004e13114f82ebfba0dead6582`; alloy 2.5.0 `f5a08ebfa51fdc243e0c6a662f5cf3428f04d1ad858e3fe77238cc78063eb86d`; wasm-bindgen 0.2.129 `9bb54f33acc68fd454578d9820b0bde1a1a3d17aa17bb7b6595806d02886d409`; llama-cpp-2 0.1.159 `fab4a3cd6f539c1d658161c85390c18b1d3f67283275e1567b34417dca3dd8c9`. All `yanked` = False | `https://crates.io/api/v1/crates/<name>/<version>`, field `version.checksum`; log lines 160-171 |
| 3h. foundry-toolchain latest release | PASS | Latest release tag `v1.9.1` (published 2026-07-28T23:39:38Z). Tag resolves to commit `908c540300062bd5a7e473851cdb4282204cee09` ("chore(deps): bump the npm-weekly group with 3 updates (#158)", committer date 2026-07-20T15:41:14Z) | `gh api repos/foundry-rs/foundry-toolchain/releases/latest` (`tag_name`); `gh api repos/foundry-rs/foundry-toolchain/git/refs/tags/v1.9.1` (`object.type` = commit, `object.sha`); log lines 172-177 |

Checksum cross-check: the SHA-256 of the downloaded `llama-cpp-sys-2-0.1.159.crate` (`1a96d43d...9ad9e`) and `llama-cpp-sys-2-0.1.160.crate` (`912d8a05...927e9a`) match the `checksum` fields returned by the crates.io API. So the crates.io `checksum` is the SHA-256 of the `.crate` file (log lines 79-81).

## Exact versions resolved

Not applicable to this spike, since nothing was installed and no lockfile was read. The versions I looked up are:

- llama-cpp-2 0.1.159; llama-cpp-sys-2 candidates 0.1.159 and 0.1.160.
- Node 24.22.0, pnpm 12.14.0, viem 2.57.7, typescript 7.0.2, @semaphore-protocol/proof 4.14.3, @semaphore-protocol/contracts 4.14.3.
- hpke 0.14.1, ohttp 0.8.0, bhttp 0.8.0, alloy 2.5.0, wasm-bindgen 0.2.129.
- foundry-toolchain v1.9.1 (commit 908c5403).

## Findings that affect a pin

1. **llama-cpp-2 0.1.159 does not pin llama.cpp directly.** It depends on `llama-cpp-sys-2 = ^0.1.159`. The llama.cpp revision therefore depends on which llama-cpp-sys-2 0.1.x is resolved:
   - llama-cpp-sys-2 **0.1.159** vendors llama.cpp `26394b4e6749a41c3633db040e0987500a5f7013`, which is 595 commits behind v0.7.0 (`620d2225...`).
   - llama-cpp-sys-2 **0.1.160** vendors llama.cpp `d81235049384534c167caea52b85a694f6103d14`, which is 240 commits behind v0.7.0.
   - Cargo resolves a caret requirement to the highest matching non-yanked version. crates.io currently reports 0.1.160 as `max_stable_version`. So an unpinned fresh resolution of `^0.1.159` would most likely pick 0.1.160. This is inferred from Cargo's documented behaviour, not measured in a resolve. To get the 0.1.159 revision, the pin must be `=0.1.159` on llama-cpp-sys-2 (or a lockfile entry that resolves it).
2. **Names available as of 2026-10-16 (lookup time only):**
   - `Comuns-ai/comuns` returns 404. The `Comuns-ai` org exists and lists only `Comuns-ai/documentation` and `Comuns-ai/.github`.
   - npm scopes `@comuns` and `@comuns-ai` return "Scope not found". `@comuns/sdk` and `@comuns-ai/sdk` return 404.
   - crates.io `comuns`, `comuns-node` and `comuns-relay` return 404.
3. **Integrity values** are listed in the table. The Node SHA-256 values come from the SHASUMS256.txt file fetched over HTTPS. I did not verify its detached signature.

## Residuals / not verified

- **Name checks are point-in-time, and a 404 is not proof of availability.** A 404 for `Comuns-ai/comuns` can also mean a private repo the token cannot see. The org repo list and search come from the authenticated `gh` token, so private repos it cannot read would not appear. The npm scope and package endpoints return 404 for unclaimed names, and do not prove that a scope can be claimed. I did not check npm user or org ownership pages.
- **npm endpoints.** The `/-/user/org.<scope>/package` endpoints were used as the "user endpoints" named in the packet. They returned "Scope not found" for both scopes. I did not check any other npm endpoint.
- **llama.cpp v0.7.0.** I checked the git tag `v0.7.0` and its commit. I did not separately fetch a GitHub Release object (`releases/tags/v0.7.0`).
- **llama-cpp-sys-2 resolved version.** I did not read any project Cargo.lock, so which llama-cpp-sys-2 version is actually resolved in this project is not measured here.
- **Earlier attempts.** I first ran some lookups interactively. The first attempts to write to the log in compound commands were refused by the sandbox and did not run. The complete set of lookups was then re-run from `$SR/S8/lookups.sh`, which appended every command and its full output to `log.txt`. The values in this report come from that logged run. `$SR/S8/run.sh` was written but not used.
- **Foundry action.** The packet asked for "the commit SHA of its latest release tag". The commit date (2026-07-20) is earlier than the release publish date (2026-07-28). I did not investigate the difference.
