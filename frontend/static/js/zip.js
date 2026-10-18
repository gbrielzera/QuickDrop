// Cria um arquivo .zip no navegador, sem biblioteca.
//
// Os arquivos entram sem compressão (método "store"): fotos, PDFs e vídeos já são comprimidos,
// então comprimir de novo quase não reduziria nada e deixaria tudo mais lento.
// Formato: [cabeçalho + conteúdo de cada arquivo][diretório central][fim do diretório central].

import { safeFileName } from "./file-size.js";

const LOCAL_FILE_HEADER_SIGNATURE = 0x04034b50;
const CENTRAL_DIRECTORY_SIGNATURE = 0x02014b50;
const END_OF_CENTRAL_DIRECTORY_SIGNATURE = 0x06054b50;

const VERSION_NEEDED = 20; // zip 2.0: o mais comum, qualquer programa abre
const UTF8_NAMES_FLAG = 0x0800; // os nomes estão em UTF-8 (acentos funcionam)
const STORE_METHOD = 0; // sem compressão
const MAX_ENTRIES = 0xffff; // o zip comum (não "zip64") guarda até 65535 arquivos

const LOCAL_HEADER_BYTES = 30;
const CENTRAL_ENTRY_BYTES = 46;
const END_RECORD_BYTES = 22;

// O zip guarda a data e a hora num formato antigo de 16 bits cada (o do MS-DOS).
const DOS_FIRST_YEAR = 1980;

const crcTable = buildCrcTable();

function buildCrcTable() {
  const table = new Uint32Array(256);
  for (let index = 0; index < 256; index++) {
    let value = index;
    for (let bit = 0; bit < 8; bit++) {
      value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table[index] = value >>> 0;
  }
  return table;
}

/** Soma de verificação (CRC-32) que o zip usa para detectar arquivos corrompidos. */
export function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

/** Data e hora no formato de 16 bits do zip. */
export function toDosDateTime(date) {
  const year = Math.max(date.getFullYear(), DOS_FIRST_YEAR);
  return {
    date: ((year - DOS_FIRST_YEAR) << 9) | ((date.getMonth() + 1) << 5) | date.getDate(),
    time: (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2),
  };
}

/** Evita nomes repetidos dentro do zip: o segundo "foto.png" vira "foto (2).png". */
export function uniqueNames(names) {
  const timesSeen = new Map();
  return names.map((name) => {
    const count = (timesSeen.get(name) ?? 0) + 1;
    timesSeen.set(name, count);
    if (count === 1) {
      return name;
    }
    const dot = name.lastIndexOf(".");
    const hasExtension = dot > 0;
    const base = hasExtension ? name.slice(0, dot) : name;
    const extension = hasExtension ? name.slice(dot) : "";
    return `${base} (${count})${extension}`;
  });
}

function buildLocalHeader(entry) {
  const header = new DataView(new ArrayBuffer(LOCAL_HEADER_BYTES));
  header.setUint32(0, LOCAL_FILE_HEADER_SIGNATURE, true);
  header.setUint16(4, VERSION_NEEDED, true);
  header.setUint16(6, UTF8_NAMES_FLAG, true);
  header.setUint16(8, STORE_METHOD, true);
  header.setUint16(10, entry.dosTime, true);
  header.setUint16(12, entry.dosDate, true);
  header.setUint32(14, entry.crc, true);
  header.setUint32(18, entry.size, true); // tamanho comprimido (igual ao original: sem compressão)
  header.setUint32(22, entry.size, true);
  header.setUint16(26, entry.nameBytes.length, true);
  header.setUint16(28, 0, true); // sem campo extra
  return new Uint8Array(header.buffer);
}

function buildCentralEntry(entry) {
  const header = new DataView(new ArrayBuffer(CENTRAL_ENTRY_BYTES));
  header.setUint32(0, CENTRAL_DIRECTORY_SIGNATURE, true);
  header.setUint16(4, VERSION_NEEDED, true); // versão que criou
  header.setUint16(6, VERSION_NEEDED, true); // versão necessária para abrir
  header.setUint16(8, UTF8_NAMES_FLAG, true);
  header.setUint16(10, STORE_METHOD, true);
  header.setUint16(12, entry.dosTime, true);
  header.setUint16(14, entry.dosDate, true);
  header.setUint32(16, entry.crc, true);
  header.setUint32(20, entry.size, true);
  header.setUint32(24, entry.size, true);
  header.setUint16(28, entry.nameBytes.length, true);
  // Os campos seguintes (extra, comentário, disco, atributos) ficam em zero.
  header.setUint32(42, entry.offset, true); // onde o cabeçalho do arquivo começa
  return new Uint8Array(header.buffer);
}

function buildEndRecord(entryCount, centralDirectorySize, centralDirectoryOffset) {
  const record = new DataView(new ArrayBuffer(END_RECORD_BYTES));
  record.setUint32(0, END_OF_CENTRAL_DIRECTORY_SIGNATURE, true);
  record.setUint16(8, entryCount, true);
  record.setUint16(10, entryCount, true);
  record.setUint32(12, centralDirectorySize, true);
  record.setUint32(16, centralDirectoryOffset, true);
  return new Uint8Array(record.buffer);
}

/**
 * Monta o .zip. `files` é uma lista de `{ name, blob, date }`. Devolve um Blob do tipo application/zip.
 * Quem chama garante nomes diferentes (veja `uniqueNames`); os nomes passam por `safeFileName`.
 */
export async function createZip(files) {
  if (files.length > MAX_ENTRIES) {
    throw new Error(`Arquivos demais para um zip (máximo ${MAX_ENTRIES}).`);
  }

  const encoder = new TextEncoder();
  const parts = [];
  const entries = [];
  let offset = 0;

  for (const file of files) {
    const bytes = new Uint8Array(await file.blob.arrayBuffer());
    const { date: dosDate, time: dosTime } = toDosDateTime(file.date);
    const entry = {
      nameBytes: encoder.encode(safeFileName(file.name)),
      size: bytes.length,
      crc: crc32(bytes),
      dosDate,
      dosTime,
      offset,
    };
    const localHeader = buildLocalHeader(entry);
    parts.push(localHeader, entry.nameBytes, bytes);
    offset += localHeader.length + entry.nameBytes.length + bytes.length;
    entries.push(entry);
  }

  const centralDirectoryOffset = offset;
  let centralDirectorySize = 0;
  for (const entry of entries) {
    const centralEntry = buildCentralEntry(entry);
    parts.push(centralEntry, entry.nameBytes);
    centralDirectorySize += centralEntry.length + entry.nameBytes.length;
  }
  parts.push(buildEndRecord(entries.length, centralDirectorySize, centralDirectoryOffset));

  return new Blob(parts, { type: "application/zip" });
}
