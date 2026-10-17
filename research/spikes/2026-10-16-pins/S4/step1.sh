SR=$SPIKE
mkdir -p $SR/S4/deps/pnpm $SR/S4/src
cd $SR/S4
export PATH=$SR/tools/node-v24.22.0-darwin-arm64/bin:$PATH
L=log.txt
run(){ { echo "\$ $*"; "$@"; echo "exit=$?"; } >> $L 2>&1; }
run node --version
for p in eslint @eslint/js typescript-eslint prettier @typescript/typescript6 typescript; do
  { echo "\$ npm view $p@latest version"; npm view $p@latest version; } >> $L 2>&1
done
echo "\$ npm view typescript versions --json (6.x)" >> $L
npm view typescript versions --json 2>>$L | grep '"6\.' | tail -8 >> $L
{ echo '$ npm view typescript dist-tags'; npm view typescript dist-tags --json; } >> $L 2>&1
run npm install --prefix deps/pnpm pnpm@12.14.0 --ignore-scripts
run ls deps/pnpm/node_modules/.bin
tail -60 $L
