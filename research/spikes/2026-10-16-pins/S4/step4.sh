SR=$SPIKE
cd $SR/S4/lint6
export PATH=$SR/tools/node-v24.22.0-darwin-arm64/bin:$PATH
L=$SR/S4/log.txt
run(){ { echo "\$ $*"; "$@"; echo "exit=$?"; } >> $L 2>&1; }
run ln -sfn ../src src
run node -e "console.log(require('typescript').version)"
run node_modules/.bin/eslint src
cd ..
run node_modules/.bin/prettier --check src eslint.config.js
{ echo '$ npm view pnpm@12.14.0 dist.integrity dist.shasum'; npm view pnpm@12.14.0 dist.integrity dist.shasum; } >> $L 2>&1
{ echo '$ npm view typescript@7.0.2 dist.integrity dist.shasum'; npm view typescript@7.0.2 dist.integrity dist.shasum; } >> $L 2>&1
{ echo '$ npm view @typescript/typescript6@6.0.2 dist.integrity'; npm view @typescript/typescript6@6.0.2 dist.integrity; } >> $L 2>&1
tail -60 $L
