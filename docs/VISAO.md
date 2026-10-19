# QuickDrop: Documento de Visão

| | |
|---|---|
| **Produto** | QuickDrop |
| **Versão do documento** | 1.0 |
| **Data** | 18/10/2026 |
| **Endereço** | https://quickdrop-syoti.mexicocentral.cloudapp.azure.com |
| **Documento irmão** | [Documento de Requisitos](REQUISITOS.md) (o que o sistema faz, em detalhe) |

> **Em uma frase:** o QuickDrop passa arquivos e textos de um aparelho para outro em segundos, sem conta e sem anúncios, e com criptografia de ponta a ponta: nem o servidor consegue ler o que você envia.

## Sumário

1. [Introdução](#1-introdução)
2. [O problema e a oportunidade](#2-o-problema-e-a-oportunidade)
3. [Posicionamento](#3-posicionamento)
4. [Usuários e partes interessadas](#4-usuários-e-partes-interessadas)
5. [Visão geral do produto](#5-visão-geral-do-produto)
6. [Diagramas](#6-diagramas)
7. [Recursos do produto](#7-recursos-do-produto)
8. [Decisões de arquitetura](#8-decisões-de-arquitetura)
9. [Restrições e premissas](#9-restrições-e-premissas)
10. [Faixas de qualidade](#10-faixas-de-qualidade)
11. [Riscos](#11-riscos)
12. [Indicadores de sucesso](#12-indicadores-de-sucesso)
13. [Estado atual e roteiro](#13-estado-atual-e-roteiro)

---

## 1. Introdução

### 1.1 Finalidade
Apresentar **a visão do QuickDrop**: por que existe, para quem, o que promete, como é construído em alto nível e quais são seus limites. É um documento para dar contexto a quem chega ao projeto (pessoas, avaliadores, futuros colaboradores). Os detalhes verificáveis estão no [Documento de Requisitos](REQUISITOS.md).

### 1.2 Escopo
O sistema inteiro: o site (frontend), o servidor (backend), a criptografia no navegador, a hospedagem e as rotinas de operação.

### 1.3 Referências
[`PRODUCT.md`](../PRODUCT.md) (propósito e princípios), [`PLANEJAMENTO.md`](PLANEJAMENTO.md) (decisões e histórico por fase), [`DESIGN.md`](../DESIGN.md) (sistema visual), [`DEPLOY.md`](DEPLOY.md) (operação), [`COMO-RODAR.md`](COMO-RODAR.md) (uso local).

---

## 2. O problema e a oportunidade

### 2.1 O problema
Quem precisa passar **um arquivo, um print ou um texto** de um aparelho para outro (do PC para o celular, do celular para o computador de um amigo) costuma recorrer a:

| Alternativa comum | Por que incomoda |
|---|---|
| Enviar para si mesmo por e-mail ou aplicativo de mensagem | Vários passos, limite de tamanho, o conteúdo fica guardado para sempre em outro serviço |
| Serviços de nuvem | Exigem conta, login nos dois aparelhos e deixam os arquivos lá |
| Sites de envio de arquivos | Lentos, cheios de anúncios, e o arquivo fica guardado em texto puro no servidor |
| Cabo ou Bluetooth | Nem sempre à mão, lento ou incompatível entre sistemas |

### 2.2 A oportunidade
Uma **sala temporária** abre em segundos, vale por algumas horas e some. Não precisa de conta. Se a criptografia for feita **no próprio navegador**, o serviço pode prometer algo que a maioria dos concorrentes não pode: **"nem nós conseguimos ler"**.

---

## 3. Posicionamento

| | |
|---|---|
| **Para** | qualquer pessoa que precisa passar arquivos ou textos entre aparelhos |
| **Que** | quer terminar a tarefa em segundos, sem criar conta nem aprender nada |
| **O** QuickDrop | é um site de salas temporárias em tempo real |
| **Que** | criptografa tudo no navegador e apaga tudo sozinho ao fim do tempo |
| **Diferente de** | e-mail, nuvens com conta e sites de upload com anúncios |
| **Nosso produto** | não pede cadastro, não guarda nada legível e não mostra anúncios |

### 3.1 Princípios do produto

1. **Velocidade antes de tudo:** da abertura do site à transferência, o mínimo de passos.
2. **Privacidade verdadeira e explicável:** só afirmar o que a criptografia realmente garante, em linguagem simples.
3. **Sem conta, sem atrito:** o código e o link são a identidade.
4. **Temporário por padrão:** tudo expira e a pessoa sempre vê quanto tempo resta.
5. **Funciona bem no celular**, na rede local e na internet.

### 3.2 O que o QuickDrop **não** promete
- Não recupera senha esquecida (ninguém consegue, nem o administrador).
- Não impede que um servidor comprometido entregue código malicioso: a criptografia no navegador depende do JavaScript que o servidor entrega. Por isso o servidor é endurecido e monitorado.
- Não substitui armazenamento permanente: salas duram de 1 a 48 horas.

---

## 4. Usuários e partes interessadas

### 4.1 Perfis de usuário

| Perfil | Situação típica | O que precisa |
|---|---|---|
| **Pessoa com dois aparelhos** | Print no celular que precisa ir para o PC; arquivo do PC para o celular | Criar a sala em um aparelho e entrar no outro com um QR Code |
| **Estudante ou profissional em computador compartilhado** | Pegar um arquivo num computador de laboratório sem fazer login | Entrar sem conta e não deixar rastros: sala que some sozinha |
| **Quem passa código ou texto** | Colar um trecho de código mantendo a indentação, ou um texto longo, em outro aparelho | Editor e blocos de código com formatação exata e botão de copiar |
| **Grupo pequeno** | Trocar fotos e documentos com amigos presentes | Um link ou QR Code que todos usam; o dono pode trancar a sala |

### 4.2 Partes interessadas

| Parte | Interesse |
|---|---|
| **Usuários** | Rapidez, privacidade, sem cadastro |
| **Administrador / autor** | Servidor barato e estável, pouca manutenção, código simples de entender |
| **Quem reportar abuso** | Canal de denúncia (página Sobre) |
| **Provedor de hospedagem** | Uso dentro das regras (conteúdo ilegal e abuso de recursos) |

### 4.3 Ambiente de uso
Navegadores modernos em computador e celular (a interface é pensada primeiro para o celular), em rede local ou na internet, em português do Brasil ou inglês.

---

## 5. Visão geral do produto

### 5.1 Como funciona, em 4 passos

1. **Criar:** a pessoa abre o site e toca em *Criar sala*. O navegador gera um segredo aleatório e deriva as chaves de criptografia.
2. **Convidar:** o outro aparelho entra pelo **QR Code**, pelo **link** ou digitando o **código**. O segredo viaja no fragmento do link (`#k=`), que o navegador nunca envia ao servidor.
3. **Trocar:** arquivos, textos, código e clips aparecem nos dois aparelhos em tempo real.
4. **Sumir:** quando o tempo acaba, ou o dono encerra, tudo é apagado de verdade.

### 5.2 Garantias de privacidade

| O servidor **sabe** | O servidor **não sabe** |
|---|---|
| Que existe uma sala, o código dela, quando expira | A senha, o segredo e a chave de criptografia |
| O tamanho aproximado dos arquivos cifrados | Nome, tipo, tamanho real e conteúdo dos arquivos |
| Quantos aparelhos estão conectados | O conteúdo dos textos, do código e dos clips |
| Contagens de eventos de segurança (sem IP nem código) | Quem são as pessoas |

---

## 6. Diagramas

Os diagramas abaixo estão em [Mermaid](https://mermaid.js.org): o GitHub os desenha sozinho.

### 6.1 Contexto do sistema

Quem usa o QuickDrop e com quais serviços externos ele conversa.

```mermaid
flowchart TB
    pessoaA["Pessoa (PC)"]
    pessoaB["Pessoa (celular)"]
    admin["Administrador"]
    sistema["QuickDrop<br/>site de salas temporárias com<br/>criptografia de ponta a ponta"]
    letsencrypt["Let's Encrypt<br/>certificado HTTPS"]
    azure["Microsoft Azure<br/>hospedagem e alerta de crédito"]
    github["GitHub<br/>código, verificações e<br/>sugestões de atualização"]

    pessoaA -->|"cria sala, envia e recebe"| sistema
    pessoaB -->|"entra por QR Code ou código"| sistema
    admin -->|"publica versões e acompanha"| sistema
    sistema -->|"pede certificado"| letsencrypt
    sistema -.->|"roda em"| azure
    github -->|"confere se está no ar<br/>a cada 15 minutos"| sistema
    admin -->|"envia o código"| github
```

### 6.2 Contêineres (visão de arquitetura)

As peças que compõem o sistema e como conversam.

```mermaid
flowchart TB
    subgraph aparelho["Aparelho do usuário (navegador)"]
        ui["Interface<br/>HTML, CSS e JavaScript"]
        crypto["crypto.js<br/>libsodium: Argon2id, XChaCha20-Poly1305"]
        ui --- crypto
    end

    subgraph vm["VM Ubuntu no Azure (Docker)"]
        caddy["Caddy<br/>HTTPS automático<br/>portas 80 e 443"]
        subgraph app["Contêiner do app"]
            rotas["Rotas REST e WebSocket"]
            regras["Regras: salas, limites,<br/>dono, expiração"]
            rotas --- regras
        end
        db[("SQLite<br/>salas, textos, clips,<br/>metadados cifrados")]
        disco[("Disco<br/>arquivos cifrados<br/>nome = UUID")]
        caddy -->|"HTTP interno"| rotas
        regras --> db
        regras --> disco
    end

    ui -->|"HTTPS (REST) e WSS<br/>só dados cifrados"| caddy
```

### 6.3 Hierarquia de chaves

De onde vem cada chave e o que vai (ou não) para o servidor.

```mermaid
flowchart TD
    segredo["Segredo gerado (12 caracteres)<br/>ou senha escolhida"]
    salt["Salt aleatório<br/>(guardado na sala, não secreto)"]
    argon["Argon2id<br/>(no navegador)"]
    mestra["Chave-mestra<br/>(apagada da memória logo depois)"]
    auth["authKey"]
    enc["Chave de criptografia"]
    servidor[("Servidor guarda só um HMAC<br/>da authKey (com chave do servidor)")]
    conteudo["Cifra arquivos, nomes, textos,<br/>código e clips<br/>(só no navegador)"]

    segredo --> argon
    salt --> argon
    argon --> mestra
    mestra -->|"derivação 1"| auth
    mestra -->|"derivação 2"| enc
    auth -->|"vai ao servidor<br/>(prova de acesso)"| servidor
    enc -->|"nunca sai do aparelho"| conteudo
```

### 6.4 Criar sala e entrar pelo QR Code

```mermaid
sequenceDiagram
    autonumber
    participant NA as Navegador do dono (PC)
    participant S as Servidor
    participant NB as Navegador do convidado (celular)

    NA->>NA: Gera segredo e salt<br/>Argon2id: authKey e chave de criptografia
    NA->>S: POST /api/rooms (salt, authKey, validade)
    S->>S: Guarda o hash da authKey<br/>cria a sala e o código de 6 caracteres
    S-->>NA: Código + cookies (participante e dono)
    NA->>NB: QR Code com /r/CODIGO#35;k=SEGREDO<br/>(o segredo não passa pelo servidor)
    NB->>S: GET /params (consulta o salt)
    S-->>NB: salt
    NB->>NB: Argon2id: authKey e chave de criptografia
    NB->>S: POST /join (authKey)
    S->>S: Confere o hash e se a sala não está trancada
    S-->>NB: Cookie de participante
    NB->>S: WebSocket (cookie e origem conferidos)
    S-->>NA: presence: 2 aparelhos
    S-->>NB: presence: 2 aparelhos
```

### 6.5 Enviar arquivo criptografado

```mermaid
sequenceDiagram
    autonumber
    participant NA as Navegador 1
    participant S as Servidor
    participant D as Disco e banco
    participant NB as Navegador 2

    NA->>NA: Confere o tamanho (100 MB) e o espaço da sala
    NA->>NA: Cifra o arquivo em blocos de 1 MB<br/>e cifra nome, tipo e tamanho
    NA->>S: POST /files (corpo e metadados cifrados)
    S->>S: Confere os limites de IP, sala e servidor
    S->>D: Grava com nome UUID
    S->>S: Reconfere o espaço, um envio por vez
    S->>D: Registra o arquivo cifrado
    S-->>NA: 201 Criado
    S-->>NB: WebSocket: file_added
    NB->>S: GET /files/ID (quando a pessoa baixa)
    S-->>NB: Bytes cifrados (como anexo)
    NB->>NB: Decifra e confere se não foi alterado
```

### 6.6 Edição do texto compartilhado com conflito

```mermaid
sequenceDiagram
    autonumber
    participant N1 as Aparelho 1
    participant S as Servidor
    participant N2 as Aparelho 2

    Note over N1,N2: Os dois leem o texto na versão 4
    N1->>S: PUT /text (cifrado, base_version 4)
    S->>S: Compara e troca de forma atômica
    S-->>N1: Versão 5
    S-->>N2: WebSocket: text_updated (versão 5)
    N2->>S: PUT /text (cifrado, base_version 4)
    S-->>N2: 409 Conflito (com o texto atual)
    N2->>N2: Pergunta: usar a do outro aparelho<br/>ou manter a minha
```

### 6.7 Modelo de dados

O servidor só guarda dados cifrados (`BLOB`). Nenhuma tabela tem conteúdo legível.

```mermaid
erDiagram
    ROOMS ||--o{ FILES : "tem"
    ROOMS ||--o| ROOM_TEXTS : "tem"
    ROOMS ||--o| ROOM_SOURCE_CODE : "tem"
    ROOMS ||--o{ CLIPS : "tem"
    ROOMS ||--o{ CODE_CLIPS : "tem"

    ROOMS {
        string id PK "UUID interno"
        string code UK "6 caracteres"
        bool has_password
        blob kdf_salt
        string auth_hash "HMAC da authKey"
        bool locked
        datetime created_at
        datetime expires_at
    }
    FILES {
        string id PK "UUID = nome no disco"
        string room_id FK
        blob encrypted_meta "nome, tipo, tamanho"
        int size_bytes "tamanho cifrado"
        datetime created_at
    }
    ROOM_TEXTS {
        string room_id PK
        blob ciphertext
        int version
        datetime updated_at
    }
    ROOM_SOURCE_CODE {
        string room_id PK
        blob ciphertext
        int version
        datetime updated_at
    }
    CLIPS {
        string id PK
        string room_id FK
        blob ciphertext
        datetime created_at
    }
    CODE_CLIPS {
        string id PK
        string room_id FK
        blob ciphertext
        datetime created_at
    }
```

Ao apagar uma sala, o banco apaga em cascata tudo o que depende dela; a pasta de arquivos da sala é removida junto.

### 6.8 Ciclo de vida da sala

```mermaid
stateDiagram-v2
    [*] --> Ativa: criar sala
    Ativa --> Trancada: dono tranca
    Trancada --> Ativa: dono destranca
    Ativa --> Encerrada: dono encerra
    Trancada --> Encerrada: dono encerra
    Ativa --> Expirada: tempo acaba
    Trancada --> Expirada: tempo acaba
    Encerrada --> [*]: tudo apagado
    Expirada --> [*]: limpeza apaga tudo<br/>(a cada 5 min)

    note right of Trancada
        Ninguém novo entra.
        Quem já entrou continua.
    end note
```

### 6.9 Casos de uso

```mermaid
flowchart LR
    visitante(["Visitante"])
    convidado(["Convidado"])
    dono(["Dono"])
    sistema(["Sistema<br/>(automático)"])
    admin(["Administrador"])

    subgraph quickdrop["QuickDrop"]
        uc1["Criar sala"]
        uc2["Entrar na sala<br/>(link, QR Code ou código)"]
        uc3["Enviar, baixar e apagar<br/>arquivos"]
        uc4["Editar texto e código"]
        uc5["Guardar e copiar clips<br/>e blocos de código"]
        uc6["Trancar ou destrancar"]
        uc7["Encerrar a sala"]
        uc8["Expirar e apagar salas"]
        uc9["Publicar versão"]
        uc10["Acompanhar saúde e alertas"]
    end

    visitante --- uc1
    visitante --- uc2
    convidado --- uc3
    convidado --- uc4
    convidado --- uc5
    dono --- uc6
    dono --- uc7
    sistema --- uc8
    admin --- uc9
    admin --- uc10
    dono -.->|"também faz tudo<br/>que o convidado faz"| convidado
```

### 6.10 Implantação (produção)

```mermaid
flowchart TB
    internet(("Internet"))
    subgraph azure["Azure (México Central)"]
        nsg["Regras de rede<br/>80 e 443: todos<br/>22: só o administrador"]
        subgraph vm["VM Ubuntu 24.04"]
            subgraph docker["Docker Compose"]
                caddy["caddy:2<br/>HTTPS e cabeçalhos"]
                app["app (Python 3.14)<br/>1 processo, sem privilégios"]
            end
            vol[("Volume quickdrop-data<br/>banco e arquivos")]
            cron["cron semanal<br/>atualiza as imagens"]
            apt["atualizações de segurança<br/>e reinício às 04:00"]
        end
    end
    internet --> nsg --> caddy --> app --> vol
    cron -.-> docker
```

### 6.11 Operação e alertas

```mermaid
flowchart TB
    admin(["Administrador"])
    subgraph github["GitHub"]
        repo["Repositório<br/>(código público)"]
        uptime["Verificação do site<br/>a cada 15 minutos"]
        dependabot["Dependabot e verificação<br/>mensal das bibliotecas"]
    end
    site["QuickDrop (produção)"]
    vm["VM no Azure"]
    orcamento["Orçamento do Azure<br/>aviso em 60% e 85% do crédito"]

    admin -->|"envia o código"| repo
    repo -.->|"git pull (manual)"| vm
    dependabot -->|"sugere atualizações"| repo
    uptime -->|"consulta /api/health"| site
    uptime -.->|"se falhar: e-mail"| admin
    orcamento -.->|"e-mail"| admin
```

### 6.12 Camadas de segurança

```mermaid
flowchart TB
    subgraph c1["1. Conteúdo: o que o servidor nunca vê"]
        e2e["Criptografia de ponta a ponta no navegador"]
    end
    subgraph c2["2. Acesso"]
        acesso["Segredo de 12 caracteres ou senha de 10+<br/>Argon2id · cookies assinados · dono x convidado · sala trancada"]
    end
    subgraph c3["3. Aplicação"]
        app["Validação estrita · limites por IP e globais<br/>CSP rígida · sem HTML de usuário · downloads como anexo"]
    end
    subgraph c4["4. Servidor"]
        srv["HTTPS e HSTS · SSH só por chave e só do administrador<br/>contêiner sem privilégios · atualizações automáticas"]
    end
    subgraph c5["5. Operação"]
        ops["Alertas de falha e de crédito · Dependabot e pip-audit<br/>resumo de eventos sem dados pessoais"]
    end
    c1 --> c2 --> c3 --> c4 --> c5
```

---

## 7. Recursos do produto

| Grupo | Recursos |
|---|---|
| **Salas** | Criar com expiração de 1, 12, 24 ou 48 h; código curto; QR Code; link; código completo; senha própria opcional; trancar; encerrar; tempo restante; aparelhos conectados |
| **Arquivos** | Qualquer tipo, até 100 MB cada e 500 MB por sala; arrastar e soltar; colar imagem com Ctrl+V; progresso; baixar; apagar; pré-visualizar imagens; baixar tudo em .zip |
| **Texto** | Editor compartilhado em tempo real, com tratamento de conflito; clips para guardar e copiar trechos |
| **Código** | Editor com indentação preservada (Tab, Shift+Tab); blocos de código copiados exatamente como guardados |
| **Segurança** | Criptografia de ponta a ponta; HTTPS; limites contra abuso; expiração automática; dono e convidados |
| **Experiência** | Português e inglês; tema claro e escuro; pensado para o celular; instalável como app; acessível por teclado |
| **Operação** | Docker; HTTPS automático; atualizações automáticas; alertas; documentação de implantação |

Os requisitos detalhados e os critérios de aceitação estão no [Documento de Requisitos](REQUISITOS.md).

---

## 8. Decisões de arquitetura

| Decisão | Escolha | Motivo | Consequência |
|---|---|---|---|
| Criptografia | No navegador (libsodium), desde o primeiro dia | Permite prometer que o servidor não lê nada | Senha esquecida = conteúdo perdido; depende de o servidor entregar JavaScript íntegro |
| Entrada na sala | QR Code ou link (segredo em `#k=`) como caminho principal; código completo como alternativa | Rápido no celular e o segredo nunca chega ao servidor | O código completo para digitar é longo (21 caracteres) |
| Backend | FastAPI (Python) com Uvicorn | Simples, rápido e com WebSocket nativo | 1 processo: estado em memória |
| Frontend | HTML (Jinja2), CSS e JavaScript puro | Sem etapa de build; fácil de entender | Um pouco mais de código manual |
| Banco | SQLite | Um arquivo; sem servidor de banco para administrar | Um servidor só; migrações manuais |
| Arquivos | Disco local, nome UUID, só bytes cifrados | Simples e barato | Limite pelo disco da VM |
| Tempo real | WebSocket por sala, com reconexão e reconferência | Resposta imediata | Conexões em memória; um servidor só |
| Conflitos de texto | Versão + troca atômica; a pessoa escolhe | Simples e sem perder texto | Não mistura edições (CRDT ficou para o futuro) |
| Acesso | Cookie assinado por sala + cookie de dono | Sem contas | Dono é o navegador, não a pessoa |
| Hospedagem | VM do Azure for Students + Docker + Caddy | Grátis (com crédito), HTTPS automático | Crédito de ~7 meses |
| Operação | GitHub Actions, Dependabot, cron e unattended-upgrades | Sem custo e quase sem manutenção | Depende de o GitHub manter os agendamentos ativos |
| Design | Sistema visual "Linhas de Metrô" | Diferencia o produto e explica o caminho da transferência | Documentado em `DESIGN.md` |

---

## 9. Restrições e premissas

**Restrições:** custo próximo de zero; um único servidor pequeno (1 vCPU e 1 GiB); sem contas nem recuperação de senha; código simples, em pastas separadas para backend e frontend; criptografia concentrada em um arquivo.

**Premissas:** navegadores atualizados; uso por poucas pessoas por sala; conteúdo temporário; o administrador acompanha os alertas por e-mail.

---

## 10. Faixas de qualidade

| Qualidade | Meta |
|---|---|
| **Segurança e privacidade** | Servidor sem acesso ao conteúdo; HTTPS; limites contra abuso; segredo com ~59 bits; senha própria com 10+ caracteres |
| **Desempenho** | Derivar as chaves em menos de ~1 s no celular; arquivos processados em blocos de 1 MB |
| **Usabilidade** | Transferência concluída sem aprender nada, em poucos passos |
| **Acessibilidade** | WCAG 2.1 AA (alvo; sem auditoria formal) |
| **Disponibilidade** | Reinício automático; alerta se o site cair |
| **Manutenibilidade** | Código limpo, 195 testes no backend e 72 no frontend, documentação atualizada |
| **Portabilidade** | Docker: o mesmo pacote roda em qualquer servidor |

---

## 11. Riscos

Probabilidade (P) e impacto (I): **B** baixo, **M** médio, **A** alto.

| # | Risco | P | I | Mitigação | Estado |
|---|---|---|---|---|---|
| R1 | O crédito do Azure acaba em cerca de 7 meses | A | M | Alerta de 60% e 85%; o Docker permite migrar de hospedagem em cerca de 20 minutos | Monitorado |
| R2 | Servidor comprometido entrega JavaScript malicioso | B | A | SSH restrito e só por chave, contêiner sem privilégios, atualizações automáticas, CSP rígida; limitação explicada na página Sobre | Mitigado em parte |
| R3 | Uso para enviar conteúdo ilegal ou malware | M | M | Salas temporárias; contato para denúncia; a ação possível é encerrar a sala | Aceito |
| R4 | Ataque de negação de serviço ou lotação do servidor | M | M | Limites por IP e globais, conferência da senha instantânea (HMAC), contagem de eventos | Mitigado |
| R5 | Senha fraca escolhida pela pessoa | M | A | Mínimo de 10 caracteres; segredo gerado de 12; Argon2id | Mitigado em parte |
| R6 | Link ou QR Code compartilhado com quem não deveria | M | M | Dono pode trancar ou encerrar; segredo some da barra de endereço; salas expiram | Mitigado em parte |
| R7 | Queda da hospedagem ou da máquina virtual | B | M | Reinício automático, alerta a cada 15 min, plano de recuperação documentado | Mitigado |
| R8 | Navegador antigo sem WebAssembly ou WebSocket | B | M | Mensagem de erro; recomendações de navegadores atualizados | Aceito |
| R9 | Entrada lenta no celular (derivação das chaves e rede) | M | M | Medido ~4 s; módulos carregados em paralelo, cache das bibliotecas e menos idas ao servidor; a medir de novo | **Em medição** |
| R10 | Rotinas agendadas do GitHub desativadas por inatividade (60 dias) | M | B | Lembrete em `DEPLOY.md`; reativar na aba Actions | Documentado |
| R11 | Perda da chave SSH ou do arquivo `.env` | B | M | Guardar cópia em cofre de senhas; recriar a VM a partir do repositório | A fazer pelo administrador |

---

## 12. Indicadores de sucesso

O produto **ainda não tem usuários além do autor**, então não há números reais de uso; nenhuma estatística foi inventada. Os indicadores a acompanhar:

| Indicador | Como medir | Meta |
|---|---|---|
| Tempo para concluir uma transferência entre dois aparelhos | Teste com pessoas | Menos de 30 s |
| Transferências concluídas sem ajuda | Teste de usabilidade | 9 em cada 10 |
| Tempo de entrada com senha no celular | Medição em aparelho | Até ~3 s (medido ~4 s antes das otimizações) |
| Disponibilidade do site | Verificação a cada 15 min | 99% ao mês |
| Vulnerabilidades conhecidas nas dependências | `pip-audit`, Dependabot | Zero em aberto |
| Cobertura de testes automatizados | Contagem | Todo requisito essencial com teste ou verificação registrada |

---

## 13. Estado atual e roteiro

### 13.1 Fases concluídas

```mermaid
flowchart TB
    subgraph linha1["Base e conteúdo"]
        direction LR
        f0["Fase 0<br/>Base do projeto"] --> f1["Fase 1<br/>Criptografia"] --> f2["Fase 2<br/>Salas"] --> f3["Fase 3<br/>Arquivos cifrados"]
    end
    subgraph linha2["Tempo real e segurança"]
        direction LR
        f4["Fase 4<br/>Tempo real"] --> f5["Fase 5<br/>Texto e clips"] --> f6["Fase 6<br/>Expiração e segurança"] --> f7["Fase 7<br/>Imagens, zip e PWA"]
    end
    subgraph linha3["Extras e publicação"]
        direction LR
        ex["Extra<br/>Código"] --> f8["Fase 8<br/>Internet"] --> seg["Extra<br/>Dono, segurança e operação"]
    end
    linha1 --> linha2 --> linha3
```

### 13.2 O que falta
- **Validar em aparelho real:** tempo de entrada com senha no celular (medir de novo depois das otimizações), outros navegadores e acessibilidade com leitores de tela. Já validados em celular real: 100 MB no 4G (1 min 36 s) e reconexão com a tela apagada.
- **Decidir a hospedagem depois do crédito** (cerca de 7 meses).
- **Ideias futuras:** realce de sintaxe, "Compartilhar com..." do Android, edição sem conflito (CRDT), nome dos aparelhos, mais de um servidor.

---

*Este documento descreve a visão do produto. As decisões e o histórico de cada fase estão no [`PLANEJAMENTO.md`](PLANEJAMENTO.md); os requisitos verificáveis, no [Documento de Requisitos](REQUISITOS.md).*
