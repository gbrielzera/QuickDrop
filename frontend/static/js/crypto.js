// Toda a criptografia do QuickDrop fica neste arquivo.
// Nenhum outro arquivo do frontend mexe em chaves: eles só chamam estas funções.
//
// Resumo do esquema (detalhes na seção 6.1 do docs/PLANEJAMENTO.md):
//   senha + salt --Argon2id--> chave-mestra --> authKey (vai ao servidor, prova que sabe a senha)
//                                           \-> encryptionKey (nunca sai do navegador)

import sodium from "./vendor/libsodium-wrappers.mjs";

// A libsodium carrega um módulo WebAssembly. Quem importa este arquivo só continua depois disso.
await sodium.ready;

const KEY_BYTES = 32;
const NONCE_BYTES = sodium.crypto_secretbox_NONCEBYTES;

// O contexto do KDF precisa ter exatamente 8 caracteres.
const KDF_CONTEXT = "quickdrp";
const AUTH_KEY_ID = 1;
const ENCRYPTION_KEY_ID = 2;

// Argon2id "interactive": rápido o bastante para celulares (cerca de 64 MB de memória).
const ARGON2_OPS_LIMIT = sodium.crypto_pwhash_OPSLIMIT_INTERACTIVE;
const ARGON2_MEMORY_LIMIT = sodium.crypto_pwhash_MEMLIMIT_INTERACTIVE;

// Arquivos são criptografados em blocos de 1 MB para não precisar do arquivo inteiro na memória.
const FILE_CHUNK_BYTES = 1024 * 1024;
const ENCRYPTED_CHUNK_BYTES = FILE_CHUNK_BYTES + sodium.crypto_secretstream_xchacha20poly1305_ABYTES;
const FILE_HEADER_BYTES = sodium.crypto_secretstream_xchacha20poly1305_HEADERBYTES;
const TAG_MESSAGE = sodium.crypto_secretstream_xchacha20poly1305_TAG_MESSAGE;
const TAG_FINAL = sodium.crypto_secretstream_xchacha20poly1305_TAG_FINAL;

// Alfabeto do segredo gerado: sem 0/O, 1/I/L, que são fáceis de confundir ao digitar.
const SECRET_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";
// 12 caracteres de um alfabeto de 31 dão cerca de 59 bits: tentar todas as combinações é inviável,
// mesmo para quem roubasse o banco de dados e testasse senhas sem passar pelo site.
const SECRET_LENGTH = 12;

// ---------- Codificação para enviar ao servidor ----------

/** Transforma bytes em texto seguro para URL e JSON (base64url, sem "="). */
export function toBase64Url(bytes) {
  return sodium.to_base64(bytes, sodium.base64_variants.URLSAFE_NO_PADDING);
}

/** Faz o caminho inverso de toBase64Url. */
export function fromBase64Url(text) {
  return sodium.from_base64(text, sodium.base64_variants.URLSAFE_NO_PADDING);
}

// ---------- Chaves ----------

/** Gera o salt (valor aleatório, não secreto) usado para derivar as chaves de uma sala. */
export function generateSalt() {
  return sodium.randombytes_buf(sodium.crypto_pwhash_SALTBYTES);
}

/** Gera o segredo de 12 caracteres usado quando o usuário não escolhe uma senha. */
export function generateRoomSecret() {
  let secret = "";
  for (let position = 0; position < SECRET_LENGTH; position++) {
    // randombytes_uniform evita viés, ao contrário de "aleatório % tamanho".
    const index = sodium.randombytes_uniform(SECRET_ALPHABET.length);
    secret += SECRET_ALPHABET[index];
  }
  return secret;
}

/**
 * Deriva as duas chaves da sala a partir da senha (ou do segredo gerado) e do salt.
 * - authKey: enviada ao servidor para provar que quem entra conhece a senha.
 * - encryptionKey: usada para criptografar tudo; nunca é enviada.
 * O servidor não consegue calcular a encryptionKey a partir da authKey.
 */
export function deriveRoomKeys(password, salt) {
  const masterKey = sodium.crypto_pwhash(
    KEY_BYTES,
    password,
    salt,
    ARGON2_OPS_LIMIT,
    ARGON2_MEMORY_LIMIT,
    sodium.crypto_pwhash_ALG_ARGON2ID13,
  );
  const authKey = sodium.crypto_kdf_derive_from_key(KEY_BYTES, AUTH_KEY_ID, KDF_CONTEXT, masterKey);
  const encryptionKey = sodium.crypto_kdf_derive_from_key(KEY_BYTES, ENCRYPTION_KEY_ID, KDF_CONTEXT, masterKey);
  sodium.memzero(masterKey);
  return { authKey, encryptionKey };
}

// ---------- Textos (editor, clips e metadados) ----------

/** Criptografa um texto. O resultado é o nonce (24 bytes aleatórios) seguido do texto cifrado. */
export function encryptText(text, encryptionKey) {
  const nonce = sodium.randombytes_buf(NONCE_BYTES);
  const cipher = sodium.crypto_secretbox_easy(text, nonce, encryptionKey);
  const result = new Uint8Array(NONCE_BYTES + cipher.length);
  result.set(nonce);
  result.set(cipher, NONCE_BYTES);
  return result;
}

/** Descriptografa o resultado de encryptText. Lança erro se a chave estiver errada ou o dado for alterado. */
export function decryptText(encryptedBytes, encryptionKey) {
  const nonce = encryptedBytes.slice(0, NONCE_BYTES);
  const cipher = encryptedBytes.slice(NONCE_BYTES);
  const plainBytes = sodium.crypto_secretbox_open_easy(cipher, nonce, encryptionKey);
  return sodium.to_string(plainBytes);
}

/** Criptografa um objeto (ex.: nome, tipo e tamanho de um arquivo). */
export function encryptJson(value, encryptionKey) {
  return encryptText(JSON.stringify(value), encryptionKey);
}

/** Descriptografa o resultado de encryptJson. */
export function decryptJson(encryptedBytes, encryptionKey) {
  return JSON.parse(decryptText(encryptedBytes, encryptionKey));
}

// ---------- Arquivos ----------
// Formato do arquivo criptografado: [cabeçalho de 24 bytes][bloco][bloco]...[bloco final]
// Cada bloco guarda um "tag"; o último é marcado como final. Assim, se alguém cortar o arquivo
// no meio, a descriptografia falha em vez de entregar um arquivo incompleto.

/** Criptografa um File/Blob e devolve um Blob com o conteúdo cifrado. */
export async function encryptFile(file, encryptionKey) {
  const { state, header } = sodium.crypto_secretstream_xchacha20poly1305_init_push(encryptionKey);
  const parts = [header];

  let offset = 0;
  do {
    const end = Math.min(offset + FILE_CHUNK_BYTES, file.size);
    const chunk = new Uint8Array(await file.slice(offset, end).arrayBuffer());
    const isLastChunk = end === file.size;
    const tag = isLastChunk ? TAG_FINAL : TAG_MESSAGE;
    parts.push(sodium.crypto_secretstream_xchacha20poly1305_push(state, chunk, null, tag));
    offset = end;
  } while (offset < file.size);

  return new Blob(parts);
}

/** Descriptografa um Blob criado por encryptFile. Lança erro se a chave estiver errada ou o arquivo for alterado. */
export async function decryptFile(encryptedBlob, encryptionKey) {
  if (encryptedBlob.size < FILE_HEADER_BYTES) {
    throw new Error("Arquivo criptografado inválido: pequeno demais.");
  }

  const header = new Uint8Array(await encryptedBlob.slice(0, FILE_HEADER_BYTES).arrayBuffer());
  const state = sodium.crypto_secretstream_xchacha20poly1305_init_pull(header, encryptionKey);
  const parts = [];

  let offset = FILE_HEADER_BYTES;
  let foundFinalChunk = false;
  while (offset < encryptedBlob.size) {
    if (foundFinalChunk) {
      throw new Error("Arquivo criptografado inválido: há dados depois do bloco final.");
    }
    const end = Math.min(offset + ENCRYPTED_CHUNK_BYTES, encryptedBlob.size);
    const encryptedChunk = new Uint8Array(await encryptedBlob.slice(offset, end).arrayBuffer());
    const { message, tag } = sodium.crypto_secretstream_xchacha20poly1305_pull(state, encryptedChunk);
    parts.push(message);
    foundFinalChunk = tag === TAG_FINAL;
    offset = end;
  }

  if (!foundFinalChunk) {
    throw new Error("Arquivo criptografado incompleto: faltam blocos no final.");
  }
  return new Blob(parts);
}
