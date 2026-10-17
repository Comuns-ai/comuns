#!/bin/bash
SR=$SPIKE
export PATH=$SR/tools/node-v24.22.0-darwin-arm64/bin:$PATH
cd $SR/S7/viem
{ echo '$ node --version'; node --version; echo "exit=$?"; } >> ../log.txt 2>&1
{ echo '$ npm install --ignore-scripts (viem 2.57.7 exact)'; npm install --ignore-scripts --save-exact 2>&1 | tail -8; echo "exit=$?"; echo '$ npm ls viem'; npm ls viem; echo "exit=$?"; } >> ../log.txt 2>&1
tail -20 ../log.txt
