// Testes da indentação do campo de código. Rodar a partir da pasta frontend/:  node --test

import assert from "node:assert/strict";
import { test } from "node:test";

import { changeIndentation } from "../static/js/code-keys.js";

// Aplica a mudança ao texto, como o campo faria, e devolve o texto novo e a seleção.
function press(text, start, end, outdent = false) {
  const change = changeIndentation(text, start, end, outdent);
  const newText = text.slice(0, change.replaceStart) + change.replacement + text.slice(change.replaceEnd);
  return { text: newText, start: change.selectionStart, end: change.selectionEnd };
}

test("Tab sem seleção insere quatro espaços no cursor", () => {
  assert.deepEqual(press("abc", 1, 1), { text: "a    bc", start: 5, end: 5 });
  assert.deepEqual(press("", 0, 0), { text: "    ", start: 4, end: 4 });
});

test("Tab com várias linhas selecionadas indenta todas", () => {
  const result = press("a\nb\nc", 0, 5);

  assert.equal(result.text, "    a\n    b\n    c");
  assert.equal(result.start, 4);
  assert.equal(result.end, 17);
});

test("Tab com seleção no meio de uma linha indenta a linha inteira", () => {
  const result = press("primeira\nsegunda", 3, 5);

  assert.equal(result.text, "    primeira\nsegunda");
  assert.equal(result.start, 7);
  assert.equal(result.end, 9);
});

test("linhas vazias não ganham espaços no fim", () => {
  assert.equal(press("a\n\nb", 0, 4).text, "    a\n\n    b");
});

test("a linha seguinte não é indentada quando a seleção termina na quebra de linha", () => {
  assert.equal(press("a\nb\nc", 0, 4).text, "    a\n    b\nc");
});

test("Shift+Tab tira até quatro espaços de cada linha", () => {
  const result = press("    a\n  b\nc", 0, 11, true);

  assert.equal(result.text, "a\nb\nc");
  assert.equal(result.start, 0);
});

test("Shift+Tab tira só a indentação de um nível", () => {
  assert.equal(press("        a", 0, 0, true).text, "    a");
});

test("Shift+Tab tira uma tabulação", () => {
  assert.equal(press("\t\ta", 0, 0, true).text, "\ta");
});

test("Shift+Tab sem seleção tira a indentação da linha do cursor e o cursor acompanha", () => {
  const result = press("x\n    y", 7, 7, true);

  assert.deepEqual(result, { text: "x\ny", start: 3, end: 3 });
});

test("Shift+Tab numa linha sem indentação não muda nada", () => {
  const result = press("a\nb", 2, 2, true);

  assert.deepEqual(result, { text: "a\nb", start: 2, end: 2 });
});

test("o texto de código é preservado exatamente fora das linhas alteradas", () => {
  const code = "def f():\n    if x:\n        return 1\n\n    return 0\n";
  const result = press(code, 9, 28);

  assert.equal(result.text, "def f():\n        if x:\n            return 1\n\n    return 0\n");
});
