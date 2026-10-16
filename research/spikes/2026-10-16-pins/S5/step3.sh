rm -rf src/Counter.sol test script
$F config | grep -nE "evm_version|solc|optimizer"
$F build --sizes
