// Conversa com o servidor (API de salas e de arquivos).

/**
 * Erro devolvido pelo servidor.
 * - status: o código HTTP (404, 401...).
 * - detail: o que o servidor explicou: um código em texto (ex.: "file_too_large") ou um objeto
 *   (ex.: o conflito do texto, com o texto atual dentro).
 * - code: o código em texto, quando houver.
 */
export class ApiError extends Error {
  constructor(status, detail = "") {
    super(`O servidor respondeu ${status}`);
    this.status = status;
    this.detail = detail;
    this.code = typeof detail === "string" ? detail : (detail?.code ?? "");
  }
}

function readDetailFromBody(body) {
  return body && typeof body === "object" && "detail" in body ? body.detail : "";
}

async function readErrorDetail(response) {
  try {
    return readDetailFromBody(await response.json());
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
    throw new ApiError(response.status, await readErrorDetail(response));
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
    throw new ApiError(response.status, await readErrorDetail(response));
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
    return readDetailFromBody(JSON.parse(responseText));
  } catch {
    return "";
  }
}

// ---------- texto compartilhado ----------

export function getText(code) {
  return request("GET", `/api/rooms/${code}/text`);
}

/** Salva o texto (já criptografado). Lança ApiError(409) se outro aparelho alterou antes. */
export function putText(code, ciphertext, baseVersion) {
  return request("PUT", `/api/rooms/${code}/text`, { ciphertext, base_version: baseVersion });
}

// ---------- clips ----------

export function listClips(code) {
  return request("GET", `/api/rooms/${code}/clips`);
}

export function createClip(code, ciphertext) {
  return request("POST", `/api/rooms/${code}/clips`, { ciphertext });
}

export function deleteClip(code, clipId) {
  return request("DELETE", `/api/rooms/${code}/clips/${clipId}`);
}
