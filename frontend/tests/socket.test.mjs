// Testes do tempo de espera entre reconexões. Rodar a partir da pasta frontend/:  node --test

import assert from "node:assert/strict";
import { test } from "node:test";

import { reconnectDelay } from "../static/js/socket.js";

test("a espera dobra a cada tentativa", () => {
  assert.equal(reconnectDelay(0), 1000);
  assert.equal(reconnectDelay(1), 2000);
  assert.equal(reconnectDelay(2), 4000);
  assert.equal(reconnectDelay(3), 8000);
  assert.equal(reconnectDelay(4), 16000);
});

test("a espera nunca passa de 30 segundos", () => {
  assert.equal(reconnectDelay(5), 30000);
  assert.equal(reconnectDelay(50), 30000);
});
