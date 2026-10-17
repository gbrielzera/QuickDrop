// Funções puras para ler e montar o código, o segredo e o link de uma sala.
//
// O código completo tem duas partes: K7P3XM-HQ4T-9WZC
//   - "K7P3XM" é o código da sala (vai ao servidor para achar a sala);
//   - "HQ4T9WZC" é o segredo (nunca vai ao servidor: gera as chaves de criptografia).

const ROOM_CODE_LENGTH = 6;
const SECRET_LENGTH = 8;
const SECRET_GROUP_LENGTH = 4;

// Mesmo alfabeto do servidor e do gerador de segredos: sem 0/O e 1/I/L.
const ROOM_CODE_PATTERN = /^[2-9A-HJKMNP-Z]{6}$/;
const SECRET_PATTERN = /^[2-9A-HJKMNP-Z]{8}$/;

/** Lê o que a pessoa digitou ("k7p3xm hq4t-9wzc" etc.) e separa o código da sala do segredo. */
export function parseRoomCodeInput(text) {
  const letters = text.toUpperCase().replace(/[^A-Z0-9]/g, "");
  return {
    code: letters.slice(0, ROOM_CODE_LENGTH),
    secret: letters.slice(ROOM_CODE_LENGTH),
  };
}

export function isValidRoomCode(code) {
  return ROOM_CODE_PATTERN.test(code);
}

export function isValidSecret(secret) {
  return SECRET_PATTERN.test(secret);
}

/** Monta o código para digitar: "K7P3XM-HQ4T-9WZC" (ou só "K7P3XM" quando não há segredo gerado). */
export function formatRoomCode(code, secret) {
  if (!secret) {
    return code;
  }
  const firstGroup = secret.slice(0, SECRET_GROUP_LENGTH);
  const secondGroup = secret.slice(SECRET_GROUP_LENGTH);
  return `${code}-${firstGroup}-${secondGroup}`;
}

/** Caminho da página da sala. O segredo vai depois do "#", parte que o navegador nunca envia ao servidor. */
export function buildRoomPath(code, secret) {
  const path = `/r/${code}`;
  return secret ? `${path}#k=${secret}` : path;
}

/** Lê o segredo de um fragmento de URL como "#k=HQ4T9WZC". Devolve "" se não houver. */
export function readSecretFromHash(hash) {
  const parameters = new URLSearchParams(hash.replace(/^#/, ""));
  return (parameters.get("k") ?? "").toUpperCase();
}
