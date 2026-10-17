// Criar uma sala e entrar numa sala: junta a criptografia com a conversa com o servidor.
// A senha e a chave de criptografia nunca saem deste aparelho; o servidor só recebe a authKey.

import * as api from "./api.js";
import {
  deriveRoomKeys,
  fromBase64Url,
  generateRoomSecret,
  generateSalt,
  toBase64Url,
} from "./crypto.js";

const KEY_STORAGE_PREFIX = "quickdrop:key:";

// Chaves já conhecidas nesta página. Garante que a chave funcione mesmo sem sessionStorage.
const keysInMemory = new Map();

// A chave também fica no sessionStorage: sobrevive ao F5, mas some quando a aba é fechada.
function saveEncryptionKey(roomCode, encryptionKey) {
  keysInMemory.set(roomCode, encryptionKey);
  try {
    sessionStorage.setItem(KEY_STORAGE_PREFIX + roomCode, toBase64Url(encryptionKey));
  } catch {
    // Sem sessionStorage: a pessoa precisará entrar de novo se recarregar a página.
  }
}

/** Devolve a chave de criptografia guardada para a sala, ou null se este aparelho ainda não entrou. */
export function loadEncryptionKey(roomCode) {
  if (keysInMemory.has(roomCode)) {
    return keysInMemory.get(roomCode);
  }
  try {
    const savedKey = sessionStorage.getItem(KEY_STORAGE_PREFIX + roomCode);
    return savedKey ? fromBase64Url(savedKey) : null;
  } catch {
    return null;
  }
}

// O cálculo das chaves é pesado e trava a tela por um instante; antes dele damos tempo
// ao navegador de mostrar "Criando..." / "Entrando...".
function waitForNextPaint() {
  return new Promise((resolve) => setTimeout(resolve, 50));
}

/**
 * Cria uma sala. Sem senha escolhida, gera um segredo aleatório (devolvido em `secret`,
 * para ir no link e no QR Code). Com senha escolhida, `secret` fica vazio.
 */
export async function createRoom({ ttlHours, password }) {
  await waitForNextPaint();
  const secret = password || generateRoomSecret();
  const salt = generateSalt();
  const { authKey, encryptionKey } = deriveRoomKeys(secret, salt);

  const room = await api.createRoom({
    ttlHours,
    hasPassword: Boolean(password),
    kdfSalt: toBase64Url(salt),
    authKey: toBase64Url(authKey),
  });

  saveEncryptionKey(room.code, encryptionKey);
  return { code: room.code, secret: password ? "" : secret };
}

/** Pergunta ao servidor se a sala tem senha e qual é o salt. Lança ApiError(404) se não existir. */
export async function getRoomParams(roomCode) {
  const params = await api.getRoomParams(roomCode);
  return { hasPassword: params.has_password, kdfSalt: fromBase64Url(params.kdf_salt) };
}

/** Entra numa sala com o segredo (ou senha). Lança ApiError(401) se estiver errado. */
export async function joinRoom(roomCode, secret) {
  await waitForNextPaint();
  const { kdfSalt } = await getRoomParams(roomCode);
  const { authKey, encryptionKey } = deriveRoomKeys(secret, kdfSalt);

  await api.joinRoom(roomCode, toBase64Url(authKey));
  saveEncryptionKey(roomCode, encryptionKey);
}
