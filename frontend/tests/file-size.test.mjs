// Testes de tamanho e nome de arquivo. Rodar a partir da pasta frontend/:  node --test

import assert from "node:assert/strict";
import { test } from "node:test";

import { formatFileSize, safeFileName } from "../static/js/file-size.js";

test("mostra bytes, KB, MB e GB", () => {
  assert.equal(formatFileSize(0, "en"), "0 B");
  assert.equal(formatFileSize(1023, "en"), "1,023 B");
  assert.equal(formatFileSize(1024, "en"), "1 KB");
  assert.equal(formatFileSize(1536, "en"), "1.5 KB");
  assert.equal(formatFileSize(100 * 1024 * 1024, "en"), "100 MB");
  assert.equal(formatFileSize(2.5 * 1024 * 1024 * 1024, "en"), "2.5 GB");
});

test("usa a vírgula decimal em português", () => {
  assert.equal(formatFileSize(1536, "pt"), "1,5 KB");
});

test("nome de arquivo comum não muda", () => {
  assert.equal(safeFileName("relatório final.pdf"), "relatório final.pdf");
  assert.equal(safeFileName("arquivo.com.muitos.pontos.tar.gz"), "arquivo.com.muitos.pontos.tar.gz");
});

test("tira barras e caracteres proibidos", () => {
  assert.equal(safeFileName("../../segredo.txt"), ".._.._segredo.txt");
  assert.equal(safeFileName("C:\\Windows\\sistema.dll"), "C__Windows_sistema.dll");
  assert.equal(safeFileName('a<b>c:"d|e?f*.txt'), "a_b_c__d_e_f_.txt");
});

test("nome vazio ou só de pontos vira um nome padrão", () => {
  assert.equal(safeFileName(""), "quickdrop-file");
  assert.equal(safeFileName("   "), "quickdrop-file");
  assert.equal(safeFileName(".."), "quickdrop-file");
});
