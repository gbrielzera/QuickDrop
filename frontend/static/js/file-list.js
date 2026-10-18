// Painel "Na sala": a lista de arquivos, com ver (imagens), baixar, baixar tudo em .zip e excluir.

import { ApiError, deleteFile, listFiles } from "./api.js";
import { createElement } from "./dom.js";
import { errorMessageKey } from "./errors.js";
import { formatFileSize } from "./file-size.js";
import { buildZipOfEntries, fetchDecryptedFile, readFileEntry, saveBlobAsFile } from "./file-transfer.js";
import { isPreviewableImage } from "./file-types.js";
import { getLanguage, onLanguageChange, t } from "./i18n.js";
import { setUpPreviewButton } from "./image-preview.js";
import { clearMessage, runWithBusyButton, setUpConfirmButton, showMessage } from "./ui.js";

const HTTP_NOT_FOUND = 404;
// O botão "Baixar tudo" só faz sentido com mais de um arquivo.
const MIN_FILES_FOR_ZIP = 2;

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
  const downloadAllButton = document.getElementById("download-all");

  const rowsById = new Map();

  function readableEntries() {
    return [...rowsById.values()].map((row) => row.entry).filter((entry) => entry.readable);
  }

  function showEmptyMessageWhenNoFiles() {
    emptyMessage.hidden = rowsById.size > 0;
    downloadAllButton.hidden = readableEntries().length < MIN_FILES_FOR_ZIP;
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

    let preview = null;

    const row = {
      element,
      entry,
      remove: removeRow,
      render() {
        nameElement.textContent = entry.readable ? entry.name : t("files.unreadableName");
        sizeElement.textContent = formatFileSize(entry.size, getLanguage());
      },
    };

    function removeRow() {
      preview?.close(); // libera a memória da imagem
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
        await runWithBusyButton(button, "action.deleting", () => deleteFile(roomCode, entry.id));
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

    if (entry.readable && isPreviewableImage(entry.type, entry.size)) {
      const previewButton = createElement("button", {
        className: "button button--outline button--small",
        i18nKey: "files.view",
        attributes: { type: "button" },
      });
      preview = setUpPreviewButton({
        button: previewButton,
        container: element,
        imageName: entry.name,
        loadBlob: () =>
          fetchDecryptedFile({ roomCode, entry, encryptionKey: getEncryptionKey(), onStage: () => {} }),
        onError: (error) => showMessage(statusElement, fileErrorKey(error)),
      });
      actions.prepend(previewButton);
    }

    const deleteButton = createElement("button", {
      className: "button button--outline button--small",
      i18nKey: "action.delete",
      attributes: { type: "button" },
    });
    setUpConfirmButton(deleteButton, "action.deleteConfirm", remove);
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

  async function downloadAll(button) {
    clearMessage(listStatus);
    try {
      const zipBlob = await runWithBusyButton(button, "files.zipping", () =>
        buildZipOfEntries({
          roomCode,
          entries: readableEntries(),
          encryptionKey: getEncryptionKey(),
          onProgress: (current, total) => showMessage(listStatus, "files.zipProgress", { current, total }),
        }),
      );
      saveBlobAsFile(zipBlob, `quickdrop-${roomCode}.zip`);
      clearMessage(listStatus);
    } catch (error) {
      showMessage(listStatus, fileErrorKey(error));
    }
  }

  downloadAllButton.addEventListener("click", () => downloadAll(downloadAllButton));

  onLanguageChange(() => {
    for (const row of rowsById.values()) {
      row.render();
    }
  });

  return { addEntry, removeEntry, load };
}
