// Botão do topo que troca entre o tema claro e o escuro. Sem escolha, a página segue o tema do aparelho;
// depois do primeiro clique, a escolha é lembrada neste navegador.

import { isTheme, oppositeTheme } from "./theme.js";

const STORAGE_KEY = "quickdrop:theme";
// Mesmas cores do fundo da página; o navegador usa para pintar a barra do topo (celular).
const BROWSER_BAR_COLORS = { light: "#fbf7f2", dark: "#17141f" };

const systemDarkQuery = matchMedia("(prefers-color-scheme: dark)");

function currentTheme() {
  const chosenTheme = document.documentElement.dataset.theme;
  if (isTheme(chosenTheme)) {
    return chosenTheme;
  }
  return systemDarkQuery.matches ? "dark" : "light";
}

function markButtons() {
  const isDark = currentTheme() === "dark";
  for (const button of document.querySelectorAll(".theme-toggle")) {
    button.setAttribute("aria-pressed", String(isDark));
  }
}

function paintBrowserBar(theme) {
  for (const meta of document.querySelectorAll('meta[name="theme-color"]')) {
    meta.setAttribute("content", BROWSER_BAR_COLORS[theme]);
  }
}

function chooseTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Não conseguiu lembrar a escolha, mas a troca vale para esta visita.
  }
  paintBrowserBar(theme);
  markButtons();
}

for (const button of document.querySelectorAll(".theme-toggle")) {
  button.addEventListener("click", () => chooseTheme(oppositeTheme(currentTheme())));
}
// Se a pessoa nunca escolheu, acompanha mudanças do aparelho (por exemplo, o modo escuro automático à noite).
systemDarkQuery.addEventListener("change", markButtons);
markButtons();
