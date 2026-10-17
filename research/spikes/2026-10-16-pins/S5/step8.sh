mkdir -p $SPIKE/S5/deps/upstream
curl -fsS -o $SPIKE/S5/deps/upstream/hardhat.config.ts https://raw.githubusercontent.com/semaphore-protocol/semaphore/v4.14.3/packages/contracts/hardhat.config.ts
cat $SPIKE/S5/deps/upstream/hardhat.config.ts
curl -sS -o /dev/null -w 'foundry.toml http=%{http_code}\n' https://raw.githubusercontent.com/semaphore-protocol/semaphore/v4.14.3/packages/contracts/foundry.toml
curl -sS -o /dev/null -w 'root foundry.toml http=%{http_code}\n' https://raw.githubusercontent.com/semaphore-protocol/semaphore/v4.14.3/foundry.toml
