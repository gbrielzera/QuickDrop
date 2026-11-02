// Confere se as bibliotecas copiadas para frontend/static/js/vendor são exatamente as registradas em SHA256SUMS.
// Uma biblioteca de criptografia trocada sem aviso quebraria a criptografia ponta a ponta inteira.
// Ao atualizar uma biblioteca de propósito, gere o arquivo de novo: cd frontend/static/js/vendor && sha256sum *.mjs > SHA256SUMS
// Uso: node scripts/verify-vendor-hashes.mjs

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

const VENDOR_DIR = new URL("../frontend/static/js/vendor/", import.meta.url);

async function sha256Of(fileName) {
  const content = await readFile(new URL(fileName, VENDOR_DIR));
  return createHash("sha256").update(content).digest("hex");
}

const sums = await readFile(new URL("SHA256SUMS", VENDOR_DIR), "utf-8");
let allMatch = true;
for (const line of sums.trim().split("\n")) {
  const [expectedHash, fileName] = line.split(/\s+\*?/);
  const matches = (await sha256Of(fileName)) === expectedHash;
  console.log(`${fileName}: ${matches ? "ok" : "DIFERENTE do registrado"}`);
  allMatch &&= matches;
}
process.exit(allMatch ? 0 : 1);
