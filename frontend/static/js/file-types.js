// Funções puras sobre o tipo e o nome dos arquivos: o que pode ser pré-visualizado e como nomear imagens coladas.

// Só tipos de imagem que o navegador desenha sem executar nada. SVG fica de fora de propósito:
// ele pode conter script, e o tipo vem de outro aparelho (não dá para confiar).
const PREVIEWABLE_IMAGE_TYPES = new Set([
  "image/png",
  "image/jpeg",
  "image/gif",
  "image/webp",
  "image/avif",
  "image/bmp",
]);

// Imagens maiores que isto não são pré-visualizadas (baixar e abrir seria lento); dá para baixar normalmente.
export const MAX_PREVIEW_BYTES = 20 * 1024 * 1024;

const EXTENSION_BY_IMAGE_TYPE = {
  "image/png": "png",
  "image/jpeg": "jpg",
  "image/gif": "gif",
  "image/webp": "webp",
  "image/avif": "avif",
  "image/bmp": "bmp",
};
const FALLBACK_EXTENSION = "bin";

// Ao colar um print, os navegadores dão sempre o mesmo nome ("image.png"), que não ajuda a distinguir um do outro.
const GENERIC_PASTED_NAME = /^(image|imagem|blob)(\.\w+)?$/i;

/** True se o arquivo é uma imagem que pode ser mostrada na lista, sem baixar. */
export function isPreviewableImage(mimeType, sizeInBytes) {
  return PREVIEWABLE_IMAGE_TYPES.has(mimeType) && sizeInBytes <= MAX_PREVIEW_BYTES;
}

function twoDigits(number) {
  return String(number).padStart(2, "0");
}

/**
 * Nome para um arquivo colado com Ctrl+V. Arquivos copiados do computador mantêm o nome;
 * imagens coladas (que chegam como "image.png") ganham a data e a hora: captura-20261018-143005.png.
 */
export function pastedFileName(file, now) {
  if (file.name && !GENERIC_PASTED_NAME.test(file.name)) {
    return file.name;
  }
  const date = `${now.getFullYear()}${twoDigits(now.getMonth() + 1)}${twoDigits(now.getDate())}`;
  const time = `${twoDigits(now.getHours())}${twoDigits(now.getMinutes())}${twoDigits(now.getSeconds())}`;
  const extension = EXTENSION_BY_IMAGE_TYPE[file.type] ?? FALLBACK_EXTENSION;
  return `captura-${date}-${time}.${extension}`;
}
