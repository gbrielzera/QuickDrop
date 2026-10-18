// Enviar e baixar arquivos: criptografa antes de enviar e descriptografa depois de baixar.
// O servidor só vê bytes embaralhados; nome, tipo e tamanho originais viajam criptografados.

import * as api from "./api.js";
import {
  decryptFile,
  decryptJson,
  encryptFile,
  encryptJson,
  fromBase64Url,
  toBase64Url,
} from "./crypto.js";
import { safeFileName } from "./file-size.js";
import { createZip, uniqueNames } from "./zip.js";

const REVOKE_URL_AFTER_MILLISECONDS = 60 * 1000;

/**
 * Transforma o que o servidor guarda de um arquivo (com os dados criptografados) em algo que a tela
 * entende. Se a chave não conferir, `readable` fica false e a tela mostra o arquivo como ilegível.
 */
export function readFileEntry(storedFile, encryptionKey) {
  const entry = {
    id: storedFile.id,
    encryptedSize: storedFile.size_bytes,
    createdAt: new Date(storedFile.created_at),
  };
  try {
    const meta = decryptJson(fromBase64Url(storedFile.encrypted_meta), encryptionKey);
    return { ...entry, readable: true, name: String(meta.name), type: String(meta.type), size: Number(meta.size) };
  } catch {
    return { ...entry, readable: false, name: "", type: "", size: storedFile.size_bytes };
  }
}

/**
 * Criptografa e envia um arquivo. `onStage` recebe "encrypting" e depois "sending";
 * `onProgress` recebe de 0 a 100 durante o envio. Devolve o arquivo como a tela o entende.
 */
export async function sendFile({ roomCode, file, encryptionKey, onStage, onProgress }) {
  onStage("encrypting");
  const encryptedBlob = await encryptFile(file, encryptionKey);
  const encryptedMeta = encryptJson({ name: file.name, type: file.type, size: file.size }, encryptionKey);

  onStage("sending");
  const storedFile = await api.uploadFile(roomCode, encryptedBlob, toBase64Url(encryptedMeta), onProgress);
  return readFileEntry(storedFile, encryptionKey);
}

/** Baixa o arquivo e o descriptografa. `onStage` recebe "downloading" e depois "decrypting". */
export async function fetchDecryptedFile({ roomCode, entry, encryptionKey, onStage }) {
  onStage("downloading");
  const encryptedBlob = await api.downloadFile(roomCode, entry.id);

  onStage("decrypting");
  const decryptedBlob = await decryptFile(encryptedBlob, encryptionKey);
  return new Blob([decryptedBlob], { type: entry.type });
}

/**
 * Baixa e descriptografa vários arquivos e os junta num .zip. `onProgress` recebe (número do arquivo, total)
 * a cada arquivo que começa a ser baixado.
 */
export async function buildZipOfEntries({ roomCode, entries, encryptionKey, onProgress }) {
  const files = [];
  for (const [index, entry] of entries.entries()) {
    onProgress(index + 1, entries.length);
    const blob = await fetchDecryptedFile({ roomCode, entry, encryptionKey, onStage: () => {} });
    files.push({ name: safeFileName(entry.name), blob, date: entry.createdAt });
  }
  const names = uniqueNames(files.map((file) => file.name));
  return createZip(files.map((file, index) => ({ ...file, name: names[index] })));
}

/** Salva o arquivo no aparelho, como se fosse um download comum. */
export function saveBlobAsFile(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = safeFileName(fileName);
  document.body.append(link);
  link.click();
  link.remove();
  // Dá tempo ao navegador de iniciar o download antes de liberar a memória.
  setTimeout(() => URL.revokeObjectURL(url), REVOKE_URL_AFTER_MILLISECONDS);
}
