// Transforma um erro técnico na chave de uma mensagem para a pessoa.

import { ApiError } from "./api.js";

const HTTP_UNAUTHORIZED = 401;
const HTTP_NOT_FOUND = 404;

/** Devolve a chave de tradução da mensagem que explica o erro. */
export function errorMessageKey(error) {
  if (error instanceof ApiError) {
    if (error.status === HTTP_UNAUTHORIZED) return "error.passwordWrong";
    if (error.status === HTTP_NOT_FOUND) return "error.roomMissing";
    return "error.generic";
  }
  // O fetch lança TypeError quando não consegue falar com o servidor.
  if (error instanceof TypeError) return "error.network";
  return "error.generic";
}
