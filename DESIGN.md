---
name: QuickDrop
description: Um espaço suave e acolhedor onde dois aparelhos se encontram: violeta para criar, verde para entrar, âmbar para o tempo.
colors:
  ground: "#fbf7f2"
  surface: "#ffffff"
  ink: "#2b2a33"
  ink-soft: "#5b5866"
  outline: "#8c8799"
  line: "#e7e0d6"
  placeholder: "#6b6778"
  violet: "#6d4aff"
  on-violet: "#ffffff"
  violet-tint: "#ece8ff"
  on-violet-tint: "#3b2bb3"
  green: "#0d7a62"
  on-green: "#ffffff"
  green-tint: "#dcf5ec"
  on-green-tint: "#0b5d4b"
  amber: "#ffb020"
  on-amber: "#2b2a33"
  danger: "#c4352b"
  ground-dark: "#17141f"
  surface-dark: "#211d2e"
  ink-dark: "#f1eefb"
  ink-soft-dark: "#b7b0cc"
  outline-dark: "#7d7794"
  line-dark: "#342f47"
  placeholder-dark: "#a39cba"
  violet-dark: "#a592ff"
  on-violet-dark: "#17141f"
  violet-tint-dark: "#2d2650"
  on-violet-tint-dark: "#cbc2ff"
  green-dark: "#5fd6b4"
  on-green-dark: "#17141f"
  green-tint-dark: "#1d3a34"
  on-green-tint-dark: "#9eecd3"
  amber-dark: "#ffbf47"
  on-amber-dark: "#17141f"
  danger-dark: "#ff8f85"
typography:
  display:
    fontFamily: "Nunito, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 1.2rem + 4vw, 4.5rem)"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Nunito, Segoe UI, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    lineHeight: 1.45
  title:
    fontFamily: "Nunito, Segoe UI, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: 1.35
  body:
    fontFamily: "Nunito, Segoe UI, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.5
  label:
    fontFamily: "Nunito, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.5
rounded:
  field: "14px"
  card: "24px"
  pill: "999px"
spacing:
  xs: "0.5rem"
  sm: "1rem"
  md: "1.5rem"
  lg: "2rem"
  gutter: "clamp(1rem, 5vw, 4.5rem)"
components:
  button-violet:
    backgroundColor: "{colors.violet}"
    textColor: "{colors.on-violet}"
    typography: "{typography.title}"
    rounded: "{rounded.pill}"
    height: "60px"
  button-green:
    backgroundColor: "{colors.green}"
    textColor: "{colors.on-green}"
    typography: "{typography.title}"
    rounded: "{rounded.pill}"
    height: "60px"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    rounded: "{rounded.pill}"
    height: "60px"
  input-text:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    height: "60px"
    padding: "0 1rem"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "1.5rem"
  tag:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.on-amber}"
    rounded: "{rounded.pill}"
    padding: "0.125rem 0.75rem"
---

# Design System: QuickDrop

## Overview

**Creative North Star: "Encontro suave"**

Dois aparelhos se encontram numa sala acolhedora. O sistema é caloroso e arredondado: fundo creme (ou roxo quase preto no escuro), cartões brancos de cantos generosos com sombra suave, botões em pílula e uma fonte arredondada. Nada intimida; tudo é fácil de tocar com uma mão só.

Criar e entrar têm o mesmo peso visual: dois cartões de mesma largura, um com faixa violeta e outro com faixa verde. O diagrama de rota (origem, sala, destino) continua sendo o único elemento de assinatura.

**Key Characteristics:**
- Cor significa função: violeta é criar/origem, verde é entrar/destino, âmbar é só tempo restante e o que está em trânsito.
- Cantos generosos: 24px nos cartões, 14px nos campos, pílula (999px) em botões, etiquetas e seletor.
- Uma família (Nunito) em três pesos, sem fonte de exibição separada.
- Profundidade suave: sombra difusa nos cartões e faixas de cor em tom pastel, nunca contornos pesados.
- Contraste primeiro: todo texto passa de 4,5:1 e toda borda de campo ou botão passa de 3:1, nos dois temas.

## Colors

Creme quente com tinta quase preta, duas cores de função saturadas e um âmbar de sinalização. Os valores do frontmatter são do tema claro; as chaves `-dark` são do tema escuro (roxo quase preto, cores de função mais claras, texto de tinta sobre elas). O tema segue o aparelho (`prefers-color-scheme`).

### Primary
- **Violeta** (`violet`): criar, origem. Botão violeta, círculo de linha do cartão Criar, item selecionado do seletor de expiração, anel de foco, cursor de texto. A faixa do cartão usa o tom pastel `violet-tint` com texto `on-violet-tint`.

### Secondary
- **Verde** (`green`): entrar, destino. Botão verde, círculo de linha do cartão Entrar, segunda metade da linha do diagrama. Faixa em `green-tint` com texto `on-green-tint`.

### Tertiary
- **Âmbar** (`amber`): só tempo restante (etiqueta) e o arquivo em trânsito (cápsula do trem). Também a seleção de texto. Texto sempre `on-amber`.

### Neutral
- **Creme** (`ground`) e **Branco** (`surface`): fundo da página e fundo dos cartões e campos.
- **Tinta** (`ink`): texto; **Tinta Suave** (`ink-soft`): texto de apoio e dicas; **Placeholder** (`placeholder`).
- **Contorno** (`outline`): bordas de campos, botões de contorno e seletor (3:1 ou mais). **Linha** (`line`): divisórias e bordas decorativas dos cartões.
- **Vermelho de Erro** (`danger`): só texto de erro e confirmação de exclusão.

### Named Rules
**The Color-Means-Job Rule.** Violeta e verde só aparecem onde a ação é criar ou entrar; âmbar só onde há tempo restante ou algo em trânsito. Nunca use uma cor de função como decoração.

**The Contrast-First Rule.** Ao mudar uma cor, confira o contraste nos dois temas (4,5:1 para texto, 3:1 para bordas de campos e botões). O anel de foco usa o violeta (`--blue` no CSS) com 3px.

## Typography

**Display Font:** Nunito (com Segoe UI, system-ui, sans-serif)
**Body Font:** Nunito (mesma família)
**Mono:** só o **código** usa a fonte monoespaçada do sistema (`ui-monospace`, Cascadia Code, SF Mono, Menlo, Consolas...), sem baixar nada, sem ligaduras e sem quebra de linha.

**Character:** Nunito é arredondada e amigável, firme em 800 nos títulos e em 600 no corpo. Hospedada localmente (600, 700, 800, licença SIL OFL), sem CDN.

### Hierarchy
- **Display** (800, clamp(2.25rem, 1.2rem + 4vw, 4.5rem), 1.05, -0.02em): o título da tela inicial; `text-wrap: balance`.
- **Headline** (800, 1.5rem): faixas dos cartões, nome das estações, marca.
- **Title** (800, 1.25rem): botões e texto de apoio (`lead`, 44ch).
- **Body** (600, 1.125rem, 1.5): texto corrido.
- **Label** (700, 1rem): rótulos de campo e legendas, em caixa de frase.

### Named Rules
**The Three-Weights Rule.** Só 600, 700 e 800. Hierarquia vem de peso e tamanho, não de outra fonte.

## Layout

Página com margem lateral fluida (`gutter`, de 1rem a 4.5rem). Barra do topo de 80px com divisória fina inferior. Os cartões ficam em duas colunas iguais com 2rem de intervalo e empilham em telas estreitas. Alvos de toque de no mínimo 44px.

## Elevation & Depth

Sombra suave e difusa nos cartões (`--shadow`: `0 14px 34px` violeta translúcido no claro, preto translúcido no escuro). Divisórias finas de 1px em `line`. Estado vem de cor, brilho e deslocamento.

## Shapes

Cartões de 24px (`rounded.card`), campos, caixa de código e QR de 14px (`rounded.field`), botões, etiquetas, seletor de expiração e botões de idioma em pílula (999px); círculos (50%) nos círculos de linha e nas estações. Contorno de campos e botões de 1.5px em `outline`.

## Components

### Buttons
- **Shape:** pílula, 60px de altura, largura total, texto 1.25rem em 800.
- **Variants:** violeta (criar), verde (entrar), contorno (secundário, borda de 1.5px em `outline`, sem preenchimento). Os botões pequenos (Copiar, Baixar, Excluir) mantêm a pílula com 44px.
- **Hover:** `brightness(1.1)`; o contorno só escurece a borda. **Pressed:** desce 2px. **Disabled/busy:** 60% de opacidade e cursor `progress`. **Focus:** anel violeta de 3px com 3px de afastamento.

### Cards (cartão)
- Fundo `surface`, borda de 1px em `line`, raio de 24px, sombra suave. Faixa de 72px com o tom pastel da função, círculo de linha na cor plena da função e título em 800. Corpo com 1.5rem de respiro.

### Inputs / Fields
- 60px, borda de 1.5px em `outline`, raio de 14px, texto 1.375rem em 700 com 0.04em de espaço entre letras (o campo de link usa 1rem sem espaçamento). Hover e foco escurecem a borda; o foco acrescenta o anel violeta de 3px. Erro aparece como texto em `danger`.
- Seletor de expiração: quatro segmentos em pílula, separados por linhas finas; hover tinge o segmento com 14% de violeta; marcado vira violeta pleno; foco desenha anel interno.
- Caixa de seleção: 1.75rem, borda de 1.5px, raio 4px, marcada fica violeta com visto.

### Etiqueta de tempo
- Âmbar, pílula, 800, números tabulares. Usada só para o tempo restante (e a variante grande na sala). Some quando vazia.

### Navigation
- Barra do topo: círculo violeta com glifo e marca em 800 à esquerda; à direita, o seletor PT / EN, o ícone ⓘ (Sobre) e o botão de tema (lua ou sol), todos com alvo de 44px (40px em telas de 420px ou menos). O idioma ativo (`aria-pressed`) fica preenchido de tinta; o ⓘ ganha o tom pastel quando é a página atual (`aria-current`). Os dois ícones têm rótulo acessível e dica ao passar o mouse (`title`) nos dois idiomas. Em telas muito estreitas (menos de ~340px) os botões descem para uma segunda linha em vez de apertar a marca. Não há rodapé.

### Arquivos, texto e clips
- **Área de soltar:** borda tracejada de 1.5px (fica violeta ao arrastar um arquivo por cima) e botão violeta de largura limitada. A fila de envio mostra nome, tamanho e uma barra preenchida de âmbar (o que está em trânsito).
- **Lista de arquivos e de clips:** itens separados por linha fina; nome em 800, tamanho em tom suave com números tabulares; ações em botões de contorno pequenos. Excluir pede confirmação: o primeiro clique troca o texto por "Confirmar exclusão" em vermelho (`danger`).
- **Pré-visualização:** a imagem aparece dentro da própria linha, com raio de 14px e altura máxima de 20rem; o botão "Ver" vira "Ocultar". "Baixar tudo (.zip)" é um botão de contorno pequeno no alto da lista.
- **Campo e blocos de código:** mesma borda, raio e foco do campo de texto, com fonte monoespaçada de 0.95rem, tabulação de 4 colunas e rolagem para o lado em vez de quebrar linhas.
- **Campo de texto (textarea):** mesma borda, raio e foco dos campos de uma linha; só estica na vertical.
- **Aviso de conflito do texto:** caixa com borda de `danger` e duas ações de contorno ("Usar a do outro aparelho", "Manter a minha"). Âmbar não é usado aqui: não é tempo nem trânsito.
- **Dono da sala:** "Trancar sala" e "Encerrar sala" (botões de contorno pequenos ao lado da etiqueta de tempo; o encerramento pede confirmação em duas etapas). Convidados veem só um aviso.
- **Navegação da sala:** âncoras de 44px com a aparência de botão de contorno (Arquivos, Texto, Código, Convidar).
- **Linhas de estado:** parágrafos com `role="status"` em 700; `status--error` muda a cor para `danger`.
- **QR Code:** sempre tinta escura sobre fundo branco, nos dois temas, para continuar escaneável.

### Diagrama da rota (assinatura)
Três estações (aparelho de origem, sala com código e tempo restante, aparelho de destino) sobre uma linha violeta-depois-verde. A cápsula âmbar "arquivo" percorre a linha uma vez ao carregar e para entre a origem e a sala; sob `prefers-reduced-motion` fica parada. O ponto do outro aparelho fica verde quando ele está conectado, e a estação deste aparelho mostra "Sem conexão. Reconectando..." em `danger` quando a conexão cai.

## Do's and Don'ts

### Do:
- **Do** usar cantos generosos (24px, 14px, pílula) em toda superfície nova.
- **Do** usar violeta para criar/origem, verde para entrar/destino e âmbar só para tempo restante e o que está em trânsito.
- **Do** manter o anel de foco violeta de 3px com 3px de afastamento e alvos de no mínimo 44px.
- **Do** conferir contraste nos dois temas ao mexer em qualquer cor.
- **Do** respeitar `prefers-reduced-motion` em qualquer movimento novo.

### Don't:
- **Don't** usar outra fonte além de Nunito 600/700/800 (exceto a monoespaçada, só para código).
- **Don't** usar âmbar ou as cores de função como enfeite.
- **Don't** reunir criar e entrar num cartão único com abas, nem dar pesos diferentes aos dois.
- **Don't** hospedar fontes ou ativos em CDN; tudo funciona sem internet.
- **Don't** criar um segundo elemento de assinatura que dispute com o diagrama.
- **Don't** usar texto claro sobre o âmbar nem cinza claro sobre creme: abaixo de 4,5:1 não passa.

## Histórico

O visual anterior era "Linhas de Metrô" (placas esmaltadas de contorno firme, Barlow, azul e verde saturados, amarelo de sinalização, tudo plano). Foi trocado por este em 22/10/2026 a pedido do autor; a estrutura do HTML, os identificadores e o JavaScript não mudaram.
