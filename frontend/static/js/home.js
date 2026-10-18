// Tela inicial: criar uma sala ou entrar numa sala.

import { errorMessageKey } from "./errors.js";
import { startLanguageSwitcher } from "./i18n.js";
import * as roomAccess from "./room-access.js";
import { buildRoomPath, isValidRoomCode, isValidSecret, parseRoomCodeInput } from "./room-code.js";
import { clearMessage, runWithBusyButton, showMessage } from "./ui.js";

const MIN_PASSWORD_LENGTH = 10;

/** A sala não tem senha, então o código digitado sozinho não basta para abrir o conteúdo. */
class SecretNeededError extends Error {}

const createForm = document.getElementById("create-form");
const usePasswordCheckbox = document.getElementById("use-password");
const createPasswordField = document.getElementById("create-password-field");
const createPasswordInput = document.getElementById("create-password");
const createSubmitButton = document.getElementById("create-submit");
const createError = document.getElementById("create-error");

const joinForm = document.getElementById("join-form");
const joinCodeInput = document.getElementById("join-code");
const joinPasswordField = document.getElementById("join-password-field");
const joinPasswordInput = document.getElementById("join-password");
const joinSubmitButton = document.getElementById("join-submit");
const joinError = document.getElementById("join-error");

// ---------- criar sala ----------

function showCreatePasswordField() {
  createPasswordField.hidden = !usePasswordCheckbox.checked;
  if (usePasswordCheckbox.checked) {
    createPasswordInput.focus();
  }
}

async function handleCreate(event) {
  event.preventDefault();
  clearMessage(createError);

  const ttlHours = Number(createForm.elements.ttl.value);
  const password = usePasswordCheckbox.checked ? createPasswordInput.value : "";
  if (usePasswordCheckbox.checked && password.length < MIN_PASSWORD_LENGTH) {
    showMessage(createError, "error.passwordTooShort");
    createPasswordInput.focus();
    return;
  }

  try {
    const room = await runWithBusyButton(createSubmitButton, "create.busy", () =>
      roomAccess.createRoom({ ttlHours, password }),
    );
    location.assign(buildRoomPath(room.code, room.secret));
  } catch (error) {
    showMessage(createError, errorMessageKey(error));
  }
}

// ---------- entrar na sala ----------

// Descobre o segredo para entrar: o digitado junto do código ou, em sala com senha, o campo de senha.
async function findSecret(roomCode, typedSecret) {
  if (typedSecret) {
    return typedSecret;
  }
  const { hasPassword } = await roomAccess.getRoomParams(roomCode);
  if (!hasPassword) {
    throw new SecretNeededError();
  }
  return joinPasswordInput.value;
}

async function tryToJoin(roomCode, typedSecret) {
  const secret = await findSecret(roomCode, typedSecret);
  if (!secret) {
    return false; // sala com senha e o campo de senha ainda está vazio
  }
  await roomAccess.joinRoom(roomCode, secret);
  return true;
}

async function handleJoin(event) {
  event.preventDefault();
  clearMessage(joinError);

  const { code: roomCode, secret: typedSecret } = parseRoomCodeInput(joinCodeInput.value);
  if (!isValidRoomCode(roomCode)) {
    showMessage(joinError, "error.codeInvalid");
    joinCodeInput.focus();
    return;
  }
  if (typedSecret && !isValidSecret(typedSecret)) {
    showMessage(joinError, "error.codeIncomplete");
    joinCodeInput.focus();
    return;
  }

  try {
    const joined = await runWithBusyButton(joinSubmitButton, "join.busy", () =>
      tryToJoin(roomCode, typedSecret),
    );
    if (joined) {
      location.assign(buildRoomPath(roomCode, typedSecret));
      return;
    }
    joinPasswordField.hidden = false;
    joinPasswordInput.focus();
    showMessage(joinError, "join.passwordNeeded");
  } catch (error) {
    const messageKey = error instanceof SecretNeededError ? "error.secretNeeded" : errorMessageKey(error);
    showMessage(joinError, messageKey);
  }
}

startLanguageSwitcher();
usePasswordCheckbox.addEventListener("change", showCreatePasswordField);
createForm.addEventListener("submit", handleCreate);
joinForm.addEventListener("submit", handleJoin);
