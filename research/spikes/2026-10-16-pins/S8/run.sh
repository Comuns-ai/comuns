#!/bin/bash
# Logs a command line and its full output to S8/log.txt, and echoes the output too.
LOG=$SPIKE/S8/log.txt
echo "\$ $*" >> "$LOG"
bash -c "$*" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
echo "exit=$rc" >> "$LOG"
echo "[exit=$rc]"
