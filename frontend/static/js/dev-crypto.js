// Página de teste da criptografia (/dev/crypto). Só serve para desenvolvimento.

import {
  decryptFile,
  decryptText,
  deriveRoomKeys,
  encryptFile,
  encryptText,
  generateRoomSecret,
  generateSalt,
  toBase64Url,
} from "./crypto.js";

const MAX_FILE_BYTES = 100 * 1024 * 1024;

const measureButton = document.getElementById("measure-button");
const measureResult = document.getElementById("measure-result");
const textInput = document.getElementById("text-input");
const textButton = document.getElementById("text-button");
const textResult = document.getElementById("text-result");
const fileInput = document.getElementById("file-input");
const fileButton = document.getElementById("file-button");
const fileResult = document.getElementById("file-result");

// Chaves de teste: a mesma sala falsa serve para o texto e para o arquivo.
function createTestKeys() {
  return deriveRoomKeys(generateRoomSecret(), generateSalt()).encryptionKey;
}

// Dá ao navegador a chance de mostrar "Calculando..." antes de o cálculo pesado travar a tela.
function waitForNextPaint() {
  return new Promise((resolve) => setTimeout(resolve, 50));
}

function formatMilliseconds(milliseconds) {
  return `${Math.round(milliseconds)} ms`;
}

async function measureKeyDerivation() {
  measureResult.textContent = "Calculando...";
  await waitForNextPaint();

  const startedAt = performance.now();
  deriveRoomKeys(generateRoomSecret(), generateSalt());
  measureResult.textContent = `Derivar as chaves levou ${formatMilliseconds(performance.now() - startedAt)}.`;
}

function testText() {
  const original = textInput.value;
  const encryptionKey = createTestKeys();

  const encrypted = encryptText(original, encryptionKey);
  const decrypted = decryptText(encrypted, encryptionKey);

  const worked = decrypted === original;
  textResult.textContent =
    `${worked ? "OK" : "ERRO"}: o servidor veria apenas isto: ${toBase64Url(encrypted)}`;
}

async function areSameBytes(firstBlob, secondBlob) {
  const first = new Uint8Array(await firstBlob.arrayBuffer());
  const second = new Uint8Array(await secondBlob.arrayBuffer());
  return first.length === second.length && first.every((byte, index) => byte === second[index]);
}

async function testFile() {
  const file = fileInput.files[0];
  if (!file) {
    fileResult.textContent = "Escolha um arquivo primeiro.";
    return;
  }
  if (file.size > MAX_FILE_BYTES) {
    fileResult.textContent = "Arquivo maior que 100 MB.";
    return;
  }

  fileResult.textContent = "Criptografando...";
  await waitForNextPaint();
  const encryptionKey = createTestKeys();

  const encryptStartedAt = performance.now();
  const encrypted = await encryptFile(file, encryptionKey);
  const encryptTime = performance.now() - encryptStartedAt;

  const decryptStartedAt = performance.now();
  const decrypted = await decryptFile(encrypted, encryptionKey);
  const decryptTime = performance.now() - decryptStartedAt;

  const worked = await areSameBytes(file, decrypted);
  fileResult.textContent =
    `${worked ? "OK" : "ERRO"}: original ${file.size} bytes, cifrado ${encrypted.size} bytes. ` +
    `Criptografar: ${formatMilliseconds(encryptTime)}. Descriptografar: ${formatMilliseconds(decryptTime)}.`;
}

function showError(resultElement, error) {
  resultElement.textContent = `ERRO: ${error.message}`;
}

measureButton.addEventListener("click", () => measureKeyDerivation().catch((error) => showError(measureResult, error)));
textButton.addEventListener("click", () => {
  try {
    testText();
  } catch (error) {
    showError(textResult, error);
  }
});
fileButton.addEventListener("click", () => testFile().catch((error) => showError(fileResult, error)));
