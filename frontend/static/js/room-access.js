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
const SECRET_STORAGE_PREFIX = "quickdrop:secret:";

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

/**
 * Guarda o segredo do link nesta aba (para o convite continuar completo depois de recarregar a página).
 * Devolve false se não foi possível guardar; nesse caso o segredo precisa continuar no endereço.
 */
export function saveRoomSecret(roomCode, secret) {
  try {
    sessionStorage.setItem(SECRET_STORAGE_PREFIX + roomCode, secret);
    return true;
  } catch {
    return false;
  }
}

/** Devolve o segredo guardado por saveRoomSecret, ou "" se não houver. */
export function loadRoomSecret(roomCode) {
  try {
    return sessionStorage.getItem(SECRET_STORAGE_PREFIX + roomCode) ?? "";
  } catch {
    return "";
  }
}

/** Esquece a chave da sala (usado quando a sala acaba). */
export function forgetEncryptionKey(roomCode) {
  keysInMemory.delete(roomCode);
  try {
    sessionStorage.removeItem(SECRET_STORAGE_PREFIX + roomCode);
    sessionStorage.removeItem(KEY_STORAGE_PREFIX + roomCode);
  } catch {
    // Sem sessionStorage: não há nada guardado para esquecer.
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

// O salt de uma sala nunca muda: guardar a resposta evita uma ida ao servidor a mais ao pedir a senha.
const paramsInMemory = new Map();

/** Pergunta ao servidor se a sala tem senha e qual é o salt. Lança ApiError(404) se não existir. */
export async function getRoomParams(roomCode) {
  if (!paramsInMemory.has(roomCode)) {
    const params = await api.getRoomParams(roomCode);
    paramsInMemory.set(roomCode, { hasPassword: params.has_password, kdfSalt: fromBase64Url(params.kdf_salt) });
  }
  return paramsInMemory.get(roomCode);
}

/** Entra numa sala com o segredo (ou senha) e devolve os dados da sala. Lança ApiError(401) se estiver errado. */
export async function joinRoom(roomCode, secret) {
  await waitForNextPaint();
  const { kdfSalt } = await getRoomParams(roomCode);
  const { authKey, encryptionKey } = deriveRoomKeys(secret, kdfSalt);

  const room = await api.joinRoom(roomCode, toBase64Url(authKey));
  saveEncryptionKey(roomCode, encryptionKey);
  return room;
}
