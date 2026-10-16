$F build --sizes --force
FOUNDRY_PROFILE=osaka $F build --sizes --force
node $SPIKE/S5/cmp.js $SPIKE/S5
