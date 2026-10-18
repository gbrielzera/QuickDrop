// Painel "Enviar arquivos": área de soltar, botão de escolher e fila de envios com progresso.

import { createElement } from "./dom.js";
import { errorMessageKey } from "./errors.js";
import { formatFileSize } from "./file-size.js";
import { pastedFileName } from "./file-types.js";
import { sendFile } from "./file-transfer.js";
import { getLanguage, onLanguageChange, t } from "./i18n.js";

const MAX_PERCENT = 100;

/**
 * Liga o painel de envio.
 * - maxFileBytes e maxRoomBytes: limites mostrados na dica e usados para recusar arquivos grandes demais.
 * - getEncryptionKey: devolve a chave da sala.
 * - onFileSent: chamada com cada arquivo enviado com sucesso.
 */
export function startUploadPanel({ roomCode, maxFileBytes, maxRoomBytes, getEncryptionKey, onFileSent }) {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const chooseButton = document.getElementById("choose-files");
  const limitsHint = document.getElementById("limits-hint");
  const transferList = document.getElementById("upload-list");

  const transferRows = new Set();
  // Os envios acontecem um por vez: cada arquivo é criptografado na memória, então mais de um junto pesaria.
  let sendQueue = Promise.resolve();

  function renderLimits() {
    limitsHint.textContent = t("files.limits", {
      fileSize: formatFileSize(maxFileBytes, getLanguage()),
      roomSize: formatFileSize(maxRoomBytes, getLanguage()),
    });
  }

  // ---------- uma linha da fila ----------

  function createTransferRow(file) {
    const nameElement = createElement("span", { className: "transfer__name", text: file.name });
    const sizeElement = createElement("span", { className: "transfer__size" });
    const bar = createElement("progress", {
      className: "transfer__bar",
      attributes: { max: String(MAX_PERCENT), "aria-label": file.name },
    });
    const statusElement = createElement("p", { className: "transfer__status" });
    const dismissButton = createElement("button", {
      className: "button button--outline button--small",
      i18nKey: "files.dismiss",
      attributes: { type: "button" },
    });
    dismissButton.hidden = true;
    const element = createElement("li", { className: "transfer" }, [
      createElement("div", { className: "transfer__top" }, [nameElement, sizeElement]),
      bar,
      statusElement,
      dismissButton,
    ]);

    let messageKey = "files.encrypting";
    let percent = 0;

    const row = {
      element,
      render() {
        sizeElement.textContent = formatFileSize(file.size, getLanguage());
        statusElement.textContent = t(messageKey, {
          percent,
          fileSize: formatFileSize(maxFileBytes, getLanguage()),
        });
      },
      setStage(stage) {
        if (stage === "encrypting") {
          bar.removeAttribute("value"); // sem valor: a barra mostra "trabalhando"
          messageKey = "files.encrypting";
        } else {
          bar.value = 0;
          messageKey = "files.sending";
        }
        row.render();
      },
      setProgress(newPercent) {
        percent = newPercent;
        bar.value = newPercent;
        row.render();
      },
      fail(newMessageKey) {
        messageKey = newMessageKey;
        bar.hidden = true;
        statusElement.classList.add("error");
        dismissButton.hidden = false;
        row.render();
      },
      remove() {
        element.remove();
        transferRows.delete(row);
      },
    };
    dismissButton.addEventListener("click", row.remove);
    transferRows.add(row);
    row.render();
    return row;
  }

  // ---------- enviar ----------

  async function sendOneFile(file, row) {
    if (file.size > maxFileBytes) {
      row.fail("error.fileTooLarge");
      return;
    }
    try {
      const entry = await sendFile({
        roomCode,
        file,
        encryptionKey: getEncryptionKey(),
        onStage: row.setStage,
        onProgress: row.setProgress,
      });
      onFileSent(entry);
      row.remove();
    } catch (error) {
      row.fail(errorMessageKey(error));
    }
  }

  function queueFiles(files) {
    for (const file of files) {
      const row = createTransferRow(file);
      transferList.append(row.element);
      sendQueue = sendQueue.then(() => sendOneFile(file, row));
    }
  }

  // ---------- escolher e arrastar ----------

  chooseButton.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    queueFiles(Array.from(fileInput.files));
    fileInput.value = ""; // permite escolher o mesmo arquivo de novo depois
  });

  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dropzone--active");
  });
  dropzone.addEventListener("dragleave", (event) => {
    if (!dropzone.contains(event.relatedTarget)) {
      dropzone.classList.remove("dropzone--active");
    }
  });
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("dropzone--active");
    queueFiles(Array.from(event.dataTransfer.files));
  });
  // Ctrl+V com uma imagem (um print, por exemplo) ou arquivos copiados envia na hora.
  // Texto colado não passa por aqui: quem cuida dele é o painel de clips.
  document.addEventListener("paste", (event) => {
    const pastedFiles = Array.from(event.clipboardData?.files ?? []);
    if (pastedFiles.length === 0) {
      return;
    }
    event.preventDefault();
    const now = new Date();
    queueFiles(pastedFiles.map((file) => new File([file], pastedFileName(file, now), { type: file.type })));
  });
  // Arquivo solto fora da área não pode fazer o navegador abri-lo e sair da sala.
  window.addEventListener("dragover", (event) => event.preventDefault());
  window.addEventListener("drop", (event) => event.preventDefault());

  renderLimits();
  onLanguageChange(() => {
    renderLimits();
    for (const row of transferRows) {
      row.render();
    }
  });
}
