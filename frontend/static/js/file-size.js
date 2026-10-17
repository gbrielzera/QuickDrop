// Funções puras para mostrar tamanhos e nomes de arquivo.

const BYTES_PER_UNIT = 1024;
const UNITS = ["B", "KB", "MB", "GB"];
const MAX_FRACTION_DIGITS = 1;
const FALLBACK_FILE_NAME = "quickdrop-file";

/** Mostra um tamanho de forma legível: 1536 vira "1,5 KB" (português) ou "1.5 KB" (inglês). */
export function formatFileSize(bytes, language) {
  let value = bytes;
  let unitIndex = 0;
  while (value >= BYTES_PER_UNIT && unitIndex < UNITS.length - 1) {
    value /= BYTES_PER_UNIT;
    unitIndex++;
  }
  const number = new Intl.NumberFormat(language, { maximumFractionDigits: MAX_FRACTION_DIGITS }).format(value);
  return `${number} ${UNITS[unitIndex]}`;
}

/**
 * Deixa um nome de arquivo seguro para salvar. O nome vem de outro aparelho, então tiramos
 * barras e caracteres que o Windows não aceita (isso também impede nomes como "../../x").
 */
export function safeFileName(name) {
  const cleaned = name
    .replace(/[\u0000-\u001f\\/:*?"<>|]/g, "_")
    .trim();
  return cleaned === "" || /^\.+$/.test(cleaned) ? FALLBACK_FILE_NAME : cleaned;
}
