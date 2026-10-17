#!/bin/bash
# S9 step 2: clippy, negative control (nonce-only fix), patched crate's own tests.
S9=$SPIKE/S9
R=$S9/run.sh

TAILN=30 $R $S9/crate 'cargo +1.99.1 clippy --all-targets -- -D warnings 2>&1 | grep -v "^   Compiling\|^    Checking"'

# Negative control: same spike tests against ohttp 0.8.0 with ONLY the nonce-buffer fix,
# to show tests (c) and (d) detect bugs 2 and 3 (bug 1 would otherwise panic first).
rm -rf $S9/negctl && mkdir -p $S9/negctl
cp -R $S9/ohttp-0.8.0-orig $S9/negctl/ohttp-noncefix-only
cp -R $S9/crate/src $S9/crate/Cargo.toml $S9/crate/Cargo.lock $S9/negctl/
mkdir -p $S9/negctl/crate && mv $S9/negctl/src $S9/negctl/Cargo.toml $S9/negctl/Cargo.lock $S9/negctl/crate/
TAILN=40 $R $S9/negctl 'sed -i "" -e "s/nonce: \[0; 16\],/nonce: [0; 32],/" -e "s/nonce: \[u8; 16\],/nonce: [u8; 32],/" ohttp-noncefix-only/src/stream.rs && diff -ru ../ohttp-0.8.0-orig ohttp-noncefix-only; sed -i "" "s#../ohttp-0.8.0-patched#../ohttp-noncefix-only#" crate/Cargo.toml && grep -A1 "patch.crates-io" crate/Cargo.toml'
TAILN=40 $R $S9/negctl/crate 'cargo +1.99.1 test --lib -- --nocapture --test-threads=1 test_c test_d test_s3 2>&1 | grep -v "^   Compiling"'

# Patched crate's own test suite, in a copy so cargo cannot touch the diffed tree.
rm -rf $S9/selftest && cp -R $S9/ohttp-0.8.0-patched $S9/selftest
TAILN=40 $R $S9/selftest 'cargo +1.99.1 test --no-default-features --features client,server,rust-hpke,stream 2>&1 | grep -v "^   Compiling" | tail -40'
TAILN=60 $R $S9/selftest 'cargo +1.99.1 test --no-default-features --features client,server,rust-hpke 2>&1 | grep -v "^   Compiling" | tail -60'
