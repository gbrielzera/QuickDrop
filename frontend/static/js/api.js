// Conversa com o servidor (API de salas e de arquivos).

/**
 * Erro devolvido pelo servidor.
 * `status` é o código HTTP (404, 401...). `code` é o motivo em texto quando o servidor informa
 * (por exemplo "file_too_large" e "room_full").
 */
export class ApiError extends Error {
  constructor(status, code = "") {
    super(`O servidor respondeu ${status}`);
    this.status = status;
    this.code = code;
  }
}

async function readErrorCode(response) {
  try {
    const body = await response.json();
    return typeof body.detail === "string" ? body.detail : "";
  } catch {
    return "";
  }
}

async function request(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorCode(response));
  }
  return response.status === 204 ? null : response.json();
}

// ---------- salas ----------

export function createRoom({ ttlHours, hasPassword, kdfSalt, authKey }) {
  return request("POST", "/api/rooms", {
    ttl_hours: ttlHours,
    has_password: hasPassword,
    kdf_salt: kdfSalt,
    auth_key: authKey,
  });
}

export function getRoomParams(code) {
  return request("GET", `/api/rooms/${code}/params`);
}

export function joinRoom(code, authKey) {
  return request("POST", `/api/rooms/${code}/join`, { auth_key: authKey });
}

export function getRoom(code) {
  return request("GET", `/api/rooms/${code}`);
}

// ---------- arquivos ----------

export function listFiles(code) {
  return request("GET", `/api/rooms/${code}/files`);
}

export function deleteFile(code, fileId) {
  return request("DELETE", `/api/rooms/${code}/files/${fileId}`);
}

/** Baixa o arquivo (ainda criptografado) como Blob. */
export async function downloadFile(code, fileId) {
  const response = await fetch(`/api/rooms/${code}/files/${fileId}`, { credentials: "same-origin" });
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorCode(response));
  }
  return response.blob();
}

/**
 * Envia um arquivo já criptografado. Usa XMLHttpRequest porque o fetch ainda não informa
 * o andamento do envio. `onProgress` recebe um número de 0 a 100.
 */
export function uploadFile(code, encryptedBlob, encryptedMeta, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `/api/rooms/${code}/files`);
    xhr.setRequestHeader("Content-Type", "application/octet-stream");
    xhr.setRequestHeader("X-File-Meta", encryptedMeta);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
        return;
      }
      reject(new ApiError(xhr.status, readDetailFromText(xhr.responseText)));
    };
    // Sem resposta do servidor (rede caiu): o mesmo tipo de erro que o fetch lança.
    xhr.onerror = () => reject(new TypeError("Falha de rede no envio."));
    xhr.send(encryptedBlob);
  });
}

function readDetailFromText(responseText) {
  try {
    const body = JSON.parse(responseText);
    return typeof body.detail === "string" ? body.detail : "";
  } catch {
    return "";
  }
}
