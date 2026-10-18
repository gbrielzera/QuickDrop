// Painel "Clips": textos curtos colados na sala, cada um com botão de copiar.
// Serve para passar um link, uma senha ou um trecho de texto de um aparelho para outro.

import { ApiError } from "./api.js";
import { decryptText, encryptText, fromBase64Url, toBase64Url } from "./crypto.js";
import { createElement } from "./dom.js";
import { errorMessageKey } from "./errors.js";
import { formatFileSize } from "./file-size.js";
import { getLanguage, onLanguageChange, t } from "./i18n.js";
import { clearMessage, runWithBusyButton, setUpConfirmButton, setUpCopyButton, showMessage } from "./ui.js";

const HTTP_NOT_FOUND = 404;

/** Transforma o clip guardado no servidor em algo que a tela entende. Se a chave não conferir, `readable` é false. */
function readClipEntry(storedClip, encryptionKey) {
  try {
    const text = decryptText(fromBase64Url(storedClip.ciphertext), encryptionKey);
    return { id: storedClip.id, readable: true, text };
  } catch {
    return { id: storedClip.id, readable: false, text: "" };
  }
}

/**
 * Liga um painel de clips (o de textos ou o de blocos de código). Devolve `{ addStoredClip, removeEntry, load }`.
 * - ids: os `id` dos elementos da tela (input, saveButton, empty, list, status).
 * - api: `{ list, create, remove }`, as funções que falam com o servidor.
 * - maxClipBytes: o limite de tamanho de cada clip.
 * - isCode: true no painel de código. O clip aparece em fonte monoespaçada e, como Ctrl+V fora de um campo
 *   não sabe se o que foi colado é texto ou código, só o painel de textos reage a ele.
 */
export function startClipsPanel({ roomCode, ids, api, maxClipBytes, getEncryptionKey, isCode = false }) {
  const input = document.getElementById(ids.input);
  const saveButton = document.getElementById(ids.saveButton);
  const emptyMessage = document.getElementById(ids.empty);
  const list = document.getElementById(ids.list);
  const statusElement = document.getElementById(ids.status);

  const rowsById = new Map();

  function showEmptyMessageWhenNoClips() {
    emptyMessage.hidden = rowsById.size > 0;
  }

  /** Chave de tradução do erro de uma ação sobre um clip. */
  function clipErrorKey(error) {
    if (error instanceof ApiError && error.status === HTTP_NOT_FOUND) return "error.clipGone";
    return errorMessageKey(error);
  }

  // ---------- uma linha da lista ----------

  function createClipRow(entry) {
    const textElement = createElement("pre", { className: isCode ? "clip__text clip__text--code" : "clip__text" });
    const rowStatus = createElement("p", { className: "status", attributes: { role: "status" } });
    const actions = createElement("div", { className: "file__actions" });
    const element = createElement("li", { className: "clip" }, [textElement, actions, rowStatus]);

    function removeRow() {
      element.remove();
      rowsById.delete(entry.id);
      showEmptyMessageWhenNoClips();
    }

    if (entry.readable) {
      const copyButton = createElement("button", {
        className: "button button--outline button--small",
        i18nKey: "action.copy",
        attributes: { type: "button" },
      });
      setUpCopyButton(copyButton, () => entry.text, rowStatus);
      actions.append(copyButton);
    }

    const deleteButton = createElement("button", {
      className: "button button--outline button--small",
      i18nKey: "action.delete",
      attributes: { type: "button" },
    });
    setUpConfirmButton(deleteButton, "action.deleteConfirm", async (button) => {
      rowStatus.classList.remove("status--error");
      clearMessage(rowStatus);
      try {
        await runWithBusyButton(button, "action.deleting", () => api.remove(roomCode, entry.id));
        removeRow();
      } catch (error) {
        if (error instanceof ApiError && error.status === HTTP_NOT_FOUND) {
          removeRow(); // já não existia (outro aparelho apagou)
          return;
        }
        rowStatus.classList.add("status--error");
        showMessage(rowStatus, clipErrorKey(error));
      }
    });
    actions.append(deleteButton);

    const row = {
      element,
      remove: removeRow,
      render() {
        textElement.textContent = entry.readable ? entry.text : t("clips.unreadable");
      },
    };
    row.render();
    return row;
  }

  // ---------- usar a lista ----------

  function addEntry(entry) {
    if (rowsById.has(entry.id)) {
      return;
    }
    const row = createClipRow(entry);
    rowsById.set(entry.id, row);
    list.prepend(row.element); // o mais novo fica no alto
    showEmptyMessageWhenNoClips();
  }

  /** Mostra um clip como o servidor o guarda (criptografado). */
  function addStoredClip(storedClip) {
    addEntry(readClipEntry(storedClip, getEncryptionKey()));
  }

  function removeEntry(clipId) {
    rowsById.get(clipId)?.remove();
  }

  async function load() {
    try {
      const storedClips = await api.list(roomCode);
      const entries = storedClips.map((storedClip) => readClipEntry(storedClip, getEncryptionKey()));
      // Reconcilia com o servidor: some o que foi apagado enquanto estávamos sem conexão e entra o que chegou.
      const idsOnServer = new Set(entries.map((entry) => entry.id));
      for (const clipId of [...rowsById.keys()]) {
        if (!idsOnServer.has(clipId)) {
          removeEntry(clipId);
        }
      }
      entries.forEach(addEntry);
    } catch (error) {
      showMessage(statusElement, errorMessageKey(error));
    }
    showEmptyMessageWhenNoClips();
  }

  // ---------- guardar um clip novo ----------

  /** Criptografa e guarda `text` como clip. Devolve true se guardou. */
  async function saveClip(text) {
    clearMessage(statusElement);
    if (new TextEncoder().encode(text).length > maxClipBytes) {
      showMessage(statusElement, "error.clipTooLarge", { clipSize: formatFileSize(maxClipBytes, getLanguage()) });
      return false;
    }
    try {
      const encrypted = toBase64Url(encryptText(text, getEncryptionKey()));
      const storedClip = await api.create(roomCode, encrypted);
      addStoredClip(storedClip);
      return true;
    } catch (error) {
      showMessage(statusElement, errorMessageKey(error), { clipSize: formatFileSize(maxClipBytes, getLanguage()) });
      return false;
    }
  }

  saveButton.addEventListener("click", async () => {
    if (input.value.trim() === "") {
      input.focus();
      return;
    }
    const saved = await runWithBusyButton(saveButton, "clips.saving", () => saveClip(input.value));
    if (saved) {
      input.value = "";
    }
  });

  // Ctrl+V fora de qualquer campo vira um clip de texto na hora.
  if (!isCode) {
    document.addEventListener("paste", (event) => {
      if (event.target.closest("input, textarea, [contenteditable]")) {
        return;
      }
      const pastedText = event.clipboardData?.getData("text/plain") ?? "";
      if (pastedText.trim() === "") {
        return;
      }
      event.preventDefault();
      saveClip(pastedText);
    });
  }

  onLanguageChange(() => {
    for (const row of rowsById.values()) {
      row.render();
    }
  });

  return { addStoredClip, removeEntry, load };
}
