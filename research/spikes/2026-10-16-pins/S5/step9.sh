mkdir -p $SPIKE/S5/deps/artifacts
cd $SPIKE/S5/deps/artifacts && npm pack @zk-kit/semaphore-artifacts@4.13.0 --json --ignore-scripts
cd $SPIKE/S5/deps/artifacts && ls -la
cd $SPIKE/S5/deps/artifacts && shasum -a 1 *.tgz
cd $SPIKE/S5/deps/artifacts && echo "sha512-$(openssl dgst -sha512 -binary *.tgz | openssl base64 -A)"
npm view @zk-kit/semaphore-artifacts@4.13.0 dist.shasum dist.integrity
cd $SPIKE/S5/deps/artifacts && mkdir -p unpacked && tar -xzf zk-kit-semaphore-artifacts-4.13.0.tgz -C unpacked
cd $SPIKE/S5/deps/artifacts/unpacked && find . -type f | wc -l
cd $SPIKE/S5/deps/artifacts/unpacked && find . -type f -exec stat -f '%z %N' {} + | sort -k2 | head -150
cd $SPIKE/S5/deps/artifacts/unpacked && du -sk . && find . -type f -exec stat -f '%z' {} + | awk '{s+=$1} END {print "total_bytes=" s}'
cd $SPIKE/S5/deps/artifacts/unpacked && find . -type f | sort | xargs shasum -a 256 > $SPIKE/S5/artifacts-sha256.txt
wc -l $SPIKE/S5/artifacts-sha256.txt
