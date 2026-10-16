$F config | grep -nE "evm_version|solc|optimizer|^auto_detect|via_ir"
$F config --json | head -c 3000
