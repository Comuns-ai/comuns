// Groups every package in the resolved graph (cargo metadata resolve.nodes) by licence string.
const fs = require("fs");
const md = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const inResolve = new Set(md.resolve.nodes.map((n) => n.id));
const groups = {};
for (const p of md.packages) {
  if (!inResolve.has(p.id)) continue;
  const lic = p.license || (p.license_file ? `FILE:${p.license_file}` : "NONE");
  (groups[lic] ||= []).push(`${p.name} ${p.version}`);
}
let total = 0;
for (const [lic, pkgs] of Object.entries(groups).sort((a, b) => b[1].length - a[1].length)) {
  pkgs.sort();
  total += pkgs.length;
  console.log(`## ${lic} (${pkgs.length})`);
  console.log(pkgs.join(", "));
}
console.log(`TOTAL packages in resolved graph: ${total}`);
