// Desenha um QR Code como imagem SVG.

import qrcode from "./vendor/qrcode.mjs";

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
const AUTO_QR_SIZE = 0;
const ERROR_CORRECTION_LEVEL = "M";
// Margem branca ao redor do QR Code. Sem ela, algumas câmeras não leem.
const QUIET_ZONE_MODULES = 4;

// O QR Code sempre é tinta escura sobre fundo branco, mesmo no tema escuro: é o que as câmeras leem melhor.
const QR_BACKGROUND = "#ffffff";
const QR_INK = "#101820";

function createSvgElement(tagName, attributes) {
  const element = document.createElementNS(SVG_NAMESPACE, tagName);
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, value);
  }
  return element;
}

// Um quadradinho escuro na posição (column, row), desenhado com a linha "M x,y h1 v1 h-1 z".
function buildDarkModulesPath(qr) {
  let pathData = "";
  for (let row = 0; row < qr.getModuleCount(); row++) {
    for (let column = 0; column < qr.getModuleCount(); column++) {
      if (qr.isDark(row, column)) {
        pathData += `M${column + QUIET_ZONE_MODULES},${row + QUIET_ZONE_MODULES}h1v1h-1z`;
      }
    }
  }
  return pathData;
}

/** Cria o SVG do QR Code de `text`. `description` é lido por leitores de tela. */
export function createQrCodeSvg(text, description) {
  const qr = qrcode(AUTO_QR_SIZE, ERROR_CORRECTION_LEVEL);
  qr.addData(text);
  qr.make();

  const totalModules = qr.getModuleCount() + QUIET_ZONE_MODULES * 2;
  const svg = createSvgElement("svg", {
    viewBox: `0 0 ${totalModules} ${totalModules}`,
    role: "img",
    "aria-label": description,
    "shape-rendering": "crispEdges",
  });
  svg.append(
    createSvgElement("rect", { width: totalModules, height: totalModules, fill: QR_BACKGROUND }),
    createSvgElement("path", { d: buildDarkModulesPath(qr), fill: QR_INK }),
  );
  return svg;
}
