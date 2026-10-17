mkdir -p $SPIKE/S5/deps/sem
cd $SPIKE/S5/deps/sem && npm init -y
cd $SPIKE/S5/deps/sem && npm install --ignore-scripts --save-exact @semaphore-protocol/contracts@4.14.3
ls $SPIKE/S5/deps/sem/node_modules $SPIKE/S5/deps/sem/node_modules/@semaphore-protocol/contracts
grep -rn "pragma solidity\|^import" $SPIKE/S5/deps/sem/node_modules/@semaphore-protocol/contracts --include=*.sol
