// Conversa com o servidor (API de salas).

/** Erro devolvido pelo servidor. O `status` é o código HTTP (404, 401...). */
export class ApiError extends Error {
  constructor(status) {
    super(`O servidor respondeu ${status}`);
    this.status = status;
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
    throw new ApiError(response.status);
  }
  return response.json();
}

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
