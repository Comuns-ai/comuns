SR=$SPIKE
cd $SR/S4
export PATH=$SR/tools/node-v24.22.0-darwin-arm64/bin:$PATH
L=$SR/S4/log.txt
run(){ { echo "\$ $*"; "$@"; echo "exit=$?"; } >> $L 2>&1; }
run $SR/S4/node_modules/.bin/prettier --check src
run $SR/S4/node_modules/.bin/prettier --write eslint.config.js
run $SR/S4/node_modules/.bin/prettier --check src eslint.config.js
cd lint6
run $SR/S4/deps/pnpm/node_modules/.bin/pnpm install --ignore-scripts
run ls -la node_modules node_modules/typescript
run node -e "console.log(require('typescript').version)"
run node_modules/.bin/eslint --config eslint.config.js ../src
cd ..
run node_modules/.bin/tsc --version
run node_modules/.bin/tsc6 --version
grep -n -A3 -E "^  (typescript|'?@typescript/typescript6)" pnpm-lock.yaml | head -60 >> $L
tail -60 $L
