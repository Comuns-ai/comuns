#!/bin/bash
SR=$SPIKE
cd $SR/S7/alloy
{ echo '$ cargo +1.99.1 build --release (time)'; time cargo +1.99.1 build --release 2>&1 | tail -20; echo "exit=${PIPESTATUS[0]}"; } >> ../log.txt 2>&1
{ echo '$ ./target/release/dynabi'; ./target/release/dynabi; echo "exit=$?"; echo '$ ./target/release/s7-alloy'; ./target/release/s7-alloy; echo "exit=$?"; } >> ../log.txt 2>&1
./target/release/dynabi > ../alloy-dyn-out.txt 2>&1
./target/release/s7-alloy > ../alloy-sol-out.txt 2>&1
cat ../alloy-dyn-out.txt
