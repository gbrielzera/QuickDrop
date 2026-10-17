// Pequenas ajudas para mexer na página: mensagens, botões ocupados e botão "copiar".

import { t } from "./i18n.js";
import { copyText } from "./copy-text.js";

const COPIED_FEEDBACK_MILLISECONDS = 2000;

/** Mostra uma mensagem (ex.: erro) a partir de uma chave de tradução. Ela muda de idioma junto com a página. */
export function showMessage(element, messageKey) {
  element.dataset.i18n = messageKey;
  element.textContent = t(messageKey);
}

export function clearMessage(element) {
  delete element.dataset.i18n;
  element.textContent = "";
}

/** Desativa o botão e troca o texto dele enquanto `task` roda. Devolve o resultado de `task`. */
export async function runWithBusyButton(button, busyMessageKey, task) {
  const idleMessageKey = button.dataset.i18n;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.dataset.i18n = busyMessageKey;
  button.textContent = t(busyMessageKey);
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.dataset.i18n = idleMessageKey;
    button.textContent = t(idleMessageKey);
  }
}

/** Faz o botão copiar o texto que `getText` devolve e mostra "Copiado" por um instante. */
export function setUpCopyButton(button, getText, statusElement) {
  const idleMessageKey = button.dataset.i18n;
  button.addEventListener("click", async () => {
    const copied = await copyText(getText());
    if (!copied) {
      showMessage(statusElement, "room.copyFailed");
      return;
    }
    showMessage(statusElement, "room.copied");
    button.dataset.i18n = "room.copied";
    button.textContent = t("room.copied");
    setTimeout(() => {
      clearMessage(statusElement);
      button.dataset.i18n = idleMessageKey;
      button.textContent = t(idleMessageKey);
    }, COPIED_FEEDBACK_MILLISECONDS);
  });
}
