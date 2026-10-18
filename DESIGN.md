---
name: QuickDrop
description: Uma sala é uma linha de metrô; cada aparelho é uma estação e o arquivo viaja entre elas.
colors:
  ground: "#f4f6f8"
  surface: "#ffffff"
  ink: "#101820"
  ink-soft: "#3b4652"
  outline: "#101820"
  placeholder: "#5d6874"
  line-blue: "#0455a1"
  on-line-blue: "#ffffff"
  line-green: "#007a5e"
  on-line-green: "#ffffff"
  signal-yellow: "#ffd100"
  on-signal: "#101820"
  danger: "#b3261e"
  ground-dark: "#0d141b"
  surface-dark: "#141d26"
  ink-dark: "#eef2f6"
  ink-soft-dark: "#b4bfca"
  outline-dark: "#5b6b7b"
  line-blue-dark: "#6aaeff"
  line-green-dark: "#3dd6a6"
  danger-dark: "#ff8a80"
typography:
  display:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 1.2rem + 4vw, 4.5rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 800
    lineHeight: 1.45
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 800
    lineHeight: 1.35
  body:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 500
    lineHeight: 1.45
  label:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.45
rounded:
  sm: "4px"
  md: "6px"
  pill: "999px"
spacing:
  xs: "0.5rem"
  sm: "1rem"
  md: "1.5rem"
  lg: "2rem"
  gutter: "clamp(1rem, 5vw, 4.5rem)"
components:
  button-blue:
    backgroundColor: "{colors.line-blue}"
    textColor: "{colors.on-line-blue}"
    typography: "{typography.title}"
    rounded: "{rounded.md}"
    height: "60px"
  button-green:
    backgroundColor: "{colors.line-green}"
    textColor: "{colors.on-line-green}"
    typography: "{typography.title}"
    rounded: "{rounded.md}"
    height: "60px"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    rounded: "{rounded.md}"
    height: "60px"
  input-text:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "60px"
    padding: "0 1rem"
  sign:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "1.5rem"
  tag:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.on-signal}"
    rounded: "{rounded.sm}"
    padding: "0.125rem 0.625rem"
  train-chip:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.on-signal}"
    rounded: "{rounded.pill}"
    padding: "0.25rem 1rem"
---

# Design System: QuickDrop

## Overview

**Creative North Star: "Linhas de Metrô"**

Uma sala é uma linha de metrô: cada aparelho é uma estação e cada arquivo viaja entre elas. O sistema se parece com sinalização de estação: placas esmaltadas com contorno firme, círculos de linha e um diagrama de rota. É calmo, direto e legível de longe, feito para quem quer concluir uma tarefa no celular ou no PC. Claro e escuro seguem o aparelho (`prefers-color-scheme`); no escuro o fundo vira tinta e as cores de linha clareiam.

Criar e entrar têm o mesmo peso visual: dois painéis de mesma largura, um de faixa azul e outro de faixa verde. O único elemento de assinatura é o diagrama da rota; nada mais compete com ele.

**Key Characteristics:**
- Cor significa função: azul é criar/origem, verde é entrar/destino, amarelo é só tempo restante e o que está em trânsito.
- Contorno de tinta de 3px e raio de 6px em toda placa, campo e botão.
- Uma família (Barlow) em três pesos, sem fonte de exibição separada.
- Plano: profundidade vem de contorno e faixa de cor, nunca de sombra.
- Uma única animação autoral, o trem que percorre a linha.

## Colors

Cinza-azulado quase branco com tinta azul-marinho, duas cores de linha saturadas e um amarelo de sinalização. Os valores do frontmatter são do tema claro; as chaves `-dark` são as trocas do tema escuro (verde e azul clareiam; amarelo, `on-*` e raio não mudam).

### Primary
- **Linha Azul** (`line-blue`): criar sala, origem. Faixa do painel Criar, botão azul, item selecionado do seletor de expiração, caixa marcada, cursor de texto. No escuro vira `line-blue-dark`, com texto de tinta sobre ele.

### Secondary
- **Linha Verde** (`line-green`): entrar, destino. Faixa do painel Entrar, botão verde, segunda metade da linha do diagrama. No escuro vira `line-green-dark`.

### Tertiary
- **Amarelo de Sinalização** (`signal-yellow`): só tempo restante (etiqueta) e o arquivo em trânsito (cápsula do trem). Também a seleção de texto e o aviso sem JavaScript. Texto sempre `on-signal`.

### Neutral
- **Fundo Gelo** (`ground`) e **Placa Branca** (`surface`): fundo da página e fundo das placas e campos.
- **Tinta Marinho** (`ink`): texto, contorno de foco, pontos de estação. **Tinta Suave** (`ink-soft`): texto de apoio e dicas. **Contorno** (`outline`): bordas de 3px; no escuro fica cinza-azulado (`outline-dark`) em vez de tinta. **Placeholder** (`placeholder`).
- **Vermelho de Erro** (`danger`): só texto de erro.

### Named Rules
**The Line-Means-Job Rule.** Azul e verde só aparecem onde a ação é criar ou entrar; amarelo só onde há tempo restante ou algo em trânsito. Nunca use uma cor de linha como decoração.

**The Ink-On-Line Rule.** Texto sobre cor de linha usa o par `on-*` do token; no escuro ele é tinta, não branco.

## Typography

**Display Font:** Barlow (com Segoe UI, system-ui, sans-serif)
**Body Font:** Barlow (mesma família)
**Label/Mono Font:** nenhuma para a interface (números usam `tabular-nums`). A única exceção é o **código**, que usa a fonte monoespaçada do sistema (`ui-monospace`, Cascadia Code, SF Mono, Menlo, Consolas...), sem baixar nada, sem ligaduras e sem quebra de linha.

**Character:** Barlow é condensada e de sinalização, firme em 800 nos títulos e em 500 no corpo. Hospedada localmente (500, 700, 800, licença SIL OFL), sem CDN.

### Hierarchy
- **Display** (800, clamp(2.25rem, 1.2rem + 4vw, 4.5rem), 1, -0.03em): o título da tela inicial; `text-wrap: balance`.
- **Headline** (800, 1.75rem, -0.01em): faixas das placas, nome das estações, marca (1.5rem no celular).
- **Title** (800, 1.375rem): botões, texto de linha de apoio (`lead`, 44ch), código digitado.
- **Body** (500, 1.125rem, 1.45): texto corrido e detalhes de estação.
- **Label** (700, 1rem): rótulos de campo e legendas, em caixa de frase (não em caixa alta); dicas em 500, 1rem.

### Named Rules
**The Three-Weights Rule.** Só 500, 700 e 800. Hierarquia vem de peso e tamanho, não de outra fonte.

## Layout

Página com margem lateral fluida (`gutter`, de 1rem a 4.5rem). Barra do topo de 88px (64px no celular) com contorno inferior de 4px. Os painéis ficam em duas colunas iguais com 2rem de intervalo e empilham sob 760px (intervalo 1.25rem). Dentro da placa, o corpo usa 1.5rem de respiro e 1.25rem entre itens. O diagrama ocupa a largura total abaixo dos painéis: três estações em colunas iguais na horizontal; sob 760px vira uma coluna vertical, com a linha à esquerda. Colunas de texto limitadas (44ch na linha de apoio, 62ch nas notas, 34rem nas páginas de coluna única). Alvos de toque de no mínimo 44px; botões e campos têm 60px.

## Elevation & Depth

Sistema plano, sem nenhuma sombra. A profundidade vem do contorno de 3px, da faixa colorida no topo da placa e do contraste entre `ground` e `surface`. Estado vem de cor, brilho e deslocamento, nunca de sombra.

### Named Rules
**The Flat-Enamel Rule.** Placas são planas como esmalte; separe camadas com contorno, não com sombra.

## Shapes

Cantos de 6px (`rounded.md`) em placas, campos, botões, QR e seletor; 4px em etiquetas e na caixa de seleção; cápsula total (999px) só no trem; círculo (50%) nos círculos de linha e nas estações. Contorno padrão de 3px em tinta (`--stroke`). Pontos de estação: 56px com borda de 10px. A linha do diagrama tem 14px de espessura, cantos arredondados, azul na primeira metade e verde na segunda. As placas recortam o conteúdo (`overflow: hidden`) para a faixa herdar o raio.

## Components

### Buttons
- **Shape:** 6px, 60px de altura, largura total, texto 1.375rem em 800.
- **Variants:** azul (criar), verde (entrar), contorno (secundário, borda 3px de tinta, sem preenchimento).
- **Hover:** `brightness(1.1)`; o contorno só escurece a borda. **Pressed:** desce 2px. **Disabled/busy:** 60% de opacidade e cursor `progress`. **Focus:** contorno de tinta de 3px com 3px de afastamento.

### Cards / Containers (placa)
- Fundo `surface`, contorno de 3px, raio 6px, sem sombra. Faixa de 72px (56px no celular) com a cor da linha, círculo de linha invertido (fundo `on-*`, glifo na cor da linha) e título em 800. Corpo com 1.5rem de respiro.

### Inputs / Fields
- 60px, contorno de 3px, raio 6px, texto 1.375rem em 700 com 0.04em de espaço entre letras (o campo de link usa 1rem sem espaçamento). Hover e foco escurecem a borda para tinta; o foco acrescenta o contorno de 3px. Erro aparece como texto em `danger` em 700 abaixo do campo.
- Seletor de expiração: quatro segmentos separados por linhas de 3px; hover tinge o segmento com 14% de azul; marcado vira azul pleno; foco desenha contorno interno.
- Caixa de seleção: 1.75rem, contorno de 3px, raio 4px, marcada fica azul com visto.

### Etiqueta de tempo
- Amarelo de sinalização, raio 4px, 800, números tabulares. Usada só para o tempo restante (e a variante grande na sala). Some quando vazia.

### Navigation
- Barra do topo: círculo azul com glifo e marca em 800 à esquerda; seletor PT / EN à direita, botões de 44px, o ativo (`aria-pressed`) preenchido de tinta.

### Arquivos, texto e clips
- **Área de soltar:** contorno tracejado de 3px (cai no azul ao arrastar um arquivo por cima), botão azul de largura limitada. A fila de envio mostra nome, tamanho e uma barra de 1.25rem com contorno de 3px, preenchida de amarelo (o que está em trânsito).
- **Lista de arquivos e de clips:** itens separados por linha de 3px; nome em 800, tamanho em tom suave com números tabulares; ações em botões de contorno de 44px de altura. Excluir pede confirmação: o primeiro clique troca o texto por "Confirmar exclusão" em vermelho (`danger`) por 4 segundos.
- **Pré-visualização:** a imagem aparece dentro da própria linha, com contorno de 3px, raio de 6px, fundo `ground` e altura máxima de 20rem; o botão "Ver" vira "Ocultar". "Baixar tudo (.zip)" é um botão de contorno pequeno no alto da lista.
- **Campo e blocos de código:** mesmo contorno, raio e foco do campo de texto, com fonte monoespaçada de 0.95rem, tabulação de 4 colunas e rolagem para o lado em vez de quebrar linhas. O bloco guardado usa o mesmo estilo, com fundo `ground` e altura máxima de 16rem. Dica de teclado em texto suave logo abaixo do campo.
- **Campo de texto (textarea):** mesmo contorno, raio e foco dos campos de uma linha; só estica na vertical. O texto de um clip aparece num bloco `ground` com rolagem a partir de 9rem.
- **Aviso de conflito do texto:** caixa com contorno de `danger` de 3px, duas ações de contorno ("Usar a do outro aparelho", "Manter a minha"). Amarelo não é usado aqui: não é tempo nem trânsito.
- **Encerrar sala:** botão de contorno pequeno ao lado da etiqueta de tempo, com a mesma confirmação em duas etapas ("Confirmar: apaga tudo"). Quando a sala acaba, a tela vira o aviso "Sala encerrada" (mesma coluna estreita da tela de "Sala não encontrada").
- **Navegação da sala:** três âncoras de 44px com a aparência de botão de contorno (Arquivos, Texto, Convidar).
- **Linhas de estado:** parágrafos com `role="status"` em 700; `status--error` muda a cor para `danger`.

### Diagrama da rota (assinatura)
Três estações (aparelho de origem, sala com código e tempo restante, aparelho de destino) sobre uma linha azul-depois-verde, pontos de 56px. A cápsula amarela "arquivo" percorre a linha uma vez ao carregar (2.4s, `cubic-bezier(0.16, 1, 0.3, 1)`) e para entre a origem e a sala; sob `prefers-reduced-motion` não anima, e na versão vertical (sob 760px) fica oculta. É a única animação autoral do sistema.

## Do's and Don'ts

### Do:
- **Do** manter contorno de 3px e raio de 6px em toda superfície interativa nova.
- **Do** usar azul para criar/origem, verde para entrar/destino e amarelo só para tempo restante e o que está em trânsito.
- **Do** usar o foco de 3px em tinta com 3px de afastamento e tocar alvos de no mínimo 44px.
- **Do** respeitar `prefers-reduced-motion` em qualquer movimento novo.
- **Do** manter os mesmos estados: repouso, hover (brilho ou segmento tingido), pressionado (2px para baixo), desabilitado/ocupado (60%, cursor `progress`), erro (texto `danger`).

### Don't:
- **Don't** usar sombras, gradientes decorativos ou outra fonte além de Barlow 500/700/800 (exceto a fonte monoespaçada, só para código).
- **Don't** usar o amarelo ou as cores de linha como enfeite.
- **Don't** reunir criar e entrar num cartão único com abas, nem dar pesos diferentes aos dois.
- **Don't** hospedar fontes ou ativos em CDN; tudo funciona sem internet.
- **Don't** criar um segundo elemento de assinatura que dispute com o diagrama.

## Divergências registradas e resíduos

- Os rótulos estão em caixa de frase, não em caixa alta pequena como no contrato (aceito na revisão final); o painel Entrar não tem QR (o QR fica na página da sala do outro aparelho).
- Resíduos conhecidos, não canonizados: o QR de 20rem no desktop é mais estreito que o campo de link abaixo dele; no celular o link longo é cortado dentro do campo somente leitura (dá para copiar).
- Ideias adiadas: círculos de linha nas pontas da linha. (O diagrama já reage à presença: o ponto do outro aparelho fica verde quando ele está conectado, e a estação deste aparelho mostra "Sem conexão. Reconectando..." em `danger` quando a conexão cai.)
