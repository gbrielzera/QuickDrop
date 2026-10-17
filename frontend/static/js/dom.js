// Cria elementos HTML sem usar innerHTML: o que vem de outros aparelhos (como nomes de arquivo)
// entra sempre como texto puro, então nunca vira código.

import { t } from "./i18n.js";

/**
 * Cria um elemento.
 * - className: classes CSS.
 * - text: texto puro.
 * - i18nKey: chave de tradução (o texto acompanha a troca de idioma).
 * - attributes: outros atributos, ex.: { type: "button" }.
 */
export function createElement(tagName, { className, text, i18nKey, attributes = {} } = {}, children = []) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  if (i18nKey) {
    element.dataset.i18n = i18nKey;
    element.textContent = t(i18nKey);
  } else if (text !== undefined) {
    element.textContent = text;
  }
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, value);
  }
  element.append(...children);
  return element;
}
