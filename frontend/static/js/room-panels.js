// Os painéis de dentro da sala: arquivos, texto, clips de texto, código e blocos de código.
// A página da sala (room.js) liga todos de uma vez e repassa a eles os avisos do servidor.

import {
  createClip,
  createCodeClip,
  deleteClip,
  deleteCodeClip,
  getSource,
  getText,
  listClips,
  listCodeClips,
  putSource,
  putText,
} from "./api.js";
import { setUpCodeKeys } from "./code-keys.js";
import { startClipsPanel } from "./clips-panel.js";
import { startFileList } from "./file-list.js";
import { readFileEntry } from "./file-transfer.js";
import { startSharedEditor } from "./shared-editor.js";
import { startUploadPanel } from "./upload-panel.js";

// Os ids dos elementos de cada painel na página da sala.
const TEXT_EDITOR_IDS = {
  textarea: "shared-text",
  status: "text-status",
  copyStatus: "text-copy-status",
  conflict: "text-conflict",
  useTheirs: "use-theirs",
  keepMine: "keep-mine",
  copyButton: "copy-text",
  clearButton: "clear-text",
};
const CODE_EDITOR_IDS = {
  textarea: "shared-code",
  status: "code-status",
  copyStatus: "code-copy-status",
  conflict: "code-conflict",
  useTheirs: "code-use-theirs",
  keepMine: "code-keep-mine",
  copyButton: "code-copy",
  clearButton: "code-clear",
};
const TEXT_CLIPS_IDS = {
  input: "clip-input",
  saveButton: "save-clip",
  empty: "clips-empty",
  list: "clip-list",
  status: "clips-status",
};
const CODE_CLIPS_IDS = {
  input: "code-clip-input",
  saveButton: "code-save-clip",
  empty: "code-clips-empty",
  list: "code-clip-list",
  status: "code-clips-status",
};

/**
 * Liga todos os painéis da sala. Devolve:
 * - loadAll: consulta o servidor e atualiza tudo (ao abrir a sala e depois de reconectar);
 * - handleMessage: recebe um aviso do servidor e devolve true se algum painel cuidou dele.
 */
export function startRoomPanels({ roomCode, getEncryptionKey }) {
  const limits = document.body.dataset;

  const fileList = startFileList({ roomCode, getEncryptionKey });
  startUploadPanel({
    roomCode,
    maxFileBytes: Number(limits.maxFileBytes),
    maxRoomBytes: Number(limits.maxRoomBytes),
    getEncryptionKey,
    onFileSent: fileList.addEntry,
  });

  const textEditor = startSharedEditor({
    roomCode,
    ids: TEXT_EDITOR_IDS,
    api: { get: getText, put: putText },
    maxBytes: Number(limits.maxTextBytes),
    getEncryptionKey,
  });
  const textClips = startClipsPanel({
    roomCode,
    ids: TEXT_CLIPS_IDS,
    api: { list: listClips, create: createClip, remove: deleteClip },
    maxClipBytes: Number(limits.maxClipBytes),
    getEncryptionKey,
  });

  const codeEditor = startSharedEditor({
    roomCode,
    ids: CODE_EDITOR_IDS,
    api: { get: getSource, put: putSource },
    maxBytes: Number(limits.maxTextBytes),
    getEncryptionKey,
  });
  setUpCodeKeys(document.getElementById(CODE_EDITOR_IDS.textarea));
  const codeClips = startClipsPanel({
    roomCode,
    ids: CODE_CLIPS_IDS,
    api: { list: listCodeClips, create: createCodeClip, remove: deleteCodeClip },
    maxClipBytes: Number(limits.maxCodeClipBytes),
    getEncryptionKey,
    isCode: true,
  });

  function loadAll() {
    fileList.load();
    textClips.load();
    codeClips.load();
    textEditor.refresh();
    codeEditor.refresh();
  }

  // Cada tipo de aviso do servidor vai para o painel que cuida dele.
  const messageHandlers = {
    file_added: (message) => fileList.addEntry(readFileEntry(message.file, getEncryptionKey())),
    file_deleted: (message) => fileList.removeEntry(message.file_id),
    text_updated: (message) => textEditor.receiveRemote(message),
    source_updated: (message) => codeEditor.receiveRemote(message),
    clip_added: (message) => textClips.addStoredClip(message.clip),
    clip_deleted: (message) => textClips.removeEntry(message.clip_id),
    code_clip_added: (message) => codeClips.addStoredClip(message.clip),
    code_clip_deleted: (message) => codeClips.removeEntry(message.clip_id),
  };

  function handleMessage(message) {
    const handler = messageHandlers[message.type];
    if (!handler) {
      return false;
    }
    handler(message);
    return true;
  }

  return { loadAll, handleMessage };
}
