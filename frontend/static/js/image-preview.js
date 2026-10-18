// Botão "Ver" / "Ocultar": mostra a imagem de um arquivo dentro da lista, sem precisar baixá-la.

import { createElement } from "./dom.js";
import { t } from "./i18n.js";
import { runWithBusyButton } from "./ui.js";

/**
 * Liga o botão de pré-visualização.
 * - container: onde a imagem aparece.
 * - imageName: descrição da imagem para leitores de tela (o nome do arquivo).
 * - loadBlob: baixa e descriptografa a imagem.
 * - onError: chamada se algo der errado.
 * Devolve `{ close }`, que esconde a imagem e libera a memória dela.
 */
export function setUpPreviewButton({ button, container, imageName, loadBlob, onError }) {
  let image = null;
  let imageUrl = null;

  function setLabel(messageKey) {
    button.dataset.i18n = messageKey;
    button.textContent = t(messageKey);
  }

  function close() {
    image?.remove();
    if (imageUrl) {
      URL.revokeObjectURL(imageUrl);
    }
    image = null;
    imageUrl = null;
    setLabel("files.view");
  }

  async function open() {
    const blob = await runWithBusyButton(button, "files.decrypting", loadBlob);
    imageUrl = URL.createObjectURL(blob);
    image = createElement("img", { className: "file__preview", attributes: { alt: imageName, decoding: "async" } });
    image.src = imageUrl;
    container.append(image);
    setLabel("files.hide");
  }

  button.addEventListener("click", async () => {
    if (image) {
      close();
      return;
    }
    try {
      await open();
    } catch (error) {
      onError(error);
    }
  });

  return { close };
}
