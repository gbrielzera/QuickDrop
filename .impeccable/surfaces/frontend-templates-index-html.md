---
version: 1
slug: "frontend-templates-index-html"
primary_target: "frontend/templates/index.html"
related_targets: ["frontend/templates/room.html"]
---

# Surface brief: tela inicial e página da sala

Modo: Operate. O visitante veio concluir uma tarefa (criar ou entrar numa sala) e a página da sala é onde ele troca arquivos e textos. Público: qualquer pessoa na internet, celular primeiro, pt-BR e inglês. Restrições: WCAG AA, claro e escuro seguindo o sistema do aparelho, sem CDN (funciona na rede local sem internet). Criar e entrar têm o mesmo peso. Evitar: visual de hacker ou cripto, cara de site de upload com anúncios, tom infantil.

Escolha do usuário: "Linhas de Metrô", o mundo sorteado, mantido.

Decisões em aberto: ilustração do trem do diagrama (por ora uma cápsula amarela com o rótulo "arquivo"); nomes das estações na sala (PC e celular genéricos até existir a lista de dispositivos).

## Direction contract

THESIS: A sala é uma linha de metrô: cada dispositivo é uma estação e cada arquivo viaja entre elas. Recusa o cartão único centralizado com abas, padrão das ferramentas de envio de arquivos.

OWN-WORLD: Fundo cinza-azulado muito claro com tinta azul-marinho escura. Duas cores de linha que significam algo: azul (criar, origem) e verde (entrar, destino); amarelo de sinalização só para tempo restante e para o que está em trânsito. Barlow em 500, 700 e 800, rótulos pequenos em caixa alta firme. Componentes como placas esmaltadas: contorno de tinta de 3px, raio de 6px, faixa colorida de linha no topo com um círculo de linha e um ícone desenhado. O diagrama da rota é o único elemento de assinatura. No escuro, o fundo vira tinta e as cores de linha clareiam.

STORY: Em um olhar o visitante entende que dois aparelhos são duas estações. Cria ou entra com o mesmo esforço. Confia porque o diagrama e o texto dizem o que é criptografado. Sai com código, link e QR Code na mão.

FIRST VIEWPORT: 1440x900. Barra de 88px: círculo Q e QuickDrop à esquerda, PT · EN à direita. Título de 72px na margem de 72px, "Do seu PC ao celular, em segundos.", linha de apoio abaixo. Dois painéis de mesma largura lado a lado: Criar sala (faixa azul: expiração 1h/12h/24h/48h, senha opcional, botão) e Entrar (faixa verde: campo do código, QR, botão). Abaixo, o diagrama em largura total: estação PC, estação Sala com código e tempo restante, estação celular, com uma cápsula amarela em trânsito. No celular os painéis empilham e o diagrama vira vertical.

FORM: Linhas de Metrô, posição 4 da minha lista ordenada de sete candidatos, atribuída pelo sorteio. SEED REFERENCE: seed:5e4dc4152176439a

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
