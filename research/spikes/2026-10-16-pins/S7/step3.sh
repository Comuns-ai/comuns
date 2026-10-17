#!/bin/bash
SR=$SPIKE
cd $SR/S7/alloy
export CARGO_TARGET_DIR=$SR/S7/alloy/target
{ echo '$ cargo +1.99.1 build --release (time)'; time cargo +1.99.1 build --release 2>&1 | tail -40; echo "exit=${PIPESTATUS[0]}"; } >> ../log.txt 2>&1
tail -45 ../log.txt
