// Painel "Na sala": a lista de arquivos, com baixar e excluir.

import { ApiError, deleteFile, listFiles } from "./api.js";
import { createElement } from "./dom.js";
import { errorMessageKey } from "./errors.js";
import { formatFileSize } from "./file-size.js";
import { fetchDecryptedFile, readFileEntry, saveBlobAsFile } from "./file-transfer.js";
import { getLanguage, onLanguageChange, t } from "./i18n.js";
import { clearMessage, runWithBusyButton, showMessage } from "./ui.js";

const HTTP_NOT_FOUND = 404;
// Excluir pede uma segunda confirmação; se a pessoa não confirmar, o botão volta ao normal.
const DELETE_CONFIRMATION_MILLISECONDS = 4000;

/** Chave de tradução do erro de uma ação sobre um arquivo (baixar ou excluir). */
function fileErrorKey(error) {
  if (error instanceof ApiError && error.status === HTTP_NOT_FOUND) return "error.fileGone";
  if (error instanceof ApiError || error instanceof TypeError) return errorMessageKey(error);
  return "error.decryptFailed"; // a descriptografia falhou: a chave não confere ou o arquivo foi alterado
}

/**
 * Liga a lista de arquivos. Devolve `{ addEntry, removeEntry, load }`.
 * `getEncryptionKey` devolve a chave da sala.
 */
export function startFileList({ roomCode, getEncryptionKey }) {
  const list = document.getElementById("file-list");
  const emptyMessage = document.getElementById("files-empty");
  const listStatus = document.getElementById("files-status");

  const rowsById = new Map();

  function showEmptyMessageWhenNoFiles() {
    emptyMessage.hidden = rowsById.size > 0;
  }

  // Tira da lista um arquivo que foi apagado (por este ou por outro aparelho).
  function removeEntry(fileId) {
    rowsById.get(fileId)?.remove();
  }

  // ---------- uma linha da lista ----------

  function createFileRow(entry) {
    const nameElement = createElement("span", { className: "file__name" });
    const sizeElement = createElement("span", { className: "file__size" });
    const statusElement = createElement("p", { className: "error", attributes: { role: "status" } });
    const actions = createElement("div", { className: "file__actions" });
    const element = createElement("li", { className: "file" }, [
      createElement("div", { className: "file__info" }, [nameElement, sizeElement]),
      actions,
      statusElement,
    ]);

    const row = {
      element,
      remove: removeRow,
      render() {
        nameElement.textContent = entry.readable ? entry.name : t("files.unreadableName");
        sizeElement.textContent = formatFileSize(entry.size, getLanguage());
      },
    };

    function removeRow() {
      element.remove();
      rowsById.delete(entry.id);
      showEmptyMessageWhenNoFiles();
    }

    async function download(button) {
      clearMessage(statusElement);
      try {
        await runWithBusyButton(button, "files.downloading", async () => {
          const blob = await fetchDecryptedFile({
            roomCode,
            entry,
            encryptionKey: getEncryptionKey(),
            onStage: (stage) => {
              const stageKey = stage === "downloading" ? "files.downloading" : "files.decrypting";
              button.dataset.i18n = stageKey;
              button.textContent = t(stageKey);
            },
          });
          saveBlobAsFile(blob, entry.name);
        });
      } catch (error) {
        showMessage(statusElement, fileErrorKey(error));
      }
    }

    async function remove(button) {
      clearMessage(statusElement);
      try {
        await runWithBusyButton(button, "files.deleting", () => deleteFile(roomCode, entry.id));
        removeRow();
      } catch (error) {
        if (error instanceof ApiError && error.status === HTTP_NOT_FOUND) {
          removeRow(); // já não existia (outro aparelho apagou)
          return;
        }
        showMessage(statusElement, fileErrorKey(error));
      }
    }

    if (entry.readable) {
      const downloadButton = createElement("button", {
        className: "button button--outline button--small",
        i18nKey: "files.download",
        attributes: { type: "button" },
      });
      downloadButton.addEventListener("click", () => download(downloadButton));
      actions.append(downloadButton);
    }

    const deleteButton = createElement("button", {
      className: "button button--outline button--small",
      i18nKey: "files.delete",
      attributes: { type: "button" },
    });
    let confirmationTimer = null;
    deleteButton.addEventListener("click", () => {
      if (confirmationTimer === null) {
        deleteButton.dataset.i18n = "files.deleteConfirm";
        deleteButton.textContent = t("files.deleteConfirm");
        deleteButton.classList.add("button--danger");
        confirmationTimer = setTimeout(() => {
          confirmationTimer = null;
          deleteButton.dataset.i18n = "files.delete";
          deleteButton.textContent = t("files.delete");
          deleteButton.classList.remove("button--danger");
        }, DELETE_CONFIRMATION_MILLISECONDS);
        return;
      }
      clearTimeout(confirmationTimer);
      confirmationTimer = null;
      deleteButton.classList.remove("button--danger");
      remove(deleteButton);
    });
    actions.append(deleteButton);

    row.render();
    return row;
  }

  // ---------- usar a lista ----------

  function addEntry(entry) {
    if (rowsById.has(entry.id)) {
      return;
    }
    const row = createFileRow(entry);
    rowsById.set(entry.id, row);
    list.prepend(row.element); // o mais novo fica no alto
    showEmptyMessageWhenNoFiles();
  }

  async function load() {
    clearMessage(listStatus);
    try {
      const storedFiles = await listFiles(roomCode);
      const entries = storedFiles.map((storedFile) => readFileEntry(storedFile, getEncryptionKey()));
      // Reconcilia com o servidor: some o que foi apagado enquanto estávamos sem conexão e entra o que chegou.
      const idsOnServer = new Set(entries.map((entry) => entry.id));
      for (const fileId of [...rowsById.keys()]) {
        if (!idsOnServer.has(fileId)) {
          removeEntry(fileId);
        }
      }
      for (const entry of entries) {
        addEntry(entry);
      }
    } catch (error) {
      showMessage(listStatus, errorMessageKey(error));
    }
    showEmptyMessageWhenNoFiles();
  }

  onLanguageChange(() => {
    for (const row of rowsById.values()) {
      row.render();
    }
  });

  return { addEntry, removeEntry, load };
}
