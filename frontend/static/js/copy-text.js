// Copia um texto para a área de transferência.

/** Copia `text`. Devolve true se conseguiu. */
export async function copyText(text) {
  // navigator.clipboard só existe em HTTPS ou localhost.
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Permissão negada: tenta o jeito antigo abaixo.
    }
  }
  return copyUsingSelection(text);
}

// Na rede local (http://192.168...) o jeito moderno não funciona; este funciona em qualquer lugar.
function copyUsingSelection(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.opacity = "0";
  document.body.append(textArea);
  textArea.select();

  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }
  textArea.remove();
  return copied;
}
