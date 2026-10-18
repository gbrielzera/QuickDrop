// Editor de texto compartilhado: o que um aparelho escreve aparece nos outros, criptografado.
//
// Como duas pessoas podem escrever ao mesmo tempo, o servidor numera cada versão do texto.
// Cada aparelho sabe em qual versão o seu texto se baseia (`baseVersion`):
//   - se ninguém mexeu antes, o servidor aceita e a versão sobe;
//   - se outro aparelho salvou antes, o servidor recusa (409) e a pessoa escolhe qual texto manter.

import { ApiError, getText, putText } from "./api.js";
import { decryptText, encryptText, fromBase64Url, toBase64Url } from "./crypto.js";
import { errorMessageKey } from "./errors.js";
import { formatFileSize } from "./file-size.js";
import { getLanguage } from "./i18n.js";
import { clearMessage, setUpConfirmButton, setUpCopyButton, showMessage } from "./ui.js";

const HTTP_CONFLICT = 409;
// Espera a pessoa parar de digitar por um instante antes de salvar, para não salvar a cada tecla.
const SAVE_DELAY_MILLISECONDS = 600;
const RETRY_AFTER_FAILURE_MILLISECONDS = 5000;

/** Devolve `{ receiveRemote, refresh }`. `maxTextBytes` é o limite de tamanho do texto. */
export function startTextEditor({ roomCode, maxTextBytes, getEncryptionKey }) {
  const textarea = document.getElementById("shared-text");
  const statusElement = document.getElementById("text-status");
  const copyStatusElement = document.getElementById("text-copy-status");
  const conflictBox = document.getElementById("text-conflict");
  const useTheirsButton = document.getElementById("use-theirs");
  const keepMineButton = document.getElementById("keep-mine");
  const clearButton = document.getElementById("clear-text");

  let baseVersion = 0; // versão do servidor em que o nosso texto se baseia
  let savedText = ""; // o texto que o servidor tem nessa versão
  let sentText = null; // o texto que está sendo salvo agora (para reconhecer o eco do nosso próprio envio)
  let isSaving = false;
  let saveTimer = null;
  let pendingConflict = null; // { text, version } do outro aparelho, enquanto a pessoa não escolhe

  function decrypt(ciphertext) {
    return ciphertext === "" ? "" : decryptText(fromBase64Url(ciphertext), getEncryptionKey());
  }

  function hasUnsavedChanges() {
    return textarea.value !== savedText;
  }

  function setStatus(messageKey, values) {
    showMessage(statusElement, messageKey, values);
  }

  function setTextKeepingCursor(text) {
    const { selectionStart, selectionEnd } = textarea;
    textarea.value = text;
    textarea.setSelectionRange(Math.min(selectionStart, text.length), Math.min(selectionEnd, text.length));
  }

  // ---------- salvar ----------

  function scheduleSave(delay = SAVE_DELAY_MILLISECONDS) {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, delay);
  }

  async function save() {
    clearTimeout(saveTimer);
    if (isSaving || pendingConflict || !hasUnsavedChanges()) {
      return;
    }
    const text = textarea.value;
    if (new TextEncoder().encode(text).length > maxTextBytes) {
      setStatus("error.textTooLarge", { textSize: formatFileSize(maxTextBytes, getLanguage()) });
      return;
    }

    isSaving = true;
    sentText = text;
    setStatus("text.saving");
    try {
      const encrypted = toBase64Url(encryptText(text, getEncryptionKey()));
      const saved = await putText(roomCode, encrypted, baseVersion);
      baseVersion = saved.version;
      savedText = text;
    } catch (error) {
      isSaving = false;
      if (error instanceof ApiError && error.status === HTTP_CONFLICT) {
        showConflict(error.detail.current);
        return;
      }
      setStatus(errorMessageKey(error));
      scheduleSave(RETRY_AFTER_FAILURE_MILLISECONDS);
      return;
    }
    isSaving = false;
    if (hasUnsavedChanges()) {
      scheduleSave(); // a pessoa continuou escrevendo enquanto salvávamos
    } else {
      setStatus("text.synced");
    }
  }

  // ---------- conflito: outro aparelho salvou antes ----------

  function showConflict({ ciphertext, version }) {
    pendingConflict = { text: decrypt(ciphertext), version };
    conflictBox.hidden = false;
    setStatus("text.conflict");
  }

  function closeConflict() {
    pendingConflict = null;
    conflictBox.hidden = true;
  }

  function useTheirVersion() {
    const { text, version } = pendingConflict;
    closeConflict();
    setTextKeepingCursor(text);
    savedText = text;
    baseVersion = version;
    setStatus("text.synced");
  }

  function keepMyVersion() {
    baseVersion = pendingConflict.version; // agora o servidor aceita o nosso texto por cima
    closeConflict();
    save();
  }

  // ---------- receber o texto de outro aparelho ----------

  /** Recebe `{ ciphertext, version }` do servidor (aviso em tempo real ou consulta). */
  function receiveRemote({ ciphertext, version }) {
    if (pendingConflict) {
      if (version > pendingConflict.version) {
        pendingConflict = { text: decrypt(ciphertext), version };
      }
      return;
    }
    if (version <= baseVersion) {
      return; // já temos esta versão (ou uma mais nova)
    }

    const remoteText = decrypt(ciphertext);
    if (isSaving && remoteText === sentText) {
      return; // é o eco do que nós mesmos estamos salvando; a resposta do servidor atualiza a versão
    }
    if (remoteText === textarea.value) {
      savedText = remoteText;
      baseVersion = version;
      return;
    }
    if (hasUnsavedChanges() || isSaving) {
      showConflict({ ciphertext, version }); // a pessoa está escrevendo: ela decide
      return;
    }
    setTextKeepingCursor(remoteText);
    savedText = remoteText;
    baseVersion = version;
    setStatus("text.synced");
  }

  /** Consulta o servidor e atualiza o texto (usado ao abrir a sala e depois de reconectar). */
  async function refresh() {
    try {
      receiveRemote(await getText(roomCode));
    } catch (error) {
      setStatus(errorMessageKey(error));
    }
  }

  // ---------- ligar a tela ----------

  textarea.addEventListener("input", () => {
    if (pendingConflict) {
      return;
    }
    setStatus("text.unsaved");
    scheduleSave();
  });
  // Se a tela do celular apagar ou a aba for para o fundo, salva o que ainda faltava.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      save();
    }
  });

  useTheirsButton.addEventListener("click", useTheirVersion);
  keepMineButton.addEventListener("click", keepMyVersion);
  setUpCopyButton(document.getElementById("copy-text"), () => textarea.value, copyStatusElement);
  setUpConfirmButton(clearButton, "text.clearConfirm", () => {
    clearMessage(copyStatusElement);
    textarea.value = "";
    setStatus("text.unsaved");
    save();
  });

  return { receiveRemote, refresh };
}
