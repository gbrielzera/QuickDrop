// Aplica o tema escolhido pela pessoa antes de a página ser desenhada, para não "piscar" de claro para escuro.
// Script comum (não módulo) e minúsculo, carregado no <head>. O resto da lógica fica em theme-toggle.js.
try {
  const savedTheme = localStorage.getItem("quickdrop:theme");
  if (savedTheme === "light" || savedTheme === "dark") {
    document.documentElement.dataset.theme = savedTheme;
  }
} catch {
  // Sem localStorage (modo privado, por exemplo): o tema segue o do aparelho.
}
