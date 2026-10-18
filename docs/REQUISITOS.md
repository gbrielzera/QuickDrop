# QuickDrop: Documento de Requisitos

| | |
|---|---|
| **Produto** | QuickDrop, transferência de arquivos e textos entre dispositivos, em tempo real e com criptografia de ponta a ponta |
| **Versão do documento** | 1.0 |
| **Data** | 18/10/2026 |
| **Estado do produto** | No ar em https://quickdrop-syoti.mexicocentral.cloudapp.azure.com |
| **Documento irmão** | [Documento de Visão](VISAO.md) (por quê, para quem e como é o sistema) |

## Sumário

1. [Introdução](#1-introdução)
2. [Atores](#2-atores)
3. [Regras de negócio](#3-regras-de-negócio)
4. [Requisitos funcionais](#4-requisitos-funcionais)
5. [Requisitos não funcionais](#5-requisitos-não-funcionais)
6. [Restrições e premissas](#6-restrições-e-premissas)
7. [Casos de uso](#7-casos-de-uso)
8. [Critérios de aceitação](#8-critérios-de-aceitação)
9. [Interfaces externas](#9-interfaces-externas)
10. [Itens pendentes e fora de escopo](#10-itens-pendentes-e-fora-de-escopo)
11. [Rastreabilidade](#11-rastreabilidade)
12. [Glossário](#12-glossário)

---

## 1. Introdução

### 1.1 Objetivo
Registrar, de forma verificável, **o que o QuickDrop faz e com que qualidade**. Este documento é a referência para testar o sistema e para decidir mudanças.

### 1.2 Escopo
O QuickDrop é um site que cria **salas temporárias**. Quem entra numa sala vê, em tempo real, os mesmos arquivos, o mesmo texto, o mesmo código e os mesmos clips. Tudo é criptografado no navegador antes de sair do aparelho; o servidor só guarda dados embaralhados.

**Dentro do escopo:** salas, arquivos, texto, código, clips, tempo real, expiração, segurança, interface em dois idiomas, app instalável (PWA), hospedagem e operação.
**Fora do escopo:** contas de usuário, histórico permanente, compartilhamento público de arquivos por link, aplicativo nativo (veja [seção 10](#10-itens-pendentes-e-fora-de-escopo)).

### 1.3 Como ler os requisitos

| Campo | Significado |
|---|---|
| **ID** | `RF` = requisito funcional, `RNF` = não funcional, `RN` = regra de negócio, `UC` = caso de uso |
| **Prioridade** | **E** Essencial (sem isso o produto não serve), **I** Importante, **D** Desejável |
| **Estado** | ✅ implementado e testado · 🟡 implementado, falta validação real ou tem limitação · ⏳ pendente |

Os valores de limites (tamanhos, tempos, quantidades) são **configuráveis** no servidor; a tabela do [apêndice 9.3](#93-limites-e-constantes) mostra os valores atuais.

---

## 2. Atores

| Ator | Descrição | Principais objetivos |
|---|---|---|
| **Visitante** | Pessoa que abre o site, sem conta | Criar uma sala ou entrar numa |
| **Dono da sala** | O navegador que **criou** a sala | Tudo o que um convidado faz, mais trancar, destrancar e encerrar a sala |
| **Convidado** | Navegador que entrou na sala pelo link, QR Code, código ou senha | Enviar, baixar e apagar arquivos; editar texto e código; guardar e copiar clips e blocos de código |
| **Sistema (tarefas automáticas)** | Rotinas do servidor | Apagar salas expiradas, limpar contadores, resumir eventos de segurança |
| **Administrador** | Quem mantém o servidor | Publicar versões, acompanhar a saúde do site e do crédito, aplicar atualizações |
| **Serviços externos** | Let's Encrypt, GitHub Actions, Azure | Certificado HTTPS, verificações automáticas e hospedagem |

---

## 3. Regras de negócio

| ID | Regra |
|---|---|
| **RN-01** | Toda sala é **temporária**. Ao expirar ou ser encerrada, **tudo** nela é apagado (arquivos, texto, código, clips e registros). |
| **RN-02** | O tempo de vida da sala é escolhido na criação entre **1, 12, 24 ou 48 horas** (padrão 12 h) e **não pode ser estendido**. |
| **RN-03** | **Não existe conta.** O código da sala e o segredo (ou a senha) são a única identidade de acesso. |
| **RN-04** | O servidor **nunca** recebe nem consegue deduzir a senha, o segredo ou a chave de criptografia. |
| **RN-05** | Quem esquecer a senha escolhida **perde o conteúdo**: ninguém, nem o administrador, consegue recuperá-lo. |
| **RN-06** | Só o **dono** (navegador que criou a sala) pode **encerrar** e **trancar/destrancar** a sala. |
| **RN-07** | Convidados podem enviar e apagar arquivos, clips e editar texto e código: a sala é um espaço **compartilhado**. |
| **RN-08** | Sala **trancada** não aceita aparelhos novos; quem já entrou continua com acesso. |
| **RN-09** | **Todos os tipos de arquivo** são aceitos. Os únicos limites são de tamanho (por arquivo e por sala). |
| **RN-10** | O servidor nunca exibe HTML, SVG nem outro conteúdo enviado por usuários; arquivos são sempre entregues para **download**. |
| **RN-11** | O servidor tem **limites globais** (espaço total, número de salas ativas, aparelhos por sala) para não ser esgotado por poucas pessoas. |
| **RN-12** | O site **não guarda IP, código de sala nem conteúdo** em registros permanentes; só contagens de eventos de segurança. |

---

## 4. Requisitos funcionais

### 4.1 Salas e acesso

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RF-001 | O visitante cria uma sala escolhendo a expiração (1, 12, 24 ou 48 h). | E | ✅ |
| RF-002 | A sala recebe um **código de 6 caracteres** (alfabeto sem 0/O/1/I/L), único e aleatório. | E | ✅ |
| RF-003 | Sem senha própria, o sistema gera um **segredo de 12 caracteres** que vai no link e no QR Code. | E | ✅ |
| RF-004 | O criador pode escolher **senha própria** (mínimo de 10 caracteres). | I | ✅ |
| RF-005 | A tela da sala mostra o **link**, o **QR Code** e o **código completo** (`K7P3XM-HQ4T-9WZC-MPN2`) com botões de copiar. | E | ✅ |
| RF-006 | Entrar por **link ou QR Code** (o segredo viaja no fragmento `#k=`, que nunca chega ao servidor). | E | ✅ |
| RF-007 | Entrar digitando o **código completo** ou o **código curto + senha**. | E | ✅ |
| RF-008 | O segredo é **retirado da barra de endereço** depois de entrar e guardado só na aba. | I | ✅ |
| RF-009 | O dono pode **trancar e destrancar** a sala. | I | ✅ |
| RF-010 | O dono pode **encerrar** a sala (com confirmação em dois passos); todos os aparelhos são avisados na hora. | E | ✅ |
| RF-011 | A sala mostra o **tempo restante** e avisa quando acaba. | E | ✅ |
| RF-012 | A sala mostra **quantos aparelhos** estão conectados (presença). | I | ✅ |
| RF-013 | Um aparelho que já entrou **volta** à sala (recarregar a página ou sala trancada) sem digitar tudo de novo. | I | ✅ |
| RF-014 | O sistema informa mensagens claras para: sala inexistente ou expirada, senha incorreta, sala trancada, sala cheia, servidor cheio, muitas tentativas. | E | ✅ |

### 4.2 Arquivos

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RF-020 | Enviar arquivos **de qualquer tipo**, por seleção ou **arrastar e soltar**. | E | ✅ |
| RF-021 | O arquivo é **criptografado no navegador**, em blocos de 1 MB, antes do envio; o nome, o tipo e o tamanho originais também. | E | ✅ |
| RF-022 | Limite de **100 MB por arquivo** e **500 MB por sala**, avisados antes de enviar e conferidos no servidor. | E | ✅ |
| RF-023 | Mostrar **"Criptografando..."** durante o preparo do arquivo e uma **barra de progresso** durante o envio. | I | ✅ |
| RF-024 | Listar os arquivos da sala com nome, tipo, tamanho e horário, atualizado em tempo real. | E | ✅ |
| RF-025 | **Baixar** um arquivo: o navegador descriptografa e entrega o arquivo original. | E | ✅ |
| RF-026 | **Apagar** um arquivo (com confirmação) para liberar espaço. | E | ✅ |
| RF-027 | **Colar imagem** com Ctrl+V em qualquer lugar da sala vira um envio (`captura-AAAAMMDD-HHMMSS.png`). | I | ✅ |
| RF-028 | **Pré-visualizar** imagens comuns (PNG, JPEG, GIF, WebP, AVIF, BMP, até 20 MB) na própria lista. **Nunca** SVG ou HTML. | D | ✅ |
| RF-029 | **Baixar tudo em .zip**, criado no navegador, quando houver 2 ou mais arquivos, com nomes seguros e sem repetição. | D | ✅ |
| RF-030 | Detectar arquivo adulterado ou chave errada e **recusar** o conteúdo com mensagem, em vez de entregar dado corrompido. | E | ✅ |

### 4.3 Texto, código e clips

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RF-040 | **Editor de texto compartilhado**: o que uma pessoa escreve aparece nos outros aparelhos em tempo real (até 1 MB). | E | ✅ |
| RF-041 | Cada alteração tem **versão**; se dois aparelhos editam ao mesmo tempo, o servidor recusa a segunda e a tela oferece **"Usar a do outro aparelho"** ou **"Manter a minha"**. | E | ✅ |
| RF-042 | Botões **Copiar tudo** e **Limpar** no editor. | I | ✅ |
| RF-043 | **Clips de texto**: guardar trechos colados (até 64 KB cada e 200 por sala), com **copiar** e **excluir** (com confirmação). | I | ✅ |
| RF-044 | **Ctrl+V fora de qualquer campo** guarda o texto colado como clip. | D | ✅ |
| RF-045 | **Editor de código compartilhado** com fonte monoespaçada, sem quebra de linha, tabulação de 4 colunas, **sem ligaduras** e sem autocorreção. | I | ✅ |
| RF-046 | No editor de código, **Tab** indenta, **Shift+Tab** remove a indentação e **Esc e depois Tab** sai do campo (acessibilidade por teclado). | I | ✅ |
| RF-047 | **Blocos de código**: guardar trechos (até 256 KB cada e 200 por sala) que são copiados **exatamente** como guardados (tabs, espaços no fim, acentos). | I | ✅ |
| RF-048 | Texto, código, clips e blocos de código são **criptografados no navegador**; o servidor guarda só dados embaralhados. | E | ✅ |

### 4.4 Tempo real

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RF-050 | Avisos em tempo real por **WebSocket**: arquivo adicionado ou apagado, texto e código alterados, clips adicionados ou apagados, presença, sala encerrada ou expirada. | E | ✅ |
| RF-051 | Ao perder a conexão, o navegador **reconecta sozinho** com espera crescente (1 s até 30 s) e, ao voltar, **confere tudo de novo** com o servidor. | E | ✅ |
| RF-052 | A tela mostra quando **este aparelho está sem conexão**. | I | ✅ |
| RF-053 | Se a sala deixou de existir enquanto o aparelho estava offline, o sistema avisa em vez de tentar reconectar para sempre. | I | ✅ |
| RF-054 | Funcionamento com a **tela do celular apagada e acesa de novo**. | I | 🟡 reconexão implementada; falta confirmar em aparelho real |

### 4.5 Interface e instalação

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RF-060 | Interface em **português (Brasil) e inglês**, com troca imediata e escolha lembrada; o idioma inicial segue o navegador. | E | ✅ |
| RF-061 | **Tema claro e escuro** conforme o sistema do aparelho. | I | ✅ |
| RF-062 | Layout **pensado primeiro para celular** e que se adapta ao computador. | E | ✅ |
| RF-063 | **App instalável (PWA)**: manifesto, ícones, cor da barra e página "sem conexão" quando o servidor não responde. O app **não guarda** salas nem arquivos em cache. | D | ✅ |
| RF-064 | Página **Sobre** com o que o servidor guarda, por quanto tempo e como denunciar abuso (contato configurável). | I | ✅ |
| RF-065 | Diagrama visual do caminho da transferência ("linhas de metrô") nas telas inicial e da sala. | D | ✅ |

### 4.6 Operação e administração

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RF-070 | **Limpeza automática** das salas expiradas a cada 5 minutos e ao iniciar o servidor. | E | ✅ |
| RF-071 | **Limites globais** configuráveis: espaço total, salas ativas e aparelhos por sala. | E | ✅ |
| RF-072 | **Verificação de saúde** (`/api/health`) usada pelo Docker e pelo monitoramento externo. | E | ✅ |
| RF-073 | **Resumo horário de eventos de segurança**, sem dados pessoais. | I | ✅ |
| RF-074 | **Implantação por Docker** com Caddy (HTTPS automático) e volume persistente. | E | ✅ |
| RF-075 | **Atualizações automáticas** do sistema e das imagens base, com reinício de madrugada quando necessário. | I | ✅ |
| RF-076 | **Alertas**: site fora do ar (GitHub Actions) e crédito da hospedagem (orçamento do Azure). | I | ✅ |

---

## 5. Requisitos não funcionais

### 5.1 Segurança e privacidade

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RNF-001 | **Criptografia de ponta a ponta**: o conteúdo é cifrado no navegador (XChaCha20-Poly1305) e o servidor não possui a chave. | E | ✅ |
| RNF-002 | A senha passa por **Argon2id** no navegador; a chave de acesso (`authKey`) e a de criptografia são derivadas separadamente, e o servidor recebe **só a primeira**. | E | ✅ |
| RNF-003 | O servidor guarda apenas um **hash Argon2** da `authKey`. | E | ✅ |
| RNF-004 | O segredo gerado tem **pelo menos ~59 bits** (12 caracteres de 31) e a senha própria **no mínimo 10 caracteres**. | E | ✅ |
| RNF-005 | **HTTPS obrigatório** em produção, com HSTS, certificado automático e redirecionamento de HTTP. | E | ✅ |
| RNF-006 | **Cookies** `HttpOnly`, `SameSite=Strict` e `Secure`, assinados, ligados ao id interno da sala e válidos só até a sala expirar. | E | ✅ |
| RNF-007 | **Controle de acesso** em todas as rotas de sala: sem cookie, 401; convidado tentando ação de dono, 403. | E | ✅ |
| RNF-008 | **Política de segurança de conteúdo (CSP)** rígida, sem scripts embutidos nem de outros sites; `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`. | E | ✅ |
| RNF-009 | O código **nunca** insere dados de usuário como HTML; nomes de arquivo e textos entram como texto. | E | ✅ |
| RNF-010 | **Limite de tentativas por IP**: senhas erradas, consultas, criação de salas, uploads e teto geral de pedidos, com resposta 429 e `Retry-After`. | E | ✅ |
| RNF-011 | **Validação estrita** das entradas (base64 rígido, tamanhos, formato de códigos e ids). | E | ✅ |
| RNF-012 | **Sem injeção de SQL**: acesso ao banco só por ORM com parâmetros. | E | ✅ |
| RNF-013 | Arquivos gravados no disco com **nome aleatório (UUID)**, nunca o original; downloads sempre como anexo. | E | ✅ |
| RNF-014 | Segredos de configuração (`SECRET_KEY`) fora do código e do Git, com permissão restrita no servidor. | E | ✅ |
| RNF-015 | O WebSocket confere a **origem** e libera conexões só para o endereço do próprio site; limites de tamanho de mensagem e de aparelhos por sala. | I | ✅ |
| RNF-016 | **Sem registros de acesso** (IP e códigos); registros do Docker com rotação. | I | ✅ |
| RNF-017 | Servidor endurecido: SSH só por chave e só do IP do administrador, contêiner sem privilégios, porta do app não exposta, documentação da API desligada. | I | ✅ |
| RNF-018 | Dependências **auditadas** (pip-audit) e monitoradas (Dependabot e verificação mensal das bibliotecas copiadas). | I | ✅ |

### 5.2 Desempenho e capacidade

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RNF-020 | Derivar as chaves a partir da senha leva **menos de ~1 segundo** em um celular comum. | I | 🟡 medido só no computador; falta medir em celular |
| RNF-021 | Arquivos são processados em **blocos de 1 MB** para não carregar o arquivo inteiro na memória ao criptografar. | E | ✅ |
| RNF-022 | O servidor atende com folga o uso previsto (dezenas de salas e poucos aparelhos por sala) em **1 vCPU e 1 GiB**, usando limites e filas para não esgotar memória. | I | ✅ |
| RNF-023 | O envio de um arquivo de **100 MB** pela internet móvel (4G) conclui sem erro. | I | 🟡 testado 20 MB na internet e 100 MB localmente; falta 100 MB no 4G |

### 5.3 Usabilidade e acessibilidade

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RNF-030 | Meta de acessibilidade **WCAG 2.1 AA**: contraste, uso completo por teclado, foco visível, rótulos para leitores de tela, alvos de toque grandes. | E | 🟡 seguido no projeto; sem auditoria formal |
| RNF-031 | Concluir uma transferência **sem aprender nada**: criar sala, entrar pelo outro aparelho e pegar o conteúdo em poucos passos. | E | ✅ |
| RNF-032 | Textos de segurança em **linguagem simples**, sem jargão, e sem prometer o que a criptografia não garante. | I | ✅ |
| RNF-033 | Sem cadastro, sem anúncios, sem rastreadores. | E | ✅ |

### 5.4 Compatibilidade

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RNF-040 | Funciona em navegadores modernos com WebAssembly, WebSocket e `sessionStorage`. | E | 🟡 validado no Chrome/Edge (computador e celular); outros navegadores sem teste formal |
| RNF-041 | Funciona em **rede local por HTTP** (com cópia de texto de reserva, pois a API de área de transferência exige HTTPS) e na internet por HTTPS. | I | ✅ |

### 5.5 Confiabilidade e disponibilidade

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RNF-050 | O servidor **reinicia sozinho** após falha ou reinício da máquina; o banco e os arquivos ficam em **volume persistente**. | E | ✅ |
| RNF-051 | Falha de um envio interrompido **não deixa resíduo**: arquivo parcial é apagado e nenhum erro é registrado. | I | ✅ |
| RNF-052 | Dois envios simultâneos **não ultrapassam** os limites de espaço. | I | ✅ |
| RNF-053 | O banco de dados de versões anteriores é **atualizado sozinho** na inicialização quando surge uma coluna nova. | I | ✅ |
| RNF-054 | Plano de recuperação: reconstruir o servidor a partir do repositório em cerca de 20 minutos. | I | ✅ |

### 5.6 Manutenibilidade e qualidade

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RNF-060 | **Código limpo** conforme `CLAUDE.md` (nomes claros, funções pequenas, comentários que explicam o porquê, tipos). | E | ✅ |
| RNF-061 | Backend e frontend em **pastas separadas**; a criptografia concentrada em **um só arquivo** do frontend. | E | ✅ |
| RNF-062 | **Testes automatizados**: 190 no backend e 72 no frontend, com formatação e análise estática (`ruff`). | E | ✅ |
| RNF-063 | Documentação do projeto atualizada (`PLANEJAMENTO.md`, `COMO-RODAR.md`, `DEPLOY.md`, `DESIGN.md`, este documento e o de Visão). | I | ✅ |

### 5.7 Portabilidade, custo e operação

| ID | Requisito | Prior. | Estado |
|---|---|---|---|
| RNF-070 | Empacotado em **Docker**; roda igual no computador e no servidor. | E | ✅ |
| RNF-071 | **Custo de hospedagem baixo ou grátis**. Hoje: US$ ~14/mês cobertos pelo crédito do Azure for Students (cerca de 7 meses). | I | 🟡 limitado pelo crédito |
| RNF-072 | Trocar de hospedagem não exige mudar o código (só `.env` e `DOMAIN`). | I | ✅ |

---

## 6. Restrições e premissas

### 6.1 Restrições
- **Tecnologia:** backend em Python (FastAPI), frontend em HTML/Jinja2, CSS e JavaScript puro (sem framework), banco SQLite.
- **Arquitetura:** um **único processo** de servidor (as conexões em tempo real e os contadores de limite ficam na memória).
- **Hospedagem atual:** uma VM pequena do Azure for Students no México Central (a assinatura só permite 5 regiões).
- **Sem recuperação de senha:** consequência direta da criptografia de ponta a ponta.
- **Limitação da criptografia no navegador:** o JavaScript vem do servidor; um servidor comprometido poderia entregar código malicioso. Mitigação: endurecimento do servidor e CSP.

### 6.2 Premissas
- Quem usa tem um navegador atualizado e aceita cookies de sessão da sala.
- O crédito do Azure for Students dura cerca de 7 meses; depois disso é preciso migrar a hospedagem.
- Os dispositivos conseguem se conectar por WebSocket; redes que bloqueiam WebSocket reduzem o tempo real (o conteúdo ainda é conferido ao reconectar).

---

## 7. Casos de uso

| ID | Caso de uso | Ator | Requisitos |
|---|---|---|---|
| UC-01 | Criar sala | Visitante | RF-001 a RF-005 |
| UC-02 | Entrar na sala por link ou QR Code | Visitante | RF-006, RF-008, RF-012 |
| UC-03 | Entrar na sala por código e senha | Visitante | RF-007, RF-014 |
| UC-04 | Enviar arquivo | Dono, Convidado | RF-020 a RF-023, RF-027 |
| UC-05 | Baixar, pré-visualizar ou apagar arquivo | Dono, Convidado | RF-024 a RF-026, RF-028, RF-029 |
| UC-06 | Editar texto compartilhado | Dono, Convidado | RF-040 a RF-042 |
| UC-07 | Guardar e copiar clip ou bloco de código | Dono, Convidado | RF-043 a RF-047 |
| UC-08 | Trancar ou destrancar a sala | Dono | RF-009 |
| UC-09 | Encerrar a sala | Dono | RF-010 |
| UC-10 | Reconectar após queda de rede | Dono, Convidado | RF-051 a RF-054 |
| UC-11 | Expirar a sala automaticamente | Sistema | RF-070, RN-01 |
| UC-12 | Publicar nova versão | Administrador | RF-074, RF-075 |
| UC-13 | Acompanhar a saúde do site | Administrador | RF-072, RF-073, RF-076 |

### UC-01: Criar sala

| | |
|---|---|
| **Pré-condição** | Nenhuma. |
| **Fluxo principal** | 1. O visitante abre o site. 2. Escolhe a expiração (padrão 12 h). 3. Toca em **Criar sala**. 4. O navegador gera o segredo, deriva as chaves e envia ao servidor só a `authKey`, o salt e a expiração. 5. O servidor cria a sala, dá os cookies de participante e de dono e devolve o código. 6. A tela da sala mostra QR Code, link e código completo. |
| **Fluxo alternativo A** | No passo 2 o visitante marca **senha própria**: ela precisa ter ao menos 10 caracteres; o segredo gerado não existe e o link só leva o código. |
| **Exceções** | Servidor cheio (503): mensagem pedindo para tentar mais tarde. Muitas criações seguidas (429): mensagem de espera. |
| **Pós-condição** | Sala ativa, com o criador como dono. |

### UC-02: Entrar por link ou QR Code

| | |
|---|---|
| **Pré-condição** | A sala está ativa e o convidado tem o link completo. |
| **Fluxo principal** | 1. O convidado abre o link; o navegador lê o segredo do fragmento `#k=`. 2. Consulta o salt da sala, deriva as chaves e envia a `authKey`. 3. O servidor confere o hash e dá o cookie de participante. 4. O navegador guarda a chave na aba, retira o segredo do endereço e mostra a sala com tudo decifrado. |
| **Exceções** | Senha errada (401): mensagem e novo campo de senha. Sala trancada (403): mensagem pedindo ao dono para destrancar. Sala inexistente ou expirada (404). Limite de aparelhos por sala excedido: o tempo real é recusado. |
| **Pós-condição** | O aparelho vê a sala e recebe avisos em tempo real. |

### UC-04: Enviar arquivo

| | |
|---|---|
| **Pré-condição** | O aparelho entrou na sala. |
| **Fluxo principal** | 1. A pessoa escolhe, arrasta ou cola o arquivo. 2. O navegador confere tamanho (100 MB) e espaço da sala. 3. Criptografa o arquivo em blocos e o nome. 4. Envia, mostrando progresso. 5. O servidor confere os limites, grava o arquivo com nome aleatório e avisa todos os aparelhos. 6. Os outros aparelhos veem o arquivo aparecer na lista. |
| **Exceções** | Arquivo grande demais; sala cheia; servidor cheio (507); limite de envios por hora (429); envio interrompido (o parcial é descartado). |
| **Pós-condição** | O arquivo existe, cifrado, na sala. |

---

## 8. Critérios de aceitação

Resumo dos cenários que definem se o produto está **aceito**. Todos têm testes automatizados ou verificação registrada no [`PLANEJAMENTO.md`](../PLANEJAMENTO.md), exceto os marcados como pendentes.

| # | Cenário | Resultado esperado |
|---|---|---|
| CA-01 | Criar sala e abrir o link em outro aparelho | O segundo aparelho vê a mesma sala sem digitar senha |
| CA-02 | Inspecionar banco e disco depois de enviar um arquivo e um texto conhecidos | Nenhum conteúdo, nome de arquivo ou texto aparece legível |
| CA-03 | Enviar arquivo de 100 MB e um de 101 MB | O primeiro é aceito; o segundo é recusado com mensagem clara |
| CA-04 | Dois aparelhos editam o texto ao mesmo tempo | O segundo recebe o aviso de conflito e escolhe qual versão manter |
| CA-05 | Convidado tenta encerrar ou trancar a sala | Resposta 403; a sala continua |
| CA-06 | Sala trancada, aparelho novo tenta entrar | Recusado; quem já estava dentro continua e pode recarregar |
| CA-07 | Sala expira | Tudo é apagado do disco e do banco e os aparelhos são avisados |
| CA-08 | Mais de 5 senhas erradas em um minuto | Resposta 429 com `Retry-After` |
| CA-09 | Desligar a rede de um aparelho e religar | Reconecta sozinho e atualiza a lista |
| CA-10 | Abrir o site em HTTP | É redirecionado para HTTPS |
| CA-11 | Arquivo adulterado no servidor | O navegador recusa a descriptografia |
| CA-12 | Celular na internet móvel cria sala, envia 100 MB e baixa em outro aparelho | **Pendente**: 100 MB no 4G ainda não foi confirmado |
| CA-13 | Celular com tela apagada por 1 minuto | **Pendente**: reconecta e atualiza |

---

## 9. Interfaces externas

### 9.1 Páginas

| Endereço | Função |
|---|---|
| `/` | Criar sala ou entrar numa sala |
| `/r/{código}` | A sala (o segredo vai no fragmento `#k=`, que não chega ao servidor) |
| `/sobre` | O que o servidor guarda, por quanto tempo e contato para denúncias |

### 9.2 API REST e WebSocket

| Método e caminho | Função | Quem pode |
|---|---|---|
| `POST /api/rooms` | Criar sala | Qualquer um (com limite) |
| `GET /api/rooms/{código}/params` | Salt e se há senha própria | Qualquer um (com limite) |
| `POST /api/rooms/{código}/join` | Entrar com a `authKey` | Qualquer um (com limite) |
| `GET /api/rooms/{código}` | Dados da sala (`is_owner`, `is_locked`) | Participante |
| `PUT /api/rooms/{código}/lock` | Trancar ou destrancar | Dono |
| `DELETE /api/rooms/{código}` | Encerrar | Dono |
| `GET/POST /api/rooms/{código}/files` | Listar e enviar arquivos | Participante |
| `GET/DELETE /api/rooms/{código}/files/{id}` | Baixar e apagar | Participante |
| `GET/PUT /api/rooms/{código}/text` | Ler e salvar texto (com versão) | Participante |
| `GET/PUT /api/rooms/{código}/source` | Ler e salvar código (com versão) | Participante |
| `GET/POST/DELETE /api/rooms/{código}/clips` | Clips de texto | Participante |
| `GET/POST/DELETE /api/rooms/{código}/code-clips` | Blocos de código | Participante |
| `GET /api/health` | Saúde do servidor | Qualquer um |
| `WS /ws/rooms/{código}` | Avisos em tempo real | Participante (cookie e origem conferidos) |

Mensagens do WebSocket: `presence`, `file_added`, `file_deleted`, `text_updated`, `source_updated`, `clip_added`, `clip_deleted`, `code_clip_added`, `code_clip_deleted`, `room_closed` (motivo `expired` ou `closed`), `ping` e `pong`.

### 9.3 Limites e constantes

| Item | Valor atual | Configuração |
|---|---|---|
| Expiração da sala | 1, 12, 24 ou 48 h (padrão 12) | `ALLOWED_TTL_HOURS`, `DEFAULT_TTL_HOURS` |
| Arquivo | 100 MB | `MAX_FILE_SIZE_MB` |
| Sala (todos os arquivos) | 500 MB | `MAX_ROOM_SIZE_MB` |
| Texto compartilhado e código compartilhado | 1 MB cada | `MAX_TEXT_SIZE_KB` |
| Clip de texto | 64 KB, até 200 por sala | `MAX_CLIP_SIZE_KB`, `MAX_CLIPS_PER_ROOM` |
| Bloco de código | 256 KB, até 200 por sala | `MAX_CODE_CLIP_SIZE_KB` |
| Espaço total do servidor | 30 GB | `MAX_TOTAL_STORAGE_MB` |
| Salas ativas no servidor | 500 | `MAX_ACTIVE_ROOMS` |
| Aparelhos conectados por sala | 20 | `MAX_CONNECTIONS_PER_ROOM` |
| Consultas e entradas por IP | 30 por minuto | `RATE_LIMIT_LOOKUPS_PER_MINUTE` |
| Senhas erradas por IP e sala | 5 por minuto | `RATE_LIMIT_FAILED_JOINS_PER_MINUTE` |
| Salas criadas por IP | 20 por hora | `RATE_LIMIT_ROOM_CREATIONS_PER_HOUR` |
| Pedidos à API por IP | 600 por minuto | `RATE_LIMIT_API_PER_MINUTE` |
| Arquivos enviados por IP | 120 por hora | `RATE_LIMIT_UPLOADS_PER_HOUR` |
| Limpeza das salas expiradas | a cada 5 minutos | `CLEANUP_INTERVAL_MINUTES` |
| Senha própria | mínimo de 10 caracteres | fixo no frontend |

---

## 10. Itens pendentes e fora de escopo

### 10.1 Pendentes de validação
- Tempo da derivação Argon2id em celular real (meta: menos de ~1 s) (RNF-020).
- Envio de 100 MB na internet móvel (RNF-023, CA-12).
- Reconexão com a tela do celular apagada (RF-054, CA-13).
- Auditoria de acessibilidade WCAG 2.1 AA com leitores de tela (RNF-030).
- Teste formal em Safari, Firefox e outros navegadores (RNF-040).

### 10.2 Ideias futuras (não prometidas)
- Realce de sintaxe nos blocos de código.
- "Compartilhar com..." do Android (share target).
- Edição simultânea sem conflito (CRDT).
- Nome de cada aparelho na sala.
- Contadores de limite que sobrevivam a reinícios; gerenciador de segredos; Alembic para migrações.
- Mais de um servidor (exigiria Redis para tempo real e limites).

### 10.3 Fora de escopo de propósito
- Contas, login, histórico e recuperação de senha.
- Links públicos de download e compartilhamento permanente.
- Aplicativo nativo.
- Expulsar aparelhos individuais (os cookies não identificam aparelhos; trancar ou encerrar cobre o caso).
- Backup dos dados das salas (são temporários e cifrados).
- Prevenção de malware ou conteúdo ilegal: o servidor não consegue ler o conteúdo; a resposta possível a uma denúncia é encerrar a sala.

---

## 11. Rastreabilidade

| Área | Onde está implementado | Onde é testado |
|---|---|---|
| Salas, acesso, dono e trancar | `backend/app/routers/rooms.py`, `session.py`, `room_service.py` | `tests/test_rooms.py`, `test_room_ending.py`, `test_hardening.py` |
| Arquivos | `routers/files.py`, `storage.py`, `file_service.py`; `frontend/static/js/file-*.js`, `upload-panel.js` | `tests/test_files.py`, `test_server_limits.py` |
| Texto e código | `routers/documents.py`, `document_service.py`; `shared-editor.js` | `tests/test_text.py`, `test_source_code.py` |
| Clips e blocos de código | `routers/clips.py`, `clip_service.py`; `clips-panel.js` | `tests/test_clips.py` |
| Tempo real | `routers/ws.py`, `realtime.py`; `socket.js` | `tests/test_realtime.py`; `frontend/tests/socket.test.mjs` |
| Criptografia | `frontend/static/js/crypto.js`, `room-access.js` | `frontend/tests/crypto.test.mjs` |
| Limites e abuso | `rate_limit.py`, `security_events.py`, `config.py` | `tests/test_rate_limits.py`, `test_monitoring.py` |
| Cabeçalhos e segurança | `security_headers.py`, `security.py` | `tests/test_security_headers.py`, `test_hardening.py` |
| Expiração | `cleanup.py` | `tests/test_room_ending.py` |
| Interface, idiomas e PWA | `frontend/templates`, `messages.js`, `i18n.js`, `service-worker.js` | `tests/test_pwa.py`; verificação no navegador |
| Operação | `Dockerfile`, `docker-compose.yml`, `Caddyfile`, `scripts/`, `.github/` | `DEPLOY.md`; verificação em produção |

---

## 12. Glossário

| Termo | Significado |
|---|---|
| **Sala** | Espaço temporário compartilhado entre aparelhos, identificado por um código |
| **Código da sala** | 6 caracteres que identificam a sala no servidor |
| **Segredo** | 12 caracteres gerados pelo app; geram as chaves de criptografia e nunca vão ao servidor |
| **Código completo** | Código da sala mais o segredo, para digitar (`K7P3XM-HQ4T-9WZC-MPN2`) |
| **`authKey`** | Chave derivada da senha que prova ao servidor que o aparelho conhece a senha |
| **Chave de criptografia** | Chave derivada da senha que cifra o conteúdo; nunca sai do navegador |
| **Argon2id** | Função que deixa o teste de senhas lento de propósito |
| **E2E** | Criptografia de ponta a ponta: só os aparelhos da sala conseguem ler o conteúdo |
| **Clip** | Texto curto guardado na sala para copiar depois |
| **Bloco de código** | Trecho de código guardado com a formatação exata |
| **Dono** | Navegador que criou a sala |
| **Convidado** | Navegador que entrou na sala por outro caminho |
| **PWA** | Site que pode ser instalado como aplicativo |
| **CSP** | Política que diz ao navegador de onde o site pode carregar código |
| **TTL** | Tempo de vida da sala |
