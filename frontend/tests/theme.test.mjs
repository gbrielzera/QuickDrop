import assert from "node:assert/strict";
import { test } from "node:test";

import { isTheme, oppositeTheme } from "../static/js/theme.js";

test("só claro e escuro são temas válidos", () => {
  assert.equal(isTheme("light"), true);
  assert.equal(isTheme("dark"), true);
  assert.equal(isTheme("auto"), false);
  assert.equal(isTheme(undefined), false);
  assert.equal(isTheme(""), false);
});

test("o botão leva do claro para o escuro e do escuro para o claro", () => {
  assert.equal(oppositeTheme("light"), "dark");
  assert.equal(oppositeTheme("dark"), "light");
});
