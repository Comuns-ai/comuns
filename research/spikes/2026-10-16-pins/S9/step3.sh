#!/bin/bash
# S9 step 3: wasm build, wasm-bindgen 0.2.129, Node + web bundles, interop.
S9=$SPIKE/S9
R=$S9/run.sh
W=crate/target/wasm32-unknown-unknown/release/comuns_crypto_spike.wasm

TAILN=8 $R $S9/crate 'set -o pipefail; cargo +1.99.1 build --target wasm32-unknown-unknown --release 2>&1 | grep -v "^   Compiling"; ls -l target/wasm32-unknown-unknown/release/*.wasm; echo RUSTFLAGS=$RUSTFLAGS; ls .cargo 2>&1'
TAILN=6 $R $S9/deps 'set -o pipefail; cargo +1.99.1 install wasm-bindgen-cli --version 0.2.129 --locked --root '$S9'/deps 2>&1 | tail -5'
TAILN=20 $R $S9 'set -o pipefail; node --version; wasm-bindgen --version; rm -rf pkg-node; wasm-bindgen --target nodejs --out-dir pkg-node '$W' && ls -l pkg-node && node node-run.cjs raw'
TAILN=20 $R $S9 'set -o pipefail; wasm-bindgen --target web --out-dir web '$W' && ls -l web; echo "-- sizes (bytes): raw, gzip -9"; for f in '$W' web/comuns_crypto_spike_bg.wasm pkg-node/comuns_crypto_spike_bg.wasm; do echo "$f $(wc -c < $f) $(gzip -9c $f | wc -c)"; done; grep -c "roundtrip" web/comuns_crypto_spike.js'

# Interop against the patched crate.
TAILN=10 $R $S9/crate 'set -o pipefail; cargo +1.99.1 build --bin interop 2>&1 | tail -3'
TAILN=15 $R $S9/interop 'set -o pipefail; node --version; npm --version; npm ci --ignore-scripts 2>&1 | tail -3; npm ls --all'
TAILN=40 $R $S9/interop 'node interop.mjs ../crate/target/debug/interop plain dir1; echo "plain-dir1-exit=$?"; echo ======; node interop.mjs ../crate/target/debug/interop plain dir2; echo "plain-dir2-exit=$?"'
TAILN=40 $R $S9/interop 'node interop.mjs ../crate/target/debug/interop chunked dir1; echo "chunked-dir1-exit=$?"; echo ======; node interop.mjs ../crate/target/debug/interop chunked dir2; echo "chunked-dir2-exit=$?"'

TAILN=15 $R $S9/crate 'grep -A1 -E "^name = \"(hpke|ohttp|bhttp|wasm-bindgen|getrandom|futures|chacha20poly1305|hkdf|sha2|js-sys)\"" Cargo.lock'
