#!/bin/bash
# usage: run.sh <dir> <cmd string> -- logs command and full output to log.txt
SR=$SPIKE
export PATH=$SR/tools/node-v24.22.0-darwin-arm64/bin:$SR/S1/deps/bin:$PATH
LOG=$SR/S1/log.txt
cd "$1" || exit 1
shift
{ echo "\$ (cwd=$PWD) $*"; bash -c "$*"; echo "exit=$?"; } 2>&1 | tee -a $LOG | tail -n ${TAILN:-60}
