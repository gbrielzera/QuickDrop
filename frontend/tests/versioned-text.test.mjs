// Testes do vínculo entre o texto e a versão. Rodar a partir da pasta frontend/:  node --test tests/

import assert from "node:assert/strict";
import { test } from "node:test";

import { attachVersion, detachVersion } from "../static/js/versioned-text.js";

test("o texto volta igual quando a versão confere", () => {
  assert.equal(detachVersion(attachVersion("olá\nmundo", 3), 3), "olá\nmundo");
});

test("texto vazio também funciona", () => {
  assert.equal(detachVersion(attachVersion("", 1), 1), "");
});

test("um texto de outra versão é recusado", () => {
  assert.throws(() => detachVersion(attachVersion("antigo", 2), 5), /versão/);
});

test("um texto sem versão é recusado", () => {
  assert.throws(() => detachVersion("sem versão nenhuma", 1), /versão/);
});
