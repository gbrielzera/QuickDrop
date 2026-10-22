// Regras puras do tema (sem tocar na página): quais temas existem e qual é o oposto.

const LIGHT = "light";
const DARK = "dark";

/** True se `value` é um tema válido ("light" ou "dark"). */
export function isTheme(value) {
  return value === LIGHT || value === DARK;
}

/** O tema para onde o botão leva: do claro para o escuro e vice-versa. */
export function oppositeTheme(theme) {
  return theme === DARK ? LIGHT : DARK;
}
