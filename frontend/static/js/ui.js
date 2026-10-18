// Pequenas ajudas para mexer na página: mensagens, botões ocupados e botão "copiar".

import { t } from "./i18n.js";
import { copyText } from "./copy-text.js";

const COPIED_FEEDBACK_MILLISECONDS = 2000;
// Ações que apagam pedem uma segunda confirmação; se a pessoa não confirmar, o botão volta ao normal.
const CONFIRMATION_MILLISECONDS = 4000;

/**
 * Mostra uma mensagem (ex.: erro) a partir de uma chave de tradução.
 * Ela muda de idioma junto com a página. `values` preenche partes como "{textSize}".
 */
export function showMessage(element, messageKey, values = {}) {
  element.dataset.i18n = messageKey;
  element.dataset.i18nValues = JSON.stringify(values);
  element.textContent = t(messageKey, values);
}

export function clearMessage(element) {
  delete element.dataset.i18n;
  delete element.dataset.i18nValues;
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

/**
 * Faz o botão pedir confirmação: o primeiro clique troca o texto por `confirmMessageKey`
 * (em vermelho) e o segundo clique executa `onConfirm`. Sem o segundo clique, volta ao normal.
 */
export function setUpConfirmButton(button, confirmMessageKey, onConfirm) {
  const idleMessageKey = button.dataset.i18n;
  let timer = null;

  function showMessageKey(messageKey) {
    button.dataset.i18n = messageKey;
    button.textContent = t(messageKey);
  }

  button.addEventListener("click", () => {
    if (timer === null) {
      showMessageKey(confirmMessageKey);
      button.classList.add("button--danger");
      timer = setTimeout(() => {
        timer = null;
        showMessageKey(idleMessageKey);
        button.classList.remove("button--danger");
      }, CONFIRMATION_MILLISECONDS);
      return;
    }
    clearTimeout(timer);
    timer = null;
    showMessageKey(idleMessageKey);
    button.classList.remove("button--danger");
    onConfirm(button);
  });
}
