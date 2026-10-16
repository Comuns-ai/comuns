node --version
/usr/bin/time -l node $SPIKE/S5/proof/prove.js 1 2>&1 | grep -vE 'page|swap|context|signals|messages|faults|reclaims|block|volunt|instructions|cycles'
/usr/bin/time -l node $SPIKE/S5/proof/prove.js 32 2>&1 | grep -vE 'page|swap|context|signals|messages|faults|reclaims|block|volunt|instructions|cycles'
