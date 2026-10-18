// Testes da criptografia. Rodar a partir da pasta frontend/:  node --test tests/

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  decryptFile,
  decryptJson,
  decryptText,
  deriveRoomKeys,
  encryptFile,
  encryptJson,
  encryptText,
  fromBase64Url,
  generateRoomSecret,
  generateSalt,
  toBase64Url,
} from "../static/js/crypto.js";

const ONE_MEGABYTE = 1024 * 1024;
const FILE_HEADER_BYTES = 24;
const ENCRYPTED_CHUNK_BYTES = ONE_MEGABYTE + 17;

const salt = generateSalt();
const { encryptionKey } = deriveRoomKeys("senha-de-teste", salt);
const otherKey = deriveRoomKeys("outra-senha", salt).encryptionKey;

function makeRandomBlob(sizeInBytes) {
  const bytes = new Uint8Array(sizeInBytes);
  // getRandomValues aceita no máximo 65536 bytes por chamada.
  for (let start = 0; start < sizeInBytes; start += 65536) {
    crypto.getRandomValues(bytes.subarray(start, Math.min(start + 65536, sizeInBytes)));
  }
  return new Blob([bytes]);
}

async function blobToBytes(blob) {
  return new Uint8Array(await blob.arrayBuffer());
}

async function assertSameContent(actualBlob, expectedBlob) {
  assert.deepEqual(await blobToBytes(actualBlob), await blobToBytes(expectedBlob));
}

// ---------- base64url ----------

test("base64url: ida e volta devolve os mesmos bytes", () => {
  const bytes = new Uint8Array([0, 1, 250, 251, 252, 253, 254, 255]);

  const text = toBase64Url(bytes);

  assert.match(text, /^[A-Za-z0-9_-]+$/);
  assert.deepEqual(fromBase64Url(text), bytes);
});

// ---------- segredo e chaves ----------

test("segredo gerado tem 12 caracteres e não usa caracteres ambíguos", () => {
  for (let attempt = 0; attempt < 200; attempt++) {
    assert.match(generateRoomSecret(), /^[2-9A-HJKMNP-Z]{12}$/);
  }
});

test("segredos gerados são diferentes entre si", () => {
  assert.notEqual(generateRoomSecret(), generateRoomSecret());
});

test("mesma senha e mesmo salt geram as mesmas chaves", () => {
  const first = deriveRoomKeys("senha", salt);
  const second = deriveRoomKeys("senha", salt);

  assert.deepEqual(first.authKey, second.authKey);
  assert.deepEqual(first.encryptionKey, second.encryptionKey);
});

test("senha ou salt diferentes geram chaves diferentes", () => {
  const base = deriveRoomKeys("senha", salt);

  assert.notDeepEqual(deriveRoomKeys("outra", salt).encryptionKey, base.encryptionKey);
  assert.notDeepEqual(deriveRoomKeys("senha", generateSalt()).encryptionKey, base.encryptionKey);
});

test("authKey e encryptionKey são diferentes (o servidor só vê a authKey)", () => {
  const { authKey, encryptionKey: derivedEncryptionKey } = deriveRoomKeys("senha", salt);

  assert.equal(authKey.length, 32);
  assert.equal(derivedEncryptionKey.length, 32);
  assert.notDeepEqual(authKey, derivedEncryptionKey);
});

// ---------- textos ----------

test("texto: ida e volta, incluindo acentos e emoji", () => {
  const original = "Olá, mundo! Ação 日本語 🔒";

  const encrypted = encryptText(original, encryptionKey);

  assert.equal(decryptText(encrypted, encryptionKey), original);
});

test("texto vazio também funciona", () => {
  assert.equal(decryptText(encryptText("", encryptionKey), encryptionKey), "");
});

test("o mesmo texto criptografado duas vezes gera resultados diferentes", () => {
  assert.notDeepEqual(encryptText("igual", encryptionKey), encryptText("igual", encryptionKey));
});

test("texto: chave errada falha", () => {
  const encrypted = encryptText("segredo", encryptionKey);

  assert.throws(() => decryptText(encrypted, otherKey));
});

test("texto: dado adulterado falha", () => {
  const encrypted = encryptText("segredo", encryptionKey);
  encrypted[encrypted.length - 1] ^= 1;

  assert.throws(() => decryptText(encrypted, encryptionKey));
});

test("texto cifrado não contém o texto original", () => {
  const encrypted = encryptText("PALAVRA-SECRETA-123", encryptionKey);

  const asLatin1 = Buffer.from(encrypted).toString("latin1");
  assert.ok(!asLatin1.includes("PALAVRA-SECRETA-123"));
});

test("objeto (metadados de arquivo): ida e volta", () => {
  const metadata = { name: "relatório.pdf", type: "application/pdf", size: 1234 };

  const encrypted = encryptJson(metadata, encryptionKey);

  assert.deepEqual(decryptJson(encrypted, encryptionKey), metadata);
});

// ---------- arquivos ----------

const fileSizes = [
  ["vazio", 0],
  ["pequeno (1 byte)", 1],
  ["menor que um bloco", 1000],
  ["exatamente um bloco", ONE_MEGABYTE],
  ["um bloco e um byte", ONE_MEGABYTE + 1],
  ["vários blocos (2,5 MB)", Math.floor(2.5 * ONE_MEGABYTE)],
];

for (const [description, size] of fileSizes) {
  test(`arquivo ${description}: ida e volta`, async () => {
    const original = makeRandomBlob(size);

    const encrypted = await encryptFile(original, encryptionKey);
    const decrypted = await decryptFile(encrypted, encryptionKey);

    await assertSameContent(decrypted, original);
  });
}

test("arquivo cifrado não contém o conteúdo original", async () => {
  const marker = "CONTEUDO-SECRETO-DO-ARQUIVO";
  const original = new Blob([marker.repeat(100)]);

  const encrypted = await encryptFile(original, encryptionKey);

  const asLatin1 = Buffer.from(await blobToBytes(encrypted)).toString("latin1");
  assert.ok(!asLatin1.includes(marker));
});

test("arquivo: chave errada falha", async () => {
  const encrypted = await encryptFile(makeRandomBlob(5000), encryptionKey);

  await assert.rejects(decryptFile(encrypted, otherKey));
});

test("arquivo: byte alterado falha", async () => {
  const bytes = await blobToBytes(await encryptFile(makeRandomBlob(5000), encryptionKey));
  bytes[FILE_HEADER_BYTES + 100] ^= 1;

  await assert.rejects(decryptFile(new Blob([bytes]), encryptionKey));
});

test("arquivo: cortado entre blocos falha em vez de entregar arquivo incompleto", async () => {
  const encrypted = await encryptFile(makeRandomBlob(Math.floor(2.5 * ONE_MEGABYTE)), encryptionKey);

  const cutAfterFirstChunk = encrypted.slice(0, FILE_HEADER_BYTES + ENCRYPTED_CHUNK_BYTES);

  await assert.rejects(decryptFile(cutAfterFirstChunk, encryptionKey), /incompleto/);
});

test("arquivo: cortado no meio de um bloco falha", async () => {
  const encrypted = await encryptFile(makeRandomBlob(5000), encryptionKey);

  await assert.rejects(decryptFile(encrypted.slice(0, encrypted.size - 5), encryptionKey));
});

test("arquivo: dados extras depois do bloco final falham", async () => {
  const encrypted = await encryptFile(makeRandomBlob(5000), encryptionKey);
  const withTrailingData = new Blob([encrypted, new Uint8Array(20)]);

  await assert.rejects(decryptFile(withTrailingData, encryptionKey));
});

test("arquivo: dados extras depois de um bloco final completo falham", async () => {
  const encrypted = await encryptFile(makeRandomBlob(ONE_MEGABYTE), encryptionKey);
  const withTrailingData = new Blob([encrypted, new Uint8Array(20)]);

  await assert.rejects(decryptFile(withTrailingData, encryptionKey), /depois do bloco final/);
});

test("arquivo: menor que o cabeçalho falha", async () => {
  await assert.rejects(decryptFile(new Blob([new Uint8Array(10)]), encryptionKey), /pequeno demais/);
});
