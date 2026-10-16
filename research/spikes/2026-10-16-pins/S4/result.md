# S4: TypeScript 7 toolchain
## Results
| Check | Result | Measured value | Evidence (log.txt) |
|---|---|---|---|
| Node 24.22.0 | PASS | v24.22.0 | `$ node --version` |
| pnpm 12.14.0 local install, install of all devDeps with --ignore-scripts | PASS | `Done in 43s using pnpm v12.14.0` | `Done in 43s using pnpm v12.14.0` |
| `tsc --version` | PASS | `Version 7.0.2` | `$ node_modules/.bin/tsc --version` |
| `tsc --strict --noEmit -p .` type-checks and errors on deliberate type error | PASS | exit=1, only error: `src/bad.ts(1,14): error TS2322: Type 'string' is not assignable to type 'number'.` (good.ts clean) | `error TS2322` |
| ESLint + typescript-eslint 8.71.2 type-aware (`recommendedTypeChecked`, `projectService: true`) on TS 7.0.2 | FAIL | Fails at config load, exit=2, before any rule runs. Error: `typescript-eslint does not support TS 7.0.` (message points to the TS 6 side-by-side blog section and typescript-eslint issue #10940 "tracking typescript-eslint's support for TS >=7.1"). Thrown by `typescript-eslint/dist/index.js:52` | `typescript-eslint does not support TS 7.0.` |
| Type-aware lint with TS 6 API (tsc stays 7.0.2) | PASS | exit=1, catches floating promise: `src/good.ts 14:3 error Promises must be awaited ... @typescript-eslint/no-floating-promises`. Only 1 problem. `require('typescript').version` in the lint dir = 6.0.3 | `no-floating-promises` |
| `prettier --check` | PASS (after one formatting fix) | First run flagged my own `eslint.config.js` (exit=1), src was clean; ran `prettier --write` on that config only; re-check: `All matched files use Prettier code style!` exit=0 | `All matched files use Prettier code style!` |

## Wiring that worked for type-aware lint (TS 7 `tsc` + TS 6 API for typescript-eslint)
Two separate pnpm projects:
- `$SR/S4/` (main): `typescript 7.0.2`, provides `tsc` 7.0.2 (also contains the unused-for-lint `@typescript/typescript6` giving a `tsc6` bin = Version 6.0.3).
- `$SR/S4/lint6/`: devDependency `"typescript": "npm:@typescript/typescript6@6.0.2"` (pnpm alias, so `require('typescript')` resolves to the TS 6 API package), plus `eslint 10.13.0`, `@eslint/js 10.0.1`, `typescript-eslint 8.71.2`. Its `src` is a symlink to `../src` and it has its own identical tsconfig.json and eslint.config.js (same `recommendedTypeChecked` + `projectService: true`).
- Not verified in a single project: I did not try one project with a pnpm override. The alias in a sibling project is what was measured. (A first attempt with `eslint ../src` from lint6 failed as ESLint ignores files outside the config base path; fixed with the symlink, which is a layout issue, not a toolchain one.)

## Exact versions resolved
Registry latest at run time (2026-10-16): eslint 10.13.0, @eslint/js 10.0.1, typescript-eslint 8.71.2, prettier 3.9.10, @typescript/typescript6 6.0.2, typescript latest 7.0.2.
- npm dist-tags for typescript: latest 7.0.2, rc 7.0.1-rc, beta 6.0.0-beta, next 7.1.0-dev.20261016.1.
- Latest TypeScript 6.x on the registry: **6.0.3** (6.0.2 also exists). `@typescript/typescript6@6.0.2` depends on `@typescript/old = npm:typescript@^6`, which resolved to typescript 6.0.3, so its reported version is 6.0.3.
- pnpm-lock.yaml (main): typescript@7.0.2, @typescript/typescript6@6.0.2, typescript@6.0.3, typescript-eslint@8.71.2 (resolved against typescript@7.0.2 peer in main), eslint 10.13.0. Node binary for TS 7 on macOS: `@typescript/typescript-darwin-arm64@7.0.2`.
- ESLint reported `ESLint: 10.13.0`.

## Integrity (registry, npm view; matched pnpm-lock where present)
- typescript 7.0.2: integrity `sha512-8FYau96o3NKOhbjKi/qNvG/W5jhzxkbdm5sj9AbZ/5T5sWqn3hJgLfGx27sRKZWTvyzCP8dLRBTf5tBTSRVUNA==`, shasum `9ec773d7954a8c182c17cc5bbd575aa28bc51582` (lock integrity identical).
- pnpm 12.14.0: integrity `sha512-wYum2HmT09Fky16JSPMrLAbuhUSH4GzY2GeBNC+z5btGNDZwNHEehoArqpw3vqkGzhkprQjXCITJfYAd8TOJpg==`, shasum `b589f9374f009fa90d07b42e803ef0ac646dffb5` (registry only; pnpm was installed with npm into deps/pnpm, so it is not in pnpm-lock.yaml).
- @typescript/typescript6 6.0.2: `sha512-mbCddXd+jm7hfx7w2YU64/Av4/NqqeG3GoRZgxPcgoTxYjhrcfJRw9ULch71SS4G+Q3bOXFhRvPqjguN0Hyp5w==`.
- typescript 6.0.3 (lock): `sha512-y2TvuxSZPDyQakkFRPZHKFm+KKVqIisdg9/CZwm9ftvKXLP8NRWj38/ODjNbr43SsoXqNuAisEf1GdCxqWcdBw==`.
- typescript-eslint 8.71.2 (lock): `sha512-Rz4effbMy2g9wnvOJZG6SbVavX313Lap1vNEbk1RUochzickvzP8P4HB+bkNg5e50eVz1hQGjh9K1omI1xB4Bw==`.

## Findings that affect a pin
1. typescript-eslint 8.71.2 hard-refuses TS 7.0 (throws at load), so type-aware lint cannot use `typescript@7.0.2` as its `typescript`. It works against the TS 6 API (`@typescript/typescript6@6.0.2`, resolves 6.0.3) and catches `no-floating-promises`. Pin: `tsc` = typescript 7.0.2; lint tooling needs `typescript` aliased to `npm:@typescript/typescript6@6.0.2` (or TS 6.0.3) in the project that runs ESLint. The error message itself states typescript-eslint support for TS >=7.1 is tracked in issue #10940.
2. Latest TS 6.x is 6.0.3; `@typescript/typescript6@6.0.2` pulls 6.0.3 via a caret range, so its effective version floats unless pinned by lockfile.
3. pnpm 12.14.0 wrote `minimumReleaseAgeExclude: [eslint@10.13.0]` into pnpm-workspace.yaml (eslint 10.13.0 was newer than the release-age gate). A repo using pnpm 12 with a release-age gate may need the same exclusion for freshly released pins. The message said it can be made strict.
4. pnpm store is at `~/Library/pnpm/store/v11` (shared user cache, normal package-manager cache; not a global install). Peer dependency warnings were printed in the main project (`Issues with peer dependencies found`), expected since typescript-eslint peers on a TS version it rejects; not inspected further.
5. Registry was slow during install (requests of 15-18 s), no failures.

## Residuals / not verified
- Single-project override wiring (pnpm overrides) not tried; only sibling-project alias.
- Whether the type-aware lint also works with `typescript@6.0.3` installed directly (rather than via the `@typescript/typescript6` alias): not tested; the resolved API was 6.0.3 either way.
- ESLint rules beyond the floating promise were not examined; no other problems reported on good.ts.
- No text addressed to an AI was encountered in package output; the only pointers were URLs in the typescript-eslint error message (not followed).
- node_modules directories (main and lint6) can be deleted by the orchestrator.
