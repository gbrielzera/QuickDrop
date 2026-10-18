// Página da sala: entra na sala (pelo link, pela chave guardada ou pela senha) e mostra como convidar outros aparelhos.

import { ApiError, deleteRoom, getRoom, lockRoom } from "./api.js";
import { errorMessageKey } from "./errors.js";
import { onLanguageChange, startLanguageSwitcher, t } from "./i18n.js";
import { createQrCodeSvg } from "./qr.js";
import {
  forgetEncryptionKey,
  getRoomParams,
  joinRoom,
  loadEncryptionKey,
  loadRoomSecret,
  saveRoomSecret,
} from "./room-access.js";
import { buildRoomPath, formatRoomCode, readSecretFromHash } from "./room-code.js";
import { startRoomPanels } from "./room-panels.js";
import { connectRoomSocket } from "./socket.js";
import { splitTimeLeft } from "./time-left.js";
import { clearMessage, runWithBusyButton, setUpConfirmButton, setUpCopyButton, showMessage } from "./ui.js";

const HTTP_UNAUTHORIZED = 401;
const HTTP_NOT_FOUND = 404;
const EXPIRY_REFRESH_MILLISECONDS = 15 * 1000;

const roomCode = document.body.dataset.roomCode;
// O segredo gerado pelo app viaja no link depois do "#". Em salas com senha própria, não existe.
// Depois de entrar ele passa a ficar só nesta aba (veja hideSecretFromAddressBar).
const secretFromLink = readSecretFromHash(location.hash) || loadRoomSecret(roomCode);

const views = {
  loading: document.getElementById("view-loading"),
  password: document.getElementById("view-password"),
  missing: document.getElementById("view-missing"),
  ready: document.getElementById("view-ready"),
};
const passwordForm = document.getElementById("room-password-form");
const passwordInput = document.getElementById("room-password");
const passwordSubmitButton = document.getElementById("room-password-submit");
const passwordError = document.getElementById("room-password-error");
const expiryTags = document.querySelectorAll("[data-expiry]");
const qrContainer = document.getElementById("qr-container");
const linkInput = document.getElementById("room-link");
const codeText = document.getElementById("room-code-text");
const passwordNote = document.getElementById("room-password-note");
const copyStatus = document.getElementById("copy-status");
const thisDeviceStation = document.getElementById("device-this");
const otherDeviceStation = document.getElementById("device-other");
const closeRoomButton = document.getElementById("close-room");
const guestNote = document.getElementById("room-guest-note");
const lockRoomButton = document.getElementById("lock-room");
const lockedNote = document.getElementById("room-locked-note");

let expiresAt = null;
let expiryTimer = null;
let panelsStarted = false;
let roomHasEnded = false;
let roomIsLocked = false;
let devicesOnline = 0;
let isConnected = false;

function showOnly(viewName) {
  for (const [name, view] of Object.entries(views)) {
    view.hidden = name !== viewName;
  }
}

// A sala acabou (expirou, foi encerrada ou não existe mais): mostra o aviso e para de usar a sala.
function showRoomEnded(titleKey, messageKey) {
  if (roomHasEnded) {
    return; // o primeiro aviso é o que vale
  }
  roomHasEnded = true;
  clearInterval(expiryTimer);
  forgetEncryptionKey(roomCode);
  const title = document.getElementById("missing-title");
  title.dataset.i18n = titleKey;
  title.textContent = t(titleKey);
  showMessage(document.getElementById("missing-detail"), messageKey);
  showOnly("missing");
}

// ---------- tempo restante ----------

function describeTimeLeft(millisecondsLeft) {
  const { hours, minutes } = splitTimeLeft(millisecondsLeft);
  if (hours > 0) return t("time.hoursMinutes", { hours, minutes });
  if (minutes > 0) return t("time.minutes", { minutes });
  return t("time.lessThanMinute");
}

function renderExpiry() {
  const millisecondsLeft = expiresAt - Date.now();
  const text =
    millisecondsLeft > 0 ? t("room.expiresIn", { time: describeTimeLeft(millisecondsLeft) }) : t("room.expired");
  for (const tag of expiryTags) {
    tag.textContent = text;
  }
  if (millisecondsLeft <= 0) {
    showRoomEnded("room.endedTitle", "room.endedExpired");
  }
}

// ---------- sala pronta ----------

// O link com o segredo fica no histórico do navegador (e é sincronizado com a conta da pessoa).
// Depois de entrar, guardamos o segredo só nesta aba e deixamos o endereço sem ele.
function hideSecretFromAddressBar() {
  if (!secretFromLink || !location.hash) {
    return;
  }
  if (saveRoomSecret(roomCode, secretFromLink)) {
    history.replaceState(null, "", location.pathname);
  }
}

function renderLockState(isLocked) {
  roomIsLocked = isLocked;
  const buttonKey = isLocked ? "room.unlock" : "room.lock";
  lockRoomButton.dataset.i18n = buttonKey;
  lockRoomButton.textContent = t(buttonKey);
  lockedNote.hidden = !isLocked;
}

async function toggleRoomLock() {
  const status = document.getElementById("room-action-status");
  clearMessage(status);
  try {
    const room = await runWithBusyButton(lockRoomButton, "room.locking", () => lockRoom(roomCode, !roomIsLocked));
    renderLockState(room.is_locked);
  } catch (error) {
    showMessage(status, errorMessageKey(error));
  }
}

function renderShareOptions() {
  const shareUrl = location.origin + buildRoomPath(roomCode, secretFromLink);
  linkInput.value = shareUrl;
  qrContainer.replaceChildren(createQrCodeSvg(shareUrl, t("room.qrAlt", { code: roomCode })));
  codeText.textContent = formatRoomCode(roomCode, secretFromLink);
  passwordNote.hidden = Boolean(secretFromLink);
}

// ---------- tempo real: quem está conectado ----------

function setStationDetail(station, messageKey, values = {}) {
  const detail = station.querySelector(".station__detail");
  detail.dataset.i18n = messageKey;
  detail.textContent = t(messageKey, values);
}

// Mostra no diagrama se há outro aparelho conectado e se este aparelho está sem conexão.
function renderPresence() {
  const otherDevices = Math.max(devicesOnline - 1, 0);
  otherDeviceStation.classList.toggle("station--online", otherDevices > 0);
  if (otherDevices === 0) {
    setStationDetail(otherDeviceStation, "route.otherDeviceDetail");
  } else if (otherDevices === 1) {
    setStationDetail(otherDeviceStation, "route.otherDeviceOnline");
  } else {
    setStationDetail(otherDeviceStation, "route.otherDevicesOnline", { count: otherDevices });
  }

  thisDeviceStation.classList.toggle("station--offline", !isConnected);
  setStationDetail(thisDeviceStation, isConnected ? "route.thisDeviceDetail" : "route.reconnecting");
}

// A conexão caiu: antes de tentar de novo, confere se a sala ainda existe e se ainda estamos nela.
async function shouldKeepReconnecting() {
  try {
    await getRoom(roomCode);
    return true;
  } catch (error) {
    if (isApiError(error, HTTP_NOT_FOUND)) {
      showRoomEnded("room.missingTitle", "error.roomMissing");
      return false;
    }
    if (isApiError(error, HTTP_UNAUTHORIZED)) {
      location.reload(); // a sessão acabou: recarregar refaz a entrada na sala
      return false;
    }
    return true; // sem rede ou erro passageiro: tenta de novo mais tarde
  }
}

// Recebe os avisos do servidor. Presença e fim da sala são tratados aqui; o resto vai para os painéis.
function startRealtime(panels) {
  function handleMessage(message) {
    if (message.type === "presence") {
      devicesOnline = message.online;
      renderPresence();
    } else if (message.type === "room_closed") {
      const messageKey = message.reason === "expired" ? "room.endedExpired" : "room.endedClosed";
      showRoomEnded("room.endedTitle", messageKey);
    } else {
      panels.handleMessage(message);
    }
  }

  connectRoomSocket({
    roomCode,
    onMessage: handleMessage,
    onOpen: () => {
      isConnected = true;
      renderPresence();
      panels.loadAll(); // pode ter havido mudanças enquanto estávamos sem conexão
    },
    onClose: () => {
      isConnected = false;
      renderPresence();
    },
    shouldReconnect: shouldKeepReconnecting,
  });
}

// Liga os painéis da sala e o tempo real (uma vez só por página).
function startPanels() {
  if (panelsStarted) {
    return;
  }
  panelsStarted = true;
  const panels = startRoomPanels({ roomCode, getEncryptionKey: () => loadEncryptionKey(roomCode) });
  panels.loadAll();
  startRealtime(panels);
}

async function showRoom() {
  const room = await getRoom(roomCode);
  expiresAt = new Date(room.expires_at).getTime();
  // Só quem criou a sala vê o botão de encerrar; os convidados veem uma explicação.
  closeRoomButton.hidden = !room.is_owner;
  lockRoomButton.hidden = !room.is_owner;
  guestNote.hidden = room.is_owner;
  renderLockState(room.is_locked);
  renderShareOptions();
  hideSecretFromAddressBar();
  renderExpiry();
  expiryTimer = setInterval(renderExpiry, EXPIRY_REFRESH_MILLISECONDS);
  showOnly("ready");
  startPanels();
}

// ---------- entrar ----------

function askForPassword(errorKey) {
  showOnly("password");
  if (errorKey) {
    showMessage(passwordError, errorKey);
  }
  passwordInput.focus();
}

async function handlePasswordSubmit(event) {
  event.preventDefault();
  clearMessage(passwordError);
  try {
    await runWithBusyButton(passwordSubmitButton, "join.busy", () => joinRoom(roomCode, passwordInput.value));
    await showRoom();
  } catch (error) {
    showMessage(passwordError, errorMessageKey(error));
  }
}

function isApiError(error, status) {
  return error instanceof ApiError && error.status === status;
}

// Encerra a sala para todos os aparelhos. O aviso na tela aparece quando o servidor confirma.
async function closeRoom(button) {
  const status = document.getElementById("room-action-status");
  clearMessage(status);
  try {
    await runWithBusyButton(button, "room.closing", () => deleteRoom(roomCode));
  } catch (error) {
    showMessage(status, errorMessageKey(error));
  }
}

async function enterRoom() {
  // 1) Este aparelho já entrou antes (chave guardada e cookie válido).
  if (loadEncryptionKey(roomCode)) {
    try {
      await showRoom();
      return;
    } catch (error) {
      if (!isApiError(error, HTTP_UNAUTHORIZED)) throw error;
    }
  }
  // 2) Chegou por um link ou QR Code com o segredo.
  if (secretFromLink) {
    try {
      await joinRoom(roomCode, secretFromLink);
      await showRoom();
      return;
    } catch (error) {
      if (!isApiError(error, HTTP_UNAUTHORIZED)) throw error;
      askForPassword("error.passwordWrong");
      return;
    }
  }
  // 3) Sem segredo no link: só dá para entrar numa sala com senha própria.
  const { hasPassword } = await getRoomParams(roomCode);
  if (!hasPassword) {
    showOnly("missing");
    showMessage(document.getElementById("missing-detail"), "error.secretNeeded");
    return;
  }
  askForPassword(null);
}

async function start() {
  startLanguageSwitcher();
  onLanguageChange(() => {
    if (expiresAt) {
      renderLockState(roomIsLocked);
      renderExpiry();
      renderShareOptions();
      renderPresence();
    }
  });
  passwordForm.addEventListener("submit", handlePasswordSubmit);
  setUpConfirmButton(closeRoomButton, "room.closeConfirm", closeRoom);
  lockRoomButton.addEventListener("click", toggleRoomLock);
  linkInput.addEventListener("focus", () => linkInput.select());
  setUpCopyButton(document.getElementById("copy-link"), () => linkInput.value, copyStatus);
  setUpCopyButton(document.getElementById("copy-code"), () => codeText.textContent, copyStatus);

  try {
    await enterRoom();
  } catch (error) {
    showOnly("missing");
    if (!isApiError(error, HTTP_NOT_FOUND)) {
      showMessage(document.getElementById("missing-detail"), errorMessageKey(error));
    }
  }
}

start();
