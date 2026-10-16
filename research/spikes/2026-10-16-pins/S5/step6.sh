$F build --sizes
$F inspect SemaphoreVerifier deployedBytecode > $SPIKE/S5/verifier-cancun.hex; wc -c $SPIKE/S5/verifier-cancun.hex
$F inspect Semaphore deployedBytecode > $SPIKE/S5/semaphore-cancun.hex; wc -c $SPIKE/S5/semaphore-cancun.hex
FOUNDRY_PROFILE=osaka $F config | grep -nE "evm_version|solc|optimizer|^out"
FOUNDRY_PROFILE=osaka $F build --sizes
FOUNDRY_PROFILE=osaka $F inspect SemaphoreVerifier deployedBytecode > $SPIKE/S5/verifier-osaka.hex; wc -c $SPIKE/S5/verifier-osaka.hex
FOUNDRY_PROFILE=osaka $F inspect Semaphore deployedBytecode > $SPIKE/S5/semaphore-osaka.hex; wc -c $SPIKE/S5/semaphore-osaka.hex
cmp $SPIKE/S5/verifier-cancun.hex $SPIKE/S5/verifier-osaka.hex && echo VERIFIER_IDENTICAL
cmp $SPIKE/S5/semaphore-cancun.hex $SPIKE/S5/semaphore-osaka.hex && echo SEMAPHORE_IDENTICAL
shasum -a 256 $SPIKE/S5/*.hex
