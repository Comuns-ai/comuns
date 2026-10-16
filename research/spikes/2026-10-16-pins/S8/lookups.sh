#!/bin/bash
# S8 read-only lookups. Only curl GET and gh api GET. Run as: bash lookups.sh >> log.txt 2>&1
S8=$SPIKE/S8
UA='comuns-spike-S8 (read-only lookup)'
cd "$S8" || exit 1

echo "===== 1. llama.cpp commit ====="
echo '$ curl -sS -A UA https://crates.io/api/v1/crates/llama-cpp-2/0.1.159/dependencies'
curl -sS -A "$UA" https://crates.io/api/v1/crates/llama-cpp-2/0.1.159/dependencies
echo
echo '$ curl -sS -A UA https://crates.io/api/v1/crates/llama-cpp-2/0.1.159'
curl -sS -A "$UA" https://crates.io/api/v1/crates/llama-cpp-2/0.1.159
echo
echo '$ curl -sS -A UA https://crates.io/api/v1/crates/llama-cpp-sys-2'
curl -sS -A "$UA" https://crates.io/api/v1/crates/llama-cpp-sys-2 | python3 -c "import json,sys; d=json.load(sys.stdin); print('max_stable', d['crate']['max_stable_version']); [print(v['num'], v['created_at'], v['checksum'], 'yanked='+str(v['yanked'])) for v in d['versions'] if v['num'].startswith('0.1.1')]"
echo '$ curl -sSL -A UA -o deps/llama-cpp-sys-2-0.1.159.crate https://static.crates.io/crates/llama-cpp-sys-2/llama-cpp-sys-2-0.1.159.crate'
curl -sSL -A "$UA" -o deps/llama-cpp-sys-2-0.1.159.crate -w 'http=%{http_code} size=%{size_download}\n' https://static.crates.io/crates/llama-cpp-sys-2/llama-cpp-sys-2-0.1.159.crate
echo '$ curl -sSL -A UA -o deps/llama-cpp-sys-2-0.1.160.crate https://static.crates.io/crates/llama-cpp-sys-2/llama-cpp-sys-2-0.1.160.crate'
curl -sSL -A "$UA" -o deps/llama-cpp-sys-2-0.1.160.crate -w 'http=%{http_code} size=%{size_download}\n' https://static.crates.io/crates/llama-cpp-sys-2/llama-cpp-sys-2-0.1.160.crate
echo '$ shasum -a 256 deps/llama-cpp-sys-2-0.1.159.crate deps/llama-cpp-sys-2-0.1.160.crate'
shasum -a 256 deps/llama-cpp-sys-2-0.1.159.crate deps/llama-cpp-sys-2-0.1.160.crate
echo '$ tar -xzOf deps/llama-cpp-sys-2-0.1.159.crate llama-cpp-sys-2-0.1.159/.cargo_vcs_info.json'
tar -xzOf deps/llama-cpp-sys-2-0.1.159.crate llama-cpp-sys-2-0.1.159/.cargo_vcs_info.json
echo '$ tar -xzOf deps/llama-cpp-sys-2-0.1.160.crate llama-cpp-sys-2-0.1.160/.cargo_vcs_info.json'
tar -xzOf deps/llama-cpp-sys-2-0.1.160.crate llama-cpp-sys-2-0.1.160/.cargo_vcs_info.json
echo '$ gh api repos/utilityai/llama-cpp-rs/contents/llama-cpp-sys-2/llama.cpp?ref=3cfdd729d65e35da407e5f820edf73201bfa54f6'
gh api 'repos/utilityai/llama-cpp-rs/contents/llama-cpp-sys-2/llama.cpp?ref=3cfdd729d65e35da407e5f820edf73201bfa54f6' --jq '{type: .type, path: .path, sha: .sha, url: .url}'
echo '$ gh api repos/utilityai/llama-cpp-rs/contents/llama-cpp-sys-2/llama.cpp?ref=0dd5814c9b061930965d144c1653cd4d05054873'
gh api 'repos/utilityai/llama-cpp-rs/contents/llama-cpp-sys-2/llama.cpp?ref=0dd5814c9b061930965d144c1653cd4d05054873' --jq '{type: .type, path: .path, sha: .sha, url: .url}'
echo '$ gh api repos/utilityai/llama-cpp-rs/contents/.gitmodules?ref=3cfdd729d65e35da407e5f820edf73201bfa54f6 (content, base64-decoded)'
gh api 'repos/utilityai/llama-cpp-rs/contents/.gitmodules?ref=3cfdd729d65e35da407e5f820edf73201bfa54f6' --jq '.content' | base64 -d
echo '$ gh api repos/ggml-org/llama.cpp/commits/26394b4e6749a41c3633db040e0987500a5f7013'
gh api repos/ggml-org/llama.cpp/commits/26394b4e6749a41c3633db040e0987500a5f7013 --jq '{sha: .sha, date: .commit.committer.date, message: (.commit.message | split("\n")[0])}'
echo '$ gh api repos/ggml-org/llama.cpp/commits/d81235049384534c167caea52b85a694f6103d14'
gh api repos/ggml-org/llama.cpp/commits/d81235049384534c167caea52b85a694f6103d14 --jq '{sha: .sha, date: .commit.committer.date, message: (.commit.message | split("\n")[0])}'
echo '$ gh api repos/ggml-org/llama.cpp/git/refs/tags/v0.7.0'
gh api repos/ggml-org/llama.cpp/git/refs/tags/v0.7.0 --jq '{ref: .ref, type: .object.type, sha: .object.sha}'
echo '$ gh api repos/ggml-org/llama.cpp/git/tags/757cad021b357f417065ddbc41a6e8f87c1f8136'
gh api repos/ggml-org/llama.cpp/git/tags/757cad021b357f417065ddbc41a6e8f87c1f8136 --jq '{tag: .tag, type: .object.type, target: .object.sha, tagger: .tagger.date}'
echo '$ gh api repos/ggml-org/llama.cpp/commits/620d2225cc436ab0b001e3200e590e3b286ef9ab'
gh api repos/ggml-org/llama.cpp/commits/620d2225cc436ab0b001e3200e590e3b286ef9ab --jq '{sha: .sha, date: .commit.committer.date, message: (.commit.message | split("\n")[0])}'
echo '$ gh api repos/ggml-org/llama.cpp/compare/26394b4e...620d2225'
gh api repos/ggml-org/llama.cpp/compare/26394b4e6749a41c3633db040e0987500a5f7013...620d2225cc436ab0b001e3200e590e3b286ef9ab --jq '{status: .status, ahead_by: .ahead_by, behind_by: .behind_by, total_commits: .total_commits}'
echo '$ gh api repos/ggml-org/llama.cpp/compare/d812350...620d2225'
gh api repos/ggml-org/llama.cpp/compare/d81235049384534c167caea52b85a694f6103d14...620d2225cc436ab0b001e3200e590e3b286ef9ab --jq '{status: .status, ahead_by: .ahead_by, behind_by: .behind_by}'

echo "===== 2. names ====="
echo '$ gh api repos/Comuns-ai/comuns'
gh api repos/Comuns-ai/comuns --jq '{full_name: .full_name, private: .private, created_at: .created_at}'
echo '$ gh api orgs/Comuns-ai/repos?per_page=100'
gh api 'orgs/Comuns-ai/repos?per_page=100' --jq '.[] | .full_name'
echo '$ gh api orgs/Comuns-ai'
gh api orgs/Comuns-ai --jq '{login: .login, id: .id, public_repos: .public_repos}'
echo '$ gh api search/repositories?q=org:Comuns-ai'
gh api 'search/repositories?q=org:Comuns-ai' --jq '{total: .total_count, names: [.items[].full_name]}'
echo '$ curl -sS -w HTTP https://registry.npmjs.org/-/org/comuns/package'
curl -sS -w '\nHTTP=%{http_code}\n' https://registry.npmjs.org/-/org/comuns/package
echo '$ curl -sS -w HTTP https://registry.npmjs.org/-/org/comuns-ai/package'
curl -sS -w '\nHTTP=%{http_code}\n' https://registry.npmjs.org/-/org/comuns-ai/package
echo '$ curl -sS -w HTTP https://registry.npmjs.org/-/user/org.comuns/package'
curl -sS -w '\nHTTP=%{http_code}\n' https://registry.npmjs.org/-/user/org.comuns/package
echo '$ curl -sS -w HTTP https://registry.npmjs.org/-/user/org.comuns-ai/package'
curl -sS -w '\nHTTP=%{http_code}\n' https://registry.npmjs.org/-/user/org.comuns-ai/package
echo '$ curl -sS -w HTTP https://registry.npmjs.org/@comuns%2fsdk'
curl -sS -o /dev/null -w 'HTTP=%{http_code}\n' https://registry.npmjs.org/@comuns%2fsdk
echo '$ curl -sS -w HTTP https://registry.npmjs.org/@comuns-ai%2fsdk'
curl -sS -o /dev/null -w 'HTTP=%{http_code}\n' https://registry.npmjs.org/@comuns-ai%2fsdk
echo '$ curl crates.io comuns-node, comuns-relay, comuns'
for n in comuns-node comuns-relay comuns; do curl -sS -A "$UA" -o /dev/null -w "$n HTTP=%{http_code}\n" https://crates.io/api/v1/crates/$n; done

echo "===== 3. integrity ====="
echo '$ curl -sS https://nodejs.org/dist/v24.22.0/SHASUMS256.txt | grep darwin-arm64/linux-x64 tarballs'
curl -sS https://nodejs.org/dist/v24.22.0/SHASUMS256.txt | grep -E 'node-v24.22.0-(darwin-arm64|linux-x64)\.tar\.gz$'
for p in "pnpm 12.14.0" "viem 2.57.7" "typescript 7.0.2"; do
  set -- $p
  echo "\$ curl -sS https://registry.npmjs.org/$1/$2 (dist fields)"
  curl -sS "https://registry.npmjs.org/$1/$2" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['name'], d['version'], 'integrity='+d['dist'].get('integrity',''), 'shasum='+d['dist'].get('shasum',''), 'tarball='+d['dist'].get('tarball',''))"
done
echo '$ curl -sS https://registry.npmjs.org/@semaphore-protocol%2fproof/4.14.3 (dist fields)'
curl -sS https://registry.npmjs.org/@semaphore-protocol%2fproof/4.14.3 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['name'], d['version'], 'integrity='+d['dist'].get('integrity',''), 'shasum='+d['dist'].get('shasum',''), 'tarball='+d['dist'].get('tarball',''))"
echo '$ curl -sS https://registry.npmjs.org/@semaphore-protocol%2fcontracts/4.14.3 (dist fields)'
curl -sS https://registry.npmjs.org/@semaphore-protocol%2fcontracts/4.14.3 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['name'], d['version'], 'integrity='+d['dist'].get('integrity',''), 'shasum='+d['dist'].get('shasum',''), 'tarball='+d['dist'].get('tarball',''))"
for c in "hpke 0.14.1" "ohttp 0.8.0" "bhttp 0.8.0" "alloy 2.5.0" "wasm-bindgen 0.2.129" "llama-cpp-2 0.1.159"; do
  set -- $c
  echo "\$ curl -sS -A UA https://crates.io/api/v1/crates/$1/$2 (checksum)"
  curl -sS -A "$UA" "https://crates.io/api/v1/crates/$1/$2" | python3 -c "import json,sys; v=json.load(sys.stdin)['version']; print(v['crate'], v['num'], 'cksum='+v['checksum'], 'yanked='+str(v['yanked']))"
done
echo '$ gh api repos/foundry-rs/foundry-toolchain/releases/latest'
gh api repos/foundry-rs/foundry-toolchain/releases/latest --jq '{tag: .tag_name, published: .published_at, target: .target_commitish}'
echo '$ gh api repos/foundry-rs/foundry-toolchain/git/refs/tags/v1.9.1'
gh api repos/foundry-rs/foundry-toolchain/git/refs/tags/v1.9.1 --jq '{type: .object.type, sha: .object.sha}'
echo '$ gh api repos/foundry-rs/foundry-toolchain/commits/v1.9.1'
gh api repos/foundry-rs/foundry-toolchain/commits/v1.9.1 --jq '{sha: .sha, date: .commit.committer.date, message: (.commit.message | split("\n")[0])}'
echo "===== done ====="
