#!/bin/bash
SR=$SPIKE
cd $SR/S7/alloy
{ echo '$ ./target/release/s7-alloy'; ./target/release/s7-alloy; echo "exit=$?"; echo '$ cargo +1.99.1 tree -e normal --prefix none | sort -u'; cargo +1.99.1 tree -e normal --prefix none | sort -u; echo '$ cargo tree -e features (alloy)'; cargo +1.99.1 tree -p alloy@2.5.0 -e features --depth 1; } >> ../log.txt 2>&1
./target/release/s7-alloy
grep -n 'name = "alloy' Cargo.lock | head -40
