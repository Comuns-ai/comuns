grep -rn --include='*.sol' -E 'pragma solidity|^import' ../deps/sem/node_modules/@semaphore-protocol/contracts
find ../deps/sem/node_modules -name '*.sol' | head -30
grep -E '"version"|"_resolved"' ../deps/sem/node_modules/@semaphore-protocol/contracts/package.json ../deps/sem/node_modules/@zk-kit/*/package.json
