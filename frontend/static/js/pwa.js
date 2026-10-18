// Registra o service worker, o que deixa o QuickDrop instalável como app no celular.
// O navegador só oferece isso em HTTPS (ou em localhost); na rede local por HTTP este código não faz nada.

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js").catch(() => {
    // Sem service worker o app funciona igual; só perde a instalação e a página de "sem conexão".
  });
}
