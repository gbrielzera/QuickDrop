// Troca de idioma (português e inglês).
//
// No HTML, um elemento com data-i18n="chave" tem o texto trocado pela tradução.
// Também funcionam data-i18n-placeholder e data-i18n-aria-label.

import { messages } from "./messages.js";

const STORAGE_KEY = "quickdrop:language";
const DEFAULT_LANGUAGE = "pt";
const LANGUAGE_CHANGED_EVENT = "languagechange";

let currentLanguage = detectLanguage();

function detectLanguage() {
  try {
    const savedLanguage = localStorage.getItem(STORAGE_KEY);
    if (savedLanguage in messages) {
      return savedLanguage;
    }
  } catch {
    // Sem acesso ao localStorage (modo privado, por exemplo): segue para o idioma do navegador.
  }
  return navigator.language.toLowerCase().startsWith("en") ? "en" : DEFAULT_LANGUAGE;
}

/** Idioma atual: "pt" ou "en". */
export function getLanguage() {
  return currentLanguage;
}

/** Devolve o texto da chave no idioma atual. Valores como {time} são trocados pelos de `values`. */
export function t(key, values = {}) {
  const template = messages[currentLanguage][key] ?? messages[DEFAULT_LANGUAGE][key] ?? key;
  return template.replace(/\{(\w+)\}/g, (placeholder, name) => values[name] ?? placeholder);
}

function translateAttribute(root, attributeName, targetAttribute) {
  for (const element of root.querySelectorAll(`[${attributeName}]`)) {
    element.setAttribute(targetAttribute, t(element.getAttribute(attributeName)));
  }
}

/** Troca os textos marcados com data-i18n dentro de `root`. */
export function applyTranslations(root = document) {
  for (const element of root.querySelectorAll("[data-i18n]")) {
    element.textContent = t(element.dataset.i18n);
  }
  translateAttribute(root, "data-i18n-placeholder", "placeholder");
  translateAttribute(root, "data-i18n-aria-label", "aria-label");
}

function markActiveLanguageButton() {
  for (const button of document.querySelectorAll("[data-language]")) {
    button.setAttribute("aria-pressed", String(button.dataset.language === currentLanguage));
  }
}

function changeLanguage(language) {
  currentLanguage = language;
  try {
    localStorage.setItem(STORAGE_KEY, language);
  } catch {
    // Não conseguiu lembrar a escolha, mas a troca vale para esta visita.
  }
  document.documentElement.lang = language === "en" ? "en" : "pt-BR";
  applyTranslations();
  markActiveLanguageButton();
  // Quem mostra textos montados em JavaScript (erros, tempo restante) escuta este evento e refaz o texto.
  document.dispatchEvent(new CustomEvent(LANGUAGE_CHANGED_EVENT));
}

/** Liga os botões [data-language] e aplica o idioma atual à página. */
export function startLanguageSwitcher() {
  for (const button of document.querySelectorAll("[data-language]")) {
    button.addEventListener("click", () => changeLanguage(button.dataset.language));
  }
  changeLanguage(currentLanguage);
}

/** Chama `callback` sempre que o idioma mudar. */
export function onLanguageChange(callback) {
  document.addEventListener(LANGUAGE_CHANGED_EVENT, callback);
}
