// Service worker do QuickDrop.
//
// Ele existe para o app poder ser instalado no celular e para mostrar uma página de "sem conexão"
// quando o servidor não responde. De propósito, NÃO guarda salas, arquivos nem a API em cache:
// tudo o que é da sala vem sempre do servidor, e uma sala em cache seria uma cópia esquecida de dados.

const CACHE_NAME = "quickdrop-offline-v1";
const OFFLINE_PAGE = "/static/offline.html";
// O que a página de "sem conexão" precisa para ficar com a cara do app.
const OFFLINE_FILES = [
  OFFLINE_PAGE,
  "/static/css/style.css",
  "/static/fonts/nunito-latin-600-normal.woff2",
  "/static/fonts/nunito-latin-700-normal.woff2",
  "/static/fonts/nunito-latin-800-normal.woff2",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_FILES)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  // Apaga o que uma versão antiga deste arquivo tenha guardado.
  event.waitUntil(
    caches
      .keys()
      .then((names) => Promise.all(names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  // Só as páginas (navegação) têm plano B. Arquivos, API e WebSocket seguem direto para o servidor.
  if (event.request.mode !== "navigate") {
    return;
  }
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE_PAGE)));
});
