// Teclas do campo de código: Tab indenta e Shift+Tab tira a indentação, como num editor de código.
//
// Num campo de texto comum, Tab pula para o próximo campo. Para quem usa só o teclado isso seria uma
// armadilha, então existe uma saída: Esc e, em seguida, Tab (ou Shift+Tab) move o foco normalmente.

const INDENT = "    "; // quatro espaços
const INDENT_WIDTH = INDENT.length;

function removeOneIndent(line) {
  if (line.startsWith("\t")) {
    return { line: line.slice(1), removed: 1 };
  }
  const leadingSpaces = line.match(new RegExp(`^ {1,${INDENT_WIDTH}}`))?.[0].length ?? 0;
  return { line: line.slice(leadingSpaces), removed: leadingSpaces };
}

/**
 * Calcula o que muda ao apertar Tab (`outdent` falso) ou Shift+Tab (`outdent` verdadeiro).
 * Sem seleção, Tab insere a indentação no cursor. Com várias linhas selecionadas, todas são indentadas.
 * Devolve o trecho a substituir (`replaceStart` até `replaceEnd`), o novo texto dele (`replacement`)
 * e como fica a seleção depois.
 */
export function changeIndentation(text, selectionStart, selectionEnd, outdent) {
  if (!outdent && selectionStart === selectionEnd) {
    return {
      replaceStart: selectionStart,
      replaceEnd: selectionStart,
      replacement: INDENT,
      selectionStart: selectionStart + INDENT_WIDTH,
      selectionEnd: selectionStart + INDENT_WIDTH,
    };
  }

  // A seleção pode começar ou terminar no meio de uma linha: trabalhamos com as linhas inteiras.
  // Se a seleção termina logo depois de uma quebra de linha, a linha seguinte não conta.
  const effectiveEnd = selectionEnd > selectionStart && text[selectionEnd - 1] === "\n" ? selectionEnd - 1 : selectionEnd;
  const firstLineStart = text.lastIndexOf("\n", selectionStart - 1) + 1;
  const lineBreakAfter = text.indexOf("\n", effectiveEnd);
  const lastLineEnd = lineBreakAfter === -1 ? text.length : lineBreakAfter;

  const lines = text.slice(firstLineStart, lastLineEnd).split("\n");
  const changes = lines.map((line) => {
    if (outdent) {
      const { line: newLine, removed } = removeOneIndent(line);
      return { line: newLine, delta: -removed };
    }
    // Linhas vazias ficam vazias: indentá-las só deixaria espaços sobrando no fim da linha.
    return line === "" ? { line, delta: 0 } : { line: INDENT + line, delta: INDENT_WIDTH };
  });

  const totalDelta = changes.reduce((sum, change) => sum + change.delta, 0);
  return {
    replaceStart: firstLineStart,
    replaceEnd: lastLineEnd,
    replacement: changes.map((change) => change.line).join("\n"),
    selectionStart: Math.max(firstLineStart, selectionStart + changes[0].delta),
    selectionEnd: Math.max(firstLineStart, selectionEnd + totalDelta),
  };
}

// Escreve no campo pelo mesmo caminho da digitação, para o "desfazer" (Ctrl+Z) e o salvamento automático funcionarem.
function replaceRange(textarea, change) {
  textarea.setSelectionRange(change.replaceStart, change.replaceEnd);
  const inserted = document.execCommand("insertText", false, change.replacement);
  if (!inserted) {
    textarea.setRangeText(change.replacement, change.replaceStart, change.replaceEnd, "end");
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }
  textarea.setSelectionRange(change.selectionStart, change.selectionEnd);
}

/** Liga as teclas de código ao campo. */
export function setUpCodeKeys(textarea) {
  let nextTabLeavesField = false;

  textarea.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      nextTabLeavesField = true;
      return;
    }
    const isPlainTab = event.key === "Tab" && !event.ctrlKey && !event.altKey && !event.metaKey;
    if (!isPlainTab) {
      nextTabLeavesField = false;
      return;
    }
    if (nextTabLeavesField) {
      nextTabLeavesField = false;
      return; // deixa o Tab mover o foco
    }

    event.preventDefault();
    const change = changeIndentation(textarea.value, textarea.selectionStart, textarea.selectionEnd, event.shiftKey);
    if (change.replacement !== textarea.value.slice(change.replaceStart, change.replaceEnd)) {
      replaceRange(textarea, change);
    }
  });
  textarea.addEventListener("blur", () => {
    nextTabLeavesField = false;
  });
}
