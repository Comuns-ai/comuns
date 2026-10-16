cat $SPIKE/S5/deps/artifacts/unpacked/package/README.md
cd $SPIKE/S5/proof && npm init -y
cd $SPIKE/S5/proof && npm install --ignore-scripts --save-exact @semaphore-protocol/core@4.14.3 @semaphore-protocol/proof@4.14.3
cd $SPIKE/S5/proof && npm ls --all 2>&1 | grep -E "semaphore|snarkjs|zk-kit"
sed -n 1,80p $SPIKE/S5/proof/node_modules/@semaphore-protocol/proof/dist/types/generateProof.d.ts
grep -rn "semaphore.hash\|\.hash\|download" $SPIKE/S5/proof/node_modules/@semaphore-protocol/proof/dist/index.node.js | head -20
