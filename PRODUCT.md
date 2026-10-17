# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Qualquer pessoa na internet: visitantes anônimos, sem conta e sem cadastro, que precisam passar um arquivo ou um trecho de texto de um dispositivo para outro (PC, celular, tablet) sem abrir e-mail nem usar sites de upload lentos e cheios de anúncios. O celular é um dispositivo de primeira classe: boa parte dos usos acontece com um aparelho na mão e outro na mesa.

## Product Purpose

QuickDrop cria uma sala temporária com código, onde todos os dispositivos que entram veem os mesmos arquivos, o mesmo editor de texto e os mesmos clips (textos colados), atualizados em tempo real. Sucesso é o visitante terminar a transferência em segundos, sem aprender nada: criar a sala, entrar pelo outro aparelho (QR Code, link ou código) e pegar o conteúdo.

## Positioning

Criptografia de ponta a ponta desde o primeiro dia: o servidor guarda apenas dados embaralhados e nunca consegue ler arquivos, nomes de arquivos, textos ou clips, nem sabe a senha. Sem conta, sem anúncios e com expiração automática. Um concorrente que guarda os arquivos em texto puro não poderia afirmar isso com verdade.

## Operating Context

- Sala com código curto, expiração escolhida na criação (1h, 12h, 24h ou 48h; padrão 12h) e apagamento automático de tudo ao expirar.
- Entrada na sala por QR Code ou link (a chave de criptografia vai no fragmento `#k=...` e nunca chega ao servidor) ou pelo código longo digitado (`K7P3XM-HQ4T-9WZC`). A senha é opcional: quem quiser escolhe a própria; sem escolha, o app gera uma.
- Limites: 100 MB por arquivo e 500 MB por sala. Todos os tipos de arquivo são aceitos.
- Primeiro uso na rede local (HTTP via IP, celular acessando o PC); depois hospedado na internet com HTTPS.
- Fluxos de uso comuns: arrastar arquivos, colar print com Ctrl+V, colar texto e copiá-lo no outro aparelho.

## Capabilities and Constraints

- Funcionalidades do MVP: criar e entrar em sala, upload e download de arquivos com barra de progresso, editor de texto compartilhado em tempo real, clips de texto, QR Code, lista de dispositivos online, expiração automática, encerrar sala.
- Tempo real por WebSocket; arquivos trafegam por HTTP.
- A criptografia roda inteira no navegador; esquecer a senha significa perder o conteúdo, e isso precisa ficar claro ao usuário.
- Sem pré-visualização de HTML ou SVG enviado pelo usuário.
- Código simples e legível; backend (FastAPI) e frontend (Jinja2, CSS e JavaScript puro) em pastas separadas.
- Interface em português do Brasil e em inglês: textos nascem prontos para dois idiomas.
- Nome QuickDrop mantido; ainda não há logotipo.

## Brand Commitments

Nome: QuickDrop. Voz direta e tranquilizadora: explicar segurança sem jargão, sem assustar. Nenhum logotipo, paleta ou referência visual vinculante foi definido.

## Evidence on Hand

Não há depoimentos, clientes, métricas nem imagens. Existe apenas o planejamento técnico em `PLANEJAMENTO.md` e um esqueleto de página inicial. Nada disso deve ser apresentado como prova social; não inventar números de usuários, velocidade ou avaliações.

## Product Principles

1. Velocidade antes de tudo: da abertura do site à transferência, o mínimo de passos e de decisões.
2. Privacidade verdadeira e explicável: só afirmar o que a criptografia realmente garante, em linguagem simples.
3. Sem conta, sem atrito: o código e o link são a identidade.
4. Temporário por padrão: tudo expira e o usuário sempre vê quanto tempo resta.
5. Funciona bem no celular e na rede local, mesmo sem HTTPS no começo.

## Accessibility & Inclusion

Padrão WCAG 2.1 AA: contraste adequado, uso completo por teclado, foco visível, rótulos para leitores de tela e alvos de toque grandes. Celular primeiro: layout pensado para telas estreitas e uso com uma mão.
