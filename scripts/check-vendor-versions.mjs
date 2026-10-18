// Compara as versões das bibliotecas copiadas para frontend/static/js/vendor com as últimas do npm.
// Sai com erro (e o GitHub avisa) quando existe versão nova. Uso: node scripts/check-vendor-versions.mjs

import { readFile } from "node:fs/promises";

const README_PATH = new URL("../frontend/static/js/vendor/README.md", import.meta.url);

// pacote do npm -> trecho do README que traz a versão em uso ("## nome (versão X.Y.Z")
const LIBRARIES = [
  { npmPackage: "libsodium-wrappers-sumo", readmeName: "libsodium" },
  { npmPackage: "qrcode-generator", readmeName: "qrcode-generator" },
];

async function latestVersion(npmPackage) {
  const response = await fetch(`https://registry.npmjs.org/${npmPackage}/latest`);
  if (!response.ok) {
    throw new Error(`Não consegui consultar ${npmPackage} no npm (HTTP ${response.status}).`);
  }
  return (await response.json()).version;
}

function versionInUse(readme, readmeName) {
  const match = readme.match(new RegExp(String.raw`## ${readmeName} \(versão ([0-9.]+)`));
  if (!match) {
    throw new Error(`Não achei a versão de "${readmeName}" no README do vendor.`);
  }
  return match[1];
}

const readme = await readFile(README_PATH, "utf-8");
let outdated = false;
for (const { npmPackage, readmeName } of LIBRARIES) {
  const inUse = versionInUse(readme, readmeName);
  const latest = await latestVersion(npmPackage);
  const status = inUse === latest ? "em dia" : "DESATUALIZADA";
  console.log(`${npmPackage}: em uso ${inUse}, última ${latest} (${status})`);
  outdated ||= inUse !== latest;
}
process.exit(outdated ? 1 : 0);
