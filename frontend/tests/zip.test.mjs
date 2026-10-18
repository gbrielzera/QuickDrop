// Testes do .zip e dos nomes/tipos de arquivo. Rodar a partir da pasta frontend/:  node --test

import assert from "node:assert/strict";
import { test } from "node:test";

import { isPreviewableImage, MAX_PREVIEW_BYTES, pastedFileName } from "../static/js/file-types.js";
import { crc32, createZip, toDosDateTime, uniqueNames } from "../static/js/zip.js";

// ---------- leitor de zip só para os testes: confere se o que criamos é um zip válido ----------

function readZip(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const endOffset = bytes.length - 22; // sem comentário, o fim do diretório tem sempre 22 bytes
  assert.equal(view.getUint32(endOffset, true), 0x06054b50, "assinatura do fim do diretório");
  const entryCount = view.getUint16(endOffset + 10, true);
  let centralOffset = view.getUint32(endOffset + 16, true);

  const entries = [];
  for (let index = 0; index < entryCount; index++) {
    assert.equal(view.getUint32(centralOffset, true), 0x02014b50, "assinatura da entrada central");
    const crc = view.getUint32(centralOffset + 16, true);
    const size = view.getUint32(centralOffset + 24, true);
    const nameLength = view.getUint16(centralOffset + 28, true);
    const localOffset = view.getUint32(centralOffset + 42, true);
    const name = new TextDecoder().decode(bytes.subarray(centralOffset + 46, centralOffset + 46 + nameLength));

    assert.equal(view.getUint32(localOffset, true), 0x04034b50, "assinatura do cabeçalho local");
    const localNameLength = view.getUint16(localOffset + 26, true);
    const dataStart = localOffset + 30 + localNameLength;
    entries.push({ name, crc, size, data: bytes.subarray(dataStart, dataStart + size) });
    centralOffset += 46 + nameLength;
  }
  return entries;
}

async function zipToEntries(files) {
  const zip = await createZip(files);
  return readZip(new Uint8Array(await zip.arrayBuffer()));
}

const SOME_DATE = new Date(2026, 9, 18, 14, 30, 6);

// ---------- CRC e datas ----------

test("crc32 bate com o valor de referência do padrão", () => {
  assert.equal(crc32(new TextEncoder().encode("123456789")), 0xcbf43926);
  assert.equal(crc32(new Uint8Array(0)), 0);
});

test("a data do zip usa o formato de 16 bits do MS-DOS", () => {
  const { date, time } = toDosDateTime(SOME_DATE);

  assert.equal(date, ((2026 - 1980) << 9) | (10 << 5) | 18);
  assert.equal(time, (14 << 11) | (30 << 5) | 3);
});

// ---------- nomes ----------

test("nomes repetidos ganham um número antes da extensão", () => {
  assert.deepEqual(uniqueNames(["a.png", "b.txt", "a.png", "a.png"]), ["a.png", "b.txt", "a (2).png", "a (3).png"]);
});

test("nomes repetidos sem extensão e arquivos que começam com ponto", () => {
  assert.deepEqual(uniqueNames(["LEIAME", "LEIAME"]), ["LEIAME", "LEIAME (2)"]);
  assert.deepEqual(uniqueNames([".env", ".env"]), [".env", ".env (2)"]);
});

// ---------- o zip ----------

test("o zip guarda cada arquivo com nome, tamanho e conteúdo certos", async () => {
  const entries = await zipToEntries([
    { name: "texto.txt", blob: new Blob(["Olá, mundo!"]), date: SOME_DATE },
    { name: "dados.bin", blob: new Blob([new Uint8Array([0, 1, 2, 255, 254])]), date: SOME_DATE },
  ]);

  assert.deepEqual(
    entries.map((entry) => [entry.name, entry.size]),
    [
      ["texto.txt", 12],
      ["dados.bin", 5],
    ],
  );
  assert.equal(new TextDecoder().decode(entries[0].data), "Olá, mundo!");
  assert.deepEqual([...entries[1].data], [0, 1, 2, 255, 254]);
});

test("a soma de verificação de cada arquivo confere", async () => {
  const entries = await zipToEntries([
    { name: "a.txt", blob: new Blob(["123456789"]), date: SOME_DATE },
    { name: "b.txt", blob: new Blob(["outro conteúdo"]), date: SOME_DATE },
  ]);

  for (const entry of entries) {
    assert.equal(crc32(entry.data), entry.crc, entry.name);
  }
});

test("nomes com acentos e espaços ficam em UTF-8", async () => {
  const entries = await zipToEntries([{ name: "relatório final ção.pdf", blob: new Blob(["x"]), date: SOME_DATE }]);

  assert.equal(entries[0].name, "relatório final ção.pdf");
});

test("arquivo vazio e arquivo maior que um bloco de criptografia", async () => {
  const big = new Uint8Array(1024 * 1024 + 7).map((_, index) => index % 251);
  const entries = await zipToEntries([
    { name: "vazio", blob: new Blob([]), date: SOME_DATE },
    { name: "grande", blob: new Blob([big]), date: SOME_DATE },
  ]);

  assert.equal(entries[0].size, 0);
  assert.deepEqual(entries[1].data, big);
});

test("um zip sem arquivos ainda é um zip válido", async () => {
  assert.deepEqual(await zipToEntries([]), []);
});

test("o tipo do arquivo gerado é application/zip", async () => {
  assert.equal((await createZip([])).type, "application/zip");
});

// ---------- pré-visualização e nome de imagem colada ----------

test("só imagens seguras e de tamanho razoável são pré-visualizadas", () => {
  assert.equal(isPreviewableImage("image/png", 1000), true);
  assert.equal(isPreviewableImage("image/jpeg", MAX_PREVIEW_BYTES), true);
  assert.equal(isPreviewableImage("image/jpeg", MAX_PREVIEW_BYTES + 1), false);
});

test("SVG, HTML e outros tipos nunca são pré-visualizados", () => {
  assert.equal(isPreviewableImage("image/svg+xml", 100), false);
  assert.equal(isPreviewableImage("text/html", 100), false);
  assert.equal(isPreviewableImage("application/pdf", 100), false);
  assert.equal(isPreviewableImage("", 100), false);
});

test("imagem colada ganha nome com data e hora", () => {
  const screenshot = new File([], "image.png", { type: "image/png" });

  assert.equal(pastedFileName(screenshot, SOME_DATE), "captura-20261018-143006.png");
});

test("a extensão do nome acompanha o tipo da imagem", () => {
  assert.equal(pastedFileName({ name: "image.png", type: "image/jpeg" }, SOME_DATE), "captura-20261018-143006.jpg");
  assert.equal(pastedFileName({ name: "", type: "image/webp" }, SOME_DATE), "captura-20261018-143006.webp");
  assert.equal(pastedFileName({ name: "", type: "" }, SOME_DATE), "captura-20261018-143006.bin");
});

test("arquivo copiado do computador mantém o nome", () => {
  assert.equal(pastedFileName({ name: "relatório.pdf", type: "application/pdf" }, SOME_DATE), "relatório.pdf");
  assert.equal(pastedFileName({ name: "foto-da-praia.png", type: "image/png" }, SOME_DATE), "foto-da-praia.png");
});

test("o zip nunca grava um nome com caminho", async () => {
  const files = [{ name: "../../evil.txt", blob: new Blob(["x"]), date: new Date(2026, 0, 1) }];

  const entries = await zipToEntries(files);

  assert.equal(entries[0].name, ".._.._evil.txt");
});
