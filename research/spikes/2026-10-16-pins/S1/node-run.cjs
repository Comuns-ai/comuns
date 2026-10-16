// Runs the wasm roundtrip() under Node via --target nodejs bindings.
const m = require("./pkg-node/comuns_crypto_spike.js");
console.log("node", process.version);
console.log("roundtrip():", m.roundtrip());
if (process.argv[2] === "raw") {
  try {
    console.log("roundtrip_b_raw():", m.roundtrip_b_raw());
  } catch (e) {
    console.log("roundtrip_b_raw() threw:", e && e.constructor && e.constructor.name, String(e && e.message));
  }
}
