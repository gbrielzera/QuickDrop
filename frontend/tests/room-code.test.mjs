// Testes das funções puras de código de sala e de tempo. Rodar a partir da pasta frontend/:  node --test

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildRoomPath,
  formatRoomCode,
  isValidRoomCode,
  isValidSecret,
  parseRoomCodeInput,
  readSecretFromHash,
} from "../static/js/room-code.js";
import { splitTimeLeft } from "../static/js/time-left.js";

test("lê o código completo com hífens, espaços e minúsculas", () => {
  assert.deepEqual(parseRoomCodeInput("k7p3xm-hq4t-9wzc-mpn2"), { code: "K7P3XM", secret: "HQ4T9WZCMPN2" });
  assert.deepEqual(parseRoomCodeInput("  K7P3XM HQ4T 9WZC MPN2 "), { code: "K7P3XM", secret: "HQ4T9WZCMPN2" });
});

test("lê só o código da sala, sem segredo", () => {
  assert.deepEqual(parseRoomCodeInput("K7P3XM"), { code: "K7P3XM", secret: "" });
});

test("código incompleto fica com menos de 6 caracteres", () => {
  assert.deepEqual(parseRoomCodeInput("K7P"), { code: "K7P", secret: "" });
  assert.deepEqual(parseRoomCodeInput(""), { code: "", secret: "" });
});

test("valida o código da sala e o segredo", () => {
  assert.equal(isValidRoomCode("K7P3XM"), true);
  assert.equal(isValidRoomCode("K7P3X"), false);
  assert.equal(isValidRoomCode("K7P3XO"), false); // "O" não existe no alfabeto
  assert.equal(isValidSecret("HQ4T9WZCMPN2"), true);
  assert.equal(isValidSecret("HQ4T9WZCMPN"), false);
  assert.equal(isValidSecret("HQ4T9WZCMPN1"), false); // "1" não existe no alfabeto
});

test("monta o código para digitar", () => {
  assert.equal(formatRoomCode("K7P3XM", "HQ4T9WZCMPN2"), "K7P3XM-HQ4T-9WZC-MPN2");
  assert.equal(formatRoomCode("K7P3XM", ""), "K7P3XM");
});

test("monta o caminho da sala com o segredo depois do #", () => {
  assert.equal(buildRoomPath("K7P3XM", "HQ4T9WZCMPN2"), "/r/K7P3XM#k=HQ4T9WZCMPN2");
  assert.equal(buildRoomPath("K7P3XM", ""), "/r/K7P3XM");
});

test("lê o segredo do fragmento da URL", () => {
  assert.equal(readSecretFromHash("#k=hq4t9wzcmpn2"), "HQ4T9WZCMPN2");
  assert.equal(readSecretFromHash(""), "");
  assert.equal(readSecretFromHash("#outra=coisa"), "");
});

test("divide o tempo que falta em horas e minutos", () => {
  assert.deepEqual(splitTimeLeft((11 * 60 + 42) * 60 * 1000), { hours: 11, minutes: 42 });
  assert.deepEqual(splitTimeLeft(59 * 1000), { hours: 0, minutes: 0 });
  assert.deepEqual(splitTimeLeft(-5000), { hours: 0, minutes: 0 });
});
