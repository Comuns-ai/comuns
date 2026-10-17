SR=$SPIKE
cd $SR/S4
export PATH=$SR/tools/node-v24.22.0-darwin-arm64/bin:$PATH
L=log.txt
run(){ { echo "\$ $*"; "$@"; echo "exit=$?"; } >> $L 2>&1; }
run $SR/S4/deps/pnpm/node_modules/.bin/pnpm --version
run $SR/S4/deps/pnpm/node_modules/.bin/pnpm install --ignore-scripts
run ls node_modules node_modules/.bin
run node_modules/.bin/tsc --version
run node_modules/.bin/tsc --strict --noEmit -p .
run node_modules/.bin/eslint src
run node_modules/.bin/prettier --check src eslint.config.js
tail -80 $L
