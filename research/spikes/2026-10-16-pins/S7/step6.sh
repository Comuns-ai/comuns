#!/bin/bash
SR=$SPIKE
cd $SR/S7/alloy-min
{ echo '# forge path NOT RUN: forge needs to download solc (no cached solc in ~/.svm; not in approved downloads)'; } >> ../log.txt
{ echo '$ (alloy-min, features sol-types+signer-local only) cargo +1.99.1 build --release (time)'; time cargo +1.99.1 build --release 2>&1 | tail -8; echo "exit=${PIPESTATUS[0]}"; } >> ../log.txt 2>&1
{ echo '$ alloy-min/target/release/s7-alloy'; ./target/release/s7-alloy; echo "exit=$?"; } >> ../log.txt 2>&1
{ echo '$ cargo tree -e normal --prefix none | sort -u | grep alloy'; cargo +1.99.1 tree -e normal --prefix none | sort -u | grep alloy; } >> ../log.txt 2>&1
{ echo '$ cargo tree -e features -i alloy (alloy-min)'; cargo +1.99.1 tree -e features --depth 1 | head -20; } >> ../log.txt 2>&1
./target/release/s7-alloy > ../alloy-min-out.txt
diff ../alloy-sol-out.txt ../alloy-min-out.txt && echo SAME_AS_FULL_BUILD
grep -A1 'name = "alloy' Cargo.lock | grep -v '^--' | paste - - | awk '{print $3,$6}'
tail -30 ../log.txt
