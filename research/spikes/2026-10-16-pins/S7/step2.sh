#!/bin/bash
SR=$SPIKE
export PATH=$SR/tools/node-v24.22.0-darwin-arm64/bin:$PATH
cd $SR/S7/viem
{ echo '$ node run.mjs > viem-out.json'; node run.mjs > ../viem-out.json; echo "exit=$?"; cat ../viem-out.json; } >> ../log.txt 2>&1
cat ../viem-out.json
