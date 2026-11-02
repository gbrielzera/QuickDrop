// Amarra o texto compartilhado ao número da versão do servidor.
//
// Sem isto, um servidor adulterado poderia entregar um texto antigo (que continua decifrando bem)
// fingindo que é a versão mais nova. Com o número da versão dentro do texto cifrado, o aparelho confere
// se o conteúdo recebido é mesmo o da versão que o servidor diz ter.

const VERSION_SEPARATOR = "\n";

/** Junta a versão ao texto, antes de criptografar. */
export function attachVersion(text, version) {
  return `${version}${VERSION_SEPARATOR}${text}`;
}

/** Separa a versão do texto, depois de descriptografar. Lança erro se não for a versão esperada. */
export function detachVersion(versionedText, expectedVersion) {
  const separatorIndex = versionedText.indexOf(VERSION_SEPARATOR);
  const claimedVersion = separatorIndex === -1 ? NaN : Number(versionedText.slice(0, separatorIndex));
  if (claimedVersion !== expectedVersion) {
    throw new Error("O texto recebido não é da versão que o servidor informou.");
  }
  return versionedText.slice(separatorIndex + VERSION_SEPARATOR.length);
}
