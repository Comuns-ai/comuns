#!/bin/zsh
# usage: run.sh <dir> <scriptfile> [tail-lines]; logs each line (command) + full output to log.txt
S=$SPIKE
export SR=$S
export F=$S/tools/foundry-1.8.5/forge
export PATH=$S/tools/node-v24.22.0-darwin-arm64/bin:$PATH
L=$S/S5/log.txt
cd "$1" || exit 1
while IFS= read -r line; do
  [ -z "$line" ] && continue
  { echo "\$ (cd $1) $line"; eval "$line"; echo "exit=$?"; } >> $L 2>&1
done < "$2"
echo "--- last output (see log.txt) ---"
tail -n ${3:-40} $L
